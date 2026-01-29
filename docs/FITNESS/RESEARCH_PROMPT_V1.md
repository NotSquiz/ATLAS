# ATLAS Fitness System Research Prompt

> **Purpose**: Provide this prompt to a web research agent to design a comprehensive, science-based fitness rehabilitation and development program.

---

## RESEARCH AGENT PROMPT

You are designing a comprehensive 12-week (Phase 1-3) fitness rehabilitation and development program for ATLAS, a personal health tracking system. Your output must be structured as JSON that can be directly imported into the system.

### SUBJECT PROFILE

```yaml
Demographics:
  Age: 38 years
  Sex: Male
  Height: 180 cm
  Weight: 72 kg

Athletic Background:
  Sport: Soccer (20 years)
  Current_Status: 4 months inactive, taking 1 year off
  Goal: Become functionally strong, powerful, and healthy

Current Injuries/Issues:
  1. Right Shoulder:
     - Diagnosis: Grade 1 Supraspinatus Tendinopathy
     - Mechanism: Chronic overhead loading + acute soccer fall
     - Contraindicated: Pull-ups, chin-ups, upright rows, wide-grip pulling
     - Status: Recovering (Phase 1 rehab)

  2. Feet (Bilateral):
     - Symptoms: Balls of feet ache and stiff in mornings
     - Cause: 20 years of soccer (metatarsal stress, plantar fascia tightness)
     - No formal diagnosis

  3. Left Ankle (primary) + Right Ankle (secondary):
     - History: Broken ankle never properly set
     - Symptoms: Cracking, loss of mobility, scar tissue on lateral joint
     - Impact: Reduced dorsiflexion, compensatory movement patterns

  4. Lower Back:
     - Symptoms: Intermittent dull ache
     - Cause: Poor posture (desk work + compensation from ankle/hip issues)
     - No structural diagnosis
```

### RESEARCH REQUIREMENTS

#### Part 1: Baseline Assessment Protocol

Research and design a comprehensive baseline testing protocol that includes:

**1.1 Strength Testing**
- Safe 3RM or 5RM tests for returning athletes (NOT 1RM for someone deconditioned)
- Appropriate exercises: Trap bar deadlift, goblet squat, floor press, rows
- How to calculate estimated 1RM from submaximal tests
- Re-testing frequency (every 4 weeks recommended)

**1.2 Power/Explosive Testing**
- Vertical jump test protocol (when safe to introduce - NOT Phase 1)
- Broad jump test protocol
- Medicine ball throw tests
- Reactive strength index concepts

**1.3 Cardiovascular Assessment**
- Resting heart rate baseline
- Heart rate recovery test (1-minute post-exercise)
- Submaximal VO2 estimation (talk test, HR zones)
- Integration with Garmin Forerunner 165 metrics (HRV, Body Battery)

**1.4 Mobility/Flexibility Assessment**
- Ankle dorsiflexion test (knee-to-wall, target: >10cm)
- Hip flexor length (Thomas test)
- Shoulder mobility (Apley scratch test, wall angels)
- Thoracic rotation
- Toe touch / sit-and-reach
- Great toe extension (critical for soccer players)

**1.5 Stability/Motor Control Assessment**
- Single-leg balance (eyes open/closed, target: 30s+)
- Single-leg squat quality
- Core endurance (McGill Big 3 baselines: curl-up, side plank, bird-dog)
- Y-balance or Star Excursion Balance Test (ankle function)

**1.6 Pain/Function Tracking**
- 0-10 pain scale for each issue (shoulder, feet, ankles, back)
- Functional tests: Can you squat to depth? Single leg hop? Overhead reach?
- Morning stiffness duration tracking

#### Part 2: Daily Non-Negotiables Routine

Design a 15-20 minute morning routine that addresses ALL issues. This should be:
- Safe to perform daily (7 days/week)
- Performable with minimal equipment (tennis ball, resistance band, foam roller)
- Progressive over 12 weeks

**Must Address:**

**Feet/Plantar Fascia:**
- Ball rolling (lacrosse/tennis ball) for plantar fascia
- Toe yoga (spreads, scrunches, big toe isolation)
- Short foot exercise (intrinsic foot strength)
- Calf stretching (gastrocnemius AND soleus)

**Ankles:**
- Ankle CARs (Controlled Articular Rotations)
- Banded ankle mobilization (anterior/posterior glides)
- Calf raises (eccentric emphasis for Achilles health)
- Alphabet writing with foot
- Scar tissue mobilization techniques for lateral ankle

**Lower Back:**
- Cat-cow (spinal segmentation)
- Dead bug (core activation without back strain)
- Hip flexor stretching (90/90, couch stretch)
- Glute activation (bridges, clamshells)
- Bird-dog (anti-rotation stability)

**Shoulder (existing protocol):**
- Doorframe external rotation isometrics
- Towel crush (internal rotation activation)
- Band pull-aparts
- Scapular wall slides

**Posture Reset:**
- Thoracic extensions over foam roller
- Chin tucks
- Wall angels

#### Part 3: Phase 1-3 Training Program

Design a 12-week periodized program with Traffic Light adaptation:

**Phase 1: Foundation (Weeks 1-4)**
- Focus: Movement quality, pain reduction, tissue tolerance
- Intensity: Low (RPE 5-6)
- Volume: 2-3 sets, 10-15 reps
- Rest: 60-90 seconds
- Progression: Add 1 set per week, then add load
- Tests: Baseline assessments Week 1, re-test Week 4

**Phase 2: Build (Weeks 5-8)**
- Focus: Progressive overload, strength foundation
- Intensity: Moderate (RPE 6-7)
- Volume: 3-4 sets, 8-12 reps
- Rest: 90-120 seconds
- Progression: Add load when hitting top of rep range
- Tests: Re-test Week 5 and Week 8
- Introduce: Tempo work, controlled eccentrics

**Phase 3: Develop (Weeks 9-12)**
- Focus: Strength development, introduce power prep
- Intensity: Moderate-High (RPE 7-8)
- Volume: 4 sets, 6-10 reps (strength), 3 sets 5 reps (power prep)
- Rest: 2-3 minutes for main lifts
- Progression: Linear periodization, add explosive prep
- Tests: Re-test Week 9 and Week 12
- Introduce: Box jumps (low height), medicine ball work

**Traffic Light Modifications:**

```yaml
GREEN_DAY:
  Criteria:
    - Sleep > 6.5 hours
    - HRV: BALANCED or better
    - RHR: < baseline + 5bpm
    - Pain levels: All < 3/10
  Action: Execute full programmed workout

YELLOW_DAY:
  Criteria:
    - Sleep 5.5-6.5 hours OR
    - HRV: borderline OR
    - Any pain level 3-5/10
  Modifications:
    - Reduce sets by 1
    - Reduce intensity by 10-15%
    - Skip explosive/power movements
    - Add extra mobility work

RED_DAY:
  Criteria:
    - Sleep < 5.5 hours OR
    - HRV: UNBALANCED/LOW OR
    - Any pain level > 5/10 OR
    - RHR elevated > 8bpm
  Action:
    - Daily non-negotiables only
    - 20-min Zone 2 walk
    - NSDR (20 min)
    - No resistance training
```

**Weekly Structure (All Phases):**

```yaml
Monday: Strength A - Lower Body Focus
Tuesday: Zone 2 Cardio + Mobility
Wednesday: Strength B - Upper Body (Shoulder Rehab Focus)
Thursday: Active Recovery / Mobility Flow
Friday: Strength C - Full Body Functional
Saturday: Cardio (Zone 2 or VO2 work depending on phase)
Sunday: Complete Rest or Light Walk
```

#### Part 4: Exercise Database Requirements

For each exercise, provide:

```yaml
Exercise:
  id: "trap_bar_deadlift"
  name: "Trap Bar Deadlift"
  category: "compound"
  primary_muscles: ["glutes", "hamstrings", "quads", "erectors"]
  equipment: ["trap_bar"]

  contraindications:
    - "acute_lower_back_pain"
    - "hip_impingement"

  injury_modifications:
    shoulder_injury: "Safe - no shoulder load"
    ankle_mobility: "Elevate heels on plates if limited dorsiflexion"
    lower_back: "Reduce load, focus on hip hinge pattern"

  progressions:
    phase_1: { sets: 3, reps: 10, rpe: 6, tempo: "2-1-2-0" }
    phase_2: { sets: 4, reps: 8, rpe: 7, tempo: "3-1-1-0" }
    phase_3: { sets: 4, reps: 6, rpe: 8, tempo: "2-0-X-0" }

  cues:
    - "Hinge at hips, not squat"
    - "Chest up, shoulders packed"
    - "Drive through whole foot"
    - "Squeeze glutes at top"

  video_reference: "URL to proper form video"
```

#### Part 5: Progression & Recalibration Rules

**Progression Criteria (to move between phases):**

```yaml
Phase_1_to_Phase_2:
  Required:
    - Complete 4 weeks with < 2 RED days per week average
    - All pain levels consistently < 3/10
    - Hit all movement quality standards:
      - Goblet squat to depth without pain
      - Single leg balance 30s+ each side
      - Ankle dorsiflexion > 8cm improvement from baseline
    - Strength tests show improvement or maintenance

Phase_2_to_Phase_3:
  Required:
    - Complete 4 weeks with < 2 RED days per week average
    - All pain levels consistently < 2/10
    - Demonstrate:
      - Controlled single leg squat
      - Can perform exercises at prescribed tempos
      - HRV trending positive or stable
    - Strength increase of 10-15% from Phase 1 baseline
```

**Recalibration Triggers:**

```yaml
PAUSE_AND_REASSESS:
  - 3+ RED days in a single week
  - Any pain level spike to 6+/10
  - Failed progression (can't complete prescribed workout 2x in a row)
  - HRV declining trend over 2 weeks

REGRESS_ONE_PHASE:
  - Injury flare-up
  - New pain presentation
  - Illness lasting > 5 days
  - Extended break (> 10 days missed)

MEDICAL_REFERRAL_TRIGGERS:
  - Pain > 7/10 that doesn't resolve with rest
  - New neurological symptoms (numbness, tingling)
  - Joint swelling
  - Pain that wakes you from sleep
```

#### Part 6: Output Format

Provide all data in JSON format matching this structure:

```json
{
  "metadata": {
    "version": "1.0",
    "created": "2026-01-XX",
    "subject_profile": { ... },
    "sources": ["list of research sources used"]
  },

  "assessments": {
    "baseline_tests": [ ... ],
    "retest_schedule": { ... },
    "scoring_rubrics": { ... }
  },

  "daily_routine": {
    "name": "ATLAS Morning Protocol",
    "duration_minutes": 15,
    "sections": [
      {
        "name": "Feet & Ankles",
        "exercises": [ ... ]
      },
      ...
    ]
  },

  "phases": {
    "phase_1": {
      "weeks": [1, 4],
      "focus": "...",
      "schedule": { ... },
      "protocols": { ... }
    },
    ...
  },

  "exercises": {
    "exercise_id": { ... }
  },

  "traffic_light_rules": { ... },

  "progression_rules": { ... },

  "recalibration_rules": { ... }
}
```

### RESEARCH SOURCES TO CONSULT

1. **Shoulder Rehabilitation**:
   - Rotator cuff tendinopathy protocols (Littlewood et al.)
   - Eccentric training for tendinopathy (Alfredson protocol adaptations)

2. **Ankle Rehabilitation**:
   - Chronic ankle instability protocols
   - Scar tissue mobilization (IASTM research)
   - Dorsiflexion improvement studies

3. **Foot Health**:
   - Plantar fasciitis management
   - Intrinsic foot muscle strengthening (McKeon et al.)
   - Barefoot training research

4. **Lower Back**:
   - McGill Big 3 for spinal stability
   - Hip-spine connection research
   - Postural correction protocols

5. **Return to Sport**:
   - Periodization for returning athletes
   - Cardiovascular reconditioning
   - Injury prevention screening (FMS, Y-Balance)

6. **Testing Protocols**:
   - NSCA guidelines for strength testing
   - Submaximal VO2 estimation methods
   - Mobility assessment standards

7. **Recovery Science**:
   - HRV-guided training research
   - Sleep and recovery relationships
   - Autoregulation in training

### DELIVERABLES CHECKLIST

- [ ] Complete baseline assessment protocol with scoring rubrics
- [ ] 15-20 minute daily routine addressing all issues
- [ ] Phase 1 complete weekly program (7 days x 4 weeks)
- [ ] Phase 2 complete weekly program (7 days x 4 weeks)
- [ ] Phase 3 complete weekly program (7 days x 4 weeks)
- [ ] Full exercise database with all exercises used
- [ ] Traffic Light modification rules for each workout
- [ ] Progression criteria between phases
- [ ] Recalibration triggers and protocols
- [ ] All data in JSON format for ATLAS import

---

## END OF PROMPT

---

## ATLAS Integration Notes

When the research agent returns data, ATLAS will:

1. Parse JSON into `config/workouts/` files
2. Add exercises to exercise database
3. Create assessment tracking tables
4. Set up phase progression logic
5. Configure recalibration alerts
6. Add pain tracking to daily logging
