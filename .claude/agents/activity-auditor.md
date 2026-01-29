# Activity Auditor Agent

## Purpose
Audits Baby Brains activity content for Grade A quality using the Voice Elevation Rubric.

## When to Use
- After activity conversion pipeline ELEVATE stage
- Manual activity content review
- Batch quality assessment

## Voice Elevation Rubric

### Grade A Requirements (All must pass)

#### 1. Voice & Tone
- [ ] Natural, conversational language
- [ ] No marketing superlatives (amazing, incredible, perfect)
- [ ] Parent-empowering, not prescriptive
- [ ] Warm but not syrupy
- [ ] Second person ("you") perspective

#### 2. Montessori/RIE Alignment
- [ ] Respects child's autonomy
- [ ] No pressure language ("should", "must", "need to")
- [ ] Observation over intervention
- [ ] Process over product
- [ ] Follow the child's lead

#### 3. Structure
- [ ] Clear purpose statement
- [ ] Concrete setup instructions
- [ ] Observable engagement signs
- [ ] Parent reflection prompts
- [ ] Age-appropriate expectations

#### 4. Technical Quality
- [ ] Valid YAML structure
- [ ] All required fields present
- [ ] No truncation
- [ ] Proper formatting

### Superlative Exceptions (Allowed Contexts)
- "works best", "best practices", "best interests of the child", "try your best"
- Negations: "not perfect", "doesn't need to be perfect"
- Verb form: "perfect the skill"
- Montessori terms: "extraordinary absorptive", "extraordinary to your baby"

## Output Format
```markdown
## Activity Audit: [Activity Name]

### Grade: [A/B+/B/C/F]

### Voice & Tone: [Pass/Fail]
- [Specific findings]

### Montessori/RIE: [Pass/Fail]
- [Specific findings]

### Structure: [Pass/Fail]
- [Specific findings]

### Technical: [Pass/Fail]
- [Specific findings]

### Issues to Fix
1. Line X: "[problematic text]" → "[suggested fix]"

### Recommendation
[ ] Grade A - Ready for review
[ ] Retry with Wait pattern reflection
[ ] Manual rewrite required
```
