"""
Pytest configuration for UI tests.

Provides fixtures and utilities for testing UI state export
and gamification integration.
"""
import json
import pytest
from pathlib import Path


def get_bridge_dir() -> Path:
    """Get the bridge directory, handling WSL2 vs Windows paths."""
    # Try home directory path first (works in WSL2)
    home_path = Path.home() / ".atlas" / ".bridge"
    if home_path.exists():
        return home_path

    # Try project .bridge directory
    project_path = Path(__file__).parent.parent.parent / ".bridge"
    if project_path.exists():
        return project_path

    # Try UNC path (Windows accessing WSL)
    try:
        unc_path = Path(r"\\wsl$\Ubuntu\home\squiz\ATLAS\.bridge")
        if unc_path.exists():
            return unc_path
    except Exception:
        pass

    # Return home path even if it doesn't exist (tests will skip)
    return home_path


@pytest.fixture
def bridge_dir():
    """Get the bridge directory path."""
    return get_bridge_dir()


@pytest.fixture
def status_file(bridge_dir):
    """Get the session_status.json file path."""
    return bridge_dir / "session_status.json"


@pytest.fixture
def audio_log_file(bridge_dir):
    """Get the audio_events.jsonl file path."""
    return bridge_dir / "audio_events.jsonl"


@pytest.fixture
def db_path():
    """Get the database path."""
    return Path.home() / ".atlas" / "atlas.db"


@pytest.fixture
def clean_audio_log(audio_log_file):
    """Clear audio log before test."""
    if audio_log_file.exists():
        audio_log_file.write_text("")
    yield
    # Optionally clean up after test too


@pytest.fixture
def load_fixture():
    """Fixture loader for database states."""
    from tests.fixtures.db_states import load_fixture as _load_fixture
    return _load_fixture


@pytest.fixture
def trigger_level_up():
    """Level-up trigger for animation testing."""
    from tests.fixtures.db_states import trigger_level_up as _trigger
    return _trigger
