"""
History Router - API endpoints for scan history and audit logs.
Provides secure access to user's scan history with pagination.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.history import ScanStatus
from app.models.history_schemas import (
    ScanHistoryListResponse,
    ScanHistoryDetail,
    ScanHistorySummary,
    ScanStatistics,
    ScanStatusEnum
)
from app.services.history_service import (
    get_user_scan_history,
    get_scan_by_id,
    get_scan_statistics
)

router = APIRouter()


@router.get(
    "/history",
    response_model=ScanHistoryListResponse,
    summary="Get Scan History",
    description="Get paginated list of user's scan history (newest first)"
)
async def get_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Results per page (max 100)"),
    status: Optional[ScanStatusEnum] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ScanHistoryListResponse:
    """
    Get user's scan history with pagination.
    
    **Security:** Users can only see their own scans.
    
    **Pagination:**
    - Default: 10 results per page
    - Maximum: 100 results per page
    - Results ordered by performed_at (newest first)
    
    **Filtering:**
    - Optional status filter (PENDING, SUCCESS, FAILED, etc.)
    
    Args:
        page: Page number (starts at 1)
        limit: Number of results per page
        status: Optional status filter
        current_user: Authenticated user (from dependency)
        db: Database session
    
    Returns:
        Paginated list of scan summaries
    
    Example:
        GET /api/v1/history?page=1&limit=10&status=SUCCESS
        Headers:
            X-User-Id: 1
        
        Response:
        {
            "scans": [
                {
                    "id": "abc-123",
                    "target": "example.com",
                    "scan_type": "dns",
                    "status": "SUCCESS",
                    "performed_at": "2025-12-01T10:30:00Z",
                    "credits_charged": 5
                }
            ],
            "total": 50,
            "page": 1,
            "limit": 10,
            "pages": 5
        }
    """
    try:
        # Convert string status to enum if provided
        status_filter = None
        if status:
            status_filter = ScanStatus[status.value]
        
        # Get paginated scan history (security: filtered by current_user.id)
        scans, total = get_user_scan_history(
            db=db,
            user_id=current_user.id,
            page=page,
            limit=limit,
            status_filter=status_filter
        )
        
        # Calculate total pages
        pages = (total + limit - 1) // limit if total > 0 else 0
        
        # Convert to response models
        scan_summaries = [
            ScanHistorySummary(
                id=str(scan.id),
                target=scan.target,
                scan_type=scan.scan_type,
                status=scan.status,
                task_id=scan.task_id,
                performed_at=scan.performed_at,
                completed_at=scan.completed_at,
                credits_charged=scan.credits_charged,
                error_message=scan.error_message
            )
            for scan in scans
        ]
        
        return ScanHistoryListResponse(
            scans=scan_summaries,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve scan history: {str(e)}"
        )


@router.get(
    "/history/{scan_id}",
    response_model=ScanHistoryDetail,
    summary="Get Scan Details",
    description="Get complete details of a specific scan including full result snapshot"
)
async def get_scan_details(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ScanHistoryDetail:
    """
    Get complete details of a specific scan.
    
    **Security:** Users can only access their own scans.
    
    Returns the full scan result snapshot for historical reconstruction.
    This endpoint may return large payloads for scans with extensive results.
    
    Args:
        scan_id: UUID of the scan
        current_user: Authenticated user (from dependency)
        db: Database session
    
    Returns:
        Complete scan details including result snapshot
    
    Raises:
        404: Scan not found or not owned by current user
    
    Example:
        GET /api/v1/history/a1b2c3d4-5678-90ab-cdef-1234567890ab
        Headers:
            X-User-Id: 1
        
        Response:
        {
            "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
            "target": "example.com",
            "scan_type": "dns",
            "status": "SUCCESS",
            "performed_at": "2025-12-01T10:30:00Z",
            "completed_at": "2025-12-01T10:30:15Z",
            "client_ip": "192.168.1.100",
            "credits_charged": 5,
            "result_snapshot": {
                "collector_name": "DNSCollector",
                "data": {...},
                "timestamp": "2025-12-01T10:30:15Z"
            }
        }
    """
    # Get scan with ownership verification (security check)
    scan = get_scan_by_id(db=db, scan_id=scan_id, user_id=current_user.id)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found or you don't have access to it"
        )
    
    # Convert to response model
    return ScanHistoryDetail(
        id=str(scan.id),
        target=scan.target,
        scan_type=scan.scan_type,
        status=scan.status,
        task_id=scan.task_id,
        performed_at=scan.performed_at,
        completed_at=scan.completed_at,
        client_ip=scan.client_ip,
        credits_charged=scan.credits_charged,
        error_message=scan.error_message,
        result_snapshot=scan.result_snapshot
    )


@router.get(
    "/history/stats/summary",
    response_model=ScanStatistics,
    summary="Get Scan Statistics",
    description="Get aggregated statistics about user's scan history"
)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ScanStatistics:
    """
    Get statistics about user's scan history.
    
    Returns aggregated data including:
    - Total number of scans
    - Counts by status (pending, success, failed, etc.)
    - Total credits spent
    
    Args:
        current_user: Authenticated user (from dependency)
        db: Database session
    
    Returns:
        Statistics summary
    
    Example:
        GET /api/v1/history/stats/summary
        Headers:
            X-User-Id: 1
        
        Response:
        {
            "total_scans": 50,
            "pending": 2,
            "processing": 1,
            "success": 45,
            "failed": 2,
            "cancelled": 0,
            "total_credits_spent": 250
        }
    """
    try:
        stats = get_scan_statistics(db=db, user_id=current_user.id)
        return ScanStatistics(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.delete(
    "/history/{scan_id}",
    summary="Delete Scan History",
    description="Delete a specific scan from history (soft delete)"
)
async def delete_scan_history(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a scan from history.
    
    **Security:** Users can only delete their own scans.
    
    Note: This performs a hard delete. Consider implementing soft deletes
    for compliance requirements.
    
    Args:
        scan_id: UUID of the scan to delete
        current_user: Authenticated user (from dependency)
        db: Database session
    
    Returns:
        Success message
    
    Raises:
        404: Scan not found or not owned by current user
    """
    # Get scan with ownership verification
    scan = get_scan_by_id(db=db, scan_id=scan_id, user_id=current_user.id)
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found or you don't have access to it"
        )
    
    try:
        db.delete(scan)
        db.commit()
        
        return {
            "message": "Scan history deleted successfully",
            "scan_id": scan_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scan history: {str(e)}"
        )
