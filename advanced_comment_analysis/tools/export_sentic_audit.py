"""Export comments that match Sentic mappings to a CSV for audit/review."""
import csv
from app.database.session import SessionLocal
from app.models.sentic_mapping import SenticMapping
from app.models.comment import Comment
import app.models.user
import app.models.ticket

OUTPATH = 'tools/sentic_audit.csv'

def export():
    db = SessionLocal()
    try:
        sentics = db.query(SenticMapping).all()
        keys = {s.emotion.lower(): s.priority for s in sentics}
        print(f'Loaded {len(keys)} sentic mappings')
        comments = db.query(Comment).filter(Comment.emotion != None).all()
        rows = []
        for c in comments:
            emo = (c.emotion or '').lower()
            if emo in keys:
                rows.append({
                    'id': c.id,
                    'emotion': c.emotion,
                    'mapped_priority': keys[emo],
                    'current_priority': getattr(c.priority, 'value', str(c.priority)),
                    'needs_ticket': c.needs_ticket,
                    'confidence': c.confidence,
                    'analyzed_at': c.analyzed_at.isoformat() if c.analyzed_at else '',
                    'created_at': c.created_at.isoformat() if c.created_at else '',
                    'content': (c.content or '')[:200].replace('\n',' ')
                })
        if not rows:
            print('No comments match current sentic mappings.')
            return
        with open(OUTPATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id','emotion','mapped_priority','current_priority','needs_ticket','confidence','analyzed_at','created_at','content'])
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f'Wrote {len(rows)} rows to {OUTPATH}')
        # print sample
        for r in rows[:10]:
            print(f"id={r['id']} emo={r['emotion']} mapped={r['mapped_priority']} current={r['current_priority']} conf={r['confidence']}")
    finally:
        db.close()

if __name__ == '__main__':
    export()
