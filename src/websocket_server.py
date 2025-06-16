#!/usr/bin/env python3
"""
WebSocket server for real-time motion detection updates
"""

import asyncio
import websockets
import json
import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class MotionDetectionWebSocketServer:
    """WebSocket server for real-time motion detection updates"""
    
    def __init__(self, host='0.0.0.0', port=8084):
        self.host = host
        self.port = port
        self.clients = set()  # Keep track of connected clients
        self.server = None
        self.loop = None
        self.server_thread = None
    
    async def register_client(self, websocket):
        """Register a new WebSocket client - never remove clients"""
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
                "timestamp": datetime.datetime.now().isoformat()
            }))
            
            # Keep connection alive with ping/pong handling
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.datetime.now().isoformat()
                        }))
                        logger.debug(f"Responded to ping from {remote_address}")
                except json.JSONDecodeError:
                    # Ignore invalid JSON messages
                    logger.warning(f"Received invalid JSON from {remote_address}")
                    pass
                except Exception as e:
                    logger.error(f"Error processing message from {remote_address}: {e}")
                    break
        
        except Exception as e:
            # Log any connection issues but never remove the client
            logger.info(f"WebSocket client {remote_address} connection ended: {e}")
        
    
    async def broadcast_motion_event(self, event_data):
        """Broadcast motion detection event to all connected clients - never remove clients"""
        if not self.clients:
            logger.info("No WebSocket clients connected, skipping broadcast")
            return
        
        message = json.dumps(event_data)
        logger.info(f"Broadcasting to {len(self.clients)} clients: {event_data['type']}")
        
        successful_sends = 0
        
        for client in self.clients:
            try:
                await client.send(message)
                successful_sends += 1
            except Exception as e:
                # Log errors but never remove clients - they might recover
                logger.warning(f"Error sending to WebSocket client (keeping connection): {e}")
        
        logger.info(f"Successfully sent to {successful_sends}/{len(self.clients)} clients")
    
    def start_server(self):
        """Start the WebSocket server in a separate thread"""
        def run_server():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            async def start_websocket_server():
                print(f"WebSocket server starting on ws://{self.host}:{self.port}")
                self.server = await websockets.serve(
                    self.register_client,
                    self.host,
                    self.port
                )
                print(f"WebSocket server listening on ws://{self.host}:{self.port}")
                await self.server.wait_closed()
            
            try:
                self.loop.run_until_complete(start_websocket_server())
            except Exception as e:
                print(f"WebSocket server error: {e}")
            finally:
                # Don't close the loop here - let stop_server handle it
                pass
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print("WebSocket server thread started")
    
    def stop_server(self):
        """Stop the WebSocket server"""
        print("Stopping WebSocket server...")
        
        if self.server and self.loop and not self.loop.is_closed():
            async def close_server():
                """Properly close the WebSocket server"""
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
            
            try:
                # Schedule the coroutine to close the server
                future = asyncio.run_coroutine_threadsafe(close_server(), self.loop)
                # Wait for the server to close with a timeout
                future.result(timeout=5)
                
                print("WebSocket server closed successfully")
            except Exception as e:
                print(f"Error closing WebSocket server: {e}")
        
        # Stop the event loop
        if self.loop and not self.loop.is_closed():
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except Exception as e:
                print(f"Error stopping event loop: {e}")
        
        # Wait for the server thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=3)
            if self.server_thread.is_alive():
                print("Warning: WebSocket server thread did not stop gracefully")
            else:
                print("WebSocket server thread stopped")
        
        # Close the event loop if it's still open
        if self.loop and not self.loop.is_closed():
            try:
                self.loop.close()
                print("Event loop closed")
            except Exception as e:
                print(f"Error closing event loop: {e}")
        
        print("WebSocket server stopped")
    
    def handle_motion_detection_event(self, camera_id, video_path, motion_detected, event_data):
        """Handle motion detection events and send updates to WebSocket clients"""
        # Use the provided event data (VideoMotion format)
        print(f"Motion detection event: {event_data}")
        
        # If we have an event loop and clients, broadcast the event
        if self.loop and self.clients:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.broadcast_motion_event(event_data),
                    self.loop
                )
                # Don't wait for the result to avoid blocking the motion detection thread
            except Exception as e:
                logger.error(f"Error scheduling WebSocket broadcast: {e}")
