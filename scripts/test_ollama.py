#!/usr/bin/env python3
"""
ATLAS Ollama Benchmark Script

Tests local LLM performance against Phase 0 targets:
- First token: ~150-200ms
- Generation: ~35-40 tok/s
- Total response: <3 seconds
"""

import subprocess
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from atlas.llm.local import OllamaClient
    ATLAS_AVAILABLE = True
except ImportError:
    ATLAS_AVAILABLE = False


def check_ollama_installed() -> bool:
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_ollama_running() -> bool:
    """Check if Ollama server is running."""
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    """List available Ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            return [line.split()[0] for line in lines if line]
        return []
    except Exception:
        return []


def benchmark_model(model: str = "atlas-local", num_runs: int = 3) -> dict:
    """
    Benchmark a model's performance.

    Returns dict with timing metrics.
    """
    if not ATLAS_AVAILABLE:
        print("Warning: atlas module not available, using raw ollama")
        return benchmark_raw(model, num_runs)

    client = OllamaClient(model=model)

    if not client.is_available():
        return {"error": "Ollama server not running"}

    prompts = [
        "What is 2+2? Reply with just the number.",
        "Name three colors. Be brief.",
        "What day comes after Monday? One word answer.",
    ]

    results = []
    print(f"\nBenchmarking {model}...")
    print("-" * 50)

    for i in range(num_runs):
        prompt = prompts[i % len(prompts)]
        print(f"\nRun {i+1}/{num_runs}: {prompt[:40]}...")

        start = time.perf_counter()
        response = client.generate(prompt, use_thinking=False)
        total_time = (time.perf_counter() - start) * 1000

        print(f"  Response: {response.content[:50]}...")
        print(f"  Total time: {total_time:.0f}ms")
        print(f"  First token: ~{response.first_token_ms:.0f}ms")
        print(f"  Tokens/sec: {response.tokens_per_second:.1f}")

        results.append({
            "total_ms": total_time,
            "first_token_ms": response.first_token_ms,
            "tokens_per_second": response.tokens_per_second,
            "eval_count": response.eval_count,
        })

    # Calculate averages
    avg_total = sum(r["total_ms"] for r in results) / len(results)
    avg_first_token = sum(r["first_token_ms"] for r in results) / len(results)
    avg_tps = sum(r["tokens_per_second"] for r in results) / len(results)

    return {
        "model": model,
        "runs": num_runs,
        "avg_total_ms": avg_total,
        "avg_first_token_ms": avg_first_token,
        "avg_tokens_per_second": avg_tps,
        "results": results,
    }


def benchmark_raw(model: str, num_runs: int) -> dict:
    """Benchmark using raw ollama command."""
    results = []
    prompt = "What is 2+2? Reply with just the number."

    for i in range(num_runs):
        print(f"\nRun {i+1}/{num_runs}...")
        start = time.perf_counter()

        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
        )

        total_time = (time.perf_counter() - start) * 1000
        print(f"  Response: {result.stdout.strip()[:50]}")
        print(f"  Total time: {total_time:.0f}ms")

        results.append({"total_ms": total_time})

    avg_total = sum(r["total_ms"] for r in results) / len(results)
    return {
        "model": model,
        "runs": num_runs,
        "avg_total_ms": avg_total,
        "results": results,
    }


def check_vram() -> dict:
    """Check VRAM usage with nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            used, total = result.stdout.strip().split(",")
            return {
                "used_mb": int(used.strip()),
                "total_mb": int(total.strip()),
                "used_gb": int(used.strip()) / 1024,
            }
    except Exception as e:
        return {"error": str(e)}
    return {"error": "nvidia-smi not available"}


def main():
    print("=" * 60)
    print("ATLAS Ollama Benchmark")
    print("=" * 60)

    # Check prerequisites
    print("\n[1/4] Checking Ollama installation...")
    if not check_ollama_installed():
        print("  ERROR: Ollama not installed!")
        print("  Run: curl -fsSL https://ollama.com/install.sh | sh")
        return 1
    print("  Ollama installed")

    print("\n[2/4] Checking Ollama server...")
    if not check_ollama_running():
        print("  WARNING: Ollama server not running")
        print("  Starting server...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

        if not check_ollama_running():
            print("  ERROR: Could not start Ollama server")
            return 1
    print("  Ollama server running")

    print("\n[3/4] Checking available models...")
    models = list_models()
    if not models:
        print("  No models found!")
        print("  Run: ollama pull qwen3:4b")
        return 1

    print(f"  Found {len(models)} model(s): {', '.join(models)}")

    # Determine which model to benchmark
    model = "atlas-local" if "atlas-local" in models else models[0]
    print(f"  Using: {model}")

    print("\n[4/4] Checking VRAM...")
    vram = check_vram()
    if "error" not in vram:
        print(f"  VRAM: {vram['used_gb']:.1f}GB / {vram['total_mb']/1024:.1f}GB")
    else:
        print(f"  {vram.get('error', 'Unknown error')}")

    # Run benchmark
    print("\n" + "=" * 60)
    print("RUNNING BENCHMARK")
    print("=" * 60)

    benchmark = benchmark_model(model, num_runs=3)

    # Check VRAM during inference
    print("\n[Post-inference VRAM check]")
    vram_after = check_vram()
    if "error" not in vram_after:
        print(f"  VRAM: {vram_after['used_gb']:.1f}GB / {vram_after['total_mb']/1024:.1f}GB")

    # Results summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    if "error" in benchmark:
        print(f"  ERROR: {benchmark['error']}")
        return 1

    print(f"\n  Model: {benchmark['model']}")
    print(f"  Runs: {benchmark['runs']}")
    print(f"\n  Average Total Time: {benchmark['avg_total_ms']:.0f}ms")

    if "avg_first_token_ms" in benchmark:
        print(f"  Average First Token: {benchmark['avg_first_token_ms']:.0f}ms")
        print(f"  Average Tokens/sec: {benchmark['avg_tokens_per_second']:.1f}")

    # Check against targets
    print("\n  TARGET COMPARISON:")
    total_ok = benchmark['avg_total_ms'] < 3000
    print(f"    Total < 3s: {'PASS' if total_ok else 'FAIL'} ({benchmark['avg_total_ms']:.0f}ms)")

    if "avg_first_token_ms" in benchmark:
        first_ok = benchmark['avg_first_token_ms'] < 300
        tps_ok = benchmark['avg_tokens_per_second'] > 30
        print(f"    First token < 300ms: {'PASS' if first_ok else 'FAIL'} ({benchmark['avg_first_token_ms']:.0f}ms)")
        print(f"    Tokens/sec > 30: {'PASS' if tps_ok else 'FAIL'} ({benchmark['avg_tokens_per_second']:.1f})")

    if "error" not in vram_after:
        vram_ok = vram_after['used_gb'] < 3.5
        print(f"    VRAM < 3.5GB: {'PASS' if vram_ok else 'FAIL'} ({vram_after['used_gb']:.1f}GB)")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
