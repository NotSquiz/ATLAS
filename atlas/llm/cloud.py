"""
ATLAS Cloud LLM Client

Wrapper for Claude via Claude Agent SDK, using Max Plan subscription.
No API key required - uses Claude Code authentication.
"""

import time
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, StreamEvent


@dataclass
class CloudLLMResponse:
    """Response from cloud LLM."""
    content: str
    model: str
    total_duration_ms: float
    first_token_ms: float
    token_count: int

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        gen_time = self.total_duration_ms - self.first_token_ms
        if gen_time > 0:
            return (self.token_count / gen_time) * 1000
        return 0.0


class ClaudeAgentClient:
    """
    Client for Claude via Claude Agent SDK.

    Uses Max Plan subscription through Claude Code authentication.
    No API key required.

    Usage:
        client = ClaudeAgentClient(model="haiku")

        # Streaming
        async for chunk in client.stream("Tell me a story"):
            print(chunk, end="", flush=True)
    """

    # Model aliases for convenience
    MODEL_ALIASES = {
        "haiku": "haiku",
        "sonnet": "sonnet",
        "opus": "opus",
        "claude-3-5-haiku": "haiku",
        "claude-3-5-sonnet": "sonnet",
        "claude-3-opus": "opus",
    }

    def __init__(
        self,
        model: str = "haiku",
        timeout: float = 60.0,
    ):
        """
        Initialize Claude client.

        Args:
            model: Model to use - "haiku", "sonnet", or "opus"
            timeout: Request timeout in seconds
        """
        self.model = self.MODEL_ALIASES.get(model, model)
        self.timeout = timeout

    async def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> AsyncIterator[str]:
        """
        Stream response tokens as they're generated.

        Useful for voice output where we want to start TTS
        before the full response is ready.

        Args:
            prompt: User prompt
            system: Optional system prompt
            temperature: Sampling temperature (not directly supported, ignored)
            max_tokens: Maximum tokens (not directly supported, ignored)

        Yields:
            String tokens as they arrive
        """
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=system,
            allowed_tools=[],  # No tools - pure text generation
            max_turns=1,  # Single turn for voice
            include_partial_messages=True,  # Get streaming updates
        )

        async for message in query(prompt=prompt, options=options):
            # Handle streaming events
            if isinstance(message, StreamEvent):
                event = message.event
                # Check for content_block_delta which contains streamed text
                if isinstance(event, dict) and event.get('type') == 'content_block_delta':
                    delta = event.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        text = delta.get('text', '')
                        if text:
                            yield text

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> CloudLLMResponse:
        """
        Generate a complete response.

        Args:
            prompt: User prompt
            system: Optional system prompt
            temperature: Sampling temperature (ignored)
            max_tokens: Maximum tokens (ignored)

        Returns:
            CloudLLMResponse with content and timing metrics
        """
        start = time.perf_counter()
        first_token_time = None
        content_parts = []
        token_count = 0

        async for token in self.stream(prompt, system, temperature, max_tokens):
            if first_token_time is None:
                first_token_time = time.perf_counter()
            content_parts.append(token)
            token_count += 1

        end = time.perf_counter()

        return CloudLLMResponse(
            content="".join(content_parts),
            model=self.model,
            total_duration_ms=(end - start) * 1000,
            first_token_ms=(first_token_time - start) * 1000 if first_token_time else 0,
            token_count=token_count,
        )

    def is_available(self) -> bool:
        """Check if Claude Agent SDK is available."""
        try:
            # Just check if we can create options
            ClaudeAgentOptions(model=self.model)
            return True
        except Exception:
            return False


def get_claude_client(model: str = "haiku") -> ClaudeAgentClient:
    """Get a Claude client instance."""
    return ClaudeAgentClient(model=model)
