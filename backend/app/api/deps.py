"""
API Dependencies for authentication, authorization, and billing.
Provides reusable dependencies for FastAPI endpoints.
"""
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional, Callable
from functools import wraps

from app.database import get_db
from app.models.user import User


async def get_current_user_id(
    x_user_id: Optional[str] = Header(None, description="User ID from authentication header")
) -> int:
    """
    Extract user ID from request header.
    
    In production, this would validate JWT tokens and extract user_id from claims.
    For development/testing, accepts X-User-Id header directly.
    
    Args:
        x_user_id: User ID from X-User-Id header
    
    Returns:
        int: Authenticated user's ID
    
    Raises:
        HTTPException(401): If no valid authentication is provided
    
    Usage:
        @app.get("/protected")
        async def protected_route(user_id: int = Depends(get_current_user_id)):
            ...
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication header. Provide X-User-Id header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from database.
    
    Args:
        user_id: User ID from authentication
        db: Database session
    
    Returns:
        User: Current user object
    
    Raises:
        HTTPException(401): If user not found
        HTTPException(403): If user account is inactive
    
    Usage:
        @app.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user.to_dict()
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


def check_and_deduct_credits(cost: int):
    """
    Factory function that creates a dependency to check and deduct credits.
    
    This implements ATOMIC credit deduction with row-level locking to prevent
    race conditions when users send parallel requests.
    
    Args:
        cost: Number of credits to deduct for this operation
    
    Returns:
        Callable: Dependency function that performs the credit check and deduction
    
    Raises:
        HTTPException(402): If user has insufficient credits
        HTTPException(500): If database transaction fails
    
    Usage:
        @app.post("/scan")
        async def create_scan(
            _: None = Depends(check_and_deduct_credits(cost=5)),
            current_user: User = Depends(get_current_user)
        ):
            # Credits have been deducted at this point
            ...
    
    Technical Details:
        - Uses SELECT ... FOR UPDATE to lock the user row
        - Prevents concurrent requests from reading stale balance
        - Transaction is automatically rolled back on exception
        - Lock is released after commit or rollback
    """
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """
        Inner dependency that performs the actual credit check and deduction.
        """
        try:
            # CRITICAL: Lock the user row for update
            # This prevents other transactions from reading/writing this row
            # until our transaction completes (commit or rollback)
            user = db.query(User).filter(
                User.id == current_user.id
            ).with_for_update().first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found during credit check"
                )
            
            # Check if user has enough credits
            if user.credits_balance < cost:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Insufficient credits. Required: {cost}, Available: {user.credits_balance}",
                    headers={
                        "X-Credits-Required": str(cost),
                        "X-Credits-Available": str(user.credits_balance),
                        "X-Credits-Needed": str(cost - user.credits_balance)
                    }
                )
            
            # Deduct credits atomically
            user.credits_balance -= cost
            db.commit()
            db.refresh(user)
            
            return user
            
        except HTTPException:
            # Re-raise HTTP exceptions (401, 402)
            db.rollback()
            raise
        except Exception as e:
            # Rollback on any other error
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process credit transaction: {str(e)}"
            )
    
    return dependency


async def get_user_credits(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Simple dependency to get user's current credit balance.
    Does not lock or modify the balance.
    
    Returns:
        dict: User credits information
    
    Usage:
        @app.get("/credits")
        async def get_credits(credits_info: dict = Depends(get_user_credits)):
            return credits_info
    """
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "credits_balance": current_user.credits_balance,
        "is_active": current_user.is_active
    }
