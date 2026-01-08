# Section 2: Implementation Patterns (2200-4600s)

> Extracted from Claude Agent SDK Masterclass - Speaker: Tariq (Anthropic Agent SDK Team)

---

## Skills Deep Dive

### What Are Skills Exactly?

> **[2200s-2220s]** Skills are "forms of progressive disclosure basically to the agent to figure out what it needs to do."

> **[2234s-2257s]** "I think skills are like an introduction into thinking about the file system as a way of storing context. They're a great abstraction, but there are many ways to use the system."

### Skills vs Direct APIs/Bash

> **[2209s-2241s]** "I don't think there's a general rule. It's like read the transcript and see what your agent wants. If your agent always thinks about the API better as an API.ts file or API.py file, do that."

**Decision**: Use case dependent - observe what works for your specific agent.

### Skill Structure & Discovery

> **[2458s-2506s]** "You just put it in the file system and you tell it 'here is a script, you can call it.' I would design all my CLI scripts to have like a --help so that the model can call that and then it can progressively disclose every subcommand inside of the script."

### Skill Marketplace

> **[2289s-2306s]** "Claude Code has a plugin marketplace that you can also use with the Agent SDK. By marketplace, I'm not sure if people will be charging. It's more just like a discovery system. You can do /plugins in Claude Code."

### Agent SDK Constraint

> **[2267s-2274s]** "The Agent SDK is basically the only way to really use skills to their full extent right now."

---

## Sub-Agent Patterns

### When to Spawn Sub-Agents

> **[3969s-4010s]** "Sub-agents are a very important way of managing context. We're using more and more sub-agents inside of Claude Code. Sub-agents are great for when you need to do a lot of work and return an answer to the main agent."

### Context Isolation - Why It Matters

> **[4147s-4161s]** "The main thing there is to avoid context pollution. You probably wouldn't want to fork the context. You'd probably want to start a new context session and just be like 'Hey, adversarially check the work of - this output was made by a junior analyst at McKinsey or something...'"

### Sub-Agent Use Cases

| Use Case | Pattern | Example |
|----------|---------|---------|
| **Search** | Spawn for complex queries | "How do I find my revenue in 2026?" - search internet, spreadsheet, etc. |
| **Verification** | Adversarial checking | "Check if this analysis is correct" |
| **Parallel Work** | Multiple sub-agents | Read and summarize sheets 1, 2, 3 simultaneously |

### How Sub-Agents Return Results

> **[4012s-4027s]** "For search, maybe you need to search the internet, search the spreadsheet, things like that. There's a bunch of things that don't need to go into the context of the main agent. The main agent just needs to see the final result."

### Parallel vs Sequential

> **[4748s-4770s]** Sub-agents can run in parallel: main agent spins off "read and summarize sheet 1/2/3" agents, collects results, then spins off more for analysis.

---

## Hook Patterns

### Verification Hooks (Deterministic)

> **[4085s-4125s]** "Ideally the best form of verification is rule-based. You're like 'is there a null pointer?' That's easy verification. It doesn't lint or compile. As many rules as you can, try and insert them. Be creative - for example, in Claude Code if the agent tries to write to a file that we know it hasn't read yet, we throw an error. We tell it 'hey, you haven't read this file yet, try reading it first.' That's an example of a deterministic tool we insert into the verification step."

### Hook Types Implied

| Type | Description | Example |
|------|-------------|---------|
| **Pre-Write** | Check before file modification | "Have you read this file?" |
| **Lint/Compile** | Syntax/type checking | Standard linting tools |
| **Rule-Based** | Custom business rules | Null checks, format validation |
| **Post-Execution** | Verify output correctness | Schema validation |

---

## Implementation Patterns

### Tool vs Bash vs Codegen Decision Tree

> **[1115s-1180s]** Three approaches to database access:

| Scenario | Choose | Reason |
|----------|--------|--------|
| Very structured data, sensitive info | **Tool** | Maximum control & safety |
| Dynamic queries, iteration needed | **Bash/Codegen** | Model can iterate on errors |
| General agentic work | **Progressive access + guardrails** | Max flexibility with safety |

> **[1145s-1162s]** "Generally if I'm building an agent today, I'm giving it as much access to my database as possible and then I'm putting in guardrails. I'm probably limiting its write access in different ways. I would give it write access and put in specific rules and then give it feedback if it tries to do something it can't do."

### API Design for Agents

> **[3583s-3607s]** "You can design an agentic search interface. Like B3 to B5 or a range string. These are things the agent knows pretty well. You can do SQL queries - agent knows SQL pretty well. You can also do XML."

**Key Insight**: Design APIs using syntax agents already understand well:
- Range syntax (B3:B5)
- SQL queries
- XML queries

### Transform to Familiar Interfaces

> **[3296s-3350s]** "If you can translate something into an interface that the agent knows very well, that's great. If you have a data source, if you can convert it into a SQL query, then your agent really knows how to search SQL. Thinking about this transformation step is really interesting."

---

## State Management

### Reversibility is Fundamental

> **[4259s-4315s]** "How reversible is the work is a really good intuition. Code is quite reversible - you can just go back, you can undo the git history... A really bad example is computer use... because computer use has non-reversible state."

> **[4266s-4276s]** "We come with these atomic operations right out of the gate. I use git constantly through Claude Code. I don't type git commands anymore."

### Checkpoint Strategy

> **[4321s-4356s]** "Can you store state between checkpoints such that the user can be like 'oh my spreadsheet is messed up right now, just go back to the previous checkpoint.' Potentially even can the model go back to previous checkpoints. Someone had this 'time travel tool' that they were giving one of the coding agents which was kind of cool."

### State Reversibility Scale

| Domain | Reversibility | Strategy |
|--------|--------------|----------|
| **Code** | High | Git history, atomic commits |
| **Spreadsheets** | Medium | Checkpoints, version history |
| **Computer Use** | Low | Careful planning, confirmations |
| **Database** | Medium | Transactions, backups |

---

## Context Window Management

### Clear Context Often

> **[4540s-4602s]** "I tend to clear the context window very often when I'm using Claude Code myself. At least in code, the state is in the files of the codebase. Claude Code can just look at my git diff and be like 'oh hey these are the changes you made.' It doesn't need to know my entire chat history to continue a new task."

### Progressive Context Loading

> **[4480s-4522s]** "You want to give it the starting amount of context. That's also how you work. Like the first 10 rows and the first 30 columns or something. That's what you see - you don't load all of it into context right away... The agent can operate the same way. It can navigate to these sheets, read them, keep a scratch pad, keep some notes and keep going."

### Context Management Principles

1. **Never load entire dataset** - Start with sample
2. **Store state externally** - Files, git, database
3. **Clear often** - State lives outside context
4. **Use scratch pads** - Agent notes for navigation

---

## Making Problems In-Distribution

> **[3942s-3963s]** "You have a problem you want to make it as in-distribution as possible for the agent. The agent knows a lot about different things... like it knows what DCF is... like it knows what SQL is. Can it combine those things together? Ideally you want to make your problem - which is going to be out of distribution in some way - more in-distribution."

### Strategies

1. Convert data sources to SQL (agent knows SQL well)
2. Use familiar range syntax for spreadsheets
3. Leverage existing knowledge (DCF, XML, JSON)
4. Combine known primitives in novel ways

---

## Agent Communication Patterns

> **[3000s-3030s]** "The agents are good at using the things that we have - HTTP requests, hash tools, API keys, named pipes. Probably the agents are just making HTTP requests back and forth from each other using HTTP server. There's interesting work there. I've seen people make a virtual forum for their agents to communicate - they post topics and reply."

### Communication Methods

| Method | Use Case |
|--------|----------|
| HTTP requests | Standard inter-agent calls |
| Named pipes | Local process communication |
| Virtual forums | Complex multi-agent coordination |
| File system | Shared state via files |

---

## System Design Principles

### Multi-User Agent Deployment

> **[2920s-2978s]** "Let's say you have two agents interacting with two different people. The question is how do you think about reusability between agents or how do agents communicate? This is a thing to be discovered... Traditionally with web apps you're serving one app to a million people. With agents like Claude Code we serve a one-to-one container... there's not a lot of communication between containers. It's a very different paradigm."

### Role-Based Access Control

> **[2815s-2851s]** "Usually that's in how you provision your API key or your backend service. I would create temporary API keys for your agents that are scoped in certain ways. On the backend you can check what it's trying to do."

**RBAC Implementation**:
1. Create temporary, scoped API keys per agent
2. Backend validation of operations
3. Proxy insertion for key management (if exfiltration concern)

---

## Mistakes & Pitfalls

### Anti-Pattern: Isolated Bash

> **[2475s-2494s]** "This is kind of an anti-pattern I see sometimes where people are like 'we're going to host the bash tool in this virtualized place and it's not going to interact with other parts of the agent loop.' That makes it hard because if you got a tool result that's saving a file, then your bash tool can't read it."

**Fix**: Bash must have access to the same file system as other tools.

### Scalability Limits

> **[4426s-4432s]** "Claude Code is worse in larger code bases than it is in smaller code bases. As the models get better they will get better at all of that."

### Loading Entire Datasets

> **[4472s-4497s]** "You should never read the entire spreadsheet into context because it would take too much."

### Complex State Machines

> **[4311s-4317s]** "Whenever you're dealing with very complex state machines that you can't undo or redo, it does become harder."

---

## Questions This Section Raises

1. **Skill Marketplace Governance**: How will skill discovery scale? Verification?
2. **Context Pollution Metrics**: How to quantify when pollution affects performance?
3. **Sub-Agent Overhead**: Latency/cost tradeoff vs keeping work in main context?
4. **Reversibility Patterns**: Beyond git/code, what other domains have good patterns?
5. **Agent Communication Standards**: Should there be formal standards (HTTP, pipes)?
6. **Scalability**: How do patterns work with million-row datasets?

---

## Key Takeaways for ATLAS

| Pattern | ATLAS Implementation |
|---------|---------------------|
| Design APIs for agents | Use SQL-like interfaces for data access |
| Progressive access + guardrails | Don't over-restrict tools |
| Think reversibility | Choose domains with good recovery |
| Use sub-agents for isolation | Don't pollute main context |
| Cache state in files | Allows clearing context often |
| Start with deterministic verification | Before relying on sub-agent critique |
| Load context progressively | Never dump entire datasets |
| Create scoped API keys | Per-agent instance security |
