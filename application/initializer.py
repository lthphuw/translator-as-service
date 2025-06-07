class IncludeAPIRouter(object):
    def __new__(cls):
        from fastapi.routing import APIRouter

        from application.main.routers.health_check import router as router_health_check
        from application.main.routers.translate import router as router_translator
        from application.main.config import settings

        # Get the major version
        major =  settings.API_VERSION.split('.')[0]
        prefix = f"/api/v{major}"

        router = APIRouter()
        router.include_router(
            router_health_check, prefix=prefix, tags=["health_check"]
        )
        router.include_router(router_translator, prefix=prefix, tags=["translate"])
        return router

class LoggerInstance(object):
    def __new__(cls):
        from application.main.utility.logger.logging import LogHandler

        return LogHandler()

class DataBaseInstance(object):
    def __new__(cls):
        from application.main.infrastructure.database import db

        return db.DataBase()


class CacheInstance(object):
    def __new__(cls):
        from application.main.infrastructure.cache import cache

        return cache.Cache()


class LimiterInstance(object):
    def __new__(cls):
        from application.main.infrastructure.rate_limiter import get_limiter

        return get_limiter()

# instance creation
logger_instance = LoggerInstance()
db_instance = DataBaseInstance()
cache_instance = CacheInstance()
limiter_instance = LimiterInstance()
