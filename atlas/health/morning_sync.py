"""
Morning Sync - Cached Health Status for Voice Pipeline

Runs at 5am via cron to cache Garmin + Traffic Light status.
Voice queries read from cache (0 tokens) instead of syncing live.

Usage:
    # Cron job (5am daily)
    python -m atlas.health.morning_sync

    # Force fresh sync
    python -m atlas.health.morning_sync --force

    # Test mode (print, don't cache)
    python -m atlas.health.morning_sync --test

    # Get cached status (for voice pipeline)
    from atlas.health.morning_sync import get_morning_status
    status = get_morning_status()  # Returns cached or syncs fresh if stale
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from atlas.health.service import HealthService
from atlas.health.garmin import is_garmin_auth_valid

logger = logging.getLogger(__name__)

# Cache location
CACHE_DIR = Path.home() / ".atlas"
CACHE_FILE = CACHE_DIR / "morning_status.json"
CACHE_MAX_AGE_HOURS = 4


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def save_morning_status(status: dict) -> None:
    """Save morning status to cache file."""
    _ensure_cache_dir()
    status["cached_at"] = datetime.now().isoformat()
    with open(CACHE_FILE, "w") as f:
        json.dump(status, f, indent=2)
    logger.info(f"Cached morning status to {CACHE_FILE}")

    # Award Recovery XP based on Garmin metrics (non-blocking)
    _award_recovery_xp(status)


def _award_recovery_xp(status: dict) -> None:
    """Award Recovery XP based on Garmin metrics (non-blocking)."""
    try:
        from atlas.gamification.xp_service import award_xp_safe_async, XP_TABLE

        # Check sleep score >= 80
        sleep_score = status.get("garmin", {}).get("sleep_score")
        if sleep_score and sleep_score >= 80:
            xp = XP_TABLE.get("sleep_good", 60)
            award_xp_safe_async("recovery", xp, "sleep_good")
            logger.debug(f"Awarded {xp} Recovery XP for good sleep (score={sleep_score})")

        # Check body battery >= 50
        body_battery = status.get("garmin", {}).get("body_battery")
        if body_battery and body_battery >= 50:
            xp = XP_TABLE.get("body_battery_good", 30)
            award_xp_safe_async("recovery", xp, "body_battery_good")
            logger.debug(f"Awarded {xp} Recovery XP for body battery (={body_battery})")

    except Exception as e:
        # XP failure should never break morning sync
        logger.debug(f"Recovery XP award skipped: {e}")


def load_cached_status() -> Optional[dict]:
    """Load morning status from cache file."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def is_cache_stale(status: dict, max_age_hours: float = CACHE_MAX_AGE_HOURS) -> bool:
    """Check if cached status is too old."""
    cached_at = status.get("cached_at")
    if not cached_at:
        return True
    try:
        cached_time = datetime.fromisoformat(cached_at)
        age = datetime.now() - cached_time
        return age > timedelta(hours=max_age_hours)
    except ValueError:
        return True


def get_morning_status(force_sync: bool = False) -> dict:
    """
    Get morning status, syncing fresh if cache is stale or missing.

    This is the main entry point for the voice pipeline.
    Zero tokens if cache is fresh, ~0 tokens if sync needed (no LLM).

    Args:
        force_sync: Force fresh sync even if cache is valid

    Returns:
        Morning status dict with traffic_light, workout, metrics
    """
    if not force_sync:
        cached = load_cached_status()
        if cached and not is_cache_stale(cached):
            logger.debug("Using cached morning status")
            return cached

    # Sync fresh
    logger.info("Syncing fresh morning status")
    status = asyncio.run(_sync_morning_status())
    save_morning_status(status)
    return status


async def _sync_morning_status() -> dict:
    """Internal sync function."""
    if not is_garmin_auth_valid():
        logger.warning("Garmin auth invalid - using manual mode")

    service = HealthService()
    return await service.morning_sync()


async def run_morning_sync(force: bool = False) -> dict:
    """
    Run morning sync (for cron job).

    Args:
        force: Force sync even if Garmin unavailable

    Returns:
        Morning status dict
    """
    logger.info("Running morning sync...")

    if not is_garmin_auth_valid():
        logger.critical("GARMIN AUTH EXPIRED - run: python scripts/garmin_auth_setup.py")
        if not force:
            return {"error": "garmin_auth_expired"}

    status = await _sync_morning_status()
    save_morning_status(status)

    logger.info(f"Morning sync complete: {status.get('traffic_light', 'UNKNOWN')}")
    return status


async def sync_and_cache_morning_status() -> dict:
    """
    Async convenience function for Voice Bridge startup.

    Syncs Garmin data and caches it. Call this when Voice Bridge starts
    to replace the 5am cron job (better for variable wake times with baby).

    Returns:
        Morning status dict (cached for subsequent voice queries)
    """
    if not is_garmin_auth_valid():
        logger.warning("Garmin auth not valid - using cached or manual mode")
        cached = load_cached_status()
        if cached:
            return cached
        return {"error": "garmin_auth_expired", "traffic_light": "UNKNOWN"}

    status = await _sync_morning_status()
    save_morning_status(status)
    return status


def _tts_friendly_name(name: str) -> str:
    """Convert workout name to TTS-friendly format.

    All-caps words get spelled out by TTS, so convert them to title case.
    Examples:
        "RED DAY Protocol" -> "Red Day Protocol"
        "Zone 2 Cardio" -> "Zone 2 Cardio" (unchanged, already mixed case)
        "STRENGTH A" -> "Strength A"
    """
    words = name.split()
    result = []
    for word in words:
        # If word is all caps and longer than 1 char, convert to title case
        if word.isupper() and len(word) > 1:
            result.append(word.title())
        else:
            result.append(word)
    return " ".join(result)


def format_status_voice(status: dict) -> str:
    """
    Format status for voice output (Lethal Gentleman persona).

    Examples:
        "Green. 7.2 hours. Your body is ready. Strength B today - shoulder focus."
        "Yellow. 5.8 hours. Adequate rest. Zone 2 cardio - reduce intensity 15%."
        "Red. 4.5 hours. Recovery mode. Walk and NSDR only."
        "Yellow. Battery 32. HRV 56. Active Mobility. Move and restore."
    """
    # Use title case for TTS - all-caps gets spelled out letter by letter
    light_raw = status.get("traffic_light", "UNKNOWN").upper()
    light_voice = light_raw.title()  # "RED" -> "Red" for TTS
    metrics = status.get("metrics", {})
    sleep = metrics.get("sleep_hours")
    body_battery = metrics.get("body_battery")
    hrv_avg = metrics.get("hrv_avg")
    workout = status.get("workout", "Rest")
    reason = status.get("traffic_light_reason", "")
    is_red_override = status.get("is_red_override", False)

    # Build response parts
    parts = [f"{light_voice}."]

    # Report best available metrics
    if sleep:
        parts.append(f"{sleep:.1f} hours.")
    elif body_battery:
        parts.append(f"Battery {body_battery}.")
        if hrv_avg:
            parts.append(f"HRV {hrv_avg}.")

    # Reason based on traffic light (use raw for comparisons)
    if light_raw == "GREEN":
        parts.append("Your body is ready.")
    elif light_raw == "YELLOW":
        if sleep:
            parts.append("Adequate rest.")
        else:
            parts.append("Proceed with caution.")
    elif light_raw == "RED":
        parts.append("Recovery mode.")
    else:
        # Handle insufficient data gracefully
        if "insufficient" in reason.lower():
            parts.append("Data incomplete. Garmin may not have synced.")
        else:
            parts.append(reason or "Status unknown.")

    # Workout
    if is_red_override:
        parts.append("Walk and NSDR only.")
    elif workout:
        # Shorten long workout names for voice
        short_name = workout
        if "(" in workout:
            short_name = workout.split("(")[0].strip()
        # Convert all-caps words to title case for TTS
        short_name = _tts_friendly_name(short_name)

        # Add context based on workout type
        workout_lower = workout.lower()
        if "shoulder" in workout_lower:
            parts.append(f"{short_name} - shoulder focus.")
        elif "zone 2" in workout_lower or "zone2" in workout_lower:
            if light_raw == "YELLOW":
                parts.append(f"{short_name} - reduce intensity 15%.")
            else:
                parts.append(f"{short_name} today.")
        elif "vo2" in workout_lower:
            if light_raw == "YELLOW":
                parts.append(f"{short_name} - reduce intervals if needed.")
            else:
                parts.append(f"{short_name}. Push your limits.")
        elif "mobility" in workout_lower:
            parts.append(f"{short_name}. Move and restore.")
        elif "recovery" in workout_lower:
            parts.append("Rest day. The gains happen in recovery.")
        else:
            parts.append(f"{short_name} today.")

    return " ".join(parts)


def format_briefing_voice(status: dict) -> str:
    """
    Format detailed morning briefing for voice (Lethal Gentleman persona).

    More comprehensive than format_status_voice - includes all available metrics.

    Example:
        "Morning briefing. Yellow status. Body battery 32, started at 100.
         HRV 56, within normal range. Sleep data unavailable.
         Today's workout: Active Mobility. Move and restore."
    """
    # Use title case for TTS - all-caps gets spelled out letter by letter
    light_raw = status.get("traffic_light", "UNKNOWN").upper()
    light_voice = light_raw.title()  # "RED" -> "Red" for TTS
    metrics = status.get("metrics", {})
    sleep = metrics.get("sleep_hours")
    body_battery = metrics.get("body_battery")
    hrv_avg = metrics.get("hrv_avg")
    hrv_status = metrics.get("hrv_status")
    stress_avg = metrics.get("stress_avg")
    workout = status.get("workout", "Rest")
    reason = status.get("traffic_light_reason", "")

    parts = ["Morning briefing."]

    # Traffic light with reason
    parts.append(f"{light_voice} status.")
    if reason and "insufficient" not in reason.lower():
        parts.append(reason + ".")

    # Body battery
    if body_battery is not None:
        if body_battery >= 70:
            parts.append(f"Body battery {body_battery}. Well charged.")
        elif body_battery >= 40:
            parts.append(f"Body battery {body_battery}. Moderate reserves.")
        else:
            parts.append(f"Body battery {body_battery}. Running low.")

    # HRV
    if hrv_avg:
        if hrv_status and hrv_status != "NONE":
            parts.append(f"HRV {hrv_avg}, {hrv_status.lower()}.")
        else:
            parts.append(f"HRV {hrv_avg}. Watch still calibrating baseline.")

    # Sleep
    if sleep:
        if sleep >= 7:
            parts.append(f"Sleep {sleep:.1f} hours. Solid recovery.")
        elif sleep >= 6:
            parts.append(f"Sleep {sleep:.1f} hours. Adequate.")
        else:
            parts.append(f"Sleep {sleep:.1f} hours. Insufficient.")
    else:
        parts.append("Sleep data unavailable from Garmin.")

    # Stress
    if stress_avg:
        if stress_avg <= 30:
            parts.append(f"Stress low at {stress_avg}.")
        elif stress_avg <= 50:
            parts.append(f"Stress moderate at {stress_avg}.")
        else:
            parts.append(f"Stress elevated at {stress_avg}.")

    # Workout
    if workout:
        short_name = workout.split("(")[0].strip() if "(" in workout else workout
        # Convert all-caps words to title case for TTS (e.g., "RED DAY" -> "Red Day")
        short_name = _tts_friendly_name(short_name)
        parts.append(f"Today's workout: {short_name}.")

    return " ".join(parts)


def print_status(status: dict) -> None:
    """Print status in human-readable format."""
    print("\n" + "=" * 50)
    print("ATLAS MORNING STATUS")
    print("=" * 50)

    light = status.get("traffic_light", "UNKNOWN")
    print(f"\nTraffic Light: {light}")
    print(f"Reason: {status.get('traffic_light_reason', 'N/A')}")

    metrics = status.get("metrics", {})
    print(f"\nMetrics:")
    print(f"  Sleep: {metrics.get('sleep_hours', 'N/A')} hours")
    print(f"  HRV Status: {metrics.get('hrv_status', 'N/A')}")
    print(f"  HRV Avg: {metrics.get('hrv_avg', 'N/A')}")
    print(f"  RHR: {metrics.get('resting_hr', 'N/A')} bpm")
    print(f"  Body Battery: {metrics.get('body_battery', 'N/A')}")
    print(f"  Stress Avg: {metrics.get('stress_avg', 'N/A')}")

    print(f"\nWorkout: {status.get('workout', 'None')}")
    print(f"Garmin Synced: {status.get('garmin_synced', False)}")

    print(f"\nCached at: {status.get('cached_at', 'N/A')}")

    print("\n" + "-" * 50)
    print("VOICE OUTPUT:")
    print(format_status_voice(status))
    print("=" * 50 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ATLAS Morning Sync - Cache health status for voice pipeline"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: print status without caching"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force fresh sync even if cache is valid"
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Print voice-formatted output only"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    if args.test:
        # Test mode: sync and print, don't cache
        status = asyncio.run(_sync_morning_status())
        if args.voice:
            print(format_status_voice(status))
        else:
            print_status(status)
    else:
        # Normal mode: sync and cache
        status = asyncio.run(run_morning_sync(force=args.force))
        if args.voice:
            print(format_status_voice(status))
        else:
            print_status(status)


if __name__ == "__main__":
    main()
