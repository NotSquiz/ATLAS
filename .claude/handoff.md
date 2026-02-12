# ATLAS Session Handoff

**Date:** February 12, 2026
**Status:** D110 + D111 applied. Cached path works, CLI has transient retry. Ready for live dry run.
**Rename Pending:** ATLAS -> Astro (not blocking build, do after Sprint 3)

---

## D111: CLI Transient Failure Retry (Feb 12, 2026)

### Bug
First dry run after D110: VALIDATE and adversarial both failed with `CLI returned exit code 1` in <4s. Empty stderr = zero diagnostics. D110 exposed this — before D110 the cached path always crashed at scratch_pad before reaching VALIDATE.

### Fix
1. **Retry in `_execute_cli`**: 1 retry on fast failures (<10s elapsed), 3s backoff. Benefits all stages.
2. **Better diagnostics**: Error includes stderr when present, falls back to stdout snippet.

### Tests
6 new tests in `tests/orchestrator/test_skill_executor.py`. All 160 tests pass.

### Recent Commits
- 4b58a0d: D108 quality audit timeout fix
- PENDING: D109 subprocess timeout audit and process cleanup
- PENDING: D110 cached transform NoneType fix
- PENDING: D111 CLI transient failure retry

### Next Steps
- **#25**: Single dry run (narrating-daily-care) to verify pipeline works end-to-end
- **#26**: Prepare batch prompt for remaining activities

---

## Pipeline Subprocess Audit Complete (Feb 12, 2026)

### What Was Done
4 parallel Opus agents traced ALL 7 pipeline stages' subprocess calls and timeout propagation.

### Fixes Applied (D109)
1. **HookRunner process orphaning** — Replaced `subprocess.run()` with `Popen` + `proc.kill()` pattern (matches SubAgentExecutor)
2. **QC_HOOK hardcoded 30s** — Changed to `STAGE_TIMEOUTS.get("qc_hook", 120)`, increased from 60→120s
3. **Hook config consistency** — Added `"timeout": 120` to activity_qc hook config

### Confirmed Working
- Stages 1-5 timeout propagation: correct (STAGE_TIMEOUTS → SkillExecutor._execute_cli)
- Quality audit timeout (D108): correct (STAGE_TIMEOUTS-based with 1.2x multiplier)
- SubAgentExecutor: proper proc.kill() on timeout

---

## BB Expression Oref Library — COMPLETE + Clothing Pipeline Testing (Feb 12, 2026 - Sessions 42-43)

### Expression Library: COMPLETE (9/9)

All expressions generated via **Gemini "Nano Banana" image editing** from master oref. MJ proved unable to override the master's calm expression at `--ow 175` across 40+ attempts.

**Master Oref Swap:** Original master archived as `master-archived.png`. New master (`neutral.png` → `master.png`) has more defined lips and direct camera gaze — more engaging, truer neutral.

| # | Expression | Status | File | Attempts | Notes |
|---|-----------|--------|------|----------|-------|
| 1 | Calm/Content (Neutral) | **DONE** | `orefs/master.png` | — | New master: defined lips, direct gaze |
| 2 | Curious/Wonder | **DONE** | `orefs/curious.png` | 3 | Distinctive eyebrow arch + 3/4 head turn. Keep only this one (not alt) |
| 3 | Joyful/Delighted | **BANKED** | `orefs/joy.png` | 5+ | Smile great. Eyes neutral — Gemini cannot do Duchenne crescent eyes on baby proportions |
| 4 | Surprised/Discovery | **DONE** | `orefs/surprised.png` | 1 | First attempt pass |
| 5 | Sleepy/Drowsy | **DONE** | `orefs/sleepy.png` | 2 | First was grumpy; softened mouth + brow |
| 6 | Concentrated/Focused | **DONE** | `orefs/focused.png` | 8 | Hardest expression. Single prompt from master solved it (multi-edit chains degrade) |
| 7 | Crying/Upset | **DONE** | `orefs/crying.png` | 1 | First attempt — extreme expressions are Gemini's sweet spot |
| 8 | Mischief/Playful | **DONE** | `orefs/mischievous.png` | 1 | Asymmetric smirk achieved first try — distinct from amused/cheeky |
| 9 | Amused/Cheeky | **DONE** | `orefs/amused-cheeky.png` | — | Bonus — found during focused iterations (overcorrected mouth = clear smile) |

### KEY LESSONS LEARNED

#### Expression Editing (Gemini Nano Banana)
- **Single prompt from master > multi-edit chains** — focused took 8 attempts via chains, solved in 1 via single prompt
- **Extreme expressions are easy** (crying, mischief = 1 attempt), **subtle ones are hard** (focused = 8 attempts)
- **Brow LOWERING (position) works, brow CREASING (texture) triggers sad** on baby faces
- **Gemini can't do fine-grained mouth adjustments** — swings between states (frown ↔ smile), doesn't land between
- **Cannot do subtle eye shape changes** — crescent eyes, half-moon, lower lid raise all fail
- **Incremental edits degrade after 2-3 rounds** — restart from master with refined single prompt
- **Emotion vocabulary matters** — describe what it LOOKS LIKE, not what muscles do
- **Describe the RESULT not the mechanism** ("eyes three-quarters open" not "lower lids pushed up by cheeks")

#### Clothing Editing (Gemini Nano Banana) — NEW
- **3-reference approach works**: master oref + clothing flat-lay (single image) + clay texture reference
- **Combine multi-piece outfits into a single reference image** — 2 separate clothing photos = photorealism drift
- **Clay texture ref is essential** — verbal "sculpted clay texture" alone produces insufficient or wrong texture
- **Too many photo refs = photorealism drift** — 2 photo refs + 1 clay ref → Gemini produced a real baby, not clay figurine
- **"Sculpted clay with tool marks" > "rough sculpted clay texture"** — the latter overcorrects into dried pottery
- **Design/logo transfer is excellent** — pineapple applique, crosshatch pattern, shoulder buttons all transferred accurately (better than MJ)
- **Seated pose = Gemini extends fabric to cover legs** — need explicit "bare legs and bare feet" language for bodysuit/romper styles
- **Name each reference explicitly in the prompt** — "the first image is the master reference, the second is the clothing reference, the third is the clay texture reference"

#### Clothing Prompt Template (VALIDATED)
```
The first image is the master reference — a sculpted clay baby figurine.
This is the character. The output must be a clay figurine, not a real baby.

Dress the baby in the outfit from the clothing reference image. Keep the
baby's face, expression, skin tone, eye colour, hair, pose, and background
exactly the same. The clothing should look like sculpted clay with tool marks
and texture, matching the clay texture reference — not real fabric.

I've attached: (1) master oref, (2) clothing flat-lay, (3) clay texture reference.
```

#### Best Result So Far
`piney oref with clay ref.png` — pineapple t-shirt + pants with clay texture at the right level. Single combined prompt with 3 references (master + combined clothing image + clay texture ref).

### Files

| File | Purpose |
|------|---------|
| `docs/research/bb-content-production/orefs/` | Expression oref library (10 files including master-archived) |
| `docs/research/bb-content-production/orefs/master.png` | Current master oref (direct gaze, defined lips) |
| `docs/research/bb-content-production/orefs/master-archived.png` | Original master (slight off-center gaze, softer lips) |
| `docs/research/bb-content-production/clothing/` | Clothing test images and references |
| `docs/research/bb-content-production/clothing/piney oref with clay ref.png` | Best clothing result — use as quality benchmark |
| `docs/research/bb-content-production/MJ_ASSET_GENERATION_GUIDE.md` | Production guide (Sections 3-9 for poses, scenes — clothing now uses Gemini, not MJ two-step) |
| `config/babybrains/character_dna.json` | Canonical character config |

### Next Steps
1. **Clothing pipeline**: Test second outfit to confirm 3-ref workflow is repeatable
2. **Joyful eyes revisit**: Banked joy has great smile but neutral eyes — may need different tool
3. **Pose testing**: Try Gemini for tummy-down, reaching, standing (medium viability — MJ fallback for complex poses)
4. **Scene generation**: MJ likely still better for scenes (Gemini untested)
5. **SynthID/metadata**: Gemini embeds SynthID but outputs are intermediate assets, not published directly. Not a concern for current workflow. If needed, MJ pass-through would strip it.

---

## Previous Session: Post-ELEVATE Dash Cleanup (Feb 12, 2026 - Session 41)

### What Was Done

**D107: Deterministic post-ELEVATE dash cleanup — 3-audit consensus fix**

Root cause: `_remove_em_dashes` only ran on ELEVATE INPUT (pre-processing), never on OUTPUT.
LLM introduces new dashes during elevation, causing token-wasting retry cycles.

**3 Independent Audit Results (all Opus):**
| Audit | Method | Diagnosis Confidence | Fix Safety |
|-------|--------|---------------------|------------|
| 1 | Code flow trace | 95% CONFIRMED | 85% |
| 2 | Inversion test | CONFIRMED + warned superlative replacement UNSAFE | 85% |
| 3 | Junior analyst | CONFIRMED + recommended hybrid approach | 90% |

**Consensus:** Em-dash/en-dash deterministic cleanup on output is SAFE. Superlative replacement is UNSAFE (destroys Montessori exception terms like "ideal period", "extraordinary absorptive mind").

**Changes made:**
1. `_remove_em_dashes` → `_remove_dashes`: Now handles em-dash (U+2014), en-dash (U+2013), double-hyphen (--)
2. Added `_remove_dashes()` on ELEVATE OUTPUT in all 3 code paths (lines 2400, 2874, 3365)
3. `_quick_validate` now checks all 3 dash variants (aligned with QC hook's DASH_PATTERN)
4. Backward-compatible `_remove_em_dashes` alias preserved
5. Decision documented as D107 in DECISIONS.md

**Test Results:** 152 pass (146 + 6 new: en-dash cleanup, double-hyphen cleanup, mixed dashes, backward compat alias, en-dash quick_validate, double-hyphen quick_validate)

### Files Modified
| File | Changes |
|------|---------|
| `atlas/pipelines/activity_conversion.py` | _remove_dashes extended, post-ELEVATE cleanup in 3 paths, _quick_validate dash alignment |
| `tests/pipelines/test_activity_conversion.py` | 6 new tests for dash cleanup and quick_validate |
| `docs/DECISIONS.md` | D107 entry added |

### Also Fixed: D108 Quality Audit Timeout

`audit_quality()` hardcoded subprocess timeout at 300s/600s, ignoring `STAGE_TIMEOUTS['quality_audit']=900s`. Live testing showed audit consistently timing out at 600s. Now uses STAGE_TIMEOUTS as base (900s normal, 1080s final attempt). Commit: 4b58a0d.

### Next Session: Re-run Activities + Live Pipeline Testing

Same plan as Session 40 — D107 (dash cleanup) + D108 (audit timeout) should fix the two main failure modes.

---

## Previous Session: Pipeline Robustness Fixes (Feb 12, 2026 - Session 40)

### What Was Done

**Fixed 4 pipeline robustness issues blocking automated activity conversion:**

| # | Fix | Severity | Files |
|---|-----|----------|-------|
| 1 | Stage cache persistence across runs | CRITICAL | activity_conversion.py |
| 2 | Non-interactive stdin detection | HIGH | activity_conversion.py |
| 3 | Graceful shutdown + orphaned progress cleanup | MEDIUM | activity_conversion.py |
| 4 | Per-stage timeout configuration | LOW | activity_conversion.py, skill_executor.py |

**Fix 1 details:**
- Session ID changed from `convert_{raw_id}_{timestamp}` to `convert_{raw_id}` (deterministic)
- `convert_with_retry()` reloads cached transform from disk at start
- Loop condition changed from `attempt == 0 or cached_transform is None` to `cached_transform is None` (P54 BUG-1 fix)
- Cache path sanitized against path traversal (P54 SEC-1 fix)

**Fix 2 details:**
- `present_for_review()` checks `sys.stdin.isatty()` at top
- Non-interactive: auto-approves Grade A, auto-rejects below

**Fix 3 details:**
- Flag-based signal handlers (SIGINT/SIGTERM) with atexit cleanup (P54 BUG-3/4 fix: avoids deadlock)
- `_current_activity_id` tracked in `_update_progress_file()`
- `cleanup_stale_progress()` method + `--cleanup-stale` CLI flag
- `last_updated` timestamp added to progress cache

**Fix 4 details:**
- `STAGE_TIMEOUTS` class constant: ingest=300s, research=600s, transform=900s, elevate=1500s, validate=300s, qc_hook=60s, quality_audit=900s
- `timeout` parameter added to `SkillExecutor.execute()` and `_execute_cli()`
- Stage timing logs: `[STAGE_NAME] Completed in {duration:.1f}s`

**P54 Independent Critic findings (addressed):**
- BUG-1 (HIGH): Disk cache loaded but never used on attempt 0 -- FIXED (changed `or` to `and` logic)
- BUG-3/4 (MEDIUM): Signal handler deadlock risk -- FIXED (flag-based + atexit)
- SEC-1 (LOW): raw_id in cache path not sanitized -- FIXED (regex sanitization)
- BUG-2 (latent): Deferred -- only triggers if scratch_pad/session uninitialized, which won't happen with current _convert_from_cached_transform path

**Test Results:**
- Pipeline tests: 146 pass (132 original + 14 new)
- Full suite: 1033 pass, 2 pre-existing fails (Garmin auth, UI state file)

### Files Modified
| File | Changes |
|------|---------|
| `atlas/pipelines/activity_conversion.py` | All 4 fixes + P54 corrections |
| `atlas/orchestrator/skill_executor.py` | timeout parameter added to execute() and _execute_cli() |
| `tests/pipelines/test_activity_conversion.py` | 14 new tests (4 cache persistence, 2 stdin detection, 4 graceful shutdown, 4 stage timeouts) |

### Next Session: Re-run Activities + Live Pipeline Testing

**IMPORTANT FINDING:** 4 previously converted activities (January 2026) are missing guidance
cross-references because the guidance files didn't exist at conversion time. These must be
RE-RUN through the full pipeline (not patched) — the pipeline now has the guidance catalog
and will produce proper cross-references during the RESEARCH stage.

**Phase A: Clear stale scratch pad caches for re-runs**
The 4 existing activities may have stale scratch pads from their original conversion.
Delete them before re-running so the pipeline does a full fresh conversion:
```bash
rm -f ~/.atlas/scratch/convert_narrating-daily-care*.json
rm -f ~/.atlas/scratch/convert_infant-sign-language*.json
rm -f ~/.atlas/scratch/convert_reciting-and-acting-out-nursery-rhymes*.json
rm -f ~/.atlas/scratch/convert_washing-fruits-and-vegetables*.json
```
Also reset their progress status if needed:
```bash
python3 -m atlas.pipelines.activity_conversion --cleanup-stale
```

**Phase B: Re-run the 4 existing activities (full pipeline, one at a time)**

| # | Activity | Domain | Age | Missing Guidance Link | File Exists |
|---|----------|--------|-----|----------------------|-------------|
| 1 | `narrating-daily-care` | language | 0-12m | GUIDANCE_LANGUAGE_0001 | Yes (overwrite) |
| 2 | `infant-sign-language` | language | 6-36m | GUIDANCE_LANGUAGE_0001 + 0002 | Yes (overwrite) |
| 3 | `reciting-and-acting-out-nursery-rhymes` | language | 12-36m | GUIDANCE_LANGUAGE_0002 | Yes (overwrite) |
| 4 | `washing-fruits-and-vegetables` | practical_life | 12-36m | GUIDANCE_PRACTICAL_LIFE_0001 | Yes (overwrite) |

```bash
# Run each one sequentially, ~15-21 min each
python3 -m atlas.pipelines.activity_conversion --activity narrating-daily-care --retry 3 --verbose --auto-approve
```

**NOTE:** These activities already have canonical YAML files on disk. The pipeline should
overwrite them with improved versions that include proper guidance cross-references. Verify
the output files have `links_to_guidance` entries referencing the new guidance IDs.

**Phase C: New activities (verify pipeline fixes work end-to-end)**

| # | Activity | Why | Status |
|---|----------|-----|--------|
| 5 | `treasure-baskets-of-real-objects` | Cache test — got Grade A in Session 40, should use cached transform | Re-run |
| 6 | `using-vocabulary-books` | Tests GUIDANCE_LANGUAGE_0002 cross-ref | New |
| 7 | `cutting-a-banana` | Group primary (4 sources), hardest test | New |

**After each activity, verify:**
- Output file exists in `/home/squiz/code/knowledge/data/canonical/activities/{domain}/`
- Grade A achieved
- `links_to_guidance` contains expected guidance IDs
- No QC violations
- Australian English throughout

**Phase D: Commit + push all results to knowledge repo**
After all activities pass, commit the new/updated files to the knowledge repo.

### Deferred Items
1. Add 7 evidence IDs to EVIDENCE_BACKLOG.csv for tracking
2. Batch 2 guidance files (3 more) when ready
3. P54 BUG-2: Initialize scratch_pad/session in _convert_from_cached_transform path (latent, not triggerable currently)
4. Systemic: Add post-guidance-creation process to scan existing activities for missing cross-references

---

## Previous Session: 7-Phase Production Test Suite (Feb 11, 2026 - Session 39)

### What Was Done

**Executed 7-phase production-grade testing suite on Batch 1 guidance YAMLs.**

| Phase | Test | Verdict |
|-------|------|---------|
| 1 | Knowledge repo Tier 1 validation scripts (5 scripts) | PASS (1 pre-existing fail) |
| 2 | YAML schema + catalog + referential integrity | PASS |
| 3 | Content quality anti-pattern scan (QC rules) | PASS (4 false positives) |
| 4 | Pytest regression suite (1019 tests) | PASS (0 regressions, 2 pre-existing fails) |
| 5 | Activity conversion pipeline smoke test | PASS |
| 6 | P54 independent critic audit (cold review) | PASS after fixes |
| 7 | Cross-repo consistency verification | PASS |

**P54 Critic (Phase 6) found 2 issues in GUIDANCE_LANGUAGE_0002, now fixed:**
- Line 62: "bin lorry" -> "garbage truck" (British English, not Australian)
- Line 195: "astonishing capacity" -> "genuine capacity" (superlative removal)
- Line 195: "an" -> "a" (article grammar fix from replacement)

**Phase 1 notable findings (all pre-existing):**
- `check_ledger_activities_materials.py`: FAIL (4 canonical entries missing, 3 legacy placeholders)
- `check_guidance_evidence_refs.py`: FAIL (7 unknown evidence IDs from new files -- expected, evidence atoms not yet created)

**Phase 7 cross-repo verification:**
- Catalog-to-filesystem: 38/38 bidirectional match, zero orphans
- Dangling guidance refs: 16/17 resolve; 1 dangling (GUIDANCE_COMMUNICATION_0001 pre-existing)
- Materials catalog: 20 entries (unchanged)
- 7 new evidence IDs NOT yet in EVIDENCE_BACKLOG.csv (follow-up needed)

### Files Modified (this session)
| File | Repo | Changes |
|------|------|---------|
| `data/canonical/guidance/language/GUIDANCE_LANGUAGE_0002.yaml` | knowledge | P54 fixes: "bin lorry"->"garbage truck", "astonishing"->"genuine" |

### Completed Between Sessions
- P54 fixes committed and pushed to knowledge repo (commit 0b86239)
- `spreading-on-a-cracker` correctly skipped by pipeline (non-primary group member — validates grouping logic)
- `treasure-baskets-of-real-objects` achieved **Grade A on attempt 2** but pipeline hung at interactive approval prompt

### Next Session: Fix Pipeline Robustness Issues, Then Resume Live Testing

**Problem discovered:** The pipeline has 4 robustness issues that block reliable automated execution. These must be fixed BEFORE continuing live testing.

**Issue 1 (HIGH): Interactive prompt blocks non-interactive execution**
- File: `atlas/pipelines/activity_conversion.py` line ~3027
- `input("> ")` blocks when stdin is non-interactive (background mode, piped input)
- `--auto-approve` exists but shouldn't be required for programmatic use
- Fix: Add `sys.stdin.isatty()` check at start of `present_for_review()`, auto-skip if non-interactive

**Issue 2 (CRITICAL): Stage cache doesn't persist across runs**
- File: `atlas/pipelines/activity_conversion.py` lines ~2085-2087
- Each run creates a NEW scratch pad with unique timestamp in session_id
- Cache is in-memory only within `convert_with_retry()` — the `cached_transform` variable is local
- Scratch pad IS written to disk (`~/.atlas/scratch/convert_{raw_id}_{timestamp}.json`) but is NEVER reloaded on subsequent runs
- Fix: Use deterministic session_id (no timestamp), reload existing scratch pad on startup, extract cached transform

**Issue 3 (MEDIUM): No per-stage timeout configuration**
- File: `atlas/orchestrator/skill_executor.py` line ~586
- Global 1200s (20min) timeout for ALL stages via `ATLAS_CLI_TIMEOUT`
- Simple stages (INGEST, VALIDATE) don't need 20 min; complex stages (ELEVATE) might need more
- Fix: Add per-stage timeout dict, pass stage-specific timeout to skill executor

**Issue 4 (MEDIUM): Orphaned IN_PROGRESS on interruption**
- File: `atlas/pipelines/activity_conversion.py` lines ~3341, 3383
- If process is killed mid-execution, status stays IN_PROGRESS forever
- No staleness detection or cleanup mechanism
- Fix: Add signal handler for graceful shutdown, add `--cleanup-stale` CLI command, add timestamp to progress entries

**Key file locations for fixes:**
- Pipeline main: `atlas/pipelines/activity_conversion.py` (~3900 lines)
- Scratch pad: `atlas/orchestrator/scratch_pad.py`
- Skill executor: `atlas/orchestrator/skill_executor.py` (subprocess calls at ~line 586)
- Progress file: `/home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md`

**After fixes, resume live testing with:**

| # | Activity | Why | Status |
|---|----------|-----|--------|
| 1 | `treasure-baskets-of-real-objects` | Got Grade A but wasn't written to disk | Re-run with fixes |
| 2 | `using-vocabulary-books` | Tests GUIDANCE_LANGUAGE_0002 | Pending |
| 3 | `cutting-a-banana` | Group primary (4 sources), hardest test | Pending |

### Deferred Items
1. Add 7 evidence IDs to EVIDENCE_BACKLOG.csv for tracking
2. Batch 2 guidance files (3 more) when ready

---

## Previous Session: Guidance Content Gap Remediation Batch 1 (Feb 11, 2026 - Session 38)

### What Was Done

**Created 3 guidance YAML files (Batch 1 of remediation plan):**

| File | Domain | Age | Path |
|------|--------|-----|------|
| GUIDANCE_LANGUAGE_0001 | Prelinguistic Communication | 0-12m | `knowledge/data/canonical/guidance/language/GUIDANCE_LANGUAGE_0001.yaml` |
| GUIDANCE_LANGUAGE_0002 | Vocabulary Building & Language Explosion | 12-36m | `knowledge/data/canonical/guidance/language/GUIDANCE_LANGUAGE_0002.yaml` |
| GUIDANCE_PRACTICAL_LIFE_0001 | Food Preparation Progression | 15-36m | `knowledge/data/canonical/guidance/practical_life/GUIDANCE_PRACTICAL_LIFE_0001.yaml` |

**Source material synthesized from:**
- Understanding the Human Being (Montanaro) pp. 137-147
- The Joyful Child Parts 1 & 2 (Davies) pp. 10-12, 35, 39, 67-72
- Montessori from the Start Parts 2 & 3 (Lillard & Jessen) pp. 64-67, 76-80, 111-114

**P54 Independent audit completed.** Findings fixed:
- CRITICAL: Fabricated page number "TJC pp. 1006-1037" corrected to "pp. 67-68" in LANGUAGE_0002
- Superlatives removed: "profoundly," "remarkable" (x3), "most significant"
- AU English fixes: "cutting board" -> "chopping board," "cookie cutters" -> "biscuit cutters"
- Missing schema fields added: montessori_pillars (PL_0001), childcare_alignment (all 3), professional_support (PL_0001)
- Missing synthesized_from entry added: MFTS in LANGUAGE_0001

**Cross-references updated:**
- NAMING_GAME activity: `GUIDANCE_LANGUAGE_0001` -> `GUIDANCE_LANGUAGE_0002` (correct age match 12-36m)
- Coverage ledger: 5 entries updated from "categorized" to "synthesized" with canonical slugs

**Catalog regenerated:** 35 -> 38 guidance entries in `config/babybrains/guidance_catalog.json`

### Files Created (knowledge repo)
- `knowledge/data/canonical/guidance/language/GUIDANCE_LANGUAGE_0001.yaml`
- `knowledge/data/canonical/guidance/language/GUIDANCE_LANGUAGE_0002.yaml`
- `knowledge/data/canonical/guidance/practical_life/GUIDANCE_PRACTICAL_LIFE_0001.yaml`

### Files Modified
| File | Repo | Changes |
|------|------|---------|
| `data/canonical/activities/language/ACTIVITY_LANGUAGE_NAMING_GAME_TWO_PERIOD_LESSON_12_36M.yaml` | knowledge | Fixed guidance_id: 0001 -> 0002, updated slug |
| `data/coverage_ledger.csv` | knowledge | 5 entries: categorized -> synthesized |
| `config/babybrains/guidance_catalog.json` | ATLAS | Regenerated (35 -> 38 entries) |

### Remaining (Batch 2 - 3 files)
- GUIDANCE_LANGUAGE_0003 (Adult Language & Modelling, 0-36m)
- GUIDANCE_PRACTICAL_LIFE_0002 (Dressing & Self-Care, 12-36m)
- GUIDANCE_PRACTICAL_LIFE_0003 (Care of Environment, 18-36m)

### Remaining (Batch 3 - 1 file)
- GUIDANCE_LANGUAGE_0004 (Bilingual & Multilingual, 0-36m)

### Quality Notes
- All 3 files use BB voice (warm, evidence-informed, parent-as-capable)
- All content traces to specific source material with page numbers
- Cross-domain tags: 4 per file (exceeds minimum of 2)
- Australian English throughout (mum, nappy, chopping board, biscuit cutters, centre)
- quality_review schema uses simplified format (reviewed_by, qc_status) rather than MI-SYN/MI-QA format from earlier files. The catalog generator accepts both.

---

## Previous Session: Pipeline Fix - Guidance/Materials Cross-Referencing (Feb 11, 2026 - Session 37)

### What Was Done

**Part 1: Pipeline Fix (implemented)**
1. Created `scripts/build_guidance_catalog.py` — scans 35 guidance + 20 material YAMLs, generates JSON indexes
2. Generated `config/babybrains/guidance_catalog.json` (35 entries) and `materials_catalog.json` (20 entries)
3. Added `_load_guidance_catalog()` and `_load_materials_catalog()` to pipeline (cached, graceful degradation)
4. Modified `_execute_research()` to inject catalogs into input_data for cross-domain matching
5. Added `_fix_validation_misclassification()` — moves guidance/materials reference issues from blocking to warnings (tightly anchored patterns with structural exclusions)
6. Wired misclassification fix at all 3 validation code paths: `convert_activity`, `_convert_from_cached_transform`, `elevate_existing_file`
7. Updated `research_activity.md` skill: catalog-based matching instead of filesystem search (Sections 4+5)
8. Updated `validate_activity.md` skill: added LANGUAGE/PRACTICAL_LIFE/TOILETING to Valid Categories, external validators → SKIPPED_BY_SKILL, explicit warn/block clarification (Sections 3.1, 5, 7)
9. Added 11 unit tests (8 misclassification + 3 catalog loading) — all 132 pipeline tests pass

**Part 2: Content Gap Remediation Plan (saved)**
- `docs/PLAN_GUIDANCE_CONTENT_GAP_REMEDIATION.md` — standalone handoff for fresh agent to create 4 language + 3 practical_life guidance YAMLs

### Files Modified (ATLAS repo)
- `atlas/pipelines/activity_conversion.py` — 3 new methods + 1 modified method + 3 wiring points
- `tests/pipelines/test_activity_conversion.py` — 11 new tests (132 total)
- `config/babybrains/guidance_catalog.json` — NEW (generated index, 35 entries)
- `config/babybrains/materials_catalog.json` — NEW (generated index, 20 entries)
- `scripts/build_guidance_catalog.py` — NEW (catalog generator)
- `docs/PLAN_GUIDANCE_CONTENT_GAP_REMEDIATION.md` — NEW (Part 2 handoff)

### Files Modified (babybrains-os repo)
- `skills/activity/research_activity.md` — Sections 4+5: catalog-based cross-domain matching
- `skills/activity/validate_activity.md` — Sections 3.1, 5, 7: categories, validators, warn/block

### Next Steps
1. Re-run `cutting-a-banana` through pipeline to verify fix end-to-end
2. Execute Part 2: Create missing language/practical_life guidance YAMLs (use PLAN_GUIDANCE_CONTENT_GAP_REMEDIATION.md)
3. After guidance creation, regenerate catalogs: `python3 scripts/build_guidance_catalog.py`

---

## Previous Session: MJ Asset Generation Guide (Feb 11, 2026 - Session 36)

### What Was Done

**Created:** `docs/research/bb-content-production/MJ_ASSET_GENERATION_GUIDE.md` (~1,020 lines)
- Production handbook with ready-to-paste MJ prompts for every Baby Brains asset type
- 9 sections: Quick Start, Expressions, Poses, Clothing, Environments, Parameters, Defects, Checklist, Workflow
- Synthesised 3 research extraction agents + 5 local doc reviews + conflict resolution
- All prompts verified against 17 anti-patterns + character_dna.json canonical values
- Independent verification audit: 11/11 criteria PASSED

**Deleted:** `SYNTHESIS_PROMPT.md`, `RESEARCH_PROMPT_DIRECTOR_AGENT_PIPELINE_PART2B.md` (superseded)

**Conflict Resolutions Applied:**
- --ow 175/200 (character_dna.json user-tested values, not Part 1's 100)
- --sw 75-150 range (not Part 3's 200-350 which conflicts with Phase D "colour death" finding)
- "Polymer clay" safe in clothing conversion Step 1 only (anti-pattern in character prompts)
- Hands/fingers NOT in negative prompts (deformed hands, extra fingers ARE acceptable)
- --draft + --oref flagged as NEEDS TESTING (conflicting sources)
- Expression orefs built at --ow 175 with master oref, production use at --ow 100

### Files Created/Modified
| File | Changes |
|------|---------|
| `docs/research/bb-content-production/MJ_ASSET_GENERATION_GUIDE.md` | NEW — 9-section production handbook |
| `docs/research/bb-content-production/SYNTHESIS_PROMPT.md` | DELETED |
| `docs/research/bb-content-production/RESEARCH_PROMPT_DIRECTOR_AGENT_PIPELINE_PART2B.md` | DELETED |

### Next Steps
- User works through guide in MidJourney sessions (expressions first, then poses, clothing, scenes)
- Test --draft + --oref compatibility (flagged in guide)
- After asset generation: update character_refs.json with expression oref file paths

---

## Current Session: Phase 6 Smoke Tests + Infrastructure Fixes (Feb 11, 2026 - Session 35)

### What Was Done

**P54 Independent Verification (4 findings fixed):**
- F2 (CRITICAL): `test_truncated_json_repair` had trivially true assertion. Fixed to concrete `assert result is None`.
- F4 (HIGH): Missing test for `_detect_truncation` Check 3. Added `test_truncated_mid_parent_search_terms`.
- F9 (MEDIUM): `test_primary_returns_info` didn't verify `source_activities`. Added verification.
- F6 (MEDIUM): Weak assertion in YAML parse error test. Changed to exact equality.

**Infrastructure Fixes (Root Causes of Pipeline Failures):**
1. **CLI Timeout**: 600s hardcoded → configurable via `ATLAS_CLI_TIMEOUT` env var (default 1200s). Each stage gets its own timeout.
2. **API tool_use.name error**: `claude -p` was sending tool_use blocks with names >200 chars. Fixed by adding `--tools ""` to disable tools in CLI mode (skills are pure generation).
3. **Raw output logging**: Added `logger.warning` for raw output preview on TRANSFORM and ELEVATE failures.
4. **TRANSFORM JSON fallback**: Added `_extract_transform_yaml_fallback()` — when JSON parsing fails for TRANSFORM output (large YAML embedded in JSON breaks escaping), extracts YAML directly from raw output, bypassing JSON.
5. **ELEVATE JSON fallback**: Same pattern for ELEVATE stage via `_extract_elevate_yaml_fallback()`.
6. **"ideal" superlative exception**: Added `is ideal` (predicate suitability) and `not ideal` (negation) as exceptions in ai_detection.py. "A ripe banana is ideal" is practical language, not AI fluff.
7. **parent_search_terms exclusion**: `_quick_validate` now strips `parent_search_terms` section before superlative checking. SEO queries like "best books for..." are what parents actually search for.

### Smoke Test Results (Phase 6)

| Activity | Type | Attempt 1 | Status |
|----------|------|-----------|--------|
| `dancing-and-singing` | Standalone, language | Grade A (1 retry) | PASS |
| `using-vocabulary-books` | Standalone, language | QC_FAILED ("ideal") | RE-RUNNING with fix |
| `cutting-a-banana` | Group primary (4 sources) | TRANSFORM JSON fail → QC_FAILED ("ideal") | RE-RUNNING with fix |

- `dancing-and-singing` Grade A output: `/tmp/smoke_test_dancing_singing.yaml` (27,159 chars, 260 lines)
- Independent Opus quality audit: 5/5 across all 6 categories, zero anti-pattern violations

### Files Modified
| File | Changes |
|------|---------|
| `atlas/orchestrator/skill_executor.py` | Configurable timeout (ATLAS_CLI_TIMEOUT env var, default 1200s), `--tools ""` flag, raw output logging |
| `atlas/pipelines/activity_conversion.py` | TRANSFORM/ELEVATE JSON fallback extractors, parent_search_terms exclusion in `_quick_validate`, raw output logging |
| `atlas/babybrains/ai_detection.py` | "ideal" exceptions: `is ideal` (predicate), `not ideal` (negation) |
| `tests/pipelines/test_activity_conversion.py` | P54 fixes + fallback tests + exception tests (112→117 tests) |
| `tests/babybrains/test_ai_detection.py` | "ideal" exception tests (118→123 tests) |

### Test Results
- Pipeline tests: **117/117 passed**
- AI detection tests: **123/123 passed**
- Total: **240/240 passed**

### Next Steps
1. Check results of re-running `cutting-a-banana` and `using-vocabulary-books`
2. Quality audit any Grade A outputs
3. Phase 7: Batch configuration for ~202 pending activities
4. Commit all changes

---

## Previous Session: Activity Conversion Pipeline Pre-Production Audit & Fix (Feb 10, 2026 - Session 34)

### What Was Done
Implemented 5 phases from the 4-round Opus audit plan for the activity conversion pipeline (3,471 lines). The pipeline has never been run end-to-end in automated mode; all 28 canonical files were produced manually.

### Phase 1: Unit Tests (102 tests)
- Created `tests/pipelines/__init__.py`, `conftest.py`, `test_activity_conversion.py`
- 102 tests covering 11 functions: `_parse_age_label`, `_detect_truncation`, `_fix_canonical_slug`, `_fix_principle_slugs` (24 parametrized mappings), `_remove_em_dashes`, `_quick_validate`, `_extract_audit_json`, `_should_skip`, `_get_group_info`, `_update_summary_counts`, `_fix_age_range`, `reconcile_progress`
- Fixture uses `object.__new__()` to bypass heavy `__init__` constructor

### Phase 2: Wire `_quick_validate` + `_fix_age_range` into ALL 3 code paths
- **H7 fix:** `_fix_age_range` was only called in `elevate_existing_file`. Now called in all 3 paths: `convert_activity`, `_convert_from_cached_transform`, `elevate_existing_file`
- **V1 fix:** `_quick_validate` was dead code (defined but never called). Now wired into all 3 paths as a fast pre-filter before expensive QC hook
- **P5 fix:** `_quick_validate` now uses `ai_detection.py`'s `check_superlatives` (context-aware exceptions) and `check_pressure_language`. "best practices" no longer false-flagged.
- Added `"ideal"` to `ai_detection.py` SUPERLATIVES with Montessori exception (`ideal period`)
- Behavior differs per path: `convert_activity`/`_convert_from_cached_transform` return QC_FAILED; `elevate_existing_file` continues to next retry

### Phase 3: Fix `_update_summary_counts` (C5)
- Was only writing Done/Pending/Failed. Skipped was counted but not written.
- Now writes all 7 statuses: Done, Pending, Failed, Skipped, Revision Needed, QC Failed, In Progress
- Uses conditional insertion for fields that may not exist in the progress file header

### Phase 4: Progress Tracker Reconciliation
- Added `reconcile_progress()` method: scans canonical output dir, cross-references with progress data
- Added `--reconcile` CLI argument
- Reports: files on disk vs tracked, untracked files, missing files, status counts

### Phase 5: QC Hook `--no-llm-context` Flag (V8)
- Added `--no-llm-context` CLI flag and `QC_NO_LLM_CONTEXT` env var to `check_activity_quality.py`
- When set, `LLM_CONTEXT_CHECK_ENABLED = False` -- all 4 LLM functions return False (default to flagging)
- Gives regex-only QC: <1s vs 30-60s per activity

### Files Created
| File | Purpose |
|------|---------|
| `tests/pipelines/__init__.py` | Test package |
| `tests/pipelines/conftest.py` | Pipeline fixture (object.__new__ approach) |
| `tests/pipelines/test_activity_conversion.py` | 102 tests for 12 functions |

### Files Modified
| File | Changes |
|------|---------|
| `atlas/pipelines/activity_conversion.py` | Import ai_detection; rewrite `_quick_validate` to use shared module; wire `_fix_age_range` into 2 missing paths; wire `_quick_validate` into all 3 paths; fix `_update_summary_counts` for 7 statuses; add `reconcile_progress()`; add `--reconcile` CLI |
| `atlas/babybrains/ai_detection.py` | Add `"ideal"` to SUPERLATIVES (9 words), add Montessori exception `ideal period` |
| `knowledge/scripts/check_activity_quality.py` | Add `--no-llm-context` flag and `QC_NO_LLM_CONTEXT` env var |

### Test Results
- Pipeline tests: **102/102 passed**
- AI detection tests: **118/118 passed**
- Full BB suite: **660 passed, 7 skipped** (API key gated)

### P54 Warning: Tests Need Independent Verification
The 102 tests in `tests/pipelines/test_activity_conversion.py` were written by the same agent that wrote the code. Per P54 (self-review degrades quality), spawn a **fresh independent agent** to:
1. Read ONLY the test file and the functions being tested (not the plan)
2. Check for tests that test the mock instead of actual behavior
3. Look for missing edge cases and boundary conditions
4. Verify fixture correctly simulates real pipeline state

### Next Steps (Phases 6-7)

**IMMEDIATE: Independent test verification (before trusting any test results)**

**Phase 6: Smoke Test** (3 activities end-to-end):
1. Pick 3 diverse activities from `--list-pending` output:
   - 1 simple movement activity
   - 1 different domain (language or feeding)
   - 1 group primary
2. Run each: `python3 -m atlas.pipelines.activity_conversion --activity <id> --retry 2`
3. Monitor memory: `watch -n5 'ps aux --sort=-rss | head -5'`
4. Verify `_quick_validate` appears in logs (confirms Phase 2 wiring works in practice)
5. Success criteria: at least 1 of 3 achieves Grade A

**Phase 7: Batch Configuration:**
1. Decide batch size (all ~202 pending vs chunks of 30-50)
2. Decide LLM context: on (slower, fewer false positives) or off (faster)
3. Set up monitoring wrapper
4. Document production run procedure
5. **BEGIN BATCH PROCESSING** -- ~202 pending activities

### Full plan reference
`/home/squiz/.claude/plans/iridescent-weaving-mccarthy.md`

---

## Previous Session: Phase D Documentation & Config Sync (Feb 10, 2026 - Session 33)

### What Was Done
Updated all documentation, config files, and code to reflect Phase D four-layer architecture. 12 identified gaps between CHARACTER_GLOW_GUIDE.md and actual Phase D findings.

### Files Modified

| File | Action | Summary |
|------|--------|---------|
| `docs/research/bb-content-production/CHARACTER_GLOW_GUIDE.md` | EDIT (13 targeted edits) | Updated Production Reference Architecture to four-layer, fixed SSS from "DROPPED" to "CONFIRMED SAFE", updated --cref→--oref throughout, added Phase D findings, updated config schema to v3.0, added V7 incompatibilities |
| `config/babybrains/mj_prompts.json` | REWRITE | V8→V9 Phase D. Added oref+sref dual reference, Phase D prompt language, updated negatives, removed SSS from keywords_to_avoid, added compound anatomical expression descriptors |
| `config/babybrains/character_dna.json` | REWRITE | "Warm watercolour illustration"→"Phase D sculpted clay figurine". Documented four-layer architecture, expression library, production rules, V7 incompatibilities |
| `atlas/babybrains/content/assets.py` | EDIT | Updated SSS_FORMULA to Phase D language, fixed KEYWORDS_TO_AVOID (removed SSS, added porcelain/vinyl) |
| `tests/babybrains/test_assets.py` | EDIT | 5 tests updated for Phase D assertions |
| `docs/research/bb-content-production/RESEARCH_PROMPT_DIRECTOR_AGENT_PIPELINE.md` | CREATE | Comprehensive Opus research prompt for Director Agent pipeline design |
| `docs/research/bb-content-production/EXPRESSION_LIBRARY_PROMPTS.md` | CREATE | 8 copy-paste MJ prompts for expression library with evaluation rubrics |

### Test Results
- `test_assets.py`: **25/25 passed**
- Full BB suite: **660 passed, 7 skipped, 0 failures**

### Key SSS Correction
Phase C Test 3 found SSS was not a visible TOGGLE (no difference with/without when warmth already present). This was misinterpreted as "SSS is unsafe" and it was DROPPED from prompts. Phase D testing (12+ images) confirmed SSS is SAFE when used alone — zero eye glow artifacts. It was only problematic when triple-stacked with "lit from within" + "bioluminescent." SSS phrase restored to production prompts for warmth control.

### Next Steps
1. User selects final oref (skin warmth candidate)
2. Generate Phase D.2 expression library using prompts from EXPRESSION_LIBRARY_PROMPTS.md
3. Give RESEARCH_PROMPT_DIRECTOR_AGENT_PIPELINE.md to Opus Research Agent for pipeline design doc
4. Phase E: Kling animation testing
5. Phase F: DaVinci glow post-production

---

## Previous Session: BB Mascot Phase D — Oref Refinement & Skin Warmth (Feb 9-10, 2026 - Sessions 31-32)

### Context
Phase D: solving the clay texture identity problem. Clay texture via clothing PROVEN. New oref created from best MJ output (Testing 1/clothing1.png) through sequential Gemini edits. Remaining blocker: skin warmth/radiance lost through editing passes.

### Phase D Results Summary — Clay Texture & Architecture (Feb 9-10, ~200+ images)

| Test | Verdict | Key Finding |
|------|---------|-------------|
| R1: --cref vs --oref | **SKIPPED** | MJ web UI "Omni Reference" box IS --oref. We've been using --oref all along. |
| R2: Double-anchor (oref+sref) | **R2b WINS** | --sw 100 = 100% usable, best consistency. --sw 200 = clothing contamination. |
| R3a: Current material language | **POOR** | 25-37% usable. Eye issues 50%, hand/foot issues 100%. |
| R3b: Research material language | **CLEAN BUT NO CLAY** | 100% usable but reads as vinyl/3D render. Zero clay texture on skin. |
| R3c: Stop-motion clay language | **MARGINAL** | Slight forehead texture. Still reads as 3D render. Clothing slightly more textile. |
| Oref assessment | **ROOT CAUSE** | Current oref has ZERO clay texture → overrides all prompt language. |
| Separated sref (real clay photo) | **BREAKTHROUGH** | Clay sculpture as sref + baby as oref = clay clothing texture achieved. |
| New oref generation (raw clay sref) | **TOO AGGRESSIVE** | --sw 150 with raw clay sref = brown/monochrome, heavy, lost colour. |
| New oref (Clothing 1 as sref) | **CLOSE** | --sw 75 = subtle texture. Good eyes but clothing texture too light for oref baseline. |
| Clothing-to-clay conversion | **PROVEN** | Two-step: catalogue clothing → clay conversion via clay sref + image prompt. |
| Gemini outfit edit (sage→cream) | **SUCCESS** | Clean colour swap, texture preserved. |
| Gemini eye edit (→cornflower blue) | **SUCCESS** | Took 2 attempts (first too saturated cobalt). Final: soft cornflower blue. |
| Gemini gaze edit (→direct camera) | **FAILED x3** | Gemini cannot do sub-pixel pupil repositioning. Gaze ~85% direct. |
| Gemini background (→white) | **SUCCESS** | Clean cutout, no fringing. |
| Photopea warmth grading | **PARTIAL** | Curves+CB+Sat got to ~80% of original warmth. Vintage/yellow feel, not radiant. |
| Photopea Soft Light overlay | **FAILED** | Muddy, killed eye sparkle. Avoid. |
| MJ warmth via old cref sref | **WARMTH YES, ARTIFACTS** | Grey bg bleed, grainy surface, blobby hands. Proves MJ can do warmth. |
| **Skin warmth** | **UNSOLVED** | Post-processing cannot replicate MJ's baked-in warm lighting/luminosity. |

### Phase D Critical Findings

1. **--stop is NOT compatible with V7.** Research paper was wrong. Remove from all prompts.
2. **The oref image is the strongest texture signal.** Prompt words cannot override a smooth oref. The oref must carry the desired texture.
3. **Clay identity lives in the CLOTHING, not the skin.** Smooth skin + clay clothing = parents immediately recognise "clay figurine." Rough skin = unattractive.
4. **Separated reference architecture works:** oref = character identity, sref = clay texture. BUT the sref must be the right intensity — raw clay sculpture is too aggressive (kills colour, makes everything brown).
5. **Two-step clothing pipeline PROVEN:** Step 1: Convert catalogue clothing → clay using clay sref + clothing image prompt. Step 2: Apply clay clothing to character.
6. **Batch-to-batch variance is significant.** Single batches can't determine true hit rates. R2b showed 100% in one batch, R3a (same params) showed 25% in another.
7. **MJ V7 "polymer clay" = smooth/polished.** MJ interprets this as finished Sculpey figurines. Use "sculpted clay" or "modeling clay" for rougher texture.
8. **Hands/feet remain the weakest point across ALL variants.** Blobby fists hide finger issues. Kling animation needs clear geometry.

### Phase D New Architecture (Replacing Phase C Architecture)

**Old:** Single --cref (smooth baby) + prompt text for everything
**New:** Upgraded oref (baby WITH clay-textured clothing) + clay sref for texture reinforcement

```
Omni Reference (oref)  → CHARACTER + CLAY CLOTHING BASELINE (new image with sculpted clay garment)
Style References (sref) → CLAY TEXTURE REINFORCEMENT (real clay sculpture photo, --sw 75-150)
Image Prompts           → CLOTHING COLOUR/PATTERN (catalogue images converted to clay first)
Prompt text             → SCENE, EXPRESSION, SPECIFIC OUTFIT DESCRIPTION
```

### Two-Step Clothing Pipeline

```
STEP 1: Convert catalogue clothing → clay
  - Style References: Clay sculpture photo (Clay ref 1 or 2)
  - Image Prompts: Catalogue clothing photo
  - Prompt: "sculpted polymer clay [colour] [pattern] onesie, hand-formed clay
    with visible tool marks and sculpting texture, miniature clothing, white background"
  - Output: Clay interpretation of the garment

STEP 2: Apply clay clothing to character
  - Omni Reference: New master oref (baby with clay clothing)
  - Style References: Clay sculpture photo
  - Prompt: Full character prompt with outfit description
  - Output: Baby character wearing clay-textured version of catalogue outfit
```

### Clay Style References

| File | Description | Best --sw | Notes |
|------|-------------|-----------|-------|
| `Phase D/CLAY ref.png` | Raw clay baby sculpture close-up | 75-150 | Strong texture. At --sw 150+ kills colour → brown/monochrome |
| `Phase D/CLAY 2 ref.png` | Olive/brown clay child sculpture | 75-150 | Heavier texture than ref 1. Good for aggressive clay look |
| `Phase D/clothing1.png` | Baby with sage green clay onesie | 75 | Best balance of texture + colour. Use as sref for subtle clay |

### New Oref Status: SELECTING FROM CANDIDATES

The new oref has been refined through Gemini edits to achieve: cream clay-textured clothing, cornflower blue eyes, white background. The remaining issue is skin warmth — lost through multiple editing passes. User has several candidate images to evaluate.

**Current image files in `docs/research/bb-illustrative/`:**
- `--oref.png` — Base new oref (white bg, cream outfit, cornflower eyes, COOL skin)
- `--oref-adjusted.png` — Photopea warmth-graded version (~80% of original warmth)
- `--oref - adjusted.Fill.png` — Soft Light attempt (REJECTED - muddy)
- `--cref.archived.png` — Original cref (perfect warmth, no clay clothing) — REFERENCE ONLY
- `colour graded.png` — Gemini warmth attempt (REJECTED - yellow foundation look)
- `maybe 1.png` — MJ gen with old cref as sref (best warmth but artifacts)
- `1.png, 3.png, 6.png, 8.png` — Additional candidates user is evaluating
- `test/` — Archived test images from earlier phases (moved to clean up)

**Target oref qualities:**
- Baby character identity preserved (face, eyes, proportions)
- Clothing clearly reads as sculpted clay (visible tool marks, hand-formed)
- Warm golden-peach skin tone with rosy cheeks (radiant, not yellow/vintage)
- Cornflower blue eyes with catchlights
- Cream/neutral outfit (won't bias future colour generations)
- Clean white background
- Front-facing sitting pose

**Skin warmth options for next session:**
1. Accept oref-adjusted (~80% warmth) — let prompt language carry the rest
2. Strategic MJ run: --ow 200 + old cref as sref at --sw 50 + full warmth language. 2-3 batches only.
3. Try Photopea "Photo Filter > Warming 85" at 10-20% density (not yet tested, reportedly forgiving)

### Gemini (Nano Banana) Capabilities & Limits (Learned Session 32)
- **Good at:** Outfit colour swaps, background removal, eye colour changes
- **Bad at:** Sub-pixel gaze adjustment, subtle colour grading (applies flat tint), warmth/luminosity
- **Each pass slightly degrades** image quality and shifts colour balance — minimize passes
- **AI Moderator blocks** "nappy/diaper" + baby, "realistic clothing" in negatives

### Photopea Techniques (Learned Session 32)
- **Curves per-channel** (Red channel up, Blue channel down in midtones): Removes cool cast
- **Color Balance** (Midtones: Red +8, Yellow +5; Highlights: Red +3): Targeted warmth
- **Saturation +8-12**: Restores life to desaturated Gemini output
- **Soft Light overlay**: AVOID — tints eyes, kills sparkle, muddy result
- **Photo Filter (Warming 85)**: Not yet tested — reportedly most forgiving
- Save PSD for working file, Export PNG for MJ use

### Key Insight: Post-Processing Cannot Replicate MJ Baked-In Warmth
The original cref's "radiant alive" quality comes from how MJ rendered warm light at generation time (subsurface scattering, clean highlights, directional warmth). Colour grading shifts hue/saturation but cannot add luminosity to a flat-lit image. Warming a dull image just makes it yellow/vintage, not radiant. If warmth is critical, it must come from MJ generation (prompt language + lighting) not post-processing.

### Research Paper Errors Discovered

| Claim | Reality |
|-------|---------|
| "--cref is dead in V7, migrate to --oref" | MJ web UI "Omni Reference" IS --oref. We were already using it. |
| "--stop 85-90 preserves rough clay texture" | **--stop is NOT compatible with V7.** Prompt rejected. |
| "Visible fingerprints" is the strongest texture cue | Prompt words cannot override a smooth oref. Reference image is stronger. |
| "--stylize 500-700 fights photorealistic pull" | Not yet tested in isolation. May still be valid with image prompts. |

### Phase C Results Summary (4 tests, ~80 images)

| Test | Verdict | Key Finding |
|------|---------|-------------|
| 1. Colour palette (6 colours) | **PASS** | All colours hold, no grey-pulling. Knit/sleeves fail via text negatives. |
| 2. Scene contexts (4 scenes) | **PASS** | All scenes render, character holds. Cool colours desaturate in warm light. |
| 3. Warmth toggle (SSS A/B) | **FAIL** | No visible difference. SSS phrase is redundant. Skin nicer without it. **DROPPED from prompts.** |
| 4. Image prompts (2 outfits) | **CONDITIONAL** | Garment shape YES, complex prints NO, degrades clay toward vinyl/porcelain. |

### Phase C.5 Results — Image Prompt Refinement (3 sub-tests)

| Sub-test | Image Prompt | Result |
|----------|-------------|--------|
| C.5a: --cref as --sref + flat-lay romper | Flat-lay product photo + --cref doubled as --sref at --sw 200 | Jumbo/ballooning clothing. --sref fought image prompt. |
| C.5b: Full baby wearing clothes | Baby in striped onesie (white bg, no filter) | Expression contaminated (open mouth), clay → porcelain, but garment fit GOOD |
| **C.5c: Cropped body (no face)** | Baby torso only, head removed, transparent bg | **WINNER.** Expression clean, garment fit good, short sleeves, hands/feet improved. Transparent bg → black (use white fill). Clay slightly degraded but usable. |

**Validated clothing image prompt recipe:**
```
1. Product photo of garment ON a baby (fitted proportions)
2. Crop head off (prevents expression contamination)
3. Crop/remove background
4. Fill background WHITE (not transparent — MJ reads transparent as black)
5. Upload as image prompt alongside --cref
```

**Production rule:** Simple patterns (stripes, solids, colour-blocking) transfer cleanly. Complex illustrated prints don't. Garment SHAPE always transfers.

### Key Decisions This Session
1. **SSS phrase DROPPED from production prompts.** Test 3 proved no visible toggle effect. Skin nicer without it.
2. **Clothing control via cropped image prompt, not text.** Text negatives cannot override MJ V7 knit prior. Image prompts solve garment shape + sleeves.
3. **Colour-scene compatibility rules** for Director Agent: cool colours avoid warm interiors, cream avoids warm light.
4. **--sref as clay anchor did NOT work** (C.5a). The --sref fights the image prompt rather than complementing it.
5. **Cropped body (no face) is the optimal image prompt format** for clothing. Preserves garment fit info while avoiding expression/identity contamination.

### PRODUCTION REFERENCES (Phase D — Evolving)

| Reference | MJ Box | File | Description |
|-----------|--------|------|-------------|
| **Master oref (OLD)** | Omni Reference | `docs/research/bb-illustrative/--cref.archived.png` | Smooth baby, no clothing. ARCHIVED — has zero clay texture. Reference for warmth/skin tone only. |
| **Master oref (NEW)** | Omni Reference | `docs/research/bb-illustrative/--oref.png` or `--oref-adjusted.png` (PENDING SELECTION) | Baby with clay-textured cream onesie, cornflower eyes, white bg. Skin warmth TBD. |
| **Clay sref 1** | Style References | `test/` (moved to archive) | Raw clay baby sculpture. Use at --sw 75-150. |
| **Clay sref 2** | Style References | `test/` (moved to archive) | Olive clay child sculpture. Heavier texture. |

### Architecture: Four Independent Layers (Phase D)
```
Omni Reference (oref)    → CHARACTER + CLAY CLOTHING BASELINE
Style References (sref)   → CLAY TEXTURE REINFORCEMENT (--sw 75-150)
Image Prompts + text      → SPECIFIC OUTFIT (catalogue→clay conversion)
DaVinci PowerGrade        → GLOW (breathing animation, post-production)
```

### Key Decisions Made This Session
1. **--sref ABANDONED.** Phase B testing proved --sref contaminates clothing colour (blue→grey), sleeve length (short→long), garment style at ALL --sw levels (100/200/300). Not tunable.
2. **Single --cref architecture adopted.** --cref carries character identity only. Clothing, warmth, scene, expression all via prompt text. Full creative freedom.
3. **SSS warmth via PROMPT, not reference.** "Subtle warm subsurface scattering in the clay" in prompt text — include for warm scenes, omit for neutral. Proven to work with --cref-only.
4. **No SSS baked into --cref.** Neutral skin baseline gives maximum flexibility. Warmth is scene-dependent, not character-dependent.
5. **MJ V7 cannot produce fine hair.** After 30+ generations across multiple prompts/parameters, MJ stubbornly renders thick combed strands. Fixed via Nano Banana external AI editing.
6. **Director Agent = animation studio pipeline.** Preset emotions, clothing options, scene templates, warmth levels. Agent composes from validated library.

### Key Document: CHARACTER_GLOW_GUIDE.md
`docs/research/bb-content-production/CHARACTER_GLOW_GUIDE.md` — ~1600+ lines, living document.
Now includes: full Production Reference Architecture, Director Agent pipeline design, single --cref architecture rationale, config file structure, expression library plan, 11 agent guidance notes.

### Phase Order (Current → Future)

| Phase | Status | Description |
|-------|--------|-------------|
| **A: R14 Screening** | DONE | SSS confirmed as warmth trigger |
| **B: Reference Architecture** | DONE | --sref abandoned, single --cref locked, prompt warmth |
| **C: Colour + Scene Validation** | DONE | Colour PASS, scene PASS, SSS toggle FAIL (dropped), image prompt CONDITIONAL |
| **C.5: Image Prompt Refinement** | DONE | Cropped body (no face) + white bg = best clothing method. --cref as --sref failed. |
| **D: Clay Texture & New Oref** | **IN PROGRESS** | Clay identity via clothing (not skin). New oref with clay clothing. Two-step clothing pipeline proven. |
| D.2: Expression Library | Pending | 6-8 emotion refs (after oref locked) |
| E: Kling Animation Test | Pending | Breathing animation from production stills |
| F: DaVinci PowerGrade | Pending | Tier 0/1/2 glow grades + Fusion breathing macro |
| G: Director Agent Build | Pending | Agent reads config, assembles prompts from asset library |

### Phase C+C.5 Protocol — COMPLETE
All 4 Phase C tests + 3 Phase C.5 sub-tests complete (~80+ images analysed). See results tables above. Next phase: D (Expression Library).

**Base prompt for Test 1:**
```
A stylized clay baby figurine sitting, smooth refined clay, smooth warm
golden tan skin, round head, wearing a simple [COLOUR] short-sleeve
onesie. Subtle warm subsurface scattering in the clay. Round silvery
blue eyes full of wonder, fine wispy blonde hair close to scalp, calm
gentle expression, small rounded hands with defined fingers, bare feet
with five distinct small toes. Premium collectible figurine, art toy
quality. Front lighting, soft warm fill light. Clean studio photography,
neutral grey background, shallow depth of field.
--cref [CREF_URL] --v 7 --style raw --s 250 --ar 2:3
--no side lighting, rim light, backlit, rough texture, photorealistic,
Disney, Pixar, glossy, neon, fire, sparks, cracks, veins, lava, heart,
eyelashes, makeup, deformed hands, extra fingers, fused toes, missing
fingers, transparent, translucent, thick hair, styled hair, volumized hair
```

### Image Analysis Protocol
When user shares MidJourney generations, analyze each image with this scoring:

| Dimension | What "Good" Looks Like |
|-----------|----------------------|
| **Glow quality (1-5)** | Warm, diffuse, internal-feeling, not side-lit or surface flush |
| **Glow type** | Classify: diffuse body / heart-shaped / side-lit / surface warm / none |
| **Character consistency (1-5)** | Peach fuzz hair, blue eyes with catchlights, clay texture, proportions |
| **Video suitability (Y/N/Maybe)** | Clean forms, no complex textures that will morph, stable silhouette |
| **--sref suitability** | Neutral bg, no distinctive clothing, controlled blush, even warmth |

### Key Learnings from Reference Selection
| Finding | Impact |
|---------|--------|
| --sref captures background + clothing + colour palette | Neutral bg MANDATORY for --sref |
| Pupil-to-iris ratio determines engagement quality | SSS/8 rejected despite technical quality — "staring off" |
| MJ V7 renders knit textures for baby figurines despite negatives | Accepted as unavoidable — prompt overrides at moderate --sw |
| Nude baby prompts blocked by MJ moderator | Use "bodysuit matching clay skin tone" or neutral onesie |
| "Bodysuit matching skin tone" creates colour zone differential | Grey onesie is safer — no colour contamination |
| Expression library MUST use locked --sref | Generate emotions AFTER --sref is locked (Phase D) |
| Three independent controls: --cref + --sref + prompt | Character identity, warmth style, and scene are separable |

### --sref Winning Prompt (produced v2/6)
```
A stylized clay baby figurine sitting, smooth refined clay, smooth warm
golden tan skin, round head, wearing a simple smooth plain light grey
onesie. Subtle warm subsurface scattering in the clay. Round silvery
blue eyes, subtle blonde hair close to scalp, calm gentle expression,
small rounded hands with defined fingers, bare feet with five small
toes. Premium collectible figurine, art toy quality. Front lighting,
soft warm fill light. Clean studio photography, neutral grey background,
shallow depth of field.
--v 7 --style raw --s 250 --ar 2:3
--no side lighting, rim light, backlit, rough texture, textured skin,
pores, photorealistic, Disney, Pixar, glossy, neon, fire, sparks,
cracks, veins, lava, heart, eyelashes, makeup, blush, deformed hands,
extra fingers, fused toes, missing fingers, transparent, translucent,
knitted, knit texture, woven, buttons, patterns, embroidery
```

### Files to Read
1. `.claude/handoff.md` — This file (current state)
2. `docs/research/bb-content-production/CHARACTER_GLOW_GUIDE.md` — Living glow reference (~1400+ lines) with LOCKED REFERENCES and Production Reference Architecture
3. `docs/research/bb-content-production/ROUND_14_PROMPTS.md` — R14 results, contradiction resolutions, V7 compatibility
4. `docs/research/bb-illustrative/Controlling inner glow on AI-generated clay figurines.md` — Research agent results (450 lines)
5. `docs/research/bb-illustrative/bb baby ref.png` — LOCKED --cref (character identity)
6. `docs/research/bb-illustrative/sss.v2/6.png` — LOCKED --sref (warmth/style reference)

### Files Updated This Session
- `.claude/handoff.md` — This file (full rewrite of current session section)
- `docs/research/bb-content-production/CHARACTER_GLOW_GUIDE.md` — LOCKED REFERENCES table, Production Reference Architecture, dual reference system, expression library plan, agent guidance notes
- `docs/research/bb-content-production/ROUND_14_PROMPTS.md` — Contradiction resolutions, full results section, V7 compatibility table

---

## Previous Session: BB Baby Character Asset V4 Update (Feb 4, 2026 - Session 18)

### What We Did
1. **Updated hero prompt with bioluminescent SSS language** (`atlas/babybrains/content/assets.py`):
   - Added "subsurface scattering, lit from within" for inner glow effect
   - Added "bioluminescent inner glow, soft inner luminance"
   - Added "subtle translucency" for light passing through edges
   - Added "wax-like warmth" for tactile quality (not plastic)
   - Increased `--stylize 250` and added `--chaos 15` for SSS variation
   - Added "Brancusi" reference for sculptural aesthetic

2. **Added brand DNA constants**:
   - `SSS_FORMULA`: Core subsurface scattering prompt formula
   - `KEYWORDS_TO_AVOID`: Terms that cause generic drift (cute, adorable, plastic, etc.)
   - Glow spectrum philosophy documented in code comments

3. **Updated turnaround and expression prompts**:
   - All prompts now include SSS language
   - Added "cold lighting" to negative prompts
   - Increased --stylize to 100 for consistency

4. **Updated CharacterFeatures dataclass**:
   - Added `translucency` and `texture` properties
   - Updated `lighting` to describe bioluminescent inner glow

5. **Updated config/babybrains/mj_prompts.json**:
   - Added `brand_version: "V4 - Bioluminescent Subsurface Glow"`
   - Added `brand_dna` section with visual language documentation
   - All character prompts include SSS language

6. **Added 7 new tests** for SSS language verification:
   - `test_hero_prompt_has_sss_language`
   - `test_hero_prompt_has_increased_stylize`
   - `test_hero_prompt_has_chaos_for_variation`
   - `test_sss_formula_constant_exists`
   - `test_keywords_to_avoid_exists`
   - `test_turnaround_prompts_have_sss`
   - `test_expression_template_has_sss`

### Files Modified
- `atlas/babybrains/content/assets.py` — Added SSS language, brand DNA constants, updated CharacterFeatures
- `config/babybrains/mj_prompts.json` — V4 brand-aligned prompts with SSS
- `tests/babybrains/test_assets.py` — 7 new tests for SSS verification

### Test Results
- Asset tests: 25/25 passing (18 existing + 7 new)
- Full BB suite: 660 passed, 7 skipped (API key gated)

### Key Changes in V4 Hero Prompt

**Before (Iteration 1 - missing inner glow):**
```
stylized sculptural infant, smooth ovoid head, soft matte clay surface,
large expressive bright blue eyes, small natural swirl of warm light
blonde hair at front of head, warm tan clay-amber skin, inner glow...
--stylize 100
```

**After (V4 - Bioluminescent SSS):**
```
stylized sculptural infant, smooth ovoid head referencing Brancusi,
soft matte clay surface with warm subsurface scattering, lit from within,
large expressive bright blue eyes, small natural swirl of warm light
blonde hair at front of head, warm tan clay-amber skin with subtle translucency,
bioluminescent inner glow, soft inner luminance, simplified rounded body,
soft cotton onesie in muted earth tones, clean white background, full body,
front view, soft volumetric light, warm golden ambient lighting,
stop-motion aesthetic, wax-like warmth
--stylize 250 --chaos 15
```

### What to Look For in Iteration 2 Results
- Warm amber inner luminance emanating FROM the character (not just surface lighting)
- Subtle translucency at edges (ears, fingertips)
- Character feels like it belongs with wooden brain & cosmic sphere assets
- "Lit from within" quality similar to Maple Vertical brain asset

### Next Steps (Phase 1 Iteration 2)
1. Run V4 hero prompt in MidJourney (10-15 variations)
2. Look for: bioluminescent inner glow visible, not just soft lighting
3. Select best candidate with SSS quality
4. Proceed to Phase 2 video validation

---

## Previous Session: BB Baby Character Asset Workflow (Feb 4, 2026 - Session 17)

### What We Did
1. **Implemented BB Baby character asset management module** (`atlas/babybrains/content/assets.py`):
   - `AssetWorkflowState` class with 8 phases (Feature Spec → Photo Integration)
   - `CharacterAsset`, `VideoValidationResult`, `StyleLockConfig` dataclasses
   - `CharacterFeatures` dataclass with YOUR distinctive features (blonde swirl, blue eyes, tan skin)
   - `AssetPhase` enum for workflow phases
   - MidJourney V7 prompt templates (hero, turnaround, expressions, environments)
   - Video tool prompts for Pika and Kling
   - AU localisation cues and avoid list
   - Persistent state at `~/.atlas/.babybrains/assets/workflow_state.json`

2. **Created config files**:
   - `config/babybrains/mj_prompts.json` — Full MidJourney V7 prompt library with syntax notes
   - `config/babybrains/video_validation.json` — Pika/Kling test settings and success criteria

3. **Added 8 CLI commands** (`assets` subcommand):
   - `assets status` — Show workflow phase, decision gates, assets count
   - `assets prompts` — Show MidJourney prompts for current phase
   - `assets validate` — Record video validation result (--tool pika/kling --passed)
   - `assets advance` — Advance to next workflow phase (with gate checks)
   - `assets add-hero` — Add a hero character asset (--file, --url, --score, --notes)
   - `assets select-hero` — Select hero as master reference
   - `assets style-lock` — Lock calibrated style parameters (--sw, --ow)
   - `assets select-tool` — Select video tool for production (--tool pika/kling)

4. **Created test suite** (`tests/babybrains/test_assets.py`):
   - 18 tests covering workflow state, assets, video validation, prompts
   - All tests passing

### Files Created
- `atlas/babybrains/content/assets.py` — Asset management module (450+ lines)
- `config/babybrains/mj_prompts.json` — MidJourney V7 prompt library
- `config/babybrains/video_validation.json` — Video validation settings
- `~/.atlas/.babybrains/assets/workflow_state.json` — Workflow state (auto-created)
- `~/.atlas/.babybrains/assets/01_HERO/` through `08_PHOTO_REFS/` — Asset folder structure
- `tests/babybrains/test_assets.py` — 18 tests

### Files Modified
- `atlas/babybrains/cli.py` — Added assets subcommand with 8 commands and routing

### Test Results
- New tests: 18/18 passing
- Full BB suite: 653+ passed (635 existing + 18 new)

### Key Design Decisions
- **V7 syntax only** — Uses `--oref`/`--ow` (not deprecated `--cref`/`--cw`/`--iw`)
- **TEXT-FIRST approach** — Generate character from text prompts first, photos optional later
- **Decision gates** — Cannot advance phases without meeting criteria (hero selected, video validated, etc.)
- **Fail-fast video validation** — Phase 2 tests in Pika/Kling before creating full asset library
- **File-based state** — `workflow_state.json` persists across sessions

### Usage
```bash
# Check status
python3 -m atlas.babybrains.cli assets status

# See prompts for current phase
python3 -m atlas.babybrains.cli assets prompts

# Advance to next phase
python3 -m atlas.babybrains.cli assets advance

# Add hero asset after generating in MidJourney
python3 -m atlas.babybrains.cli assets add-hero --file ~/.atlas/.babybrains/assets/01_HERO/hero_v1.png --score 8.5

# Select as master reference
python3 -m atlas.babybrains.cli assets select-hero hero_v1

# Record video validation
python3 -m atlas.babybrains.cli assets validate --tool pika --passed

# Lock style parameters after calibration
python3 -m atlas.babybrains.cli assets style-lock --sw 300 --ow 150
```

---

## Previous Session: S2.6-lite TrendService Implementation (Feb 4, 2026 - Session 16)

### What We Did
1. **Implemented S2.6-lite TrendService** — thin wrapper around GrokClient with:
   - **Budget gates**: Daily ($0.50) and monthly ($5.00) limits, SQLite-based cost tracking
   - **Brand safety filtering**: Phrase-level blocking with allowlist exceptions (D6)
   - **Fallback chain**: 12 evergreen topics when Grok unavailable (D4 trigger conditions)
   - **Data mapping**: GrokTrendTopic → TrendResult with full field preservation (D1)
   - **Storage**: Extended bb_trends schema + upsert behavior

2. **Schema migrations** (run_trends_migration):
   - Added 6 columns to bb_trends: description, content_angle, confidence, hashtags, saturation, platform_signals
   - Created bb_grok_costs table for budget tracking

3. **CLI commands** added to `trends` subparser:
   - `trends scan [--focus X] [--max 10]` — scan for trending topics
   - `trends latest [--limit 10]` — show stored trends
   - `trends budget` — show daily/monthly budget status
   - `trends suggest [-n 5]` — get content suggestions

4. **40 tests** across 6 categories (all passing):
   - Budget gate (8 tests): limits, soft warning, post-hoc recording
   - Fallback chain (7 tests): all D4 trigger conditions
   - Brand-safety filter (8 tests): phrases, strict terms, allowlist
   - Data mapping (5 tests): field preservation, enum mapping
   - Storage (4 tests): insert, upsert, get_latest, suggest
   - CLI integration (3 tests) + Scan integration (5 tests)

### Files Created
- `atlas/babybrains/trends/__init__.py` — Package exports
- `atlas/babybrains/trends/engine.py` — TrendService class (420 lines)
- `config/babybrains/fallback_topics.json` — 12 evergreen topics
- `config/babybrains/brand_safety_blocklist.json` — Phrase-level safety rules
- `tests/babybrains/test_trend_service.py` — 40 tests

### Files Modified
- `atlas/babybrains/models.py` — Extended TrendResult with 6 new fields
- `atlas/babybrains/db.py` — Added run_trends_migration, extended add_trend, added upsert_trend, cost tracking functions
- `atlas/babybrains/cli.py` — Added trends subcommand (scan, latest, budget, suggest)
- `tests/babybrains/conftest.py` — Added run_trends_migration to fixture
- `tests/babybrains/test_db.py` — Updated table count from 11 to 12

### Test Results
- TrendService tests: 40/40 passing
- Full BB suite: 635 passed, 7 skipped (API key gated)

### Design Decisions Implemented (from plan audit)
- **D1**: Extended bb_trends schema + TrendResult for Grok fields
- **D2**: SQLite bb_grok_costs table (not JSON file) for budget tracking
- **D3**: Post-hoc cost accounting (record after API call completes)
- **D4**: Fallback trigger conditions (empty+no cost+not cached = API failure)
- **D5**: No additional circuit breaker (GrokClient manages its own)
- **D6**: Phrase-level brand safety with allowlist exceptions

### NOT Implemented (Deferred to Month 2+)
- Temporal decay
- Competitor saturation scoring
- Learning loops
- Cross-source aggregation (YouTube ToS)

---

## Previous Session: AI Detection Audit Implementation (Feb 4, 2026 - Session 15)

### What We Did
1. **Implemented verified audit plan** (3 independent agents verified per P54):
   - **Bug fix (#16)**: Fixed `_is_superlative_exception()` position checking
     - Before: Exception anywhere in text would exempt ALL matches of that word
     - After: Exception must contain the specific match position
     - Example: "Follow best practices. This is the best." — now correctly flags "the best"
   - **Exception patterns (#10)**: Added "at best" and "suboptimal" patterns

2. **Dropped 7 findings** (verified as intentional design differences):
   - LLM-assisted context checking — destroys pipeline performance
   - Generic negation detection — explicit exceptions are more precise
   - Activity missing 7 categories — different content type (YAML vs prose)
   - Unify "imperfect" approach — identical outcomes already
   - Add severity to issue dicts — already has 4-level model via helpers
   - Pre-compile regex — Python caches; premature optimization
   - Line numbers — Content joins text; would need scene numbers (architectural change)

### Files Modified
- `atlas/babybrains/ai_detection.py`:
  - Fixed `_is_superlative_exception()` to verify match position (lines 83-97)
  - Added `\bat\s+best\b` to "best" exceptions (line 56)
  - Added `\bsub-?optimal\b` to "optimal" exceptions (lines 79-81)
- `tests/babybrains/test_ai_detection.py`:
  - Added `test_position_checking_prevents_false_negative()` (lines 161-169)
  - Added `test_best_exception_at_best()` (lines 171-174)
  - Added `test_optimal_exception_suboptimal()` (lines 176-179)
  - Added `test_optimal_exception_sub_optimal()` (lines 181-184)

### Test Results
- AI detection tests: 118/118 passing (114 existing + 4 new)
- Full BB suite: 595 passed, 7 skipped (API key gated)

### Manual Verification
```bash
echo '{"scenes":[{"vo_text":"Best practices are important. This is the best."}], "format_type":"60s"}' | python3 -m atlas.babybrains.content.hooks.qc_script
```
Returns: `SCRIPT_SUPERLATIVE` for "the best" (second instance) ✓

---

## Previous Session: AI Detection Cross-Reference Audit (Feb 4, 2026 - Session 14)

---

## Previous Session: Content Production Research Synthesis (Feb 2, 2026 - Session 13)

### What We Did
1. **Implemented 5-phase content production research plan** (verified by 12 independent agents across 3 rounds):
   - Phase 1: Fixed 5 factual errors in SYNTHESIS.md (CML access, Epidemic Sound pricing, Kling IMAGE 3.0 footnote, URL coverage, strategy table length)
   - Phase 2: Added 54 omissions across 3 tiers (11 CRITICAL, 28 HIGH, 15 MEDIUM) to SYNTHESIS.md
   - Phase 3: Merged 8 new resolved contradiction rows + 2 single-source notes into existing CROSS-FILE CONTRADICTIONS section
   - Phase 3.5: Rewrote Recommended Next Steps with critical constraints; updated Build Priority Roadmap to reference WORKFLOW.md
   - Phase 4: Created WORKFLOW.md (564 lines) — operational playbook with 10 sections + build priority plan
   - Phase 5: Build priority plan embedded in WORKFLOW.md (prerequisites + weeks 1-5+)
2. **Verification**: 2 parallel agents ran 17 checks (all PASS) across both files
3. **File organization**: Copied SYNTHESIS.md and WORKFLOW.md to babybrains-os/docs/research/ (prefixed with `content-production-`)
4. **Updated DOCUMENTATION_UPDATE_GUIDE.md**: Added 4 new doc path entries, updated bb-1b to DONE, added bb-3-research row, updated date

### Files Modified
- `docs/research/bb-content-production/SYNTHESIS.md` — 1284→1525 lines (54 omissions + 5 fixes + 8 contradiction rows + updated recommendations)
- `docs/DOCUMENTATION_UPDATE_GUIDE.md` — Added research doc paths, updated build status table

### Files Created
- `docs/research/bb-content-production/WORKFLOW.md` — 564-line operational playbook (new)

### Files Copied to babybrains-os
- `docs/research/content-production-SYNTHESIS.md` (copy of ATLAS source)
- `docs/research/content-production-WORKFLOW.md` (copy of ATLAS source)

### Key Research Findings (from 19 source files, verified by 12 agents)
- Multi-person motion success rate: **20%** (parent+baby scenes have 80% failure rate)
- CML music licensed for **TikTok only** — separate licensing needed for other platforms
- **5-hashtag limit** on TikTok (Aug 2025) and Instagram (Dec 2025)
- DaVinci Resolve **Studio** required for scripting (free version lost UIManager in v19.1)
- P1/P2/P3 derivative deletion is **manual** (API can only append)
- Pika Standard ($10/mo) has **NO commercial license** — must use Pro
- Burned-in captions required (neither TikTok nor Instagram support SRT sidecar)
- 92% of U.S. mobile viewers watch sound-off; but 88% of TikTok users say sound is essential
- YouTube Shorts monetization: 10M views in 90 days OR 4K watch hours
- Hardware: 8GB VRAM confirmed (CLAUDE.md says 4GB — needs separate update)

---

## Previous Session: S2.BF1 + V0.1 + V0.2 (Feb 1, 2026 - Session 12)

### What We Did
1. **S2.BF1: YouTube Quota Persistence Fix** (`atlas/babybrains/clients/youtube_client.py`):
   - Replaced in-memory `_quota_used_today` counter with file-based persistence at `~/.atlas/youtube_quota.json`
   - File format: `{"date": "2026-02-01", "used": 4500}`
   - Auto-resets when date changes (new UTC day)
   - Reads on init (`_load_quota()`), writes on every `_consume_quota()` call and quota reset (`_save_quota()`)
   - Graceful fallback: corrupted/missing file resets to 0 with warning log
   - `_save_quota()` creates parent dirs and silently handles disk errors
   - New `quota_file` constructor parameter (defaults to `~/.atlas/youtube_quota.json`)
   - 7 new tests in `TestQuotaPersistence` class
2. **V0.1: Grok API Validation** — CONFIRMED WORKING:
   - Initial test: 403 "no credits" → user purchased $5 credit at console.x.ai
   - Re-test: 200 OK, model returned `grok-3` (requested `grok-3-fast`, API resolved to `grok-3`)
   - Response: "OK" in 12 tokens, cost_in_usd_ticks: 435000
   - Pricing: $0.20/1M input, $0.50/1M output, $5/1K search calls
   - Estimated cost per `scan_opportunities()`: ~$0.016-0.027
   - Estimated scans per $5: ~183-304 (depending on search call count)
   - Note: Model name returned as `grok-3` not `grok-3-fast` — may be an alias or model consolidated. Works either way.
3. **V0.2: Anthropic API Validation** — CONFIRMED WORKING:
   - Initial test: 401 invalid key → user generated new key at console.anthropic.com
   - Re-test: 200 OK, model `claude-sonnet-4-20250514`, 12 input + 4 output tokens
   - Comment generator pattern (from `comments.py`) will work with this key

### API Status (All Green)

| API | Status | Notes |
|-----|--------|-------|
| **Grok (GROK_API_KEY)** | WORKING | $5 credit loaded. Model resolves to `grok-3`. |
| **Anthropic (ANTHROPIC_API_KEY)** | WORKING | New key, `claude-sonnet-4-20250514` confirmed. |
| **YouTube (YOUTUBE_API_KEY)** | WORKING | Used in tests, quota persistence now file-based. |

### Files Modified
- `atlas/babybrains/clients/youtube_client.py` — Added `_load_quota()`, `_save_quota()`, `quota_file` param; calls `_save_quota()` from `_consume_quota()` and `_check_quota_reset()`
- `tests/babybrains/test_youtube_client.py` — Added 7 `TestQuotaPersistence` tests; updated client fixture to use `quota_file` param

### Test Results
- YouTube client: 54/54 passing (47 existing + 7 new quota persistence)
- Full BB suite: 362 passed, 7 skipped (API key gated), 0 failures

---

## Previous Session: S2.3 Warming Integration + MCP Tools (Feb 1, 2026 - Session 11)

### What We Did
1. **Integrated WarmingBrowser into WarmingService** (`atlas/babybrains/warming/service.py`):
   - New `run_browser_session(platform)` async method — full pipeline: get pending targets → create WarmingBrowser → run session → log per-action results → update target statuses → log session result/failure
   - Lazy import of WarmingBrowser with `BROWSER_AVAILABLE` flag — graceful handling when patchright not installed
   - Browser `stop()` always called via try/finally (crash-safe cleanup)
   - Each WatchResult mapped back to DB target by index — watch/like/subscribe actions logged with correct `target_id`
   - Target status updated: successful watches → `completed`, errors → `skipped`
2. **Enhanced `bb_warming_status()` MCP tool** with browser session stats:
   - New `get_browser_session_stats(conn, days)` DB helper — returns successful/failed session counts, total session watch time, last session details, last failure reason
   - Stats merged into warming status dashboard under `browser_sessions` key
3. **Added `bb_warming_watch(platform?)` MCP tool** — triggers automated browser warming session via `WarmingService.run_browser_session()`
4. **Enhanced `bb_warming_done(platform, actions)`** — now delegates to `WarmingService.log_done()` which supports both count-based (manual) and detailed action logging with `target_id`, `actual_watch_seconds`, `content_posted`
5. **CLI: `python -m atlas.babybrains.cli warming watch`** — triggers browser session, shows results (videos watched, watch time, likes, subscribes, errors)
6. **CLI: `warming status` enhanced** — now shows browser session stats (successful/failed, watch time, last session, last failure)
7. **Failed session logging** — all failure modes log to DB via `db.log_warming_session()`:
   - Cookie expiry → `session_failure` with reason
   - Circuit breaker trip → `session_failure` with reason
   - Domain violation → `session_failure` with reason
   - Browser crash → `session_failure` with crash message
   - Import error (patchright not installed) → `session_failure`

### Files Modified
- `atlas/babybrains/db.py` — Added `log_warming_session()`, `get_browser_session_stats()`
- `atlas/babybrains/warming/service.py` — Added `run_browser_session()`, enhanced `log_done()` with `actions_detail` parameter, added `BROWSER_AVAILABLE` flag
- `atlas/mcp/server.py` — Enhanced `bb_warming_status()` (browser stats), added `bb_warming_watch()`, refactored `bb_warming_done()` to use WarmingService
- `atlas/babybrains/cli.py` — Added `warming watch` subcommand and routing, enhanced `warming status` with browser session display

### Files Created
- `tests/babybrains/test_warming_integration.py` — 29 tests across 8 test classes

### Test Results
- New tests: 29/29 passing
- Full BB suite: 355 passed, 7 skipped (API key gated), 0 failures

### Key Design Decisions
- **BROWSER_AVAILABLE flag** — lazy import with try/except at module level, not per-call. Tests can patch the flag directly.
- **Session logging uses bb_warming_actions table** — action_type `session_complete` / `session_failure` with target_id=0 for session-level events. No new tables needed.
- **Target-to-WatchResult mapping by index** — WarmingBrowser processes targets in order and appends results in order, so zip by index is safe. Early session termination (limits) means fewer results than targets.
- **log_done() backward compatible** — count-based logging (manual) still works; new `actions_detail` parameter enables rich per-action logging from browser sessions.
- **bb_warming_done MCP refactored** — now delegates to WarmingService.log_done() instead of duplicating logic.

---

## Previous Session: S2.2 WarmingBrowser Class (Feb 1, 2026 - Session 10)

### What We Did
1. **Built `atlas/babybrains/browser/warming_browser.py`** — full WarmingBrowser class:
   - Persistent browser profile per account (`~/.atlas/.browser/<account_id>/`)
   - Uses S2.1 optimal config: system Chrome + `--disable-blink-features=AutomationControlled` + patchright CDP patches
   - `check_login_state()` — navigates to YouTube, checks avatar vs sign-in button, logs WARNING on expired session
   - `watch_video(url, duration_pct)` — humanized watching with random scrolls (15-45s), mouse drift (10-30s), pauses (1-3s every 2-5 min)
   - `like_video()` — finds like button via DOM, checks already-liked state, humanized mouse movement to click
   - `subscribe_channel()` — with daily limit check from engagement rules, humanized click
   - `inter_video_delay()` — gaussian distribution (mean=45s, stddev=15s, clamped 15s-135s)
   - `run_session(targets)` — full session orchestration: login check, video limit (3-7), duration limit (15-45 min), engagement actions per level
   - Circuit breaker (aiobreaker): trips after 3 consecutive failures, 5-min reset
   - Domain allowlist: youtube.com + consent/accounts subdomains only (frozen set)
   - Session log: file-based daily tracking (`session_log.json`), max 2 sessions/day, auto-prunes entries >7 days
   - COMMENT level: watches + likes but NEVER automates comment posting (human only)
2. **Created `atlas/babybrains/browser/__init__.py`** — package with WarmingBrowser, SessionConfig, WatchResult, SessionResult exports
3. **Created `tests/babybrains/test_warming_browser.py`** — 83 tests across 14 test classes:
   - Domain allowlist (12 tests): YouTube allowed, spoofing blocked, non-YouTube rejected
   - Session limits (7 tests): video count, duration, elapsed time tracking
   - Daily session limit (8 tests): first/second/third session, new day reset, corrupted log
   - Session log persistence (4 tests): save/load, missing file, corrupted, non-dict
   - Gaussian delay (3 tests): bounds, minimum, distribution center
   - Browser profile (3 tests): path construction, per-account isolation, initial state
   - Login state (5 tests): logged in, logged out, ambiguous, not started, nav error
   - Watch video (4 tests): success, non-YouTube rejection, counter increment, not started
   - Circuit breaker (2 tests): trips after 3 failures, successful ops don't trip
   - Like video (4 tests): success, already liked, button not found, not started
   - Subscribe channel (4 tests): success, already subscribed, not found, not started
   - Run session (6 tests): video limit, expired login abort, daily limit abort, like on LIKE level, subscribe on SUBSCRIBE level, comments never automated
   - Humanization parameters (5 tests): scroll interval, mouse drift, pause duration, pause frequency, inter-video delay config
   - Result dataclasses (7 tests): WatchResult success/failure, SessionResult properties
   - Browser lifecycle (3 tests): stop without start, records session, no record on zero videos
   - Allowed domains constant (6 tests): required domains present, blocked domains absent, immutable

### Files Created
- `atlas/babybrains/browser/__init__.py` — Browser package with exports
- `atlas/babybrains/browser/warming_browser.py` — WarmingBrowser class (520 lines)
- `tests/babybrains/test_warming_browser.py` — 83 unit tests

### Key Design Decisions
- **Patchright import is lazy** (inside `start()`) — module imports without patchright installed, tests mock at the right level
- **Domain allowlist uses `frozenset`** with exact match only — no subdomain wildcarding to prevent spoofing
- **Session log is file-based** (not DB) — WarmingBrowser operates independently; DB logging happens at WarmingService level in S2.3
- **Circuit breaker is per-instance** — each WarmingBrowser gets its own breaker, separate from client-level breakers
- **No Google login automation** — `check_login_state()` only verifies; manual login is human-only
- **No comment automation** — COMMENT engagement level gets watch+like but never posts

### Test Results
- New tests: 83/83 passing
- Full BB suite: 326 passed, 7 skipped (API key gated), 0 failures

---

## Previous Session: S2.1 Patchright Stealth Spike Test (Feb 1, 2026 - Session 9)

### What We Did
1. **Installed Patchright + humanization-playwright** — browser stealth packages for BB warming
2. **Installed Google Chrome** on WSL2 (system Chrome, not bundled Chromium) — better fingerprint than Chromium
3. **Updated pyproject.toml** — added `[browser]` optional dependency group
4. **Created `scripts/stealth_spike_test.py`** — automated spike test with 6 checks
5. **Iterative stealth testing** — tested 5 configurations to find optimal setup:
   - Bundled Chromium + `--disable-blink-features=AutomationControlled`: 7/37 flags
   - System Chrome, no flags: 2/37 flags (webdriver=true)
   - System Chrome + `--disable-blink-features=AutomationControlled`: **1/57 flags** (best)
   - JS init script injection: counterproductive (sannysoft detects overrides)
   - No init scripts: cleanest results

### Spike Test Results (CONDITIONAL PASS)
| Check | Result | Detail |
|-------|--------|--------|
| Chrome launch (WSLg) | PASS | Headed Chrome opens via WSLg on WSL2 |
| navigator.webdriver | PASS | webdriver=False (via --disable-blink-features) |
| bot.sannysoft.com | 1/57 flags | Only WebGL Renderer flagged (SwiftShader = WSL2 software GPU) |
| creepjs.com | PASS | Page loads, no flagging detected |
| youtube.com | PASS | Full page with search + logo |
| Profile persistence | PASS | 51.2 MB profile persists between runs |

### Key Findings
- **Patchright patches CDP Runtime.enable** (the #1 YouTube detection vector in 2025-2026)
- **`--disable-blink-features=AutomationControlled`** hides navigator.webdriver at Blink level
- **System Chrome is better than bundled Chromium** for fingerprint consistency (57 sannysoft checks vs 37, and fewer flags)
- **JS init script injection is counterproductive** — sannysoft detects property overrides
- **WebGL Renderer (SwiftShader)** is the only remaining flag — WSL2 uses software rendering, no real GPU. Desktop machine with real GPU would eliminate this
- **Profile persistence works** — cookies, history, and session data survive across runs

### Recommended Configuration for S2.2
```python
context = await p.chromium.launch_persistent_context(
    user_data_dir=str(profile_dir),
    channel="chrome",
    headless=False,
    no_viewport=True,
    args=["--disable-blink-features=AutomationControlled"],
)
```

### WebGL Flag Assessment
The WebGL Renderer flag shows SwiftShader (software GPU in WSL2). For YouTube warming:
- YouTube primarily detects via CDP leaks and behavioral patterns, not WebGL fingerprint
- SwiftShader is used by many lightweight machines and VMs — not an automatic ban trigger
- Desktop machine (RTX 3050 Ti) would eliminate this flag entirely
- **Recommendation:** Proceed with WSL2. Monitor for issues. Fall back to desktop if needed.

### Files Created
- `scripts/stealth_spike_test.py` — Automated stealth spike test (6 checks, domain allowlist)

### Files Modified
- `pyproject.toml` — Added `[browser]` optional deps: patchright, humanization-playwright

### Dependencies Installed
- `patchright==1.58.0` — Playwright fork with CDP stealth patches
- `humanization-playwright==0.1.2` — Bezier curves, variable typing, humanized scroll
- `google-chrome-stable==144.0.7559.109` — System Chrome (via apt)
- System libraries: libnspr4, libnss3, libatk, libcups, libdrm, libxkbcommon, libgbm, etc.

### Test Results
- BB suite: 243 passed, 7 skipped (API key gated), 0 failures (no regressions)

---

## Previous Session: S0.1 Account Population (Feb 1, 2026 - Session 8)

### What We Did
1. **S0.1: Populated bb_accounts table** with 4 Baby Brains social accounts:
   - YouTube: `@babybrains-app` (status=incubating, incubation_end_date=today+7)
   - TikTok: `babybrains.app` (status=warming)
   - Instagram: `babybrains.app` (status=warming)
   - Facebook: `Baby Brains` (status=warming)
2. **Added `accounts populate` CLI command** — idempotent via upsert_account
3. **Fixed get_accounts()** to include `incubation_end_date` in BBAccount construction
4. **Fixed get_bb_status()** to include `incubation_end_date` in status dashboard
5. **Fixed status display** — removed erroneous `@` prefix on handles that already have it
6. **11 new tests** covering: 4 accounts inserted, correct handles/platforms/statuses, YouTube incubation date = today+7, idempotency (no duplicates), status dashboard shows all 4

### Files Created
- `tests/babybrains/test_populate_accounts.py` — 11 tests for S0.1

### Files Modified
- `atlas/babybrains/db.py` — Added `populate_accounts()`, fixed `get_accounts()` to include `incubation_end_date`, added `incubation_end_date` to `get_bb_status()`
- `atlas/babybrains/cli.py` — Added `accounts populate` subcommand, fixed handle display in status

### Test Results
- BB suite: 243 passed, 7 skipped (API key gated), 0 failures
- New tests: 11/11 passing

---

## Previous Session: 21-Day Fix + Agent Quality Framework (Feb 1, 2026 - Session 7)

### What We Did
1. **Fixed 21-day → 7-day propagation bug** — 15 instances across 9 files in 2 repos
   - ATLAS repo (5 fixes): schema.sql, platforms.json, cross_repo_paths.json, DECISIONS.md
   - babybrains-os repo (9 fixes): SPRINT_PLAN_V3.md (3), BB_AUTOMATION_PLAN_V2.md (2), SPRINT_TASKS.md (1), LAUNCH-STRATEGY-JAN2026.md (3)
   - Verification grep confirms zero remaining instances in operational files
2. **Built 5-layer Agent Quality Framework** to prevent propagation bugs going forward:
   - Layer 1 (SessionStart): Injects critical-state.md into every session via JSON additionalContext
   - Layer 2 (PostToolUse): Warns when source-of-truth file edited — lists reference files
   - Layer 3 (Stop): Deterministic grep blocks agent from finishing if canonical values inconsistent
   - Layer 4 (Stop): Independent agent critic reviews git diff HEAD
   - Layer 5 (PreCompact): Saves critical state before context compaction
3. **Created canonical_values.json** registry with 3 entries (incubation_duration, grok_model, intelligence_engine)
4. **All hooks tested** — inject-context outputs valid JSON, propagation warning fires correctly, stop check blocks on inconsistency, stop_hook_active guard prevents infinite loop

### Files Created
```
.claude/settings.json                    — Hook configuration (5 layers)
.claude/critical-state.md                — Compact critical state (<40 lines)
.claude/hooks/inject-context.py          — Layer 1: SessionStart injection
.claude/hooks/check-edit-propagation.py  — Layer 2: PostToolUse warning
.claude/hooks/check-propagation.py       — Layer 3: Stop-time consistency check
.claude/hooks/save-state.sh              — Layer 5: PreCompact state save
config/canonical_values.json             — Cross-file value registry
```

### Files Modified
- `atlas/babybrains/schema.sql` — 21-day → 7-day comment
- `config/babybrains/platforms.json` — duration_days 21→7, rule text
- `config/babybrains/cross_repo_paths.json` — summary text
- `docs/DECISIONS.md` — D105 rationale
- `[babybrains-os] docs/automation/SPRINT_PLAN_V3.md` — 3 instances
- `[babybrains-os] docs/automation/BB_AUTOMATION_PLAN_V2.md` — 2 instances
- `[babybrains-os] docs/automation/SPRINT_TASKS.md` — 1 instance
- `[babybrains-os] docs/automation/LAUNCH-STRATEGY-JAN2026.md` — 3 instances

### Test Results
- BB suite: 232 passed, 7 skipped (API key gated), 0 failures

---

## Previous Session: Sprint Plan V3 + Audit (Feb 1, 2026 - Session 6)

### What We Did
1. **Comprehensive next-phase analysis** — cross-referenced 55 KB patterns against build plan
2. **Round 1 audit (3 Opus agents):** Inversion Test, Adversarial Self-Check, Junior Analyst Challenge
   - FINDING: Plan was sequenced backwards — trend engine before warming is wrong
   - FINDING: A61 Critic Agent is premature (human IS the critic at <50 pieces)
   - FINDING: 23-hour decay half-life is hypothetical, not measured
   - FINDING: 92.1% opposing incentives figure is from finance domain, not content
3. **Wrote SPRINT_PLAN_V3.md** (716 lines) at `babybrains-os/docs/automation/`
4. **Round 2 audit (1 Opus agent):** Found 3 CRITICAL, 12 HIGH, 13 MEDIUM issues
5. **Incorporated all V4 findings** (24 targeted edits):
   - Cookie expiry monitoring (check_login_state)
   - YouTube ToS cross-source risk mitigation
   - requirements.txt update in S2.1
   - V0.2 Anthropic API validation task
   - Sprint 2 split into 2A + 2B
   - S2.1 debugging buffer (3-day abort)
   - S3.1/S3.3/S3.5 specs expanded
   - Risk register expanded to 15 entries
   - Agent context boundaries corrected
6. **Fixed Trend Agent context inconsistency** — removed youtube_client.py from MUST READ (YouTube not used for trend scoring per ToS fix)

### Key Decision: New Build Order
V2: S2.6 → S0.1 → A61 → S2.1-S2.3 → S3.x (WRONG — backwards)
V3: S0.1 → S2.1 → S2.2 → S2.3 → V0.1/V0.2 → M1 → S2.6-lite → A22 → S3.1-S3.2 → PUBLISH

### Sprint Plan Location
`/home/squiz/code/babybrains-os/docs/automation/SPRINT_PLAN_V3.md`

---

## Previous Session: S2.4 YouTube + S2.5 Grok API Clients + Audit (Jan 31, 2026 - Sessions 3-5)

### What We Did
1. **S2.4: YouTube Data API Client** — ToS-compliant video discovery (no cross-channel aggregation, no derived metrics, 30-day retention compliance)
2. **S2.5: Grok API Client** — Primary intelligence engine with Live Search (x_search + web_search tools), passive context system prompt (P14), Pydantic validation, cost tracking
3. **Circuit breaker** (aiobreaker) + **retry** (tenacity) on both clients
4. **Cache with confidence degradation** — stale-while-revalidate pattern (1.0 fresh → 0.3 minimum)
5. **Grok→YouTube cross-pollination** — `suggest_search_queries()` converts X.com trends into YouTube search terms
6. **Fixed warming_schedule.json** incubation from 21 → 7 days (research-backed)
7. **Updated pyproject.toml** — added aiobreaker + tenacity deps, pytest-asyncio to dev
8. **Independent 3-agent audit** (Code Reviewer, Security Reviewer, Junior Analyst) per VERIFICATION_PROMPTS.md
9. **Audit fixes applied** (Session 4):
   - Added `_safe_int()` for non-numeric YouTube API stats (was NameError)
   - Fixed 403 handler API key leak (removed `resp.text`, now uses error reason field)
   - Added `YouTubeRateLimitError` + `GrokRateLimitError` + `GrokServiceUnavailableError`
   - 429/503 now retried by tenacity (were only retrying connection errors)
   - Extracted `_strip_markdown_fences()` + `_extract_content()` helpers (DRY, was 3x duplication)
   - Fixed empty `choices` IndexError in `suggest_search_queries`/`deep_dive`
   - Wrapped `_set_cached()` in try/except for disk errors (both clients)
   - Fixed docstring/DEFAULT_MODEL mismatch (aligned to grok-3-fast)
   - Added 35 new tests covering all audit-identified gaps
10. **Integration tests** (Session 5):
   - 7 real YouTube API tests (search, details, caching, quota, health — skipped without API key)
   - 5 real circuit breaker + retry tests using httpx.MockTransport (no mocks on aiobreaker/tenacity)
   - 20 adversarial Grok parsing tests (garbage, truncated, HTML, Unicode, emoji, flat list JSON)
   - 2 end-to-end Grok flow tests with MockTransport
   - Found + fixed REAL production bug: flat list JSON crash in `_parse_trend_response`
   - Fixed environment isolation: monkeypatch.delenv for no-key tests
11. **Documentation updates** (Session 5):
   - Updated CLAUDE.md, TECHNICAL_STATUS.md, DOCUMENTATION_UPDATE_GUIDE.md

### Files Created
- `atlas/babybrains/clients/youtube_client.py` — YouTubeVideo, YouTubeDataClient, CacheEntry, quota tracking
- `atlas/babybrains/clients/grok_client.py` — GrokTrendTopic, GrokTrendResult (Pydantic), GrokClient, cost tracking
- `tests/babybrains/test_youtube_client.py` — 47 tests (30 + 17 audit)
- `tests/babybrains/test_grok_client.py` — 59 tests (41 + 18 audit)
- `tests/babybrains/test_integration.py` — 35 tests (real API + adversarial + e2e)

### Files Modified
- `atlas/babybrains/clients/__init__.py` — Added all exports incl. new error classes
- `config/babybrains/warming_schedule.json` — Incubation 21→7 days
- `pyproject.toml` — Added aiobreaker, tenacity, pytest-asyncio

### Key Architecture Decisions
- **YouTube is NOT an intelligence engine** — just simple video discovery (ToS compliance)
- **Grok is the primary intelligence engine** — x_search/web_search tools provide real-time X.com data
- **Model: grok-3-fast** (OpenAI-compatible API at api.x.ai/v1)
- **aiobreaker.call_async()** for circuit breaker (not context manager)
- **Pydantic BaseModel** for Grok response validation (catches schema inconsistencies)
- **Independent failure** — YouTube and Grok fail independently; pipeline handles partial data

### Test Results (Post-Audit)
- YouTube client: 47/47 passing
- Grok client: 59/59 passing
- Full BB suite: 204/204 passing (98 existing + 106 new)

---

## Previous Session: BB Week 2 Audit + Stealth Research (Jan 31, 2026 - Session 2)

### What We Did
1. **Audited BB Week 2 preparation checklist** against 22-source knowledge base
2. **Cross-referenced comment pipeline** against P54 (self-review degrades quality) -- found regex-only quality gate is acceptable because human-in-the-loop acts as independent critic
3. **Identified 3 missing items** from original checklist: account DB population, WSLg fallback plan, Playwright anti-detection
4. **Researched browser stealth** for Playwright: playwright-stealth, camoufox, patchright, rebrowser-patches
5. **Updated plan docs** with KB audit findings and stealth requirements
6. **Human story deferred** -- comment generator handles gracefully, fill later

### Key Decisions
- **Account warming reset:** Treat pipeline start as Day 1 (accounts not consistently warmed)
- **Human story deferred:** 0% personal angle is fine for now
- **Stealth is mandatory:** YouTube detects at infrastructure level, not content level
- **P54 mitigated by human review:** No independent critic needed yet at 5-10 comments/day

### Files Modified This Session
- `docs/SPRINT_TASKS.md` -- Added S0.1 (populate accounts), audit notes, stealth requirements to S2.1/S2.2
- `docs/BB_AUTOMATION_PLAN_V2.md` -- Added KB audit findings table, stealth requirements to D102 pipeline
- `docs/BROWSER_STEALTH_RESEARCH.md` -- NEW: Anti-detection research findings
- `docs/DOCUMENTATION_UPDATE_GUIDE.md` -- Stats updated (from Session 1)
- `.claude/handoff.md` -- This file

---

## Previous Session: Knowledge Base Source Intake (Jan 31, 2026 - Session 1)

### What We Did
Ingested 5 new sources into the overhauled knowledge base system:

| Source | Type | Items | Patterns | Cred | Key Contribution |
|--------|------|:-----:|----------|:----:|------------------|
| **S18** Claude Cowork Plugins | Product launch + OSS | 14 | P50, P51 (new) | 8 | Plugin architecture (skills+commands+connectors+sub-agents), MCP Tool Search (85% token savings) |
| **S19** Agentic Image Gen | Practitioner + Product | 12 | P52 (new) | 7 | Nano Banana + self-improving loop + Google Agentic Vision. BB carousel pipeline |
| **S20** Team of Rivals + Swarm | Academic + Scientific | 16 | P53, P54, P55 (new) | 9 | **Highest value source.** Opposing incentives (92.1% vs 60%), self-review degrades quality, quorum sensing |
| **S21** THE SEED Loop | Social media | 6 | None new | 3 | Low credibility. Confirms existing patterns only. "Accumulate WHAT, empty HOW" heuristic |
| **S22** OpenClaw Agent Canvas | Open-source tool | 12 | None new | 8 | Validates 8 patterns in one system. 13 messaging adapters, Docker sandboxes, visual agent dashboard |

### New Patterns (6 total: P50-P55)

| # | Pattern | Signal | Impact |
|---|---------|--------|--------|
| P50 | Plugin = Skills + Commands + Connectors + Sub-Agents | 8.2 | Anthropic canonical. Our `.claude/` is ~70% aligned |
| P51 | Dynamic Tool Loading (MCP Tool Search) | 7.9 | 85% token reduction. Critical as we add more MCP tools |
| P52 | Agentic Vision (Think→Act→Observe) | 8.1 | Self-improving image loops. BB carousel production |
| P53 | Opposing Incentives Create Coherence | 8.8 | Agents constrain agents. 92.1% vs 60% single-agent |
| P54 | **Self-Review Degrades Quality** | **9.1** | **Session's highest signal.** Self-verification went wrong 60% of time |
| P55 | Quorum Sensing > Consensus | 8.3 | Threshold agreement faster AND more accurate than unanimity |

### Highest-Priority New Actions

| ID | Action | Priority |
|----|--------|----------|
| **A61** | **Independent critic agent with VETO authority** | **P0** |
| A53 | Restructure `.claude/` to plugin architecture | P1 |
| A54 | Evaluate MCP Tool Search | P1 |
| A57 | Evaluate Nano Banana Pro for BB carousels | P1 |
| A62 | Quorum-based voting for multi-agent decisions | P1 |
| A63 | Swiss Cheese error layers in ATLAS | P1 |
| A65 | Study OpenClaw for Telegram bridge | P1 |

### Convergence Promotions
- **P6** (Brain+Hands) → Tier 1 (4 sources)
- **P14** (Passive Context) → Tier 1 (4 sources)
- **P38** (Cascading Failures) → Tier 2 (3 sources)
- **P19** (Sandboxed Extensibility) → Tier 2 (3 sources)
- **P40** (Single-Trigger Delegation) → Tier 2 (3 sources)

### KB Stats After Session
- **22 sources** (S1-S22), up from 17
- **55 patterns** (P1-P55), up from 49
- **67 actions** (A1-A67), up from 52
- 3 JSON indexes current
- CHANGELOG at v1.3

---

## Previous Session: Baby Brains Week 1 BUILD COMPLETE

### What We Built This Session (S1.1-S1.8)
1. **S1.1** Schema (10 tables) + models (dataclasses) + db.py (query helpers) -- 24 tests
2. **S1.2** Voice spec loader (parses 1712-line BabyBrains-Writer.md) + human story profile -- 13 tests
3. **S1.3** Cross-repo search (static path map across 5 repos) -- 11 tests
4. **S1.4** Platform configs (YouTube/IG/TikTok/FB rules from Dec 2025 research) -- 7 JSON configs
5. **S1.5** MCP tools (bb_status, bb_find_doc, bb_warming_daily, bb_warming_done, bb_warming_status) + CLI
6. **S1.6** Transcript fetcher (youtube-transcript-api) -- 12 tests
7. **S1.7** Comment generator (Sonnet API + voice spec + quality gate) -- 19 tests
8. **S1.8** WarmingService (orchestrates daily pipeline) + targets module -- 19 tests

### Files Created
```
atlas/babybrains/
├── __init__.py, __main__.py
├── schema.sql (10 tables)
├── models.py (10 dataclasses)
├── db.py (25+ query helpers)
├── voice_spec.py (section extraction)
├── cross_repo.py (5-repo search)
├── cli.py (status, find-doc, warming commands)
├── warming/
│   ├── __init__.py
│   ├── service.py (WarmingService orchestrator)
│   ├── targets.py (target generation + scoring)
│   ├── comments.py (Sonnet API + quality gate)
│   └── transcript.py (YouTube transcript fetch)
├── trends/__init__.py
├── content/__init__.py
└── clients/__init__.py

config/babybrains/
├── platforms.json (4 platform algo rules)
├── warming_schedule.json (phases, search queries)
├── warming_engagement_rules.json (watch/like/subscribe thresholds)
├── audience_segments.json (5 personas)
├── competitors.json (AU + international)
├── cross_repo_paths.json (16 topic mappings)
└── human_story.json (PLACEHOLDER -- needs user completion)

tests/babybrains/
├── conftest.py, __init__.py
├── test_db.py (24 tests)
├── test_voice_spec.py (13 tests)
├── test_cross_repo.py (11 tests)
├── test_transcript.py (12 tests)
├── test_comments.py (19 tests)
└── test_warming_service.py (19 tests)
```

### Modified Files
- `atlas/mcp/server.py` -- Added 5 BB MCP tools (bb_status, bb_find_doc, bb_warming_daily, bb_warming_done, bb_warming_status)

### Key Documents
- `[babybrains-os] docs/automation/BB_AUTOMATION_PLAN_V2.md` -- Full architecture plan (D100-D106)
- `[babybrains-os] docs/automation/SPRINT_TASKS.md` -- 21 sprint tasks with prerequisites, acceptance criteria, git workflow
- `[babybrains-os] docs/automation/LAUNCH-STRATEGY-JAN2026.md` -- Launch strategy (Jan 16, partially executed)
- `[babybrains-os] docs/automation/BROWSER_STEALTH_RESEARCH.md` -- Anti-detection research

### Knowledge Base (Overhauled Jan 31, 2026)

**Location:** `knowledge-base/` (top-level directory)

The research index was restructured from a monolithic 2,546-line file into a hub-and-spoke architecture:

```
knowledge-base/
├── README.md              # Dashboard (always read first)
├── PATTERNS.md            # 49 patterns indexed with convergence
├── SYNTHESIS.md           # 8 themes, contradictions, build order
├── ACTIONS.md             # 52 action items with IDs, status, deps
├── CHANGELOG.md           # Version history
├── indexes/
│   ├── SIGNAL_HEATMAP.md  # Top items by composite score
│   ├── by_category.json   # Tag → items
│   ├── by_source.json     # Source → metadata
│   └── by_tool.json       # Tool → references
├── sources/               # 17 individual source files (S01-S17)
├── _templates/            # Intake template for new sources
├── synthesis/             # Synthesis working files
└── archive/               # Original monolithic file preserved
```

**Session bootstrap:** Read `knowledge-base/README.md` first — it has source index, top patterns, open actions, and navigation.

**Adding sources:** Copy `_templates/source_template.md`, fill in, run `python scripts/kb_rebuild_indexes.py`

**Key stats:** 17 sources, 284 items, 49 patterns, 8 themes, 52 action items
**Signal scoring:** `(Relevance×0.30) + (Confidence×0.25) + (Credibility×0.25) + (Convergence×0.20)`

### Top Patterns (49 total, most important listed)

1. **Async delegation is THE use case** (S1, S3, S8, S14) — Consensus
2. **Hybrid model routing is consensus** (S1, S2, S3, S4, S14, S16) — 6 sources
3. **Passive context >> active retrieval** (S6, S14, S15) — 100% vs 53%
4. **Data sovereignty as strategy** (S3, S6, S11)
5. **Security before features** (S13)
6. **Brain + Hands = ReWOO pattern** (S2, S14) — 80% token savings
7. **Agents optimize for capability, humans must optimize for safety** (S8)
8. **MCP is the universal protocol** (S7)
9. **Hybrid planning is the answer** (S14) — ReWOO + ReAct + Plan-and-Execute
10. **Flat memory → structured memory = 46% improvement** (S14)
11. **Fewer tool calls > frequent calls** (S14) — validates 0-token architecture
12. **ATLAS architecture is academically validated** (S14)
13. **Forgetting is the feature** (S17) — FSRS-6 decay prevents context bloat
14. **Dual strength memory** (S17) — retrievability vs stability as independent dimensions
15. **Prediction error gating** (S17) — detect conflicts before storing
16. **Circuit breaker + fallback chains** (S16) — production resilience
17. **Privacy as routing constraint** (S16) — standard/sensitive/strict tiers

---

## Baby Brains Execution Status (Jan 30, 2026)

### What's Done
- Social media accounts CREATED (YouTube, Instagram, TikTok, Facebook)
- BabyBrains-Writer voice spec COMPLETE (95KB)
- Knowledge Graph 40-50% complete (125+ activities)
- Agent Knowledge Base research COMPLETE (17 sources)

### What's NOT Done (Priority Order)
1. **Account warming** — accounts created but NOT consistently warmed
2. **Content pipeline** — not established
3. **Content strategy** — no gameplan for what goes out or when
4. **Website** — not live, hero video still blocking
5. **Long-form articles** — none started, needed for SEO/GEO

### Planned Agent Architecture

```
ATLAS Orchestrator (shared infrastructure)
├── Personal Agent (health, development, life admin)
│   ├── Health sub-agent (Garmin, workouts, supplements)
│   ├── Memory sub-agent (thoughts, capture, digest)
│   └── Life admin sub-agent (calendar, email — Phase 5)
│
└── Baby Brains Agent (business, content, strategy)
    ├── Content sub-agent (activities, blog, copy)
    ├── Marketing sub-agent (social, SEO/GEO, analytics)
    ├── Strategy sub-agent (market research, expansion)
    └── Customer-facing agent (website/app — future)
```

### Baby Brains Agent — Immediate Build Priorities

| Priority | What to Build | Why |
|----------|--------------|-----|
| 1 | **Account warming automation** | Daily grind: watch videos, engage, leave BB-voice comments |
| 2 | **Content strategy engine** | Trending topic research → content briefs → production schedule |
| 3 | **Content production pipeline** | Script → video → captions → platform-specific export |
| 4 | **Website launch** | Unblock with placeholder hero, get articles live |
| 5 | **Article/SEO/GEO pipeline** | Long-form content for web + LLM citation |

---

## How to Resume

```
Read these files:
1. .claude/handoff.md (this file)
2. /home/squiz/code/babybrains-os/docs/automation/SPRINT_PLAN_V3.md (AUTHORITATIVE — find next PENDING task)
3. /home/squiz/code/babybrains-os/docs/automation/BROWSER_STEALTH_RESEARCH.md (if working on S2.1/S2.2)
4. knowledge-base/README.md (research dashboard — sources, patterns, actions)

NOTE: SPRINT_PLAN_V3.md supersedes SPRINT_TASKS.md for Week 2+ tasks.
      BB docs live in babybrains-os repo. ATLAS docs/ stubs point to new locations.

Sprint 1 task order:
1. ~~S0.1: Populate bb_accounts table~~ DONE (Session 8)
2. ~~S2.1: Patchright stealth spike test~~ CONDITIONAL PASS (Session 9) — WebGL only flag
3. ~~S2.2: WarmingBrowser class~~ DONE (Session 10) — 83 tests, full stealth+humanization
4. ~~S2.3: Warming integration + MCP tools~~ DONE (Session 11) — 29 tests, full pipeline
5. ~~S2.BF1: YouTube quota persistence fix~~ DONE (Session 12) — 7 new tests, file-based at ~/.atlas/youtube_quota.json
6. ~~V0.1: Validate Grok credit + model~~ DONE (Session 12) — Key valid but NO CREDITS (need purchase at console.x.ai)
7. ~~V0.2: Validate Anthropic/Sonnet API access~~ DONE (Session 12) — Key INVALID 401 (need new key from console.anthropic.com)
8. M1: Produce 3-5 pieces of content MANUALLY

Key insights (from 4-round audit):
- Browser stealth is mandatory. See BROWSER_STEALTH_RESEARCH.md.
- YouTube ToS prohibits cross-channel aggregation. Grok is the intelligence engine.
- Human IS the critic for first 50 pieces (P54 mitigated by human review).
- A61 Critic Agent and S2.6-full are DEFERRED to Month 2+ (data-driven triggers).
- S2.6-lite (thin trend wrapper) is in Sprint 2A, NOT Sprint 1.
```

### User Manual Tasks (Before Week 2 Build)
1. Get YouTube API key (console.cloud.google.com → YouTube Data API v3, free)
2. Get Grok API key (console.x.ai, $5 free credit)
3. Git pull on desktop machine
4. Copy .env to desktop (add new API keys)
5. `pip install -r requirements.txt` on desktop

### Git Sync Strategy
- All code lives in git. Push from laptop, pull on desktop.
- `.env` is gitignored — must be manually copied/recreated on each machine.
- No local-only state except `.env` and `atlas.db` (DB is recreated from schema on first run).

---

## Previous Session Context (Preserved)

### ATLAS 3.0 Vision
24/7 AI partner: health management, Baby Brains workforce, life admin, multi-platform, self-improving.

### Implementation Phases
| Phase | Description |
|-------|-------------|
| 0 | Desktop security hardening (from S13) |
| 1 | Telegram bridge |
| 2 | Daemon mode + Ralph loop |
| 3 | Model router (informed by S4, S16) |
| 4 | Self-improvement layer (informed by S14, S17) |
| 5 | Life admin (email, calendar, browser) |

### ATLAS Advantages (Don't Lose)
- Voice-first <1.8s latency
- 0-token intent matching (95%+ local) — validated by S6, S14 as optimal
- Traffic Light + GATE system
- Baby Brains quality pipeline
- Ethical gamification

### User Context
**Goal:** Build AI system as life assistant AND business partner for Baby Brains.
**Stakes:** Better life for family. Personal AI assistant = critical path.
**Baby Brains:** Evidence-based Montessori parenting platform (175+ activities, pre-launch).
**New Desktop Machine:** Available for 24/7 agent deployment.
**Separation:** Personal health/development SEPARATE from Baby Brains business agent.

### Key Research Findings for Architecture
- **Memory:** FSRS-6 decay + dual strength + prediction error gating (S17 Vestige)
- **Planning:** Hybrid ReWOO + ReAct + Plan-and-Execute (S14, already implemented)
- **Security:** Privacy tiers + circuit breakers + fallback chains (S16 BrainPro)
- **Multi-agent:** One orchestrator + specialized sub-agents (S14 five generic roles)
- **Development:** Parallel worktrees + single-trigger commands (S15)
- **Tools to evaluate:** Vestige, LobeHub, Grok API, Tailscale

### Qwen3-TTS Voice Cloning (Jan 26)
- Jeremy Irons voice working
- Config: `config/voice/qwen_tts_voices.json`
- Module: `atlas/voice/tts_qwen.py`

---

*Session updated: February 10, 2026 (Session 32 — Oref refinement, skin warmth is final blocker)*
*Knowledge base: 22 sources, 338 items, 55 patterns, 67 actions*
*BB tests: 660 passing, 7 skipped (API key gated)*
*Sprint Plan: babybrains-os/docs/automation/SPRINT_PLAN_V3.md (authoritative)*
*Phase A+B+C+C.5: COMPLETE*
*Phase D: NEARLY COMPLETE — Clay texture, eyes, outfit, background all solved. Skin warmth is final issue. User selecting from candidates.*
*Architecture: oref (baby+clay clothing) + sref (clay texture) + image prompts (catalogue→clay) + DaVinci post*
*Key files: TESTING_PIPELINE_PHASE_D.md, CHARACTER_GLOW_GUIDE.md, bb-illustrative/ (images reorganised, test images in test/ subfolder)*
*Tools used: MidJourney V7, Gemini Nano Banana (image editing), Photopea (colour grading)*
