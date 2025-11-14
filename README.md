# ShortsCreator - Video Editor API

A Flask-based video editing API with async processing capabilities, featuring subtitle generation using Whisper, video splitting/joining, and music overlay functionality.

## Features

- 🎬 **Subtitle Generation**: Automatic subtitle generation using OpenAI Whisper
- ✂️ **Video Splitting**: Split videos by start/end times
- 🔗 **Video Joining**: Concatenate multiple videos
- 🎵 **Music Overlay**: Add background music with custom settings
- ⚡ **Async Processing**: Background job processing with status polling
- 🐳 **Docker Ready**: Containerized for easy deployment
- ☁️ **Cloud Ready**: Prepared for Digital Ocean deployment

## Quick Start

### Local Development

1. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Docker Deployment

1. **Build and run with Docker Compose**:
```bash
docker-compose up --build
```

2. **Or use the deployment script**:
```bash
./deploy.sh
```

## API Endpoints

### Health Check
```
GET /health
```

### Add Subtitles
```
POST /add-subtitles
Content-Type: application/json

{
  "language": "en",
  "url": "https://example.com/video.mp4",
  "return_subtitles_file": true,
  "settings": {
    "style": "classic",
    "box-color": "#000000",
    "outline-width": 10,
    "word-color": "#002F6C",
    "shadow-offset": 0,
    "shadow-color": "#000000",
    "max-words-per-line": 4,
    "font-size": 100,
    "font-family": "Luckiest Guy",
    "position": "center-center",
    "outline-color": "#000000",
    "line-color": "#FFF4E9"
  }
}
```

### Split Video
```
POST /split-video
Content-Type: application/json

{
  "url": "https://example.com/video.mp4",
  "start_time": 10.0,
  "end_time": 30.0
}
```

### Join Videos
```
POST /join-videos
Content-Type: application/json

{
  "urls": [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
    "https://example.com/video3.mp4"
  ]
}
```

### Add Music
```
POST /add-music
Content-Type: application/json

{
  "video_url": "https://example.com/video.mp4",
  "music_url": "https://example.com/music.mp3",
  "volume": 0.5,
  "fade_in": 2,
  "fade_out": 2,
  "loop_music": true
}
```

### Check Job Status
```
GET /job-status/{job_id}
```

### Download Result
```
GET /download/{job_id}
```

## Response Format

All processing endpoints return a job ID:
```json
{
  "job_id": "uuid-here",
  "status": "pending",
  "message": "Processing started"
}
```

Job status responses:
```json
{
  "job_id": "uuid-here",
  "job_type": "add_subtitles",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:02:00",
  "progress": 100,
  "output_path": "temp/uuid_output.mp4",
  "subtitle_path": "temp/uuid_subtitles.srt"
}
```

## Subtitle Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `style` | Text style | "classic" |
| `box-color` | Background box color | "#000000" |
| `outline-width` | Text outline width | 10 |
| `word-color` | Text color | "#002F6C" |
| `shadow-offset` | Shadow offset | 0 |
| `shadow-color` | Shadow color | "#000000" |
| `max-words-per-line` | Words per line | 4 |
| `font-size` | Font size | 100 |
| `font-family` | Font family | "Luckiest Guy" |
| `position` | Text position | "center-center" |
| `outline-color` | Outline color | "#000000" |
| `line-color` | Line color | "#FFF4E9" |

### Position Options
- `top-left`, `top-center`, `top-right`
- `center-left`, `center-center`, `center-right` 
- `bottom-left`, `bottom-center`, `bottom-right`

## Music Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `volume` | Music volume (0.0-1.0) | 0.5 |
| `fade_in` | Fade in duration (seconds) | 0 |
| `fade_out` | Fade out duration (seconds) | 0 |
| `loop_music` | Loop music to match video | false |

## Digital Ocean Deployment

1. **Create a Digital Ocean Droplet** with Docker pre-installed
2. **Clone the repository** on the droplet
3. **Run the deployment script**:
```bash
./deploy.sh
```

### Environment Variables for Production

Create a `.env` file for production settings:
```bash
FLASK_ENV=production
MAX_CONTENT_LENGTH=500000000  # 500MB
UPLOAD_TIMEOUT=600  # 10 minutes
```

## Dependencies

- Flask 3.0.0
- OpenAI Whisper
- MoviePy
- FFmpeg
- PyTorch
- Pillow

## File Structure

```
ShortsCreator/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── deploy.sh             # Deployment script
├── app/
│   ├── services/
│   │   ├── video_service.py      # Video processing
│   │   ├── subtitle_service.py   # Whisper integration
│   │   └── job_manager.py        # Async job handling
│   └── utils/
│       └── download_utils.py     # URL download utilities
├── temp/                 # Temporary files
├── uploads/              # Upload directory
├── jobs/                 # Job status files
└── static/               # Static files
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details