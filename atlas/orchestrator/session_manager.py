"""
ATLAS Session Manager

Manages context across skill executions using the "git diff pattern" from Claude Agent SDK masterclass.

Architecture:
    - Sessions persist state to JSON files at ~/.atlas/sessions/
    - Git context provides minimal diff-based state for context reloading
    - Scratch data stores intermediate values during skill chains

Key Insight from Claude Agent SDK Masterclass:
    [4575s] "You can use git diff as your state reload pattern"
    [4583s] "Persist state to files, reload minimal context"

Usage:
    # Programmatic
    from atlas.orchestrator.session_manager import get_session_manager

    sm = get_session_manager()
    session_id = await sm.start_session(repo="babybrains")
    sm.add_to_scratch("key", "value")
    sm.record_skill("script_writer")
    await sm.save_state()

    # CLI
    python -m atlas.orchestrator.session_manager --start --repo babybrains
    python -m atlas.orchestrator.session_manager --list
    python -m atlas.orchestrator.session_manager --resume <session_id>
    python -m atlas.orchestrator.session_manager --git-context --path /path/to/repo
    python -m atlas.orchestrator.session_manager --cleanup --days 7
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
import json
import logging
import re
import shutil
import subprocess
import threading
import uuid

logger = logging.getLogger(__name__)


DEFAULT_SESSION_DIR = Path.home() / ".atlas" / "sessions"


def _now_utc_iso() -> str:
    """Get current time as UTC ISO format string."""
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_datetime(iso_str: str) -> datetime:
    """Parse ISO format datetime string."""
    return datetime.fromisoformat(iso_str)


@dataclass
class SessionState:
    """Persistent session state."""
    session_id: str
    created_at: str  # ISO format UTC
    last_active: str  # ISO format UTC
    repo: Optional[str] = None
    skill_chain: list[str] = field(default_factory=list)
    scratch_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Create SessionState from dictionary."""
        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            last_active=data["last_active"],
            repo=data.get("repo"),
            skill_chain=data.get("skill_chain", []),
            scratch_data=data.get("scratch_data", {}),
        )


@dataclass
class GitContext:
    """Git repository context from git status/diff."""
    files_modified: list[str] = field(default_factory=list)
    files_added: list[str] = field(default_factory=list)
    files_deleted: list[str] = field(default_factory=list)
    summary: str = ""
    is_clean: bool = True

    @classmethod
    def empty(cls) -> "GitContext":
        """Create empty GitContext for non-git directories or errors."""
        return cls(summary="No git context available")


class SessionManager:
    """
    Manage context across skill executions.

    Uses the "git diff pattern" from Claude Agent SDK masterclass:
    - Persist state to files for recovery
    - Use git diff for minimal context reload
    - Track skill chains and scratch data
    """

    def __init__(self, session_dir: Optional[Path] = None):
        """
        Initialize SessionManager.

        Args:
            session_dir: Directory for session files (default: ~/.atlas/sessions)
        """
        self.session_dir = session_dir or DEFAULT_SESSION_DIR
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self._current_state: Optional[SessionState] = None

    def _sanitize_session_id(self, session_id: str) -> Optional[str]:
        """
        Sanitize session ID to prevent path traversal.

        Args:
            session_id: Raw session ID string

        Returns:
            Sanitized session ID or None if invalid
        """
        if not session_id:
            return None
        # Reject path separators and parent directory references
        if "/" in session_id or "\\" in session_id or ".." in session_id:
            return None
        # Only allow alphanumeric, dash, underscore
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            return None
        return session_id

    def _session_path(self, session_id: str) -> Path:
        """Get file path for a session ID."""
        return self.session_dir / f"{session_id}.json"

    async def start_session(self, repo: Optional[str] = None) -> str:
        """
        Start a new session.

        Args:
            repo: Optional repository name to associate with session

        Returns:
            New session ID
        """
        session_id = str(uuid.uuid4())
        now = _now_utc_iso()

        self._current_state = SessionState(
            session_id=session_id,
            created_at=now,
            last_active=now,
            repo=repo,
            skill_chain=[],
            scratch_data={},
        )
        self.current_session_id = session_id

        # Persist immediately
        if not await self.save_state():
            # Log warning but still return ID - state is in memory
            logger.warning(f"Failed to persist session {session_id}")

        return session_id

    async def load_session(self, session_id: str) -> Optional[SessionState]:
        """
        Load a session from file.

        Args:
            session_id: Session ID to load

        Returns:
            SessionState if found and valid, None otherwise
        """
        safe_id = self._sanitize_session_id(session_id)
        if not safe_id:
            return None

        session_path = self._session_path(safe_id)
        if not session_path.exists():
            return None

        try:
            data = json.loads(session_path.read_text())
            state = SessionState.from_dict(data)
            self._current_state = state
            self.current_session_id = state.session_id
            return state
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Corrupted file - return None, don't crash
            logger.warning(f"Failed to load session {session_id}: {e}")
            return None

    async def save_state(self) -> bool:
        """
        Save current session state to file.

        Returns:
            True if saved successfully, False otherwise
        """
        if not self._current_state:
            return False

        # Update last_active timestamp
        self._current_state.last_active = _now_utc_iso()

        session_path = self._session_path(self._current_state.session_id)
        try:
            session_path.write_text(json.dumps(self._current_state.to_dict(), indent=2))
            return True
        except OSError as e:
            logger.error(f"Failed to save session state to {session_path}: {e}")
            return False

    async def get_git_context(self, repo_path: Optional[Path] = None) -> GitContext:
        """
        Get git context for a repository.

        Uses git status --porcelain for reliable parsing.

        Args:
            repo_path: Path to git repository (default: current directory)

        Returns:
            GitContext with file changes, or empty context on error
        """
        cwd = str(repo_path) if repo_path else None

        # Check if git is available
        if not shutil.which("git"):
            return GitContext.empty()

        # Check if directory is a git repo
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )
            if result.returncode != 0:
                return GitContext(summary="Not a git repository", is_clean=True)
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.debug(f"Git rev-parse failed: {e}")
            return GitContext.empty()

        # Get git status --porcelain
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            )
            if result.returncode != 0:
                return GitContext.empty()
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.debug(f"Git status failed: {e}")
            return GitContext.empty()

        # Parse porcelain output
        files_modified = []
        files_added = []
        files_deleted = []

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            # Porcelain format: XY filename
            # X = index status, Y = worktree status
            status = line[:2]
            filename = line[3:].strip()

            # Handle renamed files (R  old -> new) - only split for rename status
            if status.startswith("R") and " -> " in filename:
                filename = filename.split(" -> ")[1]

            # Categorize by status
            if status in ("M ", " M", "MM"):
                files_modified.append(filename)
            elif status in ("A ", "AM", "??"):
                files_added.append(filename)
            elif status in ("D ", " D"):
                files_deleted.append(filename)
            elif status.startswith("R"):
                files_modified.append(filename)

        is_clean = not (files_modified or files_added or files_deleted)

        # Generate summary
        parts = []
        if files_modified:
            parts.append(f"{len(files_modified)} modified")
        if files_added:
            parts.append(f"{len(files_added)} added")
        if files_deleted:
            parts.append(f"{len(files_deleted)} deleted")
        summary = ", ".join(parts) if parts else "Working tree clean"

        return GitContext(
            files_modified=files_modified,
            files_added=files_added,
            files_deleted=files_deleted,
            summary=summary,
            is_clean=is_clean,
        )

    async def clear_and_resume(self) -> dict:
        """
        Get minimal context for resuming after context clear.

        Returns:
            Dict with session_state and git_context for context reload
        """
        result = {
            "session_state": None,
            "git_context": None,
        }

        if self._current_state:
            result["session_state"] = {
                "session_id": self._current_state.session_id,
                "repo": self._current_state.repo,
                "skill_chain": self._current_state.skill_chain,
                "scratch_data": self._current_state.scratch_data,
            }

            # Get git context for repo if set
            if self._current_state.repo:
                # Try common repo locations (use home-relative path only)
                for base in [Path.home() / "code"]:
                    repo_path = base / self._current_state.repo
                    if repo_path.exists():
                        git_ctx = await self.get_git_context(repo_path)
                        result["git_context"] = {
                            "files_modified": git_ctx.files_modified,
                            "files_added": git_ctx.files_added,
                            "files_deleted": git_ctx.files_deleted,
                            "summary": git_ctx.summary,
                            "is_clean": git_ctx.is_clean,
                        }
                        break
                else:
                    # No repo found, get context for current directory
                    git_ctx = await self.get_git_context()
                    result["git_context"] = {
                        "files_modified": git_ctx.files_modified,
                        "files_added": git_ctx.files_added,
                        "files_deleted": git_ctx.files_deleted,
                        "summary": git_ctx.summary,
                        "is_clean": git_ctx.is_clean,
                    }

        return result

    def add_to_scratch(self, key: str, value: Any) -> bool:
        """
        Add a key-value pair to scratch data.

        Args:
            key: Key to store under
            value: Value to store (must be JSON serializable)

        Returns:
            True if added successfully, False if value not JSON-serializable or no session
        """
        if self._current_state:
            try:
                json.dumps(value)  # Test serializability
                self._current_state.scratch_data[key] = value
                return True
            except (TypeError, ValueError):
                logger.warning(f"Value for key '{key}' is not JSON-serializable")
                return False
        return False

    def get_from_scratch(self, key: str, default: Any = None) -> Any:
        """
        Get a value from scratch data.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Value if found, default otherwise
        """
        if self._current_state:
            return self._current_state.scratch_data.get(key, default)
        return default

    def record_skill(self, skill_name: str) -> None:
        """
        Record a skill execution in the skill chain.

        Args:
            skill_name: Name of skill that was executed
        """
        if self._current_state:
            self._current_state.skill_chain.append(skill_name)

    async def end_session(self) -> bool:
        """
        End the current session.

        Saves state and clears current session tracking.

        Returns:
            True if session was ended, False if no active session
        """
        if not self._current_state:
            return False

        if not await self.save_state():
            logger.warning(f"Failed to save final state for session {self.current_session_id}")
        self.current_session_id = None
        self._current_state = None
        return True

    def list_sessions(self, repo: Optional[str] = None) -> list[str]:
        """
        List all session IDs, optionally filtered by repo.

        Args:
            repo: Optional repo name to filter by

        Returns:
            List of session IDs
        """
        sessions = []

        for session_file in self.session_dir.glob("*.json"):
            session_id = session_file.stem

            if repo:
                # Filter by repo - need to read file
                try:
                    data = json.loads(session_file.read_text())
                    if data.get("repo") == repo:
                        sessions.append(session_id)
                except (json.JSONDecodeError, OSError) as e:
                    logger.debug(f"Skipping unreadable session file {session_file}: {e}")
                    continue
            else:
                sessions.append(session_id)

        return sessions

    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        Delete sessions older than max_age_days.

        Args:
            max_age_days: Maximum age in days before deletion

        Returns:
            Number of sessions deleted
        """
        deleted = 0
        now = datetime.now(timezone.utc)

        for session_file in self.session_dir.glob("*.json"):
            try:
                data = json.loads(session_file.read_text())
                last_active = _parse_iso_datetime(data.get("last_active", data.get("created_at", "")))

                # Make timezone-aware if needed
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)

                age = now - last_active
                if age.days > max_age_days:
                    session_file.unlink()
                    deleted += 1
            except (json.JSONDecodeError, OSError, ValueError, KeyError) as e:
                # Skip corrupted or invalid files
                logger.debug(f"Skipping invalid session file during cleanup {session_file}: {e}")
                continue

        return deleted


# Singleton instance with thread-safe access
_session_manager_instance: Optional[SessionManager] = None
_session_manager_lock = threading.Lock()


def get_session_manager() -> SessionManager:
    """
    Get or create singleton SessionManager instance.

    Thread-safe singleton pattern using double-checked locking.

    Returns:
        SessionManager singleton
    """
    global _session_manager_instance
    if _session_manager_instance is None:
        with _session_manager_lock:
            if _session_manager_instance is None:
                _session_manager_instance = SessionManager()
    return _session_manager_instance


# CLI entry point
if __name__ == "__main__":
    import argparse
    import asyncio
    import sys

    def print_session_state(state: SessionState) -> None:
        """Print session state in readable format."""
        print(json.dumps(state.to_dict(), indent=2))

    def print_git_context(ctx: GitContext) -> None:
        """Print git context in readable format."""
        print(f"Summary: {ctx.summary}")
        print(f"Is Clean: {ctx.is_clean}")
        if ctx.files_modified:
            print(f"Modified ({len(ctx.files_modified)}):")
            for f in ctx.files_modified:
                print(f"  M {f}")
        if ctx.files_added:
            print(f"Added ({len(ctx.files_added)}):")
            for f in ctx.files_added:
                print(f"  A {f}")
        if ctx.files_deleted:
            print(f"Deleted ({len(ctx.files_deleted)}):")
            for f in ctx.files_deleted:
                print(f"  D {f}")

    async def main():
        parser = argparse.ArgumentParser(
            description="ATLAS Session Manager",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Start a new session
  python -m atlas.orchestrator.session_manager --start --repo babybrains

  # List all sessions
  python -m atlas.orchestrator.session_manager --list
  python -m atlas.orchestrator.session_manager --list --repo babybrains

  # Resume/display a session
  python -m atlas.orchestrator.session_manager --resume <session_id>

  # Get git context
  python -m atlas.orchestrator.session_manager --git-context
  python -m atlas.orchestrator.session_manager --git-context --path /home/squiz/code/babybrains-os

  # Cleanup old sessions
  python -m atlas.orchestrator.session_manager --cleanup --days 7
"""
        )

        # Mutually exclusive action group
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--start", action="store_true", help="Start a new session")
        action.add_argument("--resume", metavar="ID", help="Load and display a session")
        action.add_argument("--list", action="store_true", help="List session IDs")
        action.add_argument("--git-context", action="store_true", help="Get git context")
        action.add_argument("--cleanup", action="store_true", help="Delete old sessions")

        # Optional arguments
        parser.add_argument("--repo", help="Repository name (for --start, --list)")
        parser.add_argument("--path", help="Repository path (for --git-context)")
        parser.add_argument("--days", type=int, default=30, help="Max age in days (for --cleanup)")

        args = parser.parse_args()

        sm = get_session_manager()

        if args.start:
            session_id = await sm.start_session(repo=args.repo)
            print(f"Started session: {session_id}")
            if args.repo:
                print(f"Repository: {args.repo}")

        elif args.resume:
            state = await sm.load_session(args.resume)
            if state:
                print_session_state(state)
            else:
                print(f"Error: Could not load session '{args.resume}'", file=sys.stderr)
                print("Session may not exist or file may be corrupted.", file=sys.stderr)
                sys.exit(1)

        elif args.list:
            sessions = sm.list_sessions(repo=args.repo)
            if sessions:
                if args.repo:
                    print(f"Sessions for repo '{args.repo}':")
                else:
                    print("All sessions:")
                for sid in sessions:
                    print(f"  {sid}")
                print(f"\nTotal: {len(sessions)}")
            else:
                print("No sessions found.")

        elif args.git_context:
            repo_path = Path(args.path) if args.path else None
            ctx = await sm.get_git_context(repo_path)
            print_git_context(ctx)

        elif args.cleanup:
            deleted = await sm.cleanup_old_sessions(max_age_days=args.days)
            print(f"Deleted {deleted} session(s) older than {args.days} days.")

    asyncio.run(main())
