#!/usr/bin/env python3
"""
Main entry point for the Motion Detection System
"""

import argparse
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


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_in_progress
    
    if shutdown_in_progress:
        print("Shutdown already in progress...")
        return
        
    shutdown_in_progress = True
    print("\nShutting down system...")
    
    try:
        # Stop HTTP server first to break out of serve_forever()
        if http_server:
            print("Stopping HTTP server...")
            # Use threading to shutdown from a different thread
            import threading
            def shutdown_http():
                http_server.shutdown()
            
            shutdown_thread = threading.Thread(target=shutdown_http)
            shutdown_thread.daemon = True
            shutdown_thread.start()
            shutdown_thread.join(timeout=2)
        
        # Stop cameras
        if camera_manager:
            print("Stopping cameras...")
            camera_manager.stop_all_cameras()
        
        # Stop WebSocket server
        if websocket_server:
            websocket_server.stop_server()
        
        # Close HTTP server
        if http_server:
            http_server.server_close()
        
        print("All services stopped. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during shutdown: {e}")
        # Force exit if graceful shutdown fails
        os._exit(1)


def run_motion_detection_server(host=DEFAULT_HTTP_HOST, port=DEFAULT_HTTP_PORT):
    """Run the complete motion detection server system"""
    global camera_manager, websocket_server, http_server
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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
    
    print(f"Motion Detection API server starting on http://{host}:{port}")
    print("Available endpoints:")
    print(f"  POST   http://{host}:{port}/addCamera")
    print(f"  DELETE http://{host}:{port}/deleteCamera?camera_id=ID")
    print(f"  GET    http://{host}:{port}/status")
    print(f"WebSocket server available at ws://{websocket_server.host}:{websocket_server.port}")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass  # Signal handler will take care of cleanup


def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Motion Detection API Server")
    parser.add_argument("--host", default=DEFAULT_HTTP_HOST,
                        help=f"Host to bind to (default: {DEFAULT_HTTP_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_HTTP_PORT,
                        help=f"Port to bind to (default: {DEFAULT_HTTP_PORT})")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Set logging level (default: INFO)")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Run the server
    run_motion_detection_server(args.host, args.port)


if __name__ == "__main__":
    main()
