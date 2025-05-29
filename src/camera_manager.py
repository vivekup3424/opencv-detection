#!/usr/bin/env python3
"""
Camera management with threading support
"""

import cv2
import time
import threading
from motion_detector import MotionDetector
from video_recorder import VideoRecorder
from utils import cleanup_old_recordings, create_recording_directory, generate_chunk_filename
from config import (
    DEFAULT_THRESHOLD, DEFAULT_MIN_AREA, SKIP_FRAMES, DEFAULT_POST_BUFFER_SECONDS,
    BUFFER_SIZE, MAX_INIT_FRAMES, INIT_FRAME_WAIT, DEFAULT_FPS, CHUNK_DURATION_SECONDS
)


class CameraWorker:
    """Individual camera worker that handles motion detection and recording"""
    
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
        
        # Initialize components
        self.motion_detector = MotionDetector(threshold, min_area)
        self.video_recorder = VideoRecorder()
        
        # State variables
        self.motion_detected = False
        self.motion_start_time = None
        self.last_motion_time = None
        self.chunk_start_time = None
        self.chunk_counter = 0
        self.current_chunk_filename = None
        self.recording_dir = None
    
    def run(self, stop_event):
        """Main camera worker loop"""
        print(f"{self.thread_name} Connecting to RTSP stream: {self.rtsp_url}")
        
        # Setup recording directory and cleanup
        self.recording_dir = create_recording_directory(self.camera_id)
        cleanup_old_recordings(self.camera_id)
        
        # Initialize capture
        cap = cv2.VideoCapture(self.rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
        time.sleep(2)
        
        if not cap.isOpened():
            print(f"{self.thread_name} Error: Could not open RTSP stream")
            return
        
        # Get initial frame
        ret = None
        for _ in range(MAX_INIT_FRAMES):
            ret, frame1 = cap.read()
            if ret:
                break
            time.sleep(INIT_FRAME_WAIT)
        
        if not ret:
            print(f"{self.thread_name} Error: Could not get initial frame")
            cap.release()
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
        height, width, _ = frame1.shape
        print(f"{self.thread_name} Initialized: {width}x{height} at {fps} FPS")
        
        # Initialize motion detector
        self.motion_detector.initialize_from_frame(frame1)
        
        try:
            self._main_loop(cap, stop_event)
        except KeyboardInterrupt:
            print(f"{self.thread_name} Interrupted by user")
        except Exception as e:
            print(f"{self.thread_name} Error: {e}")
        finally:
            self._cleanup(cap)
    
    def _main_loop(self, cap, stop_event):
        """Main processing loop"""
        while True:
            if stop_event and stop_event.is_set():
                print(f"{self.thread_name} Stopping camera thread...")
                break
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check if recording process is still running
            if self.motion_detected and self.video_recorder.is_recording():
                if not self.video_recorder.is_process_alive():
                    print(f"{self.thread_name} FFmpeg process ended unexpectedly")
                    self.video_recorder.recording_process = None
            
            # Motion detection
            motion_this_frame = self.motion_detector.detect_motion(frame)
            
            if motion_this_frame is not None:  # Only process when detection occurred
                self._handle_motion_detection(motion_this_frame)
            
            # Adaptive sleep
            sleep_duration = self.motion_detector.get_adaptive_sleep_duration(self.motion_detected)
            time.sleep(sleep_duration)
            
            # Print performance stats periodically
            if self.motion_detector.should_print_stats():
                stats = self.motion_detector.get_performance_stats()
                print(f"{self.thread_name} Performance: {stats['fps_actual']:.1f} FPS total, "
                      f"{stats['detection_fps']:.1f} detection FPS")
    
    def _handle_motion_detection(self, motion_this_frame):
        """Handle motion detection logic"""
        current_time = time.time()
        
        if motion_this_frame:
            if not self.motion_detected:
                # Motion just started - begin recording
                self._start_motion_recording()
            else:
                # Motion continues - update last motion time
                self.last_motion_time = current_time
                
                # Check if current chunk has reached duration limit
                if (self.video_recorder.is_recording() and 
                    current_time - self.chunk_start_time >= CHUNK_DURATION_SECONDS):
                    self._start_new_chunk()
        else:
            # Check if motion has stopped for post_buffer_seconds
            if (self.motion_detected and 
                current_time - self.last_motion_time > self.post_buffer_seconds):
                self._stop_motion_recording()
    
    def _start_motion_recording(self):
        """Start recording when motion is detected"""
        self.motion_detected = True
        current_time = time.time()
        self.motion_start_time = self.last_motion_time = self.chunk_start_time = current_time
        self.chunk_counter = 1
        
        self.current_chunk_filename = generate_chunk_filename(
            self.recording_dir, self.camera_id, self.chunk_counter
        )
        
        print(f"{self.thread_name} Motion detected. Recording chunk {self.chunk_counter}: "
              f"{self.current_chunk_filename}")
        
        # Start ffmpeg recording
        self.video_recorder.start_recording(self.current_chunk_filename, self.rtsp_url)
        
        # Send WebSocket event for motion start
        if self.websocket_server:
            absolute_path = str(self.current_chunk_filename.absolute())
            self.websocket_server.handle_motion_detection_event(
                self.camera_id, absolute_path, True
            )
    
    def _start_new_chunk(self):
        """Start a new recording chunk"""
        print(f"{self.thread_name} Chunk {self.chunk_counter} duration reached. Starting new chunk...")
        
        # Close current recording
        self.video_recorder.stop_recording()
        
        # Start new chunk
        self.chunk_counter += 1
        self.chunk_start_time = time.time()
        self.current_chunk_filename = generate_chunk_filename(
            self.recording_dir, self.camera_id, self.chunk_counter
        )
        
        print(f"{self.thread_name} Recording chunk {self.chunk_counter}: {self.current_chunk_filename}")
        self.video_recorder.start_recording(self.current_chunk_filename, self.rtsp_url)
    
    def _stop_motion_recording(self):
        """Stop recording when motion ends"""
        print(f"{self.thread_name} Motion stopped. Stopping recording after "
              f"{self.post_buffer_seconds}s post-buffer...")
        
        # Stop recording
        self.motion_detected = False
        self.video_recorder.stop_recording()
        
        # Send motion end event to WebSocket clients
        if self.websocket_server:
            try:
                absolute_path = str(self.current_chunk_filename.absolute()) if self.current_chunk_filename else None
                self.websocket_server.handle_motion_detection_event(
                    self.camera_id, absolute_path, False
                )
            except Exception as e:
                print(f"Error sending WebSocket motion end event: {e}")
        
        total_chunks = self.chunk_counter
        self.chunk_start_time = None
        self.chunk_counter = 0
        print(f"{self.thread_name} Recording session completed with {total_chunks} chunk(s)")
    
    def _cleanup(self, cap):
        """Cleanup resources"""
        print(f"{self.thread_name} Cleaning up...")
        self.video_recorder.stop_recording()
        cap.release()
        print(f"{self.thread_name} Done.")


class CameraManager:
    """Thread-safe camera management"""
    
    def __init__(self, websocket_server=None):
        self.cameras = {}  # camera_id -> {"worker": worker, "thread": thread, "stop_event": stop_event}
        self.lock = threading.Lock()
        self.websocket_server = websocket_server
    
    def add_camera(self, camera_id, rtsp_url):
        """Add and start monitoring a camera"""
        with self.lock:
            if camera_id in self.cameras:
                return False, f"Camera {camera_id} already exists"
            
            try:
                stop_event = threading.Event()
                worker = CameraWorker(camera_id, rtsp_url, self.websocket_server)
                
                thread = threading.Thread(
                    target=worker.run,
                    args=(stop_event,),
                    name=f"Camera-{camera_id}",
                    daemon=True
                )
                
                self.cameras[camera_id] = {
                    "worker": worker,
                    "thread": thread,
                    "stop_event": stop_event,
                    "rtsp_url": rtsp_url,
                    "start_time": time.time()
                }
                
                thread.start()
                print(f"Started monitoring camera: {camera_id}")
                return True, f"Camera {camera_id} started successfully"
                
            except Exception as e:
                return False, f"Failed to start camera {camera_id}: {str(e)}"
    
    def delete_camera(self, camera_id):
        """Stop and remove a camera"""
        with self.lock:
            if camera_id not in self.cameras:
                return False, f"Camera {camera_id} not found"
            
            try:
                camera_info = self.cameras[camera_id]
                stop_event = camera_info["stop_event"]
                thread = camera_info["thread"]
                
                # Signal the thread to stop
                stop_event.set()
                
                # Wait for thread to finish (with timeout)
                thread.join(timeout=10)
                
                if thread.is_alive():
                    print(f"Warning: Camera {camera_id} thread did not stop gracefully")
                
                del self.cameras[camera_id]
                print(f"Stopped monitoring camera: {camera_id}")
                return True, f"Camera {camera_id} stopped successfully"
                
            except Exception as e:
                return False, f"Failed to stop camera {camera_id}: {str(e)}"
    
    def list_cameras(self):
        """Get list of active cameras"""
        with self.lock:
            camera_list = []
            for camera_id, info in self.cameras.items():
                camera_list.append({
                    "camera_id": camera_id,
                    "rtsp_url": info["rtsp_url"],
                    "status": "running" if info["thread"].is_alive() else "stopped",
                    "uptime_seconds": int(time.time() - info["start_time"])
                })
            return camera_list
    
    def get_camera_status(self, camera_id):
        """Get status of specific camera"""
        with self.lock:
            if camera_id not in self.cameras:
                return None
            
            info = self.cameras[camera_id]
            return {
                "camera_id": camera_id,
                "rtsp_url": info["rtsp_url"],
                "status": "running" if info["thread"].is_alive() else "stopped",
                "uptime_seconds": int(time.time() - info["start_time"])
            }
    
    def stop_all_cameras(self):
        """Stop all cameras gracefully"""
        with self.lock:
            for camera_id in list(self.cameras.keys()):
                self.delete_camera(camera_id)
