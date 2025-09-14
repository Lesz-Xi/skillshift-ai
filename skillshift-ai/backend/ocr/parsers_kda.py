"""
KDA view parser using row-agnostic scoreboard detection.

This parser extracts KDA data from MLBB screenshots using the row-agnostic
approach, making it work for any player position in the scoreboard.
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from dataclasses import dataclass

from .detectors import row_agnostic_detector, RowCrop, TableRegion
from .normalizers import normalize_text_for_matching, normalize_kda_text, fix_ocr_slash_noise, clean_digits, norm_percent

logger = logging.getLogger(__name__)

@dataclass
class KDAResult:
    """Result of KDA parsing for a specific player."""
    player_ign: str
    hero: str
    kills: int
    deaths: int
    assists: int
    mvp_score: float
    confidence: float
    row_index: int
    raw_data: Dict[str, Any]

class RowAgnosticKDAParser:
    """
    KDA parser that works with row-agnostic scoreboard detection.
    
    This parser can extract KDA data from any player row in the scoreboard,
    making it position-independent.
    """
    
    def __init__(self):
        # Enhanced KDA pattern matching with noise tolerance
        self.kda_pattern = re.compile(r'(\d+)[/|\\](\d+)[/|\\](\d+)')
        self.kda_pattern_spaced = re.compile(r'(\d+)\s*/\s*(\d+)\s*/\s*(\d+)')
        # Additional pattern for spaces around slashes
        self.kda_pattern_spaced_alt = re.compile(r'(\d+)\s+/\s+(\d+)\s+/\s+(\d+)')
        self.mvp_pattern = re.compile(r'(\d+\.?\d*)')
        
        # Hero name patterns (common MLBB heroes) - case insensitive
        self.hero_patterns = [
            r'kagura', r'lesley', r'gusion', r'fanny', r'chou', r'claude',
            r'bruno', r'granger', r'kimmy', r'valentina', r'beatrix',
            r'wanwan', r'brody', r'clint', r'layla', r'miya', r'hanabi'
        ]
        
# Removed noise_patterns - now using normalizers module
        
    def parse_kda_from_screenshot(self, image_path: str, target_ign: str) -> Optional[KDAResult]:
        """
        Parse KDA data from screenshot using row-agnostic detection.
        
        Args:
            image_path: Path to the screenshot
            target_ign: Target player's IGN
            
        Returns:
            KDAResult with parsed KDA data, or None if not found
        """
        try:
            # Step 1: Detect table regions
            table_region = row_agnostic_detector.detect_table_regions(image_path)
            if not table_region:
                logger.warning("Could not detect table regions")
                return None
            
            # Step 2: Generate row crops
            row_crops = row_agnostic_detector.generate_row_crops(table_region, image_path, target_ign)
            if not row_crops:
                logger.warning("Could not generate row crops")
                return None
            
            # Step 3: Find target row
            target_row = row_agnostic_detector.find_target_row(row_crops, target_ign)
            if not target_row:
                logger.warning(f"Could not find target row for IGN: {target_ign}")
                return None
            
            # Step 4: Parse KDA from target row
            return self._parse_kda_from_row(image_path, target_row, target_ign)
            
        except Exception as e:
            logger.error(f"Error parsing KDA from screenshot: {e}")
            return None
    
    def parse_from_rows(self, image: np.ndarray, rows: List[RowCrop], target_ign: str = "Diary of dolls") -> Optional[KDAResult]:
        """
        Parse KDA data from pre-detected rows (OCR-Mission-2.md requirement).
        
        Args:
            image: The screenshot image as numpy array
            rows: List of detected row crops from row-agnostic detector
            target_ign: Target player's IGN to search for
            
        Returns:
            KDAResult with parsed KDA data, or None if not found
        """
        try:
            # Find target row containing the IGN
            target_row = None
            for row in rows:
                if self._row_contains_ign(image, row, target_ign):
                    target_row = row
                    break
            
            if not target_row:
                logger.warning(f"Target IGN '{target_ign}' not found in any row")
                return None
            
            # Extract KDA data from the target row
            return self._parse_kda_from_row_crop(image, target_row, target_ign)
            
        except Exception as e:
            logger.error(f"Error parsing KDA from rows: {e}")
            return None
    
    def _row_contains_ign(self, image: np.ndarray, row_crop: RowCrop, target_ign: str) -> bool:
        """Check if a row contains the target IGN."""
        try:
            # Extract row region
            row_y, row_x, row_width, row_height = row_crop.absolute_bbox
            row_region = image[row_y:row_y+row_height, row_x:row_x+row_width]
            
            # Convert to grayscale and preprocess
            gray_region = cv2.cvtColor(row_region, cv2.COLOR_BGR2GRAY)
            processed_region = self._preprocess_for_ocr(gray_region)
            
            # Extract text using ROI-specific OCR
            texts = self._extract_text_roi_optimized(processed_region)
            all_text = " ".join(texts).lower()
            
            # Normalize target IGN for comparison
            normalized_target = self._normalize_text_for_matching(target_ign.lower())
            normalized_text = self._normalize_text_for_matching(all_text)
            
            return normalized_target in normalized_text
            
        except Exception as e:
            logger.debug(f"Error checking if row contains IGN: {e}")
            return False
    
    def _parse_kda_from_row_crop(self, image: np.ndarray, row_crop: RowCrop, target_ign: str) -> Optional[KDAResult]:
        """Parse KDA data from a specific row crop using enhanced processing."""
        try:
            # Extract row region
            row_y, row_x, row_width, row_height = row_crop.absolute_bbox
            row_region = image[row_y:row_y+row_height, row_x:row_x+row_width]
            
            # Convert to grayscale for OCR
            gray_region = cv2.cvtColor(row_region, cv2.COLOR_BGR2GRAY)
            
            # Apply enhanced preprocessing
            processed_region = self._preprocess_for_ocr(gray_region)
            
            # Extract text using ROI-specific OCR with digits focus
            texts = self._extract_text_roi_optimized(processed_region)
            
            # Convert to OCR results format for compatibility
            ocr_results = [(None, text, 0.85) for text in texts]
            
            # Parse KDA data with enhanced noise handling
            kda_data = self._extract_kda_from_ocr_enhanced(ocr_results, target_ign)
            
            if not kda_data:
                return None
            
            # Create result with enhanced confidence calculation
            return KDAResult(
                player_ign=target_ign,
                hero=kda_data.get('hero', 'unknown'),
                kills=kda_data.get('kills', 0),
                deaths=kda_data.get('deaths', 0),
                assists=kda_data.get('assists', 0),
                mvp_score=kda_data.get('mvp_score', 0.0),
                confidence=kda_data.get('confidence', 0.0),
                row_index=row_crop.row_index,
                raw_data=kda_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing KDA from row crop: {e}")
            return None
    
    def _parse_kda_from_row(self, image_path: str, row_crop: RowCrop, target_ign: str) -> Optional[KDAResult]:
        """Parse KDA data from a specific row crop."""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Extract row region
            row_y, row_x, row_width, row_height = row_crop.absolute_bbox
            row_region = image[row_y:row_y+row_height, row_x:row_x+row_width]
            
            # Convert to grayscale for OCR
            gray_region = cv2.cvtColor(row_region, cv2.COLOR_BGR2GRAY)
            
            # Apply preprocessing for better OCR
            processed_region = self._preprocess_for_ocr(gray_region)
            
            # Extract text using optimized OCR with caching
            from backend.ocr.ocr_reader import extract_text_optimized
            texts = extract_text_optimized(processed_region)
            
            # Convert to OCR results format for compatibility
            ocr_results = [(None, text, 0.8) for text in texts]
            
            # Parse KDA data from OCR results using enhanced version with fallbacks
            kda_data = self._extract_kda_from_ocr_enhanced(ocr_results, target_ign)
            
            if not kda_data:
                return None
            
            # Create result
            return KDAResult(
                player_ign=target_ign,
                hero=kda_data.get('hero', 'unknown'),
                kills=kda_data.get('kills', 0),
                deaths=kda_data.get('deaths', 0),
                assists=kda_data.get('assists', 0),
                mvp_score=kda_data.get('mvp_score', 0.0),
                confidence=kda_data.get('confidence', 0.0),
                row_index=row_crop.row_index,
                raw_data=kda_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing KDA from row: {e}")
            return None
    
    def _preprocess_for_ocr(self, gray_image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        try:
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray_image, (3, 3), 0)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return gray_image
    
    def _extract_kda_from_ocr(self, ocr_results: List, target_ign: str) -> Optional[Dict[str, Any]]:
        """Extract KDA data from OCR results."""
        try:
            # Combine all text from OCR results
            all_text = " ".join([result[1] for result in ocr_results])
            logger.debug(f"OCR text from row: {all_text}")
            
            # Find KDA pattern
            kda_match = self.kda_pattern.search(all_text)
            if not kda_match:
                logger.warning("No KDA pattern found in OCR results")
                return None
            
            kills = int(kda_match.group(1))
            deaths = int(kda_match.group(2))
            assists = int(kda_match.group(3))
            
            # Find hero name
            hero = self._extract_hero_name(ocr_results, target_ign)
            
            # Find MVP score
            mvp_score = self._extract_mvp_score(ocr_results)
            
            # Calculate confidence based on OCR quality
            confidence = self._calculate_confidence(ocr_results, target_ign)
            
            return {
                'hero': hero,
                'kills': kills,
                'deaths': deaths,
                'assists': assists,
                'mvp_score': mvp_score,
                'confidence': confidence,
                'raw_text': all_text
            }
            
        except Exception as e:
            logger.error(f"Error extracting KDA from OCR: {e}")
            return None
    
    def _extract_hero_name(self, ocr_results: List, target_ign: str) -> str:
        """Extract hero name from OCR results."""
        try:
            # Look for hero name near the IGN
            ign_found = False
            hero_candidates = []
            
            for bbox, text, confidence in ocr_results:
                text_lower = text.lower().strip()
                
                # Check if this text contains the IGN
                if target_ign.lower() in text_lower:
                    ign_found = True
                    continue
                
                # If we found the IGN, look for hero names in nearby text
                if ign_found:
                    for pattern in self.hero_patterns:
                        if re.search(pattern, text_lower):
                            hero_candidates.append((text, confidence))
                            break
            
            # Return the hero with highest confidence
            if hero_candidates:
                best_hero = max(hero_candidates, key=lambda x: x[1])
                return best_hero[0].strip()
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error extracting hero name: {e}")
            return "unknown"
    
    def _extract_mvp_score(self, ocr_results: List) -> float:
        """Extract MVP score from OCR results."""
        try:
            # Look for numeric values that could be MVP score
            for bbox, text, confidence in ocr_results:
                # Look for decimal numbers (MVP scores are usually like 10.5, 9.2, etc.)
                mvp_match = re.search(r'(\d+\.\d+)', text)
                if mvp_match:
                    score = float(mvp_match.group(1))
                    if 5.0 <= score <= 15.0:  # Reasonable MVP score range
                        return score
            
            # Fallback: look for any number that could be MVP score
            for bbox, text, confidence in ocr_results:
                numbers = re.findall(r'\d+', text)
                for num_str in numbers:
                    num = int(num_str)
                    if 5 <= num <= 15:  # Reasonable MVP score range
                        return float(num)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error extracting MVP score: {e}")
            return 0.0
    
    def _calculate_confidence(self, ocr_results: List, target_ign: str) -> float:
        """Calculate confidence score for the parsed data."""
        try:
            if not ocr_results:
                return 0.0
            
            # Base confidence from OCR quality
            avg_confidence = sum(result[2] for result in ocr_results) / len(ocr_results)
            
            # Bonus for finding the target IGN
            ign_found = any(target_ign.lower() in result[1].lower() for result in ocr_results)
            if ign_found:
                avg_confidence += 0.2
            
            # Bonus for finding KDA pattern
            all_text = " ".join([result[1] for result in ocr_results])
            if self.kda_pattern.search(all_text):
                avg_confidence += 0.1
            
            return min(1.0, avg_confidence)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def _extract_text_roi_optimized(self, processed_region: np.ndarray) -> List[str]:
        """
        Extract text using ROI-specific OCR with digits-only optimization.
        Implements OCR-Mission-2.md requirement for numeric-only parsing.
        """
        try:
            from backend.ocr.ocr_reader import extract_text_optimized
            
            # Standard text extraction
            texts = extract_text_optimized(processed_region)
            
            # Apply ROI binarization for digits-only regions
            roi_texts = self._extract_digits_roi(processed_region)
            
            # Combine results, preferring ROI-extracted digits
            combined_texts = []
            for text in texts:
                # If text contains digits, try to get better version from ROI
                if re.search(r'\d', text):
                    roi_version = self._get_best_roi_match(text, roi_texts)
                    combined_texts.append(roi_version if roi_version else text)
                else:
                    combined_texts.append(text)
            
            # Add any ROI-only digits that weren't matched
            for roi_text in roi_texts:
                if not any(roi_text in combined for combined in combined_texts):
                    combined_texts.append(roi_text)
            
            return combined_texts
            
        except Exception as e:
            logger.error(f"Error in ROI-optimized text extraction: {e}")
            return []
    
    def _extract_digits_roi(self, processed_region: np.ndarray) -> List[str]:
        """Extract digits from ROI using digits-only allowlist."""
        try:
            from backend.ocr.ocr_reader import OCRReader
            ocr_reader = OCRReader()
            
            # Configure allowlist for digits only
            config = '--psm 8 -c tessedit_char_whitelist=0123456789/\\'
            
            # Use Tesseract with digit allowlist
            import pytesseract
            digit_text = pytesseract.image_to_string(processed_region, config=config)
            
            # Split and clean digit-only results
            digit_texts = []
            for line in digit_text.strip().split('\n'):
                cleaned = re.sub(r'[^\d/\\]', '', line.strip())
                if cleaned:
                    digit_texts.append(cleaned)
            
            return digit_texts
            
        except Exception as e:
            logger.debug(f"Error in digits ROI extraction: {e}")
            return []
    
    def _get_best_roi_match(self, original_text: str, roi_texts: List[str]) -> Optional[str]:
        """Get best ROI match for original text containing digits."""
        try:
            # Extract digits from original
            original_digits = re.findall(r'\d+', original_text)
            if not original_digits:
                return None
            
            # Find ROI text with matching digit pattern
            for roi_text in roi_texts:
                roi_digits = re.findall(r'\d+', roi_text)
                if len(roi_digits) == len(original_digits):
                    # Check if digit counts match (for KDA patterns)
                    if len(roi_digits) >= 3:  # Potential KDA pattern
                        return roi_text
            
            return None
            
        except Exception as e:
            logger.debug(f"Error finding best ROI match: {e}")
            return None
    
    def _normalize_text_for_matching(self, text: str) -> str:
        """
        Normalize text for IGN matching with OCR noise handling.
        Uses the centralised normalizers module.
        """
        return normalize_text_for_matching(text)
    
    def _extract_kda_from_ocr_enhanced(self, ocr_results: List, target_ign: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced KDA extraction with improved noise handling.
        Implements hardened regex + normalization from OCR-Mission-2.md.
        """
        try:
            # Combine all text and normalize
            all_text = " ".join([result[1] for result in ocr_results])
            normalized_text = self._normalize_text_for_matching(all_text)
            
            logger.debug(f"Normalized OCR text: '{normalized_text}'")
            logger.debug(f"Original text: '{all_text}'")
            
            # Try multiple KDA pattern variations
            kda_match = None
            
            # Primary pattern with noise tolerance
            kda_match = self.kda_pattern.search(normalized_text)
            logger.debug(f"Primary pattern match: {kda_match}")
            
            # Fallback: spaced pattern
            if not kda_match:
                kda_match = self.kda_pattern_spaced.search(normalized_text)
                logger.debug(f"Spaced pattern match: {kda_match}")
            
            # Fallback: alternative spaced pattern
            if not kda_match:
                kda_match = self.kda_pattern_spaced_alt.search(normalized_text)
                logger.debug(f"Alternative spaced pattern match: {kda_match}")
            
            # Fallback: look in original text
            if not kda_match:
                kda_match = self.kda_pattern.search(all_text)
            
            # ENHANCED REGEX FALLBACK: Try comprehensive text-wide search
            if not kda_match:
                logger.info("Regular patterns failed, trying regex fallback on full text")
                regex_result = self._extract_kda_from_text(all_text)
                if regex_result:
                    kills = regex_result["kills"]
                    deaths = regex_result["deaths"]
                    assists = regex_result["assists"]
                    logger.info(f"✅ Regex fallback succeeded: {kills}/{deaths}/{assists}")
                else:
                    logger.warning("No KDA pattern found in enhanced OCR results or regex fallback")
                    return None
            else:
                # Extract and validate KDA values from regex match
                kills = int(kda_match.group(1))
                deaths = int(kda_match.group(2))  
                assists = int(kda_match.group(3))
            
            
            # Validate KDA ranges
            if not (0 <= kills <= 50 and 0 <= deaths <= 50 and 0 <= assists <= 50):
                logger.warning(f"KDA values out of range: {kills}/{deaths}/{assists}")
                return None
            
            # Extract other data with enhanced matching
            hero = self._extract_hero_name_enhanced(ocr_results, target_ign)
            mvp_score = self._extract_mvp_score_enhanced(ocr_results)
            confidence = self._calculate_confidence_enhanced(ocr_results, target_ign, normalized_text)
            
            return {
                'hero': hero,
                'kills': kills,
                'deaths': deaths,
                'assists': assists,
                'mvp_score': mvp_score,
                'confidence': confidence,
                'raw_text': all_text,
                'normalized_text': normalized_text
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced KDA extraction: {e}")
            return None
    
    def _extract_hero_name_enhanced(self, ocr_results: List, target_ign: str) -> str:
        """Enhanced hero name extraction with better noise handling."""
        try:
            # Use normalized text for better matching
            normalized_ign = self._normalize_text_for_matching(target_ign)
            
            hero_candidates = []
            for bbox, text, confidence in ocr_results:
                normalized_text = self._normalize_text_for_matching(text)
                
                # Skip if this is the IGN text
                if normalized_ign in normalized_text:
                    continue
                
                # Check against hero patterns
                for pattern in self.hero_patterns:
                    if re.search(pattern, normalized_text, re.IGNORECASE):
                        hero_candidates.append((text.strip(), confidence))
                        break
            
            # Return highest confidence hero
            if hero_candidates:
                best_hero = max(hero_candidates, key=lambda x: x[1])
                return best_hero[0]
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error in enhanced hero extraction: {e}")
            return "unknown"
    
    def _extract_mvp_score_enhanced(self, ocr_results: List) -> float:
        """Enhanced MVP score extraction with better validation."""
        try:
            mvp_candidates = []
            
            for bbox, text, confidence in ocr_results:
                # Look for decimal MVP scores
                decimal_matches = re.findall(r'(\d+\.\d+)', text)
                for match in decimal_matches:
                    score = float(match)
                    if 1.0 <= score <= 15.0:  # Reasonable MVP range
                        mvp_candidates.append((score, confidence))
                
                # Look for integer MVP scores  
                integer_matches = re.findall(r'\b(\d{1,2})\b', text)
                for match in integer_matches:
                    score = float(match)
                    if 1.0 <= score <= 15.0:
                        mvp_candidates.append((score, confidence * 0.8))  # Lower confidence for integers
            
            # Return highest confidence MVP score
            if mvp_candidates:
                best_mvp = max(mvp_candidates, key=lambda x: x[1])
                return best_mvp[0]
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error in enhanced MVP extraction: {e}")
            return 0.0
    
    def _calculate_confidence_enhanced(self, ocr_results: List, target_ign: str, normalized_text: str) -> float:
        """Enhanced confidence calculation with multiple factors."""
        try:
            if not ocr_results:
                return 0.0
            
            # Base OCR quality confidence
            base_confidence = sum(result[2] for result in ocr_results) / len(ocr_results)
            
            # IGN matching bonus
            normalized_ign = self._normalize_text_for_matching(target_ign)
            ign_bonus = 0.2 if normalized_ign in normalized_text else 0.0
            
            # KDA pattern bonus  
            kda_bonus = 0.15 if self.kda_pattern.search(normalized_text) else 0.0
            
            # Text quality bonus (less noise = higher confidence)
            noise_penalty = len(re.findall(r'[^\w\s/]', normalized_text)) * 0.01
            
            # Data completeness bonus
            completeness_bonus = 0.1 if len(ocr_results) >= 3 else 0.0
            
            final_confidence = base_confidence + ign_bonus + kda_bonus + completeness_bonus - noise_penalty
            
            return min(1.0, max(0.0, final_confidence))
            
        except Exception as e:
            logger.error(f"Error in enhanced confidence calculation: {e}")
            return 0.0
    
    def _extract_kda_from_text(self, text: str) -> Optional[Dict[str, int]]:
        """
        Enhanced regex fallback for KDA extraction from raw text.
        Implements the Analysis_Failure_Fix.md regex fallback strategy.
        
        Args:
            text: Raw text from OCR to search for KDA patterns
            
        Returns:
            Dict with kills, deaths, assists or None if not found
        """
        try:
            if not text:
                return None
            
            # Enhanced KDA regex pattern with OCR noise handling
            KDA_RE = re.compile(r'\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})\b')
            
            # Clean up OCR noise first
            cleaned_text = text.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1")
            
            # Search for KDA pattern
            match = KDA_RE.search(cleaned_text)
            if not match:
                # Try alternative patterns with different separators
                alt_patterns = [
                    re.compile(r'\b(\d{1,2})\s*[/|\\]\s*(\d{1,2})\s*[/|\\]\s*(\d{1,2})\b'),
                    re.compile(r'\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b'),
                    re.compile(r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\b'),
                ]
                
                for pattern in alt_patterns:
                    match = pattern.search(cleaned_text)
                    if match:
                        break
            
            if not match:
                return None
            
            # Extract and validate values
            kills, deaths, assists = map(int, match.groups())
            
            # Validate ranges (reasonable MLBB values)
            if not (0 <= kills <= 50 and 0 <= deaths <= 50 and 0 <= assists <= 50):
                return None
                
            logger.info(f"Regex fallback extracted KDA: {kills}/{deaths}/{assists} from text: '{text[:50]}...'")
            
            return {
                "kills": kills,
                "deaths": deaths,
                "assists": assists
            }
            
        except Exception as e:
            logger.error(f"Error in regex KDA fallback: {e}")
            return None

# Global instance
kda_parser = RowAgnosticKDAParser()
