#!/usr/bin/env python3
"""
Comprehensive preview data seeder - creates realistic sample data for dashboard preview
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.comment import Comment
from app.models.ticket import Ticket, TicketStatus
from app.models.routing_rule import RoutingRule as RoutingRuleModel
from app.models.sentic_mapping import SenticMapping
from app.models.setting import Setting

# Sample comment templates
COMMENT_TEMPLATES = [
    ("I've been trying to get a refund for my order for 2 weeks!", "refund", "angry", "request"),
    ("The shipping cost is way too high, almost double what competitors charge.", "shipping", "frustrated", "complaint"),
    ("Your customer service was amazing! Issue resolved in minutes.", "support", "happy", "praise"),
    ("When will the new features be available?", "features", "neutral", "question"),
    ("The app keeps crashing on my phone, this is unacceptable.", "bug", "angry", "complaint"),
    ("Is there a bulk discount for orders over 100 units?", "pricing", "neutral", "question"),
    ("Love the new UI! Much more intuitive than before.", "ui", "happy", "praise"),
    ("I was charged twice for the same transaction", "billing", "upset", "complaint"),
    ("How long does standard shipping usually take?", "shipping", "neutral", "question"),
    ("Product quality has really gone downhill lately", "quality", "sad", "complaint"),
    ("Can I cancel my subscription anytime?", "subscription", "neutral", "question"),
    ("Your product saved me so much time!", "product", "happy", "praise"),
    ("The checkout process is confusing and slow", "ux", "frustrated", "complaint"),
    ("Do you offer student discounts?", "pricing", "neutral", "question"),
    ("This is the best purchase I've made all year", "product", "happy", "praise"),
    ("The mobile app is completely unusable on Android", "bug", "angry", "complaint"),
    ("What payment methods do you accept?", "billing", "neutral", "question"),
    ("Finally, a product that actually works as advertised!", "product", "happy", "praise"),
    ("My order has been stuck in processing for a week", "shipping", "frustrated", "complaint"),
    ("Are there any promo codes available right now?", "pricing", "neutral", "question"),
    ("The documentation is unclear and confusing", "support", "frustrated", "complaint"),
    ("Customer support responded immediately to my issue!", "support", "happy", "praise"),
    ("Will this feature be available on the free plan?", "features", "neutral", "question"),
    ("I'm very disappointed with the recent changes", "product", "sad", "complaint"),
    ("This feature is exactly what we needed!", "features", "happy", "praise"),
    ("The login system has been broken for days", "bug", "angry", "complaint"),
    ("How do I export my data?", "features", "neutral", "question"),
    ("Excellent work on the latest update!", "product", "happy", "praise"),
    ("Your competitors offer better service for less money", "pricing", "frustrated", "complaint"),
    ("Is there a way to get a refund after 30 days?", "refund", "neutral", "question"),
    ("The new dashboard is phenomenal!", "ui", "happy", "praise"),
    ("I can't find my account settings anywhere", "ux", "frustrated", "complaint"),
    ("What's the average response time for support tickets?", "support", "neutral", "question"),
    ("This is my go-to product now", "product", "happy", "praise"),
    ("The API documentation is outdated and useless", "support", "angry", "complaint"),
    ("Do you have a roadmap for future features?", "features", "neutral", "question"),
    ("I'm impressed with how quickly you fixed the issue", "support", "happy", "praise"),
    ("The performance has gotten worse with each update", "product", "frustrated", "complaint"),
    ("Can you add dark mode to the interface?", "features", "neutral", "request"),
    ("Five stars! Couldn't be happier!", "product", "happy", "praise"),
    ("Critical security issue needs immediate attention", "bug", "angry", "complaint"),
    ("When can I expect a response to my support ticket?", "support", "neutral", "question"),
    ("Your team goes above and beyond every time", "support", "happy", "praise"),
    ("Still waiting for the promised feature from last month", "features", "frustrated", "complaint"),
    ("Is the tool compatible with Windows 11?", "features", "neutral", "question"),
    ("Worth every penny! Highly recommend!", "product", "happy", "praise"),
    ("The UI is outdated and looks unprofessional", "ui", "sad", "complaint"),
    ("How do I contact the sales team?", "support", "neutral", "question"),
    ("Best product in its category hands down", "product", "happy", "praise"),
]

EMOTIONS = ["happy", "neutral", "sad", "angry", "frustrated", "upset"]
INTENTS = ["complaint", "question", "praise", "request"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

def seed_database():
    """Clear and seed with realistic preview data"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Comment).delete()
        db.query(Ticket).delete()
        db.query(RoutingRuleModel).delete()
        db.query(SenticMapping).delete()
        db.query(User).delete()
        db.query(Setting).delete()
        db.commit()
        print("Cleared existing data")
        
        # Create users
        admin = User(
            email="admin@example.com",
            hashed_password="$2b$12$fake_hash_admin",
            role=UserRole.admin,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Created admin user")
        
        # Create routing rules
        rules = [
            RoutingRuleModel(pattern="refund", priority="High", enabled=True),
            RoutingRuleModel(pattern="billing", priority="High", enabled=True),
            RoutingRuleModel(pattern="bug", priority="Critical", enabled=True),
            RoutingRuleModel(pattern="shipping", priority="Medium", enabled=True),
            RoutingRuleModel(pattern="support", priority="Low", enabled=True),
        ]
        db.add_all(rules)
        db.commit()
        print(f"Created {len(rules)} routing rules")
        
        # Create sentic mappings
        mappings = [
            SenticMapping(emotion="angry", priority="High"),
            SenticMapping(emotion="frustrated", priority="Medium"),
            SenticMapping(emotion="happy", priority="Low"),
        ]
        db.add_all(mappings)
        db.commit()
        print(f"Created {len(mappings)} sentic mappings")
        
        # Create 250 comments spread over last 24 hours
        comments = []
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        for i in range(250):
            # Spread comments across 24 hours
            created_at = base_time + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            template = random.choice(COMMENT_TEMPLATES)
            emotion = random.choice(EMOTIONS)
            intent = random.choice(INTENTS)
            priority = random.choice(PRIORITIES)
            confidence = round(random.uniform(0.65, 0.99), 2)
            
            comment = Comment(
                customer_name=f"Customer {i+1}",
                source=random.choice(["email", "chat", "social", "ui"]),
                content=template[0],
                emotion=emotion,
                intent=intent,
                priority=priority,
                confidence=confidence,
                suggested_response="Thank you for your feedback. We're working on improving this.",
                needs_ticket=priority in ["High", "Critical"],
                created_at=created_at,
                analyzed_at=created_at + timedelta(seconds=random.randint(1, 30))
            )
            comments.append(comment)
        
        db.add_all(comments)
        db.commit()
        print(f"Created {len(comments)} comments")
        
        # Create tickets for high/critical comments
        tickets = []
        high_critical_comments = [c for c in comments if c.priority in ["High", "Critical"]]
        
        for comment in high_critical_comments[:60]:  # Create tickets for first 60 high/critical
            status = random.choice([TicketStatus.open, TicketStatus.in_progress])
            
            ticket = Ticket(
                comment_id=comment.id,
                title=f"Ticket for comment {comment.id}: {comment.content[:50]}",
                description=f"Auto-created from sentiment analysis. Emotion: {comment.emotion}",
                priority=comment.priority,
                status=status,
                assigned_to=admin.id if status == TicketStatus.in_progress else None,
                created_at=comment.created_at + timedelta(seconds=random.randint(5, 60)),
            )
            tickets.append(ticket)
        
        db.add_all(tickets)
        db.commit()
        print(f"Created {len(tickets)} tickets")
        
        # Create settings
        settings = [
            Setting(key="ai_enabled", value="true"),
            Setting(key="auto_routing_enabled", value="true"),
            Setting(key="sentic_mapping_enabled", value="true"),
        ]
        db.add_all(settings)
        db.commit()
        print(f"Created {len(settings)} settings")
        
        # Get statistics
        comment_count = db.query(Comment).count()
        ticket_count = db.query(Ticket).count()
        rule_count = db.query(RoutingRuleModel).count()
        sentic_count = db.query(SenticMapping).count()
        
        print("\n" + "="*50)
        print("PREVIEW DATA SEEDING COMPLETE")
        print("="*50)
        print(f"Comments:      {comment_count}")
        print(f"Tickets:       {ticket_count}")
        print(f"Routing Rules: {rule_count}")
        print(f"Sentic Maps:   {sentic_count}")
        print("="*50)
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
