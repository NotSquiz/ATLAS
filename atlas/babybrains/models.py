"""
Baby Brains Data Models

Dataclasses for all BB automation entities.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BBAccount:
    """A social media account being warmed."""

    id: int = 0
    platform: str = ""
    handle: str = ""
    status: str = "warming"
    followers: int = 0
    following: int = 0
    incubation_end_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class WarmingTarget:
    """A target video/post for daily warming."""

    id: int = 0
    date: Optional[date] = None
    platform: str = ""
    url: str = ""
    channel_name: Optional[str] = None
    channel_handle: Optional[str] = None
    video_title: Optional[str] = None
    transcript_summary: Optional[str] = None
    suggested_comment: Optional[str] = None
    engagement_level: str = "WATCH"
    watch_duration_target: int = 120
    niche_relevance_score: float = 0.5
    status: str = "pending"
    created_at: Optional[datetime] = None


@dataclass
class WarmingAction:
    """An action taken on a warming target."""

    id: int = 0
    target_id: int = 0
    action_type: str = ""
    content_posted: Optional[str] = None
    actual_watch_seconds: Optional[int] = None
    engagement_result: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class EngagementLog:
    """Weekly engagement snapshot for a platform."""

    id: int = 0
    platform: str = ""
    date: Optional[date] = None
    followers: int = 0
    following: int = 0
    engagement_rate: Optional[float] = None
    impressions: int = 0
    sends_count: int = 0
    profile_visits: int = 0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class TrendResult:
    """A scored trend from the trend engine."""

    id: int = 0
    topic: str = ""
    score: float = 0.0
    sources: list[str] = field(default_factory=list)
    opportunity_level: str = "low"
    audience_segment: Optional[str] = None
    knowledge_graph_match: bool = False
    sample_urls: list[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def sources_json(self) -> str:
        return json.dumps(self.sources)

    def sample_urls_json(self) -> str:
        return json.dumps(self.sample_urls)

    @classmethod
    def from_row(cls, row: dict) -> "TrendResult":
        sources = json.loads(row.get("sources") or "[]")
        sample_urls = json.loads(row.get("sample_urls") or "[]")
        return cls(
            id=row["id"],
            topic=row["topic"],
            score=row.get("score", 0.0),
            sources=sources,
            opportunity_level=row.get("opportunity_level", "low"),
            audience_segment=row.get("audience_segment"),
            knowledge_graph_match=bool(row.get("knowledge_graph_match", False)),
            sample_urls=sample_urls,
        )


@dataclass
class ContentBrief:
    """A content brief generated from trends."""

    id: int = 0
    trend_id: Optional[int] = None
    topic: str = ""
    hooks: list[str] = field(default_factory=list)
    core_message: Optional[str] = None
    evidence: list[dict] = field(default_factory=list)
    visual_concepts: list[str] = field(default_factory=list)
    target_platforms: list[str] = field(default_factory=list)
    audience_segment: Optional[str] = None
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def hooks_json(self) -> str:
        return json.dumps(self.hooks)

    def evidence_json(self) -> str:
        return json.dumps(self.evidence)

    def visual_concepts_json(self) -> str:
        return json.dumps(self.visual_concepts)

    def target_platforms_json(self) -> str:
        return json.dumps(self.target_platforms)


@dataclass
class Script:
    """A video/article script."""

    id: int = 0
    brief_id: Optional[int] = None
    format_type: str = "60s"
    script_text: str = ""
    voiceover: Optional[str] = None
    word_count: int = 0
    captions_youtube: Optional[str] = None
    captions_instagram: Optional[str] = None
    captions_tiktok: Optional[str] = None
    hashtags: list[str] = field(default_factory=list)
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def hashtags_json(self) -> str:
        return json.dumps(self.hashtags)


@dataclass
class VisualAsset:
    """A visual asset (prompt or file) for a script."""

    id: int = 0
    script_id: Optional[int] = None
    asset_type: str = ""
    prompt_text: Optional[str] = None
    file_path: Optional[str] = None
    notes: Optional[str] = None
    status: str = "pending"
    created_at: Optional[datetime] = None


@dataclass
class Export:
    """A platform-specific export package."""

    id: int = 0
    script_id: Optional[int] = None
    platform: str = ""
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    post_url: Optional[str] = None
    performance_data: Optional[dict] = None
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CrossRepoEntry:
    """A cross-repo document index entry."""

    id: int = 0
    topic: str = ""
    repo: str = ""
    file_path: str = ""
    summary: Optional[str] = None
    last_indexed: Optional[datetime] = None
