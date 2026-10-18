from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.activity_log import ActivityLog
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/admin/activity-log", tags=["activity"])

class ActivityLogResponse(BaseModel):
    id: int
    timestamp: str
    user_id: Optional[int]
    action_type: str
    resource_type: str
    resource_id: Optional[int]
    description: str
    metadata: Optional[dict] = None

@router.get("", response_model=List[ActivityLogResponse])
async def get_activity_log(
    db: Session = Depends(get_db),
    action_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get activity log entries with optional filters"""
    query = db.query(ActivityLog)
    
    if action_type:
        query = query.filter(ActivityLog.action_type == action_type)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    # Order by most recent first
    query = query.order_by(ActivityLog.timestamp.desc())
    
    # Apply pagination
    total = query.count()
    logs = query.limit(limit).offset(offset).all()
    
    return logs

@router.post("/log")
async def log_activity(
    action_type: str,
    resource_type: str,
    description: str,
    resource_id: Optional[int] = None,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Log a user activity/action"""
    log = ActivityLog(
        user_id=1,  # TODO: Get from auth context
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        metadata=metadata
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@router.get("/stats")
async def get_activity_stats(db: Session = Depends(get_db)):
    """Get activity statistics"""
    total_logs = db.query(ActivityLog).count()
    
    # Count by action type
    from sqlalchemy import func
    action_counts = db.query(
        ActivityLog.action_type,
        func.count(ActivityLog.id).label('count')
    ).group_by(ActivityLog.action_type).all()
    
    return {
        "total_logs": total_logs,
        "by_action": {action: count for action, count in action_counts}
    }

@router.delete("/old")
async def cleanup_old_logs(days: int = Query(90, description="Delete logs older than N days"), db: Session = Depends(get_db)):
    """Delete activity logs older than N days"""
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    deleted = db.query(ActivityLog).filter(ActivityLog.timestamp < cutoff).delete()
    db.commit()
    
    return {"deleted": deleted}
