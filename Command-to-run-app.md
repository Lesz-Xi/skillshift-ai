# MLBB Coach AI - Unified Setup & Runbook

This consolidates virtualenv usage and clarifies health checks and API schema contracts.

## One-Command Startup (Recommended)

NEW: python -m uvicorn web.app:app --host 0.0.0.0 --port 8000 --reload

BEST: FASTAPI_USE_GUNICORN=1 FASTAPI_WORKERS=2 FASTAPI_TIMEOUT=180 FRONTEND_PORT=3000 bash -c 'cd skillshift-ai && ./start_services.sh'

Manual:
Backend (multi-worker): cd skillshift-ai && source venv/bin/activate && gunicorn web.app:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 180 --graceful-timeout 30 --keep-alive 5
Frontend: cd skillshift-ai/dashboard-ui-new && PORT=3000 npm run dev

```bash
cd skillshift-ai && ./start_services.sh
```

Starts FastAPI on port 8000 and Next.js on port 3000 with health checks.

## Environment Setup (Backend + Frontend)

```bash
# 1) Backend setup
cd skillshift-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2) Backend environment variables
cp .env.example .env  # edit values as needed

# 3) Frontend setup
cd dashboard-ui-new
npm install
cp .env.example .env.local  # edit SKILLSHIFT_AI_URL as needed
```

Notes:

- Use only this virtualenv: `skillshift-ai/venv` (avoid extra venvs in repo root).
- FastAPI expects backend `.env` in `skillshift-ai/.env`. Next.js expects `.env.local` in `dashboard-ui-new/`.

## Development Workflow

```bash
# Terminal A – Backend
cd skillshift-ai && source venv/bin/activate
python3 -m uvicorn web.app:app --reload --port 8000

# Terminal B – Frontend
cd skillshift-ai/dashboard-ui-new
# Force a stable port (defaults to 3000)
PORT=3000 npm run dev
```

## Health Checks (Tightened)

```bash
# Prefer isolated health (never blocks)
curl -s http://localhost:8000/api/health-isolated | python3 -m json.tool

# Standard health (lightweight)
curl -s http://localhost:8000/api/health | python3 -m json.tool

# Basic fallback
curl -s http://localhost:8000/health | python3 -m json.tool

# Frontend health proxy
curl -s http://localhost:3000/api/health | python3 -m json.tool
```

Expected backend response (api/health):

```json
{
  "status": "healthy",
  "hero_database_size": 0,
  "available_roles": [],
  "version": "2.0.0",
  "timestamp": 1737000000.0
}
```

Expected isolated health (api/health-isolated):

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T20:30:00Z",
  "version": "2.0.0",
  "uptime": "running",
  "response_time_ms": 1
}
```

## Minimal Analysis Contract (Backend → Frontend)

The dashboard proxy expects a superset of these fields from backend analysis endpoints:

- Core: `statistical_feedback` (array), `mental_feedback` (string)
- Parsed data: `parsed_data.hero`, `parsed_data.kda`, `parsed_data.damage`, `parsed_data.gpm`, `parsed_data.match_duration`, `parsed_data.rank`
- Confidence: one of `confidence_scores.overall_confidence`, `overall_confidence`, or `diagnostics.confidence_score` (normalized in proxy)
- Diagnostics (optional): `parsing_warnings`, `ultimate_analysis.processing_time`, `ultimate_analysis.improvement_roadmap`

## Port Management & Troubleshooting

```bash
# Free ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Backend docs
curl http://localhost:8000/docs

# Verbose backend
python3 -m uvicorn web.app:app --reload --port 8000 --log-level debug

# Frontend recovery
cd skillshift-ai/dashboard-ui-new && rm -rf node_modules package-lock.json && npm install
```

## Production Commands

```bash
# Gunicorn + Uvicorn workers (recommended when health timeouts occur during heavy analysis)
cd skillshift-ai && source venv/bin/activate
gunicorn web.app:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Build frontend
cd skillshift-ai/dashboard-ui-new && npm run build && npm run start
```

## Keep Health Responsive During Heavy Analysis

If `/api/health` or `/api/health-isolated` time out while an analysis is running, the backend may be running a single worker with a CPU-bound request. Use multiple workers and raise the worker timeout beyond your worst-case analysis time:

```bash
# Option 1: One-command script with gunicorn
cd skillshift-ai
FASTAPI_USE_GUNICORN=1 FASTAPI_WORKERS=2 FASTAPI_TIMEOUT=180 FRONTEND_PORT=3000 ./start_services.sh

# Option 2: Manually run gunicorn in one terminal and Next.js in another
gunicorn web.app:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 180 --graceful-timeout 30 --keep-alive 5
# In another terminal
cd dashboard-ui-new && PORT=3000 npm run dev
```

## Diagnostics Prompt

1. Specific issue, 2) Context, 3) Logs (FastAPI/Next.js), 4) Environment (Python/Node/OS/Browser).

Checklist:

- [ ] Virtual environment activated (`skillshift-ai/venv`)
- [ ] `.env` and `.env.local` configured
- [ ] Health endpoints responding (`/api/health-isolated` preferred)
- [ ] Ports free (8000, 3000, 5173)
- [ ] Dependencies installed (Python + npm)
- [ ] Frontend proxy configured to backend URL
