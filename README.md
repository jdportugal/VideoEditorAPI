# 🎬 VideoEditorAPI

AI-powered video processing API with subtitle generation, karaoke effects, and editing tools.

## ⚡ Quick Start

### Option 1: Digital Ocean App Platform (Easiest)
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/jdportugal/VideoEditorAPI/tree/main&refcode=your-referral-code)

### Option 2: One-Click Droplet Deploy  
```bash
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install-ghcr.sh | sudo bash
```

### Option 2: Local Development
```bash
git clone https://github.com/jdportugal/VideoEditorAPI.git
cd VideoEditorAPI
docker-compose up -d
```

### Option 3: Manual Docker
```bash
docker run -d -p 8080:8080 ghcr.io/jdportugal/videoeditorapi:latest
```

## 🎯 Features

- 🎤 **AI Subtitles** - Whisper-powered speech recognition
- 🌟 **Karaoke Effects** - Word-by-word highlighting
- ✂️ **Video Editing** - Split, join, trim videos
- 🎵 **Audio Mixing** - Add background music
- 📊 **Job Tracking** - Real-time processing status

## 📋 System Requirements

- **CPU**: 2+ vCPUs (4+ recommended for faster processing)
- **RAM**: 4GB minimum (8GB+ for large videos)  
- **Storage**: 25GB+ SSD
- **OS**: Ubuntu 20.04+, Docker installed

## 🛠️ API Endpoints

### Health Check
```bash
GET /health
curl http://localhost:8080/health
```
**Response:**
```json
{"status": "healthy", "timestamp": "2024-01-01T12:00:00"}
```

---

### Add Subtitles with Karaoke Effect
```bash
POST /add-subtitles
curl -X POST http://localhost:8080/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video.mp4",
    "settings": {
      "font-size": 120,
      "normal-color": "#FFF4E9"
    }
  }'
```

**Parameters:**
- `url` (required): Video URL or Google Drive link
- `language` (optional): Language code (default: "en") 
- `settings` (optional): Subtitle styling options

**Styling Options:**
```json
{
  "font-size": 120,
  "font-family": "Luckiest Guy", 
  "normal-color": "#FFFFFF",
  "outline-width": 10,
  "position": "bottom-center"
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "pending", 
  "message": "Subtitle processing started"
}
```

---

### Split Video by Time
```bash
POST /split-video
curl -X POST http://localhost:8080/split-video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video.mp4",
    "start_time": "00:00:10,000",
    "end_time": "00:01:30,500"
  }'
```

**Time Formats Supported:**
- `"00:01:30,500"` (HH:MM:SS,mmm)
- `"90.5"` (seconds as string)
- `90.5` (numeric seconds)

---

### Join Multiple Videos
```bash
POST /join-videos
curl -X POST http://localhost:8080/join-videos \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/video1.mp4",
      "https://example.com/video2.mp4"
    ]
  }'
```

---

### Add Background Music
```bash
POST /add-music
curl -X POST http://localhost:8080/add-music \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "music_url": "https://example.com/music.mp3",
    "settings": {
      "volume": 0.3,
      "fade_in": 2,
      "fade_out": 3,
      "loop_music": true
    }
  }'
```

**Music Settings:**
- `volume`: 0.0 to 1.0 (default: 0.5)
- `fade_in`: Fade in duration in seconds
- `fade_out`: Fade out duration in seconds  
- `loop_music`: Loop music to match video length

---

### Check Job Status
```bash
GET /job-status/<job_id>
curl http://localhost:8080/job-status/your-job-id
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "progress": 100,
  "video_download_url": "/download/uuid-here",
  "subtitle_download_url": "/download-subtitles/uuid-here"
}
```

**Status Values:**
- `pending` - Job queued for processing
- `processing` - Currently being processed
- `completed` - Successfully completed
- `failed` - Processing failed (check `error` field)

---

### Download Processed Video
```bash
GET /download/<job_id>
curl http://localhost:8080/download/your-job-id -o result.mp4
```

---

### Download Subtitle File
```bash
GET /download-subtitles/<job_id>  
curl http://localhost:8080/download-subtitles/your-job-id -o subtitles.srt
```

## 🎨 Subtitle Customization

### Font Styles
- **font-family**: "Luckiest Guy" (default), "Arial", "DejaVu-Sans-Bold"
- **font-size**: 80-200 pixels (default: 120)
- **normal-color**: Any hex color (default: "#FFFFFF")
- **outline-width**: 0-20 pixels (default: 10)

### Positioning
- **top-left**, **top-center**, **top-right**  
- **center-left**, **center-center**, **center-right**
- **bottom-left**, **bottom-center**, **bottom-right**

### Karaoke Modes
- **karaoke** (default): Word-by-word highlighting
- **off**: Traditional sentence subtitles
- **popup**: Individual word pop-ups
- **typewriter**: Accumulating word display

## 📊 Usage Examples

### Basic Subtitle Addition
```bash
curl -X POST http://localhost:8080/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4"}'
```

### Custom Styling
```bash
curl -X POST http://localhost:8080/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video.mp4", 
    "settings": {
      "font-size": 140,
      "normal-color": "#FFD700",
      "outline-width": 8,
      "position": "top-center"
    }
  }'
```

### Split & Process Workflow
```bash
# 1. Split video to extract segment
curl -X POST http://localhost:8080/split-video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/long-video.mp4",
    "start_time": "00:02:00,000", 
    "end_time": "00:03:30,000"
  }'

# 2. Get job ID from response, check status
curl http://localhost:8080/job-status/JOB_ID

# 3. Download split video
curl http://localhost:8080/download/JOB_ID -o segment.mp4

# 4. Add subtitles to segment
curl -X POST http://localhost:8080/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{"url": "https://yourdomain.com/segment.mp4"}'
```

## 🚀 Deployment Options

### Digital Ocean (Recommended)
1. Create droplet (4GB+ RAM, Ubuntu 20.04+)
2. Run installer:
```bash
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install-ghcr.sh | sudo bash
```

### Local Development
```bash
git clone https://github.com/jdportugal/VideoEditorAPI.git
cd VideoEditorAPI
docker-compose up -d
```

### Custom Docker
```bash
docker run -d \
  --name videoeditor \
  -p 5000:5000 \
  -v ./temp:/app/temp \
  -v ./uploads:/app/uploads \
  ghcr.io/jdportugal/videoeditorapi:latest
```

## ⚙️ Configuration

### Environment Variables
```bash
# Optional customization
FLASK_ENV=production
MAX_CONCURRENT_JOBS=4
VIDEO_MAX_DURATION=1800
WHISPER_MODEL=base
LOG_LEVEL=INFO
```

### Volume Mounts
- `/app/temp` - Temporary processing files
- `/app/uploads` - User uploaded files  
- `/app/jobs` - Job status tracking
- `/app/logs` - Application logs

## 🔧 Troubleshooting

### Check Service Status
```bash
# Docker Compose
docker-compose ps
docker-compose logs -f

# Direct Docker
docker ps
docker logs videoeditor
```

### Common Issues

**Port 8080 not accessible:**
```bash
# Check firewall
sudo ufw allow 8080/tcp

# Check if service is running
curl http://localhost:8080/health
```

**Out of disk space:**
```bash
# Clean up temporary files
docker system prune -f
sudo rm -rf ./temp/*
```

**Memory issues:**
```bash
# Check resource usage
docker stats

# Increase droplet size or add swap
```

**Job stuck in processing:**
```bash
# Restart service
docker-compose restart

# Check logs for errors
docker-compose logs video-editor-api
```

## 📈 Performance

### Processing Times (Approximate)
- **1-minute video**: 30-60 seconds
- **5-minute video**: 2-4 minutes
- **10-minute video**: 5-10 minutes

### Optimization Tips
1. **Use CPU-optimized droplets** for faster processing
2. **Keep videos under 500MB** for best performance  
3. **Ensure clear audio** for better subtitle accuracy
4. **Use MP4 format** for compatibility

## 🔄 Updates & Maintenance

### Auto-Updates (If using installer)
```bash
cd /opt/shortscreator
./update.sh
```

### Manual Updates
```bash
docker-compose pull
docker-compose up -d
```

### Health Monitoring
```bash
# Check API health
curl http://localhost:8080/health

# View recent logs
docker-compose logs --tail=50

# Monitor resources
docker stats
```

## 🌐 Integration Examples

### Node.js
```javascript
const axios = require('axios');

async function addSubtitles(videoUrl) {
  const response = await axios.post('http://localhost:8080/add-subtitles', {
    url: videoUrl,
    settings: {
      'font-size': 120,
      'normal-color': '#FFD700'
    }
  });
  
  return response.data.job_id;
}

async function checkJobStatus(jobId) {
  const response = await axios.get(`http://localhost:8080/job-status/${jobId}`);
  return response.data;
}
```

### Python
```python
import requests
import time

def add_subtitles(video_url):
    response = requests.post('http://localhost:8080/add-subtitles', json={
        'url': video_url,
        'settings': {
            'font-size': 120,
            'normal-color': '#FFD700'
        }
    })
    return response.json()['job_id']

def wait_for_completion(job_id):
    while True:
        response = requests.get(f'http://localhost:8080/job-status/{job_id}')
        status = response.json()
        
        if status['status'] == 'completed':
            return status
        elif status['status'] == 'failed':
            raise Exception(f"Job failed: {status.get('error')}")
        
        time.sleep(5)
```

### cURL Scripts
```bash
#!/bin/bash
# process_video.sh

VIDEO_URL="$1"
API_URL="http://localhost:8080"

# Submit job
JOB_ID=$(curl -s -X POST "$API_URL/add-subtitles" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$VIDEO_URL\"}" | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Wait for completion
while true; do
  STATUS=$(curl -s "$API_URL/job-status/$JOB_ID" | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    echo "Downloading result..."
    curl -o "result.mp4" "$API_URL/download/$JOB_ID"
    curl -o "subtitles.srt" "$API_URL/download-subtitles/$JOB_ID" 
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Job failed!"
    exit 1
  fi
  
  sleep 5
done
```

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/jdportugal/VideoEditorAPI/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/jdportugal/VideoEditorAPI/discussions)
- 📧 **Email**: Create an issue for support

## 📄 License

MIT License - Feel free to use in personal and commercial projects.

---

⭐ **Star this repository if it helped you!**

Built with Python, Flask, Whisper AI, and MoviePy.