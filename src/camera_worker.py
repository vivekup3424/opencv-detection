#!/usr/bin/env python3
"""
Simple camera worker for motion detection and recording
"""

import time
from motion_detector import MotionDetector
from video_recorder import VideoRecorder
from utils import create_recording_directory
from config import (
    CHUNK_DURATION_SECONDS, MAX_RECONNECT_ATTEMPTS, RECONNECT_DELAY
)


class CameraWorker:
    """Simple camera worker using MotionDetector"""

    def __init__(self, camera_id, rtsp_url, websocket_server=None):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.websocket_server = websocket_server
        self.thread_name = f"[{camera_id}]"
        
        # Components
        self.motion_detector = None
        self.video_recorder = VideoRecorder()
        
        # State
        self.recording = False
        self.current_filename = None
        self.chunk_start_time = None
        self.reconnect_count = 0
    
    def run(self, stop_event):
        """Main loop with reconnection logic"""
        print(f"{self.thread_name} Starting camera worker...")
        
        # Setup recording directory
        recording_dir = create_recording_directory(self.camera_id)
        
        # Main reconnection loop
        while not (stop_event and stop_event.is_set()):
            try:
                # Connect with retry logic
                if self._connect_with_retry(stop_event):
                    # Reset reconnect count on successful connection
                    if self.reconnect_count > 0:
                        print(f"{self.thread_name} Successfully reconnected after {self.reconnect_count} attempts")
                        self.reconnect_count = 0
                    
                    # Run main processing loop
                    self._main_loop(stop_event, recording_dir)
                else:
                    print(f"{self.thread_name} Failed to connect after {MAX_RECONNECT_ATTEMPTS} attempts")
                    break
                    
            except Exception as e:
                print(f"{self.thread_name} Unexpected error: {e}")
            finally:
                self._cleanup_connection()
            
            # If we get here, connection was lost - attempt reconnection
            if not (stop_event and stop_event.is_set()):
                self.reconnect_count += 1
                print(f"{self.thread_name} Connection lost. Reconnecting in {RECONNECT_DELAY}s... (attempt {self.reconnect_count})")
                time.sleep(RECONNECT_DELAY)
        
        print(f"{self.thread_name} Camera worker stopped")
    
    def _connect_with_retry(self, stop_event):
        """Connect to motion detector with retry logic"""
        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            if stop_event and stop_event.is_set():
                return False
            
            print(f"{self.thread_name} Connection attempt {attempt}/{MAX_RECONNECT_ATTEMPTS}")
            
            try:
                self.motion_detector = MotionDetector(
                    self.rtsp_url)
                self.motion_detector.initialize_from_stream()
                print(f"{self.thread_name} Connected successfully")
                return True
                
            except Exception as e:
                print(f"{self.thread_name} Connection attempt {attempt} failed: {e}")
                if attempt < MAX_RECONNECT_ATTEMPTS:
                    time.sleep(RECONNECT_DELAY)
        
        return False
    
    def _main_loop(self, stop_event, recording_dir):
        """Main processing loop"""
        while not (stop_event and stop_event.is_set()):
            try:
                # Read frame and detect motion
                frame = self.motion_detector.read_next_frame()
                motion_detected = self.motion_detector.detect_motion(frame)
                
                # Handle motion state changes
                if motion_detected and not self.recording:
                    self._start_recording(recording_dir)
                elif motion_detected and self.recording:
                    self._check_chunk_duration(recording_dir)
                elif not motion_detected and self.recording:
                    self._stop_recording()
                
                # Sleep based on motion detector's recommendation
                sleep_duration = self.motion_detector.get_adaptive_sleep_duration(motion_detected)
                time.sleep(sleep_duration)
                
            except RuntimeError as e:
                # Stream connection error
                print(f"{self.thread_name} Stream error: {e}")
                break
            except Exception as e:
                print(f"{self.thread_name} Processing error: {e}")
                break
    
    def _start_recording(self, recording_dir):
        """Start recording with timestamp-based filename"""
        self.recording = True
        self.chunk_start_time = time.time()
        
        # Generate timestamp-based filename
        timestamp = int(self.chunk_start_time * 1000)  # milliseconds
        self.current_filename = recording_dir / f"{self.camera_id}_{timestamp}.mp4"
        
        print(f"{self.thread_name} Motion detected - Recording: {self.current_filename}")
        self.video_recorder.start_recording(self.current_filename, self.rtsp_url)
        
        # Send WebSocket event with proper format
        if self.websocket_server:
            self._send_websocket_event("start", str(self.current_filename.absolute()), timestamp)
    
    def _check_chunk_duration(self, recording_dir):
        """Check if current chunk duration exceeded, start new chunk if needed"""
        current_time = time.time()
        if current_time - self.chunk_start_time >= CHUNK_DURATION_SECONDS:
            # Stop current recording and send end event
            self._stop_current_chunk()
            # Start new recording and send start event
            self._start_recording(recording_dir)
    
    def _stop_recording(self):
        """Stop recording when motion ends"""
        print(f"{self.thread_name} Motion ended - Stopping recording")
        self._stop_current_chunk()
        self.recording = False
    
    def _stop_current_chunk(self):
        """Stop current chunk and send WebSocket end event"""
        if self.video_recorder.is_recording():
            self.video_recorder.stop_recording()
            
            # Send WebSocket end event
            if self.websocket_server and self.current_filename:
                end_time = int(time.time() * 1000)  # milliseconds
                start_time = int(self.chunk_start_time * 1000)  # milliseconds
                self._send_websocket_event("stop", str(self.current_filename.absolute()), start_time, end_time)
    
    def _send_websocket_event(self, action, video_path, start_time, end_time=None):
        """Send WebSocket event in the requested format"""
        if not self.websocket_server:
            return
            
        try:
            self.websocket_server.handle_motion_detection_event(
                self.camera_id, video_path, action, start_time, end_time
            )
            
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    def _cleanup_connection(self):
        """Cleanup motion detector connection"""
        if self.motion_detector:
            try:
                self.motion_detector.release_stream()
            except:
                pass
            self.motion_detector = None
    
    def _cleanup(self):
        """Cleanup all resources"""
        print(f"{self.thread_name} Cleaning up...")
        if self.video_recorder.is_recording():
            self.video_recorder.stop_recording()
        self._cleanup_connection()
        print(f"{self.thread_name} Cleanup completed")