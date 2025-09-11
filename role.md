# Goal

Scale coaching feedback from a few hard-coded heroes to every hero in `data/heroes_cleaned.json`, while keeping per-role fallbacks and allowing hero-specific overrides.

## Ground truth & current layout

- Hero catalog: `data/heroes_cleaned.json` (keys: name, slug, role, sub_role, specialty, …).
- Existing rule files (examples):
  - `rules/roles/mage/generic_mage.py`, `rules/roles/mage/kagura.py`
  - `rules/roles/support/mathilda.py`, `rules/roles/support/estes.py`
  - `rules/roles/fighter/chou.py`, `rules/roles/marksman/miya.py`, `rules/roles/tank/tigreal.py`, …
- Backend returns flat metrics to UI (we already normalize): `kda`, `gpm`, `role`, `hero`, damage_view metrics (`hero_damage`, `turret_damage`, `damage_taken`, `teamfight_participation`), and `confidence_score` (0–1).
- We must keep working even when some numbers are missing → use graceful N/A and role fallbacks.

## What to build

### 1. Hero Coaching Registry

- New module: `rules/registry.py`
- Expose:

```python
from typing import Callable, Dict, Any

FeedbackFn = Callable[[Dict[str, Any]], list[str]]

class CoachRegistry:
    def __init__(self): ...
    def register(self, role: str, hero_slug: str, fn: FeedbackFn): ...
    def register_role_default(self, role: str, fn: FeedbackFn): ...
    def get(self, role: str, hero_slug: str) -> FeedbackFn: ...
```

- Resolution order: exact hero → role default → global default (a minimal "generic" coach).
- Provide `GLOBAL_DEFAULT` that returns 1 friendly message if nothing else applies.

### 2. Auto-wiring from JSON

- New script: `scripts/build_hero_registry.py`
- Reads `data/heroes_cleaned.json`.
- For each hero:
  - Compute `role_dir = rules/roles/{role}` and `hero_module = {slug}.py`
  - If file exists and provides `coach(feats: dict) -> list[str]`, register it.
  - Else register the role default (see #3) and generate a hero stub to speed future authoring:
    - Path: `rules/roles/{role}/{slug}.py`
    - Contents: import role generic, then override none; expose `coach()` that defers to generic. Add TODO header with hero meta (sub_role, specialty, priority).
- Output a compiled `rules/auto_registry.py` that instantiates CoachRegistry, performs all registrations, and exposes a singleton:

```python
from .registry import CoachRegistry
REGISTRY = CoachRegistry()
# registrations…
```

### 3. Role Defaults (generic coaches)

- Ensure a generic coach exists per top-level role:
  - `rules/roles/mage/generic_mage.py`
  - `rules/roles/assassin/generic_assassin.py`
  - `rules/roles/fighter/generic_fighter.py`
  - `rules/roles/marksman/generic_marksman.py`
  - `rules/roles/support/generic_support.py`
  - `rules/roles/tank/generic_tank.py`
- If a file is missing, create it using the threshold patterns below.
- Each generic returns a list of short, actionable strings.
- Threshold helpers (put in `rules/shared/thresholds.py`):

```python
def safe_get(d, key, default=None):
    v = d.get(key, default)
    return v if v not in (None, "N/A", "NaN") else default

def parse_kda_str(kda_str: str) -> tuple[int,int,int] | None:
    if not kda_str or kda_str in ("N/A", "NaN"): return None
    try:
        k, d, a = [int(x) for x in kda_str.split("/")]
        return k, d, a
    except Exception:
        return None
```

- Common metrics the coaches may read (present when available):
  - `kda` (string like "9/2/12"), `gpm` (int),
  - `hero_damage`, `turret_damage`, `damage_taken`, `teamfight_participation` (percent 0–100),
  - plus flags: `is_mvp`, `match_duration_minutes` (int), `confidence_score` (0–1).
- Generic rule ideas (concise, safe with missing data):
  - If deaths ≥ 6 → "Tighten positioning: ward & wait for CC before entering."
  - If gpm < 600 and role in {mage, marksman, assassin} → "Farm windows: clear two waves between skirmishes."
  - If teamfight_participation < 55% → "Rotate earlier to 5v5s; ping before objective."
  - If hero_damage < team average (if average provided) or very low absolute for role → "Increase poke before commit."
  - If is_mvp → start with 1 positive reinforcement line before warnings.

### 4. Hero-specific overrides

- Keep existing files like `rules/roles/mage/kagura.py`.
- For a hero module, we follow convention:

```python
# rules/roles/mage/kagura.py
from ..mage.generic_mage import coach as generic_mage_coach
from ..shared.thresholds import safe_get, parse_kda_str

def coach(feats: dict) -> list[str]:
    tips = []
    tips += generic_mage_coach(feats)  # base
    # Minimal Kagura flavor example:
    kda = parse_kda_str(feats.get("kda"))
    if kda:
        k, d, a = kda
        if d >= 4:
            tips.append("Use Umbrella (Seimei) to disengage after first combo; don't re-enter without R.")
    if safe_get(feats, "teamfight_participation") is not None and feats["teamfight_participation"] < 55:
        tips.append("Rotate with Umbrella to set up R slow—arrive first around objectives.")
    return tips
```

### 5. Adapter to call the registry

- Update your analysis combiner (where we currently assemble statistical_feedback) to:

```python
from rules.auto_registry import REGISTRY
feedback_fn = REGISTRY.get(role=detected_role, hero_slug=detected_hero_slug)
feedback_lines = feedback_fn(perf_dict)
# De-dup, cap to 4–6 lines, prepend intro if first_upload.
```

- Keep working when hero is overridden by the user; pass that slug to the registry.

### 6. Quality guardrails

- If `confidence_score < 0.5` → append a low-confidence banner line like:
  "Some values were estimated. Upload another match for sharper advice."
- Always skip numeric comparisons when a value is missing; never produce "0 (< 60,000.0)" style messages.
- Provide pluralization that reads cleanly (no decimals, use integers and %).

### 7. Tests

- Add `tests/test_registry.py`, `tests/test_generic_role_rules.py`, `tests/test_kagura_rule.py`.
- Use tiny dictionaries to simulate:
  - A mage with KDA 9/2/12, gpm 720, tfp 68, hero_damage high → produce at least 1 praise + ≤2 targeted suggestions.
  - A missing-data case returns no numeric nonsense and still 1–2 general tips.

### 8. Developer ergonomics

- Add `make register-heroes` → runs `python scripts/build_hero_registry.py`.
- On run, print counts: total heroes, hero-specific modules found, stubs generated, roles using generic.

## Acceptance criteria

- `rules/auto_registry.py` is generated and imported by backend without manual edits.
- For any hero in `heroes_cleaned.json`, the system returns non-empty, readable feedback lines, never containing raw placeholders like `0 (< 60,000.0)`.
- User hero override (e.g., Kagura) resolves the Kagura file when present; otherwise the role generic.
- Unit tests pass; CI green.
- No regressions to the API response shape expected by the frontend.
