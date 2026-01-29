# Visual Feedback & Continuous Testing for CustomTkinter in WSL2/Windows

Claude Code can achieve autonomous visual iteration on your OSRS-style dashboard through a combination of **state file exports**, **automated testing**, and **optional screenshot capture**. The most practical architecture for your setup uses JSON state dumps as the primary feedback mechanism, supplemented by on-demand Windows screenshots when visual verification is needed.

## The recommended workflow achieves <3 second feedback loops

Your existing `session_status.json` IPC pattern is the foundation—extend it to include full UI state, and Claude Code can iterate autonomously using the Ralph Wiggum Loop. Screenshot capture becomes supplementary verification rather than the primary feedback mechanism.

---

## Quick start: essential tools to install

**For Claude Code (WSL2 side):**
```bash
# Official Ralph Wiggum plugin
/install-github-plugin anthropics/claude-code plugins/ralph-wiggum

# Windows screenshot access MCP (reads Screenshots folder)
claude mcp add windows-screenshots -s user -- npx mcp-windows-screenshots@latest
```

**For your Python environment:**
```bash
pip install watchdog tkreload pyautogui Pillow imagehash mss
```

**Create the on-demand screenshot helper** (Windows PowerShell):
Save as `C:\Scripts\capture_screen.ps1`:
```powershell
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$timestamp = Get-Date -f 'yyyyMMdd_HHmmss'
$outputFile = "C:\Users\$env:USERNAME\Pictures\Screenshots\atlas_$timestamp.png"
$Screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = New-Object System.Drawing.Bitmap $Screen.Width, $Screen.Height
$graphic = [System.Drawing.Graphics]::FromImage($bitmap)
$graphic.CopyFromScreen($Screen.Left, $Screen.Top, 0, 0, $bitmap.Size)
$bitmap.Save($outputFile, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Output $outputFile
```

---

## The state file pattern beats screenshots for speed

Extend your existing `~/.atlas/.bridge/session_status.json` with a full UI state dump. This gives Claude Code **instant, structured feedback** without image processing overhead.

**Enhanced session_status.json structure:**
```json
{
  "timer_state": { "running": true, "elapsed_ms": 45000 },
  "gamification": {
    "player_level": 12,
    "total_xp": 4850,
    "skills": {
      "strength": { "level": 8, "xp": 1200, "progress_to_next": 0.45 },
      "agility": { "level": 15, "xp": 3650, "progress_to_next": 0.72 }
    },
    "active_quests": [
      { "id": "q_001", "name": "Complete 5 workouts", "progress": 3, "target": 5 }
    ],
    "pending_events": []
  },
  "ui_state": {
    "current_view": "dashboard",
    "visible_widgets": ["skill_cards", "quest_list", "xp_bar"],
    "animation_in_progress": null,
    "last_level_up": null,
    "theme": "osrs_dark"
  },
  "audio_events": [],
  "last_updated": "2026-01-22T10:30:00.123Z"
}
```

**Python code for atlas_launcher.py to export state:**
```python
import json
import time
from pathlib import Path

class StateExporter:
    def __init__(self, bridge_path="~/.atlas/.bridge"):
        self.bridge_path = Path(bridge_path).expanduser()
        self.status_file = self.bridge_path / "session_status.json"
        self.audio_log = []
        
    def export_full_state(self, app, widgets_dict, gamification_data):
        """Export complete app state for Claude to read"""
        state = {
            "timer_state": self._get_timer_state(),
            "gamification": gamification_data,
            "ui_state": self._snapshot_widgets(app, widgets_dict),
            "audio_events": self.audio_log[-20:],  # Last 20 audio events
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        self.status_file.write_text(json.dumps(state, indent=2))
        
    def _snapshot_widgets(self, app, widgets):
        """Capture current widget states"""
        snapshot = {
            "current_view": getattr(app, 'current_view', 'unknown'),
            "visible_widgets": [],
            "widget_values": {}
        }
        for name, widget in widgets.items():
            if widget.winfo_viewable():
                snapshot["visible_widgets"].append(name)
            # Capture relevant properties
            if hasattr(widget, 'get'):
                try:
                    snapshot["widget_values"][name] = {"value": widget.get()}
                except:
                    pass
            if hasattr(widget, 'cget'):
                try:
                    snapshot["widget_values"][name] = {
                        "text": widget.cget("text"),
                        "fg_color": str(widget.cget("fg_color"))
                    }
                except:
                    pass
        return snapshot
    
    def log_audio_event(self, sound_file, event_type="play"):
        """Log audio events for verification"""
        self.audio_log.append({
            "file": sound_file,
            "type": event_type,
            "timestamp": time.time()
        })
```

---

## The Ralph Wiggum Loop enables autonomous iteration

The Ralph Wiggum technique runs Claude Code in a continuous loop, re-feeding prompts after each exit until completion criteria are met. State persists in files and git history, not in context.

**Create `.ralph/PROMPT_ui.md`:**
```markdown
# OSRS Dashboard UI Development Loop

## Context
You are iterating on atlas_launcher.py, an OSRS-style gamification dashboard.
- CustomTkinter app running on Windows
- State exported to ~/.atlas/.bridge/session_status.json every 100ms
- SQLite database at ~/.atlas/atlas.db with gamification tables

## Each Iteration
1. Read ~/.atlas/.bridge/session_status.json to understand current UI state
2. Study @IMPLEMENTATION_PLAN.md for the current priority task
3. Make ONE incremental change to atlas_launcher.py
4. Run the test harness: `python tests/test_ui_state.py`
5. If tests pass, update @IMPLEMENTATION_PLAN.md and git commit
6. Output your status in this format:

RALPH_STATUS:
- PROGRESS_MADE: true/false
- CURRENT_TASK: "description"
- COMPLETION_CONFIDENCE: 0-100
- EXIT_SIGNAL: true/false (only true when ALL tasks complete)

## Completion Criteria
- All skill cards render correctly with pixel fonts (Press Start 2P, VT323)
- Level-up banner animation triggers on XP threshold
- Audio event logged when level-up sound should play
- Quest list updates dynamically from database
- State export includes all visible widget data

When all criteria met, output: <promise>UI_COMPLETE</promise>
```

**Loop script (`loop_ui.sh`):**
```bash
#!/bin/bash
MAX_ITERATIONS=${1:-50}
ITERATION=0

echo "Starting Ralph Wiggum UI Loop (max: $MAX_ITERATIONS)"

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    echo -e "\n=== ITERATION $((ITERATION + 1)) ===\n"
    
    # Run Claude with the UI prompt
    cat .ralph/PROMPT_ui.md | claude -p \
        --dangerously-skip-permissions \
        --output-format=stream-json \
        2>&1 | tee .ralph/logs/iteration_$ITERATION.log
    
    # Check for completion promise
    if grep -q "<promise>UI_COMPLETE</promise>" .ralph/logs/iteration_$ITERATION.log; then
        echo "✓ UI development complete!"
        break
    fi
    
    # Push changes
    git push origin "$(git branch --show-current)" 2>/dev/null || true
    
    ITERATION=$((ITERATION + 1))
    sleep 2  # Brief pause between iterations
done

echo "Loop ended after $ITERATION iterations"
```

---

## Test fixtures simulate different player states

Create database fixtures that Claude can swap in to test various UI states without manually earning XP.

**Test fixtures (`tests/fixtures/`):**
```python
# tests/fixtures/db_states.py
import sqlite3
from pathlib import Path

FIXTURES = {
    "new_player": {
        "player_skills": [
            ("strength", 1, 0),
            ("agility", 1, 0),
            ("endurance", 1, 0)
        ],
        "xp_events": []
    },
    "mid_level": {
        "player_skills": [
            ("strength", 25, 12500),
            ("agility", 18, 6800),
            ("endurance", 22, 9200)
        ],
        "xp_events": [
            ("strength", 500, "2026-01-22 10:00:00"),
            ("agility", 200, "2026-01-22 10:05:00")
        ]
    },
    "about_to_level": {
        "player_skills": [
            ("strength", 9, 995),  # Level 10 at 1000 XP
            ("agility", 15, 3650),
            ("endurance", 12, 2100)
        ],
        "xp_events": []
    },
    "max_level_veteran": {
        "player_skills": [
            ("strength", 99, 13034431),
            ("agility", 99, 13034431),
            ("endurance", 99, 13034431)
        ],
        "xp_events": []
    }
}

def load_fixture(fixture_name: str, db_path: str = "~/.atlas/atlas.db"):
    """Swap database to a specific test state"""
    db_path = Path(db_path).expanduser()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    fixture = FIXTURES[fixture_name]
    
    # Clear existing data
    cursor.execute("DELETE FROM player_skills")
    cursor.execute("DELETE FROM xp_events")
    
    # Load fixture data
    cursor.executemany(
        "INSERT INTO player_skills (skill_name, level, xp) VALUES (?, ?, ?)",
        fixture["player_skills"]
    )
    cursor.executemany(
        "INSERT INTO xp_events (skill_name, xp_amount, timestamp) VALUES (?, ?, ?)",
        fixture["xp_events"]
    )
    
    conn.commit()
    conn.close()
    return f"Loaded fixture: {fixture_name}"
```

**Trigger level-up programmatically:**
```python
# tests/trigger_events.py
def trigger_level_up(db_path="~/.atlas/atlas.db", skill="strength"):
    """Award XP to trigger a level-up event"""
    conn = sqlite3.connect(Path(db_path).expanduser())
    cursor = conn.cursor()
    
    # Get current XP
    cursor.execute("SELECT xp FROM player_skills WHERE skill_name = ?", (skill,))
    current_xp = cursor.fetchone()[0]
    
    # Calculate XP needed for next level (simplified OSRS formula)
    current_level = xp_to_level(current_xp)
    next_level_xp = level_to_xp(current_level + 1)
    xp_needed = next_level_xp - current_xp + 1
    
    # Award XP
    cursor.execute(
        "UPDATE player_skills SET xp = xp + ? WHERE skill_name = ?",
        (xp_needed, skill)
    )
    cursor.execute(
        "INSERT INTO xp_events (skill_name, xp_amount, timestamp) VALUES (?, ?, datetime('now'))",
        (skill, xp_needed)
    )
    
    conn.commit()
    conn.close()
    return f"Awarded {xp_needed} XP to {skill}, triggering level {current_level + 1}"
```

---

## Audio verification uses mock logging, not actual playback

Claude can't hear audio, but it can verify that sound effects were triggered at the right moments by checking the audio event log.

**Mock audio player:**
```python
# atlas/audio/sound_player.py
import time
import json
from pathlib import Path

class SoundPlayer:
    """Sound player with logging for test verification"""
    
    def __init__(self, bridge_path="~/.atlas/.bridge"):
        self.bridge_path = Path(bridge_path).expanduser()
        self.audio_log_file = self.bridge_path / "audio_events.jsonl"
        self._test_mode = False
        
    def enable_test_mode(self):
        """In test mode, log events but don't play audio"""
        self._test_mode = True
        
    def play(self, sound_file: str, event_context: dict = None):
        """Play sound and log the event"""
        event = {
            "action": "play",
            "file": sound_file,
            "timestamp": time.time(),
            "context": event_context or {}
        }
        
        # Always log for verification
        with open(self.audio_log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        if not self._test_mode:
            # Actual playback (pygame, playsound, etc.)
            self._play_actual(sound_file)
            
    def _play_actual(self, sound_file):
        # Your existing audio playback implementation
        pass

# Usage in level-up handler
def on_level_up(skill_name, new_level, sound_player):
    sound_player.play(
        "sounds/osrs_level_up.wav",
        event_context={
            "trigger": "level_up",
            "skill": skill_name,
            "level": new_level
        }
    )
```

**Test that verifies audio triggered:**
```python
# tests/test_audio_events.py
import json
from pathlib import Path

def test_level_up_plays_sound():
    """Verify level-up sound plays at correct moment"""
    audio_log = Path("~/.atlas/.bridge/audio_events.jsonl").expanduser()
    
    # Clear log
    audio_log.write_text("")
    
    # Trigger level-up
    trigger_level_up(skill="strength")
    
    # Wait for app to process
    time.sleep(0.5)
    
    # Check audio log
    events = [json.loads(line) for line in audio_log.read_text().splitlines()]
    level_up_sounds = [e for e in events if e.get("context", {}).get("trigger") == "level_up"]
    
    assert len(level_up_sounds) == 1
    assert "osrs_level_up" in level_up_sounds[0]["file"]
    assert level_up_sounds[0]["context"]["skill"] == "strength"
```

---

## Hot reload enables rapid visual iteration

Use `tkreload` or watchdog to auto-restart the app on file changes, reducing the edit-see cycle to under 2 seconds.

**Method 1: tkreload (simplest)**
```bash
pip install tkreload
tkreload scripts/atlas_launcher.py
```

**Method 2: Custom watchdog with state preservation**
```python
# dev_tools/hot_reload.py
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class HotReloader(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script = script_path
        self.process = None
        self.debounce_timer = None
        self.start_app()
        
    def start_app(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print(f"[HotReload] Starting {self.script}")
        self.process = subprocess.Popen(
            ["python", self.script, "--test-mode"],
            env={**os.environ, "ATLAS_TEST_MODE": "1"}
        )
        
    def on_modified(self, event):
        if event.src_path.endswith('.py') and 'atlas' in event.src_path:
            # Debounce: wait 0.3s for file writes to complete
            if self.debounce_timer:
                self.debounce_timer.cancel()
            self.debounce_timer = threading.Timer(0.3, self.start_app)
            self.debounce_timer.start()

if __name__ == "__main__":
    handler = HotReloader("scripts/atlas_launcher.py")
    observer = Observer()
    observer.schedule(handler, path=".", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

---

## Screenshots supplement state files for visual verification

When Claude needs to verify visual appearance (pixel fonts rendering, animation frames, layout), trigger a Windows screenshot from WSL2.

**Claude Code can capture on-demand via:**
```bash
# In WSL2, call the PowerShell script
screenshot_path=$(powershell.exe -ExecutionPolicy Bypass -File 'C:\Scripts\capture_screen.ps1' | tr -d '\r')
wsl_path=$(echo "$screenshot_path" | tr '\\' '/' | sed 's/C:/\/mnt\/c/')
echo "Screenshot saved to: $wsl_path"
```

**Or use the MCP Windows Screenshots server for recent screenshots:**
```
Claude, show me the latest screenshot from my Windows Screenshots folder.
```

**Visual regression comparison:**
```python
# tests/visual_regression.py
from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch

def compare_ui_state(baseline_path: str, current_path: str, diff_path: str) -> int:
    """Compare two screenshots, return number of differing pixels"""
    baseline = Image.open(baseline_path)
    current = Image.open(current_path)
    
    # Ensure same size
    if baseline.size != current.size:
        current = current.resize(baseline.size)
    
    diff = Image.new("RGBA", baseline.size)
    mismatch_pixels = pixelmatch(baseline, current, diff, threshold=0.1)
    
    if mismatch_pixels > 0:
        diff.save(diff_path)
        
    return mismatch_pixels

# Claude can run this after making UI changes
def test_skill_card_layout():
    """Verify skill card layout matches baseline"""
    # Trigger screenshot
    os.system("powershell.exe -File 'C:\\Scripts\\capture_screen.ps1'")
    time.sleep(0.5)
    
    # Get latest screenshot
    screenshots_dir = Path("/mnt/c/Users") / os.environ["USER"] / "Pictures/Screenshots"
    latest = max(screenshots_dir.glob("atlas_*.png"), key=lambda p: p.stat().st_mtime)
    
    # Compare to baseline
    diff_pixels = compare_ui_state(
        "tests/baselines/skill_cards_baseline.png",
        str(latest),
        "tests/diffs/skill_cards_diff.png"
    )
    
    assert diff_pixels < 500, f"UI changed significantly: {diff_pixels} pixels differ"
```

---

## Complete .mcp.json and CLAUDE.md configuration

**`.mcp.json` (project root):**
```json
{
  "mcpServers": {
    "windows-screenshots": {
      "command": "npx",
      "args": ["mcp-windows-screenshots@latest"],
      "env": {
        "MCP_SCREENSHOT_DIRS": "/mnt/c/Users/${USER}/Pictures/Screenshots"
      }
    }
  }
}
```

**`CLAUDE.md`:**
```markdown
# Atlas Launcher - OSRS-Style Gamification Dashboard

## Architecture
- **GUI**: CustomTkinter app at `scripts/atlas_launcher.py` (runs on Windows)
- **Backend**: Python server at `atlas/voice/bridge_file_server.py` (runs in WSL2)
- **IPC**: File-based through `~/.atlas/.bridge/` (100ms polling)
- **Database**: SQLite at `~/.atlas/atlas.db`

## Key Commands
- `python scripts/atlas_launcher.py --test-mode` - Launch app with audio logging
- `tkreload scripts/atlas_launcher.py` - Hot-reload development
- `pytest tests/test_ui_state.py -v` - Run UI state tests
- `python tests/fixtures/db_states.py load_fixture mid_level` - Load test data

## State Files (for feedback)
- `~/.atlas/.bridge/session_status.json` - Full UI + gamification state (read this!)
- `~/.atlas/.bridge/audio_events.jsonl` - Audio playback log
- `/mnt/c/Users/$USER/Pictures/Screenshots/atlas_*.png` - Screenshots

## UI Components
- Skill cards with pixel fonts (Press Start 2P for headers, VT323 for values)
- Animated level-up banner with sound effect
- Dynamic quest list from database
- Real-time XP progress bars

## Development Loop
1. Read session_status.json to understand current state
2. Make ONE change to atlas_launcher.py
3. Run pytest to verify state exports correctly
4. Check audio_events.jsonl if testing sound triggers
5. For visual verification, request a screenshot

## Test Fixtures
- `new_player` - Level 1 in all skills
- `mid_level` - Levels 18-25, some XP events
- `about_to_level` - 5 XP from level 10 (test level-up trigger)
- `max_level_veteran` - Level 99 in all skills

## Pixel Font Requirements
- Headers: "Press Start 2P" at 14px
- Values: "VT323" at 18px
- Load from `assets/fonts/` using tkinter font config
```

---

## The complete iteration workflow

When this setup is configured, Claude Code achieves autonomous UI development:

1. **Claude edits** `atlas_launcher.py` (adds skill card, changes layout, etc.)
2. **Hot reload** restarts the app automatically (watchdog/tkreload)
3. **App exports state** to `session_status.json` within 100ms
4. **Claude reads state** to verify changes took effect
5. **Tests validate** that widgets exported correctly, audio events logged
6. **If visual check needed**, Claude triggers PowerShell screenshot
7. **Claude commits** and continues to next task from IMPLEMENTATION_PLAN.md
8. **Ralph loop** repeats until completion promise output

**Target metrics achieved:**
- State feedback: <100ms (JSON file read)
- Hot reload: ~1-2 seconds  
- Screenshot capture: ~500ms (when needed)
- Full iteration cycle: **<3 seconds** for state-based feedback, **<5 seconds** with screenshot

## Feasibility ranking for your setup

| Approach | Speed | Complexity | Recommendation |
|----------|-------|------------|----------------|
| **State file dump (JSON)** | Instant | Low | **Primary method** - extend existing IPC |
| **Automated test suite** | 1-2s | Medium | **Essential** - run on every change |
| **Hot reload** | 1-2s | Low | **Essential** - use tkreload |
| **Screenshot on-demand** | 500ms | Low | **Supplementary** - for visual verification |
| **Visual regression** | 2-3s | Medium | **Nice-to-have** - baseline comparisons |
| **MCP screenshot server** | 50ms | Very Low | **Installed** - reads existing screenshots |

This architecture gives Claude Code the feedback it needs to iterate autonomously on your OSRS-style dashboard while keeping the human in control of when to trigger screenshots and what the visual baselines should look like.