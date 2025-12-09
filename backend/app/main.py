"""
OSINT Video Analysis Platform - Backend API
Version: 3.0.0 - Enhanced with Face Recognition and Audio Analysis

Features:
- Face Recognition Library (dlib-based, high accuracy)
- Faster-Whisper Audio Transcription with Keyword Spotting
- FastAPI REST endpoints
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
    description="Advanced video analysis with facial detection and audio keyword spotting",
    version="3.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CVFaceDetector:
    """
    OpenCV-based face detector with Haar Cascades and DNN option.
    Provides high accuracy with configurable confidence thresholds.
    """
    
    def __init__(self, method: str = "dnn", min_confidence: float = 0.75):
        """
        Initialize Face Detector.
        
        Args:
            method: 'haar' or 'dnn' (DNN is more accurate)
            min_confidence: Minimum confidence threshold (0.75 filters false positives)
        """
        self.method = method
        self.min_confidence = min_confidence
        
        if method == "dnn":
            # Load DNN face detector (more accurate)
            model_file = "deploy.prototxt"
            weights_file = "res10_300x300_ssd_iter_140000.caffemodel"
            
            # Try to use DNN, fallback to Haar if models not available
            try:
                self.net = cv2.dnn.readNetFromCaffe(model_file, weights_file)
                logger.info("DNN Face Detector initialized (high accuracy mode)")
            except:
                logger.warning("DNN models not found, falling back to Haar Cascade")
                self.method = "haar"
                self._init_haar()
        else:
            self._init_haar()
    
    def _init_haar(self):
        """Initialize Haar Cascade detector."""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        logger.info("Haar Cascade Face Detector initialized")
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in a frame.
        
        Args:
            frame: Input frame (BGR format from OpenCV)
            
        Returns:
            List of face detections with bounding boxes
            Format: [{"box": [ymin, xmin, height, width], "confidence": float}]
        """
        if self.method == "dnn":
            return self._detect_dnn(frame)
        else:
            return self._detect_haar(frame)
    
    def _detect_dnn(self, frame: np.ndarray) -> List[Dict]:
        """DNN-based detection."""
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame, 1.0, (300, 300), (104.0, 177.0, 123.0)
        )
        
        self.net.setInput(blob)
        detections = self.net.forward()
        
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.min_confidence:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (xmin, ymin, xmax, ymax) = box.astype("int")
                
                faces.append({
                    "box": [ymin, xmin, ymax - ymin, xmax - xmin],
                    "confidence": float(confidence)
                })
        
        return faces
    
    def _detect_haar(self, frame: np.ndarray) -> List[Dict]:
        """Haar Cascade detection."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        detections = []
        for (x, y, w, h) in faces:
            detections.append({
                "box": [y, x, h, w],
                "confidence": 0.85  # Haar doesn't provide confidence, use fixed value
            })
        
        return detections


class AudioKeywordSpotter:
    """
    Audio transcription and keyword spotting using Faster-Whisper.
    Extracts audio from video and identifies keyword occurrences.
    """
    
    def __init__(self, model_size: str = "tiny"):
        """
        Initialize Faster-Whisper model.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
                       'tiny' and 'base' are recommended for CPU performance
        """
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info(f"Faster-Whisper initialized with {model_size} model")
    
    def extract_and_transcribe(
        self, 
        video_path: str, 
        keywords_list: List[str]
    ) -> tuple[List[Dict], str]:
        """
        Extract audio from video, transcribe it, and spot keywords.
        
        Args:
            video_path: Path to video file
            keywords_list: List of keywords to search for (case-insensitive)
            
        Returns:
            Tuple of (audio_hits, audio_path):
                - audio_hits: List of keyword matches with timestamps
                  Format: [{"timestamp": float, "text": str, "keyword": str}]
                - audio_path: Path to extracted audio file (for cleanup)
        """
        audio_path = None
        audio_hits = []
        
        try:
            # Extract audio from video
            logger.info(f"Extracting audio from video: {video_path}")
            video = VideoFileClip(video_path)
            
            # Check if video has audio
            if video.audio is None:
                logger.warning("Video has no audio track")
                video.close()
                return [], None
            
            # Create temporary audio file
            audio_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            video.audio.write_audiofile(audio_path, logger=None, verbose=False)
            video.close()
            
            logger.info(f"Audio extracted to: {audio_path}")
            
            # Transcribe audio
            logger.info("Transcribing audio with Faster-Whisper...")
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            
            # Convert keywords to lowercase for case-insensitive matching
            keywords_lower = [kw.lower() for kw in keywords_list]
            
            # Process segments and find keyword matches
            for segment in segments:
                text = segment.text.strip()
                text_lower = text.lower()
                
                # Check if any keyword is in this segment
                for keyword in keywords_lower:
                    if keyword in text_lower:
                        audio_hits.append({
                            "timestamp": segment.start,
                            "text": text,
                            "keyword": keyword
                        })
                        logger.info(f"Keyword '{keyword}' found at {segment.start}s: {text}")
            
            logger.info(f"Audio analysis complete. Found {len(audio_hits)} keyword matches.")
            
        except Exception as e:
            logger.error(f"Error during audio extraction/transcription: {e}")
            # Don't raise, return empty results instead
        
        return audio_hits, audio_path


# Initialize detectors (singleton pattern)
face_detector = CVFaceDetector(method="haar", min_confidence=0.75)
audio_spotter = AudioKeywordSpotter(model_size="tiny")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "OSINT Video Analysis Platform",
        "version": "3.0.0",
        "features": [
            "OpenCV Face Detection (Haar Cascade / DNN)",
            "Faster-Whisper Audio Transcription",
            "Keyword Spotting",
            "Real-time Analysis"
        ],
        "endpoints": {
            "/analyze": "POST - Analyze video with face detection and audio keywords",
            "/health": "GET - Health check",
            "/docs": "GET - Interactive API documentation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "osint-video-analysis",
        "version": "3.0.0",
        "models": {
            "face_detection": f"OpenCV ({face_detector.method.upper()}, confidence={face_detector.min_confidence})",
            "audio_transcription": "Faster-Whisper (tiny)"
        }
    }


@app.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...),
    keywords: str = Form(default="")
):
    """
    Analyze video with face detection and audio keyword spotting.
    
    Args:
        file: Video file (MP4, AVI, MOV, MKV, WEBM)
        keywords: Comma-separated list of keywords to search for in audio
        
    Returns:
        JSON with face detections and audio keyword hits
    """
    video_path = None
    audio_path = None
    
    try:
        # Validate file type
        allowed_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded video to temporary file
        video_path = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False).name
        
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Video saved to: {video_path}")
        
        # Parse keywords
        keywords_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        logger.info(f"Keywords to search: {keywords_list}")
        
        # ===== FACE DETECTION =====
        logger.info("Starting face detection...")
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Failed to open video file")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps if fps > 0 else 0
        
        face_detections = []
        frame_skip = 5  # Process every 5th frame for performance
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Only process every 5th frame
            if frame_count % frame_skip == 0:
                timestamp = frame_count / fps
                
                # Detect faces in this frame
                faces = face_detector.detect_faces(frame)
                
                # Add timestamp to each detection
                for face in faces:
                    # Convert numpy types to Python native types for JSON serialization
                    box = [int(x) if isinstance(x, (np.integer, np.int32, np.int64)) else float(x) for x in face["box"]]
                    face_detections.append({
                        "timestamp": round(timestamp, 2),
                        "box": box,
                        "confidence": float(face["confidence"])
                    })
            
            frame_count += 1
        
        cap.release()
        logger.info(f"Face detection complete. Found {len(face_detections)} faces.")
        
        # ===== AUDIO KEYWORD SPOTTING =====
        audio_hits = []
        
        if keywords_list:
            logger.info("Starting audio keyword spotting...")
            try:
                audio_hits, audio_path = audio_spotter.extract_and_transcribe(
                    video_path, 
                    keywords_list
                )
            except Exception as e:
                logger.error(f"Audio analysis failed: {e}")
                # Continue without audio analysis rather than failing entirely
                audio_hits = []
        else:
            logger.info("No keywords provided, skipping audio analysis")
        
        # ===== PREPARE RESPONSE =====
        response = {
            "status": "success",
            "filename": file.filename,
            "video_duration": round(video_duration, 2),
            "frames_analyzed": frame_count // frame_skip,
            "faces": face_detections,
            "audio_hits": audio_hits,
            "detection_config": {
                "face_detector": f"OpenCV {face_detector.method.upper()}",
                "min_confidence": face_detector.min_confidence,
                "frame_skip": frame_skip,
                "audio_model": "Faster-Whisper (tiny)" if keywords_list else "disabled"
            }
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during video analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Cleanup: Delete temporary files
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
                logger.info(f"Deleted temporary video: {video_path}")
            except Exception as e:
                logger.warning(f"Failed to delete video file: {e}")
        
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
                logger.info(f"Deleted temporary audio: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to delete audio file: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
