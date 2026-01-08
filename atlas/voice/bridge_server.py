#!/usr/bin/env python3
"""
ATLAS Audio Bridge Server - WSL2 Side

This server receives audio from Windows, processes it through the ATLAS pipeline,
and returns TTS audio. Run this in WSL2 before starting the Windows client.

Usage:
    cd /home/squiz/ATLAS
    source venv/bin/activate
    ANTHROPIC_API_KEY="$(cat .env | tr -d '\\n')" python -m atlas.voice.bridge_server

Architecture:
    Windows (audio capture) -> Socket -> WSL2 (STT -> Router -> LLM -> TTS) -> Socket -> Windows (playback)
"""

import asyncio
import socket
import struct
import sys
import time
from typing import Optional

import numpy as np

# Import ATLAS components
from atlas.voice.stt import get_stt
from atlas.voice.tts import get_tts
from atlas.voice.vad import StreamingVAD, VADConfig
from atlas.llm.router import get_router, Tier
from atlas.llm.local import get_client

# Configuration
HOST = "0.0.0.0"  # Listen on all interfaces (accessible from Windows)
PORT = 9999
SAMPLE_RATE = 16000

# Filler phrases for cloud latency masking
FILLER_PHRASES = [
    "Let me see.",
    "One moment.",
    "Give me a moment.",
]

# System prompt (Lethal Gentleman)
SYSTEM_PROMPT = """You are ATLAS, a refined AI assistant. Speak economically - lead with shorter sentences, avoid hedging qualifiers. Your responses should be brief (1-3 sentences for simple queries) and direct. You have understated confidence and practical concern for the user's wellbeing."""


class BridgeServer:
    """WSL2 server that processes audio from Windows."""

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.server_socket = None

        # Initialize components
        print("Loading ATLAS components...")
        self.stt = get_stt("moonshine")
        self.tts = get_tts("bm_lewis")
        self.router = get_router()
        self.llm = get_client()
        self.vad = StreamingVAD(VADConfig())
        self._filler_index = 0
        print("Components loaded.")

    def _get_filler_phrase(self) -> str:
        """Get next filler phrase (round-robin)."""
        phrase = FILLER_PHRASES[self._filler_index % len(FILLER_PHRASES)]
        self._filler_index += 1
        return phrase

    def start(self):
        """Start the server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

        print(f"\nATLAS Bridge Server listening on {self.host}:{self.port}")
        print("Waiting for Windows client connection...")

        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"Client connected from {addr}")
                self.handle_client(client_socket)
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
            finally:
                if client_socket:
                    client_socket.close()

        self.server_socket.close()

    def handle_client(self, client_socket: socket.socket):
        """Handle a connected client."""
        audio_buffer = []
        recording = False

        try:
            while True:
                # Receive length prefix
                length_data = self._recv_exact(client_socket, 4)
                if not length_data:
                    break
                length = struct.unpack(">I", length_data)[0]

                # Receive data
                data = self._recv_exact(client_socket, length)
                if not data:
                    break

                # Check if it's a command or audio
                try:
                    cmd = data.decode("utf-8")
                    if cmd == "START_RECORDING":
                        print("\n[Recording started]")
                        recording = True
                        audio_buffer = []
                        continue
                    elif cmd == "STOP_RECORDING":
                        print("[Recording stopped]")
                        recording = False
                        # Process the recorded audio
                        if audio_buffer:
                            self.process_audio(client_socket, audio_buffer)
                        continue
                except UnicodeDecodeError:
                    pass  # Not a command, it's audio data

                # It's audio data
                if recording:
                    audio = np.frombuffer(data, dtype=np.float32)
                    audio_buffer.append(audio)

        except Exception as e:
            print(f"Client error: {e}")

    def _recv_exact(self, sock: socket.socket, n: int) -> bytes | None:
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _send_audio(self, sock: socket.socket, audio: np.ndarray):
        """Send audio data to client."""
        audio_bytes = audio.astype(np.float32).tobytes()
        sock.sendall(struct.pack(">I", len(audio_bytes)))
        sock.sendall(audio_bytes)

    def process_audio(self, client_socket: socket.socket, audio_chunks: list):
        """Process recorded audio through the ATLAS pipeline."""
        # Combine audio chunks
        audio = np.concatenate(audio_chunks)
        print(f"Processing {len(audio) / SAMPLE_RATE:.1f}s of audio...")

        # STT
        start = time.perf_counter()
        transcription = self.stt.transcribe(audio, SAMPLE_RATE)
        stt_time = (time.perf_counter() - start) * 1000
        print(f"You: {transcription.text}")
        print(f"  [STT: {stt_time:.0f}ms]")

        if not transcription.text.strip():
            print("  [No speech detected]")
            # Send empty response
            self._send_audio(client_socket, np.array([], dtype=np.float32))
            return

        # Route the query
        decision = self.router.classify(transcription.text)
        print(f"  [Route: {decision.tier.value}, conf: {decision.confidence:.2f}]")

        # If cloud tier, send filler phrase first
        if decision.tier != Tier.LOCAL:
            filler = self._get_filler_phrase()
            print(f"ATLAS: {filler}")
            filler_audio = self.tts.synthesize(filler)
            self._send_audio(client_socket, filler_audio.audio)

        # Generate response
        print("ATLAS: ", end="", flush=True)
        response_text = ""

        # Use router to get response
        start = time.perf_counter()
        async def get_response():
            nonlocal response_text
            async for token in self.router.route_and_stream(
                transcription.text,
                temperature=0.7,
                max_tokens=256,
            ):
                response_text += token
                print(token, end="", flush=True)

        asyncio.run(get_response())
        llm_time = (time.perf_counter() - start) * 1000
        print()
        print(f"  [LLM: {llm_time:.0f}ms]")

        # TTS
        if response_text.strip():
            start = time.perf_counter()
            result = self.tts.synthesize(response_text)
            tts_time = (time.perf_counter() - start) * 1000
            print(f"  [TTS: {tts_time:.0f}ms]")

            # Send TTS audio back to Windows
            self._send_audio(client_socket, result.audio)
        else:
            self._send_audio(client_socket, np.array([], dtype=np.float32))


def main():
    """Entry point."""
    print("=" * 50)
    print("ATLAS Bridge Server (WSL2)")
    print("=" * 50)

    server = BridgeServer()
    server.start()


if __name__ == "__main__":
    main()
