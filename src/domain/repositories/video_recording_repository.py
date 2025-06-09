"""Video recording repository interface."""

from abc import ABC, abstractmethod
from typing import Optional


class IVideoRecordingRepository(ABC):
    """Interface for video recording operations."""
    
    @abstractmethod
    def start_recording(self, camera_id: str, rtsp_url: str) -> bool:
        """Start recording for the specified camera.
        
        Args:
            camera_id: Unique identifier for the camera
            rtsp_url: RTSP stream URL for the camera
            
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def stop_recording(self, camera_id: str) -> bool:
        """Stop recording for the specified camera.
        
        Args:
            camera_id: Unique identifier for the camera
            
        Returns:
            bool: True if recording stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def is_recording(self, camera_id: str) -> bool:
        """Check if recording is active for the camera.
        
        Args:
            camera_id: Unique identifier for the camera
            
        Returns:
            bool: True if recording is active, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup_old_recordings(self, camera_id: str, days: int = None) -> int:
        """Clean up old recordings for the camera.
        
        Args:
            camera_id: Unique identifier for the camera
            days: Number of days to keep recordings (optional)
            
        Returns:
            int: Number of files deleted
        """
        pass
