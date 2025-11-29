"""
Social Reconnaissance Service - Advanced Identity Triangulation
Based on Sherlock-like architecture with async profile discovery
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from urllib.parse import quote


logger = logging.getLogger(__name__)


class ProfileStatus(Enum):
    """Status of profile verification"""
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class SocialProfile:
    """Represents a discovered social media profile"""
    platform: str
    username: str
    url: str
    status: ProfileStatus
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "username": self.username,
            "url": self.url,
            "status": self.status.value,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


class SocialProfiler:
    """
    Advanced Social Media Profile Discovery Engine
    Implements intelligent verification with multiple detection strategies
    """
    
    # Platform configuration with detection strategies
    PLATFORMS = {
        "GitHub": {
            "url": "https://github.com/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "Twitter": {
            "url": "https://twitter.com/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "Instagram": {
            "url": "https://www.instagram.com/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "response_url",
            "error_match": "https://www.instagram.com/accounts/login"
        },
        "LinkedIn": {
            "url": "https://www.linkedin.com/in/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "Reddit": {
            "url": "https://www.reddit.com/user/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "Twitch": {
            "url": "https://www.twitch.tv/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "YouTube": {
            "url": "https://www.youtube.com/@{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "TikTok": {
            "url": "https://www.tiktok.com/@{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "Medium": {
            "url": "https://medium.com/@{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "DevTo": {
            "url": "https://dev.to/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        },
        "HackerNews": {
            "url": "https://news.ycombinator.com/user?id={}",
            "method": "response_text",
            "status_match": 200,
            "text_match": "user?id={}",
            "error_text": "No such user"
        },
        "StackOverflow": {
            "url": "https://stackoverflow.com/users/{}",
            "method": "status_code",
            "status_match": 200,
            "error_type": "status_code",
            "error_match": 404
        }
    }
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, timeout: int = 10, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _check_platform(
        self,
        platform: str,
        username: str,
        config: Dict[str, Any]
    ) -> SocialProfile:
        """
        Check if username exists on a specific platform
        
        Args:
            platform: Platform name
            username: Username to check
            config: Platform configuration
            
        Returns:
            SocialProfile with verification results
        """
        url = config["url"].format(quote(username))
        method = config["method"]
        
        session = await self._get_session()
        
        headers = {
            "User-Agent": self.USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                status = response.status
                final_url = str(response.url)
                
                # Method 1: Status code matching
                if method == "status_code":
                    if status == config["status_match"]:
                        # Verify it's not an error page
                        error_type = config.get("error_type")
                        if error_type == "response_url":
                            if final_url == config.get("error_match"):
                                return self._create_profile(
                                    platform, username, url,
                                    ProfileStatus.NOT_FOUND, 0.9
                                )
                        
                        return self._create_profile(
                            platform, username, url,
                            ProfileStatus.FOUND, 0.95,
                            {"status_code": status, "final_url": final_url}
                        )
                    elif status == config.get("error_match"):
                        return self._create_profile(
                            platform, username, url,
                            ProfileStatus.NOT_FOUND, 0.9
                        )
                    else:
                        return self._create_profile(
                            platform, username, url,
                            ProfileStatus.ERROR, 0.3,
                            {"unexpected_status": status}
                        )
                
                # Method 2: Response text matching
                elif method == "response_text":
                    text = await response.text()
                    
                    if status == config["status_match"]:
                        text_match = config.get("text_match", "").format(username)
                        error_text = config.get("error_text", "")
                        
                        if error_text and error_text in text:
                            return self._create_profile(
                                platform, username, url,
                                ProfileStatus.NOT_FOUND, 0.9
                            )
                        elif text_match and text_match in text:
                            return self._create_profile(
                                platform, username, url,
                                ProfileStatus.FOUND, 0.85,
                                {"matched_text": True}
                            )
                    
                    return self._create_profile(
                        platform, username, url,
                        ProfileStatus.ERROR, 0.4
                    )
                
        except asyncio.TimeoutError:
            logger.warning(f"{platform}: Timeout checking {username}")
            return self._create_profile(
                platform, username, url,
                ProfileStatus.ERROR, 0.0,
                {"error": "Timeout"}
            )
        except aiohttp.ClientError as e:
            logger.error(f"{platform}: Client error - {e}")
            return self._create_profile(
                platform, username, url,
                ProfileStatus.ERROR, 0.0,
                {"error": str(e)}
            )
        except Exception as e:
            logger.error(f"{platform}: Unexpected error - {e}")
            return self._create_profile(
                platform, username, url,
                ProfileStatus.ERROR, 0.0,
                {"error": f"Unexpected: {str(e)}"}
            )
    
    def _create_profile(
        self,
        platform: str,
        username: str,
        url: str,
        status: ProfileStatus,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SocialProfile:
        """Create a SocialProfile instance"""
        return SocialProfile(
            platform=platform,
            username=username,
            url=url,
            status=status,
            confidence=confidence,
            metadata=metadata or {}
        )
    
    async def discover_profiles(
        self,
        username: str,
        platforms: Optional[List[str]] = None
    ) -> List[SocialProfile]:
        """
        Discover social media profiles for a username
        
        Args:
            username: Username to search
            platforms: Optional list of specific platforms to check
            
        Returns:
            List of SocialProfile objects with verification results
        """
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        username = username.strip()
        
        # Filter platforms if specified
        platforms_to_check = {}
        if platforms:
            platforms_to_check = {
                k: v for k, v in self.PLATFORMS.items()
                if k in platforms
            }
        else:
            platforms_to_check = self.PLATFORMS
        
        if not platforms_to_check:
            raise ValueError("No valid platforms specified")
        
        logger.info(f"Starting profile discovery for '{username}' across {len(platforms_to_check)} platforms")
        
        # Create async tasks for all platforms
        tasks = [
            self._check_platform(platform, username, config)
            for platform, config in platforms_to_check.items()
        ]
        
        # Execute all checks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        profiles = []
        for result in results:
            if isinstance(result, SocialProfile):
                profiles.append(result)
            else:
                logger.error(f"Task failed: {result}")
        
        logger.info(
            f"Discovery complete: {len(profiles)} profiles checked, "
            f"{sum(1 for p in profiles if p.status == ProfileStatus.FOUND)} found"
        )
        
        return profiles
    
    async def get_confirmed_profiles(self, username: str) -> List[SocialProfile]:
        """
        Get only confirmed profiles (status=FOUND)
        
        Args:
            username: Username to search
            
        Returns:
            List of confirmed SocialProfile objects
        """
        all_profiles = await self.discover_profiles(username)
        return [p for p in all_profiles if p.status == ProfileStatus.FOUND]
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Neo4j Graph Schema representation
GRAPH_SCHEMA = """
// Neo4j Cypher Schema for Identity Triangulation

// ============ NODES ============

// Person Node (Target Identity)
CREATE (p:Person {
    person_id: "uuid",
    name: "string",
    aliases: ["list", "of", "usernames"],
    first_seen: datetime(),
    last_updated: datetime(),
    confidence_score: 0.0  // Overall identity confidence
})

// Social Profile Node
CREATE (sp:SocialProfile {
    profile_id: "uuid",
    platform: "GitHub",
    username: "string",
    url: "https://...",
    verified: true,
    confidence: 0.95,
    discovered_at: datetime(),
    metadata: {}  // Platform-specific data
})

// Video Node
CREATE (v:Video {
    video_id: "uuid",
    filename: "video.mp4",
    duration_seconds: 120,
    resolution: "1920x1080",
    fps: 30,
    file_size_mb: 50.5,
    analyzed_at: datetime(),
    checksum: "sha256_hash"
})

// Face Encoding Node (Biometric)
CREATE (fe:FaceEncoding {
    encoding_id: "uuid",
    encoding_vector: [128d_vector],  // face_recognition encoding
    confidence: 0.92,
    frame_timestamp: 45.2,
    bbox: {x: 100, y: 150, w: 200, h: 250}
})

// Transcript Node (Speech-to-Text)
CREATE (t:Transcript {
    transcript_id: "uuid",
    full_text: "Transcribed audio text...",
    language: "en",
    word_count: 500,
    duration_seconds: 120,
    confidence: 0.88
})

// Keyword Node (Topic Extraction)
CREATE (k:Keyword {
    keyword_id: "uuid",
    term: "cybersecurity",
    frequency: 15,
    tf_idf_score: 0.75,
    category: "technology"
})


// ============ RELATIONSHIPS ============

// Person -> Social Profile
CREATE (p:Person)-[r:HAS_ACCOUNT {
    verified_at: datetime(),
    verification_method: "profile_discovery",
    confidence: 0.95
}]->(sp:SocialProfile)

// Person -> Video (Visual Appearance)
CREATE (p:Person)-[r:APPEARS_IN {
    detected_at: datetime(),
    frame_count: 45,
    average_confidence: 0.88,
    timestamps: [12.5, 34.2, 56.8]  // Seconds where face detected
}]->(v:Video)

// Video -> Face Encoding
CREATE (v:Video)-[r:CONTAINS_FACE {
    frame_number: 450,
    timestamp: 15.0
}]->(fe:FaceEncoding)

// Face Encoding -> Person (Biometric Match)
CREATE (fe:FaceEncoding)-[r:MATCHES_IDENTITY {
    similarity_score: 0.92,  // Face distance < threshold
    matched_at: datetime(),
    algorithm: "dlib_face_recognition"
}]->(p:Person)

// Video -> Transcript
CREATE (v:Video)-[r:CONTAINS_AUDIO {
    extracted_at: datetime(),
    audio_format: "wav",
    sample_rate: 16000
}]->(t:Transcript)

// Video -> Keyword (Content Analysis)
CREATE (v:Video)-[r:MENTIONS_TOPIC {
    frequency: 15,
    relevance_score: 0.85,
    context: "mentioned in security discussion"
}]->(k:Keyword)

// Transcript -> Keyword
CREATE (t:Transcript)-[r:CONTAINS_KEYWORD {
    occurrences: 15,
    positions: [12, 45, 78, 123]  // Word positions
}]->(k:Keyword)


// ============ EXAMPLE QUERIES ============

// Find all social profiles for a person
MATCH (p:Person {person_id: "uuid"})-[r:HAS_ACCOUNT]->(sp:SocialProfile)
WHERE r.confidence > 0.8
RETURN sp.platform, sp.url, r.confidence
ORDER BY r.confidence DESC

// Find videos where a person appears with high confidence
MATCH (p:Person {person_id: "uuid"})-[r:APPEARS_IN]->(v:Video)
WHERE r.average_confidence > 0.85
RETURN v.filename, r.frame_count, r.timestamps

// Find common topics discussed by a person across videos
MATCH (p:Person)-[:APPEARS_IN]->(v:Video)-[r:MENTIONS_TOPIC]->(k:Keyword)
RETURN k.term, COUNT(v) as video_count, SUM(r.frequency) as total_mentions
ORDER BY total_mentions DESC
LIMIT 10

// Cross-reference: Find persons who appear in videos discussing specific topics
MATCH (p:Person)-[:APPEARS_IN]->(v:Video)-[:MENTIONS_TOPIC]->(k:Keyword {term: "cybersecurity"})
WITH p, COUNT(DISTINCT v) as video_count
WHERE video_count > 2
MATCH (p)-[:HAS_ACCOUNT]->(sp:SocialProfile)
RETURN p.name, video_count, COLLECT(sp.platform) as social_presence

// Biometric triangulation: Link face encodings to known identities
MATCH (v:Video)-[:CONTAINS_FACE]->(fe:FaceEncoding)-[m:MATCHES_IDENTITY]->(p:Person)
WHERE m.similarity_score > 0.90
RETURN v.filename, p.name, m.similarity_score, fe.frame_timestamp
"""
