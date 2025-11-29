"""
Identity Triangulation API Routes
Endpoints for advanced OSINT combining social profiles, video intelligence, and graph analysis
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel, Field
import tempfile
import os

from app.services.social_recon import SocialProfiler

# Video intelligence is optional (requires heavy dependencies: opencv, whisper, face_recognition)
VIDEO_INTEL_AVAILABLE = False
VideoIntelCollector = None

try:
    # Check if dependencies are available before importing
    import cv2
    import numpy
    import whisper
    from moviepy.editor import VideoFileClip
    
    # If all dependencies are available, import the collector
    from app.services.video_intel import VideoIntelCollector
    VIDEO_INTEL_AVAILABLE = True
except (ImportError, AttributeError) as e:
    # Dependencies not available - video intelligence disabled
    pass


router = APIRouter(prefix="/triangulation", tags=["Identity Triangulation"])


# ========== REQUEST/RESPONSE MODELS ==========

class SocialProfileRequest(BaseModel):
    """Request to discover social profiles"""
    username: str = Field(..., description="Username to search across platforms")
    platforms: Optional[List[str]] = Field(
        None,
        description="Specific platforms to search (default: all)"
    )
    timeout: int = Field(10, description="Timeout per platform in seconds")


class SocialProfileResponse(BaseModel):
    """Response with discovered social profiles"""
    username: str
    profiles_found: int
    profiles: List[dict]
    execution_time: float


class VideoAnalysisRequest(BaseModel):
    """Metadata for video analysis request"""
    analyze_faces: bool = Field(True, description="Enable face detection and recognition")
    analyze_audio: bool = Field(True, description="Enable audio transcription and NLP")
    frame_sample_rate: int = Field(30, description="Extract one frame every N frames")
    whisper_model: str = Field("base", description="Whisper model size: tiny, base, small, medium, large")
    target_face_path: Optional[str] = Field(None, description="Path to target face image for matching")


class VideoAnalysisResponse(BaseModel):
    """Response with video intelligence results"""
    video_id: str
    duration: float
    faces_detected: int
    unique_faces: int
    target_match_found: Optional[bool]
    transcript_available: bool
    transcript_word_count: int
    top_keywords: List[dict]
    execution_time: float


class TriangulationRequest(BaseModel):
    """Combined identity triangulation request"""
    username: str
    person_name: str
    video_path: Optional[str] = None
    analyze_social: bool = True
    analyze_video: bool = False


# ========== SOCIAL PROFILING ENDPOINTS ==========

@router.post("/social-profile", response_model=SocialProfileResponse)
async def discover_social_profiles(request: SocialProfileRequest):
    """
    Discover social media profiles for a given username
    Uses Sherlock-like async verification across multiple platforms
    """
    try:
        profiler = SocialProfiler(timeout=request.timeout)
        
        # Run profile discovery
        results = await profiler.discover_profiles(
            username=request.username,
            platforms=request.platforms
        )
        
        # Extract found profiles
        found_profiles = [
            profile.to_dict() 
            for profile in results 
            if profile.status.value == "found"
        ]
        
        return SocialProfileResponse(
            username=request.username,
            profiles_found=len(found_profiles),
            profiles=found_profiles,
            execution_time=results[0].metadata.get("elapsed_time", 0.0) if results else 0.0
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile discovery failed: {str(e)}")


@router.get("/social-profile/{username}")
async def get_social_profile_simple(username: str):
    """
    Quick social profile lookup (GET method for easy testing)
    Searches top platforms: Twitter, GitHub, Instagram, LinkedIn
    """
    try:
        profiler = SocialProfiler(timeout=8)
        
        top_platforms = ["GitHub", "Twitter", "Instagram", "LinkedIn", "Reddit"]
        results = await profiler.discover_profiles(username, platforms=top_platforms)
        
        found = [p.to_dict() for p in results if p.status.value == "found"]
        
        return {
            "username": username,
            "found_count": len(found),
            "profiles": found,
            "checked_platforms": top_platforms
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== VIDEO INTELLIGENCE ENDPOINTS ==========

@router.post("/video-analysis", response_model=VideoAnalysisResponse)
async def analyze_video_file(
    video: UploadFile = File(..., description="Video file to analyze"),
    analyze_faces: bool = Form(True),
    analyze_audio: bool = Form(True),
    frame_sample_rate: int = Form(30),
    whisper_model: str = Form("base"),
    target_face_path: Optional[str] = Form(None)
):
    """
    Analyze video file for facial recognition and audio transcription
    WARNING: This is a heavy operation - consider using Celery for production
    """
    if not VIDEO_INTEL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Video intelligence not available. Install: pip install opencv-python moviepy openai-whisper face-recognition"
        )
    
    temp_video_path = None
    
    try:
        # Save uploaded video to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            content = await video.read()
            temp_file.write(content)
            temp_video_path = temp_file.name
        
        # Initialize video intelligence collector
        collector = VideoIntelCollector(
            frame_sample_rate=frame_sample_rate,
            whisper_model_size=whisper_model
        )
        
        # Load target face if provided
        target_encoding = None
        if target_face_path and os.path.exists(target_face_path):
            target_encoding = collector.load_target_face(target_face_path)
        
        # Analyze video
        result = await collector.analyze_video(
            video_path=temp_video_path,
            analyze_faces=analyze_faces,
            analyze_audio=analyze_audio,
            target_face_encoding=target_encoding
        )
        
        # Build response
        return VideoAnalysisResponse(
            video_id=result.video_id,
            duration=result.duration,
            faces_detected=result.total_faces_detected,
            unique_faces=result.unique_faces_count,
            target_match_found=result.target_match_found,
            transcript_available=result.transcript is not None,
            transcript_word_count=result.transcript.word_count if result.transcript else 0,
            top_keywords=result.top_keywords[:10],
            execution_time=result.processing_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")
    
    finally:
        # Cleanup temp file
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
            except:
                pass


@router.post("/video-analysis-path")
async def analyze_video_by_path(request: VideoAnalysisRequest, video_path: str = Form(...)):
    """
    Analyze video file by providing server-side path
    Useful for processing videos already on the server
    """
    if not VIDEO_INTEL_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Video intelligence not available. Install required dependencies first."
        )
    
    try:
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        collector = VideoIntelCollector(
            frame_sample_rate=request.frame_sample_rate,
            whisper_model_size=request.whisper_model
        )
        
        # Load target face if specified
        target_encoding = None
        if request.target_face_path and os.path.exists(request.target_face_path):
            target_encoding = collector.load_target_face(request.target_face_path)
        
        # Analyze video
        result = await collector.analyze_video(
            video_path=video_path,
            analyze_faces=request.analyze_faces,
            analyze_audio=request.analyze_audio,
            target_face_encoding=target_encoding
        )
        
        return {
            "video_id": result.video_id,
            "video_path": video_path,
            "duration": result.duration,
            "faces": {
                "total_detected": result.total_faces_detected,
                "unique_count": result.unique_faces_count,
                "target_match": result.target_match_found
            },
            "audio": {
                "transcript_available": result.transcript is not None,
                "word_count": result.transcript.word_count if result.transcript else 0,
                "language": result.transcript.language if result.transcript else None,
                "top_keywords": result.top_keywords[:15]
            },
            "processing_time": result.processing_time
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== COMBINED TRIANGULATION ==========

@router.post("/full-triangulation")
async def full_identity_triangulation(request: TriangulationRequest):
    """
    Complete identity triangulation combining social profiling and video analysis
    Returns comprehensive digital footprint and biometric data
    """
    result = {
        "person_name": request.person_name,
        "username": request.username,
        "social_profiles": None,
        "video_analysis": None,
        "triangulation_score": 0.0
    }
    
    try:
        # Step 1: Social Profile Discovery
        if request.analyze_social:
            profiler = SocialProfiler(timeout=10)
            social_results = await profiler.discover_profiles(request.username)
            
            found_profiles = [
                p.to_dict() 
                for p in social_results 
                if p.status.value == "found"
            ]
            
            result["social_profiles"] = {
                "found_count": len(found_profiles),
                "profiles": found_profiles,
                "platforms_checked": len(social_results)
            }
        
        # Step 2: Video Intelligence (if video provided)
        if request.analyze_video and request.video_path:
            if not VIDEO_INTEL_AVAILABLE:
                result["video_analysis"] = {"error": "Video intelligence not available"}
            elif not os.path.exists(request.video_path):
                result["video_analysis"] = {"error": "Video file not found"}
            else:
                collector = VideoIntelCollector()
                video_result = await collector.analyze_video(
                    video_path=request.video_path,
                    analyze_faces=True,
                    analyze_audio=True
                )
                
                result["video_analysis"] = {
                    "video_id": video_result.video_id,
                    "duration": video_result.duration,
                    "faces_detected": video_result.total_faces_detected,
                    "unique_faces": video_result.unique_faces_count,
                    "transcript_words": video_result.transcript.word_count if video_result.transcript else 0,
                    "top_keywords": video_result.top_keywords[:10]
                }
        
        # Step 3: Calculate triangulation confidence score
        score = 0.0
        if result["social_profiles"]:
            score += min(result["social_profiles"]["found_count"] * 0.15, 0.6)
        if result["video_analysis"] and "error" not in result["video_analysis"]:
            if result["video_analysis"]["faces_detected"] > 0:
                score += 0.2
            if result["video_analysis"]["transcript_words"] > 50:
                score += 0.2
        
        result["triangulation_score"] = round(score, 2)
        result["confidence_level"] = (
            "high" if score >= 0.7 else
            "medium" if score >= 0.4 else
            "low"
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triangulation failed: {str(e)}")


# ========== HEALTH CHECK ==========

@router.get("/health")
async def triangulation_health():
    """Check if triangulation services are available"""
    services_status = {
        "social_profiler": "available",
        "video_intel": "available" if VIDEO_INTEL_AVAILABLE else "not_available",
        "face_recognition": "not_available",
        "whisper": "not_available"
    }
    
    if VIDEO_INTEL_AVAILABLE:
        try:
            import face_recognition
            services_status["face_recognition"] = "available"
        except ImportError:
            pass
        
        try:
            import whisper
            services_status["whisper"] = "available"
        except ImportError:
            pass
    
    return {
        "status": "healthy",
        "services": services_status,
        "capabilities": {
            "social_profile_discovery": True,
            "video_facial_recognition": services_status["face_recognition"] == "available",
            "video_audio_transcription": services_status["whisper"] == "available",
            "keyword_extraction": VIDEO_INTEL_AVAILABLE
        },
        "note": "Video intelligence requires: pip install opencv-python moviepy openai-whisper face-recognition"
    }
