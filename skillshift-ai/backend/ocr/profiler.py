# backend/ocr/profiler.py
import cProfile
import pstats
import io
import time
import functools
from typing import Any, Callable


def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile a function and print the top 20 time consumers.
    
    Usage:
        @profile_function
        def my_function():
            # function code here
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        pr = cProfile.Profile()
        pr.enable()
        
        # Run the function
        result = func(*args, **kwargs)
        
        pr.disable()
        s = io.StringIO()
        p = pstats.Stats(pr, stream=s).sort_stats("cumtime")
        p.print_stats(20)
        
        print(f"=== PROFILING RESULTS FOR {func.__name__} ===")
        print(s.getvalue())
        print("=" * 50)
        
        return result
    return wrapper


def profile_ocr_pipeline(image_path1: str, image_path2: str = None):
    """
    Profile the complete OCR pipeline with real screenshots.
    
    Args:
        image_path1: Path to first screenshot (KDA view)
        image_path2: Path to second screenshot (Damage view, optional)
    """
    print("🔍 Starting OCR Pipeline Performance Profiling...")
    
    pr = cProfile.Profile()
    pr.enable()
    
    try:
        # Import necessary modules
        from backend.ocr.detectors import row_agnostic_detector
        from backend.ocr.parsers_kda import kda_parser
        from backend.ocr.parsers_damage import damage_parser
        from backend.ocr.fuse import cross_view_fusion
        import cv2
        
        # Load images
        kda_img = cv2.imread(image_path1)
        if kda_img is None:
            print(f"❌ Could not load image: {image_path1}")
            return
        
        # Step 1: Detect table and rows
        start_time = time.time()
        table = row_agnostic_detector.detect_table_regions(image_path1)
        detect_time = (time.time() - start_time) * 1000
        print(f"⏱️  Table detection: {detect_time:.2f}ms")
        
        if table is None:
            print("❌ No table detected")
            return
            
        # Step 2: Generate row crops
        start_time = time.time()
        row_crops = row_agnostic_detector.generate_row_crops(table, image_path1)
        rows_time = (time.time() - start_time) * 1000
        print(f"⏱️  Row generation: {rows_time:.2f}ms")
        
        # Step 3: Parse KDA view
        start_time = time.time()
        kda_result = kda_parser.parse_kda_from_screenshot(image_path1, "Diary of dolls")
        kda_time = (time.time() - start_time) * 1000
        print(f"⏱️  KDA parsing: {kda_time:.2f}ms")
        
        # Step 4: Parse Damage view (if provided)
        damage_result = None
        damage_time = 0
        if image_path2:
            dmg_img = cv2.imread(image_path2)
            if dmg_img is not None:
                start_time = time.time()
                damage_result = damage_parser.parse_damage_from_screenshot(image_path2, "Diary of dolls")
                damage_time = (time.time() - start_time) * 1000
                print(f"⏱️  Damage parsing: {damage_time:.2f}ms")
        
        # Step 5: Cross-view fusion (if both views available)
        fusion_time = 0
        if damage_result:
            start_time = time.time()
            fusion_result = cross_view_fusion.fuse_kda_and_damage(kda_result, damage_result)
            fusion_time = (time.time() - start_time) * 1000
            print(f"⏱️  Cross-view fusion: {fusion_time:.2f}ms")
        
        total_time = detect_time + rows_time + kda_time + damage_time + fusion_time
        print(f"⏱️  **TOTAL PIPELINE TIME: {total_time:.2f}ms**")
        
        # Performance assessment
        if total_time <= 500:
            print("✅ PERFORMANCE TARGET ACHIEVED (<500ms)")
        elif total_time <= 1000:
            print("⚠️  Performance acceptable but could be improved")
        else:
            print("❌ PERFORMANCE TARGET MISSED - optimization needed")
    
    except Exception as e:
        print(f"❌ Profiling error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pr.disable()
    
    # Generate detailed profile
    s = io.StringIO()
    p = pstats.Stats(pr, stream=s).sort_stats("cumtime")
    p.print_stats(20)
    
    print("\n🔍 TOP 20 TIME CONSUMERS:")
    print(s.getvalue())


def profile_quick_test():
    """Quick profiling test with the target screenshots."""
    try:
        # Use the target screenshots from the mission
        kda_image = "/Users/lesz/Documents/Project-AI/Trial-Image/IMG_1767.PNG"
        damage_image = "/Users/lesz/Documents/Project-AI/Trial-Image/IMG_1768.PNG"
        
        print("🎯 Profiling with target screenshots...")
        print(f"KDA view: {kda_image}")
        print(f"Damage view: {damage_image}")
        
        profile_ocr_pipeline(kda_image, damage_image)
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")


if __name__ == "__main__":
    profile_quick_test()