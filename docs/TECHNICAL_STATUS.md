# ATLAS Technical Status

**Last Updated:** January 8, 2026
**Status:** Phase 0 COMPLETE (Memory) + Phase 1 COMPLETE (Voice) + Phase 2 COMPLETE (V2 Orchestrator)

---

## Quick Reference

### Core Architecture
```
User Voice → STT (Moonshine) → Router → LLM → TTS (Kokoro) → Speaker
                                  ↓
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
                 LOCAL         HAIKU       AGENT_SDK
              (Qwen 3B)    (Direct API)   (Claude Code)
               ~220ms        ~2800ms        ~7400ms
                FREE        ~$0.001/q        FREE
```

### Key Files

| File | Purpose | Status |
|------|---------|--------|
| `atlas/llm/local.py` | OllamaClient for Qwen 3B | ✅ Working |
| `atlas/llm/api.py` | Direct Anthropic API (Haiku) | ✅ Working |
| `atlas/llm/cloud.py` | Claude Agent SDK wrapper | ✅ Working |
| `atlas/llm/router.py` | Three-tier semantic router | ✅ Working |
| `atlas/llm/cost_tracker.py` | SQLite budget tracking | ✅ Working |
| `atlas/voice/pipeline.py` | Full voice pipeline | ✅ Working |
| `atlas/voice/stt.py` | Moonshine/Whisper STT | ✅ Working |
| `atlas/voice/tts.py` | Kokoro TTS | ✅ Working |
| `atlas/voice/vad.py` | Silero VAD | ✅ Working |
| `atlas/memory/store.py` | MemoryStore with hybrid RRF search | ✅ Working |
| `atlas/memory/embeddings.py` | BGE-small-en-v1.5 ONNX embeddings | ✅ Working |
| `atlas/memory/blueprint.py` | CRUD API for health/fitness tables | ✅ Working |
| `atlas/memory/schema.sql` | Complete database schema | ✅ Working |
| `config/routing.yaml` | Router configuration | ✅ Created |

---

## R29 Hybrid Routing System

### Three Tiers

| Tier | Model | Use Case | Latency | Cost |
|------|-------|----------|---------|------|
| **LOCAL** | Qwen2.5-3B (Ollama) | Commands, timers, simple queries | ~220ms | Free |
| **HAIKU** | Claude 3.5 Haiku (Direct API) | Advice, explanations, drafting | ~2800ms | ~$0.001/query |
| **AGENT_SDK** | Claude via Agent SDK | Complex planning, multi-step tasks | ~7400ms | Free (Max Plan) |

### Router Classification

The router uses three-stage classification:

1. **Regex patterns** (<1ms): Safety keywords, commands, complex task indicators
2. **Embedding similarity** (~20ms): MiniLM-L6-v2 against tier prototypes
3. **Default fallback**: HAIKU when uncertain

```python
from atlas.llm import get_router, Tier

router = get_router()
decision = router.classify("what time is it")
# decision.tier = Tier.LOCAL, confidence=0.95, category="command"

decision = router.classify("plan my workout for the week")
# decision.tier = Tier.AGENT_SDK, confidence=0.85, category="complex"
```

### Cost Tracking

SQLite database at `~/.atlas/cost_tracker.db`:
- Logs all API usage (tier, tokens, cost, latency)
- Budget limits: $10/month, $0.33/day
- Soft limit (80%): Enables "thrifty mode" - prefers LOCAL
- Hard limit (100%): API blocked, LOCAL only

```python
from atlas.llm import get_cost_tracker

tracker = get_cost_tracker()
status = tracker.get_budget_status()
# status.monthly_spend, status.can_use_api, status.thrifty_mode
```

---

## Memory System (Phase 0)

### Status: ✅ IMPLEMENTED (January 7, 2026)

**Database:** `~/.atlas/atlas.db` (SQLite + WAL mode)

### Components

| Component | Purpose | Performance |
|-----------|---------|-------------|
| `embeddings.py` | BGE-small-en-v1.5 via sentence-transformers ONNX | 10.1ms/embedding |
| `store.py` | Hybrid RRF search (60% vector, 40% FTS) | ~100ms at 100K |
| `blueprint.py` | CRUD for health/fitness tables | <1ms |
| `schema.sql` | All tables + FTS5 triggers | - |

### Usage

```python
from atlas.memory import get_memory_store, get_embedder, get_blueprint_api

# Memory operations
store = get_memory_store()
store.add_memory("User prefers morning workouts", importance=0.8)
results = store.search_hybrid("workout", embedding, limit=5)

# Blueprint operations
api = get_blueprint_api()
api.log_daily_metrics(DailyMetrics(date=date.today(), sleep_hours=7.5, mood=7))
```

### Tables

| Table | Purpose |
|-------|---------|
| `semantic_memory` | Core memory with embeddings |
| `vec_semantic` | Vector index (sqlite-vec) |
| `fts_memory` | Full-text search index (FTS5) |
| `daily_metrics` | Sleep, HRV, weight, mood |
| `supplements` | Supplement catalog |
| `supplement_log` | Dosing log |
| `workouts` | Workout sessions |
| `workout_exercises` | Exercise details |
| `lab_results` | Blood work |
| `injuries` | Injury tracking + contraindications |

### Test

```bash
python scripts/test_memory.py          # Basic tests
python scripts/test_memory.py --scale  # 100K scale test
```

---

## Voice Pipeline Features

### Current Implementation (`atlas/voice/pipeline.py`)

1. **Router Integration**
   - Uses `ATLASRouter` instead of direct OllamaClient
   - Config: `use_router=True` (default)

2. **Filler Phrases**
   - When routing to cloud, speaks: "Let me see.", "One moment.", etc.
   - Masks ~2800ms API latency
   - Config: `enable_filler_phrases=True` (default)

3. **Streaming-First TTS**
   - Speaks complete sentences as they arrive
   - Doesn't wait for full LLM response

4. **Command Interrupts**
   - Monitors for: "stop", "wait", "quiet", "shush", "enough", "okay"
   - Fuzzy matching for typos
   - Stops TTS immediately when detected

5. **Hot Window Mode**
   - After ATLAS speaks, stays listening for 6 seconds
   - No need to press Enter for follow-up questions
   - Config: `hot_window_duration_s=6.0` (default)

### Running the Voice Pipeline

```bash
cd /home/squiz/ATLAS
source venv/bin/activate

# With router (requires ANTHROPIC_API_KEY for cloud tiers)
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python -m atlas.voice.pipeline

# Local-only mode
python -c "
from atlas.voice.pipeline import VoicePipeline, VoicePipelineConfig
config = VoicePipelineConfig(use_router=False)
import asyncio
asyncio.run(VoicePipeline(config).start())
"

# Text mode (no audio)
python -m atlas.voice.pipeline --text-mode
```

---

## Windows Launcher

### File: `scripts/atlas_launcher.py`

Single-file CustomTkinter GUI for voice interaction (~735 lines).

**Features:**
- Start/Stop WSL server with progress feedback
- Hold SPACEBAR to record, release to send
- Voice toggle (Lewis/Emma)
- Session cost and routing display
- STT/TTS latency display
- GPU status indicator (CUDA/CPU)
- Transcript history with timestamps
- State indicator (Idle/Listening/Processing/Speaking)

**Running:**
```bash
# Windows PowerShell - with console (debugging)
python scripts/atlas_launcher.py

# Windows - silent (no console)
pythonw scripts/atlas_launcher.py
```

**Desktop Shortcuts:**
- `ATLAS_Launcher.bat` - Console mode
- `ATLAS_Launcher.vbs` - Silent mode

---

## Key Files Modified

| File | Changes |
|------|---------|
| `atlas/voice/stt.py` | Removed initial_prompt bias, disabled vad_filter, added 100ms silence head |
| `atlas/voice/tts.py` | GPU provider selection with CPU fallback |
| `atlas/voice/bridge_file_server.py` | base.en model, voice selection, session_status.json, 200ms silence tail |
| `atlas/llm/router.py` | Flexible timer patterns for LOCAL routing |
| `scripts/atlas_launcher.py` | New Windows launcher with spacebar-to-talk |

---

## Measured Latency (from Australia)

| Component | Latency |
|-----------|---------|
| STT (Moonshine) | ~600ms |
| Router classification | ~50ms |
| Qwen 3B local | ~220ms TTFT |
| Haiku Direct API | ~2800ms TTFT |
| Agent SDK | ~7400ms TTFT |
| TTS (Kokoro) | ~250ms |

**End-to-end with LOCAL:** ~1100ms
**End-to-end with HAIKU:** ~3700ms (filler phrase masks wait)

---

## Dependencies

### Installed
```
anthropic==0.75.0      # Direct API client
tenacity==9.1.2        # Retry logic
pybreaker==1.4.1       # Circuit breaker
httpx==0.28.1          # HTTP client
sentence-transformers  # Embedding router
torch, numpy, scipy    # ML dependencies
```

### Voice Components
```
kokoro-onnx            # TTS
moonshine / faster-whisper  # STT
silero-vad             # Voice activity detection
sounddevice            # Audio I/O
```

---

## Configuration Files

### `config/routing.yaml`
- Router thresholds (local: 0.65, haiku: 0.82, agent: 0.88)
- Budget limits ($10/month)
- Latency targets
- Persona failure messages
- Filler phrases

### `config/Modelfile.atlas`
- Ollama model config for Qwen 3B
- System prompt (Lethal Gentleman persona)

### `.env`
- ANTHROPIC_API_KEY (required for cloud tiers)

---

## Persona: The Lethal Gentleman

System prompt in `atlas/voice/pipeline.py`:
- Speaks economically, leads with shorter sentences
- No hedging qualifiers ("just", "maybe", "perhaps")
- Understated confidence, practical concern
- Brief responses: 1-3 sentences for simple queries

Failure messages:
- API error: "I cannot access that resource at the moment."
- Budget exceeded: "The external archives are temporarily unavailable."
- Uncertainty: Ask clarifying question, then escalate silently

---

## Orchestrator Infrastructure (January 2026)

### Status: ✅ IMPLEMENTED

ATLAS evolved from voice assistant to **agentic orchestrator** across Baby Brains ecosystem.

### Components

| File | Purpose | Status |
|------|---------|--------|
| `atlas/orchestrator/command_router.py` | Routes `/babybrains`, `/knowledge`, `/web`, `/app` | ✅ Working |
| `atlas/orchestrator/hooks.py` | Wraps validators for deterministic verification | ✅ Working |
| `atlas/orchestrator/skill_executor.py` | Dual-mode skill execution | ✅ Working |

### Cost Model (Critical Decision)

| Mode | Cost | Command |
|------|------|---------|
| CLI (default) | $0 (Max subscription) | `python -m atlas.orchestrator.skill_executor --skill draft_21s` |
| API | Per-token | `python -m atlas.orchestrator.skill_executor --skill draft_21s --api` |

**Key Insight:** Agent SDK = API costs. CLI mode uses Max subscription ($0).

### Testing

```bash
# Test command router
python -m atlas.orchestrator.command_router babybrains status
python -m atlas.orchestrator.command_router knowledge status

# Test skill executor (CLI mode - uses Max)
python -m atlas.orchestrator.skill_executor --skill draft_21s --repo babybrains-os
```

### V2 Components Status

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| SubAgentExecutor | `subagent_executor.py` | ✅ Complete | Fixed 7 CRITICAL + 6 HIGH issues (Jan 8, 2026) |
| HookTiming | `hooks.py` | ✅ Complete | PRE/POST enum, hook_name field, get_hooks_by_timing(), run_all_for_timing(timeout), CLI --timing/--list/--input, logging + specific exceptions (Jan 8) |
| SessionManager | `session_manager.py` | ✅ Complete | Git diff pattern, state persistence |
| Progressive Loading | `skill_executor.py` | ✅ Complete | SkillSection dataclass, 8 new methods, 5 CLI flags, partial matching (Jan 8) |
| ScratchPad | `scratch_pad.py` | ✅ Complete | ScratchEntry dataclass, file persistence, step tracking, CLI (Jan 8) |

### V2 Gaps (From Masterclass Analysis)

| Gap | Priority | Status |
|-----|----------|--------|
| Sub-agent support | High | ✅ DONE |
| Multi-point hooks | High | ✅ DONE (PRE/POST, MID deferred) |
| Context management | High | ✅ DONE |
| Adversarial checking | Medium | ✅ DONE (in SubAgentExecutor) |
| Progressive loading | Medium | ✅ DONE (Jan 8, 2026) |
| Scratch pad | Low | ✅ DONE (Jan 8, 2026) |

See `docs/ATLAS_ARCHITECTURE_V2.md` for full implementation plan.

---

## What's NOT Implemented Yet

| Feature | Priority | Notes |
|---------|----------|-------|
| Tool use (timers, etc.) | P2 | Commands acknowledged but not executed |
| MCP server | P2 | Expose memory/Blueprint tools to Claude Desktop |
| Voice ↔ Memory integration | P2 | Inject memories into voice pipeline context |
| Wake word ("Hey ATLAS") | P3 | Currently push-to-talk |

---

## Known Limitations

| Limitation | Notes |
|------------|-------|
| No tool use | Timer/alarm requests acknowledged but not executed |
| Memory ✅ | IMPLEMENTED - `atlas.memory` module with hybrid search |
| Content filtering | May block certain health topics via API |
| Router confidence | Sometimes stuck at 0.50 - embeddings may not be loading |

---

## Open Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Router always 0.50 | Medium | Embeddings may not be loading. Verify sentence-transformers. |
| Cost shows $0.0000 | Low | HAIKU calls should have cost. Tracking may be misconfigured. |
| Persona breaks | Medium | "I am Claude" slips through. May need context injection. |
| No repo awareness | Medium | ATLAS doesn't know its codebase location. |

**Status:** Minor issues. Voice works end-to-end. Note for Phase 2+.

---

## Testing Commands

```bash
# Test router classification
python -c "
from atlas.llm import get_router
router = get_router()
for q in ['what time is it', 'plan my workout', 'medical advice']:
    r = router.classify(q)
    print(f'{q} -> {r.tier.value} ({r.confidence:.2f})')
"

# Test cost tracker
python -c "
from atlas.llm import get_cost_tracker
t = get_cost_tracker()
s = t.get_budget_status()
print(f'Monthly: \${s.monthly_spend:.4f} / \${s.monthly_limit}')
"

# Test memory system
python scripts/test_memory.py

# Test memory at scale (100K records)
python scripts/test_memory.py --scale

# Test embeddings
python -c "
from atlas.memory import get_embedder
embedder = get_embedder()
result = embedder.embed('morning workout')
print(f'Latency: {result.duration_ms:.1f}ms, Dims: {len(result.embedding)}')
"

# Run latency benchmark
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python scripts/voice_latency_benchmark.py
```

---

## Research Documents

| Document | Content |
|----------|---------|
| `docs/research/R29.*` | LLM routing strategies |
| `docs/research/R21.*` | Lethal Gentleman persona |
| `docs/research/R11.*` | Voice latency optimization |
| `docs/TASK_JARVIS_FEATURE_ADOPTION.md` | Feature comparison with JARVIS |

---

## Quick Start for New Agent

1. **Understand architecture decisions:** Read `docs/DECISIONS.md`
2. **Understand the routing:** Read `atlas/llm/router.py`
3. **Understand the voice pipeline:** Read `atlas/voice/pipeline.py`
4. **Run tests:** Use commands in "Testing Commands" section
5. **Check budget:** `get_cost_tracker().get_budget_status()`
6. **Config options:** See `VoicePipelineConfig` in pipeline.py
7. **Windows launcher:** Run from Windows with `python scripts/atlas_launcher.py`
