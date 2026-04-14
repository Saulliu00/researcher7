"""
Data provider abstraction — swap data-fetching backends via config.

Usage:
    from data_providers import create_data_provider

    dp = create_data_provider("google_trends")
    trends = dp.get_trending(country="united_states", limit=25)
"""
from .base import DataProvider
from .google_trends_provider import GoogleTrendsProvider

_PROVIDERS = {
    'google_trends': GoogleTrendsProvider,
}


def create_data_provider(name: str, **config) -> DataProvider:
    """
    Factory: instantiate a data provider by name.

    Args:
        name: Provider key ("google_trends", …)
        **config: Provider-specific keyword arguments

    Raises:
        ValueError: If the provider name is unknown.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        available = ', '.join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown data provider: '{name}'. Available: {available}"
        )
    return cls(**config)


def list_data_providers() -> list[str]:
    """Return sorted list of registered data provider names."""
    return sorted(_PROVIDERS.keys())
