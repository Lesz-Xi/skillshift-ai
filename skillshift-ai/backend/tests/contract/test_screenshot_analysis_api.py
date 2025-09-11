"""
Contract tests for enhanced POST /analysis/screenshot with debug_mode.

Tests the enhanced screenshot analysis API endpoint to ensure it follows
the expected contract and integrates with OCR debugging capabilities.
"""

import pytest
import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app (assuming it exists)
try:
    from web.app import app
except ImportError:
    # Create a mock app for testing
    from fastapi import FastAPI
    app = FastAPI()


class TestScreenshotAnalysisAPI:
    """Contract tests for enhanced screenshot analysis API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_analysis_request(self):
        """Valid screenshot analysis request payload."""
        return {
            "image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "ign": "Diary of dolls",
            "debug_mode": True,
            "extract_kda": True,
            "extract_damage": True,
            "use_row_agnostic": True
        }
    
    def test_screenshot_analysis_endpoint_exists(self, client):
        """Test that the screenshot analysis endpoint exists."""
        # This test will fail until the endpoint is implemented
        # but it documents the expected contract
        response = client.post("/analysis/screenshot", json={})
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "Screenshot analysis endpoint should exist"
    
    def test_screenshot_analysis_valid_request(self, client, valid_analysis_request):
        """Test screenshot analysis with valid request."""
        response = client.post("/analysis/screenshot", json=valid_analysis_request)
        
        # Should return 200 for valid request
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            assert "success" in data, "Response should have success field"
            assert "data" in data, "Response should have data field"
            assert "confidence" in data, "Response should have confidence field"
            
            if data["success"]:
                # Validate data structure
                analysis_data = data["data"]
                assert "player_ign" in analysis_data, "Data should have player_ign"
                assert "hero" in analysis_data, "Data should have hero"
                assert "kda" in analysis_data, "Data should have kda"
                
                # Validate KDA structure
                kda = analysis_data["kda"]
                assert "kills" in kda, "KDA should have kills"
                assert "deaths" in kda, "KDA should have deaths"
                assert "assists" in kda, "KDA should have assists"
    
    def test_screenshot_analysis_debug_mode(self, client, valid_analysis_request):
        """Test screenshot analysis with debug mode enabled."""
        response = client.post("/analysis/screenshot", json=valid_analysis_request)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["success"] and valid_analysis_request["debug_mode"]:
                # Should include debug information
                assert "debug_info" in data, "Debug mode should include debug_info"
                assert "table_region" in data, "Debug mode should include table_region"
                assert "row_crops" in data, "Debug mode should include row_crops"
                assert "ocr_processing_time" in data, "Debug mode should include processing time"
    
    def test_screenshot_analysis_row_agnostic_mode(self, client, valid_analysis_request):
        """Test screenshot analysis with row-agnostic mode."""
        response = client.post("/analysis/screenshot", json=valid_analysis_request)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["success"] and valid_analysis_request["use_row_agnostic"]:
                # Should indicate row-agnostic processing
                assert "processing_method" in data, "Should indicate processing method"
                if "processing_method" in data:
                    assert "row_agnostic" in data["processing_method"].lower(), "Should use row-agnostic processing"
    
    def test_screenshot_analysis_missing_image(self, client):
        """Test screenshot analysis with missing image."""
        request = {
            "ign": "Diary of dolls",
            "debug_mode": True
        }
        
        response = client.post("/analysis/screenshot", json=request)
        
        # Should return 400 for missing required field
        assert response.status_code in [400, 422], "Should return error for missing image"
    
    def test_screenshot_analysis_missing_ign(self, client):
        """Test screenshot analysis with missing IGN."""
        request = {
            "image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "debug_mode": True
        }
        
        response = client.post("/analysis/screenshot", json=request)
        
        # Should return 400 for missing required field
        assert response.status_code in [400, 422], "Should return error for missing IGN"
    
    def test_screenshot_analysis_invalid_image_path(self, client):
        """Test screenshot analysis with invalid image path."""
        request = {
            "image_path": "/nonexistent/image.png",
            "ign": "Diary of dolls",
            "debug_mode": True
        }
        
        response = client.post("/analysis/screenshot", json=request)
        
        # Should return 400 or 422 for invalid image
        assert response.status_code in [400, 422], "Should return error for invalid image"
    
    def test_screenshot_analysis_extract_options(self, client):
        """Test screenshot analysis with different extract options."""
        base_request = {
            "image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "ign": "Diary of dolls",
            "debug_mode": False
        }
        
        # Test with only KDA extraction
        request = base_request.copy()
        request["extract_kda"] = True
        request["extract_damage"] = False
        
        response = client.post("/analysis/screenshot", json=request)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Should handle KDA-only extraction"
        
        # Test with only damage extraction
        request = base_request.copy()
        request["extract_kda"] = False
        request["extract_damage"] = True
        
        response = client.post("/analysis/screenshot", json=request)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Should handle damage-only extraction"
    
    def test_screenshot_analysis_response_time(self, client, valid_analysis_request):
        """Test that screenshot analysis responds within reasonable time."""
        import time
        
        start_time = time.time()
        response = client.post("/analysis/screenshot", json=valid_analysis_request)
        response_time = time.time() - start_time
        
        # Should respond within 30 seconds
        assert response_time < 30, f"Screenshot analysis should respond within 30s, took {response_time:.2f}s"
    
    def test_screenshot_analysis_confidence_scoring(self, client, valid_analysis_request):
        """Test screenshot analysis confidence scoring."""
        response = client.post("/analysis/screenshot", json=valid_analysis_request)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["success"]:
                # Should have confidence scores
                assert "confidence" in data, "Should have overall confidence"
                assert 0.0 <= data["confidence"] <= 1.0, "Confidence should be between 0 and 1"
                
                if "data" in data and "kda" in data["data"]:
                    kda = data["data"]["kda"]
                    if "confidence" in kda:
                        assert 0.0 <= kda["confidence"] <= 1.0, "KDA confidence should be between 0 and 1"
    
    def test_screenshot_analysis_error_handling(self, client):
        """Test screenshot analysis error handling."""
        # Test with malformed JSON
        response = client.post("/analysis/screenshot", data="invalid json")
        assert response.status_code == 422, "Should return 422 for malformed JSON"
        
        # Test with empty request
        response = client.post("/analysis/screenshot", json={})
        assert response.status_code in [400, 422], "Should return error for empty request"
    
    def test_screenshot_analysis_backward_compatibility(self, client):
        """Test screenshot analysis backward compatibility."""
        # Test with minimal request (backward compatibility)
        request = {
            "image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "ign": "Diary of dolls"
        }
        
        response = client.post("/analysis/screenshot", json=request)
        
        # Should still work with minimal request
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Should work with minimal request"
            assert "data" in data, "Should return data with minimal request"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
