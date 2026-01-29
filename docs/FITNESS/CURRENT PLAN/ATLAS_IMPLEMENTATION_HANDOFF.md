# ATLAS Implementation Handoff v1.0
## For Fresh Opus CLI Agent

**Context:** This document consolidates analysis from two independent review sessions (Opus CLI + Opus Web) plus Alexander's design decisions. Execute in phase order.

---

## Alexander's Design Decisions (Settled)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Voice vs CLI for pain/supps | **Voice primary** | Reduce friction, build habits |
| Workout confirmation UX | **Option B (smart confirmation)** | Confirm only on mismatch or flags |
| RHR baseline | **Hardcode now, auto-calc after 14 days** | Need initial data before rolling average |
| Orphaned tables | **Keep - future features** | baseline_assessments required for protocol |
| Session buffer persistence | **SQLite-backed with TTL** | Survive restarts, feel "alive" |

---

## Phase 0: Bug Fixes (Do First)

These are broken, not missing. ~30 minutes total.

### 0.1 Fix HRV Status Passing

**File:** `atlas/health/service.py` (around line 206)

**Problem:** `hrv_status=None` is hardcoded. The traffic light algorithm never receives actual HRV data even when Garmin provides it.

**Fix:**
```python
# BEFORE (broken)
traffic_light = self.router.calculate(
    hrv_status=None,  # ← This is the bug
    ...
)

# AFTER (fixed)
traffic_light = self.router.calculate(
    hrv_status=garmin_data.get("hrv_status"),  # Or however HRV is fetched
    ...
)
```

**Verification:** After fix, run `atlas health status` and confirm HRV status appears in output.

---

### 0.2 Store Body Battery in daily_metrics

**Problem:** Body battery is fetched from Garmin but not persisted. Breaks trend analysis.

**File:** `atlas/health/service.py` - `log_daily_metrics()` function

**Fix:** Add `body_battery` to the INSERT statement and function parameters.

**Schema check:** Verify `daily_metrics` table has `body_battery INTEGER` column. If not, add migration:
```sql
ALTER TABLE daily_metrics ADD COLUMN body_battery INTEGER;
```

---

### 0.3 Change Insufficient Data Default to RED

**File:** `atlas/health/router.py` (lines 185-191)

**Problem:** When data is missing, system defaults to YELLOW (moderate intensity OK). Should default to RED (conservative).

**Fix:**
```python
# BEFORE
if insufficient_data:
    return TrafficLight.YELLOW

# AFTER
if insufficient_data:
    return TrafficLight.RED
```

**Rationale:** Unknown state should be conservative. User can override if they know they're fine.

---

### 0.4 Fix Garmin Token Permissions

**Command:**
```bash
chmod 600 ~/.atlas/garmin_*
```

**Verification:** `ls -la ~/.atlas/garmin_*` should show `-rw-------`

---

### 0.5 Add Body Battery YELLOW Threshold

**File:** `atlas/health/router.py`

**Problem:** Body battery < 25 triggers RED, but 26-49 is treated as GREEN. Should be YELLOW.

**Fix:** Add condition:
```python
if body_battery is not None and body_battery < 50:
    factors.append("low_body_battery")
    if body_battery < 25:
        return TrafficLight.RED
    else:
        return TrafficLight.YELLOW  # 25-49 range
```

---

## Phase 1: Pain Logging Voice Intent

### 1.1 Schema Update

**File:** Migration or direct SQL

```sql
-- Add measured_at for when pain was actually felt (vs when logged)
ALTER TABLE pain_log ADD COLUMN measured_at TIMESTAMP;

-- Add index for date queries
CREATE INDEX IF NOT EXISTS idx_pain_log_date ON pain_log(date);
CREATE INDEX IF NOT EXISTS idx_pain_log_body_part ON pain_log(body_part);
```

---

### 1.2 Voice Patterns

**File:** `atlas/voice/bridge_file_server.py`

Add at top of file with other patterns:
```python
PAIN_PATTERNS = [
    # Direct pain reports
    r"(?:my )?(\w+)(?: is)? (?:at )?(?:a )?(\d+)(?: out of 10)?",  # "shoulder is at a 4"
    r"log pain[:\s]+(\w+)\s+(\d+)",  # "log pain: shoulder 4"
    r"(\w+) (?:pain|hurts|aching)(?: at)? (\d+)",  # "shoulder pain 4"
    
    # Stiffness reports
    r"(\w+) is stiff",  # "back is stiff"
    r"stiff (\w+)",  # "stiff shoulder"
    
    # Status queries
    r"pain (?:status|check|levels?)",
    r"how(?:'s| is) my pain",
]

# Body part normalization
BODY_PART_ALIASES = {
    "shoulder": "shoulder",
    "shoulders": "shoulder",
    "back": "lower_back",
    "lower back": "lower_back",
    "ankle": "ankle",
    "ankles": "ankle",
    "foot": "feet",
    "feet": "feet",
    "knee": "knee",
    "knees": "knee",
}
```

---

### 1.3 Detection Method

```python
def _is_pain_intent(self, text: str) -> tuple[bool, dict | None]:
    """
    Returns (is_pain_intent, extracted_data)
    extracted_data keys: action, body_part, pain_level, is_stiffness
    """
    text_lower = text.lower()
    
    # Check for status query first
    if re.search(r"pain (?:status|check|levels?)|how(?:'s| is) my pain", text_lower):
        return True, {"action": "status"}
    
    # Check for pain level reports
    # Pattern: "shoulder is at a 4" or "shoulder 4 out of 10"
    match = re.search(r"(?:my )?(\w+)(?: is)? (?:at )?(?:a )?(\d+)", text_lower)
    if match:
        body_part = self._normalize_body_part(match.group(1))
        if body_part:
            pain_level = int(match.group(2))
            if 0 <= pain_level <= 10:
                return True, {
                    "action": "log",
                    "body_part": body_part,
                    "pain_level": pain_level,
                    "is_stiffness": False
                }
    
    # Check for stiffness
    match = re.search(r"(\w+) is stiff|stiff (\w+)", text_lower)
    if match:
        body_part = self._normalize_body_part(match.group(1) or match.group(2))
        if body_part:
            return True, {
                "action": "log",
                "body_part": body_part,
                "pain_level": None,
                "is_stiffness": True
            }
    
    return False, None

def _normalize_body_part(self, part: str) -> str | None:
    """Normalize body part aliases."""
    return BODY_PART_ALIASES.get(part.lower().strip())
```

---

### 1.4 Handler Method

```python
async def _handle_pain(self, data: dict) -> str:
    """Handle pain logging and status queries."""
    from atlas.health.pain import PainService  # Or wherever this lives
    
    service = PainService()
    
    if data["action"] == "status":
        recent = service.get_recent(days=3)
        if not recent:
            return "No pain logged in the last 3 days."
        
        summary = []
        for entry in recent:
            summary.append(f"{entry.body_part}: {entry.pain_level}/10")
        return "Recent pain levels: " + ", ".join(summary)
    
    elif data["action"] == "log":
        if data["is_stiffness"]:
            service.log_stiffness(
                body_part=data["body_part"],
                measured_at=datetime.now()
            )
            return f"Logged stiffness in {data['body_part']}."
        else:
            service.log_pain(
                body_part=data["body_part"],
                pain_level=data["pain_level"],
                measured_at=datetime.now()
            )
            
            # Alert if high pain
            if data["pain_level"] >= 6:
                return f"Logged {data['body_part']} at {data['pain_level']}/10. That's elevated - consider modifying today's workout."
            else:
                return f"Logged {data['body_part']} at {data['pain_level']}/10."
```

---

### 1.5 Integration Point

In `process_audio()`, add to the if/elif chain **before** the LLM fallback:

```python
# After CAPTURE check, before LLM routing
elif (pain_result := self._is_pain_intent(transcription.text))[0]:
    _, data = pain_result
    response_text = await self._handle_pain(data)
    action_type = "pain"
    saved_to = "pain_log"
```

---

### 1.6 Traffic Light Integration

**File:** `atlas/health/router.py`

Add pain check to traffic light calculation:

```python
def _check_recent_pain(self) -> tuple[bool, str | None]:
    """Check if any body part has pain >= 6 in last 24 hours."""
    from atlas.health.pain import PainService
    
    service = PainService()
    recent = service.get_recent(hours=24)
    
    high_pain = [p for p in recent if p.pain_level and p.pain_level >= 6]
    if high_pain:
        worst = max(high_pain, key=lambda p: p.pain_level)
        return True, f"{worst.body_part} at {worst.pain_level}/10"
    
    return False, None
```

Call this in `calculate()` and factor into YELLOW/RED decision.

---

## Phase 2: Supplement Logging Voice Intent

### 2.1 Voice Patterns (Specific to General)

**CRITICAL:** Order matters. Individual supplement patterns MUST come before batch patterns.

```python
SUPPLEMENT_PATTERNS = [
    # Individual supplements (FIRST - most specific)
    r"took (?:my )?(vitamin d|omega|creatine|magnesium|zinc|electrolytes)",
    r"missed (?:my )?(vitamin d|omega|creatine|magnesium|zinc|electrolytes)",
    r"skipped (?:my )?(vitamin d|omega|creatine|magnesium|zinc|electrolytes)",
    
    # Timing-specific batches (SECOND)
    r"took (?:my )?morning (?:supps?|supplements?|stack)",
    r"took (?:my )?evening (?:supps?|supplements?|stack)",
    r"took (?:my )?(?:before )?bed (?:supps?|supplements?|stack)",
    
    # Generic batches (LAST - least specific)
    r"took (?:my )?(?:all )?(?:supps?|supplements?)",
    r"supplement (?:check|status|checklist)",
    r"(?:supps?|supplements?) (?:check|status)",
]

SUPPLEMENT_NAME_MAP = {
    "vitamin d": "Vitamin D",
    "omega": "Omega 3",
    "creatine": "Creatine",
    "magnesium": "Magnesium",
    "zinc": "Zinc",
    "electrolytes": "Electrolytes",
    # Add all 17 supplements
}
```

---

### 2.2 Detection Method

```python
def _is_supplement_intent(self, text: str) -> tuple[bool, dict | None]:
    """
    Returns (is_supplement_intent, extracted_data)
    extracted_data keys: action, timing, supplement_name, missed
    """
    text_lower = text.lower()
    
    # Status check
    if re.search(r"supplement (?:check|status)|supps? (?:check|status)", text_lower):
        return True, {"action": "status"}
    
    # Individual supplement (check FIRST)
    for supp_key in SUPPLEMENT_NAME_MAP.keys():
        if supp_key in text_lower:
            missed = "missed" in text_lower or "skipped" in text_lower
            return True, {
                "action": "log_single",
                "supplement_name": SUPPLEMENT_NAME_MAP[supp_key],
                "missed": missed
            }
    
    # Timing-specific batch
    if "morning" in text_lower:
        return True, {"action": "log_batch", "timing": "morning"}
    if "evening" in text_lower or "bed" in text_lower:
        return True, {"action": "log_batch", "timing": "before_bed"}
    
    # Generic batch
    if re.search(r"took (?:my )?(?:all )?(?:supps?|supplements?)", text_lower):
        return True, {"action": "log_batch", "timing": None}
    
    return False, None
```

---

### 2.3 Handler Method

```python
async def _handle_supplement(self, data: dict) -> str:
    """Handle supplement logging and status."""
    from atlas.health.supplement import SupplementService
    
    service = SupplementService()
    
    if data["action"] == "status":
        checklist = service.get_today()
        taken = checklist.taken_count
        total = checklist.total
        pct = checklist.completion_pct
        
        if pct == 100:
            return f"All {total} supplements taken. Nice work."
        elif pct == 0:
            return f"No supplements logged yet. {total} remaining."
        else:
            remaining = [s.name for s in checklist.items if not s.taken]
            return f"{taken} of {total} taken ({pct:.0f}%). Remaining: {', '.join(remaining[:3])}{'...' if len(remaining) > 3 else ''}"
    
    elif data["action"] == "log_single":
        if data["missed"]:
            service.mark_taken(data["supplement_name"], taken=False, notes="missed")
            return f"Noted - {data['supplement_name']} missed today."
        else:
            service.mark_taken(data["supplement_name"])
            return f"{data['supplement_name']} logged."
    
    elif data["action"] == "log_batch":
        timing = data.get("timing")
        if timing:
            count = service.mark_all_taken(timing=timing)
            return f"{timing.replace('_', ' ').title()} stack logged. {count} supplements."
        else:
            count = service.mark_all_taken()
            return f"All {count} supplements logged. Solid discipline."
```

---

### 2.4 Integration Point

In `process_audio()`, add **after WEIGHT, before WORKOUT**:

```python
elif (supp_result := self._is_supplement_intent(transcription.text))[0]:
    _, data = supp_result
    response_text = await self._handle_supplement(data)
    action_type = "supplement"
    saved_to = "supplement_log"
```

---

## Phase 3: Session Buffer (Context Memory)

### 3.1 Schema

```sql
CREATE TABLE IF NOT EXISTS session_buffer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    intent_type TEXT,  -- 'weight', 'supplement', 'llm', etc.
    topic_extracted TEXT,  -- 'sleep', 'workout', 'nutrition', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_buffer_created ON session_buffer(created_at);
```

---

### 3.2 Session Buffer Class

**File:** `atlas/voice/session_buffer.py` (new file)

```python
"""
Short-term conversation context for voice interactions.
Persists across restarts but expires after TTL.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import sqlite3

@dataclass
class Exchange:
    user_input: str
    assistant_response: str
    intent_type: str
    topic: Optional[str]
    timestamp: datetime

class SessionBuffer:
    """SQLite-backed session context with TTL."""
    
    def __init__(
        self,
        db_path: str = "~/.atlas/atlas.db",
        max_exchanges: int = 5,
        ttl_minutes: int = 10
    ):
        self.db_path = os.path.expanduser(db_path)
        self.max_exchanges = max_exchanges
        self.ttl = timedelta(minutes=ttl_minutes)
        self._ensure_table()
    
    def _ensure_table(self):
        """Create table if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    intent_type TEXT,
                    topic_extracted TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def add(
        self,
        user_input: str,
        response: str,
        intent_type: str = "unknown",
        topic: Optional[str] = None
    ):
        """Add exchange to buffer, pruning old entries."""
        with sqlite3.connect(self.db_path) as conn:
            # Insert new
            conn.execute(
                """INSERT INTO session_buffer 
                   (user_input, assistant_response, intent_type, topic_extracted)
                   VALUES (?, ?, ?, ?)""",
                (user_input, response, intent_type, topic)
            )
            
            # Prune old (keep only max_exchanges)
            conn.execute("""
                DELETE FROM session_buffer 
                WHERE id NOT IN (
                    SELECT id FROM session_buffer 
                    ORDER BY created_at DESC 
                    LIMIT ?
                )
            """, (self.max_exchanges,))
    
    def get_context(self) -> str:
        """Get recent exchanges within TTL, formatted for injection."""
        cutoff = datetime.now() - self.ttl
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT user_input, assistant_response, intent_type, topic_extracted
                   FROM session_buffer 
                   WHERE created_at > ?
                   ORDER BY created_at ASC""",
                (cutoff.isoformat(),)
            ).fetchall()
        
        if not rows:
            return ""
        
        lines = []
        for row in rows:
            lines.append(f"User: {row['user_input']}")
            lines.append(f"ATLAS: {row['assistant_response']}")
        
        return "\n".join(lines)
    
    def last_topic(self) -> Optional[str]:
        """Get the most recent topic for pronoun resolution."""
        cutoff = datetime.now() - self.ttl
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                """SELECT topic_extracted FROM session_buffer 
                   WHERE created_at > ? AND topic_extracted IS NOT NULL
                   ORDER BY created_at DESC LIMIT 1""",
                (cutoff.isoformat(),)
            ).fetchone()
        
        return result[0] if result else None
    
    def clear(self):
        """Clear all buffer entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM session_buffer")
```

---

### 3.3 Topic Extraction Helper

```python
def extract_topic(intent_type: str, user_input: str) -> Optional[str]:
    """Extract the topic from an exchange for later reference."""
    
    # Direct mapping from intent
    INTENT_TO_TOPIC = {
        "weight": "weight",
        "workout": "workout",
        "exercise": "exercise",
        "health": "health",
        "meal": "nutrition",
        "supplement": "supplements",
        "pain": "pain",
    }
    
    if intent_type in INTENT_TO_TOPIC:
        return INTENT_TO_TOPIC[intent_type]
    
    # For LLM queries, try keyword extraction
    text_lower = user_input.lower()
    
    if any(w in text_lower for w in ["sleep", "slept", "rest"]):
        return "sleep"
    if any(w in text_lower for w in ["workout", "exercise", "training"]):
        return "workout"
    if any(w in text_lower for w in ["eat", "food", "meal", "diet"]):
        return "nutrition"
    if any(w in text_lower for w in ["supplement", "vitamin", "creatine"]):
        return "supplements"
    if any(w in text_lower for w in ["pain", "hurt", "sore", "stiff"]):
        return "pain"
    if any(w in text_lower for w in ["weight", "weigh"]):
        return "weight"
    
    return None
```

---

### 3.4 Integration in Voice Bridge

**File:** `atlas/voice/bridge_file_server.py`

At initialization:
```python
from atlas.voice.session_buffer import SessionBuffer, extract_topic

class VoiceBridge:
    def __init__(self, ...):
        ...
        self.session_buffer = SessionBuffer()
```

In `process_audio()`, **before LLM routing**:
```python
# Inject session context for LLM queries
if not response_text:  # No intent matched, will go to LLM
    session_context = self.session_buffer.get_context()
    if session_context:
        # Prepend to system prompt or user message
        enhanced_prompt = f"Recent conversation:\n{session_context}\n\nUser: {transcription.text}"
        # Use enhanced_prompt instead of raw transcription
```

**After generating response** (at end of process_audio):
```python
# Save to session buffer
topic = extract_topic(action_type, transcription.text)
self.session_buffer.add(
    user_input=transcription.text,
    response=response_text,
    intent_type=action_type,
    topic=topic
)
```

---

## Phase 4: Workout Completion with Smart Confirmation

### 4.1 Voice Patterns

```python
WORKOUT_COMPLETION_PATTERNS = [
    r"finished (?:my )?workout",
    r"completed (?:my )?workout",
    r"done (?:with )?(?:my )?workout",
    r"workout (?:done|complete|finished)",
    r"did (?:my )?(strength [ab]|cardio|mobility)",  # Explicit type
    r"did (?:a )?different workout",
    r"skipped (?:my )?workout",
    r"cut (?:the )?workout short",
]
```

---

### 4.2 Smart Confirmation Logic

The confirmation flow should trigger ONLY when:
1. Today's scheduled workout doesn't match what user said
2. There's a flag from sleep/HRV/pain that warrants checking in
3. User explicitly indicates something different ("did strength B instead")

```python
async def _handle_workout_completion(self, text: str) -> str:
    """Handle workout completion with smart confirmation."""
    from atlas.workout.service import WorkoutService
    from atlas.health.service import HealthService
    
    workout_service = WorkoutService()
    health_service = HealthService()
    
    # Get today's scheduled workout
    scheduled = workout_service.get_todays_workout()
    
    # Check for flags that warrant follow-up
    flags = health_service.get_todays_flags()  # Returns list of concerns
    
    # Check if user specified a different workout
    explicit_type = self._extract_workout_type(text)
    
    # Determine if we need confirmation
    needs_confirmation = False
    confirmation_reason = None
    
    if "skipped" in text.lower():
        return await self._handle_skipped_workout(text)
    
    if "cut" in text.lower() or "short" in text.lower():
        needs_confirmation = True
        confirmation_reason = "partial"
    
    if explicit_type and explicit_type != scheduled.workout_type:
        needs_confirmation = True
        confirmation_reason = "different_workout"
    
    if scheduled.is_rest_day:
        needs_confirmation = True
        confirmation_reason = "rest_day_override"
    
    # Check for health flags that warrant a check-in
    if flags:
        # Don't require confirmation, but ask about specific concern
        flag_question = self._generate_flag_question(flags[0])
        workout_service.log_completed(
            workout_type=explicit_type or scheduled.workout_type,
            prescribed=explicit_type is None,
            completed_fully="short" not in text.lower(),
        )
        return f"Logged {explicit_type or scheduled.workout_type}. {flag_question}"
    
    if needs_confirmation:
        # Store pending state and ask
        self._pending_workout = {
            "explicit_type": explicit_type,
            "scheduled": scheduled,
            "reason": confirmation_reason,
        }
        
        if confirmation_reason == "partial":
            return "Got it. What did you cut short or skip?"
        elif confirmation_reason == "different_workout":
            return f"Logging {explicit_type} instead of scheduled {scheduled.workout_type}. Any notes?"
        elif confirmation_reason == "rest_day_override":
            return "Today was scheduled as rest. What did you do?"
    
    # Standard completion - no confirmation needed
    workout_service.log_completed(
        workout_type=scheduled.workout_type,
        prescribed=True,
        completed_fully=True,
    )
    return f"{scheduled.workout_type} logged. How'd you feel?"

def _generate_flag_question(self, flag: dict) -> str:
    """Generate contextual follow-up based on health flag."""
    flag_type = flag.get("type")
    
    if flag_type == "low_sleep":
        return "You were short on sleep - energy hold up okay?"
    elif flag_type == "elevated_rhr":
        return "Your heart rate was elevated this morning - how are you feeling?"
    elif flag_type == "pain":
        body_part = flag.get("body_part", "that area")
        return f"How did your {body_part} feel during the workout?"
    elif flag_type == "low_hrv":
        return "Your recovery markers were down - any unusual fatigue?"
    else:
        return "Any notes?"
```

---

### 4.3 Notes Capture Flow

When ATLAS asks "Any notes?" or "How'd you feel?", the next utterance should be captured as workout notes:

```python
# In process_audio(), check for pending workout notes
if self._pending_workout_notes:
    workout_id = self._pending_workout_notes
    self._pending_workout_notes = None
    
    # The current transcription is the notes
    workout_service.add_notes(workout_id, transcription.text)
    return f"Added notes to your workout log."
```

---

## Phase 5: RHR Baseline Auto-Calculation

### 5.1 Initial Hardcode

For now, set Alexander's baseline:

```python
# atlas/health/config.py
RHR_BASELINE = 52  # Alexander's current baseline

# After 14 days of data, this should switch to:
# RHR_BASELINE = None  # Triggers auto-calculation
```

### 5.2 Auto-Calculation Function

```python
def get_rhr_baseline(days: int = 14) -> Optional[float]:
    """Calculate RHR baseline from rolling average."""
    from atlas.health.service import HealthService
    
    service = HealthService()
    metrics = service.get_daily_metrics(days=days)
    
    if len(metrics) < 7:
        # Not enough data, use hardcoded
        return RHR_BASELINE
    
    rhr_values = [m.resting_hr for m in metrics if m.resting_hr]
    
    if len(rhr_values) < 7:
        return RHR_BASELINE
    
    return sum(rhr_values) / len(rhr_values)
```

### 5.3 Elevated RHR Check

```python
def is_rhr_elevated(current_rhr: float, baseline: float = None) -> bool:
    """Check if current RHR is elevated (>10% above baseline)."""
    baseline = baseline or get_rhr_baseline()
    
    if baseline is None:
        return False  # Can't determine
    
    threshold = baseline * 1.10  # 10% elevation
    return current_rhr > threshold
```

---

## Verification Checklist

After each phase, run these checks:

### Phase 0 Verification
```bash
# HRV status fix
atlas health status  # Should show HRV status, not None

# Body battery storage
sqlite3 ~/.atlas/atlas.db "SELECT body_battery FROM daily_metrics ORDER BY date DESC LIMIT 1"

# Insufficient data default
# Temporarily clear Garmin data, run health status, should show RED

# Token permissions
ls -la ~/.atlas/garmin_*  # Should be -rw-------
```

### Phase 1 Verification (Pain)
```bash
# Voice test
"shoulder is at a 4"  # Should log and respond
"pain status"  # Should show recent pain

# DB check
sqlite3 ~/.atlas/atlas.db "SELECT * FROM pain_log ORDER BY created_at DESC LIMIT 5"
```

### Phase 2 Verification (Supplements)
```bash
# Individual first (collision test)
"took my morning vitamin d"  # Should log Vitamin D, NOT morning batch

# Batch
"took my morning supps"  # Should log all morning supplements

# Status
"supplement check"  # Should show completion percentage
```

### Phase 3 Verification (Session Buffer)
```bash
# Contextual reference
"how did I sleep?"  # Wait for response
"was that better than yesterday?"  # Should understand "that" = sleep

# DB check
sqlite3 ~/.atlas/atlas.db "SELECT * FROM session_buffer ORDER BY created_at DESC LIMIT 5"
```

### Phase 4 Verification (Workout)
```bash
# Standard completion
"finished my workout"  # Should log and ask about flags if present

# Different workout
"did strength B instead"  # Should acknowledge the swap

# With notes
"finished my workout, shoulder felt tight"  # Should capture notes
```

---

## Post-Implementation: Connect Baseline Assessments

The `baseline_assessments` and `gate_assessments` tables are NOT orphaned - they're required for the protocol Alexander attached.

### Schema Needed

```sql
CREATE TABLE IF NOT EXISTS baseline_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_date DATE NOT NULL,
    session_type TEXT NOT NULL,  -- 'A', 'B', 'C'
    
    -- Session A: Body Comp
    weight_kg REAL,
    body_fat_pct REAL,
    waist_cm REAL,
    hip_cm REAL,
    
    -- Session A: Mobility
    wblt_right_cm REAL,
    wblt_left_cm REAL,
    sit_reach_cm REAL,
    
    -- Session A: Balance
    single_leg_balance_right_s INTEGER,
    single_leg_balance_left_s INTEGER,
    
    -- Session B: Strength
    goblet_squat_1rm_kg REAL,
    floor_press_1rm_kg REAL,
    pushups_max INTEGER,
    plank_seconds INTEGER,
    
    -- Session C: Cardio
    zone2_avg_hr INTEGER,
    step_test_recovery_hr INTEGER,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gate_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_number INTEGER NOT NULL,  -- 1, 2, 3, 4
    assessment_date DATE NOT NULL,
    passed BOOLEAN,
    
    -- GATE 1 specific criteria
    wblt_asymmetry_cm REAL,  -- Target: <2cm
    heel_raise_lsi_pct REAL,  -- Target: ≥90%
    single_leg_balance_60s BOOLEAN,
    pain_free_hops BOOLEAN,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Voice Intents for Baselines (Future)

```python
BASELINE_PATTERNS = [
    r"log baseline[:\s]+(.*)",
    r"record (?:my )?(wblt|sit.?reach|plank|pushups?)",
    r"baseline (status|check)",
]
```

This can be Phase 6 after core voice intents work.

---

## Summary: Execution Order

| Phase | Effort | Dependency | Verification |
|-------|--------|------------|--------------|
| 0: Bug fixes | 30 min | None | Health status shows HRV |
| 1: Pain voice | 1-2 hr | Phase 0 | "shoulder at 4" works |
| 2: Supplement voice | 1-2 hr | Phase 0 | "took morning supps" works |
| 3: Session buffer | 1-2 hr | None | "was that better" works |
| 4: Workout completion | 2-3 hr | Phase 3 | Smart confirmation works |
| 5: RHR auto-calc | 30 min | Phase 0 | After 14 days of data |
| 6: Baseline assessments | Future | Phase 1-4 | Protocol entry works |

---

## Questions for Alexander During Implementation

If you encounter ambiguity:

1. **Pain body part not recognized** - Should unknown body parts be logged anyway, or rejected?
   - Recommendation: Log with warning "I logged 'elbow' but it's not in your tracked areas"

2. **Supplement timing edge cases** - If it's 11am and user says "morning supps", warn or just log?
   - Recommendation: Log silently, track `logged_at` for drift analysis

3. **Workout notes length** - Cap at X characters or allow unlimited?
   - Recommendation: Cap at 500 chars for voice (prevents accidental novel-length captures)

4. **Session buffer TTL** - 10 minutes right? Or should morning routine get longer (30 min)?
   - Recommendation: Start with 10, make configurable

---

*Document Version: 1.0*
*Created: January 2026*
*Authors: Opus Web + Opus CLI synthesis*
