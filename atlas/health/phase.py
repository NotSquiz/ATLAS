"""
ATLAS Phase Management Service

Handles training phase tracking, progression evaluation, and phase transitions.
Integrates with GATE checks for running readiness.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from atlas.health.assessment import AssessmentService

logger = logging.getLogger(__name__)


# GATE requirements per phase transition
GATE_REQUIREMENTS = {
    # phase_1 -> phase_2 requires GATE 1 (running readiness)
    "phase_1": {
        "gate": 1,
        "name": "GATE 1: Running Readiness",
        "description": "Required before progressing to Build phase with running",
    },
    # phase_2 -> phase_3 could require GATE 2/3 (when implemented)
    "phase_2": {
        "gate": 2,
        "name": "GATE 2: Continuous Running",
        "description": "Required before progressing to Develop phase",
    },
}


@dataclass
class PhaseInfo:
    """Information about a training phase."""
    id: int
    name: str
    display_name: str
    weeks_min: int
    weeks_max: Optional[int]
    focus: str
    intensity_range: str
    volume_description: str
    progression_criteria: dict


@dataclass
class CurrentPhaseStatus:
    """Current phase status with progress information."""
    phase: PhaseInfo
    start_date: date
    weeks_completed: int
    days_in_phase: int
    can_advance: bool
    advancement_blockers: list = field(default_factory=list)
    advancement_met: list = field(default_factory=list)
    red_days_this_week: int = 0
    red_days_avg: float = 0.0
    max_pain_level: int = 0
    gate_required: Optional[int] = None
    gate_passed: bool = False
    gate_details: Optional[dict] = None


@dataclass
class ProgressionCheck:
    """Result of checking progression criteria."""
    ready: bool
    criteria_met: list = field(default_factory=list)
    criteria_not_met: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    recommendation: str = ""
    gate_required: Optional[int] = None
    gate_passed: bool = False
    gate_tests_passed: list = field(default_factory=list)
    gate_tests_failed: list = field(default_factory=list)


class PhaseService:
    """Service for managing training phases."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".atlas" / "atlas.db"
        self.assessment_service = AssessmentService(db_path=self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_phases(self) -> list[PhaseInfo]:
        """Get all defined training phases."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT * FROM training_phases ORDER BY id
        """)
        rows = cursor.fetchall()
        conn.close()

        phases = []
        for row in rows:
            criteria = {}
            if row["progression_criteria"]:
                try:
                    criteria = json.loads(row["progression_criteria"])
                except json.JSONDecodeError:
                    pass

            phases.append(PhaseInfo(
                id=row["id"],
                name=row["name"],
                display_name=row["display_name"],
                weeks_min=row["weeks_min"],
                weeks_max=row["weeks_max"],
                focus=row["focus"],
                intensity_range=row["intensity_range"],
                volume_description=row["volume_description"],
                progression_criteria=criteria,
            ))

        return phases

    def get_phase_by_name(self, name: str) -> Optional[PhaseInfo]:
        """Get a specific phase by name."""
        for phase in self.get_all_phases():
            if phase.name == name:
                return phase
        return None

    def get_current_phase(self) -> Optional[CurrentPhaseStatus]:
        """Get current active phase with status."""
        conn = self._get_conn()

        # Get active phase history entry
        cursor = conn.execute("""
            SELECT ph.*, tp.*
            FROM phase_history ph
            JOIN training_phases tp ON ph.phase_id = tp.id
            WHERE ph.status = 'active'
            ORDER BY ph.start_date DESC
            LIMIT 1
        """)
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Parse progression criteria
        criteria = {}
        if row["progression_criteria"]:
            try:
                criteria = json.loads(row["progression_criteria"])
            except json.JSONDecodeError:
                pass

        phase = PhaseInfo(
            id=row["phase_id"],
            name=row["name"],
            display_name=row["display_name"],
            weeks_min=row["weeks_min"],
            weeks_max=row["weeks_max"],
            focus=row["focus"],
            intensity_range=row["intensity_range"],
            volume_description=row["volume_description"],
            progression_criteria=criteria,
        )

        try:
            start_date = datetime.fromisoformat(row["start_date"]).date()
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid start_date in phase_history: {row['start_date']}")
            conn.close()
            return None
        days_in_phase = (date.today() - start_date).days
        weeks_completed = days_in_phase // 7

        # Get RED day count for this week
        week_start = date.today() - timedelta(days=date.today().weekday())
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM workouts
            WHERE date >= ? AND type = 'red_day'
        """, (week_start.isoformat(),))
        red_days_week = cursor.fetchone()["count"]

        # Get average RED days per week over phase
        if weeks_completed > 0:
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM workouts
                WHERE date >= ? AND type = 'red_day'
            """, (start_date.isoformat(),))
            total_red = cursor.fetchone()["count"]
            red_days_avg = total_red / max(weeks_completed, 1)
        else:
            red_days_avg = red_days_week

        # Get max pain level from last 7 days
        cursor = conn.execute("""
            SELECT MAX(pain_level) as max_pain FROM pain_log
            WHERE date >= ?
        """, ((date.today() - timedelta(days=7)).isoformat(),))
        pain_row = cursor.fetchone()
        # Handle case where pain_row is None or max_pain is None
        max_pain = 0
        if pain_row and pain_row["max_pain"] is not None:
            max_pain = pain_row["max_pain"]

        conn.close()

        # Check advancement criteria (including GATE)
        check = self.check_progression(phase, weeks_completed, red_days_avg, max_pain)

        return CurrentPhaseStatus(
            phase=phase,
            start_date=start_date,
            weeks_completed=weeks_completed,
            days_in_phase=days_in_phase,
            can_advance=check.ready,
            advancement_blockers=check.criteria_not_met,
            advancement_met=check.criteria_met,
            red_days_this_week=red_days_week,
            red_days_avg=red_days_avg,
            max_pain_level=max_pain,
            gate_required=check.gate_required,
            gate_passed=check.gate_passed,
            gate_details={
                "tests_passed": check.gate_tests_passed,
                "tests_failed": check.gate_tests_failed,
            } if check.gate_required else None,
        )

    def check_progression(
        self,
        phase: PhaseInfo,
        weeks_completed: int,
        red_days_avg: float,
        max_pain: int,
    ) -> ProgressionCheck:
        """Check if ready to advance to next phase, including GATE requirements."""
        criteria = phase.progression_criteria
        met = []
        not_met = []
        warnings = []

        # Check minimum weeks
        min_weeks = phase.weeks_min
        if weeks_completed >= min_weeks:
            met.append(f"Minimum weeks completed ({weeks_completed}/{min_weeks})")
        else:
            not_met.append(f"Minimum weeks not reached ({weeks_completed}/{min_weeks})")

        # Check max weeks (warning only)
        if phase.weeks_max and weeks_completed > phase.weeks_max:
            warnings.append(f"Exceeded maximum weeks ({weeks_completed}/{phase.weeks_max}) - consider progression")

        # Check RED days
        max_red = criteria.get("min_red_days_per_week", 2)
        if red_days_avg <= max_red:
            met.append(f"RED days acceptable ({red_days_avg:.1f}/week, max {max_red})")
        else:
            not_met.append(f"Too many RED days ({red_days_avg:.1f}/week, max {max_red})")

        # Check pain levels
        max_pain_allowed = criteria.get("max_pain_level", 3)
        if max_pain <= max_pain_allowed:
            met.append(f"Pain levels acceptable (max {max_pain}/10, threshold {max_pain_allowed})")
        else:
            not_met.append(f"Pain too high (max {max_pain}/10, threshold {max_pain_allowed})")

        # Check GATE requirements
        gate_required = None
        gate_passed = False
        gate_tests_passed = []
        gate_tests_failed = []

        if phase.name in GATE_REQUIREMENTS:
            gate_req = GATE_REQUIREMENTS[phase.name]
            gate_required = gate_req["gate"]

            try:
                gate_eval = self.assessment_service.check_gate(gate_required)
                gate_passed = gate_eval.passed
                gate_tests_passed = gate_eval.tests_passed
                gate_tests_failed = gate_eval.tests_failed

                if gate_passed:
                    met.append(f"{gate_req['name']} PASSED")
                else:
                    not_met.append(f"{gate_req['name']} NOT PASSED ({len(gate_tests_failed)} tests failed)")
            except Exception as e:
                logger.warning(f"Could not evaluate GATE {gate_required}: {e}")
                not_met.append(f"{gate_req['name']} - Unable to evaluate (log assessments first)")

        # Determine readiness (must pass all criteria AND GATE if required)
        basic_ready = len([x for x in not_met if "GATE" not in x]) == 0 and weeks_completed >= min_weeks
        ready = basic_ready and (not gate_required or gate_passed)

        if ready:
            recommendation = "Ready to advance to next phase!"
        elif not basic_ready and weeks_completed < min_weeks:
            weeks_left = min_weeks - weeks_completed
            recommendation = f"Continue current phase for {weeks_left} more week(s)."
        elif gate_required and not gate_passed:
            recommendation = f"Pass {GATE_REQUIREMENTS[phase.name]['name']} before advancing. Run 'assess gate {gate_required}' for details."
        else:
            recommendation = "Address blockers before advancing."

        return ProgressionCheck(
            ready=ready,
            criteria_met=met,
            criteria_not_met=not_met,
            warnings=warnings,
            recommendation=recommendation,
            gate_required=gate_required,
            gate_passed=gate_passed,
            gate_tests_passed=gate_tests_passed,
            gate_tests_failed=gate_tests_failed,
        )

    def start_phase(self, phase_name: str = "phase_1") -> int:
        """Start a new phase (usually phase_1 for new users)."""
        conn = self._get_conn()

        # Get phase ID
        cursor = conn.execute(
            "SELECT id FROM training_phases WHERE name = ?",
            (phase_name,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Unknown phase: {phase_name}")

        phase_id = row["id"]

        # End any active phases
        conn.execute("""
            UPDATE phase_history
            SET status = 'completed', end_date = ?, exit_reason = 'new_phase_started'
            WHERE status = 'active'
        """, (date.today().isoformat(),))

        # Start new phase
        cursor = conn.execute("""
            INSERT INTO phase_history (phase_id, start_date, status)
            VALUES (?, ?, 'active')
        """, (phase_id, date.today().isoformat()))

        conn.commit()
        history_id = cursor.lastrowid
        conn.close()

        logger.info(f"Started {phase_name}")
        return history_id

    def advance_phase(self, force: bool = False) -> tuple[bool, str]:
        """Advance to the next phase."""
        current = self.get_current_phase()

        if not current:
            # No active phase - start phase 1
            self.start_phase("phase_1")
            return True, "Started Phase 1: Foundation"

        # Check if ready
        if not current.can_advance and not force:
            blockers = ", ".join(current.advancement_blockers)
            return False, f"Not ready to advance. Blockers: {blockers}"

        # Determine next phase
        phases = self.get_all_phases()
        current_idx = next(
            (i for i, p in enumerate(phases) if p.name == current.phase.name),
            -1
        )

        if current_idx == -1 or current_idx >= len(phases) - 1:
            return False, "Already at final phase"

        next_phase = phases[current_idx + 1]

        conn = self._get_conn()

        # End current phase
        conn.execute("""
            UPDATE phase_history
            SET status = 'completed', end_date = ?, exit_reason = 'progression'
            WHERE status = 'active'
        """, (date.today().isoformat(),))

        # Start next phase
        conn.execute("""
            INSERT INTO phase_history (phase_id, start_date, status)
            VALUES (?, ?, 'active')
        """, (next_phase.id, date.today().isoformat()))

        conn.commit()
        conn.close()

        logger.info(f"Advanced from {current.phase.display_name} to {next_phase.display_name}")
        return True, f"Advanced to {next_phase.display_name}: {next_phase.focus}"

    def regress_phase(self, reason: str = "manual") -> tuple[bool, str]:
        """Regress to previous phase."""
        current = self.get_current_phase()

        if not current:
            return False, "No active phase to regress from"

        phases = self.get_all_phases()
        current_idx = next(
            (i for i, p in enumerate(phases) if p.name == current.phase.name),
            -1
        )

        if current_idx <= 0:
            return False, "Already at first phase"

        prev_phase = phases[current_idx - 1]

        conn = self._get_conn()

        # End current phase
        conn.execute("""
            UPDATE phase_history
            SET status = 'regressed', end_date = ?, exit_reason = ?
            WHERE status = 'active'
        """, (date.today().isoformat(), reason))

        # Start previous phase
        conn.execute("""
            INSERT INTO phase_history (phase_id, start_date, status, notes)
            VALUES (?, ?, 'active', ?)
        """, (prev_phase.id, date.today().isoformat(), f"Regressed from {current.phase.display_name}: {reason}"))

        conn.commit()
        conn.close()

        logger.info(f"Regressed from {current.phase.display_name} to {prev_phase.display_name}: {reason}")
        return True, f"Regressed to {prev_phase.display_name}"

    def get_phase_history(self) -> list[dict]:
        """Get history of all phase transitions."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT ph.*, tp.display_name, tp.name as phase_name
            FROM phase_history ph
            JOIN training_phases tp ON ph.phase_id = tp.id
            ORDER BY ph.start_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def check_regression_triggers(self) -> list[str]:
        """Check for automatic regression triggers."""
        triggers = []
        conn = self._get_conn()

        # Check for 3+ RED days this week
        week_start = date.today() - timedelta(days=date.today().weekday())
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM workouts
            WHERE date >= ? AND type = 'red_day'
        """, (week_start.isoformat(),))
        red_days = cursor.fetchone()["count"]
        if red_days >= 3:
            triggers.append(f"3+ RED days this week ({red_days})")

        # Check for pain spike (6+/10)
        cursor = conn.execute("""
            SELECT MAX(pain_level) as max_pain, body_part FROM pain_log
            WHERE date >= ?
            GROUP BY body_part
            HAVING max_pain >= 6
        """, ((date.today() - timedelta(days=7)).isoformat(),))
        pain_spikes = cursor.fetchall()
        for spike in pain_spikes:
            triggers.append(f"Pain spike: {spike['body_part']} at {spike['max_pain']}/10")

        conn.close()
        return triggers

    def log_red_day(self) -> int:
        """Log a RED day (for tracking purposes)."""
        conn = self._get_conn()
        cursor = conn.execute("""
            INSERT INTO workouts (date, type, duration_minutes, notes)
            VALUES (?, 'red_day', 40, 'RED day protocol - recovery')
        """, (date.today().isoformat(),))
        conn.commit()
        workout_id = cursor.lastrowid
        conn.close()
        return workout_id
