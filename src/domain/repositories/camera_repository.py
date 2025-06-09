# Repository interfaces for the motion detection system
from abc import ABC, abstractmethod
from ..entities.camera import Camera
from ..entities.motion_event import MotionEvent
from typing import List, Optional, Tuple, Dict, Any

class ICameraRepository(ABC):
    @abstractmethod
    def add_camera(self, camera: Camera) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def delete_camera(self, camera_id: str) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def list_cameras(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all cameras or get specific camera status if camera_id provided"""
        pass

    @abstractmethod
    def stop_all_cameras(self) -> None:
        pass

    @abstractmethod
    def broadcast_motion_event(self, motion_event: MotionEvent) -> None:
        """Broadcast motion event (combined with motion event functionality)"""
        pass
