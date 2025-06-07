from abc import ABC, abstractmethod
from typing import List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from application.initializer import logger_instance
from application.main.config import settings

logger = logger_instance.get_logger(__name__)


class BaseTranslator(ABC):
    model_name = ""
    _device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    _return_tensor = "pt"
    _padding = True
    _truncation = True
    _max_length = 512
    _num_beams = 5
    _stop_early = True
    _torch_dtype = torch.float16

    def device(self) -> str:
        """Returns the device on which the model is loaded.

        Returns the string representation of the current computation device.

        Returns:
            str: The name of the device (e.g., 'cuda', 'mps', or 'cpu').
        """
        return str(self._device)

    def load_model(self):
        self.model_path = (
            settings.APP_CONFIG.MODELS_DIR
            / self.__class__.__name__.lower()
            / self.model_name.replace("/", "-")
        )
        self._device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )

        # Ensure the local model directory exists
        self.model_path.mkdir(parents=True, exist_ok=True)

        # Check if model exists locally
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

    def _prepare_model(self, model_exists):
        logger.info(
            f"Loading tokenizer from {'local path' if model_exists else 'Hugging Face Hub'}: {self.model_path if model_exists else self.model_name}"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path if model_exists else self.model_name
        )

        logger.info(
            f"Loading model from {'local path' if model_exists else 'Hugging Face Hub'}: {self.model_path if model_exists else self.model_name}"
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_path if model_exists else self.model_name,
            torch_dtype=torch.float32,
            device_map=None,
        )

        if not model_exists:
            logger.info(f"Saving model to {self.model_path}")
            self.model.save_pretrained(self.model_path, safe_serialization=False)
            self.tokenizer.save_pretrained(self.model_path)
            logger.info(f"Model saved to {self.model_path}")

        # Move model to target device
        try:
            self.model.to(self._device)
            logger.info(f"Model device: {self.model.device}")
        except RuntimeError as e:
            if "meta tensor" not in str(e).lower():
                raise e
            logger.warning(
                f"Meta tensor detected, attempting to move to {self._device}"
            )
            # Try loading on CPU first if meta tensor issue persists
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_path if model_exists else self.model_name,
                torch_dtype=self._torch_dtype,
            )
            # Handle meta tensors
            if self.model.device.type == "meta":
                logger.info(f"Moving model from meta device to {self._device}")
                self.model.to_empty(device=self._device)
            else:
                self.model.to(self.device)
            logger.info(f"Model device after CPU fallback: {self.model.device}")

        self.model.eval()

    @abstractmethod
    def translate(self, texts: List[str]) -> List[str]:
        raise NotImplementedError
