# ATLAS Hybrid LLM Routing - Agent Handover Document

**Date:** January 6, 2026
**Context:** 13% until auto-compaction, full R29 research complete
**Task:** Analyze research findings, reconcile with existing architecture, implement routing system

---

## 1. What Was Done (Previous Session)

### 1.1 Voice Latency Benchmark
Ran benchmark comparing LLM backends for voice interactions:

| Model | TTFT | Simulated E2E | Verdict |
|-------|------|---------------|---------|
| Local Qwen2.5-3B | 175-1312ms | 2,162ms | GOOD |
| Claude Agent SDK | 6,076ms | 6,926ms | TOO SLOW (subprocess overhead) |

**Key finding:** Agent SDK adds ~5-6s overhead due to Claude Code subprocess spawning. Direct API is needed for voice latency.

### 1.2 R29 Research Completed
Two comprehensive research documents produced:
- `/home/squiz/ATLAS/docs/research/R29.AI Assistant Routing Strategy Research - Google Docs.pdf` (19 pages, Gemini Deep Research)
- `/home/squiz/ATLAS/docs/research/R29.LLM routing strategies for voice-first AI with three-tier architecture.md` (Claude research)

### 1.3 Files Created
- `/home/squiz/ATLAS/atlas/llm/cloud.py` - Claude Agent SDK client (working, but slow)
- `/home/squiz/ATLAS/scripts/voice_latency_benchmark.py` - Benchmark script
- `/home/squiz/.claude/plans/optimized-juggling-canyon.md` - Planning document

---

## 2. R29 Research Key Findings

### 2.1 Recommended Architecture: "Tiered Semantic Cascade"

```
┌─────────────────────────────────────────────────────────────────┐
│                    ATLAS Query Flow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Voice → STT → [Stage 1: Reflex] → [Stage 2: Router] → LLM     │
│                      │                    │                      │
│              Regex match?          Embedding sim?                │
│                   ↓                      ↓                       │
│            ┌──────────┐           ┌──────────────┐              │
│            │ Direct   │           │ Route to:    │              │
│            │ Device   │           │ - Local      │              │
│            │ Control  │           │ - Cloud      │              │
│            │ (<1ms)   │           │ - Agent SDK  │              │
│            └──────────┘           └──────────────┘              │
│                                         │                        │
│                              [Stage 3: Safety Net]               │
│                              Perplexity check on                 │
│                              local generation                    │
│                              If confused → escalate              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Three-Tier Model Distribution

| Tier | Model | % Queries | Cost | Latency | Use Case |
|------|-------|-----------|------|---------|----------|
| **1 - Valet** | Qwen2.5-3B (local) | 40-50% | Free | <200ms | Commands, device control, basic info |
| **2 - Consigliere** | Haiku 4.5 (API) | 35-40% | ~$0.001/q | ~500ms | Advice, drafting, nuanced responses |
| **3 - Operator** | Agent SDK | 10-15% | Free* | ~6s | Multi-tool tasks, planning, analysis |

*Agent SDK is free via Max Plan subscription but latency-expensive.

### 2.3 Classification Approach (Hybrid Semantic Cascade)

| Stage | Mechanism | Latency | Purpose |
|-------|-----------|---------|---------|
| 1. Reflex | Regex/Keyword patterns | <1ms | Catch obvious commands |
| 2. Router | all-MiniLM-L6-v2 embeddings | ~20ms | Semantic similarity to tier prototypes |
| 3. Safety | Local Qwen perplexity check | ~250ms | If local is "confused", escalate to cloud |

**Why this approach:**
- Embedding routers achieve 90-95% of LLM router accuracy at 1/100th the latency
- Perplexity-based escalation catches edge cases the embedding router misses
- Aligns with "Lethal Gentleman" persona: if ATLAS hesitates, it defers rather than blunders

### 2.4 Cost Projections (Confirmed Feasible)

**Per Haiku query:** ~$0.001 (230 input + 150 output tokens)
**$10/month budget:** ~10,000 cloud queries = ~330/day
**With 75% local routing:** Effectively unlimited for personal use

| Usage Level | Daily Total | Cloud Queries | Monthly Cost |
|-------------|-------------|---------------|--------------|
| Light | 50 | 13 | ~$0.40 |
| Medium | 100 | 25 | ~$0.75 |
| Heavy | 200 | 50 | ~$1.50 |
| Intensive | 500 | 125 | ~$3.75 |

### 2.5 Query Taxonomy (ATLAS-Specific)

**Category A - "The Valet" (Tier 1 Local):**
- Phatic/Social: "Good morning", "Thank you"
- Device Control: "Dim lights", "Volume 50%"
- Basic Info: "What time is it?", "Weather report"
- Recent Memory: "What did I just say?"
- **Persona note:** Responses crisp - "Done, sir." "Right away."

**Category B - "The Consigliere" (Tier 2 Cloud):**
- Drafting: "Write a polite decline to this invitation"
- Summarization: "Summarize this email thread"
- Advisory: "What are the pros and cons?"
- Complex Knowledge: "Explain the mechanism of..."
- **Persona note:** More verbose - "If I may suggest, sir..."

**Category C - "The Operator" (Tier 3 Agent SDK):**
- Planning: "Plan a 3-day trip under $1000"
- Execution: "Book a table for tonight"
- Data Analysis: "Analyze my spending spreadsheet"
- **Persona note:** Buy time - "I shall attend to this immediately. Please allow me a moment."

### 2.6 Persona Integration ("Lethal Gentleman" from R21)

**Latency Masking ("Poker Face Protocol"):**
- When router selects Cloud, immediately TTS: "Let me see..." or "One moment..."
- Buys 1.5s of perceived response time
- User perceives instant response even if actual answer takes 3s

**Failure Responses (from R21):**

| Scenario | Persona Response |
|----------|------------------|
| Cloud Timeout | "The external lines are congested, sir. I shall recall from my own memory." |
| API Error | "I am unable to access that archive at the moment. Perhaps we can approach differently?" |
| Misunderstanding | "My apologies. I seem to have missed the nuance. Let me reconsider." |
| Agent Latency | "I shall attend to this immediately. It may require some time to coordinate." |
| Budget Exhausted | "I am afraid my connection to the external archives is temporarily severed." |

### 2.7 Adaptive Routing (LinUCB Contextual Bandits)

**Implicit feedback signals:**
1. **Reformulation** (negative): User repeats query within 15s → penalty
2. **Interruption** (negative): User says "Stop", "No" mid-TTS → penalty
3. **Positive phatic** (positive): "Thanks", "Good job", "Perfect" → reward

**Memory requirement:** ~600KB for LinUCB matrices (384-dim MiniLM embeddings)

---

## 3. Files to Read (Critical Context)

### Architecture & Specifications
- `/home/squiz/ATLAS/docs/MASTER_PLAN.md` - Overall system architecture
- `/home/squiz/ATLAS/docs/MASTER_IMPLEMENTATION_GUIDE.md` - Implementation details from R1-R6

### Persona
- `/home/squiz/ATLAS/docs/research/R21.The Lethal Gentleman - A complete AI persona specification.md` - Full persona spec

### Current Voice Pipeline
- `/home/squiz/ATLAS/atlas/voice/pipeline.py` - Voice orchestration (STT → LLM → TTS)
- `/home/squiz/ATLAS/atlas/llm/local.py` - Existing Ollama client interface (MATCH THIS)
- `/home/squiz/ATLAS/atlas/llm/cloud.py` - Agent SDK client (created, needs Direct API added)

### R29 Research
- `/home/squiz/ATLAS/docs/research/R29.AI Assistant Routing Strategy Research - Google Docs.pdf`
- `/home/squiz/ATLAS/docs/research/R29.LLM routing strategies for voice-first AI with three-tier architecture.md`

---

## 4. What Needs to Be Done

### 4.1 Immediate Implementation

**Step 1: Create Direct Anthropic API Client**
File: `/home/squiz/ATLAS/atlas/llm/api.py`
- Install: `pip install anthropic`
- Must match OllamaClient interface (especially `stream()` method)
- Implement prompt caching for system prompt (90% savings)

**Step 2: Create Semantic Router**
File: `/home/squiz/ATLAS/atlas/llm/router.py`
- Install: `pip install sentence-transformers`
- Load all-MiniLM-L6-v2 on CPU (save VRAM for Qwen)
- Define tier prototype embeddings
- Implement confidence thresholds

**Step 3: Create Cost Tracker**
File: `/home/squiz/ATLAS/atlas/llm/cost_tracker.py`
- SQLite-based usage logging
- Soft limit at $8, hard limit at $10
- "Thrifty Mode" when approaching budget

**Step 4: Create Query Classifier**
File: `/home/squiz/ATLAS/atlas/llm/classifier.py`
- Combine: Regex (Stage 1) + Embeddings (Stage 2)
- Return: tier, confidence, category

**Step 5: Update Voice Pipeline**
File: `/home/squiz/ATLAS/atlas/voice/pipeline.py`
- Replace direct LLM call with router
- Add latency masking (filler phrases)
- Add circuit breaker for API failures

### 4.2 Configuration Structure

```yaml
# /home/squiz/ATLAS/config/routing.yaml
system:
  persona: "lethal_gentleman"
  latency_budget_ms: 3000

router:
  model: "all-MiniLM-L6-v2"
  device: "cpu"  # Save VRAM for Qwen
  thresholds:
    local: 0.65
    cloud: 0.82
    agent: 0.88
  reflex_patterns:
    - "turn on.*"
    - "set timer.*"
    - "stop"
    - "pause"
    - "play"

budget:
  monthly_limit_usd: 10.00
  soft_limit_pct: 0.80
  hard_limit_pct: 1.00
```

---

## 5. Areas Requiring Further Research/Optimization

### 5.1 Embedding Centroid Training
**Status:** Not yet done
**Need:** 200+ labeled queries per tier to compute prototype centroids
**Action:** Create training dataset from expected ATLAS interactions
**Research prompt if needed:** "How to create and validate semantic router centroids for intent classification"

### 5.2 Perplexity-Based Escalation
**Status:** Theoretical only
**Need:** Empirical threshold tuning for Qwen2.5-3B perplexity
**Challenge:** Ollama doesn't expose token-level logits by default
**Alternative:** Use `logprobs` parameter if available, or confidence heuristics

### 5.3 Prompt Caching Implementation
**Status:** Not implemented
**Need:** Cache the system prompt (persona) for 90% cost reduction
**Anthropic docs:** Use `cache_control` parameter with `ephemeral` type
**Potential savings:** From ~$0.001 to ~$0.0004 per query

### 5.4 Direct API Latency Benchmark
**Status:** Not yet tested
**Need:** Verify actual TTFT for Direct Haiku API from Australia
**Expected:** ~500ms, but could be higher due to geographic latency
**Action:** Add direct API test to benchmark script

### 5.5 A/B Testing Framework
**Status:** Not implemented
**Need:** Time-series A/B testing (single user)
**Approach:** Week 1 baseline (threshold 0.75), Week 2 conservative (0.85)
**Metric:** "Reformulation Rate" vs "Daily Cost"

### 5.6 Circuit Breaker Tuning
**Status:** Pattern defined, not implemented
**Need:** pybreaker integration with appropriate timeouts
**Parameters:** 3 failures → open, 60s reset timeout

---

## 6. Dependencies to Install

```bash
pip install anthropic          # Direct API client
pip install sentence-transformers  # Embedding model
pip install pybreaker          # Circuit breaker pattern
pip install tenacity           # Retry logic with backoff
```

---

## 7. Key Code Patterns from Research

### 7.1 Semantic Router (from R29)

```python
class AtlasRouter:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        self.routes = {
            "TIER_3_AGENT": ["plan a trip", "analyze this file", "research the history of"],
            "TIER_2_CLOUD": ["draft an email", "summarize this", "explain the nuance"],
            "TIER_1_LOCAL": ["what time is it", "turn on the lights", "weather forecast"]
        }
        self.route_vectors = {k: self.model.encode(v) for k, v in self.routes.items()}

    def route(self, query: str) -> str:
        query_vec = self.model.encode([query])
        best_score, selected_tier = -1, "TIER_1_LOCAL"

        for tier, prototypes in self.route_vectors.items():
            max_sim = np.max(cosine_similarity(query_vec, prototypes))
            threshold = 0.85 if tier != "TIER_1_LOCAL" else 0.65
            if max_sim > threshold and max_sim > best_score:
                best_score, selected_tier = max_sim, tier

        return selected_tier
```

### 7.2 Cost Tracker (Singleton)

```python
class CostTracker:
    PRICE_IN = 1.0 / 1_000_000   # $1 per M input
    PRICE_OUT = 5.0 / 1_000_000  # $5 per M output

    def track_transaction(self, input_tokens, output_tokens):
        cost = (input_tokens * self.PRICE_IN) + (output_tokens * self.PRICE_OUT)
        self.daily_spend += cost
        self.monthly_spend += cost

    def can_afford_cloud(self):
        return self.daily_spend < 0.33  # ~$10/month ÷ 30 days
```

### 7.3 Circuit Breaker Decorator

```python
@circuit_breaker(max_failures=3, reset_timeout=60)
@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(max=30))
async def call_haiku(query: str, timeout: float = 5.0):
    async with asyncio.timeout(timeout):
        return await anthropic_client.messages.create(...)
```

---

## 8. Validation Checklist

Before considering routing implementation complete:

- [ ] Direct Haiku API client created and tested
- [ ] Semantic router with tier prototypes working
- [ ] Cost tracker logging all API calls to SQLite
- [ ] Circuit breaker protecting against API failures
- [ ] Filler phrases implemented for latency masking
- [ ] Budget soft/hard limits enforced
- [ ] Voice pipeline integrated with router
- [ ] Benchmark comparing all three tiers
- [ ] Persona-appropriate failure messages implemented

---

## 9. Questions for User (If Needed)

1. **API Key:** Do you have an Anthropic API key ready, or need guidance on obtaining one?
2. **Prototype queries:** Can you provide 20-30 example queries per tier for training the router?
3. **Budget alerts:** How should ATLAS notify you when approaching budget limits?
4. **Explicit commands:** Do you want `/deep` and `/quick` slash commands for manual override?

---

## 10. Summary

**The research confirms the hybrid architecture is both feasible and cost-effective.** The key insight is that 70-75% of voice queries are simple enough for local processing, leaving the API budget concentrated on the 25% where quality matters.

**Critical success factors:**
1. Embedding-based routing must achieve >90% accuracy
2. Latency masking ("Poker Face Protocol") essential for UX
3. Cost tracking prevents budget overruns
4. Persona integration makes technical decisions feel natural

**Next action:** Implement the routing system following the patterns in this document, starting with the Direct Haiku API client, then the semantic router, then integrating with the voice pipeline.
