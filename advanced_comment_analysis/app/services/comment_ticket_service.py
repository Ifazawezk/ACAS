from sqlalchemy.orm import Session
from datetime import datetime

from app.models.comment import Comment, PriorityLevel
from app.models.ticket import Ticket, TicketStatus
from app.models.routing_rule import RoutingRule
from app.models.sentic_mapping import SenticMapping
import re


def save_comment_and_analysis(db: Session, content: str, analysis: dict, source: str = "manual"):
    # Save comment
    # Apply sentic mappings: explicit mapping of emotion -> priority
    emotion = analysis.get('emotion')
    mapped_priority = None
    try:
        if emotion:
            m = db.query(SenticMapping).filter(SenticMapping.emotion == emotion).first()
            if m:
                mapped_priority = m.priority
    except Exception:
        mapped_priority = None

    # Apply routing rules: pattern match overrides priority
    try:
        rules = db.query(RoutingRule).filter(RoutingRule.enabled == True).all()
        for r in rules:
            try:
                if re.search(r.pattern, content, flags=re.IGNORECASE):
                    mapped_priority = r.priority
                    break
            except re.error:
                # fallback to simple substring
                if r.pattern.lower() in content.lower():
                    mapped_priority = r.priority
                    break
    except Exception:
        pass

    final_priority = mapped_priority or analysis.get('priority') or PriorityLevel.Low

    comment = Comment(
        content=content,
        source=source,
        emotion=analysis.get('emotion'),
        intent=analysis.get('intent'),
        priority=final_priority if final_priority else PriorityLevel.Low,
        needs_ticket=analysis.get('needs_ticket', False),
        suggested_response=analysis.get('suggested_response'),
        confidence=analysis.get('confidence', 0.0),
        analyzed_at=datetime.utcnow(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Auto-create ticket for High or Critical
    if comment.priority in (PriorityLevel.High, PriorityLevel.Critical) or comment.needs_ticket:
        ticket = Ticket(
            comment_id=comment.id,
            title=(comment.intent or "Customer Issue")[:250],
            description=(comment.content)[:2000],
            status=TicketStatus.open,
            priority=comment.priority.value if hasattr(comment.priority, 'value') else str(comment.priority),
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return comment, ticket

    return comment, None
