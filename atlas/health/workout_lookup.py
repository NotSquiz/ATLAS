"""
Workout Lookup Module

Provides workout information based on current day and phase configuration.
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Config paths
ATLAS_ROOT = Path(__file__).parent.parent.parent
PHASE_CONFIG_PATH = Path.home() / ".atlas" / "phase_config.json"
DEFAULT_PHASE_CONFIG = ATLAS_ROOT / "config" / "phases" / "config_phase1_weeks1-12.json"


def get_phase_config() -> Optional[dict]:
    """Load current phase configuration."""
    if PHASE_CONFIG_PATH.exists():
        try:
            with open(PHASE_CONFIG_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load phase config: {e}")
    return None


def get_workout_config() -> Optional[dict]:
    """Load the detailed workout configuration for current phase."""
    phase_config = get_phase_config()

    if phase_config:
        config_file = phase_config.get("current_phase", {}).get("config_file")
        if config_file:
            config_path = ATLAS_ROOT / config_file
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load workout config: {e}")

    # Fall back to default
    if DEFAULT_PHASE_CONFIG.exists():
        try:
            with open(DEFAULT_PHASE_CONFIG) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load default config: {e}")

    return None


def get_current_week() -> int:
    """Calculate current week number based on phase start date."""
    phase_config = get_phase_config()

    if not phase_config:
        return 0

    start_str = phase_config.get("current_phase", {}).get("start_date")
    if not start_str:
        return 0

    try:
        start_date = date.fromisoformat(start_str)
    except ValueError:
        return 0

    today = date.today()

    if today < start_date:
        return 0  # Not started yet

    days_elapsed = (today - start_date).days
    week = (days_elapsed // 7) + 1

    # Cap at phase weeks total
    weeks_total = phase_config.get("phase_1_schedule", {}).get("weeks_total", 12)
    return min(week, weeks_total)


def is_deload_week() -> bool:
    """Check if current week is a deload week."""
    phase_config = get_phase_config()
    if not phase_config:
        return False

    current_week = get_current_week()
    deload_weeks = phase_config.get("phase_1_schedule", {}).get("deload_weeks", [4, 8])
    return current_week in deload_weeks


def get_todays_workout() -> Optional[dict]:
    """
    Return today's workout from phase config.

    Returns dict with:
        - type: STRENGTH_A, CARDIO_ZONE2, etc.
        - name: Human readable name
        - duration_minutes: Expected duration
        - exercises: List of main exercises (first 3-4)
        - ice_bath: YES/NO
        - notes: Any special notes
        - is_deload: Whether this is a deload week
    """
    config = get_workout_config()
    if not config:
        return None

    # Get day of week (lowercase)
    day = datetime.now().strftime('%A').lower()

    # Get workout
    schedule = config.get('weekly_schedule', {})
    workout = schedule.get(day)

    if not workout:
        return None

    # Extract key info
    result = {
        "type": workout.get("type", "UNKNOWN"),
        "name": workout.get("name", "Unknown Workout"),
        "duration_minutes": workout.get("duration_minutes", 0),
        "time": workout.get("time", ""),
        "focus": workout.get("focus", ""),
        "ice_bath": workout.get("ice_bath", "NO"),
        "is_deload": is_deload_week(),
        "current_week": get_current_week(),
    }

    # Extract main exercises (first 3-4)
    main_workout = workout.get("main_workout", {})
    exercises = main_workout.get("exercises", [])

    if exercises:
        result["exercises"] = [
            {
                "name": ex.get("name", "Unknown"),
                "sets": ex.get("sets", 3),
                "reps": ex.get("reps", "10"),
                "notes": ex.get("notes", ""),
            }
            for ex in exercises[:4]
        ]
    else:
        result["exercises"] = []

    # Add protocol for cardio
    if "protocol" in workout:
        result["protocol"] = workout["protocol"]

    # Add warmup duration
    warmup = workout.get("warmup", {})
    result["warmup_minutes"] = warmup.get("duration", 0)

    # Cooldown
    cooldown = workout.get("cooldown", {})
    result["cooldown_minutes"] = cooldown.get("duration", 0)

    return result


def format_workout_voice(workout: Optional[dict] = None) -> str:
    """
    Format workout for voice response (Lethal Gentleman style).

    Returns concise, terse response suitable for TTS.
    """
    if workout is None:
        workout = get_todays_workout()

    if not workout:
        return "No workout data available. Check configuration."

    workout_type = workout.get("type", "UNKNOWN")
    name = workout.get("name", "Unknown")
    duration = workout.get("duration_minutes", 0)
    week = workout.get("current_week", 0)

    # Build response
    parts = []

    # Week and phase info
    if week > 0:
        deload = workout.get("is_deload", False)
        if deload:
            parts.append(f"Week {week}. Deload.")
        else:
            parts.append(f"Week {week}.")

    # Workout type and name
    parts.append(f"{name}.")
    parts.append(f"{duration} minutes.")

    # Key exercises (first 3)
    exercises = workout.get("exercises", [])
    if exercises:
        ex_names = [ex["name"] for ex in exercises[:3]]
        parts.append(f"Key movements: {', '.join(ex_names)}.")

    # Ice bath
    if workout.get("ice_bath") == "YES":
        parts.append("Ice bath optional today.")

    return " ".join(parts)


def format_workout_display(workout: Optional[dict] = None) -> str:
    """
    Format workout for CLI display (more detailed).
    """
    if workout is None:
        workout = get_todays_workout()

    if not workout:
        return "No workout data available."

    lines = []

    # Header
    week = workout.get("current_week", 0)
    deload = workout.get("is_deload", False)

    lines.append("")
    lines.append("=" * 60)
    week_str = f"Week {week}" + (" (DELOAD)" if deload else "")
    lines.append(f"  TODAY'S WORKOUT - {week_str}")
    lines.append("=" * 60)
    lines.append("")

    # Type and name
    lines.append(f"  Type: {workout.get('type', 'UNKNOWN')}")
    lines.append(f"  Name: {workout.get('name', 'Unknown')}")
    lines.append(f"  Duration: {workout.get('duration_minutes', 0)} minutes")

    if workout.get("time"):
        lines.append(f"  Scheduled: {workout['time']}")

    if workout.get("focus"):
        lines.append(f"  Focus: {workout['focus']}")

    lines.append("")
    lines.append("-" * 60)

    # Exercises
    exercises = workout.get("exercises", [])
    if exercises:
        lines.append("  MAIN EXERCISES:")
        for ex in exercises:
            name = ex.get("name", "Unknown")
            sets = ex.get("sets", 3)
            reps = ex.get("reps", "10")
            lines.append(f"    - {name}: {sets} x {reps}")
            if ex.get("notes"):
                lines.append(f"      Note: {ex['notes']}")
        lines.append("")

    # Protocol for cardio
    if "protocol" in workout:
        protocol = workout["protocol"]
        lines.append("  PROTOCOL:")
        if isinstance(protocol, dict):
            for key, val in protocol.items():
                if isinstance(val, str):
                    lines.append(f"    {key}: {val}")
        lines.append("")

    # Ice bath
    if workout.get("ice_bath") == "YES":
        lines.append("  Ice bath: YES (optimal day)")
    else:
        lines.append("  Ice bath: NO")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    # Test
    print(f"Current week: {get_current_week()}")
    print(f"Is deload: {is_deload_week()}")
    print()

    workout = get_todays_workout()
    if workout:
        print("Voice format:")
        print(format_workout_voice(workout))
        print()
        print("Display format:")
        print(format_workout_display(workout))
    else:
        print("No workout found for today.")
