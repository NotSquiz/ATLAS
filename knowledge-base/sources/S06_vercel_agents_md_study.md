# S6: "AGENTS.md outperforms Skills in our agent evals"

**Source:** Vercel Engineering Blog — Jude Gao, January 27, 2026
**URL:** https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
**Type:** Benchmark study with controlled evaluations — passive context (AGENTS.md) vs active retrieval (Skills)
**Credibility:** Very high. Vercel is a major infrastructure company. Study uses hardened eval methodology, addresses test leakage, targets APIs NOT in training data. Actual numbers, not vibes. This is the most rigorous source we've processed so far.

---

### S6 — The Core Finding

```
AGENTS.md (passive context):  100% pass rate  (+47pp over baseline)
Skills with instructions:      79% pass rate  (+26pp over baseline)
Skills default:                53% pass rate  (+0pp — SAME as no docs)
Baseline (no docs):            53% pass rate
```

**Translation:** Embedding knowledge directly in the agent's persistent context massively outperforms giving the agent a tool to look things up. Skills, when left to the agent's discretion, were completely ignored 56% of the time.

---

### S6 — Extracted Items

#### ARCHITECTURE & KNOWLEDGE DESIGN

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S6.01 | **Passive context beats active retrieval** — AGENTS.md (always present in system prompt) achieved 100% vs Skills (on-demand tool) at 53% default / 79% with explicit instructions | `ARCH` `MEMORY` | HIGH | Fundamental design principle for our agent. Don't make the agent decide to look things up — put critical knowledge in its persistent context. Our CLAUDE.md already does this. Extend the pattern to the Baby Brains agent. |
| S6.02 | **Skills were unused 56% of the time** — agents had access but chose not to invoke them | `ARCH` | HIGH | Agents are unreliable at deciding when to use tools. Even when the skill would have helped, the agent skipped it. This has implications for our MCP tool design — don't rely on the agent choosing to use tools for critical knowledge. |
| S6.03 | **"Retrieval-led reasoning over pre-training-led reasoning"** — key instruction that shifts agent from using stale training knowledge to consulting fresh docs | `ARCH` `MEMORY` | HIGH | Directly applicable. Our agent will have training data about parenting, Montessori, etc. — but it will be generic/stale. We need to instruct it to prefer OUR knowledge base (Baby Brains activities, research) over what it "already knows." This single instruction could be the difference between generic and expert output. |
| S6.04 | **Compressed docs index (8KB) matches full injection (40KB)** — 80% reduction with same 100% pass rate. Pipe-delimited file index pointing to retrievable docs. | `MEMORY` `COST` | HIGH | Don't dump everything into context — provide a compressed index and let the agent retrieve specific files as needed. For Baby Brains: don't put all 175 activity YAMLs in context. Put a compressed index of activities, let the agent read specific ones. Massive context savings. |
| S6.05 | **Elimination of decision points** — AGENTS.md removes the moment when agents must decide whether to look up info. It's already there. | `ARCH` | HIGH | Design principle: reduce the number of decisions the agent has to make about its own process. Every decision point is a failure opportunity. Passive > active for critical knowledge. |

#### AGENT BEHAVIOR PATTERNS

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S6.06 | **Instruction ordering matters dramatically** — "invoke skill first" vs "explore project first, then invoke skill" produced very different outcomes | `ARCH` `AUTONOMY` | HIGH | The sequence in which you instruct an agent to gather context changes the result. "Look at docs first" anchors on documentation patterns and misses project-specific context. "Explore first, then consult docs" builds a mental model then uses docs as reference. **For our agent: always explore current state before applying knowledge.** |
| S6.07 | **Anchoring effect** — agents that read documentation first anchored on doc patterns and missed project-specific requirements (e.g., wrote correct page files but missed config changes) | `ARCH` | MEDIUM | Cognitive bias in LLMs. If the first thing they see is "how to do X," they do X by the book but miss context-specific nuances. Relevant to Baby Brains content pipeline — agent should understand the specific activity context before applying template knowledge. |
| S6.08 | **Skills excel for vertical, action-specific workflows** — version upgrades, migrations, best practice applications (explicit user-triggered) | `ARCH` `TOOLS` | MEDIUM | Skills aren't useless — they're just wrong for general knowledge. They work for specific, explicit actions: "upgrade my Next.js version" or "migrate to new router." For ATLAS: skills/tools for specific actions (log workout, sync Garmin), persistent context for domain knowledge (health protocols, Baby Brains methodology). |

#### PRACTICAL IMPLEMENTATION

| # | Item | Tags | Relevance | Notes |
|---|------|------|-----------|-------|
| S6.09 | **`npx @next/codemod@canary agents-md`** — auto-generates AGENTS.md by detecting project version, downloading matching docs, injecting compressed index | `TOOLS` | MEDIUM | The automation pattern matters more than the specific tool. For Baby Brains: we could build a similar generator that creates an agent context file from our knowledge base — auto-updated as activities are added. |
| S6.10 | **Build evaluations targeting APIs absent from training data** — this reveals where documentation access actually matters vs where the model already knows enough | `ARCH` `AUTONOMY` | HIGH | Testing methodology. When evaluating our agent, test it on Baby Brains-SPECIFIC knowledge (our activity format, our quality rubric, our Montessori interpretation) — not generic parenting questions the model already handles. That's where our knowledge injection proves its value. |

---

### S6 — Key Patterns Identified

**Pattern 14: Passive Context > Active Retrieval for Domain Knowledge**
The single most important finding from this source. When knowledge is critical to the agent's performance, embed it in persistent context (AGENTS.md / CLAUDE.md), don't rely on the agent choosing to look it up. Active retrieval (skills/tools) works for explicit, user-triggered actions — not for general domain expertise.

**This directly validates our ATLAS architecture:**
- Our CLAUDE.md already embeds health protocols, voice commands, architecture decisions → passive context
- Our intent dispatcher uses passive pattern matching, not active tool lookup → passive first
- Our 0-token voice responses are the ultimate passive pattern → no LLM decision needed at all

**Pattern 15: Compressed Index + File Retrieval > Full Context Injection**
You don't need to put everything in context. A compressed index (8KB) pointing to retrievable files works as well as the full content (40KB). The agent reads the index, identifies what's relevant, then retrieves specific files. This is essentially a lightweight RAG without the complexity of embeddings and vector search.

**For Baby Brains knowledge base:**
```
[Baby Brains Activity Index]|root: ./knowledge/activities
|IMPORTANT: Use Baby Brains methodology over generic Montessori training data
|0-3months:{tummy-time.yaml,tracking.yaml,grasping.yaml,...}
|3-6months:{reaching.yaml,rolling.yaml,sitting-support.yaml,...}
|6-9months:{crawling.yaml,object-permanence.yaml,finger-foods.yaml,...}
|...
```

Agent sees the index in every conversation. When asked about tummy time, it reads `tummy-time.yaml` specifically. No RAG infrastructure needed.

**Pattern 16: Test Against Training Data Gaps**
Evaluate your agent on knowledge it CAN'T already have — that's where your custom knowledge injection proves its value. Generic questions test the base model, not your system. For Baby Brains: test on our specific activity format, our Voice Elevation Rubric, our quality grades — things no base model knows.

---

### S6 — ATLAS Design Implications

| Current ATLAS | What S6 Validates | What S6 Suggests We Add |
|---------------|-------------------|------------------------|
| CLAUDE.md with extensive project context | Passive context is the right approach | Compress it. Our CLAUDE.md is large. Could we create a compressed index version? |
| 0-token intent matching | Passive pattern matching > active tool use | Keep and extend. This is our strongest architectural decision. |
| semantic_memory SQL store | Good for storage | Add compressed index of stored memories to agent context so it knows what's available to retrieve |
| Baby Brains activity YAMLs | - | Create a compressed activity index for agent context. Don't inject all 175 YAMLs — provide an index. |
| Quality rubric in QC hook | Active tool (hook runs on demand) | Also embed rubric summary in agent context as passive knowledge |

---

### S6 — Cross-References

| Item | S6 Says | Previous Sources Say | Synthesis |
|------|---------|---------------------|-----------|
| Knowledge access method | Passive context (100%) >> Active retrieval (53%) | S2.06: LobeHub RAG for knowledge base; S5.02: session memory search | **Critical nuance.** RAG (S2) and memory search (S5) are active retrieval — agent must decide to use them. S6 shows passive context is more reliable. **Best approach: passive index + active retrieval as supplement, not either/or.** |
| Agent decision-making | Agents are unreliable at deciding when to use tools | S1.02: AI as engineering manager making decisions; S2.03: Agent Groups with supervisor | **Tension.** S6 says agents are bad at meta-decisions (when to look things up). S1/S2 say agents can manage other agents. Resolution: agents are good at TASK decisions, bad at PROCESS decisions. Embed process knowledge passively, let them make task decisions actively. |
| Compressed knowledge | 8KB index = 40KB full docs (same results) | S1.08: adaptive chunking; S3.01: hybrid routing | **Efficiency win.** Compression + retrieval is the cheapest path to informed agents. Cheaper than RAG infrastructure, cheaper than full context injection, and apparently more effective than active tools. |

---

### S6 — Credibility Assessment

**Strengths:**
- Vercel is a credible engineering organization with direct experience in AI tooling
- Hardened eval methodology: addressed test leakage, used behavior-based assertions, targeted APIs outside training data
- Actual benchmark numbers with clear methodology
- Acknowledges limitations ("the gap may close as models get better at tool use")
- Practical recommendation, not just theory

**Weaknesses:**
- Tested only on Next.js coding tasks — may not generalize to all domains
- Single model tested (not specified which, likely Claude or GPT)
- "Skills" as tested may not represent all skill implementations
- Small eval suite (not specified how many tests)

**Overall:** Highest quality source processed so far. The 100% vs 53% result is striking. The design principles extracted (passive > active, compress + retrieve, test against training gaps) are immediately applicable to our agent architecture. This should influence how we design the Baby Brains agent's knowledge layer.

---

*S6 processed: January 30, 2026*

---
---
