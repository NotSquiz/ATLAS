# Activity Pipeline Workflow

## Overview
Baby Brains activity conversion from raw YAML to Grade A content.

## 7-Stage Pipeline

### Stage 1: INGEST
Load activity YAML from knowledge repository.
```bash
# Source
knowledge/activities/<category>/<activity-name>.yaml
```

### Stage 2: RESEARCH
Gather Montessori/RIE context for the activity.
- Age-appropriate expectations
- Developmental milestones
- Related Montessori principles
- RIE philosophy alignment

### Stage 3: TRANSFORM
Structure content to Baby Brains schema.
- Purpose statement
- Materials list
- Setup instructions
- Engagement flow
- Parent guidance

### Stage 4: ELEVATE
Apply Voice Elevation Rubric (draft_21s skill).

**Key Transformations:**
- Remove marketing language
- Convert prescriptive to suggestive
- Add observation prompts
- Ensure parent empowerment

### Stage 5: QC (Quality Check)
Run automated quality validation.
```bash
python knowledge/scripts/check_activity_quality.py <activity>
```

**Checks:**
- No blocked superlatives
- Valid YAML structure
- Required fields present
- No truncation

### Stage 6: AUDIT
Grade A/B+/B/C/F evaluation against Voice Rubric.

**Grade A Requirements:**
- Natural, conversational voice
- No pressure language
- Parent-empowering
- Montessori/RIE aligned
- Complete structure

### Stage 7: OUTPUT
Write to babybrains-os repository.
```bash
# Destination
babybrains-os/content/activities/<category>/<activity-name>.yaml
```

## Pipeline Commands

```bash
# Convert single activity
python -m atlas.pipelines.activity_conversion --activity tummy-time

# With retry (uses Wait pattern)
python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 3

# List pending activities
python -m atlas.pipelines.activity_conversion --list-pending

# Batch mode (use carefully)
python -m atlas.pipelines.activity_conversion --batch --limit 10
```

## Stage Caching (D79)

Retries skip stages 1-3 (INGEST/RESEARCH/TRANSFORM):
- First attempt: Full 7-stage pipeline
- Retry: Stages 4-7 only (ELEVATE -> AUDIT)
- Result: 60-70% faster retries

## Wait Pattern Integration

On non-A grade:
1. Apply Wait pattern reflection
2. Identify blind spots from audit feedback
3. Re-run ELEVATE with improved context
4. Maximum 3 retries before manual intervention
