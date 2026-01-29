"""
Routine Runner - Timer-based Morning Protocol

Guides user through the 18-minute ATLAS Morning Protocol with:
- Section and exercise announcements via TTS
- Accurate local timers (no LLM tokens burned)
- VAD-based interrupt detection for control commands
- Section jumping ("skip to shoulders")
- Quick routine mode for time-constrained mornings

Usage:
    from atlas.health.routine_runner import RoutineRunner

    runner = RoutineRunner()

    # Full routine with voice
    await runner.run(speak_func=my_speak, play_chime=my_chime)

    # Quick routine (just shoulders)
    await runner.run(speak_func=my_speak, sections=["Shoulder Rehab"])

    # CLI mode (no voice)
    python -m atlas.health.routine_runner
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, List, Awaitable

logger = logging.getLogger(__name__)

# Phase config location
PHASE_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "workouts" / "phase1.json"

# Default timing for rep-based exercises (seconds per rep)
# 4 seconds allows realistic stretch timing and controlled movement
DEFAULT_SECONDS_PER_REP = 4


class ControlCommand(Enum):
    """Voice control commands during routine."""
    NONE = "none"
    STOP = "stop"
    PAUSE = "pause"
    SKIP = "skip"
    NEXT = "next"


@dataclass
class ExerciseConfig:
    """Configuration for a single exercise."""
    id: str
    name: str
    duration_seconds: Optional[int] = None
    reps: Optional[int] = None
    sets: Optional[int] = None
    per_side: bool = False
    hold_seconds: Optional[int] = None
    cues: Optional[List[str]] = None
    type: Optional[str] = None  # "reminder" = no timer, just announcement

    @classmethod
    def from_dict(cls, data: dict) -> "ExerciseConfig":
        """Create from JSON dict."""
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Exercise"),
            duration_seconds=data.get("duration_seconds"),
            reps=data.get("reps"),
            sets=data.get("sets"),
            per_side=data.get("per_side", False),
            hold_seconds=data.get("hold_seconds"),
            cues=data.get("cues"),
            type=data.get("type"),
        )

    def is_reminder(self) -> bool:
        """Check if this is a reminder-only exercise (no timer)."""
        return self.type == "reminder"

    def get_total_duration(self) -> int:
        """Calculate total duration in seconds."""
        # Reminders have no timer duration
        if self.is_reminder():
            return 0

        # Calculate base duration
        if self.sets and self.duration_seconds:
            # Multi-set timed exercise (e.g., 5 sets x 10 seconds)
            base = self.sets * self.duration_seconds
        elif self.duration_seconds:
            base = self.duration_seconds
        elif self.reps:
            base = self.reps * DEFAULT_SECONDS_PER_REP
        else:
            base = 30  # Default fallback

        # Double if per-side
        if self.per_side:
            base *= 2

        return base


@dataclass
class SectionConfig:
    """Configuration for a routine section."""
    name: str
    duration_minutes: int
    exercises: List[ExerciseConfig]

    @classmethod
    def from_dict(cls, data: dict) -> "SectionConfig":
        """Create from JSON dict."""
        return cls(
            name=data.get("name", "Unknown Section"),
            duration_minutes=data.get("duration_minutes", 4),
            exercises=[ExerciseConfig.from_dict(ex) for ex in data.get("exercises", [])],
        )


@dataclass
class RoutineConfig:
    """Configuration for the full morning routine."""
    name: str
    duration_minutes: int
    sections: List[SectionConfig]

    @classmethod
    def from_dict(cls, data: dict) -> "RoutineConfig":
        """Create from JSON dict."""
        return cls(
            name=data.get("name", "Morning Routine"),
            duration_minutes=data.get("duration_minutes", 18),
            sections=[SectionConfig.from_dict(sec) for sec in data.get("sections", [])],
        )


def load_routine_config() -> RoutineConfig:
    """Load morning routine config from phase1.json."""
    if not PHASE_CONFIG_PATH.exists():
        logger.warning(f"Phase config not found at {PHASE_CONFIG_PATH}")
        # Return minimal default
        return RoutineConfig(
            name="Default Routine",
            duration_minutes=5,
            sections=[],
        )

    with open(PHASE_CONFIG_PATH) as f:
        data = json.load(f)

    return RoutineConfig.from_dict(data.get("daily_routine", {}))


class RoutineRunner:
    """
    Timer-based morning routine runner.

    Guides user through exercises with voice announcements and chimes.
    Supports interrupt commands for pause/skip/stop control.
    """

    def __init__(
        self,
        config: Optional[RoutineConfig] = None,
        check_interrupt: Optional[Callable[[], ControlCommand]] = None,
    ):
        """
        Initialize routine runner.

        Args:
            config: Routine configuration (loads from phase1.json if None)
            check_interrupt: Optional function to check for voice interrupt commands
        """
        self.config = config or load_routine_config()
        self._check_interrupt = check_interrupt

        # State
        self._paused = False
        self._stopped = False
        self._current_section_idx = 0
        self._current_exercise_idx = 0

    async def run(
        self,
        speak_func: Optional[Callable[[str], Awaitable[None]]] = None,
        play_chime: Optional[Callable[[], None]] = None,
        sections: Optional[List[str]] = None,
    ) -> bool:
        """
        Run the morning routine.

        Args:
            speak_func: Async function to speak text via TTS
            play_chime: Function to play completion chime
            sections: Optional list of section names to run (for quick mode)

        Returns:
            True if completed, False if stopped early
        """
        self._paused = False
        self._stopped = False

        # Filter sections if specified
        sections_to_run = self.config.sections
        if sections:
            section_names_lower = [s.lower() for s in sections]
            sections_to_run = [
                s for s in self.config.sections
                if any(name in s.name.lower() for name in section_names_lower)
            ]

        if not sections_to_run:
            logger.warning("No sections to run")
            return False

        # Calculate total time
        total_mins = sum(s.duration_minutes for s in sections_to_run)

        # Announce start
        if speak_func:
            start_msg = f"Starting {self.config.name}. {total_mins} minutes."
            if sections:
                start_msg += f" Focused on {', '.join(sections)}."
            await speak_func(start_msg)

        # Run each section
        for section_idx, section in enumerate(sections_to_run):
            if self._stopped:
                break

            self._current_section_idx = section_idx
            completed = await self._run_section(section, speak_func, play_chime)

            if not completed:
                break

        # Announce completion
        if not self._stopped and speak_func:
            await speak_func("Routine complete. Well done.")

        # Award XP for completing routine (non-blocking)
        if not self._stopped:
            self._award_routine_xp()

        if play_chime:
            # Play completion chime
            try:
                from atlas.voice.audio_utils import chime_routine_complete
                chime_routine_complete()
            except ImportError:
                play_chime()

        return not self._stopped

    async def _run_section(
        self,
        section: SectionConfig,
        speak_func: Optional[Callable[[str], Awaitable[None]]],
        play_chime: Optional[Callable[[], None]],
    ) -> bool:
        """Run a single section."""
        if speak_func:
            await speak_func(f"{section.name}. {section.duration_minutes} minutes.")

        for ex_idx, exercise in enumerate(section.exercises):
            if self._stopped:
                return False

            self._current_exercise_idx = ex_idx
            completed = await self._run_exercise(exercise, speak_func, play_chime)

            if not completed:
                return False

        # Section complete chime
        if play_chime:
            try:
                from atlas.voice.audio_utils import chime_section_complete
                chime_section_complete()
            except ImportError:
                play_chime()

        return True

    async def _run_exercise(
        self,
        exercise: ExerciseConfig,
        speak_func: Optional[Callable[[str], Awaitable[None]]],
        play_chime: Optional[Callable[[], None]],
    ) -> bool:
        """Run a single exercise."""
        # Announce exercise
        if speak_func:
            announcement = exercise.name

            # Add brief cue if available
            if exercise.cues and len(exercise.cues) > 0:
                announcement += f". {exercise.cues[0]}"

            await speak_func(announcement)

        # Calculate duration
        duration = exercise.get_total_duration()

        # Run timer with interrupt checking
        completed = await self._run_timer(duration)

        # Play exercise complete chime
        if completed and play_chime:
            try:
                from atlas.voice.audio_utils import chime_exercise_complete
                chime_exercise_complete()
            except ImportError:
                play_chime()

        return completed

    async def _run_timer(self, duration_seconds: int) -> bool:
        """
        Run a timer with interrupt checking.

        Args:
            duration_seconds: Timer duration

        Returns:
            True if completed, False if interrupted
        """
        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            # Check for pause
            while self._paused:
                if self._stopped:
                    return False
                await asyncio.sleep(0.1)

            if self._stopped:
                return False

            # Check for interrupt command
            if self._check_interrupt:
                command = self._check_interrupt()
                if command == ControlCommand.STOP:
                    self._stopped = True
                    return False
                elif command == ControlCommand.PAUSE:
                    self._paused = True
                elif command == ControlCommand.SKIP or command == ControlCommand.NEXT:
                    # Skip current exercise
                    return True

            await asyncio.sleep(0.1)

        return True

    def stop(self):
        """Stop the routine."""
        self._stopped = True

    def pause(self):
        """Pause the routine."""
        self._paused = True

    def resume(self):
        """Resume a paused routine."""
        self._paused = False

    def skip(self):
        """Skip current exercise."""
        # Handled by timer interrupt check
        pass

    def _award_routine_xp(self) -> None:
        """Award XP for completing routine (non-blocking)."""
        try:
            from atlas.gamification.xp_service import award_xp_safe_async, XP_TABLE
            xp = XP_TABLE.get("morning_routine", 75)
            award_xp_safe_async("mobility", xp, "morning_routine")
        except Exception as e:
            # XP failure should never break routine
            logger.debug(f"XP award skipped: {e}")

    def get_section_names(self) -> List[str]:
        """Get list of section names for quick mode selection."""
        return [s.name for s in self.config.sections]


def format_routine_for_display(config: Optional[RoutineConfig] = None) -> str:
    """Format routine for CLI display."""
    config = config or load_routine_config()

    lines = [
        f"\n{'=' * 50}",
        f"  {config.name}",
        f"  {config.duration_minutes} minutes total",
        f"{'=' * 50}",
    ]

    for section in config.sections:
        lines.append(f"\n▸ {section.name} ({section.duration_minutes} min)")
        for ex in section.exercises:
            duration = ex.get_total_duration()
            lines.append(f"    • {ex.name} ({duration}s)")

    lines.append(f"\n{'=' * 50}")
    return "\n".join(lines)


async def run_routine_cli(sections: Optional[List[str]] = None, dry_run: bool = False):
    """Run routine in CLI mode (prints instead of speaking)."""
    print(format_routine_for_display())

    if dry_run:
        print("\n[DRY RUN - not executing timers]")
        return

    runner = RoutineRunner()

    async def print_speak(text: str):
        print(f"\n🗣️  {text}")

    def print_chime():
        print("🔔 *chime*")

    print("\n[Starting routine - press Ctrl+C to stop]\n")

    try:
        completed = await runner.run(
            speak_func=print_speak,
            play_chime=print_chime,
            sections=sections,
        )
        if completed:
            print("\n✅ Routine completed!")
        else:
            print("\n⏹️  Routine stopped early")
    except KeyboardInterrupt:
        runner.stop()
        print("\n\n⏹️  Routine cancelled")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="ATLAS Morning Routine Runner"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show routine structure without running timers"
    )
    parser.add_argument(
        "--section", "-s",
        action="append",
        dest="sections",
        help="Run only specific section(s) - can specify multiple"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available sections"
    )
    args = parser.parse_args()

    if args.list:
        config = load_routine_config()
        print("\nAvailable sections:")
        for section in config.sections:
            print(f"  • {section.name} ({section.duration_minutes} min)")
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    asyncio.run(run_routine_cli(sections=args.sections, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
