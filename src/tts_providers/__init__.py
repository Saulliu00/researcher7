"""
TTS provider abstraction — swap text-to-speech backends via config.

Usage:
    from tts_providers import create_tts_provider

    tts = create_tts_provider("piper", voice_model="/path/to/model.onnx")

    tts.synthesize("Hello world", "output.wav")
"""
from .base import TTSProvider
from .piper_provider import PiperProvider

_PROVIDERS = {
    'piper': PiperProvider,
}


def create_tts_provider(name: str, **config) -> TTSProvider:
    """
    Factory: instantiate a TTS provider by name.

    Args:
        name: Provider key ("piper", …)
        **config: Provider-specific keyword arguments

    Raises:
        ValueError: If the provider name is unknown.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        available = ', '.join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown TTS provider: '{name}'. Available: {available}"
        )
    return cls(**config)


def list_tts_providers() -> list[str]:
    """Return sorted list of registered TTS provider names."""
    return sorted(_PROVIDERS.keys())
