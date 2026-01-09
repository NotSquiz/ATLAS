# Skill Improvement Notes

**Based on:** Real pipeline test with `narrating-daily-care` activity
**Date:** January 9, 2026

---

## QC Failures Found

The pipeline ran end-to-end successfully, but the QC hook correctly caught 3 issues in the LLM-generated output:

### 1. VOICE_EM_DASH
**Skill:** `elevate_voice_activity.md`
**Issue:** Em-dash character (U+2014) found at line 25
**Root Cause:** The elevate skill isn't detecting/replacing em-dashes
**Fix Required:**
- Add em-dash detection to the elevate skill checklist
- Replace with proper alternatives (commas, colons, or reworded sentences)
- Add explicit instruction: "NEVER use em-dashes (—). Use commas or colons instead."

### 2. STRUCTURE_MISSING_SECTION
**Skill:** `transform_activity.md`
**Issue:** Required section `au_cultural_adaptation.au_resources` is missing
**Root Cause:** Transform skill template doesn't include all 34 sections
**Fix Required:**
- Audit transform skill against full 34-section list
- Ensure `au_cultural_adaptation` has all 3 subsections:
  - `au_cultural_notes`
  - `au_compliance_standards`
  - `au_resources` ← MISSING
- Add explicit template with all section headers

### 3. CROSS_REF_INVALID_PRINCIPLE
**Skill:** `transform_activity.md`
**Issue:** Invalid principle slug 'respect' at index 1
**Root Cause:** LLM inventing principle slugs not in valid list
**Valid Slugs (18 total):**
```
absorbent_mind, concentration, cosmic_view, freedom_within_limits,
grace_and_courtesy, independence, maximum_effort, movement,
normalization, observation, order, practical_life, prepared_environment,
repetition, sensitive_periods, sensorial, spiritual_embryo, work_of_the_child
```
**Fix Required:**
- Add explicit valid slug list to transform skill
- Add validation instruction: "ONLY use slugs from this exact list"
- Consider adding "respect" as alias mapping → `grace_and_courtesy`

---

## Recommended Skill Updates

### transform_activity.md
Location: `/home/squiz/code/babybrains-os/skills/activity/transform_activity.md`

1. Add complete 34-section template with all fields
2. Add explicit list of 18 valid principle slugs
3. Add AU section structure with all 3 subsections:
   ```yaml
   au_cultural_adaptation:
     au_cultural_notes: "..."
     au_compliance_standards: ["..."]
     au_resources: ["..."]  # ← This was missing
   ```

### elevate_voice_activity.md
Location: `/home/squiz/code/babybrains-os/skills/activity/elevate_voice_activity.md`

1. Add em-dash detection to voice checklist
2. Add explicit "NEVER use em-dashes" instruction
3. Consider adding character-level checks before returning

---

## Verification After Fixes

After updating skills, re-run:
```bash
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python -c "
import asyncio
from atlas.pipelines.activity_conversion import ActivityConversionPipeline

async def test():
    p = ActivityConversionPipeline()
    result = await p.convert_activity('vocalization-imitation')
    print(f'Status: {result.status.value}')
    if result.qc_issues:
        print(f'Issues: {result.qc_issues}')
    else:
        print('QC PASSED!')

asyncio.run(test())
"
```

Target: Zero QC issues on a simple activity.

---

## Related Files

| File | Purpose |
|------|---------|
| `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` | Pipeline orchestrator |
| `/home/squiz/code/knowledge/scripts/check_activity_quality.py` | QC hook |
| `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` | Voice grading criteria |
| `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` | Voice standard (1713 lines) |
