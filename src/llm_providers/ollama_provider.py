"""Ollama (local LLM) provider."""
import requests
from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """Generate text via a local Ollama server."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434",
                 model: str = "qwen3:8b"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return "Ollama"

    @property
    def model(self) -> str:
        return self._model

    @property
    def supports_long_context(self) -> bool:
        return False  # local models benefit from shorter, multi-pass prompts

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": 300,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000,
                    },
                },
                timeout=600,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"   ✗ Ollama error: {e}")
            raise
