# 🚀 ShortsCreator - One-Click Digital Ocean Deploy

Deploy your own video processing API with subtitle generation in minutes!

## 🎯 Quick Deploy Options

### Option 1: One-Click Script (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/deploy-to-do.sh | sudo bash
```

### Option 2: Manual Docker Deploy
```bash
# Clone the repository
git clone https://github.com/jdportugal/VideoEditorAPI.git
cd shortscreator

# Start with Docker Compose
docker-compose up -d

# Check if running
curl http://localhost:5000/health
```

### Option 3: Digital Ocean App Platform
[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/jdportugal/VideoEditorAPI/tree/main)

## 📋 Server Requirements

### Minimum Requirements
- **CPU**: 2 vCPUs
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Bandwidth**: 1TB/month
- **OS**: Ubuntu 20.04+ / Debian 11+

### Recommended for Production
- **CPU**: 4 vCPUs (for faster video processing)
- **RAM**: 8GB (for larger videos)
- **Storage**: 50GB SSD (for temporary files)
- **Bandwidth**: 3TB/month

## 🔧 Digital Ocean Droplet Setup

### 1. Create Droplet
```bash
# Using doctl CLI
doctl compute droplet create shortscreator \
  --image ubuntu-20-04-x64 \
  --size s-2vcpu-4gb \
  --region nyc3 \
  --ssh-keys your-ssh-key-id
```

### 2. Connect and Deploy
```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Run the one-click installer
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/deploy-to-do.sh | bash
```

## 🌐 API Access

Once deployed, your API will be available at:
- **URL**: `http://your-droplet-ip:5000`
- **Health Check**: `http://your-droplet-ip:5000/health`

### API Endpoints
```bash
# Add subtitles to video
curl -X POST http://your-ip:5000/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4"}'

# Check job status
curl http://your-ip:5000/job-status/job-id

# Download processed video
curl http://your-ip:5000/download/job-id -o video.mp4
```

## 🔒 Security Setup (Optional)

### Enable HTTPS with Let's Encrypt
```bash
# Install Nginx
apt install nginx -y

# Install Certbot
apt install certbot python3-certbot-nginx -y

# Configure domain and SSL
certbot --nginx -d your-domain.com
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring & Maintenance

### Check Service Status
```bash
# Service status
systemctl status shortscreator

# Docker containers
docker-compose ps

# View logs
docker-compose logs -f
```

### Update Application
```bash
cd /opt/shortscreator
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## 🔧 Customization

### Environment Variables
Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
nano .env
```

### Resource Limits
Edit `docker-compose.yml` to adjust:
- Memory limits
- CPU limits
- Storage volumes

## 🆘 Troubleshooting

### Common Issues

**Port 5000 not accessible:**
```bash
# Check firewall
ufw status
ufw allow 5000/tcp

# Check if service is running
docker-compose ps
```

**Out of disk space:**
```bash
# Clean up temporary files
docker system prune -a
```

**High memory usage:**
```bash
# Check memory usage
docker stats
# Consider upgrading droplet size
```

## 💰 Cost Estimation

| Droplet Size | Monthly Cost | Processing Speed | Concurrent Jobs |
|--------------|-------------|------------------|-----------------|
| s-2vcpu-4gb  | $24/month   | Moderate         | 1-2             |
| s-4vcpu-8gb  | $48/month   | Fast             | 2-4             |
| c-4           | $80/month   | Very Fast        | 4-6             |

## 🎉 What's Included

- ✅ **Whisper AI** for subtitle generation
- ✅ **MoviePy** for video processing
- ✅ **Karaoke-style** subtitle highlighting
- ✅ **Video splitting** and joining
- ✅ **Background music** addition
- ✅ **Health monitoring**
- ✅ **Auto-restart** on failure
- ✅ **Job queue** system

## 📞 Support

- 📖 [Documentation](https://github.com/jdportugal/VideoEditorAPI/wiki)
- 🐛 [Issues](https://github.com/jdportugal/VideoEditorAPI/issues)
- 💬 [Discussions](https://github.com/jdportugal/VideoEditorAPI/discussions)