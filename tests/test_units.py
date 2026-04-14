#!/usr/bin/env python3
"""
Unit tests for Researcher7 — tests each pipeline step independently.
No LLM required. Uses mocks for external APIs and network calls.

Run:  python -m pytest tests/test_units.py -v
  or: .venv/Scripts/python.exe -m pytest tests/test_units.py -v
"""
import csv
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# -- path setup (same as main.py) ------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ===========================================================================
# Shared fixtures
# ===========================================================================

@pytest.fixture
def demo_trends():
    """Minimal trend list that every step can consume."""
    return [
        {'rank': 1, 'term': 'artificial intelligence', 'country': 'US'},
        {'rank': 2, 'term': 'climate change', 'country': 'US'},
        {'rank': 3, 'term': 'quantum computing', 'country': 'US'},
        {'rank': 4, 'term': 'renewable energy', 'country': 'US'},
        {'rank': 5, 'term': 'space exploration', 'country': 'US'},
        {'rank': 6, 'term': 'machine learning', 'country': 'US'},
        {'rank': 7, 'term': 'carbon capture', 'country': 'US'},
        {'rank': 8, 'term': 'neural networks', 'country': 'US'},
    ]


@pytest.fixture
def demo_correlation_data():
    """Pre-built correlation result for downstream steps."""
    return {
        'clusters': [
            {
                'label': 'cluster_1',
                'terms': ['artificial intelligence', 'machine learning', 'neural networks'],
                'size': 3,
                'confidence': 0.85,
            },
            {
                'label': 'cluster_2',
                'terms': ['climate change', 'renewable energy', 'carbon capture'],
                'size': 3,
                'confidence': 0.78,
            },
            {
                'label': 'noise',
                'terms': ['quantum computing', 'space exploration'],
                'size': 2,
                'confidence': 0.0,
            },
        ],
        'unified_topic': {
            'theme': 'Technology and Environment Trends',
            'key_terms': ['artificial intelligence', 'climate change'],
            'description': 'Connecting 2 major trend clusters',
            'confidence': 0.82,
        },
        'total_terms': 8,
        'num_clusters': 2,
    }


@pytest.fixture
def demo_paper():
    """Pre-built paper dict for downstream steps."""
    return {
        'title': 'Computational Sustainability: Computing for a Better World',
        'authors': ['Carla P. Gomes', 'Thomas Dietterich', 'Christopher Barrett'],
        'year': 2019,
        'abstract': 'Computational sustainability is a new field that aims to apply '
                    'techniques from computer science, information science, and related '
                    'disciplines to help solve environmental and societal challenges.',
        'citations': 342,
        'url': 'https://arxiv.org/abs/1906.02748',
        'pdf_url': 'https://arxiv.org/pdf/1906.02748',
        'venue': 'Communications of the ACM',
        'source': 'Semantic Scholar',
    }


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output directory, cleaned up automatically."""
    return str(tmp_path / 'outputs')


# ===========================================================================
# 1. DATA PROVIDERS
# ===========================================================================

class TestDataProviderFactory:
    """Test the data provider factory and registry."""

    def test_create_google_trends(self):
        from data_providers import create_data_provider
        provider = create_data_provider('google_trends')
        assert provider.name == 'Google Trends RSS'

    def test_create_unknown_raises(self):
        from data_providers import create_data_provider
        with pytest.raises(ValueError, match="Unknown data provider"):
            create_data_provider('nonexistent')

    def test_list_providers(self):
        from data_providers import list_data_providers
        providers = list_data_providers()
        assert 'google_trends' in providers

    def test_case_insensitive(self):
        from data_providers import create_data_provider
        provider = create_data_provider('Google_Trends')
        assert provider.name == 'Google Trends RSS'


class TestGoogleTrendsProvider:
    """Test the Google Trends RSS provider (network mocked)."""

    SAMPLE_RSS = '''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss">
      <channel>
        <item>
          <title>artificial intelligence</title>
          <ht:approx_traffic>500,000+</ht:approx_traffic>
          <pubDate>Wed, 09 Apr 2026 12:00:00 +0000</pubDate>
          <ht:news_item>
            <ht:news_item_title>AI Breakthrough</ht:news_item_title>
            <ht:news_item_source>TechCrunch</ht:news_item_source>
            <ht:news_item_url>https://example.com/ai</ht:news_item_url>
          </ht:news_item>
        </item>
        <item>
          <title>climate summit</title>
          <ht:approx_traffic>200,000+</ht:approx_traffic>
          <pubDate>Wed, 09 Apr 2026 11:00:00 +0000</pubDate>
        </item>
      </channel>
    </rss>'''

    def test_parse_rss_feed(self):
        from data_providers.google_trends_provider import GoogleTrendsProvider
        provider = GoogleTrendsProvider()

        mock_resp = MagicMock()
        mock_resp.text = self.SAMPLE_RSS
        mock_resp.raise_for_status = MagicMock()

        with patch.object(provider.session, 'get', return_value=mock_resp):
            trends = provider.get_trending(country='united_states', limit=25)

        assert len(trends) == 2
        assert trends[0]['term'] == 'artificial intelligence'
        assert trends[0]['rank'] == 1
        assert trends[0]['approx_traffic'] == '500,000+'
        assert len(trends[0]['news']) == 1
        assert trends[0]['news'][0]['source'] == 'TechCrunch'
        assert trends[1]['term'] == 'climate summit'
        assert trends[1]['rank'] == 2

    def test_limit_respected(self):
        from data_providers.google_trends_provider import GoogleTrendsProvider
        provider = GoogleTrendsProvider()

        mock_resp = MagicMock()
        mock_resp.text = self.SAMPLE_RSS
        mock_resp.raise_for_status = MagicMock()

        with patch.object(provider.session, 'get', return_value=mock_resp):
            trends = provider.get_trending(limit=1)

        assert len(trends) == 1

    def test_fallback_on_network_error(self):
        from data_providers.google_trends_provider import GoogleTrendsProvider
        provider = GoogleTrendsProvider()

        with patch.object(provider.session, 'get', side_effect=Exception("Network down")):
            trends = provider.get_trending(limit=5)

        # Should return demo data
        assert len(trends) == 5
        assert trends[0]['country'] == 'demo'

    def test_fallback_on_empty_feed(self):
        from data_providers.google_trends_provider import GoogleTrendsProvider
        provider = GoogleTrendsProvider()

        empty_rss = '''<?xml version="1.0"?>
        <rss version="2.0"><channel></channel></rss>'''
        mock_resp = MagicMock()
        mock_resp.text = empty_rss
        mock_resp.raise_for_status = MagicMock()

        with patch.object(provider.session, 'get', return_value=mock_resp):
            trends = provider.get_trending(limit=5)

        assert len(trends) == 5
        assert trends[0]['country'] == 'demo'

    def test_country_code_mapping(self):
        from data_providers.google_trends_provider import GoogleTrendsProvider, _COUNTRY_CODES
        provider = GoogleTrendsProvider()

        mock_resp = MagicMock()
        mock_resp.text = self.SAMPLE_RSS
        mock_resp.raise_for_status = MagicMock()

        with patch.object(provider.session, 'get', return_value=mock_resp) as mock_get:
            provider.get_trending(country='united_kingdom')
            called_url = mock_get.call_args[0][0]
            assert 'geo=GB' in called_url

    def test_unknown_country_passes_uppercase(self):
        from data_providers.google_trends_provider import GoogleTrendsProvider
        provider = GoogleTrendsProvider()

        mock_resp = MagicMock()
        mock_resp.text = self.SAMPLE_RSS
        mock_resp.raise_for_status = MagicMock()

        with patch.object(provider.session, 'get', return_value=mock_resp) as mock_get:
            provider.get_trending(country='es')
            called_url = mock_get.call_args[0][0]
            assert 'geo=ES' in called_url


# ===========================================================================
# 2. CORRELATION PROVIDERS
# ===========================================================================

class TestCorrelationProviderFactory:
    def test_create_sklearn(self):
        from correlation_providers import create_correlation_provider
        provider = create_correlation_provider('sklearn')
        assert 'sklearn' in provider.name.lower() or 'TF-IDF' in provider.name

    def test_create_unknown_raises(self):
        from correlation_providers import create_correlation_provider
        with pytest.raises(ValueError, match="Unknown correlation provider"):
            create_correlation_provider('nonexistent')

    def test_list_providers(self):
        from correlation_providers import list_correlation_providers
        assert 'sklearn' in list_correlation_providers()


class TestSklearnCorrelationProvider:
    """Test the sklearn (TF-IDF + DBSCAN) correlation provider."""

    def test_analyze_returns_required_keys(self, demo_trends):
        from correlation_providers import create_correlation_provider
        engine = create_correlation_provider('sklearn')
        result = engine.analyze_trends(demo_trends)

        assert 'clusters' in result
        assert 'unified_topic' in result
        assert 'total_terms' in result
        assert 'num_clusters' in result
        assert result['total_terms'] == len(demo_trends)

    def test_unified_topic_has_required_fields(self, demo_trends):
        from correlation_providers import create_correlation_provider
        engine = create_correlation_provider('sklearn')
        result = engine.analyze_trends(demo_trends)

        topic = result['unified_topic']
        assert 'theme' in topic
        assert 'confidence' in topic
        assert isinstance(topic['theme'], str)
        assert 0.0 <= topic['confidence'] <= 1.0

    def test_clusters_are_well_formed(self, demo_trends):
        from correlation_providers import create_correlation_provider
        engine = create_correlation_provider('sklearn')
        result = engine.analyze_trends(demo_trends)

        for cluster in result['clusters']:
            assert 'label' in cluster
            assert 'terms' in cluster
            assert 'size' in cluster
            assert 'confidence' in cluster
            assert len(cluster['terms']) == cluster['size']

    def test_num_clusters_excludes_noise(self, demo_trends):
        from correlation_providers import create_correlation_provider
        engine = create_correlation_provider('sklearn')
        result = engine.analyze_trends(demo_trends)

        non_noise = [c for c in result['clusters'] if c['label'] != 'noise']
        assert result['num_clusters'] == len(non_noise)

    def test_single_term_does_not_crash(self):
        from correlation_providers import create_correlation_provider
        engine = create_correlation_provider('sklearn')
        result = engine.analyze_trends([{'term': 'hello', 'rank': 1}])
        assert result['total_terms'] == 1

    def test_all_identical_terms(self):
        from correlation_providers import create_correlation_provider
        engine = create_correlation_provider('sklearn')
        trends = [{'term': 'same topic', 'rank': i} for i in range(5)]
        result = engine.analyze_trends(trends)
        assert result['total_terms'] == 5

    def test_theme_generation_tech(self):
        from correlation_providers.sklearn_provider import SklearnCorrelationProvider
        theme = SklearnCorrelationProvider._create_theme_from_terms(
            ['artificial intelligence', 'quantum computing']
        )
        assert 'Technology' in theme

    def test_theme_generation_environment(self):
        from correlation_providers.sklearn_provider import SklearnCorrelationProvider
        theme = SklearnCorrelationProvider._create_theme_from_terms(
            ['climate change', 'renewable energy', 'ocean conservation']
        )
        assert 'Environment' in theme

    def test_theme_generation_fallback(self):
        from correlation_providers.sklearn_provider import SklearnCorrelationProvider
        theme = SklearnCorrelationProvider._create_theme_from_terms(
            ['foo bar', 'baz qux']
        )
        assert theme == 'Emerging Global Trends'


# ===========================================================================
# 3. PAPER PROVIDERS
# ===========================================================================

class TestPaperProviderFactory:
    def test_create_semantic_scholar(self):
        with patch('semanticscholar.SemanticScholar'):
            from paper_providers import create_paper_provider
            provider = create_paper_provider('semantic_scholar')
            assert provider.name == 'Semantic Scholar'

    def test_create_arxiv(self):
        from paper_providers import create_paper_provider
        provider = create_paper_provider('arxiv')
        assert provider.name == 'arXiv'

    def test_create_unknown_raises(self):
        from paper_providers import create_paper_provider
        with pytest.raises(ValueError, match="Unknown paper provider"):
            create_paper_provider('nonexistent')

    def test_list_providers(self):
        from paper_providers import list_paper_providers
        providers = list_paper_providers()
        assert 'semantic_scholar' in providers
        assert 'arxiv' in providers


class TestSemanticScholarProvider:
    """Test Semantic Scholar provider with mocked API."""

    def _make_mock_paper(self, title="Great Paper", abstract="A" * 200,
                         citations=100):
        paper = MagicMock()
        paper.title = title
        paper.abstract = abstract
        paper.citationCount = citations
        paper.year = 2023
        paper.url = "https://example.com/paper"
        paper.openAccessPdf = None
        paper.publicationVenue = None
        author = MagicMock()
        author.name = "Alice"
        paper.authors = [author]
        return paper

    def test_returns_best_by_citations(self):
        from paper_providers.semantic_scholar_provider import SemanticScholarProvider

        with patch('semanticscholar.SemanticScholar') as MockS2:
            mock_s2 = MockS2.return_value
            mock_s2.search_paper.return_value = [
                self._make_mock_paper("Paper A", citations=50),
                self._make_mock_paper("Paper B", citations=200),
            ]
            provider = SemanticScholarProvider()
            paper = provider.find_best_paper("test topic")

        assert paper is not None
        assert paper['title'] == 'Paper B'
        assert paper['citations'] == 200

    def test_filters_short_abstracts(self):
        from paper_providers.semantic_scholar_provider import SemanticScholarProvider

        with patch('semanticscholar.SemanticScholar') as MockS2:
            mock_s2 = MockS2.return_value
            short_paper = self._make_mock_paper(abstract="Too short")
            mock_s2.search_paper.return_value = [short_paper]
            provider = SemanticScholarProvider()
            paper = provider.find_best_paper("test")

        assert paper is None

    def test_handles_api_error(self):
        from paper_providers.semantic_scholar_provider import SemanticScholarProvider

        with patch('semanticscholar.SemanticScholar') as MockS2:
            mock_s2 = MockS2.return_value
            mock_s2.search_paper.side_effect = ConnectionError("API down")
            provider = SemanticScholarProvider()
            paper = provider.find_best_paper("test")

        assert paper is None

    def test_handles_empty_results(self):
        from paper_providers.semantic_scholar_provider import SemanticScholarProvider

        with patch('semanticscholar.SemanticScholar') as MockS2:
            mock_s2 = MockS2.return_value
            mock_s2.search_paper.return_value = []
            provider = SemanticScholarProvider()
            paper = provider.find_best_paper("test")

        assert paper is None


class TestArxivProvider:
    """Test arXiv provider with mocked API."""

    def test_returns_first_result(self):
        from paper_providers.arxiv_provider import ArxivProvider

        mock_result = MagicMock()
        mock_result.title = "Arxiv Paper"
        mock_result.summary = "A nice long abstract about stuff."
        mock_result.published.year = 2024
        mock_result.entry_id = "https://arxiv.org/abs/2401.00001"
        mock_result.pdf_url = "https://arxiv.org/pdf/2401.00001"
        author = MagicMock()
        author.name = "Bob"
        mock_result.authors = [author]

        mock_arxiv_mod = MagicMock()
        mock_arxiv_mod.Client.return_value.results.return_value = [mock_result]
        mock_arxiv_mod.Search = MagicMock()
        mock_arxiv_mod.SortCriterion.Relevance = 'relevance'

        with patch.dict('sys.modules', {'arxiv': mock_arxiv_mod}):
            provider = ArxivProvider.__new__(ArxivProvider)
            provider._arxiv = mock_arxiv_mod
            provider.client = mock_arxiv_mod.Client.return_value

            paper = provider.find_best_paper("test", max_results=5)

        assert paper is not None
        assert paper['title'] == 'Arxiv Paper'
        assert paper['source'] == 'arXiv'

    def test_handles_error(self):
        from paper_providers.arxiv_provider import ArxivProvider

        mock_arxiv_mod = MagicMock()
        mock_arxiv_mod.Client.return_value.results.side_effect = Exception("timeout")
        mock_arxiv_mod.Search = MagicMock()
        mock_arxiv_mod.SortCriterion.Relevance = 'relevance'

        with patch.dict('sys.modules', {'arxiv': mock_arxiv_mod}):
            provider = ArxivProvider.__new__(ArxivProvider)
            provider._arxiv = mock_arxiv_mod
            provider.client = mock_arxiv_mod.Client.return_value

            paper = provider.find_best_paper("test")

        assert paper is None


class TestPaperProviderBase:
    """Test format_paper_summary on the base class."""

    def test_format_paper_summary(self, demo_paper):
        from paper_providers.base import PaperProvider

        # Use a concrete subclass via duck-typing
        class DummyProvider(PaperProvider):
            @property
            def name(self): return "Dummy"
            def find_best_paper(self, topic, max_results=10): return None

        provider = DummyProvider()
        summary = provider.format_paper_summary(demo_paper)
        assert 'Computational Sustainability' in summary
        assert 'Carla P. Gomes' in summary
        assert '342' in summary

    def test_format_paper_many_authors(self):
        from paper_providers.base import PaperProvider

        class DummyProvider(PaperProvider):
            @property
            def name(self): return "Dummy"
            def find_best_paper(self, topic, max_results=10): return None

        paper = {
            'title': 'Test',
            'authors': ['A', 'B', 'C', 'D', 'E'],
            'year': 2020,
            'abstract': 'Test abstract.',
            'citations': 10,
            'venue': None,
            'source': 'test',
            'url': 'https://example.com',
            'pdf_url': None,
        }
        provider = DummyProvider()
        summary = provider.format_paper_summary(paper)
        assert 'et al.' in summary
        assert '5 authors' in summary


# ===========================================================================
# 4. LLM PROVIDERS (no real LLM — mock only)
# ===========================================================================

class TestLLMProviderFactory:
    def test_create_ollama(self):
        from llm_providers import create_provider
        provider = create_provider('ollama', base_url='http://localhost:11434', model='test:7b')
        assert provider.name == 'Ollama'
        assert provider.model == 'test:7b'
        assert provider.supports_long_context is False

    def test_create_anthropic(self):
        from llm_providers import create_provider
        with patch('anthropic.Anthropic'):
            provider = create_provider('anthropic', api_key='sk-test', model='claude-test')
        assert provider.name == 'Anthropic'
        assert provider.model == 'claude-test'
        assert provider.supports_long_context is True

    def test_create_unknown_raises(self):
        from llm_providers import create_provider
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_provider('nonexistent')

    def test_list_providers(self):
        from llm_providers import list_providers
        providers = list_providers()
        assert 'ollama' in providers
        assert 'anthropic' in providers


class TestOllamaProvider:
    """Test Ollama provider with mocked HTTP."""

    def test_generate_success(self):
        from llm_providers.ollama_provider import OllamaProvider
        provider = OllamaProvider(base_url='http://localhost:11434', model='test:7b')

        mock_resp = MagicMock()
        mock_resp.json.return_value = {'response': 'Hello world'}
        mock_resp.raise_for_status = MagicMock()

        with patch('llm_providers.ollama_provider.requests.post', return_value=mock_resp):
            result = provider.generate("Say hello")

        assert result == 'Hello world'

    def test_generate_network_error(self):
        from llm_providers.ollama_provider import OllamaProvider
        import requests
        provider = OllamaProvider()

        with patch('llm_providers.ollama_provider.requests.post',
                   side_effect=requests.exceptions.ConnectionError("refused")):
            with pytest.raises(requests.exceptions.ConnectionError):
                provider.generate("test")


# ===========================================================================
# 5. SCRIPT GENERATOR (with mock LLM)
# ===========================================================================

class TestScriptGenerator:
    """Test script generator using a mock LLM provider."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.name = 'MockLLM'
        llm.model = 'mock-7b'
        llm.supports_long_context = False
        llm.generate.return_value = "This is a generated section with enough words. " * 30
        return llm

    @pytest.fixture
    def mock_llm_singlepass(self):
        llm = MagicMock()
        llm.name = 'MockClaude'
        llm.model = 'mock-claude'
        llm.supports_long_context = True
        llm.generate.return_value = "This is a full single-pass script. " * 200
        return llm

    def test_multipass_generates_10_sections(self, mock_llm, demo_trends,
                                              demo_correlation_data, demo_paper):
        from script_generator import ScriptGenerator
        gen = ScriptGenerator(provider=mock_llm)
        script = gen.generate_script(demo_trends, demo_correlation_data, demo_paper)

        # Should call LLM 10 times (one per section)
        assert mock_llm.generate.call_count == 10
        assert len(script) > 0

    def test_singlepass_calls_llm_once(self, mock_llm_singlepass, demo_trends,
                                        demo_correlation_data, demo_paper):
        from script_generator import ScriptGenerator
        gen = ScriptGenerator(provider=mock_llm_singlepass)
        script = gen.generate_script(demo_trends, demo_correlation_data, demo_paper)

        assert mock_llm_singlepass.generate.call_count == 1
        assert len(script) > 0

    def test_header_contains_metadata(self, mock_llm, demo_trends,
                                       demo_correlation_data, demo_paper):
        from script_generator import ScriptGenerator
        gen = ScriptGenerator(provider=mock_llm)
        script = gen.generate_script(demo_trends, demo_correlation_data, demo_paper)

        assert 'Researcher7 Voice Script' in script
        assert 'MockLLM' in script
        assert 'Technology and Environment Trends' in script
        assert 'Computational Sustainability' in script

    def test_autosave_creates_files(self, mock_llm, demo_trends,
                                     demo_correlation_data, demo_paper, tmp_path):
        from script_generator import ScriptGenerator
        gen = ScriptGenerator(provider=mock_llm)
        gen.autosave_dir = tmp_path / 'autosave'
        gen.autosave_dir.mkdir()

        gen.generate_script(demo_trends, demo_correlation_data, demo_paper)

        autosaved = list(gen.autosave_dir.glob('section_*.md'))
        assert len(autosaved) == 10

        progress = gen.autosave_dir / 'progress.json'
        assert progress.exists()
        data = json.loads(progress.read_text())
        assert data['completed_sections'] == 10

    def test_handles_empty_clusters(self, mock_llm, demo_trends, demo_paper):
        from script_generator import ScriptGenerator
        gen = ScriptGenerator(provider=mock_llm)

        corr_data = {
            'clusters': [],
            'unified_topic': {
                'theme': 'General Trends',
                'key_terms': [],
                'confidence': 0.5,
            },
            'total_terms': 3,
            'num_clusters': 0,
        }
        # Should not crash
        script = gen.generate_script(demo_trends, corr_data, demo_paper)
        assert len(script) > 0


# ===========================================================================
# 6. AUDIO GENERATOR (markdown stripping, no real TTS)
# ===========================================================================

class TestAudioGeneratorMarkdownStripping:
    """Test the _strip_markdown static method."""

    def test_strips_metadata_header(self):
        from audio_generator import AudioGenerator
        text = """# Researcher7 Voice Script

**Generated:** 2026-04-09 10:00:00
**Host:** Saul
**LLM Provider:** Ollama

---

## Trending Topics Captured

**Top 15 Google Trending Searches:**
1. AI
2. Climate

---

## Research Source

**Some Paper**
Source: Semantic Scholar
URL: https://example.com

---

This is the actual script content that should survive.

Here is more content."""

        result = AudioGenerator._strip_markdown(text)
        assert 'Generated:' not in result
        assert 'Host:' not in result
        assert 'LLM Provider:' not in result
        assert 'Trending Topics' not in result
        assert 'Research Source' not in result
        assert 'actual script content' in result
        assert 'more content' in result

    def test_strips_markdown_formatting(self):
        from audio_generator import AudioGenerator
        text = """Header block

---

## Section Title

This is **bold** and *italic* text with `code` and [link](http://example.com)."""

        result = AudioGenerator._strip_markdown(text)
        assert '**' not in result
        assert '*' not in result or 'italic' in result
        assert '`' not in result
        assert '[link]' not in result
        assert 'bold' in result
        assert 'italic' in result
        assert 'link' in result

    def test_empty_text(self):
        from audio_generator import AudioGenerator
        result = AudioGenerator._strip_markdown("")
        assert result == ""

    def test_audio_generator_calls_tts(self, tmp_output_dir):
        from audio_generator import AudioGenerator

        mock_tts = MagicMock()
        mock_tts.name = "MockTTS"
        mock_tts.synthesize.return_value = "output.wav"

        gen = AudioGenerator(provider=mock_tts)
        gen.generate_audio(
            script="Header\n\n---\n\nHello world.",
            topic="Test Topic",
            output_dir=tmp_output_dir,
        )

        mock_tts.synthesize.assert_called_once()
        call_args = mock_tts.synthesize.call_args
        assert 'Hello world' in call_args[0][0]


# ===========================================================================
# 7. TRANSLATION PROVIDER FACTORY
# ===========================================================================

class TestTranslationProviderFactory:
    def test_create_marianmt(self):
        from translation_providers import create_translation_provider
        provider = create_translation_provider('marianmt', source='en', target='zh')
        assert provider.name == 'MarianMT'
        assert provider.source_lang == 'en'
        assert provider.target_lang == 'zh'

    def test_create_unknown_raises(self):
        from translation_providers import create_translation_provider
        with pytest.raises(ValueError, match="Unknown translation provider"):
            create_translation_provider('nonexistent')

    def test_unsupported_language_pair(self):
        from translation_providers import create_translation_provider
        with pytest.raises(ValueError, match="No MarianMT model"):
            create_translation_provider('marianmt', source='en', target='xx')


# ===========================================================================
# 8. TTS PROVIDER FACTORY
# ===========================================================================

class TestTTSProviderFactory:
    def test_create_unknown_raises(self):
        from tts_providers import create_tts_provider
        with pytest.raises(ValueError, match="Unknown TTS provider"):
            create_tts_provider('nonexistent')

    def test_piper_requires_exe(self):
        from tts_providers import create_tts_provider
        with patch('shutil.which', return_value=None):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(FileNotFoundError, match="Piper executable"):
                    create_tts_provider('piper')


# ===========================================================================
# 9. MAIN PIPELINE (Researcher7 class, LLM mocked)
# ===========================================================================

class TestResearcher7Pipeline:
    """Integration test for the full pipeline with all externals mocked."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.name = 'MockLLM'
        llm.model = 'mock-7b'
        llm.supports_long_context = False
        llm.generate.return_value = "Generated content for this section. " * 30
        return llm

    def test_full_pipeline_no_crash(self, mock_llm, tmp_output_dir):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from main import Researcher7
        from data_providers.google_trends_provider import GoogleTrendsProvider

        # Mock the data provider to avoid network
        data_prov = GoogleTrendsProvider()
        with patch.object(data_prov.session, 'get', side_effect=Exception("no network")):
            researcher = Researcher7(
                llm_provider=mock_llm,
                data_provider=data_prov,
            )
            output = researcher.run(
                num_trends=8,
                country='united_states',
                output_dir=tmp_output_dir,
            )

        assert output.endswith('.md')
        assert os.path.exists(output)

        # CSV log should exist
        csv_path = os.path.join(tmp_output_dir, 'run_log.csv')
        assert os.path.exists(csv_path)
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['step1_country'] == 'united_states'

    def test_pipeline_with_custom_providers(self, mock_llm, demo_trends,
                                             demo_correlation_data, demo_paper,
                                             tmp_output_dir):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from main import Researcher7

        mock_data = MagicMock()
        mock_data.name = "MockData"
        mock_data.get_trending.return_value = demo_trends

        mock_corr = MagicMock()
        mock_corr.name = "MockCorr"
        mock_corr.analyze_trends.return_value = demo_correlation_data

        mock_paper = MagicMock()
        mock_paper.name = "MockPaper"
        mock_paper.find_best_paper.return_value = demo_paper

        researcher = Researcher7(
            llm_provider=mock_llm,
            data_provider=mock_data,
            correlation_provider=mock_corr,
            paper_provider=mock_paper,
        )
        output = researcher.run(output_dir=tmp_output_dir)

        assert os.path.exists(output)
        mock_data.get_trending.assert_called_once()
        mock_corr.analyze_trends.assert_called_once()
        mock_paper.find_best_paper.assert_called_once()

    def test_fallback_paper_when_none_found(self, mock_llm, tmp_output_dir):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from main import Researcher7

        mock_data = MagicMock()
        mock_data.name = "MockData"
        mock_data.get_trending.return_value = [
            {'rank': 1, 'term': 'test1'},
            {'rank': 2, 'term': 'test2'},
            {'rank': 3, 'term': 'test3'},
        ]

        mock_corr = MagicMock()
        mock_corr.name = "MockCorr"
        mock_corr.analyze_trends.return_value = {
            'clusters': [],
            'unified_topic': {'theme': 'Test', 'confidence': 0.5, 'key_terms': []},
            'total_terms': 3,
            'num_clusters': 0,
        }

        mock_paper = MagicMock()
        mock_paper.name = "MockPaper"
        mock_paper.find_best_paper.return_value = None  # No paper found

        researcher = Researcher7(
            llm_provider=mock_llm,
            data_provider=mock_data,
            correlation_provider=mock_corr,
            paper_provider=mock_paper,
        )
        output = researcher.run(output_dir=tmp_output_dir)

        # Should succeed with fallback paper
        assert os.path.exists(output)
        content = Path(output).read_text(encoding='utf-8')
        assert 'Survey of Test' in content


# ===========================================================================
# 10. CSV LOGGER
# ===========================================================================

class TestCSVLogger:
    def _make_researcher_stub(self):
        """Create a minimal Researcher7 stub with attributes needed by _log_run."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from main import Researcher7

        r = object.__new__(Researcher7)
        # _log_run reads these for provider names
        r.data_provider = MagicMock()
        r.data_provider.name = 'Google Trends RSS'
        mock_llm = MagicMock()
        mock_llm.name = 'MockLLM'
        mock_llm.model = 'mock-7b'
        mock_llm.supports_long_context = False
        r.script_generator = MagicMock()
        r.script_generator.provider = mock_llm
        return r

    def test_csv_creates_header_on_first_write(self, tmp_output_dir,
                                                demo_trends,
                                                demo_correlation_data,
                                                demo_paper):
        r = self._make_researcher_stub()
        r._log_run(
            output_dir=tmp_output_dir,
            trends=demo_trends,
            correlation_data=demo_correlation_data,
            paper=demo_paper,
            script_path='test.md',
            word_count=1000,
            country='united_states',
        )

        csv_path = os.path.join(tmp_output_dir, 'run_log.csv')
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]['step2_topic'] == 'Technology and Environment Trends'
        assert rows[0]['step4_word_count'] == '1000'
        assert rows[0]['step1_country'] == 'united_states'
        assert rows[0]['step3_paper_title'] == 'Computational Sustainability: Computing for a Better World'
        assert 'Carla P. Gomes' in rows[0]['step3_paper_authors']
        assert rows[0]['output_script_path'] == 'test.md'

    def test_csv_appends_without_duplicate_header(self, tmp_output_dir,
                                                    demo_trends,
                                                    demo_correlation_data,
                                                    demo_paper):
        r = self._make_researcher_stub()
        for _ in range(3):
            r._log_run(
                output_dir=tmp_output_dir,
                trends=demo_trends,
                correlation_data=demo_correlation_data,
                paper=demo_paper,
                script_path='test.md',
                word_count=1000,
                country='united_states',
            )

        csv_path = os.path.join(tmp_output_dir, 'run_log.csv')
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 1 header + 3 data rows
        assert len(lines) == 4
