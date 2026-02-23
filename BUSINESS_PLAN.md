# Researcher7: Trends-to-Script Bot
## Business Plan & Technical Specification

**Project Name:** Researcher7 (Trends-to-Script Bot)  
**Version:** 1.0  
**Date:** February 2026  
**Owner:** Saul Liu  
**Status:** Planning Phase  

---

## Executive Summary

Researcher7 is an AI-powered content generation system that automatically produces 30-minute voice scripts by bridging trending search topics with academic research. The system scrapes real-time search trends, identifies correlations between topics, locates relevant academic papers, and generates narrative scripts suitable for audio content creation.

**Value Proposition:**
- Automated content research and script generation
- Bridges popular culture (trending topics) with academic knowledge
- Reduces content creation time from hours to minutes
- Generates consistent, research-backed narrative scripts

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
An automated pipeline that:
- Monitors real-time search trends (Google Trends)
- Identifies thematic connections between disparate trending terms
- Locates high-quality academic research related to the unified theme
- Generates a coherent 30-minute narrative script connecting trends → theme → research

---

## 2. System Architecture

### 2.1 High-Level Workflow

```
┌─────────────────────┐
│  Google Trends API  │
│   (Last 24h Data)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Trend Scraper      │
│  - Top 25 terms     │
│  - Metadata         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Correlation Engine │
│  - NLP analysis     │
│  - Topic clustering │
│  - Theme generation │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Paper Finder       │
│  - Academic search  │
│  - Relevance score  │
│  - Citation rank    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Script Generator   │
│  - LLM (Claude)     │
│  - 30-min format    │
│  - Narrative flow   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Output Artifacts   │
│  - Script (.md)     │
│  - Metadata (.json) │
│  - Audio (optional) │
└─────────────────────┘
```

### 2.2 Component Breakdown

#### **Component 1: Trend Scraper**
- **Input:** Time window (default: last 24 hours)
- **Process:** Query Google Trends API for top 25 search terms
- **Output:** JSON array of trending terms with metadata (volume, category, region)

#### **Component 2: Correlation Engine**
- **Input:** Array of 25 trending terms
- **Process:** 
  - NLP embedding analysis (sentence transformers)
  - Semantic clustering (DBSCAN/hierarchical)
  - Topic extraction (LDA or Claude API)
- **Output:** Unified theme/topic with supporting term clusters

#### **Component 3: Paper Finder**
- **Input:** Unified topic/theme
- **Process:**
  - Query academic databases (Google Scholar, arXiv, Semantic Scholar)
  - Rank by citation count + relevance score
  - Filter for open-access availability
- **Output:** Top-ranked paper (title, authors, abstract, URL, PDF)

#### **Component 4: Script Generator**
- **Input:** 
  - Trending terms + clusters
  - Unified theme
  - Research paper content
- **Process:** Claude API with custom prompt template
- **Output:** 30-minute voice script (markdown format, ~4,500-5,000 words)

---

## 3. Technical Stack

### 3.1 Core Technologies

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Language** | Python 3.11+ | Rich data science ecosystem, async support |
| **Framework** | FastAPI | Async, modern, easy API creation |
| **Data Processing** | Pandas, NumPy | Industry-standard data manipulation |
| **NLP/ML** | sentence-transformers, scikit-learn | Pre-trained embeddings, clustering |
| **LLM** | Anthropic Claude API | Best-in-class long-form generation |
| **Database** | PostgreSQL + SQLAlchemy | Structured data, trend history |
| **Cache** | Redis | API response caching, rate limiting |
| **Deployment** | Docker + systemd | Containerized, auto-restart |

### 3.2 External APIs & Services

| Service | Purpose | Rate Limits | Cost |
|---------|---------|-------------|------|
| **Google Trends (unofficial)** | Trend scraping | ~100 req/hour | Free (pytrends) |
| **Semantic Scholar API** | Paper search | 100 req/5min | Free |
| **arXiv API** | Preprint papers | 1 req/3sec | Free |
| **Anthropic Claude API** | Script generation | 50K req/min | ~$15/1M tokens |

### 3.3 Python Dependencies

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pytrends>=4.9.0
sentence-transformers>=2.2.2
scikit-learn>=1.3.0
anthropic>=0.7.0
semanticscholar>=0.4.0
arxiv>=1.4.0
pydantic>=2.4.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
redis>=5.0.0
httpx>=0.25.0
pandas>=2.1.0
numpy>=1.24.0
```

---

## 4. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Build core scraping and data pipeline

**Tasks:**
- [ ] Set up project structure (FastAPI skeleton)
- [ ] Implement Google Trends scraper
- [ ] Create database schema (trends, papers, scripts)
- [ ] Build basic data storage layer
- [ ] Test trend retrieval (validate top 25 output)

**Deliverables:**
- Working trend scraper with 24h data retrieval
- PostgreSQL database with schema
- Unit tests for scraper module

**Success Criteria:**
- Successfully retrieve top 25 trends for any 24h window
- Store trend data with timestamps and metadata

---

### Phase 2: Correlation Engine (Weeks 3-4)
**Goal:** Implement topic clustering and theme extraction

**Tasks:**
- [ ] Integrate sentence-transformers for embeddings
- [ ] Implement clustering algorithms (DBSCAN, hierarchical)
- [ ] Build topic extraction logic
- [ ] Create correlation scoring system
- [ ] Test with historical trend data

**Deliverables:**
- NLP pipeline for term clustering
- Unified topic generation from 25 terms
- Correlation confidence scores

**Success Criteria:**
- Generate coherent unified topics from diverse trending terms
- Cluster accuracy >70% (manual validation)

---

### Phase 3: Paper Discovery (Weeks 5-6)
**Goal:** Integrate academic search and ranking

**Tasks:**
- [ ] Implement Semantic Scholar API integration
- [ ] Implement arXiv API integration
- [ ] Build relevance scoring algorithm
- [ ] Add citation ranking logic
- [ ] Create fallback search strategies

**Deliverables:**
- Multi-source academic search engine
- Paper ranking by relevance + citations
- PDF/abstract extraction

**Success Criteria:**
- Return top-ranked paper for 80%+ of generated topics
- Median citation count >10 for selected papers

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
| **Google Trends API rate limits** | High | Medium | Implement caching, retry logic, fallback to alternative sources |
| **Claude API downtime** | Low | High | Queue system, retry with exponential backoff |
| **Paper search returns no results** | Medium | Medium | Multi-source search (Scholar + arXiv), broader query fallback |
| **Poor topic correlation** | Medium | High | Manual validation during dev, tunable clustering parameters |
| **Script quality inconsistent** | Medium | Medium | Prompt engineering, few-shot examples, quality checks |

### 8.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **API cost overruns** | Medium | Medium | Budget alerts, token usage monitoring, monthly caps |
| **Data storage growth** | Low | Low | Archive old scripts to cold storage, retention policy |
| **Trend scraping breaks** | Medium | High | Error monitoring, email alerts, automated health checks |
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
- **Multi-language support:** Generate scripts in Spanish, French, Mandarin
- **Voice synthesis integration:** Auto-generate audio files (ElevenLabs/OpenAI)
- **Web dashboard:** UI for browsing/searching generated scripts
- **Custom trend sources:** Twitter trending, Reddit hot topics, YouTube trends

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
Week 1-2:   Foundation (Scraper + Database)
Week 3-4:   Correlation Engine (NLP + Clustering)
Week 5-6:   Paper Discovery (Academic Search)
Week 7-8:   Script Generation (LLM Integration)
Week 9-10:  Integration & Testing
Week 11-12: Deployment & Automation

Milestone Checkpoints:
├─ Week 2:  ✓ Trend scraper operational
├─ Week 4:  ✓ Topic generation from 25 trends
├─ Week 6:  ✓ Paper retrieval working
├─ Week 8:  ✓ First end-to-end script generated
├─ Week 10: ✓ Pipeline passing all tests
└─ Week 12: ✓ Production deployment live
```

---

## 11. Conclusion & Next Steps

### Summary
Researcher7 addresses a clear market need: automated, research-backed content generation that bridges trending topics with academic knowledge. The technical architecture is feasible with existing tools and APIs, and the cost structure is sustainable.

### Immediate Next Steps
1. **Repository setup:** Initialize GitHub repo with this business plan
2. **Environment setup:** Create Python virtual environment, install dependencies
3. **Proof of concept:** Build minimal trend scraper + Claude script generator (Week 1 goal)
4. **Validation:** Generate 3-5 sample scripts to validate concept

### Success Criteria for Go/No-Go Decision
- [ ] Successfully scrape top 25 trends from Google Trends
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

### B. Technology Alternatives

| Component | Selected | Alternative Considered | Reason for Selection |
|-----------|----------|----------------------|---------------------|
| LLM | Claude API | GPT-4, Llama 3 | Best long-form quality, context window |
| NLP | sentence-transformers | OpenAI embeddings | Free, self-hosted, proven |
| Database | PostgreSQL | MongoDB, SQLite | Relational structure, production-ready |
| Deployment | Docker | Kubernetes, VM | Right-sized for single service |

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

**Document Version:** 1.0  
**Last Updated:** February 21, 2026  
**Author:** Saul Liu  
**Contact:** saul.liu00@gmail.com  
**GitHub:** https://github.com/Saulliu00/researcher7  

---

*This business plan is a living document. Updates will be versioned and tracked in git.*
