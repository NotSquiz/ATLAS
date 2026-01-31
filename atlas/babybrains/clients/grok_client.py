"""
Grok API Client — Primary Intelligence Engine for Baby Brains Trend Detection

Uses Grok with Live Search (x_search + web_search tools) via the OpenAI-compatible
xAI API to find real-time parenting trends on X.com and the web.

Key design decisions:
- Grok is the PRIMARY intelligence engine (not YouTube)
- MUST enable x_search/web_search tools — without them Grok has Nov 2024 cutoff only
- Model: grok-3-fast ($0.20/$0.50 per M tokens)
- Search tool calls cost $5/1K calls on top of token costs
- Pydantic models for structured output (catches schema inconsistencies)
- Passive context system prompt embeds audience personas + competitor gaps (P14)
- Circuit breaker: aiobreaker (5 failures, 60s reset)
- Retry: tenacity (3 attempts, exponential jitter)
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from aiobreaker import CircuitBreaker, CircuitBreakerError
from pydantic import BaseModel, Field, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

# --- API ---
GROK_API_BASE = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-3-fast"
REQUEST_TIMEOUT = 60.0  # LLM + search tool calls can be slow

# --- Cost ---
INPUT_TOKEN_COST_PER_M = 0.20   # $0.20 per 1M input tokens
OUTPUT_TOKEN_COST_PER_M = 0.50  # $0.50 per 1M output tokens
SEARCH_CALL_COST = 0.005        # $0.005 per search tool call ($5/1K)


class GrokAPIError(Exception):
    """Raised when Grok API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class GrokParseError(GrokAPIError):
    """Raised when Grok response fails Pydantic validation."""

    pass


class GrokRateLimitError(GrokAPIError):
    """Raised on 429 rate limit — retried by tenacity."""

    pass


class GrokServiceUnavailableError(GrokAPIError):
    """Raised on 503 service unavailable — retried by tenacity."""

    pass


# --- Data Models (Pydantic for validation) ---

class GrokTrendTopic(BaseModel):
    """Single trend opportunity identified by Grok."""

    topic: str = Field(description="Trend topic name")
    description: str = Field(description="What's happening and why it matters")
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="Niche relevance to Baby Brains"
    )
    estimated_engagement: str = Field(description="low/medium/high/viral")
    opportunity_type: str = Field(
        description="gap/debate/seasonal/emerging/evergreen"
    )
    content_angle: str = Field(
        description="How Baby Brains should approach this differently"
    )
    source_context: list[str] = Field(
        default_factory=list,
        description="Tweet/post excerpts showing the conversation",
    )
    hashtags: list[str] = Field(default_factory=list)
    audience_overlap: Optional[str] = Field(
        default=None, description="Persona ID match from audience_segments"
    )
    knowledge_coverage: Optional[str] = Field(
        default=None, description="strong/partial/none"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Grok's confidence in this trend (human review recommended)"
    )
    saturation: str = Field(
        default="unknown", description="low/medium/high"
    )
    platform_signals: list[str] = Field(
        default_factory=list, description="Where this is trending"
    )


class GrokTrendResult(BaseModel):
    """Complete result from a Grok trend scan."""

    topics: list[GrokTrendTopic] = Field(default_factory=list)
    query_used: str = ""
    model: str = DEFAULT_MODEL
    tokens_used: int = 0
    search_calls_used: int = 0
    cached: bool = False
    scanned_at: Optional[str] = None
    cost_usd: float = 0.0


# --- Cache ---

class _CacheEntry:
    """Internal cache entry with confidence degradation."""

    def __init__(self, data: Any, fetched_at: str):
        self.data = data
        self.fetched_at = fetched_at
        self.max_age_seconds = 4 * 3600    # 4hr fresh
        self.stale_ttl_seconds = 8 * 3600  # 8hr stale-but-servable

    @property
    def confidence(self) -> float:
        fetched = datetime.fromisoformat(self.fetched_at)
        now = datetime.now(timezone.utc)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        age = (now - fetched).total_seconds()
        if age <= self.max_age_seconds:
            return 1.0
        if age > self.stale_ttl_seconds:
            return 0.3
        stale_ratio = min(
            (age - self.max_age_seconds) / self.stale_ttl_seconds, 1.0
        )
        return max(0.3, 1.0 - (0.5 * stale_ratio))

    @property
    def is_expired(self) -> bool:
        fetched = datetime.fromisoformat(self.fetched_at)
        now = datetime.now(timezone.utc)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        return (now - fetched).total_seconds() > self.stale_ttl_seconds


# --- Client ---

_grok_breaker = CircuitBreaker(fail_max=5, timeout_duration=timedelta(seconds=60))


class GrokClient:
    """
    Grok API client for Baby Brains trend detection and content opportunity discovery.

    Uses the OpenAI-compatible xAI API with x_search and web_search tools for
    real-time data access.

    Usage:
        client = GrokClient()
        result = await client.scan_opportunities(region="Australia")
        queries = await client.suggest_search_queries()
        deep = await client.deep_dive("screen time toddlers")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        cache_dir: Optional[Path] = None,
        config_dir: Optional[Path] = None,
    ):
        """
        Initialize Grok client.

        Args:
            api_key: xAI API key. Falls back to GROK_API_KEY env var.
            model: Grok model ID (default grok-3-fast).
            cache_dir: Cache directory. Defaults to ~/.cache/atlas/grok/
            config_dir: Path to config/babybrains/ for persona/competitor data.
        """
        self.api_key = api_key or os.environ.get("GROK_API_KEY", "")
        self.model = model
        self.cache_dir = cache_dir or Path.home() / ".cache" / "atlas" / "grok"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._breaker = _grok_breaker

        config_dir = config_dir or (
            Path(__file__).parent.parent.parent.parent / "config" / "babybrains"
        )
        self._audience = self._load_json(config_dir / "audience_segments.json")
        self._competitors = self._load_json(config_dir / "competitors.json")

    @staticmethod
    def _load_json(path: Path) -> dict:
        """Load a JSON config file, returning empty dict on failure."""
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load config {path}: {e}")
        return {}

    # --- System Prompt (P14: Passive Context) ---

    def _build_system_prompt(
        self, niche_focus: Optional[str] = None, region: str = "Australia"
    ) -> str:
        """
        Build rich system prompt with embedded passive context.

        Includes audience personas, competitor gaps, and knowledge coverage
        so Grok can identify opportunities without needing retrieval calls.
        """
        # Compress persona pain points
        persona_summary = []
        for p in self._audience.get("personas", []):
            pains = ", ".join(p.get("pain_points", [])[:3])
            persona_summary.append(
                f"- {p['name']} ({p.get('child_stage', '?')}): {pains}"
            )
        personas_text = "\n".join(persona_summary) if persona_summary else "N/A"

        # Competitor gaps
        gaps = []
        for group in self._competitors.get("competitors", {}).values():
            for c in group:
                gaps.append(f"- {c['name']}: {c.get('gap', 'N/A')}")
        gaps_text = "\n".join(gaps) if gaps else "N/A"

        # BB differentiation
        diff = self._competitors.get("bb_differentiation", {})
        differentiators = diff.get("key_differentiators", [])
        diff_text = "; ".join(differentiators[:4]) if differentiators else "N/A"

        focus_instruction = ""
        if niche_focus:
            focus_instruction = (
                f"\n\nFOCUS THIS SCAN ON: {niche_focus}. "
                "Prioritize trends in this area."
            )

        return f"""You are a trend analyst for Baby Brains, an Australian evidence-based \
Montessori parenting platform. Use your search tools to find CURRENT conversations \
and trends about parenting, child development, and Montessori education in {region}.

OUR AUDIENCE PERSONAS (pain points):
{personas_text}

COMPETITOR GAPS (what no one else combines):
{gaps_text}

OUR DIFFERENTIATION:
{diff_text}

WHAT MAKES A GOOD OPPORTUNITY:
- Currently trending or actively discussed on X.com / the web
- Undersaturated (few quality evidence-based responses)
- Overlaps with our knowledge base (Montessori + neuroscience)
- Targets one or more of our audience personas
- Has a clear content angle we can own

IMPORTANT: Use your search tools to find CURRENT data. Do not rely on training data \
for trend information. Search X.com for parenting conversations happening right now.
{focus_instruction}

Return your analysis as a JSON object with this structure:
{{
  "topics": [
    {{
      "topic": "string",
      "description": "string",
      "relevance_score": 0.0-1.0,
      "estimated_engagement": "low|medium|high|viral",
      "opportunity_type": "gap|debate|seasonal|emerging|evergreen",
      "content_angle": "string",
      "source_context": ["tweet/post excerpts..."],
      "hashtags": ["#tag1"],
      "audience_overlap": "persona_id or null",
      "knowledge_coverage": "strong|partial|none",
      "confidence": 0.0-1.0,
      "saturation": "low|medium|high",
      "platform_signals": ["X.com", "reddit", etc.]
    }}
  ]
}}

Return 5-10 topics, ordered by opportunity quality (best first)."""

    # --- Tool Definitions (OpenAI-compatible format) ---

    @staticmethod
    def _search_tool_definitions() -> list[dict]:
        """
        xAI search tool definitions for the chat completions API.

        These enable Grok's Live Search — without them, Grok has no current data.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "x_search",
                    "description": (
                        "Search X.com (Twitter) for current posts and conversations. "
                        "Use this to find trending parenting topics."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for X.com",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": (
                        "Search the web for current information, articles, and data. "
                        "Use this to verify trends and find additional context."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Web search query",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    # --- Cache Helpers ---

    def _cache_key(self, prefix: str, params: str) -> Path:
        param_hash = hashlib.md5(params.encode()).hexdigest()[:12]
        return self.cache_dir / f"{prefix}_{param_hash}.json"

    def _get_cached(self, prefix: str, params: str) -> Optional[_CacheEntry]:
        cache_file = self._cache_key(prefix, params)
        if not cache_file.exists():
            return None
        try:
            raw = json.loads(cache_file.read_text())
            entry = _CacheEntry(data=raw["data"], fetched_at=raw["fetched_at"])
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

    # --- API Call ---

    async def _chat_completion(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> dict:
        """
        Make a Grok chat completion call with circuit breaker and retry.

        Args:
            messages: Chat messages (system + user)
            tools: Tool definitions (x_search, web_search)

        Returns:
            Parsed JSON response from the API
        """
        if not self.api_key:
            raise GrokAPIError("No GROK_API_KEY configured")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # Low temp for structured output
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            return await self._breaker.call_async(
                self._do_request, headers, payload
            )
        except CircuitBreakerError:
            logger.warning("Grok circuit breaker OPEN — returning cached/empty")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=30),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            GrokRateLimitError,
            GrokServiceUnavailableError,
        )),
        reraise=True,
    )
    async def _do_request(self, headers: dict, payload: dict) -> dict:
        """Execute the HTTP request (retried by tenacity)."""
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{GROK_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
            )

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", "60")
                logger.warning(
                    f"Grok rate limited. Retry-After: {retry_after}s"
                )
                raise GrokRateLimitError(
                    f"Rate limited. Retry after {retry_after}s",
                    status_code=429,
                )

            if resp.status_code == 503:
                logger.warning("Grok 503: no healthy upstream")
                raise GrokServiceUnavailableError(
                    "Grok service unavailable",
                    status_code=503,
                )

            resp.raise_for_status()
            return resp.json()

    # --- Response Helpers ---

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """Strip markdown code fences from LLM response content."""
        text = text.strip()
        if not text.startswith("```"):
            return text
        lines = text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```") and not in_block:
                in_block = True
                continue
            if line.strip() == "```" and in_block:
                break
            if in_block:
                json_lines.append(line)
        return "\n".join(json_lines)

    @staticmethod
    def _extract_content(response: dict) -> str:
        """Safely extract message content from API response, handling empty choices."""
        choices = response.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    # --- Cost Calculation ---

    @staticmethod
    def _calculate_cost(
        input_tokens: int, output_tokens: int, search_calls: int
    ) -> float:
        """Calculate total cost in USD."""
        token_cost = (
            (input_tokens * INPUT_TOKEN_COST_PER_M / 1_000_000)
            + (output_tokens * OUTPUT_TOKEN_COST_PER_M / 1_000_000)
        )
        search_cost = search_calls * SEARCH_CALL_COST
        return round(token_cost + search_cost, 6)

    # --- Response Parsing ---

    def _parse_trend_response(
        self, response: dict, query_used: str
    ) -> GrokTrendResult:
        """
        Parse Grok API response into validated GrokTrendResult.

        Extracts JSON from the response content, validates with Pydantic,
        and calculates cost.
        """
        choices = response.get("choices", [])
        if not choices:
            raise GrokParseError("No choices in Grok response")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        # Count search tool calls from the response
        tool_calls = message.get("tool_calls", [])
        search_calls = len(tool_calls)

        # Extract usage
        usage = response.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Parse JSON from content (may be wrapped in markdown code block)
        json_str = self._strip_markdown_fences(content)

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Grok JSON: {e}")
            logger.debug(f"Raw response content: {content[:500]}")
            raise GrokParseError(f"Invalid JSON from Grok: {e}")

        # Validate topics with Pydantic
        topics = []
        if isinstance(parsed, list):
            raw_topics = parsed
        else:
            raw_topics = parsed.get("topics", [])
        for i, raw in enumerate(raw_topics):
            try:
                topics.append(GrokTrendTopic.model_validate(raw))
            except ValidationError as e:
                logger.warning(f"Topic {i} failed validation: {e}")
                # Skip invalid topics, don't fail the whole result

        cost = self._calculate_cost(input_tokens, output_tokens, search_calls)

        return GrokTrendResult(
            topics=topics,
            query_used=query_used,
            model=self.model,
            tokens_used=input_tokens + output_tokens,
            search_calls_used=search_calls,
            scanned_at=datetime.now(timezone.utc).isoformat(),
            cost_usd=cost,
        )

    # --- Public Methods ---

    async def scan_opportunities(
        self,
        niche_focus: Optional[str] = None,
        max_topics: int = 10,
        region: str = "Australia",
    ) -> GrokTrendResult:
        """
        Scan for trending parenting content opportunities using Grok Live Search.

        Builds a rich system prompt with audience personas and competitor gaps,
        then uses x_search/web_search tools to find current X.com conversations.

        Args:
            niche_focus: Optional focus area (e.g., "emerging", "conversations")
            max_topics: Maximum topics to request (default 10)
            region: Geographic focus (default "Australia")

        Returns:
            GrokTrendResult with validated trend topics and cost data.
        """
        cache_params = f"scan:{niche_focus}:{max_topics}:{region}"

        # Check cache
        cached = self._get_cached("scan", cache_params)
        if cached and cached.confidence >= 1.0:
            logger.debug("Cache hit (fresh) for scan_opportunities")
            result = GrokTrendResult.model_validate(cached.data)
            result.cached = True
            return result

        system_prompt = self._build_system_prompt(niche_focus, region)
        user_prompt = (
            f"Find up to {max_topics} current parenting and child development "
            f"trends in {region}. Search X.com and the web for what parents "
            "are discussing right now. Focus on opportunities where evidence-based "
            "Montessori content could fill a gap."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self._chat_completion(
                messages, tools=self._search_tool_definitions()
            )
            result = self._parse_trend_response(response, user_prompt)
        except (GrokAPIError, CircuitBreakerError) as e:
            logger.error(f"scan_opportunities failed: {e}")
            if cached:
                logger.info("Returning stale cached scan results")
                result = GrokTrendResult.model_validate(cached.data)
                result.cached = True
                return result
            return GrokTrendResult(query_used=user_prompt, model=self.model)

        # Cache the result
        self._set_cached("scan", cache_params, result.model_dump())
        logger.info(
            f"Scan found {len(result.topics)} topics, "
            f"cost: ${result.cost_usd:.4f}"
        )
        return result

    async def suggest_search_queries(
        self, max_queries: int = 3
    ) -> list[str]:
        """
        Convert current X.com trends into YouTube search queries (cross-pollination).

        Uses Grok's search tools to find what parents are discussing on X.com,
        then converts those into YouTube-optimised search terms. These feed
        into YouTubeDataClient.find_warming_videos() as dynamic queries.

        This is ToS-compliant: external intelligence (X.com via Grok) makes
        YouTube searches smarter. YouTube API just executes single search.list
        calls — no aggregation, no derived metrics.

        Args:
            max_queries: Maximum number of search queries to generate (default 3)

        Returns:
            List of YouTube-optimised search terms.
        """
        cache_params = f"queries:{max_queries}"

        cached = self._get_cached("queries", cache_params)
        if cached and cached.confidence >= 1.0:
            logger.debug("Cache hit (fresh) for suggest_search_queries")
            return cached.data

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a search query optimizer for a parenting content platform. "
                    "Search X.com for current parenting conversations in Australia, then "
                    "convert the trending topics into YouTube search queries that would "
                    "find relevant video content.\n\n"
                    "Return ONLY a JSON array of strings. Each string should be a "
                    "YouTube-optimised search query (natural language, not hashtags).\n\n"
                    'Example: ["screen time toddler new guidelines 2026", '
                    '"montessori sensory play ideas", "gentle parenting tantrums"]'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Find what Australian parents are discussing on X.com right now "
                    f"and convert the top {max_queries} topics into YouTube search "
                    "queries for finding relevant parenting videos."
                ),
            },
        ]

        try:
            response = await self._chat_completion(
                messages, tools=self._search_tool_definitions()
            )
        except (GrokAPIError, CircuitBreakerError) as e:
            logger.error(f"suggest_search_queries failed: {e}")
            if cached:
                return cached.data
            return []

        # Parse response
        content = self._extract_content(response)
        if not content:
            logger.error("Empty response from Grok suggest_search_queries")
            return []
        content = self._strip_markdown_fences(content)

        try:
            queries = json.loads(content)
            if not isinstance(queries, list):
                queries = []
            queries = [str(q) for q in queries[:max_queries]]
        except json.JSONDecodeError:
            logger.error(f"Failed to parse query suggestions: {content[:200]}")
            return []

        self._set_cached("queries", cache_params, queries)
        logger.info(f"Generated {len(queries)} search queries from X.com trends")
        return queries

    async def deep_dive(self, topic: str) -> dict:
        """
        Deep analysis of a single trending topic.

        Args:
            topic: The topic to analyze in depth.

        Returns:
            Dict with: summary, key_angles, content_hooks, counter_arguments,
            evidence_needed, target_formats.
        """
        cache_params = f"deep:{topic}"

        cached = self._get_cached("deep", cache_params)
        if cached and cached.confidence >= 1.0:
            logger.debug(f"Cache hit (fresh) for deep_dive: {topic}")
            return cached.data

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a content strategist for Baby Brains, an Australian "
                    "evidence-based Montessori parenting platform. Analyze the given "
                    "topic in depth for content creation.\n\n"
                    "Search X.com and the web for current discussions, then provide:\n"
                    "- summary: What's happening with this topic\n"
                    "- key_angles: 3-5 unique angles BB could take\n"
                    "- content_hooks: 3-5 attention-grabbing hooks\n"
                    "- counter_arguments: Common objections to address\n"
                    "- evidence_needed: What research/citations would strengthen content\n"
                    "- target_formats: Best formats (short video, long-form, carousel, etc.)\n\n"
                    "Return as a JSON object with these keys."
                ),
            },
            {
                "role": "user",
                "content": f"Deep dive analysis on: {topic}",
            },
        ]

        try:
            response = await self._chat_completion(
                messages, tools=self._search_tool_definitions()
            )
        except (GrokAPIError, CircuitBreakerError) as e:
            logger.error(f"deep_dive failed for '{topic}': {e}")
            if cached:
                return cached.data
            return {}

        content = self._extract_content(response)
        if not content:
            logger.error("Empty response from Grok deep_dive")
            return {}
        content = self._strip_markdown_fences(content)

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse deep dive response: {content[:200]}")
            return {}

        self._set_cached("deep", cache_params, result)
        logger.info(f"Deep dive complete for: {topic}")
        return result

    async def check_connection(self) -> bool:
        """
        Minimal connection check (no search tools, no significant cost).

        Returns:
            True if API key is valid and service reachable.
        """
        if not self.api_key:
            return False

        async def _ping() -> bool:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{GROK_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": "ping"}
                        ],
                        "max_tokens": 5,
                    },
                )
                return resp.status_code == 200

        try:
            return await self._breaker.call_async(_ping)
        except (httpx.HTTPError, CircuitBreakerError):
            return False
