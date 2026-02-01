"""
Baby Brains Warming Service

Orchestrates the daily warming pipeline:
1. Generate or load targets
2. Fetch transcripts
3. Generate BB-voice comments
4. Present for human review
5. Run automated browser warming sessions (S2.3)
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


# Browser availability flag — patchright is optional
try:
    from atlas.babybrains.browser import WarmingBrowser, SessionResult
    BROWSER_AVAILABLE = True
except ImportError:
    BROWSER_AVAILABLE = False
    WarmingBrowser = None
    SessionResult = None


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
        actions_detail: Optional[list[dict]] = None,
    ) -> dict:
        """
        Log completed warming actions.

        Args:
            platform: Platform name
            comments: Number of comments posted
            likes: Number of likes
            subscribes: Number of subscribes/follows
            watches: Number of videos watched
            actions_detail: Optional list of detailed action dicts with keys:
                target_id, action_type, actual_watch_seconds, content_posted

        Returns:
            Summary of logged actions
        """
        logged = []

        # Detailed action logging (from browser session or rich input)
        if actions_detail:
            for action in actions_detail:
                db.log_warming_action(
                    self.conn,
                    target_id=action.get("target_id", 0),
                    action_type=action.get("action_type", "watch"),
                    actual_watch_seconds=action.get("actual_watch_seconds"),
                    content_posted=action.get("content_posted"),
                    engagement_result=action.get("engagement_result"),
                    time_spent_seconds=action.get("time_spent_seconds"),
                )
            logged.append(f"{len(actions_detail)} detailed action(s)")
        else:
            # Count-based logging (manual input)
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

    async def run_browser_session(
        self,
        platform: str = "youtube",
    ) -> dict:
        """
        Run an automated browser warming session.

        1. Gets pending targets for today
        2. Creates WarmingBrowser and runs session
        3. Logs individual actions (watch/like/subscribe) to bb_warming_actions
        4. Updates target statuses
        5. Logs session result (or failure with reason) to DB

        Args:
            platform: Platform to warm ('youtube')

        Returns:
            Dictionary with session results and stats
        """
        if not BROWSER_AVAILABLE:
            error_msg = (
                "Browser dependencies not installed. "
                "Run: pip install -e '.[browser]'"
            )
            logger.error(error_msg)
            db.log_warming_session(
                self.conn,
                platform=platform,
                success=False,
                abort_reason=f"import_error: {error_msg}",
            )
            return {"status": "error", "message": error_msg}

        # Step 1: Get pending targets
        targets = db.get_warming_targets(
            self.conn, platform=platform, status="pending"
        )
        if not targets:
            msg = f"No pending warming targets for {platform} today"
            logger.info(msg)
            return {"status": "no_targets", "message": msg}

        # Step 2: Convert DB targets to browser target dicts
        browser_targets = [
            {
                "url": t.url,
                "engagement_level": t.engagement_level,
                "watch_duration_target": t.watch_duration_target,
                "niche_relevance_score": t.niche_relevance_score,
            }
            for t in targets
        ]

        # Step 3: Create browser and run session
        browser = WarmingBrowser(account_id=f"bb_{platform}")
        try:
            session_result = await browser.run_session(browser_targets)
        except Exception as e:
            error_msg = f"Browser session crashed: {e}"
            logger.error(error_msg)
            db.log_warming_session(
                self.conn,
                platform=platform,
                success=False,
                abort_reason=f"crash: {error_msg}",
            )
            return {"status": "error", "message": error_msg}
        finally:
            await browser.stop()

        # Step 4: Log individual actions and update target statuses
        actions_logged = 0
        for i, watch_result in enumerate(session_result.watch_results):
            if i >= len(targets):
                break

            target = targets[i]

            if watch_result.success:
                # Log watch action
                db.log_warming_action(
                    self.conn,
                    target_id=target.id,
                    action_type="watch",
                    actual_watch_seconds=watch_result.actual_watch_seconds,
                )
                actions_logged += 1

                # Log like action if liked
                if watch_result.liked:
                    db.log_warming_action(
                        self.conn,
                        target_id=target.id,
                        action_type="like",
                    )
                    actions_logged += 1

                # Log subscribe action if subscribed
                if watch_result.subscribed:
                    db.log_warming_action(
                        self.conn,
                        target_id=target.id,
                        action_type="subscribe",
                    )
                    actions_logged += 1

                # Mark target as completed
                db.update_target_status(self.conn, target.id, "completed")
            else:
                # Mark target as skipped on error
                db.update_target_status(self.conn, target.id, "skipped")
                if watch_result.error:
                    logger.warning(
                        f"Target {target.id} failed: {watch_result.error}"
                    )

        # Step 5: Log session-level result
        if session_result.aborted:
            db.log_warming_session(
                self.conn,
                platform=platform,
                videos_watched=session_result.videos_watched,
                total_watch_seconds=session_result.total_watch_seconds,
                likes=session_result.likes,
                subscribes=session_result.subscribes,
                success=False,
                abort_reason=session_result.abort_reason,
            )
        else:
            db.log_warming_session(
                self.conn,
                platform=platform,
                videos_watched=session_result.videos_watched,
                total_watch_seconds=session_result.total_watch_seconds,
                likes=session_result.likes,
                subscribes=session_result.subscribes,
                success=True,
            )

        return {
            "status": "aborted" if session_result.aborted else "success",
            "abort_reason": session_result.abort_reason,
            "videos_watched": session_result.videos_watched,
            "total_watch_seconds": session_result.total_watch_seconds,
            "likes": session_result.likes,
            "subscribes": session_result.subscribes,
            "errors": session_result.errors,
            "actions_logged": actions_logged,
            "summary": session_result.summary,
        }
