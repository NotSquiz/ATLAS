# Activity Pipeline Reconciliation Plan (DEPRECATED)

**Created:** January 23, 2026
**Status:** UNSAFE - DO NOT EXECUTE
**Superseded By:** reconciliation-plan-v2.md

---

## WARNING: This Plan is Flawed

Verification prompts (Inversion Test, Adversarial Check, Wait Pattern) found:
- The 17 "likely raw_ids" were fabricated from canonical filenames
- NONE of these raw_ids exist in the progress file
- Only 4 files have actual matching raw_ids (different names)
- 13 files are orphans created outside the pipeline

**Use reconciliation-plan-v2.md instead.**

---

# ORIGINAL PLAN BELOW (FOR REFERENCE ONLY)

**Purpose:** Sync 17 untracked canonical files with progress tracking

---

## The Problem

- **33 canonical YAML files** exist in `data/canonical/activities/`
- **16 entries** marked "done" in progress file
- **17 files are untracked** - they exist but aren't marked "done"

These 17 files were created before progress tracking was implemented or via paths that didn't update tracking.

---

## Files Already Tracked (16)

These raw_ids are already marked "done" - NO ACTION NEEDED:

1. carrying-stools-and-chairs
2. sweeping
3. washing-fruits-and-vegetables
4. caring-for-clothes-folding-hanging
5. sweeping-the-floor
6. mopping-a-spill
7. collaboration-in-practical-life
8. prenatal-language-foundation
9. narrating-daily-care
10. infant-sign-language
11. the-naming-game-two-period-lesson
12. reciting-and-acting-out-nursery-rhymes
13. matching-objects-to-pictures
14. stacking-blocks-or-cubes
15. art-appreciation
16. baking

---

## Files Needing Reconciliation (17)

For each file below, find the matching raw_id in the progress file and update status to "done":

| # | Canonical File | Likely raw_id | Domain |
|---|----------------|---------------|--------|
| 1 | ACTIVITY_FEEDING_ALLERGEN_INTRODUCTION_ROTATION_6_12M | allergen-introduction-rotation | feeding |
| 2 | ACTIVITY_FEEDING_FAMILY_MEAL_RITUAL_12_24M | family-meal-ritual | feeding |
| 3 | ACTIVITY_FEEDING_RESPONSIVE_BOTTLE_BREAST_0_6M | responsive-bottle-breast | feeding |
| 4 | ACTIVITY_FEEDING_WEANING_TABLE_FIRST_WEEKS_6_12M | weaning-table-first-weeks | feeding |
| 5 | ACTIVITY_MOVEMENT_BALANCE_BOARD_WALKING_24_36M | balance-board-walking | movement |
| 6 | ACTIVITY_MOVEMENT_FIRST_TRICYCLE_OR_BALANCE_BIKE_24_36M | first-tricycle-or-balance-bike | movement |
| 7 | ACTIVITY_MOVEMENT_FLOOR_FREEDOM_PLAYBLOCK_0_12M | floor-freedom-playblock | movement |
| 8 | ACTIVITY_MOVEMENT_FREE_MOVEMENT_CLOTHING_0_12M | free-movement-clothing | movement |
| 9 | ACTIVITY_MOVEMENT_HOME_MOVEMENT_AREA_0_36M | home-movement-area | movement |
| 10 | ACTIVITY_MOVEMENT_OBSTACLE_PATH_CRAWLING_CRUISING_9_18M | obstacle-path-crawling-cruising | movement |
| 11 | ACTIVITY_MOVEMENT_PRACTICAL_LIFE_POURING_18_36M | practical-life-pouring | movement |
| 12 | ACTIVITY_MOVEMENT_RESPECT_CHILD_TIMETABLE_0_12M | respect-child-timetable | movement |
| 13 | ACTIVITY_MOVEMENT_SAFE_CLIMBING_PRACTICE_12_36M | safe-climbing-practice | movement |
| 14 | ACTIVITY_MOVEMENT_TUMMY_TIME_MICRO_SESSIONS_0_6M | tummy-time-micro-sessions | movement |
| 15 | ACTIVITY_MOVEMENT_WALKING_MAXIMUM_EFFORT_JOBS_12_24M | walking-maximum-effort-jobs | movement |
| 16 | ACTIVITY_PE_SPILL_CLEANUP_PRACTICE_18_24M | spill-cleanup-practice | practical_life |
| 17 | ACTIVITY_PE_TABLE_WIPING_PRACTICE_15_24M | table-wiping-practice | practical_life |

---

## Manual Reconciliation Steps

For EACH of the 17 files above:

### Step 1: Find the raw_id in progress file
```bash
grep "raw_id_here" /home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md
```

### Step 2: Verify the file exists
```bash
ls -la /home/squiz/code/knowledge/data/canonical/activities/DOMAIN/CANONICAL_ID.yaml
```

### Step 3: Update the progress file entry
Change: `| pending |` → `| done | 2026-01-23 | Pre-existing canonical file |`

### Step 4: Verify the update
```bash
grep "raw_id_here" /home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md
```

---

## Verification After Complete

```bash
# Should both equal 33
echo "Done entries: $(grep -c '| done |' /home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md)"
echo "Canonical files: $(find /home/squiz/code/knowledge/data/canonical/activities -name '*.yaml' | wc -l)"
```

---

## Important Notes

1. **DO NOT delete any files** - only update progress tracking
2. **DO NOT run pipeline** during reconciliation - avoid race conditions
3. **Verify each change** before moving to next file
4. **If raw_id not found** - the file may have been created via different naming; search by domain/keywords

---

## Progress Tracking

- [ ] File 1: allergen-introduction-rotation
- [ ] File 2: family-meal-ritual
- [ ] File 3: responsive-bottle-breast
- [ ] File 4: weaning-table-first-weeks
- [ ] File 5: balance-board-walking
- [ ] File 6: first-tricycle-or-balance-bike
- [ ] File 7: floor-freedom-playblock
- [ ] File 8: free-movement-clothing
- [ ] File 9: home-movement-area
- [ ] File 10: obstacle-path-crawling-cruising
- [ ] File 11: practical-life-pouring
- [ ] File 12: respect-child-timetable
- [ ] File 13: safe-climbing-practice
- [ ] File 14: tummy-time-micro-sessions
- [ ] File 15: walking-maximum-effort-jobs
- [ ] File 16: spill-cleanup-practice
- [ ] File 17: table-wiping-practice
