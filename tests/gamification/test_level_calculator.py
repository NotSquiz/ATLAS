"""Tests for OSRS-style level calculator."""

import pytest
from atlas.gamification.level_calculator import (
    xp_for_level,
    level_for_xp,
    xp_to_next_level,
    progress_to_next_level,
    get_level_milestone,
    verify_xp_table,
    MAX_LEVEL,
    REFERENCE_XP,
)


class TestXPForLevel:
    """Tests for xp_for_level function."""

    def test_level_1_is_zero(self):
        """Level 1 requires 0 XP."""
        assert xp_for_level(1) == 0

    def test_level_2_is_83(self):
        """Level 2 requires 83 XP (OSRS reference)."""
        assert xp_for_level(2) == 83

    def test_level_10(self):
        """Level 10 requires ~1,154 XP."""
        assert xp_for_level(10) == 1154

    def test_level_50(self):
        """Level 50 requires ~101,333 XP."""
        assert xp_for_level(50) == 101333

    def test_level_99_is_max(self):
        """Level 99 requires ~13M XP."""
        assert xp_for_level(99) == 13034431

    def test_level_above_max_capped(self):
        """Levels above 99 return same as 99."""
        assert xp_for_level(100) == xp_for_level(99)
        assert xp_for_level(150) == xp_for_level(99)

    def test_level_zero_or_negative(self):
        """Level 0 or negative returns 0."""
        assert xp_for_level(0) == 0
        assert xp_for_level(-1) == 0

    def test_exponential_growth(self):
        """XP requirement grows exponentially."""
        # Each 10 levels should roughly triple
        xp_10 = xp_for_level(10)
        xp_20 = xp_for_level(20)
        xp_30 = xp_for_level(30)

        assert xp_20 > xp_10 * 2  # At least double
        assert xp_30 > xp_20 * 2  # At least double


class TestLevelForXP:
    """Tests for level_for_xp function."""

    def test_zero_xp_is_level_1(self):
        """0 XP is Level 1."""
        assert level_for_xp(0) == 1

    def test_exact_threshold(self):
        """Exact threshold XP gives that level."""
        assert level_for_xp(83) == 2
        assert level_for_xp(1154) == 10
        assert level_for_xp(101333) == 50

    def test_just_below_threshold(self):
        """Just below threshold stays at previous level."""
        assert level_for_xp(82) == 1
        assert level_for_xp(1153) == 9
        assert level_for_xp(101332) == 49

    def test_just_above_threshold(self):
        """Just above threshold is at the higher level."""
        assert level_for_xp(84) == 2
        assert level_for_xp(1155) == 10
        assert level_for_xp(101334) == 50

    def test_negative_xp_is_level_1(self):
        """Negative XP returns Level 1."""
        assert level_for_xp(-100) == 1

    def test_max_xp_is_level_99(self):
        """XP at or above max is Level 99."""
        assert level_for_xp(13034431) == 99
        assert level_for_xp(20000000) == 99


class TestXPToNextLevel:
    """Tests for xp_to_next_level function."""

    def test_zero_xp_needs_83(self):
        """At 0 XP, need 83 XP for Level 2."""
        assert xp_to_next_level(0) == 83

    def test_halfway_to_level_2(self):
        """At 40 XP, need 43 more for Level 2."""
        assert xp_to_next_level(40) == 43

    def test_at_level_threshold(self):
        """At exact threshold, need XP for next level."""
        # At Level 2 (83 XP), need XP for Level 3
        level_3_xp = xp_for_level(3)
        assert xp_to_next_level(83) == level_3_xp - 83

    def test_max_level_returns_zero(self):
        """At max level, returns 0."""
        assert xp_to_next_level(13034431) == 0
        assert xp_to_next_level(20000000) == 0


class TestProgressToNextLevel:
    """Tests for progress_to_next_level function."""

    def test_zero_xp_is_zero_progress(self):
        """At 0 XP, progress is 0%."""
        xp_in, xp_needed, pct = progress_to_next_level(0)
        assert xp_in == 0
        assert pct == 0.0

    def test_halfway_progress(self):
        """Halfway through a level shows ~50%."""
        # Level 1 to 2 needs 83 XP, so 41 XP should be ~49%
        xp_in, xp_needed, pct = progress_to_next_level(41)
        assert xp_needed == 83
        assert 45 < pct < 55  # Approximately 50%

    def test_max_level_is_100_percent(self):
        """At max level, progress is 100%."""
        _, _, pct = progress_to_next_level(13034431)
        assert pct == 100.0


class TestGetLevelMilestone:
    """Tests for get_level_milestone function."""

    def test_milestone_levels(self):
        """Milestone levels return names."""
        assert get_level_milestone(10) == "Apprentice"
        assert get_level_milestone(25) == "Journeyman"
        assert get_level_milestone(50) == "Expert"
        assert get_level_milestone(75) == "Master"
        assert get_level_milestone(99) == "Maxed"

    def test_non_milestone_returns_empty(self):
        """Non-milestone levels return empty string."""
        assert get_level_milestone(1) == ""
        assert get_level_milestone(15) == ""
        assert get_level_milestone(60) == ""


class TestReferenceXP:
    """Tests for reference XP values."""

    def test_reference_xp_values(self):
        """Verify key reference XP values match OSRS."""
        # These are the canonical OSRS XP values
        assert xp_for_level(1) == REFERENCE_XP[1]
        assert xp_for_level(2) == REFERENCE_XP[2]
        assert xp_for_level(10) == REFERENCE_XP[10]
        assert xp_for_level(50) == REFERENCE_XP[50]
        assert xp_for_level(92) == REFERENCE_XP[92]  # Halfway point
        assert xp_for_level(99) == REFERENCE_XP[99]


class TestMaxLevel:
    """Tests for MAX_LEVEL constant."""

    def test_max_level_is_99(self):
        """Max level is 99 (OSRS standard)."""
        assert MAX_LEVEL == 99
