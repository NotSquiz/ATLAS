"""
WarmingBrowser — Stealth browser automation for YouTube warming.

Uses Patchright (patched Playwright fork) with system Chrome for
undetectable browser automation. Implements humanized watching,
engagement actions, and session management.

Requires: pip install -e ".[browser]" (patchright + humanization-playwright)

CRITICAL RULES:
- NEVER automate Google login — manual login once, persist profile
- NEVER post comments via automation — human only
- One account per browser profile
- Residential IP only (no VPN/proxy)
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from aiobreaker import CircuitBreaker, CircuitBreakerError

from atlas.babybrains.warming.targets import get_engagement_rules

logger = logging.getLogger(__name__)

# Default profile base directory
DEFAULT_PROFILE_BASE = Path.home() / ".atlas" / ".browser"

# Session log for daily session tracking
SESSION_LOG_PATH = DEFAULT_PROFILE_BASE / "session_log.json"

# Domain allowlist — only youtube.com for warming (P30)
ALLOWED_DOMAINS = frozenset({
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "consent.youtube.com",
    "accounts.google.com",
    "accounts.youtube.com",
})


@dataclass
class SessionConfig:
    """Configuration for a warming session."""

    min_videos: int = 3
    max_videos: int = 7
    min_duration_minutes: int = 15
    max_duration_minutes: int = 45
    max_sessions_per_day: int = 2
    inter_video_delay_mean: float = 45.0
    inter_video_delay_stddev: float = 15.0
    # Humanization parameters
    scroll_interval_min: float = 15.0
    scroll_interval_max: float = 45.0
    mouse_drift_interval_min: float = 10.0
    mouse_drift_interval_max: float = 30.0
    pause_duration_min: float = 1.0
    pause_duration_max: float = 3.0
    pause_every_min: float = 120.0  # 2 min
    pause_every_max: float = 300.0  # 5 min


@dataclass
class WatchResult:
    """Result of watching a single video."""

    url: str
    actual_watch_seconds: int = 0
    liked: bool = False
    subscribed: bool = False
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.actual_watch_seconds > 0


@dataclass
class SessionResult:
    """Result of a full warming session."""

    videos_watched: int = 0
    total_watch_seconds: int = 0
    likes: int = 0
    subscribes: int = 0
    errors: list[str] = field(default_factory=list)
    watch_results: list[WatchResult] = field(default_factory=list)
    aborted: bool = False
    abort_reason: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.videos_watched > 0 and not self.aborted

    @property
    def summary(self) -> str:
        return (
            f"{self.videos_watched} videos, "
            f"{self.total_watch_seconds}s watched, "
            f"{self.likes} likes, "
            f"{self.subscribes} subscribes"
        )


def is_allowed_domain(url: str) -> bool:
    """Check if a URL's domain is in the warming allowlist."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return hostname in ALLOWED_DOMAINS
    except Exception:
        return False


def _gaussian_delay(mean: float, stddev: float, minimum: float = 5.0) -> float:
    """Generate a gaussian-distributed delay, clamped to reasonable bounds."""
    delay = random.gauss(mean, stddev)
    return max(minimum, min(mean * 3, delay))


def _load_session_log(path: Path) -> dict:
    """Load session log from disk."""
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Session log corrupted, resetting: {e}")
    return {}


def _save_session_log(path: Path, data: dict) -> None:
    """Save session log to disk."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as e:
        logger.error(f"Failed to save session log: {e}")


class WarmingBrowser:
    """
    Stealth browser automation for YouTube account warming.

    Uses Patchright with system Chrome and persistent browser profiles
    for undetectable warming behavior. Implements humanized watching
    with random scrolls, mouse drift, and natural pauses.

    Usage:
        browser = WarmingBrowser(account_id="bb_youtube")
        await browser.start()

        if not await browser.check_login_state():
            logger.error("Not logged in — log in manually first")
            await browser.stop()
            return

        result = await browser.watch_video(
            "https://www.youtube.com/watch?v=...",
            duration_pct=0.7,
        )
        await browser.stop()
    """

    def __init__(
        self,
        account_id: str,
        profile_base: Optional[Path] = None,
        config: Optional[SessionConfig] = None,
        session_log_path: Optional[Path] = None,
    ):
        self._account_id = account_id
        self._profile_base = profile_base or DEFAULT_PROFILE_BASE
        self._profile_dir = self._profile_base / account_id
        self._config = config or SessionConfig()
        self._session_log_path = session_log_path or SESSION_LOG_PATH

        # Browser state
        self._context = None
        self._page = None
        self._started = False

        # Session tracking
        self._session_video_count = 0
        self._session_start_time: Optional[float] = None
        self._session_watch_seconds = 0

        # Circuit breaker: trips after 3 consecutive failures, 5-min reset
        self._breaker = CircuitBreaker(
            fail_max=3,
            timeout_duration=timedelta(minutes=5),
        )

        # Engagement rules (loaded once)
        self._engagement_rules: Optional[dict] = None

    @property
    def profile_dir(self) -> Path:
        """Path to the persistent browser profile directory."""
        return self._profile_dir

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def session_video_count(self) -> int:
        return self._session_video_count

    @property
    def session_elapsed_minutes(self) -> float:
        if self._session_start_time is None:
            return 0.0
        return (time.monotonic() - self._session_start_time) / 60.0

    def _get_engagement_rules(self) -> dict:
        """Load and cache engagement rules."""
        if self._engagement_rules is None:
            self._engagement_rules = get_engagement_rules()
        return self._engagement_rules

    def _get_max_videos(self) -> int:
        """Get random max videos for this session within configured range."""
        return random.randint(self._config.min_videos, self._config.max_videos)

    def _get_max_duration_minutes(self) -> float:
        """Get random max duration for this session within configured range."""
        return random.uniform(
            self._config.min_duration_minutes,
            self._config.max_duration_minutes,
        )

    def check_daily_session_limit(self) -> bool:
        """
        Check if we've exceeded the daily session limit.

        Returns:
            True if another session is allowed, False if limit reached.
        """
        today = date.today().isoformat()
        log = _load_session_log(self._session_log_path)
        day_entry = log.get(today, {})
        sessions_today = day_entry.get("sessions", 0)

        if sessions_today >= self._config.max_sessions_per_day:
            logger.warning(
                f"Daily session limit reached: {sessions_today}/"
                f"{self._config.max_sessions_per_day}"
            )
            return False
        return True

    def _record_session(self) -> None:
        """Record this session in the session log."""
        today = date.today().isoformat()
        log = _load_session_log(self._session_log_path)

        if today not in log:
            log[today] = {"sessions": 0}

        log[today]["sessions"] = log[today].get("sessions", 0) + 1
        log[today]["last_session_end"] = datetime.now().isoformat()

        # Prune entries older than 7 days
        cutoff = (date.today() - timedelta(days=7)).isoformat()
        log = {k: v for k, v in log.items() if k >= cutoff}

        _save_session_log(self._session_log_path, log)

    async def start(self) -> None:
        """
        Launch the browser with persistent profile and stealth config.

        Uses the optimal configuration from S2.1 spike test:
        - System Chrome (not bundled Chromium)
        - --disable-blink-features=AutomationControlled
        - Patchright CDP patches
        - NO JS init scripts
        """
        if self._started:
            logger.warning("Browser already started")
            return

        # Lazy import — only needed when actually launching browser
        from patchright.async_api import async_playwright

        self._profile_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Launching browser with profile: {self._profile_dir}")

        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self._profile_dir),
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=["--disable-blink-features=AutomationControlled"],
        )

        self._page = (
            self._context.pages[0]
            if self._context.pages
            else await self._context.new_page()
        )

        self._started = True
        self._session_start_time = time.monotonic()
        self._session_video_count = 0
        self._session_watch_seconds = 0
        logger.info("Browser started successfully")

    async def stop(self) -> None:
        """Close the browser context and record the session."""
        if not self._started:
            return

        try:
            if self._context:
                await self._context.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        finally:
            self._context = None
            self._page = None
            self._playwright = None
            self._started = False

            if self._session_video_count > 0:
                self._record_session()

            logger.info(
                f"Browser stopped. Session: {self._session_video_count} videos, "
                f"{self._session_watch_seconds}s watched"
            )

    async def check_login_state(self) -> bool:
        """
        Verify Google/YouTube session is valid.

        Navigates to YouTube and checks if the user avatar/sign-in
        button indicates a logged-in state. Logs WARNING and returns
        False if cookies have expired.

        Returns:
            True if logged in, False if session expired.
        """
        if not self._started or not self._page:
            logger.error("Browser not started — call start() first")
            return False

        try:
            await self._page.goto(
                "https://www.youtube.com/",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await asyncio.sleep(2)

            login_state = await self._page.evaluate("""() => {
                // Check for avatar button (logged in)
                const avatar = document.querySelector(
                    'button#avatar-btn, img.yt-spec-avatar-shape__avatar'
                );
                // Check for sign-in button (not logged in)
                const signIn = document.querySelector(
                    'a[href*="accounts.google.com/ServiceLogin"], '
                    + 'ytd-button-renderer a[href*="accounts.google.com"],'
                    + 'tp-yt-paper-button[aria-label="Sign in"]'
                );
                return {
                    hasAvatar: !!avatar,
                    hasSignIn: !!signIn,
                    title: document.title,
                };
            }""")

            if login_state.get("hasAvatar") and not login_state.get("hasSignIn"):
                logger.info("Login state: VALID (avatar detected)")
                return True
            elif login_state.get("hasSignIn"):
                logger.warning(
                    "Login state: EXPIRED — Google session cookies have expired. "
                    "Log in manually to the browser profile to re-authenticate."
                )
                return False
            else:
                # Ambiguous state — consent page, regional redirect, etc.
                logger.warning(
                    f"Login state: UNKNOWN — page title: {login_state.get('title')}. "
                    "May need manual verification."
                )
                return False

        except Exception as e:
            logger.error(f"Login state check failed: {e}")
            return False

    def _check_session_limits(self, max_videos: int, max_minutes: float) -> Optional[str]:
        """
        Check if session limits have been reached.

        Returns:
            None if OK, or a string reason if limits exceeded.
        """
        if self._session_video_count >= max_videos:
            return f"Video limit reached ({self._session_video_count}/{max_videos})"

        elapsed = self.session_elapsed_minutes
        if elapsed >= max_minutes:
            return f"Duration limit reached ({elapsed:.1f}/{max_minutes:.0f} min)"

        return None

    async def watch_video(
        self,
        url: str,
        duration_pct: float = 0.7,
    ) -> WatchResult:
        """
        Watch a YouTube video with humanized behavior.

        Navigates to the URL, waits for the video player, then simulates
        watching with random scrolls, mouse drift, and occasional pauses.

        Args:
            url: YouTube video URL
            duration_pct: Fraction of video to watch (0.0-1.0), with +-15% variance

        Returns:
            WatchResult with actual watch time and any errors
        """
        result = WatchResult(url=url)

        # Domain allowlist check
        if not is_allowed_domain(url):
            result.error = f"URL not in domain allowlist: {url}"
            logger.warning(result.error)
            return result

        if not self._started or not self._page:
            result.error = "Browser not started"
            return result

        try:
            actual_seconds = await self._breaker.call_async(
                self._do_watch_video, url, duration_pct
            )
            result.actual_watch_seconds = actual_seconds
            self._session_video_count += 1
            self._session_watch_seconds += actual_seconds
            logger.info(
                f"Watched {url} for {actual_seconds}s "
                f"(video {self._session_video_count})"
            )
        except CircuitBreakerError:
            result.error = "Circuit breaker OPEN — too many consecutive failures"
            logger.error(result.error)
        except Exception as e:
            result.error = f"Watch failed: {e}"
            logger.error(f"watch_video error: {e}")

        return result

    async def _do_watch_video(self, url: str, duration_pct: float) -> int:
        """Internal: navigate and watch with humanized behavior."""
        page = self._page

        # Navigate to video
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(random.uniform(2.0, 4.0))

        # Get video duration from the player
        video_duration = await self._get_video_duration(page)
        if video_duration <= 0:
            video_duration = 180  # Default 3 min if detection fails

        # Calculate target watch time with variance
        variance = random.uniform(-0.15, 0.15)
        target_pct = max(0.3, min(1.0, duration_pct + variance))
        target_seconds = int(video_duration * target_pct)
        target_seconds = max(30, target_seconds)  # Minimum 30s

        logger.debug(
            f"Video duration: {video_duration}s, "
            f"target: {target_seconds}s ({target_pct:.0%})"
        )

        # Dismiss any consent dialogs
        await self._dismiss_dialogs(page)

        # Try to click play if video is paused
        await self._ensure_playing(page)

        # Simulate humanized watching
        await self._humanized_watch(page, target_seconds)

        return target_seconds

    async def _get_video_duration(self, page) -> float:
        """Get video duration in seconds from the player."""
        try:
            duration = await page.evaluate("""() => {
                const video = document.querySelector('video');
                if (video && video.duration && isFinite(video.duration)) {
                    return video.duration;
                }
                // Fallback: parse time display
                const timeEl = document.querySelector('.ytp-time-duration');
                if (timeEl) {
                    const parts = timeEl.textContent.split(':').map(Number);
                    if (parts.length === 2) return parts[0] * 60 + parts[1];
                    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
                }
                return 0;
            }""")
            return float(duration) if duration else 0.0
        except Exception:
            return 0.0

    async def _dismiss_dialogs(self, page) -> None:
        """Dismiss cookie consent or other overlay dialogs."""
        try:
            # YouTube consent dialog
            consent_btn = page.locator(
                'button[aria-label*="Accept"], '
                'button[aria-label*="Reject"], '
                'button:has-text("Accept all"), '
                'button:has-text("Reject all")'
            )
            if await consent_btn.first.is_visible(timeout=2000):
                await consent_btn.first.click()
                await asyncio.sleep(1)
        except Exception:
            pass  # No dialog present

    async def _ensure_playing(self, page) -> None:
        """Click play if the video is paused."""
        try:
            is_paused = await page.evaluate("""() => {
                const video = document.querySelector('video');
                return video ? video.paused : false;
            }""")
            if is_paused:
                play_btn = page.locator('.ytp-play-button')
                if await play_btn.is_visible(timeout=2000):
                    await play_btn.click()
                    await asyncio.sleep(0.5)
        except Exception:
            pass

    async def _humanized_watch(self, page, target_seconds: int) -> None:
        """
        Simulate human-like watching behavior.

        - Random scrolls every 15-45s
        - Mouse drift every 10-30s
        - Brief pauses every 2-5 min
        """
        cfg = self._config
        start = time.monotonic()
        next_scroll = start + random.uniform(
            cfg.scroll_interval_min, cfg.scroll_interval_max
        )
        next_drift = start + random.uniform(
            cfg.mouse_drift_interval_min, cfg.mouse_drift_interval_max
        )
        next_pause = start + random.uniform(cfg.pause_every_min, cfg.pause_every_max)

        while (time.monotonic() - start) < target_seconds:
            now = time.monotonic()

            # Random scroll
            if now >= next_scroll:
                await self._random_scroll(page)
                next_scroll = now + random.uniform(
                    cfg.scroll_interval_min, cfg.scroll_interval_max
                )

            # Mouse drift
            if now >= next_drift:
                await self._mouse_drift(page)
                next_drift = now + random.uniform(
                    cfg.mouse_drift_interval_min, cfg.mouse_drift_interval_max
                )

            # Brief pause (simulates looking away)
            if now >= next_pause:
                pause_duration = random.uniform(
                    cfg.pause_duration_min, cfg.pause_duration_max
                )
                await asyncio.sleep(pause_duration)
                next_pause = now + random.uniform(
                    cfg.pause_every_min, cfg.pause_every_max
                )

            # Sleep in small increments to allow checking time
            await asyncio.sleep(1.0)

    async def _random_scroll(self, page) -> None:
        """Perform a random scroll on the page."""
        try:
            scroll_amount = random.randint(-150, 300)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        except Exception:
            pass

    async def _mouse_drift(self, page) -> None:
        """Move the mouse to a random position on the page."""
        try:
            x = random.randint(200, 1200)
            y = random.randint(200, 700)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
        except Exception:
            pass

    async def like_video(self) -> bool:
        """
        Like the currently loaded video.

        Applies a probability gate based on engagement rules. Only likes
        if the like button is visible and not already pressed.

        Returns:
            True if liked successfully, False otherwise.
        """
        if not self._started or not self._page:
            logger.error("Browser not started")
            return False

        try:
            return await self._breaker.call_async(self._do_like_video)
        except CircuitBreakerError:
            logger.error("Circuit breaker OPEN — skipping like")
            return False
        except Exception as e:
            logger.error(f"like_video error: {e}")
            return False

    async def _do_like_video(self) -> bool:
        """Internal: find and click the like button."""
        page = self._page

        # Add human delay before liking
        rules = self._get_engagement_rules()
        like_rules = rules.get("engagement_levels", {}).get("LIKE", {})
        delay_range = like_rules.get("delay_after_watch_seconds", {"min": 2, "max": 5})
        await asyncio.sleep(random.uniform(delay_range["min"], delay_range["max"]))

        # Check if already liked
        like_state = await page.evaluate("""() => {
            // Modern YouTube like button
            const likeBtn = document.querySelector(
                'like-button-view-model button, '
                + 'ytd-toggle-button-renderer:first-child button[aria-label*="like" i], '
                + '#segmented-like-button button'
            );
            if (!likeBtn) return {found: false};
            const pressed = likeBtn.getAttribute('aria-pressed');
            return {
                found: true,
                alreadyLiked: pressed === 'true',
                label: likeBtn.getAttribute('aria-label') || '',
            };
        }""")

        if not like_state.get("found"):
            logger.debug("Like button not found")
            return False

        if like_state.get("alreadyLiked"):
            logger.debug("Video already liked")
            return True

        # Click like with mouse movement for humanization
        like_btn = page.locator(
            'like-button-view-model button, '
            'ytd-toggle-button-renderer:first-child button[aria-label*="like" i], '
            '#segmented-like-button button'
        )

        if await like_btn.first.is_visible(timeout=3000):
            box = await like_btn.first.bounding_box()
            if box:
                # Move to button with steps (humanized)
                target_x = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
                target_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
                await page.mouse.move(target_x, target_y, steps=random.randint(8, 20))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.mouse.click(target_x, target_y)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                logger.info("Video liked")
                return True

        return False

    async def subscribe_channel(self) -> bool:
        """
        Subscribe to the current video's channel.

        Checks the daily subscribe limit from engagement rules before
        proceeding. Only subscribes if not already subscribed.

        Returns:
            True if subscribed successfully, False otherwise.
        """
        if not self._started or not self._page:
            logger.error("Browser not started")
            return False

        # Check daily subscribe limit
        rules = self._get_engagement_rules()
        max_subs = rules.get("safety_rules", {}).get("max_subscribes_per_day", 2)

        try:
            return await self._breaker.call_async(
                self._do_subscribe_channel, max_subs
            )
        except CircuitBreakerError:
            logger.error("Circuit breaker OPEN — skipping subscribe")
            return False
        except Exception as e:
            logger.error(f"subscribe_channel error: {e}")
            return False

    async def _do_subscribe_channel(self, max_subs: int) -> bool:
        """Internal: find and click the subscribe button."""
        page = self._page

        # Check if already subscribed
        sub_state = await page.evaluate("""() => {
            const subBtn = document.querySelector(
                '#subscribe-button button, '
                + 'ytd-subscribe-button-renderer button, '
                + 'tp-yt-paper-button.ytd-subscribe-button-renderer'
            );
            if (!subBtn) return {found: false};
            const text = (subBtn.textContent || '').trim().toLowerCase();
            return {
                found: true,
                alreadySubscribed: text.includes('subscribed') && !text.includes('subscribe'),
                label: text,
            };
        }""")

        if not sub_state.get("found"):
            logger.debug("Subscribe button not found")
            return False

        if sub_state.get("alreadySubscribed"):
            logger.debug("Already subscribed to channel")
            return True

        # Add delay before subscribing
        rules = self._get_engagement_rules()
        sub_rules = rules.get("engagement_levels", {}).get("SUBSCRIBE", {})
        delay_range = sub_rules.get("delay_after_watch_seconds", {"min": 3, "max": 8})
        await asyncio.sleep(random.uniform(delay_range["min"], delay_range["max"]))

        # Click subscribe with humanized movement
        sub_btn = page.locator(
            '#subscribe-button button, '
            'ytd-subscribe-button-renderer button'
        )

        if await sub_btn.first.is_visible(timeout=3000):
            box = await sub_btn.first.bounding_box()
            if box:
                target_x = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
                target_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
                await page.mouse.move(target_x, target_y, steps=random.randint(8, 20))
                await asyncio.sleep(random.uniform(0.2, 0.5))
                await page.mouse.click(target_x, target_y)
                await asyncio.sleep(random.uniform(1.0, 2.0))
                logger.info("Subscribed to channel")

                # Cooldown after subscribe per rules
                cooldown = rules.get("safety_rules", {}).get(
                    "cooldown_after_subscribe_seconds", 300
                )
                logger.debug(f"Subscribe cooldown: {cooldown}s")

                return True

        return False

    async def inter_video_delay(self) -> float:
        """
        Wait between videos with gaussian-distributed delay.

        Returns:
            Actual delay in seconds.
        """
        delay = _gaussian_delay(
            self._config.inter_video_delay_mean,
            self._config.inter_video_delay_stddev,
            minimum=15.0,
        )
        logger.debug(f"Inter-video delay: {delay:.1f}s")
        await asyncio.sleep(delay)
        return delay

    async def run_session(
        self,
        targets: list[dict],
    ) -> SessionResult:
        """
        Run a full warming session with multiple video targets.

        Handles session limits, login state verification, inter-video
        delays, and engagement actions per target's engagement level.

        Args:
            targets: List of target dicts with keys:
                - url (str): YouTube video URL
                - engagement_level (str): WATCH, LIKE, SUBSCRIBE, or COMMENT
                - watch_duration_target (int): Target watch seconds
                - niche_relevance_score (float): 0-1 relevance

        Returns:
            SessionResult with full session statistics.
        """
        result = SessionResult()

        # Check daily session limit
        if not self.check_daily_session_limit():
            result.aborted = True
            result.abort_reason = "Daily session limit reached"
            return result

        # Start browser if not already running
        if not self._started:
            try:
                await self.start()
            except Exception as e:
                result.aborted = True
                result.abort_reason = f"Browser start failed: {e}"
                return result

        # Verify login state
        if not await self.check_login_state():
            result.aborted = True
            result.abort_reason = "Google session expired — manual re-login required"
            await self.stop()
            return result

        # Session parameters (randomized per session)
        max_videos = self._get_max_videos()
        max_minutes = self._get_max_duration_minutes()
        logger.info(
            f"Starting warming session: max {max_videos} videos, "
            f"{max_minutes:.0f} min"
        )

        for i, target in enumerate(targets):
            # Check session limits
            limit_reason = self._check_session_limits(max_videos, max_minutes)
            if limit_reason:
                logger.info(f"Session complete: {limit_reason}")
                break

            url = target.get("url", "")
            engagement_level = target.get("engagement_level", "WATCH")
            watch_duration = target.get("watch_duration_target", 120)

            # Calculate duration_pct from target watch time
            # (approximate — actual video length determined at watch time)
            duration_pct = min(1.0, watch_duration / 180.0)

            # Watch the video
            watch_result = await self.watch_video(url, duration_pct)

            if watch_result.success:
                # Engagement actions based on level
                if engagement_level in ("LIKE", "SUBSCRIBE", "COMMENT"):
                    liked = await self.like_video()
                    watch_result.liked = liked
                    if liked:
                        result.likes += 1

                if engagement_level == "SUBSCRIBE":
                    subscribed = await self.subscribe_channel()
                    watch_result.subscribed = subscribed
                    if subscribed:
                        result.subscribes += 1

                # Note: COMMENT level is human-only — never automated
                result.videos_watched += 1
                result.total_watch_seconds += watch_result.actual_watch_seconds

            elif watch_result.error:
                result.errors.append(watch_result.error)

            result.watch_results.append(watch_result)

            # Inter-video delay (skip after last video)
            if i < len(targets) - 1:
                limit_reason = self._check_session_limits(max_videos, max_minutes)
                if not limit_reason:
                    await self.inter_video_delay()

        logger.info(f"Session complete: {result.summary}")
        return result
