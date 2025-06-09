from typing import List, Optional

from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel
from starlette.requests import Request as StarletteRequest

from application.initializer import limiter_instance, logger_instance
from application.main.services import DetectorService, TranslationService


class TranslationRequest(BaseModel):
    texts: List[str]
    src_lang: Optional[str] = None
    tgt_lang: str


translation_service = TranslationService()
language_detector_service = DetectorService()
router = APIRouter(prefix="/translate")
limiter = limiter_instance
logger = logger_instance.get_logger(__name__)


@router.post("/")
@limiter.limit("50/minute")
async def translate(request: StarletteRequest, translation_request: TranslationRequest):
    logger.debug(
        "Received translation request", extra={"payload": translation_request.dict()}
    )
    try:
        if translation_request.src_lang is None:
            logger.debug(
                "Source language not provided, attempting detection",
                extra={"payload": translation_request.dict()},
            )
            detected_result = await language_detector_service.detect(
                translation_request.texts
            )
            translation_request.src_lang = detected_result["detected_lang"]

            logger.debug(
                "Language detected", extra={"detection_result": detected_result}
            )

        results = await translation_service.translate(
            translation_request.texts,
            translation_request.src_lang or "",
            translation_request.tgt_lang,
        )

        logger.info(
            "Translation completed successfully",
            extra={
                "source_lang": translation_request.src_lang,
                "target_lang": translation_request.tgt_lang,
                "num_texts": len(translation_request.texts),
            },
        )

        return JSONResponse(content=results, status_code=200)

    except RuntimeError as e:
        if str(e) == "Server is busy. Please try again later.":
            logger.warning("Request rejected due to overload")
            return JSONResponse(
                content={"detail": "Server is busy. Please try again later."},
                status_code=429,
            )
        raise e
    except ValueError as e:
        logger.error(
            "Translation failed",
            extra={"error": str(e), "payload": translation_request.dict()},
        )
        return JSONResponse(content={"detail": str(e)}, status_code=400)
