"""
LLM Provider abstraction — makes it easy to swap between APIs.

Usage:
    from llm_providers import create_provider

    provider = create_provider("ollama", model="qwen3:8b")
    provider = create_provider("anthropic", api_key="sk-...", model="claude-sonnet-4-5")

    text = provider.generate("Write a poem about AI")
"""
from .base import LLMProvider
from .ollama_provider import OllamaProvider
from .anthropic_provider import AnthropicProvider

_PROVIDERS = {
    'ollama': OllamaProvider,
    'anthropic': AnthropicProvider,
}


def create_provider(name: str, **config) -> LLMProvider:
    """
    Factory: instantiate an LLM provider by name.

    Args:
        name: Provider key ("ollama", "anthropic", …)
        **config: Provider-specific keyword arguments

    Raises:
        ValueError: If the provider name is unknown.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        available = ', '.join(sorted(_PROVIDERS.keys()))
        raise ValueError(f"Unknown LLM provider: '{name}'. Available: {available}")
    return cls(**config)


def list_providers() -> list[str]:
    """Return sorted list of registered provider names."""
    return sorted(_PROVIDERS.keys())
