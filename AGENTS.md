# Repository Guidelines

## Project Structure & Module Organization
- `skillshift-ai/` — main app
  - Backend: `web/` (FastAPI `web.app:app`), `rules/`, `data/`
  - Frontend: `dashboard-ui-new/` (Next.js)
- Tests: `skillshift-ai/tests/` and top‑level `skillshift-ai/test_*.py` files
- Artifacts: `runs/`, `temp/`, `yolo_dataset/`
- Agent scripts: `Skillshift/scripts/` (e.g., `setup-plan.sh`, `update-agent-context.sh`)

## Build, Test, and Development Commands
- Backend setup: `cd skillshift-ai && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cp .env.example .env`
- Frontend setup: `cd skillshift-ai/dashboard-ui-new && npm install && cp .env.example .env.local`
- Run locally (both services): `cd skillshift-ai && ./start_services.sh` (FastAPI on 8000, Next.js on 3000)
- Dev mode: `uvicorn web.app:app --reload --port 8000` and `PORT=3000 npm run dev` (from `dashboard-ui-new`)
- Tests: Python `cd skillshift-ai && pytest -q`; UI `cd skillshift-ai/dashboard-ui-new && npm test`; Lint UI `npm run lint`

## Coding Style & Naming Conventions
- Python: 4‑space indent; type hints encouraged. Functions/vars `snake_case`, classes `PascalCase`, modules `snake_case.py`.
- Keep API endpoints in `web/`; put pure business logic under `core/`.
- Frontend: follow `.eslintrc.cjs`. Components `PascalCase` in `components/` or `app/`; prefer small, typed props; colocate styles.
- Optional static typing: see `skillshift-ai/mypy.ini` (`mypy` before PRs encouraged).

## Testing Guidelines
- Framework: `pytest`; name tests `test_*.py`.
- Add unit tests for new logic and at least one integration test for new API routes.
- Place fixtures in `skillshift-ai/tests/`; reference assets in `skillshift-ai/test_screenshots/` or `data/`.
- Keep tests CPU‑bounded; gate heavy YOLO/vision cases behind small inputs.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`. Example: `feat(web): add /api/health-isolated endpoint`.
- PRs include: clear description, linked issues (e.g., `Closes #123`), UI screenshots when relevant, and steps to validate.
- Ensure `pytest` and `npm run lint` pass before merging.

## Security & Configuration Tips
- Never commit secrets. Copy from examples: `.env.example` → `.env`; `dashboard-ui-new/.env.example` → `.env.local`.
- Ensure ports 8000/3000/5173 are free; verify `/api/health` and `/api/health-isolated` before merging.

