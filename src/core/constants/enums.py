#!/usr/bin/env python3
"""
Application-wide constants and enums
"""

from enum import Enum


class CameraStatus(Enum):
    """Camera status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    INITIALIZING = "initializing"


class MotionEventType(Enum):
    """Motion event types"""
    MOTION_DETECTED = "motion_detection"
    CONNECTION = "connection"
    PING = "ping"
    PONG = "pong"


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# File system constants
DEFAULT_RECORDINGS_SUBDIR = "recordings"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H%M%S"
CHUNK_FILENAME_FORMAT = "{camera_id}_{timestamp}_chunk{chunk_number:03d}.mp4"

# Network constants
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_RETRY_ATTEMPTS = 3
WEBSOCKET_PING_INTERVAL = 30

# Motion detection constants
MIN_MOTION_THRESHOLD = 1
MAX_MOTION_THRESHOLD = 255
MIN_AREA_THRESHOLD = 1
MAX_SKIP_FRAMES = 100

# Recording constants
MIN_CHUNK_DURATION = 10  # seconds
MAX_CHUNK_DURATION = 3600  # 1 hour
MIN_CLEANUP_DAYS = 1
MAX_CLEANUP_DAYS = 365

# FFmpeg constants
SUPPORTED_VIDEO_CODECS = ["libx264", "libx265", "h264_nvenc"]
SUPPORTED_AUDIO_CODECS = ["aac", "mp3", "opus"]
SUPPORTED_PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
