# OCR Service - Specialized OCR Processing
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy OCR-specific requirements
COPY infrastructure/microservices/docker/ocr-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only OCR-related code
COPY core/enhanced_ocr_processor.py ./core/
COPY core/services/ocr_service.py ./core/services/
COPY core/services/base_service.py ./core/services/
COPY core/cache/ ./core/cache/
COPY core/observability/ ./core/observability/
COPY core/__init__.py ./core/
COPY core/services/__init__.py ./core/services/
COPY infrastructure/microservices/services/ocr_service.py ./

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=ocr-service
ENV SERVICE_PORT=8001
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run the OCR service
CMD ["python", "ocr_service.py"]
