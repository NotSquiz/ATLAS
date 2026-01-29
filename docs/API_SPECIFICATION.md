# ATLAS Command Centre - API Specification

**Version:** 1.0
**Date:** January 2026
**Status:** Planning Complete - Ready for Implementation

---

## Overview

The API provides read-only access to gamification data stored in `~/.atlas/atlas.db`. The voice pipeline handles all writes; the PWA only reads and displays.

**Base URL:** `http://localhost:8000/api`

**Authentication:** None (local-only, single user)

**Content Types:**
- REST: `application/json`
- SSE: `text/event-stream`

---

## REST Endpoints

### Skills

#### GET /api/skills

Returns all player skills with current XP and level.

**Response:**
```json
{
  "skills": [
    {
      "name": "strength",
      "display_name": "Strength",
      "level": 23,
      "current_xp": 9450,
      "xp_for_current_level": 8740,
      "xp_for_next_level": 12500,
      "xp_to_next": 3050,
      "progress_percent": 18.9,
      "icon": "strength.png",
      "updated_at": "2026-01-22T10:30:00Z"
    },
    // ... other skills
  ],
  "total_level": 147,
  "total_xp": 42350
}
```

**Caching:** NetworkFirst, 24h fallback

---

#### GET /api/skills/{skill_name}

Returns detailed info for a single skill.

**Parameters:**
- `skill_name` (path): Skill identifier (e.g., "strength", "mobility")

**Response:**
```json
{
  "name": "strength",
  "display_name": "Strength",
  "level": 23,
  "current_xp": 9450,
  "xp_for_current_level": 8740,
  "xp_for_next_level": 12500,
  "xp_to_next": 3050,
  "progress_percent": 18.9,
  "icon": "strength.png",
  "description": "Physical strength from weight training and resistance exercises.",
  "xp_sources": [
    { "source": "Strength A workout", "xp": 150 },
    { "source": "Strength B workout", "xp": 150 },
    { "source": "Strength C workout", "xp": 150 }
  ],
  "milestones": [
    { "level": 10, "name": "Apprentice", "reached": true },
    { "level": 25, "name": "Journeyman", "reached": false },
    { "level": 50, "name": "Expert", "reached": false },
    { "level": 75, "name": "Master", "reached": false },
    { "level": 99, "name": "Maxed", "reached": false }
  ],
  "recent_xp": [
    { "xp": 150, "source": "workout_strength_a", "timestamp": "2026-01-22T07:30:00Z" },
    { "xp": 150, "source": "workout_strength_a", "timestamp": "2026-01-20T07:45:00Z" }
  ],
  "updated_at": "2026-01-22T10:30:00Z"
}
```

**Error Response (404):**
```json
{
  "detail": "Skill 'invalid' not found"
}
```

---

### Quests

#### GET /api/quests

Returns all quests grouped by type.

**Query Parameters:**
- `type` (optional): Filter by type ("daily", "weekly", "monthly")
- `status` (optional): Filter by status ("active", "completed", "all")

**Response:**
```json
{
  "daily": [
    {
      "id": "morning_triple",
      "name": "Morning Triple",
      "description": "Complete morning routine, log weight, take morning supplements",
      "type": "daily",
      "progress": 2,
      "target": 3,
      "xp_reward": 300,
      "skill_rewards": {
        "consistency": 100,
        "mobility": 100,
        "nutrition": 100
      },
      "completed": false,
      "expires_at": "2026-01-22T23:59:59Z"
    },
    {
      "id": "deep_focus",
      "name": "Deep Focus",
      "description": "Log 2+ hours of focused work",
      "type": "daily",
      "progress": 0,
      "target": 2,
      "xp_reward": 200,
      "skill_rewards": { "work": 200 },
      "completed": false,
      "expires_at": "2026-01-22T23:59:59Z"
    }
  ],
  "weekly": [
    {
      "id": "protein_champion",
      "name": "Protein Champion",
      "description": "Hit protein target (140g+) 5 days this week",
      "type": "weekly",
      "progress": 3,
      "target": 5,
      "xp_reward": 500,
      "skill_rewards": { "nutrition": 500 },
      "completed": false,
      "expires_at": "2026-01-26T23:59:59Z"
    }
  ],
  "monthly": [],
  "summary": {
    "daily_completed": 1,
    "daily_total": 4,
    "weekly_completed": 0,
    "weekly_total": 2,
    "monthly_completed": 0,
    "monthly_total": 0
  }
}
```

---

#### GET /api/quests/{quest_id}

Returns details for a specific quest.

**Response:**
```json
{
  "id": "morning_triple",
  "name": "Morning Triple",
  "description": "Complete morning routine, log weight, take morning supplements",
  "type": "daily",
  "progress": 2,
  "target": 3,
  "xp_reward": 300,
  "skill_rewards": {
    "consistency": 100,
    "mobility": 100,
    "nutrition": 100
  },
  "completed": false,
  "requirements": [
    { "id": "morning_routine", "name": "Morning routine", "done": true },
    { "id": "weight_log", "name": "Log weight", "done": true },
    { "id": "morning_supps", "name": "Take morning supplements", "done": false }
  ],
  "history": [
    { "date": "2026-01-21", "completed": true },
    { "date": "2026-01-20", "completed": true },
    { "date": "2026-01-19", "completed": false }
  ],
  "streak": 2,
  "expires_at": "2026-01-22T23:59:59Z"
}
```

---

### Achievements

#### GET /api/achievements

Returns all achievements with unlock status.

**Query Parameters:**
- `status` (optional): "unlocked", "locked", "all" (default: "all")
- `category` (optional): Filter by category

**Response:**
```json
{
  "achievements": [
    {
      "id": "first_workout",
      "name": "First Steps",
      "description": "Complete your first workout",
      "category": "milestones",
      "icon": "first_steps.png",
      "xp_reward": 100,
      "unlocked": true,
      "unlocked_at": "2026-01-15T07:30:00Z"
    },
    {
      "id": "strength_25",
      "name": "Journeyman Strength",
      "description": "Reach Strength level 25",
      "category": "skills",
      "icon": "strength_25.png",
      "xp_reward": 500,
      "unlocked": false,
      "unlocked_at": null,
      "progress": 23,
      "target": 25
    }
  ],
  "summary": {
    "total": 50,
    "unlocked": 12,
    "percent_complete": 24
  }
}
```

---

### Streaks

#### GET /api/streaks

Returns current streak information.

**Response:**
```json
{
  "current_streak": 14,
  "longest_streak": 21,
  "streak_started": "2026-01-08",
  "last_activity_date": "2026-01-22",
  "streak_bonus_multiplier": 1.7,
  "days_until_milestone": 7,
  "next_milestone": 21,
  "history": [
    { "date": "2026-01-22", "activities": 4, "xp_earned": 420 },
    { "date": "2026-01-21", "activities": 5, "xp_earned": 380 },
    { "date": "2026-01-20", "activities": 3, "xp_earned": 290 }
  ]
}
```

---

### Stats / Dashboard

#### GET /api/stats/today

Returns today's summary statistics.

**Response:**
```json
{
  "date": "2026-01-22",
  "xp_earned": 420,
  "xp_target": 1200,
  "activities_completed": 4,
  "quests_completed": 2,
  "quests_total": 4,
  "level_ups": 0,
  "current_streak": 14,
  "top_skill_today": {
    "name": "strength",
    "xp_earned": 150
  },
  "breakdown": [
    { "skill": "strength", "xp": 150 },
    { "skill": "mobility", "xp": 75 },
    { "skill": "nutrition", "xp": 115 },
    { "skill": "consistency", "xp": 80 }
  ]
}
```

---

#### GET /api/stats/weekly

Returns weekly statistics.

**Response:**
```json
{
  "week_start": "2026-01-20",
  "week_end": "2026-01-26",
  "total_xp": 2840,
  "average_daily_xp": 473,
  "days_active": 6,
  "level_ups": 2,
  "quests_completed": 8,
  "skills_progress": [
    { "skill": "strength", "xp_gained": 600, "levels_gained": 1 },
    { "skill": "nutrition", "xp_gained": 840, "levels_gained": 1 },
    { "skill": "mobility", "xp_gained": 450, "levels_gained": 0 }
  ],
  "daily_breakdown": [
    { "date": "2026-01-22", "xp": 420 },
    { "date": "2026-01-21", "xp": 510 },
    { "date": "2026-01-20", "xp": 380 }
  ]
}
```

---

### Configuration

#### GET /api/config

Returns app configuration and skill definitions.

**Response:**
```json
{
  "version": "1.0.0",
  "skills": [
    {
      "name": "strength",
      "display_name": "Strength",
      "description": "Physical strength from weight training",
      "icon": "strength.png",
      "color": "#ff6b6b"
    },
    // ... other skills
  ],
  "xp_curve": "osrs_compressed",
  "max_level": 99,
  "theme": {
    "variant": "dark",
    "sounds_enabled": true
  }
}
```

**Caching:** StaleWhileRevalidate, 7 days

---

## Server-Sent Events

### GET /api/events/xp

Real-time XP event stream.

**Headers:**
```
Accept: text/event-stream
Cache-Control: no-cache
```

**Query Parameters:**
- `lastEventId` (optional): Resume from specific event ID

**Event Types:**

#### xp_update

Sent when XP is awarded (from voice pipeline).

```
event: xp_update
id: 12345
retry: 3000
data: {
  "skill": "strength",
  "xp_gained": 150,
  "total_xp": 9600,
  "old_level": 23,
  "new_level": 23,
  "level_up": false,
  "source": "workout_strength_a",
  "streak_bonus": 35,
  "timestamp": "2026-01-22T10:30:00Z"
}
```

#### level_up

Sent when a level-up occurs.

```
event: level_up
id: 12346
data: {
  "skill": "strength",
  "old_level": 23,
  "new_level": 24,
  "total_xp": 12500,
  "milestone": null,
  "timestamp": "2026-01-22T10:30:00Z"
}
```

Milestone values: `"Apprentice"` (10), `"Journeyman"` (25), `"Expert"` (50), `"Master"` (75), `"Maxed"` (99)

#### quest_progress

Sent when quest progress updates.

```
event: quest_progress
id: 12347
data: {
  "quest_id": "morning_triple",
  "progress": 3,
  "target": 3,
  "completed": true,
  "xp_awarded": 300,
  "timestamp": "2026-01-22T10:35:00Z"
}
```

#### achievement_unlocked

Sent when an achievement is unlocked.

```
event: achievement_unlocked
id: 12348
data: {
  "achievement_id": "week_warrior",
  "name": "Week Warrior",
  "description": "Complete all daily quests for 7 days",
  "xp_reward": 500,
  "timestamp": "2026-01-22T10:36:00Z"
}
```

#### heartbeat

Sent every 30 seconds to keep connection alive.

```
event: heartbeat
data: {"timestamp": "2026-01-22T10:30:30Z"}
```

---

## Pydantic Models

```python
# backend/app/models/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class SkillName(str, Enum):
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    MOBILITY = "mobility"
    NUTRITION = "nutrition"
    RECOVERY = "recovery"
    CONSISTENCY = "consistency"
    WORK = "work"

class QuestType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# ----- Skills -----

class SkillSummary(BaseModel):
    name: str
    display_name: str
    level: int
    current_xp: int
    xp_for_current_level: int
    xp_for_next_level: int
    xp_to_next: int
    progress_percent: float
    icon: str
    updated_at: datetime

class SkillsResponse(BaseModel):
    skills: list[SkillSummary]
    total_level: int
    total_xp: int

class XPSource(BaseModel):
    source: str
    xp: int

class Milestone(BaseModel):
    level: int
    name: str
    reached: bool

class RecentXP(BaseModel):
    xp: int
    source: str
    timestamp: datetime

class SkillDetail(SkillSummary):
    description: str
    xp_sources: list[XPSource]
    milestones: list[Milestone]
    recent_xp: list[RecentXP]

# ----- Quests -----

class QuestRequirement(BaseModel):
    id: str
    name: str
    done: bool

class Quest(BaseModel):
    id: str
    name: str
    description: str
    type: QuestType
    progress: int
    target: int
    xp_reward: int
    skill_rewards: dict[str, int]
    completed: bool
    expires_at: datetime

class QuestDetail(Quest):
    requirements: list[QuestRequirement]
    history: list[dict]
    streak: int

class QuestSummary(BaseModel):
    daily_completed: int
    daily_total: int
    weekly_completed: int
    weekly_total: int
    monthly_completed: int
    monthly_total: int

class QuestsResponse(BaseModel):
    daily: list[Quest]
    weekly: list[Quest]
    monthly: list[Quest]
    summary: QuestSummary

# ----- Achievements -----

class Achievement(BaseModel):
    id: str
    name: str
    description: str
    category: str
    icon: str
    xp_reward: int
    unlocked: bool
    unlocked_at: Optional[datetime]
    progress: Optional[int] = None
    target: Optional[int] = None

class AchievementSummary(BaseModel):
    total: int
    unlocked: int
    percent_complete: float

class AchievementsResponse(BaseModel):
    achievements: list[Achievement]
    summary: AchievementSummary

# ----- Streaks -----

class StreakDay(BaseModel):
    date: str
    activities: int
    xp_earned: int

class StreaksResponse(BaseModel):
    current_streak: int
    longest_streak: int
    streak_started: str
    last_activity_date: str
    streak_bonus_multiplier: float
    days_until_milestone: int
    next_milestone: int
    history: list[StreakDay]

# ----- Stats -----

class SkillXPBreakdown(BaseModel):
    skill: str
    xp: int

class TopSkill(BaseModel):
    name: str
    xp_earned: int

class TodayStats(BaseModel):
    date: str
    xp_earned: int
    xp_target: int
    activities_completed: int
    quests_completed: int
    quests_total: int
    level_ups: int
    current_streak: int
    top_skill_today: TopSkill
    breakdown: list[SkillXPBreakdown]

# ----- SSE Events -----

class XPUpdateEvent(BaseModel):
    skill: str
    xp_gained: int
    total_xp: int
    old_level: int
    new_level: int
    level_up: bool
    source: str
    streak_bonus: int
    timestamp: datetime

class LevelUpEvent(BaseModel):
    skill: str
    old_level: int
    new_level: int
    total_xp: int
    milestone: Optional[str]
    timestamp: datetime

class QuestProgressEvent(BaseModel):
    quest_id: str
    progress: int
    target: int
    completed: bool
    xp_awarded: Optional[int]
    timestamp: datetime

class AchievementUnlockedEvent(BaseModel):
    achievement_id: str
    name: str
    description: str
    xp_reward: int
    timestamp: datetime
```

---

## FastAPI Implementation

### Main Application

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api import routes, events
from app.config import settings

app = FastAPI(
    title="ATLAS Command Centre API",
    version="1.0.0",
    description="Gamification dashboard API"
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# API routes
app.include_router(routes.router, prefix="/api")
app.include_router(events.router, prefix="/api")

# Serve React build in production
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=static_path, html=True))
```

### SSE Endpoint

```python
# backend/app/api/events.py
from fastapi import APIRouter, Request, Query
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime

from app.services.xp_watcher import XPWatcher

router = APIRouter()
watcher = XPWatcher()

async def xp_event_generator(request: Request, last_event_id: int):
    """Generator yielding XP events from SQLite."""
    current_id = last_event_id
    heartbeat_interval = 30  # seconds
    last_heartbeat = datetime.now()

    while True:
        if await request.is_disconnected():
            break

        # Check for new events
        events = await watcher.get_events_since(current_id)

        for event in events:
            current_id = event.id
            yield {
                "event": event.event_type,
                "id": str(event.id),
                "retry": 3000,
                "data": json.dumps(event.data)
            }

        # Heartbeat
        if (datetime.now() - last_heartbeat).seconds >= heartbeat_interval:
            yield {
                "event": "heartbeat",
                "data": json.dumps({"timestamp": datetime.now().isoformat()})
            }
            last_heartbeat = datetime.now()

        await asyncio.sleep(0.5)  # Poll every 500ms

@router.get("/events/xp")
async def xp_stream(
    request: Request,
    lastEventId: int = Query(0, alias="lastEventId")
):
    """SSE endpoint for real-time XP updates."""
    return EventSourceResponse(xp_event_generator(request, lastEventId))
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Resource not found
- `500` - Internal server error

---

## Rate Limits

No rate limits for local-only access. If deployed publicly later:
- REST: 100 requests/minute
- SSE: 1 connection per client

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SSE Starlette](https://github.com/sysid/sse-starlette)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
