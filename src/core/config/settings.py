#!/usr/bin/env python3
"""
Configuration management for the Motion Detection System
Handles environment-specific settings and configuration loading
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class HttpConfig:
    """HTTP server configuration"""
    host: str = '0.0.0.0'
    port: int = 8083


@dataclass
class WebSocketConfig:
    """WebSocket server configuration"""
    host: str = '0.0.0.0'
    port: int = 8084


@dataclass
class CameraConfig:
    """Camera configuration settings"""
    default_width: int = 1280
    default_height: int = 720
    default_fps: int = 15


@dataclass
class ServerConfig:
    """Server configuration settings"""
    log_level: str = 'INFO'


@dataclass
class MotionDetectionConfig:
    """Motion detection configuration settings"""
    threshold: int = 30
    min_area: int = 800
    skip_frames: int = 10
    post_buffer_seconds: int = 3
    fps: int = 15


@dataclass
class RecordingConfig:
    """Recording configuration settings"""
    recordings_dir: str = "recordings"
    cleanup_days: int = 3
    chunk_duration_seconds: int = 60
    ffmpeg_preset: str = "ultrafast"
    ffmpeg_crf: int = 28
    ffmpeg_fps: int = 15
    ffmpeg_resolution: str = "1280x720"
    ffmpeg_audio_bitrate: str = "64k"
    ffmpeg_threads: int = 2


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    buffer_size: int = 1
    max_init_frames: int = 50
    init_frame_wait: float = 0.2
    adaptive_sleep_no_motion: float = 0.05
    adaptive_sleep_motion: float = 0.03


@dataclass
class ApplicationSettings:
    """Main application configuration"""
    http: HttpConfig
    websocket: WebSocketConfig
    camera: CameraConfig
    server: ServerConfig
    motion_detection: MotionDetectionConfig
    recording: RecordingConfig
    performance: PerformanceConfig
    log_file: Optional[str] = None
    log_level: str = 'INFO'
    
    @classmethod
    def load_from_env(cls) -> 'ApplicationSettings':
        """Load configuration from environment variables and defaults"""
        # Get base directory
        base_dir = Path(__file__).parent.parent.parent.parent
        recordings_dir = str(base_dir / "recordings")
        
        http = HttpConfig(
            host=os.getenv('HTTP_HOST', '0.0.0.0'),
            port=int(os.getenv('HTTP_PORT', '8083'))
        )
        
        websocket = WebSocketConfig(
            host=os.getenv('WEBSOCKET_HOST', '0.0.0.0'),
            port=int(os.getenv('WEBSOCKET_PORT', '8084'))
        )
        
        camera = CameraConfig(
            default_width=int(os.getenv('CAMERA_DEFAULT_WIDTH', '1280')),
            default_height=int(os.getenv('CAMERA_DEFAULT_HEIGHT', '720')),
            default_fps=int(os.getenv('CAMERA_DEFAULT_FPS', '15'))
        )
        
        server = ServerConfig(
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
        
        motion_detection = MotionDetectionConfig(
            threshold=int(os.getenv('MOTION_THRESHOLD', '30')),
            min_area=int(os.getenv('MOTION_MIN_AREA', '800')),
            skip_frames=int(os.getenv('MOTION_SKIP_FRAMES', '10')),
            post_buffer_seconds=int(os.getenv('MOTION_POST_BUFFER', '3')),
            fps=int(os.getenv('MOTION_FPS', '15'))
        )
        
        recording = RecordingConfig(
            recordings_dir=os.getenv('RECORDINGS_DIR', recordings_dir),
            cleanup_days=int(os.getenv('CLEANUP_DAYS', '3')),
            chunk_duration_seconds=int(os.getenv('CHUNK_DURATION', '60')),
            ffmpeg_preset=os.getenv('FFMPEG_PRESET', 'ultrafast'),
            ffmpeg_crf=int(os.getenv('FFMPEG_CRF', '28')),
            ffmpeg_fps=int(os.getenv('FFMPEG_FPS', '15')),
            ffmpeg_resolution=os.getenv('FFMPEG_RESOLUTION', '1280x720'),
            ffmpeg_audio_bitrate=os.getenv('FFMPEG_AUDIO_BITRATE', '64k'),
            ffmpeg_threads=int(os.getenv('FFMPEG_THREADS', '2'))
        )
        
        performance = PerformanceConfig(
            buffer_size=int(os.getenv('BUFFER_SIZE', '1')),
            max_init_frames=int(os.getenv('MAX_INIT_FRAMES', '50')),
            init_frame_wait=float(os.getenv('INIT_FRAME_WAIT', '0.2')),
            adaptive_sleep_no_motion=float(os.getenv('ADAPTIVE_SLEEP_NO_MOTION', '0.05')),
            adaptive_sleep_motion=float(os.getenv('ADAPTIVE_SLEEP_MOTION', '0.03'))
        )
        
        log_file = os.getenv('LOG_FILE')
        
        return cls(
            http=http,
            websocket=websocket,
            camera=camera,
            server=server,
            motion_detection=motion_detection,
            recording=recording,
            performance=performance,
            log_file=log_file
        )


def load_camera_config(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load camera configuration from JSON file"""
    if config_path is None:
        base_dir = Path(__file__).parent.parent.parent.parent
        config_path = base_dir / "config.json"
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load camera config from {config_path}: {e}")
        return []


# Global configuration instance
app_config = ApplicationSettings.load_from_env()

def get_settings() -> ApplicationSettings:
    """Get the global application settings."""
    return app_config
