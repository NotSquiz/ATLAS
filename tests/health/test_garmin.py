"""
Tests for Garmin Connect integration.

Tests cover:
- GarminMetrics dataclass
- GarminService class
- Response parsing (sleep, HRV, body battery)
- Error handling (auth, rate limit, no data)
- TrafficLightRouter integration
- Timezone conversion
"""

import pytest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from zoneinfo import ZoneInfo

# Test imports
from atlas.health.garmin import (
    GarminMetrics,
    GarminService,
    GarminAPIError,
    GarminAuthError,
    GarminRateLimitError,
    GarminNoDataError,
    is_garmin_auth_valid,
    GARTH_HOME,
    AEST,
)


# =============================================================================
# GarminMetrics Tests
# =============================================================================


class TestGarminMetrics:
    """Tests for GarminMetrics dataclass."""

    def test_create_with_all_fields(self):
        """Can create GarminMetrics with all fields populated."""
        metrics = GarminMetrics(
            date=date.today(),
            sync_status="success",
            sleep_hours=7.5,
            sleep_score=82,
            deep_sleep_minutes=90,
            rem_sleep_minutes=85,
            light_sleep_minutes=240,
            awake_minutes=30,
            resting_hr=52,
            hrv_status="BALANCED",
            hrv_avg=45,
            hrv_morning=48,
            body_battery=75,
            body_battery_charged=80,
            body_battery_drained=5,
            stress_avg=25,
        )

        assert metrics.sleep_hours == 7.5
        assert metrics.hrv_status == "BALANCED"
        assert metrics.resting_hr == 52
        assert metrics.body_battery == 75
        assert metrics.sync_status == "success"

    def test_optional_fields_default_to_none(self):
        """Optional fields default to None."""
        metrics = GarminMetrics(date=date.today())

        assert metrics.sleep_hours is None
        assert metrics.hrv_status is None
        assert metrics.body_battery is None
        assert metrics.sync_status == "success"  # Has default
        assert metrics.missing_fields == []  # Has default

    def test_missing_fields_tracking(self):
        """Can track missing fields."""
        metrics = GarminMetrics(
            date=date.today(),
            sync_status="partial",
            sleep_hours=7.0,
            missing_fields=["hrv_status", "body_battery"],
        )

        assert len(metrics.missing_fields) == 2
        assert "hrv_status" in metrics.missing_fields


# =============================================================================
# GarminService Configuration Tests
# =============================================================================


class TestGarminServiceConfig:
    """Tests for GarminService configuration methods."""

    def test_is_configured_no_session(self):
        """is_configured returns False when no session exists."""
        with patch.object(Path, "exists", return_value=False):
            service = GarminService()
            assert service.is_configured() is False

    def test_is_configured_with_session(self):
        """is_configured returns True when oauth1_token.json exists."""
        with patch.object(Path, "exists", return_value=True):
            service = GarminService()
            # Note: is_configured checks specific file path
            with patch.object(
                type(GARTH_HOME / "oauth1_token.json"), "exists", return_value=True
            ):
                assert service.is_configured() is True

    def test_has_valid_token_not_configured(self):
        """has_valid_token returns False when not configured."""
        service = GarminService()
        with patch.object(service, "is_configured", return_value=False):
            assert service.has_valid_token() is False


# =============================================================================
# Response Parser Tests
# =============================================================================


class TestSleepParsing:
    """Tests for sleep data parsing."""

    def test_parse_sleep_valid_response(self):
        """Parse valid sleep response with all fields."""
        service = GarminService()

        raw = {
            "dailySleepDTO": {
                "sleepTimeSeconds": 27000,  # 7.5 hours
                "deepSleepSeconds": 5400,  # 90 min
                "remSleepSeconds": 5100,  # 85 min
                "lightSleepSeconds": 14400,  # 240 min
                "awakeSleepSeconds": 1800,  # 30 min
                "restingHeartRate": 52,
                "avgOvernightHrv": 45.2,
                "sleepScores": {"overall": {"value": 82}},
            }
        }

        result = service._parse_sleep(raw)

        assert result["sleep_hours"] == 7.5
        assert result["deep_sleep_minutes"] == 90
        assert result["rem_sleep_minutes"] == 85
        assert result["light_sleep_minutes"] == 240
        assert result["awake_minutes"] == 30
        assert result["sleep_score"] == 82
        assert result["resting_hr"] == 52
        assert result["hrv_avg"] == 45
        assert len(result.get("missing", [])) == 0

    def test_parse_sleep_empty_response(self):
        """Parse empty sleep response gracefully."""
        service = GarminService()

        result = service._parse_sleep(None)
        assert result["sync_status"] == "no_data"

    def test_parse_sleep_no_daily_dto(self):
        """Handle response without dailySleepDTO (watch not synced)."""
        service = GarminService()

        raw = {"someOtherField": "value"}
        result = service._parse_sleep(raw)

        assert result["sync_status"] == "no_data"

    def test_parse_sleep_partial_data(self):
        """Parse sleep response with some fields missing."""
        service = GarminService()

        raw = {
            "dailySleepDTO": {
                "sleepTimeSeconds": 25200,  # 7 hours
                # Missing: deepSleepSeconds, remSleepSeconds, etc.
            }
        }

        result = service._parse_sleep(raw)

        assert result["sleep_hours"] == 7.0
        assert "deep_sleep_minutes" in result.get("missing", [])
        assert "sleep_score" in result.get("missing", [])


class TestHRVParsing:
    """Tests for HRV data parsing."""

    def test_parse_hrv_balanced(self):
        """Parse HRV response with BALANCED status."""
        service = GarminService()

        raw = {"hrvStatus": "BALANCED", "hrvValueMorning": 52}
        result = service._parse_hrv(raw)

        assert result["hrv_status"] == "BALANCED"
        assert result["hrv_morning"] == 52

    def test_parse_hrv_unbalanced(self):
        """Parse HRV response with UNBALANCED status."""
        service = GarminService()

        raw = {"hrvStatus": "UNBALANCED"}
        result = service._parse_hrv(raw)

        assert result["hrv_status"] == "UNBALANCED"
        assert "hrv_morning" in result.get("missing", [])

    def test_parse_hrv_empty(self):
        """Parse empty HRV response."""
        service = GarminService()

        result = service._parse_hrv(None)
        assert result["sync_status"] == "no_data"


class TestBodyBatteryParsing:
    """Tests for body battery data parsing."""

    def test_parse_body_battery_full(self):
        """Parse body battery response with all fields."""
        service = GarminService()

        raw = {"charged": 75, "drained": 25, "averageStressLevel": 30}
        result = service._parse_body_battery(raw)

        assert result["body_battery"] == 75
        assert result["body_battery_charged"] == 75
        assert result["body_battery_drained"] == 25
        assert result["stress_avg"] == 30

    def test_parse_body_battery_empty(self):
        """Parse empty body battery response."""
        service = GarminService()

        result = service._parse_body_battery(None)
        assert result["sync_status"] == "no_data"


# =============================================================================
# Timezone Conversion Tests
# =============================================================================


class TestTimezoneConversion:
    """Tests for GMT to AEST timezone conversion."""

    def test_convert_gmt_timestamp(self):
        """Convert Garmin GMT timestamp to AEST."""
        service = GarminService()

        # 2026-01-14 00:00:00 GMT in milliseconds
        gmt_ms = 1768435200000

        result = service._convert_gmt_timestamp(gmt_ms)

        assert result.tzinfo == AEST
        # AEST is UTC+10 (or +11 during daylight saving)
        assert result.year == 2026
        assert result.month == 1

    def test_aest_timezone_defined(self):
        """Verify AEST timezone is correctly defined."""
        assert AEST == ZoneInfo("Australia/Sydney")


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_handles_auth_failure(self):
        """sync_today handles authentication failure by returning None or raising."""
        service = GarminService()
        service._session_valid = True

        # Test that fetch_endpoint raises GarminAPIError on failure
        with patch.object(service, "is_configured", return_value=True):
            with patch.object(
                service,
                "_fetch_endpoint",
                side_effect=GarminAPIError("Auth failed", status_code=401),
            ):
                with pytest.raises(GarminAPIError):
                    await service.sync_today()

    def test_handles_no_data(self):
        """Parser returns no_data status for empty responses."""
        service = GarminService()

        sleep_result = service._parse_sleep(None)
        hrv_result = service._parse_hrv(None)
        battery_result = service._parse_body_battery(None)

        assert sleep_result["sync_status"] == "no_data"
        assert hrv_result["sync_status"] == "no_data"
        assert battery_result["sync_status"] == "no_data"

    def test_handles_malformed_json(self):
        """Parser handles malformed JSON gracefully."""
        service = GarminService()

        # Missing expected structure
        raw = {"unexpected": "structure", "no": "dailySleepDTO"}
        result = service._parse_sleep(raw)

        assert result["sync_status"] == "no_data"


# =============================================================================
# is_garmin_auth_valid Tests
# =============================================================================


class TestAuthValidation:
    """Tests for is_garmin_auth_valid function."""

    def test_auth_valid_no_garth_home(self):
        """Returns False when ~/.garth/ doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            assert is_garmin_auth_valid() is False

    def test_auth_valid_returns_false_when_no_tokens(self):
        """Returns False when token directory doesn't exist."""
        # Without valid tokens, auth check should return False
        # The actual function catches exceptions and returns False
        # This test verifies the expected behavior without mocking internals
        result = is_garmin_auth_valid()
        # Since we don't have actual Garmin tokens in CI, this should be False
        assert result is False


# =============================================================================
# TrafficLightRouter Integration Tests
# =============================================================================


class TestTrafficLightIntegration:
    """Tests for integration with TrafficLightRouter."""

    def test_metrics_feed_into_router_green(self):
        """GarminMetrics can produce GREEN traffic light."""
        from atlas.health.router import TrafficLightRouter, TrafficLightStatus

        metrics = GarminMetrics(
            date=date.today(),
            sleep_hours=7.5,
            hrv_status="BALANCED",
            resting_hr=52,
        )

        router = TrafficLightRouter(rhr_baseline=55)
        result = router.evaluate(
            sleep_hours=metrics.sleep_hours,
            hrv_status=metrics.hrv_status,
            resting_hr=metrics.resting_hr,
        )

        assert result.status == TrafficLightStatus.GREEN

    def test_metrics_feed_into_router_red(self):
        """GarminMetrics with poor values produces RED traffic light."""
        from atlas.health.router import TrafficLightRouter, TrafficLightStatus

        metrics = GarminMetrics(
            date=date.today(),
            sleep_hours=4.5,  # Poor sleep
            hrv_status="LOW",
            resting_hr=70,  # Elevated
        )

        router = TrafficLightRouter(rhr_baseline=55)
        result = router.evaluate(
            sleep_hours=metrics.sleep_hours,
            hrv_status=metrics.hrv_status,
            resting_hr=metrics.resting_hr,
        )

        assert result.status == TrafficLightStatus.RED


# =============================================================================
# Async Sync Tests
# =============================================================================


@pytest.mark.asyncio
class TestSyncToday:
    """Tests for sync_today method."""

    async def test_sync_not_configured_returns_none(self):
        """sync_today returns None when not configured."""
        service = GarminService()

        with patch.object(service, "is_configured", return_value=False):
            result = await service.sync_today()
            assert result is None

    async def test_sync_no_session_returns_none(self):
        """sync_today returns None when session invalid."""
        service = GarminService()
        service._session_valid = False

        with patch.object(service, "is_configured", return_value=True):
            with patch.object(service, "_load_session", return_value=False):
                result = await service.sync_today()
                assert result is None

    async def test_sync_success_returns_metrics(self):
        """sync_today returns GarminMetrics on success."""
        service = GarminService()
        service._session_valid = True

        mock_sleep = {
            "dailySleepDTO": {
                "sleepTimeSeconds": 27000,
                "sleepScores": {"overall": {"value": 80}},
            }
        }
        mock_hrv = {"hrvStatus": "BALANCED"}
        mock_battery = {"charged": 70}

        with patch.object(service, "is_configured", return_value=True):
            with patch.object(
                service,
                "_fetch_endpoint",
                side_effect=[mock_sleep, mock_hrv, mock_battery],
            ):
                result = await service.sync_today()

                assert isinstance(result, GarminMetrics)
                assert result.sleep_hours == 7.5
                assert result.hrv_status == "BALANCED"
                assert result.body_battery == 70


# =============================================================================
# Custom Exception Tests
# =============================================================================


class TestExceptions:
    """Tests for custom exception classes."""

    def test_garmin_api_error(self):
        """GarminAPIError includes status code."""
        error = GarminAPIError("API failed", status_code=500)
        assert error.status_code == 500
        assert "API failed" in str(error)

    def test_garmin_auth_error_is_api_error(self):
        """GarminAuthError inherits from GarminAPIError."""
        error = GarminAuthError("Auth failed")
        assert isinstance(error, GarminAPIError)

    def test_garmin_rate_limit_error(self):
        """GarminRateLimitError for 429 responses."""
        error = GarminRateLimitError("Too many requests")
        assert isinstance(error, GarminAPIError)


# =============================================================================
# CLI Integration Tests
# =============================================================================


class TestCLIIntegration:
    """Tests for CLI command handler."""

    def test_cmd_garmin_status_not_configured(self, capsys):
        """garmin status shows not configured message."""
        from atlas.health.cli import cmd_garmin
        import argparse

        args = argparse.Namespace(action="status")

        # Patch at the point of import in cmd_garmin
        with patch(
            "atlas.health.garmin.GarminService"
        ) as MockService:
            mock_instance = MockService.return_value
            mock_instance.is_configured.return_value = False
            mock_instance.has_valid_token.return_value = False

            cmd_garmin(args)

            captured = capsys.readouterr()
            assert "GARMIN CONNECT STATUS" in captured.out
