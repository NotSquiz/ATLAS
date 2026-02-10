"""Shared fixtures for activity conversion pipeline tests."""

import pytest

from atlas.pipelines.activity_conversion import ActivityConversionPipeline


@pytest.fixture
def pipeline(monkeypatch):
    """Pipeline with all heavy deps stubbed.

    Uses object.__new__ to bypass __init__ entirely, then sets
    the required attributes manually. This avoids fragile constructor
    patching and ensures tests only exercise the method under test.
    """
    p = object.__new__(ActivityConversionPipeline)

    # Set required data attributes (normally set in __init__)
    p.raw_activities = {}
    p.conversion_map = {}
    p.progress_data = {}

    return p
