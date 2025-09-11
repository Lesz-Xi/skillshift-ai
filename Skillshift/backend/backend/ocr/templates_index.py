#!/usr/bin/env python3
"""
Templates Index for Local Hero Template Loading

Loads hero templates from local assets directory and computes
phash and HSV color histogram features for template matching.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image
import imagehash
import cv2

# Configure logging
logger = logging.getLogger(__name__)

class TemplatesIndex:
    """Manages local hero templates with computed features"""
    
    def __init__(self, assets_dir: str = "backend/ocr/assets/heroes"):
        self.assets_dir = Path(assets_dir)
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all PNG templates from assets directory"""
        if not self.assets_dir.exists():
            logger.warning(f"Assets directory not found: {self.assets_dir}")
            return
        
        png_files = list(self.assets_dir.glob("*.png"))
        logger.info(f"Found {len(png_files)} template files")
        
        for png_file in png_files:
            slug = png_file.stem  # filename without extension
            try:
                template_data = self._process_template(png_file, slug)
                if template_data:
                    self.templates[slug] = template_data
                    logger.info(f"Loaded template: {slug}")
            except Exception as e:
                logger.error(f"Failed to process template {png_file}: {e}")
    
    def _process_template(self, template_path: Path, slug: str) -> Optional[Dict[str, Any]]:
        """
        Process a single template file and compute features
        
        Args:
            template_path: Path to template PNG file
            slug: Hero slug (filename without extension)
            
        Returns:
            Template data dictionary or None if processing failed
        """
        try:
            # Load image
            img = Image.open(template_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 96x96 for consistency
            img = img.resize((96, 96), Image.Resampling.LANCZOS)
            
            # Compute phash
            phash = str(imagehash.phash(img))
            
            # Compute HSV color histogram (16x4x4 bins)
            img_array = np.array(img)
            hsv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            hist = cv2.calcHist([hsv_img], [0, 1, 2], None, [16, 4, 4], [0, 180, 0, 256, 0, 256])
            
            # L1 normalize histogram
            hist = hist.flatten()
            hist = hist / (np.sum(hist) + 1e-8)  # Add small epsilon to avoid division by zero
            
            return {
                'slug': slug,
                'phash': phash,
                'histogram': hist.tolist(),
                'template_path': str(template_path)
            }
            
        except Exception as e:
            logger.error(f"Error processing template {template_path}: {e}")
            return None
    
    def get_template(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get template data by slug"""
        return self.templates.get(slug)
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded templates"""
        return self.templates.copy()
    
    def get_template_slugs(self) -> list:
        """Get list of all template slugs"""
        return list(self.templates.keys())


# Module-level singleton instance
_templates_index = None

def get_templates_index() -> TemplatesIndex:
    """Get singleton templates index instance"""
    global _templates_index
    if _templates_index is None:
        _templates_index = TemplatesIndex()
    return _templates_index

def get_template(slug: str) -> Optional[Dict[str, Any]]:
    """Get template by slug - convenience function"""
    index = get_templates_index()
    return index.get_template(slug)

def get_all_templates() -> Dict[str, Dict[str, Any]]:
    """Get all templates - convenience function"""
    index = get_templates_index()
    return index.get_all_templates()


if __name__ == "__main__":
    # Test the templates index
    index = get_templates_index()
    print(f"Loaded {len(index.get_all_templates())} templates")
    for slug, template in index.get_all_templates().items():
        print(f"  {slug}: phash={template['phash'][:8]}...")
