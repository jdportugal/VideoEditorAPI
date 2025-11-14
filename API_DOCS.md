# ShortsCreator API Documentation

## Overview

The ShortsCreator API is a Flask-based video editing service that provides async video processing capabilities. All operations are performed asynchronously with job status tracking.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently no authentication is required. For production deployment, consider adding API keys or JWT authentication.

## Response Format

All responses are in JSON format. Async operations return a job ID for status tracking:

```json
{
  "job_id": "uuid-string",
  "status": "pending|processing|completed|failed",
  "message": "Description"
}
```

## Error Handling

Errors return appropriate HTTP status codes with error messages:

```json
{
  "error": "Error description"
}
```

## Endpoints

### Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### Add Subtitles

Generate and add subtitles to a video using Whisper.

**Endpoint:** `POST /add-subtitles`

**Request Body:**
```json
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

**Parameters:**
- `url` (required): Video URL
- `language` (optional): Language code (default: "en")
- `return_subtitles_file` (optional): Return subtitle file separately (default: false)
- `settings` (optional): Subtitle styling settings

**Subtitle Settings:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `style` | string | "classic" | Text style |
| `box-color` | string | "#000000" | Background box color |
| `outline-width` | number | 10 | Text outline width |
| `word-color` | string | "#002F6C" | Text color |
| `shadow-offset` | number | 0 | Shadow offset |
| `shadow-color` | string | "#000000" | Shadow color |
| `max-words-per-line` | number | 4 | Words per line |
| `font-size` | number | 100 | Font size |
| `font-family` | string | "Luckiest Guy" | Font family |
| `position` | string | "center-center" | Text position |
| `outline-color` | string | "#000000" | Outline color |
| `line-color` | string | "#FFF4E9" | Line color |

**Position Options:**
- `top-left`, `top-center`, `top-right`
- `center-left`, `center-center`, `center-right`
- `bottom-left`, `bottom-center`, `bottom-right`

---

### Split Video

Split a video from start time to end time.

**Endpoint:** `POST /split-video`

**Request Body:**
```json
{
  "url": "https://example.com/video.mp4",
  "start_time": 10.0,
  "end_time": 30.0
}
```

**Parameters:**
- `url` (required): Video URL
- `start_time` (required): Start time in seconds
- `end_time` (required): End time in seconds

---

### Join Videos

Concatenate multiple videos into one.

**Endpoint:** `POST /join-videos`

**Request Body:**
```json
{
  "urls": [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
    "https://example.com/video3.mp4"
  ]
}
```

**Parameters:**
- `urls` (required): Array of video URLs (minimum 2)

---

### Add Music

Add background music to a video.

**Endpoint:** `POST /add-music`

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "music_url": "https://example.com/music.mp3",
  "volume": 0.5,
  "fade_in": 2,
  "fade_out": 2,
  "loop_music": true
}
```

**Parameters:**
- `video_url` (required): Video URL
- `music_url` (required): Music/audio URL
- `volume` (optional): Music volume 0.0-1.0 (default: 0.5)
- `fade_in` (optional): Fade in duration in seconds (default: 0)
- `fade_out` (optional): Fade out duration in seconds (default: 0)
- `loop_music` (optional): Loop music to match video length (default: false)

---

### Job Status

Check the status of an async job.

**Endpoint:** `GET /job-status/{job_id}`

**Response:**
```json
{
  "job_id": "uuid-string",
  "job_type": "add_subtitles",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:02:00",
  "progress": 100,
  "data": { ... },
  "error": null,
  "output_path": "temp/uuid_output.mp4",
  "subtitle_path": "temp/uuid_subtitles.srt"
}
```

**Status Values:**
- `pending`: Job is queued
- `processing`: Job is being processed
- `completed`: Job completed successfully
- `failed`: Job failed with error

---

### Download Result

Download the processed video file.

**Endpoint:** `GET /download/{job_id}`

**Response:** Binary file download

**Requirements:**
- Job must be in `completed` status
- Output file must exist

---

## Usage Examples

### Python

```python
import requests

# Add subtitles
response = requests.post('http://localhost:5000/add-subtitles', json={
    'url': 'https://example.com/video.mp4',
    'language': 'en',
    'settings': {
        'font-size': 120,
        'position': 'bottom-center'
    }
})

job_id = response.json()['job_id']

# Check status
status = requests.get(f'http://localhost:5000/job-status/{job_id}')
print(status.json())

# Download result when completed
if status.json()['status'] == 'completed':
    result = requests.get(f'http://localhost:5000/download/{job_id}')
    with open('output.mp4', 'wb') as f:
        f.write(result.content)
```

### cURL

```bash
# Add subtitles
curl -X POST http://localhost:5000/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video.mp4",
    "language": "en"
  }'

# Check job status
curl http://localhost:5000/job-status/YOUR-JOB-ID

# Download result
curl -O http://localhost:5000/download/YOUR-JOB-ID
```

### JavaScript

```javascript
// Add subtitles
const response = await fetch('http://localhost:5000/add-subtitles', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://example.com/video.mp4',
    language: 'en',
    settings: {
      'font-size': 120,
      'position': 'bottom-center'
    }
  })
});

const { job_id } = await response.json();

// Poll for completion
const pollStatus = async () => {
  const statusResponse = await fetch(`http://localhost:5000/job-status/${job_id}`);
  const status = await statusResponse.json();
  
  if (status.status === 'completed') {
    // Download result
    const downloadUrl = `http://localhost:5000/download/${job_id}`;
    window.open(downloadUrl);
  } else if (status.status === 'failed') {
    console.error('Job failed:', status.error);
  } else {
    setTimeout(pollStatus, 5000); // Check again in 5 seconds
  }
};

pollStatus();
```

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider adding:
- Request rate limits per IP
- Concurrent job limits per user
- File size limits
- Processing time limits

## File Size Limits

Default limits:
- Maximum upload size: 500MB
- Processing timeout: 10 minutes per job
- Temporary file cleanup: 24 hours

Configure these in the `.env` file or Docker environment variables.

## Supported Formats

**Video Input:**
- MP4, AVI, MOV, MKV, WMV, FLV, WEBM

**Audio Input:**
- MP3, WAV, AAC, OGG, FLAC, M4A

**Video Output:**
- MP4 (H.264 codec)

**Subtitle Output:**
- SRT, VTT, JSON

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (missing parameters, invalid data) |
| 404 | Not Found (invalid job ID, file not found) |
| 500 | Internal Server Error (processing error) |

## Best Practices

1. **Always check job status** before attempting to download results
2. **Use appropriate timeouts** when polling job status
3. **Handle errors gracefully** in your client applications
4. **Clean up downloaded files** to save storage space
5. **Validate URLs** before submitting to avoid failed jobs

## Deployment Notes

### Docker

The API is designed to run in Docker containers. See `docker-compose.yml` for configuration.

### Digital Ocean

For Digital Ocean deployment:
1. Create a droplet with Docker
2. Clone the repository
3. Run `./deploy.sh`
4. Configure firewall to allow port 5000
5. Optionally set up a reverse proxy (nginx) for production

### Production Considerations

- Add authentication/authorization
- Implement rate limiting
- Set up monitoring and logging
- Configure HTTPS
- Add file cleanup jobs
- Set up health checks
- Configure auto-scaling if needed