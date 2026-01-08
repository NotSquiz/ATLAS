#!/usr/bin/env python3
"""
ATLAS Audio Bridge - Windows Side

Run this script in PowerShell on Windows (not WSL2).
It captures audio from your microphone and sends it to WSL2 for processing.

Requirements (install in Windows Python, not WSL2):
    pip install sounddevice numpy

Usage:
    1. Start the WSL2 server first: python -m atlas.voice.bridge_server
    2. Run this in PowerShell: python audio_bridge_windows.py

The script connects to WSL2 via localhost (WSL2 ports are accessible from Windows).
"""

import socket
import struct
import sys
import time
import threading
import queue

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("ERROR: Missing dependencies. Run in Windows PowerShell:")
    print("  pip install sounddevice numpy")
    sys.exit(1)

# Configuration
# Try localhost first (works with mirrored networking), fall back to WSL2 IP
WSL2_HOST = "localhost"
WSL2_HOST_FALLBACK = "192.168.20.7"  # WSL2 IP - update if it changes
WSL2_PORT = 9999
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION_MS = 100  # Send 100ms chunks


class AudioBridge:
    """Bridges Windows audio to WSL2 for processing."""

    def __init__(self, host: str = WSL2_HOST, port: int = WSL2_PORT, host_fallback: str = WSL2_HOST_FALLBACK):
        self.host = host
        self.host_fallback = host_fallback
        self.port = port
        self.socket = None
        self.running = False
        self.recording = False
        self.audio_queue = queue.Queue()
        self.playback_queue = queue.Queue()

    def connect(self) -> bool:
        """Connect to WSL2 audio server."""
        # Try primary host first, then fallback
        hosts_to_try = [self.host]
        if hasattr(self, 'host_fallback') and self.host_fallback:
            hosts_to_try.append(self.host_fallback)

        for host in hosts_to_try:
            try:
                print(f"Trying to connect to {host}:{self.port}...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5)  # 5 second timeout
                self.socket.connect((host, self.port))
                self.socket.settimeout(None)  # Remove timeout after connect
                print(f"Connected to WSL2 at {host}:{self.port}")
                self.host = host  # Remember which host worked
                return True
            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                print(f"  Failed: {e}")
                if self.socket:
                    self.socket.close()
                continue

        print("\nERROR: Cannot connect to WSL2 server.")
        print("Make sure the WSL2 server is running:")
        print("  In WSL2: python -m atlas.voice.bridge_server")
        print(f"\nTried: {', '.join(hosts_to_try)}")
        return False

    def disconnect(self):
        """Disconnect from WSL2."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def send_audio(self, audio: np.ndarray):
        """Send audio chunk to WSL2."""
        if not self.socket:
            return

        # Convert to bytes
        audio_bytes = audio.astype(np.float32).tobytes()

        # Send length prefix + data
        length = len(audio_bytes)
        try:
            self.socket.sendall(struct.pack(">I", length))
            self.socket.sendall(audio_bytes)
        except Exception as e:
            print(f"Send error: {e}")

    def receive_audio(self) -> np.ndarray | None:
        """Receive TTS audio from WSL2."""
        if not self.socket:
            return None

        try:
            # Read length prefix
            length_data = self._recv_exact(4)
            if not length_data:
                return None
            length = struct.unpack(">I", length_data)[0]

            if length == 0:
                return None

            # Read audio data
            audio_bytes = self._recv_exact(length)
            if not audio_bytes:
                return None

            return np.frombuffer(audio_bytes, dtype=np.float32)

        except Exception as e:
            print(f"Receive error: {e}")
            return None

    def _recv_exact(self, n: int) -> bytes | None:
        """Receive exactly n bytes."""
        data = b""
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def send_command(self, cmd: str):
        """Send a command to WSL2 (START_RECORDING, STOP_RECORDING, etc.)."""
        if not self.socket:
            return
        cmd_bytes = cmd.encode("utf-8")
        try:
            self.socket.sendall(struct.pack(">I", len(cmd_bytes)))
            self.socket.sendall(cmd_bytes)
        except Exception as e:
            print(f"Command error: {e}")

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice input stream."""
        if status:
            print(f"Audio status: {status}")
        if self.recording:
            self.audio_queue.put(indata.copy())

    def playback_callback(self, outdata, frames, time_info, status):
        """Callback for sounddevice output stream."""
        if status:
            print(f"Playback status: {status}")
        try:
            data = self.playback_queue.get_nowait()
            if len(data) < len(outdata):
                outdata[:len(data)] = data.reshape(-1, 1)
                outdata[len(data):] = 0
            else:
                outdata[:] = data[:len(outdata)].reshape(-1, 1)
        except queue.Empty:
            outdata[:] = 0

    def sender_thread(self):
        """Thread that sends audio chunks to WSL2."""
        chunk_samples = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
        buffer = np.array([], dtype=np.float32)

        while self.running:
            try:
                # Get audio from queue
                data = self.audio_queue.get(timeout=0.1)
                buffer = np.concatenate([buffer, data.flatten()])

                # Send complete chunks
                while len(buffer) >= chunk_samples:
                    chunk = buffer[:chunk_samples]
                    buffer = buffer[chunk_samples:]
                    self.send_audio(chunk)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Sender error: {e}")
                break

    def receiver_thread(self):
        """Thread that receives TTS audio from WSL2."""
        while self.running:
            try:
                audio = self.receive_audio()
                if audio is not None and len(audio) > 0:
                    # Queue for playback
                    self.playback_queue.put(audio)
            except Exception as e:
                if self.running:
                    print(f"Receiver error: {e}")
                break

    def run(self):
        """Main loop - push-to-talk interface."""
        if not self.connect():
            return

        print("\n" + "=" * 50)
        print("ATLAS Audio Bridge (Windows -> WSL2)")
        print("=" * 50)
        print("Press ENTER to start recording")
        print("Press ENTER again to stop and process")
        print("Press Ctrl+C to quit")
        print("=" * 50 + "\n")

        self.running = True

        # Start sender thread
        sender = threading.Thread(target=self.sender_thread, daemon=True)
        sender.start()

        # Start receiver thread
        receiver = threading.Thread(target=self.receiver_thread, daemon=True)
        receiver.start()

        chunk_samples = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)

        try:
            while self.running:
                input("\nPress ENTER to speak...")

                # Start recording
                print("Recording... (press ENTER to stop)")
                self.recording = True
                self.send_command("START_RECORDING")

                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=np.float32,
                    blocksize=chunk_samples,
                    callback=self.audio_callback,
                ):
                    input()  # Wait for ENTER

                # Stop recording
                self.recording = False
                self.send_command("STOP_RECORDING")
                print("Processing...")

                # Wait for and play response
                time.sleep(0.5)  # Give WSL2 time to process
                while not self.playback_queue.empty():
                    audio = self.playback_queue.get()
                    sd.play(audio, SAMPLE_RATE)
                    sd.wait()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        finally:
            self.running = False
            self.disconnect()


def main():
    """Entry point."""
    # Check audio devices
    print("Available audio devices:")
    print(sd.query_devices())
    print()

    bridge = AudioBridge()
    bridge.run()


if __name__ == "__main__":
    main()
