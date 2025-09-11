from typing import List, Dict, Any, Optional

try:
    from rapidfuzz import process, fuzz  # type: ignore
    _HAS_RF = True
except Exception:  # Fallback to difflib if rapidfuzz missing
    from difflib import SequenceMatcher
    _HAS_RF = False


def _similar(a: str, b: str) -> float:
    a = (a or "").lower()
    b = (b or "").lower()
    if _HAS_RF:
        return float(fuzz.token_set_ratio(a, b))
    return SequenceMatcher(None, a, b).ratio() * 100.0


def pick_row(ign: str, rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pick the most likely player row.

    Args:
        ign: target player ign
        rows: list of { 'name': str, 'bbox': [x1,y1,x2,y2], 'side': 'ally'|'enemy', 'badges': [..] }
    """
    ign = (ign or "").strip()
    if ign:
        names = [r.get('name', '') for r in rows]
        # Use rapidfuzz when available for speed; fallback similarity otherwise
        if _HAS_RF:
            from rapidfuzz import process, fuzz  # type: ignore
            hit = process.extractOne(ign, names, scorer=fuzz.token_set_ratio)
            if hit and hit[1] >= 85:
                return rows[names.index(hit[0])]
        else:
            best = (-1, None)
            for i, n in enumerate(names):
                score = _similar(ign, n)
                if score > best[0]:
                    best = (score, i)
            if best[0] >= 85 and best[1] is not None:
                return rows[best[1]]

    # Fallback: ally MVP row
    for r in rows:
        if r.get('side') == 'ally' and 'MVP' in (r.get('badges') or []):
            return r

    # Last fallback: first ally row
    for r in rows:
        if r.get('side') == 'ally':
            return r

    return rows[0] if rows else None

