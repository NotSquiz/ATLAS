# ATLAS Implementation Specifications: R25-R27

**Purpose:** Complete code patterns and configurations extracted from R25-R27 research
**Date:** January 2026
**Status:** Ready for implementation

---

## 1. R25: Local LLM Configuration

### 1.1 Environment Variables

Add to `~/.bashrc`:
```bash
# Ollama optimizations for 4GB VRAM
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

# Optional: limit to single model
export OLLAMA_MAX_LOADED_MODELS=1
```

### 1.2 Ollama Model Setup

```bash
# Pull the model
ollama pull qwen3:4b

# Create ATLAS-optimized Modelfile
cat > ~/ATLAS-Modelfile << 'EOF'
FROM qwen3:4b
PARAMETER num_ctx 4096
PARAMETER num_gpu 99
PARAMETER temperature 0.7
PARAMETER top_p 0.8
SYSTEM "You are ATLAS, a personal life assistant. Respond concisely for voice output. Use /no_think for simple queries."
EOF

# Create the model
ollama create atlas-local -f ~/ATLAS-Modelfile
```

### 1.3 llama.cpp Alternative (Lower Latency)

```bash
./llama-server -m qwen3-4b-q4_k_m.gguf \
  --n-gpu-layers 99 \
  --ctx-size 4096 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --flash-attn \
  --batch-size 256 \
  --host 127.0.0.1 --port 8080
```

### 1.4 VRAM Budget

| Component | VRAM Usage |
|-----------|------------|
| Qwen3-4B Q4_K_M weights | ~2.75GB |
| KV Cache (q8_0, 4K context) | ~0.3GB |
| CUDA overhead | ~0.1GB |
| **Total** | **~3.15GB** |
| Headroom | ~0.85GB |

### 1.5 Thinking Mode Toggle

```python
def get_system_prompt(complexity: str) -> str:
    """Toggle thinking mode based on query complexity."""
    base = "You are ATLAS, a personal life assistant."

    if complexity == "simple":
        # Fast path: ~1,400ms LLM time
        return f"{base} Respond concisely. /no_think"
    else:
        # Quality path: ~1,900ms LLM time
        return f"{base} Think through complex requests carefully."
```

### 1.6 Cloud Routing Logic

```python
from enum import Enum

class RoutingDecision(Enum):
    LOCAL = "local"
    CLOUD_HAIKU = "cloud_haiku"
    CLOUD_SONNET = "cloud_sonnet"

def route_query(
    query: str,
    context_tokens: int,
    confidence: float,
    is_safety_critical: bool = False
) -> RoutingDecision:
    """Decide whether to use local LLM or cloud API."""

    # Always cloud for safety-critical (medical questions)
    if is_safety_critical:
        return RoutingDecision.CLOUD_SONNET

    # Cloud if context too long for local
    if context_tokens > 4000:
        return RoutingDecision.CLOUD_SONNET

    # Cloud if low confidence
    if confidence < 0.7:
        return RoutingDecision.CLOUD_HAIKU

    # Complex multi-step planning
    if "design" in query.lower() or "plan" in query.lower():
        if len(query) > 200:  # Long complex query
            return RoutingDecision.CLOUD_SONNET

    return RoutingDecision.LOCAL
```

---

## 2. R26: APIs for Your Use Case

### 2.1 Garmin API Integration

```python
import httpx
from datetime import date, timedelta
from typing import Optional, Dict

class GarminClient:
    """Garmin Connect API client for Forerunner 165."""

    BASE_URL = "https://connect.garmin.com"

    def __init__(self, email: str, password: str):
        self.session = httpx.AsyncClient()
        self.email = email
        self.password = password
        self._authenticated = False

    async def authenticate(self) -> bool:
        """Authenticate with Garmin Connect."""
        # Note: Garmin uses SSO, consider using garminconnect library
        # pip install garminconnect
        pass

    async def get_hrv_data(self, day: date) -> Optional[Dict]:
        """Get HRV data for a specific day."""
        endpoint = f"/hrv-service/hrv/{day.isoformat()}"
        resp = await self.session.get(f"{self.BASE_URL}{endpoint}")
        return resp.json() if resp.status_code == 200 else None

    async def get_sleep_data(self, day: date) -> Optional[Dict]:
        """Get sleep data including stages and score."""
        endpoint = f"/sleep-service/sleep/dailySleepData/{day.isoformat()}"
        resp = await self.session.get(f"{self.BASE_URL}{endpoint}")
        return resp.json() if resp.status_code == 200 else None

    async def get_activities(self, start: date, end: date) -> list:
        """Get activities in date range."""
        endpoint = "/activitylist-service/activities/search/activities"
        params = {"startDate": start.isoformat(), "endDate": end.isoformat()}
        resp = await self.session.get(f"{self.BASE_URL}{endpoint}", params=params)
        return resp.json() if resp.status_code == 200 else []

    async def get_body_composition(self) -> Optional[Dict]:
        """Get latest body composition (weight, body fat %)."""
        endpoint = "/weight-service/weight/latest"
        resp = await self.session.get(f"{self.BASE_URL}{endpoint}")
        return resp.json() if resp.status_code == 200 else None

# Recommended: Use garminconnect library instead
# pip install garminconnect
from garminconnect import Garmin

async def get_garmin_data():
    """Example using garminconnect library."""
    client = Garmin("email@example.com", "password")
    client.login()

    # Get today's data
    today = date.today()

    return {
        "hrv": client.get_hrv_data(today.isoformat()),
        "sleep": client.get_sleep_data(today.isoformat()),
        "heart_rate": client.get_heart_rates(today.isoformat()),
        "steps": client.get_steps_data(today.isoformat()),
        "stress": client.get_stress_data(today.isoformat()),
    }
```

### 2.2 Exercise Database (Curated for Your Equipment)

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set

class MuscleGroup(Enum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    CORE = "core"
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    NECK = "neck"

class Equipment(Enum):
    POWER_RACK = "power_rack"
    BENCH = "bench"
    PULLUP_BAR = "pullup_bar"
    BARBELL = "barbell"
    DUMBBELLS = "dumbbells"
    SKIPPING_ROPE = "skipping_rope"
    NECK_HARNESS = "neck_harness"
    BODYWEIGHT = "bodyweight"

@dataclass
class Exercise:
    id: str
    name: str
    equipment: Set[Equipment]
    primary_muscles: Set[MuscleGroup]
    secondary_muscles: Set[MuscleGroup]
    instructions: List[str]
    injury_contraindications: Set[str]  # e.g., {"shoulder", "lower_back"}
    difficulty: str  # "beginner", "intermediate", "advanced"

    def is_safe_for(self, injuries: Set[str]) -> bool:
        """Check if exercise is safe given user's injuries."""
        return not bool(self.injury_contraindications & injuries)

# Your curated exercise database
EXERCISE_DB: List[Exercise] = [
    # === CHEST ===
    Exercise(
        id="bench_press",
        name="Barbell Bench Press",
        equipment={Equipment.BENCH, Equipment.BARBELL, Equipment.POWER_RACK},
        primary_muscles={MuscleGroup.CHEST},
        secondary_muscles={MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS},
        instructions=[
            "Lie on bench with eyes under the bar",
            "Grip bar slightly wider than shoulder width",
            "Unrack and lower to mid-chest",
            "Press up to lockout",
        ],
        injury_contraindications={"shoulder", "rotator_cuff"},
        difficulty="intermediate",
    ),
    Exercise(
        id="incline_db_press",
        name="Incline Dumbbell Press",
        equipment={Equipment.BENCH, Equipment.DUMBBELLS},
        primary_muscles={MuscleGroup.CHEST},
        secondary_muscles={MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS},
        instructions=[
            "Set bench to 30-45 degree incline",
            "Hold dumbbells at shoulder level",
            "Press up and together",
            "Lower with control",
        ],
        injury_contraindications={"shoulder"},
        difficulty="beginner",
    ),

    # === BACK ===
    Exercise(
        id="pullups",
        name="Pull-ups",
        equipment={Equipment.PULLUP_BAR},
        primary_muscles={MuscleGroup.BACK},
        secondary_muscles={MuscleGroup.BICEPS, MuscleGroup.FOREARMS},
        instructions=[
            "Hang from bar with overhand grip",
            "Pull up until chin over bar",
            "Lower with control",
        ],
        injury_contraindications={"shoulder", "elbow"},
        difficulty="intermediate",
    ),
    Exercise(
        id="barbell_row",
        name="Barbell Row",
        equipment={Equipment.BARBELL},
        primary_muscles={MuscleGroup.BACK},
        secondary_muscles={MuscleGroup.BICEPS, MuscleGroup.CORE},
        instructions=[
            "Hinge at hips, back flat",
            "Pull bar to lower chest",
            "Squeeze shoulder blades",
            "Lower with control",
        ],
        injury_contraindications={"lower_back"},
        difficulty="intermediate",
    ),
    Exercise(
        id="deadlift",
        name="Conventional Deadlift",
        equipment={Equipment.BARBELL, Equipment.POWER_RACK},
        primary_muscles={MuscleGroup.BACK, MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES},
        secondary_muscles={MuscleGroup.CORE, MuscleGroup.FOREARMS},
        instructions=[
            "Stand with feet hip-width, bar over mid-foot",
            "Hinge and grip bar",
            "Brace core, drive through floor",
            "Lock out hips and knees together",
        ],
        injury_contraindications={"lower_back", "hip"},
        difficulty="intermediate",
    ),

    # === LEGS ===
    Exercise(
        id="squat",
        name="Barbell Back Squat",
        equipment={Equipment.BARBELL, Equipment.POWER_RACK},
        primary_muscles={MuscleGroup.QUADS, MuscleGroup.GLUTES},
        secondary_muscles={MuscleGroup.HAMSTRINGS, MuscleGroup.CORE},
        instructions=[
            "Bar on upper back, not neck",
            "Feet shoulder width, toes slightly out",
            "Descend until thighs parallel",
            "Drive up through heels",
        ],
        injury_contraindications={"knee", "lower_back", "hip"},
        difficulty="intermediate",
    ),

    # === SHOULDERS ===
    Exercise(
        id="overhead_press",
        name="Overhead Press",
        equipment={Equipment.BARBELL, Equipment.POWER_RACK},
        primary_muscles={MuscleGroup.SHOULDERS},
        secondary_muscles={MuscleGroup.TRICEPS, MuscleGroup.CORE},
        instructions=[
            "Bar at collar bone level",
            "Press straight up",
            "Lock out overhead",
            "Lower with control",
        ],
        injury_contraindications={"shoulder", "rotator_cuff", "neck"},
        difficulty="intermediate",
    ),

    # === NECK ===
    Exercise(
        id="neck_curl",
        name="Neck Curl (Harness)",
        equipment={Equipment.NECK_HARNESS},
        primary_muscles={MuscleGroup.NECK},
        secondary_muscles=set(),
        instructions=[
            "Attach weight to harness",
            "Sit on bench, lean forward",
            "Curl head up against resistance",
            "Lower slowly",
        ],
        injury_contraindications={"neck", "cervical"},
        difficulty="beginner",
    ),

    # === CARDIO ===
    Exercise(
        id="jump_rope",
        name="Jump Rope",
        equipment={Equipment.SKIPPING_ROPE},
        primary_muscles={MuscleGroup.CALVES},
        secondary_muscles={MuscleGroup.CORE, MuscleGroup.SHOULDERS},
        instructions=[
            "Hold handles at hip height",
            "Jump with minimal height",
            "Land on balls of feet",
            "Keep core tight",
        ],
        injury_contraindications={"ankle", "knee", "achilles"},
        difficulty="beginner",
    ),
]

def get_exercises_for_muscle(
    muscle: MuscleGroup,
    user_injuries: Set[str] = set()
) -> List[Exercise]:
    """Get exercises targeting a muscle, filtered by injuries."""
    return [
        ex for ex in EXERCISE_DB
        if muscle in ex.primary_muscles and ex.is_safe_for(user_injuries)
    ]
```

### 2.3 Blueprint-Style Tracking (SQLite Schema)

```sql
-- Core tracking tables for Bryan Johnson-style Blueprint

-- Daily biomarkers and measurements
CREATE TABLE daily_metrics (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Sleep (from Garmin)
    sleep_hours REAL,
    sleep_score INTEGER,
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,

    -- Heart metrics (from Garmin)
    resting_hr INTEGER,
    hrv_avg INTEGER,
    hrv_morning INTEGER,

    -- Body
    weight_kg REAL,
    body_fat_pct REAL,

    -- Subjective
    energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
    mood INTEGER CHECK(mood BETWEEN 1 AND 10),
    stress_level INTEGER CHECK(stress_level BETWEEN 1 AND 10),

    -- Notes
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplement/herb tracking
CREATE TABLE supplements (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    dosage TEXT,
    timing TEXT,  -- "morning", "with_meal", "before_bed"
    purpose TEXT,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE supplement_log (
    id INTEGER PRIMARY KEY,
    supplement_id INTEGER REFERENCES supplements(id),
    date DATE NOT NULL,
    time TIME,
    taken BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- Workout tracking
CREATE TABLE workouts (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    type TEXT,  -- "strength", "cardio", "mobility", "rehab"
    duration_minutes INTEGER,
    notes TEXT,
    energy_before INTEGER CHECK(energy_before BETWEEN 1 AND 10),
    energy_after INTEGER CHECK(energy_after BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workout_exercises (
    id INTEGER PRIMARY KEY,
    workout_id INTEGER REFERENCES workouts(id),
    exercise_id TEXT NOT NULL,
    exercise_name TEXT NOT NULL,

    -- For strength exercises
    sets INTEGER,
    reps TEXT,  -- "8,8,6" for multiple sets
    weight_kg REAL,

    -- For cardio
    duration_seconds INTEGER,
    distance_meters REAL,

    notes TEXT,
    order_index INTEGER
);

-- Blood work / lab results
CREATE TABLE lab_results (
    id INTEGER PRIMARY KEY,
    test_date DATE NOT NULL,
    marker TEXT NOT NULL,  -- "vitamin_d", "testosterone", "hba1c"
    value REAL NOT NULL,
    unit TEXT,
    reference_low REAL,
    reference_high REAL,
    notes TEXT
);

-- Injuries tracking
CREATE TABLE injuries (
    id INTEGER PRIMARY KEY,
    body_part TEXT NOT NULL,  -- "shoulder", "lower_back"
    description TEXT,
    onset_date DATE,
    severity INTEGER CHECK(severity BETWEEN 1 AND 5),
    status TEXT DEFAULT 'active',  -- "active", "recovering", "resolved"
    contraindicated_exercises TEXT,  -- JSON array
    notes TEXT
);

-- Indexes
CREATE INDEX idx_daily_metrics_date ON daily_metrics(date);
CREATE INDEX idx_supplement_log_date ON supplement_log(date);
CREATE INDEX idx_workouts_date ON workouts(date);
CREATE INDEX idx_lab_results_date ON lab_results(test_date);
```

### 2.4 Open Food Facts (For Later - Nutrition Tracking)

```python
import httpx
from typing import Optional, Dict, List

class OpenFoodFactsClient:
    """Client for Open Food Facts API (includes Australian products)."""

    BASE_URL = "https://world.openfoodfacts.org/api/v2"

    def __init__(self):
        self.session = httpx.AsyncClient(
            headers={"User-Agent": "ATLAS/1.0 (personal assistant)"}
        )

    async def get_product(self, barcode: str) -> Optional[Dict]:
        """Look up product by barcode."""
        resp = await self.session.get(
            f"{self.BASE_URL}/product/{barcode}",
            timeout=2.0
        )
        data = resp.json()
        if data.get("status") == 1:
            return data.get("product")
        return None

    async def search_products(self, query: str, page: int = 1) -> List[Dict]:
        """Search products by name."""
        resp = await self.session.get(
            f"{self.BASE_URL}/search",
            params={
                "search_terms": query,
                "page": page,
                "page_size": 20,
                "countries_tags_en": "australia",  # Prefer AU products
            },
            timeout=3.0
        )
        data = resp.json()
        return data.get("products", [])

    def extract_nutrients(self, product: Dict) -> Dict:
        """Extract key nutrients from product data."""
        nutrients = product.get("nutriments", {})
        return {
            "calories_per_100g": nutrients.get("energy-kcal_100g"),
            "protein_per_100g": nutrients.get("proteins_100g"),
            "carbs_per_100g": nutrients.get("carbohydrates_100g"),
            "fat_per_100g": nutrients.get("fat_100g"),
            "fiber_per_100g": nutrients.get("fiber_100g"),
            "sodium_per_100g": nutrients.get("sodium_100g"),
            "sugar_per_100g": nutrients.get("sugars_100g"),
        }
```

---

## 3. R27: LangGraph Patterns

### 3.1 When to Use LangGraph

```python
def should_use_langgraph(skill_name: str) -> bool:
    """Decide if skill needs LangGraph or simpler patterns."""

    LANGGRAPH_SKILLS = {
        "morning_workout",      # Multi-tool DAG + verification
        "weekly_workout_plan",  # Complex planning
        "content_pipeline",     # Branching + retry
        "meal_planning",        # Multiple API calls
    }

    SIMPLE_SKILLS = {
        "log_supplement",       # Single DB write
        "get_hrv",              # Single API call
        "set_reminder",         # Simple action
        "quick_question",       # Direct LLM call
    }

    return skill_name in LANGGRAPH_SKILLS
```

### 3.2 Basic LangGraph StateGraph

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class WorkoutState(TypedDict):
    messages: Annotated[list, add_messages]
    user_injuries: list[str]
    equipment: list[str]
    workout_type: str
    workout_plan: dict | None
    confidence: float

def load_user_profile(state: WorkoutState) -> dict:
    """Load user injuries and equipment from DB."""
    # Query SQLite for active injuries
    injuries = ["shoulder"]  # Example
    equipment = ["power_rack", "bench", "barbell", "dumbbells", "pullup_bar"]
    return {"user_injuries": injuries, "equipment": equipment}

def generate_workout(state: WorkoutState) -> dict:
    """Generate workout plan based on constraints."""
    # Filter exercises by injuries and equipment
    # Generate plan
    return {"workout_plan": {...}, "confidence": 0.85}

def route_by_confidence(state: WorkoutState) -> Literal["present", "clarify"]:
    """Route based on generation confidence."""
    if state["confidence"] >= 0.8:
        return "present"
    return "clarify"

# Build graph
builder = StateGraph(WorkoutState)
builder.add_node("load_profile", load_user_profile)
builder.add_node("generate", generate_workout)
builder.add_node("present", lambda s: {"messages": [f"Here's your workout: {s['workout_plan']}"]})
builder.add_node("clarify", lambda s: {"messages": ["I need more info about your preferences."]})

builder.add_edge(START, "load_profile")
builder.add_edge("load_profile", "generate")
builder.add_conditional_edges("generate", route_by_confidence)
builder.add_edge("present", END)
builder.add_edge("clarify", END)

workout_graph = builder.compile()
```

### 3.3 SqliteSaver Checkpointing

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# Create checkpointer
conn = sqlite3.connect("atlas_checkpoints.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# Compile graph with checkpointing
graph = builder.compile(checkpointer=checkpointer)

# Always provide thread_id for persistence
config = {"configurable": {"thread_id": "morning-workout-2024-01-05"}}
result = graph.invoke({"messages": [...], "workout_type": "strength"}, config)
```

### 3.4 Streaming for Voice Latency

```python
async def stream_workout_response(user_request: str):
    """Stream workout generation for voice output."""

    config = {"configurable": {"thread_id": "voice-session-1"}}

    async for event in graph.astream_events(
        {"messages": [user_request]},
        config=config,
        version="v2"
    ):
        if event["event"] == "on_chat_model_stream":
            # Feed to TTS immediately
            chunk = event["data"]["chunk"].content
            yield chunk
```

### 3.5 Parallel Execution with asyncio.gather

For simpler parallel needs (no LangGraph):

```python
import asyncio

async def prepare_workout_data(user_id: str):
    """Fetch all data needed for workout in parallel."""

    garmin_task = get_garmin_data()
    injuries_task = get_user_injuries(user_id)
    history_task = get_recent_workouts(user_id)

    garmin, injuries, history = await asyncio.gather(
        garmin_task,
        injuries_task,
        history_task,
        return_exceptions=True  # Don't fail if one fails
    )

    return {
        "garmin": garmin if not isinstance(garmin, Exception) else None,
        "injuries": injuries if not isinstance(injuries, Exception) else [],
        "history": history if not isinstance(history, Exception) else [],
    }
```

---

## 4. Implementation Checklist

### Phase 0: Foundation
- [ ] Apply WSL2 .wslconfig (6GB memory, swap, dropcache)
- [ ] Fix DoSvc service issue
- [ ] Install Ollama
- [ ] Pull and configure Qwen3-4B
- [ ] Set environment variables (FLASH_ATTENTION, KV_CACHE)
- [ ] Test local LLM latency
- [ ] Set up SQLite database with Blueprint schema
- [ ] Basic MCP server skeleton

### Phase 1: Core Lifestyle
- [ ] **Injury Rehab Session** (separate Opus conversation)
- [ ] **Blueprint Protocol Session** (with Naturopath input)
- [ ] Garmin API integration (garminconnect library)
- [ ] Curated exercise database for your equipment
- [ ] Workout generation with injury filtering
- [ ] Supplement logging system
- [ ] Daily metrics tracking
- [ ] Voice interface (Moonshine STT + Kokoro TTS)

### Phase 2: Enhanced (When Ready)
- [ ] Nutrition tracking (Open Food Facts)
- [ ] Meal logging
- [ ] Progress photos/measurements
- [ ] LangGraph for complex workflows

### Phase 3: Baby Brains (Month+)
- [ ] Instagram Graph API
- [ ] TikTok API
- [ ] YouTube Data API
- [ ] Content analytics dashboard

---

## 5. Separate Opus Sessions Needed

### Session 1: Injury Rehab Design

**Prompt for new conversation:**
```
I need help designing an injury rehabilitation protocol for my home workouts.

My injuries:
- [List your specific injuries]

My equipment:
- Power rack
- Bench press
- Pull-up bar
- Barbell/deadlift setup
- Dumbbells
- Skipping rope
- Neck weight harness

Please help me:
1. Identify which exercises to AVOID for each injury
2. Design REHAB exercises I can do with my equipment
3. Create a progression plan from rehab to full training
4. Set realistic timelines for recovery

I want this information structured so I can add it to my ATLAS personal assistant's exercise database.
```

### Session 2: Blueprint Protocol Design

**Prompt for new conversation:**
```
I want to design a Bryan Johnson-style Blueprint health protocol for tracking and optimization.

Context:
- My partner is a Naturopath who can advise on supplements/herbs
- I have a Garmin Forerunner 165 for HRV, sleep, activity tracking
- I want to do baseline blood work and track biomarkers

Help me design:
1. What biomarkers to track (blood work, daily metrics)
2. Supplement/herb stack considerations (my Naturopath will validate)
3. Daily routine structure (sleep, light, meals, exercise timing)
4. Weekly/monthly review cadence
5. What "success" looks like for my goals

I want this structured so I can add it to my ATLAS personal assistant's tracking system.
```

---

## Summary

This document contains all implementation specifications from R25-R27:
- Complete Qwen3-4B configuration
- Garmin API integration pattern
- Curated exercise database for your equipment
- Blueprint-style SQLite tracking schema
- LangGraph patterns for complex workflows
- Phase-by-phase implementation checklist
- Prompts for separate Opus sessions

**Next step:** Start Phase 0 (Foundation) or schedule the Injury Rehab session.
