# ATLAS R29 Hybrid LLM Routing - Complete Implementation Handover

**Date:** January 6, 2026
**Status:** Ready for implementation - all research complete, dependencies installed
**Priority:** This is the critical routing layer that controls cost and quality

---

## 1. Executive Summary

### The Problem
- **Agent SDK** (Max Plan): ~6,076ms TTFT - TOO SLOW for voice
- **Local Qwen2.5-3B**: ~200ms TTFT - Fast but limited reasoning
- **Direct Haiku API**: Expected ~500ms TTFT - Fast AND capable (NOT YET TESTED)

### The Solution: Three-Tier Hybrid Architecture
| Tier | Model | % Queries | Cost | Latency | Use Case |
|------|-------|-----------|------|---------|----------|
| **1 - Valet** | Qwen2.5-3B (local) | 40-50% | Free | <200ms | Commands, device control |
| **2 - Consigliere** | Haiku 4.5 (Direct API) | 35-40% | ~$0.001/q | ~500ms | Advice, drafting |
| **3 - Operator** | Agent SDK | 10-15% | Free* | ~6s | Multi-tool, planning |

### Budget
- **Target:** $5-10/month (flexible)
- **At 100 queries/day with 75% local routing:** ~$2.40/month
- **Hard limit:** $10/month with graceful degradation

---

## 2. What's Already Done

### 2.1 Files Created
```
/home/squiz/ATLAS/
├── atlas/llm/
│   ├── __init__.py          # Exports OllamaClient, ClaudeAgentClient
│   ├── local.py             # OllamaClient - WORKING
│   └── cloud.py             # ClaudeAgentClient (Agent SDK) - WORKING but slow
├── scripts/
│   └── voice_latency_benchmark.py  # Benchmark script - WORKING
└── docs/
    └── research/
        ├── R29.AI Assistant Routing Strategy Research - Google Docs.pdf
        └── R29.LLM routing strategies for voice-first AI with three-tier architecture.md
```

### 2.2 Dependencies Installed
```bash
# Already in venv:
anthropic==0.75.0      # Direct API client
tenacity==9.1.2        # Retry logic with backoff
pybreaker==1.4.1       # Circuit breaker pattern
httpx                  # HTTP client (used by local.py)
```

### 2.3 Benchmark Results (from previous session)
| Model | TTFT | Simulated E2E | Verdict |
|-------|------|---------------|---------|
| Local Qwen2.5-3B | 175-1312ms | 2,162ms | GOOD |
| Claude Haiku (Agent SDK) | 6,076ms | 6,926ms | TOO SLOW |
| Claude Sonnet (Agent SDK) | 6,764ms | 7,614ms | TOO SLOW |

**Key insight:** Agent SDK spawns subprocess adding ~5-6s overhead. Direct API needed.

---

## 3. Interface to Match

The `OllamaClient` in `atlas/llm/local.py` defines the interface. All LLM clients must match this:

```python
class OllamaClient:
    def __init__(self, host: str, model: str, timeout: float): ...

    def generate(self, prompt: str, system: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 256) -> LLMResponse: ...

    async def agenerate(self, prompt: str, system: Optional[str] = None,
                        temperature: float = 0.7, max_tokens: int = 256) -> LLMResponse: ...

    async def stream(self, prompt: str, system: Optional[str] = None,
                     temperature: float = 0.7, max_tokens: int = 256) -> AsyncIterator[str]: ...

    def is_available(self) -> bool: ...
```

### Response Dataclass
```python
@dataclass
class LLMResponse:
    content: str
    model: str
    total_duration_ms: float
    first_token_ms: float  # Critical for voice latency
    token_count: int

    @property
    def tokens_per_second(self) -> float: ...
```

---

## 4. Files to Create

### 4.1 Direct Anthropic API Client
**File:** `/home/squiz/ATLAS/atlas/llm/api.py`

```python
"""
ATLAS Direct Anthropic API Client

Uses Haiku 4.5 for fast voice responses.
Implements prompt caching for 90% cost reduction on system prompt.
"""

import os
import time
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import anthropic
from tenacity import retry, stop_after_attempt, wait_random_exponential
import pybreaker

# Haiku 4.5 pricing (January 2026)
PRICE_INPUT_PER_M = 1.0    # $1 per million input tokens
PRICE_OUTPUT_PER_M = 5.0   # $5 per million output tokens
PRICE_CACHE_WRITE_PER_M = 1.25  # $1.25 per million for cache writes
PRICE_CACHE_READ_PER_M = 0.10   # $0.10 per million for cache hits (90% savings!)

# Circuit breaker: 3 failures -> open, 60s reset
haiku_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=60,
    exclude=[ValueError, anthropic.AuthenticationError]
)


@dataclass
class APIResponse:
    """Response from Anthropic API."""
    content: str
    model: str
    total_duration_ms: float
    first_token_ms: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def cost_usd(self) -> float:
        """Calculate cost of this request."""
        input_cost = (self.input_tokens / 1_000_000) * PRICE_INPUT_PER_M
        output_cost = (self.output_tokens / 1_000_000) * PRICE_OUTPUT_PER_M
        cache_read_cost = (self.cache_read_tokens / 1_000_000) * PRICE_CACHE_READ_PER_M
        cache_write_cost = (self.cache_write_tokens / 1_000_000) * PRICE_CACHE_WRITE_PER_M
        return input_cost + output_cost + cache_read_cost + cache_write_cost

    @property
    def tokens_per_second(self) -> float:
        gen_time = self.total_duration_ms - self.first_token_ms
        if gen_time > 0:
            return (self.output_tokens / gen_time) * 1000
        return 0.0


class AnthropicClient:
    """
    Direct Anthropic API client for Haiku 4.5.

    Matches OllamaClient interface for drop-in routing.
    Implements prompt caching for system prompt cost reduction.
    """

    MODEL = "claude-3-5-haiku-20241022"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        system_prompt: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

        self.timeout = timeout
        self.system_prompt = system_prompt
        self._client = anthropic.Anthropic(api_key=self.api_key)
        self._async_client = anthropic.AsyncAnthropic(api_key=self.api_key)

    def _build_messages(self, prompt: str):
        """Build messages with prompt caching for system prompt."""
        return [{"role": "user", "content": prompt}]

    def _build_system(self, system: Optional[str] = None):
        """Build system prompt with cache_control for 90% savings."""
        sys_prompt = system or self.system_prompt
        if not sys_prompt:
            return None

        # Enable prompt caching on system prompt
        return [{
            "type": "text",
            "text": sys_prompt,
            "cache_control": {"type": "ephemeral"}
        }]

    @haiku_breaker
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=1, max=30),
        retry=lambda e: isinstance(e, (anthropic.RateLimitError, anthropic.APITimeoutError))
    )
    async def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> AsyncIterator[str]:
        """Stream response tokens for voice TTS."""
        async with self._async_client.messages.stream(
            model=self.MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=self._build_system(system),
            messages=self._build_messages(prompt),
        ) as stream:
            async for text in stream.text_stream:
                yield text

    @haiku_breaker
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=1, max=30),
        retry=lambda e: isinstance(e, (anthropic.RateLimitError, anthropic.APITimeoutError))
    )
    async def agenerate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> APIResponse:
        """Generate complete response asynchronously."""
        start = time.perf_counter()
        first_token_time = None
        content_parts = []

        async with self._async_client.messages.stream(
            model=self.MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=self._build_system(system),
            messages=self._build_messages(prompt),
        ) as stream:
            async for text in stream.text_stream:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                content_parts.append(text)

            # Get final message for token counts
            final = await stream.get_final_message()

        end = time.perf_counter()

        return APIResponse(
            content="".join(content_parts),
            model=self.MODEL,
            total_duration_ms=(end - start) * 1000,
            first_token_ms=(first_token_time - start) * 1000 if first_token_time else 0,
            input_tokens=final.usage.input_tokens,
            output_tokens=final.usage.output_tokens,
            cache_read_tokens=getattr(final.usage, 'cache_read_input_tokens', 0),
            cache_write_tokens=getattr(final.usage, 'cache_creation_input_tokens', 0),
        )

    def is_available(self) -> bool:
        """Check if API is accessible."""
        try:
            # Quick health check
            self._client.messages.create(
                model=self.MODEL,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False


def get_haiku_client(system_prompt: Optional[str] = None) -> AnthropicClient:
    """Get a Haiku client instance."""
    return AnthropicClient(system_prompt=system_prompt)
```

### 4.2 Cost Tracker
**File:** `/home/squiz/ATLAS/atlas/llm/cost_tracker.py`

```python
"""
ATLAS LLM Cost Tracker

SQLite-based usage logging with budget enforcement.
Implements soft/hard limits and graceful degradation.
"""

import sqlite3
import hashlib
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from contextlib import contextmanager


@dataclass
class UsageRecord:
    """Single API usage record."""
    tier: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    category: str
    confidence: float


@dataclass
class BudgetStatus:
    """Current budget status."""
    daily_spend: float
    monthly_spend: float
    daily_limit: float
    monthly_limit: float

    @property
    def daily_remaining(self) -> float:
        return max(0, self.daily_limit - self.daily_spend)

    @property
    def monthly_remaining(self) -> float:
        return max(0, self.monthly_limit - self.monthly_spend)

    @property
    def can_use_api(self) -> bool:
        return self.monthly_spend < self.monthly_limit

    @property
    def thrifty_mode(self) -> bool:
        """True when approaching budget - prefer local."""
        return self.monthly_spend > (self.monthly_limit * 0.8)


class CostTracker:
    """
    Track LLM usage costs with budget enforcement.

    Budget levels:
    - Soft limit (80%): Enable "thrifty mode" - prefer local
    - Hard limit (100%): API blocked, local-only mode
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS llm_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        query_hash TEXT NOT NULL,
        tier TEXT NOT NULL,
        model TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        cost_usd REAL NOT NULL,
        latency_ms REAL NOT NULL,
        routing_confidence REAL,
        category TEXT,
        escalated BOOLEAN DEFAULT FALSE,
        escalation_reason TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_timestamp ON llm_usage(timestamp);
    CREATE INDEX IF NOT EXISTS idx_tier ON llm_usage(tier);
    CREATE INDEX IF NOT EXISTS idx_date ON llm_usage(DATE(timestamp));

    CREATE TABLE IF NOT EXISTS budget_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        daily_limit_usd REAL DEFAULT 0.33,
        monthly_limit_usd REAL DEFAULT 10.00,
        soft_limit_pct REAL DEFAULT 0.80,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    INSERT OR IGNORE INTO budget_config (id) VALUES (1);
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".atlas" / "cost_tracker.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript(self.SCHEMA)

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def log_usage(self, record: UsageRecord, query: str = "") -> None:
        """Log an API usage record."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16] if query else ""

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO llm_usage
                (query_hash, tier, model, input_tokens, output_tokens,
                 cost_usd, latency_ms, routing_confidence, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_hash, record.tier, record.model,
                record.input_tokens, record.output_tokens,
                record.cost_usd, record.latency_ms,
                record.confidence, record.category
            ))

    def get_budget_status(self) -> BudgetStatus:
        """Get current budget status."""
        with self._get_conn() as conn:
            # Get config
            config = conn.execute(
                "SELECT daily_limit_usd, monthly_limit_usd FROM budget_config WHERE id = 1"
            ).fetchone()

            # Get daily spend
            daily = conn.execute("""
                SELECT COALESCE(SUM(cost_usd), 0) as total
                FROM llm_usage WHERE DATE(timestamp) = DATE('now')
            """).fetchone()['total']

            # Get monthly spend
            monthly = conn.execute("""
                SELECT COALESCE(SUM(cost_usd), 0) as total
                FROM llm_usage
                WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
            """).fetchone()['total']

            return BudgetStatus(
                daily_spend=daily,
                monthly_spend=monthly,
                daily_limit=config['daily_limit_usd'],
                monthly_limit=config['monthly_limit_usd'],
            )

    def set_budget(self, daily: Optional[float] = None, monthly: Optional[float] = None):
        """Update budget limits."""
        with self._get_conn() as conn:
            if daily is not None:
                conn.execute(
                    "UPDATE budget_config SET daily_limit_usd = ? WHERE id = 1",
                    (daily,)
                )
            if monthly is not None:
                conn.execute(
                    "UPDATE budget_config SET monthly_limit_usd = ? WHERE id = 1",
                    (monthly,)
                )

    def get_daily_summary(self, days: int = 7) -> list[dict]:
        """Get daily usage summary for last N days."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT
                    DATE(timestamp) as date,
                    tier,
                    COUNT(*) as requests,
                    SUM(cost_usd) as cost,
                    AVG(latency_ms) as avg_latency
                FROM llm_usage
                WHERE timestamp > datetime('now', ? || ' days')
                GROUP BY DATE(timestamp), tier
                ORDER BY date DESC, tier
            """, (f"-{days}",)).fetchall()

            return [dict(row) for row in rows]


# Singleton instance
_tracker: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    """Get singleton cost tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
```

### 4.3 Semantic Router
**File:** `/home/squiz/ATLAS/atlas/llm/router.py`

```python
"""
ATLAS Semantic Router

Three-stage classification:
1. Reflex: Regex patterns (<1ms)
2. Router: Embedding similarity (~20ms)
3. Safety: Perplexity check on local response (optional)

Routes to: local, haiku, or agent_sdk
"""

import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, AsyncIterator
import numpy as np

from .local import OllamaClient
from .api import AnthropicClient, get_haiku_client
from .cloud import ClaudeAgentClient
from .cost_tracker import get_cost_tracker, UsageRecord


class Tier(Enum):
    LOCAL = "local"           # Qwen2.5-3B
    HAIKU = "haiku"           # Direct Anthropic API
    AGENT_SDK = "agent_sdk"   # Claude Agent SDK


@dataclass
class RoutingDecision:
    """Result of query classification."""
    tier: Tier
    confidence: float
    category: str
    bypass_reason: Optional[str] = None


@dataclass
class RouterConfig:
    """Router configuration."""
    # Thresholds
    local_confidence: float = 0.65
    haiku_confidence: float = 0.82
    agent_confidence: float = 0.88

    # Latency budgets (ms)
    local_latency_max: int = 200
    haiku_latency_max: int = 500
    agent_latency_max: int = 6000

    # Features
    enable_embeddings: bool = True
    enable_perplexity_check: bool = False  # Not yet implemented


class ATLASRouter:
    """
    Hybrid semantic router for ATLAS.

    Routing logic:
    1. Safety patterns -> always AGENT_SDK
    2. Reflex patterns -> LOCAL (commands, simple queries)
    3. Complex patterns -> AGENT_SDK (planning, analysis)
    4. Embedding classification -> best matching tier
    5. Default uncertain -> HAIKU (safe middle ground)
    """

    # Stage 1: Reflex patterns (regex, <1ms)
    LOCAL_PATTERNS = [
        r"^(set|start|stop|pause|resume|cancel)\s+(timer|alarm|reminder)",
        r"^what\s+time\s+is\s+it",
        r"^(turn|switch)\s+(on|off)",
        r"^volume\s+(up|down|\d+)",
        r"^(play|pause|skip|next|previous)",
        r"^calculate\s+",
        r"^convert\s+",
        r"^weather(\s+|$)",
        r"^(yes|no|okay|ok|sure|thanks|thank you)$",
        r"^(good\s+)?(morning|afternoon|evening|night)",
    ]

    AGENT_PATTERNS = [
        r"(plan|design|create|build)\s+(a|my|the)\s+",
        r"analyze\s+(my|the|this)",
        r"research\s+(the|about|how)",
        r"compare\s+.+\s+(vs|versus|and|with)",
        r"help\s+me\s+(with|understand|figure)",
        r"write\s+(a|an|the)\s+(essay|article|report|document)",
    ]

    SAFETY_PATTERNS = [
        r"(medical|health)\s+(advice|question|concern)",
        r"(symptom|medication|drug|dosage)",
        r"(legal|law|lawsuit|contract)",
        r"(emergency|urgent|critical)",
        r"(suicide|self-harm|depression)",
    ]

    # Stage 2: Prototype queries for embedding similarity
    TIER_PROTOTYPES = {
        Tier.LOCAL: [
            "what time is it",
            "set a timer for 5 minutes",
            "turn on the lights",
            "what's the weather",
            "calculate 15 times 12",
            "stop",
            "pause",
            "volume up",
            "good morning",
            "thank you",
        ],
        Tier.HAIKU: [
            "what's a good warm-up before bench press",
            "explain how compound interest works",
            "draft a polite email declining the invitation",
            "summarize this article for me",
            "what are the pros and cons of",
            "how do I improve my sleep quality",
            "suggest some healthy meal ideas",
        ],
        Tier.AGENT_SDK: [
            "plan my workout routine for the week",
            "analyze my spending over the last month",
            "research the best practices for",
            "create a detailed training program",
            "help me design a morning routine",
            "compare these two investment strategies",
            "build a meal prep schedule",
        ],
    }

    def __init__(
        self,
        config: Optional[RouterConfig] = None,
        system_prompt: Optional[str] = None,
    ):
        self.config = config or RouterConfig()
        self.system_prompt = system_prompt

        # Compile regex patterns
        self._local_re = [re.compile(p, re.IGNORECASE) for p in self.LOCAL_PATTERNS]
        self._agent_re = [re.compile(p, re.IGNORECASE) for p in self.AGENT_PATTERNS]
        self._safety_re = [re.compile(p, re.IGNORECASE) for p in self.SAFETY_PATTERNS]

        # LLM clients (lazy init)
        self._local_client: Optional[OllamaClient] = None
        self._haiku_client: Optional[AnthropicClient] = None
        self._agent_client: Optional[ClaudeAgentClient] = None

        # Embedding model (lazy init)
        self._embedder = None
        self._prototype_embeddings: Optional[dict] = None

        # Cost tracker
        self._cost_tracker = get_cost_tracker()

    def _get_embedder(self):
        """Lazy load embedding model."""
        if self._embedder is None and self.config.enable_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                # Load on CPU to save VRAM for Qwen
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

                # Pre-compute prototype embeddings
                self._prototype_embeddings = {}
                for tier, queries in self.TIER_PROTOTYPES.items():
                    self._prototype_embeddings[tier] = self._embedder.encode(queries)
            except ImportError:
                pass  # sentence-transformers not installed
        return self._embedder

    def _get_local_client(self) -> OllamaClient:
        if self._local_client is None:
            self._local_client = OllamaClient(model="qwen2.5:3b-instruct")
        return self._local_client

    def _get_haiku_client(self) -> AnthropicClient:
        if self._haiku_client is None:
            self._haiku_client = get_haiku_client(system_prompt=self.system_prompt)
        return self._haiku_client

    def _get_agent_client(self) -> ClaudeAgentClient:
        if self._agent_client is None:
            self._agent_client = ClaudeAgentClient(model="haiku")
        return self._agent_client

    def classify(self, query: str) -> RoutingDecision:
        """
        Classify query and determine routing tier.

        Three-stage cascade:
        1. Reflex patterns (regex) - <1ms
        2. Embedding similarity - ~20ms
        3. Default to HAIKU if uncertain
        """
        query_lower = query.lower().strip()
        token_count = len(query.split())

        # Stage 1a: Safety patterns -> AGENT_SDK
        for pattern in self._safety_re:
            if pattern.search(query_lower):
                return RoutingDecision(
                    tier=Tier.AGENT_SDK,
                    confidence=1.0,
                    category="safety",
                    bypass_reason="safety_keyword"
                )

        # Stage 1b: Local patterns (simple commands)
        for pattern in self._local_re:
            if pattern.search(query_lower):
                return RoutingDecision(
                    tier=Tier.LOCAL,
                    confidence=0.95,
                    category="command",
                    bypass_reason="pattern_match"
                )

        # Stage 1c: Agent patterns (complex tasks)
        for pattern in self._agent_re:
            if pattern.search(query_lower):
                return RoutingDecision(
                    tier=Tier.AGENT_SDK,
                    confidence=0.85,
                    category="complex",
                    bypass_reason="pattern_match"
                )

        # Stage 1d: Very short queries -> LOCAL
        if token_count <= 3:
            return RoutingDecision(
                tier=Tier.LOCAL,
                confidence=0.8,
                category="brief",
                bypass_reason="short_query"
            )

        # Stage 1e: Very long queries -> AGENT_SDK
        if token_count > 25:
            return RoutingDecision(
                tier=Tier.AGENT_SDK,
                confidence=0.75,
                category="complex",
                bypass_reason="long_query"
            )

        # Stage 2: Embedding classification
        embedder = self._get_embedder()
        if embedder is not None and self._prototype_embeddings:
            query_embedding = embedder.encode([query])[0]

            best_tier = Tier.HAIKU
            best_score = -1.0

            for tier, prototypes in self._prototype_embeddings.items():
                # Cosine similarity to each prototype
                similarities = np.dot(prototypes, query_embedding) / (
                    np.linalg.norm(prototypes, axis=1) * np.linalg.norm(query_embedding)
                )
                max_sim = float(np.max(similarities))

                if max_sim > best_score:
                    best_score = max_sim
                    best_tier = tier

            # Apply confidence thresholds
            if best_tier == Tier.LOCAL and best_score >= self.config.local_confidence:
                return RoutingDecision(tier=best_tier, confidence=best_score, category="embedding")
            elif best_tier == Tier.AGENT_SDK and best_score >= self.config.agent_confidence:
                return RoutingDecision(tier=best_tier, confidence=best_score, category="embedding")
            elif best_score >= self.config.haiku_confidence:
                return RoutingDecision(tier=Tier.HAIKU, confidence=best_score, category="embedding")

        # Default: HAIKU (safe middle ground)
        return RoutingDecision(
            tier=Tier.HAIKU,
            confidence=0.5,
            category="default"
        )

    async def route_and_stream(
        self,
        query: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> AsyncIterator[str]:
        """
        Classify query, route to appropriate tier, and stream response.
        """
        # Check budget
        budget = self._cost_tracker.get_budget_status()

        # Classify
        decision = self.classify(query)

        # Budget enforcement
        if not budget.can_use_api and decision.tier != Tier.LOCAL:
            decision = RoutingDecision(
                tier=Tier.LOCAL,
                confidence=1.0,
                category="budget_exceeded",
                bypass_reason="budget_limit"
            )
        elif budget.thrifty_mode and decision.tier == Tier.HAIKU:
            # In thrifty mode, downgrade marginal HAIKU queries to LOCAL
            if decision.confidence < 0.7:
                decision = RoutingDecision(
                    tier=Tier.LOCAL,
                    confidence=decision.confidence,
                    category="thrifty_downgrade",
                    bypass_reason="budget_thrifty"
                )

        sys_prompt = system or self.system_prompt
        start = time.perf_counter()
        first_token_time = None
        token_count = 0

        # Route to appropriate client
        if decision.tier == Tier.LOCAL:
            client = self._get_local_client()
            async for token in client.stream(query, sys_prompt, temperature, max_tokens):
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                token_count += 1
                yield token

        elif decision.tier == Tier.HAIKU:
            client = self._get_haiku_client()
            async for token in client.stream(query, sys_prompt, temperature, max_tokens):
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                token_count += 1
                yield token

        else:  # AGENT_SDK
            client = self._get_agent_client()
            async for token in client.stream(query, sys_prompt, temperature, max_tokens):
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                token_count += 1
                yield token

        # Log usage (for API tiers)
        end = time.perf_counter()
        if decision.tier in (Tier.HAIKU, Tier.AGENT_SDK):
            # Estimate tokens (actual count from API response would be better)
            input_tokens = len(query.split()) * 1.3  # Rough estimate
            output_tokens = token_count

            # Haiku pricing
            if decision.tier == Tier.HAIKU:
                cost = (input_tokens / 1_000_000) * 1.0 + (output_tokens / 1_000_000) * 5.0
            else:
                cost = 0  # Agent SDK is free via Max Plan

            self._cost_tracker.log_usage(
                UsageRecord(
                    tier=decision.tier.value,
                    model="haiku" if decision.tier == Tier.HAIKU else "agent_sdk",
                    input_tokens=int(input_tokens),
                    output_tokens=output_tokens,
                    cost_usd=cost,
                    latency_ms=(end - start) * 1000,
                    category=decision.category,
                    confidence=decision.confidence,
                ),
                query=query,
            )


# Convenience function
def get_router(
    config: Optional[RouterConfig] = None,
    system_prompt: Optional[str] = None,
) -> ATLASRouter:
    """Get an ATLAS router instance."""
    return ATLASRouter(config=config, system_prompt=system_prompt)
```

### 4.4 Configuration File
**File:** `/home/squiz/ATLAS/config/routing.yaml`

```yaml
# ATLAS Routing Configuration

system:
  persona: "lethal_gentleman"
  latency_budget_ms: 3000

router:
  embedding_model: "all-MiniLM-L6-v2"
  embedding_device: "cpu"  # Save VRAM for Qwen

  thresholds:
    local: 0.65      # Confidence needed to route to local
    haiku: 0.82      # Confidence for Haiku (middle tier)
    agent_sdk: 0.88  # Confidence for Agent SDK (complex)

  # Regex patterns for immediate routing (bypass embeddings)
  reflex_patterns:
    local:
      - "turn on.*"
      - "turn off.*"
      - "set timer.*"
      - "stop"
      - "pause"
      - "play"
      - "what time.*"
      - "weather.*"
    agent:
      - "plan .* for"
      - "analyze .*"
      - "research .*"
      - "compare .* vs"

budget:
  monthly_limit_usd: 10.00
  daily_limit_usd: 0.33     # ~$10/30 days
  soft_limit_pct: 0.80      # Enable thrifty mode at 80%
  hard_limit_pct: 1.00      # Block API at 100%

latency_targets_ms:
  local: 200
  haiku: 500
  agent_sdk: 6000

# Persona-appropriate failure messages (Lethal Gentleman)
failure_messages:
  budget_warning: "Resources are running low today."
  budget_exceeded: "The external archives are temporarily unavailable."
  api_timeout: "The connection is delayed. Let me work with what's available."
  api_error: "I cannot access that resource at the moment."
  misunderstanding: "I seem to have missed the nuance. Let me reconsider."

# Latency masking phrases (said immediately while waiting for cloud)
filler_phrases:
  - "Let me see..."
  - "One moment..."
  - "Give me a moment."
  - "Let me consider this."
```

### 4.5 Updated __init__.py
**File:** `/home/squiz/ATLAS/atlas/llm/__init__.py`

```python
"""LLM subsystem with local, cloud API, and Agent SDK backends."""

from .local import OllamaClient
from .cloud import ClaudeAgentClient, get_claude_client
from .api import AnthropicClient, get_haiku_client
from .router import ATLASRouter, get_router, Tier, RoutingDecision, RouterConfig
from .cost_tracker import CostTracker, get_cost_tracker, BudgetStatus

__all__ = [
    # Clients
    "OllamaClient",
    "ClaudeAgentClient",
    "get_claude_client",
    "AnthropicClient",
    "get_haiku_client",
    # Router
    "ATLASRouter",
    "get_router",
    "Tier",
    "RoutingDecision",
    "RouterConfig",
    # Cost tracking
    "CostTracker",
    "get_cost_tracker",
    "BudgetStatus",
]
```

---

## 5. Persona Integration ("Lethal Gentleman")

### 5.1 Latency Masking ("Poker Face Protocol")
When routing to cloud, immediately speak a filler phrase to mask latency:

```python
async def voice_response(query: str):
    decision = router.classify(query)

    if decision.tier in (Tier.HAIKU, Tier.AGENT_SDK):
        # Speak filler immediately (buys 1.5s perceived time)
        await tts.speak_immediate(random.choice(FILLER_PHRASES))

    async for token in router.route_and_stream(query):
        await tts.stream_token(token)
```

### 5.2 Failure Responses
| Scenario | Response |
|----------|----------|
| Cloud Timeout | "The external lines are congested. I shall work with what's available." |
| API Error | "I cannot access that resource at the moment." |
| Budget Exhausted | "The external archives are temporarily unavailable." |
| Misunderstanding | "I seem to have missed the nuance. Let me reconsider." |

### 5.3 Never Say
- "I'm switching to a more powerful model..."
- "This is complex, so I need to use the cloud..."
- "Sorry, my local capabilities aren't sufficient..."

---

## 6. Testing Requirements

### 6.1 Benchmark Direct API Latency
Add to `scripts/voice_latency_benchmark.py`:

```python
async def benchmark_direct_haiku() -> Optional[BenchmarkResult]:
    """Benchmark Direct Haiku API (not Agent SDK)."""
    from atlas.llm.api import get_haiku_client

    client = get_haiku_client()
    start = time.perf_counter()
    first_token_time = None
    tokens = []

    try:
        async for token in client.stream(
            TEST_PROMPT,
            system=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=256,
        ):
            if first_token_time is None:
                first_token_time = time.perf_counter()
            tokens.append(token)
    except Exception as e:
        print(f"  [ERROR] Direct Haiku: {e}")
        return None

    end = time.perf_counter()

    return BenchmarkResult(
        model="Haiku (Direct API)",
        ttft_ms=(first_token_time - start) * 1000,
        total_gen_ms=(end - start) * 1000,
        token_count=len(tokens),
        response_text="".join(tokens),
    )
```

### 6.2 Router Classification Tests
```python
def test_router_classification():
    router = ATLASRouter()

    # Local tier
    assert router.classify("set timer for 5 minutes").tier == Tier.LOCAL
    assert router.classify("what time is it").tier == Tier.LOCAL
    assert router.classify("stop").tier == Tier.LOCAL

    # Agent tier
    assert router.classify("plan my workout for the week").tier == Tier.AGENT_SDK
    assert router.classify("analyze my spending patterns").tier == Tier.AGENT_SDK

    # Safety -> Agent
    assert router.classify("what are the symptoms of...").tier == Tier.AGENT_SDK
```

---

## 7. Areas Requiring Further Research

### 7.1 Embedding Centroid Training
**Status:** Using prototype queries instead of trained centroids
**Need:** 200+ labeled queries per tier for proper centroid computation
**Action:** Collect real usage data, then retrain

### 7.2 Perplexity-Based Escalation
**Status:** Not implemented
**Challenge:** Ollama doesn't expose token-level logits by default
**Alternative:** Monitor response quality through user feedback

### 7.3 Direct API Latency from Australia
**Status:** Not yet tested
**Expected:** ~500ms TTFT
**Action:** Run benchmark with `ANTHROPIC_API_KEY` set

### 7.4 Prompt Caching Validation
**Status:** Implemented in code, not validated
**Need:** Confirm cache_control works and saves 90%
**Check:** Response should show cache_read_input_tokens > 0

### 7.5 LinUCB Adaptive Routing
**Status:** Not implemented
**From research:** Thompson Sampling or LinUCB for online learning
**Memory:** ~600KB for 384-dim embedding matrices
**Defer until:** Have 500+ queries with feedback signals

---

## 8. Environment Setup

### 8.1 API Key
```bash
# Add to ~/.bashrc or .env
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 8.2 Install sentence-transformers (for embedding router)
```bash
/home/squiz/ATLAS/venv/bin/pip install sentence-transformers
```

---

## 9. Implementation Order

1. **Create `atlas/llm/api.py`** - Direct Anthropic client
2. **Create `atlas/llm/cost_tracker.py`** - SQLite cost tracking
3. **Create `atlas/llm/router.py`** - Semantic router
4. **Create `config/routing.yaml`** - Configuration
5. **Update `atlas/llm/__init__.py`** - Exports
6. **Test direct API latency** - Run benchmark
7. **Integrate with voice pipeline** - Replace direct LLM call with router

---

## 10. Validation Checklist

Before considering complete:

- [ ] Direct Haiku API client created and tested
- [ ] Cost tracker logging all API calls to SQLite
- [ ] Semantic router with tier prototypes working
- [ ] Regex patterns catching obvious commands
- [ ] Circuit breaker protecting against API failures
- [ ] Budget soft/hard limits enforced
- [ ] Benchmark showing Direct API latency
- [ ] Voice pipeline integrated with router
- [ ] Filler phrases implemented for latency masking

---

## 11. Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `atlas/llm/local.py` | OllamaClient (interface to match) | EXISTS |
| `atlas/llm/cloud.py` | ClaudeAgentClient (Agent SDK) | EXISTS |
| `atlas/llm/api.py` | AnthropicClient (Direct API) | TO CREATE |
| `atlas/llm/cost_tracker.py` | SQLite cost tracking | TO CREATE |
| `atlas/llm/router.py` | ATLASRouter (semantic routing) | TO CREATE |
| `atlas/llm/__init__.py` | Module exports | TO UPDATE |
| `config/routing.yaml` | Router configuration | TO CREATE |
| `scripts/voice_latency_benchmark.py` | Benchmark script | TO UPDATE |

---

## 12. Quick Start for Fresh Agent

```bash
# 1. Activate environment
cd /home/squiz/ATLAS
source venv/bin/activate

# 2. Verify dependencies
pip list | grep -E "anthropic|tenacity|pybreaker"

# 3. Set API key (user needs to provide)
export ANTHROPIC_API_KEY="sk-ant-..."

# 4. Create the files in order listed in Section 9

# 5. Test
python -c "from atlas.llm import get_router; print('Router loaded')"
```

---

**This handover provides everything needed to implement the R29 hybrid routing system. Start with `atlas/llm/api.py` and work through the implementation order.**
