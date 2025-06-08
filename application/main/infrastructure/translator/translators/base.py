from abc import ABC, abstractmethod
from typing import List

import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    MarianMTModel,
    MarianTokenizer,
)

from application.initializer import logger_instance
from application.main.config import settings

logger = logger_instance.get_logger(__name__)


class BaseTranslator(ABC):
    """Abstract base class for translation models with extensible model type support."""

    # Model type registry: maps model_type to (model_class, tokenizer_class)
    _MODEL_FACTORY = {
        "AutoModelForSeq2SeqLM": (AutoModelForSeq2SeqLM, AutoTokenizer),
        "MarianMTModel": (MarianMTModel, MarianTokenizer),
    }

    model_name: str = ""
    model_type: str = "" 

    _device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    
    # Use float16 on mps can cause meta tensor error
    _torch_dtype = torch.float16 if _device.type == "cuda" else torch.float32
    _return_tensor = "pt"
    _padding = True
    _truncation = True
    _max_length = 512 
    _num_beams = 4  
    _stop_early = True

    def __init__(self):
        """Initialize the translator, validating model configuration."""
        if not self.model_name:
            raise ValueError(f"model_name must be defined in {self.__class__.__name__}")
        if self.model_type not in self._MODEL_FACTORY:
            raise ValueError(
                f"Invalid model_type: {self.model_type}. Supported types: {list(self._MODEL_FACTORY.keys())}"
            )

    def device(self) -> str:
        """Returns the device on which the model is loaded.

        Returns:
            str: Device name (e.g., 'cuda', 'mps', 'cpu').
        """
        return str(self._device)

    def load_model(self) -> None:
        """Loads the model and tokenizer, with local caching and meta tensor handling."""
        self.model_path = (
            settings.APP_CONFIG.MODELS_DIR
            / self.__class__.__name__.lower()
            / self.model_name.replace("/", "-")
        )
        self.model_path.mkdir(parents=True, exist_ok=True)

        model_exists = any(
            (self.model_path / file).exists()
            for file in ["config.json", "pytorch_model.bin", "model.safetensors"]
        )

        try:
            self._prepare_model(model_exists)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize {self.__class__.__name__}: {str(e)}"
            ) from e

    def _prepare_model(self, model_exists: bool) -> None:
        """Prepares the model and tokenizer for inference."""
        model_class, tokenizer_class = self._MODEL_FACTORY[self.model_type]

        logger.info(
            f"Loading tokenizer from {'local path' if model_exists else 'Hugging Face Hub'}: "
            f"{self.model_path if model_exists else self.model_name}"
        )
        self.tokenizer = tokenizer_class.from_pretrained(
            self.model_path if model_exists else self.model_name
        )

        logger.info(
            f"Loading model from {'local path' if model_exists else 'Hugging Face Hub'}: "
            f"{self.model_path if model_exists else self.model_name}"
        )

        try:
            self.model = model_class.from_pretrained(
                self.model_path if model_exists else self.model_name,
                torch_dtype=self._torch_dtype,
                device_map=None,
                low_cpu_mem_usage=False,
            )
            self.model.to(self._device)
            
        except RuntimeError as e:
            if "meta tensor" in str(e).lower():
                self._handle_meta_tensor(model_class, model_exists)
            else:
                raise e

        if not model_exists:
            logger.info(f"Saving model to {self.model_path}")
            self.model.save_pretrained(self.model_path, safe_serialization=False)
            self.tokenizer.save_pretrained(self.model_path)
            logger.info(f"Model saved to {self.model_path}")

        logger.info(f"Model device: {self.model.device}")
        self.model.eval()

    def _handle_meta_tensor(self, model_class, model_exists):
        logger.warning("Meta tensor error, reloading using to_empty + load_state_dict fallback")

        model_temp = model_class.from_pretrained(
            self.model_path if model_exists else self.model_name,
            device_map="cpu",
            torch_dtype=self._torch_dtype,
            low_cpu_mem_usage=False
        )
        model_temp.to_empty(device=self._device)
        state_dict = model_temp.state_dict()
        self.model = model_class(self.model.config)
        self.model.to(self._device)
        self.model.load_state_dict(state_dict)

    @abstractmethod
    def translate(self, texts: List[str]) -> List[str]:
        """Translates a list of texts to the target language.

        Args:
            texts: List of input texts to translate.

        Returns:
            List of translated texts.
        """
        raise NotImplementedError
