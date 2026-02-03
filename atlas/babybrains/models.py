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
    """A content brief generated from trends or activity canonicals."""

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
    # Content production fields
    age_range: Optional[str] = None              # e.g., "0-6m", "6-12m", "12-24m"
    hook_text: Optional[str] = None              # Primary hook for video
    target_length: Optional[str] = None          # "21s", "60s", "90s"
    priority_tier: Optional[str] = None          # "p1", "p2", "p3"
    montessori_principle: Optional[str] = None   # Primary principle slug
    setting: Optional[str] = None                # "indoor", "outdoor", "both"
    au_localisers: list[str] = field(default_factory=list)  # AU visual cues
    safety_lines: list[str] = field(default_factory=list)   # Safety warnings
    camera_notes: Optional[str] = None           # Camera/filming notes
    hook_pattern: Optional[int] = None           # Hook pattern number
    content_pillar: Optional[str] = None         # Content pillar/category
    tags: list[str] = field(default_factory=list)  # Search/discovery tags
    # Source tracking (Round 7 additions)
    source: Optional[str] = None                 # "canonical:{id}", "grok:{topic}"
    canonical_id: Optional[str] = None           # FK to activity canonical file
    grok_confidence: Optional[float] = None      # Grok trend confidence 0-1
    knowledge_coverage: Optional[str] = None     # "strong", "partial", "none"
    all_principles: list[str] = field(default_factory=list)  # All principle slugs

    def hooks_json(self) -> str:
        return json.dumps(self.hooks)

    def evidence_json(self) -> str:
        return json.dumps(self.evidence)

    def visual_concepts_json(self) -> str:
        return json.dumps(self.visual_concepts)

    def target_platforms_json(self) -> str:
        return json.dumps(self.target_platforms)

    def au_localisers_json(self) -> str:
        return json.dumps(self.au_localisers)

    def safety_lines_json(self) -> str:
        return json.dumps(self.safety_lines)

    def tags_json(self) -> str:
        return json.dumps(self.tags)

    def all_principles_json(self) -> str:
        return json.dumps(self.all_principles)


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
    # Content production fields
    scenes: list[dict] = field(default_factory=list)  # Scene-by-scene breakdown
    derivative_cuts: list[dict] = field(default_factory=list)  # P1/P2/P3 derivatives
    cta_text: Optional[str] = None               # Call to action text
    safety_disclaimers: list[str] = field(default_factory=list)  # Required disclaimers
    hook_pattern_used: Optional[int] = None      # Which hook pattern was used
    reviewed_by: Optional[str] = None            # Reviewer identifier
    reviewed_at: Optional[datetime] = None       # Review timestamp

    def hashtags_json(self) -> str:
        return json.dumps(self.hashtags)

    def scenes_json(self) -> str:
        return json.dumps(self.scenes)

    def derivative_cuts_json(self) -> str:
        return json.dumps(self.derivative_cuts)

    def safety_disclaimers_json(self) -> str:
        return json.dumps(self.safety_disclaimers)


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
    # Content production fields
    tool: Optional[str] = None                   # "midjourney", "pika", "kling"
    parameters: Optional[dict] = None            # Tool-specific parameters
    negative_prompt: Optional[str] = None        # Negative prompt for generation
    motion_prompt: Optional[str] = None          # Motion/animation prompt
    estimated_credits: Optional[float] = None    # Estimated cost in credits
    scene_number: Optional[int] = None           # Which scene this is for

    def parameters_json(self) -> str:
        return json.dumps(self.parameters) if self.parameters else "{}"


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
    # Content production fields
    alt_text: Optional[str] = None               # Accessibility alt text
    title: Optional[str] = None                  # Video/post title
    description: Optional[str] = None            # Extended description
    export_tags: list[str] = field(default_factory=list)  # Platform-specific tags

    def export_tags_json(self) -> str:
        return json.dumps(self.export_tags)


@dataclass
class CrossRepoEntry:
    """A cross-repo document index entry."""

    id: int = 0
    topic: str = ""
    repo: str = ""
    file_path: str = ""
    summary: Optional[str] = None
    last_indexed: Optional[datetime] = None


@dataclass
class PipelineRun:
    """A content production pipeline run."""

    id: int = 0
    brief_id: Optional[int] = None
    script_id: Optional[int] = None
    current_stage: str = "brief"
    retry_count: int = 0
    max_retries: int = 3
    scratch_pad_key: Optional[str] = None
    hook_failures: list[dict] = field(default_factory=list)  # [{hook, code, msg, timestamp}]
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def hook_failures_json(self) -> str:
        return json.dumps(self.hook_failures)

    @property
    def is_failed(self) -> bool:
        """Check if the pipeline is in a failed state."""
        return self.current_stage.endswith("_failed")

    @property
    def is_complete(self) -> bool:
        """Check if the pipeline has completed."""
        return self.current_stage == "complete"

    @property
    def is_waiting_for_human(self) -> bool:
        """Check if the pipeline is waiting for human action."""
        return self.current_stage in ("manual_visual", "manual_assembly", "review")
