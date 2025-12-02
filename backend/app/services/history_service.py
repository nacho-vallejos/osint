"""
Scan History Service - Business logic for managing scan audit logs.
Provides functions to create and update scan history records.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.history import ScanHistory, ScanStatus
from app.models.user import User


def create_scan_log(
    db: Session,
    user_id: int,
    target: str,
    scan_type: str,
    task_id: str,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    credits_charged: int = 0
) -> ScanHistory:
    """
    Create a new scan history log entry.
    
    Called when a scan is initiated (POST /scan).
    Creates a record with PENDING status that will be updated when the scan completes.
    
    Args:
        db: Database session
        user_id: ID of the user initiating the scan
        target: Scan target (domain, IP, username, etc.)
        scan_type: Type of collector used
        task_id: Celery task ID for tracking
        client_ip: Client IP address for security auditing
        user_agent: User agent string from request
        credits_charged: Number of credits charged for this scan
    
    Returns:
        Created ScanHistory instance
    
    Example:
        scan_log = create_scan_log(
            db=db,
            user_id=current_user.id,
            target="example.com",
            scan_type="dns",
            task_id=task.id,
            client_ip=request.client.host,
            credits_charged=5
        )
    """
    scan_log = ScanHistory(
        id=uuid.uuid4(),
        user_id=user_id,
        target=target,
        scan_type=scan_type,
        status=ScanStatus.PENDING,
        task_id=task_id,
        client_ip=client_ip,
        user_agent=user_agent,
        credits_charged=credits_charged,
        performed_at=datetime.utcnow()
    )
    
    db.add(scan_log)
    db.commit()
    db.refresh(scan_log)
    
    return scan_log


def update_scan_log(
    db: Session,
    task_id: str,
    status: ScanStatus,
    result_snapshot: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> Optional[ScanHistory]:
    """
    Update a scan history log with final status and result.
    
    Called when a Celery task completes (success or failure).
    Updates the log with the final status and stores the result snapshot.
    
    Args:
        db: Database session
        task_id: Celery task ID to locate the log entry
        status: Final status (SUCCESS, FAILED, CANCELLED)
        result_snapshot: Complete scan result for historical reconstruction
        error_message: Error message if scan failed
    
    Returns:
        Updated ScanHistory instance or None if not found
    
    Example:
        # On success
        update_scan_log(
            db=db,
            task_id=task_id,
            status=ScanStatus.SUCCESS,
            result_snapshot={"collector_name": "DNSCollector", "data": {...}}
        )
        
        # On failure
        update_scan_log(
            db=db,
            task_id=task_id,
            status=ScanStatus.FAILED,
            error_message="Connection timeout"
        )
    """
    scan_log = db.query(ScanHistory).filter(ScanHistory.task_id == task_id).first()
    
    if not scan_log:
        return None
    
    # Update status and completion time
    scan_log.status = status
    scan_log.completed_at = datetime.utcnow()
    
    # Store result if provided
    if result_snapshot is not None:
        scan_log.result_snapshot = result_snapshot
    
    # Store error message if provided
    if error_message is not None:
        scan_log.error_message = error_message
    
    db.commit()
    db.refresh(scan_log)
    
    return scan_log


def get_user_scan_history(
    db: Session,
    user_id: int,
    page: int = 1,
    limit: int = 10,
    status_filter: Optional[ScanStatus] = None
) -> tuple[list[ScanHistory], int]:
    """
    Get paginated scan history for a specific user.
    
    Security: Only returns scans belonging to the specified user.
    
    Args:
        db: Database session
        user_id: User ID to filter by
        page: Page number (1-indexed)
        limit: Number of results per page
        status_filter: Optional status filter
    
    Returns:
        Tuple of (list of ScanHistory records, total count)
    
    Example:
        scans, total = get_user_scan_history(db, user_id=1, page=1, limit=10)
        pages = (total + limit - 1) // limit
    """
    query = db.query(ScanHistory).filter(ScanHistory.user_id == user_id)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(ScanHistory.status == status_filter)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    offset = (page - 1) * limit
    scans = query.order_by(ScanHistory.performed_at.desc()).offset(offset).limit(limit).all()
    
    return scans, total


def get_scan_by_id(
    db: Session,
    scan_id: str,
    user_id: int
) -> Optional[ScanHistory]:
    """
    Get a specific scan by ID.
    
    Security: Verifies that the scan belongs to the specified user.
    
    Args:
        db: Database session
        scan_id: Scan UUID
        user_id: User ID for ownership verification
    
    Returns:
        ScanHistory instance or None if not found or not owned by user
    
    Example:
        scan = get_scan_by_id(db, scan_id="abc-123", user_id=1)
        if not scan:
            raise HTTPException(404, "Scan not found")
    """
    return db.query(ScanHistory).filter(
        ScanHistory.id == scan_id,
        ScanHistory.user_id == user_id  # Security: ensure ownership
    ).first()


def get_scan_statistics(
    db: Session,
    user_id: int
) -> Dict[str, Any]:
    """
    Get scan statistics for a user.
    
    Returns counts by status and total credits spent.
    
    Args:
        db: Database session
        user_id: User ID to get statistics for
    
    Returns:
        Dictionary with statistics
    
    Example:
        stats = get_scan_statistics(db, user_id=1)
        # {
        #     "total_scans": 50,
        #     "pending": 2,
        #     "success": 45,
        #     "failed": 3,
        #     "total_credits_spent": 250
        # }
    """
    from sqlalchemy import func
    
    # Get counts by status
    status_counts = db.query(
        ScanHistory.status,
        func.count(ScanHistory.id).label('count')
    ).filter(
        ScanHistory.user_id == user_id
    ).group_by(ScanHistory.status).all()
    
    # Get total credits spent
    total_credits = db.query(
        func.sum(ScanHistory.credits_charged)
    ).filter(
        ScanHistory.user_id == user_id
    ).scalar() or 0
    
    # Build statistics dictionary
    stats = {
        "total_scans": sum(count for _, count in status_counts),
        "total_credits_spent": total_credits,
    }
    
    # Add counts by status
    for status, count in status_counts:
        status_key = status.value.lower() if isinstance(status, ScanStatus) else status.lower()
        stats[status_key] = count
    
    return stats
