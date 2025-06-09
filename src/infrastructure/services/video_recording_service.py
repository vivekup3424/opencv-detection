"""Video recording service implementation using FFmpeg."""

import subprocess
import time
import threading
from pathlib import Path
from typing import Optional, Dict
import numpy as np

from src.domain.repositories.video_recording_repository import IVideoRecordingRepository
from src.core.config.settings import app_config
from src.core.utils.file_utils import ensure_directory_exists
from src.core.utils.datetime_utils import utc_now


class VideoRecordingService(IVideoRecordingRepository):
    """FFmpeg-based implementation of video recording."""
    
    def __init__(self):
        self._recording_processes: Dict[str, subprocess.Popen] = {}
        self._current_files: Dict[str, str] = {}
        self._lock = threading.Lock()
    
    def start_recording(self, camera_id: str, rtsp_url: str) -> bool:
        """Start recording for the specified camera."""
        with self._lock:
            if camera_id in self._recording_processes:
                return False  # Already recording
            
            try:
                # Generate output filename
                timestamp = utc_now().strftime("%H%M%S")
                date_str = utc_now().strftime("%Y-%m-%d")
                recordings_dir = Path(app_config.recording.recordings_dir) / camera_id / date_str
                ensure_directory_exists(str(recordings_dir))
                
                output_file = recordings_dir / f"motion_{timestamp}_chunk001.mp4"
                
                # Build FFmpeg command
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file
                    '-rtsp_transport', 'tcp',  # Use TCP for better reliability
                    '-i', rtsp_url,  # Input RTSP stream directly
                    '-c:v', 'libx264',  # H.264 video codec
                    '-preset', app_config.recording.ffmpeg_preset,
                    '-crf', str(app_config.recording.ffmpeg_crf),
                    '-r', str(app_config.recording.ffmpeg_fps),
                    '-s', app_config.recording.ffmpeg_resolution,
                    '-c:a', 'aac',  # AAC audio codec
                    '-b:a', app_config.recording.ffmpeg_audio_bitrate,
                    '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                    '-movflags', '+faststart',  # Move metadata to beginning for web compatibility
                    '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
                    '-threads', str(app_config.recording.ffmpeg_threads),
                    str(output_file)
                ]
                
                process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE)
                self._recording_processes[camera_id] = process
                self._current_files[camera_id] = str(output_file)
                
                return True
                
            except Exception as e:
                print(f"Error starting recording for {camera_id}: {e}")
                return False
    
    def stop_recording(self, camera_id: str) -> bool:
        """Stop recording for the specified camera."""
        with self._lock:
            process = self._recording_processes.get(camera_id)
            if not process:
                return False
            
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            except Exception as e:
                print(f"Error stopping recording for {camera_id}: {e}")
                return False
            finally:
                self._recording_processes.pop(camera_id, None)
                self._current_files.pop(camera_id, None)
            
            return True
    
    def write_frame(self, camera_id: str, frame: np.ndarray, timestamp: Optional[float] = None) -> bool:
        """
        Write a frame to the recording.
        Note: This implementation uses FFmpeg directly from RTSP, so individual frame writing 
        is not needed. This method is kept for interface compatibility.
        """
        # FFmpeg handles frame writing directly from RTSP stream
        return self.is_recording(camera_id)
    
    def is_recording(self, camera_id: str) -> bool:
        """Check if recording is active for the camera."""
        with self._lock:
            process = self._recording_processes.get(camera_id)
            if process:
                return process.poll() is None  # Process is still running
            return False
    
    def get_current_filename(self, camera_id: str) -> Optional[str]:
        """Get the current recording filename for the camera."""
        with self._lock:
            return self._current_files.get(camera_id)
    
    def cleanup_old_recordings(self, camera_id: str, days: int = None) -> int:
        """Clean up old recordings for the camera. Returns number of files deleted."""
        if days is None:
            days = app_config.recording.cleanup_days
        
        try:
            from src.utils import cleanup_old_recordings
            return cleanup_old_recordings(camera_id, days)
        except Exception as e:
            print(f"Error cleaning up recordings for {camera_id}: {e}")
            return 0
    
    def is_process_alive(self, camera_id: str) -> bool:
        """Check if the recording process is still running for the camera."""
        return self.is_recording(camera_id)
    
    def get_all_recording_status(self) -> Dict[str, bool]:
        """Get recording status for all cameras."""
        with self._lock:
            return {camera_id: self.is_recording(camera_id) 
                    for camera_id in self._recording_processes.keys()}
