"""
Optimized ROI Processor for Mission 3
Implements ROI-only OCR with digits allowlist and downscaling for <500ms performance.
"""
import cv2
import numpy as np
import logging
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class OptimizedROIProcessor:
    """
    Optimized ROI processor for fast OCR with digits-only allowlist.
    
    Features:
    - Smart downscaling (≤512px max side)
    - Digits-only allowlist for OCR
    - Otsu binarization for better text recognition
    - ROI-specific preprocessing
    """
    
    def __init__(self, max_side: int = 512, min_side: int = 64):
        """
        Initialize ROI processor.
        
        Args:
            max_side: Maximum side length for downscaling
            min_side: Minimum side length to prevent over-downscaling
        """
        self.max_side = max_side
        self.min_side = min_side
        self.allowlist = "0123456789/%,."
        
    def prep_digits_roi(self, image_input, max_side: Optional[int] = None) -> np.ndarray:
        """
        Prepare ROI for digits-only OCR with optimized preprocessing.
        
        Args:
            image_input: Image path (str) or numpy array
            max_side: Override max side length
            
        Returns:
            Preprocessed binary image optimized for digits OCR
        """
        try:
            # Load image
            if isinstance(image_input, (str, Path)):
                bgr = cv2.imread(str(image_input))
                if bgr is None:
                    raise ValueError(f"Could not load image: {image_input}")
            else:
                bgr = image_input.copy()
            
            # Get dimensions
            h, w = bgr.shape[:2]
            max_dim = max(h, w)
            target_max = max_side or self.max_side
            
            # Smart downscaling
            if max_dim > target_max:
                scale = min(1.0, target_max / max_dim)
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                # Ensure minimum size
                if min(new_w, new_h) < self.min_side:
                    scale = self.min_side / min(w, h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                
                bgr = cv2.resize(bgr, (new_w, new_h), cv2.INTER_AREA)
                logger.debug(f"Downscaled image: {w}x{h} -> {new_w}x{new_h} (scale: {scale:.3f})")
            
            # Convert to grayscale
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Otsu binarization for optimal threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Optional: Apply morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            logger.debug(f"ROI preprocessing complete: {binary.shape}")
            return binary
            
        except Exception as e:
            logger.error(f"ROI preprocessing failed: {e}")
            # Return a minimal valid image as fallback
            return np.zeros((64, 64), dtype=np.uint8)
    
    def extract_digits_from_roi(self, roi_image: np.ndarray, 
                               reader, 
                               allowlist: Optional[str] = None) -> List[str]:
        """
        Extract digits from preprocessed ROI using cached OCR.
        
        Args:
            roi_image: Preprocessed binary ROI image
            reader: EasyOCR reader instance
            allowlist: Characters to allow (defaults to digits)
            
        Returns:
            List of extracted text strings
        """
        try:
            allowlist = allowlist or self.allowlist
            
            # Use cached OCR with allowlist
            from .ocr_cache import OCRCache
            cache = OCRCache()
            texts = cache.cached_readtext(reader, roi_image, allowlist=allowlist)
            
            # Filter and clean results
            cleaned_texts = []
            for text in texts:
                if text and text.strip():
                    # Remove non-allowlist characters
                    cleaned = ''.join(c for c in text if c in allowlist)
                    if cleaned:
                        cleaned_texts.append(cleaned)
            
            logger.debug(f"Extracted {len(cleaned_texts)} digit texts from ROI")
            return cleaned_texts
            
        except Exception as e:
            logger.error(f"Digit extraction failed: {e}")
            return []
    
    def detect_table_regions(self, image_input) -> List[Tuple[int, int, int, int]]:
        """
        Detect table regions using fast anchor-based detection.
        
        Args:
            image_input: Image path or numpy array
            
        Returns:
            List of (x, y, w, h) bounding boxes for table regions
        """
        try:
            # Load and preprocess image
            if isinstance(image_input, (str, Path)):
                image = cv2.imread(str(image_input))
            else:
                image = image_input.copy()
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Downscale for faster processing
            h, w = gray.shape
            if max(h, w) > 1280:
                scale = 1280 / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                gray = cv2.resize(gray, (new_w, new_h), cv2.INTER_AREA)
            
            # Apply Otsu thresholding
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find horizontal lines (table rows)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Find vertical lines (table columns)
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine lines
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter and return bounding boxes
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter by size (reasonable table region)
                if w > 100 and h > 50:
                    regions.append((x, y, w, h))
            
            logger.debug(f"Detected {len(regions)} table regions")
            return regions
            
        except Exception as e:
            logger.error(f"Table region detection failed: {e}")
            return []
    
    def extract_roi_crops(self, image_input, regions: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """
        Extract ROI crops from detected regions.
        
        Args:
            image_input: Image path or numpy array
            regions: List of (x, y, w, h) bounding boxes
            
        Returns:
            List of cropped ROI images
        """
        try:
            # Load image
            if isinstance(image_input, (str, Path)):
                image = cv2.imread(str(image_input))
            else:
                image = image_input.copy()
            
            crops = []
            for x, y, w, h in regions:
                # Ensure coordinates are within image bounds
                x = max(0, x)
                y = max(0, y)
                w = min(w, image.shape[1] - x)
                h = min(h, image.shape[0] - y)
                
                if w > 0 and h > 0:
                    crop = image[y:y+h, x:x+w]
                    crops.append(crop)
            
            logger.debug(f"Extracted {len(crops)} ROI crops")
            return crops
            
        except Exception as e:
            logger.error(f"ROI crop extraction failed: {e}")
            return []
    
    def process_roi_batch(self, image_input, 
                         reader,
                         max_regions: int = 5) -> List[Dict[str, Any]]:
        """
        Process multiple ROI regions in batch for optimal performance.
        
        Args:
            image_input: Image path or numpy array
            reader: EasyOCR reader instance
            max_regions: Maximum number of regions to process
            
        Returns:
            List of processed ROI results
        """
        try:
            # Detect table regions
            regions = self.detect_table_regions(image_input)
            
            # Limit regions for performance
            regions = regions[:max_regions]
            
            # Extract crops
            crops = self.extract_roi_crops(image_input, regions)
            
            # Process each crop
            results = []
            for i, crop in enumerate(crops):
                # Preprocess for digits
                roi_binary = self.prep_digits_roi(crop)
                
                # Extract digits
                texts = self.extract_digits_from_roi(roi_binary, reader)
                
                results.append({
                    'region_id': i,
                    'bbox': regions[i] if i < len(regions) else None,
                    'texts': texts,
                    'text_count': len(texts)
                })
            
            logger.debug(f"Processed {len(results)} ROI regions in batch")
            return results
            
        except Exception as e:
            logger.error(f"ROI batch processing failed: {e}")
            return []


class FastTableDetector:
    """
    Fast table detection using anchor-based approach.
    """
    
    def __init__(self):
        self.anchor_templates = {
            'victory': ['victory', 'win', 'defeat', 'lose'],
            'damage': ['hero damage', 'damage', 'dmg'],
            'kda': ['kda', 'k/d/a', 'kills', 'deaths', 'assists']
        }
    
    def detect_anchors(self, image_input) -> Dict[str, List[Tuple[int, int, int, int]]]:
        """
        Detect anchor points for table structure.
        
        Args:
            image_input: Image path or numpy array
            
        Returns:
            Dictionary of anchor types and their bounding boxes
        """
        try:
            # Load image
            if isinstance(image_input, (str, Path)):
                image = cv2.imread(str(image_input))
            else:
                image = image_input.copy()
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Downscale for faster processing
            h, w = gray.shape
            if max(h, w) > 1280:
                scale = 1280 / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                gray = cv2.resize(gray, (new_w, new_h), cv2.INTER_AREA)
                scale_factor = 1.0 / scale
            else:
                scale_factor = 1.0
            
            # Apply Otsu thresholding
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find text regions using contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            anchors = {key: [] for key in self.anchor_templates.keys()}
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Scale back to original coordinates
                x = int(x * scale_factor)
                y = int(y * scale_factor)
                w = int(w * scale_factor)
                h = int(h * scale_factor)
                
                # Filter by size
                if w > 50 and h > 20:
                    # Extract text region for OCR
                    text_region = image[y:y+h, x:x+w]
                    
                    # Simple text detection (could be enhanced with actual OCR)
                    # For now, use heuristics based on region characteristics
                    if h > w * 0.3:  # Tall regions might be text
                        anchors['victory'].append((x, y, w, h))
                    elif w > h * 2:  # Wide regions might be damage/KDA
                        anchors['damage'].append((x, y, w, h))
                    else:
                        anchors['kda'].append((x, y, w, h))
            
            logger.debug(f"Detected anchors: {sum(len(v) for v in anchors.values())} total")
            return anchors
            
        except Exception as e:
            logger.error(f"Anchor detection failed: {e}")
            return {key: [] for key in self.anchor_templates.keys()}
    
    def build_table_structure(self, image_input) -> Dict[str, Any]:
        """
        Build table structure from detected anchors.
        
        Args:
            image_input: Image path or numpy array
            
        Returns:
            Table structure with rows and columns
        """
        try:
            anchors = self.detect_anchors(image_input)
            
            # Simple row detection based on Y coordinates
            all_regions = []
            for anchor_type, regions in anchors.items():
                for region in regions:
                    all_regions.append((region, anchor_type))
            
            # Sort by Y coordinate to find rows
            all_regions.sort(key=lambda x: x[0][1])
            
            # Group into rows (regions with similar Y coordinates)
            rows = []
            current_row = []
            y_tolerance = 30  # Pixels
            
            for region, anchor_type in all_regions:
                x, y, w, h = region
                
                if not current_row:
                    current_row.append((region, anchor_type))
                else:
                    # Check if this region is in the same row
                    last_y = current_row[-1][0][1]
                    if abs(y - last_y) <= y_tolerance:
                        current_row.append((region, anchor_type))
                    else:
                        # Start new row
                        if current_row:
                            rows.append(current_row)
                        current_row = [(region, anchor_type)]
            
            # Add last row
            if current_row:
                rows.append(current_row)
            
            # Build table structure
            table_structure = {
                'rows': len(rows),
                'columns': max(len(row) for row in rows) if rows else 0,
                'row_data': []
            }
            
            for i, row in enumerate(rows):
                row_data = {
                    'row_id': i,
                    'y_position': row[0][0][1] if row else 0,
                    'regions': [{'bbox': region, 'type': anchor_type} for region, anchor_type in row]
                }
                table_structure['row_data'].append(row_data)
            
            logger.debug(f"Built table structure: {len(rows)} rows")
            return table_structure
            
        except Exception as e:
            logger.error(f"Table structure building failed: {e}")
            return {'rows': 0, 'columns': 0, 'row_data': []}
