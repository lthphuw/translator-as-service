import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from application.main.infrastructure.translator.translators.base import BaseTranslator


class EnViTranslator(BaseTranslator):
    def __init__(self):
        self.model_name = "VietAI/envit5-translation"
        self.__device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(
            self.device()
        )

    def translate(self, texts):
        prefixed = [f"en: {text}" for text in texts]
        inputs = self.tokenizer(
            prefixed, return_tensors="pt", padding=True, truncation=True, max_length=512
        ).input_ids.to(self.__device)
        outputs = self.model.generate(inputs, max_length=512)
        return [
            it.replace("vi: ", "")
            for it in self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        ]

    def device(self) -> str:
        return str(self.__device)
        return str(self.__device)
