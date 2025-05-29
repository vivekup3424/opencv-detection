#!/usr/bin/env python3
"""
Configuration settings for the Motion Detection System
"""

import os

# Motion detection parameters
DEFAULT_THRESHOLD = 30
DEFAULT_MIN_AREA = 800
SKIP_FRAMES = 10  # Process every 10th frame
DEFAULT_POST_BUFFER_SECONDS = 3
DEFAULT_FPS = 15  # Lower target FPS

# Video capture settings
BUFFER_SIZE = 1  # Smaller buffer to reduce memory
MAX_INIT_FRAMES = 50
INIT_FRAME_WAIT = 0.2
MOTION_DETECT_RESOLUTION = (128, 96)  # Even smaller resolution
GAUSSIAN_KERNEL = (11, 11)  # Smaller kernel

# Recording settings
RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recordings")
CLEANUP_DAYS = 3
CHUNK_DURATION_SECONDS = 60  # 1 minute chunks

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
