"""
Seed database with sample user data for testing.
Run this script to populate the database with initial users.
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User
from datetime import datetime, date
import uuid


def seed_users(db: Session):
    """Create sample users."""
    users = [
        User(
            email="admin@gov.example.com",
            role="admin",
            department="Treasury Board",
            preferences={"language": "en", "notifications": True}
        ),
        User(
            email="caseworker@gov.example.com",
            role="employee",
            department="Employment and Social Development",
            preferences={"language": "en", "theme": "light"}
        ),
        User(
            email="citizen@example.com",
            role="citizen",
            preferences={"language": "en"}
        ),
    ]

    for user in users:
        db.add(user)

    db.commit()
    print(f"✓ Created {len(users)} users")
    return users


def clear_database(db: Session):
    """Clear all data from database (for testing)."""
    print("Clearing existing data...")

    # Only clear users since we're not seeding regulatory data
    db.query(User).delete()

    db.commit()
    print("✓ Database cleared")


def main():
    """Main seeding function."""
    print("\n" + "="*50)
    print("Seeding Regulatory Intelligence Database")
    print("="*50 + "\n")

    # Create database session
    db = SessionLocal()

    try:
        # Clear existing data (comment out if you want to keep existing data)
        clear_database(db)

        # Only seed users - no regulatory data
        users = seed_users(db)

        print("\n" + "="*50)
        print("✓ Database seeding completed successfully!")
        print("Note: Only users were seeded. Regulatory data should be loaded via data pipeline.")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\n✗ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
