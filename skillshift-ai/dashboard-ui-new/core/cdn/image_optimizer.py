"""
Image Optimization Service for MLBB Coach AI
Advanced image processing, compression, and CDN integration
"""

import asyncio
import hashlib
import logging
import os
import tempfile
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import boto3
from botocore.exceptions import ClientError
from PIL import Image, ImageOps
import cv2
import numpy as np
import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    AVIF = "avif"


class OptimizationLevel(Enum):
    """Image optimization levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class ImageVariant:
    """Image variant configuration."""
    width: int
    height: int
    quality: int = 85
    format: ImageFormat = ImageFormat.WEBP
    optimization: OptimizationLevel = OptimizationLevel.MEDIUM


@dataclass
class OptimizationResult:
    """Image optimization result."""
    original_size: int
    optimized_size: int
    compression_ratio: float
    variants: Dict[str, str]  # variant_name -> cdn_url
    processing_time: float
    success: bool
    error: Optional[str] = None


class ImageOptimizer:
    """Advanced image optimization service with CDN integration."""
    
    def __init__(
        self,
        aws_access_key: str = None,
        aws_secret_key: str = None,
        aws_region: str = "us-east-1",
        s3_bucket: str = "mlbb-coach-ai-images",
        cloudfront_domain: str = "images.mlbb-coach-ai.com"
    ):
        """Initialize image optimizer."""
        self.aws_access_key = aws_access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = aws_secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket
        self.cloudfront_domain = cloudfront_domain
        
        # Initialize AWS clients
        self.s3_client = None
        self.cloudfront_client = None
        
        # Predefined image variants for different use cases
        self.variants = {
            "thumbnail": ImageVariant(150, 150, 80, ImageFormat.WEBP),
            "small": ImageVariant(300, 300, 85, ImageFormat.WEBP),
            "medium": ImageVariant(600, 600, 85, ImageFormat.WEBP),
            "large": ImageVariant(1200, 1200, 90, ImageFormat.WEBP),
            "hero_portrait": ImageVariant(400, 600, 90, ImageFormat.WEBP),
            "hero_icon": ImageVariant(64, 64, 85, ImageFormat.PNG),
            "screenshot": ImageVariant(1920, 1080, 85, ImageFormat.JPEG),
            "screenshot_thumb": ImageVariant(320, 180, 80, ImageFormat.WEBP),
        }
        
        # Quality settings by optimization level
        self.quality_settings = {
            OptimizationLevel.LOW: {"jpeg": 95, "webp": 90, "png": 9},
            OptimizationLevel.MEDIUM: {"jpeg": 85, "webp": 80, "png": 6},
            OptimizationLevel.HIGH: {"jpeg": 75, "webp": 70, "png": 4},
            OptimizationLevel.ULTRA: {"jpeg": 65, "webp": 60, "png": 2},
        }
        
    async def initialize(self):
        """Initialize AWS clients and verify access."""
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            # Initialize CloudFront client
            self.cloudfront_client = boto3.client(
                'cloudfront',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            # Test S3 access
            await self._verify_s3_access()
            
            logger.info("Image optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize image optimizer: {e}")
            raise
    
    async def _verify_s3_access(self):
        """Verify S3 bucket access."""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            logger.info(f"S3 bucket {self.s3_bucket} access verified")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"S3 bucket {self.s3_bucket} not found, creating...")
                await self._create_s3_bucket()
            else:
                raise
    
    async def _create_s3_bucket(self):
        """Create S3 bucket with proper configuration."""
        try:
            # Create bucket
            if self.aws_region != 'us-east-1':
                self.s3_client.create_bucket(
                    Bucket=self.s3_bucket,
                    CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                )
            else:
                self.s3_client.create_bucket(Bucket=self.s3_bucket)
            
            # Configure bucket for public read access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.s3_bucket}/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.s3_bucket,
                Policy=str(bucket_policy)
            )
            
            # Enable CORS
            cors_configuration = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'HEAD'],
                        'AllowedOrigins': ['*'],
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3600
                    }
                ]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=self.s3_bucket,
                CORSConfiguration=cors_configuration
            )
            
            logger.info(f"S3 bucket {self.s3_bucket} created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create S3 bucket: {e}")
            raise
    
    async def optimize_image(
        self,
        image_data: Union[bytes, str],
        image_name: str,
        variants: List[str] = None,
        upload_to_cdn: bool = True
    ) -> OptimizationResult:
        """Optimize image and create multiple variants."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Load image data
            if isinstance(image_data, str):
                # Assume it's a file path
                async with aiofiles.open(image_data, 'rb') as f:
                    image_bytes = await f.read()
            else:
                image_bytes = image_data
            
            original_size = len(image_bytes)
            
            # Load image with PIL
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                # Preserve transparency for PNG
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert('RGB')
            
            # Determine which variants to create
            variant_names = variants or ["thumbnail", "small", "medium", "large"]
            variant_results = {}
            total_optimized_size = 0
            
            # Process each variant
            for variant_name in variant_names:
                if variant_name not in self.variants:
                    logger.warning(f"Unknown variant: {variant_name}")
                    continue
                
                variant = self.variants[variant_name]
                optimized_data, size = await self._create_variant(image, variant)
                total_optimized_size += size
                
                if upload_to_cdn:
                    # Upload to S3/CDN
                    cdn_url = await self._upload_to_cdn(
                        optimized_data, 
                        f"{image_name}_{variant_name}.{variant.format.value}"
                    )
                    variant_results[variant_name] = cdn_url
                else:
                    # Save locally (for testing)
                    local_path = f"/tmp/{image_name}_{variant_name}.{variant.format.value}"
                    with open(local_path, 'wb') as f:
                        f.write(optimized_data)
                    variant_results[variant_name] = local_path
            
            processing_time = asyncio.get_event_loop().time() - start_time
            compression_ratio = (original_size - total_optimized_size) / original_size
            
            return OptimizationResult(
                original_size=original_size,
                optimized_size=total_optimized_size,
                compression_ratio=compression_ratio,
                variants=variant_results,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Image optimization failed: {e}")
            
            return OptimizationResult(
                original_size=len(image_bytes) if 'image_bytes' in locals() else 0,
                optimized_size=0,
                compression_ratio=0.0,
                variants={},
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    async def _create_variant(self, image: Image.Image, variant: ImageVariant) -> Tuple[bytes, int]:
        """Create optimized image variant."""
        # Resize image
        resized = ImageOps.fit(
            image, 
            (variant.width, variant.height), 
            Image.Resampling.LANCZOS
        )
        
        # Apply additional optimizations based on format
        if variant.format == ImageFormat.JPEG:
            # JPEG optimizations
            resized = resized.convert('RGB')
            
        elif variant.format == ImageFormat.PNG:
            # PNG optimizations - reduce colors if possible
            if resized.mode == 'RGB':
                # Try to quantize to reduce file size
                try:
                    resized = resized.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
                except:
                    pass
        
        # Save to bytes
        output = BytesIO()
        
        if variant.format == ImageFormat.WEBP:
            resized.save(
                output, 
                format='WEBP', 
                quality=variant.quality,
                optimize=True,
                method=6  # Best compression
            )
        elif variant.format == ImageFormat.JPEG:
            resized.save(
                output, 
                format='JPEG', 
                quality=variant.quality,
                optimize=True,
                progressive=True
            )
        elif variant.format == ImageFormat.PNG:
            resized.save(
                output, 
                format='PNG', 
                optimize=True,
                compress_level=6
            )
        
        output.seek(0)
        data = output.getvalue()
        return data, len(data)
    
    async def _upload_to_cdn(self, image_data: bytes, filename: str) -> str:
        """Upload image to S3/CDN."""
        try:
            # Generate S3 key
            file_hash = hashlib.md5(image_data).hexdigest()[:8]
            s3_key = f"optimized/{file_hash}/{filename}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=image_data,
                ContentType=self._get_content_type(filename),
                CacheControl='max-age=31536000',  # 1 year cache
                Metadata={
                    'optimized': 'true',
                    'original-size': str(len(image_data))
                }
            )
            
            # Return CDN URL
            cdn_url = f"https://{self.cloudfront_domain}/{s3_key}"
            logger.debug(f"Image uploaded to CDN: {cdn_url}")
            
            return cdn_url
            
        except Exception as e:
            logger.error(f"Failed to upload image to CDN: {e}")
            raise
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type for image file."""
        extension = filename.lower().split('.')[-1]
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'avif': 'image/avif'
        }
        return content_types.get(extension, 'image/jpeg')
    
    async def optimize_screenshot(
        self, 
        screenshot_data: bytes, 
        screenshot_name: str
    ) -> OptimizationResult:
        """Optimize game screenshot with specific settings."""
        # Use screenshot-specific variants
        variants = ["screenshot", "screenshot_thumb", "medium", "small"]
        return await self.optimize_image(
            screenshot_data, 
            screenshot_name, 
            variants
        )
    
    async def optimize_hero_image(
        self, 
        hero_image_data: bytes, 
        hero_name: str
    ) -> OptimizationResult:
        """Optimize hero image with specific settings."""
        # Use hero-specific variants
        variants = ["hero_portrait", "hero_icon", "medium", "thumbnail"]
        return await self.optimize_image(
            hero_image_data, 
            f"hero_{hero_name.lower()}", 
            variants
        )
    
    async def invalidate_cdn_cache(self, paths: List[str]) -> bool:
        """Invalidate CloudFront cache for specific paths."""
        try:
            # Create invalidation
            response = self.cloudfront_client.create_invalidation(
                DistributionId=self._get_distribution_id(),
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f"mlbb-invalidation-{int(asyncio.get_event_loop().time())}"
                }
            )
            
            invalidation_id = response['Invalidation']['Id']
            logger.info(f"CDN cache invalidation created: {invalidation_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate CDN cache: {e}")
            return False
    
    def _get_distribution_id(self) -> str:
        """Get CloudFront distribution ID for the domain."""
        # This would typically be configured or looked up
        # For now, return a placeholder
        return "E1234567890123"
    
    async def get_optimization_stats(self) -> Dict[str, any]:
        """Get image optimization statistics."""
        try:
            # Get S3 bucket statistics
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix="optimized/"
            )
            
            total_objects = response.get('KeyCount', 0)
            total_size = sum(obj.get('Size', 0) for obj in response.get('Contents', []))
            
            return {
                "total_optimized_images": total_objects,
                "total_storage_size": total_size,
                "average_image_size": total_size / max(total_objects, 1),
                "cdn_domain": self.cloudfront_domain,
                "s3_bucket": self.s3_bucket,
                "supported_formats": [fmt.value for fmt in ImageFormat],
                "available_variants": list(self.variants.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimization stats: {e}")
            return {"error": str(e)}


# Global image optimizer instance
_image_optimizer: Optional[ImageOptimizer] = None


async def get_image_optimizer() -> ImageOptimizer:
    """Get global image optimizer instance."""
    global _image_optimizer
    
    if _image_optimizer is None:
        _image_optimizer = ImageOptimizer()
        await _image_optimizer.initialize()
    
    return _image_optimizer


# Convenience functions
async def optimize_image(
    image_data: Union[bytes, str],
    image_name: str,
    variants: List[str] = None
) -> OptimizationResult:
    """Optimize image using global optimizer."""
    optimizer = await get_image_optimizer()
    return await optimizer.optimize_image(image_data, image_name, variants)


async def optimize_screenshot(screenshot_data: bytes, screenshot_name: str) -> OptimizationResult:
    """Optimize screenshot using global optimizer."""
    optimizer = await get_image_optimizer()
    return await optimizer.optimize_screenshot(screenshot_data, screenshot_name)


async def optimize_hero_image(hero_image_data: bytes, hero_name: str) -> OptimizationResult:
    """Optimize hero image using global optimizer."""
    optimizer = await get_image_optimizer()
    return await optimizer.optimize_hero_image(hero_image_data, hero_name)
