# backend/ocr/ocr_reader.py
import os
import easyocr
import numpy as np
from typing import Optional


_READER: Optional[easyocr.Reader] = None


def get_reader() -> easyocr.Reader:
    """
    Get the global EasyOCR reader instance with proper initialization.
    
    Returns:
        Initialized EasyOCR Reader instance
    """
    global _READER
    if _READER is None:
        # Enable GPU by default for better performance, allow CPU fallback
        use_gpu = os.getenv("OCR_GPU", "1") == "1"
        
        _READER = easyocr.Reader(['en'], gpu=use_gpu)
        
        # Warmup with a small test image
        test_img = np.zeros((16, 16), dtype='uint8')
        _READER.readtext(test_img)
    
    return _READER


def prep_digits_roi(bgr: np.ndarray, max_side: int = 512) -> np.ndarray:
    """
    Preprocess image for digit-only OCR with optimal settings.
    
    Args:
        bgr: Input BGR image
        max_side: Maximum side length for resizing
    
    Returns:
        Preprocessed binary image optimized for digit recognition
    """
    import cv2
    
    h, w = bgr.shape[:2]
    
    # Resize if too large (maintain aspect ratio)
    scale = min(1.0, max_side / max(h, w))
    if scale < 1.0:
        bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), 
                        interpolation=cv2.INTER_AREA)
    
    # Convert to grayscale
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Apply Otsu thresholding for binary image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary


def prep_text_roi(bgr: np.ndarray, max_side: int = 1024) -> np.ndarray:
    """
    Preprocess image for general text OCR.
    
    Args:
        bgr: Input BGR image
        max_side: Maximum side length for resizing
    
    Returns:
        Preprocessed image optimized for text recognition
    """
    import cv2
    
    h, w = bgr.shape[:2]
    
    # Resize if too large (maintain aspect ratio)
    scale = min(1.0, max_side / max(h, w))
    if scale < 1.0:
        bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), 
                        interpolation=cv2.INTER_AREA)
    
    # Convert to grayscale
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # Apply slight Gaussian blur
    gray = cv2.GaussianBlur(gray, (1, 1), 0)
    
    return gray


def extract_digits_optimized(img: np.ndarray) -> list:
    """
    Extract digits from image using optimized preprocessing and caching.
    
    Args:
        img: Input image array
    
    Returns:
        List of extracted digit strings
    """
    from backend.ocr.ocr_cache import ocr_digits_cached
    
    # Preprocess for digit extraction
    preprocessed = prep_digits_roi(img)
    
    # Use cached OCR
    results = ocr_digits_cached(preprocessed)
    
    # Extract text from results
    return [text for text, confidence in results if confidence > 0.5]


def extract_text_optimized(img: np.ndarray, allowlist: str = None) -> list:
    """
    Extract text from image using optimized preprocessing and caching.
    
    Args:
        img: Input image array (BGR or grayscale)
        allowlist: Characters to allow in OCR
    
    Returns:
        List of extracted text strings
    """
    from backend.ocr.ocr_cache import ocr_text_cached
    
    # Handle both BGR and grayscale images
    if len(img.shape) == 3:
        # BGR image - preprocess normally
        preprocessed = prep_text_roi(img)
    else:
        # Grayscale image - use as is
        preprocessed = img
    
    # Use cached OCR
    results = ocr_text_cached(preprocessed, allowlist)
    
    # Extract text from results
    return [text for text, confidence in results if confidence > 0.3]
