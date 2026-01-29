"""
ATLAS Qwen3-TTS Module

Qwen3-TTS wrapper with voice cloning support for Jeremy Irons voice.
Uses the Qwen3-TTS-12Hz-0.6B-Base model with ICL (In-Context Learning) mode
for high-quality voice cloning from reference audio + transcript.

Target latency: < 500ms to first audio
"""

import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


logger = logging.getLogger(__name__)


@dataclass
class SynthesisResult:
    """Result from TTS synthesis (compatible with Kokoro interface)."""
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


class Qwen3TTS:
    """
    Qwen3 Text-to-Speech wrapper with voice cloning.

    Uses Qwen3-TTS Base model for ICL voice cloning with reference audio + transcript.
    Optimized for ATLAS "Lethal Gentleman" persona with Jeremy Irons voice clone.

    Usage:
        tts = Qwen3TTS(voice="jeremy_irons")
        result = tts.synthesize("Good morning, sir.")
        play_audio(result.audio, result.sample_rate)
    """

    # Model ID for voice cloning (Base model supports ICL cloning)
    MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"

    # Voice configurations with reference audio and transcript for ICL mode
    VOICE_CONFIGS = {
        "jeremy_irons": {
            "ref_audio": "/home/squiz/ATLAS/config/voice/jeremy_irons.wav",
            "ref_text": "I became an actor to be a rogue and a vagabond, which is how we used to call actors in England, not to be a knob, which is what we call the aristocrats.",
        },
    }

    # Built-in speakers (from CustomVoice model - fallback only)
    BUILTIN_SPEAKERS = ["aiden", "dylan", "eric", "ryan", "serena", "vivian", "ono_anna", "sohee", "uncle_fu"]

    # Default output sample rate
    SAMPLE_RATE = 24000

    def __init__(
        self,
        voice: str = "jeremy_irons",
        use_gpu: bool = True,
    ):
        """
        Initialize Qwen3 TTS.

        Args:
            voice: Voice ID - 'jeremy_irons' or builtin speaker name
            use_gpu: Whether to use GPU acceleration (default: True)
        """
        self.voice = voice
        self.use_gpu = use_gpu
        self._model = None
        self._voice_config = None

    def _ensure_loaded(self) -> None:
        """Lazy-load the model on first use."""
        if self._model is not None:
            return

        try:
            from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel
            import torch

            logger.info(f"Loading Qwen3-TTS model: {self.MODEL_ID}")

            # Load model with GPU if available
            device = "cuda" if self.use_gpu and torch.cuda.is_available() else "cpu"
            self._model = Qwen3TTSModel.from_pretrained(self.MODEL_ID)
            # Note: model.to(device) may not work - Qwen3TTSModel handles device internally

            # Load voice config for cloning if available
            if self.voice in self.VOICE_CONFIGS:
                config = self.VOICE_CONFIGS[self.voice]
                ref_path = Path(config["ref_audio"])
                if ref_path.exists():
                    logger.info(f"Loading voice config: {self.voice}")
                    self._voice_config = config
                else:
                    logger.warning(f"Reference audio not found: {ref_path}")
                    self._voice_config = None

            logger.info(f"Qwen3-TTS initialized on {device}")

        except ImportError as e:
            raise ImportError(
                "qwen-tts package not installed. "
                "Install with: pip install qwen-tts"
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

        # Determine synthesis method based on voice type
        if voice in self.VOICE_CONFIGS and self._voice_config:
            # Voice cloning with reference audio + transcript (ICL mode)
            audio, sample_rate = self._synthesize_cloned(text, speed)
        elif voice in self.BUILTIN_SPEAKERS:
            # Use builtin speaker (requires CustomVoice model - may fail with Base)
            audio, sample_rate = self._synthesize_builtin(text, voice, speed)
        else:
            # Fall back to x-vector mode cloning (no transcript needed)
            logger.warning(f"Unknown voice '{voice}', using x-vector mode")
            audio, sample_rate = self._synthesize_xvector(text, speed)

        duration_ms = (time.perf_counter() - start) * 1000

        # Ensure audio is 1D numpy array
        if isinstance(audio, (list, tuple)):
            audio = audio[0]
        if hasattr(audio, 'cpu'):
            audio = audio.cpu().numpy()
        audio = np.array(audio, dtype=np.float32).flatten()

        return SynthesisResult(
            audio=audio,
            sample_rate=sample_rate,
            duration_ms=duration_ms,
            text_length=len(text),
        )

    def _synthesize_cloned(self, text: str, speed: float) -> tuple:
        """Synthesize using voice cloning with reference audio + transcript (ICL mode)."""
        try:
            audio, sr = self._model.generate_voice_clone(
                text=text,
                ref_audio=self._voice_config["ref_audio"],
                ref_text=self._voice_config["ref_text"],
                language="english",
            )
            return audio, sr
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}, falling back to x-vector mode")
            return self._synthesize_xvector(text, speed)

    def _synthesize_xvector(self, text: str, speed: float) -> tuple:
        """Synthesize using x-vector mode (no transcript needed)."""
        try:
            # Use first available voice config for reference audio
            if self._voice_config:
                ref_audio = self._voice_config["ref_audio"]
            else:
                ref_audio = list(self.VOICE_CONFIGS.values())[0]["ref_audio"]

            audio, sr = self._model.generate_voice_clone(
                text=text,
                ref_audio=ref_audio,
                x_vector_only_mode=True,
                language="english",
            )
            return audio, sr
        except Exception as e:
            logger.error(f"X-vector synthesis failed: {e}")
            raise

    def _synthesize_builtin(self, text: str, speaker: str, speed: float) -> tuple:
        """Synthesize using builtin speaker (requires CustomVoice model)."""
        # Note: This only works with CustomVoice model, not Base model
        audio, sr = self._model.generate_custom_voice(
            text=text,
            speaker=speaker,
            language="english",
        )
        return audio, sr

    def list_voices(self) -> list[str]:
        """List available voice IDs."""
        # Return cloned voices (builtin speakers require different model)
        return list(self.VOICE_CONFIGS.keys())

    def is_available(self) -> bool:
        """Check if Qwen3 TTS is available."""
        try:
            from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel
            return True
        except ImportError:
            return False


def get_qwen_tts(voice: str = "jeremy_irons") -> Qwen3TTS:
    """
    Get Qwen3 TTS instance.

    Args:
        voice: Voice ID (default: jeremy_irons)

    Returns:
        Qwen3TTS instance
    """
    return Qwen3TTS(voice=voice)
