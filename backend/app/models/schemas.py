from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

class CollectorResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    collector_name: str
    target: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CollectorRequest(BaseModel):
    collector_name: str
    target: str
