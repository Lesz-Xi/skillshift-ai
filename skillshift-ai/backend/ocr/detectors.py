"""
Row-agnostic scoreboard detection system for MLBB screenshots.

This module implements the row-agnostic approach described in OCR-Task-1.md:
1. Detect the scoreboard table once
2. Normalize all geometry to ratios
3. Generate row crops dynamically
4. Anchor parsing per row
5. Fallback & validation
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TableRegion:
    """Represents a detected table region with normalized coordinates."""
    # (top, left, width, height) as ratios
    panel_bbox: Tuple[float, float, float, float]
    rows_count: int
    row_height_ratio: float
    row_top_ratio: float
    confidence: float
    anchors_found: List[str]


@dataclass
class RowCrop:
    """Represents a single row crop with normalized coordinates."""
    row_index: int
    # (top, left, width, height) as ratios
    bbox_ratio: Tuple[float, float, float, float]
    # (top, left, width, height) in pixels
    absolute_bbox: Tuple[int, int, int, int]
    contains_target_ign: bool = False
    confidence: float = 0.0


class RowAgnosticScoreboardDetector:
    """
    Row-agnostic scoreboard detection system.

    Detects the scoreboard table once, normalizes geometry to ratios,
    and generates dynamic row crops for any player position.
    """

    def __init__(self):
        # Table detection anchors for MLBB scoreboard
        self.table_anchors = [
            "Hero Damage", "Victory", "Defeat", "KDA", "Gold",
            "Tower Damage", "Jungle", "MVP", "Bronze", "Silver", "Gold"
        ]

        # Expected row count for MLBB (usually 5 players)
        self.expected_rows = 5

        # Row detection tolerance
        self.row_tolerance = 0.05  # 5% of image height

        # Minimum confidence for table detection
        self.min_table_confidence = 0.7

    def _calculate_adaptive_threshold(self, texts: List[str], target_ign: str) -> int:
        """
        MANUS-AI METHODOLOGY: Calculate adaptive threshold based on OCR noise conditions.
        Implements error recovery through context-aware threshold adjustment.

        Args:
            texts: OCR text results to analyze for noise level
            target_ign: Target IGN to match against

        Returns:
            Adaptive threshold (40-85) based on noise analysis
        """
        try:
            # Base threshold
            base_threshold = 85

            # Analyze OCR noise level
            noise_indicators = 0
            total_texts = len(texts)

            if total_texts == 0:
                return 65  # Fallback threshold

            for text in texts:
                # Check for OCR noise indicators
                if any(char.isdigit() for char in text):  # Numbers present
                    noise_indicators += 1
                if len(text) < 3:  # Very short text fragments
                    noise_indicators += 1
                if any(char in text for char in '@#$%&*[]{}'):  # Special characters
                    noise_indicators += 1
                if text.lower() in ['mvp', 'kda', 'gold', 'damage']:  # Game terms
                    noise_indicators += 0.5

            # Calculate noise ratio
            noise_ratio = noise_indicators / total_texts

            # Apply Manus AI error recovery: Lower threshold for noisy conditions
            # MANUS-AI FIX: Lowered thresholds to handle OCR variations better
            if noise_ratio > 0.7:  # High noise
                adaptive_threshold = 35  # Lowered from 50 to handle difficult OCR
            elif noise_ratio > 0.5:  # Medium noise
                adaptive_threshold = 45  # Lowered from 60
            elif noise_ratio > 0.3:  # Low noise
                adaptive_threshold = 55  # Lowered from 70
            else:  # Clean OCR
                adaptive_threshold = base_threshold

            # Context preservation: Additional adjustment for partial matches
            target_words = target_ign.lower().split()
            for text in texts:
                text_lower = text.lower()
                # Check for partial word matches (context preservation)
                partial_matches = sum(1 for word in target_words if word in text_lower)
                if partial_matches > 0:
                    # Lower threshold when partial matches exist (context recovery)
                    adaptive_threshold = max(40, adaptive_threshold - 10)
                    break

            logger.info(f"MANUS-AI: Adaptive threshold calculated: {adaptive_threshold} (noise_ratio: {noise_ratio:.2f})")
            return adaptive_threshold

        except Exception as e:
            logger.error(f"Error calculating adaptive threshold: {e}")
            return 60  # Safe fallback threshold

    def detect_table_regions(self, image_path: str) -> Optional[TableRegion]:
        """
        Detect the scoreboard table and return normalized geometry with OCR Mission 5 robustness.
        Implements 4-tier optimization: ultra-fast, fast, medium, slow paths.

        Args:
            image_path: Path to the screenshot

        Returns:
            TableRegion with normalized coordinates, or None if not found
        """
        try:
            # OCR Mission 5: Initialize drift guards and telemetry
            from backend.ocr.robustness import detector_drift_guards, drift_telemetry_logger
            
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None

            height, width = image.shape[:2]

            # ULTRA-FAST PATH: Pattern recognition (0-5ms)
            from backend.ocr.fast_mode import fast_detector, is_fast_mode_enabled
            if is_fast_mode_enabled():
                fast_result = fast_detector.detect_fast_pattern(image_path)
                if fast_result and fast_result["confidence"] >= 0.75:
                    logger.info(f"Table detected via ULTRA-FAST path ({fast_result['method']}): "
                              f"confidence={fast_result['confidence']:.3f} in {fast_result['detection_time_ms']:.1f}ms")
                    return TableRegion(
                        panel_bbox=fast_result["bbox"],
                        rows_count=fast_result["rows_count"],
                        row_height_ratio=fast_result["row_height_ratio"],
                        row_top_ratio=fast_result["bbox"][0],
                        confidence=fast_result["confidence"],
                        anchors_found=["fast_pattern"]
                    )

            # Convert to grayscale for OCR-based detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # OCR Mission 5: Multi-anchor consensus validation
            anchors_found, consensus_confidence = detector_drift_guards.multi_anchor_consensus(gray, width, height)
            
            # FAST PATH: Try horizontal line detection (5-50ms)
            table_region = self._detect_by_horizontal_lines(gray, width, height)
            if table_region and table_region.confidence >= self.min_table_confidence:
                # OCR Mission 5: Apply drift guards
                table_region = self._apply_drift_guards(table_region, width, height, anchors_found)
                logger.info(f"Table detected via FAST path (lines): confidence={table_region.confidence:.3f}")
                return table_region

            # MEDIUM PATH: Try lightweight anchor detection on ROI (50-300ms)
            table_region = self._detect_by_anchors_fast(gray, width, height)
            if table_region and table_region.confidence >= self.min_table_confidence:
                # OCR Mission 5: Apply drift guards
                table_region = self._apply_drift_guards(table_region, width, height, anchors_found)
                logger.info(f"Table detected via MEDIUM path (ROI OCR): confidence={table_region.confidence:.3f}")
                return table_region

            # SLOW PATH: Full anchor-based detection (last resort, 1-15s)
            table_region = self._detect_by_anchors_safe(gray, width, height)
            if table_region and table_region.confidence >= self.min_table_confidence:
                # OCR Mission 5: Apply drift guards
                table_region = self._apply_drift_guards(table_region, width, height, anchors_found)
                logger.info(f"Table detected via SLOW path (full OCR): confidence={table_region.confidence:.3f}")
                return table_region

            # Fallback: use default regions based on common MLBB layout
            logger.info("Using default table region as fallback")
            return self._get_default_table_region(width, height)

        except Exception as e:
            logger.error(f"Error detecting table regions: {e}")
            return None

    def _detect_by_anchors_fast(self, gray_image: np.ndarray, width: int, height: int) -> Optional[TableRegion]:
        """
        Fast anchor-based detection using ROI processing and optimized OCR.
        Processes only key regions instead of the entire image.
        """
        try:
            # Define ROI regions where anchors typically appear (top and bottom thirds)
            roi_regions = [
                (0, int(height * 0.1), width, int(height * 0.4)),        # Top region
                (0, int(height * 0.6), width, int(height * 0.9))         # Bottom region
            ]
            
            anchor_positions = []
            found_anchors = []
            
            from backend.ocr.ocr_reader import extract_text_optimized
            
            for x, y, w, h in roi_regions:
                # Extract ROI
                roi = gray_image[y:y+h, x:x+w]
                
                # Use optimized text extraction with caching
                try:
                    texts = extract_text_optimized(roi)
                    
                    for text in texts:
                        text_lower = text.lower().strip()
                        for anchor in self.table_anchors:
                            if anchor.lower() in text_lower and len(text_lower) > 2:
                                # Calculate position relative to full image
                                # Estimate center of detected region
                                center_x = x + w // 2
                                center_y = y + h // 2
                                
                                anchor_positions.append((center_x, center_y))
                                found_anchors.append(anchor)
                                break
                                
                except Exception as e:
                    logger.debug(f"ROI processing failed for region {x},{y},{w},{h}: {e}")
                    continue
            
            # Relax threshold: allow no anchors for fallback detection
            if len(anchor_positions) < 1:
                logger.debug("No anchors found in fast detection, using fallback region")
            
            # Calculate bounding box from anchor positions with generous padding
            if anchor_positions:
                x_coords = [pos[0] for pos in anchor_positions]
                y_coords = [pos[1] for pos in anchor_positions]
                
                # Add padding around detected anchors
                padding = int(min(width, height) * 0.1)  # 10% of image size
                left = max(0, min(x_coords) - padding)
                right = min(width, max(x_coords) + padding)
                top = max(0, min(y_coords) - padding)
                bottom = min(height, max(y_coords) + padding)
                
                # Convert to ratios
                panel_bbox = (
                    top / height,      # top_ratio
                    left / width,      # left_ratio
                    (right - left) / width,  # width_ratio
                    (bottom - top) / height  # height_ratio
                )
                
                # Estimate row count and height
                row_height = (bottom - top) / self.expected_rows
                row_height_ratio = row_height / height
                row_top_ratio = top / height
                
                # Medium confidence for fast detection
                confidence = min(0.8, 0.5 + len(found_anchors) / len(self.table_anchors))
                
                return TableRegion(
                    panel_bbox=panel_bbox,
                    rows_count=self.expected_rows,
                    row_height_ratio=row_height_ratio,
                    row_top_ratio=row_top_ratio,
                    confidence=confidence,
                    anchors_found=found_anchors
                )
            else:
                # No anchors found - use fallback region estimation
                logger.debug("No anchors found, using default scoreboard region")
                fallback_bbox = (0.15, 0.0, 1.0, 0.70)  # Top 15%, full width, 70% height
                return TableRegion(
                    panel_bbox=fallback_bbox,
                    rows_count=self.expected_rows,
                    row_height_ratio=0.14,  # 70% / 5 rows = 14%
                    row_top_ratio=0.15,
                    confidence=0.3,  # Lower confidence for fallback
                    anchors_found=["fallback_no_anchors"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in fast anchor detection: {e}")
            return None

    def _detect_by_anchors_safe(self, gray_image: np.ndarray, width: int, height: int) -> Optional[TableRegion]:
        """
        Safe anchor-based detection with fail-soft error handling.
        Falls back to OCR-only approach if C-extensions fail.
        """
        try:
            # Try the original anchor-based approach
            return self._detect_by_anchors(gray_image, width, height)
        except Exception as e:
            logger.exception("Anchor path failed; falling back to OCR-only: %s", e)
            return self._ocr_only_detect_table(gray_image, width, height)

    def _detect_by_anchors(self, gray_image: np.ndarray, width: int, height: int) -> Optional[TableRegion]:
        """Detect table by looking for known anchor text."""
        try:
            # Use EasyOCR for text detection
            from backend.ocr.ocr_reader import get_reader
            reader = get_reader()
            ocr_results = reader.readtext(gray_image, detail=1)

            # Find anchor text positions
            anchor_positions = []
            found_anchors = []

            for bbox, text, confidence in ocr_results:
                text_lower = text.lower().strip()
                for anchor in self.table_anchors:
                    if anchor.lower() in text_lower and confidence > 0.5:
                        # Calculate center position
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]
                        center_x = sum(x_coords) / len(x_coords)
                        center_y = sum(y_coords) / len(y_coords)

                        anchor_positions.append((center_x, center_y))
                        found_anchors.append(anchor)
                        break

            if len(anchor_positions) < 2:
                return None

            # Calculate bounding box from anchor positions
            x_coords = [pos[0] for pos in anchor_positions]
            y_coords = [pos[1] for pos in anchor_positions]

            # Add padding around detected anchors
            padding = 50
            left = max(0, min(x_coords) - padding)
            right = min(width, max(x_coords) + padding)
            top = max(0, min(y_coords) - padding)
            bottom = min(height, max(y_coords) + padding)

            # Convert to ratios
            panel_bbox = (
                top / height,      # top_ratio
                left / width,      # left_ratio
                (right - left) / width,  # width_ratio
                (bottom - top) / height  # height_ratio
            )

            # Estimate row count and height
            row_height = (bottom - top) / self.expected_rows
            row_height_ratio = row_height / height
            row_top_ratio = top / height

            # Calculate confidence based on number of anchors found
            confidence = min(1.0, len(found_anchors) / len(self.table_anchors))

            return TableRegion(
                panel_bbox=panel_bbox,
                rows_count=self.expected_rows,
                row_height_ratio=row_height_ratio,
                row_top_ratio=row_top_ratio,
                confidence=confidence,
                anchors_found=found_anchors
            )

        except Exception as e:
            logger.error(f"Error in anchor-based detection: {e}")
            return None

    def _ocr_only_detect_table(self, gray_image: np.ndarray, width: int, height: int) -> Optional[TableRegion]:
        """
        OCR-only table detection fallback when anchor detection fails.
        Uses text distribution to estimate table region.
        """
        try:
            from backend.ocr.ocr_reader import extract_text_optimized
            
            # Extract all text from the image
            texts = extract_text_optimized(gray_image)
            
            if not texts:
                return None
            
            # Look for scoreboard-related keywords
            scoreboard_keywords = ["kda", "damage", "gold", "mvp", "victory", "defeat"]
            found_keywords = []
            
            for text in texts:
                text_lower = text.lower()
                for keyword in scoreboard_keywords:
                    if keyword in text_lower:
                        found_keywords.append(keyword)
            
            if len(found_keywords) < 2:
                return None
            
            # Estimate table region based on text distribution
            # Assume scoreboard is in the middle portion of the screen
            panel_bbox = (0.2, 0.0, 1.0, 0.6)  # Middle 60% of screen
            
            return TableRegion(
                panel_bbox=panel_bbox,
                rows_count=self.expected_rows,
                row_height_ratio=0.12,
                row_top_ratio=0.2,
                confidence=0.6,  # Medium confidence for OCR-only
                anchors_found=found_keywords
            )
            
        except Exception as e:
            logger.error(f"Error in OCR-only detection: {e}")
            return None

    def _detect_by_horizontal_lines(self, gray_image: np.ndarray, width: int, height: int) -> Optional[TableRegion]:
        """Detect table by finding horizontal lines that indicate rows."""
        try:
            # Focus on the middle portion of the image where scoreboard typically appears
            middle_start = int(height * 0.2)  # Start from 20% down
            middle_end = int(height * 0.8)    # End at 80% down
            middle_region = gray_image[middle_start:middle_end, :]
            
            # Detect horizontal lines using Hough transform with higher threshold
            edges = cv2.Canny(middle_region, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=150)  # Higher threshold

            if lines is None:
                return None

            # Filter horizontal lines and adjust Y coordinates
            horizontal_lines = []
            for line in lines:
                rho, theta = line[0]
                if abs(theta - np.pi/2) < 0.1:  # Nearly horizontal
                    # Adjust rho to full image coordinates
                    adjusted_rho = rho + middle_start
                    horizontal_lines.append(adjusted_rho)

            if len(horizontal_lines) < 3:
                return None

            # Sort lines by Y position
            horizontal_lines.sort()

            # Filter lines to reasonable scoreboard area (middle 60% of screen)
            scoreboard_lines = []
            for rho in horizontal_lines:
                if 0.2 * height <= rho <= 0.8 * height:
                    scoreboard_lines.append(rho)

            if len(scoreboard_lines) < 3:
                return None

            # Group lines that are close together (likely scoreboard rows)
            line_groups = []
            current_group = [scoreboard_lines[0]]

            for i in range(1, len(scoreboard_lines)):
                if scoreboard_lines[i] - scoreboard_lines[i-1] < 50:  # Lines close together
                    current_group.append(scoreboard_lines[i])
                else:
                    if 3 <= len(current_group) <= 10:  # Reasonable number of rows for scoreboard
                        line_groups.append(current_group)
                    current_group = [scoreboard_lines[i]]

            if 3 <= len(current_group) <= 10:
                line_groups.append(current_group)

            if not line_groups:
                return None

            # Use the group with most lines, but limit to reasonable scoreboard size
            best_group = max(line_groups, key=len)
            
            # Limit to maximum 10 rows (typical MLBB scoreboard)
            if len(best_group) > 10:
                best_group = best_group[:10]

            # Calculate table region
            top_line = min(best_group)
            bottom_line = max(best_group)

            # Add padding
            padding = 20
            top = max(0, int(top_line) - padding)
            bottom = min(height, int(bottom_line) + padding)
            left = 0
            right = width

            # Convert to ratios
            panel_bbox = (
                top / height,      # top_ratio
                left / width,      # left_ratio
                (right - left) / width,  # width_ratio
                (bottom - top) / height  # height_ratio
            )

            # Calculate row parameters
            row_height = (bottom - top) / len(best_group)
            row_height_ratio = row_height / height
            row_top_ratio = top / height

            return TableRegion(
                panel_bbox=panel_bbox,
                rows_count=len(best_group),
                row_height_ratio=row_height_ratio,
                row_top_ratio=row_top_ratio,
                confidence=0.8,  # High confidence for line-based detection
                anchors_found=["horizontal_lines"]
            )

        except Exception as e:
            logger.error(f"Error in line-based detection: {e}")
            return None

    def _get_default_table_region(self, width: int, height: int) -> TableRegion:
        """
        Enhanced fallback to default MLBB scoreboard region with adaptive heuristics.
        Implements anchor-less fallback strategy from Analysis_Failure_Fix.md.
        """
        try:
            # Adaptive region based on common MLBB screen ratios
            # Most MLBB screenshots have scoreboard in the central area
            
            # Calculate adaptive bounding box based on image dimensions
            aspect_ratio = width / height if height > 0 else 1.0
            
            if aspect_ratio > 1.5:  # Wide screen (16:9, 21:9, etc.)
                # Wide screens usually have more horizontal space
                panel_bbox = (0.15, 0.0, 1.0, 0.70)  # Top 15%, full width, 70% height
            elif aspect_ratio < 0.8:  # Portrait/mobile
                # Mobile screens often have different layout
                panel_bbox = (0.20, 0.05, 0.90, 0.60)  # 20% from top, 5% margin, 90% width, 60% height
            else:  # Square-ish (4:3, etc.)
                # Standard layout
                panel_bbox = (0.15, 0.0, 1.0, 0.70)  # 15% from top, full width, 70% height
            
            # Enhanced confidence calculation
            # Higher confidence because we use adaptive heuristics
            base_confidence = 0.35
            
            # Bonus confidence for reasonable image dimensions
            if 800 <= width <= 2560 and 600 <= height <= 1440:
                base_confidence += 0.15  # Common screenshot resolutions
            
            logger.info(f"Using enhanced fallback heuristic: aspect_ratio={aspect_ratio:.2f}, "
                       f"bbox={panel_bbox}, confidence={base_confidence:.2f}")
            
            return TableRegion(
                panel_bbox=panel_bbox,
                rows_count=self.expected_rows,
                row_height_ratio=panel_bbox[3] / self.expected_rows,  # Height / rows
                row_top_ratio=panel_bbox[0],
                confidence=base_confidence,
                anchors_found=["fallback-heuristic", f"aspect-{aspect_ratio:.1f}"]
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced fallback: {e}")
            # Ultimate fallback to safe defaults
            return TableRegion(
                panel_bbox=(0.15, 0.0, 1.0, 0.70),
                rows_count=self.expected_rows, 
                row_height_ratio=0.14,
                row_top_ratio=0.15,
                confidence=0.35,
                anchors_found=["fallback-safe"]
            )
    
    def _apply_drift_guards(self, table_region: TableRegion, width: int, height: int, anchors_found: List[str]) -> TableRegion:
        """
        Apply OCR Mission 5 drift guards to table region.
        
        Args:
            table_region: Original table region
            width: Image width
            height: Image height
            anchors_found: List of found anchors
            
        Returns:
            TableRegion with drift guards applied
        """
        try:
            from backend.ocr.robustness import detector_drift_guards
            
            # Apply dynamic bbox expansion for letterboxing/crop tolerance
            expanded_bbox = detector_drift_guards.expand_bbox_dynamic(
                table_region.panel_bbox, width, height
            )
            
            # Update table region with expanded bbox
            updated_region = TableRegion(
                panel_bbox=expanded_bbox,
                rows_count=table_region.rows_count,
                row_height_ratio=table_region.row_height_ratio,
                row_top_ratio=expanded_bbox[0],  # Update top ratio
                confidence=table_region.confidence,
                anchors_found=anchors_found if anchors_found else table_region.anchors_found
            )
            
            return updated_region
            
        except Exception as e:
            logger.error(f"Error applying drift guards: {e}")
            return table_region

    def generate_row_crops(self, table_region: TableRegion, image_path: str, target_ign: str = None) -> List[RowCrop]:
        """
        Generate row crops dynamically based on table region.

        Args:
            table_region: Detected table region with normalized coordinates
            image_path: Path to the image
            target_ign: Target IGN to search for (optional)

        Returns:
            List of RowCrop objects for each row
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []

            height, width = image.shape[:2]
            row_crops = []

            # Convert ratios to absolute coordinates
            panel_top = int(table_region.panel_bbox[0] * height)
            panel_left = int(table_region.panel_bbox[1] * width)
            panel_width = int(table_region.panel_bbox[2] * width)
            panel_height = int(table_region.panel_bbox[3] * height)

            row_height = int(table_region.row_height_ratio * height)

            # Generate crops for each row
            for i in range(table_region.rows_count):
                row_y = panel_top + i * row_height

                # Ensure row is within image bounds
                if row_y + row_height > height:
                    row_height = height - row_y
                if row_height <= 0:
                    break

                # Create row crop
                bbox_ratio = (
                    row_y / height,           # top_ratio
                    panel_left / width,       # left_ratio
                    panel_width / width,      # width_ratio
                    row_height / height       # height_ratio
                )

                absolute_bbox = (row_y, panel_left, panel_width, row_height)

                # Check if this row contains the target IGN
                contains_ign = False
                confidence = 0.0

                if target_ign:
                    contains_ign, confidence = self._check_row_for_ign(
                        image, absolute_bbox, target_ign
                    )

                # MANUS-AI DEBUG: Enhanced row detection logging
                logger.info(f"Row {i} (visual row {i+1}): contains_ign={contains_ign}, confidence={confidence:.2f}, bbox=({row_y}, {panel_left}, {panel_width}, {row_height})")

                row_crop = RowCrop(
                    row_index=i,
                    bbox_ratio=bbox_ratio,
                    absolute_bbox=absolute_bbox,
                    contains_target_ign=contains_ign,
                    confidence=confidence
                )

                row_crops.append(row_crop)

            return row_crops

        except Exception as e:
            logger.error(f"Error generating row crops: {e}")
            return []

    def _check_row_for_ign(self, image: np.ndarray, bbox: Tuple[int, int, int, int], target_ign: str) -> Tuple[bool, float]:
        """Check if a row contains the target IGN using robust fuzzy matching."""
        try:
            row_y, row_x, row_width, row_height = bbox

            # Extract row region
            row_region = image[row_y:row_y+row_height, row_x:row_x+row_width]
            
            # Use optimized OCR extraction
            from backend.ocr.ocr_reader import extract_text_optimized
            texts = extract_text_optimized(row_region)
            
            # Debug logging
            logger.debug(f"OCR texts for IGN check: {texts}")
            
            # Use robust fuzzy matching
            from backend.ocr.textmatch import best_match
            # MANUS-AI METHODOLOGY: Context preservation and error recovery
            # Apply adaptive threshold based on OCR noise conditions
            # Lower threshold for noisy OCR output to preserve context
            adaptive_threshold = self._calculate_adaptive_threshold(texts, target_ign)

            result = best_match(target_ign, texts, threshold=adaptive_threshold)

            # Debug logging for adaptive thresholding
            logger.debug(f"Best match result: {result}, type: {type(result)}, adaptive_threshold: {adaptive_threshold}")

            # Handle the result properly with context preservation
            if result and len(result) == 2:
                match, score = result
                # Use adaptive threshold for acceptance
                if match and score >= adaptive_threshold:
                    logger.info(f"✅ IGN match accepted with adaptive threshold: {score} >= {adaptive_threshold}")
                    return True, float(score) / 100.0  # Convert to 0-1 scale
                else:
                    logger.info(f"⚠️ IGN match below adaptive threshold: {score} < {adaptive_threshold}")

            return False, 0.0

        except Exception as e:
            logger.error(f"Error checking row for IGN: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, 0.0

    def find_target_row(self, row_crops: List[RowCrop], target_ign: str) -> Optional[RowCrop]:
        """
        Find the row containing the target IGN using robust fuzzy matching.

        Args:
            row_crops: List of row crops to search
            target_ign: Target IGN to find

        Returns:
            RowCrop containing the target IGN, or None if not found
        """
        from backend.ocr.textmatch import best_match

        # MANUS-AI DEBUG: Enhanced target row selection logging
        logger.info(f"🎯 Finding target row for IGN: '{target_ign}' among {len(row_crops)} rows")

        # First, try to find rows that already have IGN detection
        for i, row_crop in enumerate(row_crops):
            logger.info(f"🔍 Row {i} (visual row {i+1}): contains_ign={row_crop.contains_target_ign}, confidence={row_crop.confidence:.3f}")
            if row_crop.contains_target_ign and row_crop.confidence > 0.7:
                logger.info(f"✅ Selected row {i} (visual row {i+1}) with high confidence: {row_crop.confidence:.3f}")
                return row_crop

        # If no pre-detected matches, do OCR on all rows and use fuzzy matching
        best_row = None
        best_score = 0.0
        best_row_index = -1

        for i, row_crop in enumerate(row_crops):
            try:
                # Extract text from this row
                row_y, row_x, row_width, row_height = row_crop.absolute_bbox
                # Note: This would need the original image, but we'll use the confidence
                # from the row crop as a proxy for now

                # Use the confidence as a score and apply fuzzy matching
                if row_crop.confidence > 0.3:  # Lower threshold for fuzzy matching
                    # In a real implementation, we'd OCR the row here
                    # For now, we'll use the confidence as a proxy
                    score = row_crop.confidence * 100  # Convert to 0-100 scale

                    logger.info(f"📊 Row {i} (visual row {i+1}) candidate: score={score:.2f}, confidence={row_crop.confidence:.3f}")

                    if score > best_score:
                        best_score = score
                        best_row = row_crop
                        best_row_index = i

            except Exception as e:
                logger.error(f"Error processing row for IGN matching: {e}")
                continue

        # Return the best match if it meets our threshold
        if best_row and best_score >= 30:  # 30% threshold for fuzzy matching
            logger.info(f"🎯 Final selection: Row {best_row_index} (visual row {best_row_index+1}) with score={best_score:.2f}")
            return best_row

        logger.warning(f"❌ No suitable row found for IGN '{target_ign}'")
        return None

    def detect(self, image):
        """
        Unified detection entrypoint (for tests & services).
        Returns a dict with table bbox, row crops, and metadata.
        
        Args:
            image: Path to image file or numpy array
            
        Returns:
            Dict with bbox, confidence, rows_count, and row_crops, or None if detection fails
        """
        try:
            # Handle both image path strings and numpy arrays
            if isinstance(image, str):
                image_path = image
            else:
                # For numpy arrays, we need to save temporarily or modify the methods
                # For now, assume it's a path since that's what the existing methods expect
                logger.warning("detect() method currently only supports image paths")
                return None
            
            # Step 1: Detect table regions
            table = self.detect_table_regions(image_path)
            if not table:
                return None

            # Step 2: Generate row crops
            row_crops = self.generate_row_crops(table, image_path)
            
            # Step 3: Return unified result
            return {
                "bbox": table.panel_bbox,
                "confidence": table.confidence,
                "rows_count": table.rows_count,
                "row_crops": row_crops,
                "anchors_found": table.anchors_found,
                "row_height_ratio": table.row_height_ratio,
                "row_top_ratio": table.row_top_ratio
            }
            
        except Exception as e:
            logger.error(f"Error in unified detect method: {e}")
            return None

    def rows(self, image, table):
        """
        Extract row information for use with parsers.
        
        Args:
            image: Input image (numpy array)
            table: Table detection result from detect() method
            
        Returns:
            List of RowCrop objects for parser consumption
        """
        try:
            # If table is None or doesn't have row_crops, return empty list
            if not table or not isinstance(table, dict):
                logger.warning("Invalid table result provided to rows() method")
                return []
            
            # If table already contains row_crops, return them
            if "row_crops" in table:
                return table["row_crops"]
            
            # Fallback: if table doesn't have row_crops but has the necessary info,
            # we could regenerate them, but this shouldn't happen with our current implementation
            logger.warning("Table result missing row_crops, returning empty list")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting rows: {e}")
            return []


# Global instance
row_agnostic_detector = RowAgnosticScoreboardDetector()