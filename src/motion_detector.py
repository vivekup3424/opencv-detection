#!/usr/bin/env python3
"""
Motion detection functionality
"""

import cv2
import time
from config import (
    DEFAULT_THRESHOLD, DEFAULT_MIN_AREA, GAUSSIAN_KERNEL, SKIP_FRAMES,
    ADAPTIVE_SLEEP_NO_MOTION, ADAPTIVE_SLEEP_MOTION, DEFAULT_POST_BUFFER_SECONDS,
    MOTION_DETECT_RESOLUTION
)


class MotionDetector:
    """Handles motion detection logic"""

    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.threshold = DEFAULT_THRESHOLD
        self.min_area = DEFAULT_MIN_AREA
        self.motion_timeout = DEFAULT_POST_BUFFER_SECONDS
        self.frame_skip = SKIP_FRAMES
        self.frame_count = 0
        self.frames_processed_for_detection = 0
        self.previous_gray = None
        self.start_time = time.time()
        self.last_stats_time = time.time()

        # Add motion state tracking
        self.motion_detected = False
        self.last_motion_time = None

        # Initialize video capture
        self.cap = cv2.VideoCapture(rtsp_url)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, MOTION_DETECT_RESOLUTION[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, MOTION_DETECT_RESOLUTION[1])
        self.cap.set(cv2.CAP_PROP_FPS, 10)

        if not self.cap.isOpened():
            raise ValueError(f"Error: Could not open RTSP stream at {rtsp_url}")

    def initialize_from_stream(self):
        """Initialize motion detection with the first frame from the stream"""
        for _ in range(50):
            ret, frame = self.cap.read()
            if ret:
                break
            time.sleep(0.1)

        if not ret:
            raise RuntimeError("Failed to get initial frame from RTSP stream")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.previous_gray = cv2.GaussianBlur(gray, GAUSSIAN_KERNEL, 0)

    def read_next_frame(self):
        """Read the next frame from the video stream"""
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from RTSP stream")
        return frame

    def release_stream(self):
        """Release the video stream"""
        self.cap.release()

    def detect_motion(self, frame):
        """
        Detect motion in the current frame
        Returns True if motion is detected, False otherwise
        """
        self.frame_count += 1

        # Only process every skip_frames frame for motion detection
        if self.frame_count % self.frame_skip != 0:
            # Return current state even when skipping frames
            return self.motion_detected

        self.frames_processed_for_detection += 1

        # Convert frame to grayscale and apply Gaussian blur
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_gray = cv2.GaussianBlur(current_gray, GAUSSIAN_KERNEL, 0)

        # Calculate difference and threshold
        frame_delta = cv2.absdiff(self.previous_gray, current_gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Check for motion - simplified like reference code
        motion_this_frame = False
        for contour in contours:
            if cv2.contourArea(contour) < self.min_area:
                continue
            motion_this_frame = True
            break

        # Update motion state with simpler logic like reference code
        current_time = time.time()
        if motion_this_frame:
            if not self.motion_detected:
                self.motion_detected = True
                print(f"Motion Detected at {current_time}")
            self.last_motion_time = current_time
        elif self.motion_detected and self.last_motion_time and (current_time - self.last_motion_time >= self.motion_timeout):
            self.motion_detected = False

        # Update previous frame for next comparison
        self.previous_gray = current_gray

        return self.motion_detected

    def get_adaptive_sleep_duration(self, motion_detected):
        """Get sleep duration based on motion state"""
        if motion_detected:
            return ADAPTIVE_SLEEP_MOTION
        else:
            return ADAPTIVE_SLEEP_NO_MOTION