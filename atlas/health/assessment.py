"""
ATLAS Assessment Service

Handles fitness assessments, baseline tracking, LSI calculations, and GATE evaluations.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AssessmentResult:
    """Single assessment result."""
    id: str
    name: str
    value: float
    unit: str
    target: Optional[float] = None
    minimum: Optional[float] = None
    baseline: Optional[float] = None
    change_from_baseline: Optional[float] = None
    meets_minimum: bool = True
    meets_target: bool = False
    lower_is_better: bool = False


@dataclass
class LSIResult:
    """Limb Symmetry Index result."""
    test_name: str
    left_value: float
    right_value: float
    lsi: float  # Weaker / Stronger * 100
    meets_threshold: bool
    threshold: float


@dataclass
class GateEvaluation:
    """GATE assessment evaluation result."""
    gate_name: str
    gate_number: int
    passed: bool
    tests_passed: list = field(default_factory=list)
    tests_failed: list = field(default_factory=list)
    lsi_results: list = field(default_factory=list)
    additional_criteria_met: list = field(default_factory=list)
    additional_criteria_unmet: list = field(default_factory=list)
    recommendation: str = ""


class AssessmentService:
    """Service for managing fitness assessments."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".atlas" / "atlas.db"
        self.config_path = Path(__file__).parent.parent.parent / "config" / "assessments" / "baseline.json"
        self._config: Optional[dict] = None
        # Auto-migrate schema on init
        self._ensure_schema()

    @property
    def config(self) -> dict:
        """Load and cache assessment config."""
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Assessment config not found: {self.config_path}")
            try:
                with open(self.config_path) as f:
                    self._config = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {self.config_path}: {e}")
        return self._config

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Ensure database schema is up to date (add protocol_run if missing)."""
        conn = self._get_conn()
        try:
            conn.execute("ALTER TABLE assessments ADD COLUMN protocol_run TEXT")
            conn.commit()
            logger.info("Added protocol_run column to assessments table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        finally:
            conn.close()

    def get_assessment_categories(self) -> list[str]:
        """Get list of assessment categories."""
        return list(self.config.get("assessments", {}).keys())

    def get_assessments_by_category(self, category: str) -> list[dict]:
        """Get all assessments in a category."""
        return self.config.get("assessments", {}).get(category, [])

    def get_assessment_by_id(self, assessment_id: str) -> Optional[dict]:
        """Find assessment definition by ID."""
        for category in self.config.get("assessments", {}).values():
            for assessment in category:
                if assessment.get("id") == assessment_id:
                    return assessment
        return None

    def log_assessment(
        self,
        assessment_id: str,
        value: float,
        notes: Optional[str] = None,
        assessment_date: Optional[date] = None,
        protocol_run: Optional[str] = None,
    ) -> int:
        """Log an assessment result.

        Args:
            assessment_id: The assessment type ID (e.g., 'weight_kg', 'ankle_dorsiflexion_left')
            value: The measured value
            notes: Optional notes
            assessment_date: Date of assessment (defaults to today)
            protocol_run: Protocol identifier (e.g., 'baseline_2026_q1', 'retest_2026_q2')

        Returns:
            The database row ID of the inserted record
        """
        assessment_date = assessment_date or date.today()
        assessment_def = self.get_assessment_by_id(assessment_id)
        # Note: assessment_def may be None for protocol_voice.json tests not in baseline.json
        # We still allow logging - the type will be auto-created in the database

        # Check if this is the first (baseline) assessment of this type
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT id FROM assessments
            WHERE assessment_type_id = (
                SELECT id FROM assessment_types WHERE name = ?
            )
            """,
            (assessment_id,),
        )
        is_baseline = cursor.fetchone() is None

        # Get assessment type ID (may need to create if not in seed data)
        cursor = conn.execute(
            "SELECT id FROM assessment_types WHERE name = ?",
            (assessment_id,),
        )
        row = cursor.fetchone()

        if row:
            type_id = row["id"]
        else:
            # Create the assessment type (handles tests from protocol_voice.json not in baseline.json)
            cursor = conn.execute(
                """
                INSERT INTO assessment_types (name, category, unit, description, target_value, min_acceptable, higher_is_better)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment_id,
                    self._find_category(assessment_id),
                    assessment_def.get("unit", "") if assessment_def else "",
                    assessment_def.get("protocol", "") if assessment_def else "",
                    assessment_def.get("target") if assessment_def else None,
                    assessment_def.get("minimum") if assessment_def else None,
                    not assessment_def.get("lower_is_better", False) if assessment_def else True,
                ),
            )
            type_id = cursor.lastrowid

        # Insert the assessment result
        unit = assessment_def.get("unit", "") if assessment_def else ""
        cursor = conn.execute(
            """
            INSERT INTO assessments (assessment_type_id, date, value, unit, notes, is_baseline, phase, protocol_run)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                type_id,
                assessment_date.isoformat(),
                value,
                unit,
                notes,
                is_baseline,
                self._get_current_phase(),
                protocol_run,
            ),
        )

        conn.commit()
        result_id = cursor.lastrowid
        conn.close()

        logger.info(f"Logged assessment {assessment_id}: {value} {unit}")
        return result_id

    def _find_category(self, assessment_id: str) -> str:
        """Find which category an assessment belongs to."""
        for category, assessments in self.config.get("assessments", {}).items():
            for a in assessments:
                if a.get("id") == assessment_id:
                    return category
        return "unknown"

    def _get_current_phase(self) -> str:
        """Get current training phase."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT tp.name FROM phase_history ph
            JOIN training_phases tp ON ph.phase_id = tp.id
            WHERE ph.status = 'active'
            ORDER BY ph.start_date DESC LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()
        return row["name"] if row else "phase_1"

    def get_baseline(self, assessment_id: str) -> Optional[float]:
        """Get baseline value for an assessment."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT a.value FROM assessments a
            JOIN assessment_types at ON a.assessment_type_id = at.id
            WHERE at.name = ? AND a.is_baseline = 1
            """,
            (assessment_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else None

    def get_latest(self, assessment_id: str) -> Optional[dict]:
        """Get most recent assessment result."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT a.* FROM assessments a
            JOIN assessment_types at ON a.assessment_type_id = at.id
            WHERE at.name = ?
            ORDER BY a.date DESC LIMIT 1
            """,
            (assessment_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_history(self, assessment_id: str, limit: int = 10) -> list[dict]:
        """Get assessment history."""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            SELECT a.* FROM assessments a
            JOIN assessment_types at ON a.assessment_type_id = at.id
            WHERE at.name = ?
            ORDER BY a.date DESC LIMIT ?
            """,
            (assessment_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_result(self, assessment_id: str) -> Optional[AssessmentResult]:
        """Get assessment result with comparison to baseline and targets."""
        definition = self.get_assessment_by_id(assessment_id)
        if not definition:
            return None

        latest = self.get_latest(assessment_id)
        if not latest:
            return None

        baseline = self.get_baseline(assessment_id)
        target = definition.get("target")
        minimum = definition.get("minimum")
        lower_is_better = definition.get("lower_is_better", False)

        value = latest["value"]
        change = value - baseline if baseline else None

        # Determine if meets thresholds
        if lower_is_better:
            meets_min = value <= minimum if minimum else True
            meets_target = value <= target if target else False
        else:
            meets_min = value >= minimum if minimum else True
            meets_target = value >= target if target else False

        return AssessmentResult(
            id=assessment_id,
            name=definition.get("name", assessment_id),
            value=value,
            unit=definition.get("unit", ""),
            target=target,
            minimum=minimum,
            baseline=baseline,
            change_from_baseline=change,
            meets_minimum=meets_min,
            meets_target=meets_target,
            lower_is_better=lower_is_better,
        )

    def calculate_lsi(self, left_id: str, right_id: str, threshold: float = 90.0) -> Optional[LSIResult]:
        """Calculate Limb Symmetry Index between left and right sides."""
        left_result = self.get_latest(left_id)
        right_result = self.get_latest(right_id)

        if not left_result or not right_result:
            return None

        left_val = left_result["value"]
        right_val = right_result["value"]

        # LSI = (weaker / stronger) * 100
        # LSI requires positive values - handle zero and negative
        if left_val <= 0 or right_val <= 0:
            logger.warning(f"Invalid values for LSI calculation: left={left_val}, right={right_val}")
            return None

        weaker = min(left_val, right_val)
        stronger = max(left_val, right_val)
        lsi = (weaker / stronger) * 100

        left_def = self.get_assessment_by_id(left_id)
        test_name = left_def.get("name", left_id).replace(" - Left", "")

        return LSIResult(
            test_name=test_name,
            left_value=left_val,
            right_value=right_val,
            lsi=lsi,
            meets_threshold=lsi >= threshold,
            threshold=threshold,
        )

    def check_gate(self, gate_number: int) -> GateEvaluation:
        """Evaluate readiness for a specific GATE."""
        gate_config = self.config.get("gate_assessment_groups", {}).get(f"gate_{gate_number}")
        if not gate_config:
            raise ValueError(f"Unknown GATE: {gate_number}")

        gate_name = gate_config.get("name", f"GATE {gate_number}")
        tests = gate_config.get("tests", [])
        lsi_requirement = gate_config.get("lsi_requirement")
        additional_criteria = gate_config.get("additional_criteria", [])

        tests_passed = []
        tests_failed = []
        lsi_results = []

        # Group tests into pairs for LSI calculation
        test_pairs = {}
        for test_id in tests:
            base_name = test_id.replace("_left", "").replace("_right", "")
            if base_name not in test_pairs:
                test_pairs[base_name] = {}
            if "_left" in test_id:
                test_pairs[base_name]["left"] = test_id
            elif "_right" in test_id:
                test_pairs[base_name]["right"] = test_id
            else:
                # Non-paired test
                test_pairs[base_name]["single"] = test_id

        # Evaluate each test
        for base_name, pair in test_pairs.items():
            if "left" in pair and "right" in pair:
                # Calculate LSI
                threshold = lsi_requirement or 90.0
                lsi = self.calculate_lsi(pair["left"], pair["right"], threshold)
                if lsi:
                    lsi_results.append(lsi)
                    if lsi.meets_threshold:
                        tests_passed.append(f"{lsi.test_name} (LSI: {lsi.lsi:.1f}%)")
                    else:
                        tests_failed.append(f"{lsi.test_name} (LSI: {lsi.lsi:.1f}% < {threshold}%)")
                else:
                    tests_failed.append(f"{base_name}: No data")
            elif "single" in pair:
                # Single test (like t_test)
                result = self.get_result(pair["single"])
                if result and result.meets_minimum:
                    tests_passed.append(f"{result.name}: {result.value} {result.unit}")
                elif result:
                    tests_failed.append(f"{result.name}: {result.value} {result.unit} (below minimum)")
                else:
                    tests_failed.append(f"{base_name}: No data")

        # All additional criteria start as unmet (manual verification needed)
        criteria_met = []
        criteria_unmet = additional_criteria.copy()

        # Determine overall pass/fail
        all_tests_pass = len(tests_failed) == 0 and len(tests_passed) > 0
        passed = all_tests_pass  # Note: additional criteria require manual verification

        if passed:
            recommendation = f"All measured tests passed. Verify additional criteria manually before proceeding."
        else:
            recommendation = f"Not ready for {gate_name}. Address failed tests and retest in 1-2 weeks."

        return GateEvaluation(
            gate_name=gate_name,
            gate_number=gate_number,
            passed=passed,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            lsi_results=lsi_results,
            additional_criteria_met=criteria_met,
            additional_criteria_unmet=criteria_unmet,
            recommendation=recommendation,
        )

    def get_progress_summary(self, category: Optional[str] = None) -> dict:
        """Get summary of all assessments with progress from baseline."""
        summary = {}
        categories = [category] if category else self.get_assessment_categories()

        for cat in categories:
            summary[cat] = []
            for assessment in self.get_assessments_by_category(cat):
                result = self.get_result(assessment["id"])
                if result:
                    summary[cat].append({
                        "id": result.id,
                        "name": result.name,
                        "value": result.value,
                        "unit": result.unit,
                        "baseline": result.baseline,
                        "change": result.change_from_baseline,
                        "target": result.target,
                        "meets_target": result.meets_target,
                        "meets_minimum": result.meets_minimum,
                    })

        return summary

    def get_tests_needing_retest(self, weeks: int = 4) -> list[dict]:
        """Get assessments that are due for retesting."""
        cutoff = date.today() - timedelta(weeks=weeks)
        needing_retest = []

        for category, assessments in self.config.get("assessments", {}).items():
            for assessment in assessments:
                latest = self.get_latest(assessment["id"])
                if latest:
                    try:
                        last_date = datetime.fromisoformat(latest["date"]).date()
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date format for {assessment['id']}: {latest['date']}")
                        continue
                    if last_date < cutoff:
                        needing_retest.append({
                            "id": assessment["id"],
                            "name": assessment["name"],
                            "last_tested": last_date,
                            "days_ago": (date.today() - last_date).days,
                        })

        return needing_retest

    def list_all_tests(self, phase: Optional[str] = None) -> list[dict]:
        """List all available assessments, optionally filtered by phase availability."""
        tests = []
        current_phase = phase or self._get_current_phase()

        for category, assessments in self.config.get("assessments", {}).items():
            for assessment in assessments:
                # Check phase availability
                phase_available = assessment.get("phase_available")
                if phase_available and current_phase < phase_available:
                    continue

                tests.append({
                    "id": assessment["id"],
                    "name": assessment["name"],
                    "category": category,
                    "unit": assessment.get("unit", ""),
                    "target": assessment.get("target"),
                    "minimum": assessment.get("minimum"),
                    "protocol": assessment.get("protocol", ""),
                })

        return tests
