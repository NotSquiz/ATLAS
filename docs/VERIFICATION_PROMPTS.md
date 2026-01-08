# ATLAS Verification Prompts Reference

**Purpose:** Prompt patterns agents should use to verify their own work.

---

## 1. The "Wait" Pattern (89.3% Blind Spot Reduction)

From Anthropic introspection research. Use before self-correction:

```
Wait. Before evaluating, pause and consider:
- What assumptions did I make?
- Where might I be wrong?
- What would I tell someone else who gave this answer?

Now evaluate and correct if needed:
```

**Code:** `from atlas.orchestrator.confidence_router import apply_wait_pattern`

---

## 2. Adversarial Self-Check

After generating content, ask yourself:

```
Acting as a skeptical reviewer, identify:
1. Claims that lack evidence
2. Assumptions stated as facts
3. Edge cases not handled
4. Security vulnerabilities introduced
5. Breaking changes to existing functionality
```

---

## 3. Junior Analyst Challenge

For critical outputs, spawn a verification sub-agent:

```
You are a junior analyst at McKinsey. Your job is to find problems.

Review this output and identify:
- Logical inconsistencies
- Missing error handling
- Untested assumptions
- Potential failures under edge cases

Be thorough. Your reputation depends on catching issues.
```

---

## 4. Confidence Extraction

When uncertain, explicitly state confidence:

```
Before answering, rate your confidence:
- HIGH (>80%): I have direct knowledge/evidence
- MEDIUM (50-80%): Reasonable inference but not certain
- LOW (<50%): Speculating or unsure

State your confidence level, then answer.
```

---

## 5. Fact-Check Prompt

For factual claims:

```
For each factual claim in my response:
1. Is this from my training data or am I inferring?
2. Could this be outdated?
3. Is there a primary source I should cite?
4. Am I conflating similar concepts?
```

---

## 6. Code Review Self-Check

After writing code:

```
Review this code for:
- [ ] Unhandled exceptions (bare except?)
- [ ] Missing input validation
- [ ] Security issues (injection, path traversal)
- [ ] Race conditions
- [ ] Resource leaks
- [ ] Breaking API changes
- [ ] Missing logging
```

---

## 7. Documentation Completeness

After documenting:

```
Check documentation for:
- [ ] Usage examples included?
- [ ] All parameters documented?
- [ ] Return values specified?
- [ ] Error conditions listed?
- [ ] Dependencies mentioned?
```

---

## 8. The Inversion Test

For recommendations/decisions:

```
What would make this recommendation WRONG?
- Under what conditions would this fail?
- What's the strongest argument against this?
- What am I not considering?
```

---

## Quick Reference Table

| Situation | Use This Pattern |
|-----------|------------------|
| Self-correcting | "Wait" pattern |
| Critical output | Junior Analyst Challenge |
| Factual claims | Fact-Check Prompt |
| Code changes | Code Review Self-Check |
| Uncertain | Confidence Extraction |
| Decisions | Inversion Test |

---

## Implementation

```python
from atlas.orchestrator.confidence_router import (
    apply_wait_pattern,      # Generates "Wait" prompt
    route_by_confidence,     # Routes by extracted confidence
    extract_confidence,      # Gets confidence score from text
)
```

---

*Agents should use these patterns proactively, especially for safety-critical domains.*
