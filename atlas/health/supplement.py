"""
Supplement Service

Daily supplement tracking with yes/no checklist.

Usage:
    from atlas.health.supplement import SupplementService

    service = SupplementService()

    # Get today's checklist
    checklist = service.get_today()
    print(f"Progress: {checklist.completion_pct:.0%}")

    # Mark as taken
    service.mark_taken("Vitamin D")

    # Mark all morning supplements
    service.mark_all_taken(timing="morning")
"""

import logging
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional

from atlas.memory.blueprint import (
    get_blueprint_api,
    Supplement,
    SupplementLog,
)

logger = logging.getLogger(__name__)


@dataclass
class SupplementStatus:
    """Status of a single supplement for a day."""
    id: int
    name: str
    dosage: Optional[str]
    timing: Optional[str]
    taken: bool
    time_taken: Optional[time] = None
    notes: Optional[str] = None


@dataclass
class SupplementChecklist:
    """Daily supplement checklist."""
    date: date
    supplements: list[SupplementStatus] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total number of supplements."""
        return len(self.supplements)

    @property
    def taken_count(self) -> int:
        """Number of supplements taken."""
        return sum(1 for s in self.supplements if s.taken)

    @property
    def completion_pct(self) -> float:
        """Completion percentage."""
        if self.total == 0:
            return 100.0
        return self.taken_count / self.total * 100

    def by_timing(self, timing: str) -> list[SupplementStatus]:
        """Get supplements filtered by timing."""
        return [s for s in self.supplements if s.timing == timing]

    def to_display(self) -> str:
        """Format checklist for CLI display."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  SUPPLEMENTS - {self.date.strftime('%B %d, %Y')}")
        lines.append("=" * 60)

        # Group by timing
        timings = ["preworkout", "with_meal", "before_bed", None]
        timing_labels = {
            "preworkout": "PREWORKOUT",
            "with_meal": "WITH MEALS",
            "before_bed": "BEFORE BED",
            None: "OTHER",
        }

        for timing in timings:
            supps = self.by_timing(timing)
            if not supps:
                continue

            lines.append("")
            lines.append(f"{timing_labels.get(timing, 'OTHER')}:")

            for s in supps:
                check = "\u2713" if s.taken else "\u25CB"
                time_str = f"taken {s.time_taken.strftime('%H:%M')}" if s.time_taken else "pending"
                dosage_str = f"({s.dosage})" if s.dosage else ""
                lines.append(f"  {check} {s.name:<25} {dosage_str:<15} {time_str}")

        lines.append("")
        lines.append("-" * 60)
        lines.append(f"  Progress: {self.taken_count}/{self.total} ({self.completion_pct:.0f}%)")
        lines.append("=" * 60)

        return "\n".join(lines)


class SupplementService:
    """
    Daily supplement tracking service.

    Integrates with BlueprintAPI for database operations.
    """

    def __init__(self):
        """Initialize supplement service."""
        self._blueprint = get_blueprint_api()

    def get_active_supplements(self) -> list[Supplement]:
        """Get all active supplements from catalog."""
        return self._blueprint.get_supplements(active_only=True)

    def get_today(self, target_date: Optional[date] = None) -> SupplementChecklist:
        """
        Get today's supplement checklist with status.

        Args:
            target_date: Date to get checklist for (default: today)

        Returns:
            SupplementChecklist with all supplements and their status
        """
        if target_date is None:
            target_date = date.today()

        # Get all active supplements
        supplements = self.get_active_supplements()

        # Get today's log entries
        logs = self._blueprint.get_supplement_log(days=1)
        today_logs = {
            log.supplement_id: log
            for log in logs
            if log.date == target_date
        }

        # Build checklist
        statuses = []
        for supp in supplements:
            log = today_logs.get(supp.id)
            statuses.append(SupplementStatus(
                id=supp.id,
                name=supp.name,
                dosage=supp.dosage,
                timing=supp.timing,
                taken=log.taken if log else False,
                time_taken=log.time if log else None,
                notes=log.notes if log else None,
            ))

        return SupplementChecklist(date=target_date, supplements=statuses)

    def mark_taken(
        self,
        name: str,
        taken: bool = True,
        time_taken: Optional[time] = None,
        notes: Optional[str] = None,
        target_date: Optional[date] = None,
    ) -> bool:
        """
        Mark a supplement as taken or not taken.

        Args:
            name: Supplement name (case-insensitive partial match)
            taken: Whether it was taken (default True)
            time_taken: Time taken (default: now)
            notes: Optional notes
            target_date: Date for the log (default: today)

        Returns:
            True if successful, False if supplement not found
        """
        if target_date is None:
            target_date = date.today()
        if time_taken is None:
            time_taken = datetime.now().time()

        # Find supplement by name (case-insensitive)
        supplements = self.get_active_supplements()
        name_lower = name.lower()

        matched = None
        for supp in supplements:
            if supp.name.lower() == name_lower:
                matched = supp
                break
            elif name_lower in supp.name.lower():
                matched = supp
                # Don't break - prefer exact match

        if not matched:
            logger.warning(f"Supplement not found: {name}")
            return False

        # Check if already logged today
        logs = self._blueprint.get_supplement_log(days=1, supplement_id=matched.id)
        existing = next((l for l in logs if l.date == target_date), None)

        if existing:
            # Update existing log (need to implement update in blueprint)
            # For now, we'll just log a new entry
            logger.info(f"Supplement already logged today: {matched.name}")

        # Log the dose
        log = SupplementLog(
            supplement_id=matched.id,
            date=target_date,
            taken=taken,
            time=time_taken,
            notes=notes,
        )
        self._blueprint.log_supplement_dose(log)

        status = "taken" if taken else "skipped"
        logger.info(f"Marked {matched.name} as {status} at {time_taken}")
        return True

    def mark_all_taken(
        self,
        timing: Optional[str] = None,
        target_date: Optional[date] = None,
    ) -> int:
        """
        Mark all supplements (or by timing) as taken.

        Args:
            timing: Filter by timing ('morning', 'with_meal', 'before_bed')
            target_date: Date for the log (default: today)

        Returns:
            Number of supplements marked
        """
        if target_date is None:
            target_date = date.today()

        supplements = self.get_active_supplements()
        time_taken = datetime.now().time()

        count = 0
        for supp in supplements:
            if timing and supp.timing != timing:
                continue

            log = SupplementLog(
                supplement_id=supp.id,
                date=target_date,
                taken=True,
                time=time_taken,
            )
            self._blueprint.log_supplement_dose(log)
            count += 1

        timing_str = f" ({timing})" if timing else ""
        logger.info(f"Marked {count} supplements{timing_str} as taken")

        # Award XP for batch completion (non-blocking)
        if count > 0:
            self._award_supplement_xp(timing)

        return count

    def _award_supplement_xp(self, timing: Optional[str]) -> None:
        """Award XP for completing supplement batch (non-blocking)."""
        try:
            from atlas.gamification.xp_service import award_xp_safe_async, XP_TABLE
            xp = XP_TABLE.get("supplement_batch", 25)
            source = f"supplement_{timing}" if timing else "supplement_batch"
            award_xp_safe_async("nutrition", xp, source)
        except Exception as e:
            # XP failure should never break supplement logging
            logger.debug(f"XP award skipped: {e}")

    def get_streak(self, name: str, target_date: Optional[date] = None) -> int:
        """
        Get consecutive days a supplement has been taken.

        Args:
            name: Supplement name
            target_date: End date for streak calculation (default: today)

        Returns:
            Number of consecutive days
        """
        if target_date is None:
            target_date = date.today()

        # Find supplement
        supplements = self.get_active_supplements()
        name_lower = name.lower()
        matched = next(
            (s for s in supplements if s.name.lower() == name_lower or name_lower in s.name.lower()),
            None
        )

        if not matched:
            return 0

        # Get logs for past 30 days
        logs = self._blueprint.get_supplement_log(days=30, supplement_id=matched.id)

        # Count consecutive days
        streak = 0
        check_date = target_date

        from datetime import timedelta

        while True:
            log = next((l for l in logs if l.date == check_date and l.taken), None)
            if log:
                streak += 1
                check_date = check_date - timedelta(days=1)
            else:
                break

        return streak

    def get_weekly_compliance(self) -> dict:
        """Get weekly supplement compliance stats."""
        checklist = self.get_today()
        supplements = self.get_active_supplements()

        # Get logs for past 7 days
        logs = self._blueprint.get_supplement_log(days=7)

        # Count per supplement
        compliance = {}
        for supp in supplements:
            supp_logs = [l for l in logs if l.supplement_id == supp.id and l.taken]
            compliance[supp.name] = len(supp_logs)

        total_possible = len(supplements) * 7
        total_taken = sum(compliance.values())

        return {
            "by_supplement": compliance,
            "total_taken": total_taken,
            "total_possible": total_possible,
            "compliance_pct": total_taken / total_possible * 100 if total_possible > 0 else 0,
        }

    def add_supplement(
        self,
        name: str,
        dosage: Optional[str] = None,
        timing: Optional[str] = None,
        purpose: Optional[str] = None,
        brand: Optional[str] = None,
    ) -> int:
        """
        Add a new supplement to the catalog.

        Args:
            name: Supplement name
            dosage: Dosage (e.g., "5000 IU", "500mg")
            timing: When to take ('morning', 'with_meal', 'before_bed')
            purpose: Why taking this supplement
            brand: Brand name

        Returns:
            Supplement ID
        """
        supp = Supplement(
            name=name,
            dosage=dosage,
            timing=timing,
            purpose=purpose,
            brand=brand,
            active=True,
        )
        supp_id = self._blueprint.add_supplement(supp)
        logger.info(f"Added supplement: {name} (ID: {supp_id})")
        return supp_id
