-- ATLAS Gamification Schema
-- 12-Skill Lethal Gentleman Framework
-- BODY (4) + MIND (4) + SOUL (4) = 12 Skills
--
-- Design principles (from verification review):
-- - Atomic: Transactions for xp_events + player_skills
-- - Validated: Constraints prevent invalid data
-- - Auditable: xp_events provides full history
-- - Reconcilable: SUM(xp_events) should equal player_skills.current_xp
--
-- Source: docs/OSRS/The Lethal Gentleman - Research Synthesis.md

-- ============================================
-- PLAYER SKILLS (12-Skill Framework)
-- ============================================

-- Current skill levels and XP totals
-- Seeded with all 12 skills at initialization
CREATE TABLE IF NOT EXISTS player_skills (
    skill_name TEXT PRIMARY KEY,
    domain TEXT NOT NULL CHECK(domain IN ('body', 'mind', 'soul')),
    virtue TEXT NOT NULL,
    shadow_warning TEXT,
    current_xp INTEGER DEFAULT 0
        CHECK(current_xp >= 0 AND current_xp <= 15000000),
    current_level INTEGER DEFAULT 1
        CHECK(current_level >= 1 AND current_level <= 99),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed all 12 skills (Lethal Gentleman Framework)
-- BODY (The Vessel) - 4 Skills
INSERT OR IGNORE INTO player_skills (skill_name, domain, virtue, shadow_warning, current_xp, current_level) VALUES
    ('strength', 'body', 'Power', 'Brutality without control', 0, 1),
    ('endurance', 'body', 'Grit', 'Self-destruction', 0, 1),
    ('mobility', 'body', 'Readiness', 'Preparation as procrastination', 0, 1),
    ('nutrition', 'body', 'Temperance', 'Orthorexia', 0, 1);

-- MIND (The Citadel) - 4 Skills
INSERT OR IGNORE INTO player_skills (skill_name, domain, virtue, shadow_warning, current_xp, current_level) VALUES
    ('focus', 'mind', 'Clarity', 'Obsession without perspective', 0, 1),
    ('learning', 'mind', 'Wisdom', 'Intellectual vanity', 0, 1),
    ('reflection', 'mind', 'Self-Knowledge', 'Rumination without action', 0, 1),
    ('creation', 'mind', 'Courage Made Manifest', 'Ego expression without purpose', 0, 1);

-- SOUL (The Character) - 4 Skills
INSERT OR IGNORE INTO player_skills (skill_name, domain, virtue, shadow_warning, current_xp, current_level) VALUES
    ('presence', 'soul', 'Justice to Others', 'Enmeshment, boundary loss', 0, 1),
    ('service', 'soul', 'Generativity', 'Martyrdom, self-neglect', 0, 1),
    ('courage', 'soul', 'Facing Fear', 'Recklessness', 0, 1),
    ('consistency', 'soul', 'Discipline', 'Rigidity, streak obsession', 0, 1);


-- ============================================
-- XP EVENTS (Audit Trail)
-- ============================================

-- Every XP award is logged for:
-- - Reconciliation (verify totals match)
-- - Analytics (XP sources over time)
-- - Debugging (why did I get this XP?)
CREATE TABLE IF NOT EXISTS xp_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    xp_gained INTEGER NOT NULL CHECK(xp_gained > 0),
    source_type TEXT NOT NULL,
    streak_bonus INTEGER DEFAULT 0,
    failure_tier INTEGER CHECK(failure_tier IS NULL OR failure_tier IN (1, 2, 3)),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_name) REFERENCES player_skills(skill_name)
);

CREATE INDEX IF NOT EXISTS idx_xp_events_skill
    ON xp_events(skill_name);
CREATE INDEX IF NOT EXISTS idx_xp_events_date
    ON xp_events(created_at);
CREATE INDEX IF NOT EXISTS idx_xp_events_source
    ON xp_events(source_type);


-- ============================================
-- ACTIVITY STREAKS
-- ============================================

-- Track consecutive days of activity
-- Used for streak bonus calculation (up to 14 days)
CREATE TABLE IF NOT EXISTS activity_streaks (
    date DATE PRIMARY KEY,
    streak_day INTEGER NOT NULL CHECK(streak_day >= 1),
    activities_logged INTEGER DEFAULT 1
);


-- ============================================
-- DAILY REFLECTIONS (Seneca's Trial)
-- ============================================

-- Evening audit following Seneca's three questions:
-- 1. Prosecution: Where did I fall short?
-- 2. Judgment: What was the truth?
-- 3. Advocacy: What did I do well?
-- Plus Franklin's weekly virtue focus
CREATE TABLE IF NOT EXISTS daily_reflections (
    date DATE PRIMARY KEY,
    prosecution TEXT,           -- Where did I fall short?
    judgment TEXT,              -- What was the truth?
    advocacy TEXT,              -- What did I do well?
    virtue_focus TEXT,          -- Franklin's weekly focus virtue
    virtue_score INTEGER CHECK(virtue_score IS NULL OR (virtue_score >= 1 AND virtue_score <= 10)),
    memento_mori_complete BOOLEAN DEFAULT FALSE,
    xp_awarded INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- ACHIEVEMENTS (Future)
-- ============================================

-- Achievement definitions
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    requirement_type TEXT NOT NULL,  -- 'skill_level', 'total_xp', 'streak', 'custom'
    requirement_skill TEXT,           -- NULL for non-skill achievements
    requirement_value INTEGER NOT NULL,
    icon TEXT,                        -- Emoji or icon name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Earned achievements
CREATE TABLE IF NOT EXISTS player_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    achievement_id INTEGER NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (achievement_id) REFERENCES achievements(id),
    UNIQUE(achievement_id)  -- Can only earn each achievement once
);

-- Seed domain-based achievements
INSERT OR IGNORE INTO achievements (name, description, requirement_type, requirement_skill, requirement_value, icon) VALUES
    ('First Steps', 'Earn your first XP', 'total_xp', NULL, 1, '🎯'),
    ('Getting Started', 'Reach total level 15', 'total_level', NULL, 15, '⭐'),
    -- BODY achievements
    ('Iron Body', 'Reach Strength level 25', 'skill_level', 'strength', 25, '💪'),
    ('Endless Runner', 'Reach Endurance level 25', 'skill_level', 'endurance', 25, '🏃'),
    ('Fluid Motion', 'Reach Mobility level 25', 'skill_level', 'mobility', 25, '🧘'),
    ('Clean Fuel', 'Reach Nutrition level 25', 'skill_level', 'nutrition', 25, '🥗'),
    -- MIND achievements
    ('Deep Thinker', 'Reach Focus level 25', 'skill_level', 'focus', 25, '🎯'),
    ('Lifelong Learner', 'Reach Learning level 25', 'skill_level', 'learning', 25, '📚'),
    ('Know Thyself', 'Reach Reflection level 25', 'skill_level', 'reflection', 25, '🪞'),
    ('Maker', 'Reach Creation level 25', 'skill_level', 'creation', 25, '🛠️'),
    -- SOUL achievements
    ('Fully Present', 'Reach Presence level 25', 'skill_level', 'presence', 25, '👁️'),
    ('Servant Leader', 'Reach Service level 25', 'skill_level', 'service', 25, '🤝'),
    ('Brave Heart', 'Reach Courage level 25', 'skill_level', 'courage', 25, '🦁'),
    ('Rock Solid', 'Reach Consistency level 25', 'skill_level', 'consistency', 25, '🪨'),
    -- Streaks
    ('Week Warrior', 'Maintain a 7-day streak', 'streak', NULL, 7, '🔥'),
    ('Fortnight Fighter', 'Maintain a 14-day streak', 'streak', NULL, 14, '🔥'),
    -- Milestones
    ('Century', 'Earn 100,000 total XP', 'total_xp', NULL, 100000, '💯'),
    ('Halfway There', 'Reach level 50 in any skill', 'skill_level', NULL, 50, '🏆'),
    ('Maxed', 'Reach level 99 in any skill', 'skill_level', NULL, 99, '👑');


-- ============================================
-- MIGRATION: Add new columns to existing tables
-- ============================================

-- For existing databases, add the new columns if they don't exist
-- SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we use a workaround

-- Note: These will fail silently if columns already exist on fresh installs
-- Run these manually for existing databases:
-- ALTER TABLE player_skills ADD COLUMN domain TEXT DEFAULT 'body';
-- ALTER TABLE player_skills ADD COLUMN virtue TEXT DEFAULT '';
-- ALTER TABLE player_skills ADD COLUMN shadow_warning TEXT;
-- ALTER TABLE xp_events ADD COLUMN failure_tier INTEGER;
-- ALTER TABLE xp_events ADD COLUMN notes TEXT;


-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Reconciliation query: Check XP totals match
-- SELECT
--     ps.skill_name,
--     ps.current_xp as stored_xp,
--     COALESCE(SUM(xe.xp_gained), 0) as calculated_xp,
--     ps.current_xp - COALESCE(SUM(xe.xp_gained), 0) as difference
-- FROM player_skills ps
-- LEFT JOIN xp_events xe ON ps.skill_name = xe.skill_name
-- GROUP BY ps.skill_name
-- HAVING difference != 0;

-- Skills by domain
-- SELECT domain, skill_name, virtue, current_level, current_xp
-- FROM player_skills
-- ORDER BY domain, current_level DESC;

-- Daily XP by skill
-- SELECT
--     skill_name,
--     DATE(created_at) as date,
--     SUM(xp_gained) as daily_xp
-- FROM xp_events
-- WHERE created_at >= DATE('now', '-7 days')
-- GROUP BY skill_name, DATE(created_at)
-- ORDER BY date DESC, skill_name;

-- Top XP sources this week
-- SELECT
--     source_type,
--     COUNT(*) as events,
--     SUM(xp_gained) as total_xp
-- FROM xp_events
-- WHERE created_at >= DATE('now', '-7 days')
-- GROUP BY source_type
-- ORDER BY total_xp DESC;

-- Reflection streak
-- SELECT COUNT(*) as reflection_streak
-- FROM (
--     SELECT date,
--            date - ROW_NUMBER() OVER (ORDER BY date) as grp
--     FROM daily_reflections
--     WHERE advocacy IS NOT NULL
-- )
-- GROUP BY grp
-- ORDER BY COUNT(*) DESC
-- LIMIT 1;
