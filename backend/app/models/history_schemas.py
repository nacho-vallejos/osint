"""
Pydantic Schemas for Scan History API.
Defines request/response models for history endpoints.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ScanStatusEnum(str, Enum):
    """Scan status enum for API responses"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ScanHistorySummary(BaseModel):
    """
    Summary of a scan history entry (without full result).
    Used for list endpoints to avoid transferring large result snapshots.
    """
    model_config = ConfigDict(from_attributes=True, json_schema_extra=id: str = Field(..., description="Unique scan identifier (UUID)")
    target: str = Field(..., description="Scan target (domain, IP, username, etc.)")
    scan_type: str = Field(..., description="Type of collector used")
    status: ScanStatusEnum = Field(..., description="Current scan status")
    task_id: Optional[str] = Field(None, description="Celery task ID")
    performed_at: datetime = Field(..., description="When scan was initiated")
    completed_at: Optional[datetime] = Field(None, description="When scan completed")
    credits_charged: int = Field(..., description="Credits charged for this scan")
    error_message: Optional[str] = Field(None, description="Error message if failed"){
            "example": {
                "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
                "target": "example.com",
                "scan_type": "dns",
                "status": "SUCCESS",
                "task_id": "xyz-789",
                "performed_at": "2025-12-01T10:30:00Z",
                "completed_at": "2025-12-01T10:30:15Z",
                "credits_charged": 5
            })
        


class ScanHistoryDetail(BaseModel):
    """
    Complete scan history entry including full result snapshot.
    Used for detail endpoint when user wants to reconstruct historical scan.
    """
    model_config = ConfigDict(from_attributes=True, json_schema_extra=id: str = Field(..., description="Unique scan identifier (UUID)")
    target: str = Field(..., description="Scan target")
    scan_type: str = Field(..., description="Type of collector used")
    status: ScanStatusEnum = Field(..., description="Current scan status")
    task_id: Optional[str] = Field(None, description="Celery task ID")
    performed_at: datetime = Field(..., description="When scan was initiated")
    completed_at: Optional[datetime] = Field(None, description="When scan completed")
    client_ip: Optional[str] = Field(None, description="Client IP address")
    credits_charged: int = Field(..., description="Credits charged")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result_snapshot: Optional[Dict[str, Any]] = Field(None, description="Complete scan result"){
            "example": {
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
                    "target": "example.com",
                    "success": True,
                    "data": {"A": ["93.184.216.34"]},
                    "timestamp": "2025-12-01T10:30:15Z"
                }
            })
        


class ScanHistoryListResponse(BaseModel):
    """
    Paginated response for scan history list endpoint.
    """
    scans: List[ScanHistorySummary] = Field(..., description="List of scan summaries")
    total: int = Field(..., description="Total number of scans")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Results per page")
    pages: int = Field(..., description="Total number of pages"){
            "example": {
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
            })
        


class ScanStatistics(BaseModel):
    """
    Statistics about user's scan history.
    """
    total_scans: int = Field(..., description="Total number of scans")
    pending: int = Field(0, description="Number of pending scans")
    processing: int = Field(0, description="Number of processing scans")
    success: int = Field(0, description="Number of successful scans")
    failed: int = Field(0, description="Number of failed scans")
    cancelled: int = Field(0, description="Number of cancelled scans")
    total_credits_spent: int = Field(..., description="Total credits spent on scans"){
            "example": {
                "total_scans": 50,
                "pending": 2,
                "processing": 1,
                "success": 45,
                "failed": 2,
                "cancelled": 0,
                "total_credits_spent": 250
            })
        
