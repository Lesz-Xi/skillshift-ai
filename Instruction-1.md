# Problem (concise)

- We upload two views of the same match.
- Backend treats them as independent analyses, so hero may differ, KDA/GPM = N/A on damage view, and damage metrics = N/A on KDA view.
- UI then shows incomplete/mismatched metrics and wrong hero (OCR misread).

## Goal

Detect screen type (KDA vs Damage), anchor the same player row, extract the correct metrics from each view, and merge into a single, flat result for the match.

## Implement step-by-step

### 1. Screen-type classifier (fast & deterministic)

- In Python `core/screen_type.py` (new):
- If headers include `Hero Damage | Turret Damage | Damage Taken | Teamfight Participation` → `screen_type="damage"`.
- If columns show skull/coins/GPM and K/D/A tokens `\d+/\d+/\d+` → `screen_type="kda"`.
- Fall back to template/keyword check.

### 2. Match session ID (pairing key)

- Extract BattleID (bottom-left) via OCR with whitelist `[0-9]` and label it `battle_id`.
- If BattleID missing, compute image perceptual hash + IGN + minute rounded timestamp → `session_key`.
- Use `battle_id || session_key` to merge multiple uploads into one "match session".

### 3. Player-row anchoring (shared for both screens)

- Locate player row by IGN OCR within the left name column OR YOLO anchor (heart icon) on that row.
- Keep `row_bbox` and reuse to crop metrics consistently.

### 4. Hero identity (single source of truth)

- Prefer portrait recognition from `row_bbox` (template/feature match) over text OCR.
- Cache hero → role via `data/hero_role_map.json`.
- Store `hero_confidence` and avoid re-detecting on the other view (reuse).

### 5. Metrics per screen type

#### KDA view:

- Parse K/D/A from the row `((\d+)\s*/\s*(\d+)\s*/\s*(\d+))`.
- Extract GPM (if present on layout) or gold; set missing fields to null (don't block).
- Pick up MVP/medals if badges exist.

#### Damage view:

- Parse `hero_damage`, `turret_damage`, `damage_taken`, `teamfight_participation` from progress-bar clusters inside `row_bbox`.
- Use YOLO `damage_stats` box to tighten ROI before OCR.

### 6. Fuse results (server-side)

- Maintain a small in-memory session cache keyed by `battle_id` (or `session_key`):

```python
session = {
    battle_id, ign, hero, role, hero_confidence,
    kda, gpm, gold,
    hero_damage, turret_damage, damage_taken, teamfight_participation,
    sources: {kda_view: true/false, dmg_view: true/false}
}
```

- When second view arrives, merge non-null fields and compute a single `confidence_score` (weighted: portrait match, OCR quality, YOLO hit-rate, both-views bonus).

### 7. Return a flat payload (for UI)

```json
{
  "confidence_score": 0.78,
  "battle_id": "858921223897853062",
  "hero": "Kagura",
  "role": "mage",
  "kda": "9/2/12",
  "gpm": 724,
  "gold": 12374,
  "hero_damage": 107100,
  "turret_damage": 2854,
  "damage_taken": 54444,
  "teamfight_participation": 0.7,
  "mvp": true,
  "diagnostics": { "screen_types_seen": ["kda", "damage"], "row_anchor": "IGN" }
}
```

### 8. Frontend expectation (keep simple)

- No schema change needed — we already flatten at the route.
- If only one view is available, show partial metrics; when the second arrives, update in place.

## Acceptance tests

- For the two provided screenshots (same match):
- Hero = Kagura, Role = mage (no "Mathilda" misread).
- KDA parsed on KDA view; Damage metrics parsed on Damage view; fused result shows both.
- Confidence increases (≥ 0.6) when both screens are present.
- Coaching block renders role-level tips even if hero-specific tips are missing.

## Notes

- OCR hero-name is brittle; portrait recognition is mandatory here.
- Use YOLO boxes (`hero_*`, `player_name`, `kda_display`, `damage_stats`) to tighten ROIs before OCR.
- Cache hero templates/features in memory to keep CPU latency < 20s.

## Commit message

```
feat(analysis): pair KDA+Damage views via battle_id; robust row anchoring + portrait hero; fuse metrics into single flat result
```
