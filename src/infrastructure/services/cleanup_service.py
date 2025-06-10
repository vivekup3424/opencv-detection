"""Background cleanup service for managing old recordings."""

import time
import threading
from pathlib import Path

from src.core.config.settings import app_config
from src.core.utils.file_utils import cleanup_old_files, safe_remove_directory


class CleanupService:
    """Simple background service that cleans up old recordings every 6 hours."""
    
    def __init__(self):
        self._stop_event = threading.Event()
        self._cleanup_thread = None
        self._running = False
        
        # Configuration
        self.recordings_dir = Path(app_config.recording.recordings_dir)
        self.cleanup_days = 7  # Clean up recordings older than 7 days
        self.cleanup_interval_hours = 6  # Run every 6 hours
        
    def start(self):
        """Start the background cleanup service."""
        if self._running:
            print("Cleanup service is already running")
            return
            
        print(f"Starting cleanup service - will run every {self.cleanup_interval_hours} hours")
        print(f"Will clean up recordings older than {self.cleanup_days} days")
        
        self._stop_event.clear()
        self._running = True
        
        # Start the background thread
        self._cleanup_thread = threading.Thread(
            target=self._run_cleanup_loop,
            name="CleanupService",
            daemon=True
        )
        self._cleanup_thread.start()
        
        # Run initial cleanup
        self._perform_cleanup()
        
    def stop(self):
        """Stop the background cleanup service."""
        if not self._running:
            return
            
        print("Stopping cleanup service...")
        self._stop_event.set()
        self._running = False
        
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
            
        print("Cleanup service stopped")
        
    def _run_cleanup_loop(self):
        """Run cleanup every 6 hours."""
        while not self._stop_event.is_set():
            # Wait 6 hours (or until stop signal)
            if self._stop_event.wait(timeout=self.cleanup_interval_hours * 3600):
                break  # Stop signal received
            
            if not self._stop_event.is_set():
                self._perform_cleanup()
                
    def _perform_cleanup(self):
        """Clean up old recordings and empty directories."""
        if not self.recordings_dir.exists():
            print("Recordings directory does not exist, skipping cleanup")
            return
            
        print("Starting cleanup of old recordings...")
        
        try:
            total_files_deleted = 0
            
            # Clean up old files in all camera directories
            for camera_dir in self.recordings_dir.iterdir():
                if camera_dir.is_dir():
                    camera_id = camera_dir.name
                    files_deleted = cleanup_old_files(camera_dir, self.cleanup_days, "*.mp4")
                    if files_deleted > 0:
                        print(f"Cleaned up {files_deleted} old recordings for camera {camera_id}")
                    total_files_deleted += files_deleted
                    
            # Remove empty directories
            empty_dirs_removed = self._remove_empty_directories()
            
            print(f"Cleanup completed: {total_files_deleted} files deleted, "
                  f"{empty_dirs_removed} empty directories removed")
                  
        except Exception as e:
            print(f"Error during cleanup: {e}")
            
    def _remove_empty_directories(self) -> int:
        """Remove empty directories."""
        empty_dirs_removed = 0
        
        try:
            # Get all directories, deepest first
            all_dirs = []
            for item in self.recordings_dir.rglob("*"):
                if item.is_dir() and item != self.recordings_dir:
                    all_dirs.append(item)
                    
            # Sort by depth (deepest first)
            all_dirs.sort(key=lambda p: len(p.parts), reverse=True)
            
            for dir_path in all_dirs:
                if not any(dir_path.iterdir()):  # Empty directory
                    if safe_remove_directory(dir_path):
                        print(f"Removed empty directory: {dir_path.relative_to(self.recordings_dir)}")
                        empty_dirs_removed += 1
                        
        except Exception as e:
            print(f"Error removing empty directories: {e}")
            
        return empty_dirs_removed
