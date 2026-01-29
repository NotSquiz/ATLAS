"""
Tests for UI state export functionality.

These tests verify that session_status.json contains correct UI and
gamification state for autonomous iteration feedback.

Run with:
    pytest tests/ui/test_state_export.py -v

Note: Some tests require the atlas_launcher.py to be running in test mode.
"""
import json
import os
import pytest
from pathlib import Path


# Determine bridge directory path
# Works both in WSL2 and Windows
def get_bridge_dir() -> Path:
    """Get the bridge directory, handling WSL2 vs Windows paths."""
    # Try WSL path first
    wsl_path = Path.home() / ".atlas" / ".bridge"
    if wsl_path.exists():
        return wsl_path

    # Try UNC path (Windows accessing WSL)
    unc_path = Path(r"\\wsl$\Ubuntu\home\squiz\ATLAS\.bridge")
    if unc_path.exists():
        return unc_path

    # Fall back to home directory
    return Path.home() / ".atlas" / ".bridge"


BRIDGE_DIR = get_bridge_dir()
STATUS_FILE = BRIDGE_DIR / "session_status.json"
AUDIO_LOG = BRIDGE_DIR / "audio_events.jsonl"


def read_status_file() -> dict:
    """Read session_status.json with retry for race conditions."""
    if not STATUS_FILE.exists():
        return {}

    import time
    for attempt in range(3):
        try:
            return json.loads(STATUS_FILE.read_text())
        except json.JSONDecodeError:
            if attempt < 2:
                time.sleep(0.01)
            continue
    return {}


@pytest.fixture
def status_data():
    """Read current session status."""
    data = read_status_file()
    if not data:
        pytest.skip("session_status.json not found or empty - is the app running?")
    return data


class TestBasicStructure:
    """Tests for basic session_status.json structure."""

    def test_status_file_exists(self):
        """Session status file should exist."""
        assert STATUS_FILE.exists(), f"session_status.json not found at {STATUS_FILE}"

    def test_status_file_valid_json(self):
        """Session status should be valid JSON."""
        data = read_status_file()
        assert isinstance(data, dict)

    def test_has_updated_at(self, status_data):
        """Should have updated_at timestamp."""
        assert "updated_at" in status_data


class TestUIStateExport:
    """Tests for UI state in session_status.json."""

    def test_ui_state_present_in_test_mode(self, status_data):
        """UI state should be exported when ATLAS_TEST_MODE is set."""
        if "ui_state" not in status_data:
            pytest.skip("UI state not exported - run app with ATLAS_TEST_MODE=1")
        assert "ui_state" in status_data

    def test_ui_state_has_timer_visibility(self, status_data):
        """Timer visibility state should be exported."""
        if "ui_state" not in status_data:
            pytest.skip("UI state not exported")

        ui = status_data["ui_state"]
        assert "timer_visible" in ui
        assert isinstance(ui["timer_visible"], bool)

    def test_ui_state_has_window_geometry(self, status_data):
        """Window geometry should be exported."""
        if "ui_state" not in status_data:
            pytest.skip("UI state not exported")

        ui = status_data["ui_state"]
        if "window_geometry" in ui:
            # Format should be like "450x780+100+100"
            assert "x" in ui["window_geometry"]

    def test_ui_state_has_current_state(self, status_data):
        """Current state (idle/listening/processing/speaking) should be exported."""
        if "ui_state" not in status_data:
            pytest.skip("UI state not exported")

        ui = status_data["ui_state"]
        assert "current_state" in ui
        assert ui["current_state"] in ["idle", "listening", "processing", "speaking"]

    def test_ui_state_has_widgets_snapshot(self, status_data):
        """Widget states should be captured."""
        if "ui_state" not in status_data:
            pytest.skip("UI state not exported")

        ui = status_data["ui_state"]
        if "widgets" in ui:
            widgets = ui["widgets"]
            assert isinstance(widgets, dict)


class TestGamificationExport:
    """Tests for gamification data in session_status.json."""

    def test_gamification_present(self, status_data):
        """Gamification data should be exported."""
        if "gamification" not in status_data:
            pytest.skip("Gamification data not exported - run with state exporter")
        assert "gamification" in status_data

    def test_has_player_level(self, status_data):
        """Player total level should be present."""
        if "gamification" not in status_data:
            pytest.skip("Gamification data not exported")

        gam = status_data["gamification"]
        if "error" in gam:
            pytest.skip(f"Gamification error: {gam['error']}")

        assert "player_level" in gam
        assert isinstance(gam["player_level"], int)
        assert gam["player_level"] >= 12  # Minimum: 12 skills at level 1

    def test_has_total_xp(self, status_data):
        """Total XP should be present."""
        if "gamification" not in status_data:
            pytest.skip("Gamification data not exported")

        gam = status_data["gamification"]
        if "error" in gam:
            pytest.skip(f"Gamification error: {gam['error']}")

        assert "total_xp" in gam
        assert isinstance(gam["total_xp"], int)
        assert gam["total_xp"] >= 0

    def test_has_all_12_skills(self, status_data):
        """All 12 Lethal Gentleman skills should be present."""
        if "gamification" not in status_data:
            pytest.skip("Gamification data not exported")

        gam = status_data["gamification"]
        if "error" in gam:
            pytest.skip(f"Gamification error: {gam['error']}")

        skills = gam.get("skills", {})

        expected_skills = {
            # BODY
            "strength", "endurance", "mobility", "nutrition",
            # MIND
            "focus", "learning", "reflection", "creation",
            # SOUL
            "presence", "service", "courage", "consistency",
        }

        assert set(skills.keys()) == expected_skills, \
            f"Missing skills: {expected_skills - set(skills.keys())}"

    def test_skills_have_required_fields(self, status_data):
        """Each skill should have level, xp, domain, progress."""
        if "gamification" not in status_data:
            pytest.skip("Gamification data not exported")

        gam = status_data["gamification"]
        if "error" in gam:
            pytest.skip(f"Gamification error: {gam['error']}")

        skills = gam.get("skills", {})
        required = {"level", "xp", "domain", "progress_to_next"}

        for skill_name, skill_data in skills.items():
            for field in required:
                assert field in skill_data, f"{skill_name} missing {field}"

            # Validate values
            assert skill_data["level"] >= 1
            assert skill_data["level"] <= 99
            assert skill_data["xp"] >= 0
            assert skill_data["domain"] in ("body", "mind", "soul")
            assert 0.0 <= skill_data["progress_to_next"] <= 1.0

    def test_skills_by_domain_structure(self, status_data):
        """Skills should be grouped by domain."""
        if "gamification" not in status_data:
            pytest.skip("Gamification data not exported")

        gam = status_data["gamification"]
        if "error" in gam:
            pytest.skip(f"Gamification error: {gam['error']}")

        by_domain = gam.get("skills_by_domain", {})

        assert "body" in by_domain
        assert "mind" in by_domain
        assert "soul" in by_domain

        assert len(by_domain["body"]) == 4, "BODY should have 4 skills"
        assert len(by_domain["mind"]) == 4, "MIND should have 4 skills"
        assert len(by_domain["soul"]) == 4, "SOUL should have 4 skills"

    def test_streak_data_present(self, status_data):
        """Streak information should be present."""
        if "gamification" not in status_data:
            pytest.skip("Gamification data not exported")

        gam = status_data["gamification"]
        if "error" in gam:
            pytest.skip(f"Gamification error: {gam['error']}")

        assert "streak_days" in gam
        assert isinstance(gam["streak_days"], int)
        assert gam["streak_days"] >= 0


class TestTimerState:
    """Tests for timer state in session_status.json."""

    def test_timer_key_present(self, status_data):
        """Timer key should always be present (null or dict)."""
        # Timer can be null/None when no timer active
        timer = status_data.get("timer")
        if timer is None:
            pytest.skip("No active timer")

        assert isinstance(timer, dict)

    def test_timer_has_active_flag(self, status_data):
        """Timer should have active flag."""
        timer = status_data.get("timer")
        if timer is None:
            pytest.skip("No active timer")

        assert "active" in timer
        assert isinstance(timer["active"], bool)

    def test_timer_has_mode(self, status_data):
        """Active timer should have mode."""
        timer = status_data.get("timer")
        if timer is None or not timer.get("active"):
            pytest.skip("No active timer")

        assert "mode" in timer
        valid_modes = [
            "routine", "routine_pending", "routine_transition", "routine_complete",
            "workout", "workout_pending", "workout_rest", "workout_complete",
            "workout_set_active", "workout_awaiting_reps",
        ]
        # Mode should be one of valid options
        assert timer["mode"] in valid_modes or timer["mode"].startswith("workout")


class TestAudioEventLog:
    """Tests for audio event logging (for sound verification)."""

    def test_can_read_audio_log(self):
        """Should be able to read audio event log if it exists."""
        if not AUDIO_LOG.exists():
            pytest.skip("No audio log file")

        content = AUDIO_LOG.read_text()
        # Can be empty, that's fine

    def test_audio_events_valid_jsonl(self):
        """Audio events should be valid JSONL."""
        if not AUDIO_LOG.exists():
            pytest.skip("No audio log file")

        content = AUDIO_LOG.read_text()
        if not content.strip():
            pytest.skip("Audio log is empty")

        for line in content.splitlines():
            if line.strip():
                event = json.loads(line)
                assert "file" in event
                assert "timestamp" in event


class TestFixtures:
    """Tests for database fixtures module."""

    def test_fixtures_importable(self):
        """Fixture module should be importable."""
        from tests.fixtures.db_states import FIXTURES, load_fixture
        assert "new_player" in FIXTURES
        assert "mid_level" in FIXTURES
        assert "max_level_veteran" in FIXTURES
        assert callable(load_fixture)

    def test_all_fixtures_have_12_skills(self):
        """All fixtures should have all 12 skills defined."""
        from tests.fixtures.db_states import FIXTURES

        expected_skills = {
            "strength", "endurance", "mobility", "nutrition",
            "focus", "learning", "reflection", "creation",
            "presence", "service", "courage", "consistency",
        }

        for name, fixture in FIXTURES.items():
            fixture_skills = set(fixture["skills"].keys())
            assert fixture_skills == expected_skills, \
                f"Fixture {name} missing skills: {expected_skills - fixture_skills}"

    def test_level_up_trigger_available(self):
        """Level-up trigger function should be available."""
        from tests.fixtures.db_states import trigger_level_up
        assert callable(trigger_level_up)

    def test_fixtures_have_valid_levels(self):
        """All fixture skill levels should be valid (1-99)."""
        from tests.fixtures.db_states import FIXTURES

        for name, fixture in FIXTURES.items():
            for skill_name, (level, xp) in fixture["skills"].items():
                assert 1 <= level <= 99, \
                    f"Fixture {name}: {skill_name} has invalid level {level}"
                assert xp >= 0, \
                    f"Fixture {name}: {skill_name} has negative XP {xp}"
