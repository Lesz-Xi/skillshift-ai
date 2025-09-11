#!/usr/bin/env python3
"""
KDA Cell Reader - Geometry-anchored slash-guided digit OCR

Implements precise KDA parsing by:
1. Cropping KDA cell from player row
2. Detecting slash glyphs using template matching
3. OCR isolated digit segments with strict allowlists
4. Applying sanity validation and confidence scoring

Target: Extract exact KDA 9/2/12 from IMG_1767 with high confidence.
"""

import cv2
import numpy as np
import re
from typing import Dict, Tuple, List, Optional, Any
import easyocr
from dataclasses import dataclass


@dataclass
class KDAResult:
    """Result structure for KDA parsing"""
    k: int = 0
    d: int = 0
    a: int = 0
    ratio: float = 0.0
    confidence: float = 0.0
    method: str = "unknown"
    debug_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.debug_info is None:
            self.debug_info = {}
        # Calculate ratio if not set
        if self.ratio == 0.0:
            self.ratio = (self.k + self.a) / max(1, self.d)


class KDACellReader:
    """Advanced KDA cell reader with slash-guided parsing"""
    
    def __init__(self):
        """Initialize the KDA cell reader"""
        self.ocr_reader = None
        self._initialize_ocr()
        
    def _initialize_ocr(self):
        """Initialize EasyOCR reader for digit recognition"""
        try:
            # Fix PIL.Image.ANTIALIAS deprecation warning
            import PIL.Image
            if not hasattr(PIL.Image, 'ANTIALIAS'):
                PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
            
            self.ocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception as e:
            print(f"Warning: Failed to initialize OCR: {e}")
            self.ocr_reader = None
    
    def read_kda_from_cell(self, row_img: np.ndarray, kda_bbox: Tuple[int, int, int, int], 
                          mvp_score: Optional[float] = None, name_x2: Optional[int] = None) -> Tuple[Dict[str, int], float]:
        """
        Read KDA values from cell using slash-guided parsing with spatial filtering and candidate ranking
        
        Args:
            row_img: Image of the player row
            kda_bbox: (x1, y1, x2, y2) absolute coordinates of KDA cell
            mvp_score: Optional MVP score for sanity checking
            name_x2: Optional right edge of IGN for spatial filtering
            
        Returns:
            Tuple of (kda_dict, confidence_score)
        """
        try:
            # Step 1: Crop the KDA cell
            x1, y1, x2, y2 = kda_bbox
            crop = row_img[y1:y2, x1:x2]
            
            if crop.size == 0:
                return self._fallback_result("empty_crop")
            
            # Step 2: Preprocess the crop
            processed_crop = self._preprocess_crop(crop)
            
            # Step 3: Collect all KDA candidates from different methods
            candidates = []
            
            debug_info = {
                "crop_size": crop.shape[:2],
                "kda_cell_bbox": kda_bbox,
                "name_x2": name_x2
            }
            
            # Method A: Slash-guided segmentation
            slash_positions = self._detect_slashes(processed_crop)
            debug_info["slash_positions"] = slash_positions
            
            if len(slash_positions) >= 2:
                slash_candidates = self._extract_slash_candidates(processed_crop, slash_positions, kda_bbox)
                candidates.extend(slash_candidates)
            
            # Method B: Regex-based parsing on full crop
            regex_candidates = self._extract_regex_candidates(crop, kda_bbox)
            candidates.extend(regex_candidates)
            
            # Step 4: Apply spatial filtering if name_x2 is provided
            if name_x2 is not None:
                filtered_candidates = []
                for candidate in candidates:
                    # Convert local center_x to global coordinates
                    global_center_x = kda_bbox[0] + candidate.get("center_x", 0)
                    if global_center_x > name_x2 + 2:  # Must be to the right of name
                        filtered_candidates.append(candidate)
                
                if filtered_candidates:
                    candidates = filtered_candidates
                    debug_info["spatial_filtering"] = "applied"
                else:
                    debug_info["spatial_filtering"] = "no_candidates_after_filter"
            
            # Step 5: Rank candidates by distance to name and confidence
            def score_candidate(c):
                dist = 1e6
                if name_x2 is not None:
                    global_center_x = kda_bbox[0] + c.get("center_x", 0)
                    dist = abs(global_center_x - name_x2)
                return (dist, -c.get("conf", 0.0))
            
            candidates.sort(key=score_candidate)
            debug_info["kda_candidates"] = candidates[:3]  # Top 3 for debugging
            
            # Step 6: Validate and select best candidate
            for candidate in candidates:
                k, d, a = candidate["k"], candidate["d"], candidate["a"]
                
                # Basic range validation
                if not (0 <= k <= 30 and 0 <= d <= 30 and 0 <= a <= 30):
                    continue
                
                # Ratio plausibility check
                ratio = (k + a) / max(1, d)
                if not (0.1 <= ratio <= 30):
                    continue
                
                # Build result
                result = {
                    "k": k,
                    "d": d,
                    "a": a,
                    "ratio": ratio
                }
                
                confidence = max(0.6, candidate.get("conf", 0.6))
                
                # Apply MVP sanity checks if provided
                if mvp_score is not None:
                    result, confidence = self._apply_mvp_sanity_checks(
                        result, confidence, mvp_score, processed_crop, slash_positions, debug_info
                    )
                
                return result, confidence
            
            # Step 7: No valid candidates found
            return self._fallback_result("no_valid_candidates", debug_info)
            
        except Exception as e:
            print(f"Error reading KDA from cell: {e}")
            return self._fallback_result(f"error: {e}")
    
    def _preprocess_crop(self, crop: np.ndarray) -> np.ndarray:
        """
        Preprocess KDA cell crop for better OCR accuracy
        
        Args:
            crop: Raw crop from KDA cell
            
        Returns:
            Preprocessed binary image
        """
        # Convert to grayscale
        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop.copy()
        
        # Scale 2.0x for better OCR
        height, width = gray.shape
        scaled = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # Bilateral filter for noise reduction
        filtered = cv2.bilateralFilter(scaled, d=5, sigmaColor=60, sigmaSpace=60)
        
        # Adaptive threshold to binary
        binary = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def _detect_slashes(self, binary_crop: np.ndarray) -> List[int]:
        """
        Detect slash positions using template matching
        
        Args:
            binary_crop: Binary preprocessed crop
            
        Returns:
            List of x-coordinates of detected slashes
        """
        try:
            # Create a simple slash template (3x9)
            slash_template = np.zeros((9, 3), dtype=np.uint8)
            # Create diagonal line for '/'
            for i in range(9):
                x = 2 - (i * 2) // 9  # Diagonal line
                if 0 <= x < 3:
                    slash_template[i, x] = 255
            
            # Template matching
            result = cv2.matchTemplate(binary_crop, slash_template, cv2.TM_CCOEFF_NORMED)
            
            # Find peaks
            threshold = 0.4
            locations = np.where(result >= threshold)
            
            if len(locations[0]) == 0:
                return []
            
            # Get x-coordinates of matches
            x_positions = locations[1].tolist()
            
            # Apply non-maximum suppression to remove duplicates
            x_positions = self._suppress_close_detections(x_positions, min_distance=12)
            
            # Sort by x-coordinate
            x_positions.sort()
            
            return x_positions[:2]  # Take top 2 slashes
            
        except Exception as e:
            print(f"Error detecting slashes: {e}")
            return []
    
    def _suppress_close_detections(self, positions: List[int], min_distance: int) -> List[int]:
        """
        Suppress detections that are too close together
        
        Args:
            positions: List of x-coordinates
            min_distance: Minimum distance between detections
            
        Returns:
            Filtered list of positions
        """
        if not positions:
            return []
        
        positions = sorted(positions)
        filtered = [positions[0]]
        
        for pos in positions[1:]:
            if pos - filtered[-1] >= min_distance:
                filtered.append(pos)
        
        return filtered
    
    def _parse_with_slashes(self, binary_crop: np.ndarray, slash_positions: List[int], 
                           debug_info: Dict[str, Any]) -> Tuple[Dict[str, int], float]:
        """
        Parse KDA using detected slash positions
        
        Args:
            binary_crop: Binary preprocessed crop
            slash_positions: List of slash x-coordinates
            debug_info: Debug information dictionary
            
        Returns:
            Tuple of (kda_dict, confidence_score)
        """
        try:
            height, width = binary_crop.shape
            padding = 4  # Padding around slash positions
            
            # Define segments based on slash positions
            segments = []
            
            if len(slash_positions) >= 2:
                slash1_x, slash2_x = slash_positions[0], slash_positions[1]
                
                # K segment: start to first slash
                segments.append(("k", 0, slash1_x - padding))
                
                # D segment: first slash to second slash
                segments.append(("d", slash1_x + padding, slash2_x - padding))
                
                # A segment: second slash to end
                segments.append(("a", slash2_x + padding, width))
            
            debug_info["segments"] = [(name, x1, x2) for name, x1, x2 in segments]
            
            # OCR each segment
            kda_values = {}
            confidences = []
            
            for segment_name, x1, x2 in segments:
                if x2 <= x1:
                    continue
                
                # Extract segment
                segment_crop = binary_crop[:, max(0, x1):min(width, x2)]
                
                if segment_crop.size == 0:
                    continue
                
                # OCR the segment with digit allowlist
                value, confidence = self._ocr_digit_segment(segment_crop, segment_name)
                
                if value is not None:
                    kda_values[segment_name] = value
                    confidences.append(confidence)
            
            # Validate we have all three values
            if len(kda_values) == 3 and all(key in kda_values for key in ["k", "d", "a"]):
                # Apply sanity checks
                k, d, a = kda_values["k"], kda_values["d"], kda_values["a"]
                
                if self._validate_kda_values(k, d, a):
                    avg_confidence = sum(confidences) / len(confidences)
                    
                    result = {
                        "k": k,
                        "d": d, 
                        "a": a,
                        "ratio": (k + a) / max(1, d)
                    }
                    
                    debug_info["slash_method_success"] = True
                    debug_info["kda_candidates"] = [result]
                    
                    return result, avg_confidence
            
            return self._fallback_result("slash_parsing_failed", debug_info)
            
        except Exception as e:
            return self._fallback_result(f"slash_parsing_error: {e}", debug_info)
    
    def _ocr_digit_segment(self, segment_crop: np.ndarray, segment_name: str) -> Tuple[Optional[int], float]:
        """
        OCR a single digit segment with validation
        
        Args:
            segment_crop: Binary crop of the digit segment
            segment_name: Name of segment (k, d, or a)
            
        Returns:
            Tuple of (digit_value, confidence)
        """
        if self.ocr_reader is None:
            return None, 0.0
        
        try:
            # Convert binary to RGB for EasyOCR
            rgb_segment = cv2.cvtColor(segment_crop, cv2.COLOR_GRAY2RGB)
            
            # OCR with digit allowlist
            results = self.ocr_reader.readtext(
                rgb_segment, 
                allowlist='0123456789',
                detail=1,
                width_ths=0.7,
                height_ths=0.7
            )
            
            # Find best digit
            best_value = None
            best_confidence = 0.0
            
            for (bbox, text, confidence) in results:
                # Clean text and extract digits
                clean_text = re.sub(r'[^0-9]', '', text.strip())
                
                if clean_text and clean_text.isdigit():
                    value = int(clean_text)
                    
                    # Validate reasonable range
                    if 0 <= value <= 40:
                        if confidence > best_confidence:
                            best_value = value
                            best_confidence = confidence
            
            # Backup: connected components analysis
            if best_value is None:
                backup_value = self._connected_components_digit(segment_crop)
                if backup_value is not None:
                    best_value = backup_value
                    best_confidence = 0.5  # Lower confidence for backup method
            
            return best_value, best_confidence
            
        except Exception as e:
            print(f"Error in OCR digit segment {segment_name}: {e}")
            return None, 0.0
    
    def _connected_components_digit(self, segment_crop: np.ndarray) -> Optional[int]:
        """
        Backup digit recognition using connected components
        
        Args:
            segment_crop: Binary segment crop
            
        Returns:
            Recognized digit or None
        """
        try:
            # Find connected components
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(segment_crop, connectivity=8)
            
            if num_labels <= 1:  # No components found
                return None
            
            # Find largest component (excluding background)
            largest_component_idx = 1
            largest_area = stats[1, cv2.CC_STAT_AREA]
            
            for i in range(2, num_labels):
                area = stats[i, cv2.CC_STAT_AREA]
                if area > largest_area:
                    largest_area = area
                    largest_component_idx = i
            
            # Extract largest component
            component_mask = (labels == largest_component_idx).astype(np.uint8) * 255
            
            # Simple digit recognition based on area and aspect ratio
            area = largest_area
            x, y, w, h = stats[largest_component_idx, :4]
            aspect_ratio = w / max(1, h)
            
            # Heuristic digit recognition (very basic)
            if area < 10:
                return 1
            elif aspect_ratio > 1.5:
                return 1  # Likely "1"
            elif area > 100:
                return None  # Too large, probably noise
            else:
                # Default to most common digits in KDA context
                return 0
            
        except Exception as e:
            print(f"Error in connected components digit recognition: {e}")
            return None
    
    def _parse_with_regex(self, crop: np.ndarray, debug_info: Dict[str, Any]) -> Tuple[Dict[str, int], float]:
        """
        Fallback parsing using regex on full OCR text
        
        Args:
            crop: Raw crop image
            debug_info: Debug information dictionary
            
        Returns:
            Tuple of (kda_dict, confidence_score)
        """
        if self.ocr_reader is None:
            return self._fallback_result("no_ocr_reader", debug_info)
        
        try:
            # Convert to RGB if needed
            if len(crop.shape) == 3:
                rgb_crop = crop
            else:
                rgb_crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2RGB)
            
            # OCR with allowlist for digits and slash
            results = self.ocr_reader.readtext(
                rgb_crop,
                allowlist='0123456789/',
                detail=1
            )
            
            # Extract text
            text_parts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.3:
                    text_parts.append(text.strip())
            
            full_text = ' '.join(text_parts)
            debug_info["fallback_ocr_text"] = full_text
            
            # Regex pattern for KDA
            pattern = r'\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})\b'
            matches = re.findall(pattern, full_text)
            
            if matches:
                k, d, a = map(int, matches[0])
                
                if self._validate_kda_values(k, d, a):
                    result = {
                        "k": k,
                        "d": d,
                        "a": a,
                        "ratio": (k + a) / max(1, d)
                    }
                    
                    debug_info["regex_method_success"] = True
                    debug_info["regex_match"] = matches[0]
                    
                    return result, 0.7  # Medium confidence for regex fallback
            
            return self._fallback_result("regex_parsing_failed", debug_info)
            
        except Exception as e:
            return self._fallback_result(f"regex_parsing_error: {e}", debug_info)
    
    def _apply_mvp_sanity_checks(self, kda_result: Dict[str, int], confidence: float, 
                                mvp_score: float, processed_crop: np.ndarray, 
                                slash_positions: List[int], debug_info: Dict[str, Any]) -> Tuple[Dict[str, int], float]:
        """
        Apply MVP-based sanity checks and repair logic
        
        Args:
            kda_result: Initial KDA parsing result
            confidence: Initial confidence
            mvp_score: MVP score for consistency checking
            processed_crop: Preprocessed crop for re-parsing
            slash_positions: Original slash positions
            debug_info: Debug information
            
        Returns:
            Tuple of (corrected_kda_result, adjusted_confidence)
        """
        try:
            if not kda_result or "k" not in kda_result:
                return kda_result, confidence
            
            k, d, a = kda_result["k"], kda_result["d"], kda_result["a"]
            ratio = (k + a) / max(1, d)
            
            # Check for MVP-KDA ratio inconsistency
            # If MVP is around 10.5 but ratio is wildly high (like >12), re-read with tighter padding
            if 9.0 <= mvp_score <= 12.0 and ratio > 12:
                debug_info["mvp_inconsistency_detected"] = {
                    "mvp_score": mvp_score,
                    "kda_ratio": ratio,
                    "original_kda": f"{k}/{d}/{a}"
                }
                
                # Re-read with tighter padding around slash positions
                if slash_positions:
                    repaired_result, repair_confidence = self._repair_with_tighter_padding(
                        processed_crop, slash_positions, debug_info
                    )
                    
                    if repaired_result:
                        repair_k, repair_d, repair_a = repaired_result["k"], repaired_result["d"], repaired_result["a"]
                        repair_ratio = (repair_k + repair_a) / max(1, repair_d)
                        
                        # Use repaired result if it has lower ratio variance with MVP
                        mvp_expected_ratio = mvp_score / 1.0  # Rough heuristic
                        original_variance = abs(ratio - mvp_expected_ratio)
                        repair_variance = abs(repair_ratio - mvp_expected_ratio)
                        
                        if repair_variance < original_variance:
                            debug_info["repair_successful"] = {
                                "original": f"{k}/{d}/{a} (ratio={ratio:.2f})",
                                "repaired": f"{repair_k}/{repair_d}/{repair_a} (ratio={repair_ratio:.2f})",
                                "mvp_score": mvp_score
                            }
                            return repaired_result, min(1.0, repair_confidence + 0.1)
            
            # Check for reasonable MVP-KDA correlation
            expected_ratio_range = (mvp_score * 0.8, mvp_score * 1.2)  # Allow 20% variance
            if not (expected_ratio_range[0] <= ratio <= expected_ratio_range[1]):
                # Lower confidence for inconsistent results
                confidence *= 0.8
                debug_info["mvp_kda_inconsistency"] = {
                    "mvp_score": mvp_score,
                    "kda_ratio": ratio,
                    "expected_range": expected_ratio_range
                }
            
            return kda_result, confidence
            
        except Exception as e:
            debug_info["mvp_sanity_check_error"] = str(e)
            return kda_result, confidence * 0.9  # Slight confidence penalty for errors
    
    def _repair_with_tighter_padding(self, processed_crop: np.ndarray, slash_positions: List[int],
                                   debug_info: Dict[str, Any]) -> Tuple[Optional[Dict[str, int]], float]:
        """
        Re-parse KDA with tighter padding around slash positions
        
        Args:
            processed_crop: Binary preprocessed crop
            slash_positions: List of slash x-coordinates
            debug_info: Debug information
            
        Returns:
            Tuple of (repaired_kda_dict, confidence)
        """
        try:
            height, width = processed_crop.shape
            tight_padding = 2  # Tighter padding (was 4)
            
            # Define segments with tighter padding
            segments = []
            
            if len(slash_positions) >= 2:
                slash1_x, slash2_x = slash_positions[0], slash_positions[1]
                
                # K segment: start to first slash
                segments.append(("k", max(0, 0), min(width, slash1_x - tight_padding)))
                
                # D segment: first slash to second slash  
                segments.append(("d", max(0, slash1_x + tight_padding), min(width, slash2_x - tight_padding)))
                
                # A segment: second slash to end
                segments.append(("a", max(0, slash2_x + tight_padding), width))
            
            debug_info["repair_segments"] = [(name, x1, x2) for name, x1, x2 in segments]
            
            # OCR each segment with tighter constraints
            kda_values = {}
            confidences = []
            
            for segment_name, x1, x2 in segments:
                if x2 <= x1:
                    continue
                
                # Extract segment
                segment_crop = processed_crop[:, x1:x2]
                
                if segment_crop.size == 0:
                    continue
                
                # OCR the segment
                value, segment_confidence = self._ocr_digit_segment(segment_crop, segment_name)
                
                if value is not None:
                    kda_values[segment_name] = value
                    confidences.append(segment_confidence)
            
            # Validate we have all three values
            if len(kda_values) == 3 and all(key in kda_values for key in ["k", "d", "a"]):
                k, d, a = kda_values["k"], kda_values["d"], kda_values["a"]
                
                if self._validate_kda_values(k, d, a):
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    result = {
                        "k": k,
                        "d": d,
                        "a": a,
                        "ratio": (k + a) / max(1, d)
                    }
                    
                    return result, avg_confidence
            
            return None, 0.0
            
        except Exception as e:
            debug_info["repair_error"] = str(e)
            return None, 0.0
    
    def _extract_slash_candidates(self, processed_crop: np.ndarray, slash_positions: List[int], 
                                 kda_bbox: Tuple[int, int, int, int]) -> List[Dict[str, Any]]:
        """
        Extract KDA candidates using slash-guided segmentation
        
        Args:
            processed_crop: Binary preprocessed crop
            slash_positions: List of slash x-coordinates
            kda_bbox: KDA cell bounding box for center_x calculation
            
        Returns:
            List of candidate dictionaries with k, d, a, conf, center_x
        """
        candidates = []
        
        try:
            height, width = processed_crop.shape
            padding = 4
            
            if len(slash_positions) >= 2:
                slash1_x, slash2_x = slash_positions[0], slash_positions[1]
                
                # Define segments based on slash positions
                segments = [
                    ("k", max(0, 0), min(width, slash1_x - padding)),
                    ("d", max(0, slash1_x + padding), min(width, slash2_x - padding)),
                    ("a", max(0, slash2_x + padding), width)
                ]
                
                # OCR each segment
                kda_values = {}
                confidences = []
                
                for segment_name, x1, x2 in segments:
                    if x2 <= x1:
                        continue
                    
                    # Extract segment
                    segment_crop = processed_crop[:, x1:x2]
                    
                    if segment_crop.size == 0:
                        continue
                    
                    # OCR the segment
                    value, segment_confidence = self._ocr_digit_segment(segment_crop, segment_name)
                    
                    if value is not None:
                        kda_values[segment_name] = value
                        confidences.append(segment_confidence)
                
                # Validate we have all three values
                if len(kda_values) == 3 and all(key in kda_values for key in ["k", "d", "a"]):
                    k, d, a = kda_values["k"], kda_values["d"], kda_values["a"]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    # Calculate center_x (middle of the KDA region)
                    center_x = width // 2
                    
                    candidates.append({
                        "k": k,
                        "d": d,
                        "a": a,
                        "conf": avg_confidence,
                        "center_x": center_x,
                        "method": "slash_guided"
                    })
            
        except Exception as e:
            print(f"Error in slash candidate extraction: {e}")
        
        return candidates
    
    def _extract_regex_candidates(self, crop: np.ndarray, kda_bbox: Tuple[int, int, int, int]) -> List[Dict[str, Any]]:
        """
        Extract KDA candidates using regex-based parsing
        
        Args:
            crop: Raw crop image
            kda_bbox: KDA cell bounding box for center_x calculation
            
        Returns:
            List of candidate dictionaries with k, d, a, conf, center_x
        """
        candidates = []
        
        if self.ocr_reader is None:
            return candidates
        
        try:
            # Convert to RGB if needed
            if len(crop.shape) == 3:
                rgb_crop = crop
            else:
                rgb_crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2RGB)
            
            # OCR with allowlist for digits and slash
            results = self.ocr_reader.readtext(
                rgb_crop,
                allowlist='0123456789/',
                detail=1
            )
            
            # Look for KDA patterns in OCR results
            import re
            for (bbox_coords, text, confidence) in results:
                if confidence < 0.3:
                    continue
                
                # Regex pattern for KDA
                pattern = r'\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})\b'
                matches = re.findall(pattern, text)
                
                if matches:
                    k, d, a = map(int, matches[0])
                    
                    # Calculate center_x from bbox
                    x_coords = [point[0] for point in bbox_coords]
                    center_x = sum(x_coords) / len(x_coords)
                    
                    candidates.append({
                        "k": k,
                        "d": d,
                        "a": a,
                        "conf": confidence,
                        "center_x": center_x,
                        "method": "regex_full"
                    })
            
            # Also try extracting individual numbers and forming KDA
            numbers = []
            for (bbox_coords, text, confidence) in results:
                if confidence < 0.5:
                    continue
                
                # Extract individual numbers
                number_matches = re.findall(r'\d+', text)
                for num_str in number_matches:
                    try:
                        value = int(num_str)
                        if 0 <= value <= 30:  # Reasonable range for KDA
                            x_coords = [point[0] for point in bbox_coords]
                            center_x = sum(x_coords) / len(x_coords)
                            numbers.append((value, center_x, confidence))
                    except ValueError:
                        continue
            
            # Sort numbers by x-coordinate and try to form KDA triplets
            numbers.sort(key=lambda x: x[1])  # Sort by center_x
            
            for i in range(len(numbers) - 2):
                k_val, k_x, k_conf = numbers[i]
                d_val, d_x, d_conf = numbers[i + 1]
                a_val, a_x, a_conf = numbers[i + 2]
                
                # Check if they are reasonably spaced
                if (d_x - k_x > 10) and (a_x - d_x > 10):  # Minimum spacing
                    avg_confidence = (k_conf + d_conf + a_conf) / 3
                    center_x = (k_x + a_x) / 2  # Center of the triplet
                    
                    candidates.append({
                        "k": k_val,
                        "d": d_val,
                        "a": a_val,
                        "conf": avg_confidence,
                        "center_x": center_x,
                        "method": "number_sequence"
                    })
            
        except Exception as e:
            print(f"Error in regex candidate extraction: {e}")
        
        return candidates
    
    def _validate_kda_values(self, k: int, d: int, a: int) -> bool:
        """
        Validate KDA values for reasonableness
        
        Args:
            k, d, a: Kill, death, assist values
            
        Returns:
            True if values are reasonable
        """
        # Basic range checks
        if not (0 <= k <= 30 and 0 <= d <= 30 and 0 <= a <= 30):
            return False
        
        # Ratio sanity check
        ratio = (k + a) / max(1, d)
        if ratio > 50:  # Unreasonably high ratio
            return False
        
        return True
    
    def _fallback_result(self, reason: str, debug_info: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, int], float]:
        """
        Generate fallback result with low confidence
        
        Args:
            reason: Reason for fallback
            debug_info: Optional debug information
            
        Returns:
            Tuple of (fallback_kda_dict, low_confidence)
        """
        if debug_info is None:
            debug_info = {}
        
        debug_info["fallback_reason"] = reason
        
        # Return zero values with very low confidence
        result = {
            "k": 0,
            "d": 1,  # Avoid division by zero
            "a": 0,
            "ratio": 0.0
        }
        
        return result, 0.1


def read_kda_from_cell(row_img: np.ndarray, kda_bbox: Tuple[int, int, int, int], 
                      mvp_score: Optional[float] = None, name_x2: Optional[int] = None) -> Tuple[Dict[str, int], float]:
    """
    Module-level function for reading KDA from cell with spatial filtering
    
    Args:
        row_img: Image of the player row
        kda_bbox: (x1, y1, x2, y2) absolute coordinates of KDA cell
        mvp_score: Optional MVP score for sanity checking
        name_x2: Optional right edge of IGN for spatial filtering
        
    Returns:
        Tuple of (kda_dict, confidence_score)
    """
    reader = KDACellReader()
    return reader.read_kda_from_cell(row_img, kda_bbox, mvp_score, name_x2)


def read_kda_by_regex(crop: np.ndarray) -> Tuple[Dict[str, int], float]:
    """
    Module-level function for regex-based KDA reading
    
    Args:
        crop: Crop image of KDA cell
        
    Returns:
        Tuple of (kda_dict, confidence_score)
    """
    reader = KDACellReader()
    debug_info = {}
    return reader._parse_with_regex(crop, debug_info)


if __name__ == "__main__":
    # Test the KDA cell reader
    import sys
    from pathlib import Path
    
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
        if image_path.exists():
            image = cv2.imread(str(image_path))
            # Test with mock bbox
            bbox = (100, 50, 200, 80)  # Example bbox
            result, confidence = read_kda_from_cell(image, bbox)
            print(f"KDA result: {result}, confidence: {confidence}")
        else:
            print(f"Image not found: {image_path}")
    else:
        print("Usage: python kda_cell_reader.py <image_path>")