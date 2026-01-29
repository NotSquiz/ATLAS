# ATLAS Garmin Integration Technical Brief

## Context for CLI Agent

Alexander is building ATLAS, a personal "Life Operating System" with voice-first interaction. This component handles automated sleep data ingestion from a Garmin Forerunner 165 Music to inform daily exercise planning decisions.

**Owner's Tech Stack:**
- SQLite with vector embeddings for memory/storage
- Python-based pipelines
- Hybrid LLM architecture (local Qwen, Haiku, Claude)
- Running on personal infrastructure (Sunshine Coast, Australia - AEST timezone)

---

## Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY SLEEP → EXERCISE PIPELINE              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [5:00 AM AEST Trigger]                                         │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐                                            │
│  │ Garmin Auth     │ ← Uses saved session tokens                │
│  │ (garth library) │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Pull Sleep Data │ ← Previous night's sleep metrics           │
│  │ from Garmin API │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Ingest & Store  │ ← SQLite: raw JSON + parsed metrics        │
│  │ in ATLAS DB     │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Analysis Hook   │ ← LLM or rule-based decision engine        │
│  │ (Sleep Quality) │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ Exercise Plan   │ ← Output: today's recommended workout      │
│  │ Recommendation  │                                            │
│  └─────────────────┘                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Garmin Authentication Setup

### Library Choice: `garth`

Use `garth` (not `python-garminconnect`) — it's more actively maintained and handles OAuth better.

```bash
pip install garth
```

### Initial Authentication (One-Time Manual Setup)

Create `garmin_auth_setup.py`:

```python
import garth
from pathlib import Path

GARTH_HOME = Path.home() / ".garth"

def initial_login():
    """Run once manually to establish session tokens."""
    email = input("Garmin email: ")
    password = input("Garmin password: ")
    
    garth.login(email, password)
    garth.save(GARTH_HOME)
    
    print(f"✓ Session saved to {GARTH_HOME}")
    print("Tokens will auto-refresh on subsequent uses.")

if __name__ == "__main__":
    initial_login()
```

**Important Notes:**
- Run this interactively ONCE to generate tokens
- Tokens persist in `~/.garth/` directory
- `garth` handles token refresh automatically on subsequent loads
- If auth breaks (Garmin changes something), re-run manual login

### Loading Saved Session (For Automated Runs)

```python
import garth
from pathlib import Path

GARTH_HOME = Path.home() / ".garth"

def load_garmin_session():
    """Load existing session for automated pipeline."""
    try:
        garth.resume(GARTH_HOME)
        # Test the session is valid
        garth.connectapi("/userprofile-service/socialProfile")
        return True
    except Exception as e:
        print(f"✗ Garmin auth failed: {e}")
        return False
```

---

## Part 2: Sleep Data Retrieval

### Primary Sleep Endpoint

```python
from datetime import date, timedelta

def get_sleep_data(target_date: date = None) -> dict:
    """
    Fetch sleep data for a specific date.
    
    Args:
        target_date: The date to fetch (defaults to last night)
    
    Returns:
        Raw sleep data dict from Garmin
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    date_str = target_date.isoformat()
    
    # Primary sleep endpoint
    sleep_data = garth.connectapi(
        f"/sleep-service/sleep/{date_str}"
    )
    
    return sleep_data
```

### Key Sleep Metrics to Extract

The Garmin sleep response contains nested data. Here are the fields Alexander likely cares about:

```python
def parse_sleep_metrics(raw_sleep: dict) -> dict:
    """Extract actionable metrics from raw Garmin sleep data."""
    
    daily_sleep = raw_sleep.get("dailySleepDTO", {})
    
    metrics = {
        # Core duration metrics (in seconds)
        "total_sleep_seconds": daily_sleep.get("sleepTimeSeconds"),
        "deep_sleep_seconds": daily_sleep.get("deepSleepSeconds"),
        "light_sleep_seconds": daily_sleep.get("lightSleepSeconds"),
        "rem_sleep_seconds": daily_sleep.get("remSleepSeconds"),
        "awake_seconds": daily_sleep.get("awakeSleepSeconds"),
        
        # Quality indicators
        "sleep_score": daily_sleep.get("sleepScores", {}).get("overall", {}).get("value"),
        "sleep_quality_score": daily_sleep.get("sleepScores", {}).get("qualityScore", {}).get("value"),
        "recovery_score": daily_sleep.get("sleepScores", {}).get("recoveryScore", {}).get("value"),
        "restfulness_score": daily_sleep.get("sleepScores", {}).get("restfulnessScore", {}).get("value"),
        
        # Timing
        "sleep_start": daily_sleep.get("sleepStartTimestampGMT"),
        "sleep_end": daily_sleep.get("sleepEndTimestampGMT"),
        
        # Body metrics during sleep
        "avg_hrv": daily_sleep.get("avgOvernightHrv"),
        "resting_hr": daily_sleep.get("restingHeartRate"),
        "avg_respiration": daily_sleep.get("avgSleepRespirationValue"),
        "avg_spo2": daily_sleep.get("avgSleepSpo2"),
        
        # Raw for storage
        "_raw": raw_sleep
    }
    
    # Calculate derived metrics
    total = metrics["total_sleep_seconds"] or 0
    if total > 0:
        metrics["deep_sleep_pct"] = (metrics["deep_sleep_seconds"] or 0) / total
        metrics["rem_sleep_pct"] = (metrics["rem_sleep_seconds"] or 0) / total
        metrics["sleep_efficiency"] = total / (total + (metrics["awake_seconds"] or 0))
    
    return metrics
```

### Additional Useful Endpoints

```python
# Yesterday's HRV status (may have more detail than sleep endpoint)
hrv_data = garth.connectapi(f"/hrv-service/hrv/{date_str}")

# Body Battery (useful for recovery assessment)
body_battery = garth.connectapi(f"/wellness-service/wellness/bodyBattery/daily/{date_str}")

# Stress data
stress = garth.connectapi(f"/wellness-service/wellness/dailyStress/{date_str}")

# User summary (steps, calories, etc. from previous day)
daily_summary = garth.connectapi(f"/usersummary-service/usersummary/daily/{date_str}")
```

---

## Part 3: Data Storage Schema

Suggested SQLite schema for sleep data:

```sql
CREATE TABLE IF NOT EXISTS garmin_sleep (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,  -- ISO format YYYY-MM-DD
    
    -- Core metrics
    total_sleep_seconds INTEGER,
    deep_sleep_seconds INTEGER,
    light_sleep_seconds INTEGER,
    rem_sleep_seconds INTEGER,
    awake_seconds INTEGER,
    
    -- Scores (0-100 scale typically)
    sleep_score INTEGER,
    recovery_score INTEGER,
    restfulness_score INTEGER,
    
    -- Body metrics
    avg_hrv REAL,
    resting_hr INTEGER,
    avg_respiration REAL,
    avg_spo2 REAL,
    
    -- Derived
    deep_sleep_pct REAL,
    rem_sleep_pct REAL,
    sleep_efficiency REAL,
    
    -- Timestamps
    sleep_start TEXT,
    sleep_end TEXT,
    
    -- Raw JSON for future parsing needs
    raw_json TEXT,
    
    -- Metadata
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sleep_date ON garmin_sleep(date);
```

---

## Part 4: Exercise Decision Logic

### Suggested Decision Framework

```python
from enum import Enum
from dataclasses import dataclass

class ExerciseIntensity(Enum):
    REST = "rest"
    RECOVERY = "recovery"      # Light stretching, walking
    ZONE_2 = "zone_2"          # Easy aerobic (bike/walk)
    MODERATE = "moderate"      # Standard workout
    INTENSE = "intense"        # High intensity training

@dataclass
class SleepAssessment:
    quality: str  # "poor", "fair", "good", "excellent"
    total_hours: float
    deep_sleep_adequate: bool
    hrv_status: str  # "low", "normal", "elevated"
    recommendation: ExerciseIntensity
    reasoning: str

def assess_sleep_for_exercise(metrics: dict) -> SleepAssessment:
    """
    Rule-based assessment of sleep quality for exercise planning.
    
    Alexander's context: 
    - 38yo male
    - Interested in Zone 2 training
    - Following Bryan Johnson-style optimization
    """
    
    total_hours = (metrics.get("total_sleep_seconds") or 0) / 3600
    sleep_score = metrics.get("sleep_score") or 0
    deep_pct = metrics.get("deep_sleep_pct") or 0
    hrv = metrics.get("avg_hrv")
    
    # Assess quality tier
    if sleep_score >= 85 and total_hours >= 7:
        quality = "excellent"
    elif sleep_score >= 70 and total_hours >= 6:
        quality = "good"
    elif sleep_score >= 50 and total_hours >= 5:
        quality = "fair"
    else:
        quality = "poor"
    
    # Deep sleep check (target: >15% of total sleep)
    deep_adequate = deep_pct >= 0.15
    
    # HRV assessment (this needs baseline calibration over time)
    # Placeholder logic - should compare to personal rolling average
    if hrv is None:
        hrv_status = "unknown"
    elif hrv < 30:
        hrv_status = "low"
    elif hrv > 60:
        hrv_status = "elevated"
    else:
        hrv_status = "normal"
    
    # Decision matrix
    if quality == "poor" or hrv_status == "low":
        recommendation = ExerciseIntensity.REST
        reasoning = "Poor recovery indicators. Prioritize rest today."
    elif quality == "fair" or not deep_adequate:
        recommendation = ExerciseIntensity.RECOVERY
        reasoning = "Suboptimal sleep. Light movement only."
    elif quality == "good":
        recommendation = ExerciseIntensity.ZONE_2
        reasoning = "Adequate recovery. Good day for Zone 2 cardio."
    else:  # excellent
        recommendation = ExerciseIntensity.MODERATE
        reasoning = "Excellent recovery. Full training capacity available."
    
    return SleepAssessment(
        quality=quality,
        total_hours=round(total_hours, 1),
        deep_sleep_adequate=deep_adequate,
        hrv_status=hrv_status,
        recommendation=recommendation,
        reasoning=reasoning
    )
```

### LLM-Enhanced Decision (Optional Hook)

For more nuanced decisions, pass context to Claude:

```python
def get_llm_exercise_recommendation(metrics: dict, recent_history: list[dict]) -> str:
    """
    Use LLM for nuanced exercise recommendation.
    
    Args:
        metrics: Today's sleep metrics
        recent_history: Last 7 days of sleep + exercise data
    """
    
    prompt = f"""Based on the following sleep data, recommend today's exercise plan.

Last Night's Sleep:
- Total: {metrics['total_sleep_seconds']/3600:.1f} hours
- Sleep Score: {metrics['sleep_score']}/100
- Deep Sleep: {metrics['deep_sleep_pct']*100:.0f}%
- REM: {metrics['rem_sleep_pct']*100:.0f}%
- HRV: {metrics['avg_hrv']}
- Resting HR: {metrics['resting_hr']} bpm

Recent 7-Day Context:
{format_recent_history(recent_history)}

User Context:
- 38yo male, interested in longevity optimization
- Primary goal: Zone 2 cardiovascular training
- Has access to: exercise bike, bodyweight exercises, walking

Provide a specific recommendation with:
1. Recommended activity type
2. Duration
3. Target heart rate zone (if applicable)
4. Brief reasoning
"""
    
    # Call your preferred LLM here
    # response = call_atlas_llm(prompt)
    # return response
```

---

## Part 5: Scheduler Setup

### Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add line for 5:00 AM AEST daily
# Note: Server timezone must be AEST, or adjust accordingly
0 5 * * * /path/to/venv/bin/python /path/to/atlas/garmin_morning_pipeline.py >> /path/to/logs/garmin.log 2>&1
```

### Python Scheduler Alternative (For Process-Based Systems)

```python
import schedule
import time
from datetime import datetime

def run_morning_pipeline():
    """Main pipeline entry point."""
    print(f"[{datetime.now()}] Starting Garmin morning pipeline...")
    
    # 1. Auth
    if not load_garmin_session():
        send_alert("Garmin auth failed - manual intervention needed")
        return
    
    # 2. Fetch
    raw_sleep = get_sleep_data()
    if not raw_sleep:
        send_alert("No sleep data returned from Garmin")
        return
    
    # 3. Parse
    metrics = parse_sleep_metrics(raw_sleep)
    
    # 4. Store
    store_sleep_data(metrics)
    
    # 5. Analyze
    assessment = assess_sleep_for_exercise(metrics)
    
    # 6. Output/Notify
    notify_exercise_recommendation(assessment)
    
    print(f"[{datetime.now()}] Pipeline complete. Recommendation: {assessment.recommendation.value}")

# Schedule for 5 AM
schedule.every().day.at("05:00").do(run_morning_pipeline)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
```

---

## Part 6: Testing Strategy

### Test 1: Authentication Validation

```python
def test_garmin_auth():
    """Verify saved credentials work."""
    garth.resume(GARTH_HOME)
    profile = garth.connectapi("/userprofile-service/socialProfile")
    assert "displayName" in profile
    print(f"✓ Auth valid for user: {profile.get('displayName')}")
```

### Test 2: Sleep Data Structure

```python
def test_sleep_data_structure():
    """Verify sleep endpoint returns expected fields."""
    garth.resume(GARTH_HOME)
    
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)
    
    sleep = get_sleep_data(yesterday)
    
    # Check key fields exist
    assert "dailySleepDTO" in sleep, "Missing dailySleepDTO"
    daily = sleep["dailySleepDTO"]
    
    required_fields = ["sleepTimeSeconds", "deepSleepSeconds", "sleepScores"]
    for field in required_fields:
        assert field in daily, f"Missing required field: {field}"
    
    print("✓ Sleep data structure valid")
    print(f"  Total sleep: {daily['sleepTimeSeconds']/3600:.1f} hours")
```

### Test 3: Database Write/Read

```python
def test_database_roundtrip():
    """Verify data persists correctly."""
    test_metrics = {
        "date": "2026-01-10",
        "total_sleep_seconds": 25200,  # 7 hours
        "sleep_score": 82,
        # ... other fields
    }
    
    store_sleep_data(test_metrics)
    retrieved = get_sleep_by_date("2026-01-10")
    
    assert retrieved["sleep_score"] == 82
    print("✓ Database roundtrip successful")
```

### Test 4: Decision Logic

```python
def test_exercise_decisions():
    """Verify decision logic produces expected outputs."""
    
    # Poor sleep scenario
    poor_metrics = {
        "total_sleep_seconds": 14400,  # 4 hours
        "sleep_score": 35,
        "deep_sleep_pct": 0.10,
        "avg_hrv": 25
    }
    result = assess_sleep_for_exercise(poor_metrics)
    assert result.recommendation == ExerciseIntensity.REST
    
    # Good sleep scenario
    good_metrics = {
        "total_sleep_seconds": 27000,  # 7.5 hours
        "sleep_score": 78,
        "deep_sleep_pct": 0.18,
        "avg_hrv": 45
    }
    result = assess_sleep_for_exercise(good_metrics)
    assert result.recommendation in [ExerciseIntensity.ZONE_2, ExerciseIntensity.MODERATE]
    
    print("✓ Decision logic tests passed")
```

### Test 5: End-to-End Dry Run

```python
def test_full_pipeline_dry_run():
    """Run complete pipeline without side effects."""
    
    # Auth
    assert load_garmin_session(), "Auth failed"
    
    # Fetch (use yesterday to ensure data exists)
    raw = get_sleep_data()
    assert raw, "No data returned"
    
    # Parse
    metrics = parse_sleep_metrics(raw)
    assert metrics["total_sleep_seconds"] > 0, "Invalid sleep duration"
    
    # Analyze
    assessment = assess_sleep_for_exercise(metrics)
    
    print("✓ Full pipeline dry run successful")
    print(f"  Sleep: {assessment.total_hours}h ({assessment.quality})")
    print(f"  Recommendation: {assessment.recommendation.value}")
    print(f"  Reasoning: {assessment.reasoning}")
```

---

## Part 7: Error Handling & Monitoring

### Common Failure Modes

| Issue | Detection | Recovery |
|-------|-----------|----------|
| Token expiry | `garth.exceptions.GarthHTTPError` | Re-run manual auth script |
| Garmin API down | Connection timeout | Retry with backoff, alert if persists |
| No sleep data | Empty response or null fields | Check watch was worn; skip day |
| Rate limiting | 429 response | Back off; reduce polling frequency |
| Schema changes | KeyError on parsing | Log raw response; update parser |

### Robust Fetch Wrapper

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=5):
    """Decorator for retrying failed API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    print(f"Attempt {attempt+1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def fetch_sleep_with_retry(target_date):
    return get_sleep_data(target_date)
```

---

## Part 8: File Structure Suggestion

```
atlas/
├── integrations/
│   └── garmin/
│       ├── __init__.py
│       ├── auth.py           # Authentication handling
│       ├── client.py         # API wrapper functions
│       ├── models.py         # Data classes and enums
│       ├── parser.py         # Raw response parsing
│       └── setup_auth.py     # One-time manual auth script
├── pipelines/
│   └── morning_sleep.py      # Main daily pipeline
├── skills/
│   └── exercise_planner.py   # Decision logic / LLM hooks
├── storage/
│   ├── schema.sql
│   └── db.py                 # Database operations
├── tests/
│   └── test_garmin.py
└── config/
    └── settings.py           # Paths, thresholds, etc.
```

---

## Quick Start Checklist

1. [ ] Install garth: `pip install garth`
2. [ ] Run manual auth setup script (once)
3. [ ] Verify auth with test script
4. [ ] Create SQLite database with schema
5. [ ] Test sleep data fetch for yesterday
6. [ ] Implement parsing and storage
7. [ ] Build decision logic
8. [ ] Set up cron job for 5 AM
9. [ ] Add logging and alerting
10. [ ] Monitor for first week; adjust thresholds

---

## Tips & Gotchas

1. **Watch sync timing**: Data won't appear until watch syncs to phone. If Alexander sleeps late and checks immediately at 5 AM, last night's data may not be available yet. Consider a retry mechanism or later trigger time.

2. **HRV baselines**: HRV is highly individual. The decision logic should build a personal baseline over 2-4 weeks before making HRV-based recommendations.

3. **Weekend considerations**: Sleep patterns differ on weekends. Consider day-of-week adjustments.

4. **Garmin API stability**: This is unofficial. Subscribe to garth GitHub issues for breaking changes.

5. **Rate limits**: Don't poll more than a few times per day. Garmin may lock accounts that appear to be scraping.

6. **Timezone handling**: Garmin returns timestamps in GMT. Convert to AEST for display/logic.

---

*Document prepared for Alexander's ATLAS project. Direct questions to the main conversation thread.*
