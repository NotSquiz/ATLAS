# Section 3: Advanced Topics & Q&A (4400-6744s)

> Extracted from Claude Agent SDK Masterclass - Speaker: Tariq (Anthropic Agent SDK Team)

---

## Q&A Digest

### Q1: Large Spreadsheets (Million Rows)
**[4401s]** "How do you think about very large spreadsheets (million rows, 100,000 columns)?"

**Answer [4471s-4520s]**:
> "Model should never read entire spreadsheet into context because it would take too much. You want to give it the starting amount of context - like opening a spreadsheet you see first 10 rows, 30 columns. The agent can operate the same way - navigate to sheets, read them, keep a scratch pad, keep notes and keep going."

**Pattern**: Search-first, iterate, keep scratch pad.

---

### Q2: Context Window Fraction
**[4524s]** "Do you have a rule of thumb for what fraction of context window to use before hitting diminishing returns?"

**Answer [4558s-4648s]**:
> "When I talk to people using Claude Code, they're like 'I'm on my fifth compact.' I've almost never done a compact before... I tend to clear the context window very often. At least in code, the state is in the files of the codebase. Claude Code can just look at my git diff."

**Key Insight**: Clear context often, store state externally. For non-technical users, design UX that manages context clearing automatically.

---

### Q3: Parallel Sub-Agents for Large Data
**[4682s]** "Can we use multiple sub-agents to chunk up large spreadsheets and run them in parallel?"

**Answer [4695s-4745s]**:
> "Claude Code is the best experience for using sub-agents, especially sub-agents with bash - very very good. We invested heavily in the bash tool with race condition solving."

**Reference**: Adam Wolf's QCON talk on bash race condition handling.

---

### Q4: Where to Put Verification
**[4838s]** "Where exactly do you put verification - after generation or after execution?"

**Answer [4871s-4932s]**:
> "We do some verification in the read step of Claude Code. Use rules or heuristics - e.g., 'total columns searched should be under 10,000.' Give feedback to the model: 'chunk this up', throw an error with feedback. The great thing about the model is it listens to feedback, it will read the error outputs."

**Principle**: **Verification everywhere, not just at end.**

---

### Q5: Agent Sequencing
**[4941s]** "How do we form the steps? How do we tell the agent the sequence of operations?"

**Answer [4958s-5001s]**:
> "Use system prompt to define general flow, but let agent be intelligent about what's necessary. For read-only questions, you don't need to verify compile errors because no write operations happened."

**Principle**: Define flow in system prompt, let agent skip unnecessary steps intelligently.

---

### Q6: Deployment Architecture
**[5972s]** "If we deploy this, are we supposed to run Claude Code in a swarm or use the Agent SDK?"

**Answer [6052s-6188s]**:
> Two deployment paths:
> 1. **Local app** - Run on user's machine
> 2. **Sandbox** (Cloudflare) - Cloud-hosted containers

> "Cloudflare sandbox.st start... bun agent.ts ... that's kind of all it takes"

For UI: "Have a dev server in sandbox, expose a port, agent edits code, live refresh for user interaction" (Lovable pattern).

---

### Q7: Monetization Strategy
**[6319s]** "How are people monetizing agents - how do you handle margins?"

**Answer [6340s-6413s]**:
> "Agents are kind of pricey... focus on having the most intelligent models... rather charge fewer people more money. Find hard use cases... make sure you're solving a problem people want to pay for - that's #1. Subscription or token-based depends on usage... Claude Code does mix of rate limits + usage-based pricing... design your agent around monetization."

**Models**:
- Subscription for predictable usage
- Token-based for variable usage
- Hybrid (rate limits + usage)

---

### Q8: Hooks Deep Dive
**[6420s]** "Can you talk about hooks and your take on them?"

**Answer [6428s-6484s]**:
> "For deterministic verification and context insertion, fire as events, useful for guarding operations."

**Use Cases**:
- Fight hallucinations ("verify agent returned response without writing script")
- Give feedback ("please make sure you write a script, please make sure you read this data")
- Guard dangerous operations
- Insert context at key moments

---

### Q9: Large Codebases (50M+ LOC)
**[6632s]** "How are you dealing with large codebases?"

**Answer [6696s-6720s]**:
> "Use good CLAUDE.md files, start in right directory, verification/hooks, don't rely on semantic search. We dogfood Claude Code... we don't have custom [solutions]."

**Key Point**: Better CLAUDE.md files + verification beats semantic search for large codebases.

---

## Verification Strategies

### Deterministic vs LLM Verification

| Type | When to Use | Example |
|------|-------------|---------|
| **Rule-based** | Always first | Null checks, lint, compile |
| **Tool-based** | During execution | Read-before-write checks |
| **Sub-agent** | Complex validation | "Junior analyst" adversarial check |
| **LLM critique** | Last resort | When rules insufficient |

### Verification Hierarchy

> **[4876s-4928s]** Best practices in order:
> 1. **Deterministic rules first** (null checks, lint/compile)
> 2. **Tool-based validation** (read-before-write checks)
> 3. **Sub-agent verification** (as models improve)
> 4. **Avoid context pollution** with separate sessions

### Adversarial Checking Pattern

> **[4445s-4450s]** "Junior analyst" framing - search-first pattern: "searching Ctrl+F revenue and then check each result"

> **[4147s-4161s]** "Start a new context session and be like 'Hey, adversarially check the work of - this output was made by a junior analyst at McKinsey...'"

### Verification Placement

> **[4928s]** "Verification can happen anywhere and should happen anywhere - put it in as many places as you can."

Locations:
- After context gathering
- Before write operations
- After code generation
- After execution
- In hooks (pre/post)

---

## Context Management

### Managing Long Contexts

| Strategy | Description | When |
|----------|-------------|------|
| **Never load all** | Start with samples | Large datasets |
| **Progressive loading** | Load on demand | Navigation patterns |
| **External state** | Files, git, DB | Persistent info |
| **Clear often** | Reset context | Between tasks |

### Context Compaction

> **[4558s-4570s]** "When I talk to people using Claude Code, they're like 'I'm on my fifth compact.' I've almost never done a compact before... I tend to clear the context window very often."

> **[4632s-4636s]** "Can you maybe every time user asks new question do your own compact or something and summarize the context?"

**Insight**: Power users clear often rather than compact.

### State Storage Pattern

> **[4583s-4596s]** "At least in code, the state is in the files of the codebase. Claude Code can look at my git diff and be like 'oh hey these are the changes you made.'"

> **[4642s-4652s]** "In a spreadsheet, a lot of the state is in the spreadsheet itself. Can you store user preferences as it goes so that you remember some of this stuff?"

### Session Management for Non-Technical Users

> **[4618s-4628s]** "When building your own agent with non-technical users, they don't know what context window is - UX design of resetting conversation state."

> **[4665s-4670s]** "You probably don't need a million context - just need good context management like UX design."

---

## Production Best Practices

### What Anthropic Does Internally

1. **Git diff pattern** [4586s-4598s] - Use git diff to avoid reloading chat history
2. **Bash race conditions** [4703s-4716s] - Invested heavily in solving (Adam Wolf's QCON talk)
3. **File system context** [6017s-6050s] - Actual agent file is 50 lines, mostly boilerplate
4. **Sub-agent handling** [6040s-6047s] - "We take care of all this for you in the harness"
5. **Dogfooding** [6711s-6716s] - "We dogfood Claude Code... we don't have custom [solutions]"

### Deployment Patterns

| Path | Infrastructure | Use Case |
|------|---------------|----------|
| **Local app** | User machine | Developer tools, CLI |
| **Sandbox** | Cloudflare | SaaS products |
| **Live dev server** | Sandbox + exposed port | Interactive UI (Lovable pattern) |

### Scaling Considerations

> **[4418s-4430s]** "As data becomes larger and larger it's just a harder problem... accuracy will go down... Claude Code is worse in larger codebases."

> **[4432s]** "As models get better they will get better at all of that."

### Cost Management

> **[6340s-6376s]** "Agents are kind of pricey... focus on having the most intelligent models... rather charge fewer people more money. Find hard use cases... make sure you're solving a problem people want to pay for."

**Pricing Models**:
- Subscription: Predictable, good for consistent usage
- Token-based: Variable, matches actual consumption
- Hybrid: Rate limits + usage-based (Claude Code model)

---

## Advanced Patterns

### Multi-Level Sub-Agent Spawning

> **[4750s-4770s]** Main agent spawns read agents → collects summaries → spawns analysis agents

```
Main Agent
├── Sub-Agent 1: Read & summarize Sheet 1
├── Sub-Agent 2: Read & summarize Sheet 2
├── Sub-Agent 3: Read & summarize Sheet 3
│   [collect results]
├── Sub-Agent 4: Analyze combined summaries
└── Sub-Agent 5: Generate final report
```

### File System as Context Engineering Layer

> **[6001s-6010s]** "Think about file system as a way of doing context engineering... lot of inputs into agent."

Inputs via file system:
- Skills (markdown)
- Scripts (bash, Python)
- Configuration
- State/checkpoints
- Scratch pads

### UI Adaptation Pattern (Lovable)

> **[6163s-6188s]** "Have a dev server in sandbox, expose a port, agent edits code, live refresh for user interaction."

Flow:
1. Sandbox container with dev server
2. Agent generates/edits UI code
3. Port exposed to user
4. Live refresh on changes
5. User interacts, feedback loop

### Handling Hallucinations

> **[6558s-6591s]** "Pokemon SDK isn't very good, it tries twice and then just gives comparison table because it's hallucinatory. Generation 9 now and Venusaur stats have changed."

> **[6596s-6609s]** "Use hooks to fight against hallucinations - verify if agent returned response without writing a script. Use hooks to give feedback: 'please make sure you write a script, please make sure you read this data.'"

**Strategy**: Hooks enforce behavior (must write script, must read data).

---

## Warnings & Pitfalls

1. **[4871s]** "Verification everywhere - not just at end"
2. **[4913s-4916s]** Don't ignore model feedback - "it listens to feedback, it will read error outputs"
3. **[5040s-5044s]** "Simple is not the same as easy" - agents should be simple but require thoughtful design
4. **[6577s-6591s]** Models hallucinate when they know answers - hard to fight without hooks/feedback
5. **[6625s-6631s]** Determinism is hard: "it's an art... maybe like writing course"
6. **[6703s-6713s]** Don't over-rely on semantic search for large codebases - use good CLAUDE.md and verification

---

## Unanswered Questions

1. **Dynamic verification paths** [4862s] - How to choose between verification methods during execution?
2. **Semantic search improvements** [6645s-6655s] - Are native improvements coming to Claude Code?
3. **Agent memory across sessions** - Long-term learning from past interactions?
4. **Multi-tenant isolation** - Best practices for SaaS deployment?

---

## Summary Table

| Category | Key Finding | Timestamp |
|----------|-------------|-----------|
| Scale Handling | Never load entire dataset; use search+iterate | 4471s-4520s |
| Context Management | Clear often, use external state (git diff) | 4575s-4598s |
| Parallelization | Sub-agents are superior primitive for parallel work | 4739s-4770s |
| Verification | Do everywhere, use hooks for determinism | 4871s-6609s |
| Deployment | Local app or sandbox with dev server | 6052s-6188s |
| Monetization | Solve hard problems, design upfront, hybrid pricing | 6340s-6415s |
| Large Codebases | Good CLAUDE.md + verification, not semantic search | 6703s-6720s |

---

## Key Takeaways for ATLAS

| Insight | ATLAS Application |
|---------|-------------------|
| Verification everywhere | Add pre-execution hooks, not just post |
| Hooks fight hallucinations | Require script writing, data reading |
| Clear context often | Implement session management with git diff pattern |
| Sub-agents for parallelism | Add parallel skill execution support |
| Good CLAUDE.md | Create comprehensive ATLAS.md for context |
| Don't rely on semantic search | Use hooks + verification for large repos |
| Hybrid pricing | Design usage tracking into orchestrator |
