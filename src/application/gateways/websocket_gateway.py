"""WebSocket gateway for real-time motion detection updates following clean architecture."""

import asyncio
import websockets
import json
import threading
import logging
import time
from typing import Set, Optional, Dict, Any
from src.domain.entities.motion_event import MotionEvent
from src.core.utils.datetime_utils import utc_now
from src.core.config.settings import WebSocketConfig

logger = logging.getLogger(__name__)


class WebSocketGateway:
    """WebSocket gateway for real-time motion detection updates."""
    
    def __init__(self, websocket_config: WebSocketConfig):
        self.host = websocket_config.host
        self.port = websocket_config.port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.loop = None
        self.server_thread = None
        self._running = False
        self._start_time = None
        self._total_connections = 0
        self._total_messages_sent = 0
        self._total_messages_received = 0
        
        logger.info(f"WebSocket gateway initialized - Host: {self.host}, Port: {self.port}")
    
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new WebSocket client."""
        connection_start = time.time()
        self.clients.add(websocket)
        self._total_connections += 1
        
        try:
            remote_address = websocket.remote_address
            if remote_address:
                client_info = f"{remote_address[0]}:{remote_address[1]}"
            else:
                client_info = "unknown"
        except Exception as e:
            logger.warning(f"Failed to get client remote address: {e}")
            client_info = "unknown"
        
        logger.info(f"WebSocket client connected from {client_info}. "
                   f"Active clients: {len(self.clients)}, Total connections: {self._total_connections}")
        
        try:
            # Send welcome message with connection details
            welcome_message = {
                "type": "connection",
                "message": "Connected to Motion Detection WebSocket Server",
                "timestamp": utc_now().isoformat(),
                "server_info": {
                    "active_clients": len(self.clients),
                    "server_uptime": time.time() - self._start_time if self._start_time else 0
                }
            }
            await websocket.send(json.dumps(welcome_message))
            self._total_messages_sent += 1
            
            logger.debug(f"Sent welcome message to client {client_info}")
            
            # Handle incoming messages with improved logging
            message_count = 0
            async for message in websocket:
                message_count += 1
                self._total_messages_received += 1
                
                try:
                    data = json.loads(message)
                    message_type = data.get("type", "unknown")
                    
                    logger.debug(f"Received message from {client_info}: type={message_type}, "
                               f"client_message_count={message_count}")
                    
                    if message_type == "ping":
                        pong_response = {
                            "type": "pong",
                            "timestamp": utc_now().isoformat(),
                            "server_stats": {
                                "active_clients": len(self.clients),
                                "total_messages_sent": self._total_messages_sent,
                                "total_messages_received": self._total_messages_received
                            }
                        }
                        await websocket.send(json.dumps(pong_response))
                        self._total_messages_sent += 1
                        logger.debug(f"Sent pong response to {client_info}")
                    else:
                        logger.debug(f"Received non-ping message from {client_info}: {message_type}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received from {client_info}: {str(e)[:100]}...")
                except Exception as e:
                    logger.error(f"Error processing message from {client_info}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            connection_duration = time.time() - connection_start
            logger.info(f"WebSocket client {client_info} disconnected normally. "
                       f"Connection duration: {connection_duration:.2f}s, Messages received: {message_count}")
        except Exception as e:
            connection_duration = time.time() - connection_start
            logger.error(f"WebSocket client {client_info} disconnected with error: {e}. "
                        f"Connection duration: {connection_duration:.2f}s, Messages received: {message_count}")
        finally:
            await self.unregister_client(websocket)
    
    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a WebSocket client."""
        was_present = websocket in self.clients
        self.clients.discard(websocket)
        
        if was_present:
            logger.info(f"WebSocket client unregistered. Active clients: {len(self.clients)}")
        else:
            logger.debug("Attempted to unregister client that was not in client set")
    
    async def _broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients."""
        if not self.clients:
            logger.debug("No clients connected, skipping broadcast")
            return
        
        start_time = time.time()
        message_str = json.dumps(message)
        message_size = len(message_str.encode('utf-8'))
        disconnected_clients = set()
        successful_sends = 0
        
        logger.debug(f"Broadcasting message to {len(self.clients)} clients. "
                    f"Message size: {message_size} bytes, Type: {message.get('type', 'unknown')}")
        
        for client in self.clients.copy():
            try:
                await client.send(message_str)
                successful_sends += 1
                self._total_messages_sent += 1
            except websockets.exceptions.ConnectionClosed:
                logger.debug("Client connection closed during broadcast")
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.unregister_client(client)
        
        broadcast_duration = time.time() - start_time
        logger.info(f"Broadcast completed - Successful: {successful_sends}/{len(self.clients) + len(disconnected_clients)}, "
                   f"Disconnected: {len(disconnected_clients)}, Duration: {broadcast_duration:.3f}s, "
                   f"Message size: {message_size} bytes")
    
    async def start_server(self):
        """Start the WebSocket server."""
        try:
            self._start_time = time.time()
            logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
            logger.info(f"WebSocket configuration - Ping interval: 30s, Ping timeout: 10s")
            
            self.server = await websockets.serve(
                self.register_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            self._running = True
            logger.info(f"WebSocket server started successfully on {self.host}:{self.port}")
            logger.info("WebSocket server is ready to accept connections")
            
            # Keep the server running
            await self.server.wait_closed()
            
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.error(f"WebSocket server port {self.port} is already in use")
            else:
                logger.error(f"WebSocket server network error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {e}", exc_info=True)
            raise
        finally:
            self._running = False
            logger.info("WebSocket server start_server method completed")
    
    async def stop_server(self):
        """Stop the WebSocket server."""
        if not self.server:
            logger.warning("Attempted to stop WebSocket server that is not running")
            return
            
        stop_start_time = time.time()
        uptime = time.time() - self._start_time if self._start_time else 0
        
        logger.info(f"Stopping WebSocket server... Server uptime: {uptime:.2f}s")
        logger.info(f"Final statistics - Total connections: {self._total_connections}, "
                   f"Messages sent: {self._total_messages_sent}, Messages received: {self._total_messages_received}")
        
        self._running = False
        
        # Close all client connections with proper logging
        if self.clients:
            logger.info(f"Closing {len(self.clients)} active client connections...")
            try:
                # Send shutdown notification to clients
                shutdown_message = {
                    "type": "server_shutdown",
                    "message": "Server is shutting down",
                    "timestamp": utc_now().isoformat()
                }
                await self._broadcast_to_clients(shutdown_message)
            except Exception as e:
                logger.error(f"Error sending shutdown notification: {e}")
            
            # Close all connections
            try:
                await asyncio.gather(
                    *[client.close() for client in self.clients],
                    return_exceptions=True
                )
                self.clients.clear()
                logger.info("All client connections closed")
            except Exception as e:
                logger.error(f"Error closing client connections: {e}")
        else:
            logger.info("No active client connections to close")
        
        # Close the server
        try:
            self.server.close()
            await self.server.wait_closed()
            stop_duration = time.time() - stop_start_time
            logger.info(f"WebSocket server stopped successfully. Shutdown duration: {stop_duration:.2f}s")
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")
            raise
    
    def start_in_thread(self):
        """Start the WebSocket server in a separate thread."""
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("WebSocket server thread is already running")
            return
            
        def run_server():
            thread_start_time = time.time()
            thread_name = threading.current_thread().name
            logger.info(f"WebSocket server thread '{thread_name}' starting...")
            
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            try:
                logger.debug(f"Running WebSocket server event loop in thread '{thread_name}'")
                self.loop.run_until_complete(self.start_server())
            except Exception as e:
                thread_duration = time.time() - thread_start_time
                logger.error(f"WebSocket server thread '{thread_name}' error after {thread_duration:.2f}s: {e}", 
                           exc_info=True)
            finally:
                try:
                    self.loop.close()
                    thread_duration = time.time() - thread_start_time
                    logger.info(f"WebSocket server thread '{thread_name}' completed. Duration: {thread_duration:.2f}s")
                except Exception as e:
                    logger.error(f"Error closing WebSocket server event loop: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True, name="WebSocketServer")
        self.server_thread.start()
        logger.info(f"WebSocket server thread started with ID: {self.server_thread.ident}")
    
    def stop_thread(self):
        """Stop the WebSocket server thread."""
        if not self.loop or not self._running:
            logger.info("WebSocket server is not running, nothing to stop")
            return
            
        logger.info("Initiating WebSocket server thread shutdown...")
        
        try:
            # Schedule stop_server on the event loop
            future = asyncio.run_coroutine_threadsafe(self.stop_server(), self.loop)
            
            # Wait for the stop operation to complete
            try:
                future.result(timeout=5)
                logger.debug("WebSocket server stop operation completed")
            except asyncio.TimeoutError:
                logger.warning("WebSocket server stop operation timed out after 5 seconds")
            
        except Exception as e:
            logger.error(f"Error scheduling WebSocket server stop: {e}")
        
        # Wait for thread to finish
        if self.server_thread and self.server_thread.is_alive():
            logger.debug("Waiting for WebSocket server thread to terminate...")
            self.server_thread.join(timeout=10)
            
            if self.server_thread.is_alive():
                logger.warning("WebSocket server thread did not stop gracefully within 10 seconds")
            else:
                logger.info("WebSocket server thread terminated successfully")
    
    def is_running(self) -> bool:
        """Check if the WebSocket server is running."""
        is_running = self._running and self.server_thread and self.server_thread.is_alive()
        logger.debug(f"WebSocket server running status: {is_running} "
                    f"(_running={self._running}, thread_alive={self.server_thread and self.server_thread.is_alive()})")
        return is_running
    
    def get_client_count(self) -> int:
        """Get the number of connected clients."""
        count = len(self.clients)
        logger.debug(f"Current WebSocket client count: {count}")
        return count
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get comprehensive server statistics."""
        uptime = time.time() - self._start_time if self._start_time else 0
        stats = {
            "is_running": self.is_running(),
            "active_clients": len(self.clients),
            "total_connections": self._total_connections,
            "messages_sent": self._total_messages_sent,
            "messages_received": self._total_messages_received,
            "uptime_seconds": uptime,
            "server_address": f"{self.host}:{self.port}"
        }
        logger.debug(f"WebSocket server stats: {stats}")
        return stats

    def get_clients(self) -> Set[websockets.WebSocketServerProtocol]:
        """Get the set of connected WebSocket clients."""
        clients_copy = self.clients.copy()
        logger.debug(f"Returning copy of {len(clients_copy)} WebSocket clients")
        return clients_copy

    async def broadcast_motion_event(self, motion_event: MotionEvent):
        """
        Broadcast motion detection event to all connected WebSocket clients.
        
        Args:
            motion_event: The motion event to broadcast
        """
        if not self.clients:
            logger.warning(f"No WebSocket clients connected to broadcast motion event for camera {motion_event.camera_id}")
            return
            
        motion_type = "started" if motion_event.motion_detected else "stopped"
        logger.info(f"Broadcasting motion {motion_type} event for camera {motion_event.camera_id} to {len(self.clients)} clients")
        
        message = {
            "type": "motion_event",
            "camera_id": motion_event.camera_id,
            "motion_detected": motion_event.motion_detected,
            "timestamp": motion_event.timestamp.isoformat(),
            "video_path": motion_event.video_path
        }
        
        # Add extra context for debugging
        if motion_event.video_path:
            logger.debug(f"Motion event includes video path: {motion_event.video_path}")
        
        start_time = time.time()
        await self._broadcast_to_clients(message)
        broadcast_duration = time.time() - start_time
        
        logger.info(f"Motion {motion_type} event broadcast completed for camera {motion_event.camera_id}. "
                   f"Duration: {broadcast_duration:.3f}s")