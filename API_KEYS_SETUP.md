# API Keys Setup Guide

To get real trending topics instead of demo data, you need API keys for at least one of these services (all three recommended):

## 1. X/Twitter API (Recommended - Most Real-Time)

**Free Tier:** 1,500 requests/month (more than enough - we use 1-2/day)

### Setup Steps:

1. **Sign up for Twitter Developer Account:**
   - Go to: https://developer.twitter.com/en/portal/dashboard
   - Click "Sign up for Free Account"
   - Log in with your Twitter/X account

2. **Create a Project + App:**
   - Click "Create Project"
   - Name: "Researcher7" (or anything)
   - Use case: "Exploring the API" or "Making a bot"
   - Description: "Trending topics scraper for content generation"

3. **Get Bearer Token:**
   - After creating the app, go to "Keys and tokens" tab
   - Click "Generate" under "Bearer Token"
   - **Copy the Bearer Token** (you won't see it again!)

4. **Add to .env:**
   ```bash
   TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAABearerTokenHere1234567890
   ```

---

## 2. News API (Recommended - Most Reliable)

**Free Tier:** 100 requests/day (plenty for daily scripts)

### Setup Steps:

1. **Sign up:**
   - Go to: https://newsapi.org/register
   - Enter email and password
   - Verify email

2. **Get API Key:**
   - After login, go to: https://newsapi.org/account
   - Your API key is shown at the top

3. **Add to .env:**
   ```bash
   NEWS_API_KEY=1234567890abcdef1234567890abcdef
   ```

---

## 3. Reddit API (Recommended - Free & Unlimited)

**Free Tier:** Unlimited (no rate limits for read-only access)

### Setup Steps:

1. **Create Reddit App:**
   - Go to: https://www.reddit.com/prefs/apps
   - Scroll to bottom, click "Create another app..."
   
2. **Fill in details:**
   - Name: "Researcher7"
   - Type: **Select "script"**
   - Description: "Trending topics scraper"
   - About URL: (leave blank)
   - Redirect URI: `http://localhost:8080` (required but not used)
   - Click "Create app"

3. **Get Credentials:**
   - After creation, you'll see:
     - **Client ID:** Under the app name (looks like: `abcdef123456`)
     - **Client Secret:** Next to "secret" (looks like: `1234567890abcdefghij`)

4. **Add to .env:**
   ```bash
   REDDIT_CLIENT_ID=abcdef123456
   REDDIT_CLIENT_SECRET=1234567890abcdefghij
   ```

---

## Testing

After adding keys to `.env`, test the scraper:

```bash
cd /home/saul/.openclaw/workspace/researcher7
source venv/bin/activate
python src/trend_scraper_multi.py
```

**Expected output:**
```
✓ Twitter API initialized
✓ News API initialized
✓ Reddit API initialized
✓ Got 5 trends from Twitter
✓ Got 5 trends from News API
✓ Got 5 trends from Reddit

======================================================================
COMBINED TRENDING TOPICS (Top 15)
======================================================================
 1. tesla               [X/Twitter     ] (12 mentions)
 2. election            [News API      ] (8 mentions)
 3. gaming              [Reddit        ] (15 mentions)
...
```

---

## Minimum Requirements

**For the pipeline to work, you need AT LEAST ONE of:**
- ✅ Twitter Bearer Token (best for real-time trends)
- ✅ News API Key (best for news-focused topics)
- ✅ Reddit API credentials (best for community trends)

**Recommended:** Get all three (5 minutes total setup, all free)

---

## Troubleshooting

### Twitter API says "Not authorized"
- Make sure you copied the **Bearer Token**, not the API Key
- Bearer tokens start with: `AAAAAAAAAAAAA...`

### News API says "Invalid API key"
- Double-check you copied the full key from newsapi.org/account
- No spaces before/after the key in .env

### Reddit API says "401 Unauthorized"
- Make sure you selected **"script"** type when creating the app
- Both CLIENT_ID and CLIENT_SECRET are required

### All APIs fail
- The pipeline will fall back to demo data
- Check your `.env` file has no typos
- Make sure `.env` is in the project root directory

---

## Cost Summary

| Service | Free Tier | Our Usage | Cost |
|---------|-----------|-----------|------|
| **X/Twitter** | 1,500/month | ~60/month | $0 |
| **News API** | 100/day | ~1/day | $0 |
| **Reddit** | Unlimited | ~1/day | $0 |
| **Total** | - | - | **$0/month** |

All three services are **completely free** for our use case! 🎉
