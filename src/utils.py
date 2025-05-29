#!/usr/bin/env python3
"""
Utility functions for the Motion Detection System
"""

import datetime
import shutil
from pathlib import Path
from config import RECORDINGS_DIR, CLEANUP_DAYS


def cleanup_old_recordings(camera_id):
    """Remove recording directories older than CLEANUP_DAYS"""
    camera_dir = Path(RECORDINGS_DIR) / camera_id
    if not camera_dir.exists():
        return
    
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=CLEANUP_DAYS)
    
    for date_dir in camera_dir.iterdir():
        if date_dir.is_dir():
            try:
                # Parse directory name as date (YYYY-MM-DD format)
                dir_date = datetime.datetime.strptime(date_dir.name, '%Y-%m-%d')
                if dir_date < cutoff_date:
                    print(f"Cleaning up old recordings: {date_dir}")
                    shutil.rmtree(date_dir)
            except ValueError:
                # Skip directories that don't match date format
                continue


def create_recording_directory(camera_id):
    """Create recording directory for today's date"""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    recording_dir = Path(RECORDINGS_DIR) / camera_id / today
    recording_dir.mkdir(parents=True, exist_ok=True)
    return recording_dir


def generate_chunk_filename(recording_dir, camera_id, chunk_counter):
    """Generate filename for a recording chunk"""
    timestamp = datetime.datetime.now().strftime('%H%M%S')
    return recording_dir / f"{camera_id}_{timestamp}_chunk{chunk_counter:03d}.mp4"
