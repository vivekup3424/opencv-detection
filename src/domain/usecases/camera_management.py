"""Camera management use case - handles camera lifecycle operations (Commands only)."""

from typing import Tuple

from src.domain.entities.camera import Camera
from src.domain.repositories.camera_repository import ICameraRepository
from src.core.errors.exceptions import ValidationError, CameraError
from src.core.utils.validation import is_valid_camera_id


class CameraManagementUseCase:
    """Use case for camera management operations (Create, Delete only - CQRS Commands)."""
    
    def __init__(self, camera_repository: ICameraRepository):
        self.camera_repository = camera_repository
    
    async def add_camera(self, camera_id: str, rtsp_url: str) -> Tuple[bool, str]:
        """
        Add a new camera to the system.
        
        Args:
            camera_id: Unique identifier for the camera
            rtsp_url: RTSP stream URL for the camera
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Raises:
            ValidationError: If camera_id or rtsp_url are invalid
        """
        # Validate inputs
        if not is_valid_camera_id(camera_id):
            raise ValidationError(f"Invalid camera ID: {camera_id}")
        
        if not rtsp_url or not rtsp_url.strip():
            raise ValidationError("RTSP URL cannot be empty")
        
        # Create camera entity
        camera = Camera(
            camera_id=camera_id.strip(),
            rtsp_url=rtsp_url.strip(),
            is_active=False  # Will be activated when added to repository
        )
        
        try:
            success = await self.camera_repository.add_camera(camera)
            if success:
                return True, f"Camera {camera_id} added successfully"
            else:
                return False, f"Failed to add camera {camera_id}"
        except Exception as e:
            raise CameraError(f"Error adding camera {camera_id}: {str(e)}")
    
    async def delete_camera(self, camera_id: str) -> Tuple[bool, str]:
        """
        Delete a camera from the system.
        
        Args:
            camera_id: The ID of the camera to delete
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Raises:
            ValidationError: If camera_id is invalid
            CameraError: If deletion fails
        """
        if not is_valid_camera_id(camera_id):
            raise ValidationError(f"Invalid camera ID: {camera_id}")
        
        try:
            success = await self.camera_repository.delete_camera(camera_id)
            if success:
                return True, f"Camera {camera_id} deleted successfully"
            else:
                return False, f"Camera {camera_id} not found or could not be deleted"
        except Exception as e:
            raise CameraError(f"Error deleting camera {camera_id}: {str(e)}")
    
