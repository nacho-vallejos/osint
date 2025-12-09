/**
 * OSINT Video Facial Detection Analyzer
 * Version 3.1.0 - Enhanced tracking and keyword detection
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Upload, Play, AlertCircle, CheckCircle, Loader, FileText, Volume2, Search } from 'lucide-react';

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
      
      // Only append keywords if provided
      if (keywords && keywords.trim()) {
        formData.append('keywords', keywords.trim());
        console.log('Sending keywords:', keywords.trim());
      } else {
        console.log('No keywords provided, skipping audio analysis');
      }

      console.log('Uploading to backend...');

      // Upload to backend
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

    // Find detections within 0.15 seconds of current time (tighter sync)
    const relevantDetections = analysisResults.faces.filter(
      detection => Math.abs(detection.timestamp - currentTime) <= 0.15
    );

    if (relevantDetections.length > 0) {
      relevantDetections.forEach((detection) => {
        const [ymin, xmin, height, width] = detection.box;

        // Color based on detection type
        const color = detection.type === 'profile' ? '#00d4ff' : '#00ff41';
        
        // Style: Cyber/OSINT aesthetic with glowing effect
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.shadowBlur = 12;
        ctx.shadowColor = color;

        // Draw rectangle
        ctx.strokeRect(xmin, ymin, width, height);

        // Add corner accents
        const cornerSize = 15;
        ctx.lineWidth = 5;

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

        // Add label
        ctx.font = 'bold 14px monospace';
        ctx.fillStyle = color;
        ctx.shadowBlur = 8;
        
        const label = detection.type === 'profile' ? 'PROFILE' : 'TARGET';
        const confidence = (detection.confidence * 100).toFixed(0);
        ctx.fillText(`${label} ${confidence}%`, xmin, ymin - 8);
      });
    }

    // Highlight audio keywords
    if (analysisResults.audio_hits && analysisResults.audio_hits.length > 0) {
      const relevantAudioHits = analysisResults.audio_hits.filter(
        hit => Math.abs(hit.timestamp - currentTime) <= 2.0
      );

      if (relevantAudioHits.length > 0) {
        // Draw audio indicator banner
        ctx.fillStyle = 'rgba(255, 0, 255, 0.8)';
        ctx.shadowBlur = 20;
        ctx.shadowColor = '#ff00ff';
        ctx.fillRect(10, 10, canvas.width - 20, 60 * relevantAudioHits.length);
        
        ctx.font = 'bold 18px monospace';
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 5;
        
        relevantAudioHits.forEach((hit, index) => {
          ctx.fillText(
            `🎤 KEYWORD: "${hit.keyword}"`, 
            20, 
            35 + (index * 60)
          );
          ctx.font = '14px monospace';
          ctx.fillText(
            `"${hit.text.substring(0, 50)}${hit.text.length > 50 ? '...' : ''}"`,
            20,
            55 + (index * 60)
          );
          ctx.font = 'bold 18px monospace';
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
            OSINT Video Analysis Platform v3.1
          </h1>
          <p className="text-slate-400">
            Enhanced face tracking (frontal + profile) and audio keyword detection with Spanish language support
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
              <div className="text-sm text-slate-400 bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-blue-400 font-medium">Selected:</span> {videoFile.name}
                <div className="text-xs text-slate-500 mt-1">
                  Size: {(videoFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            )}

            {/* Keywords input */}
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
                Enter keywords in Spanish or English. The system will search for these words in the audio transcription.
                Leave empty to skip audio analysis.
              </p>
            </div>

            {/* Analyze button */}
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
                    Analyzing video... This may take a minute
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
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
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
                <div className="text-sm text-slate-400">Keyword Matches</div>
              </div>
            </div>

            {/* Keywords searched */}
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

            {/* Audio hits list */}
            {analysisResults.audio_hits.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-bold text-white mb-3 flex items-center">
                  <Volume2 className="w-5 h-5 mr-2 text-pink-400" />
                  Audio Keyword Matches ({analysisResults.audio_hits.length})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {analysisResults.audio_hits.map((hit, index) => (
                    <div key={index} className="bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-pink-500 transition-colors">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="text-pink-400 font-mono text-sm font-bold">{hit.timestamp.toFixed(1)}s</span>
                          <span className="text-slate-500 mx-2">•</span>
                          <span className="text-emerald-400 font-semibold">"{hit.keyword}"</span>
                        </div>
                      </div>
                      <div className="text-sm text-slate-300 mt-1 italic">"{hit.text}"</div>
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
                <p>• <span className="text-emerald-400">Green boxes</span>: Frontal face detections</p>
                <p>• <span className="text-cyan-400">Cyan boxes</span>: Profile face detections</p>
                <p>• <span className="text-pink-400">Pink banners</span>: Audio keyword matches</p>
                <p>• Method: {analysisResults.detection_config.face_detector}</p>
                <p>• Frame skip: Every {analysisResults.detection_config.frame_skip} frames</p>
                {analysisResults.detection_config.audio_model !== 'disabled' && (
                  <p>• Audio: {analysisResults.detection_config.audio_model}</p>
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
            <li>Enter keywords in Spanish or English to search in the audio (e.g., "amor, mujer, hombre")</li>
            <li>Click "Start Analysis" - processing may take 30-60 seconds for longer videos</li>
            <li>Review the statistics and keyword matches found</li>
            <li>Play the video to see real-time face tracking and keyword highlights</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default OsintVideoAnalyzer;
