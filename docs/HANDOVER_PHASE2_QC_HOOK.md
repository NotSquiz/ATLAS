# Phase 2 Handover: Activity QC Hook Creation

**Created:** January 9, 2026
**Priority:** CRITICAL - This is production infrastructure
**Fresh Agent Required:** Yes - Clean context for quality assurance

---

## Your Mission

Create a Python QC hook that validates Activity Atoms for voice quality, structure completeness, and cross-reference integrity. This hook will gate all 175+ activity conversions before human review.

**Zero tolerance for errors** - this validator must catch ALL voice violations and structural issues.

---

## Step 1: Read Context Documents (IN ORDER)

```
1. /home/squiz/ATLAS/docs/HANDOVER_ACTIVITY_PIPELINE.md  (full context)
2. /home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md  (grading criteria)
3. /home/squiz/code/web/.claude/agents/BabyBrains-Writer.md  (voice standard - 1713 lines)
```

---

## Step 2: Examine Reference Files

**Sample canonical activity (gold standard):**
```
/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_WASHING_FRUITS_VEGETABLES_12_36M.yaml
```

**Existing hooks implementation:**
```
/home/squiz/ATLAS/atlas/orchestrator/hooks.py
```

---

## Step 3: Create the QC Hook

**File:** `/home/squiz/code/knowledge/scripts/check_activity_quality.py`

### Requirements

**Input:** YAML content via stdin
**Output:** JSON to stdout with structure:
```json
{
  "passed": true|false,
  "issues": [
    {"code": "VOICE_EM_DASH", "severity": "blocking", "message": "Em-dash found at line 45", "line": 45}
  ],
  "warnings": [
    {"code": "WARN_MATERIAL_UNKNOWN", "message": "Material slug 'xyz' not in catalog"}
  ],
  "stats": {
    "em_dash_count": 0,
    "formal_transition_count": 0,
    "superlative_count": 0,
    "sections_found": 34,
    "sections_missing": []
  }
}
```

**Exit codes:**
- 0 = Passed (may have warnings)
- 1 = Failed (blocking issues found)

### Block Codes (MUST IMPLEMENT)

| Code | Severity | Trigger |
|------|----------|---------|
| `VOICE_EM_DASH` | blocking | Any em-dash character (—) found anywhere |
| `VOICE_FORMAL_TRANSITION` | blocking | Moreover/Furthermore/Consequently/Nevertheless/Hence/Thus/Therefore at sentence start |
| `VOICE_SUPERLATIVE` | blocking | amazing/incredible/wonderful/perfect/optimal/best (context-aware) |
| `STRUCTURE_MISSING_SECTION` | blocking | Any of the 34 required sections missing |
| `STRUCTURE_INVALID_YAML` | blocking | YAML parse error |
| `CROSS_REF_INVALID_PRINCIPLE` | blocking | Principle slug not in valid list |

### Warning Codes (non-blocking)

| Code | Trigger |
|------|---------|
| `WARN_MATERIAL_UNKNOWN` | Material slug not in catalog (catalog incomplete) |
| `WARN_GUIDANCE_MISSING` | Guidance file doesn't exist (may need creation) |
| `WARN_AGE_EXTREME` | Age range at boundaries (-9 or 72 months) |

### The 34 Required Sections

From the transform_activity.md skill, these sections MUST be present:

```yaml
# SECTION 1-6: METADATA
type, canonical_id, canonical_slug, version, last_updated, canonical

# SECTION 7: QUALITY REVIEW
quality_review (with story_id, qc_notes, voice_elevation)

# SECTION 8-12: CORE CONTENT
title, summary, age_months_min, age_months_max, domain

# SECTION 13: DESCRIPTION
description

# SECTION 14: GOALS
goals

# SECTION 15-16: SETUP
setup, environment_preparation

# SECTION 17: EXECUTION STEPS
execution_steps (array with step/action/details/rationale)

# SECTION 18-19: OBSERVATION
observation_focus, typical_progression

# SECTION 20-21: SAFETY
safety_considerations, contraindications

# SECTION 22: MATERIALS
requires_materials

# SECTION 23: PRINCIPLES
grounded_in_principles

# SECTION 24: GUIDANCE LINKS
links_to_guidance

# SECTION 25-27: EVIDENCE
evidence_strength, stated_in_sources, modern_validation

# SECTION 28-30: AU ADAPTATION
au_cultural_adaptation, au_compliance_standards, au_resources

# SECTION 31: PRODUCTION NOTES
production_notes

# SECTION 32: TAGS AND METADATA
tags, priority_ranking, query_frequency_estimate, parent_search_terms
```

### Valid Principle Slugs (18 total)

```python
VALID_PRINCIPLES = {
    "absorbent_mind",
    "sensitive_periods",
    "prepared_environment",
    "independence",
    "practical_life",
    "grace_and_courtesy",
    "maximum_effort",
    "order",
    "movement",
    "concentration",
    "repetition",
    "sensorial",
    "work_of_the_child",
    "freedom_within_limits",
    "cosmic_view",
    "observation",
    "normalization",
    "spiritual_embryo",
}
```

### Formal Transitions to Block

```python
FORMAL_TRANSITIONS = [
    "moreover",
    "furthermore",
    "consequently",
    "nevertheless",
    "hence",
    "thus",
    "therefore",
    "however",  # Only at sentence start
]
```

### Superlatives to Block

```python
SUPERLATIVES = [
    "amazing",
    "incredible",
    "wonderful",
    "perfect",
    "optimal",
    "best",
    "fantastic",
    "extraordinary",
]
```

---

## Step 4: Register Hook in ATLAS

**File:** `/home/squiz/ATLAS/atlas/orchestrator/hooks.py`

Add to the HOOKS dictionary (find existing structure):

```python
# Add "knowledge" repo if not exists, then add hook
"knowledge": {
    "activity_qc": {
        "cmd": ["python3", "scripts/check_activity_quality.py"],
        "cwd": "/home/squiz/code/knowledge",
        "blocking": True,
        "timing": HookTiming.POST_EXECUTION,
        "input_mode": "stdin",
        "output_format": "json",
    },
},
```

---

## Step 5: Test the Hook

**Test with sample canonical activity:**
```bash
cat /home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_WASHING_FRUITS_VEGETABLES_12_36M.yaml | python3 /home/squiz/code/knowledge/scripts/check_activity_quality.py
```

**Expected output for a good file:**
```json
{
  "passed": true,
  "issues": [],
  "warnings": [],
  "stats": {
    "em_dash_count": 0,
    "formal_transition_count": 0,
    "superlative_count": 0,
    "sections_found": 34,
    "sections_missing": []
  }
}
```

**Test with intentionally bad content:**
```bash
echo "description: This is an amazing—truly incredible activity" | python3 /home/squiz/code/knowledge/scripts/check_activity_quality.py
```

Should detect: em-dash, "amazing", "incredible"

---

## Success Criteria

- [ ] `check_activity_quality.py` exists and runs without errors
- [ ] Correctly detects em-dashes (test with — character)
- [ ] Correctly detects formal transitions at sentence start
- [ ] Correctly detects superlatives
- [ ] Validates all 34 sections present
- [ ] Validates principle slugs against valid list
- [ ] Returns proper JSON format
- [ ] Exit code 0 for pass, 1 for fail
- [ ] Hook registered in ATLAS hooks.py
- [ ] Sample canonical activity passes (it should be clean)
- [ ] Intentionally bad content fails appropriately

---

## DO NOT

- Do NOT modify the sample canonical activity
- Do NOT change the 34-section structure
- Do NOT add dependencies beyond Python standard library + PyYAML
- Do NOT skip any block codes listed above

---

## After Completion

Report back with:
1. File created and location
2. Test results (sample canonical + intentionally bad)
3. Hook registration confirmation
4. Any edge cases discovered

Phase 3 (Pipeline Orchestrator) will be handled by another agent after this is verified.
