"""
ATLAS Workout Scheduler

Handles intelligent workout scheduling with:
- Phase start date tracking
- Completed workout tracking
- Missed day handling (sequential or calendar mode)
- Program day calculation (Day 1, Day 2, etc.)

Usage:
    from atlas.health.scheduler import WorkoutScheduler

    scheduler = WorkoutScheduler()
    next_workout = scheduler.get_next_workout()
    # Returns: ScheduledWorkout with protocol, program_day, catch_up info
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ScheduleMode(Enum):
    """How to handle missed workouts."""
    SEQUENTIAL = "sequential"  # Missed Monday = do Strength A on Tuesday
    CALENDAR = "calendar"      # Keep to calendar days, offer catch-up
    HYBRID = "hybrid"          # Allow 1 day shift, then offer choice


@dataclass
class ScheduledWorkout:
    """Today's workout recommendation."""
    protocol_id: str           # 'strength_a', 'zone2_cardio', etc.
    protocol_name: str         # Human readable
    program_day: int           # Day 1, Day 2, etc. in the program
    program_week: int          # Week 1, Week 2, etc.
    is_catch_up: bool = False  # This is making up for a missed day
    missed_workout: Optional[str] = None  # What was missed (if catch-up)
    days_behind: int = 0       # How many workouts behind schedule
    scheduled_day: str = ""    # Original scheduled day (Monday, Tuesday, etc.)
    notes: str = ""


@dataclass
class WorkoutCompletion:
    """Record of a completed workout."""
    id: int
    date: date
    protocol_id: str
    protocol_name: str
    program_day: int
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class WorkoutScheduler:
    """
    Intelligent workout scheduling with missed day handling.

    Tracks:
    - Phase start date (Day 1 of program)
    - Completed workouts per day
    - Expected vs actual progress
    """

    PHASE_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "workouts" / "phase1.json"

    def __init__(self, db_path: Optional[Path] = None, mode: ScheduleMode = ScheduleMode.SEQUENTIAL):
        self.db_path = db_path or Path.home() / ".atlas" / "atlas.db"
        self.mode = mode
        self._config: Optional[dict] = None
        self._ensure_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                -- Track completed workout sessions
                CREATE TABLE IF NOT EXISTS workout_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    protocol_id TEXT NOT NULL,
                    protocol_name TEXT,
                    program_day INTEGER,         -- Day 1, Day 2, etc.
                    program_week INTEGER,        -- Week 1, Week 2, etc.
                    phase TEXT DEFAULT 'phase_1',
                    duration_minutes INTEGER,
                    traffic_light TEXT,          -- GREEN/YELLOW/RED
                    garmin_activity_id TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, protocol_id)
                );

                CREATE INDEX IF NOT EXISTS idx_workout_sessions_date
                    ON workout_sessions(date DESC);
                CREATE INDEX IF NOT EXISTS idx_workout_sessions_protocol
                    ON workout_sessions(protocol_id);
                CREATE INDEX IF NOT EXISTS idx_workout_sessions_day
                    ON workout_sessions(program_day);
            """)
            conn.commit()
        finally:
            conn.close()

    @property
    def config(self) -> dict:
        """Load and cache phase config."""
        if self._config is None:
            if self.PHASE_CONFIG_PATH.exists():
                with open(self.PHASE_CONFIG_PATH) as f:
                    self._config = json.load(f)
            else:
                self._config = {}
        return self._config

    def get_phase_start_date(self) -> Optional[date]:
        """Get the start date of the current phase."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT start_date FROM phase_history
                WHERE status = 'active'
                ORDER BY start_date DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return date.fromisoformat(row["start_date"])
            return None
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()

    def start_phase(self, phase_name: str = "phase_1", start_date: Optional[date] = None) -> date:
        """
        Start a new phase (or restart current phase).

        Args:
            phase_name: Phase identifier
            start_date: When to start (defaults to today)

        Returns:
            The start date
        """
        start = start_date or date.today()
        conn = self._get_conn()
        try:
            # Ensure phase_history table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS phase_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phase_id INTEGER,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    status TEXT DEFAULT 'active',
                    exit_reason TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Deactivate any existing active phases
            conn.execute("""
                UPDATE phase_history
                SET status = 'completed', end_date = ?
                WHERE status = 'active'
            """, (start.isoformat(),))

            # Start new phase
            conn.execute("""
                INSERT INTO phase_history (start_date, status, notes)
                VALUES (?, 'active', ?)
            """, (start.isoformat(), f"Started {phase_name}"))

            conn.commit()
            logger.info(f"Started {phase_name} on {start}")
            return start
        finally:
            conn.close()

    def get_program_day(self, for_date: Optional[date] = None) -> int:
        """
        Calculate program day number.

        Day 1 = phase start date
        Counts actual calendar days (not workout days)
        """
        check_date = for_date or date.today()
        phase_start = self.get_phase_start_date()

        if not phase_start:
            return 1  # No phase started, assume Day 1

        return (check_date - phase_start).days + 1

    def get_program_week(self, for_date: Optional[date] = None) -> int:
        """Calculate program week number (1-indexed)."""
        program_day = self.get_program_day(for_date)
        return ((program_day - 1) // 7) + 1

    def get_completed_workouts(self, since_date: Optional[date] = None) -> list[WorkoutCompletion]:
        """Get list of completed workouts since a date."""
        conn = self._get_conn()
        try:
            if since_date:
                cursor = conn.execute("""
                    SELECT id, date, protocol_id, protocol_name, program_day,
                           duration_minutes, notes
                    FROM workout_sessions
                    WHERE date >= ?
                    ORDER BY date ASC
                """, (since_date.isoformat(),))
            else:
                cursor = conn.execute("""
                    SELECT id, date, protocol_id, protocol_name, program_day,
                           duration_minutes, notes
                    FROM workout_sessions
                    ORDER BY date ASC
                """)

            return [
                WorkoutCompletion(
                    id=row["id"],
                    date=date.fromisoformat(row["date"]),
                    protocol_id=row["protocol_id"],
                    protocol_name=row["protocol_name"],
                    program_day=row["program_day"] or 0,
                    duration_minutes=row["duration_minutes"],
                    notes=row["notes"],
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def get_last_workout(self) -> Optional[WorkoutCompletion]:
        """Get the most recently completed workout."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT id, date, protocol_id, protocol_name, program_day,
                       duration_minutes, notes
                FROM workout_sessions
                ORDER BY date DESC, id DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return WorkoutCompletion(
                    id=row["id"],
                    date=date.fromisoformat(row["date"]),
                    protocol_id=row["protocol_id"],
                    protocol_name=row["protocol_name"],
                    program_day=row["program_day"] or 0,
                    duration_minutes=row["duration_minutes"],
                    notes=row["notes"],
                )
            return None
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()

    def _get_schedule(self) -> dict[int, str]:
        """Get day-of-week to protocol mapping from config."""
        return self.config.get("schedule", {})

    def _get_protocol_name(self, protocol_id: str) -> str:
        """Get human-readable name for a protocol."""
        names = {
            "strength_a": "Strength A (Full Body)",
            "strength_b": "Strength B (Push Focus)",
            "strength_c": "Strength C (Pull Focus)",
            "zone2_cardio": "Zone 2 Cardio",
            "zone2_extended": "Zone 2 Extended",
            "active_mobility": "Active Mobility",
            "recovery": "Recovery Day",
            "red_day": "Recovery (Red Day)",
        }
        return names.get(protocol_id, protocol_id.replace("_", " ").title())

    def _get_expected_workouts(self, since_date: date, until_date: date) -> list[tuple[date, str]]:
        """Get list of expected workouts between dates based on schedule."""
        schedule = self._get_schedule()
        expected = []

        current = since_date
        while current <= until_date:
            dow = str(current.weekday())  # 0=Monday
            if dow in schedule:
                protocol = schedule[dow]
                if protocol != "recovery":  # Don't count rest days
                    expected.append((current, protocol))
            current += timedelta(days=1)

        return expected

    def get_next_workout(self) -> ScheduledWorkout:
        """
        Determine what workout to do today.

        In SEQUENTIAL mode:
        - Returns the next workout in sequence (regardless of calendar day)
        - If behind schedule, marks as catch-up

        In CALENDAR mode:
        - Returns today's scheduled workout
        - If yesterday was missed, offers catch-up option
        """
        today = date.today()
        schedule = self._get_schedule()
        phase_start = self.get_phase_start_date()

        # If no phase started, return special status (don't auto-start)
        if not phase_start:
            dow = str(today.weekday())
            protocol_id = schedule.get(dow, "recovery")
            return ScheduledWorkout(
                protocol_id="no_phase",
                protocol_name=self._get_protocol_name(protocol_id),
                program_day=0,
                program_week=0,
                notes="No program started. Say 'start program' to begin Phase 1.",
            )

        program_day = self.get_program_day(today)
        program_week = self.get_program_week(today)

        # Get completed workouts since phase start
        completed = self.get_completed_workouts(phase_start)
        completed_dates = {c.date for c in completed}
        completed_protocols = {c.protocol_id for c in completed}

        # Get expected workouts up to today
        expected = self._get_expected_workouts(phase_start, today)

        if self.mode == ScheduleMode.SEQUENTIAL:
            # In SEQUENTIAL mode, allow multiple workouts per day for catch-up
            # The sequential logic will return "already_done" only when fully caught up
            result = self._get_sequential_workout(
                expected, completed, program_day, program_week, today, schedule
            )
            # If sequential says we're on today's scheduled workout and we already did it
            if not result.is_catch_up and today in completed_dates:
                today_workouts = [c for c in completed if c.date == today]
                # Check if today's scheduled workout was completed
                if any(c.protocol_id == result.protocol_id for c in today_workouts):
                    today_workout = next(c for c in today_workouts if c.protocol_id == result.protocol_id)
                    return ScheduledWorkout(
                        protocol_id="already_done",
                        protocol_name=f"Already completed: {today_workout.protocol_name}",
                        program_day=program_day,
                        program_week=program_week,
                        notes="You've already completed today's workout."
                    )
            return result
        else:
            # In CALENDAR mode, check if we already worked out today
            if today in completed_dates:
                today_workout = next((c for c in completed if c.date == today), None)
                return ScheduledWorkout(
                    protocol_id="already_done",
                    protocol_name=f"Already completed: {today_workout.protocol_name if today_workout else 'workout'}",
                    program_day=program_day,
                    program_week=program_week,
                    notes="You've already completed today's workout."
                )
            return self._get_calendar_workout(
                expected, completed, program_day, program_week, today, schedule
            )

    def _get_sequential_workout(
        self,
        expected: list[tuple[date, str]],
        completed: list[WorkoutCompletion],
        program_day: int,
        program_week: int,
        today: date,
        schedule: dict[int, str],
    ) -> ScheduledWorkout:
        """Sequential mode: always do the next workout in order.

        Counts completed protocols (not exact date matches) to handle catch-up
        workouts logged on different dates than originally scheduled.
        """
        from collections import Counter

        # Count how many of each protocol have been completed
        completed_counts = Counter(c.protocol_id for c in completed)

        # Track how many of each protocol we've seen in expected list
        expected_counts: dict[str, int] = {}

        for expected_date, protocol_id in expected:
            # Count expected instances of this protocol
            expected_counts[protocol_id] = expected_counts.get(protocol_id, 0) + 1

            # Check if we've completed enough of this protocol
            if completed_counts.get(protocol_id, 0) < expected_counts[protocol_id]:
                # This is the next workout to do
                is_catch_up = expected_date < today
                days_behind = (today - expected_date).days if is_catch_up else 0

                day_name = expected_date.strftime("%A")

                return ScheduledWorkout(
                    protocol_id=protocol_id,
                    protocol_name=self._get_protocol_name(protocol_id),
                    program_day=program_day,
                    program_week=program_week,
                    is_catch_up=is_catch_up,
                    missed_workout=f"{day_name}'s workout" if is_catch_up else None,
                    days_behind=days_behind,
                    scheduled_day=day_name,
                    notes=f"Catching up from {day_name}" if is_catch_up else "",
                )

        # All caught up - return today's scheduled workout
        dow = str(today.weekday())
        protocol_id = schedule.get(dow, "recovery")

        return ScheduledWorkout(
            protocol_id=protocol_id,
            protocol_name=self._get_protocol_name(protocol_id),
            program_day=program_day,
            program_week=program_week,
            scheduled_day=today.strftime("%A"),
            notes="On schedule" if protocol_id != "recovery" else "Rest day",
        )

    def _get_calendar_workout(
        self,
        expected: list[tuple[date, str]],
        completed: list[WorkoutCompletion],
        program_day: int,
        program_week: int,
        today: date,
        schedule: dict[int, str],
    ) -> ScheduledWorkout:
        """Calendar mode: stick to calendar, note missed days."""

        # Check what was missed
        completed_set = {(c.date, c.protocol_id) for c in completed}
        missed = []

        for expected_date, protocol_id in expected:
            if expected_date < today and (expected_date, protocol_id) not in completed_set:
                missed.append((expected_date, protocol_id))

        # Today's scheduled workout
        dow = str(today.weekday())
        protocol_id = schedule.get(dow, "recovery")

        return ScheduledWorkout(
            protocol_id=protocol_id,
            protocol_name=self._get_protocol_name(protocol_id),
            program_day=program_day,
            program_week=program_week,
            days_behind=len(missed),
            scheduled_day=today.strftime("%A"),
            notes=f"Missed {len(missed)} workout(s)" if missed else "",
        )

    def log_workout(
        self,
        protocol_id: str,
        duration_minutes: Optional[int] = None,
        traffic_light: Optional[str] = None,
        garmin_activity_id: Optional[str] = None,
        notes: Optional[str] = None,
        workout_date: Optional[date] = None,
    ) -> int:
        """
        Log a completed workout.

        Returns the session ID.
        """
        workout_date = workout_date or date.today()
        program_day = self.get_program_day(workout_date)
        program_week = self.get_program_week(workout_date)

        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO workout_sessions
                (date, protocol_id, protocol_name, program_day, program_week,
                 duration_minutes, traffic_light, garmin_activity_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workout_date.isoformat(),
                protocol_id,
                self._get_protocol_name(protocol_id),
                program_day,
                program_week,
                duration_minutes,
                traffic_light,
                garmin_activity_id,
                notes,
            ))
            conn.commit()
            logger.info(f"Logged workout: {protocol_id} on day {program_day}")
            session_id = cursor.lastrowid

            # Award XP (non-blocking, fail-safe)
            self._award_workout_xp(protocol_id)

            return session_id
        finally:
            conn.close()

    def _award_workout_xp(self, protocol_id: str) -> None:
        """Award XP for workout completion (non-blocking)."""
        try:
            from atlas.gamification.xp_service import award_xp_safe_async, XP_TABLE

            # Determine skill and XP based on workout type
            if protocol_id in ("strength_a", "strength_b", "strength_c"):
                skill = "strength"
                xp = XP_TABLE.get("workout_strength", 150)
            elif protocol_id in ("zone2_cardio", "zone2_extended"):
                skill = "endurance"
                xp = XP_TABLE.get("workout_cardio", 120)
            elif protocol_id == "active_mobility":
                skill = "mobility"
                xp = XP_TABLE.get("mobility_exercise", 20)
            else:
                # Unknown workout type - skip XP
                return

            award_xp_safe_async(skill, xp, f"workout_{protocol_id}")
        except Exception as e:
            # XP failure should never break workout logging
            logger.debug(f"XP award skipped: {e}")

    def get_status(self) -> dict:
        """Get overall schedule status for voice/display."""
        today = date.today()
        phase_start = self.get_phase_start_date()

        if not phase_start:
            return {
                "phase_started": False,
                "message": "Phase not started. Say 'start phase' to begin.",
            }

        program_day = self.get_program_day(today)
        program_week = self.get_program_week(today)

        # Count completed workouts
        completed = self.get_completed_workouts(phase_start)

        # Get expected workouts (excluding rest days)
        expected = self._get_expected_workouts(phase_start, today)
        expected_count = len([e for e in expected if e[1] != "recovery"])
        completed_count = len(completed)

        # Calculate status
        on_track = completed_count >= expected_count - 1  # Allow 1 day buffer

        next_workout = self.get_next_workout()

        return {
            "phase_started": True,
            "phase_start_date": phase_start.isoformat(),
            "program_day": program_day,
            "program_week": program_week,
            "workouts_completed": completed_count,
            "workouts_expected": expected_count,
            "days_behind": max(0, expected_count - completed_count),
            "on_track": on_track,
            "next_workout": next_workout.protocol_name,
            "next_workout_id": next_workout.protocol_id,
            "is_catch_up": next_workout.is_catch_up,
        }

    def format_status_voice(self) -> str:
        """Format status for voice output."""
        status = self.get_status()

        if not status["phase_started"]:
            return status["message"]

        parts = [f"Week {status['program_week']}, Day {status['program_day']}."]

        if status["on_track"]:
            parts.append(f"On track. {status['workouts_completed']} workouts completed.")
        else:
            behind = status["days_behind"]
            parts.append(f"{behind} workout{'s' if behind != 1 else ''} behind.")

        if status["is_catch_up"]:
            parts.append(f"Next: catch-up {status['next_workout']}.")
        elif status["next_workout_id"] != "recovery":
            parts.append(f"Today: {status['next_workout']}.")
        else:
            parts.append("Rest day.")

        return " ".join(parts)


# Convenience function
def get_scheduler() -> WorkoutScheduler:
    """Get a WorkoutScheduler instance."""
    return WorkoutScheduler()
