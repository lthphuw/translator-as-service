from abc import ABC, abstractmethod

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class IMiddleware(BaseHTTPMiddleware, ABC):
    @abstractmethod
    def __init__(self, app: ASGIApp):
        raise NotImplementedError

    @abstractmethod
    async def dispatch_func(self, request: Request, call_next):
        raise NotImplementedError
