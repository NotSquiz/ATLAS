# HANDOVER: Activity Atom Conversion Pipeline

**Created:** 2026-01-08
**Context:** Session ran out of context after completing Phase 1
**Status:** Phase 1 COMPLETE, Phase 2-4 PENDING

---

## What Was Built

5 ATLAS-compatible skills for converting raw Montessori activities into AAA+ canonical Activity Atoms.

### Skills Created (Phase 1 COMPLETE)

| Skill | Location | Purpose |
|-------|----------|---------|
| `ingest_activity.md` | `/home/squiz/code/babybrains-os/skills/activity/` | Parse raw activity, check skip/group/domain |
| `research_activity.md` | `/home/squiz/code/babybrains-os/skills/activity/` | Find sources, principles, safety standards |
| `transform_activity.md` | `/home/squiz/code/babybrains-os/skills/activity/` | Build 32-section canonical YAML |
| `elevate_voice_activity.md` | `/home/squiz/code/babybrains-os/skills/activity/` | Apply BabyBrains AAA+ voice |
| `validate_activity.md` | `/home/squiz/code/babybrains-os/skills/activity/` | Structure and cross-ref validation |
| `ACTIVITY_PIPELINE_GUIDE.md` | `/home/squiz/code/babybrains-os/skills/activity/` | How skills chain together |

### Verified Working
```bash
cd /home/squiz/ATLAS
python3 -c "from atlas.orchestrator.skill_executor import SkillLoader; loader = SkillLoader(); print(loader.list_skill_sections('activity/ingest_activity'))"
```
All 5 skills load correctly with ATLAS SkillLoader.

---

## The Goal

Convert **175-185 raw Montessori activities** into **AAA+ canonical Activity Atoms** using ATLAS V2 orchestrator.

**Current manual process:** Human copies prompt to fresh Opus agent, agent processes 1 activity, human reviews.
**Target automated process:** ATLAS orchestrates skill chain, QC hooks validate, human reviews at end only.

**Progress so far:** 6 of ~175 converted manually (before automation built)

---

## Full Plan

Read the complete plan: `/home/squiz/.claude/plans/dazzling-popping-wozniak.md`

### Key Decisions (Already Made)
- **Automation:** Semi-automated (human reviews each activity before write)
- **Parallelization:** Sequential (safest)
- **Skill location:** babybrains-os/skills/activity/
- **QC failure:** Flag and continue (don't block pipeline)

### Pipeline Flow
```
RAW ACTIVITY
    ↓
[ingest_activity] → skip/group/domain check
    ↓
[research_activity] → principles, safety, guidance
    ↓
[transform_activity] → build 32-section YAML
    ↓
[elevate_voice_activity] → BabyBrains voice
    ↓
[validate_activity] → structure, cross-refs
    ↓
[QC Hook] → voice scan, validators
    ↓
[Adversarial] → fresh agent double-check
    ↓
[Human Review] → approve/reject
    ↓
WRITE FILE
```

---

## What Needs to Happen Next

### Phase 2: QC Hook (NEXT)
Create `/home/squiz/code/knowledge/scripts/check_activity_quality.py`:
- Voice scan (em-dashes, formal transitions, superlatives)
- Structure check (32 sections present)
- Cross-ref validation
- Return JSON with pass/fail

Register in ATLAS hooks.py:
```python
HOOKS["knowledge"]["activity_qc"] = {
    "cmd": ["python3", "scripts/check_activity_quality.py"],
    "cwd": "/home/squiz/code/knowledge",
    "blocking": True,
    "timing": HookTiming.POST_EXECUTION,
    "input_mode": "stdin",
    "output_format": "json",
}
```

### Phase 3: Pipeline Orchestrator
Create `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py`:
- Load pending activities from CONVERSION_PROGRESS.md
- Execute skill chain for each
- Handle skip/fail/success
- Present to human for review

### Phase 4: Human Review Interface
- Present activity with QC results
- Approve → write file, update ledger
- Reject → log feedback
- Skip → come back later

---

## Critical Reference Documents

### Voice Standard (MUST READ)
`/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` (1713 lines)
- Australian voice requirements
- Anti-patterns (em-dashes, formal transitions, superlatives)
- Parent psychology integration
- Philosophy weaving

### Grading Rubric
`/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md`
- Grade A only is acceptable
- What makes B+ (rejected)

### Raw Activities Source
`/home/squiz/code/knowledge/sources/structured/activities_v1/activities_fixed_01.yaml`
- 238 raw activities
- YAML format with id, domain, age_range, presentation_steps, etc.

### Conversion Mapping
`/home/squiz/code/knowledge/.claude/workflow/ACTIVITY_CONVERSION_MAP.yaml`
- Skip list (duplicates)
- Groups (combine multiple into one)
- Domain corrections

### Progress Tracking
`/home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md`
- Which activities are done/pending/failed

### Current Manual Workflow
`/home/squiz/code/knowledge/.claude/workflow/HANDOFF_CONVERSION_SESSION.md`
- Template used for manual conversions
- Shows exact 32-section structure required

### Reference Canonical File
`/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_WASHING_FRUITS_VEGETABLES_12_36M.yaml`
- Example of completed AAA+ activity

### ATLAS V2 Guide
`/home/squiz/ATLAS/docs/V2_ORCHESTRATOR_GUIDE.md`
- How to use SkillLoader, SubAgentExecutor, HookRunner, etc.

---

## Quick Start for New Agent

1. **Read this file first**

2. **Read the skills** (in order):
   ```
   /home/squiz/code/babybrains-os/skills/activity/ingest_activity.md
   /home/squiz/code/babybrains-os/skills/activity/research_activity.md
   /home/squiz/code/babybrains-os/skills/activity/transform_activity.md
   /home/squiz/code/babybrains-os/skills/activity/elevate_voice_activity.md
   /home/squiz/code/babybrains-os/skills/activity/validate_activity.md
   /home/squiz/code/babybrains-os/skills/activity/ACTIVITY_PIPELINE_GUIDE.md
   ```

3. **Read the full plan**:
   `/home/squiz/.claude/plans/dazzling-popping-wozniak.md`

4. **Start Phase 2**: Create the QC hook

---

## File Locations Summary

| What | Where |
|------|-------|
| Activity skills | `/home/squiz/code/babybrains-os/skills/activity/` |
| Voice standard | `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` |
| Raw activities | `/home/squiz/code/knowledge/sources/structured/activities_v1/activities_fixed_01.yaml` |
| Conversion map | `/home/squiz/code/knowledge/.claude/workflow/ACTIVITY_CONVERSION_MAP.yaml` |
| Progress tracker | `/home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md` |
| Manual template | `/home/squiz/code/knowledge/.claude/workflow/HANDOFF_CONVERSION_SESSION.md` |
| Full plan | `/home/squiz/.claude/plans/dazzling-popping-wozniak.md` |
| ATLAS V2 docs | `/home/squiz/ATLAS/docs/V2_ORCHESTRATOR_GUIDE.md` |
| This handover | `/home/squiz/ATLAS/docs/HANDOVER_ACTIVITY_PIPELINE.md` |

---

## Contact Points

- **knowledge repo**: Raw activities, canonical outputs, validators
- **babybrains-os repo**: Skills, voice standard
- **ATLAS repo**: Orchestrator, hooks, pipelines

---

## Status Checklist

- [x] Phase 1: Skills created (5 skills + guide)
- [x] Phase 1: Skills verified loading with ATLAS
- [x] Phase 2: QC hook created (`/home/squiz/code/knowledge/scripts/check_activity_quality.py`)
- [x] Phase 2: Hook registered in ATLAS (`knowledge/activity_qc`)
- [ ] Phase 3: Pipeline orchestrator created
- [ ] Phase 4: Human review interface built
- [ ] Integration testing
- [ ] First automated conversion

## Phase Handover Documents

| Phase | Document | Status |
|-------|----------|--------|
| Phase 2 | `docs/HANDOVER_PHASE2_QC_HOOK.md` | COMPLETE |
| Phase 3 | `docs/HANDOVER_PHASE3_PIPELINE.md` | READY FOR FRESH AGENT |
