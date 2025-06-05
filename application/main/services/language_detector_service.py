import time
from typing import Dict

from application.initializer import logger_instance
from application.main.infrastructure.lang_detector import LanguageDetector


class LanguageDetectorService(object):
    def __init__(self):
        self.logger = logger_instance.get_logger(__name__)
        self.detector = LanguageDetector()

    async def detect(self, text: str) -> Dict:
        start_time = time.time()
        lang = self.detector.detect(text)
        duration_ms = (time.time() - start_time) * 1000

        self.logger.info(
            f"Detecting language text {text}: {lang}",
            extra={
                "input": text,
                "detected_lang": lang,
                "duration_ms": duration_ms,
            },
        )

        return {
            "detected_lang": lang,
            "time": f"{round(duration_ms / 1000, 2)}s",
        }
