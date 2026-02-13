# ATLAS Verification Prompts Reference

**Purpose:** Prompt patterns agents should use to verify their own work.

---

## 1. The "Wait" Pattern (89.3% Blind Spot Reduction)

From Anthropic introspection research. Use before self-correction:

```
Wait. Before evaluating, pause and consider:
- What assumptions did I make?
- Where might I be wrong?
- What would I tell someone else who gave this answer?

Now evaluate and correct if needed:
```

**Code:** `from atlas.orchestrator.confidence_router import apply_wait_pattern`

---

## 2. Adversarial Self-Check

After generating content, ask yourself:

```
Acting as a skeptical reviewer, identify:
1. Claims that lack evidence
2. Assumptions stated as facts
3. Edge cases not handled
4. Security vulnerabilities introduced
5. Breaking changes to existing functionality
```

---

## 3. Junior Analyst Challenge

For critical outputs, spawn a verification sub-agent:

```
You are a junior analyst at McKinsey. Your job is to find problems.

Review this output and identify:
- Logical inconsistencies
- Missing error handling
- Untested assumptions
- Potential failures under edge cases

Be thorough. Your reputation depends on catching issues.
```

---

## 4. Confidence Extraction

When uncertain, explicitly state confidence:

```
Before answering, rate your confidence:
- HIGH (>80%): I have direct knowledge/evidence
- MEDIUM (50-80%): Reasonable inference but not certain
- LOW (<50%): Speculating or unsure

State your confidence level, then answer.
```

---

## 5. Fact-Check Prompt

For factual claims:

```
For each factual claim in my response:
1. Is this from my training data or am I inferring?
2. Could this be outdated?
3. Is there a primary source I should cite?
4. Am I conflating similar concepts?
```

---

## 6. Code Review Self-Check

After writing code:

```
Review this code for:
- [ ] Unhandled exceptions (bare except?)
- [ ] Missing input validation
- [ ] Security issues (injection, path traversal)
- [ ] Race conditions
- [ ] Resource leaks
- [ ] Breaking API changes
- [ ] Missing logging
```

---

## 7. Documentation Completeness

After documenting:

```
Check documentation for:
- [ ] Usage examples included?
- [ ] All parameters documented?
- [ ] Return values specified?
- [ ] Error conditions listed?
- [ ] Dependencies mentioned?
```

---

## 8. The Inversion Test

For recommendations/decisions:

```
What would make this recommendation WRONG?
- Under what conditions would this fail?
- What's the strongest argument against this?
- What am I not considering?
```

---

## Quick Reference Table

| Situation | Use This Pattern |
|-----------|------------------|
| Self-correcting | "Wait" pattern |
| Critical output | Junior Analyst Challenge |
| Factual claims | Fact-Check Prompt |
| Code changes | Code Review Self-Check |
| Uncertain | Confidence Extraction |
| Decisions | Inversion Test |
| Workout progression | Progressive Overload Verification |
| Workout data | Data Persistence Verification |

---

## Post-Phase Verification Guide

**After an agent completes a phase, run verification based on phase type:**

### Code/Script Phases (e.g., QC Hook, Pipeline)
Run these 3:
1. **Code Review Self-Check** - Find bugs, security issues
2. **Inversion Test** - What inputs would break it?
3. **Junior Analyst Challenge** - Spawn fresh agent to find problems

### Documentation Phases
Run these 2:
1. **Documentation Completeness** - All sections present?
2. **Fact-Check Prompt** - Claims accurate?

### Architecture/Design Phases
Run these 3:
1. **Inversion Test** - What would make this design wrong?
2. **Adversarial Self-Check** - Assumptions stated as facts?
3. **"Wait" Pattern** - What am I missing?

### Research/Analysis Phases
Run these 3:
1. **Fact-Check Prompt** - Sources valid?
2. **Confidence Extraction** - How certain?
3. **"Wait" Pattern** - Assumptions?

### Phase Type Quick Matrix

| Phase Type | Must Run | Should Run | Skip |
|------------|----------|------------|------|
| Code/Scripts | Code Review, Inversion | Junior Analyst | Fact-Check, Confidence |
| Documentation | Doc Completeness, Fact-Check | Adversarial | Code Review |
| Architecture | Inversion, Adversarial | Wait, Junior Analyst | Doc Completeness |
| Research | Fact-Check, Confidence | Wait | Code Review |

### Example: Verifying Phase 2 QC Hook

After agent reports completion:

```
1. CODE REVIEW: Review check_activity_quality.py for:
   - All 5 block codes implemented?
   - Exit codes correct (0=pass, 1=fail)?
   - JSON output format matches spec?
   - Edge cases: empty YAML, malformed YAML, huge files?

2. INVERSION: What would make this QC hook wrong?
   - What valid activity would it incorrectly FAIL?
   - What invalid activity would it incorrectly PASS?
   - What em-dash variants might it miss? (—, –, -)

3. JUNIOR ANALYST: Spawn fresh agent to audit the code
   against /home/squiz/ATLAS/docs/HANDOVER_PHASE2_QC_HOOK.md
```

---

## 9. Progressive Overload Verification

For workout progression recommendations (health-critical):

```
Verify progression logic:
1. Starting weight derived correctly?
   - Baseline assessment exists and is <28 days old?
   - 1RM calculated with Brzycki: weight * 36 / (37 - reps)?
   - Starting intensity applied (70% for 10RM, 75% for 5RM)?

2. Double progression trigger valid?
   - All sets hit TOP of rep range (not just average)?
   - No pain warning active for relevant body parts?
   - Increment matches exercise config (2.5kg default)?

3. Deload detection working?
   - Pain spike ≥6/10 triggers immediate deload?
   - 4+ YELLOW days in 10 triggers fatigue deload?
   - 14-day cooldown prevents stacking deloads?

4. Voice prompt appropriate?
   - Single touchpoint (only at exercise ready)?
   - Pain warning prevents progression recommendation?
   - Weight rounded to plate increment?
```

### Progression Test Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Last workout: 25kg × 12 reps (all sets) | Recommend 27.5kg |
| Last workout: 25kg × 10 reps avg | Maintain 25kg |
| Shoulder pain trending up (slope > 0.5) | "Hold at 25kg" |
| No baseline assessment | "What weight are you using?" |
| Bodyweight exercise (bird_dog) | No weight prompt |
| Pain spike at 7/10 today | Deload all exercises |
| Last deload 5 days ago | Cooldown active, no deload |

### AMRAP Verification

```
Final set AMRAP flow:
1. User says "done" on final set
2. System responds "Last set. How many reps?"
3. User says number (e.g., "12")
4. Reps logged to workout_exercise_sets
5. Used in next session's progression calculation
```

---

## 10. Workout Data Persistence Verification

For interactive workout completion:

```
Verify data persisted correctly:
1. workout_exercises table populated?
   - All exercises from _workout_log included?
   - exercise_id, weight_kg, reps columns filled?

2. workout_exercise_sets table populated?
   - Per-set data with set_number, reps_actual, weight_kg?
   - All sets from AMRAP capture included?

3. exercise_progression_log updated?
   - actual_weight_kg matches user input?
   - actual_reps_avg calculated from set data?
   - one_rm_estimate computed (Brzycki)?

4. No data loss on edge cases?
   - User skips exercise mid-workout?
   - User stops workout early ("stop workout")?
   - Workout timeout/crash recovery?
```

### SQL Verification Queries

```sql
-- Check workout_exercise_sets populated
SELECT we.exercise_name, wes.set_number, wes.reps_actual, wes.weight_kg
FROM workout_exercise_sets wes
JOIN workout_exercises we ON wes.workout_exercise_id = we.id
WHERE we.workout_id = (SELECT MAX(id) FROM workouts);

-- Check progression log
SELECT * FROM exercise_progression_log
WHERE date = date('now')
ORDER BY exercise_id;

-- Verify 1RM trend
SELECT exercise_id, date, actual_weight_kg, actual_reps_avg, one_rm_estimate
FROM exercise_progression_log
WHERE exercise_id = 'goblet_squat'
ORDER BY date DESC LIMIT 5;
```

---

## Implementation

```python
from atlas.orchestrator.confidence_router import (
    apply_wait_pattern,      # Generates "Wait" prompt
    route_by_confidence,     # Routes by extracted confidence
    extract_confidence,      # Gets confidence score from text
)

from atlas.health.progression import ProgressionService
# service.get_recommendation("goblet_squat")  # Get weight recommendation
# service.check_deload()                       # Check deload triggers
# service.format_voice_recommendation(rec)    # Format for voice output
```

---

*Agents should use these patterns proactively, especially for safety-critical domains.*

---

## D112: Voice Spec + AI Detection Pipeline Verification

### Voice Spec Integrity Check
```
Verify: Does the voice spec tag structure parse correctly?
1. All XML-like tags have matching open/close pairs
2. No broken tags (e.g., asterisks instead of underscores)
3. <persona_architecture> replaces old <persona>
4. <ai_proof_architecture> replaces old <ai_detection_avoidance>
5. <wonder_science_bridge> exists between </voice_dna> and <ai_proof_architecture>
6. <anti_pattern_examples> exists before </few_shot_examples>
7. No examples contain banned AI patterns ("Here's the thing", etc.)
```

### Cross-Repo Consistency Check
```
Verify: Are all voice spec consumers updated?
1. voice_spec.py section lists reference ai_proof_architecture (not ai_detection_avoidance)
2. voice_spec.py section lists include wonder_science_bridge
3. ELEVATE_VOICE_EXTRACT.md contains persona_architecture (not old persona)
4. ELEVATE_VOICE_EXTRACT.md contains ai_proof_architecture (not ai_detection_avoidance)
5. ELEVATE_VOICE_EXTRACT.md does NOT contain "Here's the thing" as acceptable
6. No file in pipeline references old tag name ai_detection_avoidance
```

### Category 13 Detection Verification
```
Verify: Do all voice spec banned patterns have matching detection?
For each pattern in <what_you_never_do>:
  - Regex exists in CONVERSATIONAL_AI_TELLS
  - Test exists in test_ai_detection.py
  - Both ASCII and curly apostrophe variants handled
  - All matches reported (no early break)
```

### Pipeline Wiring Verification
```
Verify: Does _audit_ai_smell() work end-to-end?
1. _audit_ai_smell() is called in all 3 code paths:
   - convert_activity (main path)
   - _convert_from_cached_transform (retry path)
   - elevate_existing_file (elevation path)
2. Issues from _audit_ai_smell() route correctly to ai_smell_issues in _format_issue_feedback()
3. AI smell feedback section generates actionable rewrite guidance
4. Issues block progression (added to qc_issues, trigger retry)
```

### Number Range Preservation Verification
```
Verify: Does _remove_dashes() preserve number ranges?
Test cases:
  "5-8 cm" -> "5-8 cm" (en-dash preserved as hyphen)
  "0-36 months" -> "0-36 months" (em-dash preserved as hyphen)
  "37-38 C" -> "37-38 C" (temperature range)
  "word-word" -> "word. word" (prose dash replaced)
  "word-. Next" -> "word. Next" (no double period)
```

### Burstiness & AI-Proof Writing Verification
```
Verify: Does the voice spec produce measurably different output?
1. Re-run 2 previously-failed activities with new spec
2. Measure sentence length SD (target: >8 words)
3. Check for 0 em-dashes in output
4. Check for 0 banned AI patterns in output
5. Compare Grade before/after spec change
```

---

## D113 + D114: Full AI Detection Coverage Verification

### 13-Category Coverage Matrix
```
Verify: All 13 AI detection categories have at least one blocking gate.

| Cat | Name                  | QC Hook | _audit_ai_patterns | _audit_ai_smell | Blocking? |
|-----|-----------------------|---------|--------------------|-----------------| --------- |
|  1  | Superlatives          |   YES   |        YES (D113)  |                 |    YES    |
|  2  | Outcome Promises      |         |        YES (D114)  |                 |    YES    |
|  3  | Pressure Language     |   YES   |                    |                 |    YES    |
|  4  | Formal Transitions    |         |        YES (D114)  |                 |    YES    |
|  5  | Non-Contractions      |         |        YES (D113)  |                 |    YES    |
|  6  | Hollow Affirmations   |         |        YES (D113)  |                 |    YES    |
|  7  | AI Clichés            |         |        YES (D113)  |                 |    YES    |
|  8  | Hedge Stacking        |         |        YES (D113)  |                 |    YES    |
|  9  | List Intros           |         |        YES (D113)  |                 |    YES    |
| 10  | Enthusiasm Markers    |         |        YES (D113)  |                 |    YES    |
| 11  | Filler Phrases        |         |        YES (D113)  |                 |    YES    |
| 12  | Em-Dashes             |   YES   |                    |                 |    YES    |
| 13  | Conversational AI     |         |                    |      YES (D112) |    YES    |

Expected: All 13 rows show YES in at least one gate column.
```

### 3 Code Path Verification
```
Verify: All 3 pipeline code paths run all AI detection gates.

Path 1: convert_with_retry (new file, full pipeline)
  → Calls _audit_ai_patterns() at VALIDATE stage? YES
  → Calls _audit_ai_smell() at VALIDATE stage? YES
  → Calls QC hook subprocess? YES

Path 2: elevate_existing_file (re-elevate existing canonical)
  → Calls _audit_ai_patterns()? YES
  → Calls _audit_ai_smell()? YES
  → Calls adversarial verification? YES (D113)

Path 3: cached transform path (retry with cached stages)
  → Calls _audit_ai_patterns()? YES (stages 4-7 still run)
  → Calls _audit_ai_smell()? YES
  → Calls QC hook subprocess? YES

Expected: All 3 paths run all gates. No path skips detection.
```

### Type Safety Verification
```
Verify: qc_issues consumers handle str|dict correctly.

1. Search: grep -n "qc_issues" atlas/pipelines/activity_conversion.py
2. Every location that prints/displays a qc_issue must use _format_display_issue()
3. _format_display_issue handles: str → passthrough, dict → extract "msg" key
4. ConversionResult.qc_issues typed as list[str | dict]

Expected: No raw dict repr in CLI output. All 6 print locations use helper.
```

### Feedback Routing Verification
```
Verify: All AI pattern codes have feedback routing in _format_issue_feedback().

Codes that must route to feedback sections:
  SCRIPT_NO_CONTRACTION    → NON-CONTRACTIONS section
  SCRIPT_HOLLOW_AFFIRMATION → AI WRITING PATTERNS section
  SCRIPT_AI_CLICHE         → AI WRITING PATTERNS section
  SCRIPT_HEDGE_STACKING    → AI WRITING PATTERNS section
  SCRIPT_LIST_INTRO        → AI WRITING PATTERNS section
  SCRIPT_ENTHUSIASM        → AI WRITING PATTERNS section
  SCRIPT_FILLER_PHRASE     → FILLER PHRASES section
  SCRIPT_OUTCOME_PROMISE   → OUTCOME PROMISES section (D114)
  SCRIPT_FORMAL_TRANSITION → FORMAL TRANSITIONS section (D114)

Expected: Each code produces specific, actionable feedback (not generic "fix this").
```

### Regression Audit Prompt
```
Run: python scripts/audit_canonicals.py

Verify: All 29 canonical YAMLs pass all 13 AI detection categories.
If failures exist, categorize:
  - Pre-existing violations (written before D112-D114 gates existed)
  - False positives (detection rule too aggressive)
  - Genuine quality issues needing remediation

Action: Pre-existing violations → remediation backlog (not blocking new pipeline runs).
False positives → adjust detection rules. Genuine issues → fix in canonical files.
```

---

## D115: Production Field Removal Verification

```
Verify: Activity Atoms contain NO production direction fields.

1. grep -r "^production_notes:" knowledge/data/canonical/ --include="*.yaml"
   Expected: ZERO matches

2. grep -r "^content_production:" knowledge/data/canonical/ --include="*.yaml"
   Expected: ZERO matches

3. grep "production_notes" atlas/pipelines/activity_conversion.py
   Expected: ZERO matches (removed from ACTIVITY_SCHEMA_SUMMARY)

4. grep "production_notes" knowledge/scripts/check_activity_quality.py
   Expected: ZERO matches (removed from REQUIRED_SECTIONS)

5. Spot-check: tail -15 knowledge/data/canonical/activities/movement/ACTIVITY_MOVEMENT_TUMMY_TIME_MICRO_SESSIONS_0_6M.yaml
   Expected: Ends with parent_search_terms. No production_notes or content_production.

6. python scripts/audit_canonicals.py
   Expected: Runs successfully (no errors about missing production fields)
```

### Separation of Concerns Verification
```
Verify: Pipeline generates Activity Atoms WITHOUT production fields.

1. Check: ACTIVITY_SCHEMA_SUMMARY constant in activity_conversion.py
   Expected: "production_notes" NOT in the string

2. Check: REQUIRED_SECTIONS in check_activity_quality.py
   Expected: "production_notes" NOT in the list

3. Check: transform_activity.md section count
   Expected: "31" (not "32")

4. Check: validate_activity.md
   Expected: No "production" group in required_sections
```
