"""
Script Generator - uses LLM (local or cloud) to generate 30-minute voice scripts
Supports: Ollama (local, multi-pass) and Anthropic Claude (cloud, single-pass)
"""
from anthropic import Anthropic
import requests
from typing import List, Dict
import os
from pathlib import Path
import json
from datetime import datetime


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

SECTION_1_PROMPT_TEMPLATE = """You are writing the OPENING SECTION of a 30-minute voice script (Section 1 of 5).

**Context:**
- Top trending searches: {top_trends}
- Unified topic: {unified_topic}
- Research paper: {paper_title}

**Your Task:** Write EXACTLY {target_words} words for the opening hook (0-2 minutes of audio).

**Content Requirements:**
1. Start with an engaging observation about what people are searching for RIGHT NOW
2. Introduce 3-5 of the most interesting trending terms with brief context
3. Create curiosity by hinting at an unexpected connection between them
4. Pose a central question that will guide the entire narrative
5. Set up anticipation for deeper exploration

**Style:** Conversational, engaging, voice-optimized (people will be listening). Natural flow for audio narration.

**Length:** EXACTLY {target_words} words (±{variance} words acceptable). This is critical - count carefully.

Write the opening section now. No meta-commentary, just the script ready to be read aloud:"""

SECTION_2_PROMPT_TEMPLATE = """You are writing SECTION 2 of a 30-minute voice script (Trend Analysis after the intro).

**Context:**
- The intro already hooked listeners with trending topics: {top_trends}
- Now we're analyzing WHY these topics are trending and what connects them
- Leading toward: {unified_topic}

**Your Task:** Write EXACTLY {target_words} words analyzing the key trends (2-8 minutes of audio).

**Content Requirements:**
1. Deep dive into 3-5 key trending topics
2. Explain WHY each is trending - what's driving public interest?
3. Identify emerging patterns and connections between them
4. Build narrative momentum toward the unified theme
5. Create smooth transitions between topics

**Style:** Analytical but accessible, maintain conversational flow for audio. Use transitions like "Now let's consider...", "What's fascinating here is..."

**Length:** EXACTLY {target_words} words (±{variance} words acceptable). This is your target - aim for it.

Write Section 2 now, continuing naturally from the intro:"""

SECTION_3_PROMPT_TEMPLATE = """You are writing SECTION 3 of a 30-minute voice script (Research Deep Dive).

**Context:**
- Sections 1-2 analyzed trending topics and revealed patterns
- Unified theme: {unified_topic}
- Now we're diving into the academic research that illuminates this theme

**Research Paper:**
- Title: {paper_title}
- Authors: {paper_authors} ({paper_year})
- Citations: {paper_citations}
- Abstract: {paper_abstract}
- Source: {paper_source}

**Your Task:** Write EXACTLY {target_words} words exploring this research (8-15 minutes of audio).

**Content Requirements:**
1. Smoothly bridge from trending topics to academic research (why is this paper relevant?)
2. Introduce the paper and authors with context
3. Explain the core research findings in accessible, engaging language
4. Use analogies and examples to clarify complex concepts
5. Connect research findings back to the trending topics listeners care about
6. Highlight surprising insights or counterintuitive findings
7. Build intellectual excitement about the implications

**Style:** Make complex research accessible without being condescending. Maintain narrative momentum. Voice-optimized for audio.

**Length:** EXACTLY {target_words} words (±{variance} words acceptable). This is the longest section - take the space to go deep.

Write Section 3 now, continuing the narrative:"""

SECTION_4_PROMPT_TEMPLATE = """You are writing SECTION 4 of a 30-minute voice script (Applications and Examples).

**Context:**
- We've explored the research: {paper_title}
- Central theme: {unified_topic}
- Trending topics: {top_trends}
- Now we're showing real-world applications and concrete examples

**Your Task:** Write EXACTLY {target_words} words on applications and examples (15-25 minutes of audio).

**Content Requirements:**
1. Connect the research findings to real-world situations
2. Provide 2-3 concrete examples or case studies
3. Show how the research insights apply to the trending topics
4. Discuss current or near-future applications
5. Address potential challenges or limitations
6. Make abstract concepts tangible through specific scenarios

**Style:** Practical and grounded, but maintain intellectual engagement. Use vivid examples. Voice-optimized.

**Length:** EXACTLY {target_words} words (±{variance} words acceptable). Hit this target for optimal pacing.

Write Section 4 now, showing the practical implications:"""

SECTION_5_PROMPT_TEMPLATE = """You are writing SECTION 5 (FINAL) of a 30-minute voice script (Synthesis and Conclusion).

**Context:**
- We've journeyed from trending topics ({top_trends})
- Through research ({paper_title})
- To practical applications
- Now we're synthesizing everything and looking forward

**Your Task:** Write EXACTLY {target_words} words for the conclusion (25-30 minutes of audio).

**Content Requirements:**
1. Synthesize the key insights from trends + research + applications
2. Discuss future outlook - where is this heading?
3. Circle back to the original trending topics with new understanding
4. Offer actionable takeaways or thought-provoking questions
5. End with a memorable final thought that resonates
6. Create a sense of closure while inspiring further curiosity

**Style:** Thoughtful and forward-looking. Bring the narrative full circle. Voice-optimized for powerful audio conclusion.

**Length:** EXACTLY {target_words} words (±{variance} words acceptable). This is your final word count target.

Write the final section now, concluding the 30-minute journey:"""


class ScriptGenerator:
    def __init__(self, provider: str = "ollama", **kwargs):
        """
        Initialize script generator with configurable LLM provider
        
        Args:
            provider: "ollama" or "anthropic"
            **kwargs: Provider-specific arguments
                For ollama: base_url, model
                For anthropic: api_key, model
        """
        self.provider = provider.lower()
        self.target_words = TOTAL_TARGET_WORDS
        self.section_counts = SECTION_WORD_COUNTS
        self.word_variance = WORD_VARIANCE
        
        # Auto-save setup
        self.autosave_dir = Path("outputs/autosave")
        self.autosave_dir.mkdir(parents=True, exist_ok=True)
        
        if self.provider == "ollama":
            self.ollama_url = kwargs.get('base_url', 'http://127.0.0.1:11434')
            self.model = kwargs.get('model', 'qwen3:8b')
            print(f"Using Ollama: {self.model} @ {self.ollama_url}")
            print(f"Multi-pass generation enabled (10 sections)")
            
        elif self.provider == "anthropic":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Anthropic API key required for anthropic provider")
            self.client = Anthropic(api_key=api_key)
            self.model = kwargs.get('model', 'claude-sonnet-4-5')
            print(f"Using Anthropic: {self.model}")
            print(f"Single-pass generation enabled")
            
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'ollama' or 'anthropic'")
    
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
        print(f"\nGenerating script with {self.provider} ({self.model})...")
        print(f"Target: {self.target_words} words total")
        print(f"Auto-save enabled: {self.autosave_dir}")
        
        # Use multi-pass for Ollama (local models need shorter contexts)
        # Use single-pass for Anthropic (can handle long contexts)
        if self.provider == "ollama":
            script = self._generate_multipass(trends, correlation_data, paper)
        else:
            script = self._generate_singlepass(trends, correlation_data, paper)
        
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
        filepath.write_text(full_content)
        
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
        progress_file.write_text(json.dumps(progress_data, indent=2))
        
        print(f"   💾 Auto-saved: {filename} ({self._count_words(content)} words)")
    
    def _generate_multipass(self, trends: List[Dict], correlation_data: Dict, 
                           paper: Dict) -> str:
        """
        Multi-pass generation for local models (Ollama)
        Generates script in 10 smaller sections to avoid timeouts on Raspberry Pi
        Each section auto-saves on completion
        """
        print("\n📝 Multi-pass generation strategy (10 sections):")
        for key, count in self.section_counts.items():
            section_name = key.replace('_', ' ').title()
            print(f"   {section_name}: {count} words (±{self.word_variance})")
        print()
        
        sections = []
        top_trends = ', '.join([t['term'] for t in trends[:10]])
        unified_topic = correlation_data['unified_topic']['theme']
        
        # Section 1: Hook
        section_name = 'section_1_hook'
        print(f"Generating Section 1/10: Opening Hook...")
        section1 = self._generate_short_section(
            f"Write an engaging {self.section_counts[section_name]}-word opening hook for a podcast about trending topics: {top_trends}. Start with an observation about what people are searching for RIGHT NOW. Be conversational and voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section1)
        self._save_section(1, section_name, section1, trends, correlation_data, paper)
        print(f"   ✓ Section 1: {self._count_words(section1)} words")
        
        # Section 2: Trends Overview
        section_name = 'section_2_trends_overview'
        print(f"Generating Section 2/10: Trends Overview...")
        section2 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words giving an overview of these trending topics: {top_trends}. Explain briefly why people are interested. Group related topics together. Voice-optimized for podcast.",
            self.section_counts[section_name]
        )
        sections.append(section2)
        self._save_section(2, section_name, section2, trends, correlation_data, paper)
        print(f"   ✓ Section 2: {self._count_words(section2)} words")
        
        # Section 3: First Trend Cluster
        section_name = 'section_3_cluster_1'
        cluster_1_terms = ', '.join([t['term'] for t in trends[:3]])
        print(f"Generating Section 3/10: First Trend Cluster...")
        section3 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words analyzing this first cluster of trends: {cluster_1_terms}. Deep dive into why these are connected and what's driving interest. Voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section3)
        self._save_section(3, section_name, section3, trends, correlation_data, paper)
        print(f"   ✓ Section 3: {self._count_words(section3)} words")
        
        # Section 4: Second Trend Cluster
        section_name = 'section_4_cluster_2'
        cluster_2_terms = ', '.join([t['term'] for t in trends[3:6]])
        print(f"Generating Section 4/10: Second Trend Cluster...")
        section4 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words analyzing this second cluster: {cluster_2_terms}. Show connections to the first cluster. Build toward the unified theme: {unified_topic}. Voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section4)
        self._save_section(4, section_name, section4, trends, correlation_data, paper)
        print(f"   ✓ Section 4: {self._count_words(section4)} words")
        
        # Section 5: Research Intro
        section_name = 'section_5_research_intro'
        print(f"Generating Section 5/10: Research Paper Introduction...")
        section5 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words introducing this research paper: '{paper['title']}' by {', '.join(paper['authors'][:2])} ({paper['year']}). Explain why it's relevant to the trends we discussed. Bridge from trending topics to academic research. Voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section5)
        self._save_section(5, section_name, section5, trends, correlation_data, paper)
        print(f"   ✓ Section 5: {self._count_words(section5)} words")
        
        # Section 6: Research Deep Dive Part 1
        section_name = 'section_6_research_dive_1'
        print(f"Generating Section 6/10: Research Deep Dive Part 1...")
        section6 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words explaining the first half of the research findings from '{paper['title']}'. Abstract: {paper['abstract'][:200]}... Make complex concepts accessible. Use analogies. Voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section6)
        self._save_section(6, section_name, section6, trends, correlation_data, paper)
        print(f"   ✓ Section 6: {self._count_words(section6)} words")
        
        # Section 7: Research Deep Dive Part 2
        section_name = 'section_7_research_dive_2'
        print(f"Generating Section 7/10: Research Deep Dive Part 2...")
        section7 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words continuing the research explanation. Focus on key findings and surprising insights from '{paper['title']}'. Connect back to the trending topics. Voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section7)
        self._save_section(7, section_name, section7, trends, correlation_data, paper)
        print(f"   ✓ Section 7: {self._count_words(section7)} words")
        
        # Section 8: Applications
        section_name = 'section_8_applications'
        print(f"Generating Section 8/10: Real-World Applications...")
        section8 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words showing real-world applications of the research from '{paper['title']}'. Give 2-3 concrete examples. Show how it applies to the trending topics: {cluster_1_terms}, {cluster_2_terms}. Voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section8)
        self._save_section(8, section_name, section8, trends, correlation_data, paper)
        print(f"   ✓ Section 8: {self._count_words(section8)} words")
        
        # Section 9: Future Implications
        section_name = 'section_9_future'
        print(f"Generating Section 9/10: Future Implications...")
        section9 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words discussing future outlook and implications. Where is this heading? What might change? Connect research insights to future trends. Voice-optimized.",
            self.section_counts[section_name]
        )
        sections.append(section9)
        self._save_section(9, section_name, section9, trends, correlation_data, paper)
        print(f"   ✓ Section 9: {self._count_words(section9)} words")
        
        # Section 10: Conclusion
        section_name = 'section_10_conclusion'
        print(f"Generating Section 10/10: Conclusion...")
        section10 = self._generate_short_section(
            f"Write {self.section_counts[section_name]} words for the conclusion. Synthesize key insights from trends + research. Circle back to the original trending topics with new understanding. End with a memorable thought. Voice-optimized for podcast ending.",
            self.section_counts[section_name]
        )
        sections.append(section10)
        self._save_section(10, section_name, section10, trends, correlation_data, paper)
        print(f"   ✓ Section 10: {self._count_words(section10)} words")
        
        # Combine all sections
        full_script = "\n\n".join(sections)
        return full_script
    
    def _generate_short_section(self, prompt: str, target_words: int) -> str:
        """Generate a short section with simplified prompt"""
        full_prompt = f"{prompt}\n\nWrite EXACTLY {target_words} words (±{self.word_variance} acceptable). No meta-commentary, just the script:"
        return self._call_llm(full_prompt)
    
    def _generate_section_1(self, trends, correlation_data, paper) -> str:
        """Section 1: Intro + Hook"""
        top_trends = ', '.join([t['term'] for t in trends[:10]])
        unified_topic = correlation_data['unified_topic']['theme']
        
        prompt = SECTION_1_PROMPT_TEMPLATE.format(
            top_trends=top_trends,
            unified_topic=unified_topic,
            paper_title=paper['title'],
            target_words=self.section_counts['section_1_intro'],
            variance=self.word_variance
        )
        
        return self._call_llm(prompt)
    
    def _generate_section_2(self, trends, correlation_data, paper) -> str:
        """Section 2: Trend Analysis"""
        top_trends = ', '.join([t['term'] for t in trends[:5]])
        unified_topic = correlation_data['unified_topic']['theme']
        
        prompt = SECTION_2_PROMPT_TEMPLATE.format(
            top_trends=top_trends,
            unified_topic=unified_topic,
            target_words=self.section_counts['section_2_analysis'],
            variance=self.word_variance
        )
        
        return self._call_llm(prompt)
    
    def _generate_section_3(self, trends, correlation_data, paper) -> str:
        """Section 3: Research Deep Dive"""
        unified_topic = correlation_data['unified_topic']['theme']
        
        prompt = SECTION_3_PROMPT_TEMPLATE.format(
            unified_topic=unified_topic,
            paper_title=paper['title'],
            paper_authors=', '.join(paper['authors'][:3]),
            paper_year=paper['year'],
            paper_citations=f"{paper['citations']:,}",
            paper_abstract=paper['abstract'],
            paper_source=paper['source'],
            target_words=self.section_counts['section_3_research'],
            variance=self.word_variance
        )
        
        return self._call_llm(prompt)
    
    def _generate_section_4(self, trends, correlation_data, paper) -> str:
        """Section 4: Applications + Examples"""
        unified_topic = correlation_data['unified_topic']['theme']
        top_trends = ', '.join([t['term'] for t in trends[:5]])
        
        prompt = SECTION_4_PROMPT_TEMPLATE.format(
            paper_title=paper['title'],
            unified_topic=unified_topic,
            top_trends=top_trends,
            target_words=self.section_counts['section_4_applications'],
            variance=self.word_variance
        )
        
        return self._call_llm(prompt)
    
    def _generate_section_5(self, trends, correlation_data, paper) -> str:
        """Section 5: Future Outlook + Conclusion"""
        unified_topic = correlation_data['unified_topic']['theme']
        top_trends = ', '.join([t['term'] for t in trends[:5]])
        
        prompt = SECTION_5_PROMPT_TEMPLATE.format(
            top_trends=top_trends,
            paper_title=paper['title'],
            target_words=self.section_counts['section_5_conclusion'],
            variance=self.word_variance
        )
        
        return self._call_llm(prompt)
    
    def _generate_singlepass(self, trends: List[Dict], correlation_data: Dict, 
                            paper: Dict) -> str:
        """Single-pass generation for cloud models (Anthropic Claude)"""
        prompt = self._build_singlepass_prompt(trends, correlation_data, paper)
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM with the given prompt"""
        if self.provider == "ollama":
            return self._generate_ollama(prompt)
        else:
            return self._generate_anthropic(prompt)
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate text using local Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2000,  # Allow ~1500 words per section
                    }
                },
                timeout=600  # 10 minutes timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.RequestException as e:
            print(f"   ✗ Ollama error: {e}")
            raise
    
    def _generate_anthropic(self, prompt: str) -> str:
        """Generate text using Anthropic Claude API"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8000,  # ~6000 words max
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return message.content[0].text
            
        except Exception as e:
            print(f"   ✗ Anthropic error: {e}")
            raise
    
    def _build_singlepass_prompt(self, trends: List[Dict], correlation_data: Dict, 
                                 paper: Dict) -> str:
        """Build prompt for single-pass generation (Anthropic)"""
        
        unified_topic = correlation_data['unified_topic']
        top_trends = [t['term'] for t in trends[:10]]
        
        prompt = f"""You are a professional content creator specializing in educational voice scripts. Your task is to write a {self.target_words}-word script (approximately 30 minutes when read aloud at ~158 words per minute) that bridges trending topics with academic research.

**Context:**
- **Top Trending Search Terms (Last 24h):** {', '.join(top_trends)}
- **Unified Topic:** {unified_topic['theme']}
- **Key Connecting Terms:** {', '.join(unified_topic['key_terms'])}

**Academic Paper:**
- **Title:** {paper['title']}
- **Authors:** {', '.join(paper['authors'][:3])} ({paper['year']})
- **Citations:** {paper['citations']:,}
- **Abstract:** {paper['abstract']}

**Your Task:**
Write an engaging, informative 30-minute voice script with these 5 sections:

1. **Intro + Hook (0-2 min / {self.section_counts['section_1_intro']} words):**
   - Compelling observation about current search trends
   - Introduce 3-5 key trending terms
   - Tease the unexpected connection
   - Present the central question

2. **Trend Analysis (2-8 min / {self.section_counts['section_2_analysis']} words):**
   - Deep dive into key trending topics
   - Explain why each is trending
   - Identify patterns and connections
   - Build toward unified theme

3. **Research Deep Dive (8-15 min / {self.section_counts['section_3_research']} words):**
   - Bridge to academic research
   - Introduce paper and findings
   - Make complex concepts accessible
   - Connect research to trends
   - Highlight surprising insights

4. **Applications + Examples (15-25 min / {self.section_counts['section_4_applications']} words):**
   - Real-world applications
   - 2-3 concrete examples
   - Current/future implications
   - Practical connections to trends

5. **Future Outlook + Conclusion (25-30 min / {self.section_counts['section_5_conclusion']} words):**
   - Synthesize key insights
   - Future outlook and implications
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
        
        header = f"""# Researcher7 Voice Script

**Generated:** {self._get_timestamp()}
**LLM Provider:** {self.provider}
**Model:** {self.model}
**Unified Topic:** {correlation_data['unified_topic']['theme']}
**Research Paper:** {paper['title']}
**Target Length:** 30 minutes (~{self.target_words} words)

---

## Trending Topics Analyzed
{', '.join([t['term'] for t in trends[:10]])}

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
    
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        generator = ScriptGenerator(
            provider="ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b")
        )
    else:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set")
            exit(1)
        generator = ScriptGenerator(
            provider="anthropic",
            api_key=api_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        )
    
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
