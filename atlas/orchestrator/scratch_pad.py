"""
ATLAS Scratch Pad

Track intermediate state during skill chains with structured entries,
timestamps, and context-reload summaries.

Architecture:
    - ScratchEntry: Individual entry with key, value, step, timestamp
    - ScratchPad: Collection of entries for a session
    - File persistence to ~/.atlas/scratch/

Use Case: When executing a skill chain like ingest -> plan -> draft_21s -> qc,
each step produces outputs that the next step needs. ScratchPad tracks these
intermediate results so they can be:
    1. Resumed after context clearing
    2. Summarized for debugging
    3. Persisted to files for recovery

Usage:
    # Programmatic
    from atlas.orchestrator.scratch_pad import ScratchPad

    pad = ScratchPad(session_id="babybrains_20260108_143022")
    pad.add("ingest_output", {"domain": "sleep", ...}, step=1, skill_name="ingest")
    pad.add("plan_result", {"segments": [...]}, step=2, skill_name="plan")

    # Get summary for context reload
    summary = pad.get_summary()

    # Persist to file
    pad.to_file(Path("~/.atlas/scratch/session_123.json"))

    # Load from file
    pad = ScratchPad.from_file(Path("~/.atlas/scratch/session_123.json"))

    # CLI
    python -m atlas.orchestrator.scratch_pad --session test123 --add key=value --step 1
    python -m atlas.orchestrator.scratch_pad --session test123 --summary
    python -m atlas.orchestrator.scratch_pad --session test123 --json
    python -m atlas.orchestrator.scratch_pad --session test123 --clear
    python -m atlas.orchestrator.scratch_pad --load /path/to/scratch.json --summary

Note: This module is NOT thread-safe. Concurrent access from multiple threads
requires external synchronization.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import json
import logging
import re

logger = logging.getLogger(__name__)

DEFAULT_SCRATCH_DIR = Path.home() / ".atlas" / "scratch"


def _now_utc() -> datetime:
    """Get current time as timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def _sanitize_session_id(session_id: str) -> Optional[str]:
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
        logger.warning(f"Invalid session_id (contains path separators): {session_id}")
        return None
    # Only allow alphanumeric, dash, underscore
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        logger.warning(f"Invalid session_id (invalid characters): {session_id}")
        return None
    return session_id


@dataclass
class ScratchEntry:
    """A single entry in the scratch pad."""

    key: str                    # Identifier (e.g., "ingest_output", "plan_result")
    value: Any                  # The stored value (must be JSON-serializable)
    step: int                   # Step number in skill chain (1-indexed, 0 for pre-chain)
    timestamp: datetime         # When entry was created (UTC)
    skill_name: Optional[str] = None  # Which skill produced this (if any)
    metadata: dict = field(default_factory=dict)  # Optional extra info

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "skill_name": self.skill_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScratchEntry":
        """Create from dictionary."""
        timestamp_str = data["timestamp"]
        # Parse ISO format, handling timezone
        timestamp = datetime.fromisoformat(timestamp_str)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return cls(
            key=data["key"],
            value=data["value"],
            step=data["step"],
            timestamp=timestamp,
            skill_name=data.get("skill_name"),
            metadata=data.get("metadata", {}),
        )


class ScratchPad:
    """
    Track intermediate state during skill chains.

    Provides structured storage with step tracking, timestamps,
    and context-reload summaries.

    Usage:
        pad = ScratchPad(session_id="babybrains_20260108_143022")
        pad.add("ingest_output", {"domain": "sleep", ...}, step=1, skill_name="ingest")
        pad.add("plan_result", {"segments": [...]}, step=2, skill_name="plan")

        # Get summary for context reload
        summary = pad.get_summary()

        # Persist to file
        pad.to_file(Path("~/.atlas/scratch/session_123.json"))

        # Load from file
        pad = ScratchPad.from_file(Path("~/.atlas/scratch/session_123.json"))
    """

    def __init__(self, session_id: str):
        """Initialize scratch pad for a session."""
        self.session_id = session_id
        self.entries: list[ScratchEntry] = []
        self.created_at: datetime = _now_utc()
        self._current_step: int = 0

    def add(
        self,
        key: str,
        value: Any,
        step: Optional[int] = None,
        skill_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Add entry to scratch pad.

        Args:
            key: Identifier for this entry
            value: Value to store (must be JSON-serializable)
            step: Step number (auto-increments if None)
            skill_name: Which skill produced this
            metadata: Optional extra info

        Returns:
            True if added, False if value not serializable or invalid step
        """
        # Validate step
        if step is not None and step < 0:
            logger.warning(f"Negative step number rejected: {step}")
            return False

        # Determine step number
        if step is None:
            self._current_step += 1
            step = self._current_step
        else:
            # Update current step if provided step is higher
            if step > self._current_step:
                self._current_step = step

        # Verify JSON-serializability
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            logger.warning(f"Value for '{key}' not JSON-serializable: {e}")
            return False

        entry = ScratchEntry(
            key=key,
            value=value,
            step=step,
            timestamp=_now_utc(),
            skill_name=skill_name,
            metadata=metadata or {},
        )
        self.entries.append(entry)
        logger.debug(f"Added entry: {key} (step {step})")
        return True

    def get(self, key: str, default: Any = None) -> Any:
        """Get most recent value for key."""
        # Iterate in reverse to find most recent
        for entry in reversed(self.entries):
            if entry.key == key:
                return entry.value
        return default

    def get_by_step(self, step: int) -> list[ScratchEntry]:
        """Get all entries for a specific step."""
        return [e for e in self.entries if e.step == step]

    def get_by_skill(self, skill_name: str) -> list[ScratchEntry]:
        """Get all entries produced by a specific skill."""
        return [e for e in self.entries if e.skill_name == skill_name]

    def get_latest(self, n: int = 5) -> list[ScratchEntry]:
        """Get the n most recent entries."""
        return self.entries[-n:] if n > 0 else []

    def get_summary(self, max_value_chars: int = 200) -> str:
        """
        Get human-readable summary for context reload.

        Format:
        ```
        ScratchPad: session_123 (5 entries, 3 steps)

        Step 1 (ingest):
          - ingest_output: {"domain": "sleep", "age_band": "12-18m"...}

        Step 2 (plan):
          - plan_result: {"segments": [{"id": 1, "beat": "MEET"...}

        Step 3 (draft_21s):
          - draft_output: {"draft_id": "abc123", "word_count": 62...}
        ```
        """
        if not self.entries:
            return f"ScratchPad: {self.session_id} (empty)"

        # Group entries by step
        steps: dict[int, list[ScratchEntry]] = {}
        for entry in self.entries:
            if entry.step not in steps:
                steps[entry.step] = []
            steps[entry.step].append(entry)

        step_count = len(steps)
        entry_count = len(self.entries)

        lines = [f"ScratchPad: {self.session_id} ({entry_count} entries, {step_count} steps)"]
        lines.append("")

        for step_num in sorted(steps.keys()):
            step_entries = steps[step_num]
            # Get skill name from first entry with one
            skill = None
            for e in step_entries:
                if e.skill_name:
                    skill = e.skill_name
                    break

            if skill:
                lines.append(f"Step {step_num} ({skill}):")
            else:
                lines.append(f"Step {step_num}:")

            for entry in step_entries:
                # Format value with truncation
                try:
                    value_str = json.dumps(entry.value)
                except (TypeError, ValueError):
                    value_str = str(entry.value)

                if len(value_str) > max_value_chars:
                    value_str = value_str[:max_value_chars] + "..."

                lines.append(f"  - {entry.key}: {value_str}")

            lines.append("")

        return "\n".join(lines).rstrip()

    def get_context_dict(self) -> dict:
        """
        Get minimal dict for injecting into LLM context.

        Returns: {
            "session_id": str,
            "step_count": int,
            "entry_count": int,
            "latest_entries": [{"key": str, "step": int, "skill": str}, ...]
        }
        """
        # Get unique step count
        unique_steps = set(e.step for e in self.entries)

        # Get latest entries summary
        latest = self.get_latest(5)
        latest_entries = [
            {
                "key": e.key,
                "step": e.step,
                "skill": e.skill_name,
            }
            for e in latest
        ]

        return {
            "session_id": self.session_id,
            "step_count": len(unique_steps),
            "entry_count": len(self.entries),
            "latest_entries": latest_entries,
        }

    def clear(self) -> int:
        """Clear all entries. Returns count cleared."""
        count = len(self.entries)
        self.entries.clear()
        self._current_step = 0
        logger.debug(f"Cleared {count} entries from scratch pad")
        return count

    def clear_before_step(self, step: int) -> int:
        """Clear entries before a step (for recovery). Returns count cleared."""
        original_count = len(self.entries)
        self.entries = [e for e in self.entries if e.step >= step]
        cleared = original_count - len(self.entries)
        logger.debug(f"Cleared {cleared} entries before step {step}")
        return cleared

    def to_dict(self) -> dict:
        """Convert entire scratch pad to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "current_step": self._current_step,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScratchPad":
        """Create scratch pad from dictionary."""
        pad = cls(session_id=data["session_id"])

        # Parse created_at
        created_at_str = data.get("created_at")
        if created_at_str:
            created_at = datetime.fromisoformat(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            pad.created_at = created_at

        pad._current_step = data.get("current_step", 0)

        # Parse entries
        for entry_data in data.get("entries", []):
            entry = ScratchEntry.from_dict(entry_data)
            pad.entries.append(entry)

        return pad

    def to_file(self, path: Path) -> bool:
        """
        Save scratch pad to JSON file.

        Returns: True if saved, False on error
        """
        try:
            # Expand user path and ensure parent directory exists
            path = Path(path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(json.dumps(self.to_dict(), indent=2))
            logger.debug(f"Saved scratch pad to {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to save scratch pad to {path}: {e}")
            return False

    @classmethod
    def from_file(cls, path: Path) -> Optional["ScratchPad"]:
        """
        Load scratch pad from JSON file.

        Returns: ScratchPad instance or None if file not found/invalid
        """
        path = Path(path).expanduser()

        if not path.exists():
            logger.debug(f"Scratch pad file not found: {path}")
            return None

        try:
            data = json.loads(path.read_text())
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in scratch pad file {path}: {e}")
            return None
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Invalid scratch pad data in {path}: {e}")
            return None
        except OSError as e:
            logger.warning(f"Failed to read scratch pad file {path}: {e}")
            return None

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)

    def __bool__(self) -> bool:
        """Return True if has entries."""
        return len(self.entries) > 0


def get_scratch_pad(session_id: str) -> ScratchPad:
    """
    Get or create scratch pad for session.

    Loads from default scratch directory if file exists,
    otherwise creates a new scratch pad.

    Args:
        session_id: Session identifier

    Returns:
        ScratchPad instance (existing or new)
    """
    safe_id = _sanitize_session_id(session_id)
    if not safe_id:
        logger.warning(f"Invalid session_id, creating with sanitized version")
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', session_id)

    scratch_file = DEFAULT_SCRATCH_DIR / f"{safe_id}.json"

    if scratch_file.exists():
        pad = ScratchPad.from_file(scratch_file)
        if pad is not None:
            return pad
        # File exists but invalid, create new
        logger.warning(f"Invalid scratch file, creating new pad for {safe_id}")

    return ScratchPad(session_id=safe_id)


# CLI entry point
if __name__ == "__main__":
    import argparse
    import sys

    def parse_key_value(kv_string: str) -> tuple[str, Any]:
        """Parse key=value string, attempting JSON parse for value."""
        if "=" not in kv_string:
            return kv_string, True  # Flag-style: key with no value

        key, value_str = kv_string.split("=", 1)

        # Try to parse value as JSON
        try:
            value = json.loads(value_str)
        except json.JSONDecodeError:
            # Treat as string
            value = value_str

        return key, value

    def main() -> int:
        parser = argparse.ArgumentParser(
            description="ATLAS Scratch Pad",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Create new scratch pad and add entry
  python -m atlas.orchestrator.scratch_pad --session test123 --add key=value --step 1

  # Add JSON value
  python -m atlas.orchestrator.scratch_pad --session test123 --add 'data={"name":"test"}' --step 2

  # View scratch pad summary
  python -m atlas.orchestrator.scratch_pad --session test123 --summary

  # View as JSON
  python -m atlas.orchestrator.scratch_pad --session test123 --json

  # Clear scratch pad
  python -m atlas.orchestrator.scratch_pad --session test123 --clear

  # Load from file
  python -m atlas.orchestrator.scratch_pad --load /path/to/scratch.json --summary
"""
        )

        # Session or load (mutually exclusive source)
        source = parser.add_mutually_exclusive_group()
        source.add_argument("--session", help="Session ID to work with")
        source.add_argument("--load", metavar="PATH", help="Load scratch pad from file")

        # Actions
        parser.add_argument("--add", metavar="KEY=VALUE", help="Add entry (key=value format)")
        parser.add_argument("--step", type=int, help="Step number for --add")
        parser.add_argument("--skill", help="Skill name for --add")
        parser.add_argument("--summary", action="store_true", help="Display summary")
        parser.add_argument("--json", action="store_true", dest="as_json", help="Display as JSON")
        parser.add_argument("--clear", action="store_true", help="Clear all entries")
        parser.add_argument("--save", metavar="PATH", help="Save scratch pad to file")

        args = parser.parse_args()

        # Validate source
        if not args.session and not args.load:
            # Check if any action requires a source
            if args.add or args.summary or args.as_json or args.clear or args.save:
                print("Error: --session or --load required", file=sys.stderr)
                return 1
            parser.print_help()
            return 0

        # Load or create scratch pad
        if args.load:
            path = Path(args.load).expanduser()
            pad = ScratchPad.from_file(path)
            if pad is None:
                print(f"Error: Could not load scratch pad from {path}", file=sys.stderr)
                return 1
        else:
            pad = get_scratch_pad(args.session)

        # Process actions
        modified = False

        if args.add:
            key, value = parse_key_value(args.add)
            success = pad.add(
                key=key,
                value=value,
                step=args.step,
                skill_name=args.skill,
            )
            if success:
                print(f"Added: {key}")
                modified = True
            else:
                print(f"Error: Failed to add entry '{key}'", file=sys.stderr)
                return 1

        if args.clear:
            count = pad.clear()
            print(f"Cleared {count} entries")
            modified = True

        if args.summary:
            print(pad.get_summary())

        if args.as_json:
            print(json.dumps(pad.to_dict(), indent=2))

        # Save if modified
        if modified:
            if args.save:
                save_path = Path(args.save).expanduser()
            elif args.session:
                save_path = DEFAULT_SCRATCH_DIR / f"{args.session}.json"
            else:
                # Loaded from file, save back to same file
                save_path = Path(args.load).expanduser()

            if not pad.to_file(save_path):
                print(f"Error: Failed to save scratch pad to {save_path}", file=sys.stderr)
                return 1

        return 0

    sys.exit(main())
