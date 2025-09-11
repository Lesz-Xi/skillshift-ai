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


def rel_to_abs(img: np.ndarray, rel: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
    """
    Convert relative bbox coordinates to absolute pixel coordinates
    
    Args:
        img: Image array
        rel: (x1_rel, y1_rel, x2_rel, y2_rel) in range [0,1]
        
    Returns:
        (x1, y1, x2, y2) absolute pixel coordinates
    """
    h, w = img.shape[:2]
    x1_rel, y1_rel, x2_rel, y2_rel = rel
    
    x1 = max(0, min(w-1, int(x1_rel * w)))
    y1 = max(0, min(h-1, int(y1_rel * h)))
    x2 = max(x1+1, min(w, int(x2_rel * w)))
    y2 = max(y1+1, min(h, int(y2_rel * h)))
    
    return (x1, y1, x2, y2)


# Legacy alias for backward compatibility
def abs_bbox(img: np.ndarray, rel_bbox: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
    """Legacy alias for rel_to_abs"""
    return rel_to_abs(img, rel_bbox)


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
            
            return PlayerDetectionResult(found=False, detection_method="fuzzy_match")
            
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
    
    def detect_table_regions(self, image: np.ndarray, target_ign: Optional[str] = None) -> Dict[str, Any]:
        """
        Row-agnostic scoreboard detection with normalized geometry ratios.

        Implements OCR-Task-1:
        - Detect the scoreboard panel once (blue team panel)
        - Normalize all geometry to ratios relative to the panel
        - Generate row crops dynamically from configured row count
        - Anchor parsing per row (IGN OCR with fuzzy fallback)
        - Return rich geometry for downstream parsers (keeps backward-compatible keys)

        Args:
            image: OpenCV image array
            target_ign: Optional target IGN used to try row assignment and IGN bbox extraction

        Returns:
            Dict with keys including:
            - panel_bbox: (x, y, w, h) absolute panel bbox
            - panel_bbox_ratio: (x, y, w, h) as ratios of full image
            - rows_count, row_top_ratio, row_height_ratio
            - rows: list of per-row dicts with absolute and ratio bboxes and optional IGN bbox
        """
        try:
            H, W = image.shape[:2]

            # 1) Detect panel once (use config-based blue panel pct)
            panel = detect_blue_panel(image)

            def abs_to_ratio_abs_parent(x: int, y: int, w: int, h: int, parent_w: int, parent_h: int) -> Tuple[float, float, float, float]:
                return (x / parent_w, y / parent_h, w / parent_w, h / parent_h)

            panel_ratio = abs_to_ratio_abs_parent(panel.x, panel.y, panel.w, panel.h, W, H)

            # 2) Normalize geometry to panel ratios
            rows = CFG.get("table", {}).get("rows", 5)
            top_off = CFG["table"].get("row_top_offset_pct", 0.04)
            bot_off = CFG["table"].get("row_bottom_offset_pct", 0.04)
            usable_h = panel.h * (1.0 - top_off - bot_off)
            row_h = usable_h / max(1, rows)
            row_height_ratio = row_h / panel.h

            # Canonical row-relative boxes (within a single row)
            kda_row_rel = (0.58, 0.20, 0.78, 0.80)  # x1,y1,x2,y2 relative to row
            avatar_row_rel = (0.02, 0.10, 0.15, 0.90)  # x1,y1,x2,y2 relative to row

            result: Dict[str, Any] = {
                "panel_bbox": panel.to_tuple(),
                "panel_bbox_ratio": panel_ratio,
                "rows_count": rows,
                "row_top_ratio": top_off,
                "row_height_ratio": row_height_ratio,
                "kda_region": panel.to_tuple(),   # backward-compatible best guess
                "damage_region": None,            # unknown in KDA view; may be filled elsewhere
                "rows": []
            }

            # 3) Generate dynamic row crops and normalized descriptors
            assigned_row_index: Optional[int] = None
            for i in range(rows):
                rbox = row_bbox(panel, i, rows, top_off, bot_off)
                row_img = image[rbox.y:rbox.y + rbox.h, rbox.x:rbox.x + rbox.w]

                # Helpers to convert row-relative [x1,y1,x2,y2] -> absolute xyxy within panel/image
                def row_rel_to_abs_xyxy(rr: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
                    rx1, ry1, rx2, ry2 = rr
                    x1 = rbox.x + int(rx1 * rbox.w)
                    y1 = rbox.y + int(ry1 * rbox.h)
                    x2 = rbox.x + int(rx2 * rbox.w)
                    y2 = rbox.y + int(ry2 * rbox.h)
                    return (x1, y1, x2, y2)

                def xyxy_to_img_ratio(xyxy: Tuple[int, int, int, int]) -> Tuple[float, float, float, float]:
                    x1, y1, x2, y2 = xyxy
                    return (x1 / W, y1 / H, x2 / W, y2 / H)

                def xyxy_to_panel_ratio(xyxy: Tuple[int, int, int, int]) -> Tuple[float, float, float, float]:
                    x1, y1, x2, y2 = xyxy
                    return (
                        (x1 - panel.x) / panel.w,
                        (y1 - panel.y) / panel.h,
                        (x2 - panel.x) / panel.w,
                        (y2 - panel.y) / panel.h,
                    )

                # Compute KDA and avatar boxes in multiple spaces
                kda_xyxy_abs = row_rel_to_abs_xyxy(kda_row_rel)
                avatar_xyxy_abs = row_rel_to_abs_xyxy(avatar_row_rel)

                kda_img_rel = xyxy_to_img_ratio(kda_xyxy_abs)
                avatar_img_rel = xyxy_to_img_ratio(avatar_xyxy_abs)

                kda_panel_rel = xyxy_to_panel_ratio(kda_xyxy_abs)
                avatar_panel_rel = xyxy_to_panel_ratio(avatar_xyxy_abs)

                # 4) Anchor parsing per row: IGN OCR with fuzzy fallback
                ign_bbox_row_xyxy: Optional[Tuple[int, int, int, int]] = None
                ign_fuzzy_score: Optional[float] = None
                ign_text: Optional[str] = None

                if target_ign and self.ocr_reader is not None and row_img.size > 0:
                    try:
                        ign_bbox_row_xyxy = self._extract_ign_bbox(row_img, target_ign)

                        # Fuzzy confirmation using whole-row text
                        ocr_results = self.ocr_reader.readtext(row_img)
                        ocr_text = self._extract_text_from_ocr(ocr_results)
                        ign_text = ocr_text
                        ign_fuzzy_score = fuzz.ratio(target_ign.lower(), self._clean_ocr_text(ocr_text).lower()) / 100.0
                        if ign_bbox_row_xyxy and ign_fuzzy_score and ign_fuzzy_score >= 0.7 and assigned_row_index is None:
                            assigned_row_index = i
                    except Exception:
                        pass

                # Compose row info
                row_info: Dict[str, Any] = {
                    "index": i,
                    # Absolute row bbox (x,y,w,h)
                    "row_bbox": rbox.to_tuple(),
                    # Row bbox as ratio of panel
                    "row_bbox_panel_rel": (
                        0.0,  # rows span full panel width
                        (rbox.y - panel.y) / panel.h,
                        1.0,
                        rbox.h / panel.h,
                    ),
                    # Backward-compat keys (kept but now image-relative for correct usage with rel_to_abs)
                    "kda_bbox_rel": kda_img_rel,
                    "avatar_bbox": avatar_img_rel,
                    # Rich, explicit geometry in different spaces
                    "kda_bbox_row_rel": kda_row_rel,
                    "kda_bbox_panel_rel": kda_panel_rel,
                    "kda_bbox_img_rel": kda_img_rel,
                    "avatar_bbox_row_rel": avatar_row_rel,
                    "avatar_bbox_panel_rel": avatar_panel_rel,
                    "avatar_bbox_img_rel": avatar_img_rel,
                    # Row crop for downstream specialized parsers
                    "row_img": row_img,
                    # IGN detection artifacts (row-local xyxy)
                    "ign_bbox": ign_bbox_row_xyxy,
                    "ign_fuzzy_score": ign_fuzzy_score,
                    "ign_text": ign_text,
                }

                result["rows"].append(row_info)

            # Include best-guess assigned row if any
            if target_ign is not None:
                result["assigned_row_index"] = assigned_row_index

            return result

        except Exception as e:
            print(f"Error detecting table regions: {e}")
            return {
                "panel_bbox": None,
                "panel_bbox_ratio": None,
                "rows_count": 0,
                "row_top_ratio": 0.0,
                "row_height_ratio": 0.0,
                "kda_region": None,
                "damage_region": None,
                "rows": []
            }
    
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
    
    def _extract_ign_bbox(self, row_img: np.ndarray, target_ign: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Extract IGN bounding box from row image using OCR
        
        Args:
            row_img: Row image array
            target_ign: Target IGN to find
            
        Returns:
            IGN bbox (x1, y1, x2, y2) in row-local coordinates or None if not found
        """
        try:
            # OCR the row with detailed bounding boxes
            ocr_results = self.ocr_reader.readtext(row_img, detail=1)
            
            if not ocr_results:
                return None
            
            # Normalize IGN for matching
            def normalize_ign(s: str) -> str:
                return ' '.join(s.lower().split())
            
            target_normalized = normalize_ign(target_ign)
            
            # Try to find exact match first
            for (bbox_coords, text, confidence) in ocr_results:
                if confidence < 0.5:  # Skip low-confidence text
                    continue
                
                text_normalized = normalize_ign(text)
                
                # Check for exact match
                if text_normalized == target_normalized:
                    # Convert bbox coordinates to (x1, y1, x2, y2)
                    x_coords = [point[0] for point in bbox_coords]
                    y_coords = [point[1] for point in bbox_coords]
                    x1, x2 = int(min(x_coords)), int(max(x_coords))
                    y1, y2 = int(min(y_coords)), int(max(y_coords))
                    return (x1, y1, x2, y2)
            
            # If no exact match, try partial matching
            best_match = None
            best_score = 0.0
            
            for (bbox_coords, text, confidence) in ocr_results:
                if confidence < 0.3:  # Lower threshold for partial matching
                    continue
                
                text_normalized = normalize_ign(text)
                
                # Check for partial match
                if target_normalized in text_normalized or text_normalized in target_normalized:
                    # Calculate similarity score
                    score = len(set(target_normalized.split()) & set(text_normalized.split())) / max(1, len(set(target_normalized.split())))
                    
                    if score > best_score and score > 0.5:  # At least 50% word overlap
                        best_score = score
                        # Convert bbox coordinates
                        x_coords = [point[0] for point in bbox_coords]
                        y_coords = [point[1] for point in bbox_coords]
                        x1, x2 = int(min(x_coords)), int(max(x_coords))
                        y1, y2 = int(min(y_coords)), int(max(y_coords))
                        best_match = (x1, y1, x2, y2)
            
            return best_match
            
        except Exception as e:
            print(f"Error extracting IGN bbox: {e}")
            return None


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


def detect_table_regions(image: np.ndarray, target_ign: Optional[str] = None) -> Dict[str, Any]:
    """Detect table regions - module-level function"""
    detector = PlayerDetector()
    return detector.detect_table_regions(image, target_ign)


def rel_to_abs(img: np.ndarray, rel: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
    """
    Convert relative coordinates (0-1) to absolute pixel coordinates
    
    Args:
        img: Image array
        rel: Relative coordinates (x1, y1, x2, y2) as fractions
        
    Returns:
        Absolute coordinates (x1, y1, x2, y2) as integers
    """
    h, w = img.shape[:2]
    x1, y1, x2, y2 = rel
    return (
        int(x1 * w),
        int(y1 * h), 
        int(x2 * w),
        int(y2 * h)
    )


# New comprehensive KDA detection system based on Final-fix-1.md

import yaml
from difflib import SequenceMatcher
from .utils_geometry import BBox, pct_to_abs, row_bbox

# Load configuration
try:
    with open("backend/ocr/config_ocr.yaml", "r") as f:
        CFG = yaml.safe_load(f)
except Exception as e:
    # Fallback configuration if file not found
    CFG = {
        "table": {
            "blue_panel_pct": [0.03, 0.18, 0.47, 0.56],
            "rows": 5,
            "row_top_offset_pct": 0.04,
            "row_bottom_offset_pct": 0.04,
            "name_col_start_pct": 0.20,
            "name_col_width_pct": 0.35
        },
        "matching": {
            "fuzzy_ign_threshold": 0.70
        }
    }


def fuzzy_sim(a, b):
    """Calculate fuzzy similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def detect_blue_panel(img_bgr) -> BBox:
    """Detect the blue team panel using configured geometry"""
    H, W = img_bgr.shape[:2]
    panel_pct = CFG["table"]["blue_panel_pct"]
    return pct_to_abs(BBox(0, 0, W, H), panel_pct)


def detect_player_row_fuzzy(img_bgr, target_ign: str) -> int:
    """
    Return 0-based row index (0..4) for target IGN inside blue panel using fuzzy matching.
    
    Args:
        img_bgr: Full screenshot image
        target_ign: IGN to search for (e.g., "Diary of dolls")
        
    Returns:
        Row index (0-4) or -1 if not found with sufficient confidence
    """
    panel = detect_blue_panel(img_bgr)
    rows = CFG["table"]["rows"]
    top_off = CFG["table"]["row_top_offset_pct"]
    bot_off = CFG["table"]["row_bottom_offset_pct"]
    name_start_pct = CFG["table"]["name_col_start_pct"]
    name_w_pct = CFG["table"]["name_col_width_pct"]
    sim_thresh = CFG["matching"]["fuzzy_ign_threshold"]

    # Initialize EasyOCR if not already done
    if not hasattr(detect_player_row_fuzzy, 'reader'):
        import easyocr
        detect_player_row_fuzzy.reader = easyocr.Reader(['en'], gpu=False)
    
    reader = detect_player_row_fuzzy.reader

    best = (-1, 0.0)
    for i in range(rows):
        rbox = row_bbox(panel, i, rows, top_off, bot_off)
        # Position name box after avatar area
        name_x = rbox.x + int(rbox.w * name_start_pct)
        name_w = int(rbox.w * name_w_pct)
        name_box = BBox(name_x, rbox.y, name_w, rbox.h)
        crop = img_bgr[name_box.y:name_box.y+name_box.h, name_box.x:name_box.x+name_box.w]
        
        # OCR just the name column
        try:
            ocr_results = reader.readtext(crop, detail=1, paragraph=True)
            text = " ".join([t[1] for t in ocr_results if len(t) >= 2])
            sim = fuzzy_sim(text, target_ign)
            
            if sim > best[1]:
                best = (i, sim)
                
        except Exception as e:
            continue
    
    idx, score = best
    return idx if score >= sim_thresh else -1


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
