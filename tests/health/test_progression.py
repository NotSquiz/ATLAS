"""
Tests for ATLAS Progressive Overload Service

Tests:
- 1RM calculation (Brzycki formula)
- Starting weight calculation from baselines
- Double progression triggers
- Deload detection
- Pain trend calculation
- Voice recommendation formatting
"""

import sqlite3
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestBrzyckiFormula:
    """Test 1RM estimation using Brzycki formula."""

    def test_1rm_from_5rm(self):
        """5RM of 100kg should estimate ~112kg 1RM."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        # Brzycki: weight * 36 / (37 - reps)
        # 100 * 36 / (37 - 5) = 100 * 36 / 32 = 112.5
        result = service._calculate_1rm_brzycki(100, 5)
        assert 112 <= result <= 113

    def test_1rm_from_10rm(self):
        """10RM of 80kg should estimate ~107kg 1RM."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        # 80 * 36 / (37 - 10) = 80 * 36 / 27 = 106.67
        result = service._calculate_1rm_brzycki(80, 10)
        assert 106 <= result <= 107

    def test_1rm_single_rep(self):
        """1RM test should return the weight itself."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        result = service._calculate_1rm_brzycki(120, 1)
        assert result == 120

    def test_1rm_zero_reps(self):
        """Zero reps should return weight (edge case)."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        result = service._calculate_1rm_brzycki(100, 0)
        assert result == 100


class TestRoundToIncrement:
    """Test weight rounding to plate increments."""

    def test_round_to_2_5(self):
        """Round to nearest 2.5kg."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        assert service._round_to_increment(23.7) == 22.5
        assert service._round_to_increment(24.0) == 25.0
        assert service._round_to_increment(26.3) == 27.5

    def test_round_to_1_25(self):
        """Round to nearest 1.25kg (microplates)."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        assert service._round_to_increment(23.7, 1.25) == 23.75
        assert service._round_to_increment(24.0, 1.25) == 23.75


class TestStartingWeight:
    """Test starting weight derivation from baselines."""

    def test_no_weight_tracking_exercise(self):
        """Bodyweight exercises should return None."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        weight, basis, staleness = service.get_starting_weight("bird_dog")
        assert weight is None
        assert basis == "no_weight_tracking"
        assert staleness is None

    def test_band_exercise(self):
        """Band exercises should return None."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        weight, basis, staleness = service.get_starting_weight("band_pull_apart")
        assert weight is None
        assert basis == "no_weight_tracking"
        assert staleness is None

    def test_unknown_exercise(self):
        """Unknown exercises should check history then return None."""
        from atlas.health.progression import ProgressionService
        service = ProgressionService()

        # Patch the private attribute since blueprint is a property
        mock_blueprint = MagicMock()
        mock_blueprint.get_last_performance.return_value = None
        service._blueprint = mock_blueprint

        weight, basis, staleness = service.get_starting_weight("unknown_exercise_xyz")
        assert weight is None
        assert basis == "no_mapping"
        assert staleness is None


class TestDeloadTriggers:
    """Test deload detection logic."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        db_path.unlink()

    def test_pain_spike_triggers_deload(self, temp_db):
        """Pain >= 6 should trigger immediate deload."""
        from atlas.health.progression import ProgressionService
        from atlas.health.pain import PainService

        # Set up pain service to return high pain
        service = ProgressionService(db_path=temp_db)
        mock_pain = MagicMock()
        mock_pain.get_max_recent_pain.return_value = 7
        service._pain_service = mock_pain

        # Mock no cooldown
        with patch.object(service, '_get_last_deload_date', return_value=None):
            result = service.check_deload()
            assert result.should_deload is True
            assert result.trigger == "pain_spike"

    def test_fatigue_triggers_deload(self, temp_db):
        """4+ YELLOW days in 10 should trigger deload."""
        from atlas.health.progression import ProgressionService

        service = ProgressionService(db_path=temp_db)
        mock_pain = MagicMock()
        mock_pain.get_max_recent_pain.return_value = 2  # Low pain
        service._pain_service = mock_pain

        mock_blueprint = MagicMock()
        mock_blueprint.count_yellow_days.return_value = 5  # High fatigue
        service._blueprint = mock_blueprint

        with patch.object(service, '_get_last_deload_date', return_value=None):
            result = service.check_deload()
            assert result.should_deload is True
            assert result.trigger == "fatigue_accumulated"

    def test_cooldown_prevents_deload(self, temp_db):
        """Deload within 14 days should activate cooldown."""
        from atlas.health.progression import ProgressionService

        service = ProgressionService(db_path=temp_db)

        # Last deload was 5 days ago
        recent_deload = date.today() - timedelta(days=5)
        with patch.object(service, '_get_last_deload_date', return_value=recent_deload):
            result = service.check_deload()
            assert result.should_deload is False
            assert result.cooldown_active is True

    def test_no_deload_when_healthy(self, temp_db):
        """No triggers should result in no deload."""
        from atlas.health.progression import ProgressionService

        service = ProgressionService(db_path=temp_db)
        mock_pain = MagicMock()
        mock_pain.get_max_recent_pain.return_value = 2
        service._pain_service = mock_pain

        mock_blueprint = MagicMock()
        mock_blueprint.count_yellow_days.return_value = 1
        service._blueprint = mock_blueprint

        with patch.object(service, '_get_last_deload_date', return_value=None):
            with patch.object(service, '_get_current_training_week', return_value=2):
                result = service.check_deload()
                assert result.should_deload is False


class TestPainTrend:
    """Test pain trend calculation."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database with pain_log table."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)

        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE pain_log (
                id INTEGER PRIMARY KEY,
                date DATE NOT NULL,
                body_part TEXT NOT NULL,
                pain_level INTEGER,
                stiffness_level INTEGER,
                notes TEXT,
                measured_at TEXT,
                UNIQUE(date, body_part)
            )
        """)
        conn.commit()
        conn.close()

        yield db_path
        db_path.unlink()

    def test_increasing_pain_trend(self, temp_db):
        """Increasing pain over days should show positive slope."""
        from atlas.health.pain import PainService

        # Insert increasing pain data
        conn = sqlite3.connect(temp_db)
        today = date.today()
        for i in range(5):
            day = (today - timedelta(days=4-i)).isoformat()
            conn.execute(
                "INSERT INTO pain_log (date, body_part, pain_level) VALUES (?, ?, ?)",
                (day, "shoulder_right", 2 + i)  # 2, 3, 4, 5, 6
            )
        conn.commit()
        conn.close()

        service = PainService(db_path=temp_db)
        trend = service.get_trend("shoulder_right", days=7)

        assert trend is not None
        assert trend.slope > 0.5  # Should be trending up
        assert trend.trending_up is True

    def test_stable_pain_trend(self, temp_db):
        """Stable pain should show near-zero slope."""
        from atlas.health.pain import PainService

        conn = sqlite3.connect(temp_db)
        today = date.today()
        for i in range(5):
            day = (today - timedelta(days=4-i)).isoformat()
            conn.execute(
                "INSERT INTO pain_log (date, body_part, pain_level) VALUES (?, ?, ?)",
                (day, "shoulder_right", 3)  # All 3s
            )
        conn.commit()
        conn.close()

        service = PainService(db_path=temp_db)
        trend = service.get_trend("shoulder_right", days=7)

        assert trend is not None
        assert -0.1 <= trend.slope <= 0.1  # Stable
        assert trend.trending_up is False

    def test_insufficient_data(self, temp_db):
        """Single data point should return None."""
        from atlas.health.pain import PainService

        conn = sqlite3.connect(temp_db)
        conn.execute(
            "INSERT INTO pain_log (date, body_part, pain_level) VALUES (?, ?, ?)",
            (date.today().isoformat(), "shoulder_right", 3)
        )
        conn.commit()
        conn.close()

        service = PainService(db_path=temp_db)
        trend = service.get_trend("shoulder_right", days=7)

        assert trend is None  # Need at least 2 points


class TestVoiceRecommendation:
    """Test voice prompt formatting."""

    def test_progression_recommendation(self):
        """Ready to progress should prompt with new weight."""
        from atlas.health.progression import ProgressionService, ProgressionRecommendation

        service = ProgressionService()
        rec = ProgressionRecommendation(
            exercise_id="goblet_squat",
            recommended_weight_kg=27.5,
            basis="progression",
            reasoning="All sets hit top of range",
            last_weight_kg=25.0,
            last_reps_avg=12.0,
            ready_to_progress=True,
        )

        voice = service.format_voice_recommendation(rec)
        assert "25" in voice
        assert "12" in voice
        assert "27" in voice or "27.5" in voice

    def test_pain_warning_recommendation(self):
        """Pain warning should prevent progression."""
        from atlas.health.progression import ProgressionService, ProgressionRecommendation

        service = ProgressionService()
        rec = ProgressionRecommendation(
            exercise_id="floor_press",
            recommended_weight_kg=20.0,
            basis="maintain",
            reasoning="Hold weight - shoulder pain trending up",
            last_weight_kg=20.0,
            pain_warning="shoulder right pain trending up",
        )

        voice = service.format_voice_recommendation(rec)
        assert "pain" in voice.lower() or "shoulder" in voice.lower()
        assert "20" in voice

    def test_no_weight_tracking(self):
        """No weight tracking should return empty string."""
        from atlas.health.progression import ProgressionService, ProgressionRecommendation

        service = ProgressionService()
        rec = ProgressionRecommendation(
            exercise_id="bird_dog",
            recommended_weight_kg=None,
            basis="no_weight_tracking",
            reasoning="No weight tracking for bird_dog",
        )

        voice = service.format_voice_recommendation(rec)
        assert voice == ""


class TestWorkoutSummary:
    """Test post-workout summary generation."""

    def test_progression_summary(self):
        """Completed exercises should generate summary."""
        from atlas.health.progression import ProgressionService

        service = ProgressionService()
        workout_log = [
            {"id": "goblet_squat", "name": "Goblet Squat", "reps": [12, 12, 12], "weight": 25},
            {"id": "floor_press", "name": "Floor Press", "reps": [10, 10, 10], "weight": 20},
        ]

        summary = service.get_workout_summary(workout_log)

        # Goblet squat hit 12 (top of range 8-12) - should recommend increase
        assert "goblet" in summary.lower() or "squat" in summary.lower()
        assert "27" in summary or "bump" in summary.lower()

    def test_empty_workout(self):
        """Empty workout should return simple message."""
        from atlas.health.progression import ProgressionService

        service = ProgressionService()
        summary = service.get_workout_summary([])
        assert "good" in summary.lower() or len(summary) < 20
