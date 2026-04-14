"""Abstract base class for all paper-finding providers."""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class PaperProvider(ABC):
    """
    Interface every paper-finding provider must implement.

    Subclasses provide:
        name                        – human-readable provider label
        find_best_paper(topic, …)   – returns a paper dict or None
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def find_best_paper(self, topic: str,
                        max_results: int = 10) -> Optional[Dict]:
        """
        Find the best academic paper related to *topic*.

        Returns:
            Dictionary with at least:
                title, authors, year, abstract, citations,
                url, pdf_url, venue, source
            or None if nothing was found.
        """
        ...

    def format_paper_summary(self, paper: Dict) -> str:
        """Format paper details for script generation."""
        authors_str = ', '.join(paper['authors'][:3])
        if len(paper['authors']) > 3:
            authors_str += f" et al. ({len(paper['authors'])} authors)"

        summary = f"""
**Paper Title:** {paper['title']}
**Authors:** {authors_str}
**Year:** {paper['year']}
**Citations:** {paper['citations']:,}
**Venue:** {paper['venue'] or 'N/A'}
**Source:** {paper['source']}

**Abstract:**
{paper['abstract']}

**URL:** {paper['url']}
"""
        if paper.get('pdf_url'):
            summary += f"**PDF:** {paper['pdf_url']}\n"

        return summary.strip()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
