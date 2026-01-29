# Activity Pipeline Reconciliation Plan v2

**Created:** January 23, 2026
**Status:** VERIFIED - Safe to execute
**Purpose:** Reconcile canonical files with progress tracking

---

## Verification Summary

Three verification prompts applied (Inversion Test, Adversarial Check, Wait Pattern).

**CRITICAL FINDING:** The original plan (v1) was UNSAFE. The assumed raw_ids were fabricated from canonical filenames and don't exist in the progress file.

---

## Corrected Analysis

### Category 1: Files to Reconcile (4 files)

These canonical files have MATCHING pending entries in the progress file (just different naming):

| Canonical File | Actual raw_id in Progress | Line # | Status |
|----------------|---------------------------|--------|--------|
| `ACTIVITY_MOVEMENT_BALANCE_BOARD_WALKING_24_36M` | `walking-on-a-balance-board` | 170 | pending |
| `ACTIVITY_MOVEMENT_FIRST_TRICYCLE_OR_BALANCE_BIKE_24_36M` | `riding-a-first-tricycle-or-bike` | 168 | pending |
| `ACTIVITY_MOVEMENT_PRACTICAL_LIFE_POURING_18_36M` | `pouring-water-or-other-drywet-materials` | 156 | pending |
| `ACTIVITY_MOVEMENT_RESPECT_CHILD_TIMETABLE_0_12M` | `respecting-the-childs-timetable` | 154 | pending |

**Action:** Update these 4 entries from `pending` to `done` with note "Pre-existing canonical file (2025-11)"

---

### Category 2: Revision Needed (2 files)

These canonical files exist but are deliberately marked `revision_needed` because they fail QC:

| Canonical File | raw_id | Status | Reason |
|----------------|--------|--------|--------|
| `ACTIVITY_MOVEMENT_TUMMY_TIME_MICRO_SESSIONS_0_6M` | `tummy-time` | revision_needed | Fails QC (33/34 sections) |
| `ACTIVITY_PE_TABLE_WIPING_PRACTICE_15_24M` | `wiping-the-table` | revision_needed | Fails QC (31/34 sections) |

**Action:** DO NOT CHANGE. These need QC remediation, not status update.

---

### Category 3: Pioneer Files Moved to Staging (13 files)

**STATUS: COMPLETED 2026-01-23**

These files were created through manual workflows before the voice elevation pipeline existed. They are structurally complete but lack the Babybrains-writer voice.

**Action Taken:** Moved to `/home/squiz/code/knowledge/data/staging/needs_voice_elevation/`

| Domain | File | Status |
|--------|------|--------|
| feeding | `ACTIVITY_FEEDING_ALLERGEN_INTRODUCTION_ROTATION_6_12M` | Needs voice elevation |
| feeding | `ACTIVITY_FEEDING_FAMILY_MEAL_RITUAL_12_24M` | Needs voice elevation |
| feeding | `ACTIVITY_FEEDING_RESPONSIVE_BOTTLE_BREAST_0_6M` | Needs voice elevation |
| feeding | `ACTIVITY_FEEDING_WEANING_TABLE_FIRST_WEEKS_6_12M` | Needs voice elevation |
| movement | `ACTIVITY_MOVEMENT_FLOOR_FREEDOM_PLAYBLOCK_0_12M` | Needs voice elevation |
| movement | `ACTIVITY_MOVEMENT_FREE_MOVEMENT_CLOTHING_0_12M` | Needs voice elevation |
| movement | `ACTIVITY_MOVEMENT_HOME_MOVEMENT_AREA_0_36M` | Needs voice elevation |
| movement | `ACTIVITY_MOVEMENT_OBSTACLE_PATH_CRAWLING_CRUISING_9_18M` | Needs voice elevation |
| movement | `ACTIVITY_MOVEMENT_SAFE_CLIMBING_PRACTICE_12_36M` | Needs voice elevation |
| movement | `ACTIVITY_MOVEMENT_WALKING_MAXIMUM_EFFORT_JOBS_12_24M` | Needs voice elevation |
| prepared_env | `ACTIVITY_PE_SPILL_CLEANUP_PRACTICE_18_24M` | Needs voice elevation |
| prepared_env | `ACTIVITY_PE_SIMPLE_SWEEPING_INTRODUCTION_18_24M` | Needs voice elevation |
| prepared_env | `ACTIVITY_PE_VEGETABLE_WASHING_MEAL_PREP_12_24M` | Needs voice elevation |

**Next Step:** Process through voice elevation pipeline before returning to canonical.

---

## Safe Execution Steps

### Step 0: Backup

```bash
cp /home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md \
   /home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md.backup-20260123
```

### Step 1: Reconcile Category 1 (4 files)

For each entry:

**1a. walking-on-a-balance-board (line 170)**
```
Find: | 170 | walking-on-a-balance-board | motor_gross | 2-3 years | pending |  |  |
Replace: | 170 | walking-on-a-balance-board | motor_gross | 2-3 years | done | 2026-01-23 | Pre-existing canonical file (2025-11) |
```

**1b. riding-a-first-tricycle-or-bike (line 168)**
```
Find: | 168 | riding-a-first-tricycle-or-bike | motor_gross | 2.5-3 years | pending |  |  |
Replace: | 168 | riding-a-first-tricycle-or-bike | motor_gross | 2.5-3 years | done | 2026-01-23 | Pre-existing canonical file (2025-11) |
```

**1c. pouring-water-or-other-drywet-materials (line 156)**
```
Find: | 156 | pouring-water-or-other-drywet-materials | motor_gross | 1-3 years | pending |  |  |
Replace: | 156 | pouring-water-or-other-drywet-materials | motor_gross | 1-3 years | done | 2026-01-23 | Pre-existing canonical file (2025-11) |
```

**1d. respecting-the-childs-timetable (line 154)**
```
Find: | 154 | respecting-the-childs-timetable | motor_gross | 0-12m | pending |  |  |
Replace: | 154 | respecting-the-childs-timetable | motor_gross | 0-12m | done | 2026-01-23 | Pre-existing canonical file (2025-11) |
```

### Step 2: Update Summary Counts

Change header from:
```
- Done: 16 (5 pass QC, 7 need remediation)
- Pending: 212
```

To:
```
- Done: 20 (5 pass QC, 7 need remediation, 4 pre-existing)
- Pending: 208
```

### Step 3: Create Orphan Inventory

Create `/home/squiz/code/knowledge/.claude/workflow/ORPHAN_CANONICAL_FILES.md`:

```markdown
# Orphan Canonical Files

Files created directly (not through pipeline conversion).

| Canonical ID | Domain | Created | Notes |
|--------------|--------|---------|-------|
| ACTIVITY_FEEDING_ALLERGEN_INTRODUCTION_ROTATION_6_12M | feeding | 2025-11-19 | Direct creation |
| ... (13 files total) |
```

---

## Verification After Complete

```bash
# Should show 20 done entries
grep -c '| done |' /home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md

# Canonical files: 33 (but only 20 from pipeline, 2 revision_needed, 13 orphans)
find /home/squiz/code/knowledge/data/canonical/activities -name '*.yaml' | wc -l
```

---

## Progress Checklist

- [ ] Step 0: Backup created
- [ ] Step 1a: walking-on-a-balance-board → done
- [ ] Step 1b: riding-a-first-tricycle-or-bike → done
- [ ] Step 1c: pouring-water-or-other-drywet-materials → done
- [ ] Step 1d: respecting-the-childs-timetable → done
- [ ] Step 2: Summary counts updated
- [ ] Step 3: Orphan inventory created

---

## What Changed from v1

| Aspect | v1 (UNSAFE) | v2 (VERIFIED) |
|--------|-------------|---------------|
| Files to reconcile | 17 | 4 |
| Raw IDs source | Fabricated from filenames | Actual grep matches |
| Orphan handling | None (assumed all in progress) | Separate inventory |
| Revision_needed | Would overwrite to done | Preserved |
| Verification | None | 3 prompts applied |
