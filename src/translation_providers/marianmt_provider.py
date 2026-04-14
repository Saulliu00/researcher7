"""MarianMT translation provider (Helsinki-NLP, offline)."""
import re
from .base import TranslationProvider


# Map of language pairs to HuggingFace model names
_MODEL_MAP = {
    ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
    ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
    ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
    ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
    ('en', 'ja'): 'Helsinki-NLP/opus-mt-en-jap',
    ('en', 'ko'): 'Helsinki-NLP/opus-mt-en-ko',
}


class MarianMTProvider(TranslationProvider):
    """Translate text using MarianMT (runs locally, no API key needed)."""

    def __init__(self, source: str = 'en', target: str = 'zh',
                 model_name: str = None):
        """
        Args:
            source: Source language code (default 'en')
            target: Target language code (default 'zh')
            model_name: Override the HuggingFace model name
        """
        self._source = source
        self._target = target

        pair = (source, target)
        self._model_name = model_name or _MODEL_MAP.get(pair)
        if self._model_name is None:
            available = ', '.join(f'{s}→{t}' for s, t in _MODEL_MAP)
            raise ValueError(
                f"No MarianMT model for {source}→{target}. "
                f"Available pairs: {available}. "
                f"Or pass model_name= explicitly."
            )

        # Lazy-loaded on first translate() call
        self._tokenizer = None
        self._model = None

    def _load_model(self):
        """Load model and tokenizer (heavy, done once)."""
        if self._model is not None:
            return
        from transformers import MarianMTModel, MarianTokenizer
        print(f"  Loading MarianMT model: {self._model_name} ...")
        self._tokenizer = MarianTokenizer.from_pretrained(self._model_name)
        self._model = MarianMTModel.from_pretrained(self._model_name)
        print(f"  ✓ MarianMT model loaded")

    @property
    def name(self) -> str:
        return "MarianMT"

    @property
    def source_lang(self) -> str:
        return self._source

    @property
    def target_lang(self) -> str:
        return self._target

    def translate(self, text: str) -> str:
        """
        Translate a full script.  Splits by paragraph to stay within
        MarianMT's 512-token window, then reassembles.
        """
        self._load_model()

        paragraphs = re.split(r'(\n{2,})', text)
        translated_parts: list[str] = []

        for part in paragraphs:
            # Preserve whitespace separators as-is
            if not part.strip():
                translated_parts.append(part)
                continue

            # Keep markdown structure markers untranslated
            if self._is_structural(part):
                translated_parts.append(part)
                continue

            translated_parts.append(self._translate_chunk(part))

        return ''.join(translated_parts)

    # ------------------------------------------------------------------

    def _translate_chunk(self, text: str) -> str:
        """Translate a single chunk (paragraph-sized)."""
        # MarianMT has a ~512-token limit; split long paragraphs into
        # sentences and translate individually if needed.
        sentences = re.split(r'(?<=[.!?])\s+', text)
        batch: list[str] = []
        results: list[str] = []

        for sent in sentences:
            batch.append(sent)
            # Flush when batch gets long
            if sum(len(s.split()) for s in batch) > 350:
                results.append(self._batch_translate(batch))
                batch = []

        if batch:
            results.append(self._batch_translate(batch))

        return ' '.join(results)

    def _batch_translate(self, sentences: list[str]) -> str:
        """Translate a batch of sentences in one forward pass."""
        inputs = self._tokenizer(
            sentences, return_tensors="pt",
            padding=True, truncation=True, max_length=512,
        )
        translated_ids = self._model.generate(**inputs)
        decoded = self._tokenizer.batch_decode(
            translated_ids, skip_special_tokens=True,
        )
        return ' '.join(decoded)

    @staticmethod
    def _is_structural(text: str) -> bool:
        """Return True for markdown lines that should not be translated."""
        stripped = text.strip()
        if stripped.startswith('---'):
            return True
        if stripped.startswith('**Generated:') or stripped.startswith('**Host:'):
            return True
        if stripped.startswith('**LLM Provider:') or stripped.startswith('**Model:'):
            return True
        if stripped.startswith('**Target Length:'):
            return True
        return False
