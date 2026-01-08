# R29 Hybrid Routing - Implementation Status

**Date:** January 6, 2026
**Status:** COMPLETE - Routing layer + Voice pipeline integration done

---

## 1. What's Built

| Component | File | Status |
|-----------|------|--------|
| Direct Anthropic Client | `atlas/llm/api.py` | ✅ Working (with connection keep-alive) |
| Cost Tracker | `atlas/llm/cost_tracker.py` | ✅ Working |
| Semantic Router | `atlas/llm/router.py` | ✅ Working |
| Configuration | `config/routing.yaml` | ✅ Created |
| Updated Exports | `atlas/llm/__init__.py` | ✅ Updated |
| Benchmark Script | `scripts/voice_latency_benchmark.py` | ✅ Updated |
| **Voice Pipeline** | `atlas/voice/pipeline.py` | ✅ **Integrated with router** |
| Filler Phrases | `atlas/voice/pipeline.py` | ✅ Working |
| Command Interrupts | `atlas/voice/pipeline.py` | ✅ Working ("stop", "wait", etc.) |
| Hot Window Mode | `atlas/voice/pipeline.py` | ✅ Working (6s follow-up) |

---

## 2. Real-World Latency (Australia → US)

**CRITICAL UPDATE:** Research assumed ~500ms for Direct API. Reality from Australia is ~2800ms.

| Tier | TTFT (Warm) | E2E with Voice* | Verdict |
|------|-------------|-----------------|---------|
| **LOCAL** (Qwen 3B) | ~220ms | ~1,470ms | EXCELLENT |
| **HAIKU** (Direct API) | ~2,800ms | ~4,050ms | ACCEPTABLE with masking |
| **AGENT SDK** | ~7,400ms | ~8,650ms | Complex tasks only |

*E2E = STT (600ms) + TTFT + TTS first audio (250ms)

### Latency Comparison

```
Original Research Assumption:
├── Local:  ~200ms  ← Accurate ✓
├── Haiku:  ~500ms  ← WRONG (Australia penalty)
└── SDK:    ~6000ms ← Close

Actual Measured (Australia):
├── Local:  ~220ms  ← Excellent
├── Haiku:  ~2800ms ← 5.6x slower than expected
└── SDK:    ~7400ms ← Slightly worse
```

### Why the Discrepancy?

1. **Geographic latency:** Australia → US adds ~150-200ms round-trip
2. **Connection establishment:** TLS handshake, API auth
3. **Model loading:** First request may hit cold model
4. **Queueing:** Anthropic's infrastructure queueing

The ~1150ms seen in some tests was likely a warmed/cached connection. Real-world cold-start is ~2800ms.

---

## 3. Revised Strategy

### Voice Pipeline Latency Budget (Updated)

| Scenario | Breakdown | Total | User Experience |
|----------|-----------|-------|-----------------|
| **LOCAL path** | 600ms STT + 220ms TTFT + 250ms TTS | **~1,070ms** | Instant feel |
| **HAIKU path** | 600ms STT + 2800ms TTFT + 250ms TTS | **~3,650ms** | Needs masking |
| **SDK path** | 600ms STT + 7400ms TTFT + 250ms TTS | **~8,250ms** | "Working on it" |

### The Filler Phrase Strategy (Critical)

```python
async def voice_response(query: str):
    decision = router.classify(query)

    if decision.tier == Tier.LOCAL:
        # No filler needed - fast enough
        async for token in router.route_and_stream(query):
            await tts.stream_token(token)

    elif decision.tier == Tier.HAIKU:
        # IMMEDIATELY speak filler (buys ~1.5s perceived time)
        await tts.speak_immediate("Let me see...")  # ~400ms to speak
        # User hears something at ~1000ms instead of silence until ~3650ms
        async for token in router.route_and_stream(query):
            await tts.stream_token(token)

    else:  # AGENT_SDK
        # Longer acknowledgment for complex tasks
        await tts.speak_immediate("I shall attend to this. One moment.")
        async for token in router.route_and_stream(query):
            await tts.stream_token(token)
```

### Filler Phrases (Persona-Appropriate)

**For HAIKU tier (~2800ms TTFT):**
- "Let me see..."
- "One moment..."
- "Consider this..."
- "Let me think..."

**For AGENT_SDK tier (~7400ms TTFT):**
- "I shall attend to this. Please allow me a moment."
- "This requires some thought. Bear with me."
- "Let me work through this properly."

---

## 4. Router Classification (Verified Working)

```
Input                        → Tier      (Reason)
─────────────────────────────────────────────────
"set timer for 5 minutes"    → LOCAL     (command pattern)
"stop"                       → LOCAL     (brief query)
"what's a good warm-up"      → HAIKU     (embedding match)
"plan my workout"            → AGENT_SDK (complex pattern)
"medical advice"             → AGENT_SDK (safety pattern)
```

---

## 5. Cost Tracking (Active)

```yaml
Budget Configuration:
  monthly_limit: $10.00
  daily_limit: $0.33
  soft_limit: 80% → Thrifty mode (prefer LOCAL)
  hard_limit: 100% → API blocked (LOCAL only)

Per-Query Costs:
  LOCAL: $0
  HAIKU: ~$0.001 (varies with tokens)
  AGENT_SDK: $0 (Max Plan)
```

---

## 6. Next Steps (Priority Order)

### Priority 1: Voice Pipeline Integration
```python
# In atlas/voice/pipeline.py
# Replace direct LLM call:
# OLD: async for token in ollama.stream(query):
# NEW: async for token in router.route_and_stream(query):
```

### Priority 2: Filler Phrase Implementation
- Add immediate TTS for non-LOCAL tiers
- Test perceived latency improvement
- Tune phrase duration vs API latency

### Priority 3: Connection Keep-Alive
```python
# Potential optimization in api.py
# Keep HTTP/2 connection warm to reduce repeat latency
# Could reduce ~2800ms to ~1500-2000ms for subsequent requests
```

### Priority 4: End-to-End Testing
- Full voice flow: Mic → VAD → STT → Router → LLM → TTS → Speaker
- Measure real perceived latency
- Test tier transitions

### Priority 5: Usage Data Collection
- Log actual query distributions
- Validate embedding prototype accuracy
- Tune thresholds based on real usage

---

## 7. Architecture Diagram (As Built)

```
┌─────────────────────────────────────────────────────────────────┐
│                    R29 Routing Layer (COMPLETE)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query → [Classifier] → [Router] → [Budget Check] → LLM Tier   │
│              │              │            │              │        │
│         ┌────┴────┐    ┌────┴────┐  ┌────┴────┐   ┌────┴────┐  │
│         │ Stage 1 │    │ Stage 2 │  │ SQLite  │   │  Tier   │  │
│         │ Regex   │    │ Embed   │  │ Tracker │   │ Select  │  │
│         │ <1ms    │    │ ~20ms   │  │         │   │         │  │
│         └─────────┘    └─────────┘  └─────────┘   └─────────┘  │
│                                                        │        │
│                                           ┌────────────┼────────┤
│                                           │            │        │
│                                           ▼            ▼        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │ Tier 1: LOCAL    │  │ Tier 2: HAIKU    │  │ Tier 3: SDK    ││
│  │ Qwen 3B          │  │ Direct API       │  │ Agent SDK      ││
│  │ ~220ms TTFT      │  │ ~2800ms TTFT     │  │ ~7400ms TTFT   ││
│  │ Free             │  │ ~$0.001/query    │  │ Free           ││
│  │ 40-50% queries   │  │ 35-40% queries   │  │ 10-15% queries ││
│  └──────────────────┘  └──────────────────┘  └────────────────┘│
│                                                                  │
│  Cost Tracker: ~/.atlas/cost_tracker.db                         │
│  Config: /home/squiz/ATLAS/config/routing.yaml                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

                              │
                              │ NEXT: Integrate
                              ▼

┌─────────────────────────────────────────────────────────────────┐
│                    Voice Pipeline (TO INTEGRATE)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Mic → VAD → STT → [ROUTER] → TTS → Speaker                     │
│                        │                                         │
│                   Filler phrase                                  │
│                   if non-LOCAL                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Key Learnings

### What Research Got Right
- Three-tier architecture is correct
- Local should handle 40-50% of queries
- Cost tracking is essential
- Filler phrases are critical for UX

### What Research Got Wrong
- Direct API latency from Australia: Expected ~500ms, actual ~2800ms
- This makes filler phrases MORE important, not optional

### Implications
1. **LOCAL tier is even more valuable** - 220ms vs 2800ms is 12x difference
2. **Filler phrases are mandatory** - Not a "nice to have"
3. **Connection keep-alive worth investigating** - Could save ~500-1000ms
4. **SDK tier is acceptable** - 7.4s with proper acknowledgment works for complex tasks

---

## 9. Test Commands

```bash
# Activate environment
cd /home/squiz/ATLAS && source venv/bin/activate

# Test router classification
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python -c "
from atlas.llm import get_router
router = get_router()
print('Timer:', router.classify('set timer for 5 minutes'))
print('Advice:', router.classify('what\\'s a good warm-up'))
print('Plan:', router.classify('plan my workout for the week'))
"

# Run full benchmark
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python scripts/voice_latency_benchmark.py

# Check cost tracker
python -c "
from atlas.llm import get_cost_tracker
tracker = get_cost_tracker()
print(tracker.get_budget_status())
print(tracker.get_daily_summary(days=7))
"
```

---

## 10. Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `atlas/llm/api.py` | Direct Anthropic client | ~150 |
| `atlas/llm/cost_tracker.py` | SQLite cost tracking | ~120 |
| `atlas/llm/router.py` | Semantic routing | ~250 |
| `atlas/llm/local.py` | Ollama client | ~250 |
| `atlas/llm/cloud.py` | Agent SDK client | ~170 |
| `config/routing.yaml` | Configuration | ~50 |

---

**Status:** Routing layer complete. Voice pipeline integration is the next milestone.
