"""Abstract base class for all TTS providers."""
from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """
    Interface every TTS provider must implement.

    Subclasses provide:
        name                – human-readable provider label
        synthesize(text, output_path) – write audio to output_path
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> str:
        """
        Convert *text* to speech and write audio to *output_path*.

        Returns:
            The path to the written audio file.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
