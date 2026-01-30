"""Tests for Baby Brains database layer."""

import sqlite3

import pytest

from atlas.babybrains import db
from atlas.babybrains.db import init_bb_tables
from atlas.babybrains.models import WarmingTarget, TrendResult, CrossRepoEntry


BB_TABLES = [
    "bb_accounts",
    "bb_warming_targets",
    "bb_warming_actions",
    "bb_engagement_log",
    "bb_trends",
    "bb_content_briefs",
    "bb_scripts",
    "bb_visual_assets",
    "bb_exports",
    "bb_cross_repo_index",
]


class TestInitBBTables:
    """Test table initialization."""

    def test_creates_all_10_tables(self, bb_conn):
        cursor = bb_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'bb_%'"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        for table_name in BB_TABLES:
            assert table_name in tables, f"Missing table: {table_name}"

    def test_idempotent_init(self, bb_conn):
        """Calling init_bb_tables twice should not error."""
        init_bb_tables(bb_conn)
        init_bb_tables(bb_conn)

        cursor = bb_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'bb_%'"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        assert len(tables) == 10

    def test_indexes_created(self, bb_conn):
        cursor = bb_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_bb_%'"
        )
        indexes = [row["name"] for row in cursor.fetchall()]
        assert len(indexes) >= 10


class TestAccountQueries:
    """Test account management."""

    def test_upsert_account_creates(self, bb_conn):
        account_id = db.upsert_account(bb_conn, "youtube", "@babybrains_au")
        assert account_id > 0

    def test_upsert_account_updates(self, bb_conn):
        id1 = db.upsert_account(bb_conn, "youtube", "@babybrains_au", status="warming")
        id2 = db.upsert_account(bb_conn, "youtube", "@babybrains_au", status="active")
        assert id1 == id2

    def test_get_accounts_all(self, bb_conn):
        db.upsert_account(bb_conn, "youtube", "@babybrains_au")
        db.upsert_account(bb_conn, "instagram", "@babybrains.au")
        accounts = db.get_accounts(bb_conn)
        assert len(accounts) == 2

    def test_get_accounts_filtered(self, bb_conn):
        db.upsert_account(bb_conn, "youtube", "@babybrains_au")
        db.upsert_account(bb_conn, "instagram", "@babybrains.au")
        accounts = db.get_accounts(bb_conn, platform="youtube")
        assert len(accounts) == 1
        assert accounts[0].platform == "youtube"


class TestWarmingTargetQueries:
    """Test warming target management."""

    def test_add_target(self, bb_conn):
        target_id = db.add_warming_target(
            bb_conn,
            platform="youtube",
            url="https://youtube.com/watch?v=test123",
            channel_name="Test Channel",
            video_title="Test Video",
            engagement_level="LIKE",
        )
        assert target_id > 0

    def test_get_targets_today(self, bb_conn):
        db.add_warming_target(
            bb_conn, platform="youtube", url="https://youtube.com/watch?v=1"
        )
        db.add_warming_target(
            bb_conn, platform="youtube", url="https://youtube.com/watch?v=2"
        )
        targets = db.get_warming_targets(bb_conn)
        assert len(targets) == 2

    def test_get_targets_filtered_by_platform(self, bb_conn):
        db.add_warming_target(bb_conn, platform="youtube", url="https://yt.com/1")
        db.add_warming_target(bb_conn, platform="instagram", url="https://ig.com/1")
        targets = db.get_warming_targets(bb_conn, platform="youtube")
        assert len(targets) == 1

    def test_update_target_status(self, bb_conn):
        target_id = db.add_warming_target(
            bb_conn, platform="youtube", url="https://yt.com/1"
        )
        db.update_target_status(bb_conn, target_id, "completed")
        targets = db.get_warming_targets(bb_conn, status="completed")
        assert len(targets) == 1


class TestWarmingActionQueries:
    """Test warming action logging."""

    def test_log_action(self, bb_conn):
        target_id = db.add_warming_target(
            bb_conn, platform="youtube", url="https://yt.com/1"
        )
        action_id = db.log_warming_action(
            bb_conn,
            target_id=target_id,
            action_type="watch",
            actual_watch_seconds=180,
        )
        assert action_id > 0

    def test_warming_stats(self, bb_conn):
        target_id = db.add_warming_target(
            bb_conn, platform="youtube", url="https://yt.com/1"
        )
        db.log_warming_action(bb_conn, target_id, "watch", actual_watch_seconds=120)
        db.log_warming_action(bb_conn, target_id, "like")

        stats = db.get_warming_stats(bb_conn)
        assert stats["watches"] == 1
        assert stats["likes"] == 1
        assert stats["total_watch_minutes"] == 2.0


class TestTrendQueries:
    """Test trend engine storage."""

    def test_add_trend(self, bb_conn):
        trend_id = db.add_trend(
            bb_conn,
            topic="toddler repetition play",
            score=0.85,
            sources=["youtube", "grok"],
            opportunity_level="high",
        )
        assert trend_id > 0

    def test_get_recent_trends(self, bb_conn):
        db.add_trend(bb_conn, "topic A", 0.5, ["youtube"])
        db.add_trend(bb_conn, "topic B", 0.9, ["grok", "reddit"])
        trends = db.get_recent_trends(bb_conn)
        assert len(trends) == 2
        assert trends[0].topic == "topic B"  # higher score first
        assert "grok" in trends[0].sources


class TestContentPipelineQueries:
    """Test content pipeline storage."""

    def test_add_brief(self, bb_conn):
        brief_id = db.add_content_brief(
            bb_conn,
            topic="Why toddlers repeat actions",
            hooks=["Your child does the same thing 50 times. Here's why that's brilliant."],
            core_message="Repetition is neural pathway building, not boredom.",
            evidence=[{"source": "The Absorbent Mind", "page": "Ch. 3"}],
        )
        assert brief_id > 0

    def test_get_briefs_by_status(self, bb_conn):
        db.add_content_brief(bb_conn, topic="Topic 1", hooks=["hook1"], core_message="msg1")
        db.add_content_brief(bb_conn, topic="Topic 2", hooks=["hook2"], core_message="msg2")
        briefs = db.get_briefs_by_status(bb_conn, "draft")
        assert len(briefs) == 2

    def test_add_script(self, bb_conn):
        brief_id = db.add_content_brief(
            bb_conn, topic="Test", hooks=["hook"], core_message="message"
        )
        script_id = db.add_script(
            bb_conn,
            brief_id=brief_id,
            format_type="60s",
            script_text="This is a test script with enough words to count.",
        )
        assert script_id > 0


class TestEngagementLogQueries:
    """Test engagement tracking."""

    def test_log_engagement(self, bb_conn):
        log_id = db.log_engagement(
            bb_conn,
            platform="instagram",
            followers=42,
            sends_count=5,
        )
        assert log_id > 0

    def test_log_engagement_upsert(self, bb_conn):
        id1 = db.log_engagement(bb_conn, platform="instagram", followers=42)
        id2 = db.log_engagement(bb_conn, platform="instagram", followers=50)
        assert id1 == id2


class TestCrossRepoQueries:
    """Test cross-repo index."""

    def test_upsert_entry(self, bb_conn):
        entry_id = db.upsert_cross_repo_entry(
            bb_conn,
            topic="platform strategy",
            repo="babybrains-os",
            file_path="docs/PLATFORM-PLAYBOOKS.md",
            summary="Platform-specific posting strategies",
        )
        assert entry_id > 0

    def test_search_cross_repo(self, bb_conn):
        db.upsert_cross_repo_entry(
            bb_conn, "platform strategy", "babybrains-os",
            "docs/PLATFORM-PLAYBOOKS.md", "Platform posting strategies",
        )
        db.upsert_cross_repo_entry(
            bb_conn, "voice spec", "web",
            ".claude/agents/BabyBrains-Writer.md", "Brand voice specification",
        )
        results = db.search_cross_repo(bb_conn, "platform")
        assert len(results) >= 1
        assert results[0].repo == "babybrains-os"


class TestStatusDashboard:
    """Test the full status dashboard."""

    def test_get_bb_status_empty(self, bb_conn):
        status = db.get_bb_status(bb_conn)
        assert "accounts" in status
        assert "warming_7d" in status
        assert "today" in status
        assert "trends" in status
        assert "content" in status

    def test_get_bb_status_with_data(self, bb_conn):
        db.upsert_account(bb_conn, "youtube", "@babybrains_au")
        db.add_warming_target(bb_conn, "youtube", "https://yt.com/1")
        db.add_trend(bb_conn, "test topic", 0.7, ["youtube"])

        status = db.get_bb_status(bb_conn)
        assert len(status["accounts"]) == 1
        assert status["today"]["targets"] == 1
        assert status["trends"]["recent_count"] == 1
