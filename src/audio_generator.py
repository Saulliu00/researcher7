"""
Audio Generator — reads a generated script, strips markdown, and
delegates to a pluggable TTSProvider to produce an audio file.
"""
import os
import re
from datetime import datetime
from tts_providers.base import TTSProvider


class AudioGenerator:
    """Convert a markdown script to a WAV audio file."""

    def __init__(self, provider: TTSProvider):
        self.provider = provider

    def generate_audio(self, script: str, topic: str,
                       output_dir: str = 'outputs') -> str:
        """
        Generate audio from a script string.

        Args:
            script: Full markdown script text.
            topic: Topic name (used for the output filename).
            output_dir: Base output directory.

        Returns:
            Path to the generated .wav file.
        """
        clean_text = self._strip_markdown(script)

        audio_dir = os.path.join(output_dir, 'audio')
        os.makedirs(audio_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        topic_slug = topic.lower().replace(' ', '-').replace('/', '-')[:50]
        filename = f"{date_str}_{topic_slug}.wav"
        output_path = os.path.join(audio_dir, filename)

        print(f"  Synthesizing ~{len(clean_text.split()):,} words with {self.provider.name}...")
        self.provider.synthesize(clean_text, output_path)
        print(f"  ✓ Audio saved: {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # Markdown → plain text
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """
        Remove markdown metadata and formatting, returning plain text
        suitable for TTS synthesis.
        """
        lines = text.splitlines()
        body_lines: list[str] = []
        in_header_block = True  # skip the metadata header
        header_dashes_seen = 0

        for line in lines:
            stripped = line.strip()

            # Skip metadata header (delimited by --- ... ---)
            if in_header_block:
                if stripped == '---':
                    header_dashes_seen += 1
                    if header_dashes_seen >= 2:
                        in_header_block = False
                    continue
                elif header_dashes_seen == 0 and stripped:
                    # First non-empty line isn't --- → no header block
                    in_header_block = False
                    # Fall through to process this line normally
                else:
                    continue

            # Skip remaining --- separators
            if stripped == '---':
                continue

            # Skip metadata-style lines
            if stripped.startswith('**Generated:') or stripped.startswith('**Host:'):
                continue
            if stripped.startswith('**LLM Provider:') or stripped.startswith('**Model:'):
                continue
            if stripped.startswith('**Target Length:') or stripped.startswith('**Key Terms:'):
                continue
            if stripped.startswith('**Unified Topic:') or stripped.startswith('**Confidence:'):
                continue

            # Skip the "## Research Source" / "## Trending Topics" sections
            if stripped.startswith('## Trending Topics') or stripped.startswith('## Research Source'):
                continue
            if stripped.startswith('**Top 15') or stripped.startswith('Source:') or stripped.startswith('URL:'):
                continue
            if re.match(r'^\d+\.\s+\S', stripped) and len(stripped) < 80:
                # Looks like a numbered list of trend terms — skip
                continue

            # Remove markdown formatting
            cleaned = stripped
            cleaned = re.sub(r'^#{1,6}\s+', '', cleaned)  # headers
            cleaned = re.sub(r'\*\*(.+?)\*\*', r'\1', cleaned)  # bold
            cleaned = re.sub(r'\*(.+?)\*', r'\1', cleaned)  # italic
            cleaned = re.sub(r'`(.+?)`', r'\1', cleaned)  # inline code
            cleaned = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', cleaned)  # links

            if cleaned:
                body_lines.append(cleaned)

        return '\n\n'.join(body_lines)
