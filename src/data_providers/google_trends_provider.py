"""
Google Trends data provider — retrieves top trending search terms
via the Google Trends RSS feed.
"""
import xml.etree.ElementTree as ET
from typing import List, Dict

import requests

from .base import DataProvider

# Google Trends RSS namespace
_HT_NS = "https://trends.google.com/trending/rss"

# Country name → ISO-3166-1 alpha-2 code used by the RSS feed
_COUNTRY_CODES = {
    "united_states": "US",
    "united_kingdom": "GB",
    "canada": "CA",
    "australia": "AU",
    "india": "IN",
    "germany": "DE",
    "france": "FR",
    "japan": "JP",
    "brazil": "BR",
    "mexico": "MX",
}


class GoogleTrendsProvider(DataProvider):
    """Fetch trending searches from the Google Trends RSS feed."""

    def __init__(self, **kwargs):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"
        })

    @property
    def name(self) -> str:
        return "Google Trends RSS"

    def get_trending(self, country: str = 'united_states',
                     limit: int = 25) -> List[Dict]:
        geo = _COUNTRY_CODES.get(country.lower(), country.upper())
        url = f"https://trends.google.com/trending/rss?geo={geo}"

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            items = channel.findall("item") if channel is not None else []

            trend_data: List[Dict] = []
            for i, item in enumerate(items):
                if i >= limit:
                    break

                title = item.findtext("title", "").strip()
                traffic = item.findtext(f"{{{_HT_NS}}}approx_traffic", "").strip()
                pub_date = item.findtext("pubDate", "").strip()

                news_items = []
                for ni in item.findall(f"{{{_HT_NS}}}news_item"):
                    headline = ni.findtext(f"{{{_HT_NS}}}news_item_title", "").strip()
                    source = ni.findtext(f"{{{_HT_NS}}}news_item_source", "").strip()
                    news_url = ni.findtext(f"{{{_HT_NS}}}news_item_url", "").strip()
                    if headline:
                        news_items.append({
                            "headline": headline,
                            "source": source,
                            "url": news_url,
                        })

                trend_data.append({
                    "rank": i + 1,
                    "term": title,
                    "country": geo,
                    "approx_traffic": traffic,
                    "pub_date": pub_date,
                    "news": news_items,
                })

            if trend_data:
                print(f"✓ Fetched {len(trend_data)} real trends from Google Trends RSS (geo={geo})")
                return trend_data

            print("⚠ RSS feed returned no items – falling back to demo data")
            return self._get_demo_trends(limit)

        except Exception as e:
            print(f"Error fetching trends from RSS: {e}")
            return self._get_demo_trends(limit)

    @staticmethod
    def _get_demo_trends(limit: int = 25) -> List[Dict]:
        demo_trends = [
            "artificial intelligence", "climate change", "quantum computing",
            "renewable energy", "space exploration", "cryptocurrency",
            "mental health", "pandemic recovery", "electric vehicles",
            "automation", "privacy concerns", "social media impact",
            "remote work", "sustainable fashion", "gene editing",
            "virtual reality", "cybersecurity threats", "income inequality",
            "ocean conservation", "urban farming", "ai ethics",
            "blockchain technology", "digital privacy", "carbon capture",
            "personalized medicine",
        ]
        return [
            {'rank': i + 1, 'term': trend, 'country': 'demo'}
            for i, trend in enumerate(demo_trends[:limit])
        ]
