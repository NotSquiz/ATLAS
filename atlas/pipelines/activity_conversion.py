"""
Activity Conversion Pipeline Orchestrator (Quality Mode)

Converts raw Montessori activities to canonical Activity Atoms using:
- 5 chained skills (ingest -> research -> transform -> elevate -> validate)
- QC hook gate (check_activity_quality.py)
- Quality audit stage (Grade A required for human review)
- Intelligent retry with "Wait" pattern (89.3% blind spot reduction)
- Human review interface
- Progress tracking

Uses CLI mode (Max subscription) - no ANTHROPIC_API_KEY needed.

Usage:
    # Single activity (primary mode - no API key needed)
    python -m atlas.pipelines.activity_conversion --activity tummy-time

    # With explicit retry count
    python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 3

    # List pending activities
    python -m atlas.pipelines.activity_conversion --list-pending

    # Batch mode (use only after skills reliably produce Grade A)
    python -m atlas.pipelines.activity_conversion --batch --limit 10
"""

import asyncio
import fcntl
import json
import logging
import os
import re
import signal
import subprocess
import time
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

from atlas.babybrains.ai_detection import (
    check_superlatives as _ai_check_superlatives,
    check_pressure_language as _ai_check_pressure,
)
from atlas.orchestrator.hooks import HookRunner
from atlas.orchestrator.skill_executor import SkillExecutor, SkillLoader
from atlas.orchestrator.scratch_pad import ScratchPad
from atlas.orchestrator.session_manager import SessionManager
from atlas.orchestrator.subagent_executor import SubAgentExecutor

logger = logging.getLogger(__name__)


class ActivityStatus(Enum):
    """Status of an activity in the conversion pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"
    FAILED = "failed"
    REVISION_NEEDED = "revision_needed"
    QC_FAILED = "qc_failed"


@dataclass
class ConversionResult:
    """Result of converting a single activity."""

    activity_id: str
    status: ActivityStatus
    canonical_id: Optional[str] = None
    file_path: Optional[str] = None
    skip_reason: Optional[str] = None
    error: Optional[str] = None
    qc_issues: list[str] = field(default_factory=list)
    qc_warnings: list[str] = field(default_factory=list)
    elevated_yaml: Optional[str] = None


@dataclass
class BatchResult:
    """Result of batch processing multiple activities."""

    total: int
    completed: int
    skipped: int
    failed: int
    revision_needed: int
    results: list[ConversionResult] = field(default_factory=list)


class ActivityConversionPipeline:
    """
    Orchestrates the conversion of raw activities to canonical format.

    Flow:
        1. Load raw activities from YAML source
        2. Check conversion map for skip/group/domain corrections
        3. Execute skill chain: ingest -> research -> transform -> elevate -> validate
        4. Run QC hook (check_activity_quality.py)
        5. Present for human review
        6. Write approved files to canonical location
        7. Update progress tracker
    """

    # File paths
    RAW_ACTIVITIES_PATH = Path(
        "/home/squiz/code/knowledge/sources/structured/activities_v1/activities_fixed_01.yaml"
    )
    CONVERSION_MAP_PATH = Path(
        "/home/squiz/code/knowledge/.claude/workflow/ACTIVITY_CONVERSION_MAP.yaml"
    )
    PROGRESS_PATH = Path(
        "/home/squiz/code/knowledge/.claude/workflow/CONVERSION_PROGRESS.md"
    )
    CANONICAL_OUTPUT_DIR = Path("/home/squiz/code/knowledge/data/canonical/activities")
    QC_HOOK_PATH = Path("/home/squiz/code/knowledge/scripts/check_activity_quality.py")
    KNOWLEDGE_REPO = Path("/home/squiz/code/knowledge")

    # Per-stage timeout configuration (seconds)
    # Simple stages get shorter timeouts; complex stages get longer
    STAGE_TIMEOUTS = {
        "ingest": 300,      # 5 min - simple data extraction
        "research": 600,    # 10 min - cross-referencing
        "transform": 900,   # 15 min - building 34-section YAML
        "elevate": 1500,    # 25 min - voice elevation (most complex)
        "validate": 300,    # 5 min - structural checks
        "qc_hook": 60,      # 1 min - deterministic script
        "quality_audit": 900,  # 15 min - voice rubric grading
    }

    # Valid domains for activities
    # Includes both raw source domains and canonical output domains
    VALID_DOMAINS = {
        # Raw source domains
        "cognitive",
        "motor_fine",
        "language",
        "sensory",
        "motor_gross",
        "music_rhythm",
        "practical_life",
        "art_creative",
        "social_emotional",
        "nature_culture",
        # Canonical output domains (used in 23 Grade A activities)
        "movement",              # Replaces motor_fine, motor_gross
        "prepared_environment",  # Environment setup activities
        "feeding",               # Feeding and nutrition activities
        "art",                   # Simplified from art_creative
        "regulation",            # Self-regulation activities
        "motor_refinement",      # Fine motor activities
        "independence",          # Independence-focused activities
        "order",                 # Order and routine activities
    }

    # Age label patterns for parsing (D36: Age Range Normalization)
    # Implements ingest_activity.md line 111: "Always trust the label and recalculate"
    AGE_LABEL_PATTERNS = [
        # Prenatal: min=-9, max=0
        (r"^prenatal$", -9, 0),
        # X-Ym format: 0-6m, 6-12m, 12-24m etc.
        (r"^(\d+)-(\d+)\s*m$", None, None),  # Dynamic parsing
        # X-Y months format
        (r"^(\d+)-(\d+)\s*months?$", None, None),  # Dynamic parsing
        # X.X-Y years format: 1.5-3 years, 2-3 years
        (r"^(\d+(?:\.\d+)?)-(\d+)\s*years?$", None, None),  # Dynamic parsing
        # X+ months format: 18+ months
        (r"^(\d+)\+\s*months?$", None, 72),  # Dynamic min, max=72
        # 0-X format (shorthand): 0-3, 0-6, 0-12
        (r"^0-(\d+)$", 0, None),  # min=0, dynamic max
    ]

    def __init__(self):
        """Initialize the pipeline with all required components."""
        # CLI mode for Max subscription (no API key needed)
        # Uses `claude` CLI command instead of direct API calls

        self.skill_loader = SkillLoader(
            skills_path=Path("/home/squiz/code/babybrains-os/skills")
        )
        # CLI mode (uses Max subscription, no API key needed)
        self.skill_executor = SkillExecutor(use_api=False)
        self.session = SessionManager()
        self.scratch_pad: Optional[ScratchPad] = None

        # C-1: Add SubAgentExecutor for adversarial verification
        self.sub_executor = SubAgentExecutor(timeout=300)

        # C-2: Add HookRunner for QC hook
        self.hook_runner = HookRunner()

        # Data storage
        self.raw_activities: dict[str, dict] = {}
        self.conversion_map: dict[str, Any] = {}
        self.progress_data: dict[str, dict] = {}

        # Graceful shutdown: track current activity for signal handler
        self._current_activity_id: Optional[str] = None
        self._setup_signal_handlers()

        # Load source data
        self._load_source_data()

    def _setup_signal_handlers(self) -> None:
        """Install signal handlers for graceful shutdown.

        Uses flag-based approach to avoid deadlocks: signal handler sets
        a flag, and cleanup runs outside the handler via atexit.
        """
        import atexit

        self._shutdown_requested = False

        def _handle_shutdown(signum, frame):
            self._shutdown_requested = True
            # Re-raise as KeyboardInterrupt for SIGINT, exit for SIGTERM
            if signum == signal.SIGINT:
                raise KeyboardInterrupt
            else:
                sys.exit(1)

        def _cleanup_on_exit():
            """Reset current activity to PENDING if interrupted."""
            if self._current_activity_id and self._shutdown_requested:
                try:
                    self._update_progress_file(
                        self._current_activity_id, ActivityStatus.PENDING,
                        "Reset: interrupted by signal"
                    )
                except Exception:
                    pass  # Best-effort cleanup at exit

        try:
            signal.signal(signal.SIGINT, _handle_shutdown)
            signal.signal(signal.SIGTERM, _handle_shutdown)
            atexit.register(_cleanup_on_exit)
        except (OSError, ValueError):
            # Can't set signal handlers in non-main thread
            pass

    def cleanup_stale_progress(self, max_age_hours: int = 2) -> list[str]:
        """
        Reset IN_PROGRESS entries older than max_age_hours to PENDING.

        Args:
            max_age_hours: Maximum age in hours before considering stale

        Returns:
            List of activity IDs that were reset
        """
        reset_ids = []
        for raw_id, data in self.progress_data.items():
            if data.get("status") == ActivityStatus.IN_PROGRESS.value:
                last_updated = data.get("last_updated")
                if last_updated:
                    try:
                        updated_dt = datetime.fromisoformat(last_updated)
                        if updated_dt.tzinfo is None:
                            updated_dt = updated_dt.replace(tzinfo=timezone.utc)
                        age_hours = (
                            datetime.now(timezone.utc) - updated_dt
                        ).total_seconds() / 3600
                        if age_hours > max_age_hours:
                            self._update_progress_file(
                                raw_id, ActivityStatus.PENDING,
                                f"Reset: stale IN_PROGRESS ({age_hours:.1f}h)"
                            )
                            reset_ids.append(raw_id)
                            logger.info(
                                f"Reset stale IN_PROGRESS: {raw_id} ({age_hours:.1f}h old)"
                            )
                    except (ValueError, TypeError):
                        # Can't parse timestamp, reset anyway
                        self._update_progress_file(
                            raw_id, ActivityStatus.PENDING,
                            "Reset: stale IN_PROGRESS (no timestamp)"
                        )
                        reset_ids.append(raw_id)
                else:
                    # No timestamp at all — reset
                    self._update_progress_file(
                        raw_id, ActivityStatus.PENDING,
                        "Reset: stale IN_PROGRESS (no timestamp)"
                    )
                    reset_ids.append(raw_id)
        return reset_ids

    def _load_source_data(self) -> None:
        """Load raw activities and conversion map from YAML files."""
        # A-5: Defensive YAML parsing for raw activities
        if self.RAW_ACTIVITIES_PATH.exists():
            try:
                with open(self.RAW_ACTIVITIES_PATH) as f:
                    data = yaml.safe_load(f)

                # Handle empty YAML file
                if data is None:
                    logger.warning(f"Empty YAML file: {self.RAW_ACTIVITIES_PATH}")
                    self.raw_activities = {}
                    return

                activities = data.get("activities", [])

                # Validate activities is a list
                if not isinstance(activities, list):
                    raise ValueError(
                        f"'activities' must be a list, got {type(activities).__name__}"
                    )

                # Build dict with defensive parsing (skip activities without id)
                # G1: Add duplicate detection - keep first, warn on duplicates
                self.raw_activities = {}
                skipped_count = 0
                duplicate_count = 0
                for a in activities:
                    if not isinstance(a, dict):
                        logger.warning(f"Skipping non-dict activity: {type(a)}")
                        skipped_count += 1
                        continue
                    if "id" not in a:
                        logger.warning(
                            f"Skipping activity without id: {a.get('title', 'unknown')}"
                        )
                        skipped_count += 1
                        continue
                    # G1: Check for duplicate IDs before loading
                    if a["id"] in self.raw_activities:
                        logger.warning(
                            f"Duplicate activity ID found: {a['id']} - keeping first occurrence"
                        )
                        duplicate_count += 1
                        continue
                    self.raw_activities[a["id"]] = a

                log_parts = [f"Loaded {len(self.raw_activities)} raw activities"]
                if skipped_count:
                    log_parts.append(f"skipped {skipped_count}")
                if duplicate_count:
                    log_parts.append(f"duplicates {duplicate_count}")
                logger.info(" (".join(log_parts) + (")" if len(log_parts) > 1 else ""))
            except (yaml.YAMLError, ValueError) as e:
                logger.error(f"Failed to load raw activities: {e}")
                raise
        else:
            logger.warning(f"Raw activities file not found: {self.RAW_ACTIVITIES_PATH}")

        # Load conversion map
        if self.CONVERSION_MAP_PATH.exists():
            try:
                with open(self.CONVERSION_MAP_PATH) as f:
                    self.conversion_map = yaml.safe_load(f) or {}
                logger.info("Loaded conversion map")
            except yaml.YAMLError as e:
                logger.error(f"Failed to load conversion map: {e}")
                self.conversion_map = {}
        else:
            logger.warning(f"Conversion map not found: {self.CONVERSION_MAP_PATH}")
            self.conversion_map = {}

        # Parse progress file
        self._parse_progress_file()

    def _load_guidance_catalog(self) -> list[dict]:
        """
        Load the guidance catalog index for cross-domain matching.

        Returns cached catalog on subsequent calls. Returns empty list
        if the catalog file doesn't exist (graceful degradation).
        """
        if hasattr(self, "_guidance_catalog_cache"):
            return self._guidance_catalog_cache

        catalog_path = Path(__file__).resolve().parent.parent.parent / "config" / "babybrains" / "guidance_catalog.json"
        if not catalog_path.exists():
            logger.warning(f"Guidance catalog not found: {catalog_path}")
            self._guidance_catalog_cache = []
            return self._guidance_catalog_cache

        try:
            with open(catalog_path) as f:
                self._guidance_catalog_cache = json.load(f)
            logger.info(f"Loaded guidance catalog: {len(self._guidance_catalog_cache)} entries")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load guidance catalog: {e}")
            self._guidance_catalog_cache = []

        return self._guidance_catalog_cache

    def _load_materials_catalog(self) -> list[dict]:
        """
        Load the materials catalog index for material existence checking.

        Returns cached catalog on subsequent calls. Returns empty list
        if the catalog file doesn't exist (graceful degradation).
        """
        if hasattr(self, "_materials_catalog_cache"):
            return self._materials_catalog_cache

        catalog_path = Path(__file__).resolve().parent.parent.parent / "config" / "babybrains" / "materials_catalog.json"
        if not catalog_path.exists():
            logger.warning(f"Materials catalog not found: {catalog_path}")
            self._materials_catalog_cache = []
            return self._materials_catalog_cache

        try:
            with open(catalog_path) as f:
                self._materials_catalog_cache = json.load(f)
            logger.info(f"Loaded materials catalog: {len(self._materials_catalog_cache)} entries")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load materials catalog: {e}")
            self._materials_catalog_cache = []

        return self._materials_catalog_cache

    def _parse_progress_file(self) -> None:
        """
        Parse CONVERSION_PROGRESS.md markdown table into structured data.

        Table format:
        | # | Raw ID | Domain | Age Range | Status | Date | Notes |
        """
        if not self.PROGRESS_PATH.exists():
            logger.warning(f"Progress file not found: {self.PROGRESS_PATH}")
            return

        try:
            # D88: Add shared lock for reading to prevent race conditions
            with open(self.PROGRESS_PATH, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                try:
                    content = f.read()
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Find table rows using regex
            # Pattern matches: | num | raw_id | domain | age_range | status | date | notes |
            table_pattern = re.compile(
                r"^\|\s*(\d+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|",
                re.MULTILINE,
            )

            # G2: Track duplicates in progress file
            duplicate_count = 0
            for match in table_pattern.finditer(content):
                row_num = match.group(1).strip()
                raw_id = match.group(2).strip()
                domain = match.group(3).strip()
                age_range = match.group(4).strip()
                status = match.group(5).strip().lower()
                date = match.group(6).strip()
                notes = match.group(7).strip()

                # Skip header row
                if raw_id.lower() == "raw id" or raw_id == "---":
                    continue

                # G2: Check for duplicate entries - keep first, warn on duplicates
                if raw_id in self.progress_data:
                    logger.warning(
                        f"Duplicate entry in progress file: {raw_id} (row {row_num}) - keeping first"
                    )
                    duplicate_count += 1
                    continue

                self.progress_data[raw_id] = {
                    "row_num": row_num,
                    "domain": domain,
                    "age_range": age_range,
                    "status": status,
                    "date": date,
                    "notes": notes,
                }

            log_msg = f"Parsed {len(self.progress_data)} entries from progress file"
            if duplicate_count:
                log_msg += f" ({duplicate_count} duplicates ignored)"
            logger.info(log_msg)

        except OSError as e:
            logger.error(f"Failed to read progress file: {e}")

    def _validate_conversion_map(self) -> list[str]:
        """
        Validate all references in conversion map exist in raw activities.

        G3: Catches bad references early before processing.

        Returns:
            List of validation issues (empty if all valid)
        """
        issues = []

        # Check skip list
        for raw_id in self.conversion_map.get("skip", []):
            if raw_id not in self.raw_activities:
                issues.append(f"Skip list references unknown activity: {raw_id}")

        # Check groups
        for group_id, group_data in self.conversion_map.get("groups", {}).items():
            for source_id in group_data.get("sources", []):
                if source_id not in self.raw_activities:
                    issues.append(
                        f"Group '{group_id}' references unknown activity: {source_id}"
                    )

        # Check domain corrections
        for raw_id in self.conversion_map.get("domain_corrections", {}):
            if raw_id not in self.raw_activities:
                issues.append(
                    f"Domain correction references unknown activity: {raw_id}"
                )

        return issues

    def _get_group_info(self, raw_id: str) -> Optional[dict]:
        """
        Get group info if activity is a group primary.

        G5: Provides explicit group context for grouped conversions.

        Args:
            raw_id: Activity raw ID

        Returns:
            Group info dict if activity is a group primary, None otherwise
        """
        groups = self.conversion_map.get("groups", {})
        for group_id, group_data in groups.items():
            sources = group_data.get("sources", [])
            if sources and sources[0] == raw_id:
                # This is the primary - load all source activities
                source_activities = [
                    self.raw_activities.get(s)
                    for s in sources
                    if s in self.raw_activities
                ]
                return {
                    "group_id": group_id,
                    "sources": sources,
                    "source_activities": source_activities,
                    "domain": group_data.get("domain"),
                    "age_range": group_data.get("age_range"),
                }
        return None

    def reconcile_progress(self) -> dict:
        """
        Reconcile progress tracker with actual files on disk.

        C3 fix: Scans canonical output directory, cross-references with
        progress data, identifies discrepancies:
        - Files on disk but not tracked as 'done'
        - Tracked as 'done' but no file on disk
        - Count mismatches in header

        Returns:
            Dict with reconciliation report
        """
        on_disk = set()
        disk_files = []

        if self.CANONICAL_OUTPUT_DIR.exists():
            for yaml_file in self.CANONICAL_OUTPUT_DIR.rglob("*.yaml"):
                canonical_id = yaml_file.stem
                on_disk.add(canonical_id)
                disk_files.append(str(yaml_file.relative_to(self.CANONICAL_OUTPUT_DIR)))

        # Activities tracked as done in progress
        tracked_done = set()
        for raw_id, data in self.progress_data.items():
            if data.get("status") == "done":
                tracked_done.add(raw_id)

        # Find discrepancies
        # Files on disk but not tracked (could be under canonical_id, not raw_id)
        untracked = on_disk - tracked_done
        # Tracked as done but no file on disk
        missing_files = tracked_done - on_disk

        # Build report
        report = {
            "files_on_disk": len(on_disk),
            "tracked_done": len(tracked_done),
            "untracked_files": sorted(untracked),
            "missing_files": sorted(missing_files),
            "disk_files": sorted(disk_files),
            "status_counts": {},
        }

        # Count by status
        for data in self.progress_data.values():
            status = data.get("status", "unknown")
            report["status_counts"][status] = report["status_counts"].get(status, 0) + 1

        return report

    def get_deduplication_report(self) -> dict:
        """
        Generate a deduplication/grouping report.

        G4: Provides visibility into the dedup/grouping before batch processing.

        Returns:
            Dict with deduplication statistics and details
        """
        skip_list = self.conversion_map.get("skip", [])
        groups = self.conversion_map.get("groups", {})

        # Count activities in groups
        grouped_count = 0
        group_atoms = 0
        group_details = []
        for group_id, group_data in groups.items():
            sources = group_data.get("sources", [])
            grouped_count += len(sources)
            group_atoms += 1
            group_details.append({
                "group_id": group_id,
                "source_count": len(sources),
                "sources": sources,
                "domain": group_data.get("domain"),
                "age_range": group_data.get("age_range"),
            })

        # Calculate standalone count
        # Standalone = total - skip - grouped (but grouped contributes 1 each as group_atoms)
        total_raw = len(self.raw_activities)
        skip_count = len([s for s in skip_list if s in self.raw_activities])
        standalone_count = total_raw - skip_count - grouped_count + group_atoms

        # Expected canonical atoms = standalone + group_atoms
        expected_canonical = standalone_count

        # Validation issues
        validation_issues = self._validate_conversion_map()

        return {
            "raw_activities": total_raw,
            "skip_count": skip_count,
            "grouped_count": grouped_count,
            "group_atoms": group_atoms,
            "standalone_count": standalone_count - group_atoms,  # True standalone
            "expected_canonical": expected_canonical,
            "groups": group_details,
            "skip_list": [s for s in skip_list if s in self.raw_activities],
            "validation_issues": validation_issues,
        }

    def _update_progress_file(
        self,
        raw_id: str,
        status: ActivityStatus,
        notes: str = "",
    ) -> bool:
        """
        Update CONVERSION_PROGRESS.md with new status for an activity.

        Uses atomic write pattern: read -> modify -> write.

        Args:
            raw_id: Activity raw ID
            status: New status
            notes: Optional notes to add

        Returns:
            True if updated successfully, False otherwise
        """
        if not self.PROGRESS_PATH.exists():
            logger.error(f"Progress file not found: {self.PROGRESS_PATH}")
            return False

        try:
            # B-1: HIGH FIX - Use file locking for concurrent access safety
            with open(self.PROGRESS_PATH, "r+") as f:
                # Acquire exclusive lock (blocks until available)
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    content = f.read()
                    lines = content.split("\n")
                    updated = False

                    # Status string
                    status_str = status.value

                    # Date for done status
                    date_str = ""
                    if status == ActivityStatus.DONE:
                        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                    # Find and update the row
                    for i, line in enumerate(lines):
                        if (
                            f"| {raw_id} |" in line
                            or f"| {raw_id.replace('-', ' ')} |" in line
                        ):
                            # Parse existing row
                            parts = [p.strip() for p in line.split("|")]
                            if len(parts) >= 8:
                                # parts: ['', num, raw_id, domain, age_range, status, date, notes, '']
                                # Update status, date, notes
                                parts[5] = status_str
                                parts[6] = date_str
                                if notes:
                                    parts[7] = notes
                                # Re-add spaces to ALL parts for consistent formatting
                                # Format: | num | raw_id | domain | age_range | status | date | notes |
                                formatted_parts = ['']  # Leading empty
                                for j, part in enumerate(parts[1:-1], start=1):
                                    formatted_parts.append(f" {part} ")
                                formatted_parts.append('')  # Trailing empty
                                lines[i] = "|".join(formatted_parts)
                                updated = True
                                break

                    if updated:
                        # Track current activity for signal handler
                        if status == ActivityStatus.IN_PROGRESS:
                            self._current_activity_id = raw_id
                        elif status in (
                            ActivityStatus.DONE,
                            ActivityStatus.FAILED,
                            ActivityStatus.SKIPPED,
                            ActivityStatus.PENDING,
                            ActivityStatus.QC_FAILED,
                            ActivityStatus.REVISION_NEEDED,
                        ):
                            if self._current_activity_id == raw_id:
                                self._current_activity_id = None

                        # Update local cache FIRST (D83: fix stale cache bug)
                        now_str = datetime.now(timezone.utc).isoformat()
                        if raw_id in self.progress_data:
                            self.progress_data[raw_id]["status"] = status_str
                            self.progress_data[raw_id]["date"] = date_str
                            self.progress_data[raw_id]["last_updated"] = now_str
                            if notes:
                                self.progress_data[raw_id]["notes"] = notes

                        # Update summary counts (now uses current cache)
                        content = "\n".join(lines)
                        content = self._update_summary_counts(content)

                        # Truncate and write
                        f.seek(0)
                        f.write(content)
                        f.truncate()
                        logger.info(f"Updated progress for {raw_id}: {status_str}")

                        return True
                    else:
                        logger.warning(f"Activity {raw_id} not found in progress file")
                        return False

                finally:
                    # Always release the lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        except OSError as e:
            logger.error(f"Failed to update progress file: {e}")
            return False

    def _update_summary_counts(self, content: str) -> str:
        """Update all 7 summary counts in progress file content.

        C5 fix: Previously only wrote Done/Pending/Failed.
        Now writes all 7 statuses: Done, Pending, Failed, Skipped,
        Revision Needed, QC Failed, In Progress.

        For fields that may not exist in the header, uses conditional
        insertion after the "- Failed:" line.
        """
        # Count all statuses
        done = len([p for p in self.progress_data.values() if p["status"] == "done"])
        pending = len(
            [p for p in self.progress_data.values() if p["status"] == "pending"]
        )
        failed = len(
            [p for p in self.progress_data.values() if p["status"] == "failed"]
        )
        skipped = len(
            [p for p in self.progress_data.values() if p["status"] == "skipped"]
        )
        revision_needed = len(
            [p for p in self.progress_data.values() if p["status"] == "revision_needed"]
        )
        qc_failed = len(
            [p for p in self.progress_data.values() if p["status"] == "qc_failed"]
        )
        in_progress = len(
            [p for p in self.progress_data.values() if p["status"] == "in_progress"]
        )

        # Update existing fields via re.sub
        content = re.sub(r"- Done: \d+", f"- Done: {done}", content)
        content = re.sub(r"- Pending: \d+", f"- Pending: {pending}", content)
        content = re.sub(r"- Failed: \d+", f"- Failed: {failed}", content)
        content = re.sub(r"- Skipped: \d+", f"- Skipped: {skipped}", content)

        # C5 fix: Conditionally insert or update fields that may not exist
        for label, count in [
            ("Revision Needed", revision_needed),
            ("QC Failed", qc_failed),
            ("In Progress", in_progress),
        ]:
            pattern = f"- {label}: \\d+"
            if re.search(pattern, content):
                content = re.sub(pattern, f"- {label}: {count}", content)
            else:
                # Insert after "- Failed: \d+" line
                content = re.sub(
                    r"(- Failed: \d+)",
                    f"\\1\n- {label}: {count}",
                    content,
                )

        return content

    def get_pending_activities(self) -> list[str]:
        """
        Get list of activity IDs that need conversion.

        Returns:
            List of raw IDs with status 'pending'
        """
        pending = []
        for raw_id, data in self.progress_data.items():
            if data.get("status", "").lower() == "pending":
                pending.append(raw_id)
        return pending

    def get_next_available_activity(self) -> Optional[str]:
        """
        Get the next truly available activity for conversion.

        Unlike get_pending_activities(), this method filters out:
        - Activities in the skip list (duplicates/merged)
        - Non-primary activities in groups

        Returns:
            Raw ID of next convertible activity, or None if all done
        """
        pending = self.get_pending_activities()

        for raw_id in pending:
            should_skip, reason = self._should_skip(raw_id)
            if not should_skip:
                return raw_id
            else:
                logger.debug(f"Skipping {raw_id}: {reason}")

        return None

    def _should_skip(self, raw_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if activity should be skipped based on conversion map.

        Args:
            raw_id: Activity raw ID

        Returns:
            Tuple of (should_skip, reason)
        """
        skip_list = self.conversion_map.get("skip", [])
        if raw_id in skip_list:
            return True, "Listed in skip list (duplicate/merged)"

        # Check if part of a group but not primary
        groups = self.conversion_map.get("groups", {})
        for group_id, group_data in groups.items():
            sources = group_data.get("sources", [])
            if raw_id in sources:
                # First source is primary
                if sources[0] != raw_id:
                    return True, f"Non-primary in group {group_id}"

        return False, None

    def _get_domain_correction(self, raw_id: str) -> Optional[str]:
        """Get domain correction if one exists in conversion map."""
        corrections = self.conversion_map.get("domain_corrections", {})
        return corrections.get(raw_id)

    def _parse_age_label(self, label: str) -> tuple[Optional[int], Optional[int]]:
        """
        Parse an age range label into min/max months.

        D36: Age Range Normalization
        Implements ingest_activity.md line 111: "Always trust the label and recalculate"

        Args:
            label: Age label string (e.g., "2-3 years", "0-6m", "Prenatal")

        Returns:
            Tuple of (min_months, max_months) or (None, None) if parsing fails
        """
        if not label:
            return None, None

        label_lower = label.lower().strip()

        for pattern, static_min, static_max in self.AGE_LABEL_PATTERNS:
            match = re.match(pattern, label_lower, re.IGNORECASE)
            if match:
                groups = match.groups()

                # Static values (e.g., prenatal)
                if static_min is not None and static_max is not None:
                    return static_min, static_max

                # Dynamic parsing based on pattern type
                if "years" in label_lower:
                    # X.X-Y years format: convert to months
                    min_years = float(groups[0])
                    max_years = float(groups[1]) if len(groups) > 1 else 6.0
                    return int(min_years * 12), int(max_years * 12)
                elif "+" in label_lower:
                    # X+ months format
                    return int(groups[0]), static_max or 72
                elif len(groups) >= 2:
                    # X-Y format (months)
                    return int(groups[0]), int(groups[1])
                elif len(groups) == 1:
                    # 0-X shorthand
                    return static_min or 0, int(groups[0])

        # Special case: "All ages" or similar
        if "all" in label_lower:
            return 0, 72

        logger.warning(f"Could not parse age label: '{label}'")
        return None, None

    def _normalize_age_range(self, output: dict, raw_id: str) -> dict:
        """
        Normalize age range by trusting the label over raw min_months.

        D36: Age Range Normalization
        Implements ingest_activity.md line 111: "Always trust the label and recalculate"

        If raw data has min_months=0 but label says "2-3 years", this corrects
        to min_months=24, max_months=36.

        Args:
            output: INGEST output containing age_range dict
            raw_id: Activity ID for logging

        Returns:
            Updated output dict with corrected age_range if needed
        """
        age_range = output.get("age_range", {})
        if not age_range:
            # Try to get from raw_activity
            raw_activity = output.get("raw_activity", {})
            age_range = raw_activity.get("age_range", {})
            if age_range:
                output["age_range"] = age_range.copy()

        if not age_range:
            return output

        label = age_range.get("label", "")
        raw_min = age_range.get("min_months", 0)
        raw_max = age_range.get("max_months", 72)

        # Parse label to calculate expected min/max
        expected_min, expected_max = self._parse_age_label(label)

        if expected_min is None:
            # Could not parse label, keep raw values
            return output

        # Check for mismatch and correct
        if expected_min != raw_min or expected_max != raw_max:
            logger.warning(
                f"[{raw_id}] Age range correction: label '{label}' → {expected_min}-{expected_max}m "
                f"(raw data had {raw_min}-{raw_max}m)"
            )
            output["age_range"] = {
                "min_months": expected_min,
                "max_months": expected_max,
                "label": label,
            }
            output["age_range_corrected"] = True
            output["age_range_original"] = {
                "min_months": raw_min,
                "max_months": raw_max,
            }

        return output

    async def _execute_ingest(self, raw_id: str) -> tuple[bool, dict, Optional[str]]:
        """
        Execute the ingest_activity skill.

        Args:
            raw_id: Activity raw ID

        Returns:
            Tuple of (success, output_data, error_message)
        """
        logger.info(f"[INGEST] Starting for {raw_id}")

        # Check skip logic first
        should_skip, skip_reason = self._should_skip(raw_id)
        if should_skip:
            return True, {"should_skip": True, "skip_reason": skip_reason}, None

        # Get raw activity data
        raw_activity = self.raw_activities.get(raw_id)
        if not raw_activity:
            return False, {}, f"Raw activity not found: {raw_id}"

        # Check for domain correction
        domain_correction = self._get_domain_correction(raw_id)
        if domain_correction:
            raw_activity = raw_activity.copy()
            raw_activity["domain"] = domain_correction
            logger.info(f"Applied domain correction: {domain_correction}")

        # G5: Get group info if this is a group primary
        group_info = self._get_group_info(raw_id)
        if group_info:
            logger.info(
                f"Group primary detected: {group_info['group_id']} "
                f"({len(group_info['sources'])} sources)"
            )

        # Execute skill with explicit group context
        input_data = {"raw_id": raw_id, "raw_activity": raw_activity}
        if group_info:
            input_data["group_info"] = group_info

        stage_start = time.perf_counter()
        result = await self.skill_executor.execute(
            skill_name="activity/ingest_activity",
            input_data=input_data,
            validate=True,
            timeout=self.STAGE_TIMEOUTS.get("ingest"),
        )
        duration = time.perf_counter() - stage_start
        logger.info(f"[INGEST] Completed in {duration:.1f}s")

        if not result.success:
            return False, {}, result.error or "Ingest skill failed"

        output = result.output or {}
        output["raw_activity"] = raw_activity
        output["activity_id"] = raw_id

        # D36: Age Range Normalization - trust the label over raw min_months
        output = self._normalize_age_range(output, raw_id)

        return True, output, None

    async def _execute_research(
        self, ingest_output: dict
    ) -> tuple[bool, dict, Optional[str]]:
        """
        Execute the research_activity skill.

        Injects guidance and materials catalogs into input_data so the
        RESEARCH LLM can perform cross-domain matching without filesystem
        access. Uses .copy() to avoid mutating the caller's dict.

        Args:
            ingest_output: Output from ingest skill

        Returns:
            Tuple of (success, output_data, error_message)
        """
        logger.info(f"[RESEARCH] Starting for {ingest_output.get('activity_id')}")

        # Inject catalogs for cross-domain matching (copy to avoid mutation)
        enriched_input = ingest_output.copy()
        enriched_input["guidance_catalog"] = self._load_guidance_catalog()
        enriched_input["materials_catalog"] = self._load_materials_catalog()

        stage_start = time.perf_counter()
        result = await self.skill_executor.execute(
            skill_name="activity/research_activity",
            input_data=enriched_input,
            validate=True,
            timeout=self.STAGE_TIMEOUTS.get("research"),
        )
        duration = time.perf_counter() - stage_start
        logger.info(f"[RESEARCH] Completed in {duration:.1f}s")

        if not result.success:
            return False, {}, result.error or "Research skill failed"

        return True, result.output or {}, None

    def _extract_transform_yaml_fallback(self, raw_output: str) -> tuple[bool, dict, Optional[str]]:
        """
        Fallback extraction for TRANSFORM output when JSON parsing fails.

        When the LLM embeds large YAML inside a JSON string value, unescaped
        characters can break JSON parsing. This method bypasses JSON entirely
        and extracts the YAML content directly from the raw output.

        Returns:
            Tuple of (success, output_dict, error_message)
        """
        if not raw_output:
            return False, {}, "No raw output for fallback extraction"

        # Find the YAML value start — it's after "canonical_yaml": "
        yaml_key = '"canonical_yaml": "'
        yaml_start = raw_output.find(yaml_key)
        if yaml_start == -1:
            # Try alternate: YAML might start directly with type: Activity
            yaml_start = raw_output.find("type: Activity")
            if yaml_start == -1:
                return False, {}, "Fallback: no 'canonical_yaml' or 'type: Activity' found"
            yaml_escaped = raw_output[yaml_start:]
        else:
            yaml_escaped = raw_output[yaml_start + len(yaml_key):]

        # Trim trailing JSON/markdown artifacts
        # Look for the next JSON key after the YAML value
        for end_pattern in [
            '",\n  "canonical_id"',
            '",\n"canonical_id"',
            '", "canonical_id"',
            '"\n}',
            '"\n```',
        ]:
            end_idx = yaml_escaped.find(end_pattern)
            if end_idx > 0:
                yaml_escaped = yaml_escaped[:end_idx]
                break

        # Unescape JSON string encoding
        yaml_content = yaml_escaped.replace("\\n", "\n")
        yaml_content = yaml_content.replace('\\"', '"')
        yaml_content = yaml_content.replace("\\\\", "\\")
        yaml_content = yaml_content.replace("\\t", "\t")
        yaml_content = yaml_content.strip()

        if len(yaml_content) < 500:
            return False, {}, f"Fallback: extracted YAML too short ({len(yaml_content)} chars)"

        # Validate it looks like YAML
        if not yaml_content.startswith("type: Activity"):
            return False, {}, "Fallback: extracted content doesn't start with 'type: Activity'"

        # Extract canonical_id from the YAML
        canonical_id = ""
        for line in yaml_content.split("\n"):
            if line.startswith("canonical_id:"):
                canonical_id = line.split(":", 1)[1].strip()
                break

        if not canonical_id:
            return False, {}, "Fallback: could not extract canonical_id from YAML"

        # Derive file_path from canonical_id
        file_path = f"activities/{canonical_id}.yaml"

        # Try extracting canonical_id and file_path from JSON keys too
        for key, var_name in [
            ('"canonical_id": "', "canonical_id"),
            ('"file_path": "', "file_path"),
        ]:
            idx = raw_output.find(key)
            if idx > 0:
                value_start = idx + len(key)
                value_end = raw_output.find('"', value_start)
                if value_end > value_start:
                    extracted = raw_output[value_start:value_end]
                    if var_name == "canonical_id" and extracted:
                        canonical_id = extracted
                    elif var_name == "file_path" and extracted:
                        file_path = extracted

        logger.info(
            f"[TRANSFORM] Fallback extraction succeeded: "
            f"yaml={len(yaml_content)} chars, id={canonical_id}"
        )

        return True, {
            "canonical_yaml": yaml_content,
            "canonical_id": canonical_id,
            "file_path": file_path,
        }, None

    async def _execute_transform(
        self,
        ingest_output: dict,
        research_output: dict,
    ) -> tuple[bool, dict, Optional[str]]:
        """
        Execute the transform_activity skill.

        Args:
            ingest_output: Output from ingest skill
            research_output: Output from research skill

        Returns:
            Tuple of (success, output_data, error_message)
        """
        logger.info(f"[TRANSFORM] Starting for {ingest_output.get('activity_id')}")

        stage_start = time.perf_counter()
        result = await self.skill_executor.execute(
            skill_name="activity/transform_activity",
            input_data={
                "ingest_result": ingest_output,
                "research_result": research_output,
            },
            validate=True,
            timeout=self.STAGE_TIMEOUTS.get("transform"),
        )
        duration = time.perf_counter() - stage_start
        logger.info(f"[TRANSFORM] Completed in {duration:.1f}s")

        if not result.success:
            # Log raw output for debugging JSON parse failures
            if result.raw_output:
                logger.warning(
                    f"[TRANSFORM] Failed. Raw output preview ({len(result.raw_output)} chars): "
                    f"{result.raw_output[:500]}"
                )

                # Attempt fallback YAML extraction when JSON parsing fails
                if "Invalid JSON" in (result.error or ""):
                    logger.info("[TRANSFORM] Attempting fallback YAML extraction...")
                    fb_ok, fb_data, fb_err = self._extract_transform_yaml_fallback(
                        result.raw_output
                    )
                    if fb_ok:
                        logger.info("[TRANSFORM] Fallback extraction succeeded")
                        return True, fb_data, None
                    else:
                        logger.warning(f"[TRANSFORM] Fallback also failed: {fb_err}")

            return False, {}, result.error or "Transform skill failed"

        return True, result.output or {}, None

    async def _execute_elevate(
        self, canonical_yaml: str, feedback: Optional[str] = None
    ) -> tuple[bool, dict, Optional[str]]:
        """
        Execute the elevate_voice_activity skill.

        Args:
            canonical_yaml: YAML content from transform skill
            feedback: Optional feedback from previous attempt for intelligent retry

        Returns:
            Tuple of (success, output_data, error_message)

        Note:
            The manual process (Jan 1-4, 2026) that produced 23 Grade A activities
            loaded the full voice standard and rubric BEFORE elevation. This method
            replicates that by pre-loading and passing the content directly.
        """
        if feedback:
            logger.info("[ELEVATE] Starting voice elevation WITH FEEDBACK (retry)")
        else:
            logger.info("[ELEVATE] Starting voice elevation")

        # Pre-load voice standard extract and rubric
        # D40: Use focused extract (~50KB) instead of full voice standard (~95KB)
        # Extract contains only soul-carrying sections needed for Activity elevation
        # (philosophy, Australian voice, craft, transformation demos)
        # Removed: format_adaptations, evidence_framework, video/caption specs
        voice_standard_path = Path("/home/squiz/code/babybrains-os/skills/activity/ELEVATE_VOICE_EXTRACT.md")
        rubric_path = Path("/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md")

        voice_standard_content = ""
        rubric_content = ""

        try:
            if voice_standard_path.exists():
                voice_standard_content = voice_standard_path.read_text()
                logger.info(f"[ELEVATE] Loaded voice standard: {len(voice_standard_content)} chars")
            else:
                logger.warning(f"[ELEVATE] Voice standard not found: {voice_standard_path}")

            if rubric_path.exists():
                rubric_content = rubric_path.read_text()
                logger.info(f"[ELEVATE] Loaded rubric: {len(rubric_content)} chars")
            else:
                logger.warning(f"[ELEVATE] Rubric not found: {rubric_path}")
        except Exception as e:
            logger.warning(f"[ELEVATE] Error loading context files: {e}")

        # Pre-elevation dash removal (deterministic, not LLM-dependent)
        # D80: Handles em-dashes, en-dashes, and double-hyphens
        canonical_yaml = self._remove_dashes(canonical_yaml)

        # Build input data with full context (matching manual process)
        input_data = {
            "canonical_yaml": canonical_yaml,
            "voice_standard_path": str(voice_standard_path),
            "voice_standard_content": voice_standard_content,
            "rubric_content": rubric_content,
        }
        if feedback:
            input_data["retry_feedback"] = feedback
            input_data["is_retry"] = True

        stage_start = time.perf_counter()
        result = await self.skill_executor.execute(
            skill_name="activity/elevate_voice_activity",
            input_data=input_data,
            validate=True,
            timeout=self.STAGE_TIMEOUTS.get("elevate"),
        )
        duration = time.perf_counter() - stage_start
        logger.info(f"[ELEVATE] Completed in {duration:.1f}s")

        if not result.success:
            if result.raw_output:
                logger.warning(
                    f"[ELEVATE] Failed. Raw output preview ({len(result.raw_output)} chars): "
                    f"{result.raw_output[:500]}"
                )

                # Attempt fallback YAML extraction when JSON parsing fails
                if "Invalid JSON" in (result.error or ""):
                    logger.info("[ELEVATE] Attempting fallback YAML extraction...")
                    fb_ok, fb_data, fb_err = self._extract_elevate_yaml_fallback(
                        result.raw_output
                    )
                    if fb_ok:
                        logger.info("[ELEVATE] Fallback extraction succeeded")
                        return True, fb_data, None
                    else:
                        logger.warning(f"[ELEVATE] Fallback also failed: {fb_err}")

            return False, {}, result.error or "Elevate skill failed"

        # D38: Validate output has required fields - don't silently return empty dict
        output = result.output
        if not output or not isinstance(output, dict):
            return False, {}, f"Elevate returned invalid output: {type(output)}"

        if "elevated_yaml" not in output:
            return False, {}, "Elevate output missing 'elevated_yaml' field"

        return True, output, None

    def _extract_elevate_yaml_fallback(self, raw_output: str) -> tuple[bool, dict, Optional[str]]:
        """
        Fallback extraction for ELEVATE output when JSON parsing fails.

        Similar to TRANSFORM fallback but looks for 'elevated_yaml' key.

        Returns:
            Tuple of (success, output_dict, error_message)
        """
        if not raw_output:
            return False, {}, "No raw output for fallback extraction"

        # Find the YAML value start
        yaml_key = '"elevated_yaml": "'
        yaml_start = raw_output.find(yaml_key)
        if yaml_start == -1:
            # Try alternate: look for type: Activity directly
            yaml_start = raw_output.find("type: Activity")
            if yaml_start == -1:
                return False, {}, "Fallback: no 'elevated_yaml' or 'type: Activity' found"
            yaml_escaped = raw_output[yaml_start:]
        else:
            yaml_escaped = raw_output[yaml_start + len(yaml_key):]

        # Trim trailing JSON/markdown artifacts
        for end_pattern in ['"\n}', '"\n```', '"}']:
            end_idx = yaml_escaped.rfind(end_pattern)
            if end_idx > 0:
                yaml_escaped = yaml_escaped[:end_idx]
                break

        # Unescape JSON string encoding
        yaml_content = yaml_escaped.replace("\\n", "\n")
        yaml_content = yaml_content.replace('\\"', '"')
        yaml_content = yaml_content.replace("\\\\", "\\")
        yaml_content = yaml_content.replace("\\t", "\t")
        yaml_content = yaml_content.strip()

        if len(yaml_content) < 500:
            return False, {}, f"Fallback: extracted YAML too short ({len(yaml_content)} chars)"

        if not yaml_content.startswith("type: Activity"):
            return False, {}, "Fallback: extracted content doesn't start with 'type: Activity'"

        logger.info(
            f"[ELEVATE] Fallback extraction succeeded: yaml={len(yaml_content)} chars"
        )

        return True, {"elevated_yaml": yaml_content}, None

    def _remove_dashes(self, content: str) -> str:
        """
        Remove em-dashes, en-dashes, and double-hyphens from content.

        Deterministic cleanup that doesn't rely on LLM compliance.
        Aligns with QC hook's DASH_PATTERN: (—|–|--)

        Runs on ELEVATE INPUT (pre-processing) and ELEVATE OUTPUT
        (post-processing) to catch dashes the LLM introduces.

        Args:
            content: YAML content that may contain dash variants

        Returns:
            Content with dashes replaced
        """
        em_count = content.count("\u2014")  # em-dash —
        en_count = content.count("\u2013")  # en-dash –
        dd_count = content.count("--")

        total = em_count + en_count + dd_count
        if total > 0:
            logger.info(
                f"[DASH-CLEANUP] Removing {total} dashes "
                f"(em={em_count}, en={en_count}, double={dd_count})"
            )
            # Em-dash: replace with ". " (or "." if no trailing space)
            content = re.sub(r"\u2014\s*", ". ", content)
            content = content.replace("\u2014", ".")
            # En-dash: same treatment
            content = re.sub(r"\u2013\s*", ". ", content)
            content = content.replace("\u2013", ".")
            # Double-hyphen: same treatment
            content = re.sub(r"--\s*", ". ", content)
            content = content.replace("--", ".")
        return content

    def _remove_em_dashes(self, content: str) -> str:
        """Backward-compatible alias for _remove_dashes."""
        return self._remove_dashes(content)

    def _quick_validate(self, yaml_content: str) -> list[dict]:
        """
        Quick regex check for common anti-patterns before full QC.

        D36: Pre-Validation Quick Check
        Catches the most common failures early to enable quick retry with
        targeted feedback, without running the full QC hook.

        Uses ai_detection.py's check_superlatives (context-aware exceptions)
        and check_pressure_language for consistency with the QC hook.
        Keeps inline em-dash check and "make sure to" (not in ai_detection).

        Design principle: This is an optimistic PRE-FILTER -- a fast subset
        of what the QC hook checks. It must NOT be stricter than the QC hook
        (or it would cause false retries). The QC hook remains authoritative.

        Args:
            yaml_content: Elevated YAML content to check

        Returns:
            List of issue dicts (empty if no issues found)
        """
        issues = []

        # Strip parent_search_terms section before superlative checking.
        # Search terms contain SEO queries ("best books for...") that use
        # marketing language parents actually search for — not our voice.
        content_for_check = yaml_content
        pst_match = re.search(
            r"^parent_search_terms:.*",
            yaml_content,
            re.MULTILINE | re.DOTALL,
        )
        if pst_match:
            content_for_check = yaml_content[: pst_match.start()]

        # 1. Superlatives via ai_detection (context-aware exceptions)
        # Maps SCRIPT_* codes to VOICE_* codes for pipeline consistency
        for ai_issue in _ai_check_superlatives(content_for_check):
            issues.append({
                "code": "VOICE_SUPERLATIVE",
                "category": "superlative",
                "issue": ai_issue["msg"],
                "severity": "block",
            })

        # 2. Pressure language via ai_detection
        for ai_issue in _ai_check_pressure(yaml_content):
            issues.append({
                "code": "VOICE_PRESSURE_LANGUAGE",
                "category": "pressure",
                "issue": ai_issue["msg"],
                "severity": "block",
            })

        # 3. "make sure to" -- unique to pipeline, not in ai_detection
        if re.search(r"\bmake\s+sure\s+to\b", yaml_content, re.IGNORECASE):
            issues.append({
                "code": "VOICE_PRESSURE_LANGUAGE",
                "category": "pressure",
                "issue": "Found 'make sure to'. Use supportive language instead.",
                "severity": "block",
            })

        # 4. Dash check -- em-dash (U+2014), en-dash (U+2013), double-hyphen
        # D80: Aligned with QC hook's DASH_PATTERN: (—|–|--)
        for dash_char, dash_name in [
            ("\u2014", "em-dash"),
            ("\u2013", "en-dash"),
            ("--", "double-hyphen"),
        ]:
            if dash_char in yaml_content:
                issues.append({
                    "code": "VOICE_EM_DASH",
                    "category": "emdash",
                    "issue": f"Found {dash_name}. Use commas, periods, or line breaks.",
                    "severity": "block",
                })

        if issues:
            logger.info(f"[QUICK-VALIDATE] Found {len(issues)} anti-patterns before full QC")

        return issues

    def _fix_canonical_id(self, content: str, canonical_id: str) -> str:
        """
        Fix canonical_id in YAML to match the TRANSFORM-determined ID.

        ELEVATE sometimes changes the canonical_id (e.g., renaming
        "FOOD_PREPARATION_ACTIVITIES" to "FOOD_PREPARATION_PROGRESSION").
        The TRANSFORM canonical_id is authoritative.

        Args:
            content: YAML content that may have modified canonical_id
            canonical_id: The authoritative canonical_id from TRANSFORM

        Returns:
            Content with corrected canonical_id
        """
        pattern = r"(canonical_id:\s*)([^\n]+)"

        def replacer(match):
            current_id = match.group(2).strip().strip('"').strip("'")
            if current_id != canonical_id:
                logger.info(f"[POST-PROCESS] Fixing canonical_id: '{current_id}' -> '{canonical_id}'")
                return f"{match.group(1)}{canonical_id}"
            return match.group(0)

        return re.sub(pattern, replacer, content)

    def _fix_canonical_slug(self, content: str, canonical_id: str) -> str:
        """
        Fix canonical_slug to match the deterministic derivation from canonical_id.

        This ensures canonical_slug is always: canonical_id.lower().replace('_', '-')
        LLMs sometimes generate incorrect formats (e.g., adding -au suffix).

        Args:
            content: YAML content that may have incorrect canonical_slug
            canonical_id: The canonical ID to derive slug from

        Returns:
            Content with corrected canonical_slug
        """
        expected_slug = canonical_id.lower().replace("_", "-")

        # Match canonical_slug: followed by any value
        pattern = r"(canonical_slug:\s*)([^\n]+)"

        def replacer(match):
            current_slug = match.group(2).strip().strip('"').strip("'")
            if current_slug != expected_slug:
                logger.info(f"[POST-PROCESS] Fixing canonical_slug: '{current_slug}' -> '{expected_slug}'")
                return f"{match.group(1)}{expected_slug}"
            return match.group(0)

        return re.sub(pattern, replacer, content)

    def _fix_principle_slugs(self, content: str) -> str:
        """
        D35: Fix principle slugs to use underscores instead of hyphens.

        LLMs sometimes generate slugs like 'practical-life' instead of 'practical_life'.
        This post-processes to ensure consistency with VALID_PRINCIPLES in QC.
        """
        # Known principle slugs that might be hyphenated
        principle_mappings = {
            "practical-life": "practical_life",
            "absorbent-mind": "absorbent_mind",
            "sensitive-periods": "sensitive_periods",
            "prepared-environment": "prepared_environment",
            "freedom-within-limits": "freedom_within_limits",
            "grace-and-courtesy": "grace_and_courtesy",
            "maximum-effort": "maximum_effort",
            "work-of-the-child": "work_of_the_child",
            "cosmic-view": "cosmic_view",
            "spiritual-embryo": "spiritual_embryo",
            "follow-the-child": "follow_the_child",
            "freedom-of-movement": "freedom_of_movement",
            "care-of-environment": "care_of_environment",
            "hand-mind-connection": "hand_mind_connection",
            "self-correcting-materials": "self_correcting_materials",
            "concrete-to-abstract": "concrete_to_abstract",
            "sensory-exploration": "sensory_exploration",
            "inner-teacher": "inner_teacher",
            "risk-competence": "risk_competence",
            "refinement-of-movement": "refinement_of_movement",
            "language-development": "language_development",
            "respect-for-the-child": "respect_for_the_child",
            "respect-for-the-individual": "respect_for_the_individual",
            "hand-as-instrument-of-intelligence": "hand_as_instrument_of_intelligence",
        }

        fixed_content = content
        for wrong, correct in principle_mappings.items():
            if wrong in fixed_content:
                logger.info(f"[POST-PROCESS] Fixing principle slug: '{wrong}' -> '{correct}'")
                fixed_content = fixed_content.replace(wrong, correct)

        return fixed_content

    def _fix_age_range(self, elevated_yaml: str, original_yaml: str) -> str:
        """
        D90: Preserve ALL critical metadata fields from original file.

        ELEVATE regenerates the entire YAML and can corrupt non-prose fields.
        This post-processes to ensure all metadata is preserved exactly.

        Critical fields preserved:
        - type, canonical_id, canonical_slug, version, last_updated, canonical
        - age_months_min, age_months_max
        - domain (list)
        - evidence_strength, priority_ranking, query_frequency_estimate

        Args:
            elevated_yaml: YAML content after elevation
            original_yaml: Original YAML content before elevation

        Returns:
            YAML content with all metadata preserved from original
        """
        import re

        try:
            original_data = yaml.safe_load(original_yaml)
            elevated_data = yaml.safe_load(elevated_yaml)

            if not original_data or not elevated_data:
                return elevated_yaml

            # Track what we fix for logging
            fixes = []

            # Critical scalar fields that must be preserved exactly
            scalar_fields = [
                "type",
                "canonical_id",
                "canonical_slug",
                "version",
                "last_updated",
                "canonical",
                "age_months_min",
                "age_months_max",
                "evidence_strength",
                "priority_ranking",
                "query_frequency_estimate",
            ]

            fixed = elevated_yaml
            for field in scalar_fields:
                original_val = original_data.get(field)
                if original_val is not None:
                    # Use regex to preserve YAML structure
                    if isinstance(original_val, bool):
                        val_str = "true" if original_val else "false"
                        pattern = rf'^({field}:\s*)(true|false|\w+)'
                    elif isinstance(original_val, int):
                        val_str = str(original_val)
                        pattern = rf'^({field}:\s*)[\d\-]+'
                    elif isinstance(original_val, float):
                        val_str = str(original_val)
                        pattern = rf'^({field}:\s*)[\d\.\-]+'
                    else:
                        # String - handle quoted and unquoted
                        val_str = f'"{original_val}"' if ' ' in str(original_val) or '-' in str(original_val) else str(original_val)
                        pattern = rf'^({field}:\s*)["\']?[^"\'\n]+["\']?'

                    new_fixed = re.sub(pattern, rf'\g<1>{val_str}', fixed, flags=re.MULTILINE)
                    if new_fixed != fixed:
                        fixes.append(field)
                        fixed = new_fixed

            # Preserve domain list (special handling for YAML list)
            original_domains = original_data.get("domain", [])
            if original_domains and isinstance(original_domains, list):
                # Check if domain was corrupted
                elevated_domains = elevated_data.get("domain", [])
                if set(original_domains) != set(elevated_domains):
                    fixes.append("domain")
                    # Rebuild domain section
                    domain_yaml = "domain:\n" + "\n".join(f"  - {d}" for d in original_domains)
                    # Replace domain section
                    fixed = re.sub(
                        r'^domain:\n(?:  - [^\n]+\n)*',
                        domain_yaml + "\n",
                        fixed,
                        flags=re.MULTILINE
                    )

            if fixes:
                logger.info(f"[POST-PROCESS] Preserved metadata fields: {', '.join(fixes)}")

            return fixed

        except Exception as e:
            logger.warning(f"[POST-PROCESS] Metadata preservation failed: {e}")
            return elevated_yaml

    # Patterns that indicate guidance/materials reference issues (move to warnings)
    _GUIDANCE_MATERIAL_WARN_PATTERNS = [
        re.compile(r"GUIDANCE_[A-Z_]+_\d{4}\s+(not found|does not exist|missing)", re.IGNORECASE),
        re.compile(r"[Mm]aterial\s+slug\s+.+?\s+not\s+(found|in catalog)"),
        re.compile(r"[Mm]aterial.+?not\s+in\s+(catalog|materials catalog)"),
        re.compile(r"catalog\s+(is\s+)?incomplete", re.IGNORECASE),
        re.compile(r"may\s+need\s+creation", re.IGNORECASE),
    ]

    # Patterns that indicate real structural issues (keep blocking even if above match)
    _STRUCTURAL_EXCLUDE_KEYWORDS = ["section", "field", "YAML", "syntax"]

    def _fix_validation_misclassification(self, validate_output: dict) -> dict:
        """
        Move guidance/materials reference issues from blocking_issues to warnings.

        The VALIDATE LLM sometimes misclassifies guidance/materials reference
        problems as blocking when they should be warnings (the guidance and
        materials catalogs are intentionally incomplete).

        Uses tightly anchored patterns to avoid false positives on real
        structural issues (e.g., "guidance_components section not found").

        Args:
            validate_output: Raw output from validate skill

        Returns:
            validate_output with corrected classification
        """
        validation_result = validate_output.get("validation_result")
        if not validation_result:
            return validate_output

        blocking = validation_result.get("blocking_issues", [])
        if not blocking:
            return validate_output

        warnings = validation_result.get("warnings", [])
        new_blocking = []
        moved_count = 0

        for issue in blocking:
            if not isinstance(issue, str):
                new_blocking.append(issue)
                continue

            # Check if this looks like a guidance/materials reference issue
            is_ref_issue = any(p.search(issue) for p in self._GUIDANCE_MATERIAL_WARN_PATTERNS)

            # But exclude real structural issues
            is_structural = any(kw in issue for kw in self._STRUCTURAL_EXCLUDE_KEYWORDS)

            if is_ref_issue and not is_structural:
                warnings.append(issue)
                moved_count += 1
            else:
                new_blocking.append(issue)

        if moved_count > 0:
            logger.info(
                f"[POST-PROCESS] Reclassified {moved_count} guidance/materials "
                f"issues from blocking to warnings"
            )
            validation_result["blocking_issues"] = new_blocking
            validation_result["warnings"] = warnings

            # Recalculate passed if no remaining blockers
            if not new_blocking:
                validation_result["passed"] = True
                logger.info("[POST-PROCESS] No remaining blockers — validation now passes")

        return validate_output

    def _detect_truncation(self, yaml_content: str) -> tuple[bool, str]:
        """
        Detect if Activity Atom YAML output is truncated.

        All canonical Activity Atoms end with the parent_search_terms field,
        which is a YAML list. Truncation is detected when:
        - parent_search_terms section is missing
        - Last line is not a list item (- "...")
        - Required top-level fields are missing
        - Output is suspiciously short

        Returns:
            (is_truncated: bool, reason: str)
        """
        if not yaml_content or not yaml_content.strip():
            return (True, "Empty output")

        lines = yaml_content.strip().split('\n')

        # Check 1: Minimum length (shortest canonical is ~200 lines)
        if len(lines) < 150:
            return (True, f"Output too short ({len(lines)} lines, expected 150+)")

        # Check 2: parent_search_terms section must exist
        if 'parent_search_terms:' not in yaml_content:
            return (True, "Missing parent_search_terms section (final field)")

        # Check 3: Must end with a parent_search_terms list item
        # Valid endings: '  - "search term"' or "  - 'search term'"
        last_line = lines[-1].strip()
        if not (last_line.startswith('- "') or last_line.startswith("- '")):
            # Allow for trailing empty lines
            for i in range(min(3, len(lines))):
                check_line = lines[-(i+1)].strip()
                if check_line.startswith('- "') or check_line.startswith("- '"):
                    break
                if check_line and not check_line.startswith('#'):
                    return (True, f"Last content line is not a search term: '{check_line[:50]}...'")

        # Check 4: Required top-level fields
        required_fields = ['type: Activity', 'canonical_id:', 'priority_ranking:', 'query_frequency_estimate:']
        for field in required_fields:
            if field not in yaml_content:
                return (True, f"Missing required field: {field}")

        return (False, "Output appears complete")

    async def _execute_validate(
        self,
        elevated_yaml: str,
        file_path: str,
        canonical_id: str,
    ) -> tuple[bool, dict, Optional[str]]:
        """
        Execute the validate_activity skill.

        Args:
            elevated_yaml: Elevated YAML content
            file_path: Target file path
            canonical_id: Canonical activity ID

        Returns:
            Tuple of (success, output_data, error_message)
        """
        logger.info(f"[VALIDATE] Starting for {canonical_id}")

        stage_start = time.perf_counter()
        result = await self.skill_executor.execute(
            skill_name="activity/validate_activity",
            input_data={
                "elevated_yaml": elevated_yaml,
                "file_path": file_path,
                "canonical_id": canonical_id,
            },
            validate=True,
            timeout=self.STAGE_TIMEOUTS.get("validate"),
        )
        duration = time.perf_counter() - stage_start
        logger.info(f"[VALIDATE] Completed in {duration:.1f}s")

        if not result.success:
            return False, {}, result.error or "Validate skill failed"

        return True, result.output or {}, None

    async def _run_qc_hook(self, yaml_content: str) -> tuple[bool, list[str], list[str]]:
        """
        Run QC hook via HookRunner.

        C-2: SPEC COMPLIANCE - Use HookRunner instead of raw subprocess.
        The hook expects YAML via stdin and outputs JSON.

        Args:
            yaml_content: YAML content to validate

        Returns:
            Tuple of (passed, blocking_issues, warnings)
        """
        logger.info("[QC] Running quality check hook via HookRunner")

        temp_file = None
        try:
            # Write YAML to temp file for HookRunner
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write(yaml_content)
                temp_file = Path(f.name)

            # Run via HookRunner for structured results
            hook_result = await self.hook_runner.run(
                repo="knowledge",
                hook_name="activity_qc",
                input_file=temp_file,
                timeout=30,
            )

            # Convert HookResult to our format
            issues = [
                f"[{i.code}] {i.message}" for i in hook_result.blocking_issues
            ]
            warnings = [
                f"[{i.code}] {i.message}" for i in hook_result.advisory_issues
            ]

            logger.info(
                f"[QC] Result: passed={hook_result.passed}, "
                f"issues={len(issues)}, warnings={len(warnings)}"
            )

            return hook_result.passed, issues, warnings

        except asyncio.TimeoutError:
            logger.error("QC hook timed out")
            return False, ["QC hook timed out after 30s"], []
        except Exception as e:
            logger.exception(f"QC hook execution failed: {e}")
            return False, [f"QC hook execution failed: {e}"], []
        finally:
            # Clean up temp file
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    async def audit_quality(
        self, elevated_yaml: str, activity_id: str, is_final_attempt: bool = False
    ) -> dict:
        """
        Audit activity quality using BabyBrains voice standards.

        Spawns a fresh sub-agent to grade the activity against:
        - Voice Elevation Rubric criteria
        - A+ reference activity (gold standard)

        Args:
            elevated_yaml: The elevated YAML content to audit
            activity_id: Activity ID for logging
            is_final_attempt: If True, use extended timeout (10 min vs 5 min) - D28

        Returns:
            dict with grade, passed, issues, philosophy info, and recommendation

        Raises:
            ValueError: If elevated_yaml is empty or activity_id is missing
        """
        # Input validation
        if not elevated_yaml or not elevated_yaml.strip():
            logger.error("audit_quality called with empty elevated_yaml")
            return {
                "grade": "F",
                "passed": False,
                "issues": [{"category": "input", "issue": "Empty YAML provided", "fix": "Ensure elevation produces output"}],
                "philosophy_found": [],
                "philosophy_missing": [],
                "australian_voice": False,
                "rationale_quality": "unknown",
                "recommendation": "Cannot audit empty content",
            }

        if not activity_id:
            logger.error("audit_quality called without activity_id")
            activity_id = "unknown"

        # Load grading context
        rubric_path = Path("/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md")
        reference_path = Path(
            "/home/squiz/code/knowledge/data/canonical/activities/practical_life/"
            "ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml"
        )

        # Rubric is REQUIRED for meaningful audit
        if rubric_path.exists():
            rubric = rubric_path.read_text()
        else:
            logger.error(f"CRITICAL: Voice Rubric not found: {rubric_path}")
            return {
                "grade": "F",
                "passed": False,
                "issues": [{"category": "system", "issue": "Voice Rubric file missing", "fix": f"Ensure file exists at {rubric_path}"}],
                "philosophy_found": [],
                "philosophy_missing": [],
                "australian_voice": False,
                "rationale_quality": "unknown",
                "recommendation": "Cannot audit without rubric - system configuration error",
            }

        # Reference is optional but recommended
        if reference_path.exists():
            reference = reference_path.read_text()
        else:
            logger.warning(f"Reference activity not found: {reference_path}")
            reference = "Reference not found - grade based on rubric only"

        audit_prompt = f"""You are a SKEPTICAL quality auditor for BabyBrains Activity Atoms.

Your job is to FIND REAL PROBLEMS, not rubber-stamp approval. Be adversarial but fair.

## GRADING RUBRIC
{rubric}

## REFERENCE A+ ACTIVITY (Gold Standard)
```yaml
{reference}
```

## ACTIVITY TO AUDIT
```yaml
{elevated_yaml}
```

## BLOCKING vs ADVISORY ISSUES

### BLOCKING ISSUES (must fail - Grade B+ maximum):
- **Em-dashes (—)**: ANY em-dash = automatic B+ max. No exceptions.
- **Superlatives**: amazing, incredible, perfect, best, wonderful, fantastic, extraordinary
  - EXCEPTIONS (these are OK): "works best", "try your best", "best interests of the child", "best practices", "not perfect", "doesn't need to be perfect", "perfect the skill", "extraordinary absorptive", "extraordinary to your baby", "incredible focus"
- **Pressure language**: "you need to", "you must", "never allow", "always ensure", "crucial that you"
- **Formal transitions at sentence START**: Moreover, Furthermore, Additionally, Consequently, Nevertheless
  - OK mid-sentence: "this is furthermore supported by..."
- **American spelling**: mom (should be mum), diaper (nappy), stroller (pram), pacifier (dummy)
- **Missing philosophy in rationale**: Rationale MUST connect to at least one Montessori principle
- **Sales-y language**: "unlock your baby's potential", "supercharge development", "transform your parenting"

### ADVISORY ISSUES (note but do NOT fail):
- Minor word choice preferences
- Slight variations in sentence length
- Stylistic differences that don't violate explicit rubric rules
- Sentence structure you might write differently
- Field ordering within YAML

## AUDIT CHECKLIST (answer each honestly)

1. **Em-dash scan**: Search EVERY field. Found any (—)? If yes: BLOCKING.
2. **Superlative scan**: Check for forbidden words. Context matters - check exceptions list.
3. **Pressure language**: Any guilt-inducing "you must/need to" phrasing?
4. **Formal transitions**: Do sentences START with Moreover/Furthermore/Additionally?
5. **Spelling check**: Any American spellings slip through?
6. **Philosophy in rationale**: Does rationale connect observable to philosophy? If just "this helps development" with no Montessori principle = BLOCKING.
7. **Australian voice**: Understated confidence, not preachy? Cost-aware where relevant?

## PHILOSOPHY CHECK
Which of these 6 principles appear (need at least 2 for Grade A)?
- Cosmic View (meaningful work, contribution)
- Spiritual Embryo (child develops from within)
- Adult as Obstacle (parent self-reflection)
- Freedom Within Limits (boundaries as loving structure)
- Transformed Adult (adult self-regulation)
- Creating Conditions Not Outcomes (reduce anxiety)

## GRADING LOGIC
- **Grade A**: Zero BLOCKING issues + philosophy integrated + Australian voice
- **Grade B+**: 1-2 minor BLOCKING issues (fixable in one pass)
- **Grade B**: Multiple BLOCKING issues or weak philosophy
- **Grade C**: Significant problems across multiple areas
- **Grade F**: Audit failure or unusable content

**CRITICAL**: Do NOT approve Grade A unless you can honestly say "I searched for problems and found none."

Return ONLY valid JSON (no markdown, no explanation):
{{
  "grade": "A",
  "passed": true,
  "issues": [],
  "blocking_issues": [],
  "advisory_notes": [],
  "philosophy_found": ["cosmic_view", "spiritual_embryo", "adult_as_obstacle", "freedom_within_limits", "transformed_adult", "creating_conditions"],
  "philosophy_missing": [],
  "australian_voice": true,
  "rationale_quality": "excellent",
  "recommendation": "Ready for production - passed adversarial review"
}}

OR if blocking issues found:
{{
  "grade": "B+",
  "passed": false,
  "issues": [
    {{"category": "anti-pattern", "issue": "Em-dash found in description field", "fix": "Replace with period or comma", "blocking": true}},
    {{"category": "philosophy", "issue": "Rationale lacks Montessori connection", "fix": "Add 'Spiritual Embryo' principle - child developing from within", "blocking": true}}
  ],
  "blocking_issues": ["em-dash in description", "rationale missing philosophy"],
  "advisory_notes": ["Could vary sentence length more in tips"],
  "philosophy_found": ["cosmic_view"],
  "philosophy_missing": ["spiritual_embryo", "adult_as_obstacle", "transformed_adult"],
  "australian_voice": true,
  "rationale_quality": "needs_philosophy",
  "recommendation": "Fix 2 blocking issues: em-dash removal + add philosophy to rationale"
}}
"""

        # D28/D108: Use STAGE_TIMEOUTS for audit subprocess timeout
        # Old hardcoded 300s/600s was insufficient — audit consistently timed out
        base_timeout = self.STAGE_TIMEOUTS.get("quality_audit", 900)
        effective_timeout = base_timeout if not is_final_attempt else int(base_timeout * 1.2)
        logger.info(f"Running quality audit for {activity_id} (timeout={effective_timeout}s, final={is_final_attempt})")

        # Use SubAgentExecutor for fresh context
        # D34: sandbox=False - sandboxing causes EROFS errors with claude CLI config
        result = await self.sub_executor.spawn(
            task=audit_prompt,
            context={"activity_id": activity_id, "audit_type": "voice_quality"},
            timeout=effective_timeout,
            sandbox=False,
        )

        # D28: Robust JSON extraction with truncation detection
        parsed_result, error = self._extract_audit_json(result.output if result.output else "")

        if parsed_result:
            logger.info(f"Quality audit result: Grade {parsed_result.get('grade')}")
            return parsed_result

        # Log full response on failure for diagnostics
        if result.output:
            logger.error(f"Failed to parse audit response: {error}")
            logger.error(f"Full raw response ({len(result.output)} chars):\n{result.output}")
        else:
            logger.error(f"No audit output received. Error: {result.error}")

        # Fallback on failure with diagnostics
        return {
            "grade": "F",
            "passed": False,
            "issues": [
                {
                    "category": "audit",
                    "issue": f"Audit parse failed: {error or result.error or 'unknown error'}",
                    "fix": "Manual review required",
                }
            ],
            "philosophy_found": [],
            "philosophy_missing": [],
            "australian_voice": False,
            "rationale_quality": "unknown",
            "recommendation": "Audit failed - requires manual review",
            "raw_output_length": len(result.output) if result.output else 0,
        }

    def _extract_audit_json(self, raw_output: str) -> tuple[Optional[dict], Optional[str]]:
        """
        D28: Extract and validate JSON from audit response with truncation detection.

        Returns:
            Tuple of (parsed_dict, error_message)
        """
        if not raw_output:
            return None, "Empty output received"

        output = raw_output.strip()
        json_content = output

        # Handle markdown code blocks robustly
        if "```json" in output:
            parts = output.split("```json", 1)
            if len(parts) > 1:
                remaining = parts[1]
                if "```" in remaining:
                    json_content = remaining.split("```", 1)[0].strip()
                else:
                    # Truncation detected: no closing ```
                    logger.warning("Truncation detected: no closing ``` found after ```json")
                    json_content = remaining.strip()
        elif "```" in output:
            parts = output.split("```", 1)
            if len(parts) > 1:
                remaining = parts[1]
                if "```" in remaining:
                    json_content = remaining.split("```", 1)[0].strip()
                else:
                    json_content = remaining.strip()

        # Pre-validate JSON structure
        json_content = json_content.strip()
        if not json_content.startswith("{"):
            return None, f"JSON doesn't start with '{{': {json_content[:100]}"

        # Check for truncation (unbalanced braces)
        open_braces = json_content.count("{")
        close_braces = json_content.count("}")
        if open_braces != close_braces:
            logger.warning(f"Truncated JSON detected: {open_braces} open braces, {close_braces} close braces")
            # Attempt to repair by adding missing close braces
            if close_braces < open_braces:
                missing = open_braces - close_braces
                json_content = json_content.rstrip() + ("}" * missing)
                logger.info(f"Attempted JSON repair: added {missing} closing braces")

        # Check for unbalanced brackets
        open_brackets = json_content.count("[")
        close_brackets = json_content.count("]")
        if close_brackets < open_brackets:
            missing = open_brackets - close_brackets
            # Find last ] or } and insert before final }
            json_content = json_content.rstrip().rstrip("}") + ("]" * missing) + "}"
            logger.info(f"Attempted JSON repair: added {missing} closing brackets")

        try:
            result = json.loads(json_content)
            return result, None
        except json.JSONDecodeError as e:
            # Log context around error for debugging
            start = max(0, e.pos - 50)
            end = min(len(json_content), e.pos + 50)
            context = json_content[start:end]
            return None, f"Invalid JSON at position {e.pos}: {e.msg}. Context: ...{context}..."

    async def convert_activity(
        self, raw_id: str, feedback: Optional[str] = None, is_final_attempt: bool = False
    ) -> ConversionResult:
        """
        Run the full conversion pipeline for a single activity.

        Pipeline stages:
            1. Ingest - Load and validate raw activity
            2. Research - Find principles, safety, sources
            3. Transform - Build 34-section canonical YAML
            4. Elevate - Apply BabyBrains voice (with feedback if retrying)
            5. Validate - Structure and cross-reference checks
            6. QC Hook - Deterministic quality gate
            7. Quality Audit - Voice rubric grading (Grade A required)

        Args:
            raw_id: Activity raw ID
            feedback: Optional feedback from previous attempt for intelligent retry

        Returns:
            ConversionResult with status and details
        """
        logger.info(f"Starting conversion for: {raw_id}")

        # Initialize scratch pad for this conversion
        # Deterministic session_id enables cache persistence across runs
        session_id = f"convert_{raw_id}"
        self.scratch_pad = ScratchPad(session_id=session_id)

        # C-3: SPEC COMPLIANCE - Start SessionManager session
        await self.session.start_session(repo="knowledge")
        logger.debug(f"Session started: {self.session.current_session_id}")

        try:
            # Stage 1: INGEST
            success, ingest_output, error = await self._execute_ingest(raw_id)
            self.session.record_skill("ingest_activity")
            if not success:
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=f"Ingest failed: {error}",
                )

            self.scratch_pad.add(
                "ingest_output", ingest_output, step=1, skill_name="ingest_activity"
            )

            # Check if should skip
            if ingest_output.get("should_skip"):
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.SKIPPED,
                    skip_reason=ingest_output.get("skip_reason", "Marked for skip"),
                )

            # Stage 2: RESEARCH
            success, research_output, error = await self._execute_research(ingest_output)
            self.session.record_skill("research_activity")
            if not success:
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=f"Research failed: {error}",
                )

            self.scratch_pad.add(
                "research_output",
                research_output,
                step=2,
                skill_name="research_activity",
            )

            # Stage 3: TRANSFORM
            success, transform_output, error = await self._execute_transform(
                ingest_output, research_output
            )
            self.session.record_skill("transform_activity")
            if not success:
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=f"Transform failed: {error}",
                )

            self.scratch_pad.add(
                "transform_output",
                transform_output,
                step=3,
                skill_name="transform_activity",
            )

            canonical_yaml = transform_output.get("canonical_yaml", "")
            canonical_id = transform_output.get("canonical_id", "")
            file_path = transform_output.get("file_path", "")

            # A-2: CRITICAL FIX - Validate ALL required transform outputs
            missing_fields = []
            if not canonical_yaml:
                missing_fields.append("canonical_yaml")
            if not canonical_id:
                missing_fields.append("canonical_id")
            if not file_path:
                missing_fields.append("file_path")

            if missing_fields:
                error_msg = f"Transform missing required fields: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=error_msg,
                )

            # A-3: DETERMINISTIC FIX - Ensure canonical_slug matches canonical_id
            # LLMs sometimes generate incorrect formats (e.g., adding -au suffix)
            canonical_yaml = self._fix_canonical_slug(canonical_yaml, canonical_id)

            # Stage 4: ELEVATE VOICE
            # Pass feedback from previous attempt if this is a retry
            success, elevate_output, error = await self._execute_elevate(
                canonical_yaml, feedback=feedback
            )
            self.session.record_skill("elevate_voice_activity")
            if not success:
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=f"Elevate failed: {error}",
                )

            self.scratch_pad.add(
                "elevate_output",
                elevate_output,
                step=4,
                skill_name="elevate_voice_activity",
            )

            # D38: Validate elevate_output has required fields
            if not elevate_output or not isinstance(elevate_output, dict):
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=f"Elevate returned invalid output type: {type(elevate_output)}",
                )

            elevated_yaml = elevate_output.get("elevated_yaml")
            if not elevated_yaml:
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error="Elevate output missing 'elevated_yaml' - no content generated",
                )

            # Check voice grade
            grade = elevate_output.get("grade", "")
            if grade and grade != "A":
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.REVISION_NEEDED,
                    error=f"Voice grade {grade}: {elevate_output.get('issues', [])}",
                    elevated_yaml=elevated_yaml,
                )

            # DETERMINISTIC FIXES after ELEVATE (LLMs modify IDs/slugs during elevation)
            # Fix canonical_id first (ELEVATE may rename it), then slug derives from ID
            elevated_yaml = self._fix_canonical_id(elevated_yaml, canonical_id)
            elevated_yaml = self._fix_canonical_slug(elevated_yaml, canonical_id)

            # D35: DETERMINISTIC FIX - Ensure principle slugs use underscores
            # LLMs sometimes generate slugs like 'practical-life' instead of 'practical_life'
            elevated_yaml = self._fix_principle_slugs(elevated_yaml)

            # H7: Fix age range to match original (ELEVATE may incorrectly change it)
            elevated_yaml = self._fix_age_range(elevated_yaml, canonical_yaml)

            # D80: Post-ELEVATE dash cleanup - LLM generates new dashes despite prompt
            # instructions. Deterministic fix prevents token-wasting retries.
            elevated_yaml = self._remove_dashes(elevated_yaml)

            # V1: Quick pre-validation -- catch obvious failures before expensive QC/audit
            quick_issues = self._quick_validate(elevated_yaml)
            if quick_issues:
                issue_msgs = [i["issue"] for i in quick_issues]
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.QC_FAILED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    qc_issues=issue_msgs,
                    elevated_yaml=elevated_yaml,
                )

            # D78: Early truncation detection - check before expensive QC/AUDIT stages
            # All canonical Activity Atoms end with parent_search_terms list
            is_truncated, truncation_reason = self._detect_truncation(elevated_yaml)
            if is_truncated:
                logger.warning(f"[TRUNCATION] Detected: {truncation_reason}")
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.QC_FAILED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    qc_issues=[f"Output truncated: {truncation_reason}"],
                    elevated_yaml=elevated_yaml,
                )

            # C-1: SPEC COMPLIANCE - Adversarial verification via SubAgentExecutor
            # Per masterclass [4147s]: Use fresh context to verify work
            try:
                verification = await self.sub_executor.verify_adversarially(
                    output={"yaml": elevated_yaml[:15000], "grade": grade or "A"},
                    skill_name="elevate_voice_activity",
                    persona="senior Montessori education specialist",
                )
                self.scratch_pad.add(
                    "adversarial_verification",
                    {
                        "passed": verification.passed,
                        "issues": verification.issues,
                        "duration_ms": verification.duration_ms,
                    },
                    step=5,
                    skill_name="adversarial_check",
                )
                if not verification.passed:
                    logger.warning(
                        f"Adversarial check found issues: {verification.issues}"
                    )
                    # Don't fail, but add to warnings
            except Exception as adv_err:
                logger.warning(f"Adversarial verification skipped: {adv_err}")

            # Stage 5: VALIDATE
            success, validate_output, error = await self._execute_validate(
                elevated_yaml, file_path, canonical_id
            )
            self.session.record_skill("validate_activity")
            if not success:
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=f"Validate failed: {error}",
                )

            self.scratch_pad.add(
                "validate_output",
                validate_output,
                step=5,
                skill_name="validate_activity",
            )

            # Fix guidance/materials misclassification before checking
            validate_output = self._fix_validation_misclassification(validate_output)

            validation_result = validate_output.get("validation_result", {})
            if not validation_result.get("passed", False):
                blocking_issues = validation_result.get("blocking_issues", [])
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.FAILED,
                    error=f"Validation failed: {blocking_issues}",
                    elevated_yaml=elevated_yaml,
                )

            # Stage 6: QC HOOK
            qc_passed, qc_issues, qc_warnings = await self._run_qc_hook(elevated_yaml)
            if not qc_passed:
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.QC_FAILED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    qc_issues=qc_issues,
                    qc_warnings=qc_warnings,
                    elevated_yaml=elevated_yaml,
                )

            # Stage 7: QUALITY AUDIT
            logger.info(f"Stage 7: QUALITY AUDIT for {raw_id} (final={is_final_attempt})")
            audit = await self.audit_quality(
                elevated_yaml=elevated_yaml,
                activity_id=raw_id,
                is_final_attempt=is_final_attempt,  # D28: Extended timeout on final attempt
            )

            # Store audit results in scratch pad for retry reflection
            self.scratch_pad.add(
                "quality_audit",
                audit,
                step=7,
                skill_name="quality_audit",
            )
            # Also store elevated_yaml for retry access
            self.scratch_pad.add(
                "elevated_yaml",
                elevated_yaml,
                step=7,
                skill_name="quality_audit",
            )

            # Check if grade is acceptable (A, A+, A- all pass)
            grade = audit.get("grade", "Unknown")
            grade_str = str(grade).strip().upper() if grade else ""
            is_grade_a = grade_str.startswith("A") and grade_str not in ("AB", "AC", "AD", "AF")

            if not audit.get("passed") or not is_grade_a:
                logger.warning(f"Quality audit: Grade {grade} (requires A/A+/A-)")

                for issue in audit.get("issues", []):
                    if isinstance(issue, dict):
                        logger.warning(f"  [{issue.get('category')}] {issue.get('issue')}")
                        if issue.get("fix"):
                            logger.info(f"    Fix: {issue.get('fix')}")

                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.REVISION_NEEDED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    error=f"Quality audit: Grade {grade} (need A/A+/A-)",
                    qc_warnings=[
                        f"[{i.get('category')}] {i.get('issue')}"
                        for i in audit.get("issues", [])
                        if isinstance(i, dict)
                    ],
                    elevated_yaml=elevated_yaml,
                )

            logger.info(f"Quality audit PASSED: Grade {grade}")

            # SUCCESS - Ready for human review
            logger.info(f"Conversion successful for {raw_id}")
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.DONE,
                canonical_id=canonical_id,
                file_path=file_path,
                qc_issues=[],
                qc_warnings=qc_warnings,
                elevated_yaml=elevated_yaml,
            )

        except Exception as e:
            logger.exception(f"Unexpected error converting {raw_id}")
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.FAILED,
                error=f"Unexpected error: {e}",
            )

        finally:
            # B-2: HIGH FIX - Always save scratch pad for debugging
            if self.scratch_pad:
                try:
                    scratch_dir = Path.home() / ".atlas" / "scratch"
                    scratch_dir.mkdir(parents=True, exist_ok=True)
                    scratch_path = scratch_dir / f"{session_id}.json"
                    self.scratch_pad.to_file(scratch_path)
                    logger.debug(f"Saved scratch pad to: {scratch_path}")
                except Exception as save_err:
                    logger.warning(f"Failed to save scratch pad: {save_err}")

            # C-3: SPEC COMPLIANCE - End session properly
            try:
                await self.session.save_state()
                await self.session.end_session()
                logger.debug("Session ended")
            except Exception as sess_err:
                logger.warning(f"Failed to end session: {sess_err}")

    def _format_issue_feedback(self, issues: list[dict]) -> str:
        """
        Format QC issues into specific, actionable feedback with examples.

        D36: Specific Wait Pattern Feedback
        Groups issues by type and provides before/after examples.

        Args:
            issues: List of issue dicts from QC hook

        Returns:
            Formatted feedback string with specific fix instructions
        """
        # Group issues by category
        pressure_issues = []
        superlative_issues = []
        emdash_issues = []
        other_issues = []

        for issue in issues:
            code = issue.get("code", "").upper()
            category = issue.get("category", "").lower()
            msg = issue.get("issue", issue.get("msg", ""))

            if "PRESSURE" in code or "pressure" in category:
                pressure_issues.append(msg)
            elif "SUPERLATIVE" in code or "superlative" in category:
                superlative_issues.append(msg)
            elif "EM_DASH" in code or "emdash" in category or "em-dash" in msg.lower():
                emdash_issues.append(msg)
            else:
                other_issues.append(f"[{category}] {msg}")

        sections = []

        if pressure_issues:
            section = """### PRESSURE LANGUAGE - MUST FIX (Automatic Failure)

Found instances:
"""
            for issue in pressure_issues[:5]:
                section += f"- {issue}\n"

            section += """
REPLACEMENTS TO USE:
- "You need to" → "It helps to" OR "Try" OR just describe what happens
- "You must" → "What works is" OR omit entirely
- "Never allow" → "Avoid" OR phrase as positive guidance
- "Make sure to" → "When you can" OR just state the action
- "You should always" → "It often helps to" OR describe benefits

EXAMPLE TRANSFORMS:
- BEFORE: "You need to watch closely during this activity."
- AFTER: "Watching closely lets you see the small moments of discovery."

- BEFORE: "Never allow your child to..."
- AFTER: "If your child shows frustration, that's a signal to..."
"""
            sections.append(section)

        if superlative_issues:
            section = """### SUPERLATIVES - MUST FIX (Automatic Failure)

Found instances:
"""
            for issue in superlative_issues[:5]:
                section += f"- {issue}\n"

            section += """
BANNED WORDS (automatic QC failure):
amazing, incredible, wonderful, fantastic, extraordinary, perfect, optimal,
best, ideal, exceptional, remarkable, outstanding, superb, brilliant, tremendous

REPLACEMENTS TO USE:
- "the best" → "an effective" OR "what works well"
- "perfect" → "good" OR "suitable" OR just omit
- "optimal" → "effective" OR "helpful"
- "amazing/incredible/extraordinary" → describe the observation factually
- "essential" → "important" OR "helpful"
- "remarkable/outstanding" → "noticeable" OR describe what you observed

EXAMPLE TRANSFORMS:
- BEFORE: "This is the perfect time to introduce..."
- AFTER: "Around this age, many children show readiness for..."

- BEFORE: "The extraordinary capacity of..."
- AFTER: "The capacity of..." (just omit the superlative)

- BEFORE: "The best approach is to..."
- AFTER: "What often works is to..."

CRITICAL: Before outputting, search for ALL these words and remove them.
"""
            sections.append(section)

        if emdash_issues:
            section = """### EM-DASHES - MUST FIX (Automatic Failure)

Found em-dashes (—) in the output. Replace with:
- Comma for short pauses
- Period and new sentence for longer breaks
- Parentheses for asides
- Colon for explanations

NEVER use the em-dash character (—).
"""
            sections.append(section)

        if other_issues:
            section = "### OTHER ISSUES\n\n"
            for issue in other_issues[:5]:
                section += f"- {issue}\n"
            sections.append(section)

        return "\n".join(sections)

    async def reflect_on_failure(
        self,
        failed_yaml: str,
        issues: list[dict],
        grade: str,
    ) -> str:
        """
        Apply the "Wait" pattern to reflect on why an activity failed quality audit.

        D36: Enhanced with specific feedback and before/after examples.
        Uses Anthropic introspection research (89.3% blind spot reduction).

        Args:
            failed_yaml: The YAML that failed quality audit
            issues: List of issues from quality audit
            grade: Grade received (B+, B, C, F)

        Returns:
            Reflection feedback to pass to next attempt
        """
        # Input validation - ensure issues is a list of dicts
        if not isinstance(issues, list):
            issues = []
        # Filter to only dict items and limit to prevent prompt overflow
        valid_issues = [i for i in issues[:20] if isinstance(i, dict)]

        if not grade:
            grade = "Unknown"

        # D36: Format issues with specific, actionable feedback
        specific_feedback = self._format_issue_feedback(valid_issues)

        # If no specific feedback generated, use generic format
        if not specific_feedback.strip():
            specific_feedback = "\n".join(
                f"- [{i.get('category', 'unknown')}] {i.get('issue', 'No description')}"
                for i in valid_issues
            )

        # D36: Enhanced "Wait" pattern with specific fix instructions
        reflection_prompt = f"""## CRITICAL: RE-ELEVATION INSTRUCTIONS

The previous attempt received **Grade {grade}** (required: A).

{specific_feedback}

## WHAT YOU MUST DO

1. **SEARCH your output** for each banned word/phrase before submitting
2. **REPLACE** every instance using the alternatives above
3. **DO NOT** use pressure language even when the source material does
4. **DO NOT** add superlatives for emphasis - describe observations factually

## BEFORE SUBMITTING

Run this mental check:
- [ ] No "you need to", "you must", "never allow", "make sure"
- [ ] No "best", "perfect", "optimal", "amazing", "incredible"
- [ ] No em-dashes (—)
- [ ] No "Moreover", "Furthermore", "Additionally" at sentence start

If ANY of these appear, rewrite that sentence before outputting.
"""

        logger.info(f"Applying enhanced 'Wait' pattern reflection for Grade {grade}")

        # Use SubAgentExecutor for fresh reflection
        # D34: sandbox=False - sandboxing causes EROFS errors
        result = await self.sub_executor.spawn(
            task=reflection_prompt,
            context={"grade": grade, "issue_count": len(valid_issues)},
            timeout=120,  # 2 min for reflection
            sandbox=False,
        )

        if result.success and result.output:
            logger.info("Reflection generated successfully")
            return result.output
        else:
            # Fallback to formatted issues if reflection fails
            logger.warning("Reflection failed, using formatted issues as feedback")
            return f"Previous attempt failed with Grade {grade}.\n\n{specific_feedback}"

    async def _convert_from_cached_transform(
        self,
        raw_id: str,
        cached_transform: dict,
        feedback: Optional[str] = None,
        is_final_attempt: bool = False,
    ) -> ConversionResult:
        """
        D78: Run stages 4-7 from cached transform output.

        This method is used on retry to skip the expensive INGEST/RESEARCH/TRANSFORM
        stages which produce identical output. Only ELEVATE uses the feedback.

        Args:
            raw_id: Activity ID
            cached_transform: Dict with canonical_yaml, canonical_id, file_path
            feedback: Feedback from previous attempt
            is_final_attempt: Whether this is the final retry attempt

        Returns:
            ConversionResult with status
        """
        canonical_yaml = cached_transform["canonical_yaml"]
        canonical_id = cached_transform["canonical_id"]
        file_path = cached_transform["file_path"]

        logger.info(f"[CACHED] Starting from stage 4 (ELEVATE) for {raw_id}")

        # Stage 4: ELEVATE VOICE (with feedback)
        success, elevate_output, error = await self._execute_elevate(
            canonical_yaml, feedback=feedback
        )
        self.session.record_skill("elevate_voice_activity")
        if not success:
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.FAILED,
                error=f"Elevate failed: {error}",
            )

        self.scratch_pad.add(
            "elevate_output",
            elevate_output,
            step=4,
            skill_name="elevate_voice_activity",
        )

        # D38: Validate elevate_output
        if not elevate_output or not isinstance(elevate_output, dict):
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.FAILED,
                error=f"Elevate returned invalid output type: {type(elevate_output)}",
            )

        elevated_yaml = elevate_output.get("elevated_yaml")
        if not elevated_yaml:
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.FAILED,
                error="Elevate output missing 'elevated_yaml' - no content generated",
            )

        # Check voice grade from ELEVATE self-assessment
        grade = elevate_output.get("grade", "")
        if grade and grade != "A":
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.REVISION_NEEDED,
                error=f"Voice grade {grade}: {elevate_output.get('issues', [])}",
                elevated_yaml=elevated_yaml,
            )

        # Deterministic fixes (ELEVATE may modify IDs/slugs during elevation)
        elevated_yaml = self._fix_canonical_id(elevated_yaml, canonical_id)
        elevated_yaml = self._fix_canonical_slug(elevated_yaml, canonical_id)
        elevated_yaml = self._fix_principle_slugs(elevated_yaml)

        # H7: Fix age range to match original (ELEVATE may incorrectly change it)
        elevated_yaml = self._fix_age_range(elevated_yaml, canonical_yaml)

        # D80: Post-ELEVATE dash cleanup (cached transform path)
        elevated_yaml = self._remove_dashes(elevated_yaml)

        # V1: Quick pre-validation -- catch obvious failures before expensive QC/audit
        quick_issues = self._quick_validate(elevated_yaml)
        if quick_issues:
            issue_msgs = [i["issue"] for i in quick_issues]
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.QC_FAILED,
                canonical_id=canonical_id,
                file_path=file_path,
                qc_issues=issue_msgs,
                elevated_yaml=elevated_yaml,
            )

        # D78: Early truncation detection
        is_truncated, truncation_reason = self._detect_truncation(elevated_yaml)
        if is_truncated:
            logger.warning(f"[TRUNCATION] Detected: {truncation_reason}")
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.QC_FAILED,
                canonical_id=canonical_id,
                file_path=file_path,
                qc_issues=[f"Output truncated: {truncation_reason}"],
                elevated_yaml=elevated_yaml,
            )

        # Adversarial check (non-blocking)
        try:
            verification = await self.sub_executor.verify_adversarially(
                output={"yaml": elevated_yaml[:15000], "grade": grade or "A"},
                skill_name="elevate_voice_activity",
                persona="senior Montessori education specialist",
            )
            if not verification.passed:
                logger.warning(f"Adversarial check found issues: {verification.issues}")
        except Exception as adv_err:
            logger.warning(f"Adversarial verification skipped: {adv_err}")

        # Stage 5: VALIDATE
        success, validate_output, error = await self._execute_validate(
            elevated_yaml, file_path, canonical_id
        )
        self.session.record_skill("validate_activity")
        if not success:
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.FAILED,
                error=f"Validate failed: {error}",
            )

        # Fix guidance/materials misclassification before checking
        validate_output = self._fix_validation_misclassification(validate_output)

        validation_result = validate_output.get("validation_result", {})
        if not validation_result.get("passed", False):
            blocking_issues = validation_result.get("blocking_issues", [])
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.FAILED,
                error=f"Validation failed: {blocking_issues}",
                elevated_yaml=elevated_yaml,
            )

        # Stage 6: QC HOOK
        qc_passed, qc_issues, qc_warnings = await self._run_qc_hook(elevated_yaml)
        if not qc_passed:
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.QC_FAILED,
                canonical_id=canonical_id,
                file_path=file_path,
                qc_issues=qc_issues,
                qc_warnings=qc_warnings,
                elevated_yaml=elevated_yaml,
            )

        # Stage 7: QUALITY AUDIT
        logger.info(f"Stage 7: QUALITY AUDIT for {raw_id} (final={is_final_attempt})")
        audit = await self.audit_quality(
            elevated_yaml=elevated_yaml,
            activity_id=raw_id,
            is_final_attempt=is_final_attempt,
        )

        self.scratch_pad.add("quality_audit", audit, step=7, skill_name="quality_audit")
        self.scratch_pad.add("elevated_yaml", elevated_yaml, step=7, skill_name="quality_audit")

        # Check grade
        audit_grade = audit.get("grade", "Unknown")
        grade_str = str(audit_grade).strip().upper() if audit_grade else ""
        is_grade_a = grade_str.startswith("A") and grade_str not in ("AB", "AC", "AD", "AF")

        if not audit.get("passed") or not is_grade_a:
            logger.warning(f"Quality audit: Grade {audit_grade} (requires A/A+/A-)")
            return ConversionResult(
                activity_id=raw_id,
                status=ActivityStatus.REVISION_NEEDED,
                canonical_id=canonical_id,
                file_path=file_path,
                error=f"Quality audit: Grade {audit_grade} (need A/A+/A-)",
                qc_warnings=[
                    f"[{i.get('category')}] {i.get('issue')}"
                    for i in audit.get("issues", [])
                    if isinstance(i, dict)
                ],
                elevated_yaml=elevated_yaml,
            )

        logger.info(f"Quality audit PASSED: Grade {audit_grade}")
        return ConversionResult(
            activity_id=raw_id,
            status=ActivityStatus.DONE,
            canonical_id=canonical_id,
            file_path=file_path,
            qc_issues=[],
            qc_warnings=qc_warnings,
            elevated_yaml=elevated_yaml,
        )

    async def convert_with_retry(
        self,
        raw_id: str,
        max_retries: int = 2,
    ) -> ConversionResult:
        """
        Convert activity with intelligent retry using the "Wait" pattern.

        D78: Uses stage caching - INGEST/RESEARCH/TRANSFORM run once, only
        ELEVATE onward is retried. This reduces retry time by ~60-70%.

        If quality audit fails (not Grade A), applies reflection to understand
        why and retries with learned context. Each retry learns from what
        went wrong, not just hopes for different output.

        Args:
            raw_id: Activity ID to convert
            max_retries: Max retry attempts (default 2 retries = 3 total attempts)

        Returns:
            ConversionResult with final status

        Raises:
            ValueError: If raw_id is empty or max_retries is negative
        """
        # Input validation
        if not raw_id or not raw_id.strip():
            raise ValueError("raw_id is required and cannot be empty")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        last_result: Optional[ConversionResult] = None
        feedback: Optional[str] = None
        cached_transform: Optional[dict] = None  # D78: Cache for retries

        # D78+: Reload cached transform from disk if available (persists across runs)
        # Sanitize raw_id to prevent path traversal (defense-in-depth)
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_id)
        scratch_path = Path.home() / ".atlas" / "scratch" / f"convert_{safe_id}.json"
        if scratch_path.exists():
            disk_pad = ScratchPad.from_file(scratch_path)
            if disk_pad is not None:
                transform_output = disk_pad.get("transform_output")
                if transform_output and isinstance(transform_output, dict):
                    candidate = {
                        "canonical_yaml": transform_output.get("canonical_yaml", ""),
                        "canonical_id": transform_output.get("canonical_id", ""),
                        "file_path": transform_output.get("file_path", ""),
                    }
                    if all(candidate.values()):
                        cached_transform = candidate
                        logger.info(
                            f"[D78+] Resuming from cached transform (disk): {scratch_path.name}"
                        )

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt}/{max_retries} for {raw_id}")
                print(f"\nApplying 'Wait' pattern reflection...")
                print(f"Retry attempt {attempt}/{max_retries} with learned context\n")

            # D28: Mark final attempt for extended timeout in quality audit
            is_final = (attempt >= max_retries)

            # D78+: Use cached transform if available (from disk or prior attempt)
            if cached_transform is None:
                # Full pipeline - stages 1-7
                result = await self.convert_activity(raw_id, feedback=feedback, is_final_attempt=is_final)

                # Cache transform output for potential retries
                if self.scratch_pad:
                    transform_output = self.scratch_pad.get("transform_output")
                    if transform_output and isinstance(transform_output, dict):
                        cached_transform = {
                            "canonical_yaml": transform_output.get("canonical_yaml", ""),
                            "canonical_id": transform_output.get("canonical_id", ""),
                            "file_path": transform_output.get("file_path", ""),
                        }
                        # Only cache if all fields present
                        if not all(cached_transform.values()):
                            cached_transform = None
                        else:
                            logger.info(f"[D78] Cached transform output for retries")
            else:
                # D78: Cached retry - stages 4-7 only (skips INGEST/RESEARCH/TRANSFORM)
                logger.info(f"[D78] Using cached transform - skipping stages 1-3")
                result = await self._convert_from_cached_transform(
                    raw_id, cached_transform, feedback=feedback, is_final_attempt=is_final
                )

            last_result = result

            # Success - Grade A achieved
            if result.status == ActivityStatus.DONE:
                if attempt > 0:
                    logger.info(f"Succeeded on attempt {attempt + 1}")
                    print(f"\nSucceeded on attempt {attempt + 1}!")
                return result

            # Check if this is a retryable quality issue
            retryable_statuses = {ActivityStatus.REVISION_NEEDED, ActivityStatus.QC_FAILED}
            if result.status not in retryable_statuses:
                logger.info(f"Status {result.status.value} - not retrying")
                return result

            # Max retries exhausted
            if attempt >= max_retries:
                logger.warning(f"Max retries ({max_retries}) reached for {raw_id}")
                return result

            # Apply "Wait" pattern reflection for intelligent retry
            # Use QC issues if QC failed, otherwise use quality audit issues
            if result.status == ActivityStatus.QC_FAILED and result.qc_issues:
                # Convert QC issues to audit format for reflection
                issues = [
                    {"category": "QC", "issue": issue, "fix": "Review and fix"}
                    for issue in result.qc_issues
                ]
                grade = "QC_FAILED"
            else:
                # Get audit results from scratch pad
                audit = self.scratch_pad.get("quality_audit") if self.scratch_pad else {}
                if not audit:
                    audit = {"issues": [], "grade": "Unknown"}
                issues = audit.get("issues", [])
                grade = audit.get("grade", "Unknown")

            feedback = await self.reflect_on_failure(
                failed_yaml=result.elevated_yaml or "",
                issues=issues,
                grade=grade,
            )

            logger.info("Will retry with reflection feedback")
            # Show issues from either QC or quality audit
            display_issues = result.qc_issues if result.qc_issues else result.qc_warnings
            if display_issues:
                print(f"Issues from attempt {attempt + 1}:")
                for issue in display_issues[:5]:
                    print(f"  - {issue}")

        return last_result or ConversionResult(
            activity_id=raw_id,
            status=ActivityStatus.FAILED,
            error="No result from conversion attempts",
        )

    def present_for_review(
        self, result: ConversionResult, yaml_content: str
    ) -> str:
        """
        Present converted activity for human review in terminal.

        Args:
            result: Conversion result
            yaml_content: YAML content to review

        Returns:
            User decision: 'approve', 'reject', 'skip', or 'quit'
        """
        # Non-interactive detection: auto-approve Grade A, auto-reject below
        if not sys.stdin.isatty():
            if result.status == ActivityStatus.DONE:
                logger.warning("Non-interactive stdin: auto-approving Grade A result")
                return "approve"
            else:
                logger.warning(
                    f"Non-interactive stdin: auto-rejecting {result.status.value}"
                )
                return "reject"

        # Get activity metadata
        raw_activity = self.raw_activities.get(result.activity_id, {})
        domain = raw_activity.get("domain", "unknown")
        age_range = raw_activity.get("age_range", {})
        age_label = age_range.get("label", "unknown") if isinstance(age_range, dict) else str(age_range)

        # Display header
        print("\n" + "=" * 65)
        print("ACTIVITY READY FOR REVIEW")
        print("=" * 65)
        print()
        print(f"Raw ID:       {result.activity_id}")
        print(f"Canonical ID: {result.canonical_id or 'N/A'}")
        print(f"Domain:       {domain}")
        print(f"Age Range:    {age_label}")
        print()

        # QC Status
        if result.status == ActivityStatus.DONE:
            print("QC Status:    PASSED")
        elif result.status == ActivityStatus.QC_FAILED:
            print("QC Status:    FAILED")
        else:
            print(f"QC Status:    {result.status.value.upper()}")

        # Issues and warnings
        if result.qc_issues:
            print(f"Issues ({len(result.qc_issues)}):")
            for issue in result.qc_issues[:5]:
                print(f"  - {issue}")
            if len(result.qc_issues) > 5:
                print(f"  ... and {len(result.qc_issues) - 5} more")

        if result.qc_warnings:
            print(f"Warnings ({len(result.qc_warnings)}):")
            for warning in result.qc_warnings[:3]:
                print(f"  - {warning}")

        print()
        print("-" * 65)
        print("PREVIEW (first 50 lines):")
        print("-" * 65)

        # Show preview
        lines = yaml_content.split("\n")[:50]
        for line in lines:
            print(line)
        if len(yaml_content.split("\n")) > 50:
            print(f"... ({len(yaml_content.split(chr(10))) - 50} more lines)")

        print()
        print("-" * 65)
        print("[A]pprove  [R]eject  [S]kip  [V]iew Full  [Q]uit")

        # B-3: HIGH FIX - Add max attempts to prevent infinite loop
        max_attempts = 20
        attempts = 0

        while attempts < max_attempts:
            attempts += 1
            try:
                choice = input("> ").strip().lower()

                if choice in ("a", "approve"):
                    return "approve"
                elif choice in ("r", "reject"):
                    return "reject"
                elif choice in ("s", "skip"):
                    return "skip"
                elif choice in ("v", "view"):
                    # Show full content (doesn't count as attempt)
                    attempts -= 1
                    print("\n" + "=" * 65)
                    print("FULL CONTENT:")
                    print("=" * 65)
                    print(yaml_content)
                    print("=" * 65)
                    print("[A]pprove  [R]eject  [S]kip  [Q]uit")
                elif choice in ("q", "quit"):
                    return "quit"
                else:
                    remaining = max_attempts - attempts
                    print(f"Invalid choice. Use A/R/S/V/Q ({remaining} attempts remaining)")
            except (EOFError, KeyboardInterrupt):
                print("\nQuitting...")
                return "quit"

        # Too many invalid inputs, default to skip
        logger.warning(
            f"Too many invalid inputs for {result.activity_id}, defaulting to skip"
        )
        print("Too many invalid inputs. Skipping activity.")
        return "skip"

    async def elevate_existing_file(
        self, yaml_path: str, max_retries: int = 2
    ) -> ConversionResult:
        """
        Elevate an existing YAML file through stages 4-7.

        For pioneer/staging files that have content but need voice elevation.
        Runs: ELEVATE → VALIDATE → QC_HOOK → QUALITY_AUDIT

        Args:
            yaml_path: Path to existing YAML file
            max_retries: Max retry attempts for non-A grades

        Returns:
            ConversionResult with elevated_yaml if successful
        """
        path = Path(yaml_path)
        if not path.exists():
            return ConversionResult(
                activity_id=path.stem,
                status=ActivityStatus.FAILED,
                error=f"File not found: {yaml_path}",
            )

        # Extract canonical_id from filename
        canonical_id = path.stem
        activity_id = canonical_id  # Use canonical_id as activity_id for tracking

        # Read existing content
        try:
            existing_yaml = path.read_text()
        except Exception as e:
            return ConversionResult(
                activity_id=activity_id,
                status=ActivityStatus.FAILED,
                error=f"Failed to read file: {e}",
            )

        logger.info(f"[ELEVATE-EXISTING] Processing: {canonical_id}")
        logger.info(f"[ELEVATE-EXISTING] Input size: {len(existing_yaml)} chars")

        # Determine output path based on domain in file
        try:
            parsed = yaml.safe_load(existing_yaml)
            domains = parsed.get("domain", [])
            domain = domains[0] if isinstance(domains, list) and domains else "unknown"
            # Map domain names to directory names
            domain_map = {
                "practical_life": "practical_life",
                "prepared_environment": "prepared_environment",
                "feeding": "feeding",
                "movement": "movement",
                "language": "language",
                "sensory": "sensory",
                "cognitive": "cognitive",
            }
            domain_dir = domain_map.get(domain, domain)
        except Exception:
            domain_dir = "unknown"

        file_path = str(self.CANONICAL_OUTPUT_DIR / domain_dir / f"{canonical_id}.yaml")

        feedback = None
        for attempt in range(max_retries + 1):
            is_final_attempt = attempt == max_retries

            if attempt > 0:
                logger.info(f"[ELEVATE-EXISTING] Retry {attempt}/{max_retries}")

            # Stage 4: ELEVATE VOICE
            success, elevate_output, error = await self._execute_elevate(
                existing_yaml, feedback=feedback
            )
            if not success:
                logger.warning(f"[ELEVATE-EXISTING] Elevate failed: {error}")
                if not is_final_attempt:
                    feedback = f"Previous attempt failed: {error}. Please try again."
                    continue
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.FAILED,
                    error=f"Elevate failed: {error}",
                )

            elevated_yaml = elevate_output.get("elevated_yaml")
            if not elevated_yaml:
                logger.warning("[ELEVATE-EXISTING] Elevate output missing 'elevated_yaml'")
                if not is_final_attempt:
                    feedback = "Previous attempt produced no output. Please generate complete elevated YAML."
                    continue
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.FAILED,
                    error="Elevate output missing 'elevated_yaml'",
                )

            # Deterministic fixes (ELEVATE may modify IDs/slugs)
            elevated_yaml = self._fix_canonical_id(elevated_yaml, canonical_id)
            elevated_yaml = self._fix_canonical_slug(elevated_yaml, canonical_id)
            elevated_yaml = self._fix_principle_slugs(elevated_yaml)

            # Fix age range to match original file (ELEVATE may incorrectly change it)
            elevated_yaml = self._fix_age_range(elevated_yaml, existing_yaml)

            # D80: Post-ELEVATE dash cleanup (elevate_existing path)
            elevated_yaml = self._remove_dashes(elevated_yaml)

            # V1: Quick pre-validation -- catch obvious failures before expensive QC/audit
            quick_issues = self._quick_validate(elevated_yaml)
            if quick_issues:
                issue_msgs = [i["issue"] for i in quick_issues]
                if not is_final_attempt:
                    feedback = f"Quick validation issues: {issue_msgs}"
                    continue
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.QC_FAILED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    qc_issues=issue_msgs,
                    elevated_yaml=elevated_yaml,
                )

            # Check for truncation
            is_truncated, truncation_reason = self._detect_truncation(elevated_yaml)
            if is_truncated:
                logger.warning(f"[TRUNCATION] Detected: {truncation_reason}")
                if not is_final_attempt:
                    feedback = f"Output was truncated: {truncation_reason}. Ensure complete output."
                    continue
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.QC_FAILED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    qc_issues=[f"Output truncated: {truncation_reason}"],
                    elevated_yaml=elevated_yaml,
                )

            # Stage 5: VALIDATE
            success, validate_output, error = await self._execute_validate(
                elevated_yaml, file_path, canonical_id
            )
            if not success:
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.FAILED,
                    error=f"Validate failed: {error}",
                )

            # Fix guidance/materials misclassification before checking
            validate_output = self._fix_validation_misclassification(validate_output)

            validation_result = validate_output.get("validation_result", {})
            if not validation_result.get("passed", False):
                blocking_issues = validation_result.get("blocking_issues", [])
                if not is_final_attempt:
                    feedback = f"Validation issues: {blocking_issues}"
                    continue
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.FAILED,
                    error=f"Validation failed: {blocking_issues}",
                    elevated_yaml=elevated_yaml,
                )

            # Stage 6: QC HOOK
            qc_passed, qc_issues, qc_warnings = await self._run_qc_hook(elevated_yaml)
            if not qc_passed:
                if not is_final_attempt:
                    feedback = f"QC issues: {qc_issues}"
                    continue
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.QC_FAILED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    qc_issues=qc_issues,
                    qc_warnings=qc_warnings,
                    elevated_yaml=elevated_yaml,
                )

            # Stage 7: QUALITY AUDIT
            audit = await self.audit_quality(
                elevated_yaml=elevated_yaml,
                activity_id=activity_id,
                is_final_attempt=is_final_attempt,
            )

            grade = audit.get("grade", "Unknown")
            grade_str = str(grade).strip().upper() if grade else ""
            is_grade_a = grade_str.startswith("A") and grade_str not in ("AB", "AC", "AD", "AF")

            if not audit.get("passed") or not is_grade_a:
                logger.warning(f"Quality audit: Grade {grade} (requires A/A+/A-)")
                if not is_final_attempt:
                    issues_text = "; ".join(
                        str(i.get("issue", i)) for i in audit.get("issues", [])
                    )
                    feedback = f"Grade {grade}. Issues: {issues_text}"
                    continue
                return ConversionResult(
                    activity_id=activity_id,
                    status=ActivityStatus.REVISION_NEEDED,
                    canonical_id=canonical_id,
                    file_path=file_path,
                    error=f"Quality audit: Grade {grade}",
                    elevated_yaml=elevated_yaml,
                )

            # Success - Grade A achieved
            logger.info(f"[ELEVATE-EXISTING] Grade {grade} achieved for {canonical_id}")
            return ConversionResult(
                activity_id=activity_id,
                status=ActivityStatus.DONE,
                canonical_id=canonical_id,
                file_path=file_path,
                elevated_yaml=elevated_yaml,
            )

        # Should not reach here, but handle edge case
        return ConversionResult(
            activity_id=activity_id,
            status=ActivityStatus.FAILED,
            error="Unexpected: exhausted retries without return",
        )

    def write_canonical_file(self, result: ConversionResult) -> bool:
        """
        Write approved activity to canonical location.

        Path format: {CANONICAL_OUTPUT_DIR}/{domain}/{canonical_id}.yaml

        Args:
            result: Conversion result with file_path and elevated_yaml

        Returns:
            True if written successfully, False otherwise
        """
        if not result.elevated_yaml or not result.canonical_id:
            logger.error("Cannot write file: missing YAML or canonical ID")
            return False

        # Determine output path
        raw_activity = self.raw_activities.get(result.activity_id, {})
        domain = raw_activity.get("domain", "unknown")

        # Apply domain correction if exists
        corrected_domain = self._get_domain_correction(result.activity_id)
        if corrected_domain:
            domain = corrected_domain

        output_dir = self.CANONICAL_OUTPUT_DIR / domain
        output_path = output_dir / f"{result.canonical_id}.yaml"

        try:
            # Create directory if needed
            output_dir.mkdir(parents=True, exist_ok=True)

            # Write file
            output_path.write_text(result.elevated_yaml)
            logger.info(f"Wrote canonical file: {output_path}")

            # A-4: CRITICAL FIX - Clear elevated_yaml after successful write
            # For batch processing 175+ activities, this prevents OOM
            result.elevated_yaml = None

            return True

        except OSError as e:
            logger.error(f"Failed to write canonical file: {e}")
            return False

    async def run_single(self, raw_id: str) -> Optional[ConversionResult]:
        """
        Run conversion for a single activity with human review.

        Args:
            raw_id: Activity raw ID

        Returns:
            ConversionResult if completed, None if quit
        """
        # Update progress to in_progress
        self._update_progress_file(raw_id, ActivityStatus.IN_PROGRESS)

        # Run conversion
        result = await self.convert_activity(raw_id)

        # Handle based on status
        if result.status == ActivityStatus.SKIPPED:
            self._update_progress_file(
                raw_id, ActivityStatus.SKIPPED, result.skip_reason or "Skipped"
            )
            print(f"\nSkipped: {raw_id} - {result.skip_reason}")
            return result

        elif result.status == ActivityStatus.FAILED:
            self._update_progress_file(
                raw_id, ActivityStatus.FAILED, result.error or "Failed"
            )
            print(f"\nFailed: {raw_id} - {result.error}")
            return result

        elif result.status == ActivityStatus.REVISION_NEEDED:
            self._update_progress_file(
                raw_id, ActivityStatus.REVISION_NEEDED, result.error or "Needs revision"
            )
            print(f"\nRevision needed: {raw_id} - {result.error}")
            return result

        elif result.status == ActivityStatus.QC_FAILED:
            # Present for review anyway
            decision = self.present_for_review(
                result, result.elevated_yaml or ""
            )

            if decision == "approve":
                # Override QC failure
                if self.write_canonical_file(result):
                    self._update_progress_file(
                        raw_id, ActivityStatus.DONE, "QC override approved"
                    )
                    print(f"\nApproved (QC override): {raw_id}")
                    return result
            elif decision == "quit":
                self._update_progress_file(raw_id, ActivityStatus.PENDING)
                return None

            self._update_progress_file(
                raw_id, ActivityStatus.QC_FAILED, "QC failed"
            )
            return result

        elif result.status == ActivityStatus.DONE:
            # Present for human review
            decision = self.present_for_review(
                result, result.elevated_yaml or ""
            )

            if decision == "approve":
                if self.write_canonical_file(result):
                    self._update_progress_file(raw_id, ActivityStatus.DONE, "Converted")
                    print(f"\nApproved and saved: {raw_id}")
                else:
                    self._update_progress_file(
                        raw_id, ActivityStatus.FAILED, "Write failed"
                    )
                    print(f"\nFailed to write file for: {raw_id}")
            elif decision == "reject":
                self._update_progress_file(
                    raw_id, ActivityStatus.REVISION_NEEDED, "Rejected in review"
                )
                print(f"\nRejected: {raw_id}")
            elif decision == "skip":
                self._update_progress_file(raw_id, ActivityStatus.PENDING, "Skipped review")
                print(f"\nSkipped for later: {raw_id}")
            elif decision == "quit":
                self._update_progress_file(raw_id, ActivityStatus.PENDING)
                return None

            return result

        return result

    async def run_batch(
        self, limit: int = 10, auto_approve: bool = False
    ) -> BatchResult:
        """
        Process a batch of pending activities.

        Args:
            limit: Maximum number of activities to process
            auto_approve: If True, auto-approve all passing activities

        Returns:
            BatchResult with statistics
        """
        pending = self.get_pending_activities()[:limit]

        if not pending:
            print("No pending activities found.")
            return BatchResult(total=0, completed=0, skipped=0, failed=0, revision_needed=0)

        print(f"\nProcessing {len(pending)} activities...")

        batch_result = BatchResult(
            total=len(pending),
            completed=0,
            skipped=0,
            failed=0,
            revision_needed=0,
        )

        for i, raw_id in enumerate(pending, 1):
            print(f"\n[{i}/{len(pending)}] Processing: {raw_id}")

            # Update progress to in_progress
            self._update_progress_file(raw_id, ActivityStatus.IN_PROGRESS)

            # Run conversion with retry logic (D85: batch mode now uses retry)
            result = await self.convert_with_retry(raw_id, max_retries=2)

            # Handle based on status
            if result.status == ActivityStatus.SKIPPED:
                self._update_progress_file(
                    raw_id, ActivityStatus.SKIPPED, result.skip_reason or "Skipped"
                )
                batch_result.skipped += 1
                batch_result.results.append(result)
                print(f"  -> Skipped: {result.skip_reason}")

            elif result.status == ActivityStatus.FAILED:
                self._update_progress_file(
                    raw_id, ActivityStatus.FAILED, result.error or "Failed"
                )
                batch_result.failed += 1
                batch_result.results.append(result)
                print(f"  -> Failed: {result.error}")

            elif result.status == ActivityStatus.REVISION_NEEDED:
                self._update_progress_file(
                    raw_id, ActivityStatus.REVISION_NEEDED, result.error or "Needs revision"
                )
                batch_result.revision_needed += 1
                batch_result.results.append(result)
                print(f"  -> Revision needed: {result.error}")

            elif result.status == ActivityStatus.QC_FAILED:
                if auto_approve:
                    # Skip QC failures in auto mode
                    self._update_progress_file(
                        raw_id, ActivityStatus.QC_FAILED, "QC failed (auto mode)"
                    )
                    batch_result.failed += 1
                else:
                    # Present for review
                    decision = self.present_for_review(
                        result, result.elevated_yaml or ""
                    )
                    if decision == "approve":
                        if self.write_canonical_file(result):
                            self._update_progress_file(
                                raw_id, ActivityStatus.DONE, "QC override"
                            )
                            batch_result.completed += 1
                        else:
                            batch_result.failed += 1
                    elif decision == "quit":
                        self._update_progress_file(raw_id, ActivityStatus.PENDING)
                        break
                    else:
                        self._update_progress_file(
                            raw_id, ActivityStatus.QC_FAILED, "QC failed"
                        )
                        batch_result.failed += 1

                batch_result.results.append(result)

            elif result.status == ActivityStatus.DONE:
                if auto_approve:
                    # Auto-approve
                    if self.write_canonical_file(result):
                        self._update_progress_file(raw_id, ActivityStatus.DONE, "Auto-approved")
                        batch_result.completed += 1
                        print(f"  -> Auto-approved: {result.canonical_id}")
                    else:
                        self._update_progress_file(
                            raw_id, ActivityStatus.FAILED, "Write failed"
                        )
                        batch_result.failed += 1
                        print(f"  -> Failed to write file")
                else:
                    # Present for review
                    decision = self.present_for_review(
                        result, result.elevated_yaml or ""
                    )

                    if decision == "approve":
                        if self.write_canonical_file(result):
                            self._update_progress_file(
                                raw_id, ActivityStatus.DONE, "Converted"
                            )
                            batch_result.completed += 1
                        else:
                            self._update_progress_file(
                                raw_id, ActivityStatus.FAILED, "Write failed"
                            )
                            batch_result.failed += 1
                    elif decision == "reject":
                        self._update_progress_file(
                            raw_id, ActivityStatus.REVISION_NEEDED, "Rejected"
                        )
                        batch_result.revision_needed += 1
                    elif decision == "skip":
                        self._update_progress_file(raw_id, ActivityStatus.PENDING)
                    elif decision == "quit":
                        self._update_progress_file(raw_id, ActivityStatus.PENDING)
                        break

                batch_result.results.append(result)

        # Print summary
        print("\n" + "=" * 65)
        print("BATCH SUMMARY")
        print("=" * 65)
        print(f"Total processed: {batch_result.total}")
        print(f"Completed:       {batch_result.completed}")
        print(f"Skipped:         {batch_result.skipped}")
        print(f"Failed:          {batch_result.failed}")
        print(f"Revision needed: {batch_result.revision_needed}")
        print("=" * 65)

        return batch_result


async def main():
    """CLI entry point with quality-focused single activity processing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Activity Conversion Pipeline (Quality Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify deduplication/grouping before processing
  python -m atlas.pipelines.activity_conversion --verify

  # Convert single activity (primary mode - no API key needed)
  python -m atlas.pipelines.activity_conversion --activity tummy-time

  # With explicit retry count
  python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 3

  # List pending activities
  python -m atlas.pipelines.activity_conversion --list-pending

  # Batch mode (use only after skills reliably produce Grade A)
  python -m atlas.pipelines.activity_conversion --batch --limit 10

Note: Uses CLI mode (Max subscription). No ANTHROPIC_API_KEY needed.
Quality audit requires Grade A to proceed to human review.
""",
    )

    # Mutually exclusive actions
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--activity", "-a", metavar="RAW_ID",
        help="Single activity ID to convert (primary mode)"
    )
    action.add_argument(
        "--single", metavar="RAW_ID",
        help="Convert single activity (legacy, use --activity instead)"
    )
    action.add_argument(
        "--batch", action="store_true",
        help="Process batch of pending (use only after skills reliably produce Grade A)"
    )
    action.add_argument(
        "--list-pending", action="store_true",
        help="List pending activities"
    )
    action.add_argument(
        "--verify", action="store_true",
        help="Verify deduplication/grouping without processing (G4)"
    )
    action.add_argument(
        "--next", action="store_true",
        help="Find and convert the next truly available activity (skips duplicates/grouped)"
    )
    action.add_argument(
        "--elevate-existing", metavar="YAML_PATH",
        help="Elevate an existing YAML file through stages 4-7 (ELEVATE -> VALIDATE -> QC -> AUDIT)"
    )
    action.add_argument(
        "--reconcile", action="store_true",
        help="Reconcile progress tracker with files on disk (C3 fix)"
    )
    action.add_argument(
        "--cleanup-stale", action="store_true",
        help="Reset IN_PROGRESS entries older than 2 hours to PENDING"
    )

    # Options
    parser.add_argument(
        "--retry", type=int, default=2,
        help="Max retry attempts for non-A grades (default: 2)"
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="Limit for batch processing (default: 10)"
    )
    parser.add_argument(
        "--auto-approve", action="store_true",
        help="Auto-approve passing activities (batch mode)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize pipeline
    try:
        pipeline = ActivityConversionPipeline()
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}", file=sys.stderr)
        sys.exit(1)

    # Execute action
    if args.verify:
        # G4: Deduplication/grouping verification report
        report = pipeline.get_deduplication_report()

        print("\n" + "=" * 60)
        print("ACTIVITY DEDUPLICATION REPORT")
        print("=" * 60)
        print()
        print(f"Raw activities loaded:        {report['raw_activities']}")
        print(f"Explicit duplicates (skip):   {report['skip_count']}")
        print(f"Grouped activities:           {report['grouped_count']} → {report['group_atoms']} atoms")
        print(f"Standalone activities:        {report['standalone_count']}")
        print("-" * 40)
        print(f"Expected canonical atoms:     {report['expected_canonical']}")
        print()

        if report['groups']:
            print("Groups:")
            for g in report['groups']:
                print(f"  {g['group_id']}: {g['source_count']} sources → 1 atom")
                print(f"    Domain: {g['domain']}, Age: {g['age_range']}")
            print()

        if report['skip_list']:
            print("Skip list (duplicates):")
            for s in report['skip_list']:
                print(f"  - {s}")
            print()

        if report['validation_issues']:
            print("VALIDATION ISSUES:")
            for issue in report['validation_issues']:
                print(f"  ⚠ {issue}")
            print()
            sys.exit(1)
        else:
            print("✓ All conversion map references validated")
            print()

    elif args.cleanup_stale:
        reset_ids = pipeline.cleanup_stale_progress(max_age_hours=2)
        if reset_ids:
            print(f"Reset {len(reset_ids)} stale IN_PROGRESS entries:")
            for rid in reset_ids:
                print(f"  - {rid}")
        else:
            print("No stale IN_PROGRESS entries found.")

    elif args.reconcile:
        report = pipeline.reconcile_progress()

        print(f"\n{'='*60}")
        print("PROGRESS RECONCILIATION REPORT")
        print(f"{'='*60}\n")
        print(f"Files on disk:    {report['files_on_disk']}")
        print(f"Tracked as done:  {report['tracked_done']}")
        print()

        if report["status_counts"]:
            print("Status counts (from progress tracker):")
            for status, count in sorted(report["status_counts"].items()):
                print(f"  {status}: {count}")
            print()

        if report["untracked_files"]:
            print(f"Untracked files ({len(report['untracked_files'])} on disk, not tracked as done):")
            for f in report["untracked_files"][:20]:
                print(f"  - {f}")
            if len(report["untracked_files"]) > 20:
                print(f"  ... and {len(report['untracked_files']) - 20} more")
            print()

        if report["missing_files"]:
            print(f"Missing files ({len(report['missing_files'])} tracked as done, no file):")
            for f in report["missing_files"][:20]:
                print(f"  - {f}")
            print()

        if not report["untracked_files"] and not report["missing_files"]:
            print("No discrepancies found.")
        print(f"{'='*60}\n")

    elif args.list_pending:
        pending = pipeline.get_pending_activities()
        if pending:
            print(f"Pending activities ({len(pending)}):")
            for i, raw_id in enumerate(pending[:20], 1):
                print(f"  {i}. {raw_id}")
            if len(pending) > 20:
                print(f"  ... and {len(pending) - 20} more")
        else:
            print("No pending activities.")

    elif args.next:
        # Find next truly available activity (not in skip list, not non-primary)
        raw_id = pipeline.get_next_available_activity()

        if not raw_id:
            print("No available activities to convert!")
            print("All pending activities are either duplicates or non-primary group members.")
            sys.exit(0)

        print(f"\n{'='*60}")
        print(f"NEXT AVAILABLE: {raw_id}")
        print(f"Max retries: {args.retry}")
        print(f"{'='*60}\n")

        # Update progress to in_progress
        pipeline._update_progress_file(raw_id, ActivityStatus.IN_PROGRESS)

        # Run conversion with retry
        result = await pipeline.convert_with_retry(raw_id, max_retries=args.retry)

        # Print result
        print(f"\n{'='*60}")
        print(f"RESULT: {result.status.value.upper()}")

        if result.status == ActivityStatus.DONE:
            print(f"Grade A - Ready for human review!")
            print(f"Canonical ID: {result.canonical_id}")
            print(f"File path: {result.file_path}")

            # D81: Add auto-approve handling for --next path
            if args.auto_approve:
                if pipeline.write_canonical_file(result):
                    pipeline._update_progress_file(raw_id, ActivityStatus.DONE, "Converted")
                    print("\n[Auto-approved and saved]")
                else:
                    pipeline._update_progress_file(raw_id, ActivityStatus.FAILED, "Write failed")
                    print("\nFailed to write file")
                    sys.exit(1)
        elif result.status == ActivityStatus.FAILED:
            print("Failed")
            if result.error:
                print(f"Error: {result.error}")
            if result.qc_issues:
                print("QC Issues:")
                for issue in result.qc_issues[:5]:
                    print(f"  - {issue}")
            pipeline._update_progress_file(raw_id, ActivityStatus.FAILED, result.error or "Failed")
            sys.exit(1)  # D84: Exit with error code on failure

        # D82: Add missing status handlers for --next path
        elif result.status == ActivityStatus.REVISION_NEEDED:
            print("Revision needed")
            if result.error:
                print(f"Error: {result.error}")
            if result.qc_warnings:
                print("Issues:")
                for w in result.qc_warnings[:5]:
                    print(f"  - {w}")
            pipeline._update_progress_file(raw_id, ActivityStatus.REVISION_NEEDED, result.error or "Needs revision")
            sys.exit(1)  # D84: Exit with error code on revision needed

        elif result.status == ActivityStatus.QC_FAILED:
            print("QC Failed")
            if result.qc_issues:
                print("QC Issues:")
                for issue in result.qc_issues[:5]:
                    print(f"  - {issue}")
            pipeline._update_progress_file(raw_id, ActivityStatus.QC_FAILED, "QC failed")
            sys.exit(1)  # D84: Exit with error code on QC failure

        elif result.status == ActivityStatus.SKIPPED:
            print(f"Skipped: {result.skip_reason}")
            pipeline._update_progress_file(raw_id, ActivityStatus.SKIPPED, result.skip_reason or "Skipped")

        print(f"{'='*60}\n")

    elif args.activity or args.single:
        # Single activity processing with quality audit
        raw_id = args.activity or args.single

        print(f"\n{'='*60}")
        print(f"QUALITY MODE: Processing {raw_id}")
        print(f"Max retries: {args.retry}")
        print(f"{'='*60}\n")

        # Update progress to in_progress
        pipeline._update_progress_file(raw_id, ActivityStatus.IN_PROGRESS)

        # Run conversion with retry
        result = await pipeline.convert_with_retry(raw_id, max_retries=args.retry)

        # Print result
        print(f"\n{'='*60}")
        print(f"RESULT: {result.status.value.upper()}")

        if result.status == ActivityStatus.DONE:
            print(f"Grade A - Ready for human review!")
            print(f"Canonical ID: {result.canonical_id}")
            if result.file_path:
                print(f"File path: {result.file_path}")

            # Present for human review (or auto-approve)
            if args.auto_approve:
                # Auto-approve without interactive prompt
                decision = "approve"
                print("\n[Auto-approved]")
            else:
                decision = pipeline.present_for_review(
                    result, result.elevated_yaml or ""
                )

            if decision == "approve":
                if pipeline.write_canonical_file(result):
                    pipeline._update_progress_file(raw_id, ActivityStatus.DONE, "Converted")
                    print(f"\nApproved and saved: {raw_id}")
                else:
                    pipeline._update_progress_file(
                        raw_id, ActivityStatus.FAILED, "Write failed"
                    )
                    print(f"\nFailed to write file for: {raw_id}")
                    sys.exit(1)
            elif decision == "reject":
                pipeline._update_progress_file(
                    raw_id, ActivityStatus.REVISION_NEEDED, "Rejected in review"
                )
                print(f"\nRejected: {raw_id}")
            elif decision == "skip":
                pipeline._update_progress_file(raw_id, ActivityStatus.PENDING, "Skipped review")
                print(f"\nSkipped for later: {raw_id}")
            elif decision == "quit":
                pipeline._update_progress_file(raw_id, ActivityStatus.PENDING)
                print("Conversion cancelled.")
                sys.exit(0)

        elif result.status == ActivityStatus.REVISION_NEEDED:
            print(f"Status: {result.status.value}")
            if result.error:
                print(f"Error: {result.error}")
            if result.qc_warnings:
                print("Issues:")
                for w in result.qc_warnings[:5]:
                    print(f"  - {w}")
            pipeline._update_progress_file(
                raw_id, ActivityStatus.REVISION_NEEDED, result.error or "Needs revision"
            )
            sys.exit(1)

        elif result.status == ActivityStatus.SKIPPED:
            print(f"Skipped: {result.skip_reason}")
            pipeline._update_progress_file(raw_id, ActivityStatus.SKIPPED, result.skip_reason or "Skipped")
            sys.exit(0)  # SKIPPED is not an error, exit cleanly

        else:
            print(f"Status: {result.status.value}")
            if result.error:
                print(f"Error: {result.error}")
            # Show QC issues for debugging
            if result.qc_issues:
                print(f"QC Issues ({len(result.qc_issues)}):")
                for issue in result.qc_issues:
                    print(f"  - {issue}")
            if result.qc_warnings:
                print(f"QC Warnings ({len(result.qc_warnings)}):")
                for warning in result.qc_warnings[:5]:
                    print(f"  - {warning}")
            if result.status == ActivityStatus.FAILED:
                pipeline._update_progress_file(
                    raw_id, ActivityStatus.FAILED, result.error or "Failed"
                )
            elif result.status == ActivityStatus.QC_FAILED:
                pipeline._update_progress_file(
                    raw_id, ActivityStatus.QC_FAILED, "QC failed"
                )
            sys.exit(1)

        print(f"{'='*60}\n")

    elif getattr(args, 'elevate_existing', None):
        # Elevate existing file through stages 4-7
        yaml_path = args.elevate_existing

        print(f"\n{'='*60}")
        print(f"ELEVATE EXISTING: {yaml_path}")
        print(f"Stages: ELEVATE → VALIDATE → QC → AUDIT")
        print(f"Max retries: {args.retry}")
        print(f"{'='*60}\n")

        result = await pipeline.elevate_existing_file(yaml_path, max_retries=args.retry)

        print(f"\n{'='*60}")
        print(f"RESULT: {result.status.value.upper()}")

        if result.status == ActivityStatus.DONE:
            print(f"Grade A achieved!")
            print(f"Canonical ID: {result.canonical_id}")

            # Determine target path
            from pathlib import Path
            source_path = Path(yaml_path)

            if args.auto_approve and result.elevated_yaml:
                # Write directly to canonical location
                target_dir = Path(result.file_path).parent
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = Path(result.file_path)
                target_path.write_text(result.elevated_yaml)

                # Remove from staging if it was there
                if source_path.exists() and "staging" in str(source_path):
                    source_path.unlink()
                    print(f"Removed from staging: {source_path.name}")

                print(f"Saved to: {target_path}")
                print("[Auto-approved and saved]")
            else:
                decision = pipeline.present_for_review(result, result.elevated_yaml or "")

                if decision == "approve" and result.elevated_yaml:
                    target_dir = Path(result.file_path).parent
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target_path = Path(result.file_path)
                    target_path.write_text(result.elevated_yaml)

                    if source_path.exists() and "staging" in str(source_path):
                        source_path.unlink()
                        print(f"Removed from staging: {source_path.name}")

                    print(f"Approved and saved: {target_path}")
                elif decision == "reject":
                    print("Rejected - file not moved")
                elif decision == "skip":
                    print("Skipped for later")
                elif decision == "quit":
                    print("Cancelled")
                    sys.exit(0)

        elif result.status == ActivityStatus.REVISION_NEEDED:
            print(f"Needs revision - Grade not achieved")
            if result.error:
                print(f"Error: {result.error}")
            sys.exit(1)

        elif result.status == ActivityStatus.QC_FAILED:
            print("QC Failed")
            if result.qc_issues:
                print("QC Issues:")
                for issue in result.qc_issues[:5]:
                    print(f"  - {issue}")
            sys.exit(1)

        else:
            print(f"Status: {result.status.value}")
            if result.error:
                print(f"Error: {result.error}")
            sys.exit(1)

        print(f"{'='*60}\n")

    elif args.batch:
        # Batch mode warning
        print("\n" + "=" * 60)
        print("WARNING: Batch mode recommended only after skills")
        print("reliably produce Grade A content.")
        print("=" * 60 + "\n")

        result = await pipeline.run_batch(
            limit=args.limit, auto_approve=args.auto_approve
        )
        if result.failed > 0:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
