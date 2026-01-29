# Coding Style Rules

## Python Style

### Imports
```python
# Standard library
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Third party
import pytest
from anthropic import Anthropic

# Local
from atlas.gamification import get_xp_service
from atlas.health.router import TrafficLightRouter
```

### Line Length
- Max 100 characters (not 80, not unlimited)
- Break long lines at logical points

### Naming
```python
# Variables: snake_case
user_name = "squiz"
xp_awarded = 100

# Functions: snake_case
def calculate_level(xp: int) -> int:
    ...

# Classes: PascalCase
class XPService:
    ...

# Constants: SCREAMING_SNAKE_CASE
MAX_LEVEL = 99
XP_TABLE = {...}

# Private: leading underscore
def _internal_helper():
    ...
```

### String Formatting
```python
# Prefer f-strings
message = f"Awarded {xp} XP to {skill}"

# For complex formatting
message = "{skill} is now level {level}".format(
    skill=skill_name.title(),
    level=new_level
)

# Never use % formatting
message = "Awarded %d XP" % xp  # WRONG
```

### Collections
```python
# List comprehensions for simple transforms
squares = [x**2 for x in range(10)]

# Generator expressions for large data
total = sum(x**2 for x in range(10000))

# Use dict/set comprehensions
skills = {s.name: s.level for s in all_skills}

# Don't over-nest
# WRONG
result = [x for x in [y for y in data if y > 0] if x < 100]
# CORRECT
filtered = [y for y in data if y > 0]
result = [x for x in filtered if x < 100]
```

## Async Patterns

### Async Functions
```python
# Mark I/O functions as async
async def fetch_data() -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Use asyncio.gather for parallel operations
async def get_all_metrics():
    sleep, hrv, battery = await asyncio.gather(
        get_sleep(),
        get_hrv(),
        get_battery()
    )
    return Metrics(sleep, hrv, battery)
```

### Sync Wrappers
```python
# When async function must be called from sync context
import asyncio

def sync_wrapper():
    return asyncio.run(async_function())
```

## Error Handling

### Exception Hierarchy
```python
# Most specific first
try:
    result = await risky_operation()
except ConnectionTimeout:
    # Handle timeout specifically
    return cached_result
except ConnectionError:
    # Handle connection issues
    raise ServiceUnavailable()
except ValueError as e:
    # Handle bad input
    logger.warning(f"Invalid input: {e}")
    return None
except Exception:
    # Last resort
    logger.exception("Unexpected error")
    raise
```

### Custom Exceptions
```python
class ATLASError(Exception):
    """Base exception for ATLAS."""
    pass

class GarminSyncError(ATLASError):
    """Garmin synchronization failed."""
    pass

class XPAwardError(ATLASError):
    """XP award operation failed."""
    pass
```

## Data Classes

### Prefer dataclasses
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Skill:
    name: str
    xp: int
    level: int
    domain: str = "body"

    @property
    def progress(self) -> float:
        """Progress to next level as percentage."""
        return calculate_progress(self.xp)
```

### Immutable When Possible
```python
@dataclass(frozen=True)
class HealthStatus:
    traffic_light: str
    body_battery: int
    hrv_status: str
```

## Comments

### When to Comment
```python
# Explain WHY, not WHAT
# WRONG
x = x + 1  # Increment x

# CORRECT
# Compensate for 0-based indexing in OSRS level formula
x = x + 1
```

### Docstrings
```python
def complex_function(data: list, threshold: float = 0.5) -> dict:
    """
    Process data using threshold-based filtering.

    Uses the modified OSRS algorithm for level calculations.
    See: docs/OSRS_DESIGN_SYSTEM.md

    Args:
        data: List of skill records to process
        threshold: Minimum confidence level (0.0-1.0)

    Returns:
        Dictionary mapping skill names to calculated levels

    Raises:
        ValueError: If threshold is outside valid range
    """
    ...
```
