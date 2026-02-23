"""
Paper Finder - searches for relevant academic papers
"""
from semanticscholar import SemanticScholar
import arxiv
from typing import List, Dict, Optional
import time


class PaperFinder:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize paper finder with academic search APIs
        
        Args:
            api_key: Optional Semantic Scholar API key (increases rate limits)
        """
        self.s2 = SemanticScholar(api_key=api_key)
        self.arxiv_client = arxiv.Client()
    
    def find_best_paper(self, topic: str, max_results: int = 10) -> Optional[Dict]:
        """
        Find the best academic paper related to a topic
        
        Args:
            topic: The unified topic/theme to search for
            max_results: Number of results to consider
        
        Returns:
            Dictionary with paper details or None
        """
        print(f"Searching for papers on: {topic}")
        
        # Try Semantic Scholar first (better citation data)
        paper = self._search_semantic_scholar(topic, max_results)
        
        if paper:
            return paper
        
        # Fallback to arXiv
        print("Trying arXiv...")
        paper = self._search_arxiv(topic, max_results)
        
        return paper
    
    def _search_semantic_scholar(self, query: str, limit: int) -> Optional[Dict]:
        """Search Semantic Scholar API"""
        try:
            results = self.s2.search_paper(query, limit=limit, fields=[
                'title', 'abstract', 'authors', 'year', 'citationCount',
                'url', 'openAccessPdf', 'publicationVenue'
            ])
            
            papers = []
            for paper in results:
                if paper.abstract and len(paper.abstract) > 100:  # Filter out short abstracts
                    papers.append({
                        'title': paper.title,
                        'authors': [a.name for a in (paper.authors or [])],
                        'year': paper.year,
                        'abstract': paper.abstract,
                        'citations': paper.citationCount or 0,
                        'url': paper.url,
                        'pdf_url': paper.openAccessPdf.get('url') if paper.openAccessPdf else None,
                        'venue': paper.publicationVenue.get('name') if paper.publicationVenue else None,
                        'source': 'Semantic Scholar'
                    })
            
            if papers:
                # Sort by citation count
                papers.sort(key=lambda x: x['citations'], reverse=True)
                best_paper = papers[0]
                
                print(f"✓ Found: {best_paper['title']} ({best_paper['citations']} citations)")
                return best_paper
            
        except Exception as e:
            print(f"Semantic Scholar error: {e}")
        
        return None
    
    def _search_arxiv(self, query: str, limit: int) -> Optional[Dict]:
        """Search arXiv API (fallback)"""
        try:
            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in self.arxiv_client.results(search):
                papers.append({
                    'title': result.title,
                    'authors': [a.name for a in result.authors],
                    'year': result.published.year,
                    'abstract': result.summary,
                    'citations': 0,  # arXiv doesn't provide citation counts
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'venue': 'arXiv Preprint',
                    'source': 'arXiv'
                })
            
            if papers:
                best_paper = papers[0]  # Most relevant
                print(f"✓ Found: {best_paper['title']} (arXiv)")
                return best_paper
            
        except Exception as e:
            print(f"arXiv error: {e}")
        
        return None
    
    def format_paper_summary(self, paper: Dict) -> str:
        """
        Format paper details for script generation
        
        Args:
            paper: Paper dictionary from find_best_paper()
        
        Returns:
            Formatted string with paper details
        """
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
        
        if paper['pdf_url']:
            summary += f"**PDF:** {paper['pdf_url']}\n"
        
        return summary.strip()


if __name__ == "__main__":
    # Test the paper finder
    finder = PaperFinder()
    
    test_topics = [
        "Artificial Intelligence and Climate Change",
        "Quantum Computing Applications"
    ]
    
    for topic in test_topics:
        print("\n" + "="*60)
        paper = finder.find_best_paper(topic, max_results=5)
        
        if paper:
            print(f"\nBest Paper: {paper['title']}")
            print(f"Citations: {paper['citations']}")
            print(f"Abstract preview: {paper['abstract'][:200]}...")
        else:
            print("No papers found")
