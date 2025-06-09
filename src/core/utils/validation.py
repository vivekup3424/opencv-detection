"""Validation utility functions."""

import re
from typing import Any, Union, Optional, List
from pathlib import Path


def is_valid_camera_id(camera_id: Union[str, int]) -> bool:
    """Validate camera ID format."""
    if isinstance(camera_id, int):
        return camera_id >= 0
    
    if isinstance(camera_id, str):
        # Check if it's a numeric string
        if camera_id.isdigit():
            return int(camera_id) >= 0
        
        # Check if it's a valid file path or URL
        if camera_id.startswith(('http://', 'https://', 'rtsp://', 'rtmp://')):
            return _is_valid_url(camera_id)
        
        # Check if it's a valid file path
        return Path(camera_id).exists() or _is_valid_path_format(camera_id)
    
    return False


def is_valid_resolution(width: int, height: int) -> bool:
    """Validate camera resolution."""
    return (
        isinstance(width, int) and isinstance(height, int) and
        width > 0 and height > 0 and
        width <= 7680 and height <= 4320  # Max 8K resolution
    )


def is_valid_fps(fps: Union[int, float]) -> bool:
    """Validate frames per second value."""
    return isinstance(fps, (int, float)) and 0 < fps <= 120


def is_valid_threshold(threshold: Union[int, float]) -> bool:
    """Validate threshold values (typically 0-255 for image processing)."""
    return isinstance(threshold, (int, float)) and 0 <= threshold <= 255


def is_positive_number(value: Any) -> bool:
    """Check if value is a positive number."""
    return isinstance(value, (int, float)) and value > 0


def is_non_negative_number(value: Any) -> bool:
    """Check if value is a non-negative number."""
    return isinstance(value, (int, float)) and value >= 0


def is_valid_percentage(value: Union[int, float]) -> bool:
    """Check if value is a valid percentage (0-100)."""
    return isinstance(value, (int, float)) and 0 <= value <= 100


def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    if not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_port(port: int) -> bool:
    """Validate network port number."""
    return isinstance(port, int) and 1 <= port <= 65535


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = 'unnamed'
    
    return sanitized


def validate_required_fields(data: dict, required_fields: List[str]) -> List[str]:
    """Validate that required fields are present in data dictionary."""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    return missing_fields


def _is_valid_url(url: str) -> bool:
    """Basic URL format validation."""
    url_pattern = re.compile(
        r'^(https?|rtsp|rtmp)://'  # protocol
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP address
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def _is_valid_path_format(path: str) -> bool:
    """Check if string has valid path format."""
    try:
        Path(path)
        return True
    except (ValueError, TypeError):
        return False
