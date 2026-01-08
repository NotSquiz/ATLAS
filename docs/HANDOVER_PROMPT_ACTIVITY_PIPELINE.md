# Handover Prompt: Activity Pipeline Phase 2

Copy everything below this line to a fresh agent:

---

# Context: Activity Atom Conversion Pipeline

You are continuing work on automating the conversion of 175 raw Montessori activities into AAA+ canonical Activity Atoms using ATLAS V2 orchestrator.

## What Was Completed (Phase 1)

5 ATLAS-compatible skills were created and verified working:
- `ingest_activity.md` - Parse raw activities
- `research_activity.md` - Find sources, principles, safety
- `transform_activity.md` - Build 32-section canonical YAML
- `elevate_voice_activity.md` - Apply BabyBrains voice
- `validate_activity.md` - Structure validation

Location: `/home/squiz/code/babybrains-os/skills/activity/`

## Your Task: Phase 2 - QC Hook

Create the QC hook that validates Activity Atoms before human review.

### Step 1: Read the handover document
```
/home/squiz/ATLAS/docs/HANDOVER_ACTIVITY_PIPELINE.md
```

### Step 2: Read the full plan
```
/home/squiz/.claude/plans/dazzling-popping-wozniak.md
```

### Step 3: Create QC Hook

Create `/home/squiz/code/knowledge/scripts/check_activity_quality.py`:

**Requirements:**
- Accept YAML via stdin
- Voice scan: count em-dashes (—), formal transitions, superlatives
- Structure check: verify all 32 sections present
- Cross-ref check: validate guidance/material/principle slugs
- Output JSON: `{"passed": bool, "issues": [], "warnings": []}`
- Exit 0 if passed, non-zero if blocking issues

**Block codes to implement:**
- `VOICE_EM_DASH` - Any em-dash found
- `VOICE_FORMAL_TRANSITION` - Moreover/Furthermore/etc at sentence start
- `VOICE_SUPERLATIVE` - amazing/incredible/etc
- `STRUCTURE_MISSING_SECTION` - Required section missing
- `CROSS_REF_BROKEN` - Invalid guidance/material reference

### Step 4: Register Hook in ATLAS

Add to `/home/squiz/ATLAS/atlas/orchestrator/hooks.py`:

```python
HOOKS["knowledge"]["activity_qc"] = {
    "cmd": ["python3", "scripts/check_activity_quality.py"],
    "cwd": "/home/squiz/code/knowledge",
    "blocking": True,
    "timing": HookTiming.POST_EXECUTION,
    "input_mode": "stdin",
    "output_format": "json",
    "block_codes": [
        "VOICE_EM_DASH",
        "VOICE_FORMAL_TRANSITION",
        "VOICE_SUPERLATIVE",
        "STRUCTURE_MISSING_SECTION",
        "CROSS_REF_BROKEN",
    ],
}
```

## Key Reference Files

| What | Path |
|------|------|
| Voice standard | `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` |
| Voice rubric | `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` |
| Example canonical | `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_WASHING_FRUITS_VEGETABLES_12_36M.yaml` |
| ATLAS hooks.py | `/home/squiz/ATLAS/atlas/orchestrator/hooks.py` |
| Skills created | `/home/squiz/code/babybrains-os/skills/activity/` |

## Success Criteria

- [ ] `check_activity_quality.py` created and tested
- [ ] Correctly detects em-dashes, transitions, superlatives
- [ ] Validates 32-section structure
- [ ] Returns proper JSON format
- [ ] Hook registered in ATLAS
- [ ] Test with sample canonical activity

## After Phase 2

Phase 3: Create pipeline orchestrator (`atlas/pipelines/activity_conversion.py`)
Phase 4: Build human review interface
