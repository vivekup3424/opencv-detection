"""Motion detection service implementation using OpenCV."""

import cv2
import time
import numpy as np
from typing import Tuple, Optional

from src.core.config.settings import app_config


class MotionDetectionService:
    """OpenCV-based implementation of motion detection."""
    
    def __init__(self, threshold: int = None, min_area: int = None):
        self.threshold = threshold or app_config.motion_detection.threshold
        self.min_area = min_area or app_config.motion_detection.min_area
        self.frame_count = 0
        self.frames_processed_for_detection = 0
        self.consecutive_no_motion_frames = 0
        self.previous_gray = None
        self.start_time = time.time()
        self.last_stats_time = time.time()
        
        # Configuration from settings
        self.motion_detect_resolution = (320, 240)  # Could be moved to config
        self.gaussian_kernel = (21, 21)  # Could be moved to config
        self.skip_frames = app_config.motion_detection.skip_frames
    
    def initialize_from_frame(self, frame: np.ndarray) -> None:
        """Initialize motion detection with the first frame."""
        self.previous_gray = cv2.GaussianBlur(
            cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), self.motion_detect_resolution),
            self.gaussian_kernel, 0
        )
    
    def detect_motion(self, frame: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Detect motion in the given frame.
        
        Returns:
            Tuple of (motion_detected: bool, motion_mask: Optional[np.ndarray])
        """
        self.frame_count += 1
        
        # Only process every skip_frames frame for motion detection
        if self.should_skip_frame():
            return False, None  # Skip this frame, no motion processing
        
        self.frames_processed_for_detection += 1
        
        # Convert frame to grayscale and resize for motion detection
        current_gray = cv2.GaussianBlur(
            cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), self.motion_detect_resolution),
            self.gaussian_kernel, 0
        )
        
        # Calculate difference and threshold
        diff = cv2.absdiff(self.previous_gray, current_gray)
        thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check for motion
        motion_detected = any(cv2.contourArea(c) >= self.min_area for c in contours)
        
        if motion_detected:
            self.consecutive_no_motion_frames = 0
        else:
            self.consecutive_no_motion_frames += 1
        
        # Update previous frame
        self.previous_gray = current_gray
        
        return motion_detected, thresh
    
    def should_skip_frame(self) -> bool:
        """Determine if the current frame should be skipped for optimization."""
        return self.frame_count % self.skip_frames != 0
    
    def get_adaptive_sleep_time(self, motion_detected: bool) -> float:
        """Get the adaptive sleep time based on motion detection status."""
        if motion_detected:
            return app_config.performance.adaptive_sleep_motion
        else:
            # Sleep longer if no motion for extended period
            multiplier = 3 if self.consecutive_no_motion_frames > 50 else 1
            return app_config.performance.adaptive_sleep_no_motion * multiplier
    
    def get_statistics(self) -> dict:
        """Get motion detection statistics."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        fps_actual = self.frame_count / elapsed if elapsed > 0 else 0
        detection_fps = self.frames_processed_for_detection / elapsed if elapsed > 0 else 0
        
        return {
            "fps_actual": fps_actual,
            "detection_fps": detection_fps,
            "elapsed_time": elapsed,
            "frames_processed": self.frame_count,
            "detection_frames": self.frames_processed_for_detection,
            "consecutive_no_motion_frames": self.consecutive_no_motion_frames
        }
    
    def should_print_stats(self, interval_seconds: int = 60) -> bool:
        """Check if it's time to print performance statistics."""
        current_time = time.time()
        if current_time - self.last_stats_time >= interval_seconds:
            self.last_stats_time = current_time
            return True
        return False
