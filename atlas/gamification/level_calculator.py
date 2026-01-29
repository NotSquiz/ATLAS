"""
OSRS-Style Level Calculator

Uses the authentic Old School RuneScape experience point curve.
The formula creates an exponential progression where higher levels
require increasingly more XP.

Level 1: 0 XP
Level 10: ~1,154 XP
Level 25: ~8,740 XP
Level 50: ~101,333 XP
Level 99: ~13,034,431 XP (max)

Usage:
    from atlas.gamification.level_calculator import level_for_xp, xp_for_level

    level = level_for_xp(10000)  # 26
    xp_needed = xp_for_level(50)  # 101,333
"""

from functools import lru_cache
from typing import Tuple

MAX_LEVEL = 99


@lru_cache(maxsize=MAX_LEVEL + 1)
def xp_for_level(level: int) -> int:
    """
    Calculate the total XP required to reach a specific level.

    Uses the authentic OSRS formula:
    XP = sum(floor(L + 300 * 2^(L/7))) / 4 for L from 1 to level-1

    Args:
        level: Target level (1-99)

    Returns:
        Total XP required to reach that level
    """
    if level <= 1:
        return 0
    if level > MAX_LEVEL:
        level = MAX_LEVEL

    total = 0
    for lvl in range(1, level):
        total += int(lvl + 300 * (2 ** (lvl / 7)))

    return total // 4


def level_for_xp(xp: int) -> int:
    """
    Calculate the level for a given amount of XP.

    Args:
        xp: Total experience points

    Returns:
        Current level (1-99)
    """
    if xp < 0:
        return 1

    # Binary search for efficiency
    low, high = 1, MAX_LEVEL
    while low < high:
        mid = (low + high + 1) // 2
        if xp_for_level(mid) <= xp:
            low = mid
        else:
            high = mid - 1

    return low


def xp_to_next_level(current_xp: int) -> int:
    """
    Calculate XP remaining to reach the next level.

    Args:
        current_xp: Current experience points

    Returns:
        XP needed for next level, or 0 if at max level
    """
    current_level = level_for_xp(current_xp)
    if current_level >= MAX_LEVEL:
        return 0

    next_level_xp = xp_for_level(current_level + 1)
    return next_level_xp - current_xp


def progress_to_next_level(current_xp: int) -> Tuple[int, int, float]:
    """
    Calculate progress toward the next level.

    Args:
        current_xp: Current experience points

    Returns:
        Tuple of (xp_in_current_level, xp_needed_for_level, progress_percentage)
    """
    current_level = level_for_xp(current_xp)
    if current_level >= MAX_LEVEL:
        return (0, 0, 100.0)

    level_start_xp = xp_for_level(current_level)
    next_level_xp = xp_for_level(current_level + 1)

    xp_in_level = current_xp - level_start_xp
    xp_for_this_level = next_level_xp - level_start_xp

    progress = (xp_in_level / xp_for_this_level) * 100 if xp_for_this_level > 0 else 100.0

    return (xp_in_level, xp_for_this_level, progress)


def get_level_milestone(level: int) -> str:
    """
    Get milestone name for special levels.

    Args:
        level: Current level

    Returns:
        Milestone name or empty string
    """
    milestones = {
        10: "Apprentice",
        25: "Journeyman",
        50: "Expert",
        75: "Master",
        92: "Halfway to 99",  # 92 is half the XP to 99
        99: "Maxed",
    }
    return milestones.get(level, "")


# Pre-compute XP table for quick lookups
XP_TABLE = {level: xp_for_level(level) for level in range(1, MAX_LEVEL + 2)}


# ==============================================================================
# COMBAT LEVEL (OSRS-Style Combined Level)
# Formula: combat_level = (sum_of_all_skill_levels // 2) + 3
# This creates a familiar OSRS feel where 2 skill levels = 1 combat level
# Starting at level 3 (like OSRS new accounts)
# Max combat level: (12 skills × 99 max) // 2 + 3 = 597 (or capped at 126)
# ==============================================================================

COMBAT_LEVEL_START = 3
COMBAT_LEVEL_MAX = 126  # OSRS authentic max


def calculate_combat_level(skill_levels: list[int]) -> int:
    """
    Calculate OSRS-style combat level from individual skill levels.

    Formula: combat_level = (sum_of_all_skill_levels // 2) + 3

    This means:
    - Every 2 skill level-ups = 1 combat level
    - Starting at level 3 (like OSRS new accounts)
    - Capped at 126 for authenticity (OSRS max combat)

    Args:
        skill_levels: List of individual skill levels (12 skills expected)

    Returns:
        Combat level (3-126)

    Example:
        >>> calculate_combat_level([10, 8, 5, 3, 4, 2, 1, 1, 1, 1, 1, 1])  # sum=38
        22  # (38 // 2) + 3 = 22
    """
    total_skill_levels = sum(skill_levels)
    combat_level = (total_skill_levels // 2) + COMBAT_LEVEL_START

    # Cap at authentic OSRS max
    return min(combat_level, COMBAT_LEVEL_MAX)


def calculate_combat_level_from_total(total_skill_levels: int) -> int:
    """
    Calculate combat level from pre-computed total skill levels.

    Args:
        total_skill_levels: Sum of all individual skill levels

    Returns:
        Combat level (3-126)
    """
    combat_level = (total_skill_levels // 2) + COMBAT_LEVEL_START
    return min(combat_level, COMBAT_LEVEL_MAX)


def skills_to_next_combat_level(total_skill_levels: int) -> int:
    """
    Calculate how many total skill levels needed to reach next combat level.

    Since 2 skill levels = 1 combat level, this is always 2 minus current remainder.

    Args:
        total_skill_levels: Current sum of all skill levels

    Returns:
        Skill levels needed (1 or 2)
    """
    # Every 2 skill levels = 1 combat level
    remainder = total_skill_levels % 2
    return 2 - remainder if remainder > 0 else 2


# Reference XP values for verification
REFERENCE_XP = {
    1: 0,
    2: 83,
    10: 1154,
    20: 4470,
    25: 8740,
    30: 13363,
    40: 37224,
    50: 101333,
    60: 273742,
    70: 737627,
    80: 1986068,
    90: 5346332,
    92: 6517253,  # Halfway point (by XP)
    99: 13034431,
}


def verify_xp_table() -> bool:
    """Verify XP table matches OSRS reference values."""
    for level, expected_xp in REFERENCE_XP.items():
        actual_xp = xp_for_level(level)
        if actual_xp != expected_xp:
            return False
    return True


if __name__ == "__main__":
    # Quick self-test
    print("OSRS XP Table Verification")
    print("=" * 40)

    if verify_xp_table():
        print("XP table matches OSRS reference values")
    else:
        print("ERROR: XP table mismatch!")

    print("\nSample Levels:")
    for level in [1, 10, 25, 50, 75, 92, 99]:
        xp = xp_for_level(level)
        milestone = get_level_milestone(level)
        suffix = f" ({milestone})" if milestone else ""
        print(f"  Level {level:2d}: {xp:>10,} XP{suffix}")

    print("\nSample XP → Level:")
    for xp in [0, 1000, 10000, 100000, 1000000]:
        level = level_for_xp(xp)
        xp_in, xp_needed, progress = progress_to_next_level(xp)
        print(f"  {xp:>10,} XP → Level {level} ({progress:.1f}% to next)")
