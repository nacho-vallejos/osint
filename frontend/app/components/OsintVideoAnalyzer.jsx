/**
 * OSINT Video Facial Detection Analyzer
 * Version 3.2.2 - Refactored with improved synchronization logic
 * 
 * Key improvements:
 * - Closest timestamp matching (0.15s threshold) eliminates visual lag
 * - Supports both MediaPipe normalized and OpenCV pixel coordinates
 * - Prominent red warning overlay for audio keyword matches
 * - Canvas dimensions sync with video on every frame
 * - Clean green borders (linewidth 3) for face bounding boxes
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Upload, Play, AlertCircle, CheckCircle, Loader, Volume2, Search } from 'lucide-react';

const OsintVideoAnalyzer = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [videoSrcUrl, setVideoSrcUrl] = useState('');
  const [keywords, setKeywords] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [analysisComplete, setAnalysisComplete] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm'];
    if (!validTypes.includes(file.type)) {
      setError('Unsupported video format. Please use MP4, AVI, MOV, MKV, or WEBM.');
      return;
    }

    setError('');
    setAnalysisResults(null);
    setAnalysisComplete(false);
    setVideoFile(file);
    setVideoSrcUrl(URL.createObjectURL(file));
  };

  const startAnalysis = async () => {
    if (!videoFile) {
      setError('Please select a video file first');
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', videoFile);
      
      if (keywords && keywords.trim()) {
        formData.append('keywords', keywords.trim());
      }

      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data = await response.json();
      console.log('Analysis complete:', data);
      setAnalysisResults(data);
      setAnalysisComplete(true);

    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleTimeUpdate = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || !analysisResults) return;

    const ctx = canvas.getContext('2d');

    // **CRITICAL: Ensure canvas matches video dimensions for proper overlay**
    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    // **STEP 1: Clear canvas for fresh frame**
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const currentTime = video.currentTime;
    const SYNC_THRESHOLD = 0.15; // seconds

    // **STEP 2: Find CLOSEST face detection (eliminates visual lag)**
    // Use .find() pattern with closest timestamp matching
    let closestDetection = null;
    let minTimeDiff = Infinity;

    analysisResults.faces.forEach((detection) => {
      const timeDiff = Math.abs(detection.timestamp - currentTime);
      if (timeDiff < SYNC_THRESHOLD && timeDiff < minTimeDiff) {
        minTimeDiff = timeDiff;
        closestDetection = detection;
      }
    });

    // **STEP 3: Draw face bounding boxes**
    if (closestDetection && closestDetection.faces && closestDetection.faces.length > 0) {
      closestDetection.faces.forEach((face) => {
        let x, y, w, h;

        // Handle both coordinate formats:
        // - MediaPipe: normalized {xmin, ymin, width, height} (0-1 range)
        // - OpenCV: pixel array [ymin, xmin, height, width]
        if (face.box.xmin !== undefined) {
          // MediaPipe normalized coordinates (0-1)
          x = face.box.xmin * canvas.width;
          y = face.box.ymin * canvas.height;
          w = face.box.width * canvas.width;
          h = face.box.height * canvas.height;
        } else {
          // OpenCV pixel coordinates [ymin, xmin, height, width]
          const [ymin, xmin, height, width] = face.box;
          x = xmin;
          y = ymin;
          w = width;
          h = height;
        }

        // **Draw main bounding box - Green border, linewidth 3**
        ctx.strokeStyle = '#00FF00'; // Green as specified
        ctx.lineWidth = 3;
        ctx.shadowBlur = 0; // Clean lines
        ctx.shadowColor = 'transparent';
        ctx.strokeRect(x, y, w, h);

        // Confidence label
        if (face.confidence) {
          ctx.font = 'bold 14px monospace';
          ctx.fillStyle = '#00FF00';
          ctx.shadowBlur = 4;
          ctx.shadowColor = '#000000';
          const confidence = (face.confidence * 100).toFixed(0);
          ctx.fillText(`${confidence}%`, x + 5, y - 5);
        }
      });
    }

    // **STEP 4: Audio Alerts - Prominent red warning overlay**
    if (analysisResults.audio_alerts && analysisResults.audio_alerts.length > 0) {
      // Check if currentTime falls between start and end of any alert
      const activeAlerts = analysisResults.audio_alerts.filter(
        alert => currentTime >= alert.start && currentTime <= alert.end
      );

      if (activeAlerts.length > 0) {
        // **Display prominent RED warning overlay**
        const overlayHeight = 80;
        ctx.fillStyle = 'rgba(220, 38, 38, 0.95)'; // Prominent red
        ctx.shadowBlur = 0;
        ctx.fillRect(0, 0, canvas.width, overlayHeight);
        
        // Warning text with keyword
        ctx.font = 'bold 28px monospace';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 6;
        
        const alertText = `⚠️ MATCH: ${activeAlerts[0].keyword.toUpperCase()}`;
        ctx.fillText(alertText, canvas.width / 2, 40);
        
        // Additional context text
        ctx.font = '14px monospace';
        ctx.fillText(
          `"${activeAlerts[0].text.substring(0, 50)}${activeAlerts[0].text.length > 50 ? '...' : ''}"`,
          canvas.width / 2,
          65
        );
        
        // Reset text alignment
        ctx.textAlign = 'left';
      }
    }
  };

  useEffect(() => {
    return () => {
      if (videoSrcUrl) {
        URL.revokeObjectURL(videoSrcUrl);
      }
    };
  }, [videoSrcUrl]);

  // Calculate total face detections
  const totalFaceDetections = analysisResults?.faces.reduce((sum, frame) => sum + frame.faces.length, 0) || 0;

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            OSINT Video Analysis Platform v3.2.2
          </h1>
          <p className="text-slate-400">
            Lag-free face tracking with closest timestamp matching and prominent audio alerts
          </p>
        </div>

        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
          <div className="space-y-4">
            <div>
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

            {videoFile && (
              <div className="text-sm text-slate-400 bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-blue-400 font-medium">Selected:</span> {videoFile.name}
                <div className="text-xs text-slate-500 mt-1">
                  Size: {(videoFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center">
                <Search className="w-4 h-4 mr-2" />
                Audio Keywords (comma-separated, optional)
              </label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="e.g. amor, mujer, Borges"
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50"
              />
              <p className="text-xs text-slate-500 mt-1">
                Keywords are searched in Spanish audio transcription. Leave empty to skip audio analysis.
              </p>
            </div>

            {videoFile && !analysisComplete && (
              <button
                onClick={startAnalysis}
                disabled={isAnalyzing}
                className={`w-full flex items-center justify-center px-6 py-3 rounded-lg font-semibold transition-all ${
                  isAnalyzing
                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <Loader className="w-5 h-5 mr-2 animate-spin" />
                    Analyzing video... Please wait
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    Start Analysis
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {error && (
          <div className="bg-red-950/50 border border-red-800 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-red-300">{error}</div>
          </div>
        )}

        {analysisComplete && (
          <div className="bg-emerald-950/50 border border-emerald-800 rounded-lg p-4 mb-6 flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div className="text-emerald-300">
              Analysis complete! Found {totalFaceDetections} face detections
              {analysisResults.audio_alerts.length > 0 && ` and ${analysisResults.audio_alerts.length} audio keyword matches`}.
            </div>
          </div>
        )}

        {analysisResults && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
            <h2 className="text-xl font-bold text-white mb-4">Analysis Results</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-blue-400">{analysisResults.video_duration}s</div>
                <div className="text-sm text-slate-400">Duration</div>
              </div>
              
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-emerald-400">{totalFaceDetections}</div>
                <div className="text-sm text-slate-400">Face Detections</div>
              </div>
              
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-purple-400">{analysisResults.frames_analyzed}</div>
                <div className="text-sm text-slate-400">Frames Analyzed</div>
              </div>
              
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-pink-400">{analysisResults.audio_alerts.length}</div>
                <div className="text-sm text-slate-400">Keyword Matches</div>
              </div>
            </div>

            {analysisResults.detection_config.keywords_searched && analysisResults.detection_config.keywords_searched.length > 0 && (
              <div className="mb-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="text-sm font-bold text-white mb-2 flex items-center">
                  <Search className="w-4 h-4 mr-2" />
                  Keywords Searched
                </h3>
                <div className="flex flex-wrap gap-2">
                  {analysisResults.detection_config.keywords_searched.map((kw, idx) => (
                    <span key={idx} className="px-3 py-1 bg-blue-900/50 text-blue-300 rounded-full text-sm border border-blue-700">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {analysisResults.audio_alerts.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-bold text-white mb-3 flex items-center">
                  <Volume2 className="w-5 h-5 mr-2 text-pink-400" />
                  Audio Keyword Matches ({analysisResults.audio_alerts.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {analysisResults.audio_alerts.map((alert, index) => (
                    <div key={index} className="bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-pink-500 transition-colors">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="text-pink-400 font-mono text-sm font-bold">{alert.start.toFixed(1)}s - {alert.end.toFixed(1)}s</span>
                          <span className="text-slate-500 mx-2">•</span>
                          <span className="text-emerald-400 font-semibold">"{alert.keyword}"</span>
                        </div>
                      </div>
                      <div className="text-sm text-slate-300 mt-1 italic">"{alert.text}"</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {videoSrcUrl && analysisComplete && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-xl font-bold text-white mb-4">Video Playback with Real-time Overlay</h2>
            
            <div className="relative inline-block">
              <video
                ref={videoRef}
                src={videoSrcUrl}
                controls
                onTimeUpdate={handleTimeUpdate}
                className="max-w-full rounded-lg"
                style={{ display: 'block' }}
              />

              <canvas
                ref={canvasRef}
                className="absolute top-0 left-0 rounded-lg"
                style={{ pointerEvents: 'none' }}
              />
            </div>

            <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-bold text-white mb-2">Detection Information</h3>
              <div className="text-xs text-slate-400 space-y-1">
                <p>• <span className="text-emerald-400">Green boxes (linewidth 3)</span>: Face detections using closest timestamp (±0.15s threshold)</p>
                <p>• <span className="text-red-400">Red warning overlay</span>: Active when currentTime is between alert start/end times</p>
                <p>• Method: {analysisResults.detection_config.face_detector}</p>
                <p>• Confidence threshold: {analysisResults.detection_config.min_confidence}</p>
                <p>• Frame skip: Every {analysisResults.detection_config.frame_skip} frames</p>
                <p>• FPS: {analysisResults.fps}</p>
                <p>• Sync: Canvas dimensions match video dimensions on every frame</p>
                {analysisResults.detection_config.audio_model !== 'disabled' && (
                  <p>• Audio: {analysisResults.detection_config.audio_model}</p>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 bg-slate-900/50 border border-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-3">What's New in v3.2.2</h3>
          <ul className="space-y-2 text-slate-400 text-sm list-disc list-inside">
            <li><span className="text-emerald-400 font-semibold">Zero visual lag</span> - Closest timestamp matching (0.15s threshold) for perfectly smooth tracking</li>
            <li><span className="text-red-400 font-semibold">Prominent audio alerts</span> - Red warning overlay with "⚠️ MATCH: [keyword]" during detection</li>
            <li><span className="text-blue-400 font-semibold">Dual coordinate support</span> - Handles both MediaPipe normalized and OpenCV pixel coordinates</li>
            <li>Canvas dimensions automatically sync with video dimensions on every frame</li>
            <li>Clean green borders (linewidth 3) for face bounding boxes as specified</li>
            <li>Audio alerts check if currentTime falls between start/end times</li>
            <li>Enhanced OpenCV face detection (Frontal + Profile Haar Cascades)</li>
            <li>Faster-Whisper base model with VAD filtering for Spanish/English</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default OsintVideoAnalyzer;
