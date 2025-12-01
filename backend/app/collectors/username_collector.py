"""
Username Collector - Cross-platform username verification
Checks username presence across multiple social media platforms using async HTTP requests
"""

import asyncio
import httpx
from typing import Dict, List, Any
from app.collectors.base import BaseCollector
from app.models.schemas import CollectorResult
import logging

logger = logging.getLogger(__name__)


class UsernameCollector(BaseCollector):
    """
    Collector for verifying username existence across social media platforms
    Uses parallel async requests for maximum performance
    """
    
    # Platform configuration with URL patterns
    PLATFORMS = {
        "GitHub": "https://github.com/{}",
        "Twitter": "https://twitter.com/{}",
        "Reddit": "https://www.reddit.com/user/{}",
        "Instagram": "https://www.instagram.com/{}",
        "Twitch": "https://www.twitch.tv/{}",
        "Pinterest": "https://www.pinterest.com/{}",
    }
    
    # Realistic Chrome User-Agent to avoid bot detection
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
    
    TIMEOUT = 5.0  # Maximum 5 seconds per platform
    
    async def collect(self, target: str) -> CollectorResult:
        """
        Check username presence across all configured platforms
        
        Args:
            target: Username to search for
            
        Returns:
            CollectorResult with platform verification results
        """
        username = target.strip()
        
        if not username:
            return self._generate_result(
                target=target,
                success=False,
                data={"profiles": []},
                error="Username cannot be empty"
            )
        
        # Launch all platform checks in parallel
        try:
            results = await self._check_all_platforms(username)
            
            # Separate found and not found
            found_profiles = [r for r in results if r["exists"]]
            not_found = [r for r in results if not r["exists"]]
            
            return self._generate_result(
                target=username,
                success=True,
                data={
                    "username": username,
                    "profiles": results,
                    "found": found_profiles,
                    "not_found": not_found,
                    "total_platforms": len(results),
                    "found_count": len(found_profiles)
                },
                metadata={
                    "platforms_checked": list(self.PLATFORMS.keys()),
                    "timeout_per_platform": self.TIMEOUT,
                    "user_agent": self.USER_AGENT
                }
            )
            
        except Exception as e:
            logger.error(f"Error in UsernameCollector: {e}")
            return self._generate_result(
                target=username,
                success=False,
                data={"profiles": []},
                error=f"Collection failed: {str(e)}"
            )
    
    async def _check_all_platforms(self, username: str) -> List[Dict[str, Any]]:
        """
        Check username on all platforms in parallel using asyncio.gather
        
        Args:
            username: Username to verify
            
        Returns:
            List of platform check results
        """
        # Create async client with proper configuration
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.TIMEOUT),
            headers={"User-Agent": self.USER_AGENT},
            follow_redirects=True
        ) as client:
            # Create tasks for all platforms
            tasks = [
                self._check_platform(client, platform, url_pattern, username)
                for platform, url_pattern in self.PLATFORMS.items()
            ]
            
            # Execute all requests in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and convert to proper results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Platform check failed: {result}")
                    continue
                if isinstance(result, dict):
                    processed_results.append(result)
            
            return processed_results
    
    async def _check_platform(
        self,
        client: httpx.AsyncClient,
        platform: str,
        url_pattern: str,
        username: str
    ) -> Dict[str, Any]:
        """
        Check if username exists on a specific platform
        
        Args:
            client: HTTP client instance
            platform: Platform name (e.g., "GitHub")
            url_pattern: URL pattern with {} placeholder
            username: Username to check
            
        Returns:
            Dictionary with platform check result
        """
        url = url_pattern.format(username)
        
        try:
            response = await client.get(url)
            
            # Determine if profile exists based on status code
            exists = response.status_code == 200
            
            result = {
                "platform": platform,
                "url": url,
                "exists": exists,
                "status_code": response.status_code,
                "confidence": 1.0 if exists else 0.0
            }
            
            logger.debug(
                f"{platform}: {username} - "
                f"{'FOUND' if exists else 'NOT FOUND'} "
                f"(HTTP {response.status_code})"
            )
            
            return result
            
        except httpx.TimeoutException:
            logger.warning(f"{platform}: Timeout checking {username}")
            return {
                "platform": platform,
                "url": url,
                "exists": False,
                "status_code": None,
                "error": "Timeout",
                "confidence": 0.0
            }
            
        except httpx.HTTPError as e:
            logger.warning(f"{platform}: HTTP error - {e}")
            return {
                "platform": platform,
                "url": url,
                "exists": False,
                "status_code": None,
                "error": str(e),
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.error(f"{platform}: Unexpected error - {e}")
            return {
                "platform": platform,
                "url": url,
                "exists": False,
                "status_code": None,
                "error": str(e),
                "confidence": 0.0
            }
