"""
Advanced Hero Resolver for OCR Mission 4

Implements phash (perceptual hash), ORB descriptors + BFMatcher, and histogram
matching for ≥90% accuracy on golden hero portraits.

Target: Replace placeholder logic with real similarity metrics for hero detection.
"""

import cv2
import numpy as np
import logging
import hashlib
import sys
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
import os

# Add backend path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parents[1]
sys.path.insert(0, str(project_root))

try:
    from src.config.data_paths import get_heroes_json_path
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class HeroMatchResult:
    """Result of hero matching operation."""
    hero_name: str
    confidence: float
    method: str
    phash_distance: Optional[int] = None
    orb_matches: Optional[int] = None
    histogram_similarity: Optional[float] = None
    debug_info: Dict[str, Any] = None


class AdvancedHeroResolver:
    """
    Advanced hero resolver using multiple similarity metrics.
    
    Implements:
    - phash (perceptual hash) for fast candidate filtering
    - ORB descriptors + BFMatcher for final match
    - Histogram fallback for ambiguous cases
    """
    
    def __init__(self, hero_database_path: Optional[str] = None):
        """Initialize the advanced hero resolver."""
        self.hero_database_path = hero_database_path or self._find_hero_database()
        self.hero_templates = {}
        self.phash_database = {}
        self.orb_database = {}
        self.histogram_database = {}
        
        # ORB detector and matcher
        self.orb_detector = cv2.ORB_create(nfeatures=1000)
        self.bf_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Load hero templates and build databases
        self._load_hero_templates()
        self._build_similarity_databases()
        
        logger.info(f"Advanced Hero Resolver initialized with {len(self.hero_templates)} heroes")
    
    def _find_hero_database(self) -> str:
        """Find the hero database file."""
        # Use configuration system first
        if CONFIG_AVAILABLE:
            config_path = get_heroes_json_path()
            if os.path.exists(config_path):
                return config_path
        
        # Fallback to multiple paths if config not available
        fallback_paths = [
            "data/heroes_cleaned.json",
            "../data/heroes_cleaned.json",
            "../../data/heroes_cleaned.json",
            "/Users/lesz/Documents/Project-AI/skillshift-ai/data/heroes_cleaned.json"
        ]
        
        for path in fallback_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("Hero database not found, using fallback")
        return "data/heroes_cleaned.json"
    
    def _load_hero_templates(self):
        """Load hero portrait templates from database."""
        try:
            if os.path.exists(self.hero_database_path):
                with open(self.hero_database_path, 'r', encoding='utf-8') as f:
                    heroes_data = json.load(f)
                    
                # Handle both list and dict formats
                if isinstance(heroes_data, list):
                    heroes_list = heroes_data
                elif isinstance(heroes_data, dict):
                    heroes_list = list(heroes_data.values())
                else:
                    heroes_list = []
                    
                for hero in heroes_list:
                    if isinstance(hero, dict):
                        hero_name = hero.get('name', '').lower()
                        image_path = hero.get('image_path', '')
                    else:
                        continue
                    
                    if hero_name and image_path and os.path.exists(image_path):
                        # Load and preprocess template image
                        template_img = cv2.imread(image_path)
                        if template_img is not None:
                            # Resize to standard size for consistent matching
                            template_img = cv2.resize(template_img, (64, 64))
                            self.hero_templates[hero_name] = template_img
                            
        except Exception as e:
            logger.error(f"Error loading hero templates: {e}")
            # Create fallback templates for common heroes
            self._create_fallback_templates()
    
    def _create_fallback_templates(self):
        """Create fallback templates for common heroes."""
        # Create simple colored templates for testing
        common_heroes = ['kagura', 'lancelot', 'beatrix', 'hayabusa', 'chou']
        
        for i, hero in enumerate(common_heroes):
            # Create a simple colored template
            template = np.zeros((64, 64, 3), dtype=np.uint8)
            template[:, :] = [50 + i * 40, 100 + i * 30, 150 + i * 20]
            self.hero_templates[hero] = template
            
        logger.info(f"Created {len(self.hero_templates)} fallback templates")
    
    def _build_similarity_databases(self):
        """Build phash, ORB, and histogram databases for all hero templates."""
        for hero_name, template_img in self.hero_templates.items():
            try:
                # Build phash database
                phash = self._compute_phash(template_img)
                self.phash_database[hero_name] = phash
                
                # Build ORB database
                gray_template = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
                kp, des = self.orb_detector.detectAndCompute(gray_template, None)
                if des is not None:
                    self.orb_database[hero_name] = (kp, des)
                
                # Build histogram database
                hist = self._compute_histogram(template_img)
                self.histogram_database[hero_name] = hist
                
            except Exception as e:
                logger.warning(f"Error building database for {hero_name}: {e}")
    
    def _compute_phash(self, image: np.ndarray) -> int:
        """Compute perceptual hash of an image."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Resize to 8x8 for phash
            resized = cv2.resize(gray, (8, 8))
            
            # Compute average
            avg = np.mean(resized)
            
            # Create hash
            phash = 0
            for i in range(8):
                for j in range(8):
                    if resized[i, j] > avg:
                        phash |= 1 << (i * 8 + j)
            
            return phash
            
        except Exception as e:
            logger.error(f"Error computing phash: {e}")
            return 0
    
    def _compute_histogram(self, image: np.ndarray) -> np.ndarray:
        """Compute color histogram of an image."""
        try:
            # Convert to HSV for better color representation
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Compute histogram
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
            
            # Normalize
            hist = cv2.normalize(hist, hist).flatten()
            
            return hist
            
        except Exception as e:
            logger.error(f"Error computing histogram: {e}")
            return np.zeros(180000)  # Default size for HSV histogram
    
    def resolve_hero(self, hero_crop: np.ndarray, target_ign: str = "Diary of dolls") -> HeroMatchResult:
        """
        Resolve hero from portrait crop using multiple similarity metrics.
        
        Args:
            hero_crop: Cropped hero portrait image
            target_ign: Target player's IGN for context
            
        Returns:
            HeroMatchResult with hero name, confidence, and method
        """
        try:
            if hero_crop is None or hero_crop.size == 0:
                return HeroMatchResult("unknown", 0.0, "no_image")
            
            # Preprocess the input image
            processed_crop = self._preprocess_hero_crop(hero_crop)
            
            # Step 1: Fast phash filtering
            phash_candidates = self._phash_filter(processed_crop)
            
            if not phash_candidates:
                logger.warning("No phash candidates found")
                return HeroMatchResult("unknown", 0.0, "phash_filter_failed")
            
            # Step 2: ORB matching on candidates
            orb_result = self._orb_match(processed_crop, phash_candidates)
            
            if orb_result.confidence >= 0.9:
                logger.info(f"Hero resolved by ORB: {orb_result.hero_name} (confidence: {orb_result.confidence:.3f})")
                return orb_result
            
            # Step 3: Histogram fallback for ambiguous cases
            histogram_result = self._histogram_match(processed_crop, phash_candidates)
            
            if histogram_result.confidence >= 0.7:
                logger.info(f"Hero resolved by histogram: {histogram_result.hero_name} (confidence: {histogram_result.confidence:.3f})")
                return histogram_result
            
            # Return best result from all methods
            best_result = self._select_best_result([orb_result, histogram_result])
            
            logger.info(f"Hero resolved: {best_result.hero_name} (confidence: {best_result.confidence:.3f}, method: {best_result.method})")
            return best_result
            
        except Exception as e:
            logger.error(f"Error resolving hero: {e}")
            return HeroMatchResult("unknown", 0.0, "error", debug_info={"error": str(e)})
    
    def _preprocess_hero_crop(self, crop: np.ndarray) -> np.ndarray:
        """Preprocess hero crop for consistent matching with OCR Mission 5 enhancements."""
        try:
            # Handle partial/corner crops with reflection padding
            if self._is_partial_crop(crop):
                crop = self._reflect_pad_crop(crop, pad=8)
            
            # Resize to standard size
            resized = cv2.resize(crop, (64, 64))
            
            # Apply slight Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(resized, (3, 3), 0)
            
            # Enhanced contrast with CLAHE (OCR Mission 5 requirement)
            lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error preprocessing hero crop: {e}")
            return crop
    
    def _is_partial_crop(self, crop: np.ndarray) -> bool:
        """Check if crop appears to be a partial/corner crop."""
        try:
            if crop is None or crop.size == 0:
                return True
            
            height, width = crop.shape[:2]
            
            # Check if crop is too small (likely partial)
            if height < 32 or width < 32:
                return True
            
            # Check for corner-like patterns (high contrast on one side)
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
            
            # Check edge variance - partial crops often have high variance on one edge
            left_edge = gray[:, :width//4]
            right_edge = gray[:, 3*width//4:]
            top_edge = gray[:height//4, :]
            bottom_edge = gray[3*height//4:, :]
            
            edge_variances = [
                np.var(left_edge),
                np.var(right_edge),
                np.var(top_edge),
                np.var(bottom_edge)
            ]
            
            # If one edge has much higher variance, likely a partial crop
            max_var = max(edge_variances)
            min_var = min(edge_variances)
            
            return max_var > min_var * 3.0  # Threshold for partial crop detection
            
        except Exception as e:
            logger.debug(f"Error checking partial crop: {e}")
            return False
    
    def _reflect_pad_crop(self, crop: np.ndarray, pad: int = 8) -> np.ndarray:
        """Apply reflection padding to partial crops."""
        try:
            if len(crop.shape) == 3:
                # Color image
                padded = cv2.copyMakeBorder(
                    crop, pad, pad, pad, pad, 
                    cv2.BORDER_REFLECT_101
                )
            else:
                # Grayscale image
                padded = cv2.copyMakeBorder(
                    crop, pad, pad, pad, pad, 
                    cv2.BORDER_REFLECT_101
                )
            
            return padded
            
        except Exception as e:
            logger.error(f"Error applying reflection padding: {e}")
            return crop
    
    def _phash_filter(self, processed_crop: np.ndarray) -> List[str]:
        """Filter candidates using phash distance with skin-aware prefilter (OCR Mission 5)."""
        try:
            crop_phash = self._compute_phash(processed_crop)
            candidates = []
            
            # OCR Mission 5: Skin-aware prefilter with configurable threshold
            from backend.ocr.robustness import robustness_config
            phash_threshold = robustness_config.phash_threshold
            
            for hero_name, template_phash in self.phash_database.items():
                # Calculate Hamming distance
                hamming_distance = bin(crop_phash ^ template_phash).count('1')
                
                # Skin-aware threshold: lower threshold for better skin variant detection
                if hamming_distance <= phash_threshold:
                    candidates.append(hero_name)
            
            logger.debug(f"Skin-aware phash filtering found {len(candidates)} candidates (threshold: {phash_threshold})")
            return candidates
            
        except Exception as e:
            logger.error(f"Error in phash filtering: {e}")
            return []
    
    def _orb_match(self, processed_crop: np.ndarray, candidates: List[str]) -> HeroMatchResult:
        """Match using ORB descriptors and BFMatcher."""
        try:
            # Extract ORB features from crop
            gray_crop = cv2.cvtColor(processed_crop, cv2.COLOR_BGR2GRAY)
            kp_crop, des_crop = self.orb_detector.detectAndCompute(gray_crop, None)
            
            if des_crop is None or len(kp_crop) < 10:
                return HeroMatchResult("unknown", 0.0, "orb_no_features")
            
            best_hero = "unknown"
            best_confidence = 0.0
            best_matches = 0
            best_phash_distance = None
            
            for hero_name in candidates:
                if hero_name not in self.orb_database:
                    continue
                
                kp_template, des_template = self.orb_database[hero_name]
                
                if des_template is None:
                    continue
                
                # Match descriptors
                matches = self.bf_matcher.match(des_crop, des_template)
                matches = sorted(matches, key=lambda x: x.distance)
                
                # Filter good matches
                good_matches = [m for m in matches if m.distance < 50]  # Adjust threshold
                
                if len(good_matches) >= 5:  # Minimum matches required
                    # Calculate confidence based on number of good matches
                    confidence = min(1.0, len(good_matches) / 20.0)  # Normalize to 0-1
                    
                    if confidence > best_confidence:
                        best_hero = hero_name
                        best_confidence = confidence
                        best_matches = len(good_matches)
                        
                        # Calculate phash distance for debug info
                        if hero_name in self.phash_database:
                            crop_phash = self._compute_phash(processed_crop)
                            template_phash = self.phash_database[hero_name]
                            best_phash_distance = bin(crop_phash ^ template_phash).count('1')
            
            return HeroMatchResult(
                hero_name=best_hero,
                confidence=best_confidence,
                method="orb",
                orb_matches=best_matches,
                phash_distance=best_phash_distance,
                debug_info={
                    "total_candidates": len(candidates),
                    "crop_features": len(kp_crop),
                    "good_matches": best_matches
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ORB matching: {e}")
            return HeroMatchResult("unknown", 0.0, "orb_error", debug_info={"error": str(e)})
    
    def _histogram_match(self, processed_crop: np.ndarray, candidates: List[str]) -> HeroMatchResult:
        """Match using histogram similarity as fallback."""
        try:
            crop_hist = self._compute_histogram(processed_crop)
            
            best_hero = "unknown"
            best_confidence = 0.0
            best_similarity = 0.0
            
            for hero_name in candidates:
                if hero_name not in self.histogram_database:
                    continue
                
                template_hist = self.histogram_database[hero_name]
                
                # Calculate histogram correlation
                similarity = cv2.compareHist(crop_hist, template_hist, cv2.HISTCMP_CORREL)
                
                if similarity > best_similarity:
                    best_hero = hero_name
                    best_similarity = similarity
                    best_confidence = similarity  # Use similarity as confidence
            
            return HeroMatchResult(
                hero_name=best_hero,
                confidence=best_confidence,
                method="histogram",
                histogram_similarity=best_similarity,
                debug_info={
                    "total_candidates": len(candidates),
                    "best_similarity": best_similarity
                }
            )
            
        except Exception as e:
            logger.error(f"Error in histogram matching: {e}")
            return HeroMatchResult("unknown", 0.0, "histogram_error", debug_info={"error": str(e)})
    
    def _select_best_result(self, results: List[HeroMatchResult]) -> HeroMatchResult:
        """Select the best result from multiple matching methods."""
        if not results:
            return HeroMatchResult("unknown", 0.0, "no_results")
        
        # Filter out unknown results
        valid_results = [r for r in results if r.hero_name != "unknown"]
        
        if not valid_results:
            return HeroMatchResult("unknown", 0.0, "no_valid_results")
        
        # Return result with highest confidence
        best_result = max(valid_results, key=lambda x: x.confidence)
        
        # Update method to indicate combination
        if len(valid_results) > 1:
            methods = [r.method for r in valid_results if r.confidence > 0.5]
            best_result.method = f"combined_{'+'.join(methods)}"
        
        return best_result
    
    def get_hero_confidence_breakdown(self, hero_crop: np.ndarray) -> Dict[str, Any]:
        """Get detailed confidence breakdown for debugging."""
        try:
            processed_crop = self._preprocess_hero_crop(hero_crop)
            
            # Get phash candidates
            phash_candidates = self._phash_filter(processed_crop)
            
            # Get ORB result
            orb_result = self._orb_match(processed_crop, phash_candidates)
            
            # Get histogram result
            histogram_result = self._histogram_match(processed_crop, phash_candidates)
            
            return {
                "phash_candidates": len(phash_candidates),
                "orb_result": {
                    "hero": orb_result.hero_name,
                    "confidence": orb_result.confidence,
                    "matches": orb_result.orb_matches
                },
                "histogram_result": {
                    "hero": histogram_result.hero_name,
                    "confidence": histogram_result.confidence,
                    "similarity": histogram_result.histogram_similarity
                },
                "final_result": self._select_best_result([orb_result, histogram_result]).__dict__
            }
            
        except Exception as e:
            return {"error": str(e)}


# Global instance
hero_resolver = AdvancedHeroResolver()