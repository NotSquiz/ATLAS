"""
ATLAS Blueprint API

CRUD operations for health/fitness tracking tables:
- daily_metrics: Daily biomarkers (sleep, HRV, weight, mood)
- supplements: Supplement catalog and dosing log
- workouts: Workout sessions and exercises
- lab_results: Blood work markers
- injuries: Injury tracking with contraindications

Usage:
    from atlas.memory.blueprint import get_blueprint_api

    api = get_blueprint_api()

    # Log daily metrics
    api.log_daily_metrics(DailyMetrics(
        date=date.today(),
        sleep_hours=7.5,
        hrv_morning=45,
        mood=7
    ))

    # Get recent metrics
    metrics = api.get_daily_metrics(days=7)
"""

import json
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional

from .store import MemoryStore


@dataclass
class DailyMetrics:
    """Daily biomarker measurements."""
    date: date
    sleep_hours: Optional[float] = None
    sleep_score: Optional[int] = None
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    resting_hr: Optional[int] = None
    hrv_avg: Optional[int] = None
    hrv_morning: Optional[int] = None
    hrv_status: Optional[str] = None  # "BALANCED", "UNBALANCED", "LOW"
    body_battery: Optional[int] = None  # 0-100 from Garmin
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    energy_level: Optional[int] = None  # 1-10
    mood: Optional[int] = None  # 1-10
    stress_level: Optional[int] = None  # 1-10
    notes: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Supplement:
    """Supplement catalog entry."""
    name: str
    brand: Optional[str] = None
    dosage: Optional[str] = None
    timing: Optional[str] = None  # 'morning', 'with_meal', 'before_bed'
    purpose: Optional[str] = None
    active: bool = True
    id: Optional[int] = None


@dataclass
class SupplementLog:
    """Supplement dose log entry."""
    supplement_id: int
    date: date
    taken: bool = True
    time: Optional[time] = None
    notes: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Workout:
    """Workout session."""
    date: date
    type: Optional[str] = None  # 'strength', 'cardio', 'mobility', 'rehab'
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    energy_before: Optional[int] = None  # 1-10
    energy_after: Optional[int] = None  # 1-10
    id: Optional[int] = None


@dataclass
class WorkoutExercise:
    """Exercise within a workout."""
    workout_id: int
    exercise_id: str
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[str] = None  # '8,8,6' for multiple sets
    weight_kg: Optional[float] = None
    duration_seconds: Optional[int] = None
    distance_meters: Optional[float] = None
    notes: Optional[str] = None
    order_index: Optional[int] = None
    id: Optional[int] = None
    # New fields for Phase 1 exercise support
    per_side: bool = False  # If true, exercise was performed per side
    hold_seconds: Optional[int] = None  # For isometric holds
    side: Optional[str] = None  # 'left', 'right', 'both' for unilateral tracking
    distance_steps: Optional[int] = None  # For step-based exercises
    per_direction: bool = False  # If true, exercise was performed each direction


@dataclass
class WorkoutExerciseSet:
    """Individual set within a workout exercise."""
    workout_exercise_id: int
    set_number: int
    reps_actual: int
    weight_kg: Optional[float] = None
    reps_target: Optional[int] = None
    rpe: Optional[int] = None  # 1-10 rating of perceived exertion
    tempo_achieved: bool = True
    notes: Optional[str] = None
    id: Optional[int] = None


@dataclass
class ExercisePerformance:
    """Summary of last workout performance for an exercise."""
    exercise_id: str
    date: date
    weight_kg: Optional[float]
    sets_completed: int
    reps_per_set: list[int]  # Actual reps per set
    avg_reps: float
    all_sets_hit_target: bool
    workout_id: int


@dataclass
class LabResult:
    """Blood work / lab result."""
    test_date: date
    marker: str  # 'vitamin_d', 'testosterone', 'hba1c'
    value: float
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    notes: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Injury:
    """Injury tracking."""
    body_part: str  # 'shoulder', 'lower_back'
    side: Optional[str] = None  # 'left', 'right', 'both'
    description: Optional[str] = None
    onset_date: Optional[date] = None
    severity: Optional[int] = None  # 1-5
    status: str = "active"  # 'active', 'recovering', 'resolved'
    contraindicated_exercises: list[str] = field(default_factory=list)
    rehab_notes: Optional[str] = None
    id: Optional[int] = None


class BlueprintAPI:
    """
    Health/fitness data API built on MemoryStore.

    Usage:
        api = BlueprintAPI()

        # Log daily metrics
        api.log_daily_metrics(DailyMetrics(
            date=date.today(),
            sleep_hours=7.5,
            hrv_morning=45,
            mood=7
        ))

        # Get recent metrics
        metrics = api.get_daily_metrics(days=7)
    """

    def __init__(self, store: Optional[MemoryStore] = None):
        """
        Initialize Blueprint API.

        Args:
            store: MemoryStore instance (creates default if None)
        """
        self._store = store

    @property
    def store(self) -> MemoryStore:
        """Get or create memory store."""
        if self._store is None:
            self._store = MemoryStore()
            self._store.init_db()
        return self._store

    # ==================== DAILY METRICS ====================

    def log_daily_metrics(self, metrics: DailyMetrics) -> int:
        """
        Log or update daily metrics.

        If metrics for the date exist, updates them.
        Otherwise, creates new entry.

        Returns:
            Row ID of inserted/updated record
        """
        conn = self.store.conn

        # Check if entry exists for date
        existing = conn.execute(
            "SELECT id FROM daily_metrics WHERE date = ?",
            (metrics.date.isoformat(),)
        ).fetchone()

        if existing:
            # Update existing
            conn.execute("""
                UPDATE daily_metrics SET
                    sleep_hours = COALESCE(?, sleep_hours),
                    sleep_score = COALESCE(?, sleep_score),
                    deep_sleep_minutes = COALESCE(?, deep_sleep_minutes),
                    rem_sleep_minutes = COALESCE(?, rem_sleep_minutes),
                    resting_hr = COALESCE(?, resting_hr),
                    hrv_avg = COALESCE(?, hrv_avg),
                    hrv_morning = COALESCE(?, hrv_morning),
                    hrv_status = COALESCE(?, hrv_status),
                    body_battery = COALESCE(?, body_battery),
                    weight_kg = COALESCE(?, weight_kg),
                    body_fat_pct = COALESCE(?, body_fat_pct),
                    energy_level = COALESCE(?, energy_level),
                    mood = COALESCE(?, mood),
                    stress_level = COALESCE(?, stress_level),
                    notes = COALESCE(?, notes),
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = ?
            """, (
                metrics.sleep_hours, metrics.sleep_score,
                metrics.deep_sleep_minutes, metrics.rem_sleep_minutes,
                metrics.resting_hr, metrics.hrv_avg, metrics.hrv_morning,
                metrics.hrv_status, metrics.body_battery,
                metrics.weight_kg, metrics.body_fat_pct,
                metrics.energy_level, metrics.mood, metrics.stress_level,
                metrics.notes, metrics.date.isoformat()
            ))
            conn.commit()
            return existing["id"]
        else:
            # Insert new
            cursor = conn.execute("""
                INSERT INTO daily_metrics (
                    date, sleep_hours, sleep_score, deep_sleep_minutes,
                    rem_sleep_minutes, resting_hr, hrv_avg, hrv_morning,
                    hrv_status, body_battery,
                    weight_kg, body_fat_pct, energy_level, mood,
                    stress_level, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.date.isoformat(),
                metrics.sleep_hours, metrics.sleep_score,
                metrics.deep_sleep_minutes, metrics.rem_sleep_minutes,
                metrics.resting_hr, metrics.hrv_avg, metrics.hrv_morning,
                metrics.hrv_status, metrics.body_battery,
                metrics.weight_kg, metrics.body_fat_pct,
                metrics.energy_level, metrics.mood, metrics.stress_level,
                metrics.notes
            ))
            conn.commit()
            return cursor.lastrowid

    def get_daily_metrics(
        self,
        days: int = 7,
        start_date: Optional[date] = None
    ) -> list[DailyMetrics]:
        """
        Get recent daily metrics.

        Args:
            days: Number of days to retrieve
            start_date: Start from this date (default: today)

        Returns:
            List of DailyMetrics, newest first
        """
        if start_date is None:
            start_date = date.today()

        cursor = self.store.conn.execute("""
            SELECT * FROM daily_metrics
            WHERE date <= ?
            ORDER BY date DESC
            LIMIT ?
        """, (start_date.isoformat(), days))

        results = []
        for row in cursor.fetchall():
            results.append(DailyMetrics(
                id=row["id"],
                date=date.fromisoformat(row["date"]),
                sleep_hours=row["sleep_hours"],
                sleep_score=row["sleep_score"],
                deep_sleep_minutes=row["deep_sleep_minutes"],
                rem_sleep_minutes=row["rem_sleep_minutes"],
                resting_hr=row["resting_hr"],
                hrv_avg=row["hrv_avg"],
                hrv_morning=row["hrv_morning"],
                hrv_status=row["hrv_status"] if "hrv_status" in row.keys() else None,
                body_battery=row["body_battery"] if "body_battery" in row.keys() else None,
                weight_kg=row["weight_kg"],
                body_fat_pct=row["body_fat_pct"],
                energy_level=row["energy_level"],
                mood=row["mood"],
                stress_level=row["stress_level"],
                notes=row["notes"]
            ))
        return results

    # ==================== SUPPLEMENTS ====================

    def add_supplement(self, supplement: Supplement) -> int:
        """Add a supplement to the catalog."""
        cursor = self.store.conn.execute("""
            INSERT INTO supplements (name, brand, dosage, timing, purpose, active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            supplement.name, supplement.brand, supplement.dosage,
            supplement.timing, supplement.purpose, supplement.active
        ))
        self.store.conn.commit()
        return cursor.lastrowid

    def get_supplements(self, active_only: bool = True) -> list[Supplement]:
        """Get all supplements in catalog."""
        query = "SELECT * FROM supplements"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY name"

        cursor = self.store.conn.execute(query)
        return [
            Supplement(
                id=row["id"],
                name=row["name"],
                brand=row["brand"],
                dosage=row["dosage"],
                timing=row["timing"],
                purpose=row["purpose"],
                active=bool(row["active"])
            )
            for row in cursor.fetchall()
        ]

    def log_supplement_dose(self, log: SupplementLog) -> int:
        """Log a supplement dose."""
        cursor = self.store.conn.execute("""
            INSERT INTO supplement_log (supplement_id, date, time, taken, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (
            log.supplement_id,
            log.date.isoformat(),
            log.time.isoformat() if log.time else None,
            log.taken,
            log.notes
        ))
        self.store.conn.commit()
        return cursor.lastrowid

    def get_supplement_log(
        self,
        days: int = 7,
        supplement_id: Optional[int] = None
    ) -> list[SupplementLog]:
        """Get recent supplement log entries."""
        query = """
            SELECT * FROM supplement_log
            WHERE date >= date('now', ?)
        """
        params: list = [f"-{days} days"]

        if supplement_id:
            query += " AND supplement_id = ?"
            params.append(supplement_id)

        query += " ORDER BY date DESC, time DESC"

        cursor = self.store.conn.execute(query, params)
        return [
            SupplementLog(
                id=row["id"],
                supplement_id=row["supplement_id"],
                date=date.fromisoformat(row["date"]),
                time=time.fromisoformat(row["time"]) if row["time"] else None,
                taken=bool(row["taken"]),
                notes=row["notes"]
            )
            for row in cursor.fetchall()
        ]

    # ==================== WORKOUTS ====================

    def log_workout(self, workout: Workout) -> int:
        """Log a workout session."""
        cursor = self.store.conn.execute("""
            INSERT INTO workouts (date, type, duration_minutes, notes, energy_before, energy_after)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            workout.date.isoformat(),
            workout.type,
            workout.duration_minutes,
            workout.notes,
            workout.energy_before,
            workout.energy_after
        ))
        self.store.conn.commit()
        return cursor.lastrowid

    def add_workout_exercise(self, exercise: WorkoutExercise) -> int:
        """Add an exercise to a workout."""
        cursor = self.store.conn.execute("""
            INSERT INTO workout_exercises (
                workout_id, exercise_id, exercise_name, sets, reps,
                weight_kg, duration_seconds, distance_meters, notes, order_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exercise.workout_id,
            exercise.exercise_id,
            exercise.exercise_name,
            exercise.sets,
            exercise.reps,
            exercise.weight_kg,
            exercise.duration_seconds,
            exercise.distance_meters,
            exercise.notes,
            exercise.order_index
        ))
        self.store.conn.commit()
        return cursor.lastrowid

    def get_workouts(self, days: int = 30) -> list[Workout]:
        """Get recent workouts."""
        cursor = self.store.conn.execute("""
            SELECT * FROM workouts
            WHERE date >= date('now', ?)
            ORDER BY date DESC
        """, (f"-{days} days",))

        return [
            Workout(
                id=row["id"],
                date=date.fromisoformat(row["date"]),
                type=row["type"],
                duration_minutes=row["duration_minutes"],
                notes=row["notes"],
                energy_before=row["energy_before"],
                energy_after=row["energy_after"]
            )
            for row in cursor.fetchall()
        ]

    def get_workout_exercises(self, workout_id: int) -> list[WorkoutExercise]:
        """Get exercises for a workout."""
        cursor = self.store.conn.execute("""
            SELECT * FROM workout_exercises
            WHERE workout_id = ?
            ORDER BY order_index, id
        """, (workout_id,))

        return [
            WorkoutExercise(
                id=row["id"],
                workout_id=row["workout_id"],
                exercise_id=row["exercise_id"],
                exercise_name=row["exercise_name"],
                sets=row["sets"],
                reps=row["reps"],
                weight_kg=row["weight_kg"],
                duration_seconds=row["duration_seconds"],
                distance_meters=row["distance_meters"],
                notes=row["notes"],
                order_index=row["order_index"]
            )
            for row in cursor.fetchall()
        ]

    # ==================== WORKOUT EXERCISE SETS ====================

    def add_workout_exercise_set(self, exercise_set: WorkoutExerciseSet) -> int:
        """Add an individual set record to a workout exercise."""
        cursor = self.store.conn.execute("""
            INSERT INTO workout_exercise_sets (
                workout_exercise_id, set_number, reps_target, reps_actual,
                weight_kg, rpe, tempo_achieved, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exercise_set.workout_exercise_id,
            exercise_set.set_number,
            exercise_set.reps_target,
            exercise_set.reps_actual,
            exercise_set.weight_kg,
            exercise_set.rpe,
            exercise_set.tempo_achieved,
            exercise_set.notes
        ))
        self.store.conn.commit()
        return cursor.lastrowid

    def get_workout_exercise_sets(self, workout_exercise_id: int) -> list[WorkoutExerciseSet]:
        """Get all sets for a workout exercise."""
        cursor = self.store.conn.execute("""
            SELECT * FROM workout_exercise_sets
            WHERE workout_exercise_id = ?
            ORDER BY set_number
        """, (workout_exercise_id,))

        return [
            WorkoutExerciseSet(
                id=row["id"],
                workout_exercise_id=row["workout_exercise_id"],
                set_number=row["set_number"],
                reps_target=row["reps_target"],
                reps_actual=row["reps_actual"],
                weight_kg=row["weight_kg"],
                rpe=row["rpe"],
                tempo_achieved=bool(row["tempo_achieved"]),
                notes=row["notes"]
            )
            for row in cursor.fetchall()
        ]

    def get_last_performance(self, exercise_id: str, days: int = 30) -> Optional[ExercisePerformance]:
        """
        Get the most recent performance for an exercise.

        Looks for workout_exercise_sets data first, falls back to workout_exercises.

        Args:
            exercise_id: Exercise identifier
            days: How far back to look

        Returns:
            ExercisePerformance or None if no data
        """
        # First try to get set-level data
        cursor = self.store.conn.execute("""
            SELECT
                we.exercise_id,
                w.date,
                we.weight_kg as exercise_weight,
                we.id as workout_exercise_id,
                w.id as workout_id,
                wes.weight_kg as set_weight,
                wes.reps_actual,
                wes.reps_target,
                wes.set_number
            FROM workout_exercises we
            JOIN workouts w ON we.workout_id = w.id
            LEFT JOIN workout_exercise_sets wes ON wes.workout_exercise_id = we.id
            WHERE we.exercise_id = ?
            AND w.date >= date('now', ?)
            ORDER BY w.date DESC, wes.set_number ASC
        """, (exercise_id, f"-{days} days"))

        rows = cursor.fetchall()
        if not rows:
            return None

        # Group by workout (first row is most recent)
        workout_id = rows[0]["workout_id"]
        workout_date = date.fromisoformat(rows[0]["date"])
        exercise_weight = rows[0]["exercise_weight"]

        # Collect sets for this workout
        reps_per_set = []
        set_weight = None
        reps_target = None

        for row in rows:
            if row["workout_id"] != workout_id:
                break  # Only process most recent workout
            if row["reps_actual"] is not None:
                reps_per_set.append(row["reps_actual"])
                if row["set_weight"]:
                    set_weight = row["set_weight"]
                if row["reps_target"]:
                    reps_target = row["reps_target"]

        # If no set data, fall back to workout_exercises.reps
        if not reps_per_set:
            reps_str = rows[0].get("reps") if "reps" in rows[0].keys() else None
            if reps_str:
                # Parse reps string like "8,8,8" or "10-12"
                try:
                    reps_per_set = [int(r.strip()) for r in reps_str.split(",")]
                except ValueError:
                    reps_per_set = []

        if not reps_per_set:
            return None

        weight = set_weight or exercise_weight
        avg_reps = sum(reps_per_set) / len(reps_per_set)

        # Check if all sets hit target (for double progression)
        all_hit_target = False
        if reps_target:
            all_hit_target = all(r >= reps_target for r in reps_per_set)

        return ExercisePerformance(
            exercise_id=exercise_id,
            date=workout_date,
            weight_kg=weight,
            sets_completed=len(reps_per_set),
            reps_per_set=reps_per_set,
            avg_reps=avg_reps,
            all_sets_hit_target=all_hit_target,
            workout_id=workout_id,
        )

    def get_exercise_history(
        self,
        exercise_id: str,
        limit: int = 10
    ) -> list[ExercisePerformance]:
        """Get exercise performance history for progression analysis."""
        cursor = self.store.conn.execute("""
            SELECT DISTINCT w.id as workout_id, w.date
            FROM workout_exercises we
            JOIN workouts w ON we.workout_id = w.id
            WHERE we.exercise_id = ?
            ORDER BY w.date DESC
            LIMIT ?
        """, (exercise_id, limit))

        workouts = cursor.fetchall()
        history = []

        for workout_row in workouts:
            perf = self.get_last_performance(exercise_id, days=365)
            if perf and perf.workout_id == workout_row["workout_id"]:
                history.append(perf)
            # Otherwise, need to query specifically for this workout
            else:
                cursor2 = self.store.conn.execute("""
                    SELECT
                        we.exercise_id,
                        w.date,
                        we.weight_kg as exercise_weight,
                        we.id as workout_exercise_id,
                        w.id as workout_id,
                        wes.weight_kg as set_weight,
                        wes.reps_actual,
                        wes.reps_target,
                        wes.set_number
                    FROM workout_exercises we
                    JOIN workouts w ON we.workout_id = w.id
                    LEFT JOIN workout_exercise_sets wes ON wes.workout_exercise_id = we.id
                    WHERE we.exercise_id = ? AND w.id = ?
                    ORDER BY wes.set_number ASC
                """, (exercise_id, workout_row["workout_id"]))

                rows = cursor2.fetchall()
                if rows:
                    workout_date = date.fromisoformat(rows[0]["date"])
                    exercise_weight = rows[0]["exercise_weight"]
                    reps_per_set = []
                    set_weight = None

                    for row in rows:
                        if row["reps_actual"] is not None:
                            reps_per_set.append(row["reps_actual"])
                            if row["set_weight"]:
                                set_weight = row["set_weight"]

                    if reps_per_set:
                        history.append(ExercisePerformance(
                            exercise_id=exercise_id,
                            date=workout_date,
                            weight_kg=set_weight or exercise_weight,
                            sets_completed=len(reps_per_set),
                            reps_per_set=reps_per_set,
                            avg_reps=sum(reps_per_set) / len(reps_per_set),
                            all_sets_hit_target=False,  # Unknown without target
                            workout_id=workout_row["workout_id"],
                        ))

        return history

    def count_yellow_days(self, window_days: int = 10) -> int:
        """Count YELLOW traffic light days in recent period (for deload trigger)."""
        cursor = self.store.conn.execute("""
            SELECT COUNT(*) as count FROM daily_metrics
            WHERE date >= date('now', ?)
            AND hrv_status = 'UNBALANCED'
        """, (f"-{window_days} days",))
        row = cursor.fetchone()
        return row["count"] if row else 0

    # ==================== LAB RESULTS ====================

    def log_lab_result(self, result: LabResult) -> int:
        """Log a lab result."""
        cursor = self.store.conn.execute("""
            INSERT INTO lab_results (
                test_date, marker, value, unit,
                reference_low, reference_high, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            result.test_date.isoformat(),
            result.marker,
            result.value,
            result.unit,
            result.reference_low,
            result.reference_high,
            result.notes
        ))
        self.store.conn.commit()
        return cursor.lastrowid

    def get_lab_results(
        self,
        marker: Optional[str] = None,
        limit: int = 10
    ) -> list[LabResult]:
        """Get lab results, optionally filtered by marker."""
        query = "SELECT * FROM lab_results"
        params: list = []

        if marker:
            query += " WHERE marker = ?"
            params.append(marker)

        query += " ORDER BY test_date DESC LIMIT ?"
        params.append(limit)

        cursor = self.store.conn.execute(query, params)

        return [
            LabResult(
                id=row["id"],
                test_date=date.fromisoformat(row["test_date"]),
                marker=row["marker"],
                value=row["value"],
                unit=row["unit"],
                reference_low=row["reference_low"],
                reference_high=row["reference_high"],
                notes=row["notes"]
            )
            for row in cursor.fetchall()
        ]

    # ==================== INJURIES ====================

    def log_injury(self, injury: Injury) -> int:
        """Log an injury."""
        cursor = self.store.conn.execute("""
            INSERT INTO injuries (
                body_part, side, description, onset_date, severity,
                status, contraindicated_exercises, rehab_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            injury.body_part,
            injury.side,
            injury.description,
            injury.onset_date.isoformat() if injury.onset_date else None,
            injury.severity,
            injury.status,
            json.dumps(injury.contraindicated_exercises),
            injury.rehab_notes
        ))
        self.store.conn.commit()
        return cursor.lastrowid

    def get_injuries(self, active_only: bool = True) -> list[Injury]:
        """Get injuries, optionally filtered by status."""
        query = "SELECT * FROM injuries"
        if active_only:
            query += " WHERE status IN ('active', 'recovering')"
        query += " ORDER BY onset_date DESC"

        cursor = self.store.conn.execute(query)

        return [
            Injury(
                id=row["id"],
                body_part=row["body_part"],
                side=row["side"],
                description=row["description"],
                onset_date=date.fromisoformat(row["onset_date"]) if row["onset_date"] else None,
                severity=row["severity"],
                status=row["status"],
                contraindicated_exercises=json.loads(row["contraindicated_exercises"] or "[]"),
                rehab_notes=row["rehab_notes"]
            )
            for row in cursor.fetchall()
        ]

    def update_injury_status(self, injury_id: int, status: str) -> bool:
        """Update injury status ('active', 'recovering', 'resolved')."""
        cursor = self.store.conn.execute("""
            UPDATE injuries SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, injury_id))
        self.store.conn.commit()
        return cursor.rowcount > 0

    def get_contraindicated_exercises(self) -> list[str]:
        """Get all contraindicated exercises from active injuries."""
        cursor = self.store.conn.execute("""
            SELECT contraindicated_exercises FROM injuries
            WHERE status IN ('active', 'recovering')
        """)

        exercises = set()
        for row in cursor.fetchall():
            if row["contraindicated_exercises"]:
                exercises.update(json.loads(row["contraindicated_exercises"]))

        return sorted(exercises)


# Singleton instance
_blueprint_api: Optional[BlueprintAPI] = None


def get_blueprint_api() -> BlueprintAPI:
    """Get singleton Blueprint API instance."""
    global _blueprint_api
    if _blueprint_api is None:
        _blueprint_api = BlueprintAPI()
    return _blueprint_api
