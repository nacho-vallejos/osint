"""
Social Media Username Collector
Searches for username presence across multiple social media platforms using async requests.
"""

import asyncio
import aiohttp
from typing import Dict, List, Any
from .base import BaseCollector
from ..models.schemas import CollectorResult


class SocialCollector(BaseCollector):
    """
    Collector for finding usernames across social media platforms.
    Uses asynchronous requests for high-performance parallel checking.
    """
    
    # Platform configuration with URL patterns
    PLATFORMS = {
        "GitHub": "https://github.com/{}",
        "Twitter": "https://twitter.com/{}",
        "Instagram": "https://instagram.com/{}",
        "Reddit": "https://reddit.com/user/{}",
        "Twitch": "https://twitch.tv/{}",
        "LinkedIn": "https://linkedin.com/in/{}",
        "Facebook": "https://facebook.com/{}",
        "TikTok": "https://tiktok.com/@{}",
        "YouTube": "https://youtube.com/@{}",
        "Medium": "https://medium.com/@{}",
        "Pinterest": "https://pinterest.com/{}",
        "Snapchat": "https://snapchat.com/add/{}",
        "Telegram": "https://t.me/{}",
        "Discord": "https://discord.com/users/{}",
        "Steam": "https://steamcommunity.com/id/{}",
    }
    
    # Generic User-Agent to avoid basic blocking
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    async def _check_platform(
        self,
        session: aiohttp.ClientSession,
        platform: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Check if username exists on a specific platform.
        
        Args:
            session: aiohttp client session
            platform: Platform name (e.g., "GitHub")
            url: Full URL to check
            
        Returns:
            Dictionary with platform, url, and found status
        """
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True
            ) as response:
                # Status code 200 indicates profile exists
                found = response.status == 200
                
                return {
                    "platform": platform,
                    "url": url,
                    "found": found,
                    "status_code": response.status
                }
                
        except asyncio.TimeoutError:
            return {
                "platform": platform,
                "url": url,
                "found": False,
                "error": "Timeout"
            }
        except aiohttp.ClientError as e:
            return {
                "platform": platform,
                "url": url,
                "found": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "platform": platform,
                "url": url,
                "found": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def collect(self, target: str) -> CollectorResult:
        """
        Search for username across multiple social media platforms.
        
        Args:
            target: Username to search for
            
        Returns:
            CollectorResult with findings from all platforms
        """
        username = target.strip()
        
        # Prepare headers with User-Agent
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Create async tasks for all platforms
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [
                self._check_platform(
                    session,
                    platform,
                    url_pattern.format(username)
                )
                for platform, url_pattern in self.PLATFORMS.items()
            ]
            
            # Execute all requests in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and process results
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                # Handle exceptions from gather
                self.logger.warning(f"Task failed with exception: {result}")
        
        # Count found profiles
        found_count = sum(1 for r in valid_results if r.get("found", False))
        
        # Prepare summary
        summary = {
            "username": username,
            "total_platforms_checked": len(self.PLATFORMS),
            "profiles_found": found_count,
            "profiles_not_found": len(valid_results) - found_count,
            "platforms": valid_results
        }
        
        # Separate found and not found for easier consumption
        found_platforms = [r for r in valid_results if r.get("found", False)]
        not_found_platforms = [r for r in valid_results if not r.get("found", False)]
        
        return CollectorResult(
            collector_name="SocialCollector",
            target=username,
            success=True,
            data={
                "username": username,
                "found_profiles": found_platforms,
                "checked_but_not_found": not_found_platforms,
                "statistics": {
                    "total_checked": len(self.PLATFORMS),
                    "found": found_count,
                    "not_found": len(valid_results) - found_count,
                    "errors": len(results) - len(valid_results)
                }
            },
            metadata={
                "platforms_checked": list(self.PLATFORMS.keys()),
                "user_agent": self.USER_AGENT
            }
        )
