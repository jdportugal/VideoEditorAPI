#!/bin/bash

# ShortsCreator ngrok Setup Script

set -e

echo "🌍 Setting up ngrok for ShortsCreator API..."

# Check if Docker container is running
if ! docker ps | grep -q shortscreator; then
    echo "❌ Docker container not running. Start it first with:"
    echo "   docker-compose up -d"
    exit 1
fi

# Check if API is responding locally
echo "🔍 Checking local API..."
if ! curl -s http://localhost:5000/health > /dev/null; then
    echo "❌ Local API not responding on port 5000"
    exit 1
fi

echo "✅ Local API is healthy"

# Stop any existing ngrok processes
echo "🛑 Stopping existing ngrok processes..."
pkill -f ngrok 2>/dev/null || true
sleep 2

# Start ngrok
echo "🚀 Starting ngrok tunnel..."
ngrok http 5000 > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get tunnel information
echo "📋 Getting tunnel information..."
TUNNEL_INFO=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)

if echo "$TUNNEL_INFO" | grep -q '"public_url"'; then
    PUBLIC_URL=$(echo "$TUNNEL_INFO" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['tunnels']:
    print(data['tunnels'][0]['public_url'])
")
    
    echo ""
    echo "🎉 ngrok tunnel successfully created!"
    echo "=================================="
    echo "🌐 Public URL: $PUBLIC_URL"
    echo "🏠 Local URL:  http://localhost:5000"
    echo "📊 Dashboard:  http://localhost:4040"
    echo ""
    echo "📋 API Endpoints:"
    echo "  Health:       $PUBLIC_URL/health"
    echo "  Add Subtitles: $PUBLIC_URL/add-subtitles"
    echo "  Split Video:   $PUBLIC_URL/split-video"
    echo "  Join Videos:   $PUBLIC_URL/join-videos"
    echo "  Add Music:     $PUBLIC_URL/add-music"
    echo ""
    echo "🧪 Test your API:"
    echo "  curl $PUBLIC_URL/health"
    echo ""
    echo "ℹ️  Press Ctrl+C to stop ngrok"
    
    # Test the public URL
    echo "🔍 Testing public URL..."
    if curl -s "$PUBLIC_URL/health" | grep -q "healthy"; then
        echo "✅ Public API is responding correctly!"
    else
        echo "⚠️  Public URL may need verification (ngrok free tier)"
    fi
    
else
    echo "❌ Failed to get ngrok tunnel information"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

# Keep script running
echo ""
echo "🔄 Tunnel is active. Press Ctrl+C to stop."
wait $NGROK_PID