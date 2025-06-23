#!/usr/bin/env python3
"""
Configuration settings for the Motion Detection System
"""

import os

# Motion detection parameters
DEFAULT_THRESHOLD = 20
DEFAULT_MIN_AREA = 300  # Smaller minimum area to catch smaller movements
SKIP_FRAMES = 2
DEFAULT_POST_BUFFER_SECONDS = 3

# Video capture settings
MOTION_DETECT_RESOLUTION = (320, 240)
GAUSSIAN_KERNEL = (11, 11)  # Same kernel size

# Recording settings
RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recordings")
CLEANUP_DAYS = 7
CHUNK_DURATION_SECONDS = 60  # 1 minute chunks

# Reconnection settings
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 5  # seconds between reconnection attempts

# Performance settings
ADAPTIVE_SLEEP_NO_MOTION = 0.05
ADAPTIVE_SLEEP_MOTION = 0.03

# Server settings
DEFAULT_HTTP_HOST = '0.0.0.0'
DEFAULT_HTTP_PORT = 8083
DEFAULT_WEBSOCKET_HOST = '0.0.0.0'
DEFAULT_WEBSOCKET_PORT = 8084

# FFmpeg settings
FFMPEG_PRESET = 'ultrafast'
FFMPEG_CRF = 28
FFMPEG_FPS = 15
FFMPEG_RESOLUTION = '1280x720'
FFMPEG_AUDIO_BITRATE = '64k'
FFMPEG_THREADS = 2
