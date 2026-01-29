"""State dataclasses for voice bridge components.

Consolidates scattered instance variables from BridgeFileServer into clean
dataclass structures for better organization and testability.
"""

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class AssessmentState:
    """State for baseline assessment protocol sessions."""

    runner: Any = None  # AssessmentProtocolRunner instance (avoid circular import)
    timing: bool = False  # True during timed test
    timer_start: float | None = None
    pending_session: str | None = None  # Session choice pending (A/B/C)

    def reset(self) -> None:
        """Reset all state to defaults."""
        self.runner = None
        self.timing = False
        self.timer_start = None
        self.pending_session = None


@dataclass
class WorkoutState:
    """State for interactive workout sessions."""

    # Session state
    active: bool = False  # In workout session
    protocol: Any = None  # Current WorkoutProtocol (avoid circular import)
    exercises: list = field(default_factory=list)  # List of WorkoutExercise
    exercise_idx: int = 0  # Current exercise index
    current_exercise: dict | None = None  # Current exercise dict
    current_set: int = 0  # Current set number (1-indexed during workout)
    current_weight: float | None = None  # Weight for current exercise
    exercise_pending: bool = False  # Waiting for "ready"
    set_active: bool = False  # User doing a set
    total_sets: int = 0  # Total sets for current exercise
    awaiting_reps: bool = False  # Waiting for AMRAP rep count

    # Rest timer
    rest_active: bool = False  # Rest timer running
    rest_start: float | None = None
    rest_duration: int = 0
    beeps_played: set = field(default_factory=set)  # Countdown beeps played

    # Logging
    log: list = field(default_factory=list)  # Track completed exercises with weights
    set_reps: list = field(default_factory=list)  # Track reps per set for current exercise

    # Exercise timer (for timed holds like balance exercises)
    exercise_timer_active: bool = False  # Timer running for timed exercise
    exercise_timer_start: float | None = None
    exercise_timer_duration: int = 0  # Per-side duration
    exercise_current_side: str | None = None  # 'left', 'right', or None
    exercise_sides_done: int = 0  # 0, 1, or 2 for per_side exercises
    exercise_beeps_played: set = field(default_factory=set)  # Countdown beeps for exercise
    last_set_of_timed_exercise: bool = False  # Flag for async advance after last timed set

    # Pause state (UI button support)
    paused: bool = False  # Workout paused
    timer_remaining: int = 0  # Stored when paused
    pause_in_progress: bool = False  # Debounce for pause to prevent double-entry

    # Completion state (awaiting user confirmation to log)
    workout_finished: bool = False  # Workout complete, awaiting COMPLETE button
    exercises_completed: int = 0  # Count of exercises done when finished

    def reset(self) -> None:
        """Reset all state to defaults."""
        self.active = False
        self.protocol = None
        self.exercises = []
        self.exercise_idx = 0
        self.current_exercise = None
        self.current_set = 0
        self.current_weight = None
        self.exercise_pending = False
        self.set_active = False
        self.total_sets = 0
        self.awaiting_reps = False

        self.rest_active = False
        self.rest_start = None
        self.rest_duration = 0
        self.beeps_played = set()

        self.log = []
        self.set_reps = []

        self.exercise_timer_active = False
        self.exercise_timer_start = None
        self.exercise_timer_duration = 0
        self.exercise_current_side = None
        self.exercise_sides_done = 0
        self.exercise_beeps_played = set()
        self.last_set_of_timed_exercise = False

        self.paused = False
        self.timer_remaining = 0
        self.pause_in_progress = False

        self.workout_finished = False
        self.exercises_completed = 0


@dataclass
class RoutineState:
    """State for interactive morning routine sessions."""

    # Session state
    active: bool = False  # In routine session
    runner: Any = None  # RoutineRunner instance (avoid circular import)
    paused: bool = False  # Routine paused
    current_section: str | None = None
    current_exercise: dict | None = None
    exercise_idx: int = 0
    section_idx: int = 0

    # Timer state
    timer_start: float | None = None
    timer_duration: int = 0
    timer_remaining: int = 0  # Stored when paused
    timer_active: bool = False  # Timer currently running

    # Exercise state
    exercise_complete: bool = False  # Current exercise timer done
    exercise_pending: bool = False  # Waiting for user "ready/begin/go"
    current_side: str | None = None  # 'left' or 'right' for per_side exercises
    side_switched: bool = False  # Has side switch happened for this exercise

    # Auto-advance state (Command Centre - autonomous flow)
    auto_advance_pending: bool = False  # Transitioning to next exercise
    auto_advance_start: float | None = None  # When transition started
    auto_advance_phase: str | None = None  # 'completed', 'announcing', 'positioning'
    next_exercise_msg: str | None = None  # Pre-built announcement for next exercise
    next_exercise_name: str | None = None  # Name of next exercise (for UI during transition)

    # Routine completion state (for COMPLETE button in UI)
    routine_finished: bool = False  # Entire routine complete, awaiting user confirmation
    routine_finish_time: float | None = None  # When routine finished

    def reset(self) -> None:
        """Reset all state to defaults."""
        self.active = False
        self.runner = None
        self.paused = False
        self.current_section = None
        self.current_exercise = None
        self.exercise_idx = 0
        self.section_idx = 0

        self.timer_start = None
        self.timer_duration = 0
        self.timer_remaining = 0
        self.timer_active = False

        self.exercise_complete = False
        self.exercise_pending = False
        self.current_side = None
        self.side_switched = False

        self.auto_advance_pending = False
        self.auto_advance_start = None
        self.auto_advance_phase = None
        self.next_exercise_msg = None
        self.next_exercise_name = None

        self.routine_finished = False
        self.routine_finish_time = None


@dataclass
class TimerState:
    """Shared timer synchronization state."""

    lock: Lock = field(default_factory=Lock)
    tts_speaking: bool = False  # True while TTS is playing in background

    def reset(self) -> None:
        """Reset state to defaults (lock is not reset)."""
        self.tts_speaking = False
