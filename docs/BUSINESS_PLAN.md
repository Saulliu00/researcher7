# Researcher7: Trends-to-Script Bot
## Business Plan & Technical Specification

**Project Name:** Researcher7 (Trends-to-Script Bot)  
**Version:** 1.0  
**Date:** February 2026  
**Owner:** Saul Liu  
**Status:** Planning Phase  

---

## Executive Summary

Researcher7 is an AI-powered content generation system that automatically produces 30-minute voice scripts by bridging trending topics with academic research. The system is built on a **fully modular, pluggable pipeline** where every step — from data fetching to audio generation — can be configured to use different tools and providers. By default, it scrapes Google Trends, clusters topics with scikit-learn, finds papers via Semantic Scholar, and generates scripts with a local LLM — all with zero configuration.

**Value Proposition:**
- **Modular pipeline:** Every step uses a pluggable provider pattern — swap data sources, ML engines, LLMs, and output tools via config
- Automated content research and script generation
- Bridges popular culture (trending topics) with academic knowledge
- Reduces content creation time from hours to minutes
- Generates consistent, research-backed narrative scripts
- **Zero-config defaults** with the flexibility to customize every component

**Target Use Case:** Content creators, educators, podcasters, and knowledge workers who need to produce timely, research-based audio content.

---

## 1. Original Request & Problem Statement

### User Request
> "Build a bot that scrapes the last 24 hours' top 25 Google search terms, analyzes correlations between terms to generate a unified topic, finds a high-ranked research paper related to that topic, and generates a 30-minute voice script that bridges the trending terms → topic → research paper."

### Problem Statement
Content creators face two major challenges:
1. **Time-intensive research:** Finding trending topics, correlating them, and locating relevant academic sources is labor-intensive
2. **Synthesis difficulty:** Bridging popular trending topics with academic research requires significant domain knowledge and narrative skill

### Solution
A **modular, automated pipeline** where each step is a pluggable provider that can be swapped via configuration:
- **Fetches trending data** from configurable sources (Google Trends by default, or Twitter/X, Reddit, YouTube, Hacker News)
- **Identifies thematic connections** between disparate trending terms using pluggable correlation engines
- **Locates high-quality academic research** from configurable paper databases (Semantic Scholar, arXiv, PubMed, OpenAlex)
- **Generates a coherent 30-minute narrative script** connecting trends → theme → research using pluggable LLM providers
- **Optionally translates and synthesizes audio** via pluggable translation and TTS providers

---

## 2. System Architecture

### 2.1 High-Level Workflow

Every pipeline step follows a **pluggable provider** pattern: each step defines an abstract interface, and concrete implementations (providers) can be swapped via environment variables or CLI flags. Defaults are chosen for zero-config startup.

```
┌──────────────────────────────────────┐
│  Step 1: Data Fetcher (pluggable)    │
│  Providers:                          │
│   • Google Trends RSS  ← default    │
│   • Twitter/X Trends API            │
│   • Reddit Hot Topics               │
│   • YouTube Trends                   │
│   • Hacker News API                  │
│  Config: DATA_PROVIDER / --data-source│
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Step 2: Correlation Engine          │
│          (pluggable)                 │
│  Providers:                          │
│   • TF-IDF + DBSCAN    ← default   │
│   • LLM-based clustering            │
│   • Sentence-Transformers + HDBSCAN  │
│  Config: CORRELATION_PROVIDER        │
│          / --correlator              │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Step 3: Paper Finder (pluggable)    │
│  Providers:                          │
│   • Semantic Scholar    ← default   │
│   • arXiv API                        │
│   • PubMed                           │
│   • OpenAlex                         │
│  Config: PAPER_PROVIDER              │
│          / --paper-source            │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Step 4: Script Generator            │
│          (pluggable)                 │
│  Providers:                          │
│   • Ollama (local)      ← default  │
│   • Anthropic Claude (cloud)         │
│  Config: LLM_PROVIDER / --provider   │
└──────────────────┬───────────────────┘
                   │
                   ▼
            ┌──────┴──────┐
            │  lang=zh?   │
            └──┬──────┬───┘
          yes  │      │  no (default: en)
               ▼      │
┌──────────────────────┐│
│  Step 5: Translator  ││
│  (pluggable)         ││
│  Providers:          ││
│   • MarianMT         ││
│     ← default       ││
│   • LLM-based        ││
│   • Google Translate  ││
│   • DeepL            ││
│  Config:             ││
│   TRANSLATION_PROVIDER││
│   / --translator     ││
└──────────┬───────────┘│
           │             │
           ▼             ▼
┌──────────────────────────────────────┐
│  Step 6: Audio Generator (pluggable) │
│  Providers:                          │
│   • Piper TTS           ← default  │
│   • Coqui (XTTS v2)                 │
│   • Kokoro                           │
│   • Edge TTS (cloud)                 │
│  Config: TTS_PROVIDER / --tts        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Output Artifacts                    │
│   • Script (.md)                     │
│   • Audio (.wav)                     │
│   • Run log (.csv)                   │
└──────────────────────────────────────┘
```

### 2.2 Component Breakdown

All pipeline components follow the same **provider abstraction** pattern: a base interface defines the contract, and concrete providers implement it. Users select a provider via environment variable (`{STEP}_PROVIDER` in `.env`) or CLI flag. Every step ships with a **default provider** that requires zero extra configuration.

#### **Component 1: Data Fetcher** *(pluggable — `src/data_providers/`)*
- **Input:** Time window (default: last 24 hours), region, limit
- **Process:** Fetch trending/popular topics from the configured data source
- **Output:** JSON array of trending terms with metadata (volume, category, region)
- **Config:** `DATA_PROVIDER` env var / `--data-source` CLI flag
- **Pluggable providers:**

| Provider | Type | How it works | Config | Default |
|----------|------|-------------|--------|---------|
| **google_trends** | Cloud (RSS) | Google Trends RSS feed — no API key required | Region via `--country` | ✅ |
| **twitter** | Cloud (API) | Twitter/X Trends API — trending hashtags & topics | Requires `TWITTER_API_KEY` | |
| **reddit** | Cloud (API) | Reddit Hot Topics via PRAW — top posts from configurable subreddits | Requires `REDDIT_CLIENT_ID`, `REDDIT_SECRET` | |
| **youtube** | Cloud (API) | YouTube Trending Videos via Data API v3 | Requires `YOUTUBE_API_KEY` | |
| **hackernews** | Cloud (API) | Hacker News front-page stories via Firebase API | No key required | |

#### **Component 2: Correlation Engine** *(pluggable — `src/correlation_providers/`)*
- **Input:** Array of trending terms with metadata
- **Process:** Cluster terms, extract unified theme, generate bridge concept
- **Output:** Unified theme/topic with supporting term clusters and confidence scores
- **Config:** `CORRELATION_PROVIDER` env var / `--correlator` CLI flag
- **Pluggable providers:**

| Provider | Type | How it works | Config | Default |
|----------|------|-------------|--------|---------|
| **sklearn** | Offline | TF-IDF vectorization + DBSCAN clustering (scikit-learn) | No extra dependency | ✅ |
| **llm** | Offline/Cloud | Uses the configured LLM provider to cluster and extract themes | Uses `LLM_PROVIDER` setting | |
| **sentence_transformers** | Offline | Sentence-Transformers embeddings + HDBSCAN clustering | Downloads model on first use | |

#### **Component 3: Paper Finder** *(pluggable — `src/paper_providers/`)*
- **Input:** Unified topic/theme
- **Process:** Query academic databases, rank by citation count + relevance, filter for accessibility
- **Output:** Top-ranked paper (title, authors, abstract, URL, citation count)
- **Config:** `PAPER_PROVIDER` env var / `--paper-source` CLI flag
- **Pluggable providers:**

| Provider | Type | How it works | Config | Default |
|----------|------|-------------|--------|---------|
| **semantic_scholar** | Cloud (API) | Semantic Scholar API — full metadata + citation graph | Optional `SEMANTIC_SCHOLAR_API_KEY` for higher rate limits | ✅ |
| **arxiv** | Cloud (API) | arXiv API — preprints, sorted by relevance | No key required | |
| **pubmed** | Cloud (API) | PubMed/NCBI API — biomedical & life science literature | No key required | |
| **openalex** | Cloud (API) | OpenAlex API — open catalog of scholarly works | No key required | |

#### **Component 4: Script Generator** *(pluggable — `src/llm_providers/`)*
- **Input:** Trending terms + clusters, unified theme, research paper content
- **Process:** LLM generates 30-minute voice script with custom prompt template
- **Output:** 30-minute voice script (markdown format, ~4,500-5,000 words)
- **Config:** `LLM_PROVIDER` env var / `--provider` CLI flag
- **Pluggable providers:**

| Provider | Type | How it works | Config | Default |
|----------|------|-------------|--------|---------|
| **ollama** | Offline (local) | Local LLM via Ollama API — multi-pass generation for smaller models | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | ✅ |
| **anthropic** | Cloud (API) | Anthropic Claude — single-pass generation with large context window | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | |

#### **Component 5: Translator** *(conditional, pluggable — `src/translation_providers/`)*
- **Input:** English script from Component 4
- **Process:**
  - Activated only when user selects `--lang zh` before running the pipeline
  - Preserves section structure, narrative flow, and formatting
  - Skipped entirely in default English mode
- **Output:** Chinese-translated script (.md), saved alongside the English original
- **Config:** `TRANSLATION_PROVIDER` env var / `--translator` CLI flag
- **Pluggable providers:**

| Provider | Type | How it works | Config | Default |
|----------|------|-------------|--------|---------|
| **marianmt** | Offline | Helsinki-NLP MarianMT models — chunked paragraph translation | Downloads model on first use | ✅ |
| **llm** | Offline/Cloud | Uses the configured LLM provider to translate | Uses `LLM_PROVIDER` setting | |
| **google** | Cloud | Google Translate API via `googletrans` | Free, no API key | |
| **deepl** | Cloud | DeepL API (high quality) | Requires `DEEPL_API_KEY` | |

#### **Component 6: Audio Generator** *(pluggable — `src/tts_providers/`)*
- **Input:** Final script (English or Chinese, depending on language selection)
- **Process:**
  - Strips markdown metadata/formatting before synthesis
  - Splits long scripts into paragraph-sized chunks for stable generation
- **Output:** Audio file (.wav) saved to `outputs/audio/`
- **Config:** `TTS_PROVIDER` env var / `--tts` CLI flag
- **Pluggable providers:**

| Provider | Type | Model | EN | ZH | Default |
|----------|------|-------|----|----|---------|
| **piper** | Offline | Piper TTS | ✅ | ✅ | ✅ |
| **coqui** | Offline | XTTS v2 | ✅ | ✅ | |
| **kokoro** | Offline | Kokoro-82M | ✅ | ✅ | |
| **edge** | Cloud | Microsoft Edge TTS | ✅ | ✅ | |

**Language flow summary:**
- `--lang en` (default): Script (EN) → TTS Provider (EN voice) → Audio
- `--lang zh`: Script (EN) → Translation Provider (EN→ZH) → TTS Provider (ZH voice) → Audio

---

## 3. Technical Stack

### 3.1 Core Technologies

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Language** | Python 3.11+ | Rich data science ecosystem |
| **Data Sources** | Pluggable: Google Trends RSS (default), Twitter/X, Reddit, YouTube, Hacker News | Provider abstraction — swap via config |
| **NLP/ML** | Pluggable: scikit-learn TF-IDF + DBSCAN (default), LLM-based, Sentence-Transformers + HDBSCAN | Provider abstraction — swap via config |
| **LLM** | Pluggable: Ollama local (default), Anthropic Claude (cloud) | Provider abstraction — swap via config |
| **Paper Search** | Pluggable: Semantic Scholar (default), arXiv, PubMed, OpenAlex | Provider abstraction — swap via config |
| **Translation** | Pluggable: MarianMT (default), LLM-based, Google Translate, DeepL | Provider abstraction — swap via config |
| **TTS** | Pluggable: Piper TTS (default), Coqui, Kokoro, Edge TTS | Provider abstraction — swap via config |
| **SSL** | truststore | OS certificate store for corporate proxies |

### 3.2 External APIs & Services

| Service | Pipeline Step | Rate Limits | Cost |
|---------|--------------|-------------|------|
| **Google Trends RSS** | Data Fetcher (default) | Unlimited (RSS) | Free |
| **Twitter/X API v2** | Data Fetcher (alt) | 500K tweets/month (Basic) | Free tier / $100/mo |
| **Reddit API (PRAW)** | Data Fetcher (alt) | 100 req/min | Free |
| **YouTube Data API v3** | Data Fetcher (alt) | 10K units/day | Free |
| **Hacker News Firebase API** | Data Fetcher (alt) | Unlimited | Free |
| **Semantic Scholar API** | Paper Finder (default) | 100 req/5min | Free |
| **arXiv API** | Paper Finder (alt) | 1 req/3sec | Free |
| **PubMed/NCBI API** | Paper Finder (alt) | 3 req/sec (with key: 10/sec) | Free |
| **OpenAlex API** | Paper Finder (alt) | 100K req/day | Free |
| **Ollama** | Script Generator (default) | N/A (local) | Free |
| **Anthropic Claude API** | Script Generator (alt) | 50K req/min | ~$15/1M tokens |
| **Piper TTS** | Audio Generator (default) | N/A (local) | Free |
| **Coqui TTS (XTTS v2)** | Audio Generator (alt) | N/A (local) | Free |

### 3.3 Python Dependencies

```
# Core
python-dotenv>=1.0.0
requests>=2.31.0
truststore>=0.9.0

# NLP & ML (Correlation Engine — default: sklearn)
scikit-learn>=1.4.0
numpy>=1.24.0

# Academic Paper Search (Paper Finder — default: semantic_scholar)
semanticscholar>=0.8.3
arxiv>=2.1.0                    # alt provider: arxiv

# LLM Providers (Script Generator — optional based on configuration)
anthropic>=0.18.0               # alt provider: anthropic

# TTS (Audio Generator — default: piper)
piper-tts>=1.0.0                # default provider
TTS>=0.22.0                     # alt provider: coqui
```

**Optional dependencies for alternative providers:**
```
# Data Fetcher alternatives
tweepy>=4.14.0                  # provider: twitter
praw>=7.7.0                     # provider: reddit
google-api-python-client>=2.0   # provider: youtube

# Correlation Engine alternatives
sentence-transformers>=2.2.0    # provider: sentence_transformers
hdbscan>=0.8.33                 # provider: sentence_transformers

# Paper Finder alternatives
biopython>=1.81                 # provider: pubmed (Entrez)
pyalex>=0.13                    # provider: openalex

# Translation alternatives
googletrans>=4.0.0              # provider: google
deepl>=1.16.0                   # provider: deepl
```

### 3.4 Modular Configuration

Every pipeline step is configured through a consistent pattern:

| Pipeline Step | Env Variable | CLI Flag | Default |
|--------------|-------------|----------|---------|
| Data Fetcher | `DATA_PROVIDER` | `--data-source` | `google_trends` |
| Correlation Engine | `CORRELATION_PROVIDER` | `--correlator` | `sklearn` |
| Paper Finder | `PAPER_PROVIDER` | `--paper-source` | `semantic_scholar` |
| Script Generator | `LLM_PROVIDER` | `--provider` | `ollama` |
| Translator | `TRANSLATION_PROVIDER` | `--translator` | `marianmt` |
| Audio Generator | `TTS_PROVIDER` | `--tts` | `piper` |

**Configuration priority:** CLI flag > `.env` file > factory default

**Zero-config startup:** All defaults are chosen so that `python main.py` works out of the box with no API keys (Google Trends RSS + scikit-learn + Semantic Scholar + Ollama). Only alternative providers require additional configuration.

---

## 4. Implementation Phases

### Phase 1: Foundation & Provider Abstraction (Weeks 1-2)
**Goal:** Build core pipeline skeleton with pluggable provider architecture

**Tasks:**
- [ ] Set up project structure with provider abstraction layer
- [ ] Define base interfaces for all 6 pipeline steps (Data Fetcher, Correlation, Paper Finder, Script Generator, Translator, Audio Generator)
- [ ] Implement factory + registry pattern for provider discovery
- [ ] Implement Google Trends RSS provider (default data source)
- [ ] Implement provider configuration via `.env` and CLI flags
- [ ] Test end-to-end provider loading and fallback behavior

**Deliverables:**
- Working provider abstraction layer with factory pattern
- Google Trends RSS data fetcher (default provider)
- Configuration system (env vars + CLI flags)
- Unit tests for provider loading and data fetching

**Success Criteria:**
- Successfully retrieve top 25 trends via default provider (Google Trends)
- Providers are swappable via `DATA_PROVIDER` env var
- Adding a new provider requires only implementing the base interface

---

### Phase 2: Correlation Engine (Weeks 3-4)
**Goal:** Implement topic clustering and theme extraction with pluggable providers

**Tasks:**
- [ ] Define correlation provider base interface
- [ ] Implement sklearn provider (TF-IDF + DBSCAN) as default
- [ ] Implement LLM-based correlation provider (uses configured LLM)
- [ ] Build topic extraction logic
- [ ] Create correlation scoring system
- [ ] Test with historical trend data

**Deliverables:**
- Pluggable correlation engine with sklearn default
- LLM-based alternative for users without ML dependencies
- Correlation confidence scores

**Success Criteria:**
- Generate coherent unified topics from diverse trending terms
- Cluster accuracy >70% (manual validation)
- Providers are swappable via `CORRELATION_PROVIDER` env var

---

### Phase 3: Paper Discovery (Weeks 5-6)
**Goal:** Integrate academic search with pluggable paper providers

**Tasks:**
- [ ] Define paper provider base interface
- [ ] Implement Semantic Scholar provider (default)
- [ ] Implement arXiv provider (fallback/alternative)
- [ ] Build relevance scoring algorithm
- [ ] Add citation ranking logic
- [ ] Create fallback chain (try default, then alternatives)

**Deliverables:**
- Pluggable paper search with Semantic Scholar default
- arXiv fallback provider
- Paper ranking by relevance + citations

**Success Criteria:**
- Return top-ranked paper for 80%+ of generated topics
- Median citation count >10 for selected papers
- Providers are swappable via `PAPER_PROVIDER` env var

---

### Phase 4: Script Generation (Weeks 7-8)
**Goal:** LLM-powered narrative script creation

**Tasks:**
- [ ] Design prompt template for 30-min scripts
- [ ] Integrate Anthropic Claude API
- [ ] Implement script structure (intro, body, conclusion)
- [ ] Add narrative flow optimization
- [ ] Create output formatting (markdown, JSON metadata)

**Deliverables:**
- Claude API integration with custom prompts
- 30-minute script generator
- Quality assurance checks

**Success Criteria:**
- Generate scripts with 4,500-5,000 words
- Coherent narrative connecting trends → topic → research
- 80%+ user satisfaction (readability, flow)

---

### Phase 5: Integration & Testing (Weeks 9-10)
**Goal:** End-to-end pipeline validation

**Tasks:**
- [ ] Connect all components into single pipeline
- [ ] Add error handling and retry logic
- [ ] Implement logging and monitoring
- [ ] Load testing (concurrent requests)
- [ ] User acceptance testing

**Deliverables:**
- Fully integrated pipeline
- Error handling and graceful degradation
- Performance benchmarks

**Success Criteria:**
- End-to-end success rate >90%
- Pipeline completion time <5 minutes
- Handle 10 concurrent requests

---

### Phase 6: Deployment & Automation (Weeks 11-12)
**Goal:** Production deployment and scheduled runs

**Tasks:**
- [ ] Dockerize application
- [ ] Set up systemd service
- [ ] Configure scheduled jobs (daily runs)
- [ ] Set up monitoring (Prometheus/Grafana or simple logs)
- [ ] Create user documentation

**Deliverables:**
- Docker container with full stack
- Automated daily script generation
- Monitoring dashboard
- User guide and API documentation

**Success Criteria:**
- 99% uptime for scheduled jobs
- Automated daily script delivery
- <2 hour recovery time for failures

---

## 5. Data Flow & Script Structure

### 5.1 Input Data Example

**Trending Terms (Last 24h):**
```json
[
  {"term": "quantum computing breakthrough", "volume": 150000, "category": "Science"},
  {"term": "AI regulation EU", "volume": 120000, "category": "Politics"},
  {"term": "climate change summit", "volume": 95000, "category": "Environment"},
  ...
]
```

### 5.2 Correlation Output Example

**Unified Topic:**
```json
{
  "theme": "Technology Governance and Environmental Impact",
  "clusters": [
    {
      "label": "Emerging Tech",
      "terms": ["quantum computing breakthrough", "AI regulation EU"],
      "confidence": 0.87
    },
    {
      "label": "Climate Policy",
      "terms": ["climate change summit", "renewable energy"],
      "confidence": 0.82
    }
  ],
  "bridge_concept": "Sustainable Innovation Frameworks"
}
```

### 5.3 Paper Selection Example

**Selected Paper:**
```json
{
  "title": "Computational Sustainability: Computing for a Better World and Future",
  "authors": ["Carla P. Gomes"],
  "year": 2019,
  "citations": 342,
  "url": "https://arxiv.org/abs/1906.02748",
  "relevance_score": 0.91
}
```

### 5.4 Script Structure (30-Minute Format)

**Target Length:** 4,500-5,000 words (~150-165 words/minute reading pace)

**Structure:**
1. **Hook (0-2 min / 300-350 words):**
   - Introduce top trending terms
   - Tease the connection between them
   - Present the central question

2. **Trend Analysis (2-8 min / 900-1,000 words):**
   - Deep dive into 3-5 key trends
   - Explain why they're trending
   - Identify emerging patterns

3. **Topic Synthesis (8-15 min / 1,050-1,150 words):**
   - Reveal the unified theme
   - Connect disparate trends
   - Build narrative bridge to research

4. **Research Deep Dive (15-25 min / 1,500-1,700 words):**
   - Introduce the academic paper
   - Explain core findings
   - Connect research to trends

5. **Synthesis & Implications (25-28 min / 450-500 words):**
   - Bring trends and research together
   - Discuss real-world implications
   - Future outlook

6. **Conclusion (28-30 min / 300-350 words):**
   - Recap the journey (trends → topic → research)
   - Call to action or reflection
   - Closing thought

---

## 6. Budget & Resource Planning

### 6.1 Development Costs

| Item | Cost | Notes |
|------|------|-------|
| **Developer Time** | 480 hours @ $0 | Self-development (12 weeks × 40h) |
| **API Costs (Development)** | ~$50 | Claude API testing (~3M tokens) |
| **Server (Development)** | $0 | Raspberry Pi (existing) |
| **Total Development** | ~$50 | |

### 6.2 Production Costs (Annual)

| Item | Monthly | Annual | Notes |
|------|---------|--------|-------|
| **Claude API** | $100-150 | $1,200-1,800 | ~80-120M tokens/year |
| **VPS Hosting** | $20-40 | $240-480 | DigitalOcean/Linode droplet |
| **PostgreSQL** | $0 | $0 | Self-hosted |
| **Redis** | $0 | $0 | Self-hosted |
| **Domain/SSL** | $1-2 | $12-24 | Optional |
| **Total Annual** | ~$121-192 | ~$1,452-2,304 | |

### 6.3 Scaling Costs

**Per 1,000 Scripts:**
- API tokens: ~$100-120 (Claude)
- Storage: ~50GB (~$2-5)
- Compute: Negligible (batch processing)

**Break-even:** ~10-15 scripts/day at $0.50-1.00 per script value

---

## 7. Success Metrics & KPIs

### 7.1 Technical Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **Pipeline Success Rate** | >90% | <70% requires investigation |
| **Execution Time** | <5 min | <10 min acceptable |
| **Script Quality (Coherence)** | >8/10 (manual review) | >6/10 minimum |
| **Paper Relevance** | >80% relevant | >60% minimum |
| **Uptime** | 99% | 95% minimum |

### 7.2 Content Quality Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Narrative Coherence** | 8/10 | Manual review (5-point scale) |
| **Trend-Topic Alignment** | >85% | Semantic similarity score |
| **Research Integration** | >75% | Citation density, context usage |
| **Script Length** | 4,500-5,000 words | Automated word count |
| **Reading Level** | Grade 10-12 | Flesch-Kincaid readability |

### 7.3 User Satisfaction (Post-MVP)

- **Usability:** >80% find scripts useful
- **Accuracy:** >75% verify trend-research connection is valid
- **Time Savings:** >90% report time savings vs manual research

---

## 8. Risk Analysis & Mitigation

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Google Trends API rate limits** | High | Medium | Switch to alternative data provider (Twitter, Reddit, YouTube, Hacker News) via `DATA_PROVIDER` config; implement caching and retry logic |
| **Claude API downtime** | Low | High | Fall back to Ollama local LLM via `LLM_PROVIDER` config; queue system, retry with exponential backoff |
| **Paper search returns no results** | Medium | Medium | Try fallback paper providers (arXiv, PubMed, OpenAlex) via `PAPER_PROVIDER` config; broader query fallback |
| **Poor topic correlation** | Medium | High | Switch correlation provider (LLM-based vs sklearn) via `CORRELATION_PROVIDER` config; tunable clustering parameters |
| **Script quality inconsistent** | Medium | Medium | Prompt engineering, few-shot examples, quality checks |

### 8.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **API cost overruns** | Medium | Medium | Budget alerts, token usage monitoring, monthly caps |
| **Data storage growth** | Low | Low | Archive old scripts to cold storage, retention policy |
| **Trend scraping breaks** | Medium | Low | Switch to alternative data provider — modular architecture allows instant failover via config change |
| **Server downtime** | Low | Medium | Systemd auto-restart, uptime monitoring |

### 8.3 Content Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Misinformation in papers** | Low | High | Citation ranking filter, peer-review status check |
| **Offensive/controversial trends** | Medium | Medium | Content filtering, manual review option |
| **Copyright issues (paper PDFs)** | Low | Medium | Use abstracts only, link to original source |

---

## 9. Future Enhancements (Post-MVP)

### 9.1 Phase 2 Features
- **Additional data source providers:** News APIs (NewsAPI, Bing News), tech-specific feeds (Product Hunt, TechCrunch), regional trend sources
- **Additional paper providers:** Google Scholar scraper, CrossRef API, CORE API
- **Additional languages:** Extend translation module to Spanish, French, Japanese, Korean
- **Voice cloning:** Use Coqui XTTS voice cloning to generate audio in a custom voice
- **Web dashboard:** UI for browsing/searching generated scripts and playing audio
- **Provider health monitoring:** Automatic failover between providers when one is down

### 9.2 Phase 3 Features
- **Personalization:** User-defined topic preferences, industry focus
- **Collaborative filtering:** Recommend scripts based on user interests
- **Script variants:** Different lengths (10min, 20min, 45min)
- **Multi-paper synthesis:** Combine 2-3 papers for deeper analysis

### 9.3 Commercialization
- **SaaS model:** Subscription-based access ($10-50/month)
- **API licensing:** Sell API access to content platforms
- **White-label:** Custom deployments for media companies
- **Educational licensing:** Bulk licenses for universities

---

## 10. Project Timeline (12-Week Roadmap)

```
Week 1-2:   Foundation & Provider Abstraction Layer
Week 3-4:   Correlation Engine (Pluggable Providers)
Week 5-6:   Paper Discovery (Pluggable Providers)
Week 7-8:   Script Generation (LLM Providers)
Week 9-10:  Integration & Testing
Week 11-12: Deployment & Automation

Milestone Checkpoints:
├─ Week 2:  ✓ Provider abstraction layer + Google Trends default
├─ Week 4:  ✓ Topic generation with pluggable correlation
├─ Week 6:  ✓ Paper retrieval with pluggable providers
├─ Week 8:  ✓ First end-to-end script generated
├─ Week 10: ✓ Pipeline passing all tests
└─ Week 12: ✓ Production deployment live
```

---

## 11. Conclusion & Next Steps

### Summary
Researcher7 addresses a clear market need: automated, research-backed content generation that bridges trending topics with academic knowledge. The **fully modular, pluggable architecture** means every pipeline step can be customized to use different tools, APIs, and providers — while shipping with sensible defaults that work out of the box. The technical architecture is feasible with existing tools and APIs, and the cost structure is sustainable.

### Immediate Next Steps
1. **Repository setup:** Initialize GitHub repo with this business plan
2. **Environment setup:** Create Python virtual environment, install dependencies
3. **Provider abstraction:** Build the base provider interfaces and factory pattern for all 6 pipeline steps
4. **Proof of concept:** Build default providers (Google Trends + sklearn + Semantic Scholar + Ollama)
5. **Validation:** Generate 3-5 sample scripts to validate concept

### Success Criteria for Go/No-Go Decision
- [ ] Successfully fetch top 25 trends from default data provider (Google Trends)
- [ ] Providers are swappable via env var / CLI flag without code changes
- [ ] Generate coherent unified topic from trends (manual validation)
- [ ] Retrieve relevant academic paper (>70% success rate)
- [ ] Produce readable 30-minute script (>7/10 quality)

**Decision Point:** End of Week 2 (after Foundation phase)

---

## Appendix

### A. Alternative Approaches Considered

**Approach 1: Manual Curator (Rejected)**
- Pros: High quality, full human control
- Cons: Not scalable, defeats automation purpose

**Approach 2: Pure LLM (No Paper Search) (Rejected)**
- Pros: Simpler pipeline
- Cons: Lacks research grounding, accuracy concerns

**Approach 3: Pre-defined Topics (Rejected)**
- Pros: Easier to find papers
- Cons: Not responsive to real-time trends

**Selected Approach: Automated Pipeline (Trends → Correlation → Paper → Script)**
- Best balance of automation, quality, and real-time responsiveness

### B. Technology Alternatives (Now Built-in Providers)

The modular architecture means technology alternatives are **built-in providers**, not rejected approaches. Users can switch between them via configuration:

| Pipeline Step | Default Provider | Built-in Alternatives | Selection Criteria |
|--------------|-----------------|----------------------|-------------------|
| Data Fetcher | Google Trends RSS | Twitter/X, Reddit, YouTube, Hacker News | Coverage, API access, content domain |
| Correlation | scikit-learn (TF-IDF + DBSCAN) | LLM-based, Sentence-Transformers + HDBSCAN | Accuracy vs. speed vs. dependencies |
| Paper Finder | Semantic Scholar | arXiv, PubMed, OpenAlex | Domain focus, coverage, rate limits |
| Script Generator | Ollama (local) | Anthropic Claude (cloud) | Quality vs. cost vs. privacy |
| Translator | MarianMT (offline) | LLM-based, Google Translate, DeepL | Quality vs. speed vs. cost |
| Audio Generator | Piper TTS (offline) | Coqui, Kokoro, Edge TTS | Voice quality vs. language support |

### C. References & Prior Art

- **Similar Tools:**
  - Jasper.ai (general content generation)
  - Copy.ai (marketing content)
  - Descript (audio/video editing with AI)

- **Key Differences:**
  - Researcher7 is research-focused (academic grounding)
  - Real-time trend integration (not static templates)
  - Voice script optimization (narrative flow for audio)

- **Academic Papers:**
  - "Automatic Text Summarization" (Radev et al., 2002)
  - "Topic Modeling in Embedding Spaces" (Dieng et al., 2020)
  - "Retrieval-Augmented Generation" (Lewis et al., 2020)

---

**Document Version:** 2.0  
**Last Updated:** April 9, 2026  
**Author:** Saul Liu  
**Contact:** saul.liu00@gmail.com  
**GitHub:** https://github.com/Saulliu00/researcher7  

---

*This business plan is a living document. Updates will be versioned and tracked in git.*
