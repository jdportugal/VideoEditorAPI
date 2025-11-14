#!/bin/bash

# Digital Ocean deployment script for ShortsCreator Video Editor API

set -e

echo "🚀 Starting Digital Ocean deployment..."

# Configuration
APP_NAME="shorts-creator"
DOCKER_IMAGE="$APP_NAME:latest"
CONTAINER_NAME="$APP_NAME-container"

# Build Docker image
echo "📦 Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Stop and remove existing container if it exists
echo "🔄 Stopping existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Run new container
echo "🆕 Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p 5000:5000 \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/jobs:/app/jobs \
  -v $(pwd)/static:/app/static \
  $DOCKER_IMAGE

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 10

# Check container status
if docker ps | grep -q $CONTAINER_NAME; then
    echo "✅ Deployment successful!"
    echo "🌐 API is running at: http://localhost:5000"
    echo "📊 Health check: http://localhost:5000/health"
    
    # Show container logs
    echo "📋 Recent logs:"
    docker logs --tail 20 $CONTAINER_NAME
else
    echo "❌ Deployment failed!"
    echo "📋 Container logs:"
    docker logs $CONTAINER_NAME
    exit 1
fi

echo "🎉 Deployment complete!"