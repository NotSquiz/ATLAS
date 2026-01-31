# ATLAS Knowledge Base -- Action Items Tracker

Generated: 2026-01-31 | Sources: S01-S17 (284 extracted items, 49 patterns)

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Actions** | 67 |
| **P0 (Critical)** | 13 |
| **P1 (High)** | 21 |
| **P2 (Medium)** | 24 |
| **P3 (Low)** | 9 |
| **Status: TODO** | 67 |

## Domain Dashboard

| Domain | P0 | P1 | P2 | P3 | Total |
|--------|:--:|:--:|:--:|:--:|:-----:|
| MEMORY | 4 | 4 | 4 | 2 | 14 |
| ARCH | 2 | 7 | 3 | 1 | 13 |
| SECURITY | 5 | 2 | 2 | 0 | 9 |
| TOOLS | 0 | 3 | 5 | 2 | 10 |
| WORKFLOW | 0 | 2 | 3 | 1 | 6 |
| VOICE | 0 | 2 | 1 | 1 | 4 |
| BUSINESS | 0 | 0 | 2 | 1 | 3 |
| COST | 1 | 1 | 1 | 1 | 4 |

---

## P0 -- Critical

Security-critical items or validated by 3+ sources as essential. Do these first.

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A01 | Harden desktop: UFW default-deny, fail2ban, Tailscale VPN mesh, SSH keys-only via Tailscale IP range | S13 | P28, P29 | TODO | -- | SECURITY |
| A02 | Set file permissions: `chmod 600` all `.env` files, `chmod 700` credential dirs, enable unattended-upgrades | S13 | P28 | TODO | A01 | SECURITY |
| A03 | Implement privacy tiers for model routing (standard/sensitive/strict) with sensitive-pattern auto-escalation | S16, S3, S13 | P42, P10 | TODO | -- | SECURITY |
| A04 | Implement circuit breaker + fallback chains for Garmin, USDA, and LLM APIs (Closed->Open->HalfOpen pattern) | S16, S14 | P43, P38 | TODO | -- | ARCH |
| A05 | Add FSRS-6 decay to `semantic_memory` -- memories must forget or retrieval degrades at scale | S17, S14 | P46, P35 | TODO | -- | MEMORY |
| A06 | Add prediction error gating to ThoughtClassifier -- detect CREATE/UPDATE/SUPERSEDE before storage | S17, S14 | P48, P35 | TODO | -- | MEMORY |
| A07 | Design dual-strength scoring for memory entries (retrievability vs stability as independent dimensions) | S17, S14 | P47, P35 | TODO | A05 | MEMORY |
| A08 | Enforce tool-level access control for `.claude/agents/` -- prompt instructions are not enforcement | S16, S14 | P44 | TODO | -- | SECURITY |
| A09 | Formalize fallback chains with category overrides: Claude -> Haiku -> Ollama, coding always tries Claude first | S16, S4 | P43, P13 | TODO | A04 | ARCH |
| A10 | Allowlist-only for all external interfaces: Telegram user IDs, browser domains, email senders | S13, S8, S10 | P30, P21, P27 | TODO | A01 | SECURITY |
| A11 | Add temporal backbone to `semantic_memory` -- `previous_thought_id` and `related_thought_ids` columns | S14, S17 | P35, P46 | TODO | -- | MEMORY |
| A12 | Implement cost tracking: token counts, USD per backend, API spend monitoring (Prometheus or JSON export) | S16, S4, S1 | P43 | TODO | -- | COST |

---

## P1 -- High

Important items validated by multiple sources. Not blocking but high-impact.

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A13 | Evaluate LobeHub: self-host via Docker, test agent groups, knowledge base, MCP integration, model routing | S2, S3 | P6, P8 | TODO | A01 | TOOLS |
| A14 | Evaluate Vestige as drop-in MCP memory layer (29 tools, FSRS-6, 100% local, Rust) | S17, S14 | P46, P47, P48 | TODO | -- | MEMORY |
| A15 | Add periodic memory quality audit -- re-classify stored thoughts via ThoughtClassifier to detect drift | S14, S17 | P35, P48 | TODO | A06 | MEMORY |
| A16 | Implement entity linking via ThoughtClassifier taxonomy -- make categories graph-queryable | S14, S17 | P35 | TODO | A11 | MEMORY |
| A17 | Adopt git worktrees for parallel ATLAS development (4-5 simultaneous Claude Code instances) | S15, S14 | P39 | TODO | -- | WORKFLOW |
| A18 | Create custom Claude Code commands for ATLAS: `/intake`, `/build`, `/deploy` | S15, S16 | P40, P45 | TODO | -- | WORKFLOW |
| A19 | Upgrade STT from PowerShell to Whisper Local (V3 Turbo) -- STT is the weakest link in voice chain | S9 | P25 | TODO | -- | VOICE |
| A20 | Add JSONL session logging for agent audit trail (currently discarded after 10 min) | S16, S8 | P43, P21 | TODO | -- | SECURITY |
| A21 | Document hybrid planning architecture formally: 0-token=none, ReWOO=structured, Plan-and-Execute=pipeline, ReAct=general | S14 | P32, P33 | TODO | -- | ARCH |
| A22 | Build compressed knowledge index for Baby Brains activities (8KB index vs 40KB full injection) | S6 | P15 | TODO | -- | ARCH |
| A23 | Implement prospective memory (future intention triggers) -- "remember to X" should surface at the right TIME | S17, S14 | P49 | TODO | A05 | MEMORY |
| A24 | Sign up for Grok API, test X Search with Baby Brains queries for trend research | S4 | P13 | TODO | -- | TOOLS |
| A25 | Build pre-compaction memory flush hook -- save full context summary before context window purge | S5, S17 | P46 | TODO | -- | ARCH |
| A26 | Decompose CLAUDE.md into modular prompt components (identity -> conventions -> tools -> mode) | S16 | P45 | TODO | -- | ARCH |
| A27 | Add filler-word removal and correction detection to voice STT pipeline | S9 | P25 | TODO | A19 | VOICE |
| A28 | Implement sensitive-pattern detection for voice pipeline -- auto-route when user says something private | S16, S9 | P42 | TODO | A03 | SECURITY |

---

## P2 -- Medium

Worth doing when relevant. Validated by at least one source with clear rationale.

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A29 | Evaluate Olares OS for containerized service management on desktop | S3 | P10, P11 | TODO | A01 | TOOLS |
| A30 | Evaluate Perplexica as self-hosted search (free alternative to Grok Web Search for general queries) | S3, S4 | P10 | TODO | A01 | TOOLS |
| A31 | Evaluate pgvector (PostgreSQL) vs SQLite semantic_memory for Baby Brains knowledge base | S2 | P8 | TODO | -- | MEMORY |
| A32 | Build MCP-accessible memory search tool so agent can query its own conversation history | S5, S7 | P17 | TODO | A11 | MEMORY |
| A33 | Investigate qmd for token reduction in batch processing (96% claimed reduction) | S1 | P3 | TODO | -- | COST |
| A34 | Set up MCP integrations for Baby Brains customer feedback pipeline (Featurebase or equiv -> GitHub) | S15, S7 | P17, P40 | TODO | -- | WORKFLOW |
| A35 | Build hello-world MCP App (health status viewer) and test with cloudflared tunnel | S7 | P18, P19 | TODO | -- | TOOLS |
| A36 | Add retroactive importance to captured thoughts -- promote when recalled in high-leverage context | S17 | P49 | TODO | A07 | MEMORY |
| A37 | Evaluate NocoDB as self-hosted Airtable for Baby Brains activity tracking / content calendar | S3 | P10 | TODO | A01 | WORKFLOW |
| A38 | Add inter-agent communication via ScratchPad for multi-agent coordination | S14 | P31 | TODO | -- | ARCH |
| A39 | Build ATLAS security self-check command (verify permissions, ports, firewall, credentials) | S13 | P28 | TODO | A01 | SECURITY |
| A40 | Benchmark semantic_memory at 10K+ entries to test retrieval degradation | S17, S14 | P46 | TODO | -- | MEMORY |
| A41 | Evaluate Beeper as unified messaging bridge (alternative to per-platform bridges) | S1 | P4 | TODO | -- | WORKFLOW |
| A42 | Try Typeless free tier for human dictation productivity ($12/mo, 4x faster than typing) | S9 | P24 | TODO | -- | VOICE |
| A43 | Create "self-critique" prompts for activity pipeline ("What are 10 things wrong with this output?") | S15 | P41 | TODO | -- | ARCH |
| A44 | Adopt `.brainpro/commands/` pattern for custom ATLAS commands with YAML frontmatter + tool restrictions | S16, S15 | P40, P44 | TODO | A18 | TOOLS |

---

## P3 -- Low / Backlog

Long-term items. Revisit when relevant phase begins.

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A45 | Evaluate Steel.dev / Playwright MCP for browser automation when Phase 5 starts | S10 | P26, P27 | TODO | -- | TOOLS |
| A46 | Implement agent-controlled forgetting (agent decides what to retain and what to purge) | S14, S17 | P37, P46 | TODO | A05 | MEMORY |
| A47 | Implement proactive intent prediction ("It's 5am, you probably want morning briefing") | S14 | P31 | TODO | -- | ARCH |
| A48 | Review sparse communication topology literature for Phase 5+ multi-agent design | S14 | P31 | TODO | -- | MEMORY |
| A49 | Study FSRS-6 parameter tuning for ATLAS-specific memory patterns (health vs project vs admin decay) | S17 | P46 | TODO | A05 | COST |
| A50 | Evaluate RL fine-tuning for Qwen3-4B with QC rubric as reward signal | S14 | P34 | TODO | -- | TOOLS |
| A51 | Study BrainPro Rust implementation for daemon mode design (WebSocket -> Unix socket -> agent) | S16 | P43 | TODO | -- | VOICE |
| A52 | Revisit Composer browser agent in 3-6 months for maturity check | S10 | P26 | TODO | -- | WORKFLOW |

---

## S18 Actions (January 31, 2026)

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A53 | Restructure `.claude/` to follow plugin architecture: add `plugin.json` manifest, formalize skills/commands/agents to match Cowork convention | S18 | P50, P45 | TODO | -- | ARCH |
| A54 | Evaluate MCP Tool Search for ATLAS: test dynamic tool loading as MCP tool count grows beyond 10 | S18 | P51, P3 | TODO | -- | COST |
| A55 | Study 11 open-source reference plugins for skill/command design patterns | S18 | P50 | TODO | -- | TOOLS |
| A56 | Build Baby Brains Cowork plugin: export BB warming, content pipeline, doc search as installable plugin | S18 | P50 | TODO | A53 | BUSINESS |

---

## S19 Actions (January 31, 2026)

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A57 | Evaluate Nano Banana Pro API for BB carousel image generation — test with sample carousel, measure quality and cost | S19 | P52 | TODO | -- | TOOLS |
| A58 | Build BB image generation Claude Code skill — wrap Nano Banana API with BB brand guidelines as system context | S19 | P50, P52 | TODO | A57 | BUSINESS |
| A59 | Investigate Agentic Vision (Gemini 3 Flash) for visual QC — test carousel images through Think→Act→Observe | S19 | P52 | TODO | A57 | ARCH |
| A60 | Research SynthID implications for BB content — determine policy on AI-generated imagery disclosure | S19 | -- | TODO | -- | BUSINESS |

---

## S20 Actions (January 31, 2026)

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A61 | Implement independent critic agent for ATLAS pipelines — separate model from generator, VETO authority not scoring | S20, S14 | P53, P54 | TODO | -- | ARCH |
| A62 | Design quorum-based voting for multi-agent decisions — threshold agreement with confidence weighting | S20 | P55 | TODO | -- | ARCH |
| A63 | Implement Swiss Cheese error layers — map intent→execution→QC→output as independent failure layers | S20, S14, S16 | P53, P38 | TODO | A61 | ARCH |
| A64 | Add context isolation between sub-agents (Context Ray Tracing) — role-relevant info only, summaries bridge | S20, S16 | P44, P53 | TODO | -- | SECURITY |

---

## S22 Actions (January 31, 2026)

| ID | Action | Source(s) | Patterns | Status | Depends | Domain |
|----|--------|-----------|----------|--------|---------|--------|
| A65 | Evaluate OpenClaw as reference architecture for ATLAS multi-platform messaging — study 13 adapter implementations for Telegram bridge | S22 | P4, P30 | TODO | -- | COMMS |
| A66 | Study OpenClaw's AGENTS.md/SOUL.md/TOOLS.md split as model for decomposing CLAUDE.md | S22, S16 | P45 | TODO | A26 | ARCH |
| A67 | Evaluate OpenClaw Agent Canvas UI as reference for ATLAS multi-agent dashboard | S22 | -- | TODO | -- | TOOLS |

---

## Dependency Graph (Key Chains)

```
A01 (harden desktop)
 ├── A02 (file permissions)
 ├── A10 (allowlist-only)
 ├── A13 (evaluate LobeHub)
 ├── A29 (evaluate Olares)
 ├── A30 (evaluate Perplexica)
 ├── A37 (evaluate NocoDB)
 └── A39 (security self-check)

A05 (FSRS-6 decay)
 ├── A07 (dual-strength scoring)
 │    └── A36 (retroactive importance)
 ├── A23 (prospective memory)
 ├── A46 (agent-controlled forgetting)
 └── A49 (FSRS parameter tuning)

A06 (prediction error gating)
 └── A15 (periodic memory audit)

A11 (temporal backbone)
 ├── A16 (entity linking)
 └── A32 (MCP memory search)

A04 (circuit breaker)
 └── A09 (fallback chains)

A03 (privacy tiers)
 └── A28 (sensitive pattern detection)

A19 (Whisper STT upgrade)
 └── A27 (filler-word removal)

A18 (custom commands)
 └── A44 (YAML frontmatter commands)

A53 (plugin architecture)
 └── A56 (BB Cowork plugin)

A57 (evaluate Nano Banana)
 ├── A58 (BB image gen skill)
 └── A59 (Agentic Vision QC)

A61 (independent critic agent)
 └── A63 (Swiss Cheese error layers)

A26 (decompose CLAUDE.md)
 └── A66 (study OpenClaw AGENTS/SOUL/TOOLS split)
```

---

## Deduplication Notes

The following items appeared in multiple sources and were merged:

| Merged Action | Sources That Recommended It |
|---------------|----------------------------|
| A03 (privacy tiers) | S16 (privacy routing), S3 (data sovereignty), S13 (security hardening) |
| A04 (circuit breaker) | S16 (BrainPro pattern), S14 (OWASP ASI08 cascading failures) |
| A05 (FSRS-6 decay) | S17 (Vestige implementation), S14 (flat memory fails, MAGMA 46% improvement) |
| A09 (fallback chains) | S16 (BrainPro), S4 (role allocation), S1 (model routing), S2 (40+ providers) |
| A10 (allowlist-only) | S13 (Telegram allowlist), S8 (permission creep), S10 (browser whitelist) |
| A11 (temporal backbone) | S14 (MAGMA traversal > structure), S17 (context-dependent retrieval) |
| A13 (evaluate LobeHub) | S2 (full evaluation), S3 (listed as ChatGPT alternative on Olares) |
| A22 (compressed index) | S6 (8KB = 40KB, 100% vs 53%), S14 (passive context validated) |
| A30 (Perplexica) | S3 (self-hosted Perplexity), S4 (compare with Grok Web Search) |

---

## How to Update This File

1. When starting an action: change Status from `TODO` to `IN PROGRESS`
2. When completing: change to `DONE` and add completion date in Notes
3. When an action spawns sub-actions: add new rows with next available A{NN} ID
4. When a new source (S18+) is processed: extract actions, deduplicate, assign IDs starting after A52
5. Re-run domain dashboard counts after any status changes

---

*Last updated: 2026-01-31*
*Source: 22 sources (S01-S22), 338 items, 55 patterns*
