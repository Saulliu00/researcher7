"""
arXiv paper provider — queries the arXiv API.
"""
from typing import Dict, Optional

from .base import PaperProvider


class ArxivProvider(PaperProvider):
    """Find papers via the arXiv API."""

    def __init__(self, **kwargs):
        import arxiv
        self._arxiv = arxiv
        self.client = arxiv.Client()

    @property
    def name(self) -> str:
        return "arXiv"

    def find_best_paper(self, topic: str,
                        max_results: int = 10) -> Optional[Dict]:
        print(f"Searching arXiv for: {topic}")
        try:
            search = self._arxiv.Search(
                query=topic,
                max_results=max_results,
                sort_by=self._arxiv.SortCriterion.Relevance,
            )

            papers = []
            for result in self.client.results(search):
                papers.append({
                    'title': result.title,
                    'authors': [a.name for a in result.authors],
                    'year': result.published.year,
                    'abstract': result.summary,
                    'citations': 0,  # arXiv doesn't provide citation counts
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'venue': 'arXiv Preprint',
                    'source': 'arXiv',
                })

            if papers:
                best = papers[0]
                print(f"✓ Found: {best['title']} (arXiv)")
                return best

        except Exception as e:
            print(f"arXiv error: {e}")

        return None
