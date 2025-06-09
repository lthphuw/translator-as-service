import abc

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from application.initializer import logger_instance
from application.main.config import settings

logger = logger_instance.get_logger(__name__)


class BaseDetector(abc.ABC):
    model_name = ""

    def __init__(self):
        super().__init__()

    def load_model(self):
        self.model_path = (
            settings.APP_CONFIG.MODELS_DIR
            / self.__class__.__name__.lower()
            / self.model_name.replace("/", "-")
        )

        # Ensure the local model directory exists
        self.model_path.mkdir(parents=True, exist_ok=True)

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )

        # Check if model exists locally
        model_exists = any(
            (self.model_path / file).exists()
            for file in ["config.json", "pytorch_model.bin", "model.safetensors"]
        )

        try:
            self._prepare_model(model_exists)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Language detector: {str(e)}"
            ) from e
        self.id2label = self.model.config.id2label

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
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name, torch_dtype=torch.float16
        )

        if not model_exists:
            logger.info(f"Saving model to {self.model_path}")
            self.model.save_pretrained(self.model_path, safe_serialization=False)
            self.tokenizer.save_pretrained(self.model_path)
            logger.info(f"Model saved to {self.model_path}")

        # Handle meta tensors
        if self.model.device.type == "meta":
            logger.info(f"Moving model from meta device to {self.device}")
            self.model.to_empty(device=self.device)
        else:
            self.model.to(self.device)
        logger.info(f"Model device: {self.model.device}")

        self.model.eval()

    @abc.abstractmethod
    def detect(self, texts: list[str], topk=3) -> list[dict]:
        raise NotImplementedError()
