import abc
from typing import Any, Optional


class ICacheOperations(abc.ABC):
    @abc.abstractmethod
    def set(self, key: str, obj: Any, ttl: Optional[float] = None) -> None:
        pass

    @abc.abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        pass
