"""Timer status dict builders for Command Centre UI.

Extracted from BridgeFileServer._get_timer_status() to reduce method complexity.
Each builder handles a specific timer mode (routine, workout, transitions).
"""

from dataclasses import dataclass, field
from typing import Any, Callable
import time


def _can_skip(next_exercise: str | None) -> bool:
    """Check if skip is allowed based on next exercise.

    Returns False if on last exercise (next_exercise empty or 'Routine/Workout Complete').
    """
    if not next_exercise:
        return False
    if next_exercise.lower() in ('routine complete', 'workout complete', ''):
        return False
    return True


@dataclass
class TimerContext:
    """Context needed by timer builders - avoids passing whole server instance.

    Contains all state variables and callback functions needed to build
    timer status dictionaries for the Command Centre UI.
    """
    # Routine context
    routine_active: bool = False
    routine_timer_active: bool = False
    routine_paused: bool = False
    routine_timer_start: float | None = None
    routine_timer_duration: int = 0
    routine_timer_remaining: int = 0
    routine_current_exercise: dict | None = None
    routine_current_section: str | None = None
    routine_exercise_pending: bool = False
    routine_current_side: str | None = None
    routine_exercise_idx: int = 0
    routine_section_idx: int = 0
    routine_auto_advance_pending: bool = False
    routine_auto_advance_start: float | None = None
    routine_auto_advance_phase: str | None = None
    routine_next_exercise_name: str | None = None
    routine_finished: bool = False  # Entire routine complete, awaiting user log confirmation

    # Workout context
    workout_active: bool = False
    workout_rest_active: bool = False
    workout_rest_start: float | None = None
    workout_rest_duration: int = 0
    workout_exercise_timer_active: bool = False
    workout_exercise_timer_start: float | None = None
    workout_exercise_timer_duration: int = 0
    workout_exercise_current_side: str | None = None
    workout_exercise_pending: bool = False
    workout_current_exercise: dict | None = None
    workout_current_set: int = 0
    workout_total_sets: int = 0
    workout_paused: bool = False
    workout_timer_remaining: int = 0
    workout_exercise_idx: int = 0
    workout_exercises: list = field(default_factory=list)
    workout_protocol_name: str = 'Workout'
    workout_current_weight: float | None = None
    workout_set_active: bool = False
    workout_awaiting_reps: bool = False
    workout_finished: bool = False  # Workout complete, awaiting user log confirmation
    workout_exercises_completed: int = 0  # Count of exercises done

    # Callbacks for external lookups (function references)
    get_form_cue: Callable[[str, str, int], str | None] | None = None
    get_setup_tip: Callable[[str, str], str | None] | None = None
    get_next_exercise_info: Callable[[], dict | None] | None = None
    count_routine_exercises: Callable[[], int] | None = None
    get_routine_exercise_number: Callable[[], int] | None = None
    get_workout_form_cue: Callable[[str, str], str | None] | None = None
    get_workout_setup_tip: Callable[[str, str], str | None] | None = None
    get_next_workout_exercise_info: Callable[[], dict | None] | None = None
    get_weight_recommendation: Callable[[str], float | None] | None = None


def build_routine_timer_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for active routine timer.

    Handles the main routine exercise timer, including:
    - Active/paused state with correct remaining time calculation
    - Form cue rotation (every 10 seconds)
    - Setup text and next exercise preview

    Returns None if conditions not met.
    """
    if not (ctx.routine_active and (ctx.routine_timer_active or ctx.routine_paused) and ctx.routine_timer_start):
        return None

    ex = ctx.routine_current_exercise
    if not ex:
        return None

    # Calculate timing based on pause state
    if ctx.routine_paused:
        remaining = ctx.routine_timer_remaining
        elapsed = ctx.routine_timer_duration - remaining
    else:
        elapsed = time.monotonic() - ctx.routine_timer_start
        remaining = max(0, ctx.routine_timer_duration - elapsed)

    progress = min(100, (elapsed / ctx.routine_timer_duration) * 100) if ctx.routine_timer_duration > 0 else 0

    # Get external data via callbacks
    total_exercises = ctx.count_routine_exercises() if ctx.count_routine_exercises else 0
    current_num = ctx.get_routine_exercise_number() if ctx.get_routine_exercise_number else 1

    # Form cue rotation (every 10 seconds)
    cue_index = int(elapsed // 10)
    form_cue = ''
    if ctx.get_form_cue:
        form_cue = ctx.get_form_cue(ex.get('id', ''), ex.get('name', ''), cue_index) or ''

    setup_text = ''
    if ctx.get_setup_tip:
        setup_text = ctx.get_setup_tip(ex.get('id', ''), ex.get('name', '')) or ''

    next_ex_info = ctx.get_next_exercise_info() if ctx.get_next_exercise_info else None

    return {
        "active": True,
        "mode": "routine",
        "is_paused": ctx.routine_paused,
        "exercise_name": ex.get('name', 'Exercise'),
        "exercise_idx": current_num,
        "total_exercises": total_exercises,
        "section_name": ctx.routine_current_section or '',
        "duration_seconds": ctx.routine_timer_duration,
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "progress_pct": round(progress, 1),
        "per_side": ex.get('per_side', False),
        "current_side": ctx.routine_current_side,
        "form_cue": form_cue,
        "setup_text": setup_text,
        "next_exercise": next_ex_info.get('name') if next_ex_info else '',
        "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
        "auto_advance": ctx.routine_auto_advance_pending,
        "auto_advance_phase": ctx.routine_auto_advance_phase,
    }


def build_routine_transition_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for routine auto-advance transition.

    Handles two phases:
    - 'completed': 2-second pause showing "COMPLETE" screen
    - 'pending': 4-second positioning showing "READY?" screen

    Returns None if conditions not met.
    """
    if not (ctx.routine_active and ctx.routine_auto_advance_pending):
        return None

    # Calculate elapsed from auto-advance start
    elapsed = time.monotonic() - (ctx.routine_auto_advance_start or time.monotonic())

    total_exercises = ctx.count_routine_exercises() if ctx.count_routine_exercises else 0
    current_num = ctx.get_routine_exercise_number() if ctx.get_routine_exercise_number else 1

    if ctx.routine_auto_advance_phase == 'completed':
        # 2-second "exercise complete" pause
        countdown = max(0, 2 - elapsed)
        next_ex_name = ctx.routine_next_exercise_name or 'Next Exercise'

        return {
            "active": True,
            "mode": "routine_transition",
            "is_paused": False,
            "exercise_name": next_ex_name,
            "exercise_idx": current_num + 1,  # +1 for next exercise
            "total_exercises": total_exercises,
            "section_name": ctx.routine_current_section or '',
            "duration_seconds": 2,
            "elapsed_seconds": int(elapsed),
            "remaining_seconds": int(countdown),
            "progress_pct": 0,
            "per_side": False,
            "current_side": None,
            "form_cue": '',
            "setup_text": '',
            "next_exercise": ctx.routine_next_exercise_name or '',
            "can_skip": _can_skip(ctx.routine_next_exercise_name),
            "auto_advance": True,
            "auto_advance_phase": 'completed',
        }

    elif ctx.routine_auto_advance_phase == 'pending':
        # 4-second pending/positioning phase
        # State has been advanced, so current_exercise is the NEW exercise
        pending_elapsed = elapsed - 2.0  # Subtract the 2s completed phase
        countdown = max(0, 4 - pending_elapsed)

        ex = ctx.routine_current_exercise
        if not ex:
            return None

        # Get first cue from exercise
        form_cue = ''
        if ex.get('cues'):
            form_cue = ex.get('cues')[0] or ''

        setup_text = ''
        if ctx.get_setup_tip:
            setup_text = ctx.get_setup_tip(ex.get('id', ''), ex.get('name', '')) or ''

        next_ex_info = ctx.get_next_exercise_info() if ctx.get_next_exercise_info else None

        return {
            "active": True,
            "mode": "routine_pending",  # Show READY? screen
            "is_paused": False,
            "exercise_name": ex.get('name', 'Exercise'),
            "exercise_idx": current_num,
            "total_exercises": total_exercises,
            "section_name": ctx.routine_current_section or '',
            "duration_seconds": ex.get('duration_seconds') or ctx.routine_timer_duration or 30,
            "elapsed_seconds": 0,
            "remaining_seconds": int(countdown),  # Countdown to auto-start
            "progress_pct": 0,
            "per_side": ex.get('per_side', False),
            "current_side": 'left' if ex.get('per_side', False) else None,
            "form_cue": form_cue,
            "setup_text": setup_text,
            "next_exercise": next_ex_info.get('name') if next_ex_info else '',
            "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
            "auto_advance": True,
            "auto_advance_phase": 'pending',
            "pending_ready": True,  # Signal UI
        }

    return None


def build_routine_pending_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for routine pending (waiting for 'ready' command).

    Shows exercise info while waiting for user to say "ready".

    Returns None if conditions not met.
    """
    if not (ctx.routine_active and ctx.routine_exercise_pending and ctx.routine_current_exercise):
        return None

    ex = ctx.routine_current_exercise

    total_exercises = ctx.count_routine_exercises() if ctx.count_routine_exercises else 0
    current_num = ctx.get_routine_exercise_number() if ctx.get_routine_exercise_number else 1

    duration = ex.get('duration_seconds') or ctx.routine_timer_duration or 30

    # Get first cue from exercise
    form_cue = ''
    if ex.get('cues'):
        form_cue = ex.get('cues')[0] or ''

    setup_text = ''
    if ctx.get_setup_tip:
        setup_text = ctx.get_setup_tip(ex.get('id', ''), ex.get('name', '')) or ''

    next_ex_info = ctx.get_next_exercise_info() if ctx.get_next_exercise_info else None

    return {
        "active": True,
        "mode": "routine_pending",
        "is_paused": False,
        "exercise_name": ex.get('name', 'Exercise'),
        "exercise_idx": current_num,
        "total_exercises": total_exercises,
        "section_name": ctx.routine_current_section or '',
        "duration_seconds": duration,
        "elapsed_seconds": 0,
        "remaining_seconds": duration,
        "progress_pct": 0,
        "per_side": ex.get('per_side', False),
        "current_side": 'left' if ex.get('per_side', False) else None,
        "form_cue": form_cue,
        "setup_text": setup_text,
        "next_exercise": next_ex_info.get('name') if next_ex_info else '',
        "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
        "auto_advance": False,
        "auto_advance_phase": None,
        "pending_ready": True,  # Signal UI to show "Say READY to start"
    }


def build_routine_complete_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for routine completion (awaiting user confirmation).

    Shows the COMPLETE button for user to log the routine completion.
    Active until user clicks COMPLETE or dismisses.

    Returns None if conditions not met.
    """
    if not ctx.routine_finished:
        return None

    total_exercises = ctx.count_routine_exercises() if ctx.count_routine_exercises else 0

    return {
        "active": True,
        "mode": "routine_complete",
        "is_paused": False,
        "exercise_name": "Routine Complete",
        "exercise_idx": total_exercises,
        "total_exercises": total_exercises,
        "section_name": "Well done!",
        "duration_seconds": 0,
        "elapsed_seconds": 0,
        "remaining_seconds": 0,
        "progress_pct": 100,
        "per_side": False,
        "current_side": None,
        "form_cue": "",
        "setup_text": "Press COMPLETE to log today's routine",
        "next_exercise": "",
        "can_skip": False,  # Can't skip on complete screen
        "auto_advance": False,
        "auto_advance_phase": None,
        "routine_finished": True,  # Signal UI to show COMPLETE button
    }


def build_workout_complete_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for workout completion (awaiting user confirmation).

    Shows the COMPLETE button for user to log the workout.
    Active until user clicks COMPLETE or says 'finished workout'.

    Returns None if conditions not met.
    """
    if not ctx.workout_finished:
        return None

    return {
        "active": True,
        "mode": "workout_complete",
        "is_paused": False,
        "exercise_name": "Workout Complete",
        "exercise_idx": ctx.workout_exercises_completed,
        "total_exercises": ctx.workout_exercises_completed,
        "section_name": "Well done!",
        "duration_seconds": 0,
        "elapsed_seconds": 0,
        "remaining_seconds": 0,
        "progress_pct": 100,
        "per_side": False,
        "current_side": None,
        "form_cue": "",
        "setup_text": "Press COMPLETE to log workout",
        "next_exercise": "",
        "can_skip": False,  # Can't skip on complete screen
        "workout_finished": True,  # Signal UI to show COMPLETE button
    }


def build_workout_timer_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for workout timed exercise (e.g., balance holds).

    Returns None if conditions not met.
    """
    if not (ctx.workout_active and ctx.workout_exercise_timer_active and ctx.workout_exercise_timer_start):
        return None

    ex = ctx.workout_current_exercise
    if not ex:
        return None

    elapsed = time.monotonic() - ctx.workout_exercise_timer_start
    remaining = max(0, ctx.workout_exercise_timer_duration - elapsed)
    progress = min(100, (elapsed / ctx.workout_exercise_timer_duration) * 100) if ctx.workout_exercise_timer_duration > 0 else 0

    form_cue = ''
    if ctx.get_workout_form_cue:
        form_cue = ctx.get_workout_form_cue(ex.get('id', ''), ex.get('name', '')) or ''

    setup_text = ''
    if ctx.get_workout_setup_tip:
        setup_text = ctx.get_workout_setup_tip(ex.get('id', ''), ex.get('name', '')) or ''

    next_ex_info = ctx.get_next_workout_exercise_info() if ctx.get_next_workout_exercise_info else None

    return {
        "active": True,
        "mode": "workout",
        "exercise_name": ex.get('name', 'Exercise'),
        "exercise_idx": ctx.workout_exercise_idx + 1,
        "total_exercises": len(ctx.workout_exercises),
        "section_name": ctx.workout_protocol_name,
        "duration_seconds": ctx.workout_exercise_timer_duration,
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "progress_pct": round(progress, 1),
        "per_side": ex.get('per_side', False),
        "current_side": ctx.workout_exercise_current_side,
        "form_cue": form_cue,
        "set_info": f"Set {ctx.workout_current_set}/{ctx.workout_total_sets}",
        "is_paused": ctx.workout_paused,
        "setup_text": setup_text,
        "next_exercise": next_ex_info.get('name') if next_ex_info else '',
        "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
    }


def build_workout_rest_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for workout rest timer.

    Returns None if conditions not met.
    """
    if not (ctx.workout_active and ctx.workout_rest_active and ctx.workout_rest_start):
        return None

    elapsed = time.monotonic() - ctx.workout_rest_start
    remaining = max(0, ctx.workout_rest_duration - elapsed)
    progress = min(100, (elapsed / ctx.workout_rest_duration) * 100) if ctx.workout_rest_duration > 0 else 0

    ex = ctx.workout_current_exercise
    next_ex_info = ctx.get_next_workout_exercise_info() if ctx.get_next_workout_exercise_info else None

    return {
        "active": True,
        "mode": "workout_rest",
        "exercise_name": ex.get('name', 'Exercise') if ex else 'Rest',
        "exercise_idx": ctx.workout_exercise_idx + 1,
        "total_exercises": len(ctx.workout_exercises),
        "section_name": ctx.workout_protocol_name,
        "duration_seconds": ctx.workout_rest_duration,
        "elapsed_seconds": int(elapsed),
        "remaining_seconds": int(remaining),
        "progress_pct": round(progress, 1),
        "per_side": False,
        "current_side": None,
        "form_cue": 'Rest',
        "set_info": f"Set {ctx.workout_current_set}/{ctx.workout_total_sets}",
        "is_paused": ctx.workout_paused,
        "setup_text": '',  # Rest period - no setup needed
        "next_exercise": next_ex_info.get('name') if next_ex_info else '',
        "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
    }


def build_workout_pending_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for workout pending (waiting for 'ready' or START button).

    Returns None if conditions not met.
    """
    if not (ctx.workout_active and ctx.workout_exercise_pending):
        return None

    ex = ctx.workout_current_exercise
    if not ex:
        return None

    form_cue = ''
    if ctx.get_workout_form_cue:
        form_cue = ctx.get_workout_form_cue(ex.get('id', ''), ex.get('name', '')) or ''

    setup_text = ''
    if ctx.get_workout_setup_tip:
        setup_text = ctx.get_workout_setup_tip(ex.get('id', ''), ex.get('name', '')) or ''

    next_ex_info = ctx.get_next_workout_exercise_info() if ctx.get_next_workout_exercise_info else None

    # Get recommended weight if not yet set
    recommended_weight = None
    if not ctx.workout_current_weight and ctx.get_weight_recommendation:
        exercise_id = ex.get('id', ex.get('name', '')).lower().replace(' ', '_')
        recommended_weight = ctx.get_weight_recommendation(exercise_id)

    return {
        "active": True,
        "mode": "workout_pending",
        "exercise_name": ex.get('name', 'Exercise'),
        "exercise_idx": ctx.workout_exercise_idx + 1,
        "total_exercises": len(ctx.workout_exercises),
        "section_name": ctx.workout_protocol_name,
        "duration_seconds": ex.get('duration_seconds', 0),
        "remaining_seconds": 0,
        "progress_pct": 0,
        "current_set": ctx.workout_current_set + 1,
        "total_sets": ex.get('sets', 3),
        "reps": ex.get('reps'),
        "weight": ctx.workout_current_weight,
        "recommended_weight": recommended_weight,
        "per_side": ex.get('per_side', False),
        "form_cue": form_cue,
        "pending_ready": True,
        "is_paused": ctx.workout_paused,
        "setup_text": setup_text,
        "next_exercise": next_ex_info.get('name') if next_ex_info else '',
        "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
    }


def build_workout_set_active_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for workout set active (rep-based set in progress).

    No countdown timer for rep-based exercises.

    Returns None if conditions not met.
    """
    if not (ctx.workout_active and ctx.workout_set_active and not ctx.workout_exercise_timer_active):
        return None

    ex = ctx.workout_current_exercise
    if not ex:
        return None

    form_cue = ''
    if ctx.get_workout_form_cue:
        form_cue = ctx.get_workout_form_cue(ex.get('id', ''), ex.get('name', '')) or ''

    setup_text = ''
    if ctx.get_workout_setup_tip:
        setup_text = ctx.get_workout_setup_tip(ex.get('id', ''), ex.get('name', '')) or ''

    next_ex_info = ctx.get_next_workout_exercise_info() if ctx.get_next_workout_exercise_info else None

    total_sets = ex.get('sets', 3)
    progress = (ctx.workout_current_set / total_sets) * 100 if total_sets > 0 else 0

    return {
        "active": True,
        "mode": "workout_set_active",
        "exercise_name": ex.get('name', 'Exercise'),
        "exercise_idx": ctx.workout_exercise_idx + 1,
        "total_exercises": len(ctx.workout_exercises),
        "section_name": ctx.workout_protocol_name,
        "duration_seconds": 0,  # No timer for rep-based
        "remaining_seconds": 0,
        "progress_pct": round(progress, 1),
        "current_set": ctx.workout_current_set,
        "total_sets": total_sets,
        "weight": ctx.workout_current_weight,
        "per_side": ex.get('per_side', False),
        "form_cue": form_cue,
        "is_paused": ctx.workout_paused,
        "setup_text": setup_text,
        "next_exercise": next_ex_info.get('name') if next_ex_info else '',
        "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
    }


def build_workout_awaiting_reps_dict(ctx: TimerContext) -> dict | None:
    """Build timer dict for workout awaiting AMRAP rep count.

    Returns None if conditions not met.
    """
    if not (ctx.workout_active and ctx.workout_awaiting_reps):
        return None

    ex = ctx.workout_current_exercise
    if not ex:
        return None

    next_ex_info = ctx.get_next_workout_exercise_info() if ctx.get_next_workout_exercise_info else None

    return {
        "active": True,
        "mode": "workout_awaiting_reps",
        "exercise_name": ex.get('name', 'Exercise'),
        "exercise_idx": ctx.workout_exercise_idx + 1,
        "total_exercises": len(ctx.workout_exercises),
        "section_name": ctx.workout_protocol_name,
        "duration_seconds": 0,
        "remaining_seconds": 0,
        "progress_pct": 100,
        "current_set": ctx.workout_current_set,
        "total_sets": ex.get('sets', 3),
        "weight": ctx.workout_current_weight,
        "per_side": False,
        "form_cue": "Last set complete. Enter reps.",
        "is_paused": False,
        "setup_text": '',  # AMRAP done - no setup needed
        "next_exercise": next_ex_info.get('name') if next_ex_info else '',
        "can_skip": _can_skip(next_ex_info.get('name') if next_ex_info else ''),
    }


def get_timer_status(ctx: TimerContext) -> dict | None:
    """Get current timer status by trying each builder in priority order.

    This is the main entry point - tries each builder until one returns
    a valid result.

    Priority order:
    1. Routine timer (active/paused)
    2. Routine auto-advance transition
    3. Routine pending
    4. Workout timed exercise
    5. Workout rest
    6. Workout pending
    7. Workout set active
    8. Workout awaiting reps

    Returns None if no timer is active.
    """
    # Routine builders (higher priority than workout)
    result = build_routine_timer_dict(ctx)
    if result:
        return result

    result = build_routine_transition_dict(ctx)
    if result:
        return result

    result = build_routine_pending_dict(ctx)
    if result:
        return result

    result = build_routine_complete_dict(ctx)
    if result:
        return result

    # Workout builders
    result = build_workout_timer_dict(ctx)
    if result:
        return result

    result = build_workout_rest_dict(ctx)
    if result:
        return result

    result = build_workout_pending_dict(ctx)
    if result:
        return result

    result = build_workout_set_active_dict(ctx)
    if result:
        return result

    result = build_workout_awaiting_reps_dict(ctx)
    if result:
        return result

    result = build_workout_complete_dict(ctx)
    if result:
        return result

    return None
