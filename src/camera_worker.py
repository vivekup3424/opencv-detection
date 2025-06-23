#!/usr/bin/env python3
"""
Optimized individual camera worker that handles motion detection and recording
"""

import time
from motion_detector import MotionDetector
from video_recorder import VideoRecorder
from utils import cleanup_old_recordings, create_recording_directory, generate_chunk_filename
from config import (
    DEFAULT_THRESHOLD, DEFAULT_MIN_AREA, DEFAULT_POST_BUFFER_SECONDS,
    CHUNK_DURATION_SECONDS, MAX_RECONNECT_ATTEMPTS, RECONNECT_DELAY
)


class CameraWorker:
    """Optimized camera worker that uses MotionDetector's built-in stream handling"""

    def __init__(self, camera_id, rtsp_url, websocket_server=None,
                 threshold=DEFAULT_THRESHOLD, min_area=DEFAULT_MIN_AREA,
                 post_buffer_seconds=DEFAULT_POST_BUFFER_SECONDS):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.websocket_server = websocket_server
        self.threshold = threshold
        self.min_area = min_area
        self.post_buffer_seconds = post_buffer_seconds
        self.thread_name = f"[{camera_id}]"

        # Components - motion detector initialized on connection
        self.motion_detector = None
        self.video_recorder = VideoRecorder()

        # State variables
        self.motion_detected = False
        self.motion_start_time = None
        self.chunk_start_time = None
        self.chunk_counter = 0
        self.current_chunk_filename = None
        self.recording_dir = None
        self.reconnect_count = 0
    
    def _connect_with_retry(self, stop_event):
        """Connect to motion detector with retry logic"""
        attempt = 0
        while attempt < MAX_RECONNECT_ATTEMPTS:
            if stop_event and stop_event.is_set():
                print(f"{self.thread_name} Connection cancelled by stop event")
                return False
            
            attempt += 1
            print(f"{self.thread_name} Connection attempt {attempt}/{MAX_RECONNECT_ATTEMPTS}")
            
            try:
                # Create motion detector with built-in RTSP handling
                self.motion_detector = MotionDetector(
                    self.rtsp_url, 
                    self.threshold, 
                    self.min_area, 
                    self.post_buffer_seconds
                )
                
                # Initialize from stream
                self.motion_detector.initialize_from_stream()
                print(f"{self.thread_name} Successfully connected via MotionDetector")
                self.reconnect_count = 0
                return True
                    
            except Exception as e:
                print(f"{self.thread_name} Connection error: {e}")
                self._cleanup_motion_detector()
            
            if attempt < MAX_RECONNECT_ATTEMPTS:
                print(f"{self.thread_name} Waiting {RECONNECT_DELAY}s before retry...")
                time.sleep(RECONNECT_DELAY)
        
        print(f"{self.thread_name} Failed to connect after {MAX_RECONNECT_ATTEMPTS} attempts")
        return False

    def _cleanup_motion_detector(self):
        """Clean up motion detector resources"""
        if self.motion_detector:
            try:
                self.motion_detector.release_stream()
            except:
                pass
            self.motion_detector = None
    
    def run(self, stop_event):
        """Main camera worker loop"""
        print(f"{self.thread_name} Starting optimized camera worker...")
        
        # Setup recording directory and cleanup
        self.recording_dir = create_recording_directory(self.camera_id)
        cleanup_old_recordings(self.camera_id)
        
        while True:
            if stop_event and stop_event.is_set():
                print(f"{self.thread_name} Stopping camera worker...")
                break
            
            # Connect with retry logic
            if not self._connect_with_retry(stop_event):
                print(f"{self.thread_name} Could not establish connection, exiting...")
                break
            
            if self.reconnect_count > 0:
                print(f"{self.thread_name} Successfully reconnected after {self.reconnect_count} attempts")
            
            try:
                # Run main processing loop
                connection_lost = self._main_loop(stop_event)
                
                if connection_lost and not (stop_event and stop_event.is_set()):
                    print(f"{self.thread_name} Connection lost, attempting to reconnect...")
                    self._reset_state()
                    self.reconnect_count += 1
                    if self.reconnect_count >= MAX_RECONNECT_ATTEMPTS:
                        print(f"{self.thread_name} Max reconnection attempts reached, exiting...")
                        break
                    time.sleep(RECONNECT_DELAY)
                    continue
                else:
                    break
                    
            except KeyboardInterrupt:
                print(f"{self.thread_name} Interrupted by user")
                break
            except Exception as e:
                print(f"{self.thread_name} Error: {e}")
                self.reconnect_count += 1
                if self.reconnect_count >= MAX_RECONNECT_ATTEMPTS:
                    break
                time.sleep(RECONNECT_DELAY)
                continue
            finally:
                self._cleanup()
    
    def _main_loop(self, stop_event):
        """Optimized main processing loop using MotionDetector's stream handling"""
        while True:
            if stop_event and stop_event.is_set():
                return False  # Normal exit
            
            try:
                # Single call for frame reading and motion detection
                frame = self.motion_detector.read_next_frame()
                motion_detected = self.motion_detector.detect_motion(frame)
                
                # Check recording process health
                if self.motion_detected and self.video_recorder.is_recording():
                    if not self.video_recorder.is_process_alive():
                        print(f"{self.thread_name} FFmpeg process ended unexpectedly")
                        self.video_recorder.recording_process = None
                
                # Handle motion state changes
                self._handle_motion_state(motion_detected)
                
                # Use adaptive sleep from motion detector
                sleep_duration = self.motion_detector.get_adaptive_sleep_duration(motion_detected)
                time.sleep(sleep_duration)
                
            except RuntimeError:
                return True  # Connection lost
            except Exception as e:
                print(f"{self.thread_name} Unexpected error: {e}")
                return True
        
        return False
    
    def _handle_motion_state(self, motion_detected):
        """Handle motion state transitions - simplified logic"""
        current_time = time.time()
        
        # Motion state transitions
        if motion_detected and not self.motion_detected:
            # Motion started
            self._start_recording()
        elif motion_detected and self.motion_detected:
            # Motion continues - check for chunk duration
            if (self.video_recorder.is_recording() and 
                current_time - self.chunk_start_time >= CHUNK_DURATION_SECONDS):
                self._start_new_chunk()
        elif not motion_detected and self.motion_detected:
            # Motion stopped
            self._stop_recording()
    
    def _start_recording(self):
        """Start recording when motion begins"""
        self.motion_detected = True
        current_time = time.time()
        self.motion_start_time = self.chunk_start_time = current_time
        self.chunk_counter = 1
        
        self.current_chunk_filename = generate_chunk_filename(
            self.recording_dir, self.camera_id, self.chunk_counter
        )
        
        print(f"{self.thread_name} Motion started. Recording chunk {self.chunk_counter}: "
              f"{self.current_chunk_filename}")
        
        self.video_recorder.start_recording(self.current_chunk_filename, self.rtsp_url)
        
        # WebSocket notification
        if self.websocket_server:
            absolute_path = str(self.current_chunk_filename.absolute())
            self.websocket_server.handle_motion_detection_event(
                self.camera_id, absolute_path, True
            )
    
    def _start_new_chunk(self):
        """Start a new recording chunk"""
        print(f"{self.thread_name} Starting new chunk {self.chunk_counter + 1}...")
        
        self.video_recorder.stop_recording()
        
        self.chunk_counter += 1
        self.chunk_start_time = time.time()
        self.current_chunk_filename = generate_chunk_filename(
            self.recording_dir, self.camera_id, self.chunk_counter
        )
        
        self.video_recorder.start_recording(self.current_chunk_filename, self.rtsp_url)
    
    def _stop_recording(self):
        """Stop recording when motion ends"""
        print(f"{self.thread_name} Motion ended. Stopping recording...")
        
        self.motion_detected = False
        self.video_recorder.stop_recording()
        
        # WebSocket notification
        if self.websocket_server:
            try:
                absolute_path = str(self.current_chunk_filename.absolute()) if self.current_chunk_filename else None
                self.websocket_server.handle_motion_detection_event(
                    self.camera_id, absolute_path, False
                )
            except Exception as e:
                print(f"WebSocket error: {e}")
        
        total_chunks = self.chunk_counter
        self.chunk_counter = 0
        self.chunk_start_time = None
        print(f"{self.thread_name} Recording completed with {total_chunks} chunk(s)")
    
    def _reset_state(self):
        """Reset state for reconnection"""
        print(f"{self.thread_name} Resetting state...")
        
        # Stop recording
        if self.video_recorder.is_recording():
            self.video_recorder.stop_recording()
        
        # Reset state
        self.motion_detected = False
        self.motion_start_time = None
        self.chunk_start_time = None
        self.chunk_counter = 0
        self.current_chunk_filename = None
        
        # Clean up motion detector
        self._cleanup_motion_detector()
        
        print(f"{self.thread_name} State reset completed")
    
    def _cleanup(self):
        """Cleanup all resources"""
        print(f"{self.thread_name} Cleaning up...")
        self.video_recorder.stop_recording()
        self._cleanup_motion_detector()
        print(f"{self.thread_name} Cleanup completed")
