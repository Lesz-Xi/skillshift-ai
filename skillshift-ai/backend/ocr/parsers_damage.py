"""
Damage view parser using row-agnostic scoreboard detection.

This parser extracts damage data from MLBB screenshots using the row-agnostic
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
class DamageResult:
    """Result of damage parsing for a specific player."""
    player_ign: str
    hero: str
    hero_damage: int
    tower_damage: int
    damage_taken: int
    teamfight_participation: float
    gold_per_minute: int
    confidence: float
    row_index: int
    raw_data: Dict[str, Any]

class RowAgnosticDamageParser:
    """
    Damage parser that works with row-agnostic scoreboard detection.
    
    This parser can extract damage data from any player row in the scoreboard,
    making it position-independent.
    """
    
    def __init__(self):
        # Enhanced damage pattern matching with noise tolerance
        self.damage_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*)')
        self.percentage_pattern = re.compile(r'(\d+(?:\.\d+)?)%')
        self.gpm_pattern = re.compile(r'(\d{3,5})')
        
        # Hero name patterns (common MLBB heroes) - case insensitive
        self.hero_patterns = [
            r'kagura', r'lesley', r'gusion', r'fanny', r'chou', r'claude',
            r'bruno', r'granger', r'kimmy', r'valentina', r'beatrix',
            r'wanwan', r'brody', r'clint', r'layla', r'miya', r'hanabi'
        ]
        
        # Damage value ranges for validation
        self.hero_damage_range = (1000, 500000)  # Reasonable hero damage range
        self.tower_damage_range = (0, 100000)    # Reasonable tower damage range
        self.gpm_range = (200, 10000)            # Reasonable GPM range
        
        # Removed noise_patterns - now using normalizers module
        
    def parse_damage_from_screenshot(self, image_path: str, target_ign: str) -> Optional[DamageResult]:
        """
        Parse damage data from screenshot using row-agnostic detection.
        
        Args:
            image_path: Path to the screenshot
            target_ign: Target player's IGN
            
        Returns:
            DamageResult with parsed damage data, or None if not found
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
            
            # Step 4: Parse damage from target row
            return self._parse_damage_from_row(image_path, target_row, target_ign)
            
        except Exception as e:
            logger.error(f"Error parsing damage from screenshot: {e}")
            return None
    
    def parse_from_rows(self, image: np.ndarray, rows: List[RowCrop], target_ign: str = "Diary of dolls") -> Optional[DamageResult]:
        """
        Parse damage data from pre-detected rows (OCR-Mission-2.md requirement).
        
        Args:
            image: The screenshot image as numpy array
            rows: List of detected row crops from row-agnostic detector
            target_ign: Target player's IGN to search for
            
        Returns:
            DamageResult with parsed damage data, or None if not found
        """
        try:
            # Find target row containing the IGN
            target_row = None
            for row in rows:
                if self._row_contains_ign(image, row, target_ign):
                    target_row = row
                    break
            
            if not target_row:
                logger.warning(f"Target IGN '{target_ign}' not found in any row for damage parsing")
                return None
            
            # Extract damage data from the target row
            return self._parse_damage_from_row_crop(image, target_row, target_ign)
            
        except Exception as e:
            logger.error(f"Error parsing damage from rows: {e}")
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
    
    def _parse_damage_from_row_crop(self, image: np.ndarray, row_crop: RowCrop, target_ign: str) -> Optional[DamageResult]:
        """Parse damage data from a specific row crop using enhanced processing."""
        try:
            # Extract row region
            row_y, row_x, row_width, row_height = row_crop.absolute_bbox
            row_region = image[row_y:row_y+row_height, row_x:row_x+row_width]
            
            # Convert to grayscale for OCR
            gray_region = cv2.cvtColor(row_region, cv2.COLOR_BGR2GRAY)
            
            # Apply enhanced preprocessing
            processed_region = self._preprocess_for_ocr(gray_region)
            
            # Extract text using ROI-specific OCR with percentage focus
            texts = self._extract_text_roi_optimized(processed_region)
            
            # Convert to OCR results format for compatibility
            ocr_results = [(None, text, 0.85) for text in texts]
            
            # Parse damage data with enhanced noise handling
            damage_data = self._extract_damage_from_ocr_enhanced(ocr_results, target_ign)
            
            if not damage_data:
                return None
            
            # Create result with enhanced confidence calculation
            return DamageResult(
                player_ign=target_ign,
                hero=damage_data.get('hero', 'unknown'),
                hero_damage=damage_data.get('hero_damage', 0),
                tower_damage=damage_data.get('tower_damage', 0),
                damage_taken=damage_data.get('damage_taken', 0),
                teamfight_participation=damage_data.get('teamfight_participation', 0.0),
                gold_per_minute=damage_data.get('gold_per_minute', 0),
                confidence=damage_data.get('confidence', 0.0),
                row_index=row_crop.row_index,
                raw_data=damage_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing damage from row crop: {e}")
            return None
    
    def _parse_damage_from_row(self, image_path: str, row_crop: RowCrop, target_ign: str) -> Optional[DamageResult]:
        """Parse damage data from a specific row crop."""
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
            
            # Parse damage data from OCR results
            damage_data = self._extract_damage_from_ocr(ocr_results, target_ign)
            
            if not damage_data:
                return None
            
            # Create result
            return DamageResult(
                player_ign=target_ign,
                hero=damage_data.get('hero', 'unknown'),
                hero_damage=damage_data.get('hero_damage', 0),
                tower_damage=damage_data.get('tower_damage', 0),
                damage_taken=damage_data.get('damage_taken', 0),
                teamfight_participation=damage_data.get('teamfight_participation', 0.0),
                gold_per_minute=damage_data.get('gold_per_minute', 0),
                confidence=damage_data.get('confidence', 0.0),
                row_index=row_crop.row_index,
                raw_data=damage_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing damage from row: {e}")
            return None
    
    def _preprocess_for_ocr(self, gray_image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results with OCR Mission 5 adaptive binarization."""
        try:
            # OCR Mission 5: Use adaptive binarization with Otsu + Sauvola fallback
            from backend.ocr.robustness import adaptive_normalizer
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray_image, (3, 3), 0)
            
            # Use adaptive binarization instead of simple adaptive thresholding
            binary = adaptive_normalizer.adaptive_binarization(blurred)
            
            # Apply morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return gray_image
    
    def _extract_damage_from_ocr(self, ocr_results: List, target_ign: str) -> Optional[Dict[str, Any]]:
        """Extract damage data from OCR results."""
        try:
            # Combine all text from OCR results
            all_text = " ".join([result[1] for result in ocr_results])
            logger.debug(f"OCR text from damage row: {all_text}")
            
            # Find all damage values
            damage_values = self._extract_damage_values(ocr_results)
            
            if not damage_values:
                logger.warning("No damage values found in OCR results")
                return None
            
            # Find hero name
            hero = self._extract_hero_name(ocr_results, target_ign)
            
            # Extract specific damage types
            hero_damage = self._extract_hero_damage(damage_values)
            tower_damage = self._extract_tower_damage(damage_values)
            damage_taken = self._extract_damage_taken(damage_values)
            
            # Extract teamfight participation
            teamfight_participation = self._extract_teamfight_participation(ocr_results)
            
            # Extract GPM
            gpm = self._extract_gpm(ocr_results)
            
            # Calculate confidence
            confidence = self._calculate_confidence(ocr_results, target_ign, damage_values)
            
            return {
                'hero': hero,
                'hero_damage': hero_damage,
                'tower_damage': tower_damage,
                'damage_taken': damage_taken,
                'teamfight_participation': teamfight_participation,
                'gold_per_minute': gpm,
                'confidence': confidence,
                'raw_text': all_text,
                'all_damage_values': damage_values
            }
            
        except Exception as e:
            logger.error(f"Error extracting damage from OCR: {e}")
            return None
    
    def _extract_damage_values(self, ocr_results: List) -> List[int]:
        """Extract all numeric damage values from OCR results."""
        damage_values = []
        
        for bbox, text, confidence in ocr_results:
            # Find all numbers in the text
            numbers = re.findall(r'\d{1,3}(?:,\d{3})*', text)
            for num_str in numbers:
                try:
                    # Remove commas and convert to int
                    num = int(num_str.replace(',', ''))
                    if 100 <= num <= 1000000:  # Reasonable damage range
                        damage_values.append(num)
                except ValueError:
                    continue
        
        return sorted(damage_values, reverse=True)  # Sort descending
    
    def _extract_hero_damage(self, damage_values: List[int]) -> int:
        """Extract hero damage (usually the largest value)."""
        for value in damage_values:
            if self.hero_damage_range[0] <= value <= self.hero_damage_range[1]:
                return value
        return 0
    
    def _extract_tower_damage(self, damage_values: List[int]) -> int:
        """Extract tower damage (usually smaller than hero damage)."""
        for value in damage_values:
            if self.tower_damage_range[0] <= value <= self.tower_damage_range[1]:
                return value
        return 0
    
    def _extract_damage_taken(self, damage_values: List[int]) -> int:
        """Extract damage taken (usually the second largest value)."""
        if len(damage_values) >= 2:
            return damage_values[1]  # Second largest
        return 0
    
    def _extract_teamfight_participation(self, ocr_results: List) -> float:
        """Extract teamfight participation percentage."""
        for bbox, text, confidence in ocr_results:
            # Look for percentage values
            percentage_match = self.percentage_pattern.search(text)
            if percentage_match:
                percentage = float(percentage_match.group(1))
                if 0 <= percentage <= 100:  # Valid percentage range
                    return percentage
        return 0.0
    
    def _extract_gpm(self, ocr_results: List) -> int:
        """Extract gold per minute."""
        for bbox, text, confidence in ocr_results:
            # Look for GPM values (usually 3-5 digits)
            gpm_match = self.gpm_pattern.search(text)
            if gpm_match:
                gpm = int(gpm_match.group(1))
                if self.gpm_range[0] <= gpm <= self.gpm_range[1]:
                    return gpm
        return 0
    
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
    
    def _calculate_confidence(self, ocr_results: List, target_ign: str, damage_values: List[int]) -> float:
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
            
            # Bonus for finding damage values
            if damage_values:
                avg_confidence += 0.1
            
            # Bonus for finding hero damage in reasonable range
            hero_damage = self._extract_hero_damage(damage_values)
            if hero_damage > 0:
                avg_confidence += 0.1
            
            return min(1.0, avg_confidence)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def _extract_text_roi_optimized(self, processed_region: np.ndarray) -> List[str]:
        """
        Extract text using ROI-specific OCR with percentage and numbers optimization.
        Implements OCR-Mission-2.md requirement for numeric-only parsing.
        """
        try:
            from backend.ocr.ocr_reader import extract_text_optimized
            
            # Standard text extraction
            texts = extract_text_optimized(processed_region)
            
            # Apply ROI binarization for percentage and damage values
            roi_texts = self._extract_damage_roi(processed_region)
            
            # Combine results, preferring ROI-extracted values
            combined_texts = []
            for text in texts:
                # If text contains numbers or percentages, try to get better version from ROI
                if re.search(r'[\d%,]', text):
                    roi_version = self._get_best_roi_match(text, roi_texts)
                    combined_texts.append(roi_version if roi_version else text)
                else:
                    combined_texts.append(text)
            
            # Add any ROI-only values that weren't matched
            for roi_text in roi_texts:
                if not any(roi_text in combined for combined in combined_texts):
                    combined_texts.append(roi_text)
            
            return combined_texts
            
        except Exception as e:
            logger.error(f"Error in ROI-optimized text extraction: {e}")
            return []
    
    def _extract_damage_roi(self, processed_region: np.ndarray) -> List[str]:
        """Extract damage values and percentages from ROI using specialized allowlist."""
        try:
            # Configure allowlist for damage values (digits, commas, percentages)
            config = '--psm 8 -c tessedit_char_whitelist=0123456789,%.'
            
            # Use Tesseract with damage-focused allowlist
            import pytesseract
            damage_text = pytesseract.image_to_string(processed_region, config=config)
            
            # Split and clean damage-focused results
            damage_texts = []
            for line in damage_text.strip().split('\n'):
                cleaned = re.sub(r'[^\d%,.]', '', line.strip())
                if cleaned and (re.search(r'\d', cleaned) or '%' in cleaned):
                    damage_texts.append(cleaned)
            
            return damage_texts
            
        except Exception as e:
            logger.debug(f"Error in damage ROI extraction: {e}")
            return []
    
    def _get_best_roi_match(self, original_text: str, roi_texts: List[str]) -> Optional[str]:
        """Get best ROI match for original text containing numbers/percentages."""
        try:
            # Extract numbers from original
            original_numbers = re.findall(r'\d+(?:,\d{3})*', original_text)
            original_percentages = re.findall(r'\d+(?:\.\d+)?%', original_text)
            
            if not original_numbers and not original_percentages:
                return None
            
            # Find ROI text with matching pattern
            for roi_text in roi_texts:
                roi_numbers = re.findall(r'\d+(?:,\d{3})*', roi_text)
                roi_percentages = re.findall(r'\d+(?:\.\d+)?%', roi_text)
                
                # Match by number count and percentage presence
                if (len(roi_numbers) == len(original_numbers) and 
                    bool(roi_percentages) == bool(original_percentages)):
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
    
    def _extract_damage_from_ocr_enhanced(self, ocr_results: List, target_ign: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced damage extraction with improved noise handling and percentage tolerance.
        Implements hardened regex + normalization from OCR-Mission-2.md and OCR-Mission-5.md.
        """
        try:
            # Combine all text and normalize
            all_text = " ".join([result[1] for result in ocr_results])
            
            # OCR Mission 5: Normalize percentage tokens before text normalization
            from backend.ocr.robustness import adaptive_normalizer
            percentage_normalized_text = adaptive_normalizer.normalize_percentage_tokens(all_text)
            normalized_text = self._normalize_text_for_matching(percentage_normalized_text)
            
            logger.debug(f"Normalized damage OCR text: {normalized_text}")
            logger.debug(f"Percentage normalized text: {percentage_normalized_text}")
            
            # Extract damage values with enhanced validation
            damage_values = self._extract_damage_values_enhanced(ocr_results)
            
            if not damage_values:
                logger.warning("No valid damage values found in enhanced OCR results")
                return None
            
            # Extract hero name with enhanced matching
            hero = self._extract_hero_name_enhanced(ocr_results, target_ign)
            
            # Extract specific damage types with % tolerance
            hero_damage = self._extract_hero_damage_enhanced(damage_values)
            tower_damage = self._extract_tower_damage_enhanced(damage_values)
            damage_taken = self._extract_damage_taken_enhanced(damage_values)
            
            # Extract percentages with improved tolerance (using percentage-normalized text)
            hero_damage_pct = self._extract_hero_damage_percentage_enhanced(percentage_normalized_text)
            turret_damage_pct = self._extract_turret_damage_percentage_enhanced(percentage_normalized_text)
            taken_damage_pct = self._extract_taken_damage_percentage_enhanced(percentage_normalized_text)
            
            # Extract teamfight participation and GPM
            teamfight_participation = self._extract_teamfight_participation_enhanced(ocr_results)
            gpm = self._extract_gpm_enhanced(ocr_results)
            
            # Calculate enhanced confidence
            confidence = self._calculate_confidence_enhanced(ocr_results, target_ign, damage_values)
            
            return {
                'hero': hero,
                'hero_damage': hero_damage,
                'tower_damage': tower_damage,
                'damage_taken': damage_taken,
                'hero_damage_pct': hero_damage_pct,
                'turret_damage_pct': turret_damage_pct,
                'taken_damage_pct': taken_damage_pct,
                'teamfight_participation': teamfight_participation,
                'gold_per_minute': gpm,
                'confidence': confidence,
                'raw_text': all_text,
                'percentage_normalized_text': percentage_normalized_text,
                'normalized_text': normalized_text,
                'all_damage_values': damage_values
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced damage extraction: {e}")
            return None
    
    def _extract_damage_values_enhanced(self, ocr_results: List) -> List[int]:
        """Enhanced damage value extraction with better validation."""
        damage_values = []
        
        for bbox, text, confidence in ocr_results:
            # Normalize text for better number extraction
            normalized_text = self._normalize_text_for_matching(text)
            
            # Find all numbers with comma formatting
            numbers = re.findall(r'\d{1,3}(?:,\d{3})*', normalized_text)
            for num_str in numbers:
                try:
                    # Remove commas and convert to int
                    num = int(num_str.replace(',', ''))
                    # Enhanced range validation
                    if 50 <= num <= 1000000:  # More flexible damage range
                        damage_values.append(num)
                except ValueError:
                    continue
            
            # Also try to extract plain numbers without commas
            plain_numbers = re.findall(r'\d{4,6}', normalized_text)
            for num_str in plain_numbers:
                try:
                    num = int(num_str)
                    if 50 <= num <= 1000000:
                        damage_values.append(num)
                except ValueError:
                    continue
        
        return sorted(damage_values, reverse=True)  # Sort descending
    
    def _extract_hero_damage_enhanced(self, damage_values: List[int]) -> int:
        """Enhanced hero damage extraction with flexible range."""
        for value in damage_values:
            if 500 <= value <= 500000:  # More flexible range
                return value
        return 0
    
    def _extract_tower_damage_enhanced(self, damage_values: List[int]) -> int:
        """Enhanced tower damage extraction."""
        for value in damage_values:
            if self.tower_damage_range[0] <= value <= self.tower_damage_range[1]:
                return value
        return 0
    
    def _extract_damage_taken_enhanced(self, damage_values: List[int]) -> int:
        """Enhanced damage taken extraction."""
        if len(damage_values) >= 2:
            return damage_values[1]  # Second largest
        elif len(damage_values) == 1:
            # If only one value, assume it's damage taken if in reasonable range
            value = damage_values[0]
            if 1000 <= value <= 200000:
                return value
        return 0
    
    def _extract_hero_damage_percentage(self, ocr_results: List) -> float:
        """Extract hero damage percentage with OCR-Mission-2.md % tolerance."""
        return self._extract_percentage_by_position(ocr_results, 0)
    
    def _extract_turret_damage_percentage(self, ocr_results: List) -> float:
        """Extract turret damage percentage."""
        return self._extract_percentage_by_position(ocr_results, 1)
    
    def _extract_taken_damage_percentage(self, ocr_results: List) -> float:
        """Extract taken damage percentage."""
        return self._extract_percentage_by_position(ocr_results, 2)
    
    def _extract_percentage_by_position(self, ocr_results: List, position: int) -> float:
        """Extract percentage value by expected position."""
        percentages = []
        
        for bbox, text, confidence in ocr_results:
            # Find percentage values with tolerance
            percentage_matches = re.findall(r'(\d+(?:\.\d+)?)%', text)
            for match in percentage_matches:
                try:
                    percentage = float(match)
                    if 0 <= percentage <= 100:  # Valid percentage range
                        percentages.append(percentage)
                except ValueError:
                    continue
        
        # Return percentage by position if available
        if len(percentages) > position:
            return percentages[position]
        
        return 0.0
    
    def _extract_hero_damage_percentage_enhanced(self, normalized_text: str) -> float:
        """Extract hero damage percentage with OCR Mission 5 tolerance."""
        try:
            # Look for percentage values in normalized text
            percentage_matches = re.findall(r'(\d+(?:\.\d+)?)%', normalized_text)
            for match in percentage_matches:
                try:
                    percentage = float(match)
                    if 0 <= percentage <= 100:
                        return percentage
                except ValueError:
                    continue
            return 0.0
        except Exception as e:
            logger.debug(f"Error extracting hero damage percentage: {e}")
            return 0.0
    
    def _extract_turret_damage_percentage_enhanced(self, normalized_text: str) -> float:
        """Extract turret damage percentage with OCR Mission 5 tolerance."""
        try:
            # Look for second percentage value (turret damage is usually second)
            percentage_matches = re.findall(r'(\d+(?:\.\d+)?)%', normalized_text)
            if len(percentage_matches) >= 2:
                try:
                    percentage = float(percentage_matches[1])
                    if 0 <= percentage <= 100:
                        return percentage
                except ValueError:
                    pass
            return 0.0
        except Exception as e:
            logger.debug(f"Error extracting turret damage percentage: {e}")
            return 0.0
    
    def _extract_taken_damage_percentage_enhanced(self, normalized_text: str) -> float:
        """Extract taken damage percentage with OCR Mission 5 tolerance."""
        try:
            # Look for third percentage value (taken damage is usually third)
            percentage_matches = re.findall(r'(\d+(?:\.\d+)?)%', normalized_text)
            if len(percentage_matches) >= 3:
                try:
                    percentage = float(percentage_matches[2])
                    if 0 <= percentage <= 100:
                        return percentage
                except ValueError:
                    pass
            return 0.0
        except Exception as e:
            logger.debug(f"Error extracting taken damage percentage: {e}")
            return 0.0
    
    def _extract_teamfight_participation_enhanced(self, ocr_results: List) -> float:
        """Enhanced teamfight participation extraction."""
        for bbox, text, confidence in ocr_results:
            # Look for percentage values that could be teamfight participation
            percentage_matches = re.findall(r'(\d+(?:\.\d+)?)%', text)
            for match in percentage_matches:
                try:
                    percentage = float(match)
                    # Teamfight participation is usually higher (20-100%)
                    if 20 <= percentage <= 100:
                        return percentage
                except ValueError:
                    continue
        return 0.0
    
    def _extract_gpm_enhanced(self, ocr_results: List) -> int:
        """Enhanced GPM extraction with better validation."""
        gpm_candidates = []
        
        for bbox, text, confidence in ocr_results:
            # Look for GPM values (usually 3-5 digits)
            numbers = re.findall(r'\b(\d{3,5})\b', text)
            for num_str in numbers:
                try:
                    gpm = int(num_str)
                    if self.gpm_range[0] <= gpm <= self.gpm_range[1]:
                        gpm_candidates.append((gpm, confidence))
                except ValueError:
                    continue
        
        # Return highest confidence GPM
        if gpm_candidates:
            best_gpm = max(gpm_candidates, key=lambda x: x[1])
            return best_gpm[0]
        
        return 0
    
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
    
    def _calculate_confidence_enhanced(self, ocr_results: List, target_ign: str, damage_values: List[int]) -> float:
        """Enhanced confidence calculation with damage-specific factors."""
        try:
            if not ocr_results:
                return 0.0
            
            # Base OCR quality confidence
            base_confidence = sum(result[2] for result in ocr_results) / len(ocr_results)
            
            # IGN matching bonus
            normalized_ign = self._normalize_text_for_matching(target_ign)
            all_text = " ".join([result[1] for result in ocr_results])
            normalized_text = self._normalize_text_for_matching(all_text)
            ign_bonus = 0.2 if normalized_ign in normalized_text else 0.0
            
            # Damage values bonus
            damage_bonus = 0.15 if damage_values else 0.0
            
            # Percentage bonus (damage view should have percentages)
            percentage_bonus = 0.1 if any('%' in result[1] for result in ocr_results) else 0.0
            
            # Data completeness bonus
            completeness_bonus = 0.1 if len(ocr_results) >= 4 else 0.0
            
            # Noise penalty
            noise_penalty = len(re.findall(r'[^\w\s%,.]', normalized_text)) * 0.01
            
            final_confidence = base_confidence + ign_bonus + damage_bonus + percentage_bonus + completeness_bonus - noise_penalty
            
            return min(1.0, max(0.0, final_confidence))
            
        except Exception as e:
            logger.error(f"Error in enhanced confidence calculation: {e}")
            return 0.0

# Global instance
damage_parser = RowAgnosticDamageParser()
