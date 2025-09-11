#!/bin/bash

# MLBB Coach AI - Docker Images Build Script
# This script builds all Docker images for the microservices

set -e

echo "🏗️  MLBB Coach AI - Building Docker Images"
echo "=========================================="

# Configuration
PROJECT_ROOT="$(dirname "$0")/../../.."
DOCKER_DIR="$(dirname "$0")/../docker"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-mlbb-coach-ai}"

echo "📁 Project root: $PROJECT_ROOT"
echo "🏷️  Image tag: $IMAGE_TAG"
echo "📦 Registry: $REGISTRY"

# Change to project root
cd "$PROJECT_ROOT"

# Build API Gateway
echo "🌐 Building API Gateway image..."
docker build -f "$DOCKER_DIR/api-gateway/Dockerfile" -t "$REGISTRY/api-gateway:$IMAGE_TAG" .

# Build OCR Service
echo "🧠 Building OCR Service image..."
docker build -f "$DOCKER_DIR/ocr-service/Dockerfile" -t "$REGISTRY/ocr-service:$IMAGE_TAG" .

# Build Detection Service
echo "🔍 Building Detection Service image..."
docker build -f "$DOCKER_DIR/detection-service/Dockerfile" -t "$REGISTRY/detection-service:$IMAGE_TAG" .

# Build Analysis Service
echo "📊 Building Analysis Service image..."
docker build -f "$DOCKER_DIR/analysis-service/Dockerfile" -t "$REGISTRY/analysis-service:$IMAGE_TAG" .

# Build Frontend (if exists)
if [ -d "dashboard-ui-new" ]; then
    echo "🎨 Building Frontend image..."
    docker build -f "$DOCKER_DIR/frontend/Dockerfile" -t "$REGISTRY/frontend:$IMAGE_TAG" dashboard-ui-new/
fi

echo ""
echo "✅ All images built successfully!"
echo ""
echo "📋 Built images:"
docker images | grep "$REGISTRY"

echo ""
echo "🚀 Next steps:"
echo "   1. Test images: docker run -p 8001:8001 $REGISTRY/ocr-service:$IMAGE_TAG"
echo "   2. Push to registry: docker push $REGISTRY/[service-name]:$IMAGE_TAG"
echo "   3. Deploy with compose: ./deploy-docker-compose.sh"
echo "   4. Deploy to K8s: ./deploy-kubernetes.sh"
