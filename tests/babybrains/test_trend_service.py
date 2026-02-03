"""
Tests for TrendService (S2.6-lite)

Comprehensive coverage: ~35 tests across 6 categories.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas.babybrains import db
from atlas.babybrains.clients.grok_client import GrokTrendResult, GrokTrendTopic
from atlas.babybrains.models import TrendResult
from atlas.babybrains.trends.engine import (
    DAILY_BUDGET_LIMIT,
    MONTHLY_BUDGET_LIMIT,
    TrendService,
    TrendServiceResult,
)


# ============================================
# FIXTURES
# ============================================


@pytest.fixture
def mock_grok_topic():
    """Create a mock GrokTrendTopic."""
    return GrokTrendTopic(
        topic="Tummy time tips for newborns",
        description="Parents discussing positioning and duration",
        relevance_score=0.85,
        estimated_engagement="high",
        opportunity_type="gap",
        content_angle="Evidence-based approach with Montessori observation",
        source_context=["tweet1", "tweet2"],
        hashtags=["#tummytime", "#newborn"],
        audience_overlap="anxious_new_parent",
        knowledge_coverage="strong",
        confidence=0.9,
        saturation="low",
        platform_signals=["X.com", "reddit"],
    )


@pytest.fixture
def mock_grok_result(mock_grok_topic):
    """Create a mock GrokTrendResult."""
    return GrokTrendResult(
        topics=[mock_grok_topic],
        query_used="test query",
        model="grok-3-fast",
        tokens_used=1000,
        search_calls_used=2,
        cost_usd=0.03,
        scanned_at=datetime.now().isoformat(),
    )


@pytest.fixture
def trend_service(bb_conn, tmp_path):
    """Create TrendService with test database and config."""
    # Create test config files
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Fallback topics
    fallback = {
        "topics": [
            {
                "topic": "Fallback topic 1",
                "description": "Evergreen content",
                "relevance_score": 0.8,
                "confidence": 0.7,
                "opportunity_level": "medium",
                "audience_segment": "test_segment",
            }
        ]
    }
    (config_dir / "fallback_topics.json").write_text(json.dumps(fallback))

    # Brand safety rules
    safety = {
        "blocked_phrases": ["anti-vax movement", "vaccines cause autism"],
        "blocked_terms_strict": ["#antivax"],
        "allowlist_exceptions": ["vaccination schedule"],
        "category_blocks": {"test_category": ["blocked phrase"]},
    }
    (config_dir / "brand_safety_blocklist.json").write_text(json.dumps(safety))

    # Run migration
    db.run_trends_migration(bb_conn)

    return TrendService(conn=bb_conn, config_dir=config_dir)


# ============================================
# BUDGET GATE TESTS (8 tests)
# ============================================


class TestBudgetGates:
    """Tests for budget management and limits."""

    def test_get_budget_status_empty(self, trend_service):
        """Budget status shows zero when no costs recorded."""
        status = trend_service.get_budget_status()

        assert status["daily"]["used"] == 0.0
        assert status["daily"]["remaining"] == DAILY_BUDGET_LIMIT
        assert status["monthly"]["used"] == 0.0
        assert status["monthly"]["remaining"] == MONTHLY_BUDGET_LIMIT
        assert status["budget_ok"] is True
        assert status["budget_warning"] is False

    def test_get_budget_status_with_costs(self, bb_conn, trend_service):
        """Budget status reflects recorded costs."""
        db.add_grok_cost(bb_conn, "scan", 0.10, 1000, 2)
        db.add_grok_cost(bb_conn, "scan", 0.15, 1500, 3)

        status = trend_service.get_budget_status()

        assert status["daily"]["used"] == 0.25
        assert status["daily"]["remaining"] == DAILY_BUDGET_LIMIT - 0.25
        assert status["daily"]["operations"] == 2

    def test_budget_exceeded_daily(self, bb_conn, trend_service):
        """Budget gate blocks when daily limit exceeded."""
        db.add_grok_cost(bb_conn, "scan", DAILY_BUDGET_LIMIT + 0.01, 10000, 10)

        status = trend_service.get_budget_status()

        assert status["budget_ok"] is False
        assert status["daily"]["remaining"] <= 0

    def test_budget_exceeded_monthly(self, bb_conn, trend_service):
        """Budget gate blocks when monthly limit exceeded."""
        # Add costs across multiple days
        for i in range(10):
            db.add_grok_cost(
                bb_conn, "scan", 0.60,
                cost_date=f"2026-02-{i+1:02d}",
            )

        status = trend_service.get_budget_status()

        assert status["monthly"]["used"] == 6.0
        assert status["budget_ok"] is False

    def test_budget_warning_threshold(self, bb_conn, trend_service):
        """Budget warning when close to limit."""
        db.add_grok_cost(bb_conn, "scan", DAILY_BUDGET_LIMIT - 0.05, 5000, 5)

        status = trend_service.get_budget_status()

        assert status["budget_ok"] is True
        assert status["budget_warning"] is True

    @pytest.mark.asyncio
    async def test_scan_returns_fallback_on_budget_exceeded(
        self, bb_conn, trend_service
    ):
        """Scan returns fallback topics when budget exceeded."""
        db.add_grok_cost(bb_conn, "scan", DAILY_BUDGET_LIMIT + 0.10, 10000, 10)

        result = await trend_service.scan()

        assert result.source == "fallback"
        assert result.cost_usd == 0.0
        assert "Budget exceeded" in result.reason
        assert len(result.topics) > 0

    def test_record_cost_creates_entry(self, bb_conn, trend_service):
        """Recording cost creates database entry."""
        trend_service._record_cost("scan", 0.05, 500, 1)

        costs = db.get_grok_costs_for_date(bb_conn)

        assert costs["total_cost_usd"] == 0.05
        assert costs["operations"] == 1
        assert costs["tokens_used"] == 500
        assert costs["search_calls"] == 1

    def test_get_costs_for_month(self, bb_conn):
        """Monthly cost aggregation works correctly."""
        db.run_trends_migration(bb_conn)  # Ensure table exists

        db.add_grok_cost(bb_conn, "scan", 0.10, cost_date="2026-02-01")
        db.add_grok_cost(bb_conn, "scan", 0.20, cost_date="2026-02-15")
        db.add_grok_cost(bb_conn, "scan", 0.30, cost_date="2026-01-31")  # Different month

        costs = db.get_grok_costs_for_month(bb_conn, 2026, 2)

        assert abs(costs["total_cost_usd"] - 0.30) < 0.001  # Float precision
        assert costs["operations"] == 2


# ============================================
# FALLBACK CHAIN TESTS (7 tests)
# ============================================


class TestFallbackChain:
    """Tests for fallback topic handling."""

    def test_fallback_topics_loaded(self, trend_service):
        """Fallback topics loaded from config."""
        topics = trend_service._get_fallback_topics()

        assert len(topics) > 0
        assert topics[0].topic == "Fallback topic 1"
        assert topics[0].sources == ["fallback"]

    def test_should_use_fallback_on_api_failure(self, trend_service):
        """Fallback triggered when API returns empty with no cost."""
        grok_result = GrokTrendResult(
            topics=[],
            cost_usd=0.0,
            cached=False,
        )

        assert trend_service._should_use_fallback(grok_result) is True

    def test_no_fallback_on_valid_empty(self, trend_service):
        """No fallback when API returns empty with cost (valid search)."""
        grok_result = GrokTrendResult(
            topics=[],
            cost_usd=0.03,
            cached=False,
        )

        assert trend_service._should_use_fallback(grok_result) is False

    def test_no_fallback_on_cache_hit(self, trend_service):
        """No fallback when using cached results."""
        grok_result = GrokTrendResult(
            topics=[],
            cost_usd=0.0,
            cached=True,
        )

        assert trend_service._should_use_fallback(grok_result) is False

    def test_no_fallback_when_topics_exist(self, trend_service, mock_grok_result):
        """No fallback when Grok returns topics."""
        assert trend_service._should_use_fallback(mock_grok_result) is False

    @pytest.mark.asyncio
    async def test_scan_uses_fallback_on_api_error(self, trend_service):
        """Scan returns fallback on Grok API error."""
        from datetime import timedelta
        from aiobreaker import CircuitBreakerError

        with patch.object(
            trend_service._grok, "scan_opportunities",
            side_effect=CircuitBreakerError("test", timedelta(seconds=60))
        ):
            result = await trend_service.scan()

        assert result.source == "fallback"
        assert len(result.topics) > 0

    def test_fallback_file_missing_returns_empty(self, bb_conn, tmp_path):
        """Missing fallback file returns empty list gracefully."""
        config_dir = tmp_path / "empty_config"
        config_dir.mkdir()
        # Don't create fallback_topics.json

        service = TrendService(conn=bb_conn, config_dir=config_dir)
        topics = service._get_fallback_topics()

        assert topics == []


# ============================================
# BRAND SAFETY FILTER TESTS (8 tests)
# ============================================


class TestBrandSafetyFilter:
    """Tests for brand safety filtering."""

    def test_safe_topic_passes(self, trend_service, mock_grok_topic):
        """Normal topic passes brand safety."""
        assert trend_service._is_brand_safe(mock_grok_topic) is True

    def test_blocked_phrase_filtered(self, trend_service):
        """Topic with blocked phrase is filtered."""
        topic = GrokTrendTopic(
            topic="Discussion about anti-vax movement",
            description="Parents debating vaccines",
            relevance_score=0.8,
            estimated_engagement="high",
            opportunity_type="debate",
            content_angle="n/a",
        )

        assert trend_service._is_brand_safe(topic) is False

    def test_blocked_phrase_in_description(self, trend_service):
        """Blocked phrase in description is filtered."""
        topic = GrokTrendTopic(
            topic="Parenting debate",
            description="Some say vaccines cause autism which is wrong",
            relevance_score=0.8,
            estimated_engagement="high",
            opportunity_type="debate",
            content_angle="n/a",
        )

        assert trend_service._is_brand_safe(topic) is False

    def test_strict_hashtag_filtered(self, trend_service):
        """Strict hashtag term is filtered."""
        topic = GrokTrendTopic(
            topic="Vaccine discussion",
            description="Normal discussion",
            relevance_score=0.8,
            estimated_engagement="medium",
            opportunity_type="emerging",
            content_angle="n/a",
            hashtags=["#parenting", "#antivax"],
        )

        assert trend_service._is_brand_safe(topic) is False

    def test_allowlist_exception_passes(self, trend_service):
        """Allowlist exception passes despite containing blocked substring."""
        topic = GrokTrendTopic(
            topic="Understanding vaccination schedule",
            description="When to get baby vaccinated",
            relevance_score=0.9,
            estimated_engagement="high",
            opportunity_type="gap",
            content_angle="Helpful guidance",
        )

        assert trend_service._is_brand_safe(topic) is True

    def test_category_block_filtered(self, trend_service):
        """Category block phrases are filtered."""
        topic = GrokTrendTopic(
            topic="Test blocked phrase in topic",
            description="Normal description",
            relevance_score=0.7,
            estimated_engagement="medium",
            opportunity_type="emerging",
            content_angle="n/a",
        )

        assert trend_service._is_brand_safe(topic) is False

    def test_case_insensitive_matching(self, trend_service):
        """Matching is case insensitive."""
        topic = GrokTrendTopic(
            topic="ANTI-VAX MOVEMENT discussion",
            description="uppercase test",
            relevance_score=0.8,
            estimated_engagement="high",
            opportunity_type="debate",
            content_angle="n/a",
        )

        assert trend_service._is_brand_safe(topic) is False

    def test_filter_topics_counts_removed(self, trend_service, mock_grok_topic):
        """Filter counts removed topics."""
        unsafe_topic = GrokTrendTopic(
            topic="Anti-vax movement debate",
            description="Filtered",
            relevance_score=0.5,
            estimated_engagement="low",
            opportunity_type="debate",
            content_angle="n/a",
        )

        safe_topics, removed = trend_service._filter_topics(
            [mock_grok_topic, unsafe_topic]
        )

        assert len(safe_topics) == 1
        assert removed == 1


# ============================================
# DATA MAPPING TESTS (5 tests)
# ============================================


class TestDataMapping:
    """Tests for Grok -> TrendResult mapping."""

    def test_map_grok_to_trend_all_fields(self, trend_service, mock_grok_topic):
        """All fields mapped correctly from GrokTrendTopic."""
        trend = trend_service._map_grok_to_trend(mock_grok_topic)

        assert trend.topic == mock_grok_topic.topic
        assert trend.score == mock_grok_topic.relevance_score
        assert trend.sources == ["grok"]
        assert trend.opportunity_level == "high"  # mapped from estimated_engagement
        assert trend.audience_segment == mock_grok_topic.audience_overlap
        assert trend.knowledge_graph_match is True  # strong coverage
        assert trend.description == mock_grok_topic.description
        assert trend.content_angle == mock_grok_topic.content_angle
        assert trend.confidence == mock_grok_topic.confidence
        assert trend.hashtags == mock_grok_topic.hashtags
        assert trend.saturation == mock_grok_topic.saturation
        assert trend.platform_signals == mock_grok_topic.platform_signals

    def test_engagement_to_level_mapping(self, trend_service):
        """Estimated engagement maps to opportunity level correctly."""
        mappings = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "viral": "urgent",
        }

        for engagement, expected_level in mappings.items():
            topic = GrokTrendTopic(
                topic="Test",
                description="Test",
                relevance_score=0.5,
                estimated_engagement=engagement,
                opportunity_type="gap",
                content_angle="n/a",
            )
            trend = trend_service._map_grok_to_trend(topic)
            assert trend.opportunity_level == expected_level

    def test_knowledge_coverage_to_bool(self, trend_service):
        """Knowledge coverage maps to bool correctly."""
        for coverage, expected in [("strong", True), ("partial", True), ("none", False)]:
            topic = GrokTrendTopic(
                topic="Test",
                description="Test",
                relevance_score=0.5,
                estimated_engagement="medium",
                opportunity_type="gap",
                content_angle="n/a",
                knowledge_coverage=coverage,
            )
            trend = trend_service._map_grok_to_trend(topic)
            assert trend.knowledge_graph_match == expected

    def test_map_fallback_to_trend(self, trend_service):
        """Fallback dict maps to TrendResult correctly."""
        fallback = {
            "topic": "Test fallback",
            "description": "Description",
            "relevance_score": 0.75,
            "confidence": 0.8,
            "opportunity_level": "medium",
            "audience_segment": "test_segment",
            "content_angle": "Angle text",
        }

        trend = trend_service._map_fallback_to_trend(fallback)

        assert trend.topic == "Test fallback"
        assert trend.score == 0.75
        assert trend.sources == ["fallback"]
        assert trend.knowledge_graph_match is True  # Always true for fallbacks
        assert trend.saturation == "low"  # Always low for evergreen

    def test_trend_result_from_row(self, bb_conn):
        """TrendResult.from_row handles extended fields."""
        db.run_trends_migration(bb_conn)

        trend_id = db.add_trend(
            bb_conn,
            topic="Test topic",
            score=0.85,
            sources=["grok"],
            opportunity_level="high",
            description="Test description",
            content_angle="Test angle",
            confidence=0.9,
            hashtags=["#test"],
            saturation="low",
            platform_signals=["X.com"],
        )

        trends = db.get_recent_trends(bb_conn, limit=1)
        trend = trends[0]

        assert trend.description == "Test description"
        assert trend.content_angle == "Test angle"
        assert trend.confidence == 0.9
        assert trend.hashtags == ["#test"]
        assert trend.saturation == "low"
        assert trend.platform_signals == ["X.com"]


# ============================================
# STORAGE TESTS (4 tests)
# ============================================


class TestStorage:
    """Tests for database storage operations."""

    def test_store_trends_inserts(self, bb_conn, trend_service):
        """Storing trends inserts into database."""
        trend = TrendResult(
            topic="Test trend",
            score=0.8,
            sources=["grok"],
            opportunity_level="high",
        )

        count = trend_service._store_trends([trend])

        assert count == 1
        stored = db.get_recent_trends(bb_conn, limit=1)
        assert stored[0].topic == "Test trend"

    def test_upsert_trend_updates_existing(self, bb_conn):
        """Upsert updates existing trend by topic."""
        db.run_trends_migration(bb_conn)

        # Insert
        db.upsert_trend(bb_conn, "Test topic", 0.5, ["grok"])

        # Upsert with same topic
        db.upsert_trend(bb_conn, "Test topic", 0.9, ["grok", "fallback"])

        trends = db.get_recent_trends(bb_conn, limit=10)
        assert len(trends) == 1
        assert trends[0].score == 0.9
        assert trends[0].sources == ["grok", "fallback"]

    @pytest.mark.asyncio
    async def test_get_latest_returns_stored(self, bb_conn, trend_service):
        """get_latest returns stored trends."""
        db.add_trend(bb_conn, "Topic 1", 0.8, ["grok"])
        db.add_trend(bb_conn, "Topic 2", 0.9, ["grok"])

        trends = await trend_service.get_latest(limit=5)

        assert len(trends) == 2
        # Ordered by score DESC
        assert trends[0].score >= trends[1].score

    @pytest.mark.asyncio
    async def test_suggest_topics_ranks_by_value(self, bb_conn, trend_service):
        """suggest_topics_for_content returns high-value topics first."""
        # Low value
        db.add_trend(
            bb_conn, "Low value", 0.3, ["fallback"],
            confidence=0.3, opportunity_level="low",
        )
        # High value
        db.add_trend(
            bb_conn, "High value", 0.9, ["grok"],
            confidence=0.9, opportunity_level="high", knowledge_graph_match=True,
        )

        suggestions = await trend_service.suggest_topics_for_content(n=2)

        assert suggestions[0].topic == "High value"


# ============================================
# CLI INTEGRATION TESTS (3 tests)
# ============================================


class TestCLIIntegration:
    """Tests for CLI command integration."""

    def test_trends_budget_command(self, bb_conn, capsys):
        """trends budget command shows status."""
        from atlas.babybrains.cli import cmd_trends_budget

        db.run_trends_migration(bb_conn)

        class Args:
            pass

        # Patch get_conn to return our test connection
        with patch("atlas.babybrains.cli.get_conn", return_value=bb_conn):
            cmd_trends_budget(Args())

        captured = capsys.readouterr()
        assert "GROK BUDGET STATUS" in captured.out
        assert "DAILY" in captured.out
        assert "MONTHLY" in captured.out

    def test_trends_latest_command_empty(self, bb_conn, capsys):
        """trends latest command handles empty database."""
        from atlas.babybrains.cli import cmd_trends_latest

        db.run_trends_migration(bb_conn)

        class Args:
            limit = 10

        with patch("atlas.babybrains.cli.get_conn", return_value=bb_conn):
            cmd_trends_latest(Args())

        captured = capsys.readouterr()
        assert "No trends stored yet" in captured.out

    def test_trends_latest_command_with_data(self, bb_conn, capsys):
        """trends latest command shows stored trends."""
        from atlas.babybrains.cli import cmd_trends_latest

        db.run_trends_migration(bb_conn)
        db.add_trend(bb_conn, "CLI Test Topic", 0.75, ["grok"])

        class Args:
            limit = 10

        with patch("atlas.babybrains.cli.get_conn", return_value=bb_conn):
            cmd_trends_latest(Args())

        captured = capsys.readouterr()
        assert "CLI Test Topic" in captured.out
        assert "Score: 0.75" in captured.out


# ============================================
# SCAN INTEGRATION TESTS (5 tests)
# ============================================


class TestScanIntegration:
    """Integration tests for the scan method."""

    @pytest.mark.asyncio
    async def test_scan_success_flow(self, trend_service, mock_grok_result):
        """Successful scan stores results and returns them."""
        with patch.object(
            trend_service._grok, "scan_opportunities",
            new_callable=AsyncMock, return_value=mock_grok_result
        ):
            result = await trend_service.scan()

        assert result.source == "grok"
        assert result.cost_usd == mock_grok_result.cost_usd
        assert len(result.topics) == 1
        assert result.topics[0].topic == "Tummy time tips for newborns"

    @pytest.mark.asyncio
    async def test_scan_cache_source(self, trend_service, mock_grok_result):
        """Cached results show grok_cache source."""
        mock_grok_result.cached = True

        with patch.object(
            trend_service._grok, "scan_opportunities",
            new_callable=AsyncMock, return_value=mock_grok_result
        ):
            result = await trend_service.scan()

        assert result.source == "grok_cache"

    @pytest.mark.asyncio
    async def test_scan_records_cost(self, bb_conn, trend_service, mock_grok_result):
        """Scan records cost in database."""
        with patch.object(
            trend_service._grok, "scan_opportunities",
            new_callable=AsyncMock, return_value=mock_grok_result
        ):
            await trend_service.scan()

        costs = db.get_grok_costs_for_date(bb_conn)
        assert costs["total_cost_usd"] == mock_grok_result.cost_usd

    @pytest.mark.asyncio
    async def test_scan_filters_unsafe_topics(self, trend_service, mock_grok_topic):
        """Scan filters out unsafe topics."""
        unsafe_topic = GrokTrendTopic(
            topic="Anti-vax movement discussion",
            description="Should be filtered",
            relevance_score=0.9,
            estimated_engagement="viral",
            opportunity_type="debate",
            content_angle="n/a",
        )
        result = GrokTrendResult(
            topics=[mock_grok_topic, unsafe_topic],
            cost_usd=0.05,
        )

        with patch.object(
            trend_service._grok, "scan_opportunities",
            new_callable=AsyncMock, return_value=result
        ):
            scan_result = await trend_service.scan()

        assert len(scan_result.topics) == 1
        assert scan_result.filtered_count == 1

    @pytest.mark.asyncio
    async def test_scan_respects_max_topics(self, trend_service):
        """Scan respects max_topics parameter."""
        topics = [
            GrokTrendTopic(
                topic=f"Topic {i}",
                description=f"Desc {i}",
                relevance_score=0.8,
                estimated_engagement="medium",
                opportunity_type="gap",
                content_angle="n/a",
            )
            for i in range(20)
        ]
        result = GrokTrendResult(topics=topics, cost_usd=0.10)

        with patch.object(
            trend_service._grok, "scan_opportunities",
            new_callable=AsyncMock, return_value=result
        ):
            scan_result = await trend_service.scan(max_topics=5)

        assert len(scan_result.topics) == 5
