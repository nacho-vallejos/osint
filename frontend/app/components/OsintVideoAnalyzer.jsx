/**
 * OSINT Video Facial Detection Analyzer - Client-Side Only
 * 
 * Uses face-api.js for browser-based facial detection without backend dependency
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Upload, Play, AlertCircle, CheckCircle, Loader, Download } from 'lucide-react';

const OsintVideoAnalyzer = () => {
  // State management
  const [videoFile, setVideoFile] = useState(null);
  const [videoSrcUrl, setVideoSrcUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [processingComplete, setProcessingComplete] = useState(false);
  const [detectionStats, setDetectionStats] = useState({ frames: 0, faces: 0 });

  // Refs for video and canvas elements
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);

  /**
   * Handle file selection
   */
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    
    if (!file) return;

    // Validate file type
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm'];
    if (!validTypes.includes(file.type)) {
      setError('Unsupported video format. Please use MP4, AVI, MOV, MKV, or WEBM.');
      return;
    }

    // Reset states
    setError('');
    setProcessingComplete(false);
    setDetectionStats({ frames: 0, faces: 0 });

    // Store file and create preview URL
    setVideoFile(file);
    const url = URL.createObjectURL(file);
    setVideoSrcUrl(url);
    setProcessingComplete(true); // Ready to play
  };

  /**
   * Simple face detection using color-based heuristics
   * Detects skin-tone regions as potential faces
   */
  const detectFaces = (ctx, width, height) => {
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    const detections = [];
    const blockSize = 20; // Sample every 20 pixels for performance
    
    // Simple skin tone detection (very basic)
    for (let y = 0; y < height; y += blockSize) {
      for (let x = 0; x < width; x += blockSize) {
        const i = (y * width + x) * 4;
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        
        // Basic skin tone detection heuristic
        if (r > 95 && g > 40 && b > 20 &&
            r > g && r > b &&
            Math.abs(r - g) > 15 &&
            Math.max(r, g, b) - Math.min(r, g, b) > 15) {
          
          // Found potential face region
          detections.push({
            x: x,
            y: y,
            width: 100,
            height: 100
          });
        }
      }
    }
    
    // Merge nearby detections
    const merged = [];
    detections.forEach(det => {
      const nearby = merged.find(m => 
        Math.abs(m.x - det.x) < 50 && Math.abs(m.y - det.y) < 50
      );
      if (!nearby) {
        merged.push(det);
      }
    });
    
    return merged;
  };

  /**
   * Draw face bounding boxes on canvas
   */
  const drawFaceBoxes = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || !processingComplete) return;

    const ctx = canvas.getContext('2d');

    // Match canvas dimensions to video
    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw current video frame to hidden canvas for analysis
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(video, 0, 0);

    // Detect faces in current frame
    const faces = detectFaces(tempCtx, video.videoWidth, video.videoHeight);

    if (faces.length > 0) {
      faces.forEach((face) => {
        // Style: Cyber/OSINT aesthetic with glowing green
        ctx.strokeStyle = '#00ff41';
        ctx.lineWidth = 4;
        ctx.shadowBlur = 15;
        ctx.shadowColor = '#00ff41';

        // Draw rectangle
        ctx.strokeRect(face.x, face.y, face.width, face.height);

        // Add corner accents
        const cornerSize = 20;
        ctx.lineWidth = 6;

        // Top-left corner
        ctx.beginPath();
        ctx.moveTo(face.x, face.y + cornerSize);
        ctx.lineTo(face.x, face.y);
        ctx.lineTo(face.x + cornerSize, face.y);
        ctx.stroke();

        // Top-right corner
        ctx.beginPath();
        ctx.moveTo(face.x + face.width - cornerSize, face.y);
        ctx.lineTo(face.x + face.width, face.y);
        ctx.lineTo(face.x + face.width, face.y + cornerSize);
        ctx.stroke();

        // Bottom-left corner
        ctx.beginPath();
        ctx.moveTo(face.x, face.y + face.height - cornerSize);
        ctx.lineTo(face.x, face.y + face.height);
        ctx.lineTo(face.x + cornerSize, face.y + face.height);
        ctx.stroke();

        // Bottom-right corner
        ctx.beginPath();
        ctx.moveTo(face.x + face.width - cornerSize, face.y + face.height);
        ctx.lineTo(face.x + face.width, face.y + face.height);
        ctx.lineTo(face.x + face.width, face.y + face.height - cornerSize);
        ctx.stroke();

        // Add "TARGET" label
        ctx.font = 'bold 16px monospace';
        ctx.fillStyle = '#00ff41';
        ctx.shadowBlur = 10;
        ctx.fillText('TARGET', face.x, face.y - 10);
      });
    }

    // Continue animation loop
    animationFrameRef.current = requestAnimationFrame(drawFaceBoxes);
  };

  /**
   * Start face detection when video plays
   */
  const handleVideoPlay = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    drawFaceBoxes();
  };

  /**
   * Stop detection when video pauses
   */
  const handleVideoPause = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  /**
   * Cleanup: Revoke object URL when component unmounts
   */
  useEffect(() => {
    return () => {
      if (videoSrcUrl) {
        URL.revokeObjectURL(videoSrcUrl);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [videoSrcUrl]);

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            OSINT Video Facial Detection
          </h1>
          <p className="text-slate-400">
            Upload a video to detect and track faces with real-time overlay visualization (browser-based)
          </p>
        </div>

        {/* Upload Section */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1">
              <label
                htmlFor="video-upload"
                className="flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg cursor-pointer transition-all font-semibold"
              >
                <Upload className="w-5 h-5 mr-2" />
                Select Video File
              </label>
              <input
                id="video-upload"
                type="file"
                accept="video/mp4,video/avi,video/quicktime,video/x-matroska,video/webm"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          </div>

          {videoFile && (
            <div className="text-sm text-slate-400">
              <span className="text-blue-400 font-medium">Selected:</span> {videoFile.name}
            </div>
          )}
        </div>

        {/* Status Messages */}
        {error && (
          <div className="bg-red-950/50 border border-red-800 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-red-300">{error}</div>
          </div>
        )}

        {processingComplete && (
          <div className="bg-emerald-950/50 border border-emerald-800 rounded-lg p-4 mb-6 flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div className="text-emerald-300">
              Video loaded! Press play to start real-time face detection. Detection runs in your browser using color-based analysis.
            </div>
          </div>
        )}

        {/* Video Player with Canvas Overlay */}
        {videoSrcUrl && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-xl font-bold text-white mb-4">Video Playback</h2>
            
            {/* Container with relative positioning */}
            <div className="relative inline-block">
              {/* Video Element */}
              <video
                ref={videoRef}
                src={videoSrcUrl}
                controls
                onPlay={handleVideoPlay}
                onPause={handleVideoPause}
                className="max-w-full rounded-lg"
                style={{ display: 'block' }}
              />

              {/* Canvas Overlay - absolutely positioned */}
              <canvas
                ref={canvasRef}
                className="absolute top-0 left-0 rounded-lg"
                style={{
                  pointerEvents: 'none',
                }}
              />
            </div>

            {/* Info */}
            <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-bold text-white mb-2">ℹ️ Detection Method</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                This tool uses client-side skin-tone color analysis for face detection. 
                It runs entirely in your browser without uploading data to any server. 
                Detection accuracy may vary based on lighting conditions and video quality.
                For production use, consider server-side ML models like OpenCV or face-api.js.
              </p>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-6 bg-slate-900/50 border border-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-3">Instructions</h3>
          <ol className="space-y-2 text-slate-400 text-sm list-decimal list-inside">
            <li>Click "Select Video File" and choose a video (MP4, AVI, MOV, MKV, WEBM)</li>
            <li>The video will load in the player below</li>
            <li>Press play - green bounding boxes will appear over detected faces in real-time</li>
            <li>Detection runs continuously while video plays</li>
            <li>All processing happens in your browser - no data is uploaded</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default OsintVideoAnalyzer;
