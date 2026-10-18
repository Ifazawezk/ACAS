from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
import shutil
import os
import csv
import json
from typing import List
from datetime import datetime

from app.database.session import get_db, SessionLocal
from app.schemas.comment import CommentCreate, CommentRead
from app.services.ai_service import analyze_text
from app.services.comment_ticket_service import save_comment_and_analysis
from app.services import csv_service
from app.models.activity_log import ActivityLog, Favorite
from app.utils.roles import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])


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
    tmp_path = os.path.join(tmp_dir, file.filename)
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # schedule background processing
    background_tasks.add_task(csv_service.process_csv_file, tmp_path, source)
    return {"status": "accepted", "filename": file.filename}


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
    db: Session = Depends(get_db)
):
    """Perform bulk actions on multiple comments.
    
    Actions:
    - tag: Tag comments (currently just marks),
    - assign_priority: Set priority for multiple comments
    - create_tickets: Create tickets for all comments
    - delete: Delete multiple comments
    """
    from app.models.comment import Comment
    from app.models.ticket import Ticket, TicketStatus, Priority
    
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
            try:
                db.delete(comment)
                count += 1
            except:
                continue
        db.commit()
    
    return {"status": "success", "action": action, "affected_count": count}


@router.get("/export/download", response_model=dict)
def export_comments(
    format: str = Query("csv", regex="^(csv|json)$"),
    emotion: str = Query(None),
    intent: str = Query(None),
    priority: str = Query(None),
    db: Session = Depends(get_db)
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
    
    filename = f"comments_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    if format == "json":
        filepath = f"/tmp/{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    else:  # csv
        filepath = f"/tmp/{filename}.csv"
        if data:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                for row in data:
                    writer.writerow({k: str(v) if v else "" for k, v in row.items()})
    
    return {
        "status": "ready",
        "filename": f"{filename}.{format}",
        "count": len(data),
        "url": f"/export/{filename}.{format}"
    }


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
    
    favorites = db.query(Comment).join(Favorite).filter(Favorite.user_id == user.id).all()
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
