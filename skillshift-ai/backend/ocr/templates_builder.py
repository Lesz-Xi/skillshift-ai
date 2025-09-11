#!/usr/bin/env python3
"""
Templates Index Builder for MLBB Coach AI

Builds precomputed hero template features from heroes_cleaned.json
and saves them to cache for instant loading during hero resolution.
"""

import json
import pickle
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
import requests
from PIL import Image
import numpy as np
import cv2
import imagehash
from skimage import exposure

# Add backend path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parents[1]
sys.path.insert(0, str(project_root))

try:
    from src.config.data_paths import get_heroes_json_path
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class TemplatesBuilder:
    """Builds and caches hero template features for fast hero resolution."""
    
    def __init__(self, heroes_data_path: str, cache_dir: str = "backend/ocr/cache"):
        self.heroes_data_path = heroes_data_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates_cache_path = self.cache_dir / "hero_templates.pkl"
        self.images_cache_dir = self.cache_dir / "hero_images"
        self.images_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def build_templates_index(self) -> Dict[str, Any]:
        """
        Build templates index from heroes_cleaned.json.
        
        Returns:
            Dictionary mapping hero slugs to template data
        """
        logger.info("Building hero templates index...")
        
        with open(self.heroes_data_path, 'r') as f:
            heroes_data = json.load(f)
        
        templates_index = {}
        
        for hero in heroes_data['heroes']:
            slug = hero['slug']
            name = hero['name']
            role = hero['role']
            image_url = hero['image_url']
            
            logger.info(f"Processing hero: {name} ({slug})")
            
            # Download and process hero image
            template_data = self._process_hero_image(slug, name, role, image_url)
            
            if template_data:
                templates_index[slug] = template_data
                logger.info(f"✓ Processed {name}: confidence={template_data.get('confidence', 0):.3f}")
            else:
                logger.warning(f"✗ Failed to process {name}")
        
        # Save to cache
        self._save_templates_cache(templates_index)
        
        logger.info(f"Built templates index with {len(templates_index)} heroes")
        return templates_index
    
    def _process_hero_image(self, slug: str, name: str, role: str, image_url: str) -> Optional[Dict[str, Any]]:
        """
        Process hero image and extract template features.
        
        Args:
            slug: Hero slug (e.g., 'kagura')
            name: Hero name (e.g., 'Kagura')
            role: Hero role (e.g., 'mage')
            image_url: URL to hero image
            
        Returns:
            Template data dictionary or None if processing failed
        """
        try:
            # Download image
            image_data = self._download_image(image_url, slug)
            if image_data is None:
                return None
            
            # Preprocess image
            processed_img = self._preprocess_hero_image(image_data)
            
            # Extract features
            features = self._extract_template_features(processed_img)
            
            return {
                'slug': slug,
                'name': name,
                'role': role,
                'image_url': image_url,
                'confidence': 0.8,  # Base confidence for template
                **features
            }
            
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            return None
    
    def _download_image(self, image_url: str, slug: str) -> Optional[np.ndarray]:
        """Download hero image and return as numpy array."""
        try:
            # Check if image is already cached
            cached_path = self.images_cache_dir / f"{slug}.png"
            if cached_path.exists():
                img = Image.open(cached_path)
                return np.array(img)
            
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Save to cache
            with open(cached_path, 'wb') as f:
                f.write(response.content)
            
            # Load and return
            img = Image.open(cached_path)
            return np.array(img)
            
        except Exception as e:
            logger.error(f"Failed to download image for {slug}: {e}")
            return None
    
    def _preprocess_hero_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess hero image for template matching.
        
        Args:
            image: Input image (RGB format)
            
        Returns:
            Preprocessed image (128x128 RGB)
        """
        # Convert to PIL Image for processing
        if len(image.shape) == 3 and image.shape[2] == 3:
            pil_img = Image.fromarray(image)
        else:
            pil_img = image
        
        # Resize to 128x128
        pil_img = pil_img.resize((128, 128), Image.Resampling.LANCZOS)
        
        # Convert back to numpy array
        img_array = np.array(pil_img)
        
        # Light denoising
        img_array = cv2.bilateralFilter(img_array, 9, 75, 75)
        
        # Histogram equalization
        img_array = exposure.equalize_hist(img_array)
        img_array = (img_array * 255).astype(np.uint8)
        
        return img_array
    
    def _extract_template_features(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract template features from preprocessed image.
        
        Args:
            image: Preprocessed image (128x128 RGB)
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        try:
            # Perceptual hash
            pil_img = Image.fromarray(image)
            features['phash'] = str(imagehash.phash(pil_img))
            
            # Color histogram (HSV 16x4x4)
            hsv_img = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
            hist = cv2.calcHist([hsv_img], [0, 1, 2], None, [16, 4, 4], [0, 180, 0, 256, 0, 256])
            features['histogram'] = hist.flatten().tolist()
            
            # ORB keypoints and descriptors
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            orb = cv2.ORB_create(nfeatures=100)
            keypoints, descriptors = orb.detectAndCompute(gray, None)
            
            features['orb_keypoints'] = len(keypoints)
            features['orb_descriptors'] = descriptors.tolist() if descriptors is not None else []
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Return default features
            features = {
                'phash': '0000000000000000',
                'histogram': [0.0] * (16 * 4 * 4),
                'orb_keypoints': 0,
                'orb_descriptors': []
            }
        
        return features
    
    def _save_templates_cache(self, templates_index: Dict[str, Any]) -> None:
        """Save templates index to cache file."""
        try:
            with open(self.templates_cache_path, 'wb') as f:
                pickle.dump(templates_index, f)
            logger.info(f"Saved templates cache to {self.templates_cache_path}")
        except Exception as e:
            logger.error(f"Failed to save templates cache: {e}")
    
    def load_templates_cache(self) -> Optional[Dict[str, Any]]:
        """Load templates index from cache file."""
        try:
            if self.templates_cache_path.exists():
                with open(self.templates_cache_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load templates cache: {e}")
        return None


def main():
    """Main function to build templates index."""
    import argparse
    
    # Get default path from configuration if available
    default_heroes_path = 'data/heroes_cleaned.json'  # fallback
    if CONFIG_AVAILABLE:
        try:
            default_heroes_path = get_heroes_json_path()
        except Exception:
            pass
    
    parser = argparse.ArgumentParser(description='Build hero templates index')
    parser.add_argument('--heroes-data', default=default_heroes_path,
                       help='Path to heroes_cleaned.json')
    parser.add_argument('--cache-dir', default='backend/ocr/cache',
                       help='Cache directory')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Build templates
    builder = TemplatesBuilder(args.heroes_data, args.cache_dir)
    templates_index = builder.build_templates_index()
    
    print(f"✓ Built templates index with {len(templates_index)} heroes")
    print(f"✓ Cache saved to {builder.templates_cache_path}")


if __name__ == '__main__':
    main()
