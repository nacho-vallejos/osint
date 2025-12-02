"""
Scan History Model - Audit log for all OSINT scan operations.
Stores complete scan metadata and results for compliance and user history.
"""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ScanStatus(str, enum.Enum):
    """Scan execution status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ScanHistory(Base):
    """
    Audit log table for OSINT scan operations.
    
    Stores complete scan metadata including:
    - Who performed the scan (user_id)
    - What was scanned (target, scan_type)
    - When it was performed (performed_at)
    - From where (client_ip)
    - What was the result (result_snapshot)
    
    Security Features:
    - UUID primary key (non-sequential, unpredictable)
    - Indexed user_id for fast queries by user
    - Indexed performed_at for time-range queries
    - Client IP logging for security audits
    - Immutable after creation (update only status/result)
    
    Compliance:
    - Full audit trail of all scan operations
    - Result snapshots for historical reconstruction
    - IP address tracking for security investigations
    """
    __tablename__ = "scan_history"
    
    # Primary key - UUID for security (non-sequential)
    id = Column(
        String(36),  # Store UUID as string for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique scan identifier"
    )
    
    # Foreign key to users table
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who initiated the scan"
    )
    
    # Scan parameters
    target = Column(
        String(500),
        nullable=False,
        index=True,
        comment="Scan target (domain, IP, username, email, etc.)"
    )
    
    scan_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of collector used (dns, username, metadata, etc.)"
    )
    
    # Scan status
    status = Column(
        SQLEnum(ScanStatus),
        nullable=False,
        default=ScanStatus.PENDING,
        index=True,
        comment="Current scan status"
    )
    
    # Result storage - JSON for both SQLite and PostgreSQL
    result_snapshot = Column(
        JSON,  # Works with both SQLite and PostgreSQL
        nullable=True,
        comment="Complete scan result for historical reconstruction"
    )
    
    # Error information
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if scan failed"
    )
    
    # Celery task tracking
    task_id = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Celery task ID for status tracking"
    )
    
    # Audit trail
    performed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Timestamp when scan was initiated"
    )
    
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when scan completed (success or failure)"
    )
    
    client_ip = Column(
        String(45),  # IPv6 max length
        nullable=True,
        index=True,
        comment="Client IP address for security auditing"
    )
    
    user_agent = Column(
        String(500),
        nullable=True,
        comment="User agent string for audit trail"
    )
    
    # Credits charged
    credits_charged = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of credits charged for this scan"
    )
    
    # Relationships
    user = relationship("User", backref="scan_history")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_scan_history_user_performed', 'user_id', 'performed_at'),
        Index('ix_scan_history_user_status', 'user_id', 'status'),
        Index('ix_scan_history_status_performed', 'status', 'performed_at'),
    )
    
    def __repr__(self):
        return f"<ScanHistory(id={self.id}, user_id={self.user_id}, target='{self.target}', status='{self.status}')>"
    
    def to_dict(self, include_result: bool = False):
        """
        Convert model to dictionary for API responses.
        
        Args:
            include_result: Whether to include the potentially large result_snapshot
        
        Returns:
            Dictionary representation of the scan history
        """
        data = {
            "id": str(self.id),
            "user_id": self.user_id,
            "target": self.target,
            "scan_type": self.scan_type,
            "status": self.status.value if isinstance(self.status, enum.Enum) else self.status,
            "task_id": self.task_id,
            "performed_at": self.performed_at.isoformat() if self.performed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "client_ip": self.client_ip,
            "credits_charged": self.credits_charged,
        }
        
        # Optionally include error message
        if self.error_message:
            data["error_message"] = self.error_message
        
        # Optionally include full result snapshot
        if include_result and self.result_snapshot:
            data["result_snapshot"] = self.result_snapshot
        
        return data
