# ATLAS Knowledge Base: Pattern Index

**Total Patterns:** 55 (P1-P55)
**Sources:** 20 (S1-S20)
**Themes:** 8 (T1-T8)
**Generated:** January 31, 2026

---

## Master Table

| # | Name | Sources | Conv. | Theme | Key Insight |
|---|------|---------|-------|-------|-------------|
| P1 | Agent-as-Manager | S1 | 1 | T1 | Agents operate with judgment and authority, managing other systems rather than just executing commands |
| P2 | Multi-Model Routing is Standard | S1, S2, S3, S4, S14, S16 | 6 | T3 | Route different tasks to different models by capability, cost, privacy, and risk |
| P3 | Cost Awareness is Critical | S1 | 1 | T3 | Token reduction (96% via qmd), adaptive chunking, model switching; 0-token matching is competitive advantage |
| P4 | Isolation = Safety | S1, S3, S8, S13 | 4 | T4 | Dedicated machines, separate accounts, session boundaries; agents need containment |
| P5 | Proactive > Reactive | S1 | 1 | T1 | Shift from "do what I say" to "notice what needs doing"; daemon/loop concept |
| P6 | Design Layer vs Execution Layer (Brain + Hands) | S2, S14, S15, S20 | 4 | T7 | Separate design/orchestration layer from execution layer, connected via MCP |
| P7 | Distillation Workflow | S2 | 1 | T7 | Multi-agent collaboration for design, distill best workflow into single deployed agent prompt |
| P8 | Knowledge Base as Shared Infrastructure | S2, S18 | 2 | T2 | RAG is infrastructure shared across all agents via MCP; single source of truth |
| P9 | Honest Complexity Assessment | S2 | 1 | T7 | Don't adopt tools because they're impressive; adopt them if they solve a real problem |
| P10 | Data Sovereignty as Strategy | S3, S6, S11 | 3 | T4, T8 | Private data is competitive advantage; local-first architecture protects the moat |
| P11 | Physical Control Over AI Agents | S3, S13 | 2 | T4 | Ability to physically disconnect an autonomous agent matters; local hardware > cloud VPS |
| P12 | Overnight Autonomous Work | S1, S3, S8 | 3 | T1 | Agents produce real deliverables when given goals and left unattended for extended periods |
| P13 | Hybrid Model Routing is Consensus | S1, S2, S3, S4, S14, S16 | 6 | T3 | Local for routing/private data, cloud for heavy reasoning; established architecture |
| P14 | Passive Context > Active Retrieval | S6, S14, S15, S18 | 4 | T2 | Embedding knowledge in persistent context (100% pass) massively outperforms tool-based lookup (53%) |
| P15 | Compressed Index + File Retrieval | S6 | 1 | T2 | 8KB compressed index matches 40KB full injection; agent reads index, retrieves specific files |
| P16 | Test Against Training Data Gaps | S6, S11 | 2 | T2, T8 | Evaluate agents on knowledge they cannot already have; domain-specific tests prove custom knowledge value |
| P17 | Protocol Layer vs Application Layer | S7, S18 | 2 | T3 | Anthropic leads at protocol (MCP); value is in domain-specific applications built on top |
| P18 | Interactive > Text for Complex Data | S7 | 1 | T6 | Text loses fidelity with complex data; MCP Apps enable interactive UI inside AI conversations |
| P19 | Sandboxed Extensibility | S7, S16, S18 | 3 | T4 | Sandboxed iframe + host-controlled capabilities shows how to safely extend AI with third-party code |
| P20 | Async Delegation > Real-Time Interaction | S1, S3, S8, S14 | 4 | T1 | Agent excels with high-level goal left alone; struggles with real-time back-and-forth |
| P21 | Agents Optimize Capability, Humans Optimize Safety | S8, S13, S16, S17 | 4 | T4 | Agents request max permissions by default; human role is to constrain, scope, and gate |
| P22 | LLMs Cannot Do Temporal Reasoning | S8 | 1 | T4 | Dates, recurring events, day-of-week calculations require deterministic code, not LLM reasoning |
| P23 | Voice Input Scales Beyond Simple Commands | S1, S3, S8, S9 | 4 | T6 | 200+ word specifications via voice work; voice is not limited to short commands |
| P24 | Separate Human Voice Tools from Agent Voice Tools | S9 | 1 | T6 | Human needs dictation (Typeless); agent needs STT (Whisper/Deepgram); complementary layers |
| P25 | STT is the Weakest Link in Voice Chains | S9 | 1 | T6 | STT input is the bottleneck; upgrading it improves everything downstream |
| P26 | Browser is the Missing Hands Layer | S10 | 1 | T3 | Agent can speak, listen, execute code; cannot interact with the web; browser agents fill this gap |
| P27 | Browser Access Requires Highest Security Tier | S10, S13 | 2 | T4 | Browser agents access credentials, forms, transactions; whitelist-only domains, screenshot before submit |
| P28 | Security Before Features (Non-Negotiable) | S13, S16 | 2 | T4 | Every exploited agent was deployed features-first, security-later; harden THEN install |
| P29 | Local > VPS for Security | S3, S13 | 2 | T4 | Local hardware with no public exposure eliminates remote exploitation; tradeoff is VPN for remote access |
| P30 | Allowlist-Only for All External Interfaces | S7, S10, S13 | 3 | T4 | Telegram user IDs, browser domains, MCP capabilities, email addresses; default DENY with explicit exceptions |
| P31 | Three-Layer Agent Architecture | S14 | 1 | T1 | Foundation (planning/tools) --> Self-Evolving (feedback/memory) --> Collective (multi-agent); formalized as POMDP |
| P32 | Hybrid Planning is the Answer | S14 | 1 | T1 | No single planning approach dominates; real systems combine ReAct + ReWOO + Plan-and-Execute |
| P33 | Decoupling Planning from Execution (ReWOO) | S2, S14 | 2 | T1 | Plan first, execute separately; 80% token reduction vs ReAct on structured tasks |
| P34 | Reflexion = Wait Pattern (Quantified) | S14 | 1 | T5 | Verbal RL: reflect on failure, retry with lessons; 20% improvement on HotPotQA, 22% on ALFWorld |
| P35 | Flat Memory --> Structured Memory | S5, S14, S17 | 3 | T5 | MAGMA structured memory scores 46% above flat; traversal policy matters more than graph structure |
| P36 | Fewer Deliberate Tool Calls > Frequent Calls (ARTIST) | S6, S14 | 2 | T1, T2 | Less LLM involvement = better for known workflows; validates 0-token architecture |
| P37 | Memory Operations as Agent Actions | S14, S17 | 2 | T5 | Write, retrieve, forget as explicit agent decisions, not passive storage; RL-optimized memory management |
| P38 | Cascading Failures are the Multi-Agent Threat | S14, S16, S20 | 3 | T4 | Single compromised agent poisoned 87% of downstream decisions in 4 hours; Swiss Cheese Model prevents cascade |
| P39 | Parallel Agent Instances via Git Worktrees | S15 | 1 | T7 | Run 4-5 Claude Code instances simultaneously, each in own worktree; practical multi-agent with zero infra |
| P40 | Single-Trigger Delegation | S15, S16, S18 | 3 | T7 | Collapse complex multi-step operations into one-word commands; extreme friction reduction |
| P41 | Developer as Engineering Manager | S2, S15 | 2 | T7 | Stop writing code, start directing; human energy goes to architecture, taste, and quality judgment |
| P42 | Privacy as a Routing Constraint | S3, S16 | 2 | T3, T4 | Three tiers (standard/sensitive/strict) determine backend selection; sensitive content auto-escalates |
| P43 | Circuit Breaker + Fallback Chain | S14, S16 | 2 | T3, T4 | Circuit breakers prevent hammering failed services; fallback chains route to alternatives; production resilience |
| P44 | Tool-Level Access Control > Prompt-Level Instructions | S16, S18 | 2 | T4 | Subagent tool restrictions enforced at access level; prompt instructions can be ignored |
| P45 | Modular Prompt Assembly | S16, S18 | 2 | T7 | Composable prompt layers (identity --> soul --> tooling --> mode) vs monolithic system prompt |
| P46 | Forgetting is the Feature (Memory != Storage) | S17 | 1 | T5 | FSRS-6 decay prevents context bloat; infinite retention RAG degrades after ~10K interactions |
| P47 | Dual Strength Memory (Retrievability != Stability) | S17 | 1 | T5 | Two independent dimensions per memory: access speed (retrievability) and decay rate (stability) |
| P48 | Prediction Error Gating | S17 | 1 | T5 | Detect conflicts before storage; decide CREATE/UPDATE/SUPERSEDE rather than blindly appending |
| P49 | Retroactive Importance | S17 | 1 | T5 | Memories gain importance after storage; trivial memory recalled in high-leverage context gets promoted |
| P50 | Plugin Architecture = Canonical Agent Customization | S18 | 1 | T7 | Anthropic's formalization: skills (passive) + commands (explicit) + connectors (MCP) + sub-agents (scoped) = domain-specific agent |
| P51 | Dynamic Tool Loading (MCP Tool Search) | S18 | 1 | T3 | Load tools on demand when context exceeds threshold; 85% token reduction AND accuracy improvement |
| P52 | Agentic Vision = Think→Act→Observe for Multimodal | S19 | 1 | T1 | Agents generate visual output, evaluate against criteria, identify flaws, regenerate. Self-improving loops for images |
| P53 | Opposing Incentives Create Coherence (Team of Rivals) | S20 | 1 | T4 | Agents with different goals constrain each other; planner vs executor vs critic. 92.1% success vs 60% single-agent |
| P54 | Self-Review Degrades Quality | S20 | 1 | T4 | Same entity cannot reliably evaluate itself; self-verification changed correct→incorrect 60% of the time |
| P55 | Quorum Sensing > Consensus | S20 | 1 | T1 | Threshold agreement is faster AND more accurate than unanimity; bees use 10-15/300+ scouts; quality-weighted advocacy |

---

## Patterns by Theme

### T1: Async Delegation
*Agents excel with high-level goals and autonomous execution, not real-time back-and-forth.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P20 | Async Delegation > Real-Time Interaction | 4 | S1 overnight orchestration, S3 24hr run, S8 Reddit research star, S14 ReWOO |
| P12 | Overnight Autonomous Work | 3 | Alex Finn 24hr run produced 3 scripts + systems + second-brain |
| P1 | Agent-as-Manager | 1 | Agents with judgment: push back on PRs, draft emails, manage systems |
| P5 | Proactive > Reactive | 1 | "Notice what needs doing" vs "do what I say"; daemon/loop concept |
| P31 | Three-Layer Agent Architecture | 1 | Foundation --> Self-Evolving --> Collective; POMDP formalization |
| P32 | Hybrid Planning is the Answer | 1 | ReAct + ReWOO + Plan-and-Execute; no single approach dominates |
| P33 | Decoupling Planning from Execution (ReWOO) | 2 | 80% token reduction; plan full sequence then execute without re-consulting LLM |
| P36 | Fewer Tool Calls > Frequent Calls (ARTIST) | 2 | Less LLM involvement = better for known workflows; validates 0-token |
| P52 | Agentic Vision (Think→Act→Observe) | 1 | S19: generate → evaluate → critique → retry for images; 5-10% quality boost; Google-formalized |
| P55 | Quorum Sensing > Consensus | 1 | S20: threshold agreement faster AND more accurate; bees use 10-15/300+; quality-weighted |

### T2: Passive Context
*Embed critical knowledge in persistent context rather than relying on active tool retrieval.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P14 | Passive Context > Active Retrieval | 4 | S6: 100% vs 53%; S18: Cowork skills ARE passive context (first-party validation) |
| P15 | Compressed Index + File Retrieval | 1 | 8KB index = 40KB full docs at same 100% pass rate |
| P16 | Test Against Training Data Gaps | 2 | Evaluate on knowledge agent cannot already have |
| P8 | Knowledge Base as Shared Infrastructure | 1 | RAG shared across all agents via MCP; single source of truth |
| P36 | Fewer Tool Calls > Frequent Calls (ARTIST) | 2 | Passive matching > active tool invocation |

### T3: Hybrid Routing
*Route tasks to the right model by capability, cost, privacy, and risk.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P2 | Multi-Model Routing is Standard | 6 | S1, S2, S3, S4, S14, S16 all independently validate |
| P13 | Hybrid Model Routing is Consensus | 6 | Local for private, cloud for heavy; 6 independent sources |
| P3 | Cost Awareness is Critical | 1 | 96% token reduction (qmd), adaptive chunking, model switching |
| P17 | Protocol Layer vs Application Layer | 1 | MCP is protocol; domain-specific applications are the value |
| P26 | Browser is the Missing Hands Layer | 1 | Web interaction as another capability tier to route to |
| P42 | Privacy as a Routing Constraint | 2 | Standard/sensitive/strict tiers; auto-escalation on sensitive content |
| P43 | Circuit Breaker + Fallback Chain | 2 | Primary --> secondary --> local failover; category-specific overrides |
| P51 | Dynamic Tool Loading (MCP Tool Search) | 1 | S18: 134K→5K tokens (85%); Opus 4.5 accuracy 79.5%→88.1% |

### T4: Security Layers
*Security is the most cross-referenced theme: 12 of 49 patterns. Three levels: platform, agent, operational.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P4 | Isolation = Safety | 4 | S1, S3, S8, S13; dedicated machines, separate accounts |
| P21 | Agents Optimize Capability, Humans Optimize Safety | 4 | S8 permission creep; agents request max by default |
| P30 | Allowlist-Only for All External Interfaces | 3 | Telegram IDs, browser domains, MCP capabilities; default DENY |
| P10 | Data Sovereignty as Strategy | 3 | Private data is moat; local-first protects it |
| P11 | Physical Control Over AI Agents | 2 | Local hardware can be unplugged; cloud VPS cannot |
| P19 | Sandboxed Extensibility | 2 | MCP Apps security: sandboxed iframe + host-controlled capabilities |
| P27 | Browser Access Requires Highest Security Tier | 2 | Credentials, forms, transactions; whitelist-only domains |
| P28 | Security Before Features | 2 | Every exploited agent was deployed features-first |
| P29 | Local > VPS for Security | 2 | Local eliminates remote exploitation; S13 documents active exploits |
| P38 | Cascading Failures are the Multi-Agent Threat | 2 | 87% downstream decisions poisoned in 4 hours |
| P42 | Privacy as a Routing Constraint | 2 | Health data --> strict/ZDR-only providers |
| P44 | Tool-Level Access Control > Prompt Instructions | 1 | Subagent restrictions enforced at tool access level |
| P22 | LLMs Cannot Do Temporal Reasoning | 1 | Deterministic code for dates/schedules, never LLM |
| P53 | Opposing Incentives Create Coherence | 1 | S20: 92.1% success via rival critics; Swiss Cheese misaligned failure modes |
| P54 | Self-Review Degrades Quality | 1 | S20: self-verification changed correct→incorrect 60%; independent critics essential |

### T5: Cognitive Memory
*Flat storage fails at scale. Memory needs decay, conflict detection, and dual-strength scoring.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P35 | Flat Memory --> Structured Memory | 3 | MAGMA: 46% improvement; traversal > structure in ablation |
| P37 | Memory Operations as Agent Actions | 2 | Write/retrieve/forget as explicit decisions, not passive storage |
| P34 | Reflexion = Wait Pattern (Quantified) | 1 | 20% on HotPotQA, 22% on ALFWorld via episodic failure memory |
| P46 | Forgetting is the Feature | 1 | FSRS-6 decay; RAG degrades after ~10K interactions without it |
| P47 | Dual Strength Memory | 1 | Retrievability (access speed) vs stability (decay rate) are independent |
| P48 | Prediction Error Gating | 1 | Detect conflicts: CREATE/UPDATE/SUPERSEDE, not blind append |
| P49 | Retroactive Importance | 1 | Memories gain importance after storage via synaptic tagging |

### T6: Voice-First
*Voice is the primary interface. STT is the bottleneck. Voice scales beyond simple commands.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P23 | Voice Input Scales Beyond Simple Commands | 4 | S1, S3, S8 (200+ word specs), S9; voice is not limited to short commands |
| P18 | Interactive > Text for Complex Data | 1 | MCP Apps enable interactive UI inside conversations |
| P24 | Separate Human Voice from Agent Voice | 1 | Human dictation (Typeless) vs agent STT (Whisper/Deepgram) |
| P25 | STT is the Weakest Link | 1 | Upgrading STT improves entire downstream chain |

### T7: Development Multiplier
*How we build matters as much as what we build. Parallel work, single-trigger commands, modular prompts.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P6 | Design Layer vs Execution Layer | 3 | Brain (design/test/iterate) + Hands (24/7 execution); connected via MCP |
| P41 | Developer as Engineering Manager | 2 | Stop implementing, start directing; human energy to architecture and taste |
| P40 | Single-Trigger Delegation | 2 | "PR" triggers entire branch --> commit --> description --> submit workflow |
| P7 | Distillation Workflow | 1 | Multi-agent design, single-agent deployment; quality inherits from design |
| P9 | Honest Complexity Assessment | 1 | Adopt tools for real problems, not impressiveness |
| P39 | Parallel Agent Instances via Git Worktrees | 1 | 4-5 Claude Code instances in parallel; zero infrastructure needed |
| P45 | Modular Prompt Assembly | 2 | Composable layers: identity --> soul --> tooling --> mode; S18 plugin manifest |
| P50 | Plugin Architecture = Canonical Agent Customization | 1 | S18: skills + commands + connectors + sub-agents; Anthropic's first-party formalization |

### T8: Data Quality
*Data differentiates, not models. Knowledge graph completion matters more than model upgrades.*

| # | Pattern | Conv. | Key Evidence |
|---|---------|-------|-------------|
| P10 | Data Sovereignty as Strategy | 3 | Private data is moat no cloud company can replicate |
| P16 | Test Against Training Data Gaps | 2 | Domain-specific knowledge is where custom systems prove value |

---

## Patterns by Convergence

*Ranked by number of independent sources supporting the pattern. Higher convergence = higher confidence.*

### Tier 1: Consensus (4+ independent sources)

| # | Pattern | Sources | Conv. |
|---|---------|---------|-------|
| P2 | Multi-Model Routing is Standard | S1, S2, S3, S4, S14, S16 | 6 |
| P13 | Hybrid Model Routing is Consensus | S1, S2, S3, S4, S14, S16 | 6 |
| P4 | Isolation = Safety | S1, S3, S8, S13 | 4 |
| P20 | Async Delegation > Real-Time Interaction | S1, S3, S8, S14 | 4 |
| P21 | Agents Optimize Capability, Humans Optimize Safety | S8, S13, S16, S17 | 4 |
| P23 | Voice Input Scales Beyond Simple Commands | S1, S3, S8, S9 | 4 |
| P14 | Passive Context > Active Retrieval | S6, S14, S15, S18 | 4 |
| P6 | Design Layer vs Execution Layer | S2, S14, S15, S20 | 4 |

### Tier 2: Validated (3 independent sources)

| # | Pattern | Sources | Conv. |
|---|---------|---------|-------|
| P10 | Data Sovereignty as Strategy | S3, S6, S11 | 3 |
| P12 | Overnight Autonomous Work | S1, S3, S8 | 3 |
| P19 | Sandboxed Extensibility | S7, S16, S18 | 3 |
| P30 | Allowlist-Only for All External Interfaces | S7, S10, S13 | 3 |
| P35 | Flat Memory --> Structured Memory | S5, S14, S17 | 3 |
| P38 | Cascading Failures are the Multi-Agent Threat | S14, S16, S20 | 3 |
| P40 | Single-Trigger Delegation | S15, S16, S18 | 3 |

### Tier 3: Corroborated (2 independent sources)

| # | Pattern | Sources | Conv. |
|---|---------|---------|-------|
| P11 | Physical Control Over AI Agents | S3, S13 | 2 |
| P16 | Test Against Training Data Gaps | S6, S11 | 2 |

| P27 | Browser Access Requires Highest Security Tier | S10, S13 | 2 |
| P28 | Security Before Features | S13, S16 | 2 |
| P29 | Local > VPS for Security | S3, S13 | 2 |
| P33 | Decoupling Planning from Execution (ReWOO) | S2, S14 | 2 |
| P36 | Fewer Tool Calls > Frequent Calls (ARTIST) | S6, S14 | 2 |
| P37 | Memory Operations as Agent Actions | S14, S17 | 2 |
| P41 | Developer as Engineering Manager | S2, S15 | 2 |
| P42 | Privacy as a Routing Constraint | S3, S16 | 2 |
| P43 | Circuit Breaker + Fallback Chain | S14, S16 | 2 |

### Tier 4: Single Source (1 source — may still be high value)

| # | Pattern | Source | Notes |
|---|---------|--------|-------|
| P1 | Agent-as-Manager | S1 | Foundational concept from practitioner community |
| P3 | Cost Awareness is Critical | S1 | Practical but narrowly sourced |
| P5 | Proactive > Reactive | S1 | Daemon/loop concept; validated by architecture but single source |
| P7 | Distillation Workflow | S2 | Multi-agent design to single-agent deploy |
| P8 | Knowledge Base as Shared Infrastructure | S2 | RAG as infrastructure via MCP |
| P9 | Honest Complexity Assessment | S2 | Meta-principle for tool adoption |
| P15 | Compressed Index + File Retrieval | S6 | Quantified (8KB=40KB) but single study |
| P17 | Protocol Layer vs Application Layer | S7 | Anthropic's own spec; single but authoritative |
| P18 | Interactive > Text for Complex Data | S7 | MCP Apps announcement |
| P22 | LLMs Cannot Do Temporal Reasoning | S8 | Documented failure; our code already handles this |
| P24 | Separate Human Voice from Agent Voice | S9 | Architectural distinction; not widely discussed |
| P25 | STT is the Weakest Link | S9 | Specific to voice pipeline assessment |
| P26 | Browser is the Missing Hands Layer | S10 | Capability gap identification |
| P31 | Three-Layer Agent Architecture | S14 | Academic survey (800 papers); single source but highest authority |
| P32 | Hybrid Planning is the Answer | S14 | Academic consensus from 800-paper survey |
| P34 | Reflexion = Wait Pattern (Quantified) | S14 | 20-22% improvement quantified |
| P39 | Parallel Agent Instances via Git Worktrees | S15 | Practitioner workflow |
| P44 | Tool-Level Access Control > Prompt Instructions | S16 | Implementation pattern from production system |
| P45 | Modular Prompt Assembly | S16 | Composable prompt architecture |
| P46 | Forgetting is the Feature | S17 | FSRS-6 backed by 100M+ Anki users |
| P47 | Dual Strength Memory | S17 | Cognitive science (Bjork Lab, UCLA) |
| P48 | Prediction Error Gating | S17 | Conflict detection before storage |
| P49 | Retroactive Importance | S17 | Synaptic tagging; no other source addresses this |
| P50 | Plugin Architecture = Canonical Agent Customization | S18 | Anthropic first-party formalization; new but authoritative |
| P51 | Dynamic Tool Loading (MCP Tool Search) | S18 | Quantified (85% token reduction, accuracy gains); new |
| P52 | Agentic Vision (Think→Act→Observe) | S19 | Self-improving image loops; Google formalized; practitioners validate |
| P53 | Opposing Incentives Create Coherence | S20 | 92.1% success via rival critics; Swiss Cheese; production-validated |
| P54 | Self-Review Degrades Quality | S20 | Self-verification changed correct→incorrect 60%; quantified on 522 sessions |
| P55 | Quorum Sensing > Consensus | S20 | Bees, Byzantine-tolerant swarms; faster AND more accurate than unanimity |

---

## Quick Reference: Source Coverage

| Source | Patterns | Domains |
|--------|----------|---------|
| S1: Scoble Molty Report | P1, P2, P3, P4, P5 | Architecture, autonomy, cost |
| S2: Youssef LobeHub | P6, P7, P8, P9 | Architecture, knowledge, design |
| S3: $3000 Computer Local AI | P10, P11, P12, P13 | Security, privacy, hardware |
| S4: Grok API + Role Allocation | (P2, P13 reinforced) | Routing, cost, strategy |
| S5: Memory Flush Config | (P35 reinforced) | Memory, session persistence |
| S6: Vercel AGENTS.md Study | P14, P15, P16 | Context, evaluation, knowledge |
| S7: Anthropic MCP Apps | P17, P18, P19 | Protocol, UI, security |
| S8: Claire Vo 24hrs Clawdbot | P20, P21, P22, P23 | Async, safety, failures |
| S9: Typeless + Voice Input | P24, P25 | Voice architecture |
| S10: Browser Agent Landscape | P26, P27 | Browser capability, security |
| S11: Brain Emulation 2025 | (P10, P16 reinforced) | Neuroscience, data quality |
| S12: Asimov Press Brains | (S11 companion) | Timelines, conceptual grounding |
| S13: VPS Security Hardening | P28, P29, P30 | Security, exploitation evidence |
| S14: Agentic Reasoning Survey | P31-P38 | Academic framework (800 papers) |
| S15: Claude Code Ship Team Five | P39, P40, P41 | Development workflow |
| S16: BrainPro Multi-Vendor | P42, P43, P44, P45 | Privacy, resilience, access control |
| S17: Vestige FSRS-6 Memory | P46, P47, P48, P49 | Cognitive memory, forgetting |
| S18: Claude Cowork Plugins | P50, P51 (new); P8, P14, P17, P19, P40, P44, P45 (reinforced) | Plugin architecture, dynamic tools, MCP ecosystem |
| S19: Agentic Image Generation | P52 (new); P5, P6, P41, P50 (reinforced) | Self-improving image loops, Nano Banana, Agentic Vision, BB content |
| S20: Team of Rivals + Swarm Intelligence | P53, P54, P55 (new); P4, P6, P21, P38, P44 (reinforced) | Opposing incentives, self-review degradation, quorum sensing, bio-inspired |

---

*Index generated from 20 sources, 326 extracted items.*
*Cross-referenced against SYNTHESIS_V1.md theme mapping.*
