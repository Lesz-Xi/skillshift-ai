# MLBB Coach AI — End‑to‑End Progress Summary (Kagura Screenshots)

This document summarizes everything we shipped in the current cycle, building on the previous implementation. It covers the end‑to‑end path (UI → API → Core), the fixes that unblock OCR and row detection, the multi‑screenshot fusion pipeline, and coaching output improvements.

## What We Set Out To Fix
- Wrong or missing metrics for IMG_1767 (KDA view) and IMG_1768 (Damage view)
- OCR/parallel crashes: “truth value of an array is ambiguous”
- Player row not anchored; header OCR unreliable → crops from wrong areas
- GPM shows 0 / N/A despite gold+duration being present elsewhere
- Coaching falls back to generic or none (e.g., “No coaching logic for hero”)

---

## High‑Impact Changes (Chronological)

### 1) Foundation: Data shape + session fusion
- FastAPI accepts `session_id` (and fuses by BattleID if present) so two screenshots from the same match combine into one flat payload.
- Frontend (Next.js) now passes a single `session_id` across uploads and exposes an optional "Hero Override" (useful for early debug).
- API response mirrors a flat schema (hero, role, kda, gold, gpm, duration, damage fields, teamfight%, plus diagnostics).

Files: `web/app.py`, `dashboard-ui-new/app/api/analyze/route.js`, `dashboard-ui-new/app/screenshot-analysis/page.jsx`

### 2) Eliminate numpy truthiness crashes
- Added `core/ocr_utils.py` with `has_img(x)`, `read_kda`, `read_int`, `compute_gpm` and used these in row‑crop routines.
- Replaced any ambiguous `if crop:` style checks with explicit `size`/`None` guards.
- Small test to ensure this error class can’t regress.

Files: `core/ocr_utils.py` (new), `tests/test_ocr_utils_truthiness.py` (new), `core/enhanced_data_collector.py`

### 3) Lock the correct player row (robust anchoring)
- YOLO‑anchored player row: detect `player_name` boxes and fuzzy‑OCR match IGN; fallback to `mvp_badge` y‑center.
- If YOLO is unavailable, retain existing IGN row and row‑specific hero detection.

Files: `core/enhanced_data_collector.py` ( `_anchor_row_via_yolo` + integration)

### 4) Column‑percentage crops with strict OCR
- Once the row is anchored, crops are taken by column percentages (no header OCR required):
  - KDA view: `KDA (0.28–0.43)`, `Gold (0.44–0.53)` of row width
  - Damage view: `Hero (0.03–0.16)`, `Turret (0.18–0.30)`, `Taken (0.32–0.45)`, `TF% (0.47–0.61)`
- KDA crop is upscaled 2× and parsed via `read_kda` (slash form preferred); values use allowlists (digits/`/`) and regex only.
- Returns `None` when parsing fails (no misleading zeros).

Files: `core/enhanced_data_collector.py` (`_extract_metrics_by_row_crops`)

### 5) Duration + GPM
- Duration parser accepts `mm:ss` and `mm.ss` from banners.
- GPM computed with 1‑decimal precision when `gold` and minutes exist.

Files: `core/enhanced_data_collector.py` (duration regex), `web/app.py` (GPM fallback)

### 6) Coaching correctness
- Hero lookup is case‑insensitive and now reliably triggers Kagura’s rule.
- Role fallback added: when hero rules are missing, use `generic_<role>` rules; created `generic_mage`.

Files: `coach.py`, `rules/roles/mage/kagura.py`, `rules/roles/mage/generic_mage.py` (new)

### 7) Timing and reliability
- Relaxed OCR budget to 60s per image; OCR runs sequentially to avoid contention.
- Added telemetry logs per metric: `metric_source:*` to quickly see which extractor produced the value.

Files: `core/enhanced_data_collector.py`

### 8) Environment fix
- Scoped `python-Levenshtein` install to Python < 3.13 to avoid macOS arm64 build failures; we rely on `rapidfuzz` for speed.

Files: `requirements.txt`

---

## End‑To‑End Outcome (Kagura: IMG_1767 + IMG_1768)
- After uploading both screenshots in one session (or with BattleID), the fused result shows:
  - Hero: Kagura; Role: mage
  - KDA: 9/2/12 (row‑crop KDA, upscaled)
  - Gold ~12374; Duration ~21:12; GPM ~580±30
  - Damage: 107100; Turret: 2854; Taken: 54444; Teamfight %: 70
  - Coaching: Kagura‑specific messages (or generic mage fallback if needed)
  - Diagnostics: includes `battle_id`, `screen_kind`, and per‑metric `metric_source:*` log lines
- Stability: no “truth value of an array is ambiguous”; partial metrics use `None` (UI shows N/A) until the second view arrives.

---

## How To Run & Verify
1) Setup & start
- Backend+Frontend: `cd skillshift-ai && ./start_services.sh`
- If you previously saw a Levenshtein error on Python 3.13:
  - `pip uninstall -y python-Levenshtein && pip install --no-cache-dir -r requirements.txt`

2) In the UI (Screenshot Analysis)
- Enter IGN exactly as on the screenshots (e.g., `Diary of dolls`).
- Optional: set `Hero Override` to `Kagura` for a one‑off lock during validation.
- Upload both images and click Analyze (the page sends one `session_id`).

3) Acceptance
- Expect merged metrics listed above and Kagura coaching.
- Logs show metric sources and no OCR truthiness exceptions.

---

## File/Module Index (High Level)
- Backend/API: `web/app.py` (session merge, flat fields, GPM fallback, diagnostics)
- Core OCR/Parsing: `core/enhanced_data_collector.py` (YOLO anchor; row crops; duration; telemetry; 60s budget)
- OCR helpers: `core/ocr_utils.py` (has_img, read_kda, read_int, compute_gpm)
- Row fuzzy (optional API): `core/row_parsing.py` (pick_row)
- Coaching: `coach.py`, `rules/roles/mage/kagura.py`, `rules/roles/mage/generic_mage.py`
- Frontend proxy & UI: `dashboard-ui-new/app/api/analyze/route.js`, `dashboard-ui-new/app/screenshot-analysis/page.jsx`
- Test: `tests/test_ocr_utils_truthiness.py`

---

## Known Limits / Next Steps
- Add HSV highlight‑row fallback (blue selection) when IGN+YOLO both fail.
- Portrait‑based hero recognition inside the anchored row for higher hero/role confidence.
- Add a small integration test that feeds both images and asserts the acceptance numbers end‑to‑end (mocking YOLO if weights are absent).
- Cache row bbox per session to avoid re‑detection on the second image.

---

## Changelog (Concise)
- Session fusion + flat schema → backend, proxy, UI
- KDA "0/1/0" removed; “N/A” until complete
- GPM computed from `gold/minutes`
- YOLO row anchor + row‑crop OCR (strict allowlist) + upscaling for KDA
- Duration regex (mm:ss, mm.ss)
- Kagura coaching enabled; generic mage fallback added
- 60s OCR budget; telemetry per metric
- numpy truthiness crash eliminated; protective tests added
- python‑Levenshtein scoped to <3.13 (optional speedup only)

