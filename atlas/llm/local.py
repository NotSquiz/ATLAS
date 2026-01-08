"""
ATLAS Local LLM Client

Wrapper for Ollama with Qwen2.5-3B-Instruct model.
Qwen2.5 has no thinking mode - content streams immediately.
"""

import time
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import httpx


@dataclass
class LLMResponse:
    """Response from local LLM."""
    content: str
    model: str
    total_duration_ms: float
    load_duration_ms: float
    prompt_eval_count: int
    eval_count: int
    eval_duration_ms: float

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        if self.eval_duration_ms > 0:
            return (self.eval_count / self.eval_duration_ms) * 1000
        return 0.0

    @property
    def first_token_ms(self) -> float:
        """Approximate time to first token."""
        return self.total_duration_ms - self.eval_duration_ms


class OllamaClient:
    """
    Client for local Ollama LLM.

    Usage:
        client = OllamaClient()

        # Simple query
        response = client.generate("What is 2+2?")
        print(response.content)

        # Streaming
        async for chunk in client.stream("Tell me a story"):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "atlas",
        timeout: float = 60.0,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        self._async_client: Optional[httpx.AsyncClient] = None

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> LLMResponse:
        """
        Generate a response synchronously.

        Args:
            prompt: The user prompt
            system: Optional system prompt override
            temperature: Sampling temperature (default 0.7)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content and timing metrics
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        start = time.perf_counter()
        response = self._client.post(
            f"{self.host}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data.get("response", "").strip(),
            model=data.get("model", self.model),
            total_duration_ms=data.get("total_duration", 0) / 1_000_000,
            load_duration_ms=data.get("load_duration", 0) / 1_000_000,
            prompt_eval_count=data.get("prompt_eval_count", 0),
            eval_count=data.get("eval_count", 0),
            eval_duration_ms=data.get("eval_duration", 0) / 1_000_000,
        )

    async def agenerate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> LLMResponse:
        """Generate a response asynchronously."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        response = await self.async_client.post(
            f"{self.host}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data.get("response", "").strip(),
            model=data.get("model", self.model),
            total_duration_ms=data.get("total_duration", 0) / 1_000_000,
            load_duration_ms=data.get("load_duration", 0) / 1_000_000,
            prompt_eval_count=data.get("prompt_eval_count", 0),
            eval_count=data.get("eval_count", 0),
            eval_duration_ms=data.get("eval_duration", 0) / 1_000_000,
        )

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

        Uses /api/chat for proper message formatting.
        Qwen2.5-3B has no thinking mode - content streams immediately.
        """
        import json as json_module

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # Use fresh client for streaming to avoid connection reuse issues
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.host}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        data = json_module.loads(line)
                        # Get content from message (chat API)
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            if content:
                                yield content

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = self._client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def list_models(self) -> list[str]:
        """List available models."""
        try:
            response = self._client.get(f"{self.host}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except httpx.RequestError:
            return []

    def close(self) -> None:
        """Close HTTP clients."""
        self._client.close()
        if self._async_client is not None:
            # Note: In async context, use await self._async_client.aclose()
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function
def get_client(
    host: str = "http://localhost:11434",
    model: str = "atlas-local",
) -> OllamaClient:
    """Get an Ollama client instance."""
    return OllamaClient(host=host, model=model)
