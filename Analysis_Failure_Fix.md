1) Frontend ↔ Backend: stop the “error loading resource”

A) Verify the API is reachable (one command)
# Adjust port if you run uvicorn differently
curl -sS http://localhost:8000/health | python -m json.tool

Expected: {"status":"ok"}. If not, (re)start the API:
uvicorn web.app:app --host 0.0.0.0 --port 8000 --reload

B) Add/confirm CORS in web/app.py
# web/app.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Skillshift AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # or your UI origin(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

C) Confirm the endpoint works with the same payload your UI sends
If your UI sends multipart with two images + ign:
curl -sS -X POST http://localhost:8000/v2/analysis/screenshot \
  -F "kda_image=@/Users/lesz/Documents/Project-AI/Trial-Image/IMG_1767.PNG" \
  -F "damage_image=@/Users/lesz/Documents/Project-AI/Trial-Image/IMG_1768.PNG" \
  -F "ign=Diary of dolls" \
  -H "Accept: application/json" | python -m json.tool

  If this fails (non-200 or HTML), the UI will show “error loading resource”. Fix the backend first—the browser preview error is almost always a non-JSON response.

  D) Make the frontend resilient (one safe guard)

Where you call fetch(...) in the UI:
async function postJSON(url: string, body: FormData | object) {
  const opts: RequestInit = body instanceof FormData
    ? { method: "POST", body }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };

  const res = await fetch(url, opts);
  const text = await res.text();               // <-- don’t assume JSON
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0,300)}`);
  try { return JSON.parse(text); } catch { return { raw:text }; }
}
Now the UI will show the real server error instead of a generic preview failure.

2) OCR returning 0/0/0 & confidence ~32%

These are the fastest fixes to avoid “empty” KDA:

A) Use robust IGN matching everywhere

Ensure you call a fuzzy matcher before falling back to MVP/top row. (If you don’t have this already, drop it in and use it in KDA row selection.)
# backend/ocr/normalizers.py
import re
from rapidfuzz import fuzz, process

def norm_ign(s: str) -> str:
    if not s: return ""
    s = s.lower().replace("’","'")
    s = re.sub(r"[\W_]+", "", s)
    s = s.replace("0","o").replace("1","l")
    return s

def best_ign_match(target: str, names: list[str], cutoff: int = 86):
    if not names: return (None, 0)
    t = norm_ign(target)
    pool = [norm_ign(n) for n in names]
    mapping = {norm_ign(n): n for n in names}
    m = process.extractOne(t, pool, scorer=fuzz.token_set_ratio)
    if not m: return (None, 0)
    hit, score, _ = m
    return (mapping[hit], score) if score >= cutoff else (None, score)

    Use it in your KDA parser/detector when deciding which row to parse.


B) Anchor-less fallback so we always get rows

When anchors or YOLO fail, split a central table region into 5 rows by ratio (you already show 5 rows in debug—great). Make sure your detector returns crops even with low confidence:
# backend/ocr/detectors.py (fallback path)
def detect_table_regions(img):
    region = try_anchor_based(img)
    if region: return region
    h, w = img.shape[:2]
    return {"bbox": (int(0.15*w), int(0.20*h), int(0.70*w), int(0.60*h)),
            "confidence": 0.35, "source": "fallback-heuristic"}


C) Regex fallback for KDA text so we don’t return zeros
If per-cell OCR fails, do a quick text-wide search on the row crop:
# backend/ocr/parsers_kda.py (inside the row parse)
import re
KDA_RE = re.compile(r'\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})\b')

def _extract_kda_from_text(text: str):
    m = KDA_RE.search(text.replace("O","0"))
    if not m: return None
    k,d,a = map(int, m.groups())
    return {"kills": k, "deaths": d, "assists": a}

    Combine this with your OCR tokens per row: join tokens into a single line and apply _extract_kda_from_text.

    D) Kill the classic NumPy truthiness crash (often masks results)

Anywhere you have if some_numpy_array: replace with if arr is not None and arr.size > 0:. One helper to be safe:
# backend/ocr/ocr_reader.py
import numpy as np
def truthy(x): return False if x is None else (x.size > 0 if isinstance(x, np.ndarray) else bool(x))

3) One-shot local triage (paste & run)

Create scripts/triage.sh:
#!/usr/bin/env bash
set -euo pipefail

API=${API:-http://localhost:8000}

echo "1) Health:"
curl -sS "$API/health" | python -m json.tool

echo "2) Analysis (multipart):"
curl -sS -X POST "$API/v2/analysis/screenshot" \
  -F "kda_image=@$1" \
  -F "damage_image=@$2" \
  -F "ign=${3:-Diary of dolls}" \
  -H "Accept: application/json" | python -m json.tool

  Run:
  bash scripts/triage.sh /path/IMG_1767.PNG /path/IMG_1768.PNG "Diary of dolls"

  	•	If this returns valid JSON in the terminal, the frontend issue is purely fetch/error-handling or CORS.
	•	If this shows empty KDA, your row selection / regex fallback isn’t wired; apply the snippets above.

    4) Quick sanity assertions (drop in pytest later)
    def test_ign_matching_high_score():
    from backend.ocr.normalizers import best_ign_match
    hit, score = best_ign_match("Diary of dolls", ["D1ary 0f d0lls","diary-of-dolls","Diary Of Dolls"])
    assert hit is not None and score >= 86

def test_hero_db_loaded():
    from backend.ocr.hero_resolver import AdvancedHeroResolver
    r = AdvancedHeroResolver()
    assert r.count >= 120

    TL;DR
	•	Fix browser error by confirming /health and POST /v2/analysis/screenshot via curl, add CORS, and make the frontend parse non-JSON safely.
	•	Fix 0/0/0 by (a) robust IGN matching, (b) anchor-less row fallback, (c) regex KDA fallback, (d) removing NumPy truthiness pitfalls.

Ping me with the curl output from step 3 if anything still looks off, and I’ll tailor the next micro-patch.
