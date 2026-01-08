#!/usr/bin/env python3
"""
ATLAS Voice Bridge - Windows Launcher

A unified Windows GUI for launching and controlling the ATLAS voice assistant.
- Start/Stop WSL server
- Hold SPACEBAR to record, release to send
- Voice toggle (M/F)
- Session cost and routing display

Usage (from Windows):
    python atlas_launcher.py
    # Or double-click atlas_launcher.pyw (hides console)

Dependencies:
    pip install customtkinter sounddevice numpy
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from threading import Thread, Event
from typing import Optional

# Check dependencies
try:
    import customtkinter as ctk
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print("ERROR: Missing dependencies. Run in Windows PowerShell:")
    print("  pip install customtkinter sounddevice numpy")
    print(f"\nMissing: {e.name}")
    sys.exit(1)

# Configuration
WSL_PATH = Path(r"\\wsl$\Ubuntu\home\squiz\ATLAS")
BRIDGE_DIR = WSL_PATH / ".bridge"
SAMPLE_RATE = 16000

# Colors (dark theme)
COLORS = {
    "bg": "#1a1a1a",
    "card": "#2d2d2d",
    "accent": "#4a9eff",
    "success": "#238636",
    "warning": "#d29922",
    "error": "#f85149",
    "text": "#e6e6e6",
    "muted": "#8b949e",
    "listening": "#238636",    # Green
    "processing": "#d29922",   # Yellow/Orange
    "speaking": "#4a9eff",     # Blue
}

# State colors for status indicator
STATE_COLORS = {
    "idle": "#8b949e",
    "listening": "#238636",
    "processing": "#d29922",
    "speaking": "#4a9eff",
}


class ATLASLauncher(ctk.CTk):
    """Main launcher window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("ATLAS Voice Bridge")
        self.geometry("450x720")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State
        self.server_process: Optional[subprocess.Popen] = None
        self.server_ready = Event()
        self.recording = False
        self.audio_chunks = []
        self.stream = None
        self.processing = False
        self.transcript_history = []  # List of (timestamp, user, atlas) tuples
        self.last_exchange_hash = ""  # To detect new exchanges
        self.current_state = "idle"  # idle, listening, processing, speaking
        self.last_timing = {"stt": 0, "tts": 0}  # Last timing info

        # Build UI
        self._build_ui()
        self._bind_keys()
        self._start_polling()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the user interface."""
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="ATLAS Voice Bridge",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.title_label.pack(pady=(0, 15))

        # Start/Stop buttons
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=(0, 15))

        self.start_btn = ctk.CTkButton(
            self.btn_frame,
            text="START",
            width=120,
            height=40,
            command=self._start_server,
            fg_color=COLORS["success"],
            hover_color="#2ea043",
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            self.btn_frame,
            text="STOP",
            width=120,
            height=40,
            command=self._stop_server,
            fg_color=COLORS["error"],
            hover_color="#da3633",
            state="disabled",
        )
        self.stop_btn.pack(side="left")

        # Status card
        self.status_card = ctk.CTkFrame(self.main_frame, fg_color=COLORS["card"])
        self.status_card.pack(fill="x", pady=(0, 15))

        self.server_status = ctk.CTkLabel(
            self.status_card,
            text="● Server: Stopped",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["muted"],
        )
        self.server_status.pack(anchor="w", padx=15, pady=(10, 5))

        self.voice_status = ctk.CTkLabel(
            self.status_card,
            text="● Voice: Lewis (M)",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["muted"],
        )
        self.voice_status.pack(anchor="w", padx=15, pady=(0, 5))

        self.gpu_status = ctk.CTkLabel(
            self.status_card,
            text="● GPU: Unknown",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["muted"],
        )
        self.gpu_status.pack(anchor="w", padx=15, pady=(0, 5))

        self.timing_label = ctk.CTkLabel(
            self.status_card,
            text="STT: --ms | TTS: --ms",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted"],
        )
        self.timing_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Voice toggle
        self.voice_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.voice_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            self.voice_frame, text="Voice:", font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 10))

        self.voice_var = ctk.StringVar(value="bm_lewis")
        self.voice_m = ctk.CTkRadioButton(
            self.voice_frame,
            text="Lewis (M)",
            variable=self.voice_var,
            value="bm_lewis",
            command=self._on_voice_change,
        )
        self.voice_m.pack(side="left", padx=(0, 15))

        self.voice_f = ctk.CTkRadioButton(
            self.voice_frame,
            text="Emma (F)",
            variable=self.voice_var,
            value="bf_emma",
            command=self._on_voice_change,
        )
        self.voice_f.pack(side="left")

        # Cost/Routing card
        self.stats_card = ctk.CTkFrame(self.main_frame, fg_color=COLORS["card"])
        self.stats_card.pack(fill="x", pady=(0, 15))

        self.cost_label = ctk.CTkLabel(
            self.stats_card,
            text="Session: $0.0000",
            font=ctk.CTkFont(size=14),
        )
        self.cost_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.route_label = ctk.CTkLabel(
            self.stats_card,
            text="Last: - (-.--)",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["muted"],
        )
        self.route_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Transcript area with counter
        self.transcript_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.transcript_header.pack(fill="x", pady=(0, 5))

        self.transcript_label = ctk.CTkLabel(
            self.transcript_header,
            text="Transcript",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["muted"],
        )
        self.transcript_label.pack(side="left")

        self.clear_btn = ctk.CTkButton(
            self.transcript_header,
            text="Clear",
            width=50,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["card"],
            hover_color=COLORS["muted"],
            command=self._clear_transcript,
        )
        self.clear_btn.pack(side="right", padx=(5, 0))

        self.exchange_count = ctk.CTkLabel(
            self.transcript_header,
            text="(0 exchanges)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted"],
        )
        self.exchange_count.pack(side="right")

        self.transcript_box = ctk.CTkTextbox(
            self.main_frame,
            height=150,
            font=ctk.CTkFont(size=11),
            fg_color=COLORS["card"],
            wrap="word",
        )
        self.transcript_box.pack(fill="x", pady=(0, 15))
        self.transcript_box.configure(state="disabled")

        # Voice input area
        self.voice_card = ctk.CTkFrame(self.main_frame, fg_color=COLORS["card"])
        self.voice_card.pack(fill="x", pady=(0, 15))

        self.voice_instruction = ctk.CTkLabel(
            self.voice_card,
            text="Hold SPACE to speak",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.voice_instruction.pack(pady=(20, 10))

        # Recording indicator
        self.recording_indicator = ctk.CTkProgressBar(
            self.voice_card, width=200, height=10
        )
        self.recording_indicator.pack(pady=(0, 20))
        self.recording_indicator.set(0)

        # Status bar at bottom
        self.status_bar = ctk.CTkLabel(
            self.main_frame,
            text="Ready - Press START to begin",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        )
        self.status_bar.pack(side="bottom", pady=(10, 0))

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self.bind("<KeyPress-space>", self._on_space_press)
        self.bind("<KeyRelease-space>", self._on_space_release)
        # Also bind to the window to catch focus
        self.bind("<FocusIn>", lambda e: None)

    def _set_state(self, state: str):
        """Set the current state and update status bar."""
        self.current_state = state
        state_texts = {
            "idle": "Ready",
            "listening": "● Listening...",
            "processing": "● Processing...",
            "speaking": "● Speaking...",
        }
        self.status_bar.configure(
            text=state_texts.get(state, "Ready"),
            text_color=STATE_COLORS.get(state, COLORS["muted"])
        )

    def _clear_transcript(self):
        """Clear the transcript history."""
        self.transcript_history = []
        self.last_exchange_hash = ""
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")
        self.exchange_count.configure(text="(0 exchanges)")

    def _start_polling(self):
        """Start polling for status updates."""
        self._poll_status()

    def _poll_status(self):
        """Poll status files and update UI."""
        # Read session status if exists
        status_file = BRIDGE_DIR / "session_status.json"
        try:
            if status_file.exists():
                data = json.loads(status_file.read_text())
                cost = data.get('session_cost', 0)
                self.cost_label.configure(text=f"Session: ${cost:.4f}")

                routing = data.get("routing", {})
                tier = routing.get("tier", "-")
                conf = routing.get("confidence", 0)
                self.route_label.configure(
                    text=f"Last: {tier.upper()} ({conf:.2f})"
                )

                # Update timing display
                timing = data.get("timing", {})
                stt_ms = timing.get("stt_ms", 0)
                tts_ms = timing.get("tts_ms", 0)
                if stt_ms or tts_ms:
                    self.timing_label.configure(
                        text=f"STT: {stt_ms}ms | TTS: {tts_ms}ms"
                    )

                # Update GPU status
                gpu = data.get("gpu", "Unknown")
                gpu_color = COLORS["success"] if gpu == "CUDA" else COLORS["warning"]
                self.gpu_status.configure(
                    text=f"● GPU: {gpu}",
                    text_color=gpu_color
                )

                # Check for new exchange
                exchange = data.get("last_exchange", {})
                user_text = exchange.get("user", "")
                atlas_text = exchange.get("atlas", "")
                updated_at = data.get("updated_at", "")

                # Create hash to detect new exchanges
                exchange_hash = f"{updated_at}:{user_text[:20] if user_text else ''}"
                if exchange_hash != self.last_exchange_hash and user_text:
                    self.last_exchange_hash = exchange_hash
                    # Add to history
                    self.transcript_history.append((updated_at, user_text, atlas_text))
                    # Keep only last 20 exchanges
                    if len(self.transcript_history) > 20:
                        self.transcript_history = self.transcript_history[-20:]
                    # Update display
                    self._update_transcript_display()
        except Exception as e:
            print(f"[Poll Error] {e}")

        # Schedule next poll
        self.after(500, self._poll_status)

    def _update_transcript_display(self):
        """Update the transcript textbox with full history."""
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")

        for i, (timestamp, user, atlas) in enumerate(self.transcript_history):
            # Add separator between exchanges (except first)
            if i > 0:
                self.transcript_box.insert("end", "─" * 40 + "\n")
            self.transcript_box.insert("end", f"[{timestamp}]\n")
            self.transcript_box.insert("end", f"You: {user}\n\n")
            self.transcript_box.insert("end", f"ATLAS: {atlas}\n")

        # Update counter
        count = len(self.transcript_history)
        self.exchange_count.configure(text=f"({count} exchange{'s' if count != 1 else ''})")

        # Scroll to bottom
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    def _start_server(self):
        """Start the WSL server."""
        if self.server_process is not None:
            return

        self.server_ready.clear()
        self.status_bar.configure(
            text="Starting server...",
            text_color=COLORS["warning"]
        )
        self.start_btn.configure(state="disabled")

        # Check WSL accessibility
        if not WSL_PATH.exists():
            self.status_bar.configure(
                text="ERROR: Cannot access WSL. Is WSL running?",
                text_color=COLORS["error"],
            )
            self.start_btn.configure(state="normal")
            return

        # Build the WSL command with absolute paths
        # Use python -u for unbuffered output so we can see logs in real-time
        cmd = (
            "cd /home/squiz/ATLAS && "
            "source /home/squiz/ATLAS/venv/bin/activate && "
            "source /home/squiz/.bashrc && "
            'ANTHROPIC_API_KEY="$(cat /home/squiz/ATLAS/.env | tr -d \'\\n\')" '
            "python -u -m atlas.voice.bridge_file_server"
        )

        try:
            # Start WSL process
            self.server_process = subprocess.Popen(
                ["wsl", "-d", "Ubuntu", "bash", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Start thread to monitor output
            Thread(target=self._monitor_server, daemon=True).start()

        except Exception as e:
            self.status_bar.configure(
                text=f"ERROR: {e}", text_color=COLORS["error"]
            )
            self.start_btn.configure(state="normal")
            self.server_process = None

    def _monitor_server(self):
        """Monitor server stdout for ready signal."""
        if self.server_process is None:
            return

        try:
            for line in iter(self.server_process.stdout.readline, ""):
                if not line:
                    break

                line = line.strip()
                print(f"[Server] {line}")  # Debug output

                # Show loading progress in status bar
                if "Loading ATLAS" in line:
                    self.after(0, lambda: self.status_bar.configure(
                        text="Loading ATLAS components...",
                        text_color=COLORS["warning"]
                    ))
                elif "Preloading STT" in line:
                    self.after(0, lambda: self.status_bar.configure(
                        text="Loading STT model...",
                        text_color=COLORS["warning"]
                    ))
                elif "Preloading TTS" in line:
                    self.after(0, lambda: self.status_bar.configure(
                        text="Loading TTS model...",
                        text_color=COLORS["warning"]
                    ))
                elif "Preloading router" in line:
                    self.after(0, lambda: self.status_bar.configure(
                        text="Loading router...",
                        text_color=COLORS["warning"]
                    ))

                # Check for ready signal
                if "Components loaded and ready." in line:
                    self.server_ready.set()
                    self.after(0, self._on_server_ready)

            # Process ended
            self.after(0, self._on_server_stopped)

        except Exception as e:
            print(f"Monitor error: {e}")
            self.after(0, self._on_server_stopped)

    def _on_server_ready(self):
        """Called when server is ready."""
        self.server_status.configure(
            text="● Server: Running", text_color=COLORS["success"]
        )
        self.status_bar.configure(
            text="Server ready - Hold SPACE to speak",
            text_color=COLORS["text"],
        )
        self.stop_btn.configure(state="normal")

    def _on_server_stopped(self):
        """Called when server stops."""
        self.server_process = None
        self.server_ready.clear()
        self.server_status.configure(
            text="● Server: Stopped", text_color=COLORS["muted"]
        )
        self.status_bar.configure(
            text="Server stopped", text_color=COLORS["muted"]
        )
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _stop_server(self):
        """Stop the WSL server."""
        if self.server_process is None:
            return

        self.status_bar.configure(text="Stopping server...")

        # Send QUIT command
        try:
            BRIDGE_DIR.mkdir(exist_ok=True)
            (BRIDGE_DIR / "command.txt").write_text("QUIT")
        except Exception as e:
            print(f"Error sending QUIT: {e}")

        # Give it time to exit gracefully
        try:
            self.server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.server_process.kill()

        self._on_server_stopped()

    def _on_voice_change(self):
        """Handle voice selection change."""
        voice = self.voice_var.get()
        voice_name = "Lewis (M)" if voice == "bm_lewis" else "Emma (F)"
        self.voice_status.configure(text=f"● Voice: {voice_name}")

        # Write preference to file
        try:
            BRIDGE_DIR.mkdir(exist_ok=True)
            (BRIDGE_DIR / "voice.txt").write_text(voice)
        except Exception as e:
            print(f"Error saving voice: {e}")

    def _on_space_press(self, event):
        """Start recording when SPACE is pressed."""
        # Ignore if server not ready or already recording/processing
        if not self.server_ready.is_set() or self.recording or self.processing:
            return

        self.recording = True
        self.audio_chunks = []

        # Start audio stream
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype=np.float32,
                callback=self._audio_callback,
            )
            self.stream.start()

            # Update UI
            self.recording_indicator.configure(progress_color=COLORS["listening"])
            self.recording_indicator.set(1)
            self.voice_instruction.configure(text="Recording...")
            self._set_state("listening")

        except Exception as e:
            self.recording = False
            self.status_bar.configure(
                text=f"Mic error: {e}", text_color=COLORS["error"]
            )

    def _audio_callback(self, indata, frames, time_info, status):
        """Audio stream callback."""
        if self.recording:
            self.audio_chunks.append(indata.copy())

    def _on_space_release(self, event):
        """Stop recording and send when SPACE is released."""
        if not self.recording:
            return

        self.recording = False

        # Stop audio stream
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        # Update UI
        self.recording_indicator.set(0)
        self.voice_instruction.configure(text="Processing...")
        self._set_state("processing")

        # Process audio in background
        if self.audio_chunks:
            audio = np.concatenate(self.audio_chunks)
            Thread(target=self._send_audio, args=(audio,), daemon=True).start()
        else:
            self.voice_instruction.configure(text="Hold SPACE to speak")
            self._set_state("idle")

    def _send_audio(self, audio: np.ndarray):
        """Send audio to server and play response."""
        self.processing = True

        try:
            # Update status
            self.after(0, lambda: self._set_state("processing"))

            # Save audio to file
            audio.astype(np.float32).tofile(BRIDGE_DIR / "audio_in.raw")

            # Clear status and send command
            status_file = BRIDGE_DIR / "status.txt"
            if status_file.exists():
                status_file.unlink()
            (BRIDGE_DIR / "command.txt").write_text("PROCESS")

            # Wait for DONE (timeout 60s)
            start = time.time()
            while time.time() - start < 60:
                if status_file.exists():
                    status = status_file.read_text().strip()
                    if status == "DONE":
                        break
                time.sleep(0.1)
            else:
                self.after(
                    0,
                    lambda: self.status_bar.configure(
                        text="Timeout waiting for response",
                        text_color=COLORS["error"],
                    ),
                )
                return

            # Read and play response
            audio_out = BRIDGE_DIR / "audio_out.raw"
            if audio_out.exists():
                # Get sample rate from metadata
                metadata = BRIDGE_DIR / "metadata.txt"
                playback_rate = 24000  # default
                if metadata.exists():
                    for line in metadata.read_text().splitlines():
                        if "sample_rate=" in line:
                            playback_rate = int(line.split("=")[1])

                # Load and play
                response = np.fromfile(audio_out, dtype=np.float32)
                if len(response) > 0:
                    duration = len(response) / playback_rate
                    self.after(0, lambda: self._set_state("speaking"))
                    sd.play(response, playback_rate)
                    sd.wait()

                # Clean up
                audio_out.unlink()

            # Done
            self.after(
                0,
                lambda: [
                    self.voice_instruction.configure(text="Hold SPACE to speak"),
                    self._set_state("idle"),
                ],
            )

        except Exception as e:
            self.after(
                0,
                lambda: self.status_bar.configure(
                    text=f"Error: {e}", text_color=COLORS["error"]
                ),
            )

        finally:
            self.processing = False
            self.after(
                0,
                lambda: self.voice_instruction.configure(
                    text="Hold SPACE to speak"
                ),
            )

    def _on_close(self):
        """Handle window close."""
        if self.server_process:
            self._stop_server()
        self.destroy()


def main():
    """Entry point."""
    # Check WSL accessibility
    if not WSL_PATH.exists():
        print("=" * 50)
        print("ERROR: Cannot access WSL at:")
        print(f"  {WSL_PATH}")
        print()
        print("Make sure:")
        print("  1. WSL is installed and running")
        print("  2. Ubuntu distribution is available")
        print("=" * 50)
        input("Press Enter to exit...")
        sys.exit(1)

    app = ATLASLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
