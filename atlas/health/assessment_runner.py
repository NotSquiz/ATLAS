"""
ATLAS Assessment Protocol Runner

Voice-guided assessment protocol execution with:
- Session management (start, pause, resume)
- Timed test support with auto-stop
- Multiple input types (numeric, boolean, categorical, FMS, compound)
- Undo/correction support
- Baseline comparison
- Progress persistence
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from atlas.voice.number_parser import (
    parse_spoken_number,
    parse_boolean,
    parse_categorical,
    parse_fms_score,
    parse_duration,
    parse_blood_pressure,
    parse_weight_reps,
    format_echo,
)
from atlas.health.assessment_calculator import (
    calculate_1rm_brzycki,
    calculate_lsi,
    format_comparison_voice,
    estimate_session_duration,
)
from atlas.health.assessment import AssessmentService

logger = logging.getLogger(__name__)

# TTS-friendly session names (now using numbers for reliability)
SESSION_TTS_NAMES = {"1": "1", "2": "2", "3": "3", "A": "1", "B": "2", "C": "3"}


def _tts_session(session_id: str) -> str:
    """Convert session ID to TTS-friendly name."""
    return SESSION_TTS_NAMES.get(session_id.upper(), session_id)


@dataclass
class TestState:
    """Current test state."""
    test_id: str
    test_def: dict
    section_name: str
    attempt: int = 1  # For multi-attempt tests
    compound_field_idx: int = 0  # For compound tests
    compound_values: dict = field(default_factory=dict)


@dataclass
class SessionState:
    """Session state for persistence."""
    session_id: str
    current_test_id: str
    started_at: str
    updated_at: str
    results_logged: int = 0
    last_value: Optional[str] = None
    last_test_id: Optional[str] = None
    protocol_run: Optional[str] = None  # e.g., 'baseline_2026_q1', 'retest_2026_q2'


class AssessmentProtocolRunner:
    """Voice-guided assessment protocol execution."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".atlas" / "atlas.db"
        self.config_path = Path(__file__).parent.parent.parent / "config" / "assessments" / "protocol_voice.json"
        self._config: Optional[dict] = None
        self._state: Optional[SessionState] = None
        self._test_state: Optional[TestState] = None
        self._timer_start: Optional[float] = None
        self._assessment_service = AssessmentService(db_path)

        # Load any saved state
        self._load_state()

    @property
    def config(self) -> dict:
        """Load and cache protocol config."""
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Protocol config not found: {self.config_path}")
            with open(self.config_path) as f:
                self._config = json.load(f)
        return self._config

    @property
    def state(self) -> Optional[SessionState]:
        """Current session state."""
        return self._state

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ========================================
    # Session Control
    # ========================================

    def get_session_choices(self) -> str:
        """Get session selection prompt."""
        sessions = self.config.get("sessions", {})
        choices = []
        for sid, session in sessions.items():
            name = session.get("name", sid)
            duration = session.get("duration_minutes", 30)
            choices.append(f"{_tts_session(sid)} is {name}, {duration} minutes")
        return "Session " + ". ".join(choices) + ". Which one?"

    def parse_session_choice(self, text: str) -> Optional[str]:
        """Parse session selection from text."""
        text_lower = text.lower().strip()
        sessions = self.config.get("sessions", {})

        for sid, session in sessions.items():
            # Direct match
            if sid.lower() in text_lower:
                return sid

            # Alias match
            aliases = session.get("aliases", [])
            for alias in aliases:
                if alias.lower() in text_lower:
                    return sid

        return None

    def _generate_protocol_run(self) -> str:
        """Generate a protocol run identifier based on current date.

        Format: baseline_YYYY_qN (e.g., 'baseline_2026_q1')
        For subsequent runs in same quarter, could be 'retest_2026_q1' etc.
        """
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"baseline_{now.year}_q{quarter}"

    async def start_session(self, session_id: str, protocol_run: Optional[str] = None) -> str:
        """
        Start a new assessment session.

        Args:
            session_id: 'A', 'B', or 'C'
            protocol_run: Optional protocol identifier (auto-generated if not provided)
                         e.g., 'baseline_2026_q1', 'retest_2026_q2', 'gate_1_check'

        Returns:
            First test prompt
        """
        session_id = session_id.upper()
        session = self.config.get("sessions", {}).get(session_id)

        if not session:
            return f"Unknown session: {session_id}. {self.get_session_choices()}"

        # Get first test
        first_test = self._get_first_test(session_id)
        if not first_test:
            return f"Session {_tts_session(session_id)} has no tests configured."

        # Generate or use provided protocol_run
        if not protocol_run:
            protocol_run = self._generate_protocol_run()

        # Initialize state
        now = datetime.now().isoformat()
        self._state = SessionState(
            session_id=session_id,
            current_test_id=first_test["id"],
            started_at=now,
            updated_at=now,
            protocol_run=protocol_run,
        )

        # Initialize test state
        section_name = self._find_section_for_test(session_id, first_test["id"])
        self._test_state = TestState(
            test_id=first_test["id"],
            test_def=first_test,
            section_name=section_name,
        )

        # Save to DB
        self._save_state()

        # Build response
        name = session.get("name", session_id)
        sections = session.get("sections", [])
        total_tests = sum(len(s.get("tests", [])) for s in sections)
        equipment = session.get("equipment", [])

        intro = f"Session {_tts_session(session_id)}. {name}. {total_tests} tests."
        if equipment:
            intro += f" Equipment needed: {', '.join(equipment)}."

        first_prompt = self._format_test_prompt(first_test)
        return f"{intro} First: {first_prompt}"

    async def resume_session(self) -> str:
        """
        Resume from saved state.

        Returns:
            Current test prompt
        """
        if not self._state:
            self._load_state()

        if not self._state:
            return "No saved session found. Say start baseline assessment to begin."

        # Verify session still exists in config
        session = self.config.get("sessions", {}).get(self._state.session_id)
        if not session:
            return f"Session {_tts_session(self._state.session_id)} no longer exists. Start a new session."

        # Find current test
        test_def = self._find_test_by_id(self._state.session_id, self._state.current_test_id)
        if not test_def:
            # Test ID changed - try to recover
            first_test = self._get_first_test(self._state.session_id)
            if first_test:
                self._state.current_test_id = first_test["id"]
                test_def = first_test
            else:
                return "Session configuration changed. Please start a new session."

        # Restore test state
        section_name = self._find_section_for_test(self._state.session_id, self._state.current_test_id)
        self._test_state = TestState(
            test_id=self._state.current_test_id,
            test_def=test_def,
            section_name=section_name,
        )

        prompt = self._format_test_prompt(test_def)
        logged = self._state.results_logged
        total = self._count_total_tests(self._state.session_id)

        return f"Resuming Session {_tts_session(self._state.session_id)}. Test {logged + 1} of {total}. {prompt}"

    async def pause_session(self) -> str:
        """
        Pause and save current session.

        Returns:
            Confirmation message
        """
        if not self._state:
            return "No active session to pause."

        # Stop any timer
        self._timer_start = None

        # Save state
        self._state.updated_at = datetime.now().isoformat()
        self._save_state()

        test_name = self._test_state.test_def.get("name", "Unknown") if self._test_state else "Unknown"
        return f"Paused at {test_name}. Say resume assessment to continue."

    # ========================================
    # Test Interaction
    # ========================================

    async def record_result(self, value: Any, notes: str = "") -> str:
        """
        Record a test result and advance to next test.

        Args:
            value: The recorded value
            notes: Optional notes

        Returns:
            Confirmation with comparison and next test prompt
        """
        if not self._state or not self._test_state:
            return "No active session. Start or resume first."

        test = self._test_state.test_def
        test_id = self._test_state.test_id

        # Store for undo
        self._state.last_test_id = test_id
        self._state.last_value = json.dumps({"value": value, "notes": notes})

        # Log to assessment service
        try:
            # Get unit
            unit = test.get("unit", "")

            # For compound fields, we might have a specific unit
            if self._test_state.compound_field_idx > 0:
                fields = test.get("fields", [])
                if self._test_state.compound_field_idx - 1 < len(fields):
                    unit = fields[self._test_state.compound_field_idx - 1].get("unit", unit)

            self._assessment_service.log_assessment(
                assessment_id=test_id,
                value=float(value) if isinstance(value, (int, float)) else 0,
                notes=notes,
                protocol_run=self._state.protocol_run if self._state else None,
            )
        except Exception as e:
            # CRITICAL: Never silently fail on data storage
            logger.error(f"CRITICAL: Failed to log assessment {test_id}: {e}")
            # Return error to user so they know data wasn't saved
            return f"ERROR: Failed to save {test_id}. Value {value} NOT SAVED. Error: {e}"

        # Format echo and comparison
        unit = test.get("unit", "")
        echo = format_echo(value, unit) if isinstance(value, (int, float)) else str(value)

        # Get baseline comparison
        baseline = self._assessment_service.get_baseline(test_id)
        lower_is_better = test.get("lower_is_better", False)
        comparison = format_comparison_voice(value, baseline, unit, lower_is_better)

        # Update state
        self._state.results_logged += 1
        self._state.updated_at = datetime.now().isoformat()

        # Advance to next test
        if not self._advance_to_next():
            # Session complete - save count before clearing
            total = self._state.results_logged if self._state else 0
            self._clear_state()
            return f"Logged {echo}. {comparison} Session complete. {total} tests recorded."

        # Format response
        next_prompt = self._format_test_prompt(self._test_state.test_def)
        self._save_state()

        return f"Logged {echo}. {comparison} Next: {next_prompt}"

    async def get_setup(self) -> str:
        """Get detailed setup instructions for current test."""
        if not self._test_state:
            return "No active test."

        test = self._test_state.test_def
        setup = test.get("voice_setup", "")

        if setup:
            return setup
        else:
            return f"No detailed setup for {test.get('name', 'this test')}. Just do your best."

    async def skip_test(self) -> str:
        """Skip current test and move to next."""
        if not self._state or not self._test_state:
            return "No active session."

        skipped_name = self._test_state.test_def.get("name", "Unknown")

        if not self._advance_to_next():
            self._clear_state()
            return f"Skipped {skipped_name}. Session complete."

        self._save_state()
        next_prompt = self._format_test_prompt(self._test_state.test_def)
        return f"Skipped. Next: {next_prompt}"

    async def undo_last(self) -> str:
        """Undo last recorded result."""
        if not self._state or not self._state.last_test_id:
            return "Nothing to undo."

        last_data = json.loads(self._state.last_value) if self._state.last_value else {}
        last_value = last_data.get("value", "unknown")

        # Reset to previous test
        self._state.current_test_id = self._state.last_test_id
        self._state.results_logged = max(0, self._state.results_logged - 1)

        # Find and restore test state
        test_def = self._find_test_by_id(self._state.session_id, self._state.last_test_id)
        if test_def:
            section_name = self._find_section_for_test(self._state.session_id, self._state.last_test_id)
            self._test_state = TestState(
                test_id=self._state.last_test_id,
                test_def=test_def,
                section_name=section_name,
            )

        self._state.last_test_id = None
        self._state.last_value = None
        self._save_state()

        return f"Last was {last_value}. What should it be?"

    async def get_status(self) -> str:
        """Get current progress status."""
        if not self._state:
            return "No active session."

        current = self._state.results_logged + 1
        total = self._count_total_tests(self._state.session_id)
        remaining = total - self._state.results_logged
        time_estimate = estimate_session_duration(remaining)

        test_name = self._test_state.test_def.get("name", "Unknown") if self._test_state else "Unknown"

        return f"Test {current} of {total}. {test_name}. {remaining} remaining, {time_estimate}."

    async def get_equipment_needed(self) -> str:
        """Get equipment needed for next section."""
        if not self._state or not self._test_state:
            return "No active session."

        # Find next section's equipment reminder
        session = self.config.get("sessions", {}).get(self._state.session_id, {})
        sections = session.get("sections", [])

        for section in sections:
            for test in section.get("tests", []):
                if test.get("id") == self._test_state.test_id:
                    reminder = section.get("equipment_reminder", "")
                    if reminder:
                        return reminder
                    equipment = session.get("equipment", [])
                    if equipment:
                        return f"Equipment for this session: {', '.join(equipment)}."
                    return "No special equipment needed."

        return "No equipment information available."

    # ========================================
    # Timed Tests
    # ========================================

    def current_test_is_timed(self) -> bool:
        """Check if current test is a timed test."""
        if not self._test_state:
            return False
        return self._test_state.test_def.get("input_type") == "timed"

    def current_test_is_countdown(self) -> bool:
        """Check if current test is a countdown test."""
        if not self._test_state:
            return False
        return self._test_state.test_def.get("input_type") == "countdown_reps"

    def get_max_time(self) -> int:
        """Get max time for current timed test."""
        if not self._test_state:
            return 60
        return self._test_state.test_def.get("max_time", 60)

    def get_countdown_seconds(self) -> int:
        """Get countdown duration for countdown test."""
        if not self._test_state:
            return 30
        return self._test_state.test_def.get("countdown_seconds", 30)

    def get_beep_intervals(self) -> list[int]:
        """Get beep intervals for current test."""
        if not self._test_state:
            return []
        return self._test_state.test_def.get("beep_intervals", [])

    async def start_timer(self) -> str:
        """Start timer for timed test."""
        if not self._test_state:
            return "No active test."

        if not self.current_test_is_timed() and not self.current_test_is_countdown():
            return "This test doesn't use a timer."

        self._timer_start = time.time()
        return "Timing..."

    async def stop_timer(self) -> tuple[float, str]:
        """
        Stop timer and record elapsed time.

        Returns:
            (elapsed_seconds, response_message)
        """
        if not self._timer_start:
            return 0.0, "No timer running."

        elapsed = time.time() - self._timer_start
        self._timer_start = None

        # Cap at max time if applicable
        max_time = self.get_max_time()
        if elapsed >= max_time:
            elapsed = float(max_time)
            response = await self.record_result(elapsed)
            return elapsed, f"{int(elapsed)} seconds. Maximum reached. " + response.split(". ", 1)[-1]

        elapsed = round(elapsed, 1)
        response = await self.record_result(elapsed)
        return elapsed, response

    def check_timer_elapsed(self) -> Optional[float]:
        """Check elapsed time without stopping. Returns None if no timer."""
        if not self._timer_start:
            return None
        return time.time() - self._timer_start

    # ========================================
    # Input Parsing
    # ========================================

    async def parse_and_record(self, text: str) -> str:
        """
        Parse spoken input and record result.

        Handles all input types based on current test definition.
        """
        if not self._test_state:
            return "No active test."

        test = self._test_state.test_def
        input_type = test.get("input_type", "numeric")

        # Handle different input types
        if input_type == "numeric":
            value = parse_spoken_number(text)
            if value is None:
                return "Didn't catch that number. Try again?"

            # Validate range
            valid_range = test.get("valid_range")
            if valid_range and (value < valid_range[0] or value > valid_range[1]):
                return f"Value {value} seems outside expected range {valid_range[0]}-{valid_range[1]}. Say again or confirm."

            return await self.record_result(value)

        elif input_type == "boolean":
            value = parse_boolean(text)
            if value is None:
                return "Yes or no?"

            return await self.record_result(1 if value else 0)

        elif input_type == "categorical":
            options = test.get("options", [])
            value = parse_categorical(text, options)
            if value is None:
                options_str = ", ".join(options)
                return f"Choose one: {options_str}."

            return await self.record_result(value)

        elif input_type == "fms":
            value = parse_fms_score(text)
            if value is None:
                return "Score zero to three. Zero if any pain."

            return await self.record_result(value)

        elif input_type == "compound":
            return await self._handle_compound_input(text)

        elif input_type == "multi_attempt":
            return await self._handle_multi_attempt_input(text)

        elif input_type == "duration":
            value = parse_duration(text)
            if value is None:
                value = parse_spoken_number(text, allow_duration=True)
            if value is None:
                return "Give me the time in minutes and seconds, like 5:30."

            return await self.record_result(value)

        elif input_type == "calculated":
            # Skip calculated fields
            return await self.skip_test()

        elif input_type == "timed":
            # User gave number directly instead of using timer
            value = parse_spoken_number(text)
            if value is not None:
                return await self.record_result(value)
            return "Say go to start the timer, or give me the time in seconds."

        elif input_type == "countdown_reps":
            # User giving reps count
            value = parse_spoken_number(text)
            if value is not None:
                return await self.record_result(value)
            return "How many reps did you complete?"

        else:
            # Default to numeric
            value = parse_spoken_number(text)
            if value is None:
                return "Didn't catch that. Try again?"
            return await self.record_result(value)

    async def _handle_compound_input(self, text: str) -> str:
        """Handle compound input type (multiple fields)."""
        test = self._test_state.test_def
        fields = test.get("fields", [])
        test_id = self._test_state.test_id

        if not fields:
            # Fallback to simple numeric
            value = parse_spoken_number(text)
            if value is not None:
                return await self.record_result(value)
            return "Didn't catch that number."

        # Check for blood pressure natural speech: "120 over 80"
        if "blood_pressure" in test_id and self._test_state.compound_field_idx == 0:
            systolic, diastolic = parse_blood_pressure(text)
            if systolic is not None and diastolic is not None:
                # Got both values in one phrase
                self._test_state.compound_values["systolic"] = systolic
                self._test_state.compound_values["diastolic"] = diastolic
                self._test_state.compound_field_idx = len(fields)  # Skip to end
                return await self._finalize_compound()

        # Check for weight+reps natural speech: "20 kilos for 5 reps"
        field_names = [f.get("name", "") for f in fields]
        if "weight" in field_names and "reps" in field_names and self._test_state.compound_field_idx == 0:
            weight, reps = parse_weight_reps(text)
            if weight is not None and reps is not None:
                self._test_state.compound_values["weight"] = weight
                self._test_state.compound_values["reps"] = reps
                self._test_state.compound_field_idx = len(fields)
                return await self._finalize_compound()

        # Current field (sequential input)
        idx = self._test_state.compound_field_idx
        if idx >= len(fields):
            # All fields complete - calculate and record
            return await self._finalize_compound()

        field_def = fields[idx]
        value = parse_spoken_number(text)

        if value is None:
            return f"{field_def.get('prompt', 'Value?')}"

        # Validate range
        valid_range = field_def.get("valid_range")
        if valid_range and (value < valid_range[0] or value > valid_range[1]):
            return f"Value {value} outside expected range. {field_def.get('prompt', 'Try again?')}"

        # Store value
        self._test_state.compound_values[field_def.get("name", f"field_{idx}")] = value
        self._test_state.compound_field_idx += 1

        # Check if more fields
        if self._test_state.compound_field_idx < len(fields):
            next_field = fields[self._test_state.compound_field_idx]
            return f"Got {value}. {next_field.get('prompt', 'Next value?')}"

        # All fields complete
        return await self._finalize_compound()

    async def _finalize_compound(self) -> str:
        """Finalize compound input and calculate derived values."""
        test = self._test_state.test_def
        values = self._test_state.compound_values

        # Calculate if formula specified
        calculate = test.get("calculate")
        if calculate == "1rm_brzycki":
            weight = values.get("weight", 0)
            reps = values.get("reps", 1)
            estimated_1rm = calculate_1rm_brzycki(weight, int(reps))

            # Reset compound state
            self._test_state.compound_field_idx = 0
            self._test_state.compound_values = {}

            # Record the 1RM
            response = await self.record_result(estimated_1rm)
            return f"Calculated 1RM: {estimated_1rm} kg. {response}"

        else:
            # Just record the primary value
            primary_value = list(values.values())[0] if values else 0
            self._test_state.compound_field_idx = 0
            self._test_state.compound_values = {}
            return await self.record_result(primary_value)

    async def _handle_multi_attempt_input(self, text: str) -> str:
        """Handle multi-attempt input (best of N)."""
        test = self._test_state.test_def
        max_attempts = test.get("attempts", 3)
        record_method = test.get("record", "best")

        value = parse_spoken_number(text)
        if value is None:
            return f"Attempt {self._test_state.attempt} of {max_attempts}. What's the measurement?"

        # Store attempt
        if "attempts" not in self._test_state.compound_values:
            self._test_state.compound_values["attempts"] = []
        self._test_state.compound_values["attempts"].append(value)

        self._test_state.attempt += 1

        if self._test_state.attempt <= max_attempts:
            attempts = self._test_state.compound_values["attempts"]
            current_best = max(attempts) if record_method == "best" else min(attempts)
            return f"Got {value}. Best so far: {current_best}. Attempt {self._test_state.attempt}?"

        # All attempts complete
        attempts = self._test_state.compound_values["attempts"]
        if record_method == "best":
            final_value = max(attempts)
        else:
            final_value = min(attempts)

        self._test_state.attempt = 1
        self._test_state.compound_values = {}

        response = await self.record_result(final_value)
        return f"Best of {max_attempts}: {final_value}. {response}"

    # ========================================
    # Helper Methods
    # ========================================

    def _get_first_test(self, session_id: str) -> Optional[dict]:
        """Get first test in session."""
        session = self.config.get("sessions", {}).get(session_id, {})
        for section in session.get("sections", []):
            tests = section.get("tests", [])
            if tests:
                return tests[0]
        return None

    def _find_test_by_id(self, session_id: str, test_id: str) -> Optional[dict]:
        """Find test definition by ID."""
        session = self.config.get("sessions", {}).get(session_id, {})
        for section in session.get("sections", []):
            for test in section.get("tests", []):
                if test.get("id") == test_id:
                    return test
        return None

    def _find_section_for_test(self, session_id: str, test_id: str) -> str:
        """Find section name containing a test."""
        session = self.config.get("sessions", {}).get(session_id, {})
        for section in session.get("sections", []):
            for test in section.get("tests", []):
                if test.get("id") == test_id:
                    return section.get("name", "Unknown")
        return "Unknown"

    def _count_total_tests(self, session_id: str) -> int:
        """Count total tests in session."""
        session = self.config.get("sessions", {}).get(session_id, {})
        total = 0
        for section in session.get("sections", []):
            total += len(section.get("tests", []))
        return total

    def _format_test_prompt(self, test: dict) -> str:
        """Format voice prompt for a test."""
        return test.get("voice_prompt", test.get("name", "Next test?"))

    def _advance_to_next(self) -> bool:
        """
        Advance to next test in session.

        Returns:
            True if advanced, False if session complete
        """
        if not self._state or not self._test_state:
            return False

        session = self.config.get("sessions", {}).get(self._state.session_id, {})
        current_id = self._test_state.test_id

        # Find current test and get next
        found_current = False
        for section in session.get("sections", []):
            for test in section.get("tests", []):
                if found_current:
                    # This is the next test
                    self._state.current_test_id = test["id"]
                    self._test_state = TestState(
                        test_id=test["id"],
                        test_def=test,
                        section_name=section.get("name", "Unknown"),
                    )
                    return True
                if test.get("id") == current_id:
                    found_current = True

        # No more tests
        return False

    # ========================================
    # State Persistence
    # ========================================

    def _save_state(self) -> None:
        """Save session state to database."""
        if not self._state:
            return

        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO assessment_session_state
                (session_id, current_test_id, started_at, updated_at, results_logged, last_value, last_test_id, protocol_run)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    current_test_id = excluded.current_test_id,
                    updated_at = excluded.updated_at,
                    results_logged = excluded.results_logged,
                    last_value = excluded.last_value,
                    last_test_id = excluded.last_test_id,
                    protocol_run = excluded.protocol_run
            """, (
                self._state.session_id,
                self._state.current_test_id,
                self._state.started_at,
                self._state.updated_at,
                self._state.results_logged,
                self._state.last_value,
                self._state.last_test_id,
                self._state.protocol_run,
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
        finally:
            conn.close()

    def _load_state(self) -> None:
        """Load session state from database."""
        conn = self._get_conn()
        try:
            # Ensure table exists with protocol_run column
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assessment_session_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    current_test_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    results_logged INTEGER DEFAULT 0,
                    last_value TEXT,
                    last_test_id TEXT,
                    notes TEXT,
                    protocol_run TEXT,
                    UNIQUE(session_id)
                )
            """)

            # Add protocol_run column if missing (migration for existing DBs)
            try:
                conn.execute("ALTER TABLE assessment_session_state ADD COLUMN protocol_run TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists

            cursor = conn.execute("""
                SELECT * FROM assessment_session_state
                ORDER BY updated_at DESC LIMIT 1
            """)
            row = cursor.fetchone()

            if row:
                # Handle case where protocol_run might not exist in old rows
                protocol_run = row["protocol_run"] if "protocol_run" in row.keys() else None
                self._state = SessionState(
                    session_id=row["session_id"],
                    current_test_id=row["current_test_id"],
                    started_at=row["started_at"],
                    updated_at=row["updated_at"],
                    results_logged=row["results_logged"],
                    last_value=row["last_value"],
                    last_test_id=row["last_test_id"],
                    protocol_run=protocol_run,
                )
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            self._state = None
        finally:
            conn.close()

    def _clear_state(self) -> None:
        """Clear session state from database."""
        if not self._state:
            return

        conn = self._get_conn()
        try:
            conn.execute("""
                DELETE FROM assessment_session_state WHERE session_id = ?
            """, (self._state.session_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear state: {e}")
        finally:
            conn.close()

        self._state = None
        self._test_state = None


# Export
__all__ = ["AssessmentProtocolRunner"]
