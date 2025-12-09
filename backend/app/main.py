"""
OSINT Video Analysis Platform - Backend API
Version: 3.2.0 - Enhanced OpenCV with improved synchronization

Features:
- Enhanced OpenCV Face Detection (Frontal + Profile)
- Precise timestamp synchronization via CAP_PROP_POS_MSEC
- Faster-Whisper Audio Transcription (base model)
- Audio alerts with start/end times
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip
from faster_whisper import WhisperModel
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OSINT Video Analysis Platform",
    description="Advanced video analysis with face detection and audio transcription",
    version="3.2.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EnhancedFaceDetector:
    """
    Enhanced OpenCV face detector with multiple methods for better coverage.
    """
    
    def __init__(self, min_confidence: float = 0.6):
        """Initialize face detectors."""
        self.min_confidence = min_confidence
        
        # Load Haar cascades
        self.haar_frontal = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.haar_profile = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        )
        
        logger.info(f"Enhanced Face Detector initialized (confidence: {min_confidence})")
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """Detect faces using multiple methods."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        all_faces = []
        
        # Frontal faces
        frontal_faces = self.haar_frontal.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        for (x, y, w, h) in frontal_faces:
            all_faces.append({
                "box": [int(y), int(x), int(h), int(w)],
                "confidence": 0.85
            })
        
        # Profile faces
        profile_faces = self.haar_profile.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        for (x, y, w, h) in profile_faces:
            # Check for overlaps
            is_duplicate = False
            for existing in all_faces:
                ey, ex, eh, ew = existing["box"]
                overlap_x = max(0, min(x + w, ex + ew) - max(x, ex))
                overlap_y = max(0, min(y + h, ey + eh) - max(y, ey))
                overlap_area = overlap_x * overlap_y
                
                if overlap_area > 0.3 * (w * h):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                all_faces.append({
                    "box": [int(y), int(x), int(h), int(w)],
                    "confidence": 0.75
                })
        
        return all_faces


class AudioTranscriber:
    """Audio transcription with Faster-Whisper."""
    
    def __init__(self, model_size: str = "base"):
        """Initialize Whisper model."""
        try:
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info(f"Faster-Whisper initialized with {model_size} model")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
            logger.info("Falling back to tiny model")
    
    def extract_and_transcribe(
        self, 
        video_path: str, 
        keywords: List[str]
    ) -> tuple[List[Dict], Optional[str]]:
        """Extract audio and find keywords."""
        audio_path = None
        audio_alerts = []
        
        try:
            logger.info(f"Extracting audio from: {video_path}")
            video = VideoFileClip(video_path)
            
            if video.audio is None:
                logger.warning("Video has no audio track")
                video.close()
                return [], None
            
            audio_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            video.audio.write_audiofile(audio_path, logger=None, verbose=False)
            video.close()
            
            logger.info(f"Audio extracted to: {audio_path}")
            
            if not keywords:
                logger.info("No keywords provided, skipping transcription")
                return [], audio_path
            
            logger.info(f"Transcribing audio and searching for: {keywords}")
            
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                language="es",
                condition_on_previous_text=True,
                vad_filter=True
            )
            
            keywords_lower = [kw.strip().lower() for kw in keywords if kw.strip()]
            
            segment_count = 0
            for segment in segments:
                segment_count += 1
                text = segment.text.strip()
                text_lower = text.lower()
                
                for keyword in keywords_lower:
                    if keyword in text_lower:
                        audio_alerts.append({
                            "start": float(segment.start),
                            "end": float(segment.end),
                            "text": text,
                            "keyword": keyword
                        })
                        logger.info(f"✓ Keyword '{keyword}' found at {segment.start:.1f}s: {text}")
            
            logger.info(f"Transcription complete: {segment_count} segments, {len(audio_alerts)} matches")
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}", exc_info=True)
        
        return audio_alerts, audio_path


def process_video(file_path: str, keywords: List[str]) -> Dict:
    """Process video with face detection and audio transcription."""
    # Initialize
    face_detector = EnhancedFaceDetector(min_confidence=0.6)
    audio_transcriber = AudioTranscriber(model_size="base")
    
    # Audio processing
    audio_alerts, audio_path = audio_transcriber.extract_and_transcribe(file_path, keywords)
    
    # Video processing with precise timestamps
    logger.info("Starting video face detection...")
    cap = cv2.VideoCapture(file_path)
    
    if not cap.isOpened():
        raise ValueError("Failed to open video file")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps if fps > 0 else 0
    
    face_detections = []
    frame_skip = 3  # Process every 3rd frame
    frame_count = 0
    frames_analyzed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            # Get precise timestamp from video position
            timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            timestamp = timestamp_ms / 1000.0
            
            # Detect faces
            faces = face_detector.detect_faces(frame)
            
            if faces:
                # Convert numpy types to Python native
                faces_serializable = []
                for face in faces:
                    box = [int(x) if isinstance(x, (np.integer, np.int32, np.int64)) else float(x) 
                           for x in face["box"]]
                    faces_serializable.append({
                        "box": box,
                        "confidence": float(face["confidence"])
                    })
                
                face_detections.append({
                    "timestamp": round(timestamp, 3),  # More precision
                    "faces": faces_serializable
                })
            
            frames_analyzed += 1
        
        frame_count += 1
    
    cap.release()
    
    logger.info(f"Video analysis complete: {len(face_detections)} frames with faces detected")
    
    # Cleanup audio file
    if audio_path and os.path.exists(audio_path):
        try:
            os.unlink(audio_path)
            logger.info("Temporary audio file deleted")
        except Exception as e:
            logger.warning(f"Failed to delete audio file: {e}")
    
    return {
        "fps": round(fps, 2),
        "video_duration": round(video_duration, 2),
        "total_frames": total_frames,
        "frames_analyzed": frames_analyzed,
        "faces": face_detections,
        "audio_alerts": audio_alerts
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "OSINT Video Analysis Platform",
        "version": "3.2.0",
        "features": [
            "Enhanced OpenCV Face Detection (Frontal + Profile)",
            "Precise timestamp synchronization (CAP_PROP_POS_MSEC)",
            "Faster-Whisper Audio Transcription (base model)",
            "Audio alerts with start/end times",
            "VAD filtering for silence removal"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "service": "osint-video-analysis",
        "version": "3.2.0",
        "models": {
            "face_detection": "OpenCV Enhanced (Frontal + Profile)",
            "audio_transcription": "Faster-Whisper (base, Spanish/English)"
        }
    }


@app.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...),
    keywords: Optional[str] = Form(None)
):
    """Analyze video with face detection and audio keywords."""
    video_path = None
    
    try:
        # Validate file type
        allowed_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save video
        video_path = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False).name
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Video uploaded: {file.filename} ({len(content)} bytes)")
        
        # Parse keywords
        keywords_list = []
        if keywords and keywords.strip():
            keywords_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        
        logger.info(f"Keywords: {keywords_list}")
        
        # Process video
        results = process_video(video_path, keywords_list)
        
        # Response
        response = {
            "status": "success",
            "filename": file.filename,
            "fps": results["fps"],
            "video_duration": results["video_duration"],
            "total_frames": results["total_frames"],
            "frames_analyzed": results["frames_analyzed"],
            "faces": results["faces"],
            "audio_alerts": results["audio_alerts"],
            "detection_config": {
                "face_detector": "OpenCV Enhanced (Frontal + Profile)",
                "min_confidence": 0.6,
                "frame_skip": 3,
                "audio_model": "Faster-Whisper (base)" if keywords_list else "disabled",
                "keywords_searched": keywords_list
            }
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
                logger.info("Temporary video file deleted")
            except Exception as e:
                logger.warning(f"Failed to delete video file: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
