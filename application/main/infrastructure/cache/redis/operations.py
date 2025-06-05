import json
import logging
from typing import Any, Optional

import redis.asyncio as redis  # Sử dụng async client cho FastAPI
from pytimeparse.timeparse import timeparse
from redis.exceptions import ConnectionError, TimeoutError

from application.main.config import settings
from application.main.infrastructure.cache.cache_interface import CacheOperations
from application.main.utility.config_loader import ConfigReaderInstance

logger = logging.getLogger(__name__)


class Redis(CacheOperations):
    def __init__(self):
        super().__init__()
        self.config = ConfigReaderInstance.yaml.read_config_from_file(
            settings.CACHE + "_config.yaml"
        )

        if not all(hasattr(self.config, attr) for attr in ["host", "port", "ttl"]):
            raise ValueError("Invalid Redis config: missing host, port, or ttl")

        ttl = timeparse(self.config.ttl)
        if ttl is None or ttl <= 0:
            ttl = None

        setattr(self.config, "ttl", ttl)

        # Sử dụng connection pool cho thread-safety
        self.pool = redis.ConnectionPool(
            host=self.config.host,
            port=self.config.port,
            decode_responses=True,
            max_connections=10,
        )
        self.r = redis.Redis(connection_pool=self.pool)

    @classmethod
    def get_uri(cls, config: Any = None) -> str:
        """
        Class method to get Redis URI from config.
        If config is not provided, use default values.
        """
        config = config or ConfigReaderInstance.yaml.read_config_from_file(
            settings.CACHE + "_config.yaml"
        )
        host = getattr(config, "host", "localhost")
        port = getattr(config, "port", 6379)
        return f"redis://{host}:{port}"

    async def set(self, key: str, obj: Any, ttl: Optional[float] = None) -> None:
        """
        Set a key-value pair in Redis with optional TTL.
        Serialize obj to JSON if it's not a string.
        """
        try:
            value = obj if isinstance(obj, (str, bytes)) else json.dumps(obj)
            async with self.r as client:
                if ttl is not None:
                    await client.set(key, value, ex=int(ttl))
                else:
                    await client.set(key, value, ex=int(self.config.ttl))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to set key {key} in Redis: {e}")
            raise

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis by key.
        Deserialize JSON if the value is a JSON string.
        """
        try:
            async with self.r as client:
                value = await client.get(key)
                if value is None:
                    return None
                # Try to deserialize as JSON, fallback to raw value
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to get key {key} from Redis: {e}")
            raise

    async def delete(self, key: str) -> None:
        """Delete a key from Redis."""
        try:
            async with self.r as client:
                await client.delete(key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to delete key {key} from Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection pool."""
        await self.r.close()
        await self.pool.disconnect()
        logger.info("Redis connection pool closed")
