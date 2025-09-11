# backend/ocr/textmatch.py
import re
from rapidfuzz import process, fuzz


def norm(s: str) -> str:
    """
    AGGRESSIVE normalization for bulletproof OCR matching.
    Handles OCR noise, punctuation variants, and common misreadings.
    """
    if not s:
        return ""
    
    # Convert to lowercase
    s = s.lower()
    
    # Fix common OCR digit/letter confusions FIRST
    ocr_fixes = {
        # Digit to letter confusions
        '0': 'o', '1': 'i', '5': 's', '8': 'b', '6': 'g',
        # Letter to digit confusions (reverse)
        'o': '0', 'i': '1', 's': '5', 'b': '8', 'g': '6',
        # Common OCR misreadings
        'rn': 'm', 'vv': 'w', 'ii': 'n', 'll': 'u'
    }
    
    # Apply OCR fixes
    for wrong, right in ocr_fixes.items():
        s = s.replace(wrong, right)
    
    # Normalize ALL quote variants and punctuation
    quote_variants = ["'", "'", "'", '"', '"', '"', "`", "´"]
    for quote in quote_variants:
        s = s.replace(quote, "")  # Remove quotes entirely
    
    # Collapse ALL whitespace, underscores, hyphens, and dots
    s = re.sub(r"[\s_\-\.]+", " ", s)
    
    # Remove ALL punctuation except letters, numbers, and spaces
    s = re.sub(r"[^\w\s]", "", s)
    
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    
    # Strip and return
    s = s.strip()
    return s


def best_match(query: str, candidates: list[str], threshold: int = 85):
    """
    Find the best match using RapidFuzz with token_sort_ratio.
    ENHANCED with aggressive normalization and detailed logging.
    
    Args:
        query: The string to match against
        candidates: List of candidate strings
        threshold: Minimum score to consider a match (0-100, default 85)
    
    Returns:
        Tuple of (best_candidate, score) or (None, 0) if no match found
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not query or not candidates:
        logger.debug(f"Empty query or candidates: query='{query}', candidates={len(candidates) if candidates else 0}")
        return None, 0
    
    # Normalize query and candidates
    q = norm(query)
    pool = [norm(c) for c in candidates]
    
    # Log normalization results for debugging
    logger.debug(f"Normalized query: '{query}' → '{q}'")
    
    # Use token_sort_ratio for robust matching against word order/spacing noise
    match = process.extractOne(q, pool, scorer=fuzz.token_sort_ratio)
    
    if not match:
        logger.debug(f"No match found for query '{q}' against {len(pool)} candidates")
        return None, 0
    
    val, score, idx = match
    original_candidate = candidates[idx]
    
    # DETAILED LOGGING as requested in OCR-Mission-1.md
    logger.info(f"IGN Match: '{query}' → '{original_candidate}' (score: {score:.1f}, normalized: '{q}' → '{val}')")
    
    # Early exit for high-confidence matches (optimization)
    if score >= 95:
        logger.info(f"High-confidence IGN match found early: score={score:.1f}")
        return original_candidate, score
    
    # Return original candidate (not normalized) if score meets threshold
    if score >= threshold:
        logger.info(f"IGN match accepted: score={score:.1f} >= threshold={threshold}")
        return original_candidate, score
    else:
        logger.info(f"IGN match rejected: score={score:.1f} < threshold={threshold}")
        return None, 0


def fuzzy_contains(query: str, text: str, threshold: int = 80) -> bool:
    """
    Check if query is contained in text using fuzzy matching.
    
    Args:
        query: String to search for
        text: Text to search in
        threshold: Minimum score to consider a match
    
    Returns:
        True if query is found with sufficient similarity
    """
    if not query or not text:
        return False
    
    # Split text into words and check for partial matches
    words = text.split()
    for word in words:
        if len(word) >= 3:  # Only check words of reasonable length
            match, score = best_match(query, [word], threshold)
            if match:
                return True
    
    return False


def test_ign_matching():
    """
    Test enhanced IGN matching with target case from OCR-Mission-1.md.
    Tests bulletproof matching for "Diary of dolls" against various OCR variations.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Target IGN from the mission
    target_ign = "Diary of dolls"
    
    # Common OCR variations and misreadings
    test_cases = [
        # Perfect case
        "Diary of dolls",
        
        # Case variations
        "DIARY OF DOLLS",
        "diary of dolls", 
        "Diary Of Dolls",
        
        # Spacing variations
        "Diary  of  dolls",
        "Diaryofdolls",
        "Diary-of-dolls",
        "Diary.of.dolls",
        
        # Quote variations
        "\"Diary of dolls\"",
        "'Diary of dolls'",
        "\"Diary of dolls\"",  # Smart quotes test
        
        # OCR noise variations
        "D1ary of dolls",  # 1 instead of i
        "Diary 0f dolls",  # 0 instead of o
        "D1ary 0f d0lls",  # Multiple substitutions
        "Diaryrnof dolls", # rn misread as m (will be fixed by norm)
        
        # Partial matches
        "Diary of",
        "of dolls",
        
        # Should NOT match
        "Different name",
        "Diary",
        "dolls"
    ]
    
    logger.info("=== IGN MATCHING TEST ===")
    logger.info(f"Target IGN: '{target_ign}'")
    logger.info(f"Normalized target: '{norm(target_ign)}'")
    
    successful_matches = 0
    total_tests = len(test_cases)
    
    for i, candidate in enumerate(test_cases):
        match, score = best_match(target_ign, [candidate], threshold=85)
        
        # Determine if this should be a successful match
        is_valid_variation = i < 12  # First 12 are valid variations
        
        if is_valid_variation and match:
            successful_matches += 1
            status = "✅ PASS"
        elif not is_valid_variation and not match:
            status = "✅ PASS (correctly rejected)"
        elif is_valid_variation and not match:
            status = "❌ FAIL (should have matched)"
        else:
            status = "❌ FAIL (should not have matched)"
        
        logger.info(f"Test {i+1:2d}: '{candidate}' → {status} (score: {score:.1f})")
    
    success_rate = (successful_matches / 12) * 100  # Only count valid variations
    logger.info(f"=== RESULTS: {successful_matches}/12 valid variations matched ({success_rate:.1f}%) ===")
    
    return success_rate >= 90  # 90% success rate required


if __name__ == "__main__":
    # Run test when module is executed directly
    import logging
    logging.basicConfig(level=logging.INFO)
    success = test_ign_matching()
    print(f"IGN matching test {'PASSED' if success else 'FAILED'}")
