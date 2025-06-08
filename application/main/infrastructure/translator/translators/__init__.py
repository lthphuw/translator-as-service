from typing import Callable, Dict

from application.main.infrastructure.translator.translators.base import BaseTranslator
from application.main.infrastructure.translator.translators.en_fr import EnFrTranslator
from application.main.infrastructure.translator.translators.en_vi import EnViTranslator
from application.main.infrastructure.translator.translators.fr_en import FrEnTranslator
from application.main.infrastructure.translator.translators.fr_vi import FrViTranslator
from application.main.infrastructure.translator.translators.vi_en import ViEnTranslator
from application.main.infrastructure.translator.translators.vi_fr import ViFrTranslator

TRANSLATOR_FACTORY: Dict[str, Callable[[], BaseTranslator]] = {
    "vi2fr": ViFrTranslator,
    "vi2en": ViEnTranslator,
    "en2fr": EnFrTranslator,
    "en2vi": EnViTranslator,
    "fr2en": FrEnTranslator,
    "fr2vi": FrViTranslator,
}
