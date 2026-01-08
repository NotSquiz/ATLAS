#!/usr/bin/env python3
"""
Voice Latency Benchmark

Compares LLM latency for voice interactions:
- Local Qwen2.5-3B (via Ollama)
- Claude Haiku (via Agent SDK)
- Claude Sonnet (via Agent SDK)

Measures time-to-first-token and total generation time,
then calculates simulated end-to-end voice latency.
"""

import asyncio
import sys
import time
from dataclasses import dataclass
from typing import Optional

# Add project root to path
sys.path.insert(0, "/home/squiz/ATLAS")

from atlas.llm.local import OllamaClient
from atlas.llm.cloud import ClaudeAgentClient
from atlas.llm.api import get_haiku_client


# Simulated voice component latencies (from actual measurements)
STT_LATENCY_MS = 600    # Moonshine Base on CPU
TTS_LATENCY_MS = 250    # Kokoro first audio

# Test prompt - representative of voice query
TEST_PROMPT = "What's a good warm-up before bench press?"
SYSTEM_PROMPT = "You are ATLAS—a mentor who speaks economically. Keep responses to 1-3 sentences. Be direct."

# Number of test runs per model
NUM_RUNS = 3


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    model: str
    ttft_ms: float          # Time to first token
    total_gen_ms: float     # Total generation time
    token_count: int
    response_text: str

    @property
    def simulated_e2e_ms(self) -> float:
        """Simulated end-to-end latency including STT and TTS."""
        return STT_LATENCY_MS + self.ttft_ms + TTS_LATENCY_MS

    @property
    def tokens_per_second(self) -> float:
        """Token generation speed."""
        gen_time = self.total_gen_ms - self.ttft_ms
        if gen_time > 0:
            return (self.token_count / gen_time) * 1000
        return 0.0


async def benchmark_ollama() -> Optional[BenchmarkResult]:
    """Benchmark local Qwen2.5-3B via Ollama."""
    client = OllamaClient(model="qwen2.5:3b-instruct")

    if not client.is_available():
        print("  [SKIP] Ollama not available")
        return None

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
        print(f"  [ERROR] Ollama: {e}")
        return None

    end = time.perf_counter()

    if first_token_time is None:
        return None

    return BenchmarkResult(
        model="Qwen2.5-3B (local)",
        ttft_ms=(first_token_time - start) * 1000,
        total_gen_ms=(end - start) * 1000,
        token_count=len(tokens),
        response_text="".join(tokens),
    )


async def benchmark_direct_haiku() -> Optional[BenchmarkResult]:
    """Benchmark Direct Haiku API (not Agent SDK)."""
    try:
        client = get_haiku_client()
    except ValueError as e:
        print(f"  [SKIP] Direct Haiku: {e}")
        return None

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

    if first_token_time is None:
        print("  [WARN] No tokens received from Direct Haiku")
        return None

    return BenchmarkResult(
        model="Haiku (Direct API)",
        ttft_ms=(first_token_time - start) * 1000,
        total_gen_ms=(end - start) * 1000,
        token_count=len(tokens),
        response_text="".join(tokens),
    )


async def benchmark_claude(model: str) -> Optional[BenchmarkResult]:
    """Benchmark Claude via Agent SDK."""
    client = ClaudeAgentClient(model=model)

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
        print(f"  [ERROR] Claude {model}: {e}")
        return None

    end = time.perf_counter()

    if first_token_time is None:
        print(f"  [WARN] No tokens received from Claude {model}")
        return None

    return BenchmarkResult(
        model=f"Claude {model.capitalize()}",
        ttft_ms=(first_token_time - start) * 1000,
        total_gen_ms=(end - start) * 1000,
        token_count=len(tokens),
        response_text="".join(tokens),
    )


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results table."""
    print("\n" + "=" * 70)
    print("Voice Latency Benchmark Results")
    print("=" * 70)
    print(f"Test prompt: \"{TEST_PROMPT}\"")
    print(f"Simulated STT: {STT_LATENCY_MS}ms | TTS first audio: {TTS_LATENCY_MS}ms")
    print("-" * 70)
    print(f"{'Model':<22} {'TTFT':>10} {'Total Gen':>12} {'E2E (sim)':>12} {'Verdict':>12}")
    print("-" * 70)

    for r in results:
        # Verdict based on simulated E2E
        if r.simulated_e2e_ms < 2000:
            verdict = "EXCELLENT"
        elif r.simulated_e2e_ms < 2500:
            verdict = "GOOD"
        elif r.simulated_e2e_ms < 3000:
            verdict = "ACCEPTABLE"
        else:
            verdict = "TOO SLOW"

        print(f"{r.model:<22} {r.ttft_ms:>8.0f}ms {r.total_gen_ms:>10.0f}ms {r.simulated_e2e_ms:>10.0f}ms {verdict:>12}")

    print("-" * 70)

    # Recommendation
    print("\nRECOMMENDATION:")

    # Find fastest cloud and local
    local_results = [r for r in results if "local" in r.model.lower()]
    cloud_results = [r for r in results if "Claude" in r.model]

    if cloud_results:
        fastest_cloud = min(cloud_results, key=lambda r: r.simulated_e2e_ms)

        if fastest_cloud.simulated_e2e_ms < 2500:
            print(f"  -> Use Claude for voice! {fastest_cloud.model} achieves {fastest_cloud.simulated_e2e_ms:.0f}ms E2E")
            print(f"  -> RAM upgrade NOT needed - skip the $210 purchase")
        elif fastest_cloud.simulated_e2e_ms < 3000:
            print(f"  -> {fastest_cloud.model} is marginally acceptable at {fastest_cloud.simulated_e2e_ms:.0f}ms E2E")
            print(f"  -> Consider keeping local 3B for voice, Claude for complex reasoning")
        else:
            print(f"  -> Claude too slow for voice ({fastest_cloud.simulated_e2e_ms:.0f}ms E2E)")
            print(f"  -> Keep local LLM for voice interactions")
            if local_results:
                print(f"  -> Consider RAM upgrade for local 7B planning layer")

    print("=" * 70)


async def run_benchmark() -> None:
    """Run the full benchmark suite."""
    print("=" * 70)
    print("ATLAS Voice Latency Benchmark")
    print("=" * 70)
    print(f"Running {NUM_RUNS} iterations per model...")
    print()

    all_results: dict[str, list[BenchmarkResult]] = {}

    # Test local Qwen2.5-3B
    print("[1/4] Testing Qwen2.5-3B (local via Ollama)...")
    ollama_results = []
    for i in range(NUM_RUNS):
        print(f"  Run {i+1}/{NUM_RUNS}...", end=" ", flush=True)
        result = await benchmark_ollama()
        if result:
            ollama_results.append(result)
            print(f"TTFT: {result.ttft_ms:.0f}ms, Total: {result.total_gen_ms:.0f}ms")
        else:
            print("FAILED")
    if ollama_results:
        all_results["local"] = ollama_results

    print()

    # Test Direct Haiku API
    print("[2/4] Testing Haiku (Direct API)...")
    direct_haiku_results = []
    for i in range(NUM_RUNS):
        print(f"  Run {i+1}/{NUM_RUNS}...", end=" ", flush=True)
        result = await benchmark_direct_haiku()
        if result:
            direct_haiku_results.append(result)
            print(f"TTFT: {result.ttft_ms:.0f}ms, Total: {result.total_gen_ms:.0f}ms")
        else:
            print("FAILED")
        await asyncio.sleep(1)
    if direct_haiku_results:
        all_results["direct_haiku"] = direct_haiku_results

    print()

    # Test Claude Haiku (Agent SDK)
    print("[3/4] Testing Claude Haiku (via Agent SDK)...")
    haiku_results = []
    for i in range(NUM_RUNS):
        print(f"  Run {i+1}/{NUM_RUNS}...", end=" ", flush=True)
        result = await benchmark_claude("haiku")
        if result:
            haiku_results.append(result)
            print(f"TTFT: {result.ttft_ms:.0f}ms, Total: {result.total_gen_ms:.0f}ms")
        else:
            print("FAILED")
        # Small delay between Claude calls to avoid rate limiting
        await asyncio.sleep(1)
    if haiku_results:
        all_results["haiku"] = haiku_results

    print()

    # Test Claude Sonnet
    print("[4/4] Testing Claude Sonnet (via Agent SDK)...")
    sonnet_results = []
    for i in range(NUM_RUNS):
        print(f"  Run {i+1}/{NUM_RUNS}...", end=" ", flush=True)
        result = await benchmark_claude("sonnet")
        if result:
            sonnet_results.append(result)
            print(f"TTFT: {result.ttft_ms:.0f}ms, Total: {result.total_gen_ms:.0f}ms")
        else:
            print("FAILED")
        await asyncio.sleep(1)
    if sonnet_results:
        all_results["sonnet"] = sonnet_results

    # Calculate averages and display results
    avg_results = []
    for key, results in all_results.items():
        if results:
            avg = BenchmarkResult(
                model=results[0].model,
                ttft_ms=sum(r.ttft_ms for r in results) / len(results),
                total_gen_ms=sum(r.total_gen_ms for r in results) / len(results),
                token_count=sum(r.token_count for r in results) // len(results),
                response_text=results[0].response_text,  # Just use first response
            )
            avg_results.append(avg)

    if avg_results:
        print_results(avg_results)
    else:
        print("\n[ERROR] No benchmark results collected!")

    # Show sample responses
    print("\nSample Responses:")
    print("-" * 70)
    for key, results in all_results.items():
        if results:
            print(f"{results[0].model}:")
            print(f"  \"{results[0].response_text[:200]}...\"" if len(results[0].response_text) > 200 else f"  \"{results[0].response_text}\"")
            print()


def main():
    """Entry point."""
    asyncio.run(run_benchmark())


if __name__ == "__main__":
    main()
