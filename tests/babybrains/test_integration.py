"""
Integration tests for YouTube + Grok clients.

These go BEYOND unit mocks:
1. Real YouTube API calls (requires YOUTUBE_API_KEY env var, costs ~101 quota units)
2. Real aiobreaker circuit breaker + tenacity retry with httpx.MockTransport
3. Adversarial Grok response parsing (malformed, truncated, weird LLM output)

Run with: pytest tests/babybrains/test_integration.py -v
Skip real API: pytest tests/babybrains/test_integration.py -v -k "not real_api"
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from aiobreaker import CircuitBreakerError

from atlas.babybrains.clients.grok_client import (
    GrokClient,
    GrokParseError,
    GrokRateLimitError,
    GrokServiceUnavailableError,
    GrokTrendResult,
    GrokTrendTopic,
    _grok_breaker,
)
from atlas.babybrains.clients.youtube_client import (
    YouTubeAPIError,
    YouTubeDataClient,
    YouTubeQuotaExceededError,
    YouTubeRateLimitError,
    YouTubeVideo,
    _youtube_breaker,
)


# ============================================================================
# PART 1: REAL YOUTUBE API TESTS
# Skip if no API key. Costs ~101 quota units per run.
# ============================================================================

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
SKIP_REAL_API = not YOUTUBE_API_KEY or len(YOUTUBE_API_KEY) < 10

real_api = pytest.mark.skipif(
    SKIP_REAL_API,
    reason="YOUTUBE_API_KEY not set or too short — skipping real API tests",
)


@pytest.fixture
def real_youtube_client(tmp_path) -> YouTubeDataClient:
    """YouTube client with real API key."""
    config_dir = tmp_path / "config" / "babybrains"
    config_dir.mkdir(parents=True)
    schedule = {
        "search_queries": {
            "youtube": [
                "montessori toddler activities",
                "gentle parenting tips australia",
            ]
        }
    }
    (config_dir / "warming_schedule.json").write_text(json.dumps(schedule))
    return YouTubeDataClient(
        api_key=YOUTUBE_API_KEY,
        cache_dir=tmp_path / "cache",
        warming_schedule_path=config_dir / "warming_schedule.json",
    )


class TestRealYouTubeAPI:
    """Tests against the LIVE YouTube Data API v3."""

    @real_api
    @pytest.mark.asyncio
    async def test_real_search_returns_videos(self, real_youtube_client):
        """Real search returns actual YouTubeVideo objects with valid data."""
        videos = await real_youtube_client.search_videos(
            "montessori toddler activities", max_results=3
        )

        assert len(videos) > 0, "Search returned no results — API issue?"
        for v in videos:
            assert isinstance(v, YouTubeVideo)
            assert v.video_id, "video_id is empty"
            assert len(v.video_id) == 11, f"Unexpected video_id length: {v.video_id}"
            assert v.title, "title is empty"
            assert v.channel_id, "channel_id is empty"
            assert v.published_at, "published_at is empty"
            assert v.url.startswith("https://youtube.com/watch?v=")
            assert v.fetched_at is not None

    @real_api
    @pytest.mark.asyncio
    async def test_real_search_then_details(self, real_youtube_client):
        """Real search + detail enrichment returns stats as integers."""
        videos = await real_youtube_client.search_videos(
            "baby sensory videos", max_results=2
        )
        assert len(videos) > 0

        ids = [v.video_id for v in videos]
        detailed = await real_youtube_client.get_video_details(ids)

        assert len(detailed) > 0, "Detail fetch returned no results"
        for v in detailed:
            # Stats should be actual integers (our _safe_int handles this)
            assert isinstance(v.view_count, int)
            assert isinstance(v.like_count, int)
            assert isinstance(v.comment_count, int)
            # Popular baby sensory videos have significant views
            assert v.view_count >= 0
            assert v.duration is not None, "duration missing from contentDetails"
            assert v.duration.startswith("PT"), f"Unexpected duration format: {v.duration}"
            assert v.tags is not None  # May be empty list but not None

    @real_api
    @pytest.mark.asyncio
    async def test_real_search_caches_on_disk(self, real_youtube_client):
        """Real results are cached to disk and served on second call."""
        query = "evidence based parenting"
        videos1 = await real_youtube_client.search_videos(query, max_results=2)
        assert len(videos1) > 0

        # Check cache file exists
        cache_files = list(real_youtube_client.cache_dir.glob("search_*.json"))
        assert len(cache_files) > 0, "No cache file written"

        # Read cache and verify it's valid JSON with our schema
        cache_data = json.loads(cache_files[0].read_text())
        assert "data" in cache_data
        assert "fetched_at" in cache_data
        assert isinstance(cache_data["data"], list)

        # Second call should use cache (no additional API call)
        initial_quota = real_youtube_client._quota_used_today
        videos2 = await real_youtube_client.search_videos(query, max_results=2)
        assert len(videos2) == len(videos1)
        assert real_youtube_client._quota_used_today == initial_quota  # No new quota

    @real_api
    @pytest.mark.asyncio
    async def test_real_find_warming_videos(self, real_youtube_client):
        """find_warming_videos works end-to-end with real API."""
        videos = await real_youtube_client.find_warming_videos()

        assert len(videos) > 0, "Warming search returned no results"
        # Should have stats (went through detail enrichment)
        assert any(v.view_count > 0 for v in videos), (
            "No video has views — detail enrichment may have failed"
        )

    @real_api
    @pytest.mark.asyncio
    async def test_real_quota_tracked(self, real_youtube_client):
        """Quota tracking works with real API calls."""
        initial = real_youtube_client._quota_used_today
        await real_youtube_client.search_videos("test", max_results=1)

        status = real_youtube_client.get_quota_status()
        assert status["used_today"] > initial
        assert status["used_today"] == initial + 100  # SEARCH_COST

    @real_api
    @pytest.mark.asyncio
    async def test_real_health_check(self, real_youtube_client):
        """Health check passes with real API key."""
        healthy = await real_youtube_client.check_health()
        assert healthy is True

    @real_api
    @pytest.mark.asyncio
    async def test_real_video_retention_check(self, real_youtube_client):
        """Fetched videos have fetched_at set and pass retention check."""
        videos = await real_youtube_client.search_videos(
            "montessori", max_results=1
        )
        assert len(videos) > 0
        v = videos[0]
        assert v.fetched_at is not None
        assert v.is_within_retention() is True
        assert v.hours_since_publish > 0


# ============================================================================
# PART 2: REAL CIRCUIT BREAKER + RETRY INTEGRATION
# Uses httpx.MockTransport — real aiobreaker + tenacity, fake HTTP.
# ============================================================================


@pytest.fixture(autouse=True)
def reset_breakers():
    """Reset both circuit breakers between tests."""
    _youtube_breaker.close()
    _grok_breaker.close()
    yield


class TestRealCircuitBreakerYouTube:
    """Real aiobreaker state transitions with YouTube client."""

    @pytest.mark.asyncio
    async def test_breaker_opens_after_5_failures(self, tmp_path):
        """Circuit breaker opens after 5 consecutive failures (real aiobreaker)."""
        call_count = 0

        def failing_transport(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(500, json={"error": "server error"})

        client = YouTubeDataClient(
            api_key="test-key", cache_dir=tmp_path / "cache"
        )

        # Patch httpx.AsyncClient to use our transport
        original_init = httpx.AsyncClient.__init__

        def patched_init(self_client, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(failing_transport)
            kwargs.pop("timeout", None)
            original_init(self_client, *args, timeout=15.0, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", patched_init):
            # Fire failures to trip the breaker.
            # breaker.call_async(_do_request) — _do_request retries 3x internally,
            # then raises. That's 1 failure to the breaker. Need 5 to trip it.
            # The 5th failure causes the breaker to open AND raise CircuitBreakerError.
            for i in range(6):
                try:
                    await client._api_call("search", {"q": "test"})
                except (YouTubeAPIError, httpx.HTTPStatusError, CircuitBreakerError):
                    pass

        # Breaker should now be open
        state = str(client._breaker.current_state).lower()
        assert "open" in state, f"Expected open, got: {state}"

        # Next call should raise CircuitBreakerError immediately
        with pytest.raises(CircuitBreakerError):
            await client._breaker.call_async(lambda: None)

    @pytest.mark.asyncio
    async def test_429_triggers_tenacity_retry(self, tmp_path):
        """429 response triggers tenacity retry (real retry, mock transport)."""
        call_count = 0

        def rate_limit_then_succeed(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return httpx.Response(429, json={})
            return httpx.Response(200, json={"items": []})

        client = YouTubeDataClient(
            api_key="test-key", cache_dir=tmp_path / "cache"
        )

        original_init = httpx.AsyncClient.__init__

        def patched_init(self_client, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(rate_limit_then_succeed)
            kwargs.pop("timeout", None)
            original_init(self_client, *args, timeout=15.0, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", patched_init):
            result = await client._api_call("search", {"q": "test"})

        # Should have retried twice then succeeded
        assert call_count == 3
        assert result == {"items": []}


class TestRealCircuitBreakerGrok:
    """Real aiobreaker state transitions with Grok client."""

    @pytest.mark.asyncio
    async def test_breaker_opens_after_5_failures(self, tmp_path):
        """Grok circuit breaker opens after 5 consecutive failures."""
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "audience_segments.json").write_text('{"personas": []}')
        (cfg / "competitors.json").write_text('{"competitors": {}}')

        def failing_transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "server error"})

        client = GrokClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            config_dir=cfg,
        )

        original_init = httpx.AsyncClient.__init__

        def patched_init(self_client, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(failing_transport)
            kwargs.pop("timeout", None)
            original_init(self_client, *args, timeout=60.0, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", patched_init):
            for i in range(5):
                try:
                    await client._chat_completion(
                        [{"role": "user", "content": "test"}]
                    )
                except (Exception,):
                    pass

        state = str(client._breaker.current_state).lower()
        assert "open" in state, f"Expected open, got: {state}"

    @pytest.mark.asyncio
    async def test_503_triggers_retry_then_succeeds(self, tmp_path):
        """503 triggers tenacity retry, then succeeds (real retry logic)."""
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "audience_segments.json").write_text('{"personas": []}')
        (cfg / "competitors.json").write_text('{"competitors": {}}')

        call_count = 0

        def flaky_transport(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return httpx.Response(503, json={"error": "no healthy upstream"})
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "pong"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 2},
                },
            )

        client = GrokClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            config_dir=cfg,
        )

        original_init = httpx.AsyncClient.__init__

        def patched_init(self_client, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(flaky_transport)
            kwargs.pop("timeout", None)
            original_init(self_client, *args, timeout=60.0, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", patched_init):
            result = await client._chat_completion(
                [{"role": "user", "content": "test"}]
            )

        assert call_count == 3
        assert result["choices"][0]["message"]["content"] == "pong"

    @pytest.mark.asyncio
    async def test_429_retries_with_real_tenacity(self, tmp_path):
        """429 triggers GrokRateLimitError which tenacity retries."""
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "audience_segments.json").write_text('{"personas": []}')
        (cfg / "competitors.json").write_text('{"competitors": {}}')

        call_count = 0

        def rate_limit_transport(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return httpx.Response(
                    429, headers={"Retry-After": "1"}, json={}
                )
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "ok"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1},
                },
            )

        client = GrokClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            config_dir=cfg,
        )

        original_init = httpx.AsyncClient.__init__

        def patched_init(self_client, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(rate_limit_transport)
            kwargs.pop("timeout", None)
            original_init(self_client, *args, timeout=60.0, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", patched_init):
            result = await client._chat_completion(
                [{"role": "user", "content": "test"}]
            )

        assert call_count == 2
        assert result["choices"][0]["message"]["content"] == "ok"


# ============================================================================
# PART 3: ADVERSARIAL GROK RESPONSE PARSING
# Feed real parser with garbage, partial, weird LLM output.
# ============================================================================


@pytest.fixture
def grok_client(tmp_path) -> GrokClient:
    """Grok client for parsing tests."""
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "audience_segments.json").write_text(json.dumps({
        "personas": [{"id": "test", "name": "Test", "child_stage": "0-12m", "pain_points": ["sleep"]}]
    }))
    (cfg / "competitors.json").write_text(json.dumps({
        "competitors": {"au": [{"name": "X", "gap": "Y"}]},
        "bb_differentiation": {"key_differentiators": ["evidence-based"]},
    }))
    return GrokClient(
        api_key="test-key",
        cache_dir=tmp_path / "cache",
        config_dir=cfg,
    )


class TestAdversarialGrokParsing:
    """Feed garbage through the REAL Grok response parser."""

    def _make_response(self, content: str, tool_calls: int = 0) -> dict:
        """Build a fake API response with given content."""
        tc = [
            {"id": f"call_{i}", "function": {"name": "x_search"}}
            for i in range(tool_calls)
        ]
        return {
            "choices": [{
                "message": {
                    "content": content,
                    "tool_calls": tc,
                },
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

    def test_valid_json_parses(self, grok_client):
        """Normal valid JSON parses correctly."""
        content = json.dumps({
            "topics": [{
                "topic": "Test",
                "description": "D",
                "relevance_score": 0.5,
                "estimated_engagement": "medium",
                "opportunity_type": "gap",
                "content_angle": "A",
            }]
        })
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 1

    def test_empty_string_raises(self, grok_client):
        """Empty content raises GrokParseError."""
        with pytest.raises(GrokParseError):
            grok_client._parse_trend_response(
                self._make_response(""), "test"
            )

    def test_plain_text_raises(self, grok_client):
        """Non-JSON text raises GrokParseError."""
        with pytest.raises(GrokParseError):
            grok_client._parse_trend_response(
                self._make_response("I couldn't find any trends right now."), "test"
            )

    def test_truncated_json_raises(self, grok_client):
        """Truncated JSON raises GrokParseError."""
        with pytest.raises(GrokParseError):
            grok_client._parse_trend_response(
                self._make_response('{"topics": [{"topic": "Test", "desc'), "test"
            )

    def test_html_response_raises(self, grok_client):
        """HTML error page raises GrokParseError."""
        with pytest.raises(GrokParseError):
            grok_client._parse_trend_response(
                self._make_response("<html><body>Error 502</body></html>"), "test"
            )

    def test_nested_markdown_json_block(self, grok_client):
        """Triple-nested markdown code block."""
        inner = json.dumps({"topics": [{
            "topic": "T", "description": "D", "relevance_score": 0.5,
            "estimated_engagement": "m", "opportunity_type": "gap",
            "content_angle": "A",
        }]})
        content = f"```json\n{inner}\n```"
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 1

    def test_markdown_with_preamble_text(self, grok_client):
        """LLM adds text before the JSON block (common Grok behavior)."""
        inner = json.dumps({"topics": [{
            "topic": "T", "description": "D", "relevance_score": 0.5,
            "estimated_engagement": "m", "opportunity_type": "gap",
            "content_angle": "A",
        }]})
        # Text before code block — our parser starts at ```
        content = f"Here are the trends I found:\n\n```json\n{inner}\n```\n\nLet me know!"
        # This should fail because the parser strips from first ``` to closing ```
        # but the content starts with "Here are..." not "```"
        # Wait — our _strip_markdown_fences checks if text starts with ```
        # This WON'T be stripped. The "Here are..." text will be passed to json.loads
        # which will raise JSONDecodeError → GrokParseError
        with pytest.raises(GrokParseError):
            grok_client._parse_trend_response(
                self._make_response(content), "test"
            )

    def test_unicode_content(self, grok_client):
        """Unicode characters in topic data."""
        content = json.dumps({"topics": [{
            "topic": "育児トレンド 2026",  # Japanese
            "description": "日本の子育てトレンド",
            "relevance_score": 0.3,
            "estimated_engagement": "low",
            "opportunity_type": "emerging",
            "content_angle": "Cross-cultural Montessori",
        }]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 1
        assert "育児" in result.topics[0].topic

    def test_emoji_in_content(self, grok_client):
        """Emoji in LLM output."""
        content = json.dumps({"topics": [{
            "topic": "Screen Time Debate 📱",
            "description": "Parents debating 🤔",
            "relevance_score": 0.7,
            "estimated_engagement": "high",
            "opportunity_type": "debate",
            "content_angle": "Evidence > emotion 🧪",
        }]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 1

    def test_topics_as_flat_list(self, grok_client):
        """LLM returns a flat list instead of {topics: [...]}."""
        content = json.dumps([{
            "topic": "T", "description": "D", "relevance_score": 0.5,
            "estimated_engagement": "m", "opportunity_type": "gap",
            "content_angle": "A",
        }])
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        # Our parser handles this: parsed if isinstance(parsed, list) else []
        assert len(result.topics) == 1

    def test_empty_topics_list(self, grok_client):
        """LLM returns empty topics array."""
        content = json.dumps({"topics": []})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 0
        assert result.cost_usd >= 0

    def test_all_topics_invalid(self, grok_client):
        """Every topic fails Pydantic validation — result has 0 topics."""
        content = json.dumps({"topics": [
            {"topic": "A", "missing": "required fields"},
            {"nope": "not even close"},
        ]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 0

    def test_mixed_valid_invalid_topics(self, grok_client):
        """Mix of valid and invalid topics — valid ones kept."""
        content = json.dumps({"topics": [
            {
                "topic": "Good", "description": "D", "relevance_score": 0.5,
                "estimated_engagement": "m", "opportunity_type": "gap",
                "content_angle": "A",
            },
            {"garbage": True},
            {
                "topic": "Also Good", "description": "D", "relevance_score": 0.9,
                "estimated_engagement": "high", "opportunity_type": "emerging",
                "content_angle": "B",
            },
        ]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 2

    def test_relevance_score_boundary_0(self, grok_client):
        """relevance_score at exactly 0.0 is valid."""
        content = json.dumps({"topics": [{
            "topic": "T", "description": "D", "relevance_score": 0.0,
            "estimated_engagement": "low", "opportunity_type": "gap",
            "content_angle": "A",
        }]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 1
        assert result.topics[0].relevance_score == 0.0

    def test_relevance_score_boundary_1(self, grok_client):
        """relevance_score at exactly 1.0 is valid."""
        content = json.dumps({"topics": [{
            "topic": "T", "description": "D", "relevance_score": 1.0,
            "estimated_engagement": "viral", "opportunity_type": "gap",
            "content_angle": "A",
        }]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 1
        assert result.topics[0].relevance_score == 1.0

    def test_relevance_score_out_of_range_filtered(self, grok_client):
        """relevance_score > 1.0 fails validation, topic is skipped."""
        content = json.dumps({"topics": [{
            "topic": "T", "description": "D", "relevance_score": 1.5,
            "estimated_engagement": "viral", "opportunity_type": "gap",
            "content_angle": "A",
        }]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 0

    def test_negative_relevance_score_filtered(self, grok_client):
        """Negative relevance_score fails validation."""
        content = json.dumps({"topics": [{
            "topic": "T", "description": "D", "relevance_score": -0.5,
            "estimated_engagement": "low", "opportunity_type": "gap",
            "content_angle": "A",
        }]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 0

    def test_cost_calculation_with_tool_calls(self, grok_client):
        """Cost includes search tool calls."""
        content = json.dumps({"topics": []})
        result = grok_client._parse_trend_response(
            self._make_response(content, tool_calls=5), "test"
        )
        # 100 input + 50 output tokens, 5 search calls
        expected_token_cost = (100 * 0.20 / 1_000_000) + (50 * 0.50 / 1_000_000)
        expected_search_cost = 5 * 0.005
        assert abs(result.cost_usd - (expected_token_cost + expected_search_cost)) < 0.0001
        assert result.search_calls_used == 5

    def test_no_choices_raises_parse_error(self, grok_client):
        """Response with no choices raises GrokParseError."""
        with pytest.raises(GrokParseError, match="No choices"):
            grok_client._parse_trend_response(
                {"choices": [], "usage": {}}, "test"
            )

    def test_very_large_response(self, grok_client):
        """Response with many topics (stress test parser)."""
        topics = []
        for i in range(50):
            topics.append({
                "topic": f"Topic {i}",
                "description": f"Description for topic {i} " * 20,
                "relevance_score": round(i / 50, 2),
                "estimated_engagement": "medium",
                "opportunity_type": "emerging",
                "content_angle": f"Angle {i}",
                "source_context": [f"Post excerpt {j}" for j in range(5)],
                "hashtags": [f"#tag{j}" for j in range(3)],
            })
        content = json.dumps({"topics": topics})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 50

    def test_extra_fields_in_topic_ignored(self, grok_client):
        """Extra fields from LLM are silently ignored by Pydantic."""
        content = json.dumps({"topics": [{
            "topic": "T", "description": "D", "relevance_score": 0.5,
            "estimated_engagement": "m", "opportunity_type": "gap",
            "content_angle": "A",
            "made_up_field": "should be ignored",
            "another_extra": 42,
        }]})
        result = grok_client._parse_trend_response(
            self._make_response(content), "test"
        )
        assert len(result.topics) == 1


# ============================================================================
# PART 4: END-TO-END GROK PARSING WITH REALISTIC MOCK TRANSPORT
# Full scan_opportunities flow with httpx.MockTransport (no class patching)
# ============================================================================


class TestGrokEndToEndParsing:
    """Full scan_opportunities with MockTransport — real parsing pipeline."""

    @pytest.mark.asyncio
    async def test_scan_end_to_end_with_mock_transport(self, tmp_path):
        """Full scan_opportunities with realistic mock response."""
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "audience_segments.json").write_text(json.dumps({
            "personas": [{"id": "p1", "name": "P1", "child_stage": "0-12m", "pain_points": ["sleep"]}]
        }))
        (cfg / "competitors.json").write_text(json.dumps({
            "competitors": {"au": [{"name": "C1", "gap": "no science"}]},
            "bb_differentiation": {"key_differentiators": ["evidence-based"]},
        }))

        api_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({"topics": [
                        {
                            "topic": "Sleep training debate 2026",
                            "description": "Australian parents debating new sleep guidelines",
                            "relevance_score": 0.85,
                            "estimated_engagement": "high",
                            "opportunity_type": "debate",
                            "content_angle": "Evidence-based sleep with Montessori principles",
                            "source_context": ["Lots of discussion on X about CIO vs gentle"],
                            "hashtags": ["#sleeptraining", "#gentleparenting"],
                            "audience_overlap": "p1",
                            "knowledge_coverage": "strong",
                            "confidence": 0.8,
                            "saturation": "medium",
                            "platform_signals": ["X.com", "reddit"],
                        }
                    ]}),
                    "tool_calls": [
                        {"id": "c1", "function": {"name": "x_search"}},
                    ],
                },
            }],
            "usage": {"prompt_tokens": 800, "completion_tokens": 300},
        }

        def mock_transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=api_response)

        client = GrokClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            config_dir=cfg,
        )

        original_init = httpx.AsyncClient.__init__

        def patched_init(self_client, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(mock_transport)
            kwargs.pop("timeout", None)
            original_init(self_client, *args, timeout=60.0, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", patched_init):
            result = await client.scan_opportunities(region="Australia")

        assert isinstance(result, GrokTrendResult)
        assert len(result.topics) == 1
        assert result.topics[0].topic == "Sleep training debate 2026"
        assert result.topics[0].relevance_score == 0.85
        assert result.topics[0].audience_overlap == "p1"
        assert result.search_calls_used == 1
        assert result.cost_usd > 0
        assert result.cached is False
        assert result.tokens_used == 1100  # 800 + 300

    @pytest.mark.asyncio
    async def test_suggest_queries_end_to_end(self, tmp_path):
        """Full suggest_search_queries flow with MockTransport."""
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "audience_segments.json").write_text('{"personas": []}')
        (cfg / "competitors.json").write_text('{"competitors": {}}')

        api_response = {
            "choices": [{
                "message": {
                    "content": '```json\n["toddler sleep regression", "montessori at home"]\n```',
                },
            }],
            "usage": {"prompt_tokens": 200, "completion_tokens": 30},
        }

        def mock_transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=api_response)

        client = GrokClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            config_dir=cfg,
        )

        original_init = httpx.AsyncClient.__init__

        def patched_init(self_client, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(mock_transport)
            kwargs.pop("timeout", None)
            original_init(self_client, *args, timeout=60.0, **kwargs)

        with patch.object(httpx.AsyncClient, "__init__", patched_init):
            queries = await client.suggest_search_queries(max_queries=2)

        assert len(queries) == 2
        assert "sleep regression" in queries[0]
