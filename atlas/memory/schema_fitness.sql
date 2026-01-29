-- ATLAS Fitness Schema Extension
-- Extends base schema with assessment, pain tracking, and phase management

-- ============================================
-- DAILY PAIN TRACKING
-- ============================================

-- Track pain levels for each body area daily
CREATE TABLE IF NOT EXISTS pain_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    body_part TEXT NOT NULL,  -- 'shoulder_right', 'ankle_left', 'lower_back', 'feet'
    pain_level INTEGER CHECK(pain_level BETWEEN 0 AND 10),
    stiffness_level INTEGER CHECK(stiffness_level BETWEEN 0 AND 10),
    stiffness_duration_minutes INTEGER,  -- How long morning stiffness lasts
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, body_part)
);

-- ============================================
-- FITNESS ASSESSMENTS
-- ============================================

-- Assessment types and their target values
CREATE TABLE IF NOT EXISTS assessment_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,  -- 'strength', 'power', 'mobility', 'stability', 'cardio'
    unit TEXT,  -- 'kg', 'cm', 'seconds', 'reps', 'bpm'
    description TEXT,
    target_value REAL,  -- Goal to work towards
    min_acceptable REAL,  -- Minimum acceptable value
    higher_is_better BOOLEAN DEFAULT TRUE,
    retest_weeks INTEGER DEFAULT 4,  -- How often to retest
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual assessment results
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_type_id INTEGER REFERENCES assessment_types(id),
    date DATE NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    notes TEXT,
    is_baseline BOOLEAN DEFAULT FALSE,  -- First test of this type
    phase TEXT,  -- 'phase_1', 'phase_2', 'phase_3'
    protocol_run TEXT,  -- 'baseline_2026_q1', 'retest_2026_q2', 'gate_1_2026_03', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TRAINING PHASES
-- ============================================

-- Phase definitions
CREATE TABLE IF NOT EXISTS training_phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- 'phase_1', 'phase_2', 'phase_3'
    display_name TEXT NOT NULL,  -- 'Foundation', 'Build', 'Develop'
    weeks_min INTEGER NOT NULL,
    weeks_max INTEGER,
    focus TEXT,
    intensity_range TEXT,  -- 'RPE 5-6', 'RPE 6-7'
    volume_description TEXT,
    progression_criteria TEXT,  -- JSON with criteria to advance
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User's phase history
CREATE TABLE IF NOT EXISTS phase_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER REFERENCES training_phases(id),
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT DEFAULT 'active',  -- 'active', 'completed', 'regressed'
    exit_reason TEXT,  -- 'progression', 'regression', 'injury'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EXERCISE DATABASE
-- ============================================

-- Comprehensive exercise library
CREATE TABLE IF NOT EXISTS exercises (
    id TEXT PRIMARY KEY,  -- 'trap_bar_deadlift', 'goblet_squat'
    name TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'compound', 'isolation', 'cardio', 'mobility', 'rehab'
    primary_muscles TEXT,  -- JSON array
    secondary_muscles TEXT,  -- JSON array
    equipment TEXT,  -- JSON array
    contraindications TEXT,  -- JSON array of conditions
    injury_modifications TEXT,  -- JSON object with modifications per injury
    cues TEXT,  -- JSON array of coaching cues
    video_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exercise progressions per phase
CREATE TABLE IF NOT EXISTS exercise_progressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id TEXT REFERENCES exercises(id),
    phase TEXT NOT NULL,  -- 'phase_1', 'phase_2', 'phase_3'
    sets INTEGER,
    reps TEXT,  -- '10-12' or '8,8,6'
    rpe INTEGER CHECK(rpe BETWEEN 1 AND 10),
    tempo TEXT,  -- '2-1-2-0' (eccentric-pause-concentric-pause)
    rest_seconds INTEGER,
    notes TEXT,
    UNIQUE(exercise_id, phase)
);

-- ============================================
-- WORKOUT EXTENSIONS
-- ============================================

-- Add RPE and traffic light to workout_exercises
-- (These would be added via ALTER TABLE in migration, but showing structure)

-- Extended workout logging with RPE
CREATE TABLE IF NOT EXISTS workout_exercise_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_exercise_id INTEGER REFERENCES workout_exercises(id) ON DELETE CASCADE,
    set_number INTEGER NOT NULL,
    reps_target INTEGER,
    reps_actual INTEGER,
    weight_kg REAL,
    rpe INTEGER CHECK(rpe BETWEEN 1 AND 10),
    tempo_achieved BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- RECALIBRATION ALERTS
-- ============================================

CREATE TABLE IF NOT EXISTS recalibration_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    alert_type TEXT NOT NULL,  -- 'pause_reassess', 'regress_phase', 'medical_referral'
    trigger_reason TEXT NOT NULL,
    details TEXT,  -- JSON with specifics
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_date DATE,
    action_taken TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- WEIGHT TRACKING
-- ============================================

CREATE TABLE IF NOT EXISTS weight_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    time TIME,
    weight_kg REAL NOT NULL CHECK(weight_kg BETWEEN 20 AND 300),
    body_fat_pct REAL CHECK(body_fat_pct IS NULL OR body_fat_pct BETWEEN 1 AND 70),
    muscle_mass_pct REAL CHECK(muscle_mass_pct IS NULL OR muscle_mass_pct BETWEEN 10 AND 70),
    water_pct REAL CHECK(water_pct IS NULL OR water_pct BETWEEN 30 AND 80),
    bone_mass_kg REAL CHECK(bone_mass_kg IS NULL OR bone_mass_kg BETWEEN 1 AND 10),
    visceral_fat INTEGER CHECK(visceral_fat IS NULL OR visceral_fat BETWEEN 1 AND 59),
    bmi REAL CHECK(bmi IS NULL OR bmi BETWEEN 10 AND 60),
    bmr INTEGER CHECK(bmr IS NULL OR bmr BETWEEN 800 AND 4000),
    source VARCHAR(20) DEFAULT 'manual',  -- manual, voice
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, time)
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_weight_log_date ON weight_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_pain_log_date ON pain_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_pain_log_body_part ON pain_log(body_part);
CREATE INDEX IF NOT EXISTS idx_assessments_date ON assessments(date DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_type ON assessments(assessment_type_id);
CREATE INDEX IF NOT EXISTS idx_phase_history_active ON phase_history(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_exercises_category ON exercises(category);

-- ============================================
-- SEED DATA: Assessment Types
-- ============================================

INSERT OR IGNORE INTO assessment_types (name, category, unit, description, target_value, min_acceptable, higher_is_better, retest_weeks) VALUES
-- Strength
('trap_bar_deadlift_5rm', 'strength', 'kg', 'Trap bar deadlift 5 rep max', 120, 60, 1, 4),
('goblet_squat_10rm', 'strength', 'kg', 'Goblet squat 10 rep max', 32, 16, 1, 4),
('floor_press_10rm', 'strength', 'kg', 'Floor press 10 rep max', 30, 15, 1, 4),

-- Mobility
('ankle_dorsiflexion_left', 'mobility', 'cm', 'Knee to wall test - left ankle', 12, 8, 1, 4),
('ankle_dorsiflexion_right', 'mobility', 'cm', 'Knee to wall test - right ankle', 12, 8, 1, 4),
('shoulder_flexion_right', 'mobility', 'degrees', 'Overhead reach - right arm', 180, 150, 1, 4),
('hip_flexor_length_left', 'mobility', 'score', 'Thomas test score 1-5', 5, 3, 1, 4),
('hip_flexor_length_right', 'mobility', 'score', 'Thomas test score 1-5', 5, 3, 1, 4),
('toe_touch', 'mobility', 'cm', 'Distance past toes (negative = cant reach)', 5, -10, 1, 4),
('great_toe_extension', 'mobility', 'degrees', 'Big toe extension range', 70, 45, 1, 4),

-- Stability
('single_leg_balance_left_eo', 'stability', 'seconds', 'Single leg balance eyes open - left', 60, 30, 1, 4),
('single_leg_balance_right_eo', 'stability', 'seconds', 'Single leg balance eyes open - right', 60, 30, 1, 4),
('single_leg_balance_left_ec', 'stability', 'seconds', 'Single leg balance eyes closed - left', 30, 10, 1, 4),
('single_leg_balance_right_ec', 'stability', 'seconds', 'Single leg balance eyes closed - right', 30, 10, 1, 4),
('mcgill_curlup', 'stability', 'seconds', 'McGill curl-up hold', 60, 30, 1, 4),
('side_plank_left', 'stability', 'seconds', 'Side plank hold - left', 60, 30, 1, 4),
('side_plank_right', 'stability', 'seconds', 'Side plank hold - right', 60, 30, 1, 4),

-- Cardio
('resting_hr', 'cardio', 'bpm', 'Resting heart rate', 55, 70, 0, 4),
('hr_recovery_1min', 'cardio', 'bpm', 'HR drop after 1 min post-exercise', 25, 12, 1, 4),

-- Power (Phase 2+)
('vertical_jump', 'power', 'cm', 'Countermovement vertical jump', 45, 30, 1, 4),
('broad_jump', 'power', 'cm', 'Standing broad jump', 200, 150, 1, 4);

-- ============================================
-- SEED DATA: Training Phases
-- ============================================

INSERT OR IGNORE INTO training_phases (name, display_name, weeks_min, weeks_max, focus, intensity_range, volume_description, progression_criteria) VALUES
('phase_1', 'Foundation', 4, 6, 'Movement quality, pain reduction, tissue tolerance', 'RPE 5-6', '2-3 sets, 10-15 reps, 60-90s rest', '{"min_red_days_per_week": 2, "max_pain_level": 3, "required_tests": ["single_leg_balance", "ankle_dorsiflexion"]}'),
('phase_2', 'Build', 4, 6, 'Progressive overload, strength foundation', 'RPE 6-7', '3-4 sets, 8-12 reps, 90-120s rest', '{"min_red_days_per_week": 2, "max_pain_level": 2, "strength_increase_pct": 10}'),
('phase_3', 'Develop', 4, 8, 'Strength development, power introduction', 'RPE 7-8', '4 sets, 6-10 reps strength / 3x5 power, 2-3min rest', '{"min_red_days_per_week": 1, "max_pain_level": 2, "strength_increase_pct": 15}');

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


-- ============================================
-- VOICE ASSESSMENT SESSION STATE
-- ============================================
-- Persists current position for pause/resume functionality
-- Uses test_id instead of indices for robustness against config changes

CREATE TABLE IF NOT EXISTS assessment_session_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,           -- 'A', 'B', 'C' or quick protocol name
    current_test_id TEXT NOT NULL,      -- test_id from protocol_voice.json
    started_at TEXT NOT NULL,           -- ISO timestamp
    updated_at TEXT NOT NULL,           -- ISO timestamp
    results_logged INTEGER DEFAULT 0,   -- Count of tests completed
    last_value TEXT,                    -- JSON of last recorded value (for undo)
    last_test_id TEXT,                  -- test_id of last recorded (for undo)
    notes TEXT,                         -- Session-level notes
    UNIQUE(session_id)                  -- One active session per session type
);

-- Store individual results during session (before committing to assessments table)
CREATE TABLE IF NOT EXISTS assessment_session_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_state_id INTEGER REFERENCES assessment_session_state(id) ON DELETE CASCADE,
    test_id TEXT NOT NULL,
    value TEXT NOT NULL,                -- JSON for compound values
    unit TEXT,
    attempt_number INTEGER DEFAULT 1,   -- For multi-attempt tests
    recorded_at TEXT NOT NULL,
    UNIQUE(session_state_id, test_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS idx_session_state_updated ON assessment_session_state(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_results_test ON assessment_session_results(test_id);


-- ============================================
-- WORKOUT HR DATA (Garmin Activity Sync)
-- ============================================
-- Stores HR metrics from Garmin activities linked to workouts
-- Enables trend analysis: "Your avg HR during strength dropped from 135 to 122"

CREATE TABLE IF NOT EXISTS workout_hr_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
    garmin_activity_id TEXT UNIQUE,     -- Garmin's activity ID for dedup
    activity_type TEXT,                  -- 'strength_training', 'cycling', 'running'
    activity_name TEXT,                  -- User's activity name from Garmin
    avg_hr INTEGER,
    max_hr INTEGER,
    calories INTEGER,
    duration_minutes INTEGER,
    distance_meters REAL,
    start_time TEXT,                     -- ISO timestamp from Garmin
    recorded_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_workout_hr_workout ON workout_hr_data(workout_id);
CREATE INDEX IF NOT EXISTS idx_workout_hr_type ON workout_hr_data(activity_type);
CREATE INDEX IF NOT EXISTS idx_workout_hr_date ON workout_hr_data(start_time DESC);


-- ============================================
-- PROGRESSIVE OVERLOAD TRACKING
-- ============================================
-- Tracks recommended vs actual weights for progression analysis
-- Used by ProgressionService for:
-- - Starting weight derivation from baselines
-- - Double progression triggers (all sets hit top of range)
-- - Deload detection (cooldown tracking)
-- - 1RM estimation over time

CREATE TABLE IF NOT EXISTS exercise_progression_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id TEXT NOT NULL,                -- 'goblet_squat', 'floor_press', etc.
    date DATE NOT NULL,
    recommended_weight_kg REAL,               -- What ProgressionService recommended
    actual_weight_kg REAL,                    -- What user actually used
    recommended_reps INTEGER,                 -- Target reps
    actual_reps_avg REAL,                     -- Average reps achieved
    basis TEXT,                               -- 'baseline_1rm', 'last_workout', 'deload', 'derived'
    one_rm_estimate REAL,                     -- Brzycki 1RM estimate from this session
    UNIQUE(exercise_id, date)
);

CREATE INDEX IF NOT EXISTS idx_progression_exercise ON exercise_progression_log(exercise_id);
CREATE INDEX IF NOT EXISTS idx_progression_date ON exercise_progression_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_progression_basis ON exercise_progression_log(basis);
