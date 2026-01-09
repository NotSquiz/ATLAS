# Phase Handover Template

Use this template when creating handover documentation for fresh agents.

---

# Phase [N] Handover: [Task Name]

**Created:** [Date]
**Priority:** [CRITICAL/HIGH/MEDIUM] - [Brief justification]
**Fresh Agent Required:** [Yes/No] - [Reason]
**Prerequisite:** [Previous phase] (COMPLETE)

---

## Your Mission

[1-2 sentence description of what the agent must create/accomplish]

**The Goal:** [Concrete outcome in one sentence]

---

## Step 1: Read Context Documents (IN ORDER)

| Priority | Document | Location | Why |
|----------|----------|----------|-----|
| 1 | This handover | You're reading it | Complete task spec |
| 2 | [Key doc 1] | `/path/to/doc` | [Reason] |
| 3 | [Key doc 2] | `/path/to/doc` | [Reason] |

---

## Step 2: [Understand the Architecture/Data Flow/Context]

[Include diagrams, flow charts, or structural explanations]

```
[ASCII diagram if helpful]
```

---

## Step 3: Key Input Files

### 3.1 [Input 1]
**File:** `/path/to/file`

```yaml
# Example structure
key: value
```

[Explain the structure]

### 3.2 [Input 2]
**File:** `/path/to/file`

[Same pattern]

---

## Step 4: [Components/Tools/APIs to Use]

### 4.1 [Component 1]
**File:** `/path/to/component`

```python
# Usage example
from module import Component
result = Component.method(input)
```

[Repeat for each component]

---

## Step 5: [I/O Contracts / Data Schemas]

### 5.1 [Interface 1]
**Input:**
```json
{"field": "value"}
```

**Output:**
```json
{"field": "value"}
```

[Repeat for each interface]

---

## Step 6: Create [The Main Artifact]

**File:** `/path/to/create/file.py`

### Required Structure

```python
"""
[Docstring]
"""

# [Code skeleton with clear TODO markers]
```

---

## Step 7: [Additional Requirements]

[Any UI, CLI, or interface requirements]

---

## Step 8: Success Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]
- [ ] [Final verification]

---

## Step 9: Test Commands

### Test [Scenario 1]
```bash
[command]
```

### Test [Scenario 2]
```bash
[command]
```

---

## Step 10: Verification After Completion

Run these verification prompts (from `/home/squiz/ATLAS/docs/VERIFICATION_PROMPTS.md`):

### Code Review Self-Check
```
Review [file] for:
- [ ] [Check 1]
- [ ] [Check 2]
```

### Inversion Test
```
What would make this [artifact] WRONG?
- [Question 1]
- [Question 2]
```

### Junior Analyst Challenge
```
Spawn fresh agent to audit the code against this handover spec.
```

---

## DO NOT

- Do NOT [anti-pattern 1]
- Do NOT [anti-pattern 2]
- Do NOT [anti-pattern 3]

---

## After Completion

Report back with:
1. File(s) created and location(s)
2. Test results
3. Any edge cases discovered
4. Suggestions for next phase

---

## File Locations Summary

| What | Where |
|------|-------|
| **CREATE THIS** | `/path/to/new/file` |
| [Input 1] | `/path/to/input` |
| [Input 2] | `/path/to/input` |
| [Reference 1] | `/path/to/reference` |

---

## [Reference Data if needed]

```python
VALID_VALUES = {"a", "b", "c"}
```

---

# Accompanying Prompt File Template

Create a matching `PROMPT_PHASE[N]_FRESH_AGENT.md`:

```markdown
# Prompt for Fresh Agent - Phase [N] [Task Name]

Copy everything below this line to a fresh Opus agent:

---

# CRITICAL TASK: [Task Name]

[1-2 sentence context]

## Your Task

Read the handover document and execute Phase [N]:

\```
/home/squiz/ATLAS/docs/HANDOVER_PHASE[N]_[NAME].md
\```

## Quick Summary

1. **Create:** `/path/to/file`
2. **Implement:** [Main components]
3. **Test:** [Test approach]
4. **Report:** Confirm success criteria

## Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| 1 | Handover doc | Task spec |
| 2 | [Doc 2] | [Reason] |

## Critical Requirements

- [Requirement 1]
- [Requirement 2]

## DO NOT

- [Anti-pattern 1]
- [Anti-pattern 2]

Start by reading the handover document, then implement methodically.
```
