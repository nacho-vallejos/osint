/**
 * OSINT Video Facial Detection Analyzer
 * 
 * Connects to FastAPI backend for:
 * - Face detection using OpenCV (DNN/Haar)
 * - Audio transcription using Faster-Whisper
 * - Keyword spotting in audio
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Upload, Play, AlertCircle, CheckCircle, Loader, FileText, Volume2 } from 'lucide-react';

const OsintVideoAnalyzer = () => {
  // State management
  const [videoFile, setVideoFile] = useState(null);
  const [videoSrcUrl, setVideoSrcUrl] = useState('');
  const [keywords, setKeywords] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [analysisComplete, setAnalysisComplete] = useState(false);

  // Refs for video and canvas elements
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

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
    setAnalysisResults(null);
    setAnalysisComplete(false);

    // Store file and create preview URL
    setVideoFile(file);
    const url = URL.createObjectURL(file);
    setVideoSrcUrl(url);
  };

  /**
   * Start analysis by uploading to backend
   */
  const startAnalysis = async () => {
    if (!videoFile) {
      setError('Please select a video file first');
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('file', videoFile);
      formData.append('keywords', keywords);

      // Upload to backend
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data = await response.json();
      setAnalysisResults(data);
      setAnalysisComplete(true);

    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  /**
   * Draw face bounding boxes on canvas overlay
   */
  const handleTimeUpdate = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || !analysisResults) return;

    const ctx = canvas.getContext('2d');

    // Match canvas dimensions to video
    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get current timestamp
    const currentTime = video.currentTime;

    // Find detections within 0.2 seconds of current time
    const relevantDetections = analysisResults.faces.filter(
      detection => Math.abs(detection.timestamp - currentTime) <= 0.2
    );

    if (relevantDetections.length > 0) {
      relevantDetections.forEach((detection) => {
        const [ymin, xmin, height, width] = detection.box;

        // Style: Cyber/OSINT aesthetic with glowing green
        ctx.strokeStyle = '#00ff41';
        ctx.lineWidth = 4;
        ctx.shadowBlur = 15;
        ctx.shadowColor = '#00ff41';

        // Draw rectangle
        ctx.strokeRect(xmin, ymin, width, height);

        // Add corner accents
        const cornerSize = 20;
        ctx.lineWidth = 6;

        // Top-left corner
        ctx.beginPath();
        ctx.moveTo(xmin, ymin + cornerSize);
        ctx.lineTo(xmin, ymin);
        ctx.lineTo(xmin + cornerSize, ymin);
        ctx.stroke();

        // Top-right corner
        ctx.beginPath();
        ctx.moveTo(xmin + width - cornerSize, ymin);
        ctx.lineTo(xmin + width, ymin);
        ctx.lineTo(xmin + width, ymin + cornerSize);
        ctx.stroke();

        // Bottom-left corner
        ctx.beginPath();
        ctx.moveTo(xmin, ymin + height - cornerSize);
        ctx.lineTo(xmin, ymin + height);
        ctx.lineTo(xmin + cornerSize, ymin + height);
        ctx.stroke();

        // Bottom-right corner
        ctx.beginPath();
        ctx.moveTo(xmin + width - cornerSize, ymin + height);
        ctx.lineTo(xmin + width, ymin + height);
        ctx.lineTo(xmin + width, ymin + height - cornerSize);
        ctx.stroke();

        // Add "TARGET" label
        ctx.font = 'bold 16px monospace';
        ctx.fillStyle = '#00ff41';
        ctx.shadowBlur = 10;
        ctx.fillText(`TARGET ${(detection.confidence * 100).toFixed(0)}%`, xmin, ymin - 10);
      });
    }

    // Highlight audio keywords
    if (analysisResults.audio_hits) {
      const relevantAudioHits = analysisResults.audio_hits.filter(
        hit => Math.abs(hit.timestamp - currentTime) <= 1.0
      );

      if (relevantAudioHits.length > 0) {
        // Draw audio indicator
        ctx.fillStyle = '#ff00ff';
        ctx.shadowBlur = 20;
        ctx.shadowColor = '#ff00ff';
        ctx.font = 'bold 20px monospace';
        
        relevantAudioHits.forEach((hit, index) => {
          ctx.fillText(
            `🎤 "${hit.keyword}" detected`, 
            20, 
            30 + (index * 30)
          );
        });
      }
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
    };
  }, [videoSrcUrl]);

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            OSINT Video Analysis Platform
          </h1>
          <p className="text-slate-400">
            AI-powered facial detection and audio keyword spotting with OpenCV and Faster-Whisper
          </p>
        </div>

        {/* Upload Section */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
          <div className="space-y-4">
            {/* File upload */}
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
              <div className="text-sm text-slate-400">
                <span className="text-blue-400 font-medium">Selected:</span> {videoFile.name}
              </div>
            )}

            {/* Keywords input */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Audio Keywords (comma-separated, optional)
              </label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="e.g. bomb, weapon, suspicious"
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">
                Enter keywords to search for in the audio track. Leave empty to skip audio analysis.
              </p>
            </div>

            {/* Analyze button */}
            {videoFile && !analysisComplete && (
              <button
                onClick={startAnalysis}
                disabled={isAnalyzing}
                className={`flex items-center justify-center px-6 py-3 rounded-lg font-semibold transition-all ${
                  isAnalyzing
                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <Loader className="w-5 h-5 mr-2 animate-spin" />
                    Analyzing...
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

        {/* Status Messages */}
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
              Analysis complete! Found {analysisResults.faces.length} face detections
              {analysisResults.audio_hits.length > 0 && ` and ${analysisResults.audio_hits.length} audio keyword matches`}.
            </div>
          </div>
        )}

        {/* Analysis Results Stats */}
        {analysisResults && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
            <h2 className="text-xl font-bold text-white mb-4">Analysis Results</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-blue-400">{analysisResults.video_duration}s</div>
                <div className="text-sm text-slate-400">Duration</div>
              </div>
              
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-emerald-400">{analysisResults.faces.length}</div>
                <div className="text-sm text-slate-400">Face Detections</div>
              </div>
              
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-purple-400">{analysisResults.frames_analyzed}</div>
                <div className="text-sm text-slate-400">Frames Analyzed</div>
              </div>
              
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <div className="text-2xl font-bold text-pink-400">{analysisResults.audio_hits.length}</div>
                <div className="text-sm text-slate-400">Audio Matches</div>
              </div>
            </div>

            {/* Audio hits list */}
            {analysisResults.audio_hits.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-bold text-white mb-3 flex items-center">
                  <Volume2 className="w-5 h-5 mr-2 text-pink-400" />
                  Audio Keyword Matches
                </h3>
                <div className="space-y-2">
                  {analysisResults.audio_hits.map((hit, index) => (
                    <div key={index} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="text-pink-400 font-mono text-sm">{hit.timestamp.toFixed(1)}s</span>
                          <span className="text-slate-500 mx-2">•</span>
                          <span className="text-emerald-400 font-semibold">"{hit.keyword}"</span>
                        </div>
                      </div>
                      <div className="text-sm text-slate-300 mt-1">"{hit.text}"</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Video Player with Canvas Overlay */}
        {videoSrcUrl && analysisComplete && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h2 className="text-xl font-bold text-white mb-4">Video Playback with Detections</h2>
            
            {/* Container with relative positioning */}
            <div className="relative inline-block">
              {/* Video Element */}
              <video
                ref={videoRef}
                src={videoSrcUrl}
                controls
                onTimeUpdate={handleTimeUpdate}
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

            {/* Detection info */}
            <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
              <h3 className="text-sm font-bold text-white mb-2">Detection Information</h3>
              <div className="text-xs text-slate-400 space-y-1">
                <p>• <span className="text-emerald-400">Green boxes</span>: Face detections with confidence scores</p>
                <p>• <span className="text-pink-400">Pink text</span>: Audio keyword matches at current timestamp</p>
                <p>• Method: {analysisResults.detection_config.face_detector}</p>
                <p>• Confidence threshold: {analysisResults.detection_config.min_confidence}</p>
                {analysisResults.detection_config.audio_model !== 'disabled' && (
                  <p>• Audio model: {analysisResults.detection_config.audio_model}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-6 bg-slate-900/50 border border-slate-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-3">Instructions</h3>
          <ol className="space-y-2 text-slate-400 text-sm list-decimal list-inside">
            <li>Click "Select Video File" and choose a video (MP4, AVI, MOV, MKV, WEBM)</li>
            <li>Optionally, enter keywords to search for in the audio (comma-separated)</li>
            <li>Click "Start Analysis" to process the video on the server</li>
            <li>Wait for analysis to complete (this may take a minute for longer videos)</li>
            <li>Play the video to see face detections and audio keyword matches in real-time</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default OsintVideoAnalyzer;
