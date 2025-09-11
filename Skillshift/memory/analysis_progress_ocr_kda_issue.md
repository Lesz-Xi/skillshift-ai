# Session Memory — Screenshot Parsing & OCR/KDA Issue

Date: 2025-09-09

## Summary
- UI shows “Analysis Complete, Confidence: 0%” with KDA N/A or 0/0/0 and hero Unknown.
- Network Preview sometimes stalls on `/api/analyze` and health calls. Frontend previously defaulted to an incorrect IGN.
- OCR was running but parsers received little/no text due to an input-type bug and weak row anchoring.

## Confirmed Root Causes
- EasyOCR input bug: `_parallel_ocr_analysis` passed a dict (from preprocessing) into `readtext`, starving OCR.
- IGN mismatch/missing: Frontend defaulted to `Lesz XVII`; screenshot IGN differs (e.g., “HVD Diary of dolls”), so row parsing could not anchor.
- Sparse row parsing: earlier logic wasn’t x‑ordered and lacked robust IGN‑aware extraction and fallback.

## Fixes Implemented
- OCR hardening and dict→image fix
  - `core/enhanced_data_collector.py` → `_parallel_ocr_analysis`: select `processed_image/full_image`, coerce to `uint8`, normalize shape (BGRA→BGR/gray).
- IGN auto‑infer + stronger validation
  - `core/enhanced_data_collector.py` → `_validate_ign_enhanced`: extract potential IGNs from OCR, re‑match, choose best candidate.
- Row parsing (x‑aware, IGN‑aware K/D/A)
  - `core/data_collector.py` → `_parse_player_row`: row tolerance 50px, left→right ordering by x, prefer IGN‑aware K/D/A before spatial fallback; better gold/damage extraction.
  - `core/enhanced_data_collector.py` → `_parse_player_row_enhanced`: fallback to direct row extraction using bbox Y when base parser returns empty.
- Frontend guard
  - `dashboard-ui-new/app/api/analyze/route.js`: IGN required (or set `ALLOW_DEFAULT_IGN=true`), prevents parsing against wrong default.
- Test added
  - `tests/test_row_parsing_kda.py`: synthetic row → asserts K/D/A=9/2/12 and gold≥1000.

## How to Validate
- Backend dev: `cd skillshift-ai && source venv/bin/activate && uvicorn web.app:app --reload --port 8000`
- Provide IGN: set `ALLOW_DEFAULT_IGN=true` and `DEFAULT_IGN="HVD Diary of dolls"` (dev) or pass `ign` from UI.
- Fast path: `POST /api/analyze-instant?ign=...` with the screenshot. Check logs for:
  - `OCR baseline count` > 0; `Parsed KDA (IGN‑aware/spatial)` messages.
- Unit test: `cd skillshift-ai && pytest -q tests/test_row_parsing_kda.py`.

## Current Status / Next Steps
- If confidence remains 0%:
  - Verify IGN is sent; ensure it appears in OCR lines.
  - Try multi‑worker backend: `FASTAPI_USE_GUNICORN=1 FASTAPI_WORKERS=2 FASTAPI_TIMEOUT=180 ./start_services.sh`.
  - Confirm screenshot is a post‑match scoreboard (not the stats page).
- Optional improvements:
  - Add a debug API to dump first 10 OCR lines + top YOLO ROIs for a given image.
  - Tighten frontend to show a clear message when `kda` is N/A (instead of “complete”).
