from app.collectors.base import BaseCollector
from app.models.schemas import CollectorResult
from datetime import datetime, timedelta

class WhoisCollector(BaseCollector):
    async def collect(self, target: str) -> CollectorResult:
        try:
            data = {
                "domain": target,
                "registrar": "Example Registrar Inc.",
                "creation_date": (datetime.now() - timedelta(days=730)).isoformat(),
                "expiration_date": (datetime.now() + timedelta(days=365)).isoformat(),
                "nameservers": ["ns1.example.com", "ns2.example.com"],
                "status": ["clientTransferProhibited"],
                "emails": ["admin@" + target]
            }
            return self._generate_result(target, True, data)
        except Exception as e:
            return self._generate_result(target, False, {}, str(e))
