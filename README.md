# 🎬 VideoEditorAPI - AI Video Processing with Subtitles

Transform videos with AI-generated subtitles, karaoke effects, and professional editing tools.

## ⚡ Quick Deploy on Digital Ocean

```bash
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install-ghcr.sh | sudo bash
```

**That's it!** Your API will be running at `http://your-droplet-ip:5000` in 30 seconds.

## 🎯 Features

- 🎤 **AI Subtitles** - Whisper-powered speech recognition with word-level timing
- 🌟 **Karaoke Effects** - Real-time word highlighting with customizable styles
- ✂️ **Video Editing** - Split, join, and trim videos with precise timing
- 🎵 **Audio Mixing** - Add background music with volume control and fading
- 📊 **Job Tracking** - Real-time processing status with progress updates
- 🚀 **One-Click Deploy** - Ready for Digital Ocean with pre-built containers

## 🚀 Quick Start

### Option 1: One-Click Digital Ocean Deploy (Recommended)
```bash
# Create a Digital Ocean droplet (4GB+ RAM recommended)
# SSH into your droplet and run:
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install-ghcr.sh | sudo bash
```

### Option 2: Local Development
```bash
git clone https://github.com/jdportugal/VideoEditorAPI.git
cd VideoEditorAPI
docker-compose up -d
```

## 🛠️ API Endpoints

### Add Subtitles with Karaoke Effect
```bash
curl -X POST http://your-ip:5000/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video.mp4",
    "settings": {
      "font-size": 120,
      "normal-color": "#FFF4E9"
    }
  }'
```

### Split Video by Time Range
```bash
curl -X POST http://your-ip:5000/split-video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video.mp4",
    "start_time": "00:00:10,000",
    "end_time": "00:01:30,500"
  }'
```

### Join Multiple Videos
```bash
curl -X POST http://your-ip:5000/join-videos \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/video1.mp4",
      "https://example.com/video2.mp4"
    ]
  }'
```

### Add Background Music
```bash
curl -X POST http://your-ip:5000/add-music \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "music_url": "https://example.com/music.mp3",
    "settings": {
      "volume": 0.3,
      "fade_in": 2,
      "fade_out": 3
    }
  }'
```

### Check Job Status
```bash
curl http://your-ip:5000/job-status/YOUR_JOB_ID
```

### Download Results
```bash
# Download processed video
curl http://your-ip:5000/download/YOUR_JOB_ID -o result.mp4

# Download subtitle file
curl http://your-ip:5000/download-subtitles/YOUR_JOB_ID -o subtitles.srt
```

## 📋 System Requirements

| Use Case | CPU | RAM | Storage | Monthly Cost |
|----------|-----|-----|---------|--------------|
| Personal | 2 vCPUs | 4GB | 25GB | ~$24 |
| Small Team | 4 vCPUs | 8GB | 50GB | ~$48 |
| Production | 8 vCPUs | 16GB | 100GB | ~$96 |

## 🎨 Subtitle Customization

The API supports extensive subtitle customization:

```json
{
  "url": "https://example.com/video.mp4",
  "settings": {
    "font-size": 120,
    "font-family": "Luckiest Guy",
    "normal-color": "#FFFFFF",
    "outline-width": 10,
    "position": "bottom-center"
  }
}
```

### Available Options
- **Font sizes**: 80-200px
- **Colors**: Any hex color (#FFFFFF, #FF0000, etc.)
- **Positions**: top-center, center-center, bottom-center, etc.
- **Effects**: Karaoke highlighting, typewriter, popup modes

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Optional customization in .env file
FLASK_ENV=production
MAX_CONCURRENT_JOBS=4
VIDEO_MAX_DURATION=1800
WHISPER_MODEL=base
```

### Docker Compose Override
```yaml
version: '3.8'
services:
  video-editor-api:
    image: ghcr.io/jdportugal/videoeditorapi:latest
    environment:
      - MAX_WORKERS=8
    volumes:
      - ./custom-fonts:/app/fonts
```

## 📊 Performance & Scaling

### Processing Times (Approximate)
- **1-minute video**: 30-60 seconds
- **5-minute video**: 2-4 minutes  
- **10-minute video**: 5-8 minutes

### Scaling Options
- **Horizontal**: Multiple droplets + load balancer
- **Vertical**: Upgrade to CPU-optimized droplets
- **Queue**: Redis-based job queuing for high volume

## 🆘 Troubleshooting

### Common Issues

**API not responding:**
```bash
# Check service status
docker-compose ps
docker-compose logs -f

# Restart if needed
docker-compose restart
```

**Out of disk space:**
```bash
# Clean up temporary files
docker system prune -f
rm -rf /opt/shortscreator/temp/*
```

**Memory issues:**
```bash
# Check resource usage
docker stats

# Consider upgrading droplet size
```

## 🔄 Updates & Maintenance

### One-Command Updates
```bash
cd /opt/shortscreator
./update.sh
```

### Manual Updates
```bash
docker-compose pull
docker-compose up -d
```

## 📚 Documentation

- [🚀 Deployment Guide](DEPLOY.md) - Complete setup instructions
- [🔧 Maintenance Guide](MAINTENANCE.md) - Zero-touch maintenance
- [📖 API Documentation](API_DOCS.md) - Detailed endpoint reference

## 🎉 What's Included

✅ **Whisper AI** for accurate speech recognition  
✅ **MoviePy** for professional video processing  
✅ **Karaoke-style** subtitle highlighting  
✅ **Custom fonts** (Luckiest Guy included)  
✅ **Health monitoring** with auto-restart  
✅ **Job queue system** for async processing  
✅ **One-command updates** for easy maintenance  
✅ **Pre-built Docker images** for fast deployment  

## 🌟 Use Cases

- **Content Creation**: Add subtitles to YouTube videos, TikToks, Instagram Reels
- **Education**: Create educational videos with highlighted text
- **Marketing**: Professional video content for social media
- **Accessibility**: Make videos accessible with accurate subtitles
- **Localization**: Generate subtitle files for translation

## 💡 Tips for Best Results

1. **Video Quality**: Use MP4 format with clear audio
2. **File Size**: Keep videos under 500MB for faster processing
3. **Audio Quality**: Clear speech improves subtitle accuracy
4. **Network**: Stable internet connection for file uploads/downloads

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📞 Support

- 📖 [Documentation](https://github.com/jdportugal/VideoEditorAPI/wiki)
- 🐛 [Issues](https://github.com/jdportugal/VideoEditorAPI/issues)
- 💬 [Discussions](https://github.com/jdportugal/VideoEditorAPI/discussions)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

⭐ **Star this repository if it helped you!**

Built with ❤️ using Python, Flask, Whisper AI, and MoviePy.