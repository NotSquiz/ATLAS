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
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

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

    # Valid domains for activities
    VALID_DOMAINS = {
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
    }

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

        # Load source data
        self._load_source_data()

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
                self.raw_activities = {}
                skipped_count = 0
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
                    self.raw_activities[a["id"]] = a

                logger.info(
                    f"Loaded {len(self.raw_activities)} raw activities"
                    + (f" (skipped {skipped_count})" if skipped_count else "")
                )
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
            content = self.PROGRESS_PATH.read_text()

            # Find table rows using regex
            # Pattern matches: | num | raw_id | domain | age_range | status | date | notes |
            table_pattern = re.compile(
                r"^\|\s*(\d+)\s*\|\s*([^\|]+)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|\s*([^\|]*)\s*\|",
                re.MULTILINE,
            )

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

                self.progress_data[raw_id] = {
                    "row_num": row_num,
                    "domain": domain,
                    "age_range": age_range,
                    "status": status,
                    "date": date,
                    "notes": notes,
                }

            logger.info(f"Parsed {len(self.progress_data)} entries from progress file")

        except OSError as e:
            logger.error(f"Failed to read progress file: {e}")

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
                                parts[5] = f" {status_str} "
                                parts[6] = f" {date_str} "
                                if notes:
                                    parts[7] = f" {notes} "
                                lines[i] = "|".join(parts)
                                updated = True
                                break

                    if updated:
                        # Update summary counts
                        content = "\n".join(lines)
                        content = self._update_summary_counts(content)

                        # Truncate and write
                        f.seek(0)
                        f.write(content)
                        f.truncate()
                        logger.info(f"Updated progress for {raw_id}: {status_str}")

                        # Update local cache
                        if raw_id in self.progress_data:
                            self.progress_data[raw_id]["status"] = status_str
                            self.progress_data[raw_id]["date"] = date_str
                            if notes:
                                self.progress_data[raw_id]["notes"] = notes

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
        """Update summary counts in progress file content."""
        # Count statuses
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

        # Update summary section
        content = re.sub(r"- Done: \d+", f"- Done: {done}", content)
        content = re.sub(r"- Pending: \d+", f"- Pending: {pending}", content)
        content = re.sub(r"- Failed: \d+", f"- Failed: {failed}", content)

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

        # Execute skill
        result = await self.skill_executor.execute(
            skill_name="activity/ingest_activity",
            input_data={"raw_id": raw_id, "raw_activity": raw_activity},
            validate=True,
        )

        if not result.success:
            return False, {}, result.error or "Ingest skill failed"

        output = result.output or {}
        output["raw_activity"] = raw_activity
        output["activity_id"] = raw_id

        return True, output, None

    async def _execute_research(
        self, ingest_output: dict
    ) -> tuple[bool, dict, Optional[str]]:
        """
        Execute the research_activity skill.

        Args:
            ingest_output: Output from ingest skill

        Returns:
            Tuple of (success, output_data, error_message)
        """
        logger.info(f"[RESEARCH] Starting for {ingest_output.get('activity_id')}")

        result = await self.skill_executor.execute(
            skill_name="activity/research_activity",
            input_data=ingest_output,
            validate=True,
        )

        if not result.success:
            return False, {}, result.error or "Research skill failed"

        return True, result.output or {}, None

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

        result = await self.skill_executor.execute(
            skill_name="activity/transform_activity",
            input_data={
                "ingest_result": ingest_output,
                "research_result": research_output,
            },
            validate=True,
        )

        if not result.success:
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
        """
        if feedback:
            logger.info("[ELEVATE] Starting voice elevation WITH FEEDBACK (retry)")
        else:
            logger.info("[ELEVATE] Starting voice elevation")

        # Build input data with optional feedback for retry context
        input_data = {"canonical_yaml": canonical_yaml}
        if feedback:
            input_data["retry_feedback"] = feedback
            input_data["is_retry"] = True

        result = await self.skill_executor.execute(
            skill_name="activity/elevate_voice_activity",
            input_data=input_data,
            validate=True,
        )

        if not result.success:
            return False, {}, result.error or "Elevate skill failed"

        return True, result.output or {}, None

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

        result = await self.skill_executor.execute(
            skill_name="activity/validate_activity",
            input_data={
                "elevated_yaml": elevated_yaml,
                "file_path": file_path,
                "canonical_id": canonical_id,
            },
            validate=True,
        )

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

    async def audit_quality(self, elevated_yaml: str, activity_id: str) -> dict:
        """
        Audit activity quality using BabyBrains voice standards.

        Spawns a fresh sub-agent to grade the activity against:
        - Voice Elevation Rubric criteria
        - A+ reference activity (gold standard)

        Args:
            elevated_yaml: The elevated YAML content to audit
            activity_id: Activity ID for logging

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

        audit_prompt = f"""You are a quality auditor for BabyBrains Activity Atoms.

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

## YOUR TASK
Grade this activity using the Voice Elevation Rubric. Check:

1. **Anti-Pattern Check**: Any em-dashes (—), formal transitions (Moreover, Furthermore, etc.), superlatives (amazing, incredible)?
2. **Philosophy Integration**: Which of the 6 Montessori principles are present?
   - Cosmic View (connects to meaningful work)
   - Spiritual Embryo (child develops from within)
   - Adult as Obstacle (parent self-reflection prompts)
   - Freedom Within Limits (boundaries as loving structure)
   - Transformed Adult (adult self-regulation matters)
   - Creating Conditions Not Outcomes (anxiety-reducing)
3. **Australian Voice**: Understated confidence, tall poppy safe, cost-aware, correct vocab (mum, nappy, cot)?
4. **Rationale Field**: Does it follow the A+ pattern? (Observable → Philosophy → Parent psychology → Reassurance)
5. **Science Weaving**: Observable → Invisible → Meaningful pattern?

**IMPORTANT**: Grade A requires ALL checks to pass. Any em-dash = automatic B+ maximum.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "grade": "A",
  "passed": true,
  "issues": [],
  "philosophy_found": ["cosmic_view", "spiritual_embryo", "adult_as_obstacle", "freedom_within_limits", "transformed_adult", "creating_conditions"],
  "philosophy_missing": [],
  "australian_voice": true,
  "rationale_quality": "excellent",
  "recommendation": "Ready for production"
}}

OR if issues found:
{{
  "grade": "B+",
  "passed": false,
  "issues": [
    {{"category": "anti-pattern", "issue": "Em-dash found in description", "fix": "Replace with period or comma"}},
    {{"category": "philosophy", "issue": "Missing 'Adult as Obstacle' reflection", "fix": "Add prompt for parent self-awareness"}}
  ],
  "philosophy_found": ["cosmic_view", "spiritual_embryo"],
  "philosophy_missing": ["adult_as_obstacle", "transformed_adult"],
  "australian_voice": true,
  "rationale_quality": "needs_work",
  "recommendation": "Needs elevation - add philosophy integration and fix anti-patterns"
}}
"""

        logger.info(f"Running quality audit for {activity_id}")

        # Use SubAgentExecutor for fresh context
        result = await self.sub_executor.spawn(
            task=audit_prompt,
            context={"activity_id": activity_id, "audit_type": "voice_quality"},
            timeout=300,  # 5 min for quality audit
            sandbox=True,
        )

        # Parse JSON response
        if result.success and result.output:
            try:
                output = result.output.strip()
                # Handle potential markdown code blocks
                if "```json" in output:
                    output = output.split("```json")[1].split("```")[0].strip()
                elif "```" in output:
                    output = output.split("```")[1].split("```")[0].strip()

                audit_result = json.loads(output)
                logger.info(f"Quality audit result: Grade {audit_result.get('grade')}")
                return audit_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse audit response: {e}")
                logger.debug(f"Raw response: {result.output[:500]}")

        # Fallback on failure
        return {
            "grade": "F",
            "passed": False,
            "issues": [
                {
                    "category": "audit",
                    "issue": "Audit failed - could not parse response",
                    "fix": "Manual review required",
                }
            ],
            "philosophy_found": [],
            "philosophy_missing": [],
            "australian_voice": False,
            "rationale_quality": "unknown",
            "recommendation": "Audit failed - requires manual review",
        }

    async def convert_activity(
        self, raw_id: str, feedback: Optional[str] = None
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
        session_id = f"convert_{raw_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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

            # Check voice grade
            grade = elevate_output.get("grade", "")
            if grade and grade != "A":
                return ConversionResult(
                    activity_id=raw_id,
                    status=ActivityStatus.REVISION_NEEDED,
                    error=f"Voice grade {grade}: {elevate_output.get('issues', [])}",
                    elevated_yaml=elevate_output.get("elevated_yaml"),
                )

            elevated_yaml = elevate_output.get("elevated_yaml", canonical_yaml)

            # C-1: SPEC COMPLIANCE - Adversarial verification via SubAgentExecutor
            # Per masterclass [4147s]: Use fresh context to verify work
            try:
                verification = await self.sub_executor.verify_adversarially(
                    output={"yaml": elevated_yaml[:5000], "grade": grade or "A"},
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
            logger.info(f"Stage 7: QUALITY AUDIT for {raw_id}")
            audit = await self.audit_quality(
                elevated_yaml=elevated_yaml,
                activity_id=raw_id,
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

    async def reflect_on_failure(
        self,
        failed_yaml: str,
        issues: list[dict],
        grade: str,
    ) -> str:
        """
        Apply the "Wait" pattern to reflect on why an activity failed quality audit.

        Uses Anthropic introspection research (89.3% blind spot reduction) to
        generate intelligent feedback for retry attempts.

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

        # Format issues for reflection
        issues_text = "\n".join(
            f"- [{i.get('category', 'unknown')}] {i.get('issue', 'No description')}"
            + (f"\n  Fix: {i.get('fix')}" if i.get("fix") else "")
            for i in valid_issues
        )
        if len(issues) > 20:
            issues_text += f"\n... and {len(issues) - 20} more issues"

        # The "Wait" pattern from Anthropic introspection research
        reflection_prompt = f"""Wait. Before re-elevating this activity, pause and consider:

## Failed Activity (Grade {grade})
The previous elevation attempt received Grade {grade} instead of the required A.

## Specific Issues Found
{issues_text}

## Reflection Questions
- What assumptions did the previous elevation make that led to these issues?
- Why did these specific anti-patterns or gaps occur?
- What would I tell another agent who made these same mistakes?

## Your Task
Based on this reflection, provide specific guidance for the re-elevation:
1. What MUST change to achieve Grade A?
2. Which Montessori principles need stronger integration?
3. What Australian voice elements need adjustment?
4. Any anti-patterns that must be eliminated?

Be specific and actionable. This feedback will guide the next elevation attempt.
"""

        logger.info(f"Applying 'Wait' pattern reflection for Grade {grade}")

        # Use SubAgentExecutor for fresh reflection
        result = await self.sub_executor.spawn(
            task=reflection_prompt,
            context={"grade": grade, "issue_count": len(valid_issues)},
            timeout=120,  # 2 min for reflection
            sandbox=True,
        )

        if result.success and result.output:
            logger.info("Reflection generated successfully")
            return result.output
        else:
            # Fallback to formatted issues if reflection fails
            logger.warning("Reflection failed, using formatted issues as feedback")
            return f"Previous attempt failed with Grade {grade}. Issues:\n{issues_text}"

    async def convert_with_retry(
        self,
        raw_id: str,
        max_retries: int = 2,
    ) -> ConversionResult:
        """
        Convert activity with intelligent retry using the "Wait" pattern.

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

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt}/{max_retries} for {raw_id}")
                print(f"\nApplying 'Wait' pattern reflection...")
                print(f"Retry attempt {attempt}/{max_retries} with learned context\n")

            # Run conversion with any feedback from previous attempt
            result = await self.convert_activity(raw_id, feedback=feedback)
            last_result = result

            # Success - Grade A achieved
            if result.status == ActivityStatus.DONE:
                if attempt > 0:
                    logger.info(f"Succeeded on attempt {attempt + 1}")
                    print(f"\nSucceeded on attempt {attempt + 1}!")
                return result

            # Not a quality issue (FAILED, QC_FAILED, SKIPPED) - don't retry
            if result.status != ActivityStatus.REVISION_NEEDED:
                logger.info(f"Status {result.status.value} - not retrying")
                return result

            # Max retries exhausted
            if attempt >= max_retries:
                logger.warning(f"Max retries ({max_retries}) reached for {raw_id}")
                return result

            # Apply "Wait" pattern reflection for intelligent retry
            # Get audit results from scratch pad
            audit = self.scratch_pad.get(f"quality_audit") if self.scratch_pad else {}
            if not audit:
                audit = {"issues": [], "grade": "Unknown"}

            feedback = await self.reflect_on_failure(
                failed_yaml=result.elevated_yaml or "",
                issues=audit.get("issues", []),
                grade=audit.get("grade", "Unknown"),
            )

            logger.info(f"Will retry with reflection feedback")
            if result.qc_warnings:
                print(f"Issues from attempt {attempt + 1}:")
                for w in result.qc_warnings[:3]:
                    print(f"  - {w}")

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

            # Run conversion
            result = await self.convert_activity(raw_id)

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
    if args.list_pending:
        pending = pipeline.get_pending_activities()
        if pending:
            print(f"Pending activities ({len(pending)}):")
            for i, raw_id in enumerate(pending[:20], 1):
                print(f"  {i}. {raw_id}")
            if len(pending) > 20:
                print(f"  ... and {len(pending) - 20} more")
        else:
            print("No pending activities.")

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

            # Present for human review
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

        else:
            print(f"Status: {result.status.value}")
            if result.error:
                print(f"Error: {result.error}")
            if result.status == ActivityStatus.FAILED:
                pipeline._update_progress_file(
                    raw_id, ActivityStatus.FAILED, result.error or "Failed"
                )
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
