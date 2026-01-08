# ATLAS Voice Latency Test Handoff

## Context

The user has an **Anthropic Max Plan** with unlimited access to Claude Haiku/Sonnet/Opus. We need to determine whether local LLM inference is necessary for voice, or if Claude API streaming is fast enough.

## The Decision Point

**If Claude API latency is acceptable (~2-3s):**
- Skip local LLM entirely
- Use Claude for ALL reasoning (dramatically smarter)
- No need for RAM upgrade ($210 Kingston 2x16GB)
- Architecture: Local STT → Claude API → Local TTS

**If Claude API latency is too slow:**
- Keep local 3B for voice (fast)
- Use Claude for complex reasoning
- Consider RAM upgrade for local 7B planning layer

## Task: Voice Latency Benchmark

Create and run a benchmark that tests the full voice pipeline:
```
Simulated Voice → STT (Moonshine, local) → LLM → TTS (Kokoro, local) → Audio
```

Test with:
1. **Local Qwen2.5-3B** (via Ollama) - baseline
2. **Claude Haiku** - fastest cloud
3. **Claude Sonnet** - balanced
4. **Claude Opus** - smartest (optional, likely too slow for voice)

### Metrics to Capture

| Metric | Description |
|--------|-------------|
| STT time | Moonshine transcription (should be ~600ms) |
| LLM first token | Time to first token from LLM |
| LLM total | Full response generation |
| TTS first audio | Time to first audio output |
| **Total E2E** | Speech end → First audio out |

### Target Latencies

| Model | Acceptable for Voice? |
|-------|----------------------|
| < 2.0s | Excellent |
| 2.0-2.5s | Good |
| 2.5-3.0s | Acceptable |
| > 3.0s | Too slow |

## Current State

### Voice Components (All Working)
- **STT**: Moonshine Base on CPU - `/home/squiz/ATLAS/atlas/voice/stt.py`
- **TTS**: Kokoro-82M on GPU - `/home/squiz/ATLAS/atlas/voice/tts.py`
- **VAD**: Silero v6.2 - `/home/squiz/ATLAS/atlas/voice/vad.py`
- **Pipeline**: Push-to-talk loop - `/home/squiz/ATLAS/atlas/voice/pipeline.py`

### Local LLM (Working)
- **Model**: Qwen2.5-3B-Instruct via Ollama
- **Client**: `/home/squiz/ATLAS/atlas/llm/local.py`
- **Note**: Switched from Qwen3-4B due to mandatory thinking mode issues (see R28)

### Cloud LLM (Needs Setup)
- **No cloud client exists yet** - needs to be created at `/home/squiz/ATLAS/atlas/llm/cloud.py`
- Check if `anthropic` package is installed: `pip show anthropic`
- Check for API key: `env | grep ANTHROPIC`
- User has Max Plan, so API key should be available

## Implementation Steps

1. **Install anthropic SDK** (if not present):
   ```bash
   pip install anthropic
   ```

2. **Create cloud client** at `/home/squiz/ATLAS/atlas/llm/cloud.py`:
   ```python
   import anthropic
   import time
   from typing import AsyncIterator

   class ClaudeClient:
       def __init__(self, model: str = "claude-3-5-haiku-latest"):
           self.client = anthropic.Anthropic()
           self.model = model

       async def stream(self, prompt: str, system: str = None, max_tokens: int = 256) -> AsyncIterator[str]:
           # Streaming implementation
           ...
   ```

3. **Create benchmark script** at `/home/squiz/ATLAS/scripts/voice_latency_benchmark.py`:
   - Test same prompt across all models
   - Measure each stage
   - Output comparison table

4. **Run benchmarks** and report results

## Files to Reference

| File | Purpose |
|------|---------|
| `/home/squiz/ATLAS/docs/MASTER_PLAN.md` | Full architecture |
| `/home/squiz/ATLAS/atlas/llm/local.py` | Ollama client (reference for cloud client) |
| `/home/squiz/ATLAS/atlas/voice/pipeline.py` | Voice pipeline with metrics |
| `/home/squiz/ATLAS/docs/research/R28.Best local LLM for voice-first AI assistant on 4GB VRAM.md` | Why we switched from Qwen3 to Qwen2.5 |

## System Context

- **Hardware**: ThinkPad X1 Extreme Gen 4, i7-11800H, 16GB RAM, RTX 3050 Ti (4GB VRAM)
- **OS**: Windows 11 + WSL2
- **WSL2 Memory**: 6GB allocated (could increase to 12-14GB with RAM upgrade)
- **User Location**: Australia (affects API latency to Anthropic servers)

## Test Prompt (Use Same for All Models)

```
User: "What's a good warm-up before bench press?"
System: "You are ATLAS—a mentor who speaks economically. Keep responses to 1-3 sentences. Be direct."
```

Short response expected, representative of typical voice query.

## Expected Outcomes

### Scenario A: Claude is fast enough
- Haiku < 2.5s end-to-end
- **Recommendation**: Skip local LLM, go full Claude
- **RAM upgrade**: Not needed

### Scenario B: Claude is too slow
- Haiku > 3s end-to-end
- **Recommendation**: Keep local 3B for voice, Claude for complex tasks
- **RAM upgrade**: Consider for local 7B planning layer

## User's Current Thinking

The user is weighing:
1. $210 for Kingston 2x16GB RAM upgrade (32GB total)
2. This would enable running 7B model on CPU for local reasoning
3. But with unlimited Claude access, local reasoning may be unnecessary
4. Need latency data to make informed decision
