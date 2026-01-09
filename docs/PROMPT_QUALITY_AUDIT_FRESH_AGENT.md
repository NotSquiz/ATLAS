# Prompt for Fresh Agent - Quality Audit Pipeline Enhancement

Copy everything below this line to a fresh Opus agent:

---

# TASK: Add Quality Audit to Activity Pipeline

You are enhancing the Activity Conversion Pipeline to ensure only Grade A content reaches production.

## Your Task

Read the handover document and implement the changes:

```
/home/squiz/ATLAS/docs/HANDOVER_QUALITY_AUDIT_PIPELINE.md
```

## Quick Summary

**File to modify:** `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py`

**Changes needed:**
1. Switch from API mode to CLI mode (Max subscription)
2. Add `audit_quality()` method that grades activities A/B+/B/C/F
3. Integrate audit after QC hook - only Grade A proceeds
4. Update CLI for single-activity processing

## Key Files

| Purpose | Location |
|---------|----------|
| Pipeline to modify | `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` |
| Voice Rubric (grading) | `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` |
| Reference A+ Activity | `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml` |

## Critical Requirements

- **CLI mode**: No ANTHROPIC_API_KEY - uses Max subscription via `claude` CLI
- **Quality audit**: Spawn sub-agent to grade against Voice Elevation Rubric
- **Grade A only**: Non-A grades return REVISION_NEEDED with specific issues
- **Single activity**: Process 1 at a time for maximum quality

## Test Command

```bash
# No API key needed
python -m atlas.pipelines.activity_conversion --activity tummy-time
```

## DO NOT

- Use API mode (user has Max subscription)
- Allow batch processing
- Let non-A grades proceed to human review

Start by reading the handover document, then implement the changes.
