# Detection Service - YOLO and Computer Vision Detection
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for CV
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy detection-specific requirements
COPY infrastructure/microservices/docker/detection-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy detection-related code
COPY core/services/detection_service.py ./core/services/
COPY core/services/yolo_detection_service.py ./core/services/
COPY core/services/base_service.py ./core/services/
COPY core/premium_hero_detector.py ./core/
COPY core/trophy_medal_detector_v3.py ./core/
COPY core/yolo_fallback.py ./core/
COPY core/cache/ ./core/cache/
COPY core/observability/ ./core/observability/
COPY core/__init__.py ./core/
COPY core/services/__init__.py ./core/services/
COPY models/ ./models/
COPY infrastructure/microservices/services/detection_service.py ./

# Download YOLO model if not present
RUN if [ ! -f "./models/yolov8n.pt" ]; then \
        wget -O ./models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt; \
    fi

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=detection-service
ENV SERVICE_PORT=8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Run the detection service
CMD ["python", "detection_service.py"]
