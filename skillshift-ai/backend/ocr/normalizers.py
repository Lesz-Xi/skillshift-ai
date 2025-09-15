import re
from typing import List, Tuple, Optional

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

_O_MAP = str.maketrans({"O":"0","o":"0"})
_L_MAP = str.maketrans({"l":"1","I":"1","|":"1"})

def clean_digits(s: str) -> str:
    return s.translate(_O_MAP).translate(_L_MAP)

def fix_ocr_slash_noise(s: str) -> str:
    # "Ol2ll2" -> "0/2/12"
    s = clean_digits(s)
    s = re.sub(r"(\d)(?=[^\d])", r"\1", s)
    s = re.sub(r"(\d+)[^\d]+(\d+)[^\d]+(\d+)", r"\1/\2/\3", s)
    return s

def normalize_kda_text(s: str) -> str:
    s = s.strip()
    s = fix_ocr_slash_noise(s)
    s = re.sub(r"[^\d/]", "", s)
    return s

def norm_percent(s: str) -> float:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%?", s)
    return float(m.group(1))/100.0 if m else 0.0

def normalize_text_for_matching(text: str) -> str:
    """
    Normalize text for IGN matching with OCR noise handling.
    Implements OCR-Mission-2.md requirement for bulletproof IGN matching.
    """
    try:
        # Convert to lowercase first
        normalized = text.lower()
        
        # OCR noise normalization patterns (OCR mistake → correct character)
        noise_patterns = {
            '0': 'o', '1': 'i', '5': 's', '8': 'b', '6': 'g'
        }
        
        # Apply OCR noise corrections character by character, but only for letters
        result = ""
        for char in normalized:
            if char in noise_patterns and char.isalpha():
                result += noise_patterns[char]
            else:
                result += char
        normalized = result
        
        # Common OCR confusions specific to "Diary of dolls" (do these FIRST)
        normalized = normalized.replace('d1ary', 'diary')
        normalized = normalized.replace('0f', 'of')
        normalized = normalized.replace('d0lls', 'dolls')
        normalized = normalized.replace('d011s', 'dolls')
        normalized = normalized.replace('do11s', 'dolls')
        
        # More general OCR noise corrections
        normalized = normalized.replace('cl0ry', 'clory')  # common OCR confusion
        normalized = normalized.replace('d0iry', 'doiry')  # another pattern
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
        
    except Exception as e:
        # Fallback to original text if normalization fails
        return text.lower()


def is_ign_match(target_ign: str, ocr_text: str) -> bool:
    """
    Check if target IGN matches OCR text, handling guild/clan tags.
    
    Examples:
    - "Diary of dolls" matches "HVD Diary of dolls"
    - "Diary of dolls" matches "[CLAN] Diary of dolls"
    - "HVD Diary of dolls" matches "Diary of dolls"
    """
    # Normalize both texts
    target_norm = normalize_text_for_matching(target_ign)
    ocr_norm = normalize_text_for_matching(ocr_text)
    
    # Direct substring match (handles when target is part of OCR text)
    if target_norm in ocr_norm:
        return True
    
    # Check if OCR text is part of target (handles when OCR missed guild tag)
    if ocr_norm in target_norm:
        return True
    
    # Handle guild/clan tags by checking if core IGN matches
    # Common guild tag patterns: [TAG], TAG·, «TAG», etc.
    guild_pattern = r'^(?:\[\w+\]|\w{2,5}[·\s]|«\w+»|\w+\|)\s*(.+)'
    
    # Try to extract core IGN from OCR text
    ocr_match = re.match(guild_pattern, ocr_norm)
    if ocr_match:
        core_ocr_ign = ocr_match.group(1).strip()
        if target_norm == core_ocr_ign or target_norm in core_ocr_ign:
            return True
    
    # Try to extract core IGN from target
    target_match = re.match(guild_pattern, target_norm)
    if target_match:
        core_target_ign = target_match.group(1).strip()
        if core_target_ign == ocr_norm or core_target_ign in ocr_norm:
            return True
    
    return False

# Legacy helper functions for backward compatibility
def normalize_diary_of_dolls_text(text: str) -> str:
    """Legacy function - use normalize_text_for_matching instead."""
    return normalize_text_for_matching(text)


def norm_ign(s: str) -> str:
    """
    Normalize IGN text for fuzzy matching.
    Handles OCR noise and common character confusion patterns.
    """
    if not s: 
        return ""
    
    s = s.lower().replace("'","'")
    s = re.sub(r"[\W_]+", "", s)
    s = s.replace("0","o").replace("1","l")
    return s


def best_ign_match(target: str, names: List[str], cutoff: int = 86) -> Tuple[Optional[str], int]:
    """
    Find the best IGN match using fuzzy string matching.
    
    Args:
        target: The target IGN to search for
        names: List of candidate IGN names
        cutoff: Minimum score threshold (default 86)
        
    Returns:
        Tuple of (best_match_name, score) or (None, 0) if no good match
    """
    if not names: 
        return (None, 0)
    
    if not RAPIDFUZZ_AVAILABLE:
        # Fallback to basic string matching without rapidfuzz
        target_norm = norm_ign(target)
        for name in names:
            if norm_ign(name) == target_norm:
                return (name, 100)
        return (None, 0)
    
    # Use rapidfuzz for fuzzy matching
    t = norm_ign(target)
    pool = [norm_ign(n) for n in names]
    mapping = {norm_ign(n): n for n in names}
    
    try:
        m = process.extractOne(t, pool, scorer=fuzz.token_set_ratio)
        if not m: 
            return (None, 0)
        
        hit, score, _ = m
        return (mapping[hit], score) if score >= cutoff else (None, score)
    except Exception:
        # Fallback to basic matching if rapidfuzz fails
        target_norm = norm_ign(target)
        for name in names:
            if norm_ign(name) == target_norm:
                return (name, 100)
        return (None, 0)