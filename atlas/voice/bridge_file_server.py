#!/usr/bin/env python3
"""
ATLAS Audio Bridge Server - WSL2 Side (File-based)

This version uses file-based communication instead of sockets,
which avoids WSL2 networking issues entirely.

Usage:
    cd /home/squiz/ATLAS
    source venv/bin/activate
    ANTHROPIC_API_KEY="$(cat .env | tr -d '\\n')" python -m atlas.voice.bridge_file_server
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# Import ATLAS components
from atlas.voice.stt import get_stt
from atlas.voice.tts import get_tts
from atlas.llm.router import get_router, Tier
from atlas.llm.local import get_client

# Configuration
BRIDGE_DIR = Path.home() / "ATLAS" / ".bridge"
AUDIO_IN_FILE = BRIDGE_DIR / "audio_in.raw"
AUDIO_OUT_FILE = BRIDGE_DIR / "audio_out.raw"
METADATA_FILE = BRIDGE_DIR / "metadata.txt"  # Contains sample rate for playback
COMMAND_FILE = BRIDGE_DIR / "command.txt"
STATUS_FILE = BRIDGE_DIR / "status.txt"
SAMPLE_RATE_IN = 16000  # Input audio from Windows mic
# TTS sample rate determined at runtime (Kokoro uses 24000)

# Launcher integration files
VOICE_FILE = BRIDGE_DIR / "voice.txt"
SESSION_STATUS_FILE = BRIDGE_DIR / "session_status.json"


SYSTEM_PROMPT = """
STRICT RULES (NEVER BREAK):
1. You ARE Atlas. Never say "I am Claude" or mention Anthropic.
2. Maximum 20 words. Count them. Stop at 20.
3. One sentence preferred. Two max.
4. No lists, no markdown, no asterisks.

WHO YOU ARE:
You are ATLAS - a voice assistant I built. You run locally on my Windows/WSL2 machine
in the /home/squiz/ATLAS repository. You use Whisper (STT), Kokoro (TTS), and an LLM brain.
We are building you together. You know this.

YOUR VOICE:
Terse. Direct. No filler words. Dry wit.
Speak like a mentor who has seen much and wastes no words.
"""


class BridgeFileServer:
    """WSL2 server that processes audio via file-based communication."""

    def __init__(self):
        print("Loading ATLAS components...", flush=True)
        # Use faster-whisper since moonshine API changed
        # base.en is 2-3x faster than small.en, good accuracy for voice
        self.stt = get_stt("faster-whisper", model="base.en")
        self.current_voice = self._read_voice_preference()
        self.tts = get_tts(self.current_voice)
        self.router = get_router(system_prompt=SYSTEM_PROMPT)
        self.llm = get_client()
        self._session_cost = 0.0  # Track session cost for launcher

        # Preload models to eliminate first-request latency
        print("  Preloading STT model...", flush=True)
        self.stt._ensure_loaded()
        print("  Preloading TTS model...", flush=True)
        self.tts._ensure_loaded()
        print("  Preloading router embeddings...", flush=True)
        self.router._get_embedder()

        print("Components loaded and ready.", flush=True)

    def setup(self):
        """Create bridge directory and files."""
        BRIDGE_DIR.mkdir(exist_ok=True)
        # Clear old files
        for f in [AUDIO_IN_FILE, AUDIO_OUT_FILE, COMMAND_FILE, STATUS_FILE]:
            if f.exists():
                f.unlink()
        print(f"Bridge directory: {BRIDGE_DIR}")

    def write_status(self, status: str):
        """Write status to file."""
        STATUS_FILE.write_text(status)

    def read_command(self) -> str:
        """Read and clear command file."""
        try:
            cmd = COMMAND_FILE.read_text().strip()
            COMMAND_FILE.unlink()
            return cmd
        except FileNotFoundError:
            return ""

    def write_metadata(self, sample_rate: int):
        """Write audio metadata for Windows client."""
        METADATA_FILE.write_text(f"sample_rate={sample_rate}")

    def _read_voice_preference(self) -> str:
        """Read voice preference from file (for launcher integration)."""
        if VOICE_FILE.exists():
            v = VOICE_FILE.read_text().strip()
            if v in ["bf_emma", "bm_lewis"]:
                return v
        return "bm_lewis"  # default

    def _write_session_status(
        self, tier: str, confidence: float, cost: float = 0.0,
        user_text: str = "", atlas_response: str = "",
        stt_ms: float = 0, tts_ms: float = 0
    ):
        """Write session status JSON for Windows launcher."""
        self._session_cost += cost
        status = {
            "last_cost": cost,
            "session_cost": self._session_cost,
            "routing": {"tier": tier, "confidence": confidence},
            "updated_at": time.strftime("%H:%M:%S"),
            "last_exchange": {
                "user": user_text,
                "atlas": atlas_response
            },
            "timing": {
                "stt_ms": int(stt_ms),
                "tts_ms": int(tts_ms)
            },
            "gpu": "CUDA" if self.tts.use_gpu else "CPU"
        }
        SESSION_STATUS_FILE.write_text(json.dumps(status, indent=2))

    def process_audio(self):
        """Process audio file through ATLAS pipeline."""
        # Read audio
        audio = np.fromfile(AUDIO_IN_FILE, dtype=np.float32)
        AUDIO_IN_FILE.unlink()

        print(f"\nProcessing {len(audio) / SAMPLE_RATE_IN:.1f}s of audio...")

        # STT
        start = time.perf_counter()
        transcription = self.stt.transcribe(audio, SAMPLE_RATE_IN)
        stt_time = (time.perf_counter() - start) * 1000
        print(f"You: {transcription.text}")
        print(f"  [STT: {stt_time:.0f}ms]")

        if not transcription.text.strip():
            print("  [No speech detected]")
            self.write_status("DONE")
            return

        # Route
        decision = self.router.classify(transcription.text)
        print(f"  [Route: {decision.tier.value}, conf: {decision.confidence:.2f}]")

        # Collect all audio to send back
        all_audio = []
        tts_sample_rate = 24000  # Will be updated by actual TTS output
        tts_time = 0  # Track TTS timing for launcher

        # Generate response
        print("ATLAS: ", end="", flush=True)
        response_text = ""

        async def get_response():
            nonlocal response_text
            async for token in self.router.route_and_stream(
                transcription.text,
                temperature=0.7,
                max_tokens=100,  # Keep responses short for voice
            ):
                response_text += token
                print(token, end="", flush=True)

        asyncio.run(get_response())
        print()

        # TTS for response - check for voice preference change
        if response_text.strip():
            new_voice = self._read_voice_preference()
            if new_voice != self.current_voice:
                print(f"  [Voice changed: {self.current_voice} -> {new_voice}]")
                self.current_voice = new_voice
                self.tts = get_tts(new_voice)
                self.tts._ensure_loaded()

            start = time.perf_counter()
            result = self.tts.synthesize(response_text)
            tts_time = (time.perf_counter() - start) * 1000
            tts_sample_rate = result.sample_rate
            print(f"  [TTS: {tts_time:.0f}ms, {tts_sample_rate}Hz]")
            all_audio.append(result.audio)

        # Write combined audio to output file with metadata
        if all_audio:
            combined = np.concatenate(all_audio)
            # Add 200ms silence tail to prevent audio cutoff during playback
            silence_tail = np.zeros(int(0.2 * tts_sample_rate), dtype=np.float32)
            combined = np.concatenate([combined, silence_tail])
            combined.astype(np.float32).tofile(AUDIO_OUT_FILE)
            self.write_metadata(tts_sample_rate)  # Tell Windows the correct sample rate
            print(f"  [Response: {len(combined) / tts_sample_rate:.1f}s audio @ {tts_sample_rate}Hz]")

        # Write session status for Windows launcher
        self._write_session_status(
            tier=decision.tier.value,
            confidence=decision.confidence,
            cost=0.0,  # LOCAL is free; HAIKU cost tracked separately by router
            user_text=transcription.text,
            atlas_response=response_text,
            stt_ms=stt_time,
            tts_ms=tts_time
        )

        self.write_status("DONE")

    def run(self):
        """Main loop."""
        self.setup()

        print("\n" + "=" * 50)
        print("ATLAS Bridge Server (File-based)")
        print("=" * 50)
        print("Waiting for Windows client...")
        print("=" * 50 + "\n")

        try:
            while True:
                cmd = self.read_command()

                if cmd == "PING":
                    print("[PING received]")
                    self.write_status("PONG")

                elif cmd == "PROCESS":
                    if AUDIO_IN_FILE.exists():
                        self.process_audio()
                    else:
                        print("[PROCESS but no audio file]")
                        self.write_status("DONE")

                elif cmd == "QUIT":
                    print("[QUIT received]")
                    break

                time.sleep(0.1)  # Poll every 100ms

        except KeyboardInterrupt:
            print("\n\nShutting down...")


def main():
    server = BridgeFileServer()
    server.run()


if __name__ == "__main__":
    main()
