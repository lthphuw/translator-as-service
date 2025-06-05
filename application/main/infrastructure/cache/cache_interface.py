import abc
from typing import Any, Optional


class CacheOperations(abc.ABC):
    @abc.abstractmethod
    async def set(self, key: str, obj: Any, ttl: Optional[float] = None) -> None:
        pass

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abc.abstractmethod
    async def delete(self, key: str) -> None:
        pass
