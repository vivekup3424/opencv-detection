#!/usr/bin/env python3
"""
Main entry point for the Motion Detection System using Clean Architecture
"""

import signal
import sys
import os
import logging
from http.server import HTTPServer

from .di import initialize_container
from .core.config.settings import get_settings
from .core.errors.exceptions import ApplicationStartupError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global instances
container = None
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
        
        # Shutdown dependency container (which stops all services)
        if container:
            print("Stopping all services...")
            # Stop cleanup service first
            try:
                cleanup_service = container.get_cleanup_service()
                cleanup_service.stop()
            except Exception as e:
                print(f"Error stopping cleanup service: {e}")
            
            container.shutdown()
        
        # Close HTTP server
        if http_server:
            http_server.server_close()
        
        print("All services stopped. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during shutdown: {e}")
        # Force exit if graceful shutdown fails
        os._exit(1)


def run_motion_detection_server():
    """Run the complete motion detection server system"""
    global container, http_server
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting Motion Detection System...")
    
    try:
        # Initialize dependency container
        print("Initializing dependency container...")
        container = initialize_container()
        
        # Get settings
        settings = get_settings()
        
        # Start WebSocket gateway
        print("Starting WebSocket gateway...")
        websocket_gateway = container.get_websocket_gateway()
        websocket_gateway.start_in_thread()
        
        # Start cleanup service
        print("Starting cleanup service...")
        cleanup_service = container.get_cleanup_service()
        cleanup_service.start()
        
        # Create HTTP server with clean architecture controller
        print("Starting HTTP API server...")
        camera_controller_class = container.get_camera_controller_class()
        http_server = HTTPServer((settings.http.host, settings.http.port), camera_controller_class)
        
        print(f"Motion Detection API server starting on http://{settings.http.host}:{settings.http.port}")
        print("Available endpoints:")
        print(f"  POST   http://{settings.http.host}:{settings.http.port}/addCamera")
        print(f"  DELETE http://{settings.http.host}:{settings.http.port}/deleteCamera?camera_id=ID")
        print(f"  GET    http://{settings.http.host}:{settings.http.port}/status")
        print(f"WebSocket server available at ws://{settings.websocket.host}:{settings.websocket.port}")
        print("\nPress Ctrl+C to stop the server")
        
        # Start serving HTTP requests
        http_server.serve_forever()
        
    except ApplicationStartupError as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        pass  # Signal handler will take care of cleanup


def main():
    """Main entry point"""
    try:
        run_motion_detection_server()
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
