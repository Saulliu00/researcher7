# Google Trends API Issue

**Status:** ❌ Broken  
**Date:** 2026-02-26  
**Impact:** All pipeline runs use identical demo/fallback data

## Problem

The Google Trends API (via `pytrends` library) is returning 404 errors on all endpoints:
- `trending_searches()` - **404 error**
- `realtime_trending_searches()` - **404 error** 
- Web scraping fallback - **Failed** (HTML structure too complex)

**Result:** The pipeline falls back to hardcoded demo data, so every run has identical trending topics regardless of what's actually trending.

## Evidence

```bash
$ python -c "from src.trend_scraper import TrendScraper; scraper = TrendScraper(); trends = scraper.get_trending_searches(limit=5); print(trends)"

Error fetching trends: The request failed: Google returned a response with code 404
[
  {'rank': 1, 'term': 'artificial intelligence', 'country': 'demo'},
  {'rank': 2, 'term': 'climate change', 'country': 'demo'},
  ...
]
```

## Root Cause

Google periodically changes their internal Google Trends API endpoints without notice. The `pytrends` community library cannot keep up with these changes, leading to periodic breakage.

**Current pytrends version:** 4.9.2 (latest as of 2026-02-26)

## Solutions

### Option 1: Use Twitter/X Trending API (Recommended)
- **Pros:** More real-time, diverse topics, reliable API
- **Cons:** Requires Twitter API key (free tier available)
- **Implementation:** Replace `pytrends` with `tweepy` library

```python
import tweepy

# Get trending topics from Twitter
api = tweepy.API(auth)
trends = api.get_place_trends(id=23424977)  # US WOEID
```

### Option 2: Use News API for Trending Headlines
- **Pros:** Free tier (100 requests/day), reliable, news-focused
- **Cons:** More news-centric than general search trends
- **Implementation:** Use `newsapi-python` library

```python
from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key='YOUR_KEY')
headlines = newsapi.get_top_headlines(country='us')
```

### Option 3: Use Reddit Trending Subreddits
- **Pros:** Free, no API key needed, diverse topics
- **Cons:** Reddit-specific bias, less "mainstream"
- **Implementation:** Use `praw` library

```python
import praw

reddit = praw.Reddit(user_agent='researcher7')
trending = reddit.subreddit('all').hot(limit=25)
```

### Option 4: Manual Daily Update
- **Pros:** Complete control, always accurate
- **Cons:** Requires manual intervention
- **Implementation:** Update `demo_trends` list daily from actual Google Trends website

### Option 5: Use Paid Google Trends Service
- **Pros:** Official, reliable, comprehensive
- **Cons:** Costs money (~$200-500/month)
- **Services:** Glimpse, SimilarWeb, SEMrush

## Recommendation

**Short-term:** Accept demo data for testing, or manually update the demo list weekly.

**Long-term:** Switch to **Twitter Trending API** (Option 1):
- More dynamic and real-time than Google Trends
- Better for content generation (hashtags provide context)
- Free tier sufficient for our use case (1-2 API calls/day)
- More reliable API (Twitter maintains it professionally)

## Current Impact on Pipeline

**All runs since ~Feb 25 have used identical demo data:**
- artificial intelligence
- climate change  
- quantum computing
- renewable energy
- ...etc (same 25 topics every time)

**This means:**
- ✅ Pipeline still works end-to-end
- ✅ Claude API generation still successful
- ❌ Not generating fresh, timely content based on real trends
- ❌ Scripts are repetitive with similar themes

## Action Items

1. **Immediate:** Document this in README
2. **Near-term:** Add Twitter API integration (if free tier acceptable)
3. **Alternative:** Switch to News API for headline-based scripts
4. **Fallback:** Continue with demo data but update it weekly with real trending topics

## Related Files

- `src/trend_scraper.py` - Current implementation
- `src/trend_scraper_fixed.py` - Attempted web scraping fix (failed)
- `.env` - Would store API keys for alternatives
