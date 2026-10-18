from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.ticket import TicketStatus
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def safe_enum_value(enum_obj):
    """Safely convert enum to string value."""
    if enum_obj is None:
        return None
    if hasattr(enum_obj, 'value'):
        return enum_obj.value
    return str(enum_obj)


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    total_comments = db.query(func.count(Comment.id)).scalar() or 0
    # define negative emotions set
    negative_emotions = ["angry", "sad", "frustrated", "negative", "upset"]
    negative_count = db.query(func.count(Comment.id)).filter(Comment.emotion.in_(negative_emotions)).scalar() or 0
    pct_negative = (negative_count / total_comments) if total_comments else 0.0

    high_priority_tickets = db.query(func.count(Ticket.id)).filter(Ticket.priority.in_(("High", "Critical"))).scalar() or 0

    sentiment_distribution = db.query(Comment.emotion, func.count(Comment.id)).group_by(Comment.emotion).all()
    sentiment_distribution = [{"emotion": e or "unknown", "count": c} for e, c in sentiment_distribution]

    priority_distribution = db.query(Comment.priority, func.count(Comment.id)).group_by(Comment.priority).all()
    priority_distribution = [{"priority": safe_enum_value(p), "count": c} for p, c in priority_distribution]

    top_complaint = db.query(Comment.intent, func.count(Comment.id)).group_by(Comment.intent).order_by(func.count(Comment.id).desc()).first()
    top_complaint = top_complaint[0] if top_complaint else None

    ticket_status = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    ticket_status = [{"status": safe_enum_value(s), "count": c} for s, c in ticket_status]

    return {
        "total_comments": total_comments,
        "pct_negative": pct_negative,
        "high_priority_tickets": high_priority_tickets,
        "sentiment_distribution": sentiment_distribution,
        "priority_distribution": priority_distribution,
        "top_complaint": top_complaint,
        "ticket_status_breakdown": ticket_status,
    }


@router.get('/metrics/history')
def metrics_history(db: Session = Depends(get_db)):
    """Return hourly comment counts for the last 24 hours."""
    end = datetime.utcnow()
    start = end - timedelta(hours=23)
    # SQLite: group by hour using strftime
    hour_col = func.strftime('%Y-%m-%d %H:00', Comment.created_at)
    rows = db.query(hour_col.label('hour'), func.count(Comment.id)).filter(Comment.created_at >= start).group_by('hour').order_by('hour').all()
    # build map
    counts = { r[0]: r[1] for r in rows }
    result = []
    for i in range(24):
        t = start + timedelta(hours=i)
        key = t.strftime('%Y-%m-%d %H:00')
        result.append({'ts': key, 'count': counts.get(key, 0)})
    return {'hours': result}
