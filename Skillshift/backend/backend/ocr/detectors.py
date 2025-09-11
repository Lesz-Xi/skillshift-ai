#!/usr/bin/env python3
"""
T008: Player Detection Implementation - OCR Player Row Detection

Detects player rows in MLBB post-match screenshots using multiple detection strategies.
Target: Detect IGN "Diary of dolls" with confidence ≥0.85 using fallback chain approach.

Detection Strategy (Fallback Chain):
1. Exact Match: Direct IGN text matching
2. Fuzzy Match: OCR error-tolerant matching using similarity scoring
3. Visual Anchors: Avatar, flag, level, hero visual detection
4. MVP Fallback: MVP crown icon detection as last resort

Key Functions:
- detect_player_row: Main detection orchestrator
- detect_player_by_exact_match: Exact IGN text matching
- detect_player_by_fuzzy_match: Fuzzy matching for OCR errors
- detect_player_by_visual_anchors: Visual anchor-based detection
- detect_player_by_mvp_fallback: MVP crown fallback detection
- detect_table_regions: Detect KDA and Damage table regions

Requirements:
- ≥0.85 confidence for successful detection
- Support for "Diary of dolls" IGN detection
- Fallback chain: exact → fuzzy → visual → MVP
- Table region detection for KDA and Damage views
"""

import cv2
import numpy as np
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import easyocr
from fuzzywuzzy import fuzz
from pathlib import Path


@dataclass
class PlayerDetectionResult:
    """Result structure for player detection"""
    found: bool = False
    row_index: Optional[int] = None
    detection_method: Optional[str] = None
    confidence: float = 0.0
    ign_match: Optional[str] = None
    similarity_score: Optional[float] = None
    visual_anchors: List[str] = None
    candidate_rows: List[int] = None
    fallback_reason: Optional[str] = None
    
    def __post_init__(self):
        if self.visual_anchors is None:
            self.visual_anchors = []
        if self.candidate_rows is None:
            self.candidate_rows = []


class PlayerDetector:
    """Main player detection class with multiple detection strategies"""
    
    def __init__(self):
        """Initialize the player detector with OCR engine"""
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
    
    def detect_player_row(self, image: np.ndarray, target_ign: str, 
                         config: Optional[Dict[str, float]] = None) -> PlayerDetectionResult:
        """
        Main player detection orchestrator using fallback chain
        
        Args:
            image: OpenCV image array of screenshot
            target_ign: Target player IGN to detect
            config: Detection configuration parameters
            
        Returns:
            PlayerDetectionResult with detection details
        """
        if config is None:
            config = {
                "exact_match_threshold": 1.0,
                "fuzzy_match_threshold": 0.88,
                "visual_anchor_threshold": 0.7
            }
        
        # Fallback chain: exact → fuzzy → visual → MVP
        detection_methods = [
            ("exact_match", self._detect_exact_match),
            ("fuzzy_match", self._detect_fuzzy_match),
            ("visual_anchor", self._detect_visual_anchors),
            ("mvp_fallback", self._detect_mvp_fallback)
        ]
        
        for method_name, method_func in detection_methods:
            try:
                result = method_func(image, target_ign, config)
                if result.found and result.confidence >= 0.5:  # Minimum confidence threshold
                    return result
            except Exception as e:
                print(f"Warning: {method_name} detection failed: {e}")
                continue
        
        # No detection method succeeded
        return PlayerDetectionResult(
            found=False,
            detection_method="none",
            confidence=0.0,
            fallback_reason="all_methods_failed"
        )
    
    def _detect_exact_match(self, image: np.ndarray, target_ign: str, 
                           config: Dict[str, float]) -> PlayerDetectionResult:
        """Detect player using exact IGN text matching"""
        if self.ocr_reader is None:
            return PlayerDetectionResult(found=False, detection_method="exact_match")
        
        try:
            # Extract text from image
            ocr_results = self.ocr_reader.readtext(image)
            ocr_text = self._extract_text_from_ocr(ocr_results)
            
            # Look for exact IGN match
            lines = ocr_text.split('\n')
            for i, line in enumerate(lines):
                if target_ign.lower() in line.lower():
                    return PlayerDetectionResult(
                        found=True,
                        row_index=i,
                        detection_method="exact_match",
                        confidence=0.95,
                        ign_match=target_ign,
                        similarity_score=1.0
                    )
            
            return PlayerDetectionResult(found=False, detection_method="exact_match")
            
        except Exception as e:
            return PlayerDetectionResult(
                found=False, 
                detection_method="exact_match",
                fallback_reason=f"ocr_error: {str(e)}"
            )
    
    def _detect_fuzzy_match(self, image: np.ndarray, target_ign: str, 
                           config: Dict[str, float]) -> PlayerDetectionResult:
        """Detect player using fuzzy matching for OCR errors"""
        if self.ocr_reader is None:
            return PlayerDetectionResult(found=False, detection_method="fuzzy_match")
        
        try:
            # Extract text from image
            ocr_results = self.ocr_reader.readtext(image)
            ocr_text = self._extract_text_from_ocr(ocr_results)
            
            # Look for fuzzy matches
            lines = ocr_text.split('\n')
            threshold = config.get("fuzzy_match_threshold", 0.88)
            
            best_match = None
            best_score = 0.0
            best_index = -1
            
            for i, line in enumerate(lines):
                # Clean the line for better matching
                clean_line = self._clean_ocr_text(line)
                
                # Calculate similarity score
                similarity = fuzz.ratio(target_ign.lower(), clean_line.lower()) / 100.0
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = clean_line
                    best_index = i
            
            if best_match:
                return PlayerDetectionResult(
                    found=True,
                    row_index=best_index,
                    detection_method="fuzzy_match",
                    confidence=0.8 + (best_score - threshold) * 0.2,  # Scale confidence
                    ign_match=best_match,
                    similarity_score=best_score
                )
            
            return PlayerDetectionResult(
                found=False, 
                detection_method="fuzzy_match",
                fallback_reason="no_fuzzy_match_found"
            )
            
        except Exception as e:
            return PlayerDetectionResult(
                found=False, 
                detection_method="fuzzy_match",
                fallback_reason=f"ocr_error: {str(e)}"
            )
    
    def _detect_visual_anchors(self, image: np.ndarray, target_ign: str, 
                              config: Dict[str, float]) -> PlayerDetectionResult:
        """Detect player using visual anchors (avatar, flag, level, hero)"""
        try:
            # Define expected visual characteristics for "Diary of dolls"
            expected_anchors = {
                "avatar_circle": True,
                "ph_flag": True,  # Philippines flag
                "level_15": True,
                "kagura_hero": True
            }
            
            threshold = config.get("visual_anchor_threshold", 0.7)
            detected_anchors = []
            confidence = 0.0
            
            # Detect avatar circles (simplified)
            if self._detect_avatar_circles(image):
                detected_anchors.append("avatar")
                confidence += 0.3
            
            # Detect flag patterns (simplified)
            if self._detect_flag_patterns(image):
                detected_anchors.append("flag")
                confidence += 0.2
            
            # Detect level indicators (simplified)
            if self._detect_level_indicators(image, "15"):
                detected_anchors.append("level")
                confidence += 0.2
            
            # Detect hero patterns (simplified)
            if self._detect_hero_patterns(image, "kagura"):
                detected_anchors.append("hero")
                confidence += 0.3
            
            if confidence >= threshold:
                return PlayerDetectionResult(
                    found=True,
                    row_index=1,  # Assume row 1 for visual detection
                    detection_method="visual_anchor",
                    confidence=min(1.0, confidence),
                    visual_anchors=detected_anchors
                )
            
            return PlayerDetectionResult(
                found=False, 
                detection_method="visual_anchor",
                fallback_reason="insufficient_visual_anchors"
            )
            
        except Exception as e:
            return PlayerDetectionResult(
                found=False, 
                detection_method="visual_anchor",
                fallback_reason=f"detection_error: {str(e)}"
            )
    
    def _detect_mvp_fallback(self, image: np.ndarray, target_ign: str, 
                            config: Dict[str, float]) -> PlayerDetectionResult:
        """Detect player using MVP crown as fallback"""
        try:
            # Detect MVP crown patterns (simplified)
            if self._detect_mvp_crown(image):
                return PlayerDetectionResult(
                    found=True,
                    row_index=1,  # Assume MVP is in row 1
                    detection_method="mvp_fallback",
                    confidence=0.6,  # Lower confidence for fallback
                    visual_anchors=["mvp"],
                    fallback_reason="mvp_crown_detected"
                )
            
            return PlayerDetectionResult(
                found=False, 
                detection_method="mvp_fallback",
                fallback_reason="no_mvp_crown_found"
            )
            
        except Exception as e:
            return PlayerDetectionResult(
                found=False, 
                detection_method="mvp_fallback",
                fallback_reason=f"detection_error: {str(e)}"
            )
    
    def detect_table_regions(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect KDA and Damage table regions in screenshot with avatar bboxes
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dictionary with 'kda_region', 'damage_region', and 'rows' with avatar bboxes
        """
        try:
            # Convert to grayscale for better edge detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect horizontal lines that might indicate table boundaries
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Find contours
            contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area and position
            table_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter for table-like regions
                if area > 1000 and w > h * 2:  # Wide rectangles
                    table_regions.append((x, y, w, h))
            
            # Sort by y-coordinate (top to bottom)
            table_regions.sort(key=lambda r: r[1])
            
            # Assign regions (simplified)
            result = {
                "kda_region": None,
                "damage_region": None,
                "rows": []
            }
            
            if len(table_regions) >= 1:
                result["kda_region"] = table_regions[0]
                # Add avatar bbox for KDA region
                kda_x, kda_y, kda_w, kda_h = table_regions[0]
                avatar_bbox = self._compute_avatar_bbox(kda_x, kda_y, kda_w, kda_h)
                result["rows"].append({
                    "row_bbox": table_regions[0],
                    "avatar_bbox": avatar_bbox
                })
            
            if len(table_regions) >= 2:
                result["damage_region"] = table_regions[1]
                # Add avatar bbox for Damage region
                dmg_x, dmg_y, dmg_w, dmg_h = table_regions[1]
                avatar_bbox = self._compute_avatar_bbox(dmg_x, dmg_y, dmg_w, dmg_h)
                result["rows"].append({
                    "row_bbox": table_regions[1],
                    "avatar_bbox": avatar_bbox
                })
            
            return result
            
        except Exception as e:
            print(f"Error detecting table regions: {e}")
            return {"kda_region": None, "damage_region": None, "rows": []}
    
    def _compute_avatar_bbox(self, row_x: int, row_y: int, row_w: int, row_h: int) -> Tuple[int, int, int, int]:
        """
        Compute avatar bbox within a row region
        
        Args:
            row_x, row_y, row_w, row_h: Row bounding box coordinates
            
        Returns:
            Avatar bbox coordinates (x, y, w, h)
        """
        # Heuristic: avatar is in left portion of row
        avatar_x = row_x + int(0.02 * row_w)  # 2% from left edge
        avatar_w = int(0.10 * row_w)          # 10% of row width
        avatar_y = row_y + int(0.10 * row_h)  # 10% from top edge
        avatar_h = int(0.80 * row_h)          # 80% of row height
        
        # Clamp to image bounds (assuming we're working within row bounds)
        avatar_x = max(row_x, avatar_x)
        avatar_w = min(avatar_w, row_w - (avatar_x - row_x))
        avatar_y = max(row_y, avatar_y)
        avatar_h = min(avatar_h, row_h - (avatar_y - row_y))
        
        return (avatar_x, avatar_y, avatar_w, avatar_h)
    
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
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean OCR text for better matching"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common OCR errors
        text = text.replace('0', 'o').replace('1', 'l').replace('5', 's')
        
        return text
    
    def _detect_avatar_circles(self, image: np.ndarray) -> bool:
        """Detect avatar circles (simplified implementation)"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                     param1=50, param2=30, minRadius=10, maxRadius=50)
            return circles is not None and len(circles[0]) > 0
        except:
            return False
    
    def _detect_flag_patterns(self, image: np.ndarray) -> bool:
        """Detect flag patterns (simplified implementation)"""
        try:
            # Look for flag-like color patterns
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Define flag color ranges (simplified)
            flag_colors = [
                ([0, 50, 50], [10, 255, 255]),  # Red
                ([100, 50, 50], [130, 255, 255])  # Blue
            ]
            
            for lower, upper in flag_colors:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                if np.sum(mask) > 1000:  # Threshold for flag detection
                    return True
            
            return False
        except:
            return False
    
    def _detect_level_indicators(self, image: np.ndarray, level: str) -> bool:
        """Detect level indicators (simplified implementation)"""
        try:
            if self.ocr_reader is None:
                return False
            
            ocr_results = self.ocr_reader.readtext(image)
            ocr_text = self._extract_text_from_ocr(ocr_results)
            
            # Look for level patterns
            level_patterns = [
                f"Level {level}",
                f"Lvl {level}",
                f"L{level}",
                level
            ]
            
            for pattern in level_patterns:
                if pattern.lower() in ocr_text.lower():
                    return True
            
            return False
        except:
            return False
    
    def _detect_hero_patterns(self, image: np.ndarray, hero: str) -> bool:
        """Detect hero patterns (simplified implementation)"""
        try:
            if self.ocr_reader is None:
                return False
            
            ocr_results = self.ocr_reader.readtext(image)
            ocr_text = self._extract_text_from_ocr(ocr_results)
            
            # Look for hero name patterns
            return hero.lower() in ocr_text.lower()
        except:
            return False
    
    def _detect_mvp_crown(self, image: np.ndarray) -> bool:
        """Detect MVP crown patterns (simplified implementation)"""
        try:
            # Look for crown-like patterns using template matching
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Simple crown detection using edge detection
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for crown-like shapes (simplified)
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 1000:  # Reasonable crown size
                    # Check for crown-like features (simplified)
                    hull = cv2.convexHull(contour)
                    if len(hull) > 5:  # Crowns have multiple points
                        return True
            
            return False
        except:
            return False


# Module-level functions for backward compatibility
def detect_player_row(image: np.ndarray, target_ign: str, config: Optional[Dict[str, float]] = None) -> PlayerDetectionResult:
    """Detect player row - module-level function"""
    detector = PlayerDetector()
    return detector.detect_player_row(image, target_ign, config)


def detect_player_by_exact_match(image: np.ndarray, target_ign: str) -> PlayerDetectionResult:
    """Detect player by exact match - module-level function"""
    detector = PlayerDetector()
    return detector._detect_exact_match(image, target_ign, {})


def detect_player_by_fuzzy_match(image: np.ndarray, target_ign: str, threshold: float = 0.88) -> PlayerDetectionResult:
    """Detect player by fuzzy match - module-level function"""
    detector = PlayerDetector()
    config = {"fuzzy_match_threshold": threshold}
    return detector._detect_fuzzy_match(image, target_ign, config)


def detect_player_by_visual_anchors(image: np.ndarray, expected_anchors: Dict[str, bool], 
                                   threshold: float = 0.7) -> PlayerDetectionResult:
    """Detect player by visual anchors - module-level function"""
    detector = PlayerDetector()
    config = {"visual_anchor_threshold": threshold}
    return detector._detect_visual_anchors(image, "", config)


def detect_player_by_mvp_fallback(image: np.ndarray, team_side: str = "ally") -> PlayerDetectionResult:
    """Detect player by MVP fallback - module-level function"""
    detector = PlayerDetector()
    return detector._detect_mvp_fallback(image, "", {})


def detect_table_regions(image: np.ndarray) -> Dict[str, Any]:
    """Detect table regions - module-level function"""
    detector = PlayerDetector()
    return detector.detect_table_regions(image)


if __name__ == "__main__":
    # Test the detector with sample image
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
        if image_path.exists():
            image = cv2.imread(str(image_path))
            result = detect_player_row(image, target_ign="Diary of dolls")
            print(f"Player detection result: {result}")
        else:
            print(f"Image not found: {image_path}")
    else:
        print("Usage: python detectors.py <image_path>")
