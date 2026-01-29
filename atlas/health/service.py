"""
Health Service

Unified orchestration layer for health tracking.

Combines:
- GarminService: Sync wearable data
- TrafficLightRouter: Determine workout intensity
- WorkoutService: Manage workout protocols
- SupplementService: Track daily supplements
- BlueprintAPI: Store health metrics

Usage:
    from atlas.health.service import HealthService

    service = HealthService()

    # Morning routine
    status = await service.morning_sync()
    print(f"{status['traffic_light']} - {status['workout']}")

    # Get daily status
    status = service.get_daily_status()
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from atlas.memory.blueprint import get_blueprint_api, DailyMetrics
from atlas.health.router import TrafficLightRouter, TrafficLightStatus, TrafficLightResult
from atlas.health.workout import WorkoutService, WorkoutPlan
from atlas.health.supplement import SupplementService, SupplementChecklist
from atlas.health.garmin import GarminService, GarminMetrics

logger = logging.getLogger(__name__)


@dataclass
class DailyStatus:
    """Complete daily health status."""
    date: date
    traffic_light: TrafficLightResult
    workout_plan: Optional[WorkoutPlan]
    supplements: SupplementChecklist
    metrics: Optional[DailyMetrics]
    garmin_synced: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date.isoformat(),
            "traffic_light": self.traffic_light.to_dict(),
            "workout": {
                "name": self.workout_plan.protocol.name if self.workout_plan else None,
                "type": self.workout_plan.protocol.type if self.workout_plan else None,
                "is_red_override": self.workout_plan.is_red_day_override if self.workout_plan else False,
            },
            "supplements": {
                "taken": self.supplements.taken_count,
                "total": self.supplements.total,
                "completion_pct": self.supplements.completion_pct,
            },
            "garmin_synced": self.garmin_synced,
        }


class HealthService:
    """
    Unified health service orchestrating all health components.

    This is the main entry point for health operations,
    coordinating Garmin, workouts, supplements, and metrics.
    """

    def __init__(self, rhr_baseline: int = 52):
        """
        Initialize health service.

        Args:
            rhr_baseline: Resting heart rate baseline for Traffic Light
        """
        self.garmin = GarminService()
        self.workout = WorkoutService()
        self.supplement = SupplementService()
        self.router = TrafficLightRouter(rhr_baseline=rhr_baseline)
        self.blueprint = get_blueprint_api()

    async def morning_sync(
        self,
        manual_sleep: Optional[float] = None,
        manual_hrv: Optional[str] = None,
        manual_rhr: Optional[int] = None,
    ) -> dict:
        """
        Morning sync routine.

        1. Sync Garmin data (if configured)
        2. Store in daily_metrics
        3. Evaluate Traffic Light
        4. Get today's workout
        5. Return summary

        Args:
            manual_sleep: Manual sleep hours (if no Garmin)
            manual_hrv: Manual HRV status (if no Garmin)
            manual_rhr: Manual resting HR (if no Garmin)

        Returns:
            Summary dict with traffic_light, workout, and status
        """
        today = date.today()
        garmin_metrics: Optional[GarminMetrics] = None
        garmin_synced = False

        # Try Garmin sync
        if self.garmin.is_configured() and self.garmin.has_valid_token():
            try:
                garmin_metrics = await self.garmin.sync_today()
                if garmin_metrics:
                    garmin_synced = True
                    logger.info("Synced Garmin data successfully")
            except Exception as e:
                logger.error(f"Garmin sync failed: {e}")

        # Use Garmin data or manual input
        if garmin_metrics:
            sleep_hours = garmin_metrics.sleep_hours
            hrv_status = garmin_metrics.hrv_status
            resting_hr = garmin_metrics.resting_hr

            # Store in database
            self.blueprint.log_daily_metrics(DailyMetrics(
                date=today,
                sleep_hours=sleep_hours,
                sleep_score=garmin_metrics.sleep_score,
                deep_sleep_minutes=garmin_metrics.deep_sleep_minutes,
                rem_sleep_minutes=garmin_metrics.rem_sleep_minutes,
                resting_hr=resting_hr,
                hrv_avg=garmin_metrics.hrv_avg,
                hrv_morning=garmin_metrics.hrv_morning,
            ))
        else:
            sleep_hours = manual_sleep
            hrv_status = manual_hrv
            resting_hr = manual_rhr

            # Store manual input
            if any([sleep_hours, hrv_status, resting_hr]):
                self.blueprint.log_daily_metrics(DailyMetrics(
                    date=today,
                    sleep_hours=sleep_hours,
                    resting_hr=resting_hr,
                ))

        # Evaluate Traffic Light
        traffic_light = self.router.evaluate(
            sleep_hours=sleep_hours,
            hrv_status=hrv_status,
            resting_hr=resting_hr,
        )

        # Get today's workout
        workout_plan = self.workout.get_todays_workout(traffic_light=traffic_light.status)

        return {
            "date": today.isoformat(),
            "garmin_synced": garmin_synced,
            "traffic_light": traffic_light.status.value,
            "traffic_light_reason": traffic_light.reason,
            "recommendation": traffic_light.recommendation,
            "workout": workout_plan.protocol.name if workout_plan else None,
            "workout_type": workout_plan.protocol.type if workout_plan else None,
            "is_red_override": workout_plan.is_red_day_override if workout_plan else False,
            "metrics": {
                "sleep_hours": sleep_hours,
                "hrv_status": hrv_status,
                "hrv_avg": garmin_metrics.hrv_avg if garmin_metrics else None,
                "resting_hr": resting_hr,
                "body_battery": garmin_metrics.body_battery if garmin_metrics else None,
                "stress_avg": garmin_metrics.stress_avg if garmin_metrics else None,
            },
        }

    def get_daily_status(self, target_date: Optional[date] = None) -> DailyStatus:
        """
        Get complete daily health status.

        Args:
            target_date: Date to get status for (default: today)

        Returns:
            DailyStatus with all health information
        """
        if target_date is None:
            target_date = date.today()

        # Get metrics from database
        metrics_list = self.blueprint.get_daily_metrics(days=1, start_date=target_date)
        metrics = metrics_list[0] if metrics_list else None

        # Determine traffic light from stored metrics
        traffic_light = self.router.evaluate(
            sleep_hours=metrics.sleep_hours if metrics else None,
            hrv_status=metrics.hrv_status if metrics else None,
            resting_hr=metrics.resting_hr if metrics else None,
            body_battery=metrics.body_battery if metrics else None,
        )

        # Get workout plan
        workout_plan = self.workout.get_todays_workout(
            traffic_light=traffic_light.status,
            target_date=target_date,
        )

        # Get supplement status
        supplements = self.supplement.get_today(target_date=target_date)

        return DailyStatus(
            date=target_date,
            traffic_light=traffic_light,
            workout_plan=workout_plan,
            supplements=supplements,
            metrics=metrics,
            garmin_synced=self.garmin.has_valid_token(),
        )

    def get_weekly_summary(self) -> dict:
        """
        Get weekly health summary for digest.

        Returns:
            Summary dict with workouts, supplements, trends
        """
        workout_stats = self.workout.get_weekly_stats()
        supp_stats = self.supplement.get_weekly_compliance()

        # Get metrics for trend analysis
        metrics = self.blueprint.get_daily_metrics(days=7)

        avg_sleep = None
        if metrics:
            sleep_values = [m.sleep_hours for m in metrics if m.sleep_hours]
            if sleep_values:
                avg_sleep = sum(sleep_values) / len(sleep_values)

        return {
            "workouts": {
                "completed": workout_stats["completed"],
                "expected": workout_stats["expected"],
                "completion_pct": workout_stats["completion_pct"],
                "total_minutes": workout_stats["total_duration_minutes"],
            },
            "supplements": {
                "compliance_pct": supp_stats["compliance_pct"],
                "by_supplement": supp_stats["by_supplement"],
            },
            "trends": {
                "avg_sleep_hours": avg_sleep,
                "days_tracked": len(metrics),
            },
        }

    def log_workout_quick(
        self,
        duration_minutes: int,
        notes: Optional[str] = None,
    ) -> int:
        """
        Quick workout log (auto-detects type from schedule).

        Args:
            duration_minutes: Workout duration
            notes: Optional notes

        Returns:
            Workout ID
        """
        return self.workout.log_completed(
            duration_minutes=duration_minutes,
            notes=notes,
        )

    def check_supplement(self, name: str) -> bool:
        """
        Quick supplement check-off.

        Args:
            name: Supplement name

        Returns:
            True if found and marked
        """
        return self.supplement.mark_taken(name)


# Convenience functions for MCP/voice integration
async def health_sync(
    sleep: Optional[float] = None,
    hrv: Optional[str] = None,
    rhr: Optional[int] = None,
) -> dict:
    """Quick health sync for MCP/voice."""
    service = HealthService()
    return await service.morning_sync(
        manual_sleep=sleep,
        manual_hrv=hrv,
        manual_rhr=rhr,
    )


def get_todays_workout() -> Optional[str]:
    """Get today's workout name for MCP/voice."""
    service = HealthService()
    plan = service.workout.get_todays_workout()
    if plan:
        return plan.to_display()
    return None
