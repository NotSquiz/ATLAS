"""Tests for Baby Brains database layer."""

import json
import sqlite3

import pytest

from atlas.babybrains import db
from atlas.babybrains.db import (
    init_bb_tables,
    run_content_migration,
    _column_exists,
    _migrate_add_column,
)
from atlas.babybrains.models import (
    WarmingTarget,
    TrendResult,
    CrossRepoEntry,
    ContentBrief,
    Script,
    PipelineRun,
)


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
    "bb_pipeline_runs",
    "bb_grok_costs",  # S2.6-lite cost tracking
]


class TestInitBBTables:
    """Test table initialization."""

    def test_creates_all_12_tables(self, bb_conn):
        cursor = bb_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'bb_%'"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        for table_name in BB_TABLES:
            assert table_name in tables, f"Missing table: {table_name}"
        assert len(tables) == 12

    def test_idempotent_init(self, bb_conn):
        """Calling init_bb_tables twice should not error."""
        init_bb_tables(bb_conn)
        init_bb_tables(bb_conn)

        cursor = bb_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'bb_%'"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        assert len(tables) == 12

    def test_indexes_created(self, bb_conn):
        cursor = bb_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = [row["name"] for row in cursor.fetchall()]
        # Now includes pipeline run indexes
        assert len(indexes) >= 13


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


class TestSchemaMigration:
    """Test schema migration utilities."""

    def test_column_exists_true(self, bb_conn):
        """Column that exists should return True."""
        assert _column_exists(bb_conn, "bb_content_briefs", "topic") is True

    def test_column_exists_false(self, bb_conn):
        """Column that doesn't exist should return False."""
        assert _column_exists(bb_conn, "bb_content_briefs", "nonexistent_column") is False

    def test_migrate_add_column_adds_new_column(self, bb_conn):
        """_migrate_add_column should add a new column."""
        assert _column_exists(bb_conn, "bb_content_briefs", "test_column_xyz") is False
        _migrate_add_column(bb_conn, "bb_content_briefs", "test_column_xyz", "TEXT")
        assert _column_exists(bb_conn, "bb_content_briefs", "test_column_xyz") is True

    def test_migrate_add_column_idempotent(self, bb_conn):
        """_migrate_add_column should not error when column exists."""
        _migrate_add_column(bb_conn, "bb_content_briefs", "test_col_abc", "TEXT")
        # Calling again should not raise
        _migrate_add_column(bb_conn, "bb_content_briefs", "test_col_abc", "TEXT")
        assert _column_exists(bb_conn, "bb_content_briefs", "test_col_abc") is True

    def test_run_content_migration_idempotent(self, bb_conn):
        """run_content_migration should be safe to call multiple times."""
        run_content_migration(bb_conn)
        run_content_migration(bb_conn)  # Should not error
        # Verify some columns exist
        assert _column_exists(bb_conn, "bb_content_briefs", "age_range") is True
        assert _column_exists(bb_conn, "bb_scripts", "scenes") is True

    def test_content_migration_adds_all_brief_columns(self, bb_conn):
        """Migration should add all 17 ContentBrief columns."""
        run_content_migration(bb_conn)
        expected_columns = [
            "age_range", "hook_text", "target_length", "priority_tier",
            "montessori_principle", "setting", "au_localisers", "safety_lines",
            "camera_notes", "hook_pattern", "content_pillar", "tags",
            "source", "canonical_id", "grok_confidence", "knowledge_coverage",
            "all_principles",
        ]
        for col in expected_columns:
            assert _column_exists(bb_conn, "bb_content_briefs", col), f"Missing: {col}"

    def test_content_migration_adds_all_script_columns(self, bb_conn):
        """Migration should add all 7 Script columns."""
        run_content_migration(bb_conn)
        expected_columns = [
            "scenes", "derivative_cuts", "cta_text", "safety_disclaimers",
            "hook_pattern_used", "reviewed_by", "reviewed_at",
        ]
        for col in expected_columns:
            assert _column_exists(bb_conn, "bb_scripts", col), f"Missing: {col}"

    def test_content_migration_creates_indexes(self, bb_conn):
        """Migration should create source/canonical indexes."""
        run_content_migration(bb_conn)
        cursor = bb_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_briefs_%'"
        )
        indexes = {row["name"] for row in cursor.fetchall()}
        assert "idx_briefs_canonical" in indexes
        assert "idx_briefs_source" in indexes


class TestWALMode:
    """Test WAL mode is enabled."""

    def test_wal_mode_enabled(self, tmp_path):
        """get_bb_connection should enable WAL mode."""
        db_path = tmp_path / "test_wal.db"
        conn = db.get_bb_connection(db_path)
        cursor = conn.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        assert mode == "wal"
        conn.close()


class TestContentBriefNullHandling:
    """Test that None values produce [] not null in JSON columns."""

    def test_add_brief_with_none_hooks_produces_empty_list(self, bb_conn):
        """hooks=None should store as '[]' not 'null'."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(
            bb_conn,
            topic="Test topic",
            hooks=None,  # Explicitly None
            core_message=None,
        )
        cursor = bb_conn.execute(
            "SELECT hooks FROM bb_content_briefs WHERE id = ?", (brief_id,)
        )
        row = cursor.fetchone()
        # Should be "[]" not "null"
        assert row["hooks"] == "[]"
        parsed = json.loads(row["hooks"])
        assert parsed == []

    def test_add_brief_with_none_tags_produces_empty_list(self, bb_conn):
        """tags=None should store as '[]' not 'null'."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(
            bb_conn,
            topic="Test topic",
            tags=None,
        )
        cursor = bb_conn.execute(
            "SELECT tags FROM bb_content_briefs WHERE id = ?", (brief_id,)
        )
        row = cursor.fetchone()
        assert row["tags"] == "[]"

    def test_get_brief_by_id_returns_brief(self, bb_conn):
        """get_brief_by_id should return a ContentBrief object."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(
            bb_conn,
            topic="Test topic",
            age_range="6-12m",
            montessori_principle="follow_the_child",
            source="canonical:test123",
        )
        brief = db.get_brief_by_id(bb_conn, brief_id)
        assert isinstance(brief, ContentBrief)
        assert brief.topic == "Test topic"
        assert brief.age_range == "6-12m"
        assert brief.montessori_principle == "follow_the_child"
        assert brief.source == "canonical:test123"

    def test_get_brief_by_id_missing_returns_none(self, bb_conn):
        """get_brief_by_id should return None for missing ID."""
        brief = db.get_brief_by_id(bb_conn, 99999)
        assert brief is None


class TestScriptQueries:
    """Test script query helpers."""

    def test_get_script_by_id(self, bb_conn):
        """get_script_by_id should return a Script object."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        script_id = db.add_script(
            bb_conn, brief_id, "60s", "Test script text here."
        )
        script = db.get_script_by_id(bb_conn, script_id)
        assert isinstance(script, Script)
        assert script.format_type == "60s"
        assert "Test script" in script.script_text

    def test_update_script_fields(self, bb_conn):
        """update_script_fields should update specific fields."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        script_id = db.add_script(bb_conn, brief_id, "60s", "Original text")
        db.update_script_fields(
            bb_conn, script_id,
            cta_text="Follow for more!",
            scenes=[{"number": 1, "vo_text": "Hello"}],
        )
        script = db.get_script_by_id(bb_conn, script_id)
        assert script.cta_text == "Follow for more!"
        assert len(script.scenes) == 1
        assert script.scenes[0]["number"] == 1


class TestVisualAssetQueries:
    """Test visual asset query helpers."""

    def test_add_visual_asset(self, bb_conn):
        """add_visual_asset should create a visual asset."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        script_id = db.add_script(bb_conn, brief_id, "60s", "Text")
        asset_id = db.add_visual_asset(
            bb_conn, script_id, "midjourney_prompt",
            prompt_text="A baby playing with blocks",
            tool="midjourney",
            scene_number=1,
        )
        assert asset_id > 0

    def test_get_visual_assets_by_script(self, bb_conn):
        """get_visual_assets_by_script should return all assets."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        script_id = db.add_script(bb_conn, brief_id, "60s", "Text")
        db.add_visual_asset(bb_conn, script_id, "mj", prompt_text="P1", scene_number=1)
        db.add_visual_asset(bb_conn, script_id, "mj", prompt_text="P2", scene_number=2)
        assets = db.get_visual_assets_by_script(bb_conn, script_id)
        assert len(assets) == 2
        assert assets[0].scene_number == 1
        assert assets[1].scene_number == 2


class TestExportQueries:
    """Test export query helpers."""

    def test_add_export(self, bb_conn):
        """add_export should create an export entry."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        script_id = db.add_script(bb_conn, brief_id, "60s", "Text")
        export_id = db.add_export(
            bb_conn, script_id, "instagram",
            caption="Great content!",
            title="Test Video",
            export_tags=["parenting", "montessori"],
        )
        assert export_id > 0

    def test_get_exports_by_script(self, bb_conn):
        """get_exports_by_script should return all exports."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        script_id = db.add_script(bb_conn, brief_id, "60s", "Text")
        db.add_export(bb_conn, script_id, "instagram", caption="IG caption")
        db.add_export(bb_conn, script_id, "tiktok", caption="TT caption")
        exports = db.get_exports_by_script(bb_conn, script_id)
        assert len(exports) == 2
        platforms = {e.platform for e in exports}
        assert "instagram" in platforms
        assert "tiktok" in platforms


class TestPipelineRunQueries:
    """Test pipeline run query helpers."""

    def test_add_pipeline_run(self, bb_conn):
        """add_pipeline_run should create a pipeline run."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        run_id = db.add_pipeline_run(bb_conn, brief_id, "brief")
        assert run_id > 0

    def test_get_pipeline_run(self, bb_conn):
        """get_pipeline_run should return a PipelineRun object."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        run_id = db.add_pipeline_run(bb_conn, brief_id, "brief", max_retries=5)
        run = db.get_pipeline_run(bb_conn, run_id)
        assert isinstance(run, PipelineRun)
        assert run.brief_id == brief_id
        assert run.current_stage == "brief"
        assert run.max_retries == 5

    def test_update_pipeline_run(self, bb_conn):
        """update_pipeline_run should update specific fields."""
        run_content_migration(bb_conn)
        brief_id = db.add_content_brief(bb_conn, topic="Test")
        run_id = db.add_pipeline_run(bb_conn, brief_id, "brief")
        db.update_pipeline_run(
            bb_conn, run_id,
            current_stage="script",
            retry_count=1,
            hook_failures=[{"hook": "qc_safety", "code": "SAFETY_CHOKING", "msg": "Hazard"}],
        )
        run = db.get_pipeline_run(bb_conn, run_id)
        assert run.current_stage == "script"
        assert run.retry_count == 1
        assert len(run.hook_failures) == 1
        assert run.hook_failures[0]["code"] == "SAFETY_CHOKING"

    def test_get_active_pipeline_runs(self, bb_conn):
        """get_active_pipeline_runs should exclude complete and failed."""
        run_content_migration(bb_conn)
        brief1 = db.add_content_brief(bb_conn, topic="Active")
        brief2 = db.add_content_brief(bb_conn, topic="Complete")
        brief3 = db.add_content_brief(bb_conn, topic="Failed")
        run1 = db.add_pipeline_run(bb_conn, brief1, "script")
        run2 = db.add_pipeline_run(bb_conn, brief2, "complete")
        run3 = db.add_pipeline_run(bb_conn, brief3, "script_failed")
        active = db.get_active_pipeline_runs(bb_conn)
        assert len(active) == 1
        assert active[0].id == run1

    def test_pipeline_run_is_failed_property(self, bb_conn):
        """PipelineRun.is_failed should detect failed stages."""
        run = PipelineRun(current_stage="script_failed")
        assert run.is_failed is True
        run.current_stage = "script"
        assert run.is_failed is False

    def test_pipeline_run_is_complete_property(self, bb_conn):
        """PipelineRun.is_complete should detect complete stage."""
        run = PipelineRun(current_stage="complete")
        assert run.is_complete is True
        run.current_stage = "review"
        assert run.is_complete is False

    def test_pipeline_run_is_waiting_for_human_property(self, bb_conn):
        """PipelineRun.is_waiting_for_human should detect manual gates."""
        run = PipelineRun(current_stage="manual_visual")
        assert run.is_waiting_for_human is True
        run.current_stage = "script"
        assert run.is_waiting_for_human is False
