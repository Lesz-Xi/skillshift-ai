#!/usr/bin/env python3
"""
T010: Damage Parser Implementation - OCR Damage View Parsing

Extracts damage-related statistics from MLBB post-match damage view screenshots.
Target: Extract hero damage percentage, teamfight participation for "Diary of dolls" → Kagura

Key Functions:
- parse_damage_view: Main damage view parsing orchestrator
- extract_hero_damage_percentage: Extract damage percentage from damage view
- extract_teamfight_participation: Extract teamfight participation data
- DamageViewResult: Data structure for damage parsing results

Requirements:
- ≥0.7 confidence for damage metrics
- Handle "No numeric data found" errors gracefully
- Support for IMG_1768 (Damage view) screenshot format
"""

import cv2
import numpy as np
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import easyocr
from pathlib import Path


@dataclass
class DamageViewResult:
    """Result structure for damage view parsing"""
    player_ign: Optional[str] = None
    hero: Optional[str] = None
    hero_damage_pct: Optional[float] = None
    teamfight_participation: Optional[float] = None
    confidence: float = 0.0
    data_source: str = "damage_view"
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class DamageViewParser:
    """Main damage view parser class"""
    
    def __init__(self):
        """Initialize the damage parser with OCR engine"""
        self.ocr_reader = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize EasyOCR reader (lazy loading)"""
        try:
            # Fix PIL.Image.ANTIALIAS deprecation warning
            import PIL.Image
            if not hasattr(PIL.Image, 'ANTIALIAS'):
                PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
            
            self.ocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception as e:
            print(f"Warning: Failed to initialize OCR: {e}")
            self.ocr_reader = None
    
    def parse_damage_view(self, image: np.ndarray, player_row_index: int, target_ign: str) -> DamageViewResult:
        """
        Parse damage view screenshot to extract damage statistics
        
        Args:
            image: OpenCV image array of damage view screenshot
            player_row_index: Index of player row in damage table
            target_ign: Target player IGN to locate
            
        Returns:
            DamageViewResult with extracted damage data
        """
        result = DamageViewResult()
        result.player_ign = target_ign
        
        try:
            # Use row-agnostic geometry to focus OCR on the correct row
            try:
                from backend.ocr.detectors import detect_table_regions
                regions = detect_table_regions(image, target_ign=target_ign)
                rows = regions.get("rows", [])
                assigned = regions.get("assigned_row_index")
                use_index = player_row_index if player_row_index is not None else assigned
                ocr_image = image
                if use_index is not None and 0 <= use_index < len(rows):
                    rb = rows[use_index].get("row_bbox")
                    if rb:
                        x, y, w, h = rb
                        ocr_image = image[y:y+h, x:x+w]
            except Exception:
                ocr_image = image
            # Perform OCR on the image
            if self.ocr_reader is None:
                result.error_message = "OCR engine not initialized"
                result.confidence = 0.0
                return result
            
            # Extract text from focused crop (row) when available
            ocr_results = self.ocr_reader.readtext(ocr_image)
            ocr_text = self._extract_text_from_ocr(ocr_results)
            
            if not ocr_text.strip():
                result.error_message = "No text detected in damage view"
                result.confidence = 0.0
                return result
            
            # Extract damage percentage
            damage_pct = self.extract_hero_damage_percentage(
                ocr_image, player_row_index if player_row_index is not None else (assigned if 'assigned' in locals() else 0), target_ign, ocr_text
            )
            result.hero_damage_pct = damage_pct
            
            # Extract teamfight participation
            teamfight_pct = self.extract_teamfight_participation(
                ocr_image, player_row_index if player_row_index is not None else (assigned if 'assigned' in locals() else 0), target_ign, ocr_text
            )
            result.teamfight_participation = teamfight_pct
            
            # Calculate overall confidence
            result.confidence = self._calculate_confidence(result)
            
            # Add warnings for missing data
            if result.hero_damage_pct is None:
                result.warnings.append("Hero damage percentage not found")
            if result.teamfight_participation is None:
                result.warnings.append("Teamfight participation not found")
            
        except Exception as e:
            result.error_message = f"Error parsing damage view: {str(e)}"
            result.confidence = 0.0
        
        return result
    
    def extract_hero_damage_percentage(self, image: np.ndarray, player_row_index: int, 
                                     target_ign: str, ocr_text: str = None) -> Optional[float]:
        """
        Extract hero damage percentage from damage view
        
        Args:
            image: OpenCV image array
            player_row_index: Player row index in damage table
            target_ign: Target player IGN
            ocr_text: Pre-extracted OCR text (optional)
            
        Returns:
            Hero damage percentage (0-100) or None if not found
        """
        try:
            if ocr_text is None:
                if self.ocr_reader is None:
                    return None
                ocr_results = self.ocr_reader.readtext(image)
                ocr_text = self._extract_text_from_ocr(ocr_results)
            
            # Look for damage percentage patterns
            damage_patterns = [
                r'(\d+(?:\.\d+)?)\s*%',  # Basic percentage pattern
                r'(\d+(?:\.\d+)?)\s*damage',  # "X damage" pattern
                r'damage[:\s]*(\d+(?:\.\d+)?)',  # "damage: X" pattern
                r'(\d+(?:\.\d+)?)\s*hero\s*damage',  # "X hero damage" pattern
            ]
            
            for pattern in damage_patterns:
                matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                if matches:
                    # Take the first reasonable percentage
                    for match in matches:
                        try:
                            value = float(match)
                            if 0 <= value <= 100:  # Valid percentage range
                                return value
                        except ValueError:
                            continue
            
            # If no percentage found, try to extract from damage numbers
            damage_numbers = self._extract_damage_numbers(ocr_text)
            if damage_numbers:
                # Calculate percentage based on total damage
                total_damage = sum(damage_numbers)
                if total_damage > 0 and len(damage_numbers) > 1:
                    # Assume the largest number is the player's damage
                    player_damage = max(damage_numbers)
                    percentage = (player_damage / total_damage) * 100
                    if 0 <= percentage <= 100:
                        return percentage
            
            return None
            
        except Exception as e:
            print(f"Error extracting hero damage percentage: {e}")
            return None
    
    def extract_teamfight_participation(self, image: np.ndarray, player_row_index: int,
                                      target_ign: str, ocr_text: str = None) -> Optional[float]:
        """
        Extract teamfight participation percentage from damage view
        
        Args:
            image: OpenCV image array
            player_row_index: Player row index in damage table
            target_ign: Target player IGN
            ocr_text: Pre-extracted OCR text (optional)
            
        Returns:
            Teamfight participation percentage (0-100) or None if not found
        """
        try:
            if ocr_text is None:
                if self.ocr_reader is None:
                    return None
                ocr_results = self.ocr_reader.readtext(image)
                ocr_text = self._extract_text_from_ocr(ocr_results)
            
            # Look for teamfight participation patterns
            teamfight_patterns = [
                r'(\d+(?:\.\d+)?)\s*%',  # Basic percentage pattern
                r'(\d+(?:\.\d+)?)\s*teamfight',  # "X teamfight" pattern
                r'teamfight[:\s]*(\d+(?:\.\d+)?)',  # "teamfight: X" pattern
                r'participation[:\s]*(\d+(?:\.\d+)?)',  # "participation: X" pattern
            ]
            
            for pattern in teamfight_patterns:
                matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        try:
                            value = float(match)
                            if 0 <= value <= 100:  # Valid percentage range
                                return value
                        except ValueError:
                            continue
            
            return None
            
        except Exception as e:
            print(f"Error extracting teamfight participation: {e}")
            return None
    
    def _extract_text_from_ocr(self, ocr_results: List[Tuple]) -> str:
        """Extract and clean text from OCR results"""
        if not ocr_results:
            return ""
        
        # Sort by y-coordinate to get text in reading order
        sorted_results = sorted(ocr_results, key=lambda x: x[0][0][1])
        
        text_parts = []
        for (bbox, text, confidence) in sorted_results:
            if confidence > 0.5:  # Only include high-confidence text
                text_parts.append(text.strip())
        
        return ' '.join(text_parts)
    
    def _extract_damage_numbers(self, text: str) -> List[float]:
        """Extract damage numbers from text"""
        # Look for large numbers that could be damage values
        number_pattern = r'\b(\d{4,})\b'  # 4+ digit numbers
        matches = re.findall(number_pattern, text)
        
        damage_numbers = []
        for match in matches:
            try:
                value = float(match)
                if 1000 <= value <= 200000:  # Reasonable damage range
                    damage_numbers.append(value)
            except ValueError:
                continue
        
        return damage_numbers
    
    def _calculate_confidence(self, result: DamageViewResult) -> float:
        """Calculate overall confidence based on extracted data"""
        confidence_factors = []
        
        # Base confidence from data availability
        if result.hero_damage_pct is not None:
            confidence_factors.append(0.85)  # 85% for damage data
        if result.teamfight_participation is not None:
            confidence_factors.append(0.15)  # 15% for teamfight data
        
        if not confidence_factors:
            return 0.0
        
        # Average confidence with bonus for multiple data points
        base_confidence = sum(confidence_factors) / len(confidence_factors)
        bonus = 0.3 if len(confidence_factors) > 1 else 0.0
        
        return min(1.0, base_confidence + bonus)


# Module-level functions for backward compatibility
def parse_damage_view(image: np.ndarray, player_row_index: int, target_ign: str) -> DamageViewResult:
    """Parse damage view screenshot - module-level function"""
    parser = DamageViewParser()
    return parser.parse_damage_view(image, player_row_index, target_ign)


def extract_hero_damage_percentage(image: np.ndarray, player_row_index: int, target_ign: str) -> Optional[float]:
    """Extract hero damage percentage - module-level function"""
    parser = DamageViewParser()
    return parser.extract_hero_damage_percentage(image, player_row_index, target_ign)


def extract_teamfight_participation(image: np.ndarray, player_row_index: int, target_ign: str) -> Optional[float]:
    """Extract teamfight participation - module-level function"""
    parser = DamageViewParser()
    return parser.extract_teamfight_participation(image, player_row_index, target_ign)


if __name__ == "__main__":
    # Test the damage parser with sample image
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
        if image_path.exists():
            image = cv2.imread(str(image_path))
            result = parse_damage_view(image, player_row_index=1, target_ign="Diary of dolls")
            print(f"Damage parsing result: {result}")
        else:
            print(f"Image not found: {image_path}")
    else:
        print("Usage: python parsers_damage.py <image_path>")
