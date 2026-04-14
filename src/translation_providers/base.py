"""Abstract base class for all translation providers."""
from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    """
    Interface every translation provider must implement.

    Subclasses provide:
        name            – human-readable provider label
        translate(text) – returns the translated text
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    @abstractmethod
    def source_lang(self) -> str:
        """Source language code (e.g. 'en')."""
        ...

    @property
    @abstractmethod
    def target_lang(self) -> str:
        """Target language code (e.g. 'zh')."""
        ...

    @abstractmethod
    def translate(self, text: str) -> str:
        """Translate *text* from source_lang to target_lang."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.source_lang}→{self.target_lang})"
