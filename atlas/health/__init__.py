"""
ATLAS Health Module

Provides health/fitness tracking with:
- Garmin sync (HRV, sleep, heart rate)
- Traffic Light workout routing (GREEN/YELLOW/RED)
- Workout protocol management
- Supplement tracking

Usage:
    from atlas.health import HealthService

    service = HealthService()
    status = await service.morning_sync()
    print(f"{status['traffic_light']} - {status['workout']}")

CLI Usage:
    python -m atlas.health.cli daily --sleep 7.2 --hrv BALANCED
    python -m atlas.health.cli workout
    python -m atlas.health.cli supplements
"""

from atlas.health.router import TrafficLightRouter, TrafficLightStatus, TrafficLightResult
from atlas.health.workout import WorkoutService, WorkoutProtocol, WorkoutPlan
from atlas.health.supplement import SupplementService, SupplementChecklist
from atlas.health.garmin import GarminService, GarminMetrics
from atlas.health.service import HealthService, DailyStatus

__all__ = [
    # Main Service
    "HealthService",
    "DailyStatus",
    # Router
    "TrafficLightRouter",
    "TrafficLightStatus",
    "TrafficLightResult",
    # Workout
    "WorkoutService",
    "WorkoutProtocol",
    "WorkoutPlan",
    # Supplement
    "SupplementService",
    "SupplementChecklist",
    # Garmin
    "GarminService",
    "GarminMetrics",
]
