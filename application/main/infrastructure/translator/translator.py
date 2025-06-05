import asyncio
import hashlib
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List

import torch

from application.initializer import cache_instance, logger_instance
from application.main.infrastructure.translator.translators import (
    BaseTranslator,
    EnViTranslator,
    ViEnTranslator,
)

logger = logger_instance.get_logger(__name__)
_cache = cache_instance


class UniversalTranslator:
    SUPPORTED_LANGUAGES: Dict[str, List[str]] = {
        "vi": ["en"],
        "en": ["vi"],
    }

    def __init__(self):
        self.translators: Dict[str, BaseTranslator] = {}
        self.lock = asyncio.Lock()

    def __key(self, src_lang: str, tgt_lang: str):
        return f"{src_lang}2{tgt_lang}"

    def __get_translator(self, src_lang: str, tgt_lang: str) -> BaseTranslator:
        if tgt_lang not in self.SUPPORTED_LANGUAGES.get(src_lang, []):
            logger.error(f"Unsupported translation model: {src_lang} -> {tgt_lang}")
            raise ValueError(f"Translation from {src_lang} to {tgt_lang} not supported")

        key = self.__key(src_lang, tgt_lang)
        if key not in self.translators:
            logger.info(f"Loading model {key} for the first time...")
            if key == "vi2en":
                self.translators[key] = ViEnTranslator()
            elif key == "en2vi":
                self.translators[key] = EnViTranslator()

        return self.translators[key]

    async def translate(
        self, texts: List[str], src_lang: str, tgt_lang: str
    ) -> List[str]:
        if tgt_lang not in self.SUPPORTED_LANGUAGES.get(src_lang, []):
            logger.error(f"Unsupported translation: {src_lang} -> {tgt_lang}")
            raise ValueError(
                f"Translation from {src_lang} to {tgt_lang} is not supported"
            )

        translator = self.__get_translator(src_lang, tgt_lang)
        cache_key_prefix = self.__key(src_lang, tgt_lang)
        cached_results = {}
        texts_to_translate = []

        for text in texts:
            key = cache_key_prefix + hashlib.md5(text.encode()).hexdigest()
            result = await _cache.get(key)
            if result:
                cached_results[text] = result
            else:
                texts_to_translate.append(text)

        if texts_to_translate:
            async with self.lock:
                logger.debug(
                    f"Translating {len(texts_to_translate)} texts with {src_lang}2{tgt_lang}"
                )
                new_translations = await asyncio.get_event_loop().run_in_executor(
                    ProcessPoolExecutor(),
                    translator.translate,
                    texts_to_translate,
                )
                for text, translated in zip(texts_to_translate, new_translations):
                    key = cache_key_prefix + hashlib.md5(text.encode()).hexdigest()
                    cached_results[text] = translated
                    await _cache.set(key, translated)

        return [cached_results[text] for text in texts]

    def device(self):
        return str(
            torch.device(
                "cuda"
                if torch.cuda.is_available()
                else "mps"
                if torch.backends.mps.is_available()
                else "cpu"
            )
        )

    def get_supported_languages(self) -> Dict[str, List[str]]:
        return self.SUPPORTED_LANGUAGES
