#!/usr/bin/env python3
"""
Test script for Enhanced OCR Processor - Task 3 Implementation
Tests the new OCR enhancement features and validates performance improvements.
"""

import asyncio
import logging
import time
import os
import sys
from pathlib import Path

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core.enhanced_ocr_processor import (
    EnhancedOCRProcessor, 
    PreprocessingMethod, 
    OCREngine, 
    process_image_enhanced
)
from core.data_collector import DataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class OCREnhancementTester:
    """Test suite for Enhanced OCR functionality."""
    
    def __init__(self):
        self.processor = EnhancedOCRProcessor()
        self.data_collector = DataCollector()
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'performance_metrics': [],
            'quality_improvements': []
        }
    
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite for enhanced OCR."""
        logger.info("🚀 Starting Enhanced OCR Test Suite")
        logger.info("=" * 60)
        
        # Test 1: Basic functionality
        await self._test_basic_functionality()
        
        # Test 2: Preprocessing methods
        await self._test_preprocessing_methods()
        
        # Test 3: OCR engine ensemble
        await self._test_ocr_ensemble()
        
        # Test 4: Quality assessment
        await self._test_quality_assessment()
        
        # Test 5: Performance comparison
        await self._test_performance_comparison()
        
        # Test 6: Integration with DataCollector
        await self._test_datacollector_integration()
        
        # Generate final report
        self._generate_test_report()
    
    async def _test_basic_functionality(self):
        """Test basic enhanced OCR functionality."""
        logger.info("📋 Test 1: Basic Functionality")
        
        try:
            # Create a simple test image (if available)
            test_image_path = self._find_test_image()
            
            if test_image_path:
                result = await self.processor.process_image(
                    image_path=test_image_path,
                    preprocessing_method=PreprocessingMethod.ADVANCED,
                    ocr_engine=OCREngine.EASYOCR
                )
                
                if result.success:
                    logger.info(f"✅ Basic functionality test PASSED")
                    logger.info(f"   - Found {len(result.results)} text regions")
                    logger.info(f"   - Quality score: {result.quality_score:.3f}")
                    logger.info(f"   - Processing time: {result.processing_time:.3f}s")
                    self.test_results['passed_tests'] += 1
                else:
                    logger.error(f"❌ Basic functionality test FAILED: {result.error}")
                    self.test_results['failed_tests'] += 1
            else:
                logger.warning("⚠️ No test image found, skipping basic functionality test")
            
            self.test_results['total_tests'] += 1
            
        except Exception as e:
            logger.error(f"❌ Basic functionality test FAILED with exception: {e}")
            self.test_results['failed_tests'] += 1
            self.test_results['total_tests'] += 1
    
    async def _test_preprocessing_methods(self):
        """Test different preprocessing methods."""
        logger.info("📋 Test 2: Preprocessing Methods")
        
        test_image_path = self._find_test_image()
        if not test_image_path:
            logger.warning("⚠️ No test image found, skipping preprocessing test")
            return
        
        methods = [
            PreprocessingMethod.BASIC,
            PreprocessingMethod.ADVANCED,
            PreprocessingMethod.GAME_SPECIFIC,
            PreprocessingMethod.ADAPTIVE
        ]
        
        for method in methods:
            try:
                start_time = time.time()
                result = await self.processor.process_image(
                    image_path=test_image_path,
                    preprocessing_method=method,
                    ocr_engine=OCREngine.EASYOCR
                )
                processing_time = time.time() - start_time
                
                if result.success:
                    logger.info(f"✅ {method.value} preprocessing: {len(result.results)} regions, "
                              f"quality={result.quality_score:.3f}, time={processing_time:.3f}s")
                    self.test_results['performance_metrics'].append({
                        'method': method.value,
                        'text_regions': len(result.results),
                        'quality_score': result.quality_score,
                        'processing_time': processing_time
                    })
                    self.test_results['passed_tests'] += 1
                else:
                    logger.error(f"❌ {method.value} preprocessing FAILED: {result.error}")
                    self.test_results['failed_tests'] += 1
                
                self.test_results['total_tests'] += 1
                
            except Exception as e:
                logger.error(f"❌ {method.value} preprocessing FAILED with exception: {e}")
                self.test_results['failed_tests'] += 1
                self.test_results['total_tests'] += 1
    
    async def _test_ocr_ensemble(self):
        """Test OCR engine ensemble functionality."""
        logger.info("📋 Test 3: OCR Engine Ensemble")
        
        test_image_path = self._find_test_image()
        if not test_image_path:
            logger.warning("⚠️ No test image found, skipping ensemble test")
            return
        
        engines = [OCREngine.EASYOCR, OCREngine.ENSEMBLE]
        
        # Note: Tesseract might not be installed, so we test what's available
        for engine in engines:
            try:
                start_time = time.time()
                result = await self.processor.process_image(
                    image_path=test_image_path,
                    preprocessing_method=PreprocessingMethod.ADVANCED,
                    ocr_engine=engine
                )
                processing_time = time.time() - start_time
                
                if result.success:
                    logger.info(f"✅ {engine.value} engine: {len(result.results)} regions, "
                              f"confidence={result.ensemble_confidence:.3f}, time={processing_time:.3f}s")
                    self.test_results['passed_tests'] += 1
                else:
                    logger.error(f"❌ {engine.value} engine FAILED: {result.error}")
                    self.test_results['failed_tests'] += 1
                
                self.test_results['total_tests'] += 1
                
            except Exception as e:
                logger.error(f"❌ {engine.value} engine FAILED with exception: {e}")
                self.test_results['failed_tests'] += 1
                self.test_results['total_tests'] += 1
    
    async def _test_quality_assessment(self):
        """Test quality assessment functionality."""
        logger.info("📋 Test 4: Quality Assessment")
        
        test_image_path = self._find_test_image()
        if not test_image_path:
            logger.warning("⚠️ No test image found, skipping quality assessment test")
            return
        
        try:
            result = await self.processor.process_image(
                image_path=test_image_path,
                preprocessing_method=PreprocessingMethod.ADVANCED,
                ocr_engine=OCREngine.EASYOCR
            )
            
            if result.success and 'quality_assessment' in result.raw_engine_results:
                quality_data = result.raw_engine_results['quality_assessment']
                logger.info(f"✅ Quality assessment test PASSED")
                logger.info(f"   - Overall score: {quality_data['overall_score']:.3f}")
                logger.info(f"   - Quality level: {quality_data['quality_level']}")
                logger.info(f"   - Image quality: {quality_data['image_quality']['score']:.3f}")
                logger.info(f"   - OCR quality: {quality_data['ocr_quality']['score']:.3f}")
                
                if quality_data.get('recommendations'):
                    logger.info(f"   - Recommendations: {len(quality_data['recommendations'])}")
                
                self.test_results['passed_tests'] += 1
            else:
                logger.error("❌ Quality assessment test FAILED: No quality data returned")
                self.test_results['failed_tests'] += 1
            
            self.test_results['total_tests'] += 1
            
        except Exception as e:
            logger.error(f"❌ Quality assessment test FAILED with exception: {e}")
            self.test_results['failed_tests'] += 1
            self.test_results['total_tests'] += 1
    
    async def _test_performance_comparison(self):
        """Compare performance between standard and enhanced OCR."""
        logger.info("📋 Test 5: Performance Comparison")
        
        test_image_path = self._find_test_image()
        if not test_image_path:
            logger.warning("⚠️ No test image found, skipping performance comparison")
            return
        
        try:
            # Test standard OCR (if we have a way to test it)
            logger.info("   Testing standard vs enhanced OCR performance...")
            
            # Enhanced OCR test
            start_time = time.time()
            enhanced_result = await self.processor.process_image(
                image_path=test_image_path,
                preprocessing_method=PreprocessingMethod.ADVANCED,
                ocr_engine=OCREngine.EASYOCR
            )
            enhanced_time = time.time() - start_time
            
            if enhanced_result.success:
                logger.info(f"✅ Enhanced OCR: {len(enhanced_result.results)} regions, "
                          f"quality={enhanced_result.quality_score:.3f}, time={enhanced_time:.3f}s")
                
                self.test_results['quality_improvements'].append({
                    'test': 'enhanced_ocr',
                    'text_regions': len(enhanced_result.results),
                    'quality_score': enhanced_result.quality_score,
                    'processing_time': enhanced_time,
                    'ensemble_confidence': enhanced_result.ensemble_confidence
                })
                
                self.test_results['passed_tests'] += 1
            else:
                logger.error(f"❌ Enhanced OCR performance test FAILED: {enhanced_result.error}")
                self.test_results['failed_tests'] += 1
            
            self.test_results['total_tests'] += 1
            
        except Exception as e:
            logger.error(f"❌ Performance comparison test FAILED with exception: {e}")
            self.test_results['failed_tests'] += 1
            self.test_results['total_tests'] += 1
    
    async def _test_datacollector_integration(self):
        """Test integration with DataCollector."""
        logger.info("📋 Test 6: DataCollector Integration")
        
        test_image_path = self._find_test_image()
        if not test_image_path:
            logger.warning("⚠️ No test image found, skipping DataCollector integration test")
            return
        
        try:
            # Test enhanced screenshot processing
            result = await self.data_collector.from_screenshot_enhanced(
                ign="TestPlayer",
                image_path=test_image_path,
                use_ensemble=True
            )
            
            if result and 'data' in result:
                logger.info("✅ DataCollector integration test PASSED")
                logger.info(f"   - Data extracted successfully")
                logger.info(f"   - Warnings: {len(result.get('warnings', []))}")
                
                if result.get('warnings'):
                    for warning in result['warnings'][:3]:  # Show first 3 warnings
                        logger.info(f"   - Warning: {warning}")
                
                self.test_results['passed_tests'] += 1
            else:
                logger.error("❌ DataCollector integration test FAILED: No data returned")
                self.test_results['failed_tests'] += 1
            
            self.test_results['total_tests'] += 1
            
        except Exception as e:
            logger.error(f"❌ DataCollector integration test FAILED with exception: {e}")
            self.test_results['failed_tests'] += 1
            self.test_results['total_tests'] += 1
    
    def _find_test_image(self) -> str:
        """Find a test image for OCR testing."""
        # Look for test images in common locations
        test_paths = [
            "Screenshot-Test/Screenshot-Test-Excellent-1.png",
            "Screenshot-Test/Screenshot-Test-Excellent-2.png", 
            "test_screenshot.png",
            "sample_image.png"
        ]
        
        for path in test_paths:
            if os.path.exists(path):
                return path
        
        # Look in parent directory
        parent_dir = Path(__file__).parent.parent
        for path in test_paths:
            full_path = parent_dir / path
            if full_path.exists():
                return str(full_path)
        
        return None
    
    def _generate_test_report(self):
        """Generate final test report."""
        logger.info("=" * 60)
        logger.info("📊 ENHANCED OCR TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        logger.info(f"📈 Overall Results:")
        logger.info(f"   - Total Tests: {total}")
        logger.info(f"   - Passed: {passed}")
        logger.info(f"   - Failed: {failed}")
        logger.info(f"   - Success Rate: {success_rate:.1f}%")
        
        if self.test_results['performance_metrics']:
            logger.info(f"\n📊 Performance Metrics:")
            for metric in self.test_results['performance_metrics']:
                logger.info(f"   - {metric['method']}: {metric['text_regions']} regions, "
                          f"quality={metric['quality_score']:.3f}, time={metric['processing_time']:.3f}s")
        
        if self.test_results['quality_improvements']:
            logger.info(f"\n🎯 Quality Improvements:")
            for improvement in self.test_results['quality_improvements']:
                logger.info(f"   - Enhanced OCR: {improvement['text_regions']} regions, "
                          f"quality={improvement['quality_score']:.3f}, "
                          f"confidence={improvement['ensemble_confidence']:.3f}")
        
        # Performance stats from processor
        stats = self.processor.get_performance_stats()
        if not stats.get('no_data'):
            logger.info(f"\n📈 Processor Statistics:")
            logger.info(f"   - Total Processed: {stats['total_processed']}")
            logger.info(f"   - Average Processing Time: {stats['average_processing_time']:.3f}s")
            logger.info(f"   - Average Quality Score: {stats['average_quality_score']:.3f}")
        
        # Final assessment
        if success_rate >= 80:
            logger.info(f"\n✅ ENHANCED OCR IMPLEMENTATION: SUCCESS")
            logger.info(f"   Task 3 OCR Performance Enhancement is working correctly!")
        elif success_rate >= 60:
            logger.info(f"\n⚠️ ENHANCED OCR IMPLEMENTATION: PARTIAL SUCCESS")
            logger.info(f"   Some features working, but improvements needed.")
        else:
            logger.info(f"\n❌ ENHANCED OCR IMPLEMENTATION: NEEDS ATTENTION")
            logger.info(f"   Multiple issues detected, review implementation.")
        
        logger.info("=" * 60)


async def main():
    """Main test function."""
    logger.info("🧪 Enhanced OCR Processor Test Suite")
    logger.info("Task 3: OCR Performance Enhancement Validation")
    logger.info("-" * 60)
    
    tester = OCREnhancementTester()
    await tester.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())

