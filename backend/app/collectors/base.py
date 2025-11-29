from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.schemas import CollectorResult
import uuid

class BaseCollector(ABC):
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def collect(self, target: str) -> CollectorResult:
        pass
    
    def _generate_result(
        self, 
        target: str, 
        success: bool, 
        data: Dict[str, Any], 
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CollectorResult:
        return CollectorResult(
            id=str(uuid.uuid4()),
            collector_name=self.name,
            target=target,
            success=success,
            data=data,
            error=error,
            metadata=metadata or {}
        )
