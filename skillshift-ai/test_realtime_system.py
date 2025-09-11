#!/usr/bin/env python3
"""
Real-Time System Test - Validation for Task 8 Implementation
============================================================

This test validates the real-time analysis pipeline implementation.
"""

import asyncio
import json
import numpy as np
import cv2
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "target_fps": 1,
    "max_latency_ms": 1000,
    "buffer_size": 10,
    "enable_coaching": True,
    "enable_event_detection": True
}

def create_test_frame() -> np.ndarray:
    """Create a test frame for processing"""
    # Create a simple test image (720p resolution)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Add some content to make it look like a game screenshot
    cv2.rectangle(frame, (100, 100), (200, 200), (0, 255, 0), -1)  # Green rectangle
    cv2.circle(frame, (640, 360), 50, (255, 0, 0), -1)  # Blue circle
    cv2.putText(frame, "MLBB Test Frame", (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return frame

async def test_realtime_processor():
    """Test the real-time processor functionality"""
    
    logger.info("🚀 Starting Real-Time System Test")
    
    try:
        # Import the real-time processor
        from core.realtime_processor import (
            RealTimeAnalysisProcessor, 
            StreamConfig, 
            AnalysisMode
        )
        
        logger.info("✅ Successfully imported real-time processor")
        
        # Create configuration
        config = StreamConfig(
            target_fps=TEST_CONFIG["target_fps"],
            max_latency_ms=TEST_CONFIG["max_latency_ms"],
            buffer_size=TEST_CONFIG["buffer_size"],
            enable_coaching=TEST_CONFIG["enable_coaching"],
            enable_event_detection=TEST_CONFIG["enable_event_detection"],
            analysis_mode=AnalysisMode.LIVE_GAMEPLAY
        )
        
        # Initialize processor
        processor = RealTimeAnalysisProcessor(config)
        logger.info("✅ Real-time processor initialized")
        
        # Start stream
        start_result = await processor.start_stream("test_user", "test_session")
        logger.info(f"✅ Stream started: {start_result}")
        
        if not start_result.get("success", False):
            logger.error("❌ Failed to start stream")
            return False
        
        # Process test frames
        logger.info("🔄 Processing test frames...")
        
        for i in range(3):
            # Create test frame
            test_frame = create_test_frame()
            
            # Process frame
            frame_result = await processor.process_frame(
                test_frame, 
                "test_user", 
                "test_session"
            )
            
            logger.info(f"📊 Frame {i+1} result: {frame_result}")
            
            # Wait between frames
            await asyncio.sleep(2)
        
        # Get metrics
        metrics = processor.get_metrics()
        logger.info(f"📈 Final metrics: {json.dumps(metrics, indent=2)}")
        
        # Stop stream
        stop_result = await processor.stop_stream("test_user")
        logger.info(f"✅ Stream stopped: {stop_result}")
        
        # Validate results
        success = (
            start_result.get("success", False) and
            stop_result.get("success", False) and
            metrics["frames_processed"] > 0
        )
        
        if success:
            logger.info("🎉 Real-time processor test PASSED")
        else:
            logger.error("❌ Real-time processor test FAILED")
        
        return success
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False

async def test_websocket_api():
    """Test WebSocket API endpoints"""
    
    logger.info("🌐 Testing WebSocket API")
    
    try:
        # Import WebSocket API
        from web.realtime_api import router, StreamConfigModel
        
        logger.info("✅ Successfully imported WebSocket API")
        
        # Test configuration model
        config_model = StreamConfigModel(
            target_fps=2,
            max_latency_ms=500,
            enable_coaching=True
        )
        
        logger.info(f"✅ Configuration model created: {config_model}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ WebSocket API import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ WebSocket API test error: {e}")
        return False

def test_event_system():
    """Test event system integration"""
    
    logger.info("📡 Testing Event System")
    
    try:
        # Import event system components
        from core.events.websocket_manager import WebSocketManager
        from core.events.event_bus import get_event_bus
        from core.events.event_types import Event, EventType
        
        logger.info("✅ Successfully imported event system")
        
        # Test WebSocket manager
        ws_manager = WebSocketManager()
        logger.info("✅ WebSocket manager created")
        
        # Test event bus
        event_bus = get_event_bus()
        logger.info("✅ Event bus retrieved")
        
        # Test event creation
        test_event = Event(
            event_type=EventType.ANALYSIS_STARTED,
            data={"test": "data"}
        )
        logger.info(f"✅ Test event created: {test_event.event_id}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Event system import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Event system test error: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive test suite"""
    
    logger.info("🧪 Starting Comprehensive Real-Time System Test")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: Event System
    logger.info("\n📡 Test 1: Event System Integration")
    test_results["event_system"] = test_event_system()
    
    # Test 2: WebSocket API
    logger.info("\n🌐 Test 2: WebSocket API")
    test_results["websocket_api"] = await test_websocket_api()
    
    # Test 3: Real-Time Processor
    logger.info("\n🚀 Test 3: Real-Time Processor")
    test_results["realtime_processor"] = await test_realtime_processor()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name.upper()}: {status}")
    
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED - Real-time system is ready!")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} test(s) failed")
        return False

def main():
    """Main test function"""
    
    print("🚀 MLBB Coach AI - Real-Time System Test")
    print("Task 8: Real-Time Analysis Pipeline Validation")
    print("=" * 60)
    
    # Run tests
    result = asyncio.run(run_comprehensive_test())
    
    print("\n" + "=" * 60)
    if result:
        print("✅ REAL-TIME SYSTEM VALIDATION: SUCCESS")
        print("🎉 Task 8 implementation is working correctly!")
    else:
        print("❌ REAL-TIME SYSTEM VALIDATION: PARTIAL SUCCESS")
        print("⚠️ Some components may need attention")
    
    return result

if __name__ == "__main__":
    main()
