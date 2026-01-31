# S14: Agentic Reasoning for Large Language Models — Full Survey Deep Dive

**Source:** arXiv:2601.12538 + GitHub `weitianxin/Awesome-Agentic-Reasoning`
**Authors:** Tianxin Wei + 28 co-authors (UIUC, Meta, Amazon, Google DeepMind, UCSD, Yale)
**Date:** January 18, 2026
**Scope:** 135-page survey reviewing ~800 papers
**Distinction:** #1 Paper of the Day on HuggingFace (182 upvotes). Highest-credibility source in this knowledge base.
**Processing:** Full paper synthesis via 3 parallel Opus agents — framework analysis, section-by-section findings, and ATLAS-specific practical mapping.

### Paper's Core Thesis

> "Agentic reasoning marks a paradigm shift by reframing LLMs as autonomous agents that plan, act, and learn through continual interaction."

The paper reframes LLMs **from passive sequence predictors to autonomous entities** capable of planning, tool use, and adaptive learning via continual environment interaction. The central message: agentic reasoning is not merely about better prompting or better training — it is about the **closed loop** between thought and action.

### The Three-Layer Framework (Detailed)

Formalized as a **Partially Observable Markov Decision Process (POMDP)** with dual policies — one for internal reasoning, one for action execution. Agents don't observe full environment state; they construct internal representations from interaction histories.

| Layer | Environment | Purpose | Our Phases |
|-------|-------------|---------|------------|
| **Foundational** | Stable | Single-agent core: planning, tool use, search | Phases 1-2 |
| **Self-Evolving** | Dynamic | Improvement via feedback, memory, adaptation | Phases 3-4 |
| **Collective** | Collaborative | Multi-agent coordination, knowledge sharing | Phase 5+ |

Cross-cutting: **In-Context** (test-time, prompt-based, no weight changes) vs **Post-Training** (RL/SFT, permanent capability improvement).

### Extracted Items

#### A. Foundational Layer — Planning

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 185 | **Three-layer framework**: Foundational → Self-Evolving → Collective, formalized as POMDP with dual policies | `ARCH` | HIGH | Our architectural north star. Maps directly to ATLAS build phases |
| 186 | **Two optimization paradigms**: In-Context (test-time scaling) vs Post-Training (RL/SFT) | `ARCH`, `COST` | HIGH | We operate in-context (can't fine-tune Claude). Local Qwen could use post-training |
| 187 | **Five planning subcategories**: Workflow design, tree search, process formalization, decomposition, external aid | `ARCH`, `AUTONOMY` | HIGH | Survey's taxonomy for all planning approaches |
| 188 | **ReAct** (ICLR 2023): Interleave think → act → observe in continuous loop. Dominant paradigm for interactive tasks | `ARCH` | HIGH | Our Haiku fallback + SessionBuffer is simplified ReAct. Best for exploratory/unknown tasks |
| 189 | **ReWOO**: Plan ALL steps upfront, then execute separately. ~80% token reduction vs ReAct on structured tasks | `ARCH`, `COST` | HIGH | Our WorkoutRunner, RoutineRunner, AssessmentRunner already DO this — plan full sequence, execute without re-consulting LLM |
| 190 | **Plan-and-Execute**: Create plan, execute steps, replan if needed. 92% task accuracy vs ReAct's 85% at ~50% more tokens | `ARCH` | HIGH | Our 7-stage activity pipeline with stage caching on retry IS textbook Plan-and-Execute with replanning |
| 191 | **Tree of Thoughts** (NeurIPS 2023): Branch exploration + backtracking. Dramatically improves problems requiring backtracking | `ARCH`, `AUTONOMY` | LOW | Overkill for personal assistant. Only relevant for complex Baby Brains strategic decisions |
| 192 | **Hybrid planning works best**: No single approach dominates. Real systems combine ReAct + ReWOO + Plan-and-Execute | `ARCH` | HIGH | **We already do this without knowing it.** 0-token = no planning, structured workflows = ReWOO, activity pipeline = Plan-and-Execute, general queries = ReAct |
| 193 | **Decomposition is essential for long-horizon tasks**: Hierarchical subgoal generation → solve individually | `ARCH` | HIGH | Validates our 7-stage pipeline decomposition and skill progressive loading |

#### B. Foundational Layer — Tool Use

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 194 | **Tool use progression**: Prompt-based → SFT bootstrapping → RL mastery → Orchestration frameworks | `TOOLS`, `ARCH` | HIGH | Maps the full maturity path. We're at orchestration level (IntentDispatcher, BridgeFileServer) |
| 195 | **ARTIST finding**: Fewer deliberate tool calls outperform frequent calls or verbose self-reasoning | `TOOLS`, `COST` | HIGH | **Validates our 0-token approach.** The LESS you call the LLM for predictable workflows, the better |
| 196 | **Agents as tool CREATORS**: LLMs now generate new tools, not just use predefined ones | `TOOLS`, `AUTONOMY` | MEDIUM | Phase 4+ potential. Agent could create new voice intents or health tracking tools |
| 197 | **Context-aware tool selection > exhaustive tool lists**: Optimizing which tools are presented matters more than having all tools available | `TOOLS` | HIGH | Our intent priority ordering (23 levels) is exactly this — contextual selection, not exhaustive matching |

#### C. Foundational Layer — Agentic Search

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 198 | **Static RAG → Decision-aware adaptive retrieval**: Agent decides WHEN and WHAT to retrieve based on current reasoning state | `MEMORY`, `TOOLS` | HIGH | Shift from "search once, generate once" to active, iterative information seeking |
| 199 | **Self-RAG / FLARE**: Agent autonomously decides during reasoning whether it needs more information, then retrieves | `MEMORY` | MEDIUM | Our Perplexica investigation (S3) aligns. Agent should know when it doesn't know enough |

#### D. Self-Evolving Layer — Feedback

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 200 | **Three feedback types** (complementary, not competing): Reflective (self-critique at inference), Parametric (SFT/RL baking patterns into weights), Validator-driven (external signals) | `AUTONOMY` | HIGH | Our Wait pattern = Reflective. QC hooks = Validator-driven. Parametric requires local model fine-tuning |
| 201 | **Reflexion achieves 20% improvement on HotPotQA, 22% on ALFWorld** via episodic memory of failures | `AUTONOMY` | HIGH | Academic validation + quantified improvement. Our Wait pattern retry IS Reflexion |
| 202 | **Closed feedback loop is key**: Feedback → memory → action → new feedback. Agent DRIVES which feedback it seeks | `AUTONOMY` | HIGH | Our activity pipeline does this: audit → identify weakness → Wait reflection → retry. The loop is the value, not any single component |

#### E. Self-Evolving Layer — Memory

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 203 | **Flat memory fails at scale**: Intertwines semantics with topology → redundant representations, unstructured retrieval, degraded accuracy as context grows | `MEMORY` | HIGH | Direct diagnosis of our `semantic_memory` table's limitations |
| 204 | **Structured memory taxonomy**: Architecture (hierarchical vs flat), Content (semantic vs procedural), Topology (centralized vs decentralized), Management (summarization, filtering, RL-driven adaptation) | `MEMORY` | HIGH | Framework for designing our memory upgrade |
| 205 | **MAGMA multi-graph memory** (Jan 2026): Four orthogonal graphs — Temporal, Causal, Semantic, Entity. Scores 0.700 vs flat-context 0.481 | `MEMORY` | HIGH | State of the art. 46% improvement over flat memory. 95% compression ratio |
| 206 | **MAGMA ablation: Traversal policy > graph structure** — removing traversal policy had biggest impact (0.700 → 0.637). HOW you query matters more than WHAT you store | `MEMORY` | HIGH | Critical insight. Don't over-engineer the schema — invest in query/traversal logic instead |
| 207 | **MemAgent / Memory-R1 / Mem-as-Action**: Memory operations (write, retrieve, forget) as explicit agent ACTIONS, not passive storage | `MEMORY`, `AUTONOMY` | HIGH | Agent decides what to remember and what to forget. RL-optimized memory management |
| 208 | **MemGPT**: OS-inspired tiered architecture — "RAM" (main context) vs "disk" (external storage) with agent-controlled paging | `MEMORY` | MEDIUM | Architecture pattern: hot context window + cold long-term store with intelligent swapping |
| 209 | **Zep dual-storage pattern**: Store raw episodic data AND derived semantic entities separately, cross-linked. Mirrors human memory | `MEMORY` | HIGH | Our `semantic_memory` = raw episodic. Our domain tables (assessments, pain_log) = derived. We're halfway to Zep without knowing it |

#### F. Self-Evolving Layer — Capability Evolution

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 210 | **Three evolution axes**: Self-evolving planning (self-generated curricula), self-evolving tool use (tool creation), self-evolving search (adaptive retrieval) | `AUTONOMY` | MEDIUM | Phase 4 roadmap. Agent creates its own training scenarios and new tools |
| 211 | **RL yields genuine extrapolative gains ONLY when pre-training had ≥1% exposure to the domain** (Raschka 2025-2026). At 0%, RL completely fails to transfer | `AUTONOMY`, `COST` | HIGH | RL doesn't create new reasoning — it improves sampling of existing capabilities. Sets realistic expectations for local model fine-tuning |

#### G. Collective Layer — Multi-Agent

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 212 | **Five generic agent roles**: Leader/Manager (orchestrates), Executor (performs), Critic/Evaluator (validates), Memory Keeper (state), Communication Facilitator (routes) | `ARCH` | HIGH | Our ATLAS V2 already maps: ConfidenceRouter=Leader, SkillLoader=Executor, HookRunner=Critic, SessionManager=MemoryKeeper, BridgeFileServer=Facilitator |
| 213 | **Manager-Executor-Supervisor structure**: Manager decomposes, executors work, supervisor validates. Creates built-in quality loop | `ARCH` | HIGH | Our activity pipeline: planner decomposes → agent converts → QC/audit validates. Pattern confirmed |
| 214 | **Sparse communication topologies ≈ fully connected** at lower cost. Pruning redundant communication edges doesn't hurt performance | `ARCH`, `COST` | MEDIUM | When we build multi-agent systems, don't over-connect. Targeted communication > broadcast |
| 215 | **Manual → Learned topology progression**: Start with fixed pipelines, evolve to adaptive coordination. GPTSwarm explores graph-structured agent teams with iterative refinement | `ARCH` | MEDIUM | Validates our approach: start with fixed cascading pipelines (activity conversion), evolve later |
| 216 | **Multi-Agent Debate (MAD)**: Agents deliberate, revise low-quality responses, reduce hallucinations. But breaks down when agents have similar capabilities → need role differentiation | `ARCH` | MEDIUM | If we deploy multiple agents, they need distinct roles/perspectives, not clones debating |

#### H. Applications & Validation

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 217 | **Healthcare validated as agentic domain**: Diagnostic reasoning + tool access + safety constraints + multi-agent specialist consultation | `BUSINESS` | HIGH | Our health tracking (Traffic Light, GATE, assessments) is a real-world instance of healthcare agentic reasoning |
| 218 | **"Vibe Coding"**: Agents handle syntax while humans focus on high-level intent. Agents improve through execution feedback | `TOOLS` | MEDIUM | Describes how we already use Claude Code. Agent reasons about implementation, human reasons about purpose |

#### I. Future Challenges & Gaps

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 219 | **Six open challenges**: (1) Personalization, (2) Long-horizon interaction, (3) World modeling, (4) Scalable multi-agent training, (5) Latent reasoning, (6) Governance/safety | `ARCH` | HIGH | Our roadmap should address 1 (memory upgrade), 2 (session persistence beyond 10-min TTL), 3 (proactive intent prediction), 6 (sandbox configs + security rules) |
| 220 | **Long-horizon credit assignment is unsolved**: Error accumulates over multi-step chains without mitigation. Agents must maintain coherence over hundreds of steps | `ARCH`, `AUTONOMY` | HIGH | Directly relevant to our activity pipeline (7 stages) and workout programs (weeks of tracking). Our stage caching + Wait pattern are mitigations |
| 221 | **OWASP ASI08 — Cascading Failures** (Dec 2025): Official category. "A single compromised agent poisoned 87% of downstream decisions within 4 hours" in simulation | `SECURITY` | HIGH | Our regex-based intent dispatch is MORE robust than LLM-based routing against cascading failures — deterministic routing prevents cascade propagation |
| 222 | **Memory pollution prevention**: Hallucinated entries, redundancy, drift. Need learnable write/retrieve/forget objectives | `MEMORY`, `SECURITY` | HIGH | Our ThoughtClassifier could re-classify stored thoughts periodically to detect drift and contamination |

#### J. ATLAS Architecture Validation

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 223 | **ATLAS already implements ReWOO**: WorkoutRunner, RoutineRunner, AssessmentRunner all plan full sequences upfront and execute without re-consulting LLM | `ARCH` | HIGH | We built the pattern before learning the name. Academic validation of our design |
| 224 | **ATLAS already implements ReAct**: Haiku fallback + SessionBuffer context is simplified ReAct (reason with context → act → observe response → continue) | `ARCH` | HIGH | Our general query path is ReAct |
| 225 | **ATLAS already implements Plan-and-Execute**: 7-stage activity pipeline with stage caching on retry = Plan-and-Execute with replanning | `ARCH` | HIGH | Activity pipeline is textbook Plan-and-Execute |
| 226 | **ATLAS 0-token intents are academically optimal**: ARTIST finding confirms fewer deliberate tool calls > frequent calls. Our 0-token bypass is the most efficient pattern possible | `COST` | HIGH | Our most distinctive feature (0-token voice responses) is validated as optimal by the survey ecosystem |
| 227 | **ATLAS maps to CTDE pattern** (Centralized Training, Decentralized Execution): Centralized config files (`config/`) + decentralized runners (each service runs independently) | `ARCH` | MEDIUM | Multi-agent architecture pattern — we do this at the config level |
| 228 | **In-context reasoning is correct for ATLAS**: Can't fine-tune Claude. Post-training only applicable to local Qwen. Our "training" IS configuration (phase configs, exercise libraries, intent patterns, form guides) | `ARCH`, `COST` | HIGH | Confirms our strategic choice. Configuration-as-training is our in-context approach |

### Key Patterns from S14

**Pattern 31: Three-Layer Agent Architecture (Foundation → Evolution → Collective)**
Academic consensus maps agent development: (1) basic single-agent reasoning, (2) self-improvement through feedback/memory, (3) multi-agent coordination. ATLAS phases mirror this. The framework is formalized as POMDP with dual policies for reasoning and action.

**Pattern 32: Hybrid Planning is the Answer (ReAct + ReWOO + Plan-and-Execute)**
No single planning approach dominates. The survey concludes real systems combine approaches. ATLAS already does this naturally: 0-token (no planning needed), ReWOO (structured workflows), Plan-and-Execute (activity pipeline), ReAct (general queries). Our intent dispatcher IS a planning router.

**Pattern 33: Decoupling Planning from Execution (ReWOO) Saves 80% Tokens**
Plan first, execute separately. ReWOO achieves ~80% token reduction vs ReAct on structured tasks (2,000 vs 9,795 tokens on HotpotQA). Reinforces Pattern 6 ("Brain + Hands"). Our workout/routine/assessment runners are ReWOO implementations.

**Pattern 34: Reflexion = Our Wait Pattern (Quantified)**
Reflexion (verbal reinforcement learning — reflect on failure, retry with lessons) achieves 20% improvement on HotPotQA, 22% on ALFWorld. Our activity conversion Wait pattern independently implements this approach. Academic validation with measured improvement.

**Pattern 35: Flat Memory → Structured Memory is the Evolution Path (46% improvement)**
MAGMA shows structured memory scores 0.700 vs flat 0.481 (46% improvement). But the ablation shows **traversal policy matters more than graph structure** (0.700 → 0.637 without it). Don't over-engineer the schema — invest in query logic. Our `semantic_memory` is flat; adding temporal + entity linking is the highest-impact upgrade.

**Pattern 36: Fewer Deliberate Tool Calls > Frequent Calls (ARTIST)**
ARTIST finding validates our 0-token architecture. The less you call the LLM for predictable workflows, the better. Our most distinctive feature (23-priority 0-token intent matching) is academically optimal.

**Pattern 37: Memory Operations Should Be Agent Actions (Write/Retrieve/Forget)**
MemAgent, Memory-R1, and Mem-as-Action formalize memory as explicit agent actions, not passive storage. The agent should decide what to remember and what to forget. Our ThoughtClassifier routes incoming thoughts (write) but doesn't yet handle retrieval optimization or active forgetting.

**Pattern 38: Cascading Failures are the Multi-Agent Threat (OWASP ASI08)**
A single compromised agent poisoned 87% of downstream decisions within 4 hours. Deterministic routing (our regex intent dispatch) is MORE robust than LLM-based routing against cascading failures. Our architecture accidentally provides cascade protection.

### Cross-References

| S14 Item | Connects To | Relationship |
|----------|-------------|-------------|
| Three-layer framework (#185) | S1 Pattern 1 (Agent-as-Manager) | Foundational layer = manager pattern |
| ReWOO (#189) | S2 Pattern 6 (Brain + Hands) | Same concept, academic name. 80% token savings quantified |
| Hybrid planning (#192) | S4 Role Allocation Framework | Each model layer uses different planning approach |
| ARTIST fewer calls (#195) | S6 Pattern 14 (Passive context wins) | Both validate: less LLM involvement = better for known workflows |
| Reflexion (#201) | Activity pipeline Wait pattern | Our implementation predates our awareness of the paper. 20-22% improvement quantified |
| Tool-use progression (#194) | S7 MCP standard | MCP = the orchestration-tier tool protocol |
| Flat memory fails (#203) | S5 memory flush, S6 passive context | Flat vs structured maps to our memory architecture decisions |
| MAGMA multi-graph (#205) | S3 Pattern 10 (Data sovereignty) | Structured memory on local hardware = private knowledge graph |
| Zep dual-storage (#209) | Our semantic_memory + domain tables | We're halfway to the pattern already |
| Five generic roles (#212) | S1 Pattern 4 (Isolation), S2 Pattern 6 | Academic framework for what Moltbot community builds informally |
| Feedback types (#200) | S8 Pattern 21 (humans optimize safety) | Self-evolution feedback must be constrained — permission creep |
| OWASP ASI08 (#221) | S13 Pattern 28 (Security before features) | Cascading failures = new security category for agent systems |
| Long-horizon challenge (#220) | Our WorkoutScheduler (weeks of tracking) | We already face this challenge at small scale |
| In-context correct (#228) | S6 Pattern 14 (passive context wins) | Prompt engineering > training for API-based systems |
| Healthcare validated (#217) | Our Traffic Light + GATE system | Academic validation of our health domain approach |

### Action Items from S14

| Priority | Action | Rationale |
|----------|--------|-----------|
| **HIGH** | Add temporal backbone to `semantic_memory` — `previous_thought_id` and `related_thought_ids` columns | MAGMA ablation: traversal > structure. Temporal linking is highest-impact single improvement |
| **HIGH** | Implement entity linking via ThoughtClassifier taxonomy — make categories graph-queryable | Pattern 35: flat → structured memory. ThoughtClassifier already provides the entity backbone |
| **HIGH** | Document our hybrid planning architecture formally | Pattern 32: We already implement ReWOO + ReAct + Plan-and-Execute. Formalizing prevents accidental regression |
| **HIGH** | Add periodic memory quality audit — re-classify stored thoughts to detect drift | Item #222: Memory pollution prevention. ThoughtClassifier can audit existing entries |
| **MEDIUM** | Read MAGMA paper for memory upgrade specifics | Item #205-206: State of art memory architecture with ablation data |
| **MEDIUM** | Read Reflexion paper for Wait pattern improvements | Pattern 34: May improve our retry pipeline (20-22% improvement quantified) |
| **MEDIUM** | Add inter-agent communication via ScratchPad | Item #212-213: Survey recommends explicit communication topologies between agents |
| **MEDIUM** | Evaluate RL fine-tuning for Qwen3-4B with QC rubric as reward | Item #211: Only works if Qwen has ≥1% exposure to similar tasks |
| **LOW** | Implement agent-controlled forgetting | Pattern 37: Agent should actively manage what it retains |
| **LOW** | Implement proactive intent prediction (world modeling) | Item #219: "It's 5am, you probably want morning briefing" |
| **LOW** | Review sparse topology literature for Phase 5+ | Item #214: Don't over-connect multi-agent systems |

### ATLAS Architecture Mapping

The survey's framework validates our existing architecture with specific academic names:

```
ATLAS Component              → Survey Concept
─────────────────────────────────────────────────────
0-token intents              → ARTIST (fewer calls optimal)
WorkoutRunner/RoutineRunner  → ReWOO (plan then execute)
Activity pipeline            → Plan-and-Execute with replanning
Haiku fallback + SessionBuf  → ReAct (reason-act-observe loop)
IntentDispatcher (23 levels) → Context-aware tool selection
Wait pattern + retry         → Reflexion (verbal RL)
QC hooks + audit_quality()   → Validator-driven feedback
ThoughtClassifier            → Structured memory (partial)
semantic_memory table        → Flat memory (needs upgrade)
.claude/agents/ (4 agents)   → Role-based multi-agent (5 roles)
config/ centralized          → CTDE pattern
Sandbox configs              → Governance framework (partial)
ConfidenceRouter             → Leader/Manager role
BridgeFileServer             → Communication Facilitator role
```

### Credibility Assessment

**Source Quality: 10/10** (upgraded from initial 9/10 after full processing)
135-page survey from UIUC + Meta + Amazon + Google DeepMind + UCSD + Yale. 29 authors. ~800 papers reviewed. #1 on HuggingFace. CC-BY 4.0 licensed. The most comprehensive and authoritative source in this knowledge base by a significant margin.

**Strengths:**
- Comprehensive taxonomy with formal POMDP foundation — not just opinions
- Maps clearly to practical implementation: each approach has named patterns with quantified tradeoffs
- Cross-validates patterns we identified independently from practitioner sources (S1-S13)
- ~800 papers filtered into actionable categories — the "sorting through noise" is done
- Quantified comparisons: ReWOO 80% token reduction, MAGMA 46% over flat memory, Reflexion 20-22% improvement
- Identifies exactly where we are (foundational layer, in-context reasoning) and what comes next

**Weaknesses:**
- Academic focus — doesn't address real-world deployment specifics (latency targets, cost per query)
- Missing practitioner perspective (Moltbot community, specific tool recommendations)
- Multi-agent section is less detailed than foundational section (acknowledged by reviewers)
- No cost-per-token analysis for different approaches
- Error accumulation mitigation strategies are identified as needed but not fully provided

**Overall:** This source is the Rosetta Stone for our project. It provides academic names and quantified tradeoffs for patterns we built intuitively. The three-layer framework (Foundation → Evolution → Collective) maps perfectly to our build phases. Most critically: **our architecture decisions are validated across the board** — ReWOO for structured workflows, ReAct for general queries, Reflexion for retry, 0-token for known intents, role-based multi-agent, passive context over active retrieval. We independently arrived at approaches confirmed by ~800 papers. The survey also identifies exactly what we should build next: structured memory (MAGMA-style, 46% improvement), agent-controlled memory operations, and formalized hybrid planning.

---

*S14 processed: January 30, 2026*

---
