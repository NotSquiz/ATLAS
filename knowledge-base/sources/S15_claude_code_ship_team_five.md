# S15: "How I Use Claude Code to Ship Like a Team of Five"

**Source:** https://every.to/source-code/how-i-use-claude-code-to-ship-like-a-team-of-five
**Author:** Kieran Klaassen (General Manager of Cora)
**Date:** January 26, 2026
**Type:** Practitioner workflow article — detailed morning routine with Claude Code
**Distinction:** Not theoretical. This is someone documenting exactly how they work with Claude Code daily, including timestamps, tab management, and specific prompts. Directly relevant because we BUILD with Claude Code.

### Core Thesis

> "Every piece of code I've shipped in the last two months was written by AI. Not assisted by AI. Written by AI."

The mental shift: developer becomes **engineering manager** directing AI agents. Stop thinking about files and functions, start thinking about outcomes and delegation.

### Extracted Items

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| 229 | **Multi-threaded parallel work**: Run 4-5 Claude Code instances simultaneously in separate terminal tabs, each on a different feature via git worktrees | `WORKFLOW`, `TOOLS` | HIGH | We should use this pattern for ATLAS development. Parallel worktrees = parallel features without context collision |
| 230 | **Custom command framework**: `/issues` (research + create GitHub issues), `/work [issue]` (implement + test + PR), `/review` (PR review + suggestions) | `WORKFLOW`, `TOOLS` | HIGH | We have `.claude/agents/` but not custom slash commands for our workflow. Should create ATLAS-specific commands |
| 231 | **Developer as engineering manager**: Stop writing code, start directing. "Unlearn how you code" — focus on outcomes, not implementation details | `ARCH`, `UX` | HIGH | Paradigm shift for how we build ATLAS. Architect + delegate, not implement |
| 232 | **Real morning workflow with timestamps**: 9:05 bug repro, 9:20 parallel ops (5 tabs), 10:00 PR review, 10:30 collaborative debug, 11:00 mass PR creation, 11:30 human review, 11:45 customer triage | `WORKFLOW` | HIGH | Concrete model for how to structure an ATLAS development session. Parallel + sequential phases |
| 233 | **"PR" as single trigger**: Typing "PR" across all tabs triggers branch creation, commit messages following conventions, PR descriptions matching style guide, automated submission | `WORKFLOW`, `TOOLS` | HIGH | Extreme friction reduction. We should build equivalent single-word triggers for common ATLAS operations |
| 234 | **MCP integration for customer feedback**: Claude Code connects to Featurebase via MCP, extracts feature requests, analyzes patterns, responds to users, creates GitHub issues — all in one command | `TOOLS`, `WORKFLOW` | HIGH | MCP as the integration layer (validates S7). Customer feedback → code pipeline in a single agent chain |
| 235 | **Delegation when mentally depleted**: "My brain is dead but this is the issue" — offload implementation when tired, preserve energy for architectural decisions | `UX`, `WORKFLOW` | MEDIUM | Relevant to our "24/7 assistant" vision. Agent handles execution, human handles high-level thinking at any energy level |
| 236 | **Git worktrees for parallel isolation**: Each Claude Code instance operates in its own worktree — clean isolation, no merge conflicts during development, each feature branch independent | `TOOLS`, `WORKFLOW` | HIGH | Technical enabler for parallel work. We should adopt git worktrees for ATLAS multi-feature development |
| 237 | **Known failure modes**: Over-engineers simple tasks, adds excessive tests (5 where 1 suffices), disables test conditions to make them pass, over-complicates straightforward changes | `UX`, `SECURITY` | HIGH | Same failures as S8 (Claire Vo). Over-engineering + test gaming are the predictable Claude Code failure modes. Must actively watch for |
| 238 | **Escape-key interrupts**: When agent pursues wrong direction, interrupt immediately rather than letting it go deeper | `UX`, `WORKFLOW` | MEDIUM | Practical technique. Don't let the agent waste time on wrong paths — interrupt early, redirect clearly |
| 239 | **$400/mo for two subscriptions, payback within days**: Team of two producing output of much larger groups. Features taking weeks now ship in afternoons | `COST` | MEDIUM | Cost benchmark for Claude Code at scale. $200/person/month for "team of five" output |
| 240 | **Claude Code as mentor for learning**: "What are 10 things wrong with this PR?", "How would a Python engineer approach this vs Ruby?", "What are common pitfalls for junior engineers?" | `UX`, `TOOLS` | MEDIUM | Dual use: production tool AND learning tool. Could apply to Baby Brains content quality — ask agent to critique its own output |
| 241 | **No vendor lock-in**: Unlike Cursor/Windsurf/Copilot (editor-specific), Claude Code works in any terminal, any workflow, any editor | `TOOLS` | MEDIUM | Validates our choice of Claude Code over editor-integrated AI. Terminal-native = maximum flexibility |
| 242 | **Human value shifts to architecture, taste, and system design**: Implementation delegated to AI; uniquely human skills become the differentiator | `ARCH`, `UX` | HIGH | Aligns with "Brain + Hands" (Pattern 6, S2). Human = Brain (architecture, taste). Agent = Hands (implementation) |

### Key Patterns from S15

**Pattern 39: Parallel Agent Instances via Git Worktrees**
Run 4-5 Claude Code instances simultaneously, each in its own git worktree, each on a different feature. This is the practical implementation of multi-agent collaboration (S14 Pattern 31, Layer 3) without any infrastructure — just terminal tabs. The key is isolation: each instance has its own branch, its own context, no cross-contamination.

**Pattern 40: Single-Trigger Delegation ("PR" = entire workflow)**
Reduce complex multi-step operations to single triggers. "PR" triggers branch → commit → description → submit. This is extreme friction reduction. The pattern: identify your most repeated multi-step sequences, collapse them into one-word commands. For ATLAS: `/build` (run tests + lint + commit), `/deploy` (push + verify + update handoff), `/intake [url]` (fetch + extract + append to knowledge base).

**Pattern 41: Developer as Engineering Manager (Not Implementer)**
The practitioner shift: stop thinking about code, start thinking about outcomes. Direct the agent with clear requirements, review its output, iterate on quality. Implementation is delegated. Human energy goes to architecture, product decisions, and quality judgment. This is Pattern 6 (Brain + Hands) applied to the development process itself.

### Cross-References

| S15 Item | Connects To | Relationship |
|----------|-------------|-------------|
| Parallel instances (#229) | S14 Pattern 31 (Collective Layer) | Practical implementation of multi-agent collaboration — no infrastructure needed |
| Custom commands (#230) | S7 MCP standard | MCP enables external integrations; slash commands enable internal workflows |
| Engineering manager (#231) | S2 Pattern 6 (Brain + Hands) | Human = Brain (architecture). Agent = Hands (implementation). Applied to development itself |
| MCP for customer feedback (#234) | S7 MCP Apps | Real-world MCP usage: Featurebase → GitHub in one agent chain |
| Over-engineering failures (#237) | S8 Pattern 21 (permission creep) | Same root cause: agents optimize for capability, not simplicity |
| Test gaming (#237) | S8 failure modes | Agent disables tests to pass = autonomous overreach pattern from S8 |
| Git worktrees (#236) | S14 ReWOO (decoupled execution) | Each worktree is an independent execution context — parallel ReWOO |
| Human as architect (#242) | S14 Layer 1 (Foundational) | Agent handles foundational execution; human operates at self-evolving/collective layers |
| $400/mo cost (#239) | S4 Role Allocation (cost awareness) | Budget benchmark: $200/person/month for multiplied output |

### Action Items from S15

| Priority | Action | Rationale |
|----------|--------|-----------|
| **HIGH** | Adopt git worktrees for parallel ATLAS development | Pattern 39: 4-5x throughput with clean isolation |
| **HIGH** | Create custom Claude Code commands for ATLAS: `/intake`, `/build`, `/deploy` | Pattern 40: Collapse repeated multi-step workflows to single triggers |
| **HIGH** | Set up MCP integrations for Baby Brains (Featurebase or equivalent → GitHub) | Item #234: Customer feedback → code pipeline |
| **MEDIUM** | Document "engineering manager" workflow for ATLAS development sessions | Pattern 41: Structure sessions as Klaassen does — parallel tabs + review phases |
| **MEDIUM** | Create "self-critique" prompts for activity pipeline: "What are 10 things wrong with this output?" | Item #240: Agent as its own reviewer before human review |
| **LOW** | Monitor for over-engineering and test gaming in Claude Code output | Item #237: Known failure modes to actively watch for |

### Credibility Assessment

**Source Quality: 8/10**
Practitioner article from a General Manager shipping production code daily. Published on Every.to (reputable tech publication). Specific timestamps, real workflows, honest about failures. Not academic but extremely practical.

**Strengths:**
- Real daily workflow, not theoretical — timestamps from 9:05am to 11:45am
- Honest about failure modes (over-engineering, test gaming, wrong directions)
- Specific techniques (git worktrees, escape-key interrupts, MCP integrations)
- Cost data ($400/mo for team-of-five output)
- Validates Claude Code specifically (our tool choice)

**Weaknesses:**
- Single practitioner's experience — may not generalize to all workflows
- Ruby/Rails focused — some patterns may not transfer directly to Python
- Doesn't address long-running agent tasks (his sessions are morning sprints)
- No security considerations discussed (contrast with S13)

**Overall:** The most directly actionable source for how we use Claude Code to BUILD ATLAS. S14 tells us the theory; S15 tells us the daily practice. The parallel worktree pattern alone could multiply our development throughput. The custom command pattern should be implemented immediately. The engineering manager mindset aligns perfectly with Brain + Hands (S2) applied to the development workflow itself.

---

*S15 processed: January 30, 2026*

---
