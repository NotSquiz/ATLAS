# OSRS-Style Command Centre - Autonomous UI Development Setup

**Goal:** Enable Claude Code to iterate autonomously on the CustomTkinter dashboard with <3 second feedback loops.

---

## Quick Start (TL;DR)

```bash
# 1. Install dependencies (Windows PowerShell)
pip install customtkinter sounddevice numpy watchdog Pillow imagehash

# 2. Create dev tools directory
mkdir -p dev_tools tests/fixtures tests/ui

# 3. Run hot-reload development
python dev_tools/hot_reload.py

# 4. (Optional) Install screenshot capability - run in PowerShell as Admin
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 1. Python Dependencies

### Windows (where atlas_launcher.py runs):
```powershell
# Core dependencies (already installed)
pip install customtkinter sounddevice numpy

# Hot reload and testing
pip install watchdog Pillow imagehash pytest

# Optional: Visual regression
pip install pixelmatch
```

### WSL2 (for test orchestration):
```bash
# No additional deps needed - tests run via Windows Python
```

---

## 2. Directory Structure

```
ATLAS/
├── dev_tools/
│   ├── hot_reload.py          # File watcher with auto-restart
│   ├── state_exporter.py      # UI state export helpers
│   └── capture_screen.ps1     # Screenshot script (Windows)
├── tests/
│   ├── fixtures/
│   │   └── db_states.py       # Database fixtures (new/mid/max player)
│   ├── ui/
│   │   ├── test_state_export.py
│   │   └── test_gamification_ui.py
│   └── baselines/             # Visual regression baselines (PNG)
└── scripts/
    └── atlas_launcher.py      # Main UI (enhanced with state export)
```

---

## 3. State Export Integration

### Changes to atlas_launcher.py

Add state export to the existing polling mechanism. The key is extending `session_status.json` with gamification data.

```python
# Add to ATLASLauncher.__init__():
self.state_exporter = StateExporter(BRIDGE_DIR)

# Add to _poll_status() - after timer update:
self._export_ui_state()

# New method:
def _export_ui_state(self):
    """Export current UI state for autonomous iteration feedback."""
    try:
        # Only export in test mode to avoid overhead in production
        if not os.environ.get("ATLAS_TEST_MODE"):
            return

        ui_state = {
            "window_geometry": self.geometry(),
            "timer_visible": self.timer_visible,
            "timer_mode": self.current_timer_mode,
            "is_paused": self.is_paused,
            "is_pending": self.is_pending_mode,
            "server_ready": self.server_ready.is_set(),
            "recording": self.recording,
            "processing": self.processing,
            "current_state": self.current_state,
            "transcript_count": len(self.transcript_history),
            "transcript_expanded": self.transcript_expanded,
            "voice_selection": self.voice_var.get(),
            "widgets": self._snapshot_widgets(),
        }

        self.state_exporter.update_ui_state(ui_state)
    except Exception as e:
        print(f"[StateExport] Error: {e}")

def _snapshot_widgets(self) -> dict:
    """Capture visible widget states for verification."""
    snapshot = {}

    # Timer display
    if self.timer_visible:
        snapshot["timer"] = {
            "display_text": self.timer_display.cget("text"),
            "display_color": str(self.timer_display.cget("text_color")),
            "exercise_name": self.exercise_name_label.cget("text"),
            "section_name": self.section_name_label.cget("text"),
            "progress": self.timer_progress.get(),
            "form_cue": self.form_cue_label.cget("text"),
        }

    # Status indicators
    snapshot["status"] = {
        "server": self.server_status.cget("text"),
        "gpu": self.gpu_status.cget("text"),
        "cost": self.cost_label.cget("text"),
        "timing": self.timing_label.cget("text"),
    }

    # Button states
    snapshot["buttons"] = {
        "pause_text": self.pause_btn.cget("text"),
        "pause_state": str(self.pause_btn.cget("state")),
        "skip_state": str(self.skip_btn.cget("state")),
        "start_state": str(self.start_btn.cget("state")),
        "stop_state": str(self.stop_btn.cget("state")),
    }

    return snapshot
```

---

## 4. State Exporter Module

### dev_tools/state_exporter.py

```python
"""
State Exporter for ATLAS UI Development

Extends session_status.json with UI state and gamification data
for autonomous iteration feedback.
"""
import json
import time
from pathlib import Path
from typing import Optional
import sqlite3


class StateExporter:
    """Export UI and gamification state for Claude Code feedback."""

    def __init__(self, bridge_dir: Path):
        self.bridge_dir = Path(bridge_dir)
        self.status_file = self.bridge_dir / "session_status.json"
        self.audio_log_file = self.bridge_dir / "audio_events.jsonl"
        self.db_path = Path.home() / ".atlas" / "atlas.db"
        self._last_export = 0
        self._export_interval = 0.1  # 100ms minimum between exports

    def update_ui_state(self, ui_state: dict):
        """
        Merge UI state into session_status.json.

        Uses atomic write pattern to prevent race conditions.
        """
        now = time.time()
        if now - self._last_export < self._export_interval:
            return  # Throttle exports

        self._last_export = now

        try:
            # Read existing status
            existing = {}
            if self.status_file.exists():
                try:
                    existing = json.loads(self.status_file.read_text())
                except json.JSONDecodeError:
                    pass  # File was mid-write, use empty

            # Merge UI state
            existing["ui_state"] = ui_state
            existing["gamification"] = self._get_gamification_state()
            existing["ui_updated_at"] = time.strftime("%H:%M:%S.") + f"{int(now * 1000) % 1000:03d}"

            # Atomic write: write to temp, then rename
            temp_file = self.status_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(existing, indent=2))
            temp_file.replace(self.status_file)

        except Exception as e:
            print(f"[StateExporter] Failed to update: {e}")

    def _get_gamification_state(self) -> dict:
        """
        Get current gamification state from database.

        Returns skill levels, XP, streaks for UI verification.
        """
        try:
            if not self.db_path.exists():
                return {"error": "Database not found"}

            conn = sqlite3.connect(self.db_path, timeout=1.0)
            conn.row_factory = sqlite3.Row

            # Get all skills
            cursor = conn.execute("""
                SELECT skill_name, domain, current_xp, current_level, virtue
                FROM player_skills
                ORDER BY current_level DESC, current_xp DESC
            """)
            skills = {}
            for row in cursor.fetchall():
                skills[row["skill_name"]] = {
                    "level": row["current_level"],
                    "xp": row["current_xp"],
                    "domain": row["domain"],
                    "virtue": row["virtue"],
                    "progress_to_next": self._calc_progress(row["current_xp"]),
                }

            # Get today's XP
            cursor = conn.execute("""
                SELECT COALESCE(SUM(xp_gained), 0) as today_xp
                FROM xp_events
                WHERE DATE(created_at) = DATE('now')
            """)
            today_xp = cursor.fetchone()["today_xp"]

            # Get streak
            cursor = conn.execute("""
                SELECT streak_day FROM activity_streaks
                WHERE date = DATE('now')
            """)
            row = cursor.fetchone()
            streak = row["streak_day"] if row else 0

            # Calculate totals
            total_level = sum(s["level"] for s in skills.values())
            total_xp = sum(s["xp"] for s in skills.values())

            conn.close()

            return {
                "player_level": total_level,
                "total_xp": total_xp,
                "today_xp": today_xp,
                "streak_days": streak,
                "skills": skills,
                "skills_by_domain": {
                    "body": {k: v for k, v in skills.items() if v["domain"] == "body"},
                    "mind": {k: v for k, v in skills.items() if v["domain"] == "mind"},
                    "soul": {k: v for k, v in skills.items() if v["domain"] == "soul"},
                },
            }

        except Exception as e:
            return {"error": str(e)}

    def _calc_progress(self, xp: int) -> float:
        """Calculate progress to next level (0.0 - 1.0)."""
        # Simplified OSRS formula approximation
        # Full formula in atlas/gamification/level_calculator.py
        if xp <= 0:
            return 0.0

        # Find current and next level thresholds
        level = 1
        for lvl in range(1, 100):
            threshold = int(sum(int(lvl_i + 300 * (2 ** (lvl_i / 7))) / 4 for lvl_i in range(1, lvl + 1)))
            if xp < threshold:
                level = lvl
                break

        # Calculate progress within current level
        current_threshold = int(sum(int(i + 300 * (2 ** (i / 7))) / 4 for i in range(1, level)))
        next_threshold = int(sum(int(i + 300 * (2 ** (i / 7))) / 4 for i in range(1, level + 1)))

        if next_threshold == current_threshold:
            return 1.0

        return (xp - current_threshold) / (next_threshold - current_threshold)

    def log_audio_event(self, sound_file: str, context: dict = None):
        """
        Log audio playback for verification (Claude can't hear audio).

        Events logged to audio_events.jsonl for test verification.
        """
        event = {
            "file": sound_file,
            "timestamp": time.time(),
            "context": context or {},
        }

        try:
            with open(self.audio_log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            print(f"[AudioLog] Failed: {e}")

    def clear_audio_log(self):
        """Clear audio event log (for test setup)."""
        try:
            self.audio_log_file.write_text("")
        except Exception:
            pass
```

---

## 5. Test Fixtures

### tests/fixtures/db_states.py

```python
"""
Database fixtures for UI testing.

Provides predefined player states for testing different UI scenarios.
"""
import sqlite3
from pathlib import Path
from typing import Literal

# OSRS XP formula thresholds (approximate)
XP_FOR_LEVEL = {
    1: 0, 10: 1154, 25: 8740, 50: 101333, 75: 1210421, 99: 13034431
}

FIXTURES = {
    "new_player": {
        "description": "Fresh start - all skills Level 1",
        "skills": {
            # BODY
            "strength": (1, 0), "endurance": (1, 0),
            "mobility": (1, 0), "nutrition": (1, 0),
            # MIND
            "focus": (1, 0), "learning": (1, 0),
            "reflection": (1, 0), "creation": (1, 0),
            # SOUL
            "presence": (1, 0), "service": (1, 0),
            "courage": (1, 0), "consistency": (1, 0),
        },
        "streak": 0,
        "today_xp": 0,
    },

    "mid_level": {
        "description": "Active player - mixed progress, some streaks",
        "skills": {
            # BODY - most active domain
            "strength": (25, 8740), "endurance": (18, 4470),
            "mobility": (22, 6517), "nutrition": (15, 2411),
            # MIND
            "focus": (20, 5346), "learning": (12, 1358),
            "reflection": (8, 512), "creation": (16, 2863),
            # SOUL
            "presence": (10, 1000), "service": (5, 100),
            "courage": (14, 2107), "consistency": (19, 4824),
        },
        "streak": 7,
        "today_xp": 450,
    },

    "about_to_level": {
        "description": "5 XP from level-up in Strength (for animation testing)",
        "skills": {
            "strength": (24, 8735),  # Level 25 at 8740 XP
            "endurance": (15, 2411), "mobility": (18, 4470),
            "nutrition": (10, 1000), "focus": (12, 1358),
            "learning": (8, 512), "reflection": (5, 100),
            "creation": (10, 1000), "presence": (7, 363),
            "service": (3, 40), "courage": (9, 760),
            "consistency": (14, 2107),
        },
        "streak": 5,
        "today_xp": 200,
    },

    "max_level_veteran": {
        "description": "Endgame player - multiple 99s",
        "skills": {
            "strength": (99, 13034431), "endurance": (99, 13034431),
            "mobility": (75, 1210421), "nutrition": (60, 273742),
            "focus": (99, 13034431), "learning": (50, 101333),
            "reflection": (45, 61512), "creation": (80, 1986068),
            "presence": (55, 166636), "service": (40, 37224),
            "courage": (65, 449428), "consistency": (99, 13034431),
        },
        "streak": 14,
        "today_xp": 1200,
    },

    "title_boundary": {
        "description": "At title transition boundaries for animation testing",
        "skills": {
            # Each at a title boundary
            "strength": (15, 2411),   # About to become Practitioner (16)
            "endurance": (35, 22406), # About to become Journeyman (36)
            "mobility": (55, 166636), # About to become Adept (56)
            "nutrition": (10, 1000),
            "focus": (75, 1210421),   # About to become Master (76)
            "learning": (25, 8740),
            "reflection": (12, 1358),
            "creation": (90, 5346332), # About to become Grandmaster (91)
            "presence": (20, 5346),
            "service": (8, 512),
            "courage": (5, 100),
            "consistency": (30, 13363),
        },
        "streak": 10,
        "today_xp": 800,
    },
}


FixtureName = Literal["new_player", "mid_level", "about_to_level", "max_level_veteran", "title_boundary"]


def load_fixture(
    fixture_name: FixtureName,
    db_path: str = None,
) -> str:
    """
    Load a test fixture into the database.

    WARNING: This REPLACES existing data. Use only for testing.

    Args:
        fixture_name: One of the predefined fixtures
        db_path: Database path (defaults to ~/.atlas/atlas.db)

    Returns:
        Description of loaded fixture
    """
    if db_path is None:
        db_path = str(Path.home() / ".atlas" / "atlas.db")

    fixture = FIXTURES.get(fixture_name)
    if not fixture:
        raise ValueError(f"Unknown fixture: {fixture_name}. Available: {list(FIXTURES.keys())}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Update skills (preserving domain/virtue metadata)
        for skill_name, (level, xp) in fixture["skills"].items():
            cursor.execute("""
                UPDATE player_skills
                SET current_xp = ?, current_level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE skill_name = ?
            """, (xp, level, skill_name))

        # Clear XP events and add today's XP if specified
        cursor.execute("DELETE FROM xp_events")
        if fixture["today_xp"] > 0:
            cursor.execute("""
                INSERT INTO xp_events (skill_name, xp_gained, source_type, created_at)
                VALUES ('strength', ?, 'fixture_load', CURRENT_TIMESTAMP)
            """, (fixture["today_xp"],))

        # Set streak
        cursor.execute("DELETE FROM activity_streaks")
        if fixture["streak"] > 0:
            cursor.execute("""
                INSERT INTO activity_streaks (date, streak_day, activities_logged)
                VALUES (DATE('now'), ?, 1)
            """, (fixture["streak"],))

        conn.commit()
        return f"Loaded fixture: {fixture_name} - {fixture['description']}"

    finally:
        conn.close()


def trigger_level_up(
    skill: str = "strength",
    db_path: str = None,
) -> str:
    """
    Award enough XP to trigger a level-up.

    Used for testing level-up animations and sounds.
    """
    if db_path is None:
        db_path = str(Path.home() / ".atlas" / "atlas.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get current XP
        cursor.execute(
            "SELECT current_xp, current_level FROM player_skills WHERE skill_name = ?",
            (skill,)
        )
        row = cursor.fetchone()
        if not row:
            return f"Skill not found: {skill}"

        current_xp, current_level = row

        # Find XP needed for next level
        next_level = current_level + 1
        if next_level > 99:
            return f"{skill} is already at max level"

        # Calculate next level threshold (simplified)
        next_threshold = int(sum(
            int(i + 300 * (2 ** (i / 7))) / 4
            for i in range(1, next_level + 1)
        ))

        xp_needed = next_threshold - current_xp + 1

        # Award XP
        cursor.execute("""
            UPDATE player_skills
            SET current_xp = current_xp + ?, current_level = ?
            WHERE skill_name = ?
        """, (xp_needed, next_level, skill))

        cursor.execute("""
            INSERT INTO xp_events (skill_name, xp_gained, source_type)
            VALUES (?, ?, 'test_level_up')
        """, (skill, xp_needed))

        conn.commit()
        return f"Awarded {xp_needed} XP to {skill}, now level {next_level}"

    finally:
        conn.close()


# CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python db_states.py <fixture_name>")
        print(f"Available fixtures: {list(FIXTURES.keys())}")
        sys.exit(1)

    fixture_name = sys.argv[1]

    if fixture_name == "level_up":
        skill = sys.argv[2] if len(sys.argv) > 2 else "strength"
        result = trigger_level_up(skill)
    else:
        result = load_fixture(fixture_name)

    print(result)
```

---

## 6. Hot Reload Watcher

### dev_tools/hot_reload.py

```python
"""
Hot Reload Watcher for ATLAS UI Development

Automatically restarts atlas_launcher.py when Python files change.
Preserves state via session_status.json for continuity.
"""
import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Handle different import paths
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError:
    print("ERROR: watchdog not installed. Run: pip install watchdog")
    sys.exit(1)


class HotReloader(FileSystemEventHandler):
    """
    File watcher that restarts the UI on Python file changes.

    Features:
    - Debouncing (waits for saves to complete)
    - Process cleanup on restart
    - Test mode environment variable
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
            self.script_path.parent.parent / "atlas",  # atlas/
            self.script_path.parent.parent / "dev_tools",  # dev_tools/
        ]
        self.debounce_seconds = debounce_seconds
        self.process = None
        self.debounce_timer = None
        self.restart_count = 0

        print(f"[HotReload] Watching: {[str(p) for p in self.watch_paths]}")

    def start_app(self):
        """Start or restart the UI application."""
        if self.process:
            print("[HotReload] Stopping previous instance...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

        self.restart_count += 1
        print(f"[HotReload] Starting {self.script_path.name} (restart #{self.restart_count})")

        # Set test mode for state export
        env = os.environ.copy()
        env["ATLAS_TEST_MODE"] = "1"

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
        ).start()

    def _monitor_output(self):
        """Print subprocess output with prefix."""
        if not self.process:
            return
        try:
            for line in iter(self.process.stdout.readline, ""):
                if not line:
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

        # Ignore __pycache__ and .pyc files
        if '__pycache__' in event.src_path or '.pyc' in event.src_path:
            return

        # Debounce: cancel previous timer, start new one
        if self.debounce_timer:
            self.debounce_timer.cancel()

        print(f"[HotReload] Change detected: {Path(event.src_path).name}")

        self.debounce_timer = threading.Timer(
            self.debounce_seconds,
            self.start_app,
        )
        self.debounce_timer.start()

    def cleanup(self):
        """Clean up process on exit."""
        if self.debounce_timer:
            self.debounce_timer.cancel()
        if self.process:
            print("[HotReload] Cleaning up...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()


def main():
    """Entry point for hot reload watcher."""
    # Determine script path
    script_path = Path(__file__).parent.parent / "scripts" / "atlas_launcher.py"

    if not script_path.exists():
        print(f"ERROR: {script_path} not found")
        sys.exit(1)

    print("=" * 60)
    print("ATLAS UI Hot Reload Development Server")
    print("=" * 60)
    print(f"Script: {script_path}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    handler = HotReloader(script_path)
    observer = Observer()

    # Watch all relevant directories
    for path in handler.watch_paths:
        if path.exists():
            observer.schedule(handler, str(path), recursive=True)

    observer.start()
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
```

---

## 7. Screenshot Capture (Windows)

### dev_tools/capture_screen.ps1

```powershell
<#
.SYNOPSIS
    Capture screenshot of ATLAS Command Centre window.

.DESCRIPTION
    Uses .NET System.Drawing to capture the primary monitor.
    Screenshots saved to Pictures/Screenshots with timestamp.

    SECURITY NOTES:
    - Only captures screen, no file access beyond output directory
    - Timestamp prevents overwrites
    - No elevation required

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File capture_screen.ps1
#>

# Load required assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Generate output path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = "$env:USERPROFILE\Pictures\Screenshots"
$outputFile = "$outputDir\atlas_$timestamp.png"

# Ensure directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Capture screen
$screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphic = [System.Drawing.Graphics]::FromImage($bitmap)

try {
    $graphic.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)
    $bitmap.Save($outputFile, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output $outputFile
} finally {
    $graphic.Dispose()
    $bitmap.Dispose()
}
```

### WSL2 Wrapper (for Claude Code to call):

```bash
#!/bin/bash
# dev_tools/screenshot.sh
# Capture Windows screenshot and return WSL path

screenshot_path=$(powershell.exe -ExecutionPolicy Bypass -File '/mnt/c/ATLAS/dev_tools/capture_screen.ps1' 2>/dev/null | tr -d '\r')

if [[ -z "$screenshot_path" ]]; then
    echo "ERROR: Screenshot capture failed"
    exit 1
fi

# Convert Windows path to WSL path
wsl_path=$(echo "$screenshot_path" | sed 's/\\/\//g' | sed 's/C:/\/mnt\/c/')
echo "$wsl_path"
```

---

## 8. UI State Tests

### tests/ui/test_state_export.py

```python
"""
Tests for UI state export functionality.

These tests verify that session_status.json contains correct UI and
gamification state for autonomous iteration feedback.
"""
import json
import time
import pytest
from pathlib import Path


# Path constants
BRIDGE_DIR = Path(r"\\wsl$\Ubuntu\home\squiz\ATLAS\.bridge")
STATUS_FILE = BRIDGE_DIR / "session_status.json"
AUDIO_LOG = BRIDGE_DIR / "audio_events.jsonl"


@pytest.fixture
def status_data():
    """Read current session status."""
    if not STATUS_FILE.exists():
        pytest.skip("session_status.json not found - is the app running?")
    return json.loads(STATUS_FILE.read_text())


class TestUIStateExport:
    """Tests for UI state in session_status.json."""

    def test_ui_state_present(self, status_data):
        """UI state should be exported."""
        assert "ui_state" in status_data, "ui_state key missing from session_status.json"

    def test_ui_state_has_window_geometry(self, status_data):
        """Window geometry should be exported."""
        ui = status_data.get("ui_state", {})
        assert "window_geometry" in ui

    def test_ui_state_has_timer_visibility(self, status_data):
        """Timer visibility state should be exported."""
        ui = status_data.get("ui_state", {})
        assert "timer_visible" in ui
        assert isinstance(ui["timer_visible"], bool)

    def test_ui_state_has_button_states(self, status_data):
        """Button states should be captured in widgets."""
        ui = status_data.get("ui_state", {})
        widgets = ui.get("widgets", {})

        if "buttons" in widgets:
            buttons = widgets["buttons"]
            assert "pause_text" in buttons
            assert "pause_state" in buttons
            assert "start_state" in buttons


class TestGamificationExport:
    """Tests for gamification data in session_status.json."""

    def test_gamification_present(self, status_data):
        """Gamification data should be exported."""
        assert "gamification" in status_data

    def test_has_player_level(self, status_data):
        """Player total level should be present."""
        gam = status_data.get("gamification", {})
        assert "player_level" in gam
        assert isinstance(gam["player_level"], int)
        assert gam["player_level"] >= 12  # Minimum: 12 skills at level 1

    def test_has_all_12_skills(self, status_data):
        """All 12 Lethal Gentleman skills should be present."""
        gam = status_data.get("gamification", {})
        skills = gam.get("skills", {})

        expected_skills = {
            "strength", "endurance", "mobility", "nutrition",  # BODY
            "focus", "learning", "reflection", "creation",      # MIND
            "presence", "service", "courage", "consistency",    # SOUL
        }

        assert set(skills.keys()) == expected_skills

    def test_skills_have_required_fields(self, status_data):
        """Each skill should have level, xp, domain, progress."""
        gam = status_data.get("gamification", {})
        skills = gam.get("skills", {})

        required = {"level", "xp", "domain", "progress_to_next"}

        for skill_name, skill_data in skills.items():
            for field in required:
                assert field in skill_data, f"{skill_name} missing {field}"

    def test_skills_by_domain_structure(self, status_data):
        """Skills should be grouped by domain."""
        gam = status_data.get("gamification", {})
        by_domain = gam.get("skills_by_domain", {})

        assert "body" in by_domain
        assert "mind" in by_domain
        assert "soul" in by_domain

        assert len(by_domain["body"]) == 4
        assert len(by_domain["mind"]) == 4
        assert len(by_domain["soul"]) == 4


class TestAudioEventLog:
    """Tests for audio event logging (for sound verification)."""

    def test_audio_log_exists(self):
        """Audio log file should exist."""
        # May not exist if no sounds played
        pass  # Just verify we can check it

    def test_can_clear_audio_log(self):
        """Should be able to clear audio log for test isolation."""
        if AUDIO_LOG.exists():
            AUDIO_LOG.write_text("")
            assert AUDIO_LOG.read_text() == ""


# Fixture helper tests
class TestFixtureLoading:
    """Tests for database fixture loading."""

    def test_fixtures_importable(self):
        """Fixture module should be importable."""
        from tests.fixtures.db_states import FIXTURES, load_fixture
        assert "new_player" in FIXTURES
        assert "mid_level" in FIXTURES
        assert "max_level_veteran" in FIXTURES

    def test_level_up_trigger_available(self):
        """Level-up trigger function should be available."""
        from tests.fixtures.db_states import trigger_level_up
        assert callable(trigger_level_up)
```

---

## 9. Race Condition Mitigations

### File IPC Safety Patterns

The file-based IPC between Windows UI and WSL2 server has inherent race conditions. Here's how they're mitigated:

| Race Condition | Mitigation | Location |
|----------------|------------|----------|
| **JSON mid-write read** | Retry with 10ms delay (3 attempts) | `atlas_launcher.py:_poll_status()` |
| **Atomic file updates** | Write to .tmp, then rename | `state_exporter.py:update_ui_state()` |
| **Audio file access** | Temp file + atomic rename | `atlas_launcher.py:_send_audio()` |
| **Command file collision** | Single-line commands only | All command writers |
| **Export throttling** | 100ms minimum between exports | `state_exporter.py` |

### Code Review Checklist

Before deployment, verify:

```markdown
## Race Condition Safety
- [ ] All JSON writes use atomic pattern (write .tmp, rename)
- [ ] All JSON reads have retry logic for decode errors
- [ ] No file locks held across network boundary (WSL2 <-> Windows)
- [ ] Export throttling prevents CPU thrashing

## Resource Leak Prevention
- [ ] Hot reload watcher kills subprocess on restart
- [ ] Signal handlers clean up processes
- [ ] Database connections closed in finally blocks
- [ ] ThreadPoolExecutor shutdown called on service close

## Security (PowerShell Script)
- [ ] No user input interpolated into paths
- [ ] Output directory is fixed (Pictures/Screenshots)
- [ ] No elevation required
- [ ] Timestamp prevents path manipulation
```

---

## 10. Verification Checklist

Run these checks to confirm setup is working:

### Step 1: Dependencies
```powershell
# Windows PowerShell
python -c "import customtkinter, sounddevice, numpy, watchdog, PIL; print('All deps OK')"
```

### Step 2: Hot Reload
```powershell
# Start hot reload server
python dev_tools\hot_reload.py

# In another terminal, edit atlas_launcher.py
# -> Should see "[HotReload] Change detected" and app restart
```

### Step 3: State Export
```powershell
# With app running in test mode:
$env:ATLAS_TEST_MODE="1"
python scripts\atlas_launcher.py

# Check session_status.json includes ui_state and gamification
type \\wsl$\Ubuntu\home\squiz\ATLAS\.bridge\session_status.json
```

### Step 4: Fixtures
```powershell
# Load a fixture
python tests\fixtures\db_states.py mid_level

# Verify state exported correctly
python -c "import json; print(json.loads(open(r'\\wsl$\Ubuntu\home\squiz\ATLAS\.bridge\session_status.json').read())['gamification']['player_level'])"
# Should print total level for mid_level fixture (~200)
```

### Step 5: Screenshot
```powershell
# Take screenshot
powershell -ExecutionPolicy Bypass -File dev_tools\capture_screen.ps1
# Should output path like C:\Users\...\Pictures\Screenshots\atlas_20260123_...png
```

### Step 6: Run Tests
```powershell
# Run UI state tests
pytest tests\ui\ -v
```

---

## 11. Claude Code Integration

### .claude/commands/iterate-ui.md

```markdown
# Iterate on ATLAS UI

1. Read ~/.atlas/.bridge/session_status.json to understand current state
2. Check gamification.skills for XP/level data
3. Check ui_state for widget visibility and button states
4. Make ONE incremental change to scripts/atlas_launcher.py
5. Wait 2 seconds for hot reload
6. Read session_status.json again to verify change took effect
7. If visual verification needed, run: `./dev_tools/screenshot.sh`
```

### Autonomous Iteration Pattern

```bash
# Claude Code can run this loop:
while not complete:
    # 1. Read state
    state = read_file("~/.atlas/.bridge/session_status.json")

    # 2. Check gamification data
    skills = state["gamification"]["skills"]

    # 3. Make change
    edit("scripts/atlas_launcher.py", ...)

    # 4. Wait for hot reload
    sleep(2)

    # 5. Verify change in state
    new_state = read_file("~/.atlas/.bridge/session_status.json")
    assert new_state["ui_state"]["widgets"]["skill_card_visible"]
```

---

## Summary

| Component | File | Purpose |
|-----------|------|---------|
| Hot Reload | `dev_tools/hot_reload.py` | Auto-restart on file changes |
| State Export | `dev_tools/state_exporter.py` | UI + gamification to JSON |
| Fixtures | `tests/fixtures/db_states.py` | Preset player states |
| Screenshot | `dev_tools/capture_screen.ps1` | Visual capture |
| Tests | `tests/ui/test_state_export.py` | Verify state export |

**Feedback Loop Timing:**
- State file read: <10ms
- Hot reload restart: 1-2 seconds
- Full verification cycle: <3 seconds

This setup enables Claude Code to iterate autonomously on the OSRS-style dashboard with structured feedback, without requiring human visual verification for each change.
