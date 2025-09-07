# MLBB Coach AI - Application Setup & Commands

## Install requirements
cd skillshift-ai; ./venv/bin/activate; 


## Checl if the installation is completed
cd skillshift-ai && pip list | grep numpy

## Quick Start Commands

```bash
# Backend (FastAPI)
source venv/bin/activate 
python3 -m uvicorn web.app:app --reload --port 8000

# Frontend (React + Vite)
npm run dev
```

## Prerequisites

```bash
# Python environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

# Node.js dependencies
npm install
```

## Environment Setup

```bash
# Create virtual environment
cd skillshift-ai
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (if using frontend)
npm install
```

## Development Workflow

```bash
# 1. Activate Python environment
source venv/bin/activate

# 2. Start backend with auto-reload
python3 -m uvicorn web.app:app --reload --port 8000

# 3. Start frontend (in new terminal)
npm run dev

# 4. Test API endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"player_name": "TestPlayer", "hero": "Chou", "kda": "5/2/8"}'
```

## Port Management & Troubleshooting

### Kill Processes on Ports

```bash
# Kill process on port 8000 (Backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173 (Frontend - Vite default)
lsof -ti:5173 | xargs kill -9

# Kill process on port 3000 (Alternative frontend port)
lsof -ti:3000 | xargs kill -9

# Find what's running on a port
lsof -i :8000
```

### Common Issues & Solutions

#### Backend Issues

```bash
# Check if FastAPI is accessible
curl http://localhost:8000/docs

# Check Python path and imports
python3 -c "import sys; print(sys.path)"
python3 -c "from web.app import app; print('Import successful')"

# Run with verbose logging
python3 -m uvicorn web.app:app --reload --port 8000 --log-level debug
```

#### Frontend Issues

```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check Vite config
npm run build --verbose
```

#### OCR & Dependencies

```bash
# Verify EasyOCR installation
python3 -c "import easyocr; print('EasyOCR OK')"

# Test image processing
python3 -c "from PIL import Image; print('PIL OK')"

# Check OpenCV
python3 -c "import cv2; print('OpenCV OK')"
```

## Testing Commands

### API Testing

```bash
# Test analysis endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "player_name": "Lesz XVII",
    "hero": "Chou",
    "kda": "5/2/8",
    "damage": 67551,
    "gpm": 450,
    "match_duration": 12.5
  }'

# Test health endpoint
curl http://localhost:8000/health

# Test with file upload
curl -X POST http://localhost:8000/upload \
  -F "file=@screenshot.png" \
  -F "player_name=TestPlayer"
```

### Unit Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test
python3 -m pytest tests/test_data_collector.py -v

# Run with coverage
python3 -m pytest tests/ --cov=core --cov-report=html
```

## Performance Monitoring

```bash
# Monitor backend performance
python3 test_performance_analyzer.py

# Monitor API response times
time curl -X POST http://localhost:8000/analyze -H "Content-Type: application/json" -d '{"player_name":"Test","hero":"Chou"}'

# Check memory usage
python3 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

## Production Deployment

```bash
# Production server (Gunicorn)
gunicorn web.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Build frontend for production
npm run build

# Serve static files
python3 -m http.server 3000 --directory dist
```

## Debugging Commands

```bash
# Debug screenshot analysis
python3 debug_user_screenshots.py

# Debug hero detection
python3 debug_hero_detection.py

# Debug counter pick system
python3 debug_counter_pick_assistant.py

# Generate validation report
python3 test_comprehensive_validation.py
```

## 🚀 AUTOMATED STARTUP & RECOVERY

### One-Command Startup

```bash
# Start both backend and frontend with health checking
cd skillshift-ai && ./start_services.sh
```

### Backend Connection Issue Recovery

```bash
# Diagnose backend connection problems
cd skillshift-ai && ./diagnose_backend.sh

# Quick fix for "Backend Connection Issue" alerts:
killall -9 python3 node  # Kill all processes
cd skillshift-ai && ./start_services.sh  # Restart with health checks
```

### Frontend "Analyze Buttons Not Working" Fix

The frontend disables analyze buttons when it can't reach the backend health endpoint.
Fixed in latest version:

- Added `/api/health` endpoint (frontend expects this)
- Fallback to `/health` endpoint
- Auto-reconnection logic
- Manual "Reconnect Backend" button in UI

## BEST ENGINEERING PROMPT

I'm having this problem right now. Please do a full comprehensive step-by-step analysis of my codebase and identify the root cause:

1. **Describe the specific issue** (error messages, unexpected behavior)
2. **Provide context** (what you were trying to do, recent changes)
3. **Include relevant logs** (FastAPI logs, browser console, Python traceback)
4. **Specify environment** (Python version, OS, browser)

### Quick Diagnostic Checklist

- [ ] Virtual environment activated?
- [ ] All dependencies installed?
- [ ] Ports available (8000, 5173)?
- [ ] Required files present in `data/` directory?
- [ ] OCR libraries working?
- [ ] API endpoints responding?
- [ ] Frontend build successful?
- [ ] **NEW**: Backend health endpoint responding? (`curl http://localhost:8000/api/health`)
- [ ] **NEW**: Frontend showing "Backend Connection Issue"? (Use reconnect button)
