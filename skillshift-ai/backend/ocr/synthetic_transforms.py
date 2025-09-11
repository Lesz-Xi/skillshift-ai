"""
OCR Mission 5: Synthetic Transform Fixtures

This module creates synthetic transforms for testing layout robustness
across aspect ratios, resolutions, device filters, and hero skin changes.

Target: Generate test fixtures for comprehensive robustness validation.
"""

import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import random
import json

logger = logging.getLogger(__name__)


class SyntheticTransformGenerator:
    """
    Generator for synthetic transforms to test OCR Mission 5 robustness.
    
    Creates transforms for:
    - Layout robustness: aspect ratios (16:9, 19.5:9, 21:9), resolutions (720p–4K), letterboxing, crops
    - Filter tolerance: brightness/contrast shifts, slight blur, JPEG noise
    - Hero variants: skin variants and partial occlusions
    """
    
    def __init__(self):
        # Transform parameters for OCR Mission 5
        self.aspect_ratios = [
            (16, 9),    # Standard
            (19, 9),    # 19.5:9 (modern phones)
            (21, 9),    # 21:9 (ultrawide)
            (4, 3),     # Classic
            (3, 2)      # Alternative
        ]
        
        self.resolutions = [
            (1280, 720),   # 720p
            (1920, 1080),  # 1080p
            (2560, 1440),  # 1440p
            (3840, 2160),  # 4K
            (1600, 900),   # 900p
            (1366, 768)    # 768p
        ]
        
        self.blur_levels = [0.0, 0.6, 1.2, 2.0]
        self.jpeg_qualities = [55, 70, 85, 95]
        self.brightness_shifts = [-15, -10, -5, 0, 5, 10, 15]
        self.contrast_shifts = [-10, -5, 0, 5, 10]
        self.scale_factors = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5]
        self.padding_percentages = [0.0, 0.01, 0.03, 0.05, 0.06]
    
    def generate_layout_transforms(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Generate layout transforms for aspect ratio and resolution testing.
        
        Args:
            image: Input image
            
        Returns:
            List of transform configurations
        """
        transforms = []
        
        # Generate aspect ratio transforms
        for aspect_w, aspect_h in self.aspect_ratios:
            for resolution in self.resolutions:
                # Calculate target size maintaining aspect ratio
                target_w, target_h = resolution
                
                # Apply aspect ratio constraint
                if target_w / target_h > aspect_w / aspect_h:
                    # Image is too wide, crop width
                    new_w = int(target_h * aspect_w / aspect_h)
                    crop_x = (target_w - new_w) // 2
                    transform = {
                        "type": "aspect_ratio_crop",
                        "aspect_ratio": f"{aspect_w}:{aspect_h}",
                        "resolution": f"{target_w}x{target_h}",
                        "crop_x": crop_x,
                        "crop_w": new_w,
                        "target_size": (new_w, target_h)
                    }
                else:
                    # Image is too tall, crop height
                    new_h = int(target_w * aspect_h / aspect_w)
                    crop_y = (target_h - new_h) // 2
                    transform = {
                        "type": "aspect_ratio_crop",
                        "aspect_ratio": f"{aspect_w}:{aspect_h}",
                        "resolution": f"{target_w}x{target_h}",
                        "crop_y": crop_y,
                        "crop_h": new_h,
                        "target_size": (target_w, new_h)
                    }
                
                transforms.append(transform)
        
        return transforms
    
    def generate_filter_transforms(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Generate filter transforms for brightness, contrast, blur, and JPEG noise.
        
        Args:
            image: Input image
            
        Returns:
            List of filter transform configurations
        """
        transforms = []
        
        # Brightness and contrast combinations
        for brightness in self.brightness_shifts:
            for contrast in self.contrast_shifts:
                if brightness == 0 and contrast == 0:
                    continue  # Skip no-op transform
                
                transform = {
                    "type": "brightness_contrast",
                    "brightness": brightness,
                    "contrast": contrast,
                    "description": f"brightness_{brightness:+d}_contrast_{contrast:+d}"
                }
                transforms.append(transform)
        
        # Blur transforms
        for blur_sigma in self.blur_levels:
            if blur_sigma > 0:
                transform = {
                    "type": "blur",
                    "sigma": blur_sigma,
                    "description": f"blur_sigma_{blur_sigma}"
                }
                transforms.append(transform)
        
        # JPEG compression transforms
        for quality in self.jpeg_qualities:
            if quality < 95:  # Skip lossless
                transform = {
                    "type": "jpeg_compression",
                    "quality": quality,
                    "description": f"jpeg_quality_{quality}"
                }
                transforms.append(transform)
        
        return transforms
    
    def generate_scale_pad_transforms(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Generate scale and padding transforms.
        
        Args:
            image: Input image
            
        Returns:
            List of scale/pad transform configurations
        """
        transforms = []
        
        # Scale transforms
        for scale in self.scale_factors:
            if scale != 1.0:
                transform = {
                    "type": "scale",
                    "scale_factor": scale,
                    "description": f"scale_{scale:.1f}x"
                }
                transforms.append(transform)
        
        # Padding transforms
        for pad_pct in self.padding_percentages:
            if pad_pct > 0:
                transform = {
                    "type": "padding",
                    "padding_percentage": pad_pct,
                    "description": f"pad_{pad_pct:.1%}"
                }
                transforms.append(transform)
        
        return transforms
    
    def apply_transform(self, image: np.ndarray, transform_config: Dict[str, Any]) -> np.ndarray:
        """
        Apply a synthetic transform to an image.
        
        Args:
            image: Input image
            transform_config: Transform configuration
            
        Returns:
            Transformed image
        """
        try:
            transform_type = transform_config["type"]
            
            if transform_type == "aspect_ratio_crop":
                return self._apply_aspect_ratio_crop(image, transform_config)
            elif transform_type == "brightness_contrast":
                return self._apply_brightness_contrast(image, transform_config)
            elif transform_type == "blur":
                return self._apply_blur(image, transform_config)
            elif transform_type == "jpeg_compression":
                return self._apply_jpeg_compression(image, transform_config)
            elif transform_type == "scale":
                return self._apply_scale(image, transform_config)
            elif transform_type == "padding":
                return self._apply_padding(image, transform_config)
            else:
                logger.warning(f"Unknown transform type: {transform_type}")
                return image
                
        except Exception as e:
            logger.error(f"Error applying transform {transform_config}: {e}")
            return image
    
    def _apply_aspect_ratio_crop(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Apply aspect ratio cropping."""
        try:
            h, w = image.shape[:2]
            target_w, target_h = config["target_size"]
            
            # Resize to target resolution first
            resized = cv2.resize(image, (target_w, target_h))
            
            # Apply cropping if needed
            if "crop_x" in config:
                crop_x = config["crop_x"]
                crop_w = config["crop_w"]
                return resized[:, crop_x:crop_x + crop_w]
            elif "crop_y" in config:
                crop_y = config["crop_y"]
                crop_h = config["crop_h"]
                return resized[crop_y:crop_y + crop_h, :]
            
            return resized
            
        except Exception as e:
            logger.error(f"Error applying aspect ratio crop: {e}")
            return image
    
    def _apply_brightness_contrast(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Apply brightness and contrast adjustments."""
        try:
            brightness = config["brightness"]
            contrast = config["contrast"]
            
            # Convert to float for calculations
            img_float = image.astype(np.float32)
            
            # Apply brightness (additive)
            img_float += brightness
            
            # Apply contrast (multiplicative)
            img_float *= (1.0 + contrast / 100.0)
            
            # Clip to valid range and convert back
            img_float = np.clip(img_float, 0, 255)
            return img_float.astype(np.uint8)
            
        except Exception as e:
            logger.error(f"Error applying brightness/contrast: {e}")
            return image
    
    def _apply_blur(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Apply Gaussian blur."""
        try:
            sigma = config["sigma"]
            kernel_size = int(2 * np.ceil(2 * sigma) + 1)  # Standard kernel size
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
            
        except Exception as e:
            logger.error(f"Error applying blur: {e}")
            return image
    
    def _apply_jpeg_compression(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Apply JPEG compression simulation."""
        try:
            quality = config["quality"]
            
            # Encode and decode to simulate JPEG compression
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, encoded_img = cv2.imencode('.jpg', image, encode_param)
            decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
            
            return decoded_img
            
        except Exception as e:
            logger.error(f"Error applying JPEG compression: {e}")
            return image
    
    def _apply_scale(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Apply scaling transform."""
        try:
            scale_factor = config["scale_factor"]
            h, w = image.shape[:2]
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            
            return cv2.resize(image, (new_w, new_h))
            
        except Exception as e:
            logger.error(f"Error applying scale: {e}")
            return image
    
    def _apply_padding(self, image: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Apply random padding transform."""
        try:
            pad_pct = config["padding_percentage"]
            h, w = image.shape[:2]
            
            # Calculate padding amounts
            pad_h = int(h * pad_pct)
            pad_w = int(w * pad_pct)
            
            # Random padding on each side
            pad_top = random.randint(0, pad_h)
            pad_bottom = pad_h - pad_top
            pad_left = random.randint(0, pad_w)
            pad_right = pad_w - pad_left
            
            # Apply padding with reflection
            return cv2.copyMakeBorder(
                image, pad_top, pad_bottom, pad_left, pad_right,
                cv2.BORDER_REFLECT_101
            )
            
        except Exception as e:
            logger.error(f"Error applying padding: {e}")
            return image
    
    def generate_transform_matrix(self, image: np.ndarray, max_transforms: int = 12) -> List[Dict[str, Any]]:
        """
        Generate a comprehensive transform matrix for testing.
        
        Args:
            image: Input image
            max_transforms: Maximum number of transforms to generate
            
        Returns:
            List of transform configurations
        """
        all_transforms = []
        
        # Layout transforms (aspect ratios and resolutions)
        layout_transforms = self.generate_layout_transforms(image)
        all_transforms.extend(layout_transforms[:3])  # Limit to 3 layout transforms
        
        # Filter transforms
        filter_transforms = self.generate_filter_transforms(image)
        all_transforms.extend(filter_transforms[:5])  # Limit to 5 filter transforms
        
        # Scale and padding transforms
        scale_pad_transforms = self.generate_scale_pad_transforms(image)
        all_transforms.extend(scale_pad_transforms[:4])  # Limit to 4 scale/pad transforms
        
        # Shuffle and limit to max_transforms
        random.shuffle(all_transforms)
        return all_transforms[:max_transforms]
    
    def create_test_fixtures(self, golden_images: List[str], output_dir: str) -> Dict[str, List[str]]:
        """
        Create test fixtures for all golden images with synthetic transforms.
        
        Args:
            golden_images: List of paths to golden test images
            output_dir: Output directory for fixtures
            
        Returns:
            Dictionary mapping original images to generated fixture paths
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            fixture_mapping = {}
            
            for image_path in golden_images:
                try:
                    # Load image
                    image = cv2.imread(image_path)
                    if image is None:
                        logger.warning(f"Could not load image: {image_path}")
                        continue
                    
                    # Generate transforms
                    transforms = self.generate_transform_matrix(image, max_transforms=12)
                    
                    # Create fixtures
                    image_name = Path(image_path).stem
                    fixture_paths = []
                    
                    for i, transform in enumerate(transforms):
                        # Apply transform
                        transformed_image = self.apply_transform(image, transform)
                        
                        # Save fixture
                        transform_desc = transform.get('description', f"transform_{i:02d}")
                        fixture_name = f"{image_name}_transform_{i:02d}_{transform_desc}.png"
                        fixture_path = output_path / fixture_name
                        cv2.imwrite(str(fixture_path), transformed_image)
                        fixture_paths.append(str(fixture_path))
                        
                        logger.debug(f"Created fixture: {fixture_path}")
                    
                    fixture_mapping[image_path] = fixture_paths
                    logger.info(f"Created {len(fixture_paths)} fixtures for {image_path}")
                    
                except Exception as e:
                    logger.error(f"Error creating fixtures for {image_path}: {e}")
                    continue
            
            # Save fixture mapping
            mapping_path = output_path / "fixture_mapping.json"
            with open(mapping_path, 'w') as f:
                json.dump(fixture_mapping, f, indent=2)
            
            logger.info(f"Created {sum(len(paths) for paths in fixture_mapping.values())} total fixtures")
            return fixture_mapping
            
        except Exception as e:
            logger.error(f"Error creating test fixtures: {e}")
            return {}


# Global instance
synthetic_transform_generator = SyntheticTransformGenerator()
