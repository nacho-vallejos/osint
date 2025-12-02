"""
Scan Router - API endpoints for async OSINT scanning with Rate Limiting and Credits
Provides endpoints to enqueue scan tasks and check their status.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from celery.result import AsyncResult
from enum import Enum
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.tasks.scan_tasks import perform_osint_scan, COLLECTOR_MAP
from app.api.deps import check_and_deduct_credits, get_current_user, get_user_credits
from app.models.user import User
from app.database import get_db
from app.services.history_service import create_scan_log

router = APIRouter()


class CollectorType(str, Enum):
    """Available collector types"""
    DNS = "dns"
    USERNAME = "username"
    METADATA = "metadata"
    IDENTITY = "identity"
    SOCIAL = "social"
    CRTSH = "crtsh"
    WHOIS = "whois"
    SHODAN = "shodan"
    VIRUSTOTAL = "virustotal"
    HAVEIBEENPWNED = "haveibeenpwned"
    SECURITYTRAILS = "securitytrails"


class ScanRequest(BaseModel):
    """Request model for initiating a scan"""
    target: str = Field(..., description="Target to scan (domain, IP, username, email, etc.)")
    type: CollectorType = Field(..., description="Type of collector to use", alias="type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target": "example.com",
                "type": "dns"
            }
        }


class ScanResponse(BaseModel):
    """Response model for scan initiation"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Initial task status")
    message: str = Field(..., description="Human-readable message")
    target: str = Field(..., description="Target being scanned")
    collector_type: str = Field(..., description="Collector type being used")
    credits_remaining: int = Field(..., description="User's remaining credits after deduction")
    cost: int = Field(..., description="Credits deducted for this scan")


class TaskStatusResponse(BaseModel):
    """Response model for task status query"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    progress: Optional[str] = None


@router.post(
    "/scan",
    response_model=ScanResponse,
    summary="Initiate OSINT Scan",
    description="Enqueue an asynchronous OSINT scan task (Rate Limited: 10 req/min, Cost: 5 credits)",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def initiate_scan(
    scan_request: ScanRequest,
    http_request: Request,
    user: User = Depends(check_and_deduct_credits(cost=5)),
    db: Session = Depends(get_db)
) -> ScanResponse:
    """
    Initiate an asynchronous OSINT scan.
    
    **RATE LIMIT:** 10 requests per minute per user
    **COST:** 5 credits per scan
    
    This endpoint immediately returns a task ID that can be used to check the scan status.
    The actual scan runs in the background via Celery workers.
    
    **Authentication:**
    - Requires `X-User-Id` header with valid user ID
    
    **Credits System:**
    - Each scan costs 5 credits
    - Credits are deducted atomically before enqueueing the task
    - If insufficient credits, returns 402 Payment Required
    
    **Rate Limiting:**
    - Limited to 10 scans per minute per user
    - Exceeding rate limit returns 429 Too Many Requests
    
    Args:
        request: ScanRequest containing target and collector type
        user: Current authenticated user (injected by dependency)
        
    Returns:
        ScanResponse with task_id, status, and remaining credits
        
    Raises:
        401: Missing or invalid authentication
        402: Insufficient credits
        429: Rate limit exceeded
        400: Invalid collector type
        500: Server error
        
    Example:
        POST /api/v1/scan
        Headers:
            X-User-Id: 1
        Body:
        {
            "target": "example.com",
            "type": "dns"
        }
        
        Response (200 OK):
        {
            "task_id": "a1b2c3d4-...",
            "status": "PENDING",
            "message": "Scan initiated successfully",
            "target": "example.com",
            "collector_type": "dns",
            "credits_remaining": 45,
            "cost": 5
        }
        
        Response (402 Payment Required):
        {
            "detail": "Insufficient credits. Required: 5, Available: 2"
        }
        Headers:
            X-Credits-Required: 5
            X-Credits-Available: 2
            X-Credits-Needed: 3
    """
    try:
        # Validate collector type
        collector_type = scan_request.type.value
        if collector_type not in COLLECTOR_MAP:
            available = ", ".join(COLLECTOR_MAP.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Invalid collector type '{collector_type}'. Available: {available}"
            )
        
        # Enqueue the task (credits already deducted by dependency)
        task = perform_osint_scan.delay(scan_request.target, collector_type)
        
        # Extract client IP and user agent for audit trail
        client_ip = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent")
        
        # Create scan history log entry
        create_scan_log(
            db=db,
            user_id=user.id,
            target=scan_request.target,
            scan_type=collector_type,
            task_id=task.id,
            client_ip=client_ip,
            user_agent=user_agent,
            credits_charged=5
        )
        
        return ScanResponse(
            task_id=task.id,
            status="PENDING",
            message="Scan initiated successfully. Use task_id to check status.",
            target=scan_request.target,
            collector_type=collector_type,
            credits_remaining=user.credits_balance,
            cost=5
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (rate limit, auth, etc.)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate scan: {str(e)}"
        )


@router.get(
    "/scan/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get Scan Status",
    description="Retrieve the current status and result of a scan task"
)
async def get_scan_status(
    task_id: str,
    _: User = Depends(get_current_user)
) -> TaskStatusResponse:
    """
    Get the status of an OSINT scan task.
    
    **Authentication Required:** X-User-Id header
    
    Args:
        task_id: The unique task identifier returned from /scan endpoint
        
    Returns:
        TaskStatusResponse with current status and result (if complete)
        
    Status values:
        - PENDING: Task is waiting to be executed
        - STARTED: Task has been started
        - PROCESSING: Task is currently running (custom state)
        - SUCCESS: Task completed successfully
        - FAILURE: Task failed
        - RETRY: Task is being retried
        
    Example:
        GET /api/v1/scan/a1b2c3d4-...
        Headers:
            X-User-Id: 1
        
        Response (pending):
        {
            "task_id": "a1b2c3d4-...",
            "status": "PROCESSING",
            "meta": {
                "collector_type": "dns",
                "target": "example.com",
                "status": "Running DNSCollector..."
            }
        }
        
        Response (complete):
        {
            "task_id": "a1b2c3d4-...",
            "status": "SUCCESS",
            "result": {
                "id": "...",
                "collector_name": "DNSCollector",
                "target": "example.com",
                "success": true,
                "data": {...},
                "timestamp": "..."
            }
        }
    """
    try:
        # Get task result
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.state
        )
        
        # Handle different task states
        if task_result.state == "PENDING":
            response.progress = "Task is waiting in queue..."
        
        elif task_result.state == "STARTED":
            response.progress = "Task execution has started..."
        
        elif task_result.state == "PROCESSING":
            # Custom state with progress info
            response.meta = task_result.info
            if isinstance(task_result.info, dict):
                response.progress = task_result.info.get("status", "Processing...")
        
        elif task_result.state == "SUCCESS":
            # Task completed successfully
            response.result = task_result.result
            response.progress = "Scan completed successfully"
        
        elif task_result.state == "FAILURE":
            # Task failed
            response.error = str(task_result.info)
            response.progress = "Task failed"
        
        elif task_result.state == "RETRY":
            # Task is being retried
            response.progress = "Task failed, retrying..."
            response.meta = {"retry_count": task_result.info.get("retries", 0) if isinstance(task_result.info, dict) else 0}
        
        else:
            # Unknown state
            response.progress = f"Task state: {task_result.state}"
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve task status: {str(e)}"
        )


@router.get(
    "/scan/{task_id}/cancel",
    summary="Cancel Scan",
    description="Cancel a running scan task"
)
async def cancel_scan(
    task_id: str,
    _: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel a running scan task.
    
    **Note:** Cancelled scans do NOT refund credits.
    
    Args:
        task_id: The unique task identifier
        
    Returns:
        Cancellation confirmation
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {
            "task_id": task_id,
            "status": "REVOKED",
            "message": "Task cancellation requested. Credits are not refunded."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.get(
    "/credits",
    summary="Get User Credits",
    description="Get current user's credit balance"
)
async def get_credits(
    credits_info: dict = Depends(get_user_credits)
) -> Dict[str, Any]:
    """
    Get the current user's credit balance.
    
    Returns:
        User credits information
        
    Example:
        GET /api/v1/credits
        Headers:
            X-User-Id: 1
        
        Response:
        {
            "user_id": 1,
            "email": "user@example.com",
            "credits_balance": 45,
            "is_active": true
        }
    """
    return credits_info


@router.get(
    "/collectors",
    summary="List Available Collectors",
    description="Get a list of all available OSINT collectors"
)
async def list_collectors() -> Dict[str, Any]:
    """
    List all available OSINT collectors.
    
    Returns:
        Dictionary with collector information
    """
    return {
        "collectors": [
            {
                "type": collector_type,
                "class": collector_class.__name__,
                "description": collector_class.__doc__.strip() if collector_class.__doc__ else "No description"
            }
            for collector_type, collector_class in COLLECTOR_MAP.items()
        ],
        "total": len(COLLECTOR_MAP)
    }


@router.get(
    "/health",
    summary="Celery Health Check",
    description="Check if Celery workers are running"
)
async def celery_health() -> Dict[str, Any]:
    """
    Check Celery worker health.
    
    Returns:
        Health status information
    """
    try:
        # Inspect active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if not active_workers:
            return {
                "status": "unhealthy",
                "message": "No active Celery workers found",
                "workers": 0
            }
        
        return {
            "status": "healthy",
            "message": "Celery workers are operational",
            "workers": len(active_workers),
            "worker_names": list(active_workers.keys()),
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check worker health: {str(e)}",
            "workers": 0
        }
