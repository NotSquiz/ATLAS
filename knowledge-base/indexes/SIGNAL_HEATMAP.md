# Signal Heatmap

> Composite ranking of the most important items across all 17 knowledge base sources.

**Last updated:** January 31, 2026
**Items scored:** 38 (from 284 total extracted items)
**Sources covered:** S1-S17

---

## Scoring Formula

```
Signal = (R x 0.30) + (C x 0.25) + (Q x 0.25) + (V x 0.20)
```

| Dimension | Symbol | Weight | Scale | Scoring Guide |
|-----------|--------|--------|-------|---------------|
| **Relevance** | R | 0.30 | 0-10 | How directly applicable to ATLAS / Baby Brains. HIGH=8-10, MEDIUM=5-7, LOW=2-4 |
| **Confidence** | C | 0.25 | 0-10 | Evidence quality. Peer-reviewed=9-10, Practitioner=7-8, Inference=5-6, Anecdote=3-4, Hype=1-2 |
| **Credibility** | Q | 0.25 | 0-10 | Source credibility. S14=10, S16=9, S7=9, S6/S8/S13/S17/S2/S15=8, S1/S3/S4/S5/S11=7 |
| **Convergence** | V | 0.20 | 0-10 | Independent sources supporting. 1=2, 2=4, 3=6, 4+=8, 6+=10 |

**Security override:** SECURITY-tagged items with credible evidence floor at Signal 7.0 minimum.

---

## S-Tier (Signal 9.0+)

Items with the strongest evidence, highest relevance, and broadest convergence. Build decisions should rely on these.

| Rank | ID | Item | Signal | R | C | Q | V | Tags |
|------|-----|------|--------|---|---|---|---|------|
| 1 | S14.192 | **Hybrid planning works best** -- real systems combine ReAct + ReWOO + Plan-and-Execute. No single approach dominates. ATLAS already implements all three. | **9.45** | 10 | 10 | 10 | 8 | `ARCH` |
| 2 | S6.01 | **Passive context (100%) >> active retrieval (53%)** -- AGENTS.md always-present beats Skills on-demand. Agents skipped tools 56% of the time. | **9.20** | 10 | 9 | 8 | 8 | `ARCH` `MEMORY` |
| 3 | S14.195 | **ARTIST: fewer deliberate tool calls > frequent calls** -- validates 0-token architecture as academically optimal. Less LLM involvement = better for known workflows. | **9.20** | 10 | 10 | 10 | 6 | `TOOLS` `COST` |
| 4 | S14.205 | **MAGMA multi-graph memory** -- 4 orthogonal graphs (Temporal, Causal, Semantic, Entity). 0.700 vs flat 0.481 (46% improvement). 95% compression. | **9.20** | 10 | 10 | 10 | 6 | `MEMORY` |
| 5 | S13.01 | **Active exploitation of unsecured agents** -- Netflix, Spotify, bank accounts harvested from live Clawdbot instances. Not theoretical. | **9.15** | 10 | 9 | 8 | 8 | `SECURITY` |
| 6 | S17.263 | **Forgetting as a feature** -- FSRS-6 decay prevents context bloat. Without decay, RAG degrades at scale. Memory != Storage. | **9.10** | 10 | 9 | 8 | 8 | `MEMORY` |
| 7 | S16.254 | **Circuit breaker + fallback chains** -- Closed/Open/HalfOpen state machine prevents cascading failures. Category-specific fallbacks. | **9.05** | 10 | 9 | 9 | 8 | `ARCH` `SECURITY` |
| 8 | S14.201 | **Reflexion achieves 20-22% improvement** -- episodic memory of failures drives retry improvement. Validates our Wait pattern. | **9.05** | 10 | 10 | 10 | 6 | `AUTONOMY` |
| 9 | S2.01 | **Brain + Hands architecture** -- separate design/orchestration from execution, connect via MCP. Maps to ReWOO (S14). | **9.00** | 10 | 8 | 8 | 10 | `ARCH` |
| 10 | S17.266 | **Prediction error gating** -- detect conflicts before storing. CREATE/UPDATE/SUPERSEDE decisions prevent contradictory memories. | **9.00** | 10 | 9 | 8 | 8 | `MEMORY` `AUTONOMY` |

---

## A-Tier (7.5-8.9)

Strong evidence, high relevance. Should inform architecture and build priorities.

| Rank | ID | Item | Signal | R | C | Q | V | Tags |
|------|-----|------|--------|---|---|---|---|------|
| 11 | S3.01 | **Hybrid intelligence pattern** -- local model routes private data, cloud frontier handles heavy reasoning. Private data never leaves. | **8.90** | 10 | 8 | 7 | 10 | `ARCH` `SECURITY` |
| 12 | S16.246 | **Privacy tiers as routing constraint** -- standard/sensitive/strict levels determine which backends can process data. Auto-escalation on sensitive patterns. | **8.85** | 10 | 9 | 9 | 6 | `SECURITY` |
| 13 | S8.06 | **Async research = sweet spot** -- high-level delegation with synthesis output is the winning pattern. Not real-time back-and-forth. | **8.80** | 10 | 8 | 8 | 8 | `WORKFLOW` `AUTONOMY` |
| 14 | S14.206 | **MAGMA ablation: traversal policy > graph structure** -- HOW you query matters more than WHAT you store. Removing traversal dropped 0.700 to 0.637. | **8.80** | 9 | 10 | 10 | 6 | `MEMORY` |
| 15 | S8.03 | **Permission pushback lesson** -- agents request max permissions by default. Optimize for capability, not safety. Humans must constrain. | **8.75** | 10 | 8 | 8 | 8 | `SECURITY` `AUTONOMY` |
| 16 | S17.265 | **Dual strength memory model** -- retrievability (access speed) vs stability (decay rate) are independent. Frequently accessed = high retrievability. Core preferences = high stability. | **8.75** | 10 | 9 | 8 | 6 | `MEMORY` |
| 17 | S14.189 | **ReWOO: 80% token reduction** -- plan ALL steps upfront, execute separately. Our WorkoutRunner/RoutineRunner already implement this. | **8.70** | 10 | 10 | 10 | 4 | `ARCH` `COST` |
| 18 | S6.04 | **Compressed index (8KB) = full injection (40KB)** -- 80% context reduction with same 100% pass rate. Pipe-delimited index + file retrieval. | **8.55** | 10 | 9 | 8 | 6 | `MEMORY` `COST` |
| 19 | S13.07 | **Tailscale VPN mesh** -- private network for all access. Free personal tier. No public exposure of agent ports. | **8.50** | 10 | 8 | 8 | 6 | `SECURITY` `TOOLS` |
| 20 | S14.221 | **OWASP ASI08: cascading failures** -- single compromised agent poisoned 87% of downstream decisions in 4 hours. Deterministic routing resists this. | **8.50** | 9 | 9 | 10 | 6 | `SECURITY` |
| 21 | S17.268 | **Retroactive importance (synaptic tagging)** -- memories become important AFTER storage when recalled in high-leverage contexts. | **8.35** | 9 | 9 | 8 | 6 | `MEMORY` `AUTONOMY` |
| 22 | S16.253 | **Tool-level access control > prompt instructions** -- subagents declare allowed_tools list. Enforcement at tool level, not prompt level. | **8.35** | 9 | 9 | 9 | 6 | `SECURITY` `ARCH` |
| 23 | S14.203 | **Flat memory fails at scale** -- intertwined semantics and topology cause redundancy, degraded retrieval. Structured memory = upgrade path. | **8.30** | 9 | 10 | 10 | 4 | `MEMORY` |
| 24 | S8.07 | **LLMs cannot do temporal reasoning** -- calendar dates consistently wrong. Deterministic code for time/date operations. | **8.30** | 10 | 8 | 8 | 6 | `WORKFLOW` |
| 25 | S6.03 | **Retrieval-led reasoning over pre-training** -- instruct agents to prefer YOUR knowledge base over stale training data. | **8.15** | 10 | 9 | 8 | 4 | `ARCH` `MEMORY` |
| 26 | S15.229 | **Parallel work via git worktrees** -- 4-5 Claude Code instances simultaneously, each on a different feature. Clean isolation. | **8.10** | 10 | 8 | 8 | 4 | `WORKFLOW` `TOOLS` |
| 27 | S14.212 | **Five generic agent roles** -- Leader, Executor, Critic, Memory Keeper, Communication Facilitator. ATLAS V2 already maps to these. | **8.05** | 9 | 10 | 10 | 4 | `ARCH` |
| 28 | S16.247 | **Sensitive pattern auto-escalation** -- prompts with passwords, API keys, PEM markers auto-route to ZDR-only providers. | **8.05** | 9 | 9 | 9 | 4 | `SECURITY` |
| 29 | S7.02 | **MCP Apps: build once, deploy everywhere** -- open standard for interactive UI in AI conversations. Works across Claude, VS Code, etc. | **7.95** | 9 | 8 | 9 | 6 | `ARCH` `TOOLS` |
| 30 | S14.200 | **Three feedback types (complementary)** -- Reflective (self-critique), Parametric (RL/SFT), Validator-driven (external). Our Wait pattern = Reflective, QC hooks = Validator. | **7.95** | 9 | 10 | 10 | 4 | `AUTONOMY` |
| 31 | S17.267 | **Context-dependent retrieval** -- retrieval context should match encoding context. Separate mechanism from semantic search. | **7.80** | 9 | 9 | 8 | 4 | `MEMORY` |
| 32 | S13.15 | **Security before features** -- secure first, deploy second. Never the reverse. | **7.70** | 9 | 8 | 8 | 6 | `SECURITY` |
| 33 | S1.07 | **96% token reduction (qmd)** -- massive savings claim for batch processing. Needs investigation. | **7.60** | 9 | 6 | 7 | 8 | `COST` |
| 34 | S15.233 | **Single-trigger delegation ("PR")** -- collapse complex multi-step operations to single-word commands. Extreme friction reduction. | **7.55** | 9 | 8 | 8 | 4 | `WORKFLOW` `TOOLS` |

---

## B-Tier (5.5-7.4)

Noteworthy items with solid evidence but narrower applicability or fewer supporting sources.

| Rank | ID | Item | Signal | R | C | Q | V | Tags |
|------|-----|------|--------|---|---|---|---|------|
| 35 | S5.01 | **Memory flush before compaction** -- persist everything important before context window purge. Design principle: always persist before purge. | **7.40** | 9 | 7 | 7 | 6 | `MEMORY` |
| 36 | S9.13 | **Voice quality chain / STT is weakest link** -- entire experience depends on weakest link. Our STT is the bottleneck, not TTS. | **7.20** | 9 | 7 | 7 | 4 | `VOICE` `ARCH` |
| 37 | S14.211 | **RL requires 1%+ pre-training domain exposure** -- at 0%, RL completely fails to transfer. Sets realistic expectations for local model fine-tuning. | **7.15** | 7 | 10 | 10 | 2 | `AUTONOMY` `COST` |
| 38 | S10.08 | **Gartner: CISOs should block AI browser agents** -- autonomous browser access is highest-risk capability. Whitelist-only. | **7.00** | 7 | 7 | 6 | 8 | `SECURITY` |

---

## Scoring Notes

### Source Credibility (Q) Reference

| Score | Sources | Rationale |
|-------|---------|-----------|
| 10 | S14 | 800-paper academic survey, UIUC+Meta+Google DeepMind+Yale, #1 HuggingFace |
| 9 | S7, S16 | Anthropic official spec (S7), Bitcoin Core veteran + production Rust (S16) |
| 8 | S2, S6, S8, S13, S15, S17 | Practitioner evidence with specifics, Vercel engineering (S6), real exploit evidence (S13) |
| 7 | S1, S3, S4, S5, S9, S11, S12 | Community reports, mixed credibility, tool evaluations |
| 6 | S10 | Early-stage tools, landscape research from mixed outlets |

### Convergence (V) High Scorers

Items scoring V=8+ are supported by 4+ independent sources:

- **Hybrid model routing** (S1, S2, S3, S4, S14, S16) -- V=10. Six sources independently describe local+cloud hybrid pattern.
- **Brain + Hands / ReWOO** (S2, S14, S15, S16, S17) -- V=10. Separation of planning from execution appears everywhere.
- **Security before features** (S3, S8, S10, S13, S16) -- V=8. Five sources document agent security failures or hardening.
- **Async delegation wins** (S1, S3, S8, S15) -- V=8. Four sources document async as the winning agent workflow.
- **Passive context wins** (S6, S14, S17) -- combined with convergent evidence from MAGMA, ARTIST, and FSRS findings.
- **Forgetting/memory management** (S5, S14, S17) -- three independent sources (practitioner, academic survey, cognitive science implementation).

### Security Override Applied

The following items would have scored below 7.0 without the security floor but are elevated due to SECURITY tag + credible evidence:

- S10.08 (Gartner browser agent warning): Raw score 6.85, floored to 7.00

### Items Considered But Not Included

The following HIGH-relevance items were evaluated but did not make the top 38:

- S4.05 (Grok native X search) -- R=8, but lower convergence (unique capability, single source)
- S11.01 (Data > compute) -- Conceptual, low direct applicability despite being true
- S7.06 (MCP sandbox isolation) -- Important but specific to MCP Apps implementation
- S12.04 (Generic vs individual emulation) -- Conceptual background
- S9.01 (Typeless dictation) -- User productivity tool, not agent architecture

---

## How to Use This Heatmap

1. **Architecture decisions** -- S-Tier items are validated by multiple strong sources. Build with confidence.
2. **Priority ordering** -- Higher signal = higher priority when allocating development time.
3. **Risk assessment** -- SECURITY-tagged items in S/A-Tier represent non-negotiable requirements.
4. **Memory upgrade path** -- 6 of the top 38 items are MEMORY-tagged. Memory is the #1 upgrade area.
5. **Convergence as confidence** -- V=8+ items have independent validation. V=2 items may still be correct but need further evidence.
