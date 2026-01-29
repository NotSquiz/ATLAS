"""
Workout Runner - Timer-based Workout Execution

Guides user through workout protocols with:
- Exercise announcements with form cues
- Lifting cadence guidance (tempo)
- Rest timers between sets
- Equipment change pauses
- Set/rep tracking

Usage:
    from atlas.health.workout_runner import WorkoutRunner

    runner = WorkoutRunner()

    # Run today's workout
    await runner.run_todays_workout(speak_func=my_speak, play_chime=my_chime)

    # Run specific protocol
    await runner.run_protocol("strength_b", speak_func=my_speak)

    # CLI mode
    python -m atlas.health.workout_runner
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, List, Awaitable, Dict, Any

from atlas.health.router import TrafficLightStatus

logger = logging.getLogger(__name__)

# Phase config location
PHASE_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "workouts" / "phase1.json"

# Default timing
DEFAULT_SET_DURATION_SECONDS = 45  # Time for one set
DEFAULT_REST_SECONDS = 90  # Rest between sets
DEFAULT_EQUIPMENT_CHANGE_SECONDS = 30


class ControlCommand(Enum):
    """Voice control commands during workout."""
    NONE = "none"
    STOP = "stop"
    PAUSE = "pause"
    SKIP = "skip"
    NEXT = "next"


@dataclass
class WorkoutExercise:
    """Configuration for a workout exercise."""
    id: str
    name: str
    sets: int = 3
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None
    duration_minutes: Optional[int] = None
    distance_meters: Optional[int] = None
    rest_seconds: int = DEFAULT_REST_SECONDS
    notes: Optional[str] = None
    tempo: Optional[str] = None  # e.g., "3-1-2" (3s down, 1s pause, 2s up)
    work_seconds: Optional[int] = None  # For interval training
    equipment_change: bool = False
    # New fields for Phase 1 exercise support
    per_side: bool = False  # If true, exercise is performed per side (clamshells, side plank)
    hold_seconds: Optional[int] = None  # For isometric holds (McGill curl-up 8-10s)
    side: Optional[str] = None  # 'left', 'right', 'both' for unilateral tracking
    distance_steps: Optional[int] = None  # For step-based exercises (lateral walks)
    per_direction: bool = False  # If true, exercise is performed each direction

    @classmethod
    def from_dict(cls, data: dict) -> "WorkoutExercise":
        """Create from JSON dict."""
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Exercise"),
            sets=data.get("sets", 3),
            reps=data.get("reps"),
            duration_seconds=data.get("duration_seconds"),
            duration_minutes=data.get("duration_minutes"),
            distance_meters=data.get("distance_meters"),
            rest_seconds=data.get("rest_seconds", DEFAULT_REST_SECONDS),
            notes=data.get("notes"),
            tempo=data.get("tempo"),
            work_seconds=data.get("work_seconds"),
            per_side=data.get("per_side", False),
            hold_seconds=data.get("hold_seconds"),
            side=data.get("side"),
            distance_steps=data.get("distance_steps"),
            per_direction=data.get("per_direction", False),
        )

    def get_set_duration(self) -> int:
        """Calculate duration for one set in seconds."""
        if self.duration_seconds:
            return self.duration_seconds
        if self.duration_minutes:
            return self.duration_minutes * 60
        if self.work_seconds:
            return self.work_seconds
        if self.reps:
            # Estimate based on rep count
            return self.reps * 4  # ~4 seconds per rep
        return DEFAULT_SET_DURATION_SECONDS


@dataclass
class WorkoutProtocol:
    """Configuration for a workout protocol."""
    id: str
    name: str
    type: str
    duration_minutes: int
    goal: Optional[str] = None
    warmup: Optional[List[str]] = None
    cooldown: Optional[List[str]] = None
    exercises: List[WorkoutExercise] = field(default_factory=list)
    target_hr_pct: Optional[List[int]] = None  # For cardio

    @classmethod
    def from_dict(cls, data: dict) -> "WorkoutProtocol":
        """Create from JSON dict."""
        return cls(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown Workout"),
            type=data.get("type", "strength"),
            duration_minutes=data.get("duration_minutes", 45),
            goal=data.get("goal"),
            warmup=data.get("warmup"),
            cooldown=data.get("cooldown"),
            exercises=[WorkoutExercise.from_dict(ex) for ex in data.get("exercises", [])],
            target_hr_pct=data.get("target_hr_pct"),
        )


def load_protocols() -> Dict[str, WorkoutProtocol]:
    """Load all workout protocols from phase1.json."""
    if not PHASE_CONFIG_PATH.exists():
        logger.warning(f"Phase config not found at {PHASE_CONFIG_PATH}")
        return {}

    with open(PHASE_CONFIG_PATH) as f:
        data = json.load(f)

    protocols = {}
    for protocol_id, protocol_data in data.get("protocols", {}).items():
        protocols[protocol_id] = WorkoutProtocol.from_dict(protocol_data)

    # Add red day override protocol
    red_day_data = data.get("red_day_override", {}).get("protocol", {})
    if red_day_data:
        protocols["red_day"] = WorkoutProtocol.from_dict(red_day_data)

    return protocols


def get_todays_protocol(traffic_light: TrafficLightStatus = TrafficLightStatus.GREEN) -> Optional[WorkoutProtocol]:
    """Get today's workout protocol based on schedule and traffic light."""
    from datetime import date

    protocols = load_protocols()

    # Check for red day override
    if traffic_light == TrafficLightStatus.RED:
        return protocols.get("red_day")

    # Load schedule
    if not PHASE_CONFIG_PATH.exists():
        return None

    with open(PHASE_CONFIG_PATH) as f:
        data = json.load(f)

    schedule = data.get("schedule", {})
    day_of_week = str(date.today().weekday())  # 0=Monday

    protocol_id = schedule.get(day_of_week)
    if protocol_id:
        return protocols.get(protocol_id)

    return None


class WorkoutRunner:
    """
    Timer-based workout runner.

    Guides user through workout with voice announcements, rest timers, and chimes.
    """

    def __init__(
        self,
        check_interrupt: Optional[Callable[[], ControlCommand]] = None,
        intensity_modifier: float = 1.0,  # 0.85 for YELLOW days
    ):
        """
        Initialize workout runner.

        Args:
            check_interrupt: Optional function to check for voice interrupt commands
            intensity_modifier: Multiplier for rest times (>1 = more rest for YELLOW days)
        """
        self._check_interrupt = check_interrupt
        self._intensity_modifier = intensity_modifier
        self._protocols = load_protocols()

        # State
        self._paused = False
        self._stopped = False
        self._current_exercise_idx = 0
        self._current_set = 0

        # Tracking for post-workout logging
        self._completed_exercises: List[Dict[str, Any]] = []

    async def run_todays_workout(
        self,
        speak_func: Optional[Callable[[str], Awaitable[None]]] = None,
        play_chime: Optional[Callable[[], None]] = None,
        traffic_light: TrafficLightStatus = TrafficLightStatus.GREEN,
    ) -> bool:
        """
        Run today's scheduled workout.

        Args:
            speak_func: Async function to speak text via TTS
            play_chime: Function to play completion chime
            traffic_light: Traffic light status (affects intensity/protocol)

        Returns:
            True if completed, False if stopped early
        """
        protocol = get_todays_protocol(traffic_light)

        if not protocol:
            if speak_func:
                await speak_func("No workout scheduled for today.")
            return False

        # Adjust intensity for YELLOW days
        if traffic_light == TrafficLightStatus.YELLOW:
            self._intensity_modifier = 1.15  # 15% more rest

        return await self.run_protocol(protocol, speak_func, play_chime)

    async def run_protocol(
        self,
        protocol: WorkoutProtocol,
        speak_func: Optional[Callable[[str], Awaitable[None]]] = None,
        play_chime: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        Run a specific workout protocol.

        Args:
            protocol: The workout protocol to run
            speak_func: Async function to speak text via TTS
            play_chime: Function to play completion chime

        Returns:
            True if completed, False if stopped early
        """
        self._paused = False
        self._stopped = False
        self._completed_exercises = []

        # Announce workout
        if speak_func:
            announcement = f"{protocol.name}. {protocol.duration_minutes} minutes."
            if protocol.goal:
                announcement += f" {protocol.goal}"
            await speak_func(announcement)

        # Warmup reminder
        if protocol.warmup and speak_func:
            await speak_func("Complete your warmup. Morning routine recommended.")
            await asyncio.sleep(2)

        # Run exercises
        for ex_idx, exercise in enumerate(protocol.exercises):
            if self._stopped:
                break

            self._current_exercise_idx = ex_idx
            completed = await self._run_exercise(exercise, speak_func, play_chime)

            if completed:
                self._completed_exercises.append({
                    "name": exercise.name,
                    "sets": exercise.sets,
                    "reps": exercise.reps,
                })

            if not completed and self._stopped:
                break

        # Cooldown reminder
        if protocol.cooldown and speak_func and not self._stopped:
            await speak_func("Cooldown time. Stretch and recover.")

        # Final announcement
        if not self._stopped and speak_func:
            await speak_func("Workout complete. Log your results when ready.")

        if not self._stopped and play_chime:
            try:
                from atlas.voice.audio_utils import chime_routine_complete
                chime_routine_complete()
            except ImportError:
                play_chime()

        return not self._stopped

    async def _run_exercise(
        self,
        exercise: WorkoutExercise,
        speak_func: Optional[Callable[[str], Awaitable[None]]],
        play_chime: Optional[Callable[[], None]],
    ) -> bool:
        """Run a single exercise with all its sets."""
        # Announce exercise
        if speak_func:
            if exercise.reps:
                announcement = f"{exercise.name}. {exercise.sets} sets of {exercise.reps}."
            elif exercise.duration_seconds:
                announcement = f"{exercise.name}. {exercise.sets} sets of {exercise.duration_seconds} seconds."
            elif exercise.duration_minutes:
                announcement = f"{exercise.name}. {exercise.duration_minutes} minutes."
            else:
                announcement = f"{exercise.name}."

            if exercise.notes:
                announcement += f" {exercise.notes}"

            await speak_func(announcement)

        # Special handling for continuous exercises (cardio, stretches)
        if exercise.sets == 1 and (exercise.duration_minutes or exercise.work_seconds):
            duration = exercise.get_set_duration()
            if exercise.duration_minutes:
                duration = exercise.duration_minutes * 60

            if speak_func:
                await speak_func("Begin.")

            completed = await self._run_timer(duration)

            if completed and play_chime:
                play_chime()

            return completed

        # Run sets
        for set_num in range(1, exercise.sets + 1):
            if self._stopped:
                return False

            self._current_set = set_num

            # Announce set
            if speak_func:
                await speak_func(f"Set {set_num}. Begin.")

            # Run set timer
            set_duration = exercise.get_set_duration()
            completed = await self._run_timer(set_duration)

            if not completed:
                return False

            # Set complete chime
            if play_chime:
                play_chime()

            # Rest between sets (except after last set)
            if set_num < exercise.sets:
                rest_time = int(exercise.rest_seconds * self._intensity_modifier)

                if speak_func:
                    await speak_func(f"Rest. {rest_time} seconds.")

                completed = await self._run_timer(rest_time)

                if not completed:
                    return False

                if play_chime:
                    play_chime()

        return True

    async def _run_timer(self, duration_seconds: int) -> bool:
        """Run a timer with interrupt checking."""
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
                    return True

            await asyncio.sleep(0.1)

        return True

    def stop(self):
        """Stop the workout."""
        self._stopped = True

    def pause(self):
        """Pause the workout."""
        self._paused = True

    def resume(self):
        """Resume paused workout."""
        self._paused = False

    def get_completed_summary(self) -> str:
        """Get summary of completed exercises for logging."""
        if not self._completed_exercises:
            return "No exercises completed"

        parts = []
        for ex in self._completed_exercises:
            if ex.get("reps"):
                parts.append(f"{ex['name']} {ex['sets']}x{ex['reps']}")
            else:
                parts.append(ex['name'])

        return ". ".join(parts)


def format_protocol_for_display(protocol: WorkoutProtocol) -> str:
    """Format protocol for CLI display."""
    lines = [
        f"\n{'=' * 50}",
        f"  {protocol.name}",
        f"  {protocol.type.upper()} | {protocol.duration_minutes} min",
    ]

    if protocol.goal:
        lines.append(f"  Goal: {protocol.goal}")

    lines.append(f"{'=' * 50}")

    if protocol.warmup:
        lines.append("\n📋 Warmup:")
        for item in protocol.warmup:
            lines.append(f"    • {item}")

    lines.append("\n🏋️ Exercises:")
    for ex in protocol.exercises:
        if ex.reps:
            detail = f"{ex.sets}x{ex.reps}"
        elif ex.duration_seconds:
            detail = f"{ex.sets}x{ex.duration_seconds}s"
        elif ex.duration_minutes:
            detail = f"{ex.duration_minutes}min"
        else:
            detail = f"{ex.sets} sets"

        lines.append(f"    • {ex.name} ({detail})")
        if ex.notes:
            lines.append(f"      ↳ {ex.notes}")

    if protocol.cooldown:
        lines.append("\n🧘 Cooldown:")
        for item in protocol.cooldown:
            lines.append(f"    • {item}")

    lines.append(f"\n{'=' * 50}")
    return "\n".join(lines)


async def run_workout_cli(protocol_id: Optional[str] = None, dry_run: bool = False):
    """Run workout in CLI mode."""
    protocols = load_protocols()

    if protocol_id:
        protocol = protocols.get(protocol_id)
        if not protocol:
            print(f"Unknown protocol: {protocol_id}")
            print(f"Available: {', '.join(protocols.keys())}")
            return
    else:
        protocol = get_todays_protocol()
        if not protocol:
            print("No workout scheduled for today.")
            return

    print(format_protocol_for_display(protocol))

    if dry_run:
        print("\n[DRY RUN - not executing timers]")
        return

    runner = WorkoutRunner()

    async def print_speak(text: str):
        print(f"\n🗣️  {text}")

    def print_chime():
        print("🔔 *chime*")

    print("\n[Starting workout - press Ctrl+C to stop]\n")

    try:
        completed = await runner.run_protocol(
            protocol,
            speak_func=print_speak,
            play_chime=print_chime,
        )
        if completed:
            print("\n✅ Workout completed!")
            print(f"Summary: {runner.get_completed_summary()}")
        else:
            print("\n⏹️  Workout stopped early")
    except KeyboardInterrupt:
        runner.stop()
        print("\n\n⏹️  Workout cancelled")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="ATLAS Workout Runner"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show workout structure without running timers"
    )
    parser.add_argument(
        "--protocol", "-p",
        help="Run specific protocol (e.g., strength_a, zone2_cardio)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available protocols"
    )
    args = parser.parse_args()

    if args.list:
        protocols = load_protocols()
        print("\nAvailable workout protocols:")
        for pid, protocol in protocols.items():
            print(f"  • {pid}: {protocol.name} ({protocol.duration_minutes} min)")
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    asyncio.run(run_workout_cli(protocol_id=args.protocol, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
