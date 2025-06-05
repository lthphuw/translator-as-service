import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer



class LanguageDetector:
    def __init__(self):
        self.model_name = "papluca/xlm-roberta-base-language-detection"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )

        self.model.to(self.device)
        self.model.eval()
        self.id2label = self.model.config.id2label

    def detect(self, text: str) -> str:
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

        with torch.no_grad():
            logits = self.model(**inputs).logits

        predicted_id = logits.argmax().item()
        return self.id2label[predicted_id]
