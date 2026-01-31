# S5: Moltbot Memory Flush + Session Search Config

**Source:** Alex Finn (@AlexFinn) via X.com
**Type:** Configuration tip — two hidden memory features disabled by default
**Credibility:** Alex Finn appeared in S3 as a serious Moltbot user (24-hour autonomous run, Mac Studio upgrade, restaurant reservation via voice call). Credible source for config tips.

---

### S5 — Extracted Items

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S5.01 | **Memory flush before compaction** — `compaction.memoryFlush.enabled: true`. Agent automatically saves everything important to a file before context window gets wiped during compaction. Prevents information loss between sessions. | `MEMORY` | HIGH | Directly relevant to any agent we build. Context compaction is when the agent's working memory gets too large and the system summarizes/truncates it. Without memory flush, context that hasn't been explicitly saved is lost. This is the same problem our SessionBuffer (5-exchange, 10-min TTL) solves for voice — but for long-running agent sessions. **Design principle: always persist before purge.** |
| S5.02 | **Session memory search** — `memorySearch.experimental.sessionMemory: true` with sources `[memory, sessions]`. Agent can search through every past conversation, even ones no longer in active context. | `MEMORY` | HIGH | Cross-session memory retrieval. Currently ATLAS stores to semantic_memory SQLite but has no mechanism for the agent to search its own conversation history. This is the difference between "remembers what you told it to remember" and "can recall anything you've ever discussed." For a 24/7 Baby Brains agent, this is essential — "what did we decide about the pricing last Tuesday?" |
| S5.03 | **Both features disabled by default** — users must explicitly enable them. | `MEMORY` `SECURITY` | MEDIUM | Interesting design choice. Likely disabled for privacy/storage reasons (storing all conversations has implications). When we build our agent, we should enable equivalents by default but with configurable retention periods and data scoping. Not everything should be remembered forever. |

---

### S5 — ATLAS Design Implications

These two features map to a gap in our current architecture:

| Moltbot Feature | ATLAS Equivalent | Status |
|-----------------|-----------------|--------|
| Memory flush before compaction | SessionBuffer saves to semantic_memory | **Partial** — SessionBuffer has 10-min TTL and 5-exchange limit. No explicit "flush everything before context loss" mechanism. |
| Session memory search | `SELECT * FROM semantic_memory WHERE ...` | **Partial** — We store to semantic_memory but retrieval is manual/code-level. No agent-accessible search across past sessions. |

**What we should build (when the time comes):**
1. Pre-compaction hook that writes full context summary to persistent storage
2. MCP-accessible memory search tool so the agent can query its own history
3. Configurable retention: business conversations kept longer, casual ones expire

---

*S5 processed: January 30, 2026*

---
---
