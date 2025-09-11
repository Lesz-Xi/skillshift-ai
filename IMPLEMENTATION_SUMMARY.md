# Current Implementation Summary

## End‑to‑End Flow
- Frontend proxy `dashboard-ui-new/app/api/analyze/route.js` posts image + `ign` to backend (`/api/analyze`).
- Backend `skillshift-ai/web/app.py` fast path uses `EnhancedDataCollector.analyze_screenshot_with_session(...)`, then escalates to Ultimate Parsing if data is sparse.
- Core parsing lives under `dashboard-ui-new/core/` (symlinked as `skillshift-ai/core`), with OCR, row parsing, hero DB, and optional YOLO fallbacks.

## Key Enhancements (this pass)
- Hero canonicalization + role resolution
  - Added `canonicalize_name()` and `get_role_for_hero()` in `core/hero_database.py`.
  - Role now derives from the canonical DB hero with safe heuristics as fallback.
- Row‑specific hero detection hook
  - In `EnhancedDataCollector._parse_player_row_enhanced`, when falling back to direct row extraction, run `RowSpecificHeroDetector.detect_hero_in_player_row(...)` to avoid cross‑row misreads.
- GPM fallback
  - In `web/app.py` fast path, compute GPM from `gold / match_duration` when direct GPM is missing.
- Safer role inference
  - Changed `_infer_role` to exact‑name checks (avoids substring collisions like “Hilda” within “Mathilda”).
- Optional YOLO import
  - YOLO service is loaded lazily to keep OCR‑only runs stable.

## Current Validation (local)
- Command
  - `curl -s -X POST 'http://localhost:8000/api/analyze?ign=Diary%20of%20dolls' -F 'file=@Trial-Image/IMG_1767.PNG'`
- Observed output (fast path)
  - hero: Edith (expected: Mathilda)
  - role: fighter (expected: support)
  - kda: 0/1/0 (expected from scoreboard: 9/2/12)
  - gpm: 0 (gold not captured → no fallback calc)
- Interpretation
  - IGN row anchoring succeeds intermittently; hero still mis‑IDs in this sample before row‑specific detector engages (because base row parser returned a hero). We will promote row‑specific detector to validate/override hero even when a hero is already found.

## Files Touched
- `skillshift-ai/web/app.py` — canonical hero usage, role alignment, GPM fallback.
- `skillshift-ai/dashboard-ui-new/core/hero_database.py` — canonicalization, robust role lookup, safer `_infer_role`.
- `skillshift-ai/dashboard-ui-new/core/enhanced_data_collector.py` — direct row extraction + row‑specific hero detector, lazy YOLO import.

## Next Steps (short list)
- Always run row‑specific hero validation and override on mismatch/low confidence.
- Harden KDA extraction with column‑anchor alignment and IGN‑proximal search.
- Improve gold extraction on scoreboard (use YOLO ROI for gold box when OCR low).
- Add tests for: canonicalization, role lookup, GPM fallback, row‑specific override.
- Re‑run the two provided images and verify: hero=Mathilda, role=support, KDA=9/2/12, GPM computed from gold/duration.
