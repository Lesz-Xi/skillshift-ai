# backend/ocr/ocr_cache.py
import hashlib
from functools import lru_cache
from typing import List, Tuple, Any
import numpy as np

# Global cache for OCR results
_OCR_STASH = {}


def _hash_array(arr: np.ndarray) -> str:
    """Create a hash of the numpy array for caching."""
    return hashlib.sha1(memoryview(arr).tobytes()).hexdigest()


@lru_cache(maxsize=4096)
def _ocr_cached(key: str, allowlist: str) -> List[Tuple[str, float]]:
    """Cached OCR function that retrieves from stash."""
    arr = _OCR_STASH[key]
    from backend.ocr.ocr_reader import get_reader
    reader = get_reader()
    results = reader.readtext(arr, detail=0, paragraph=False, allowlist=allowlist)
    # Convert to (text, confidence) tuples
    return [(text, 0.8) for text in results]


def ocr_digits_cached(arr: np.ndarray) -> List[Tuple[str, float]]:
    """
    OCR with caching for digit-only text extraction.
    
    Args:
        arr: Preprocessed image array
    
    Returns:
        List of (text, confidence) tuples
    """
    key = _hash_array(arr)
    _OCR_STASH[key] = arr
    return _ocr_cached(key, "0123456789/")


def ocr_text_cached(arr: np.ndarray, allowlist: str = None) -> List[Tuple[str, float]]:
    """
    OCR with caching for general text extraction.
    
    Args:
        arr: Preprocessed image array
        allowlist: Characters to allow in OCR (None for all)
    
    Returns:
        List of (text, confidence) tuples
    """
    key = _hash_array(arr)
    _OCR_STASH[key] = arr
    return _ocr_cached(key, allowlist or "")


def clear_cache():
    """Clear the OCR cache to free memory."""
    global _OCR_STASH
    _OCR_STASH.clear()
    _ocr_cached.cache_clear()


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring."""
    return {
        "stash_size": len(_OCR_STASH),
        "lru_cache_info": _ocr_cached.cache_info()
    }
