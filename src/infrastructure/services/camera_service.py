"""Camera service implementation."""

import cv2
import time
import threading
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.domain.repositories.camera_repository import ICameraRepository
from src.domain.repositories.motion_detection_repository import IMotionDetectionRepository
from src.domain.repositories.video_recording_repository import IVideoRecordingRepository
from src.core.config.settings import app_config
from src.core.utils.file_utils import ensure_directory_exists
from src.core.utils.datetime_utils import utc_now


class CameraWorker:
    """Individual camera worker that handles motion detection and recording."""
    
    def __init__(self, 
                 camera_id: str, 
                 rtsp_url: str,
                 motion_detection_service: IMotionDetectionRepository,
                 video_recording_service: IVideoRecordingRepository):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.motion_detection_service = motion_detection_service
        self.video_recording_service = video_recording_service
        self.thread_name = f"[{camera_id}]"
        
        # Motion state
        self.motion_detected = False
        self.last_motion_time = 0
        self.motion_start_time = 0
        self.chunk_start_time = 0
        self.chunk_counter = 0
        
        # Configuration
        self.post_buffer_seconds = app_config.motion_detection.post_buffer_seconds
        self.chunk_duration_seconds = app_config.recording.chunk_duration_seconds
        
        # Recording directory
        self.recording_dir = Path(app_config.recording.recordings_dir) / camera_id
        ensure_directory_exists(str(self.recording_dir))
    
    def run(self, stop_event: threading.Event):
        """Main worker loop."""
        print(f"{self.thread_name} Starting camera worker...")
        
        # Cleanup old recordings
        self.video_recording_service.cleanup_old_recordings(self.camera_id)
        
        # Initialize capture
        cap = cv2.VideoCapture(self.rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, app_config.performance.buffer_size)
        time.sleep(2)
        
        if not cap.isOpened():
            print(f"{self.thread_name} Error: Could not open RTSP stream")
            return
        
        # Get initial frame
        ret = None
        for _ in range(app_config.performance.max_init_frames):
            ret, frame1 = cap.read()
            if ret:
                break
            time.sleep(app_config.performance.init_frame_wait)
        
        if not ret:
            print(f"{self.thread_name} Error: Could not get initial frame")
            cap.release()
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS) or app_config.motion_detection.fps
        height, width, _ = frame1.shape
        print(f"{self.thread_name} Initialized: {width}x{height} at {fps} FPS")
        
        # Initialize motion detector
        self.motion_detection_service.initialize_from_frame(frame1)
        
        try:
            self._main_loop(cap, stop_event)
        except KeyboardInterrupt:
            print(f"{self.thread_name} Interrupted by user")
        except Exception as e:
            print(f"{self.thread_name} Error: {e}")
        finally:
            self._cleanup(cap)
    
    def _main_loop(self, cap, stop_event):
        """Main processing loop."""
        while True:
            if stop_event and stop_event.is_set():
                print(f"{self.thread_name} Stopping camera thread...")
                break
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check if recording process is still running
            if (self.motion_detected and 
                self.video_recording_service.is_recording(self.camera_id)):
                if not self.video_recording_service.is_recording(self.camera_id):
                    print(f"{self.thread_name} Recording process ended unexpectedly")
            
            # Motion detection
            motion_this_frame, _ = self.motion_detection_service.detect_motion(frame)
            
            if not self.motion_detection_service.should_skip_frame():
                self._handle_motion_detection(motion_this_frame)
            
            # Adaptive sleep
            sleep_duration = self.motion_detection_service.get_adaptive_sleep_time(self.motion_detected)
            time.sleep(sleep_duration)
            
            # Print performance stats periodically
            if self.motion_detection_service.should_print_stats():
                stats = self.motion_detection_service.get_statistics()
                print(f"{self.thread_name} Performance: {stats['fps_actual']:.1f} FPS total, "
                      f"{stats['detection_fps']:.1f} detection FPS")
    
    def _handle_motion_detection(self, motion_this_frame: bool):
        """Handle motion detection logic."""
        current_time = time.time()
        
        if motion_this_frame:
            if not self.motion_detected:
                # Motion just started - begin recording
                self._start_motion_recording()
            else:
                # Motion continues - update last motion time
                self.last_motion_time = current_time
                
                # Check if current chunk has reached duration limit
                if (self.video_recording_service.is_recording(self.camera_id) and 
                    current_time - self.chunk_start_time >= self.chunk_duration_seconds):
                    self._start_new_chunk()
        else:
            # Check if motion has stopped for post_buffer_seconds
            if (self.motion_detected and 
                current_time - self.last_motion_time > self.post_buffer_seconds):
                self._stop_motion_recording()
    
    def _start_motion_recording(self):
        """Start recording when motion is detected."""
        self.motion_detected = True
        current_time = time.time()
        self.motion_start_time = self.last_motion_time = self.chunk_start_time = current_time
        self.chunk_counter = 1
        
        print(f"{self.thread_name} Motion detected. Starting recording...")
        
        # Start recording
        success = self.video_recording_service.start_recording(self.camera_id, self.rtsp_url)
        if not success:
            print(f"{self.thread_name} Failed to start recording")
    
    def _start_new_chunk(self):
        """Start a new recording chunk."""
        print(f"{self.thread_name} Chunk {self.chunk_counter} duration reached. Starting new chunk...")
        
        # Stop current recording
        self.video_recording_service.stop_recording(self.camera_id)
        
        # Start new chunk
        self.chunk_counter += 1
        self.chunk_start_time = time.time()
        
        print(f"{self.thread_name} Recording chunk {self.chunk_counter}")
        self.video_recording_service.start_recording(self.camera_id, self.rtsp_url)
    
    def _stop_motion_recording(self):
        """Stop recording when motion ends."""
        print(f"{self.thread_name} Motion stopped. Stopping recording after "
              f"{self.post_buffer_seconds}s post-buffer...")
        
        # Stop recording
        self.motion_detected = False
        self.video_recording_service.stop_recording(self.camera_id)
    
    def _cleanup(self, cap):
        """Cleanup resources."""
        if self.video_recording_service.is_recording(self.camera_id):
            self.video_recording_service.stop_recording(self.camera_id)
        
        cap.release()
        print(f"{self.thread_name} Camera worker stopped")


class CameraService(ICameraServiceRepository):
    """Thread-safe camera management service."""
    
    def __init__(self, 
                 motion_detection_service: IMotionDetectionRepository,
                 video_recording_service: IVideoRecordingRepository):
        self.motion_detection_service = motion_detection_service
        self.video_recording_service = video_recording_service
        self.cameras = {}  # camera_id -> {"worker": worker, "thread": thread, "stop_event": stop_event}
        self.lock = threading.Lock()
    
    def add_camera(self, camera_id: str, rtsp_url: str) -> Tuple[bool, str]:
        """Add and start monitoring a camera."""
        with self.lock:
            if camera_id in self.cameras:
                return False, f"Camera {camera_id} already exists"
            
            try:
                stop_event = threading.Event()
                worker = CameraWorker(
                    camera_id, 
                    rtsp_url, 
                    self.motion_detection_service,
                    self.video_recording_service
                )
                
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
                return True, f"Camera {camera_id} started successfully"
                
            except Exception as e:
                return False, f"Failed to start camera {camera_id}: {str(e)}"
    
    def delete_camera(self, camera_id: str) -> Tuple[bool, str]:
        """Stop and remove a camera."""
        return self.stop_camera(camera_id)
    
    def stop_camera(self, camera_id: str) -> Tuple[bool, str]:
        """Stop a camera without removing it."""
        with self.lock:
            camera_info = self.cameras.get(camera_id)
            if not camera_info:
                return False, f"Camera {camera_id} not found"
            
            try:
                # Signal the thread to stop
                camera_info["stop_event"].set()
                
                # Wait for thread to finish
                camera_info["thread"].join(timeout=10)
                
                # Remove from active cameras
                del self.cameras[camera_id]
                
                return True, f"Camera {camera_id} stopped successfully"
                
            except Exception as e:
                return False, f"Error stopping camera {camera_id}: {str(e)}"
    
    def get_camera_status(self, camera_id: str) -> Optional[Dict]:
        """Get status information for a specific camera."""
        with self.lock:
            camera_info = self.cameras.get(camera_id)
            if not camera_info:
                return None
            
            return {
                "camera_id": camera_id,
                "rtsp_url": camera_info["rtsp_url"],
                "start_time": camera_info["start_time"],
                "is_active": camera_info["thread"].is_alive(),
                "is_recording": self.video_recording_service.is_recording(camera_id)
            }
    
    def list_cameras(self) -> List[Dict]:
        """List all cameras with their status."""
        with self.lock:
            return [self.get_camera_status(camera_id) 
                    for camera_id in self.cameras.keys()]
    
    def stop_all_cameras(self) -> int:
        """Stop all cameras. Returns number of cameras stopped."""
        camera_ids = list(self.cameras.keys())
        stopped_count = 0
        
        for camera_id in camera_ids:
            success, _ = self.stop_camera(camera_id)
            if success:
                stopped_count += 1
        
        return stopped_count
    
    def is_camera_active(self, camera_id: str) -> bool:
        """Check if a camera is currently active."""
        with self.lock:
            camera_info = self.cameras.get(camera_id)
            return camera_info is not None and camera_info["thread"].is_alive()
