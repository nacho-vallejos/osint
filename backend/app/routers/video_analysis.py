"""
OSINT Video Facial Detection Module
Processes video files to detect faces frame-by-frame with timestamps
Uses OpenCV Haar Cascade for fast facial detection
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import cv2
import shutil
import tempfile
import os
from typing import List, Dict
from pathlib import Path

router = APIRouter(prefix="/video", tags=["Video Analysis"])


def process_video(video_path: str) -> List[Dict]:
    """
    Process video file to detect faces in frames using Haar Cascade
    
    Args:
        video_path: Path to temporary video file
        
    Returns:
        List of dictionaries containing timestamp and face coordinates
        Format: [{"timestamp": 1.5, "faces": [[top, right, bottom, left], ...]}, ...]
    """
    results = []
    
    try:
        # Load Haar Cascade classifier for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Open video file
        video_capture = cv2.VideoCapture(video_path)
        
        if not video_capture.isOpened():
            raise ValueError("Failed to open video file")
        
        # Get video properties
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        
        # Process every 5th frame for performance optimization
        frame_skip = 5
        
        while True:
            ret, frame = video_capture.read()
            
            if not ret:
                break
            
            # Only process every 5th frame
            if frame_count % frame_skip == 0:
                # Convert to grayscale for Haar Cascade
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                # Returns list of [x, y, w, h]
                faces = face_cascade.detectMultiScale(
                    gray_frame,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # Calculate timestamp in seconds
                timestamp = frame_count / fps
                
                # Store results if faces were detected
                if len(faces) > 0:
                    # Convert from (x, y, w, h) to (top, right, bottom, left) format
                    face_locations = []
                    for (x, y, w, h) in faces:
                        top = y
                        right = x + w
                        bottom = y + h
                        left = x
                        face_locations.append([top, right, bottom, left])
                    
                    results.append({
                        "timestamp": round(timestamp, 2),
                        "faces": face_locations
                    })
            
            frame_count += 1
        
        # Release video capture object
        video_capture.release()
        
    except Exception as e:
        raise Exception(f"Error processing video: {str(e)}")
    
    return results


@router.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """
    OSINT Video Analysis Endpoint
    
    Accepts video file, processes frame-by-frame for facial detection,
    returns JSON report with timestamps and face coordinates.
    
    Security: Deletes temporary file after processing (OPSEC requirement)
    """
    
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create temporary file
    temp_file = None
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        # Process video for facial detection
        analysis_results = process_video(temp_file_path)
        
        # OPSEC: Delete temporary file after processing
        os.unlink(temp_file_path)
        
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "total_detections": len(analysis_results),
            "detection_method": "OpenCV Haar Cascade",
            "results": analysis_results
        })
        
    except Exception as e:
        # Ensure cleanup even on error
        if temp_file and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Video analysis failed: {str(e)}"
        )
    
    finally:
        # Close uploaded file
        await file.close()
