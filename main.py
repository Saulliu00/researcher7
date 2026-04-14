#!/usr/bin/env python3
"""
Researcher7 - Main Pipeline
Trends → Correlation → Paper → Script
"""

# Inject OS certificate store BEFORE any network imports
# (fixes SSL errors behind corporate proxies)
import truststore
truststore.inject_into_ssl()

import csv
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_providers import create_data_provider
from correlation_providers import create_correlation_provider
from paper_providers import create_paper_provider
from script_generator import ScriptGenerator
from audio_generator import AudioGenerator
from llm_providers import create_provider
from translation_providers import create_translation_provider
from tts_providers import create_tts_provider


class Researcher7:
    def __init__(self, llm_provider, data_provider=None,
                 correlation_provider=None, paper_provider=None,
                 translator=None, tts_provider=None):
        """
        Initialize the Researcher7 pipeline

        Args:
            llm_provider: An LLMProvider instance (from llm_providers.create_provider)
            data_provider: A DataProvider instance (default: google_trends)
            correlation_provider: A CorrelationProvider instance (default: sklearn)
            paper_provider: A PaperProvider instance (default: semantic_scholar)
            translator: A TranslationProvider instance (optional, for --lang zh)
            tts_provider: A TTSProvider instance (optional, for --tts)
        """
        print("Initializing Researcher7...")
        print("="*60)

        self.data_provider = data_provider or create_data_provider("google_trends")
        self.correlation_provider = correlation_provider or create_correlation_provider("sklearn")
        self.paper_provider = paper_provider or create_paper_provider("semantic_scholar")
        self.script_generator = ScriptGenerator(provider=llm_provider)
        self.translator = translator
        self.audio_generator = AudioGenerator(provider=tts_provider) if tts_provider else None

        print("✓ All components initialized!")
        print("="*60 + "\n")
    
    def run(self, num_trends: int = 25, country: str = 'united_states',
            output_dir: str = 'outputs', lang: str = 'en') -> str:
        """
        Run the complete pipeline
        
        Args:
            num_trends: Number of trending terms to analyze
            country: Country for trends (default: united_states)
            output_dir: Directory to save output script
            lang: Output language ('en' or 'zh')
        
        Returns:
            Path to generated script file
        """
        print("🚀 Starting Researcher7 Pipeline\n")
        
        # Step 1: Fetch Trending Data
        print(f"📊 Step 1: Fetching Trending Data ({self.data_provider.name})")
        print("-" * 60)
        trends = self.data_provider.get_trending(
            country=country,
            limit=num_trends
        )
        print(f"✓ Retrieved {len(trends)} trending topics")
        print(f"  Top 3: {', '.join([t['term'] for t in trends[:3]])}\n")
        
        # Step 2: Analyze Correlations
        print(f"🔗 Step 2: Analyzing Correlations ({self.correlation_provider.name})")
        print("-" * 60)
        correlation_data = self.correlation_provider.analyze_trends(trends)
        unified_topic = correlation_data['unified_topic']
        print(f"✓ Unified Topic: {unified_topic['theme']}")
        print(f"  Confidence: {unified_topic['confidence']:.2%}")
        print(f"  Clusters: {correlation_data['num_clusters']}\n")
        
        # Free correlation provider memory (no longer needed)
        del self.correlation_provider
        import gc
        gc.collect()
        
        # Step 3: Find Academic Paper
        print(f"📚 Step 3: Finding Research Paper ({self.paper_provider.name})")
        print("-" * 60)
        paper = self.paper_provider.find_best_paper(
            topic=unified_topic['theme'],
            max_results=10
        )
        
        if not paper:
            print("❌ No suitable paper found, using fallback.")
            paper = {
                'title': f'Survey of {unified_topic["theme"]}',
                'authors': ['Various Authors'],
                'year': 2025,
                'abstract': f'A comprehensive survey examining recent developments in {unified_topic["theme"].lower()}.',
                'citations': 0,
                'url': '',
                'pdf_url': None,
                'venue': 'N/A',
                'source': 'fallback'
            }
        
        print(f"  Paper: {paper['title'][:60]}...")
        print(f"  Citations: {paper['citations']:,}\n")
        
        # Step 4: Generate Script
        print("✍️  Step 4: Generating Voice Script")
        print("-" * 60)
        script = self.script_generator.generate_script(
            trends=trends,
            correlation_data=correlation_data,
            paper=paper
        )
        
        # Step 5: Save Output
        print("\n💾 Step 5: Saving Output")
        print("-" * 60)
        output_path = self._save_script(
            script=script,
            topic=unified_topic['theme'],
            output_dir=output_dir
        )
        print(f"✓ Script saved: {output_path}")
        
        # Step 5b: Translate (if Chinese mode)
        translated_script = None
        translation_path = ''
        if lang == 'zh' and self.translator:
            print("\n🌐 Step 5b: Translating to Chinese")
            print("-" * 60)
            translated_script = self.translator.translate(script)
            translation_path = output_path.replace('.md', '_zh.md')
            with open(translation_path, 'w', encoding='utf-8') as f:
                f.write(translated_script)
            print(f"✓ Chinese script saved: {translation_path}")
        
        # Step 5c: Generate Audio (if TTS enabled)
        audio_path = ''
        if self.audio_generator:
            print("\n🔊 Step 5c: Generating Audio")
            print("-" * 60)
            tts_script = translated_script if translated_script else script
            audio_path = self.audio_generator.generate_audio(
                script=tts_script,
                topic=unified_topic['theme'],
                output_dir=output_dir,
            )
        
        # Step 6: Log run to CSV
        word_count = len(script.split())
        self._log_run(
            output_dir=output_dir,
            trends=trends,
            correlation_data=correlation_data,
            paper=paper,
            script_path=output_path,
            word_count=word_count,
            country=country,
            translation_path=translation_path,
            audio_path=audio_path,
        )
        
        # Summary
        print("\n" + "="*60)
        print("✅ Pipeline Complete!")
        print("="*60)
        print(f"Output: {output_path}")
        print(f"Topic: {unified_topic['theme']}")
        print(f"Paper: {paper['title']}")
        print(f"Words: ~{word_count:,}")
        if audio_path:
            print(f"Audio: {audio_path}")
        
        return output_path
    
    # ------------------------------------------------------------------
    # CSV run logger
    # ------------------------------------------------------------------
    _CSV_COLUMNS = [
        # Run info
        'timestamp',
        # Step 1: Data Fetch
        'step1_country',
        'step1_num_trends',
        'step1_top_trends',
        'step1_provider',
        # Step 2: Correlation
        'step2_topic',
        'step2_confidence',
        'step2_num_clusters',
        'step2_cluster_summary',
        'step2_provider',
        # Step 3: Paper Search
        'step3_paper_title',
        'step3_paper_authors',
        'step3_paper_year',
        'step3_paper_citations',
        'step3_paper_url',
        'step3_provider',
        # Step 4: Script Generation
        'step4_word_count',
        'step4_sections',
        'step4_provider',
        # Outputs
        'output_script_path',
        'output_translation_path',
        'output_audio_path',
    ]

    def _log_run(self, output_dir: str, trends, correlation_data, paper,
                 script_path: str, word_count: int, country: str,
                 translation_path: str = '', audio_path: str = '') -> None:
        """Append one row to the master run-log CSV."""
        csv_path = os.path.join(output_dir, 'run_log.csv')
        os.makedirs(output_dir, exist_ok=True)

        write_header = not os.path.exists(csv_path)

        unified = correlation_data['unified_topic']

        # Build a short cluster summary like "AI/ML(3) | Climate(3) | noise(2)"
        cluster_parts = []
        for c in correlation_data.get('clusters', []):
            label = c['label']
            top_term = c['terms'][0] if c['terms'] else '?'
            cluster_parts.append(f"{label}: {top_term} +{c['size'] - 1}")
        cluster_summary = ' | '.join(cluster_parts) if cluster_parts else 'none'

        # Paper authors (first 2 + et al.)
        authors = paper.get('authors', [])
        if len(authors) > 2:
            author_str = f"{authors[0]}, {authors[1]} et al."
        else:
            author_str = ', '.join(authors)

        row = {
            'timestamp':              datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Step 1
            'step1_country':          country,
            'step1_num_trends':       len(trends),
            'step1_top_trends':       ' | '.join(t['term'] for t in trends[:5]),
            'step1_provider':         self.data_provider.name if hasattr(self, 'data_provider') else '',
            # Step 2
            'step2_topic':            unified['theme'],
            'step2_confidence':       f"{unified['confidence']:.1%}",
            'step2_num_clusters':     correlation_data['num_clusters'],
            'step2_cluster_summary':  cluster_summary,
            'step2_provider':         'sklearn',
            # Step 3
            'step3_paper_title':      paper['title'],
            'step3_paper_authors':    author_str,
            'step3_paper_year':       paper.get('year', ''),
            'step3_paper_citations':  paper['citations'],
            'step3_paper_url':        paper.get('url', ''),
            'step3_provider':         paper.get('source', ''),
            # Step 4
            'step4_word_count':       word_count,
            'step4_sections':         10 if not self.script_generator.provider.supports_long_context else 1,
            'step4_provider':         f"{self.script_generator.provider.name} ({self.script_generator.provider.model})",
            # Outputs
            'output_script_path':     script_path,
            'output_translation_path': translation_path,
            'output_audio_path':      audio_path,
        }

        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self._CSV_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

        print(f"📋 Run logged to {csv_path}")

    def _save_script(self, script: str, topic: str, output_dir: str) -> str:
        """Save the generated script to a file"""
        scripts_dir = os.path.join(output_dir, 'scripts')
        os.makedirs(scripts_dir, exist_ok=True)
        
        # Create filename from date and topic
        date_str = datetime.now().strftime("%Y-%m-%d")
        topic_slug = topic.lower().replace(' ', '-').replace('/', '-')[:50]
        filename = f"{date_str}_{topic_slug}.md"
        
        filepath = os.path.join(scripts_dir, filename)
        
        # Write script
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script)
        
        return filepath


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments first
    import argparse
    parser = argparse.ArgumentParser(description='Researcher7 - Trends to Script Bot')
    parser.add_argument('--trends', type=int, default=25,
                       help='Number of trending topics to analyze (default: 25)')
    parser.add_argument('--country', type=str, default='united_states',
                       help='Country for trends (default: united_states)')
    parser.add_argument('--output', type=str, default='outputs',
                       help='Output directory (default: outputs)')
    parser.add_argument('--provider', type=str, choices=['ollama', 'anthropic'],
                       help='Override LLM provider from .env')
    parser.add_argument('--data-source', type=str, dest='data_source',
                       help='Data-fetching provider (default from .env or google_trends)')
    parser.add_argument('--correlator', type=str,
                       help='Correlation provider (default from .env or sklearn)')
    parser.add_argument('--paper-source', type=str, dest='paper_source',
                       help='Paper-finding provider (default from .env or semantic_scholar)')
    parser.add_argument('--lang', type=str, default='en', choices=['en', 'zh'],
                       help='Output language (default: en). zh activates translation.')
    parser.add_argument('--translator', type=str,
                       help='Translation provider (default from .env or marianmt)')
    parser.add_argument('--tts', type=str,
                       help='Enable TTS audio generation with the given provider')
    
    args = parser.parse_args()
    
    # Determine provider (CLI overrides .env)
    llm_provider_name = (args.provider or os.getenv("LLM_PROVIDER", "ollama")).lower()
    semantic_scholar_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    # -- Data provider --
    data_provider_name = (
        args.data_source or os.getenv("DATA_PROVIDER", "google_trends")
    ).lower()
    data_provider = create_data_provider(data_provider_name)
    print(f"📊 Data Provider: {data_provider.name}")

    # -- Correlation provider --
    corr_provider_name = (
        args.correlator or os.getenv("CORRELATION_PROVIDER", "sklearn")
    ).lower()
    correlation_provider = create_correlation_provider(corr_provider_name)
    print(f"🔗 Correlation Provider: {correlation_provider.name}")

    # -- Paper provider --
    paper_provider_name = (
        args.paper_source or os.getenv("PAPER_PROVIDER", "semantic_scholar")
    ).lower()
    paper_kwargs = {}
    if paper_provider_name == "semantic_scholar" and semantic_scholar_key:
        paper_kwargs['api_key'] = semantic_scholar_key
    paper_provider = create_paper_provider(paper_provider_name, **paper_kwargs)
    print(f"📚 Paper Provider: {paper_provider.name}")

    # -- LLM provider --
    if llm_provider_name == "ollama":
        llm = create_provider(
            "ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        )
        print(f"🤖 LLM Provider: Ollama ({llm.model})")
        
    elif llm_provider_name == "anthropic":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            print("❌ Error: ANTHROPIC_API_KEY not found in environment")
            print("Please add to .env file:")
            print("  ANTHROPIC_API_KEY=your_key_here")
            sys.exit(1)
        llm = create_provider(
            "anthropic",
            api_key=anthropic_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        )
        print(f"🤖 LLM Provider: Anthropic ({llm.model})")
        
    else:
        print(f"❌ Error: Unknown LLM_PROVIDER: {llm_provider_name}")
        print("Valid options: 'ollama' or 'anthropic'")
        sys.exit(1)
    
    # Build translator (only when --lang zh)
    translator = None
    if args.lang == 'zh':
        translator_name = (
            args.translator
            or os.getenv("TRANSLATION_PROVIDER", "marianmt")
        ).lower()
        translator = create_translation_provider(
            translator_name,
            source='en',
            target='zh',
        )
        print(f"🌐 Translator: {translator.name} ({translator.source_lang}→{translator.target_lang})")
    
    # Build TTS provider (only when --tts is set)
    tts = None
    tts_name = (args.tts or os.getenv("TTS_PROVIDER", "")).lower()
    if tts_name:
        tts = create_tts_provider(tts_name)
        print(f"🔊 TTS Provider: {tts.name}")
    
    # Run pipeline
    try:
        researcher = Researcher7(
            llm_provider=llm,
            data_provider=data_provider,
            correlation_provider=correlation_provider,
            paper_provider=paper_provider,
            translator=translator,
            tts_provider=tts,
        )
        
        output_path = researcher.run(
            num_trends=args.trends,
            country=args.country,
            output_dir=args.output,
            lang=args.lang,
        )
        
        print(f"\n✨ Success! Script ready at: {output_path}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
