"""
Google Trends scraper - retrieves top trending search terms
"""
from pytrends.request import TrendReq
from typing import List, Dict
import time
import random


class TrendScraper:
    def __init__(self):
        """Initialize the Google Trends scraper"""
        self.pytrends = TrendReq(hl='en-US', tz=360)
    
    def get_trending_searches(self, country: str = 'united_states', limit: int = 25) -> List[Dict]:
        """
        Get current trending searches
        
        Args:
            country: Country code (default: 'united_states')
            limit: Maximum number of trends to return (default: 25)
        
        Returns:
            List of dictionaries with trend data
        """
        try:
            # Get trending searches (real-time)
            trending_df = self.pytrends.trending_searches(pn=country)
            
            # Convert to list and limit
            trends = trending_df[0].tolist()[:limit]
            
            # Format as structured data
            trend_data = []
            for i, term in enumerate(trends):
                trend_data.append({
                    'rank': i + 1,
                    'term': term,
                    'country': country
                })
            
            return trend_data
            
        except Exception as e:
            print(f"Error fetching trends: {e}")
            # Return demo data if API fails
            return self._get_demo_trends(limit)
    
    def get_related_queries(self, keywords: List[str]) -> Dict:
        """
        Get related queries for specific keywords
        
        Args:
            keywords: List of search terms to analyze
        
        Returns:
            Dictionary of related queries
        """
        try:
            # Build payload
            self.pytrends.build_payload(keywords, timeframe='now 1-d')
            
            # Get related queries
            related = self.pytrends.related_queries()
            
            return related
            
        except Exception as e:
            print(f"Error fetching related queries: {e}")
            return {}
    
    def _get_demo_trends(self, limit: int = 25) -> List[Dict]:
        """
        Demo/fallback trends for testing when API is unavailable
        """
        demo_trends = [
            "artificial intelligence",
            "climate change",
            "quantum computing",
            "renewable energy",
            "space exploration",
            "cryptocurrency",
            "mental health",
            "pandemic recovery",
            "electric vehicles",
            "automation",
            "privacy concerns",
            "social media impact",
            "remote work",
            "sustainable fashion",
            "gene editing",
            "virtual reality",
            "cybersecurity threats",
            "income inequality",
            "ocean conservation",
            "urban farming",
            "ai ethics",
            "blockchain technology",
            "digital privacy",
            "carbon capture",
            "personalized medicine"
        ]
        
        return [
            {'rank': i + 1, 'term': trend, 'country': 'demo'}
            for i, trend in enumerate(demo_trends[:limit])
        ]


if __name__ == "__main__":
    # Test the scraper
    scraper = TrendScraper()
    trends = scraper.get_trending_searches(limit=10)
    
    print("Top 10 Trending Searches:")
    print("-" * 50)
    for trend in trends:
        print(f"{trend['rank']:2d}. {trend['term']}")
