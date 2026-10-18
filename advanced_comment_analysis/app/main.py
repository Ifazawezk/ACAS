from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware  # <-- Add this import
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
import os
from pathlib import Path
from app.database import session as db_session
from app.api import auth as auth_router
from app.api import ai as ai_router
from app.api import comments as comments_router
from app.api import tickets as tickets_router
from app.api import dashboard as dashboard_router
from app.api import admin as admin_router
from app.api import templates as templates_router
from app.api import activity as activity_router
from app.utils.logging_config import configure_logging
from app.utils.roles import require_role
from app.models.user import UserRole
from app.models.api_config import APIConfig  # Import to ensure table is created
from app.models.activity_log import ActivityLog, Favorite  # Import for audit logging
from app.services.ai_service import analyze_text
from app.database.session import SessionLocal
import logging

app = FastAPI(title="Advanced Comment Analysis System - MVP")

# --- Add CORS Setup Here ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# ---------------------------

# include routers
app.include_router(auth_router.router)
app.include_router(ai_router.router)
app.include_router(comments_router.router)
app.include_router(tickets_router.router)
app.include_router(dashboard_router.router)
app.include_router(admin_router.router)
app.include_router(templates_router.router)
app.include_router(activity_router.router)

# Mount static files for frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="static")
else:
    print(f"Warning: Frontend directory not found at {frontend_dir}")


@app.on_event("startup")
def startup():
    # Configure logging
    configure_logging()
    # Create tables if not present
    db_session.Base.metadata.create_all(bind=db_session.engine)


@app.get('/admin-only')
def admin_only(user = Depends(require_role(UserRole.admin))):
    return {"status": "ok", "user": user.email}


@app.get("/health")
def health_check():
    logger = logging.getLogger(__name__)
    status = {"status": "ok"}
    # DB check
    try:
        db = SessionLocal()
        # simple query
        db.execute(text('SELECT 1'))
        db.close()
        status['db'] = 'ok'
    except Exception as e:
        logger.exception('DB health check failed')
        status['db'] = 'error'
        status['status'] = 'degraded'

    # AI quick check (use small input, will fall back to simulated)
    try:
        res = analyze_text('health check')
        if res and isinstance(res.confidence, float):
            status['ai'] = 'ok'
        else:
            status['ai'] = 'error'
            status['status'] = 'degraded'
    except Exception:
        logger.exception('AI health check failed')
        status['ai'] = 'error'
        status['status'] = 'degraded'

    return status