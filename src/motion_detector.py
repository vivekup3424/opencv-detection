#!/usr/bin/env python3
"""
Motion detection functionality
"""

import cv2
import time
from config import (
    MOTION_DETECT_RESOLUTION, GAUSSIAN_KERNEL, SKIP_FRAMES,
    ADAPTIVE_SLEEP_NO_MOTION, ADAPTIVE_SLEEP_MOTION, DEFAULT_MOTION_TIMEOUT
)


class MotionDetector:
    """Handles motion detection logic"""
    
    def __init__(self, threshold=25, min_area=500, motion_timeout=DEFAULT_MOTION_TIMEOUT):
        self.threshold = threshold
        self.min_area = min_area
        self.motion_timeout = motion_timeout  # Add timeout parameter
        self.frame_count = 0
        self.frames_processed_for_detection = 0
        self.previous_gray = None
        self.start_time = time.time()
        self.last_stats_time = time.time()
        
        # Add motion state tracking
        self.motion_detected = False
        self.last_motion_time = None
    
    def initialize_from_frame(self, frame):
        """Initialize motion detection with the first frame"""
        # Initialize without resizing for better accuracy
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.previous_gray = cv2.GaussianBlur(gray, GAUSSIAN_KERNEL, 0)
    
    def detect_motion(self, frame):
        """
        Detect motion in the current frame
        Returns True if motion is detected, False otherwise
        """
        self.frame_count += 1
        
        # Only process every skip_frames frame for motion detection
        if self.frame_count % SKIP_FRAMES != 0:
            return None  # Skip processing, don't return cached state
        
        self.frames_processed_for_detection += 1
        
        # Convert frame to grayscale and apply Gaussian blur (no resizing for better accuracy)
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_gray = cv2.GaussianBlur(current_gray, GAUSSIAN_KERNEL, 0)
        
        # Calculate difference and threshold
        diff = cv2.absdiff(self.previous_gray, current_gray)
        thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=1)
        
        # Find contours (use copy to avoid modifying original)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check for motion - use explicit loop like reference code
        motion_this_frame = False
        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue
            motion_this_frame = True
            break
        
        # Update previous frame
        self.previous_gray = current_gray
        
        # Update motion state with simpler logic like reference code
        current_time = time.time()
        if motion_this_frame:
            if not self.motion_detected:
                self.motion_detected = True
            self.last_motion_time = current_time
        elif self.motion_detected and self.last_motion_time and (current_time - self.last_motion_time >= self.motion_timeout):
            self.motion_detected = False
        
        return self.motion_detected
    
    def get_motion_state_info(self):
        """Get detailed motion state information"""
        current_time = time.time()
        return {
            "motion_detected": self.motion_detected,
            "last_motion_time": self.last_motion_time,
            "time_since_motion": current_time - self.last_motion_time if self.last_motion_time else None,
            "motion_timeout": self.motion_timeout
        }
    
    def get_adaptive_sleep_duration(self, motion_detected):
        """Get sleep duration based on motion state"""
        if motion_detected:
            return ADAPTIVE_SLEEP_MOTION
        else:
            return ADAPTIVE_SLEEP_NO_MOTION
    
    def get_performance_stats(self):
        """Get current performance statistics"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        fps_actual = self.frame_count / elapsed if elapsed > 0 else 0
        detection_fps = self.frames_processed_for_detection / elapsed if elapsed > 0 else 0
        
        return {
            "fps_actual": fps_actual,
            "detection_fps": detection_fps,
            "elapsed_time": elapsed,
            "frames_processed": self.frame_count,
            "detection_frames": self.frames_processed_for_detection
        }
    
    def should_print_stats(self, interval_seconds=60):
        """Check if it's time to print performance statistics"""
        current_time = time.time()
        if current_time - self.last_stats_time >= interval_seconds:
            self.last_stats_time = current_time
            return True
        return False
