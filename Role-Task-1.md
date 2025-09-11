1) Role → Hero inheritance (resolver)

Unify the merge so every request gets: role defaults + hero overrides (if any). Never return empty.
# backend/coaching/resolver.py
import json, pathlib, operator
from functools import lru_cache
from typing import List
from pydantic import BaseModel
OPS = {">":operator.gt,">=":operator.ge,"<":operator.lt,"<=":operator.le,"==":operator.eq,"!=":operator.ne}

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROLES = ROOT / "coaching" / "rules" / "roles"
HEROES = ROOT / "coaching" / "rules" / "heroes"

class MetricRule(BaseModel):
    metric: str; op: str; value: float; weight: float = 1.0

class Snippet(BaseModel):
    id: str; title: str; body: str
    tags: list[str] = []; when: list[MetricRule] = []; priority: int = 100

class RolePack(BaseModel):
    role: str; defaults: list[Snippet] = []

class HeroPack(BaseModel):
    hero: str; slug: str; role: str; overrides: list[Snippet] = []; params: dict = {}

def _slug(s: str) -> str: return s.lower().replace(" ", "-")

@lru_cache(maxsize=128)
def _load_role(role: str) -> RolePack:
    return RolePack(**json.loads((ROLES / f"{role}.json").read_text()))

@lru_cache(maxsize=512)
def _load_hero(slug: str) -> HeroPack:
    return HeroPack(**json.loads((HEROES / f"{slug}.json").read_text()))

def _score(sn: Snippet, stats: dict) -> float:
    if not sn.when: return float(50 - sn.priority)
    acc = 0.0
    for cond in sn.when:
        m = cond.metric
        v = None
        if m == "kda" and (kd := stats.get("kda")):
            v = (kd.get("k",0)+kd.get("a",0))/max(1, kd.get("d",0))
        else:
            v = stats.get(m)
        if v is None or not OPS[cond.op](float(v), float(cond.value)):
            return -1.0
        acc += cond.weight
    return acc

def resolve_coaching(hero: str, role: str|None, stats: dict) -> list[dict]:
    hp = _load_hero(_slug(hero))
    rp = _load_role((role or hp.role).lower())
    cand = rp.defaults + hp.overrides
    ranked = [(sn, _score(sn, stats)) for sn in cand]
    ranked = [x for x in ranked if x[1] >= 0.0]
    ranked.sort(key=lambda x: (-x[1], x[0].priority))
    top = [s[0].dict() for s in ranked[:8]]
    return top or [s.dict() for s in rp.defaults[:3]]
    Opinion: this is the linchpin. Once this function exists, “no coaching logic” cannot happen unless role packs are missing.

    2) Generator for the 116 missing hero packs

Create stubs for all heroes from data/heroes_cleaned.json. Each stub inherits at runtime; you only edit overrides when you want nuance.
# backend/src/cli/generate_hero_rules.py
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
HEROES_JSON = ROOT / "data" / "heroes_cleaned.json"
OUT = ROOT / "backend" / "coaching" / "rules" / "heroes"
OUT.mkdir(parents=True, exist_ok=True)

BASE = {
  "hero":"", "slug":"", "role":"",
  "overrides":[
    {"id":"generic_strengths","title":"Lean into your kit","body":"Trade on your spikes, avoid unfavored trades.","tags":["identity"],"when":[],"priority":100},
    {"id":"objectives_sync","title":"Sync plays to objectives","body":"Time roams to Turtle/Lord; avoid coin flips.","tags":["macro"],"when":[],"priority":110},
    {"id":"safe_resets","title":"Reset before big fights","body":"Reset for mana/HP/items before objectives.","tags":["tempo"],"when":[],"priority":120}
  ],
  "params":{}
}

def main():
    data = json.loads(HEROES_JSON.read_text())
    emitted = 0
    for h in data:
        name = h["name"]; role = (h.get("role") or "").lower()
        if role not in {"mage","marksman","tank","fighter","assassin","support"}:
            role = "fighter"
        slug = (h.get("slug") or name.lower().replace(" ","-"))
        path = OUT / f"{slug}.json"
        if not path.exists():  # don't clobber hand-authored overrides
            stub = dict(BASE); stub["hero"]=name; stub["slug"]=slug; stub["role"]=role
            path.write_text(json.dumps(stub, indent=2))
            emitted += 1
    print(f"Generated {emitted} new hero rulepacks in {OUT}")

if __name__=="__main__": main()

Run it
	•	macOS/zsh:
    venv/bin/python -m backend.src.cli.generate_hero_rules
    This will add ~116 JSONs under backend/coaching/rules/heroes/. Your 10 existing hero files won’t be overwritten.