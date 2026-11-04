from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
import shutil
import os
import csv
import json
import re
import uuid
from pathlib import Path, PureWindowsPath
from typing import List
from datetime import datetime

from app.database.session import get_db, SessionLocal
from app.schemas.comment import CommentCreate, CommentRead
from app.services.ai_service import analyze_text
from app.services.comment_ticket_service import save_comment_and_analysis
from app.services import csv_service
from app.models.activity_log import ActivityLog, Favorite
from app.services.activity_service import record
from app.utils.roles import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])

PROJECT_DIR = Path(__file__).resolve().parents[2]
EXPORT_NAME = re.compile(r"comments_export_\d{8}_\d{6}_[0-9a-f]{8}\.(csv|json)")
EXPORT_FIELDS = (
    "id", "customer_name", "source", "content", "raw_metadata", "emotion", "intent", "priority",
    "needs_ticket", "suggested_response", "confidence", "created_at", "analyzed_at", "ticket",
)


def export_dir() -> Path:
    """Where exports are saved: EXPORT_DIR if set, relative to the project, or else data/exports."""
    folder = Path(os.getenv("EXPORT_DIR") or "data/exports")
    return folder if folder.is_absolute() else PROJECT_DIR / folder


def user_export_dir(user) -> Path:
    # One folder per account, so an admin can only download their own exports.
    return export_dir() / str(user.id)


def safe_enum_value(enum_obj):
    """Safely convert enum to string value."""
    if enum_obj is None:
        return None
    if hasattr(enum_obj, 'value'):
        return enum_obj.value
    return str(enum_obj)


def serialize_comment(c):
    """Serialize a comment ORM object to JSON-friendly dict."""
    ticket_data = None
    if c.ticket:
        ticket_data = {
            'id': c.ticket.id,
            'title': c.ticket.title,
            'status': safe_enum_value(c.ticket.status) or 'open',
            'priority': safe_enum_value(c.ticket.priority),
        }
    return {
        'id': c.id,
        'customer_name': c.customer_name,
        'source': c.source,
        'content': c.content,
        'raw_metadata': c.raw_metadata,
        'emotion': c.emotion,
        'intent': c.intent,
        'priority': safe_enum_value(c.priority),
        'needs_ticket': c.needs_ticket,
        'suggested_response': c.suggested_response,
        'confidence': c.confidence,
        'created_at': c.created_at,
        'analyzed_at': c.analyzed_at,
        'ticket': ticket_data,
    }


@router.post("/upload")
def upload_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...), source: str = "csv"):
    # Save uploaded file temporarily and process in background
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    # The client picks file.filename, so it never becomes part of a path on this server.
    tmp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.csv")
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # schedule background processing
    background_tasks.add_task(csv_service.process_csv_file, tmp_path, source)
    # PureWindowsPath splits on both kinds of slash.
    return {"status": "accepted", "filename": PureWindowsPath(file.filename or "").name}


@router.post("/", response_model=dict)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db)):
    # Analyze synchronously for manual entry
    analysis = analyze_text(payload.content)
    if not analysis:
        raise HTTPException(status_code=500, detail="AI analysis failed")
    comment, ticket = save_comment_and_analysis(db, payload.content, analysis.dict(), source=payload.source or 'manual')
    return serialize_comment(comment)


@router.get("/", response_model=List[dict])
def list_comments(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query(None),
    emotion: str = Query(None),
    intent: str = Query(None),
    priority: str = Query(None),
    source: str = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|confidence|priority)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """List comments with search, filter, and sort options.
    
    Query params:
    - search: Search in comment content
    - emotion: Filter by emotion (joy, anger, sad, etc.)
    - intent: Filter by intent (complaint, praise, question, etc.)
    - priority: Filter by priority (Low, Medium, High, Critical)
    - source: Filter by source (manual, csv, url, api)
    - sort_by: Sort by field (created_at, confidence, priority)
    - sort_order: asc or desc
    - limit: Results per page (max 500)
    - offset: Pagination offset
    """
    from app.models.comment import Comment
    
    query = db.query(Comment)
    
    # Apply filters
    if search:
        query = query.filter(Comment.content.ilike(f"%{search}%"))
    if emotion:
        query = query.filter(Comment.emotion == emotion)
    if intent:
        query = query.filter(Comment.intent == intent)
    if priority:
        query = query.filter(Comment.priority == priority)
    if source:
        query = query.filter(Comment.source == source)
    
    # Apply sorting
    sort_field = getattr(Comment, sort_by, Comment.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())
    
    # Pagination
    total = query.count()
    comments = query.offset(offset).limit(limit).all()
    
    return [serialize_comment(c) for c in comments]


@router.get("/{comment_id}", response_model=dict)
def get_comment_details(comment_id: int, db: Session = Depends(get_db)):
    """Get full details of a single comment."""
    from app.models.comment import Comment
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return serialize_comment(comment)


@router.post("/bulk-action")
def bulk_action(
    action: str = Query(..., regex="^(tag|assign_priority|create_tickets|delete)$"),
    comment_ids: List[int] = Query(...),
    priority: str = Query(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """Perform bulk actions on multiple comments.
    
    Actions:
    - tag: Tag comments (currently just marks),
    - assign_priority: Set priority for multiple comments
    - create_tickets: Create tickets for all comments
    - delete: Delete multiple comments
    """
    from app.models.comment import Comment
    from app.models.ticket import Ticket, TicketStatus
    
    comments = db.query(Comment).filter(Comment.id.in_(comment_ids)).all()
    if not comments:
        raise HTTPException(status_code=404, detail="No comments found")
    
    count = 0
    
    if action == "assign_priority" and priority:
        for comment in comments:
            try:
                comment.priority = priority
                count += 1
            except:
                continue
        db.commit()
    
    elif action == "create_tickets":
        for comment in comments:
            if not comment.ticket and comment.needs_ticket:
                try:
                    ticket = Ticket(
                        title=f"[{comment.emotion}] {comment.intent}",
                        description=comment.content[:500],
                        priority=comment.priority,
                        status=TicketStatus.open,
                        comment_id=comment.id
                    )
                    db.add(ticket)
                    count += 1
                except:
                    continue
        db.commit()
    
    elif action == "delete":
        for comment in comments:
            # A ticket cannot exist without its comment, and favorites have no foreign key.
            if comment.ticket:
                db.delete(comment.ticket)
            db.query(Favorite).filter(Favorite.comment_id == comment.id).delete()
            db.delete(comment)
            count += 1
        db.commit()

    record(db, user, "bulk", "comment", details=f"{action} on {count} comments")
    db.commit()
    return {"status": "success", "action": action, "affected_count": count}


@router.get("/export/download", response_model=dict)
def export_comments(
    format: str = Query("csv", regex="^(csv|json)$"),
    emotion: str = Query(None),
    intent: str = Query(None),
    priority: str = Query(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """Export comments to CSV or JSON with optional filtering."""
    from app.models.comment import Comment
    
    query = db.query(Comment)
    if emotion:
        query = query.filter(Comment.emotion == emotion)
    if intent:
        query = query.filter(Comment.intent == intent)
    if priority:
        query = query.filter(Comment.priority == priority)
    
    comments = query.all()
    data = [serialize_comment(c) for c in comments]
    
    filename = f"comments_export_{datetime.utcnow():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}.{format}"
    folder = user_export_dir(user)
    folder.mkdir(parents=True, exist_ok=True)

    if format == "json":
        with open(folder / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    else:
        # Excel only reads a CSV as UTF-8 when it starts with a byte order mark, which utf-8-sig writes.
        with open(folder / filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=EXPORT_FIELDS)
            writer.writeheader()
            for row in data:
                writer.writerow({k: "" if v is None else str(v) for k, v in row.items()})

    record(db, user, "export", "comment", details=f"{len(data)} comments as {format}")
    db.commit()
    return {
        "status": "ready",
        "filename": filename,
        "count": len(data),
        "url": f"/comments/export/files/{filename}",
    }


@router.get("/export/files/{filename}")
def download_export(filename: str, user = Depends(get_current_user)):
    """Send an export file back to the admin who made it."""
    path = user_export_dir(user) / filename
    if not EXPORT_NAME.fullmatch(filename) or not path.is_file():
        raise HTTPException(status_code=404, detail="Export not found")
    # Starlette adds "; charset=utf-8" to text types itself.
    media_type = "text/csv" if filename.endswith(".csv") else "application/json"
    return FileResponse(path, media_type=media_type, filename=filename)


@router.post("/{comment_id}/favorite")
def toggle_favorite(comment_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Add/remove comment from user's favorites."""
    from app.models.comment import Comment
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    favorite = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.comment_id == comment_id
    ).first()
    
    if favorite:
        db.delete(favorite)
        is_favorite = False
    else:
        favorite = Favorite(user_id=user.id, comment_id=comment_id)
        db.add(favorite)
        is_favorite = True
    
    db.commit()
    return {"comment_id": comment_id, "is_favorite": is_favorite}


@router.get("/favorites/list")
def get_favorites(db: Session = Depends(get_db), user = Depends(get_current_user)):
    """Get user's favorite comments."""
    from app.models.comment import Comment
    
    # Favorite has no foreign key to Comment, so the join needs its condition spelled out.
    favorites = (
        db.query(Comment)
        .join(Favorite, Favorite.comment_id == Comment.id)
        .filter(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return [serialize_comment(c) for c in favorites]


@router.get("/activity/log")
def get_activity_log(
    limit: int = Query(100),
    resource_type: str = Query(None),
    action: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get activity log entries."""
    query = db.query(ActivityLog)
    
    if resource_type:
        query = query.filter(ActivityLog.resource_type == resource_type)
    if action:
        query = query.filter(ActivityLog.action == action)
    
    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]
