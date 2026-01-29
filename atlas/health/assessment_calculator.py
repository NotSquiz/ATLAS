"""
ATLAS Assessment Calculator

Provides calculations for:
- Estimated 1RM from submaximal lifts (Brzycki formula)
- Limb Symmetry Index (LSI%)
- HR recovery calculations
- FMS total scores
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_1rm_brzycki(weight: float, reps: int) -> float:
    """
    Calculate estimated 1RM using Brzycki formula.

    Formula: 1RM = weight / (1.0278 - 0.0278 × reps)

    Accurate for reps 1-10, less accurate above 10.

    Args:
        weight: Weight lifted in kg
        reps: Number of reps performed

    Returns:
        Estimated 1RM in kg
    """
    if reps < 1:
        return weight
    if reps == 1:
        return weight
    if reps > 10:
        logger.warning(f"Brzycki formula less accurate for {reps} reps (>10)")

    estimated_1rm = weight / (1.0278 - 0.0278 * reps)
    return round(estimated_1rm, 1)


def calculate_1rm_epley(weight: float, reps: int) -> float:
    """
    Calculate estimated 1RM using Epley formula.

    Formula: 1RM = weight × (1 + 0.0333 × reps)

    Alternative formula, tends to estimate slightly higher.

    Args:
        weight: Weight lifted in kg
        reps: Number of reps performed

    Returns:
        Estimated 1RM in kg
    """
    if reps < 1:
        return weight
    if reps == 1:
        return weight

    estimated_1rm = weight * (1 + 0.0333 * reps)
    return round(estimated_1rm, 1)


def calculate_lsi(value_involved: float, value_uninvolved: float) -> float:
    """
    Calculate Limb Symmetry Index.

    Formula: LSI = (weaker / stronger) × 100

    Note: Does NOT assume which side is involved/uninvolved.
    Simply calculates weaker as percentage of stronger.

    Args:
        value_involved: Value from involved (injured) limb
        value_uninvolved: Value from uninvolved limb

    Returns:
        LSI percentage (0-100+)
    """
    if value_involved <= 0 or value_uninvolved <= 0:
        logger.warning(f"Invalid values for LSI: {value_involved}, {value_uninvolved}")
        return 0.0

    weaker = min(value_involved, value_uninvolved)
    stronger = max(value_involved, value_uninvolved)

    lsi = (weaker / stronger) * 100
    return round(lsi, 1)


def calculate_lsi_with_comparison(left: float, right: float) -> dict:
    """
    Calculate LSI with detailed comparison.

    Returns:
        dict with:
            - lsi: The LSI percentage
            - weaker_side: 'left' or 'right'
            - difference: Absolute difference
            - symmetrical: True if LSI >= 90%
    """
    if left <= 0 or right <= 0:
        return {
            "lsi": 0.0,
            "weaker_side": "unknown",
            "difference": 0.0,
            "symmetrical": False,
        }

    lsi = calculate_lsi(left, right)
    weaker_side = "left" if left < right else "right" if right < left else "equal"
    difference = abs(left - right)

    return {
        "lsi": lsi,
        "weaker_side": weaker_side,
        "difference": round(difference, 1),
        "symmetrical": lsi >= 90.0,
    }


def calculate_hr_recovery(peak_hr: int, recovery_hr: int) -> int:
    """
    Calculate heart rate recovery.

    A drop of 12+ bpm in first minute is considered normal.
    A drop of 25+ bpm is excellent cardiovascular fitness.

    Args:
        peak_hr: Heart rate immediately after exercise
        recovery_hr: Heart rate after 1 minute of rest

    Returns:
        HR recovery (drop in bpm)
    """
    return peak_hr - recovery_hr


def calculate_hr_recovery_assessment(drop: int) -> str:
    """
    Assess HR recovery quality.

    Args:
        drop: HR drop in bpm

    Returns:
        Assessment string
    """
    if drop < 12:
        return "Below normal. Consider cardiac evaluation if persistent."
    elif drop < 18:
        return "Normal range."
    elif drop < 25:
        return "Good cardiovascular fitness."
    else:
        return "Excellent cardiovascular fitness."


def calculate_fms_total(scores: dict) -> int:
    """
    Calculate total FMS score.

    Standard FMS has 7 tests, each scored 0-3.
    Total possible: 21

    Args:
        scores: Dict of test_id -> score (0-3)

    Returns:
        Total FMS score
    """
    fms_tests = [
        "fms_deep_squat",
        "fms_hurdle_step",
        "fms_inline_lunge",
        "fms_aslr",
        "fms_trunk_stability_pushup",
        "fms_rotary_stability",
        "fms_shoulder_mobility",  # Optional in our protocol
    ]

    total = 0
    for test in fms_tests:
        if test in scores:
            total += scores[test]

    return total


def calculate_body_composition_change(
    current_weight: float,
    baseline_weight: float,
    current_bf: Optional[float] = None,
    baseline_bf: Optional[float] = None,
) -> dict:
    """
    Calculate body composition changes from baseline.

    Args:
        current_weight: Current weight in kg
        baseline_weight: Baseline weight in kg
        current_bf: Current body fat percentage (optional)
        baseline_bf: Baseline body fat percentage (optional)

    Returns:
        dict with weight change, estimated lean mass change, etc.
    """
    weight_change = round(current_weight - baseline_weight, 1)

    result = {
        "weight_change_kg": weight_change,
        "weight_change_pct": round((weight_change / baseline_weight) * 100, 1),
    }

    if current_bf is not None and baseline_bf is not None:
        current_lean = current_weight * (1 - current_bf / 100)
        baseline_lean = baseline_weight * (1 - baseline_bf / 100)
        current_fat = current_weight * (current_bf / 100)
        baseline_fat = baseline_weight * (baseline_bf / 100)

        result["lean_mass_change_kg"] = round(current_lean - baseline_lean, 1)
        result["fat_mass_change_kg"] = round(current_fat - baseline_fat, 1)
        result["bf_change_pct"] = round(current_bf - baseline_bf, 1)

    return result


def format_comparison_voice(
    current: float,
    baseline: Optional[float],
    unit: str = "",
    lower_is_better: bool = False,
) -> str:
    """
    Format a comparison to baseline for voice output.

    Args:
        current: Current value
        baseline: Baseline value (None if first measurement)
        unit: Unit for display
        lower_is_better: If True, decreases are improvements

    Returns:
        Voice-friendly comparison string
    """
    if baseline is None:
        return "First baseline."

    diff = current - baseline

    if abs(diff) < 0.1:
        return "Same as baseline."

    # Format the difference
    if diff == int(diff):
        diff_str = str(int(abs(diff)))
    else:
        diff_str = f"{abs(diff):.1f}"

    # Determine direction and quality
    if diff > 0:
        direction = "up"
        quality = "worse" if lower_is_better else "improvement"
    else:
        direction = "down"
        quality = "improvement" if lower_is_better else "worse"

    # Build response
    unit_str = f" {unit}" if unit and unit not in ["%", "score"] else ""
    return f"{direction.capitalize()} {diff_str}{unit_str} from baseline."


def estimate_session_duration(tests_remaining: int, avg_time_per_test: float = 1.5) -> str:
    """
    Estimate remaining session duration.

    Args:
        tests_remaining: Number of tests left
        avg_time_per_test: Average minutes per test

    Returns:
        Human-friendly duration string
    """
    minutes = int(tests_remaining * avg_time_per_test)

    if minutes < 2:
        return "about a minute"
    elif minutes < 5:
        return "a few minutes"
    elif minutes < 10:
        return f"about {minutes} minutes"
    elif minutes < 20:
        return f"about {(minutes // 5) * 5} minutes"
    else:
        return f"about {minutes} minutes"


# Export main functions
__all__ = [
    "calculate_1rm_brzycki",
    "calculate_1rm_epley",
    "calculate_lsi",
    "calculate_lsi_with_comparison",
    "calculate_hr_recovery",
    "calculate_hr_recovery_assessment",
    "calculate_fms_total",
    "calculate_body_composition_change",
    "format_comparison_voice",
    "estimate_session_duration",
]
