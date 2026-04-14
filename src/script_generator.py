"""
Script Generator - uses LLM (local or cloud) to generate 30-minute voice scripts.
Provider-agnostic: receives an LLMProvider instance and calls provider.generate().
"""
from typing import List, Dict
import os
from pathlib import Path
import json
from datetime import datetime

from llm_providers.base import LLMProvider


# ============================================================================
# CONFIGURATION: Section Word Counts (adjust these for fine-tuning)
# ============================================================================
# 10-section strategy: smaller pieces to avoid Ollama timeouts on Raspberry Pi
SECTION_WORD_COUNTS = {
    'section_1_hook': 400,              # Opening hook (0-2.5 min)
    'section_2_trends_overview': 500,   # Trend overview (2.5-6 min)
    'section_3_cluster_1': 500,         # First trend cluster (6-9 min)
    'section_4_cluster_2': 500,         # Second trend cluster (9-12 min)
    'section_5_research_intro': 400,    # Research paper intro (12-15 min)
    'section_6_research_dive_1': 500,   # Research deep dive part 1 (15-18 min)
    'section_7_research_dive_2': 500,   # Research deep dive part 2 (18-21 min)
    'section_8_applications': 500,      # Real-world applications (21-24 min)
    'section_9_future': 500,            # Future implications (24-27 min)
    'section_10_conclusion': 400,       # Conclusion/Call-to-action (27-30 min)
}

# Total target (sum of sections)
TOTAL_TARGET_WORDS = sum(SECTION_WORD_COUNTS.values())  # 4700 words

# Acceptable variance per section (±)
WORD_VARIANCE = 50

# ============================================================================
# PROMPT TEMPLATES (modular for easy fine-tuning)
# ============================================================================

class ScriptGenerator:
    def __init__(self, provider: LLMProvider):
        """
        Initialize script generator with a pluggable LLM provider.

        Args:
            provider: An LLMProvider instance (e.g. OllamaProvider, AnthropicProvider)
        """
        self.provider = provider
        self.target_words = TOTAL_TARGET_WORDS
        self.section_counts = SECTION_WORD_COUNTS
        self.word_variance = WORD_VARIANCE
        
        # Auto-save setup
        self.autosave_dir = Path("outputs/autosave")
        self.autosave_dir.mkdir(parents=True, exist_ok=True)

        mode = "single-pass" if provider.supports_long_context else "multi-pass (10 sections)"
        print(f"Using {provider.name}: {provider.model}")
        print(f"Generation strategy: {mode}")
    
    def generate_script(self, trends: List[Dict], correlation_data: Dict, 
                       paper: Dict) -> str:
        """
        Generate a 30-minute voice script
        
        Args:
            trends: List of trending terms from TrendScraper
            correlation_data: Output from CorrelationEngine
            paper: Paper data from PaperFinder
        
        Returns:
            Formatted script text (markdown)
        """
        print(f"\nGenerating script with {self.provider.name} ({self.provider.model})...")
        print(f"Target: {self.target_words} words total")
        print(f"Auto-save enabled: {self.autosave_dir}")
        
        # Use multi-pass for local models (shorter contexts)
        # Use single-pass for cloud models with long context support
        if self.provider.supports_long_context:
            script = self._generate_singlepass(trends, correlation_data, paper)
        else:
            script = self._generate_multipass(trends, correlation_data, paper)
        
        # Add metadata header
        header = self._create_header(trends, correlation_data, paper)
        full_script = f"{header}\n\n{script}"
        
        word_count = self._count_words(script)
        print(f"\n✅ Generated script: {word_count:,} words")
        print(f"   Target: {self.target_words} words ({word_count/self.target_words*100:.1f}% of target)")
        
        return full_script
    
    def _save_section(self, section_num: int, section_name: str, content: str, 
                      trends: List[Dict], correlation_data: Dict, paper: Dict):
        """Save a completed section to autosave directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"section_{section_num:02d}_{section_name}.md"
        filepath = self.autosave_dir / filename
        
        # Create section with context
        header = f"""# Section {section_num}/10: {section_name.replace('_', ' ').title()}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Word Count:** {self._count_words(content)}
**Target:** {self.section_counts.get(section_name, 'N/A')}

---

"""
        full_content = header + content
        
        # Save section
        filepath.write_text(full_content, encoding='utf-8')
        
        # Also save progress JSON
        progress_file = self.autosave_dir / "progress.json"
        progress_data = {
            "last_section": section_num,
            "last_section_name": section_name,
            "timestamp": timestamp,
            "completed_sections": section_num,
            "total_sections": len(self.section_counts),
            "unified_topic": correlation_data['unified_topic']['theme'],
            "paper_title": paper['title']
        }
        progress_file.write_text(json.dumps(progress_data, indent=2), encoding='utf-8')
        
        print(f"   💾 Auto-saved: {filename} ({self._count_words(content)} words)")
    
    def _generate_multipass(self, trends: List[Dict], correlation_data: Dict, 
                           paper: Dict) -> str:
        """
        Multi-pass generation for local models (Ollama).
        Generates script in 10 smaller sections to avoid timeouts.
        Each section auto-saves on completion.
        """
        print("\n📝 Multi-pass generation strategy (10 sections):")
        for key, count in self.section_counts.items():
            section_name = key.replace('_', ' ').title()
            print(f"   {section_name}: {count} words (±{self.word_variance})")
        print()

        top_trends = ', '.join(t['term'] for t in trends[:10])
        unified_topic = correlation_data['unified_topic']['theme']

        # Use real cluster terms when available, fall back to index-based slicing
        clusters = [c for c in correlation_data.get('clusters', []) if c['label'] != 'noise']
        cluster_1_terms = ', '.join(clusters[0]['terms'][:3]) if clusters else ', '.join(t['term'] for t in trends[:3])
        cluster_2_terms = ', '.join(clusters[1]['terms'][:3]) if len(clusters) > 1 else ', '.join(t['term'] for t in trends[3:6])

        # Define each section's prompt (order matters)
        section_defs = [
            ('section_1_hook',
             f"You are Saul, the host of this podcast. Write an engaging {{words}}-word opening hook about trending topics: {top_trends}. "
             f"Start with 'Hey, this is Saul...' and make an observation about what people are searching for RIGHT NOW. Be conversational, personal, and voice-optimized."),
            ('section_2_trends_overview',
             f"You are Saul, continuing your podcast. Write {{words}} words giving an overview of these trending topics: {top_trends}. "
             f"Explain briefly why people are interested. Group related topics together. Use first person ('I noticed...', 'What fascinates me...'). Voice-optimized."),
            ('section_3_cluster_1',
             f"Write {{words}} words analyzing this first cluster of trends: {cluster_1_terms}. "
             f"Deep dive into why these are connected and what's driving interest. Voice-optimized."),
            ('section_4_cluster_2',
             f"Write {{words}} words analyzing this second cluster: {cluster_2_terms}. "
             f"Show connections to the first cluster. Build toward the unified theme: {unified_topic}. Voice-optimized."),
            ('section_5_research_intro',
             f"Write {{words}} words introducing this research paper: '{paper['title']}' by {', '.join(paper['authors'][:2])} ({paper['year']}). "
             f"Explain why it's relevant to the trends we discussed. Bridge from trending topics to academic research. Voice-optimized."),
            ('section_6_research_dive_1',
             f"Write {{words}} words explaining the first half of the research findings from '{paper['title']}'. "
             f"Abstract: {paper['abstract'][:200]}... Make complex concepts accessible. Use analogies. Voice-optimized."),
            ('section_7_research_dive_2',
             f"Write {{words}} words continuing the research explanation. Focus on key findings and surprising insights from '{paper['title']}'. "
             f"Connect back to the trending topics. Voice-optimized."),
            ('section_8_applications',
             f"Write {{words}} words showing real-world applications of the research from '{paper['title']}'. "
             f"Give 2-3 concrete examples. Show how it applies to the trending topics: {cluster_1_terms}, {cluster_2_terms}. Voice-optimized."),
            ('section_9_future',
             f"Write {{words}} words discussing future outlook and implications. Where is this heading? What might change? "
             f"Connect research insights to future trends. Voice-optimized."),
            ('section_10_conclusion',
             f"You are Saul, wrapping up your podcast. Write {{words}} words for the conclusion. "
             f"Synthesize key insights from trends + research. Circle back to the original trending topics with new understanding. "
             f"End with a personal sign-off ('This is Saul, thanks for listening...'). Voice-optimized for podcast ending."),
        ]

        import gc
        sections = []
        total = len(section_defs)
        for idx, (section_name, prompt_template) in enumerate(section_defs, start=1):
            target_words = self.section_counts[section_name]
            label = section_name.replace('_', ' ').title()
            print(f"Generating Section {idx}/{total}: {label}...")

            prompt = prompt_template.format(words=target_words)
            content = self._generate_short_section(prompt, target_words)
            sections.append(content)
            self._save_section(idx, section_name, content, trends, correlation_data, paper)
            print(f"   ✓ Section {idx}: {self._count_words(content)} words")
            gc.collect()

        return "\n\n".join(sections)
    
    def _generate_short_section(self, prompt: str, target_words: int) -> str:
        """Generate a short section with simplified prompt"""
        full_prompt = f"{prompt}\n\nWrite EXACTLY {target_words} words (±{self.word_variance} acceptable). No meta-commentary, just the script:"
        return self._call_llm(full_prompt)
    
    def _generate_singlepass(self, trends: List[Dict], correlation_data: Dict, 
                            paper: Dict) -> str:
        """Single-pass generation for cloud models (Anthropic Claude)"""
        prompt = self._build_singlepass_prompt(trends, correlation_data, paper)
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """Delegate to the pluggable LLM provider."""
        return self.provider.generate(prompt)
    
    def _build_singlepass_prompt(self, trends: List[Dict], correlation_data: Dict, 
                                 paper: Dict) -> str:
        """Build prompt for single-pass generation (Anthropic)"""
        
        unified_topic = correlation_data['unified_topic']
        top_trends = [t['term'] for t in trends[:10]]
        
        prompt = f"""You are a professional content creator specializing in educational voice scripts. Your task is to write a {self.target_words}-word script (approximately 30 minutes when read aloud at ~158 words per minute) that bridges trending topics with academic research.

**Context:**
- **Top Trending Search Terms (Last 24h):** {', '.join(top_trends)}
- **Unified Topic:** {unified_topic['theme']}
- **Key Connecting Terms:** {', '.join(unified_topic.get('key_terms', []))}

**Academic Paper:**
- **Title:** {paper['title']}
- **Authors:** {', '.join(paper['authors'][:3])} ({paper['year']})
- **Citations:** {paper['citations']:,}
- **Abstract:** {paper['abstract']}

**Your Task:**
Write an engaging, informative 30-minute voice script with these 10 sections:

1. **Opening Hook (0-2.5 min / {self.section_counts['section_1_hook']} words):**
   - Compelling observation about current search trends
   - Introduce 3-5 key trending terms
   - Tease the unexpected connection
   - Present the central question

2. **Trends Overview (2.5-6 min / {self.section_counts['section_2_trends_overview']} words):**
   - Overview of trending topics and why people care
   - Group related topics together

3. **Trend Cluster 1 (6-9 min / {self.section_counts['section_3_cluster_1']} words):**
   - Deep dive into the first cluster of related trends
   - Explain connections and drivers

4. **Trend Cluster 2 (9-12 min / {self.section_counts['section_4_cluster_2']} words):**
   - Deep dive into the second cluster
   - Build toward the unified theme

5. **Research Introduction (12-15 min / {self.section_counts['section_5_research_intro']} words):**
   - Bridge from trends to academic research
   - Introduce the paper and why it matters

6. **Research Deep Dive Part 1 (15-18 min / {self.section_counts['section_6_research_dive_1']} words):**
   - Core findings explained accessibly
   - Use analogies and examples

7. **Research Deep Dive Part 2 (18-21 min / {self.section_counts['section_7_research_dive_2']} words):**
   - Key insights and surprises
   - Connect back to trending topics

8. **Real-World Applications (21-24 min / {self.section_counts['section_8_applications']} words):**
   - 2-3 concrete examples or case studies
   - Practical connections to trends

9. **Future Implications (24-27 min / {self.section_counts['section_9_future']} words):**
   - Where is this heading?
   - Forward-looking analysis

10. **Conclusion (27-30 min / {self.section_counts['section_10_conclusion']} words):**
    - Synthesize key insights
    - Circle back to original trends
    - Memorable closing thought

**Style Guidelines:**
- Write for AUDIO (conversational, flowing language)
- Natural transitions and signposting
- Rhetorical questions to engage
- Accessible but intelligent
- Narrative flow throughout
- Target EXACTLY {self.target_words} words

**Tone:** Intelligent but accessible, curious and enthusiastic, authoritative but not dry.

Write the complete script now. No meta-commentary - just the script itself:"""
        
        return prompt
    
    def _create_header(self, trends: List[Dict], correlation_data: Dict, 
                      paper: Dict) -> str:
        """Create metadata header for the script"""
        
        # Format trending terms with rankings
        trending_list = '\n'.join([f"{i+1}. {t['term']}" for i, t in enumerate(trends[:15])])
        
        # Format clusters if available
        clusters_text = ""
        if correlation_data.get('clusters'):
            clusters_text = "\n\n**Identified Clusters:**\n"
            for i, cluster in enumerate(correlation_data['clusters'][:5], 1):
                cluster_terms = ', '.join(cluster['terms'][:5])
                clusters_text += f"- Cluster {i}: {cluster_terms}\n"
        
        unified_topic = correlation_data['unified_topic']
        
        header = f"""# Researcher7 Voice Script

**Generated:** {self._get_timestamp()}
**Host:** Saul
**LLM Provider:** {self.provider.name}
**Model:** {self.provider.model}
**Target Length:** 30 minutes (~{self.target_words} words)

---

## Trending Topics Captured

**Top 15 Google Trending Searches:**
{trending_list}

**Unified Topic:** {unified_topic['theme']}  
**Confidence:** {unified_topic['confidence']:.1%}  
**Key Terms:** {', '.join(unified_topic.get('key_terms', [])[:5])}
{clusters_text}

---

## Research Source

**{paper['title']}**  
{', '.join(paper['authors'][:3])} ({paper['year']}) - {paper['citations']:,} citations  
Source: {paper['source']}  
URL: {paper['url']}

---
"""
        return header.strip()
    
    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    # Test the script generator
    import os
    from dotenv import load_dotenv
    load_dotenv()

    from llm_providers import create_provider

    provider_name = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider_name == "ollama":
        llm = create_provider(
            "ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        )
    else:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set")
            exit(1)
        llm = create_provider(
            "anthropic",
            api_key=api_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        )

    generator = ScriptGenerator(provider=llm)
    
    # Demo data
    demo_trends = [
        {'term': 'artificial intelligence', 'rank': 1},
        {'term': 'climate change', 'rank': 2},
        {'term': 'quantum computing', 'rank': 3},
    ]
    
    demo_correlation = {
        'unified_topic': {
            'theme': 'Technology and Environmental Sustainability',
            'key_terms': ['artificial intelligence', 'climate change']
        },
        'clusters': []
    }
    
    demo_paper = {
        'title': 'AI for Climate Change Mitigation',
        'authors': ['John Doe', 'Jane Smith'],
        'year': 2024,
        'citations': 150,
        'abstract': 'This paper explores how artificial intelligence can be applied to climate change mitigation...',
        'url': 'https://example.com',
        'source': 'Demo'
    }
    
    script = generator.generate_script(demo_trends, demo_correlation, demo_paper)
    print("\n" + "="*60)
    print("GENERATED SCRIPT PREVIEW:")
    print("="*60)
    print(script[:500] + "...")
