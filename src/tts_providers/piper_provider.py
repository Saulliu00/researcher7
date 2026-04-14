"""Piper TTS provider (fast, offline, local neural TTS)."""
import io
import os
import struct
import subprocess
import shutil
import wave
from .base import TTSProvider


class PiperProvider(TTSProvider):
    """
    Generate speech using Piper — a fast local neural TTS engine.

    Piper runs as a standalone executable (no Python-version constraints).

    Setup:
        1. Download piper from https://github.com/rhasspy/piper/releases
           (e.g. piper_windows_amd64.zip) and unzip.
        2. Download a voice model (.onnx + .onnx.json) from
           https://huggingface.co/rhasspy/piper-voices
        3. Set PIPER_EXE and PIPER_VOICE in .env (or pass them here).

    Recommended voices:
        English: en_US-lessac-medium.onnx
        Chinese: zh_CN-huayan-medium.onnx
    """

    def __init__(self, piper_exe: str = None, voice_model: str = None,
                 speaker: int = None, speed: float = 1.0):
        """
        Args:
            piper_exe:    Path to the piper executable.
                          Auto-detected from PATH / PIPER_EXE env var.
            voice_model:  Path to the .onnx voice model file.
            speaker:      Speaker ID for multi-speaker models (optional).
            speed:        Speaking rate multiplier (default 1.0).
        """
        self._exe = piper_exe or os.getenv("PIPER_EXE") or shutil.which("piper")
        self._voice = voice_model or os.getenv("PIPER_VOICE")
        self._speaker = speaker
        self._speed = speed

        if not self._exe:
            raise FileNotFoundError(
                "Piper executable not found. Either:\n"
                "  1. Add piper to your PATH, or\n"
                "  2. Set PIPER_EXE=/path/to/piper in .env\n"
                "Download from: https://github.com/rhasspy/piper/releases"
            )
        if not self._voice:
            raise FileNotFoundError(
                "No Piper voice model configured. Set PIPER_VOICE=/path/to/model.onnx in .env\n"
                "Download voices from: https://huggingface.co/rhasspy/piper-voices"
            )

    @property
    def name(self) -> str:
        return "Piper"

    def synthesize(self, text: str, output_path: str) -> str:
        """
        Synthesize *text* to a WAV file at *output_path*.

        Long texts are split into paragraphs and synthesized individually,
        then concatenated into a single WAV.
        """
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        if len(paragraphs) <= 1:
            self._synthesize_chunk(text, output_path)
            return output_path

        # Synthesize paragraphs individually, then concatenate
        chunk_buffers: list[bytes] = []
        params = None  # (nchannels, sampwidth, framerate)

        for i, para in enumerate(paragraphs):
            buf = io.BytesIO()
            # Write to in-memory buffer via temp file
            tmp_path = output_path + f'.chunk_{i:04d}.wav'
            try:
                self._synthesize_chunk(para, tmp_path)
                with wave.open(tmp_path, 'rb') as wf:
                    if params is None:
                        params = wf.getparams()
                    chunk_buffers.append(wf.readframes(wf.getnframes()))
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            if (i + 1) % 10 == 0:
                print(f"   🔊 TTS progress: {i + 1}/{len(paragraphs)} paragraphs")

        # Concatenate all chunks into one WAV
        with wave.open(output_path, 'wb') as out:
            out.setparams(params)
            # Add a short silence between paragraphs (0.4s)
            silence = b'\x00' * int(params.framerate * params.sampwidth * 0.4)
            for i, frames in enumerate(chunk_buffers):
                out.writeframes(frames)
                if i < len(chunk_buffers) - 1:
                    out.writeframes(silence)

        return output_path

    def _synthesize_chunk(self, text: str, output_path: str):
        """Call piper executable to synthesize a single chunk."""
        cmd = [
            self._exe,
            '--model', self._voice,
            '--output_file', output_path,
        ]

        if self._speaker is not None:
            cmd.extend(['--speaker', str(self._speaker)])

        if self._speed != 1.0:
            cmd.extend(['--length_scale', str(1.0 / self._speed)])

        result = subprocess.run(
            cmd,
            input=text,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Piper failed (exit {result.returncode}): {result.stderr.strip()}"
            )
