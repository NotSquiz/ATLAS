"""Intent dispatcher for voice pipeline.

Refactored from process_audio() in bridge_file_server.py to separate
intent detection and routing logic from audio processing.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from atlas.voice.bridge_file_server import BridgeFileServer

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result from intent handling."""

    response_text: str
    action_type: str = "query"
    saved_to: str = ""
    tier_override: str | None = None
    handled: bool = True


def _make_decision(tier_value: str, confidence: float = 1.0) -> Any:
    """Create a mock decision object matching router.classify() output.

    Args:
        tier_value: The tier string (e.g., 'WORKOUT', 'HEALTH', 'ASSESSMENT')
        confidence: Confidence score (default 1.0 for intents)

    Returns:
        A mock object with tier.value and confidence attributes
    """
    return type(
        "obj",
        (object,),
        {"tier": type("t", (object,), {"value": tier_value})(), "confidence": confidence},
    )()


class IntentDispatcher:
    """Dispatches voice intents to appropriate handlers.

    Extracts the massive if/elif chain from process_audio() into a clean
    dispatcher pattern with grouped handlers by priority.

    Priority order (highest to lowest):
    1. Stateful sessions (assessment active, workout confirmation pending)
    2. Active workout/routine sessions
    3. Pending states (phase reset, session choice)
    4. Start commands (workout, routine, assessment, phase)
    5. Logging commands (weight, pain, supplements, workout completion)
    6. Query commands (health status, schedule, exercise info)
    7. Capture intents (remember, note)
    8. Meal logging
    """

    def __init__(self, server: "BridgeFileServer"):
        """Initialize dispatcher with server reference.

        Args:
            server: Reference to BridgeFileServer for state access and handlers
        """
        self.server = server

    def dispatch(self, text: str) -> IntentResult | None:
        """Dispatch text to appropriate intent handler.

        Returns IntentResult if intent was handled, None if should fall through to LLM.

        Args:
            text: Transcribed text from STT

        Returns:
            IntentResult if an intent was matched and handled, None otherwise
        """
        # Try handlers in priority order
        result = self._try_stateful_handlers(text)
        if result:
            return result

        result = self._try_active_session_handlers(text)
        if result:
            return result

        result = self._try_pending_state_handlers(text)
        if result:
            return result

        result = self._try_start_handlers(text)
        if result:
            return result

        result = self._try_logging_handlers(text)
        if result:
            return result

        result = self._try_query_handlers(text)
        if result:
            return result

        result = self._try_capture_handlers(text)
        if result:
            return result

        result = self._try_meal_handlers(text)
        if result:
            return result

        # No intent matched - fall through to LLM
        return None

    # =========================================================================
    # Handler Groups
    # =========================================================================

    def _try_stateful_handlers(self, text: str) -> IntentResult | None:
        """Handle stateful sessions (highest priority).

        These handlers take precedence because they represent ongoing
        conversations that should not be interrupted.
        """
        # Workout confirmation pending
        if self.server._is_workout_confirmation(text):
            logger.debug("[Intent: WORKOUT_CONFIRM]")
            try:
                response = asyncio.run(self.server._handle_workout_confirmation(text))
            except Exception as e:
                logger.debug(f"[WORKOUT_CONFIRM ERROR: {e}]")
                response = f"Confirmation failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="workout_complete",
                saved_to="workouts",
                tier_override="WORKOUT_COMPLETE",
            )

        # Assessment active (highest priority when running)
        if self.server._is_assessment_active():
            logger.debug("[Intent: ASSESSMENT_INPUT]")
            try:
                response = asyncio.run(self.server._handle_assessment_input(text))
            except Exception as e:
                logger.debug(f"[ASSESSMENT_INPUT ERROR: {e}]")
                import traceback
                traceback.print_exc()
                response = f"Assessment input failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="assessment",
                saved_to="assessments",
                tier_override="ASSESSMENT",
            )

        # Assessment session pending (user needs to pick A/B/C)
        if self.server._is_assessment_session_pending():
            logger.debug("[Intent: ASSESSMENT_SESSION_CHOICE]")
            try:
                response = asyncio.run(self.server._handle_assessment_session_choice(text))
            except Exception as e:
                logger.debug(f"[ASSESSMENT_SESSION_CHOICE ERROR: {e}]")
                response = f"Session selection failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="assessment",
                tier_override="ASSESSMENT",
            )

        # Assessment resume intent
        if self.server._is_assessment_resume_intent(text):
            logger.debug("[Intent: ASSESSMENT_RESUME]")
            try:
                response = asyncio.run(self.server._handle_assessment_resume())
            except Exception as e:
                logger.debug(f"[ASSESSMENT_RESUME ERROR: {e}]")
                response = f"Resume failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="assessment",
                tier_override="ASSESSMENT",
            )

        # Assessment info query
        if self.server._is_assessment_info_intent(text):
            logger.debug("[Intent: ASSESSMENT_INFO]")
            try:
                response = asyncio.run(self.server._handle_assessment_info(text))
            except Exception as e:
                logger.debug(f"[ASSESSMENT_INFO ERROR: {e}]")
                response = f"Assessment info failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="assessment_info",
                tier_override="ASSESSMENT_INFO",
            )

        # Assessment start intent
        if self.server._is_assessment_start_intent(text):
            logger.debug("[Intent: ASSESSMENT_START]")
            try:
                response = asyncio.run(self.server._handle_assessment_start(text))
            except Exception as e:
                logger.debug(f"[ASSESSMENT_START ERROR: {e}]")
                response = f"Assessment start failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="assessment",
                tier_override="ASSESSMENT",
            )

        # Seneca Trial (reflection) active
        if self.server._is_reflection_active():
            logger.debug("[Intent: REFLECTION_INPUT]")
            try:
                response = asyncio.run(self.server._handle_reflection_input(text))
            except Exception as e:
                logger.debug(f"[REFLECTION_INPUT ERROR: {e}]")
                response = f"Reflection input failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="reflection",
                saved_to="daily_reflections",
                tier_override="REFLECTION",
            )

        return None

    def _try_active_session_handlers(self, text: str) -> IntentResult | None:
        """Handle active workout/routine sessions.

        These have complex sub-state machines for different phases
        of the workout or routine.
        """
        # Interactive workout active
        if self.server.workout.active:
            result = self._handle_active_workout(text)
            if result:
                return result

        # Interactive routine active
        if self.server.routine.active:
            result = self._handle_active_routine(text)
            if result:
                return result

        return None

    def _try_pending_state_handlers(self, text: str) -> IntentResult | None:
        """Handle pending states that need confirmation or choice."""
        # Phase reset pending (confirmation required)
        if self.server._phase_reset_pending:
            # Check for timeout (30 seconds)
            if self.server._phase_reset_time and (time.time() - self.server._phase_reset_time) > 30:
                self.server._phase_reset_pending = False
                self.server._phase_reset_time = None
                response = "Reset timed out. No changes made."
            elif self.server._is_phase_confirm_command(text):
                logger.debug("[Intent: PHASE_CONFIRM]")
                try:
                    response = asyncio.run(self.server._handle_phase_confirm())
                except Exception as e:
                    response = f"Reset failed: {e}"
            elif self.server._is_cancel_command(text):
                logger.debug("[Intent: PHASE_CANCEL]")
                try:
                    response = asyncio.run(self.server._handle_phase_cancel())
                except Exception as e:
                    response = f"Cancel failed: {e}"
            else:
                response = "Say confirm to reset to Day 1, or cancel to keep current progress."
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="phase_confirm",
                tier_override="SCHEDULE",
            )

        return None

    def _try_start_handlers(self, text: str) -> IntentResult | None:
        """Handle start commands for workouts, routines, assessments, phases."""
        # Schedule status query
        if self.server._is_schedule_status_intent(text):
            logger.debug("[Intent: SCHEDULE_STATUS]")
            try:
                response = asyncio.run(self.server._handle_schedule_status())
            except Exception as e:
                logger.debug(f"[SCHEDULE_STATUS ERROR: {e}]")
                response = f"Schedule check failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="schedule_status",
                tier_override="SCHEDULE",
            )

        # Phase start request
        if self.server._is_phase_start_intent(text):
            logger.debug("[Intent: PHASE_START_REQUEST]")
            try:
                response = asyncio.run(self.server._handle_phase_start_request(text))
            except Exception as e:
                logger.debug(f"[PHASE_START ERROR: {e}]")
                response = f"Phase start failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="phase_start",
                tier_override="SCHEDULE",
            )

        # Workout start or traffic override
        if self.server._is_workout_start_intent(text) or self.server._detect_traffic_override(text):
            traffic_override = self.server._detect_traffic_override(text)
            protocol_id = self.server._parse_workout_type(text)
            logger.debug(f"[Intent: WORKOUT_START (override={traffic_override}, protocol={protocol_id})]")
            try:
                response = asyncio.run(
                    self.server._start_interactive_workout(
                        traffic_override=traffic_override,
                        protocol_id=protocol_id,
                    )
                )
            except Exception as e:
                logger.debug(f"[WORKOUT_START ERROR: {e}]")
                import traceback
                traceback.print_exc()
                response = f"Workout start failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="workout_start",
                tier_override="WORKOUT_INTERACTIVE",
            )

        # Routine start
        if self.server._is_routine_start_intent(text):
            logger.debug("[Intent: ROUTINE_START]")
            try:
                response = asyncio.run(self.server._start_interactive_routine())
            except Exception as e:
                logger.error(f"[ROUTINE_START ERROR: {e}]")
                response = f"Routine start failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="routine_start",
                tier_override="ROUTINE_INTERACTIVE",
            )

        # Seneca Trial (reflection) start
        if self.server._is_reflection_start_intent(text):
            is_quick = self.server._is_quick_reflection_intent(text)
            logger.debug(f"[Intent: REFLECTION_START (quick={is_quick})]")
            try:
                response = asyncio.run(self.server._start_reflection(is_quick))
            except Exception as e:
                logger.error(f"[REFLECTION_START ERROR: {e}]")
                response = f"Reflection start failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="reflection_start",
                tier_override="REFLECTION",
            )

        return None

    def _try_logging_handlers(self, text: str) -> IntentResult | None:
        """Handle logging commands (weight, pain, supplements, workout completion)."""
        # Weight query (before weight logging)
        weight_query = self.server._is_weight_query_intent(text)
        if weight_query[0]:
            _, query_type = weight_query
            logger.debug(f"[Intent: WEIGHT_QUERY - {query_type}]")
            try:
                response = asyncio.run(self.server._handle_weight_query(query_type))
            except Exception as e:
                logger.debug(f"[WEIGHT_QUERY ERROR: {e}]")
                response = f"Weight query failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="weight_query",
                tier_override="WEIGHT_QUERY",
            )

        # Weight logging (with body composition)
        weight_result = self.server._is_weight_intent(text)
        if weight_result[0] and weight_result[1]:
            body_comp = weight_result[1]
            extras = []
            if body_comp.body_fat_pct:
                extras.append(f"{body_comp.body_fat_pct}% fat")
            if body_comp.muscle_mass_pct:
                extras.append(f"{body_comp.muscle_mass_pct}% muscle")
            extra_str = f" ({', '.join(extras)})" if extras else ""
            logger.debug(f"[Intent: WEIGHT - {body_comp.weight_kg}kg{extra_str}]")
            try:
                response = asyncio.run(self.server._handle_weight_log(body_comp))
            except Exception as e:
                logger.debug(f"[WEIGHTHANDLER ERROR: {e}]")
                response = f"Weight logging failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="weight",
                saved_to="weight_log",
                tier_override="WEIGHT",
            )

        # Pain logging
        pain_result = self.server._is_pain_intent(text)
        if pain_result[0]:
            _, body_part, pain_level, is_status = pain_result
            logger.debug(f"[Intent: PAIN - {body_part}:{pain_level} status={is_status}]")
            try:
                response = asyncio.run(self.server._handle_pain(body_part, pain_level, is_status))
            except Exception as e:
                logger.debug(f"[PAINHANDLER ERROR: {e}]")
                response = f"Pain logging failed: {e}"
            print(f"ATLAS: {response}")
            saved_to = "pain_log" if pain_level is not None else ""
            return IntentResult(
                response_text=response,
                action_type="pain",
                saved_to=saved_to,
                tier_override="PAIN",
            )

        # Supplement logging
        supp_result = self.server._is_supplement_intent(text)
        if supp_result[0]:
            _, supp_name, timing, is_status, status_type = supp_result
            logger.debug(
                f"[Intent: SUPPLEMENT - {supp_name or 'batch'}/{timing or 'none'} "
                f"status={is_status} type={status_type}]"
            )
            try:
                response = asyncio.run(
                    self.server._handle_supplement(supp_name, timing, is_status, status_type)
                )
            except Exception as e:
                logger.debug(f"[SUPPLEMENTHANDLER ERROR: {e}]")
                response = f"Supplement logging failed: {e}"
            print(f"ATLAS: {response}")
            saved_to = "supplement_log" if not is_status else ""
            return IntentResult(
                response_text=response,
                action_type="supplement",
                saved_to=saved_to,
                tier_override="SUPPLEMENT",
            )

        # Workout completion
        workout_complete = self.server._is_workout_completion_intent(text)
        if workout_complete[0]:
            _, has_issues = workout_complete
            logger.debug(f"[Intent: WORKOUT_COMPLETE - issues={has_issues}]")
            try:
                response = asyncio.run(self.server._handle_workout_completion(text, has_issues))
            except Exception as e:
                logger.debug(f"[WORKOUT_COMPLETE ERROR: {e}]")
                response = f"Workout logging failed: {e}"
            print(f"ATLAS: {response}")
            saved_to = "workouts" if "logged" in response.lower() else ""
            return IntentResult(
                response_text=response,
                action_type="workout_complete",
                saved_to=saved_to,
                tier_override="WORKOUT_COMPLETE",
            )

        return None

    def _try_query_handlers(self, text: str) -> IntentResult | None:
        """Handle query commands (health status, workout info, exercise info, skill status)."""
        # Skill/XP status query
        if self.server._is_skill_status_intent(text):
            logger.debug("[Intent: SKILL_STATUS]")
            try:
                response = asyncio.run(self.server._handle_skill_status())
            except Exception as e:
                print(f"[SKILL_STATUS HANDLER ERROR: {e}]")
                response = "Skill status unavailable."
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="skill_status",
                tier_override="SKILL_STATUS",
            )

        # Workout query
        if self.server._is_workout_intent(text):
            logger.debug("[Intent: WORKOUT]")
            try:
                response = asyncio.run(self.server._handle_workout_query())
            except Exception as e:
                print(f"[WORKOUT HANDLER ERROR: {e}]")
                response = f"Workout lookup failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="workout",
                tier_override="WORKOUT",
            )

        # Exercise query
        exercise_result = self.server._is_exercise_intent(text)
        if exercise_result[0]:
            _, exercise_name = exercise_result
            logger.debug(f"[Intent: EXERCISE - {exercise_name}]")
            try:
                response = asyncio.run(self.server._handle_exercise_query(exercise_name))
            except Exception as e:
                print(f"[EXERCISE HANDLER ERROR: {e}]")
                response = f"Exercise lookup failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="exercise",
                tier_override="EXERCISE",
            )

        # Health status
        if self.server._is_health_intent(text):
            logger.debug("[Intent: HEALTH]")
            try:
                response = asyncio.run(self.server._handle_health_status(text))
            except Exception as e:
                print(f"[HEALTH HANDLER ERROR: {e}]")
                import traceback
                traceback.print_exc()
                response = f"Status check failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="health",
                tier_override="HEALTH",
            )

        return None

    def _try_capture_handlers(self, text: str) -> IntentResult | None:
        """Handle capture intents (remember, note, save)."""
        if self.server._is_capture_intent(text):
            logger.debug("[Intent: CAPTURE]")
            response = asyncio.run(self.server._handle_capture(text))
            print(f"ATLAS: {response}")
            # Extract destination from response (format: "Saved to X." or "Saved to X:Y.")
            saved_to = ""
            if "Saved to " in response:
                saved_to = response.split("Saved to ")[1].rstrip(".")
            return IntentResult(
                response_text=response,
                action_type="capture",
                saved_to=saved_to,
                tier_override="CAPTURE",
            )

        return None

    def _try_meal_handlers(self, text: str) -> IntentResult | None:
        """Handle meal logging intents."""
        if self.server._is_meal_intent(text):
            logger.debug("[Intent: MEAL]")
            try:
                response = asyncio.run(self.server._handle_meal(text))
            except Exception as e:
                print(f"[MEAL HANDLER ERROR: {e}]")
                import traceback
                traceback.print_exc()
                response = f"Meal logging failed: {e}"
            print(f"ATLAS: {response}")
            return IntentResult(
                response_text=response,
                action_type="meal",
                saved_to="semantic_memory:health:meals",
                tier_override="MEAL",
            )

        return None

    # =========================================================================
    # Complex State Machine Handlers
    # =========================================================================

    def _handle_active_workout(self, text: str) -> IntentResult | None:
        """Handle all intents when an interactive workout is active.

        The workout state machine has multiple sub-states:
        - rest_active: Rest timer between sets
        - exercise_pending: Waiting for user to say "ready"
        - awaiting_reps: Waiting for AMRAP rep count
        - set_active: User performing a set
        - exercise_timer_active: Timed exercise in progress
        """
        response_text = ""

        # Check rest timer first (may have message even without user input)
        timer_msg, beeps = self.server._check_workout_rest_timer()

        # Check exercise timer (for timed holds like balance exercises)
        ex_timer_msg, ex_beeps = self.server._check_workout_exercise_timer()

        # Handle last set of timed exercise (needs async advance)
        last_set_advanced = False
        if self.server.workout.last_set_of_timed_exercise:
            self.server.workout.last_set_of_timed_exercise = False
            last_set_advanced = True
            try:
                response_text = asyncio.run(self.server._advance_to_next_exercise())
            except Exception as e:
                response_text = f"Advance failed: {e}"

        # Play countdown beeps if any triggered (rest timer)
        if beeps:
            from atlas.voice.audio_utils import play_countdown_beep

            for bp in beeps:
                play_countdown_beep(bp)
                logger.debug(f"[WORKOUT_REST_BEEP: {bp}s remaining]")

        # Play exercise timer beeps
        if ex_beeps:
            from atlas.voice.audio_utils import play_countdown_beep

            for bp in ex_beeps:
                play_countdown_beep(bp)
                logger.debug(f"[WORKOUT_EX_BEEP: {bp}s remaining]")

        # If we just advanced from last timed set, skip other checks
        if last_set_advanced:
            pass  # response_text already set

        # Global stop check (works in any workout state)
        elif self.server._is_workout_stop_command(text):
            logger.debug("[Intent: WORKOUT_STOP]")
            try:
                response_text = asyncio.run(self.server._handle_workout_stop())
            except Exception as e:
                logger.debug(f"[WORKOUT_STOP ERROR: {e}]")
                response_text = f"Stop failed: {e}"

        # Workout completion check (allows "finished workout" during active workout)
        elif self.server._is_workout_completion_intent(text)[0]:
            _, has_issues = self.server._is_workout_completion_intent(text)
            logger.debug(f"[Intent: WORKOUT_COMPLETE (during active) - issues={has_issues}]")
            try:
                # Stop the workout first, then log it
                self.server._force_reset_workout_state()
                response_text = asyncio.run(self.server._handle_workout_completion(text, has_issues))
            except Exception as e:
                logger.debug(f"[WORKOUT_COMPLETE ERROR: {e}]")
                import traceback
                traceback.print_exc()
                response_text = f"Completion failed: {e}"

        # Global pause check (works in any workout state when not already paused)
        elif self.server._is_workout_pause_command(text) and not self.server.workout.paused:
            logger.debug("[Intent: WORKOUT_PAUSE]")
            try:
                response_text = asyncio.run(self.server._handle_workout_pause())
            except Exception as e:
                logger.debug(f"[WORKOUT_PAUSE ERROR: {e}]")
                response_text = f"Pause failed: {e}"

        # Global resume check (works when paused)
        elif self.server._is_workout_resume_command(text) and self.server.workout.paused:
            logger.debug("[Intent: WORKOUT_RESUME]")
            try:
                response_text = asyncio.run(self.server._handle_workout_resume())
            except Exception as e:
                logger.debug(f"[WORKOUT_RESUME ERROR: {e}]")
                response_text = f"Resume failed: {e}"

        # Restart workout if user says "start workout" again (handles stuck state)
        elif self.server._is_workout_start_intent(text):
            logger.debug("[Intent: WORKOUT_RESTART (was active)]")
            # Reset all workout state before restarting
            self.server.workout.active = False
            self.server.workout.rest_active = False
            self.server.workout.set_active = False
            self.server.workout.exercise_pending = False
            self.server.workout.exercise_timer_active = False
            self.server.workout.awaiting_reps = False
            self.server.workout.last_set_of_timed_exercise = False
            try:
                traffic_override = self.server._detect_traffic_override(text)
                protocol_id = self.server._parse_workout_type(text)
                response_text = asyncio.run(
                    self.server._start_interactive_workout(
                        traffic_override=traffic_override,
                        protocol_id=protocol_id,
                    )
                )
            except Exception as e:
                logger.debug(f"[WORKOUT_RESTART ERROR: {e}]")
                import traceback
                traceback.print_exc()
                response_text = f"Workout restart failed: {e}"

        # During rest period
        elif self.server.workout.rest_active:
            response_text = self._handle_workout_rest_state(text, timer_msg)

        # Waiting for user to be ready for set/exercise
        elif self.server.workout.exercise_pending:
            response_text = self._handle_workout_pending_state(text)

        # Waiting for AMRAP rep count after "How many reps?"
        elif self.server.workout.awaiting_reps:
            response_text = self._handle_workout_awaiting_reps(text)

        # User doing a set
        elif self.server.workout.set_active:
            response_text = self._handle_workout_set_active(text, ex_timer_msg)

        else:
            # Fallback - shouldn't reach here normally
            logger.debug(
                f"[WORKOUT_UNCLEAR_STATE: rest={self.server.workout.rest_active}, "
                f"pending={self.server.workout.exercise_pending}, "
                f"set_active={self.server.workout.set_active}, "
                f"awaiting_reps={self.server.workout.awaiting_reps}, "
                f"timer={self.server.workout.exercise_timer_active}, "
                f"last_set_flag={self.server.workout.last_set_of_timed_exercise}]"
            )
            response_text = "Workout active but unclear state. Say ready, done, or stop workout."

        print(f"ATLAS: {response_text}")
        return IntentResult(
            response_text=response_text,
            action_type="workout_interactive",
            tier_override="WORKOUT_INTERACTIVE",
        )

    def _handle_workout_rest_state(self, text: str, timer_msg: str | None) -> str:
        """Handle intents during workout rest period."""
        if self.server._is_workout_skip_command(text):
            logger.debug("[Intent: WORKOUT_SKIP (rest)]")
            try:
                return asyncio.run(self.server._handle_workout_skip())
            except Exception as e:
                return f"Skip failed: {e}"

        if "how long" in text.lower() or "time" in text.lower():
            remaining = self.server._get_workout_rest_remaining()
            return f"{remaining} seconds left."

        if self.server._is_workout_ready_command(text):
            # User ready early, skip rest
            self.server.workout.rest_active = False
            logger.debug("[Intent: WORKOUT_READY (early)]")
            try:
                return asyncio.run(self.server._handle_workout_ready(text))
            except Exception as e:
                return f"Ready failed: {e}"

        if timer_msg:
            # Rest timer finished
            return timer_msg

        # During rest, acknowledge but don't do anything
        remaining = self.server._get_workout_rest_remaining()
        return f"Resting. {remaining} seconds. Say ready to skip."

    def _handle_workout_pending_state(self, text: str) -> str:
        """Handle intents while waiting for user to be ready."""
        if self.server._is_workout_ready_command(text):
            logger.debug("[Intent: WORKOUT_READY]")
            try:
                return asyncio.run(self.server._handle_workout_ready(text))
            except Exception as e:
                return f"Ready failed: {e}"

        if self.server._is_workout_skip_command(text):
            logger.debug("[Intent: WORKOUT_SKIP]")
            try:
                return asyncio.run(self.server._handle_workout_skip())
            except Exception as e:
                return f"Skip failed: {e}"

        if self.server._is_workout_stop_command(text):
            # Allow stopping workout from READY screen
            logger.debug("[Intent: WORKOUT_STOP from READY]")
            try:
                return asyncio.run(self.server._handle_workout_stop())
            except Exception as e:
                return f"Stop failed: {e}"

        if text.lower().strip() in ["done", "finished", "done.", "finished."]:
            # Simple "done" or "finished" on READY screen = stop workout
            logger.debug("[Intent: WORKOUT_STOP from READY (done/finished)]")
            try:
                return asyncio.run(self.server._handle_workout_stop())
            except Exception as e:
                return f"Stop failed: {e}"

        if self.server._is_workout_completion_intent(text)[0]:
            # Allow completing workout from READY screen
            logger.debug("[Intent: WORKOUT_COMPLETE from READY]")
            _, has_issues = self.server._is_workout_completion_intent(text)
            if has_issues:
                # Store pending completion for confirmation
                self.server._pending_workout = {
                    "created_at": time.time(),
                    "has_issues": True,
                }
                return "Got it. What did you skip or modify? Any notes?"
            else:
                try:
                    return asyncio.run(self.server._handle_workout_completion(text, False))
                except Exception as e:
                    return f"Logging failed: {e}"

        # Check if user is providing weight
        from atlas.voice.number_parser import parse_weight_value

        weight = parse_weight_value(text)
        if weight:
            self.server.workout.current_weight = weight
            return f"Got it. {int(weight)} kilos. Say ready to begin."

        ex = self.server.workout.current_exercise
        ex_name = ex["name"] if ex else "exercise"
        return f"Waiting for you. Say ready when set up for {ex_name}."

    def _handle_workout_awaiting_reps(self, text: str) -> str:
        """Handle intents while awaiting AMRAP rep count."""
        from atlas.voice.number_parser import parse_spoken_number

        reps = parse_spoken_number(text)
        if reps:
            logger.debug(f"[Intent: WORKOUT_AMRAP_REPS - {reps}]")
            try:
                self.server.workout.set_reps.append(int(reps))
                self.server.workout.awaiting_reps = False
                return asyncio.run(self.server._advance_to_next_exercise())
            except Exception as e:
                return f"Rep logging failed: {e}"
        return "How many reps did you get?"

    def _handle_workout_set_active(self, text: str, ex_timer_msg: str | None) -> str:
        """Handle intents while user is performing a set."""
        # Check for exercise timer message (switch sides, set complete)
        if ex_timer_msg:
            return ex_timer_msg

        if self.server._is_workout_set_done_command(text):
            logger.debug("[Intent: WORKOUT_SET_DONE]")
            # For timed exercises, "done" skips remaining time
            if self.server.workout.exercise_timer_active:
                self.server.workout.exercise_timer_active = False
                # Manually complete the timed set
                ex = self.server.workout.current_exercise
                is_per_side = ex.get("per_side", False) if ex else False
                if is_per_side and self.server.workout.exercise_sides_done == 0:
                    # Skip to second side
                    self.server.workout.exercise_sides_done = 1
                    self.server.workout.exercise_current_side = "right"
                    self.server.workout.exercise_timer_start = time.monotonic()
                    self.server.workout.exercise_timer_active = True
                    self.server.workout.exercise_beeps_played = set()
                    return "Skipping to right side. Begin."
                else:
                    # Complete the set entirely
                    return asyncio.run(self.server._handle_workout_set_done(text))
            else:
                try:
                    return asyncio.run(self.server._handle_workout_set_done(text))
                except Exception as e:
                    return f"Set done failed: {e}"

        if self.server._is_workout_redo_command(text):
            logger.debug("[Intent: WORKOUT_REDO_SET]")
            try:
                return asyncio.run(self.server._handle_workout_redo_set(text))
            except Exception as e:
                return f"Redo failed: {e}"

        if self.server._is_workout_skip_command(text):
            logger.debug("[Intent: WORKOUT_SKIP (set)]")
            # Stop any active exercise timer
            self.server.workout.exercise_timer_active = False
            try:
                return asyncio.run(self.server._handle_workout_skip())
            except Exception as e:
                return f"Skip failed: {e}"

        if "how long" in text.lower() or "time" in text.lower():
            # Report time remaining for timed exercises
            if self.server.workout.exercise_timer_active:
                remaining = self.server._get_workout_exercise_time_remaining()
                side_info = (
                    f" on {self.server.workout.exercise_current_side}"
                    if self.server.workout.exercise_current_side
                    else ""
                )
                return f"{remaining} seconds{side_info}."
            return "Set in progress. Say done when finished."

        # Different message for timed vs rep-based exercises
        if self.server.workout.exercise_timer_active:
            remaining = self.server._get_workout_exercise_time_remaining()
            return f"{remaining} seconds remaining."
        return "Set in progress. Say done when finished."

    def _handle_active_routine(self, text: str) -> IntentResult | None:
        """Handle all intents when an interactive routine is active.

        The routine state machine has multiple sub-states:
        - auto_advance_pending: Transitioning between exercises
        - paused: Routine paused
        - exercise_pending: Waiting for user to say "ready"
        - timer_active: Exercise timer running
        - exercise_complete: Timer just finished, auto-advance needed
        """
        response_text = ""

        # Check exercise timer (only if timer is active)
        timer_msg, exercise_done = None, False
        if self.server.routine.timer_active:
            timer_msg, exercise_done = self.server._check_routine_timer()

        # Global stop check (works in any routine state including auto-advance)
        if self.server._is_routine_stop_command(text):
            logger.debug("[Intent: ROUTINE_STOP]")
            try:
                response_text = asyncio.run(self.server._handle_routine_stop())
            except Exception as e:
                logger.debug(f"[ROUTINE_STOP ERROR: {e}]")
                response_text = f"Stop failed: {e}"

        # Auto-advance in progress (user can skip or wait)
        elif self.server.routine.auto_advance_pending:
            response_text = self._handle_routine_auto_advance(text)

        # Paused state
        elif self.server.routine.paused:
            response_text = self._handle_routine_paused(text)

        # Pending state - waiting for user to say ready/begin/go
        elif self.server.routine.exercise_pending:
            response_text = self._handle_routine_pending(text)

        # Timer active - exercise in progress
        elif self.server.routine.timer_active and not self.server.routine.exercise_complete:
            response_text = self._handle_routine_timer_active(text)

        # Exercise timer complete - auto advance
        elif self.server.routine.exercise_complete:
            # Advance to next exercise automatically
            logger.debug("[Intent: ROUTINE_AUTO_ADVANCE]")
            try:
                response_text = asyncio.run(self.server._advance_routine_exercise())
            except Exception as e:
                response_text = f"Advance failed: {e}"

        else:
            # Fallback - shouldn't reach here
            ex = self.server.routine.current_exercise
            ex_name = ex["name"] if ex else "exercise"
            response_text = f"Routine active on {ex_name}. Say ready to start, or skip."

        print(f"ATLAS: {response_text}")
        return IntentResult(
            response_text=response_text,
            action_type="routine_interactive",
            tier_override="ROUTINE_INTERACTIVE",
        )

    def _handle_routine_auto_advance(self, text: str) -> str:
        """Handle intents during routine auto-advance transition."""
        if self.server._is_routine_skip_command(text):
            logger.debug("[Intent: ROUTINE_SKIP (during auto-advance)]")
            # Cancel current auto-advance and skip to next exercise
            self.server.routine.auto_advance_pending = False
            self.server.routine.auto_advance_start = None
            self.server.routine.auto_advance_phase = None
            try:
                return asyncio.run(self.server._handle_routine_skip())
            except Exception as e:
                return f"Skip failed: {e}"

        if self.server._is_routine_ready_command(text):
            logger.debug("[Intent: ROUTINE_READY (during auto-advance) - start now]")
            # Skip remaining transition time and start immediately
            self.server.routine.auto_advance_pending = False
            self.server.routine.auto_advance_phase = None
            self.server._auto_start_routine_timer()
            ex = self.server.routine.current_exercise
            if ex:
                return f"Timer started. {ex.get('name', 'Exercise')}. Go."
            return "Starting now."

        # During auto-advance, acknowledge but let it continue
        phase = self.server.routine.auto_advance_phase
        if phase == "completed":
            return "Getting ready for next exercise."
        elif phase == "announcing":
            return "Positioning. Say ready to start now, or wait."
        return "Transitioning. Please wait or say skip."

    def _handle_routine_paused(self, text: str) -> str:
        """Handle intents while routine is paused."""
        if self.server._is_routine_resume_command(text) or self.server._is_routine_ready_command(text):
            # Both "resume" and "ready" unpause and restart the timer
            logger.debug("[Intent: ROUTINE_RESUME (via ready/resume)]")
            try:
                return asyncio.run(self.server._handle_routine_resume())
            except Exception as e:
                return f"Resume failed: {e}"

        if self.server._is_routine_skip_command(text):
            # Skip works during pause too
            logger.debug("[Intent: ROUTINE_SKIP (during pause)]")
            self.server.routine.paused = False
            try:
                return asyncio.run(self.server._handle_routine_skip())
            except Exception as e:
                return f"Skip failed: {e}"

        if self.server._is_routine_stop_command(text):
            # Stop works during pause too
            logger.debug("[Intent: ROUTINE_STOP (during pause)]")
            self.server.routine.paused = False
            try:
                return asyncio.run(self.server._handle_routine_stop())
            except Exception as e:
                return f"Stop failed: {e}"

        if self.server._is_routine_form_request(text):
            logger.debug("[Intent: ROUTINE_FORM]")
            try:
                return asyncio.run(self.server._handle_routine_form_request(text))
            except Exception as e:
                return f"Form help failed: {e}"

        ex = self.server.routine.current_exercise
        ex_name = ex["name"] if ex else "exercise"
        return f"Paused on {ex_name}. Say resume, or ask about form."

    def _handle_routine_pending(self, text: str) -> str:
        """Handle intents while waiting for user to be ready."""
        ex = self.server.routine.current_exercise
        ex_name = ex["name"] if ex else "exercise"

        # Check if this exercise has no timer (like Morning Sunlight)
        has_timer = ex and (ex.get("duration_seconds") or ex.get("reps"))

        # Complete command - finish routine gracefully
        if self.server._is_routine_complete_command(text):
            logger.debug("[Intent: ROUTINE_COMPLETE]")
            try:
                return asyncio.run(self.server._handle_routine_complete())
            except Exception as e:
                return f"Complete failed: {e}"

        if self.server._is_routine_ready_command(text):
            if has_timer:
                logger.debug("[Intent: ROUTINE_READY]")
                try:
                    return asyncio.run(self.server._handle_routine_ready())
                except Exception as e:
                    return f"Ready failed: {e}"
            else:
                # No timer exercise - check if last exercise
                is_last = self.server._is_routine_last_exercise()
                if is_last:
                    logger.debug("[Intent: ROUTINE_READY (last, no timer) -> COMPLETE]")
                    try:
                        return asyncio.run(self.server._handle_routine_complete())
                    except Exception as e:
                        return f"Complete failed: {e}"
                else:
                    logger.debug("[Intent: ROUTINE_READY (no timer) -> SKIP]")
                    try:
                        return asyncio.run(self.server._handle_routine_skip())
                    except Exception as e:
                        return f"Skip failed: {e}"

        if self.server._is_routine_stop_command(text):
            # Redundant stop check for pending state (safety net)
            logger.debug("[Intent: ROUTINE_STOP (pending - safety net)]")
            try:
                return asyncio.run(self.server._handle_routine_stop())
            except Exception as e:
                return f"Stop failed: {e}"

        if self.server._is_routine_skip_command(text):
            logger.debug("[Intent: ROUTINE_SKIP (pending)]")
            try:
                return asyncio.run(self.server._handle_routine_skip())
            except Exception as e:
                return f"Skip failed: {e}"

        if self.server._is_routine_form_request(text):
            logger.debug("[Intent: ROUTINE_FORM (pending)]")
            try:
                response = asyncio.run(self.server._handle_routine_form_request(text))
                if has_timer:
                    response += " Say ready to start timer."
                else:
                    response += " Say finished when done."
                return response
            except Exception as e:
                return f"Form help failed: {e}"

        if has_timer:
            return f"Waiting. {ex_name}. Say ready, begin, or go to start timer."
        return f"{ex_name}. No timer needed. Say finished when done, or skip."

    def _handle_routine_timer_active(self, text: str) -> str:
        """Handle intents while exercise timer is running."""
        if self.server._is_routine_pause_command(text):
            logger.debug("[Intent: ROUTINE_PAUSE]")
            try:
                return asyncio.run(self.server._handle_routine_pause())
            except Exception as e:
                return f"Pause failed: {e}"

        if self.server._is_routine_stop_command(text):
            # Redundant stop check for timer active state (safety net)
            logger.debug("[Intent: ROUTINE_STOP (timer active - safety net)]")
            try:
                return asyncio.run(self.server._handle_routine_stop())
            except Exception as e:
                return f"Stop failed: {e}"

        if self.server._is_routine_skip_command(text):
            logger.debug("[Intent: ROUTINE_SKIP]")
            try:
                return asyncio.run(self.server._handle_routine_skip())
            except Exception as e:
                return f"Skip failed: {e}"

        if self.server._is_routine_form_request(text):
            # Pause and provide form help
            logger.debug("[Intent: ROUTINE_FORM (auto-pause)]")
            try:
                asyncio.run(self.server._handle_routine_pause())
                return asyncio.run(self.server._handle_routine_form_request(text))
            except Exception as e:
                return f"Form help failed: {e}"

        if "how long" in text.lower() or "time" in text.lower():
            remaining = self.server._get_routine_time_remaining()
            return f"{remaining} seconds remaining."

        # During exercise, acknowledge
        remaining = self.server._get_routine_time_remaining()
        ex = self.server.routine.current_exercise
        ex_name = ex["name"] if ex else "exercise"
        return f"{ex_name}. {remaining} seconds. Say pause for form help."
