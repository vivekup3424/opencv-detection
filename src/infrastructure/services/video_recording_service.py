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
    """Simple FFmpeg-based video recording with 60-minute chunks."""
    
    def __init__(self):
        self._recording_processes: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()
    
    def start_recording(self, camera_id: str, rtsp_url: str) -> bool:
        """Start recording video+audio with 60-minute chunks."""
        with self._lock:
            if camera_id in self._recording_processes:
                return False  # Already recording
            
            try:
                # Generate output filename pattern for 60-minute chunks
                timestamp = utc_now().strftime("%H%M%S")
                date_str = utc_now().strftime("%Y-%m-%d")
                recordings_dir = Path(app_config.recording.recordings_dir) / camera_id / date_str
                ensure_directory_exists(str(recordings_dir))
                
                output_pattern = recordings_dir / f"{camera_id}_{timestamp}_chunk%03d.mp4"
                
                # Simple FFmpeg command for video+audio recording
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file
                    '-rtsp_transport', 'tcp',
                    '-i', rtsp_url,
                    '-c:v', 'copy',  # Copy video stream (no re-encoding)
                    '-c:a', 'copy',  # Copy audio stream (no re-encoding)
                    '-f', 'segment',  # Use segment muxer for chunks
                    '-segment_time', '3600',  # 60 minutes = 3600 seconds
                    '-segment_format', 'mp4',
                    '-reset_timestamps', '1',
                    str(output_pattern)
                ]
                
                print(f"Starting recording for {camera_id}...")
                process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                
                self._recording_processes[camera_id] = process
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
                
            return True
    
    def is_recording(self, camera_id: str) -> bool:
        """Check if recording is active for the camera."""
        with self._lock:
            process = self._recording_processes.get(camera_id)
            return process is not None and process.poll() is None
    
    def write_frame(self, camera_id: str, frame: np.ndarray, timestamp: Optional[float] = None) -> bool:
        """Not used - FFmpeg handles frames directly from RTSP."""
        return self.is_recording(camera_id)
