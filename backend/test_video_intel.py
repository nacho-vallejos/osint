"""
Test script for VideoIntelCollector service
Demonstrates video analysis with face detection and transcription
NOTE: Requires a sample video file to test
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.video_intel import VideoIntelCollector, FACE_RECOGNITION_AVAILABLE


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_sample_video_info():
    """Display instructions for getting a sample video"""
    print("""
    📹 VIDEO INTEL COLLECTOR TEST
    
    To test this module, you need a video file. Options:
    
    1. Download a sample video:
       wget https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4
    
    2. Use your own video:
       - Place a video file in the backend directory
       - Name it 'test_video.mp4'
    
    3. Create a simple test video with ffmpeg:
       ffmpeg -f lavfi -i testsrc=duration=10:size=640x480:rate=30 test_video.mp4
    """)


async def test_video_intel_basic():
    """Basic video intelligence test"""
    
    print("=" * 70)
    print("🎬 VIDEO INTELLIGENCE COLLECTOR TEST")
    print("=" * 70)
    
    # Check for sample video
    video_path = "test_video.mp4"
    
    if not os.path.exists(video_path):
        create_sample_video_info()
        print(f"\n❌ Video file not found: {video_path}")
        print("Please provide a test video and run again.\n")
        return
    
    # Initialize collector
    collector = VideoIntelCollector(
        frame_sample_rate=30,  # Sample 1 frame per second (at 30fps)
        whisper_model="tiny",  # Use tiny model for faster testing
        face_detection_model="hog"  # Use HOG (faster, CPU-friendly)
    )
    
    print(f"\n📊 Collector Configuration:")
    print(f"  • Frame Sample Rate: 1 frame every {collector.frame_sample_rate} frames")
    print(f"  • Whisper Model: {collector.whisper_model_name}")
    print(f"  • Face Detection: {collector.face_detection_model}")
    print(f"  • Face Recognition Available: {FACE_RECOGNITION_AVAILABLE}")
    
    # Analyze video
    print(f"\n🔍 Analyzing video: {video_path}")
    print("This may take a few minutes...\n")
    
    try:
        result = await collector.analyze_video(video_path)
        
        # Display results
        print("=" * 70)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 70)
        
        # Video metadata
        print(f"\n📹 VIDEO METADATA:")
        print(f"  • File: {result.video_path}")
        print(f"  • Checksum: {result.checksum[:16]}...")
        print(f"  • Duration: {result.duration:.2f}s")
        print(f"  • FPS: {result.fps:.2f}")
        print(f"  • Frame Count: {result.frame_count}")
        print(f"  • Resolution: {result.resolution[0]}x{result.resolution[1]}")
        
        # Vision analysis
        print(f"\n👤 VISION ANALYSIS:")
        print(f"  • Total Faces Detected: {len(result.faces_detected)}")
        print(f"  • Unique Faces: {result.unique_face_count}")
        print(f"  • Target Matches: {len(result.target_face_matches)}")
        
        if result.faces_detected:
            print(f"\n  Face Detections (first 5):")
            for face in result.faces_detected[:5]:
                print(f"    - Frame {face.frame_number} @ {face.timestamp:.2f}s")
                print(f"      BBox: ({face.bbox[3]}, {face.bbox[0]}) to ({face.bbox[1]}, {face.bbox[2]})")
                print(f"      Has Encoding: {face.encoding is not None}")
        
        # Audio analysis
        print(f"\n🎤 AUDIO ANALYSIS:")
        if result.transcript:
            print(f"  • Language: {result.transcript.language}")
            print(f"  • Word Count: {result.transcript.word_count}")
            print(f"  • Confidence: {result.transcript.confidence:.2f}")
            print(f"  • Segments: {len(result.transcript.segments)}")
            
            if result.transcript.text:
                preview = result.transcript.text[:200]
                print(f"\n  📝 Transcript Preview:")
                print(f"     \"{preview}{'...' if len(result.transcript.text) > 200 else ''}\"")
        else:
            print(f"  • No audio track or transcription failed")
        
        # Keywords
        print(f"\n🔑 KEYWORD EXTRACTION:")
        if result.top_keywords:
            print(f"  Top {len(result.top_keywords)} keywords:")
            for keyword, freq in result.top_keywords[:10]:
                bar = "█" * min(freq, 20)
                print(f"    {keyword:20} {bar} ({freq})")
        else:
            print(f"  • No keywords extracted")
        
        # Errors
        if result.errors:
            print(f"\n⚠️  ERRORS:")
            for error in result.errors:
                print(f"  • {error}")
        
        # Graph relationships
        print(f"\n🔗 GRAPH RELATIONSHIPS:")
        print(f"  Video(id='{result.checksum[:8]}...')")
        print(f"    └─[CONTAINS_FACE]─> {len(result.faces_detected)} FaceEncoding nodes")
        if result.transcript:
            print(f"    └─[CONTAINS_AUDIO]─> Transcript(words={result.transcript.word_count})")
        for keyword, freq in result.top_keywords[:5]:
            print(f"    └─[MENTIONS_TOPIC]─> Keyword('{keyword}', freq={freq})")
        
        # Save result to JSON
        import json
        output_file = "video_analysis_result.json"
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        print(f"\n💾 Full results saved to: {output_file}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


async def test_with_target_face():
    """Test face matching with a target face"""
    
    print("\n" + "=" * 70)
    print("🎯 FACE MATCHING TEST (with target face)")
    print("=" * 70)
    
    if not FACE_RECOGNITION_AVAILABLE:
        print("❌ face_recognition library not available")
        return
    
    video_path = "test_video.mp4"
    target_image = "target_face.jpg"  # Image of person to find
    
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return
    
    if not os.path.exists(target_image):
        print(f"⚠️  Target face image not found: {target_image}")
        print("Skipping face matching test...")
        return
    
    try:
        import face_recognition
        
        # Load target face
        print(f"Loading target face from: {target_image}")
        target_img = face_recognition.load_image_file(target_image)
        target_encodings = face_recognition.face_encodings(target_img)
        
        if not target_encodings:
            print("❌ No face found in target image")
            return
        
        target_encoding = target_encodings[0]
        print(f"✅ Target face loaded (encoding vector: 128d)")
        
        # Analyze video with target
        collector = VideoIntelCollector(
            frame_sample_rate=15,  # More frequent sampling for face matching
            whisper_model="tiny",
            face_detection_model="hog"
        )
        
        print(f"\nSearching for target face in video...")
        result = await collector.analyze_video(
            video_path,
            target_face_encoding=target_encoding
        )
        
        print(f"\n🎯 FACE MATCHING RESULTS:")
        print(f"  • Total Faces: {len(result.faces_detected)}")
        print(f"  • Target Matches: {len(result.target_face_matches)}")
        
        if result.target_face_matches:
            print(f"\n  ✅ Target face found at:")
            for match in result.target_face_matches:
                print(f"    - Frame {match.frame_number} @ {match.timestamp:.2f}s (confidence: {match.confidence:.2f})")
            
            print(f"\n  🔗 Graph Relationship:")
            print(f"    Person(id='target') -[APPEARS_IN]-> Video")
            print(f"      Properties: {{")
            print(f"        frame_count: {len(result.target_face_matches)},")
            timestamps = [m.timestamp for m in result.target_face_matches]
            print(f"        timestamps: {timestamps[:5]},")
            avg_conf = sum(m.confidence for m in result.target_face_matches) / len(result.target_face_matches)
            print(f"        average_confidence: {avg_conf:.2f}")
            print(f"      }}")
        else:
            print(f"  ❌ Target face not found in video")
    
    except Exception as e:
        print(f"❌ Face matching test failed: {e}")
        import traceback
        traceback.print_exc()


def test_celery_integration():
    """Show Celery task integration example"""
    
    print("\n" + "=" * 70)
    print("🔄 CELERY INTEGRATION EXAMPLE")
    print("=" * 70 + "\n")
    
    print("""
    To use VideoIntelCollector with Celery for async processing:
    
    1. Install Celery and Redis:
       pip install celery redis
    
    2. Start Redis:
       redis-server
    
    3. Create celery_app.py:
    
       from celery import Celery
       from app.services.video_intel import create_celery_task
       
       app = Celery('osint', broker='redis://localhost:6379/0')
       analyze_video_task = create_celery_task(app)
    
    4. Start Celery worker:
       celery -A celery_app worker --loglevel=info
    
    5. Submit task:
       from celery_app import analyze_video_task
       
       task = analyze_video_task.delay('video.mp4')
       result = task.get()  # Wait for completion
    
    6. Monitor with Flower:
       pip install flower
       celery -A celery_app flower
       # Open http://localhost:5555
    """)


if __name__ == "__main__":
    print("\n🚀 Starting VideoIntelCollector Tests\n")
    
    try:
        # Check dependencies
        missing_deps = []
        
        try:
            import cv2
        except ImportError:
            missing_deps.append("opencv-python")
        
        try:
            import whisper
        except ImportError:
            missing_deps.append("openai-whisper")
        
        try:
            from moviepy.editor import VideoFileClip
        except ImportError:
            missing_deps.append("moviepy")
        
        if missing_deps:
            print("⚠️  Missing dependencies:")
            for dep in missing_deps:
                print(f"  • {dep}")
            print("\nInstall with: pip install " + " ".join(missing_deps))
            print()
        
        # Run tests
        asyncio.run(test_video_intel_basic())
        asyncio.run(test_with_target_face())
        test_celery_integration()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
