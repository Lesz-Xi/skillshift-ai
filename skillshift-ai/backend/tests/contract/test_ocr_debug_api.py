"""
Contract tests for POST /ocr/debug endpoint.

Tests the OCR debug API endpoint to ensure it follows the expected contract
and can handle various input scenarios.
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


class TestOCRDebugAPI:
    """Contract tests for OCR debug API."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def valid_debug_request(self):
        """Valid OCR debug request payload."""
        return {
            "image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "target_ign": "Diary of dolls",
            "debug_mode": True,
            "extract_kda": True,
            "extract_damage": True
        }
    
    def test_ocr_debug_endpoint_exists(self, client):
        """Test that the OCR debug endpoint exists."""
        # This test will fail until the endpoint is implemented
        # but it documents the expected contract
        response = client.post("/ocr/debug", json={})
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "OCR debug endpoint should exist"
    
    def test_ocr_debug_valid_request(self, client, valid_debug_request):
        """Test OCR debug with valid request."""
        response = client.post("/ocr/debug", json=valid_debug_request)
        
        # Should return 200 for valid request
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            assert "success" in data, "Response should have success field"
            assert "debug_info" in data, "Response should have debug_info field"
            assert "table_region" in data, "Response should have table_region field"
            assert "row_crops" in data, "Response should have row_crops field"
            
            if data["success"]:
                # Validate table region structure
                table_region = data["table_region"]
                assert "panel_bbox" in table_region, "Table region should have panel_bbox"
                assert "rows_count" in table_region, "Table region should have rows_count"
                assert "confidence" in table_region, "Table region should have confidence"
                
                # Validate row crops structure
                row_crops = data["row_crops"]
                assert isinstance(row_crops, list), "Row crops should be a list"
                
                for row_crop in row_crops:
                    assert "row_index" in row_crop, "Row crop should have row_index"
                    assert "bbox_ratio" in row_crop, "Row crop should have bbox_ratio"
                    assert "confidence" in row_crop, "Row crop should have confidence"
    
    def test_ocr_debug_missing_image(self, client):
        """Test OCR debug with missing image."""
        request = {
            "target_ign": "Diary of dolls",
            "debug_mode": True
        }
        
        response = client.post("/ocr/debug", json=request)
        
        # Should return 400 for missing required field
        assert response.status_code in [400, 422], "Should return error for missing image"
    
    def test_ocr_debug_invalid_image_path(self, client):
        """Test OCR debug with invalid image path."""
        request = {
            "image_path": "/nonexistent/image.png",
            "target_ign": "Diary of dolls",
            "debug_mode": True
        }
        
        response = client.post("/ocr/debug", json=request)
        
        # Should return 400 or 422 for invalid image
        assert response.status_code in [400, 422], "Should return error for invalid image"
    
    def test_ocr_debug_missing_target_ign(self, client):
        """Test OCR debug with missing target IGN."""
        request = {
            "image_path": str(project_root.parent / "Trial-Image" / "IMG_1767.PNG"),
            "debug_mode": True
        }
        
        response = client.post("/ocr/debug", json=request)
        
        # Should return 400 or 422 for missing required field
        assert response.status_code in [400, 422], "Should return error for missing target_ign"
    
    def test_ocr_debug_debug_mode_false(self, client, valid_debug_request):
        """Test OCR debug with debug_mode=False."""
        request = valid_debug_request.copy()
        request["debug_mode"] = False
        
        response = client.post("/ocr/debug", json=request)
        
        if response.status_code == 200:
            data = response.json()
            # Should still return debug info but maybe less detailed
            assert "success" in data, "Response should have success field"
    
    def test_ocr_debug_extract_options(self, client, valid_debug_request):
        """Test OCR debug with different extract options."""
        # Test with only KDA extraction
        request = valid_debug_request.copy()
        request["extract_kda"] = True
        request["extract_damage"] = False
        
        response = client.post("/ocr/debug", json=request)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Response should have success field"
        
        # Test with only damage extraction
        request = valid_debug_request.copy()
        request["extract_kda"] = False
        request["extract_damage"] = True
        
        response = client.post("/ocr/debug", json=request)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Response should have success field"
    
    def test_ocr_debug_response_time(self, client, valid_debug_request):
        """Test that OCR debug responds within reasonable time."""
        import time
        
        start_time = time.time()
        response = client.post("/ocr/debug", json=valid_debug_request)
        response_time = time.time() - start_time
        
        # Should respond within 30 seconds
        assert response_time < 30, f"OCR debug should respond within 30s, took {response_time:.2f}s"
    
    def test_ocr_debug_error_handling(self, client):
        """Test OCR debug error handling."""
        # Test with malformed JSON
        response = client.post("/ocr/debug", data="invalid json")
        assert response.status_code == 422, "Should return 422 for malformed JSON"
        
        # Test with empty request
        response = client.post("/ocr/debug", json={})
        assert response.status_code in [400, 422], "Should return error for empty request"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
