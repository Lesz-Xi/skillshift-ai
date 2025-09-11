#!/bin/bash

# MLBB Coach AI - Docker Compose Deployment Script
# This script deploys the microservices architecture using Docker Compose

set -e

echo "🚀 MLBB Coach AI - Microservices Deployment (Docker Compose)"
echo "=============================================================="

# Configuration
COMPOSE_DIR="$(dirname "$0")/../compose"
ENV_FILE="$COMPOSE_DIR/.env"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Environment file not found. Creating from template..."
    cp "$COMPOSE_DIR/env.example" "$ENV_FILE"
    echo "📝 Please edit $ENV_FILE with your configuration values"
    echo "   Especially set your OPENAI_API_KEY"
    read -p "Press Enter to continue after editing the environment file..."
fi

# Change to compose directory
cd "$COMPOSE_DIR"

echo "🔧 Building Docker images..."
docker-compose build --parallel

echo "🏗️  Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 30

# Health check
echo "🔍 Checking service health..."
services=("redis" "ocr-service" "detection-service" "analysis-service" "api-gateway")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose ps "$service" | grep -q "healthy\|Up"; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is not healthy"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo ""
    echo "🎉 All services are healthy!"
    echo ""
    echo "📊 Service URLs:"
    echo "   API Gateway: http://localhost:8000"
    echo "   OCR Service: http://localhost:8001"
    echo "   Detection Service: http://localhost:8002"
    echo "   Analysis Service: http://localhost:8003"
    echo "   Frontend: http://localhost:3000"
    echo "   Prometheus: http://localhost:9090"
    echo "   Grafana: http://localhost:3001 (admin/admin)"
    echo ""
    echo "🔧 Management commands:"
    echo "   View logs: docker-compose logs -f [service-name]"
    echo "   Stop all: docker-compose down"
    echo "   Restart: docker-compose restart [service-name]"
    echo "   Scale service: docker-compose up -d --scale [service-name]=3"
else
    echo ""
    echo "⚠️  Some services are not healthy. Check logs with:"
    echo "   docker-compose logs [service-name]"
    exit 1
fi
