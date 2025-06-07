import hashlib
from typing import Callable, Dict, List
from concurrent.futures import ThreadPoolExecutor

import torch

from application.initializer import cache_instance, logger_instance
from application.main.infrastructure.translator.translators import (
    EnViTranslator,
    BaseTranslator,
    ViEnTranslator,
)

logger = logger_instance.get_logger(__name__)
_cache = cache_instance


class UniversalTranslator:
    """UniversalTranslator provides translation services between supported language pairs.

    This class manages multiple translation models, handles model loading in parallel, and caches translation results for efficiency.
    """
    SUPPORTED_LANGUAGES: Dict[str, List[str]] = {
        "vi": ["en"],
        "en": ["vi"],
    }

    TRANSLATOR_FACTORIES: Dict[str, Callable[[], BaseTranslator]] = {
        "vi2en": ViEnTranslator,
        "en2vi": EnViTranslator,
    }

    def __init__(self):
        self.translators: Dict[str, BaseTranslator] = {}

        # Eager load all supported translators in parallel
        with ThreadPoolExecutor() as executor:
            futures = []
            for src_lang, tgt_langs in self.SUPPORTED_LANGUAGES.items():
                for tgt_lang in tgt_langs:
                    key = self.__key(src_lang, tgt_lang)
                    logger.info(f"Submitting translator loading task: {key}")
                    futures.append(executor.submit(self.__load_translator, src_lang, tgt_lang))

            for future in futures:
                try:
                    future.result()  # Force exception to surface if any
                except Exception as e:
                    logger.error(f"Failed to load translator: {e}")
                    raise

    def __key(self, src_lang: str, tgt_lang: str) -> str:
        return f"{src_lang}2{tgt_lang}"

    def __load_translator(self, src_lang: str, tgt_lang: str):
        """Used for eager loading at init with ThreadPoolExecutor"""
        key = self.__key(src_lang, tgt_lang)
        if key not in self.translators:
            factory = self.TRANSLATOR_FACTORIES.get(key)
            if not factory:
                raise ValueError(f"No translator factory for {key}")
            logger.info(f"Loading translator model: {key}")
            self.translators[key] = factory()
            logger.info(f"Loading translator model: {key} Finished!")

    def __get_translator(self, src_lang: str, tgt_lang: str) -> BaseTranslator:
        key = self.__key(src_lang, tgt_lang)
        if translator := self.translators.get(key):
            return translator
        else:
            raise ValueError(f"Translator for {key} not loaded")

    async def translate(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if tgt_lang not in self.SUPPORTED_LANGUAGES.get(src_lang, []):
            logger.error(f"Unsupported translation: {src_lang} -> {tgt_lang}")
            raise ValueError(f"Translation from {src_lang} to {tgt_lang} is not supported")

        translator = self.__get_translator(src_lang, tgt_lang)
        cache_key_prefix = self.__key(src_lang, tgt_lang)
        cached_results = {}
        texts_to_translate = []

        for text in texts:
            key = cache_key_prefix + hashlib.md5(text.encode()).hexdigest()
            if result := _cache.get(key):
                logger.debug(f"cache hit: {cache_key_prefix}:{text}")
                cached_results[text] = result.decode("utf-8")
            else:
                texts_to_translate.append(text)

        if texts_to_translate:
            logger.debug(f"translating {len(texts_to_translate)} texts with {src_lang}2{tgt_lang}")
            new_translations = translator.translate(texts_to_translate)

            for text, translated in zip(texts_to_translate, new_translations):
                key = cache_key_prefix + hashlib.md5(text.encode()).hexdigest()
                cached_results[text] = translated
                _cache.set(key, translated)

        return [cached_results[text] for text in texts]

    def device(self) -> str:
        return str(
            torch.device(
                "cuda" if torch.cuda.is_available() else
                "mps" if torch.backends.mps.is_available() else
                "cpu"
            )
        )

    def get_supported_languages(self) -> Dict[str, List[str]]:
        return self.SUPPORTED_LANGUAGES
