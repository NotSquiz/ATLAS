"""
Baby Brains Database Layer

Initializes BB tables and provides query helpers.
Uses the existing ATLAS MemoryStore connection.
"""

import json
import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from atlas.babybrains.models import (
    BBAccount,
    ContentBrief,
    EngagementLog,
    Export,
    PipelineRun,
    Script,
    TrendResult,
    VisualAsset,
    WarmingAction,
    WarmingTarget,
    CrossRepoEntry,
)

logger = logging.getLogger(__name__)

# Schema file location
BB_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_bb_tables(conn: sqlite3.Connection) -> None:
    """
    Initialize Baby Brains tables in the database.

    Idempotent -- safe to call multiple times (uses CREATE IF NOT EXISTS).

    Args:
        conn: SQLite connection (from MemoryStore or standalone)
    """
    if not BB_SCHEMA_PATH.exists():
        raise FileNotFoundError(f"BB schema not found: {BB_SCHEMA_PATH}")

    schema = BB_SCHEMA_PATH.read_text()
    conn.executescript(schema)
    conn.commit()
    logger.info("Baby Brains tables initialized")


def get_bb_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get a standalone BB database connection.

    Prefers using the ATLAS shared database. Falls back to ~/.atlas/atlas.db.
    Enables WAL mode for concurrent access.

    Args:
        db_path: Optional explicit database path

    Returns:
        SQLite connection with row_factory set and WAL mode enabled
    """
    if db_path is None:
        db_path = Path.home() / ".atlas" / "atlas.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for concurrent access (must be set after connect, before use)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# ============================================
# SCHEMA MIGRATION HELPERS
# ============================================


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _migrate_add_column(
    conn: sqlite3.Connection, table: str, column: str, col_type: str
) -> None:
    """Add column if it doesn't exist (idempotent)."""
    if not _column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        logger.info(f"Added column {table}.{column}")
    else:
        logger.debug(f"Column {table}.{column} already exists")


def run_content_migration(conn: sqlite3.Connection) -> None:
    """
    Run all content production schema migrations (idempotent).

    Adds columns needed for the content production pipeline.
    Safe to call multiple times - uses _column_exists() checks.
    """
    # bb_content_briefs (17 new columns including Round 7 additions)
    _migrate_add_column(conn, "bb_content_briefs", "age_range", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "hook_text", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "target_length", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "priority_tier", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "montessori_principle", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "setting", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "au_localisers", "TEXT")  # JSON
    _migrate_add_column(conn, "bb_content_briefs", "safety_lines", "TEXT")   # JSON
    _migrate_add_column(conn, "bb_content_briefs", "camera_notes", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "hook_pattern", "INTEGER")
    _migrate_add_column(conn, "bb_content_briefs", "content_pillar", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "tags", "TEXT")           # JSON
    # Round 7 audit additions
    _migrate_add_column(conn, "bb_content_briefs", "source", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "canonical_id", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "grok_confidence", "REAL")
    _migrate_add_column(conn, "bb_content_briefs", "knowledge_coverage", "TEXT")
    _migrate_add_column(conn, "bb_content_briefs", "all_principles", "TEXT")  # JSON

    # bb_scripts (7 new columns)
    _migrate_add_column(conn, "bb_scripts", "scenes", "TEXT")               # JSON
    _migrate_add_column(conn, "bb_scripts", "derivative_cuts", "TEXT")      # JSON
    _migrate_add_column(conn, "bb_scripts", "cta_text", "TEXT")
    _migrate_add_column(conn, "bb_scripts", "safety_disclaimers", "TEXT")   # JSON
    _migrate_add_column(conn, "bb_scripts", "hook_pattern_used", "INTEGER")
    _migrate_add_column(conn, "bb_scripts", "reviewed_by", "TEXT")
    _migrate_add_column(conn, "bb_scripts", "reviewed_at", "TEXT")

    # bb_visual_assets (6 new columns)
    _migrate_add_column(conn, "bb_visual_assets", "tool", "TEXT")
    _migrate_add_column(conn, "bb_visual_assets", "parameters", "TEXT")     # JSON
    _migrate_add_column(conn, "bb_visual_assets", "negative_prompt", "TEXT")
    _migrate_add_column(conn, "bb_visual_assets", "motion_prompt", "TEXT")
    _migrate_add_column(conn, "bb_visual_assets", "estimated_credits", "REAL")
    _migrate_add_column(conn, "bb_visual_assets", "scene_number", "INTEGER")

    # bb_exports (4 new columns)
    _migrate_add_column(conn, "bb_exports", "alt_text", "TEXT")
    _migrate_add_column(conn, "bb_exports", "title", "TEXT")
    _migrate_add_column(conn, "bb_exports", "description", "TEXT")
    _migrate_add_column(conn, "bb_exports", "export_tags", "TEXT")          # JSON (renamed to avoid column name conflict)

    conn.commit()

    # Create indexes for new columns
    conn.execute("CREATE INDEX IF NOT EXISTS idx_briefs_canonical ON bb_content_briefs(canonical_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_briefs_source ON bb_content_briefs(source)")
    conn.commit()

    logger.info("Content production schema migration complete")


# ============================================
# ACCOUNT QUERIES
# ============================================


def upsert_account(
    conn: sqlite3.Connection,
    platform: str,
    handle: str,
    status: str = "warming",
    incubation_end_date: Optional[str] = None,
) -> int:
    """Create or update a platform account."""
    cursor = conn.execute(
        "SELECT id FROM bb_accounts WHERE platform = ? AND handle = ?",
        (platform, handle),
    )
    row = cursor.fetchone()

    if row:
        conn.execute(
            """UPDATE bb_accounts
               SET status = ?, incubation_end_date = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, incubation_end_date, row["id"]),
        )
        conn.commit()
        return row["id"]

    cursor = conn.execute(
        """INSERT INTO bb_accounts (platform, handle, status, incubation_end_date)
           VALUES (?, ?, ?, ?)""",
        (platform, handle, status, incubation_end_date),
    )
    conn.commit()
    return cursor.lastrowid


def get_accounts(
    conn: sqlite3.Connection, platform: Optional[str] = None
) -> list[BBAccount]:
    """Get all accounts, optionally filtered by platform."""
    if platform:
        cursor = conn.execute(
            "SELECT * FROM bb_accounts WHERE platform = ?", (platform,)
        )
    else:
        cursor = conn.execute("SELECT * FROM bb_accounts ORDER BY platform")

    return [
        BBAccount(
            id=r["id"],
            platform=r["platform"],
            handle=r["handle"],
            status=r["status"],
            followers=r["followers"],
            following=r["following"],
            incubation_end_date=r["incubation_end_date"],
        )
        for r in cursor.fetchall()
    ]


def populate_accounts(conn: sqlite3.Connection) -> list[dict]:
    """
    Populate bb_accounts with the 4 Baby Brains social accounts.

    Idempotent -- uses upsert, safe to call multiple times.
    YouTube gets 'incubating' status with 7-day incubation end date.
    All others get 'warming' status.

    Args:
        conn: SQLite connection with BB tables initialized

    Returns:
        List of dicts with platform, handle, status, action ('inserted'/'updated')
    """
    incubation_end = (date.today() + timedelta(days=7)).isoformat()

    accounts = [
        {
            "platform": "youtube",
            "handle": "@babybrains-app",
            "status": "incubating",
            "incubation_end_date": incubation_end,
        },
        {
            "platform": "tiktok",
            "handle": "babybrains.app",
            "status": "warming",
            "incubation_end_date": None,
        },
        {
            "platform": "instagram",
            "handle": "babybrains.app",
            "status": "warming",
            "incubation_end_date": None,
        },
        {
            "platform": "facebook",
            "handle": "Baby Brains",
            "status": "warming",
            "incubation_end_date": None,
        },
    ]

    results = []
    for acct in accounts:
        # Check if already exists
        cursor = conn.execute(
            "SELECT id FROM bb_accounts WHERE platform = ? AND handle = ?",
            (acct["platform"], acct["handle"]),
        )
        existed = cursor.fetchone() is not None

        upsert_account(
            conn,
            platform=acct["platform"],
            handle=acct["handle"],
            status=acct["status"],
            incubation_end_date=acct["incubation_end_date"],
        )

        results.append({
            "platform": acct["platform"],
            "handle": acct["handle"],
            "status": acct["status"],
            "action": "updated" if existed else "inserted",
        })
        logger.info(
            "Account %s/%s %s (status=%s)",
            acct["platform"],
            acct["handle"],
            "updated" if existed else "inserted",
            acct["status"],
        )

    return results


# ============================================
# WARMING TARGET QUERIES
# ============================================


def add_warming_target(
    conn: sqlite3.Connection,
    platform: str,
    url: str,
    channel_name: Optional[str] = None,
    channel_handle: Optional[str] = None,
    video_title: Optional[str] = None,
    transcript_summary: Optional[str] = None,
    suggested_comment: Optional[str] = None,
    engagement_level: str = "WATCH",
    watch_duration_target: int = 120,
    niche_relevance_score: float = 0.5,
    target_date: Optional[str] = None,
) -> int:
    """Add a warming target for today (or specified date)."""
    target_date = target_date or date.today().isoformat()

    cursor = conn.execute(
        """INSERT INTO bb_warming_targets
           (date, platform, url, channel_name, channel_handle, video_title,
            transcript_summary, suggested_comment, engagement_level,
            watch_duration_target, niche_relevance_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            target_date, platform, url, channel_name, channel_handle,
            video_title, transcript_summary, suggested_comment,
            engagement_level, watch_duration_target, niche_relevance_score,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_warming_targets(
    conn: sqlite3.Connection,
    target_date: Optional[str] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
) -> list[WarmingTarget]:
    """Get warming targets for a date, optionally filtered."""
    target_date = target_date or date.today().isoformat()

    query = "SELECT * FROM bb_warming_targets WHERE date = ?"
    params: list = [target_date]

    if platform:
        query += " AND platform = ?"
        params.append(platform)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY niche_relevance_score DESC"

    cursor = conn.execute(query, params)
    return [
        WarmingTarget(
            id=r["id"],
            platform=r["platform"],
            url=r["url"],
            channel_name=r["channel_name"],
            channel_handle=r["channel_handle"],
            video_title=r["video_title"],
            transcript_summary=r["transcript_summary"],
            suggested_comment=r["suggested_comment"],
            engagement_level=r["engagement_level"],
            watch_duration_target=r["watch_duration_target"],
            niche_relevance_score=r["niche_relevance_score"],
            status=r["status"],
        )
        for r in cursor.fetchall()
    ]


def update_target_status(
    conn: sqlite3.Connection, target_id: int, status: str
) -> None:
    """Update a warming target's status."""
    conn.execute(
        "UPDATE bb_warming_targets SET status = ? WHERE id = ?",
        (status, target_id),
    )
    conn.commit()


# ============================================
# WARMING ACTION QUERIES
# ============================================


def log_warming_action(
    conn: sqlite3.Connection,
    target_id: int,
    action_type: str,
    content_posted: Optional[str] = None,
    actual_watch_seconds: Optional[int] = None,
    engagement_result: Optional[str] = None,
    time_spent_seconds: Optional[int] = None,
) -> int:
    """Log an action taken on a warming target."""
    cursor = conn.execute(
        """INSERT INTO bb_warming_actions
           (target_id, action_type, content_posted, actual_watch_seconds,
            engagement_result, time_spent_seconds)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            target_id, action_type, content_posted,
            actual_watch_seconds, engagement_result, time_spent_seconds,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_warming_stats(
    conn: sqlite3.Connection, days: int = 7
) -> dict:
    """Get warming statistics for the last N days."""
    # Target stats
    cursor = conn.execute(
        """SELECT
            COUNT(*) as total_targets,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
        FROM bb_warming_targets
        WHERE date >= date('now', ?)""",
        (f"-{days} days",),
    )
    target_row = cursor.fetchone()

    # Action stats (includes unlinked actions where target_id = 0)
    cursor = conn.execute(
        """SELECT
            COUNT(CASE WHEN action_type = 'watch' THEN 1 END) as watches,
            COUNT(CASE WHEN action_type = 'like' THEN 1 END) as likes,
            COUNT(CASE WHEN action_type = 'subscribe' THEN 1 END) as subscribes,
            COUNT(CASE WHEN action_type = 'comment' THEN 1 END) as comments,
            COALESCE(SUM(actual_watch_seconds), 0) as total_watch_seconds
        FROM bb_warming_actions
        WHERE created_at >= datetime('now', ?)""",
        (f"-{days} days",),
    )
    action_row = cursor.fetchone()

    return {
        "total_targets": target_row["total_targets"],
        "completed": target_row["completed"],
        "watches": action_row["watches"],
        "likes": action_row["likes"],
        "subscribes": action_row["subscribes"],
        "comments": action_row["comments"],
        "total_watch_minutes": round(action_row["total_watch_seconds"] / 60, 1),
        "period_days": days,
    }


def log_warming_session(
    conn: sqlite3.Connection,
    platform: str,
    videos_watched: int = 0,
    total_watch_seconds: int = 0,
    likes: int = 0,
    subscribes: int = 0,
    success: bool = True,
    abort_reason: Optional[str] = None,
) -> int:
    """
    Log a browser warming session result (success or failure).

    Uses bb_warming_actions with action_type 'session_complete' or
    'session_failure' and target_id=0 for session-level events.

    Args:
        conn: SQLite connection
        platform: Platform name ('youtube')
        videos_watched: Number of videos watched in session
        total_watch_seconds: Total watch time in seconds
        likes: Number of likes in session
        subscribes: Number of subscribes in session
        success: Whether session completed without abort
        abort_reason: Reason if session was aborted

    Returns:
        Action ID of the logged session entry
    """
    action_type = "session_complete" if success else "session_failure"
    if abort_reason:
        result_text = abort_reason
    else:
        result_text = (
            f"{platform}: {videos_watched} videos, "
            f"{total_watch_seconds}s watched, "
            f"{likes} likes, {subscribes} subscribes"
        )

    cursor = conn.execute(
        """INSERT INTO bb_warming_actions
           (target_id, action_type, engagement_result,
            actual_watch_seconds, time_spent_seconds)
           VALUES (?, ?, ?, ?, ?)""",
        (
            0, action_type, result_text,
            total_watch_seconds if success else None,
            total_watch_seconds,
        ),
    )
    conn.commit()
    logger.info(f"Session logged: {action_type} — {result_text}")
    return cursor.lastrowid


def get_browser_session_stats(
    conn: sqlite3.Connection, days: int = 7
) -> dict:
    """
    Get browser session statistics for warming status dashboard.

    Queries session-level entries from bb_warming_actions to provide
    browser automation stats including successful/failed sessions
    and last session details.

    Args:
        conn: SQLite connection
        days: Number of days to look back

    Returns:
        Dictionary with session stats
    """
    cutoff = f"-{days} days"

    # Session counts
    cursor = conn.execute(
        """SELECT
            COUNT(CASE WHEN action_type = 'session_complete' THEN 1 END)
                as successful_sessions,
            COUNT(CASE WHEN action_type = 'session_failure' THEN 1 END)
                as failed_sessions,
            COALESCE(SUM(CASE WHEN action_type = 'session_complete'
                THEN actual_watch_seconds ELSE 0 END), 0)
                as total_session_watch_seconds
        FROM bb_warming_actions
        WHERE created_at >= datetime('now', ?)
        AND action_type IN ('session_complete', 'session_failure')""",
        (cutoff,),
    )
    row = cursor.fetchone()

    # Most recent session
    cursor = conn.execute(
        """SELECT action_type, engagement_result, created_at
        FROM bb_warming_actions
        WHERE action_type IN ('session_complete', 'session_failure')
        ORDER BY created_at DESC
        LIMIT 1""",
    )
    last_session = cursor.fetchone()

    # Most recent failure reason
    cursor = conn.execute(
        """SELECT engagement_result, created_at
        FROM bb_warming_actions
        WHERE action_type = 'session_failure'
        AND created_at >= datetime('now', ?)
        ORDER BY created_at DESC
        LIMIT 1""",
        (cutoff,),
    )
    last_failure = cursor.fetchone()

    return {
        "successful_sessions": row["successful_sessions"],
        "failed_sessions": row["failed_sessions"],
        "total_session_watch_minutes": round(
            row["total_session_watch_seconds"] / 60, 1
        ),
        "last_session": {
            "type": last_session["action_type"] if last_session else None,
            "detail": last_session["engagement_result"] if last_session else None,
            "at": last_session["created_at"] if last_session else None,
        } if last_session else None,
        "last_failure": {
            "reason": last_failure["engagement_result"] if last_failure else None,
            "at": last_failure["created_at"] if last_failure else None,
        } if last_failure else None,
        "period_days": days,
    }


# ============================================
# TREND QUERIES
# ============================================


def add_trend(
    conn: sqlite3.Connection,
    topic: str,
    score: float,
    sources: list[str],
    opportunity_level: str = "low",
    audience_segment: Optional[str] = None,
    knowledge_graph_match: bool = False,
    sample_urls: Optional[list[str]] = None,
) -> int:
    """Add a trend scan result."""
    cursor = conn.execute(
        """INSERT INTO bb_trends
           (topic, score, sources, opportunity_level, audience_segment,
            knowledge_graph_match, sample_urls)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            topic, score, json.dumps(sources), opportunity_level,
            audience_segment, knowledge_graph_match,
            json.dumps(sample_urls or []),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_recent_trends(
    conn: sqlite3.Connection, limit: int = 20
) -> list[TrendResult]:
    """Get recent trends sorted by score."""
    cursor = conn.execute(
        """SELECT * FROM bb_trends
           ORDER BY score DESC, created_at DESC
           LIMIT ?""",
        (limit,),
    )
    return [TrendResult.from_row(dict(r)) for r in cursor.fetchall()]


# ============================================
# CONTENT PIPELINE QUERIES
# ============================================


def add_content_brief(
    conn: sqlite3.Connection,
    topic: str,
    hooks: Optional[list[str]] = None,
    core_message: Optional[str] = None,
    evidence: Optional[list[dict]] = None,
    visual_concepts: Optional[list[str]] = None,
    target_platforms: Optional[list[str]] = None,
    audience_segment: Optional[str] = None,
    trend_id: Optional[int] = None,
    # Content production fields
    age_range: Optional[str] = None,
    hook_text: Optional[str] = None,
    target_length: Optional[str] = None,
    priority_tier: Optional[str] = None,
    montessori_principle: Optional[str] = None,
    setting: Optional[str] = None,
    au_localisers: Optional[list[str]] = None,
    safety_lines: Optional[list[str]] = None,
    camera_notes: Optional[str] = None,
    hook_pattern: Optional[int] = None,
    content_pillar: Optional[str] = None,
    tags: Optional[list[str]] = None,
    # Source tracking fields
    source: Optional[str] = None,
    canonical_id: Optional[str] = None,
    grok_confidence: Optional[float] = None,
    knowledge_coverage: Optional[str] = None,
    all_principles: Optional[list[str]] = None,
) -> int:
    """
    Add a content brief.

    All list fields use `or []` pattern to ensure JSON produces "[]" not "null".
    """
    cursor = conn.execute(
        """INSERT INTO bb_content_briefs
           (trend_id, topic, hooks, core_message, evidence,
            visual_concepts, target_platforms, audience_segment,
            age_range, hook_text, target_length, priority_tier,
            montessori_principle, setting, au_localisers, safety_lines,
            camera_notes, hook_pattern, content_pillar, tags,
            source, canonical_id, grok_confidence, knowledge_coverage, all_principles)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            trend_id, topic,
            json.dumps(hooks or []),              # FIX: or [] prevents "null"
            core_message,
            json.dumps(evidence or []),
            json.dumps(visual_concepts or []),
            json.dumps(target_platforms or ["youtube", "instagram", "tiktok"]),
            audience_segment,
            age_range, hook_text, target_length, priority_tier,
            montessori_principle, setting,
            json.dumps(au_localisers or []),      # FIX: or []
            json.dumps(safety_lines or []),       # FIX: or []
            camera_notes, hook_pattern, content_pillar,
            json.dumps(tags or []),               # FIX: or []
            source, canonical_id, grok_confidence, knowledge_coverage,
            json.dumps(all_principles or []),     # FIX: or []
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_brief_by_id(conn: sqlite3.Connection, brief_id: int) -> Optional[ContentBrief]:
    """Get a content brief by ID."""
    cursor = conn.execute(
        "SELECT * FROM bb_content_briefs WHERE id = ?",
        (brief_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    return ContentBrief(
        id=row["id"],
        trend_id=row["trend_id"],
        topic=row["topic"],
        hooks=json.loads(row["hooks"] or "[]"),
        core_message=row["core_message"],
        evidence=json.loads(row["evidence"] or "[]"),
        visual_concepts=json.loads(row["visual_concepts"] or "[]"),
        target_platforms=json.loads(row["target_platforms"] or "[]"),
        audience_segment=row["audience_segment"],
        status=row["status"],
        # Content production fields (may not exist in older rows)
        age_range=row["age_range"] if "age_range" in row.keys() else None,
        hook_text=row["hook_text"] if "hook_text" in row.keys() else None,
        target_length=row["target_length"] if "target_length" in row.keys() else None,
        priority_tier=row["priority_tier"] if "priority_tier" in row.keys() else None,
        montessori_principle=row["montessori_principle"] if "montessori_principle" in row.keys() else None,
        setting=row["setting"] if "setting" in row.keys() else None,
        au_localisers=json.loads(row["au_localisers"] or "[]") if "au_localisers" in row.keys() else [],
        safety_lines=json.loads(row["safety_lines"] or "[]") if "safety_lines" in row.keys() else [],
        camera_notes=row["camera_notes"] if "camera_notes" in row.keys() else None,
        hook_pattern=row["hook_pattern"] if "hook_pattern" in row.keys() else None,
        content_pillar=row["content_pillar"] if "content_pillar" in row.keys() else None,
        tags=json.loads(row["tags"] or "[]") if "tags" in row.keys() else [],
        source=row["source"] if "source" in row.keys() else None,
        canonical_id=row["canonical_id"] if "canonical_id" in row.keys() else None,
        grok_confidence=row["grok_confidence"] if "grok_confidence" in row.keys() else None,
        knowledge_coverage=row["knowledge_coverage"] if "knowledge_coverage" in row.keys() else None,
        all_principles=json.loads(row["all_principles"] or "[]") if "all_principles" in row.keys() else [],
    )


def get_briefs_by_status(
    conn: sqlite3.Connection, status: str = "draft", limit: int = 20
) -> list[dict]:
    """Get content briefs by status."""
    cursor = conn.execute(
        "SELECT * FROM bb_content_briefs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
        (status, limit),
    )
    results = []
    for r in cursor.fetchall():
        results.append({
            "id": r["id"],
            "topic": r["topic"],
            "hooks": json.loads(r["hooks"] or "[]"),
            "core_message": r["core_message"],
            "status": r["status"],
            "audience_segment": r["audience_segment"],
            "created_at": r["created_at"],
        })
    return results


def add_script(
    conn: sqlite3.Connection,
    brief_id: int,
    format_type: str,
    script_text: str,
    voiceover: Optional[str] = None,
    word_count: Optional[int] = None,
) -> int:
    """Add a script for a content brief."""
    if word_count is None:
        word_count = len(script_text.split())

    cursor = conn.execute(
        """INSERT INTO bb_scripts
           (brief_id, format_type, script_text, voiceover, word_count)
           VALUES (?, ?, ?, ?, ?)""",
        (brief_id, format_type, script_text, voiceover, word_count),
    )
    conn.commit()
    return cursor.lastrowid


# ============================================
# ENGAGEMENT LOG QUERIES
# ============================================


def log_engagement(
    conn: sqlite3.Connection,
    platform: str,
    followers: int = 0,
    following: int = 0,
    engagement_rate: Optional[float] = None,
    impressions: int = 0,
    sends_count: int = 0,
    profile_visits: int = 0,
    notes: Optional[str] = None,
    log_date: Optional[str] = None,
) -> int:
    """Log engagement metrics for a platform."""
    log_date = log_date or date.today().isoformat()

    # Upsert
    cursor = conn.execute(
        "SELECT id FROM bb_engagement_log WHERE platform = ? AND date = ?",
        (platform, log_date),
    )
    row = cursor.fetchone()

    if row:
        conn.execute(
            """UPDATE bb_engagement_log
               SET followers = ?, following = ?, engagement_rate = ?,
                   impressions = ?, sends_count = ?, profile_visits = ?, notes = ?
               WHERE id = ?""",
            (followers, following, engagement_rate, impressions,
             sends_count, profile_visits, notes, row["id"]),
        )
        conn.commit()
        return row["id"]

    cursor = conn.execute(
        """INSERT INTO bb_engagement_log
           (platform, date, followers, following, engagement_rate,
            impressions, sends_count, profile_visits, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (platform, log_date, followers, following, engagement_rate,
         impressions, sends_count, profile_visits, notes),
    )
    conn.commit()
    return cursor.lastrowid


# ============================================
# CROSS-REPO INDEX QUERIES
# ============================================


def upsert_cross_repo_entry(
    conn: sqlite3.Connection,
    topic: str,
    repo: str,
    file_path: str,
    summary: Optional[str] = None,
) -> int:
    """Add or update a cross-repo index entry."""
    cursor = conn.execute(
        "SELECT id FROM bb_cross_repo_index WHERE repo = ? AND file_path = ?",
        (repo, file_path),
    )
    row = cursor.fetchone()

    if row:
        conn.execute(
            """UPDATE bb_cross_repo_index
               SET topic = ?, summary = ?, last_indexed = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (topic, summary, row["id"]),
        )
        conn.commit()
        return row["id"]

    cursor = conn.execute(
        """INSERT INTO bb_cross_repo_index (topic, repo, file_path, summary)
           VALUES (?, ?, ?, ?)""",
        (topic, repo, file_path, summary),
    )
    conn.commit()
    return cursor.lastrowid


def search_cross_repo(
    conn: sqlite3.Connection, query: str, limit: int = 10
) -> list[CrossRepoEntry]:
    """Search the cross-repo index by topic keyword."""
    cursor = conn.execute(
        """SELECT * FROM bb_cross_repo_index
           WHERE topic LIKE ? OR summary LIKE ? OR file_path LIKE ?
           ORDER BY last_indexed DESC
           LIMIT ?""",
        (f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )
    return [
        CrossRepoEntry(
            id=r["id"],
            topic=r["topic"],
            repo=r["repo"],
            file_path=r["file_path"],
            summary=r["summary"],
        )
        for r in cursor.fetchall()
    ]


# ============================================
# STATUS DASHBOARD
# ============================================


def get_bb_status(conn: sqlite3.Connection) -> dict:
    """Get a full Baby Brains status dashboard."""
    accounts = get_accounts(conn)
    warming_stats = get_warming_stats(conn, days=7)
    today_targets = get_warming_targets(conn)
    recent_trends = get_recent_trends(conn, limit=5)
    draft_briefs = get_briefs_by_status(conn, "draft", limit=5)

    return {
        "accounts": [
            {
                "platform": a.platform,
                "handle": a.handle,
                "status": a.status,
                "followers": a.followers,
                "incubation_end_date": a.incubation_end_date,
            }
            for a in accounts
        ],
        "warming_7d": warming_stats,
        "today": {
            "targets": len(today_targets),
            "pending": sum(1 for t in today_targets if t.status == "pending"),
            "completed": sum(1 for t in today_targets if t.status == "completed"),
        },
        "trends": {
            "recent_count": len(recent_trends),
            "top_topics": [t.topic for t in recent_trends[:3]],
        },
        "content": {
            "draft_briefs": len(draft_briefs),
        },
    }


# ============================================
# SCRIPT QUERIES
# ============================================


def get_script_by_id(conn: sqlite3.Connection, script_id: int) -> Optional[Script]:
    """Get a script by ID."""
    cursor = conn.execute(
        "SELECT * FROM bb_scripts WHERE id = ?",
        (script_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    keys = row.keys()
    return Script(
        id=row["id"],
        brief_id=row["brief_id"],
        format_type=row["format_type"],
        script_text=row["script_text"],
        voiceover=row["voiceover"],
        word_count=row["word_count"],
        captions_youtube=row["captions_youtube"],
        captions_instagram=row["captions_instagram"],
        captions_tiktok=row["captions_tiktok"],
        hashtags=json.loads(row["hashtags"] or "[]"),
        status=row["status"],
        # Content production fields
        scenes=json.loads(row["scenes"] or "[]") if "scenes" in keys else [],
        derivative_cuts=json.loads(row["derivative_cuts"] or "[]") if "derivative_cuts" in keys else [],
        cta_text=row["cta_text"] if "cta_text" in keys else None,
        safety_disclaimers=json.loads(row["safety_disclaimers"] or "[]") if "safety_disclaimers" in keys else [],
        hook_pattern_used=row["hook_pattern_used"] if "hook_pattern_used" in keys else None,
        reviewed_by=row["reviewed_by"] if "reviewed_by" in keys else None,
        reviewed_at=row["reviewed_at"] if "reviewed_at" in keys else None,
    )


def update_script_fields(conn: sqlite3.Connection, script_id: int, **fields) -> None:
    """
    Update specific fields on a script.

    Handles JSON serialization for list/dict fields.
    """
    if not fields:
        return

    # JSON-encode list/dict fields
    json_fields = {"scenes", "derivative_cuts", "safety_disclaimers", "hashtags"}
    for key in json_fields:
        if key in fields and isinstance(fields[key], (list, dict)):
            fields[key] = json.dumps(fields[key])

    set_clauses = ", ".join(f"{k} = ?" for k in fields.keys())
    values = list(fields.values()) + [script_id]

    conn.execute(
        f"UPDATE bb_scripts SET {set_clauses}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values,
    )
    conn.commit()


# ============================================
# VISUAL ASSET QUERIES
# ============================================


def add_visual_asset(
    conn: sqlite3.Connection,
    script_id: int,
    asset_type: str,
    prompt_text: Optional[str] = None,
    file_path: Optional[str] = None,
    notes: Optional[str] = None,
    tool: Optional[str] = None,
    parameters: Optional[dict] = None,
    negative_prompt: Optional[str] = None,
    motion_prompt: Optional[str] = None,
    estimated_credits: Optional[float] = None,
    scene_number: Optional[int] = None,
) -> int:
    """Add a visual asset for a script."""
    cursor = conn.execute(
        """INSERT INTO bb_visual_assets
           (script_id, asset_type, prompt_text, file_path, notes,
            tool, parameters, negative_prompt, motion_prompt,
            estimated_credits, scene_number)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            script_id, asset_type, prompt_text, file_path, notes,
            tool, json.dumps(parameters) if parameters else None,
            negative_prompt, motion_prompt, estimated_credits, scene_number,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_visual_assets_by_script(
    conn: sqlite3.Connection, script_id: int
) -> list[VisualAsset]:
    """Get all visual assets for a script."""
    cursor = conn.execute(
        "SELECT * FROM bb_visual_assets WHERE script_id = ? ORDER BY scene_number, id",
        (script_id,),
    )
    keys = None
    results = []
    for row in cursor.fetchall():
        if keys is None:
            keys = row.keys()
        results.append(VisualAsset(
            id=row["id"],
            script_id=row["script_id"],
            asset_type=row["asset_type"],
            prompt_text=row["prompt_text"],
            file_path=row["file_path"],
            notes=row["notes"],
            status=row["status"],
            tool=row["tool"] if "tool" in keys else None,
            parameters=json.loads(row["parameters"] or "{}") if "parameters" in keys else None,
            negative_prompt=row["negative_prompt"] if "negative_prompt" in keys else None,
            motion_prompt=row["motion_prompt"] if "motion_prompt" in keys else None,
            estimated_credits=row["estimated_credits"] if "estimated_credits" in keys else None,
            scene_number=row["scene_number"] if "scene_number" in keys else None,
        ))
    return results


# ============================================
# EXPORT QUERIES
# ============================================


def add_export(
    conn: sqlite3.Connection,
    script_id: int,
    platform: str,
    caption: Optional[str] = None,
    hashtags: Optional[str] = None,
    alt_text: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    export_tags: Optional[list[str]] = None,
) -> int:
    """Add an export entry for a script."""
    cursor = conn.execute(
        """INSERT INTO bb_exports
           (script_id, platform, caption, hashtags,
            alt_text, title, description, export_tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            script_id, platform, caption, hashtags,
            alt_text, title, description,
            json.dumps(export_tags or []),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_exports_by_script(conn: sqlite3.Connection, script_id: int) -> list[Export]:
    """Get all exports for a script."""
    cursor = conn.execute(
        "SELECT * FROM bb_exports WHERE script_id = ? ORDER BY platform",
        (script_id,),
    )
    keys = None
    results = []
    for row in cursor.fetchall():
        if keys is None:
            keys = row.keys()
        results.append(Export(
            id=row["id"],
            script_id=row["script_id"],
            platform=row["platform"],
            caption=row["caption"],
            hashtags=row["hashtags"],
            scheduled_at=row["scheduled_at"],
            published_at=row["published_at"],
            post_url=row["post_url"],
            performance_data=json.loads(row["performance_data"] or "{}") if row["performance_data"] else None,
            status=row["status"],
            alt_text=row["alt_text"] if "alt_text" in keys else None,
            title=row["title"] if "title" in keys else None,
            description=row["description"] if "description" in keys else None,
            export_tags=json.loads(row["export_tags"] or "[]") if "export_tags" in keys else [],
        ))
    return results


# ============================================
# PIPELINE RUN QUERIES
# ============================================


def add_pipeline_run(
    conn: sqlite3.Connection,
    brief_id: int,
    current_stage: str = "brief",
    max_retries: int = 3,
) -> int:
    """Add a new pipeline run."""
    cursor = conn.execute(
        """INSERT INTO bb_pipeline_runs
           (brief_id, current_stage, max_retries)
           VALUES (?, ?, ?)""",
        (brief_id, current_stage, max_retries),
    )
    conn.commit()
    return cursor.lastrowid


def update_pipeline_run(conn: sqlite3.Connection, run_id: int, **fields) -> None:
    """
    Update specific fields on a pipeline run.

    Handles JSON serialization for hook_failures list.
    """
    if not fields:
        return

    # JSON-encode list fields
    if "hook_failures" in fields and isinstance(fields["hook_failures"], list):
        fields["hook_failures"] = json.dumps(fields["hook_failures"])

    set_clauses = ", ".join(f"{k} = ?" for k in fields.keys())
    values = list(fields.values()) + [run_id]

    conn.execute(
        f"UPDATE bb_pipeline_runs SET {set_clauses}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    conn.commit()


def get_pipeline_run(conn: sqlite3.Connection, run_id: int) -> Optional[PipelineRun]:
    """Get a pipeline run by ID."""
    cursor = conn.execute(
        "SELECT * FROM bb_pipeline_runs WHERE id = ?",
        (run_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    return PipelineRun(
        id=row["id"],
        brief_id=row["brief_id"],
        script_id=row["script_id"],
        current_stage=row["current_stage"],
        retry_count=row["retry_count"],
        max_retries=row["max_retries"],
        scratch_pad_key=row["scratch_pad_key"],
        hook_failures=json.loads(row["hook_failures"] or "[]"),
        started_at=row["started_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )


def get_pipeline_run_by_script_id(
    conn: sqlite3.Connection, script_id: int
) -> Optional[PipelineRun]:
    """Get a pipeline run by script ID."""
    cursor = conn.execute(
        "SELECT * FROM bb_pipeline_runs WHERE script_id = ? ORDER BY id DESC LIMIT 1",
        (script_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    return PipelineRun(
        id=row["id"],
        brief_id=row["brief_id"],
        script_id=row["script_id"],
        current_stage=row["current_stage"],
        retry_count=row["retry_count"],
        max_retries=row["max_retries"],
        scratch_pad_key=row["scratch_pad_key"],
        hook_failures=json.loads(row["hook_failures"] or "[]"),
        started_at=row["started_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )


def get_active_pipeline_runs(conn: sqlite3.Connection) -> list[PipelineRun]:
    """Get all active (non-complete, non-failed) pipeline runs."""
    cursor = conn.execute(
        """SELECT * FROM bb_pipeline_runs
           WHERE current_stage NOT IN ('complete')
           AND current_stage NOT LIKE '%_failed'
           ORDER BY updated_at DESC""",
    )
    results = []
    for row in cursor.fetchall():
        results.append(PipelineRun(
            id=row["id"],
            brief_id=row["brief_id"],
            script_id=row["script_id"],
            current_stage=row["current_stage"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            scratch_pad_key=row["scratch_pad_key"],
            hook_failures=json.loads(row["hook_failures"] or "[]"),
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        ))
    return results


def get_all_pipeline_runs(conn: sqlite3.Connection, limit: int = 50) -> list[PipelineRun]:
    """Get all pipeline runs including failed and complete."""
    cursor = conn.execute(
        "SELECT * FROM bb_pipeline_runs ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    )
    results = []
    for row in cursor.fetchall():
        results.append(PipelineRun(
            id=row["id"],
            brief_id=row["brief_id"],
            script_id=row["script_id"],
            current_stage=row["current_stage"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            scratch_pad_key=row["scratch_pad_key"],
            hook_failures=json.loads(row["hook_failures"] or "[]"),
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        ))
    return results
