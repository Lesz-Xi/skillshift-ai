"""
OCR Performance Test Suite for Mission 3
Tests end-to-end KDA+Damage fusion path performance with budgeted timing.
"""
import os
import time
import pytest
import logging
from typing import Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance budget configuration
BUDGET_MS = int(os.getenv("OCR_BUDGET_MS", "2000"))
FAST_TEST = os.getenv("FAST_TEST", "1") == "1"
JSON_LOGS = os.getenv("OCR_JSON_LOGS", "0") == "1"

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
GOLDEN_IMAGE = FIXTURES_DIR / "golden_test_image.png"


class PerformanceTimer:
    """High-precision performance timer with stage tracking."""
    
    def __init__(self):
        self.stages = {}
        self.start_time = None
        self.current_stage = None
    
    def start(self):
        """Start overall timing."""
        self.start_time = time.perf_counter()
        self.stages = {}
    
    def stage_start(self, stage_name: str):
        """Start timing a specific stage."""
        if self.current_stage:
            self.stage_end()
        self.current_stage = stage_name
        self.stages[stage_name] = {"start": time.perf_counter()}
    
    def stage_end(self):
        """End timing current stage."""
        if self.current_stage and self.current_stage in self.stages:
            self.stages[self.current_stage]["end"] = time.perf_counter()
            self.stages[self.current_stage]["duration_ms"] = (
                self.stages[self.current_stage]["end"] - self.stages[self.current_stage]["start"]
            ) * 1000
            self.current_stage = None
    
    def get_total_time(self) -> float:
        """Get total elapsed time in milliseconds."""
        if self.start_time is None:
            return 0.0
        return (time.perf_counter() - self.start_time) * 1000
    
    def get_stage_timings(self) -> Dict[str, float]:
        """Get all stage timings in milliseconds."""
        timings = {}
        for stage, data in self.stages.items():
            if "duration_ms" in data:
                timings[stage] = data["duration_ms"]
        return timings
    
    def print_timings(self):
        """Print formatted timing results."""
        total = self.get_total_time()
        stage_timings = self.get_stage_timings()
        
        print(f"\n⏱️  Performance Results:")
        print(f"   Total: {total:.1f}ms (budget: {BUDGET_MS}ms)")
        
        for stage, duration in stage_timings.items():
            print(f"   {stage}: {duration:.1f}ms")
        
        if JSON_LOGS:
            import json
            log_data = {
                "total_ms": total,
                "budget_ms": BUDGET_MS,
                "stage_ms": stage_timings,
                "within_budget": total <= BUDGET_MS
            }
            print(f"\n📊 JSON Log: {json.dumps(log_data, indent=2)}")


@pytest.fixture
def performance_timer():
    """Performance timer fixture."""
    return PerformanceTimer()


@pytest.fixture
def golden_image_path():
    """Path to golden test image."""
    if not GOLDEN_IMAGE.exists():
        pytest.skip(f"Golden test image not found: {GOLDEN_IMAGE}")
    return str(GOLDEN_IMAGE)


@pytest.fixture
def test_ign():
    """Test IGN for golden test."""
    return "Diary of dolls"


class TestOCRPerformance:
    """OCR Performance test suite."""
    
    def test_golden_performance_budget(self, performance_timer, golden_image_path, test_ign):
        """Test golden image performance within budget."""
        if FAST_TEST:
            pytest.skip("Skipping performance test in FAST_TEST mode")
        
        # Import here to avoid initialization overhead
        from skillshift_ai.core.enhanced_data_collector import EnhancedDataCollector
        
        timer = performance_timer
        timer.start()
        
        try:
            # Initialize collector
            timer.stage_start("init")
            collector = EnhancedDataCollector()
            timer.stage_end()
            
            # Run analysis
            timer.stage_start("analyze")
            result = collector.analyze_screenshot_with_session(
                image_path=golden_image_path,
                ign=test_ign
            )
            timer.stage_end()
            
            # Validate results
            timer.stage_start("validate")
            self._validate_golden_result(result, test_ign)
            timer.stage_end()
            
            # Check performance budget
            total_time = timer.get_total_time()
            timer.print_timings()
            
            assert total_time <= BUDGET_MS, (
                f"Performance budget exceeded: {total_time:.1f}ms > {BUDGET_MS}ms"
            )
            
            # Validate golden test criteria
            data = result.get("data", {})
            assert data.get("kills") == 9, f"Expected kills=9, got {data.get('kills')}"
            assert data.get("deaths") == 2, f"Expected deaths=2, got {data.get('deaths')}"
            assert data.get("assists") == 12, f"Expected assists=12, got {data.get('assists')}"
            
            confidence = result.get("confidence", 0.0)
            assert confidence >= 0.85, f"Expected confidence >= 0.85, got {confidence:.3f}"
            
            logger.info(f"✅ Golden test passed: {total_time:.1f}ms (budget: {BUDGET_MS}ms)")
            
        except Exception as e:
            timer.print_timings()
            raise
    
    def test_roi_optimization_performance(self, performance_timer, golden_image_path, test_ign):
        """Test ROI optimization performance."""
        if FAST_TEST:
            pytest.skip("Skipping ROI test in FAST_TEST mode")
        
        # Import optimized components
        from skillshift_ai.core.ocr.optimized_roi_processor import OptimizedROIProcessor
        from skillshift_ai.core.ocr.ocr_cache import OCRCache
        
        timer = performance_timer
        timer.start()
        
        try:
            # Test ROI preprocessing
            timer.stage_start("roi_prep")
            roi_processor = OptimizedROIProcessor()
            roi_image = roi_processor.prep_digits_roi(golden_image_path)
            timer.stage_end()
            
            # Test cached OCR
            timer.stage_start("cached_ocr")
            cache = OCRCache()
            reader = cache.get_reader()
            texts = cache.cached_readtext(reader, roi_image, allowlist="0123456789/%,.")
            timer.stage_end()
            
            # Validate ROI results
            timer.stage_start("validate_roi")
            assert len(texts) > 0, "ROI OCR should extract some text"
            timer.stage_end()
            
            total_time = timer.get_total_time()
            timer.print_timings()
            
            # ROI should be significantly faster than full OCR
            assert total_time < BUDGET_MS * 0.5, (
                f"ROI processing too slow: {total_time:.1f}ms"
            )
            
            logger.info(f"✅ ROI optimization test passed: {total_time:.1f}ms")
            
        except Exception as e:
            timer.print_timings()
            raise
    
    def test_early_exit_fusion_performance(self, performance_timer, golden_image_path, test_ign):
        """Test early-exit fusion performance."""
        if FAST_TEST:
            pytest.skip("Skipping early-exit test in FAST_TEST mode")
        
        from skillshift_ai.core.ocr.early_exit_fusion import EarlyExitFusion
        
        timer = performance_timer
        timer.start()
        
        try:
            # Test early-exit fusion
            timer.stage_start("early_exit_fusion")
            fusion = EarlyExitFusion()
            result = fusion.analyze_with_early_exit(
                image_path=golden_image_path,
                ign=test_ign,
                confidence_threshold=0.9
            )
            timer.stage_end()
            
            # Validate early-exit results
            timer.stage_start("validate_early_exit")
            self._validate_golden_result(result, test_ign)
            timer.stage_end()
            
            total_time = timer.get_total_time()
            timer.print_timings()
            
            # Early-exit should be faster than full analysis
            assert total_time < BUDGET_MS * 0.7, (
                f"Early-exit too slow: {total_time:.1f}ms"
            )
            
            logger.info(f"✅ Early-exit fusion test passed: {total_time:.1f}ms")
            
        except Exception as e:
            timer.print_timings()
            raise
    
    def test_performance_regression(self, performance_timer, golden_image_path, test_ign):
        """Test for performance regressions."""
        if FAST_TEST:
            pytest.skip("Skipping regression test in FAST_TEST mode")
        
        from skillshift_ai.core.data_collector import DataCollector
        
        timer = performance_timer
        timer.start()
        
        try:
            # Test baseline performance
            timer.stage_start("baseline_analysis")
            collector = DataCollector()
            result = collector.from_screenshot_enhanced(
                ign=test_ign,
                image_path=golden_image_path
            )
            timer.stage_end()
            
            total_time = timer.get_total_time()
            timer.print_timings()
            
            # Baseline should not exceed 2x budget (regression check)
            max_allowed = BUDGET_MS * 2
            assert total_time <= max_allowed, (
                f"Performance regression detected: {total_time:.1f}ms > {max_allowed}ms"
            )
            
            logger.info(f"✅ Performance regression test passed: {total_time:.1f}ms")
            
        except Exception as e:
            timer.print_timings()
            raise
    
    def _validate_golden_result(self, result: Dict[str, Any], expected_ign: str):
        """Validate golden test result structure and content."""
        assert isinstance(result, dict), "Result should be a dictionary"
        
        data = result.get("data", {})
        assert isinstance(data, dict), "Result should contain 'data' field"
        
        # Check for required fields
        required_fields = ["kills", "deaths", "assists", "hero_damage"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check confidence
        confidence = result.get("confidence", 0.0)
        assert 0.0 <= confidence <= 1.0, f"Invalid confidence: {confidence}"
        
        # Check for warnings (should be minimal for golden test)
        warnings = result.get("warnings", [])
        if warnings:
            logger.warning(f"Golden test warnings: {warnings}")


def test_performance_ratchet():
    """Test performance budget ratcheting in CI."""
    if not os.getenv("CI"):
        pytest.skip("Performance ratchet only runs in CI")
    
    # Test different budget levels
    budgets = [2000, 1500, 1000, 500]
    current_budget = BUDGET_MS
    
    assert current_budget in budgets, f"Invalid budget level: {current_budget}"
    
    # Find current level and next target
    current_idx = budgets.index(current_budget)
    if current_idx > 0:
        next_target = budgets[current_idx - 1]
        logger.info(f"Current budget: {current_budget}ms, next target: {next_target}ms")
    else:
        logger.info(f"At minimum budget: {current_budget}ms")


if __name__ == "__main__":
    # Run performance tests directly
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    # Set test environment
    os.environ["FAST_TEST"] = "0"
    os.environ["OCR_BUDGET_MS"] = "2000"
    
    pytest.main([__file__, "-v", "-s"])
