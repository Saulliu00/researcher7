"""
Paper provider abstraction — swap academic-search backends via config.

Usage:
    from paper_providers import create_paper_provider

    finder = create_paper_provider("semantic_scholar")
    paper  = finder.find_best_paper("AI and climate change")
"""
from .base import PaperProvider
from .semantic_scholar_provider import SemanticScholarProvider
from .arxiv_provider import ArxivProvider

_PROVIDERS = {
    'semantic_scholar': SemanticScholarProvider,
    'arxiv': ArxivProvider,
}


def create_paper_provider(name: str, **config) -> PaperProvider:
    """
    Factory: instantiate a paper provider by name.

    Args:
        name: Provider key ("semantic_scholar", "arxiv", …)
        **config: Provider-specific keyword arguments

    Raises:
        ValueError: If the provider name is unknown.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        available = ', '.join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown paper provider: '{name}'. Available: {available}"
        )
    return cls(**config)


def list_paper_providers() -> list[str]:
    """Return sorted list of registered paper provider names."""
    return sorted(_PROVIDERS.keys())
