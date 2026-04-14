# Researcher7 Setup Guide

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd /home/saul/.openclaw/workspace/researcher7

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR: venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
nano .env  # or your preferred editor
```

Add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

**Where to get your API key:**
- Go to: https://console.anthropic.com/
- Navigate to "API Keys"
- Create a new key or copy an existing one

### 3. Test the Installation

```bash
# Test trend scraper
python src/trend_scraper.py

# Test correlation engine (downloads ~80MB NLP model on first run)
python src/correlation_engine.py
```

### 4. Run Your First Script

```bash
# Run the full pipeline
python main.py

# Or with custom options:
python main.py --trends 15 --country united_states
```

## Expected Output

```
🚀 Starting Researcher7 Pipeline

📊 Step 1: Scraping Trending Topics
------------------------------------------------------------
✓ Retrieved 25 trending topics
  Top 3: artificial intelligence, climate change, quantum computing

🔗 Step 2: Analyzing Correlations
------------------------------------------------------------
Loading NLP model: all-MiniLM-L6-v2...
✓ Unified Topic: Technology and Environment Trends
  Confidence: 82%
  Clusters: 3

📚 Step 3: Finding Research Paper
------------------------------------------------------------
Searching for papers on: Technology and Environment Trends
✓ Found: AI for Climate Change Mitigation (342 citations)

✍️  Step 4: Generating Voice Script
------------------------------------------------------------
Generating script with claude-sonnet-4-5...
✓ Generated script (4,847 words)

💾 Step 5: Saving Output
------------------------------------------------------------
✓ Script saved: outputs/2026-02-22_technology-and-environment-trends.md

✅ Pipeline Complete!
```

## File Structure

```
researcher7/
├── main.py                 # Main pipeline orchestrator
├── requirements.txt        # Python dependencies
├── .env                    # API keys (you create this)
├── .env.example           # Template for .env
├── src/
│   ├── trend_scraper.py       # Google Trends scraper
│   ├── correlation_engine.py  # NLP analysis & clustering
│   ├── paper_finder.py        # Academic paper search
│   └── script_generator.py    # Claude-powered script gen
├── outputs/               # Generated scripts (created on first run)
├── BUSINESS_PLAN.md      # Full project documentation
└── README.md             # Project overview
```

## Troubleshooting

### "No module named 'pytrends'"
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not found"
```bash
# Check .env file exists
ls -la .env

# Verify it contains your key
cat .env

# Make sure you're running from the project directory
cd /home/saul/.openclaw/workspace/researcher7
python main.py
```

### "Google Trends API rate limit"
The trend scraper includes fallback demo data. If you hit rate limits frequently:
- Wait 30-60 minutes between runs
- Use the demo data (automatically triggered on API failure)

### "No papers found"
If Semantic Scholar fails:
- The system automatically tries arXiv as backup
- Try a broader topic (edit correlation engine)
- Check your internet connection

### NLP Model Download Slow
First run downloads ~80MB sentence-transformer model:
- This only happens once
- Stored in `~/.cache/torch/sentence_transformers/`
- Takes 1-5 minutes depending on connection

## Command Line Options

```bash
# Default (25 trends, US)
python main.py

# Analyze 15 trends
python main.py --trends 15

# Different country
python main.py --country india

# Custom output directory
python main.py --output my_scripts/

# All options
python main.py --trends 20 --country united_kingdom --output uk_scripts/
```

## Cost Estimates

**Per Script Run:**
- Google Trends: Free
- Semantic Scholar: Free
- arXiv: Free
- Claude API: ~$0.10-0.15 (depending on script length)

**Monthly (Daily Scripts):**
- ~$3-5 for 30 scripts
- Mostly Claude API costs
- Other services are free

## Next Steps

1. **Review Generated Script:** Check `outputs/` directory
2. **Customize Prompts:** Edit `src/script_generator.py` for different styles
3. **Adjust Topics:** Tune `src/correlation_engine.py` clustering parameters
4. **Automate:** Set up cron job for daily scripts

## Getting Help

- **Issues:** https://github.com/Saulliu00/researcher7/issues
- **Email:** saul.liu00@gmail.com
- **Documentation:** See BUSINESS_PLAN.md for architecture details

---

**Time to First Script:** ~5 minutes after setup  
**Setup Time:** ~10 minutes (mostly dependency downloads)
