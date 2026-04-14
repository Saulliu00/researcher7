"""Abstract base class for all LLM providers."""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Interface every LLM provider must implement.

    Subclasses provide:
        name              – human-readable provider label (e.g. "Ollama")
        model             – model identifier (e.g. "qwen3:8b")
        supports_long_context – whether single-pass generation is preferred
        generate(prompt)  – returns the generated text
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier string."""
        ...

    @property
    def supports_long_context(self) -> bool:
        """Return True if the provider handles long prompts well (→ single-pass).
        Local models typically return False (→ multi-pass)."""
        return False

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the generated text."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"
