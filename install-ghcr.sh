#!/bin/bash
# ShortsCreator - Maintenance-Simple Install with GHCR
# Usage: curl -fsSL https://raw.githubusercontent.com/jdportugal/VideoEditorAPI/main/install-ghcr.sh | sudo bash

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

echo
echo "🎬 ShortsCreator - Simple Install (GHCR)"
echo "======================================"
echo "✅ Pre-built images for faster deployment"
echo "✅ Automatic updates available"
echo "✅ Minimal maintenance required"
echo

# Quick system check
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -lt 3 ]; then
    print_warning "System has only ${TOTAL_MEM}GB RAM. 4GB+ recommended for video processing."
fi

# Install Docker if needed (minimal)
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com | sh > /dev/null 2>&1
    systemctl enable docker && systemctl start docker
    print_success "Docker installed"
else
    print_success "Docker already available"
fi

# Install Docker Compose if needed
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
fi

# Setup application directory
APP_DIR="/opt/shortscreator"
print_status "Setting up application in $APP_DIR"
mkdir -p $APP_DIR && cd $APP_DIR

# Create simple docker-compose.yml using GHCR image
print_status "Creating deployment configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  shortscreator:
    image: ghcr.io/jdportugal/videoeditorapi:latest
    container_name: shortscreator
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./data:/app/temp
      - ./uploads:/app/uploads
      - ./jobs:/app/jobs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
EOF

# Create data directories
mkdir -p data uploads jobs logs
chmod 755 data uploads jobs logs

# Create simple environment file
cat > .env << 'EOF'
# ShortsCreator Configuration
FLASK_ENV=production
COMPOSE_PROJECT_NAME=shortscreator
EOF

# Create update script for easy maintenance
cat > update.sh << 'EOF'
#!/bin/bash
echo "🔄 Updating ShortsCreator..."
docker-compose pull
docker-compose up -d
echo "✅ Update complete!"
EOF
chmod +x update.sh

# Create systemd service (simple)
print_status "Setting up auto-start service..."
cat > /etc/systemd/system/shortscreator.service << EOF
[Unit]
Description=ShortsCreator API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable shortscreator.service

# Configure minimal firewall
print_status "Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw --force enable > /dev/null 2>&1
    ufw allow ssh > /dev/null 2>&1
    ufw allow 5000/tcp > /dev/null 2>&1
fi

# Start the service
print_status "Starting ShortsCreator..."
print_status "Pulling pre-built image (this may take a moment)..."

# Try GHCR first, fallback if needed
if docker pull ghcr.io/jdportugal/videoeditorapi:latest > /dev/null 2>&1; then
    print_success "Using pre-built image from GitHub"
else
    print_warning "Pre-built image not available, falling back to build"
    # Fallback to build approach
    cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  shortscreator:
    build: 
      context: https://github.com/jdportugal/VideoEditorAPI.git
    container_name: shortscreator
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./data:/app/temp
      - ./uploads:/app/uploads
      - ./jobs:/app/jobs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
EOF
fi

# Start the service
systemctl start shortscreator.service

# Wait and verify
print_status "Waiting for service to start..."
sleep 45

# Get server IP
SERVER_IP=$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo "YOUR_SERVER_IP")

# Verify health
if curl -f -s "http://localhost:5000/health" > /dev/null; then
    print_success "🎉 ShortsCreator is running successfully!"
else
    print_warning "Service may still be starting up..."
fi

echo
echo "📋 Installation Complete!"
echo "========================"
echo "🌐 API URL: http://$SERVER_IP:5000"
echo "🔍 Health: http://$SERVER_IP:5000/health"
echo
echo "🛠️  Simple Management:"
echo "  Update:  cd $APP_DIR && ./update.sh"
echo "  Stop:    systemctl stop shortscreator"
echo "  Start:   systemctl start shortscreator"
echo "  Logs:    docker-compose logs -f"
echo
echo "🎬 Ready for video processing!"
echo "✨ Zero maintenance - just use it!"