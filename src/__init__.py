#!/usr/bin/env python3
"""
Motion Detection System Package

A clean architecture motion detection system with RTSP camera support,
video recording, and real-time WebSocket notifications.
"""

__version__ = "2.0.0"
__author__ = "Motion Detection System"

# Clean Architecture Exports
from .domain.entities.camera import Camera
from .domain.entities.motion_event import MotionEvent
from .core.config.settings import get_settings

__all__ = [
    'Camera',
    'MotionEvent', 
    'get_settings'
]
