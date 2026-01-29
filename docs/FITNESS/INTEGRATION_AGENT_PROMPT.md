# ATLAS Fitness Integration Agent Prompt

> **Purpose**: Give this prompt + your research output to a fresh Claude agent to integrate everything into ATLAS.

---

## AGENT INSTRUCTIONS

You are integrating a comprehensive fitness rehabilitation program into ATLAS, a personal health tracking system. The user will provide detailed research output containing morning routines, workout protocols, and phase progressions.

Your job is to:
1. Parse the research into ATLAS-compatible JSON format
2. Create config files for each phase
3. Extend the daily routine system
4. Ensure Traffic Light (GREEN/YELLOW/RED) variations are captured
5. Set up baseline testing protocols
6. Configure progression rules

---

## ATLAS SYSTEM ARCHITECTURE

### Directory Structure
```
/home/squiz/ATLAS/
├── atlas/
│   └── health/
│       ├── __init__.py      # Module exports
│       ├── router.py        # TrafficLightRouter (GREEN/YELLOW/RED logic)
│       ├── workout.py       # WorkoutService (loads protocols, logs workouts)
│       ├── supplement.py    # SupplementService
│       ├── garmin.py        # GarminService stub
│       ├── service.py       # HealthService orchestrator
│       └── cli.py           # CLI commands
├── config/
│   └── workouts/
│       └── phase1.json      # Current Phase 1 protocol (to be replaced/extended)
└── docs/
    └── FITNESS/
        └── *.md             # Documentation
```

### Database Schema (already created)

**Core Tables**:
- `daily_metrics` - Sleep, HRV, weight, energy, mood
- `workouts` - Workout sessions
- `workout_exercises` - Exercises within workouts
- `supplements` / `supplement_log` - Supplement tracking
- `injuries` - Active injuries with contraindications

**Fitness Extension Tables** (already created):
- `pain_log` - Daily pain tracking (0-10) per body part
- `assessment_types` - Test definitions with targets
- `assessments` - Individual test results
- `training_phases` - Phase definitions
- `phase_history` - User's progression through phases
- `exercises` - Exercise database
- `exercise_progressions` - Per-phase exercise parameters
- `recalibration_alerts` - Auto-triggers for adjustments

**Registered Injuries**:
```
- shoulder (right): Grade 1 Supraspinatus Tendinopathy
- feet (both): Metatarsal stress, plantar fascia tightness
- ankle (left): Old break, scar tissue, reduced mobility
- ankle (right): Compensation patterns
- lower_back: Intermittent dull ache, poor posture
```

---

## JSON FORMAT SPECIFICATIONS

### Phase Configuration (`config/workouts/phase{N}.json`)

```json
{
  "metadata": {
    "phase": 1,
    "name": "Foundation & Rehabilitation",
    "weeks": [1, 12],
    "focus": "Movement quality, pain reduction, tissue tolerance",
    "intensity_range": "RPE 5-6",
    "source": "Web research agent - January 2026"
  },

  "schedule": {
    "0": "strength_a",
    "1": "zone2_cardio",
    "2": "strength_b",
    "3": "active_mobility",
    "4": "strength_c",
    "5": "vo2_max_or_zone2",
    "6": "recovery"
  },

  "daily_routine": {
    "name": "ATLAS Morning Protocol",
    "duration_minutes": 18,
    "frequency": "daily",
    "sections": [
      {
        "name": "Feet & Plantar Fascia",
        "duration_minutes": 4,
        "exercises": [
          {
            "id": "plantar_ball_roll",
            "name": "Plantar Fascia Ball Roll",
            "duration_seconds": 60,
            "per_side": true,
            "equipment": ["lacrosse_ball"],
            "cues": ["Apply moderate pressure", "Roll heel to toes", "Pause on tender spots"],
            "video_url": null
          }
        ]
      },
      {
        "name": "Ankle Mobility",
        "duration_minutes": 4,
        "exercises": [...]
      },
      {
        "name": "Lower Back & Hips",
        "duration_minutes": 4,
        "exercises": [...]
      },
      {
        "name": "Shoulder Rehab",
        "duration_minutes": 4,
        "exercises": [...]
      },
      {
        "name": "Posture Reset",
        "duration_minutes": 2,
        "exercises": [...]
      }
    ]
  },

  "protocols": {
    "strength_a": {
      "id": "strength_a",
      "name": "Strength A - Lower Body",
      "type": "strength",
      "day_of_week": 0,
      "duration_minutes": 45,
      "goal": "Build posterior chain strength, fix hip/ankle mobility",

      "warmup": {
        "description": "Complete Daily Routine + specific activation",
        "exercises": [
          {"id": "glute_bridge", "sets": 2, "reps": 10}
        ]
      },

      "exercises": [
        {
          "id": "trap_bar_deadlift",
          "name": "Trap Bar Deadlift",
          "category": "compound",
          "primary_muscles": ["glutes", "hamstrings", "quads"],

          "green_day": {
            "sets": 3,
            "reps": "8",
            "rpe": 7,
            "tempo": "2-1-2-0",
            "rest_seconds": 90
          },
          "yellow_day": {
            "sets": 2,
            "reps": "10",
            "rpe": 6,
            "tempo": "3-1-2-0",
            "rest_seconds": 90
          },
          "red_day": null,

          "cues": [
            "Hinge at hips, not squat",
            "Chest up, shoulders packed",
            "Drive through whole foot"
          ],
          "injury_modifications": {
            "ankle_mobility": "Elevate heels on 1-inch plates",
            "lower_back": "Reduce load 20%, focus on hip hinge"
          }
        }
      ],

      "cooldown": ["Pigeon stretch 90s/side", "Hip flexor stretch 60s/side"]
    },

    "zone2_cardio": {...},
    "strength_b": {...},
    "active_mobility": {...},
    "strength_c": {...},
    "vo2_max_or_zone2": {...},
    "recovery": {...}
  },

  "red_day_override": {
    "protocol": {
      "id": "red_day",
      "name": "RED DAY Protocol",
      "type": "recovery",
      "duration_minutes": 40,
      "exercises": [
        {"id": "daily_routine", "name": "Complete Morning Routine", "duration_minutes": 18},
        {"id": "zone2_walk", "name": "Zone 2 Walk", "duration_minutes": 20},
        {"id": "nsdr", "name": "NSDR / Yoga Nidra", "duration_minutes": 20}
      ]
    }
  },

  "traffic_light_rules": {
    "green": {
      "criteria": {
        "sleep_hours_min": 6.5,
        "hrv_status": ["BALANCED", "GOOD", "EXCELLENT"],
        "rhr_max_above_baseline": 5,
        "pain_max": 2
      },
      "action": "Execute full programmed workout"
    },
    "yellow": {
      "criteria": {
        "sleep_hours_range": [5.5, 6.5],
        "pain_range": [3, 5]
      },
      "modifications": [
        "Reduce sets by 1",
        "Reduce intensity by 15%",
        "Skip explosive/power movements",
        "Add 5 min extra mobility"
      ]
    },
    "red": {
      "criteria": {
        "sleep_hours_max": 5.5,
        "hrv_status": ["UNBALANCED", "LOW", "STRAINED"],
        "rhr_above_baseline": 8,
        "pain_min": 6
      },
      "action": "RED DAY Protocol only"
    }
  },

  "progression_rules": {
    "advance_to_next_phase": {
      "weeks_minimum": 4,
      "red_days_per_week_max": 2,
      "pain_levels_max": 3,
      "strength_tests_improvement": true,
      "mobility_targets_met": ["ankle_dorsiflexion >= 10cm"]
    },
    "regress_triggers": [
      "3+ RED days in single week",
      "Pain spike to 6+/10",
      "New injury or flare-up"
    ]
  }
}
```

### Baseline Assessments (`config/assessments/baseline.json`)

```json
{
  "metadata": {
    "name": "Baseline Assessment Protocol",
    "duration_minutes": 60,
    "retest_frequency_weeks": 4
  },

  "assessments": {
    "strength": [
      {
        "id": "trap_bar_deadlift_5rm",
        "name": "Trap Bar Deadlift 5RM",
        "protocol": "Warm up progressively. Find weight you can lift 5 times with good form.",
        "unit": "kg",
        "calculate_1rm": "weight * 1.15",
        "target": 100,
        "minimum": 60
      }
    ],

    "mobility": [
      {
        "id": "ankle_dorsiflexion_left",
        "name": "Ankle Dorsiflexion - Left",
        "protocol": "Knee to wall test. Measure distance from big toe to wall when knee touches.",
        "unit": "cm",
        "target": 12,
        "minimum": 8,
        "notes": "Key metric for ankle rehab"
      }
    ],

    "stability": [
      {
        "id": "single_leg_balance_left_eo",
        "name": "Single Leg Balance - Left (Eyes Open)",
        "protocol": "Stand on one leg, hands on hips. Time until loss of balance.",
        "unit": "seconds",
        "target": 60,
        "minimum": 30
      }
    ],

    "cardio": [
      {
        "id": "resting_hr",
        "name": "Resting Heart Rate",
        "protocol": "Measure upon waking, before getting out of bed. Average 3 days.",
        "unit": "bpm",
        "target": 55,
        "minimum": 70,
        "lower_is_better": true
      }
    ]
  },

  "pain_baseline": {
    "body_parts": ["shoulder_right", "feet", "ankle_left", "ankle_right", "lower_back"],
    "scale": "0-10 where 0=no pain, 10=worst imaginable",
    "measure_timing": "Upon waking, before any movement"
  }
}
```

### Running Protocol (`config/workouts/running_return.json`)

```json
{
  "metadata": {
    "name": "Return to Running Protocol",
    "prerequisite_phase": "phase_1",
    "prerequisite_criteria": {
      "ankle_dorsiflexion_min": 10,
      "single_leg_balance_min": 45,
      "pain_levels_max": 2,
      "weeks_pain_free": 2
    }
  },

  "progression": [
    {
      "week": 1,
      "sessions_per_week": 3,
      "protocol": "Walk 4min / Jog 1min x 4 rounds",
      "total_minutes": 20,
      "surface": "Grass or track preferred",
      "pace": "Conversational jog only",
      "abort_if": "Any pain > 3/10 during or next day"
    },
    {
      "week": 2,
      "sessions_per_week": 3,
      "protocol": "Walk 3min / Jog 2min x 4 rounds",
      "total_minutes": 20
    }
  ]
}
```

---

## INTEGRATION TASKS

### Task 1: Create Phase JSON Files

Create the following files from the research:

```
config/workouts/
├── phase1_foundation.json      # Weeks 1-12: Rehab focus
├── phase2_combat_ready.json    # Weeks 13-24: Performance
├── daily_routine.json          # Morning routine (can be shared)
├── running_return.json         # Running protocol
└── assessments_baseline.json   # Testing protocols
```

### Task 2: Update WorkoutService

Extend `/home/squiz/ATLAS/atlas/health/workout.py` to:
- Load the daily routine separately
- Support GREEN/YELLOW/RED variations per exercise
- Handle phase transitions

### Task 3: Create Daily Routine Display

Add to CLI (`atlas/health/cli.py`):
```bash
python3 -m atlas.health.cli routine          # Show today's routine
python3 -m atlas.health.cli routine start    # Interactive guided routine
python3 -m atlas.health.cli routine log      # Mark routine complete
```

### Task 4: Create Assessment Commands

Add to CLI:
```bash
python3 -m atlas.health.cli assess baseline  # Run full baseline
python3 -m atlas.health.cli assess log ankle_dorsiflexion_left --value 9.5
python3 -m atlas.health.cli assess progress  # Show progress vs baseline
```

### Task 5: Update Daily Command

Enhance `daily` command to include:
- Pain check prompt (or show if logged)
- Traffic Light with pain consideration
- Morning routine reminder
- Today's workout with correct variation

### Task 6: Create Phase Management

Add to CLI:
```bash
python3 -m atlas.health.cli phase            # Show current phase + progress
python3 -m atlas.health.cli phase check      # Check if ready to advance
python3 -m atlas.health.cli phase advance    # Move to next phase
```

---

## VALIDATION CHECKLIST

After integration, verify:

- [ ] `python3 -m atlas.health.cli routine` displays morning routine
- [ ] `python3 -m atlas.health.cli workout` shows correct GREEN/YELLOW/RED variation
- [ ] `python3 -m atlas.health.cli daily --sleep 5 --hrv UNBALANCED` triggers RED day
- [ ] `python3 -m atlas.health.cli pain` integrates with Traffic Light
- [ ] `python3 -m atlas.health.cli assess baseline` lists all tests
- [ ] `python3 -m atlas.health.cli phase` shows current phase
- [ ] Phase 2 protocol loads correctly when configured

---

## SUBJECT CONTEXT (for reference)

```yaml
Subject:
  Age: 38
  Height: 180cm
  Weight: 72kg
  Background: 20 years soccer, 4 months inactive
  Goal: Functional strength, power, pain-free movement

Injuries:
  - Right shoulder: Supraspinatus tendinopathy (recovering)
  - Feet: Plantar fascia tightness (both)
  - Left ankle: Old break, scar tissue, reduced mobility
  - Right ankle: Compensation patterns
  - Lower back: Postural strain

Contraindicated:
  - Pull-ups, chin-ups, upright rows (shoulder)
  - Loaded spinal flexion (back)
  - High-impact single-leg left (ankle)

Current Supplements:
  - Vitamin D (5000 IU, morning)
  - Creatine (5g, morning)
  - Omega-3 (2g, with meals)
  - Magnesium (400mg, before bed)
```

---

## HOW TO USE THIS PROMPT

1. Start a new Claude conversation
2. Paste this entire prompt
3. Then paste your research output (the detailed routines, exercises, phases)
4. Say: "Integrate this research into ATLAS following the specifications above"

The agent will:
- Parse your research
- Create the JSON config files
- Extend the Python services as needed
- Add CLI commands
- Verify everything works

---

**End of Integration Prompt**
