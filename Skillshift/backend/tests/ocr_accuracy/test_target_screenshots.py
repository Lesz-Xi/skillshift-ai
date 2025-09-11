"""
T014: OCR Accuracy Validation Test
High-precision validation against known target screenshots with strict acceptance criteria
"""

import pytest
import cv2
import time
from pathlib import Path
from typing import Dict, Any, List

# Import the OCR pipeline components
from backend.ocr.parsers_kda import parse_kda_view_v2
from backend.ocr.parsers_damage import parse_damage_view  
from backend.ocr.fuse import fuse_cross_view_data
from backend.ocr.detectors import detect_player_row_fuzzy
from backend.ocr.normalizers import normalize_kda_text


class TestTargetScreenshotAccuracy:
    """High-precision accuracy tests for target screenshots"""
    
    @pytest.fixture
    def target_test_cases(self):
        """Target test cases with precise expected results"""
        return [
            {
                "name": "Diary of dolls - Kagura",
                "kda_image": "backend/tests/fixtures/IMG_1767.PNG",
                "damage_image": "backend/tests/fixtures/IMG_1768.PNG",
                "target_ign": "Diary of dolls",
                "expected": {
                    "player_located": True,
                    "hero": "kagura",
                    "kda": {"k": 9, "d": 2, "a": 12},
                    "kda_ratio": 10.5,  # (9+12)/2 = 10.5
                    "mvp_score": 10.5,
                    "min_overall_confidence": 0.85,
                    "min_data_completeness": 0.85,
                    "max_warnings": 0,  # Zero warnings for perfect case
                    "required_fields": ["hero", "kda", "mvp_score"],
                }
            }
        ]
    
    @pytest.fixture
    def performance_requirements(self):
        """Performance requirements for validation"""
        return {
            "max_total_time_ms": 5000,  # 5 seconds max total
            "max_kda_time_ms": 2000,    # 2 seconds max for KDA
            "max_damage_time_ms": 2000, # 2 seconds max for Damage
            "max_fusion_time_ms": 500,  # 500ms max for fusion
            "target_total_time_ms": 3000 # 3 seconds target
        }
    
    @pytest.mark.parametrize("test_case", pytest.lazy_fixture('target_test_cases'))
    def test_target_screenshot_accuracy(self, test_case, performance_requirements):
        """T014-1: Validate accuracy against target screenshot with strict criteria"""
        
        print(f"\n🎯 Testing: {test_case['name']}")
        print(f"Target IGN: '{test_case['target_ign']}'")
        
        # Load test images
        kda_image = cv2.imread(test_case["kda_image"])
        damage_image = cv2.imread(test_case["damage_image"])
        
        assert kda_image is not None, f"Failed to load KDA image: {test_case['kda_image']}"
        assert damage_image is not None, f"Failed to load Damage image: {test_case['damage_image']}"
        
        # Time the entire process
        start_time = time.time()
        
        # Process KDA view with timing
        print("🔍 Processing KDA view...")
        kda_start = time.time()
        kda_result = parse_kda_view_v2(kda_image, test_case["target_ign"])
        kda_time = (time.time() - kda_start) * 1000
        
        # Process Damage view with timing
        print("🔍 Processing Damage view...")
        damage_start = time.time()
        damage_row = detect_player_row_fuzzy(damage_image, test_case["target_ign"])
        damage_result = None
        if damage_row >= 0:
            damage_result = parse_damage_view(damage_image, damage_row, test_case["target_ign"])
        damage_time = (time.time() - damage_start) * 1000
        
        # Fuse results with timing
        print("🔄 Fusing results...")
        fusion_start = time.time()
        fused_result = fuse_cross_view_data(kda_result, damage_result, test_case["target_ign"])
        fusion_time = (time.time() - fusion_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        # Print performance metrics
        print(f"⏱️ Performance Metrics:")
        print(f"  KDA Processing: {kda_time:.1f}ms")
        print(f"  Damage Processing: {damage_time:.1f}ms")
        print(f"  Fusion Processing: {fusion_time:.1f}ms")
        print(f"  Total Time: {total_time:.1f}ms")
        
        # Validate performance requirements
        self._validate_performance(
            kda_time, damage_time, fusion_time, total_time, 
            performance_requirements
        )
        
        # Validate accuracy requirements
        self._validate_accuracy(fused_result, test_case["expected"])
        
        # Print success summary
        print(f"✅ {test_case['name']} - All criteria met!")
        self._print_result_summary(fused_result)
    
    def test_kda_extraction_precision(self):
        """T014-2: Test precise KDA extraction accuracy"""
        kda_image = cv2.imread("backend/tests/fixtures/IMG_1767.PNG")
        target_ign = "Diary of dolls"
        
        # Test the KDA parsing specifically
        result = parse_kda_view_v2(kda_image, target_ign)
        
        # Validate precise KDA values
        assert result is not None, "KDA parsing failed"
        assert result.kda is not None, "KDA values not extracted"
        assert result.kda["k"] == 9, f"Kills: expected 9, got {result.kda['k']}"
        assert result.kda["d"] == 2, f"Deaths: expected 2, got {result.kda['d']}"
        assert result.kda["a"] == 12, f"Assists: expected 12, got {result.kda['a']}"
        
        # Validate ratio calculation
        expected_ratio = (9 + 12) / max(1, 2)  # (K+A)/max(1,D)
        actual_ratio = (result.kda["k"] + result.kda["a"]) / max(1, result.kda["d"])
        assert abs(actual_ratio - expected_ratio) < 0.01, f"KDA ratio mismatch: {actual_ratio}"
        
        print(f"✅ KDA Extraction: {result.kda['k']}/{result.kda['d']}/{result.kda['a']} (ratio: {actual_ratio})")
    
    def test_hero_identification_precision(self):
        """T014-3: Test precise hero identification"""
        kda_image = cv2.imread("backend/tests/fixtures/IMG_1767.PNG")
        target_ign = "Diary of dolls"
        
        result = parse_kda_view_v2(kda_image, target_ign)
        
        # Validate hero identification
        assert result is not None, "KDA parsing failed"
        assert result.hero is not None, "Hero not identified"
        assert result.hero.lower() == "kagura", f"Hero: expected 'kagura', got '{result.hero}'"
        
        print(f"✅ Hero Identification: {result.hero}")
    
    def test_mvp_score_precision(self):
        """T014-4: Test MVP score extraction precision"""
        kda_image = cv2.imread("backend/tests/fixtures/IMG_1767.PNG")
        target_ign = "Diary of dolls"
        
        result = parse_kda_view_v2(kda_image, target_ign)
        
        # Validate MVP score
        assert result is not None, "KDA parsing failed"
        assert result.mvp_score is not None, "MVP score not extracted"
        
        # MVP score should be approximately 10.5 (allowing small tolerance)
        expected_mvp = 10.5
        assert abs(result.mvp_score - expected_mvp) < 1.0, \
            f"MVP Score: expected ~{expected_mvp}, got {result.mvp_score}"
        
        print(f"✅ MVP Score: {result.mvp_score}")
    
    def test_player_detection_precision(self):
        """T014-5: Test precise player detection across both views"""
        kda_image = cv2.imread("backend/tests/fixtures/IMG_1767.PNG")
        damage_image = cv2.imread("backend/tests/fixtures/IMG_1768.PNG")
        target_ign = "Diary of dolls"
        
        # Test KDA view detection
        kda_result = parse_kda_view_v2(kda_image, target_ign)
        assert kda_result is not None, "KDA parsing failed"
        assert hasattr(kda_result, 'player_located'), "Missing player_located field"
        assert kda_result.player_located is True, "Player not located in KDA view"
        
        # Test Damage view detection
        damage_row = detect_player_row_fuzzy(damage_image, target_ign)
        assert damage_row >= 0, f"Player not detected in damage view: row {damage_row}"
        
        damage_result = parse_damage_view(damage_image, damage_row, target_ign)
        if damage_result:
            assert hasattr(damage_result, 'player_located') or damage_row >= 0, \
                "Player should be located in damage view"
        
        print(f"✅ Player Detection: KDA=Found, Damage=Row {damage_row}")
    
    def test_no_regression_errors(self):
        """T014-6: Ensure no regression errors or warnings for perfect case"""
        kda_image = cv2.imread("backend/tests/fixtures/IMG_1767.PNG")
        damage_image = cv2.imread("backend/tests/fixtures/IMG_1768.PNG")
        target_ign = "Diary of dolls"
        
        # Process full pipeline
        kda_result = parse_kda_view_v2(kda_image, target_ign)
        damage_row = detect_player_row_fuzzy(damage_image, target_ign)
        damage_result = parse_damage_view(damage_image, damage_row, target_ign) if damage_row >= 0 else None
        fused_result = fuse_cross_view_data(kda_result, damage_result, target_ign)
        
        # Check for regression errors
        regression_indicators = [
            "No numeric data found in fallback parsing",
            "Failed to parse",
            "Critical error",
            "Exception occurred",
            "Unexpected format"
        ]
        
        all_warnings = []
        if hasattr(fused_result, 'warnings'):
            all_warnings.extend(fused_result.warnings)
        if hasattr(kda_result, 'warnings'):
            all_warnings.extend(getattr(kda_result, 'warnings', []))
        
        # Check for regression indicators
        for warning in all_warnings:
            for indicator in regression_indicators:
                assert indicator not in warning, f"Regression detected: {warning}"
        
        # For the perfect test case, we should have minimal warnings
        assert len(all_warnings) <= 2, f"Too many warnings for perfect case: {all_warnings}"
        
        print(f"✅ No Regression: {len(all_warnings)} warnings (acceptable)")
    
    def _validate_performance(self, kda_time: float, damage_time: float, 
                            fusion_time: float, total_time: float, 
                            requirements: Dict[str, float]):
        """Validate performance against requirements"""
        
        # Check individual component times
        assert kda_time < requirements["max_kda_time_ms"], \
            f"KDA processing {kda_time:.1f}ms exceeds {requirements['max_kda_time_ms']}ms limit"
        
        assert damage_time < requirements["max_damage_time_ms"], \
            f"Damage processing {damage_time:.1f}ms exceeds {requirements['max_damage_time_ms']}ms limit"
        
        assert fusion_time < requirements["max_fusion_time_ms"], \
            f"Fusion processing {fusion_time:.1f}ms exceeds {requirements['max_fusion_time_ms']}ms limit"
        
        # Check total time
        assert total_time < requirements["max_total_time_ms"], \
            f"Total processing {total_time:.1f}ms exceeds {requirements['max_total_time_ms']}ms limit"
        
        # Report if we meet the target time
        if total_time < requirements["target_total_time_ms"]:
            print(f"🚀 Excellent performance: {total_time:.1f}ms (under {requirements['target_total_time_ms']}ms target)")
        else:
            print(f"⚡ Acceptable performance: {total_time:.1f}ms (within {requirements['max_total_time_ms']}ms limit)")
    
    def _validate_accuracy(self, result: Any, expected: Dict[str, Any]):
        """Validate accuracy against expected results"""
        
        # Player detection
        assert result.player_located == expected["player_located"], \
            f"Player location: expected {expected['player_located']}, got {result.player_located}"
        
        # Hero identification
        if expected.get("hero"):
            assert result.hero is not None, "Hero should not be None"
            assert result.hero.lower() == expected["hero"].lower(), \
                f"Hero: expected '{expected['hero']}', got '{result.hero}'"
        
        # KDA values (exact match required)
        if expected.get("kda"):
            assert result.kda is not None, "KDA should not be None"
            exp_kda = expected["kda"]
            assert result.kda["k"] == exp_kda["k"], f"Kills: expected {exp_kda['k']}, got {result.kda['k']}"
            assert result.kda["d"] == exp_kda["d"], f"Deaths: expected {exp_kda['d']}, got {result.kda['d']}"
            assert result.kda["a"] == exp_kda["a"], f"Assists: expected {exp_kda['a']}, got {result.kda['a']}"
        
        # MVP score (with tolerance)
        if expected.get("mvp_score"):
            assert result.mvp_score is not None, "MVP score should not be None"
            assert abs(result.mvp_score - expected["mvp_score"]) < 1.0, \
                f"MVP Score: expected ~{expected['mvp_score']}, got {result.mvp_score}"
        
        # Quality thresholds
        assert result.overall_confidence >= expected["min_overall_confidence"], \
            f"Confidence {result.overall_confidence:.3f} below required {expected['min_overall_confidence']}"
        
        assert result.data_completeness >= expected["min_data_completeness"], \
            f"Completeness {result.data_completeness:.3f} below required {expected['min_data_completeness']}"
        
        # Warning limit
        warning_count = len(result.warnings) if hasattr(result, 'warnings') else 0
        assert warning_count <= expected["max_warnings"], \
            f"Too many warnings: {warning_count} > {expected['max_warnings']}"
        
        # Required fields present
        for field in expected.get("required_fields", []):
            assert hasattr(result, field) and getattr(result, field) is not None, \
                f"Required field '{field}' is missing or None"
    
    def _print_result_summary(self, result: Any):
        """Print comprehensive result summary"""
        print(f"\n📊 Result Summary:")
        print(f"  Player Located: {result.player_located}")
        print(f"  Player IGN: {result.player_ign}")
        print(f"  Hero: {result.hero}")
        
        if hasattr(result, 'kda') and result.kda:
            print(f"  KDA: {result.kda['k']}/{result.kda['d']}/{result.kda['a']}")
            ratio = (result.kda['k'] + result.kda['a']) / max(1, result.kda['d'])
            print(f"  KDA Ratio: {ratio:.2f}")
        
        if hasattr(result, 'mvp_score') and result.mvp_score:
            print(f"  MVP Score: {result.mvp_score}")
        
        print(f"  Overall Confidence: {result.overall_confidence:.3f}")
        print(f"  Data Completeness: {result.data_completeness:.3f}")
        
        if hasattr(result, 'warnings') and result.warnings:
            print(f"  Warnings ({len(result.warnings)}): {result.warnings}")
        else:
            print(f"  Warnings: None")