"""
ATLAS Voice Activity Detection Module

Silero VAD wrapper for detecting speech in audio.
Per R11: < 1ms per 30ms chunk processing overhead.

Configuration optimized for conversational turn-taking (R11):
- threshold: 0.5 (increase to 0.6-0.7 in noisy environments)
- min_speech_duration_ms: 250 (filter short noise bursts)
- min_silence_duration_ms: 400 (balance responsiveness vs clipping)
- speech_pad_ms: 100 (prevent clipping utterance edges)
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

import numpy as np


@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection."""

    # Speech detection threshold (0.0-1.0)
    # Higher = fewer false positives, may miss quiet speech
    threshold: float = 0.5

    # Minimum speech duration to register (ms)
    # Filters out short noise bursts
    min_speech_duration_ms: int = 250

    # Silence duration to end speech (ms)
    # Main tuning lever for responsiveness
    min_silence_duration_ms: int = 400

    # Padding around speech (ms)
    # Prevents clipping utterance edges
    speech_pad_ms: int = 100

    # Sample rate for VAD processing
    sample_rate: int = 16000


@dataclass
class SpeechSegment:
    """Detected speech segment."""
    start_ms: float
    end_ms: float
    audio: np.ndarray

    @property
    def duration_ms(self) -> float:
        """Duration of speech segment in milliseconds."""
        return self.end_ms - self.start_ms


class SileroVAD:
    """
    Silero VAD wrapper for voice activity detection.

    Detects speech in audio stream and determines when
    the user has finished speaking.

    Usage:
        vad = SileroVAD()

        # Check if chunk contains speech
        is_speech = vad.is_speech(audio_chunk)

        # Detect speech segments in audio
        for segment in vad.detect_segments(audio):
            process(segment.audio)

        # Process streaming audio
        for result in vad.process_stream(audio_iterator):
            if result.speech_ended:
                transcribe(result.audio)
    """

    SAMPLE_RATE = 16000
    CHUNK_MS = 30  # Silero processes 30ms chunks

    def __init__(self, config: Optional[VADConfig] = None):
        """
        Initialize Silero VAD.

        Args:
            config: VAD configuration (default: R11 optimized settings)
        """
        self.config = config or VADConfig()
        self._model = None
        self._get_speech_timestamps = None

    def _ensure_loaded(self) -> None:
        """Lazy-load the model on first use."""
        if self._model is not None:
            return

        try:
            from silero_vad import load_silero_vad, get_speech_timestamps

            self._model = load_silero_vad()
            self._get_speech_timestamps = get_speech_timestamps
        except ImportError as e:
            raise ImportError(
                "silero-vad package not installed. "
                "Install with: pip install silero-vad"
            ) from e

    def is_speech(self, audio: np.ndarray) -> bool:
        """
        Check if audio chunk contains speech.

        Args:
            audio: Audio chunk (16kHz mono float32, ~30ms)

        Returns:
            True if speech detected above threshold
        """
        self._ensure_loaded()

        # Convert numpy array to PyTorch tensor (Silero VAD requires tensor input)
        import torch
        audio_tensor = torch.from_numpy(audio)

        # Get speech probability
        prob = self._model(
            audio_tensor,
            self.config.sample_rate,
        ).item()

        return prob > self.config.threshold

    def get_speech_probability(self, audio: np.ndarray) -> float:
        """
        Get speech probability for audio chunk.

        Args:
            audio: Audio chunk (16kHz mono float32)

        Returns:
            Speech probability (0.0-1.0)
        """
        self._ensure_loaded()

        # Convert numpy array to PyTorch tensor (Silero VAD requires tensor input)
        import torch
        audio_tensor = torch.from_numpy(audio)

        return self._model(
            audio_tensor,
            self.config.sample_rate,
        ).item()

    def detect_segments(
        self,
        audio: np.ndarray,
    ) -> list[SpeechSegment]:
        """
        Detect speech segments in audio.

        Args:
            audio: Full audio (16kHz mono float32)

        Returns:
            List of detected speech segments
        """
        self._ensure_loaded()

        import torch

        # Convert to torch tensor if needed
        if isinstance(audio, np.ndarray):
            audio_tensor = torch.from_numpy(audio).float()
        else:
            audio_tensor = audio

        # Get speech timestamps
        timestamps = self._get_speech_timestamps(
            audio_tensor,
            self._model,
            sampling_rate=self.config.sample_rate,
            threshold=self.config.threshold,
            min_speech_duration_ms=self.config.min_speech_duration_ms,
            min_silence_duration_ms=self.config.min_silence_duration_ms,
            speech_pad_ms=self.config.speech_pad_ms,
        )

        segments = []
        for ts in timestamps:
            start_sample = ts['start']
            end_sample = ts['end']

            start_ms = (start_sample / self.config.sample_rate) * 1000
            end_ms = (end_sample / self.config.sample_rate) * 1000

            segment_audio = audio[start_sample:end_sample]

            segments.append(SpeechSegment(
                start_ms=start_ms,
                end_ms=end_ms,
                audio=segment_audio,
            ))

        return segments

    def reset(self) -> None:
        """Reset VAD state for new conversation."""
        self._ensure_loaded()

        if hasattr(self._model, 'reset_states'):
            self._model.reset_states()

    def is_available(self) -> bool:
        """Check if Silero VAD is available."""
        try:
            from silero_vad import load_silero_vad
            return True
        except ImportError:
            return False


class StreamingVAD:
    """
    Streaming VAD for real-time speech detection.

    Processes audio in real-time and signals when speech ends.

    Usage:
        vad = StreamingVAD()

        # In audio callback
        def on_audio(chunk):
            result = vad.process_chunk(chunk)
            if result.speech_ended:
                audio = result.get_speech_audio()
                transcribe(audio)
    """

    def __init__(self, config: Optional[VADConfig] = None):
        """Initialize streaming VAD."""
        self.config = config or VADConfig()
        self.vad = SileroVAD(config)

        self._audio_buffer: list[np.ndarray] = []
        self._is_speaking = False
        self._silence_samples = 0
        self._speech_samples = 0

        # Circular buffer for pre-speech audio (~300ms at 64ms chunks = 5 chunks)
        # This captures audio before VAD triggers, preventing word cutoff
        self._prespeech_buffer: deque[np.ndarray] = deque(maxlen=5)

    @dataclass
    class ProcessResult:
        """Result from processing an audio chunk."""
        is_speech: bool
        speech_started: bool
        speech_ended: bool
        probability: float
        audio_buffer: Optional[np.ndarray] = None

        def get_speech_audio(self) -> Optional[np.ndarray]:
            """Get accumulated speech audio if speech ended."""
            return self.audio_buffer

    def process_chunk(self, audio: np.ndarray) -> ProcessResult:
        """
        Process an audio chunk for speech detection.

        Args:
            audio: Audio chunk (16kHz mono float32)

        Returns:
            ProcessResult indicating speech state
        """
        prob = self.vad.get_speech_probability(audio)
        is_speech = prob > self.config.threshold

        speech_started = False
        speech_ended = False
        audio_buffer = None

        samples_per_ms = self.config.sample_rate / 1000

        if is_speech:
            # Speech detected
            self._silence_samples = 0
            self._speech_samples += len(audio)

            # On first speech detection, prepend recent audio from circular buffer
            # This recovers audio that was recorded before VAD triggered
            if not self._audio_buffer and self._prespeech_buffer:
                self._audio_buffer.extend(self._prespeech_buffer)
                self._prespeech_buffer.clear()

            self._audio_buffer.append(audio)

            if not self._is_speaking:
                # Check if enough speech to start
                speech_ms = self._speech_samples / samples_per_ms
                if speech_ms >= self.config.min_speech_duration_ms:
                    self._is_speaking = True
                    speech_started = True
        else:
            # Silence detected
            if self._is_speaking:
                self._silence_samples += len(audio)
                self._audio_buffer.append(audio)  # Keep for padding

                # Check if enough silence to end
                silence_ms = self._silence_samples / samples_per_ms
                if silence_ms >= self.config.min_silence_duration_ms:
                    speech_ended = True
                    audio_buffer = np.concatenate(self._audio_buffer)
                    self.reset()
            else:
                # Maintain rolling pre-speech buffer instead of discarding
                # This allows us to recover audio before VAD triggers
                self._prespeech_buffer.append(audio)
                self._speech_samples = 0

        return self.ProcessResult(
            is_speech=is_speech,
            speech_started=speech_started,
            speech_ended=speech_ended,
            probability=prob,
            audio_buffer=audio_buffer,
        )

    def reset(self) -> None:
        """Reset streaming state for new utterance."""
        self._audio_buffer = []
        self._is_speaking = False
        self._silence_samples = 0
        self._speech_samples = 0
        self._prespeech_buffer.clear()
        self.vad.reset()

    def is_speaking(self) -> bool:
        """Check if currently detecting speech."""
        return self._is_speaking


def get_vad(config: Optional[VADConfig] = None) -> SileroVAD:
    """
    Get VAD instance.

    Args:
        config: VAD configuration

    Returns:
        SileroVAD instance
    """
    return SileroVAD(config)


def get_streaming_vad(config: Optional[VADConfig] = None) -> StreamingVAD:
    """
    Get streaming VAD instance.

    Args:
        config: VAD configuration

    Returns:
        StreamingVAD instance
    """
    return StreamingVAD(config)
