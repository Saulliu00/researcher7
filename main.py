#!/usr/bin/env python3
"""
Researcher7 - Main Pipeline
Trends → Correlation → Paper → Script
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from trend_scraper import TrendScraper
from correlation_engine import CorrelationEngine
from paper_finder import PaperFinder
from script_generator import ScriptGenerator


class Researcher7:
    def __init__(self, llm_provider: str = "ollama", llm_config: dict = None, 
                 semantic_scholar_key: str = None):
        """
        Initialize the Researcher7 pipeline
        
        Args:
            llm_provider: LLM provider ("ollama" or "anthropic")
            llm_config: Provider-specific configuration dict
            semantic_scholar_key: Semantic Scholar API key (optional)
        """
        print("Initializing Researcher7...")
        print("="*60)
        
        self.trend_scraper = TrendScraper()
        self.correlation_engine = CorrelationEngine()
        self.paper_finder = PaperFinder(api_key=semantic_scholar_key)
        self.script_generator = ScriptGenerator(provider=llm_provider, **(llm_config or {}))
        
        print("✓ All components initialized!")
        print("="*60 + "\n")
    
    def run(self, num_trends: int = 25, country: str = 'united_states',
            output_dir: str = 'outputs') -> str:
        """
        Run the complete pipeline
        
        Args:
            num_trends: Number of trending terms to analyze
            country: Country for trends (default: united_states)
            output_dir: Directory to save output script
        
        Returns:
            Path to generated script file
        """
        print("🚀 Starting Researcher7 Pipeline\n")
        
        # Step 1: Scrape Trends
        print("📊 Step 1: Scraping Trending Topics")
        print("-" * 60)
        trends = self.trend_scraper.get_trending_searches(
            country=country,
            limit=num_trends
        )
        print(f"✓ Retrieved {len(trends)} trending topics")
        print(f"  Top 3: {', '.join([t['term'] for t in trends[:3]])}\n")
        
        # Step 2: Analyze Correlations
        print("🔗 Step 2: Analyzing Correlations")
        print("-" * 60)
        correlation_data = self.correlation_engine.analyze_trends(trends)
        unified_topic = correlation_data['unified_topic']
        print(f"✓ Unified Topic: {unified_topic['theme']}")
        print(f"  Confidence: {unified_topic['confidence']:.2%}")
        print(f"  Clusters: {correlation_data['num_clusters']}\n")
        
        # Free correlation engine memory (OOM prevention)
        print("💾 Freeing correlation engine memory...")
        del self.correlation_engine.model
        del self.correlation_engine
        import gc
        gc.collect()
        print("✓ Memory freed\n")
        
        # Step 3: Find Academic Paper
        print("📚 Step 3: Finding Research Paper")
        print("-" * 60)
        paper = self.paper_finder.find_best_paper(
            topic=unified_topic['theme'],
            max_results=10
        )
        
        if not paper:
            print("❌ No suitable paper found. Exiting.")
            sys.exit(1)
        
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
        
        # Summary
        print("\n" + "="*60)
        print("✅ Pipeline Complete!")
        print("="*60)
        print(f"Output: {output_path}")
        print(f"Topic: {unified_topic['theme']}")
        print(f"Paper: {paper['title']}")
        print(f"Words: ~{len(script.split()):,}")
        
        return output_path
    
    def _save_script(self, script: str, topic: str, output_dir: str) -> str:
        """Save the generated script to a file"""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename from date and topic
        date_str = datetime.now().strftime("%Y-%m-%d")
        topic_slug = topic.lower().replace(' ', '-').replace('/', '-')[:50]
        filename = f"{date_str}_{topic_slug}.md"
        
        filepath = os.path.join(output_dir, filename)
        
        # Write script
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script)
        
        return filepath


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Get LLM provider configuration
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    semantic_scholar_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    
    # Build provider-specific config
    llm_config = {}
    if llm_provider == "ollama":
        llm_config = {
            'base_url': os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            'model': os.getenv("OLLAMA_MODEL", "qwen3:8b")
        }
        print(f"🤖 LLM Provider: Ollama ({llm_config['model']})")
        
    elif llm_provider == "anthropic":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            print("❌ Error: ANTHROPIC_API_KEY not found in environment")
            print("Please add to .env file:")
            print("  ANTHROPIC_API_KEY=your_key_here")
            sys.exit(1)
        llm_config = {
            'api_key': anthropic_key,
            'model': os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        }
        print(f"🤖 LLM Provider: Anthropic ({llm_config['model']})")
        
    else:
        print(f"❌ Error: Unknown LLM_PROVIDER: {llm_provider}")
        print("Valid options: 'ollama' or 'anthropic'")
        sys.exit(1)
    
    # Parse command line arguments
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
    
    args = parser.parse_args()
    
    # Override provider from command line if specified
    if args.provider:
        llm_provider = args.provider
        # Rebuild config for overridden provider
        if llm_provider == "ollama":
            llm_config = {
                'base_url': os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                'model': os.getenv("OLLAMA_MODEL", "qwen3:8b")
            }
        else:
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_key:
                print("❌ Error: ANTHROPIC_API_KEY required for anthropic provider")
                sys.exit(1)
            llm_config = {
                'api_key': anthropic_key,
                'model': os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
            }
    
    # Run pipeline
    try:
        researcher = Researcher7(
            llm_provider=llm_provider,
            llm_config=llm_config,
            semantic_scholar_key=semantic_scholar_key
        )
        
        output_path = researcher.run(
            num_trends=args.trends,
            country=args.country,
            output_dir=args.output
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
