"""
Garmin Connect Service

Integration with Garmin Connect via garth library for syncing:
- Sleep data (hours, score, stages)
- HRV status and values
- Resting heart rate
- Body Battery

Authentication:
    1. Set credentials in .env:
       GARMIN_USERNAME=your@email.com
       GARMIN_PASSWORD=your_password

    2. Run one-time auth setup:
       python scripts/garmin_auth_setup.py

    3. Remove GARMIN_PASSWORD from .env after tokens saved

    4. Tokens persist in ~/.garth/ and auto-refresh

Usage:
    from atlas.health.garmin import GarminService, is_garmin_auth_valid

    # Quick auth check (for 5am cron fail-fast)
    if not is_garmin_auth_valid():
        logger.critical("GARMIN AUTH EXPIRED")
        sys.exit(1)

    # Sync data
    service = GarminService()
    metrics = await service.sync_today()
    if metrics:
        print(f"Sleep: {metrics.sleep_hours}h, HRV: {metrics.hrv_status}")
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Timezone for Australia/Sydney (AEST/AEDT)
AEST = ZoneInfo("Australia/Sydney")

# Session token storage location (managed by garth)
GARTH_HOME = Path.home() / ".garth"


# =============================================================================
# Custom Exceptions
# =============================================================================


class GarminAPIError(Exception):
    """Raised when Garmin API request fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class GarminAuthError(GarminAPIError):
    """Raised when authentication fails or session is invalid."""

    pass


class GarminRateLimitError(GarminAPIError):
    """Raised when rate limited by Garmin."""

    pass


class GarminNoDataError(GarminAPIError):
    """Raised when no data available (e.g., watch not synced yet)."""

    pass


# =============================================================================
# Health Check Function
# =============================================================================


def is_garmin_auth_valid() -> bool:
    """
    Quick check if Garmin session is valid.

    Use this for fail-fast in pipelines (e.g., 5am cron).
    Returns True if session exists and can make API calls.
    """
    try:
        import garth

        if not GARTH_HOME.exists():
            return False

        garth.resume(GARTH_HOME)
        # Lightweight API call to verify session
        garth.connectapi("/userprofile-service/socialProfile")
        return True
    except Exception as e:
        logger.debug(f"Garmin auth check failed: {e}")
        return False


# =============================================================================
# Retry Decorator
# =============================================================================


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 5.0,
    exceptions: tuple = (GarminAPIError, GarminRateLimitError),
):
    """
    Decorator for retrying failed API calls with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubled each retry)
        exceptions: Tuple of exception types to catch and retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
            raise last_error  # Should never reach here

        return wrapper

    return decorator


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class GarminMetrics:
    """Synced metrics from Garmin Connect."""

    date: date
    # Sync status
    sync_status: str = "success"  # success, no_data, partial, error

    # Sleep
    sleep_hours: Optional[float] = None
    sleep_score: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    awake_minutes: Optional[int] = None

    # Heart
    resting_hr: Optional[int] = None
    hrv_status: Optional[str] = None  # "BALANCED", "UNBALANCED", "LOW"
    hrv_avg: Optional[int] = None
    hrv_morning: Optional[int] = None

    # Recovery
    body_battery: Optional[int] = None
    body_battery_charged: Optional[int] = None
    body_battery_drained: Optional[int] = None
    stress_avg: Optional[int] = None

    # Activity
    steps: Optional[int] = None
    active_calories: Optional[int] = None
    distance_meters: Optional[float] = None

    # Missing fields tracking (for logging)
    missing_fields: list = field(default_factory=list)


# =============================================================================
# Garmin Service
# =============================================================================


class GarminService:
    """
    Garmin Connect API client using garth library.

    Uses session tokens from ~/.garth/ for authentication.
    Run scripts/garmin_auth_setup.py for initial setup.
    """

    def __init__(self):
        """Initialize Garmin service and load session if available."""
        self._session_valid = False
        self._load_session()

    def _load_session(self) -> bool:
        """
        Load existing garth session from disk.

        Returns True if session loaded and validated successfully.
        """
        try:
            import garth

            if not GARTH_HOME.exists():
                logger.debug("No Garmin session found at ~/.garth/")
                return False

            garth.resume(GARTH_HOME)
            self._session_valid = True
            logger.debug("Garmin session loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to load Garmin session: {e}")
            self._session_valid = False
            return False

    def is_configured(self) -> bool:
        """Check if Garmin session tokens exist."""
        return (GARTH_HOME / "oauth1_token.json").exists()

    def has_valid_token(self) -> bool:
        """Check if we have a valid session (garth auto-refreshes)."""
        if not self.is_configured():
            return False
        return self._session_valid

    async def _get_display_name(self) -> Optional[str]:
        """
        Get user's display name for API endpoints that require it.

        Returns the display name/ID used by Garmin Connect API.
        """
        try:
            profile = await self._fetch_endpoint("/userprofile-service/socialProfile")
            if profile and isinstance(profile, dict):
                return profile.get("displayName")
            return None
        except Exception as e:
            logger.warning(f"Failed to get display name: {e}")
            return None

    # =========================================================================
    # Response Parsers
    # =========================================================================

    def _convert_gmt_timestamp(self, gmt_timestamp_ms: int) -> datetime:
        """Convert Garmin GMT timestamp (milliseconds) to AEST datetime."""
        return datetime.fromtimestamp(gmt_timestamp_ms / 1000, tz=AEST)

    def _parse_sleep(self, raw: Optional[dict]) -> dict:
        """
        Parse raw Garmin sleep response.

        Handles:
        - Empty response (watch not synced)
        - Partial data (some fields missing)
        - Full data with all metrics
        """
        result = {}
        missing = []

        if not raw:
            logger.warning("Sleep API returned empty response")
            return {"sync_status": "no_data"}

        daily = raw.get("dailySleepDTO")
        if not daily:
            logger.warning(
                "No dailySleepDTO in response - watch may not have synced"
            )
            return {"sync_status": "no_data"}

        # Sleep duration
        total_seconds = daily.get("sleepTimeSeconds")
        if total_seconds:
            result["sleep_hours"] = round(total_seconds / 3600, 2)
        else:
            missing.append("sleep_hours")

        # Sleep stages (convert seconds to minutes)
        for stage, key in [
            ("deep_sleep_minutes", "deepSleepSeconds"),
            ("rem_sleep_minutes", "remSleepSeconds"),
            ("light_sleep_minutes", "lightSleepSeconds"),
            ("awake_minutes", "awakeSleepSeconds"),
        ]:
            value = daily.get(key)
            if value is not None:
                result[stage] = value // 60
            else:
                missing.append(stage)

        # Sleep score (nested structure)
        scores = daily.get("sleepScores", {})
        overall = scores.get("overall", {})
        if "value" in overall:
            result["sleep_score"] = overall["value"]
        else:
            missing.append("sleep_score")

        # Heart metrics from sleep data (check both daily DTO and root level)
        resting_hr = daily.get("restingHeartRate") or raw.get("restingHeartRate")
        if resting_hr:
            result["resting_hr"] = resting_hr
        else:
            missing.append("resting_hr")

        # HRV from dailySleepDTO or root level (dailySleepData endpoint has it at root)
        hrv_avg = daily.get("avgOvernightHrv") or raw.get("avgOvernightHrv")
        if hrv_avg:
            result["hrv_avg"] = int(hrv_avg)
        else:
            missing.append("hrv_avg")

        # HRV status from root level (dailySleepData endpoint)
        if raw.get("hrvStatus"):
            result["hrv_status"] = raw["hrvStatus"]

        # Body battery change from root level (dailySleepData endpoint)
        if raw.get("bodyBatteryChange") is not None:
            result["body_battery_change"] = raw["bodyBatteryChange"]

        result["missing"] = missing
        return result

    def _parse_hrv(self, raw: Optional[dict]) -> dict:
        """Parse raw Garmin HRV response."""
        result = {}
        missing = []

        if not raw:
            return {"sync_status": "no_data"}

        # HRV data is nested in hrvSummary
        summary = raw.get("hrvSummary", raw)  # Fallback to raw if no summary

        # HRV status (BALANCED, UNBALANCED, LOW, NONE)
        if "status" in summary:
            result["hrv_status"] = summary["status"]
        elif "hrvStatus" in raw:
            result["hrv_status"] = raw["hrvStatus"]
        else:
            missing.append("hrv_status")

        # Last night average HRV
        if "lastNightAvg" in summary and summary["lastNightAvg"]:
            result["hrv_avg"] = summary["lastNightAvg"]
        elif "hrvAvg" in raw:
            result["hrv_avg"] = raw["hrvAvg"]
        else:
            missing.append("hrv_avg")

        # Morning reading (5-min high during sleep)
        if "lastNight5MinHigh" in summary and summary["lastNight5MinHigh"]:
            result["hrv_morning"] = summary["lastNight5MinHigh"]
        elif "hrvValueMorning" in raw:
            result["hrv_morning"] = raw["hrvValueMorning"]
        else:
            missing.append("hrv_morning")

        # Weekly average baseline
        if "weeklyAvg" in summary and summary["weeklyAvg"]:
            result["hrv_weekly_avg"] = summary["weeklyAvg"]

        result["missing"] = missing
        return result

    def _parse_body_battery(self, raw: Optional[dict]) -> dict:
        """Parse raw Garmin body battery response."""
        result = {}
        missing = []

        if not raw:
            return {"sync_status": "no_data"}

        # Current level (most recent reading)
        if "charged" in raw:
            result["body_battery"] = raw["charged"]
            result["body_battery_charged"] = raw["charged"]
        else:
            missing.append("body_battery")

        if "drained" in raw:
            result["body_battery_drained"] = raw["drained"]
        else:
            missing.append("body_battery_drained")

        if "averageStressLevel" in raw:
            result["stress_avg"] = raw["averageStressLevel"]
        else:
            missing.append("stress_avg")

        result["missing"] = missing
        return result

    def _parse_stress_for_body_battery(self, raw: Optional[dict]) -> dict:
        """
        Parse stress response for body battery and stress data.

        The dailyStress endpoint returns avg/max stress and body battery
        readings in bodyBatteryValuesArray format: [timestamp, status, level, version]
        """
        result = {}
        missing = []

        if not raw:
            return {"sync_status": "no_data"}

        # Stress values
        if "avgStressLevel" in raw:
            result["stress_avg"] = raw["avgStressLevel"]
        else:
            missing.append("stress_avg")

        # Body battery from array (most recent value at end of array)
        battery_array = raw.get("bodyBatteryValuesArray", [])
        if battery_array:
            # Each entry is [timestamp, status, bodyBatteryLevel, version]
            latest = battery_array[-1]  # Most recent reading
            if len(latest) >= 3:
                result["body_battery"] = latest[2]  # bodyBatteryLevel

            # Find high (max) and low (min) for the day
            levels = [entry[2] for entry in battery_array if len(entry) >= 3]
            if levels:
                result["body_battery_charged"] = max(levels)
                result["body_battery_drained"] = min(levels)
        else:
            missing.append("body_battery")

        result["missing"] = missing
        return result

    # =========================================================================
    # API Methods
    # =========================================================================

    async def _fetch_endpoint(self, endpoint: str) -> Optional[dict]:
        """
        Fetch data from Garmin API endpoint.

        Uses direct HTTP requests to connectapi.garmin.com with OAuth2 token.
        This is more reliable than garth.connectapi() which can return empty.
        """
        import garth
        import requests

        try:
            # Get OAuth2 token from garth
            token = garth.client.oauth2_token.access_token
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
            }

            # Build full URL
            url = f'https://connectapi.garmin.com{endpoint}'

            # Make request in thread pool
            def do_request():
                resp = requests.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                return resp.json() if resp.text else None

            return await asyncio.to_thread(do_request)

        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                if e.response.status_code == 429:
                    raise GarminRateLimitError("Rate limited by Garmin API")
                elif e.response.status_code in (401, 403):
                    raise GarminAuthError(f"Authentication failed: {e}")
                elif e.response.status_code == 404:
                    logger.debug(f"Endpoint not found: {endpoint}")
                    return None
            raise GarminAPIError(f"API request failed: {e}")
        except Exception as e:
            raise GarminAPIError(f"Unexpected error: {e}")

    @retry_with_backoff(max_retries=3, base_delay=5.0)
    async def sync_today(self) -> Optional[GarminMetrics]:
        """
        Sync today's metrics from Garmin Connect.

        Fetches sleep, HRV, and body battery data, combining into
        a single GarminMetrics object.

        Returns:
            GarminMetrics with today's data, or None on failure
        """
        if not self.is_configured():
            logger.warning(
                "Garmin not configured. Run: python scripts/garmin_auth_setup.py"
            )
            return None

        if not self._session_valid:
            if not self._load_session():
                logger.error(
                    "No valid Garmin session. Run: python scripts/garmin_auth_setup.py"
                )
                return None

        today = date.today()

        # Sleep data is from previous night - if before noon, use yesterday's date
        now = datetime.now(AEST)
        sleep_date = today - timedelta(days=1) if now.hour < 12 else today

        logger.info(
            "Garmin sync started",
            extra={"date": today.isoformat(), "sleep_date": sleep_date.isoformat()},
        )

        try:
            # Get display name for wellness endpoint (required for dailySleepData)
            display_name = await self._get_display_name()
            if not display_name:
                logger.warning("Could not get display name for sleep API")

            # Fetch all endpoints - using connectapi.garmin.com directly
            # Use dailySleepData endpoint (works with new accounts, sleep-service doesn't)
            if display_name:
                sleep_raw = await self._fetch_endpoint(
                    f"/wellness-service/wellness/dailySleepData/{display_name}"
                    f"?date={sleep_date.isoformat()}&nonSleepBufferMinutes=60"
                )
            else:
                # Fallback to old endpoint (likely to return empty)
                sleep_raw = await self._fetch_endpoint(
                    f"/sleep-service/sleep/{sleep_date.isoformat()}"
                )
            hrv_raw = await self._fetch_endpoint(
                f"/hrv-service/hrv/{today.isoformat()}"
            )
            # Stress endpoint includes some body battery data
            stress_raw = await self._fetch_endpoint(
                f"/wellness-service/wellness/dailyStress/{today.isoformat()}"
            )

            # Parse responses
            sleep = self._parse_sleep(sleep_raw)
            hrv = self._parse_hrv(hrv_raw)
            battery = self._parse_stress_for_body_battery(stress_raw)

            # Determine overall sync status
            all_no_data = all(
                d.get("sync_status") == "no_data" for d in [sleep, hrv, battery]
            )
            any_no_data = any(
                d.get("sync_status") == "no_data" for d in [sleep, hrv, battery]
            )

            if all_no_data:
                sync_status = "no_data"
                logger.warning(
                    "No Garmin data available - watch may not have synced yet"
                )
            elif any_no_data:
                sync_status = "partial"
            else:
                sync_status = "success"

            # Collect all missing fields
            all_missing = (
                sleep.get("missing", [])
                + hrv.get("missing", [])
                + battery.get("missing", [])
            )

            if all_missing:
                logger.warning(
                    "Partial data returned",
                    extra={"missing_fields": all_missing},
                )

            # Build metrics object
            # Prefer data from sleep endpoint (dailySleepData has more complete data)
            metrics = GarminMetrics(
                date=today,
                sync_status=sync_status,
                # Sleep
                sleep_hours=sleep.get("sleep_hours"),
                sleep_score=sleep.get("sleep_score"),
                deep_sleep_minutes=sleep.get("deep_sleep_minutes"),
                rem_sleep_minutes=sleep.get("rem_sleep_minutes"),
                light_sleep_minutes=sleep.get("light_sleep_minutes"),
                awake_minutes=sleep.get("awake_minutes"),
                # Heart (prefer sleep endpoint, fallback to hrv endpoint)
                resting_hr=sleep.get("resting_hr"),
                hrv_status=sleep.get("hrv_status") or hrv.get("hrv_status"),
                hrv_avg=sleep.get("hrv_avg") or hrv.get("hrv_avg"),
                hrv_morning=hrv.get("hrv_morning"),
                # Recovery
                body_battery=battery.get("body_battery"),
                body_battery_charged=battery.get("body_battery_charged"),
                body_battery_drained=battery.get("body_battery_drained"),
                stress_avg=battery.get("stress_avg"),
                # Tracking
                missing_fields=all_missing,
            )

            logger.info(
                "Garmin sync completed",
                extra={
                    "status": sync_status,
                    "sleep_hours": metrics.sleep_hours,
                    "hrv_status": metrics.hrv_status,
                },
            )

            return metrics

        except GarminAuthError as e:
            logger.critical(
                "GARMIN AUTH EXPIRED - run: python scripts/garmin_auth_setup.py"
            )
            raise
        except GarminRateLimitError:
            logger.error("Rate limited by Garmin - try again later")
            raise
        except GarminAPIError as e:
            logger.error(f"Garmin sync failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Garmin sync: {e}")
            return None

    async def sync_with_alert(self) -> Optional[GarminMetrics]:
        """
        Sync with auth failure alerting.

        Use this in pipelines where you want fail-fast behavior
        with explicit auth failure logging.
        """
        if not is_garmin_auth_valid():
            logger.critical(
                "GARMIN AUTH EXPIRED - re-authentication required. "
                "Run: python scripts/garmin_auth_setup.py"
            )
            # Future: trigger push notification / voice alert
            return None
        return await self.sync_today()

    async def sync_range(
        self, start: date, end: date
    ) -> list[GarminMetrics]:
        """
        Sync metrics for a date range.

        Args:
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            List of GarminMetrics for each day
        """
        results = []
        current = start
        while current <= end:
            # TODO: Implement per-date sync
            # For now, this is a placeholder
            logger.warning("Range sync not yet fully implemented")
            current += timedelta(days=1)
        return results

    async def get_activities(self, days: int = 7) -> list[dict]:
        """
        Get recent activities (runs, walks, etc.).

        Args:
            days: Number of days to look back

        Returns:
            List of activity dictionaries
        """
        if not self._session_valid:
            logger.warning("No valid Garmin session for activities")
            return []

        try:
            raw = await self._fetch_endpoint(
                f"/activitylist-service/activities/search/activities?limit={days * 3}"
            )
            return raw if isinstance(raw, list) else []
        except Exception as e:
            logger.error(f"Failed to fetch activities: {e}")
            return []

    def get_cached_today(self) -> Optional[GarminMetrics]:
        """
        Get cached metrics for today (non-blocking).

        Returns cached data without API call, or None if not cached.
        TODO: Implement caching layer
        """
        return None

    # =========================================================================
    # Activity Sync (for workout HR data)
    # =========================================================================

    async def get_latest_activity(self, max_age_hours: int = 4) -> Optional[dict]:
        """
        Get most recent activity with HR data.

        Args:
            max_age_hours: Only return activity if started within this many hours

        Returns:
            Activity dict or None if no recent activity
        """
        activities = await self.get_activities(days=1)
        if not activities:
            return None

        # Get most recent (first in list)
        latest = activities[0]

        # Check age - use AEST-aware datetime for correct comparison
        start_time_str = latest.get("startTimeLocal")
        if start_time_str and max_age_hours > 0:
            try:
                # Parse ISO format: "2024-01-15 10:30:00" (local time from Garmin)
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                # Make timezone-aware (Garmin returns local time = AEST for this user)
                start_time = start_time.replace(tzinfo=AEST)
                now = datetime.now(AEST)
                age_hours = (now - start_time).total_seconds() / 3600
                if age_hours > max_age_hours:
                    logger.debug(f"Latest activity too old: {age_hours:.1f}h > {max_age_hours}h")
                    return None
            except Exception as e:
                logger.warning(f"Could not parse activity time '{start_time_str}': {e}")
                # Don't return activity without age validation - could be stale
                return None

        return latest

    def get_activity_hr_summary(self, activity: dict) -> dict:
        """
        Extract HR metrics from activity.

        Args:
            activity: Activity dict from get_activities()

        Returns:
            dict with avg_hr, max_hr, duration_min, calories, activity_type
        """
        if not activity:
            return {}

        # Extract activity type
        activity_type = activity.get("activityType", {})
        type_key = activity_type.get("typeKey", "unknown") if isinstance(activity_type, dict) else "unknown"

        # Duration is in seconds
        duration_seconds = activity.get("duration", 0)
        duration_min = int(duration_seconds / 60) if duration_seconds else 0

        return {
            "garmin_activity_id": activity.get("activityId"),
            "activity_type": type_key,
            "avg_hr": activity.get("averageHR"),
            "max_hr": activity.get("maxHR"),
            "duration_min": duration_min,
            "calories": activity.get("calories"),
            "distance_m": activity.get("distance"),
            "start_time": activity.get("startTimeLocal"),
            "activity_name": activity.get("activityName", ""),
        }

    async def sync_latest_activity(self) -> Optional[dict]:
        """
        Convenience method: get latest activity and extract HR summary.

        Returns:
            HR summary dict or None
        """
        activity = await self.get_latest_activity()
        if activity:
            return self.get_activity_hr_summary(activity)
        return None


# =============================================================================
# CLI Support
# =============================================================================


def print_setup_instructions() -> None:
    """Print Garmin setup instructions."""
    print(
        """
Garmin Connect Setup (using garth library)
===========================================

Prerequisites:
  1. Garmin Forerunner 165 watch syncing to Garmin Connect app
  2. Garmin Connect account credentials

Steps:
  1. Add credentials to .env:
     GARMIN_USERNAME="your@email.com"
     GARMIN_PASSWORD="your_password"

  2. Run one-time authentication:
     python scripts/garmin_auth_setup.py

  3. Remove GARMIN_PASSWORD from .env after success
     (tokens persist in ~/.garth/)

  4. Test sync:
     python -m atlas.health.cli garmin sync

Troubleshooting:
  - "Auth expired": Re-run scripts/garmin_auth_setup.py
  - "No data": Ensure watch has synced to Garmin Connect app
  - "Rate limited": Wait 30 min before retrying
"""
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Garmin Connect integration")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    parser.add_argument(
        "--status", action="store_true", help="Check configuration status"
    )
    parser.add_argument("--sync", action="store_true", help="Sync today's data")
    parser.add_argument(
        "--verify", action="store_true", help="Verify auth is valid"
    )
    args = parser.parse_args()

    service = GarminService()

    if args.status:
        print(f"Configured: {service.is_configured()}")
        print(f"Session valid: {service.has_valid_token()}")
        if not service.is_configured():
            print("\nRun: python scripts/garmin_auth_setup.py")
    elif args.verify:
        valid = is_garmin_auth_valid()
        print(f"Auth valid: {valid}")
        exit(0 if valid else 1)
    elif args.sync:
        if not service.is_configured():
            print("Not configured. Run: python scripts/garmin_auth_setup.py")
            exit(1)

        result = asyncio.run(service.sync_today())
        if result:
            print(f"Status: {result.sync_status}")
            print(f"Sleep: {result.sleep_hours}h (score: {result.sleep_score})")
            print(f"HRV: {result.hrv_status} (avg: {result.hrv_avg})")
            print(f"RHR: {result.resting_hr} bpm")
            print(f"Body Battery: {result.body_battery}%")
            if result.missing_fields:
                print(f"Missing: {', '.join(result.missing_fields)}")
        else:
            print("Sync failed. Check logs for details.")
            exit(1)
    else:
        print_setup_instructions()
