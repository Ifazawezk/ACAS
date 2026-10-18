#!/usr/bin/env python3
"""
Generate random data for graph visualization
"""

from datetime import datetime, timedelta
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.comment import Comment, PriorityLevel
from app.models.ticket import Ticket, TicketStatus

# Sample names and content templates
NAMES = [
    "Ahmed", "Fatima", "Mohammed", "Layla", "Karim", "Noor", "Hamza", "Dina",
    "Samir", "Rania", "Omar", "Sara", "Youssef", "Hana", "Hassan", "Maryam",
    "Ali", "Zainab", "Ibrahim", "Leila", "Khalid", "Nadia", "Rashid", "Aisha"
]

SOURCES = ["email", "twitter", "facebook", "support_chat", "survey", "instagram", "whatsapp"]

EMOTIONS = ["joy", "sadness", "anger", "fear", "neutral", "surprise", "disgust"]

INTENTS = ["praise", "complaint", "suggestion", "question", "feedback", "bug_report"]

SAMPLE_CONTENTS = [
    "Your product is amazing! Highly recommend.",
    "I'm frustrated with the constant bugs and crashes.",
    "Great service but needs improvement in UI.",
    "The customer support is excellent and responsive.",
    "Pricing is too high for small businesses.",
    "Love the new features, very useful!",
    "The app keeps crashing on my device.",
    "Best solution I've found for this problem.",
    "Would love to see more reporting features.",
    "Terrible experience, switching to competitor.",
    "Good product but documentation is poor.",
    "Exceeded all my expectations!",
    "Performance issues during peak hours.",
    "Perfect integration with our workflow.",
    "Needs better mobile optimization.",
    "Outstanding customer service team.",
    "The API is well-designed and easy to use.",
    "Missing key features we need.",
    "Worth every penny we invested.",
    "Support team never responds to tickets.",
]

def generate_graph_data():
    """Generate random data for graphs"""
    db = SessionLocal()
    try:
        print("🔄 Generating random data for graphs...")
        
        # Generate 200 random comments spread across multiple dates
        for i in range(200):
            # Random date from past 90 days
            days_ago = random.randint(0, 90)
            created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            comment = Comment(
                customer_name=f"{random.choice(NAMES)} {random.choice(NAMES)}",
                source=random.choice(SOURCES),
                content=random.choice(SAMPLE_CONTENTS),
                emotion=random.choice(EMOTIONS),
                intent=random.choice(INTENTS),
                priority=random.choice(list(PriorityLevel)),
                confidence=round(random.uniform(0.75, 1.0), 2),
                created_at=created_at
            )
            db.add(comment)
        
        db.commit()
        print("✅ Added 200 random comments")
        
        # Generate 50 random tickets (linked to comments)
        ticket_templates = [
            "System performance degradation",
            "User authentication issues",
            "Data export not working",
            "UI rendering problems",
            "API rate limiting errors",
            "Database connection timeout",
            "Feature request implementation",
            "Documentation update needed",
            "Integration with third-party tool",
            "Security vulnerability report",
        ]
        
        # Get existing comments to link tickets to
        comments = db.query(Comment).all()
        
        for i in range(min(50, len(comments))):
            days_ago = random.randint(0, 90)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            ticket = Ticket(
                comment_id=comments[i].id,
                title=random.choice(ticket_templates),
                description=f"Issue #{i+1}: {random.choice(SAMPLE_CONTENTS)}",
                status=random.choice([TicketStatus.open, TicketStatus.open, TicketStatus.in_progress, TicketStatus.closed]),
                priority=random.choice(list(PriorityLevel)),
                created_at=created_at
            )
            db.add(ticket)
        
        db.commit()
        print("✅ Added 50 random tickets")
        
        print("\n" + "="*50)
        print("📊 Graph Data Generation Complete!")
        print("="*50)
        print(f"✅ Total Comments: {db.query(Comment).count()}")
        print(f"✅ Total Tickets: {db.query(Ticket).count()}")
        print("\n🎉 Your graphs should now be populated with data!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_graph_data()
