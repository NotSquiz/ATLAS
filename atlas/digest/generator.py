"""
ATLAS Digest Generator

Transforms ATLAS from reactive to proactive by generating:
- Daily Digest: Top priorities, stuck items, small wins (150 words)
- Weekly Review: Week summary, open loops, suggested focus (250 words)

Based on "2nd Brain" principles: AI running a loop, not just AI as search.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from atlas.memory.store import get_store, MemoryStore

logger = logging.getLogger(__name__)


@dataclass
class HealthSnapshot:
    """Current health state summary."""
    energy_level: Optional[int] = None
    mood: Optional[int] = None
    stress_level: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight_kg: Optional[float] = None
    active_injuries: list[dict] = field(default_factory=list)
    recent_workouts: list[dict] = field(default_factory=list)
    supplements_today: list[str] = field(default_factory=list)


@dataclass
class MemorySnapshot:
    """Recent memories summary."""
    high_importance: list[dict] = field(default_factory=list)
    recent_events: list[dict] = field(default_factory=list)
    preferences: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)


@dataclass
class DailyDigest:
    """Daily digest structure (~150 words target)."""
    date: date
    greeting: str
    top_priorities: list[str]
    stuck_on: Optional[str]
    small_win: Optional[str]
    health_note: Optional[str]
    word_count: int = 0

    def to_text(self) -> str:
        """Render digest as plain text."""
        lines = [
            self.greeting,
            "",
            "**Today's Priorities:**",
        ]
        for i, priority in enumerate(self.top_priorities[:3], 1):
            lines.append(f"{i}. {priority}")

        if self.stuck_on:
            lines.extend(["", f"**Might be stuck on:** {self.stuck_on}"])

        if self.small_win:
            lines.extend(["", f"**Small win to notice:** {self.small_win}"])

        if self.health_note:
            lines.extend(["", f"**Health:** {self.health_note}"])

        text = "\n".join(lines)
        self.word_count = len(text.split())
        return text

    def to_voice(self) -> str:
        """Render digest for voice output (no markdown)."""
        lines = [self.greeting, ""]

        if self.top_priorities:
            lines.append("Your top priorities today:")
            for i, priority in enumerate(self.top_priorities[:3], 1):
                lines.append(f"  {i}. {priority}")

        if self.stuck_on:
            lines.append(f"\nYou might be stuck on: {self.stuck_on}")

        if self.small_win:
            lines.append(f"\nSmall win to notice: {self.small_win}")

        if self.health_note:
            lines.append(f"\n{self.health_note}")

        return "\n".join(lines)


@dataclass
class WeeklyReview:
    """Weekly review structure (~250 words target)."""
    week_ending: date
    summary: str
    completed_items: list[str]
    open_loops: list[str]
    suggested_focus: list[str]
    recurring_theme: Optional[str]
    health_summary: Optional[str]
    word_count: int = 0

    def to_text(self) -> str:
        """Render review as plain text."""
        lines = [
            f"## Weekly Review - Week ending {self.week_ending}",
            "",
            self.summary,
            "",
        ]

        if self.completed_items:
            lines.append("**Completed:**")
            for item in self.completed_items[:5]:
                lines.append(f"- {item}")
            lines.append("")

        if self.open_loops:
            lines.append("**Open Loops:**")
            for loop in self.open_loops[:5]:
                lines.append(f"- {loop}")
            lines.append("")

        if self.suggested_focus:
            lines.append("**Suggested Focus for Next Week:**")
            for i, focus in enumerate(self.suggested_focus[:3], 1):
                lines.append(f"{i}. {focus}")
            lines.append("")

        if self.recurring_theme:
            lines.append(f"**Recurring Theme:** {self.recurring_theme}")
            lines.append("")

        if self.health_summary:
            lines.append(f"**Health Summary:** {self.health_summary}")

        text = "\n".join(lines)
        self.word_count = len(text.split())
        return text


class DigestGenerator:
    """
    Generates daily and weekly digests from ATLAS data.

    Usage:
        generator = DigestGenerator()

        # Daily digest
        daily = generator.generate_daily()
        print(daily.to_text())

        # Weekly review
        weekly = generator.generate_weekly()
        print(weekly.to_text())

        # Voice output
        print(daily.to_voice())
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize with optional database path."""
        self.store = get_store(db_path)
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure database is initialized."""
        self.store.init_db()

    def _get_health_snapshot(self, days: int = 1) -> HealthSnapshot:
        """Get health data for the specified period."""
        conn = self.store.conn
        snapshot = HealthSnapshot()

        # Get latest daily metrics
        cursor = conn.execute(
            """
            SELECT energy_level, mood, stress_level, sleep_hours, weight_kg, notes
            FROM daily_metrics
            WHERE date >= date('now', ?)
            ORDER BY date DESC
            LIMIT 1
            """,
            (f"-{days} days",),
        )
        row = cursor.fetchone()
        if row:
            snapshot.energy_level = row["energy_level"]
            snapshot.mood = row["mood"]
            snapshot.stress_level = row["stress_level"]
            snapshot.sleep_hours = row["sleep_hours"]
            snapshot.weight_kg = row["weight_kg"]

        # Get active injuries
        cursor = conn.execute(
            """
            SELECT body_part, side, severity, status, description
            FROM injuries
            WHERE status IN ('active', 'recovering')
            ORDER BY severity DESC
            LIMIT 3
            """
        )
        snapshot.active_injuries = [dict(row) for row in cursor.fetchall()]

        # Get recent workouts
        cursor = conn.execute(
            """
            SELECT date, type, duration_minutes, notes
            FROM workouts
            WHERE date >= date('now', ?)
            ORDER BY date DESC
            LIMIT 5
            """,
            (f"-{days} days",),
        )
        snapshot.recent_workouts = [dict(row) for row in cursor.fetchall()]

        # Get today's supplements
        cursor = conn.execute(
            """
            SELECT s.name
            FROM supplement_log sl
            JOIN supplements s ON sl.supplement_id = s.id
            WHERE sl.date = date('now') AND sl.taken = 1
            """
        )
        snapshot.supplements_today = [row["name"] for row in cursor.fetchall()]

        return snapshot

    def _get_memory_snapshot(self, days: int = 1) -> MemorySnapshot:
        """Get recent memories for the specified period."""
        snapshot = MemorySnapshot()
        conn = self.store.conn

        # Get high importance memories
        cursor = conn.execute(
            """
            SELECT id, content, importance, memory_type, created_at
            FROM semantic_memory
            WHERE importance >= 0.7
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        snapshot.high_importance = [dict(row) for row in cursor.fetchall()]

        # Get recent events
        cursor = conn.execute(
            """
            SELECT id, content, created_at
            FROM semantic_memory
            WHERE memory_type = 'event'
            AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (f"-{days} days",),
        )
        snapshot.recent_events = [dict(row) for row in cursor.fetchall()]

        # Get preferences
        cursor = conn.execute(
            """
            SELECT id, content
            FROM semantic_memory
            WHERE memory_type = 'preference'
            ORDER BY access_count DESC, created_at DESC
            LIMIT 3
            """
        )
        snapshot.preferences = [dict(row) for row in cursor.fetchall()]

        # Get facts
        cursor = conn.execute(
            """
            SELECT id, content
            FROM semantic_memory
            WHERE memory_type = 'fact'
            ORDER BY importance DESC, created_at DESC
            LIMIT 5
            """
        )
        snapshot.facts = [dict(row) for row in cursor.fetchall()]

        return snapshot

    def _format_greeting(self) -> str:
        """Generate time-appropriate greeting."""
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning."
        elif hour < 17:
            return "Good afternoon."
        else:
            return "Good evening."

    def _format_health_note(self, health: HealthSnapshot) -> Optional[str]:
        """Format a brief health note."""
        notes = []

        if health.sleep_hours:
            if health.sleep_hours < 6:
                notes.append(f"Only {health.sleep_hours:.1f}h sleep - take it easy")
            elif health.sleep_hours >= 8:
                notes.append(f"{health.sleep_hours:.1f}h sleep - well rested")

        if health.energy_level:
            if health.energy_level <= 4:
                notes.append("energy is low")
            elif health.energy_level >= 8:
                notes.append("energy is high")

        if health.active_injuries:
            injury = health.active_injuries[0]
            side = f" ({injury['side']})" if injury.get("side") and injury["side"] != "n/a" else ""
            notes.append(f"{injury['body_part']}{side} still {injury['status']}")

        if notes:
            return ". ".join(notes).capitalize() + "."
        return None

    def generate_daily(self, target_date: Optional[date] = None) -> DailyDigest:
        """
        Generate a daily digest.

        Args:
            target_date: Date for digest (default: today)

        Returns:
            DailyDigest with priorities, stuck items, wins, health note
        """
        target_date = target_date or date.today()

        health = self._get_health_snapshot(days=1)
        memories = self._get_memory_snapshot(days=1)

        # Extract priorities from high-importance memories
        priorities = []
        for mem in memories.high_importance[:3]:
            content = mem["content"]
            # Truncate long content
            if len(content) > 100:
                content = content[:97] + "..."
            priorities.append(content)

        # If no high-importance memories, use recent events
        if not priorities and memories.recent_events:
            for event in memories.recent_events[:3]:
                content = event["content"]
                if len(content) > 100:
                    content = content[:97] + "..."
                priorities.append(content)

        # Default priority if nothing found
        if not priorities:
            priorities = ["Review your goals and set priorities for today"]

        # Identify potential stuck items (from events or preferences)
        stuck_on = None
        for mem in memories.recent_events:
            content = mem["content"].lower()
            if any(word in content for word in ["stuck", "blocked", "waiting", "pending"]):
                stuck_on = mem["content"][:100]
                break

        # Small win - recent workout or supplement consistency
        small_win = None
        if health.recent_workouts:
            workout = health.recent_workouts[0]
            small_win = f"Completed {workout['type']} workout ({workout['duration_minutes']}min)"
        elif health.supplements_today:
            small_win = f"Took {len(health.supplements_today)} supplements today"

        return DailyDigest(
            date=target_date,
            greeting=self._format_greeting(),
            top_priorities=priorities,
            stuck_on=stuck_on,
            small_win=small_win,
            health_note=self._format_health_note(health),
        )

    def generate_weekly(self, week_ending: Optional[date] = None) -> WeeklyReview:
        """
        Generate a weekly review.

        Args:
            week_ending: End date for the week (default: today)

        Returns:
            WeeklyReview with summary, open loops, suggested focus
        """
        week_ending = week_ending or date.today()
        week_start = week_ending - timedelta(days=7)

        health = self._get_health_snapshot(days=7)
        memories = self._get_memory_snapshot(days=7)

        # Summary
        workout_count = len(health.recent_workouts)
        summary = f"This week you logged {workout_count} workouts"

        if memories.recent_events:
            summary += f" and captured {len(memories.recent_events)} events"
        summary += "."

        # Completed items (events marked as done or past)
        completed = []
        for event in memories.recent_events:
            content = event["content"]
            if any(word in content.lower() for word in ["completed", "done", "finished"]):
                completed.append(content[:80])

        # Open loops (high importance items still pending)
        open_loops = []
        for mem in memories.high_importance:
            content = mem["content"]
            if not any(word in content.lower() for word in ["completed", "done", "finished"]):
                open_loops.append(content[:80])

        # Suggested focus
        suggested_focus = []
        if health.active_injuries:
            injury = health.active_injuries[0]
            suggested_focus.append(f"Continue rehab for {injury['body_part']}")

        if open_loops:
            suggested_focus.append(f"Close loop: {open_loops[0][:50]}")

        if workout_count < 3:
            suggested_focus.append("Increase workout frequency")

        if not suggested_focus:
            suggested_focus = ["Review and update your goals", "Clear any mental clutter"]

        # Recurring theme (look for patterns in memory content)
        recurring_theme = None
        word_freq: dict[str, int] = {}
        for mem in memories.high_importance + memories.recent_events:
            words = mem["content"].lower().split()
            for word in words:
                if len(word) > 5:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1

        if word_freq:
            top_word = max(word_freq.items(), key=lambda x: x[1])
            if top_word[1] >= 3:
                recurring_theme = f"'{top_word[0]}' appears frequently in your notes"

        # Health summary
        health_summary = None
        if workout_count > 0:
            workout_types = [w["type"] for w in health.recent_workouts if w.get("type")]
            if workout_types:
                health_summary = f"{workout_count} workouts ({', '.join(set(workout_types))})"

        return WeeklyReview(
            week_ending=week_ending,
            summary=summary,
            completed_items=completed[:5],
            open_loops=open_loops[:5],
            suggested_focus=suggested_focus[:3],
            recurring_theme=recurring_theme,
            health_summary=health_summary,
        )


# CLI interface
def main():
    """CLI for digest generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate ATLAS digests")
    parser.add_argument(
        "--type",
        choices=["daily", "weekly"],
        default="daily",
        help="Type of digest to generate",
    )
    parser.add_argument(
        "--format",
        choices=["text", "voice"],
        default="text",
        help="Output format",
    )
    args = parser.parse_args()

    generator = DigestGenerator()

    if args.type == "daily":
        digest = generator.generate_daily()
        if args.format == "voice":
            print(digest.to_voice())
        else:
            print(digest.to_text())
    else:
        review = generator.generate_weekly()
        print(review.to_text())


if __name__ == "__main__":
    main()
