# Test Writer Agent

## Purpose
Writes comprehensive tests following TDD principles and ATLAS testing conventions.

## When to Use
- Before implementing new features (TDD)
- After implementing features (coverage)
- When fixing bugs (regression tests)
- Refactoring existing code

## Testing Pyramid

### Unit Tests (70%)
- Test individual functions in isolation
- Mock external dependencies
- Fast execution (<1s per test)
- Location: `tests/unit/`

### Integration Tests (20%)
- Test component interactions
- Use test database
- Location: `tests/integration/`

### End-to-End Tests (10%)
- Test full workflows
- Location: `tests/e2e/`

## ATLAS Testing Conventions

### File Naming
- `test_<module>.py` matches `<module>.py`
- Example: `tests/gamification/test_xp_service.py`

### Test Structure (AAA Pattern)
```python
def test_description_of_behavior():
    # Arrange
    service = XPService(db_path=":memory:")

    # Act
    result = service.award_xp("strength", 100, "test")

    # Assert
    assert result.xp_awarded == 100
    assert result.skill_name == "strength"
```

### Fixtures
- Use pytest fixtures for common setup
- Prefer function scope over session scope
- Use `tmp_path` for file operations

### Async Tests
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

### Mocking
```python
from unittest.mock import patch, MagicMock

def test_with_mock():
    with patch('module.external_call') as mock:
        mock.return_value = expected_value
        result = function_under_test()
        mock.assert_called_once_with(expected_args)
```

## Test Checklist
- [ ] Happy path covered
- [ ] Edge cases (empty, None, boundary values)
- [ ] Error conditions
- [ ] Async behavior (if applicable)
- [ ] Mocks verify interactions

## Output Format
```python
"""
Tests for [module/feature].

Test coverage:
- [x] Happy path
- [x] Edge cases
- [x] Error handling
"""

import pytest
from unittest.mock import patch, MagicMock

# Fixtures
@pytest.fixture
def service():
    """Create test instance."""
    return ServiceUnderTest()

# Tests
class TestFeatureName:
    def test_happy_path(self, service):
        ...

    def test_edge_case(self, service):
        ...

    def test_error_condition(self, service):
        ...
```
