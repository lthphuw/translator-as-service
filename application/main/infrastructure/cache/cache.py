from typing import Any, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from application.initializer import logger_instance
from application.main.config import settings
from application.main.infrastructure.cache import CacheToUse

logger = logger_instance.get_logger(__name__)


def cache_retry():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type(Exception),
        reraise=True,
        before_sleep=lambda r: logger.warning(
            f"Retrying Redis due to: {r.outcome.exception()}"  # type: ignore
        ),
    )


class Cache:
    def __init__(self):
        self._cache = CacheToUse[settings.CACHE]

    @cache_retry()
    async def __set(self, key: str, obj: Any, ttl: Optional[float] = None) -> None:
        await self._cache.set(key, obj, ttl)

    async def set(
        self, key: str, obj: Any, ttl: Optional[float] = None
    ) -> Optional[bool]:
        try:
            await self.__set(key, obj, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key={key}: {e}")
            return None

    @cache_retry()
    async def __get(self, key: str) -> Optional[Any]:
        return await self._cache.get(key)

    async def get(self, key: str) -> Optional[Any]:
        try:
            return await self.__get(key)
        except Exception as e:
            logger.error(f"Failed to get cache key={key}: {e}")
            return None

    @cache_retry()
    async def __delete(self, key: str) -> None:
        await self._cache.delete(key)

    async def delete(self, key: str) -> Optional[bool]:
        try:
            await self.__delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key={key}: {e}")
            return None
