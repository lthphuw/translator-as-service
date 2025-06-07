import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from application.main.infrastructure.cache.redis.operations import Redis

logger = logging.getLogger(__name__)
_limiter = None


def get_limiter() -> Limiter:
    global _limiter
    if _limiter is not None:
        return _limiter

    storage_uri = Redis.get_uri()
    _limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["5/minute"],
    strategy="sliding-window-counter",
        storage_uri=storage_uri,
        in_memory_fallback_enabled=True,
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
