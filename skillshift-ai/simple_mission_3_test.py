#!/usr/bin/env python3
"""
Simple Mission 3 Test
Basic validation of OCR Mission 3 implementation.
"""
import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_basic_imports():
    """Test basic imports."""
    logger.info("Testing basic imports...")
    
    try:
        from core.ocr.optimized_roi_processor import OptimizedROIProcessor
        from core.ocr.ocr_cache import OCRCache
        from core.ocr.ocr_reader import get_reader
        from core.ocr.fast_table_detector import FastTableDetector
        from core.ocr.early_exit_fusion import EarlyExitFusion
        from core.ocr.config import get_global_config
        from core.ocr.optimized_analysis_engine import get_global_engine
        
        logger.info("✅ All imports successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_roi_processor():
    """Test ROI processor."""
    logger.info("Testing ROI processor...")
    
    try:
        import numpy as np
        from core.ocr.optimized_roi_processor import OptimizedROIProcessor
        
        # Create test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[20:80, 20:80] = 255
        
        # Test processor
        processor = OptimizedROIProcessor()
        roi_binary = processor.prep_digits_roi(test_image)
        
        assert roi_binary.shape[0] > 0, "ROI should have height"
        assert roi_binary.shape[1] > 0, "ROI should have width"
        
        logger.info("✅ ROI processor test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ ROI processor test failed: {e}")
        return False


def test_ocr_cache():
    """Test OCR cache."""
    logger.info("Testing OCR cache...")
    
    try:
        import numpy as np
        from core.ocr.ocr_cache import OCRCache
        
        # Test cache
        cache = OCRCache(max_size=100)
        test_image = np.zeros((32, 32), dtype=np.uint8)
        test_image[10:20, 10:20] = 255
        
        reader = cache.get_reader()
        texts = cache.cached_readtext(reader, test_image, allowlist="0123456789")
        
        assert isinstance(texts, list), "Should return list"
        
        logger.info("✅ OCR cache test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ OCR cache test failed: {e}")
        return False


def test_configuration():
    """Test configuration system."""
    logger.info("Testing configuration...")
    
    try:
        from core.ocr.config import get_global_config
        
        config = get_global_config()
        budget = config.get('performance.budget_ms')
        
        assert isinstance(budget, (int, float)), "Should return numeric budget"
        assert budget > 0, "Budget should be positive"
        
        logger.info("✅ Configuration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_performance_target():
    """Test performance target."""
    logger.info("Testing performance target...")
    
    try:
        from core.ocr.optimized_analysis_engine import get_global_engine
        import numpy as np
        import cv2
        
        # Create test image
        test_image = np.zeros((200, 300, 3), dtype=np.uint8)
        test_image[50:150, 50:250] = 255
        
        # Save test image
        test_image_path = project_root / "temp" / "test_image.png"
        test_image_path.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(test_image_path), test_image)
        
        # Test engine
        engine = get_global_engine()
        
        start_time = time.time()
        result = engine.analyze_screenshot(str(test_image_path), "Test Player")
        processing_time = (time.time() - start_time) * 1000
        
        # Check performance
        target_ms = 500
        if processing_time <= target_ms:
            logger.info(f"✅ Performance target met: {processing_time:.1f}ms <= {target_ms}ms")
        else:
            logger.warning(f"⚠️ Performance target missed: {processing_time:.1f}ms > {target_ms}ms")
        
        # Cleanup
        if test_image_path.exists():
            test_image_path.unlink()
        
        return processing_time <= target_ms
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("🚀 Starting Mission 3 Simple Test")
    logger.info("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("ROI Processor", test_roi_processor),
        ("OCR Cache", test_ocr_cache),
        ("Configuration", test_configuration),
        ("Performance Target", test_performance_target)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name}...")
        try:
            success = test_func()
            if success:
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Mission 3 Implementation Complete!")
        return True
    else:
        logger.error(f"⚠️ {total-passed} tests failed")
        return False


if __name__ == "__main__":
    # Set environment variables
    os.environ["OCR_BUDGET_MS"] = "500"
    os.environ["FAST_TEST"] = "0"
    
    success = main()
    sys.exit(0 if success else 1)
