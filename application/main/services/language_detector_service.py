import asyncio
import time
from typing import Dict

from application.initializer import logger_instance
from application.main.infrastructure.detector import Detector


class DetectorService(object):
    _max_concurrent_inference = 5
    _semaphore = asyncio.Semaphore(_max_concurrent_inference)
    _semaphore_timeout_sec = 10

    def __init__(self):
        self.logger = logger_instance.get_logger(__name__)
        self.detector = Detector()

    async def detect(self, texts: list[str]) -> Dict:
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(), timeout=self._semaphore_timeout_sec
            )
        except asyncio.TimeoutError as e:
            raise RuntimeError("Server is busy. Please try again later.") from e

        try:
            start_time = time.time()
            lang = self.detector.detect(texts)[0]["language"]
            duration_ms = (time.time() - start_time) * 1000

            self.logger.info(
                f"Detecting language texts {texts}: {lang}",
                extra={
                    "input": texts,
                    "detected_lang": lang,
                    "duration_ms": duration_ms,
                },
            )

            return {
                "detected_lang": lang,
                "time": f"{round(duration_ms / 1000, 2)}s",
            }

        finally:
            self._semaphore.release()
