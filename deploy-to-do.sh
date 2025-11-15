#!/bin/bash
set -e

echo "🚀 ShortsCreator - Digital Ocean One-Click Deploy Script"
echo "======================================================="

# Update system
echo "📦 Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create app directory
APP_DIR="/opt/shortscreator"
echo "📁 Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Download application files from GitHub (you'll need to update this URL)
echo "⬇️  Downloading application files..."
# Replace with your actual GitHub repository URL
GITHUB_REPO="https://github.com/jdportugal/VideoEditorAPI"
git clone $GITHUB_REPO .

# Create environment file with default settings
cat > .env << EOF
FLASK_ENV=production
FLASK_APP=app.py
PYTHONPATH=/app
# Add any other environment variables here
EOF

# Set up directory permissions
echo "🔐 Setting up permissions..."
mkdir -p temp uploads jobs static logs
chmod 755 temp uploads jobs static logs

# Create systemd service for auto-start
echo "⚙️  Setting up systemd service..."
cat > /etc/systemd/system/shortscreator.service << EOF
[Unit]
Description=ShortsCreator Video Processing API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl daemon-reload
systemctl enable shortscreator.service

# Start the application
echo "🎬 Starting ShortsCreator API..."
docker-compose up -d

# Configure firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    ufw allow 5000/tcp
    ufw allow ssh
    echo "y" | ufw enable
fi

# Get server IP
SERVER_IP=$(curl -s http://checkip.amazonaws.com || echo "localhost")

echo ""
echo "✅ ShortsCreator API deployed successfully!"
echo "========================================"
echo "🌐 API URL: http://$SERVER_IP:5000"
echo "🔍 Health Check: http://$SERVER_IP:5000/health"
echo "📝 Logs: docker-compose logs -f video-editor-api"
echo "🛑 Stop: systemctl stop shortscreator"
echo "🔄 Restart: systemctl restart shortscreator"
echo ""
echo "📚 API Endpoints:"
echo "  POST /add-subtitles    - Add subtitles to video"
echo "  POST /split-video      - Split video by time"
echo "  POST /join-videos      - Join multiple videos"
echo "  POST /add-music        - Add background music"
echo "  GET  /job-status/<id>  - Check job status"
echo ""
echo "🎉 Ready to process videos!"