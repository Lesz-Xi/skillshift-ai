Codex Context Pack — High-ROI Template

Purpose: Copy this file, fill the placeholders, and paste the filled block into your next request. It gives me exactly what I need to ship fast, correct fixes and features in this repo.

1) Objective
- Goal: <one-line outcome>
- Acceptance:
  - <bullet of verifiable result>
  - <tests/endpoint response to prove it>

2) Repo Scope
- Files to touch only: <paths like `skillshift-ai/web/app.py:…`, `dashboard-ui-new/app/...`>
- Don’t touch: <paths/modules to avoid>

3) Reproduction
- Command(s):
  - Backend dev: `cd skillshift-ai && source venv/bin/activate && uvicorn web.app:app --reload --port 8000`
  - Frontend dev: `cd skillshift-ai/dashboard-ui-new && PORT=3000 npm run dev`
  - One-liner: `FASTAPI_USE_GUNICORN=1 FASTAPI_WORKERS=2 FASTAPI_TIMEOUT=180 FRONTEND_PORT=3000 bash -c 'cd skillshift-ai && ./start_services.sh'`
- Curl(s):
  - Simple: `curl -s -X POST 'http://localhost:8000/api/analyze-simple?ign=<IGN>' -F 'file=@<IMG_PATH>'`
  - Instant: `curl -s -X POST 'http://localhost:8000/api/analyze-instant?ign=<IGN>' -F 'file=@<IMG_PATH>'`
  - Jobs: `curl -s -X POST 'http://localhost:8000/api/jobs?ign=<IGN>' -F 'file=@<IMG_PATH>'`
           `curl -s 'http://localhost:8000/api/jobs/<JOB_ID>'`
- Expected vs Actual:
  - Expected: <short JSON snippet or metric>
  - Actual: <short JSON snippet or error/trace>
- Minimal logs (top 5 relevant lines):
  - Backend: <paste small excerpt>
  - Frontend: <paste small excerpt>

4) Environment
- OS: <macOS/Linux/Windows + version>
- Python: <e.g., 3.13.5>
- Node: <e.g., 20.x>
- Sandbox/Approvals: <danger-full-access / never>
- Network: <enabled/restricted>
- Ports in use: <8000/3000/5173>
- venv: `skillshift-ai/venv`
- Env files:
  - Backend: `skillshift-ai/.env`
  - Frontend: `skillshift-ai/dashboard-ui-new/.env.local`

5) Inputs & Context
- Image: `<absolute-or-repo-relative path>`, Type: <scoreboard|stats page>
- IGN used: `<player name>` (must match OCR text closely)
- Endpoint chosen: </api/analyze-simple | /api/analyze-instant | /api/analyze>
- Feature flags / env vars: `USE_FAST_ANALYSIS=<true|false>`, `ALLOW_DEFAULT_IGN=<true|false>`

6) Contracts (as used by the dashboard)
- Core fields expected: statistical_feedback[], mental_feedback (string)
- Performance: hero, kda, damage/hero_damage, gpm/gold_per_min, match_duration, rank, role
- Confidence: overall_confidence (0–100), warnings[]
- Backend health: `/api/health`, `/api/health-isolated` should return status healthy

7) Constraints & Targets
- Latency target: <e.g., <15s simple, <60s analyze>
- Worker mode: <gunicorn workers=N, timeout=>
- Memory/CPU considerations: <notes>

8) Validation Plan
- Unit tests: `cd skillshift-ai && venv/bin/python -m pytest -q -k '<pattern>'`
- Full tests: `cd skillshift-ai && pytest -q`
- UI lint: `cd skillshift-ai/dashboard-ui-new && npm run lint`
- Health checks:
  - `curl -s http://localhost:8000/api/health-isolated | python3 -m json.tool`
  - `curl -s http://localhost:8000/api/health | python3 -m json.tool`
  - `curl -s http://localhost:3000/api/health | python3 -m json.tool`
- Acceptance demo: <exact curl + expected JSON keys/values>

9) Risks & Rollback
- Potential side effects: <e.g., affects feedback formatting only>
- Rollback: <files to revert / flags to disable>

10) Next Steps Ask
- After implementation, please: <run tests|build UI|add docs|open PR>


Mini-Templates

Bug Fix
- Goal: <fix X>
- Repro: <command + expected vs actual>
- Scope: <files to touch>
- Accept: <response/time/tests>
- Notes: <edge cases>

Feature
- Goal: <add Y>
- Contract: <request/response shapes>
- Accept: <UI/endpoint behavior + tests>
- Flags: <env/feature flags>
- Perf: <targets>


Repo-Specific Tips (SkillShift AI)
- Always send IGN or set `ALLOW_DEFAULT_IGN=true` in frontend to avoid row-anchor misses.
- Multi-worker backend keeps health responsive under load:
  - `FASTAPI_USE_GUNICORN=1 FASTAPI_WORKERS=2 FASTAPI_TIMEOUT=180 ./start_services.sh`
- Stats page images yield less structured data than scoreboard; prefer scoreboard for full fields (GPM, KDA, role).
- Instant mode returns a job link; poll `/api/jobs/{id}` if Redis/RQ is running. Otherwise prefer `/api/analyze-simple` for synchronous flow.


Quick Utilities
- Free ports: `lsof -ti:8000 | xargs kill -9 || true && lsof -ti:3000 | xargs kill -9 || true && lsof -ti:5173 | xargs kill -9 || true`
- Frontend recovery: `cd skillshift-ai/dashboard-ui-new && rm -rf node_modules package-lock.json && npm install`

