"""
Multi-Source Trend Scraper
Combines trending topics from X/Twitter, News API, and Reddit
"""
import os
from typing import List, Dict
import tweepy
from newsapi import NewsApiClient
import praw
from datetime import datetime, timedelta


class MultiSourceTrendScraper:
    def __init__(self, 
                 twitter_bearer_token: str = None,
                 news_api_key: str = None,
                 reddit_client_id: str = None,
                 reddit_client_secret: str = None):
        """
        Initialize the multi-source trend scraper
        
        Args:
            twitter_bearer_token: Twitter API v2 bearer token
            news_api_key: News API key
            reddit_client_id: Reddit API client ID
            reddit_client_secret: Reddit API client secret
        """
        self.twitter_token = twitter_bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        self.news_key = news_api_key or os.getenv('NEWS_API_KEY')
        self.reddit_id = reddit_client_id or os.getenv('REDDIT_CLIENT_ID')
        self.reddit_secret = reddit_client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        
        # Initialize clients
        self.twitter_client = None
        self.news_client = None
        self.reddit_client = None
        
        if self.twitter_token:
            try:
                self.twitter_client = tweepy.Client(bearer_token=self.twitter_token)
                print("✓ Twitter API initialized")
            except Exception as e:
                print(f"⚠️  Twitter API failed: {e}")
        
        if self.news_key:
            try:
                self.news_client = NewsApiClient(api_key=self.news_key)
                print("✓ News API initialized")
            except Exception as e:
                print(f"⚠️  News API failed: {e}")
        
        if self.reddit_id and self.reddit_secret:
            try:
                self.reddit_client = praw.Reddit(
                    client_id=self.reddit_id,
                    client_secret=self.reddit_secret,
                    user_agent='researcher7:v1.0 (by /u/researcher7bot)'
                )
                print("✓ Reddit API initialized")
            except Exception as e:
                print(f"⚠️  Reddit API failed: {e}")
    
    def get_trending_searches(self, limit: int = 25) -> List[Dict]:
        """
        Get trending topics from all sources
        
        Args:
            limit: Target total number of trends (divided among sources)
        
        Returns:
            Combined list of trending topics from all sources
        """
        all_trends = []
        
        # Get 5 from each source (15 total by default)
        per_source = 5
        
        # X/Twitter trends
        twitter_trends = self._get_twitter_trends(per_source)
        all_trends.extend(twitter_trends)
        
        # News API trends
        news_trends = self._get_news_trends(per_source)
        all_trends.extend(news_trends)
        
        # Reddit trends
        reddit_trends = self._get_reddit_trends(per_source)
        all_trends.extend(reddit_trends)
        
        # If we didn't get enough, use demo data to fill
        if len(all_trends) < limit:
            demo_trends = self._get_demo_trends(limit - len(all_trends))
            all_trends.extend(demo_trends)
        
        # Re-rank everything
        for i, trend in enumerate(all_trends[:limit]):
            trend['rank'] = i + 1
        
        return all_trends[:limit]
    
    def _get_twitter_trends(self, limit: int = 5) -> List[Dict]:
        """Get trending topics from X/Twitter"""
        if not self.twitter_client:
            print("⚠️  Twitter API not configured, skipping")
            return []
        
        try:
            # Get trending topics for US (WOEID: 23424977)
            # Note: Twitter API v2 doesn't have direct trends endpoint
            # We'll search for trending hashtags instead
            
            # Search for tweets with high engagement in last 24h
            query = "-is:retweet lang:en"
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=['public_metrics', 'created_at']
            )
            
            if not tweets.data:
                print("⚠️  No Twitter data returned")
                return []
            
            # Extract hashtags and topics
            topics = {}
            for tweet in tweets.data:
                text = tweet.text.lower()
                # Simple topic extraction (split on spaces, filter common words)
                words = [w.strip('#.,!?') for w in text.split() 
                        if len(w) > 3 and w.startswith('#')]
                for word in words[:3]:  # Max 3 hashtags per tweet
                    topics[word] = topics.get(word, 0) + 1
            
            # Sort by frequency
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
            
            trends = []
            for i, (topic, count) in enumerate(sorted_topics[:limit]):
                trends.append({
                    'rank': i + 1,
                    'term': topic.replace('#', ''),
                    'source': 'X/Twitter',
                    'count': count
                })
            
            print(f"✓ Got {len(trends)} trends from Twitter")
            return trends
            
        except Exception as e:
            print(f"⚠️  Twitter trends failed: {e}")
            return []
    
    def _get_news_trends(self, limit: int = 5) -> List[Dict]:
        """Get trending topics from News API"""
        if not self.news_client:
            print("⚠️  News API not configured, skipping")
            return []
        
        try:
            # Get top headlines from US
            top_headlines = self.news_client.get_top_headlines(
                country='us',
                page_size=20
            )
            
            if not top_headlines or not top_headlines.get('articles'):
                print("⚠️  No news headlines returned")
                return []
            
            # Extract topics from headlines
            topics = {}
            for article in top_headlines['articles']:
                title = article.get('title', '').lower()
                # Simple keyword extraction
                words = [w.strip('.,!?') for w in title.split() 
                        if len(w) > 4 and w not in ['about', 'after', 'where', 'which']]
                for word in words[:3]:
                    topics[word] = topics.get(word, 0) + 1
            
            # Sort by frequency
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
            
            trends = []
            for i, (topic, count) in enumerate(sorted_topics[:limit]):
                trends.append({
                    'rank': i + 1,
                    'term': topic,
                    'source': 'News API',
                    'count': count
                })
            
            print(f"✓ Got {len(trends)} trends from News API")
            return trends
            
        except Exception as e:
            print(f"⚠️  News API trends failed: {e}")
            return []
    
    def _get_reddit_trends(self, limit: int = 5) -> List[Dict]:
        """Get trending topics from Reddit (last 48 hours)"""
        if not self.reddit_client:
            print("⚠️  Reddit API not configured, skipping")
            return []
        
        try:
            # Get hot posts from /r/all from last 48h
            subreddit = self.reddit_client.subreddit('all')
            hot_posts = subreddit.hot(limit=100)
            
            # Filter posts from last 48 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=48)
            
            topics = {}
            for post in hot_posts:
                post_time = datetime.utcfromtimestamp(post.created_utc)
                
                if post_time >= cutoff_time:
                    # Extract keywords from title
                    title = post.title.lower()
                    words = [w.strip('.,!?[]()') for w in title.split() 
                            if len(w) > 4 and w not in ['about', 'after', 'where', 'which', 'their']]
                    for word in words[:3]:
                        topics[word] = topics.get(word, 0) + 1
            
            # Sort by frequency
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
            
            trends = []
            for i, (topic, count) in enumerate(sorted_topics[:limit]):
                trends.append({
                    'rank': i + 1,
                    'term': topic,
                    'source': 'Reddit',
                    'count': count
                })
            
            print(f"✓ Got {len(trends)} trends from Reddit")
            return trends
            
        except Exception as e:
            print(f"⚠️  Reddit trends failed: {e}")
            return []
    
    def _get_demo_trends(self, limit: int = 25) -> List[Dict]:
        """Fallback demo trends"""
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
            "automation"
        ]
        
        return [
            {'rank': i + 1, 'term': trend, 'source': 'demo (fallback)', 'count': 0}
            for i, trend in enumerate(demo_trends[:limit])
        ]


if __name__ == "__main__":
    # Test the scraper
    scraper = MultiSourceTrendScraper()
    trends = scraper.get_trending_searches(limit=15)
    
    print("\n" + "="*70)
    print("COMBINED TRENDING TOPICS (Top 15)")
    print("="*70)
    for trend in trends:
        source = trend.get('source', 'unknown')
        count = trend.get('count', 0)
        print(f"{trend['rank']:2d}. {trend['term']:30s} [{source:15s}] ({count} mentions)")
