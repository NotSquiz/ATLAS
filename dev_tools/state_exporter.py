"""
State Exporter for ATLAS UI Development

Extends session_status.json with UI state and gamification data
for autonomous iteration feedback.

Usage:
    from dev_tools.state_exporter import StateExporter

    exporter = StateExporter(bridge_dir)
    exporter.update_ui_state(ui_state_dict)

Design:
    - Atomic writes prevent race conditions
    - Throttling (100ms) prevents CPU thrashing
    - Gamification data fetched from SQLite
    - Audio events logged for sound verification
"""
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


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

        Uses atomic write pattern to prevent race conditions:
        1. Write to .tmp file
        2. Rename to target (atomic on same filesystem)

        Args:
            ui_state: Dictionary of UI state to export
        """
        now = time.time()
        if now - self._last_export < self._export_interval:
            return  # Throttle exports

        self._last_export = now

        try:
            # Read existing status (with retry for mid-write reads)
            existing = self._read_existing_status()

            # Merge UI state
            existing["ui_state"] = ui_state
            existing["gamification"] = self._get_gamification_state()
            existing["ui_updated_at"] = time.strftime("%H:%M:%S.") + f"{int(now * 1000) % 1000:03d}"

            # Atomic write: write to temp, then rename
            temp_file = self.status_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(existing, indent=2))
            temp_file.replace(self.status_file)

        except Exception as e:
            logger.warning(f"[StateExporter] Failed to update: {e}")

    def _read_existing_status(self) -> dict:
        """Read existing session_status.json with retry for race conditions."""
        if not self.status_file.exists():
            return {}

        for attempt in range(3):
            try:
                return json.loads(self.status_file.read_text())
            except json.JSONDecodeError:
                if attempt < 2:
                    time.sleep(0.01)  # 10ms retry delay
                continue

        return {}  # All retries failed

    def _get_gamification_state(self) -> dict:
        """
        Get current gamification state from database.

        Returns skill levels, XP, streaks for UI verification.
        """
        try:
            if not self.db_path.exists():
                return {"error": "Database not found"}

            conn = sqlite3.connect(str(self.db_path), timeout=1.0)
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
                    "domain": row["domain"] or "body",
                    "virtue": row["virtue"] or "",
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
            logger.warning(f"[StateExporter] Gamification fetch failed: {e}")
            return {"error": str(e)}

    def _calc_progress(self, xp: int) -> float:
        """
        Calculate progress to next level (0.0 - 1.0).

        Uses OSRS XP formula approximation.
        """
        if xp <= 0:
            return 0.0

        # Find current level threshold
        level = 1
        for lvl in range(1, 100):
            threshold = int(sum(
                int(i + 300 * (2 ** (i / 7))) / 4
                for i in range(1, lvl + 1)
            ))
            if xp < threshold:
                level = lvl
                break
            level = lvl

        # Calculate progress within current level
        current_threshold = int(sum(
            int(i + 300 * (2 ** (i / 7))) / 4
            for i in range(1, level)
        )) if level > 1 else 0

        next_threshold = int(sum(
            int(i + 300 * (2 ** (i / 7))) / 4
            for i in range(1, level + 1)
        ))

        if next_threshold <= current_threshold:
            return 1.0

        return min(1.0, max(0.0, (xp - current_threshold) / (next_threshold - current_threshold)))

    def log_audio_event(self, sound_file: str, context: Optional[dict] = None):
        """
        Log audio playback for verification.

        Claude can't hear audio, but can verify sounds were triggered
        at the right moments by checking this log.

        Args:
            sound_file: Path or name of sound file
            context: Optional context (trigger type, skill, level, etc.)
        """
        event = {
            "file": sound_file,
            "timestamp": time.time(),
            "timestamp_str": time.strftime("%H:%M:%S"),
            "context": context or {},
        }

        try:
            with open(self.audio_log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.warning(f"[AudioLog] Failed to log: {e}")

    def clear_audio_log(self):
        """Clear audio event log (for test setup)."""
        try:
            self.audio_log_file.write_text("")
        except Exception:
            pass

    def get_audio_events(self, since: float = 0) -> list:
        """
        Get audio events since timestamp.

        Args:
            since: Unix timestamp to filter from (0 = all events)

        Returns:
            List of audio event dictionaries
        """
        if not self.audio_log_file.exists():
            return []

        events = []
        try:
            for line in self.audio_log_file.read_text().splitlines():
                if line.strip():
                    event = json.loads(line)
                    if event.get("timestamp", 0) >= since:
                        events.append(event)
        except Exception as e:
            logger.warning(f"[AudioLog] Read failed: {e}")

        return events
