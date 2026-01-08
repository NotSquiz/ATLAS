# ATLAS Voice Pipeline Streaming Debug Handoff

> **STATUS: RESOLVED** - Issue solved by switching from Qwen3-4B to Qwen2.5-3B-Instruct.
> Qwen2.5-3B has NO thinking mode architecture. Content streams immediately.
> See `/home/squiz/ATLAS/docs/research/R28.Best local LLM for voice-first AI assistant on 4GB VRAM.md` for details.
> This document is preserved as historical reference for why Qwen3-4B failed.

---

## Original Issue (RESOLVED)
The Ollama streaming API returned **0 content tokens** when a custom system prompt was provided with Qwen3-4B.

## What We've Determined

### 1. The Root Cause: Qwen3-4B Thinking Mode
- Qwen3-4B has a "thinking" feature that outputs reasoning in a separate `thinking` field
- When a custom system prompt is used, the model spends ALL tokens on thinking
- With 512 tokens and a system prompt: 511 thinking tokens, 0 content tokens
- Without system prompt: ~45 chars of content generated correctly

### 2. `/no_think` Is NOT Working
The R25 research says to use `/no_think` for fast queries, but testing shows:
- When we send `/no_think Hello` as user content, the model interprets it as text
- It thinks: "the user sent /no_think Hello. First, I need to understand what they mean..."
- The `/no_think` feature may need to be enabled in the Modelfile or works differently than documented

### 3. Memory Pressure
- GPU: 3203 MiB / 4096 MiB (78% used)
- Earlier CUDA OOM error: "an illegal memory access was encountered"
- This is expected - Qwen3-4B uses ~3.1GB, but the solution is to run STT on CPU (already implemented)

## Code Changes Made

### 1. Updated `/home/squiz/ATLAS/atlas/llm/local.py`
- Changed `stream()` to use `/api/chat` instead of `/api/generate` (for thinking/content separation)
- Added `use_thinking` parameter (default False for voice)
- Attempted to prepend `/no_think` to user content (not working)
- Changed to use fresh `httpx.AsyncClient` per request

### 2. Updated `/home/squiz/ATLAS/atlas/voice/pipeline.py`
- System prompt updated to "Lethal Gentleman" persona (R21)
- `llm_max_tokens` increased to 512 (was 150)

## Files to Review

| File | Purpose |
|------|---------|
| `/home/squiz/ATLAS/docs/research/R25.Definitive LLM selection for ATLAS - Qwen3-4B wins decisively.md` | Qwen3 configuration, `/no_think` guidance |
| `/home/squiz/ATLAS/docs/research/R21.The Lethal Gentleman - A complete AI persona specification.md` | ATLAS persona spec |
| `/home/squiz/ATLAS/atlas/llm/local.py` | Ollama client with streaming |
| `/home/squiz/ATLAS/atlas/voice/pipeline.py` | Voice pipeline config |

## What Works vs What Doesn't

### Works:
- `curl` non-streaming with system prompt → Returns content correctly
- `curl` streaming without system prompt → Returns content tokens
- Python httpx non-streaming → Returns content correctly
- Python streaming WITHOUT system prompt → Returns ~45-58 chars

### Doesn't Work:
- Python streaming WITH system prompt → 0 content, all thinking tokens
- `/no_think` prefix → Model treats it as text, not a command

## Next Steps to Debug

1. **Check Modelfile**: Run `ollama show atlas-local --modelfile` to see current config
   - Look for how `/no_think` is supposed to work
   - Check if there's a template that handles the thinking mode

2. **Test Qwen3 thinking mode properly**:
   - The Qwen3 docs may have specific syntax for disabling thinking
   - Try: `<|/no_think|>` or `<think>off</think>` or similar tokens

3. **Alternative: Use the built-in system prompt**:
   - The Modelfile has its own system prompt
   - Maybe don't override it, just append to user message

4. **Alternative: Increase tokens significantly**:
   - With 1024+ tokens, thinking completes and content follows
   - But this adds latency (~8+ seconds)

## Test Commands

```bash
# Test curl streaming
curl -s http://localhost:11434/api/chat -d '{
  "model": "atlas-local",
  "messages": [
    {"role": "system", "content": "You are ATLAS. Keep it brief."},
    {"role": "user", "content": "Hello"}
  ],
  "stream": true,
  "options": {"num_predict": 512}
}' | grep -v '"content":""' | head -5

# Test Python streaming
source venv/bin/activate && python -c "
import asyncio
from atlas.llm.local import OllamaClient

async def test():
    client = OllamaClient(model='atlas-local')
    response = ''
    async for token in client.stream('Hello', system='Keep it brief.', max_tokens=512):
        response += token
        print(token, end='', flush=True)
    print(f'\nResult: {len(response)} chars')

asyncio.run(test())
"

# Check GPU memory
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

## Todo Status
- ✅ Install dependencies (moonshine, silero-vad, etc.)
- ✅ Create voice module structure
- ✅ Implement STT, TTS, VAD wrappers
- ✅ Implement voice pipeline
- ✅ Add MCP tools
- ✅ Create exercise database
- ✅ Update persona to Lethal Gentleman
- ⏳ Fix streaming issue with system prompt
- ⏳ Test end-to-end voice interaction

## Key Insight
The fundamental issue is that Qwen3-4B's thinking mode is not properly controlled when using custom system prompts via the chat API. The `/no_think` feature documented in R25 either:
1. Doesn't work with custom system prompts
2. Requires special syntax not yet identified
3. Must be configured in the Modelfile, not the API call

The fresh agent should start by examining how Qwen3's thinking mode is supposed to be controlled, potentially by:
- Checking official Qwen3 documentation
- Reviewing the Ollama Modelfile syntax
- Looking at the Qwen3 chat template
