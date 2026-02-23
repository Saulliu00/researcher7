"""
Script Generator - uses LLM (local or cloud) to generate 30-minute voice scripts
Supports: Ollama (local) and Anthropic Claude (cloud)
"""
from anthropic import Anthropic
import requests
from typing import List, Dict
import os


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
        self.target_words = 4750  # Target for 30-minute script (~158 words/min)
        
        if self.provider == "ollama":
            self.ollama_url = kwargs.get('base_url', 'http://127.0.0.1:11434')
            self.model = kwargs.get('model', 'qwen3:8b')
            print(f"Using Ollama: {self.model} @ {self.ollama_url}")
            
        elif self.provider == "anthropic":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Anthropic API key required for anthropic provider")
            self.client = Anthropic(api_key=api_key)
            self.model = kwargs.get('model', 'claude-sonnet-4-5')
            print(f"Using Anthropic: {self.model}")
            
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
        print(f"Generating script with {self.provider} ({self.model})...")
        
        # Build the prompt
        prompt = self._build_prompt(trends, correlation_data, paper)
        
        # Generate based on provider
        if self.provider == "ollama":
            script = self._generate_ollama(prompt)
        else:
            script = self._generate_anthropic(prompt)
        
        # Add metadata header
        header = self._create_header(trends, correlation_data, paper)
        full_script = f"{header}\n\n{script}"
        
        print(f"✓ Generated script ({self._count_words(script):,} words)")
        
        return full_script
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate script using local Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 6000,  # Allow ~6000 tokens for script
                    }
                },
                timeout=600  # 10 minutes timeout for local generation
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.RequestException as e:
            print(f"Ollama error: {e}")
            raise
    
    def _generate_anthropic(self, prompt: str) -> str:
        """Generate script using Anthropic Claude API"""
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
            print(f"Anthropic error: {e}")
            raise
    
    def _build_prompt(self, trends: List[Dict], correlation_data: Dict, 
                     paper: Dict) -> str:
        """Build the LLM prompt for script generation"""
        
        # Extract key data
        unified_topic = correlation_data['unified_topic']
        clusters = [c for c in correlation_data['clusters'] if c['label'] != 'noise']
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
Write an engaging, informative 30-minute voice script that:

1. **Opens with a Hook (0-2 min / 300-350 words):**
   - Start with a compelling observation about what people are searching for right now
   - Introduce 3-5 of the most interesting trending terms
   - Tease the unexpected connection between them
   - Present the central question that will guide the narrative

2. **Analyzes the Trends (2-8 min / 900-1,000 words):**
   - Deep dive into 3-5 key trending topics
   - Explain why each is trending and what's driving public interest
   - Identify emerging patterns and connections
   - Build narrative momentum toward the unified theme

3. **Synthesizes the Topic (8-15 min / 1,050-1,150 words):**
   - Reveal the unified theme: "{unified_topic['theme']}"
   - Show how the disparate trends actually connect to a deeper theme
   - Build a bridge to academic research
   - Introduce why this academic paper is perfectly relevant

4. **Explores the Research (15-25 min / 1,500-1,700 words):**
   - Introduce the paper and its authors with context
   - Explain the core findings in accessible language
   - Connect the research findings back to the trending topics
   - Use examples and analogies to make complex concepts clear
   - Highlight surprising insights or implications

5. **Synthesizes & Concludes (25-30 min / 750-800 words):**
   - Bring the trends and research together into a cohesive narrative
   - Discuss real-world implications and future outlook
   - Circle back to the original trending topics with new understanding
   - End with a memorable thought or call to reflection

**Style Guidelines:**
- Write for AUDIO (voice script) - use conversational, flowing language
- Avoid bullet points or visual elements (people will be listening, not reading)
- Use natural transitions and signposting ("Now here's where it gets interesting...")
- Include rhetorical questions to engage listeners
- Make complex ideas accessible without being condescending
- Maintain narrative flow throughout - this should feel like a story, not a lecture
- Target exactly {self.target_words} words (±200 words is acceptable)

**Tone:** Intelligent but accessible, curious and enthusiastic, authoritative but not dry.

Write the complete script now. Do not include any meta-commentary - just the script itself, ready to be read aloud.
"""
        
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
