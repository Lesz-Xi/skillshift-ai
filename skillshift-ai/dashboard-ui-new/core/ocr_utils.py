import re
from typing import Optional, Tuple


KDA_RX = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{1,2})\b")


def has_img(x) -> bool:
    """Safe check for numpy images to avoid truthiness errors."""
    return x is not None and hasattr(x, "size") and int(getattr(x, "size", 0)) > 0


def only_digits(s: str) -> str:
    return "".join(ch for ch in str(s) if ch.isdigit())


def read_int(text: str) -> Optional[int]:
    ds = only_digits(text)
    try:
        return int(ds) if ds else None
    except Exception:
        return None


def read_kda(text: str) -> Optional[Tuple[int, int, int]]:
    t = (text or "").replace(" ", "").strip()
    m = KDA_RX.search(t)
    if not m:
        return None
    try:
        k, d, a = map(int, m.groups())
        if 0 <= k <= 50 and 0 <= d <= 50 and 0 <= a <= 50:
            return k, d, a
    except Exception:
        pass
    return None


def compute_gpm(gold: Optional[int], minutes: Optional[float]) -> Optional[float]:
    try:
        if gold is None or minutes is None or float(minutes) <= 0:
            return None
        return round(float(gold) / float(minutes), 1)
    except Exception:
        return None

