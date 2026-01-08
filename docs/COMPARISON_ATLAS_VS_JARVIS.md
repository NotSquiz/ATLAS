# ATLAS vs isair/jarvis: Architectural Comparison

**Date:** January 6, 2026
**Purpose:** Compare ATLAS design with [isair/jarvis](https://github.com/isair/jarvis) to identify strengths, weaknesses, and potential improvements

---

## Executive Summary

| Dimension | ATLAS | isair/jarvis | Winner |
|-----------|-------|--------------|--------|
| **LLM Intelligence** | Three-tier routing (Local/API/SDK) | Single local model (20B) | ATLAS |
| **Cost Management** | SQLite tracking, budgets, thrifty mode | None (all local) | ATLAS |
| **Memory System** | RAG + sqlite-vec + FTS5 | Persistent + keyword search | Comparable |
| **MCP Integration** | Planned, basic | Extensive (500+ services) | jarvis |
| **Voice** | Wake word + STT + TTS | Wake word + interrupt + voice cloning | jarvis |
| **Persona** | Single sophisticated ("Lethal Gentleman") | Multiple profiles (Dev/Business/Coach) | Different approaches |
| **Home Automation** | Planned via integrations | Native Home Assistant MCP | jarvis |
| **Privacy Hardening** | Implicit (local-first) | Explicit verification mode | jarvis |
| **Hardware Flexibility** | Designed for constraints → scaling | 16GB minimum, GPU optional | ATLAS |
| **Research Depth** | 29 research topics (R1-R29) | Practical implementation | ATLAS |
| **Production Ready** | In development | Functional now | jarvis |

**Bottom Line:** jarvis is more complete and usable TODAY. ATLAS has more sophisticated intelligence architecture but isn't built yet. They solve different problems - jarvis is "good local AI now", ATLAS is "optimized hybrid AI with research backing."

---

## 1. LLM Architecture

### isair/jarvis
```
┌─────────────────────────────────────────────────────────────────┐
│                    jarvis LLM Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Query → Ollama (gpt-oss:20b) → Response                   │
│                                                                  │
│  - Single model for everything                                  │
│  - 20B parameters (decent but not frontier)                     │
│  - No cloud fallback                                            │
│  - No routing intelligence                                      │
│  - Simple but limited                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Strengths:**
- Simple, predictable
- Zero cost
- Complete privacy
- Works offline

**Weaknesses:**
- 20B model can't match frontier reasoning
- No escalation path for complex queries
- One-size-fits-all quality

### ATLAS (R29 Design)
```
┌─────────────────────────────────────────────────────────────────┐
│                    ATLAS R29 LLM Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query → [Classifier] → [Router] → [Budget Check] → Tier       │
│              │              │            │                       │
│         Regex + Embed   Confidence    Cost Track                │
│              │              │            │                       │
│              ▼              ▼            ▼                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Tier 1 (40-50%)  │  Tier 2 (35-40%)  │  Tier 3 (10-15%)  │
│  │   Local 3B-70B     │  Haiku API        │  Agent SDK      │   │
│  │   Free, <200ms     │  $0.001, ~500ms   │  Free, ~6s      │   │
│  │   Commands         │  Advice           │  Planning       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  + Cost tracking + Budget limits + Graceful degradation         │
│  + Adaptive learning (LinUCB) + Latency masking                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Strengths:**
- Right-sized model for each query
- Frontier reasoning when needed (Claude)
- Cost-aware with budgets
- Adaptive learning
- Graceful degradation

**Weaknesses:**
- More complex
- Requires API key for Tier 2
- Not implemented yet

### Verdict: ATLAS wins on intelligence, jarvis wins on simplicity

---

## 2. Memory System

### isair/jarvis
```python
# Memory approach
- Persistent storage (never forgets)
- Keyword extraction from conversations
- Time-range filtering
- Semantic search with nomic-embed-text
- "Memory enrichment" at query time

# Example from their docs:
[ memory ] 🧠 searching with keywords=['news', 'interest'],
           time: 2025-01-15T00:00:00Z to 2025-01-15T23:59:59Z
[ memory ] ✅ found 3 results for memory enrichment
```

### ATLAS
```python
# Memory approach (from MASTER_PLAN)
- SQLite + sqlite-vec + FTS5
- BGE-small-en-v1.5 embeddings (ONNX)
- Hybrid RRF search (60% vector, 40% FTS)
- Importance scoring
- <75ms at 100K records

# Schema
CREATE TABLE semantic_memory (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP,
    embedding BLOB
);
```

### Comparison

| Feature | jarvis | ATLAS |
|---------|--------|-------|
| Persistence | ✅ | ✅ |
| Semantic search | ✅ nomic-embed | ✅ BGE-small |
| Full-text search | ❓ Unclear | ✅ FTS5 |
| Hybrid ranking | ❓ | ✅ RRF |
| Keyword extraction | ✅ Automatic | ❌ Not specified |
| Time filtering | ✅ Native | ❌ Not specified |
| Importance scoring | ❌ | ✅ |
| Performance benchmark | ❓ | ✅ <75ms/100K |

### Verdict: Comparable - jarvis has better keyword/time features, ATLAS has better hybrid search

**ATLAS should adopt:**
- Automatic keyword extraction
- Time-range filtering in queries
- Memory enrichment pattern

---

## 3. Voice System

### isair/jarvis
```
Features:
- Wake word: "Jarvis" (always listening)
- Interrupt: "stop" or "shush" mid-response
- Hot window: Stays active for follow-ups
- TTS Options:
  - Standard TTS
  - Chatterbox (voice cloning + emotion)
  - 3-10 second sample for cloning
  - Exaggeration control (0.0-1.0+)
```

### ATLAS
```
Features (from MASTER_PLAN):
- Wake word: Planned (Silero VAD)
- STT: Moonshine Base (CPU)
- TTS: Kokoro-82M (GPU streaming)
- Latency budget: <2,400ms E2E
- No interrupt capability specified
- No voice cloning
```

### Comparison

| Feature | jarvis | ATLAS |
|---------|--------|-------|
| Wake word | ✅ "Jarvis" | ⏳ Planned |
| Interrupt mid-speech | ✅ "stop/shush" | ❌ |
| Voice cloning | ✅ Chatterbox | ❌ |
| Emotion control | ✅ | ❌ |
| Latency engineering | ❓ | ✅ Explicit budget |
| Streaming TTS | ❓ | ✅ Kokoro |
| Hot window (follow-ups) | ✅ | ❌ Not specified |

### Verdict: jarvis wins on features, ATLAS wins on latency engineering

**ATLAS should adopt:**
- Interrupt capability ("stop" command)
- Hot window mode for follow-ups
- Voice cloning option (Chatterbox or similar)

---

## 4. Persona System

### isair/jarvis: Multiple Profiles
```
Three contextual personalities:
1. Developer - debugging, code reviews, technical help
2. Business - professional tasks, meeting planning
3. Life Coach - health tracking, personal advice

Automatic switching based on query context.
Each profile has different tool access and response style.
```

### ATLAS: Single Sophisticated Persona
```
"Lethal Gentleman" (R16-R21):
- Capable, refined, restrained
- "Power held in check signals greater capability"
- Direct speech, no empty phrases

Five Interaction MODES (not personalities):
1. Minimal - User in flow, brief responses
2. Structured - User overwhelmed, break into steps
3. Challenging - User stuck, OARS framework
4. Philosophical - Meaning-seeking, open questions
5. Listening - Venting, reflect don't fix
```

### Comparison

| Approach | jarvis | ATLAS |
|----------|--------|-------|
| Multiple personalities | ✅ 3 profiles | ❌ 1 persona |
| Context-aware switching | ✅ | ✅ (modes) |
| Tool routing by profile | ✅ | ❌ |
| Depth of persona design | Basic | Deep (R16-R21) |
| Psychological framework | ❌ | ✅ OARS, MI |
| Speech patterns defined | ❓ | ✅ Detailed |

### Verdict: Different philosophies - both valid

**Consideration for ATLAS:**
jarvis's approach of "Developer/Business/Coach" profiles could be ADDED to the Lethal Gentleman. The persona stays consistent, but tool access and response depth vary:

```
Lethal Gentleman (always)
├── Developer Mode → Code tools, technical depth
├── Business Mode → Calendar, email, professional tone
└── Coach Mode → Health tools, motivational approach
```

---

## 5. MCP Integration

### isair/jarvis: Extensive
```json
// Ready-to-use integrations:
{
  "Google Workspace": "Gmail, Drive, Calendar, Docs, Sheets",
  "Notion": "Knowledge base",
  "Slack": "Team communication",
  "Databases": "MySQL, PostgreSQL, SQLite, MongoDB",
  "GitHub": "Repos, issues, PRs, workflows",
  "VSCode": "Code analysis",
  "Discord": "Community management",
  "Home Assistant": "Smart home control",
  "500+ via Composio": "Everything else"
}
```

### ATLAS: Planned
```
From MASTER_PLAN:
- MCP: STDIO transport, unified server
- Garmin integration (planned)
- Calendar integration (planned)
- No pre-built MCP configurations
```

### Verdict: jarvis wins decisively

**ATLAS must adopt:**
- Pre-built MCP configurations for common services
- Home Assistant MCP integration
- Google Workspace integration
- The Composio pattern for extensibility

---

## 6. Privacy & Security

### isair/jarvis: Explicit Hardening
```json
// Hardened configuration
{
  "web_search_enabled": false,
  "mcps": {},
  "location_auto_detect": false,
  "location_cgnat_resolve_public_ip": false
}

// Verification commands
sudo lsof -i -n -P | grep jarvis  # macOS
ss -tupan | grep jarvis           # Linux
```

- Automatic redaction of sensitive patterns
- Local storage in `~/.local/share/jarvis`
- User-controlled deletion and export
- Network verification tools

### ATLAS: Implicit
```
- Local-first by design
- No explicit hardening mode
- No verification tools
- No redaction patterns
```

### Verdict: jarvis wins

**ATLAS should adopt:**
- Hardened mode configuration
- Sensitive data redaction patterns
- Network verification scripts
- Data export/deletion tools

---

## 7. Unique Features

### jarvis Has, ATLAS Lacks

| Feature | Value | Difficulty to Add |
|---------|-------|-------------------|
| Screenshot OCR | Visual context for debugging | Medium |
| Voice cloning | Personalized TTS | Medium |
| Interrupt commands | Better UX | Easy |
| Hot window mode | Conversation flow | Easy |
| Multiple personalities | Context routing | Medium |
| 500+ MCP integrations | Ecosystem | Hard (time) |
| Privacy verification | Trust | Easy |
| Cross-platform scripts | Usability | Easy |

### ATLAS Has, jarvis Lacks

| Feature | Value | jarvis Could Add |
|---------|-------|------------------|
| Three-tier routing | Right-sized quality | Complex |
| Cost tracking | Budget management | Medium |
| Semantic classification | Intelligent routing | Complex |
| Latency masking | UX polish | Easy |
| Circuit breakers | Resilience | Medium |
| Adaptive learning | Improvement over time | Complex |
| Research backing | Confidence in decisions | N/A |
| Hardware scaling path | Constraint → power | N/A |
| Verification architecture (R22) | Quality assurance | Medium |
| DAG execution (R23) | Parallel workflows | Medium |

---

## 8. Production Readiness

| Aspect | jarvis | ATLAS |
|--------|--------|-------|
| Can install today | ✅ | ❌ |
| Working voice | ✅ | Partial |
| Working memory | ✅ | Planned |
| Working MCP | ✅ | Skeleton |
| Documentation | ✅ Good | ✅ Extensive |
| Test suite | ✅ | ❌ |
| Multi-platform | ✅ | ❌ (WSL2 only) |

### Verdict: jarvis is usable now, ATLAS is still in design/early implementation

---

## 9. Strategic Recommendations

### What ATLAS Should Adopt from jarvis

1. **Immediate (Easy Wins):**
   - Interrupt commands ("stop", "shush")
   - Hot window mode for follow-ups
   - Privacy verification scripts
   - Cross-platform install scripts

2. **Short-term (Medium Effort):**
   - Screenshot/OCR capability
   - Voice cloning option
   - Multiple personality profiles (within Lethal Gentleman)
   - Automatic keyword extraction for memory

3. **Long-term (Significant Effort):**
   - Extensive MCP pre-configurations
   - Composio-style 500+ integrations
   - Home Assistant native integration

### What ATLAS Should Keep (Advantages Over jarvis)

1. **Core Differentiators:**
   - Three-tier routing (jarvis can't match frontier reasoning)
   - Cost tracking and budgets
   - Semantic classification intelligence
   - Research-backed architecture

2. **Quality Features:**
   - Latency engineering (<3s E2E)
   - Verification architecture
   - DAG parallel execution
   - Adaptive learning path

3. **Philosophy:**
   - Hardware-aware scaling (constraint → power)
   - Deep persona design (not just profiles)
   - Explicit latency masking

---

## 10. The Synthesis: Best of Both

### Proposed ATLAS 2.0 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              ATLAS 2.0: jarvis Features + R29 Intelligence       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  VOICE LAYER (Enhanced from jarvis)                             │
│  ├── Wake word: "ATLAS" (always listening)                      │
│  ├── Interrupt: "stop", "quiet", "wait"                         │
│  ├── Hot window: 30s follow-up mode                             │
│  ├── TTS: Kokoro + voice cloning option                         │
│  └── Latency masking: "Let me see..." (R29)                     │
│                                                                  │
│  INTELLIGENCE LAYER (ATLAS R29 - Superior)                      │
│  ├── Three-tier routing (Local/API/SDK)                         │
│  ├── Semantic classifier (regex + embeddings)                   │
│  ├── Cost tracking + budget management                          │
│  ├── Adaptive learning (LinUCB)                                 │
│  └── Circuit breakers + graceful degradation                    │
│                                                                  │
│  PERSONA LAYER (ATLAS + jarvis hybrid)                          │
│  ├── Core: "Lethal Gentleman" (always)                          │
│  ├── Profile: Developer (code tools, technical)                 │
│  ├── Profile: Business (calendar, email, professional)          │
│  └── Profile: Coach (health, motivation, personal)              │
│                                                                  │
│  MEMORY LAYER (Enhanced)                                        │
│  ├── SQLite + sqlite-vec + FTS5 (ATLAS)                         │
│  ├── Automatic keyword extraction (jarvis)                      │
│  ├── Time-range filtering (jarvis)                              │
│  ├── Hybrid RRF search (ATLAS)                                  │
│  └── Memory enrichment at query time (jarvis)                   │
│                                                                  │
│  INTEGRATION LAYER (jarvis patterns)                            │
│  ├── Home Assistant MCP (native)                                │
│  ├── Google Workspace MCP                                       │
│  ├── GitHub MCP                                                 │
│  ├── Garmin integration (ATLAS specific)                        │
│  └── Composio for 500+ services                                 │
│                                                                  │
│  TOOLS LAYER (Combined)                                         │
│  ├── Screenshot OCR (jarvis)                                    │
│  ├── Web search (privacy-respecting)                            │
│  ├── File operations                                            │
│  ├── Nutrition tracking (both have this)                        │
│  ├── Multi-step planning (jarvis pattern)                       │
│  └── DAG parallel execution (ATLAS R23)                         │
│                                                                  │
│  PRIVACY LAYER (jarvis patterns)                                │
│  ├── Hardened mode configuration                                │
│  ├── Sensitive data redaction                                   │
│  ├── Network verification scripts                               │
│  └── Data export/deletion tools                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Conclusion

### jarvis is Better At:
- Being usable right now
- MCP ecosystem breadth
- Voice features (interrupt, cloning)
- Privacy hardening
- Cross-platform support

### ATLAS is Better At:
- Intelligence architecture (routing, classification)
- Cost awareness and management
- Latency engineering
- Research-backed decisions
- Scaling path (constrained → powerful hardware)
- Deep persona design

### The Honest Assessment:

**If you need something working TODAY:** Use jarvis. It's functional, has good MCP integrations, and does 80% of what you want.

**If you're building for the LONG TERM:** ATLAS's architecture is more sophisticated. The three-tier routing, cost management, and adaptive learning create a system that optimizes over time.

**The Ideal Path:**
1. Install jarvis NOW to learn what works in practice
2. Continue building ATLAS with jarvis learnings incorporated
3. When ATLAS is ready, migrate - bringing the best of both

### Final Verdict

**Neither is "superior" - they're solving different problems:**

- **jarvis:** "Give me a working local AI assistant today"
- **ATLAS:** "Give me an optimized, cost-aware, research-backed AI system for the long term"

ATLAS should adopt jarvis's practical features (interrupt, voice cloning, MCP configs, privacy hardening) while keeping its core architectural advantages (routing intelligence, cost tracking, research depth).

---

## Sources

- [isair/jarvis GitHub](https://github.com/isair/jarvis)
- [ATLAS MASTER_PLAN](/home/squiz/ATLAS/docs/MASTER_PLAN.md)
- [ATLAS R29 Research](/home/squiz/ATLAS/docs/research/R29.LLM%20routing%20strategies%20for%20voice-first%20AI%20with%20three-tier%20architecture.md)
