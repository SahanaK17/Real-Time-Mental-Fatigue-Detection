"""
WebSocket Connection Manager
=============================
Manages per-user WebSocket connections with Redis Pub/Sub
for scalable real-time broadcast across multiple workers.
"""

import asyncio
import json
from typing import Dict, Set

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """
    Manages active WebSocket connections per user.

    Architecture:
    - Each user can have multiple active connections (e.g., multiple browser tabs)
    - Redis Pub/Sub allows broadcasting across multiple FastAPI worker processes
    - Messages are JSON strings
    """

    def __init__(self):
        # user_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._redis_subscriber = None

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        logger.info("WebSocket connected", user_id=user_id, total=len(self._connections[user_id]))

    def disconnect(self, user_id: str, websocket: WebSocket = None) -> None:
        """Remove a WebSocket connection."""
        if user_id in self._connections:
            if websocket:
                self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id)

    async def send_to_user(self, user_id: str, message: str) -> None:
        """Send a message to all connections of a specific user."""
        if user_id not in self._connections:
            return

        dead_connections = set()
        for ws in self._connections[user_id].copy():
            try:
                await ws.send_text(message)
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self._connections[user_id].discard(ws)

    async def broadcast_to_user(self, user_id: str, message: str) -> None:
        """
        Broadcast a message to a user via both direct connections and Redis Pub/Sub.
        Redis Pub/Sub ensures delivery even when the user is connected to a different worker.
        """
        # Direct send to locally connected clients
        await self.send_to_user(user_id, message)

        # Also publish via Redis for multi-worker support
        try:
            from app.core.redis_client import redis_client
            await redis_client.publish(f"ws:user:{user_id}", message)
        except Exception as e:
            logger.warning("Redis publish failed", error=str(e), user_id=user_id)

    async def broadcast_to_all(self, message: str) -> None:
        """Broadcast a message to all connected users."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)

    def get_connected_users(self) -> list:
        """Return list of currently connected user IDs."""
        return list(self._connections.keys())

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._connections and bool(self._connections[user_id])

    async def start_redis_listener(self) -> None:
        """
        Subscribe to Redis Pub/Sub and forward messages to local WebSocket connections.
        Should be started as a background task.
        """
        try:
            from app.core.redis_client import redis_client
            pubsub = redis_client.pubsub()
            await pubsub.psubscribe("ws:user:*")

            logger.info("Redis WebSocket subscriber started")

            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    channel = message["channel"]
                    # Extract user_id from channel name "ws:user:{user_id}"
                    user_id = channel.split("ws:user:")[-1]
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode()
                    # Only send to locally connected clients (avoids double-sending)
                    await self.send_to_user(user_id, data)

        except Exception as e:
            logger.error("Redis subscriber error", error=str(e))


# Singleton instance
ws_manager = WebSocketManager()
