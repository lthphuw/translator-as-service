from typing import Any, Optional


from application.initializer import logger_instance
from application.main.config import settings
from application.main.infrastructure.cache import CacheToUse

logger = logger_instance.get_logger(__name__)


class Cache:
    def __init__(self):
        self._cache = CacheToUse[settings.CACHE]

    def __set(self, key: str, obj: Any, ttl: Optional[float] = None) -> None:
        self._cache.set(key, obj, ttl)

    def set(self, key: str, obj: Any, ttl: Optional[float] = None) -> Optional[bool]:
        try:
            self.__set(key, obj, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key={key}: {e}")
            return None

    def __get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def get(self, key: str) -> Optional[Any]:
        try:
            return self.__get(key)
        except Exception as e:
            logger.error(f"Failed to get cache key={key}: {e}")
            return None

    def __delete(self, key: str) -> None:
        self._cache.delete(key)

    def delete(self, key: str) -> Optional[bool]:
        try:
            self.__delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key={key}: {e}")
            return None
