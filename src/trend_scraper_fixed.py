"""
Google Trends scraper - retrieves top trending search terms
Fixed version using web scraping when API fails
"""
from pytrends.request import TrendReq
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import re


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
        # Try API first
        try:
            trending_df = self.pytrends.trending_searches(pn=country)
            trends = trending_df[0].tolist()[:limit]
            
            trend_data = []
            for i, term in enumerate(trends):
                trend_data.append({
                    'rank': i + 1,
                    'term': term,
                    'country': country
                })
            
            return trend_data
            
        except Exception as e:
            print(f"⚠️  Google Trends API failed: {e}")
            print("   Trying web scraping fallback...")
            
            # Try web scraping
            try:
                return self._scrape_trending_from_web(limit)
            except Exception as scrape_error:
                print(f"⚠️  Web scraping also failed: {scrape_error}")
                print("   Using demo data as final fallback")
                return self._get_demo_trends(limit)
    
    def _scrape_trending_from_web(self, limit: int = 25) -> List[Dict]:
        """
        Scrape trending topics directly from Google Trends website
        """
        url = "https://trends.google.com/trending?geo=US"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find trending searches (Google Trends uses specific CSS classes)
        # This may need adjustment as Google changes their HTML structure
        trends = []
        
        # Try to find trend items
        trend_items = soup.find_all('div', class_=re.compile(r'mZ3RIc'))
        
        if not trend_items:
            raise Exception("Could not find trend items in HTML")
        
        for i, item in enumerate(trend_items[:limit]):
            text = item.get_text(strip=True)
            if text:
                trends.append({
                    'rank': i + 1,
                    'term': text.lower(),
                    'country': 'US (web-scraped)'
                })
        
        print(f"✓ Successfully scraped {len(trends)} real trending topics!")
        return trends
    
    def get_related_queries(self, keywords: List[str]) -> Dict:
        """
        Get related queries for specific keywords
        
        Args:
            keywords: List of search terms to analyze
        
        Returns:
            Dictionary of related queries
        """
        try:
            self.pytrends.build_payload(keywords, timeframe='now 1-d')
            related = self.pytrends.related_queries()
            return related
            
        except Exception as e:
            print(f"Error fetching related queries: {e}")
            return {}
    
    def _get_demo_trends(self, limit: int = 25) -> List[Dict]:
        """
        Demo/fallback trends for testing when API AND scraping fail
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
            {'rank': i + 1, 'term': trend, 'country': 'demo (fallback)'}
            for i, trend in enumerate(demo_trends[:limit])
        ]


if __name__ == "__main__":
    # Test the scraper
    scraper = TrendScraper()
    trends = scraper.get_trending_searches(limit=15)
    
    print("\nTop 15 Trending Searches:")
    print("-" * 60)
    for trend in trends:
        print(f"{trend['rank']:2d}. {trend['term']:40s} ({trend['country']})")
