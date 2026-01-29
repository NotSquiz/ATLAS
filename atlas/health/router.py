"""
Traffic Light Workout Router

Routes workout intensity based on recovery metrics (HRV, sleep, RHR).

Based on the Shoulder Rehab Protocol's "Traffic Light Logic":
- GREEN DAY: Sleep > 6.5hrs, HRV "Balanced", RHR < 55bpm -> Full intensity
- YELLOW DAY: Mixed signals -> Moderate intensity
- RED DAY: Sleep < 5.5hrs OR HRV "Unbalanced" OR RHR elevated -> Recovery only

Usage:
    from atlas.health.router import TrafficLightRouter, TrafficLightStatus

    router = TrafficLightRouter()

    # With Garmin metrics
    result = router.evaluate(
        sleep_hours=7.2,
        hrv_status="BALANCED",
        resting_hr=52
    )

    if result.status == TrafficLightStatus.RED:
        print("Zone 2 walk + NSDR only")
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class TrafficLightStatus(Enum):
    """Workout intensity level based on recovery metrics."""
    GREEN = "green"    # Full intensity
    YELLOW = "yellow"  # Moderate intensity
    RED = "red"        # Recovery only


@dataclass
class TrafficLightResult:
    """Result of traffic light evaluation."""
    status: TrafficLightStatus
    reason: str
    recommendation: str
    sleep_hours: Optional[float] = None
    hrv_status: Optional[str] = None
    resting_hr: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "reason": self.reason,
            "recommendation": self.recommendation,
            "metrics": {
                "sleep_hours": self.sleep_hours,
                "hrv_status": self.hrv_status,
                "resting_hr": self.resting_hr,
            }
        }


class TrafficLightRouter:
    """
    Routes workout intensity based on Garmin recovery metrics.

    Thresholds from Shoulder Rehab Protocol:

    GREEN DAY Criteria (all must pass):
    - Sleep > 6.5 hours
    - HRV "BALANCED", "GOOD", or "EXCELLENT"
    - RHR < 55 bpm (or < baseline + 5bpm)

    RED DAY Criteria (any one triggers):
    - Sleep < 5.5 hours
    - HRV "UNBALANCED", "LOW", or "STRAINED"
    - RHR elevated > 5bpm above baseline

    YELLOW DAY:
    - Mixed signals / intermediate state
    """

    # Configurable thresholds
    GREEN_SLEEP_MIN = 6.5
    RED_SLEEP_MAX = 5.5
    GREEN_RHR_MAX = 55
    RHR_ELEVATED_THRESHOLD = 5  # bpm above baseline

    # HRV status categories
    GOOD_HRV = {"BALANCED", "GOOD", "EXCELLENT", "HIGH", "OPTIMAL"}
    BAD_HRV = {"UNBALANCED", "LOW", "STRAINED", "POOR"}

    def __init__(self, rhr_baseline: int = 52):
        """
        Initialize router with RHR baseline.

        Args:
            rhr_baseline: Resting heart rate baseline in bpm.
                          Used to detect elevated RHR on bad recovery days.
        """
        self.rhr_baseline = rhr_baseline

    def evaluate(
        self,
        sleep_hours: Optional[float] = None,
        hrv_status: Optional[str] = None,
        resting_hr: Optional[int] = None,
        body_battery: Optional[int] = None,
    ) -> TrafficLightResult:
        """
        Evaluate recovery metrics and return traffic light status.

        Args:
            sleep_hours: Total sleep duration
            hrv_status: HRV status from Garmin (BALANCED, UNBALANCED, etc.)
            resting_hr: Resting heart rate in bpm
            body_battery: Garmin Body Battery score (0-100)

        Returns:
            TrafficLightResult with status, reason, and recommendation
        """
        # Normalize HRV status
        hrv_normalized = hrv_status.upper() if hrv_status else None

        # Check RED flags first (any one triggers RED)
        red_reasons = []

        if sleep_hours is not None and sleep_hours < self.RED_SLEEP_MAX:
            red_reasons.append(f"Sleep only {sleep_hours:.1f}h (< {self.RED_SLEEP_MAX}h)")

        if hrv_normalized and hrv_normalized in self.BAD_HRV:
            red_reasons.append(f"HRV status: {hrv_status}")

        if resting_hr is not None:
            elevated_threshold = self.rhr_baseline + self.RHR_ELEVATED_THRESHOLD
            if resting_hr > elevated_threshold:
                red_reasons.append(
                    f"RHR elevated: {resting_hr}bpm "
                    f"(baseline: {self.rhr_baseline}, threshold: {elevated_threshold})"
                )

        if body_battery is not None and body_battery < 25:
            red_reasons.append(f"Body Battery critical: {body_battery}%")

        if red_reasons:
            return TrafficLightResult(
                status=TrafficLightStatus.RED,
                reason=" | ".join(red_reasons),
                recommendation="Zone 2 walk (20min) + NSDR (20min). Skip heavy lifting.",
                sleep_hours=sleep_hours,
                hrv_status=hrv_status,
                resting_hr=resting_hr,
            )

        # Check GREEN criteria (all must pass)
        green_checks = []

        if sleep_hours is not None:
            green_checks.append(sleep_hours >= self.GREEN_SLEEP_MIN)

        if hrv_normalized:
            green_checks.append(hrv_normalized in self.GOOD_HRV)

        if resting_hr is not None:
            green_checks.append(resting_hr <= self.GREEN_RHR_MAX)

        if body_battery is not None:
            green_checks.append(body_battery >= 50)

        # If we have checks and all pass, it's GREEN
        if green_checks and all(green_checks):
            return TrafficLightResult(
                status=TrafficLightStatus.GREEN,
                reason="All recovery metrics optimal",
                recommendation="Execute full programmed intensity. Push weights on main lifts.",
                sleep_hours=sleep_hours,
                hrv_status=hrv_status,
                resting_hr=resting_hr,
            )

        # Insufficient data → RED (conservative default)
        if not green_checks:
            return TrafficLightResult(
                status=TrafficLightStatus.RED,
                reason="Insufficient data - defaulting to recovery mode",
                recommendation="Cannot assess recovery. Take it easy today.",
                sleep_hours=sleep_hours,
                hrv_status=hrv_status,
                resting_hr=resting_hr,
            )

        # Check for YELLOW conditions (body battery 25-49)
        yellow_reasons = []
        if body_battery is not None and 25 <= body_battery < 50:
            yellow_reasons.append(f"Body Battery moderate: {body_battery}%")

        # Mixed signals or body battery 25-49 → YELLOW
        reason = " | ".join(yellow_reasons) if yellow_reasons else "Mixed recovery signals"
        return TrafficLightResult(
            status=TrafficLightStatus.YELLOW,
            reason=reason,
            recommendation="Moderate intensity. Listen to your body. Stop if fatigue sets in.",
            sleep_hours=sleep_hours,
            hrv_status=hrv_status,
            resting_hr=resting_hr,
        )

    def get_day_emoji(self, status: TrafficLightStatus) -> str:
        """Get emoji for traffic light status."""
        return {
            TrafficLightStatus.GREEN: "\U0001F7E2",   # Green circle
            TrafficLightStatus.YELLOW: "\U0001F7E1",  # Yellow circle
            TrafficLightStatus.RED: "\U0001F534",     # Red circle
        }.get(status, "\u2753")  # Question mark fallback


# Convenience function
def evaluate_traffic_light(
    sleep_hours: Optional[float] = None,
    hrv_status: Optional[str] = None,
    resting_hr: Optional[int] = None,
    rhr_baseline: int = 52,
) -> TrafficLightResult:
    """
    Quick evaluation of traffic light status.

    Usage:
        result = evaluate_traffic_light(sleep_hours=7.2, hrv_status="BALANCED")
        print(f"{result.status.value}: {result.recommendation}")
    """
    router = TrafficLightRouter(rhr_baseline=rhr_baseline)
    return router.evaluate(
        sleep_hours=sleep_hours,
        hrv_status=hrv_status,
        resting_hr=resting_hr,
    )
