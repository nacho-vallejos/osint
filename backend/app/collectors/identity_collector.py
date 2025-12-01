"""
Identity Collector - Person & Digital Identity Discovery
Searches for digital footprints through Gravatar, social media, and identity signals
"""

import hashlib
import re
import logging
from typing import Dict, List, Any, Optional

import httpx

from app.collectors.base import BaseCollector
from app.models.schemas import CollectorResult

logger = logging.getLogger(__name__)


class IdentityCollector(BaseCollector):
    """
    Advanced identity collector for person discovery and digital footprint analysis.
    
    Searches for:
    - Gravatar profiles (email-based)
    - Social media accounts (GitHub, Twitter, Instagram, Reddit)
    - Username presence across platforms
    
    Useful for:
    - Person identification
    - Digital footprint mapping
    - OSINT investigations
    - Identity verification
    """
    
    # High-value social platforms for identity discovery
    SOCIAL_PLATFORMS = [
        {
            "name": "GitHub",
            "url": "https://github.com/{}",
            "check_status": 200,
            "icon": "💻"
        },
        {
            "name": "Twitter",
            "url": "https://twitter.com/{}",
            "check_status": 200,
            "icon": "🐦"
        },
        {
            "name": "Instagram",
            "url": "https://www.instagram.com/{}",
            "check_status": 200,
            "icon": "📷"
        },
        {
            "name": "Reddit",
            "url": "https://www.reddit.com/user/{}",
            "check_status": 200,
            "icon": "🤖"
        },
        {
            "name": "LinkedIn",
            "url": "https://www.linkedin.com/in/{}",
            "check_status": 200,
            "icon": "💼"
        },
        {
            "name": "Medium",
            "url": "https://medium.com/@{}",
            "check_status": 200,
            "icon": "📝"
        },
    ]
    
    TIMEOUT = 5.0
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )
    
    async def collect(self, target: str) -> CollectorResult:
        """
        Collect identity signals from target (email or username).
        
        Args:
            target: Email address or username to investigate
            
        Returns:
            CollectorResult with identity signals and digital footprints
        """
        target = target.strip()
        
        if not target:
            return self._generate_result(
                target=target,
                success=False,
                data={},
                error="Target cannot be empty"
            )
        
        try:
            identity_data = {
                "target": target,
                "target_type": self._detect_target_type(target),
                "gravatar": None,
                "social_accounts": [],
                "found_signals": 0,
            }
            
            # Extract username from email if needed
            username = self._extract_username(target)
            
            # Module 1: Gravatar check (if email)
            if self._is_email(target):
                logger.info(f"Checking Gravatar for email: {target}")
                gravatar_data = await self._check_gravatar(target)
                if gravatar_data:
                    identity_data["gravatar"] = gravatar_data
                    identity_data["found_signals"] += 1
            
            # Module 2: Social Signals check
            logger.info(f"Checking social platforms for: {username}")
            social_accounts = await self._check_social_platforms(username)
            identity_data["social_accounts"] = social_accounts
            identity_data["found_signals"] += len(social_accounts)
            
            # Generate summary
            identity_data["summary"] = self._generate_summary(identity_data)
            
            return self._generate_result(
                target=target,
                success=True,
                data=identity_data,
                metadata={
                    "platforms_checked": len(self.SOCIAL_PLATFORMS),
                    "gravatar_checked": self._is_email(target),
                    "username_used": username
                }
            )
            
        except Exception as e:
            logger.error(f"IdentityCollector error: {e}")
            return self._generate_result(
                target=target,
                success=False,
                data={},
                error=f"Collection failed: {str(e)}"
            )
    
    def _detect_target_type(self, target: str) -> str:
        """Detect if target is email or username"""
        return "email" if self._is_email(target) else "username"
    
    def _is_email(self, target: str) -> bool:
        """Check if target is a valid email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, target))
    
    def _extract_username(self, target: str) -> str:
        """Extract username from email or return target as-is"""
        if self._is_email(target):
            return target.split('@')[0]
        return target
    
    async def _check_gravatar(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Check if email has a Gravatar profile.
        
        Args:
            email: Email address to check
            
        Returns:
            Dictionary with Gravatar data or None if not found
        """
        try:
            # Normalize email and generate MD5 hash
            normalized_email = email.lower().strip()
            email_hash = hashlib.md5(normalized_email.encode('utf-8')).hexdigest()
            
            # Gravatar URL with 404 parameter
            gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.TIMEOUT),
                headers={"User-Agent": self.USER_AGENT},
                follow_redirects=True
            ) as client:
                response = await client.get(gravatar_url)
                
                if response.status_code == 200:
                    logger.info(f"Gravatar found for {email}")
                    return {
                        "exists": True,
                        "avatar_url": f"https://www.gravatar.com/avatar/{email_hash}",
                        "email_hash": email_hash,
                        "profile_url": f"https://gravatar.com/{email_hash}"
                    }
                else:
                    logger.debug(f"No Gravatar found for {email} (HTTP {response.status_code})")
                    return None
                    
        except Exception as e:
            logger.warning(f"Gravatar check failed: {e}")
            return None
    
    async def _check_social_platforms(self, username: str) -> List[Dict[str, Any]]:
        """
        Check username presence across social platforms.
        
        Args:
            username: Username to search for
            
        Returns:
            List of found social accounts with metadata
        """
        found_accounts = []
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.TIMEOUT),
            headers={"User-Agent": self.USER_AGENT},
            follow_redirects=True
        ) as client:
            for platform in self.SOCIAL_PLATFORMS:
                try:
                    url = platform["url"].format(username)
                    
                    # Use HEAD request first (faster)
                    try:
                        response = await client.head(url)
                    except:
                        # Fallback to GET if HEAD not supported
                        response = await client.get(url)
                    
                    if response.status_code == platform["check_status"]:
                        logger.info(f"Found {platform['name']} account: {url}")
                        found_accounts.append({
                            "platform": platform["name"],
                            "url": url,
                            "status_code": response.status_code,
                            "icon": platform["icon"],
                            "exists": True,
                            "confidence": 1.0
                        })
                    else:
                        logger.debug(f"{platform['name']}: Not found (HTTP {response.status_code})")
                        
                except httpx.TimeoutException:
                    logger.warning(f"{platform['name']}: Timeout")
                except Exception as e:
                    logger.debug(f"{platform['name']}: Check failed - {e}")
                    continue
        
        return found_accounts
    
    def _generate_summary(self, identity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from identity data"""
        return {
            "total_signals": identity_data["found_signals"],
            "has_gravatar": identity_data["gravatar"] is not None,
            "social_accounts_found": len(identity_data["social_accounts"]),
            "platforms_with_presence": [
                acc["platform"] for acc in identity_data["social_accounts"]
            ],
            "identity_strength": self._calculate_identity_strength(identity_data)
        }
    
    def _calculate_identity_strength(self, identity_data: Dict[str, Any]) -> str:
        """Calculate identity strength based on signals found"""
        signals = identity_data["found_signals"]
        
        if signals == 0:
            return "none"
        elif signals <= 2:
            return "low"
        elif signals <= 4:
            return "medium"
        else:
            return "high"
