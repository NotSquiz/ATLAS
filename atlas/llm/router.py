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
        # Timer/alarm - flexible: "set a 30 second timer", "start timer", etc.
        r"(set|start|stop|pause|resume|cancel).*(timer|alarm|reminder)",
        r"timer\s+for\s+\d+",  # "timer for 30 seconds"
        r"\d+\s*(second|minute|hour)s?\s+timer",  # "30 second timer"
        # Time queries
        r"what\s+time",
        r"what's\s+the\s+time",
        # Smart home
        r"(turn|switch)\s+(on|off|the)",
        r"lights?\s+(on|off)",
        r"volume\s+(up|down|\d+)",
        # Media
        r"^(play|pause|skip|next|previous|stop)\s*(music|song|track)?$",
        # Math
        r"(calculate|compute|what('s| is))\s+\d+",
        r"^\d+\s*[\+\-\*\/x]\s*\d+",  # "5 + 3", "10 * 2"
        # Conversions
        r"convert\s+\d+",
        r"how\s+(many|much).*(in|to)\s+",
        # Weather
        r"weather",
        r"temperature",
        r"(is\s+it|will\s+it)\s+(rain|snow|sunny|cold|hot)",
        # Simple acknowledgments
        r"^(yes|no|okay|ok|sure|thanks|thank you|yep|nope|yeah|nah)$",
        r"^(good\s+)?(morning|afternoon|evening|night|bye|goodbye|hello|hi)$",
        # Simple questions about ATLAS itself
        r"^(who|what)\s+(are\s+you|is\s+your\s+name)",
        r"^can\s+you\s+hear\s+me",
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
