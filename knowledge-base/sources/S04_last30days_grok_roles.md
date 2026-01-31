# S4: /last30days Skill + Grok API + Role Allocation Strategy

**Source:** GitHub repo (mvanhorn/last30days-skill) + xAI API documentation + user strategic input
**Type:** Tool evaluation + architectural strategy question
**Context:** User already identified /last30days in R31 research. This revisit adds technical depth plus a critical strategic question: how do different AI models/agents divide responsibilities?

---

### S4 — Tool: /last30days Skill (Updated Assessment)

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S4.01 | **/last30days** — Claude Code skill that scrapes Reddit + X for last 30 days on any topic, synthesizes into copy-paste prompts | `TOOLS` `BUSINESS` | HIGH | 1.6k stars, 181 forks, active development (Jan 2026 commits). Baby Brains use: `/last30days montessori parenting trends`, `/last30days toddler activities viral content`. |
| S4.02 | **Requires OpenAI API key + X (Twitter) API key** — stored in `~/.config/last30days/.env` | `TOOLS` `COST` | HIGH | Dependencies: OpenAI for synthesis, X API for social data. Note: uses `XAI_API_KEY` env var — this is likely Grok/xAI, not legacy Twitter API. Confirms Grok API is the path to X data. |
| S4.03 | **Engagement-metric weighting** — ranks by upvotes, likes, comments rather than recency alone | `TOOLS` | MEDIUM | Smart filtering: surfaces community-validated content, not just newest. Reduces noise in trend research. |
| S4.04 | **Outputs tool-specific prompts** — `/last30days [topic] for [tool]` generates prompts tuned for ChatGPT, Midjourney, Claude, etc. | `TOOLS` `WORKFLOW` | MEDIUM | Useful for Baby Brains content creation: `/last30days parenting instagram reels for midjourney` to get visual content prompts. |

### S4 — Tool: Grok API (xAI)

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S4.05 | **Grok API has native X Search tool** — real-time access to X/Twitter data. $5 per 1,000 calls. | `TOOLS` `COST` | HIGH | This is the unique capability no other LLM has. Claude, GPT, Gemini cannot search X natively. For Baby Brains trend monitoring, competitor analysis, and content research, X data is essential. |
| S4.06 | **Grok 4.1 Fast** — near-frontier performance at $0.20/$0.50 per million tokens (input/output) | `TOOLS` `COST` | HIGH | Extremely cheap for bulk work. 10x cheaper than Claude for non-critical tasks. Could handle all trend research, content drafting, social monitoring at minimal cost. |
| S4.07 | **OpenAI-compatible API format** — change base URL + API key to switch from OpenAI/Claude | `TOOLS` `ARCH` | HIGH | Drop-in replacement. Our model router can include Grok with minimal integration work. Same client libraries, same request format. |
| S4.08 | **2 million token context window** (Grok 4) | `TOOLS` | MEDIUM | Massive context. Could ingest entire Baby Brains knowledge base in a single prompt for analysis. Not needed for routine tasks but powerful for deep research passes. |
| S4.09 | **Web Search tool** — also $5 per 1,000 calls, for general web (not just X) | `TOOLS` | MEDIUM | Grok can search the open web too. Compare with Perplexica (free, self-hosted from S3) vs Grok Web Search ($5/1k calls). |
| S4.10 | **Cost estimate: $5-30/month for light use** | `COST` | HIGH | Affordable for Baby Brains. X Search at $5/1k calls — if we do 100 trend queries/month = $0.50. Model tokens for synthesis on top. Total well under $30/month for comprehensive social intelligence. |

### S4 — Strategic: AI Role Allocation

This is the most important question raised so far. The user asks: where does Grok handle things vs Claude vs the local agent?

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S4.11 | **Role allocation question** — which AI handles what in a multi-model, multi-agent system? | `ARCH` `COST` | HIGH | This needs a clear framework. Not just "route to cheapest" but "route to most capable for this specific task type." See proposed framework below. |
| S4.12 | **Grok's unique capability = real-time social data** — no other model can do this. Role is clear: social intelligence layer. | `ARCH` `TOOLS` | HIGH | Grok isn't competing with Claude for reasoning. It's filling a gap Claude literally cannot fill. This makes role allocation clean rather than overlapping. |

---

### S4 — Proposed Role Allocation Framework

This is a first draft. Will evolve as more sources come in and we understand capabilities better.

```
┌─────────────────────────────────────────────────────────────┐
│              ATLAS 3.0 — AI ROLE ALLOCATION                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  LAYER 1: LOCAL MODEL (Qwen3-4B / Ollama)                    │
│  ├── Intent classification (voice commands)                   │
│  ├── 0-token pattern matching                                │
│  ├── Private data queries (health, finance, personal)        │
│  ├── Simple routing decisions                                │
│  ├── Draft generation for non-critical content               │
│  └── Cost: FREE (electricity only)                           │
│                                                               │
│  LAYER 2: GROK (xAI API)                                     │
│  ├── X/Twitter trend research                                │
│  ├── Real-time social sentiment analysis                     │
│  ├── Competitor monitoring on X                              │
│  ├── Content trend discovery                                 │
│  ├── Web search (alternative to Perplexica)                  │
│  ├── Bulk content drafting (cheap tokens)                    │
│  └── Cost: $5-30/month                                       │
│                                                               │
│  LAYER 3: CLAUDE (Anthropic API)                              │
│  ├── Complex reasoning and analysis                          │
│  ├── Code generation and review                              │
│  ├── Quality-critical content (Baby Brains activities)       │
│  ├── Multi-step planning and strategy                        │
│  ├── Safety-critical decisions                               │
│  ├── Agent orchestration (Claude Code / Opus)                │
│  └── Cost: $20-100/month (usage dependent)                   │
│                                                               │
│  LAYER 4: EXECUTION AGENT (Moltbot-like / ATLAS daemon)      │
│  ├── 24/7 always-on presence                                 │
│  ├── Messaging bridge (Telegram, voice)                      │
│  ├── Task execution (file ops, shell, APIs)                  │
│  ├── Scheduling and proactive notifications                  │
│  ├── Routes TO other layers based on task type               │
│  └── Cost: Hardware electricity                              │
│                                                               │
│  ROUTING LOGIC:                                               │
│  ├── "What's trending in parenting on X?" → Grok             │
│  ├── "Review this Baby Brains activity YAML" → Claude        │
│  ├── "My status" → Local (0 tokens)                          │
│  ├── "Draft 10 social media posts" → Grok (cheap bulk)       │
│  ├── "Analyze our conversion funnel" → Claude (complex)      │
│  ├── "Remind me to call the supplier" → Local (simple)       │
│  ├── "What are competitors posting?" → Grok (X Search)       │
│  └── "Build the landing page" → Claude (code gen)            │
│                                                               │
│  KEY PRINCIPLE: Route by UNIQUE CAPABILITY, not just cost.    │
│  Grok: real-time social (exclusive)                          │
│  Claude: deep reasoning + code (best-in-class)               │
│  Local: private data + zero cost (sovereignty)               │
│  Agent: execution + presence (always-on)                     │
└─────────────────────────────────────────────────────────────┘
```

**Why this works:**
- No overlap in unique capabilities — each layer does something the others literally cannot
- Cost scales with complexity — free for simple, cheap for bulk, expensive only for hard problems
- Privacy respected — sensitive data never leaves local, social queries go to Grok (public data anyway), complex reasoning goes to Claude (with appropriate data scoping)
- The execution agent is the ROUTER, not a model — it decides where to send each task

**Open questions:**
1. Does Grok's X Search return enough structured data for programmatic analysis, or just conversational summaries?
2. Can /last30days be adapted to use Grok API directly instead of OpenAI + X API separately?
3. What happens when layers disagree? (e.g., Grok says trend X is hot, Claude says it's low quality)
4. How does LobeHub (S2) fit into this? As the management/design layer above all four?

---

### S4 — Cross-References

| Item | S4 Says | Previous Sources Say | Synthesis |
|------|---------|---------------------|-----------|
| Multi-model routing | Route by unique capability | S1.09-S1.11: route for cost; S2.09: 40+ providers; S3.01: local for private, cloud for heavy | **Evolving understanding.** S1-S3 focused on cost optimization. S4 adds capability-based routing. Both matter. Route by capability first, then by cost within capability tier. |
| Real-time social data | Grok is the only option | S1 report was generated by CAF reading X data; /last30days uses X API | **Grok API is the integration point.** CAF used X API directly (~$50 for 5k posts). /last30days uses X API. Grok wraps this with LLM reasoning on top. More powerful, similar cost. |
| Self-hosted search | Perplexica from S3 | S4.09: Grok Web Search $5/1k calls | **Use both.** Perplexica for general web research (free). Grok for X-specific social intelligence (paid but unique). |

---

### S4 — Action Items for Investigation

| Priority | Item | What to Find Out |
|----------|------|------------------|
| 1 | **Grok API signup** | Get API key, test X Search with Baby Brains queries ("montessori activities", "toddler development"). Evaluate data quality and structure. |
| 2 | **Grok X Search output format** | Does it return structured data (user, engagement metrics, timestamps) or just text summaries? Structured = much more useful for trend analysis. |
| 3 | **Grok + /last30days integration** | Can /last30days use Grok API instead of separate OpenAI + X API? Would simplify the stack. |
| 4 | **Grok vs Perplexica for web search** | $5/1k calls vs free self-hosted. Is the quality difference worth the cost? |
| 5 | **Layer routing implementation** | How does the execution agent decide which layer to route to? Rules-based (pattern matching) or LLM-classified? Our intent dispatcher already does pattern matching — extend it. |

---

### S4 — Baby Brains Specific Use Cases for Grok

| Use Case | Query Pattern | Frequency | Est. Cost |
|----------|---------------|-----------|-----------|
| Content trends | "What parenting content is viral this week?" | Weekly | ~$0.05/query |
| Competitor watch | "What are @competitor1 @competitor2 posting?" | Daily | ~$0.15/day |
| Topic validation | "Is Montessori trending up or down?" | Monthly | ~$0.05/query |
| Content ideas | "What parenting questions get most engagement?" | Weekly | ~$0.05/query |
| Influencer discovery | "Who's talking about baby development with high engagement?" | Monthly | ~$0.05/query |
| Sentiment analysis | "How do parents feel about screen time for toddlers?" | As needed | ~$0.10/query |
| **Monthly total** | | | **~$5-10** |

---

*S4 processed: January 30, 2026*

---
---
