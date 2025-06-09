"""Broadcast motion event use case for real-time notifications."""

import logging
from typing import Optional

from src.domain.entities.motion_event import MotionEvent
from src.core.utils.datetime_utils import utc_now
from src.core.errors.exceptions import ValidationError, CameraError
from src.application.gateways.websocket_gateway import WebSocketGateway

logger = logging.getLogger(__name__)

class BroadcastMotionEventUseCase:
    """
    Use case for broadcasting motion detection events.
    This handles real-time notifications when motion is detected or stops.
    """
    
    def __init__(self, websocket_gateway: WebSocketGateway):
        self.websocket_gateway = websocket_gateway
        logger.info("BroadcastMotionEventUseCase initialized")
    
    async def broadcast_motion_start(self, 
                                   camera_id: str, 
                                   video_path: Optional[str] = None) -> bool:
        """
        Broadcast motion detection start event.
        
        Args:
            camera_id: The ID of the camera that detected motion
            video_path: Optional path to the recorded video file
            
        Returns:
            True if broadcast was successful, False otherwise
            
        Raises:
            ValidationError: If camera_id is invalid
            CameraError: If broadcasting fails
        """
        logger.info(f"Broadcasting motion start event for camera: {camera_id}")
        
        if not camera_id or not camera_id.strip():
            logger.error("Attempted to broadcast motion start with empty camera_id")
            raise ValidationError("Camera ID cannot be empty")
        
        try:
            sanitized_camera_id = camera_id.strip()
            
            # Check if WebSocket gateway has connected clients
            client_count = self.websocket_gateway.get_client_count()
            logger.debug(f"WebSocket gateway has {client_count} connected clients for motion start broadcast")
            
            motion_event = MotionEvent(
                camera_id=sanitized_camera_id,
                motion_detected=True,
                timestamp=utc_now(),
                video_path=video_path
            )
            
            logger.debug(f"Created motion start event for camera {sanitized_camera_id}. "
                        f"Video path: {video_path or 'None'}, Timestamp: {motion_event.timestamp}")
            
            await self.websocket_gateway.broadcast_motion_event(motion_event)
            
            logger.info(f"Successfully broadcasted motion start event for camera {sanitized_camera_id}")
            return True
            
        except ValidationError:
            raise  # Re-raise validation errors as-is
        except Exception as e:
            error_msg = f"Failed to broadcast motion start event for {camera_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CameraError(error_msg)
    
    async def broadcast_motion_stop(self, 
                                  camera_id: str, 
                                  video_path: Optional[str] = None) -> bool:
        """
        Broadcast motion detection stop event.
        
        Args:
            camera_id: The ID of the camera that stopped detecting motion
            video_path: Optional path to the final recorded video file
            
        Returns:
            True if broadcast was successful, False otherwise
            
        Raises:
            ValidationError: If camera_id is invalid
            CameraError: If broadcasting fails
        """
        logger.info(f"Broadcasting motion stop event for camera: {camera_id}")
        
        if not camera_id or not camera_id.strip():
            logger.error("Attempted to broadcast motion stop with empty camera_id")
            raise ValidationError("Camera ID cannot be empty")
        
        try:
            sanitized_camera_id = camera_id.strip()
            
            # Check if WebSocket gateway has connected clients
            client_count = self.websocket_gateway.get_client_count()
            logger.debug(f"WebSocket gateway has {client_count} connected clients for motion stop broadcast")
            
            motion_event = MotionEvent(
                camera_id=sanitized_camera_id,
                motion_detected=False,
                timestamp=utc_now(),
                video_path=video_path
            )
            
            logger.debug(f"Created motion stop event for camera {sanitized_camera_id}. "
                        f"Video path: {video_path or 'None'}, Timestamp: {motion_event.timestamp}")
            
            # Broadcast via WebSocket to clients
            await self.websocket_gateway.broadcast_motion_event(motion_event)
            
            logger.info(f"Successfully broadcasted motion stop event for camera {sanitized_camera_id}")
            return True
            
        except ValidationError:
            raise  # Re-raise validation errors as-is
        except Exception as e:
            error_msg = f"Failed to broadcast motion stop event for {camera_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CameraError(error_msg)