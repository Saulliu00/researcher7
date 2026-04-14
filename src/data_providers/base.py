"""Abstract base class for all data-fetching providers."""
from abc import ABC, abstractmethod
from typing import List, Dict


class DataProvider(ABC):
    """
    Interface every data-fetching provider must implement.

    Subclasses provide:
        name                            – human-readable provider label
        get_trending(country, limit)    – returns a list of trend dicts
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def get_trending(self, country: str = 'united_states',
                     limit: int = 25) -> List[Dict]:
        """
        Fetch trending / popular topics from the data source.

        Each dict in the returned list MUST contain at least:
            - rank  (int)
            - term  (str)

        Additional keys (country, approx_traffic, news, …) are optional
        and provider-specific.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
