-- ATLAS Tactical Curriculum Schema
-- The Lethal Gentleman's Curriculum
-- SQLite schema for tracking tactical training progression

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ============================================
-- CURRICULUM STRUCTURE
-- ============================================

-- Phases of the curriculum (Core, Intermediate, Advanced, Maintenance)
CREATE TABLE IF NOT EXISTS tactical_phases (
    id INTEGER PRIMARY KEY,
    phase_number INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    duration_weeks INTEGER,
    prerequisites TEXT,  -- JSON array of phase IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Modules within each phase
CREATE TABLE IF NOT EXISTS tactical_modules (
    id INTEGER PRIMARY KEY,
    phase_id INTEGER REFERENCES tactical_phases(id),
    module_code TEXT UNIQUE NOT NULL,  -- e.g., 'AWARE-001', 'COMBAT-003'
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,  -- 'awareness', 'physical', 'technical', 'medical', 'mindset', 'evasion'
    prerequisites TEXT,  -- JSON array of module_codes
    estimated_hours REAL,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual lessons within modules
CREATE TABLE IF NOT EXISTS tactical_lessons (
    id INTEGER PRIMARY KEY,
    module_id INTEGER REFERENCES tactical_modules(id),
    lesson_code TEXT UNIQUE NOT NULL,  -- e.g., 'AWARE-001-03'
    title TEXT NOT NULL,

    -- Content
    content_md TEXT NOT NULL,  -- Markdown lesson content
    key_concepts TEXT,  -- JSON array of key takeaways
    source_references TEXT,  -- JSON array of source citations
    quotes TEXT,  -- JSON array of relevant quotes from masters

    -- Practical components
    drill_assignment TEXT,  -- What to practice today
    drill_type TEXT,  -- 'observation', 'physical', 'mental', 'scenario', 'build'
    observation_task TEXT,  -- Awareness exercise for the day
    physical_drill TEXT,  -- Physical practice if applicable
    scenario_prompt TEXT,  -- Mental rehearsal scenario

    -- Media
    diagrams TEXT,  -- JSON array of diagram file paths
    video_links TEXT,  -- JSON array of external video references

    -- Metadata
    difficulty INTEGER CHECK(difficulty BETWEEN 1 AND 5),
    estimated_minutes INTEGER,
    requires_equipment TEXT,  -- JSON array of equipment needed
    requires_partner BOOLEAN DEFAULT FALSE,
    order_index INTEGER,

    -- XP
    xp_lesson INTEGER DEFAULT 25,  -- XP for completing lesson
    xp_drill INTEGER DEFAULT 15,  -- XP for completing drill
    skill_credited TEXT DEFAULT 'learning',  -- Which skill gets XP

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- USER PROGRESS TRACKING
-- ============================================

-- User's progress through lessons
CREATE TABLE IF NOT EXISTS tactical_progress (
    id INTEGER PRIMARY KEY,
    lesson_id INTEGER REFERENCES tactical_lessons(id),

    -- Completion tracking
    started_at TIMESTAMP,
    lesson_completed_at TIMESTAMP,
    drill_completed_at TIMESTAMP,

    -- Quality tracking
    comprehension_rating INTEGER CHECK(comprehension_rating BETWEEN 1 AND 5),
    drill_notes TEXT,
    questions TEXT,  -- Questions that arose during lesson

    -- XP awarded
    xp_awarded INTEGER DEFAULT 0,

    -- Spaced repetition for retention
    next_review_date DATE,
    review_count INTEGER DEFAULT 0,
    retention_score REAL DEFAULT 1.0,

    UNIQUE(lesson_id)
);

-- Quiz/assessment results
CREATE TABLE IF NOT EXISTS tactical_assessments (
    id INTEGER PRIMARY KEY,
    assessment_type TEXT NOT NULL,  -- 'quiz', 'scenario', 'physical', 'practical'
    assessment_code TEXT,  -- Links to specific assessment
    module_id INTEGER REFERENCES tactical_modules(id),

    -- Results
    date_taken DATE NOT NULL,
    score INTEGER,  -- Percentage or points
    max_score INTEGER,
    passed BOOLEAN,

    -- Details
    results_json TEXT,  -- Detailed breakdown
    notes TEXT,
    time_taken_seconds INTEGER,

    -- XP
    xp_awarded INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PHYSICAL BENCHMARKS
-- ============================================

-- Military-style physical fitness tracking
CREATE TABLE IF NOT EXISTS tactical_physical_benchmarks (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    benchmark_type TEXT NOT NULL,  -- 'baseline', 'monthly', 'quarterly'

    -- Standard PT tests
    pushups_2min INTEGER,
    situps_2min INTEGER,
    pullups_max INTEGER,
    run_1_5_mile_seconds INTEGER,
    plank_seconds INTEGER,
    sprint_400m_seconds INTEGER,

    -- Combat-relevant tests
    burpees_2min INTEGER,
    farmers_carry_meters REAL,  -- With specified weight
    farmers_carry_weight_kg REAL,
    dead_hang_seconds INTEGER,
    grip_strength_kg REAL,

    -- Standards comparison
    meets_army_standard BOOLEAN,
    meets_ranger_standard BOOLEAN,
    meets_sf_standard BOOLEAN,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DRILL AND PRACTICE LOG
-- ============================================

-- Log of all drills and practice sessions
CREATE TABLE IF NOT EXISTS tactical_drill_log (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    lesson_id INTEGER REFERENCES tactical_lessons(id),

    drill_type TEXT NOT NULL,  -- 'observation', 'physical', 'scenario', 'equipment', 'build'
    drill_description TEXT,
    duration_minutes INTEGER,

    -- Outcomes
    completed BOOLEAN DEFAULT TRUE,
    quality_rating INTEGER CHECK(quality_rating BETWEEN 1 AND 5),
    observations TEXT,  -- What was noticed/learned

    -- For scenario drills
    scenario_description TEXT,
    response_taken TEXT,
    lessons_learned TEXT,

    -- XP
    xp_awarded INTEGER DEFAULT 0,
    skill_credited TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EQUIPMENT TRACKING
-- ============================================

-- Equipment inventory for training and preparedness
CREATE TABLE IF NOT EXISTS tactical_equipment (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,  -- 'medical', 'communication', 'detection', 'protection', 'tools'
    name TEXT NOT NULL,
    description TEXT,

    -- Status
    owned BOOLEAN DEFAULT FALSE,
    location TEXT,  -- Where it's stored
    condition TEXT,  -- 'new', 'good', 'fair', 'replace'

    -- Maintenance
    last_checked DATE,
    next_check_date DATE,
    expiry_date DATE,  -- For medical supplies, batteries, etc.

    -- Acquisition
    priority INTEGER CHECK(priority BETWEEN 1 AND 5),  -- 1 = must have, 5 = nice to have
    estimated_cost_aud REAL,
    purchase_link TEXT,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SCENARIO LIBRARY
-- ============================================

-- Pre-built scenarios for mental rehearsal
CREATE TABLE IF NOT EXISTS tactical_scenarios (
    id INTEGER PRIMARY KEY,
    scenario_code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'family_protection', 'home_defense', 'public_space', 'vehicle', 'evasion'

    -- Scenario content
    setup TEXT NOT NULL,  -- The situation description
    variables TEXT,  -- JSON array of variable factors
    decision_points TEXT,  -- JSON array of key decision moments
    optimal_responses TEXT,  -- JSON array of recommended actions
    common_mistakes TEXT,  -- JSON array of what to avoid

    -- Metadata
    difficulty INTEGER CHECK(difficulty BETWEEN 1 AND 5),
    with_family BOOLEAN DEFAULT FALSE,
    time_pressure TEXT,  -- 'immediate', 'seconds', 'minutes', 'planning'

    source_reference TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User's scenario practice log
CREATE TABLE IF NOT EXISTS tactical_scenario_practice (
    id INTEGER PRIMARY KEY,
    scenario_id INTEGER REFERENCES tactical_scenarios(id),
    date DATE NOT NULL,

    -- Response
    response_description TEXT,
    decision_analysis TEXT,

    -- Assessment
    response_quality INTEGER CHECK(response_quality BETWEEN 1 AND 5),
    time_to_decision_seconds INTEGER,
    lessons_learned TEXT,

    -- XP
    xp_awarded INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DAILY REFLECTION INTEGRATION
-- ============================================

-- Daily tactical debrief (integrates with evening reflection)
CREATE TABLE IF NOT EXISTS tactical_daily_debrief (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Today's lesson
    lesson_id INTEGER REFERENCES tactical_lessons(id),
    lesson_completed BOOLEAN DEFAULT FALSE,

    -- Observation drill
    observation_task TEXT,
    observations_made TEXT,
    anomalies_noticed TEXT,

    -- Physical training
    physical_drill_completed BOOLEAN DEFAULT FALSE,
    physical_notes TEXT,

    -- Mental rehearsal
    scenario_practiced TEXT,
    scenario_notes TEXT,

    -- General debrief
    situational_awareness_rating INTEGER CHECK(situational_awareness_rating BETWEEN 1 AND 5),
    security_posture_notes TEXT,
    areas_for_improvement TEXT,
    questions_for_next_session TEXT,

    -- XP
    total_xp_today INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SPACED REPETITION FOR RETENTION
-- ============================================

-- Critical knowledge that needs periodic review
CREATE TABLE IF NOT EXISTS tactical_retention_items (
    id INTEGER PRIMARY KEY,
    item_type TEXT NOT NULL,  -- 'concept', 'procedure', 'technique', 'protocol'
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- The knowledge to retain

    -- Spaced repetition parameters (FSRS-like)
    stability REAL DEFAULT 1.0,
    difficulty REAL DEFAULT 0.3,
    next_review_date DATE,
    last_review_date DATE,
    review_count INTEGER DEFAULT 0,

    -- Source
    lesson_id INTEGER REFERENCES tactical_lessons(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review log
CREATE TABLE IF NOT EXISTS tactical_retention_reviews (
    id INTEGER PRIMARY KEY,
    item_id INTEGER REFERENCES tactical_retention_items(id),
    review_date DATE NOT NULL,

    -- Performance
    recalled BOOLEAN,
    confidence INTEGER CHECK(confidence BETWEEN 1 AND 5),

    -- New scheduling
    new_stability REAL,
    new_next_review DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PROJECT BUILDS (DIY Electronics, etc.)
-- ============================================

-- DIY project tracking
CREATE TABLE IF NOT EXISTS tactical_projects (
    id INTEGER PRIMARY KEY,
    project_code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'detection', 'communication', 'security', 'medical', 'power'

    -- Project details
    description TEXT,
    purpose TEXT,
    difficulty INTEGER CHECK(difficulty BETWEEN 1 AND 5),
    estimated_hours REAL,
    estimated_cost_aud REAL,

    -- Requirements
    parts_list TEXT,  -- JSON array of parts with sources
    tools_required TEXT,  -- JSON array
    skills_required TEXT,  -- JSON array

    -- Instructions
    instructions_md TEXT,  -- Full build instructions in markdown
    schematics TEXT,  -- JSON array of schematic file paths

    -- Progress
    status TEXT DEFAULT 'not_started',  -- 'not_started', 'in_progress', 'completed', 'tested'
    started_date DATE,
    completed_date DATE,

    -- XP
    xp_value INTEGER DEFAULT 100,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_tactical_lessons_module ON tactical_lessons(module_id);
CREATE INDEX IF NOT EXISTS idx_tactical_progress_lesson ON tactical_progress(lesson_id);
CREATE INDEX IF NOT EXISTS idx_tactical_progress_next_review ON tactical_progress(next_review_date);
CREATE INDEX IF NOT EXISTS idx_tactical_drill_log_date ON tactical_drill_log(date);
CREATE INDEX IF NOT EXISTS idx_tactical_debrief_date ON tactical_daily_debrief(date);
CREATE INDEX IF NOT EXISTS idx_tactical_retention_next_review ON tactical_retention_items(next_review_date);
CREATE INDEX IF NOT EXISTS idx_tactical_physical_date ON tactical_physical_benchmarks(date);

-- ============================================
-- INITIAL DATA: PHASES
-- ============================================

INSERT OR IGNORE INTO tactical_phases (phase_number, name, description, duration_weeks) VALUES
(1, 'Core Foundation', 'Essential knowledge and awareness. Legal framework, mindset, basic threat assessment, fundamental physical skills.', 12),
(2, 'Intermediate Development', 'Deeper tactical knowledge. Advanced awareness, physical capability, technical skills, scenario mastery.', 12),
(3, 'Advanced Integration', 'Specialist knowledge. Electronic countermeasures, advanced evasion, complex scenarios, teaching capability.', 12),
(4, 'Maintenance', 'Ongoing skill retention. New content, periodic assessment, continuous improvement.', NULL);

-- ============================================
-- INITIAL DATA: MODULE CATEGORIES
-- ============================================

-- Phase 1 Modules (to be populated with lessons from research)
INSERT OR IGNORE INTO tactical_modules (phase_id, module_code, title, category, order_index) VALUES
-- Phase 1: Core Foundation
(1, 'LEGAL-001', 'Legal Framework for Self-Defense (QLD)', 'mindset', 1),
(1, 'MINDSET-001', 'Combat Mindset Fundamentals', 'mindset', 2),
(1, 'AWARE-001', 'Situational Awareness Basics', 'awareness', 3),
(1, 'VIOLENCE-001', 'Violence Dynamics', 'awareness', 4),
(1, 'PHYSICAL-001', 'Physical Combat Fundamentals', 'physical', 5),
(1, 'MEDICAL-001', 'Trauma Response Basics', 'medical', 6),
(1, 'HOME-001', 'Home Security Fundamentals', 'technical', 7),
(1, 'FAMILY-001', 'Family Protection Scenarios', 'awareness', 8),

-- Phase 2: Intermediate
(2, 'AWARE-002', 'Pre-Attack Indicators (Left of Bang)', 'awareness', 1),
(2, 'PHYSICAL-002', 'Weapon Defense', 'physical', 2),
(2, 'EVASION-001', 'Urban Evasion Fundamentals', 'evasion', 3),
(2, 'TECH-001', 'Electronic Surveillance Detection', 'technical', 4),
(2, 'COMMS-001', 'Communications Security', 'technical', 5),
(2, 'MEDICAL-002', 'Advanced Trauma Care', 'medical', 6),
(2, 'VEHICLE-001', 'Vehicle Security and Tactics', 'awareness', 7),

-- Phase 3: Advanced
(3, 'TECH-002', 'Counter-Drone and Aerial Threats', 'technical', 1),
(3, 'TECH-003', 'Directed Energy Awareness', 'technical', 2),
(3, 'TECH-004', 'EMP Protection', 'technical', 3),
(3, 'DIY-001', 'DIY Security Electronics', 'technical', 4),
(3, 'EVASION-002', 'Advanced Counter-Surveillance', 'evasion', 5),
(3, 'THERMAL-001', 'Thermal/IR Awareness and Evasion', 'technical', 6),
(3, 'SCENARIO-001', 'Complex Scenario Mastery', 'awareness', 7);
