import asyncio
import time
from typing import Dict, List

from application.initializer import logger_instance
from application.main.infrastructure.translator import UniversalTranslator


class TranslationService:
    _max_concurrent_inference = 5
    _semaphore = asyncio.Semaphore(_max_concurrent_inference)
    _semaphore_timeout_sec = 5

    def __init__(self):
        self.logger = logger_instance.get_logger(__name__)
        self.translator = UniversalTranslator()

    async def translate(self, texts: List[str], src_lang: str, tgt_lang: str) -> Dict:
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(), timeout=self._semaphore_timeout_sec
            )
        except asyncio.TimeoutError as e:
            raise RuntimeError("Server is busy. Please try again later.") from e

        try:
            start_time = time.time()
            results = await self.translator.translate(texts, src_lang, tgt_lang)
            duration_ms = (time.time() - start_time) * 1000

            self.logger.info(
                f"Translating {len(texts)} texts from {src_lang} to {tgt_lang} in {duration_ms:.2f} ms on {self.translator.device()}",
                extra={
                    "src_lang": src_lang,
                    "tgt_lang": tgt_lang,
                    "input": texts,
                    "output": results,
                    "device": self.translator.device(),
                    "num_texts": len(texts),
                    "duration_ms": duration_ms,
                },
            )

            return {
                "results": results,
                "time": f"{(duration_ms / 1000):.2f}s",
                "src_lang": src_lang,
                "tgt_lang": tgt_lang,
            }
        finally:
            self._semaphore.release()
