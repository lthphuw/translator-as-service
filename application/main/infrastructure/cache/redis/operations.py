import json
import logging
from typing import Any, Optional

import pybreaker
import redis
from pytimeparse.timeparse import timeparse
from redis.exceptions import ConnectionError, TimeoutError

from application.main.config import settings
from application.main.infrastructure.cache.cache_interface import ICacheOperations
from application.main.utility.config_loader import ConfigReaderInstance
from application.main.utility.retry import retry

logger = logging.getLogger(__name__)


class Redis(ICacheOperations):
    @retry(service=__name__, logger=logger)
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

        self.redis = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            decode_responses=False,
        )

        self.redis_breaker = pybreaker.CircuitBreaker(
            fail_max=3,
            reset_timeout=60,
            state_storage=pybreaker.CircuitRedisStorage(
                pybreaker.STATE_CLOSED, self.redis
            ),
        )

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

    def set(self, key: str, obj: Any, ttl: Optional[float] = None) -> None:
        value = obj if isinstance(obj, (str, bytes)) else json.dumps(obj)

        @self.redis_breaker
        def protected_set():
            if ttl is not None:
                self.redis.set(key, value, ex=int(ttl))
            else:
                self.redis.set(key, value, ex=int(self.config.ttl))

        try:
            protected_set()
        except pybreaker.CircuitBreakerError:
            logger.error(f"Circuit breaker is open: failed to set key {key}")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis set error: {e}")

    def get(self, key: str) -> Optional[Any]:
        @self.redis_breaker
        def protected_get():
            return self.redis.get(key)

        try:
            result = protected_get()
            try:
                return json.loads(result)
            except (TypeError, json.JSONDecodeError):
                return result
        except pybreaker.CircuitBreakerError:
            logger.error(f"Circuit breaker is open: failed to get key {key}")
            return None
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis get error: {e}")
            return None

    def delete(self, key: str) -> None:
        @self.redis_breaker
        def protected_delete():
            self.redis.delete(key)

        try:
            protected_delete()
        except pybreaker.CircuitBreakerError:
            logger.error(f"Circuit breaker is open: failed to delete key {key}")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis delete error: {e}")
