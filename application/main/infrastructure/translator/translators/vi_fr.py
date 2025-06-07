from application.main.infrastructure.translator.translators.base import BaseTranslator


class ViFrTranslator(BaseTranslator):
    model_name = "Helsinki-NLP/opus-mt-vi-fr"
    model_type = "MarianMTModel"

    def __init__(self):
        super().__init__()
        self.load_model()

    def translate(self, texts):
        batch = self.tokenizer(
            texts,
            return_tensors=self._return_tensor,
            padding=self._padding,
            truncation=self._truncation,
            max_length=self._max_length,
        ).to(self._device)
        generated_ids = self.model.generate(
            **batch,
            max_length=self._max_length,
            num_beams=self._num_beams,
            early_stopping=self._stop_early,
        )
        return list(
            self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        )
