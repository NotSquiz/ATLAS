-- ATLAS Memory Schema
-- SQLite + sqlite-vec + FTS5

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ============================================
-- SEMANTIC MEMORY (for AI context/retrieval)
-- ============================================

CREATE TABLE IF NOT EXISTS semantic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5 CHECK(importance >= 0 AND importance <= 1),
    memory_type TEXT DEFAULT 'general',  -- 'general', 'fact', 'preference', 'event'
    source TEXT,  -- where this memory came from
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

-- Vector index for semantic search (sqlite-vec)
-- 384 dimensions for BGE-small-en-v1.5
CREATE VIRTUAL TABLE IF NOT EXISTS vec_semantic USING vec0(
    memory_id INTEGER PRIMARY KEY,
    embedding float[384]
);

-- Full-text search index (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS fts_memory USING fts5(
    content,
    content=semantic_memory,
    content_rowid=id
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS semantic_memory_ai AFTER INSERT ON semantic_memory BEGIN
    INSERT INTO fts_memory(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS semantic_memory_ad AFTER DELETE ON semantic_memory BEGIN
    INSERT INTO fts_memory(fts_memory, rowid, content) VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS semantic_memory_au AFTER UPDATE ON semantic_memory BEGIN
    INSERT INTO fts_memory(fts_memory, rowid, content) VALUES('delete', old.id, old.content);
    INSERT INTO fts_memory(rowid, content) VALUES (new.id, new.content);
END;

-- ============================================
-- BLUEPRINT TRACKING (health/fitness data)
-- ============================================

-- Daily biomarkers and measurements
CREATE TABLE IF NOT EXISTS daily_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,

    -- Sleep (from Garmin)
    sleep_hours REAL,
    sleep_score INTEGER CHECK(sleep_score >= 0 AND sleep_score <= 100),
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,

    -- Heart metrics (from Garmin)
    resting_hr INTEGER,
    hrv_avg INTEGER,
    hrv_morning INTEGER,
    hrv_status TEXT,  -- "BALANCED", "UNBALANCED", "LOW"
    body_battery INTEGER CHECK(body_battery >= 0 AND body_battery <= 100),

    -- Body
    weight_kg REAL,
    body_fat_pct REAL,

    -- Subjective
    energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
    mood INTEGER CHECK(mood BETWEEN 1 AND 10),
    stress_level INTEGER CHECK(stress_level BETWEEN 1 AND 10),

    -- Notes
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplement/herb tracking
CREATE TABLE IF NOT EXISTS supplements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    dosage TEXT,
    timing TEXT,  -- 'morning', 'with_meal', 'before_bed'
    purpose TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS supplement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplement_id INTEGER REFERENCES supplements(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    time TIME,
    taken BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workout tracking
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    type TEXT,  -- 'strength', 'cardio', 'mobility', 'rehab'
    duration_minutes INTEGER,
    notes TEXT,
    energy_before INTEGER CHECK(energy_before BETWEEN 1 AND 10),
    energy_after INTEGER CHECK(energy_after BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_id TEXT NOT NULL,
    exercise_name TEXT NOT NULL,

    -- For strength exercises
    sets INTEGER,
    reps TEXT,  -- '8,8,6' for multiple sets
    weight_kg REAL,

    -- For cardio/timed exercises
    duration_seconds INTEGER,
    distance_meters REAL,

    notes TEXT,
    order_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blood work / lab results
CREATE TABLE IF NOT EXISTS lab_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_date DATE NOT NULL,
    marker TEXT NOT NULL,  -- 'vitamin_d', 'testosterone', 'hba1c'
    value REAL NOT NULL,
    unit TEXT,
    reference_low REAL,
    reference_high REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Injuries tracking
CREATE TABLE IF NOT EXISTS injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    body_part TEXT NOT NULL,  -- 'shoulder', 'lower_back'
    side TEXT,  -- 'left', 'right', 'both', NULL
    description TEXT,
    onset_date DATE,
    severity INTEGER CHECK(severity BETWEEN 1 AND 5),
    status TEXT DEFAULT 'active',  -- 'active', 'recovering', 'resolved'
    contraindicated_exercises TEXT,  -- JSON array
    rehab_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_semantic_memory_type ON semantic_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_semantic_memory_importance ON semantic_memory(importance DESC);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_supplement_log_date ON supplement_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(date DESC);
CREATE INDEX IF NOT EXISTS idx_lab_results_date ON lab_results(test_date DESC);
CREATE INDEX IF NOT EXISTS idx_injuries_status ON injuries(status);
