#!/usr/bin/env python3
"""
Video recording functionality using FFmpeg
"""

import subprocess
from config import (
    FFMPEG_PRESET, FFMPEG_CRF, FFMPEG_FPS, FFMPEG_RESOLUTION,
    FFMPEG_AUDIO_BITRATE, FFMPEG_THREADS
)


class VideoRecorder:
    """Handles video recording using FFmpeg"""
    
    def __init__(self):
        self.recording_process = None
    
    def start_recording(self, output_file, rtsp_url):
        """Start ffmpeg process for recording RTSP stream with video and audio - optimized for low CPU"""
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-rtsp_transport', 'tcp',  # Use TCP for better reliability
            '-i', rtsp_url,  # Input RTSP stream directly
            '-c:v', 'libx264',  # H.264 video codec
            '-preset', FFMPEG_PRESET,  # Fastest encoding for lower CPU usage
            '-crf', str(FFMPEG_CRF),  # Higher CRF for smaller files and lower CPU usage
            '-r', str(FFMPEG_FPS),  # Limit frame rate
            '-s', FFMPEG_RESOLUTION,  # Limit resolution
            '-c:a', 'aac',  # AAC audio codec
            '-b:a', FFMPEG_AUDIO_BITRATE,  # Lower audio bitrate
            '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
            '-movflags', '+faststart',  # Move metadata to beginning for web compatibility
            '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
            '-threads', str(FFMPEG_THREADS),  # Limit CPU threads
            str(output_file)
        ]
        
        self.recording_process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE)
        return self.recording_process
    
    def stop_recording(self):
        """Stop the current recording process"""
        if self.recording_process:
            try:
                self.recording_process.terminate()
                self.recording_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.recording_process.kill()
                self.recording_process.wait()
            finally:
                self.recording_process = None
    
    def is_recording(self):
        """Check if currently recording"""
        return self.recording_process is not None
    
    def is_process_alive(self):
        """Check if the recording process is still running"""
        if self.recording_process:
            return self.recording_process.poll() is None
        return False
