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
import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential
import pybreaker

# HTTP connection pool settings for keep-alive
# Reduces latency on repeat requests by reusing TCP/TLS connections
HTTP_LIMITS = httpx.Limits(
    max_keepalive_connections=5,  # Keep 5 connections warm
    max_connections=10,
    keepalive_expiry=300.0,  # 5 minutes keep-alive
)

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

        # Configure HTTP client with connection pooling for keep-alive
        # This reuses TCP/TLS connections across requests, reducing latency
        http_client = httpx.Client(
            limits=HTTP_LIMITS,
            timeout=httpx.Timeout(timeout),
        )
        async_http_client = httpx.AsyncClient(
            limits=HTTP_LIMITS,
            timeout=httpx.Timeout(timeout),
        )

        self._client = anthropic.Anthropic(
            api_key=self.api_key,
            http_client=http_client,
        )
        self._async_client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            http_client=async_http_client,
        )

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
        # Build kwargs - only include system if we have one
        kwargs = {
            "model": self.MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": self._build_messages(prompt),
        }
        system_content = self._build_system(system)
        if system_content:
            kwargs["system"] = system_content

        async with self._async_client.messages.stream(**kwargs) as stream:
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
