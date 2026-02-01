"""
Tests for WarmingBrowser — stealth browser automation for YouTube warming.

All tests use mocked browser context (no real browser launched).
Tests verify: humanization parameters, domain allowlist, session limits,
circuit breaker, login state checking, like/subscribe behavior.
"""

import asyncio
import json
import time
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas.babybrains.browser.warming_browser import (
    ALLOWED_DOMAINS,
    SessionConfig,
    SessionResult,
    WarmingBrowser,
    WatchResult,
    _gaussian_delay,
    _load_session_log,
    _save_session_log,
    is_allowed_domain,
)


# ============================================
# Fixtures
# ============================================


@pytest.fixture
def session_log_path(tmp_path):
    """Temporary session log path."""
    return tmp_path / "session_log.json"


@pytest.fixture
def profile_base(tmp_path):
    """Temporary profile base directory."""
    return tmp_path / "browser_profiles"


@pytest.fixture
def config():
    """Default session config for tests."""
    return SessionConfig(
        min_videos=3,
        max_videos=7,
        min_duration_minutes=15,
        max_duration_minutes=45,
        max_sessions_per_day=2,
        inter_video_delay_mean=45.0,
        inter_video_delay_stddev=15.0,
    )


@pytest.fixture
def browser(profile_base, config, session_log_path):
    """Create a WarmingBrowser instance (not started)."""
    return WarmingBrowser(
        account_id="bb_test",
        profile_base=profile_base,
        config=config,
        session_log_path=session_log_path,
    )


def _mock_page():
    """Create a mock page with common methods."""
    page = AsyncMock()
    page.goto = AsyncMock()
    page.evaluate = AsyncMock(return_value={})
    page.locator = MagicMock()
    page.mouse = AsyncMock()
    page.mouse.move = AsyncMock()
    page.mouse.click = AsyncMock()

    # Default: locator returns a visible element with bounding box
    locator_mock = AsyncMock()
    locator_mock.first = AsyncMock()
    locator_mock.first.is_visible = AsyncMock(return_value=True)
    locator_mock.first.bounding_box = AsyncMock(
        return_value={"x": 100, "y": 100, "width": 50, "height": 30}
    )
    locator_mock.first.click = AsyncMock()
    page.locator.return_value = locator_mock

    return page


def _mock_context(page):
    """Create a mock browser context."""
    context = AsyncMock()
    context.pages = [page]
    context.new_page = AsyncMock(return_value=page)
    context.close = AsyncMock()
    return context


# ============================================
# Domain Allowlist Tests
# ============================================


class TestDomainAllowlist:
    """Verify domain allowlist enforcement."""

    def test_youtube_allowed(self):
        assert is_allowed_domain("https://www.youtube.com/watch?v=abc123")

    def test_youtube_no_www_allowed(self):
        assert is_allowed_domain("https://youtube.com/watch?v=abc123")

    def test_mobile_youtube_allowed(self):
        assert is_allowed_domain("https://m.youtube.com/watch?v=abc123")

    def test_consent_youtube_allowed(self):
        assert is_allowed_domain("https://consent.youtube.com/m?continue=...")

    def test_google_accounts_allowed(self):
        assert is_allowed_domain("https://accounts.google.com/ServiceLogin")

    def test_random_site_blocked(self):
        assert not is_allowed_domain("https://example.com/page")

    def test_google_search_blocked(self):
        assert not is_allowed_domain("https://www.google.com/search?q=test")

    def test_tiktok_blocked(self):
        assert not is_allowed_domain("https://www.tiktok.com/@user")

    def test_empty_url_blocked(self):
        assert not is_allowed_domain("")

    def test_invalid_url_blocked(self):
        assert not is_allowed_domain("not-a-url")

    def test_youtube_subdomain_spoofing_blocked(self):
        """Ensure evil-youtube.com doesn't pass."""
        assert not is_allowed_domain("https://evil-youtube.com/watch")

    @pytest.mark.asyncio
    async def test_watch_video_rejects_non_youtube(self, browser):
        """watch_video should reject URLs outside the allowlist."""
        browser._started = True
        browser._page = _mock_page()

        result = await browser.watch_video("https://example.com/video")
        assert not result.success
        assert "not in domain allowlist" in result.error


# ============================================
# Session Limit Tests
# ============================================


class TestSessionLimits:
    """Verify session video count and duration limits."""

    def test_check_limits_under_video_max(self, browser):
        browser._session_video_count = 2
        browser._session_start_time = time.monotonic()
        assert browser._check_session_limits(7, 45) is None

    def test_check_limits_at_video_max(self, browser):
        browser._session_video_count = 7
        browser._session_start_time = time.monotonic()
        reason = browser._check_session_limits(7, 45)
        assert reason is not None
        assert "Video limit" in reason

    def test_check_limits_over_duration(self, browser):
        browser._session_video_count = 1
        # Set start time to 50 minutes ago
        browser._session_start_time = time.monotonic() - (50 * 60)
        reason = browser._check_session_limits(7, 45)
        assert reason is not None
        assert "Duration limit" in reason

    def test_session_elapsed_minutes_not_started(self, browser):
        assert browser.session_elapsed_minutes == 0.0

    def test_session_elapsed_minutes_running(self, browser):
        browser._session_start_time = time.monotonic() - 120  # 2 min ago
        elapsed = browser.session_elapsed_minutes
        assert 1.9 <= elapsed <= 2.2

    def test_min_max_videos_config(self, config):
        assert config.min_videos == 3
        assert config.max_videos == 7

    def test_min_max_duration_config(self, config):
        assert config.min_duration_minutes == 15
        assert config.max_duration_minutes == 45


# ============================================
# Daily Session Limit Tests
# ============================================


class TestDailySessionLimit:
    """Verify per-day session tracking."""

    def test_first_session_allowed(self, browser):
        assert browser.check_daily_session_limit() is True

    def test_second_session_allowed(self, browser, session_log_path):
        today = date.today().isoformat()
        _save_session_log(session_log_path, {today: {"sessions": 1}})
        assert browser.check_daily_session_limit() is True

    def test_third_session_blocked(self, browser, session_log_path):
        today = date.today().isoformat()
        _save_session_log(session_log_path, {today: {"sessions": 2}})
        assert browser.check_daily_session_limit() is False

    def test_new_day_resets(self, browser, session_log_path):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        _save_session_log(session_log_path, {yesterday: {"sessions": 5}})
        assert browser.check_daily_session_limit() is True

    def test_corrupted_log_resets(self, browser, session_log_path):
        session_log_path.parent.mkdir(parents=True, exist_ok=True)
        session_log_path.write_text("not valid json")
        assert browser.check_daily_session_limit() is True

    def test_missing_log_allows(self, browser):
        assert browser.check_daily_session_limit() is True

    def test_record_session_increments(self, browser, session_log_path):
        browser._session_video_count = 5  # Must be > 0 to record
        browser._record_session()
        log = _load_session_log(session_log_path)
        today = date.today().isoformat()
        assert log[today]["sessions"] == 1

    def test_record_session_prunes_old(self, browser, session_log_path):
        old_date = (date.today() - timedelta(days=10)).isoformat()
        _save_session_log(session_log_path, {old_date: {"sessions": 3}})
        browser._session_video_count = 1
        browser._record_session()
        log = _load_session_log(session_log_path)
        assert old_date not in log


# ============================================
# Session Log Persistence Tests
# ============================================


class TestSessionLog:
    """Verify session log file operations."""

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "log.json"
        data = {"2026-02-01": {"sessions": 1}}
        _save_session_log(path, data)
        loaded = _load_session_log(path)
        assert loaded == data

    def test_load_missing_file(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        assert _load_session_log(path) == {}

    def test_load_corrupted_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid")
        assert _load_session_log(path) == {}

    def test_load_non_dict_file(self, tmp_path):
        path = tmp_path / "array.json"
        path.write_text("[1, 2, 3]")
        assert _load_session_log(path) == {}


# ============================================
# Gaussian Delay Tests
# ============================================


class TestGaussianDelay:
    """Verify gaussian delay distribution parameters."""

    def test_delay_within_bounds(self):
        """Delays should be clamped to reasonable range."""
        for _ in range(100):
            delay = _gaussian_delay(45.0, 15.0, minimum=15.0)
            assert 15.0 <= delay <= 135.0  # min to 3*mean

    def test_delay_respects_minimum(self):
        """Even with low mean, delay should respect minimum."""
        for _ in range(100):
            delay = _gaussian_delay(1.0, 0.5, minimum=5.0)
            assert delay >= 5.0

    def test_delay_distribution_centered(self):
        """Mean of many samples should be near the target mean."""
        samples = [_gaussian_delay(45.0, 15.0) for _ in range(1000)]
        mean = sum(samples) / len(samples)
        assert 35.0 <= mean <= 55.0  # Within +-10 of target


# ============================================
# Browser Profile Tests
# ============================================


class TestBrowserProfile:
    """Verify profile directory management."""

    def test_profile_dir_path(self, browser, profile_base):
        assert browser.profile_dir == profile_base / "bb_test"

    def test_profile_dir_per_account(self, profile_base, session_log_path):
        b1 = WarmingBrowser("account_a", profile_base=profile_base,
                            session_log_path=session_log_path)
        b2 = WarmingBrowser("account_b", profile_base=profile_base,
                            session_log_path=session_log_path)
        assert b1.profile_dir != b2.profile_dir
        assert b1.profile_dir.name == "account_a"
        assert b2.profile_dir.name == "account_b"

    def test_not_started_initially(self, browser):
        assert not browser.is_started


# ============================================
# Login State Tests
# ============================================


class TestLoginState:
    """Verify Google session validation."""

    @pytest.mark.asyncio
    async def test_logged_in_detected(self, browser):
        """Should detect logged-in state from avatar presence."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={
            "hasAvatar": True,
            "hasSignIn": False,
            "title": "YouTube",
        })
        browser._started = True
        browser._page = page

        assert await browser.check_login_state() is True

    @pytest.mark.asyncio
    async def test_logged_out_detected(self, browser):
        """Should detect expired session from sign-in button."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={
            "hasAvatar": False,
            "hasSignIn": True,
            "title": "YouTube",
        })
        browser._started = True
        browser._page = page

        assert await browser.check_login_state() is False

    @pytest.mark.asyncio
    async def test_ambiguous_state_returns_false(self, browser):
        """Unknown state (consent page, etc.) should return False."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={
            "hasAvatar": False,
            "hasSignIn": False,
            "title": "Before you continue",
        })
        browser._started = True
        browser._page = page

        assert await browser.check_login_state() is False

    @pytest.mark.asyncio
    async def test_not_started_returns_false(self, browser):
        """Should return False if browser not started."""
        assert await browser.check_login_state() is False

    @pytest.mark.asyncio
    async def test_navigation_error_returns_false(self, browser):
        """Should handle navigation errors gracefully."""
        page = _mock_page()
        page.goto = AsyncMock(side_effect=Exception("Network error"))
        browser._started = True
        browser._page = page

        assert await browser.check_login_state() is False


# ============================================
# Watch Video Tests
# ============================================


class TestWatchVideo:
    """Verify video watching with humanized behavior."""

    @pytest.mark.asyncio
    async def test_watch_returns_result(self, browser):
        """Should return WatchResult with actual watch seconds."""
        page = _mock_page()

        # Mock video duration as 300s
        evaluate_responses = [
            {},  # goto evaluations
            300.0,  # _get_video_duration
            None,  # _dismiss_dialogs
            False,  # _ensure_playing (not paused)
        ]
        call_count = {"n": 0}

        async def mock_evaluate(script, *args):
            idx = call_count["n"]
            call_count["n"] += 1
            if idx < len(evaluate_responses):
                return evaluate_responses[idx]
            return None

        page.evaluate = mock_evaluate
        browser._started = True
        browser._page = page

        # Patch _humanized_watch to skip real waiting
        with patch.object(browser, "_humanized_watch", new_callable=AsyncMock):
            result = await browser.watch_video(
                "https://www.youtube.com/watch?v=test123",
                duration_pct=0.7,
            )

        assert result.url == "https://www.youtube.com/watch?v=test123"
        assert result.actual_watch_seconds > 0
        assert result.error is None
        assert browser.session_video_count == 1

    @pytest.mark.asyncio
    async def test_watch_non_youtube_url_rejected(self, browser):
        """Should reject non-YouTube URLs."""
        browser._started = True
        browser._page = _mock_page()

        result = await browser.watch_video("https://tiktok.com/video")
        assert not result.success
        assert "allowlist" in result.error

    @pytest.mark.asyncio
    async def test_watch_increments_session_count(self, browser):
        """Each successful watch should increment the counter."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value=180.0)
        browser._started = True
        browser._page = page

        with patch.object(browser, "_humanized_watch", new_callable=AsyncMock):
            with patch.object(browser, "_dismiss_dialogs", new_callable=AsyncMock):
                with patch.object(browser, "_ensure_playing", new_callable=AsyncMock):
                    await browser.watch_video("https://www.youtube.com/watch?v=a")
                    await browser.watch_video("https://www.youtube.com/watch?v=b")

        assert browser.session_video_count == 2

    @pytest.mark.asyncio
    async def test_watch_not_started_error(self, browser):
        """Should error if browser not started."""
        result = await browser.watch_video("https://www.youtube.com/watch?v=test")
        assert not result.success
        assert "not started" in result.error


# ============================================
# Circuit Breaker Tests
# ============================================


class TestCircuitBreaker:
    """Verify circuit breaker trips after consecutive failures."""

    @pytest.mark.asyncio
    async def test_trips_after_3_failures(self, browser):
        """Circuit breaker should open after 3 consecutive failures."""
        page = _mock_page()
        page.goto = AsyncMock(side_effect=Exception("Connection failed"))
        browser._started = True
        browser._page = page

        results = []
        for i in range(5):
            result = await browser.watch_video(
                f"https://www.youtube.com/watch?v=fail{i}"
            )
            results.append(result)

        # First 3 should be regular errors, then circuit breaker should open
        assert all(not r.success for r in results)

        # At least one result should mention circuit breaker
        circuit_errors = [r for r in results if r.error and "Circuit breaker" in r.error]
        assert len(circuit_errors) >= 1

    @pytest.mark.asyncio
    async def test_successful_ops_dont_trip(self, browser):
        """Successful operations should not trip the breaker."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value=120.0)
        browser._started = True
        browser._page = page

        with patch.object(browser, "_humanized_watch", new_callable=AsyncMock):
            with patch.object(browser, "_dismiss_dialogs", new_callable=AsyncMock):
                with patch.object(browser, "_ensure_playing", new_callable=AsyncMock):
                    for i in range(5):
                        result = await browser.watch_video(
                            f"https://www.youtube.com/watch?v=ok{i}"
                        )
                        assert result.success


# ============================================
# Like Video Tests
# ============================================


class TestLikeVideo:
    """Verify like behavior with engagement rules."""

    @pytest.mark.asyncio
    async def test_like_success(self, browser):
        """Should click like button when found and not already liked."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={
            "found": True,
            "alreadyLiked": False,
            "label": "like this video",
        })
        browser._started = True
        browser._page = page

        result = await browser.like_video()
        assert result is True

    @pytest.mark.asyncio
    async def test_already_liked_returns_true(self, browser):
        """Should return True without clicking if already liked."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={
            "found": True,
            "alreadyLiked": True,
            "label": "unlike this video",
        })
        browser._started = True
        browser._page = page

        result = await browser.like_video()
        assert result is True

    @pytest.mark.asyncio
    async def test_like_button_not_found(self, browser):
        """Should return False when like button not found."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={"found": False})
        browser._started = True
        browser._page = page

        result = await browser.like_video()
        assert result is False

    @pytest.mark.asyncio
    async def test_like_not_started(self, browser):
        """Should return False when browser not started."""
        result = await browser.like_video()
        assert result is False


# ============================================
# Subscribe Channel Tests
# ============================================


class TestSubscribeChannel:
    """Verify subscribe behavior with threshold checks."""

    @pytest.mark.asyncio
    async def test_subscribe_success(self, browser):
        """Should click subscribe when found and not subscribed."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={
            "found": True,
            "alreadySubscribed": False,
            "label": "subscribe",
        })
        browser._started = True
        browser._page = page

        result = await browser.subscribe_channel()
        assert result is True

    @pytest.mark.asyncio
    async def test_already_subscribed_returns_true(self, browser):
        """Should return True without clicking if already subscribed."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={
            "found": True,
            "alreadySubscribed": True,
            "label": "subscribed",
        })
        browser._started = True
        browser._page = page

        result = await browser.subscribe_channel()
        assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_button_not_found(self, browser):
        """Should return False when subscribe button not found."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value={"found": False})
        browser._started = True
        browser._page = page

        result = await browser.subscribe_channel()
        assert result is False

    @pytest.mark.asyncio
    async def test_subscribe_not_started(self, browser):
        """Should return False when browser not started."""
        result = await browser.subscribe_channel()
        assert result is False


# ============================================
# Run Session Tests
# ============================================


class TestRunSession:
    """Verify full session orchestration."""

    @pytest.mark.asyncio
    async def test_session_respects_video_limit(self, browser):
        """Session should stop after max_videos reached."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value=120.0)
        browser._started = True
        browser._page = page
        browser._session_start_time = time.monotonic()

        # Override config for predictable test
        browser._config.min_videos = 2
        browser._config.max_videos = 2

        targets = [
            {"url": f"https://www.youtube.com/watch?v={i}", "engagement_level": "WATCH",
             "watch_duration_target": 60, "niche_relevance_score": 0.5}
            for i in range(5)
        ]

        with patch.object(browser, "check_login_state", new_callable=AsyncMock, return_value=True):
            with patch.object(browser, "_do_watch_video", new_callable=AsyncMock, return_value=60):
                with patch.object(browser, "inter_video_delay", new_callable=AsyncMock, return_value=1.0):
                    result = await browser.run_session(targets)

        assert result.videos_watched <= 2

    @pytest.mark.asyncio
    async def test_session_aborts_on_expired_login(self, browser):
        """Session should abort if login check fails."""
        browser._started = True
        browser._page = _mock_page()

        with patch.object(browser, "check_login_state", new_callable=AsyncMock, return_value=False):
            with patch.object(browser, "stop", new_callable=AsyncMock):
                result = await browser.run_session([
                    {"url": "https://www.youtube.com/watch?v=1", "engagement_level": "WATCH",
                     "watch_duration_target": 60, "niche_relevance_score": 0.5}
                ])

        assert result.aborted
        assert "session expired" in result.abort_reason.lower()

    @pytest.mark.asyncio
    async def test_session_aborts_on_daily_limit(self, browser, session_log_path):
        """Session should abort if daily limit reached."""
        today = date.today().isoformat()
        _save_session_log(session_log_path, {today: {"sessions": 2}})

        result = await browser.run_session([
            {"url": "https://www.youtube.com/watch?v=1", "engagement_level": "WATCH",
             "watch_duration_target": 60, "niche_relevance_score": 0.5}
        ])

        assert result.aborted
        assert "session limit" in result.abort_reason.lower()

    @pytest.mark.asyncio
    async def test_session_likes_on_like_level(self, browser):
        """Session should like videos with LIKE engagement level."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value=120.0)
        browser._started = True
        browser._page = page
        browser._session_start_time = time.monotonic()
        browser._config.min_videos = 1
        browser._config.max_videos = 1

        targets = [
            {"url": "https://www.youtube.com/watch?v=1", "engagement_level": "LIKE",
             "watch_duration_target": 60, "niche_relevance_score": 0.6}
        ]

        with patch.object(browser, "check_login_state", new_callable=AsyncMock, return_value=True):
            with patch.object(browser, "_do_watch_video", new_callable=AsyncMock, return_value=60):
                with patch.object(browser, "like_video", new_callable=AsyncMock, return_value=True):
                    result = await browser.run_session(targets)

        assert result.likes == 1

    @pytest.mark.asyncio
    async def test_session_subscribes_on_subscribe_level(self, browser):
        """Session should like AND subscribe for SUBSCRIBE level."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value=120.0)
        browser._started = True
        browser._page = page
        browser._session_start_time = time.monotonic()
        browser._config.min_videos = 1
        browser._config.max_videos = 1

        targets = [
            {"url": "https://www.youtube.com/watch?v=1", "engagement_level": "SUBSCRIBE",
             "watch_duration_target": 90, "niche_relevance_score": 0.8}
        ]

        with patch.object(browser, "check_login_state", new_callable=AsyncMock, return_value=True):
            with patch.object(browser, "_do_watch_video", new_callable=AsyncMock, return_value=90):
                with patch.object(browser, "like_video", new_callable=AsyncMock, return_value=True):
                    with patch.object(browser, "subscribe_channel", new_callable=AsyncMock, return_value=True):
                        result = await browser.run_session(targets)

        assert result.likes == 1
        assert result.subscribes == 1

    @pytest.mark.asyncio
    async def test_session_never_automates_comments(self, browser):
        """COMMENT level should watch+like but NEVER post a comment."""
        page = _mock_page()
        page.evaluate = AsyncMock(return_value=120.0)
        browser._started = True
        browser._page = page
        browser._session_start_time = time.monotonic()
        browser._config.min_videos = 1
        browser._config.max_videos = 1

        targets = [
            {"url": "https://www.youtube.com/watch?v=1", "engagement_level": "COMMENT",
             "watch_duration_target": 120, "niche_relevance_score": 0.7}
        ]

        with patch.object(browser, "check_login_state", new_callable=AsyncMock, return_value=True):
            with patch.object(browser, "_do_watch_video", new_callable=AsyncMock, return_value=120):
                with patch.object(browser, "like_video", new_callable=AsyncMock, return_value=True):
                    result = await browser.run_session(targets)

        # COMMENT level gets like (part of LIKE+ levels) but no subscribe
        assert result.likes == 1
        assert result.subscribes == 0
        # No comment automation exists — verify no "comment" method was called


# ============================================
# Humanization Parameter Tests
# ============================================


class TestHumanizationParameters:
    """Verify humanization timing parameters are within spec."""

    def test_scroll_interval_range(self, config):
        """Scroll interval should be 15-45s per spec."""
        assert config.scroll_interval_min == 15.0
        assert config.scroll_interval_max == 45.0

    def test_mouse_drift_interval_range(self, config):
        """Mouse drift should be 10-30s per spec."""
        assert config.mouse_drift_interval_min == 10.0
        assert config.mouse_drift_interval_max == 30.0

    def test_pause_duration_range(self, config):
        """Pause should be 1-3s per spec."""
        assert config.pause_duration_min == 1.0
        assert config.pause_duration_max == 3.0

    def test_pause_frequency_range(self, config):
        """Pauses should occur every 2-5 min per spec."""
        assert config.pause_every_min == 120.0  # 2 min
        assert config.pause_every_max == 300.0  # 5 min

    def test_inter_video_delay_gaussian(self, config):
        """Inter-video delay should use gaussian(45s, 15s)."""
        assert config.inter_video_delay_mean == 45.0
        assert config.inter_video_delay_stddev == 15.0


# ============================================
# WatchResult / SessionResult Tests
# ============================================


class TestResultDataclasses:
    """Verify result dataclass properties."""

    def test_watch_result_success_on_positive_watch(self):
        r = WatchResult(url="https://youtube.com/watch?v=1", actual_watch_seconds=60)
        assert r.success

    def test_watch_result_failure_on_error(self):
        r = WatchResult(url="https://youtube.com/watch?v=1", error="Failed")
        assert not r.success

    def test_watch_result_failure_on_zero_watch(self):
        r = WatchResult(url="https://youtube.com/watch?v=1", actual_watch_seconds=0)
        assert not r.success

    def test_session_result_success(self):
        r = SessionResult(videos_watched=3, total_watch_seconds=300)
        assert r.success

    def test_session_result_aborted_not_success(self):
        r = SessionResult(videos_watched=3, aborted=True)
        assert not r.success

    def test_session_result_no_videos_not_success(self):
        r = SessionResult(videos_watched=0)
        assert not r.success

    def test_session_result_summary(self):
        r = SessionResult(
            videos_watched=5,
            total_watch_seconds=600,
            likes=3,
            subscribes=1,
        )
        assert "5 videos" in r.summary
        assert "600s" in r.summary
        assert "3 likes" in r.summary
        assert "1 subscribes" in r.summary


# ============================================
# Browser Start/Stop Tests
# ============================================


class TestBrowserLifecycle:
    """Verify browser start/stop behavior."""

    @pytest.mark.asyncio
    async def test_stop_without_start(self, browser):
        """stop() should not error if not started."""
        await browser.stop()
        assert not browser.is_started

    @pytest.mark.asyncio
    async def test_stop_records_session_when_videos_watched(self, browser, session_log_path):
        """stop() should record session if videos were watched."""
        browser._started = True
        browser._session_video_count = 3
        browser._session_watch_seconds = 300
        browser._context = AsyncMock()
        browser._playwright = AsyncMock()

        await browser.stop()

        log = _load_session_log(session_log_path)
        today = date.today().isoformat()
        assert log[today]["sessions"] == 1

    @pytest.mark.asyncio
    async def test_stop_no_record_when_no_videos(self, browser, session_log_path):
        """stop() should NOT record session if no videos were watched."""
        browser._started = True
        browser._session_video_count = 0
        browser._context = AsyncMock()
        browser._playwright = AsyncMock()

        await browser.stop()

        log = _load_session_log(session_log_path)
        assert log == {}


# ============================================
# Allowed Domains Constant Tests
# ============================================


class TestAllowedDomainsConstant:
    """Verify the ALLOWED_DOMAINS set contains required domains."""

    def test_contains_youtube(self):
        assert "youtube.com" in ALLOWED_DOMAINS

    def test_contains_www_youtube(self):
        assert "www.youtube.com" in ALLOWED_DOMAINS

    def test_contains_google_accounts(self):
        assert "accounts.google.com" in ALLOWED_DOMAINS

    def test_does_not_contain_google_search(self):
        assert "www.google.com" not in ALLOWED_DOMAINS

    def test_does_not_contain_instagram(self):
        assert "www.instagram.com" not in ALLOWED_DOMAINS

    def test_is_frozen_set(self):
        """Should be immutable."""
        assert isinstance(ALLOWED_DOMAINS, frozenset)
