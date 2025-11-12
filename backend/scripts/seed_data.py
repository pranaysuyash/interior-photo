"""
Database seeding script for Interior AI

Seeds the database with initial data:
- Admin user
- Sample users for testing
- Initial configuration data
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.user import User, SubscriptionTier
from app.core.security import get_password_hash
import uuid


def seed_admin_user(db):
    """Create admin user"""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@interior-ai.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")

    # Check if admin exists
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if existing_admin:
        print(f"Admin user already exists: {admin_email}")
        return

    admin = User(
        email=admin_email,
        password_hash=get_password_hash(admin_password),
        name="Admin User",
        credits=9999,
        subscription_tier=SubscriptionTier.ENTERPRISE,
        is_active=True
    )

    db.add(admin)
    db.commit()
    print(f"✓ Admin user created: {admin_email}")
    print(f"  Default password: {admin_password}")
    print(f"  PLEASE CHANGE THIS PASSWORD IMMEDIATELY!")


def seed_sample_users(db):
    """Create sample users for testing"""
    sample_users = [
        {
            "email": "free_user@example.com",
            "password": "password123",
            "name": "Free User",
            "tier": SubscriptionTier.FREE,
            "credits": 5
        },
        {
            "email": "pro_user@example.com",
            "password": "password123",
            "name": "Pro User",
            "tier": SubscriptionTier.PRO,
            "credits": 100
        },
        {
            "email": "enterprise_user@example.com",
            "password": "password123",
            "name": "Enterprise User",
            "tier": SubscriptionTier.ENTERPRISE,
            "credits": 1000
        }
    ]

    for user_data in sample_users:
        # Check if user exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"Sample user already exists: {user_data['email']}")
            continue

        user = User(
            email=user_data["email"],
            password_hash=get_password_hash(user_data["password"]),
            name=user_data["name"],
            credits=user_data["credits"],
            subscription_tier=user_data["tier"],
            is_active=True
        )

        db.add(user)
        print(f"✓ Sample user created: {user_data['email']} ({user_data['tier'].value})")

    db.commit()


def main():
    """Main seeding function"""
    print("=" * 60)
    print("Interior AI - Database Seeding")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        print("Seeding admin user...")
        seed_admin_user(db)
        print()

        # Only seed sample users in non-production environments
        if os.getenv("ENVIRONMENT", "production") != "production":
            print("Seeding sample users...")
            seed_sample_users(db)
            print()
        else:
            print("Skipping sample users (production environment)")
            print()

        print("=" * 60)
        print("Database seeding completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
