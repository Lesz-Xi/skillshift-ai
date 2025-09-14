"""
Mission 6: Streaming Image Processor for Large Images
Implements M6-20B - streaming processing to reduce memory footprint for large images
"""

import asyncio
import io
import math
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import AsyncGenerator, Generator, List, Optional, Tuple, Union
import numpy as np
import cv2
from PIL import Image
import logging
from pathlib import Path

from .memory_efficiency_manager import MemoryBuffer, BufferPool, MemoryPriority

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for streaming image processing"""
    chunk_size: int = 1024 * 1024  # 1MB chunks
    max_memory_per_chunk: int = 50 * 1024 * 1024  # 50MB per chunk
    overlap_pixels: int = 32  # Overlap between chunks for seamless processing
    parallel_chunks: int = 3  # Number of chunks to process in parallel
    enable_streaming_decode: bool = True
    prefer_quality_over_speed: bool = True


@dataclass
class ChunkInfo:
    """Information about an image chunk"""
    index: int
    x: int
    y: int
    width: int
    height: int
    total_chunks: int
    is_last: bool = False


class StreamingImageProcessor:
    """Processes large images in streaming chunks to minimize memory usage"""
    
    def __init__(
        self, 
        config: Optional[StreamingConfig] = None,
        buffer_pool: Optional[BufferPool] = None
    ):
        self.config = config or StreamingConfig()
        self.buffer_pool = buffer_pool
        self.executor = ThreadPoolExecutor(max_workers=self.config.parallel_chunks)
        self.stats = {
            'total_chunks_processed': 0,
            'memory_saved_mb': 0,
            'streaming_decodes': 0,
            'parallel_processing_time_saved': 0.0
        }
    
    async def process_large_image_streaming(
        self,
        image_path: Union[str, Path],
        processing_func: callable,
        max_dimension: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[Tuple[np.ndarray, ChunkInfo], None]:
        """
        Process large image in streaming chunks
        
        Args:
            image_path: Path to large image
            processing_func: Function to apply to each chunk
            max_dimension: Maximum dimension for chunking
            **kwargs: Additional arguments for processing function
            
        Yields:
            Tuple of (processed_chunk, chunk_info)
        """
        try:
            # Get image dimensions with minimal memory usage
            dimensions = await self._get_image_dimensions_async(image_path)
            width, height = dimensions
            
            # Apply dimension limit if specified
            if max_dimension:
                scale_factor = min(max_dimension / width, max_dimension / height)
                if scale_factor < 1.0:
                    width = int(width * scale_factor)
                    height = int(height * scale_factor)
            
            # Calculate optimal chunking strategy
            chunks = self._calculate_chunk_strategy(width, height)
            
            logger.info(
                f"🚀 Starting streaming processing: {len(chunks)} chunks for "
                f"{width}x{height} image (max {max_dimension or 'unlimited'}px)"
            )
            
            # Process chunks in parallel streams
            async for chunk_result in self._process_chunks_parallel(
                image_path, chunks, processing_func, **kwargs
            ):
                yield chunk_result
                
        except Exception as e:
            logger.error(f"❌ Streaming processing failed: {e}")
            raise
    
    async def _get_image_dimensions_async(self, image_path: Union[str, Path]) -> Tuple[int, int]:
        """Get image dimensions with minimal memory usage"""
        def get_dimensions_sync():
            with Image.open(image_path) as img:
                return img.size
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, get_dimensions_sync)
    
    def _calculate_chunk_strategy(self, width: int, height: int) -> List[ChunkInfo]:
        """Calculate optimal chunking strategy"""
        chunks = []
        
        # Calculate chunk size based on memory constraints
        max_pixels_per_chunk = (self.config.max_memory_per_chunk * 8) // 3  # 3 bytes per RGB pixel
        
        # Calculate chunk dimensions
        aspect_ratio = width / height
        
        if width > height:
            # Landscape: chunk horizontally
            chunk_width = min(width, int(math.sqrt(max_pixels_per_chunk * aspect_ratio)))
            chunk_height = min(height, int(max_pixels_per_chunk / chunk_width))
            
            num_horizontal_chunks = math.ceil(width / (chunk_width - self.config.overlap_pixels))
            num_vertical_chunks = math.ceil(height / (chunk_height - self.config.overlap_pixels))
        else:
            # Portrait: chunk vertically
            chunk_height = min(height, int(math.sqrt(max_pixels_per_chunk / aspect_ratio)))
            chunk_width = min(width, int(max_pixels_per_chunk / chunk_height))
            
            num_vertical_chunks = math.ceil(height / (chunk_height - self.config.overlap_pixels))
            num_horizontal_chunks = math.ceil(width / (chunk_width - self.config.overlap_pixels))
        
        # Create chunk information
        chunk_index = 0
        total_chunks = num_horizontal_chunks * num_vertical_chunks
        
        for v_idx in range(num_vertical_chunks):
            for h_idx in range(num_horizontal_chunks):
                # Calculate chunk position with overlap
                x = max(0, h_idx * (chunk_width - self.config.overlap_pixels))
                y = max(0, v_idx * (chunk_height - self.config.overlap_pixels))
                
                # Adjust for edge chunks
                chunk_w = min(chunk_width, width - x)
                chunk_h = min(chunk_height, height - y)
                
                chunks.append(ChunkInfo(
                    index=chunk_index,
                    x=x, y=y,
                    width=chunk_w,
                    height=chunk_h,
                    total_chunks=total_chunks,
                    is_last=(chunk_index == total_chunks - 1)
                ))
                
                chunk_index += 1
        
        logger.debug(f"📐 Chunk strategy: {len(chunks)} chunks, "
                    f"avg size: {chunks[0].width}x{chunks[0].height}")
        
        return chunks
    
    async def _process_chunks_parallel(
        self,
        image_path: Union[str, Path],
        chunks: List[ChunkInfo],
        processing_func: callable,
        **kwargs
    ) -> AsyncGenerator[Tuple[np.ndarray, ChunkInfo], None]:
        """Process chunks in parallel with controlled memory usage"""
        
        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(self.config.parallel_chunks)
        
        async def process_chunk(chunk: ChunkInfo) -> Tuple[np.ndarray, ChunkInfo]:
            async with semaphore:
                return await self._process_single_chunk(image_path, chunk, processing_func, **kwargs)
        
        # Create tasks for all chunks
        tasks = [process_chunk(chunk) for chunk in chunks]
        
        # Yield results as they complete
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                yield result
            except Exception as e:
                logger.error(f"❌ Chunk processing failed: {e}")
                # Continue with other chunks
                continue
    
    async def _process_single_chunk(
        self,
        image_path: Union[str, Path],
        chunk: ChunkInfo,
        processing_func: callable,
        **kwargs
    ) -> Tuple[np.ndarray, ChunkInfo]:
        """Process a single chunk with memory efficiency"""
        start_time = time.time()
        
        try:
            # Extract chunk with minimal memory usage
            chunk_data = await self._extract_chunk_async(image_path, chunk)
            
            # Get buffer for processing
            if self.buffer_pool:
                async with self.buffer_pool.get_buffer_async(
                    chunk_data.nbytes,
                    priority=MemoryPriority.HIGH
                ) as buffer:
                    np.copyto(buffer, chunk_data.ravel())
                    processed_chunk = buffer.reshape(chunk_data.shape)
                    
                    # Apply processing function
                    result = processing_func(processed_chunk, chunk, **kwargs)
            else:
                # Direct processing (fallback)
                result = processing_func(chunk_data, chunk, **kwargs)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats['total_chunks_processed'] += 1
            self.stats['parallel_processing_time_saved'] += max(0, 0.1 - processing_time)  # Assume 100ms baseline
            
            # Calculate memory saved
            estimated_full_image_memory = chunk.total_chunks * chunk_data.nbytes
            actual_chunk_memory = chunk_data.nbytes
            memory_saved = estimated_full_image_memory - actual_chunk_memory
            self.stats['memory_saved_mb'] += memory_saved / (1024 * 1024)
            
            logger.debug(f"✅ Chunk {chunk.index + 1}/{chunk.total_chunks} "
                        f"processed in {processing_time:.3f}s")
            
            return result, chunk
            
        except Exception as e:
            logger.error(f"❌ Failed to process chunk {chunk.index}: {e}")
            raise
    
    async def _extract_chunk_async(
        self,
        image_path: Union[str, Path],
        chunk: ChunkInfo
    ) -> np.ndarray:
        """Extract image chunk asynchronously with streaming"""
        
        if self.config.enable_streaming_decode:
            return await self._extract_chunk_streaming(image_path, chunk)
        else:
            return await self._extract_chunk_standard(image_path, chunk)
    
    async def _extract_chunk_streaming(
        self,
        image_path: Union[str, Path],
        chunk: ChunkInfo
    ) -> np.ndarray:
        """Extract chunk using streaming decode"""
        def extract_streaming_sync():
            with Image.open(image_path) as img:
                # Crop the specific region
                region = img.crop((chunk.x, chunk.y, chunk.x + chunk.width, chunk.y + chunk.height))
                
                # Convert to numpy array
                if region.mode != 'RGB':
                    region = region.convert('RGB')
                
                return np.array(region)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, extract_streaming_sync)
        self.stats['streaming_decodes'] += 1
        
        return result
    
    async def _extract_chunk_standard(
        self,
        image_path: Union[str, Path],
        chunk: ChunkInfo
    ) -> np.ndarray:
        """Extract chunk using standard method"""
        def extract_standard_sync():
            # Load full image (less memory efficient but more compatible)
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert RGB if needed
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Extract chunk
            chunk_data = image[chunk.y:chunk.y + chunk.height, chunk.x:chunk.x + chunk.width]
            
            return chunk_data
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, extract_standard_sync)
    
    def get_streaming_stats(self) -> dict:
        """Get streaming processing statistics"""
        return self.stats.copy()
    
    async def process_large_image_for_ocr(
        self,
        image_path: Union[str, Path],
        ocr_func: callable,
        max_dimension: int = 4000  # Limit to prevent memory issues
    ) -> List[dict]:
        """
        Specialized method for OCR processing of large images
        
        Args:
            image_path: Path to large image
            ocr_func: OCR function to apply to each chunk
            max_dimension: Maximum dimension for processing
            
        Returns:
            Combined OCR results from all chunks
        """
        all_results = []
        
        async for processed_chunk, chunk_info in self.process_large_image_streaming(
            image_path, ocr_func, max_dimension=max_dimension
        ):
            # Process OCR results
            if isinstance(processed_chunk, dict):
                all_results.append({
                    'chunk_info': {
                        'index': chunk_info.index,
                        'position': (chunk_info.x, chunk_info.y),
                        'size': (chunk_info.width, chunk_info.height)
                    },
                    'results': processed_chunk
                })
            elif isinstance(processed_chunk, (list, tuple)):
                for result in processed_chunk:
                    all_results.append({
                        'chunk_info': {
                            'index': chunk_info.index,
                            'position': (chunk_info.x, chunk_info.y),
                            'size': (chunk_info.width, chunk_info.height)
                        },
                        'results': result
                    })
        
        # Combine overlapping results (remove duplicates)
        combined_results = self._combine_overlapping_results(all_results)
        
        return combined_results
    
    def _combine_overlapping_results(self, results: List[dict]) -> List[dict]:
        """Combine results from overlapping chunks to remove duplicates"""
        # Simple implementation: remove exact duplicates
        seen_texts = set()
        unique_results = []
        
        for result in results:
            result_data = result['results']
            
            # Extract text for deduplication
            if isinstance(result_data, dict) and 'text' in result_data:
                text_key = result_data['text'].strip().lower()
            elif isinstance(result_data, str):
                text_key = result_data.strip().lower()
            else:
                # Can't deduplicate, keep as is
                unique_results.append(result)
                continue
            
            if text_key and text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_results.append(result)
        
        return unique_results


class StreamingOCRProcessor:
    """Specialized streaming processor for OCR tasks"""
    
    def __init__(
        self,
        streaming_config: Optional[StreamingConfig] = None,
        buffer_pool: Optional[BufferPool] = None
    ):
        self.streaming_processor = StreamingImageProcessor(streaming_config, buffer_pool)
        self.ocr_stats = {
            'large_images_processed': 0,
            'total_ocr_calls_saved': 0,
            'avg_memory_reduction_pct': 0.0
        }
    
    async def process_large_image_ocr(
        self,
        image_path: Union[str, Path],
        ocr_reader,
        region_detector: Optional[callable] = None,
        max_dimension: int = 4000
    ) -> dict:
        """
        Process large image with OCR using streaming
        
        Args:
            image_path: Path to large image
            ocr_reader: OCR reader instance
            region_detector: Optional function to detect OCR regions
            max_dimension: Maximum dimension for processing
            
        Returns:
            Combined OCR results with performance metrics
        """
        start_time = time.time()
        image_path = Path(image_path)
        
        # Check if image is large enough to warrant streaming
        image_size = image_path.stat().st_size
        is_large_image = image_size > 10 * 1024 * 1024  # > 10MB
        
        if not is_large_image:
            # Use standard processing for small images
            return await self._process_small_image_standard(image_path, ocr_reader, region_detector)
        
        logger.info(f"🚀 Processing large image with streaming OCR: {image_size / 1024 / 1024:.1f}MB")
        
        # Define OCR processing function for chunks
        def ocr_chunk_processing(chunk_data: np.ndarray, chunk_info: ChunkInfo) -> List[dict]:
            try:
                # Detect regions in chunk if detector provided
                if region_detector:
                    regions = region_detector(chunk_data)
                else:
                    # Use entire chunk
                    regions = [(0, 0, chunk_data.shape[1], chunk_data.shape[0])]
                
                chunk_results = []
                for region in regions:
                    x1, y1, x2, y2 = region
                    region_data = chunk_data[y1:y2, x1:x2]
                    
                    # Apply OCR
                    ocr_results = ocr_reader.readtext(region_data)
                    
                    # Adjust coordinates to global image space
                    for result in ocr_results:
                        if len(result) >= 2:
                            text = result[0] if isinstance(result[0], str) else result[1]
                            confidence = result[1] if isinstance(result[1], float) else 0.0
                            bbox = result[0] if isinstance(result[0], list) else [0, 0, 0, 0]
                            
                            # Adjust bbox coordinates
                            adjusted_bbox = [
                                bbox[0] + chunk_info.x + x1,
                                bbox[1] + chunk_info.y + y1,
                                bbox[2] + chunk_info.x + x1,
                                bbox[3] + chunk_info.y + y1
                            ]
                            
                            chunk_results.append({
                                'text': text,
                                'confidence': confidence,
                                'bbox': adjusted_bbox,
                                'chunk_index': chunk_info.index,
                                'global_position': (chunk_info.x + x1, chunk_info.y + y1)
                            })
                
                return chunk_results
                
            except Exception as e:
                logger.error(f"❌ OCR chunk processing failed: {e}")
                return []
        
        # Process with streaming
        combined_results = await self.streaming_processor.process_large_image_for_ocr(
            image_path, ocr_chunk_processing, max_dimension=max_dimension
        )
        
        # Calculate performance metrics
        processing_time = time.time() - start_time
        streaming_stats = self.streaming_processor.get_streaming_stats()
        
        # Update OCR statistics
        self.ocr_stats['large_images_processed'] += 1
        
        # Estimate OCR calls saved (traditional would process entire image multiple times)
        estimated_traditional_calls = len(combined_results) * 3  # Assume 3x processing in traditional
        actual_streaming_calls = streaming_stats['total_chunks_processed']
        ocr_calls_saved = max(0, estimated_traditional_calls - actual_streaming_calls)
        self.ocr_stats['total_ocr_calls_saved'] += ocr_calls_saved
        
        # Calculate memory reduction
        if streaming_stats['memory_saved_mb'] > 0:
            estimated_full_memory = streaming_stats['memory_saved_mb'] + (
                streaming_stats['total_chunks_processed'] * 50  # Assume 50MB per chunk
            )
            memory_reduction_pct = (streaming_stats['memory_saved_mb'] / estimated_full_memory) * 100
            self.ocr_stats['avg_memory_reduction_pct'] = memory_reduction_pct
        
        logger.info(
            f"✅ Streaming OCR complete: {len(combined_results)} results, "
            f"{processing_time:.3f}s, saved {ocr_calls_saved} OCR calls"
        )
        
        return {
            'success': True,
            'results': combined_results,
            'performance': {
                'processing_time': processing_time,
                'image_size_mb': image_size / 1024 / 1024,
                'chunks_processed': streaming_stats['total_chunks_processed'],
                'memory_saved_mb': streaming_stats['memory_saved_mb'],
                'ocr_calls_saved': ocr_calls_saved,
                'memory_reduction_pct': memory_reduction_pct
            },
            'streaming_used': True
        }
    
    async def _process_small_image_standard(
        self,
        image_path: Path,
        ocr_reader,
        region_detector: Optional[callable]
    ) -> dict:
        """Process small image with standard OCR"""
        start_time = time.time()
        
        def process_sync():
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to RGB
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect regions or use entire image
            if region_detector:
                regions = region_detector(image)
            else:
                regions = [(0, 0, image.shape[1], image.shape[0])]
            
            results = []
            for region in regions:
                x1, y1, x2, y2 = region
                region_data = image[y1:y2, x1:x2]
                
                ocr_results = ocr_reader.readtext(region_data)
                
                for result in ocr_results:
                    if len(result) >= 2:
                        text = result[0] if isinstance(result[0], str) else result[1]
                        confidence = result[1] if isinstance(result[1], float) else 0.0
                        bbox = result[0] if isinstance(result[0], list) else [0, 0, 0, 0]
                        
                        results.append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox,
                            'global_position': (x1, y1)
                        })
            
            return results
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(self.streaming_processor.executor, process_sync)
        
        processing_time = time.time() - start_time
        image_size = image_path.stat().st_size
        
        return {
            'success': True,
            'results': results,
            'performance': {
                'processing_time': processing_time,
                'image_size_mb': image_size / 1024 / 1024,
                'chunks_processed': 1,
                'memory_saved_mb': 0,
                'ocr_calls_saved': 0,
                'memory_reduction_pct': 0
            },
            'streaming_used': False
        }
    
    def get_ocr_stats(self) -> dict:
        """Get OCR-specific streaming statistics"""
        return {
            **self.ocr_stats.copy(),
            'streaming_stats': self.streaming_processor.get_streaming_stats()
        }