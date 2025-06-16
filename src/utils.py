#!/usr/bin/env python3
"""
Utility functions for the Motion Detection System
"""

import datetime
from pathlib import Path
from config import RECORDINGS_DIR, CLEANUP_DAYS


def cleanup_old_recordings(camera_id):
    """Remove recordings older than CLEANUP_DAYS"""
    camera_dir = Path(RECORDINGS_DIR) / camera_id
    if not camera_dir.exists():
        return
    
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=CLEANUP_DAYS)
    
    for video_file in camera_dir.glob("*.mp4"):
        try:
            # Get file modification time
            file_mtime = datetime.datetime.fromtimestamp(video_file.stat().st_mtime)
            if file_mtime < cutoff_time:
                print(f"Cleaning up old recording: {video_file}")
                video_file.unlink()
        except Exception as e:
            print(f"Error cleaning up file {video_file}: {e}")
            continue


def create_recording_directory(camera_id):
    """Create recording directory for camera_id"""
    recording_dir = Path(RECORDINGS_DIR) / camera_id
    recording_dir.mkdir(parents=True, exist_ok=True)
    return recording_dir


