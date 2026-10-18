import csv
import os
from app.database.session import SessionLocal
from app.services.ai_service import analyze_text
from app.services.comment_ticket_service import save_comment_and_analysis


def process_csv_file(path: str, source: str = "csv"):
    """Expect CSV with a header row and a `content` column."""
    db = SessionLocal()
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                content = row.get('content') or row.get('comment') or ''
                if not content:
                    continue
                analysis = analyze_text(content)
                if analysis:
                    save_comment_and_analysis(db, content, analysis.dict(), source=source)
    finally:
        db.close()
        try:
            os.remove(path)
        except Exception:
            pass
