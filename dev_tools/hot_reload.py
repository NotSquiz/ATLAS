#!/usr/bin/env python3
"""
Hot Reload Watcher for ATLAS UI Development

Automatically restarts atlas_launcher.py when Python files change.
Preserves state via session_status.json for continuity.

Usage (from Windows):
    python dev_tools/hot_reload.py

Features:
    - Debouncing (waits for saves to complete)
    - Process cleanup on restart
    - Test mode environment variable set automatically
    - Output monitoring with prefix

Dependencies:
    pip install watchdog
"""
import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError:
    print("ERROR: watchdog not installed. Run: pip install watchdog")
    sys.exit(1)


class HotReloader(FileSystemEventHandler):
    """
    File watcher that restarts the UI on Python file changes.

    Thread-safe restart with debouncing to handle rapid saves.
    """

    def __init__(
        self,
        script_path: str,
        watch_paths: list = None,
        debounce_seconds: float = 0.5,
    ):
        self.script_path = Path(script_path).resolve()
        self.watch_paths = watch_paths or [
            self.script_path.parent,  # scripts/
        ]
        self.debounce_seconds = debounce_seconds
        self.process = None
        self.debounce_timer = None
        self.restart_count = 0
        self._lock = threading.Lock()

        print(f"[HotReload] Target: {self.script_path}")
        print(f"[HotReload] Watching: {[str(p) for p in self.watch_paths]}")

    def start_app(self):
        """Start or restart the UI application."""
        with self._lock:
            if self.process:
                print("[HotReload] Stopping previous instance...")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("[HotReload] Force killing...")
                    self.process.kill()
                    self.process.wait()
                except Exception as e:
                    print(f"[HotReload] Stop error: {e}")
                self.process = None

            self.restart_count += 1
            print(f"\n[HotReload] Starting {self.script_path.name} (restart #{self.restart_count})")
            print("-" * 50)

            # Set test mode for state export
            env = os.environ.copy()
            env["ATLAS_TEST_MODE"] = "1"

            try:
                self.process = subprocess.Popen(
                    [sys.executable, str(self.script_path)],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                # Start output monitor thread
                threading.Thread(
                    target=self._monitor_output,
                    daemon=True,
                    name=f"output-monitor-{self.restart_count}",
                ).start()

            except Exception as e:
                print(f"[HotReload] Failed to start: {e}")

    def _monitor_output(self):
        """Print subprocess output with prefix."""
        proc = self.process
        if not proc:
            return

        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                # Don't print if process has been replaced
                if proc is not self.process:
                    break
                print(f"[UI] {line.rstrip()}")
        except Exception:
            pass

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        # Only react to Python files
        if not event.src_path.endswith('.py'):
            return

        # Ignore __pycache__, .pyc, and tmp files
        if any(x in event.src_path for x in ['__pycache__', '.pyc', '.tmp']):
            return

        # Debounce: cancel previous timer, start new one
        if self.debounce_timer:
            self.debounce_timer.cancel()

        filename = Path(event.src_path).name
        print(f"\n[HotReload] Change detected: {filename}")

        self.debounce_timer = threading.Timer(
            self.debounce_seconds,
            self.start_app,
        )
        self.debounce_timer.start()

    def cleanup(self):
        """Clean up process on exit."""
        if self.debounce_timer:
            self.debounce_timer.cancel()

        with self._lock:
            if self.process:
                print("\n[HotReload] Cleaning up...")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                except Exception:
                    pass


def main():
    """Entry point for hot reload watcher."""
    # Determine script path (relative to this file's location)
    dev_tools_dir = Path(__file__).parent.resolve()
    project_root = dev_tools_dir.parent

    # Try to find atlas_launcher.py
    script_path = project_root / "scripts" / "atlas_launcher.py"

    if not script_path.exists():
        # Maybe running from different location
        if len(sys.argv) > 1:
            script_path = Path(sys.argv[1]).resolve()
        else:
            print(f"ERROR: Cannot find atlas_launcher.py")
            print(f"  Expected at: {script_path}")
            print(f"  Usage: python hot_reload.py [path/to/atlas_launcher.py]")
            sys.exit(1)

    if not script_path.exists():
        print(f"ERROR: {script_path} not found")
        sys.exit(1)

    print("=" * 60)
    print("ATLAS UI Hot Reload Development Server")
    print("=" * 60)
    print(f"Script: {script_path}")
    print(f"Test Mode: ATLAS_TEST_MODE=1")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    handler = HotReloader(script_path)
    observer = Observer()

    # Watch the scripts directory
    for path in handler.watch_paths:
        if path.exists():
            observer.schedule(handler, str(path), recursive=True)
            print(f"[HotReload] Watching: {path}")

    observer.start()

    # Initial start
    handler.start_app()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n[HotReload] Shutting down...")
        handler.cleanup()
        observer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
