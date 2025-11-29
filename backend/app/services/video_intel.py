"""
Video Intelligence Service - Advanced Media Analysis for OSINT
Combines computer vision (face detection), speech-to-text, and NLP
Compatible with Celery for async processing of heavy workloads
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import tempfile
import hashlib
from collections import Counter

import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import whisper

# Face recognition (requires dlib and face_recognition_models)
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logging.warning("face_recognition not available - facial analysis disabled")


logger = logging.getLogger(__name__)


@dataclass
class FaceDetection:
    """Represents a detected face in a video frame"""
    frame_number: int
    timestamp: float  # Seconds
    bbox: Tuple[int, int, int, int]  # (top, right, bottom, left)
    encoding: Optional[np.ndarray] = None  # 128d face encoding vector
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_number": self.frame_number,
            "timestamp": round(self.timestamp, 2),
            "bbox": {
                "top": self.bbox[0],
                "right": self.bbox[1],
                "bottom": self.bbox[2],
                "left": self.bbox[3]
            },
            "has_encoding": self.encoding is not None,
            "confidence": round(self.confidence, 3)
        }


@dataclass
class AudioTranscript:
    """Represents transcribed audio from video"""
    text: str
    language: str
    segments: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    duration: float = 0.0
    word_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "segments_count": len(self.segments),
            "confidence": round(self.confidence, 3),
            "duration": round(self.duration, 2),
            "word_count": self.word_count
        }


@dataclass
class VideoAnalysisResult:
    """Complete video intelligence analysis result"""
    video_path: str
    checksum: str
    duration: float
    fps: float
    frame_count: int
    resolution: Tuple[int, int]
    
    # Vision analysis
    faces_detected: List[FaceDetection]
    unique_face_count: int
    target_face_matches: List[FaceDetection]
    
    # Audio analysis
    transcript: Optional[AudioTranscript]
    top_keywords: List[Tuple[str, int]]
    
    # Metadata
    analysis_timestamp: str
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "video": {
                "path": self.video_path,
                "checksum": self.checksum,
                "duration": round(self.duration, 2),
                "fps": round(self.fps, 2),
                "frame_count": self.frame_count,
                "resolution": f"{self.resolution[0]}x{self.resolution[1]}"
            },
            "vision_analysis": {
                "total_faces_detected": len(self.faces_detected),
                "unique_faces": self.unique_face_count,
                "target_matches": len(self.target_face_matches),
                "faces": [f.to_dict() for f in self.faces_detected]
            },
            "audio_analysis": {
                "transcript": self.transcript.to_dict() if self.transcript else None,
                "top_keywords": [{"term": k, "frequency": f} for k, f in self.top_keywords]
            },
            "metadata": {
                "analyzed_at": self.analysis_timestamp,
                "errors": self.errors
            }
        }


class VideoIntelCollector:
    """
    Advanced Video Intelligence Collector
    Extracts faces, transcribes audio, and performs keyword analysis
    Designed for Celery async processing
    """
    
    # Common English stopwords for keyword filtering
    STOPWORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
        "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
        'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
        'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
        'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
        'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
        'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
        'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm',
        'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
        "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven',
        "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't",
        'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't",
        'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't", 'yeah', 'um', 'uh',
        'like', 'know', 'think', 'going', 'really', 'well', 'right', 'oh', 'got'
    }
    
    def __init__(
        self,
        frame_sample_rate: int = 30,  # Extract frame every N frames
        whisper_model: str = "base",  # tiny, base, small, medium, large
        face_detection_model: str = "hog",  # hog or cnn
        face_match_threshold: float = 0.6  # Lower = stricter
    ):
        """
        Initialize VideoIntelCollector
        
        Args:
            frame_sample_rate: Extract 1 frame every N frames (30 = 1fps at 30fps video)
            whisper_model: Whisper model size (tiny/base/small/medium/large)
            face_detection_model: 'hog' (faster, CPU) or 'cnn' (accurate, GPU)
            face_match_threshold: Face similarity threshold (0.6 = default)
        """
        self.frame_sample_rate = frame_sample_rate
        self.whisper_model_name = whisper_model
        self.face_detection_model = face_detection_model
        self.face_match_threshold = face_match_threshold
        
        self.whisper_model: Optional[Any] = None
        self._load_whisper_model()
    
    def _load_whisper_model(self):
        """Lazy load Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.whisper_model_name}")
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None
    
    def _calculate_checksum(self, filepath: str) -> str:
        """Calculate SHA256 checksum of video file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_faces_from_video(
        self,
        video_path: str,
        target_face_encoding: Optional[np.ndarray] = None
    ) -> Tuple[List[FaceDetection], int, List[FaceDetection]]:
        """
        Extract faces from video frames
        
        Args:
            video_path: Path to video file
            target_face_encoding: Optional face encoding to match against
            
        Returns:
            Tuple of (all_faces, unique_face_count, target_matches)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            logger.warning("Face recognition not available")
            return [], 0, []
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Processing video: {total_frames} frames at {fps} fps")
        
        all_faces: List[FaceDetection] = []
        known_encodings: List[np.ndarray] = []
        target_matches: List[FaceDetection] = []
        
        frame_number = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample frames at specified rate
                if frame_number % self.frame_sample_rate != 0:
                    frame_number += 1
                    continue
                
                timestamp = frame_number / fps
                
                # Convert BGR (OpenCV) to RGB (face_recognition)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(
                    rgb_frame,
                    model=self.face_detection_model
                )
                
                if face_locations:
                    # Generate encodings for detected faces
                    face_encodings = face_recognition.face_encodings(
                        rgb_frame,
                        face_locations
                    )
                    
                    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                        detection = FaceDetection(
                            frame_number=frame_number,
                            timestamp=timestamp,
                            bbox=(top, right, bottom, left),
                            encoding=encoding,
                            confidence=0.9  # face_recognition doesn't provide confidence
                        )
                        
                        all_faces.append(detection)
                        
                        # Check if this is a new unique face
                        if not known_encodings:
                            known_encodings.append(encoding)
                        else:
                            matches = face_recognition.compare_faces(
                                known_encodings,
                                encoding,
                                tolerance=self.face_match_threshold
                            )
                            if not any(matches):
                                known_encodings.append(encoding)
                        
                        # Check if this matches target face
                        if target_face_encoding is not None:
                            match = face_recognition.compare_faces(
                                [target_face_encoding],
                                encoding,
                                tolerance=self.face_match_threshold
                            )[0]
                            
                            if match:
                                # Calculate similarity (face distance)
                                distance = face_recognition.face_distance(
                                    [target_face_encoding],
                                    encoding
                                )[0]
                                detection.confidence = 1.0 - distance
                                target_matches.append(detection)
                
                frame_number += 1
                
                # Log progress every 100 frames
                if frame_number % 100 == 0:
                    logger.info(f"Processed {frame_number}/{total_frames} frames")
        
        finally:
            cap.release()
        
        unique_count = len(known_encodings)
        
        logger.info(
            f"Face detection complete: {len(all_faces)} faces detected, "
            f"{unique_count} unique faces"
        )
        
        return all_faces, unique_count, target_matches
    
    def _extract_audio_and_transcribe(
        self,
        video_path: str
    ) -> Optional[AudioTranscript]:
        """
        Extract audio from video and transcribe using Whisper
        
        Args:
            video_path: Path to video file
            
        Returns:
            AudioTranscript or None if extraction fails
        """
        if self.whisper_model is None:
            logger.error("Whisper model not loaded")
            return None
        
        temp_audio_path = None
        
        try:
            # Extract audio using moviepy
            logger.info("Extracting audio from video...")
            video_clip = VideoFileClip(video_path)
            
            if video_clip.audio is None:
                logger.warning("Video has no audio track")
                return None
            
            # Save audio to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
                video_clip.audio.write_audiofile(
                    temp_audio_path,
                    codec='pcm_s16le',
                    fps=16000,
                    nbytes=2,
                    logger=None  # Suppress moviepy logs
                )
            
            video_clip.close()
            
            # Transcribe with Whisper
            logger.info("Transcribing audio with Whisper...")
            result = self.whisper_model.transcribe(
                temp_audio_path,
                fp16=False,  # Use FP32 for CPU compatibility
                verbose=False
            )
            
            # Calculate average confidence from segments
            avg_confidence = 0.0
            if result.get("segments"):
                confidences = [
                    seg.get("no_speech_prob", 0.0)
                    for seg in result["segments"]
                ]
                avg_confidence = 1.0 - (sum(confidences) / len(confidences))
            
            transcript = AudioTranscript(
                text=result["text"].strip(),
                language=result.get("language", "unknown"),
                segments=result.get("segments", []),
                confidence=avg_confidence,
                duration=video_clip.duration,
                word_count=len(result["text"].split())
            )
            
            logger.info(
                f"Transcription complete: {transcript.word_count} words, "
                f"language: {transcript.language}"
            )
            
            return transcript
        
        except Exception as e:
            logger.error(f"Audio extraction/transcription failed: {e}")
            return None
        
        finally:
            # Cleanup temporary audio file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception as e:
                    logger.warning(f"Could not delete temp audio file: {e}")
    
    def _extract_keywords(
        self,
        text: str,
        top_n: int = 20,
        min_word_length: int = 4
    ) -> List[Tuple[str, int]]:
        """
        Extract top keywords from text using frequency analysis
        
        Args:
            text: Input text
            top_n: Number of top keywords to return
            min_word_length: Minimum word length to consider
            
        Returns:
            List of (keyword, frequency) tuples
        """
        if not text:
            return []
        
        # Tokenize and clean
        words = text.lower().split()
        
        # Filter words
        filtered_words = [
            word.strip('.,!?;:"()[]{}')
            for word in words
            if (
                len(word) >= min_word_length
                and word.lower() not in self.STOPWORDS
                and word.isalnum()
            )
        ]
        
        # Count frequencies
        word_counts = Counter(filtered_words)
        
        # Get top N
        top_keywords = word_counts.most_common(top_n)
        
        logger.info(f"Extracted {len(top_keywords)} keywords from {len(words)} words")
        
        return top_keywords
    
    async def analyze_video(
        self,
        video_path: str,
        target_face_encoding: Optional[np.ndarray] = None,
        extract_keywords: bool = True
    ) -> VideoAnalysisResult:
        """
        Complete video intelligence analysis
        
        Args:
            video_path: Path to video file
            target_face_encoding: Optional face encoding to match
            extract_keywords: Whether to perform keyword extraction
            
        Returns:
            VideoAnalysisResult with complete analysis
        """
        from datetime import datetime
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        logger.info(f"Starting video analysis: {video_path}")
        
        errors = []
        
        # Get video metadata
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        
        checksum = self._calculate_checksum(video_path)
        
        # Vision analysis
        faces = []
        unique_faces = 0
        target_matches = []
        
        try:
            faces, unique_faces, target_matches = self._extract_faces_from_video(
                video_path,
                target_face_encoding
            )
        except Exception as e:
            error_msg = f"Face detection failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Audio analysis
        transcript = None
        keywords = []
        
        try:
            transcript = self._extract_audio_and_transcribe(video_path)
            
            if transcript and extract_keywords:
                keywords = self._extract_keywords(transcript.text)
        
        except Exception as e:
            error_msg = f"Audio analysis failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        result = VideoAnalysisResult(
            video_path=video_path,
            checksum=checksum,
            duration=duration,
            fps=fps,
            frame_count=frame_count,
            resolution=(width, height),
            faces_detected=faces,
            unique_face_count=unique_faces,
            target_face_matches=target_matches,
            transcript=transcript,
            top_keywords=keywords,
            analysis_timestamp=datetime.utcnow().isoformat(),
            errors=errors
        )
        
        logger.info("Video analysis complete")
        
        return result


# Celery task wrapper example
def create_celery_task(celery_app):
    """
    Create Celery task for async video processing
    
    Usage:
        from celery import Celery
        app = Celery('osint', broker='redis://localhost:6379/0')
        analyze_video_task = create_celery_task(app)
    """
    
    @celery_app.task(bind=True, name='video_intel.analyze')
    def analyze_video_task(self, video_path: str, **kwargs):
        """
        Celery task for video analysis
        
        Args:
            video_path: Path to video file
            **kwargs: Additional arguments for VideoIntelCollector
        """
        import asyncio
        
        collector = VideoIntelCollector(
            frame_sample_rate=kwargs.get('frame_sample_rate', 30),
            whisper_model=kwargs.get('whisper_model', 'base'),
            face_detection_model=kwargs.get('face_detection_model', 'hog')
        )
        
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Analyzing video...'})
        
        # Run analysis
        result = asyncio.run(collector.analyze_video(video_path))
        
        return result.to_dict()
    
    return analyze_video_task
