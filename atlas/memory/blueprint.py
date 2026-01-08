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
                    weight_kg, body_fat_pct, energy_level, mood,
                    stress_level, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.date.isoformat(),
                metrics.sleep_hours, metrics.sleep_score,
                metrics.deep_sleep_minutes, metrics.rem_sleep_minutes,
                metrics.resting_hr, metrics.hrv_avg, metrics.hrv_morning,
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
