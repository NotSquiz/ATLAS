"""
Pain Tracking Service

Simple service for logging and querying daily pain levels.

Usage:
    from atlas.health.pain import PainService

    service = PainService()
    service.log_pain("shoulder_right", 5, notes="After workout")
    today = service.get_today()
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PainTrend:
    """Pain trend analysis for a body part."""
    body_part: str
    slope: float  # Positive = increasing pain, negative = decreasing
    avg_pain: float
    days_analyzed: int
    trending_up: bool  # slope > 0.5 indicates concerning upward trend
    data_points: int


# Valid body parts for Alexander's tracked injuries
BODY_PARTS = [
    "shoulder_right",
    "shoulder_left",
    "feet",
    "ankle_left",
    "ankle_right",
    "lower_back",
]


@dataclass
class PainEntry:
    """Single pain log entry."""
    body_part: str
    pain_level: Optional[int]
    stiffness_level: Optional[int] = None
    notes: Optional[str] = None
    date: Optional[date] = None
    measured_at: Optional[datetime] = None


@dataclass
class DailyPain:
    """All pain entries for a day."""
    date: date
    entries: list[PainEntry]

    @property
    def max_pain(self) -> int:
        """Maximum pain level across all body parts."""
        levels = [e.pain_level for e in self.entries if e.pain_level is not None]
        return max(levels) if levels else 0

    @property
    def avg_pain(self) -> float:
        """Average pain level across all body parts."""
        levels = [e.pain_level for e in self.entries if e.pain_level is not None]
        return sum(levels) / len(levels) if levels else 0.0

    @property
    def has_high_pain(self) -> bool:
        """Check if any body part has pain >= 6."""
        return self.max_pain >= 6


class PainService:
    """
    Pain tracking service using SQLite.

    Tracks pain levels for Alexander's injury areas:
    - shoulder_right (rotator cuff)
    - ankle_left, ankle_right (worse on left)
    - lower_back
    - feet
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize PainService.

        Args:
            db_path: Path to SQLite database (default: ~/.atlas/atlas.db)
        """
        self.db_path = db_path or (Path.home() / ".atlas" / "atlas.db")

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def log_pain(
        self,
        body_part: str,
        pain_level: int,
        stiffness_level: Optional[int] = None,
        notes: Optional[str] = None,
        measured_at: Optional[datetime] = None,
        target_date: Optional[date] = None,
    ) -> bool:
        """
        Log pain for a body part.

        Args:
            body_part: Body part identifier (e.g., "shoulder_right")
            pain_level: Pain level 0-10
            stiffness_level: Optional stiffness level 0-10
            notes: Optional notes
            measured_at: When pain was measured (default: now)
            target_date: Date to log for (default: today)

        Returns:
            True if logged successfully
        """
        if target_date is None:
            target_date = date.today()

        if measured_at is None:
            measured_at = datetime.now()

        if body_part not in BODY_PARTS:
            logger.warning(f"Unknown body part: {body_part}")
            # Still allow logging for flexibility
            pass

        if not 0 <= pain_level <= 10:
            logger.error(f"Invalid pain level: {pain_level}")
            return False

        conn = self._get_conn()
        try:
            # Use INSERT OR REPLACE to update if entry exists for date+body_part
            conn.execute("""
                INSERT OR REPLACE INTO pain_log
                (date, body_part, pain_level, stiffness_level, notes, measured_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                target_date.isoformat(),
                body_part,
                pain_level,
                stiffness_level,
                notes,
                measured_at.isoformat() if measured_at else None
            ))
            conn.commit()
            logger.info(f"Logged pain: {body_part}={pain_level}")
            return True
        except Exception as e:
            logger.error(f"Failed to log pain: {e}")
            return False
        finally:
            conn.close()

    def get_today(self, target_date: Optional[date] = None) -> DailyPain:
        """
        Get all pain entries for a date.

        Args:
            target_date: Date to query (default: today)

        Returns:
            DailyPain with all entries for the date
        """
        if target_date is None:
            target_date = date.today()

        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT body_part, pain_level, stiffness_level, notes, measured_at
                FROM pain_log
                WHERE date = ?
            """, (target_date.isoformat(),))

            entries = []
            for row in cursor.fetchall():
                entries.append(PainEntry(
                    body_part=row["body_part"],
                    pain_level=row["pain_level"],
                    stiffness_level=row["stiffness_level"],
                    notes=row["notes"],
                    date=target_date,
                    measured_at=datetime.fromisoformat(row["measured_at"]) if row["measured_at"] else None,
                ))

            return DailyPain(date=target_date, entries=entries)
        finally:
            conn.close()

    def get_recent(self, days: int = 3) -> list[PainEntry]:
        """
        Get recent pain entries across multiple days.

        Args:
            days: Number of days to look back

        Returns:
            List of PainEntry ordered by date descending
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT date, body_part, pain_level, stiffness_level, notes, measured_at
                FROM pain_log
                WHERE date >= date('now', ?)
                ORDER BY date DESC, body_part
            """, (f"-{days} days",))

            entries = []
            for row in cursor.fetchall():
                entries.append(PainEntry(
                    body_part=row["body_part"],
                    pain_level=row["pain_level"],
                    stiffness_level=row["stiffness_level"],
                    notes=row["notes"],
                    date=date.fromisoformat(row["date"]),
                    measured_at=datetime.fromisoformat(row["measured_at"]) if row["measured_at"] else None,
                ))

            return entries
        finally:
            conn.close()

    def format_voice(self, body_part: str, pain_level: int) -> str:
        """
        Format pain log confirmation for voice response.

        Uses Lethal Gentleman persona - terse, direct, actionable.

        Args:
            body_part: Body part that was logged
            pain_level: Pain level that was logged

        Returns:
            Voice response string
        """
        # Clean up body part name for voice
        part_name = body_part.replace("_", " ")

        if pain_level == 0:
            return f"Logged {part_name} at zero. No pain. Good."
        elif pain_level <= 2:
            return f"Logged {part_name} at {pain_level}. Manageable."
        elif pain_level <= 4:
            return f"Logged {part_name} at {pain_level}. Monitor it."
        elif pain_level <= 6:
            return f"Logged {part_name} at {pain_level}. Consider modifications."
        else:
            return f"Logged {part_name} at {pain_level}. That's elevated. Recovery priority."

    def format_status_voice(self) -> str:
        """
        Format pain status for voice response.

        Returns:
            Voice summary of recent pain levels
        """
        today = self.get_today()

        if not today.entries:
            return "No pain logged today."

        parts = []
        for entry in today.entries:
            if entry.pain_level is not None:
                part_name = entry.body_part.replace("_", " ")
                parts.append(f"{part_name} {entry.pain_level}")

        if not parts:
            return "No pain levels logged today."

        return "Pain levels: " + ", ".join(parts) + "."

    def get_trend(self, body_part: str, days: int = 7) -> Optional[PainTrend]:
        """
        Calculate pain trend for a body part over specified days.

        Uses simple linear regression to determine if pain is increasing.
        A slope > 0.5 indicates a concerning upward trend that should
        prevent weight progression recommendations.

        Args:
            body_part: Body part to analyze (e.g., "shoulder_right")
            days: Number of days to look back

        Returns:
            PainTrend with slope and analysis, or None if insufficient data
        """
        conn = self._get_conn()
        try:
            # Get pain entries for the specified period
            cutoff = (date.today() - timedelta(days=days)).isoformat()
            cursor = conn.execute("""
                SELECT date, pain_level
                FROM pain_log
                WHERE body_part = ? AND date >= ? AND pain_level IS NOT NULL
                ORDER BY date ASC
            """, (body_part, cutoff))

            rows = cursor.fetchall()
            if len(rows) < 2:
                return None  # Need at least 2 points for trend

            # Convert to day numbers (0 = oldest day in range)
            base_date = date.fromisoformat(rows[0]["date"])
            points = []
            for row in rows:
                row_date = date.fromisoformat(row["date"])
                day_num = (row_date - base_date).days
                points.append((day_num, row["pain_level"]))

            # Simple linear regression: slope = Cov(x,y) / Var(x)
            n = len(points)
            sum_x = sum(p[0] for p in points)
            sum_y = sum(p[1] for p in points)
            sum_xy = sum(p[0] * p[1] for p in points)
            sum_x2 = sum(p[0] ** 2 for p in points)

            mean_x = sum_x / n
            mean_y = sum_y / n

            # Avoid division by zero (all same day)
            var_x = sum_x2 / n - mean_x ** 2
            if var_x == 0:
                slope = 0.0
            else:
                cov_xy = sum_xy / n - mean_x * mean_y
                slope = cov_xy / var_x

            return PainTrend(
                body_part=body_part,
                slope=round(slope, 3),
                avg_pain=round(mean_y, 1),
                days_analyzed=days,
                trending_up=slope > 0.5,
                data_points=n,
            )
        finally:
            conn.close()

    def get_max_recent_pain(self, body_parts: Optional[list[str]] = None, days: int = 1) -> int:
        """
        Get maximum pain level across body parts in recent period.

        Useful for deload trigger: pain spike >= 6 triggers immediate deload.

        Args:
            body_parts: Body parts to check (None = all)
            days: Number of days to look back

        Returns:
            Maximum pain level (0 if no data)
        """
        conn = self._get_conn()
        try:
            cutoff = (date.today() - timedelta(days=days)).isoformat()

            if body_parts:
                placeholders = ",".join("?" * len(body_parts))
                cursor = conn.execute(f"""
                    SELECT MAX(pain_level) as max_pain
                    FROM pain_log
                    WHERE body_part IN ({placeholders}) AND date >= ?
                """, (*body_parts, cutoff))
            else:
                cursor = conn.execute("""
                    SELECT MAX(pain_level) as max_pain
                    FROM pain_log
                    WHERE date >= ?
                """, (cutoff,))

            row = cursor.fetchone()
            return row["max_pain"] if row and row["max_pain"] else 0
        finally:
            conn.close()


# Convenience function for quick logging
def log_pain(body_part: str, pain_level: int, **kwargs) -> bool:
    """Quick pain logging without instantiating service."""
    service = PainService()
    return service.log_pain(body_part, pain_level, **kwargs)
