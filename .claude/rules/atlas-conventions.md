# ATLAS Project Conventions

## Core Principles

### 1. Voice-First Design
- Target <1.8s latency for voice responses
- 0-token responses where possible (cache hits)
- Fail gracefully - never leave user waiting

### 2. Fail-Safe Pattern
XP/gamification failures must NEVER break core health tracking.
```python
# CORRECT: Fail-safe wrapper
result = award_xp_safe("strength", 100, "workout_strength")
if result:
    # XP awarded
else:
    # XP failed, but health tracking continues
```

### 3. Async Everything
All I/O operations must be async.
```python
# CORRECT
async def get_status() -> HealthStatus:
    metrics = await garmin.sync_today()
    return HealthStatus(...)

# WRONG
def get_status() -> HealthStatus:
    metrics = garmin.sync_today()  # Blocking!
    return HealthStatus(...)
```

## Code Style

### Error Handling
```python
# CORRECT: Specific exceptions first
try:
    result = await operation()
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    return default_value
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

### Logging
Every new module MUST have logging.
```python
import logging

logger = logging.getLogger(__name__)

def do_something():
    logger.debug("Starting operation")
    logger.info("Operation complete")
    logger.warning("Unexpected state, continuing")
    logger.error("Operation failed")
```

### Type Hints
Function signatures require type hints.
```python
# CORRECT
def award_xp(skill: str, amount: int, source: str) -> XPAwardResult:
    ...

# WRONG
def award_xp(skill, amount, source):
    ...
```

### Docstrings
Public functions need docstrings.
```python
def calculate_lsi(affected: float, unaffected: float) -> float:
    """
    Calculate Limb Symmetry Index.

    Args:
        affected: Measurement from affected limb
        unaffected: Measurement from unaffected limb

    Returns:
        LSI as percentage (0-100+)

    Raises:
        ValueError: If unaffected is zero
    """
    ...
```

## File Organization

### Module Structure
```
atlas/<domain>/
├── __init__.py       # Public exports
├── service.py        # Main orchestration
├── models.py         # Data classes
├── cli.py            # Command-line interface
└── <specific>.py     # Domain-specific logic
```

### Test Structure
```
tests/<domain>/
├── __init__.py
├── test_service.py
├── test_models.py
└── conftest.py       # Shared fixtures
```

## Database Patterns

### Schema Location
- Main schema: `atlas/memory/schema.sql`
- Domain schemas: `atlas/memory/schema_<domain>.sql`

### Query Style
```python
# CORRECT: Parameterized queries
cursor = conn.execute(
    "SELECT * FROM skills WHERE name = ?",
    (skill_name,)
)

# WRONG: String interpolation (SQL injection risk)
cursor = conn.execute(
    f"SELECT * FROM skills WHERE name = '{skill_name}'"
)
```

## Voice Pipeline

### Intent Priority
Higher priority intents must be checked first.
```python
# Order matters - stateful sessions first
if self._active_assessment:
    return self._handle_assessment(text)
if self._active_workout:
    return self._handle_workout(text)
# Then pattern matching
if self._is_pain_log(text):
    return self._handle_pain(text)
```

### Response Format
Keep voice responses concise.
```python
# CORRECT: Brief, actionable
"GREEN. Battery 52. HRV balanced. Full workout today."

# WRONG: Verbose
"Your current status is GREEN. Your body battery is at 52 percent.
Your heart rate variability is showing a balanced reading.
You are cleared for a full intensity workout today."
```
