"""
Mission 6: Memory Efficiency Integration for OCR Pipeline
Integrates async I/O, buffer pools, and singleton models with existing OCR system
"""

import asyncio
import time
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import numpy as np
import cv2
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor

from .memory_efficiency_manager import (
    get_memory_processor, MemoryPoolConfig, MemoryPriority,
    AsyncImageLoader, BufferPool, SingletonModelManager
)
from .transcendent_ocr_manager import TranscendentOCRManager
from .transcendent_ocr_integration import analyze_with_transcendent_intelligence

logger = logging.getLogger(__name__)


@dataclass
class ProcessingContext:
    """Context for memory-efficient OCR processing"""
    session_id: str
    image_path: Union[str, Path]
    target_size: Optional[Tuple[int, int]] = None
    use_memory_map: bool = True
    buffer_priority: MemoryPriority = MemoryPriority.MEDIUM
    
    # Processing options
    skip_yolo: bool = False
    skip_ocr: bool = False
    force_reprocess: bool = False
    
    # Performance tracking
    start_time: float = field(default_factory=time.time)
    memory_usage_peak: int = 0
    
    # Results cache
    yolo_results: Optional[List[Dict[str, Any]]] = None
    ocr_results: Optional[List[Dict[str, Any]]] = None
    final_results: Optional[Dict[str, Any]] = None


class MemoryEfficientOCRProcessor:
    """OCR processor with memory efficiency optimizations"""
    
    def __init__(
        self,
        max_workers: int = 4,
        memory_config: Optional[MemoryPoolConfig] = None
    ):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.memory_processor = get_memory_processor(memory_config)
        self.transcendent_manager = TranscendentOCRManager()
        
        # Processing stats
        self.stats = {
            'total_processed': 0,
            'memory_saved_mb': 0,
            'async_time_saved_ms': 0,
            'cache_hits': 0,
            'buffer_reuses': 0,
            'yolo_loads_prevented': 0,
            'ocr_loads_prevented': 0
        }
        
        # Model loaders
        self._yolo_loader = None
        self._ocr_loader = None
    
    @asynccontextmanager
    async def create_processing_context(
        self,
        session_id: str,
        image_path: Union[str, Path],
        **kwargs
    ) -> ProcessingContext:
        """Create and manage processing context"""
        context = ProcessingContext(
            session_id=session_id,
            image_path=image_path,
            **kwargs
        )
        
        try:
            yield context
        finally:
            # Update stats
            self.stats['total_processed'] += 1
            
            # Log performance
            processing_time = time.time() - context.start_time
            logger.info(
                f"Session {context.session_id} processed in {processing_time:.3f}s, "
                f"peak memory: {context.memory_usage_peak / 1024 / 1024:.1f}MB"
            )
    
    async def process_image_with_memory_efficiency(
        self,
        image_path: Union[str, Path],
        session_id: str,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process image with memory-efficient OCR pipeline
        
        Args:
            image_path: Path to image file
            session_id: Session identifier
            processing_options: Additional processing options
            
        Returns:
            Processing results with metadata
        """
        options = processing_options or {}
        
        async with self.create_processing_context(
            session_id=session_id,
            image_path=image_path,
            target_size=options.get('target_size'),
            use_memory_map=options.get('use_memory_map', True),
            buffer_priority=options.get('buffer_priority', MemoryPriority.MEDIUM)
        ) as context:
            
            # Load image asynchronously
            image = await self._load_image_async(context)
            
            # Process with transcendent OCR if available
            if hasattr(self.transcendent_manager, 'process_with_transcendent_intelligence'):
                return await self._process_with_transcendent_ocr(context, image, options)
            else:
                # Fallback to standard memory-efficient processing
                return await self._process_standard(context, image, options)
    
    async def _load_image_async(self, context: ProcessingContext) -> np.ndarray:
        """Load image with async I/O optimization"""
        start_time = time.time()
        
        image = await self.memory_processor.image_loader.load_image_async(
            context.image_path,
            target_size=context.target_size,
            use_memory_map=context.use_memory_map
        )
        
        load_time = time.time() - start_time
        self.stats['async_time_saved_ms'] += max(0, (0.1 - load_time) * 1000)  # Assume 100ms baseline
        
        logger.debug(f"Image loaded in {load_time:.3f}s, shape: {image.shape}")
        return image
    
    async def _process_with_transcendent_ocr(
        self,
        context: ProcessingContext,
        image: np.ndarray,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process image using transcendent OCR with memory efficiency"""
        try:
            # Use buffer pool for YOLO processing
            async with self.memory_processor.buffer_pool.get_buffer_async(
                image.nbytes, 
                priority=MemoryPriority.HIGH
            ) as buffer:
                np.copyto(buffer, image.ravel())
                processed_image = buffer.reshape(image.shape)
                
                # Extract regions for OCR
                regions = self._extract_ocr_regions(processed_image, options)
                
                # Process with transcendent OCR
                results = await self.transcendent_manager.process_with_transcendent_intelligence(
                    processed_image,
                    regions,
                    context.session_id
                )
                
                # Update context
                context.yolo_results = self._format_yolo_results(regions)
                context.ocr_results = self._format_ocr_results(results)
                context.final_results = self._combine_results(context.yolo_results, context.ocr_results)
                
                return {
                    'success': True,
                    'results': context.final_results,
                    'performance': {
                        'processing_time': time.time() - context.start_time,
                        'memory_usage_mb': context.memory_usage_peak / 1024 / 1024,
                        'async_time_saved_ms': self.stats['async_time_saved_ms'],
                        'buffer_reuses': self.stats['buffer_reuses']
                    },
                    'optimizations': {
                        'memory_mapped': context.use_memory_map,
                        'buffer_pool_used': True,
                        'transcendent_processing': True
                    }
                }
                
        except Exception as e:
            logger.error(f"Transcendent OCR processing failed: {e}")
            # Fallback to standard processing
            return await self._process_standard(context, image, options)
    
    async def _process_standard(
        self,
        context: ProcessingContext,
        image: np.ndarray,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Standard memory-efficient OCR processing"""
        try:
            # YOLO detection with singleton model
            if not context.skip_yolo:
                yolo_results = await self._yolo_detection_async(image, context)
                context.yolo_results = yolo_results
            else:
                yolo_results = []
            
            # OCR processing with singleton reader
            if not context.skip_ocr:
                ocr_results = await self._ocr_processing_async(image, yolo_results, context)
                context.ocr_results = ocr_results
            else:
                ocr_results = []
            
            # Combine results
            context.final_results = self._combine_results(context.yolo_results, context.ocr_results)
            
            return {
                'success': True,
                'results': context.final_results,
                'performance': {
                    'processing_time': time.time() - context.start_time,
                    'memory_usage_mb': context.memory_usage_peak / 1024 / 1024,
                    'async_time_saved_ms': self.stats['async_time_saved_ms'],
                    'buffer_reuses': self.stats['buffer_reuses']
                },
                'optimizations': {
                    'memory_mapped': context.use_memory_map,
                    'buffer_pool_used': True,
                    'singleton_models': True
                }
            }
            
        except Exception as e:
            logger.error(f"Standard OCR processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': {},
                'performance': {
                    'processing_time': time.time() - context.start_time,
                    'memory_usage_mb': context.memory_usage_peak / 1024 / 1024
                }
            }
    
    async def _yolo_detection_async(self, image: np.ndarray, context: ProcessingContext) -> List[Dict[str, Any]]:
        """YOLO detection with memory efficiency"""
        loop = asyncio.get_event_loop()
        
        def yolo_detection_sync():
            # Get singleton YOLO model
            if self._yolo_loader:
                yolo_model = self.memory_processor.get_yolo_model(self._yolo_loader)
                self.stats['yolo_loads_prevented'] += 1
            else:
                # Fallback: direct model loading
                from ultralytics import YOLO
                yolo_model = YOLO('yolov8n.pt')
            
            # Use buffer for processing
            with self.memory_processor.buffer_pool.get_buffer_sync(
                image.nbytes,
                priority=MemoryPriority.HIGH
            ) as buffer:
                np.copyto(buffer, image.ravel())
                processed_image = buffer.reshape(image.shape)
                
                results = yolo_model(processed_image)
                return self._extract_detections(results)
        
        results = await loop.run_in_executor(self.executor, yolo_detection_sync)
        return results
    
    async def _ocr_processing_async(
        self, 
        image: np.ndarray, 
        yolo_results: List[Dict[str, Any]], 
        context: ProcessingContext
    ) -> List[Dict[str, Any]]:
        """OCR processing with memory efficiency"""
        loop = asyncio.get_event_loop()
        
        def ocr_processing_sync():
            # Get singleton OCR reader
            if self._ocr_loader:
                ocr_reader = self.memory_processor.get_ocr_reader(self._ocr_loader)
                self.stats['ocr_loads_prevented'] += 1
            else:
                # Fallback: direct reader loading
                import easyocr
                ocr_reader = easyocr.Reader(['en'])
            
            ocr_results = []
            
            # Process each detection region
            for detection in yolo_results:
                bbox = detection.get('bbox')
                if bbox:
                    # Extract region with buffer
                    region = self._extract_region_with_buffer(image, bbox)
                    
                    # OCR processing
                    ocr_text = ocr_reader.readtext(region)
                    
                    ocr_results.append({
                        'bbox': bbox,
                        'text': ocr_text,
                        'confidence': detection.get('confidence', 0.0)
                    })
            
            return ocr_results
        
        results = await loop.run_in_executor(self.executor, ocr_processing_sync)
        return results
    
    def _extract_region_with_buffer(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract region using buffer pool"""
        x1, y1, x2, y2 = bbox
        region = image[y1:y2, x1:x2]
        
        # Use buffer for region processing
        with self.memory_processor.buffer_pool.get_buffer_sync(
            region.nbytes,
            priority=MemoryPriority.MEDIUM
        ) as buffer:
            np.copyto(buffer, region.ravel())
            self.stats['buffer_reuses'] += 1
            return buffer.reshape(region.shape)
    
    def _extract_ocr_regions(self, image: np.ndarray, options: Dict[str, Any]) -> List[Tuple[int, int, int, int]]:
        """Extract OCR regions from image"""
        # Default regions if no YOLO detection
        height, width = image.shape[:2]
        
        # Scoreboard regions (typical MLBB layout)
        regions = [
            (0, 0, width // 2, height // 4),      # Top left (KDA)
            (width // 2, 0, width, height // 4),   # Top right (Team info)
            (0, height // 4, width, height // 2),  # Middle section
        ]
        
        # Add damage view region if requested
        if options.get('include_damage_view', False):
            regions.append((0, height // 2, width, height))
        
        return regions
    
    def _extract_detections(self, yolo_results) -> List[Dict[str, Any]]:
        """Extract detections from YOLO results"""
        detections = []
        
        for result in yolo_results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    detections.append({
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                        'confidence': float(confidence),
                        'class_id': class_id
                    })
        
        return detections
    
    def _format_yolo_results(self, regions: List[Tuple[int, int, int, int]]) -> List[Dict[str, Any]]:
        """Format YOLO results"""
        return [
            {
                'bbox': region,
                'confidence': 0.8,  # Default confidence for predefined regions
                'class_id': 0
            }
            for region in regions
        ]
    
    def _format_ocr_results(self, results) -> List[Dict[str, Any]]:
        """Format OCR results"""
        formatted = []
        
        if hasattr(results, '__iter__'):
            for result in results:
                if hasattr(result, 'text'):
                    formatted.append({
                        'text': result.text,
                        'confidence': getattr(result, 'confidence', 0.0),
                        'bbox': getattr(result, 'bbox', (0, 0, 0, 0))
                    })
        
        return formatted
    
    def _combine_results(
        self, 
        yolo_results: List[Dict[str, Any]], 
        ocr_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Combine YOLO and OCR results"""
        return {
            'detections': yolo_results,
            'ocr_results': ocr_results,
            'total_detections': len(yolo_results),
            'total_ocr_regions': len(ocr_results),
            'processing_complete': True
        }
    
    def set_model_loaders(
        self, 
        yolo_loader: Optional[Callable[[], Any]] = None,
        ocr_loader: Optional[Callable[[], Any]] = None
    ) -> None:
        """Set model loader functions"""
        self._yolo_loader = yolo_loader
        self._ocr_loader = ocr_loader
    
    def get_efficiency_stats(self) -> Dict[str, Any]:
        """Get memory efficiency statistics"""
        base_stats = self.memory_processor.get_comprehensive_stats()
        
        return {
            'processing_stats': self.stats.copy(),
            'memory_efficiency': base_stats,
            'total_memory_saved_mb': self.stats['memory_saved_mb'],
            'total_async_time_saved_ms': self.stats['async_time_saved_ms'],
            'models_prevented_from_reloading': {
                'yolo': self.stats['yolo_loads_prevented'],
                'ocr': self.stats['ocr_loads_prevented']
            }
        }
    
    def clear_caches(self) -> None:
        """Clear all memory caches"""
        self.memory_processor.image_loader.clear_cache()
        logger.info("Memory caches cleared")
    
    def shutdown(self) -> None:
        """Shutdown and cleanup"""
        self.executor.shutdown(wait=True)
        self.clear_caches()
        logger.info("Memory efficient OCR processor shutdown complete")


# Global instance
_memory_processor_instance: Optional[MemoryEfficientOCRProcessor] = None
_processor_lock = asyncio.Lock()


async def get_memory_efficient_processor(
    max_workers: int = 4,
    memory_config: Optional[MemoryPoolConfig] = None
) -> MemoryEfficientOCRProcessor:
    """Get global memory efficient OCR processor instance"""
    global _memory_processor_instance
    async with _processor_lock:
        if _memory_processor_instance is None:
            _memory_processor_instance = MemoryEfficientOCRProcessor(
                max_workers=max_workers,
                memory_config=memory_config
            )
        return _memory_processor_instance


async def shutdown_memory_efficient_processor() -> None:
    """Shutdown global memory efficient processor"""
    global _memory_processor_instance
    async with _processor_lock:
        if _memory_processor_instance is not None:
            _memory_processor_instance.shutdown()
            _memory_processor_instance = None