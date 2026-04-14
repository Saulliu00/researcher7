"""
Correlation provider abstraction — swap clustering backends via config.

Usage:
    from correlation_providers import create_correlation_provider

    engine = create_correlation_provider("sklearn")
    result = engine.analyze_trends(trends)
"""
from .base import CorrelationProvider
from .sklearn_provider import SklearnCorrelationProvider

_PROVIDERS = {
    'sklearn': SklearnCorrelationProvider,
}


def create_correlation_provider(name: str, **config) -> CorrelationProvider:
    """
    Factory: instantiate a correlation provider by name.

    Args:
        name: Provider key ("sklearn", …)
        **config: Provider-specific keyword arguments

    Raises:
        ValueError: If the provider name is unknown.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        available = ', '.join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown correlation provider: '{name}'. Available: {available}"
        )
    return cls(**config)


def list_correlation_providers() -> list[str]:
    """Return sorted list of registered correlation provider names."""
    return sorted(_PROVIDERS.keys())
