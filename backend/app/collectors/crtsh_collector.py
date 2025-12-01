"""
Certificate Transparency Subdomain Collector
Uses crt.sh API to discover subdomains from CT logs
"""

from app.collectors.base import BaseCollector
from app.models.schemas import CollectorResult
import httpx
import logging
from typing import Set

logger = logging.getLogger(__name__)


class CrtshCollector(BaseCollector):
    """
    Collector for discovering subdomains using Certificate Transparency logs
    via crt.sh API. CT logs are highly reliable sources for subdomain enumeration.
    """
    
    CRTSH_API_URL = "https://crt.sh/"
    TIMEOUT = 15  # CT logs can be slow to query
    
    async def collect(self, target: str) -> CollectorResult:
        """
        Query Certificate Transparency logs for subdomains
        
        Args:
            target: Domain to search for (e.g., "example.com")
            
        Returns:
            CollectorResult with discovered subdomains
        """
        try:
            # Query crt.sh API
            params = {
                "q": f"%.{target}",
                "output": "json"
            }
            
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(self.CRTSH_API_URL, params=params)
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    certificates = response.json()
                except ValueError as e:
                    logger.error(f"Invalid JSON response from crt.sh: {e}")
                    return self._generate_result(
                        target=target,
                        success=False,
                        data={"subdomains": []},
                        error="Invalid JSON response from crt.sh"
                    )
            
            # Extract and clean subdomains
            subdomains = self._extract_subdomains(certificates, target)
            
            # Build metadata
            metadata = {
                "source": "crt.sh",
                "certificates_found": len(certificates) if isinstance(certificates, list) else 0,
                "unique_subdomains": len(subdomains),
                "api_endpoint": self.CRTSH_API_URL
            }
            
            return self._generate_result(
                target=target,
                success=True,
                data={
                    "subdomains": sorted(list(subdomains)),
                    "total_count": len(subdomains)
                },
                metadata=metadata
            )
            
        except httpx.TimeoutException:
            logger.error(f"Timeout querying crt.sh for {target}")
            return self._generate_result(
                target=target,
                success=False,
                data={"subdomains": []},
                error=f"Timeout after {self.TIMEOUT} seconds querying crt.sh"
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error querying crt.sh: {e}")
            return self._generate_result(
                target=target,
                success=False,
                data={"subdomains": []},
                error=f"HTTP error: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in CrtshCollector: {e}")
            return self._generate_result(
                target=target,
                success=False,
                data={"subdomains": []},
                error=f"Unexpected error: {str(e)}"
            )
    
    def _extract_subdomains(self, certificates: list, target: str) -> Set[str]:
        """
        Extract and clean subdomains from certificate data
        
        Args:
            certificates: List of certificate objects from crt.sh
            target: Original domain to filter out
            
        Returns:
            Set of unique, cleaned subdomains
        """
        subdomains = set()
        
        if not isinstance(certificates, list):
            return subdomains
        
        for cert in certificates:
            # Extract name_value field
            name_value = cert.get("name_value", "")
            
            if not name_value:
                continue
            
            # name_value can contain multiple domains separated by newlines
            domains = name_value.split("\n")
            
            for domain in domains:
                domain = domain.strip().lower()
                
                if not domain:
                    continue
                
                # Remove wildcard prefix
                if domain.startswith("*."):
                    domain = domain[2:]
                
                # Skip if it's the target domain itself (we want subdomains)
                if domain == target.lower():
                    continue
                
                # Only include if it's actually a subdomain of target
                if domain.endswith(f".{target.lower()}"):
                    subdomains.add(domain)
        
        return subdomains
