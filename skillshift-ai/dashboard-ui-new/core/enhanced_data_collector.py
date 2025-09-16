import re
import os
import logging
import time
import concurrent.futures
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher
import threading
from dataclasses import dataclass
import json

import cv2
import numpy as np

# Import IGN matching helper
try:
    from backend.ocr.normalizers import is_ign_match
except ImportError:
    # Fallback if backend module not available
    def is_ign_match(target_ign: str, ocr_text: str) -> bool:
        return target_ign.lower() in ocr_text.lower()

# Define simple types to replace the missing classes
SCREENSHOT_TYPE_SCOREBOARD = "scoreboard"
SCREENSHOT_TYPE_STATS = "stats"
SCREENSHOT_TYPE_UNKNOWN = "unknown"

# Handle both module and script execution
try:
    from .data_collector import DataCollector, get_ocr_reader
    from .session_manager import SessionManager
    from .screenshot_analyzer import ScreenshotAnalyzer
    from .ign_validator import IGNValidator
    from .trophy_medal_detector_v3 import (
        advanced_trophy_medal_detector as trophy_medal_detector
    )
    from .hero_database import HeroDatabase
    from .ocr_utils import has_img, read_int, read_kda, compute_gpm
    # Lazy/optional YOLO service import to avoid heavy deps during basic OCR testing
    try:
        from .services.yolo_detection_service import get_yolo_detection_service  # type: ignore
        _YOLO_AVAILABLE = True
    except Exception:
        _YOLO_AVAILABLE = False
        def get_yolo_detection_service():  # type: ignore
            return None
    from .row_specific_hero_detector import RowSpecificHeroDetector
    # Optional enhanced OCR processor
    try:
        from .enhanced_ocr_processor import (
            EnhancedOCRProcessor,
            PreprocessingMethod,
            OCREngine,
        )
        _ENHANCED_OCR_AVAILABLE = True
    except Exception:
        _ENHANCED_OCR_AVAILABLE = False
except ImportError:
    # Fallback for when running as script
    from data_collector import DataCollector, get_ocr_reader
    from session_manager import SessionManager
    from screenshot_analyzer import ScreenshotAnalyzer
    from ign_validator import IGNValidator
    from trophy_medal_detector_v3 import (
        advanced_trophy_medal_detector as trophy_medal_detector
    )
    from hero_database import HeroDatabase
    from ocr_utils import has_img, read_int, read_kda, compute_gpm
    # Lazy/optional YOLO service import for script mode
    try:
        from services.yolo_detection_service import get_yolo_detection_service  # type: ignore
        _YOLO_AVAILABLE = True
    except Exception:
        _YOLO_AVAILABLE = False
        def get_yolo_detection_service():  # type: ignore
            return None
    from row_specific_hero_detector import RowSpecificHeroDetector
    # Optional enhanced OCR processor
    try:
        from enhanced_ocr_processor import (
            EnhancedOCRProcessor,
            PreprocessingMethod,
            OCREngine,
        )
        _ENHANCED_OCR_AVAILABLE = True
    except Exception:
        _ENHANCED_OCR_AVAILABLE = False


# MLBB-SPECIFIC ROI DEFINITIONS
@dataclass
class MLBBRegion:
    """Define regions of interest for MLBB screenshots."""
    name: str
    coordinates: Tuple[float, float, float, float]  # (x1, y1, x2, y2) as ratios
    priority: int
    ocr_config: Dict[str, Any]

class MLBBRegionDetector:
    """Detects and extracts regions of interest from MLBB screenshots."""
    
    def __init__(self):
        self.regions = {
            'scoreboard': MLBBRegion(
                'scoreboard',
                (0.1, 0.15, 0.9, 0.85),  # Central scoreboard area
                1,
                {'psm': 6, 'oem': 3}
            ),
            'player_stats': MLBBRegion(
                'player_stats',
                (0.05, 0.3, 0.95, 0.7),  # Player statistics area
                2,
                {'psm': 8, 'oem': 1}
            ),
            'team_blue': MLBBRegion(
                'team_blue',
                (0.1, 0.15, 0.9, 0.5),   # Blue team section
                3,
                {'psm': 6, 'oem': 3}
            ),
            'team_red': MLBBRegion(
                'team_red',
                (0.1, 0.5, 0.9, 0.85),   # Red team section
                3,
                {'psm': 6, 'oem': 3}
            ),
            'kda_section': MLBBRegion(
                'kda_section', 
                (0.6, 0.2, 0.85, 0.8),   # KDA columns
                2,
                {'psm': 7, 'oem': 1}
            )
        }
        
    def extract_regions(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract all ROI regions from the image."""
        regions = {}
        height, width = image.shape[:2]
        
        for region_name, region in self.regions.items():
            x1 = int(region.coordinates[0] * width)
            y1 = int(region.coordinates[1] * height)
            x2 = int(region.coordinates[2] * width)
            y2 = int(region.coordinates[3] * height)
            
            # Extract region
            roi = image[y1:y2, x1:x2]
            regions[region_name] = roi
            
        return regions
    
    def get_region_config(self, region_name: str) -> Dict[str, Any]:
        """Get OCR configuration for specific region."""
        return self.regions.get(region_name, self.regions['scoreboard']).ocr_config

# TEMPLATE MATCHING SYSTEM
class MLBBTemplateDatabase:
    """Database of MLBB UI templates for fallback detection."""
    
    def __init__(self):
        self.templates = {}
        self.template_paths = {
            'victory_banner': 'templates/victory_banner.png',
            'defeat_banner': 'templates/defeat_banner.png',
            'mvp_icon': 'templates/mvp_icon.png',
            'legendary_icon': 'templates/legendary_icon.png',
            'savage_icon': 'templates/savage_icon.png',
            'maniac_icon': 'templates/maniac_icon.png'
        }
        self._load_templates()
    
    def _load_templates(self):
        """Load template images."""
        for template_name, template_path in self.template_paths.items():
            if os.path.exists(template_path):
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    self.templates[template_name] = template
                    logger.info(f"📋 Loaded template: {template_name}")
    
    def match_template(self, image: np.ndarray, template_name: str, threshold: float = 0.8) -> List[Tuple[int, int, float]]:
        """Match template in image and return locations with confidence."""
        if template_name not in self.templates:
            return []
        
        template = self.templates[template_name]
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image
        
        # Perform template matching
        result = cv2.matchTemplate(image_gray, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        matches = []
        for pt in zip(*locations[::-1]):
            confidence = float(result[pt[1], pt[0]])
            matches.append((pt[0], pt[1], confidence))
        
        return matches

# PROGRESSIVE TIMEOUT MANAGER  
class ProgressiveTimeoutManager:
    """Manages progressive timeouts with early termination."""
    
    def __init__(self):
        self.timeouts = [10, 30, 60]  # Progressive timeout stages
        self.current_stage = 0
        self.start_time = None
        self.quality_threshold = 0.5
        
    def start_analysis(self):
        """Start the analysis timer."""
        self.start_time = time.time()
        self.current_stage = 0
        
    def should_terminate(self, quality_score: float = None) -> bool:
        """Check if analysis should terminate early."""
        if self.start_time is None:
            return False
            
        elapsed = time.time() - self.start_time
        current_timeout = self.timeouts[min(self.current_stage, len(self.timeouts) - 1)]
        
        # Early termination for low quality
        if quality_score is not None and quality_score < self.quality_threshold and elapsed > 5:
            logger.warning(f"⏰ Early termination: Low quality {quality_score:.3f} after {elapsed:.1f}s")
            return True
            
        # Stage-based timeout
        if elapsed > current_timeout:
            if self.current_stage < len(self.timeouts) - 1:
                self.current_stage += 1
                logger.info(f"⏰ Moving to timeout stage {self.current_stage + 1}")
                return False
            else:
                logger.warning(f"⏰ Final timeout reached: {elapsed:.1f}s")
                return True
                
        return False
        
    def get_remaining_time(self) -> float:
        """Get remaining time for current stage."""
        if self.start_time is None:
            return self.timeouts[0]
            
        elapsed = time.time() - self.start_time
        current_timeout = self.timeouts[min(self.current_stage, len(self.timeouts) - 1)]
        return max(0, current_timeout - elapsed)

# PERFORMANCE OPTIMIZATION: Enhanced Parallel Processing Manager
class ParallelProcessingManager:
    """
    Enhanced parallel execution manager with MLBB-specific optimizations.
    
    Features:
    - Concurrent OCR operations with region-specific processing
    - Parallel image preprocessing with quality assessment
    - Hybrid detection coordination (OCR → YOLO → Template)
    - Resource-aware thread pool management
    - Progressive timeout integration
    """
    
    def __init__(self, max_workers: int = None):
        # Optimized worker count for MLBB processing
        import os
        cpu_count = os.cpu_count() or 4
        # CRITICAL FIX: Prevent resource exhaustion causing 40+s timeouts and worker kills
        self.max_workers = max_workers or min(max(1, cpu_count // 4), 2)  # Ultra-conservative for stability
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.active_tasks = []
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.timeout_manager = ProgressiveTimeoutManager()
        
        # MLBB-specific components
        self.region_detector = MLBBRegionDetector()
        self.template_db = MLBBTemplateDatabase()
        
        # Add resource monitoring 
        self.processing_start_time = None
        self.timeout_threshold = 180  # Maximum 180 seconds per analysis (increased for session fusion)
        
        logging.info(f"🚀 Enhanced MLBB parallel processing initialized with {self.max_workers} workers (performance mode)")
        logging.warning(f"⚠️ Resource limits: max {self.timeout_threshold}s timeout, {self.max_workers} workers")
    
    def submit_task(self, func, *args, **kwargs):
        """Submit a task for parallel execution."""
        future = self.executor.submit(func, *args, **kwargs)
        self.active_tasks.append(future)
        return future
    
    def wait_for_all(self, timeout=None):
        """Wait for all active tasks to complete with intelligent timeout."""
        # Use conservative timeout to prevent resource exhaustion
        effective_timeout = timeout or min(self.timeout_threshold, 20)  # Max 20s for stability
        completed = []
        failed = []
        
        start_time = time.time()
        
        try:
            for future in concurrent.futures.as_completed(self.active_tasks, timeout=effective_timeout):
                # Check if we're approaching timeout
                elapsed = time.time() - start_time
                if elapsed > effective_timeout * 0.8:  # 80% of timeout
                    logging.warning(f"⏰ Approaching timeout ({elapsed:.1f}s), may terminate early")
                
                try:
                    result = future.result(timeout=5)  # Individual task timeout
                    completed.append(result)
                    self.completed_tasks += 1
                except Exception as e:
                    failed.append(str(e))
                    self.failed_tasks += 1
                    logging.error(f"Parallel task failed: {str(e)}")
        except concurrent.futures.TimeoutError:
            logging.error(f"❌ Parallel tasks timed out after {effective_timeout}s - terminating for stability")
            # Cancel remaining tasks to prevent resource leaks
            for future in self.active_tasks:
                future.cancel()
        
        self.active_tasks.clear()
        return completed, failed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parallel processing statistics."""
        return {
            "max_workers": self.max_workers,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.completed_tasks / max(1, self.completed_tasks + self.failed_tasks)
        }
    
    def shutdown(self):
        """Shutdown the thread pool."""
        self.executor.shutdown(wait=True)
        logging.info("🛑 Parallel processing manager shutdown")
        
logger = logging.getLogger(__name__)


def _text_from_ocr(ocr_results: List) -> str:
    """Utility: join OCR texts into one lowercase string for regex parsing."""
    try:
        return " ".join([str(t[1]) for t in ocr_results if len(t) >= 2]).lower()
    except Exception:
        return ""


class HybridDetectionEngine:
    """Implements the three-tier hybrid detection strategy: OCR → YOLO → Template Matching."""
    
    def __init__(self, data_collector):
        self.data_collector = data_collector
        self.yolo_service = None
        self.template_db = MLBBTemplateDatabase()
        self.confidence_thresholds = {
            'ocr': 0.6,
            'yolo': 0.7,
            'template': 0.8
        }
        
        # Initialize YOLO service
        try:
            self.yolo_service = get_yolo_detection_service()
            logger.info("🎯 YOLO detection service initialized")
        except Exception as e:
            logger.warning(f"⚠️ YOLO service unavailable: {e}")
    
    def analyze_with_hybrid_strategy(self, image_path: str, ign: str, preprocessing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hybrid detection strategy with progressive fallbacks."""
        results = {
            'method_used': 'none',
            'confidence': 0.0,
            'data': {},
            'fallback_attempts': []
        }
        
        # Stage 1: Enhanced OCR (Primary)
        ocr_result = self._try_ocr_detection(image_path, ign, preprocessing_result)
        results['fallback_attempts'].append(('ocr', ocr_result['confidence']))
        
        if ocr_result['confidence'] >= self.confidence_thresholds['ocr']:
            logger.info(f"✅ OCR detection successful: {ocr_result['confidence']:.3f}")
            results.update({
                'method_used': 'ocr',
                'confidence': ocr_result['confidence'],
                'data': ocr_result['data']
            })
            return results
        
        logger.info(f"🔄 OCR confidence low ({ocr_result['confidence']:.3f}), trying YOLO...")
        
        # Stage 2: YOLO Object Detection (Fallback 1)
        if self.yolo_service:
            yolo_result = self._try_yolo_detection(image_path, ign, preprocessing_result)
            results['fallback_attempts'].append(('yolo', yolo_result['confidence']))
            
            if yolo_result['confidence'] >= self.confidence_thresholds['yolo']:
                logger.info(f"✅ YOLO detection successful: {yolo_result['confidence']:.3f}")
                results.update({
                    'method_used': 'yolo',
                    'confidence': yolo_result['confidence'],
                    'data': yolo_result['data']
                })
                return results
                
            logger.info(f"🔄 YOLO confidence low ({yolo_result['confidence']:.3f}), trying template matching...")
        else:
            logger.info("🔄 YOLO unavailable, trying template matching...")
            results['fallback_attempts'].append(('yolo', 0.0))
        
        # Stage 3: Template Matching (Final Fallback)
        template_result = self._try_template_matching(image_path, ign, preprocessing_result)
        results['fallback_attempts'].append(('template', template_result['confidence']))
        
        if template_result['confidence'] >= self.confidence_thresholds['template']:
            logger.info(f"✅ Template matching successful: {template_result['confidence']:.3f}")
            results.update({
                'method_used': 'template',
                'confidence': template_result['confidence'],
                'data': template_result['data']
            })
            return results
        
        # All methods failed
        logger.warning("❌ All detection methods failed - returning best attempt")
        best_attempt = max(results['fallback_attempts'], key=lambda x: x[1]) if results['fallback_attempts'] else ('none', 0.0)
        results.update({
            'method_used': f'failed_{best_attempt[0]}',
            'confidence': best_attempt[1],
            'data': ocr_result['data'] if best_attempt[0] == 'ocr' else {}
        })
        
        return results
    
    def _try_ocr_detection(self, image_path: str, ign: str, preprocessing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt OCR-based detection with region-specific processing."""
        try:
            # Use enhanced preprocessing results
            if not preprocessing_result['success']:
                return {'confidence': 0.0, 'data': {}}
            
            confidence_scores = []
            combined_data = {}
            
            # Process each region with OCR
            for region_name, region_image in preprocessing_result['regions'].items():
                if region_image.size == 0:
                    continue
                    
                # Get region-specific OCR results
                region_data = self._process_region_with_ocr(region_image, region_name, ign)
                
                if region_data['confidence'] > 0:
                    confidence_scores.append(region_data['confidence'])
                    combined_data.update(region_data['data'])
            
            # Calculate overall confidence
            overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
            
            return {
                'confidence': overall_confidence,
                'data': combined_data
            }
            
        except Exception as e:
            logger.error(f"OCR detection error: {e}")
            return {'confidence': 0.0, 'data': {}}
    
    def _try_yolo_detection(self, image_path: str, ign: str, preprocessing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt YOLO-based object detection."""
        try:
            if not self.yolo_service:
                return {'confidence': 0.0, 'data': {}}
            
            # Use YOLO to detect UI elements and text regions
            detections = self.yolo_service.detect_objects(image_path)
            
            # Process detections to extract player data
            player_data = self._process_yolo_detections(detections, ign)
            
            # Calculate confidence based on detection quality
            confidence = self._calculate_yolo_confidence(detections, player_data)
            
            return {
                'confidence': confidence,
                'data': player_data
            }
            
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
            return {'confidence': 0.0, 'data': {}}
    
    def _try_template_matching(self, image_path: str, ign: str, preprocessing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt template matching for standard UI elements."""
        try:
            image = preprocessing_result.get('processed_image', np.array([]))
            if image.size == 0:
                return {'confidence': 0.0, 'data': {}}
            
            matches = {}
            confidence_scores = []
            
            # Try to match common MLBB UI templates
            for template_name in ['victory_banner', 'defeat_banner', 'mvp_icon', 'legendary_icon']:
                template_matches = self.template_db.match_template(image, template_name)
                
                if template_matches:
                    matches[template_name] = template_matches
                    # Use highest confidence match
                    best_confidence = max(match[2] for match in template_matches)
                    confidence_scores.append(best_confidence)
            
            # Extract basic game outcome data from template matches
            template_data = self._extract_data_from_templates(matches)
            
            overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
            
            return {
                'confidence': overall_confidence,
                'data': template_data
            }
            
        except Exception as e:
            logger.error(f"Template matching error: {e}")
            return {'confidence': 0.0, 'data': {}}
    
    def _process_region_with_ocr(self, region_image: np.ndarray, region_name: str, ign: str) -> Dict[str, Any]:
        """Process a specific region with OCR."""
        # This would integrate with existing OCR processing logic
        # For now, return placeholder structure
        return {
            'confidence': 0.5,
            'data': {}
        }
    
    def _process_yolo_detections(self, detections: List, ign: str) -> Dict[str, Any]:
        """Process YOLO detections to extract player data."""
        return {}
    
    def _calculate_yolo_confidence(self, detections: List, player_data: Dict) -> float:
        """Calculate confidence score for YOLO detection results."""
        return 0.0
    
    def _extract_data_from_templates(self, matches: Dict) -> Dict[str, Any]:
        """Extract game data from template matches."""
        data = {}
        
        # Basic game outcome detection
        if 'victory_banner' in matches:
            data['game_result'] = 'victory'
        elif 'defeat_banner' in matches:
            data['game_result'] = 'defeat'
            
        # Performance indicators
        if 'mvp_icon' in matches:
            data['mvp'] = True
        if 'legendary_icon' in matches:
            data['legendary'] = True
            
        return data


class RobustIGNMatcher:
    """Advanced IGN matching with multiple fallback strategies."""
    
    def __init__(self):
        self.min_similarity = 0.45  # Relaxed: Lower threshold for OCR variations
        
    def find_ign_in_ocr(self, target_ign: str, ocr_results: List) -> Dict[str, Any]:
        """Find IGN using multiple robust strategies."""
        strategies = [
            ("exact_match", self._exact_match),
            ("case_insensitive", self._case_insensitive_match),
            ("fuzzy_match", self._fuzzy_match),
            ("partial_match", self._partial_match),
            ("cleaned_match", self._cleaned_match),
            ("token_match", self._token_match)
        ]
        
        best_result = {"found": False, "confidence": 0.0, "strategy": None, "bbox": None, "text": None}
        
        for strategy_name, strategy_func in strategies:
            result = strategy_func(target_ign, ocr_results)
            if result["found"] and result["confidence"] > best_result["confidence"]:
                result["strategy"] = strategy_name
                best_result = result
                
                # If we get a high-confidence match, return immediately
                if result["confidence"] >= 0.95:
                    break
        
        logger.debug(f"IGN matching result: {best_result['strategy']} "
                    f"confidence={best_result['confidence']:.3f}")
        return best_result
    
    def _exact_match(self, target_ign: str, ocr_results: List) -> Dict[str, Any]:
        """Exact string matching."""
        for bbox, text, conf in ocr_results:
            if target_ign == text:
                return {"found": True, "confidence": 1.0, "bbox": bbox, "text": text}
        return {"found": False, "confidence": 0.0}
    
    def _case_insensitive_match(self, target_ign: str, ocr_results: List) -> Dict[str, Any]:
        """Case-insensitive matching."""
        target_lower = target_ign.lower()
        for bbox, text, conf in ocr_results:
            if target_lower == text.lower():
                return {"found": True, "confidence": 0.95, "bbox": bbox, "text": text}
        return {"found": False, "confidence": 0.0}
    
    def _fuzzy_match(self, target_ign: str, ocr_results: List) -> Dict[str, Any]:
        """Fuzzy string matching using sequence similarity."""
        best_match = {"found": False, "confidence": 0.0}
        target_lower = target_ign.lower()
        
        for bbox, text, conf in ocr_results:
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, target_lower, text.lower()).ratio()
            
            if similarity >= self.min_similarity and similarity > best_match["confidence"]:
                best_match = {
                    "found": True,
                    "confidence": similarity * 0.9,  # Slight penalty for fuzzy match
                    "bbox": bbox,
                    "text": text
                }
        
        return best_match
    
    def _partial_match(self, target_ign: str, ocr_results: List) -> Dict[str, Any]:
        """Partial matching - IGN contains or is contained in text."""
        best_match = {"found": False, "confidence": 0.0}
        
        for bbox, text, conf in ocr_results:
            # Use flexible IGN matching that handles guild tags
            if is_ign_match(target_ign, text):
                confidence = min(0.8, conf * 0.9)  # Slightly lower confidence for partial match
                
                if confidence > best_match["confidence"]:
                    best_match = {
                        "found": True,
                        "confidence": confidence,
                        "bbox": bbox,
                        "text": text
                    }
        
        return best_match
    
    def _cleaned_match(self, target_ign: str, ocr_results: List) -> Dict[str, Any]:
        """Matching after cleaning common OCR artifacts."""
        def clean_text(text):
            # Remove common OCR artifacts and normalize
            cleaned = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
            return cleaned.strip().lower()
        
        target_cleaned = clean_text(target_ign)
        best_match = {"found": False, "confidence": 0.0}
        
        for bbox, text, conf in ocr_results:
            text_cleaned = clean_text(text)
            
            if target_cleaned == text_cleaned:
                return {"found": True, "confidence": 0.85, "bbox": bbox, "text": text}
            
            # Fuzzy match on cleaned text
            similarity = SequenceMatcher(None, target_cleaned, text_cleaned).ratio()
            if similarity >= self.min_similarity and similarity > best_match["confidence"]:
                best_match = {
                    "found": True,
                    "confidence": similarity * 0.8,  # Penalty for cleaned match
                    "bbox": bbox,
                    "text": text
                }
        
        return best_match
    
    def _token_match(self, target_ign: str, ocr_results: List) -> Dict[str, Any]:
        """Token-based matching for multi-word IGNs."""
        target_tokens = set(target_ign.lower().split())
        if len(target_tokens) < 2:
            return {"found": False, "confidence": 0.0}
        
        best_match = {"found": False, "confidence": 0.0}
        
        for bbox, text, conf in ocr_results:
            text_tokens = set(text.lower().split())
            
            # Calculate token overlap
            common_tokens = target_tokens.intersection(text_tokens)
            if not common_tokens:
                continue
                
            # Calculate confidence based on token overlap
            overlap_ratio = len(common_tokens) / len(target_tokens)
            if overlap_ratio >= 0.3:  # Relaxed: At least 30% token overlap for OCR variations
                confidence = overlap_ratio * 0.7  # Penalty for token-based match
                
                if confidence > best_match["confidence"]:
                    best_match = {
                        "found": True,
                        "confidence": confidence,
                        "bbox": bbox,
                        "text": text
                    }
        
        return best_match


class AnchorBasedLayoutParser:
    """Layout-aware parser using UI anchors for robust data extraction."""
    
    def __init__(self):
        self.ui_anchors = {
            # Match result anchors
            'DEFEAT': {'patterns': ['defeat', 'loss', 'lose'], 'region': (0.2, 0.0, 0.8, 0.4)},
            'VICTORY': {'patterns': ['victory', 'win', 'won'], 'region': (0.2, 0.0, 0.8, 0.4)},
            
            # Column header anchors
            'DURATION': {'patterns': ['duration', 'time'], 'region': (0.0, 0.0, 1.0, 0.4)},
            'KDA_HEADER': {'patterns': ['k/d/a', 'kda', 'kills'], 'identifies_column': True},
            'GOLD_HEADER': {'patterns': ['gold'], 'identifies_column': True},
            'DAMAGE_HEADER': {'patterns': ['damage', 'dmg'], 'identifies_column': True},
            
            # UI elements that help identify layout
            'PLAYER_LIST': {'patterns': ['blue', 'red', 'team'], 'region': (0.0, 0.3, 1.0, 0.9)},
        }
        
        self.column_tolerance = 50  # Pixels tolerance for column alignment
        
    def detect_anchors(self, ocr_results: List, image_shape: Tuple[int, int]) -> Dict[str, Dict]:
        """Detect UI anchors in the OCR results."""
        anchors = {}
        height, width = image_shape[:2]
        
        for bbox, text, conf in ocr_results:
            text_lower = text.lower().strip()
            if not text_lower:
                continue
                
            # Calculate text position
            text_center_x = sum(point[0] for point in bbox) / 4
            text_center_y = sum(point[1] for point in bbox) / 4
            
            # Normalize coordinates
            norm_x = text_center_x / width
            norm_y = text_center_y / height
            
            # Check each anchor type
            for anchor_name, anchor_info in self.ui_anchors.items():
                for pattern in anchor_info['patterns']:
                    if pattern in text_lower:
                        # Check if position matches expected region (if specified)
                        if 'region' in anchor_info:
                            x1, y1, x2, y2 = anchor_info['region']
                            if not (x1 <= norm_x <= x2 and y1 <= norm_y <= y2):
                                continue
                        
                        anchors[anchor_name] = {
                            'bbox': bbox,
                            'text': text,
                            'confidence': conf,
                            'position': (text_center_x, text_center_y),
                            'normalized_position': (norm_x, norm_y)
                        }
                        logger.debug(f"Found anchor {anchor_name}: '{text}' at ({norm_x:.2f}, {norm_y:.2f})")
                        break
        
        return anchors
    
    def identify_columns(self, ocr_results: List, anchors: Dict) -> Dict[str, List]:
        """Identify table columns based on header anchors and spatial alignment."""
        columns = {}
        
        # Find column headers
        column_headers = {}
        for anchor_name, anchor_data in anchors.items():
            if self.ui_anchors.get(anchor_name, {}).get('identifies_column'):
                header_x = anchor_data['position'][0]
                column_headers[anchor_name] = {
                    'x_position': header_x,
                    'column_data': []
                }
        
        # Group OCR results by column alignment
        for bbox, text, conf in ocr_results:
            text_center_x = sum(point[0] for point in bbox) / 4
            
            # Find which column this text belongs to
            for column_name, column_info in column_headers.items():
                column_x = column_info['x_position']
                if abs(text_center_x - column_x) <= self.column_tolerance:
                    column_info['column_data'].append({
                        'text': text,
                        'bbox': bbox,
                        'confidence': conf,
                        'position': (text_center_x, sum(point[1] for point in bbox) / 4)
                    })
                    break
        
        # Sort column data by vertical position
        for column_name, column_info in column_headers.items():
            column_info['column_data'].sort(key=lambda x: x['position'][1])
            columns[column_name] = column_info['column_data']
        
        return columns
    
    def extract_player_row_data(self, ign: str, ocr_results: List, anchors: Dict, columns: Dict) -> Dict[str, Any]:
        """Extract player data using anchor-based layout understanding."""
        parsed_data = {}
        
        # First, find the player's row by IGN
        player_row_y = None
        ign_matcher = RobustIGNMatcher()
        ign_result = ign_matcher.find_ign_in_ocr(ign, ocr_results)
        
        if ign_result["found"]:
            ign_bbox = ign_result["bbox"]
            player_row_y = sum(point[1] for point in ign_bbox) / 4
            logger.info(f"Found player row at y={player_row_y:.1f}")
        else:
            logger.warning("Could not locate player IGN for row-based extraction")
            return self._fallback_extraction(ocr_results)
        
        # ENHANCED: Direct row extraction when columns are not identified
        if not columns:
            logger.info("No columns identified, using direct row extraction")
            parsed_data = self._extract_from_player_row_direct(ocr_results, player_row_y, ign)
        else:
            # Extract data from each column at the player's row level
            row_tolerance = 50  # Increased vertical tolerance for same row alignment
            
            for column_name, column_data in columns.items():
                for item in column_data:
                    item_y = item['position'][1]
                    if abs(item_y - player_row_y) <= row_tolerance:
                        # This item is in the player's row
                        text = item['text']
                        
                        if column_name == 'KDA_HEADER':
                            self._extract_kda_from_text(text, parsed_data)
                        elif column_name == 'GOLD_HEADER':
                            self._extract_gold_from_text(text, parsed_data)
                        elif column_name == 'DAMAGE_HEADER':
                            self._extract_damage_from_text(text, parsed_data)
                        
                        break
        
        # Extract match-level data from anchors
        if 'VICTORY' in anchors:
            parsed_data['match_result'] = 'victory'
        elif 'DEFEAT' in anchors:
            parsed_data['match_result'] = 'defeat'
        
        if 'DURATION' in anchors:
            duration_text = anchors['DURATION']['text']
            self._extract_duration_from_text(duration_text, parsed_data)
        
        return parsed_data
    
    def _determine_quality_hint(self, image_path: str, ocr_results: List) -> str:
        """Determine image quality hint for adaptive trophy detection."""
        
        try:
            # Load image to check basic quality metrics
            image = cv2.imread(image_path)
            if image is None:
                return "poor"
            
            height, width = image.shape[:2]
            
            # Basic quality indicators
            quality_score = 0
            
            # Resolution quality
            total_pixels = width * height
            if total_pixels > 2000000:  # High resolution (>2MP)
                quality_score += 2
            elif total_pixels > 1000000:  # Medium resolution (>1MP)
                quality_score += 1
            
            # OCR quality indicators
            if ocr_results:
                # Count high-confidence OCR results
                high_conf_results = sum(1 for result in ocr_results 
                                      if len(result) >= 3 and result[2] > 0.8)
                total_results = len(ocr_results)
                
                if total_results > 0:
                    ocr_quality_ratio = high_conf_results / total_results
                    if ocr_quality_ratio > 0.7:
                        quality_score += 2
                    elif ocr_quality_ratio > 0.5:
                        quality_score += 1
            
            # Map quality score to hint
            if quality_score >= 4:
                return "excellent"
            elif quality_score >= 3:
                return "good"
            elif quality_score >= 2:
                return "average"
            else:
                return "poor"
                
        except Exception as e:
            logger.warning(f"Quality hint determination failed: {e}")
            return "average"  # Default fallback
    
    def _fallback_trophy_detection(
        self, 
        image_path: str, 
        ign: str, 
        ocr_results: List,
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Fallback trophy detection when IGN is not found."""
        
        logger.info("🔄 Attempting fallback trophy detection without IGN positioning")
        
        try:
            # Load image to get dimensions
            image = cv2.imread(image_path)
            if image is None:
                warnings.append("Fallback trophy detection failed - could not load image")
                return {}
            
            height, width = image.shape[:2]
            
            # Strategy 1: Try common player row positions based on image resolution
            common_positions = [
                height * 0.3,   # Upper third
                height * 0.4,   # Common position 1
                height * 0.5,   # Middle
                height * 0.6,   # Common position 2
                height * 0.7,   # Lower third
            ]
            
            quality_hint = self._determine_quality_hint(image_path, ocr_results)
            best_trophy_result = None
            best_confidence = 0.0
            
            for y_pos in common_positions:
                try:
                    trophy_result = trophy_medal_detector.detect_trophy_in_player_row(
                        image_path=image_path,
                        player_row_y=y_pos,
                        player_name_x=None,  # Search full width
                        debug_mode=False,
                        quality_hint=quality_hint
                    )
                    
                    if trophy_result.confidence > best_confidence:
                        best_confidence = trophy_result.confidence
                        best_trophy_result = trophy_result
                        logger.info(f"🎯 Fallback trophy detection at Y={y_pos:.1f}: "
                                   f"{trophy_result.trophy_type.value} (conf: {trophy_result.confidence:.1%})")
                
                except Exception as e:
                    logger.warning(f"Fallback trophy detection failed at Y={y_pos}: {e}")
            
            # Strategy 2: If no trophy found, try text-based detection across full image
            if best_confidence < 0.3:
                logger.info("🔄 Trying full-image text-based trophy detection")
                
                try:
                    from .data_collector import get_ocr_reader
                    
                    # Look for MVP indicators in OCR results
                    mvp_confidence = 0.0
                    for result in ocr_results:
                        if len(result) >= 3:
                            text = result[1].lower().strip()
                            confidence = result[2]
                            
                            if any(indicator in text for indicator in ['mvp', 'most valuable', 'crown']):
                                mvp_confidence = max(mvp_confidence, confidence * 0.8)
                                logger.info(f"🏆 MVP indicator found in text: '{result[1]}' (conf: {confidence:.3f})")
                    
                    if mvp_confidence > 0.4:
                        # Create synthetic trophy result for MVP
                        trophy_data = {
                            "mvp_detected": True,
                            "medal_type": None,
                            "trophy_confidence": mvp_confidence,
                            "performance_label": "Excellent",
                            "trophy_detection_method": "fallback_text_mvp",
                            "contextual_performance_rating": "Excellent",
                            "rating_boost_reasons": ["MVP detected via fallback text analysis"]
                        }
                        
                        warnings.append(f"Trophy detected via fallback text analysis (confidence: {mvp_confidence:.1%})")
                        logger.info("🏆 MVP detected via fallback text analysis")
                        return trophy_data
                
                except Exception as e:
                    logger.warning(f"Fallback text detection failed: {e}")
            
            # Return best result if found
            if best_trophy_result and best_confidence > 0.3:
                trophy_data = {
                    "mvp_detected": best_trophy_result.trophy_type.value == "mvp_crown",
                    "medal_type": (best_trophy_result.trophy_type.value 
                                 if best_trophy_result.trophy_type.value != "mvp_crown" else None),
                    "trophy_confidence": best_trophy_result.confidence,
                    "performance_label": best_trophy_result.performance_label.value,
                    "trophy_detection_method": f"fallback_{best_trophy_result.detection_method.value}",
                    "contextual_performance_rating": best_trophy_result.performance_label.value
                }
                
                # Add performance boost logic
                if best_trophy_result.trophy_type.value == "mvp_crown":
                    trophy_data["rating_boost_reasons"] = ["MVP detected via fallback positioning"]
                    logger.info("🏆 MVP detected via fallback positioning")
                
                warnings.append(f"Trophy detected via fallback positioning (confidence: {best_confidence:.1%})")
                return trophy_data
            
            # No trophy detected
            logger.warning("Fallback trophy detection failed - no trophies found")
            warnings.append("Fallback trophy detection failed - no trophies found")
            return {}
            
        except Exception as e:
            logger.error(f"Fallback trophy detection error: {e}")
            warnings.append(f"Fallback trophy detection error: {str(e)}")
            return {}
    
    def _extract_from_player_row_direct(self, ocr_results: List, player_row_y: float, player_ign: Optional[str] = None) -> Dict[str, Any]:
        """Direct extraction from player row when column detection fails."""
        parsed_data = {}
        row_tolerance = 50  # Further increased tolerance for better row detection
        
        # Collect all text and bounding boxes in the player's row with spatial information
        row_items = []
        
        for bbox, text, conf in ocr_results:
            # Calculate center Y coordinate more accurately
            bbox_points = bbox if isinstance(bbox, list) else bbox.tolist()
            y_coords = [point[1] for point in bbox_points]
            text_y = sum(y_coords) / len(y_coords)
            
            if abs(text_y - player_row_y) <= row_tolerance:
                # Calculate center X coordinate for spatial ordering
                x_coords = [point[0] for point in bbox_points]
                text_x = sum(x_coords) / len(x_coords)
                
                row_items.append({
                    'text': text,
                    'x': text_x,
                    'y': text_y,
                    'confidence': conf,
                    'bbox': bbox
                })
        
        # Sort by X coordinate (left to right) for better field alignment
        row_items.sort(key=lambda item: item['x'])
        
        row_texts = [item['text'] for item in row_items]
        row_numbers = []
        
        # Extract numbers with their spatial positions
        import re
        for item in row_items:
            numbers = [(int(n), item['x']) for n in re.findall(r'\b(\d+)\b', item['text'])]
            row_numbers.extend(numbers)
        
        logger.debug(f"Direct row extraction - texts: {row_texts}")
        logger.debug(f"Direct row extraction - numbers: {[n[0] for n in row_numbers]}")
        
        # Extract KDA using pattern matching with improved spatial awareness
        combined_text = " ".join(row_texts)
        self._extract_kda_from_text_enhanced(combined_text, row_items, parsed_data, player_ign)
        
        # Extract gold using improved MLBB-specific logic
        gold_candidates = [(n, x) for n, x in row_numbers if 1000 <= n <= 50000]  # More specific gold range
        if gold_candidates:
            # Sort by spatial position (X coordinate) for proper column alignment
            gold_candidates.sort(key=lambda item: item[1])  # Sort by X position
            
            # For MLBB, gold is typically the first large number after KDA
            # Skip small numbers (KDA range) and find the first large number
            for gold_val, x_pos in gold_candidates:
                if gold_val >= 1000:  # Definitely gold, not KDA
                    parsed_data['gold'] = gold_val
                    logger.debug(f"Extracted gold via MLBB-specific logic: {gold_val}")
                    break
        
        # Extract damage values using spatial positioning
        damage_candidates = [(n, x) for n, x in row_numbers if 1000 <= n <= 500000]
        if damage_candidates:
            # Sort by spatial position for column alignment
            damage_candidates.sort(key=lambda item: item[1])  # Sort by X position
            
            # Filter out gold value to avoid confusion
            gold_value = parsed_data.get('gold', 0)
            damage_only = [(n, x) for n, x in damage_candidates if n != gold_value]
            
            if damage_only:
                # Use spatial ordering (left to right)
                damage_values = [item[0] for item in damage_only]
                
                if len(damage_values) >= 1:
                    parsed_data['hero_damage'] = damage_values[0]
                    logger.debug(f"Extracted hero damage via spatial method: {damage_values[0]}")
                if len(damage_values) >= 2:
                    parsed_data['damage_taken'] = damage_values[1]
                    logger.debug(f"Extracted damage taken via spatial method: {damage_values[1]}")
        
        return parsed_data
    
    def _extract_kda_from_text(self, text: str, data: Dict[str, Any]):
        """Extract KDA values from text."""
        # Look for KDA pattern: X/Y/Z or X Y Z
        kda_patterns = [
            r'(\d+)\s*/\s*(\d+)\s*/\s*(\d+)',  # X/Y/Z format
            r'(\d+)\s+(\d+)\s+(\d+)',          # X Y Z format  
            r'(\d+)-(\d+)-(\d+)',              # X-Y-Z format
        ]
        
        for pattern in kda_patterns:
            match = re.search(pattern, text)
            if match:
                k, d, a = map(int, match.groups())
                if 0 <= k <= 50 and 0 <= d <= 50 and 0 <= a <= 50:  # Sanity check
                    data['kills'] = k
                    data['deaths'] = max(1, d)  # Deaths can't be 0
                    data['assists'] = a
                    logger.debug(f"Extracted KDA: {k}/{d}/{a}")
                    return

    def _extract_kda_from_text_enhanced(self, text: str, row_items: List, data: Dict[str, Any], player_ign: Optional[str] = None):
        """Enhanced KDA extraction with IGN-aware pattern and spatial fallback.

        Prefers K/D/A triplet immediately following the player's IGN in the
        same row. Falls back to spatial and general detection if needed.
        """
        import re
        
        # First try the standard text-based extraction
        self._extract_kda_from_text(text, data)
        
        # If that failed, try MLBB-specific spatial extraction
        if not all(k in data for k in ['kills', 'deaths', 'assists']):
            logger.debug(f"Standard KDA extraction failed, trying MLBB-specific extraction")
            
            # MLBB-specific: Look for the pattern after IGN
            # Format: "IGN K D A GOLD ..." where K/D/A are small numbers
            combined_text = " ".join([item['text'] for item in row_items])
            logger.debug(f"Combined row text: {combined_text}")
            
            # Try to find KDA pattern after IGN
            # Look for pattern: IGN followed by 3 small numbers (K/D/A)
            match = None
            if player_ign:
                escaped_ign = re.escape(player_ign)
                ign_kda_pattern = rf"{escaped_ign}.*?(\d{{1,2}})\s+(\d{{1,2}})\s+(\d{{1,2}})"
                match = re.search(ign_kda_pattern, combined_text, re.IGNORECASE)
            
            if match:
                kills, deaths, assists = map(int, match.groups())
                if all(0 <= val <= 50 for val in [kills, deaths, assists]):  # Sanity check
                    data['kills'] = kills
                    data['deaths'] = max(1, deaths)
                    data['assists'] = assists
                    logger.debug(f"Extracted KDA via MLBB pattern: {kills}/{deaths}/{assists}")
                    return
            
            # Fallback: Look for clusters of small numbers after finding IGN position
            ign_found = False
            ign_x_position = 0
            
            # If IGN known, estimate its X position within this row
            if player_ign:
                for item in row_items:
                    if is_ign_match(player_ign, item['text']):
                        ign_found = True
                        ign_x_position = item['x']
                        break
            
            if ign_found:
                # Look for small numbers to the right of IGN
                kda_candidates = []
                
                for item in row_items:
                    if item['x'] > ign_x_position:  # To the right of IGN
                        numbers = [int(n) for n in re.findall(r'\b(\d+)\b', item['text'])]
                        for num in numbers:
                            if 0 <= num <= 50:  # KDA range
                                kda_candidates.append((num, item['x']))
                
                # Sort by X position and take first 3 as K/D/A
                if len(kda_candidates) >= 3:
                    kda_candidates.sort(key=lambda x: x[1])  # Sort by X position
                    kills, deaths, assists = [k[0] for k in kda_candidates[:3]]
                    
                    data['kills'] = kills
                    data['deaths'] = max(1, deaths)
                    data['assists'] = assists
                    logger.debug(f"Extracted KDA via spatial method: {kills}/{deaths}/{assists}")
                    return
            
            # Final fallback: Look for any sequence of 3 small numbers
            all_small_numbers = []
            for item in row_items:
                numbers = [int(n) for n in re.findall(r'\b(\d+)\b', item['text'])]
                for num in numbers:
                    if 0 <= num <= 50:
                        all_small_numbers.append((num, item['x']))
            
            if len(all_small_numbers) >= 3:
                all_small_numbers.sort(key=lambda x: x[1])
                kills, deaths, assists = [k[0] for k in all_small_numbers[:3]]
                
                data['kills'] = kills  
                data['deaths'] = max(1, deaths)
                data['assists'] = assists
                logger.debug(f"Extracted KDA via fallback method: {kills}/{deaths}/{assists}")
    
    def _extract_gold_from_text(self, text: str, data: Dict[str, Any]):
        """Extract gold value from text."""
        # Look for 3-6 digit numbers (typical gold range) - Fixed threshold
        gold_match = re.search(r'\b(\d{3,6})\b', text)
        if gold_match:
            gold_value = int(gold_match.group(1))
            if 100 <= gold_value <= 50000:  # Reasonable gold range - Fixed threshold
                data['gold'] = gold_value
                logger.debug(f"Extracted gold: {gold_value}")
    
    def _extract_damage_from_text(self, text: str, data: Dict[str, Any]):
        """Extract damage values from text."""
        # Look for large numbers (damage values)
        damage_matches = re.findall(r'\b(\d{4,7})\b', text)
        if damage_matches:
            damage_values = [int(d) for d in damage_matches]
            damage_values.sort(reverse=True)
            
            # Assign largest as hero damage
            if damage_values and 1000 <= damage_values[0] <= 500000:
                data['hero_damage'] = damage_values[0]
                logger.debug(f"Extracted hero damage: {damage_values[0]}")
    
    def _extract_duration_from_text(self, text: str, data: Dict[str, Any]):
        """Extract match duration from text."""
        duration_match = re.search(r'(\d{1,2})[:\.](\d{2})', text)
        if duration_match:
            minutes = int(duration_match.group(1))
            seconds = int(duration_match.group(2))
            data['match_duration'] = minutes + seconds / 60
            logger.debug(f"Extracted duration: {minutes}:{seconds:02d}")
    
    def _fallback_extraction(self, ocr_results: List) -> Dict[str, Any]:
        """Fallback extraction when anchor-based parsing fails."""
        logger.info("Using fallback extraction - anchor-based parsing failed")
        
        # Simple number extraction as fallback
        all_text = " ".join([result[1] for result in ocr_results])
        data = {}
        
        # Look for any KDA pattern in the text
        kda_match = re.search(r'(\d{1,2})\s*/?\s*(\d{1,2})\s*/?\s*(\d{1,2})', all_text)
        if kda_match:
            k, d, a = map(int, kda_match.groups())
            data.update({'kills': k, 'deaths': max(1, d), 'assists': a})
        
        # Look for gold values
        gold_values = [int(m) for m in re.findall(r'\b(\d{4,6})\b', all_text)]
        if gold_values:
            data['gold'] = max(gold_values)
        
        return data


class EnhancedDataCollector(DataCollector):
    """
    Enhanced data collector with parallel processing, improved parsing,
    and video timestamp correlation support.
    """
    
    def __init__(self, enable_parallel_processing: bool = True):
        """
        Initialize the enhanced data collector.
        
        Args:
            enable_parallel_processing: Whether to use parallel processing
        """
        self.enable_parallel_processing = enable_parallel_processing
        self.parallel_manager = (
            ParallelProcessingManager()
            if enable_parallel_processing else None
        )
        
        # Initialize hybrid detection engine
        self.hybrid_engine = HybridDetectionEngine(self)
        
        # Initialize session manager
        self.session_manager = SessionManager()
        
        # Initialize hero database for role classification
        try:
            self.hero_db = HeroDatabase()
        except Exception:
            self.hero_db = None
        
        # Initialize enhanced OCR processor if available
        try:
            self.ocr_processor = EnhancedOCRProcessor() if _ENHANCED_OCR_AVAILABLE else None
        except Exception:
            self.ocr_processor = None
        
        # Initialize trophy/medal detector
        self.trophy_detector = trophy_medal_detector
        
        # Initialize screenshot analyzer
        self.screenshot_analyzer = ScreenshotAnalyzer()
        
        # Initialize IGN matcher with improved algorithms
        self.ign_matcher = RobustIGNMatcher()
        
        # Initialize IGN validator
        self.ign_validator = IGNValidator()
        
        # Initialize anchor-based layout parser
        self.anchor_parser = AnchorBasedLayoutParser()
        
        # Performance tracking
        self.performance_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_processing_time": 0.0,
            "parallel_speedup": 1.0
        }
        
        # OCR reader (lazy loading)
        self._ocr_reader = None
    
    def analyze_screenshot_with_timestamp(
        self,
        image_path: str,
        ign: str,
        video_timestamp: float = None,
        frame_number: int = None,
        frame_metadata: Dict[str, Any] = None,
        session_id: str = None,
        hero_override: str = None,
        known_igns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshot with video timestamp correlation.
        
        Args:
            image_path: Path to the screenshot image
            ign: Player's in-game name
            video_timestamp: Time in seconds from video start
            frame_number: Frame number in the video
            frame_metadata: Additional frame metadata
            session_id: Optional session ID for multi-screenshot analysis
            hero_override: Manually specified hero name
            known_igns: List of known IGNs for validation
            
        Returns:
            Dictionary containing analysis results with timestamp information
        """
        import time
        start_time = time.time()
        
        # Perform standard screenshot analysis
        result = self.analyze_screenshot_with_session(
            image_path=image_path,
            ign=ign,
            session_id=session_id,
            hero_override=hero_override,
            known_igns=known_igns
        )
        
        # Add timestamp information to the result
        temporal_info = {
            "video_timestamp": video_timestamp,
            "frame_number": frame_number,
            "frame_metadata": frame_metadata or {},
            "analysis_timestamp": time.time(),
            "processing_time": time.time() - start_time
        }
        
        # Add temporal information to the result
        result["temporal_info"] = temporal_info
        
        # If we have data, add timestamp to the data section
        if result.get("data"):
            result["data"]["video_timestamp"] = video_timestamp
            result["data"]["frame_number"] = frame_number
            
            # Add game phase information based on timestamp
            if video_timestamp is not None:
                result["data"]["game_phase"] = self._determine_game_phase(
                    video_timestamp
                )
        
        return result
    
    def _determine_game_phase(self, timestamp: float) -> str:
        """
        Determine game phase based on video timestamp.
        
        Args:
            timestamp: Time in seconds from video start
            
        Returns:
            Game phase string (early, mid, late)
        """
        if timestamp < 300:  # 0-5 minutes
            return "early_game"
        elif timestamp < 900:  # 5-15 minutes
            return "mid_game"
        else:  # 15+ minutes
            return "late_game"
    
    def analyze_timestamped_frames_batch(
        self,
        timestamped_frames: List,  # List of TimestampedFrame objects
        ign: str,
        session_id: str = None,
        hero_override: str = None,
        known_igns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple timestamped frames in batch.
        
        Args:
            timestamped_frames: List of TimestampedFrame objects
            ign: Player's in-game name
            session_id: Optional session ID for multi-screenshot analysis
            hero_override: Manually specified hero name
            known_igns: List of known IGNs for validation
            
        Returns:
            List of analysis results with timestamp correlation
        """
        results = []
        
        for timestamped_frame in timestamped_frames:
            try:
                result = self.analyze_screenshot_with_timestamp(
                    image_path=timestamped_frame.frame_path,
                    ign=ign,
                    video_timestamp=timestamped_frame.timestamp,
                    frame_number=timestamped_frame.frame_number,
                    frame_metadata=timestamped_frame.metadata,
                    session_id=session_id,
                    hero_override=hero_override,
                    known_igns=known_igns
                )
                results.append(result)
                
            except Exception as e:
                logger.error(
                    f"Error analyzing timestamped frame at "
                    f"{timestamped_frame.timestamp:.2f}s: {str(e)}"
                )
                results.append({
                    "success": False,
                    "error": str(e),
                    "temporal_info": {
                        "video_timestamp": timestamped_frame.timestamp,
                        "frame_number": timestamped_frame.frame_number,
                        "frame_metadata": timestamped_frame.metadata
                    }
                })
        
        return results
    
    def create_temporal_event_log(
        self,
        analysis_results: List[Dict[str, Any]],
        event_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a temporal event log from analysis results.
        
        Args:
            analysis_results: List of analysis results with temporal info
            event_types: Types of events to include in the log
            
        Returns:
            List of timestamped events
        """
        if event_types is None:
            event_types = ["score_screen", "statistics", "match_result"]
        
        events = []
        
        for result in analysis_results:
            if (not result.get("success", False) or
                    not result.get("temporal_info")):
                continue
            
            temporal_info = result["temporal_info"]
            data = result.get("data", {})
            
            # Create event based on detected content
            event_type = self._classify_event_type(result)
            
            if event_type in event_types:
                event = {
                    "event_type": event_type,
                    "video_timestamp": temporal_info.get("video_timestamp"),
                    "frame_number": temporal_info.get("frame_number"),
                    "game_phase": data.get("game_phase"),
                    "confidence": result.get("confidence", 0.0),
                    "data": data,
                    "metadata": temporal_info.get("frame_metadata", {})
                }
                events.append(event)
        
        # Sort events by timestamp
        events.sort(key=lambda x: x["video_timestamp"] or 0)
        
        return events
    
    def _classify_event_type(self, analysis_result: Dict[str, Any]) -> str:
        """
        Classify the type of event based on analysis result.
        
        Args:
            analysis_result: Analysis result dictionary
            
        Returns:
            Event type string
        """
        data = analysis_result.get("data", {})
        
        # Check for different types of screens/events
        if data.get("mvp_badge") or data.get("legend_badge"):
            return "match_result"
        elif (data.get("kills") is not None and
              data.get("deaths") is not None):
            return "score_screen"
        elif data.get("hero_damage") or data.get("gold"):
            return "statistics"
        else:
            return "unknown"
    
    def analyze_screenshot_with_session(
        self,
        image_path: str,
        ign: str,
        session_id: Optional[str] = None,
        hero_override: Optional[str] = None,
        known_igns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshot with session management for multi-screenshot processing.
        
        Args:
            image_path: Path to screenshot
            ign: Player's in-game name
            session_id: Existing session ID (optional)
            hero_override: Manual hero specification (optional)
            known_igns: List of known IGNs (optional)
            
        Returns:
            Dictionary with analysis results and session info
        """
        try:
            # Create or get session
            if session_id:
                session = self.session_manager.get_session(session_id)
                if not session:
                    logger.warning(
                        f"Session {session_id} not found; creating session with provided id"
                    )
                    session_id = self.session_manager.create_session_with_id(session_id, ign)
                else:
                    logger.info(f"Reusing existing session {session_id} with {len(session.screenshots)} screenshots")
            else:
                session_id = self.session_manager.create_session(ign)
                logger.info(f"Created new session {session_id}")
            
            # Analyze screenshot type
            screenshot_type, type_confidence, detected_keywords = (
                self.screenshot_analyzer.analyze_screenshot_type(image_path)
            )
            
            logger.info(
                f"Screenshot analysis: type={screenshot_type.value}, "
                f"confidence={type_confidence:.3f}, "
                f"keywords={detected_keywords[:3]}"
            )
            
            # Perform enhanced OCR analysis
            analysis_result = self._enhanced_screenshot_analysis(
                image_path, ign, screenshot_type, hero_override, known_igns
            )
            
            # Create screenshot analysis object (using proper dataclass)
            from .session_manager import ScreenshotAnalysis
            screenshot_analysis = ScreenshotAnalysis(
                screenshot_type=screenshot_type,
                raw_data=analysis_result.get("data", {}),
                confidence=analysis_result.get(
                    "overall_confidence", type_confidence
                ),
                warnings=analysis_result.get("warnings", [])
            )
            
            # Add to session
            self.session_manager.add_screenshot_analysis(
                session_id, screenshot_analysis
            )
            
            # Check if we have a complete result
            session = self.session_manager.get_session(session_id)
            if session and session.is_complete:
                final_result = session.final_result
                logger.info(
                    f"Session {session_id} complete with final result"
                )
            else:
                final_result = analysis_result.get("data", {})
            
            return {
                "data": final_result,
                "session_id": session_id,
                "screenshot_type": screenshot_type.value,
                "type_confidence": type_confidence,
                "session_complete": session.is_complete if session else False,
                "overall_confidence": analysis_result.get("overall_confidence", 0.0),
                "completeness_score": analysis_result.get("completeness_score", 0.0),
                "warnings": analysis_result.get("warnings", []),
                "debug_info": {
                    "detected_keywords": detected_keywords,
                    "screenshot_count": (
                        len(session.screenshots) if session else 1
                    ),
                    "hero_suggestions": analysis_result.get(
                        "hero_suggestions", []
                    ),
                    "hero_debug": analysis_result.get("hero_debug", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced screenshot analysis failed: {str(e)}")
            return {
                "data": {},
                "session_id": session_id if 'session_id' in locals() else None,
                "error": str(e),
                "warnings": [f"Analysis failed: {str(e)}"]
            }
    
    def _enhanced_screenshot_analysis(
        self,
        image_path: str,
        ign: str,
        screenshot_type: str,
        hero_override: Optional[str] = None,
        known_igns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """OPTIMIZED enhanced analysis with parallel processing."""
        start_time = time.time()
        
        logger.info(
            f"Starting PARALLEL enhanced analysis for {screenshot_type.value} screenshot"
        )
        
        try:
            if self.enable_parallel_processing:
                # PARALLEL EXECUTION: Run independent tasks concurrently
                return self._run_parallel_analysis(
                    image_path, ign, screenshot_type, hero_override, known_igns
                )
            else:
                # FALLBACK: Sequential execution
                return self._run_sequential_analysis(
                    image_path, ign, screenshot_type, hero_override, known_igns
                )
                
        except Exception as e:
            logger.error(f"Enhanced analysis failed: {str(e)}")
            return {
                "data": {},
                "warnings": [f"Analysis failed: {str(e)}"],
                "overall_confidence": 0.0,
                "completeness_score": 0.0,
                "processing_time": time.time() - start_time
            }
    
    def _run_parallel_analysis(
        self,
        image_path: str,
        ign: str,
        screenshot_type: str,
        hero_override: Optional[str] = None,
        known_igns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run analysis with parallel processing for performance."""
        
        start_time = time.time()
        warnings = []
        # Ensure we have a default value before any parallel tasks use it
        validated_ign = ign
        
        # PHASE 1: Sequential preprocessing (eliminates OCR resource contention)
        logger.info("🔄 Phase 1: Sequential preprocessing...")
        
        try:
            # Step 1: Image preprocessing (fast, independent)
            preprocessed_image = self._preprocess_image_enhanced(image_path)
            
            # Step 2: OCR analysis (sequential to avoid resource competition)
            ocr_results = self._parallel_ocr_analysis(image_path)
            
            # Step 3: IGN validation (can be parallel with analysis tasks)
            ign_validation_future = self.parallel_manager.submit_task(
                self._parallel_ign_validation, ign, known_igns
            )
            
        except concurrent.futures.TimeoutError:
            logger.warning("Parallel preprocessing timed out, falling back to sequential")
            return self._run_sequential_analysis(
                image_path, ign, screenshot_type, hero_override, known_igns
            )
        except Exception as e:
            logger.error(f"Parallel preprocessing failed: {str(e)}")
            warnings.append(f"Parallel preprocessing error: {str(e)}")
            # Try to continue with sequential processing
            ocr_results = self._parallel_ocr_analysis(image_path)
            validated_ign = ign
        
        # Normalize screenshot_type to a simple string for branching
        stype = getattr(screenshot_type, 'value', screenshot_type)

        # PHASE 2: Launch parallel analysis tasks (OCR complete, no contention)
        logger.info("🚀 Phase 2: Launching parallel analysis tasks...")
        
        # Task 4: Player row parsing (depends on OCR)
        if str(stype).lower() == "scoreboard":
            parsing_future = self.parallel_manager.submit_task(
                self._parse_scoreboard_enhanced, validated_ign, ocr_results, [], image_path
            )
        else:
            parsing_future = self.parallel_manager.submit_task(
                self._parse_stats_page_enhanced, validated_ign, ocr_results, []
            )
        
        # Task 5: Trophy detection (depends on OCR, can run in parallel with parsing)
        trophy_future = self.parallel_manager.submit_task(
            self._parallel_trophy_detection, image_path, validated_ign, ocr_results
        )
        
        # Task 6: Hero detection (independent, if no override)
        if not hero_override:
            hero_future = self.parallel_manager.submit_task(
                self._parallel_hero_detection, image_path, validated_ign
            )
        else:
            hero_future = None
        
        # Get IGN validation result (update for subsequent logic only)
        try:
            validated_ign = ign_validation_future.result(timeout=2)
        except Exception as e:
            warnings.append(f"IGN validation fallback to provided IGN: {str(e)}")
            validated_ign = ign
        
        # PHASE 3: Collect all results
        logger.info("📊 Phase 3: Collecting results...")
        
        try:
            # Get parsing results - increased timeout for complex MLBB analysis
            parsed_data = parsing_future.result(timeout=60)
        
            # Get trophy detection results - increased timeout for medal detection
            trophy_data = trophy_future.result(timeout=45)
        
            # Get hero detection results - increased timeout for comprehensive hero analysis
            if hero_future:
                hero_data = hero_future.result(timeout=40)
            else:
                hero_data = {"hero": hero_override or "unknown", "hero_confidence": 0.0}
            
            # Fallback: if the chosen parser produced almost no actionable fields,
            # try the alternate parser once to salvage partial metrics.
            def _is_sparse(d: Dict[str, Any]) -> bool:
                if not d:
                    return True
                keys = set(d.keys())
                has_kda = any(k in keys for k in ("kills", "deaths", "assists"))
                has_damage = any(k in keys for k in ("hero_damage", "damage_taken", "turret_damage"))
                has_hero = bool(d.get("hero"))
                return not (has_kda or has_damage or has_hero)

            if _is_sparse(parsed_data):
                try:
                    if str(stype).lower().startswith("stats"):
                        logger.info("Parsed data sparse for stats_page; trying scoreboard parser fallback")
                        alt = self._parse_scoreboard_enhanced(validated_ign, ocr_results, warnings, image_path)
                    else:
                        logger.info("Parsed data sparse for scoreboard; trying stats_page parser fallback")
                        alt = self._parse_stats_page_enhanced(validated_ign, ocr_results, warnings)
                    if alt:
                        # Merge alt fields without clobbering existing non-empty values
                        for k, v in alt.items():
                            if k not in parsed_data or parsed_data[k] in (None, "", 0, "unknown"):
                                parsed_data[k] = v
                except Exception as e:
                    logger.warning(f"Alternate parser fallback failed: {e}")

        except concurrent.futures.TimeoutError:
            logger.warning("Parallel analysis tasks timed out")
            warnings.append("Some parallel tasks timed out")
            # Provide fallback results
            parsed_data = {}
            trophy_data = {}
            hero_data = {"hero": hero_override or "unknown", "hero_confidence": 0.0}
        except Exception as e:
            logger.error(f"Parallel analysis failed: {str(e)}")
            warnings.append(f"Parallel analysis error: {str(e)}")
            parsed_data = {}
            trophy_data = {}
            hero_data = {"hero": hero_override or "unknown", "hero_confidence": 0.0}
        
        # PHASE 5: Combine results
        logger.info("🔗 Phase 5: Combining results...")
        
        # Merge all data
        final_data = {}
        final_data.update(parsed_data)
        final_data.update(trophy_data)
        final_data.update(hero_data)

        # Attach battle_id if present in OCR
        try:
            battle_id = self._extract_battle_id(ocr_results)
            if battle_id:
                final_data["battle_id"] = battle_id
        except Exception:
            pass
        
        # Role classification based on extracted hero
        try:
            hero_name = str(final_data.get("hero", "unknown")).lower()
            if hero_name and hero_name != "unknown" and self.hero_db:
                # Prefer database lookup; fallback to heuristic if not found
                hero_obj = self.hero_db.heroes.get(hero_name.capitalize()) or self.hero_db.heroes.get(hero_name)
                if hero_obj and getattr(hero_obj, "role", None):
                    final_data["role"] = hero_obj.role
                else:
                    # Fallback heuristic
                    final_data["role"] = self.hero_db._infer_role(hero_name)
        except Exception:
            # Best-effort; do not fail pipeline on role classification
            pass
        
        # Add default values
        self._add_default_values(final_data)
        
        # Calculate final metrics
        data_field_count = len([v for v in final_data.values() if v])
        hero_confidence = hero_data.get("hero_confidence", 0.0)
        completeness_score = self._validate_data_completeness(final_data, warnings)
        overall_confidence = self._calculate_overall_confidence(
            hero_confidence, len(warnings), data_field_count, completeness_score
        )
        
        processing_time = time.time() - start_time
        
        # Log performance improvement
        parallel_stats = self.parallel_manager.get_stats()
        logger.info(f"✅ Parallel analysis complete in {processing_time:.3f}s")
        logger.info(f"📈 Parallel stats: {parallel_stats}")
        
        return {
            "data": final_data,
            "warnings": warnings,
            "overall_confidence": overall_confidence,
            "completeness_score": completeness_score,
            "processing_time": processing_time,
            "parallel_stats": parallel_stats,
            "optimization_applied": ["parallel_processing"]
        }

    def _parallel_ocr_analysis(self, image_path: str) -> List:
        """OCR analysis with MLBB-specific preprocessing and YOLO-assisted fallback."""
        try:
            # 1) Baseline OCR with our enhanced preprocessing
            prep_result = self._preprocess_image_enhanced(image_path)
            # Select an actual image array from preprocessing result
            preprocessed = None
            if isinstance(prep_result, dict):
                # Fix: Avoid numpy array boolean evaluation by checking explicitly
                full_image = prep_result.get("full_image")
                processed_image = prep_result.get("processed_image")
                if full_image is not None:
                    preprocessed = full_image
                elif processed_image is not None:
                    preprocessed = processed_image
            else:
                preprocessed = prep_result
            # HARDEN: Ensure EasyOCR-friendly numpy image
            try:
                import numpy as np
                import cv2
                if preprocessed is None or not hasattr(preprocessed, 'dtype'):
                    raw = cv2.imread(image_path)
                    if raw is not None:
                        preprocessed = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
                if preprocessed is not None:
                    if preprocessed.dtype != np.uint8:
                        preprocessed = preprocessed.astype(np.uint8)
                    if preprocessed.ndim == 3 and preprocessed.shape[2] == 4:
                        preprocessed = cv2.cvtColor(preprocessed, cv2.COLOR_BGRA2BGR)
                    elif preprocessed.ndim not in (2, 3):
                        # Reduce to safe grayscale
                        preprocessed = cv2.cvtColor(preprocessed, cv2.COLOR_BGR2GRAY)
            except Exception:
                pass
            reader = get_ocr_reader()
            results: List = reader.readtext(preprocessed, detail=1)
            logger.debug(f"🔍 OCR baseline count: {len(results)}")

            # Helper: compute simple OCR quality
            def _ocr_quality(rs: List) -> float:
                if not rs:
                    return 0.0
                confs = [float(r[2]) for r in rs if len(r) >= 3]
                return float(sum(confs) / max(1, len(confs)))

            avg_conf = _ocr_quality(results)

            # 2) If weak baseline OCR, try Enhanced OCR Processor (game-specific)
            enhanced_list: List = []
            if (len(results) < 8 or avg_conf < 0.6) and getattr(self, 'ocr_processor', None) is not None:
                try:
                    ocr_resp = self.ocr_processor.process_image(
                        image_path=image_path,
                        preprocessing_method=PreprocessingMethod.GAME_SPECIFIC,
                        ocr_engine=OCREngine.ENSEMBLE,
                    )
                    # Convert EnhancedOCRResponse to (bbox, text, conf)
                    if getattr(ocr_resp, 'success', False) and getattr(ocr_resp, 'results', None):
                        for r in ocr_resp.results:
                            # r.bbox is list of [x,y] points; convert to 4-point list if needed
                            bbox = r.bbox if isinstance(r.bbox, list) else []
                            enhanced_list.append((bbox, r.text, float(r.confidence)))
                        logger.info(f"🧠 Enhanced OCR added {len(enhanced_list)} items")
                except Exception as ee:
                    logger.warning(f"Enhanced OCR fallback failed: {ee}")

            # Merge baseline + enhanced
            combined = list(results) + enhanced_list

            # 3) If still poor, apply YOLO-assisted ROI OCR on top regions
            if len(combined) < 10 or _ocr_quality(combined) < 0.6:
                try:
                    yolo = get_yolo_detection_service()
                    roi_info = yolo.enhance_ocr_regions(image_path, ocr_confidence=0.0)
                    rois = roi_info.get('recommended_ocr_regions', [])[:5]
                    if rois:
                        img = cv2.imread(image_path)
                        os.makedirs('temp', exist_ok=True)
                        for i, (x1, y1, x2, y2) in enumerate(rois):
                            crop = img[int(y1):int(y2), int(x1):int(x2)]
                            if crop is None or (crop.size if hasattr(crop, 'size') else 0) == 0:
                                continue
                            tmp = f"temp/ocr_roi_{i}_{int(time.time()*1000)}.png"
                            cv2.imwrite(tmp, crop)
                            try:
                                if getattr(self, 'ocr_processor', None) is not None:
                                    roi_resp = self.ocr_processor.process_image(
                                        image_path=tmp,
                                        preprocessing_method=PreprocessingMethod.GAME_SPECIFIC,
                                        ocr_engine=OCREngine.ENSEMBLE,
                                    )
                                    if getattr(roi_resp, 'success', False):
                                        for r in roi_resp.results:
                                            bbox = r.bbox if isinstance(r.bbox, list) else []
                                            combined.append((bbox, r.text, float(r.confidence)))
                                else:
                                    # Fallback to EasyOCR on crop
                                    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                                    combined.extend(reader.readtext(crop_gray, detail=1))
                            finally:
                                try:
                                    if os.path.exists(tmp):
                                        os.remove(tmp)
                                except Exception:
                                    pass
                        logger.info(f"🧩 YOLO-assisted OCR merged; total={len(combined)}")
                except Exception as ye:
                    logger.warning(f"YOLO-assisted OCR failed: {ye}")

            # 4) Deduplicate by normalized text + coarse position bucket
            def _norm_text(t: str) -> str:
                t = t or ''
                t = re.sub(r'[^\w\s]', ' ', t)
                return ' '.join(t.split()).lower()

            seen = set()
            deduped: List = []
            for entry in combined:
                try:
                    bbox, text, conf = entry
                except ValueError:
                    # EasyOCR detail=1 ensures triple, but guard anyway
                    continue
                key_text = _norm_text(text)
                # Coarse position key: use bbox center rounded to 25px grid
                try:
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    cx = int(sum(xs) / max(1, len(xs)))
                    cy = int(sum(ys) / max(1, len(ys)))
                except Exception:
                    cx, cy = (0, 0)
                key = (key_text, cx // 25, cy // 25)
                if key not in seen and key_text:
                    seen.add(key)
                    deduped.append((bbox, text, conf))

            logger.debug(f"🔍 Final OCR count after merge/dedupe: {len(deduped)}")
            return deduped
        except Exception as e:
            logger.error(f"Parallel OCR failed: {str(e)}")
            return []

    # --- Battle ID extraction -------------------------------------------------
    def _extract_battle_id(self, ocr_results: List) -> Optional[str]:
        """Extract Battle ID from OCR results if present.

        Handles common OCR variants like 'BattlelD' (lD vs ID), spacing, etc.
        Returns numeric string when found, else None.
        """
        try:
            text = _text_from_ocr(ocr_results)
            if not text:
                return None
            # normalize common OCR confusions
            norm = text.replace("battleld", "battleid")
            norm = norm.replace("battelld", "battleid")
            norm = norm.replace("battle id", "battleid")
            # 1) explicit keyword followed by digits
            import re
            m = re.search(r"battleid\s*([0-9]{12,20})", norm)
            if m:
                return m.group(1)
            # 2) generic long-digit fallback near word 'battle'
            m2 = re.search(r"battle\w*\s*([0-9]{12,20})", norm)
            if m2:
                return m2.group(1)
            # 3) last-resort: pick a very long number at end of text
            m3 = re.findall(r"([0-9]{12,20})", norm)
            if m3:
                return m3[-1]
            return None
        except Exception:
            return None
    
    def _parallel_ign_validation(self, ign: str, known_igns: Optional[List[str]]) -> str:
        """Parallel IGN validation task."""
        try:
            # Quick validation
            if known_igns and ign not in known_igns:
                logger.warning(f"IGN '{ign}' not in known IGNs, but proceeding")
            return ign
        except Exception as e:
            logger.error(f"Parallel IGN validation failed: {str(e)}")
            return ign
    
    def _parallel_trophy_detection(self, image_path: str, ign: str, ocr_results: List) -> Dict[str, Any]:
        """Parallel trophy detection task."""
        try:
            return self._detect_trophy_and_performance(
                image_path, ign, ocr_results, {}, []
            )
        except Exception as e:
            logger.error(f"Parallel trophy detection failed: {str(e)}")
            return {}
    
    def _parallel_hero_detection(self, image_path: str, ign: str) -> Dict[str, Any]:
        """Parallel hero detection task."""
        try:
            from .advanced_hero_detector import AdvancedHeroDetector
            detector = AdvancedHeroDetector()
            hero, confidence, debug = detector.detect_hero_comprehensive(image_path, ign)
            return {
                "hero": hero,
                "hero_confidence": confidence,
                "hero_debug": debug
            }
        except Exception as e:
            logger.error(f"Parallel hero detection failed: {str(e)}")
            return {"hero": "unknown", "hero_confidence": 0.0}
    
    def _validate_ign_enhanced(self, ign: str, ocr_results: List, warnings: List[str]) -> str:
        """Enhanced IGN validation with robust multi-strategy matching."""
        # Use the robust IGN matcher
        ign_match_result = self.ign_matcher.find_ign_in_ocr(ign, ocr_results)
        
        if ign_match_result["found"]:
            confidence = ign_match_result["confidence"]
            matched_text = ign_match_result["text"]
            strategy = ign_match_result["strategy"]
            
            logger.info(f"IGN found using {strategy}: '{matched_text}' "
                       f"(confidence: {confidence:.3f})")
            
            # Validate the matched IGN using the MLBB validator
            validation_result = self.ign_validator.validate_mlbb_ign(matched_text)
            if validation_result['is_valid']:
                validated_ign = validation_result['cleaned_ign']
                
                # Add appropriate warnings based on confidence (relaxed thresholds)
                if confidence < 0.5:
                    warnings.append(f"Low IGN match confidence: {confidence:.1%}")
                elif confidence < 0.8:
                    warnings.append(f"IGN matched with {strategy} (confidence: {confidence:.1%})")
                
                logger.info(f"IGN validated and cleaned: '{validated_ign}'")
                return validated_ign
            else:
                # IGN found but doesn't validate as MLBB format
                warnings.append(f"Found '{matched_text}' but failed MLBB IGN validation")
                return matched_text
        
        # Fallback: Try original validation approach with fuzzy matching
        from difflib import SequenceMatcher
        best_fallback = {"ign": None, "similarity": 0.0}
        
        for bbox, text, conf in ocr_results:
            validation_result = self.ign_validator.validate_mlbb_ign(text)
            if validation_result['is_valid']:
                cleaned_ign = validation_result['cleaned_ign']
                # Use fuzzy matching instead of exact substring
                similarity = SequenceMatcher(None, ign.lower(), cleaned_ign.lower()).ratio()
                if similarity >= 0.4 and similarity > best_fallback["similarity"]:  # Relaxed threshold
                    best_fallback = {"ign": cleaned_ign, "similarity": similarity}
        
        if best_fallback["ign"]:
            warnings.append(f"IGN found via fallback fuzzy validation: {best_fallback['ign']} (similarity: {best_fallback['similarity']:.1%})")
            return best_fallback["ign"]
        
        # AUTO-INFER: Extract potential IGNs from OCR and choose best that can be located
        try:
            candidates = []
            if hasattr(self.ign_validator, 'extract_potential_igns'):
                candidates = list(dict.fromkeys(self.ign_validator.extract_potential_igns(ocr_results)))
            best_cand = None
            best_score = 0.0
            for cand in candidates:
                if not cand or len(cand.strip()) < 3:
                    continue
                tokens = [t for t in cand.split() if t]
                token_bonus = 1.0 if len(tokens) >= 2 else 0.0
                try:
                    style = float(self.ign_validator.validate_mlbb_ign(cand).get('mlbb_style_score', 0.0))
                except Exception:
                    style = 0.0
                matched = self.ign_matcher.find_ign_in_ocr(cand, ocr_results)
                conf = float(matched.get('confidence', 0.0)) if isinstance(matched, dict) else 0.0
                score = token_bonus + min(len(cand) / 20.0, 1.0) + style + conf
                if (matched.get('found') if isinstance(matched, dict) else False) and score > best_score:
                    best_score = score
                    best_cand = cand
            if best_cand:
                warnings.append(f"IGN auto-inferred from OCR: {best_cand}")
                return best_cand
        except Exception as e:
            warnings.append(f"IGN auto-infer failed: {str(e)}")
        
        # No IGN found with any method
        warnings.append(f"IGN '{ign}' not found in screenshot using any matching strategy")
        logger.warning(f"IGN '{ign}' not found in OCR results despite robust matching")
        return ign
    
    def _parse_scoreboard_enhanced(
        self, ign: str, ocr_results: List, warnings: List[str], image_path: str = None
    ) -> Dict[str, Any]:
        """Enhanced parsing specifically for scoreboard screenshots with anchor-based layout detection."""
        logger.info("Using enhanced scoreboard parsing with anchor-based layout detection")
        
        # Step 1: Try anchor-based parsing first (most robust)
        parsed_data = self._parse_with_anchors(ign, ocr_results, warnings)
        
        if not parsed_data or len(parsed_data) < 3:  # Need at least some basic data
            logger.info("Anchor-based parsing insufficient, trying enhanced row parsing")
            # Step 2: Fall back to enhanced player row parsing
            parsed_data = self._parse_player_row_enhanced(ign, ocr_results, warnings, image_path)
            
        if not parsed_data or len(parsed_data) < 2:
            logger.info("Enhanced row parsing insufficient, trying fallback strategy")
            warnings.append("Could not locate player using standard methods")
            # Step 3: Try alternative parsing methods
            parsed_data = self._parse_fallback_strategy(ocr_results, warnings)
            
        if not parsed_data:
            logger.warning("All parsing strategies failed")
            return {}
        
        # Extract match duration and result
        text_content = " ".join([result[1] for result in ocr_results])
        
        # Match duration
        import re
        duration_match = re.search(r"duration\s+(\d{1,2})[:\.](\d{2})", text_content.lower())
        if duration_match:
            minutes = int(duration_match.group(1))
            seconds = int(duration_match.group(2))
            parsed_data["match_duration"] = minutes + seconds / 60
        else:
            # Try alternative duration patterns
            alt_duration = re.search(r"(\d{1,2})[:\.](\d{2})", text_content)
            if alt_duration:
                minutes = int(alt_duration.group(1))
                seconds = int(alt_duration.group(2))
                parsed_data["match_duration"] = minutes + seconds / 60
            else:
                parsed_data["match_duration"] = 10  # Default
                warnings.append("Could not detect match duration")
        
        # Match result - Enhanced detection
        text_lower = text_content.lower()
        if any(word in text_lower for word in ["victory", "win", "won"]):
            parsed_data["match_result"] = "victory"
        elif any(word in text_lower for word in ["defeat", "loss", "lose", "lost"]):
            parsed_data["match_result"] = "defeat"
        else:
            # Try to infer from UI elements or positioning
            if "blue" in text_lower and "red" in text_lower:
                # Look for score patterns like "4 26" for team kills
                score_pattern = re.search(r"(\d+)\s+(\d+)", text_content)
                if score_pattern:
                    team1_score = int(score_pattern.group(1))
                    team2_score = int(score_pattern.group(2))
                    # Basic heuristic: if one team has significantly fewer kills, they likely lost
                    if team1_score < team2_score * 0.6:
                        parsed_data["match_result"] = "defeat"
                    elif team2_score < team1_score * 0.6:
                        parsed_data["match_result"] = "victory"
                    else:
                        warnings.append("Could not determine match result from scores")
                else:
                    warnings.append("Could not detect match result")
            else:
                warnings.append("Could not detect match result")
        
        # Player rank detection
        rank_keywords = [
            "warrior", "elite", "master", "grandmaster", "epic", 
            "legend", "mythic", "mythical", "bronze", "silver", "gold"
        ]
        detected_rank = None
        for keyword in rank_keywords:
            if keyword in text_lower:
                detected_rank = keyword.title()
                break
        
        if detected_rank:
            parsed_data["player_rank"] = detected_rank
            logger.info(f"Detected player rank: {detected_rank}")
        else:
            # Default rank assumption for rating context
            parsed_data["player_rank"] = "Unknown"
            warnings.append("Could not detect player rank")
        
        # Enhanced context detection
        parsed_data["screenshot_confidence"] = self._calculate_screenshot_confidence(text_content, warnings)
        
        return parsed_data
    
    def _parse_with_anchors(self, ign: str, ocr_results: List, warnings: List[str]) -> Dict[str, Any]:
        """Parse using anchor-based layout detection for maximum robustness."""
        logger.info("Attempting anchor-based parsing")
        
        # We need image shape for anchor detection, let's get it from OCR results
        # Estimate image dimensions from OCR bounding boxes
        max_x = max_y = 0
        for bbox, _, _ in ocr_results:
            for point in bbox:
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])
        
        estimated_image_shape = (int(max_y + 100), int(max_x + 100))  # Add padding
        
        try:
            # Step 1: Detect UI anchors
            anchors = self.anchor_parser.detect_anchors(ocr_results, estimated_image_shape)
            logger.debug(f"Found {len(anchors)} UI anchors: {list(anchors.keys())}")
            
            if not anchors:
                logger.warning("No UI anchors detected, skipping anchor-based parsing")
                return {}
            
            # Step 2: Identify table columns based on anchors
            columns = self.anchor_parser.identify_columns(ocr_results, anchors)
            logger.debug(f"Identified {len(columns)} table columns: {list(columns.keys())}")
            
            # Step 3: Extract player data using layout understanding
            parsed_data = self.anchor_parser.extract_player_row_data(ign, ocr_results, anchors, columns)
            
            if parsed_data:
                logger.info(f"Anchor-based parsing extracted {len(parsed_data)} fields")
                
                # Add parsing method info for debugging
                parsed_data['_parsing_method'] = 'anchor_based'
                parsed_data['_anchors_found'] = list(anchors.keys())
                parsed_data['_columns_found'] = list(columns.keys())
                
                return parsed_data
            else:
                warnings.append("Anchor-based parsing found layout but no player data")
                return {}
                
        except Exception as e:
            logger.error(f"Anchor-based parsing failed with error: {str(e)}")
            warnings.append(f"Anchor-based parsing error: {str(e)}")
            return {}
    
    def _parse_stats_page_enhanced(
        self, ign: str, ocr_results: List, warnings: List[str]
    ) -> Dict[str, Any]:
        """Enhanced parsing for detailed stats page screenshots."""
        logger.info("Using enhanced stats page parsing")
        
        parsed_data = {}
        text_content = " ".join([result[1] for result in ocr_results])
        
        # Extract damage values
        import re
        # Focus on 5-6 digit damage numbers to reduce noise from smaller counters
        damage_values = [int(match) for match in re.findall(r"\b(\d{5,6})\b", text_content)]
        damage_values.sort(reverse=True)
        
        if len(damage_values) >= 1:
            parsed_data["hero_damage"] = damage_values[0]
        if len(damage_values) >= 2:
            parsed_data["damage_taken"] = damage_values[1]
        if len(damage_values) >= 3:
            parsed_data["turret_damage"] = damage_values[2]
        
        # Extract percentage values
        percentages = [int(match) for match in re.findall(r"\b(\d{1,3})%", text_content)]
        if percentages:
            # Heuristic: the largest percentage is usually teamfight participation (~50-90)
            tf_pct = max(percentages)
            parsed_data["teamfight_participation"] = tf_pct
            rest = [p for p in percentages if p != tf_pct]
            # Map remaining top 3 to hero/turret/taken percentages by magnitude
            rest_sorted = sorted(rest, reverse=True)[:3]
            if rest_sorted:
                if len(rest_sorted) >= 1:
                    parsed_data["hero_damage_pct"] = rest_sorted[0]
                if len(rest_sorted) >= 2:
                    parsed_data["damage_taken_pct"] = rest_sorted[1]
                if len(rest_sorted) >= 3:
                    parsed_data["turret_damage_pct"] = rest_sorted[2]
        
        # Stats page typically does NOT contain KDA in a simple textual triplet form.
        # Avoid misclassifying unrelated number triplets (e.g., 30 victory 29) as KDA.
        # Only attempt KDA extraction if explicit KDA label is present.
        text_lower = text_content.lower()
        if "kda" in text_lower:
            kda_match = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})\b", text_content)
            if kda_match:
                parsed_data["kills"] = int(kda_match.group(1))
                parsed_data["deaths"] = max(1, int(kda_match.group(2)))
                parsed_data["assists"] = int(kda_match.group(3))
        
        return parsed_data
    
    def _add_default_values(self, parsed_data: Dict[str, Any]):
        """Add safe defaults without fabricating core metrics.

        Core metrics (kills, deaths, assists, gold, hero_damage, turret_damage,
        damage_taken, teamfight_participation) are left as-is when missing so
        the UI can display N/A and fusion can fill them later.
        """
        # Soft defaults for non-critical fields
        if parsed_data.get("positioning_rating") is None:
            parsed_data["positioning_rating"] = "average"
        if parsed_data.get("ult_usage") is None:
            parsed_data["ult_usage"] = "average"
        if parsed_data.get("match_duration") is None:
            # Keep a small sentinel only if totally absent; avoid overriding a valid parse
            parsed_data["match_duration"] = 10

        # Ensure deaths positive only if present
        if parsed_data.get("deaths") is not None and parsed_data.get("deaths") <= 0:
            parsed_data["deaths"] = 1

        # Calculate GPM if we have gold and duration
        gold = parsed_data.get("gold")
        duration = parsed_data.get("match_duration")
        try:
            if gold is not None and duration and float(duration) > 0:
                parsed_data["gold_per_min"] = int(round(float(gold) / float(duration)))
        except Exception:
            pass

        # Log snapshot without masking missing values
        data_summary = {k: parsed_data.get(k) for k in ["kills","deaths","assists","gold","hero_damage","teamfight_participation"]}
        logger.info(f"Final data after safe defaults: {data_summary}")
    
    def _preprocess_image_enhanced(self, image_path: str) -> Dict[str, Any]:
        """Enhanced MLBB-specific image preprocessing with ROI detection and quality assessment."""
        image = cv2.imread(image_path)
        
        if image is None:
            logger.error(f"❌ Failed to load image from {image_path}")
            return {"success": False, "quality_score": 0.0, "regions": {}, "processed_image": np.array([])}
        
        logger.info(f"🔍 Processing MLBB screenshot: {image.shape}")
        
        # Assess image quality first
        quality_score = self._assess_image_quality(image)
        logger.info(f"📊 Image quality score: {quality_score:.3f}")
        
        # Early termination for very low quality images
        if quality_score < 0.3:
            logger.warning(f"⚠️ Terminating: Quality too low ({quality_score:.3f})")
            return {"success": False, "quality_score": quality_score, "regions": {}, "processed_image": np.array([])}
        
        # MLBB-specific preprocessing pipeline
        processed_image = self._apply_mlbb_preprocessing(image, quality_score)
        
        # Extract regions of interest
        regions = self.parallel_manager.region_detector.extract_regions(processed_image) if self.parallel_manager else {}
        
        # Apply region-specific enhancements
        enhanced_regions = {}
        for region_name, region_img in regions.items():
            if region_img.size > 0:
                enhanced_regions[region_name] = self._enhance_region_for_ocr(region_img, region_name, quality_score)
        
        logger.info(f"✅ Processed {len(enhanced_regions)} regions with quality {quality_score:.3f}")
        
        return {
            "success": True,
            "quality_score": quality_score,
            "regions": enhanced_regions,
            "processed_image": processed_image,
            "full_image": processed_image  # For backward compatibility
        }
    
    def _apply_mlbb_preprocessing(self, image: np.ndarray, quality_score: float) -> np.ndarray:
        """Apply MLBB-specific preprocessing optimizations."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # MLBB screenshots often have dark backgrounds, enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)
        
        if quality_score > 0.7:
            # High quality: minimal processing to preserve text clarity
            logger.info("🔹 Applying minimal MLBB preprocessing")
            return contrast_enhanced
            
        elif quality_score > 0.5:
            # Medium quality: moderate enhancement
            logger.info("🔹 Applying moderate MLBB preprocessing")
            
            # Light denoising
            denoised = cv2.fastNlMeansDenoising(contrast_enhanced, h=8)
            
            # Sharpen text areas (common in MLBB UI)
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            return sharpened
            
        else:
            # Low quality: aggressive enhancement for MLBB screenshots
            logger.info("🔹 Applying aggressive MLBB preprocessing")
            
            # Strong denoising
            denoised = cv2.fastNlMeansDenoising(contrast_enhanced, h=12)
            
            # Adaptive thresholding optimized for MLBB UI
            adaptive_thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
            )
            
            # Morphological operations to clean MLBB text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
            cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
    
    def _enhance_region_for_ocr(self, region: np.ndarray, region_name: str, quality_score: float) -> np.ndarray:
        """Apply region-specific OCR enhancements."""
        if region.size == 0:
            return region
            
        # Get region-specific configuration
        region_config = self.parallel_manager.region_detector.get_region_config(region_name) if self.parallel_manager else {}
        
        if region_name == 'kda_section':
            # KDA numbers need high contrast
            kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
            enhanced = cv2.filter2D(region, -1, kernel)
            return cv2.GaussianBlur(enhanced, (1, 1), 0)
            
        elif region_name in ['team_blue', 'team_red']:
            # Player names and hero names
            if quality_score < 0.6:
                # Apply text-specific enhancement
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
                enhanced = cv2.morphologyEx(region, cv2.MORPH_CLOSE, kernel)
                return enhanced
                
        # Default enhancement
        return region
    
    def _assess_image_quality(self, image: np.ndarray) -> float:
        """
        Assess image quality based on various metrics.
        Returns a score between 0 (low quality) and 1 (high quality).
        """
        quality_factors = []
        
        # 1. Resolution factor
        height, width = image.shape[:2]
        resolution_score = float(min(1.0, (height * width) / (1920 * 1080)))  # Normalize to FHD
        quality_factors.append(resolution_score)
        
        # 2. Sharpness using Laplacian variance
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        gray = gray.astype(np.float64)  # Ensure float64 for calculations
        laplacian_var = float(cv2.Laplacian(gray, -1).var())
        sharpness_score = float(min(1.0, laplacian_var / 500.0))  # Normalize based on typical values
        quality_factors.append(sharpness_score)
        
        # 3. Contrast using standard deviation
        contrast_score = float(min(1.0, np.std(gray) / 80.0))  # Normalize based on typical values
        quality_factors.append(contrast_score)
        
        # 4. Brightness distribution
        mean_brightness = float(np.mean(gray))
        # Ideal brightness is around 120-140, penalize too dark or too bright
        if 100 <= mean_brightness <= 160:
            brightness_score = 1.0
        else:
            brightness_score = float(max(0, 1.0 - abs(mean_brightness - 130) / 130))
        quality_factors.append(brightness_score)
        
        # 5. Noise estimation using local variance
        kernel_size = 5
        local_mean = cv2.blur(gray, (kernel_size, kernel_size))
        # FIX: Ensure proper float operations to avoid numpy.bool_ issues
        gray_diff = gray.astype(np.float64) - local_mean.astype(np.float64)
        local_variance = cv2.blur(gray_diff ** 2, (kernel_size, kernel_size))
        noise_level = float(np.mean(np.sqrt(np.abs(local_variance))))  # abs() to handle any negative values
        noise_score = float(max(0, 1.0 - noise_level / 20.0))  # Lower noise = higher score
        quality_factors.append(noise_score)
        
        # Calculate weighted average - ensure all values are proper floats
        weights = [0.15, 0.25, 0.20, 0.20, 0.20]  # Resolution, Sharpness, Contrast, Brightness, Noise
        quality_score = float(sum(w * f for w, f in zip(weights, quality_factors)))
        
        # FORCE DEBUG: Print all quality metrics
        print(f"🔍 DEBUG: Quality metrics breakdown:")
        print(f"  Resolution: {resolution_score:.3f} (weight: 0.15)")
        print(f"  Sharpness:  {sharpness_score:.3f} (weight: 0.25)")
        print(f"  Contrast:   {contrast_score:.3f} (weight: 0.20)")
        print(f"  Brightness: {brightness_score:.3f} (weight: 0.20)")
        print(f"  Noise:      {noise_score:.3f} (weight: 0.20)")
        print(f"  FINAL:      {quality_score:.3f}")
        
        logger.debug(f"Quality metrics - Resolution: {resolution_score:.3f}, Sharpness: {sharpness_score:.3f}, "
                    f"Contrast: {contrast_score:.3f}, Brightness: {brightness_score:.3f}, Noise: {noise_score:.3f}")
        
        return quality_score
    
    def _detect_trophy_and_performance(
        self, 
        image_path: str, 
        ign: str, 
        ocr_results: List, 
        parsed_data: Dict[str, Any], 
        warnings: List[str]
    ) -> Dict[str, Any]:
        """
        PRIORITY 1: Detect MVP badge and medals for accurate performance rating.
        
        This implements the core requirement:
        - MVP Badge Detection → "Excellent" performance
        - Gold Medal → "Good" performance  
        - Silver Medal → "Average" performance
        - Bronze Medal → "Poor" performance
        """
        trophy_data = {}
        
        try:
            # ENHANCED: Find player row location from IGN with multiple strategies
            ign_matcher = RobustIGNMatcher()
            
            # Strategy 1: Try exact IGN matching
            ign_result = ign_matcher.find_ign_in_ocr(ign, ocr_results)
            
            # Strategy 2: If exact IGN fails, try common IGN variations
            if not ign_result["found"]:
                logger.info("🔄 Exact IGN not found, trying common variations")
                common_ign_variations = [
                    ign.replace(" ", ""),  # Remove spaces
                    ign.replace("XVII", "17"),  # Roman to numeric
                    ign.replace("XVIII", "18"),
                    ign.replace("XVI", "16"),
                    ign.replace("XV", "15"),
                    ign.split()[0] if " " in ign else ign,  # First part only
                    ign.lower(),  # Lowercase
                    ign.upper()   # Uppercase
                ]
                
                for variation in common_ign_variations:
                    if variation != ign:  # Skip if same as original
                        ign_result = ign_matcher.find_ign_in_ocr(variation, ocr_results)
                        if ign_result["found"]:
                            logger.info(f"✅ IGN found using variation: '{variation}' → '{ign_result.get('text','')}'")
                            break
            
            # Strategy 3: Conservative approach - skip heuristic matching, go directly to fallback
            # (Heuristic matching was causing incorrect player name detection)
            
            if not ign_result["found"]:
                logger.warning("IGN not found - trying fallback trophy detection strategies")
                warnings.append("IGN not found - using fallback positioning for trophy detection")
                
                # FALLBACK STRATEGY: Try trophy detection at common player row positions
                try:
                    image = cv2.imread(image_path)
                    if image is not None:
                        height, width = image.shape[:2]
                        
                        # ENHANCED: Try comprehensive player row positions with different strategies
                        # Inline quality hint calculation
                        total_pixels = width * height
                        if total_pixels > 2000000:
                            fallback_quality_hint = "good"
                        elif total_pixels > 1000000:
                            fallback_quality_hint = "average"
                        else:
                            fallback_quality_hint = "poor"
                        
                        # STRATEGY A: Comprehensive grid search optimized for MLBB screenshots
                        common_positions = []
                        
                        # Primary positions for typical MLBB screenshot layouts
                        primary_positions = [
                            height * 0.30,  # Upper player rows
                            height * 0.40,  # Common position 1
                            height * 0.50,  # Middle (most common)
                            height * 0.60,  # Common position 2
                            height * 0.70,  # Lower player rows
                        ]
                        common_positions.extend(primary_positions)
                        
                        # STRATEGY B: Dense grid search for high-resolution images
                        if height > 1000:  # High resolution images
                            # More granular search between primary positions
                            fine_grid = []
                            for i in range(10):  # 10 positions between 25% and 75%
                                pos = height * (0.25 + i * 0.05)
                                if pos not in primary_positions:  # Avoid duplicates
                                    fine_grid.append(pos)
                            common_positions.extend(fine_grid)
                        
                        # STRATEGY C: OCR-guided positioning (look for number patterns that indicate player rows)
                        ocr_guided_positions = []
                        for result in ocr_results:
                            if len(result) >= 3:
                                text = result[1].strip()
                                # Look for KDA patterns (e.g., "5/2/8", numbers separated by slashes)
                                if re.match(r'\d+[/\-\.]\d+[/\-\.]\d+', text):
                                    bbox = result[0]
                                    y_pos = sum(point[1] for point in bbox) / len(bbox)
                                    if height * 0.2 <= y_pos <= height * 0.8:  # Reasonable range
                                        ocr_guided_positions.append(y_pos)
                        
                        if ocr_guided_positions:
                            common_positions.extend(ocr_guided_positions)
                            logger.info(f"📊 Added {len(ocr_guided_positions)} OCR-guided positions based on KDA patterns")
                        
                        best_trophy_result = None
                        best_confidence = 0.0
                        detection_attempts = []
                        
                        for y_pos in common_positions:
                            try:
                                trophy_result = trophy_medal_detector.detect_trophy_in_player_row(
                                    image_path=image_path,
                                    player_row_y=y_pos,
                                    player_name_x=None,
                                    debug_mode=False,
                                    quality_hint=fallback_quality_hint
                                )
                                
                                # Track all detection attempts for analysis
                                detection_attempts.append({
                                    "y_position": y_pos,
                                    "trophy_type": trophy_result.trophy_type.value,
                                    "confidence": trophy_result.confidence,
                                    "method": trophy_result.detection_method.value
                                })
                                
                                if trophy_result.confidence > best_confidence:
                                    best_confidence = trophy_result.confidence
                                    best_trophy_result = trophy_result
                                    logger.info(f"🎯 Fallback trophy at Y={y_pos:.1f}: "
                                               f"{trophy_result.trophy_type.value} (conf: {trophy_result.confidence:.1%})")
                            
                            except Exception as e:
                                logger.warning(f"Fallback detection failed at Y={y_pos}: {e}")
                        
                        # CONFIDENCE BOOSTING: Analyze detection patterns for confidence adjustment
                        if detection_attempts:
                            logger.info(f"📊 Fallback analysis: {len(detection_attempts)} attempts, "
                                       f"best confidence: {best_confidence:.3f}")
                            
                            # ENHANCED CONFIDENCE BOOSTING: More aggressive boosting for consensus
                            trophy_types = [attempt["trophy_type"] for attempt in detection_attempts if attempt["confidence"] > 0.2]
                            
                            if trophy_types:
                                most_common_type = max(set(trophy_types), key=trophy_types.count)
                                type_count = trophy_types.count(most_common_type)
                                
                                # Calculate consensus strength
                                consensus_ratio = type_count / len(trophy_types) if trophy_types else 0
                                
                                if most_common_type != "none" and consensus_ratio >= 0.4:  # 40% consensus
                                    # Enhanced confidence boosting formula
                                    base_boost = min(0.25, consensus_ratio * 0.3)
                                    position_boost = min(0.15, type_count * 0.08)
                                    total_boost = base_boost + position_boost
                                    
                                    if best_trophy_result and best_trophy_result.trophy_type.value == most_common_type:
                                        original_confidence = best_confidence
                                        best_confidence = min(1.0, best_confidence + total_boost)
                                        logger.info(f"🚀 Enhanced confidence boost: {original_confidence:.3f} → {best_confidence:.3f} "
                                                   f"(consensus: {type_count}/{len(trophy_types)}, ratio: {consensus_ratio:.1%})")
                        
                        # AGGRESSIVE INTELLIGENT RETRY: Try multiple strategies to reach 95% target
                        if best_trophy_result and best_confidence < 0.6:  # More aggressive retry threshold
                            logger.info("🔄 Attempting aggressive retry strategies to improve confidence")
                            
                            # Strategy 1: Quality hint variations
                            quality_hints = ["poor", "average", "good", "excellent"]
                            for quality_hint in quality_hints:
                                if quality_hint != fallback_quality_hint:  # Skip already tried hint
                                    try:
                                        retry_y = best_trophy_result.bounding_box[1] if best_trophy_result.bounding_box else height * 0.5
                                        retry_result = trophy_medal_detector.detect_trophy_in_player_row(
                                            image_path=image_path,
                                            player_row_y=retry_y,
                                            player_name_x=None,
                                            debug_mode=False,
                                            quality_hint=quality_hint
                                        )
                                        
                                        if retry_result.confidence > best_confidence:
                                            best_confidence = retry_result.confidence
                                            best_trophy_result = retry_result
                                            logger.info(f"🎯 Quality hint retry improved: {quality_hint} → {retry_result.confidence:.1%}")
                                            
                                    except Exception as e:
                                        logger.warning(f"Quality hint retry failed: {e}")
                            
                            # Strategy 2: Focused search around best position with different X coordinates
                            if best_trophy_result and best_trophy_result.bounding_box:
                                best_y = best_trophy_result.bounding_box[1]
                                x_variations = [None, width * 0.3, width * 0.5, width * 0.7]
                                
                                for x_pos in x_variations:
                                    try:
                                        focused_result = trophy_medal_detector.detect_trophy_in_player_row(
                                            image_path=image_path,
                                            player_row_y=best_y,
                                            player_name_x=x_pos,
                                            debug_mode=False,
                                            quality_hint="good"  # Use good quality for focused search
                                        )
                                        
                                        if focused_result.confidence > best_confidence:
                                            best_confidence = focused_result.confidence
                                            best_trophy_result = focused_result
                                            logger.info(f"🎯 Focused search improved: X={x_pos} → {focused_result.confidence:.1%}")
                                            
                                    except Exception as e:
                                        logger.warning(f"Focused search retry failed: {e}")
                        
                        # If we found a trophy, return the result (lowered threshold for better detection)
                        if best_trophy_result and best_confidence > 0.25:
                            trophy_data = {
                                "mvp_detected": best_trophy_result.trophy_type.value == "mvp_crown",
                                "medal_type": (best_trophy_result.trophy_type.value 
                                             if best_trophy_result.trophy_type.value != "mvp_crown" else None),
                                "trophy_confidence": best_trophy_result.confidence,
                                "performance_label": best_trophy_result.performance_label.value,
                                "trophy_detection_method": f"fallback_{best_trophy_result.detection_method.value}",
                                "contextual_performance_rating": best_trophy_result.performance_label.value
                            }
                            
                            if best_trophy_result.trophy_type.value == "mvp_crown":
                                trophy_data["rating_boost_reasons"] = ["MVP detected via fallback positioning"]
                            
                            warnings.append(f"Trophy detected via fallback positioning (confidence: {best_confidence:.1%})")
                            logger.info(f"✅ Fallback trophy detection successful: {best_trophy_result.trophy_type.value}")
                            return trophy_data
                
                except Exception as e:
                    logger.error(f"Fallback trophy detection error: {e}")
                    warnings.append(f"Fallback trophy detection error: {str(e)}")
                
                # If all fallback strategies fail
                logger.warning("All fallback trophy detection strategies failed")
                warnings.append("Trophy detection failed - IGN not found and fallback strategies unsuccessful")
                return {}
            
            # Extract player row Y coordinate
            ign_bbox = ign_result["bbox"]
            player_row_y = sum(point[1] for point in ign_bbox) / 4
            player_name_x = sum(point[0] for point in ign_bbox) / 4
            
            logger.info(f"Trophy detection: Player row at y={player_row_y:.1f}, x={player_name_x:.1f}")
            
            # ENHANCED: Run trophy detection with quality hint and fallback strategies
            # Determine quality hint based on context (inline to avoid parallel processing issues)
            quality_hint = "average"  # Default fallback
            try:
                image_check = cv2.imread(image_path)
                if image_check is not None:
                    height, width = image_check.shape[:2]
                    total_pixels = width * height
                    if total_pixels > 2000000:
                        quality_hint = "good"
                    elif total_pixels > 1000000:
                        quality_hint = "average"
                    else:
                        quality_hint = "poor"
            except:
                quality_hint = "average"
            
            trophy_result = trophy_medal_detector.detect_trophy_in_player_row(
                image_path=image_path,
                player_row_y=player_row_y,
                player_name_x=player_name_x,
                debug_mode=True,  # Save debug images for analysis
                quality_hint=quality_hint
            )
            
            # FALLBACK: If trophy detection fails, try alternative positioning (lowered threshold)
            if trophy_result.confidence < 0.25:
                logger.info("🔄 Primary trophy detection failed, trying fallback positioning")
                
                # Try multiple Y positions around the detected player row
                fallback_positions = [
                    player_row_y - 30,  # Above
                    player_row_y + 30,  # Below
                    player_row_y - 50,  # Further above
                    player_row_y + 50   # Further below
                ]
                
                best_fallback_result = trophy_result
                for fallback_y in fallback_positions:
                    try:
                        fallback_result = trophy_medal_detector.detect_trophy_in_player_row(
                            image_path=image_path,
                            player_row_y=fallback_y,
                            player_name_x=player_name_x,
                            debug_mode=False,
                            quality_hint=quality_hint
                        )
                        
                        if fallback_result.confidence > best_fallback_result.confidence:
                            best_fallback_result = fallback_result
                            logger.info(f"🎯 Better trophy detection at fallback Y={fallback_y:.1f} "
                                       f"(confidence: {fallback_result.confidence:.1%})")
                    except Exception as e:
                        logger.warning(f"Fallback positioning failed at Y={fallback_y}: {e}")
                
                trophy_result = best_fallback_result
            
            # Log trophy detection results
            logger.info(f"Trophy detection result: {trophy_result.trophy_type.value} "
                       f"(confidence: {trophy_result.confidence:.1%})")
            
            # Update parsed data with trophy information
            trophy_data.update({
                "mvp_detected": trophy_result.trophy_type.value == "mvp_crown",
                "medal_type": trophy_result.trophy_type.value if trophy_result.trophy_type.value != "mvp_crown" else None,
                "trophy_confidence": trophy_result.confidence,
                "performance_label": trophy_result.performance_label.value,
                "trophy_detection_method": trophy_result.detection_method
            })
            
            # Apply performance rating based on trophy detection
            if trophy_result.confidence > 0.6:
                trophy_data["contextual_performance_rating"] = trophy_result.performance_label.value
                
                # Add specific performance indicators
                if trophy_result.trophy_type.value == "mvp_crown":
                    trophy_data["rating_boost_reasons"] = ["MVP Badge Detected"]
                    logger.info("🏆 MVP badge detected - applying 'Excellent' performance rating")
                    
                elif trophy_result.trophy_type.value == "gold_medal":
                    trophy_data["rating_boost_reasons"] = ["Gold Medal Detected"]
                    logger.info("🥇 Gold medal detected - applying 'Good' performance rating")
                    
                elif trophy_result.trophy_type.value == "silver_medal":
                    trophy_data["rating_boost_reasons"] = ["Silver Medal Detected"]
                    logger.info("🥈 Silver medal detected - applying 'Average' performance rating")
                    
                elif trophy_result.trophy_type.value == "bronze_medal":
                    trophy_data["rating_boost_reasons"] = ["Bronze Medal Detected"]
                    logger.info("🥉 Bronze medal detected - applying 'Poor' performance rating")
                    
                # Apply support role logic if applicable
                hero_name = parsed_data.get("hero", "unknown")
                if isinstance(hero_name, (list, tuple)):
                    hero_name = hero_name[0] if hero_name else "unknown"
                    
                if hero_name in ["estes", "mathilda", "angela", "rafaela", "kaja", "diggie"]:
                    # Support-specific performance criteria
                    tfp = parsed_data.get("teamfight_participation", 0)
                    if tfp >= 70 and trophy_result.trophy_type.value == "mvp_crown":
                        trophy_data["support_role_boost"] = True
                        trophy_data["rating_boost_reasons"].append("Support + TFP ≥ 70%")
                        logger.info("💫 Support role with high TFP - additional rating boost")
                
                # Apply victory bonus
                match_result = parsed_data.get("match_result", "unknown")
                if match_result == "victory" and trophy_result.confidence > 0.7:
                    if "rating_boost_reasons" not in trophy_data:
                        trophy_data["rating_boost_reasons"] = []
                    trophy_data["rating_boost_reasons"].append("Victory")
                    logger.info("🎊 Victory with high trophy confidence - additional boost")
                    
            else:
                # Low confidence trophy detection
                logger.warning(f"Low trophy detection confidence: {trophy_result.confidence:.1%}")
                warnings.append(f"Trophy detection confidence low: {trophy_result.confidence:.1%}")
            
            # Add debug information for analysis
            trophy_data["trophy_debug_info"] = {
                "detection_method": trophy_result.detection_method,
                "bounding_box": trophy_result.bounding_box,
                "color_analysis": trophy_result.color_analysis,
                "shape_analysis": trophy_result.shape_analysis,
                "search_region_y": player_row_y
            }
            
        except Exception as e:
            logger.error(f"Trophy detection failed: {str(e)}")
            warnings.append(f"Trophy detection error: {str(e)}")
            
        return trophy_data
    
    def _parse_player_row_enhanced(self, ign: str, ocr_results: List, warnings: List[str], image_path: str = None) -> Dict[str, Any]:
        """Enhanced player row parsing with better gold extraction."""
        # Prefer YOLO-based row anchoring for stability
        parsed_data = {}
        try:
            if image_path and _YOLO_AVAILABLE:
                y_pos = self._anchor_row_via_yolo(image_path, ign)
                if y_pos is not None:
                    parsed_data = self._extract_from_player_row_direct(ocr_results, y_pos, ign)
                    # Attempt fixed-column crops for stricter OCR
                    try:
                        crop_metrics = self._extract_metrics_by_row_crops(image_path, ocr_results, y_pos)
                        for k, v in (crop_metrics or {}).items():
                            if v not in (None, ""):
                                parsed_data[k] = v
                    except Exception as ce:
                        warnings.append(f"row-crop metrics failed: {ce}")
                warnings.append("Row anchored via YOLO player_name/mvp")
        except Exception as ye:
            warnings.append(f"YOLO row anchor failed: {str(ye)}")

        # Fallback to original method if YOLO anchor didn't yield data
        if not parsed_data:
            parsed_data = self._parse_player_row(ign, ocr_results, None, image_path)

        # If base parser couldn't extract, try robust IGN → direct row extraction
        if not parsed_data:
            try:
                ign_result = self.ign_matcher.find_ign_in_ocr(ign, ocr_results)
                if ign_result.get("found") and ign_result.get("bbox"):
                    bbox = ign_result["bbox"]
                    y_coords = [p[1] for p in (bbox if isinstance(bbox, list) else bbox.tolist())]
                    player_row_y = sum(y_coords) / len(y_coords)
                    parsed_data = self._extract_from_player_row_direct(ocr_results, player_row_y, ign)
                    # Row-specific hero detection to avoid cross-row mistakes
                    try:
                        if image_path:
                            rsd = RowSpecificHeroDetector()
                            hero_name, hero_conf, _dbg = rsd.detect_hero_in_player_row(
                                image_path=image_path,
                                player_ign=ign,
                                player_row_y=player_row_y,
                                ocr_results=ocr_results,
                                hero_override=None,
                            )
                            if hero_name and hero_name != "unknown" and hero_conf >= 0.75:
                                parsed_data["hero"] = hero_name
                                warnings.append(f"Hero set by row-specific detector (conf {hero_conf:.2f})")
                    except Exception as he:
                        warnings.append(f"Row-specific hero detector failed: {str(he)}")
                else:
                    parsed_data = {}
            except Exception as e:
                warnings.append(f"Direct row extraction failed: {str(e)}")
                parsed_data = {}

        if not parsed_data:
            return {}

        # Always validate/override hero with row-specific detector when possible
        try:
            if image_path:
                ign_result = self.ign_matcher.find_ign_in_ocr(ign, ocr_results)
                if ign_result.get("found") and ign_result.get("bbox"):
                    bbox = ign_result["bbox"]
                    y_coords = [p[1] for p in (bbox if isinstance(bbox, list) else bbox.tolist())]
                    player_row_y = sum(y_coords) / len(y_coords)
                    rsd = RowSpecificHeroDetector()
                    hero_name, hero_conf, _dbg = rsd.detect_hero_in_player_row(
                        image_path=image_path,
                        player_ign=ign,
                        player_row_y=player_row_y,
                        ocr_results=ocr_results,
                        hero_override=None,
                    )
                    if hero_name and hero_name != "unknown":
                        current_hero = parsed_data.get("hero")
                        # Override if current missing/unknown or row-specific has higher confidence expectation
                        if (not current_hero) or current_hero == "unknown" or hero_conf >= 0.80:
                            parsed_data["hero"] = hero_name
                            warnings.append(f"Hero validated by row-specific detector (conf {hero_conf:.2f})")
        except Exception as he2:
            warnings.append(f"Row-specific validation failed: {str(he2)}")
        
        # Enhanced gold parsing with multiple strategies
        if not parsed_data.get("gold") or parsed_data.get("gold", 0) <= 0:
            logger.info("Applying enhanced gold parsing strategies")
            
            # Strategy 1: Look for large numbers in proximity to player IGN
            gold_value = self._extract_gold_near_ign(ign, ocr_results)
            if gold_value:
                parsed_data["gold"] = gold_value
                logger.info(f"Gold found via IGN proximity: {gold_value}")
            
            # Strategy 2: Pattern-based gold extraction (common ranges)
            if not parsed_data.get("gold") or parsed_data.get("gold", 0) <= 0:
                gold_value = self._extract_gold_by_pattern(ocr_results)
                if gold_value:
                    parsed_data["gold"] = gold_value
                    logger.info(f"Gold found via pattern matching: {gold_value}")
            
            # Strategy 3: Statistical analysis of detected numbers
            if not parsed_data.get("gold") or parsed_data.get("gold", 0) <= 0:
                gold_value = self._extract_gold_statistical(ocr_results)
                if gold_value:
                    parsed_data["gold"] = gold_value
                    logger.info(f"Gold found via statistical analysis: {gold_value}")
                    warnings.append(f"Gold value estimated using statistical analysis: {gold_value}")
        
        return parsed_data

    def _extract_metrics_by_row_crops(self, image_path: str, ocr_results: List, row_y: float) -> Dict[str, Any]:
        """Crop anchored row and read KDA/gold/damage using column percentages.

        Returns a dict of extracted fields; missing ones are omitted.
        """
        try:
            img = cv2.imread(image_path)
            if not has_img(img):
                return {}
            H, W = img.shape[:2]

            # Estimate row bbox from OCR entries near row_y
            xs, ys = [], []
            for bbox, text, conf in ocr_results:
                try:
                    x_coords = [p[0] for p in bbox]
                    y_coords = [p[1] for p in bbox]
                except Exception:
                    continue
                cy = (min(y_coords) + max(y_coords)) / 2
                if abs(cy - row_y) <= 50:
                    xs.extend(x_coords)
                    ys.extend(y_coords)
            if not xs or not ys:
                # Fallback: take a fixed-height band across the full width around row_y
                band = 50
                y1 = max(0, int(row_y - band))
                y2 = min(H, int(row_y + band))
                x1, x2 = 0, W
                row = img[y1:y2, x1:x2]
                if not has_img(row):
                    return {}
                rh, rw = row.shape[:2]
            else:
                x1 = max(0, int(min(xs) - 8))
                x2 = min(W, int(max(xs) + 8))
                y1 = max(0, int(min(ys) - 6))
                y2 = min(H, int(max(ys) + 6))
                row = img[y1:y2, x1:x2]
                if not has_img(row):
                    return {}
                rh, rw = row.shape[:2]

            def crop(rng: Tuple[float, float]):
                sx = max(0, int(rng[0] * rw)); ex = min(rw, int(rng[1] * rw))
                return row[:, sx:ex]

            def ocr(crop_img, allow: str) -> str:
                reader = get_ocr_reader()
                gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
                gray = cv2.fastNlMeansDenoising(gray, h=8)
                txts = reader.readtext(gray, detail=0, allowlist=allow)
                return " ".join(txts) if txts else ""

            out: Dict[str, Any] = {}

            # Scoreboard columns
            COL_KDA = (0.28, 0.43)
            COL_GOLD = (0.44, 0.53)
            try:
                kda_crop = crop(COL_KDA)
                # Upscale for sharper OCR on small digits
                try:
                    kda_crop = cv2.resize(kda_crop, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                except Exception:
                    pass
                t = ocr(kda_crop, "0123456789/")
                kda = read_kda(t)
                if kda:
                    out['kills'], out['deaths'], out['assists'] = kda
                    logger.info("metric_source:kda=row_crop_kda(upscaled)")
            except Exception:
                pass
            try:
                gtxt = ocr(crop(COL_GOLD), "0123456789")
                gval = read_int(gtxt)
                if gval is not None and gval >= 1000:
                    out['gold'] = gval
                    logger.info("metric_source:gold=row_crop_gold")
            except Exception:
                pass

            # Damage screen columns
            COL_DMG_HERO = (0.03, 0.16)
            COL_DMG_TUR = (0.18, 0.30)
            COL_DMG_TAKEN = (0.32, 0.45)
            COL_TF_PART = (0.47, 0.61)
            try:
                hd = read_int(ocr(crop(COL_DMG_HERO), "0123456789"))
                if hd is not None:
                    out['hero_damage'] = hd
                    logger.info("metric_source:hero_damage=row_crop_damage")
            except Exception:
                pass
            try:
                td = read_int(ocr(crop(COL_DMG_TUR), "0123456789"))
                if td is not None:
                    out['turret_damage'] = td
                    logger.info("metric_source:turret_damage=row_crop_damage")
            except Exception:
                pass
            try:
                tk = read_int(ocr(crop(COL_DMG_TAKEN), "0123456789"))
                if tk is not None:
                    out['damage_taken'] = tk
                    logger.info("metric_source:damage_taken=row_crop_damage")
            except Exception:
                pass
            try:
                tf = ocr(crop(COL_TF_PART), "0123456789%")
                m = re.search(r"(\d{1,3})\s*%", tf)
                if m:
                    out['teamfight_participation'] = int(m.group(1))
                    logger.info("metric_source:teamfight=row_crop_tf")
            except Exception:
                pass

            return out
        except Exception:
            return {}

    def _anchor_row_via_yolo(self, image_path: str, ign: str) -> Optional[float]:
        """Anchor player's row using YOLO `player_name` or `mvp_badge`.

        Returns:
            y-center (float) in pixels if found, else None.
        """
        try:
            service = get_yolo_detection_service() if _YOLO_AVAILABLE else None
            if not service:
                return None
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return None
            H, W = image.shape[:2]
            # Force YOLO usage by passing low ocr_confidence to bypass fallback gating
            dets = service.detect_objects(
                image_path,
                target_classes=["player_name", "mvp_badge"],
                ocr_confidence=0.0,
            ).get("detections", [])
            # Try fuzzy OCR inside player_name boxes
            name_boxes = [d for d in dets if d.get("class_name") == "player_name"]
            if name_boxes:
                reader = get_ocr_reader()
                from difflib import SequenceMatcher
                ign_norm = " ".join(ign.lower().split())
                best = (None, 0.0)
                for d in name_boxes:
                    x1, y1, x2, y2 = [int(v) for v in d.get("bbox_xyxy", [0, 0, 0, 0])]
                    x1 = max(0, x1); y1 = max(0, y1); x2 = min(W, x2); y2 = min(H, y2)
                    if x2 <= x1 or y2 <= y1:
                        continue
                    crop = image[y1:y2, x1:x2]
                    if crop is None or crop.size == 0:
                        continue
                    try:
                        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                        text = " ".join(reader.readtext(gray, detail=0)).lower().strip()
                        score = SequenceMatcher(None, ign_norm, text).ratio()
                        if score > best[1]:
                            best = ((x1, y1, x2, y2), score)
                    except Exception:
                        continue
                if best[0] is not None and best[1] >= 0.75:
                    _, y1, _, y2 = best[0]
                    return (y1 + y2) / 2.0
            # Fallback to MVP badge y
            mvp = [d for d in dets if d.get("class_name") == "mvp_badge"]
            if mvp:
                best = max(mvp, key=lambda dd: dd.get("confidence", 0.0))
                _, y1, _, y2 = [int(v) for v in best.get("bbox_xyxy", [0, 0, 0, 0])]
                return (y1 + y2) / 2.0
        except Exception:
            return None
        return None
    
    def _parse_fallback_strategy(self, ocr_results: List, warnings: List[str]) -> Dict[str, Any]:
        """Fallback parsing when IGN-based parsing fails."""
        logger.info("Applying fallback parsing strategy")
        
        parsed_data = {}
        all_text = " ".join([result[1] for result in ocr_results])
        
        # Extract all numbers and try to categorize them
        import re
        all_numbers = [int(match) for match in re.findall(r'\b(\d+)\b', all_text)]
        
        if not all_numbers:
            warnings.append("No numeric data found in fallback parsing")
            return {}
        
        # Sort numbers for analysis
        all_numbers.sort()
        
        # Gold: Typically the largest number (> 1000)
        gold_candidates = [n for n in all_numbers if n >= 1000]
        if gold_candidates:
            # Take the median gold value to avoid outliers
            gold_index = len(gold_candidates) // 2
            parsed_data["gold"] = gold_candidates[gold_index]
        
        # KDA: Small numbers (0-50)
        kda_candidates = [n for n in all_numbers if 0 <= n <= 50]
        if len(kda_candidates) >= 3:
            # Take first three as KDA
            parsed_data["kills"] = kda_candidates[0]
            parsed_data["deaths"] = max(1, kda_candidates[1])  # Deaths can't be 0
            parsed_data["assists"] = kda_candidates[2]
        
        # Damage: Medium-large numbers (1000-100000)
        damage_candidates = [n for n in all_numbers if 1000 <= n <= 100000]
        if damage_candidates:
            parsed_data["hero_damage"] = max(damage_candidates)
        
        if parsed_data:
            warnings.append("Data extracted using fallback parsing - accuracy may be reduced")
        
        return parsed_data
    
    def _extract_gold_near_ign(self, ign: str, ocr_results: List) -> Optional[int]:
        """Extract gold by finding large numbers near the player IGN."""
        import re
        
        # Find IGN position in OCR results
        ign_positions = []
        for i, (bbox, text, conf) in enumerate(ocr_results):
            if is_ign_match(ign, text):
                ign_positions.append(i)
        
        if not ign_positions:
            return None
        
        # Look for gold values within 3 positions of IGN
        for ign_pos in ign_positions:
            for i in range(max(0, ign_pos - 3), min(len(ocr_results), ign_pos + 4)):
                bbox, text, conf = ocr_results[i]
                numbers = [int(match) for match in re.findall(r'\b(\d{4,6})\b', text)]
                
                for num in numbers:
                    if 1000 <= num <= 50000:  # Reasonable gold range
                        return num
        
        return None
    
    def _extract_gold_by_pattern(self, ocr_results: List) -> Optional[int]:
        """Extract gold using common MLBB gold value patterns."""
        import re
        
        gold_patterns = [
            r'\b(1[0-9]{3,4})\b',   # 1000-19999 range
            r'\b(2[0-9]{3,4})\b',   # 2000-29999 range  
            r'\b(3[0-9]{3,4})\b',   # 3000-39999 range
            r'\b([4-9][0-9]{3,4})\b' # 4000+ range
        ]
        
        all_text = " ".join([result[1] for result in ocr_results])
        
        for pattern in gold_patterns:
            matches = re.findall(pattern, all_text)
            if matches:
                # Return the most reasonable gold value
                gold_values = [int(match) for match in matches]
                # Filter for reasonable game gold amounts
                reasonable_values = [g for g in gold_values if 1000 <= g <= 30000]
                if reasonable_values:
                    return reasonable_values[0]
        
        return None
    
    def _extract_gold_statistical(self, ocr_results: List) -> Optional[int]:
        """Extract gold using statistical analysis of all detected numbers."""
        import re
        
        all_text = " ".join([result[1] for result in ocr_results])
        all_numbers = [int(match) for match in re.findall(r'\b(\d+)\b', all_text)]
        
        if not all_numbers:
            return None
        
        # Find numbers in typical gold range
        gold_candidates = [n for n in all_numbers if 1000 <= n <= 30000]
        
        if not gold_candidates:
            return None
        
        # Use median to avoid outliers
        gold_candidates.sort()
        median_index = len(gold_candidates) // 2
        estimated_gold = gold_candidates[median_index]
        
        # Sanity check: should be reasonable for match duration
        if 800 <= estimated_gold <= 35000:
            return estimated_gold
        
        return None
    
    def _validate_data_completeness(self, parsed_data: Dict[str, Any], warnings: List[str]) -> float:
        """Validate completeness of parsed data."""
        required_fields = ["kills", "deaths", "assists", "hero", "gold"]
        optional_fields = ["hero_damage", "turret_damage", "damage_taken", "teamfight_participation"]
        
        required_score = sum(1 for field in required_fields if parsed_data.get(field))
        optional_score = sum(1 for field in optional_fields if parsed_data.get(field))
        
        completeness = (required_score / len(required_fields)) * 0.7 + (optional_score / len(optional_fields)) * 0.3
        
        if completeness < 0.5:
            warnings.append(f"Low data completeness: {completeness:.1%}")
        
        return completeness
    
    def _calculate_overall_confidence(
        self, hero_confidence: float, warning_count: int, data_field_count: int, completeness_score: float
    ) -> float:
        """Calculate overall confidence score with data-first approach."""
        # NEW APPROACH: Data quality is primary factor, hero detection is secondary
        confidence = 0.0
        
        # 1. DATA COMPLETENESS: 50% weight - most important factor
        confidence += completeness_score * 0.50
        
        # 2. CRITICAL DATA PRESENCE: 25% weight - KDA + Gold = viable analysis
        critical_data_score = 0.0
        if data_field_count >= 4:  # KDA + Gold minimum
            critical_data_score = 0.8
        elif data_field_count >= 2:  # Partial data
            critical_data_score = 0.4
        elif data_field_count >= 1:  # Some data
            critical_data_score = 0.2
        confidence += critical_data_score * 0.25
        
        # 3. HERO DETECTION: Only 10% weight - nice to have, not essential
        confidence += hero_confidence * 0.10
        
        # 4. BASE CONFIDENCE: 15% - ensures viable minimum
        base_confidence = 0.15
        confidence += base_confidence
        
        # BONUSES for high-quality extraction
        quality_bonus = 0.0
        if completeness_score >= 0.8:  # Excellent data quality
            quality_bonus += 0.15
        elif completeness_score >= 0.6:  # Good data quality
            quality_bonus += 0.10
        
        if data_field_count >= 6:  # Rich data set
            quality_bonus += 0.10
        
        confidence += quality_bonus
        
        # WARNING PENALTIES (minimal impact)
        warning_penalty = min(0.20, warning_count * 0.05)  # Max 20% penalty
        confidence -= warning_penalty
        
        # SMART FLOOR: Based on actual data extracted
        if data_field_count >= 3 and completeness_score >= 0.3:
            minimum_confidence = 0.30  # We have usable data
        elif data_field_count >= 1:
            minimum_confidence = 0.15  # We have some data  
        else:
            minimum_confidence = 0.05  # Almost no data
        
        # Ensure valid range with smart boundaries
        final_confidence = max(minimum_confidence, min(1.0, confidence))
        
        logger.debug(f"Confidence calculation: completeness={completeness_score:.3f}, "
                    f"fields={data_field_count}, hero={hero_confidence:.3f}, "
                    f"warnings={warning_count}, final={final_confidence:.3f}")
        
        return float(final_confidence)
    
    def _calculate_screenshot_confidence(self, text_content: str, warnings: List[str]) -> float:
        """Calculate confidence score based on detected elements."""
        confidence_factors = []
        
        # Check for key UI elements
        ui_elements = ["duration", "gold", "damage", "kda", "kills", "deaths", "assists"]
        detected_elements = sum(1 for element in ui_elements if element in text_content.lower())
        confidence_factors.append(detected_elements / len(ui_elements))
        
        # Penalty for warnings
        warning_penalty = max(0, 1 - (len(warnings) * 0.1))
        confidence_factors.append(warning_penalty)
        
        # Check for match result clarity
        result_clarity = 1.0 if any(word in text_content.lower() for word in ["victory", "defeat"]) else 0.7
        confidence_factors.append(result_clarity)
        
        # Average confidence - ensure Python float return type
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        return float(round(overall_confidence, 2))
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "player_ign": session.player_ign,
            "screenshot_count": len(session.screenshots),
            "is_complete": session.is_complete,
            "created_at": session.created_at,
            "last_updated": session.last_updated,
            "screenshot_types": [s.screenshot_type.value for s in session.screenshots]
        }
    
    def analyze_screenshot_enhanced(self, image_path: str, ign: str, **kwargs) -> Dict[str, Any]:
        """
        Enhanced MLBB screenshot analysis with hybrid detection, progressive timeout,
        and early termination capabilities.
        
        This method addresses the core issues:
        1. False positive success reporting - Fixed with confidence-based success determination
        2. Poor OCR pipeline - Enhanced with MLBB-specific preprocessing and ROI detection  
        3. No fallback strategies - Implemented hybrid detection (OCR → YOLO → Template)
        4. Resource waste - Added early termination and progressive timeouts
        """
        start_time = time.time()
        
        # Initialize progressive timeout manager with performance limits
        if self.parallel_manager:
            self.parallel_manager.processing_start_time = start_time
            if hasattr(self.parallel_manager, 'timeout_manager'):
                self.parallel_manager.timeout_manager.start_analysis()
        
        logger.info(f"🚀 Starting enhanced MLBB analysis for {ign}")
        
        try:
            # Stage 1: Enhanced image preprocessing with ROI detection
            logger.info("🔹 Stage 1: Enhanced image preprocessing")
            preprocessing_result = self._preprocess_image_enhanced(image_path)
            
            if not preprocessing_result['success']:
                logger.warning(f"❌ Preprocessing failed: {preprocessing_result['quality_score']:.3f}")
                return self._create_failure_result(
                    'preprocessing_failed', 
                    preprocessing_result['quality_score'],
                    time.time() - start_time
                )
            
            # Check for early termination based on quality
            quality_score = preprocessing_result['quality_score']
            if self.parallel_manager and self.parallel_manager.timeout_manager.should_terminate(quality_score):
                logger.warning(f"⏰ Early termination triggered: quality={quality_score:.3f}")
                return self._create_failure_result(
                    'early_termination',
                    quality_score,
                    time.time() - start_time
                )
            
            # Stage 2: Hybrid detection strategy (OCR → YOLO → Template)
            logger.info(f"🔹 Stage 2: Hybrid detection (quality: {quality_score:.3f})")
            detection_result = self.hybrid_engine.analyze_with_hybrid_strategy(
                image_path, ign, preprocessing_result
            )
            
            # Check timeout during detection
            if self.parallel_manager and self.parallel_manager.timeout_manager.should_terminate():
                logger.warning("⏰ Timeout during detection phase")
                return self._create_failure_result(
                    'detection_timeout',
                    quality_score,
                    time.time() - start_time
                )
            
            # Stage 3: Result validation and confidence assessment
            logger.info(f"🔹 Stage 3: Result validation (method: {detection_result['method_used']})")
            final_result = self._validate_and_enhance_results(detection_result, preprocessing_result, ign)
            
            # Add comprehensive metadata
            processing_time = time.time() - start_time
            final_result.update({
                'processing_time': processing_time,
                'image_quality_score': quality_score,
                'method_used': detection_result['method_used'],
                'fallback_attempts': detection_result['fallback_attempts'],
                'early_termination': False,
                'regions_processed': len(preprocessing_result['regions'])
            })
            
            # CRITICAL FIX: Confidence-based success determination (addresses false positive issue)
            confidence = final_result.get('confidence', 0.0)
            if confidence < 0.3:  # Require minimum 30% confidence
                final_result['success'] = False
                logger.warning(f"❌ Analysis failed: Low confidence {confidence:.3f}")
            else:
                final_result['success'] = True
                logger.info(f"✅ Analysis successful: {confidence:.3f} confidence in {processing_time:.1f}s")
            
            return final_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Enhanced analysis failed: {e}")
            return self._create_failure_result(
                'analysis_error',
                0.0,
                processing_time,
                str(e)
            )
    
    def _create_failure_result(self, failure_type: str, quality_score: float, processing_time: float, error_msg: str = None) -> Dict[str, Any]:
        """Create a standardized failure result that never reports false success."""
        result = {
            'success': False,  # CRITICAL: Never report success on failure
            'confidence': 0.0,
            'processing_time': processing_time,
            'image_quality_score': quality_score,
            'failure_type': failure_type,
            'method_used': 'none',
            'fallback_attempts': [],
            'early_termination': failure_type in ['early_termination', 'detection_timeout'],
            'regions_processed': 0,
            # Default empty values for backward compatibility
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'hero': 'Unknown',
            'gold': 0,
            'hero_damage': 0,
            'performance_rating': 'Unknown'
        }
        
        if error_msg:
            result['error'] = error_msg
            
        logger.info(f"📊 Failure result: {failure_type}, quality={quality_score:.3f}, time={processing_time:.1f}s")
        return result
    
    def _validate_and_enhance_results(self, detection_result: Dict[str, Any], preprocessing_result: Dict[str, Any], ign: str) -> Dict[str, Any]:
        """Validate and enhance detection results with additional processing."""
        validated_data = detection_result['data'].copy()
        
        # Add confidence from detection
        validated_data['confidence'] = detection_result['confidence']
        
        # Enhance with region-specific analysis if OCR was used
        if detection_result['method_used'] == 'ocr' and preprocessing_result['regions']:
            enhanced_data = self._extract_additional_metrics(preprocessing_result['regions'], ign)
            validated_data.update(enhanced_data)
        
        # Apply MLBB-specific validation rules
        validated_data = self._apply_mlbb_validation_rules(validated_data)
        
        # Apply default values for missing fields
        self._apply_data_defaults(validated_data)
        
        return validated_data
    
    def _extract_additional_metrics(self, regions: Dict[str, np.ndarray], ign: str) -> Dict[str, Any]:
        """Extract additional metrics from processed regions using existing logic."""
        additional_data = {}
        
        # This would integrate with existing extraction methods like:
        # - extract_player_row_data()  
        # - _detect_trophy_and_performance()
        # - _extract_kda_from_text()
        
        # For now, return empty dict to maintain structure
        return additional_data
    
    def _apply_mlbb_validation_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply MLBB-specific validation rules to extracted data."""
        # Ensure reasonable value ranges for MLBB
        if 'kills' in data:
            data['kills'] = max(0, min(int(data.get('kills', 0)), 50))
        if 'deaths' in data:
            data['deaths'] = max(0, min(int(data.get('deaths', 0)), 30))
        if 'assists' in data:
            data['assists'] = max(0, min(int(data.get('assists', 0)), 100))
        if 'gold' in data:
            data['gold'] = max(0, min(int(data.get('gold', 0)), 50000))
        if 'hero_damage' in data:
            data['hero_damage'] = max(0, int(data.get('hero_damage', 0)))
            
        return data


# Global enhanced data collector instance
enhanced_data_collector = EnhancedDataCollector()
