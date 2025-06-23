#!/usr/bin/env python3
"""
Camera management with threading support
"""

import time
import threading
from camera_worker import CameraWorker


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
