"""Camera status use case for read-only operations (CQRS Query side)."""

from typing import List, Optional, Dict, Any

from src.domain.entities.camera import Camera
from src.domain.repositories.camera_repository import ICameraRepository


class CameraStatusUseCase:
    """
    Use case for retrieving camera status and information.
    This follows CQRS pattern - only handles queries (read operations).
    """
    
    def __init__(self, camera_repository: ICameraRepository):
        self.camera_repository = camera_repository
    
    async def get_camera_by_id(self, camera_id: str) -> Optional[Camera]:
        """
        Get detailed information about a specific camera.
        
        Args:
            camera_id: The ID of the camera to retrieve
            
        Returns:
            Camera entity if found, None otherwise
        """
        return await self.camera_repository.get_camera(camera_id)
    
    async def list_all_cameras(self) -> List[Camera]:
        """
        Get a list of all cameras in the system.
        
        Returns:
            List of all camera entities
        """
        return await self.camera_repository.list_cameras()
    
    async def get_camera_runtime_status(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed runtime status for a specific camera.
        Includes operational metrics like recording status, uptime, etc.
        
        Args:
            camera_id: The ID of the camera
            
        Returns:
            Dictionary with runtime status information, None if camera not found
        """
        camera = await self.camera_repository.get_camera(camera_id)
        if not camera:
            return None
            
        # Get additional runtime status from repository
        return await self.camera_repository.get_camera_status(camera_id)
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """
        Get system-wide overview statistics.
        
        Returns:
            Dictionary containing system overview metrics
        """
        cameras = await self.list_all_cameras()
        active_cameras = [c for c in cameras if c.is_active]
        
        return {
            "total_cameras": len(cameras),
            "active_cameras": len(active_cameras),
            "inactive_cameras": len(cameras) - len(active_cameras),
            "camera_list": [
                {
                    "camera_id": camera.camera_id,
                    "is_active": camera.is_active,
                    "rtsp_url": camera.rtsp_url
                }
                for camera in cameras
            ]
        }
    
    async def is_camera_active(self, camera_id: str) -> bool:
        """
        Check if a camera is currently active and running.
        
        Args:
            camera_id: The ID of the camera to check
            
        Returns:
            True if camera is active, False otherwise
        """
        camera = await self.get_camera_by_id(camera_id)
        return camera is not None and camera.is_active
    
    async def get_cameras_by_status(self, active_only: bool = True) -> List[Camera]:
        """
        Get cameras filtered by their active status.
        
        Args:
            active_only: If True, return only active cameras. If False, return only inactive cameras.
            
        Returns:
            List of cameras matching the status filter
        """
        all_cameras = await self.list_all_cameras()
        return [camera for camera in all_cameras if camera.is_active == active_only]
