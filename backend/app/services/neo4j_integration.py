"""
Neo4j Integration for Identity Triangulation
Stores and queries relationships between persons, social profiles, videos, and biometric data
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from neo4j import GraphDatabase, Driver
import logging


logger = logging.getLogger(__name__)


class IdentityGraphDB:
    """
    Neo4j database handler for OSINT identity triangulation
    Manages Person, SocialProfile, Video, FaceEncoding, Transcript, and Keyword nodes
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            user: Database username
            password: Database password
        """
        self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        self._create_indexes()
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
    
    def _create_indexes(self):
        """Create indexes for faster queries"""
        with self.driver.session() as session:
            # Create indexes
            session.run("CREATE INDEX person_id IF NOT EXISTS FOR (p:Person) ON (p.person_id)")
            session.run("CREATE INDEX social_profile_id IF NOT EXISTS FOR (sp:SocialProfile) ON (sp.profile_id)")
            session.run("CREATE INDEX video_id IF NOT EXISTS FOR (v:Video) ON (v.video_id)")
            session.run("CREATE INDEX video_checksum IF NOT EXISTS FOR (v:Video) ON (v.checksum)")
            session.run("CREATE INDEX keyword_term IF NOT EXISTS FOR (k:Keyword) ON (k.term)")
            
            logger.info("Neo4j indexes created/verified")
    
    # ========== PERSON NODES ==========
    
    def create_person(
        self,
        person_id: str,
        name: str,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create or update a Person node"""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (p:Person {person_id: $person_id})
                SET p.name = $name,
                    p.aliases = $aliases,
                    p.last_updated = datetime(),
                    p.metadata = $metadata
                ON CREATE SET p.first_seen = datetime()
                RETURN p
            """, person_id=person_id, name=name, aliases=aliases or [], metadata=metadata or {})
            
            record = result.single()
            return dict(record["p"]) if record else {}
    
    # ========== SOCIAL PROFILE INTEGRATION ==========
    
    def link_social_profiles(
        self,
        person_id: str,
        profiles: List[Dict[str, Any]]
    ) -> int:
        """
        Link social profiles to a person
        
        Args:
            person_id: Person identifier
            profiles: List of profile dicts from SocialProfiler
            
        Returns:
            Number of profiles linked
        """
        with self.driver.session() as session:
            linked_count = 0
            
            for profile in profiles:
                try:
                    session.run("""
                        MATCH (p:Person {person_id: $person_id})
                        MERGE (sp:SocialProfile {
                            platform: $platform,
                            username: $username
                        })
                        SET sp.url = $url,
                            sp.verified = true,
                            sp.confidence = $confidence,
                            sp.discovered_at = datetime(),
                            sp.metadata = $metadata
                        MERGE (p)-[r:HAS_ACCOUNT]->(sp)
                        SET r.verified_at = datetime(),
                            r.verification_method = 'social_profiler',
                            r.confidence = $confidence
                    """,
                        person_id=person_id,
                        platform=profile["platform"],
                        username=profile["username"],
                        url=profile["url"],
                        confidence=profile["confidence"],
                        metadata=profile.get("metadata", {})
                    )
                    linked_count += 1
                except Exception as e:
                    logger.error(f"Failed to link profile {profile['platform']}: {e}")
            
            logger.info(f"Linked {linked_count} social profiles to person {person_id}")
            return linked_count
    
    # ========== VIDEO INTELLIGENCE INTEGRATION ==========
    
    def create_video_node(
        self,
        video_result: Dict[str, Any]
    ) -> str:
        """
        Create Video node from VideoIntelCollector result
        
        Args:
            video_result: Result dict from VideoIntelCollector.to_dict()
            
        Returns:
            Video node ID (checksum)
        """
        video_data = video_result["video"]
        
        with self.driver.session() as session:
            result = session.run("""
                MERGE (v:Video {checksum: $checksum})
                SET v.filename = $filename,
                    v.duration = $duration,
                    v.fps = $fps,
                    v.frame_count = $frame_count,
                    v.resolution = $resolution,
                    v.analyzed_at = datetime()
                RETURN v.checksum as video_id
            """,
                checksum=video_data["checksum"],
                filename=video_data["path"],
                duration=video_data["duration"],
                fps=video_data["fps"],
                frame_count=video_data["frame_count"],
                resolution=video_data["resolution"]
            )
            
            record = result.single()
            video_id = record["video_id"] if record else video_data["checksum"]
            
            # Create transcript if available
            if video_result["audio_analysis"]["transcript"]:
                self._create_transcript(video_id, video_result["audio_analysis"]["transcript"])
            
            # Create keyword nodes
            self._create_keywords(video_id, video_result["audio_analysis"]["top_keywords"])
            
            # Create face encoding nodes
            self._create_face_encodings(video_id, video_result["vision_analysis"]["faces"])
            
            logger.info(f"Created video node: {video_id}")
            return video_id
    
    def _create_transcript(self, video_id: str, transcript: Dict[str, Any]):
        """Create Transcript node linked to Video"""
        with self.driver.session() as session:
            session.run("""
                MATCH (v:Video {checksum: $video_id})
                MERGE (t:Transcript {video_id: $video_id})
                SET t.full_text = $text,
                    t.language = $language,
                    t.word_count = $word_count,
                    t.confidence = $confidence,
                    t.duration = $duration
                MERGE (v)-[r:CONTAINS_AUDIO]->(t)
                SET r.extracted_at = datetime()
            """,
                video_id=video_id,
                text=transcript["text"],
                language=transcript["language"],
                word_count=transcript["word_count"],
                confidence=transcript["confidence"],
                duration=transcript["duration"]
            )
    
    def _create_keywords(self, video_id: str, keywords: List[Dict[str, Any]]):
        """Create Keyword nodes and link to Video"""
        with self.driver.session() as session:
            for kw in keywords:
                session.run("""
                    MATCH (v:Video {checksum: $video_id})
                    MERGE (k:Keyword {term: $term})
                    ON CREATE SET k.created_at = datetime()
                    MERGE (v)-[r:MENTIONS_TOPIC]->(k)
                    SET r.frequency = $frequency,
                        r.relevance_score = 0.85,
                        r.detected_at = datetime()
                """,
                    video_id=video_id,
                    term=kw["term"],
                    frequency=kw["frequency"]
                )
    
    def _create_face_encodings(self, video_id: str, faces: List[Dict[str, Any]]):
        """Create FaceEncoding nodes linked to Video"""
        with self.driver.session() as session:
            for face in faces:
                if not face.get("has_encoding"):
                    continue
                
                encoding_id = f"{video_id}_{face['frame_number']}"
                
                session.run("""
                    MATCH (v:Video {checksum: $video_id})
                    MERGE (fe:FaceEncoding {encoding_id: $encoding_id})
                    SET fe.frame_timestamp = $timestamp,
                        fe.frame_number = $frame_number,
                        fe.bbox = $bbox,
                        fe.confidence = $confidence
                    MERGE (v)-[r:CONTAINS_FACE]->(fe)
                    SET r.frame_number = $frame_number,
                        r.timestamp = $timestamp
                """,
                    video_id=video_id,
                    encoding_id=encoding_id,
                    timestamp=face["timestamp"],
                    frame_number=face["frame_number"],
                    bbox=face["bbox"],
                    confidence=face["confidence"]
                )
    
    def link_person_to_video(
        self,
        person_id: str,
        video_id: str,
        match_data: Dict[str, Any]
    ):
        """
        Create APPEARS_IN relationship between Person and Video
        
        Args:
            person_id: Person identifier
            video_id: Video checksum
            match_data: Data about face matches (timestamps, confidence, etc.)
        """
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Person {person_id: $person_id})
                MATCH (v:Video {checksum: $video_id})
                MERGE (p)-[r:APPEARS_IN]->(v)
                SET r.detected_at = datetime(),
                    r.frame_count = $frame_count,
                    r.average_confidence = $avg_confidence,
                    r.timestamps = $timestamps
            """,
                person_id=person_id,
                video_id=video_id,
                frame_count=match_data.get("frame_count", 0),
                avg_confidence=match_data.get("average_confidence", 0.0),
                timestamps=match_data.get("timestamps", [])
            )
            
            logger.info(f"Linked person {person_id} to video {video_id}")
    
    # ========== QUERY METHODS ==========
    
    def get_person_digital_footprint(self, person_id: str) -> Dict[str, Any]:
        """Get complete digital footprint for a person"""
        with self.driver.session() as session:
            # Social profiles
            profiles_result = session.run("""
                MATCH (p:Person {person_id: $person_id})-[r:HAS_ACCOUNT]->(sp:SocialProfile)
                RETURN sp.platform as platform, sp.url as url, r.confidence as confidence
                ORDER BY r.confidence DESC
            """, person_id=person_id)
            
            profiles = [dict(record) for record in profiles_result]
            
            # Video appearances
            videos_result = session.run("""
                MATCH (p:Person {person_id: $person_id})-[r:APPEARS_IN]->(v:Video)
                RETURN v.filename as filename, 
                       v.duration as duration,
                       r.frame_count as appearances,
                       r.average_confidence as confidence
                ORDER BY r.detected_at DESC
            """, person_id=person_id)
            
            videos = [dict(record) for record in videos_result]
            
            return {
                "person_id": person_id,
                "social_profiles": profiles,
                "video_appearances": videos
            }
    
    def find_people_by_topic(self, topic: str, min_mentions: int = 5) -> List[Dict[str, Any]]:
        """Find people who frequently discuss a specific topic"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[:APPEARS_IN]->(v:Video)-[r:MENTIONS_TOPIC]->(k:Keyword {term: $topic})
                WITH p, COUNT(DISTINCT v) as video_count, SUM(r.frequency) as total_mentions
                WHERE total_mentions >= $min_mentions
                MATCH (p)-[:HAS_ACCOUNT]->(sp:SocialProfile)
                RETURN p.name as name,
                       p.person_id as person_id,
                       video_count,
                       total_mentions,
                       COLLECT(sp.platform) as social_platforms
                ORDER BY total_mentions DESC
            """, topic=topic, min_mentions=min_mentions)
            
            return [dict(record) for record in result]
    
    def find_common_video_appearances(
        self,
        person_id_1: str,
        person_id_2: str
    ) -> List[Dict[str, Any]]:
        """Find videos where two people appear together"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p1:Person {person_id: $pid1})-[:APPEARS_IN]->(v:Video)<-[:APPEARS_IN]-(p2:Person {person_id: $pid2})
                RETURN v.filename as filename,
                       v.checksum as video_id,
                       v.duration as duration
            """, pid1=person_id_1, pid2=person_id_2)
            
            return [dict(record) for record in result]
    
    def get_video_intelligence_summary(self, video_id: str) -> Dict[str, Any]:
        """Get complete intelligence summary for a video"""
        with self.driver.session() as session:
            # Basic video info
            video_result = session.run("""
                MATCH (v:Video {checksum: $video_id})
                RETURN v.filename as filename,
                       v.duration as duration,
                       v.resolution as resolution
            """, video_id=video_id)
            
            video_record = video_result.single()
            if not video_record:
                return {}
            
            # People detected
            people_result = session.run("""
                MATCH (p:Person)-[r:APPEARS_IN]->(v:Video {checksum: $video_id})
                RETURN p.name as name,
                       r.average_confidence as confidence,
                       r.frame_count as appearances
            """, video_id=video_id)
            
            people = [dict(record) for record in people_result]
            
            # Topics discussed
            topics_result = session.run("""
                MATCH (v:Video {checksum: $video_id})-[r:MENTIONS_TOPIC]->(k:Keyword)
                RETURN k.term as topic, r.frequency as frequency
                ORDER BY r.frequency DESC
                LIMIT 10
            """, video_id=video_id)
            
            topics = [dict(record) for record in topics_result]
            
            # Transcript
            transcript_result = session.run("""
                MATCH (v:Video {checksum: $video_id})-[:CONTAINS_AUDIO]->(t:Transcript)
                RETURN t.full_text as text, t.language as language
            """, video_id=video_id)
            
            transcript_record = transcript_result.single()
            transcript = dict(transcript_record) if transcript_record else None
            
            return {
                "video": dict(video_record),
                "people_detected": people,
                "top_topics": topics,
                "transcript": transcript
            }
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Example usage
if __name__ == "__main__":
    """
    Example: Complete identity triangulation workflow
    
    Setup:
        1. Install Neo4j: https://neo4j.com/download/
        2. Start Neo4j: neo4j start
        3. Access browser: http://localhost:7474
        4. Set password: neo4j/password
    """
    
    import asyncio
    import os
    from app.services.social_recon import SocialProfiler
    from app.services.video_intel import VideoIntelCollector
    
    async def triangulation_workflow():
        # Connect to Neo4j
        graph_db = IdentityGraphDB(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        
        try:
            # Step 1: Discover social profiles
            print("Step 1: Social Profile Discovery")
            async with SocialProfiler() as profiler:
                profiles = await profiler.get_confirmed_profiles("elonmusk")
                
                # Create person node
                person_id = "person_elon_musk"
                graph_db.create_person(
                    person_id=person_id,
                    name="Elon Musk",
                    aliases=["elonmusk", "elon"]
                )
                
                # Link social profiles
                profile_dicts = [p.to_dict() for p in profiles]
                graph_db.link_social_profiles(person_id, profile_dicts)
                
                print(f"  Linked {len(profiles)} social profiles")
            
            # Step 2: Analyze video
            print("\nStep 2: Video Intelligence Analysis")
            video_path = "elon_interview.mp4"  # Example video
            
            if os.path.exists(video_path):
                collector = VideoIntelCollector()
                result = await collector.analyze_video(video_path)
                
                # Store video in graph
                video_id = graph_db.create_video_node(result.to_dict())
                print(f"  Created video node: {video_id}")
                
                # Link person to video (if face match found)
                if result.target_face_matches:
                    match_data = {
                        "frame_count": len(result.target_face_matches),
                        "average_confidence": sum(m.confidence for m in result.target_face_matches) / len(result.target_face_matches),
                        "timestamps": [m.timestamp for m in result.target_face_matches]
                    }
                    
                    graph_db.link_person_to_video(person_id, video_id, match_data)
                    print(f"  Linked person to video appearance")
            
            # Step 3: Query graph
            print("\nStep 3: Query Digital Footprint")
            footprint = graph_db.get_person_digital_footprint(person_id)
            
            print(f"  Social Profiles: {len(footprint['social_profiles'])}")
            for profile in footprint['social_profiles'][:3]:
                print(f"    - {profile['platform']}: {profile['url']}")
            
            print(f"  Video Appearances: {len(footprint['video_appearances'])}")
            
        finally:
            graph_db.close()
    
    # Run workflow
    # asyncio.run(triangulation_workflow())
    
    print("Example workflow defined. Uncomment last line to run.")
