#!/usr/bin/env python3
"""
Database Initialization Script
Creates tables and seeds test users with credits.
"""
import sys
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base, init_db
from app.models.user import User


def create_test_users(db: Session):
    """Create test users with different credit balances"""
    
    test_users = [
        {"email": "test@example.com", "credits_balance": 100, "is_active": True},
        {"email": "admin@example.com", "credits_balance": 1000, "is_active": True},
        {"email": "premium@example.com", "credits_balance": 500, "is_active": True},
        {"email": "basic@example.com", "credits_balance": 10, "is_active": True},
        {"email": "broke@example.com", "credits_balance": 0, "is_active": True},
        {"email": "inactive@example.com", "credits_balance": 50, "is_active": False},
    ]
    
    created = 0
    skipped = 0
    
    for user_data in test_users:
        # Check if user already exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"⏭  User '{user_data['email']}' already exists (ID: {existing.id}, Credits: {existing.credits_balance})")
            skipped += 1
            continue
        
        # Create new user
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✓ Created user: {user.email} (ID: {user.id}, Credits: {user.credits_balance}, Active: {user.is_active})")
        created += 1
    
    return created, skipped


def main():
    """Initialize database and create test data"""
    print("=" * 70)
    print("DATABASE INITIALIZATION")
    print("=" * 70)
    
    # Create tables
    print("\n[1/2] Creating database tables...")
    try:
        init_db()
        print("✓ All tables created successfully\n")
    except Exception as e:
        print(f"✗ Failed to create tables: {e}")
        sys.exit(1)
    
    # Create test users
    print("[2/2] Creating test users...")
    db = SessionLocal()
    try:
        created, skipped = create_test_users(db)
        print(f"\n✓ Database initialization complete!")
        print(f"  - Users created: {created}")
        print(f"  - Users skipped: {skipped}")
    except Exception as e:
        print(f"✗ Failed to create test users: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    
    # Display usage instructions
    print("\n" + "=" * 70)
    print("USAGE INSTRUCTIONS")
    print("=" * 70)
    print("\nTo make API requests, include the X-User-Id header:")
    print("\n  curl -X POST http://localhost:8000/api/v1/scan \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -H 'X-User-Id: 1' \\")
    print("    -d '{\"target\": \"example.com\", \"type\": \"dns\"}'")
    
    print("\nTest user credentials:")
    db = SessionLocal()
    users = db.query(User).all()
    for user in users:
        status = "✓ Active" if user.is_active else "✗ Inactive"
        print(f"  - ID {user.id}: {user.email:25s} | {user.credits_balance:4d} credits | {status}")
    db.close()
    
    print("\nCheck credits balance:")
    print("  curl http://localhost:8000/api/v1/credits -H 'X-User-Id: 1'")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
