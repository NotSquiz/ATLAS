"""
ATLAS Text-to-Speech Module

Kokoro TTS wrapper for GPU-based speech synthesis.
Uses bm_lewis voice (British male) per voice-persona.md.

Target latency: < 300ms to first audio (streaming)
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

import numpy as np


@dataclass
class SynthesisResult:
    """Result from TTS synthesis."""
    audio: np.ndarray
    sample_rate: int
    duration_ms: float
    text_length: int

    @property
    def audio_duration_s(self) -> float:
        """Duration of synthesized audio in seconds."""
        return len(self.audio) / self.sample_rate

    @property
    def realtime_factor(self) -> float:
        """Ratio of synthesis time to audio duration."""
        if self.audio_duration_s > 0:
            return (self.duration_ms / 1000) / self.audio_duration_s
        return 0.0


class KokoroTTS:
    """
    Kokoro Text-to-Speech wrapper.

    Uses Kokoro-82M ONNX model for high-quality TTS.
    Configured for ATLAS "Lethal Gentleman" persona with British male voice.

    Usage:
        tts = KokoroTTS()

        # Full synthesis
        result = tts.synthesize("Good morning, sir.")
        play_audio(result.audio, result.sample_rate)

        # Streaming synthesis
        for audio_chunk in tts.synthesize_stream("A longer response..."):
            play_audio(audio_chunk)
    """

    # Default paths for ATLAS models
    DEFAULT_MODEL_PATH = "/home/squiz/ATLAS/models/kokoro-v1.0.onnx"
    DEFAULT_VOICES_PATH = "/home/squiz/ATLAS/models/voices-v1.0.bin"

    # British male voice per voice-persona.md
    DEFAULT_VOICE = "bm_lewis"

    # Sample rate for Kokoro output
    SAMPLE_RATE = 24000

    def __init__(
        self,
        model_path: Optional[str] = None,
        voices_path: Optional[str] = None,
        voice: str = DEFAULT_VOICE,
        use_gpu: bool = True,
    ):
        """
        Initialize Kokoro TTS.

        Args:
            model_path: Path to kokoro-v1.0.onnx model
            voices_path: Path to voices-v1.0.bin
            voice: Voice ID (default: bm_lewis for British male)
            use_gpu: Whether to use GPU acceleration (default: True)
        """
        self.model_path = model_path or self.DEFAULT_MODEL_PATH
        self.voices_path = voices_path or self.DEFAULT_VOICES_PATH
        self.voice = voice
        self.use_gpu = use_gpu
        self._kokoro = None

    def _ensure_loaded(self) -> None:
        """Lazy-load the model on first use."""
        if self._kokoro is not None:
            return

        import os
        import logging
        from kokoro_onnx import Kokoro

        log = logging.getLogger(__name__)

        try:
            # Try GPU first if requested
            if self.use_gpu:
                try:
                    os.environ["ONNX_PROVIDER"] = "CUDAExecutionProvider"
                    self._kokoro = Kokoro(self.model_path, self.voices_path)
                    log.info("TTS initialized with CUDA GPU acceleration")
                    return
                except Exception as e:
                    log.warning(f"CUDA unavailable ({e}), falling back to CPU")

            # CPU fallback
            os.environ["ONNX_PROVIDER"] = "CPUExecutionProvider"
            self._kokoro = Kokoro(self.model_path, self.voices_path)
            log.info("TTS initialized with CPU (slower)")

        except ImportError as e:
            raise ImportError(
                "kokoro-onnx package not installed. "
                "Install with: pip install kokoro-onnx"
            ) from e
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Kokoro model files not found at {self.model_path} "
                f"or {self.voices_path}. Download them first."
            ) from e

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice: Voice ID (default: configured voice)
            speed: Speech speed multiplier (default: 1.0)

        Returns:
            SynthesisResult with audio data and metrics
        """
        self._ensure_loaded()

        voice = voice or self.voice
        start = time.perf_counter()

        # Synthesize
        audio, sample_rate = self._kokoro.create(
            text,
            voice=voice,
            speed=speed,
        )

        duration_ms = (time.perf_counter() - start) * 1000

        return SynthesisResult(
            audio=audio,
            sample_rate=sample_rate,
            duration_ms=duration_ms,
            text_length=len(text),
        )

    def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        chunk_size: int = 400,
    ) -> Iterator[np.ndarray]:
        """
        Stream synthesized audio in chunks for low latency.

        Per R11: chunksize=400 achieves ~300ms to first audio.

        Args:
            text: Text to synthesize
            voice: Voice ID (default: configured voice)
            speed: Speech speed multiplier
            chunk_size: Characters per chunk (default: 400)

        Yields:
            Audio chunks as numpy arrays (24kHz mono float32)
        """
        self._ensure_loaded()

        voice = voice or self.voice

        # Check if streaming is supported
        if hasattr(self._kokoro, 'create_stream'):
            # Use native streaming if available
            for audio_chunk in self._kokoro.create_stream(
                text,
                voice=voice,
                speed=speed,
            ):
                yield audio_chunk
        else:
            # Fall back to sentence-based chunking
            for chunk in self._chunk_text(text, chunk_size):
                audio, _ = self._kokoro.create(
                    chunk,
                    voice=voice,
                    speed=speed,
                )
                yield audio

    def _chunk_text(self, text: str, max_length: int = 400) -> Iterator[str]:
        """
        Split text into chunks at sentence boundaries.

        Args:
            text: Text to split
            max_length: Maximum characters per chunk

        Yields:
            Text chunks
        """
        import re

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    yield current_chunk.strip()
                current_chunk = sentence

        if current_chunk:
            yield current_chunk.strip()

    def list_voices(self) -> list[str]:
        """List available voice IDs."""
        self._ensure_loaded()

        if hasattr(self._kokoro, 'get_voices'):
            return self._kokoro.get_voices()

        # Known voices from Kokoro
        return [
            "af_bella",    # American female
            "af_nicole",   # American female
            "af_sarah",    # American female
            "af_sky",      # American female
            "am_adam",     # American male
            "am_michael",  # American male
            "bf_emma",     # British female
            "bf_isabella", # British female
            "bm_george",   # British male
            "bm_lewis",    # British male (ATLAS default)
        ]

    def is_available(self) -> bool:
        """Check if Kokoro TTS is available."""
        try:
            from kokoro_onnx import Kokoro
            return (
                Path(self.model_path).exists() and
                Path(self.voices_path).exists()
            )
        except ImportError:
            return False


def get_tts(voice: str = KokoroTTS.DEFAULT_VOICE) -> KokoroTTS:
    """
    Get TTS instance.

    Args:
        voice: Voice ID (default: bm_lewis)

    Returns:
        KokoroTTS instance
    """
    return KokoroTTS(voice=voice)
