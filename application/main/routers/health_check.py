from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from application.initializer import logger_instance

# _db = db_instance
router = APIRouter(prefix="/health-check")
logger = logger_instance.get_logger(__name__)


@router.get("/")
async def health_check():
    logger.info("Health Check")
    return JSONResponse(content="OK", status_code=200)
