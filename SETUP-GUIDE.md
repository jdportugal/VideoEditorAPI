# 🚀 ShortsCreator - Complete GHCR Setup Guide

**Total Time: ~20 minutes**

## 📋 **Prerequisites**
- ✅ GitHub account
- ✅ Your ShortsCreator code ready
- ✅ Git installed locally

---

## **PHASE 1: GitHub Repository Setup** (5 minutes)

### Step 1: Create GitHub Repository
1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** button → **"New repository"**
3. **Repository name**: `shortscreator` (or your preferred name)
4. **Visibility**: **Public** (for free GitHub Container Registry)
5. **Initialize**: Leave unchecked (we have existing code)
6. Click **"Create repository"**

### Step 2: Connect Local Repository
```bash
# Navigate to your project directory
cd /path/to/your/ShortsCreator

# Initialize git (if not already done)
git init

# Add your GitHub repository (replace YOURUSERNAME)
git remote add origin https://github.com/YOURUSERNAME/shortscreator.git

# Verify connection
git remote -v
```

---

## **PHASE 2: Update Configuration** (10 minutes)

### Step 3: Replace Repository References
**Critical**: Replace `YOURUSERNAME` with your actual GitHub username in ALL commands below:

```bash
# Update GitHub Actions workflow
sed -i '' 's/yourusername/YOURUSERNAME/g' .github/workflows/docker-publish.yml

# Update docker-compose.yml
sed -i '' 's/yourusername/YOURUSERNAME/g' docker-compose.yml

# Update install script
sed -i '' 's/yourusername/YOURUSERNAME/g' install-ghcr.sh

# Update deploy script
sed -i '' 's/yourusername/YOURUSERNAME/g' deploy-to-do.sh

# Update documentation
sed -i '' 's/yourusername/YOURUSERNAME/g' README-GHCR.md
sed -i '' 's/yourusername/YOURUSERNAME/g' DEPLOY.md
sed -i '' 's/yourusername/YOURUSERNAME/g' README-DEPLOY.md
sed -i '' 's/yourusername/YOURUSERNAME/g' MAINTENANCE.md
```

### Step 4: Verify Updates
```bash
# Check that your username appears correctly
grep -r "YOURUSERNAME" .github/workflows/
grep "YOURUSERNAME" docker-compose.yml
```

---

## **PHASE 3: First Commit & Push** (5 minutes)

### Step 5: Add All Files
```bash
# Add all files to git
git add .

# Create initial commit
git commit -m "Initial commit - ShortsCreator with GHCR setup"

# Push to GitHub (this triggers the first build)
git push -u origin main
```

### Step 6: Monitor First Build
1. Go to your GitHub repository
2. Click **"Actions"** tab
3. You should see **"Build and Publish Docker Image"** running
4. Click on it to watch progress (takes 5-10 minutes)
5. ✅ When complete, you'll see green checkmarks

---

## **PHASE 4: Verification & Testing** (10 minutes)

### Step 7: Verify Container Registry
1. In your GitHub repository, click **"Packages"** (right side)
2. You should see **"shortscreator"** package
3. Click on it to see the published Docker image
4. Note the pull command: `docker pull ghcr.io/YOURUSERNAME/shortscreator:latest`

### Step 8: Test Local Pull
```bash
# Test pulling the image locally
docker pull ghcr.io/YOURUSERNAME/shortscreator:latest

# Verify it downloaded
docker images | grep shortscreator
```

### Step 9: Test Deployment (Optional but Recommended)
Create a test droplet and try the installer:

```bash
# On a fresh Ubuntu 20.04+ droplet
curl -fsSL https://raw.githubusercontent.com/YOURUSERNAME/shortscreator/main/install-ghcr.sh | sudo bash

# Should complete in ~30 seconds and show:
# "🎉 ShortsCreator is running successfully!"
```

---

## **PHASE 5: Documentation Updates** (5 minutes)

### Step 10: Update Main README
Create or update your main README.md:

```bash
cat > README.md << 'EOF'
# 🎬 ShortsCreator - AI Video Processing API

Transform videos with AI-generated subtitles, karaoke effects, and professional editing.

## ⚡ Quick Deploy on Digital Ocean

```bash
curl -fsSL https://raw.githubusercontent.com/YOURUSERNAME/shortscreator/main/install-ghcr.sh | sudo bash
```

**That's it!** Your API will be running at `http://your-droplet-ip:5000` in 30 seconds.

## 🎯 Features

- 🎤 **AI Subtitles** - Whisper-powered speech recognition
- 🌟 **Karaoke Effects** - Word-by-word highlighting
- ✂️ **Video Editing** - Split, join, and trim videos
- 🎵 **Audio Mixing** - Add background music with volume control
- 📊 **Job Tracking** - Real-time processing status
- 🚀 **One-Click Deploy** - Ready for Digital Ocean

## 📚 Documentation

- [🚀 Deployment Guide](DEPLOY.md)
- [🔧 Maintenance Guide](MAINTENANCE.md)
- [📖 API Documentation](API.md)

## 🛠️ API Endpoints

### Add Subtitles with Karaoke Effect
```bash
curl -X POST http://your-ip:5000/add-subtitles \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4"}'
```

### Split Video by Time
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

## 📋 System Requirements

- **CPU**: 2+ vCPUs (4+ recommended)
- **RAM**: 4GB (8GB+ for larger videos)
- **Storage**: 25GB SSD
- **OS**: Ubuntu 20.04+

## 💰 Digital Ocean Costs

| Droplet Size | Monthly Cost | Performance |
|--------------|--------------|-------------|
| s-2vcpu-4gb  | $24         | Good        |
| s-4vcpu-8gb  | $48         | Better      |
| c-4          | $80         | Best        |

## 🎉 What's Included

✅ Whisper AI for subtitle generation  
✅ MoviePy video processing  
✅ Karaoke-style highlighting  
✅ Health monitoring  
✅ Auto-restart on failure  
✅ One-command updates  

## 📞 Support

- 📖 [Documentation](https://github.com/YOURUSERNAME/shortscreator/wiki)
- 🐛 [Issues](https://github.com/YOURUSERNAME/shortscreator/issues)
- 💬 [Discussions](https://github.com/YOURUSERNAME/shortscreator/discussions)

---

⭐ **Star this repository if it helped you!**
EOF
```

### Step 11: Commit Documentation
```bash
# Add updated README
git add README.md
git commit -m "Add comprehensive README with deployment instructions"
git push origin main
```

---

## **PHASE 6: Success Verification** ✅

### Step 12: Final Checklist
- [ ] GitHub repository created and pushed
- [ ] GitHub Actions workflow completed successfully  
- [ ] Container image visible in GitHub Packages
- [ ] Can pull image: `docker pull ghcr.io/YOURUSERNAME/shortscreator:latest`
- [ ] Install script works: `curl -fsSL https://raw.githubusercontent.com/YOURUSERNAME/shortscreator/main/install-ghcr.sh`
- [ ] Documentation updated with correct URLs

### Step 13: Share Your Creation
Your one-click installer is now live at:
```
https://raw.githubusercontent.com/YOURUSERNAME/shortscreator/main/install-ghcr.sh
```

Anyone can deploy your video API with:
```bash
curl -fsSL https://raw.githubusercontent.com/YOURUSERNAME/shortscreator/main/install-ghcr.sh | sudo bash
```

---

## 🎯 **What Happens Next**

### Automatic Operations
- ✅ **Every push to main** → New Docker image built and published
- ✅ **Users run installer** → Get latest image in 30 seconds  
- ✅ **Users run `./update.sh`** → Pull latest updates instantly
- ✅ **Health monitoring** → Auto-restart on failures

### Your Maintenance
- 💡 **Code changes**: Just `git push` - everything else is automatic
- 💡 **User support**: Point them to the one-line installer
- 💡 **Updates**: Zero effort - GitHub handles everything
- 💡 **Monitoring**: Optional 10-minute quarterly health checks

---

## 🚨 **Troubleshooting Setup**

### GitHub Actions Failing?
```bash
# Check repository permissions
# Go to repository Settings → Actions → General
# Ensure "Read and write permissions" is selected
```

### Can't Pull Image?
```bash
# Check image exists
curl -s https://api.github.com/users/YOURUSERNAME/packages/container/shortscreator

# Make package public
# Go to GitHub → Your profile → Packages → shortscreator → Package settings
# Change visibility to "Public"
```

### Install Script Not Working?
```bash
# Test the raw URL works
curl https://raw.githubusercontent.com/YOURUSERNAME/shortscreator/main/install-ghcr.sh

# If 404, check file exists in repository
```

---

## 🎉 **Success!**

You now have a **maintenance-free, one-click deployment system**!

**Users get**: 30-second installs, automatic updates, bulletproof reliability  
**You get**: Zero maintenance, automatic builds, focus on features  

**Total setup time**: 20 minutes once  
**Ongoing maintenance**: ~10 minutes/month  
**User happiness**: Infinite 😄  

---

## 🚀 **Next Steps**

1. **Test thoroughly** - Deploy on a fresh droplet
2. **Share with users** - Give them the one-line installer  
3. **Develop features** - Just push code, deployment is handled
4. **Enjoy simplicity** - Set and forget! ✨