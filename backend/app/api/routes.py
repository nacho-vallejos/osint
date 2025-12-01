from fastapi import APIRouter, HTTPException
from app.models.schemas import CollectorRequest, CollectorResult
from app.collectors.registry import registry
from app.collectors.dns_collector import DNSCollector
from app.collectors.shodan_collector import ShodanCollector
from app.collectors.whois_collector import WhoisCollector
from app.collectors.virustotal_collector import VirusTotalCollector
from app.collectors.haveibeenpwned_collector import HaveIBeenPwnedCollector
from app.collectors.securitytrails_collector import SecurityTrailsCollector
from app.collectors.social_collector import SocialCollector
from app.collectors.crtsh_collector import CrtshCollector
from app.collectors.username_collector import UsernameCollector
from app.collectors.metadata_collector import MetadataCollector

# Register all collectors
registry.register(DNSCollector)
registry.register(ShodanCollector)
registry.register(WhoisCollector)
registry.register(VirusTotalCollector)
registry.register(HaveIBeenPwnedCollector)
registry.register(SecurityTrailsCollector)
registry.register(SocialCollector)
registry.register(CrtshCollector)
registry.register(UsernameCollector)
registry.register(MetadataCollector)

router = APIRouter()

@router.get("/collectors")
async def list_collectors():
    return {"collectors": registry.list_collectors()}

@router.post("/collectors/execute", response_model=CollectorResult)
async def execute_collector(request: CollectorRequest):
    try:
        collector = registry.get_collector(request.collector_name)
        result = await collector.collect(request.target)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
