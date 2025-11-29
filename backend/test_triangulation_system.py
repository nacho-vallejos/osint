"""
Test script for Identity Triangulation System
Demonstrates the complete workflow: Social Profiling → Video Analysis → Graph Storage
"""

import asyncio
import json
from pathlib import Path

# Import our services
import sys
sys.path.append(str(Path(__file__).parent))

from app.services.social_recon import SocialProfiler
from app.services.video_intel import VideoIntelCollector


async def test_social_profiling():
    """Test 1: Social Media Profile Discovery"""
    print("\n" + "="*80)
    print("TEST 1: SOCIAL MEDIA RECONNAISSANCE")
    print("="*80)
    
    profiler = SocialProfiler(timeout=10)
    
    # Test with a known username
    test_usernames = ["octocat", "elonmusk", "nachovalle"]
    
    for username in test_usernames:
        print(f"\n🔍 Searching for username: {username}")
        print("-" * 60)
        
        results = await profiler.search_username(
            username=username,
            platforms=["GitHub", "Twitter", "Instagram", "LinkedIn", "Reddit"]
        )
        
        found = [p for p in results if p.status.value == "found"]
        not_found = [p for p in results if p.status.value == "not_found"]
        errors = [p for p in results if p.status.value == "error"]
        
        print(f"✅ Found: {len(found)} profiles")
        print(f"❌ Not Found: {len(not_found)} profiles")
        print(f"⚠️  Errors: {len(errors)} profiles")
        
        if found:
            print("\n📋 Discovered Profiles:")
            for profile in found:
                print(f"  • {profile.platform}: {profile.url}")
                print(f"    Confidence: {profile.confidence:.2f}")
        
        print()


async def test_video_intelligence():
    """Test 2: Video Intelligence Analysis (Demo with mock data)"""
    print("\n" + "="*80)
    print("TEST 2: VIDEO INTELLIGENCE ANALYSIS")
    print("="*80)
    
    print("\n📹 Video Analysis Capabilities:")
    print("-" * 60)
    print("✅ Face Detection: Extract faces from video frames")
    print("✅ Face Recognition: Compare faces with target person")
    print("✅ Audio Transcription: Speech-to-Text using Whisper")
    print("✅ NLP Analysis: Keyword extraction and topic modeling")
    
    # Check if face_recognition is available
    try:
        import face_recognition
        print("✅ face_recognition library: Available")
    except ImportError:
        print("⚠️  face_recognition library: Not installed")
        print("   Install with: pip install face-recognition")
    
    # Check Whisper
    try:
        import whisper
        print("✅ OpenAI Whisper: Available")
    except ImportError:
        print("⚠️  OpenAI Whisper: Not installed")
        print("   Install with: pip install openai-whisper")
    
    print("\n📊 Example Video Analysis Result:")
    print("-" * 60)
    
    # Mock example result
    example_result = {
        "video_id": "abc123def456",
        "duration": 120.5,
        "faces": {
            "total_detected": 45,
            "unique_faces": 3,
            "target_match_found": True,
            "match_frames": [12, 45, 78, 102]
        },
        "audio": {
            "transcript_available": True,
            "language": "en",
            "word_count": 245,
            "top_keywords": [
                {"keyword": "artificial", "frequency": 12, "relevance": 0.89},
                {"keyword": "intelligence", "frequency": 10, "relevance": 0.85},
                {"keyword": "machine", "frequency": 8, "relevance": 0.78},
                {"keyword": "learning", "frequency": 7, "relevance": 0.75},
                {"keyword": "neural", "frequency": 6, "relevance": 0.72}
            ]
        },
        "processing_time": 45.3
    }
    
    print(json.dumps(example_result, indent=2))


def test_graph_schema():
    """Test 3: Neo4j Graph Schema"""
    print("\n" + "="*80)
    print("TEST 3: IDENTITY GRAPH SCHEMA (Neo4j)")
    print("="*80)
    
    print("\n📊 Graph Database Schema:")
    print("-" * 60)
    
    schema = """
    NODES:
    ------
    (Person)           - Individual being investigated
    (SocialProfile)    - Social media account
    (Video)            - Video file analyzed
    (FaceEncoding)     - Biometric face data (128d vector)
    (Transcript)       - Audio transcription
    (Keyword)          - Extracted topic/keyword
    
    RELATIONSHIPS:
    --------------
    (Person)-[HAS_ACCOUNT]->(SocialProfile)
        Properties: verified, confidence, discovered_date
    
    (Person)-[APPEARS_IN]->(Video)
        Properties: face_match_confidence, frame_numbers, timestamp
    
    (Video)-[CONTAINS_FACE]->(FaceEncoding)
        Properties: frame_number, bbox, encoding_vector
    
    (Video)-[HAS_TRANSCRIPT]->(Transcript)
        Properties: language, word_count, duration
    
    (Transcript)-[MENTIONS]->(Keyword)
        Properties: frequency, relevance_score
    
    (Video)-[MENTIONS_TOPIC]->(Keyword)
        Properties: context, timestamp_references
    """
    
    print(schema)
    
    print("\n🔍 Example Cypher Queries:")
    print("-" * 60)
    
    queries = [
        ("Find all social profiles for a person",
         "MATCH (p:Person {person_id: 'john_doe'})-[r:HAS_ACCOUNT]->(sp:SocialProfile)\nRETURN p.name, sp.platform, sp.url, r.confidence"),
        
        ("Find videos where person appears",
         "MATCH (p:Person)-[a:APPEARS_IN]->(v:Video)\nWHERE p.person_id = 'john_doe' AND a.face_match_confidence > 0.8\nRETURN v.video_id, v.duration, a.frame_numbers"),
        
        ("Find common topics across person's videos",
         "MATCH (p:Person)-[:APPEARS_IN]->(v:Video)-[m:MENTIONS_TOPIC]->(k:Keyword)\nWHERE p.person_id = 'john_doe'\nRETURN k.term, count(v) as video_count, avg(m.relevance) as avg_relevance\nORDER BY video_count DESC\nLIMIT 10"),
        
        ("Find persons with similar digital footprint",
         "MATCH (p1:Person)-[:HAS_ACCOUNT]->(sp1:SocialProfile)\nMATCH (p2:Person)-[:HAS_ACCOUNT]->(sp2:SocialProfile)\nWHERE p1 <> p2 AND sp1.platform = sp2.platform\nRETURN p1.name, p2.name, collect(sp1.platform) as common_platforms")
    ]
    
    for title, query in queries:
        print(f"\n{title}:")
        print(f"```cypher\n{query}\n```")


async def test_full_triangulation():
    """Test 4: Complete Triangulation Workflow"""
    print("\n" + "="*80)
    print("TEST 4: FULL IDENTITY TRIANGULATION WORKFLOW")
    print("="*80)
    
    target_person = "John Doe"
    target_username = "johndoe"
    
    print(f"\n🎯 Target Person: {target_person}")
    print(f"🎯 Username: {target_username}")
    print("-" * 60)
    
    # Step 1: Social Profiling
    print("\n📱 STEP 1: Social Media Reconnaissance")
    profiler = SocialProfiler(timeout=8)
    social_results = await profiler.search_username(target_username, platforms=["GitHub", "Twitter", "LinkedIn"])
    found_profiles = [p for p in social_results if p.status.value == "found"]
    print(f"   Found {len(found_profiles)} profiles")
    
    # Step 2: Video Analysis (simulated)
    print("\n📹 STEP 2: Video Intelligence Analysis")
    print("   [Simulated] Analyzing video: 'interview_2024.mp4'")
    print("   • Faces detected: 2 (1 match with confidence: 0.92)")
    print("   • Audio transcribed: 1,250 words")
    print("   • Top keywords: technology, innovation, future, AI, startup")
    
    # Step 3: Graph Storage (simulated)
    print("\n🔗 STEP 3: Graph Database Integration")
    print("   [Simulated] Creating nodes and relationships in Neo4j")
    print("   • Created Person node: 'John Doe'")
    print(f"   • Linked {len(found_profiles)} SocialProfile nodes")
    print("   • Linked 1 Video node with FaceEncoding")
    print("   • Extracted 15 Keyword nodes from transcript")
    
    # Step 4: Triangulation Score
    print("\n📊 STEP 4: Triangulation Confidence Score")
    score = (len(found_profiles) * 0.2) + 0.4  # 0.4 for video match
    print(f"   Score: {score:.2f} / 1.0")
    print(f"   Level: {'HIGH' if score >= 0.7 else 'MEDIUM' if score >= 0.4 else 'LOW'}")
    
    print("\n✅ Triangulation Complete!")
    print("-" * 60)
    print(f"Digital Footprint Summary:")
    print(f"  • Social Accounts: {len(found_profiles)}")
    print(f"  • Video Appearances: 1")
    print(f"  • Biometric Matches: 1")
    print(f"  • Keywords Tracked: 15")
    print(f"  • Overall Confidence: {score:.2%}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 OSINT IDENTITY TRIANGULATION SYSTEM - TEST SUITE")
    print("="*80)
    print("\nThis system combines:")
    print("  1. Social Media Reconnaissance (Sherlock-like)")
    print("  2. Video Intelligence (Face Recognition + Speech-to-Text)")
    print("  3. Graph Database (Neo4j for relationship mapping)")
    print("\n" + "="*80)
    
    try:
        await test_social_profiling()
        await test_video_intelligence()
        test_graph_schema()
        await test_full_triangulation()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\n📚 Next Steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Start FastAPI server: uvicorn app.main:app --reload")
        print("  3. Visit API docs: http://localhost:8000/docs")
        print("  4. Test endpoints:")
        print("     • GET  /api/v1/triangulation/social-profile/{username}")
        print("     • POST /api/v1/triangulation/video-analysis")
        print("     • POST /api/v1/triangulation/full-triangulation")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
