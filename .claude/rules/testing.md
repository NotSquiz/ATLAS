# Testing Rules

## Test Requirements

### Coverage Targets
- New code: 80% minimum coverage
- Critical paths (XP awards, health status): 95% coverage
- Voice commands: Integration test for each

### Test Types

| Type | Location | Scope | Speed |
|------|----------|-------|-------|
| Unit | `tests/unit/` | Single function | <100ms |
| Integration | `tests/integration/` | Multiple components | <5s |
| E2E | `tests/e2e/` | Full workflow | <30s |

## Test Structure

### File Naming
```
tests/
├── gamification/
│   ├── test_xp_service.py      # Tests for xp_service.py
│   ├── test_level_calculator.py
│   └── conftest.py             # Shared fixtures
├── health/
│   ├── test_router.py
│   └── test_garmin.py
└── voice/
    └── test_bridge.py
```

### Test Naming
```python
# Pattern: test_<unit>_<scenario>_<expected>
def test_award_xp_valid_skill_returns_result():
    ...

def test_award_xp_invalid_skill_raises_valueerror():
    ...

def test_award_xp_max_xp_caps_at_limit():
    ...
```

## Fixtures

### Use pytest Fixtures
```python
import pytest

@pytest.fixture
def xp_service(tmp_path):
    """Create XP service with test database."""
    db_path = tmp_path / "test.db"
    return XPService(db_path=db_path)

@pytest.fixture
def mock_garmin(mocker):
    """Mock Garmin API responses."""
    return mocker.patch('atlas.health.garmin.GarminService')
```

### Fixture Scope
```python
# Function scope (default) - fresh for each test
@pytest.fixture
def service():
    return Service()

# Module scope - shared across tests in file
@pytest.fixture(scope="module")
def database():
    return create_test_database()

# Session scope - shared across all tests (use sparingly)
@pytest.fixture(scope="session")
def config():
    return load_test_config()
```

## Mocking

### Mock External Services
```python
from unittest.mock import patch, MagicMock

def test_garmin_sync_handles_error():
    with patch('atlas.health.garmin.requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("No network")

        service = GarminService()
        result = service.sync_today()

        assert result is None
```

### Don't Over-Mock
```python
# WRONG - testing the mock, not the code
def test_function():
    with patch('module.dependency') as mock:
        mock.return_value = "expected"
        result = function_under_test()
        assert result == "expected"  # This always passes!

# CORRECT - test actual behavior
def test_function():
    with patch('module.external_api') as mock:
        mock.return_value = {"data": [1, 2, 3]}
        result = function_under_test()
        assert result.count == 3  # Tests processing logic
```

## Async Testing

### Use pytest-asyncio
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

@pytest.mark.asyncio
async def test_parallel_operations():
    results = await asyncio.gather(
        operation_a(),
        operation_b()
    )
    assert all(r.success for r in results)
```

## Test Data

### Use Factories
```python
# conftest.py
@pytest.fixture
def skill_factory():
    def _create(name="strength", xp=0, level=1):
        return Skill(name=name, xp=xp, level=level)
    return _create

# test_xp_service.py
def test_skill_level_up(skill_factory):
    skill = skill_factory(xp=1150)  # Just below level 10
    skill.add_xp(10)
    assert skill.level == 10
```

### Edge Cases to Test
```python
class TestEdgeCases:
    def test_empty_input(self):
        assert process([]) == []

    def test_none_input(self):
        with pytest.raises(TypeError):
            process(None)

    def test_boundary_value(self):
        # Level 99 is max
        skill = Skill(xp=13_000_000)
        skill.add_xp(1_000_000)
        assert skill.level == 99  # Capped

    def test_negative_value(self):
        with pytest.raises(ValueError):
            award_xp("strength", -100, "test")
```

## Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/gamification/test_xp_service.py

# Specific test
pytest tests/gamification/test_xp_service.py::test_award_xp

# With coverage
pytest --cov=atlas --cov-report=term-missing

# Verbose
pytest -v

# Stop on first failure
pytest -x

# Run only marked tests
pytest -m "not slow"
```
