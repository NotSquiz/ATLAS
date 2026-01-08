#!/usr/bin/env python3
"""
Windows Audio Capture for ATLAS
Run this on Windows to capture microphone and send to WSL2.

Usage (in Windows PowerShell):
    python win_audio_capture.py

Press SPACE to start/stop recording (Push-to-Talk)
Press Q to quit
"""

import socket
import sys
import threading
import time

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("Install required packages: pip install sounddevice numpy")
    sys.exit(1)

# Configuration
WSL_HOST = "localhost"  # WSL2 listens on localhost from Windows perspective
WSL_PORT = 5555
SAMPLE_RATE = 16000
CHANNELS = 1

class AudioCapture:
    def __init__(self):
        self.recording = False
        self.audio_buffer = []
        self.sock = None
        self.connected = False

    def connect_to_wsl(self):
        """Connect to WSL2 audio receiver."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((WSL_HOST, WSL_PORT))
            self.connected = True
            print(f"Connected to WSL2 at {WSL_HOST}:{WSL_PORT}")
            return True
        except ConnectionRefusedError:
            print(f"Cannot connect to WSL2. Make sure wsl_audio_receiver.py is running.")
            return False

    def audio_callback(self, indata, frames, time_info, status):
        """Called for each audio block."""
        if status:
            print(f"Audio status: {status}")
        if self.recording and self.connected:
            # Send audio data directly
            try:
                self.sock.sendall(indata.tobytes())
            except Exception as e:
                print(f"Send error: {e}")
                self.connected = False

    def start_recording(self):
        """Start recording audio."""
        if not self.connected:
            if not self.connect_to_wsl():
                return

        # Send START marker
        self.sock.sendall(b"START")
        self.recording = True
        print("Recording... (press SPACE to stop)")

    def stop_recording(self):
        """Stop recording and signal end."""
        self.recording = False
        if self.connected:
            # Send END marker
            self.sock.sendall(b"END")
        print("Stopped recording")

    def run(self):
        """Main loop with keyboard control."""
        try:
            import msvcrt  # Windows-only
        except ImportError:
            print("This script must run on Windows")
            return

        print("=" * 50)
        print("ATLAS Audio Capture (Windows)")
        print("=" * 50)
        print("SPACE = Push-to-Talk (hold to record)")
        print("Q = Quit")
        print("=" * 50)
        print()

        # List audio devices
        print("Available audio devices:")
        print(sd.query_devices())
        print()

        # Start audio stream
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32',
            callback=self.audio_callback,
            blocksize=1024
        ):
            print("Audio stream ready. Press SPACE to talk...")

            space_held = False
            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()

                    if key == b' ':  # Space
                        if not space_held:
                            space_held = True
                            self.start_recording()
                    elif key == b'q' or key == b'Q':
                        print("Quitting...")
                        break
                else:
                    # Check if space was released
                    if space_held:
                        # Simple polling - in real app use keyboard library
                        import ctypes
                        VK_SPACE = 0x20
                        if not (ctypes.windll.user32.GetAsyncKeyState(VK_SPACE) & 0x8000):
                            space_held = False
                            self.stop_recording()

                time.sleep(0.01)

        if self.sock:
            self.sock.close()


if __name__ == "__main__":
    capture = AudioCapture()
    capture.run()
