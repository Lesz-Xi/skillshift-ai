# Context

- App: SkillShift AI, screenshot analysis for MLBB.
- Two images from same match & player:
- `IMG_1767.PNG` = KDA view (should read: KDA 9/2/12, Gold 12374, Duration 21:12).
- `IMG_1768.PNG` = Damage view (should read: HeroD 107100 (31%), TurretD 2854 (9%), Taken 54444 (11%), TF% 70%).
- Current JSON (frontend Network preview) shows: `kda="0/1/0"`, `gpm=0`, `damage="N/A"`, `match_duration=10`, `warnings=[exact IGN not found, no numeric data]`.

## Symptoms to fix

1. OCR pipeline throws: "truth value of an array… ambiguous" → OCR skipped.
2. Player row not reliably anchored; fallback fills zeros.
3. Duration not parsed; GPM shows 0 (should be gold / minutes).
4. No hero coaching for "Kagura"; use generic mage rules if hero-specific missing.
5. Normalize backend → proxy → UI data shape (flat fields).

## Make these changes (in order)

### 1. Stop the OCR crash

In OCR/preprocessing code (likely `core/enhanced_data_collector.py` and any helpers), replace boolean checks on arrays:

```python
# BAD
if enhanced: ...
if blurred: ...
if thresh: ...

# GOOD
if enhanced is not None:
    ...
if blurred is not None and getattr(blurred, "size", 0):
    ...
if thresh is not None and (np.asarray(thresh).size > 0):
    ...
```

Also avoid `if arr:` anywhere a NumPy array may flow; use `.any()` or explicit size checks.

### 2. Robust row anchoring for "my player"

- Use YOLO detections you already trained: `hero_ally`, `player_name`, `mvp_badge`, `kda_display`, `gold`, `match_duration`.
- Determine `row_y` by:
  - First, fuzzy-match IGN ("Diary of dolls") against OCR of all `player_name` crops (lowercased; strip punctuation; ratio ≥ 0.75).
  - If not found, use MVP badge y-center as anchor (only if badge within ally team region).
  - For that `row_y`, select the nearest ROI among detections for `kda_display`, `gold`, and in damage view the four bars/values.
- Persist anchors to logs (drawn debug images) so we can visually verify.

### 3. Numeric OCR with allowlists

- For KDA: crop ROI; OCR with digits and `/` only.
  - Example (EasyOCR): post-filter `re.findall(r"\d+/\d+/\d+", text)`.
- For Gold: digits only; then compute GPM = `round(gold / minutes)`.
- For Duration: from the top banner (mm:ss); fallback to damage screen's "Duration" too.
- For damage view values & percents:
  - Numbers: `r"\d{1,3}(?:,\d{3})*"` → int
  - Percents: `r"(\d{1,3})\s*%"`
- Add small preprocessing: grayscale → CLAHE → adaptive threshold; invert if light-on-dark.

### 4. Data normalization (single flat schema to UI)

Ensure the analyze endpoint returns flat fields:

```json
{
  "confidence_score": 0.54,
  "kda": "9/2/12",
  "gold": 12374,
  "gpm": 583,
  "match_duration": 1272,        // seconds
  "hero": "Kagura",
  "role": "mage",
  "hero_damage": 107100,
  "hero_damage_pct": 31,
  "turret_damage": 2854,
  "turret_damage_pct": 9,
  "damage_taken": 54444,
  "damage_taken_pct": 11,
  "teamfight_participation_pct": 70,
  "warnings": [...],
  "diagnostics": { "anchors": "...", "ocr_debug": "..." }
}
```

Keep existing nested objects, but always mirror these flat keys.

### 5. Coaching fallback

- Add `coaching/rules/roles/mage_generic.json` (or similar) and map any unknown hero with `role=mage` to this rule.
- Wire mapping: `hero_rules.get(hero_name, role_rules.get(role, generic_rules))`.

### 6. Acceptance tests (must pass with the two images)

- `IMG_1767.PNG` → `kda="9/2/12"`, `gold≈12374`, `duration≈21:12`, `gpm≈580±30`, `hero="Kagura"`, `role="mage"`.
- `IMG_1768.PNG` → `hero_damage=107100±1%`, `turret_damage=2854±1%`, `damage_taken=54444±1%`, `teamfight_participation=70±1%`.
- `overall_confidence >= 0.50` and `data_completeness >= 0.70`.
- Frontend shows coaching text (mage generic) instead of "No coaching logic".

## Files likely touched

- `core/enhanced_data_collector.py` (preprocess + parallel OCR)
- `core/screenshot_analyzer.py` (type detection, duration parse)
- `core/services/yolo_detection_service.py` (ROI selection helpers)
- `core/premium_hero_detector.py` (IGN fuzzy match)
- `coaching/` (rules + hero→role mapping)
- `app/api/analyze/route.js` (normalize to flat schema)

## Dev notes

- Save debug crops to `temp/debug/<timestamp>/…` any time OCR parsing occurs.
- Add a unit test that feeds both images and asserts the acceptance criteria.
- Keep the frontend timeout ≥ 180s; process screenshots sequentially.
