#!/bin/bash

# MLBB Coach AI - Service Startup Script
# This script starts both backend and frontend services with proper health checking

echo "🚀 Starting MLBB Coach AI Services..."
echo "=================================="

# Kill existing processes on ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "📋 Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Start backend
echo "🖥️  Starting FastAPI backend..."
# Allow opting into multi-worker mode to keep health endpoints responsive during heavy analysis
if [ "${FASTAPI_USE_GUNICORN:-0}" = "1" ]; then
  if command -v gunicorn >/dev/null 2>&1; then
    WORKERS=${FASTAPI_WORKERS:-2}
    TIMEOUT=${FASTAPI_TIMEOUT:-180}
    GRACEFUL=${FASTAPI_GRACEFUL_TIMEOUT:-30}
    KEEPALIVE=${FASTAPI_KEEPALIVE:-5}
    echo "🔧 Using gunicorn with ${WORKERS} workers"
    gunicorn web.app:app \
      -w ${WORKERS} \
      -k uvicorn.workers.UvicornWorker \
      --bind 0.0.0.0:8000 \
      --timeout ${TIMEOUT} \
      --graceful-timeout ${GRACEFUL} \
      --keep-alive ${KEEPALIVE} &
  else
    echo "⚠️  gunicorn not found in this venv. Falling back to uvicorn."
    echo "💡 Tip: pip install gunicorn (or add to requirements) to enable multi-worker mode."
    python3 -m uvicorn web.app:app --reload --port 8000 &
  fi
else
  echo "🔧 Using uvicorn --reload (single worker)"
  python3 -m uvicorn web.app:app --reload --port 8000 &
fi
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Test backend health
echo "🔍 Testing backend health..."
for i in {1..10}; do
    # Prefer isolated health (never blocks)
    if curl -s --max-time 1 http://localhost:8000/api/health-isolated > /dev/null; then
        echo "✅ Backend is healthy! Isolated health endpoint responding."
        break
    elif curl -s --max-time 2 http://localhost:8000/api/health > /dev/null; then
        echo "✅ Backend is healthy! Health endpoint responding."
        break
    elif curl -s --max-time 2 http://localhost:8000/health > /dev/null; then
        echo "✅ Backend is healthy! Fallback health endpoint responding."
        break
    else
        echo "⏳ Backend not ready yet... ($i/10)"
        sleep 2
    fi

    if [ $i -eq 10 ]; then
        echo "❌ Backend health check failed after ~20 seconds"
        echo "🔍 Checking backend processes..."
        ps aux | grep uvicorn
        exit 1
    fi
done

# Start frontend
echo "🌐 Starting Next.js frontend..."
cd dashboard-ui-new
npm install --silent
# Allow overriding the frontend port; default to 3000 for consistency
FRONTEND_PORT=${FRONTEND_PORT:-3000}
PORT=${FRONTEND_PORT} npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Services Started Successfully!"
echo "=================================="
echo "🖥️  Backend:  http://localhost:8000"
echo "🌐 Frontend: http://localhost:${FRONTEND_PORT}"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Health Endpoints:"
echo "   - http://localhost:8000/api/health-isolated"
echo "   - http://localhost:8000/api/health"
echo "   - http://localhost:8000/health"
echo "   Frontend Health Proxy: http://localhost:${FRONTEND_PORT}/api/health"
echo ""
echo "🛑 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📊 Service Status:"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""

# Monitor services
echo "🔍 Monitoring services (Ctrl+C to stop)..."
wait 
