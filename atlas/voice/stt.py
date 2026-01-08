"""
ATLAS Speech-to-Text Module

Moonshine STT wrapper for CPU-based transcription.
Per R25: STT runs on CPU to reserve GPU for LLM.

Target latency: < 700ms for typical utterance
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import numpy as np


@dataclass
class TranscriptionResult:
    """Result from STT transcription."""
    text: str
    duration_ms: float
    audio_duration_s: float

    @property
    def realtime_factor(self) -> float:
        """Ratio of processing time to audio duration."""
        if self.audio_duration_s > 0:
            return (self.duration_ms / 1000) / self.audio_duration_s
        return 0.0


class MoonshineSTT:
    """
    Moonshine Speech-to-Text wrapper.

    Uses Moonshine Base model on CPU for transcription.
    Designed for low-latency voice assistant use.

    Usage:
        stt = MoonshineSTT()

        # From file
        result = stt.transcribe("audio.wav")
        print(result.text)

        # From numpy array (16kHz mono)
        result = stt.transcribe(audio_array)
    """

    SAMPLE_RATE = 16000

    def __init__(self, model: str = "moonshine/base"):
        """
        Initialize Moonshine STT.

        Args:
            model: Model name - "moonshine/tiny" or "moonshine/base"
                   Base is recommended for better accuracy.
        """
        self.model_name = model
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self) -> None:
        """Lazy-load the model on first use."""
        if self._model is not None:
            return

        try:
            import moonshine
            from moonshine import load_model, load_tokenizer

            # Load model and tokenizer
            self._model = load_model(self.model_name)
            self._tokenizer = load_tokenizer()
        except ImportError as e:
            raise ImportError(
                "moonshine package not installed. "
                "Install with: pip install moonshine"
            ) from e

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        sample_rate: Optional[int] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio: Audio file path or numpy array (16kHz mono float32)
            sample_rate: Sample rate if audio is numpy array (default 16000)

        Returns:
            TranscriptionResult with text and timing metrics
        """
        self._ensure_loaded()

        import moonshine

        start = time.perf_counter()

        # Handle file path
        if isinstance(audio, (str, Path)):
            audio_path = str(audio)
            # Load audio file
            audio_data = moonshine.load_audio(audio_path, self.SAMPLE_RATE)
            audio_duration = len(audio_data) / self.SAMPLE_RATE
        else:
            # Assume numpy array
            audio_data = audio
            sr = sample_rate or self.SAMPLE_RATE
            audio_duration = len(audio_data) / sr

            # Resample if needed
            if sr != self.SAMPLE_RATE:
                audio_data = self._resample(audio_data, sr, self.SAMPLE_RATE)

        # Transcribe
        tokens = moonshine.transcribe(self._model, audio_data)
        text = self._tokenizer.decode_batch(tokens)[0]

        duration_ms = (time.perf_counter() - start) * 1000

        return TranscriptionResult(
            text=text.strip(),
            duration_ms=duration_ms,
            audio_duration_s=audio_duration,
        )

    def transcribe_streaming(
        self,
        audio_chunks: list[np.ndarray],
    ) -> TranscriptionResult:
        """
        Transcribe streaming audio chunks.

        Args:
            audio_chunks: List of audio chunks (16kHz mono float32)

        Returns:
            TranscriptionResult for combined audio
        """
        # Concatenate chunks
        audio = np.concatenate(audio_chunks)
        return self.transcribe(audio)

    def _resample(
        self,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int,
    ) -> np.ndarray:
        """Resample audio to target sample rate."""
        if orig_sr == target_sr:
            return audio

        # Simple linear interpolation resampling
        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)
        indices = np.linspace(0, len(audio) - 1, target_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    def is_available(self) -> bool:
        """Check if Moonshine is available."""
        try:
            import moonshine
            return True
        except ImportError:
            return False


# Alternative: faster-whisper backend (already installed)
class FasterWhisperSTT:
    """
    Alternative STT using faster-whisper.

    Use this if Moonshine has issues or for better accuracy.
    Note: faster-whisper can use GPU, but we force CPU per R25.
    """

    SAMPLE_RATE = 16000

    def __init__(self, model: str = "base.en"):
        """
        Initialize faster-whisper STT.

        Args:
            model: Model name - "tiny.en", "base.en", "small.en"
        """
        self.model_name = model
        self._model = None

    def _ensure_loaded(self) -> None:
        """Lazy-load the model on first use."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        # Force CPU to reserve GPU for LLM (R25)
        self._model = WhisperModel(
            self.model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
        )

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        sample_rate: Optional[int] = None,
    ) -> TranscriptionResult:
        """Transcribe audio to text."""
        self._ensure_loaded()

        start = time.perf_counter()

        # Handle input type
        if isinstance(audio, (str, Path)):
            audio_path = str(audio)
            # Get duration from file
            import soundfile as sf
            info = sf.info(audio_path)
            audio_duration = info.duration
            audio_input = audio_path
        else:
            sr = sample_rate or self.SAMPLE_RATE
            audio_duration = len(audio) / sr
            audio_input = audio

        # Transcribe with optimized settings (R11)
        # Note: Removed initial_prompt - it was biasing transcription
        # ("ATLAS" caused "Who are you" → "To all you")

        # Add silence padding to prevent first-word cutoff
        silence_pad = np.zeros(int(0.1 * self.SAMPLE_RATE), dtype=np.float32)
        if isinstance(audio_input, np.ndarray):
            audio_input = np.concatenate([silence_pad, audio_input])

        segments, _ = self._model.transcribe(
            audio_input,
            beam_size=1,  # Greedy decoding for speed
            language="en",
            vad_filter=False,  # Disabled - user controls start/stop via Enter key
            condition_on_previous_text=False,
            word_timestamps=False,
        )

        # Collect text
        text = " ".join(segment.text for segment in segments)
        duration_ms = (time.perf_counter() - start) * 1000

        return TranscriptionResult(
            text=text.strip(),
            duration_ms=duration_ms,
            audio_duration_s=audio_duration,
        )

    def is_available(self) -> bool:
        """Check if faster-whisper is available."""
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False


def get_stt(
    backend: str = "moonshine",
    model: str = "base.en",
) -> Union[MoonshineSTT, FasterWhisperSTT]:
    """
    Get STT instance with specified backend.

    Args:
        backend: "moonshine" or "faster-whisper"
        model: For faster-whisper: "tiny.en", "base.en", "small.en", "medium.en"

    Returns:
        STT instance
    """
    if backend == "moonshine":
        return MoonshineSTT()
    elif backend == "faster-whisper":
        return FasterWhisperSTT(model=model)
    else:
        raise ValueError(f"Unknown STT backend: {backend}")
