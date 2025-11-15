# 🚀 One-Click Digital Ocean Deployment

Deploy ShortsCreator on Digital Ocean with a single command!

## ⚡ Quick Deploy (30 seconds)

### Step 1: Create Digital Ocean Droplet
```bash
# Minimum: 2 vCPUs, 4GB RAM, Ubuntu 20.04
# Recommended: 4 vCPUs, 8GB RAM for better performance
```

### Step 2: One-Click Install
```bash
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install.sh | sudo bash
```

That's it! Your video processing API will be running at `http://your-droplet-ip:5000`

## 🎯 What You Get

- ✅ **Complete Docker setup** with auto-restart
- ✅ **Whisper AI** for subtitle generation  
- ✅ **Karaoke-style** highlighting
- ✅ **Video splitting** and joining
- ✅ **Background music** addition
- ✅ **Health monitoring** and logging
- ✅ **Firewall configuration**
- ✅ **Systemd service** for auto-start

## 📋 Deployment Options

### Option 1: One-Click Script (Easiest)
```bash
# SSH into your Digital Ocean droplet
ssh root@your-droplet-ip

# Run the installer
curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install.sh | bash
```

### Option 2: Manual Docker Deploy
```bash
# Clone repository
git clone https://github.com/jdportugal/VideoEditorAPI.git
cd shortscreator

# Start services
docker-compose up -d

# Check status
curl http://localhost:5000/health
```

### Option 3: Digital Ocean App Platform
Click the deploy button in your GitHub repository:

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/jdportugal/VideoEditorAPI/tree/main)

## 🖥️ Server Requirements

| Use Case | CPU | RAM | Storage | Monthly Cost |
|----------|-----|-----|---------|--------------|
| Personal | 2 vCPUs | 4GB | 25GB | ~$24 |
| Small Team | 4 vCPUs | 8GB | 50GB | ~$48 |
| Production | 8 vCPUs | 16GB | 100GB | ~$96 |

## 🔧 Post-Deployment Setup

### Test Your API
```bash
# Health check
curl http://your-droplet-ip:5000/health

# Process a test video
curl -X POST http://your-droplet-ip:5000/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{"url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"}'
```

### Monitor Your Service
```bash
# Check service status
systemctl status shortscreator

# View logs
docker-compose logs -f video-editor-api

# System resources
htop
```

### Enable HTTPS (Optional)
```bash
# Install Nginx and Certbot
apt install nginx certbot python3-certbot-nginx -y

# Get SSL certificate (replace your-domain.com)
certbot --nginx -d your-domain.com

# Nginx will proxy to localhost:5000
```

## 🔒 Security Considerations

### Firewall Rules
The installer automatically configures:
- ✅ Port 22 (SSH) - Open
- ✅ Port 5000 (API) - Open  
- ✅ All other ports - Blocked

### Additional Security
```bash
# Change SSH port (optional)
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart ssh
ufw allow 2222/tcp
ufw delete allow ssh

# Add API authentication (edit app.py)
# Implement rate limiting
# Set up monitoring/alerts
```

## 📊 Monitoring & Maintenance

### Built-in Health Monitoring
- Health endpoint: `/health`
- Docker health checks
- Auto-restart on failure
- System resource monitoring

### Log Management
```bash
# Application logs
docker-compose logs -f

# System logs
journalctl -u shortscreator.service -f

# Nginx logs (if using HTTPS)
tail -f /var/log/nginx/error.log
```

### Updates
```bash
cd /opt/shortscreator
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

## 🆘 Troubleshooting

### Service Won't Start
```bash
# Check service status
systemctl status shortscreator

# Check Docker
docker-compose ps

# View detailed logs
journalctl -u shortscreator.service -n 50
```

### API Not Responding
```bash
# Check if port is open
netstat -tlnp | grep :5000

# Check firewall
ufw status

# Test internally
curl http://localhost:5000/health
```

### Out of Disk Space
```bash
# Clean up Docker
docker system prune -a

# Clean up temp files
rm -rf /opt/shortscreator/temp/*

# Check disk usage
df -h
```

## 💡 Tips for Production

### Performance Optimization
1. **Use SSD droplets** for faster I/O
2. **Enable swap** for memory overflow
3. **Set up log rotation** to prevent disk fills
4. **Monitor resource usage** with tools like htop
5. **Consider load balancing** for high traffic

### Cost Optimization
1. **Auto-shutdown** during off-hours
2. **Use block storage** for large files
3. **Implement caching** for repeated requests
4. **Set up alerts** for resource usage

### Scaling
1. **Multiple droplets** behind a load balancer
2. **Separate database** droplet if needed
3. **CDN** for video delivery
4. **Queue system** for job processing

## 🎉 Success!

Once deployed, you'll have a fully functional video processing API that can:

- 🎬 Add AI-generated subtitles with karaoke highlighting
- ✂️ Split videos by time range
- 🔗 Join multiple videos together  
- 🎵 Add background music with volume control
- 📊 Track processing jobs with real-time status
- 💾 Download processed videos and subtitle files

Your API is now ready to handle video processing requests from anywhere in the world!