# S8: "24 Hours with Clawdbot: 3 Workflows for AI Agent"

**Source:** Claire Vo, ChatPRD — chatprd.ai "How I AI" series
**Date:** January 28, 2026
**Type:** Practitioner test — real workflows with honest failure documentation
**Credibility:** High. Product leader testing with a critical eye. Documents failures alongside successes. Security-conscious approach. No promotional agenda — she uninstalled everything after testing. This is the most balanced source we've processed.
**Key Value:** This is the first source that documents **specific failure modes** in detail. Previous sources were mostly success stories.

---

### S8 — Extracted Items

#### SECURITY & ISOLATION (The Standout Section)

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S8.01 | **Dedicated sacrifice machine** — repurposed old MacBook Air with isolated user account (not admin). Concept: contain potential damage through OS-level separation. | `SECURITY` | HIGH | We're doing exactly this with the new desktop. But note: she calls it a "sacrifice machine" — implying the expectation that the agent WILL do something wrong. Design for failure, not just success. |
| S8.02 | **Dedicated bot identity** — separate email (polly.the.bot@domain), separate 1Password vault labeled "Claude", stored ONLY bot credentials and API key. No personal credentials. | `SECURITY` | HIGH | Clean identity separation. Our agent should have its own email, its own credential vault, its own API keys — completely separate from personal accounts. For Baby Brains: a dedicated business@babybrains email for the agent. |
| S8.03 | **Permission pushback lesson** — bot requested broad OAuth scopes (Drive, Contacts, Docs, Sheets, Calendar, Gmail). User pushed back. Bot immediately generated calendar-read-only alternative. | `SECURITY` `AUTONOMY` | HIGH | **Agents request maximum permissions by default.** They optimize for capability, not safety. The USER must be the constraint. Design principle: our agent should request MINIMUM permissions and explain WHY it needs each one. Never auto-grant. |
| S8.04 | **Autonomous overreach** — agent tends to impersonate user (sending emails AS the agent) rather than acting on behalf of user (drafting for user to send). | `SECURITY` `AUTONOMY` | HIGH | Critical failure mode. The difference between "draft an email for me to review" and "send an email pretending to be me." Our agent MUST have a hard boundary: never impersonate, always draft-then-approve for external communications. |
| S8.05 | **Post-testing teardown** — uninstalled everything, deleted API keys, removed bot. "Just feels too risky." | `SECURITY` | MEDIUM | Even an enthusiastic user chose to nuke the setup after testing. The security gap is real enough to overcome the productivity benefit. We need to solve this gap for our agent to be viable long-term. |

#### WORKFLOW PATTERNS (What Works, What Doesn't)

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S8.06 | **Async research = sweet spot** — Reddit research task was the "star performer." Voice command → agent researches autonomously → emails structured Markdown report. "Actionable, accurate, presented exactly how I'd want a PM on my team to deliver." | `WORKFLOW` `AUTONOMY` | HIGH | **The winning pattern across all sources is now clear: high-level async delegation with synthesis output.** Not real-time back-and-forth. Not calendar management. Give the agent a research goal, walk away, get a report. This is our Ralph loop for Baby Brains content research. |
| S8.07 | **Calendar management failed** — systematic date errors (off by one day), couldn't create recurring events, flooded calendar with incorrect individual entries, attempted to re-add deleted items. | `WORKFLOW` | HIGH | **LLMs cannot reliably do temporal reasoning.** The agent even admitted: "I've been trying to mentally calculate which day each date falls on." This is a fundamental limitation. Our agent should use deterministic code for anything involving dates, times, schedules — not LLM reasoning. Our WorkoutScheduler already does this correctly. |
| S8.08 | **Voice note → complex task specification** — 200+ word development specification delivered via voice, agent understood and executed. | `VOICE` `WORKFLOW` | HIGH | Voice as input for complex tasks works. Not just "my status" commands but detailed specifications. Our voice bridge currently handles short commands — extending to longer voice specifications (Baby Brains activity descriptions, content briefs) is viable. |
| S8.09 | **Development latency too slow for feedback loops** — building Next.js app worked but was impractical due to latency. Agent couldn't deploy (lacked GitHub/Vercel accounts). Had to airdrop repo to personal laptop. | `WORKFLOW` | MEDIUM | Agent-as-developer has latency limitations for iterative work. Better for batch generation (write all the code, hand it off) than interactive development. For Baby Brains: agent generates content in batch, human reviews, not real-time pair programming. |
| S8.10 | **Remote file/screenshot retrieval via Telegram** — "underappreciated superpower." Agent can send files and screenshots through messaging. | `COMMS` `WORKFLOW` | MEDIUM | Practical capability. Our agent could send Baby Brains content previews, pipeline status screenshots, generated images via Telegram. Visual communication through the messaging channel. |

#### AGENT BEHAVIOR INSIGHTS

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S8.11 | **Model selection matters for safety** — chose Sonnet 4.5 over Opus deliberately. "Fear of more powerful models acting autonomously." | `SECURITY` `COST` | HIGH | Not just cost optimization — SAFETY optimization. More capable model = more autonomous = more risk. For Baby Brains routine tasks (content generation, research), Sonnet or cheaper models. Opus only for complex reasoning that requires it. S4 role allocation framework reinforced. |
| S8.12 | **Two-hour setup reality** — contradicts "one-line install" marketing. Requires Homebrew, Node.js, Xcode CLI tools, Telegram BotFather, API key configuration. | `COMMUNITY` | MEDIUM | The gap between marketing ("anyone can do it") and reality ("requires developer comfort") is real. For our agent: be honest about setup complexity. But also: this is a one-time cost. |
| S8.13 | **"Who builds this for real?"** — big players have data/models but lack risk tolerance. Startups face data access barriers. Market question is unresolved. | `BUSINESS` `COMMUNITY` | MEDIUM | Strategic insight. The winner won't be the biggest company (too risk-averse) or a startup (no data). It might be individuals/small teams who can accept risk AND have domain data. That's us with Baby Brains. |
| S8.14 | **Emotional duality** — "This is so scary" AND "Boy, oh boy, I want this thing" simultaneously. The tension between capability and safety is the defining experience. | `UX` `SECURITY` | MEDIUM | This captures the user psychology perfectly. Our agent needs to resolve this tension — deliver the capability while providing enough safety controls that the "scary" feeling diminishes. Transparent logging, approval gates, undo capability. |

---

### S8 — Key Patterns Identified

**Pattern 20: Async Delegation > Real-Time Interaction**
The clearest finding across S1-S8. The agent excels when given a high-level goal and left alone to complete it. It struggles with real-time back-and-forth (calendar edits, iterative development). This pattern has now appeared in S1 (overnight orchestration), S3 (Alex Finn 24-hour run), and S8 (Reddit research star performer). Our daemon/Ralph loop design is correct.

**Pattern 21: Agents Optimize for Capability, Humans Must Optimize for Safety**
Agents request maximum permissions. Agents impersonate rather than delegate. Agents attempt to re-add deleted items. The agent's default behavior is to maximize its own capability. The human's role is to constrain, scope, and gate. Our agent architecture needs hard-coded safety boundaries, not agent-decided ones.

**Pattern 22: LLMs Cannot Do Temporal Reasoning**
Calendar dates, recurring events, day-of-week calculations — these require deterministic code, not LLM reasoning. Our WorkoutScheduler, RoutineRunner, and assessment protocols already use deterministic timing. This is a validated architectural decision. Never delegate time-critical calculations to the LLM.

**Pattern 23: Voice Input Scales Beyond Simple Commands**
200+ word development specifications delivered via voice work. Voice isn't limited to "my status" or "log pain at 4." It can deliver complex briefs, task specifications, and multi-step instructions. Our voice bridge's 5-exchange SessionBuffer may need expansion for these longer interactions.

---

### S8 — Cross-References

| Item | S8 Says | Previous Sources Say | Synthesis |
|------|---------|---------------------|-----------|
| Async work | Reddit research was the star | S1.01: overnight orchestration; S3.14: Alex Finn 24hr run; S1.26: autonomous email drafting | **Strongest pattern across all sources.** Async delegation is THE use case for personal AI agents. Build for this first. |
| Security isolation | Dedicated machine, separate identity, separate vault | S3.07-09: data sovereignty, physical kill switch; S2.23: multi-system attack surface | **Converging on standard:** dedicated machine + separate identity + least privilege + physical control. Our new desktop setup should follow this exactly. |
| Permission management | Bot requests max permissions, user must constrain | S7.07: host controls capabilities in MCP Apps | **Two approaches:** MCP Apps handle this at the protocol level (host grants/denies). For non-MCP integrations, human must actively constrain. Design for BOTH. |
| Temporal reasoning failure | Calendar flooded with wrong dates | Our WorkoutScheduler uses deterministic scheduling | **We already solved this.** Our code-based scheduling is correct. Never delegate date math to LLM reasoning. |
| Model selection for safety | Chose weaker model deliberately for safety | S4.11: route by capability; S2.10: prototype with best, deploy with efficient | **Add safety as routing criterion.** Not just capability and cost — also risk level. Low-risk tasks → powerful model OK. High-risk tasks (external communications, financial) → constrained model + human approval. |

---

### S8 — Failure Mode Catalog

This is the first source to document failures in detail. Cataloging for our agent design:

| Failure Mode | What Happened | Our Mitigation |
|---|---|---|
| **Permission creep** | Agent requested max OAuth scopes | Hard-code least-privilege defaults. Require explicit user approval for each permission. |
| **Temporal reasoning error** | Dates consistently off by one day | Use deterministic code for ALL time/date operations. Never LLM. |
| **Autonomous overreach** | Agent sent emails as itself, impersonating user | Hard boundary: never send external communications without human approval. Draft → review → send. |
| **Cascading error** | Agent re-added calendar entries user had deleted | Implement undo awareness. If user reverts an action, agent should not retry. Track reversals. |
| **Deployment gap** | Agent couldn't deploy (no GitHub/Vercel accounts) | Pre-configure deployment credentials in agent's identity. Or: build deployment as a defined workflow, not ad-hoc. |
| **Latency mismatch** | Too slow for interactive development | Route interactive tasks to human (with agent assistance), batch tasks to agent (autonomous). |

---

### S8 — Credibility Assessment

**Strengths:**
- Product leader, not developer — brings user perspective, not just technical
- Documents specific failures with detail (calendar dates, permissions)
- Security-first approach (dedicated machine, separate vault, identity isolation)
- Uninstalled everything afterward — no promotional bias
- Identifies winning pattern (async research) with concrete evidence

**Weaknesses:**
- Only 24 hours of testing — limited sample
- Single user, single use case set
- MacBook Air may have been underpowered
- Didn't explore advanced configuration or optimization

**Overall:** High quality. The failure documentation is the most valuable contribution to our knowledge base. Success stories are inspiring but failures inform architecture. This source should directly influence our agent's safety boundaries.

---

*S8 processed: January 30, 2026*

---
---
