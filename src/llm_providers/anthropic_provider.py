"""Anthropic Claude provider."""
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Generate text via the Anthropic Claude API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        if not api_key:
            raise ValueError("Anthropic API key is required")
        # Lazy import — only pull in the SDK when actually needed
        from anthropic import Anthropic
        self._client = Anthropic(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return "Anthropic"

    @property
    def model(self) -> str:
        return self._model

    @property
    def supports_long_context(self) -> bool:
        return True  # Claude handles long contexts well → single-pass

    def generate(self, prompt: str) -> str:
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=8000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            print(f"   ✗ Anthropic error: {e}")
            raise
