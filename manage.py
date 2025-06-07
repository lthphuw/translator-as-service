from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from application.initializer import IncludeAPIRouter
from application.main.config import settings
from application.main.infrastructure.rate_limiter.limiter import setup_rate_limit
from application.main.middlewares import LoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown code ...


def get_application():
    _app = FastAPI(
        title=settings.API_NAME,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        lifespan=lifespan,
    )
    _app.include_router(IncludeAPIRouter())

    _app.add_middleware(
        CORSMiddleware,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.add_middleware(LoggingMiddleware)

    setup_rate_limit(_app)
    return _app


app = get_application()

if __name__ == "__main__":
    uvicorn.run(
        "manage:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
        use_colors=True,
        reload=True,
    )
