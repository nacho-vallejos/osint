# 🔺 Identity Triangulation & Media Intelligence System

## Overview

Advanced OSINT system that combines **social media reconnaissance**, **video intelligence**, and **graph analysis** to create comprehensive digital profiles and detect patterns across multiple data sources.

---

## 🎯 Core Capabilities

### 1. **Social Media Reconnaissance** (`services/social_recon.py`)

Sherlock-inspired username discovery across 12+ platforms with intelligent verification.

**Features:**
- ✅ Async parallel checking (blazing fast)
- ✅ Multiple detection strategies (status codes, redirects, content analysis)
- ✅ Confidence scoring (0.0 - 1.0)
- ✅ Rate limit handling
- ✅ Customizable timeouts per platform

**Supported Platforms:**
- GitHub, Twitter, Instagram, Reddit, Twitch
- LinkedIn, Facebook, TikTok, YouTube
- Medium, DevTo, HackerNews, StackOverflow

**Example Usage:**
```python
from app.services.social_recon import SocialProfiler

profiler = SocialProfiler(timeout=10)
results = await profiler.search_username("johndoe")

found_profiles = [p for p in results if p.status.value == "found"]
for profile in found_profiles:
    print(f"{profile.platform}: {profile.url} (confidence: {profile.confidence})")
```

---

### 2. **Video Intelligence** (`services/video_intel.py`)

Multi-modal video analysis combining computer vision and NLP.

**Vision Capabilities:**
- 🎥 Face detection in video frames
- 👤 128-dimensional face encoding (biometric vectors)
- 🔍 Target face matching (person identification)
- 📊 Unique face counting across video

**Audio & NLP Capabilities:**
- 🎤 Audio extraction from video
- 📝 Speech-to-Text transcription (OpenAI Whisper)
- 🌍 Multi-language support
- 🔑 Keyword extraction with frequency analysis
- 📈 Topic modeling from transcript

**Tech Stack:**
- `opencv-python` - Video frame processing
- `face_recognition` - Facial biometrics (dlib-based)
- `moviepy` - Audio extraction
- `openai-whisper` - State-of-the-art speech recognition

**Example Usage:**
```python
from app.services.video_intel import VideoIntelCollector

collector = VideoIntelCollector(
    frame_sample_rate=30,
    whisper_model_size="base"
)

# Analyze video
result = await collector.analyze_video(
    video_path="interview.mp4",
    analyze_faces=True,
    analyze_audio=True
)

print(f"Faces detected: {result.total_faces_detected}")
print(f"Unique faces: {result.unique_faces_count}")
print(f"Transcript words: {result.transcript.word_count}")
print(f"Top keywords: {result.top_keywords[:5]}")
```

---

### 3. **Graph Database Integration** (`services/neo4j_integration.py`)

Neo4j-powered identity graph for relationship mapping.

**Graph Schema:**

```cypher
# Nodes
(Person)         - Individual being investigated
(SocialProfile)  - Social media account
(Video)          - Analyzed video file
(FaceEncoding)   - Biometric face data
(Transcript)     - Audio transcription
(Keyword)        - Extracted topic

# Relationships
(Person)-[HAS_ACCOUNT]->(SocialProfile)
(Person)-[APPEARS_IN]->(Video)
(Video)-[CONTAINS_FACE]->(FaceEncoding)
(Video)-[HAS_TRANSCRIPT]->(Transcript)
(Transcript)-[MENTIONS]->(Keyword)
```

**Example Queries:**

```python
from app.services.neo4j_integration import IdentityGraphDB

db = IdentityGraphDB(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Create person and link profiles
db.create_person(person_id="john_doe", name="John Doe")
db.link_social_profiles("john_doe", social_profiles)

# Store video analysis
db.store_video_analysis("john_doe", video_result)

# Query digital footprint
footprint = db.get_digital_footprint("john_doe")
```

---

## 🚀 API Endpoints

### Health Check
```bash
GET /api/v1/triangulation/health
```

### Social Profile Discovery
```bash
# Simple GET
GET /api/v1/triangulation/social-profile/{username}

# Advanced POST with options
POST /api/v1/triangulation/social-profile
{
  "username": "johndoe",
  "platforms": ["GitHub", "Twitter", "LinkedIn"],
  "timeout": 10
}
```

**Response:**
```json
{
  "username": "johndoe",
  "profiles_found": 3,
  "profiles": [
    {
      "platform": "GitHub",
      "url": "https://github.com/johndoe",
      "status": "found",
      "confidence": 0.95
    }
  ],
  "execution_time": 2.3
}
```

### Video Analysis (Upload)
```bash
POST /api/v1/triangulation/video-analysis
Content-Type: multipart/form-data

video: [file]
analyze_faces: true
analyze_audio: true
frame_sample_rate: 30
whisper_model: "base"
```

### Video Analysis (Server Path)
```bash
POST /api/v1/triangulation/video-analysis-path
{
  "video_path": "/path/to/video.mp4",
  "analyze_faces": true,
  "analyze_audio": true,
  "frame_sample_rate": 30,
  "whisper_model": "base"
}
```

**Response:**
```json
{
  "video_id": "abc123",
  "duration": 120.5,
  "faces": {
    "total_detected": 45,
    "unique_count": 3,
    "target_match": true
  },
  "audio": {
    "transcript_available": true,
    "word_count": 1250,
    "language": "en",
    "top_keywords": [
      {"keyword": "technology", "frequency": 15, "relevance": 0.89}
    ]
  }
}
```

### Full Triangulation
```bash
POST /api/v1/triangulation/full-triangulation
{
  "username": "johndoe",
  "person_name": "John Doe",
  "video_path": "/path/to/video.mp4",
  "analyze_social": true,
  "analyze_video": true
}
```

**Response:**
```json
{
  "person_name": "John Doe",
  "username": "johndoe",
  "social_profiles": {
    "found_count": 5,
    "profiles": [...],
    "platforms_checked": 12
  },
  "video_analysis": {
    "video_id": "abc123",
    "faces_detected": 45,
    "unique_faces": 3,
    "transcript_words": 1250,
    "top_keywords": [...]
  },
  "triangulation_score": 0.85,
  "confidence_level": "high"
}
```

---

## 📦 Installation

### 1. Core Dependencies
```bash
pip install fastapi uvicorn pydantic aiohttp
```

### 2. Video Intelligence Dependencies
```bash
# OpenCV for video processing
pip install opencv-python

# Face recognition (requires dlib)
# Note: dlib requires cmake and a C++ compiler
pip install cmake
pip install dlib
pip install face-recognition

# Audio processing
pip install moviepy

# Speech-to-Text (Whisper)
pip install openai-whisper
```

### 3. Graph Database
```bash
pip install neo4j

# Install and run Neo4j
# Docker: docker run -p 7687:7687 -p 7474:7474 neo4j:latest
# Or download from: https://neo4j.com/download/
```

### 4. Optional: Celery for Async Tasks
```bash
pip install celery redis
```

---

## 🧪 Testing

Run the comprehensive test suite:
```bash
cd backend
python test_triangulation_system.py
```

This will test:
1. ✅ Social profile discovery
2. ✅ Video intelligence capabilities
3. ✅ Graph schema and queries
4. ✅ Full triangulation workflow

---

## 🔧 Configuration

### Environment Variables
```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Video Processing
FRAME_SAMPLE_RATE=30
WHISPER_MODEL=base  # tiny, base, small, medium, large

# Social Profiling
SOCIAL_TIMEOUT=10
USER_AGENT=Mozilla/5.0 (compatible; OSINT-Bot/2.0)
```

---

## 📊 Performance Considerations

### Social Profiling
- **Parallel execution:** Checks all platforms simultaneously
- **Typical time:** 2-5 seconds for 12 platforms
- **Configurable timeout:** Adjust per platform (default: 10s)

### Video Analysis
- ⚠️ **Heavy operation:** Can take 30s-5min depending on video length
- **Recommended:** Use Celery for async processing in production
- **Face recognition:** ~100ms per frame
- **Whisper transcription:** ~1x video duration (realtime)

### Memory Usage
- **Face encodings:** ~500 bytes per face (128d float array)
- **Whisper models:**
  - tiny: 39 MB
  - base: 74 MB
  - small: 244 MB
  - medium: 769 MB
  - large: 1550 MB

---

## 🎨 Architecture

```
┌──────────────────────────────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Social     │  │    Video     │  │   Neo4j    │ │
│  │   Profiler   │  │  Intelligence│  │  Graph DB  │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
│         │                  │                 │        │
│         └──────────────────┴─────────────────┘        │
│                     │                                  │
│              Triangulation                             │
│                 Engine                                 │
└──────────────────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────────┐              ┌──────────┐
    │ Celery │              │  Redis   │
    │Workers │              │  Queue   │
    └────────┘              └──────────┘
```

---

## 🔒 Security & Ethics

**⚠️ IMPORTANT DISCLAIMERS:**

1. **Legal Compliance:** This tool is for legitimate OSINT research only. Always comply with:
   - Terms of Service of platforms being queried
   - Local laws regarding data collection
   - Privacy regulations (GDPR, CCPA, etc.)

2. **Ethical Usage:**
   - Obtain proper authorization before analyzing videos of individuals
   - Respect privacy and data protection rights
   - Use only for legal investigations, security research, or with explicit consent

3. **Rate Limiting:**
   - Implement proper delays between requests
   - Respect `robots.txt` and rate limits
   - Consider using proxies for large-scale operations

4. **Data Storage:**
   - Biometric data (face encodings) are sensitive
   - Implement proper encryption for stored data
   - Follow data retention policies

---

## 📚 Use Cases

### 1. **Corporate Security**
- Employee verification during onboarding
- Threat actor profiling
- Brand protection monitoring

### 2. **Law Enforcement**
- Person of interest investigations
- Digital evidence collection
- Pattern analysis across multiple sources

### 3. **Journalism**
- Source verification
- Fact-checking
- Investigative reporting

### 4. **Cybersecurity**
- Threat intelligence gathering
- Social engineering defense
- Incident response

---

## 🛣️ Roadmap

- [ ] Add more social platforms (Discord, Telegram, WhatsApp)
- [ ] Implement real-time video stream analysis
- [ ] Add face clustering for grouping unknown persons
- [ ] Emotion detection from facial expressions
- [ ] Voice recognition and speaker diarization
- [ ] Automated report generation
- [ ] Web scraping for additional context
- [ ] Integration with other OSINT tools (Maltego, Recon-ng)

---

## 🤝 Contributing

This is a research project. Contributions welcome:
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

---

## 📄 License

This project is for educational and research purposes. Use responsibly and ethically.

---

## 🆘 Troubleshooting

### Face Recognition Installation Issues
```bash
# macOS
brew install cmake dlib
pip install face-recognition

# Ubuntu/Debian
sudo apt-get install cmake libopenblas-dev liblapack-dev
pip install face-recognition

# Windows
# Install Visual Studio C++ Build Tools first
pip install cmake
pip install dlib
pip install face-recognition
```

### Whisper CUDA Support
```bash
# For GPU acceleration
pip install openai-whisper[cuda]
```

### Neo4j Connection Issues
```bash
# Check Neo4j is running
cypher-shell -u neo4j -p password

# Verify connection
curl http://localhost:7474
```

---

## 📞 Support

For issues or questions:
1. Check the test suite: `python test_triangulation_system.py`
2. Review API documentation: http://localhost:8000/docs
3. Open an issue on GitHub

---

**Built with ❤️ for the OSINT community**
