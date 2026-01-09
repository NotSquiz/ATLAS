# Prompt for Fresh Agent - Phase 3 Pipeline Orchestrator

Copy everything below this line to a fresh Opus agent:

---

# CRITICAL TASK: Create Activity Pipeline Orchestrator

You are creating the automation pipeline that will convert 175+ raw Montessori activities into canonical Activity Atoms. This orchestrator wires together 5 skills, a QC hook, and human review.

## Your Task

Read the handover document and execute Phase 3:

```
/home/squiz/ATLAS/docs/HANDOVER_PHASE3_PIPELINE.md
```

This document contains:
- Complete data flow diagram
- Input file structures (raw activities, conversion map, progress tracker)
- ATLAS V2 component usage (SkillExecutor, HookRunner, SessionManager)
- Skill I/O contracts for all 5 skills
- Pipeline orchestrator code skeleton
- Human review interface design
- Test commands
- Success criteria

## Quick Summary

1. **Create:** `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py`
2. **Implement:** ActivityConversionPipeline class
3. **Test:** Single activity conversion + batch processing
4. **Report:** Confirm all success criteria met

## Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| 1 | `HANDOVER_PHASE3_PIPELINE.md` | Your exact task spec |
| 2 | V2 Orchestrator Guide | `/home/squiz/ATLAS/docs/V2_ORCHESTRATOR_GUIDE.md` |
| 3 | Activity Pipeline Overview | `/home/squiz/ATLAS/docs/HANDOVER_ACTIVITY_PIPELINE.md` |
| 4 | Existing orchestrator components | `/home/squiz/ATLAS/atlas/orchestrator/*.py` |

## Critical Requirements

- Load 238 raw activities from YAML source
- Parse conversion map (skip list, groups, domain corrections)
- Execute 5-skill chain: ingest → research → transform → elevate → validate
- Run QC hook (check_activity_quality.py) as gate
- Present activities for human review before writing
- Update CONVERSION_PROGRESS.md after each activity
- Handle errors gracefully with logging

## DO NOT

- Modify raw activities source file
- Skip human review step
- Write files without user approval
- Add dependencies beyond ATLAS standard

Start by reading the handover document, then implement methodically.
