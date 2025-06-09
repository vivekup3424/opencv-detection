from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MotionEvent:
    camera_id: str
    motion_detected: bool
    timestamp: datetime
    video_path: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MotionEvent':
        """Create MotionEvent from dictionary (e.g., from WebSocket message)"""
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']
        return cls(
            camera_id=data['camera_id'],
            motion_detected=data['motion_detected'],
            timestamp=timestamp,
            video_path=data.get('video_path')
        )
    
    def to_dict(self) -> dict:
        """Convert MotionEvent to dictionary (e.g., for WebSocket message)"""
        return {
            'type': 'motion_detection',
            'camera_id': self.camera_id,
            'motion_detected': self.motion_detected,
            'timestamp': self.timestamp.isoformat(),
            'video_path': self.video_path
        }
