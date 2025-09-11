# MLBB Coach – Fix OCR Metrics & Coaching Output

## Problem summary (use this context)

- Backend logs show Parallel OCR crash: The truth value of an array with more than one element is ambiguous → metrics default to zeros.
- Row lock fails: IGN not matched → crops aren't taken from the player row.
- Anchors not found on both KDA and Damage views → header OCR unreliable.
- We do detect hero and MVP (and we can override hero), but performance metrics are 0/N/A, causing generic or wrong coaching.
- Tight 30s per image and parallel OCR increase failures.

## Goal

Robustly extract metrics for the player row by (1) fixing NumPy truthiness, (2) locking the row with fuzzy matching, (3) cropping by column percentages (no header OCR), (4) strict OCR regex/allowlists, (5) computing GPM, (6) softening timeouts / sequential OCR. Then return a flat result shape to the UI.

---

## Files you will likely touch

- `core/enhanced_data_collector.py`
- `core/screenshot_analyzer.py`
- `core/row_parsing.py` (create if missing)
- `core/ocr_utils.py` (add helpers if missing)
- (Optional) `core/ai_coach_v2.py` – ensure hero-specific rules trigger once metrics are present.
- Frontend already normalizes shapes, but confirm `app/api/analyze/route.js` still outputs flat fields: `{hero, role, kda, gpm, damage, hero_damage, turret_damage, damage_taken, teamfight_participation, confidence_score}`.

---

## Implement these changes

### 1) Kill the NumPy truthiness crash (root cause)

Search the backend for any `if roi:` or `if arr:` checks on NumPy arrays and replace.

```python
# BAD
if roi:
    ...

# GOOD
def has_img(x):
    return x is not None and hasattr(x, "size") and int(getattr(x, "size", 0)) > 0

if has_img(roi):
    ...
```

Also guard returns from any crop function:

```python
if isinstance(roi, np.ndarray) and roi.size == 0:
    return None
```

### 2) Lock the correct player row (fuzzy by IGN, fallback MVP)

Create `core/row_parsing.py` with:

```python
from rapidfuzz import process, fuzz

def pick_row(ign, rows):
    # rows: [{'name','bbox','side','badges'}]
    if ign:
        names = [r['name'] for r in rows]
        hit = process.extractOne(ign, names, scorer=fuzz.token_set_ratio)
        if hit and hit[1] >= 85:
            return rows[names.index(hit[0])]
    # fallback: ally MVP row
    for r in rows:
        if r.get('side') == 'ally' and 'MVP' in r.get('badges', []):
            return r
    # last fallback: first ally row
    return next((r for r in rows if r.get('side') == 'ally'), None)
```

**Speed**: add dependency `python-Levenshtein` to remove slow warning.

### 3) Use column percentages for crops (no header OCR)

Once you have the row bbox `(x,y,w,h)`:

**KDA screen (IMG_1767)**: (tune if needed; start with these)

```python
COL_KDA   = (0.28, 0.43)  # of row width
COL_GOLD  = (0.44, 0.53)
COL_ROLE  = (0.11, 0.20)  # optional
```

**Damage screen (IMG_1768; hero is Kagura in your sample)**:
Left team columns (blue side) are consistent; for the locked row:

```python
COL_DMG_HERO  = (0.03, 0.16)
COL_DMG_TUR   = (0.18, 0.30)
COL_DMG_TAKEN = (0.32, 0.45)
COL_TF_PART   = (0.47, 0.61)
```

Crop each by percent of the row bbox, not the full image.

### 4) OCR with strict allowlists + regex (don't coerce to zero)

Add helpers in `core/ocr_utils.py`:

```python
import re

KDA_RX = re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{1,2})\b')

def read_kda(text):
    m = KDA_RX.search(text.replace(' ', ''))
    if not m: return None
    return tuple(map(int, m.groups()))

def only_digits(s):
    return ''.join(ch for ch in s if ch.isdigit())

def read_int(text):
    ds = only_digits(text)
    return int(ds) if ds else None
```

OCR calls should pass allowlists:

- KDA crops: whitelist `0123456789/`
- Gold/damage: whitelist `0123456789`

If a field can't be read, return `None` (UI shows N/A), not 0.

### 5) Compute GPM

Duration is in header "Duration 21:12" → minutes = 21 + 12/60 = 21.2.

```python
def compute_gpm(gold, minutes):
    if not gold or not minutes or minutes <= 0: return None
    return round(gold / minutes, 1)
```

### 6) Tame timing: sequential OCR + relaxed cap

- In `enhanced_data_collector`, process sequentially for now (disable parallel OCR on MLBB images).
- Increase per-image budget to 60–90s (you already increased FE timeout; align BE).
- Keep the YOLO fallback thresholds, but don't trigger trophy-only success—ensure metrics stage must run.

### 7) Output a flat result shape

Ensure the final payload includes:

```json
{
  "hero": "Kagura",
  "role": "mage",
  "kda": "9/2/12",
  "gold": 12374,
  "gpm": 583.7,          // example using duration
  "hero_damage": 107100,
  "turret_damage": 2854,
  "damage_taken": 54444,
  "teamfight_participation": 70,  // %
  "confidence_score": 0.54,       // 0..1
  "warnings": [...],
  ...
}
```

### 8) Coaching rule sanity

When hero is known and metrics exist, emit hero-specific tips (Kagura):

- Low fight presence (<60%): mention umbrella poke + rotation timing
- High deaths (>7): emphasize Rasho Umbrella Flee usage
- Low turret dmg for mage: advise wave clear then rotate

(You already showed generic rules working; this ensures they become specific once metrics are present.)

## Acceptance tests (use your two files)

Artifacts: `/mnt/data/IMG_1767.jpeg` and `/mnt/data/IMG_1768.jpeg` (frontend loads as PNG).

### 1. KDA view (IMG_1767)

- Detected hero == "Kagura", role == "mage".
- `kda == "9/2/12"`.
- `gold == 12374` (±10 if OCR spacing).
- `gpm != None` and > 500 given duration ~21.2 min and team gold context.
- Coaching shows at least one Kagura-specific tip (no generic "0.0" warnings).

### 2. Damage view (IMG_1768)

- `hero_damage == 107100`
- `turret_damage == 2854`
- `damage_taken == 54444`
- `teamfight_participation == 70`
- Coaching references fight presence/damage patterns, not zeros.

### 3. General requirements

- No fallback zeros when OCR fails → fields become null and UI shows N/A.
- No crash: Log does not contain "truth value of an array … ambiguous".

---

## Dev notes / setup

- Add dependency: `python-Levenshtein` (speeds fuzzy).
- Prefer `rapidfuzz` over `fuzzywuzzy` if available.
- Keep YOLO model as is; this task is OCR/cropping.

---

## Nice-to-have (if time permits)

- Cache row bbox per session (IGN + layout hash) to skip re-detection on the second image.
- Add tiny unit tests for `read_kda`, `read_int`, `compute_gpm`.

## Commands (example)

```bash
# install speedup for fuzzy matching
pip install python-Levenshtein rapidfuzz

# run backend
./start_services.sh

# watch logs during two-image run to confirm:
# - no NumPy truthiness error
# - row picked by IGN or MVP
# - flat payload contains correct values
```
