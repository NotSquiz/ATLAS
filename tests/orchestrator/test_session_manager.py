"""Tests for session_manager.py - ATLAS Session Manager basics."""
import pytest
import asyncio
import tempfile
from pathlib import Path


class TestSessionManagerInstantiation:
    """Test SessionManager can be instantiated."""

    def test_can_instantiate(self):
        """SessionManager should be instantiable."""
        from atlas.orchestrator.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SessionManager(session_dir=Path(tmpdir))
            assert sm is not None

    def test_default_session_dir(self):
        """SessionManager should use default session dir when not specified."""
        from atlas.orchestrator.session_manager import SessionManager, DEFAULT_SESSION_DIR

        sm = SessionManager()
        assert sm.session_dir == DEFAULT_SESSION_DIR

    def test_custom_session_dir(self):
        """SessionManager should accept custom session dir."""
        from atlas.orchestrator.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_sessions"
            sm = SessionManager(session_dir=custom_dir)
            assert sm.session_dir == custom_dir
            assert custom_dir.exists()  # Should create the directory

    def test_no_current_session_initially(self):
        """SessionManager should have no current session after instantiation."""
        from atlas.orchestrator.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SessionManager(session_dir=Path(tmpdir))
            assert sm.current_session_id is None


class TestStartSession:
    """Test start_session() returns session_id."""

    def test_returns_session_id(self):
        """start_session() should return a session_id string."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                session_id = await sm.start_session()
                assert session_id is not None
                assert isinstance(session_id, str)
                assert len(session_id) > 0

        asyncio.run(run_test())

    def test_returns_uuid_format(self):
        """start_session() should return a UUID format string."""
        from atlas.orchestrator.session_manager import SessionManager
        import uuid

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                session_id = await sm.start_session()
                # Should be a valid UUID
                uuid.UUID(session_id)  # Will raise if invalid

        asyncio.run(run_test())

    def test_sets_current_session_id(self):
        """start_session() should set current_session_id."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                session_id = await sm.start_session()
                assert sm.current_session_id == session_id

        asyncio.run(run_test())

    def test_creates_session_file(self):
        """start_session() should persist session to file."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                session_id = await sm.start_session()
                session_file = Path(tmpdir) / f"{session_id}.json"
                assert session_file.exists()

        asyncio.run(run_test())

    def test_accepts_repo_parameter(self):
        """start_session() should accept optional repo parameter."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                session_id = await sm.start_session(repo="test-repo")
                assert session_id is not None
                # Load and verify repo was stored
                state = await sm.load_session(session_id)
                assert state.repo == "test-repo"

        asyncio.run(run_test())

    def test_multiple_sessions_unique_ids(self):
        """Multiple start_session() calls should return unique IDs."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                session_id1 = await sm.start_session()
                session_id2 = await sm.start_session()
                assert session_id1 != session_id2

        asyncio.run(run_test())


class TestSessionState:
    """Test SessionState dataclass."""

    def test_can_create(self):
        """SessionState should be creatable."""
        from atlas.orchestrator.session_manager import SessionState

        state = SessionState(
            session_id="test-id",
            created_at="2024-01-01T00:00:00Z",
            last_active="2024-01-01T00:00:00Z",
        )
        assert state.session_id == "test-id"
        assert state.skill_chain == []
        assert state.scratch_data == {}

    def test_to_dict(self):
        """SessionState.to_dict() should return dict."""
        from atlas.orchestrator.session_manager import SessionState

        state = SessionState(
            session_id="test-id",
            created_at="2024-01-01T00:00:00Z",
            last_active="2024-01-01T00:00:00Z",
            repo="test-repo",
        )
        d = state.to_dict()
        assert isinstance(d, dict)
        assert d["session_id"] == "test-id"
        assert d["repo"] == "test-repo"

    def test_from_dict(self):
        """SessionState.from_dict() should reconstruct state."""
        from atlas.orchestrator.session_manager import SessionState

        data = {
            "session_id": "test-id",
            "created_at": "2024-01-01T00:00:00Z",
            "last_active": "2024-01-01T00:00:00Z",
            "repo": "test-repo",
            "skill_chain": ["skill1", "skill2"],
            "scratch_data": {"key": "value"},
        }
        state = SessionState.from_dict(data)
        assert state.session_id == "test-id"
        assert state.repo == "test-repo"
        assert state.skill_chain == ["skill1", "skill2"]
        assert state.scratch_data == {"key": "value"}


class TestGetSessionManager:
    """Test get_session_manager() singleton function."""

    def test_returns_session_manager(self):
        """get_session_manager() should return a SessionManager."""
        from atlas.orchestrator.session_manager import get_session_manager, SessionManager

        sm = get_session_manager()
        assert isinstance(sm, SessionManager)

    def test_returns_same_instance(self):
        """get_session_manager() should return the same instance (singleton)."""
        from atlas.orchestrator.session_manager import get_session_manager

        sm1 = get_session_manager()
        sm2 = get_session_manager()
        assert sm1 is sm2


class TestGitContext:
    """Test GitContext dataclass."""

    def test_can_create(self):
        """GitContext should be creatable."""
        from atlas.orchestrator.session_manager import GitContext

        ctx = GitContext()
        assert ctx.files_modified == []
        assert ctx.files_added == []
        assert ctx.files_deleted == []
        assert ctx.is_clean is True

    def test_empty_factory(self):
        """GitContext.empty() should create empty context."""
        from atlas.orchestrator.session_manager import GitContext

        ctx = GitContext.empty()
        assert ctx.summary == "No git context available"


class TestScratchData:
    """Test scratch data functionality."""

    def test_add_to_scratch(self):
        """add_to_scratch() should store value."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                await sm.start_session()
                result = sm.add_to_scratch("key", "value")
                assert result is True

        asyncio.run(run_test())

    def test_get_from_scratch(self):
        """get_from_scratch() should retrieve value."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                await sm.start_session()
                sm.add_to_scratch("key", "value")
                value = sm.get_from_scratch("key")
                assert value == "value"

        asyncio.run(run_test())

    def test_get_from_scratch_default(self):
        """get_from_scratch() should return default for missing key."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                await sm.start_session()
                value = sm.get_from_scratch("missing", "default")
                assert value == "default"

        asyncio.run(run_test())

    def test_add_non_serializable_fails(self):
        """add_to_scratch() should fail for non-JSON-serializable values."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                await sm.start_session()
                # Lambda is not JSON-serializable
                result = sm.add_to_scratch("key", lambda x: x)
                assert result is False

        asyncio.run(run_test())


class TestRecordSkill:
    """Test skill chain recording."""

    def test_record_skill(self):
        """record_skill() should add to skill chain."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                await sm.start_session()
                sm.record_skill("skill1")
                sm.record_skill("skill2")
                assert sm._current_state.skill_chain == ["skill1", "skill2"]

        asyncio.run(run_test())


class TestListSessions:
    """Test list_sessions() functionality."""

    def test_list_sessions_empty(self):
        """list_sessions() should return empty list when no sessions."""
        from atlas.orchestrator.session_manager import SessionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            sm = SessionManager(session_dir=Path(tmpdir))
            sessions = sm.list_sessions()
            assert sessions == []

    def test_list_sessions_returns_ids(self):
        """list_sessions() should return session IDs."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                id1 = await sm.start_session()
                id2 = await sm.start_session()
                sessions = sm.list_sessions()
                assert id1 in sessions
                assert id2 in sessions

        asyncio.run(run_test())

    def test_list_sessions_filter_by_repo(self):
        """list_sessions() should filter by repo."""
        from atlas.orchestrator.session_manager import SessionManager

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                sm = SessionManager(session_dir=Path(tmpdir))
                id1 = await sm.start_session(repo="repo1")
                id2 = await sm.start_session(repo="repo2")

                sessions_repo1 = sm.list_sessions(repo="repo1")
                assert id1 in sessions_repo1
                assert id2 not in sessions_repo1

        asyncio.run(run_test())
