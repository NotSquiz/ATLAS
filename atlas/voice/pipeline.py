"""
ATLAS Voice Pipeline

Push-to-talk conversation loop integrating:
- STT (Moonshine on CPU)
- LLM (Qwen2.5-3B-Instruct via Ollama)
- TTS (Kokoro on GPU)
- VAD (Silero for speech end detection)

Target: < 2 second end-to-end latency (achievable with Qwen2.5's no-thinking mode)
"""

import asyncio
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable, Optional

logger = logging.getLogger(__name__)

import numpy as np
import sounddevice as sd

from atlas.voice.stt import MoonshineSTT, FasterWhisperSTT, get_stt
from atlas.voice.tts import KokoroTTS, get_tts
from atlas.voice.vad import StreamingVAD, VADConfig, get_streaming_vad
from atlas.llm.local import OllamaClient, get_client
from atlas.llm.router import ATLASRouter, get_router, Tier
from atlas.orchestrator.classifier import ThoughtClassifier, Category, ProjectRecord, RecipeRecord

# Filler phrases for cloud latency masking (Lethal Gentleman persona)
FILLER_PHRASES = [
    "Let me see.",
    "One moment.",
    "Give me a moment.",
]

# Command words for interrupt detection
INTERRUPT_COMMANDS = ["stop", "wait", "quiet", "shush", "enough", "okay"]

# Capture intent triggers - phrases that indicate user wants to save something
CAPTURE_TRIGGERS = [
    "remember", "save", "note", "capture", "record", "store",
    "don't forget", "log this", "write down", "make a note",
    "add to memory", "remember this", "save this", "note this",
]

# Meal logging triggers - phrases that indicate meal/food logging
MEAL_TRIGGERS = [
    "log meal", "log food", "logged meal", "logged food",
    "had for breakfast", "had for lunch", "had for dinner", "had for snack",
    "ate for breakfast", "ate for lunch", "ate for dinner",
    "eating", "just ate", "just had", "i ate", "i had",
    "track meal", "track food", "food log", "meal log",
]

# Health/fitness intent triggers - patterns for voice commands
HEALTH_TRIGGERS = {
    # Status queries (0 tokens - read from cache)
    r"(what'?s|what is|show|give me|tell me) (my )?(status|morning status)": "get_status",
    r"(how am i|how'm i) (doing|today)": "get_status",
    r"my (morning )?status": "get_status",
    r"traffic light": "get_status",

    # Routine control
    r"start (my |the )?(morning )?(routine|protocol)": "start_routine",
    r"begin (my |the )?(morning )?(routine|protocol)": "start_routine",
    r"(quick|short) routine": "start_quick_routine",
    r"(just |only )?(shoulders?|shoulder rehab)": "start_routine_shoulders",

    # Workout queries
    r"(what'?s|what is|show|my|today'?s) workout": "get_workout",
    r"what (should i|am i) (do|doing) today": "get_workout",
    r"start (my |the |today'?s )?workout": "start_workout",
    r"begin (my |the |today'?s )?workout": "start_workout",

    # Workout logging
    r"log workout": "log_workout",
    r"logged? (my )?(workout|training|session)": "log_workout",
    r"(finish|done|complete)d? (my |the |today'?s )?(workout|training)": "log_workout",
}

# Workout logging triggers - for natural language workout logging
WORKOUT_LOG_TRIGGERS = [
    "log workout", "logged workout", "finish workout",
    "done with workout", "workout complete", "completed workout",
    "finished my workout", "log my workout", "log training",
]


@dataclass
class PipelineMetrics:
    """Timing metrics for voice pipeline."""
    request_id: str
    vad_end_time: float = 0.0
    stt_start_time: float = 0.0
    stt_end_time: float = 0.0
    llm_first_token_time: float = 0.0
    tts_first_audio_time: float = 0.0
    pipeline_end_time: float = 0.0

    @property
    def stt_duration_ms(self) -> float:
        """STT processing time in ms."""
        return (self.stt_end_time - self.stt_start_time) * 1000

    @property
    def time_to_first_token_ms(self) -> float:
        """Time from speech end to LLM first token."""
        return (self.llm_first_token_time - self.vad_end_time) * 1000

    @property
    def time_to_first_audio_ms(self) -> float:
        """Time from speech end to first TTS audio."""
        return (self.tts_first_audio_time - self.vad_end_time) * 1000

    @property
    def total_latency_ms(self) -> float:
        """Total pipeline latency in ms."""
        return (self.pipeline_end_time - self.vad_end_time) * 1000


@dataclass
class VoicePipelineConfig:
    """Configuration for voice pipeline."""

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 64  # 64ms chunks for VAD (Silero needs >= 32ms / 512 samples)

    # VAD settings (R11 optimized)
    vad_threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 400
    speech_pad_ms: int = 100

    # STT backend
    stt_backend: str = "moonshine"  # or "faster-whisper"

    # TTS settings
    tts_voice: str = "bm_lewis"  # British male per persona

    # LLM settings
    llm_model: str = "atlas-local"
    llm_max_tokens: int = 256  # Qwen2.5 has no thinking mode - all tokens for content
    llm_temperature: float = 0.7

    # Router settings
    use_router: bool = True  # Use hybrid router instead of local-only
    enable_filler_phrases: bool = True  # Speak filler when routing to cloud

    # Hot window settings
    hot_window_duration_s: float = 6.0  # Stay listening after TTS without wake word

    # System prompt for ATLAS persona (The Lethal Gentleman - R21)
    system_prompt: str = """You are ATLAS—a mentor who has seen much, speaks economically, means what you say, and trusts the user to handle truth. Your voice carries quiet authority from proven competence held in check.

Core principles:
- Speak with economy. Lead with shorter sentences for impact.
- Use precise Anglo-Saxon words over ornate Latinate alternatives.
- No hedging qualifiers: never "just", "maybe", "perhaps", "sort of".
- Understated confidence—don't announce your capabilities.
- Warm through action, not sentiment. Practical concern, not effusion.
- Challenge the work, not the person. Support effort, not ego.

Your responses will be spoken aloud. Keep them brief—1-3 sentences for simple queries. When something matters, say so directly."""


class VoicePipeline:
    """
    Push-to-talk voice conversation pipeline.

    Usage:
        pipeline = VoicePipeline()
        await pipeline.start()

        # Or run a single turn
        response = await pipeline.process_turn()
    """

    def __init__(self, config: Optional[VoicePipelineConfig] = None):
        """Initialize voice pipeline."""
        self.config = config or VoicePipelineConfig()

        # Initialize components (lazy-loaded)
        self._stt = None
        self._tts = None
        self._vad = None
        self._llm = None
        self._router = None

        # Audio state
        self._in_hot_window = False
        self._hot_window_end_time = 0.0
        self._audio_buffer: list[np.ndarray] = []
        self._is_recording = False
        self._stream = None

        # Metrics
        self._last_metrics: Optional[PipelineMetrics] = None

    @property
    def stt(self):
        """Get STT instance (lazy-loaded)."""
        if self._stt is None:
            self._stt = get_stt(self.config.stt_backend)
        return self._stt

    @property
    def tts(self):
        """Get TTS instance (lazy-loaded)."""
        if self._tts is None:
            self._tts = get_tts(self.config.tts_voice)
        return self._tts

    @property
    def vad(self):
        """Get VAD instance (lazy-loaded)."""
        if self._vad is None:
            vad_config = VADConfig(
                threshold=self.config.vad_threshold,
                min_speech_duration_ms=self.config.min_speech_duration_ms,
                min_silence_duration_ms=self.config.min_silence_duration_ms,
                speech_pad_ms=self.config.speech_pad_ms,
                sample_rate=self.config.sample_rate,
            )
            self._vad = get_streaming_vad(vad_config)
        return self._vad

    @property
    def llm(self):
        """Get LLM client (lazy-loaded)."""
        if self._llm is None:
            self._llm = get_client(model=self.config.llm_model)
        return self._llm

    @property
    def router(self):
        """Get hybrid router (lazy-loaded)."""
        if self._router is None:
            self._router = get_router(system_prompt=self.config.system_prompt)
        return self._router

    def _get_filler_phrase(self) -> str:
        """Get a random filler phrase for latency masking."""
        import random
        return random.choice(FILLER_PHRASES)

    def _is_interrupt_command(self, text: str) -> bool:
        """Check if text contains an interrupt command."""
        from difflib import SequenceMatcher
        text_lower = text.lower().strip()
        for cmd in INTERRUPT_COMMANDS:
            # Exact match
            if cmd in text_lower:
                return True
            # Fuzzy match for short utterances
            if len(text_lower) <= 10:
                ratio = SequenceMatcher(None, cmd, text_lower).ratio()
                if ratio > 0.7:
                    return True
        return False

    def _is_capture_intent(self, text: str) -> bool:
        """
        Check if text indicates user wants to capture/save something.

        Triggers on phrases like:
        - "Remember that Sarah called"
        - "Save this: meeting tomorrow at 3pm"
        - "Note: need to buy groceries"
        - "Don't forget the deadline is Friday"

        Uses word boundary matching to avoid false positives like
        "I can't remember" or "notable achievement".
        """
        text_lower = text.lower().strip()

        # Check if trigger appears at START of text (most reliable)
        for trigger in CAPTURE_TRIGGERS:
            if text_lower.startswith(trigger):
                return True

        # Check for word boundary match (e.g., "please remember" but not "I can't remember")
        # Only match if trigger is preceded by start or a command word
        import re
        command_prefixes = r"^(?:please\s+|hey\s+|atlas\s+|okay\s+)?"
        for trigger in CAPTURE_TRIGGERS:
            # Match trigger as whole word at start (with optional prefix)
            pattern = command_prefixes + r"\b" + re.escape(trigger) + r"\b"
            if re.match(pattern, text_lower):
                return True

        return False

    def _extract_capture_content(self, text: str) -> str:
        """
        Extract the content to capture from user speech.

        Removes trigger phrases to get the actual content.
        e.g., "Remember that Sarah called" → "Sarah called"
        """
        text_lower = text.lower()
        content = text

        # Remove trigger phrases from start
        for trigger in CAPTURE_TRIGGERS:
            if text_lower.startswith(trigger):
                content = text[len(trigger):].lstrip(" :,-")
                break
            # Handle "remember that", "note that" patterns
            if text_lower.startswith(trigger + " that"):
                content = text[len(trigger) + 5:].lstrip(" :,-")
                break
            if text_lower.startswith(trigger + " this"):
                content = text[len(trigger) + 5:].lstrip(" :,-")
                break

        return content.strip() or text

    async def _handle_capture(self, text: str) -> str:
        """
        Handle a capture intent - classify and store the thought.

        Args:
            text: User's spoken text with capture intent

        Returns:
            Confirmation message to speak back
        """
        # Extract the actual content to save
        content = self._extract_capture_content(text)

        # Lazy-load classifier
        if not hasattr(self, '_classifier'):
            self._classifier = ThoughtClassifier()

        # Classify and store
        result = self._classifier.classify_and_store(content)

        # Generate voice-friendly confirmation with hierarchy for projects
        if result.category == Category.PROJECTS and isinstance(result.record, ProjectRecord):
            parent = result.record.parent_project
            sub = result.record.sub_area
            if parent and sub:
                # e.g., "Baby Brains website project"
                category_name = f"{parent.replace('-', ' ').title()} {sub} project"
            elif parent:
                category_name = f"{parent.replace('-', ' ').title()} project"
            else:
                category_name = "a project"
        elif result.category == Category.RECIPES:
            category_name = "a recipe"
        else:
            category_names = {
                Category.PEOPLE: "a person note",
                Category.IDEAS: "an idea",
                Category.ADMIN: "an admin task",
                Category.UNKNOWN: "a note",
            }
            category_name = category_names.get(result.category, "a note")

        if result.memory_id:
            return f"Captured as {category_name}. Stored."
        else:
            return f"Noted as {category_name}, but confidence too low to store automatically."

    def _is_meal_log(self, text: str) -> bool:
        """
        Check if text indicates user wants to log a meal.

        Triggers on phrases like:
        - "Log meal: 100g chicken, cup of rice"
        - "Had for breakfast: oatmeal with banana"
        - "Just ate 5 crackers with cheese"

        Uses start-of-text matching to avoid false positives like
        "I had a meeting" or "logging into my account".
        """
        text_lower = text.lower().strip()

        # Check if trigger appears at START of text (most reliable)
        for trigger in MEAL_TRIGGERS:
            if text_lower.startswith(trigger):
                return True

        # Check for word boundary match with optional command prefix
        import re
        command_prefixes = r"^(?:please\s+|hey\s+|atlas\s+|okay\s+)?"
        for trigger in MEAL_TRIGGERS:
            # Match trigger as whole phrase at start (with optional prefix)
            pattern = command_prefixes + re.escape(trigger) + r"\b"
            if re.match(pattern, text_lower):
                return True

        return False

    def _extract_meal_content(self, text: str) -> str:
        """
        Extract the food items from meal log text.

        Removes trigger phrases to get the actual food list.
        e.g., "Log meal: 100g chicken, rice" → "100g chicken, rice"
        """
        text_lower = text.lower()
        content = text

        # Remove trigger phrases from start
        for trigger in MEAL_TRIGGERS:
            if text_lower.startswith(trigger):
                content = text[len(trigger):].lstrip(" :,-")
                break

        return content.strip() or text

    async def _handle_meal_log(self, text: str) -> str:
        """
        Handle a meal logging request - parse and calculate nutrition.

        Args:
            text: User's spoken text with meal items

        Returns:
            Confirmation message with nutrition summary
        """
        # Extract the food content
        content = self._extract_meal_content(text)

        try:
            from atlas.nutrition import NutritionService

            # Lazy-load nutrition service
            if not hasattr(self, '_nutrition_service'):
                self._nutrition_service = NutritionService()

            # Log the meal
            record = await self._nutrition_service.log_meal(content)

            if record.items:
                return record.summary()
            else:
                return "Couldn't parse the meal. Try listing items like: 100g chicken, cup of rice."

        except ImportError:
            # Fallback if nutrition module not available
            return "Nutrition tracking not available. Logged as health note instead."
        except Exception as e:
            return f"Failed to log meal. Error: {str(e)[:50]}"

    def _detect_health_intent(self, text: str) -> Optional[str]:
        """
        Detect health/fitness intent from text.

        Returns intent name if matched, None otherwise.
        """
        import re
        text_lower = text.lower().strip()

        for pattern, intent in HEALTH_TRIGGERS.items():
            if re.search(pattern, text_lower):
                return intent

        return None

    def _is_workout_log(self, text: str) -> bool:
        """Check if text indicates workout logging."""
        text_lower = text.lower().strip()
        for trigger in WORKOUT_LOG_TRIGGERS:
            if trigger in text_lower:
                return True
        return False

    async def _handle_health_intent(self, intent: str, text: str) -> str:
        """
        Handle a health/fitness intent.

        Args:
            intent: The detected intent name
            text: Original user text

        Returns:
            Response to speak
        """
        try:
            if intent == "get_status":
                return await self._get_morning_status()

            elif intent == "get_workout":
                return await self._get_todays_workout()

            elif intent == "start_routine":
                return await self._start_morning_routine()

            elif intent == "start_quick_routine":
                return await self._start_morning_routine(sections=["Shoulder Rehab"])

            elif intent == "start_routine_shoulders":
                return await self._start_morning_routine(sections=["Shoulder Rehab"])

            elif intent == "start_workout":
                return await self._start_workout()

            elif intent == "log_workout":
                return await self._handle_workout_log(text)

            else:
                return f"Health intent '{intent}' not implemented yet."

        except Exception as e:
            logger.error(f"Health intent handler error: {e}")
            return "Sorry, there was an error processing that request."

    async def _get_morning_status(self) -> str:
        """Get morning status from cache (0 tokens)."""
        try:
            from atlas.health.morning_sync import get_morning_status, format_status_voice
            status = get_morning_status()
            return format_status_voice(status)
        except ImportError:
            return "Morning sync module not available."
        except Exception as e:
            logger.error(f"Failed to get morning status: {e}")
            return "Could not retrieve status. Try running morning sync first."

    async def _get_todays_workout(self) -> str:
        """Get today's workout description (0 tokens)."""
        try:
            from atlas.health.workout_runner import get_todays_protocol, format_protocol_for_display
            from atlas.health.morning_sync import get_morning_status

            # Get traffic light status for proper workout selection
            status = get_morning_status()
            traffic_light_str = status.get("traffic_light", "GREEN")

            from atlas.health.router import TrafficLightStatus
            traffic_light = TrafficLightStatus(traffic_light_str)

            protocol = get_todays_protocol(traffic_light)
            if not protocol:
                return "No workout scheduled for today. Rest day."

            # Format for voice (brief version)
            if protocol.type == "recovery":
                return f"{protocol.name}. Rest and recover. The gains happen in recovery."

            exercises = [ex.name for ex in protocol.exercises[:3]]
            exercise_list = ", ".join(exercises)
            if len(protocol.exercises) > 3:
                exercise_list += f", and {len(protocol.exercises) - 3} more"

            return f"{protocol.name}. {protocol.duration_minutes} minutes. {exercise_list}."

        except Exception as e:
            logger.error(f"Failed to get workout: {e}")
            return "Could not retrieve today's workout."

    async def _start_morning_routine(self, sections: Optional[list] = None) -> str:
        """Start the morning routine with timers."""
        try:
            from atlas.health.routine_runner import RoutineRunner

            runner = RoutineRunner()

            # Announce start
            if sections:
                start_msg = f"Starting focused routine. {', '.join(sections)}."
            else:
                start_msg = "Starting morning protocol. 18 minutes."

            await self._speak(start_msg)

            # Create speak function for runner
            async def speak_func(text: str):
                await self._speak(text)

            def play_chime():
                try:
                    from atlas.voice.audio_utils import play_chime as pc
                    pc("single", blocking=True)
                except ImportError:
                    pass

            # Run routine
            completed = await runner.run(
                speak_func=speak_func,
                play_chime=play_chime,
                sections=sections,
            )

            if completed:
                return "Routine complete. Well done."
            else:
                return "Routine stopped."

        except Exception as e:
            logger.error(f"Failed to start routine: {e}")
            return "Could not start routine."

    async def _start_workout(self) -> str:
        """Start today's workout with timers."""
        try:
            from atlas.health.workout_runner import WorkoutRunner, get_todays_protocol
            from atlas.health.morning_sync import get_morning_status
            from atlas.health.router import TrafficLightStatus

            # Get traffic light for workout selection
            status = get_morning_status()
            traffic_light_str = status.get("traffic_light", "GREEN")
            traffic_light = TrafficLightStatus(traffic_light_str)

            # Check for RED day override
            if traffic_light == TrafficLightStatus.RED:
                return "RED day. Recovery protocol only. Walk and NSDR. No intense training."

            protocol = get_todays_protocol(traffic_light)
            if not protocol:
                return "No workout scheduled for today."

            runner = WorkoutRunner(
                intensity_modifier=1.15 if traffic_light == TrafficLightStatus.YELLOW else 1.0
            )

            async def speak_func(text: str):
                await self._speak(text)

            def play_chime():
                try:
                    from atlas.voice.audio_utils import play_chime as pc
                    pc("single", blocking=True)
                except ImportError:
                    pass

            completed = await runner.run_protocol(
                protocol,
                speak_func=speak_func,
                play_chime=play_chime,
            )

            if completed:
                summary = runner.get_completed_summary()
                return f"Workout complete. {summary}. Log your results when ready."
            else:
                return "Workout stopped."

        except Exception as e:
            logger.error(f"Failed to start workout: {e}")
            return "Could not start workout."

    async def _handle_workout_log(self, text: str) -> str:
        """
        Handle workout logging via natural language.

        Uses Haiku to parse exercises, sets, reps, weights from speech.
        """
        try:
            # Extract workout details after trigger phrase
            import re
            for trigger in WORKOUT_LOG_TRIGGERS:
                if trigger in text.lower():
                    # Get text after trigger
                    idx = text.lower().find(trigger)
                    workout_text = text[idx + len(trigger):].strip(" .,:")
                    if workout_text:
                        text = workout_text
                    break

            # Use Haiku to parse workout details
            parse_prompt = f"""Extract workout details from this text. Return JSON only.
Text: "{text}"

Return format:
{{"exercises": [{{"name": "exercise name", "sets": 3, "reps": 10, "weight_kg": 20}}], "notes": "optional notes", "rpe": 6}}

If weight is mentioned in pounds/lbs, convert to kg. If no weight mentioned, omit weight_kg.
Return only valid JSON, no explanation."""

            # Route to Haiku for parsing
            if self.config.use_router:
                response = ""
                async for token in self.router.route_and_stream(
                    parse_prompt,
                    temperature=0.1,
                    max_tokens=256,
                ):
                    response += token
            else:
                response = text  # Fallback - just echo back

            # Parse JSON response
            import json
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {"exercises": [], "notes": text}
            except json.JSONDecodeError:
                data = {"exercises": [], "notes": text}

            # Format confirmation (Lethal Gentleman)
            exercises = data.get("exercises", [])
            if exercises:
                parts = []
                for ex in exercises:
                    if ex.get("weight_kg"):
                        parts.append(f"{ex['name']} {ex.get('sets', 3)}x{ex.get('reps', 10)} at {ex['weight_kg']}kg")
                    else:
                        parts.append(f"{ex['name']} {ex.get('sets', 3)}x{ex.get('reps', 10)}")

                summary = ". ".join(parts)
                rpe = data.get("rpe", "")
                notes = data.get("notes", "")

                response = f"Logged. {summary}."
                if notes and notes != text:
                    response += f" {notes}."
                response += " Solid work."

                return response
            else:
                return f"Logged workout. {text[:50]}. Solid work."

        except Exception as e:
            logger.error(f"Failed to log workout: {e}")
            return "Workout noted. Could not parse full details."

    async def record_until_silence(self) -> np.ndarray:
        """
        Record audio until speech ends (VAD detects silence).

        Returns:
            Audio data as numpy array (16kHz mono float32)
        """
        self._audio_buffer = []
        self._is_recording = True
        self.vad.reset()

        chunk_samples = int(
            self.config.sample_rate * self.config.chunk_duration_ms / 1000
        )

        speech_audio = None

        def audio_callback(indata, frames, time_info, status):
            """Callback for audio input stream."""
            if status:
                print(f"Audio status: {status}", file=sys.stderr)

            # Convert to mono float32
            audio_chunk = indata[:, 0].copy().astype(np.float32)

            # Process with VAD
            result = self.vad.process_chunk(audio_chunk)

            if result.speech_started:
                print("Speech detected...", file=sys.stderr)

            if result.speech_ended:
                nonlocal speech_audio
                speech_audio = result.get_speech_audio()
                raise sd.CallbackStop()

            # Buffer audio while recording
            if self.vad.is_speaking():
                self._audio_buffer.append(audio_chunk)

        # Open input stream
        with sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype=np.float32,
            blocksize=chunk_samples,
            callback=audio_callback,
        ):
            print("Listening...", file=sys.stderr)
            while speech_audio is None:
                await asyncio.sleep(0.01)

        return speech_audio

    async def process_turn(self) -> str:
        """
        Process a single conversation turn.

        Records audio, transcribes, generates response, and speaks it.

        Returns:
            LLM response text
        """
        request_id = str(time.time())
        metrics = PipelineMetrics(request_id=request_id)

        # 1. Record audio until speech ends
        print("\n[Press Enter to speak, Ctrl+C to quit]")
        input()  # Wait for user to press Enter

        print("Recording... (speak now)")
        audio = await self.record_until_silence()
        metrics.vad_end_time = time.perf_counter()
        print(f"Captured {len(audio) / self.config.sample_rate:.1f}s of audio")

        # 2. Transcribe (STT on CPU)
        metrics.stt_start_time = time.perf_counter()
        transcription = self.stt.transcribe(audio, self.config.sample_rate)
        metrics.stt_end_time = time.perf_counter()

        user_text = transcription.text
        print(f"You: {user_text}")
        print(f"  [STT: {transcription.duration_ms:.0f}ms]")

        if not user_text.strip():
            print("No speech detected.")
            return ""

        # 2.5a. Check for health/fitness intent FIRST (0 tokens for cached data)
        health_intent = self._detect_health_intent(user_text)
        if health_intent:
            print(f"  [Health intent: {health_intent}]")
            response_text = await self._handle_health_intent(health_intent, user_text)
            print(f"ATLAS: {response_text}")
            await self._speak(response_text)

            metrics.pipeline_end_time = time.perf_counter()
            self._last_metrics = metrics
            print(f"  [Health: {(metrics.pipeline_end_time - metrics.vad_end_time) * 1000:.0f}ms]")

            # Stay in hot window for follow-ups
            self._in_hot_window = True
            self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s
            return response_text

        # 2.5b. Check for meal log intent
        if self._is_meal_log(user_text):
            print("  [Meal log detected]")
            response_text = await self._handle_meal_log(user_text)
            print(f"ATLAS: {response_text}")
            await self._speak(response_text)

            metrics.pipeline_end_time = time.perf_counter()
            self._last_metrics = metrics
            print(f"  [Meal log: {(metrics.pipeline_end_time - metrics.vad_end_time) * 1000:.0f}ms]")
            return response_text

        # 2.5d. Check for capture intent BEFORE routing to LLM
        if self._is_capture_intent(user_text):
            print("  [Capture intent detected]")
            response_text = await self._handle_capture(user_text)
            print(f"ATLAS: {response_text}")
            await self._speak(response_text)

            metrics.pipeline_end_time = time.perf_counter()
            self._last_metrics = metrics
            print(f"  [Capture: {(metrics.pipeline_end_time - metrics.vad_end_time) * 1000:.0f}ms]")

            # Enter hot window for follow-up captures
            self._in_hot_window = True
            self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s
            return response_text

        # 3. Route query and generate response
        response_text = ""
        first_token = True
        sentence_buffer = ""
        was_interrupted = False

        # Classify the query to decide routing
        if self.config.use_router:
            decision = self.router.classify(user_text)
            tier = decision.tier
            print(f"  [Route: {tier.value}, conf: {decision.confidence:.2f}]")

            # Speak filler phrase if routing to cloud (masks latency)
            if self.config.enable_filler_phrases and tier != Tier.LOCAL:
                filler = self._get_filler_phrase()
                print(f"ATLAS: {filler}")
                await self._speak(filler)
                metrics.tts_first_audio_time = time.perf_counter()

        print("ATLAS: ", end="", flush=True)

        # Stream from router or direct LLM
        if self.config.use_router:
            stream = self.router.route_and_stream(
                user_text,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
        else:
            stream = self.llm.stream(
                user_text,
                system=self.config.system_prompt,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )

        async for token in stream:
            if first_token:
                metrics.llm_first_token_time = time.perf_counter()
                first_token = False

            response_text += token
            sentence_buffer += token
            print(token, end="", flush=True)

            # 4. Speak complete sentences immediately (streaming TTS)
            if sentence_buffer.rstrip().endswith(('.', '!', '?', ':')):
                if metrics.tts_first_audio_time == 0:
                    metrics.tts_first_audio_time = time.perf_counter()

                # Synthesize and play sentence (may be interrupted)
                was_interrupted = await self._speak_interruptible(sentence_buffer.strip())
                sentence_buffer = ""

                if was_interrupted:
                    print(" [interrupted]", end="")
                    break

        # Speak any remaining text (if not interrupted)
        if sentence_buffer.strip() and not was_interrupted:
            if metrics.tts_first_audio_time == 0:
                metrics.tts_first_audio_time = time.perf_counter()
            await self._speak_interruptible(sentence_buffer.strip())

        print()  # New line after response
        metrics.pipeline_end_time = time.perf_counter()

        # Log metrics
        self._last_metrics = metrics
        print(f"  [TTFA: {metrics.time_to_first_audio_ms:.0f}ms, "
              f"Total: {metrics.total_latency_ms:.0f}ms]")

        # Enter hot window mode (stay listening for follow-ups)
        self._in_hot_window = True
        self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s

        return response_text

    async def _wait_for_speech_or_timeout(self) -> Optional[np.ndarray]:
        """
        Wait for speech during hot window, or timeout.

        Returns:
            Audio data if speech detected, None if timeout
        """
        self._audio_buffer = []
        self.vad.reset()

        chunk_samples = int(
            self.config.sample_rate * self.config.chunk_duration_ms / 1000
        )

        speech_audio = None
        timed_out = False

        def audio_callback(indata, frames, time_info, status):
            nonlocal speech_audio, timed_out

            if time.perf_counter() > self._hot_window_end_time:
                timed_out = True
                raise sd.CallbackStop()

            audio_chunk = indata[:, 0].copy().astype(np.float32)
            result = self.vad.process_chunk(audio_chunk)

            if result.speech_started:
                print("Speech detected...", file=sys.stderr)

            if result.speech_ended:
                speech_audio = result.get_speech_audio()
                raise sd.CallbackStop()

            if self.vad.is_speaking():
                self._audio_buffer.append(audio_chunk)

        try:
            with sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=np.float32,
                blocksize=chunk_samples,
                callback=audio_callback,
            ):
                while speech_audio is None and not timed_out:
                    await asyncio.sleep(0.01)

        except sd.CallbackStop:
            pass

        return speech_audio

    async def _speak(self, text: str) -> None:
        """Synthesize and play text (blocking, no interrupt detection)."""
        if not text:
            return

        result = self.tts.synthesize(text)

        # Play audio
        sd.play(result.audio, result.sample_rate)
        sd.wait()

    async def _speak_interruptible(self, text: str) -> bool:
        """
        Synthesize and play text with interrupt command detection.

        Monitors microphone during playback for "stop", "wait", "quiet" commands.

        Args:
            text: Text to speak

        Returns:
            True if interrupted, False if completed normally
        """
        if not text:
            return False

        result = self.tts.synthesize(text)

        # Calculate audio duration
        audio_duration_s = len(result.audio) / result.sample_rate

        # Start playback
        sd.play(result.audio, result.sample_rate)

        # Monitor for interrupt commands during playback
        chunk_samples = int(self.config.sample_rate * 0.1)  # 100ms chunks
        interrupt_detected = False
        interrupt_buffer = []

        def audio_callback(indata, frames, time_info, status):
            nonlocal interrupt_detected, interrupt_buffer
            if status:
                pass  # Ignore status during interrupt monitoring

            # Accumulate audio for potential STT
            audio_chunk = indata[:, 0].copy().astype(np.float32)

            # Quick VAD check - is there speech?
            self.vad.reset()
            vad_result = self.vad.process_chunk(audio_chunk)

            if vad_result.speech_started or self.vad.is_speaking():
                interrupt_buffer.append(audio_chunk)

                # If we have enough audio, try to transcribe
                if len(interrupt_buffer) >= 3:  # ~300ms of audio
                    combined = np.concatenate(interrupt_buffer)

                    # Quick transcription check
                    try:
                        transcription = self.stt.transcribe(combined, self.config.sample_rate)
                        if self._is_interrupt_command(transcription.text):
                            interrupt_detected = True
                            sd.stop()  # Stop playback immediately
                            raise sd.CallbackStop()
                    except sd.CallbackStop:
                        raise  # Re-raise to stop playback
                    except Exception as e:
                        # Log but don't fail - interrupt check is best-effort
                        logger.debug(f"Interrupt check transcription failed: {e}")

                    # Reset buffer but keep last chunk for overlap
                    interrupt_buffer = interrupt_buffer[-1:]

        try:
            # Open input stream for interrupt monitoring
            with sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=np.float32,
                blocksize=chunk_samples,
                callback=audio_callback,
            ):
                # Wait for playback to complete or interrupt
                start_time = time.perf_counter()
                while time.perf_counter() - start_time < audio_duration_s:
                    if interrupt_detected:
                        break
                    await asyncio.sleep(0.05)

        except sd.CallbackStop:
            pass  # Expected when interrupted

        # Make sure playback is stopped
        sd.stop()

        return interrupt_detected

    async def start(self) -> None:
        """
        Start the voice pipeline conversation loop.

        Press Enter to speak, Ctrl+C to quit.
        Supports hot window mode - after ATLAS speaks, you can respond
        without pressing Enter for 6 seconds.
        """
        print("=" * 50)
        print("ATLAS Voice Pipeline")
        print("=" * 50)
        print(f"STT: {self.config.stt_backend}")
        print(f"TTS: Kokoro ({self.config.tts_voice})")
        print(f"LLM: {self.config.llm_model}")
        if self.config.use_router:
            print("Router: Enabled (LOCAL → HAIKU → AGENT_SDK)")
        print(f"Hot Window: {self.config.hot_window_duration_s}s")
        print("=" * 50)

        # Check components
        if not self.stt.is_available():
            print(f"Warning: STT backend '{self.config.stt_backend}' not available")

        if not self.tts.is_available():
            print("Warning: TTS (Kokoro) not available")

        if not self.llm.is_available():
            print("Warning: LLM (Ollama) not available")

        # Conversation loop with hot window support
        try:
            while True:
                if self._in_hot_window and time.perf_counter() < self._hot_window_end_time:
                    # Hot window active - listen without Enter
                    remaining = self._hot_window_end_time - time.perf_counter()
                    print(f"\n[Listening for {remaining:.1f}s... or press Enter]")

                    # Race: wait for speech OR Enter key OR timeout
                    audio = await self._wait_for_speech_or_timeout()

                    if audio is not None:
                        # Speech detected in hot window - process it
                        await self._process_audio(audio)
                    else:
                        # Hot window expired
                        self._in_hot_window = False
                        print("[Hot window expired]")
                else:
                    # Normal mode - wait for Enter
                    self._in_hot_window = False
                    await self.process_turn()

        except KeyboardInterrupt:
            print("\n\nGoodbye, sir.")

    async def _process_audio(self, audio: np.ndarray) -> str:
        """
        Process pre-recorded audio (used by hot window mode).

        Args:
            audio: Audio data from hot window capture

        Returns:
            LLM response text
        """
        request_id = str(time.time())
        metrics = PipelineMetrics(request_id=request_id)
        metrics.vad_end_time = time.perf_counter()

        print(f"Captured {len(audio) / self.config.sample_rate:.1f}s of audio")

        # Transcribe
        metrics.stt_start_time = time.perf_counter()
        transcription = self.stt.transcribe(audio, self.config.sample_rate)
        metrics.stt_end_time = time.perf_counter()

        user_text = transcription.text
        print(f"You: {user_text}")
        print(f"  [STT: {transcription.duration_ms:.0f}ms]")

        if not user_text.strip():
            print("No speech detected.")
            return ""

        # Check for interrupt command (shouldn't happen in hot window, but just in case)
        if self._is_interrupt_command(user_text):
            print("  [Interrupt command ignored in hot window]")
            return ""

        # Check for health/fitness intent FIRST (0 tokens for cached data)
        health_intent = self._detect_health_intent(user_text)
        if health_intent:
            print(f"  [Health intent: {health_intent}]")
            response_text = await self._handle_health_intent(health_intent, user_text)
            print(f"ATLAS: {response_text}")
            await self._speak(response_text)

            metrics.pipeline_end_time = time.perf_counter()
            self._last_metrics = metrics
            print(f"  [Health: {(metrics.pipeline_end_time - metrics.vad_end_time) * 1000:.0f}ms]")

            # Stay in hot window for follow-ups
            self._in_hot_window = True
            self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s
            return response_text

        # Check for meal log intent - handle directly without LLM
        if self._is_meal_log(user_text):
            print("  [Meal log detected]")
            response_text = await self._handle_meal_log(user_text)
            print(f"ATLAS: {response_text}")
            await self._speak(response_text)

            metrics.pipeline_end_time = time.perf_counter()
            self._last_metrics = metrics
            print(f"  [Meal log: {(metrics.pipeline_end_time - metrics.vad_end_time) * 1000:.0f}ms]")
            return response_text

        # Check for capture intent - handle directly without LLM
        if self._is_capture_intent(user_text):
            print("  [Capture intent detected]")
            response_text = await self._handle_capture(user_text)
            print(f"ATLAS: {response_text}")
            await self._speak(response_text)

            metrics.pipeline_end_time = time.perf_counter()
            self._last_metrics = metrics
            print(f"  [Capture: {(metrics.pipeline_end_time - metrics.vad_end_time) * 1000:.0f}ms]")

            # Stay in hot window for follow-up captures
            self._in_hot_window = True
            self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s
            return response_text

        # Route and generate response (reuse logic from process_turn)
        response_text = ""
        first_token = True
        sentence_buffer = ""
        was_interrupted = False

        if self.config.use_router:
            decision = self.router.classify(user_text)
            tier = decision.tier
            print(f"  [Route: {tier.value}, conf: {decision.confidence:.2f}]")

            if self.config.enable_filler_phrases and tier != Tier.LOCAL:
                filler = self._get_filler_phrase()
                print(f"ATLAS: {filler}")
                await self._speak(filler)
                metrics.tts_first_audio_time = time.perf_counter()

        print("ATLAS: ", end="", flush=True)

        if self.config.use_router:
            stream = self.router.route_and_stream(
                user_text,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )
        else:
            stream = self.llm.stream(
                user_text,
                system=self.config.system_prompt,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )

        async for token in stream:
            if first_token:
                metrics.llm_first_token_time = time.perf_counter()
                first_token = False

            response_text += token
            sentence_buffer += token
            print(token, end="", flush=True)

            if sentence_buffer.rstrip().endswith(('.', '!', '?', ':')):
                if metrics.tts_first_audio_time == 0:
                    metrics.tts_first_audio_time = time.perf_counter()

                was_interrupted = await self._speak_interruptible(sentence_buffer.strip())
                sentence_buffer = ""

                if was_interrupted:
                    print(" [interrupted]", end="")
                    break

        if sentence_buffer.strip() and not was_interrupted:
            if metrics.tts_first_audio_time == 0:
                metrics.tts_first_audio_time = time.perf_counter()
            await self._speak_interruptible(sentence_buffer.strip())

        print()
        metrics.pipeline_end_time = time.perf_counter()

        self._last_metrics = metrics
        print(f"  [TTFA: {metrics.time_to_first_audio_ms:.0f}ms, "
              f"Total: {metrics.total_latency_ms:.0f}ms]")

        # Reset hot window for next turn
        self._in_hot_window = True
        self._hot_window_end_time = time.perf_counter() + self.config.hot_window_duration_s

        return response_text

    def get_last_metrics(self) -> Optional[PipelineMetrics]:
        """Get metrics from the last conversation turn."""
        return self._last_metrics


class SimplePipeline:
    """
    Simplified pipeline for testing without push-to-talk.

    Processes text input directly without audio recording.
    """

    def __init__(self, config: Optional[VoicePipelineConfig] = None):
        """Initialize simple pipeline."""
        self.config = config or VoicePipelineConfig()
        self._tts = None
        self._llm = None

    @property
    def tts(self):
        """Get TTS instance."""
        if self._tts is None:
            self._tts = get_tts(self.config.tts_voice)
        return self._tts

    @property
    def llm(self):
        """Get LLM client."""
        if self._llm is None:
            self._llm = get_client(model=self.config.llm_model)
        return self._llm

    async def process_text(self, user_text: str) -> str:
        """
        Process text input and return spoken response.

        Args:
            user_text: User input text

        Returns:
            LLM response text
        """
        response_text = ""
        sentence_buffer = ""

        print(f"You: {user_text}")
        print("ATLAS: ", end="", flush=True)

        async for token in self.llm.stream(
            user_text,
            system=self.config.system_prompt,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
        ):
            response_text += token
            sentence_buffer += token
            print(token, end="", flush=True)

            # Speak complete sentences
            if sentence_buffer.rstrip().endswith(('.', '!', '?', ':')):
                result = self.tts.synthesize(sentence_buffer.strip())
                sd.play(result.audio, result.sample_rate)
                sd.wait()
                sentence_buffer = ""

        # Speak remaining text
        if sentence_buffer.strip():
            result = self.tts.synthesize(sentence_buffer.strip())
            sd.play(result.audio, result.sample_rate)
            sd.wait()

        print()
        return response_text

    async def start(self) -> None:
        """Start text-based conversation loop."""
        print("ATLAS Simple Pipeline (text mode)")
        print("Type 'quit' to exit\n")

        try:
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in ('quit', 'exit', 'q'):
                    break
                if user_input:
                    await self.process_text(user_input)
        except KeyboardInterrupt:
            pass

        print("\nGoodbye, sir.")


def main():
    """CLI entry point for voice pipeline."""
    asyncio.run(_async_main())


async def _async_main():
    """Async entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ATLAS Voice Pipeline")
    parser.add_argument(
        "--text-mode",
        action="store_true",
        help="Run in text mode (no audio)",
    )
    parser.add_argument(
        "--stt",
        choices=["moonshine", "faster-whisper"],
        default="moonshine",
        help="STT backend (default: moonshine)",
    )
    parser.add_argument(
        "--voice",
        default="bm_lewis",
        help="TTS voice (default: bm_lewis)",
    )

    args = parser.parse_args()

    config = VoicePipelineConfig(
        stt_backend=args.stt,
        tts_voice=args.voice,
    )

    if args.text_mode:
        pipeline = SimplePipeline(config)
    else:
        pipeline = VoicePipeline(config)

    await pipeline.start()


if __name__ == "__main__":
    main()
