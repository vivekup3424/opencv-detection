#!/usr/bin/env python3
"""
Main entry point for the Motion Detection System
"""
import signal
import sys
import os
import logging
from http.server import HTTPServer

from config import DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT
from camera_manager import CameraManager
from websocket_server import MotionDetectionWebSocketServer
from api_handler import create_handler_class

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global instances
camera_manager = None
websocket_server = None
http_server = None
shutdown_in_progress = False

def run_motion_detection_server(host=DEFAULT_HTTP_HOST, port=DEFAULT_HTTP_PORT):
    """Run the complete motion detection server system"""
    global camera_manager, websocket_server, http_server
    
    print("Starting Motion Detection System...")
    
    # Initialize WebSocket server
    print("Starting WebSocket server...")
    websocket_server = MotionDetectionWebSocketServer()
    websocket_server.start_server()
    
    # Initialize camera manager with WebSocket server reference
    print("Initializing camera manager...")
    camera_manager = CameraManager(websocket_server)
    
    # Create HTTP server with configured handler
    handler_class = create_handler_class(camera_manager)
    http_server = HTTPServer((host, port), handler_class)
    
    logger.info(f"Motion Detection API server starting on http://{host}:{port}")
    logger.info("Available endpoints:")
    logger.info(f"  POST   http://{host}:{port}/addCamera")
    logger.info(f"  DELETE http://{host}:{port}/deleteCamera?camera_id=ID")
    logger.info(f"  GET    http://{host}:{port}/status")
    logger.info(f"WebSocket server available at ws://{websocket_server.host}:{websocket_server.port}")
    logger.info("\nPress Ctrl+C to stop the server")
    
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down system")
        if camera_manager:
            logger.info("Stopping cameras...")
            camera_manager.stop_all_cameras()
        if websocket_server:
            logger.info("Stopping WebSocket server...")
            websocket_server.stop_server()
        if http_server:
            logger.info("Stopping HTTP server...")
            http_server.shutdown()
def main():
    """Main entry point with command line argument parsing"""
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, "INFO"))
    
    # Run the server
    run_motion_detection_server(DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT)


if __name__ == "__main__":
    main()
