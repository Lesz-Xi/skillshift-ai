#!/usr/bin/env python3
"""
Real-Time Analysis API - WebSocket endpoints for real-time MLBB coaching
========================================================================

This module provides FastAPI WebSocket endpoints for real-time analysis:
- WebSocket connections for live streaming
- Real-time frame processing endpoints
- Stream management and configuration
- Live coaching and event broadcasting
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import base64

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import numpy as np
import cv2

# Import real-time processor
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.realtime_processor import (
        RealTimeAnalysisProcessor, 
        StreamConfig, 
        AnalysisMode,
        get_realtime_processor
    )
    from core.events.websocket_manager import WebSocketManager
    REALTIME_IMPORTS_AVAILABLE = True
except ImportError as e:
    REALTIME_IMPORTS_AVAILABLE = False
    logging.warning(f"Real-time imports not available: {e}")

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/realtime", tags=["realtime"])

# Global WebSocket manager
websocket_manager = WebSocketManager()


# Pydantic models
class StreamConfigModel(BaseModel):
    """Stream configuration model"""
    target_fps: int = Field(default=2, ge=1, le=10, description="Target frames per second")
    max_latency_ms: int = Field(default=500, ge=100, le=5000, description="Maximum latency in milliseconds")
    buffer_size: int = Field(default=30, ge=10, le=100, description="Frame buffer size")
    quality_threshold: float = Field(default=0.7, ge=0.1, le=1.0, description="Minimum quality threshold")
    analysis_mode: str = Field(default="live_gameplay", description="Analysis mode")
    enable_coaching: bool = Field(default=True, description="Enable live coaching")
    enable_event_detection: bool = Field(default=True, description="Enable event detection")
    coaching_frequency: int = Field(default=5, ge=1, le=30, description="Coaching frequency in seconds")
    max_concurrent_analysis: int = Field(default=2, ge=1, le=5, description="Max concurrent analysis")
    enable_gpu_acceleration: bool = Field(default=True, description="Enable GPU acceleration")
    enable_caching: bool = Field(default=True, description="Enable caching")


class FrameData(BaseModel):
    """Frame data model"""
    frame_data: str = Field(description="Base64 encoded frame data")
    timestamp: Optional[str] = Field(default=None, description="Frame timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Frame metadata")


class StreamStartRequest(BaseModel):
    """Stream start request"""
    user_id: Optional[str] = Field(default=None, description="User ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    config: Optional[StreamConfigModel] = Field(default=None, description="Stream configuration")


# WebSocket connection management
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time streaming"""
    
    if not REALTIME_IMPORTS_AVAILABLE:
        await websocket.close(code=1000, reason="Real-time processing not available")
        return
    
    # Accept connection
    await websocket.accept()
    
    # Generate client ID
    client_id = str(uuid.uuid4())
    active_connections[client_id] = websocket
    
    # Connect to WebSocket manager
    await websocket_manager.connect(websocket, user_id=None, session_id=None)
    
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to MLBB Coach AI Real-Time Analysis"
        })
        
        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(websocket, client_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Message processing error: {str(e)}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        if client_id in active_connections:
            del active_connections[client_id]
        await websocket_manager.disconnect(client_id)


async def handle_websocket_message(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages"""
    
    message_type = message.get("type")
    
    if message_type == "start_stream":
        await handle_start_stream(websocket, client_id, message)
    
    elif message_type == "stop_stream":
        await handle_stop_stream(websocket, client_id, message)
    
    elif message_type == "process_frame":
        await handle_process_frame(websocket, client_id, message)
    
    elif message_type == "get_metrics":
        await handle_get_metrics(websocket, client_id)
    
    elif message_type == "update_config":
        await handle_update_config(websocket, client_id, message)
    
    elif message_type == "ping":
        await websocket.send_json({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })


async def handle_start_stream(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle stream start request"""
    
    try:
        # Extract parameters
        user_id = message.get("user_id")
        session_id = message.get("session_id")
        config_data = message.get("config", {})
        
        # Create stream config
        config = None
        if config_data:
            # Convert to StreamConfig
            config = StreamConfig(
                target_fps=config_data.get("target_fps", 2),
                max_latency_ms=config_data.get("max_latency_ms", 500),
                buffer_size=config_data.get("buffer_size", 30),
                quality_threshold=config_data.get("quality_threshold", 0.7),
                analysis_mode=AnalysisMode(config_data.get("analysis_mode", "live_gameplay")),
                enable_coaching=config_data.get("enable_coaching", True),
                enable_event_detection=config_data.get("enable_event_detection", True),
                coaching_frequency=config_data.get("coaching_frequency", 5),
                max_concurrent_analysis=config_data.get("max_concurrent_analysis", 2),
                enable_gpu_acceleration=config_data.get("enable_gpu_acceleration", True),
                enable_caching=config_data.get("enable_caching", True)
            )
        
        # Get processor and start stream
        processor = get_realtime_processor(config)
        result = await processor.start_stream(user_id, session_id)
        
        # Send response
        await websocket.send_json({
            "type": "stream_started",
            "client_id": client_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to start stream: {str(e)}"
        })


async def handle_stop_stream(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle stream stop request"""
    
    try:
        user_id = message.get("user_id")
        
        # Get processor and stop stream
        processor = get_realtime_processor()
        result = await processor.stop_stream(user_id)
        
        # Send response
        await websocket.send_json({
            "type": "stream_stopped",
            "client_id": client_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to stop stream: {str(e)}"
        })


async def handle_process_frame(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle frame processing request"""
    
    try:
        frame_data = message.get("frame_data")
        user_id = message.get("user_id")
        session_id = message.get("session_id")
        
        if not frame_data:
            await websocket.send_json({
                "type": "error",
                "message": "No frame data provided"
            })
            return
        
        # Process frame
        processor = get_realtime_processor()
        result = await processor.process_frame(frame_data, user_id, session_id)
        
        # Send response
        await websocket.send_json({
            "type": "frame_processed",
            "client_id": client_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to process frame: {str(e)}"
        })


async def handle_get_metrics(websocket: WebSocket, client_id: str):
    """Handle metrics request"""
    
    try:
        processor = get_realtime_processor()
        metrics = processor.get_metrics()
        
        await websocket.send_json({
            "type": "metrics",
            "client_id": client_id,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to get metrics: {str(e)}"
        })


async def handle_update_config(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle configuration update request"""
    
    try:
        new_config = message.get("config", {})
        
        processor = get_realtime_processor()
        result = await processor.update_config(new_config)
        
        await websocket.send_json({
            "type": "config_updated",
            "client_id": client_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to update config: {str(e)}"
        })


# REST API endpoints
@router.post("/start")
async def start_realtime_stream(request: StreamStartRequest):
    """Start real-time analysis stream via REST API"""
    
    if not REALTIME_IMPORTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Real-time processing not available")
    
    try:
        # Convert config if provided
        config = None
        if request.config:
            config = StreamConfig(
                target_fps=request.config.target_fps,
                max_latency_ms=request.config.max_latency_ms,
                buffer_size=request.config.buffer_size,
                quality_threshold=request.config.quality_threshold,
                analysis_mode=AnalysisMode(request.config.analysis_mode),
                enable_coaching=request.config.enable_coaching,
                enable_event_detection=request.config.enable_event_detection,
                coaching_frequency=request.config.coaching_frequency,
                max_concurrent_analysis=request.config.max_concurrent_analysis,
                enable_gpu_acceleration=request.config.enable_gpu_acceleration,
                enable_caching=request.config.enable_caching
            )
        
        # Start stream
        processor = get_realtime_processor(config)
        result = await processor.start_stream(request.user_id, request.session_id)
        
        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error starting stream via REST: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_realtime_stream(user_id: Optional[str] = None):
    """Stop real-time analysis stream via REST API"""
    
    if not REALTIME_IMPORTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Real-time processing not available")
    
    try:
        processor = get_realtime_processor()
        result = await processor.stop_stream(user_id)
        
        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error stopping stream via REST: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/frame")
async def process_frame_rest(
    frame_data: FrameData,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Process single frame via REST API"""
    
    if not REALTIME_IMPORTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Real-time processing not available")
    
    try:
        processor = get_realtime_processor()
        result = await processor.process_frame(frame_data.frame_data, user_id, session_id)
        
        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing frame via REST: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_realtime_metrics():
    """Get real-time processing metrics"""
    
    if not REALTIME_IMPORTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Real-time processing not available")
    
    try:
        processor = get_realtime_processor()
        metrics = processor.get_metrics()
        
        return JSONResponse(content={
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics via REST: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_realtime_status():
    """Get real-time processing status"""
    
    if not REALTIME_IMPORTS_AVAILABLE:
        return JSONResponse(content={
            "success": False,
            "status": "unavailable",
            "message": "Real-time processing not available",
            "timestamp": datetime.now().isoformat()
        })
    
    try:
        processor = get_realtime_processor()
        metrics = processor.get_metrics()
        config = processor.get_config()
        
        return JSONResponse(content={
            "success": True,
            "status": metrics["state"],
            "metrics": metrics,
            "config": config,
            "connections": len(active_connections),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting status via REST: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_realtime_config(config: StreamConfigModel):
    """Update real-time processing configuration"""
    
    if not REALTIME_IMPORTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Real-time processing not available")
    
    try:
        # Convert to dict
        config_dict = config.dict()
        
        processor = get_realtime_processor()
        result = await processor.update_config(config_dict)
        
        return JSONResponse(content={
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating config via REST: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections")
async def get_active_connections():
    """Get active WebSocket connections"""
    
    connection_info = []
    for client_id, websocket in active_connections.items():
        connection_info.append({
            "client_id": client_id,
            "state": websocket.client_state.name if hasattr(websocket, 'client_state') else "unknown"
        })
    
    return JSONResponse(content={
        "success": True,
        "total_connections": len(active_connections),
        "connections": connection_info,
        "timestamp": datetime.now().isoformat()
    })


# Health check
@router.get("/health")
async def realtime_health_check():
    """Health check for real-time processing"""
    
    health_status = {
        "service": "realtime_analysis",
        "status": "healthy" if REALTIME_IMPORTS_AVAILABLE else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "imports": REALTIME_IMPORTS_AVAILABLE,
            "connections": len(active_connections),
        }
    }
    
    if REALTIME_IMPORTS_AVAILABLE:
        try:
            processor = get_realtime_processor()
            metrics = processor.get_metrics()
            health_status["checks"]["processor_state"] = metrics["state"]
            health_status["checks"]["error_count"] = metrics["error_count"]
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["checks"]["processor_error"] = str(e)
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


# Example client code (for testing)
EXAMPLE_CLIENT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MLBB Coach AI - Real-Time Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .connected { background-color: #d4edda; color: #155724; }
        .disconnected { background-color: #f8d7da; color: #721c24; }
        .metrics { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        button { padding: 10px 20px; margin: 5px; }
        #messages { height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
    </style>
</head>
<body>
    <h1>MLBB Coach AI - Real-Time Analysis</h1>
    
    <div id="status" class="status disconnected">Disconnected</div>
    
    <button onclick="connect()">Connect</button>
    <button onclick="disconnect()">Disconnect</button>
    <button onclick="startStream()">Start Stream</button>
    <button onclick="stopStream()">Stop Stream</button>
    <button onclick="getMetrics()">Get Metrics</button>
    
    <div class="metrics" id="metrics">
        <h3>Metrics</h3>
        <pre id="metricsData">No metrics available</pre>
    </div>
    
    <div id="messages"></div>
    
    <script>
        let ws = null;
        let connected = false;
        
        function connect() {
            if (ws) return;
            
            ws = new WebSocket('ws://localhost:8000/realtime/stream');
            
            ws.onopen = function() {
                connected = true;
                updateStatus('Connected', true);
                addMessage('Connected to WebSocket');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage('Received: ' + JSON.stringify(data, null, 2));
                
                if (data.type === 'metrics') {
                    document.getElementById('metricsData').textContent = JSON.stringify(data.metrics, null, 2);
                }
            };
            
            ws.onclose = function() {
                connected = false;
                updateStatus('Disconnected', false);
                addMessage('Disconnected from WebSocket');
                ws = null;
            };
            
            ws.onerror = function(error) {
                addMessage('WebSocket error: ' + error);
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
            }
        }
        
        function startStream() {
            if (!connected) return;
            
            const message = {
                type: 'start_stream',
                user_id: 'test_user',
                config: {
                    target_fps: 2,
                    max_latency_ms: 500,
                    enable_coaching: true
                }
            };
            
            ws.send(JSON.stringify(message));
        }
        
        function stopStream() {
            if (!connected) return;
            
            const message = {
                type: 'stop_stream',
                user_id: 'test_user'
            };
            
            ws.send(JSON.stringify(message));
        }
        
        function getMetrics() {
            if (!connected) return;
            
            const message = {
                type: 'get_metrics'
            };
            
            ws.send(JSON.stringify(message));
        }
        
        function updateStatus(text, isConnected) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = text;
            statusDiv.className = 'status ' + (isConnected ? 'connected' : 'disconnected');
        }
        
        function addMessage(message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.innerHTML = '<strong>' + new Date().toLocaleTimeString() + ':</strong> ' + 
                                 (typeof message === 'string' ? message : '<pre>' + message + '</pre>');
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
"""


@router.get("/client")
async def get_test_client():
    """Get test client HTML page"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=EXAMPLE_CLIENT_HTML)
