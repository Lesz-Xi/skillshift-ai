#!/usr/bin/env python3
"""
MLBB OCR Analysis Triage Script
Tests the key fixes implemented for frontend-backend integration
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30
EXPECTED_KEYS = ["kills", "deaths", "assists", "hero", "confidence"]

class TriageTest:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_health_endpoint(self) -> bool:
        """Test the health endpoint we added for API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            success = response.status_code == 200 and response.json().get("status") == "ok"
            self.log(f"Health endpoint: {'✅ PASS' if success else '❌ FAIL'}")
            return success
        except Exception as e:
            self.log(f"Health endpoint: ❌ FAIL - {e}", "ERROR")
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS middleware is working"""
        try:
            response = requests.options(f"{self.base_url}/health", timeout=5)
            has_cors = "Access-Control-Allow-Origin" in response.headers
            self.log(f"CORS middleware: {'✅ PASS' if has_cors else '❌ FAIL'}")
            return has_cors
        except Exception as e:
            self.log(f"CORS middleware: ❌ FAIL - {e}", "ERROR")
            return False
    
    def test_analyze_endpoint_structure(self) -> bool:
        """Test analyze endpoint returns proper structure even without image"""
        try:
            # Test with missing file
            response = requests.post(f"{self.base_url}/analyze", timeout=10)
            
            # Should get 422 for validation error (proper error handling)
            if response.status_code == 422:
                error_detail = response.json()
                has_proper_structure = "detail" in error_detail
                self.log(f"Error handling structure: {'✅ PASS' if has_proper_structure else '❌ FAIL'}")
                return has_proper_structure
            else:
                self.log(f"Error handling structure: ❌ FAIL - Got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"Error handling structure: ❌ FAIL - {e}", "ERROR")
            return False
    
    def test_fuzzy_ign_matching(self) -> bool:
        """Test IGN matching functionality"""
        try:
            # Test the normalizer functions directly
            from backend.ocr.normalizers import norm_ign, best_ign_match
            
            # Test basic normalization
            test_ign = "Diary0f dolls"  # With OCR noise (0 instead of o)
            normalized = norm_ign(test_ign)
            expected = "diaryofdolls"  # Should convert 0 to o
            
            norm_success = normalized == expected
            self.log(f"IGN normalization: {'✅ PASS' if norm_success else '❌ FAIL'} ({normalized})")
            
            # Test fuzzy matching
            candidates = ["Diary of dolls", "DiaryOfDolls", "diary_of_dolls"]
            match, score = best_ign_match("D1ary 0f d0lls", candidates)
            
            match_success = match is not None and score >= 80
            self.log(f"IGN fuzzy matching: {'✅ PASS' if match_success else '❌ FAIL'} (match: {match}, score: {score})")
            
            return norm_success and match_success
            
        except Exception as e:
            self.log(f"IGN matching tests: ❌ FAIL - {e}", "ERROR")
            return False
    
    def test_kda_regex_fallback(self) -> bool:
        """Test KDA regex extraction fallback"""
        try:
            from backend.ocr.parsers_kda import MLBBKDAParser
            
            parser = MLBBKDAParser()
            
            # Test the regex fallback method directly
            test_text = "Player stats: 12/3/8 KDA ratio"
            result = parser._extract_kda_from_text(test_text)
            
            success = (result is not None and 
                      result.get("kills") == 12 and 
                      result.get("deaths") == 3 and 
                      result.get("assists") == 8)
            
            self.log(f"KDA regex fallback: {'✅ PASS' if success else '❌ FAIL'} ({result})")
            return success
            
        except Exception as e:
            self.log(f"KDA regex fallback: ❌ FAIL - {e}", "ERROR")
            return False
    
    def test_table_detection_fallback(self) -> bool:
        """Test table detection fallback mechanisms"""
        try:
            from backend.ocr.detectors import MLBBTableDetector
            import numpy as np
            
            detector = MLBBTableDetector()
            
            # Create a test image (dummy data)
            test_image = np.zeros((720, 1280, 3), dtype=np.uint8)
            
            # Test the default table region fallback
            width, height = test_image.shape[1], test_image.shape[0]
            region = detector._get_default_table_region(width, height)
            
            success = (region is not None and 
                      hasattr(region, 'panel_bbox') and 
                      len(region.panel_bbox) == 4)
            
            self.log(f"Table detection fallback: {'✅ PASS' if success else '❌ FAIL'}")
            return success
            
        except Exception as e:
            self.log(f"Table detection fallback: ❌ FAIL - {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all triage tests"""
        self.log("Starting MLBB OCR Analysis Triage Tests")
        self.log("=" * 50)
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("CORS Middleware", self.test_cors_headers),
            ("Error Handling Structure", self.test_analyze_endpoint_structure),
            ("IGN Fuzzy Matching", self.test_fuzzy_ign_matching),
            ("KDA Regex Fallback", self.test_kda_regex_fallback),
            ("Table Detection Fallback", self.test_table_detection_fallback),
        ]
        
        results = {}
        passed = 0
        
        for test_name, test_func in tests:
            self.log(f"\nRunning: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                self.log(f"{test_name}: ❌ FAIL - Unexpected error: {e}", "ERROR")
                results[test_name] = False
        
        # Summary
        total = len(tests)
        self.log("\n" + "=" * 50)
        self.log(f"TRIAGE SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED - System appears to be working correctly!")
        elif passed >= total * 0.8:
            self.log("⚠️  Most tests passed - System should work with minor issues")
        else:
            self.log("❌ Multiple failures - System needs attention")
        
        return {
            "passed": passed,
            "total": total,
            "success_rate": passed / total,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def main():
    """Run the triage tests"""
    triage = TriageTest()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ Backend server is running")
    except requests.exceptions.RequestException:
        print("❌ Backend server is not running!")
        print("Please start the server with: python -m uvicorn web.app:app --host 0.0.0.0 --port 8000")
        return 1
    
    # Run tests
    results = triage.run_all_tests()
    
    # Save results
    results_file = Path("triage_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    return 0 if results["success_rate"] == 1.0 else 1

if __name__ == "__main__":
    sys.exit(main())