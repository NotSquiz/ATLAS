#!/usr/bin/env python3
"""
WSL2 Audio Receiver for ATLAS
Receives audio from Windows, transcribes with faster-whisper.

Usage (in WSL2):
    source ~/ATLAS/venv/bin/activate
    python ~/ATLAS/bin/wsl_audio_receiver.py

Then run win_audio_capture.py on Windows.
"""

import socket
import numpy as np
import io
import sys

# Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5555
SAMPLE_RATE = 16000

def load_whisper():
    """Load faster-whisper model."""
    print("Loading faster-whisper model (first run downloads ~500MB)...")
    from faster_whisper import WhisperModel

    # Use 'small' model - good balance of speed/accuracy
    # Runs on CPU since we have limited VRAM
    model = WhisperModel(
        "small",
        device="cpu",  # Use CPU to save GPU for other tasks
        compute_type="int8"  # Faster on CPU
    )
    print("Model loaded.")
    return model


def transcribe_audio(model, audio_data: bytes) -> str:
    """Transcribe audio bytes to text."""
    # Convert bytes to numpy array
    audio = np.frombuffer(audio_data, dtype=np.float32)

    if len(audio) < SAMPLE_RATE * 0.5:  # Less than 0.5 seconds
        return ""

    # Transcribe
    segments, info = model.transcribe(
        audio,
        language="en",
        beam_size=5,
        vad_filter=True,  # Filter out silence
    )

    # Combine segments
    text = " ".join(segment.text for segment in segments).strip()
    return text


def run_server(model):
    """Run the audio receiver server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Listening on {HOST}:{PORT}")
    print("Waiting for Windows audio capture to connect...")

    while True:
        conn, addr = server.accept()
        print(f"Connected: {addr}")

        audio_buffer = bytearray()
        recording = False

        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break

                # Check for control markers
                if data == b"START":
                    recording = True
                    audio_buffer = bytearray()
                    print("Recording started...")
                    continue
                elif data == b"END":
                    recording = False
                    print(f"Recording ended. Got {len(audio_buffer)} bytes")

                    if audio_buffer:
                        print("Transcribing...")
                        text = transcribe_audio(model, bytes(audio_buffer))
                        if text:
                            print(f">>> {text}")
                            # TODO: Send to Claude here
                        else:
                            print("(no speech detected)")
                    audio_buffer = bytearray()
                    continue

                if recording:
                    audio_buffer.extend(data)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
            print("Connection closed")


def main():
    print("=" * 50)
    print("ATLAS Audio Receiver (WSL2)")
    print("=" * 50)

    model = load_whisper()
    run_server(model)


if __name__ == "__main__":
    main()
