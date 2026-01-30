"""
Baby Brains Warming Service

Orchestrates the daily warming pipeline:
1. Generate or load targets
2. Fetch transcripts
3. Generate BB-voice comments
4. Present for human review
"""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from atlas.babybrains import db
from atlas.babybrains.models import WarmingTarget
from atlas.babybrains.warming.comments import CommentDraft, CommentGenerator
from atlas.babybrains.warming.targets import (
    determine_engagement_level,
    calculate_watch_duration,
    score_niche_relevance,
)
from atlas.babybrains.warming.transcript import fetch_transcript, TranscriptResult

logger = logging.getLogger(__name__)


@dataclass
class WarmingDailyResult:
    """Result of running the daily warming pipeline."""

    date: str
    platform: Optional[str] = None
    targets: list[dict] = field(default_factory=list)
    comments_generated: int = 0
    transcripts_fetched: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (
            f"{len(self.targets)} targets, "
            f"{self.transcripts_fetched} transcripts, "
            f"{self.comments_generated} comments"
        )


class WarmingService:
    """
    Orchestrates the Baby Brains warming pipeline.

    Usage:
        service = WarmingService(conn)
        result = await service.run_daily(platform="youtube")
    """

    def __init__(
        self,
        conn: Optional[sqlite3.Connection] = None,
        db_path: Optional[Path] = None,
    ):
        self._conn = conn
        self._db_path = db_path
        self._comment_gen: Optional[CommentGenerator] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = db.get_bb_connection(self._db_path)
            db.init_bb_tables(self._conn)
        return self._conn

    @property
    def comment_generator(self) -> CommentGenerator:
        if self._comment_gen is None:
            self._comment_gen = CommentGenerator()
        return self._comment_gen

    async def run_daily(
        self,
        platform: Optional[str] = None,
        generate_comments: bool = True,
    ) -> WarmingDailyResult:
        """
        Run the daily warming pipeline.

        1. Load existing targets for today (or generate from config)
        2. Fetch transcripts for targets missing them
        3. Generate BB-voice comments for COMMENT-level targets
        4. Return results for human review

        Args:
            platform: Filter by platform (None = all)
            generate_comments: Whether to generate AI comments

        Returns:
            WarmingDailyResult with targets and comments
        """
        result = WarmingDailyResult(
            date=date.today().isoformat(),
            platform=platform,
        )

        # Step 1: Get today's targets
        targets = db.get_warming_targets(
            self.conn,
            platform=platform,
            status="pending",
        )

        if not targets:
            logger.info("No warming targets for today")
            return result

        # Step 2: Fetch transcripts for targets that need them
        for target in targets:
            if target.platform == "youtube" and not target.transcript_summary:
                transcript = await self._fetch_and_store_transcript(target)
                if transcript and transcript.available:
                    result.transcripts_fetched += 1

        # Reload targets after transcript updates
        targets = db.get_warming_targets(
            self.conn,
            platform=platform,
            status="pending",
        )

        # Step 3: Generate comments for COMMENT-level targets
        for target in targets:
            target_dict = {
                "id": target.id,
                "platform": target.platform,
                "url": target.url,
                "channel": target.channel_name,
                "title": target.video_title,
                "transcript_summary": target.transcript_summary,
                "engagement_level": target.engagement_level,
                "watch_seconds": target.watch_duration_target,
                "relevance": target.niche_relevance_score,
                "status": target.status,
                "suggested_comment": target.suggested_comment,
            }

            if (
                generate_comments
                and target.engagement_level == "COMMENT"
                and not target.suggested_comment
                and target.transcript_summary
            ):
                comment = await self._generate_comment(target)
                if comment and comment.passes_quality_gate:
                    target_dict["suggested_comment"] = comment.comment_text
                    result.comments_generated += 1
                elif comment:
                    target_dict["comment_issues"] = comment.quality_issues

            result.targets.append(target_dict)

        logger.info(f"Warming daily: {result.summary}")
        return result

    async def add_targets_from_urls(
        self,
        urls: list[dict],
        platform: str = "youtube",
        fetch_transcripts: bool = True,
    ) -> int:
        """
        Add warming targets from a list of URLs.

        Args:
            urls: List of dicts with 'url', 'title', 'channel' keys
            platform: Platform name
            fetch_transcripts: Whether to fetch transcripts immediately

        Returns:
            Number of targets added
        """
        from atlas.babybrains.warming.targets import generate_manual_targets

        targets = generate_manual_targets(urls, platform)
        count = 0

        for t in targets:
            target_id = db.add_warming_target(
                self.conn,
                platform=t["platform"],
                url=t["url"],
                channel_name=t.get("channel_name"),
                video_title=t.get("video_title"),
                engagement_level=t["engagement_level"],
                watch_duration_target=t["watch_duration_target"],
                niche_relevance_score=t["niche_relevance_score"],
            )

            if fetch_transcripts and platform == "youtube":
                # Create a minimal target object for transcript fetching
                target = WarmingTarget(
                    id=target_id,
                    platform=platform,
                    url=t["url"],
                    video_title=t.get("video_title"),
                )
                await self._fetch_and_store_transcript(target)

            count += 1

        return count

    async def _fetch_and_store_transcript(
        self, target: WarmingTarget
    ) -> Optional[TranscriptResult]:
        """Fetch transcript and update the target in DB."""
        try:
            result = await fetch_transcript(target.url)
            if result.available:
                self.conn.execute(
                    """UPDATE bb_warming_targets
                       SET transcript_summary = ?
                       WHERE id = ?""",
                    (result.summary or result.text[:500], target.id),
                )
                self.conn.commit()
                logger.debug(f"Transcript fetched for target {target.id}")
            return result
        except Exception as e:
            logger.error(f"Transcript fetch failed for {target.url}: {e}")
            return None

    async def _generate_comment(
        self, target: WarmingTarget
    ) -> Optional[CommentDraft]:
        """Generate a comment for a target and store it."""
        try:
            comment = await self.comment_generator.generate_comment(
                transcript=target.transcript_summary or "",
                video_title=target.video_title or "",
                video_id=str(target.id),
                platform=target.platform,
            )

            if comment.passes_quality_gate:
                self.conn.execute(
                    """UPDATE bb_warming_targets
                       SET suggested_comment = ?
                       WHERE id = ?""",
                    (comment.comment_text, target.id),
                )
                self.conn.commit()

            return comment
        except Exception as e:
            logger.error(f"Comment generation failed for target {target.id}: {e}")
            return None

    def log_done(
        self,
        platform: str,
        comments: int = 0,
        likes: int = 0,
        subscribes: int = 0,
        watches: int = 0,
    ) -> dict:
        """
        Log completed warming actions.

        Args:
            platform: Platform name
            comments: Number of comments posted
            likes: Number of likes
            subscribes: Number of subscribes/follows
            watches: Number of videos watched

        Returns:
            Summary of logged actions
        """
        logged = []
        for action_type, count in [
            ("comment", comments),
            ("like", likes),
            ("subscribe", subscribes),
            ("watch", watches),
        ]:
            for _ in range(count):
                db.log_warming_action(
                    self.conn, target_id=0, action_type=action_type
                )
            if count > 0:
                logged.append(f"{count} {action_type}(s)")

        return {
            "platform": platform,
            "actions": logged,
            "message": f"Logged for {platform}: {', '.join(logged)}",
        }
