"""
ATLAS Gamification Module

OSRS-inspired skill tracking and XP system for health/fitness activities.

Design principles (from verification review):
- XP as FEEDBACK, not reward (avoid crowding out intrinsic motivation)
- Fail-safe: XP failures never break core health tracking
- Non-blocking: XP awards don't add latency to voice responses
- Announcements only on level-ups (avoid fatigue)

Usage:
    from atlas.gamification import get_xp_service

    service = get_xp_service()

    # Non-blocking XP award (fire-and-forget)
    service.award_xp_async("strength", 100, "workout_strength")

    # Get current skills (for display)
    skills = service.get_all_skills()
    for skill in skills:
        print(f"{skill.name}: Level {skill.level} ({skill.xp:,} XP)")
"""

# Level calculator is always available (pure math, no dependencies)
from atlas.gamification.level_calculator import (
    xp_for_level,
    level_for_xp,
    xp_to_next_level,
    progress_to_next_level,
    calculate_combat_level,
    calculate_combat_level_from_total,
    skills_to_next_combat_level,
    MAX_LEVEL,
    COMBAT_LEVEL_MAX,
)

# XP service uses lazy loading to avoid import issues
_xp_service_instance = None


def get_xp_service():
    """
    Get singleton XPService instance with lazy loading.

    Uses lazy loading to:
    - Avoid circular imports
    - Defer database connection until needed
    - Allow health services to import without XP dependency
    """
    global _xp_service_instance
    if _xp_service_instance is None:
        from atlas.gamification.xp_service import XPService
        _xp_service_instance = XPService()
    return _xp_service_instance


__all__ = [
    "get_xp_service",
    "xp_for_level",
    "level_for_xp",
    "xp_to_next_level",
    "progress_to_next_level",
    "calculate_combat_level",
    "calculate_combat_level_from_total",
    "skills_to_next_combat_level",
    "MAX_LEVEL",
    "COMBAT_LEVEL_MAX",
]
