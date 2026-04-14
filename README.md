# Researcher7: Trends-to-Script Pipeline

> Automatically generate 30-minute podcast scripts by connecting real-time trends with academic research — fully modular with pluggable providers for every step.

[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Tests](https://img.shields.io/badge/tests-59%20passed-brightgreen)]()

## How It Works

```
Data Fetcher ──▶ Correlation Engine ──▶ Paper Finder ──▶ Script Generator ──▶ Translator ──▶ Audio Generator
 (pluggable)       (pluggable)          (pluggable)       (pluggable)        (pluggable)      (pluggable)
```

Every pipeline step is backed by a **pluggable provider**. Switch implementations via CLI flags, environment variables, or `.env` — no code changes required.

| Step | Default Provider | Alternatives |
|------|-----------------|-------------|
| 1. Data Fetcher | Google Trends RSS | *(extensible)* |
| 2. Correlation Engine | scikit-learn (TF-IDF + DBSCAN) | *(extensible)* |
| 3. Paper Finder | Semantic Scholar | arXiv |
| 4. Script Generator | Ollama (local) | Anthropic Claude (cloud) |
| 5. Translator | MarianMT | *(extensible)* |
| 6. Audio Generator | Piper TTS | *(extensible)* |

## Quick Start

```bash
# Clone
git clone https://github.com/Saulliu00/researcher7.git
cd researcher7

# Virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env — set LLM_PROVIDER and keys

# Run
python main.py
```

## CLI Options

```bash
python main.py                                  # defaults: 25 trends, US, Ollama
python main.py --trends 15                      # fewer trends
python main.py --country united_kingdom         # different country
python main.py --provider anthropic             # use Claude instead of Ollama
python main.py --data-source google_trends      # explicit data provider
python main.py --correlator sklearn             # explicit correlation provider
python main.py --paper-source arxiv             # use arXiv instead of Semantic Scholar
python main.py --lang zh --translator marianmt  # translate to Chinese
python main.py --tts piper                      # generate audio via Piper TTS
python main.py --output my_outputs              # custom output directory
```

CLI flags override environment variables, which override factory defaults.

## Example Run

```
🚀 Starting Researcher7 Pipeline

📊 Step 1: Fetching Trending Data (Google Trends RSS)
✓ Retrieved 25 trending topics
  Top 3: artificial intelligence, climate change, quantum computing

🔗 Step 2: Analyzing Correlations (TF-IDF + DBSCAN)
✓ Unified Topic: Technology and Society Trends
  Confidence: 45.00%
  Clusters: 3

📚 Step 3: Finding Research Paper (Semantic Scholar)
  Paper: AI for Climate Change Mitigation...
  Citations: 342

✍️  Step 4: Generating Voice Script
✓ Section 1/10: Opening Hook... 412 words
✓ Section 2/10: Trends Overview... 508 words
...
✅ Generated script: 4,730 words

💾 Step 5: Saving Output
✓ Script saved: outputs/scripts/2026-04-09_technology-and-society-trends.md

📋 Run logged to outputs/run_log.csv
```

## Project Structure

```
researcher7/
├── main.py                          # Pipeline orchestrator + CLI + CSV logger
├── test_pipeline.py                 # Integration test (steps 1-3, no LLM)
├── tests/
│   └── test_units.py                # 59 unit tests (all steps, no LLM needed)
├── requirements.txt
├── .env.example
├── src/
│   ├── data_providers/              # Step 1: Trend data fetching
│   │   ├── base.py                  #   DataProvider ABC
│   │   ├── google_trends_provider.py#   Google Trends RSS implementation
│   │   └── __init__.py              #   Factory + registry
│   ├── correlation_providers/       # Step 2: Trend clustering
│   │   ├── base.py                  #   CorrelationProvider ABC
│   │   ├── sklearn_provider.py      #   TF-IDF + DBSCAN implementation
│   │   └── __init__.py              #   Factory + registry
│   ├── paper_providers/             # Step 3: Academic paper search
│   │   ├── base.py                  #   PaperProvider ABC
│   │   ├── semantic_scholar_provider.py
│   │   ├── arxiv_provider.py
│   │   └── __init__.py              #   Factory + registry
│   ├── llm_providers/               # Step 4: LLM text generation
│   │   ├── base.py                  #   LLMProvider ABC
│   │   ├── ollama_provider.py       #   Local Ollama
│   │   ├── anthropic_provider.py    #   Anthropic Claude
│   │   └── __init__.py              #   Factory + registry
│   ├── translation_providers/       # Step 5: Text translation
│   │   ├── base.py                  #   TranslationProvider ABC
│   │   ├── marianmt_provider.py     #   MarianMT (HuggingFace)
│   │   └── __init__.py              #   Factory + registry
│   ├── tts_providers/               # Step 6: Text-to-speech
│   │   ├── base.py                  #   TTSProvider ABC
│   │   ├── piper_provider.py        #   Piper TTS
│   │   └── __init__.py              #   Factory + registry
│   ├── script_generator.py          # Multi-pass / single-pass script builder
│   └── audio_generator.py           # Markdown stripping + TTS delegation
├── outputs/
│   ├── run_log.csv                  # Master log of all pipeline runs
│   ├── scripts/                     # Final generated voice scripts
│   └── autosave/                    # Section-by-section auto-saves
├── logs/                            # Archived old run logs
└── docs/                            # Project documentation
```

### Provider Architecture

Each provider package follows the same pattern:

```
src/<step>_providers/
├── base.py        # Abstract base class (ABC) defining the interface
├── <impl>.py      # One or more concrete implementations
└── __init__.py    # Factory function + provider registry dict
```

To add a new provider, create a new `<impl>.py` and register it in `__init__.py`.

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `ollama` or `anthropic` | `ollama` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Ollama model name | `phi4-mini:latest` |
| `ANTHROPIC_API_KEY` | Claude API key | — |
| `ANTHROPIC_MODEL` | Claude model name | `claude-sonnet-4-5` |
| `DATA_PROVIDER` | Data-fetching provider | `google_trends` |
| `CORRELATION_PROVIDER` | Correlation provider | `sklearn` |
| `PAPER_PROVIDER` | Paper search provider | `semantic_scholar` |
| `TRANSLATION_PROVIDER` | Translation provider | `marianmt` |
| `TTS_PROVIDER` | TTS provider | `piper` |
| `SEMANTIC_SCHOLAR_API_KEY` | Optional, increases rate limits | — |

### Resolution Order

CLI flag > Environment variable (`.env`) > Factory default

## Testing

```bash
# Run all 59 unit tests (no LLM or network required)
python -m pytest tests/test_units.py -v

# Run integration test (steps 1-3, no LLM)
python -m pytest test_pipeline.py -v
```

Unit tests cover all 6 pipeline steps with mocked externals:
- Provider factory creation, registration, and error handling
- Google Trends RSS parsing, limits, country codes, and network fallback
- TF-IDF + DBSCAN clustering, theme generation, and edge cases
- Semantic Scholar and arXiv paper search with mocked APIs
- Multi-pass (10 sections) and single-pass script generation
- Markdown stripping for TTS audio output
- Full pipeline integration with custom mock providers
- CSV run logger header/append behavior

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Data fetching | Google Trends RSS feed |
| NLP clustering | scikit-learn (TF-IDF + DBSCAN) |
| Paper search | Semantic Scholar API, arXiv API |
| Script generation | Ollama (local) or Anthropic Claude (cloud) |
| Translation | MarianMT (HuggingFace Transformers) |
| Text-to-speech | Piper TTS |
| SSL handling | truststore (OS certificate store) |

## Run Log (CSV)

Every pipeline run appends a row to `outputs/run_log.csv`:

| Column | Description |
|--------|-------------|
| `timestamp` | When the run started |
| `country` | Country used for trends |
| `lang` | Output language (`en` or `zh`) |
| `num_trends` | Number of trends fetched |
| `search_terms` | All trending terms (pipe-separated) |
| `unified_topic` | The identified theme |
| `confidence` | Clustering confidence score |
| `num_clusters` | Number of trend clusters |
| `paper_title` | Selected research paper |
| `paper_url` | Link to the paper |
| `paper_citations` | Citation count |
| `paper_source` | Which provider found the paper |
| `script_path` | Path to the generated script |
| `word_count` | Total words generated |
| `audio_path` | Path to audio file (if TTS enabled) |

## License

MIT — see [LICENSE](./LICENSE).

## Contact

**Saul Liu** — [@Saulliu00](https://github.com/Saulliu00) — saul.liu00@gmail.com

**Status:** v2.0 — Modular pipeline with pluggable providers, 59 unit tests passing.

*Last updated: April 9, 2026*
