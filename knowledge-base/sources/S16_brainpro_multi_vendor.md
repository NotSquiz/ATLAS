# S16: BrainPro — Multi-Vendor Agentic Coding Assistant (Rust)

**Source:** https://github.com/jgarzik/brainpro + X.com post by Jeff Garzik (@jgarzik)
**Author:** Jeff Garzik (Bitcoin Core developer, veteran systems programmer)
**Date:** January 2026
**Type:** Open-source agentic coding assistant with production-grade architecture
**Distinction:** Written in Rust by a serious systems engineer. Not a demo or wrapper — a fully architected agent platform with circuit breakers, privacy tiers, fallback chains, permission policies, and Docker deployment. The most security-conscious agent implementation we've seen.

### Core Architecture

Two modes: **MrCode** (direct CLI `yo`, 7 coding tools) and **MrBot** (gateway daemon, 12+ tools, remote access via WebSocket). Personas define identity through modular prompt assembly. Multi-vendor LLM backends via OpenAI-compatible API standardization.

### Extracted Items

#### A. Multi-Vendor Model Routing

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 243 | **Task-based model routing**: Keyword detection routes to optimal model — planning→Qwen, coding→Claude, exploration→GPT-4o-mini. Configurable via TOML | `ARCH`, `COST` | HIGH | Implements S4 Role Allocation Framework in code. Each task category gets the right model for cost/quality tradeoff |
| 244 | **Backend registry with lazy loading**: `model@backend` targeting (e.g., `claude-3-5-sonnet@claude`). All backends standardize on OpenAI `/v1/chat/completions` format | `ARCH`, `TOOLS` | HIGH | Clean abstraction: swap providers without changing agent logic. We should adopt this target format |
| 245 | **Fallback chains**: Primary → secondary → local automatic failover. Category-specific overrides (coding always tries Claude first). Triggers on circuit breaker open, 429, 5xx | `ARCH`, `SECURITY` | HIGH | Production resilience pattern we lack. Our Haiku fallback to Ollama is informal — BrainPro formalizes it |

#### B. Privacy & Zero Data Retention

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 246 | **Three privacy levels**: `standard` (any provider), `sensitive` (prefer ZDR, warn otherwise), `strict` (ZDR-only, fail if unavailable) | `SECURITY` | HIGH | Formalizes S3's data sovereignty concept. Privacy as a first-class routing constraint, not an afterthought |
| 247 | **Sensitive pattern auto-escalation**: Prompts containing `password`, `secret`, `api_key`, `token`, `ssn`, `credit_card`, PEM markers auto-escalate to strict privacy | `SECURITY` | HIGH | Automatic security — agent detects sensitive content and routes to ZDR providers without user intervention |
| 248 | **ZDR registry per backend**: Venice=ZDR, Ollama=ZDR (local), Claude=ZDR, OpenAI=not ZDR. Provider privacy is metadata, not assumption | `SECURITY`, `ARCH` | HIGH | Each provider explicitly declares data retention policy. Routing decisions respect this |
| 249 | **SecretString with zeroize-on-drop**: API keys wrapped in type that zeros memory on deallocation. Never logged, never serialized | `SECURITY` | HIGH | Rust-level memory safety for credentials. We can't do this in Python but should use equivalent patterns (del + gc) |

#### C. Permission System & Policy Engine

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 250 | **Three permission modes**: `default` (read-only free, writes need approval), `acceptEdits` (file mutations OK, bash needs approval), `bypassPermissions` (all allowed, trusted only) | `SECURITY` | HIGH | Graduated permission model. Maps to our sandbox configs but more granular |
| 251 | **Pattern-matched permission rules**: Allow/ask/deny with patterns — `"Bash(git:*)"`, `"Bash(npm install)"`, `"mcp.server.*"`. Rules match in order | `SECURITY` | HIGH | Specific command-level permissions. Our sandbox configs should adopt this pattern syntax |
| 252 | **Built-in protections**: curl/wget blocked by default, file paths validated to project root, symlinks resolved to prevent escape | `SECURITY` | HIGH | Defense in depth. These are the exact mitigations S13 called for — but implemented at the agent level, not the OS level |
| 253 | **Subagent tool restrictions**: Each subagent in `.brainpro/agents/<name>.toml` declares `allowed_tools` list. Scout agent gets Read/Grep/Glob only | `SECURITY`, `ARCH` | HIGH | Our `.claude/agents/` use prompt instructions for restrictions. BrainPro enforces restrictions at the tool access level — much stronger |

#### D. Resilience Architecture

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 254 | **Circuit breaker pattern**: Closed → Open (5 failures) → HalfOpen (probe with 3 requests) → Closed. Prevents cascading failures to unhealthy backends | `ARCH`, `SECURITY` | HIGH | S14 Pattern 38 (OWASP ASI08) implemented in code. We need this for Garmin API, USDA API, and LLM backends |
| 255 | **Provider health tracking**: Healthy → Degraded (high latency) → Unhealthy (consistent failures, cooldown). Sliding-window latency averages | `ARCH` | HIGH | Sophisticated monitoring. Our GarminService has basic retry but no health state tracking |
| 256 | **Exponential backoff with jitter**: 1s initial, 60s max, ±30% randomization. Respects Retry-After headers on 429s | `ARCH` | MEDIUM | Standard resilience pattern. Our API calls should adopt this |

#### E. Persona & Skill System

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 257 | **Modular prompt assembly**: identity.md → soul.md → tooling.md → plan-mode.md → optimize.md. Assembled in order per persona | `ARCH` | HIGH | Clean prompt engineering. Our CLAUDE.md is monolithic. BrainPro decomposes into composable layers |
| 258 | **Skill packs**: Reusable instruction sets in `.brainpro/skills/<name>/SKILL.md` with YAML frontmatter declaring allowed tools. Activated/deactivated at runtime | `TOOLS`, `ARCH` | HIGH | Like our skills in ATLAS but with tool-level restrictions. A "secure-review" skill only gets Read/Grep/Glob |
| 259 | **Custom slash commands**: `.brainpro/commands/<name>.md` with YAML frontmatter + `$ARGUMENTS` template substitution. Define workflow in markdown | `TOOLS`, `WORKFLOW` | HIGH | S15's custom commands pattern, fully formalized. We should adopt this format for ATLAS commands |

#### F. Observability & Audit

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 260 | **JSONL session transcripts**: Every event logged — messages, tool calls, results, permissions, subagent lifecycles, skill activations, errors. Full audit trail | `SECURITY` | HIGH | Complete observability. Our `SessionBuffer` discards after 10 min. BrainPro keeps everything for audit |
| 261 | **Prometheus metrics**: Request totals/duration by backend/model/status, circuit breaker trips, token counts, USD cost tracking. JSON export for non-Prometheus setups | `COST`, `TOOLS` | MEDIUM | Cost and performance monitoring. We track nothing about our API usage currently |
| 262 | **Event protocol**: Thinking → ToolCall → ToolResult → Content → Done → Yield (paused for approval) → Error. WebSocket streaming for real-time UI | `ARCH`, `UX` | HIGH | Maps to our voice bridge event model (status.txt = ready/processing/done). BrainPro's is more granular |

### Key Patterns from S16

**Pattern 42: Privacy as a Routing Constraint (Not an Afterthought)**
BrainPro treats data privacy as a first-class model routing dimension. Three tiers (standard/sensitive/strict) determine which backends can be used. Sensitive content auto-escalates — prompts with passwords or API keys automatically route to ZDR-only providers. This formalizes S3's "data sovereignty" into a concrete implementation pattern. Our model router should incorporate privacy tiers.

**Pattern 43: Circuit Breaker + Fallback Chain = Production Resilience**
Circuit breakers prevent hammering failed services. Fallback chains route to alternatives when primary fails. Category overrides ensure critical paths (coding→Claude) get the right fallback. This is the missing resilience layer in ATLAS — our Garmin API, USDA API, and LLM backends all need this.

**Pattern 44: Tool-Level Access Control > Prompt-Level Instructions**
BrainPro enforces subagent restrictions at the tool access level — a scout agent literally cannot call Write, regardless of what the prompt says. Our `.claude/agents/` rely on prompt instructions ("You should only read files"), which agents can ignore. Tool-level enforcement is fundamentally stronger.

**Pattern 45: Modular Prompt Assembly (Composable Persona Layers)**
Instead of one monolithic system prompt, BrainPro assembles prompts from composable files: identity → soul → tooling → mode. This enables mixing and matching personality, tool access, and operational mode. Our CLAUDE.md is a single large file — decomposing it would improve maintainability and enable per-task prompt customization.

### Cross-References

| S16 Item | Connects To | Relationship |
|----------|-------------|-------------|
| Task-based model routing (#243) | S4 Role Allocation Framework | BrainPro implements our theoretical framework in Rust code |
| Privacy levels (#246) | S3 Pattern 10 (Data sovereignty) | Formalizes data sovereignty as routing constraint |
| ZDR registry (#248) | S3 local hardware argument | Local/ZDR backends preferred for private data |
| Sensitive auto-escalation (#247) | S13 Pattern 28 (Security before features) | Automatic security enforcement — no user action needed |
| Permission rules (#251) | S13 hardening checklist | Agent-level security complementing OS-level hardening |
| Circuit breaker (#254) | S14 Pattern 38 (OWASP ASI08) | Implementation of cascading failure prevention |
| Fallback chains (#245) | S4 Role Allocation (local → API) | Formal version of our informal Haiku → Ollama fallback |
| Subagent restrictions (#253) | S14 #212 (Five generic roles) | Each role gets precisely the tools it needs, no more |
| Modular prompts (#257) | S6 Pattern 14 (Passive context) | Composable context assembly is structured passive context |
| Skill packs (#258) | S15 custom commands (#230) | Same concept (reusable workflows), stronger enforcement |
| JSONL transcripts (#260) | S8 Pattern 21 (humans optimize safety) | Audit trail enables human oversight of agent behavior |
| Event protocol (#262) | Our voice bridge status.txt | Same pattern (state machine events), more granular |
| Prometheus metrics (#261) | S4 cost awareness | Cost tracking as operational requirement |
| Custom commands (#259) | S15 Pattern 40 (single-trigger) | Formalized with YAML frontmatter + tool restrictions |

### Action Items from S16

| Priority | Action | Rationale |
|----------|--------|-----------|
| **HIGH** | Implement circuit breaker for Garmin, USDA, and LLM APIs | Pattern 43: We have no resilience against API failures. BrainPro's pattern is production-proven |
| **HIGH** | Add privacy tiers to model routing | Pattern 42: Health data (Garmin, pain logs) should auto-route to ZDR/local providers |
| **HIGH** | Implement tool-level restrictions for our `.claude/agents/` | Pattern 44: Prompt instructions are not enforcement. Need actual tool access controls |
| **HIGH** | Formalize fallback chains: Claude → Haiku → Ollama with category overrides | Item #245: Our informal fallback should be configured, not hardcoded |
| **MEDIUM** | Decompose CLAUDE.md into modular prompt components | Pattern 45: identity → conventions → tools → mode. Composable > monolithic |
| **MEDIUM** | Add JSONL session logging for agent audit trail | Item #260: We discard session context after 10 min. Should persist for review |
| **MEDIUM** | Implement cost tracking (token counts, USD per backend) | Item #261: We track zero about our API spend. Need Prometheus or JSON export |
| **MEDIUM** | Adopt `.brainpro/commands/` pattern for custom ATLAS commands | Item #259: Formalized slash commands with YAML frontmatter + tool restrictions |
| **LOW** | Study BrainPro's Rust implementation for daemon mode design | Phase 2: Their gateway architecture (WebSocket → Unix socket → agent daemon) is relevant |
| **LOW** | Evaluate sensitive pattern detection for our voice pipeline | Item #247: Auto-detect when user says something sensitive and route accordingly |

### Credibility Assessment

**Source Quality: 9/10**
Jeff Garzik is a Bitcoin Core developer and veteran systems programmer. The architecture reflects deep experience with production systems — circuit breakers, fallback chains, privacy tiers, permission engines, audit trails. The Rust implementation provides memory safety guarantees. Comprehensive DESIGN.md and USERGUIDE.md demonstrate serious engineering discipline.

**Strengths:**
- Production-grade architecture from a systems programming veteran
- Security-first: privacy tiers, permission policies, sensitive auto-escalation, SecretString, path validation
- Resilience: circuit breaker, fallback chains, health tracking, exponential backoff
- Observability: JSONL transcripts, Prometheus metrics, cost tracking
- Clean abstractions: model@backend targeting, modular prompt assembly, composable skill packs
- Docker deployment with volume persistence and secrets management
- Multi-vendor neutrality — not locked to any single LLM provider

**Weaknesses:**
- Still early stage ("Core engine working, UI still basic stdin REPL" per the X.com post)
- No voice pipeline or real-time interaction patterns
- No memory/persistence layer beyond session transcripts
- Rust is harder to extend than Python for rapid prototyping
- No community ecosystem yet (contrast with Moltbot/LobeHub)
- MrBot persona seems basic compared to full Moltbot personality system

**Overall:** The most architecturally mature agent implementation in this knowledge base. While Moltbot/LobeHub (S2) has community and ecosystem, and Claude Code (S15) has workflow patterns, BrainPro has the strongest **infrastructure engineering**: circuit breakers, fallback chains, privacy tiers, permission policies, audit trails. This is what a production agent looks like under the hood. We should study its patterns closely for ATLAS Phase 2 (daemon mode) and Phase 3 (model router). The privacy-as-routing-constraint pattern (Pattern 42) and circuit breaker pattern (Pattern 43) should be among the first things we implement.

---

*S16 processed: January 30, 2026*

---
