"""Entries for the activity log. The caller commits, so an entry is saved with the change it describes."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


def record(
    db: Session,
    user,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
) -> ActivityLog:
    """Add an entry to the session. action is create, update, delete, bulk or export."""
    entry = ActivityLog(
        user_id=user.id if user is not None else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(entry)
    return entry
