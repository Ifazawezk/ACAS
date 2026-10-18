"""Apply Sentic mappings to existing comments in the DB.

Updates comment.priority based on SenticMapping.emotion -> priority.
Optionally auto-creates tickets for newly-upgraded High/Critical comments.
"""
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.sentic_mapping import SenticMapping
from app.models.comment import Comment, PriorityLevel
from app.models.ticket import Ticket, TicketStatus
import app.models.user  # ensure mapper registry for relationships is configured

def apply_mappings(dry_run=False):
    db: Session = SessionLocal()
    try:
        mappings = db.query(SenticMapping).all()
        mapd = {m.emotion.lower(): m.priority for m in mappings}
        print(f"Loaded {len(mapd)} sentic mappings")

        comments = db.query(Comment).filter(Comment.emotion != None).all()
        updated = 0
        tickets_created = 0
        for c in comments:
            emo = (c.emotion or '').lower()
            if not emo: 
                continue
            if emo in mapd:
                target = mapd[emo]
                try:
                    target_enum = PriorityLevel(target)
                except Exception:
                    # skip invalid mapping
                    continue
                if c.priority != target_enum:
                    print(f"Comment {c.id}: priority {c.priority} -> {target_enum}")
                    if not dry_run:
                        c.priority = target_enum
                        # ensure analyzed_at exists
                        if not c.analyzed_at:
                            from datetime import datetime
                            c.analyzed_at = datetime.utcnow()
                        db.add(c)
                        db.commit()
                        db.refresh(c)
                    updated += 1
                    # auto-create ticket if now High/Critical and no ticket exists
                    if target_enum in (PriorityLevel.High, PriorityLevel.Critical) and not c.ticket:
                        if not dry_run:
                            t = Ticket(comment_id=c.id, title=(c.intent or 'Customer Issue')[:250], description=(c.content or '')[:2000], status=TicketStatus.open, priority=target_enum.value)
                            db.add(t)
                            db.commit()
                            db.refresh(t)
                        tickets_created += 1

        print(f"Done. Comments updated: {updated}. Tickets created: {tickets_created}")
    finally:
        db.close()

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--dry', action='store_true', help='Dry run, do not write changes')
    args = p.parse_args()
    apply_mappings(dry_run=args.dry)
