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
    
    async def get_camera_by_id(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific camera.
        
        Args:
            camera_id: The ID of the camera to retrieve
            
        Returns:
            Camera information if found, None otherwise
        """
        return await self.camera_repository.get_camera_status(camera_id)
    
    async def list_all_cameras(self) -> List[Dict[str, Any]]:
        """
        Get a list of all cameras in the system.
        
        Returns:
            List of all camera information
        """
        return await self.camera_repository.list_cameras()
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """
        Get system-wide overview statistics.
        
        Returns:
            Dictionary containing system overview metrics
        """
        cameras = await self.list_all_cameras()
        
        return {
            "total_cameras": len(cameras),
            "camera_list": cameras
        }