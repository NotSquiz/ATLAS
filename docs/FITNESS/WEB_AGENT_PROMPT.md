# Fitness Program Design Prompt for Web Research Agent

**Copy everything below this line to give to a web research agent (Claude, Gemini, etc.)**

---

## TASK

Design a comprehensive 12-week periodized fitness rehabilitation program. Output must be structured JSON that can be imported into a tracking system.

## SUBJECT PROFILE

- **Age**: 38 | **Sex**: Male | **Height**: 180cm | **Weight**: 72kg
- **Background**: 20 years soccer, 4 months inactive, taking 1 year off to rebuild
- **Goal**: Become functionally strong, powerful, and pain-free

### Current Injuries (All Must Be Addressed)

| Area | Issue | Severity |
|------|-------|----------|
| Right Shoulder | Grade 1 Supraspinatus Tendinopathy | Recovering |
| Feet (both) | Morning stiffness, metatarsal ache (20yr soccer wear) | Active |
| Left Ankle | Old break never set properly, scar tissue, reduced mobility | Active |
| Right Ankle | Compensation patterns, cracking | Active |
| Lower Back | Intermittent dull ache, poor posture | Active |

### Contraindicated Exercises
- Pull-ups, chin-ups, upright rows, wide-grip overhead work (shoulder)
- Loaded spinal flexion (back)
- High-impact single-leg work on left side (ankle)

## REQUIRED DELIVERABLES

### 1. Baseline Assessment Protocol (Week 1)

Design tests for:
- **Strength**: 5RM trap bar deadlift, 10RM goblet squat, 10RM floor press
- **Mobility**: Ankle dorsiflexion (knee-to-wall), shoulder flexion, hip flexors, toe touch, great toe extension
- **Stability**: Single-leg balance (eyes open/closed), McGill Big 3 holds
- **Cardio**: Resting HR, HR recovery (1-min post-exercise)
- **Pain Baseline**: 0-10 scale for each injury area

### 2. Daily Morning Routine (15-20 min)

Must address ALL issues:

**Feet/Plantar Fascia**: Ball rolling, toe yoga, short foot exercise, calf stretches
**Ankles**: CARs, banded mobilization, eccentric calf raises, scar tissue work
**Lower Back**: Cat-cow, dead bug, hip flexor stretch, glute bridges, bird-dog
**Shoulder**: Doorframe isometrics, band pull-aparts, wall slides
**Posture**: Thoracic extensions, chin tucks

### 3. Phase 1: Foundation (Weeks 1-4)

- **Focus**: Movement quality, pain reduction, tissue tolerance
- **Intensity**: RPE 5-6 (light to moderate)
- **Volume**: 2-3 sets, 10-15 reps, 60-90s rest
- **Weekly Structure**:
  - Mon: Lower body strength
  - Tue: Zone 2 cardio + mobility
  - Wed: Upper body (shoulder-safe)
  - Thu: Active recovery / mobility flow
  - Fri: Full body functional
  - Sat: Zone 2 cardio
  - Sun: Rest

### 4. Phase 2: Build (Weeks 5-8)

- **Focus**: Progressive overload, strength foundation
- **Intensity**: RPE 6-7
- **Volume**: 3-4 sets, 8-12 reps, 90-120s rest
- **Progression**: Add load when hitting top of rep range
- **Introduce**: Tempo work, controlled eccentrics

### 5. Phase 3: Develop (Weeks 9-12)

- **Focus**: Strength development, power preparation
- **Intensity**: RPE 7-8
- **Volume**: 4 sets, 6-10 reps (strength), 3x5 (power prep)
- **Introduce**: Box jumps (low height), medicine ball work

### 6. Traffic Light System

```yaml
GREEN (Full Workout):
  - Sleep > 6.5h
  - HRV balanced
  - All pain < 3/10

YELLOW (Modified):
  - Sleep 5.5-6.5h OR pain 3-5/10
  - Reduce sets by 1
  - Reduce intensity 15%
  - Skip explosive work

RED (Recovery Only):
  - Sleep < 5.5h OR pain > 5/10 OR HRV unbalanced
  - Morning routine only
  - 20min Zone 2 walk
  - NSDR 20min
```

### 7. Progression Criteria

**Phase 1 → 2**: 4 weeks complete, <2 RED days/week avg, all pain <3/10, hit mobility targets
**Phase 2 → 3**: 4 weeks complete, all pain <2/10, 10-15% strength increase, single-leg squat achieved

### 8. Recalibration Triggers

- 3+ RED days in one week → Pause and reassess
- Pain spike to 6+/10 → Regress one phase
- New symptoms → Medical referral

## OUTPUT FORMAT

```json
{
  "metadata": {
    "version": "1.0",
    "subject_profile": {...},
    "sources": ["list research sources"]
  },
  "daily_routine": {
    "duration_minutes": 15,
    "sections": [
      {"name": "Feet & Ankles", "exercises": [...]},
      {"name": "Lower Back & Hips", "exercises": [...]},
      {"name": "Shoulder", "exercises": [...]},
      {"name": "Posture Reset", "exercises": [...]}
    ]
  },
  "assessments": {
    "baseline_tests": [...],
    "retest_schedule": "every 4 weeks",
    "scoring": {...}
  },
  "phases": {
    "phase_1": {
      "weeks": [1,4],
      "schedule": {
        "monday": {...},
        "tuesday": {...}
      },
      "exercises": [...]
    },
    "phase_2": {...},
    "phase_3": {...}
  },
  "traffic_light_rules": {...},
  "progression_rules": {...}
}
```

## RESEARCH SOURCES TO USE

- Rotator cuff tendinopathy protocols (Littlewood)
- Chronic ankle instability rehab
- Plantar fasciitis / intrinsic foot strengthening (McKeon)
- McGill Big 3 for spinal stability
- Return-to-sport periodization for 35+ athletes
- HRV-guided autoregulation research

## KEY REQUIREMENTS

1. Every exercise must have: sets, reps, tempo, RPE target, coaching cues
2. Include injury modifications for each exercise
3. Specify when to progress vs regress
4. Include warm-up for each workout
5. Reference science/research for major decisions

---

**End of prompt**
