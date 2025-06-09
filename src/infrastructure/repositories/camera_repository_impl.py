"""Implementation of camera repository using clean architecture services."""

from typing import List, Optional, Dict, Any
import threading
import asyncio
from dataclasses import asdict

from src.domain.entities.camera import Camera
from src.domain.repositories.camera_repository import ICameraRepository
from src.core.errors.exceptions import CameraError, ValidationError
from src.core.utils.validation import is_valid_camera_id
from src.core.utils.datetime_utils import utc_now


class CameraRepositoryImpl(ICameraRepository):
    """Complete implementation of camera repository with WebSocket support."""
    
    def __init__(self, camera_service=None, websocket_gateway=None):
        """Initialize camera repository.
        
        Args:
            camera_service: Optional camera service for actual camera operations
            websocket_gateway: Optional WebSocket gateway for broadcasting events
        """
        self._camera_service = camera_service
        self._websocket_gateway = websocket_gateway
        self._cameras: Dict[str, Camera] = {}
        self._lock = threading.Lock()
    
    async def add_camera(self, camera: Camera) -> bool:
        """Add a new camera."""
        try:
            # Store camera in memory
            with self._lock:
                self._cameras[camera.camera_id] = camera
            
            # Add to camera service if available
            if self._camera_service and hasattr(self._camera_service, 'add_camera'):
                result = self._camera_service.add_camera(camera)
                if hasattr(result, '__iter__') and not isinstance(result, str):
                    # Result is a tuple (success, message)
                    success, message = result
                    if not success:
                        raise CameraError(f"Failed to add camera: {message}")
                elif not result:
                    raise CameraError(f"Failed to add camera {camera.camera_id}")
            
            return True
            
        except Exception as e:
            raise CameraError(f"Error adding camera {camera.camera_id}: {str(e)}") from e
    
    async def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera."""
        try:
            # Remove from memory
            with self._lock:
                if camera_id in self._cameras:
                    del self._cameras[camera_id]
            
            # Remove from camera service if available
            if self._camera_service and hasattr(self._camera_service, 'delete_camera'):
                result = self._camera_service.delete_camera(camera_id)
                if hasattr(result, '__iter__') and not isinstance(result, str):
                    # Result is a tuple (success, message)
                    success, message = result
                    if not success:
                        raise CameraError(f"Failed to remove camera: {message}")
                elif not result:
                    raise CameraError(f"Failed to remove camera {camera_id}")
            
            return True
            
        except Exception as e:
            raise CameraError(f"Error removing camera {camera_id}: {str(e)}") from e
    
    async def delete_camera(self, camera_id: str) -> bool:
        """Delete a camera (alias for remove_camera to match interface)."""
        return await self.remove_camera(camera_id)
    
    async def list_cameras(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all cameras or get specific camera by ID."""
        try:
            # If camera_id is specified, return specific camera
            if camera_id:
                with self._lock:
                    if camera_id in self._cameras:
                        camera = self._cameras[camera_id]
                        return [{
                            "camera_id": camera.camera_id,
                            "rtsp_url": camera.rtsp_url
                        }]
                return []
            
            # Get all cameras from memory
            cameras = []
            with self._lock:
                for camera in self._cameras.values():
                    cameras.append({
                        "camera_id": camera.camera_id,
                        "rtsp_url": camera.rtsp_url
                    })
            
            return cameras
            
        except Exception as e:
            raise CameraError(f"Error listing cameras: {str(e)}") from e
    
    async def get_camera_status(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get camera information."""
        try:
            # Check memory
            with self._lock:
                if camera_id in self._cameras:
                    camera = self._cameras[camera_id]
                    return {
                        "camera_id": camera.camera_id,
                        "rtsp_url": camera.rtsp_url
                    }
            
            return None
            
        except Exception as e:
            raise CameraError(f"Error getting camera {camera_id}: {str(e)}") from e