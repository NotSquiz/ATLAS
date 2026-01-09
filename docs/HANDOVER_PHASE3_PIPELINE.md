# Phase 3 Handover: Activity Pipeline Orchestrator

**Created:** January 9, 2026
**Priority:** HIGH - Enables automated conversion of 175+ activities
**Fresh Agent Required:** Yes - Clean context for complex orchestration work
**Prerequisite:** Phase 2 QC Hook (COMPLETE)

---

## Your Mission

Create `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` - a pipeline orchestrator that automates the conversion of raw Montessori activities into canonical Activity Atoms using ATLAS V2 components.

**The Goal:** Convert 175+ raw activities to AAA+ canonical format with human review at the end only.

---

## Step 1: Read Context Documents (IN ORDER)

| Priority | Document | Location | Why |
|----------|----------|----------|-----|
| 1 | This handover | You're reading it | Complete task spec |
| 2 | V2 Orchestrator Guide | `/home/squiz/ATLAS/docs/V2_ORCHESTRATOR_GUIDE.md` | How to use ATLAS components |
| 3 | Activity Pipeline Overview | `/home/squiz/ATLAS/docs/HANDOVER_ACTIVITY_PIPELINE.md` | Full pipeline context |
| 4 | Pipeline Guide | `/home/squiz/code/babybrains-os/skills/activity/ACTIVITY_PIPELINE_GUIDE.md` | How skills chain |

---

## Step 2: Understand the Data Flow

```
RAW ACTIVITY (activities_fixed_01.yaml)
       │
       ▼
┌─────────────────────┐
│ ingest_activity     │ Check skip/group/domain
│ OUTPUT: {ingest}    │
└─────────┬───────────┘
          │
          │ should_skip? ──YES──► SKIP (update progress)
          │
          ▼ NO
┌─────────────────────┐
│ research_activity   │ Find principles, safety, sources
│ OUTPUT: {research}  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ transform_activity  │ Build 34-section YAML
│ OUTPUT: {yaml}      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────┐
│ elevate_voice_activity  │ Apply BabyBrains voice
│ OUTPUT: {elevated, grade}│
└─────────┬───────────────┘
          │
          │ grade != "A"? ──YES──► REVISION QUEUE
          │
          ▼ NO
┌─────────────────────┐
│ validate_activity   │ Structure/cross-ref check
│ OUTPUT: {validation}│
└─────────┬───────────┘
          │
          │ passed? ──NO──► FLAG + LOG ISSUES
          │
          ▼ YES
┌──────────────────────┐
│ QC HOOK              │ check_activity_quality.py
│ OUTPUT: {pass/fail}  │
└─────────┬────────────┘
          │
          │ pass? ──NO──► QC FAILED (log to scratch)
          │
          ▼ YES
┌──────────────────────┐
│ HUMAN REVIEW         │ Present activity for approval
│ Approve/Reject/Skip  │
└─────────┬────────────┘
          │
          ▼
WRITE FILE + UPDATE PROGRESS
```

---

## Step 3: Key Input Files

### 3.1 Raw Activities Source
**File:** `/home/squiz/code/knowledge/sources/structured/activities_v1/activities_fixed_01.yaml`

```yaml
activities:
  - id: tummy-time                    # kebab-case unique ID
    title: Tummy Time
    source:
      book: The Joyful Child
      part: Part 1
    age_range:
      min_months: 0
      max_months: 6
      label: "0-6m"
    domain: motor_gross               # One of 10 domains
    purpose: |
      To exercise and strengthen...
    montessori_principles:
      - "Freedom of Movement..."
    developmental_windows:
      - gross_motor_skills_0_6
    materials:
      montessori_standard: N/A
      household_diy: "A soft but firm surface..."
    environment_setup: "Place the infant..."
    presentation_steps:
      - "From the very first day..."
    observation:
      signs_of_readiness: "From the first day..."
      what_to_watch: "The child's efforts..."
      signs_of_mastery: "The child can comfortably..."
    variations: {}
    when_to_introduce: "From the first day."
    when_to_remove: "Once the child can roll over..."
    common_mistakes: "Only placing an infant on their back..."
    page_reference: "p. 13"
```

**Total Activities:** 238
**Domains:** cognitive, motor_fine, language, sensory, motor_gross, music_rhythm, practical_life, art_creative, social_emotional, nature_culture

### 3.2 Conversion Map
**File:** `/home/squiz/code/knowledge/.claude/workflow/ACTIVITY_CONVERSION_MAP.yaml`

```yaml
# Activities to SKIP (duplicates, merged elsewhere)
skip:
  - offering-limited-choices
  - the-weaning-table
  - prenatal-music-exposure
  # ... 7 total

# Activities to GROUP (combine multiple into one canonical)
groups:
  visual-mobiles-progression:
    sources:
      - munari-mobile
      - octahedron-mobile
      - gobbi-mobile
    domain: sensory
    age_range: "0-4m"
  # ... 22 groups total

# Domain corrections (override raw domain)
domain_corrections:
  clearing-the-table-and-washing-dishes: practical_life
  box-with-incline-and-drawer-object-permanence: cognitive
  # ... 23 corrections
```

### 3.3 Progress Tracker
**File:** `/home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md`

```markdown
# Activity Conversion Progress

## Summary
- Total: 238
- Done: 13
- Pending: 225
- Failed: 0

## Conversion Queue
| # | Raw ID | Domain | Age Range | Status | Date | Notes |
|---|--------|--------|-----------|--------|------|-------|
| 1 | carrying-stools | practical_life | 1.5-3y | done | 2026-01-02 | Converted |
| 2 | sweeping | practical_life | 1.5-3y | pending | | |
```

**Update Pattern:**
1. Find row by Raw ID
2. Set Status: done | pending | in_progress | failed | skipped
3. Add date (YYYY-MM-DD) for done
4. Add brief note
5. Update Summary counts

---

## Step 4: ATLAS V2 Components to Use

### 4.1 SkillLoader - Load Activity Skills
**File:** `/home/squiz/ATLAS/atlas/orchestrator/skill_executor.py`

```python
from atlas.orchestrator.skill_executor import SkillLoader, SkillExecutor

loader = SkillLoader(
    skills_path=Path("/home/squiz/code/babybrains-os/skills")
)

# List activity skills
skills = loader.list_skills()  # ['activity/ingest_activity', ...]

# Load full skill
content = loader.load_skill("activity/ingest_activity")

# Load specific section (saves tokens)
section = loader.load_skill_section("activity/transform_activity", "Output")
```

### 4.2 SkillExecutor - Execute Skills
```python
# Default is CLI mode (free via Max subscription)
# use_api=True required for automation pipelines
executor = SkillExecutor(use_api=True)

result = await executor.execute(
    skill_name="activity/ingest_activity",
    input_data={"raw_id": "tummy-time"},
    validate=True
)

if result.success:
    output = result.output  # Parsed JSON
else:
    error = result.error
    validation_errors = result.validation_errors
```

### 4.3 SubAgentExecutor - Parallel/Adversarial Agents
**File:** `/home/squiz/ATLAS/atlas/orchestrator/subagent_executor.py`

```python
from atlas.orchestrator.subagent_executor import SubAgentExecutor

sub = SubAgentExecutor(timeout=120)

# Single sub-agent
result = await sub.spawn(
    task="Research safety standards for water play activities",
    context={"domain": "practical_life", "involves_water": True},
    sandbox=True  # Runs in sandbox if srt available
)

# Adversarial verification
verification = await sub.verify_adversarially(
    output={"yaml": elevated_yaml, "grade": "A"},
    skill_name="elevate_voice_activity",
    persona="junior analyst at McKinsey"
)

if not verification.passed:
    print(f"Issues: {verification.issues}")
```

### 4.4 HookRunner - Run QC Hook
**File:** `/home/squiz/ATLAS/atlas/orchestrator/hooks.py`

```python
from atlas.orchestrator.hooks import HookRunner, HookTiming

hooks = HookRunner()

# Run QC hook
result = await hooks.run(
    repo="knowledge",
    hook_name="activity_qc",
    input_data={"content": elevated_yaml, "format": "yaml"},
    timeout=30
)

if result.passed:
    print("QC passed!")
else:
    print(f"Blocking: {result.blocking}")
    for issue in result.blocking_issues:
        print(f"  [{issue.code}] {issue.message}")
```

### 4.5 SessionManager - Track State
**File:** `/home/squiz/ATLAS/atlas/orchestrator/session_manager.py`

```python
from atlas.orchestrator.session_manager import SessionManager

session = SessionManager()
session_id = await session.start_session(repo="knowledge")

# Track progress
session.record_skill("ingest_activity")
session.add_to_scratch("current_activity", "tummy-time")
session.add_to_scratch("ingest_output", ingest_result.output)

# Save for recovery
await session.save_state()

# End session
await session.end_session()
```

---

## Step 5: Skill I/O Contracts

### 5.1 ingest_activity
**Input:**
```json
{"raw_id": "tummy-time"}
```

**Output:**
```json
{
  "activity_id": "tummy-time",
  "should_skip": false,
  "skip_reason": null,
  "is_grouped": false,
  "group_id": null,
  "is_group_primary": true,
  "domain": "motor_gross",
  "domain_corrected": false,
  "age_range": {"min_months": 0, "max_months": 6, "label": "0-6m"},
  "raw_activity": {/* full raw YAML object */},
  "source_book": "The Joyful Child",
  "source_part": "Part 1",
  "page_reference": "p. 13"
}
```

**Flow Control:**
- If `should_skip == true`: SKIP, update progress, next activity
- If `is_grouped && !is_group_primary`: SKIP (only primary gets converted)

### 5.2 research_activity
**Input:** Output from ingest_activity

**Output:**
```json
{
  "source_material": {
    "found": true,
    "file_path": "/home/squiz/code/knowledge/sources/raw_extractions/activities/...",
    "relevant_sections": "..."
  },
  "principles": [
    {
      "slug": "freedom_within_limits",
      "rationale": "Why this applies...",
      "how_manifested": "How it appears..."
    }
  ],
  "safety_research": {
    "concerns": [
      {"concern": "...", "severity": "high", "au_standard": "Red Nose...", "mitigation": "..."}
    ]
  },
  "related_guidance": [{"guidance_id": "GUIDANCE_XXX", "relationship": "..."}],
  "related_materials": [{"material_slug": "floor-mat", "exists": true}]
}
```

### 5.3 transform_activity
**Input:** ingest_result + research_result

**Output:**
```json
{
  "canonical_yaml": "type: Activity\ncanonical_id: ACTIVITY_MOTOR_GROSS_TUMMY_TIME_0_6M\n...",
  "file_path": "data/canonical/activities/motor_gross/ACTIVITY_MOTOR_GROSS_TUMMY_TIME_0_6M.yaml",
  "canonical_id": "ACTIVITY_MOTOR_GROSS_TUMMY_TIME_0_6M",
  "sections_completed": 34,
  "sections_missing": []
}
```

### 5.4 elevate_voice_activity
**Input:** canonical_yaml from transform

**Output:**
```json
{
  "elevated_yaml": "...",
  "voice_checks": {
    "em_dashes": 0,
    "formal_transitions": [],
    "superlatives": [],
    "australian_fixes": ["mom→mum", "diaper→nappy"]
  },
  "grade": "A",
  "issues": []
}
```

**Flow Control:**
- If `grade != "A"`: Send to REVISION QUEUE, don't continue

### 5.5 validate_activity
**Input:** elevated_yaml, file_path, canonical_id

**Output:**
```json
{
  "validation_result": {
    "passed": true,
    "blocking_issues": [],
    "warnings": []
  },
  "structure_check": {"all_sections_present": true, "section_count": 34},
  "cross_ref_check": {"guidance_refs_valid": true, "material_refs_valid": true, "principle_refs_valid": true},
  "yaml_check": {"valid_syntax": true}
}
```

### 5.6 QC Hook (check_activity_quality.py)
**Input:** YAML via stdin
**Output:** JSON to stdout

```json
{
  "pass": true,
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

**Exit Codes:** 0 = pass, 1 = fail

---

## Step 6: Create the Pipeline Orchestrator

**File:** `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py`

### Required Structure

```python
"""
Activity Conversion Pipeline Orchestrator

Converts raw Montessori activities to canonical Activity Atoms using:
- 5 chained skills (ingest → research → transform → elevate → validate)
- QC hook gate (check_activity_quality.py)
- Human review interface
- Progress tracking
"""

import asyncio
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from atlas.orchestrator.skill_executor import SkillLoader, SkillExecutor, SkillResult
from atlas.orchestrator.subagent_executor import SubAgentExecutor
from atlas.orchestrator.hooks import HookRunner
from atlas.orchestrator.session_manager import SessionManager


class ActivityStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"
    FAILED = "failed"
    REVISION_NEEDED = "revision_needed"


@dataclass
class ConversionResult:
    activity_id: str
    status: ActivityStatus
    canonical_id: Optional[str] = None
    file_path: Optional[str] = None
    skip_reason: Optional[str] = None
    error: Optional[str] = None
    qc_issues: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class ActivityConversionPipeline:
    """Orchestrates the conversion of raw activities to canonical format."""

    RAW_ACTIVITIES_PATH = Path("/home/squiz/code/knowledge/sources/structured/activities_v1/activities_fixed_01.yaml")
    CONVERSION_MAP_PATH = Path("/home/squiz/code/knowledge/.claude/workflow/ACTIVITY_CONVERSION_MAP.yaml")
    PROGRESS_PATH = Path("/home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md")
    CANONICAL_OUTPUT_DIR = Path("/home/squiz/code/knowledge/data/canonical/activities")

    def __init__(self):
        self.skill_loader = SkillLoader(
            skills_path=Path("/home/squiz/code/babybrains-os/skills")
        )
        self.skill_executor = SkillExecutor(use_api=True)
        self.sub_executor = SubAgentExecutor(timeout=120)
        self.hook_runner = HookRunner()
        self.session = SessionManager()

        # Load source data
        self._load_source_data()

    def _load_source_data(self):
        """Load raw activities and conversion map."""
        with open(self.RAW_ACTIVITIES_PATH) as f:
            data = yaml.safe_load(f)
            self.raw_activities = {a['id']: a for a in data['activities']}

        with open(self.CONVERSION_MAP_PATH) as f:
            self.conversion_map = yaml.safe_load(f)

    def get_pending_activities(self) -> list[str]:
        """Get list of activity IDs that need conversion."""
        # Parse CONVERSION_PROGRESS.md
        # Return IDs with status 'pending'
        pass

    async def convert_activity(self, raw_id: str) -> ConversionResult:
        """Run full conversion pipeline for a single activity."""

        # 1. INGEST
        ingest = await self.skill_executor.execute(
            "activity/ingest_activity",
            input_data={"raw_id": raw_id}
        )
        if not ingest.success:
            return ConversionResult(raw_id, ActivityStatus.FAILED, error=ingest.error)

        if ingest.output.get("should_skip"):
            return ConversionResult(
                raw_id, ActivityStatus.SKIPPED,
                skip_reason=ingest.output.get("skip_reason")
            )

        # 2. RESEARCH
        research = await self.skill_executor.execute(
            "activity/research_activity",
            input_data=ingest.output
        )
        if not research.success:
            return ConversionResult(raw_id, ActivityStatus.FAILED, error=research.error)

        # 3. TRANSFORM
        transform = await self.skill_executor.execute(
            "activity/transform_activity",
            input_data={
                "ingest_result": ingest.output,
                "research_result": research.output
            }
        )
        if not transform.success:
            return ConversionResult(raw_id, ActivityStatus.FAILED, error=transform.error)

        # 4. ELEVATE VOICE
        elevate = await self.skill_executor.execute(
            "activity/elevate_voice_activity",
            input_data={"canonical_yaml": transform.output["canonical_yaml"]}
        )
        if not elevate.success:
            return ConversionResult(raw_id, ActivityStatus.FAILED, error=elevate.error)

        if elevate.output.get("grade") != "A":
            return ConversionResult(
                raw_id, ActivityStatus.REVISION_NEEDED,
                error=f"Voice grade {elevate.output.get('grade')}: {elevate.output.get('issues')}"
            )

        # 5. VALIDATE
        validate = await self.skill_executor.execute(
            "activity/validate_activity",
            input_data={
                "elevated_yaml": elevate.output["elevated_yaml"],
                "file_path": transform.output["file_path"],
                "canonical_id": transform.output["canonical_id"]
            }
        )
        if not validate.success or not validate.output["validation_result"]["passed"]:
            return ConversionResult(
                raw_id, ActivityStatus.FAILED,
                error=f"Validation failed: {validate.output.get('validation_result', {}).get('blocking_issues')}"
            )

        # 6. QC HOOK
        qc = await self.hook_runner.run(
            repo="knowledge",
            hook_name="activity_qc",
            input_data={"content": elevate.output["elevated_yaml"], "format": "yaml"}
        )
        if not qc.passed:
            return ConversionResult(
                raw_id, ActivityStatus.FAILED,
                qc_issues=[f"[{i.code}] {i.msg}" for i in qc.blocking_issues]
            )

        # 7. SUCCESS - Ready for human review
        return ConversionResult(
            activity_id=raw_id,
            status=ActivityStatus.DONE,
            canonical_id=transform.output["canonical_id"],
            file_path=transform.output["file_path"],
            warnings=[f"[{w.code}] {w.msg}" for w in qc.advisory_issues] if hasattr(qc, 'advisory_issues') else []
        )

    async def present_for_review(self, result: ConversionResult, yaml_content: str) -> str:
        """Present converted activity for human review."""
        # Display activity summary
        # Show QC results
        # Prompt: Approve / Reject / Skip
        # Return decision
        pass

    def update_progress(self, raw_id: str, status: ActivityStatus, notes: str = ""):
        """Update CONVERSION_PROGRESS.md with new status."""
        pass

    def write_canonical_file(self, file_path: str, yaml_content: str):
        """Write approved activity to canonical location."""
        pass

    async def run_batch(self, limit: int = 10):
        """Process a batch of pending activities."""
        pending = self.get_pending_activities()[:limit]

        for raw_id in pending:
            self.update_progress(raw_id, ActivityStatus.IN_PROGRESS)

            result = await self.convert_activity(raw_id)

            if result.status == ActivityStatus.DONE:
                # Present for human review
                # If approved: write file, update progress
                pass
            else:
                self.update_progress(raw_id, result.status, result.error or result.skip_reason)


async def main():
    pipeline = ActivityConversionPipeline()
    await pipeline.run_batch(limit=5)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 7: Human Review Interface

The pipeline should present each converted activity for human approval:

```
═══════════════════════════════════════════════════════════════
ACTIVITY READY FOR REVIEW
═══════════════════════════════════════════════════════════════

Raw ID:       tummy-time
Canonical ID: ACTIVITY_MOTOR_GROSS_TUMMY_TIME_0_6M
Domain:       motor_gross
Age Range:    0-6 months

QC Status:    PASSED
Warnings:     None

─────────────────────────────────────────────────────────────────
PREVIEW (first 50 lines):
─────────────────────────────────────────────────────────────────
type: Activity
canonical_id: ACTIVITY_MOTOR_GROSS_TUMMY_TIME_0_6M
title: "Tummy Time"
...

─────────────────────────────────────────────────────────────────
[A]pprove  [R]eject  [S]kip  [V]iew Full  [Q]uit
>
```

---

## Step 8: Success Criteria

- [ ] `activity_conversion.py` exists at `/home/squiz/ATLAS/atlas/pipelines/`
- [ ] Can load raw activities from YAML source
- [ ] Can parse conversion map (skip, groups, domain_corrections)
- [ ] Can read/update CONVERSION_PROGRESS.md
- [ ] Executes all 5 skills in sequence with proper data passing
- [ ] Handles skip/group logic correctly
- [ ] Runs QC hook and respects pass/fail
- [ ] Presents activities for human review
- [ ] Writes approved activities to canonical location
- [ ] Updates progress tracker after each activity
- [ ] Graceful error handling with logging

---

## Step 9: Test the Pipeline

### Test with Single Activity
```bash
cd /home/squiz/ATLAS
python -c "
import asyncio
from atlas.pipelines.activity_conversion import ActivityConversionPipeline

async def test():
    pipeline = ActivityConversionPipeline()
    result = await pipeline.convert_activity('tummy-time')
    print(f'Status: {result.status}')
    print(f'Canonical ID: {result.canonical_id}')
    if result.error:
        print(f'Error: {result.error}')

asyncio.run(test())
"
```

### Test Batch Processing
```bash
cd /home/squiz/ATLAS
python -m atlas.pipelines.activity_conversion
```

---

## Step 10: Verification After Completion

Run these verification prompts (from `/home/squiz/ATLAS/docs/VERIFICATION_PROMPTS.md`):

### Code Review Self-Check
```
Review activity_conversion.py for:
- [ ] Unhandled exceptions
- [ ] Missing input validation
- [ ] Resource leaks (file handles, sessions)
- [ ] Race conditions in async code
- [ ] Missing logging
```

### Inversion Test
```
What would make this pipeline WRONG?
- What valid activity would it incorrectly FAIL?
- What invalid activity would it incorrectly PASS?
- What edge cases break it? (empty YAML, huge files, malformed data)
```

### Junior Analyst Challenge
```
Spawn fresh agent to audit the code against this handover spec.
```

---

## DO NOT

- Do NOT modify raw activities source file
- Do NOT modify conversion map without explicit instruction
- Do NOT skip the human review step
- Do NOT write files without approval
- Do NOT add dependencies beyond what ATLAS already has

---

## After Completion

Report back with:
1. File created and location
2. Test results (single activity + batch)
3. Sample human review interaction
4. Any edge cases discovered
5. Suggestions for Phase 4 (Human Review Interface improvements)

---

## File Locations Summary

| What | Where |
|------|-------|
| **CREATE THIS** | `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py` |
| Raw activities | `/home/squiz/code/knowledge/sources/structured/activities_v1/activities_fixed_01.yaml` |
| Conversion map | `/home/squiz/code/knowledge/.claude/workflow/ACTIVITY_CONVERSION_MAP.yaml` |
| Progress tracker | `/home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md` |
| Canonical output | `/home/squiz/code/knowledge/data/canonical/activities/{domain}/` |
| Activity skills | `/home/squiz/code/babybrains-os/skills/activity/*.md` |
| QC Hook | `/home/squiz/code/knowledge/scripts/check_activity_quality.py` |
| V2 Components | `/home/squiz/ATLAS/atlas/orchestrator/*.py` |
| V2 Guide | `/home/squiz/ATLAS/docs/V2_ORCHESTRATOR_GUIDE.md` |

---

## Valid Principle Slugs (for validation)

```python
VALID_PRINCIPLES = {
    "absorbent_mind", "sensitive_periods", "prepared_environment",
    "independence", "practical_life", "grace_and_courtesy",
    "maximum_effort", "order", "movement", "concentration",
    "repetition", "sensorial", "work_of_the_child",
    "freedom_within_limits", "cosmic_view", "observation",
    "normalization", "spiritual_embryo"
}
```

---

## Domains (10 total)

```python
DOMAINS = {
    "cognitive", "motor_fine", "language", "sensory",
    "motor_gross", "music_rhythm", "practical_life",
    "art_creative", "social_emotional", "nature_culture"
}
```
