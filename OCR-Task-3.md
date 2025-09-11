# OCR Task 3: Environment and Code Structure Fixes

## Issues Identified

### 1. **Hard environment error**

- `numpy.dtype size changed… Expected 96, got 88` = a C-extension was built against a different NumPy ABI than the one currently installed
- Typical culprits: opencv-python(-headless), scikit-image, scipy, or any Cython bits you compile
- Result: your anchor-based detection path blows up; you fall back to default_region, then miss the IGN

### 2. **Soft logic gap (even if env is healthy)**

- Your IGN matching is brittle
- You're not normalizing OCR candidates enough and you're not using a robust matcher (rapidfuzz) with a sane threshold

**Let's fix both—env first, then code hardening.**

## A) Environment Fix — Realign NumPy ABI with all C-extensions (macOS arm64, py3.13)

### 1. Record & Inspect

```bash
venv/bin/python - <<'PY'
import sys, numpy as np
print("Python:", sys.version)
print("NumPy:", np.__version__)
try:
    import cv2; print("OpenCV:", cv2.__version__)
except Exception as e:
    print("OpenCV import error:", repr(e))
try:
    import skimage; print("scikit-image:", skimage.__version__)
except Exception as e:
    print("skimage import error:", repr(e))
try:
    import scipy; print("SciPy:", scipy.__version__)
except Exception as e:
    print("SciPy import error:", repr(e))
PY
```

### 2. Clean Reinstall in the Right Order (NumPy First)

**Rationale:** Anything with compiled code that depends on NumPy must be built after the exact NumPy you'll run with.

```bash
# upgrade build tooling
venv/bin/pip install -U pip setuptools wheel

# remove likely mismatched wheels
venv/bin/pip uninstall -y opencv-python opencv-python-headless scikit-image scipy pillow easyocr

# pin/upgrade NumPy FIRST (use a recent 2.x wheel compatible with py3.13)
venv/bin/pip install "numpy>=2.1,<3"

# reinstall binary deps against that NumPy
# prefer headless to avoid Cocoa video backends for servers
venv/bin/pip install "opencv-python-headless>=4.9" "scipy>=1.12" "scikit-image>=0.22" "pillow>=10.3"

# EasyOCR (pure python) + deps
venv/bin/pip install "easyocr>=1.7.1"

# fast fuzzy matching (also kills your warning)
venv/bin/pip install rapidfuzz python-Levenshtein

# sanity check
venv/bin/python - <<'PY'
import numpy, cv2, skimage, scipy
print("OK:", numpy.__version__, cv2.__version__, skimage.__version__, scipy.__version__)
PY
```

### 3. If You Still See the dtype Error

You've got a cached wheel mismatch. Nuke build caches and force fresh wheels:

```bash
rm -rf ~/.cache/pip
venv/bin/pip install --no-cache-dir --force-reinstall \
  "numpy>=2.1,<3" \
  "opencv-python-headless>=4.9" "scipy>=1.12" "scikit-image>=0.22" "pillow>=10.3" "easyocr>=1.7.1"
```

## B) Code Hardening — Make IGN Matching and Detection Resilient

### 1) Fail-Soft Around Anchor Path

Right now, a single C-ext error kills row targeting. Wrap anchor detection + IGN row checks, and always fall back to OCR-only row scoring:

```python
# backend/ocr/detectors.py (inside your row-agnostic detector)
def find_target_row_safe(img, rows, target_ign, ocr_fn):
    try:
        # your anchor-based fast path here
        return anchor_based_find_row(img, rows, target_ign)
    except Exception as e:
        logger.exception("Anchor path failed; falling back to OCR-only: %s", e)
        return ocr_only_find_row(img, rows, target_ign, ocr_fn)
```

### 2) Normalize Strings Aggressively + Use RapidFuzz

Create a shared normalizer and scorer:

```python
# backend/ocr/textmatch.py
import re
from rapidfuzz import process, fuzz

def norm(s: str) -> str:
    if not s: return ""
    s = s.lower()
    s = s.replace("'", "'").replace(""","\"").replace(""","\"")
    s = re.sub(r"[\s_]+", " ", s)         # collapse whitespace/underscores
    s = s.strip()
    return s

def best_match(query: str, candidates: list[str], threshold=85):
    q = norm(query)
    pool = [norm(c) for c in candidates]
    # token_sort_ratio is robust against word order/spacing noise
    match = process.extractOne(q, pool, scorer=fuzz.token_sort_ratio)
    if not match: return None, 0
    val, score, idx = match
    return candidates[idx], score if score >= threshold else 0
```

Wire it in your IGN locator:

```python
# backend/ocr/parsers_kda.py (where you pick the row)
from backend.ocr.textmatch import best_match

def choose_row_by_ign(rows_ocr_texts, target_ign):
    cand, score = best_match(target_ign, rows_ocr_texts, threshold=85)
    if score:
        return rows_ocr_texts.index(cand), score
    return None, 0
```

### 3) ROI-Only OCR + Allowlist (Keep It Fast and Clean)

Make sure every KDA/damage OCR call does: downscale → gray → Otsu → allowlist.

```python
def prep_digits_roi(bgr, max_side=512):
    import cv2
    h,w = bgr.shape[:2]
    s = min(1.0, max_side/max(h,w))
    if s < 1.0:
        bgr = cv2.resize(bgr, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (3,3), 0)
    _, bin_ = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return bin_

# then
text = reader.readtext(prep_digits_roi(roi), detail=0, paragraph=False, allowlist="0123456789/")
```

### 4) Cache OCR by Crop Hash (Kills Repeated Work)

```python
# backend/ocr/ocr_cache.py
import hashlib
from functools import lru_cache

_OCR_STASH = {}

def _h(arr):
    return hashlib.sha1(memoryview(arr).tobytes()).hexdigest()

@lru_cache(maxsize=4096)
def _ocr_cached(key, allowlist):
    arr = _OCR_STASH[key]
    return READER.readtext(arr, detail=0, paragraph=False, allowlist=allowlist)

def ocr_digits_cached(arr):
    key = _h(arr); _OCR_STASH[key] = arr
    return _ocr_cached(key, "0123456789/")
```

### 5) Add One-Time Reader Warmup and Pin EasyOCR CPU on macOS

MPS often isn't faster for EasyOCR:

```python
# backend/ocr/ocr_reader.py
import os, easyocr, numpy as np
_READER=None

def get_reader():
    global _READER
    if _READER is None:
        _READER = easyocr.Reader(['en'], gpu=os.getenv("OCR_GPU","0")=="1")
        _READER.readtext(np.zeros((16,16), dtype='uint8'))  # warmup
    return _READER
```

## C) Quick Validation Sequence

### 1. After the Reinstall

```bash
venv/bin/python -c "import numpy, cv2; print(numpy.__version__, cv2.__version__)"
```

No import errors, no dtype warnings.

### 2. CLI Again (Should Not Log NumPy dtype Errors)

```bash
venv/bin/python -m backend.src.cli.ocr_debug \
  --image /Users/lesz/Documents/Project-AI/Trial-Image/IMG_1767.PNG \
  --ign "Diary of dolls" --debug --all
```

### 3. Targeted Match Probe (Prints Best Candidate + Score)

```bash
python - <<'PY'
from backend.ocr.textmatch import best_match
cands = ["Diary  of  dolls", "diary-of-dolls", "Diary 0f dolls", "DIARY OF D0LLS"]
print(best_match("Diary of dolls", cands, threshold=80))
PY
```

### 4. Performance Test (Fast Mode)

```bash
FAST_TEST=1 OCR_BUDGET_MS=2000 venv/bin/pytest backend/tests/performance/test_ocr_performance.py -q
```

**Expect drop in time once caching + ROI + rapidfuzz are in place.**
