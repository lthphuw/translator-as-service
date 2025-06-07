import json
import time

from fastapi import Request, Response
from starlette.types import ASGIApp

from application.initializer import logger_instance
from application.main.middlewares.middleware_interface import IMiddleware

logger = logger_instance.get_logger(__name__)


class LoggingMiddleware(IMiddleware):
    def __init__(self, app: ASGIApp):
        self.app = app

    async def dispatch_func(self, request: Request, call_next):
        start_time = time.time()

        # Read body safely
        body_bytes = await request.body()
        request_body = self._parse_body(body_bytes)

        # Rebuild request stream (because it can be read only once)
        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = receive

        # Process request
        response: Response = await call_next(request)

        process_time = (time.time() - start_time) * 1000  # in ms

        log_data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "body": request_body,
            "status_code": response.status_code,
            "process_time_ms": round(process_time, 2),
        }

        logger.debug("HTTP request log", extra=log_data)

        return response

    def _parse_body(self, body_bytes: bytes):
        try:
            body_str = body_bytes.decode("utf-8")
            return json.loads(body_str)
        except Exception:
            return body_bytes.decode("utf-8", errors="ignore")
