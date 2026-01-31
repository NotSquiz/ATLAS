# S17: Vestige + FSRS-6 — Cognitive Memory System for Claude

**Source:** Reddit r/ClaudeAI post + https://github.com/samvallad33/vestige + https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
**Author:** samvallad33 (Vestige), open-spaced-repetition community (FSRS)
**Date:** January 2026 (Vestige v1.1.2, Jan 27, 2026)
**Type:** Open-source MCP server implementing cognitive science memory for Claude + the underlying spaced repetition algorithm
**Distinction:** This is the first implementation we've seen that treats **forgetting as a feature, not a bug**. Grounded in 130 years of memory research. 42,000 lines of Rust. 29 MCP tools. 100% local. The author's core insight: "We treat AI memory like a database, but human intelligence relies on forgetting. If you remembered every sandwich you ever ate, you wouldn't be able to remember your wedding day."

### The Problem Statement

> "Every conversation with Claude starts the same way: from zero. No matter how many hours you spend together, no matter how much context you build, the next session, it's gone. You're strangers again."

This is the same problem our `SessionBuffer` solves partially (5 exchanges, 10-min TTL) and our `semantic_memory` table attempts to solve (persistent but flat). Vestige solves it with cognitive science.

### Core Architecture: Four Cognitive Principles

**1. FSRS-6 Spaced Repetition** (from Anki, 100M+ users)
Each memory has a **stability score** calculated by the FSRS-6 algorithm (21 parameters). Unused memories naturally decay into "Dormant" state, keeping context windows clean. Key formulas:
- Retrievability: R(t,S) = (1 + factor·t/S)^(-w₂₀) where factor ensures R(S,S) = 0.9
- Stability after recall: S'(S,G) = S·e^(w₁₇·(G-3+w₁₈))·S^(-w₁₉)
- Post-lapse: S'f = w₁₁·D^(-w₁₂)·((S+1)^w₁₃-1)·e^(w₁₄·(1-R))
- Stability increases faster when small, slower when large (logarithmic convergence)

**2. Dual Strength Memory Model** (Bjork Lab, UCLA)
Two independent strength values per memory:
- **Retrievability strength**: How easily a memory surfaces during retrieval. Updated on every recall.
- **Stability strength**: How slowly the memory decays. Stable memories persist; unstable ones fade fast.
When you recall a memory, it physically strengthens (updates retrieval strength in SQLite). Active projects stay "hot."

**3. Prediction Error Gating** ("Titans" Mechanism)
When you try to save something that **conflicts** with an existing memory, Vestige detects the "surprise." It doesn't create a duplicate — it decides: CREATE (new info), UPDATE (refinement), or SUPERSEDE (correction). The system effectively learns from its mistakes.

**4. Context-Dependent Retrieval** (Tulving's Encoding Specificity Principle, 1973)
Memories are easier to recall when the retrieval context matches the encoding context. `match_context` is a separate tool from `semantic_search` because they implement different cognitive mechanisms.

### Plus: Synaptic Tagging & Capture (Retroactive Importance)
Pure CS systems require correct tagging at ingestion time. Vestige allows memories to become important **retroactively** — a trivial memory recalled during a high-leverage moment gets promoted. This is the `trigger_importance` tool.

### Extracted Items

#### A. Core Memory Architecture

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 263 | **Forgetting as a feature**: FSRS-6 decay prevents context bloat. Without decay, RAG "falls off a cliff" as dataset grows — high recall but low precision. Memory ≠ Storage | `MEMORY` | HIGH | Reframes our entire memory approach. Our `semantic_memory` has infinite retention = will drown in noise over time |
| 264 | **FSRS-6 algorithm** (21 parameters): Stability, Difficulty, Retrievability model. Stability after recall grows logarithmically (fast when small, slow when large). Most efficient known algorithm for predicting retrieval probability | `MEMORY` | HIGH | Battle-tested by 100M+ Anki users. Not experimental — production-grade spaced repetition |
| 265 | **Dual Strength Model** (Bjork Lab): Retrievability (access speed) vs Stability (decay rate) are independent dimensions. Recalled memories strengthen retrievability; time strengthens stability | `MEMORY` | HIGH | Maps to our need: frequently accessed health data = high retrievability. Core preferences = high stability |
| 266 | **Prediction Error Gating**: Detect conflicts between new and existing memories. Decide CREATE/UPDATE/SUPERSEDE rather than blindly appending. Prevents duplicate/contradictory memories | `MEMORY`, `AUTONOMY` | HIGH | Our `semantic_memory` just appends. No conflict detection. "Use async reqwest" today, "blocking is fine" tomorrow = both persist |
| 267 | **Context-Dependent Retrieval** (Tulving 1973): Retrieval context should match encoding context. Separate mechanism from semantic similarity search | `MEMORY` | HIGH | Our memory retrieval is context-unaware. What you were doing when you stored the memory matters for recall |
| 268 | **Synaptic Tagging — Retroactive Importance**: Memories can become important AFTER storage. A trivial memory recalled during a high-leverage moment gets promoted automatically | `MEMORY`, `AUTONOMY` | HIGH | No existing system we've seen does this. Memories aren't just tagged at write-time — their importance evolves |

#### B. Implementation & Integration

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 269 | **29 MCP tools across 5 subsystems**: Core memory (FSRS-6), Neuroscience layer (synaptic tagging, states, context matching), Codebase memory (project patterns), Prospective memory (future intentions), Feedback/maintenance | `TOOLS`, `MEMORY` | HIGH | Each tool maps to a distinct cognitive principle — not arbitrary features. Can't collapse to fewer without losing capabilities |
| 270 | **smart_ingest vs ingest**: `smart_ingest` uses Prediction Error Gating to detect duplicates/conflicts before storage. `ingest` is simple append. Two different operations for two different needs | `MEMORY`, `TOOLS` | HIGH | We need both: smart capture for thoughts (detect conflicts) and simple append for raw data (pain logs, assessments) |
| 271 | **promote_memory / demote_memory**: Bidirectional feedback — user can strengthen helpful memories or weaken incorrect ones. Agent doesn't decide alone what to keep | `MEMORY`, `UX` | HIGH | Human-in-the-loop memory management. Aligns with S8 Pattern 21 (humans optimize safety) — applied to memory |
| 272 | **Memory states (Active → Dormant)**: FSRS-6 calculates when memories cross retrieval threshold. Dormant memories still exist but don't pollute context window | `MEMORY` | HIGH | Clean solution to context window management. Our SessionBuffer just deletes after 10 min. Vestige lets memories sleep |
| 273 | **100% local**: Rust + SQLite + FastEmbed (nomic-embed-text-v1.5, ~130MB). No cloud dependencies after initial setup. Embeddings generated locally via MCP server | `SECURITY`, `COST` | HIGH | Aligns with S3 (data sovereignty), S13 (security), S16 (privacy routing). Memory should be local |
| 274 | **3-4K token overhead**: Tool definitions add one-time cost per conversation, not per message. Queries return only relevant memories (few hundred tokens), not entire memory store | `COST` | MEDIUM | Manageable cost. Retrieval is on-demand, not dumped into every context |

#### C. Why Forgetting Matters (Author's Arguments)

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 275 | **"Storage vs Memory"**: Vector DB = infinite retention = 500 irrelevant 3-year-old chunks matching keywords. Memory = decay + precision. High recall ≠ high precision | `MEMORY` | HIGH | Strongest argument for FSRS over flat storage. Our semantic_memory will hit this wall as it grows |
| 276 | **"Limited Context Window = biological memory constraint"**: LLMs face the same problem brains evolved to solve — limited attention, must prioritize what to surface. Forgetting is the solution, not the problem | `MEMORY`, `ARCH` | HIGH | Reframes context window limitations as a design opportunity, not a limitation |
| 277 | **RAG degrades with scale**: Without decay, RAG performance falls off a cliff after ~10,000 interactions. Stale memories crowd out fresh ones. Author challenges anyone to benchmark this | `MEMORY` | HIGH | Quantified prediction: RAG fails at scale without forgetting. Our semantic_memory will face this |
| 278 | **Retroactive importance vs upfront tagging**: Pure CS systems require correct tags at ingestion. Real memory lets importance emerge over time — trivial memory becomes critical when recalled in high-leverage context | `MEMORY` | HIGH | Fundamentally different from our ThoughtClassifier which tags once at ingestion |

#### D. MCP Architecture Arguments

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 279 | **MCP > CLI for cognitive tools**: Structured JSON schemas eliminate "hallucinated syntax" errors. Client caches tool definitions. Works in Claude Desktop, Zed, Cursor, any MCP-compatible environment | `TOOLS`, `ARCH` | HIGH | Validates S7 (MCP as universal protocol). Vestige works everywhere MCP works |
| 280 | **Spreading Activation**: Retrieval activates semantically related memories and tags them based on relevance. Context-aware recall without exhaustive search | `MEMORY` | MEDIUM | Graph-like memory traversal similar to MAGMA (S14 #205). Related memories surface together |
| 281 | **Five cognitive subsystems, not arbitrary tools**: Core memory, Neuroscience layer, Codebase memory, Prospective memory (future intentions), Feedback/maintenance. Each tool maps to a cognitive principle | `MEMORY`, `ARCH` | HIGH | Clean architecture: subsystems based on cognitive science, not engineering convenience |
| 282 | **Prospective memory (intentions)**: The `intention` tool sets reminders and future triggers. Not just remembering the past — remembering things you NEED to do | `MEMORY`, `WORKFLOW` | HIGH | Our ThoughtClassifier captures "remember to..." but doesn't have a trigger mechanism for when to surface it |
| 283 | **FSRS mean reversion prevents "ease hell"**: Difficulty converges toward target, preventing memories from getting stuck in "too hard" or "too easy" states | `MEMORY` | MEDIUM | Technical detail but important — prevents memory system from locking into wrong states |
| 284 | **Trainable forgetting curve**: FSRS-6 decay exponent is optimized through parameter learning, not fixed. Adapts to actual usage patterns | `MEMORY`, `AUTONOMY` | MEDIUM | The forgetting rate itself adapts. Personalized memory decay per user |

### Key Patterns from S17

**Pattern 46: Forgetting is the Feature (Memory ≠ Storage)**
The fundamental insight: AI memory systems that never forget become LESS useful over time, not more. Vector DBs with infinite retention drown in their own history. FSRS-6 spaced repetition decay ensures only relevant memories surface. The context window constraint LLMs face is the same constraint biological memory evolved to solve. Forgetting IS the solution.

**Pattern 47: Dual Strength Memory (Retrievability ≠ Stability)**
Two independent dimensions per memory: how easily it surfaces (retrievability, updated on every access) and how slowly it decays (stability, grows with time). Active project context stays hot via frequent retrieval. Core preferences persist via high stability. This maps to ATLAS needs: health data accessed daily = high retrievability; user preferences = high stability; one-off thoughts = low both.

**Pattern 48: Prediction Error Gating (Conflict Detection Before Storage)**
Don't blindly append to memory. Detect when new information conflicts with existing memories. Decide CREATE/UPDATE/SUPERSEDE. This prevents the "two contradictory preferences" problem that flat memory systems accumulate. Our `semantic_memory` has no conflict detection — it just appends.

**Pattern 49: Retroactive Importance (Memories Get More Important Over Time)**
Traditional systems require correct importance tagging at write-time. Synaptic Tagging allows importance to emerge retroactively — a trivial memory becomes critical when recalled during a high-leverage moment. This is fundamentally different from ThoughtClassifier's one-time categorization.

### Cross-References

| S17 Item | Connects To | Relationship |
|----------|-------------|-------------|
| Forgetting as feature (#263) | S14 Pattern 35 (flat → structured memory) | FSRS decay IS the structured memory upgrade the survey recommends |
| FSRS-6 (#264) | S14 #205 (MAGMA multi-graph) | Both solve "what to surface?" — FSRS via decay, MAGMA via traversal |
| Dual strength (#265) | S14 #207 (MemAgent — memory as action) | Both treat memory as active, not passive. Vestige auto-updates strength on recall |
| Prediction error gating (#266) | S14 #222 (memory pollution prevention) | Direct solution to the survey's identified challenge of memory contamination |
| Context-dependent retrieval (#267) | S6 Pattern 14 (passive context wins) | Context matching at retrieval = better passive context delivery |
| Retroactive importance (#268) | S14 #206 (traversal > structure) | Importance as emergent property, not pre-assigned tag. Similar insight: HOW you query > WHAT you store |
| 100% local (#273) | S3 Pattern 10 (data sovereignty), S16 Pattern 42 (privacy routing) | Memory data is the most private data. Must be local |
| MCP tools (#269) | S7 Pattern 17 (MCP protocol layer) | Vestige proves MCP works for complex cognitive architectures, not just simple tools |
| Smart ingest (#270) | S16 #253 (subagent restrictions) | Both implement intelligent gating before operations execute |
| Promote/demote (#271) | S8 Pattern 21 (humans optimize safety) | Human-in-the-loop applied to memory quality |
| Memory states (#272) | S5 (memory flush before compaction) | Both manage memory lifecycle. Vestige does it algorithmically; S5 does it manually |
| Prospective memory (#282) | S14 #219 (personalization challenge) | Future intention triggers = proactive personalization |
| RAG degrades with scale (#277) | S14 #203 (flat memory fails at scale) | Same diagnosis from practitioner (Vestige) and academia (MAGMA survey) |

### Action Items from S17

| Priority | Action | Rationale |
|----------|--------|-----------|
| **HIGH** | Evaluate Vestige as drop-in memory layer for ATLAS | 29 MCP tools, 100% local, handles everything our semantic_memory doesn't. Could replace our flat memory entirely |
| **HIGH** | Implement FSRS-6 decay for `semantic_memory` regardless of Vestige adoption | Pattern 46: Our memory will drown in noise without forgetting. FSRS-6 is the most proven decay algorithm |
| **HIGH** | Add prediction error gating to ThoughtClassifier | Pattern 48: Detect conflicts before appending. "Use async" and "use blocking" can't both persist as preferences |
| **HIGH** | Design dual-strength scoring for memory entries | Pattern 47: Separate "how often accessed" from "how important long-term" |
| **MEDIUM** | Implement prospective memory (future triggers) | Item #282: "Remember to..." should surface at the right TIME, not just on search |
| **MEDIUM** | Add retroactive importance to captured thoughts | Pattern 49: Thoughts recalled during high-leverage moments should get promoted automatically |
| **MEDIUM** | Benchmark our semantic_memory at scale | Item #277: Test what happens when we have 10,000+ entries. Does retrieval degrade? |
| **LOW** | Study FSRS-6 parameter tuning for ATLAS-specific memory patterns | Item #284: Trainable decay rates could adapt to our health/project/admin memory differently |

### Credibility Assessment

**Source Quality: 8/10**
Open-source (MIT/Apache-2.0), 42K lines of Rust, 211 GitHub stars, active development (v1.1.2 as of Jan 27). Author is articulate about the science and honest about tradeoffs. FSRS-6 algorithm itself is battle-tested by 100M+ Anki users. The cognitive science foundations (Bjork Lab, Tulving 1973) are well-established research, not speculation.

**Strengths:**
- Grounded in proven cognitive science (not made-up "AI memory" hype)
- FSRS-6 is the most battle-tested spaced repetition algorithm (100M+ Anki users)
- 100% local, Rust implementation (performance + memory safety)
- MCP integration means it works with any MCP-compatible tool
- Author demonstrates deep understanding of WHY each design decision (see discussion comments)
- "Storage vs Memory" distinction is the clearest framing of the flat memory problem we've seen
- Prediction error gating solves a real problem (contradictory memories) that no other source has addressed

**Weaknesses:**
- Relatively new project (211 stars, 50 commits) — not yet battle-tested at scale
- 29 MCP tools may be too many for some workflows (3-4K token overhead)
- No benchmarks published yet (author acknowledges this, invites comparison)
- Rust implementation harder to modify than Python for our stack
- Embedding model (FastEmbed, nomic-embed-text-v1.5) may not be optimal for all use cases
- No multi-user support — single-user cognitive architecture

**Overall:** The most important memory architecture source in this knowledge base. While S14 identified flat→structured memory as the key upgrade (Pattern 35, 46% improvement), Vestige provides a concrete implementation grounded in cognitive science. The core insight — that forgetting is the feature, not the bug — reframes our entire memory strategy. FSRS-6 decay solves the context window bloat problem. Prediction error gating solves the contradictory memory problem. Dual strength solves the "what to surface" problem. Whether we adopt Vestige directly or implement these principles in Python, the cognitive architecture should inform our memory upgrade.

---

*S17 processed: January 30, 2026*
*Running total: 284 items extracted across 17 sources, 49 patterns identified*

---
---
