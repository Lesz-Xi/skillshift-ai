#!/usr/bin/env python3
"""
Mission 3 Validation Script
Comprehensive validation of OCR Mission 3 implementation for <500ms performance.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_performance_harness():
    """Test performance harness functionality."""
    logger.info("🧪 Testing Performance Harness...")
    
    try:
        from tests.performance.test_ocr_performance import PerformanceTimer, TestOCRPerformance
        
        # Test timer functionality
        timer = PerformanceTimer()
        timer.start()
        
        timer.stage_start("test_stage")
        time.sleep(0.01)  # Simulate work
        timer.stage_end()
        
        total_time = timer.get_total_time()
        stage_timings = timer.get_stage_timings()
        
        assert total_time > 0, "Timer should record time"
        assert "test_stage" in stage_timings, "Should record stage timings"
        assert stage_timings["test_stage"] > 0, "Stage timing should be positive"
        
        logger.info("✅ Performance harness test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance harness test failed: {e}")
        return False


def test_roi_optimization():
    """Test ROI optimization system."""
    logger.info("🧪 Testing ROI Optimization...")
    
    try:
        from core.ocr.optimized_roi_processor import OptimizedROIProcessor
        import numpy as np
        
        # Create test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[20:80, 20:80] = 255  # White rectangle
        
        # Test ROI processor
        processor = OptimizedROIProcessor(max_side=512, min_side=64)
        
        # Test preprocessing
        roi_binary = processor.prep_digits_roi(test_image)
        assert roi_binary.shape[0] > 0, "ROI should have height"
        assert roi_binary.shape[1] > 0, "ROI should have width"
        
        # Test table detection
        regions = processor.detect_table_regions(test_image)
        assert isinstance(regions, list), "Should return list of regions"
        
        logger.info("✅ ROI optimization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ ROI optimization test failed: {e}")
        return False


def test_ocr_caching():
    """Test OCR caching system."""
    logger.info("🧪 Testing OCR Caching...")
    
    try:
        from core.ocr.ocr_cache import OCRCache, PerformanceOptimizedCache
        import numpy as np
        
        # Test basic cache
        cache = OCRCache(max_size=100)
        
        # Create test image
        test_image = np.zeros((32, 32), dtype=np.uint8)
        test_image[10:20, 10:20] = 255
        
        # Test caching
        reader = cache.get_reader()
        texts1 = cache.cached_readtext(reader, test_image, allowlist="0123456789")
        texts2 = cache.cached_readtext(reader, test_image, allowlist="0123456789")
        
        # Should get same result (cached)
        assert texts1 == texts2, "Cached results should be identical"
        
        # Test performance cache
        perf_cache = PerformanceOptimizedCache(max_size=100)
        stats = perf_cache.get_performance_metrics()
        assert 'cache_size' in stats, "Should have cache size in metrics"
        
        logger.info("✅ OCR caching test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ OCR caching test failed: {e}")
        return False


def test_singleton_reader():
    """Test singleton OCR reader."""
    logger.info("🧪 Testing Singleton OCR Reader...")
    
    try:
        from core.ocr.ocr_reader import get_reader, get_optimized_reader, get_reader_stats
        
        # Test basic reader
        reader1 = get_reader()
        reader2 = get_reader()
        assert reader1 is reader2, "Should return same singleton instance"
        
        # Test optimized reader
        opt_reader = get_optimized_reader()
        assert opt_reader is not None, "Should return optimized reader"
        
        # Test stats
        stats = get_reader_stats()
        assert 'initialized' in stats, "Should have initialization status"
        assert stats['initialized'], "Reader should be initialized"
        
        logger.info("✅ Singleton reader test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Singleton reader test failed: {e}")
        return False


def test_table_detection():
    """Test fast table detection."""
    logger.info("🧪 Testing Fast Table Detection...")
    
    try:
        from core.ocr.fast_table_detector import FastTableDetector, ProjectionBasedDetector
        import numpy as np
        
        # Create test image with table-like structure
        test_image = np.zeros((200, 300, 3), dtype=np.uint8)
        
        # Add horizontal lines (table rows)
        test_image[50:55, :] = 255
        test_image[100:105, :] = 255
        test_image[150:155, :] = 255
        
        # Add vertical lines (table columns)
        test_image[:, 100:105] = 255
        test_image[:, 200:205] = 255
        
        # Test fast detector
        detector = FastTableDetector(downscale_size=1280)
        result = detector.detect_table_structure(test_image)
        
        assert 'rows_count' in result, "Should have rows count"
        assert 'columns_count' in result, "Should have columns count"
        assert 'confidence' in result, "Should have confidence"
        
        # Test projection detector
        proj_detector = ProjectionBasedDetector(downscale_size=1280)
        rows = proj_detector.detect_table_rows(test_image)
        assert isinstance(rows, list), "Should return list of rows"
        
        logger.info("✅ Table detection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Table detection test failed: {e}")
        return False


def test_early_exit_fusion():
    """Test early-exit fusion system."""
    logger.info("🧪 Testing Early-Exit Fusion...")
    
    try:
        from core.ocr.early_exit_fusion import EarlyExitFusion
        import numpy as np
        
        # Create test image
        test_image = np.zeros((100, 200, 3), dtype=np.uint8)
        test_image[20:80, 20:180] = 255
        
        # Test fusion system
        fusion = EarlyExitFusion(
            confidence_threshold=0.9,
            max_iterations=3,
            enable_performance_monitoring=True
        )
        
        # Test IGN matching
        test_texts = ["Diary of dolls", "9/2/12", "45,230"]
        ign_result = fusion._quick_ign_match("Diary of dolls", test_texts)
        
        assert 'matched_ign' in ign_result, "Should have matched IGN"
        assert 'confidence' in ign_result, "Should have confidence"
        
        # Test KDA extraction
        kda_data = fusion._extract_kda_from_texts(test_texts)
        assert 'kills' in kda_data, "Should have kills"
        assert 'deaths' in kda_data, "Should have deaths"
        assert 'assists' in kda_data, "Should have assists"
        
        # Test damage extraction
        damage_data = fusion._extract_damage_from_texts(test_texts)
        assert 'hero_damage' in damage_data, "Should have hero damage"
        
        logger.info("✅ Early-exit fusion test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Early-exit fusion test failed: {e}")
        return False


def test_configuration():
    """Test configuration system."""
    logger.info("🧪 Testing Configuration System...")
    
    try:
        from core.ocr.config import OCRConfiguration, get_global_config
        
        # Test basic configuration
        config = OCRConfiguration()
        config.load_from_env_or_yaml()
        
        # Test get/set
        budget = config.get('performance.budget_ms')
        assert isinstance(budget, (int, float)), "Should return numeric budget"
        
        config.set('performance.test_value', 123)
        test_value = config.get('performance.test_value')
        assert test_value == 123, "Should set and get values"
        
        # Test hardware config
        hw_config = config.get_hardware_config()
        assert 'gpu_backend' in hw_config, "Should have GPU backend"
        
        # Test global config
        global_config = get_global_config()
        assert global_config is not None, "Should return global config"
        
        logger.info("✅ Configuration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_optimized_analysis_engine():
    """Test the main optimized analysis engine."""
    logger.info("🧪 Testing Optimized Analysis Engine...")
    
    try:
        from core.ocr.optimized_analysis_engine import OptimizedAnalysisEngine, get_global_engine
        import numpy as np
        
        # Create test image
        test_image = np.zeros((200, 300, 3), dtype=np.uint8)
        test_image[50:150, 50:250] = 255  # White rectangle
        
        # Save test image
        test_image_path = project_root / "temp" / "test_image.png"
        test_image_path.parent.mkdir(exist_ok=True)
        
        import cv2
        cv2.imwrite(str(test_image_path), test_image)
        
        # Test engine
        engine = OptimizedAnalysisEngine()
        
        # Test analysis
        result = engine.analyze_screenshot(
            str(test_image_path), 
            "Test Player",
            enable_early_exit=True
        )
        
        assert 'data' in result, "Should have data"
        assert 'confidence' in result, "Should have confidence"
        assert 'processing_time_ms' in result, "Should have processing time"
        assert 'performance' in result, "Should have performance metrics"
        
        # Test performance metrics
        metrics = engine.get_performance_metrics()
        assert 'engine_metrics' in metrics, "Should have engine metrics"
        assert 'cache_metrics' in metrics, "Should have cache metrics"
        
        # Test global engine
        global_engine = get_global_engine()
        assert global_engine is not None, "Should return global engine"
        
        # Cleanup
        if test_image_path.exists():
            test_image_path.unlink()
        
        logger.info("✅ Optimized analysis engine test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Optimized analysis engine test failed: {e}")
        return False


def test_performance_targets():
    """Test that performance targets are met."""
    logger.info("🧪 Testing Performance Targets...")
    
    try:
        from core.ocr.optimized_analysis_engine import get_global_engine
        import numpy as np
        import cv2
        
        # Create test image
        test_image = np.zeros((400, 600, 3), dtype=np.uint8)
        
        # Add some structure
        test_image[50:350, 50:550] = 255
        test_image[100:110, :] = 128  # Horizontal line
        test_image[200:210, :] = 128  # Horizontal line
        test_image[300:310, :] = 128  # Horizontal line
        
        # Save test image
        test_image_path = project_root / "temp" / "perf_test_image.png"
        test_image_path.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(test_image_path), test_image)
        
        # Test performance
        engine = get_global_engine()
        
        # Run multiple tests for average
        times = []
        for i in range(3):
            start_time = time.time()
            result = engine.analyze_screenshot(
                str(test_image_path), 
                "Performance Test Player",
                enable_early_exit=True
            )
            processing_time = (time.time() - start_time) * 1000
            times.append(processing_time)
        
        avg_time = sum(times) / len(times)
        
        # Check performance target
        target_ms = 500
        if avg_time <= target_ms:
            logger.info(f"✅ Performance target met: {avg_time:.1f}ms <= {target_ms}ms")
        else:
            logger.warning(f"⚠️ Performance target missed: {avg_time:.1f}ms > {target_ms}ms")
        
        # Cleanup
        if test_image_path.exists():
            test_image_path.unlink()
        
        return avg_time <= target_ms
        
    except Exception as e:
        logger.error(f"❌ Performance target test failed: {e}")
        return False


def run_comprehensive_validation():
    """Run comprehensive validation of Mission 3 implementation."""
    logger.info("🚀 Starting Mission 3 Comprehensive Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Performance Harness", test_performance_harness),
        ("ROI Optimization", test_roi_optimization),
        ("OCR Caching", test_ocr_caching),
        ("Singleton Reader", test_singleton_reader),
        ("Table Detection", test_table_detection),
        ("Early-Exit Fusion", test_early_exit_fusion),
        ("Configuration", test_configuration),
        ("Optimized Analysis Engine", test_optimized_analysis_engine),
        ("Performance Targets", test_performance_targets)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name}...")
        try:
            success = test_func()
            results[test_name] = success
            if success:
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name:<30} {status}")
    
    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Mission 3 Implementation Complete!")
        return True
    else:
        logger.error(f"⚠️ {total-passed} tests failed - Mission 3 needs fixes")
        return False


if __name__ == "__main__":
    # Set environment variables for testing
    os.environ["OCR_BUDGET_MS"] = "500"
    os.environ["FAST_TEST"] = "0"
    os.environ["OCR_JSON_LOGS"] = "1"
    
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)
