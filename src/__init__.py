#!/usr/bin/env python3
"""
Motion Detection System Package

A modular motion detection system with RTSP camera support,
video recording, and real-time WebSocket notifications.
"""

__version__ = "2.0.0"
__author__ = "Motion Detection System"

# Import main components for easy access
from .main import main, run_motion_detection_server
from .camera_manager import CameraManager, CameraWorker
from .motion_detector import MotionDetector
from .video_recorder import VideoRecorder
from .websocket_server import MotionDetectionWebSocketServer
from .api_handler import MotionAPIHandler, create_handler_class
from .utils import cleanup_old_recordings, create_recording_directory
from . import config

__all__ = [
    'main',
    'run_motion_detection_server',
    'CameraManager',
    'CameraWorker',
    'MotionDetector',
    'VideoRecorder',
    'MotionDetectionWebSocketServer',
    'MotionAPIHandler',
    'create_handler_class',
    'cleanup_old_recordings',
    'create_recording_directory',
    'config'
]
