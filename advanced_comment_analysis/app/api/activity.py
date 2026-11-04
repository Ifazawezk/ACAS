from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.activity_log import ActivityLog
from app.services.activity_service import record
from app.utils.roles import get_current_user

router = APIRouter(prefix="/admin/activity-log", tags=["activity"])


class ActivityCreate(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[str] = None


@router.get("", response_model=List[dict])
def get_activity_log(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Activity log entries, newest first."""
    query = db.query(ActivityLog)
    if action:
        query = query.filter(ActivityLog.action == action)
    if resource_type:
        query = query.filter(ActivityLog.resource_type == resource_type)
    if user_id is not None:
        query = query.filter(ActivityLog.user_id == user_id)
    logs = query.order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc()).offset(offset).limit(limit).all()
    return [log.to_dict() for log in logs]


@router.post("/log")
def log_activity(entry: ActivityCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Add an entry by hand. It is saved under the admin who sent it."""
    log = record(db, user, entry.action, entry.resource_type, entry.resource_id, entry.details)
    db.commit()
    db.refresh(log)
    return log.to_dict()


@router.get("/stats")
def get_activity_stats(db: Session = Depends(get_db)):
    """Number of entries, in total and for each action."""
    counts = db.query(ActivityLog.action, func.count(ActivityLog.id)).group_by(ActivityLog.action).all()
    return {
        "total_logs": db.query(ActivityLog).count(),
        "by_action": {action: count for action, count in counts},
    }


@router.delete("/old")
def cleanup_old_logs(
    days: int = Query(90, ge=1, description="Delete entries older than this many days"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete old entries. The clean-up itself is logged, so it can't be hidden."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(ActivityLog).filter(ActivityLog.created_at < cutoff).delete(synchronize_session=False)
    record(db, user, "delete", "activity_log", details=f"Deleted {deleted} entries older than {days} days")
    db.commit()
    return {"deleted": deleted}
