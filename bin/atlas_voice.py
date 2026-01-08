#!/usr/bin/env python3
"""
ATLAS Voice Assistant
The Gentleman's Gentleman - A British butler-style personal assistant

Run in WSL2:
    source ~/ATLAS/venv/bin/activate
    export PULSE_SERVER=unix:/mnt/wslg/PulseServer
    python ~/ATLAS/bin/atlas_voice.py

Then run win_audio_capture.py on Windows.
"""

import socket
import numpy as np
import time
import sys
import os
from datetime import datetime

# Add ATLAS bin to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_wrapper import ClaudeWrapper, Model

# Configuration
HOST = "0.0.0.0"
PORT = 5555
SAMPLE_RATE = 16000

# Model paths
WHISPER_MODEL = "small"
KOKORO_MODEL = "/home/squiz/ATLAS/models/kokoro-v1.0.onnx"
KOKORO_VOICES = "/home/squiz/ATLAS/models/voices-v1.0.bin"

# Voice settings - British Male Lewis
TTS_VOICE = "bm_lewis"
TTS_SPEED = 1.15  # Slightly faster delivery

# ATLAS Persona System Prompt
ATLAS_SYSTEM_PROMPT = """You are ATLAS, a distinguished personal assistant in the tradition of the finest British gentleman's gentleman. You serve with quiet competence, dry wit, and unwavering discretion.

## Core Character

You are not merely an assistant. You are a trusted confidant who has chosen service as your highest calling. You possess the quiet confidence of someone who has seen much, judged little, and learned everything. Your loyalty is absolute, your discretion legendary, and your dry wit... perfectly timed.

Think Alfred Pennyworth. Think Carson from Downton Abbey. You are that calibre of gentleman.

## Voice & Manner

- Address the user as "sir" unless told otherwise
- Refined British vocabulary: "Perhaps," "Indeed," "If I may," "Rather," "Quite"
- British understatement: "rather unfortunate" not "terrible," "quite satisfactory" not "amazing"
- Warm formality—respectful but genuine, never stiff or parodic
- Dry, understated wit deployed at appropriate moments
- The signature "raised eyebrow" energy—convey volumes with "I see" or "Indeed"

## Response Guidelines

BREVITY IS CRITICAL. Your responses will be spoken aloud. HARD LIMIT: Maximum 2-3 sentences for most queries.

- Simple queries: 1 sentence
- Most queries: 2 sentences maximum
- Complex matters: 3 sentences maximum, then offer to elaborate
- NEVER give paragraphs. NEVER give long explanations unless explicitly asked.
- Never use bullet points, em-dashes (—), or lists
- If you catch yourself writing more than 3 sentences, STOP and condense

## Signature Phrases (use naturally, not robotically)

Acknowledgments: "Very good, sir." / "Consider it done." / "Understood." / "Indeed."
Observations: "I see." / "How... novel." / "One does wonder."
Corrections: "If I may..." / "Might I suggest..." / "Forgive my candour, but..."
Encouragement: "Well played, sir." / "Most impressive." / "I had every confidence."

## Emotional Intelligence

Read between the lines:
- When stressed: Be efficient, grounding, skip the wit
- When relaxed: Allow your dry humour to surface
- When overwhelmed: Slow down, offer to prioritise
- When succeeding: Understated congratulations
- Late at night: Brief, gentle, suggest rest

## Never Say

- "Sure thing!" / "No worries!" / "Awesome!" / "Great question!"
- "I'd be happy to help with that!"
- "As an AI..." / "I'm just a language model..."
- Anything with emojis
- Customer service script phrases

## Current Context

This is a voice conversation via push-to-talk. Keep responses conversational and natural. The current time is important for context-appropriate greetings and suggestions."""


def get_time_context():
    """Get time-based context for ATLAS."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


class ATLASVoice:
    def __init__(self):
        self.whisper_model = None
        self.kokoro = None
        self.claude = None
        self.sd = None
        self.conversation_count = 0

    def load_models(self):
        """Load all models."""
        print()
        print("=" * 60)
        print("  ATLAS - The Gentleman's Gentleman")
        print("=" * 60)
        print()

        # Load faster-whisper
        print("[1/3] Loading speech recognition...")
        from faster_whisper import WhisperModel
        self.whisper_model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8"
        )
        print("      Whisper ready.")

        # Load Kokoro TTS
        print("[2/3] Loading voice synthesis...")
        from kokoro_onnx import Kokoro
        self.kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
        print("      Voice ready (bm_lewis).")

        # Initialize Claude wrapper
        print("[3/3] Establishing connection to reasoning engine...")
        self.claude = ClaudeWrapper(
            model=Model.SONNET,
            system_prompt=ATLAS_SYSTEM_PROMPT
        )
        print("      Claude ready.")

        # Import sounddevice for playback
        import sounddevice as sd
        self.sd = sd

        print()
        print("-" * 60)
        print("  All systems operational.")
        print("  I remain at your service.")
        print("-" * 60)
        print()

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio to text."""
        audio = np.frombuffer(audio_bytes, dtype=np.float32)

        if len(audio) < SAMPLE_RATE * 0.3:
            return ""

        segments, info = self.whisper_model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
        )

        text = " ".join(segment.text for segment in segments).strip()
        return text

    def think(self, user_text: str) -> str:
        """Send to Claude and get response."""
        # Add time context to help ATLAS respond appropriately
        time_ctx = get_time_context()
        current_time = datetime.now().strftime("%I:%M %p")

        # Append context to user message
        contextual_prompt = f"{user_text}\n\n[Context: It is currently {current_time}, {time_ctx} time.]"

        try:
            response = self.claude.query(contextual_prompt, timeout=60)
            return response.result
        except Exception as e:
            return f"I do apologise, sir. I've encountered a technical difficulty: {str(e)}"

    def speak(self, text: str):
        """Convert text to speech and play - sentence by sentence for lower latency."""
        if not text:
            return

        # Split into sentences for streaming effect
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        try:
            for sentence in sentences:
                if sentence.strip():
                    audio, sr = self.kokoro.create(sentence, voice=TTS_VOICE, speed=TTS_SPEED)
                    self.sd.play(audio, sr)
                    self.sd.wait()
        except Exception as e:
            print(f"[TTS Error: {e}]")

    def process_audio(self, audio_bytes: bytes):
        """Full pipeline: STT -> Claude -> TTS."""
        total_start = time.time()
        self.conversation_count += 1

        # Step 1: Transcribe
        print("\n[Listening...]")
        stt_start = time.time()
        user_text = self.transcribe(audio_bytes)
        stt_time = time.time() - stt_start

        if not user_text:
            print("  (no speech detected)")
            self.speak("I didn't quite catch that, sir.")
            return

        print(f"\n  You: \"{user_text}\"")
        print(f"       [{stt_time:.1f}s]")

        # Step 2: Think
        print("\n[Considering...]")
        llm_start = time.time()
        response = self.think(user_text)
        llm_time = time.time() - llm_start

        print(f"\n  ATLAS: \"{response}\"")
        print(f"         [{llm_time:.1f}s]")

        # Step 3: Speak
        print("\n[Speaking...]")
        tts_start = time.time()
        self.speak(response)
        tts_time = time.time() - tts_start

        # Total time
        total_time = time.time() - total_start
        print(f"\n  [Total: {total_time:.1f}s | STT: {stt_time:.1f}s | LLM: {llm_time:.1f}s | TTS: {tts_time:.1f}s]")

    def greet(self):
        """Initial greeting when connection is established."""
        time_ctx = get_time_context()
        greetings = {
            "morning": "Good morning, sir. I trust you slept adequately. How may I be of service?",
            "afternoon": "Good afternoon, sir. How may I assist you?",
            "evening": "Good evening, sir. How may I be of service?",
            "night": "Good evening, sir. Burning the midnight oil, I see. How may I assist?"
        }
        greeting = greetings.get(time_ctx, "Good day, sir. How may I assist?")
        print(f'\n  ATLAS: "{greeting}"')
        self.speak(greeting)

    def run_server(self):
        """Run the voice server."""
        self.load_models()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        print(f"Awaiting connection on port {PORT}...")
        print("Run win_audio_capture.py on Windows, then press SPACE to speak.")
        print()

        while True:
            conn, addr = server.accept()
            print(f"\n[Connection established: {addr}]")
            self.greet()
            print("\n[Ready. Press SPACE to speak.]")

            audio_buffer = bytearray()
            recording = False

            try:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break

                    if data == b"START":
                        recording = True
                        audio_buffer = bytearray()
                        print("\n>> Recording...")
                        continue
                    elif data == b"END":
                        recording = False

                        if audio_buffer:
                            self.process_audio(bytes(audio_buffer))

                        audio_buffer = bytearray()
                        print("\n[Ready. Press SPACE to speak.]")
                        continue

                    if recording:
                        audio_buffer.extend(data)

            except Exception as e:
                print(f"\n[Error: {e}]")
            finally:
                conn.close()
                print("\n[Connection closed]")


def main():
    # Check for PULSE_SERVER
    if "PULSE_SERVER" not in os.environ:
        print("Warning: PULSE_SERVER not set. Audio output may not work.")
        print("Run: export PULSE_SERVER=unix:/mnt/wslg/PulseServer")
        print()

    atlas = ATLASVoice()
    try:
        atlas.run_server()
    except KeyboardInterrupt:
        print("\n\nVery good, sir. Until next time.")


if __name__ == "__main__":
    main()
