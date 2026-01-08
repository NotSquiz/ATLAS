"""
ATLAS Voice Module

Voice pipeline components for speech-to-text, text-to-speech,
and voice activity detection.

Architecture (from R11/R25):
- STT: Moonshine Base on CPU (reserve GPU for LLM)
- TTS: Kokoro-82M on GPU (streaming)
- VAD: Silero VAD v6.2

Target latency: < 3 seconds end-to-end
"""

from atlas.voice.stt import MoonshineSTT
from atlas.voice.tts import KokoroTTS
from atlas.voice.vad import SileroVAD
from atlas.voice.pipeline import VoicePipeline

__all__ = [
    "MoonshineSTT",
    "KokoroTTS",
    "SileroVAD",
    "VoicePipeline",
]
