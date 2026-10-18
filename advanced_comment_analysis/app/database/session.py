import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Development helper: if USE_SQLITE_DEV is set, use a local SQLite file so the app
# can run without requiring Postgres or Docker. For production, unset this flag and
# provide a proper POSTGRES DATABASE_URL.
USE_SQLITE_DEV = os.getenv("USE_SQLITE_DEV", "true").lower() in ("1", "true", "yes")

if USE_SQLITE_DEV:
    # Use a local SQLite file in the project root for quick local testing
    # Use __file__ for absolute path computation instead of relying on cwd
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
    SQLITE_PATH = os.path.join(BASE_DIR, "data", "dev.db")
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
    # sqlite needs check_same_thread False when used with multiple threads
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/commentdb")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# FastAPI dependency helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
