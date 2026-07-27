"""
Redis Client
============
Async Redis client using redis-py with connection pooling.
Used for caching, session storage, and Pub/Sub.
"""

import structlog
from typing import Optional, Any
import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """
    Async Redis client wrapper with connection pooling.
    Provides methods for common cache operations and Pub/Sub.
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._is_enabled: bool = True

    async def connect(self) -> None:
        """Initialize the connection pool and verify connection."""
        if not self._is_enabled:
            return

        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            await self._client.ping()
            logger.info("Redis connection pool initialized")
        except Exception as e:
            logger.warning("Redis connection failed, disabling cache/pubsub", error=str(e))
            self._is_enabled = False
            self._client = None
            self._pool = None

    async def disconnect(self) -> None:
        """Close all connections."""
        if self._client:
            await self._client.aclose()
        logger.info("Redis connection closed")

    async def ping(self) -> bool:
        """Test Redis connectivity."""
        if not self._is_enabled:
            return False
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return False
        try:
            return await self._client.ping()
        except Exception:
            self._is_enabled = False
            return False

    async def close(self) -> None:
        await self.disconnect()

    # ── Cache Operations ──────────────────────────────────

    async def get(self, key: str) -> Optional[str]:
        """Get a cached value."""
        if not self._is_enabled:
            return None
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return None
        try:
            return await self._client.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str, expire: int = None) -> bool:
        """Set a cached value with optional TTL in seconds."""
        if not self._is_enabled:
            return False
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return False
        try:
            return await self._client.set(key, value, ex=expire)
        except Exception:
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not self._is_enabled:
            return 0
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return 0
        try:
            return await self._client.delete(*keys)
        except Exception:
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        if not self._is_enabled:
            return False
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return False
        try:
            return bool(await self._client.exists(key))
        except Exception:
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set TTL on an existing key."""
        if not self._is_enabled:
            return False
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return False
        try:
            return await self._client.expire(key, seconds)
        except Exception:
            return False

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        if not self._is_enabled:
            return 0
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return 0
        try:
            return await self._client.incr(key)
        except Exception:
            return 0

    async def hset(self, name: str, mapping: dict) -> int:
        """Set hash fields."""
        if not self._is_enabled:
            return 0
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return 0
        try:
            return await self._client.hset(name, mapping=mapping)
        except Exception:
            return 0

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get a hash field."""
        if not self._is_enabled:
            return None
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return None
        try:
            return await self._client.hget(name, key)
        except Exception:
            return None

    async def hgetall(self, name: str) -> dict:
        """Get all hash fields."""
        if not self._is_enabled:
            return {}
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return {}
        try:
            return await self._client.hgetall(name)
        except Exception:
            return {}

    # ── Pub/Sub ───────────────────────────────────────────

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel."""
        if not self._is_enabled:
            return 0
        if not self._client:
            await self.connect()
            if not self._is_enabled:
                return 0
        try:
            return await self._client.publish(channel, message)
        except Exception:
            return 0

    def pubsub(self):
        """Get a Pub/Sub connection."""
        if not self._is_enabled or not self._client:
            raise RuntimeError("Redis not connected or disabled")
        return self._client.pubsub()

    # ── Token Blacklist (for JWT logout) ──────────────────

    async def blacklist_token(self, jti: str, expire_seconds: int) -> None:
        """Add a JWT ID to the blacklist."""
        await self.set(f"bl:{jti}", "1", expire=expire_seconds)

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a JWT has been blacklisted."""
        return await self.exists(f"bl:{jti}")

    # ── Session Caching ───────────────────────────────────

    async def cache_user_session(self, user_id: str, session_data: dict) -> None:
        """Cache active user session data."""
        import json

        await self.set(
            f"session:{user_id}",
            json.dumps(session_data),
            expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def get_cached_session(self, user_id: str) -> Optional[dict]:
        """Get cached user session."""
        import json

        data = await self.get(f"session:{user_id}")
        return json.loads(data) if data else None


# Optional type hint
from typing import Optional

# Singleton instance
redis_client = RedisClient()
