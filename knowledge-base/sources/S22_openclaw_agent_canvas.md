# S22: OpenClaw (Clawdbot/Moltbot Rebrand) — Agent Canvas UI + Multi-Agent Architecture

## Frontmatter

| Field | Value |
|-------|-------|
| **ID** | S22 |
| **Source** | https://github.com/grp06/moltbot-agent-ui, https://github.com/openclaw/openclaw, https://openclaw.ai/ |
| **Author** | OpenClaw team (formerly Clawdbot/Moltbot; 9.7k GitHub stars on main repo) |
| **Date** | January 2026 |
| **Type** | Open-source tool / Agent platform |
| **Processed** | January 31, 2026 |
| **Credibility** | 8 |
| **Items Extracted** | 12 |
| **Patterns Identified** | None new; P4, P13, P30, P42, P43, P45, P50 reinforced |
| **Intake Mode** | DEEP |

## TL;DR (3 lines max)

OpenClaw (rebranded from Clawdbot/Moltbot) is a production local-first personal AI assistant with 13 messaging platform adapters, per-session Docker sandboxes, model failover chains, and multi-agent coordination via session tools. New: **Agent Canvas UI** — a Next.js visual command center for multi-agent orchestration with real-time WebSocket streaming. Architecture validates nearly every security and routing pattern in our index.

## Key Thesis

> "When you run multiple agents, you need a place to see what's happening. Terminals are great for commands. They're bad at orchestrating teams of agents."

---

## Extracted Items

### Agent Canvas UI (New)

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S22.01 | **Visual command center for multi-agent orchestration** — Next.js app connects to OpenClaw gateway via WebSocket (ws://127.0.0.1:18789). Real-time streaming of tool outputs and agent actions. Agent dashboard shows all running agents at a glance. Local-first, state persists to disk | `TOOLS` `ARCH` | HIGH | HIGH | 7.5 | P50 | ATLAS has Command Centre UI for health/workout. Multi-agent variant needed as agent count grows. Evaluate as reference for ATLAS agent dashboard |
| S22.02 | **Shared workspace management** — Central file storage for agent context (AGENTS.md, MEMORY.md). All agents in a workspace see same files. Workspace path is the unit of isolation between agent groups | `ARCH` `MEMORY` | HIGH | HIGH | 7.2 | P45 | Maps to our `.claude/` structure. Workspace = shared context boundary. Good pattern for BB agent vs Personal agent isolation |

### Gateway Architecture

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S22.03 | **WebSocket gateway as single control plane** — Sessions, channels, tools, and events all route through one gateway. Binds to loopback by default. Remote access via Tailscale Serve/Funnel or SSH tunnels | `ARCH` `SECURITY` | HIGH | HIGH | 7.8 | P4, P30 | Validates Tailscale for remote access (already in A01). Gateway = centralized routing with secure defaults |
| S22.04 | **Multi-agent routing** — Different messaging channels route to isolated agent instances via workspaces and per-agent sessions. Specialization and isolation by design. Each agent has own session, own context | `ARCH` | HIGH | HIGH | 7.6 | P4, P42 | This IS our dual-agent architecture (Personal vs BB). Different channels → different specialized agents. Production-validated |
| S22.05 | **13 messaging platform adapters** — WhatsApp (Baileys), Telegram (grammY), Discord (discord.js), Slack, Signal, iMessage, BlueBubbles, Microsoft Teams, Matrix, Google Chat, Zalo, WebChat. Each with dedicated adapter | `COMMS` `TOOLS` | HIGH | HIGH | 7.0 | -- | ATLAS has 0 messaging adapters. Phase 1 plan = Telegram bridge. OpenClaw proves 13 is feasible from a single codebase |

### Security & Isolation

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S22.06 | **Per-session Docker sandboxes** — Non-main sessions (groups/channels) run inside Docker containers. Allowlist safe tools (bash, read, write, sessions_*). Denylist sensitive tools (browser, canvas, cron, gateway) | `SECURITY` | HIGH | HIGH | 8.0 | P4, P30, P44 | Production implementation of P4+P30+P44. Tool allowlists at container level. ATLAS should adopt for untrusted contexts |
| S22.07 | **DM access control (pairing)** — Unknown senders receive a short code. Bot doesn't process messages until approved. Public inbound requires explicit opt-in (dmPolicy="open"). Default DENY | `SECURITY` | HIGH | HIGH | 7.5 | P30 | Exactly P30 (allowlist-only). ATLAS Telegram bridge should use same pattern — approval before processing |
| S22.08 | **Tool access control via TCC** — macOS Transparent Consent & Control for sensitive operations. Distinguishes "host permissions" (elevated bash) from device permissions (camera, location, screen recording) | `SECURITY` | MEDIUM | HIGH | 6.8 | P44 | Permission tiers beyond just tool allowlists. Device-level access control. Relevant for ATLAS desktop deployment |

### Agent Lifecycle & Memory

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S22.09 | **Injected prompt files shape agent behavior** — AGENTS.md (agent definitions), SOUL.md (personality/values), TOOLS.md (available capabilities). Dropped into workspace, auto-loaded. Modular prompt assembly in practice | `ARCH` | HIGH | HIGH | 7.4 | P45, P50 | Exactly P45. Our CLAUDE.md is monolithic. OpenClaw splits into AGENTS/SOUL/TOOLS. Maps to plugin architecture (P50) — skills + commands separated |
| S22.10 | **Session-based multi-agent coordination** — sessions_list (discover active), sessions_history (fetch transcripts), sessions_send (message another session with optional reply-back). Agents coordinate without shared context window | `ARCH` | HIGH | HIGH | 7.6 | P4 | Inter-agent communication via message passing, not shared context. Prevents context contamination (S20 lesson). Better than our ScratchPad approach |
| S22.11 | **Model failover with profile rotation** — Anthropic (Opus 4.5 recommended), OpenAI, local models. Profile rotation between OAuth and API keys. Fallback chains when primary model fails | `ARCH` `COST` | HIGH | HIGH | 7.3 | P13, P43 | Production fallback chains as described in P43. OpenClaw already implements what we have in A09 (formalize fallback chains) |
| S22.12 | **Context compaction** — /compact command creates summaries, reducing token overhead for long conversations. Session pruning for context management | `MEMORY` | MEDIUM | HIGH | 6.5 | P46 | Similar to our context summarization. Not as sophisticated as FSRS-6 decay but pragmatic for session persistence |

---

## Patterns Identified

**No new patterns.** OpenClaw is a production implementation of patterns already in our index. What's significant is the QUANTITY of patterns validated in a single production system:

| OpenClaw Feature | Pattern Validated | Status |
|-----------------|-------------------|--------|
| Per-session Docker sandboxes | P4 (Isolation = Safety) | Production-validated |
| Tool allowlists/denylists | P30 (Allowlist-Only), P44 (Tool-Level Access Control) | Production-validated |
| DM pairing/approval | P30 (Allowlist-Only) | Production-validated |
| Model failover chains | P13 (Hybrid Routing), P43 (Circuit Breaker + Fallback) | Production-validated |
| AGENTS.md/SOUL.md/TOOLS.md | P45 (Modular Prompt Assembly) | Production-validated |
| Skills framework | P50 (Plugin Architecture) | Production-validated |
| Multi-agent routing by channel | P42 (Privacy as Routing Constraint) | Production-validated |
| Session-based coordination | P4 (Isolation), P53 (context isolation from S20) | Production-validated |

**8 patterns validated in one production system.** This is the highest pattern density of any source in the index.

---

## Action Items

| ID | Action | Priority | Status | Depends On | Rationale |
|----|--------|----------|--------|------------|-----------|
| A65 | Evaluate OpenClaw as reference architecture for ATLAS multi-platform messaging — study 13 adapter implementations for Telegram bridge (Phase 1) | P1 | TODO | -- | OpenClaw proves 13 platforms from one codebase. Our Phase 1 = just Telegram. Study their grammY adapter |
| A66 | Study OpenClaw's AGENTS.md/SOUL.md/TOOLS.md split as model for decomposing CLAUDE.md (already in A26) | P2 | TODO | A26 | Three-file split is cleaner than our monolithic CLAUDE.md. Aligns with A26 and plugin architecture (A53) |
| A67 | Evaluate OpenClaw Agent Canvas UI as reference for ATLAS multi-agent dashboard — could replace/extend OSRS Command Centre | P2 | TODO | -- | As ATLAS adds more agents (BB, health, memory sub-agents), terminal output becomes unmanageable. Visual dashboard needed |

---

## Cross-References

| This Source | Connects To | Relationship |
|-------------|-------------|-------------|
| S22.01 (Agent Canvas UI) | ATLAS Command Centre (scripts/atlas_launcher.py) | ATLAS has single-agent health UI. OpenClaw has multi-agent orchestration UI. Different scope but same insight: agents need visual oversight |
| S22.04 (multi-agent routing) | Handoff.md (dual-agent architecture) | OpenClaw's channel→agent routing IS our Personal Agent vs BB Agent plan. They've implemented it |
| S22.06 (Docker sandboxes) | S16 (BrainPro tool ACLs, P44) | S16 proposed tool-level access control. OpenClaw implements it at container level with allowlist/denylist |
| S22.09 (prompt file injection) | S18 (plugin architecture, P50) | OpenClaw's AGENTS.md/SOUL.md/TOOLS.md = Cowork's skills/commands. Same modular prompt pattern, different naming |
| S22.10 (session coordination) | S20 (Context Ray Tracing, P53) | Both solve same problem: agents coordinating without sharing full context. OpenClaw uses message passing; S20 uses FSM-controlled visibility |
| S22.11 (model failover) | S16 (fallback chains, P43), A09 | OpenClaw already implements A09 (formalize fallback chains). Study their implementation |
| S22.03 (Tailscale gateway) | S13 (security hardening), A01 | Both recommend Tailscale. OpenClaw uses Tailscale Serve/Funnel for remote gateway access |

---

## Credibility Assessment

| Dimension | Score (1-10) | Notes |
|-----------|-------------|-------|
| Author expertise | 8 | Open-source team, 9.7k GitHub stars on main repo, production users across 13 platforms |
| Evidence quality | 8 | Running production code, not theory. Docker sandbox configs, adapter implementations, gateway architecture all verifiable |
| Recency | 9 | Active development January 2026. Agent Canvas UI is brand new |
| Reproducibility | 9 | Fully open-source, documented setup, works on macOS/Linux/WSL2 |
| Bias risk (10=none) | 7 | Open-source project, no commercial product. Some marketing ("personal AI assistant") but code is verifiable |
| **Composite** | **8** | |

### Strengths
- Production-validated: 13 messaging adapters, Docker sandboxes, model failover — all running code
- Validates 8 patterns from our index in a single system (highest pattern density)
- Directly comparable to ATLAS: local-first, personal assistant, multi-agent, voice+chat
- Agent Canvas UI solves a real pain point (terminal-based agent oversight is terrible)
- Security-conscious: DM pairing, tool allowlists, sandbox isolation, Tailscale

### Weaknesses
- Agent Canvas UI is v1 (124 stars vs 9.7k for main repo) — early and likely rough
- No performance benchmarks (latency, resource usage with 13 adapters)
- Architecture documentation is sparse in places (MCP integration details missing)
- Unclear how well it handles the adversarial agent scenarios S20 warns about
- Not clear if opposing incentives / critic patterns are implemented (just isolation)

---

## Noise Filter

- Naming history (Clawdbot → Moltbot → OpenClaw) — noted once, not repeated
- Specific adapter library choices (Baileys, grammY, etc.) — noted in items, not individually assessed
- Discord integration details for Agent Canvas UI — platform-specific, not architectural
- Individual messaging platform setup guides — operational, not architectural

---

## Verification Checklist

- [x] **Fact-Check**: 13 messaging adapters verified in GitHub source code. Docker sandbox configuration verified in repo. WebSocket gateway architecture verified. Model failover confirmed in config schema. DM pairing flow documented.
- [x] **Confidence Extraction**: All items HIGH confidence — verified against running code. No speculative claims.
- [x] **Wait Pattern**: "What assumptions am I making?" — Assuming production quality from star count (9.7k). Stars != quality. Assuming adapters all work reliably (some may be experimental). Assuming Agent Canvas UI is usable (v1, only 124 stars).
- [ ] **Inversion Test**: S22.06 (Docker sandboxes, 8.0): "What would make this wrong?" — If Docker overhead makes latency unacceptable for voice pipeline (<1.8s target). If sandbox escape vulnerabilities exist (Docker is generally secure but not impenetrable). Risk: LOW for non-voice contexts, MEDIUM for voice.

---

*S22 processed: 2026-01-31*
