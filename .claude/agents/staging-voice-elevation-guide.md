# Staging Voice Elevation Guide

**Purpose:** Process pioneer files through voice elevation pipeline to Grade A quality.
**Location:** `/home/squiz/code/knowledge/data/staging/needs_voice_elevation/`
**Target:** Move to `/home/squiz/code/knowledge/data/canonical/activities/` when Grade A achieved.

---

## Command

```bash
python3 -m atlas.pipelines.activity_conversion \
  --elevate-existing /home/squiz/code/knowledge/data/staging/needs_voice_elevation/FILENAME.yaml \
  --auto-approve
```

This runs the file through:
- **Stage 4: ELEVATE** - Apply Babybrains-writer voice via skill
- **Stage 5: VALIDATE** - Schema validation
- **Stage 6: QC_HOOK** - Quality control checks
- **Stage 7: QUALITY_AUDIT** - Grade A verification

If Grade A is achieved with `--auto-approve`, the file is automatically:
1. Saved to canonical directory
2. Removed from staging

---

## Current Status (January 24, 2026)

### Completed
- `ACTIVITY_MOVEMENT_SAFE_CLIMBING_PRACTICE_12_36M` - Grade A, moved to canonical

### Ready to Process (Has Goals)
- `ACTIVITY_MOVEMENT_WALKING_MAXIMUM_EFFORT_JOBS_12_24M`

### Blocked (Missing Goals Section)

These files fail at VALIDATE because they lack the required `goals` section:

| # | File | Domain |
|---|------|--------|
| 1 | `ACTIVITY_FEEDING_ALLERGEN_INTRODUCTION_ROTATION_6_12M` | feeding |
| 2 | `ACTIVITY_FEEDING_FAMILY_MEAL_RITUAL_12_24M` | feeding |
| 3 | `ACTIVITY_FEEDING_RESPONSIVE_BOTTLE_BREAST_0_6M` | feeding |
| 4 | `ACTIVITY_FEEDING_WEANING_TABLE_FIRST_WEEKS_6_12M` | feeding |
| 5 | `ACTIVITY_MOVEMENT_FLOOR_FREEDOM_PLAYBLOCK_0_12M` | movement |
| 6 | `ACTIVITY_MOVEMENT_FREE_MOVEMENT_CLOTHING_0_12M` | movement |
| 7 | `ACTIVITY_MOVEMENT_HOME_MOVEMENT_AREA_0_36M` | movement |
| 8 | `ACTIVITY_MOVEMENT_OBSTACLE_PATH_CRAWLING_CRUISING_9_18M` | movement |
| 9 | `ACTIVITY_PE_SIMPLE_SWEEPING_INTRODUCTION_18_24M` | prepared_environment |
| 10 | `ACTIVITY_PE_SPILL_CLEANUP_PRACTICE_18_24M` | prepared_environment |
| 11 | `ACTIVITY_PE_VEGETABLE_WASHING_MEAL_PREP_12_24M` | prepared_environment |

---

## Before Processing Blocked Files

Each file needs a `goals` section added. Format:

```yaml
goals:
  - "First learning outcome in present tense"
  - "Second learning outcome"
  - "Third learning outcome"
  - "Fourth learning outcome (optional)"
  - "Fifth learning outcome (optional)"
```

Goals should:
- Describe developmental benefits
- Use present tense ("Develops", "Builds", "Supports")
- Be specific to the activity
- Avoid superlatives

---

## Processing Workflow

### Step 1: Check for Goals

```bash
grep -n "^goals:" /path/to/file.yaml
```

If no output, file needs goals added before processing.

### Step 2: Run Pipeline

```bash
python3 -m atlas.pipelines.activity_conversion \
  --elevate-existing /home/squiz/code/knowledge/data/staging/needs_voice_elevation/FILENAME.yaml \
  --auto-approve
```

### Step 3: Verify Success

```bash
# Check file is in canonical
ls /home/squiz/code/knowledge/data/canonical/activities/DOMAIN/FILENAME.yaml

# Check file removed from staging
ls /home/squiz/code/knowledge/data/staging/needs_voice_elevation/FILENAME.yaml
# Should show "No such file"
```

---

## Failure Handling

### If "Missing goals" Error
Add goals section to file, then re-run.

### If JSON Parse Error
Pipeline will auto-retry (up to 3 times). If persistent, check CLI mode.

### If QC Failed
Check specific QC issue. Common fixes:
- Remove superlatives (best, perfect, amazing)
- Remove pressure language (you must, you need to)
- Remove em-dashes

---

## Verification After All Complete

```bash
# Staging should only have README.md
ls /home/squiz/code/knowledge/data/staging/needs_voice_elevation/

# All canonical files should pass QC
for f in /home/squiz/code/knowledge/data/canonical/activities/**/*.yaml; do
  python3 /home/squiz/code/knowledge/scripts/check_activity_quality.py "$f" > /dev/null 2>&1 || echo "FAIL: $f"
done
```
