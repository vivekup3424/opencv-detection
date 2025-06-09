"""Motion detection repository interface."""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import numpy as np


class IMotionDetectionRepository(ABC):
    """Interface for motion detection operations."""
    
    @abstractmethod
    def initialize_from_frame(self, frame: np.ndarray) -> None:
        """Initialize motion detection with the first frame."""
        pass
    
    @abstractmethod
    def detect_motion(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Detect motion in the given frame.
        
        Returns:
            Tuple of (motion_detected: bool, motion_mask: Optional[np.ndarray])
        """
        pass
    
    @abstractmethod
    def should_skip_frame(self) -> bool:
        """Determine if the current frame should be skipped for optimization."""
        pass
    
    @abstractmethod
    def get_adaptive_sleep_time(self, motion_detected: bool) -> float:
        """Get the adaptive sleep time based on motion detection status."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> dict:
        """Get motion detection statistics."""
        pass
