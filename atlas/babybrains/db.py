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

    Args:
        db_path: Optional explicit database path

    Returns:
        SQLite connection with row_factory set
    """
    if db_path is None:
        db_path = Path.home() / ".atlas" / "atlas.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


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
    hooks: list[str],
    core_message: str,
    evidence: Optional[list[dict]] = None,
    visual_concepts: Optional[list[str]] = None,
    target_platforms: Optional[list[str]] = None,
    audience_segment: Optional[str] = None,
    trend_id: Optional[int] = None,
) -> int:
    """Add a content brief."""
    cursor = conn.execute(
        """INSERT INTO bb_content_briefs
           (trend_id, topic, hooks, core_message, evidence,
            visual_concepts, target_platforms, audience_segment)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            trend_id, topic, json.dumps(hooks), core_message,
            json.dumps(evidence or []), json.dumps(visual_concepts or []),
            json.dumps(target_platforms or ["youtube", "instagram", "tiktok"]),
            audience_segment,
        ),
    )
    conn.commit()
    return cursor.lastrowid


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
