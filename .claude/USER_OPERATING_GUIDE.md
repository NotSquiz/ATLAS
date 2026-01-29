# How to Operate Claude Effectively

**For the ATLAS project - practical patterns that get results.**

---

## Claude's Attention Patterns (Honest Assessment)

```
WHAT CLAUDE RELIABLY READS:
✓ First 50 lines of CLAUDE.md
✓ Your current message
✓ Files Claude just opened
✓ Explicit instructions you give

WHAT CLAUDE OFTEN MISSES:
✗ Long files after line 150
✗ Separate files Claude must seek out
✗ Rules buried in paragraphs
✗ Instructions from previous sessions
```

**Key Insight:** Claude's memory resets each session. Context must be rebuilt.

---

## Session Start Rituals

### For Any Work Session
```
You: "Read .claude/handoff.md first, then let me know the current state."
```
This forces Claude to load context before doing anything.

### For Implementation Work
```
You: "We're implementing [feature]. Read handoff.md, then spawn the planner
     agent from .claude/agents/planner.md to create an implementation plan."
```

### For Code Review
```
You: "Review [file] using the code-reviewer agent from .claude/agents/"
```

### For Continuing Previous Work
```
You: "Continue from where we left off. Read .claude/handoff.md for state."
```

---

## Slash Commands (Future - Not Yet Implemented)

These will be created as the system matures:
- `/plan` - Spawn planner agent
- `/review` - Spawn code-reviewer agent
- `/status` - Show current project state
- `/checkpoint` - Force Claude to verify work

---

## Effective Prompting Patterns

### Be Explicit About Workflow
```
BAD:  "Add a new feature for tracking habits"
GOOD: "Add habit tracking. First read existing gamification code,
       then use TodoWrite to plan steps, then implement."
```

### Force Checkpoints
```
"Before writing any code, show me:
1. Which files you'll modify
2. Your planned approach
3. What tests you'll add"
```

### Reference the Infrastructure
```
"Follow .claude/rules/atlas-conventions.md for coding standards"
"Use the patterns from .claude/skills/tdd-workflow.md"
```

### End Sessions Properly
```
"Update .claude/handoff.md with what we accomplished and what's next"
```

---

## When Things Go Wrong

### Claude Ignores Rules
```
You: "STOP. Read .claude/rules/[relevant-rule].md and tell me what it says.
      Then apply it to what you just did."
```

### Claude Goes Off Track
```
You: "Wait. What's in your todo list right now? Let's re-align."
```

### Claude Makes Assumptions
```
You: "Before continuing, what assumptions are you making? Let's verify them."
```

### Claude Skips Steps
```
You: "Show me your checkpoint verification:
      □ File read first?
      □ Tests considered?
      □ Handoff updated?"
```

---

## Project-Specific Patterns

### For ATLAS Health Features
```
"We're modifying health tracking. First:
1. Read atlas/health/service.py
2. Check .claude/rules/atlas-conventions.md for async patterns
3. Plan with TodoWrite
4. Implement with tests"
```

### For Baby Brains Activities
```
"Converting activity [name]. Use the activity-auditor agent from
.claude/agents/activity-auditor.md to verify Grade A quality."
```

### For Gamification Changes
```
"Modifying XP system. Read atlas/gamification/xp_service.py first.
Remember: XP failures must NEVER break health tracking (fail-safe pattern)."
```

---

## The Meta-Rule

**If Claude seems to be ignoring something, the problem is usually:**
1. The instruction is too far down in a long file
2. Claude didn't read the relevant file
3. The instruction is implicit, not explicit

**Solution:** Be explicit. Reference files by path. Force file reads first.

---

## Quick Reference Card

| Situation | Say This |
|-----------|----------|
| Start session | "Read .claude/handoff.md first" |
| Plan feature | "Spawn planner agent from .claude/agents/" |
| Review code | "Use code-reviewer agent" |
| Check rules | "Read .claude/rules/[name].md" |
| End session | "Update handoff.md with what we did" |
| Claude off track | "What's in your todo list?" |
| Force checkpoint | "Show me your verification checklist" |
