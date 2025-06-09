"""Camera management HTTP controller following clean architecture."""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any
import asyncio

from src.domain.entities.camera import Camera
from src.domain.usecases.camera_management import CameraManagementUseCase
from src.domain.usecases.camera_status import CameraStatusUseCase
from src.core.errors.exceptions import ValidationError, CameraError
from src.core.utils.validation import is_valid_camera_id, validate_required_fields


class CameraController(BaseHTTPRequestHandler):
    """HTTP controller for camera management operations."""
    
    def __init__(self, request, client_address, server, 
                 camera_management_usecase: CameraManagementUseCase,
                 camera_status_usecase: CameraStatusUseCase):
        self.camera_management_usecase = camera_management_usecase
        self.camera_status_usecase = camera_status_usecase
        super().__init__(request, client_address, server)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response with CORS headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_error_response(self, status_code: int, message: str):
        """Send standardized error response."""
        self.send_json_response(status_code, {
            "success": False,
            "message": message
        })
    
    def do_POST(self):
        """Handle POST requests for adding cameras."""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/addCamera':
                self._handle_add_camera()
            else:
                self.send_error_response(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_DELETE(self):
        """Handle DELETE requests for removing cameras."""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/deleteCamera':
                self._handle_delete_camera()
            else:
                self.send_error_response(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests for status."""
        try:
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/status':
                self._handle_status()
            elif parsed_url.path.startswith('/camera/'):
                self._handle_camera_detail()
            else:
                self.send_error_response(404, "Endpoint not found")
                
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def _handle_add_camera(self):
        """Handle adding a new camera."""
        try:
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            # Validate required fields
            missing_fields = validate_required_fields(data, ['camera_id', 'rtsp_url'])
            if missing_fields:
                self.send_error_response(400, f"Missing required fields: {', '.join(missing_fields)}")
                return
            
            camera_id = data['camera_id']
            rtsp_url = data['rtsp_url']
            
            # Validate camera ID format
            if not is_valid_camera_id(camera_id):
                self.send_error_response(400, "Invalid camera ID format")
                return
            
            # Call the use case with the extracted parameters
            success, message = asyncio.run(self.camera_management_usecase.add_camera(camera_id, rtsp_url))
            print("result", success, message)
            
            if success:
                self.send_json_response(200, {
                    "success": True,
                    "message": message,
                    "camera_id": camera_id
                })
            else:
                self.send_error_response(400, message)
                
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON format")
        except ValidationError as e:
            self.send_error_response(400, str(e))
        except CameraError as e:
            self.send_error_response(400, str(e))
    
    def _handle_delete_camera(self):
        """Handle deleting a camera."""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            camera_id = query_params.get('camera_id', [None])[0]
            
            if not camera_id:
                self.send_error_response(400, "Missing required parameter: camera_id")
                return
            
            success, message = asyncio.run(self.camera_management_usecase.delete_camera(camera_id))
            
            if success:
                self.send_json_response(200, {
                    "success": True,
                    "message": message,
                    "camera_id": camera_id
                })
            else:
                self.send_error_response(404, message)
                
        except CameraError as e:
            self.send_error_response(400, str(e))
    
    def _handle_status(self):
        """Handle general status requests."""
        try:
            cameras = asyncio.run(self.camera_status_usecase.list_all_cameras())
            
            camera_list = [
                {
                    "camera_id": camera["camera_id"],
                    "rtsp_url": camera["rtsp_url"],
                }
                for camera in cameras
            ]
            
            self.send_json_response(200, {
                "success": True,
                "api_status": "running",
                "active_cameras": len([c for c in cameras if c.get("is_active", True)]),
                "total_cameras": len(cameras),
                "cameras": camera_list
            })
            
        except CameraError as e:
            self.send_error_response(500, str(e))
    
    def _handle_camera_detail(self):
        """Handle individual camera status requests."""
        try:
            # Extract camera_id from path /camera/{camera_id}
            parsed_url = urlparse(self.path)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) != 2 or path_parts[0] != 'camera':
                self.send_error_response(400, "Invalid camera detail path")
                return
            
            camera_id = path_parts[1]
            
            status = asyncio.run(self.camera_status_usecase.get_camera_status(camera_id))
            
            if status:
                self.send_json_response(200, {
                    "success": True,
                    "camera_status": status
                })
            else:
                self.send_error_response(404, f"Camera {camera_id} not found")
                
        except CameraError as e:
            self.send_error_response(500, str(e))


def create_camera_controller_class(camera_management_usecase: CameraManagementUseCase,
                                  camera_status_usecase: CameraStatusUseCase):
    """Factory function to create controller class with injected dependencies."""
    class ConfiguredCameraController(CameraController):
        def __init__(self, request, client_address, server):
            super().__init__(request, client_address, server, 
                           camera_management_usecase, camera_status_usecase)
    
    return ConfiguredCameraController
