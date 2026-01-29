"""
ATLAS Scheduler Loop

Background automation that transforms ATLAS from reactive to proactive.
Runs scheduled tasks like digest generation without user intervention.

"AI running a loop, not just AI as search."

Usage:
    # Run interactively
    python -m atlas.scheduler.loop

    # Run in background
    python -m atlas.scheduler.loop --daemon

    # Run once (for cron)
    python -m atlas.scheduler.loop --once daily

    # Generate systemd service
    python -m atlas.scheduler.loop --generate-systemd
"""

import asyncio
import logging
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for scheduled tasks."""

    # Daily digest timing (default: 7:00 AM)
    daily_digest_hour: int = 7
    daily_digest_minute: int = 0

    # Weekly review timing (default: Sunday 6:00 PM)
    weekly_review_day: int = 6  # 0=Monday, 6=Sunday
    weekly_review_hour: int = 18
    weekly_review_minute: int = 0

    # Output settings
    output_dir: Optional[Path] = None
    voice_output: bool = False
    notification: bool = True

    # Check interval (seconds)
    check_interval: int = 60


@dataclass
class ScheduledTask:
    """A scheduled task."""

    name: str
    func: Callable
    schedule_check: Callable[[datetime], bool]
    last_run: Optional[datetime] = None
    enabled: bool = True


class ATLASScheduler:
    """
    Background scheduler for ATLAS proactive features.

    Runs scheduled tasks:
    - Daily digest generation (morning)
    - Weekly review generation (Sunday evening)

    Usage:
        scheduler = ATLASScheduler()

        # Run in foreground (blocking)
        scheduler.run()

        # Run single task
        scheduler.run_task("daily_digest")

        # Check what would run
        scheduler.check_schedule()
    """

    def __init__(self, config: Optional[ScheduleConfig] = None):
        """Initialize scheduler with optional config."""
        self.config = config or ScheduleConfig()
        self.tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._setup_default_tasks()

    def _setup_default_tasks(self) -> None:
        """Set up default scheduled tasks."""

        # Daily digest
        def daily_check(now: datetime) -> bool:
            return (
                now.hour == self.config.daily_digest_hour
                and now.minute == self.config.daily_digest_minute
            )

        self.tasks["daily_digest"] = ScheduledTask(
            name="Daily Digest",
            func=self._run_daily_digest,
            schedule_check=daily_check,
        )

        # Weekly review
        def weekly_check(now: datetime) -> bool:
            return (
                now.weekday() == self.config.weekly_review_day
                and now.hour == self.config.weekly_review_hour
                and now.minute == self.config.weekly_review_minute
            )

        self.tasks["weekly_review"] = ScheduledTask(
            name="Weekly Review",
            func=self._run_weekly_review,
            schedule_check=weekly_check,
        )

    def _run_daily_digest(self) -> str:
        """Generate and output daily digest."""
        from atlas.digest import DigestGenerator

        logger.info("Generating daily digest...")
        generator = DigestGenerator()
        digest = generator.generate_daily()

        output = digest.to_voice() if self.config.voice_output else digest.to_text()

        # Save to file if output_dir configured
        if self.config.output_dir:
            output_file = self.config.output_dir / f"digest_{datetime.now():%Y%m%d}.txt"
            output_file.write_text(output)
            logger.info(f"Saved digest to {output_file}")

        logger.info(f"Daily digest generated ({digest.word_count} words)")
        return output

    def _run_weekly_review(self) -> str:
        """Generate and output weekly review."""
        from atlas.digest import DigestGenerator

        logger.info("Generating weekly review...")
        generator = DigestGenerator()
        review = generator.generate_weekly()

        output = review.to_text()

        # Save to file if output_dir configured
        if self.config.output_dir:
            output_file = (
                self.config.output_dir / f"review_{datetime.now():%Y%m%d}.txt"
            )
            output_file.write_text(output)
            logger.info(f"Saved review to {output_file}")

        logger.info(f"Weekly review generated ({review.word_count} words)")
        return output

    def run_task(self, task_name: str) -> Optional[str]:
        """
        Run a specific task immediately.

        Args:
            task_name: Name of task to run

        Returns:
            Task output or None if task not found
        """
        task = self.tasks.get(task_name)
        if not task:
            logger.error(f"Task not found: {task_name}")
            return None

        logger.info(f"Running task: {task.name}")
        try:
            result = task.func()
            task.last_run = datetime.now()
            return result
        except Exception as e:
            logger.error(f"Task {task.name} failed: {e}")
            raise

    def check_schedule(self) -> list[str]:
        """
        Check which tasks would run at the current time.

        Returns:
            List of task names that would run
        """
        now = datetime.now()
        due_tasks = []

        for name, task in self.tasks.items():
            if not task.enabled:
                continue

            if task.schedule_check(now):
                # Check if already run this minute
                if task.last_run:
                    elapsed = now - task.last_run
                    if elapsed < timedelta(minutes=1):
                        continue
                due_tasks.append(name)

        return due_tasks

    def _check_and_run(self) -> None:
        """Check schedule and run due tasks."""
        due_tasks = self.check_schedule()

        for task_name in due_tasks:
            try:
                self.run_task(task_name)
            except Exception as e:
                logger.error(f"Failed to run {task_name}: {e}")

    def run(self) -> None:
        """
        Run the scheduler loop (blocking).

        Checks schedule every minute and runs due tasks.
        """
        self._running = True
        logger.info("ATLAS Scheduler started")
        logger.info(f"Daily digest: {self.config.daily_digest_hour:02d}:{self.config.daily_digest_minute:02d}")
        logger.info(f"Weekly review: Day {self.config.weekly_review_day}, {self.config.weekly_review_hour:02d}:{self.config.weekly_review_minute:02d}")

        # Set up signal handlers
        def handle_signal(signum, frame):
            logger.info("Received shutdown signal")
            self._running = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        try:
            while self._running:
                self._check_and_run()

                # Sleep until next check
                for _ in range(self.config.check_interval):
                    if not self._running:
                        break
                    asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))

        except KeyboardInterrupt:
            logger.info("Scheduler interrupted")
        finally:
            logger.info("ATLAS Scheduler stopped")

    def get_next_run(self, task_name: str) -> Optional[datetime]:
        """
        Get the next scheduled run time for a task.

        Args:
            task_name: Name of task

        Returns:
            Next run datetime or None
        """
        task = self.tasks.get(task_name)
        if not task:
            return None

        now = datetime.now()

        if task_name == "daily_digest":
            next_run = now.replace(
                hour=self.config.daily_digest_hour,
                minute=self.config.daily_digest_minute,
                second=0,
                microsecond=0,
            )
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif task_name == "weekly_review":
            next_run = now.replace(
                hour=self.config.weekly_review_hour,
                minute=self.config.weekly_review_minute,
                second=0,
                microsecond=0,
            )
            days_until = (self.config.weekly_review_day - now.weekday()) % 7
            if days_until == 0 and next_run <= now:
                days_until = 7
            next_run += timedelta(days=days_until)
            return next_run

        return None

    def status(self) -> dict:
        """Get scheduler status."""
        return {
            "running": self._running,
            "tasks": {
                name: {
                    "enabled": task.enabled,
                    "last_run": str(task.last_run) if task.last_run else None,
                    "next_run": str(self.get_next_run(name)),
                }
                for name, task in self.tasks.items()
            },
            "config": {
                "daily_time": f"{self.config.daily_digest_hour:02d}:{self.config.daily_digest_minute:02d}",
                "weekly_day": self.config.weekly_review_day,
                "weekly_time": f"{self.config.weekly_review_hour:02d}:{self.config.weekly_review_minute:02d}",
            },
        }


def generate_systemd_service() -> str:
    """Generate a systemd service file for the scheduler."""
    import os

    python_path = sys.executable
    atlas_path = Path(__file__).parent.parent.parent
    user = os.environ.get("USER", "squiz")

    return f"""[Unit]
Description=ATLAS Scheduler - Proactive AI Assistant
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={atlas_path}
Environment=PYTHONPATH={atlas_path}
ExecStart={python_path} -m atlas.scheduler.loop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""


def generate_cron_entries() -> str:
    """Generate cron entries for the scheduler."""
    python_path = sys.executable
    atlas_path = Path(__file__).parent.parent.parent

    return f"""# ATLAS Scheduler - Proactive AI Assistant
# Add to crontab with: crontab -e

# Daily digest at 7:00 AM
0 7 * * * cd {atlas_path} && {python_path} -m atlas.scheduler.loop --once daily_digest >> /tmp/atlas_digest.log 2>&1

# Weekly review on Sunday at 6:00 PM
0 18 * * 0 cd {atlas_path} && {python_path} -m atlas.scheduler.loop --once weekly_review >> /tmp/atlas_review.log 2>&1
"""


def main():
    """CLI for the scheduler."""
    import argparse

    parser = argparse.ArgumentParser(description="ATLAS Scheduler")
    parser.add_argument(
        "--once",
        metavar="TASK",
        help="Run a single task and exit (daily_digest or weekly_review)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (background process)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show scheduler status",
    )
    parser.add_argument(
        "--generate-systemd",
        action="store_true",
        help="Generate systemd service file",
    )
    parser.add_argument(
        "--generate-cron",
        action="store_true",
        help="Generate cron entries",
    )
    parser.add_argument(
        "--daily-hour",
        type=int,
        default=7,
        help="Hour for daily digest (default: 7)",
    )
    parser.add_argument(
        "--daily-minute",
        type=int,
        default=0,
        help="Minute for daily digest (default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to save outputs",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Generate config files
    if args.generate_systemd:
        print(generate_systemd_service())
        return

    if args.generate_cron:
        print(generate_cron_entries())
        return

    # Create config
    config = ScheduleConfig(
        daily_digest_hour=args.daily_hour,
        daily_digest_minute=args.daily_minute,
        output_dir=args.output_dir,
    )

    scheduler = ATLASScheduler(config)

    # Show status
    if args.status:
        import json
        print(json.dumps(scheduler.status(), indent=2))
        return

    # Run single task
    if args.once:
        output = scheduler.run_task(args.once)
        if output:
            print(output)
        return

    # Daemon mode
    if args.daemon:
        import os
        # Fork and detach
        if os.fork() > 0:
            sys.exit(0)
        os.setsid()
        if os.fork() > 0:
            sys.exit(0)

        # Redirect stdio
        sys.stdin = open("/dev/null", "r")
        sys.stdout = open("/tmp/atlas_scheduler.log", "a")
        sys.stderr = sys.stdout

    # Run scheduler loop
    print("Starting ATLAS Scheduler...")
    print("Press Ctrl+C to stop")
    scheduler.run()


if __name__ == "__main__":
    main()
