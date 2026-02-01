"""
YouTube Data API v3 Client — ToS-Compliant Video Discovery

Simple, compliant video discovery for warming targets. NOT an intelligence engine.
Deliberately avoids cross-channel aggregation, derived metrics, and custom rankings
that violate YouTube API Terms of Service.

What this client does:
- Search for videos matching warming queries (one at a time)
- Get details on specific videos (by ID)
- Track quota usage to stay within daily 10K limit

What this client deliberately does NOT do (ToS compliance):
- Aggregate data across unrelated channels
- Calculate derived metrics (engagement_rate, view_velocity)
- Create custom trending scores or calculated rankings
- Store API data beyond 30 days
- Build cross-channel comparative analytics

Circuit breaker: aiobreaker (5 failures, 60s reset, 3-success recovery)
Retry: tenacity (3 attempts, exponential jitter, 1s base, 30s max)
Cache: File-based with confidence degradation (stale-while-revalidate)
"""

import hashlib
import json
import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from aiobreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

# --- Quota Constants ---
DAILY_QUOTA_LIMIT = 10_000
SEARCH_COST = 100
DETAIL_COST = 1
QUOTA_WARNING_THRESHOLD = 8_000

# --- API ---
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    """Raised when YouTube API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class YouTubeQuotaExceededError(YouTubeAPIError):
    """Raised when daily quota is exceeded."""

    pass


class YouTubeRateLimitError(YouTubeAPIError):
    """Raised on 429 rate limit — retried by tenacity."""

    pass


# --- Cache ---

@dataclass
class CacheEntry:
    """Cache entry with confidence degradation for stale-while-revalidate."""

    data: Any
    fetched_at: str  # ISO 8601
    max_age_seconds: float = 4 * 3600       # 4 hours fresh
    stale_ttl_seconds: float = 12 * 3600    # 12 hours stale-but-servable

    @property
    def confidence(self) -> float:
        """
        Confidence score based on cache age.

        1.0 = fresh (within max_age)
        0.5-0.9 = stale but servable
        0.3 = minimum fallback confidence
        """
        fetched = datetime.fromisoformat(self.fetched_at)
        now = datetime.now(timezone.utc)
        # Handle naive datetimes from older cache entries
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        age = (now - fetched).total_seconds()
        if age <= self.max_age_seconds:
            return 1.0
        if age > self.stale_ttl_seconds:
            return 0.3
        stale_ratio = min((age - self.max_age_seconds) / self.stale_ttl_seconds, 1.0)
        return max(0.3, 1.0 - (0.5 * stale_ratio))

    @property
    def is_expired(self) -> bool:
        """True if beyond stale TTL (should not be served)."""
        fetched = datetime.fromisoformat(self.fetched_at)
        now = datetime.now(timezone.utc)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        return (now - fetched).total_seconds() > self.stale_ttl_seconds


# --- Data Model ---

@dataclass
class YouTubeVideo:
    """A single YouTube video. No derived metrics (ToS compliance)."""

    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: str  # ISO 8601
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration: Optional[str] = None  # ISO 8601 duration
    thumbnail_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    fetched_at: Optional[str] = None  # For 30-day TTL compliance

    @property
    def url(self) -> str:
        """Direct video URL."""
        return f"https://youtube.com/watch?v={self.video_id}"

    @property
    def hours_since_publish(self) -> float:
        """Hours since video was published. Deterministic (P22)."""
        try:
            published = datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            return (now - published).total_seconds() / 3600
        except (ValueError, AttributeError):
            return 0.0

    def is_within_retention(self, max_days: int = 30) -> bool:
        """Check if data is within YouTube API 30-day storage limit."""
        if not self.fetched_at:
            return True  # No fetched_at = just retrieved
        try:
            fetched = datetime.fromisoformat(self.fetched_at)
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - fetched).days < max_days
        except (ValueError, AttributeError):
            return False

    def to_dict(self) -> dict:
        """Serialize to dict for caching."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "published_at": self.published_at,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "duration": self.duration,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "YouTubeVideo":
        """Deserialize from dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# --- Helpers ---


def _safe_int(value: Any) -> int:
    """Safely convert a value to int. YouTube API returns stats as strings."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


# --- Client ---

# Module-level circuit breaker (shared across instances)
_youtube_breaker = CircuitBreaker(fail_max=5, timeout_duration=timedelta(seconds=60))


class YouTubeDataClient:
    """
    ToS-compliant YouTube Data API v3 client for warming video discovery.

    Usage:
        client = YouTubeDataClient()
        videos = await client.search_videos("montessori toddler activities")
        details = await client.get_video_details([v.video_id for v in videos])
        warming = await client.find_warming_videos()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        warming_schedule_path: Optional[Path] = None,
        quota_file: Optional[Path] = None,
    ):
        """
        Initialize YouTube client.

        Args:
            api_key: YouTube Data API v3 key. Falls back to YOUTUBE_API_KEY env var.
            cache_dir: Cache directory. Defaults to ~/.cache/atlas/youtube/
            warming_schedule_path: Path to warming_schedule.json config.
            quota_file: Path to quota persistence file. Defaults to ~/.atlas/youtube_quota.json.
        """
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY", "")
        if not self.api_key:
            logger.warning(
                "No YOUTUBE_API_KEY set. API calls will fail. "
                "Get a key at https://console.cloud.google.com/"
            )

        self.cache_dir = cache_dir or Path.home() / ".cache" / "atlas" / "youtube"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._warming_schedule_path = warming_schedule_path or (
            Path(__file__).parent.parent.parent.parent
            / "config" / "babybrains" / "warming_schedule.json"
        )

        # Quota tracking — file-based persistence (survives restarts)
        self._quota_file = quota_file or Path.home() / ".atlas" / "youtube_quota.json"
        self._quota_used_today: int = 0
        self._quota_reset_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._load_quota()

        # Circuit breaker reference
        self._breaker = _youtube_breaker

    # --- Quota ---

    def _load_quota(self) -> None:
        """Load quota state from persistent file. Resets to 0 on missing/corrupted file."""
        try:
            if self._quota_file.exists():
                data = json.loads(self._quota_file.read_text(encoding="utf-8"))
                saved_date = data.get("date", "")
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                if saved_date == today:
                    self._quota_used_today = int(data.get("used", 0))
                    self._quota_reset_date = saved_date
                    logger.debug(
                        f"Loaded quota from file: {self._quota_used_today} used on {saved_date}"
                    )
                else:
                    # Different day — reset
                    logger.info(
                        f"Quota file is from {saved_date}, resetting for {today}"
                    )
                    self._quota_used_today = 0
                    self._quota_reset_date = today
        except (json.JSONDecodeError, ValueError, TypeError, OSError) as e:
            logger.warning(f"Failed to load quota file, resetting to 0: {e}")
            self._quota_used_today = 0
            self._quota_reset_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _save_quota(self) -> None:
        """Persist current quota state to file. Silently fails on disk errors."""
        try:
            self._quota_file.parent.mkdir(parents=True, exist_ok=True)
            self._quota_file.write_text(
                json.dumps({"date": self._quota_reset_date, "used": self._quota_used_today}),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning(f"Failed to save quota file: {e}")

    def _check_quota_reset(self) -> None:
        """Reset quota counter if new UTC day. Approximates YouTube's Pacific reset."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._quota_reset_date:
            logger.info(
                f"Quota reset: {self._quota_used_today} units used yesterday"
            )
            self._quota_used_today = 0
            self._quota_reset_date = today
            self._save_quota()

    def _consume_quota(self, units: int) -> bool:
        """
        Attempt to consume quota units.

        Returns:
            True if quota available, False if would exceed limit.
        """
        self._check_quota_reset()
        if self._quota_used_today + units > DAILY_QUOTA_LIMIT:
            logger.warning(
                f"Quota would exceed limit: {self._quota_used_today} + {units} "
                f"> {DAILY_QUOTA_LIMIT}"
            )
            return False
        self._quota_used_today += units
        self._save_quota()
        if self._quota_used_today >= QUOTA_WARNING_THRESHOLD:
            logger.warning(
                f"Quota at {self._quota_used_today}/{DAILY_QUOTA_LIMIT} "
                f"({self._quota_used_today * 100 // DAILY_QUOTA_LIMIT}%)"
            )
        return True

    def get_quota_status(self) -> dict:
        """Get current quota usage status."""
        self._check_quota_reset()
        return {
            "used_today": self._quota_used_today,
            "remaining": DAILY_QUOTA_LIMIT - self._quota_used_today,
            "percentage": round(self._quota_used_today * 100 / DAILY_QUOTA_LIMIT, 1),
            "circuit_state": str(self._breaker.current_state).split(".")[-1].lower(),
        }

    # --- Cache ---

    def _cache_key(self, prefix: str, params: str) -> Path:
        """Generate cache file path."""
        param_hash = hashlib.md5(params.encode()).hexdigest()[:12]
        return self.cache_dir / f"{prefix}_{param_hash}.json"

    def _get_cached(self, prefix: str, params: str) -> Optional[CacheEntry]:
        """Get cached entry if available."""
        cache_file = self._cache_key(prefix, params)
        if not cache_file.exists():
            return None
        try:
            raw = json.loads(cache_file.read_text())
            entry = CacheEntry(
                data=raw["data"],
                fetched_at=raw["fetched_at"],
            )
            # 30-day retention compliance
            if entry.is_expired:
                cache_file.unlink(missing_ok=True)
                return None
            return entry
        except (json.JSONDecodeError, KeyError, ValueError):
            cache_file.unlink(missing_ok=True)
            return None

    def _set_cached(self, prefix: str, params: str, data: Any) -> None:
        """Store data in cache. Silently fails on disk errors."""
        try:
            cache_file = self._cache_key(prefix, params)
            cache_file.write_text(json.dumps({
                "data": data,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }))
        except OSError as e:
            logger.warning(f"Failed to write cache: {e}")

    def _prune_expired_cache(self) -> int:
        """Remove cache entries older than 30 days. Returns count removed."""
        removed = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                raw = json.loads(f.read_text())
                fetched = datetime.fromisoformat(raw.get("fetched_at", "1970-01-01"))
                if fetched.tzinfo is None:
                    fetched = fetched.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - fetched).days >= 30:
                    f.unlink()
                    removed += 1
            except (json.JSONDecodeError, ValueError, OSError):
                f.unlink(missing_ok=True)
                removed += 1
        if removed:
            logger.info(f"Pruned {removed} expired cache entries")
        return removed

    # --- API Calls ---

    async def _api_call(self, endpoint: str, params: dict) -> dict:
        """
        Make a YouTube Data API v3 call with circuit breaker and retry.

        Args:
            endpoint: API endpoint (e.g., "search", "videos")
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        if not self.api_key:
            raise YouTubeAPIError("No API key configured")

        params["key"] = self.api_key
        url = f"{YOUTUBE_API_BASE}/{endpoint}"

        try:
            return await self._breaker.call_async(self._do_request, url, params)
        except CircuitBreakerError:
            logger.warning("YouTube circuit breaker OPEN — returning cached/empty")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=30),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            YouTubeRateLimitError,
        )),
        reraise=True,
    )
    async def _do_request(self, url: str, params: dict) -> dict:
        """Execute the HTTP request (retried by tenacity)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)

            if resp.status_code == 403:
                body = resp.json()
                errors = body.get("error", {}).get("errors", [])
                if any(e.get("reason") == "quotaExceeded" for e in errors):
                    raise YouTubeQuotaExceededError(
                        "YouTube API daily quota exceeded",
                        status_code=403,
                    )
                reason = errors[0].get("reason", "unknown") if errors else "unknown"
                raise YouTubeAPIError(
                    f"YouTube API forbidden: reason={reason}",
                    status_code=403,
                )

            if resp.status_code == 429:
                raise YouTubeRateLimitError(
                    "YouTube API rate limited", status_code=429
                )

            resp.raise_for_status()
            return resp.json()

    # --- Public Methods ---

    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        published_after: Optional[str] = None,
        region_code: str = "AU",
    ) -> list[YouTubeVideo]:
        """
        Search for videos matching a query.

        Args:
            query: Search term (e.g., "montessori toddler activities")
            max_results: Number of results (max 50, default 10)
            published_after: ISO 8601 date filter (e.g., "2026-01-01T00:00:00Z")
            region_code: Country code for results (default "AU" for Australia)

        Returns:
            List of YouTubeVideo objects (stats will be 0 — snippet only).
            Returns cached results if circuit is open or quota exceeded.
        """
        if not query or not query.strip():
            return []

        max_results = min(max_results, 50)
        cache_params = f"{query}:{max_results}:{published_after}:{region_code}"

        # Check cache first
        cached = self._get_cached("search", cache_params)
        if cached and cached.confidence >= 1.0:
            logger.debug(f"Cache hit (fresh) for search: {query}")
            return [YouTubeVideo.from_dict(v) for v in cached.data]

        # Check quota
        if not self._consume_quota(SEARCH_COST):
            if cached:
                logger.info(f"Quota exceeded, returning stale cache for: {query}")
                return [YouTubeVideo.from_dict(v) for v in cached.data]
            return []

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "regionCode": region_code,
            "relevanceLanguage": "en",
            "order": "relevance",
        }
        if published_after:
            params["publishedAfter"] = published_after

        try:
            data = await self._api_call("search", params)
        except (YouTubeAPIError, CircuitBreakerError):
            if cached:
                logger.info(f"API failed, returning stale cache for: {query}")
                return [YouTubeVideo.from_dict(v) for v in cached.data]
            return []

        now = datetime.now(timezone.utc).isoformat()
        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            vid_id = item.get("id", {}).get("videoId", "")
            if not vid_id:
                continue
            videos.append(YouTubeVideo(
                video_id=vid_id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                channel_id=snippet.get("channelId", ""),
                channel_title=snippet.get("channelTitle", ""),
                published_at=snippet.get("publishedAt", ""),
                thumbnail_url=snippet.get("thumbnails", {}).get(
                    "medium", {}
                ).get("url"),
                fetched_at=now,
            ))

        # Cache results
        self._set_cached("search", cache_params, [v.to_dict() for v in videos])
        logger.info(f"Search '{query}' returned {len(videos)} videos")
        return videos

    async def get_video_details(
        self, video_ids: list[str]
    ) -> list[YouTubeVideo]:
        """
        Get full details for specific videos by ID.

        Batches up to 50 IDs per call (1 quota unit per call).

        Args:
            video_ids: List of video IDs to fetch details for.

        Returns:
            List of YouTubeVideo with full stats (views, likes, comments, etc.)
        """
        if not video_ids:
            return []

        all_videos: list[YouTubeVideo] = []

        # Batch into groups of 50
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            batch_key = ",".join(sorted(batch))

            # Check cache
            cached = self._get_cached("details", batch_key)
            if cached and cached.confidence >= 1.0:
                logger.debug(f"Cache hit for video details batch ({len(batch)} IDs)")
                all_videos.extend(
                    [YouTubeVideo.from_dict(v) for v in cached.data]
                )
                continue

            # Check quota
            if not self._consume_quota(DETAIL_COST):
                if cached:
                    all_videos.extend(
                        [YouTubeVideo.from_dict(v) for v in cached.data]
                    )
                continue

            params = {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(batch),
            }

            try:
                data = await self._api_call("videos", params)
            except (YouTubeAPIError, CircuitBreakerError):
                if cached:
                    all_videos.extend(
                        [YouTubeVideo.from_dict(v) for v in cached.data]
                    )
                continue

            now = datetime.now(timezone.utc).isoformat()
            batch_videos = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                content = item.get("contentDetails", {})
                batch_videos.append(YouTubeVideo(
                    video_id=item.get("id", ""),
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    channel_id=snippet.get("channelId", ""),
                    channel_title=snippet.get("channelTitle", ""),
                    published_at=snippet.get("publishedAt", ""),
                    view_count=_safe_int(stats.get("viewCount", 0)),
                    like_count=_safe_int(stats.get("likeCount", 0)),
                    comment_count=_safe_int(stats.get("commentCount", 0)),
                    duration=content.get("duration"),
                    thumbnail_url=snippet.get("thumbnails", {}).get(
                        "medium", {}
                    ).get("url"),
                    tags=snippet.get("tags", []),
                    fetched_at=now,
                ))

            self._set_cached(
                "details", batch_key, [v.to_dict() for v in batch_videos]
            )
            all_videos.extend(batch_videos)

        logger.info(f"Got details for {len(all_videos)} videos")
        return all_videos

    async def find_warming_videos(
        self,
        platform: str = "youtube",
        dynamic_queries: Optional[list[str]] = None,
        dynamic_ratio: float = 0.5,
    ) -> list[YouTubeVideo]:
        """
        Find videos for today's warming session.

        Picks ONE random query (from dynamic Grok-suggested or static config)
        and runs a single search. Returns results WITHOUT ranking or scoring.
        The warming targets module (targets.py) decides engagement levels.

        Args:
            platform: Platform to get static queries for (default "youtube")
            dynamic_queries: Grok-suggested search terms (cross-pollination)
            dynamic_ratio: Chance of using dynamic vs static query (0-1)

        Returns:
            List of YouTubeVideo results from a single search query.
            Cost: 101 quota units (1 search + 1 detail batch).
        """
        query = None

        # Select query source: dynamic (Grok) or static (config)
        if dynamic_queries and random.random() < dynamic_ratio:
            query = random.choice(dynamic_queries)
            logger.info(f"Using dynamic (Grok) query: {query}")
        else:
            static_queries = self._load_static_queries(platform)
            if static_queries:
                query = random.choice(static_queries)
                logger.info(f"Using static query: {query}")

        if not query:
            logger.warning("No search queries available")
            return []

        # Search for videos
        videos = await self.search_videos(query, max_results=10)
        if not videos:
            return []

        # Enrich with full details (1 quota unit for up to 50 videos)
        video_ids = [v.video_id for v in videos]
        detailed = await self.get_video_details(video_ids)

        return detailed if detailed else videos

    async def check_health(self) -> bool:
        """
        Minimal API health check.

        Returns:
            True if API is reachable and key is valid.
        """
        if not self.api_key:
            return False

        try:
            # Cheapest possible call: channels.list for a known channel (1 unit)
            if not self._consume_quota(DETAIL_COST):
                return False
            await self._api_call("channels", {
                "part": "id",
                "id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Google Developers
                "maxResults": 1,
            })
            return True
        except (YouTubeAPIError, CircuitBreakerError):
            return False

    # --- Private Helpers ---

    def _load_static_queries(self, platform: str) -> list[str]:
        """Load search queries from warming_schedule.json."""
        try:
            if self._warming_schedule_path.exists():
                config = json.loads(
                    self._warming_schedule_path.read_text(encoding="utf-8")
                )
                return config.get("search_queries", {}).get(platform, [])
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load warming schedule: {e}")
        return []
