#!/usr/bin/env python3
"""
Motion detection functionality
"""

import cv2
import time
from config import (
    MOTION_DETECT_RESOLUTION, GAUSSIAN_KERNEL, SKIP_FRAMES,
    ADAPTIVE_SLEEP_NO_MOTION, ADAPTIVE_SLEEP_MOTION
)


class MotionDetector:
    """Handles motion detection logic"""
    
    def __init__(self, threshold=30, min_area=800):
        self.threshold = threshold
        self.min_area = min_area
        self.frame_count = 0
        self.frames_processed_for_detection = 0
        self.consecutive_no_motion_frames = 0
        self.previous_gray = None
        self.start_time = time.time()
        self.last_stats_time = time.time()
    
    def initialize_from_frame(self, frame):
        """Initialize motion detection with the first frame"""
        self.previous_gray = cv2.GaussianBlur(
            cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), MOTION_DETECT_RESOLUTION),
            GAUSSIAN_KERNEL, 0
        )
    
    def detect_motion(self, frame):
        """
        Detect motion in the current frame
        Returns True if motion is detected, False otherwise
        """
        self.frame_count += 1
        
        # Only process every skip_frames frame for motion detection
        if self.frame_count % SKIP_FRAMES != 0:
            return None  # Skip this frame
        
        self.frames_processed_for_detection += 1
        
        # Convert frame to grayscale and resize for motion detection
        current_gray = cv2.GaussianBlur(
            cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), MOTION_DETECT_RESOLUTION),
            GAUSSIAN_KERNEL, 0
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
        
        return motion_detected
    
    def get_adaptive_sleep_duration(self, motion_detected):
        """Get adaptive sleep duration based on motion state"""
        if motion_detected:
            return ADAPTIVE_SLEEP_MOTION
        else:
            # Sleep longer if no motion for extended period
            multiplier = 3 if self.consecutive_no_motion_frames > 50 else 1
            return ADAPTIVE_SLEEP_NO_MOTION * multiplier
    
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
