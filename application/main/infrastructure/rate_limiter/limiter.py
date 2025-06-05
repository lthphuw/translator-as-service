import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import redis
from redis.exceptions import ConnectionError, TimeoutError

from application.main.infrastructure.cache.redis.operations import Redis

logger = logging.getLogger(__name__)
_limiter = None


def test_redis_connection(url: str) -> bool:
    try:
        client = redis.Redis.from_url(url)
        client.ping()
        logger.info(f"[RateLimit] Successfully connected to Redis at {url}")
        return True
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"[RateLimit] Redis unavailable: {e}")
        return False


def get_limiter() -> Limiter:
    global _limiter
    if _limiter is not None:
        return _limiter

    redis_url = Redis.get_uri()
    storage_uri = (
        redis_url if redis_url.startswith("redis://") else f"redis://{redis_url}"
    )

    if test_redis_connection(redis_url):
        logger.info("[RateLimit] Using Redis storage")
        _limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["5/minute"],
            strategy="sliding-window-counter",
            storage_uri=storage_uri,
        )
    else:
        logger.warning("[RateLimit] Falling back to MemoryStorage")
        _limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["5/minute"],
            strategy="sliding-window-counter",
            storage_uri="memory://",
        )
    return _limiter


def setup_rate_limit(app: FastAPI):
    app.state.limiter = get_limiter()

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Too Many Requests, retry after {getattr(exc, 'retry_after', 60)}",
                "retry_after": getattr(exc, "retry_after", 60),
            },
        )

    app.add_middleware(SlowAPIMiddleware)
