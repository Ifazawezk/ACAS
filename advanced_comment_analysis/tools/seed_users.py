#!/usr/bin/env python3
"""Seed database with default users including manager account."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.utils.security import hash_password

load_dotenv()


def seed_users():
    """Create default users in the database."""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if manager already exists
        existing_manager = db.query(User).filter(User.username == "maha_ebeid").first()
        manager_password = os.getenv("SEED_MANAGER_PASSWORD")
        if existing_manager:
            print("✓ Manager account already exists")
        elif not manager_password:
            print("• Skipping manager account (set SEED_MANAGER_PASSWORD to create it)")
        else:
            # Create manager account
            manager_user = User(
                username="maha_ebeid",
                email="maha_ebeid@example.com",
                hashed_password=hash_password(manager_password),
                role=UserRole.manager,
                is_active=True
            )
            db.add(manager_user)
            print(f"✓ Created manager account: maha_ebeid")

        # Create admin account if needed
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin@123"),
                role=UserRole.admin,
                is_active=True
            )
            db.add(admin_user)
            print(f"✓ Created admin account: admin (password: admin@123)")
        else:
            print("✓ Admin account already exists")

        # Create demo user account if needed
        existing_user = db.query(User).filter(User.username == "demo_user").first()
        if not existing_user:
            demo_user = User(
                username="demo_user",
                email="demo@example.com",
                hashed_password=hash_password("demo@123"),
                role=UserRole.user,
                is_active=True
            )
            db.add(demo_user)
            print(f"✓ Created demo user account: demo_user (password: demo@123)")
        else:
            print("✓ Demo user account already exists")

        db.commit()
        print("\n✅ User seeding completed successfully!\n")
        print("Default credentials:")
        print("  Manager: maha_ebeid / <SEED_MANAGER_PASSWORD>")
        print("  Admin: admin / admin@123")
        print("  User: demo_user / demo@123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
