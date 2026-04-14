"""
Translation provider abstraction — swap translation backends via config.

Usage:
    from translation_providers import create_translation_provider

    t = create_translation_provider("marianmt")
    t = create_translation_provider("marianmt", source="en", target="zh")

    translated = t.translate("Hello world")
"""
from .base import TranslationProvider
from .marianmt_provider import MarianMTProvider

_PROVIDERS = {
    'marianmt': MarianMTProvider,
}


def create_translation_provider(name: str, **config) -> TranslationProvider:
    """
    Factory: instantiate a translation provider by name.

    Args:
        name: Provider key ("marianmt", …)
        **config: Provider-specific keyword arguments

    Raises:
        ValueError: If the provider name is unknown.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        available = ', '.join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown translation provider: '{name}'. Available: {available}"
        )
    return cls(**config)


def list_translation_providers() -> list[str]:
    """Return sorted list of registered translation provider names."""
    return sorted(_PROVIDERS.keys())
