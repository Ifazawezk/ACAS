"""Point the app at a throwaway database and the offline analyzer before it is imported."""
import os
import tempfile
from pathlib import Path

_database = Path(tempfile.mkdtemp(prefix="acas-tests-")) / "test.db"

os.environ["USE_SQLITE_DEV"] = "false"
os.environ["DATABASE_URL"] = f"sqlite:///{_database.as_posix()}"
os.environ["FORCE_LOCAL"] = "true"
os.environ["OPENAI_API_KEY"] = ""
