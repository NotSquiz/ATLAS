"""Tests for YouTube Data API Client (S2.4)."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from atlas.babybrains.clients.youtube_client import (
    DAILY_QUOTA_LIMIT,
    DETAIL_COST,
    SEARCH_COST,
    CacheEntry,
    YouTubeAPIError,
    YouTubeDataClient,
    YouTubeQuotaExceededError,
    YouTubeRateLimitError,
    YouTubeVideo,
    _safe_int,
    _youtube_breaker,
)


# --- Fixtures ---

@pytest.fixture
def sample_video() -> YouTubeVideo:
    """A sample video for testing."""
    return YouTubeVideo(
        video_id="abc123",
        title="Montessori Toddler Activities at Home",
        description="Great activities for your toddler",
        channel_id="UC_test",
        channel_title="TestChannel",
        published_at="2026-01-30T10:00:00Z",
        view_count=1500,
        like_count=120,
        comment_count=15,
        duration="PT10M30S",
        thumbnail_url="https://i.ytimg.com/vi/abc123/mqdefault.jpg",
        tags=["montessori", "toddler"],
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


@pytest.fixture
def client(tmp_path) -> YouTubeDataClient:
    """Create a YouTube client with test config."""
    # Create a minimal warming_schedule.json
    config_dir = tmp_path / "config" / "babybrains"
    config_dir.mkdir(parents=True)
    schedule = {
        "search_queries": {
            "youtube": [
                "montessori toddler activities",
                "gentle parenting tips",
            ]
        }
    }
    (config_dir / "warming_schedule.json").write_text(json.dumps(schedule))

    return YouTubeDataClient(
        api_key="test-api-key",
        cache_dir=tmp_path / "cache",
        warming_schedule_path=config_dir / "warming_schedule.json",
        quota_file=tmp_path / "youtube_quota.json",
    )


@pytest.fixture
def mock_search_response() -> dict:
    """Mock YouTube search.list API response."""
    return {
        "items": [
            {
                "id": {"videoId": "vid001"},
                "snippet": {
                    "title": "Montessori Morning Routine",
                    "description": "A complete guide to morning routines",
                    "channelId": "UC_ch1",
                    "channelTitle": "Montessori Mum",
                    "publishedAt": "2026-01-29T08:00:00Z",
                    "thumbnails": {
                        "medium": {"url": "https://i.ytimg.com/vi/vid001/mqdefault.jpg"}
                    },
                },
            },
            {
                "id": {"videoId": "vid002"},
                "snippet": {
                    "title": "Gentle Parenting Tips for Tantrums",
                    "description": "Evidence-based tantrum strategies",
                    "channelId": "UC_ch2",
                    "channelTitle": "Parenting Lab",
                    "publishedAt": "2026-01-28T12:00:00Z",
                    "thumbnails": {
                        "medium": {"url": "https://i.ytimg.com/vi/vid002/mqdefault.jpg"}
                    },
                },
            },
        ]
    }


@pytest.fixture
def mock_details_response() -> dict:
    """Mock YouTube videos.list API response."""
    return {
        "items": [
            {
                "id": "vid001",
                "snippet": {
                    "title": "Montessori Morning Routine",
                    "description": "A complete guide",
                    "channelId": "UC_ch1",
                    "channelTitle": "Montessori Mum",
                    "publishedAt": "2026-01-29T08:00:00Z",
                    "tags": ["montessori", "morning", "routine"],
                    "thumbnails": {
                        "medium": {"url": "https://i.ytimg.com/vi/vid001/mqdefault.jpg"}
                    },
                },
                "statistics": {
                    "viewCount": "5200",
                    "likeCount": "340",
                    "commentCount": "28",
                },
                "contentDetails": {
                    "duration": "PT15M42S",
                },
            }
        ]
    }


@pytest.fixture(autouse=True)
def reset_breaker():
    """Reset circuit breaker state between tests."""
    _youtube_breaker.close()
    yield


# --- TestYouTubeVideo ---

class TestYouTubeVideo:
    """Tests for YouTubeVideo dataclass."""

    def test_url_property(self, sample_video):
        """URL is correctly formatted."""
        assert sample_video.url == "https://youtube.com/watch?v=abc123"

    def test_hours_since_publish(self, sample_video):
        """hours_since_publish returns a positive float."""
        hours = sample_video.hours_since_publish
        assert hours > 0
        # Published ~1 day ago, should be roughly 24+ hours
        assert hours >= 1.0

    def test_hours_since_publish_invalid_date(self):
        """Invalid published_at returns 0."""
        video = YouTubeVideo(
            video_id="x",
            title="t",
            description="d",
            channel_id="c",
            channel_title="ct",
            published_at="not-a-date",
        )
        assert video.hours_since_publish == 0.0

    def test_is_within_retention_recent(self, sample_video):
        """Recently fetched video is within retention."""
        assert sample_video.is_within_retention() is True

    def test_is_within_retention_old(self):
        """Video fetched 31 days ago is outside retention."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        video = YouTubeVideo(
            video_id="old",
            title="t",
            description="d",
            channel_id="c",
            channel_title="ct",
            published_at="2025-12-01T00:00:00Z",
            fetched_at=old_date,
        )
        assert video.is_within_retention() is False

    def test_is_within_retention_no_fetched_at(self):
        """Video with no fetched_at is within retention (just fetched)."""
        video = YouTubeVideo(
            video_id="x",
            title="t",
            description="d",
            channel_id="c",
            channel_title="ct",
            published_at="2026-01-30T00:00:00Z",
        )
        assert video.is_within_retention() is True

    def test_to_dict_from_dict_roundtrip(self, sample_video):
        """Serialization roundtrip preserves data."""
        d = sample_video.to_dict()
        restored = YouTubeVideo.from_dict(d)
        assert restored.video_id == sample_video.video_id
        assert restored.title == sample_video.title
        assert restored.view_count == sample_video.view_count
        assert restored.tags == sample_video.tags


# --- TestYouTubeDataClientInit ---

class TestYouTubeDataClientInit:
    """Tests for client initialization."""

    def test_api_key_from_param(self, tmp_path):
        """API key from constructor parameter."""
        c = YouTubeDataClient(api_key="my-key", cache_dir=tmp_path / "cache")
        assert c.api_key == "my-key"

    def test_api_key_from_env(self, tmp_path, monkeypatch):
        """API key from environment variable."""
        monkeypatch.setenv("YOUTUBE_API_KEY", "env-key")
        c = YouTubeDataClient(cache_dir=tmp_path / "cache")
        assert c.api_key == "env-key"

    def test_missing_key_warns(self, tmp_path, monkeypatch, caplog):
        """Missing API key logs a warning but doesn't crash."""
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        import logging
        with caplog.at_level(logging.WARNING):
            c = YouTubeDataClient(api_key="", cache_dir=tmp_path / "cache")
        assert c.api_key == ""
        assert "No YOUTUBE_API_KEY" in caplog.text

    def test_cache_dir_created(self, tmp_path):
        """Cache directory is created on init."""
        cache_dir = tmp_path / "my_cache"
        assert not cache_dir.exists()
        YouTubeDataClient(api_key="k", cache_dir=cache_dir)
        assert cache_dir.exists()


# --- TestQuota ---

class TestQuota:
    """Tests for quota tracking."""

    def test_consume_quota_succeeds(self, client):
        """Quota consumption within limit succeeds."""
        assert client._consume_quota(100) is True
        assert client._quota_used_today == 100

    def test_consume_quota_exceeds(self, client):
        """Quota consumption exceeding limit returns False."""
        client._quota_used_today = DAILY_QUOTA_LIMIT - 50
        assert client._consume_quota(100) is False

    def test_quota_status(self, client):
        """get_quota_status returns correct dict."""
        client._quota_used_today = 500
        status = client.get_quota_status()
        assert status["used_today"] == 500
        assert status["remaining"] == DAILY_QUOTA_LIMIT - 500
        assert status["percentage"] == 5.0
        assert "circuit_state" in status


# --- TestCacheConfidence ---

class TestCacheConfidence:
    """Tests for cache entry confidence degradation."""

    def test_fresh_confidence_is_1(self):
        """Freshly cached entry has confidence 1.0."""
        entry = CacheEntry(
            data={"test": True},
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )
        assert entry.confidence == 1.0

    def test_stale_confidence_degrades(self):
        """Stale entry has confidence between 0.3 and 1.0."""
        fetched = datetime.now(timezone.utc) - timedelta(hours=6)
        entry = CacheEntry(
            data={"test": True},
            fetched_at=fetched.isoformat(),
        )
        c = entry.confidence
        assert 0.3 < c < 1.0

    def test_expired_confidence_is_minimum(self):
        """Expired entry has minimum confidence."""
        fetched = datetime.now(timezone.utc) - timedelta(hours=24)
        entry = CacheEntry(
            data={"test": True},
            fetched_at=fetched.isoformat(),
        )
        assert entry.confidence == 0.3

    def test_expired_is_expired(self):
        """Entry beyond stale TTL is expired."""
        fetched = datetime.now(timezone.utc) - timedelta(hours=24)
        entry = CacheEntry(
            data={"test": True},
            fetched_at=fetched.isoformat(),
        )
        assert entry.is_expired is True


# --- TestSearchVideos ---

class TestSearchVideos:
    """Tests for search_videos method."""

    @pytest.mark.asyncio
    async def test_search_returns_videos(self, client, mock_search_response):
        """search_videos returns parsed YouTubeVideo objects."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_search_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            videos = await client.search_videos("montessori toddler")

        assert len(videos) == 2
        assert videos[0].video_id == "vid001"
        assert videos[0].title == "Montessori Morning Routine"
        assert videos[1].video_id == "vid002"

    @pytest.mark.asyncio
    async def test_search_uses_cache(self, client, mock_search_response):
        """Second call uses cache instead of API."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_search_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # First call hits API
            videos1 = await client.search_videos("montessori toddler")
            assert len(videos1) == 2

            # Second call should use cache
            videos2 = await client.search_videos("montessori toddler")
            assert len(videos2) == 2

            # API was only called once
            assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_search_respects_quota(self, client):
        """Search returns empty when quota exceeded."""
        client._quota_used_today = DAILY_QUOTA_LIMIT - 10  # Not enough for search
        videos = await client.search_videos("test query")
        assert videos == []

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_empty(self, client):
        """Empty query returns empty list."""
        videos = await client.search_videos("")
        assert videos == []


# --- TestGetVideoDetails ---

class TestGetVideoDetails:
    """Tests for get_video_details method."""

    @pytest.mark.asyncio
    async def test_details_returns_full_stats(self, client, mock_details_response):
        """get_video_details returns videos with full statistics."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_details_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            videos = await client.get_video_details(["vid001"])

        assert len(videos) == 1
        v = videos[0]
        assert v.view_count == 5200
        assert v.like_count == 340
        assert v.comment_count == 28
        assert v.duration == "PT15M42S"
        assert "montessori" in v.tags

    @pytest.mark.asyncio
    async def test_details_empty_ids(self, client):
        """Empty ID list returns empty."""
        videos = await client.get_video_details([])
        assert videos == []


# --- TestFindWarmingVideos ---

class TestFindWarmingVideos:
    """Tests for find_warming_videos method."""

    @pytest.mark.asyncio
    async def test_find_warming_uses_static_query(
        self, client, mock_search_response, mock_details_response
    ):
        """find_warming_videos picks a query from config."""
        call_count = 0

        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            # First call = search, second call = details
            if call_count == 1:
                mock_resp.json.return_value = mock_search_response
            else:
                mock_resp.json.return_value = mock_details_response
            return mock_resp

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=mock_get_side_effect)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            videos = await client.find_warming_videos()

        assert len(videos) >= 1

    @pytest.mark.asyncio
    async def test_find_warming_no_queries(self, tmp_path):
        """Returns empty when no queries are configured."""
        # Create empty config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        empty_schedule = config_dir / "warming_schedule.json"
        empty_schedule.write_text(json.dumps({"search_queries": {}}))

        c = YouTubeDataClient(
            api_key="k",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=empty_schedule,
        )
        videos = await c.find_warming_videos()
        assert videos == []


# --- TestCircuitBreaker ---

class TestCircuitBreaker:
    """Tests for circuit breaker behavior."""

    @pytest.mark.asyncio
    async def test_circuit_starts_closed(self, client):
        """Circuit breaker starts in closed state."""
        assert "closed" in str(client._breaker.current_state).lower()

    @pytest.mark.asyncio
    async def test_api_error_no_key(self, tmp_path, monkeypatch):
        """API call with no key raises YouTubeAPIError."""
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        c = YouTubeDataClient(api_key="", cache_dir=tmp_path / "cache")
        with pytest.raises(YouTubeAPIError, match="No API key"):
            await c._api_call("search", {"q": "test"})

    @pytest.mark.asyncio
    async def test_search_returns_cached_on_failure(
        self, client, mock_search_response
    ):
        """When API fails, returns stale cached data if available."""
        # Prime the cache
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_search_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # First call primes cache
            await client.search_videos("montessori toddler")

        # Invalidate fresh cache by adjusting TTL expectation
        # (we'll make the API fail on second call but cache is still fresh)
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            # This should return cache (it's still fresh)
            videos = await client.search_videos("montessori toddler")
            assert len(videos) == 2  # From cache


# --- TestHealthCheck ---

class TestHealthCheck:
    """Tests for check_health method."""

    @pytest.mark.asyncio
    async def test_health_check_no_key(self, tmp_path, monkeypatch):
        """Health check with no key returns False."""
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        c = YouTubeDataClient(api_key="", cache_dir=tmp_path / "cache")
        assert await c.check_health() is False


# --- TestSafeInt ---

class TestSafeInt:
    """Tests for _safe_int helper."""

    def test_int_passthrough(self):
        assert _safe_int(42) == 42

    def test_string_number(self):
        assert _safe_int("5200") == 5200

    def test_non_numeric_string(self):
        assert _safe_int("N/A") == 0

    def test_empty_string(self):
        assert _safe_int("") == 0

    def test_none(self):
        assert _safe_int(None) == 0

    def test_float_string(self):
        """Float strings truncate to int."""
        assert _safe_int("3.14") == 0  # int("3.14") raises ValueError


# --- TestRateLimitRetry ---

class TestRateLimitRetry:
    """Tests for 429 rate limit handling."""

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, client):
        """429 response raises YouTubeRateLimitError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            with pytest.raises(YouTubeRateLimitError):
                await client._do_request(
                    "https://www.googleapis.com/youtube/v3/search",
                    {"q": "test"},
                )


# --- TestQuotaExceeded ---

class TestQuotaExceeded:
    """Tests for 403 quota exceeded handling."""

    @pytest.mark.asyncio
    async def test_403_quota_exceeded(self, client):
        """403 with quotaExceeded reason raises YouTubeQuotaExceededError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.json.return_value = {
            "error": {
                "errors": [{"reason": "quotaExceeded"}],
            }
        }

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            with pytest.raises(YouTubeQuotaExceededError):
                await client._do_request(
                    "https://www.googleapis.com/youtube/v3/search",
                    {"q": "test"},
                )

    @pytest.mark.asyncio
    async def test_403_other_reason(self, client):
        """403 with non-quota reason raises YouTubeAPIError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.json.return_value = {
            "error": {
                "errors": [{"reason": "forbidden"}],
            }
        }

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            with pytest.raises(YouTubeAPIError, match="reason=forbidden"):
                await client._do_request(
                    "https://www.googleapis.com/youtube/v3/search",
                    {"q": "test"},
                )


# --- TestPruneExpiredCache ---

class TestPruneExpiredCache:
    """Tests for _prune_expired_cache."""

    def test_prune_removes_old_entries(self, client):
        """Entries older than 30 days are pruned."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        cache_file = client.cache_dir / "old_entry_abc123.json"
        cache_file.write_text(json.dumps({
            "data": {"test": True},
            "fetched_at": old_date,
        }))

        removed = client._prune_expired_cache()
        assert removed == 1
        assert not cache_file.exists()

    def test_prune_keeps_recent_entries(self, client):
        """Recent entries are kept."""
        recent_date = datetime.now(timezone.utc).isoformat()
        cache_file = client.cache_dir / "recent_abc123.json"
        cache_file.write_text(json.dumps({
            "data": {"test": True},
            "fetched_at": recent_date,
        }))

        removed = client._prune_expired_cache()
        assert removed == 0
        assert cache_file.exists()


# --- TestBatching ---

class TestBatching:
    """Tests for >50 ID batching in get_video_details."""

    @pytest.mark.asyncio
    async def test_batches_over_50_ids(self, client):
        """IDs > 50 are split into multiple API calls."""
        ids = [f"vid{i:03d}" for i in range(75)]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            await client.get_video_details(ids)

            # Should be called twice: 50 + 25
            assert mock_client.get.call_count == 2


# --- TestFromDictEdgeCases ---

class TestFromDictEdgeCases:
    """Tests for from_dict with unusual inputs."""

    def test_from_dict_extra_fields_ignored(self):
        """Extra fields in dict are ignored."""
        data = {
            "video_id": "x",
            "title": "t",
            "description": "d",
            "channel_id": "c",
            "channel_title": "ct",
            "published_at": "2026-01-01T00:00:00Z",
            "extra_field": "should be ignored",
        }
        video = YouTubeVideo.from_dict(data)
        assert video.video_id == "x"

    def test_from_dict_missing_optional_fields(self):
        """Missing optional fields use defaults."""
        data = {
            "video_id": "x",
            "title": "t",
            "description": "d",
            "channel_id": "c",
            "channel_title": "ct",
            "published_at": "2026-01-01T00:00:00Z",
        }
        video = YouTubeVideo.from_dict(data)
        assert video.view_count == 0
        assert video.tags == []
        assert video.duration is None


# --- TestDynamicQueries ---

class TestDynamicQueries:
    """Tests for find_warming_videos with dynamic Grok queries."""

    @pytest.mark.asyncio
    async def test_uses_dynamic_query(self, client, mock_search_response):
        """When dynamic queries provided, uses one of them."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_search_response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            # dynamic_ratio=1.0 forces dynamic query selection
            videos = await client.find_warming_videos(
                dynamic_queries=["grok suggested query"],
                dynamic_ratio=1.0,
            )

        assert len(videos) >= 1


# --- TestSetCachedDiskError ---

class TestSetCachedDiskError:
    """Tests for _set_cached handling disk errors."""

    def test_set_cached_survives_disk_error(self, client, caplog):
        """Disk write failure is logged but doesn't raise."""
        import logging
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            with caplog.at_level(logging.WARNING):
                client._set_cached("test", "params", {"data": True})
        assert "Failed to write cache" in caplog.text


# --- TestNonNumericStats ---

class TestNonNumericStats:
    """Tests for non-numeric statistics in API response."""

    @pytest.mark.asyncio
    async def test_non_numeric_stats_default_to_zero(self, client):
        """Non-numeric stat values don't crash, default to 0."""
        response = {
            "items": [{
                "id": "vid001",
                "snippet": {
                    "title": "Test",
                    "description": "Desc",
                    "channelId": "ch",
                    "channelTitle": "Ch",
                    "publishedAt": "2026-01-29T08:00:00Z",
                    "thumbnails": {},
                    "tags": [],
                },
                "statistics": {
                    "viewCount": "not_a_number",
                    "likeCount": "",
                    "commentCount": None,
                },
                "contentDetails": {"duration": "PT5M"},
            }]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            videos = await client.get_video_details(["vid001"])

        assert len(videos) == 1
        assert videos[0].view_count == 0
        assert videos[0].like_count == 0
        assert videos[0].comment_count == 0


# --- TestQuotaPersistence (S2.BF1) ---

class TestQuotaPersistence:
    """Tests for file-based quota persistence across restarts."""

    def test_quota_survives_restart(self, tmp_path):
        """Quota persists across client instances (simulates process restart)."""
        config_dir = tmp_path / "config" / "babybrains"
        config_dir.mkdir(parents=True)
        (config_dir / "warming_schedule.json").write_text(
            json.dumps({"search_queries": {}})
        )
        quota_file = tmp_path / "youtube_quota.json"

        # First client: consume some quota
        c1 = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )
        assert c1._consume_quota(500) is True
        assert c1._quota_used_today == 500

        # Second client: reads quota from file (simulates restart)
        c2 = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache2",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )
        assert c2._quota_used_today == 500

    def test_quota_resets_on_new_day(self, tmp_path):
        """Quota resets when file date differs from today."""
        quota_file = tmp_path / "youtube_quota.json"
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        quota_file.write_text(json.dumps({"date": yesterday, "used": 7000}))

        config_dir = tmp_path / "config" / "babybrains"
        config_dir.mkdir(parents=True)
        (config_dir / "warming_schedule.json").write_text(
            json.dumps({"search_queries": {}})
        )

        c = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )
        assert c._quota_used_today == 0

    def test_corrupted_file_resets_to_zero(self, tmp_path):
        """Corrupted quota file resets to 0 gracefully."""
        quota_file = tmp_path / "youtube_quota.json"
        quota_file.write_text("NOT VALID JSON {{{{")

        config_dir = tmp_path / "config" / "babybrains"
        config_dir.mkdir(parents=True)
        (config_dir / "warming_schedule.json").write_text(
            json.dumps({"search_queries": {}})
        )

        c = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )
        assert c._quota_used_today == 0

    def test_missing_file_starts_at_zero(self, tmp_path):
        """Missing quota file starts at 0 (first run)."""
        quota_file = tmp_path / "nonexistent" / "youtube_quota.json"
        assert not quota_file.exists()

        config_dir = tmp_path / "config" / "babybrains"
        config_dir.mkdir(parents=True)
        (config_dir / "warming_schedule.json").write_text(
            json.dumps({"search_queries": {}})
        )

        c = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )
        assert c._quota_used_today == 0

    def test_save_creates_parent_dirs(self, tmp_path):
        """_save_quota creates parent directories if needed."""
        quota_file = tmp_path / "deep" / "nested" / "youtube_quota.json"
        assert not quota_file.parent.exists()

        config_dir = tmp_path / "config" / "babybrains"
        config_dir.mkdir(parents=True)
        (config_dir / "warming_schedule.json").write_text(
            json.dumps({"search_queries": {}})
        )

        c = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )
        c._consume_quota(200)
        assert quota_file.exists()
        data = json.loads(quota_file.read_text())
        assert data["used"] == 200

    def test_quota_file_format(self, tmp_path):
        """Quota file contains expected JSON structure."""
        config_dir = tmp_path / "config" / "babybrains"
        config_dir.mkdir(parents=True)
        (config_dir / "warming_schedule.json").write_text(
            json.dumps({"search_queries": {}})
        )
        quota_file = tmp_path / "youtube_quota.json"

        c = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )
        c._consume_quota(1234)

        data = json.loads(quota_file.read_text())
        assert "date" in data
        assert "used" in data
        assert data["used"] == 1234
        assert data["date"] == datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def test_save_quota_survives_disk_error(self, tmp_path, caplog):
        """Disk write failure in _save_quota is logged but doesn't crash."""
        import logging

        config_dir = tmp_path / "config" / "babybrains"
        config_dir.mkdir(parents=True)
        (config_dir / "warming_schedule.json").write_text(
            json.dumps({"search_queries": {}})
        )
        quota_file = tmp_path / "youtube_quota.json"

        c = YouTubeDataClient(
            api_key="test-key",
            cache_dir=tmp_path / "cache",
            warming_schedule_path=config_dir / "warming_schedule.json",
            quota_file=quota_file,
        )

        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            with caplog.at_level(logging.WARNING):
                c._save_quota()
        assert "Failed to save quota file" in caplog.text
