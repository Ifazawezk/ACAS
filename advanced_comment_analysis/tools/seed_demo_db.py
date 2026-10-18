#!/usr/bin/env python3
"""Seed a demo SQLite database with example data for investor demos.

Run from project root (where .venv lives):
.\.venv\Scripts\python.exe tools\seed_demo_db.py
"""
import json
from datetime import datetime, timedelta
from app.database import session as dbs
from app.models.comment import Comment, PriorityLevel
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.models.routing_rule import RoutingRule
from app.models.sentic_mapping import SenticMapping
from app.models.setting import Setting


def main():
    engine = dbs.engine
    print('Creating tables...')
    dbs.Base.metadata.create_all(bind=engine)

    db = dbs.SessionLocal()
    try:
        # Users
        print('Adding demo users...')
        admin = User(email='admin@example.com', hashed_password='demo', role=UserRole.admin)
        support = User(email='support@example.com', hashed_password='demo', role=UserRole.support)
        db.add_all([admin, support])
        db.flush()

        # Routing rules
        print('Adding routing rules...')
        rules = [
            RoutingRule(pattern='refund', priority='High', enabled=True),
            RoutingRule(pattern='bug|error|crash', priority='High', enabled=True),
            RoutingRule(pattern='feature request|feature_request', priority='Medium', enabled=True),
        ]
        db.add_all(rules)

        # Sentic mappings
        print('Adding sentic mappings...')
        sentics = [
            SenticMapping(emotion='angry', priority='Critical'),
            SenticMapping(emotion='frustrated', priority='High'),
            SenticMapping(emotion='neutral', priority='Low'),
        ]
        db.add_all(sentics)

        # Settings
        print('Adding settings...')
        cfg = Setting(key='ui_defaults', value={'theme':'dark', 'lang':'en'})
        db.add(cfg)

        db.flush()

        # Seed comments over last 24 hours
        print('Seeding comments and tickets...')
        now = datetime.utcnow()
        sample = [
            ('I want a refund, my order never arrived', 'refund', 'angry', PriorityLevel.Critical, 0.95),
            ('App crashes when I upload a photo', 'bug', 'frustrated', PriorityLevel.High, 0.87),
            ('I would love a dark mode in the app', 'feature_request', 'neutral', PriorityLevel.Medium, 0.78),
            ('How do I change my password?', 'question', 'neutral', PriorityLevel.Low, 0.92),
            ('Payment failed but money taken', 'billing', 'angry', PriorityLevel.Critical, 0.88),
            ('Feature idea: allow export of data', 'feature_request', 'neutral', PriorityLevel.Medium, 0.65),
        ]

        comments = []
        for i, (text, intent, emotion, pr, conf) in enumerate(sample * 8):
            # spread across last 24 hours
            ts = now - timedelta(hours=(i % 24), minutes=(i * 7) % 60)
            c = Comment(content=text, source='demo', intent=intent, emotion=emotion, priority=pr, confidence=conf, created_at=ts, analyzed_at=ts)
            db.add(c)
            db.flush()
            comments.append(c)
            # create a ticket for critical/high
            if pr in (PriorityLevel.Critical, PriorityLevel.High):
                t = Ticket(comment_id=c.id, title=f"Auto: {intent}", description=text[:200], status=TicketStatus.open, priority=pr, assigned_to=admin.id)
                db.add(t)

        db.commit()
        print('Database seeded successfully.')
        print('Demo users: admin@example.com / support@example.com (password: demo)')
        print('SQLite URL:', dbs.DATABASE_URL)
    finally:
        db.close()


if __name__ == '__main__':
    main()
