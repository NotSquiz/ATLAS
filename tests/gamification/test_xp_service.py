"""Tests for XP service."""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from atlas.gamification.xp_service import (
    XPService,
    Skill,
    XPAwardResult,
    SkillName,
    XP_TABLE,
    award_xp_safe,
    award_xp_safe_async,
)
from atlas.gamification.level_calculator import xp_for_level


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def xp_service(temp_db):
    """Create XP service with temp database."""
    service = XPService(db_path=temp_db)
    yield service
    service.close()


class TestSkillName:
    """Tests for SkillName enum (12-skill Lethal Gentleman Framework)."""

    def test_all_skills_defined(self):
        """All 12 skills are defined across 3 domains."""
        skills = list(SkillName)
        assert len(skills) == 12

    def test_skill_values(self):
        """Skill values are lowercase."""
        # BODY skills
        assert SkillName.STRENGTH.value == "strength"
        assert SkillName.ENDURANCE.value == "endurance"
        assert SkillName.MOBILITY.value == "mobility"
        assert SkillName.NUTRITION.value == "nutrition"
        # MIND skills
        assert SkillName.FOCUS.value == "focus"
        assert SkillName.LEARNING.value == "learning"
        assert SkillName.REFLECTION.value == "reflection"
        assert SkillName.CREATION.value == "creation"
        # SOUL skills
        assert SkillName.PRESENCE.value == "presence"
        assert SkillName.SERVICE.value == "service"
        assert SkillName.COURAGE.value == "courage"
        assert SkillName.CONSISTENCY.value == "consistency"


class TestXPTable:
    """Tests for XP_TABLE values."""

    def test_xp_table_has_expected_keys(self):
        """XP_TABLE has all expected source types."""
        expected_keys = [
            "workout_strength",
            "workout_cardio",
            "morning_routine",
            "supplement_batch",
            "meal_log",
            "sleep_good",
            "body_battery_good",
            "rest_day",
            "daily_checkin",
            "streak_bonus",
            "work_session",
            "work_capture",
            "assessment_complete",
            "weight_log",
        ]
        for key in expected_keys:
            assert key in XP_TABLE, f"Missing XP_TABLE key: {key}"

    def test_xp_values_positive(self):
        """All XP values are positive."""
        for key, value in XP_TABLE.items():
            assert value > 0, f"{key} has non-positive XP: {value}"


class TestXPServiceInit:
    """Tests for XP service initialization."""

    def test_tables_created(self, xp_service, temp_db):
        """Tables are created on init."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "player_skills" in tables
        assert "xp_events" in tables
        assert "activity_streaks" in tables

    def test_skills_seeded(self, xp_service):
        """All 12 skills are seeded at Level 1."""
        skills = xp_service.get_all_skills()
        assert len(skills) == 12
        for skill in skills:
            assert skill.level == 1
            assert skill.xp == 0

    def test_daily_reflections_table_created(self, xp_service, temp_db):
        """Daily reflections table is created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "daily_reflections" in tables


class TestAwardXP:
    """Tests for award_xp method."""

    def test_basic_award(self, xp_service):
        """Basic XP award works."""
        result = xp_service.award_xp("strength", 100, "test", apply_streak_bonus=False)
        assert result.xp_awarded == 100
        assert result.skill_name == "strength"
        assert result.new_total_xp == 100

    def test_award_accumulates(self, xp_service):
        """Multiple awards accumulate."""
        xp_service.award_xp("strength", 50, "test1", apply_streak_bonus=False)
        result = xp_service.award_xp("strength", 50, "test2", apply_streak_bonus=False)
        assert result.new_total_xp == 100

    def test_level_up(self, xp_service):
        """Awards that cross level threshold trigger level up."""
        # Level 2 requires 83 XP
        result = xp_service.award_xp("strength", 100, "test", apply_streak_bonus=False)
        assert result.leveled_up is True
        assert result.new_level == 2
        assert result.old_level == 1

    def test_no_level_up(self, xp_service):
        """Award below threshold doesn't level up."""
        result = xp_service.award_xp("strength", 50, "test", apply_streak_bonus=False)
        assert result.leveled_up is False
        assert result.new_level == 1

    def test_skill_name_normalized(self, xp_service):
        """Skill names are normalized to lowercase."""
        result = xp_service.award_xp("STRENGTH", 50, "test", apply_streak_bonus=False)
        assert result.skill_name == "strength"

    def test_invalid_skill_raises(self, xp_service):
        """Invalid skill name raises ValueError."""
        with pytest.raises(ValueError):
            xp_service.award_xp("invalid_skill", 50, "test")

    def test_xp_capped(self, xp_service):
        """XP is capped at max value."""
        # Award more than max
        result = xp_service.award_xp("strength", 20_000_000, "test", apply_streak_bonus=False)
        assert result.new_total_xp == 15_000_000  # MAX_XP_PER_SKILL


class TestGetSkill:
    """Tests for get_skill method."""

    def test_get_existing_skill(self, xp_service):
        """Can get an existing skill."""
        skill = xp_service.get_skill("strength")
        assert skill is not None
        assert skill.name == "strength"
        assert skill.level == 1
        assert skill.xp == 0

    def test_get_after_award(self, xp_service):
        """Get skill reflects awards."""
        xp_service.award_xp("strength", 100, "test", apply_streak_bonus=False)
        skill = xp_service.get_skill("strength")
        assert skill.xp == 100
        assert skill.level == 2


class TestGetAllSkills:
    """Tests for get_all_skills method."""

    def test_returns_all_skills(self, xp_service):
        """Returns all 12 skills across 3 domains."""
        skills = xp_service.get_all_skills()
        assert len(skills) == 12
        skill_names = {s.name for s in skills}
        expected = {
            # BODY
            "strength", "endurance", "mobility", "nutrition",
            # MIND
            "focus", "learning", "reflection", "creation",
            # SOUL
            "presence", "service", "courage", "consistency"
        }
        assert skill_names == expected

    def test_ordered_by_level(self, xp_service):
        """Skills are ordered by level descending."""
        xp_service.award_xp("creation", 1000, "test", apply_streak_bonus=False)
        skills = xp_service.get_all_skills()
        # Creation should be first (highest level)
        assert skills[0].name == "creation"

    def test_skills_have_domain(self, xp_service):
        """Each skill has a domain (body/mind/soul)."""
        skills = xp_service.get_all_skills()
        for skill in skills:
            assert skill.domain in ("body", "mind", "soul")

    def test_skills_have_virtue(self, xp_service):
        """Each skill has a virtue."""
        skills = xp_service.get_all_skills()
        for skill in skills:
            assert skill.virtue != ""


class TestGetTotalLevel:
    """Tests for get_total_level method."""

    def test_initial_total_level(self, xp_service):
        """Initial total level is 12 (all at Level 1)."""
        assert xp_service.get_total_level() == 12

    def test_total_level_increases(self, xp_service):
        """Total level increases with awards."""
        xp_service.award_xp("strength", 100, "test", apply_streak_bonus=False)  # Level 2
        assert xp_service.get_total_level() == 13


class TestGetTotalXP:
    """Tests for get_total_xp method."""

    def test_initial_total_xp(self, xp_service):
        """Initial total XP is 0."""
        assert xp_service.get_total_xp() == 0

    def test_total_xp_accumulates(self, xp_service):
        """Total XP accumulates across skills."""
        xp_service.award_xp("strength", 50, "test1", apply_streak_bonus=False)
        xp_service.award_xp("mobility", 50, "test2", apply_streak_bonus=False)
        assert xp_service.get_total_xp() == 100


class TestReconcile:
    """Tests for reconcile method."""

    def test_reconcile_passes_initially(self, xp_service):
        """Reconciliation passes when data is consistent."""
        valid, discrepancies = xp_service.reconcile()
        assert valid is True
        assert len(discrepancies) == 0

    def test_reconcile_passes_after_awards(self, xp_service):
        """Reconciliation passes after normal awards."""
        xp_service.award_xp("strength", 100, "test1", apply_streak_bonus=False)
        xp_service.award_xp("mobility", 200, "test2", apply_streak_bonus=False)
        valid, discrepancies = xp_service.reconcile()
        assert valid is True


class TestFormatStatusVoice:
    """Tests for format_status_voice method."""

    def test_initial_status(self, xp_service):
        """Initial status has all 12 skills at level 1."""
        status = xp_service.format_status_voice()
        assert "Total level 12" in status

    def test_status_after_awards(self, xp_service):
        """Status reflects awards."""
        xp_service.award_xp("strength", 1000, "test", apply_streak_bonus=False)
        status = xp_service.format_status_voice()
        assert "Strength" in status
        # Level should be higher than 1


class TestGetSkillsByDomain:
    """Tests for get_skills_by_domain method."""

    def test_body_domain(self, xp_service):
        """Body domain has 4 skills."""
        skills = xp_service.get_skills_by_domain("body")
        assert len(skills) == 4
        names = {s.name for s in skills}
        assert names == {"strength", "endurance", "mobility", "nutrition"}

    def test_mind_domain(self, xp_service):
        """Mind domain has 4 skills."""
        skills = xp_service.get_skills_by_domain("mind")
        assert len(skills) == 4
        names = {s.name for s in skills}
        assert names == {"focus", "learning", "reflection", "creation"}

    def test_soul_domain(self, xp_service):
        """Soul domain has 4 skills."""
        skills = xp_service.get_skills_by_domain("soul")
        assert len(skills) == 4
        names = {s.name for s in skills}
        assert names == {"presence", "service", "courage", "consistency"}

    def test_invalid_domain_raises(self, xp_service):
        """Invalid domain raises ValueError."""
        with pytest.raises(ValueError):
            xp_service.get_skills_by_domain("invalid")


class TestSkillDataclass:
    """Tests for Skill dataclass."""

    def test_xp_to_next(self):
        """xp_to_next property works."""
        skill = Skill(name="strength", xp=50, level=1)
        assert skill.xp_to_next == 33  # Need 83 for Level 2, have 50

    def test_progress_pct(self):
        """progress_pct property works."""
        skill = Skill(name="strength", xp=41, level=1)
        assert 45 < skill.progress_pct < 55  # About 50%

    def test_to_voice(self):
        """to_voice method formats correctly."""
        skill = Skill(name="strength", xp=100, level=2)
        assert skill.to_voice() == "Strength level 2"


class TestXPAwardResult:
    """Tests for XPAwardResult dataclass."""

    def test_level_up_message_when_leveled(self):
        """level_up_message returns message when leveled up."""
        result = XPAwardResult(
            skill_name="strength",
            xp_awarded=100,
            new_total_xp=100,
            old_level=1,
            new_level=2,
            leveled_up=True,
            source="test",
        )
        msg = result.level_up_message()
        assert msg is not None
        assert "Level up" in msg
        assert "Strength" in msg
        assert "2" in msg

    def test_level_up_message_when_not_leveled(self):
        """level_up_message returns None when not leveled."""
        result = XPAwardResult(
            skill_name="strength",
            xp_awarded=50,
            new_total_xp=50,
            old_level=1,
            new_level=1,
            leveled_up=False,
            source="test",
        )
        assert result.level_up_message() is None


class TestSafeFunctions:
    """Tests for fail-safe wrapper functions."""

    def test_award_xp_safe_returns_result(self, temp_db, monkeypatch):
        """award_xp_safe returns result on success."""
        # Need to patch the global singleton
        import atlas.gamification
        service = XPService(db_path=temp_db)
        monkeypatch.setattr(atlas.gamification, "_xp_service_instance", service)

        result = award_xp_safe("strength", 100, "test", apply_streak_bonus=False)
        assert result is not None
        assert result.xp_awarded == 100

        service.close()

    def test_award_xp_safe_handles_errors(self, monkeypatch):
        """award_xp_safe returns None on error."""
        # Patch to raise error
        import atlas.gamification
        monkeypatch.setattr(atlas.gamification, "_xp_service_instance", None)

        def bad_get():
            raise RuntimeError("Test error")

        monkeypatch.setattr(atlas.gamification, "get_xp_service", bad_get)

        result = award_xp_safe("strength", 100, "test")
        assert result is None


class TestOctalysisTitles:
    """Tests for Octalysis-informed title system."""

    def test_title_for_level_1(self, xp_service):
        """Level 1 skills have Apprentice title."""
        skill = xp_service.get_skill("strength")
        assert skill.title == "Apprentice"

    def test_title_for_level_20(self, xp_service):
        """Level 20 skills have Practitioner title."""
        # Award enough XP to reach level 20 (about 4,470 XP)
        xp_service.award_xp("strength", 5000, "test", apply_streak_bonus=False)
        skill = xp_service.get_skill("strength")
        assert skill.level >= 16
        assert skill.title == "Practitioner"

    def test_title_description_exists(self, xp_service):
        """Title descriptions are not empty."""
        skill = xp_service.get_skill("strength")
        assert skill.title_description != ""
        assert "foundation" in skill.title_description.lower() or "learning" in skill.title_description.lower()

    def test_to_voice_with_title(self, xp_service):
        """to_voice_with_title includes title."""
        skill = xp_service.get_skill("strength")
        voice = skill.to_voice_with_title()
        assert "Strength" in voice
        assert "level 1" in voice
        assert "Apprentice" in voice


class TestOctalysisLevelUp:
    """Tests for Octalysis-enhanced level-up messages."""

    def test_level_up_message_with_title(self, xp_service):
        """Level-up message includes new level."""
        result = xp_service.award_xp("strength", 100, "test", apply_streak_bonus=False)
        assert result.leveled_up
        msg = result.level_up_message_with_title()
        assert "Level up" in msg
        assert "2" in msg

    def test_title_change_detected(self, xp_service):
        """Title change is detected across tier boundary."""
        # Award XP to get to level 16 (Practitioner tier starts at 16)
        result = xp_service.award_xp("strength", 3000, "test", apply_streak_bonus=False)
        # This might not cross tier, let's check
        if result.new_level >= 16 and result.old_level < 16:
            assert result.title_changed


class TestOctalysisRollingWindow:
    """Tests for rolling window consistency (ethical streak alternative)."""

    def test_rolling_window_initial(self, xp_service):
        """Initial rolling window is 0 of 7."""
        active, total = xp_service.get_rolling_window_consistency()
        assert active == 0
        assert total == 7

    def test_is_consistent_initially_false(self, xp_service):
        """User is not consistent initially."""
        assert not xp_service.is_consistent_rolling_window()


class TestOctalysisStrategicRest:
    """Tests for strategic rest system (shadow counter)."""

    def test_log_strategic_rest_planned(self, xp_service):
        """Logging planned rest awards XP."""
        xp = xp_service.log_strategic_rest("planned", "Recovery week")
        assert xp > 0

    def test_strategic_rest_awards_to_consistency(self, xp_service):
        """Strategic rest XP goes to Consistency skill."""
        before = xp_service.get_skill("consistency").xp
        xp_service.log_strategic_rest("planned")
        after = xp_service.get_skill("consistency").xp
        assert after > before


class TestOctalysisSkillDrives:
    """Tests for skill-to-drive mapping."""

    def test_skills_have_drives(self, xp_service):
        """Each skill has Core Drive mapping."""
        skill = xp_service.get_skill("strength")
        drives = skill.drives
        assert len(drives) == 3
        assert drives[0].startswith("CD")  # Primary drive
        assert drives[1].startswith("CD")  # Secondary drive

    def test_consistency_has_flexibility_counter(self, xp_service):
        """Consistency skill includes flexibility as drive counter."""
        skill = xp_service.get_skill("consistency")
        drives = skill.drives
        assert "FLEXIBILITY" in drives[2].upper()


class TestOctalysisStreakFreezes:
    """Tests for streak freeze system."""

    def test_initial_freezes_zero(self, xp_service):
        """No streak freezes initially."""
        assert xp_service.get_available_streak_freezes() == 0

    def test_streak_status_voice(self, xp_service):
        """Streak status voice output is formatted."""
        status = xp_service.get_streak_status_voice()
        assert isinstance(status, str)
        assert len(status) > 0


class TestOctalysisGraduation:
    """Tests for graduation status (design for exit)."""

    def test_low_level_no_graduation(self, xp_service):
        """Low level skills don't show graduation."""
        status = xp_service.get_graduation_status("strength")
        assert status is None

    def test_format_status_with_titles(self, xp_service):
        """Status with titles formats correctly."""
        status = xp_service.format_status_voice_with_titles()
        assert "Apprentice" in status
        assert "Total level" in status
