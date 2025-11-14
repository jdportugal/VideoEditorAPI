# 🌍 ngrok Setup for ShortsCreator API

Your ShortsCreator API is now accessible globally via ngrok!

## 🚀 **Current Setup**

**Public URL:** `https://3659b7ea957e.ngrok-free.app`
**Local URL:** `http://localhost:5000`
**Dashboard:** `http://localhost:4040`

## 📋 **Available Endpoints**

| Endpoint | Method | Purpose | Public URL |
|----------|--------|---------|------------|
| Health Check | GET | API status | `https://3659b7ea957e.ngrok-free.app/health` |
| Add Subtitles | POST | Generate subtitles | `https://3659b7ea957e.ngrok-free.app/add-subtitles` |
| Split Video | POST | Split video clips | `https://3659b7ea957e.ngrok-free.app/split-video` |
| Join Videos | POST | Concatenate videos | `https://3659b7ea957e.ngrok-free.app/join-videos` |
| Add Music | POST | Add background music | `https://3659b7ea957e.ngrok-free.app/add-music` |
| Job Status | GET | Check processing status | `https://3659b7ea957e.ngrok-free.app/job-status/{id}` |
| Download | GET | Download processed file | `https://3659b7ea957e.ngrok-free.app/download/{id}` |

## 🔧 **Management Scripts**

### Start ngrok
```bash
./setup_ngrok.sh
```

### Test ngrok API
```bash
python3 test_ngrok_api.py
```

### Manual ngrok start
```bash
# Stop existing
pkill -f ngrok

# Start new tunnel
ngrok http 5000
```

## 🧪 **Quick Test Commands**

```bash
# Health check
curl https://3659b7ea957e.ngrok-free.app/health

# Split a video (fastest test)
curl -X POST https://3659b7ea957e.ngrok-free.app/split-video \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    "start_time": 2,
    "end_time": 8
  }'

# Check job status (use job_id from above response)
curl https://3659b7ea957e.ngrok-free.app/job-status/YOUR-JOB-ID

# Download result when completed
curl -O https://3659b7ea957e.ngrok-free.app/download/YOUR-JOB-ID
```

## 📱 **Example: Add Subtitles via ngrok**

```bash
curl -X POST https://3659b7ea957e.ngrok-free.app/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-video-url.com/video.mp4",
    "language": "en",
    "return_subtitles_file": true,
    "settings": {
      "font-size": 120,
      "position": "bottom-center",
      "line-color": "#FFFFFF",
      "outline-color": "#000000",
      "max-words-per-line": 3
    }
  }'
```

## 🌐 **Remote Access Instructions**

### For External Users/Applications:

1. **Base URL:** Use `https://3659b7ea957e.ngrok-free.app` instead of `localhost:5000`
2. **Same API:** All endpoints work exactly the same
3. **Authentication:** No authentication required (add if needed for production)

### Python Example:
```python
import requests

# Your API base URL
API_BASE = "https://3659b7ea957e.ngrok-free.app"

# Add subtitles
response = requests.post(f"{API_BASE}/add-subtitles", json={
    "url": "https://your-video.com/video.mp4",
    "language": "en"
})

job_id = response.json()['job_id']

# Check status
status = requests.get(f"{API_BASE}/job-status/{job_id}")
print(status.json())
```

### JavaScript Example:
```javascript
const API_BASE = "https://3659b7ea957e.ngrok-free.app";

// Add subtitles
const response = await fetch(`${API_BASE}/add-subtitles`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: "https://your-video.com/video.mp4",
    language: "en"
  })
});

const { job_id } = await response.json();

// Check status
const statusResponse = await fetch(`${API_BASE}/job-status/${job_id}`);
const status = await statusResponse.json();
console.log(status);
```

## ⚙️ **ngrok Configuration**

### Current Setup:
- **Protocol:** HTTPS
- **Port:** 5000
- **Subdomain:** Random (changes on restart)
- **Plan:** Free tier

### Upgrade Options:
- **Static subdomain:** Upgrade to paid plan
- **Custom domain:** Pro plan feature  
- **Authentication:** Can be added in ngrok config
- **Rate limiting:** Available in paid plans

## 🔒 **Security Notes**

### Current Security:
- ✅ HTTPS encryption provided by ngrok
- ✅ Random subdomain makes URL hard to guess
- ⚠️ No authentication - anyone with URL can access

### Production Recommendations:
1. **Add API authentication** (JWT tokens, API keys)
2. **Rate limiting** to prevent abuse
3. **Input validation** for all endpoints
4. **Custom domain** for professional use
5. **Monitoring** for usage and errors

## 🛠 **Troubleshooting**

### ngrok Not Working:
```bash
# Check if ngrok is running
curl http://localhost:4040/api/tunnels

# Restart ngrok
./setup_ngrok.sh

# Check Docker container
docker ps | grep shortscreator
```

### API Not Responding:
```bash
# Test local API first
curl http://localhost:5000/health

# Check Docker logs
docker logs shortscreator-video-editor-api-1

# Restart container
docker-compose restart
```

### Job Processing Issues:
```bash
# Check job status files
ls jobs/

# Check container logs for errors
docker logs shortscreator-video-editor-api-1 --tail 50
```

## 📞 **Support**

Your ShortsCreator API is now globally accessible! The ngrok tunnel allows you to:

- ✅ Test from any device/location
- ✅ Share with team members 
- ✅ Integrate with external services
- ✅ Demo to clients
- ✅ Mobile app development

**Public URL:** `https://3659b7ea957e.ngrok-free.app`

**Note:** This URL changes each time ngrok restarts. For a permanent URL, consider upgrading to ngrok's paid plan.