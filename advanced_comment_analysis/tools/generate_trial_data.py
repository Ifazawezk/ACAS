#!/usr/bin/env python3
"""
Generate comprehensive trial data for at least 50 unique people
Populates inbox, comments, and tickets
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
from app.models.user import User

# 60+ unique names database
FIRST_NAMES = [
    "Ahmed", "Fatima", "Mohammed", "Layla", "Karim", "Noor", "Hamza", "Dina",
    "Samir", "Rania", "Omar", "Sara", "Youssef", "Hana", "Hassan", "Maryam",
    "Ali", "Zainab", "Ibrahim", "Leila", "Khalid", "Nadia", "Rashid", "Aisha",
    "Jamal", "Huda", "Tariq", "Amira", "Fadi", "Reema", "Walid", "Laila",
    "Bilal", "Mona", "Nasir", "Samira", "Majid", "Leen", "Akram", "Noor",
    "Rafiq", "Farida", "Imran", "Lina", "Jarir", "Maha", "Amin", "Reem",
    "Ehab", "Sally", "Sami", "Judy", "Kamel", "Vera", "Nathan", "Zara",
    "Marcus", "Elena", "David", "Sofia", "James", "Emma", "Robert", "Olivia"
]

LAST_NAMES = [
    "Hassan", "Ahmed", "Mohammed", "Ali", "Khan", "Ibrahim", "Abdullah", "Khalil",
    "Samir", "Rashid", "Kareem", "Nasir", "Saleh", "Faisal", "Malik", "Adel",
    "Jamal", "Waad", "Habib", "Saad", "Nabil", "Tariq", "Rafiq", "Ameen",
    "Wilson", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"
]

# Various comment templates with placeholders
SOURCES = ["email", "twitter", "facebook", "support_chat", "survey", "instagram", "whatsapp", "linkedin"]

EMOTIONS = ["joy", "sadness", "anger", "fear", "neutral", "surprise", "disgust"]

INTENTS = ["praise", "complaint", "suggestion", "question", "feedback", "bug_report"]

# Various comment templates with placeholders
COMMENT_TEMPLATES = [
    "Your product is {adj}! I've been using it for {time} and it's {adj}.",
    "I'm {emotion} with {issue}. Please fix this ASAP.",
    "The {feature} feature is {adj} but could use {improvement}.",
    "Customer support was {adj}. They helped me {action}.",
    "The {aspect} is too {quality}. We need {solution}.",
    "Love the new {feature}! This {action} my workflow.",
    "The app keeps {issue}. This is {adj}.",
    "Best {category} I've found for {purpose}.",
    "Would love to see {feature} in the next update.",
    "Can't believe how {adj} this is. {statement}",
    "The documentation is {quality}. Please improve it.",
    "I've been a customer for {time} and this is {opinion}.",
    "The integration with {service} is {quality}.",
    "Performance issues during {time_range}.",
    "Exceeded my expectations! {recommendation}",
    "Support team never {action}. Very disappointed.",
    "The API is {adj}. {statement}",
    "Missing key features we need for {purpose}.",
    "Worth every penny. {statement}",
    "The {aspect} makes it {impact}.",
]

ADJECTIVES = ["amazing", "great", "excellent", "awesome", "perfect", "terrible", "awful", "poor", "confusing", "intuitive"]
EMOTIONS_TEXT = ["frustrated", "happy", "angry", "confused", "satisfied", "disappointed"]
ISSUES = ["crashes", "lags", "doesn't save", "connection drops", "errors", "bugs"]
FEATURES = ["dashboard", "reporting", "analytics", "API", "mobile app", "export", "integration"]
TIME_PERIODS = ["3 months", "6 months", "1 year", "2 years", "a week"]
IMPROVEMENTS = ["improvements in UI", "better documentation", "more features", "faster performance", "mobile support"]
QUALITIES = ["high", "low", "poor", "excellent", "adequate"]
SOLUTIONS = ["additional features", "price adjustment", "better support", "mobile version"]
ACTIONS = ["transformed", "changed", "improved", "disrupted"]
STATEMENTS = ["Highly recommend!", "This changed everything!", "Best investment ever!", "A game changer!"]
RECOMMENDATIONS = ["Highly recommend to others!", "Tell all your friends!", "Worth the investment!"]
SERVICES = ["Slack", "Teams", "Salesforce", "HubSpot", "Zapier"]
TIME_RANGES = ["peak hours", "weekends", "evenings", "weekdays"]
REQUESTS = ["Please optimize.", "This needs fixing.", "Very frustrating."]
CATEGORIES = ["solution", "product", "tool", "platform"]
PURPOSES = ["managing comments", "analyzing sentiment", "ticket routing", "team collaboration"]
OPINIONS = ["the best", "incredible", "a life saver", "essential"]
ASPECTS = ["pricing", "UI", "performance", "documentation", "support"]
IMPACTS = ["amazing", "frustrating", "essential", "game-changing"]

def generate_comment_content():
    """Generate realistic comment content"""
    template = random.choice(COMMENT_TEMPLATES)
    try:
        content = template.format(
            adj=random.choice(ADJECTIVES),
            emotion=random.choice(EMOTIONS_TEXT),
            issue=random.choice(ISSUES),
            feature=random.choice(FEATURES),
            improvement=random.choice(IMPROVEMENTS),
            time=random.choice(TIME_PERIODS),
            quality=random.choice(QUALITIES),
            solution=random.choice(SOLUTIONS),
            action=random.choice(ACTIONS),
            statement=random.choice(STATEMENTS),
            recommendation=random.choice(RECOMMENDATIONS),
            service=random.choice(SERVICES),
            category=random.choice(CATEGORIES),
            purpose=random.choice(PURPOSES),
            opinion=random.choice(OPINIONS),
            aspect=random.choice(ASPECTS),
            impact=random.choice(IMPACTS),
            time_range=random.choice(TIME_RANGES),
        )
    except KeyError:
        # Fallback if template has undefined variables
        content = f"Customer feedback: {random.choice(ADJECTIVES)} experience with our service"
    return content

def generate_trial_data():
    """Generate comprehensive trial data for 60+ unique people"""
    db = SessionLocal()
    try:
        print("🔄 Generating comprehensive trial data...")
        print(f"📊 Generating data for {len(FIRST_NAMES)} unique people\n")
        
        # Generate 1 comment per unique person (60+) + extra comments for variety
        comments_created = 0
        
        # Create 1-3 comments per person for 60+ people
        unique_people = set()
        for first in FIRST_NAMES:
            for last in random.sample(LAST_NAMES, min(3, len(LAST_NAMES))):
                unique_people.add(f"{first} {last}")
                if len(unique_people) >= 80:
                    break
            if len(unique_people) >= 80:
                break
        
        print(f"✅ Generated {len(unique_people)} unique people names")
        
        # Create comments for each person
        for person_name in sorted(unique_people):
            # 1-3 comments per person
            num_comments = random.randint(1, 3)
            
            for comment_idx in range(num_comments):
                days_ago = random.randint(0, 180)
                created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
                
                comment = Comment(
                    customer_name=person_name,
                    source=random.choice(SOURCES),
                    content=generate_comment_content(),
                    emotion=random.choice(EMOTIONS),
                    intent=random.choice(INTENTS),
                    priority=random.choice(list(PriorityLevel)),
                    confidence=round(random.uniform(0.75, 1.0), 2),
                    created_at=created_at
                )
                db.add(comment)
                comments_created += 1
                
                if comments_created % 50 == 0:
                    db.commit()
                    print(f"  ✓ {comments_created} comments created...")
        
        db.commit()
        print(f"\n✅ Created {comments_created} total comments from {len(unique_people)} unique people")
        
        # Create tickets for high/critical priority comments
        print("\n🎫 Creating tickets for high-priority items...")
        high_critical_comments = db.query(Comment).filter(
            Comment.priority.in_(['High', 'Critical'])
        ).all()
        
        tickets_created = 0
        for comment in high_critical_comments[:100]:  # Create tickets for first 100 high/critical items
            if random.random() > 0.3:  # 70% of high/critical get tickets
                ticket = Ticket(
                    comment_id=comment.id,
                    title=f"{comment.intent or 'Issue'}: {comment.content[:50]}",
                    description=comment.content[:200],
                    status=random.choice([TicketStatus.open, TicketStatus.open, TicketStatus.in_progress]),
                    priority=comment.priority,
                )
                db.add(ticket)
                tickets_created += 1
                
                if tickets_created % 20 == 0:
                    db.commit()
                    print(f"  ✓ {tickets_created} tickets created...")
        
        db.commit()
        print(f"✅ Created {tickets_created} tickets")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TRIAL DATA GENERATION COMPLETE!")
        print("="*60)
        total_comments = db.query(Comment).count()
        total_tickets = db.query(Ticket).count()
        print(f"✅ Total Comments: {total_comments}")
        print(f"✅ Total Unique People: {len(unique_people)}")
        print(f"✅ Total Tickets: {total_tickets}")
        print(f"\n📧 Inbox is ready with data from {len(unique_people)} unique people!")
        print(f"💬 Comment breakdown:")
        
        # Emotion breakdown
        emotion_counts = {}
        for comment in db.query(Comment).all():
            emotion = comment.emotion or "unknown"
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {emotion}: {count}")
        
        print(f"\n🎫 Ticket breakdown:")
        priority_counts = {}
        for ticket in db.query(Ticket).all():
            priority = ticket.priority or "unknown"
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {priority}: {count}")
        
        print("\n" + "="*60)
        print("🎉 All systems ready! Refresh your dashboard to see the data.")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generate_trial_data()
