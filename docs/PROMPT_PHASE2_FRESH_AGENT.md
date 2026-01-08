# Prompt for Fresh Agent - Phase 2 QC Hook

Copy everything below this line to a fresh Opus agent:

---

# CRITICAL TASK: Create Activity QC Hook

You are creating a production-quality Python validator for the BabyBrains Activity Atom pipeline. This hook will gate 175+ activity conversions. **Zero tolerance for errors.**

## Your Task

Read the handover document and execute Phase 2:

```
/home/squiz/ATLAS/docs/HANDOVER_PHASE2_QC_HOOK.md
```

This document contains:
- Exact requirements for the QC hook
- All 32 required sections to validate
- Block codes to implement
- Valid principle slugs
- Test procedures
- Success criteria

## Quick Summary

1. **Create:** `/home/squiz/code/knowledge/scripts/check_activity_quality.py`
2. **Register:** Add hook to `/home/squiz/ATLAS/atlas/orchestrator/hooks.py`
3. **Test:** Run against sample canonical activity
4. **Report:** Confirm all success criteria met

## Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| 1 | `HANDOVER_PHASE2_QC_HOOK.md` | Your exact task spec |
| 2 | Voice rubric | `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` |
| 3 | Sample canonical | `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_WASHING_FRUITS_VEGETABLES_12_36M.yaml` |
| 4 | Existing hooks | `/home/squiz/ATLAS/atlas/orchestrator/hooks.py` |

## Critical Requirements

- Detect ALL em-dashes (—)
- Detect formal transitions at sentence start (Moreover, Furthermore, etc.)
- Detect superlatives (amazing, incredible, wonderful, etc.)
- Validate all 32 required YAML sections
- Validate principle slugs against valid list
- Return JSON with passed/issues/warnings/stats
- Exit 0 for pass, 1 for fail

Start by reading the handover document, then implement methodically.
