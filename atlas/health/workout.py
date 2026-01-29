"""
Workout Service

Manages workout protocols and logging.

Loads workout protocols from JSON files and integrates with:
- BlueprintAPI for database logging
- TrafficLightRouter for intensity routing
- Injury tracking for exercise filtering

Usage:
    from atlas.health.workout import WorkoutService

    service = WorkoutService()

    # Get today's workout
    plan = service.get_todays_workout()
    print(plan)

    # Log completed workout
    workout_id = service.log_completed(
        duration_minutes=45,
        energy_before=7,
        energy_after=8
    )
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from atlas.memory.blueprint import (
    get_blueprint_api,
    Workout,
    WorkoutExercise,
)
from atlas.health.router import TrafficLightStatus

logger = logging.getLogger(__name__)


@dataclass
class Exercise:
    """An exercise within a workout protocol."""
    id: str
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None
    duration_minutes: Optional[int] = None
    distance_meters: Optional[float] = None
    notes: Optional[str] = None
    work_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None


@dataclass
class WorkoutProtocol:
    """A workout template from the protocol JSON."""
    id: str
    name: str
    type: str  # 'strength', 'cardio', 'mobility', 'recovery'
    day_of_week: int  # 0=Monday
    duration_minutes: int
    goal: str = ""
    exercises: list[Exercise] = field(default_factory=list)
    warmup: list[str] = field(default_factory=list)
    cooldown: list[str] = field(default_factory=list)
    contraindications: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class WorkoutPlan:
    """Today's workout plan with Traffic Light modifications."""
    protocol: WorkoutProtocol
    traffic_light: TrafficLightStatus
    date: date
    is_red_day_override: bool = False
    skipped_exercises: list[str] = field(default_factory=list)
    modifications: list[str] = field(default_factory=list)

    def to_display(self) -> str:
        """Format workout plan for CLI display."""
        lines = []
        day_names = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        day_name = day_names[self.protocol.day_of_week]

        # Header
        emoji = {
            TrafficLightStatus.GREEN: "\U0001F7E2",
            TrafficLightStatus.YELLOW: "\U0001F7E1",
            TrafficLightStatus.RED: "\U0001F534",
        }.get(self.traffic_light, "")

        intensity = {
            TrafficLightStatus.GREEN: "Full Intensity",
            TrafficLightStatus.YELLOW: "Moderate Intensity",
            TrafficLightStatus.RED: "Recovery Only",
        }.get(self.traffic_light, "")

        lines.append("=" * 60)
        lines.append(f"  {day_name} - {self.protocol.name}")
        lines.append(f"  Duration: ~{self.protocol.duration_minutes} min | {emoji} {intensity}")
        lines.append("=" * 60)

        if self.is_red_day_override:
            lines.append("")
            lines.append("  \u26A0\uFE0F  RED DAY OVERRIDE - Recovery protocol activated")

        # Goal
        if self.protocol.goal:
            lines.append("")
            lines.append(f"GOAL: {self.protocol.goal}")

        # Warmup
        if self.protocol.warmup:
            lines.append("")
            lines.append("WARM-UP:")
            for item in self.protocol.warmup:
                lines.append(f"  \u2022 {item}")

        # Exercises
        lines.append("")
        lines.append("EXERCISES:")
        for i, ex in enumerate(self.protocol.exercises, 1):
            if ex.id in self.skipped_exercises:
                lines.append(f"  {i}. {ex.name} - SKIPPED (injury)")
                continue

            details = []
            if ex.sets:
                if ex.reps:
                    details.append(f"{ex.sets}x{ex.reps}")
                elif ex.duration_seconds:
                    details.append(f"{ex.sets}x{ex.duration_seconds}s")
                elif ex.duration_minutes:
                    details.append(f"{ex.sets}x{ex.duration_minutes}min")
            elif ex.duration_minutes:
                details.append(f"{ex.duration_minutes} min")

            detail_str = " | ".join(details) if details else ""
            lines.append(f"  {i}. {ex.name:<35} {detail_str}")
            if ex.notes:
                lines.append(f"     \u2192 {ex.notes}")

        # Cooldown
        if self.protocol.cooldown:
            lines.append("")
            lines.append("COOL-DOWN:")
            for item in self.protocol.cooldown:
                lines.append(f"  \u2022 {item}")

        # Modifications/warnings
        if self.modifications:
            lines.append("")
            lines.append("-" * 60)
            for mod in self.modifications:
                lines.append(f"  \u26A0\uFE0F  {mod}")

        lines.append("=" * 60)
        return "\n".join(lines)


class WorkoutService:
    """
    Workout protocol loading and logging service.

    Loads protocols from config/workouts/*.json
    Phase 1 is the Shoulder Rehab Protocol (weeks 1-4).
    """

    PROTOCOLS_DIR = Path(__file__).parent.parent.parent / "config" / "workouts"

    def __init__(self, phase: str = "phase1"):
        """
        Initialize workout service.

        Args:
            phase: Protocol phase to load ('phase1', 'phase2', etc.)
        """
        self.phase = phase
        self.protocols: dict[str, WorkoutProtocol] = {}
        self.schedule: dict[int, str] = {}  # day_of_week -> protocol_id
        self.red_day_protocol: Optional[WorkoutProtocol] = None
        self.daily_nonnegotiables: list[Exercise] = []
        self.injury_context: dict = {}
        self._blueprint = get_blueprint_api()
        self._load_protocols()

    def _load_protocols(self) -> None:
        """Load workout protocols from JSON file."""
        protocol_file = self.PROTOCOLS_DIR / f"{self.phase}.json"

        if not protocol_file.exists():
            logger.warning(f"Protocol file not found: {protocol_file}")
            return

        try:
            with open(protocol_file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse protocol file: {e}")
            return

        # Load schedule
        self.schedule = {int(k): v for k, v in data.get("schedule", {}).items()}

        # Load protocols
        for proto_id, proto_data in data.get("protocols", {}).items():
            exercises = [
                Exercise(
                    id=ex.get("id", ""),
                    name=ex.get("name", ""),
                    sets=ex.get("sets"),
                    reps=ex.get("reps"),
                    duration_seconds=ex.get("duration_seconds"),
                    duration_minutes=ex.get("duration_minutes"),
                    distance_meters=ex.get("distance_meters"),
                    notes=ex.get("notes"),
                    work_seconds=ex.get("work_seconds"),
                    rest_seconds=ex.get("rest_seconds"),
                )
                for ex in proto_data.get("exercises", [])
            ]

            self.protocols[proto_id] = WorkoutProtocol(
                id=proto_id,
                name=proto_data.get("name", proto_id),
                type=proto_data.get("type", "strength"),
                day_of_week=proto_data.get("day_of_week", 0),
                duration_minutes=proto_data.get("duration_minutes", 45),
                goal=proto_data.get("goal", ""),
                exercises=exercises,
                warmup=proto_data.get("warmup", []),
                cooldown=proto_data.get("cooldown", []),
                contraindications=proto_data.get("contraindications", []),
            )

        # Load RED day override
        red_day_data = data.get("red_day_override", {}).get("protocol")
        if red_day_data:
            exercises = [
                Exercise(
                    id=ex.get("id", ""),
                    name=ex.get("name", ""),
                    duration_minutes=ex.get("duration_minutes"),
                    notes=ex.get("notes"),
                )
                for ex in red_day_data.get("exercises", [])
            ]
            self.red_day_protocol = WorkoutProtocol(
                id="red_day",
                name=red_day_data.get("name", "RED DAY Protocol"),
                type="recovery",
                day_of_week=-1,  # Any day
                duration_minutes=red_day_data.get("duration_minutes", 40),
                exercises=exercises,
            )

        # Load daily non-negotiables
        nn_data = data.get("daily_nonnegotiables", {})
        self.daily_nonnegotiables = [
            Exercise(
                id=ex.get("id", ""),
                name=ex.get("name", ""),
                sets=ex.get("sets"),
                reps=ex.get("reps"),
                duration_seconds=ex.get("duration_seconds"),
                duration_minutes=ex.get("duration_minutes"),
                notes=ex.get("notes"),
            )
            for ex in nn_data.get("exercises", [])
        ]

        # Load injury context
        self.injury_context = data.get("injury_context", {})

        logger.info(f"Loaded {len(self.protocols)} workout protocols for {self.phase}")

    def get_protocol_for_day(self, day_of_week: int) -> Optional[WorkoutProtocol]:
        """
        Get scheduled protocol for a day of week.

        Args:
            day_of_week: 0=Monday, 6=Sunday

        Returns:
            WorkoutProtocol or None if no workout scheduled
        """
        protocol_id = self.schedule.get(day_of_week)
        if protocol_id:
            return self.protocols.get(protocol_id)
        return None

    def get_todays_workout(
        self,
        traffic_light: TrafficLightStatus = TrafficLightStatus.GREEN,
        target_date: Optional[date] = None,
    ) -> Optional[WorkoutPlan]:
        """
        Get today's workout plan with Traffic Light modifications.

        Args:
            traffic_light: Current traffic light status
            target_date: Date to get workout for (default: today)

        Returns:
            WorkoutPlan with appropriate modifications
        """
        if target_date is None:
            target_date = date.today()

        day_of_week = target_date.weekday()  # 0=Monday

        # RED day override
        if traffic_light == TrafficLightStatus.RED and self.red_day_protocol:
            return WorkoutPlan(
                protocol=self.red_day_protocol,
                traffic_light=traffic_light,
                date=target_date,
                is_red_day_override=True,
                modifications=["RED DAY: Scheduled workout replaced with recovery protocol"],
            )

        # Get scheduled protocol
        protocol = self.get_protocol_for_day(day_of_week)
        if not protocol:
            return None

        # Get contraindicated exercises from active injuries
        contraindicated = set(self._blueprint.get_contraindicated_exercises())
        # Add protocol-specific contraindications
        contraindicated.update(protocol.contraindications)

        # Filter exercises
        skipped = []
        for ex in protocol.exercises:
            if ex.id in contraindicated:
                skipped.append(ex.id)

        modifications = []
        if skipped:
            modifications.append(
                f"Active injury: Skipping {len(skipped)} exercises ({', '.join(skipped)})"
            )

        if traffic_light == TrafficLightStatus.YELLOW:
            modifications.append("YELLOW DAY: Moderate intensity. Stop if fatigue sets in.")

        return WorkoutPlan(
            protocol=protocol,
            traffic_light=traffic_light,
            date=target_date,
            skipped_exercises=skipped,
            modifications=modifications,
        )

    def log_completed(
        self,
        duration_minutes: int,
        workout_type: Optional[str] = None,
        energy_before: Optional[int] = None,
        energy_after: Optional[int] = None,
        notes: Optional[str] = None,
        exercises: Optional[list[dict]] = None,
        target_date: Optional[date] = None,
    ) -> int:
        """
        Log a completed workout.

        Args:
            duration_minutes: How long the workout lasted
            workout_type: Type of workout (strength, cardio, mobility, recovery)
            energy_before: Energy level before (1-10)
            energy_after: Energy level after (1-10)
            notes: Optional notes
            exercises: Optional list of exercise dicts with sets/reps/weight
            target_date: Date of workout (default: today)

        Returns:
            Workout ID
        """
        if target_date is None:
            target_date = date.today()

        # Determine workout type from schedule if not provided
        if not workout_type:
            protocol = self.get_protocol_for_day(target_date.weekday())
            workout_type = protocol.type if protocol else "strength"

        # Log workout
        workout = Workout(
            date=target_date,
            type=workout_type,
            duration_minutes=duration_minutes,
            energy_before=energy_before,
            energy_after=energy_after,
            notes=notes,
        )
        workout_id = self._blueprint.log_workout(workout)

        # Log exercises if provided
        if exercises:
            for i, ex in enumerate(exercises):
                exercise = WorkoutExercise(
                    workout_id=workout_id,
                    exercise_id=ex.get("id", f"exercise_{i}"),
                    exercise_name=ex.get("name", "Unknown"),
                    sets=ex.get("sets"),
                    reps=ex.get("reps"),
                    weight_kg=ex.get("weight_kg"),
                    duration_seconds=ex.get("duration_seconds"),
                    notes=ex.get("notes"),
                    order_index=i,
                )
                self._blueprint.add_workout_exercise(exercise)

        logger.info(f"Logged workout {workout_id}: {workout_type}, {duration_minutes}min")
        return workout_id

    def get_workout_history(self, days: int = 14) -> list[dict]:
        """
        Get recent workout history.

        Args:
            days: Number of days to look back

        Returns:
            List of workout dicts with exercises
        """
        workouts = self._blueprint.get_workouts(days=days)
        result = []

        for w in workouts:
            exercises = self._blueprint.get_workout_exercises(w.id)
            result.append({
                "id": w.id,
                "date": w.date.isoformat(),
                "type": w.type,
                "duration_minutes": w.duration_minutes,
                "energy_before": w.energy_before,
                "energy_after": w.energy_after,
                "notes": w.notes,
                "exercises": [
                    {
                        "name": ex.exercise_name,
                        "sets": ex.sets,
                        "reps": ex.reps,
                        "weight_kg": ex.weight_kg,
                    }
                    for ex in exercises
                ],
            })

        return result

    def get_weekly_stats(self) -> dict:
        """Get weekly workout statistics."""
        workouts = self._blueprint.get_workouts(days=7)

        total_duration = sum(w.duration_minutes or 0 for w in workouts)
        by_type = {}
        for w in workouts:
            by_type[w.type] = by_type.get(w.type, 0) + 1

        # Expected workouts this week
        expected = len(self.schedule)
        completed = len(workouts)

        return {
            "completed": completed,
            "expected": expected,
            "completion_pct": completed / expected * 100 if expected > 0 else 0,
            "total_duration_minutes": total_duration,
            "by_type": by_type,
        }
