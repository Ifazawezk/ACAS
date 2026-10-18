from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketRead, TicketCreate

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/", response_model=List[TicketRead])
def list_tickets(status: Optional[TicketStatus] = None, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.created_at.desc()).limit(limit).all()


@router.post("/", response_model=TicketRead)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """Create a new ticket from a comment"""
    # Verify comment exists
    from app.models.comment import Comment
    comment = db.query(Comment).filter(Comment.id == payload.comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if ticket already exists for this comment
    existing_ticket = db.query(Ticket).filter(Ticket.comment_id == payload.comment_id).first()
    if existing_ticket:
        raise HTTPException(status_code=400, detail="Ticket already exists for this comment")
    
    # Create new ticket
    ticket = Ticket(
        comment_id=payload.comment_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=TicketStatus.open,
        assigned_to=payload.assigned_to
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/close", response_model=TicketRead)
def close_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = TicketStatus.closed
    db.commit()
    db.refresh(ticket)
    return ticket
