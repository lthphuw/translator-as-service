from abc import ABC, abstractmethod
from typing import List


class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, texts: List[str]) -> List[str]:
        pass

    @abstractmethod
    def device(self) -> str:
        pass
