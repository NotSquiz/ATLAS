# Handover: Quality Audit Pipeline Enhancement

**Created:** January 9, 2026
**Priority:** HIGH - Ensures only Grade A content reaches production
**Fresh Agent Required:** Yes - Clean context for pipeline modification
**Prerequisite:** Phase 3 Pipeline Orchestrator (COMPLETE)

---

## Your Mission

Modify `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` to:
1. Use CLI mode (Max subscription) instead of API
2. Add a quality audit stage using BabyBrains voice standards
3. Only allow Grade A content to proceed to human review
4. Process 1 activity at a time for maximum quality

---

## Step 1: Read Context Documents (IN ORDER)

| Priority | Document | Location | Why |
|----------|----------|----------|-----|
| 1 | This handover | You're reading it | Complete task spec |
| 2 | Current pipeline | `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` | Code to modify |
| 3 | Voice Elevation Rubric | `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` | Grading criteria |
| 4 | BabyBrains-Writer Agent | `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` | Voice standards |

---

## Step 2: Understand the New Pipeline Flow

```
RAW ACTIVITY
       │
       ▼
┌─────────────────────┐
│ 1. INGEST           │
│ 2. RESEARCH         │
│ 3. TRANSFORM        │  Using CLI mode (Max subscription)
│ 4. ELEVATE          │
│ 5. VALIDATE         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 6. QC HOOK          │ Mechanical checks (em-dashes, sections, etc.)
└─────────┬───────────┘
          │
          │ pass? ──NO──► FAILED
          │
          ▼ YES
┌─────────────────────────────────────────┐
│ 7. QUALITY AUDIT (NEW)                  │
│                                         │
│ Sub-agent loads:                        │
│ - VOICE_ELEVATION_RUBRIC.md (grading)   │
│ - A+ reference activity (gold standard) │
│                                         │
│ Grades: A / B+ / B / C / F              │
│ Returns specific issues if not A        │
└─────────┬───────────────────────────────┘
          │
          │ Grade A? ──NO──► REVISION_NEEDED (with feedback)
          │
          ▼ YES
┌─────────────────────┐
│ 8. HUMAN REVIEW     │ Only sees Grade A content
└─────────────────────┘
```

---

## Step 3: Key Files

### Files to Read
| Purpose | Location |
|---------|----------|
| **Pipeline to modify** | `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` |
| **Voice Rubric** | `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` |
| **Voice Agent Spec** | `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` |
| **Reference A+ Activity** | `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml` |
| **SubAgentExecutor** | `/home/squiz/ATLAS/atlas/orchestrator/subagent_executor.py` |

### Reference A+ Activities (Gold Standards)
```
/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml
/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_FLOOR_CARE_18_36M.yaml
```

---

## Step 4: Implementation Changes

### Change 1: Switch to CLI Mode

**Location:** `__init__` method, around line 130-140

```python
# FIND:
self.skill_executor = SkillExecutor(use_api=True)

# REPLACE WITH:
# CLI mode for Max subscription (no API key needed)
self.skill_executor = SkillExecutor(timeout=300)  # 5 min timeout for CLI
```

Also remove or comment out the ANTHROPIC_API_KEY check if present:
```python
# REMOVE/COMMENT:
# if not os.environ.get("ANTHROPIC_API_KEY"):
#     raise ValueError("ANTHROPIC_API_KEY required")
```

---

### Change 2: Add Quality Audit Method

**Add this new method to the `ActivityConversionPipeline` class:**

```python
async def audit_quality(self, elevated_yaml: str, activity_id: str) -> dict:
    """
    Audit activity quality using BabyBrains voice standards.

    Spawns a fresh sub-agent to grade the activity against:
    - Voice Elevation Rubric criteria
    - A+ reference activity (gold standard)

    Returns:
        {
            "grade": "A" | "B+" | "B" | "C" | "F",
            "passed": bool,
            "issues": [{"category": str, "issue": str, "fix": str}],
            "philosophy_found": list[str],
            "philosophy_missing": list[str],
            "australian_voice": bool,
            "rationale_quality": str,
            "recommendation": str
        }
    """
    import json
    from pathlib import Path

    # Load grading context
    rubric_path = Path("/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md")
    reference_path = Path("/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml")

    rubric = rubric_path.read_text() if rubric_path.exists() else "Rubric not found"
    reference = reference_path.read_text() if reference_path.exists() else "Reference not found"

    audit_prompt = f"""You are a quality auditor for BabyBrains Activity Atoms.

## GRADING RUBRIC
{rubric}

## REFERENCE A+ ACTIVITY (Gold Standard)
```yaml
{reference}
```

## ACTIVITY TO AUDIT
```yaml
{elevated_yaml}
```

## YOUR TASK
Grade this activity using the Voice Elevation Rubric. Check:

1. **Anti-Pattern Check**: Any em-dashes (—), formal transitions (Moreover, Furthermore, etc.), superlatives (amazing, incredible)?
2. **Philosophy Integration**: Which of the 6 Montessori principles are present?
   - Cosmic View (connects to meaningful work)
   - Spiritual Embryo (child develops from within)
   - Adult as Obstacle (parent self-reflection prompts)
   - Freedom Within Limits (boundaries as loving structure)
   - Transformed Adult (adult self-regulation matters)
   - Creating Conditions Not Outcomes (anxiety-reducing)
3. **Australian Voice**: Understated confidence, tall poppy safe, cost-aware, correct vocab (mum, nappy, cot)?
4. **Rationale Field**: Does it follow the A+ pattern? (Observable → Philosophy → Parent psychology → Reassurance)
5. **Science Weaving**: Observable → Invisible → Meaningful pattern?

**IMPORTANT**: Grade A requires ALL checks to pass. Any em-dash = automatic B+ maximum.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "grade": "A",
  "passed": true,
  "issues": [],
  "philosophy_found": ["cosmic_view", "spiritual_embryo", "adult_as_obstacle", "freedom_within_limits", "transformed_adult", "creating_conditions"],
  "philosophy_missing": [],
  "australian_voice": true,
  "rationale_quality": "excellent",
  "recommendation": "Ready for production"
}}

OR if issues found:
{{
  "grade": "B+",
  "passed": false,
  "issues": [
    {{"category": "anti-pattern", "issue": "Em-dash found in description", "fix": "Replace with period or comma"}},
    {{"category": "philosophy", "issue": "Missing 'Adult as Obstacle' reflection", "fix": "Add prompt for parent self-awareness"}}
  ],
  "philosophy_found": ["cosmic_view", "spiritual_embryo"],
  "philosophy_missing": ["adult_as_obstacle", "transformed_adult"],
  "australian_voice": true,
  "rationale_quality": "needs_work",
  "recommendation": "Needs elevation - add philosophy integration and fix anti-patterns"
}}
"""

    logger.info(f"Running quality audit for {activity_id}")

    # Use SubAgentExecutor for fresh context
    result = await self.sub_executor.spawn(
        task=audit_prompt,
        context={"activity_id": activity_id, "audit_type": "voice_quality"},
        sandbox=True
    )

    # Parse JSON response
    if result.success and result.output:
        try:
            # Try to extract JSON from response
            output = result.output.strip()
            # Handle potential markdown code blocks
            if "```json" in output:
                output = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                output = output.split("```")[1].split("```")[0].strip()

            audit_result = json.loads(output)
            logger.info(f"Quality audit result: Grade {audit_result.get('grade')}")
            return audit_result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse audit response: {e}")
            logger.debug(f"Raw response: {result.output[:500]}")

    # Fallback on failure
    return {
        "grade": "F",
        "passed": False,
        "issues": [{"category": "audit", "issue": "Audit failed - could not parse response", "fix": "Manual review required"}],
        "philosophy_found": [],
        "philosophy_missing": [],
        "australian_voice": False,
        "rationale_quality": "unknown",
        "recommendation": "Audit failed - requires manual review"
    }
```

---

### Change 3: Integrate Audit into convert_activity()

**Find the section after QC hook passes (around line 630-650) and add:**

```python
# After QC HOOK section, before returning success:

# 7. QUALITY AUDIT
logger.info(f"Stage 7/8: QUALITY AUDIT for {raw_id}")
audit = await self.audit_quality(
    elevated_yaml=elevate.output.get("elevated_yaml", ""),
    activity_id=raw_id
)

# Store audit results in scratch pad
self.scratch_pad.set(f"{raw_id}_audit", audit)

if not audit.get("passed") or audit.get("grade") != "A":
    grade = audit.get("grade", "Unknown")
    logger.warning(f"Quality audit: Grade {grade} (requires A)")

    for issue in audit.get("issues", []):
        logger.warning(f"  [{issue.get('category')}] {issue.get('issue')}")
        if issue.get('fix'):
            logger.info(f"    Fix: {issue.get('fix')}")

    return ConversionResult(
        activity_id=raw_id,
        status=ActivityStatus.REVISION_NEEDED,
        canonical_id=transform.output.get("canonical_id"),
        file_path=transform.output.get("file_path"),
        error=f"Quality audit: Grade {grade} (need A)",
        warnings=[
            f"[{i.get('category')}] {i.get('issue')}"
            for i in audit.get("issues", [])
        ]
    )

logger.info(f"Quality audit PASSED: Grade A")
```

---

### Change 4: Add Retry Loop (Optional but Recommended)

**Add this new method:**

```python
async def convert_with_retry(self, raw_id: str, max_retries: int = 2) -> ConversionResult:
    """
    Convert activity with automatic retry if not Grade A.

    Args:
        raw_id: Activity ID to convert
        max_retries: Max attempts (default 2 retries = 3 total attempts)

    Returns:
        ConversionResult with final status
    """
    last_result = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            logger.info(f"Retry attempt {attempt}/{max_retries} for {raw_id}")

        result = await self.convert_activity(raw_id)
        last_result = result

        if result.status == ActivityStatus.DONE:
            if attempt > 0:
                logger.info(f"Succeeded on attempt {attempt + 1}")
            return result

        if result.status != ActivityStatus.REVISION_NEEDED:
            # Not a quality issue, don't retry
            return result

        if attempt >= max_retries:
            logger.warning(f"Max retries ({max_retries}) reached for {raw_id}")
            return result

        # Could pass audit feedback to next attempt here
        logger.info(f"Will retry - issues: {result.warnings[:3]}")

    return last_result
```

---

### Change 5: Update CLI Interface

**Find the argparse/click section at the bottom and update:**

```python
async def main():
    """Main entry point with quality-focused single activity processing."""
    import argparse

    parser = argparse.ArgumentParser(description="Activity Conversion Pipeline (Quality Mode)")
    parser.add_argument("--activity", "-a", help="Single activity ID to convert")
    parser.add_argument("--retry", type=int, default=2, help="Max retry attempts for non-A grades")
    parser.add_argument("--list-pending", action="store_true", help="List pending activities")

    args = parser.parse_args()

    pipeline = ActivityConversionPipeline()

    if args.list_pending:
        pending = pipeline.get_pending_activities()
        print(f"Pending activities: {len(pending)}")
        for i, act in enumerate(pending[:20], 1):
            print(f"  {i}. {act}")
        if len(pending) > 20:
            print(f"  ... and {len(pending) - 20} more")
        return

    if not args.activity:
        print("Usage: python -m atlas.pipelines.activity_conversion --activity <activity-id>")
        print("       python -m atlas.pipelines.activity_conversion --list-pending")
        return

    print(f"\n{'='*60}")
    print(f"QUALITY MODE: Processing {args.activity}")
    print(f"Max retries: {args.retry}")
    print(f"{'='*60}\n")

    result = await pipeline.convert_with_retry(args.activity, max_retries=args.retry)

    print(f"\n{'='*60}")
    print(f"RESULT: {result.status.value}")
    if result.status == ActivityStatus.DONE:
        print(f"Grade A - Ready for review!")
        print(f"Canonical ID: {result.canonical_id}")
        print(f"File path: {result.file_path}")
    else:
        print(f"Status: {result.status.value}")
        if result.error:
            print(f"Error: {result.error}")
        if result.warnings:
            print("Issues:")
            for w in result.warnings[:5]:
                print(f"  - {w}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Step 5: Voice Elevation Rubric Quick Reference

The rubric grades on a **A / B+ / B / C / F** scale:

### Grade A (Production Ready)
- Zero em-dashes
- Zero formal transitions (Moreover, Furthermore, etc.)
- Zero superlatives (amazing, incredible)
- All 6 philosophy principles present
- Australian voice authentic
- Rationale field follows pattern

### Grade B+ (Must Elevate)
- 1-2 fixable issues
- Missing 1-2 philosophy principles
- Minor voice issues

### Automatic Downgrades
- Any em-dash = B+ maximum
- Missing philosophy in rationale = B+ maximum
- Superlatives/formal transitions = B maximum

---

## Step 6: Success Criteria

- [ ] Pipeline uses CLI mode (no ANTHROPIC_API_KEY needed)
- [ ] `audit_quality()` method added and working
- [ ] Audit integrated after QC hook in `convert_activity()`
- [ ] Only Grade A activities reach human review
- [ ] Non-A grades return REVISION_NEEDED with specific issues
- [ ] Retry loop implemented (optional)
- [ ] CLI updated for single-activity mode

---

## Step 7: Test the Pipeline

### Test Single Activity (CLI Mode)
```bash
cd /home/squiz/ATLAS

# No API key needed - uses Max subscription via CLI
python -m atlas.pipelines.activity_conversion --activity tummy-time
```

### Expected Output (Grade A)
```
============================================================
QUALITY MODE: Processing tummy-time
Max retries: 2
============================================================

Stage 1/8: INGEST ✓
Stage 2/8: RESEARCH ✓
Stage 3/8: TRANSFORM ✓
Stage 4/8: ELEVATE ✓
Stage 5/8: VALIDATE ✓
Stage 6/8: QC HOOK ✓
Stage 7/8: QUALITY AUDIT ✓

============================================================
RESULT: done
Grade A - Ready for review!
Canonical ID: ACTIVITY_MOTOR_GROSS_TUMMY_TIME_0_6M
============================================================
```

### Expected Output (Needs Work)
```
Stage 7/8: QUALITY AUDIT...
Quality audit: Grade B+ (requires A)
  [philosophy] Missing 'Adult as Obstacle' reflection prompt
  [rationale] Needs observable → philosophy → reassurance pattern

Retry attempt 1/2 for tummy-time
...
```

---

## Step 8: Verification Prompts

After implementation, run these checks:

### Code Review
```
Review activity_conversion.py for:
- [ ] audit_quality() handles JSON parsing errors gracefully
- [ ] CLI mode timeout is sufficient (300s)
- [ ] Retry loop doesn't infinite loop
- [ ] Scratch pad saves audit results for debugging
```

### Inversion Test
```
What would make this audit WRONG?
- What Grade B+ activity might incorrectly pass as A?
- What Grade A activity might incorrectly fail?
- What if rubric file doesn't exist?
- What if sub-agent returns non-JSON?
```

---

## DO NOT

- Do NOT use API mode (user has Max subscription)
- Do NOT batch process (single activity only for quality)
- Do NOT skip quality audit stage
- Do NOT let non-A grades proceed to human review
- Do NOT modify the Voice Elevation Rubric

---

## After Completion

Report back with:
1. Confirmation CLI mode works (no API key)
2. Test result for single activity
3. Quality audit output example
4. Any edge cases discovered

---

## File Locations Summary

| What | Where |
|------|-------|
| **MODIFY THIS** | `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` |
| Voice Rubric | `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` |
| Voice Agent Spec | `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` |
| Reference A+ | `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml` |
| SubAgentExecutor | `/home/squiz/ATLAS/atlas/orchestrator/subagent_executor.py` |
