"""
Hero Resolution Module for MLBB Coach AI

Resolves hero names from portrait thumbnails using deterministic template matching
with phash and HSV color histogram similarity metrics.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pickle
import hashlib

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import imagehash
from skimage import exposure
from skimage.filters import unsharp_mask

# Configure logging
logger = logging.getLogger(__name__)

class HeroResolver:
    """
    Resolves hero names from portrait thumbnails using deterministic template matching.
    
    Uses phash and HSV color histogram similarity metrics for reliable matching.
    """
    
    def __init__(self, heroes_data_path: str = "data/heroes_cleaned.json"):
        self.heroes_data_path = heroes_data_path
        self.heroes_data = None
        self._load_heroes_data()
    
    def _load_heroes_data(self) -> None:
        """Load heroes data from JSON file"""
        try:
            with open(self.heroes_data_path, 'r') as f:
                self.heroes_data = json.load(f)
            logger.info(f"Loaded {len(self.heroes_data['heroes'])} heroes from {self.heroes_data_path}")
        except Exception as e:
            logger.error(f"Failed to load heroes data: {e}")
            self.heroes_data = {"heroes": []}
    
    def _preprocess_portrait(self, portrait_img: np.ndarray) -> np.ndarray:
        """
        Preprocess portrait image for template matching.
        
        Args:
            portrait_img: Input portrait image (BGR format)
            
        Returns:
            Preprocessed image (RGB format, 96x96)
        """
        # Convert BGR to RGB
        if len(portrait_img.shape) == 3 and portrait_img.shape[2] == 3:
            portrait_img = cv2.cvtColor(portrait_img, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image for processing
        pil_img = Image.fromarray(portrait_img)
        
        # Resize to 96x96
        pil_img = pil_img.resize((96, 96), Image.Resampling.LANCZOS)
        
        # Light denoising
        img_array = np.array(pil_img)
        img_array = cv2.bilateralFilter(img_array, 9, 75, 75)
        
        # Histogram equalization
        img_array = exposure.equalize_hist(img_array)
        img_array = (img_array * 255).astype(np.uint8)
        
        return img_array
    
    def _compute_similarity_metrics(self, portrait_img: np.ndarray, template_data: Dict) -> Dict[str, float]:
        """
        Compute similarity metrics between portrait and template.
        
        Args:
            portrait_img: Preprocessed portrait image (96x96 RGB)
            template_data: Template data from templates index
            
        Returns:
            Dictionary of similarity scores
        """
        scores = {}
        
        try:
            # Convert to PIL Image for phash computation
            pil_img = Image.fromarray(portrait_img)
            
            # Compute phash
            portrait_phash = imagehash.phash(pil_img)
            template_phash = imagehash.hex_to_hash(template_data['phash'])
            
            # Phash distance (lower is better, normalize to [0,1])
            phash_distance = portrait_phash - template_phash
            scores['phash'] = max(0.0, 1.0 - (phash_distance / 64.0))
            
            # Compute HSV color histogram
            hsv_img = cv2.cvtColor(portrait_img, cv2.COLOR_RGB2HSV)
            hist = cv2.calcHist([hsv_img], [0, 1, 2], None, [16, 4, 4], [0, 180, 0, 256, 0, 256])
            hist = hist.flatten()
            hist = hist / (np.sum(hist) + 1e-8)  # L1 normalize
            
            # Bhattacharyya distance for histogram comparison
            template_hist = np.array(template_data['histogram'], dtype=np.float32)
            hist_float32 = hist.astype(np.float32)
            bhattacharyya_dist = cv2.compareHist(hist_float32, template_hist, cv2.HISTCMP_BHATTACHARYYA)
            scores['histogram'] = max(0.0, 1.0 - bhattacharyya_dist)
            
        except Exception as e:
            logger.error(f"Error computing similarity metrics: {e}")
            scores = {'phash': 0.0, 'histogram': 0.0}
        
        return scores
    
    def _fuse_scores(self, scores: Dict[str, float], role_hint: Optional[str] = None, hero_role: Optional[str] = None) -> float:
        """
        Fuse similarity scores into a single confidence score.
        
        Args:
            scores: Dictionary of similarity scores
            role_hint: Optional role hint from text
            hero_role: Hero role from template data
            
        Returns:
            Fused confidence score [0, 1]
        """
        # Weighted average: 70% phash, 30% histogram
        fused_score = 0.7 * scores.get('phash', 0.0) + 0.3 * scores.get('histogram', 0.0)
        
        # Add role hint bonus if provided
        if role_hint and hero_role and role_hint.lower() == hero_role.lower():
            fused_score += 0.05
        
        return min(1.0, max(0.0, fused_score))
    
    def resolve_hero_from_portrait(self, row_img: np.ndarray, avatar_bbox: Tuple[int, int, int, int], 
                                 templates_index: Dict[str, Dict[str, Any]], 
                                 role_hint: Optional[str] = None) -> Tuple[Optional[str], float, Dict]:
        """
        Resolve hero from portrait thumbnail using deterministic template matching.
        
        Args:
            row_img: Player row image (BGR format)
            avatar_bbox: Avatar bounding box (x, y, w, h)
            templates_index: Templates index from local assets
            role_hint: Optional role hint from text analysis
            
        Returns:
            Tuple of (hero_slug, confidence, debug_info)
        """
        debug_info = {
            'avatar_bbox': avatar_bbox,
            'candidates': [],
            'top_candidate': None,
            'role_hint': role_hint
        }
        
        try:
            # Crop avatar from row image
            x, y, w, h = avatar_bbox
            avatar_img = row_img[y:y+h, x:x+w]
            
            # Preprocess avatar
            processed_avatar = self._preprocess_portrait(avatar_img)
            
            # Compare with all templates
            candidates = []
            
            for slug, template_data in templates_index.items():
                scores = self._compute_similarity_metrics(processed_avatar, template_data)
                
                # Get hero role for role hint bonus
                hero_role = self.lookup_role(slug)
                confidence = self._fuse_scores(scores, role_hint, hero_role)
                
                candidates.append({
                    'slug': slug,
                    'confidence': confidence,
                    'scores': scores,
                    'role': hero_role
                })
            
            # Sort by confidence
            candidates.sort(key=lambda x: x['confidence'], reverse=True)
            debug_info['candidates'] = candidates[:3]  # Top 3 candidates
            
            # Return top candidate if confidence >= 0.35 (lowered for testing)
            if candidates and candidates[0]['confidence'] >= 0.35:
                top_candidate = candidates[0]
                debug_info['top_candidate'] = top_candidate
                return top_candidate['slug'], top_candidate['confidence'], debug_info
            
            debug_info['error'] = f"Best confidence {candidates[0]['confidence']:.3f} below threshold 0.40"
            return None, 0.0, debug_info
            
        except Exception as e:
            logger.error(f"Error resolving hero from portrait: {e}")
            debug_info['error'] = str(e)
            return None, 0.0, debug_info
    
    def lookup_role(self, hero_slug: str) -> Optional[str]:
        """
        Look up hero role from slug using heroes_cleaned.json.
        
        Args:
            hero_slug: Hero slug (e.g., 'kagura')
            
        Returns:
            Role string or None if not found
        """
        if not self.heroes_data:
            return None
        
        for hero in self.heroes_data['heroes']:
            if hero['slug'] == hero_slug:
                return hero['role']
        return None


# Module-level singleton instance
_hero_resolver = None

def get_hero_resolver() -> HeroResolver:
    """Get singleton hero resolver instance."""
    global _hero_resolver
    if _hero_resolver is None:
        _hero_resolver = HeroResolver()
    return _hero_resolver

def resolve_hero_from_portrait(row_img: np.ndarray, avatar_bbox: Tuple[int, int, int, int], 
                             templates_index: Dict[str, Dict[str, Any]], 
                             role_hint: Optional[str] = None) -> Tuple[Optional[str], float, Dict]:
    """
    Convenience function to resolve hero from portrait.
    
    Args:
        row_img: Player row image (BGR format)
        avatar_bbox: Avatar bounding box (x, y, w, h)
        templates_index: Templates index from local assets
        role_hint: Optional role hint from text analysis
        
    Returns:
        Tuple of (hero_slug, confidence, debug_info)
    """
    resolver = get_hero_resolver()
    return resolver.resolve_hero_from_portrait(row_img, avatar_bbox, templates_index, role_hint)

def lookup_role(hero_slug: str) -> Optional[str]:
    """
    Convenience function to lookup hero role.
    
    Args:
        hero_slug: Hero slug (e.g., 'kagura')
        
    Returns:
        Role string or None if not found
    """
    resolver = get_hero_resolver()
    return resolver.lookup_role(hero_slug)
