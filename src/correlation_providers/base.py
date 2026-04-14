"""Abstract base class for all correlation / clustering providers."""
from abc import ABC, abstractmethod
from typing import List, Dict


class CorrelationProvider(ABC):
    """
    Interface every correlation provider must implement.

    Subclasses provide:
        name                    – human-readable provider label
        analyze_trends(trends)  – returns correlation result dict
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def analyze_trends(self, trends: List[Dict],
                       min_cluster_size: int = 2) -> Dict:
        """
        Analyze trending terms and identify thematic clusters.

        Args:
            trends: List of trend dicts (must contain 'term' key).
            min_cluster_size: Minimum terms per cluster.

        Returns:
            Dictionary with at least:
                - clusters       (list of cluster dicts)
                - unified_topic  (dict with 'theme', 'confidence', …)
                - total_terms    (int)
                - num_clusters   (int)
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
