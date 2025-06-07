from application.main.infrastructure.translator.translators.base import BaseTranslator


class ViEnTranslator(BaseTranslator):
    def __init__(self):
        super().__init__()
        self.model_name = "VietAI/envit5-translation"
        self.load_model()

    def translate(self, texts):
        prefixed = [f"vi: {text}" for text in texts]
        inputs = self.tokenizer(
            prefixed,
            return_tensors=self._return_tensor,
            padding=self._padding,
            truncation=self._truncation,
            max_length=self._max_length,
        ).to(self._device)
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=self._max_length,
            num_beams=self._num_beams,
            early_stopping=self._stop_early,
        )
        return [
            it.replace("en: ", "")
            for it in self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        ]
