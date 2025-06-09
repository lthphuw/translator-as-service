import torch
import torch.nn.functional as F

from application.main.infrastructure.detector.base import BaseDetector


class Detector(BaseDetector):
    """

    Supports the following 20 languages:
    arabic (ar), bulgarian (bg), german (de), modern greek (el), english (en), spanish (es), french (fr), hindi (hi), italian (it), japanese (ja), dutch (nl), polish (pl), portuguese (pt), russian (ru), swahili (sw), thai (th), turkish (tr), urdu (ur), vietnamese (vi), and chinese (zh)

    """

    def __init__(self):
        self.model_name = "papluca/xlm-roberta-base-language-detection"
        self.load_model()

    def detect(self, texts: list[str], topk=3) -> list[dict]:
        """Detects the most probable languages present in a list of text strings.

        Merges the input texts, runs language detection, and returns the top three detected languages with confidence scores.

        Args:
            texts (list[str]): List of text strings to analyze.

        Returns:
            list[dict]: List of dictionaries containing language labels and confidence scores for the top three detected languages.
        """
        # Merge into a paragraph
        merged_text = " ".join(texts)

        # Tokenize the paragraph
        inputs = self.tokenizer(
            merged_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(self.device)

        # Inference
        with torch.no_grad():
            logits = self.model(**inputs).logits  # shape: [1, num_classes]

        # Do the softmax (for probability)
        probs = F.softmax(logits, dim=-1)[0]  # shape: [num_classes]

        # Get the top 3
        topk = torch.topk(probs, k=topk)

        top_languages = []
        top_languages.extend(
            {"language": self.id2label[idx], "confidence": score}
            for idx, score in zip(topk.indices.tolist(), topk.values.tolist())
        )

        return top_languages
