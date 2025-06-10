"""Motion detection service implementation using OpenCV."""

import cv2
import numpy as np
from typing import Tuple

from src.core.config.settings import app_config


class MotionDetectionService:
    """Simple OpenCV-based motion detection."""
    
    def __init__(self, threshold: int = None, min_area: int = None):
        self.threshold = threshold or app_config.motion_detection.threshold
        self.min_area = min_area or app_config.motion_detection.min_area
        self.frame_count = 0
        self.previous_gray = None
        self.skip_frames = app_config.motion_detection.skip_frames
    
    def initialize_from_frame(self, frame: np.ndarray) -> None:
        """Initialize motion detection with the first frame."""
        self.previous_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    def detect_motion(self, frame: np.ndarray) -> Tuple[bool, None]:
        """Detect motion in the current frame."""
        self.frame_count += 1
        
        # Skip frames for performance
        if self.frame_count % self.skip_frames != 0:
            return False, None
        
        # Convert to grayscale
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference
        diff = cv2.absdiff(self.previous_gray, current_gray)
        thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check for motion
        motion_detected = any(cv2.contourArea(c) >= self.min_area for c in contours)
        
        # Update previous frame
        self.previous_gray = current_gray
        
        return motion_detected, None
    
    def should_skip_frame(self) -> bool:
        """Check if current frame should be skipped."""
        return self.frame_count % self.skip_frames != 0
