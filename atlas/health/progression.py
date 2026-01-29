"""
ATLAS Progressive Overload Service

Handles weight recommendations, progression tracking, and deload logic.

Uses double progression model:
1. Start at bottom of rep range
2. When all sets hit top of range, increase weight
3. Drop back to bottom with new weight

Usage:
    from atlas.health.progression import ProgressionService

    service = ProgressionService()
    rec = service.get_recommendation("goblet_squat")
    # Returns: ProgressionRecommendation with weight, basis, voice prompt
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ProgressionRecommendation:
    """Weight recommendation for an exercise."""
    exercise_id: str
    recommended_weight_kg: Optional[float]
    basis: str  # 'baseline_1rm', 'last_workout', 'derived', 'deload', 'no_baseline', 'no_weight_tracking'
    reasoning: str
    last_weight_kg: Optional[float] = None
    last_reps_avg: Optional[float] = None
    ready_to_progress: bool = False
    pain_warning: Optional[str] = None
    staleness_warning: Optional[str] = None


@dataclass
class DeloadStatus:
    """Deload trigger status."""
    should_deload: bool
    trigger: Optional[str] = None  # 'pain_spike', 'fatigue_accumulated', 'stalled_progress', 'scheduled'
    cooldown_active: bool = False
    last_deload_date: Optional[date] = None
    message: str = ""


class ProgressionService:
    """
    Progressive overload recommendation engine.

    Derives starting weights from baseline assessments and provides
    weekly progression recommendations based on workout history.
    """

    CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "progressions" / "exercise_map.json"
    DELOAD_COOLDOWN_DAYS = 14

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".atlas" / "atlas.db"
        self._config: Optional[dict] = None
        self._blueprint = None
        self._pain_service = None
        self._assessment_service = None

    @property
    def config(self) -> dict:
        """Load and cache exercise mapping config."""
        if self._config is None:
            if not self.CONFIG_PATH.exists():
                logger.warning(f"Exercise map not found: {self.CONFIG_PATH}")
                return {"exercises": {}, "deload_rules": {}}
            with open(self.CONFIG_PATH) as f:
                self._config = json.load(f)
        return self._config

    @property
    def blueprint(self):
        """Get BlueprintAPI instance."""
        if self._blueprint is None:
            from atlas.memory.blueprint import get_blueprint_api
            self._blueprint = get_blueprint_api()
        return self._blueprint

    @property
    def pain_service(self):
        """Get PainService instance."""
        if self._pain_service is None:
            from atlas.health.pain import PainService
            self._pain_service = PainService(self.db_path)
        return self._pain_service

    @property
    def assessment_service(self):
        """Get AssessmentService instance."""
        if self._assessment_service is None:
            from atlas.health.assessment import AssessmentService
            self._assessment_service = AssessmentService(self.db_path)
        return self._assessment_service

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _round_to_increment(self, weight: float, increment: float = 2.5) -> float:
        """Round weight to nearest increment (default 2.5kg)."""
        return round(weight / increment) * increment

    def _calculate_1rm_brzycki(self, weight: float, reps: int) -> float:
        """Calculate estimated 1RM using Brzycki formula."""
        if reps <= 0 or reps > 30:
            return weight
        if reps == 1:
            return weight
        return weight * (36 / (37 - reps))

    def get_starting_weight(self, exercise_id: str) -> tuple[Optional[float], str, Optional[str]]:
        """
        Calculate starting weight for an exercise.

        Priority:
        1. Direct baseline assessment
        2. Derived from related exercise
        3. Last workout history
        4. None (prompt user)

        Args:
            exercise_id: Exercise identifier

        Returns:
            (weight_kg, basis, staleness_warning) tuple
            staleness_warning is a string if baseline is >28 days old, else None
        """
        exercises = self.config.get("exercises", {})
        mapping = exercises.get(exercise_id)

        if not mapping:
            # Unknown exercise - check history
            last_perf = self.blueprint.get_last_performance(exercise_id)
            if last_perf and last_perf.weight_kg:
                return last_perf.weight_kg, "last_workout", None
            return None, "no_mapping", None

        # Check if no weight tracking needed
        if mapping.get("no_weight_tracking"):
            return None, "no_weight_tracking", None

        # 1. Check for direct baseline assessment
        if mapping.get("assessment_id"):
            baseline = self._get_baseline_value(mapping["assessment_id"])
            if baseline:
                intensity = mapping.get("intensity", 0.70)
                increment = mapping.get("increment_kg", 2.5)

                # Check staleness (>28 days old)
                staleness_warning = self._check_baseline_staleness(mapping["assessment_id"])

                # Check if baseline is already a calculated 1RM (from protocol tests with calculate: "1rm_brzycki")
                # or if it needs conversion from raw weight+reps
                if mapping.get("baseline_is_1rm", True):
                    # Baseline value IS the 1RM (default for protocol_voice.json tests)
                    one_rm = baseline["value"]
                else:
                    # Baseline is raw weight, need to calculate 1RM
                    test_reps = mapping.get("test_reps", 10)
                    one_rm = self._calculate_1rm_brzycki(baseline["value"], test_reps)

                starting = one_rm * intensity
                return self._round_to_increment(starting, increment), "baseline_1rm", staleness_warning

        # 2. Check for derived ratio
        if mapping.get("derived_from"):
            base_exercise = mapping["derived_from"]
            base_weight, base_basis, base_staleness = self.get_starting_weight(base_exercise)
            if base_weight:
                ratio = mapping.get("ratio", 1.0)
                derived = base_weight * ratio
                increment = mapping.get("increment_kg", 2.5)
                # Pass through staleness warning from base exercise
                return self._round_to_increment(derived, increment), f"derived:{base_exercise}", base_staleness

        # 3. Check workout history
        last_perf = self.blueprint.get_last_performance(exercise_id)
        if last_perf and last_perf.weight_kg:
            return last_perf.weight_kg, "last_workout", None

        # 4. RPE-based exercises
        if mapping.get("type") == "rpe_based":
            return None, "rpe_based", None

        return None, "no_baseline", None

    def _get_baseline_value(self, assessment_id: str) -> Optional[dict]:
        """Get baseline assessment value with staleness check."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT a.value, a.date FROM assessments a
                JOIN assessment_types at ON a.assessment_type_id = at.id
                WHERE at.name = ?
                ORDER BY a.date DESC LIMIT 1
            """, (assessment_id,))
            row = cursor.fetchone()
            if row:
                return {"value": row["value"], "date": row["date"]}
            return None
        finally:
            conn.close()

    def _check_baseline_staleness(self, assessment_id: str) -> Optional[str]:
        """Check if baseline is stale (>28 days old)."""
        baseline = self._get_baseline_value(assessment_id)
        if not baseline:
            return None

        baseline_date = date.fromisoformat(baseline["date"])
        days_old = (date.today() - baseline_date).days
        staleness_threshold = self.config.get("metadata", {}).get("staleness_warning_days", 28)

        if days_old > staleness_threshold:
            return f"Baseline {days_old} days old - consider retest"
        return None

    def get_recommendation(self, exercise_id: str) -> ProgressionRecommendation:
        """
        Get weight recommendation for an exercise.

        Considers:
        - Last workout performance
        - Double progression rules
        - Pain trends
        - Deload triggers

        Args:
            exercise_id: Exercise identifier

        Returns:
            ProgressionRecommendation with all context
        """
        exercises = self.config.get("exercises", {})
        mapping = exercises.get(exercise_id, {})

        # Check for no weight tracking
        if mapping.get("no_weight_tracking"):
            return ProgressionRecommendation(
                exercise_id=exercise_id,
                recommended_weight_kg=None,
                basis="no_weight_tracking",
                reasoning=f"No weight tracking for {exercise_id}",
            )

        # Check deload status first
        deload = self.check_deload()
        if deload.should_deload and not deload.cooldown_active:
            # Get last weight and reduce
            last_perf = self.blueprint.get_last_performance(exercise_id)
            if last_perf and last_perf.weight_kg:
                deload_weight = self._round_to_increment(last_perf.weight_kg * 0.70)
                return ProgressionRecommendation(
                    exercise_id=exercise_id,
                    recommended_weight_kg=deload_weight,
                    basis="deload",
                    reasoning=f"Deload: {deload.trigger}",
                    last_weight_kg=last_perf.weight_kg,
                    last_reps_avg=last_perf.avg_reps,
                )

        # Check pain trend
        pain_warning = None
        relevant_body_parts = self._get_exercise_body_parts(exercise_id)
        for body_part in relevant_body_parts:
            trend = self.pain_service.get_trend(body_part, days=7)
            if trend and trend.trending_up:
                pain_warning = f"{body_part.replace('_', ' ')} pain trending up"
                break

        # Get starting/current weight (now includes staleness check)
        starting_weight, basis, staleness_warning = self.get_starting_weight(exercise_id)

        # Get last performance
        last_perf = self.blueprint.get_last_performance(exercise_id)

        # If no history, use starting weight
        if not last_perf:
            return ProgressionRecommendation(
                exercise_id=exercise_id,
                recommended_weight_kg=starting_weight,
                basis=basis,
                reasoning=f"First session - starting from {basis}",
                staleness_warning=staleness_warning,
            )

        # Double progression check
        rep_range = mapping.get("rep_range")
        ready_to_progress = False
        recommended_weight = last_perf.weight_kg

        if rep_range and len(rep_range) == 2:
            top_of_range = rep_range[1]
            # Require ALL sets to hit top of rep range (AND not OR)
            if last_perf.all_sets_hit_target and last_perf.avg_reps >= top_of_range:
                # Ready to increase weight
                if not pain_warning:
                    increment = mapping.get("increment_kg", 2.5)
                    recommended_weight = self._round_to_increment(
                        (last_perf.weight_kg or starting_weight or 0) + increment
                    )
                    ready_to_progress = True

        # If pain warning, hold at last weight
        if pain_warning:
            recommended_weight = last_perf.weight_kg
            ready_to_progress = False

        return ProgressionRecommendation(
            exercise_id=exercise_id,
            recommended_weight_kg=recommended_weight,
            basis="progression" if ready_to_progress else "maintain",
            reasoning=self._build_reasoning(last_perf, ready_to_progress, pain_warning),
            last_weight_kg=last_perf.weight_kg,
            last_reps_avg=last_perf.avg_reps,
            ready_to_progress=ready_to_progress,
            pain_warning=pain_warning,
            staleness_warning=staleness_warning,
        )

    def _build_reasoning(
        self,
        last_perf,
        ready_to_progress: bool,
        pain_warning: Optional[str]
    ) -> str:
        """Build human-readable reasoning for recommendation."""
        if pain_warning:
            return f"Hold weight - {pain_warning}"
        if ready_to_progress:
            return f"All sets hit top of range ({last_perf.avg_reps:.0f} avg) - progress"
        if last_perf:
            return f"Continue at current weight ({last_perf.avg_reps:.0f} avg reps)"
        return "Starting weight from baseline"

    def _get_exercise_body_parts(self, exercise_id: str) -> list[str]:
        """Map exercise to relevant body parts for pain check."""
        # Simplified mapping - expand as needed
        mappings = {
            "floor_press": ["shoulder_right"],
            "landmine_press": ["shoulder_right"],
            "chest_supported_row": ["shoulder_right"],
            "band_pull_apart": ["shoulder_right"],
            "side_lying_wiper": ["shoulder_right"],
            "goblet_squat": ["lower_back", "ankle_left", "ankle_right"],
            "trap_bar_deadlift": ["lower_back"],
            "split_squat": ["ankle_left", "ankle_right"],
            "suitcase_carry": ["lower_back"],
        }
        return mappings.get(exercise_id, [])

    def check_deload(self) -> DeloadStatus:
        """
        Check if deload should be triggered.

        Priority order (first match wins):
        1. Pain spike >= 6/10
        2. Fatigue: 4+ YELLOW days in 10 days
        3. Stalled: Same weight+reps for 3 sessions
        4. Scheduled: Weeks 4 and 8

        Cooldown: No deload within 14 days of last deload.
        """
        # Check cooldown first
        last_deload = self._get_last_deload_date()
        if last_deload:
            days_since = (date.today() - last_deload).days
            if days_since < self.DELOAD_COOLDOWN_DAYS:
                return DeloadStatus(
                    should_deload=False,
                    cooldown_active=True,
                    last_deload_date=last_deload,
                    message=f"Deload cooldown: {self.DELOAD_COOLDOWN_DAYS - days_since} days remaining"
                )

        # 1. Pain spike
        max_pain = self.pain_service.get_max_recent_pain(days=1)
        if max_pain >= 6:
            return DeloadStatus(
                should_deload=True,
                trigger="pain_spike",
                message=f"Pain at {max_pain}/10 - immediate deload"
            )

        # 2. Fatigue accumulated
        yellow_days = self.blueprint.count_yellow_days(window_days=10)
        if yellow_days >= 4:
            return DeloadStatus(
                should_deload=True,
                trigger="fatigue_accumulated",
                message=f"{yellow_days} YELLOW days in 10 days - deload needed"
            )

        # 3. Stalled progress (check later - needs history analysis)
        # For now, skip this trigger

        # 4. Scheduled deload weeks
        scheduled_weeks = self.config.get("deload_rules", {}).get("scheduled_weeks", [4, 8])
        current_week = self._get_current_training_week()
        if current_week in scheduled_weeks:
            return DeloadStatus(
                should_deload=True,
                trigger="scheduled",
                message=f"Scheduled deload week {current_week}"
            )

        return DeloadStatus(should_deload=False)

    def _get_last_deload_date(self) -> Optional[date]:
        """Get date of last deload workout (if any)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT date FROM exercise_progression_log
                WHERE basis = 'deload'
                ORDER BY date DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return date.fromisoformat(row["date"])
            return None
        except sqlite3.OperationalError:
            # Table might not exist yet
            return None
        finally:
            conn.close()

    def _get_current_training_week(self) -> int:
        """Get current week number in training phase."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT start_date FROM phase_history
                WHERE status = 'active'
                ORDER BY start_date DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                start = date.fromisoformat(row["start_date"])
                return ((date.today() - start).days // 7) + 1
            return 1
        except sqlite3.OperationalError:
            return 1
        finally:
            conn.close()

    def _get_current_phase(self) -> str:
        """Get current training phase (phase_1, phase_2, etc)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                SELECT phase_id FROM phase_history
                WHERE status = 'active'
                ORDER BY start_date DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return row["phase_id"]
            return "phase_1"  # Default to phase 1 (rehab)
        except sqlite3.OperationalError:
            return "phase_1"
        finally:
            conn.close()

    def log_progression(
        self,
        exercise_id: str,
        recommended_weight: Optional[float],
        actual_weight: Optional[float],
        actual_reps_avg: float,
        basis: str,
    ) -> int:
        """Log progression data for tracking."""
        conn = self._get_conn()
        try:
            # Ensure table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exercise_progression_log (
                    id INTEGER PRIMARY KEY,
                    exercise_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    recommended_weight_kg REAL,
                    actual_weight_kg REAL,
                    recommended_reps INTEGER,
                    actual_reps_avg REAL,
                    basis TEXT,
                    one_rm_estimate REAL,
                    UNIQUE(exercise_id, date)
                )
            """)

            # Calculate 1RM estimate if we have data
            one_rm = None
            if actual_weight and actual_reps_avg > 0:
                one_rm = self._calculate_1rm_brzycki(actual_weight, int(actual_reps_avg))

            cursor = conn.execute("""
                INSERT OR REPLACE INTO exercise_progression_log
                (exercise_id, date, recommended_weight_kg, actual_weight_kg, actual_reps_avg, basis, one_rm_estimate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                exercise_id,
                date.today().isoformat(),
                recommended_weight,
                actual_weight,
                actual_reps_avg,
                basis,
                one_rm,
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def format_voice_recommendation(self, rec: ProgressionRecommendation) -> str:
        """
        Format recommendation for voice output.

        Single touchpoint - clear and actionable.
        """
        if rec.basis == "no_weight_tracking":
            return ""  # No voice prompt needed

        if rec.pain_warning:
            return f"{rec.pain_warning.capitalize()}. Hold at {int(rec.last_weight_kg or 0)} kilos. What weight?"

        if rec.ready_to_progress:
            last = int(rec.last_weight_kg or 0)
            new = int(rec.recommended_weight_kg or 0)
            return f"Last week {last} kilos for {rec.last_reps_avg:.0f} reps. Ready for {new}?"

        if rec.last_weight_kg:
            return f"Last workout {int(rec.last_weight_kg)} kilos. Same weight or different?"

        if rec.recommended_weight_kg:
            return f"Starting weight {int(rec.recommended_weight_kg)} kilos based on {rec.basis.replace('_', ' ')}. Ready?"

        return "What weight are you using?"

    def get_workout_summary(self, workout_log: list[dict]) -> str:
        """
        Generate post-workout progression summary.

        Args:
            workout_log: List of completed exercises with weights/reps

        Returns:
            Voice summary of progression status
        """
        summaries = []
        exercises = self.config.get("exercises", {})

        for entry in workout_log:
            exercise_id = entry.get("id", "").lower().replace(" ", "_")
            mapping = exercises.get(exercise_id, {})

            if mapping.get("no_weight_tracking"):
                continue

            rep_range = mapping.get("rep_range")
            if not rep_range:
                continue

            top_of_range = rep_range[1] if len(rep_range) == 2 else 12
            reps = entry.get("reps")
            weight = entry.get("weight")
            name = entry.get("name", exercise_id)

            # Parse reps if it's a list or average
            avg_reps = 0
            if isinstance(reps, list):
                avg_reps = sum(reps) / len(reps)
            elif isinstance(reps, (int, float)):
                avg_reps = reps

            if avg_reps >= top_of_range and weight:
                increment = mapping.get("increment_kg", 2.5)
                new_weight = self._round_to_increment(weight + increment)
                summaries.append(f"{name} hit {int(avg_reps)} reps - bump to {int(new_weight)} next time")
            elif weight:
                summaries.append(f"{name} at {int(avg_reps)} reps - same weight next workout")

        if not summaries:
            return "Good session."

        return ". ".join(summaries[:3]) + "."  # Limit to 3 for voice brevity
