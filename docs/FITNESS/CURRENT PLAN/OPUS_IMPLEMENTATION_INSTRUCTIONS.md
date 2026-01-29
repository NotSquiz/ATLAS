# ATLAS Implementation Instructions for Opus CLI
## Consolidated from Claude Web Session - January 16, 2026

**Context:** Alexander is starting Phase 1 training on Monday 19th January 2026. These instructions set up ATLAS to track baselines, workouts, cardio, and prepare for future integrations (Keiser M3i bike, Withings scale).

---

## 1. FILES TO SAVE

Two files have been created and should be saved to the ATLAS repo:

1. `atlas_baseline_assessment_protocol.md` → Save to `docs/` or `config/assessments/`
2. `config_phase1_weeks1-12.json` → Save to `config/phases/`

---

## 2. DATABASE SCHEMA ADDITIONS

Add these tables to the ATLAS SQLite database:

```sql
-- ============================================
-- BASELINE ASSESSMENTS (Full protocol results)
-- ============================================
CREATE TABLE IF NOT EXISTS baseline_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_date DATE NOT NULL,
    assessment_type VARCHAR(30) NOT NULL,  -- 'initial', 'week4', 'week8', 'week12', 'gate1'
    phase INTEGER DEFAULT 1,
    week_number INTEGER,
    
    -- Anthropometrics
    weight_kg REAL,
    body_fat_pct REAL,
    waist_cm REAL,
    hips_cm REAL,
    chest_cm REAL,
    
    -- Garmin vitals (snapshot)
    resting_hr INTEGER,
    hrv_status VARCHAR(20),
    hrv_avg INTEGER,
    vo2_max_estimate REAL,
    body_battery INTEGER,
    
    -- Flexibility (bilateral data)
    wblt_right_cm REAL,
    wblt_left_cm REAL,
    wblt_asymmetry_cm REAL,
    sit_reach_cm REAL,
    shoulder_mobility_right_cm REAL,
    shoulder_mobility_left_cm REAL,
    
    -- Balance
    sl_balance_eo_right_sec INTEGER,
    sl_balance_eo_left_sec INTEGER,
    sl_balance_ec_right_sec INTEGER,
    sl_balance_ec_left_sec INTEGER,
    sit_to_stand_score INTEGER,
    
    -- FMS
    fms_deep_squat INTEGER,
    fms_hurdle_step INTEGER,
    fms_inline_lunge INTEGER,
    fms_aslr INTEGER,
    fms_trunk_pushup INTEGER,
    fms_rotary_stability INTEGER,
    fms_total INTEGER,
    
    -- Strength (estimated 1RM in kg)
    goblet_squat_1rm REAL,
    rdl_1rm REAL,
    floor_press_1rm REAL,
    row_1rm REAL,
    pushups_max INTEGER,
    pullups_max INTEGER,
    plank_sec INTEGER,
    wall_sit_sec INTEGER,
    dead_hang_sec INTEGER,
    
    -- Rehab specific
    heel_raises_right INTEGER,
    heel_raises_left INTEGER,
    heel_raises_lsi REAL,
    double_hop_completed BOOLEAN,
    double_hop_pain INTEGER,
    
    -- Cardio
    zone2_avg_hr INTEGER,
    zone2_avg_power INTEGER,
    step_test_recovery_hr INTEGER,
    walk_1km_time_sec INTEGER,
    walk_1km_avg_hr INTEGER,
    
    -- Pain snapshot (JSON)
    pain_snapshot JSON,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_baseline_date ON baseline_assessments(assessment_date DESC);
CREATE INDEX IF NOT EXISTS idx_baseline_type ON baseline_assessments(assessment_type);


-- ============================================
-- TEST RESULTS (Individual test tracking over time)
-- ============================================
CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_date DATE NOT NULL,
    test_name VARCHAR(50) NOT NULL,  -- 'wblt_right', 'pushups', 'goblet_squat_1rm', etc.
    test_category VARCHAR(30),        -- 'flexibility', 'strength', 'balance', 'cardio', 'rehab'
    value REAL NOT NULL,
    unit VARCHAR(20),                 -- 'cm', 'kg', 'reps', 'seconds', 'bpm'
    pain_during INTEGER,              -- 0-10
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_test_name ON test_results(test_name);
CREATE INDEX IF NOT EXISTS idx_test_date ON test_results(test_date DESC);


-- ============================================
-- GATE ASSESSMENTS (Pass/fail tracking for phase transitions)
-- ============================================
CREATE TABLE IF NOT EXISTS gate_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_number INTEGER NOT NULL,     -- 1, 2, 3, 4
    assessment_date DATE NOT NULL,
    
    -- Individual test results (JSON for flexibility)
    test_results JSON,
    
    -- Overall
    all_passed BOOLEAN,
    tests_passed INTEGER,
    tests_failed INTEGER,
    
    -- Decision
    outcome VARCHAR(20),              -- 'passed', 'failed', 'partial'
    next_action TEXT,
    retest_date DATE,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- CARDIO LOG (For bike sessions, walks, etc.)
-- ============================================
CREATE TABLE IF NOT EXISTS cardio_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    activity_type VARCHAR(30),        -- 'zone2_cycling', 'zone2_walk', 'family_hike', 'vo2max_intervals'
    duration_min INTEGER,
    avg_hr INTEGER,
    max_hr INTEGER,
    avg_power_watts INTEGER,          -- NULL until M3i paired
    avg_cadence INTEGER,              -- NULL until M3i paired
    calories INTEGER,
    distance_km REAL,
    zone_2_minutes INTEGER,           -- Time actually in Zone 2
    garmin_activity_id VARCHAR(50),
    rpe INTEGER,                      -- 1-10
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(garmin_activity_id)
);

CREATE INDEX IF NOT EXISTS idx_cardio_date ON cardio_log(date DESC);
```

---

## 3. PHASE TRACKING CONFIG

Add or update the ATLAS config to include phase tracking:

```json
{
  "current_phase": {
    "phase_number": 1,
    "name": "Foundation & Rehab",
    "start_date": "2026-01-19",
    "current_week": 1,
    "config_file": "config/phases/config_phase1_weeks1-12.json"
  },
  "phase_1_schedule": {
    "start_date": "2026-01-19",
    "deload_weeks": [4, 8],
    "gate_1_target_date": "2026-04-06",
    "weeks_total": 12
  },
  "key_dates": {
    "week_4_deload": "2026-02-09",
    "week_8_deload": "2026-03-09", 
    "week_12_gate1": "2026-04-06"
  }
}
```

This can be stored in `~/.atlas/phase_config.json` or merged into existing config.

---

## 4. VOICE/CLI INTENT PATTERNS

Add these patterns to `bridge_file_server.py` (or wherever intent detection lives):

### Weight Logging (if not already implemented)
```python
WEIGHT_PATTERNS = [
    r"log weight (\d+\.?\d*)",
    r"weight (\d+\.?\d*)",
    r"weigh(ed)? in (\d+\.?\d*)",
    r"(\d+\.?\d*) (kilos?|kg)",
]

async def handle_weight_log(match):
    weight_kg = float(match.group(1))
    # Insert into weight_log table
    # Return: "Logged {weight} kilos"
```

### Workout Lookup by Day
```python
WORKOUT_PATTERNS = [
    r"what'?s (my |today'?s )?workout",
    r"(what|which) (workout|training|session) today",
    r"today'?s (workout|training|session)",
]

async def handle_workout_lookup():
    # Get day of week
    # Load config/phases/config_phase1_weeks1-12.json
    # Return today's workout type, duration, key exercises
    # Include ice bath note if applicable
```

### Baseline/Test Logging
```python
BASELINE_PATTERNS = [
    r"log baseline",
    r"record (baseline|assessment)",
]

TEST_PATTERNS = [
    r"(wblt|lunge test) (left|right) (\d+\.?\d*)",
    r"pushups (\d+)",
    r"plank (\d+)",
    r"log (wblt|balance|plank|pushups|pullups|heel raises) (\d+\.?\d*)",
    r"test result (.+) (\d+\.?\d*)",
]
```

### Cardio Logging
```python
CARDIO_PATTERNS = [
    r"log (cardio|ride|cycling|bike)",
    r"zone 2 (\d+) minutes",
]
```

---

## 5. GARMIN SYNC ON STARTUP

Modify Voice Bridge startup to sync Garmin data fresh each session:

```python
# In bridge_file_server.py startup sequence
async def on_startup():
    """Run when Voice Bridge starts"""
    # Sync Garmin data fresh
    from atlas.health.garmin import GarminService
    garmin = GarminService()
    await garmin.sync_morning_status()  # Updates ~/.atlas/morning_status.json
    
    # Log startup
    print(f"ATLAS started. Garmin synced. Phase 1 Week {get_current_week()}")
```

This replaces the need for a cron job (better for variable wake times with baby).

---

## 6. WORKOUT LOOKUP IMPLEMENTATION

Create a function to read the phase config and return today's workout:

```python
import json
from datetime import datetime

def get_todays_workout():
    """Return today's workout from phase config"""
    
    # Load phase config
    with open('config/phases/config_phase1_weeks1-12.json', 'r') as f:
        config = json.load(f)
    
    # Get day of week (lowercase)
    day = datetime.now().strftime('%A').lower()
    
    # Get workout
    workout = config['weekly_schedule'].get(day)
    
    if not workout:
        return "No workout found for today"
    
    # Format response
    response = f"{workout['type']}: {workout['name']}. {workout['duration_minutes']} minutes."
    
    # Add key exercises (first 3)
    if 'main_workout' in workout and 'exercises' in workout['main_workout']:
        exercises = workout['main_workout']['exercises'][:3]
        exercise_names = [e['name'] for e in exercises]
        response += f" Key exercises: {', '.join(exercise_names)}."
    
    # Add ice bath note
    if workout.get('ice_bath') == 'YES':
        response += " Ice bath optional today."
    
    return response

def get_current_week():
    """Calculate current week number based on start date"""
    from datetime import date
    
    start_date = date(2026, 1, 19)
    today = date.today()
    
    if today < start_date:
        return 0  # Not started yet
    
    days_elapsed = (today - start_date).days
    week = (days_elapsed // 7) + 1
    
    return min(week, 12)  # Cap at 12 for Phase 1

def is_deload_week():
    """Check if current week is a deload week"""
    current_week = get_current_week()
    return current_week in [4, 8]
```

---

## 7. CLI COMMANDS TO ADD

Add these commands to `atlas/health/cli.py`:

```python
# Baseline assessment logging
@cli.command()
@click.argument('assessment_type', default='initial')
def baseline(assessment_type):
    """Log or view baseline assessment"""
    # Interactive prompts for each measurement
    # Or load from JSON file
    pass

# Test result logging  
@cli.command()
@click.argument('test_name')
@click.argument('value', type=float)
@click.option('--pain', type=int, default=0, help='Pain during test 0-10')
def test(test_name, value, pain):
    """Log individual test result"""
    # Insert into test_results table
    pass

# Cardio logging
@cli.command()
@click.option('--type', 'activity_type', default='zone2_cycling')
@click.option('--duration', type=int, required=True)
@click.option('--hr', 'avg_hr', type=int)
@click.option('--power', type=int)
def cardio(activity_type, duration, avg_hr, power):
    """Log cardio session"""
    # Insert into cardio_log table
    pass

# Phase/week check
@cli.command()
def phase():
    """Show current phase and week"""
    week = get_current_week()
    deload = is_deload_week()
    # Return: "Phase 1, Week 3. Normal training." or "Phase 1, Week 4. DELOAD WEEK."
    pass
```

---

## 8. WEIGHT LOGGING (Wire Up)

Ensure weight logging actually works via voice. The schema exists (`weight_log` table from HEALTH_ROUTINE.md), but needs the voice handler:

```python
async def handle_weight_log(weight_kg: float, body_fat_pct: float = None):
    """Log weight to database"""
    import sqlite3
    from datetime import date, datetime
    
    conn = sqlite3.connect('~/.atlas/atlas.db')  # Adjust path
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO weight_log (date, time, weight_kg, body_fat_pct, source)
        VALUES (?, ?, ?, ?, ?)
    ''', (date.today(), datetime.now().time(), weight_kg, body_fat_pct, 'voice'))
    
    conn.commit()
    conn.close()
    
    return f"Logged {weight_kg} kilos"
```

---

## 9. SUMMARY OF TASKS

### Immediate (Before Monday 19th):
1. ✅ Save the two config files to repo
2. ✅ Run SQL schema additions
3. ✅ Add phase config JSON
4. ✅ Implement workout lookup by day
5. ✅ Wire up weight logging voice command
6. ✅ Add Garmin sync on Voice Bridge startup

### After Baseline Testing:
7. Create CLI command to input baseline assessment data
8. Implement baseline comparison (current vs initial)

### Future (When M3i Arrives):
9. Extend cardio_log to auto-import from Garmin activities
10. Parse power/cadence data from paired bike

---

## 10. TESTING CHECKLIST

After implementation, verify:

- [ ] `python -m atlas.health.cli workout` returns Monday's workout
- [ ] "What's my workout" via voice returns correct response
- [ ] `python -m atlas.health.cli weight log 82.3` works
- [ ] "Log weight 82.3" via voice works
- [ ] `python -m atlas.health.cli phase` shows "Phase 1, Week 0" (before Monday)
- [ ] Garmin syncs on Voice Bridge startup
- [ ] Database tables created successfully

---

*Instructions compiled by Claude (Web) for Opus (CLI)*  
*January 16, 2026*
