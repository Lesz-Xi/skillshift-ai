"""
Fast Table Detection for Mission 3
Implements anchor-based detection with projections for <500ms performance.
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FastTableDetector:
    """
    Fast table detection using anchor-based approach with projections.
    
    Features:
    - Downscale → Otsu thresholding
    - Anchor detection (Victory/Defeat, Hero Damage, slash patterns)
    - Row detection via vertical projections
    - Ratio-based coordinates for scalability
    """
    
    def __init__(self, downscale_size: int = 1280):
        """
        Initialize fast table detector.
        
        Args:
            downscale_size: Maximum size for downscaling
        """
        self.downscale_size = downscale_size
        self.anchor_templates = self._load_anchor_templates()
        
    def _load_anchor_templates(self) -> Dict[str, List[str]]:
        """Load anchor text patterns for detection."""
        return {
            'victory': ['victory', 'win', 'defeat', 'lose', 'mvp'],
            'damage': ['hero damage', 'damage', 'dmg', 'hero'],
            'kda': ['kda', 'k/d/a', 'kills', 'deaths', 'assists'],
            'slash': ['/', '\\', '|'],
            'numbers': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        }
    
    def detect_table_structure(self, image_input) -> Dict[str, Any]:
        """
        Detect table structure using fast anchor-based approach.
        
        Args:
            image_input: Image path or numpy array
            
        Returns:
            Table structure with rows, columns, and confidence
        """
        try:
            # Load and preprocess image
            image = self._load_and_preprocess(image_input)
            original_shape = image.shape[:2]
            
            # Detect anchors
            anchors = self._detect_anchors(image)
            
            # Build table structure from anchors
            table_structure = self._build_table_from_anchors(anchors, original_shape)
            
            # Detect rows using projections
            rows = self._detect_rows_with_projections(image, anchors)
            
            # Combine results
            result = {
                'bbox': self._calculate_table_bbox(anchors, original_shape),
                'rows_count': len(rows),
                'columns_count': self._estimate_columns(anchors),
                'confidence': self._calculate_confidence(anchors, rows),
                'anchors': anchors,
                'row_crops': rows,
                'table_structure': table_structure
            }
            
            logger.debug(f"Detected table: {result['rows_count']} rows, {result['columns_count']} columns")
            return result
            
        except Exception as e:
            logger.error(f"Table detection failed: {e}")
            return self._empty_table_structure()
    
    def _load_and_preprocess(self, image_input) -> np.ndarray:
        """Load and preprocess image for fast detection."""
        try:
            # Load image
            if isinstance(image_input, (str, Path)):
                image = cv2.imread(str(image_input))
                if image is None:
                    raise ValueError(f"Could not load image: {image_input}")
            else:
                image = image_input.copy()
            
            # Downscale for faster processing
            h, w = image.shape[:2]
            if max(h, w) > self.downscale_size:
                scale = self.downscale_size / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                image = cv2.resize(image, (new_w, new_h), cv2.INTER_AREA)
                logger.debug(f"Downscaled image: {w}x{h} -> {new_w}x{new_h}")
            
            return image
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return np.zeros((64, 64, 3), dtype=np.uint8)
    
    def _detect_anchors(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect anchor points for table structure.
        
        Args:
            image: Preprocessed image
            
        Returns:
            List of detected anchors
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Otsu thresholding
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            anchors = []
            h, w = image.shape[:2]
            
            for contour in contours:
                x, y, cw, ch = cv2.boundingRect(contour)
                
                # Filter by size
                if cw < 20 or ch < 10 or cw > w * 0.8 or ch > h * 0.8:
                    continue
                
                # Calculate relative position
                rel_x = x / w
                rel_y = y / h
                rel_w = cw / w
                rel_h = ch / h
                
                # Classify anchor type based on position and size
                anchor_type = self._classify_anchor(rel_x, rel_y, rel_w, rel_h)
                
                if anchor_type:
                    anchor = {
                        'type': anchor_type,
                        'bbox': (x, y, cw, ch),
                        'relative_bbox': (rel_x, rel_y, rel_w, rel_h),
                        'confidence': self._calculate_anchor_confidence(contour, anchor_type)
                    }
                    anchors.append(anchor)
            
            # Sort anchors by Y position
            anchors.sort(key=lambda a: a['bbox'][1])
            
            logger.debug(f"Detected {len(anchors)} anchors")
            return anchors
            
        except Exception as e:
            logger.error(f"Anchor detection failed: {e}")
            return []
    
    def _classify_anchor(self, rel_x: float, rel_y: float, rel_w: float, rel_h: float) -> Optional[str]:
        """
        Classify anchor type based on position and size.
        
        Args:
            rel_x, rel_y, rel_w, rel_h: Relative coordinates and dimensions
            
        Returns:
            Anchor type or None
        """
        # Victory/Defeat banners (top of screen, wide)
        if rel_y < 0.2 and rel_w > 0.3 and rel_h < 0.1:
            return 'victory'
        
        # Damage labels (left side, medium width)
        elif rel_x < 0.3 and 0.1 < rel_w < 0.4 and rel_h < 0.05:
            return 'damage'
        
        # KDA patterns (right side, narrow)
        elif rel_x > 0.6 and rel_w < 0.3 and rel_h < 0.05:
            return 'kda'
        
        # Slash patterns (center, very small)
        elif 0.3 < rel_x < 0.7 and rel_w < 0.1 and rel_h < 0.03:
            return 'slash'
        
        # Number patterns (various positions, small)
        elif rel_w < 0.05 and rel_h < 0.03:
            return 'numbers'
        
        return None
    
    def _calculate_anchor_confidence(self, contour, anchor_type: str) -> float:
        """Calculate confidence score for anchor."""
        try:
            # Basic confidence based on contour properties
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            if perimeter == 0:
                return 0.0
            
            # Circularity score
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # Aspect ratio score
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            # Type-specific scoring
            if anchor_type == 'victory':
                # Victory banners should be wide and not too tall
                aspect_score = min(1.0, aspect_ratio / 3.0)
            elif anchor_type == 'damage':
                # Damage labels should be moderately wide
                aspect_score = min(1.0, aspect_ratio / 2.0)
            elif anchor_type == 'kda':
                # KDA should be compact
                aspect_score = min(1.0, aspect_ratio / 1.5)
            else:
                aspect_score = 0.5
            
            # Combine scores
            confidence = (circularity * 0.3 + aspect_score * 0.7)
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _build_table_from_anchors(self, anchors: List[Dict[str, Any]], original_shape: Tuple[int, int]) -> Dict[str, Any]:
        """Build table structure from detected anchors."""
        try:
            if not anchors:
                return {'rows': 0, 'columns': 0, 'structure': []}
            
            # Group anchors by Y position (rows)
            y_tolerance = 20  # Pixels
            rows = []
            current_row = []
            
            for anchor in anchors:
                y = anchor['bbox'][1]
                
                if not current_row:
                    current_row = [anchor]
                else:
                    # Check if this anchor is in the same row
                    last_y = current_row[-1]['bbox'][1]
                    if abs(y - last_y) <= y_tolerance:
                        current_row.append(anchor)
                    else:
                        # Start new row
                        if current_row:
                            rows.append(current_row)
                        current_row = [anchor]
            
            # Add last row
            if current_row:
                rows.append(current_row)
            
            # Build structure
            structure = []
            for i, row in enumerate(rows):
                row_data = {
                    'row_id': i,
                    'y_position': row[0]['bbox'][1],
                    'anchors': row,
                    'anchor_count': len(row)
                }
                structure.append(row_data)
            
            return {
                'rows': len(rows),
                'columns': max(len(row) for row in rows) if rows else 0,
                'structure': structure
            }
            
        except Exception as e:
            logger.error(f"Table structure building failed: {e}")
            return {'rows': 0, 'columns': 0, 'structure': []}
    
    def _detect_rows_with_projections(self, image: np.ndarray, anchors: List[Dict[str, Any]]) -> List[np.ndarray]:
        """
        Detect table rows using vertical projections.
        
        Args:
            image: Preprocessed image
            anchors: Detected anchors
            
        Returns:
            List of row crop images
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            # Create projection mask
            projection_mask = np.zeros_like(gray)
            
            # Add anchor regions to mask
            for anchor in anchors:
                x, y, cw, ch = anchor['bbox']
                projection_mask[y:y+ch, x:x+cw] = 255
            
            # Vertical projection
            vertical_projection = np.sum(projection_mask, axis=1)
            
            # Find projection peaks (potential row centers)
            peaks = self._find_projection_peaks(vertical_projection)
            
            # Extract row crops
            row_crops = []
            row_height = 30  # Approximate row height
            
            for peak in peaks:
                y_start = max(0, peak - row_height // 2)
                y_end = min(h, peak + row_height // 2)
                
                if y_end - y_start > 10:  # Minimum row height
                    row_crop = image[y_start:y_end, :]
                    row_crops.append(row_crop)
            
            logger.debug(f"Detected {len(row_crops)} rows from projections")
            return row_crops
            
        except Exception as e:
            logger.error(f"Row detection failed: {e}")
            return []
    
    def _find_projection_peaks(self, projection: np.ndarray, min_height: int = 50) -> List[int]:
        """Find peaks in vertical projection."""
        try:
            peaks = []
            threshold = np.mean(projection) + np.std(projection)
            
            for i in range(1, len(projection) - 1):
                if (projection[i] > threshold and 
                    projection[i] > projection[i-1] and 
                    projection[i] > projection[i+1]):
                    peaks.append(i)
            
            # Filter peaks by minimum height
            peaks = [p for p in peaks if projection[p] >= min_height]
            
            return peaks
            
        except Exception as e:
            logger.error(f"Peak finding failed: {e}")
            return []
    
    def _calculate_table_bbox(self, anchors: List[Dict[str, Any]], original_shape: Tuple[int, int]) -> Tuple[float, float, float, float]:
        """Calculate table bounding box as ratios."""
        try:
            if not anchors:
                return (0.0, 0.0, 1.0, 1.0)
            
            # Find min/max coordinates
            min_x = min(anchor['bbox'][0] for anchor in anchors)
            min_y = min(anchor['bbox'][1] for anchor in anchors)
            max_x = max(anchor['bbox'][0] + anchor['bbox'][2] for anchor in anchors)
            max_y = max(anchor['bbox'][1] + anchor['bbox'][3] for anchor in anchors)
            
            # Convert to ratios
            h, w = original_shape
            rel_x = min_x / w
            rel_y = min_y / h
            rel_w = (max_x - min_x) / w
            rel_h = (max_y - min_y) / h
            
            return (rel_x, rel_y, rel_w, rel_h)
            
        except Exception as e:
            logger.error(f"Bbox calculation failed: {e}")
            return (0.0, 0.0, 1.0, 1.0)
    
    def _estimate_columns(self, anchors: List[Dict[str, Any]]) -> int:
        """Estimate number of columns from anchors."""
        try:
            if not anchors:
                return 0
            
            # Group by Y position to find rows
            y_tolerance = 20
            rows = []
            current_row = []
            
            for anchor in anchors:
                y = anchor['bbox'][1]
                
                if not current_row:
                    current_row = [anchor]
                else:
                    last_y = current_row[-1]['bbox'][1]
                    if abs(y - last_y) <= y_tolerance:
                        current_row.append(anchor)
                    else:
                        if current_row:
                            rows.append(current_row)
                        current_row = [anchor]
            
            if current_row:
                rows.append(current_row)
            
            # Return maximum columns in any row
            return max(len(row) for row in rows) if rows else 0
            
        except Exception as e:
            logger.error(f"Column estimation failed: {e}")
            return 0
    
    def _calculate_confidence(self, anchors: List[Dict[str, Any]], rows: List[np.ndarray]) -> float:
        """Calculate overall detection confidence."""
        try:
            if not anchors:
                return 0.0
            
            # Base confidence from anchor count
            anchor_confidence = min(1.0, len(anchors) / 10.0)
            
            # Row confidence
            row_confidence = min(1.0, len(rows) / 5.0)
            
            # Average anchor confidence
            avg_anchor_conf = np.mean([a['confidence'] for a in anchors]) if anchors else 0.0
            
            # Combined confidence
            total_confidence = (anchor_confidence * 0.4 + 
                              row_confidence * 0.3 + 
                              avg_anchor_conf * 0.3)
            
            return min(1.0, max(0.0, total_confidence))
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    def _empty_table_structure(self) -> Dict[str, Any]:
        """Return empty table structure for error cases."""
        return {
            'bbox': (0.0, 0.0, 1.0, 1.0),
            'rows_count': 0,
            'columns_count': 0,
            'confidence': 0.0,
            'anchors': [],
            'row_crops': [],
            'table_structure': {'rows': 0, 'columns': 0, 'structure': []}
        }


class ProjectionBasedDetector:
    """
    Alternative detector using projection-based approach.
    """
    
    def __init__(self, downscale_size: int = 1280):
        self.downscale_size = downscale_size
    
    def detect_table_rows(self, image_input) -> List[Tuple[int, int, int, int]]:
        """
        Detect table rows using horizontal projections.
        
        Args:
            image_input: Image path or numpy array
            
        Returns:
            List of (x, y, w, h) bounding boxes for rows
        """
        try:
            # Load and preprocess
            if isinstance(image_input, (str, Path)):
                image = cv2.imread(str(image_input))
            else:
                image = image_input.copy()
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Downscale
            h, w = gray.shape
            if max(h, w) > self.downscale_size:
                scale = self.downscale_size / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                gray = cv2.resize(gray, (new_w, new_h), cv2.INTER_AREA)
                scale_factor = 1.0 / scale
            else:
                scale_factor = 1.0
            
            # Apply Otsu thresholding
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Horizontal projection
            horizontal_projection = np.sum(binary, axis=1)
            
            # Find row boundaries
            row_boundaries = self._find_row_boundaries(horizontal_projection)
            
            # Convert back to original coordinates
            rows = []
            for y_start, y_end in row_boundaries:
                # Scale back to original coordinates
                orig_y_start = int(y_start * scale_factor)
                orig_y_end = int(y_end * scale_factor)
                
                rows.append((0, orig_y_start, w, orig_y_end - orig_y_start))
            
            return rows
            
        except Exception as e:
            logger.error(f"Row detection failed: {e}")
            return []
    
    def _find_row_boundaries(self, projection: np.ndarray, min_gap: int = 10) -> List[Tuple[int, int]]:
        """Find row boundaries in horizontal projection."""
        try:
            # Find gaps (low projection values)
            gaps = []
            in_gap = False
            gap_start = 0
            
            threshold = np.mean(projection) * 0.5
            
            for i, value in enumerate(projection):
                if value < threshold:
                    if not in_gap:
                        gap_start = i
                        in_gap = True
                else:
                    if in_gap:
                        gap_length = i - gap_start
                        if gap_length >= min_gap:
                            gaps.append((gap_start, i))
                        in_gap = False
            
            # Convert gaps to row boundaries
            rows = []
            prev_end = 0
            
            for gap_start, gap_end in gaps:
                if gap_start > prev_end:
                    rows.append((prev_end, gap_start))
                prev_end = gap_end
            
            # Add final row if needed
            if prev_end < len(projection):
                rows.append((prev_end, len(projection)))
            
            return rows
            
        except Exception as e:
            logger.error(f"Boundary finding failed: {e}")
            return []
