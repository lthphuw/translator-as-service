import torch

from application.main.infrastructure.lang_detector.base import BaseLanguageDetector


class LanguageDetector(BaseLanguageDetector):
    def __init__(self):
        self.model_name = "papluca/xlm-roberta-base-language-detection"
        self.load_model()

    def detect(self, text: str) -> str:
        # Tokenize the single text
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=512
        ).to(self.device)

        # Run inference
        with torch.no_grad():
            logits = self.model(**inputs).logits

        # Get predicted label ID
        predicted_id = logits.argmax(dim=-1).item()

        return self.id2label[predicted_id]
