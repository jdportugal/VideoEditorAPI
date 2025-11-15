#!/bin/bash

# ShortsCreator One-Click Installer for Digital Ocean
# Usage: curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Get system information
ARCH=$(uname -m)
OS=$(lsb_release -si 2>/dev/null || echo "Unknown")
VERSION=$(lsb_release -sr 2>/dev/null || echo "Unknown")

print_status "System detected: $OS $VERSION ($ARCH)"

# Check minimum requirements
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -lt 3 ]; then
    print_warning "System has only ${TOTAL_MEM}GB RAM. Minimum 4GB recommended."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo
echo "🎬 ShortsCreator - One-Click Installer"
echo "====================================="
echo "This will install:"
echo "  • Docker & Docker Compose"
echo "  • ShortsCreator API server"
echo "  • Automatic startup service"
echo "  • Firewall configuration"
echo

read -p "Continue with installation? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    exit 0
fi

# Update system
print_status "Updating system packages..."
apt-get update -y > /dev/null 2>&1

# Install required packages
print_status "Installing required packages..."
apt-get install -y curl wget git ufw > /dev/null 2>&1

# Install Docker
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh > /dev/null 2>&1
    rm get-docker.sh
    systemctl enable docker > /dev/null 2>&1
    systemctl start docker > /dev/null 2>&1
    print_success "Docker installed successfully"
else
    print_success "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose already installed"
fi

# Set up application directory
APP_DIR="/opt/shortscreator"
print_status "Setting up application directory: $APP_DIR"
rm -rf $APP_DIR
mkdir -p $APP_DIR
cd $APP_DIR

# Clone repository
print_status "Downloading ShortsCreator application..."
# Replace this URL with your actual GitHub repository
REPO_URL="https://github.com/jdportugal/VideoEditorAPI.git"
git clone $REPO_URL . > /dev/null 2>&1

# Create environment file
print_status "Setting up configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Create required directories
mkdir -p temp uploads jobs static logs
chmod 755 temp uploads jobs static logs

# Pull and build Docker images
print_status "Building Docker images (this may take a few minutes)..."
docker-compose pull > /dev/null 2>&1 || true
docker-compose build > /dev/null 2>&1

# Create systemd service
print_status "Setting up auto-start service..."
cat > /etc/systemd/system/shortscreator.service << EOF
[Unit]
Description=ShortsCreator Video Processing API
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
TimeoutStartSec=120
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable shortscreator.service > /dev/null 2>&1

# Configure firewall
print_status "Configuring firewall..."
ufw --force enable > /dev/null 2>&1
ufw allow ssh > /dev/null 2>&1
ufw allow 5000/tcp > /dev/null 2>&1

# Start the application
print_status "Starting ShortsCreator API..."
systemctl start shortscreator.service

# Wait for service to be ready
print_status "Waiting for service to start..."
sleep 30

# Check if service is running
if systemctl is-active --quiet shortscreator.service; then
    print_success "Service started successfully"
else
    print_error "Service failed to start"
    echo "Check logs with: journalctl -u shortscreator.service"
    exit 1
fi

# Get server IP
SERVER_IP=$(curl -s http://checkip.amazonaws.com 2>/dev/null || curl -s http://ipinfo.io/ip 2>/dev/null || echo "YOUR_SERVER_IP")

# Test health endpoint
print_status "Testing API health..."
sleep 10
if curl -f -s "http://localhost:8080/health" > /dev/null; then
    print_success "API is responding correctly"
else
    print_warning "API health check failed - service may still be starting"
fi

echo
print_success "🎉 ShortsCreator installed successfully!"
echo
echo "📋 Installation Summary:"
echo "======================="
echo "🌐 API URL: http://$SERVER_IP:8080"
echo "🔍 Health Check: http://$SERVER_IP:8080/health"
echo "📁 App Directory: $APP_DIR"
echo
echo "🛠️  Management Commands:"
echo "  Status:  systemctl status shortscreator"
echo "  Stop:    systemctl stop shortscreator"
echo "  Start:   systemctl start shortscreator"
echo "  Restart: systemctl restart shortscreator"
echo "  Logs:    docker-compose logs -f"
echo
echo "📚 API Endpoints:"
echo "  POST /add-subtitles    - Add subtitles with karaoke effect"
echo "  POST /split-video      - Split video by time range"
echo "  POST /join-videos      - Join multiple videos"
echo "  POST /add-music        - Add background music"
echo "  GET  /job-status/<id>  - Check processing status"
echo "  GET  /download/<id>    - Download processed video"
echo
echo "🔧 Example Usage:"
echo "curl -X POST http://$SERVER_IP:8080/add-subtitles \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"url\": \"https://example.com/video.mp4\"}'"
echo
echo "🎬 Happy video processing!"