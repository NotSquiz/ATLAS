#!/usr/bin/env python3
"""
ATLAS Audio Bridge - Windows Side (File-based)

This version uses file-based communication instead of sockets,
which avoids WSL2 networking issues entirely.

Usage:
    1. Start WSL2 server: python -m atlas.voice.bridge_file_server
    2. Run this in PowerShell: python audio_bridge_windows_file.py
"""

import sys
import time
import os

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("ERROR: Missing dependencies. Run in Windows PowerShell:")
    print("  pip install sounddevice numpy")
    sys.exit(1)

# Configuration
SAMPLE_RATE = 16000
CHANNELS = 1

# File paths for communication (via \\wsl$)
WSL_PATH = r"\\wsl$\Ubuntu\home\squiz\ATLAS"
AUDIO_IN_FILE = os.path.join(WSL_PATH, ".bridge", "audio_in.raw")
AUDIO_OUT_FILE = os.path.join(WSL_PATH, ".bridge", "audio_out.raw")
METADATA_FILE = os.path.join(WSL_PATH, ".bridge", "metadata.txt")
COMMAND_FILE = os.path.join(WSL_PATH, ".bridge", "command.txt")
STATUS_FILE = os.path.join(WSL_PATH, ".bridge", "status.txt")


def ensure_bridge_dir():
    """Create bridge directory if needed."""
    bridge_dir = os.path.join(WSL_PATH, ".bridge")
    if not os.path.exists(bridge_dir):
        os.makedirs(bridge_dir)


def write_command(cmd: str):
    """Write command to file."""
    with open(COMMAND_FILE, "w") as f:
        f.write(cmd)


def read_status() -> str:
    """Read status from file."""
    try:
        with open(STATUS_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def clear_status():
    """Clear status file."""
    try:
        os.remove(STATUS_FILE)
    except FileNotFoundError:
        pass


def read_metadata() -> dict:
    """Read metadata from file."""
    metadata = {"sample_rate": 24000}  # Default Kokoro rate
    try:
        with open(METADATA_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    if key == "sample_rate":
                        metadata["sample_rate"] = int(value)
    except FileNotFoundError:
        pass
    return metadata


def wait_for_status(expected: str, timeout: float = 30.0) -> bool:
    """Wait for specific status."""
    start = time.time()
    while time.time() - start < timeout:
        if read_status() == expected:
            return True
        time.sleep(0.1)
    return False


def record_audio() -> np.ndarray:
    """Record audio until Enter is pressed."""
    print("Recording... (press ENTER to stop)")

    audio_chunks = []
    recording = True

    def callback(indata, frames, time_info, status):
        if recording:
            audio_chunks.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype=np.float32, callback=callback):
        input()  # Wait for Enter

    recording = False

    if audio_chunks:
        return np.concatenate(audio_chunks)
    return np.array([], dtype=np.float32)


def main():
    print("=" * 50)
    print("ATLAS Audio Bridge (Windows -> WSL2 via Files)")
    print("=" * 50)

    # Check WSL path accessible
    if not os.path.exists(WSL_PATH):
        print(f"ERROR: Cannot access WSL2 at {WSL_PATH}")
        print("Make sure WSL2 is running.")
        return

    print(f"WSL2 path: {WSL_PATH}")

    # Create bridge directory
    ensure_bridge_dir()
    print("Bridge directory ready.")

    # Check if server is running
    write_command("PING")
    print("Waiting for WSL2 server...")

    if not wait_for_status("PONG", timeout=10):
        print("\nERROR: WSL2 server not responding.")
        print("Start it with: python -m atlas.voice.bridge_file_server")
        return

    print("Connected to WSL2 server!")
    clear_status()

    print("\nPress ENTER to start recording, ENTER again to stop.")
    print("Press Ctrl+C to quit.\n")

    try:
        while True:
            input("\nPress ENTER to speak...")

            # Record audio
            audio = record_audio()

            if len(audio) == 0:
                print("No audio recorded.")
                continue

            print(f"Recorded {len(audio) / SAMPLE_RATE:.1f}s of audio")

            # Save audio to file
            audio.astype(np.float32).tofile(AUDIO_IN_FILE)

            # Signal server to process
            clear_status()
            write_command("PROCESS")

            print("Processing...")

            # Wait for response
            if not wait_for_status("DONE", timeout=60):
                print("Timeout waiting for response.")
                continue

            # Read metadata for correct sample rate
            metadata = read_metadata()
            playback_rate = metadata["sample_rate"]

            # Read and play response audio
            if os.path.exists(AUDIO_OUT_FILE):
                response_audio = np.fromfile(AUDIO_OUT_FILE, dtype=np.float32)
                if len(response_audio) > 0:
                    print(f"Playing response ({len(response_audio) / playback_rate:.1f}s @ {playback_rate}Hz)...")
                    sd.play(response_audio, playback_rate)
                    sd.wait()
                os.remove(AUDIO_OUT_FILE)

            clear_status()

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        write_command("QUIT")


if __name__ == "__main__":
    main()
