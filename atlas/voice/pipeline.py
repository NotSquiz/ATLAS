"""
ATLAS Voice Pipeline

Push-to-talk conversation loop integrating:
- STT (Moonshine on CPU)
- LLM (Qwen2.5-3B-Instruct via Ollama)
- TTS (Kokoro on GPU)
- VAD (Silero for speech end detection)

Target: < 2 second end-to-end latency (achievable with Qwen2.5's no-thinking mode)
"""

import asyncio
import sys
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable, Optional

import numpy as np
import sounddevice as sd

from atlas.voice.stt import MoonshineSTT, FasterWhisperSTT, get_stt
from atlas.voice.tts import KokoroTTS, get_tts
from atlas.voice.vad import StreamingVAD, VADConfig, get_streaming_vad
from atlas.llm.local import OllamaClient, get_client
from atlas.llm.router import ATLASRouter, get_router, Tier

# Filler phrases for cloud latency masking (Lethal Gentleman persona)
FILLER_PHRASES = [
    "Let me see.",
    "One moment.",
    "Give me a moment.",
]

# Command words for interrupt detection
INTERRUPT_COMMANDS = ["stop", "wait", "quiet", "shush", "enough", "okay"]


@dataclass
class PipelineMetrics:
    """Timing metrics for voice pipeline."""
    request_id: str
    vad_end_time: float = 0.0
    stt_start_time: float = 0.0
    stt_end_time: float = 0.0
    llm_first_token_time: float = 0.0
    tts_first_audio_time: float = 0.0
    pipeline_end_time: float = 0.0

    @property
    def stt_duration_ms(self) -> float:
        """STT processing time in ms."""
        return (self.stt_end_time - self.stt_start_time) * 1000

    @property
    def time_to_first_token_ms(self) -> float:
        """Time from speech end to LLM first token."""
        return (self.llm_first_token_time - self.vad_end_time) * 1000

    @property
    def time_to_first_audio_ms(self) -> float:
        """Time from speech end to first TTS audio."""
        return (self.tts_first_audio_time - self.vad_end_time) * 1000

    @property
    def total_latency_ms(self) -> float:
        """Total pipeline latency in ms."""
        return (self.pipeline_end_time - self.vad_end_time) * 1000


@dataclass
class VoicePipelineConfig:
    """Configuration for voice pipeline."""

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 64  # 64ms chunks for VAD (Silero needs >= 32ms / 512 samples)

    # VAD settings (R11 optimized)
    vad_threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 400
    speech_pad_ms: int = 100

    # STT backend
    stt_backend: str = "moonshine"  # or "faster-whisper"

    # TTS settings
    tts_voice: str = "bm_lewis"  # British male per persona

    # LLM settings
    llm_model: str = "atlas-local"
    llm_max_tokens: int = 256  # Qwen2.5 has no thinking mode - all tokens for content
    llm_temperature: float = 0.7

    # Router settings
    use_router: bool = True  # Use hybrid router instead of local-only
    enable_filler_phrases: bool = True  # Speak filler when routing to cloud

    # Hot window settings
    hot_window_duration_s: float = 6.0  # Stay listening after TTS without wake word

    # System prompt for ATLAS persona (The Lethal Gentleman - R21)
    system_prompt: str = """You are ATLAS—a mentor who has seen much, speaks economically, means what you say, and trusts the user to handle truth. Your voice carries quiet authority from proven competence held in check.

Core principles:
- Speak with economy. Lead with shorter sentences for impact.
- Use precise Anglo-Saxon words over ornate Latinate alternatives.
- No hedging qualifiers: never "just", "maybe", "perhaps", "sort of".
- Understated confidence—don't announce your capabilities.
- Warm through action, not sentiment. Practical concern, not effusion.
- Challenge the work, not the person. Support effort, not ego.

Your responses will be spoken aloud. Keep them brief—1-3 sentences for simple queries. When something matters, say so directly."""


class VoicePipeline:
    """
    Push-to-talk voice conversation pipeline.

    Usage:
        pipeline = VoicePipeline()
        await pipeline.start()

        # Or run a single turn
        response = await pipeline.process_turn()
    """

    def __init__(self, config: Optional[VoicePipelineConfig] = None):
        """Initialize voice pipeline."""
        self.config = config or VoicePipelineConfig()

        # Initialize components (lazy-loaded)
        self._stt = None
        self._tts = None
        self._vad = None
        self._llm = None
        self._router = None

        # Audio state
        self._in_hot_window = False
        self._hot_window_end_time = 0.0
        self._audio_buffer: list[np.ndarray] = []
        self._is_recording = False
        self._stream = None

        # Metrics
        self._last_metrics: Optional[PipelineMetrics] = None

    @property
    def stt(self):
        """Get STT instance (lazy-loaded)."""
        if self._stt is None:
            self._stt = get_stt(self.config.stt_backend)
        return self._stt

    @property
    def tts(self):
        """Get TTS instance (lazy-loaded)."""
        if self._tts is None:
            self._tts = get_tts(self.config.tts_voice)
        return self._tts

    @property
    def vad(self):
        """Get VAD instance (lazy-loaded)."""
        if self._vad is None:
            vad_config = VADConfig(
                threshold=self.config.vad_threshold,
                min_speech_duration_ms=self.config.min_speech_duration_ms,
                min_silence_duration_ms=self.config.min_silence_duration_ms,
                speech_pad_ms=self.config.speech_pad_ms,
                sample_rate=self.config.sample_rate,
            )
            self._vad = get_streaming_vad(vad_config)
        return self._vad

    @property
    def llm(self):
        """Get LLM client (lazy-loaded)."""
        if self._llm is None:
            self._llm = get_client(model=self.config.llm_model)
        return self._llm

    @property
    def router(self):
        """Get hybrid router (lazy-loaded)."""
        if self._router is None:
            self._router = get_router(system_prompt=self.config.system_prompt)
        return self._router

    def _get_filler_phrase(self) -> str:
        """Get a random filler phrase for latency masking."""
        import random
        return random.choice(FILLER_PHRASES)

    def _is_interrupt_command(self, text: str) -> bool:
        """Check if text contains an interrupt command."""
        from difflib import SequenceMatcher
        text_lower = text.lower().strip()
        for cmd in INTERRUPT_COMMANDS:
            # Exact match
            if cmd in text_lower:
                return True
            # Fuzzy match for short utterances
            if len(text_lower) <= 10:
                ratio = SequenceMatcher(None, cmd, text_lower).ratio()
                if ratio > 0.7:
                    return True
        return False

    async def record_until_silence(self) -> np.ndarray:
        """
        Record audio until speech ends (VAD detects silence).

        Returns:
            Audio data as numpy array (16kHz mono float32)
        """
        self._audio_buffer = []
        self._is_recording = True
        self.vad.reset()

        chunk_samples = int(
            self.config.sample_rate * self.config.chunk_duration_ms / 1000
        )

        speech_audio = None

        def audio_callback(indata, frames, time_info, status):
            """Callback for audio input stream."""
            if status:
                print(f"Audio status: {status}", file=sys.stderr)

            # Convert to mono float32
            audio_chunk = indata[:, 0].copy().astype(np.float32)

            # Process with VAD
            result = self.vad.process_chunk(audio_chunk)

            if result.speech_started:
                print("Speech detected...", file=sys.stderr)

            if result.speech_ended:
                nonlocal speech_audio
                speech_audio = result.get_speech_audio()
                raise sd.CallbackStop()

            # Buffer audio while recording
            if self.vad.is_speaking():
                self._audio_buffer.append(audio_chunk)

        # Open input stream
        with sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype=np.float32,
            blocksize=chunk_samples,
            callback=audio_callback,
        ):
            print("Listening...", file=sys.stderr)
            while speech_audio is None:
                await asyncio.sleep(0.01)

        return speech_audio

    async def process_turn(self) -> str:
        """
        Process a single conversation turn.

        Records audio, transcribes, generates response, and speaks it.

        Returns:
            LLM response text
        """
        request_id = str(time.time())
        metrics = PipelineMetrics(request_id=request_id)

        # 1. Record audio until speech ends
        print("\n[Press Enter to speak, Ctrl+C to quit]")
        input()  # Wait for user to press Enter

        print("Recording... (speak now)")
        audio = await self.record_until_silence()
        metrics.vad_end_time = time.perf_counter()
        print(f"Captured {len(audio) / self.config.sample_rate:.1f}s of audio")

        # 2. Transcribe (STT on CPU)
        metrics.stt_start_time = time.perf_counter()
        transcription = self.stt.transcribe(audio, self.config.sample_rate)
        metrics.stt_end_time = time.perf_counter()

        user_text = transcription.text
        print(f"You: {user_text}")
        print(f"  [STT: {transcription.duration_ms:.0f}ms]")

        if not user_text.strip():
            print("No speech detected.")
            return ""

        # 3. Route query and generate response
        response_text = ""
        first_token = True
        sentence_buffer = ""
        was_interrupted = False

        # Classify the query to decide routing
        if self.config.use_router:
            decision = self.router.classify(user_text)
            tier = decision.tier
            print(f"  [Route: {tier.value}, conf: {decision.confidence:.2f}]")

            # Speak filler phrase if routing to cloud (masks latency)
            if self.config.enable_filler_phrases and tier != Tier.LOCAL:
                filler = self._get_filler_phrase()
                print(f"ATLAS: {filler}")
                await self._speak(filler)
                metrics.tts_first_audio_time = time.perf_counter()

        print("ATLAS: ", end="", flush=True)

        # Stream from router or direct LLM
        if self.config.use_router:
            stream = self.router.route_and_stream(
                user_text,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
        else:
            stream = self.llm.stream(
                user_text,
                system=self.config.system_prompt,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )

        async for token in stream:
            if first_token:
                metrics.llm_first_token_time = time.perf_counter()
                first_token = False

            response_text += token
            sentence_buffer += token
            print(token, end="", flush=True)

            # 4. Speak complete sentences immediately (streaming TTS)
            if sentence_buffer.rstrip().endswith(('.', '!', '?', ':')):
                if metrics.tts_first_audio_time == 0:
                    metrics.tts_first_audio_time = time.perf_counter()

                # Synthesize and play sentence (may be interrupted)
                was_interrupted = await self._speak_interruptible(sentence_buffer.strip())
                sentence_buffer = ""

                if was_interrupted:
                    print(" [interrupted]", end="")
                    break

        # Speak any remaining text (if not interrupted)
        if sentence_buffer.strip() and not was_interrupted:
            if metrics.tts_first_audio_time == 0:
                metrics.tts_first_audio_time = time.perf_counter()
            await self._speak_interruptible(sentence_buffer.strip())

        print()  # New line after response
        metrics.pipeline_end_time = time.perf_counter()

        # Log metrics
        self._last_metrics = metrics
        print(f"  [TTFA: {metrics.time_to_first_audio_ms:.0f}ms, "
              f"Total: {metrics.total_latency_ms:.0f}ms]")

        # Enter hot window mode (stay listening for follow-ups)
        self._in_hot_window = True
        self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s

        return response_text

    async def _wait_for_speech_or_timeout(self) -> Optional[np.ndarray]:
        """
        Wait for speech during hot window, or timeout.

        Returns:
            Audio data if speech detected, None if timeout
        """
        self._audio_buffer = []
        self.vad.reset()

        chunk_samples = int(
            self.config.sample_rate * self.config.chunk_duration_ms / 1000
        )

        speech_audio = None
        timed_out = False

        def audio_callback(indata, frames, time_info, status):
            nonlocal speech_audio, timed_out

            if time.perf_counter() > self._hot_window_end_time:
                timed_out = True
                raise sd.CallbackStop()

            audio_chunk = indata[:, 0].copy().astype(np.float32)
            result = self.vad.process_chunk(audio_chunk)

            if result.speech_started:
                print("Speech detected...", file=sys.stderr)

            if result.speech_ended:
                speech_audio = result.get_speech_audio()
                raise sd.CallbackStop()

            if self.vad.is_speaking():
                self._audio_buffer.append(audio_chunk)

        try:
            with sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=np.float32,
                blocksize=chunk_samples,
                callback=audio_callback,
            ):
                while speech_audio is None and not timed_out:
                    await asyncio.sleep(0.01)

        except sd.CallbackStop:
            pass

        return speech_audio

    async def _speak(self, text: str) -> None:
        """Synthesize and play text (blocking, no interrupt detection)."""
        if not text:
            return

        result = self.tts.synthesize(text)

        # Play audio
        sd.play(result.audio, result.sample_rate)
        sd.wait()

    async def _speak_interruptible(self, text: str) -> bool:
        """
        Synthesize and play text with interrupt command detection.

        Monitors microphone during playback for "stop", "wait", "quiet" commands.

        Args:
            text: Text to speak

        Returns:
            True if interrupted, False if completed normally
        """
        if not text:
            return False

        result = self.tts.synthesize(text)

        # Calculate audio duration
        audio_duration_s = len(result.audio) / result.sample_rate

        # Start playback
        sd.play(result.audio, result.sample_rate)

        # Monitor for interrupt commands during playback
        chunk_samples = int(self.config.sample_rate * 0.1)  # 100ms chunks
        interrupt_detected = False
        interrupt_buffer = []

        def audio_callback(indata, frames, time_info, status):
            nonlocal interrupt_detected, interrupt_buffer
            if status:
                pass  # Ignore status during interrupt monitoring

            # Accumulate audio for potential STT
            audio_chunk = indata[:, 0].copy().astype(np.float32)

            # Quick VAD check - is there speech?
            self.vad.reset()
            vad_result = self.vad.process_chunk(audio_chunk)

            if vad_result.speech_started or self.vad.is_speaking():
                interrupt_buffer.append(audio_chunk)

                # If we have enough audio, try to transcribe
                if len(interrupt_buffer) >= 3:  # ~300ms of audio
                    combined = np.concatenate(interrupt_buffer)

                    # Quick transcription check
                    try:
                        transcription = self.stt.transcribe(combined, self.config.sample_rate)
                        if self._is_interrupt_command(transcription.text):
                            interrupt_detected = True
                            sd.stop()  # Stop playback immediately
                            raise sd.CallbackStop()
                    except Exception:
                        pass  # Ignore transcription errors during interrupt check

                    # Reset buffer but keep last chunk for overlap
                    interrupt_buffer = interrupt_buffer[-1:]

        try:
            # Open input stream for interrupt monitoring
            with sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=np.float32,
                blocksize=chunk_samples,
                callback=audio_callback,
            ):
                # Wait for playback to complete or interrupt
                start_time = time.perf_counter()
                while time.perf_counter() - start_time < audio_duration_s:
                    if interrupt_detected:
                        break
                    await asyncio.sleep(0.05)

        except sd.CallbackStop:
            pass  # Expected when interrupted

        # Make sure playback is stopped
        sd.stop()

        return interrupt_detected

    async def start(self) -> None:
        """
        Start the voice pipeline conversation loop.

        Press Enter to speak, Ctrl+C to quit.
        Supports hot window mode - after ATLAS speaks, you can respond
        without pressing Enter for 6 seconds.
        """
        print("=" * 50)
        print("ATLAS Voice Pipeline")
        print("=" * 50)
        print(f"STT: {self.config.stt_backend}")
        print(f"TTS: Kokoro ({self.config.tts_voice})")
        print(f"LLM: {self.config.llm_model}")
        if self.config.use_router:
            print("Router: Enabled (LOCAL → HAIKU → AGENT_SDK)")
        print(f"Hot Window: {self.config.hot_window_duration_s}s")
        print("=" * 50)

        # Check components
        if not self.stt.is_available():
            print(f"Warning: STT backend '{self.config.stt_backend}' not available")

        if not self.tts.is_available():
            print("Warning: TTS (Kokoro) not available")

        if not self.llm.is_available():
            print("Warning: LLM (Ollama) not available")

        # Conversation loop with hot window support
        try:
            while True:
                if self._in_hot_window and time.perf_counter() < self._hot_window_end_time:
                    # Hot window active - listen without Enter
                    remaining = self._hot_window_end_time - time.perf_counter()
                    print(f"\n[Listening for {remaining:.1f}s... or press Enter]")

                    # Race: wait for speech OR Enter key OR timeout
                    audio = await self._wait_for_speech_or_timeout()

                    if audio is not None:
                        # Speech detected in hot window - process it
                        await self._process_audio(audio)
                    else:
                        # Hot window expired
                        self._in_hot_window = False
                        print("[Hot window expired]")
                else:
                    # Normal mode - wait for Enter
                    self._in_hot_window = False
                    await self.process_turn()

        except KeyboardInterrupt:
            print("\n\nGoodbye, sir.")

    async def _process_audio(self, audio: np.ndarray) -> str:
        """
        Process pre-recorded audio (used by hot window mode).

        Args:
            audio: Audio data from hot window capture

        Returns:
            LLM response text
        """
        request_id = str(time.time())
        metrics = PipelineMetrics(request_id=request_id)
        metrics.vad_end_time = time.perf_counter()

        print(f"Captured {len(audio) / self.config.sample_rate:.1f}s of audio")

        # Transcribe
        metrics.stt_start_time = time.perf_counter()
        transcription = self.stt.transcribe(audio, self.config.sample_rate)
        metrics.stt_end_time = time.perf_counter()

        user_text = transcription.text
        print(f"You: {user_text}")
        print(f"  [STT: {transcription.duration_ms:.0f}ms]")

        if not user_text.strip():
            print("No speech detected.")
            return ""

        # Check for interrupt command (shouldn't happen in hot window, but just in case)
        if self._is_interrupt_command(user_text):
            print("  [Interrupt command ignored in hot window]")
            return ""

        # Route and generate response (reuse logic from process_turn)
        response_text = ""
        first_token = True
        sentence_buffer = ""
        was_interrupted = False

        if self.config.use_router:
            decision = self.router.classify(user_text)
            tier = decision.tier
            print(f"  [Route: {tier.value}, conf: {decision.confidence:.2f}]")

            if self.config.enable_filler_phrases and tier != Tier.LOCAL:
                filler = self._get_filler_phrase()
                print(f"ATLAS: {filler}")
                await self._speak(filler)
                metrics.tts_first_audio_time = time.perf_counter()

        print("ATLAS: ", end="", flush=True)

        if self.config.use_router:
            stream = self.router.route_and_stream(
                user_text,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
        else:
            stream = self.llm.stream(
                user_text,
                system=self.config.system_prompt,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )

        async for token in stream:
            if first_token:
                metrics.llm_first_token_time = time.perf_counter()
                first_token = False

            response_text += token
            sentence_buffer += token
            print(token, end="", flush=True)

            if sentence_buffer.rstrip().endswith(('.', '!', '?', ':')):
                if metrics.tts_first_audio_time == 0:
                    metrics.tts_first_audio_time = time.perf_counter()

                was_interrupted = await self._speak_interruptible(sentence_buffer.strip())
                sentence_buffer = ""

                if was_interrupted:
                    print(" [interrupted]", end="")
                    break

        if sentence_buffer.strip() and not was_interrupted:
            if metrics.tts_first_audio_time == 0:
                metrics.tts_first_audio_time = time.perf_counter()
            await self._speak_interruptible(sentence_buffer.strip())

        print()
        metrics.pipeline_end_time = time.perf_counter()

        self._last_metrics = metrics
        print(f"  [TTFA: {metrics.time_to_first_audio_ms:.0f}ms, "
              f"Total: {metrics.total_latency_ms:.0f}ms]")

        # Reset hot window for next turn
        self._in_hot_window = True
        self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s

        return response_text

    def get_last_metrics(self) -> Optional[PipelineMetrics]:
        """Get metrics from the last conversation turn."""
        return self._last_metrics


class SimplePipeline:
    """
    Simplified pipeline for testing without push-to-talk.

    Processes text input directly without audio recording.
    """

    def __init__(self, config: Optional[VoicePipelineConfig] = None):
        """Initialize simple pipeline."""
        self.config = config or VoicePipelineConfig()
        self._tts = None
        self._llm = None

    @property
    def tts(self):
        """Get TTS instance."""
        if self._tts is None:
            self._tts = get_tts(self.config.tts_voice)
        return self._tts

    @property
    def llm(self):
        """Get LLM client."""
        if self._llm is None:
            self._llm = get_client(model=self.config.llm_model)
        return self._llm

    async def process_text(self, user_text: str) -> str:
        """
        Process text input and return spoken response.

        Args:
            user_text: User input text

        Returns:
            LLM response text
        """
        response_text = ""
        sentence_buffer = ""

        print(f"You: {user_text}")
        print("ATLAS: ", end="", flush=True)

        async for token in self.llm.stream(
            user_text,
            system=self.config.system_prompt,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
        ):
            response_text += token
            sentence_buffer += token
            print(token, end="", flush=True)

            # Speak complete sentences
            if sentence_buffer.rstrip().endswith(('.', '!', '?', ':')):
                result = self.tts.synthesize(sentence_buffer.strip())
                sd.play(result.audio, result.sample_rate)
                sd.wait()
                sentence_buffer = ""

        # Speak remaining text
        if sentence_buffer.strip():
            result = self.tts.synthesize(sentence_buffer.strip())
            sd.play(result.audio, result.sample_rate)
            sd.wait()

        print()
        return response_text

    async def start(self) -> None:
        """Start text-based conversation loop."""
        print("ATLAS Simple Pipeline (text mode)")
        print("Type 'quit' to exit\n")

        try:
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in ('quit', 'exit', 'q'):
                    break
                if user_input:
                    await self.process_text(user_input)
        except KeyboardInterrupt:
            pass

        print("\nGoodbye, sir.")


def main():
    """CLI entry point for voice pipeline."""
    asyncio.run(_async_main())


async def _async_main():
    """Async entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ATLAS Voice Pipeline")
    parser.add_argument(
        "--text-mode",
        action="store_true",
        help="Run in text mode (no audio)",
    )
    parser.add_argument(
        "--stt",
        choices=["moonshine", "faster-whisper"],
        default="moonshine",
        help="STT backend (default: moonshine)",
    )
    parser.add_argument(
        "--voice",
        default="bm_lewis",
        help="TTS voice (default: bm_lewis)",
    )

    args = parser.parse_args()

    config = VoicePipelineConfig(
        stt_backend=args.stt,
        tts_voice=args.voice,
    )

    if args.text_mode:
        pipeline = SimplePipeline(config)
    else:
        pipeline = VoicePipeline(config)

    await pipeline.start()


if __name__ == "__main__":
    main()
