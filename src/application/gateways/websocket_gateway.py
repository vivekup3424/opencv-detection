"""WebSocket gateway for real-time motion detection updates following clean architecture."""

import asyncio
import websockets
import json
import datetime
import threading
import logging
from typing import Set, Optional, Dict, Any

from src.domain.entities.motion_event import MotionEvent
from src.domain.usecases.broadcast_motion_event import BroadcastMotionEventUseCase
from src.core.errors.exceptions import CameraError
from src.core.utils.datetime_utils import utc_now
from src.core.config.settings import WebSocketConfig

logger = logging.getLogger(__name__)


class WebSocketGateway:
    """WebSocket gateway for real-time motion detection updates."""
    
    def __init__(self, 
                 broadcast_usecase: BroadcastMotionEventUseCase,
                 websocket_config: WebSocketConfig):
        self.host = websocket_config.host
        self.port = websocket_config.port
        self.broadcast_usecase = broadcast_usecase
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.loop = None
        self.server_thread = None
        self._running = False
    
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        
        try:
            remote_address = websocket.remote_address
        except:
            remote_address = "unknown"
        
        logger.info(f"WebSocket client connected from {remote_address}. Total clients: {len(self.clients)}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection",
                "message": "Connected to Motion Detection WebSocket Server",
                "timestamp": utc_now().isoformat()
            }))
            
            # Keep connection alive with ping/pong handling
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": utc_now().isoformat()
                        }))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from {remote_address}")
                except Exception as e:
                    logger.error(f"Error processing message from {remote_address}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket client {remote_address} disconnected normally")
        except Exception as e:
            logger.error(f"WebSocket client {remote_address} disconnected with error: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client."""
        self.clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast_motion_event(self, camera_id: str, file_path: Optional[str], motion_started: bool):
        """Broadcast motion detection event to all connected clients."""
        if not self.clients:
            logger.debug("No WebSocket clients connected for motion event broadcast")
            return
        
        try:
            # Create motion event entity
            motion_event = MotionEvent(
                camera_id=camera_id,
                motion_detected=motion_started,
                file_path=file_path,
                timestamp=utc_now()
            )
            
            # Use domain use case to handle the business logic
            await self.broadcast_usecase.execute(motion_event)
            
            # Broadcast to WebSocket clients
            message = {
                "type": "motion_event",
                "camera_id": camera_id,
                "motion_detected": motion_started,
                "file_path": file_path,
                "timestamp": motion_event.timestamp.isoformat(),
                "event": "motion_start" if motion_started else "motion_end"
            }
            
            await self._broadcast_to_clients(message)
            
        except Exception as e:
            logger.error(f"Error broadcasting motion event: {e}")
    
    async def broadcast_camera_status(self, camera_id: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Broadcast camera status updates to all connected clients."""
        if not self.clients:
            logger.debug("No WebSocket clients connected for camera status broadcast")
            return
        
        try:
            message = {
                "type": "camera_status",
                "camera_id": camera_id,
                "status": status,
                "timestamp": utc_now().isoformat(),
                "details": details or {}
            }
            
            await self._broadcast_to_clients(message)
            
        except Exception as e:
            logger.error(f"Error broadcasting camera status: {e}")
    
    async def _broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients."""
        if not self.clients:
            return
        
        message_str = json.dumps(message)
        disconnected_clients = set()
        
        for client in self.clients.copy():
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.unregister_client(client)
        
        logger.debug(f"Broadcasted message to {len(self.clients)} clients")
    
    async def start_server(self):
        """Start the WebSocket server."""
        try:
            logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
            
            self.server = await websockets.serve(
                self.register_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            self._running = True
            logger.info(f"WebSocket server started successfully on {self.host}:{self.port}")
            
            # Keep the server running
            await self.server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if self.server:
            logger.info("Stopping WebSocket server...")
            self._running = False
            
            # Close all client connections
            if self.clients:
                await asyncio.gather(
                    *[client.close() for client in self.clients],
                    return_exceptions=True
                )
                self.clients.clear()
            
            # Close the server
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    def start_in_thread(self):
        """Start the WebSocket server in a separate thread."""
        def run_server():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            try:
                self.loop.run_until_complete(self.start_server())
            except Exception as e:
                logger.error(f"WebSocket server thread error: {e}")
            finally:
                self.loop.close()
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info("WebSocket server thread started")
    
    def stop_thread(self):
        """Stop the WebSocket server thread."""
        if self.loop and self._running:
            # Schedule stop_server on the event loop
            asyncio.run_coroutine_threadsafe(self.stop_server(), self.loop)
            
            # Wait for thread to finish
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=10)
                
                if self.server_thread.is_alive():
                    logger.warning("WebSocket server thread did not stop gracefully")
    
    def is_running(self) -> bool:
        """Check if the WebSocket server is running."""
        return self._running and self.server_thread and self.server_thread.is_alive()
    
    def get_client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self.clients)
    
    # Legacy compatibility methods for existing camera manager integration
    def handle_motion_detection_event(self, camera_id: str, file_path: Optional[str], motion_started: bool):
        """Legacy method for compatibility with existing camera manager."""
        if self.loop and self._running:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_motion_event(camera_id, file_path, motion_started),
                self.loop
            )
    
    def handle_camera_status_event(self, camera_id: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Legacy method for compatibility with existing camera manager."""
        if self.loop and self._running:
            asyncio.run_coroutine_threadsafe(
                self.broadcast_camera_status(camera_id, status, details),
                self.loop
            )
