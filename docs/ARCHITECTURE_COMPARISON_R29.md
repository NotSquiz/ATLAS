# ATLAS Architecture Evolution: MASTER_PLAN vs R29 Hybrid Routing

**Date:** January 6, 2026
**Purpose:** Deep analysis of architectural changes between original design and R29 hybrid approach

---

## Executive Summary

The R29 hybrid architecture represents a **fundamental paradigm shift** in how ATLAS handles queries:

| Aspect | MASTER_PLAN (R1-R28) | R29 Hybrid |
|--------|---------------------|------------|
| **Philosophy** | Local-first, cloud as fallback | Right-tier for each query |
| **Routing Logic** | Binary (2 conditions, 3 lines) | Cascade (3 stages, semantic) |
| **Cost Model** | Implicit (just use local) | Explicit ($10/month budget) |
| **Quality Model** | Local = acceptable, Cloud = better | Tiered quality matching |
| **Hardware Role** | Primary constraint | One factor among many |

**The key insight:** R29 transforms ATLAS from a "constrained local system with cloud escape hatch" into a "cost-optimized hybrid intelligence" where hardware limitations become an economic optimization problem rather than a capability ceiling.

---

## 1. LLM Routing Architecture

### MASTER_PLAN Approach (Lines 127-133)

```python
def route_query(context_tokens: int, confidence: float) -> str:
    if context_tokens > 4000: return "cloud_sonnet"
    if confidence < 0.7: return "cloud_haiku"
    return "local"
```

**Characteristics:**
- **Binary decision:** Local unless two specific conditions fail
- **Reactive:** Confidence measured AFTER local attempts (implied)
- **Simple triggers:** Context length OR confidence threshold
- **No cost awareness:** Just route and hope
- **No classification:** All queries treated equally

### R29 Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                    Query Classification Cascade                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query → [Stage 1: Reflex] → [Stage 2: Router] → [Budget] → LLM │
│               │                    │               │             │
│         Regex <1ms          Embeddings ~20ms   Cost check       │
│               │                    │               │             │
│        ┌──────┴──────┐      ┌──────┴──────┐   ┌──┴───┐         │
│        │ Patterns:   │      │ Similarity: │   │Check:│         │
│        │ - Commands  │      │ - Prototypes│   │- Daily│        │
│        │ - Safety    │      │ - Confidence│   │- Month│        │
│        │ - Complex   │      │ - Thresholds│   │- Mode │        │
│        └─────────────┘      └─────────────┘   └──────┘         │
│                                                                  │
│  Output: Tier 1 (Local) | Tier 2 (Haiku API) | Tier 3 (SDK)    │
└─────────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- **Three-tier decision:** Match query complexity to capability tier
- **Proactive:** Classification BEFORE any inference
- **Intelligent triggers:** Regex patterns + semantic embeddings
- **Cost-aware:** Budget tracking with soft/hard limits
- **Query taxonomy:** Different query types routed differently

---

## 2. Tier Distribution and Query Taxonomy

### MASTER_PLAN Distribution (Implied)

| Destination | Trigger | Expected % |
|-------------|---------|------------|
| Local | Default | ~90%+ |
| Cloud Haiku | confidence < 0.7 | ~5-8% |
| Cloud Sonnet | context > 4K | ~2-5% |

**Assumption:** Most queries should work locally; cloud is for edge cases.

### R29 Distribution (Research-Validated)

| Tier | Model | % Queries | Query Types |
|------|-------|-----------|-------------|
| **Tier 1 - Valet** | Local Qwen2.5-3B | 40-50% | Commands, timers, basic info, greetings |
| **Tier 2 - Consigliere** | Haiku API | 35-40% | Advice, drafting, explanations |
| **Tier 3 - Operator** | Agent SDK | 10-15% | Planning, analysis, multi-tool |

**Key shift:** Intentionally routing 35-40% of queries to cloud for BETTER QUALITY, not as a failure fallback.

### Query Taxonomy (New in R29)

| Category | Examples | Route | Rationale |
|----------|----------|-------|-----------|
| **Phatic/Social** | "Good morning", "Thanks" | Local | No reasoning needed |
| **Device Control** | "Set timer", "Volume up" | Local | Pattern extraction only |
| **Basic Info** | "What time is it?" | Local | Simple retrieval |
| **Quick Knowledge** | "What supplements did I take?" | Local + DB | Database lookup |
| **Advice/Guidance** | "Good warm-up for bench?" | **Haiku** | Quality matters |
| **Drafting** | "Write polite decline email" | **Haiku** | Nuance needed |
| **Complex Planning** | "Plan my week's workouts" | **Agent SDK** | Multi-step reasoning |
| **Safety-Critical** | "Is this safe with my meds?" | **Agent SDK** | Cannot risk error |
| **Multi-Tool** | "Check Garmin, then plan" | **Agent SDK** | Tool orchestration |

---

## 3. Cost Model

### MASTER_PLAN Cost Model

**Implicit assumption:** Local is free, cloud usage should be minimal.

- No cost tracking
- No budget limits
- No visibility into spend
- Hope that cloud usage stays low

### R29 Cost Model

**Explicit budgeting with full observability:**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Cost Control System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Per-Query Tracking (SQLite):                                   │
│  - Tier used                                                    │
│  - Input/output tokens                                          │
│  - Cost in USD                                                  │
│  - Latency                                                      │
│  - Classification confidence                                    │
│                                                                  │
│  Budget Enforcement:                                            │
│  ┌────────────┬────────────┬─────────────────────────────┐     │
│  │ Threshold  │ Action     │ Behavior                    │     │
│  ├────────────┼────────────┼─────────────────────────────┤     │
│  │ 0-80%      │ Normal     │ Route per classification    │     │
│  │ 80-100%    │ Thrifty    │ Prefer local for marginal   │     │
│  │ 100%+      │ Local-only │ API blocked until reset     │     │
│  └────────────┴────────────┴─────────────────────────────┘     │
│                                                                  │
│  Projections (100 queries/day):                                 │
│  - 40-50 local: $0                                              │
│  - 35-40 Haiku: ~$1.20/month                                    │
│  - 10-15 Agent SDK: $0 (Max Plan)                               │
│  - TOTAL: ~$2.40/month (well under $10 budget)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Latency Architecture

### MASTER_PLAN Latency Budget

| Component | Time | Notes |
|-----------|------|-------|
| VAD silence | ~400ms | |
| STT (Moonshine) | ~600ms | |
| LLM first token | ~200ms | Local only |
| LLM streaming | ~1200ms | |
| TTS first audio | ~250ms | |
| **TOTAL** | **~2,400ms** | Single path |

**Problem:** What happens when cloud is needed? No latency masking.

### R29 Latency Architecture

| Tier | Classification | LLM TTFT | E2E Budget |
|------|---------------|----------|------------|
| Local | ~25ms | ~200ms | ~2,475ms |
| Haiku | ~25ms | ~500ms | ~2,775ms |
| Agent SDK | ~25ms | ~6,000ms | ~8,000ms |

**New: Latency Masking ("Poker Face Protocol")**

```python
async def voice_response(query: str):
    decision = router.classify(query)  # ~25ms

    if decision.tier != Tier.LOCAL:
        # Speak filler IMMEDIATELY (buys 1.5s perceived time)
        await tts.speak_immediate("Let me see...")  # ~250ms
        # User hears response while API is loading

    async for token in router.stream(query):
        await tts.stream_token(token)
```

**Filler Phrases (Persona-Appropriate):**
- "Let me see..."
- "One moment..."
- "Give me a moment."
- "Let me consider this."

**Result:** User perceives instant acknowledgment even for cloud queries.

---

## 5. Hardware Impact Analysis

### MASTER_PLAN Hardware Model

**Hardware as Primary Constraint:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hardware Determines Capability                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  4GB VRAM → Must use 3B model → Limited reasoning               │
│  6GB RAM  → Can run STT/TTS  → Voice works                      │
│                                                                  │
│  Capability ceiling = hardware ceiling                          │
│                                                                  │
│  To improve: Buy more hardware                                  │
│  - 8GB VRAM → 7B model → Better reasoning                       │
│  - 32GB RAM → Larger context → More history                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### R29 Hardware Model

**Hardware as One Factor Among Many:**

```
┌─────────────────────────────────────────────────────────────────┐
│                Hardware + Cloud = Optimized System               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  4GB VRAM → 3B model → Handles 40-50% of queries                │
│  Cloud API → Haiku   → Handles 35-40% of queries                │
│  Agent SDK → Full    → Handles 10-15% of queries                │
│                                                                  │
│  Capability ceiling = Claude capability (not hardware)          │
│                                                                  │
│  To improve: Multiple options                                   │
│  - More VRAM → Better local → More % handled locally → Lower $  │
│  - More budget → More cloud → Higher quality overall            │
│  - Better network → Lower API latency → Better UX               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Hardware Relevance Comparison

| Resource | MASTER_PLAN Impact | R29 Impact |
|----------|-------------------|------------|
| **VRAM (4GB)** | CRITICAL - determines model size | MODERATE - affects local tier capacity |
| **RAM (6GB)** | IMPORTANT - runs pipeline | MODERATE - adds embedding model (~90MB) |
| **CPU** | MODERATE - runs STT | SLIGHTLY HIGHER - runs embeddings too |
| **Network** | LOW - occasional cloud | IMPORTANT - 35-50% of queries use API |
| **GPU Speed** | HIGH - inference speed | MODERATE - only 40-50% runs locally |

### New Hardware Requirements (R29)

| Component | RAM | Purpose |
|-----------|-----|---------|
| all-MiniLM-L6-v2 | ~90MB | Embedding classification |
| SQLite cost tracker | ~10MB | Usage logging |
| Prototype embeddings | ~5MB | Cached tier centroids |
| **Additional Total** | **~105MB** | |

**Net impact:** RAM usage increases by ~105MB, but VRAM pressure DECREASES because fewer queries hit local LLM.

---

## 6. Can Better Hardware Improve This?

### Yes, But Differently Than Before

#### Scenario A: More VRAM (8GB+)

| Change | Effect |
|--------|--------|
| Run 7B local model | Higher quality local responses |
| Shift tier distribution | 60% local, 30% Haiku, 10% SDK |
| Cost impact | Reduce API spend by ~40% |
| Latency impact | Same (7B still ~200-400ms TTFT) |

**Verdict:** Saves money, marginal quality improvement for "moderate" queries.

#### Scenario B: More RAM (32GB+)

| Change | Effect |
|--------|--------|
| Larger embedding model | Better classification accuracy |
| Bigger context windows | More conversation history |
| Run multiple models | Specialist models per domain |
| Cost impact | Minimal direct savings |

**Verdict:** Better classification, not transformative.

#### Scenario C: Better GPU (RTX 4090)

| Change | Effect |
|--------|--------|
| Run 13B+ local model | Near-cloud quality locally |
| Faster inference | Local competitive with API latency |
| Shift tier distribution | 80% local, 15% API, 5% SDK |
| Cost impact | Near-zero API spend |

**Verdict:** Could eliminate Tier 2 entirely - local becomes good enough.

#### Scenario D: Faster Network (Fiber + CDN proximity)

| Change | Effect |
|--------|--------|
| Lower API latency | Haiku TTFT drops from ~500ms to ~200ms |
| Shift tier thresholds | More queries to Haiku (same latency as local) |
| Cost impact | Increase (more API usage) |
| Quality impact | Better overall quality |

**Verdict:** Makes cloud more attractive, increases quality at cost of $.

### The Critical Insight

**MASTER_PLAN logic:** "I can't afford good hardware → I'm stuck with limited capability"

**R29 logic:** "I can't afford good hardware → I'll optimize the cost/quality tradeoff per query"

Better hardware changes the ECONOMICS but the hybrid architecture remains valuable:
- Even with a 4090, you'd still want Agent SDK for multi-tool tasks
- Even with 64GB RAM, you'd still want cloud for safety-critical queries
- The routing intelligence has value at ANY hardware level

---

## 7. New Capabilities Unlocked by R29

### 7.1 Quality Optimization Per Query

**Before:** Every query gets 3B-quality response (unless it fails)
**After:** Each query gets appropriate-tier quality

| Query | MASTER_PLAN Quality | R29 Quality |
|-------|--------------------|--------------
| "Set timer 5 min" | 3B (overkill) | 3B (appropriate) |
| "Good warm-up for bench?" | 3B (insufficient) | Haiku (appropriate) |
| "Plan my week's workouts" | 3B (poor) or Sonnet (expensive) | Agent SDK (appropriate) |

### 7.2 Cost Visibility and Control

**Before:** Unknown spend, hope it's low
**After:**
- Per-query cost tracking
- Daily/monthly rollups
- Budget alerts
- Graceful degradation
- Historical analysis

### 7.3 Resilience and Fallback

**Before:** If cloud fails... unclear
**After:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Graceful Degradation Matrix                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Scenario        │ Haiku │ SDK │ Action                         │
│  ────────────────┼───────┼─────┼────────────────────────────────│
│  Normal          │  ✓    │  ✓  │ Route per classification       │
│  Haiku down      │  ✗    │  ✓  │ Local for simple, SDK for rest │
│  SDK down        │  ✓    │  ✗  │ Local for simple, Haiku rest   │
│  Both down       │  ✗    │  ✗  │ Local-only + disclaimer        │
│  Budget exceeded │  —    │  —  │ Local-only until reset         │
│  Rate limited    │  ⚠    │  ✓  │ Backoff + retry, then fallback │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 Adaptive Learning (Future)

**Before:** Static routing rules
**After:** LinUCB contextual bandits can learn:
- Which queries YOUR usage pattern sends to which tier
- Optimal thresholds for YOUR query distribution
- Per-category routing adjustments

Feedback signals:
- User corrections → negative signal
- Follow-up questions → incomplete answer
- Task completion → success
- "Thanks" / positive phatic → reward

### 7.5 Persona-Consistent UX

**Before:** Jarring transitions when cloud needed
**After:**
- Latency masking hides routing decisions
- Persona-appropriate failure messages
- Invisible tier switching
- User experiences quality variation as "natural"

---

## 8. What Stays the Same

These MASTER_PLAN decisions are UNCHANGED by R29:

| Component | Decision | Still Valid |
|-----------|----------|-------------|
| Local LLM | Qwen2.5-3B-Instruct | Yes - Tier 1 model |
| STT | Moonshine Base (CPU) | Yes - unchanged |
| TTS | Kokoro-82M (GPU) | Yes - unchanged |
| VAD | Silero v6.2 | Yes - unchanged |
| Memory | SQLite + sqlite-vec | Yes - unchanged |
| Embeddings | BGE-small-en-v1.5 | Yes - for memory search |
| Persona | Lethal Gentleman | Yes - integrated into routing UX |
| Verification | External grounding | Yes - unchanged |
| Workflows | LangGraph for complex | Yes - Tier 3 uses this |

**R29 is ADDITIVE** - it enhances the LLM layer without breaking other components.

---

## 9. Architecture Diagram Comparison

### MASTER_PLAN Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ATLAS Voice Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Mic → VAD → STT → [Simple Router] → LLM → TTS → Speaker       │
│                           │                                      │
│                    ┌──────┴──────┐                               │
│                    │ if ctx>4K:  │                               │
│                    │   Sonnet    │                               │
│                    │ elif conf<.7│                               │
│                    │   Haiku     │                               │
│                    │ else:       │                               │
│                    │   Local     │                               │
│                    └─────────────┘                               │
│                                                                  │
│   Memory ←──────────── SQLite + sqlite-vec ──────────→ Skills   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### R29 Hybrid Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   ATLAS R29 Hybrid Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Mic → VAD → STT ─┬─→ [Classifier] → [Router] → LLM → TTS     │
│                    │        │             │         │           │
│                    │   ┌────┴────┐   ┌────┴────┐   │           │
│                    │   │ Stage 1 │   │ Budget  │   │           │
│                    │   │ Regex   │   │ Check   │   │           │
│                    │   │ <1ms    │   │         │   │           │
│                    │   └────┬────┘   └────┬────┘   │           │
│                    │   ┌────┴────┐        │        │           │
│                    │   │ Stage 2 │        │        │           │
│                    │   │ Embed   │        │        │           │
│                    │   │ ~20ms   │        │        │           │
│                    │   └────┬────┘        │        │           │
│                    │        │             │        │           │
│                    │        ▼             ▼        │           │
│                    │   ┌─────────────────────┐    │           │
│                    │   │   Tier Selection    │    │           │
│                    │   │  ┌───┐ ┌───┐ ┌───┐ │    │           │
│                    │   │  │ 1 │ │ 2 │ │ 3 │ │    │           │
│                    │   │  │Loc│ │API│ │SDK│ │    │           │
│                    │   │  └───┘ └───┘ └───┘ │    │           │
│                    │   └─────────────────────┘    │           │
│                    │                              │           │
│                    │   [Latency Mask]             │           │
│                    │   "Let me see..."            │           │
│                    │        │                     │           │
│                    └────────┼─────────────────────┘           │
│                             │                                  │
│                             ▼                                  │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │                    Cost Tracker                          │ │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │ │
│   │  │ Log Use  │  │ Check $  │  │ Adapt    │              │ │
│   │  │ SQLite   │  │ Limits   │  │ Thresholds│             │ │
│   │  └──────────┘  └──────────┘  └──────────┘              │ │
│   └─────────────────────────────────────────────────────────┘ │
│                                                                │
│   Memory ←──────────── SQLite + sqlite-vec ──────────→ Skills │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 10. Summary: The Paradigm Shift

| Dimension | MASTER_PLAN | R29 Hybrid |
|-----------|-------------|------------|
| **Mental Model** | "Make local work, escape to cloud" | "Match tier to query" |
| **Hardware Role** | Capability ceiling | Cost optimization factor |
| **Cloud Usage** | Failure fallback | Intentional quality tier |
| **Cost** | Implicit/unknown | Explicit/budgeted |
| **Quality** | Binary (local/cloud) | Three tiers |
| **Classification** | Post-hoc confidence | Pre-inference semantic |
| **Latency** | Accept variance | Mask variance |
| **Resilience** | Unclear | Explicit degradation |
| **Learning** | None | Adaptive (future) |

### The Fundamental Transformation

**MASTER_PLAN asks:** "Can my hardware handle this query?"
- If yes → local
- If no → cloud (reluctantly)

**R29 asks:** "What's the optimal tier for this query given cost/quality/latency tradeoffs?"
- Simple command → local (fast, free, sufficient)
- Needs nuance → Haiku (fast, cheap, good quality)
- Needs reasoning → Agent SDK (slow, free, excellent)
- Over budget → local (graceful degradation)

### The Net Effect

1. **Quality improves** - 35-40% of queries now get Haiku instead of 3B
2. **Cost is controlled** - $2-3/month instead of unknown
3. **Hardware pressure decreases** - fewer queries hit local LLM
4. **Complexity increases** - more code, more configuration
5. **Observability improves** - full visibility into usage and spend
6. **Resilience improves** - explicit fallback paths
7. **UX improves** - latency masking hides routing decisions

### Should You Do This?

**Yes, if:**
- You want better quality on "moderate" queries
- You want cost visibility and control
- You're okay with ~$2-5/month API spend
- You value resilience and fallback paths

**Maybe not, if:**
- Local quality is truly sufficient for all your queries
- You have zero tolerance for API costs
- You're upgrading to much better hardware soon
- You prefer simplicity over optimization

### Hardware Upgrade Recommendation

The R29 analysis changes the hardware calculation:

**Before R29:** "I need 8GB VRAM for better local model"
**After R29:** "8GB VRAM would save ~$1/month in API costs"

The $210 RAM upgrade is now a **cost optimization**, not a **capability unlock**. You already have full Claude capability via API/SDK. The question is whether the upfront hardware cost is worth the ongoing API savings.

At $2.40/month API spend, $210 hardware = 87 months to break even.
At current hardware, you get full capability NOW for $2.40/month.

**Recommendation:** Implement R29 first. Gather real usage data. Then decide on hardware based on actual tier distribution and costs.

---

## 11. Files to Update in MASTER_PLAN

If R29 is adopted, these sections need updating:

| Section | Current | Update To |
|---------|---------|-----------|
| §2 Cloud Routing | 3-line function | Reference R29 router |
| §4 Voice Pipeline | Single LLM path | Add classifier + router |
| §13 Files to Create | Simple router.py | Full routing subsystem |
| §14 RAM Budget | ~1.85GB | ~1.95GB (+embeddings) |
| NEW | — | Add cost tracking schema |
| NEW | — | Add routing.yaml config |
| NEW | — | Add R29 to research status |

---

*This document should be read alongside `/home/squiz/ATLAS/docs/HANDOVER_R29_COMPLETE.md` for implementation details.*
