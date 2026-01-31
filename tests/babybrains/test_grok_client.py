"""Tests for Grok API Client (S2.5)."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError

from atlas.babybrains.clients.grok_client import (
    DEFAULT_MODEL,
    GrokAPIError,
    GrokClient,
    GrokParseError,
    GrokRateLimitError,
    GrokServiceUnavailableError,
    GrokTrendResult,
    GrokTrendTopic,
    _CacheEntry,
    _grok_breaker,
)


# --- Fixtures ---


@pytest.fixture
def config_dir(tmp_path) -> Path:
    """Create test config directory with audience/competitor data."""
    cfg = tmp_path / "config"
    cfg.mkdir()

    (cfg / "audience_segments.json").write_text(json.dumps({
        "personas": [
            {
                "id": "anxious_new_parent",
                "name": "Anxious New Parent",
                "child_stage": "0-12 months",
                "pain_points": [
                    "Sleep deprivation decisions",
                    "Conflicting advice",
                    "Fear of developmental damage",
                ],
            },
            {
                "id": "toddler_wrangler",
                "name": "Toddler Wrangler",
                "child_stage": "12-36 months",
                "pain_points": [
                    "Tantrums in public",
                    "Screen time guilt",
                    "Picky eating battles",
                ],
            },
        ]
    }))

    (cfg / "competitors.json").write_text(json.dumps({
        "competitors": {
            "australia": [
                {
                    "name": "Chantel Mila",
                    "gap": "No evidence-based developmental science",
                },
                {
                    "name": "Maggie Dent",
                    "gap": "Not Montessori-specific",
                },
            ]
        },
        "bb_differentiation": {
            "key_differentiators": [
                "Evidence-based with real citations",
                "Neuroscience + Montessori intersection",
                "Australian-first",
            ]
        },
    }))

    return cfg


@pytest.fixture
def client(tmp_path, config_dir) -> GrokClient:
    """Create a Grok client with test config."""
    return GrokClient(
        api_key="test-grok-key",
        cache_dir=tmp_path / "cache",
        config_dir=config_dir,
    )


@pytest.fixture
def mock_scan_response() -> dict:
    """Mock Grok chat completion response for scan_opportunities."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "topics": [
                            {
                                "topic": "Screen time guidelines 2026",
                                "description": "New WHO guidelines on toddler screen time",
                                "relevance_score": 0.85,
                                "estimated_engagement": "high",
                                "opportunity_type": "emerging",
                                "content_angle": "Evidence-based breakdown with Montessori alternatives",
                                "source_context": ["Parents debating new limits on X"],
                                "hashtags": ["#screentime", "#toddlerlife"],
                                "audience_overlap": "toddler_wrangler",
                                "knowledge_coverage": "strong",
                                "confidence": 0.8,
                                "saturation": "medium",
                                "platform_signals": ["X.com", "reddit"],
                            },
                            {
                                "topic": "Montessori floor beds debate",
                                "description": "Parents sharing floor bed experiences",
                                "relevance_score": 0.9,
                                "estimated_engagement": "medium",
                                "opportunity_type": "debate",
                                "content_angle": "Safety research + age-appropriate guidance",
                                "source_context": ["Thread about floor bed safety"],
                                "hashtags": ["#montessori", "#floorbed"],
                                "audience_overlap": "montessori_curious",
                                "knowledge_coverage": "strong",
                                "confidence": 0.75,
                                "saturation": "low",
                                "platform_signals": ["X.com"],
                            },
                        ]
                    }),
                    "tool_calls": [
                        {"id": "call_1", "function": {"name": "x_search"}},
                        {"id": "call_2", "function": {"name": "web_search"}},
                    ],
                },
            }
        ],
        "usage": {
            "prompt_tokens": 800,
            "completion_tokens": 400,
        },
    }


@pytest.fixture
def mock_query_response() -> dict:
    """Mock Grok response for suggest_search_queries."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps([
                        "screen time toddler new guidelines 2026",
                        "montessori floor bed safety tips",
                        "gentle parenting tantrums australia",
                    ]),
                },
            }
        ],
        "usage": {"prompt_tokens": 200, "completion_tokens": 50},
    }


@pytest.fixture
def mock_deep_dive_response() -> dict:
    """Mock Grok response for deep_dive."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "summary": "Screen time guidelines updated by WHO",
                        "key_angles": ["Evidence breakdown", "Montessori alternatives"],
                        "content_hooks": ["The REAL reason screen time matters"],
                        "counter_arguments": ["Some screen time is educational"],
                        "evidence_needed": ["WHO 2026 report", "AAP guidelines"],
                        "target_formats": ["short video", "carousel"],
                    }),
                },
            }
        ],
        "usage": {"prompt_tokens": 300, "completion_tokens": 200},
    }


@pytest.fixture(autouse=True)
def reset_breaker():
    """Reset circuit breaker between tests."""
    _grok_breaker.close()
    yield


# --- TestGrokTrendTopic ---

class TestGrokTrendTopic:
    """Tests for GrokTrendTopic Pydantic model."""

    def test_valid_topic(self):
        """Valid data passes Pydantic validation."""
        topic = GrokTrendTopic(
            topic="Test trend",
            description="A test",
            relevance_score=0.7,
            estimated_engagement="high",
            opportunity_type="emerging",
            content_angle="Our take",
        )
        assert topic.topic == "Test trend"
        assert topic.relevance_score == 0.7

    def test_field_constraints(self):
        """relevance_score must be 0-1."""
        with pytest.raises(ValidationError):
            GrokTrendTopic(
                topic="Bad score",
                description="Test",
                relevance_score=1.5,  # Invalid
                estimated_engagement="high",
                opportunity_type="gap",
                content_angle="Test",
            )

    def test_defaults(self):
        """Default values are set correctly."""
        topic = GrokTrendTopic(
            topic="Minimal",
            description="Test",
            relevance_score=0.5,
            estimated_engagement="medium",
            opportunity_type="gap",
            content_angle="Test angle",
        )
        assert topic.confidence == 0.5
        assert topic.saturation == "unknown"
        assert topic.hashtags == []
        assert topic.platform_signals == []
        assert topic.audience_overlap is None
        assert topic.knowledge_coverage is None


# --- TestGrokTrendResult ---

class TestGrokTrendResult:
    """Tests for GrokTrendResult Pydantic model."""

    def test_empty_result(self):
        """Empty result has sensible defaults."""
        result = GrokTrendResult()
        assert result.topics == []
        assert result.tokens_used == 0
        assert result.cost_usd == 0.0
        assert result.cached is False

    def test_serialization_roundtrip(self, mock_scan_response):
        """Model can be serialized and deserialized."""
        result = GrokTrendResult(
            topics=[
                GrokTrendTopic(
                    topic="Test",
                    description="Desc",
                    relevance_score=0.5,
                    estimated_engagement="medium",
                    opportunity_type="gap",
                    content_angle="Angle",
                )
            ],
            query_used="test query",
            model="grok-3-fast",
            tokens_used=100,
            cost_usd=0.001,
        )
        dumped = result.model_dump()
        restored = GrokTrendResult.model_validate(dumped)
        assert len(restored.topics) == 1
        assert restored.topics[0].topic == "Test"


# --- TestGrokClientInit ---

class TestGrokClientInit:
    """Tests for client initialization."""

    def test_api_key_from_param(self, tmp_path, config_dir):
        """API key from constructor parameter."""
        c = GrokClient(
            api_key="my-key", cache_dir=tmp_path / "cache", config_dir=config_dir
        )
        assert c.api_key == "my-key"

    def test_api_key_from_env(self, tmp_path, config_dir, monkeypatch):
        """API key from environment variable."""
        monkeypatch.setenv("GROK_API_KEY", "env-key")
        c = GrokClient(cache_dir=tmp_path / "cache", config_dir=config_dir)
        assert c.api_key == "env-key"

    def test_loads_audience_config(self, client):
        """Client loads audience personas at init."""
        assert len(client._audience.get("personas", [])) == 2

    def test_loads_competitor_config(self, client):
        """Client loads competitor data at init."""
        assert "competitors" in client._competitors

    def test_model_selection(self, tmp_path, config_dir):
        """Custom model can be specified."""
        c = GrokClient(
            api_key="k",
            model="grok-3",
            cache_dir=tmp_path / "cache",
            config_dir=config_dir,
        )
        assert c.model == "grok-3"

    def test_cache_dir_created(self, tmp_path, config_dir):
        """Cache directory is created on init."""
        cache_dir = tmp_path / "new_cache"
        assert not cache_dir.exists()
        GrokClient(api_key="k", cache_dir=cache_dir, config_dir=config_dir)
        assert cache_dir.exists()


# --- TestSystemPrompt ---

class TestSystemPrompt:
    """Tests for the passive context system prompt (P14)."""

    def test_prompt_contains_personas(self, client):
        """System prompt includes audience persona pain points."""
        prompt = client._build_system_prompt()
        assert "Anxious New Parent" in prompt
        assert "Sleep deprivation" in prompt

    def test_prompt_contains_competitor_gaps(self, client):
        """System prompt includes competitor gaps."""
        prompt = client._build_system_prompt()
        assert "Chantel Mila" in prompt
        assert "No evidence-based" in prompt

    def test_prompt_contains_differentiation(self, client):
        """System prompt includes BB differentiation."""
        prompt = client._build_system_prompt()
        assert "Evidence-based" in prompt

    def test_prompt_includes_focus(self, client):
        """Niche focus is added to prompt."""
        prompt = client._build_system_prompt(niche_focus="emerging trends")
        assert "FOCUS THIS SCAN ON: emerging trends" in prompt

    def test_prompt_includes_region(self, client):
        """Region is included in prompt."""
        prompt = client._build_system_prompt(region="New Zealand")
        assert "New Zealand" in prompt


# --- TestSearchTools ---

class TestSearchTools:
    """Tests for search tool definitions."""

    def test_tool_definitions_structure(self):
        """Tool definitions match OpenAI function calling format."""
        tools = GrokClient._search_tool_definitions()
        assert len(tools) == 2
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "x_search"
        assert tools[1]["function"]["name"] == "web_search"

    def test_tool_definitions_have_params(self):
        """Each tool has a query parameter."""
        tools = GrokClient._search_tool_definitions()
        for tool in tools:
            params = tool["function"]["parameters"]
            assert "query" in params["properties"]
            assert "query" in params["required"]


# --- TestCostCalculation ---

class TestCostCalculation:
    """Tests for cost tracking."""

    def test_cost_calculation(self):
        """Cost includes tokens + search calls."""
        cost = GrokClient._calculate_cost(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            search_calls=10,
        )
        # $0.20 input + $0.50 output + $0.05 search = $0.75
        expected = 0.20 + 0.50 + (10 * 0.005)
        assert abs(cost - expected) < 0.001

    def test_cost_zero(self):
        """Zero usage = zero cost."""
        assert GrokClient._calculate_cost(0, 0, 0) == 0.0

    def test_cost_search_only(self):
        """Cost with search calls only."""
        cost = GrokClient._calculate_cost(0, 0, 100)
        assert abs(cost - 0.5) < 0.001


# --- TestScanOpportunities ---

class TestScanOpportunities:
    """Tests for scan_opportunities method."""

    @pytest.mark.asyncio
    async def test_scan_returns_validated_result(self, client, mock_scan_response):
        """scan_opportunities returns a validated GrokTrendResult."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_scan_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await client.scan_opportunities(region="Australia")

        assert isinstance(result, GrokTrendResult)
        assert len(result.topics) == 2
        assert result.topics[0].topic == "Screen time guidelines 2026"
        assert result.topics[0].relevance_score == 0.85
        assert result.search_calls_used == 2
        assert result.cost_usd > 0

    @pytest.mark.asyncio
    async def test_scan_caches_result(self, client, mock_scan_response):
        """Second call uses cache."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_scan_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # First call
            result1 = await client.scan_opportunities()
            assert result1.cached is False

            # Second call should use cache
            result2 = await client.scan_opportunities()
            assert result2.cached is True
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_scan_no_key_returns_empty(self, tmp_path, config_dir, monkeypatch):
        """scan_opportunities with no API key returns empty result."""
        monkeypatch.delenv("GROK_API_KEY", raising=False)
        c = GrokClient(
            api_key="", cache_dir=tmp_path / "cache", config_dir=config_dir
        )
        result = await c.scan_opportunities()
        assert result.topics == []

    @pytest.mark.asyncio
    async def test_scan_invalid_json_raises_parse_error(self, client):
        """Invalid JSON from Grok raises GrokParseError internally but returns empty."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "not json at all"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # GrokParseError raised by _parse_trend_response,
            # which is a subclass of GrokAPIError, caught by scan_opportunities
            result = await client.scan_opportunities()
            assert result.topics == []

    @pytest.mark.asyncio
    async def test_scan_tracks_cost(self, client, mock_scan_response):
        """Cost is calculated including search tool calls."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_scan_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await client.scan_opportunities()

        assert result.cost_usd > 0
        assert result.tokens_used == 1200  # 800 + 400
        assert result.search_calls_used == 2

    @pytest.mark.asyncio
    async def test_scan_partial_validation(self, client):
        """Valid topics are kept even if some fail validation."""
        response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "topics": [
                            {
                                "topic": "Valid topic",
                                "description": "Good",
                                "relevance_score": 0.8,
                                "estimated_engagement": "high",
                                "opportunity_type": "gap",
                                "content_angle": "Our angle",
                            },
                            {
                                "topic": "Bad topic",
                                "description": "Invalid",
                                "relevance_score": 5.0,  # Invalid: > 1.0
                                "estimated_engagement": "high",
                                "opportunity_type": "gap",
                                "content_angle": "Bad",
                            },
                        ]
                    }),
                },
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await client.scan_opportunities()

        # Only the valid topic should pass
        assert len(result.topics) == 1
        assert result.topics[0].topic == "Valid topic"


# --- TestSuggestSearchQueries ---

class TestSuggestSearchQueries:
    """Tests for suggest_search_queries method."""

    @pytest.mark.asyncio
    async def test_returns_queries(self, client, mock_query_response):
        """Returns YouTube-optimised search terms."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_query_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            queries = await client.suggest_search_queries(max_queries=3)

        assert len(queries) == 3
        assert "screen time" in queries[0].lower()

    @pytest.mark.asyncio
    async def test_caches_queries(self, client, mock_query_response):
        """Second call uses cache."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_query_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            queries1 = await client.suggest_search_queries()
            queries2 = await client.suggest_search_queries()
            assert queries1 == queries2
            assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_respects_max_queries(self, client, mock_query_response):
        """Respects max_queries limit."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_query_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            queries = await client.suggest_search_queries(max_queries=2)

        assert len(queries) <= 2

    @pytest.mark.asyncio
    async def test_returns_empty_on_failure(self, tmp_path, config_dir, monkeypatch):
        """Returns empty list when API fails and no cache."""
        monkeypatch.delenv("GROK_API_KEY", raising=False)
        c = GrokClient(
            api_key="", cache_dir=tmp_path / "cache", config_dir=config_dir
        )
        queries = await c.suggest_search_queries()
        assert queries == []


# --- TestDeepDive ---

class TestDeepDive:
    """Tests for deep_dive method."""

    @pytest.mark.asyncio
    async def test_returns_structured_dict(self, client, mock_deep_dive_response):
        """deep_dive returns expected structure."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_deep_dive_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await client.deep_dive("screen time toddlers")

        assert "summary" in result
        assert "key_angles" in result
        assert "content_hooks" in result
        assert "counter_arguments" in result
        assert "evidence_needed" in result
        assert "target_formats" in result

    @pytest.mark.asyncio
    async def test_deep_dive_caches(self, client, mock_deep_dive_response):
        """Deep dive results are cached separately."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_deep_dive_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result1 = await client.deep_dive("screen time")
            result2 = await client.deep_dive("screen time")
            assert result1 == result2
            assert mock_client.post.call_count == 1


# --- TestCheckConnection ---

class TestCheckConnection:
    """Tests for check_connection method."""

    @pytest.mark.asyncio
    async def test_connection_success(self, client):
        """Successful connection returns True."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            assert await client.check_connection() is True

    @pytest.mark.asyncio
    async def test_connection_no_key(self, tmp_path, config_dir, monkeypatch):
        """No API key returns False."""
        monkeypatch.delenv("GROK_API_KEY", raising=False)
        c = GrokClient(
            api_key="", cache_dir=tmp_path / "cache", config_dir=config_dir
        )
        assert await c.check_connection() is False


# --- TestCircuitBreaker ---

class TestCircuitBreaker:
    """Tests for circuit breaker behavior."""

    def test_breaker_starts_closed(self, client):
        """Circuit breaker starts in closed state."""
        assert "closed" in str(client._breaker.current_state).lower()

    @pytest.mark.asyncio
    async def test_scan_returns_cached_on_api_failure(
        self, client, mock_scan_response
    ):
        """When API fails, stale cache is returned."""
        # Prime cache
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_scan_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await client.scan_opportunities()

        # Now fail the API
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # Should return cached (still fresh)
            result = await client.scan_opportunities()
            assert result.cached is True
            assert len(result.topics) == 2


# --- TestCacheEntry ---

class TestCacheEntry:
    """Tests for internal cache entry."""

    def test_fresh_confidence(self):
        """Fresh entry has confidence 1.0."""
        entry = _CacheEntry(
            data={"test": True},
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )
        assert entry.confidence == 1.0

    def test_stale_confidence_degrades(self):
        """Stale entry has degraded confidence."""
        fetched = datetime.now(timezone.utc) - timedelta(hours=6)
        entry = _CacheEntry(
            data={"test": True},
            fetched_at=fetched.isoformat(),
        )
        c = entry.confidence
        assert 0.3 < c < 1.0

    def test_expired_is_expired(self):
        """Entry beyond stale TTL is expired."""
        fetched = datetime.now(timezone.utc) - timedelta(hours=12)
        entry = _CacheEntry(
            data={"test": True},
            fetched_at=fetched.isoformat(),
        )
        assert entry.is_expired is True


# --- TestMarkdownCodeFenceStripping ---

class TestMarkdownStripping:
    """Tests for JSON extraction from markdown-wrapped responses."""

    @pytest.mark.asyncio
    async def test_scan_handles_markdown_wrapped_json(self, client):
        """Grok sometimes wraps JSON in markdown code fences."""
        response = {
            "choices": [{
                "message": {
                    "content": '```json\n{"topics": [{"topic": "Test", '
                    '"description": "D", "relevance_score": 0.5, '
                    '"estimated_engagement": "medium", '
                    '"opportunity_type": "gap", "content_angle": "A"}]}\n```',
                },
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await client.scan_opportunities()

        assert len(result.topics) == 1
        assert result.topics[0].topic == "Test"


# --- TestEmptyChoices ---

class TestEmptyChoices:
    """Tests for empty choices in API response (IndexError guard)."""

    @pytest.mark.asyncio
    async def test_suggest_queries_empty_choices(self, client):
        """suggest_search_queries handles empty choices without IndexError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [],
            "usage": {"prompt_tokens": 10, "completion_tokens": 0},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            queries = await client.suggest_search_queries()

        assert queries == []

    @pytest.mark.asyncio
    async def test_deep_dive_empty_choices(self, client):
        """deep_dive handles empty choices without IndexError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [],
            "usage": {"prompt_tokens": 10, "completion_tokens": 0},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            result = await client.deep_dive("test topic")

        assert result == {}

    @pytest.mark.asyncio
    async def test_scan_empty_choices(self, client):
        """scan_opportunities handles empty choices (GrokParseError -> empty)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [],
            "usage": {"prompt_tokens": 10, "completion_tokens": 0},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            result = await client.scan_opportunities()

        assert result.topics == []


# --- TestDeepDiveParseFailure ---

class TestDeepDiveParseFailure:
    """Tests for deep_dive JSON parse failure."""

    @pytest.mark.asyncio
    async def test_deep_dive_invalid_json(self, client):
        """deep_dive returns empty dict on invalid JSON."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "not valid json at all"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            result = await client.deep_dive("test topic")

        assert result == {}


# --- TestRateLimitRetry ---

class TestGrokRateLimitRetry:
    """Tests for 429/503 rate limit and service unavailable handling."""

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        """429 response raises GrokRateLimitError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.headers = {"Retry-After": "30"}

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            with pytest.raises(GrokRateLimitError):
                await client._do_request(
                    {"Authorization": "Bearer test"},
                    {"model": "grok-3-fast", "messages": []},
                )

    @pytest.mark.asyncio
    async def test_503_raises_service_unavailable(self, client):
        """503 response raises GrokServiceUnavailableError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 503

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            with pytest.raises(GrokServiceUnavailableError):
                await client._do_request(
                    {"Authorization": "Bearer test"},
                    {"model": "grok-3-fast", "messages": []},
                )


# --- TestSuggestQueriesMarkdown ---

class TestSuggestQueriesMarkdown:
    """Tests for markdown-wrapped query suggestions."""

    @pytest.mark.asyncio
    async def test_suggest_queries_markdown_wrapped(self, client):
        """Markdown-wrapped JSON array is parsed correctly."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{
                "message": {
                    "content": (
                        '```json\n["screen time toddlers", '
                        '"montessori activities"]\n```'
                    ),
                },
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 30},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            queries = await client.suggest_search_queries()

        assert len(queries) == 2
        assert "screen time" in queries[0]


# --- TestSuggestQueriesNonList ---

class TestSuggestQueriesNonList:
    """Tests for non-list JSON response in suggest_search_queries."""

    @pytest.mark.asyncio
    async def test_non_list_response(self, client):
        """Non-list JSON response returns empty list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"error": "unexpected format"}',
                },
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 30},
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            queries = await client.suggest_search_queries()

        assert queries == []


# --- TestSetCachedDiskError ---

class TestGrokSetCachedDiskError:
    """Tests for _set_cached handling disk errors."""

    def test_set_cached_survives_disk_error(self, client, caplog):
        """Disk write failure is logged but doesn't raise."""
        import logging
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            with caplog.at_level(logging.WARNING):
                client._set_cached("test", "params", {"data": True})
        assert "Failed to write cache" in caplog.text


# --- TestStripMarkdownFences ---

class TestStripMarkdownFences:
    """Tests for _strip_markdown_fences helper."""

    def test_plain_json(self):
        """Plain JSON is returned as-is."""
        assert GrokClient._strip_markdown_fences('{"key": "value"}') == '{"key": "value"}'

    def test_json_code_block(self):
        """JSON in markdown code block is extracted."""
        text = '```json\n{"key": "value"}\n```'
        assert GrokClient._strip_markdown_fences(text) == '{"key": "value"}'

    def test_plain_code_block(self):
        """Plain ``` code block is extracted."""
        text = '```\n{"key": "value"}\n```'
        assert GrokClient._strip_markdown_fences(text) == '{"key": "value"}'

    def test_empty_string(self):
        assert GrokClient._strip_markdown_fences("") == ""

    def test_whitespace_trimmed(self):
        assert GrokClient._strip_markdown_fences("  hello  ") == "hello"


# --- TestExtractContent ---

class TestExtractContent:
    """Tests for _extract_content helper."""

    def test_normal_response(self):
        resp = {"choices": [{"message": {"content": "hello"}}]}
        assert GrokClient._extract_content(resp) == "hello"

    def test_empty_choices(self):
        resp = {"choices": []}
        assert GrokClient._extract_content(resp) == ""

    def test_missing_choices(self):
        resp = {}
        assert GrokClient._extract_content(resp) == ""

    def test_missing_message(self):
        resp = {"choices": [{}]}
        assert GrokClient._extract_content(resp) == ""
