"""
Semantic Scholar paper provider — queries the Semantic Scholar API.
"""
from typing import Dict, Optional

from .base import PaperProvider


class SemanticScholarProvider(PaperProvider):
    """Find papers via the Semantic Scholar API."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        from semanticscholar import SemanticScholar
        self.s2 = SemanticScholar(api_key=api_key, timeout=10, retry=False)

    @property
    def name(self) -> str:
        return "Semantic Scholar"

    def find_best_paper(self, topic: str,
                        max_results: int = 10) -> Optional[Dict]:
        print(f"Searching Semantic Scholar for: {topic}")
        try:
            results = self.s2.search_paper(topic, limit=max_results, fields=[
                'title', 'abstract', 'authors', 'year', 'citationCount',
                'url', 'openAccessPdf', 'publicationVenue',
            ])

            papers = []
            for paper in results:
                if paper.abstract and len(paper.abstract) > 100:
                    papers.append({
                        'title': paper.title,
                        'authors': [a.name for a in (paper.authors or [])],
                        'year': paper.year,
                        'abstract': paper.abstract,
                        'citations': paper.citationCount or 0,
                        'url': paper.url,
                        'pdf_url': getattr(paper.openAccessPdf, 'url', None)
                                   if paper.openAccessPdf else None,
                        'venue': getattr(paper.publicationVenue, 'name', None)
                                 if paper.publicationVenue else None,
                        'source': 'Semantic Scholar',
                    })

            if papers:
                papers.sort(key=lambda x: x['citations'], reverse=True)
                best = papers[0]
                print(f"✓ Found: {best['title']} ({best['citations']} citations)")
                return best

        except Exception as e:
            print(f"Semantic Scholar error: {e}")

        return None
