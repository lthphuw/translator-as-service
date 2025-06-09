import asyncio
import csv
import hashlib
from typing import Dict, List

import torch

from application.initializer import cache_instance, logger_instance
from application.main.config import settings
from application.main.infrastructure.detector import Detector
from application.main.infrastructure.translator.translators import (
    TRANSLATOR_FACTORY,
    BaseTranslator,
)

logger = logger_instance.get_logger(__name__)
_cache = cache_instance
detector = Detector()


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
        self.languages = self.load_lang_dict_from_csv(
            str(settings.APP_CONFIG.RESOURCES_DIR / "languages.csv")
        )

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
        """Translates a list of texts from a source language to a target language.

        Automatically detects the source language if not provided, uses caching for efficiency, and formats the translated output to match the source text.

        Args:
            texts: List of text strings to translate.
            src_lang: Source language code. If empty, language detection is performed.
            tgt_lang: Target language code.

        Returns:
            List[str]: List of translated and formatted text strings.

        Raises:
            ValueError: If the translation direction is not supported or the translator is not loaded.
        """
        if not src_lang:
            detected_langs = detector.detect(texts, topk=3)
            logger.debug(
                f"src_lang not found, try to detect it: {detected_langs}",
            )
            src_lang = detected_langs[0]["language"]

        if tgt_lang not in self.SUPPORTED_LANGUAGES.get(src_lang, []):
            logger.error(
                f"Unsupported translation: {self.languages[src_lang]} ({src_lang}) ->  {self.languages[tgt_lang]}  ({tgt_lang})"
            )
            raise ValueError(
                f"Translation from {self.languages[src_lang]} ({src_lang}) ->  {self.languages[tgt_lang]} ({tgt_lang}) is not supported"
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

        return [
            self.improve_translation_formatting(
                text, cached_results[text], improve_punctuation=True
            )
            for text in texts
        ]

    def improve_translation_formatting(
        self,
        source,
        translation,
        improve_punctuation=True,
    ):
        """Improves the formatting of a translated string to better match the source string.

        Adjusts punctuation and capitalization of the translation to align with the source text, optionally improving punctuation consistency.

        Args:
            source: The original source string.
            translation: The translated string to be formatted.
            improve_punctuation: Whether to adjust punctuation to match the source (default: True).

        Returns:
            str: The formatted translation string.
        """
        source = source.strip()
        translation = translation.strip()

        if not source:
            return ""

        if not translation:
            return source

        if improve_punctuation:
            punctuation_chars = ["!", "?", ".", ",", ";", "。"]
            source_last_char = source.rstrip()[-1]
            translation_last_char = translation[-1]

            if source_last_char in punctuation_chars:
                if translation_last_char != source_last_char:
                    if translation_last_char in punctuation_chars:
                        translation = translation[:-1]
                    translation += source_last_char
            elif translation_last_char in punctuation_chars:
                translation = translation[:-1]

        if source.islower():
            return translation.lower()

        if source.isupper():
            return translation.upper()

        if source[0].islower():
            return translation[0].lower() + translation[1:]

        if source[0].isupper():
            return translation[0].upper() + translation[1:]

        return translation

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

    def load_lang_dict_from_csv(self, file_path: str) -> Dict[str, str]:
        lang_dict = {}
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue  # bỏ qua dòng không hợp lệ
                name, code = row[0].strip(), row[1].strip()
                lang_dict[code] = name
        return lang_dict
