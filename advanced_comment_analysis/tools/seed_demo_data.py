#!/usr/bin/env python3
"""
Seed example data for ACAS dashboard demo
Creates realistic comments, tickets, and user data
"""

from datetime import datetime, timedelta
import random
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.comment import Comment, PriorityLevel
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User


def seed_demo_data():
    """Seed comprehensive demo data"""
    db = SessionLocal()
    try:
        # Sample comments data
        sample_comments = [
            {
                "customer_name": "Ahmed Hassan",
                "source": "email",
                "content": "Your product is amazing! The customer service was exceptional and helped me solve my problem quickly.",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.95
            },
            {
                "customer_name": "Fatima Al-Rashid",
                "source": "twitter",
                "content": "I'm really frustrated with the app crashing every time I try to export data. This is unacceptable.",
                "emotion": "anger",
                "intent": "complaint",
                "priority": PriorityLevel.High,
                "confidence": 0.92
            },
            {
                "customer_name": "Mohammed Ahmed",
                "source": "facebook",
                "content": "The new feature is interesting but could use some improvements in the UI design.",
                "emotion": "neutral",
                "intent": "suggestion",
                "priority": PriorityLevel.Medium,
                "confidence": 0.88
            },
            {
                "customer_name": "Layla Noor",
                "source": "support_chat",
                "content": "Thank you so much for the quick response! Your team is incredibly helpful and professional.",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.97
            },
            {
                "customer_name": "Karim Samir",
                "source": "email",
                "content": "I've been using this for 3 months and it has transformed how we manage comments. Excellent work!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.94
            },
            {
                "customer_name": "Noor Zakaria",
                "source": "survey",
                "content": "The pricing is too high compared to competitors. Please consider more flexible plans.",
                "emotion": "sadness",
                "intent": "feedback",
                "priority": PriorityLevel.Medium,
                "confidence": 0.85
            },
            {
                "customer_name": "Hamza Ibrahim",
                "source": "twitter",
                "content": "Just setup the dashboard - wow, the analytics are incredibly detailed! Love it!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.96
            },
            {
                "customer_name": "Dina Khalil",
                "source": "email",
                "content": "There's a bug in the sentiment analysis - it's marking negative comments as positive.",
                "emotion": "anger",
                "intent": "bug_report",
                "priority": PriorityLevel.Critical,
                "confidence": 0.91
            },
            {
                "customer_name": "Samir Aziz",
                "source": "facebook",
                "content": "When will you release the mobile app? That's the main thing we're waiting for.",
                "emotion": "neutral",
                "intent": "question",
                "priority": PriorityLevel.Medium,
                "confidence": 0.80
            },
            {
                "customer_name": "Rania Hassan",
                "source": "support_chat",
                "content": "I'm satisfied with the service, just needed a small tweak to integrate with our system.",
                "emotion": "neutral",
                "intent": "feedback",
                "priority": PriorityLevel.Low,
                "confidence": 0.87
            },
            {
                "customer_name": "Omar Khalid",
                "source": "email",
                "content": "The documentation is confusing and poorly written. Please improve it.",
                "emotion": "anger",
                "intent": "complaint",
                "priority": PriorityLevel.Medium,
                "confidence": 0.89
            },
            {
                "customer_name": "Sara Ahmed",
                "source": "twitter",
                "content": "So happy with this platform! Made our workflow 10x more efficient. Highly recommend!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.98
            },
            {
                "customer_name": "Youssef Mahmoud",
                "source": "survey",
                "content": "The system is okay but needs better reporting features for executive summaries.",
                "emotion": "neutral",
                "intent": "suggestion",
                "priority": PriorityLevel.High,
                "confidence": 0.83
            },
            {
                "customer_name": "Hana Rashid",
                "source": "email",
                "content": "I'm really unhappy with the recent update. It removed features I depend on daily.",
                "emotion": "sadness",
                "intent": "complaint",
                "priority": PriorityLevel.High,
                "confidence": 0.90
            },
            {
                "customer_name": "Tariq Hassan",
                "source": "support_chat",
                "content": "Great product! Just needed clarification on some API endpoints.",
                "emotion": "neutral",
                "intent": "question",
                "priority": PriorityLevel.Low,
                "confidence": 0.82
            },
            {
                "customer_name": "Amina Noor",
                "source": "facebook",
                "content": "Amazing customer support team! They went above and beyond to help us. 5 stars!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.99
            },
            {
                "customer_name": "Zain Khalid",
                "source": "email",
                "content": "The system keeps timing out during peak hours. This is really affecting our business.",
                "emotion": "anger",
                "intent": "complaint",
                "priority": PriorityLevel.Critical,
                "confidence": 0.93
            },
            {
                "customer_name": "Leila Samir",
                "source": "twitter",
                "content": "Just integrated with our CRM. Works like a dream. Best decision we made this year!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.95
            },
            {
                "customer_name": "Basil Ahmed",
                "source": "survey",
                "content": "The training materials could be more comprehensive and include video tutorials.",
                "emotion": "neutral",
                "intent": "suggestion",
                "priority": PriorityLevel.Medium,
                "confidence": 0.81
            },
            {
                "customer_name": "Sophia Noor",
                "source": "email",
                "content": "Thank you for the amazing onboarding experience. Your team was very helpful!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.96
            },
            {
                "customer_name": "Ibrahim Aziz",
                "source": "support_chat",
                "content": "Data export feature is broken and returning corrupted files.",
                "emotion": "anger",
                "intent": "bug_report",
                "priority": PriorityLevel.Critical,
                "confidence": 0.92
            },
            {
                "customer_name": "Maya Hassan",
                "source": "facebook",
                "content": "Love the UI updates! Much more intuitive than before. Keep up the great work!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.97
            },
            {
                "customer_name": "Aden Khalid",
                "source": "email",
                "content": "Performance has improved significantly since the last update. Excellent!",
                "emotion": "joy",
                "intent": "praise",
                "priority": PriorityLevel.Low,
                "confidence": 0.94
            },
            {
                "customer_name": "Nadia Samir",
                "source": "twitter",
                "content": "Would love to see more integration options with popular marketing platforms.",
                "emotion": "neutral",
                "intent": "suggestion",
                "priority": PriorityLevel.Medium,
                "confidence": 0.79
            },
            {
                "customer_name": "Rashid Ahmed",
                "source": "survey",
                "content": "The dashboard takes too long to load. Please optimize the performance.",
                "emotion": "anger",
                "intent": "complaint",
                "priority": PriorityLevel.High,
                "confidence": 0.88
            },
        ]

        # Get users for ticket assignment
        admin_user = db.query(User).filter(User.username == "admin").first()
        manager_user = db.query(User).filter(User.username == "maha_ebeid").first()
        
        # Clear existing data
        existing_comments = db.query(Comment).count()
        if existing_comments > 0:
            print(f"✓ Found {existing_comments} existing comments, keeping them")
        else:
            print("🆕 No existing comments found, adding new ones")

        # Add comments with distributed dates
        base_date = datetime.utcnow() - timedelta(days=60)
        created_comments = []
        
        for idx, comment_data in enumerate(sample_comments):
            # Distribute comments over the last 60 days
            days_offset = random.randint(0, 59)
            hours_offset = random.randint(0, 23)
            created_at = base_date + timedelta(days=days_offset, hours=hours_offset)
            
            comment = Comment(
                customer_name=comment_data["customer_name"],
                source=comment_data["source"],
                content=comment_data["content"],
                emotion=comment_data["emotion"],
                intent=comment_data["intent"],
                priority=comment_data["priority"],
                confidence=comment_data["confidence"],
                needs_ticket=comment_data["priority"] in [PriorityLevel.High, PriorityLevel.Critical],
                created_at=created_at,
                analyzed_at=created_at + timedelta(seconds=random.randint(1, 30))
            )
            
            db.add(comment)
            db.flush()  # Get the ID
            created_comments.append((comment, created_at))
        
        db.commit()
        print(f"✅ Added {len(created_comments)} comments")

        # Create tickets from comments that need them
        critical_issues = ["anger", "bug_report"]
        ticket_titles = {
            "bug_report": "Bug Report: System Issue",
            "complaint": "Customer Complaint Resolution",
            "question": "Customer Inquiry",
            "suggestion": "Feature Suggestion",
        }

        tickets_created = 0
        for comment, comment_date in created_comments:
            if comment.needs_ticket or comment.emotion in critical_issues:
                # Assign to random user
                assigned_to = random.choice([admin_user.id, manager_user.id]) if admin_user and manager_user else None
                
                ticket_status = random.choice([
                    TicketStatus.open,
                    TicketStatus.open,
                    TicketStatus.in_progress,
                    TicketStatus.closed
                ])
                
                closed_date = None
                if ticket_status == TicketStatus.closed:
                    closed_date = comment_date + timedelta(days=random.randint(1, 14))
                
                ticket = Ticket(
                    comment_id=comment.id,
                    title=f"{ticket_titles.get(comment.intent, 'Support Ticket')}: {comment.customer_name}",
                    description=f"Auto-generated from comment: {comment.content[:100]}...",
                    status=ticket_status,
                    priority=comment.priority.value,
                    assigned_to=assigned_to,
                    created_at=comment_date,
                    closed_at=closed_date
                )
                
                db.add(ticket)
                tickets_created += 1
        
        db.commit()
        print(f"✅ Created {tickets_created} support tickets")

        # Print summary
        total_comments = db.query(Comment).count()
        positive = db.query(Comment).filter(Comment.emotion.in_(["joy", "surprise"])).count()
        negative = db.query(Comment).filter(Comment.emotion.in_(["anger", "sadness"])).count()
        neutral = db.query(Comment).filter(Comment.emotion == "neutral").count()
        
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.open).count()
        closed_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.closed).count()

        print("\n" + "="*50)
        print("📊 DEMO DATA SUMMARY")
        print("="*50)
        print(f"\n💬 Comments: {total_comments} total")
        print(f"   ✅ Positive: {positive} ({positive*100//total_comments}%)")
        print(f"   ❌ Negative: {negative} ({negative*100//total_comments}%)")
        print(f"   ⚪ Neutral: {neutral} ({neutral*100//total_comments}%)")
        
        print(f"\n🎫 Tickets: {total_tickets} total")
        print(f"   🟢 Open: {open_tickets}")
        print(f"   🔵 Closed: {closed_tickets}")
        
        print(f"\n🎉 Demo data successfully seeded!")
        print("="*50)

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
