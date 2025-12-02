"""
User model with credits balance for billing system.
Implements atomic credit deductions with row-level locking to prevent race conditions.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class User(Base):
    """
    User model with credits-based billing system.
    
    Attributes:
        id: Primary key (auto-increment)
        email: Unique user email (indexed)
        credits_balance: Available credits for API usage
        is_active: Account status flag
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    
    Usage for safe credit deduction:
        # Always use with_for_update() to lock the row during transaction
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        if user.credits_balance >= cost:
            user.credits_balance -= cost
            db.commit()
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User identification
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Credits system - CRITICAL: Use with_for_update() when modifying
    credits_balance = Column(
        Integer,
        nullable=False,
        default=10,
        server_default="10",
        comment="Available credits for API usage. Default: 10 credits"
    )
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', credits={self.credits_balance})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "email": self.email,
            "credits_balance": self.credits_balance,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
