#!/usr/bin/env python3
"""
HTTP API handlers for the Motion Detection System
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class MotionAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for motion detection API"""
    
    def __init__(self, request, client_address, server, camera_manager):
        self.camera_manager = camera_manager
        super().__init__(request, client_address, server)
    
    def log_message(self, format, *args):
        """Override to reduce verbose logging"""
        pass  # Comment this line if you want to see HTTP logs
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, status_code, data):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def do_POST(self):
        """Handle POST requests for adding cameras"""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/addCamera':
                self._handle_add_camera()
            else:
                self.send_json_response(404, {
                    "success": False,
                    "message": "Endpoint not found"
                })
                
        except Exception as e:
            self.send_json_response(500, {
                "success": False,
                "message": f"Internal server error: {str(e)}"
            })
    
    def do_DELETE(self):
        """Handle DELETE requests for removing cameras"""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/deleteCamera':
                self._handle_delete_camera()
            else:
                self.send_json_response(404, {
                    "success": False,
                    "message": "Endpoint not found"
                })
                
        except Exception as e:
            self.send_json_response(500, {
                "success": False,
                "message": f"Internal server error: {str(e)}"
            })
    
    def do_GET(self):
        """Handle GET requests for status"""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/status':
                self._handle_status()
            else:
                self.send_json_response(404, {
                    "success": False,
                    "message": "Endpoint not found"
                })
                
        except Exception as e:
            self.send_json_response(500, {
                "success": False,
                "message": f"Internal server error: {str(e)}"
            })
    
    def _handle_add_camera(self):
        """Handle adding a new camera"""
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            camera_id = data.get('camera_id')
            rtsp_url = data.get('rtsp_url')
            
            if not camera_id or not rtsp_url:
                self.send_json_response(400, {
                    "success": False,
                    "message": "Missing required fields: camera_id and rtsp_url"
                })
                return
            
            success, message = self.camera_manager.add_camera(camera_id, rtsp_url)
            status_code = 200 if success else 400
            
            self.send_json_response(status_code, {
                "success": success,
                "message": message,
                "camera_id": camera_id
            })
            
        except json.JSONDecodeError:
            self.send_json_response(400, {
                "success": False,
                "message": "Invalid JSON format"
            })
    
    def _handle_delete_camera(self):
        """Handle deleting a camera"""
        # Parse query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        camera_id = query_params.get('camera_id', [None])[0]
        
        if not camera_id:
            self.send_json_response(400, {
                "success": False,
                "message": "Missing required parameter: camera_id"
            })
            return
        
        success, message = self.camera_manager.delete_camera(camera_id)
        status_code = 200 if success else 404
        
        self.send_json_response(status_code, {
            "success": success,
            "message": message,
            "camera_id": camera_id
        })
    
    def _handle_status(self):
        """Handle status requests"""
        # General API status
        cameras = self.camera_manager.list_cameras()
        self.send_json_response(200, {
            "success": True,
            "api_status": "running",
            "active_cameras": len(cameras),
            "cameras": cameras
        })


def create_handler_class(camera_manager):
    """Factory function to create handler class with camera_manager dependency"""
    class ConfiguredMotionAPIHandler(MotionAPIHandler):
        def __init__(self, request, client_address, server):
            super().__init__(request, client_address, server, camera_manager)
    
    return ConfiguredMotionAPIHandler
