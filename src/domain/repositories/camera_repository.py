# Repository interfaces for the motion detection system
from abc import ABC, abstractmethod
from ..entities.camera import Camera
from typing import List, Optional, Dict, Any

class ICameraRepository(ABC):
    """Interface for camera repository operations."""
    
    @abstractmethod
    async def add_camera(self, camera: Camera) -> bool:
        """Add a new camera to the system.
        
        Args:
            camera: Camera entity to add
            
        Returns:
            bool: True if camera was added successfully, False otherwise
        """
        pass

    @abstractmethod
    async def delete_camera(self, camera_id: str) -> bool:
        """Delete a camera from the system.
        
        Args:
            camera_id: Unique identifier for the camera
            
        Returns:
            bool: True if camera was deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    async def list_cameras(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all cameras or get specific camera status if camera_id provided.
        
        Args:
            camera_id: Optional camera ID to filter by
            
        Returns:
            List[Dict[str, Any]]: List of camera information dictionaries
        """
        pass

