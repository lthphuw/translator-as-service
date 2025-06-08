import asyncio
import hashlib
from typing import Dict, List

import torch

from application.initializer import cache_instance, logger_instance
from application.main.infrastructure.translator.translators import (
    TRANSLATOR_FACTORY,
    BaseTranslator,
)

logger = logger_instance.get_logger(__name__)
_cache = cache_instance


class UniversalTranslator:
    """UniversalTranslator provides translation services between supported language pairs.

    This class manages multiple translation models, acts like Registry Pattern,
    handles model loading, and caches translation results for efficiency.
    """

    SUPPORTED_LANGUAGES: Dict[str, List[str]] = {
        "vi": ["en", "fr"],
        "en": ["vi", "fr"],
        "fr": ["en", "vi"],
    }

    def __init__(self):
        self.translators: Dict[str, BaseTranslator] = {}

        for src_lang, tgt_langs in self.SUPPORTED_LANGUAGES.items():
            for tgt_lang in tgt_langs:
                key = self.__key(src_lang, tgt_lang)
                logger.info(f"Register translator model: {key}")
                try:
                    self.__register_translator(src_lang, tgt_lang)
                except Exception as e:
                    logger.error(f"Failed to load translator {key}: {e}")
                    raise

    def __key(self, src_lang: str, tgt_lang: str) -> str:
        return f"{src_lang}2{tgt_lang}"

    def _make_cache_key(self, src_lang: str, tgt_lang: str, text: str) -> str:
        prefix = self.__key(src_lang, tgt_lang)
        return f"{prefix}:{hashlib.md5(text.encode()).hexdigest()}"

    def __register_translator(self, src_lang: str, tgt_lang: str):
        key = self.__key(src_lang, tgt_lang)
        if key not in self.translators:
            factory = TRANSLATOR_FACTORY.get(key)
            if not factory:
                raise ValueError(f"No translator factory for {key}")
            self.translators[key] = factory()
            logger.info(f"Loading translator model: {key} Finished!")

    def __get_translator(self, src_lang: str, tgt_lang: str) -> BaseTranslator:
        key = self.__key(src_lang, tgt_lang)
        translator = self.translators.get(key)
        if translator is None:
            raise ValueError(f"Translator for {key} not loaded")
        return translator

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
        cached_results: Dict[str, str] = {}
        texts_to_translate: List[str] = []

        for text in texts:
            key = self._make_cache_key(src_lang, tgt_lang, text)
            if result := _cache.get(key):
                logger.debug(f"cache hit: {cache_key_prefix}:{text}")
                cached_results[text] = result.decode("utf-8")
            else:
                texts_to_translate.append(text)

        if texts_to_translate:
            logger.debug(
                f"translating {len(texts_to_translate)} texts with {cache_key_prefix}"
            )
            translations = await asyncio.to_thread(
                translator.translate, texts_to_translate
            )

            for text, translated in zip(texts_to_translate, translations):
                key = self._make_cache_key(src_lang, tgt_lang, text)
                cached_results[text] = translated
                _cache.set(key, translated)

        return [cached_results[text] for text in texts]

    def device(self) -> str:
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
