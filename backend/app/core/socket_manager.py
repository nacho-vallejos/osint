"""
WebSocket Manager with Redis Pub/Sub
Manages real-time connections for OSINT scan updates.
"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and Redis Pub/Sub subscriptions.
    Enables real-time notifications for scan task updates.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        # Active WebSocket connections per task_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Redis client for pub/sub
        self.redis_url = redis_url
        self.redis_client: aioredis.Redis | None = None
        
        # Background tasks for listening to Redis
        self.listener_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info(f"ConnectionManager initialized with Redis: {redis_url}")
    
    async def get_redis_client(self) -> aioredis.Redis:
        """Get or create Redis async client"""
        if self.redis_client is None:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis async client created")
        return self.redis_client
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """
        Accept WebSocket connection and start listening for updates.
        
        Args:
            websocket: FastAPI WebSocket instance
            task_id: Task ID to subscribe to
        """
        await websocket.accept()
        
        # Add connection to tracking
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        
        logger.info(f"WebSocket connected for task {task_id}. Total connections: {len(self.active_connections[task_id])}")
        
        # Start Redis listener if not already running for this task
        if task_id not in self.listener_tasks or self.listener_tasks[task_id].done():
            self.listener_tasks[task_id] = asyncio.create_task(
                self._redis_listener(task_id)
            )
            logger.info(f"Started Redis listener for task {task_id}")
    
    async def disconnect(self, websocket: WebSocket, task_id: str):
        """
        Remove WebSocket connection and cleanup if no more clients.
        
        Args:
            websocket: FastAPI WebSocket instance
            task_id: Task ID to unsubscribe from
        """
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            
            # If no more connections for this task, stop listener
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
                
                # Cancel the Redis listener task
                if task_id in self.listener_tasks:
                    self.listener_tasks[task_id].cancel()
                    del self.listener_tasks[task_id]
                
                logger.info(f"All clients disconnected from task {task_id}. Listener stopped.")
            else:
                logger.info(f"Client disconnected from task {task_id}. Remaining: {len(self.active_connections[task_id])}")
    
    async def _redis_listener(self, task_id: str):
        """
        Background task that listens to Redis Pub/Sub for a specific task.
        Broadcasts received messages to all connected WebSocket clients.
        
        Args:
            task_id: Task ID to listen for
        """
        redis = await self.get_redis_client()
        channel_name = f"scan_updates:{task_id}"
        
        try:
            # Create pubsub instance
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel_name)
            
            logger.info(f"Subscribed to Redis channel: {channel_name}")
            
            # Listen for messages
            async for message in pubsub.listen():
                # Skip subscription confirmation messages
                if message["type"] == "message":
                    data = message["data"]
                    logger.info(f"Received message on {channel_name}: {data[:100]}...")
                    
                    # Parse JSON if it's a string
                    try:
                        if isinstance(data, str):
                            json_data = json.loads(data)
                        else:
                            json_data = data
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse message as JSON: {data}")
                        continue
                    
                    # Broadcast to all connected clients
                    await self.broadcast(task_id, json_data)
                    
                    # If scan is complete, stop listening
                    if json_data.get("status") in ["SUCCESS", "FAILURE"]:
                        logger.info(f"Scan {task_id} completed. Stopping listener.")
                        break
        
        except asyncio.CancelledError:
            logger.info(f"Redis listener for {task_id} cancelled")
        except Exception as e:
            logger.error(f"Error in Redis listener for {task_id}: {e}", exc_info=True)
        finally:
            # Cleanup subscription
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
                logger.info(f"Unsubscribed from {channel_name}")
            except Exception as e:
                logger.error(f"Error unsubscribing: {e}")
    
    async def broadcast(self, task_id: str, message: dict):
        """
        Send message to all WebSocket clients subscribed to a task.
        
        Args:
            task_id: Task ID to broadcast to
            message: Dictionary to send as JSON
        """
        if task_id not in self.active_connections:
            logger.warning(f"No active connections for task {task_id}")
            return
        
        # Get copy of connections to avoid modification during iteration
        connections = list(self.active_connections[task_id])
        
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
                logger.debug(f"Sent message to client on task {task_id}")
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket, task_id)
    
    async def publish_update(self, task_id: str, message: dict):
        """
        Publish an update to Redis for a specific task.
        This is typically called from Celery workers.
        
        Args:
            task_id: Task ID to publish update for
            message: Dictionary to publish
        """
        redis = await self.get_redis_client()
        channel_name = f"scan_updates:{task_id}"
        
        try:
            # Serialize message to JSON
            json_message = json.dumps(message)
            
            # Publish to Redis
            await redis.publish(channel_name, json_message)
            logger.info(f"Published update to {channel_name}")
        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}", exc_info=True)
    
    async def close(self):
        """Cleanup all connections and Redis client"""
        # Cancel all listener tasks
        for task in self.listener_tasks.values():
            task.cancel()
        
        # Close all WebSocket connections
        for connections in self.active_connections.values():
            for websocket in connections:
                try:
                    await websocket.close()
                except Exception:
                    pass
        
        # Close Redis client
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("ConnectionManager closed")


# Global instance
connection_manager: ConnectionManager | None = None


def get_connection_manager(redis_url: str = "redis://localhost:6379/0") -> ConnectionManager:
    """Get or create global ConnectionManager instance"""
    global connection_manager
    if connection_manager is None:
        connection_manager = ConnectionManager(redis_url)
    return connection_manager
