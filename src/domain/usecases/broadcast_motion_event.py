"""Broadcast motion event use case for real-time notifications."""

from typing import Optional

from src.domain.entities.motion_event import MotionEvent
from src.domain.repositories.camera_repository import ICameraRepository
from src.core.utils.datetime_utils import utc_now
from src.core.errors.exceptions import ValidationError, CameraError


class BroadcastMotionEventUseCase:
    """
    Use case for broadcasting motion detection events.
    This handles real-time notifications when motion is detected or stops.
    """
    
    def __init__(self, camera_repository: ICameraRepository):
        self.camera_repository = camera_repository
    
    async def broadcast_motion_start(self, 
                                   camera_id: str, 
                                   video_path: Optional[str] = None) -> bool:
        """
        Broadcast motion detection start event.
        
        Args:
            camera_id: The ID of the camera that detected motion
            video_path: Optional path to the recorded video file
            
        Returns:
            True if broadcast was successful, False otherwise
            
        Raises:
            ValidationError: If camera_id is invalid
            CameraError: If broadcasting fails
        """
        if not camera_id or not camera_id.strip():
            raise ValidationError("Camera ID cannot be empty")
        
        try:
            motion_event = MotionEvent(
                camera_id=camera_id.strip(),
                motion_detected=True,
                timestamp=utc_now(),
                video_path=video_path
            )
            
            return await self.camera_repository.broadcast_motion_event(motion_event)
        except Exception as e:
            raise CameraError(f"Failed to broadcast motion start event for {camera_id}: {str(e)}")
    
    async def broadcast_motion_stop(self, 
                                  camera_id: str, 
                                  video_path: Optional[str] = None) -> bool:
        """
        Broadcast motion detection stop event.
        
        Args:
            camera_id: The ID of the camera that stopped detecting motion
            video_path: Optional path to the final recorded video file
            
        Returns:
            True if broadcast was successful, False otherwise
            
        Raises:
            ValidationError: If camera_id is invalid
            CameraError: If broadcasting fails
        """
        if not camera_id or not camera_id.strip():
            raise ValidationError("Camera ID cannot be empty")
        
        try:
            motion_event = MotionEvent(
                camera_id=camera_id.strip(),
                motion_detected=False,
                timestamp=utc_now(),
                video_path=video_path
            )
            
            return await self.camera_repository.broadcast_motion_event(motion_event)
        except Exception as e:
            raise CameraError(f"Failed to broadcast motion stop event for {camera_id}: {str(e)}")
    
    async def broadcast_motion_event(self, 
                                   camera_id: str, 
                                   motion_detected: bool,
                                   video_path: Optional[str] = None) -> bool:
        """
        Generic method to broadcast motion events.
        
        Args:
            camera_id: The ID of the camera
            motion_detected: Whether motion was detected (True) or stopped (False)
            video_path: Optional path to the recorded video file
            
        Returns:
            True if broadcast was successful, False otherwise
        """
        if motion_detected:
            return await self.broadcast_motion_start(camera_id, video_path)
        else:
            return await self.broadcast_motion_stop(camera_id, video_path)
