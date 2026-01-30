"""
Warming Target Generation

Generates daily warming targets from search queries and manual lists.
API-driven target generation (YouTube Data API, Grok) added in Sprint 2.
"""

import json
import logging
import random
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Config paths
WARMING_SCHEDULE_PATH = Path(__file__).parent.parent.parent.parent / "config" / "babybrains" / "warming_schedule.json"
ENGAGEMENT_RULES_PATH = Path(__file__).parent.parent.parent.parent / "config" / "babybrains" / "warming_engagement_rules.json"


def _load_config(path: Path) -> dict:
    """Load a JSON config file."""
    if not path.exists():
        logger.warning(f"Config not found: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_search_queries(platform: str) -> list[str]:
    """Get search queries for a platform from config."""
    config = _load_config(WARMING_SCHEDULE_PATH)
    queries = config.get("search_queries", {}).get(platform, [])
    return queries


def get_engagement_rules() -> dict:
    """Load engagement rules config."""
    return _load_config(ENGAGEMENT_RULES_PATH)


def determine_engagement_level(
    niche_relevance: float,
    channel_quality: float = 0.5,
) -> str:
    """
    Determine the engagement level for a target.

    Based on niche relevance score and channel quality.

    Args:
        niche_relevance: How relevant is this to BB niche (0-1)
        channel_quality: Channel quality score (0-1)

    Returns:
        Engagement level: WATCH, LIKE, SUBSCRIBE, or COMMENT
    """
    rules = get_engagement_rules()
    levels = rules.get("engagement_levels", {})

    # Start from highest and work down
    if (niche_relevance >= levels.get("SUBSCRIBE", {}).get("niche_relevance_threshold", 0.6)
            and channel_quality >= 0.6):
        return "SUBSCRIBE"
    elif niche_relevance >= levels.get("COMMENT", {}).get("niche_relevance_threshold", 0.5):
        return "COMMENT"
    elif niche_relevance >= levels.get("LIKE", {}).get("niche_relevance_threshold", 0.3):
        return "LIKE"
    else:
        return "WATCH"


def calculate_watch_duration(engagement_level: str) -> int:
    """
    Calculate target watch duration based on engagement level.

    Includes random variance (+-15%) for natural behavior.
    """
    rules = get_engagement_rules()
    level_config = rules.get("engagement_levels", {}).get(engagement_level, {})

    min_watch = level_config.get("min_watch_seconds", 60)
    max_watch = level_config.get("max_watch_seconds", 120)

    base_duration = random.randint(min_watch, max_watch)

    # Add variance
    variance_pct = rules.get("safety_rules", {}).get("watch_time_variance_percent", 15)
    variance = int(base_duration * variance_pct / 100)
    duration = base_duration + random.randint(-variance, variance)

    return max(30, duration)  # Never less than 30 seconds


def score_niche_relevance(title: str, description: str = "") -> float:
    """
    Score how relevant a video is to the BB niche.

    Uses keyword matching against niche keywords from config.

    Args:
        title: Video title
        description: Video description or transcript

    Returns:
        Relevance score 0-1
    """
    rules = get_engagement_rules()
    keywords = rules.get("scoring", {}).get("niche_keywords", [])

    if not keywords:
        return 0.5

    text = f"{title} {description}".lower()
    matches = sum(1 for kw in keywords if kw.lower() in text)

    # Normalize: 3+ keyword matches = 1.0
    return min(1.0, matches / 3.0)


def generate_manual_targets(
    urls: list[dict],
    platform: str = "youtube",
) -> list[dict]:
    """
    Generate targets from a manually provided URL list.

    This is the initial mode before API-driven target generation.

    Args:
        urls: List of dicts with 'url', 'title', 'channel' keys
        platform: Platform name

    Returns:
        List of target dicts ready for db.add_warming_target()
    """
    targets = []
    for item in urls:
        url = item.get("url", "")
        title = item.get("title", "")
        channel = item.get("channel", "")

        relevance = score_niche_relevance(title)
        engagement = determine_engagement_level(relevance)
        watch_duration = calculate_watch_duration(engagement)

        targets.append({
            "platform": platform,
            "url": url,
            "channel_name": channel,
            "video_title": title,
            "engagement_level": engagement,
            "watch_duration_target": watch_duration,
            "niche_relevance_score": relevance,
        })

    # Sort by relevance (highest first)
    targets.sort(key=lambda t: t["niche_relevance_score"], reverse=True)
    return targets
