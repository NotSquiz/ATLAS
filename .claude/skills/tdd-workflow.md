# TDD Workflow

## Overview
Test-Driven Development workflow for ATLAS project. Write tests first, then implement.

## The TDD Cycle

### 1. RED - Write Failing Test
```bash
# Create test file first
tests/<module>/test_<feature>.py
```

Write a test that:
- Describes the desired behavior
- Fails because feature doesn't exist yet
- Is minimal but complete

### 2. GREEN - Make It Pass
Write the minimum code to make the test pass:
- No premature optimization
- No extra features
- Just enough to pass

### 3. REFACTOR - Clean Up
With passing tests as safety net:
- Remove duplication
- Improve naming
- Extract methods/classes
- Maintain test coverage

## ATLAS TDD Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/gamification/test_xp_service.py

# Run with coverage
pytest --cov=atlas --cov-report=term-missing

# Run tests matching pattern
pytest -k "test_award"

# Run in watch mode (requires pytest-watch)
ptw tests/
```

## Test File Template

```python
"""
Tests for <module>.<feature>.

TDD Status:
- [x] Test written
- [ ] Implementation complete
- [ ] Refactoring done
"""

import pytest
from <module> import FeatureUnderTest


class TestFeatureName:
    """Tests for FeatureName behavior."""

    @pytest.fixture
    def feature(self):
        """Create test instance."""
        return FeatureUnderTest()

    def test_should_do_expected_behavior(self, feature):
        """Feature should [expected behavior]."""
        # Arrange
        input_data = ...

        # Act
        result = feature.method(input_data)

        # Assert
        assert result == expected_output

    def test_should_handle_edge_case(self, feature):
        """Feature should handle [edge case]."""
        ...

    def test_should_raise_on_invalid_input(self, feature):
        """Feature should raise ValueError for invalid input."""
        with pytest.raises(ValueError):
            feature.method(invalid_input)
```

## When to Skip TDD

TDD is valuable but not always practical:
- Exploratory prototyping
- UI/visual work
- Integration with external APIs (use integration tests after)

In these cases, write tests immediately after implementation.
