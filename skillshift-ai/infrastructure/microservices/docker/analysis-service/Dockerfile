# Analysis Service - AI Coaching and Performance Analysis
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy analysis-specific requirements
COPY infrastructure/microservices/docker/analysis-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy analysis-related code
COPY core/services/analysis_service.py ./core/services/
COPY core/services/behavioral_modeling_service.py ./core/services/
COPY core/services/tactical_coaching_service.py ./core/services/
COPY core/services/base_service.py ./core/services/
COPY core/advanced_performance_analyzer.py ./core/
COPY core/ai_coach_v2.py ./core/
COPY core/behavioral_modeling.py ./core/
COPY core/mental_coach.py ./core/
COPY core/cache/ ./core/cache/
COPY core/observability/ ./core/observability/
COPY core/__init__.py ./core/
COPY core/services/__init__.py ./core/services/
COPY config/ ./config/
COPY rules/ ./rules/
COPY infrastructure/microservices/services/analysis_service.py ./

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=analysis-service
ENV SERVICE_PORT=8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Expose port
EXPOSE 8003

# Run the analysis service
CMD ["python", "analysis_service.py"]
