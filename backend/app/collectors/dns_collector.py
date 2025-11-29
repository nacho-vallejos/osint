from app.collectors.base import BaseCollector
from app.models.schemas import CollectorResult
import dns.resolver
import socket

class DNSCollector(BaseCollector):
    async def collect(self, target: str) -> CollectorResult:
        try:
            data = {"records": {}}
            resolver = dns.resolver.Resolver()
            
            for record_type in ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME']:
                try:
                    answers = resolver.resolve(target, record_type)
                    data["records"][record_type] = [str(rdata) for rdata in answers]
                except:
                    pass
            
            return self._generate_result(target, True, data)
        except Exception as e:
            return self._generate_result(target, False, {}, str(e))
