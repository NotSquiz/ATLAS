# Agent Knowledge Base

**Purpose:** Structured research index for building ATLAS 3.0 — a 24/7 AI assistant for Baby Brains and personal use.

| Metric | Value |
|--------|-------|
| Sources | 22 (S1-S22) |
| Items | 244 |
| Patterns | 55 (P1-P55) |
| Themes | 8 |
| Actions | 64 (13 critical) |
| Phase | Intake ongoing, Synthesis v1 complete |
| Last updated | 2026-01-31 |

---

## Navigation

| Need | File |
|------|------|
| Overview (this file) | `README.md` |
| All patterns indexed | `PATTERNS.md` |
| Synthesis themes | `SYNTHESIS.md` |
| Action items tracker | `ACTIONS.md` |
| Top items by signal score | `indexes/SIGNAL_HEATMAP.md` |
| Specific source deep-dive | `sources/S{NN}_*.md` |
| New source template | `_templates/source_template.md` |
| Change history | `CHANGELOG.md` |

---

## Source Index

| ID | Source | Type | Items | Cred | Key Contribution |
|----|--------|------|:-----:|:----:|------------------|
| S1 | Scoble Molty Report #2 | Use cases | 34 | 7 | Agent-as-manager pattern, cost optimization, multi-platform |
| S2 | Youssef: LobeHub + Moltbot | Architecture | 28 | 8 | Brain+Hands pattern, RAG as shared infra, MCP bridge |
| S3 | "$3000 Computer" article | Privacy/deploy | 18 | 7 | Data sovereignty, hybrid routing, self-hosted stack |
| S4 | /last30days + Grok API | Tool eval | 12 | 7 | Role allocation framework, Grok X Search, routing by capability |
| S5 | Alex Finn memory config | Config tip | 3 | 7 | Memory flush before compaction, session search |
| S6 | Vercel AGENTS.md study | Benchmark | 10 | 8 | Passive context 100% vs active 53%, compressed index |
| S7 | Anthropic MCP Apps | Protocol spec | 15 | 9 | Interactive UI in conversations, sandboxed extensibility |
| S8 | Claire Vo: 24hrs Clawdbot | Practitioner | 14 | 8 | Failure catalog, async=sweet spot, permission creep |
| S9 | Typeless + STT landscape | Voice eval | 13 | 7 | Human vs agent voice tools, STT bottleneck |
| S10 | Composer + browser agents | Landscape | 11 | 6 | Browser as missing capability, security concerns |
| S11 | Brain Emulation Report | Neuroscience | 6 | 9 | Data > compute, individuality from experience |
| S12 | Asimov Press brains | Companion | 4 | 9 | Timelines, mechanism vs output distinction |
| S13 | VPS Security Hardening | Security | 16 | 9 | ACTIVE exploitation, Tailscale, hardening checklist |
| S14 | Agentic Reasoning Survey | Academic (800 papers) | 44 | 10 | Three-layer framework, planning taxonomy, ATLAS validation |
| S15 | Claude Code "Team of Five" | Practitioner | 14 | 8 | Parallel worktrees, custom commands, eng-manager mindset |
| S16 | BrainPro (Jeff Garzik) | Agent impl | 20 | 9 | Circuit breakers, privacy tiers, fallback chains, tool ACLs |
| S17 | Vestige + FSRS-6 | Memory arch | 22 | 8 | Forgetting as feature, dual strength, prediction error gating |
| S18 | Claude Cowork Plugins | Product launch + OSS | 14 | 8 | Plugin architecture (skills+commands+connectors+sub-agents), MCP Tool Search (85% token reduction) |
| S19 | Agentic Image Generation | Practitioner + Product | 12 | 7 | Self-improving image loops (Nano Banana + Claude Code), Google Agentic Vision, BB carousel pipeline |
| S20 | Team of Rivals + Swarm Intelligence | Academic + Scientific | 16 | 9 | Opposing incentives (92.1% vs 60%), self-review degrades quality, quorum sensing, bio-inspired consensus |
| S21 | THE SEED Recursive Loop | Social media / Practitioner | 6 | 3 | 8-phase meta-learning loop, "accumulate WHAT empty HOW" heuristic. Low credibility, confirms existing patterns |
| S22 | OpenClaw Agent Canvas | Open-source tool | 12 | 8 | Visual agent dashboard, 13 messaging adapters, Docker sandboxes, model failover. Validates 8 patterns in one system |

---

## Top Patterns (by convergence)

| Conv | Pattern | Sources | Theme |
|:----:|---------|---------|-------|
| 6 | P2/P13: Hybrid model routing | S1,S2,S3,S4,S14,S16 | T3 |
| 4 | P4: Isolation = Safety | S1,S3,S8,S13 | T4 |
| 4 | P20: Async delegation is THE use case | S1,S3,S8,S14 | T1 |
| 4 | P21: Humans must optimize for safety | S8,S13,S14,S16 | T4 |
| 3 | P6: Brain + Hands (design vs execution) | S2,S14,S15 | T7 |
| 3 | P10: Data sovereignty as strategy | S3,S6,S11 | T4,T8 |
| 3 | P12: Overnight autonomous work | S1,S3,S8 | T1 |
| 4 | P14: Passive context >> active retrieval | S6,S14,S15,S18 | T2 |
| 3 | P35: Flat -> structured memory (46%) | S5,S6,S14,S17 | T5 |

---

## Themes (from Synthesis v1)

| # | Theme | Confidence | BB Priority |
|---|-------|------------|-------------|
| T1 | Async delegation is THE use case | Consensus (4+) | CRITICAL |
| T2 | Passive context >> active retrieval | Quantified (100% vs 53%) | HIGH |
| T3 | Hybrid model routing | Consensus (6 sources) | MEDIUM |
| T4 | Security is non-negotiable | Evidence (real exploits) | HIGH |
| T5 | Memory must evolve (flat -> cognitive) | Quantified (46%) | LOW launch / HIGH infra |
| T6 | Voice is the primary interface | Validated | LOW for BB launch |
| T7 | Development multiplier | Practitioner | HIGH |
| T8 | Data quality > model quality | Multi-domain | CRITICAL |

---

## Open Actions (top 10)

| ID | Action | Priority | Domain | Source |
|----|--------|:--------:|--------|--------|
| A01 | Harden desktop (UFW, fail2ban, Tailscale) | P0 | SECURITY | S13 |
| A03 | Add privacy tiers to model routing | P0 | SECURITY | S16 |
| A04 | Implement circuit breakers for APIs | P0 | ARCH | S16 |
| A05 | Implement FSRS-6 decay for semantic_memory | P0 | MEMORY | S17 |
| A06 | Add prediction error gating to ThoughtClassifier | P0 | MEMORY | S17 |
| A08 | Tool-level access control for agents | P0 | SECURITY | S16 |
| A09 | Formalize fallback chains (Claude->Haiku->Ollama) | P0 | ARCH | S16 |
| A13 | Evaluate LobeHub on desktop | P1 | TOOLS | S2,S3 |
| A14 | Evaluate Vestige as memory layer | P1 | MEMORY | S17 |
| A17 | Adopt git worktrees for parallel dev | P1 | WORKFLOW | S15 |

Full list: `ACTIONS.md` (52 items)

---

## Category Taxonomy

| Tag | Covers | Items |
|-----|--------|:-----:|
| `ARCH` | Architecture, infrastructure, deployment | ~47 |
| `SECURITY` | Sandboxing, safety, permissions, data protection | ~38 |
| `MEMORY` | Persistence, knowledge graphs, episodic memory | ~29 |
| `VOICE` | TTS, STT, voice interaction patterns | ~18 |
| `AUTONOMY` | Self-improvement, daemon mode, proactive behavior | ~22 |
| `COMMS` | Messaging platforms, multi-channel, notifications | ~12 |
| `WORKFLOW` | Task management, email, calendar, productivity | ~20 |
| `TOOLS` | Specific tools, libraries, APIs, integrations | ~35 |
| `COST` | Token optimization, hardware costs, efficiency | ~15 |
| `UX` | Interaction design, emotional engagement | ~8 |
| `BUSINESS` | Baby Brains specific, revenue, content pipeline | ~10 |
| `COMMUNITY` | Sentiment, adoption patterns, what's working | ~6 |

---

## Signal Scoring

Items are ranked by composite score: `Signal = (R×0.30) + (C×0.25) + (Q×0.25) + (V×0.20)`

| Tier | Range | Meaning | Count |
|------|-------|---------|:-----:|
| S-Tier | 9.0+ | Validated, critical, act now | 10 |
| A-Tier | 7.5-8.9 | Strong signal, plan for it | 24 |
| B-Tier | 5.5-7.4 | Worth investigating | 4 |

Full heatmap: `indexes/SIGNAL_HEATMAP.md`

---

## How to Add a New Source

1. Copy `_templates/source_template.md` to `sources/S{NN}_{slug}.md`
2. Fill frontmatter, TL;DR, key thesis
3. Extract items with tags, relevance, confidence, signal score
4. Identify patterns (new P-numbers or references to existing)
5. Run verification checklist (Fact-Check, Confidence, Wait, Inversion)
6. Write cross-references, credibility assessment, noise filter
7. Add action items to `ACTIONS.md` with A-numbers
8. Update this README: source index row, stats
9. Run `python scripts/kb_rebuild_indexes.py` to regenerate indexes
10. If 5+ sources since last synthesis: trigger synthesis refresh

### Intake Modes

| Mode | When | Effort |
|------|------|--------|
| **Quick Capture** | Tweets, tool mentions, bookmarks | ~30 sec |
| **Deep Intake** | Papers, practitioner articles, tools | 15-45 min |

### Signal Type Classification (during initial read)

| Novel? | Changes architecture? | Type | Action |
|--------|----------------------|------|--------|
| Yes | Yes | **Hidden Gem** | Always Deep Intake |
| No | Yes | **Contradiction** | Always Deep Intake + resolve |
| Yes | No | **Confirmation** | Quick Capture, note pattern |
| No | No | **Noise** | Skip or Quick Capture |

### HIGH Relevance Gate

Before marking any item HIGH, verify:
1. Source is credible and identifiable
2. Claim is falsifiable + has evidence OR independently reported
3. Specific connection to ATLAS architecture or planned feature
4. Inversion test passed (for architecture-changing items)
5. Wait pattern applied (for single-source items)
