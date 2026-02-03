"""
Baby Brains TrendService — Thin Wrapper around GrokClient

S2.6-lite implementation: budget gates, brand safety, fallback chain.

NOT implemented (deferred to Month 2+):
- Temporal decay
- Competitor saturation scoring
- Learning loops
- Cross-source aggregation (YouTube ToS)
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiobreaker import CircuitBreakerError

from atlas.babybrains import db
from atlas.babybrains.clients.grok_client import (
    GrokAPIError,
    GrokClient,
    GrokTrendResult,
    GrokTrendTopic,
)
from atlas.babybrains.models import TrendResult

logger = logging.getLogger(__name__)

# Budget limits
DAILY_BUDGET_LIMIT = 0.50   # $0.50/day
MONTHLY_BUDGET_LIMIT = 5.00  # $5/month


@dataclass
class TrendServiceResult:
    """Result from TrendService operations."""

    topics: list[TrendResult] = field(default_factory=list)
    source: str = "empty"  # "grok", "grok_cache", "fallback", "empty"
    cost_usd: float = 0.0
    filtered_count: int = 0
    reason: Optional[str] = None


class TrendService:
    """
    Thin trend wrapper - delegates to GrokClient, adds budget/safety.

    Responsibilities:
    1. Budget gates (daily/monthly limits)
    2. Brand-safety filtering
    3. Fallback to evergreen topics
    4. Store results in bb_trends

    Does NOT add another circuit breaker - GrokClient manages its own.
    """

    def __init__(
        self,
        conn: Optional[sqlite3.Connection] = None,
        grok_client: Optional[GrokClient] = None,
        config_dir: Optional[Path] = None,
    ):
        """
        Initialize TrendService.

        Args:
            conn: SQLite connection. Falls back to get_bb_connection().
            grok_client: GrokClient instance. Created if not provided.
            config_dir: Path to config/babybrains/ for safety/fallback files.
        """
        self._conn = conn
        self._grok = grok_client or GrokClient()
        self._config_dir = config_dir or (
            Path(__file__).parent.parent.parent.parent / "config" / "babybrains"
        )
        self._safety_rules = self._load_json("brand_safety_blocklist.json")
        self._fallback_topics = self._load_json("fallback_topics.json")

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = db.get_bb_connection()
            db.init_bb_tables(self._conn)
            db.run_trends_migration(self._conn)
        return self._conn

    def _load_json(self, filename: str) -> dict:
        """Load a JSON config file."""
        path = self._config_dir / filename
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load config {path}: {e}")
        return {}

    # --- Budget Management ---

    def get_budget_status(self) -> dict:
        """
        Get current budget usage (sync - just DB queries).

        Returns:
            Dict with daily/monthly usage and remaining budget.
        """
        conn = self._get_conn()
        today = db.get_grok_costs_for_date(conn)
        month = db.get_grok_costs_for_month(conn)

        daily_remaining = max(0.0, DAILY_BUDGET_LIMIT - today["total_cost_usd"])
        monthly_remaining = max(0.0, MONTHLY_BUDGET_LIMIT - month["total_cost_usd"])

        return {
            "daily": {
                "used": today["total_cost_usd"],
                "limit": DAILY_BUDGET_LIMIT,
                "remaining": daily_remaining,
                "operations": today["operations"],
            },
            "monthly": {
                "used": month["total_cost_usd"],
                "limit": MONTHLY_BUDGET_LIMIT,
                "remaining": monthly_remaining,
                "operations": month["operations"],
            },
            "budget_ok": daily_remaining > 0 and monthly_remaining > 0,
            "budget_warning": daily_remaining < 0.10 or monthly_remaining < 1.00,
        }

    def _check_budget(self) -> tuple[bool, str]:
        """
        Check if we're within budget (pre-call soft gate).

        Returns:
            (can_proceed, reason)
        """
        status = self.get_budget_status()

        if status["daily"]["remaining"] <= 0:
            return False, f"Daily budget exceeded (${DAILY_BUDGET_LIMIT}/day)"

        if status["monthly"]["remaining"] <= 0:
            return False, f"Monthly budget exceeded (${MONTHLY_BUDGET_LIMIT}/month)"

        if status["budget_warning"]:
            logger.warning(
                f"Budget warning: daily ${status['daily']['remaining']:.2f}, "
                f"monthly ${status['monthly']['remaining']:.2f} remaining"
            )

        return True, "ok"

    def _record_cost(
        self, operation: str, cost_usd: float, tokens_used: int, search_calls: int
    ) -> None:
        """Record cost after API call completes."""
        conn = self._get_conn()
        db.add_grok_cost(conn, operation, cost_usd, tokens_used, search_calls)
        logger.info(f"Recorded Grok cost: {operation} ${cost_usd:.4f}")

    # --- Brand Safety ---

    def _is_brand_safe(self, topic: GrokTrendTopic) -> bool:
        """
        Check if a topic passes brand safety filtering.

        Logic (from D6):
        1. Check allowlist first - if any exception matches, PASS
        2. Check blocked_phrases - exact phrase match in topic OR description
        3. Check blocked_terms_strict - exact match in hashtags only

        Args:
            topic: GrokTrendTopic to check

        Returns:
            True if brand-safe, False if blocked
        """
        if not self._safety_rules:
            return True

        text_to_check = f"{topic.topic} {topic.description}".lower()
        hashtags_lower = [h.lower() for h in topic.hashtags]

        # 1. Allowlist exceptions
        allowlist = self._safety_rules.get("allowlist_exceptions", [])
        for exception in allowlist:
            if exception.lower() in text_to_check:
                logger.debug(f"Allowlist match for '{topic.topic}': {exception}")
                return True

        # 2. Blocked phrases
        blocked_phrases = self._safety_rules.get("blocked_phrases", [])
        for phrase in blocked_phrases:
            if phrase.lower() in text_to_check:
                logger.info(f"Blocked phrase match for '{topic.topic}': {phrase}")
                return False

        # 3. Strict hashtag blocks
        blocked_strict = self._safety_rules.get("blocked_terms_strict", [])
        for term in blocked_strict:
            if term.lower() in hashtags_lower:
                logger.info(f"Blocked hashtag match for '{topic.topic}': {term}")
                return False

        # 4. Category blocks
        category_blocks = self._safety_rules.get("category_blocks", {})
        for category, phrases in category_blocks.items():
            for phrase in phrases:
                if phrase.lower() in text_to_check:
                    logger.info(
                        f"Category block ({category}) for '{topic.topic}': {phrase}"
                    )
                    return False

        return True

    def _filter_topics(
        self, topics: list[GrokTrendTopic]
    ) -> tuple[list[GrokTrendTopic], int]:
        """
        Apply brand safety filter to topic list.

        Returns:
            (filtered_topics, removed_count)
        """
        safe_topics = []
        removed = 0

        for topic in topics:
            if self._is_brand_safe(topic):
                safe_topics.append(topic)
            else:
                removed += 1

        if removed > 0:
            logger.info(f"Brand safety filtered {removed} topics")

        return safe_topics, removed

    # --- Data Mapping ---

    def _map_grok_to_trend(self, grok_topic: GrokTrendTopic) -> TrendResult:
        """
        Map GrokTrendTopic to TrendResult with explicit field mapping.

        Field mapping:
        - topic -> topic
        - description -> description
        - relevance_score -> score
        - estimated_engagement -> opportunity_level (mapped)
        - opportunity_type -> (not stored, could be derived)
        - content_angle -> content_angle
        - source_context -> (not stored - too volatile)
        - hashtags -> hashtags
        - audience_overlap -> audience_segment
        - knowledge_coverage -> knowledge_graph_match (bool conversion)
        - confidence -> confidence
        - saturation -> saturation
        - platform_signals -> platform_signals
        """
        # Map estimated_engagement to opportunity_level
        engagement_to_level = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "viral": "urgent",
        }
        opportunity_level = engagement_to_level.get(
            grok_topic.estimated_engagement.lower(), "low"
        )

        # Map knowledge_coverage to bool
        knowledge_match = grok_topic.knowledge_coverage in ("strong", "partial")

        return TrendResult(
            topic=grok_topic.topic,
            score=grok_topic.relevance_score,
            sources=["grok"],
            opportunity_level=opportunity_level,
            audience_segment=grok_topic.audience_overlap,
            knowledge_graph_match=knowledge_match,
            sample_urls=[],  # Not provided by Grok
            description=grok_topic.description,
            content_angle=grok_topic.content_angle,
            confidence=grok_topic.confidence,
            hashtags=grok_topic.hashtags,
            saturation=grok_topic.saturation,
            platform_signals=grok_topic.platform_signals,
        )

    def _map_fallback_to_trend(self, fallback: dict) -> TrendResult:
        """Map fallback topic dict to TrendResult."""
        return TrendResult(
            topic=fallback.get("topic", ""),
            score=fallback.get("relevance_score", 0.5),
            sources=["fallback"],
            opportunity_level=fallback.get("opportunity_level", "medium"),
            audience_segment=fallback.get("audience_segment"),
            knowledge_graph_match=True,  # Fallbacks are known content
            sample_urls=[],
            description=fallback.get("description"),
            content_angle=fallback.get("content_angle"),
            confidence=fallback.get("confidence", 0.7),
            hashtags=[],
            saturation="low",  # Evergreen = low saturation
            platform_signals=[],
        )

    # --- Storage ---

    def _store_trends(self, trends: list[TrendResult]) -> int:
        """Store trend results in database, returning count stored."""
        conn = self._get_conn()
        stored = 0

        for trend in trends:
            try:
                db.upsert_trend(
                    conn,
                    topic=trend.topic,
                    score=trend.score,
                    sources=trend.sources,
                    opportunity_level=trend.opportunity_level,
                    audience_segment=trend.audience_segment,
                    knowledge_graph_match=trend.knowledge_graph_match,
                    sample_urls=trend.sample_urls,
                    description=trend.description,
                    content_angle=trend.content_angle,
                    confidence=trend.confidence,
                    hashtags=trend.hashtags,
                    saturation=trend.saturation,
                    platform_signals=trend.platform_signals,
                )
                stored += 1
            except Exception as e:
                logger.error(f"Failed to store trend '{trend.topic}': {e}")

        logger.info(f"Stored {stored} trends")
        return stored

    # --- Fallback ---

    def _get_fallback_topics(self, max_topics: int = 10) -> list[TrendResult]:
        """Get evergreen fallback topics."""
        raw_topics = self._fallback_topics.get("topics", [])[:max_topics]
        return [self._map_fallback_to_trend(t) for t in raw_topics]

    def _should_use_fallback(self, grok_result: GrokTrendResult) -> bool:
        """
        Determine if we should use fallback topics.

        Conditions (from D4):
        - topics=[] AND cost_usd > 0 → Valid empty (no trends found) - no fallback
        - topics=[] AND cost_usd == 0 AND cached=False → API failure - use fallback
        - topics=[] AND cached=True → Stale cache hit - use as-is
        - Exception raised → API failure - use fallback (handled in caller)
        """
        if grok_result.topics:
            return False

        # Empty result with no cost and not cached = API failure
        if grok_result.cost_usd == 0.0 and not grok_result.cached:
            return True

        return False

    # --- Public Methods ---

    async def scan(
        self,
        niche_focus: Optional[str] = None,
        max_topics: int = 10,
        region: str = "Australia",
    ) -> TrendServiceResult:
        """
        Scan for trending parenting content opportunities.

        Delegates to GrokClient, applies budget/safety, stores results.

        Args:
            niche_focus: Optional focus area (e.g., "emerging", "conversations")
            max_topics: Maximum topics to return (default 10)
            region: Geographic focus (default "Australia")

        Returns:
            TrendServiceResult with topics, source, cost, and filter info
        """
        # Pre-flight budget check
        can_proceed, budget_reason = self._check_budget()
        if not can_proceed:
            logger.warning(f"Budget exceeded: {budget_reason}")
            fallback = self._get_fallback_topics(max_topics)
            return TrendServiceResult(
                topics=fallback,
                source="fallback",
                cost_usd=0.0,
                filtered_count=0,
                reason=f"Budget exceeded: {budget_reason}",
            )

        # Call Grok
        try:
            grok_result = await self._grok.scan_opportunities(
                niche_focus=niche_focus,
                max_topics=max_topics,
                region=region,
            )
        except (GrokAPIError, CircuitBreakerError) as e:
            logger.error(f"Grok scan failed: {e}")
            fallback = self._get_fallback_topics(max_topics)
            return TrendServiceResult(
                topics=fallback,
                source="fallback",
                cost_usd=0.0,
                filtered_count=0,
                reason=f"Grok API error: {e}",
            )

        # Record cost (post-hoc)
        if grok_result.cost_usd > 0:
            self._record_cost(
                "scan",
                grok_result.cost_usd,
                grok_result.tokens_used,
                grok_result.search_calls_used,
            )

        # Check if we need fallback
        if self._should_use_fallback(grok_result):
            logger.info("Using fallback topics (Grok returned empty)")
            fallback = self._get_fallback_topics(max_topics)
            return TrendServiceResult(
                topics=fallback,
                source="fallback",
                cost_usd=grok_result.cost_usd,
                filtered_count=0,
                reason="Grok returned no topics",
            )

        # Apply brand safety filter
        safe_topics, filtered_count = self._filter_topics(grok_result.topics)

        # Map to TrendResult
        trends = [self._map_grok_to_trend(t) for t in safe_topics[:max_topics]]

        # Store in database
        if trends:
            self._store_trends(trends)

        source = "grok_cache" if grok_result.cached else "grok"
        return TrendServiceResult(
            topics=trends,
            source=source,
            cost_usd=grok_result.cost_usd,
            filtered_count=filtered_count,
            reason=None,
        )

    async def get_latest(self, limit: int = 10) -> list[TrendResult]:
        """
        Get latest stored trends from database.

        Args:
            limit: Maximum trends to return

        Returns:
            List of TrendResult from database
        """
        conn = self._get_conn()
        return db.get_recent_trends(conn, limit=limit)

    async def suggest_topics_for_content(self, n: int = 5) -> list[TrendResult]:
        """
        Suggest high-value topics for content creation.

        Returns trends with:
        - High confidence
        - High opportunity level
        - Knowledge graph match (we have content for it)

        Args:
            n: Number of suggestions to return

        Returns:
            List of recommended TrendResult
        """
        conn = self._get_conn()
        all_trends = db.get_recent_trends(conn, limit=50)

        # Score and sort
        def score_trend(t: TrendResult) -> float:
            score = t.score * 0.4
            score += t.confidence * 0.3
            if t.knowledge_graph_match:
                score += 0.2
            level_bonus = {"urgent": 0.1, "high": 0.07, "medium": 0.03, "low": 0}
            score += level_bonus.get(t.opportunity_level, 0)
            return score

        scored = sorted(all_trends, key=score_trend, reverse=True)
        return scored[:n]
