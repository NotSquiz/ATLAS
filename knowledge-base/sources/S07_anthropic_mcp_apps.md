# S7: Interactive Tools in Claude + MCP Apps Extension

**Source:** Anthropic blog (claude.com/blog/interactive-tools-in-claude) + MCP specification (modelcontextprotocol.io/docs/extensions/apps)
**Date:** January 26, 2026
**Type:** Platform announcement + full technical specification for MCP Apps (first official MCP extension)
**Credibility:** Maximum. This is the protocol creator's own specification. Anthropic sets the standard here.

**User's observation:** Anthropic are arguably the leaders, but open source and smaller teams provide opportunity for experimentation. Both are correct. Anthropic defines the protocol layer (MCP) — but the VALUE is in domain-specific implementations built on top of it. That's our opportunity.

---

### S7 — What MCP Apps Are

MCP Apps extend the Model Context Protocol to allow tools to return **interactive UI** (not just text) that renders inside the AI conversation. Dashboards, forms, visualizations, multi-step workflows — all inside the chat window.

```
Traditional MCP:  User → Agent → Tool → Text Response
MCP Apps:         User → Agent → Tool → Interactive UI (sandboxed iframe)
                                         ↕ bidirectional data flow
                                        User interacts directly
```

**Technical flow:**
1. Tool declares a `ui://` resource containing HTML interface
2. Host (Claude, VS Code, etc.) preloads the UI resource
3. Tool gets called → host fetches resource → renders in sandboxed iframe
4. App communicates with host via JSON-RPC over postMessage
5. App can call server tools, update model context, trigger follow-up messages

---

### S7 — Extracted Items

#### ARCHITECTURE & PROTOCOL

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S7.01 | **MCP Apps = interactive UI inside AI conversations** — first official MCP extension. Tools return HTML/JS that renders in sandboxed iframe. | `ARCH` `TOOLS` | HIGH | Paradigm shift from text-only to interactive. For Baby Brains: imagine asking "show me the activity for tummy time" and getting an interactive card with images, video embeds, age ranges, modification options — all inside the conversation. |
| S7.02 | **Build once, deploy across multiple AI platforms** — open standard. Works in Claude, Claude Desktop, VS Code, Goose, Postman, ChatGPT (coming). | `ARCH` | HIGH | This is the interoperability argument. We build a Baby Brains MCP App ONCE and it works everywhere. Not locked into any single AI platform. If we invest in MCP Apps, the work is portable. |
| S7.03 | **Bidirectional data flow** — app can call any tool on the MCP server, host can push fresh results to the app. No separate API/auth needed. | `ARCH` | HIGH | The app inherits the server's capabilities. A Baby Brains activity viewer app could call the knowledge base, the quality checker, the content generator — all through the MCP server it's attached to. No separate API to build. |
| S7.04 | **`ui://` resource protocol** — tools declare UI resources that hosts fetch and render. Server registers tool with `_meta.ui.resourceUri` metadata. | `ARCH` `TOOLS` | MEDIUM | Technical detail for implementation. The `ui://` scheme is the convention. |
| S7.05 | **SDK: `@modelcontextprotocol/ext-apps`** — TypeScript SDK with `App` class for UI-to-host communication. Framework templates for React, Vue, Svelte, Preact, Solid, vanilla JS. | `TOOLS` | HIGH | Ready to use. We can scaffold MCP Apps with any framework we're comfortable with. The SDK handles postMessage, tool calls, context updates. |

#### SECURITY

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S7.06 | **Sandboxed iframe isolation** — app cannot access parent window DOM, cookies, local storage, or navigate parent page. All communication via auditable JSON-RPC postMessage. | `SECURITY` | HIGH | Strong security model. Third-party MCP Apps can't escape their container. This addresses our R31 concern about malicious skills. MCP Apps are inherently safer than full-access skills because they're sandboxed. |
| S7.07 | **Host controls capabilities** — the host (Claude, VS Code) controls which tools an app can call and what capabilities it has. CSP controls external resource loading. | `SECURITY` | HIGH | Principle of least privilege built into the protocol. The app declares what it needs, the host grants or denies. This is the security model we want for our agent. |
| S7.08 | **Pre-declared templates + auditable messages** — security layers include pre-declared HTML templates, JSON-RPC audit trail, host-managed approvals for UI-initiated tool calls. | `SECURITY` | MEDIUM | Defense in depth. Multiple security layers, not just one sandbox. |

#### PRACTICAL CAPABILITIES

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S7.09 | **Launch partners: Asana, Slack, Figma, Canva, Amplitude, Box, Hex, monday.com, Salesforce** — immediate real-world integrations. No additional charge on paid Claude plans. | `TOOLS` `WORKFLOW` | MEDIUM | The specific partners matter less than the pattern: project management, communication, design, analytics, data — all accessible from within Claude. For our agent: we could build Baby Brains-specific interactive tools in the same way. |
| S7.10 | **Example apps available** — 3D visualization (Three.js, CesiumJS maps), data exploration (cohort heatmaps, customer segmentation), business apps (scenario modeler, budget allocator), media (PDF viewer, video, sheet music, TTS), utilities (QR codes, system monitor, speech-to-text). | `TOOLS` | HIGH | The system-monitor example is essentially what our Command Centre UI does. The transcript-server (STT) and say-server (TTS) overlap with our voice pipeline. These are reference implementations we can learn from or adapt. |
| S7.11 | **Context preservation** — app lives inside the conversation. No tab switching, no lost context. UI alongside the discussion that led to it. | `UX` | HIGH | This is the UX argument. Instead of: "go to this dashboard → find the thing → come back and tell me" — the dashboard IS the conversation. For health tracking: ask about your status, get an interactive dashboard right there. |
| S7.12 | **Integration with host capabilities** — app can delegate actions to the host, which routes through user's connected tools. No per-app integrations needed. | `ARCH` `WORKFLOW` | MEDIUM | "Schedule this meeting" → host routes to user's calendar, not the app's calendar integration. The app focuses on its domain, the host handles cross-tool orchestration. |

#### DEVELOPMENT & DEPLOYMENT

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S7.13 | **`create-mcp-app` skill** — AI coding agent can scaffold complete MCP App project. Install via `/plugin marketplace add modelcontextprotocol/ext-apps`. | `TOOLS` | MEDIUM | Meta: use AI to build AI tools. We could have Claude Code generate Baby Brains MCP Apps for us. |
| S7.14 | **Local dev with cloudflared tunnel** — run MCP server locally, tunnel to internet via cloudflared, add as custom connector in Claude. | `ARCH` | MEDIUM | Development workflow for testing. Run on new desktop, tunnel to Claude for testing. |
| S7.15 | **Available on paid Claude plans (Pro, Max, Team, Enterprise)** — no additional charge for connectors/tools. | `COST` | MEDIUM | Already covered by existing Claude subscription. No extra cost to use MCP Apps. |

---

### S7 — Key Patterns Identified

**Pattern 17: Protocol Layer vs Application Layer**
Anthropic leads at the PROTOCOL layer (MCP, MCP Apps). They define how tools connect to AI. But the VALUE is in the APPLICATION layer — domain-specific implementations built on the protocol. Anthropic doesn't know about Baby Brains activities, Montessori methodology, or rehabilitation protocols. We do. The protocol is the foundation; our expertise is the differentiation.

This is the same pattern as the web: HTTP/HTML (protocol) vs specific websites (application). Nobody wins by reimplementing HTTP. You win by building the best application on top of it.

**Pattern 18: Interactive > Text for Complex Data**
Text responses lose fidelity when data is complex. A list of workout stats is less useful than an interactive chart. Pain trends over time are better as a visual graph than a text summary. MCP Apps enable this without building a separate web application.

**Pattern 19: Sandboxed Extensibility**
The MCP Apps security model (sandboxed iframe, host-controlled capabilities, auditable messages) shows how to safely extend an AI system with third-party code. This addresses the R31 concern about malicious skills — MCP Apps are inherently safer because they can't escape their container. Our agent should adopt this same security model for any extensions we add.

---

### S7 — ATLAS / Baby Brains Application Ideas

| MCP App Idea | What It Would Do | Replaces |
|---|---|---|
| **Activity Viewer** | Interactive card showing activity details, age ranges, materials, modifications. Click to generate content variants. | Current YAML reading workflow |
| **Health Dashboard** | Traffic Light status, pain trends, assessment progress, workout history — all interactive in conversation. | CLI output + manual chart creation |
| **Workout Timer** | Interactive timer with exercise display, set tracking, form cues. (Partially overlaps with Command Centre UI) | Current file-based timer IPC |
| **Content Pipeline Monitor** | Visual pipeline showing activity conversion status, quality grades, retry counts. | CLI output from pipeline |
| **Baby Brains Knowledge Explorer** | Browse activities by age, domain, materials. Preview, edit, approve — all in conversation. | Manual file browsing |
| **Assessment Protocol Runner** | Visual assessment interface with body diagrams, measurement inputs, progress tracking. | Voice-only assessment runner |

**Key insight:** These apps would work in Claude.ai, Claude Desktop, AND VS Code. Build once, use everywhere. They'd also work with other AI platforms that adopt MCP Apps.

---

### S7 — Cross-References

| Item | S7 Says | Previous Sources Say | Synthesis |
|------|---------|---------------------|-----------|
| MCP as bridge | MCP Apps extends MCP with interactive UI | S2.05: MCP as bridge between LobeHub + Moltbot; S4.05: Grok API is OpenAI-compatible | **MCP is becoming the universal protocol.** Everything connects via MCP. Our agent should be MCP-native. Build tools as MCP servers, build UIs as MCP Apps. |
| Security model | Sandboxed iframe, host-controlled capabilities | S2.23-24: multi-system attack surface; S3.11: containerized isolation; R31: malicious skills | **MCP Apps security > Claude Skills security.** Skills run with full agent permissions. MCP Apps run in sandboxed iframe with host-controlled capabilities. Prefer MCP Apps architecture for extensions. |
| Interactive UI | UI inside conversation | S2.14: branching conversations in LobeHub; S2.07: artifact rendering | **Complementary.** LobeHub provides branching/artifacts for agent DEVELOPMENT. MCP Apps provides interactive UI for agent USAGE. Different stages of the workflow. |
| Skills vs context | MCP Apps are tools (active), not passive context | S6.01-02: passive context beats skills (100% vs 53%) | **Important distinction.** S6 shows passive context is better for KNOWLEDGE. S7 shows interactive tools are better for INTERACTION. They're solving different problems. Knowledge in AGENTS.md, interaction via MCP Apps. Both are correct for their domain. |

---

### S7 — Strategic Assessment

**Should we invest in MCP Apps?**

| Argument For | Argument Against |
|---|---|
| Open standard, build once deploy everywhere | Early stage, spec may change |
| Strong security model (sandboxed) | We already have Command Centre UI |
| No extra cost on Claude plans | Adds development complexity |
| Interactive > text for complex data | Voice-first doesn't need visual UI |
| Baby Brains could showcase via MCP Apps | Core business value is content, not tooling |

**Verdict:** Not immediate priority for Baby Brains launch, but high strategic value for ATLAS 3.0. The protocol is the future — learning it now positions us well. Start with something small (health dashboard or activity viewer) to learn the SDK, then expand.

**User's insight is correct:** Anthropic leads at the protocol layer, but the value is in domain-specific applications. Open source enables experimentation that Anthropic can't do. Our edge is knowing Baby Brains' domain deeply — Anthropic never will.

---

### S7 — Action Items for Investigation

| Priority | Item | What to Find Out |
|----------|------|------------------|
| 1 | **Install `create-mcp-app` skill** | `/plugin marketplace add modelcontextprotocol/ext-apps` in Claude Code. Test scaffolding. |
| 2 | **Build hello-world MCP App** | Simple health status viewer. Test with cloudflared tunnel to Claude. |
| 3 | **Review system-monitor example** | How does it compare to our Command Centre UI? Can we learn from it? |
| 4 | **Review transcript-server + say-server** | STT/TTS as MCP Apps. Compare with our Qwen3-TTS + voice bridge. |
| 5 | **Assess MCP Apps on new desktop** | Can we run MCP App servers on the desktop and connect to Claude? |

---

*S7 processed: January 30, 2026*

---
---
