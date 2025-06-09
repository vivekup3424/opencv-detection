"""Video recording repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class IVideoRecordingRepository(ABC):
    """Interface for video recording operations."""
    
    @abstractmethod
    def start_recording(self, camera_id: str) -> bool:
        """Start recording for the specified camera."""
        pass
    
    @abstractmethod
    def stop_recording(self, camera_id: str) -> bool:
        """Stop recording for the specified camera."""
        pass
    
    @abstractmethod
    def write_frame(self, camera_id: str, frame: np.ndarray, timestamp: Optional[float] = None) -> bool:
        """Write a frame to the recording."""
        pass
    
    @abstractmethod
    def is_recording(self, camera_id: str) -> bool:
        """Check if recording is active for the camera."""
        pass
    
    @abstractmethod
    def get_current_filename(self, camera_id: str) -> Optional[str]:
        """Get the current recording filename for the camera."""
        pass
    
    @abstractmethod
    def cleanup_old_recordings(self, camera_id: str, days: int = None) -> int:
        """Clean up old recordings for the camera. Returns number of files deleted."""
        pass
