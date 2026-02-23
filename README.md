# Researcher7: Trends-to-Script Bot

> AI-powered content generation that bridges trending topics with academic research

[![Status](https://img.shields.io/badge/status-planning-yellow)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## Overview

Researcher7 automatically generates 30-minute voice scripts by:
1. 📊 Scraping the last 24 hours' top 25 Google search trends
2. 🔗 Analyzing correlations to identify a unified topic
3. 📚 Finding high-ranked academic research papers
4. ✍️ Generating narrative scripts connecting trends → topic → research

**Perfect for:** Content creators, educators, podcasters, and knowledge workers who need research-backed audio content.

---

## Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/Saulliu00/researcher7.git
cd researcher7

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# Run the pipeline
python main.py
```

**See [SETUP.md](./SETUP.md) for detailed setup instructions and troubleshooting.**

### Example Output
```bash
$ python main.py --date 2026-02-20

✓ Scraped 25 trending terms
✓ Generated unified topic: "AI Regulation and Digital Privacy"
✓ Found paper: "The Age of Surveillance Capitalism" (citations: 8,234)
✓ Generated 4,847-word script

Output: outputs/2026-02-20_ai-regulation-digital-privacy.md
```

---

## Features

### Core Capabilities
- 🔍 **Real-time Trend Monitoring:** Google Trends scraping with 24-hour windows
- 🧠 **NLP-Powered Correlation:** Semantic clustering to find thematic connections
- 📖 **Academic Paper Discovery:** Multi-source search (Semantic Scholar, arXiv)
- 🎯 **Intelligent Script Generation:** Claude-powered narrative scripts optimized for voice

### Technical Highlights
- **Async Pipeline:** FastAPI-based for concurrent processing
- **Multi-source Search:** Redundant academic databases for reliability
- **Quality Assurance:** Automated coherence checks and readability scoring
- **Cost Optimized:** Caching, batching, and smart API usage

---

## Architecture

```
┌─────────────────┐
│ Google Trends   │
│   (pytrends)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐       ┌──────────────────┐
│ Correlation     │──────▶│  Paper Finder    │
│ Engine (NLP)    │       │  (Scholar/arXiv) │
└─────────────────┘       └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Script Generator │
                          │  (Claude API)    │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  Output Script   │
                          │  (Markdown/JSON) │
                          └──────────────────┘
```

See [BUSINESS_PLAN.md](./BUSINESS_PLAN.md) for detailed architecture and technical specifications.

---

## Project Status

**Current Phase:** ✅ Phase 1 Complete - MVP Ready!  
**Status:** Working end-to-end pipeline (simplified, no database yet)

### Roadmap
- [x] **Phase 1:** Foundation - Core pipeline working! ✨
  - [x] Trend scraper (Google Trends via pytrends)
  - [x] Correlation engine (NLP embeddings + clustering)
  - [x] Paper finder (Semantic Scholar + arXiv)
  - [x] Script generator (Claude API)
  - [x] End-to-end pipeline integration
- [ ] **Phase 2:** Database & Persistence — *Next*
- [ ] **Phase 3:** Web Interface & API
- [ ] **Phase 4:** Advanced Features (multi-language, audio generation)
- [ ] **Phase 5:** Production Deployment & Automation

See [BUSINESS_PLAN.md](./BUSINESS_PLAN.md) for detailed timeline and milestones.

---

## Documentation

- 📋 **[Business Plan](./BUSINESS_PLAN.md):** Complete project specification, architecture, budget, and roadmap
- 📖 **[API Documentation](#):** Coming soon
- 🎓 **[User Guide](#):** Coming soon
- 🔧 **[Development Guide](#):** Coming soon

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11+ |
| **Framework** | FastAPI |
| **NLP/ML** | sentence-transformers, scikit-learn |
| **LLM** | Anthropic Claude API |
| **Database** | PostgreSQL + SQLAlchemy |
| **Cache** | Redis |
| **Deployment** | Docker + systemd |

**External APIs:**
- Google Trends (pytrends)
- Semantic Scholar API
- arXiv API
- Anthropic Claude API

---

## Example Use Cases

### 1. Daily Podcast Scripts
Generate a daily 30-minute script connecting trending news to academic research:
```bash
python main.py --daily --output podcasts/
```

### 2. Educational Content
Create explainer scripts for specific trending topics:
```bash
python main.py --topic "quantum computing" --paper-filter "physics"
```

### 3. Batch Processing
Generate scripts for the last 7 days:
```bash
python main.py --batch --start-date 2026-02-14 --end-date 2026-02-20
```

---

## Cost Estimate

**Development:** ~$50 (API testing)  
**Production (Annual):** $1,200-1,800 (Claude API) + $240-480 (hosting) = **~$1,440-2,280/year**

**Per Script:** ~$0.10-0.15 (API costs)

See [BUSINESS_PLAN.md](./BUSINESS_PLAN.md) Section 6 for detailed budget breakdown.

---

## Contributing

This project is currently in the planning phase. Contributions will be welcome after the MVP is complete.

### Development Setup (Coming Soon)
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

## Contact

**Saul Liu**  
📧 Email: saul.liu00@gmail.com  
🐙 GitHub: [@Saulliu00](https://github.com/Saulliu00)  
💬 Issues: [GitHub Issues](https://github.com/Saulliu00/researcher7/issues)

---

## Acknowledgments

- **Google Trends API:** Trend data via [pytrends](https://github.com/GeneralMills/pytrends)
- **Semantic Scholar:** Academic paper search API
- **Anthropic:** Claude API for script generation
- **OpenClaw:** Development framework and automation

---

**Status:** 🚧 Under Construction — Check back soon for updates!

*Last updated: February 21, 2026*
