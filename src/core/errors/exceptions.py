#!/usr/bin/env python3
"""
Custom error types and error handling utilities
"""

from typing import Optional, Any


class MotionDetectionError(Exception):
    """Base exception for motion detection system"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class CameraError(MotionDetectionError):
    """Camera-related errors"""
    pass


class CameraConnectionError(CameraError):
    """Camera connection failed"""
    pass


class CameraNotFoundError(CameraError):
    """Camera not found"""
    pass


class CameraAlreadyExistsError(CameraError):
    """Camera already exists"""
    pass


class RecordingError(MotionDetectionError):
    """Recording-related errors"""
    pass


class FFmpegError(RecordingError):
    """FFmpeg process errors"""
    pass


class StorageError(RecordingError):
    """Storage/filesystem errors"""
    pass


class ConfigurationError(MotionDetectionError):
    """Configuration-related errors"""
    pass


class WebSocketError(MotionDetectionError):
    """WebSocket-related errors"""
    pass


class ValidationError(MotionDetectionError):
    """Input validation errors"""
    pass


class ApplicationStartupError(MotionDetectionError):
    """Application startup errors"""
    pass


def handle_camera_error(error: Exception, camera_id: str) -> CameraError:
    """Convert generic exceptions to camera-specific errors"""
    if isinstance(error, CameraError):
        return error
    
    error_message = f"Camera '{camera_id}' error: {str(error)}"
    
    if "connection" in str(error).lower() or "timeout" in str(error).lower():
        return CameraConnectionError(error_message, "CAMERA_CONNECTION_FAILED", {"camera_id": camera_id})
    
    return CameraError(error_message, "CAMERA_ERROR", {"camera_id": camera_id, "original_error": str(error)})


def handle_recording_error(error: Exception, video_path: Optional[str] = None) -> RecordingError:
    """Convert generic exceptions to recording-specific errors"""
    if isinstance(error, RecordingError):
        return error
    
    error_message = f"Recording error: {str(error)}"
    details = {"original_error": str(error)}
    
    if video_path:
        details["video_path"] = video_path
    
    if "ffmpeg" in str(error).lower():
        return FFmpegError(error_message, "FFMPEG_ERROR", details)
    
    if "permission" in str(error).lower() or "space" in str(error).lower():
        return StorageError(error_message, "STORAGE_ERROR", details)
    
    return RecordingError(error_message, "RECORDING_ERROR", details)
