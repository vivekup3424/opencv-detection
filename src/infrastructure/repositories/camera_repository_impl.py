"""Implementation of camera repository using clean architecture services."""

from typing import List, Optional, Dict, Any
import threading
import time
from dataclasses import asdict

from src.domain.entities.camera import Camera
from src.domain.entities.motion_event import MotionEvent
from src.domain.repositories.camera_repository import ICameraRepository
from src.core.errors.exceptions import CameraError, ValidationError
from src.core.utils.validation import is_valid_camera_id
from src.core.utils.datetime_utils import utc_now


class InMemoryICameraRepository(ICameraRepository):
    """In-memory implementation of camera repository using clean architecture services."""
    
    def __init__(self, camera_service: ICameraRepository):
        self._camera_service = camera_service
        self._motion_events: List[MotionEvent] = []
        self._lock = threading.Lock()
    
    async def add_camera(self, camera: Camera) -> bool:
        """Add a new camera."""
        if not is_valid_camera_id(camera.camera_id):
            raise ValidationError(f"Invalid camera ID: {camera.camera_id}")
        
        try:
            success, message = self._camera_service.add_camera(
                camera.camera_id, 
                camera.rtsp_url
            )
            
            if not success:
                raise CameraError(f"Failed to add camera: {message}")
            
            return True
            
        except Exception as e:
            raise CameraError(f"Error adding camera {camera.camera_id}: {str(e)}") from e
    
    async def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera."""
        try:
            success, message = self._camera_service.delete_camera(camera_id)
            
            if not success:
                raise CameraError(f"Failed to remove camera: {message}")
            
            return True
            
        except Exception as e:
            raise CameraError(f"Error removing camera {camera_id}: {str(e)}") from e
    
    async def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Get a specific camera."""
        try:
            status = self._camera_service.get_camera_status(camera_id)
            
            if status is None:
                return None
            
            return Camera(
                camera_id=status["camera_id"],
                rtsp_url=status["rtsp_url"],
                is_active=status["status"] == "running",
                created_at=utc_now(),  # We don't have the actual creation time
                last_seen=utc_now() if status["status"] == "running" else None
            )
            
        except Exception as e:
            raise CameraError(f"Error getting camera {camera_id}: {str(e)}") from e
    
    async def list_cameras(self) -> List[Camera]:
        """List all cameras."""
        try:
            camera_list = self._camera_service.list_cameras()
            
            cameras = []
            for camera_info in camera_list:
                camera = Camera(
                    camera_id=camera_info["camera_id"],
                    rtsp_url=camera_info["rtsp_url"],
                    is_active=camera_info["status"] == "running",
                    created_at=utc_now(),  # We don't have the actual creation time
                    last_seen=utc_now() if camera_info["status"] == "running" else None
                )
                cameras.append(camera)
            
            return cameras
            
        except Exception as e:
            raise CameraError(f"Error listing cameras: {str(e)}") from e
    
    async def update_camera_status(self, camera_id: str, is_active: bool) -> bool:
        """Update camera status."""
        try:
            camera = await self.get_camera(camera_id)
            if camera is None:
                return False
            
            if is_active and not camera.is_active:
                # Start camera if it's not running
                success, _ = self._camera_service.add_camera(camera_id, camera.rtsp_url)
                return success
            elif not is_active and camera.is_active:
                # Stop camera if it's running
                success, _ = self._camera_service.delete_camera(camera_id)
                return success
            
            return True  # No change needed
            
        except Exception as e:
            raise CameraError(f"Error updating camera status {camera_id}: {str(e)}") from e
    
    async def get_camera_status(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed camera status."""
        try:
            status = self._camera_service.get_camera_status(camera_id)
            
            if status is None:
                return None
            
            return {
                "camera_id": status["camera_id"],
                "rtsp_url": status["rtsp_url"],
                "is_active": status["status"] == "running",
                "uptime_seconds": status["uptime_seconds"],
                "status": status["status"]
            }
            
        except Exception as e:
            raise CameraError(f"Error getting camera status {camera_id}: {str(e)}") from e
    
    async def record_motion_event(self, motion_event: MotionEvent) -> bool:
        """Record a motion detection event."""
        try:
            with self._lock:
                self._motion_events.append(motion_event)
                
                # Keep only last 1000 events to prevent memory issues
                if len(self._motion_events) > 1000:
                    self._motion_events = self._motion_events[-1000:]
            
            return True
            
        except Exception as e:
            raise CameraError(f"Error recording motion event: {str(e)}") from e
    
    async def get_motion_events(self, camera_id: str, limit: int = 100) -> List[MotionEvent]:
        """Get recent motion events for a camera."""
        try:
            with self._lock:
                # Filter events for the specific camera and apply limit
                camera_events = [
                    event for event in self._motion_events 
                    if event.camera_id == camera_id
                ]
                
                # Sort by timestamp (newest first) and apply limit
                camera_events.sort(key=lambda x: x.timestamp, reverse=True)
                return camera_events[:limit]
                
        except Exception as e:
            raise CameraError(f"Error getting motion events for {camera_id}: {str(e)}") from e
    
    async def get_all_motion_events(self, limit: int = 100) -> List[MotionEvent]:
        """Get recent motion events from all cameras."""
        try:
            with self._lock:
                # Sort by timestamp (newest first) and apply limit
                sorted_events = sorted(
                    self._motion_events, 
                    key=lambda x: x.timestamp, 
                    reverse=True
                )
                return sorted_events[:limit]
                
        except Exception as e:
            raise CameraError(f"Error getting all motion events: {str(e)}") from e
    
    async def stop_all_cameras(self) -> bool:
        """Stop all cameras."""
        try:
            self._camera_service.stop_all_cameras()
            return True
            
        except Exception as e:
            raise CameraError(f"Error stopping all cameras: {str(e)}") from e