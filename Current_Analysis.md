Current Analysis — Status, Issues, and Implementation Plan

Summary
- Services: Backend and frontend are healthy on ports 8000/3000. Health endpoints respond instantly.
- Pipeline: Hero and KDA are detected for your samples; stats‑page images yield lower completeness than scoreboard images.
- UX issue: A validation string ("Invalid match data: Field required") appeared as coaching text; role showed "tank" for Mathilda.
- Async flow: Instant endpoint returned a status URL that didn’t exist; jobs require a running Redis/RQ worker.
- Tests: A few tests block collection due to a debug script, an indentation error, and missing package init files.

Problems Observed
- Feedback validation noise: Strict Pydantic validation rejected partial match data, surfacing an error string in coaching feedback instead of advice.
- Role normalization gap: "mathilda" was labeled as tank when role should be support; simple analysis path didn’t align role from the hero DB.
- Simple endpoint latency: `/api/analyze-simple` can take ~75s on some images; scoreboard vs stats page differ in extractable signals.
- Async status mismatch: `/api/analyze-instant` returned `/api/job-status/{id}` while the real endpoint is `/api/jobs/{id}`.
- No worker: Instant job queue requires Redis + RQ worker; without it, instant returns a stub.
- Tests not green:
  - `skillshift-ai/test_debug_numpy.py` exits(1) on missing image path.
  - `skillshift-ai/test_performance_optimizations.py` has an indentation error.
  - `tests/test_chou.py` and `tests/test_franco.py` import `rules.roles.*` but the package lacks `__init__.py`.

Changes Shipped Now
- Tolerant coaching validation to prevent noisy error messages
  - File: `skillshift-ai/coach.py:72`
  - Behavior: On validation failure, coerce partial inputs (parse KDA string, compute GPM from gold+duration, set defaults) and retry before emitting an error message.
- Role + GPM normalization in fast path
  - File: `skillshift-ai/web/app.py:1984`
  - Behavior: Align hero to canonical DB name and set `role` from DB; derive `gold_per_min` when missing.
- Instant status URL fixed
  - File: `skillshift-ai/web/app.py:1705`
  - Behavior: `/api/analyze-instant` now returns `status_endpoint: /api/jobs/{job_id}`.

Impact
- Coaching panel: No more "Invalid match data" line when fields are missing; users see actionable advice.
- Performance metrics: Role for Mathilda resolves to support; `gold_per_min` appears when gold+duration exist.
- Instant analysis: Status link matches the backend job polling route.

Recommended Implementation (Next)
1) Keep health responsive during heavy analysis
   - Run multi‑worker: `FASTAPI_USE_GUNICORN=1 FASTAPI_WORKERS=2 FASTAPI_TIMEOUT=180 bash -c 'cd skillshift-ai && ./start_services.sh'`
   - Rationale: Prevents health/API timeouts while a CPU‑bound task is running.

2) Enable async jobs end‑to‑end (optional but recommended)
   - Start Redis locally and an RQ worker bound to the "analysis" queue.
   - Poll `/api/jobs/{job_id}` (UI fallback already implemented).

3) Tests: unblock collection
   - Add `__init__.py` to `skillshift-ai/rules` and `skillshift-ai/rules/roles` to fix imports.
   - Fix the indent at `skillshift-ai/test_performance_optimizations.py:151`.
   - Exclude or guard `skillshift-ai/test_debug_numpy.py` so it doesn’t exit during pytest.

4) Parser mode‑awareness
   - Auto‑detect scoreboard vs stats page; prefer scoreboard path for complete KDA/GPM/role.
   - For stats pages, surface partial metrics clearly and avoid misleading confidence.

5) Debug tooling (quality of life)
   - Small API to dump first N OCR lines and key ROIs for a given image (for targeted troubleshooting).

Validation Steps
- Frontend upload (stats page: `IMG_1768.PNG`)
  - Expect: hero=Mathilda, role=support, KDA built from components; no coaching error strings.
- Simple endpoint (scoreboard preferred)
  - `curl -s -X POST 'http://localhost:8000/api/analyze-simple?ign=<IGN>' -F 'file=@<IMG_PATH>'`
- Instant endpoint
  - Observe `status_endpoint: /api/jobs/{job_id}`; poll when worker is active.
- Health
  - `curl -s http://localhost:8000/api/health-isolated`
  - `curl -s http://localhost:8000/api/health`

Operational Notes
- IGN matters: ensure the IGN sent from the UI matches OCR text for robust row anchoring; set `ALLOW_DEFAULT_IGN=true` only in development.
- Image type: Scoreboard images provide the richest signals; stats pages have less consistent KDA/GPM.

Backlog (Optional Enhancements)
- Confidence gating: Cap confidence when critical fields are missing to avoid inflated values.
- Caching: Add a lightweight file/Redis cache keyed by `md5(file)+IGN` for instant hits on re‑uploads.
- Worker script: Add a repo script to launch `rq worker analysis` from the venv.

