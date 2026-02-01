"""
Tests for S2.3: Warming Integration + MCP Tools.

Integration tests with mocked WarmingBrowser. Tests the full flow:
generate targets → browser watches → actions logged to DB.
Error handling: expired cookies → session aborts with WARNING.
CLI command test. DB session logging.
"""

import asyncio
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas.babybrains import db
from atlas.babybrains.browser.warming_browser import (
    SessionResult,
    WatchResult,
)
from atlas.babybrains.warming.service import WarmingService


# ============================================
# DB HELPER TESTS
# ============================================


class TestLogWarmingSession:
    """Test db.log_warming_session()."""

    def test_log_successful_session(self, bb_conn):
        action_id = db.log_warming_session(
            bb_conn,
            platform="youtube",
            videos_watched=5,
            total_watch_seconds=600,
            likes=3,
            subscribes=1,
            success=True,
        )
        assert action_id > 0

        # Verify stored
        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE id = ?", (action_id,)
        )
        row = cursor.fetchone()
        assert row["action_type"] == "session_complete"
        assert row["actual_watch_seconds"] == 600
        assert "5 videos" in row["engagement_result"]
        assert "3 likes" in row["engagement_result"]

    def test_log_failed_session(self, bb_conn):
        action_id = db.log_warming_session(
            bb_conn,
            platform="youtube",
            success=False,
            abort_reason="Google session expired — manual re-login required",
        )
        assert action_id > 0

        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE id = ?", (action_id,)
        )
        row = cursor.fetchone()
        assert row["action_type"] == "session_failure"
        assert "expired" in row["engagement_result"]
        assert row["actual_watch_seconds"] is None

    def test_log_failed_session_cookie_expiry(self, bb_conn):
        db.log_warming_session(
            bb_conn,
            platform="youtube",
            success=False,
            abort_reason="cookie_expiry: Google session cookies have expired",
        )

        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE action_type = 'session_failure'"
        )
        row = cursor.fetchone()
        assert "cookie_expiry" in row["engagement_result"]

    def test_log_failed_session_circuit_breaker(self, bb_conn):
        db.log_warming_session(
            bb_conn,
            platform="youtube",
            success=False,
            abort_reason="circuit_breaker: Too many consecutive failures",
        )

        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE action_type = 'session_failure'"
        )
        row = cursor.fetchone()
        assert "circuit_breaker" in row["engagement_result"]

    def test_log_failed_session_domain_violation(self, bb_conn):
        db.log_warming_session(
            bb_conn,
            platform="youtube",
            success=False,
            abort_reason="domain_violation: URL not in domain allowlist",
        )

        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE action_type = 'session_failure'"
        )
        row = cursor.fetchone()
        assert "domain_violation" in row["engagement_result"]


class TestGetBrowserSessionStats:
    """Test db.get_browser_session_stats()."""

    def test_empty_stats(self, bb_conn):
        stats = db.get_browser_session_stats(bb_conn, days=7)
        assert stats["successful_sessions"] == 0
        assert stats["failed_sessions"] == 0
        assert stats["total_session_watch_minutes"] == 0.0
        assert stats["last_session"] is None
        assert stats["last_failure"] is None

    def test_stats_after_successful_session(self, bb_conn):
        db.log_warming_session(
            bb_conn,
            platform="youtube",
            videos_watched=5,
            total_watch_seconds=600,
            success=True,
        )

        stats = db.get_browser_session_stats(bb_conn, days=7)
        assert stats["successful_sessions"] == 1
        assert stats["failed_sessions"] == 0
        assert stats["total_session_watch_minutes"] == 10.0
        assert stats["last_session"] is not None
        assert stats["last_session"]["type"] == "session_complete"

    def test_stats_after_failed_session(self, bb_conn):
        db.log_warming_session(
            bb_conn,
            platform="youtube",
            success=False,
            abort_reason="Cookie expiry",
        )

        stats = db.get_browser_session_stats(bb_conn, days=7)
        assert stats["successful_sessions"] == 0
        assert stats["failed_sessions"] == 1
        assert stats["last_failure"] is not None
        assert stats["last_failure"]["reason"] == "Cookie expiry"

    def test_stats_mixed_sessions(self, bb_conn):
        db.log_warming_session(
            bb_conn, platform="youtube",
            videos_watched=3, total_watch_seconds=300,
            success=True,
        )
        db.log_warming_session(
            bb_conn, platform="youtube",
            success=False,
            abort_reason="Circuit breaker tripped",
        )
        db.log_warming_session(
            bb_conn, platform="youtube",
            videos_watched=5, total_watch_seconds=600,
            success=True,
        )

        stats = db.get_browser_session_stats(bb_conn, days=7)
        assert stats["successful_sessions"] == 2
        assert stats["failed_sessions"] == 1
        assert stats["total_session_watch_minutes"] == 15.0  # (300+600)/60


# ============================================
# WARMING SERVICE BROWSER SESSION TESTS
# ============================================


def _make_session_result(
    videos_watched=3,
    total_watch_seconds=360,
    likes=2,
    subscribes=0,
    aborted=False,
    abort_reason=None,
    watch_results=None,
):
    """Helper to create a SessionResult for testing."""
    if watch_results is None:
        watch_results = [
            WatchResult(
                url=f"https://www.youtube.com/watch?v=test{i}",
                actual_watch_seconds=120,
                liked=(i < likes),
                subscribed=False,
            )
            for i in range(videos_watched)
        ]

    return SessionResult(
        videos_watched=videos_watched,
        total_watch_seconds=total_watch_seconds,
        likes=likes,
        subscribes=subscribes,
        watch_results=watch_results,
        aborted=aborted,
        abort_reason=abort_reason,
    )


class TestRunBrowserSession:
    """Test WarmingService.run_browser_session() with mocked browser."""

    def _add_test_targets(self, conn, count=5):
        """Add test warming targets to the DB."""
        target_ids = []
        for i in range(count):
            tid = db.add_warming_target(
                conn,
                platform="youtube",
                url=f"https://www.youtube.com/watch?v=test{i}",
                video_title=f"Test Video {i}",
                engagement_level="LIKE" if i % 2 == 0 else "WATCH",
                watch_duration_target=120,
                niche_relevance_score=0.7,
            )
            target_ids.append(tid)
        return target_ids

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_successful_session(self, MockBrowser, bb_conn):
        """Full flow: targets → browser watches → actions logged."""
        target_ids = self._add_test_targets(bb_conn, count=5)

        # Mock browser
        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        session_result = _make_session_result(
            videos_watched=3,
            total_watch_seconds=360,
            likes=2,
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_browser_session(platform="youtube"))

        assert result["status"] == "success"
        assert result["videos_watched"] == 3
        assert result["likes"] == 2
        assert result["actions_logged"] == 5  # 3 watches + 2 likes

        # Verify actions logged to DB
        stats = db.get_warming_stats(bb_conn, days=1)
        assert stats["watches"] == 3
        assert stats["likes"] == 2

        # Verify session logged
        session_stats = db.get_browser_session_stats(bb_conn, days=1)
        assert session_stats["successful_sessions"] == 1

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_target_statuses_updated(self, MockBrowser, bb_conn):
        """Successful watches mark targets as completed."""
        target_ids = self._add_test_targets(bb_conn, count=3)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        watch_results = [
            WatchResult(url="https://www.youtube.com/watch?v=test0",
                        actual_watch_seconds=120, liked=False),
            WatchResult(url="https://www.youtube.com/watch?v=test1",
                        actual_watch_seconds=120, liked=False),
            WatchResult(url="https://www.youtube.com/watch?v=test2",
                        actual_watch_seconds=0,
                        error="Circuit breaker OPEN"),
        ]

        session_result = SessionResult(
            videos_watched=2,
            total_watch_seconds=240,
            watch_results=watch_results,
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        asyncio.run(service.run_browser_session(platform="youtube"))

        # Check target statuses
        targets = db.get_warming_targets(bb_conn)
        statuses = {t.id: t.status for t in targets}
        assert statuses[target_ids[0]] == "completed"
        assert statuses[target_ids[1]] == "completed"
        assert statuses[target_ids[2]] == "skipped"  # Error → skipped

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_expired_cookies_abort(self, MockBrowser, bb_conn):
        """Expired cookies → session aborts with WARNING logged to DB."""
        self._add_test_targets(bb_conn, count=3)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        session_result = SessionResult(
            aborted=True,
            abort_reason="Google session expired — manual re-login required",
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_browser_session(platform="youtube"))

        assert result["status"] == "aborted"
        assert "expired" in result["abort_reason"]

        # Verify failure logged to DB
        session_stats = db.get_browser_session_stats(bb_conn, days=1)
        assert session_stats["failed_sessions"] == 1
        assert "expired" in session_stats["last_failure"]["reason"]

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_daily_limit_abort(self, MockBrowser, bb_conn):
        """Daily session limit reached → session aborts."""
        self._add_test_targets(bb_conn, count=3)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        session_result = SessionResult(
            aborted=True,
            abort_reason="Daily session limit reached",
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_browser_session(platform="youtube"))

        assert result["status"] == "aborted"
        assert "Daily session limit" in result["abort_reason"]

    def test_no_targets_returns_no_targets(self, bb_conn):
        """No pending targets → returns no_targets status."""
        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_browser_session(platform="youtube"))
        assert result["status"] == "no_targets"

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", False)
    def test_browser_not_available(self, bb_conn):
        """Browser deps not installed → error logged to DB."""
        self._add_test_targets(bb_conn, count=3)

        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_browser_session(platform="youtube"))

        assert result["status"] == "error"
        assert "not installed" in result["message"]

        # Verify failure logged
        session_stats = db.get_browser_session_stats(bb_conn, days=1)
        assert session_stats["failed_sessions"] == 1

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_browser_crash_logged(self, MockBrowser, bb_conn):
        """Browser crash → failure logged to DB."""
        self._add_test_targets(bb_conn, count=3)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance
        mock_instance.run_session = AsyncMock(
            side_effect=RuntimeError("Browser process died")
        )
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_browser_session(platform="youtube"))

        assert result["status"] == "error"
        assert "crashed" in result["message"]

        session_stats = db.get_browser_session_stats(bb_conn, days=1)
        assert session_stats["failed_sessions"] == 1

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_subscribe_actions_logged(self, MockBrowser, bb_conn):
        """Subscribe actions are logged with correct target IDs."""
        target_ids = self._add_test_targets(bb_conn, count=2)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        watch_results = [
            WatchResult(
                url="https://www.youtube.com/watch?v=test0",
                actual_watch_seconds=120,
                liked=True,
                subscribed=True,
            ),
            WatchResult(
                url="https://www.youtube.com/watch?v=test1",
                actual_watch_seconds=100,
                liked=False,
                subscribed=False,
            ),
        ]

        session_result = SessionResult(
            videos_watched=2,
            total_watch_seconds=220,
            likes=1,
            subscribes=1,
            watch_results=watch_results,
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_browser_session(platform="youtube"))

        # 2 watches + 1 like + 1 subscribe = 4 actions
        assert result["actions_logged"] == 4

        # Verify subscribe logged with correct target
        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE action_type = 'subscribe'"
        )
        sub_rows = cursor.fetchall()
        assert len(sub_rows) == 1
        assert sub_rows[0]["target_id"] == target_ids[0]

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_browser_stop_called_on_success(self, MockBrowser, bb_conn):
        """Browser.stop() is always called, even on success."""
        self._add_test_targets(bb_conn, count=1)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        session_result = _make_session_result(videos_watched=1, likes=0)
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        asyncio.run(service.run_browser_session(platform="youtube"))

        mock_instance.stop.assert_awaited_once()

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_browser_stop_called_on_crash(self, MockBrowser, bb_conn):
        """Browser.stop() is called even when session crashes."""
        self._add_test_targets(bb_conn, count=1)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance
        mock_instance.run_session = AsyncMock(
            side_effect=RuntimeError("Crash")
        )
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        asyncio.run(service.run_browser_session(platform="youtube"))

        mock_instance.stop.assert_awaited_once()

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_account_id_uses_platform(self, MockBrowser, bb_conn):
        """Browser is created with account_id matching platform."""
        self._add_test_targets(bb_conn, count=1)

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        session_result = _make_session_result(videos_watched=1, likes=0)
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        service = WarmingService(conn=bb_conn)
        asyncio.run(service.run_browser_session(platform="youtube"))

        MockBrowser.assert_called_once_with(account_id="bb_youtube")


# ============================================
# LOG DONE ENHANCEMENT TESTS
# ============================================


class TestLogDoneEnhanced:
    """Test enhanced log_done with detailed action logging."""

    def test_count_based_logging(self, bb_conn):
        """Original count-based logging still works."""
        service = WarmingService(conn=bb_conn)
        result = service.log_done("youtube", comments=2, likes=3)

        assert "2 comment(s)" in result["actions"]
        assert "3 like(s)" in result["actions"]

        stats = db.get_warming_stats(bb_conn, days=1)
        assert stats["comments"] == 2
        assert stats["likes"] == 3

    def test_detailed_action_logging(self, bb_conn):
        """Detailed action logging with target IDs and watch seconds."""
        # Add a target first
        target_id = db.add_warming_target(
            bb_conn,
            platform="youtube",
            url="https://youtube.com/watch?v=abc",
            video_title="Test",
        )

        service = WarmingService(conn=bb_conn)
        result = service.log_done(
            "youtube",
            actions_detail=[
                {
                    "target_id": target_id,
                    "action_type": "watch",
                    "actual_watch_seconds": 180,
                },
                {
                    "target_id": target_id,
                    "action_type": "like",
                },
            ],
        )

        assert "2 detailed action(s)" in result["actions"]

        # Verify with target_id
        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE target_id = ?",
            (target_id,),
        )
        rows = cursor.fetchall()
        assert len(rows) == 2

        watch_row = [r for r in rows if r["action_type"] == "watch"][0]
        assert watch_row["actual_watch_seconds"] == 180


# ============================================
# CLI TESTS
# ============================================


class TestCLIWarmingWatch:
    """Test CLI warming watch command."""

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_warming_watch_command(self, MockBrowser, bb_conn, capsys):
        """CLI warming watch runs browser session and prints results."""
        from atlas.babybrains.cli import cmd_warming_watch

        # Add targets
        db.add_warming_target(
            bb_conn,
            platform="youtube",
            url="https://www.youtube.com/watch?v=test1",
            video_title="Test",
        )

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        session_result = _make_session_result(
            videos_watched=3, total_watch_seconds=360, likes=2,
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        # Mock args
        args = MagicMock()
        args.platform = "youtube"

        # Mock get_conn to return our test conn
        with patch("atlas.babybrains.cli.get_conn", return_value=bb_conn):
            cmd_warming_watch(args)

        output = capsys.readouterr().out
        assert "STARTING WARMING SESSION" in output
        assert "Videos watched: 3" in output

    def test_warming_watch_no_targets(self, bb_conn, capsys):
        """CLI warming watch with no targets shows message."""
        from atlas.babybrains.cli import cmd_warming_watch

        args = MagicMock()
        args.platform = "youtube"

        with patch("atlas.babybrains.cli.get_conn", return_value=bb_conn):
            cmd_warming_watch(args)

        output = capsys.readouterr().out
        assert "No pending" in output

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_warming_watch_aborted(self, MockBrowser, bb_conn, capsys):
        """CLI warming watch shows abort reason."""
        from atlas.babybrains.cli import cmd_warming_watch

        db.add_warming_target(
            bb_conn,
            platform="youtube",
            url="https://www.youtube.com/watch?v=test1",
            video_title="Test",
        )

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        session_result = SessionResult(
            aborted=True,
            abort_reason="Google session expired — manual re-login required",
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        args = MagicMock()
        args.platform = "youtube"

        with patch("atlas.babybrains.cli.get_conn", return_value=bb_conn):
            cmd_warming_watch(args)

        output = capsys.readouterr().out
        assert "ABORTED" in output
        assert "expired" in output


# ============================================
# WARMING STATUS WITH BROWSER STATS TESTS
# ============================================


class TestWarmingStatusWithBrowserStats:
    """Test enhanced warming status includes browser session stats."""

    def test_status_includes_browser_stats(self, bb_conn):
        """Warming status dashboard includes browser session data."""
        # Log some sessions
        db.log_warming_session(
            bb_conn, platform="youtube",
            videos_watched=5, total_watch_seconds=600,
            success=True,
        )
        db.log_warming_session(
            bb_conn, platform="youtube",
            success=False,
            abort_reason="Cookie expiry",
        )

        browser_stats = db.get_browser_session_stats(bb_conn, days=7)
        warming_stats = db.get_warming_stats(bb_conn, days=7)

        # Combine like the MCP tool does
        warming_stats["browser_sessions"] = browser_stats

        assert "browser_sessions" in warming_stats
        assert warming_stats["browser_sessions"]["successful_sessions"] == 1
        assert warming_stats["browser_sessions"]["failed_sessions"] == 1

    def test_status_cli_shows_browser_stats(self, bb_conn, capsys):
        """CLI warming status shows browser session info."""
        from atlas.babybrains.cli import cmd_warming_status

        db.log_warming_session(
            bb_conn, platform="youtube",
            videos_watched=5, total_watch_seconds=600,
            success=True,
        )

        args = MagicMock()
        args.days = 7

        with patch("atlas.babybrains.cli.get_conn", return_value=bb_conn):
            cmd_warming_status(args)

        output = capsys.readouterr().out
        assert "BROWSER SESSIONS" in output
        assert "Successful: 1" in output


# ============================================
# FULL FLOW INTEGRATION TESTS
# ============================================


class TestFullWarmingFlow:
    """End-to-end integration test: targets → browser → DB."""

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_full_flow_targets_to_db(self, MockBrowser, bb_conn):
        """
        Full integration: add targets → run browser → verify DB state.

        This is the primary acceptance test for S2.3.
        """
        service = WarmingService(conn=bb_conn)

        # Step 1: Add targets from URLs
        urls = [
            {
                "url": "https://youtube.com/watch?v=mont1",
                "title": "Montessori sensory play",
                "channel": "MontiLife",
            },
            {
                "url": "https://youtube.com/watch?v=baby2",
                "title": "Baby development milestones",
                "channel": "BabySteps",
            },
            {
                "url": "https://youtube.com/watch?v=gen3",
                "title": "Gentle parenting tips",
                "channel": "GentleParent",
            },
        ]
        count = asyncio.run(
            service.add_targets_from_urls(urls, fetch_transcripts=False)
        )
        assert count == 3

        # Verify targets in DB
        targets = db.get_warming_targets(bb_conn, status="pending")
        assert len(targets) == 3

        # Step 2: Mock browser to return successful results
        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        watch_results = [
            WatchResult(
                url="https://youtube.com/watch?v=mont1",
                actual_watch_seconds=150,
                liked=True,
                subscribed=True,
            ),
            WatchResult(
                url="https://youtube.com/watch?v=baby2",
                actual_watch_seconds=120,
                liked=True,
                subscribed=False,
            ),
            WatchResult(
                url="https://youtube.com/watch?v=gen3",
                actual_watch_seconds=90,
                liked=False,
                subscribed=False,
            ),
        ]

        session_result = SessionResult(
            videos_watched=3,
            total_watch_seconds=360,
            likes=2,
            subscribes=1,
            watch_results=watch_results,
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        # Step 3: Run browser session
        result = asyncio.run(service.run_browser_session(platform="youtube"))

        assert result["status"] == "success"
        assert result["videos_watched"] == 3
        assert result["likes"] == 2
        assert result["subscribes"] == 1
        # 3 watches + 2 likes + 1 subscribe = 6 actions
        assert result["actions_logged"] == 6

        # Step 4: Verify DB state
        # All targets should be completed
        all_targets = db.get_warming_targets(bb_conn)
        for t in all_targets:
            assert t.status == "completed"

        # Actions logged with correct target IDs
        cursor = bb_conn.execute(
            "SELECT * FROM bb_warming_actions WHERE action_type = 'watch' "
            "AND target_id > 0 ORDER BY target_id"
        )
        watch_actions = cursor.fetchall()
        assert len(watch_actions) == 3
        assert watch_actions[0]["actual_watch_seconds"] == 150
        assert watch_actions[1]["actual_watch_seconds"] == 120
        assert watch_actions[2]["actual_watch_seconds"] == 90

        # Session logged
        session_stats = db.get_browser_session_stats(bb_conn, days=1)
        assert session_stats["successful_sessions"] == 1

        # Warming stats reflect actions
        warming_stats = db.get_warming_stats(bb_conn, days=1)
        assert warming_stats["watches"] == 3
        assert warming_stats["likes"] == 2
        assert warming_stats["subscribes"] == 1

    @patch("atlas.babybrains.warming.service.BROWSER_AVAILABLE", True)
    @patch("atlas.babybrains.warming.service.WarmingBrowser")
    def test_partial_session_with_errors(self, MockBrowser, bb_conn):
        """Session with some failures: successful watches logged, errors skipped."""
        service = WarmingService(conn=bb_conn)

        # Add targets
        urls = [
            {"url": "https://youtube.com/watch?v=ok1", "title": "OK video", "channel": "Ch"},
            {"url": "https://youtube.com/watch?v=fail2", "title": "Fail video", "channel": "Ch"},
            {"url": "https://youtube.com/watch?v=ok3", "title": "Another OK", "channel": "Ch"},
        ]
        asyncio.run(service.add_targets_from_urls(urls, fetch_transcripts=False))

        mock_instance = MagicMock()
        MockBrowser.return_value = mock_instance

        watch_results = [
            WatchResult(url="https://youtube.com/watch?v=ok1",
                        actual_watch_seconds=120, liked=False),
            WatchResult(url="https://youtube.com/watch?v=fail2",
                        actual_watch_seconds=0,
                        error="Circuit breaker OPEN"),
            WatchResult(url="https://youtube.com/watch?v=ok3",
                        actual_watch_seconds=100, liked=True),
        ]

        session_result = SessionResult(
            videos_watched=2,
            total_watch_seconds=220,
            likes=1,
            errors=["Circuit breaker OPEN"],
            watch_results=watch_results,
        )
        mock_instance.run_session = AsyncMock(return_value=session_result)
        mock_instance.stop = AsyncMock()

        result = asyncio.run(service.run_browser_session(platform="youtube"))

        assert result["status"] == "success"
        assert result["videos_watched"] == 2
        assert len(result["errors"]) == 1

        # Check statuses: 2 completed, 1 skipped
        targets = db.get_warming_targets(bb_conn)
        statuses = [t.status for t in targets]
        assert statuses.count("completed") == 2
        assert statuses.count("skipped") == 1
