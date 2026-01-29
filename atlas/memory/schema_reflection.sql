-- ATLAS Reflection & Journal Schema
-- Seneca's Trial and Daily Reflection System
-- SQLite schema for structured self-examination

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ============================================
-- DAILY REFLECTIONS
-- ============================================

-- Main daily reflection entry
CREATE TABLE IF NOT EXISTS daily_reflections (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    reflection_type TEXT NOT NULL,  -- 'evening_audit', 'senecas_trial', 'morning_prep', 'weekly_review'

    -- ============================================
    -- SENECA'S TRIAL STRUCTURE
    -- ============================================

    -- The Prosecution: Where did I fall short?
    prosecution_shortfalls TEXT,  -- What went wrong
    prosecution_vices TEXT,  -- What vices did I indulge
    prosecution_avoidances TEXT,  -- What difficult things did I avoid

    -- The Judgment: What is the truth?
    judgment_in_control TEXT,  -- What was within my control
    judgment_out_of_control TEXT,  -- What was outside my control
    judgment_response_quality TEXT,  -- How well did I respond to what I controlled

    -- The Advocacy: What did I do well?
    advocacy_achievements TEXT,  -- What went well
    advocacy_growth TEXT,  -- What growth did today produce
    advocacy_tomorrow TEXT,  -- What will I do differently tomorrow

    -- ============================================
    -- VIRTUE TRACKING (Franklin-style)
    -- ============================================

    focus_virtue TEXT,  -- Today's virtue focus (from 12 virtues)
    virtue_score INTEGER CHECK(virtue_score BETWEEN 1 AND 10),
    virtue_notes TEXT,

    -- ============================================
    -- MEMENTO MORI
    -- ============================================

    memento_mori_reflection TEXT,  -- "If this were my last day, was it well spent?"
    life_well_spent BOOLEAN,

    -- ============================================
    -- PREMEDITATIO MALORUM (Morning or Evening)
    -- ============================================

    premeditatio_scenario TEXT,  -- What I visualized going wrong
    premeditatio_response TEXT,  -- How I prepared to respond

    -- ============================================
    -- GENERAL REFLECTION
    -- ============================================

    gratitude TEXT,  -- What am I grateful for
    key_learning TEXT,  -- Most important lesson today
    open_questions TEXT,  -- Questions to explore

    -- ============================================
    -- DOMAIN-SPECIFIC REFLECTIONS
    -- ============================================

    -- Fatherhood
    father_reflection TEXT,
    presence_quality INTEGER CHECK(presence_quality BETWEEN 1 AND 10),

    -- Work/Creation (Baby Brains, ATLAS, etc.)
    work_reflection TEXT,
    creation_progress TEXT,

    -- Health/Body
    body_reflection TEXT,
    energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),

    -- Tactical (links to tactical_daily_debrief)
    tactical_debrief_id INTEGER,

    -- ============================================
    -- TOMORROW PREPARATION
    -- ============================================

    tomorrow_must_do TEXT,  -- One non-negotiable
    tomorrow_virtue_focus TEXT,  -- Virtue to focus on
    tomorrow_intention TEXT,  -- Overall intention

    -- ============================================
    -- METADATA
    -- ============================================

    duration_minutes INTEGER,  -- Time spent reflecting
    mood_before INTEGER CHECK(mood_before BETWEEN 1 AND 10),
    mood_after INTEGER CHECK(mood_after BETWEEN 1 AND 10),

    -- XP
    xp_awarded INTEGER DEFAULT 0,
    reflection_depth TEXT,  -- 'quick', 'standard', 'deep' - affects XP

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- WEEKLY REVIEWS
-- ============================================

CREATE TABLE IF NOT EXISTS weekly_reviews (
    id INTEGER PRIMARY KEY,
    week_start DATE NOT NULL UNIQUE,
    week_end DATE NOT NULL,

    -- Week Overview
    week_summary TEXT,
    major_wins TEXT,  -- JSON array
    major_challenges TEXT,  -- JSON array
    lessons_learned TEXT,  -- JSON array

    -- Virtue Analysis
    virtue_scores_summary TEXT,  -- JSON object: {virtue: avg_score}
    strongest_virtue TEXT,
    weakest_virtue TEXT,
    virtue_patterns TEXT,

    -- Domain Reviews
    father_week_summary TEXT,
    work_week_summary TEXT,
    body_week_summary TEXT,
    tactical_week_summary TEXT,

    -- Pattern Recognition
    recurring_shortfalls TEXT,
    improvement_areas TEXT,
    emerging_strengths TEXT,

    -- Next Week
    next_week_focus TEXT,
    next_week_goals TEXT,  -- JSON array
    experiments_to_try TEXT,

    -- XP
    xp_awarded INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- MONTHLY REVIEWS
-- ============================================

CREATE TABLE IF NOT EXISTS monthly_reviews (
    id INTEGER PRIMARY KEY,
    month DATE NOT NULL UNIQUE,  -- First day of month

    -- Month Overview
    month_summary TEXT,
    theme TEXT,  -- Emergent theme of the month

    -- Progress Assessment
    goals_set TEXT,  -- JSON array of goals set at month start
    goals_achieved TEXT,  -- JSON array of achieved
    goals_missed TEXT,  -- JSON array of missed with reasons

    -- Growth Analysis
    character_growth TEXT,
    skill_growth TEXT,
    knowledge_growth TEXT,

    -- Failure Analysis (Tier 2/3 from Failure Codex)
    significant_failures TEXT,  -- JSON array
    failure_learnings TEXT,
    failure_xp_earned INTEGER DEFAULT 0,

    -- Looking Forward
    next_month_intention TEXT,
    adjustments_needed TEXT,

    -- XP
    xp_awarded INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FAILURE CODEX ENTRIES
-- ============================================

-- Structured failure processing (from Lethal Gentleman research)
CREATE TABLE IF NOT EXISTS failure_entries (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    tier INTEGER NOT NULL CHECK(tier BETWEEN 1 AND 3),  -- 1=bad day, 2=missed target, 3=major setback

    -- What happened
    description TEXT NOT NULL,
    category TEXT,  -- 'health', 'work', 'family', 'tactical', 'discipline', 'other'

    -- Tier 1: Bad Day Processing
    acceptance_noted BOOLEAN DEFAULT FALSE,  -- Musashi: "Accept everything just the way it is"
    logged_without_judgment BOOLEAN DEFAULT FALSE,
    single_learning TEXT,

    -- Tier 2: Missed Target Processing
    control_audit_internal TEXT,  -- What was in my control
    control_audit_external TEXT,  -- What was not in my control
    explanatory_permanence TEXT,  -- Is this forever or temporary?
    explanatory_pervasiveness TEXT,  -- Does this ruin everything or just this?
    explanatory_personalization TEXT,  -- Is this all my fault or did factors contribute?
    premeditatio_for_next TEXT,  -- How to respond if this happens again
    target_adjustment_needed BOOLEAN DEFAULT FALSE,

    -- Tier 3: Major Setback Processing
    after_action_what_worked TEXT,
    after_action_what_didnt TEXT,
    after_action_surprises TEXT,
    after_action_hindsight TEXT,
    ptg_appreciation BOOLEAN DEFAULT FALSE,  -- Greater appreciation for life
    ptg_relationships BOOLEAN DEFAULT FALSE,  -- Improved relationships
    ptg_possibilities BOOLEAN DEFAULT FALSE,  -- New possibilities revealed
    ptg_strength BOOLEAN DEFAULT FALSE,  -- New personal strength
    ptg_understanding BOOLEAN DEFAULT FALSE,  -- Changed understanding of what matters
    obstacle_as_path TEXT,  -- How this becomes the training
    musashi_response TEXT,  -- What within me must change

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    days_to_process INTEGER,

    -- XP (Failure XP - processing failure is the rep)
    xp_awarded INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- VIRTUE TRACKING
-- ============================================

-- The 12 Virtues from Lethal Gentleman research
CREATE TABLE IF NOT EXISTS virtue_definitions (
    id INTEGER PRIMARY KEY,
    virtue_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    stoic_source TEXT,  -- Connection to Stoic philosophy
    bushido_source TEXT,  -- Connection to Bushido
    shadow_side TEXT,  -- What this virtue becomes when corrupted
    practices TEXT,  -- JSON array of daily practices
    order_index INTEGER
);

-- Virtue focus tracking (Franklin's weekly focus system)
CREATE TABLE IF NOT EXISTS virtue_focus_weeks (
    id INTEGER PRIMARY KEY,
    week_start DATE NOT NULL,
    virtue_id INTEGER REFERENCES virtue_definitions(id),
    intention TEXT,
    end_of_week_notes TEXT,
    average_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- QUOTES AND WISDOM LIBRARY
-- ============================================

-- Quotes from the masters for reflection prompts
CREATE TABLE IF NOT EXISTS wisdom_quotes (
    id INTEGER PRIMARY KEY,
    source_author TEXT NOT NULL,  -- 'Marcus Aurelius', 'Seneca', 'Musashi', etc.
    source_work TEXT,  -- 'Meditations', 'Letters', 'Dokkōdō', etc.
    quote_text TEXT NOT NULL,
    category TEXT,  -- 'courage', 'discipline', 'reflection', 'adversity', etc.
    virtue_related TEXT,  -- Which virtue this quote relates to
    use_context TEXT,  -- 'morning', 'evening', 'failure', 'success', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- MORNING PROTOCOL TRACKING
-- ============================================

CREATE TABLE IF NOT EXISTS morning_protocols (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Stoic Morning (Marcus Aurelius Meditations 2.1)
    stoic_morning_completed BOOLEAN DEFAULT FALSE,
    stoic_morning_notes TEXT,

    -- Premeditatio Malorum
    premeditatio_completed BOOLEAN DEFAULT FALSE,
    premeditatio_scenario TEXT,
    premeditatio_preparation TEXT,

    -- Arena Question (Franklin + Roosevelt)
    arena_question_completed BOOLEAN DEFAULT FALSE,
    what_good_shall_i_do TEXT,  -- Franklin
    arena_or_stands TEXT,  -- Roosevelt
    todays_virtue_focus TEXT,
    must_happen_today TEXT,

    -- Morning Study (Da Vinci notebook)
    morning_study_completed BOOLEAN DEFAULT FALSE,
    study_topic TEXT,
    idea_captured TEXT,

    -- Physical Preparation
    physical_completed BOOLEAN DEFAULT FALSE,
    physical_type TEXT,  -- 'mobility', 'training', 'cold_exposure'

    -- XP
    total_xp INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- JOURNAL ENTRIES (Free-form)
-- ============================================

-- For longer, unstructured journaling
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    entry_type TEXT DEFAULT 'general',  -- 'general', 'insight', 'dream', 'letter_to_self', 'letter_to_future'

    title TEXT,
    content TEXT NOT NULL,

    tags TEXT,  -- JSON array of tags
    mood TEXT,
    related_reflection_id INTEGER REFERENCES daily_reflections(id),

    -- For letter to future self
    open_date DATE,  -- When this should be revealed
    opened BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FTS for searching journal and reflections
CREATE VIRTUAL TABLE IF NOT EXISTS fts_reflections USING fts5(
    prosecution_shortfalls, advocacy_achievements, key_learning, gratitude,
    content=daily_reflections,
    content_rowid=id
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_journal USING fts5(
    title, content,
    content=journal_entries,
    content_rowid=id
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_reflections_date ON daily_reflections(date);
CREATE INDEX IF NOT EXISTS idx_reflections_type ON daily_reflections(reflection_type);
CREATE INDEX IF NOT EXISTS idx_weekly_reviews_week ON weekly_reviews(week_start);
CREATE INDEX IF NOT EXISTS idx_failure_entries_date ON failure_entries(date);
CREATE INDEX IF NOT EXISTS idx_failure_entries_tier ON failure_entries(tier);
CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(date);
CREATE INDEX IF NOT EXISTS idx_morning_protocols_date ON morning_protocols(date);

-- ============================================
-- INITIAL DATA: VIRTUES
-- ============================================

INSERT OR IGNORE INTO virtue_definitions (virtue_code, name, description, stoic_source, bushido_source, shadow_side, order_index) VALUES
('WISDOM', 'Wisdom', 'Right judgment about what to pursue and avoid', 'Sophia/Phronesis - Cardinal Virtue', 'Gi (Righteousness)', 'Paralysis by analysis, intellectual arrogance', 1),
('COURAGE', 'Courage', 'Action despite fear, not absence of fear', 'Andreia - Cardinal Virtue', 'Yū (Courage)', 'Recklessness, foolhardiness', 2),
('JUSTICE', 'Justice', 'Giving others their due, serving the common good', 'Dikaiosyne - "Source of all virtues" (Marcus)', 'Jin (Benevolence)', 'Self-righteousness, judgmentalism', 3),
('TEMPERANCE', 'Temperance', 'Self-mastery over desires and impulses', 'Sophrosyne - Cardinal Virtue', 'Implicit in all codes', 'Rigidity, joylessness', 4),
('HONOR', 'Honor', 'Internal accountability that requires no audience', 'Arete - Living excellently', 'Meiyo (Honor)', 'Pride, obsession with reputation', 5),
('HONESTY', 'Honesty', 'Truth in word and deed, authenticity', 'Aletheia - Speaking truth', 'Makoto (Sincerity)', 'Brutal honesty that harms, tactlessness', 6),
('INDUSTRY', 'Industry', 'Purposeful effort toward meaningful work', 'Ergon - Function/purpose', 'Implicit in duty', 'Workaholism, neglecting rest', 7),
('HUMILITY', 'Humility', 'Accurate self-assessment, thinking lightly of yourself and deeply of the world', 'Musashi: "Think lightly of yourself"', 'Implicit in service', 'False modesty, self-deprecation', 8),
('LOYALTY', 'Loyalty', 'Faithfulness to commitments and people', 'Implicit in Stoic relationships', 'Chūgi (Loyalty)', 'Blind loyalty, tribalism', 9),
('GENEROSITY', 'Generosity', 'Giving without expectation of return', 'Marcus on service to others', 'Jin (Benevolence)', 'Enabling, martyrdom', 10),
('RESILIENCE', 'Resilience', 'Transforming obstacles into paths', 'Marcus: "The impediment to action advances action"', 'Perseverance in all codes', 'Denial of pain, toxic positivity', 11),
('PRESENCE', 'Presence', 'Full attention to the current moment and those in it', 'Focus on what is "up to us"', 'Zanshin (continuing awareness)', 'Enmeshment, loss of boundaries', 12);

-- ============================================
-- INITIAL DATA: SAMPLE QUOTES
-- ============================================

INSERT OR IGNORE INTO wisdom_quotes (source_author, source_work, quote_text, category, virtue_related, use_context) VALUES
-- Marcus Aurelius
('Marcus Aurelius', 'Meditations 2.1', 'When you wake up in the morning, tell yourself: The people I deal with today will be meddling, ungrateful, arrogant, dishonest, jealous, and surly. They are like this because they can''t tell good from evil. But I have seen the beauty of good, and the ugliness of evil, and have recognized that the wrongdoer has a nature related to my own—not of the same blood or birth, but of the same mind, and possessing a share of the divine. And so none of them can hurt me.', 'morning_preparation', 'WISDOM', 'morning'),
('Marcus Aurelius', 'Meditations', 'You could leave life right now. Let that determine what you do and say and think.', 'mortality', 'PRESENCE', 'evening'),
('Marcus Aurelius', 'Meditations', 'The impediment to action advances action. What stands in the way becomes the way.', 'adversity', 'RESILIENCE', 'failure'),
('Marcus Aurelius', 'Meditations', 'Waste no more time arguing about what a good man should be. Be one.', 'action', 'COURAGE', 'morning'),

-- Seneca
('Seneca', 'Letters', 'We suffer more often in imagination than in reality.', 'fear', 'COURAGE', 'morning'),
('Seneca', 'Letters', 'It is not that we have a short time to live, but that we waste a lot of it.', 'time', 'INDUSTRY', 'morning'),
('Seneca', 'On Anger', 'I will now govern my passions as I would wish other men to govern theirs. I will examine myself every evening, for I mean to make full use of this privilege of self-examination.', 'reflection', 'WISDOM', 'evening'),

-- Musashi
('Miyamoto Musashi', 'Dokkōdō', 'Accept everything just the way it is.', 'acceptance', 'WISDOM', 'failure'),
('Miyamoto Musashi', 'Dokkōdō', 'Think lightly of yourself and deeply of the world.', 'humility', 'HUMILITY', 'morning'),
('Miyamoto Musashi', 'Dokkōdō', 'Never stray from the Way.', 'discipline', 'TEMPERANCE', 'morning'),
('Miyamoto Musashi', 'Book of Five Rings', 'There is nothing outside of yourself that can ever enable you to get better, stronger, richer, quicker, or smarter. Everything is within. Everything exists. Seek nothing outside of yourself.', 'self_reliance', 'INDUSTRY', 'failure'),

-- Roosevelt
('Theodore Roosevelt', 'Citizenship in a Republic', 'It is not the critic who counts; not the man who points out how the strong man stumbles. The credit belongs to the man who is actually in the arena, whose face is marred by dust and sweat and blood.', 'courage', 'COURAGE', 'morning'),

-- Franklin
('Benjamin Franklin', 'Autobiography', 'What good shall I do this day?', 'intention', 'JUSTICE', 'morning'),
('Benjamin Franklin', 'Autobiography', 'What good have I done today?', 'reflection', 'JUSTICE', 'evening'),

-- Epictetus
('Epictetus', 'Enchiridion', 'Make the best use of what is in your power, and take the rest as it happens.', 'control', 'WISDOM', 'morning'),
('Epictetus', 'Discourses', 'It is not things that disturb us, but our judgments about things.', 'perception', 'WISDOM', 'failure'),

-- Jocko Willink
('Jocko Willink', 'Extreme Ownership', 'Discipline equals freedom.', 'discipline', 'TEMPERANCE', 'morning'),
('Jocko Willink', 'Various', 'Good.', 'adversity', 'RESILIENCE', 'failure');
