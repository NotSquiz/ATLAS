-- Baby Brains Automation Schema
-- Extends ATLAS database with 10 tables for warming, trends, and content pipeline.

-- ============================================
-- ACCOUNT MANAGEMENT
-- ============================================

CREATE TABLE IF NOT EXISTS bb_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,  -- 'youtube', 'instagram', 'tiktok', 'facebook'
    handle TEXT NOT NULL,
    status TEXT DEFAULT 'warming',  -- 'warming', 'incubating', 'active', 'paused'
    followers INTEGER DEFAULT 0,
    following INTEGER DEFAULT 0,
    incubation_end_date DATE,  -- YouTube 21-day rule
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, handle)
);

-- ============================================
-- WARMING PIPELINE
-- ============================================

CREATE TABLE IF NOT EXISTS bb_warming_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL DEFAULT (date('now')),
    platform TEXT NOT NULL,
    url TEXT NOT NULL,
    channel_name TEXT,
    channel_handle TEXT,
    video_title TEXT,
    transcript_summary TEXT,
    suggested_comment TEXT,
    engagement_level TEXT DEFAULT 'WATCH',  -- 'WATCH', 'LIKE', 'SUBSCRIBE', 'COMMENT'
    watch_duration_target INTEGER DEFAULT 120,  -- seconds
    niche_relevance_score REAL DEFAULT 0.5,  -- 0-1
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'skipped'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bb_warming_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER REFERENCES bb_warming_targets(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,  -- 'watch', 'like', 'subscribe', 'comment'
    content_posted TEXT,  -- actual comment text posted (if comment)
    actual_watch_seconds INTEGER,
    engagement_result TEXT,  -- 'reply_received', 'liked_by_creator', 'no_response'
    time_spent_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ENGAGEMENT TRACKING
-- ============================================

CREATE TABLE IF NOT EXISTS bb_engagement_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    date DATE NOT NULL DEFAULT (date('now')),
    followers INTEGER DEFAULT 0,
    following INTEGER DEFAULT 0,
    engagement_rate REAL,
    impressions INTEGER DEFAULT 0,
    sends_count INTEGER DEFAULT 0,  -- Instagram "Sends" KPI
    profile_visits INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, date)
);

-- ============================================
-- TREND ENGINE
-- ============================================

CREATE TABLE IF NOT EXISTS bb_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    score REAL DEFAULT 0.0,  -- opportunity score 0-1
    sources TEXT,  -- JSON: which sources found this (youtube, grok, reddit, google)
    opportunity_level TEXT DEFAULT 'low',  -- 'low', 'medium', 'high', 'urgent'
    audience_segment TEXT,  -- which persona this targets
    knowledge_graph_match BOOLEAN DEFAULT FALSE,  -- do we have content for this?
    sample_urls TEXT,  -- JSON: example content URLs
    expires_at TIMESTAMP,  -- trends decay
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CONTENT PIPELINE
-- ============================================

CREATE TABLE IF NOT EXISTS bb_content_briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trend_id INTEGER REFERENCES bb_trends(id) ON DELETE SET NULL,
    topic TEXT NOT NULL,
    hooks TEXT,  -- JSON: array of hook options
    core_message TEXT,
    evidence TEXT,  -- JSON: knowledge graph references
    visual_concepts TEXT,  -- JSON: visual ideas
    target_platforms TEXT,  -- JSON: ['youtube', 'instagram', 'tiktok']
    audience_segment TEXT,
    status TEXT DEFAULT 'draft',  -- 'draft', 'approved', 'in_production', 'published'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bb_scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER REFERENCES bb_content_briefs(id) ON DELETE SET NULL,
    format_type TEXT NOT NULL,  -- '21s', '60s', 'article'
    script_text TEXT NOT NULL,
    voiceover TEXT,
    word_count INTEGER,
    captions_youtube TEXT,
    captions_instagram TEXT,
    captions_tiktok TEXT,
    hashtags TEXT,  -- JSON
    status TEXT DEFAULT 'draft',  -- 'draft', 'reviewed', 'approved', 'produced'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bb_visual_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES bb_scripts(id) ON DELETE SET NULL,
    asset_type TEXT NOT NULL,  -- 'midjourney_prompt', 'kling_prompt', 'image', 'video'
    prompt_text TEXT,
    file_path TEXT,
    notes TEXT,
    status TEXT DEFAULT 'pending',  -- 'pending', 'generated', 'approved'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bb_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER REFERENCES bb_scripts(id) ON DELETE SET NULL,
    platform TEXT NOT NULL,
    caption TEXT,
    hashtags TEXT,
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    post_url TEXT,
    performance_data TEXT,  -- JSON: views, likes, shares, saves, sends
    status TEXT DEFAULT 'draft',  -- 'draft', 'scheduled', 'published', 'archived'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CROSS-REPO INTELLIGENCE
-- ============================================

CREATE TABLE IF NOT EXISTS bb_cross_repo_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    repo TEXT NOT NULL,  -- 'ATLAS', 'babybrains-os', 'knowledge', 'web', 'app'
    file_path TEXT NOT NULL,
    summary TEXT,
    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repo, file_path)
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_bb_accounts_platform ON bb_accounts(platform);
CREATE INDEX IF NOT EXISTS idx_bb_warming_targets_date ON bb_warming_targets(date DESC);
CREATE INDEX IF NOT EXISTS idx_bb_warming_targets_status ON bb_warming_targets(status);
CREATE INDEX IF NOT EXISTS idx_bb_warming_actions_target ON bb_warming_actions(target_id);
CREATE INDEX IF NOT EXISTS idx_bb_engagement_log_platform_date ON bb_engagement_log(platform, date DESC);
CREATE INDEX IF NOT EXISTS idx_bb_trends_score ON bb_trends(score DESC);
CREATE INDEX IF NOT EXISTS idx_bb_trends_opportunity ON bb_trends(opportunity_level);
CREATE INDEX IF NOT EXISTS idx_bb_content_briefs_status ON bb_content_briefs(status);
CREATE INDEX IF NOT EXISTS idx_bb_scripts_status ON bb_scripts(status);
CREATE INDEX IF NOT EXISTS idx_bb_exports_platform ON bb_exports(platform);
CREATE INDEX IF NOT EXISTS idx_bb_exports_status ON bb_exports(status);
CREATE INDEX IF NOT EXISTS idx_bb_cross_repo_topic ON bb_cross_repo_index(topic);
