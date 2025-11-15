# 🔧 ShortsCreator - Zero-Touch Maintenance Guide

## 🎯 Philosophy: Set It and Forget It

This setup is designed for **minimal maintenance overhead**. Once configured, it runs itself.

## 🤖 What's Automated

### ✅ Automatic Image Builds
- **Trigger**: Push to `main` branch
- **Output**: New Docker image in GitHub Container Registry
- **Time**: ~5-10 minutes after push
- **Action Required**: None

### ✅ Automatic Deployments
- **Method**: Users pull latest image with `./update.sh`
- **Frequency**: On-demand or scheduled
- **Rollback**: Previous image tags available
- **Action Required**: None

### ✅ Health Monitoring
- **Docker health checks**: Every 30 seconds
- **Auto-restart**: On failure
- **Service management**: systemd handles startup/shutdown
- **Action Required**: None

## 📅 Maintenance Schedule

### Daily: Nothing ✨
- System monitors itself
- Health checks ensure uptime
- Auto-restart handles temporary issues

### Weekly: Nothing ✨
- Log rotation handled by Docker
- Temporary files auto-cleaned
- No manual intervention needed

### Monthly: Optional Check (2 minutes)
```bash
# Quick health check
curl http://localhost:5000/health

# Check disk usage
df -h

# View recent logs if curious
docker-compose logs --tail=50
```

### Quarterly: Security Updates (5 minutes)
```bash
# Update base system (optional)
apt update && apt upgrade -y

# Images auto-update with your code pushes
# No manual Docker image management needed
```

## 🚀 User Update Process (Self-Service)

Users can update their deployment with one command:
```bash
cd /opt/shortscreator && ./update.sh
```

This script automatically:
1. Pulls latest image
2. Restarts service
3. Verifies health
4. Reports status

## 🔄 Developer Workflow (You)

### Making Changes
```bash
# 1. Make code changes
# 2. Commit and push to main
git add .
git commit -m "Add new feature"
git push origin main

# 3. That's it! GitHub Actions builds and publishes automatically
```

### Versioning (Optional)
```bash
# Create a release tag for major versions
git tag v1.0.0
git push origin v1.0.0

# This creates both :latest and :v1.0.0 images
```

## 🆘 Troubleshooting (Rare)

### Issue: Service Won't Start
**Frequency**: Rare (usually after major system updates)

```bash
# Check what's wrong
systemctl status shortscreator
docker-compose logs

# Fix: Restart Docker service
systemctl restart docker
systemctl restart shortscreator
```

### Issue: Image Pull Fails
**Frequency**: Very rare (GitHub outage)

**Solution**: Script automatically falls back to build mode
```bash
# Manual fallback if needed
cd /opt/shortscreator
docker-compose build
docker-compose up -d
```

### Issue: Disk Space Full
**Frequency**: Depends on usage

```bash
# Clean up old Docker images (safe)
docker system prune -f

# Clean up old temp files
rm -rf /opt/shortscreator/data/*
```

## 📊 Monitoring (Optional)

### Simple Health Dashboard
Create a basic monitoring script:
```bash
#!/bin/bash
# /opt/shortscreator/health-check.sh
echo "🔍 ShortsCreator Health Check"
echo "API Status: $(curl -s http://localhost:5000/health | jq -r .status)"
echo "Container: $(docker ps --filter name=shortscreator --format 'table {{.Names}}\t{{.Status}}')"
echo "Disk Usage: $(df -h /opt/shortscreator | tail -1 | awk '{print $5}')"
```

### Optional Alerts (Advanced)
Set up a simple cron job for notifications:
```bash
# Check every hour, send email if down
0 * * * * curl -f http://localhost:5000/health || echo "ShortsCreator down" | mail -s "Alert" admin@yoursite.com
```

## 🎯 Maintenance Complexity: Near Zero

### What You Never Need to Do:
- ❌ Manual Docker image builds
- ❌ Dependency management
- ❌ Service configuration updates
- ❌ Log file rotation
- ❌ Health check setup
- ❌ Firewall configuration
- ❌ Update distribution

### What You Rarely Need to Do:
- 🔸 Check disk space (maybe quarterly)
- 🔸 Review logs (only if issues reported)
- 🔸 Update base system (standard server maintenance)

### What You Always Do:
- ✅ Push code changes (your normal development)
- ✅ GitHub Actions handles the rest automatically

## 💡 Best Practices

### Semantic Versioning
```bash
# For major releases, use tags
git tag v1.0.0  # Breaking changes
git tag v1.1.0  # New features
git tag v1.1.1  # Bug fixes
```

### Testing Before Release
```bash
# Test locally before pushing
docker build -t shortscreator-test .
docker run -p 5000:5000 shortscreator-test

# Then push to trigger auto-build
git push origin main
```

### Backup Strategy (Optional)
```bash
# Simple backup of user data
tar -czf backup-$(date +%Y%m%d).tar.gz /opt/shortscreator/uploads /opt/shortscreator/jobs
```

## 🎉 Result: 95% Hands-Off Operation

Once set up:
- **Users**: One-command installs and updates
- **You**: Just push code, everything else is automatic
- **Servers**: Self-monitoring and self-healing
- **Maintenance**: Quarterly check-ups at most

**Total monthly maintenance time: ~10 minutes**