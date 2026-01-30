"""Tests for Baby Brains warming service and targets."""

import asyncio

import pytest

from atlas.babybrains import db
from atlas.babybrains.warming.targets import (
    determine_engagement_level,
    calculate_watch_duration,
    score_niche_relevance,
    generate_manual_targets,
)
from atlas.babybrains.warming.service import WarmingService, WarmingDailyResult


class TestDetermineEngagementLevel:
    """Test engagement level determination."""

    def test_low_relevance_watch(self):
        assert determine_engagement_level(0.1) == "WATCH"

    def test_medium_relevance_like(self):
        assert determine_engagement_level(0.4) == "LIKE"

    def test_high_relevance_comment(self):
        assert determine_engagement_level(0.5) == "COMMENT"

    def test_very_high_relevance_subscribe(self):
        assert determine_engagement_level(0.8, channel_quality=0.7) == "SUBSCRIBE"

    def test_high_relevance_low_quality_not_subscribe(self):
        # High relevance but low channel quality shouldn't subscribe
        level = determine_engagement_level(0.8, channel_quality=0.3)
        assert level != "SUBSCRIBE"


class TestCalculateWatchDuration:
    """Test watch duration calculation."""

    def test_watch_duration_in_range(self):
        for _ in range(10):
            duration = calculate_watch_duration("WATCH")
            assert 30 <= duration <= 200  # With variance

    def test_subscribe_longer_watch(self):
        durations = [calculate_watch_duration("SUBSCRIBE") for _ in range(10)]
        avg = sum(durations) / len(durations)
        assert avg >= 80  # Subscribe should have longer watches

    def test_never_below_30(self):
        for _ in range(20):
            duration = calculate_watch_duration("WATCH")
            assert duration >= 30


class TestScoreNicheRelevance:
    """Test niche relevance scoring."""

    def test_high_relevance(self):
        score = score_niche_relevance(
            "Montessori sensory play for toddlers"
        )
        assert score >= 0.6

    def test_low_relevance(self):
        score = score_niche_relevance(
            "Best cars of 2025 review"
        )
        assert score <= 0.3

    def test_medium_relevance(self):
        score = score_niche_relevance(
            "Parenting tips for new parents"
        )
        assert 0.0 <= score <= 1.0

    def test_empty_title(self):
        score = score_niche_relevance("")
        assert score == 0.0


class TestGenerateManualTargets:
    """Test manual target generation."""

    def test_generates_targets(self):
        urls = [
            {"url": "https://youtube.com/watch?v=test1", "title": "Montessori activities", "channel": "Test"},
            {"url": "https://youtube.com/watch?v=test2", "title": "Car reviews 2025", "channel": "Other"},
        ]
        targets = generate_manual_targets(urls)
        assert len(targets) == 2
        # Higher relevance should be first
        assert targets[0]["niche_relevance_score"] >= targets[1]["niche_relevance_score"]

    def test_target_has_required_fields(self):
        urls = [{"url": "https://youtube.com/watch?v=test", "title": "Gentle parenting tips", "channel": "Ch"}]
        targets = generate_manual_targets(urls)
        assert len(targets) == 1
        t = targets[0]
        assert "platform" in t
        assert "url" in t
        assert "engagement_level" in t
        assert "watch_duration_target" in t
        assert "niche_relevance_score" in t


class TestWarmingService:
    """Test WarmingService orchestration."""

    def test_run_daily_empty(self, bb_conn):
        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_daily())
        assert isinstance(result, WarmingDailyResult)
        assert len(result.targets) == 0

    def test_run_daily_with_targets(self, bb_conn):
        # Add a target
        db.add_warming_target(
            bb_conn,
            platform="youtube",
            url="https://youtube.com/watch?v=test123",
            video_title="Test Video",
            engagement_level="WATCH",
            transcript_summary="Some transcript text here.",
        )

        service = WarmingService(conn=bb_conn)
        result = asyncio.run(service.run_daily(generate_comments=False))
        assert len(result.targets) == 1
        assert result.targets[0]["title"] == "Test Video"

    def test_add_targets_from_urls(self, bb_conn):
        service = WarmingService(conn=bb_conn)
        urls = [
            {"url": "https://youtube.com/watch?v=abc", "title": "Montessori at home", "channel": "Test"},
        ]
        count = asyncio.run(service.add_targets_from_urls(urls, fetch_transcripts=False))
        assert count == 1

        targets = db.get_warming_targets(bb_conn)
        assert len(targets) == 1
        assert targets[0].video_title == "Montessori at home"

    def test_log_done(self, bb_conn):
        service = WarmingService(conn=bb_conn)
        result = service.log_done("youtube", comments=3, likes=2)
        assert "3 comment(s)" in result["actions"]
        assert "2 like(s)" in result["actions"]

        stats = db.get_warming_stats(bb_conn)
        assert stats["comments"] == 3
        assert stats["likes"] == 2


class TestWarmingDailyResult:
    """Test WarmingDailyResult dataclass."""

    def test_summary(self):
        result = WarmingDailyResult(
            date="2026-01-30",
            targets=[{"id": 1}, {"id": 2}],
            transcripts_fetched=1,
            comments_generated=1,
        )
        assert "2 targets" in result.summary
        assert "1 transcripts" in result.summary
        assert "1 comments" in result.summary
