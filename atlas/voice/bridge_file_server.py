#!/usr/bin/env python3
"""
ATLAS Audio Bridge Server - WSL2 Side (File-based)

This version uses file-based communication instead of sockets,
which avoids WSL2 networking issues entirely.

Usage:
    cd /home/squiz/ATLAS
    source venv/bin/activate
    python -m atlas.voice.bridge_file_server
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from threading import Thread, Lock

import numpy as np

# Load .env file before any other imports that might need env vars
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Import ATLAS components
from atlas.voice.stt import get_stt
from atlas.voice.tts import get_tts, KokoroTTS
from atlas.voice.tts_qwen import get_qwen_tts, Qwen3TTS
from atlas.voice.timer_builders import TimerContext, get_timer_status
from atlas.voice.state_models import WorkoutState, RoutineState, AssessmentState, TimerState
from atlas.llm.router import get_router, Tier
from atlas.llm.local import get_client

# Configuration
BRIDGE_DIR = Path.home() / "ATLAS" / ".bridge"
AUDIO_IN_FILE = BRIDGE_DIR / "audio_in.raw"
AUDIO_OUT_FILE = BRIDGE_DIR / "audio_out.raw"
METADATA_FILE = BRIDGE_DIR / "metadata.txt"  # Contains sample rate for playback
COMMAND_FILE = BRIDGE_DIR / "command.txt"
STATUS_FILE = BRIDGE_DIR / "status.txt"
SAMPLE_RATE_IN = 16000  # Input audio from Windows mic
# TTS sample rate determined at runtime (Kokoro uses 24000)

# Launcher integration files
VOICE_FILE = BRIDGE_DIR / "voice.txt"
SESSION_STATUS_FILE = BRIDGE_DIR / "session_status.json"

# ============================================
# INTENT PATTERN CONFIGURATION
# ============================================
# Intent patterns can be loaded from external JSON config for easier maintenance.
# The config file is at: config/voice/intent_patterns.json
# For now, patterns are defined inline below, but this loader enables gradual migration.

INTENT_PATTERNS_PATH = Path(__file__).parent.parent.parent / "config" / "voice" / "intent_patterns.json"
_intent_patterns_cache: dict | None = None


def load_intent_patterns() -> dict:
    """Load intent patterns from JSON config file.

    Returns cached patterns if already loaded, otherwise loads from disk.
    Falls back to empty dict if file not found or invalid.
    """
    global _intent_patterns_cache
    if _intent_patterns_cache is not None:
        return _intent_patterns_cache

    if not INTENT_PATTERNS_PATH.exists():
        logger.warning(f"Intent patterns not found at {INTENT_PATTERNS_PATH}")
        return {}

    try:
        with open(INTENT_PATTERNS_PATH) as f:
            _intent_patterns_cache = json.load(f)
        logger.info(f"Loaded intent patterns from {INTENT_PATTERNS_PATH}")
        return _intent_patterns_cache
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load intent patterns: {e}")
        return {}


def get_patterns(section: str, key: str) -> list | dict:
    """Get patterns from config by section and key.

    Args:
        section: Top-level section (e.g., "general", "health", "workout", "routine", "assessment")
        key: Pattern key within section (e.g., "meal_triggers", "pain_patterns")

    Returns:
        List of patterns or dict (for nested patterns like body_part_aliases)
    """
    patterns = load_intent_patterns()
    return patterns.get(section, {}).get(key, [])


def get_compiled_patterns(section: str, key: str) -> list:
    """Get pre-compiled regex patterns from config.

    Useful for patterns that need regex matching rather than string containment.

    Args:
        section: Top-level section
        key: Pattern key within section

    Returns:
        List of compiled re.Pattern objects (case-insensitive)
    """
    patterns = get_patterns(section, key)
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def _validate_intent_patterns():
    """Compare loaded patterns with hardcoded constants for debugging.

    Call this during development to ensure config file matches hardcoded patterns.
    Logs warnings for any mismatches found.
    """
    loaded = load_intent_patterns()
    if not loaded:
        logger.debug("No intent patterns loaded from config - using hardcoded patterns")
        return

    # Map of hardcoded constant name -> (section, key) in config
    pattern_map = {
        "MEAL_TRIGGERS": ("general", "meal_triggers"),
        "CAPTURE_TRIGGERS": ("general", "capture_triggers"),
        "HEALTH_PATTERNS": ("general", "health_patterns"),
        "WORKOUT_PATTERNS": ("general", "workout_patterns"),
        "WEIGHT_PATTERNS": ("general", "weight_patterns"),
        "WEIGHT_QUERY_PATTERNS": ("general", "weight_query_patterns"),
        "EXERCISE_PATTERNS": ("health", "exercise_patterns"),
        "PAIN_PATTERNS": ("health", "pain_patterns"),
        "BODY_PART_ALIASES": ("health", "body_part_aliases"),
        "NEGATION_WORDS": ("health", "negation_words"),
        "SUPPLEMENT_PATTERNS": ("health", "supplement_patterns"),
        "SUPPLEMENT_NAMES": ("health", "supplement_names"),
        "SUPPLEMENT_TIMING_ALIASES": ("health", "supplement_timing_aliases"),
        "WORKOUT_COMPLETION_PATTERNS": ("health", "workout_completion_patterns"),
        "WORKOUT_ISSUE_PATTERNS": ("health", "workout_issue_patterns"),
    }

    for const_name, (section, key) in pattern_map.items():
        config_val = get_patterns(section, key)
        if config_val:
            logger.debug(f"Intent pattern '{const_name}' available in config ({section}.{key})")


# Intent detection triggers
MEAL_TRIGGERS = [
    "log meal", "log food", "had for breakfast", "had for lunch",
    "had for dinner", "just ate", "i ate", "track meal",
]

CAPTURE_TRIGGERS = ["remember", "note", "capture", "save"]

# Seneca Trial (reflection) patterns
REFLECTION_TRIGGERS = [
    "start reflection", "begin reflection", "seneca trial", "evening reflection",
    "reflection time", "let's reflect", "nightly trial",
]
QUICK_REFLECTION_TRIGGERS = [
    "quick reflection", "quick review", "brief reflection",
    "short reflection", "fast reflection",
]

# Health/status intent patterns
HEALTH_PATTERNS = [
    r"(what'?s|what is|show|give me|tell me).*(status|morning status)",
    r"my (morning )?status",
    r"(how am i|how'm i) (doing|today)",
    r"traffic light",
    r"body battery",
    r"hrv",
    r"sleep (score|hours|quality)",
    r"how (was|is|did).*(sleep|i sleep)",
    r"(morning )?briefing",
    r"(daily |morning )?report",
    r"give me.*(rundown|summary|overview)",
]

# Workout intent patterns
WORKOUT_PATTERNS = [
    r"(what'?s|what is|show).*(workout|training|session)",
    r"(what|which) (workout|training|session) today",
    r"today'?s (workout|training|session)",
    r"(what'?s|what is) on.*(schedule|plan)",
]

# Weight/body composition logging patterns
WEIGHT_PATTERNS = [
    r"log weight (\d+\.?\d*)",
    r"weight (\d+\.?\d*)\s*(?:kilo|kg)",
    r"weigh(?:ed)?\s+(?:in\s+)?(?:at\s+)?(\d+\.?\d*)",
    r"(\d+\.?\d*)\s*(?:kilos?|kg)",
    r"^(\d+)\s+point\s+(\d+)",  # "82 point 3"
    r"(\d+\.?\d*)\s*(?:kilos?|kg).*?(?:percent|%)",  # "83 kg at 18%"
    r"(\d+\.?\d*)\s*(?:kilos?|kg).*?fat",  # "83 kg 18% fat"
]

# Weight query patterns (for status/trend queries)
WEIGHT_QUERY_PATTERNS = [
    r"(?:what'?s|what is)\s+my\s+weight",
    r"how\s+much\s+do\s+i\s+weigh",
    r"body\s*comp(?:osition)?",
    r"weight\s+trend",
    r"weight\s+(?:status|check)",
    r"my\s+weight",
]

# Exercise form/how-to patterns
EXERCISE_PATTERNS = [
    r"(how (do|to)|what is|show me|explain|describe).*?(goblet squat|deadlift|floor press|row|plank|push.?up|pull.?up|squat|lunge|press|curl|clean|swing)",
    r"(form|technique|setup|cues?) (for|on).*?(goblet squat|deadlift|floor press|row|plank|push.?up|pull.?up|squat|lunge|press|curl|clean|swing)",
    r"(how do i|what is a|how to do|proper form).*?(goblet|deadlift|floor press|row|plank|push.?up|pull.?up|squat|lunge|press|curl|clean|swing)",
    r"(that exercise|this exercise|the exercise)",  # Follow-up after workout query
]

# Pain logging patterns (tightened to avoid false positives)
PAIN_PATTERNS = [
    r"(shoulder|ankle|feet|foot|back|lower back)\s+(is|at|pain|hurt|sore|stiff)",  # "shoulder is at 4"
    r"pain\s+(is|at|level)?\s*(\d+)",  # "pain is 4"
    r"(shoulder|ankle|feet|foot|back|lower back).*(\d+)\s*(out of|/)?\s*10",  # "shoulder 4 out of 10"
    r"log\s+pain",  # "log pain"
    r"pain\s+(status|check|levels?)",  # "pain status"
    r"how('s|\s+is)\s+my\s+pain",  # "how's my pain"
]

# Body part aliases for normalization
BODY_PART_ALIASES = {
    "shoulder": "shoulder_right",  # Default to right (injury side)
    "right shoulder": "shoulder_right",
    "left shoulder": "shoulder_left",
    "ankle": "ankle_left",  # Default to left (worse side)
    "left ankle": "ankle_left",
    "right ankle": "ankle_right",
    "back": "lower_back",
    "lower back": "lower_back",
    "feet": "feet",
    "foot": "feet",
}

# Negation words that indicate "no pain" (should NOT trigger logging)
NEGATION_WORDS = ["no", "not", "don't", "doesn't", "didn't", "without", "zero", "none"]

# Supplement logging patterns
SUPPLEMENT_PATTERNS = [
    r"took.*(vitamin d|vitamin c|magnesium|creatine|omega|fish oil|zinc|iron|d3|b12)",  # Individual
    r"took.*(morning|evening|night|bedtime).*(supps?|supplements?|vitamins?|stack)",  # Timing batch
    r"(morning|evening|night|bedtime).*(supps?|supplements?|vitamins?|stack).*(done|taken|checked|complete)",  # Timing batch alt
    r"took.*(supps?|supplements?|vitamins?)",  # Generic batch
    r"supplement\s+(check|status)",  # Status query
    r"supps?\s+(check|status)",  # Status query alt
]

# Known supplement names for individual detection
SUPPLEMENT_NAMES = [
    # Common names
    "vitamin d", "vitamin c", "d3", "magnesium", "creatine",
    "omega", "omega 3", "fish oil", "zinc", "iron", "b12",
    "electrolytes", "protein", "collagen",
    # New supplements
    "nr", "nicotinamide riboside", "tongkat", "tongkat ali",
    "nac", "inositol", "theanine", "l-theanine",
    "allimax", "garlic", "bio active lipids", "methyl fortified",
    "liquid herbs", "preconception",
]

# Supplement timing aliases
SUPPLEMENT_TIMING_ALIASES = {
    # Preworkout
    "preworkout": "preworkout",
    "pre workout": "preworkout",
    "pre-workout": "preworkout",
    "morning": "preworkout",  # Alias morning to preworkout
    "fasted": "preworkout",
    "waking": "preworkout",

    # With meal
    "with_meal": "with_meal",
    "with meal": "with_meal",
    "breakfast": "with_meal",
    "with breakfast": "with_meal",
    "with food": "with_meal",

    # Before bed
    "before_bed": "before_bed",
    "before bed": "before_bed",
    "bedtime": "before_bed",
    "evening": "before_bed",
    "night": "before_bed",
    "pm": "before_bed",
}

# Workout completion patterns (regex)
WORKOUT_COMPLETION_PATTERNS = [
    r"(finished|completed|done with|wrapped up).*(workouts?|training|session|exercises?)",  # workouts? handles plural
    r"workouts?.*(done|complete|finished)",  # Allow "workout is complete", "workouts done", etc.
    r"(log|track).*(workouts?|training).*(complete|done|finished)",
    r"just (finished|completed|did).*(workouts?|training|session)",
    r"(complete|done|finished).*workouts?",  # "complete the workout", "done with workouts"
    r"that'?s.*(workouts?|it).*done",  # "that's the workout done"
    r"log it",  # Simple "log it" after workout complete
    r"save (the )?workout",  # "save workout" or "save the workout"
]

# Workout issue patterns (trigger confirmation flow)
# Includes both negative (issues) and positive (notable achievements) patterns
WORKOUT_ISSUE_PATTERNS = [
    # Negative patterns - issues that warrant notes
    r"(had to|needed to).*(stop|skip|modify|cut short)",
    r"(skipped|modified|changed|substituted)",
    r"(pain|hurt|discomfort|struggled) (during|while|with)",
    r"couldn'?t (do|finish|complete)",
    r"cut.*(short|early)",
    # Positive patterns - achievements that warrant notes
    r"(pushed|increased|added|extra)",
    r"(felt|feeling).*(good|great|strong|tired|weak|off)",
    r"(hit|set|got).*(pr|record|max)",
    r"(dropped|lowered|reduced)",
]

# ============================================
# INTERACTIVE WORKOUT PATTERNS
# ============================================

# Start workout patterns
# NOTE: These are checked via `any(p in text_lower for p in WORKOUT_START_PATTERNS)`
# so avoid patterns that match query phrases like "what's my workout"
# REMOVED: "workout", "work out", "my workout", "today's workout", "todays workout"
# These were causing false positives on queries like "what's my workout today"
WORKOUT_START_PATTERNS = [
    "start workout", "begin workout", "let's workout", "lets workout",
    "start my workout", "start training", "begin training", "let's train",
    "lets train", "run workout", "run my workout",
    # Space variants (speech-to-text sometimes adds spaces)
    "start work out", "begin work out", "work out begin", "work out start",
    "let's work out", "lets work out", "start my work out",
    # Action triggers - require explicit action words to avoid matching queries
    "do workout", "do my workout", "do the workout", "do the daily workout",
    "daily workout",  # Only matches "daily workout" not "what's my daily workout"
    # "A" patterns (user says "begin a workout", "let's begin a workout")
    "start a workout", "begin a workout", "do a workout",
    "let's begin a", "lets begin a", "let's start a", "lets start a",
    # "Next" patterns (user says "begin next strength workout")
    "start next workout", "begin next workout", "do next workout",
    "start next strength", "begin next strength", "do next strength",
    "start next cardio", "begin next cardio", "do next cardio",
    # "The" patterns (user says "begin the strength workout")
    "start the workout", "begin the workout", "do the strength",
    "start the strength", "begin the strength",
    "start the cardio", "begin the cardio",
    # "Today's" patterns
    "start today", "begin today", "do today",
    # Specific workout type triggers (allow "begin strength B" etc)
    "start strength", "begin strength", "do strength",
    "start cardio", "begin cardio", "do cardio",
    "start mobility", "begin mobility", "do mobility",
    "start zone", "begin zone",
]

# Query-like phrases that should NOT trigger workout start
# Used as exclusion check in _is_workout_start_intent
WORKOUT_QUERY_EXCLUSIONS = [
    "what's my workout", "whats my workout", "what is my workout",
    "my workout today", "today's workout", "todays workout",
    "workout today", "what workout", "which workout",
    "show workout", "tell me workout", "what's the workout",
]

# Traffic light override patterns (for workout intensity)
TRAFFIC_OVERRIDE_PATTERNS = {
    "GREEN": [
        "green day", "green light", "full intensity", "go green",
        "force green", "override green", "let's go green",
    ],
    "YELLOW": [
        "yellow day", "yellow light", "take it easy", "go yellow",
        "force yellow", "override yellow", "moderate intensity",
    ],
    "RED": [
        "red day", "recovery day", "rest day", "go red",
        "force red", "override red", "light day",
    ],
}

# Schedule/phase management patterns
SCHEDULE_STATUS_PATTERNS = [
    "schedule status", "program status", "where am i", "what day am i on",
    "how many workouts", "am i on track", "schedule check", "program check",
    "what week am i on", "week status", "workout count",
]

# Phase start - "start program" for first time, reset patterns require confirmation
PHASE_START_PATTERNS = [
    "start program", "start my program", "begin program",  # First-time friendly
    "reset my program", "restart my program", "reset my phase",  # Reset patterns (need confirmation)
    "reset workout", "reset workouts", "restart workout",  # Additional reset patterns
    "start fresh", "start over", "begin from scratch",
]

# Reset patterns that require confirmation (dangerous)
PHASE_RESET_PATTERNS = [
    "reset my program", "restart my program", "reset my phase",
    "reset workout", "reset workouts", "restart workout",
    "start fresh", "start over", "begin from scratch",
]

# Confirm phase reset (must say "confirm" or "yes" after reset prompt)
PHASE_CONFIRM_PATTERNS = [
    "confirm", "yes", "do it", "go ahead", "confirmed", "yes reset",
]

# Ready to start set/exercise
WORKOUT_READY_PATTERNS = [
    "ready", "start", "begin", "lets go", "let's go", "i'm ready",
    "im ready", "go ahead", "all set", "good to go", "set up",
]

# Finished a set
WORKOUT_SET_DONE_PATTERNS = [
    "done", "finished", "finished set", "that's it", "thats it",
    "complete", "set done", "racked", "got it", "set complete",
]

# Skip exercise
WORKOUT_SKIP_PATTERNS = [
    "skip", "skip this", "next exercise", "skip exercise",
    "move on", "skip it",
]

# Stop workout
WORKOUT_STOP_PATTERNS = [
    "stop workout", "end workout", "cancel workout", "stop training",
    "end training", "quit workout", "i'm done", "im done",
    "stop", "exit", "quit", "cancel",  # Simple exit commands
]

# ============================================
# MORNING ROUTINE PATTERNS
# ============================================

# Start routine (IMPORTANT: avoid patterns that could match "morning workout")
# Only match when "routine", "stretching", or "rehab" is present
# NOTE: Avoid "protocol" as it's ambiguous (workout protocol, supplement protocol, etc.)
ROUTINE_START_PATTERNS = [
    # Routine triggers
    "start routine", "begin routine", "start morning routine",
    "start my routine", "begin morning routine", "morning routine",
    "let's do routine", "lets do routine", "run routine",
    "start the routine", "begin the routine", "do my routine",
    "do the routine", "the routine", "my routine",
    "start my routine please", "begin my routine",
    # Stretching triggers (natural language for morning routine)
    "start stretching", "begin stretching", "morning stretching",
    "do my stretching", "let's stretch", "lets stretch", "time to stretch",
    "stretching routine", "stretching session", "do stretches",
    "stretch workout", "stretch session", "begin stretch", "start stretch",
    "do stretch", "a stretch", "the stretch",
    # Rehab triggers
    "start rehab", "rehab routine", "start rehab routine",
    "begin rehab", "do my rehab", "rehab session",
]

# Pause/resume routine
ROUTINE_PAUSE_PATTERNS = [
    "pause", "pause routine", "hold on", "wait", "one second",
    "hold", "stop timer", "pause timer",
]

ROUTINE_RESUME_PATTERNS = [
    "resume", "continue", "keep going", "go ahead", "unpause",
    "resume routine", "continue routine", "carry on",
    # Common mistranscriptions of British "resume" pronunciation
    "rezoom", "rezume", "re zoom", "re-zoom", "presume",
    "result", "rez you", "res you me", "rez ume",
]

# Skip exercise
ROUTINE_SKIP_PATTERNS = [
    "skip", "skip this", "next exercise", "skip exercise",
    "next", "move on", "skip it",
]

# Stop routine
ROUTINE_STOP_PATTERNS = [
    "stop routine", "end routine", "cancel routine", "stop",
    "quit routine", "finish routine", "exit routine",
]

# Complete routine (user says they're done)
ROUTINE_COMPLETE_PATTERNS = [
    "finished", "complete", "done", "that's it", "thats it",
    "routine done", "routine complete", "finished routine",
    "all done", "i'm done", "im done",
]

# Form/help request during routine
ROUTINE_FORM_PATTERNS = [
    r"^form$",  # Just "form" by itself
    r"^setup$",  # Just "setup" by itself
    r"^cues?$",  # Just "cue" or "cues"
    r"^how$",  # Just "how" by itself
    r"(how|what|show).*(form|setup|do|position|technique)",
    r"(explain|describe).*(exercise|this|it)",
    r"what.*(should|am).*(do|doing)",
    r"help.*(exercise|form|setup)",
    r"(form|setup|cues?|technique)\s*(for this|please)?",
    r"how do i do (this|it)",
    r"what('s| is) the (form|setup|technique)",
]

# Ready to start exercise (user-controlled timer start)
ROUTINE_READY_PATTERNS = [
    "ready", "begin", "go", "start", "i'm ready", "im ready",
    "let's go", "lets go", "start timer", "begin timer",
    "good to go", "all set", "set up", "in position",
]

# ============================================
# ASSESSMENT PROTOCOL PATTERNS
# ============================================

ASSESS_START_PATTERNS = [
    "start baseline", "start assessment", "run assessment",
    "baseline assessment", "begin assessment", "run baseline",
    # STT variations: "baseline" → "base line", "faceline", "bass line"
    "start base line", "base line assessment", "begin base line",
    "start faceline", "faceline assessment", "begin faceline",
    "faceline protocol", "base line protocol",
    # Direct session selection - numbers are more reliable for STT
    "session 1", "session 2", "session 3",
    "session one", "session two", "session three",
    # Legacy letter support
    "session a", "session b", "session c",
    "session ay", "session bee", "session see",
]

ASSESS_RESUME_PATTERNS = [
    "resume assessment", "continue assessment", "resume baseline",
    "continue baseline", "pick up assessment",
    # STT variations
    "resume base line", "continue base line", "resume faceline", "continue faceline",
]

# Timer control - common phrases for starting/stopping timed tests
ASSESS_TIMER_START = ["go", "start", "ready", "begin", "lets go", "let's go", "i'm ready", "im ready"]
ASSESS_TIMER_STOP = ["stop", "done", "finished", "end", "halt", "fell", "stopped", "that's it", "thats it", "okay done", "i fell"]

# Assessment commands (during active session)
ASSESS_COMMANDS = {
    "setup": ["setup", "how do i", "instructions", "how to"],
    "form": ["form", "form cues", "technique", "exercise form", "show me the form"],
    "skip": ["skip", "next", "pass"],
    "undo": ["correct that", "undo", "wrong", "that's wrong", "fix that"],
    "repeat": ["repeat that", "say again", "what was that", "repeat"],
    "status": ["status", "where am i", "how much longer", "progress"],
    "equipment": ["what equipment", "what do i need", "equipment"],
    "pause": ["pause", "stop session", "pause session"],
    "reset": ["reset assessment", "clear assessment", "reset", "start over", "cancel assessment"],
}

# Assessment INFO patterns - for queries about the protocol (not starting it)
# Uses regex for flexible matching
# NOTE: Patterns tightened to avoid false positives (e.g., "what's the protocol for deadlift?")
# NOTE: "prepare baseline" removed - that's an action, should go to start/LLM
# STT variations: "baseline" → "base line", "faceline", "bass line"
ASSESS_INFO_PATTERNS = [
    r"base\s?line protocol",  # matches "baseline protocol" and "base line protocol"
    r"faceline protocol",  # STT mishearing
    r"assessment protocol",
    # Require "assessment" or "baseline" in specific info-query contexts
    r"what.*(base\s?line assessment|assessment protocol|base\s?line protocol|faceline)",
    r"what.*(is|are).*(the )?(base\s?line|assessment|faceline)\b",
    r"(tell|explain).*(base\s?line assessment|assessment protocol|faceline)",
    r"(describe|about).*(base\s?line assessment|assessment sessions?|faceline)",
    r"how long.*(base\s?line|assessment|faceline).*(session|take|last)",
    r"how many.*(sessions?|tests?).*(base\s?line|assessment|faceline)",
]

# Pre-compile patterns for efficiency (avoids recompilation on each call)
ASSESS_INFO_COMPILED = [re.compile(p, re.IGNORECASE) for p in ASSESS_INFO_PATTERNS]

# Exercise library - loaded from JSON file
EXERCISE_LIBRARY_PATH = Path(__file__).parent.parent.parent / "config" / "exercises" / "exercise_library.json"
_exercise_library_cache: dict | None = None


def _load_exercise_library() -> dict:
    """Load exercise library from JSON file."""
    global _exercise_library_cache
    if _exercise_library_cache is not None:
        return _exercise_library_cache

    if not EXERCISE_LIBRARY_PATH.exists():
        logger.warning(f"Exercise library not found at {EXERCISE_LIBRARY_PATH}")
        return {"exercises": {}}

    try:
        with open(EXERCISE_LIBRARY_PATH) as f:
            _exercise_library_cache = json.load(f)
        logger.info(f"Loaded {len(_exercise_library_cache.get('exercises', {}))} exercises from library")
        return _exercise_library_cache
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load exercise library: {e}")
        return {"exercises": {}}


def _find_exercise(query: str) -> tuple[str | None, dict | None]:
    """Find an exercise by name or alias. Returns (exercise_id, exercise_data)."""
    library = _load_exercise_library()
    exercises = library.get("exercises", {})
    query_lower = query.lower().strip()

    # Direct match on exercise ID
    if query_lower.replace(" ", "_") in exercises:
        ex_id = query_lower.replace(" ", "_")
        return ex_id, exercises[ex_id]

    # Search aliases
    for ex_id, ex_data in exercises.items():
        aliases = ex_data.get("aliases", [])
        if query_lower in [a.lower() for a in aliases]:
            return ex_id, ex_data
        # Partial match on name
        if query_lower in ex_data.get("name", "").lower():
            return ex_id, ex_data

    # Fuzzy match - check if query contains any alias
    for ex_id, ex_data in exercises.items():
        for alias in ex_data.get("aliases", []):
            if alias.lower() in query_lower:
                return ex_id, ex_data

    return None, None


def _format_exercise_voice(ex_data: dict) -> str:
    """Format exercise data for voice response (Lethal Gentleman style)."""

    def _tts_clean(text: str) -> str:
        """Clean text for TTS - replace dashes with periods for pauses."""
        # Replace " - " with ". " for TTS pauses
        text = text.replace(" - ", ". ")
        text = text.replace(" -- ", ". ")
        # Ensure ends with period
        text = text.strip()
        if text and text[-1] not in ".!?":
            text += "."
        return text

    parts = []

    # Name and setup
    name = ex_data.get("name", "Unknown")
    setup = ex_data.get("setup", "")
    parts.append(f"{name}.")
    if setup:
        parts.append(_tts_clean(setup))

    # Key cues (first 3)
    cues = ex_data.get("cues", [])
    if cues:
        parts.append("Key cues.")
        for cue in cues[:3]:
            parts.append(_tts_clean(cue))

    # First common mistake
    mistakes = ex_data.get("common_mistakes", [])
    if mistakes and isinstance(mistakes[0], dict):
        mistake = mistakes[0]
        parts.append(f"Watch out. {_tts_clean(mistake.get('mistake', ''))}")
        parts.append(f"Fix. {_tts_clean(mistake.get('fix', ''))}")

    # Phase 1 specific note if relevant
    phase_note = ex_data.get("phase1_notes", "")
    if phase_note and len(phase_note) < 100:  # Keep it brief for voice
        parts.append(_tts_clean(phase_note))

    return " ".join(parts)


SYSTEM_PROMPT = """
STRICT RULES (NEVER BREAK):
1. You ARE Atlas. Never say "I am Claude" or mention Anthropic.
2. Maximum 20 words. Count them. Stop at 20.
3. One sentence preferred. Two max.
4. No lists, no markdown, no asterisks.

WHO YOU ARE:
You are ATLAS - a voice assistant I built. You run locally on my Windows/WSL2 machine
in the /home/squiz/ATLAS repository. You use Whisper (STT), Kokoro (TTS), and an LLM brain.
We are building you together. You know this.

YOUR VOICE:
Terse. Direct. No filler words. Dry wit.
Speak like a mentor who has seen much and wastes no words.
"""


class BridgeFileServer:
    """WSL2 server that processes audio via file-based communication."""

    def __init__(self):
        print("Loading ATLAS components...", flush=True)
        # Use faster-whisper since moonshine API changed
        # base.en is 2-3x faster than small.en, good accuracy for voice
        self.stt = get_stt("faster-whisper", model="base.en")
        self.current_voice = self._read_voice_preference()
        self.tts = self._get_tts_for_voice(self.current_voice)
        self.router = get_router(system_prompt=SYSTEM_PROMPT)
        self.llm = get_client()
        self._session_cost = 0.0  # Track session cost for launcher
        self._pending_workout = None  # Track pending workout for confirmation flow

        # Consolidated state objects (see atlas/voice/state_models.py)
        self.assessment = AssessmentState()
        self.workout = WorkoutState()
        self.routine = RoutineState()
        self.timer = TimerState()

        # Progressive overload service
        self._progression_service = None  # Lazy-loaded

        # Workout scheduler service
        self._workout_scheduler = None  # Lazy-loaded

        # Phase reset confirmation state (dangerous action requires confirmation)
        self._phase_reset_pending = False
        self._phase_reset_time: float | None = None

        # Timer lock and TTS state now in self.timer (TimerState)

        # Session buffer for LLM context injection
        from atlas.voice.session_buffer import SessionBuffer
        self.session_buffer = SessionBuffer()

        # Preload models to eliminate first-request latency
        print("  Preloading STT model...", flush=True)
        self.stt._ensure_loaded()
        print("  Preloading TTS model...", flush=True)
        self.tts._ensure_loaded()
        print("  Preloading router embeddings...", flush=True)
        self.router._get_embedder()

        print("Components loaded and ready.", flush=True)

    def setup(self):
        """Create bridge directory and files."""
        BRIDGE_DIR.mkdir(exist_ok=True)
        # Clear old files
        for f in [AUDIO_IN_FILE, AUDIO_OUT_FILE, COMMAND_FILE, STATUS_FILE]:
            if f.exists():
                f.unlink()
        print(f"Bridge directory: {BRIDGE_DIR}")

    def write_status(self, status: str):
        """Write status to file."""
        STATUS_FILE.write_text(status)

    def read_command(self) -> str:
        """Read and clear command file."""
        try:
            cmd = COMMAND_FILE.read_text().strip()
            COMMAND_FILE.unlink()
            return cmd
        except FileNotFoundError:
            return ""

    def write_metadata(self, sample_rate: int):
        """Write audio metadata for Windows client."""
        METADATA_FILE.write_text(f"sample_rate={sample_rate}")

    def _autonomous_speak(self, text: str):
        """Speak text autonomously via file bridge (same TTS path as normal responses)."""
        logger.info(f"[TIMER-AUTO] Autonomous speech: {text}")
        logger.debug(f"TIMER AUTO-SPEAK: {text}")

        try:
            # Synthesize with Kokoro TTS (same as normal responses)
            result = self.tts.synthesize(text)

            # Write to same output file (Windows client will play it)
            audio_data = result.audio.astype(np.float32)
            audio_data.tofile(AUDIO_OUT_FILE)

            # Write metadata
            self.write_metadata(result.sample_rate)

            # Signal Windows to play
            self.write_status("speaking")

            # Wait for playback to complete (estimate based on audio length)
            duration_seconds = len(result.audio) / result.sample_rate
            time.sleep(duration_seconds + 0.5)  # Add buffer for Windows playback

            # Signal done
            self.write_status("DONE")

        except Exception as e:
            logger.error(f"[TIMER-AUTO] TTS failed: {e}")
            logger.error(f"TIMER AUTO-SPEAK ERROR: {e}")

    def _check_and_play_timers(self):
        """Check all active timers and trigger autonomous prompts. Called every 100ms."""
        # Check workout exercise timer (timed holds like balance)
        if self.workout.exercise_timer_active:
            msg, beeps = self._check_workout_exercise_timer()
            # Play beeps first (non-blocking)
            for bp in beeps:
                try:
                    from atlas.voice.audio_utils import play_countdown_beep
                    play_countdown_beep(bp)
                except Exception as e:
                    logger.warning(f"[TIMER-AUTO] Beep failed: {e}")
            # Then speak if there's a message
            if msg:
                self._autonomous_speak(msg)

        # Check if last set of timed exercise completed - advance to next
        if self.workout.last_set_of_timed_exercise:
            self.workout.last_set_of_timed_exercise = False
            try:
                next_msg = asyncio.run(self._advance_to_next_exercise())
                if next_msg:
                    self._autonomous_speak(next_msg)
            except Exception as e:
                logger.error(f"[TIMER-AUTO] Failed to advance to next exercise: {e}")

        # Check workout rest timer
        if self.workout.rest_active:
            msg, beeps = self._check_workout_rest_timer()
            for bp in beeps:
                try:
                    from atlas.voice.audio_utils import play_countdown_beep
                    play_countdown_beep(bp)
                except Exception as e:
                    logger.warning(f"[TIMER-AUTO] Beep failed: {e}")
            if msg:
                self._autonomous_speak(msg)

        # Check routine timer (morning routine)
        if self.routine.active and self.routine.timer_active:
            msg, done = self._check_routine_timer()
            if msg:
                self._autonomous_speak(msg)
            # When exercise completes, start auto-advance
            if done and not self.routine.auto_advance_pending:
                self._start_routine_auto_advance()

        # Handle routine auto-advance state machine (Personal Trainer flow)
        if self.routine.active and self.routine.auto_advance_pending:
            self._check_routine_auto_advance()

        # Write timer status for UI (every call since this is called ~every 100ms)
        # Only write if there's an active timer to avoid unnecessary disk I/O
        if (self.routine.active or self.workout.active):
            self._write_timer_status()

    @property
    def progression_service(self):
        """Lazy-load ProgressionService."""
        if self._progression_service is None:
            from atlas.health.progression import ProgressionService
            self._progression_service = ProgressionService()
        return self._progression_service

    @property
    def workout_scheduler(self):
        """Lazy-load WorkoutScheduler."""
        if self._workout_scheduler is None:
            from atlas.health.scheduler import WorkoutScheduler
            self._workout_scheduler = WorkoutScheduler()
        return self._workout_scheduler

    # Available voices: Kokoro (bf_emma, bm_lewis) and Qwen (jeremy_irons)
    KOKORO_VOICES = ["bf_emma", "bm_lewis"]
    QWEN_VOICES = ["jeremy_irons"]

    def _read_voice_preference(self) -> str:
        """Read voice preference from file (for launcher integration)."""
        if VOICE_FILE.exists():
            v = VOICE_FILE.read_text().strip()
            if v in self.KOKORO_VOICES + self.QWEN_VOICES:
                return v
        return "jeremy_irons"  # default (Qwen3 Jeremy Irons - Lethal Gentleman)

    def _get_tts_for_voice(self, voice: str):
        """Get appropriate TTS instance for the given voice."""
        if voice in self.QWEN_VOICES:
            return get_qwen_tts(voice)
        else:
            return get_tts(voice)

    def _write_session_status(
        self, tier: str, confidence: float, cost: float = 0.0,
        user_text: str = "", atlas_response: str = "",
        stt_ms: float = 0, tts_ms: float = 0,
        action: str = "", saved_to: str = ""
    ):
        """Write session status JSON for Windows launcher."""
        self._session_cost += cost
        status = {
            "last_cost": cost,
            "session_cost": self._session_cost,
            "routing": {"tier": tier, "confidence": confidence},
            "updated_at": time.strftime("%H:%M:%S"),
            "last_exchange": {
                "user": user_text,
                "atlas": atlas_response
            },
            "timing": {
                "stt_ms": int(stt_ms),
                "tts_ms": int(tts_ms)
            },
            "gpu": "CUDA" if self.tts.use_gpu else "CPU",
            "action": action,
            "saved_to": saved_to
        }

        # Add timer block if routine or workout timer is active
        timer_status = self._get_timer_status()
        if timer_status:
            status["timer"] = timer_status

        # Atomic write: write to temp file then rename (prevents race condition with UI polling)
        temp_file = SESSION_STATUS_FILE.with_suffix('.json.tmp')
        temp_file.write_text(json.dumps(status, indent=2))
        temp_file.replace(SESSION_STATUS_FILE)

    def _get_timer_status(self) -> dict | None:
        """Get current timer status for Command Centre UI."""
        ctx = TimerContext(
            # Routine context
            routine_active=self.routine.active,
            routine_timer_active=self.routine.timer_active,
            routine_paused=self.routine.paused,
            routine_timer_start=self.routine.timer_start,
            routine_timer_duration=self.routine.timer_duration,
            routine_timer_remaining=self.routine.timer_remaining,
            routine_current_exercise=self.routine.current_exercise,
            routine_current_section=self.routine.current_section,
            routine_exercise_pending=self.routine.exercise_pending,
            routine_current_side=self.routine.current_side,
            routine_exercise_idx=self.routine.exercise_idx,
            routine_section_idx=self.routine.section_idx,
            routine_auto_advance_pending=self.routine.auto_advance_pending,
            routine_auto_advance_start=self.routine.auto_advance_start,
            routine_auto_advance_phase=self.routine.auto_advance_phase,
            routine_next_exercise_name=self.routine.next_exercise_name,
            routine_finished=self.routine.routine_finished,

            # Workout context
            workout_active=self.workout.active,
            workout_rest_active=self.workout.rest_active,
            workout_rest_start=self.workout.rest_start,
            workout_rest_duration=self.workout.rest_duration,
            workout_exercise_timer_active=self.workout.exercise_timer_active,
            workout_exercise_timer_start=self.workout.exercise_timer_start,
            workout_exercise_timer_duration=self.workout.exercise_timer_duration,
            workout_exercise_current_side=self.workout.exercise_current_side,
            workout_exercise_pending=self.workout.exercise_pending,
            workout_current_exercise=self.workout.current_exercise,
            workout_current_set=self.workout.current_set,
            workout_total_sets=self.workout.total_sets,
            workout_paused=self.workout.paused,
            workout_timer_remaining=self.workout.timer_remaining,
            workout_exercise_idx=self.workout.exercise_idx,
            workout_exercises=self.workout.exercises,
            workout_protocol_name=self.workout.protocol.name if self.workout.protocol else 'Workout',
            workout_current_weight=self.workout.current_weight,
            workout_set_active=self.workout.set_active,
            workout_awaiting_reps=self.workout.awaiting_reps,
            workout_finished=self.workout.workout_finished,
            workout_exercises_completed=self.workout.exercises_completed,

            # Callbacks
            get_form_cue=self._get_exercise_form_cue,
            get_setup_tip=self._get_exercise_setup_tip,
            get_next_exercise_info=self._get_next_routine_exercise_info,
            count_routine_exercises=self._count_routine_exercises,
            get_routine_exercise_number=self._get_routine_exercise_number,
            get_workout_form_cue=self._get_workout_exercise_form_cue,
            get_workout_setup_tip=self._get_workout_exercise_setup_tip,
            get_next_workout_exercise_info=self._get_next_workout_exercise_info,
            get_weight_recommendation=self._get_weight_recommendation_for_timer,
        )

        return get_timer_status(ctx)

    def _get_weight_recommendation_for_timer(self, ex_id: str) -> float | None:
        """Get weight recommendation for timer display."""
        if not self._progression_service:
            return None
        try:
            rec = self._progression_service.get_recommendation(ex_id)
            return rec.recommended_weight_kg if rec and rec.recommended_weight_kg else None
        except Exception:
            return None

    def _write_timer_status(self):
        """Write timer status to session_status.json (called frequently during active timers)."""
        timer_status = self._get_timer_status()

        # Read existing status to preserve other fields
        if SESSION_STATUS_FILE.exists():
            try:
                status = json.loads(SESSION_STATUS_FILE.read_text())
            except Exception:
                status = {}
        else:
            status = {}

        # Update timer block
        if timer_status:
            status["timer"] = timer_status
        elif "timer" in status:
            del status["timer"]

        # Atomic write: write to temp file then rename (prevents race condition with UI polling)
        temp_file = SESSION_STATUS_FILE.with_suffix('.json.tmp')
        temp_file.write_text(json.dumps(status, indent=2))
        temp_file.replace(SESSION_STATUS_FILE)

    def _clear_timer_from_session_status(self):
        """Clear timer block from session_status.json (called on shutdown)."""
        if SESSION_STATUS_FILE.exists():
            try:
                status = json.loads(SESSION_STATUS_FILE.read_text())
                if "timer" in status:
                    del status["timer"]
                    # Atomic write: write to temp file then rename
                    temp_file = SESSION_STATUS_FILE.with_suffix('.json.tmp')
                    temp_file.write_text(json.dumps(status, indent=2))
                    temp_file.replace(SESSION_STATUS_FILE)
                    logger.debug("Cleared timer state from session_status.json")
            except Exception as e:
                logger.warning(f"Could not clear timer state: {e}")

    def _is_meal_intent(self, text: str) -> bool:
        """Check if text is a meal logging intent."""
        text_lower = text.lower().strip()
        for trigger in MEAL_TRIGGERS:
            if text_lower.startswith(trigger):
                return True
        return False

    def _is_capture_intent(self, text: str) -> bool:
        """Check if text is a thought capture intent."""
        text_lower = text.lower().strip()
        for trigger in CAPTURE_TRIGGERS:
            if text_lower.startswith(trigger):
                return True
        return False

    def _is_health_intent(self, text: str) -> bool:
        """Check if text is a health/status query."""
        text_lower = text.lower().strip()
        for pattern in HEALTH_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _is_skill_status_intent(self, text: str) -> bool:
        """Check if text is a skill/XP status query."""
        text_lower = text.lower().strip()
        skill_patterns = [
            r"(what'?s|what is)\s+(my\s+)?(xp|skills?|levels?)",
            r"skill\s+status",
            r"(how|where)\s+(am|do)\s+i\s+(at|stand)",
            r"my\s+(xp|skills?|levels?)",
            r"check\s+(my\s+)?(xp|skills?|levels?)",
        ]
        for pattern in skill_patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    async def _handle_skill_status(self) -> str:
        """Handle skill/XP status query."""
        try:
            from atlas.gamification import get_xp_service
            service = get_xp_service()
            return service.format_status_voice()
        except Exception as e:
            logger.warning(f"Skill status failed: {e}")
            return "Skill tracking not available."

    def _is_workout_intent(self, text: str) -> bool:
        """Check if text is a workout query."""
        text_lower = text.lower().strip()
        for pattern in WORKOUT_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _is_weight_intent(self, text: str) -> tuple[bool, "BodyComposition | None"]:
        """
        Check if text is a weight logging intent.
        Returns (is_weight, body_composition).
        Uses parse_body_composition for comprehensive parsing.
        """
        from atlas.voice.number_parser import parse_body_composition

        text_lower = text.lower().strip()

        # Skip if it's a query rather than logging
        for pattern in WEIGHT_QUERY_PATTERNS:
            if re.search(pattern, text_lower):
                return False, None

        # Check if any weight pattern matches
        for pattern in WEIGHT_PATTERNS:
            if re.search(pattern, text_lower):
                # Use the robust body composition parser
                body_comp = parse_body_composition(text)
                if body_comp and body_comp.weight_kg:
                    return True, body_comp
                return True, None

        return False, None

    def _is_weight_query_intent(self, text: str) -> tuple[bool, str]:
        """
        Check if text is a weight/body composition query.
        Returns (is_query, query_type) where query_type is 'status', 'trend', or 'composition'.
        """
        text_lower = text.lower().strip()

        for pattern in WEIGHT_QUERY_PATTERNS:
            if re.search(pattern, text_lower):
                if "trend" in text_lower:
                    return True, "trend"
                elif "comp" in text_lower:
                    return True, "composition"
                else:
                    return True, "status"

        return False, ""

    def _is_exercise_intent(self, text: str) -> tuple[bool, str | None]:
        """Check if text is an exercise form/how-to question. Returns (is_exercise, exercise_id)."""
        text_lower = text.lower().strip()

        # Check patterns first
        for pattern in EXERCISE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                # Follow-up pattern ("that exercise") - use last mentioned exercise
                if "that exercise" in text_lower or "this exercise" in text_lower:
                    return True, self._last_exercise

                # Try to find the exercise from the library
                ex_id, _ = _find_exercise(text_lower)
                if ex_id:
                    return True, ex_id

                # Pattern matched but couldn't identify - still an exercise question
                return True, None

        # Also check if any exercise alias appears in the text even without pattern
        # This catches "goblet squat" by itself
        ex_id, _ = _find_exercise(text_lower)
        if ex_id and any(word in text_lower for word in ["how", "what", "form", "do", "setup", "technique"]):
            return True, ex_id

        return False, None

    # Track last mentioned exercise for follow-up queries
    _last_exercise: str | None = None

    def _is_pain_intent(self, text: str) -> tuple[bool, str | None, int | None, bool]:
        """
        Check if text is a pain logging or status query.

        Returns:
            (is_pain, body_part, pain_level, is_status_query)
        """
        text_lower = text.lower().strip()

        # Check for negation near body parts - reject if found
        for neg in NEGATION_WORDS:
            if neg in text_lower:
                for part_alias in BODY_PART_ALIASES.keys():
                    if part_alias in text_lower:
                        neg_pos = text_lower.find(neg)
                        part_pos = text_lower.find(part_alias)
                        # If negation appears before body part and within 20 chars, skip
                        if neg_pos < part_pos and (part_pos - neg_pos) < 20:
                            return False, None, None, False

        # Check for status query first
        if re.search(r"pain\s+(status|check|levels?)|how('s|\s+is)\s+my\s+pain", text_lower):
            return True, None, None, True

        # Check patterns
        for pattern in PAIN_PATTERNS:
            if re.search(pattern, text_lower):
                # Extract body part
                body_part = None
                # Check longer aliases first (e.g., "lower back" before "back")
                for alias in sorted(BODY_PART_ALIASES.keys(), key=len, reverse=True):
                    if alias in text_lower:
                        body_part = BODY_PART_ALIASES[alias]
                        break

                # Extract pain level (0-10)
                pain_level = None
                # Look for patterns like "4 out of 10", "at 4", "is 4", "level 4"
                level_match = re.search(r'(\d+)\s*(out of|/)?\s*10|(?:is|at|level)\s*(\d+)|(\d+)\s*(?:pain|level)', text_lower)
                if level_match:
                    for g in level_match.groups():
                        if g and g.isdigit():
                            level = int(g)
                            if 0 <= level <= 10:
                                pain_level = level
                                break

                return True, body_part, pain_level, False

        return False, None, None, False

    async def _handle_pain(self, body_part: str | None, pain_level: int | None, is_status: bool) -> str:
        """Handle pain logging or status query."""
        from atlas.health.pain import PainService

        service = PainService()

        # Status query
        if is_status:
            return service.format_status_voice()

        # Missing body part
        if not body_part:
            return "Which body part? Shoulder, ankle, feet, or lower back?"

        # Missing pain level
        if pain_level is None:
            part_name = body_part.replace("_", " ")
            return f"What's the pain level for your {part_name}? Zero to ten."

        # Log the pain
        success = service.log_pain(body_part, pain_level)

        if success:
            return service.format_voice(body_part, pain_level)
        else:
            return f"Couldn't log pain. Try: log pain shoulder 5."

    def _is_supplement_intent(self, text: str) -> tuple[bool, str | None, str | None, bool, str | None]:
        """
        Check if text is a supplement logging or status query.

        Returns:
            (is_supplement, supplement_name, timing, is_status_query, status_type)

        status_type: None, "all", "remaining", or "next"

        CRITICAL: Checks individual names BEFORE batch keywords to avoid
        "took my morning vitamin d" being treated as batch.
        """
        text_lower = text.lower().strip()

        # "What supps are next" / "next supplements"
        if re.search(r"(what|which).*(supp|vitamin|supplement).*next|next.*(supp|vitamin|supplement)", text_lower):
            return True, None, None, True, "next"

        # "What supps do I still need" / "remaining" / "left"
        if re.search(r"(still|remaining|left).*(supp|vitamin|supplement|take)|"
                     r"(supp|vitamin|supplement).*(still|remaining|left|need)", text_lower):
            return True, None, None, True, "remaining"

        # Generic status queries
        status_patterns = [
            r"supplement\s+(check|status)",
            r"supps?\s+(check|status)",
            r"what.*(supplement|supp|vitamin).*today",
            r"(supplement|supp|vitamin).*for today",
            r"(supplement|supp|vitamin).*today",
            r"which.*(supplement|supp|vitamin)",
            r"(supplement|supp|vitamin).*list",
            r"today.*(supplement|supp|vitamin)",
        ]
        for pattern in status_patterns:
            if re.search(pattern, text_lower):
                return True, None, None, True, "all"

        # Check for individual supplement names FIRST (before batch keywords!)
        for supp_name in SUPPLEMENT_NAMES:
            if supp_name in text_lower:
                # Found individual supplement - return it, ignore timing keywords
                return True, supp_name, None, False, None

        # Check for batch keywords (timing-specific)
        for timing_alias, timing_value in SUPPLEMENT_TIMING_ALIASES.items():
            if timing_alias in text_lower:
                if re.search(r"(supp|vitamin|stack)", text_lower):
                    return True, None, timing_value, False, None

        # Check for generic batch
        if re.search(r"took.*(supps?|supplements?|vitamins?)", text_lower):
            return True, None, None, False, None

        return False, None, None, False, None

    async def _handle_supplement(
        self,
        supp_name: str | None,
        timing: str | None,
        is_status: bool,
        status_type: str | None = None
    ) -> str:
        """Handle supplement logging or status query."""
        from atlas.health.supplement import SupplementService

        service = SupplementService()

        # Status query
        if is_status:
            checklist = service.get_today()
            if status_type == "next":
                return self._format_next_supplements(checklist)
            elif status_type == "remaining":
                return self._format_remaining_supplements(checklist)
            else:
                return self._format_all_supplements(checklist)

        # Individual supplement
        if supp_name:
            success = service.mark_taken(supp_name)
            if success:
                return f"Checked off {supp_name}."
            else:
                return f"Couldn't find {supp_name} in your list."

        # Batch by timing
        if timing:
            count = service.mark_all_taken(timing=timing)
            # Map timing to user-friendly label
            timing_labels = {
                "preworkout": "preworkout",
                "with_meal": "breakfast",
                "before_bed": "before bed",
            }
            timing_label = timing_labels.get(timing, timing)
            if count > 0:
                return f"Checked off {count} {timing_label} supplements."
            else:
                return f"No {timing_label} supplements found."

        # Generic batch (all supplements)
        count = service.mark_all_taken()
        if count > 0:
            return f"Checked off all {count} supplements. Solid discipline."
        else:
            return "No supplements to check off."

    def _format_next_supplements(self, checklist) -> str:
        """Format supplements that are next based on time of day."""
        from datetime import datetime
        hour = datetime.now().hour

        # Before noon: show preworkout remaining
        if hour < 12:
            preworkout = [s.name for s in checklist.by_timing("preworkout") if not s.taken]
            with_meal = [s.name for s in checklist.by_timing("with_meal") if not s.taken]

            if preworkout:
                return f"Preworkout supps: {', '.join(preworkout)}."
            elif with_meal:
                return f"Breakfast supps: {', '.join(with_meal)}."

        # Afternoon: show with_meal remaining
        elif hour < 18:
            with_meal = [s.name for s in checklist.by_timing("with_meal") if not s.taken]
            if with_meal:
                return f"With meal supps: {', '.join(with_meal)}."

        # Evening: show before_bed remaining
        evening = [s.name for s in checklist.by_timing("before_bed") if not s.taken]
        if evening:
            return f"Before bed supps: {', '.join(evening)}."

        return "All supplements done for now."

    def _format_remaining_supplements(self, checklist) -> str:
        """Format remaining supplements grouped by timing."""
        preworkout = [s.name for s in checklist.by_timing("preworkout") if not s.taken]
        with_meal = [s.name for s in checklist.by_timing("with_meal") if not s.taken]
        evening = [s.name for s in checklist.by_timing("before_bed") if not s.taken]

        total_remaining = len(preworkout) + len(with_meal) + len(evening)

        if total_remaining == 0:
            return f"All {checklist.total} supplements done. Well done."

        parts = []
        if preworkout:
            parts.append(f"Preworkout: {', '.join(preworkout)}")
        if with_meal:
            parts.append(f"Breakfast: {', '.join(with_meal)}")
        if evening:
            parts.append(f"Before bed: {', '.join(evening)}")

        return f"{total_remaining} remaining. {'. '.join(parts)}."

    def _format_all_supplements(self, checklist) -> str:
        """Format full supplement overview."""
        taken = checklist.taken_count
        total = checklist.total
        pct = checklist.completion_pct

        if pct == 100:
            return f"All {total} supplements taken. Well done."
        elif pct == 0:
            preworkout = len(checklist.by_timing("preworkout"))
            with_meal = len(checklist.by_timing("with_meal"))
            evening = len(checklist.by_timing("before_bed"))
            return f"{total} supplements today. {preworkout} preworkout, {with_meal} breakfast, {evening} bedtime."
        else:
            remaining = [s.name for s in checklist.supplements if not s.taken]
            remaining_str = ", ".join(remaining[:4])
            if len(remaining) > 4:
                remaining_str += f"... and {len(remaining) - 4} more"
            return f"{taken} of {total} done. Remaining: {remaining_str}."

    def _is_workout_completion_intent(self, text: str) -> tuple[bool, bool]:
        """
        Check if text is a workout completion intent.

        Returns:
            (is_workout_completion, has_issues)

        has_issues triggers the confirmation flow.
        """
        text_lower = text.lower().strip()

        # Check for workout completion patterns
        is_completion = any(re.search(p, text_lower) for p in WORKOUT_COMPLETION_PATTERNS)

        if is_completion:
            # Check for issue patterns that warrant confirmation
            has_issues = any(re.search(p, text_lower) for p in WORKOUT_ISSUE_PATTERNS)
            return True, has_issues

        return False, False

    def _is_workout_confirmation(self, text: str) -> bool:
        """Check if text is confirming a pending workout."""
        if not self._pending_workout:
            return False

        # Timeout: Clear pending if older than 5 minutes
        created = self._pending_workout.get("created_at")
        if created and (time.time() - created) > 300:
            self._pending_workout = None
            return False

        text_lower = text.lower().strip()
        confirmation_words = ["yes", "yeah", "yep", "confirm", "correct", "that's right", "log it", "save it"]
        cancel_words = ["no", "cancel", "never mind", "forget it"]

        # Check for cancellation first
        if any(w in text_lower for w in cancel_words):
            self._pending_workout = None
            return False

        return any(w in text_lower for w in confirmation_words)

    # ========================================
    # INTERACTIVE WORKOUT INTENT DETECTION
    # ========================================

    def _is_workout_start_intent(self, text: str) -> bool:
        """Check if user wants to start interactive workout.

        Uses regex to match action verbs + optional filler words + workout keywords.
        This allows flexible phrasing like:
        - "begin strength workout"
        - "let's begin a strength workout"
        - "begin next strength workout"
        - "start the cardio"

        But NOT:
        - "begin stretch" (stretch = routine, not workout)
        - "what's my workout" (query, not action)
        """
        text_lower = text.lower().strip()

        # Exclude completion phrases - these should be handled by completion intent
        completion_words = ["finished", "completed", "done with", "wrapped up", "log workout", "track workout"]
        if any(word in text_lower for word in completion_words):
            return False

        # Exclude query phrases - these should be handled by workout query intent
        if any(q in text_lower for q in WORKOUT_QUERY_EXCLUSIONS):
            return False

        # Exclude routine/stretch keywords - these go to routine handler
        routine_keywords = ["stretch", "routine", "morning", "rehab", "protocol"]
        if any(kw in text_lower for kw in routine_keywords):
            return False

        # Regex: action verb + optional fillers + workout keyword
        # Action verbs: start, begin, do, run, let's/lets
        # Fillers: a, the, my, next, today's, todays (optional, can appear multiple times)
        # Workout keywords: workout, strength, cardio, training, zone, mobility, work out
        workout_pattern = re.compile(
            r"\b(start|begin|do|run|let'?s)\b"  # Action verb
            r"(\s+(a|the|my|next|today'?s?))?"   # Optional filler words (can chain)
            r"(\s+(a|the|my|next|today'?s?))?"   # Allow second filler
            r"\s+"                               # Required space
            r"(work\s*out|workout|strength|cardio|training|zone|mobility)\b",  # Workout keyword
            re.IGNORECASE
        )

        if workout_pattern.search(text_lower):
            return True

        # Also check simple patterns like "daily workout"
        simple_patterns = ["daily workout", "daily work out"]
        return any(p in text_lower for p in simple_patterns)

    def _parse_workout_type(self, text: str) -> str | None:
        """Parse specific workout type from user text.

        Examples:
            "start strength B" -> "strength_b"
            "start cardio" -> "zone2_cardio"
            "begin workout A" -> "strength_a"
            "start zone 2" -> "zone2_cardio"
        """
        text_lower = text.lower().strip()

        # Map user terms to protocol IDs
        # Order matters - check more specific patterns first
        workout_aliases = {
            # Strength workouts (with spelled-out numbers)
            "strength a": "strength_a",
            "strength 1": "strength_a",
            "strength one": "strength_a",
            "workout a": "strength_a",
            "workout 1": "strength_a",
            "workout one": "strength_a",
            "legs": "strength_a",
            "legs and back": "strength_a",

            "strength b": "strength_b",
            "strength 2": "strength_b",
            "strength two": "strength_b",
            "strength to": "strength_b",  # Speech-to-text variant
            "strength too": "strength_b",  # Speech-to-text variant
            "workout b": "strength_b",
            "workout 2": "strength_b",
            "workout two": "strength_b",
            "workout to": "strength_b",  # Speech-to-text variant
            "shoulder rehab": "strength_b",
            "shoulders": "strength_b",
            "shoulder": "strength_b",

            "strength c": "strength_c",
            "strength 3": "strength_c",
            "strength three": "strength_c",
            "workout c": "strength_c",
            "workout 3": "strength_c",
            "workout three": "strength_c",
            "full body": "strength_c",

            # Cardio workouts - check extended FIRST (more specific)
            "extended cardio": "zone2_extended",
            "long cardio": "zone2_extended",
            "zone 2 extended": "zone2_extended",
            "zone2 extended": "zone2_extended",
            "cardio 2": "zone2_extended",
            "cardio two": "zone2_extended",
            "ruck": "zone2_extended",

            # Basic cardio (less specific, check after extended)
            "zone 2": "zone2_cardio",
            "zone2": "zone2_cardio",
            "cardio 1": "zone2_cardio",
            "cardio one": "zone2_cardio",
            "cardio": "zone2_cardio",

            # Mobility
            "active mobility": "active_mobility",
            "mobility": "active_mobility",
            "stretch": "active_mobility",
        }

        for alias, protocol_id in workout_aliases.items():
            if alias in text_lower:
                return protocol_id

        return None

    def _detect_traffic_override(self, text: str) -> str | None:
        """Detect if user is requesting a traffic light override."""
        text_lower = text.lower().strip()
        for color, patterns in TRAFFIC_OVERRIDE_PATTERNS.items():
            if any(p in text_lower for p in patterns):
                return color
        return None

    def _is_schedule_status_intent(self, text: str) -> bool:
        """Check if user wants schedule/program status."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in SCHEDULE_STATUS_PATTERNS)

    def _is_phase_start_intent(self, text: str) -> bool:
        """Check if user wants to start/restart the program phase."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in PHASE_START_PATTERNS)

    def _is_workout_ready_command(self, text: str) -> bool:
        """Check if user is ready to start set/exercise."""
        text_lower = text.lower().strip()
        # Single word matches for common commands
        if text_lower in ["ready", "start", "begin", "go"]:
            return True
        return any(p in text_lower for p in WORKOUT_READY_PATTERNS)

    def _is_workout_set_done_command(self, text: str) -> bool:
        """Check if user finished their set."""
        text_lower = text.lower().strip()
        # Single word matches
        if text_lower in ["done", "finished", "complete"]:
            return True
        return any(p in text_lower for p in WORKOUT_SET_DONE_PATTERNS)

    def _is_workout_skip_command(self, text: str) -> bool:
        """Check if user wants to skip exercise."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in WORKOUT_SKIP_PATTERNS)

    def _is_workout_stop_command(self, text: str) -> bool:
        """Check if user wants to stop workout."""
        text_lower = text.lower().strip()
        # Exclude negations: "don't stop", "can't stop", "won't stop"
        negation_patterns = ["don't stop", "dont stop", "can't stop", "cant stop", "won't stop", "wont stop", "do not stop"]
        if any(neg in text_lower for neg in negation_patterns):
            return False
        # Exact "stop" by itself
        if text_lower == "stop":
            return True
        return any(p in text_lower for p in WORKOUT_STOP_PATTERNS if p != "stop")

    def _is_workout_pause_command(self, text: str) -> bool:
        """Check if user wants to pause workout."""
        text_lower = text.lower().strip()
        # Exclude conversational phrases: "can you wait", "please wait a moment"
        if "can you wait" in text_lower or "could you wait" in text_lower:
            return False
        # Only match explicit pause commands
        # "wait" must be exact or at start (e.g., "wait", "wait a sec") not in middle of sentence
        if text_lower == "wait" or text_lower.startswith("wait ") or text_lower.startswith("wait,"):
            return True
        return any(p in text_lower for p in ["pause", "hold on", "stop timer"])

    def _is_workout_resume_command(self, text: str) -> bool:
        """Check if user wants to resume paused workout."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in ["resume", "continue", "carry on", "unpause"])

    def _is_workout_redo_command(self, text: str) -> bool:
        """Check if user wants to redo/restart current set (e.g., wrong weight)."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in [
            "redo", "go back", "wrong weight", "change weight", "wrong",
            "start over", "restart set", "too heavy", "too light"
        ])

    # ========================================
    # INTERACTIVE ROUTINE INTENT DETECTION
    # ========================================

    def _is_routine_start_intent(self, text: str) -> bool:
        """Check if user wants to start morning routine."""
        text_lower = text.lower().strip()
        # Exclude if "workout" is present - that's a workout intent, not routine
        if "workout" in text_lower or "work out" in text_lower:
            return False
        return any(p in text_lower for p in ROUTINE_START_PATTERNS)

    def _is_routine_pause_command(self, text: str) -> bool:
        """Check if user wants to pause routine."""
        text_lower = text.lower().strip()
        # Exclude conversational phrases
        if "can you wait" in text_lower or "could you wait" in text_lower:
            return False
        # "wait" must be exact or at start
        if text_lower == "wait" or text_lower.startswith("wait ") or text_lower.startswith("wait,"):
            return True
        return any(p in text_lower for p in ROUTINE_PAUSE_PATTERNS if p != "wait")

    def _is_routine_resume_command(self, text: str) -> bool:
        """Check if user wants to resume routine."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in ROUTINE_RESUME_PATTERNS)

    def _is_routine_skip_command(self, text: str) -> bool:
        """Check if user wants to skip exercise."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in ROUTINE_SKIP_PATTERNS)

    def _is_routine_stop_command(self, text: str) -> bool:
        """Check if user wants to stop routine."""
        text_lower = text.lower().strip()
        # Exclude negations: "don't stop", "can't stop", "won't stop"
        negation_patterns = ["don't stop", "dont stop", "can't stop", "cant stop", "won't stop", "wont stop", "do not stop"]
        if any(neg in text_lower for neg in negation_patterns):
            return False
        # "stop" alone should stop routine when active
        if text_lower == "stop":
            return True
        return any(p in text_lower for p in ROUTINE_STOP_PATTERNS if p != "stop")

    def _is_routine_form_request(self, text: str) -> bool:
        """Check if user is asking for form/setup help."""
        text_lower = text.lower().strip()
        for pattern in ROUTINE_FORM_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _is_routine_ready_command(self, text: str) -> bool:
        """Check if user is ready to start exercise timer."""
        text_lower = text.lower().strip()
        # Single word matches
        if text_lower in ["ready", "begin", "go", "start"]:
            return True
        return any(p in text_lower for p in ROUTINE_READY_PATTERNS)

    def _is_routine_complete_command(self, text: str) -> bool:
        """Check if user is saying routine is complete."""
        text_lower = text.lower().strip()
        # Single word matches
        if text_lower in ["finished", "complete", "done"]:
            return True
        return any(p in text_lower for p in ROUTINE_COMPLETE_PATTERNS)

    def _is_routine_last_exercise(self) -> bool:
        """Check if current exercise is the last one in the routine."""
        if not hasattr(self, '_routine_sections') or not self._routine_sections:
            return True
        # Check if we're on the last section
        if self.routine.section_idx >= len(self._routine_sections) - 1:
            # Check if we're on the last exercise of that section
            current_section = self._routine_sections[self.routine.section_idx]
            if self.routine.exercise_idx >= len(current_section.exercises) - 1:
                return True
        return False

    # ========================================
    # SENECA TRIAL (REFLECTION) INTENT DETECTION
    # ========================================

    def _is_reflection_start_intent(self, text: str) -> bool:
        """Check if user wants to start a reflection."""
        text_lower = text.lower().strip()
        # Check both full and quick triggers
        all_triggers = REFLECTION_TRIGGERS + QUICK_REFLECTION_TRIGGERS
        return any(t in text_lower for t in all_triggers)

    def _is_quick_reflection_intent(self, text: str) -> bool:
        """Check if user wants quick reflection mode."""
        text_lower = text.lower().strip()
        return any(t in text_lower for t in QUICK_REFLECTION_TRIGGERS)

    def _is_reflection_active(self) -> bool:
        """Check if a reflection session is currently active."""
        from atlas.health.seneca_runner import get_seneca_runner
        runner = get_seneca_runner()
        return runner.is_active

    async def _start_reflection(self, is_quick: bool = False) -> str:
        """Start a Seneca Trial reflection session."""
        from atlas.health.seneca_runner import get_seneca_runner
        runner = get_seneca_runner()

        if is_quick:
            return runner.start_quick()
        else:
            return runner.start()

    async def _handle_reflection_input(self, text: str) -> str:
        """Handle user input during active reflection."""
        from atlas.health.seneca_runner import get_seneca_runner
        runner = get_seneca_runner()

        # Check for skip/cancel commands
        text_lower = text.lower().strip()
        if text_lower in ["skip", "next"]:
            return runner.handle_skip()
        if text_lower in ["cancel", "stop", "quit"]:
            return runner.cancel()

        # Process the response
        return runner.handle_input(text)

    # ========================================
    # INTERACTIVE WORKOUT HANDLERS
    # ========================================

    def _setup_next_exercise(self):
        """Set up current exercise from the exercise list."""
        if self.workout.exercise_idx < len(self.workout.exercises):
            ex = self.workout.exercises[self.workout.exercise_idx]
            logger.info(f"[SETUP-DIAG] Raw exercise object: {ex}")
            logger.info(f"[SETUP-DIAG] ex.duration_seconds={getattr(ex, 'duration_seconds', 'MISSING')}, ex.reps={getattr(ex, 'reps', 'MISSING')}, ex.per_side={getattr(ex, 'per_side', 'MISSING')}")

            # Check if this is a cardio/continuous session (has duration_minutes, no reps)
            duration_minutes = getattr(ex, 'duration_minutes', None)
            is_continuous_session = duration_minutes is not None and ex.reps is None

            # Convert WorkoutExercise to dict for easier access
            self.workout.current_exercise = {
                'id': getattr(ex, 'id', ex.name.lower().replace(' ', '_')),
                'name': ex.name,
                'sets': 1 if is_continuous_session else ex.sets,  # Cardio = 1 continuous session
                'reps': ex.reps,
                'duration_seconds': ex.duration_seconds,
                'duration_minutes': duration_minutes,  # For cardio workouts
                'rest_seconds': ex.rest_seconds,
                'notes': ex.notes,
                'per_side': getattr(ex, 'per_side', False),
                'hold_seconds': getattr(ex, 'hold_seconds', None),
                'per_direction': getattr(ex, 'per_direction', False),
                'distance_steps': getattr(ex, 'distance_steps', None),
                'is_continuous': is_continuous_session,  # Flag for cardio handling
            }
            logger.info(f"[SETUP-DIAG] Converted exercise dict: {self.workout.current_exercise}")

    async def _start_interactive_workout(
        self,
        traffic_override: str | None = None,
        protocol_id: str | None = None
    ) -> str:
        """Start interactive workout session.

        Args:
            traffic_override: Optional traffic light override ("GREEN", "YELLOW", "RED")
            protocol_id: Optional specific protocol to start (e.g., "strength_b")
                        If not provided, uses scheduler to determine next workout.
        """
        from atlas.health.workout_runner import get_todays_protocol, load_protocols
        from atlas.health.morning_sync import load_cached_status
        from atlas.health.router import TrafficLightStatus

        # If specific protocol requested, use it directly
        if protocol_id:
            protocols = load_protocols()
            protocol = protocols.get(protocol_id)
            if not protocol:
                return f"Unknown workout: {protocol_id}. Try strength a, strength b, strength c, cardio, or mobility."

            # Get program info for display
            scheduled = self.workout_scheduler.get_next_workout()
            program_week = scheduled.program_week if scheduled else 1
            program_day = scheduled.program_day if scheduled else 1
            catch_up_msg = ""
            day_msg = f"Week {program_week}, Day {program_day}. "
        else:
            # Check scheduler for which workout to do (handles missed days)
            scheduled = self.workout_scheduler.get_next_workout()

            # Already done today
            if scheduled.protocol_id == "already_done":
                return scheduled.protocol_name

            # Rest day - don't start interactive workout
            if scheduled.protocol_id == "recovery":
                return f"Today is a recovery day. No workout scheduled. Rest, stretch, or go for a light walk. Say schedule status for your week overview."

            # No phase started - prompt user to start program
            if scheduled.protocol_id == "no_phase":
                return f"No program started yet. Today would be {scheduled.protocol_name}. Say 'start program' to begin Phase 1 from today."

            # Use scheduled workout
            protocol_id = scheduled.protocol_id
            protocols = load_protocols()
            protocol = protocols.get(protocol_id)

            # Build catch-up message if applicable
            catch_up_msg = ""
            if scheduled.is_catch_up:
                catch_up_msg = f"Catching up from {scheduled.scheduled_day}. "

            # Program day info
            day_msg = f"Week {scheduled.program_week}, Day {scheduled.program_day}. "

        # Get traffic light status (use override if provided)
        status = load_cached_status()
        if traffic_override:
            traffic_str = traffic_override
            override_msg = f"Override to {traffic_str}. "
        else:
            traffic_str = status.get("traffic_light", "GREEN") if status else "GREEN"
            override_msg = ""

        try:
            traffic_light = TrafficLightStatus[traffic_str]
        except KeyError:
            traffic_light = TrafficLightStatus.GREEN

        # RED day overrides to red_day protocol (unless specific protocol was requested)
        if traffic_light == TrafficLightStatus.RED and not protocol_id:
            protocol = load_protocols().get("red_day")

        if not protocol:
            return "No workout scheduled for today."

        if not protocol.exercises:
            return "Workout has no exercises configured."

        try:
            # Clean up all routine state (user transitioning from routine to workout)
            # Note: Always clear these flags unconditionally to prevent stale state
            # from blocking workout handlers (e.g., START_TIMER, SKIP_EXERCISE)
            self.routine.active = False
            self.routine.paused = False
            self.routine.exercise_pending = False
            self.routine.timer_active = False
            self.routine.timer_start = None
            self.routine.current_exercise = None
            self.routine.current_section = None
            # Clear auto-advance state that could block workout handlers
            self.routine.auto_advance_pending = False
            self.routine.auto_advance_start = None
            self.routine.auto_advance_phase = None

            # Initialize workout state
            self.workout.active = True
            self.workout.protocol = protocol
            self.workout.exercise_idx = 0
            self.workout.current_set = 0
            self.workout.current_weight = None
            self.workout.exercises = list(protocol.exercises)
            logger.info(f"[START-DIAG] Loaded {len(self.workout.exercises)} exercises from protocol '{protocol.name}'")
            for i, ex in enumerate(self.workout.exercises):
                logger.info(f"[START-DIAG] Exercise {i}: {ex.name}, duration_seconds={ex.duration_seconds}, reps={ex.reps}, per_side={ex.per_side}")
            self.workout.log = []
            self.workout.rest_active = False
            self.workout.set_active = False
            self.workout.beeps_played = set()  # Reset beeps for new workout
            self.workout.awaiting_reps = False
            self.workout.set_reps = []
            # Reset exercise timer state
            self.workout.exercise_timer_active = False
            self.workout.exercise_timer_start = None
            self.workout.exercise_timer_duration = 0
            self.workout.exercise_current_side = None
            self.workout.exercise_sides_done = 0
            self.workout.exercise_beeps_played = set()
            self.workout.last_set_of_timed_exercise = False

            # Announce workout with day info, override, and catch-up messages
            response = f"{day_msg}{catch_up_msg}{override_msg}{protocol.name}. {protocol.duration_minutes} minutes. "
            if protocol.goal:
                response += f"{protocol.goal}. "

            # Set up first exercise
            self._setup_next_exercise()
            ex = self.workout.current_exercise
            if ex:
                # Handle cardio/continuous sessions differently
                if ex.get('is_continuous'):
                    duration_mins = ex.get('duration_minutes', 50)
                    response += f"First exercise: {ex['name']}. {duration_mins} minutes continuous. "
                    if ex.get('notes'):
                        response += f"{ex['notes']} "
                    response += "Say ready to begin, done when finished."
                else:
                    response += f"First exercise: {ex['name']}. {ex['sets']} sets"
                    if ex.get('reps'):
                        response += f" of {ex['reps']}"
                        if ex.get('per_side'):
                            response += " each side"
                    elif ex.get('duration_seconds'):
                        response += f" for {ex['duration_seconds']} seconds"
                        if ex.get('per_side'):
                            response += " each side"
                        else:
                            response += " each"
                    if ex.get('per_direction'):
                        response += " each direction"
                    if ex.get('hold_seconds'):
                        response += f". Hold {ex['hold_seconds']} seconds each rep"
                    response += ". Say ready when set up."
                self.workout.exercise_pending = True

            return response

        except Exception as e:
            # Clean up state on failure
            self.workout.active = False
            self.workout.rest_active = False
            self.workout.set_active = False
            self.workout.exercise_pending = False
            raise

    async def _handle_workout_ready(self, text: str) -> str:
        """User said ready - check for weight or start the set."""
        logger.info(f"[READY-DIAG] _handle_workout_ready called with text='{text}'")

        if not self.workout.active:
            logger.warning("[READY-DIAG] No workout active - returning early")
            return "No workout in progress."

        ex = self.workout.current_exercise
        logger.info(f"[READY-DIAG] Current exercise object: {ex}")

        if not ex:
            logger.warning("[READY-DIAG] No current exercise - returning early")
            return "No current exercise."

        # Log all relevant exercise fields for diagnostics
        logger.info(f"[READY-DIAG] Exercise fields: reps={ex.get('reps')}, duration_seconds={ex.get('duration_seconds')}, per_side={ex.get('per_side')}")
        logger.info(f"[READY-DIAG] Current state: set={self.workout.current_set}, weight={self.workout.current_weight}")

        # If exercise needs weight tracking (has reps), check for weight in text
        has_reps = ex.get('reps')
        logger.info(f"[READY-DIAG] has_reps={has_reps}, _workout_current_weight={self.workout.current_weight}")

        # Check if this exercise needs weight tracking
        # RPE-based exercises (light weight, bodyweight, etc.) don't need weight input
        notes = ex.get('notes', '').lower()
        is_rpe_based = any(hint in notes for hint in [
            'light weight', 'bodyweight', 'use light', 'rpe', 'no weight',
            '1-2kg', '2-3kg', 'band only', 'own bodyweight'
        ])
        needs_weight = has_reps and not is_rpe_based and ex.get('track_weight', True)
        logger.info(f"[READY-DIAG] Weight check: has_reps={has_reps}, is_rpe_based={is_rpe_based}, needs_weight={needs_weight}")

        if needs_weight and not self.workout.current_weight:
            logger.info("[READY-DIAG] Taking WEIGHT CHECK path (has reps, needs weight, no weight set)")
            # Try to parse weight from "ready, 30 kilos" or "30kg"
            from atlas.voice.number_parser import parse_weight_value
            weight = parse_weight_value(text)
            if weight:
                self.workout.current_weight = weight
                logger.info(f"[READY-DIAG] Parsed weight from text: {weight}")
            else:
                # First set - get progression recommendation
                if self.workout.current_set == 0:
                    logger.info("[READY-DIAG] First set, getting progression recommendation")
                    exercise_id = ex.get('id', ex.get('name', '')).lower().replace(' ', '_')
                    try:
                        rec = self.progression_service.get_recommendation(exercise_id)
                        voice_prompt = self.progression_service.format_voice_recommendation(rec)
                        if voice_prompt:
                            # Set the recommended weight so next "ready" proceeds
                            if rec.recommended_weight_kg:
                                self.workout.current_weight = rec.recommended_weight_kg
                                logger.info(f"[READY-DIAG] Set recommended weight: {rec.recommended_weight_kg}")
                            logger.info(f"[READY-DIAG] Returning progression prompt: {voice_prompt}")
                            return voice_prompt
                    except Exception as e:
                        logger.warning(f"Progression recommendation failed: {e}")
                    logger.info("[READY-DIAG] Returning 'What weight are you using?'")
                    return "What weight are you using?"
        else:
            logger.info(f"[READY-DIAG] SKIPPING weight check (has_reps={has_reps}, weight={self.workout.current_weight})")

        # Handle continuous/cardio sessions differently
        if ex.get('is_continuous'):
            logger.info("[READY-DIAG] CONTINUOUS SESSION DETECTED - starting session")
            self.workout.current_set = 1
            self.workout.set_active = True
            self.workout.exercise_pending = False
            duration_mins = ex.get('duration_minutes', 50)

            # Play START beep
            try:
                from atlas.voice.audio_utils import chime_timer_start
                chime_timer_start()
            except Exception as e:
                logger.warning(f"Timer start beep failed: {e}")

            notes = ex.get('notes', '')
            # Don't truncate notes for voice - they're important instructions
            note_str = f" {notes}" if notes else ""
            return f"{duration_mins} minutes. Begin.{note_str} Say done when finished."

        self.workout.current_set += 1
        self.workout.set_active = True
        self.workout.exercise_pending = False
        self.workout.total_sets = ex.get('sets', 3)
        logger.info(f"[READY-DIAG] Set incremented to {self.workout.current_set}, set_active=True")

        # Check if this is a timed exercise (has duration_seconds instead of reps)
        duration = ex.get('duration_seconds')
        is_per_side = ex.get('per_side', False)
        logger.info(f"[READY-DIAG] Checking timed exercise: duration={duration}, is_per_side={is_per_side}")

        if duration:
            logger.info(f"[READY-DIAG] TIMED EXERCISE DETECTED - starting timer for {duration}s")
            # Start exercise timer for timed holds (like balance exercises)
            self.workout.exercise_timer_active = True
            self.workout.exercise_timer_start = time.monotonic()
            self.workout.exercise_timer_duration = duration
            self.workout.exercise_beeps_played = set()

            # Play START beep to signal timer has begun
            try:
                from atlas.voice.audio_utils import chime_timer_start
                chime_timer_start()
            except Exception as e:
                logger.warning(f"Timer start beep failed: {e}")

            if is_per_side:
                self.workout.exercise_current_side = 'left'
                self.workout.exercise_sides_done = 0
                response = f"Set {self.workout.current_set}. Left side. {duration} seconds. Begin."
                logger.info(f"[READY-DIAG] Returning TIMED per-side response: {response}")
                return response
            else:
                self.workout.exercise_current_side = None
                self.workout.exercise_sides_done = 0
                response = f"Set {self.workout.current_set}. {duration} seconds. Begin."
                logger.info(f"[READY-DIAG] Returning TIMED response: {response}")
                return response
        else:
            logger.info("[READY-DIAG] Not a timed exercise (no duration_seconds)")

        # Rep-based exercise
        weight_str = f" at {int(self.workout.current_weight)} kilos" if self.workout.current_weight else ""
        response = f"Set {self.workout.current_set}{weight_str}. Begin."
        logger.info(f"[READY-DIAG] Returning REP-BASED response: {response}")
        return response

    async def _handle_workout_set_done(self, text: str = "") -> str:
        """User finished a set."""
        if not self.workout.active or not self.workout.set_active:
            return "No active set."

        self.workout.set_active = False
        ex = self.workout.current_exercise

        if not ex:
            return "No current exercise."

        # Handle continuous/cardio sessions - just advance when done
        if ex.get('is_continuous'):
            return await self._advance_to_next_exercise()

        # If awaiting AMRAP reps, try to parse from text
        if self.workout.awaiting_reps:
            self.workout.awaiting_reps = False
            from atlas.voice.number_parser import parse_spoken_number
            reps = parse_spoken_number(text)
            if reps:
                self.workout.set_reps.append(int(reps))
            else:
                # Default to target reps if not provided
                target_reps = ex.get('reps', 10)
                if isinstance(target_reps, str) and '-' in target_reps:
                    target_reps = int(target_reps.split('-')[0])
                self.workout.set_reps.append(int(target_reps))
            return await self._advance_to_next_exercise()

        # Track reps for this set (only for rep-based exercises)
        # Check both duration_seconds AND duration_minutes (cardio uses minutes)
        is_timed_exercise = ex.get('duration_seconds') is not None or ex.get('duration_minutes') is not None
        if not is_timed_exercise and ex.get('reps') is not None:
            target_reps = ex.get('reps')
            if isinstance(target_reps, str) and '-' in target_reps:
                target_reps = int(target_reps.split('-')[0])
            self.workout.set_reps.append(int(target_reps))

        # Check if more sets
        if self.workout.current_set < ex['sets']:
            # Start rest timer
            rest_seconds = ex.get('rest_seconds', 60 if is_timed_exercise else 90)
            self.workout.rest_active = True
            self.workout.rest_start = time.monotonic()
            self.workout.rest_duration = rest_seconds
            self.workout.beeps_played = set()

            return f"Set {self.workout.current_set} complete. Rest {rest_seconds} seconds."
        else:
            # Final set - ask for AMRAP reps (only for rep-based exercises)
            if ex.get('reps') and not is_timed_exercise:
                self.workout.awaiting_reps = True
                # Pop the assumed reps we just added - we'll get the real number
                if self.workout.set_reps:
                    self.workout.set_reps.pop()
                return "Last set. How many reps?"
            else:
                # Timed exercise - no AMRAP
                return await self._advance_to_next_exercise()

    async def _advance_to_next_exercise(self) -> str:
        """Move to next exercise or finish workout."""
        # Log completed exercise with set-level reps
        if self.workout.current_exercise:
            exercise_entry = {
                "id": self.workout.current_exercise.get('id', ''),
                "name": self.workout.current_exercise['name'],
                "sets": self.workout.current_set,
                "reps": self.workout.set_reps.copy() if self.workout.set_reps else None,
                "weight": self.workout.current_weight,
            }
            self.workout.log.append(exercise_entry)

            # Log to progression service if we have meaningful data
            if self.workout.current_weight and self.workout.set_reps:
                try:
                    exercise_id = self.workout.current_exercise.get('id', '').lower().replace(' ', '_')
                    avg_reps = sum(self.workout.set_reps) / len(self.workout.set_reps)
                    self.progression_service.log_progression(
                        exercise_id=exercise_id,
                        recommended_weight=None,  # We didn't track what was recommended
                        actual_weight=self.workout.current_weight,
                        actual_reps_avg=avg_reps,
                        basis="workout_session",
                    )
                except Exception as e:
                    logger.warning(f"Failed to log progression: {e}")

        self.workout.exercise_idx += 1
        self.workout.set_reps = []  # Reset reps tracking for next exercise

        if self.workout.exercise_idx >= len(self.workout.exercises):
            # Workout complete - generate summary
            self.workout.active = False
            self.workout.rest_active = False
            self.workout.set_active = False
            self.workout.exercise_pending = False
            exercises_done = len(self.workout.log)

            # Generate progression summary
            try:
                summary = self.progression_service.get_workout_summary(self.workout.log)
                return f"Workout complete! {exercises_done} exercises. {summary} Say finished workout to log it."
            except Exception as e:
                logger.warning(f"Failed to generate workout summary: {e}")
                return f"Workout complete! {exercises_done} exercises done. Say finished workout to log it."

        # Reset for next exercise
        self._setup_next_exercise()
        self.workout.current_set = 0
        self.workout.current_weight = None  # Reset weight for new exercise
        self.workout.rest_active = False

        ex = self.workout.current_exercise

        # Bounds check - if exercise setup failed, treat as workout complete
        if not ex:
            self.workout.active = False
            return "Workout complete! Say finished workout to log it."

        # Handle cardio/continuous sessions differently
        if ex.get('is_continuous'):
            duration_mins = ex.get('duration_minutes', 50)
            response = f"Next: {ex['name']}. {duration_mins} minutes continuous. "
            if ex.get('notes'):
                response += f"{ex['notes']} "
            response += "Say ready to begin, done when finished."
        else:
            response = f"Next: {ex['name']}. {ex['sets']} sets"
            if ex.get('reps'):
                response += f" of {ex['reps']}"
                if ex.get('per_side'):
                    response += " each side"
            elif ex.get('duration_seconds'):
                response += f" for {ex['duration_seconds']} seconds"
                if ex.get('per_side'):
                    response += " each side"
                else:
                    response += " each"
            if ex.get('per_direction'):
                response += " each direction"
            if ex.get('hold_seconds'):
                response += f". Hold {ex['hold_seconds']} seconds each rep"
            if ex.get('notes'):
                # Notes are curated form cues - don't truncate
                response += f". {ex['notes']}"
            response += ". Say ready when set up."

        self.workout.exercise_pending = True
        return response

    async def _handle_workout_skip(self) -> str:
        """Skip current exercise."""
        if not self.workout.active:
            return "No workout in progress."

        ex_name = self.workout.current_exercise['name'] if self.workout.current_exercise else "exercise"

        # Reset all exercise-specific state (timer, sides, etc.)
        self.workout.rest_active = False
        self.workout.rest_start = None  # Reset rest timer timestamp
        self.workout.set_active = False
        self.workout.exercise_pending = False  # Reset pending flag
        self.workout.exercise_timer_active = False
        self.workout.exercise_timer_start = None
        self.workout.beeps_played = set()  # Reset rest timer beeps for next exercise
        self.workout.exercise_beeps_played = set()
        self.workout.exercise_sides_done = 0
        self.workout.exercise_current_side = None
        self.workout.awaiting_reps = False
        self.workout.last_set_of_timed_exercise = False  # Reset last set flag

        response = f"Skipping {ex_name}. "
        response += await self._advance_to_next_exercise()
        return response

    async def _handle_workout_stop(self) -> str:
        """Stop workout - show COMPLETE screen for logging."""
        exercises_done = len(self.workout.log)
        ex = self.workout.current_exercise
        ex_name = ex.get('name', 'workout') if ex else 'workout'

        logger.info(f"[WORKOUT-STOP] Stopping workout at {ex_name}, {exercises_done} exercises completed")

        # Stop all timers but keep log for COMPLETE screen
        self.workout.rest_active = False
        self.workout.rest_start = None
        self.workout.exercise_timer_active = False
        self.workout.exercise_timer_start = None
        self.workout.exercise_pending = False
        self.workout.set_active = False
        self.workout.awaiting_reps = False
        self.workout.paused = False

        # Set workout_finished to show COMPLETE screen
        self.workout.workout_finished = True
        self.workout.exercises_completed = exercises_done
        # Keep active=False so normal intent routing works
        self.workout.active = False

        logger.info("[WORKOUT-STOP] Set workout_finished - showing COMPLETE screen")

        return f"Workout complete. {exercises_done} exercises done. Press COMPLETE or say finished workout to log."

    async def _handle_workout_pause(self) -> str:
        """Pause workout (any state)."""
        if self.workout.pause_in_progress:
            return "Already pausing."
        self.workout.pause_in_progress = True

        try:
            self.workout.paused = True

            # Store remaining time for whichever timer is active
            if self.workout.rest_active and self.workout.rest_start:
                elapsed = time.monotonic() - self.workout.rest_start
                self.workout.timer_remaining = max(0, int(self.workout.rest_duration - elapsed))
                context = f"rest, {self.workout.timer_remaining} seconds left"
            elif self.workout.exercise_timer_active and self.workout.exercise_timer_start:
                elapsed = time.monotonic() - self.workout.exercise_timer_start
                self.workout.timer_remaining = max(0, int(self.workout.exercise_timer_duration - elapsed))
                ex = self.workout.current_exercise
                ex_name = ex.get('name', 'exercise') if ex else 'exercise'
                context = f"{ex_name}, {self.workout.timer_remaining} seconds left"
            elif self.workout.set_active:
                context = f"set {self.workout.current_set}"
                self.workout.timer_remaining = 0
            else:
                context = "workout"
                self.workout.timer_remaining = 0

            ex = self.workout.current_exercise
            ex_name = ex.get('name', 'Exercise') if ex else 'Exercise'
            return f"Paused. {ex_name}, {context}. Say resume to continue."
        finally:
            self.workout.pause_in_progress = False

    async def _handle_workout_resume(self) -> str:
        """Resume workout from pause."""
        if not self.workout.paused:
            return "Workout not paused."

        self.workout.paused = False
        remaining = self.workout.timer_remaining

        # Restart the appropriate timer
        if self.workout.rest_active and remaining > 0:
            elapsed_before_pause = self.workout.rest_duration - remaining
            self.workout.rest_start = time.monotonic() - elapsed_before_pause
            return f"Resuming rest. {remaining} seconds."
        elif self.workout.exercise_timer_active and remaining > 0:
            elapsed_before_pause = self.workout.exercise_timer_duration - remaining
            self.workout.exercise_timer_start = time.monotonic() - elapsed_before_pause
            return f"Resuming. {remaining} seconds."
        else:
            return "Resuming workout."

    async def _handle_workout_redo_set(self, text: str) -> str:
        """Redo current set - reset to pending state for weight correction."""
        ex = self.workout.current_exercise
        if not ex:
            return "No exercise in progress."

        # Stop any active timers
        self.workout.exercise_timer_active = False
        self.workout.exercise_timer_start = None
        self.workout.exercise_beeps_played = set()
        self.workout.exercise_sides_done = 0
        self.workout.exercise_current_side = None

        # Reset set state back to pending
        self.workout.set_active = False
        self.workout.exercise_pending = True

        # Decrement set counter (we're redoing this set)
        if self.workout.current_set > 0:
            self.workout.current_set -= 1

        # Check if user provided a new weight in the same utterance
        from atlas.voice.number_parser import parse_weight_value
        new_weight = parse_weight_value(text)
        if new_weight:
            self.workout.current_weight = new_weight
            return f"Got it. {int(new_weight)} kilos. Say ready to begin set {self.workout.current_set + 1}."
        else:
            # Clear weight so they can provide a new one
            self.workout.current_weight = None
            return f"Set reset. What weight for {ex.get('name', 'this exercise')}?"

    def _force_reset_workout_state(self):
        """Force reset all workout state (for error recovery)."""
        logger.debug("FORCE_RESET: Clearing all workout state")
        self.workout.reset()
        logger.info("[WORKOUT] Force reset all state")
        # Clear timer from session status
        self._clear_timer_from_session_status()

    # ========================================
    # SCHEDULE/PHASE HANDLERS
    # ========================================

    async def _handle_schedule_status(self) -> str:
        """Get program schedule status."""
        return self.workout_scheduler.format_status_voice()

    def _is_reset_pattern(self, text: str) -> bool:
        """Check if this is a reset pattern (needs confirmation)."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in PHASE_RESET_PATTERNS)

    async def _handle_phase_start_request(self, original_text: str = "") -> str:
        """Request to start/reset program phase - requires confirmation for resets."""
        status = self.workout_scheduler.get_status()

        if status.get("phase_started"):
            # Already have a phase - check if this is a reset pattern
            if self._is_reset_pattern(original_text):
                # Explicit reset request - ask for confirmation
                completed = status.get("workouts_completed", 0)
                week = status.get("program_week", 1)
                self._phase_reset_pending = True
                self._phase_reset_time = time.time()
                return f"You're on Week {week} with {completed} workouts logged. Reset to Day 1? Say confirm to reset, or cancel."
            else:
                # Just saying "start program" but already have one
                return f"Program already running. Week {status.get('program_week', 1)}, Day {status.get('program_day', 1)}. Say 'reset my program' to start over."
        else:
            # No phase yet - just start it (no confirmation needed)
            return await self._handle_phase_confirm()

    async def _handle_phase_confirm(self) -> str:
        """Confirm phase reset."""
        from datetime import date
        self._phase_reset_pending = False
        self._phase_reset_time = None
        self.workout_scheduler.start_phase("phase_1", date.today())
        status = self.workout_scheduler.get_status()
        return f"Phase 1 started. Day 1, Week 1. Today: {status['next_workout']}. Say start workout when ready."

    async def _handle_phase_cancel(self) -> str:
        """Cancel phase reset."""
        self._phase_reset_pending = False
        self._phase_reset_time = None
        status = self.workout_scheduler.get_status()
        return f"Reset cancelled. Still on Week {status.get('program_week', 1)}, Day {status.get('program_day', 1)}."

    def _is_phase_confirm_command(self, text: str) -> bool:
        """Check if user is confirming phase reset."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in PHASE_CONFIRM_PATTERNS)

    def _is_cancel_command(self, text: str) -> bool:
        """Check if user is cancelling."""
        text_lower = text.lower().strip()
        return any(w in text_lower for w in ["cancel", "no", "nevermind", "never mind", "stop", "abort"])

    def _check_workout_rest_timer(self) -> tuple[str | None, list[int]]:
        """
        Check workout rest timer status.

        Returns:
            (message, beeps_to_play) - message if timer ended, list of beep points hit (only 5s beep)
        """
        if not self.workout.rest_active or not self.workout.rest_start:
            return None, []

        elapsed = time.monotonic() - self.workout.rest_start
        remaining = self.workout.rest_duration - elapsed

        # Only beep at 5 seconds remaining (not 30/15)
        new_beeps = []
        if remaining <= 5 and 5 not in self.workout.beeps_played:
            self.workout.beeps_played.add(5)
            new_beeps.append(5)

        # Check if rest timer finished
        if elapsed >= self.workout.rest_duration:
            # Play REST DONE triple ascending beep
            try:
                from atlas.voice.audio_utils import chime_rest_done
                chime_rest_done()
            except Exception as e:
                logger.warning(f"Rest done chime failed: {e}")

            self.workout.rest_active = False
            # Don't increment set here - _handle_workout_ready() does that
            self.workout.set_active = False
            self.workout.exercise_pending = True  # Wait for ready
            next_set = self.workout.current_set + 1
            return f"Rest done. Set {next_set}. Say ready when you're set.", []

        return None, new_beeps

    def _get_workout_rest_remaining(self) -> int:
        """Get remaining rest time in seconds."""
        if not self.workout.rest_active or not self.workout.rest_start:
            return 0
        elapsed = time.monotonic() - self.workout.rest_start
        return max(0, int(self.workout.rest_duration - elapsed))

    def _check_workout_exercise_timer(self) -> tuple[str | None, list[int]]:
        """
        Check workout exercise timer status (for timed holds).

        Returns:
            (message, beeps_to_play) - message if timer event, empty list (no countdown beeps for exercises)
        """
        if not self.workout.exercise_timer_active or not self.workout.exercise_timer_start:
            return None, []

        elapsed = time.monotonic() - self.workout.exercise_timer_start

        # No countdown beeps during timed exercises - only sounds on completion/switch

        # Check if timer finished for current side/exercise
        if elapsed >= self.workout.exercise_timer_duration:
            ex = self.workout.current_exercise
            is_per_side = ex.get('per_side', False) if ex else False

            if is_per_side and self.workout.exercise_sides_done == 0:
                # First side done - play SIDE SWITCH double beep
                try:
                    from atlas.voice.audio_utils import chime_side_switch
                    chime_side_switch()
                except Exception as e:
                    logger.warning(f"Side switch chime failed: {e}")

                # Switch to other side
                self.workout.exercise_sides_done = 1
                self.workout.exercise_current_side = 'right'
                self.workout.exercise_timer_start = time.monotonic()
                self.workout.exercise_beeps_played = set()
                return "Switch sides. Right leg. Begin.", []
            else:
                # Both sides done (or non-per_side exercise) - play SET COMPLETE chime
                try:
                    from atlas.voice.audio_utils import chime_exercise_complete
                    chime_exercise_complete()
                except Exception as e:
                    logger.warning(f"Set complete chime failed: {e}")

                self.workout.exercise_timer_active = False
                self.workout.exercise_sides_done = 0
                self.workout.exercise_current_side = None
                self.workout.set_active = False

                # Check if more sets remain
                total_sets = ex.get('sets', 3) if ex else 3
                if self.workout.current_set < total_sets:
                    rest_seconds = ex.get('rest_seconds', 60) if ex else 60

                    if rest_seconds == 0:
                        # NO REST - immediately start next set (balance exercises)
                        self.workout.current_set += 1
                        self.workout.set_active = True
                        self.workout.exercise_timer_active = True
                        self.workout.exercise_timer_start = time.monotonic()
                        self.workout.exercise_beeps_played = set()

                        # Play start beep for new set
                        try:
                            from atlas.voice.audio_utils import chime_timer_start
                            chime_timer_start()
                        except Exception as e:
                            logger.warning(f"Timer start beep failed: {e}")

                        if ex.get('per_side', False):
                            self.workout.exercise_current_side = 'left'
                            self.workout.exercise_sides_done = 0
                            return f"Set {self.workout.current_set}. Left side. Begin.", []
                        else:
                            return f"Set {self.workout.current_set}. Begin.", []
                    else:
                        # Start rest timer
                        self.workout.rest_active = True
                        self.workout.rest_start = time.monotonic()
                        self.workout.rest_duration = rest_seconds
                        self.workout.beeps_played = set()
                        return f"Set {self.workout.current_set} complete. Rest {rest_seconds} seconds.", []
                else:
                    # Last set done - move to next exercise
                    self.workout.exercise_pending = False
                    # Note: We don't call _advance_to_next_exercise() here since it's async
                    # Instead, set a flag for the main loop to handle
                    self.workout.last_set_of_timed_exercise = True
                    return "Last set complete. Moving to next exercise.", []

        return None, []

    def _get_workout_exercise_time_remaining(self) -> int:
        """Get remaining time for current timed exercise in seconds."""
        if not self.workout.exercise_timer_active or not self.workout.exercise_timer_start:
            return 0
        elapsed = time.monotonic() - self.workout.exercise_timer_start
        return max(0, int(self.workout.exercise_timer_duration - elapsed))

    async def _handle_workout_completion(self, text: str, has_issues: bool) -> str:
        """Handle workout completion logging."""
        from atlas.health.workout_lookup import get_todays_workout

        # Always get scheduled for context, but prefer _workout_protocol for accuracy
        scheduled = get_todays_workout()

        # Guard: require workout context (active, logged, finished, or scheduled) before logging
        # This prevents "log it" from triggering without any workout context
        has_workout_context = (
            self.workout.protocol is not None or
            self.workout.log or
            self.workout.active or
            self.workout.workout_finished or
            scheduled is not None
        )
        if not has_workout_context:
            return "No workout to log. Start a workout first with 'start workout'."

        # Use the actual workout that was running if available (interactive session)
        if self.workout.protocol:
            expected_duration = self.workout.protocol.duration_minutes
            expected_type = getattr(self.workout.protocol, 'type', 'STRENGTH_A').upper()
            workout_name = self.workout.protocol.name
            # Map protocol id to workout type
            protocol_id = getattr(self.workout.protocol, 'id', '')
            if protocol_id:
                type_mapping = {
                    "strength_a": "STRENGTH_A",
                    "strength_b": "STRENGTH_B",
                    "strength_c": "STRENGTH_C",
                    "zone2_cardio": "CARDIO_ZONE2",
                    "zone2_extended": "ZONE2_EXTENDED",
                    "active_mobility": "ACTIVE_MOBILITY",
                    "recovery": "RECOVERY",
                }
                expected_type = type_mapping.get(protocol_id, expected_type)
        elif scheduled:
            # Fallback to scheduled workout (non-interactive completion)
            expected_duration = scheduled.get("duration_minutes", 45)
            expected_type = scheduled.get("type", "STRENGTH_A")
            workout_name = scheduled.get("name", "Workout")
        else:
            expected_duration = 45
            expected_type = "UNKNOWN"
            workout_name = "Workout"

        # Extract duration if mentioned
        duration = None
        duration_match = re.search(r'(\d+)\s*(min|minutes?|mins?)', text.lower())
        if duration_match:
            duration = int(duration_match.group(1))

        # If issues mentioned, store pending and ask for details
        if has_issues:
            self._pending_workout = {
                "scheduled": scheduled,
                "mentioned_issues": text,
                "duration": duration,
                "created_at": time.time(),
            }
            return "Got it. What did you skip or modify? Any notes?"

        # Check for duration mismatch (>15 min difference)
        if duration and abs(duration - expected_duration) > 15:
            self._pending_workout = {
                "scheduled": scheduled,
                "duration": duration,
                "created_at": time.time(),
            }
            return f"You logged {duration} minutes, but {workout_name} is usually {expected_duration}. Confirm or add notes?"

        # Standard completion - log directly
        if not duration:
            duration = expected_duration

        # Log the workout with exercise data from interactive session
        try:
            from atlas.health.workout import WorkoutService
            from atlas.memory.blueprint import get_blueprint_api, WorkoutExerciseSet

            service = WorkoutService()

            # Build exercises list from _workout_log if available (interactive session)
            exercises = None
            if self.workout.log:
                exercises = []
                for ex in self.workout.log:
                    exercises.append({
                        "id": ex.get("id", ""),
                        "name": ex.get("name", "Unknown"),
                        "sets": ex.get("sets", 0),
                        "reps": ",".join(map(str, ex.get("reps", []))) if ex.get("reps") else None,
                        "weight_kg": ex.get("weight"),
                    })

            workout_id = service.log_completed(
                workout_type=expected_type,
                duration_minutes=duration,
                notes=None,
                exercises=exercises,
            )

            # Log to workout scheduler for program tracking
            try:
                # Map workout type to protocol ID
                type_to_protocol = {
                    "STRENGTH_A": "strength_a",
                    "STRENGTH_B": "strength_b",
                    "STRENGTH_C": "strength_c",
                    "CARDIO_ZONE2": "zone2_cardio",
                    "ZONE2_EXTENDED": "zone2_extended",
                    "ACTIVE_MOBILITY": "active_mobility",
                    "RECOVERY": "recovery",
                }
                protocol_id = type_to_protocol.get(expected_type, expected_type.lower())
                self.workout_scheduler.log_workout(
                    protocol_id=protocol_id,
                    duration_minutes=duration,
                    traffic_light=None,  # Could get from cache if needed
                )
            except Exception as e:
                logger.warning(f"Failed to log to scheduler: {e}")

            # Log set-level data to workout_exercise_sets if available
            if self.workout.log:
                blueprint = get_blueprint_api()
                workout_exercises = blueprint.get_workout_exercises(workout_id)

                for i, ex_log in enumerate(self.workout.log):
                    if i >= len(workout_exercises):
                        break
                    we = workout_exercises[i]
                    reps_list = ex_log.get("reps", [])
                    weight = ex_log.get("weight")

                    for set_num, reps_actual in enumerate(reps_list, 1):
                        try:
                            exercise_set = WorkoutExerciseSet(
                                workout_exercise_id=we.id,
                                set_number=set_num,
                                reps_actual=reps_actual,
                                weight_kg=weight,
                            )
                            blueprint.add_workout_exercise_set(exercise_set)
                        except Exception as e:
                            logger.warning(f"Failed to log set data: {e}")

                # Clear the workout log after persisting
                self.workout.log = []

            # Reset workout finished state after successful logging
            self.workout.workout_finished = False
            self.workout.exercises_completed = 0
            self.workout.protocol = None  # Clear protocol reference
            self._clear_timer_from_session_status()

            # Try to sync Garmin activity data
            hr_info = await self._sync_garmin_activity(workout_id, expected_type)
            if hr_info:
                return f"{workout_name} logged. {duration} min. Avg HR {hr_info['avg_hr']}, max {hr_info['max_hr']}."
            return f"{workout_name} logged. {duration} minutes. Well executed."
        except Exception as e:
            import traceback
            logger.error(f"Workout logging error: {e}")
            logger.error(traceback.format_exc())
            logger.error(f"WORKOUT_LOG_ERROR: {e}")
            logger.debug(traceback.format_exc())
            return f"Couldn't log workout: {str(e)[:50]}. Try again."

    async def _handle_workout_confirmation(self, text: str) -> str:
        """Confirm and log pending workout."""
        if not self._pending_workout:
            return "No pending workout to confirm."

        pending = self._pending_workout
        self._pending_workout = None  # Clear pending

        # Extract notes from confirmation text
        notes = pending.get("mentioned_issues", "")

        # Extract duration from confirmation if provided
        duration = pending.get("duration")
        duration_match = re.search(r'(\d+)\s*(min|minutes?)', text.lower())
        if duration_match:
            duration = int(duration_match.group(1))

        if not duration:
            scheduled = pending.get("scheduled", {})
            duration = scheduled.get("duration_minutes", 45) if scheduled else 45

        scheduled = pending.get("scheduled", {})
        workout_type = scheduled.get("type", "STRENGTH_A") if scheduled else "STRENGTH_A"
        workout_name = scheduled.get("name", "Workout") if scheduled else "Workout"

        # Log the workout
        try:
            from atlas.health.workout import WorkoutService
            service = WorkoutService()
            workout_id = service.log_completed(
                workout_type=workout_type,
                duration_minutes=duration,
                notes=notes if notes else text,
            )

            # Try to sync Garmin activity data
            hr_info = await self._sync_garmin_activity(workout_id, workout_type)
            if hr_info:
                return f"{workout_name} logged. {duration} min. Avg HR {hr_info['avg_hr']}, max {hr_info['max_hr']}."
            return f"{workout_name} logged with notes. {duration} minutes. Recovery is part of the plan."
        except Exception as e:
            logger.error(f"Workout confirmation error: {e}")
            return f"Couldn't log workout. Try again."

    async def _sync_garmin_activity(self, workout_id: int, expected_type: str = "") -> dict | None:
        """
        Sync Garmin activity data and store with workout.

        Args:
            workout_id: The logged workout ID to associate HR data with
            expected_type: Expected workout type (e.g., "STRENGTH_A") to validate against

        Returns HR summary dict if successful, None otherwise.
        """
        try:
            from atlas.health.garmin import GarminService
            import sqlite3
            from pathlib import Path

            garmin = GarminService()
            if not garmin.is_configured():
                logger.debug("Garmin not configured")
                return None

            # Get latest activity (within last 4 hours)
            hr_data = await garmin.sync_latest_activity()
            if not hr_data:
                logger.debug("No recent Garmin activity found")
                return None

            if not hr_data.get("avg_hr"):
                logger.debug(f"Garmin activity has no HR data: {hr_data.get('activity_name')}")
                return None

            # Validate activity type matches expected workout
            activity_type = hr_data.get("activity_type", "").lower()
            expected_lower = expected_type.lower() if expected_type else ""

            # Map workout types to acceptable Garmin activity types
            valid_matches = {
                "strength": ["strength_training", "indoor_cardio", "other"],
                "cardio": ["cycling", "indoor_cycling", "running", "walking", "elliptical"],
                "mobility": ["yoga", "stretching", "pilates", "other"],
            }

            # Check if activity type is reasonable for the workout
            if expected_lower:
                workout_category = "strength" if "strength" in expected_lower else \
                                   "cardio" if "cardio" in expected_lower else \
                                   "mobility" if "mobility" in expected_lower else ""
                acceptable = valid_matches.get(workout_category, [])
                if acceptable and activity_type not in acceptable:
                    logger.warning(f"Activity type mismatch: got '{activity_type}', expected one of {acceptable}")
                    # Still sync but log warning - user might have used different activity type

            logger.info(f"Garmin sync: {activity_type} - avg HR {hr_data['avg_hr']}, max {hr_data.get('max_hr')}")

            # Store in database
            db_path = Path.home() / ".atlas" / "atlas.db"
            conn = sqlite3.connect(db_path)
            try:
                # Ensure table exists (matches schema_fitness.sql)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workout_hr_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workout_id INTEGER,
                        garmin_activity_id TEXT UNIQUE,
                        activity_type TEXT,
                        activity_name TEXT,
                        avg_hr INTEGER,
                        max_hr INTEGER,
                        calories INTEGER,
                        duration_minutes INTEGER,
                        distance_meters REAL,
                        start_time TEXT,
                        recorded_at TEXT DEFAULT (datetime('now'))
                    )
                """)

                # Check if activity already synced
                cursor = conn.execute(
                    "SELECT id FROM workout_hr_data WHERE garmin_activity_id = ?",
                    (hr_data.get("garmin_activity_id"),)
                )
                existing = cursor.fetchone()
                if existing:
                    logger.debug(f"Activity {hr_data.get('garmin_activity_id')} already synced")
                    # Still return hr_data for response, just don't insert again
                else:
                    conn.execute("""
                        INSERT INTO workout_hr_data
                        (workout_id, garmin_activity_id, activity_type, activity_name,
                         avg_hr, max_hr, calories, duration_minutes, distance_meters, start_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        workout_id,
                        hr_data.get("garmin_activity_id"),
                        hr_data.get("activity_type"),
                        hr_data.get("activity_name"),
                        hr_data.get("avg_hr"),
                        hr_data.get("max_hr"),
                        hr_data.get("calories"),
                        hr_data.get("duration_min"),
                        hr_data.get("distance_m"),
                        hr_data.get("start_time"),
                    ))
                    conn.commit()
                    logger.debug(f"Stored HR data for workout {workout_id}")
            finally:
                conn.close()

            return hr_data

        except Exception as e:
            logger.error(f"Garmin sync error for workout {workout_id}: {e}")
            return None

    async def _handle_health_status(self, text: str = "") -> str:
        """Get morning status from cache or sync fresh."""
        from atlas.health.morning_sync import get_morning_status, format_status_voice, format_briefing_voice

        # Detect if user wants detailed briefing
        text_lower = text.lower()
        wants_briefing = any(word in text_lower for word in [
            "briefing", "report", "rundown", "summary", "detail",
            "how was", "how did", "sleep", "overview"
        ])

        status = get_morning_status()

        if wants_briefing:
            return format_briefing_voice(status)
        else:
            return format_status_voice(status)

    async def _handle_workout_query(self) -> str:
        """Get today's workout from phase config."""
        from atlas.health.workout_lookup import get_todays_workout, format_workout_voice

        workout = get_todays_workout()
        if workout:
            # Track exercises mentioned for follow-up queries
            exercises = workout.get("exercises", [])
            if exercises:
                first_ex = exercises[0].get("name", "").lower()
                ex_id, _ = _find_exercise(first_ex)
                if ex_id:
                    self._last_exercise = ex_id
            return format_workout_voice(workout)
        else:
            return "No workout scheduled for today. Check your configuration."

    async def _handle_exercise_query(self, exercise_id: str | None) -> str:
        """Get form cues for an exercise from the library."""
        if not exercise_id:
            # List some available exercises
            library = _load_exercise_library()
            exercises = list(library.get("exercises", {}).keys())[:6]
            exercise_list = ", ".join(e.replace("_", " ") for e in exercises)
            return f"Which exercise? I can help with {exercise_list}, and more."

        # Find exercise in library
        ex_id, ex_data = _find_exercise(exercise_id)

        if not ex_data:
            return f"I don't have form cues for {exercise_id} yet. Try asking about goblet squat, deadlift, floor press, or any rehab exercise."

        # Track this exercise for follow-ups
        self._last_exercise = ex_id

        # Format for voice output
        return _format_exercise_voice(ex_data)

    async def _get_exercise_form_for_assessment(self) -> str:
        """Get exercise form cues from library for current assessment test."""
        if not self.assessment.runner or not self.assessment.runner._test_state:
            return "No active test."

        test = self.assessment.runner._test_state.test_def
        test_id = self.assessment.runner._test_state.test_id
        test_name = test.get("name", "")

        # Try to find exercise in library by test ID or name
        # Strip common suffixes like _8rm, _5rm, _right, _left, _max
        search_terms = [
            test_id.replace("_8rm", "").replace("_5rm", "").replace("_right", "").replace("_left", "").replace("_max", ""),
            test_name.lower(),
        ]

        for term in search_terms:
            ex_id, ex_data = _find_exercise(term)
            if ex_data:
                self._last_exercise = ex_id
                return _format_exercise_voice(ex_data)

        # Fallback - no exercise found in library
        return f"No detailed form guide for {test_name}. Try the setup command for test instructions."

    async def _handle_weight_log(self, body_comp: "BodyComposition") -> str:
        """Log weight and body composition to database."""
        import sqlite3
        from datetime import date, datetime

        db_path = Path.home() / ".atlas" / "atlas.db"
        conn = sqlite3.connect(db_path)

        today = date.today()
        current_time = datetime.now().strftime("%H:%M")

        try:
            # Build dynamic INSERT with available fields
            fields = ["date", "time", "weight_kg", "source"]
            values = [today.isoformat(), current_time, body_comp.weight_kg, "voice"]

            if body_comp.body_fat_pct is not None:
                fields.append("body_fat_pct")
                values.append(body_comp.body_fat_pct)
            if body_comp.muscle_mass_pct is not None:
                fields.append("muscle_mass_pct")
                values.append(body_comp.muscle_mass_pct)
            if body_comp.water_pct is not None:
                fields.append("water_pct")
                values.append(body_comp.water_pct)
            if body_comp.bone_mass_kg is not None:
                fields.append("bone_mass_kg")
                values.append(body_comp.bone_mass_kg)
            if body_comp.visceral_fat is not None:
                fields.append("visceral_fat")
                values.append(body_comp.visceral_fat)
            if body_comp.bmi is not None:
                fields.append("bmi")
                values.append(body_comp.bmi)
            if body_comp.bmr is not None:
                fields.append("bmr")
                values.append(body_comp.bmr)

            placeholders = ", ".join(["?"] * len(values))
            field_list = ", ".join(fields)

            # Build ON CONFLICT update clause
            update_fields = [f for f in fields if f not in ("date", "time")]
            update_clause = ", ".join([f"{f} = excluded.{f}" for f in update_fields])

            conn.execute(f"""
                INSERT INTO weight_log ({field_list})
                VALUES ({placeholders})
                ON CONFLICT(date, time) DO UPDATE SET {update_clause}
            """, values)
            conn.commit()

            # Get previous weight for comparison
            cursor = conn.execute("""
                SELECT weight_kg, body_fat_pct FROM weight_log
                WHERE date < ? ORDER BY date DESC, time DESC LIMIT 1
            """, (today.isoformat(),))
            row = cursor.fetchone()

            # Build response
            response = f"Logged. {body_comp.weight_kg} kilos"

            if body_comp.body_fat_pct is not None:
                response += f", {body_comp.body_fat_pct}% body fat"
            if body_comp.muscle_mass_pct is not None:
                response += f", {body_comp.muscle_mass_pct}% muscle"

            if row:
                diff = body_comp.weight_kg - row[0]
                if abs(diff) >= 0.1:
                    direction = "up" if diff > 0 else "down"
                    response += f". {abs(diff):.1f} {direction} from last."

            return response + "."

        except Exception as e:
            return f"Failed to log weight: {e}"
        finally:
            conn.close()

    async def _handle_weight_query(self, query_type: str) -> str:
        """Handle weight/body composition queries."""
        import sqlite3
        from datetime import date, timedelta

        db_path = Path.home() / ".atlas" / "atlas.db"
        conn = sqlite3.connect(db_path)

        try:
            today = date.today()

            # Get latest weight
            cursor = conn.execute("""
                SELECT weight_kg, body_fat_pct, muscle_mass_pct, water_pct, date
                FROM weight_log ORDER BY date DESC, time DESC LIMIT 1
            """)
            latest = cursor.fetchone()

            if not latest:
                return "No weight data recorded yet."

            weight_kg, body_fat, muscle, water, last_date = latest

            if query_type == "trend":
                # Get weight from 7 days ago
                week_ago = (today - timedelta(days=7)).isoformat()
                cursor = conn.execute("""
                    SELECT weight_kg, body_fat_pct FROM weight_log
                    WHERE date <= ? ORDER BY date DESC, time DESC LIMIT 1
                """, (week_ago,))
                old = cursor.fetchone()

                if old:
                    weight_diff = weight_kg - old[0]
                    direction = "Down" if weight_diff < 0 else "Up"
                    response = f"{direction} {abs(weight_diff):.1f} kilos this week."
                    if body_fat and old[1]:
                        fat_diff = body_fat - old[1]
                        fat_dir = "down" if fat_diff < 0 else "up"
                        response += f" Body fat {fat_dir} {abs(fat_diff):.1f}%."
                    return response
                else:
                    return f"{weight_kg} kilos. Not enough data for trend."

            elif query_type == "composition":
                response = f"{weight_kg} kilos."
                if body_fat:
                    response += f" {body_fat}% body fat."
                if muscle:
                    response += f" {muscle}% muscle."
                if water:
                    response += f" {water}% water."
                return response

            else:  # status
                # Get previous for comparison
                cursor = conn.execute("""
                    SELECT weight_kg FROM weight_log
                    WHERE date < ? ORDER BY date DESC, time DESC LIMIT 1
                """, (last_date,))
                prev = cursor.fetchone()

                response = f"{weight_kg} kilos"
                if body_fat:
                    response += f", {body_fat}% body fat"
                if prev:
                    diff = weight_kg - prev[0]
                    if abs(diff) >= 0.1:
                        direction = "down" if diff < 0 else "up"
                        response += f". {abs(diff):.1f} {direction} from yesterday"
                return response + "."

        except Exception as e:
            return f"Weight query failed: {e}"
        finally:
            conn.close()

    async def _handle_meal(self, text: str) -> str:
        """Log meal via NutritionService."""
        try:
            import os
            from atlas.nutrition import NutritionService

            # Debug: log API key status
            usda_key = os.environ.get("USDA_API_KEY", "")
            logger.info(f"USDA_API_KEY: {'set (' + usda_key[:8] + '...)' if usda_key else 'NOT SET'}")

            service = NutritionService()
            # Extract food content (remove trigger phrase)
            food_text = text
            for trigger in MEAL_TRIGGERS:
                if food_text.lower().startswith(trigger):
                    food_text = food_text[len(trigger):].lstrip(":- ")
                    break
            # Use asyncio.wait_for to add overall timeout
            try:
                record = await asyncio.wait_for(
                    service.log_meal(food_text, store=True),
                    timeout=20.0  # Max 20 seconds for entire operation
                )
                if record.nutrients.calories > 0:
                    # Success with nutrition data
                    return f"Saved. {record.nutrients.summary()}"
                else:
                    # Stored but no nutrition data
                    return f"Saved: {food_text}. No nutrition data found."
            except asyncio.TimeoutError:
                return f"Saved: {food_text}. Nutrition lookup timed out."
        except Exception as e:
            logger.error(f"Meal error: {e}")
            return f"Couldn't log meal: {e}"

    async def _handle_capture(self, text: str) -> str:
        """Capture thought via ThoughtClassifier."""
        try:
            from atlas.orchestrator.classifier import ThoughtClassifier
            classifier = ThoughtClassifier()
            result = classifier.classify_and_store(text)
            return f"Saved to {result.category.value}."
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return f"Couldn't capture: {e}"

    # ========================================
    # INTERACTIVE ROUTINE HANDLERS
    # ========================================

    async def _start_interactive_routine(self) -> str:
        """Start interactive morning routine session."""
        from atlas.health.routine_runner import load_routine_config

        config = load_routine_config()
        if not config.sections:
            return "No routine configured. Check phase1.json daily_routine section."

        try:
            # Initialize routine state
            self.routine.active = True
            self.routine.paused = False
            self.routine.section_idx = 0
            self.routine.exercise_idx = 0
            self._routine_config = config
            self._routine_sections = config.sections
            self.routine.exercise_complete = False
            self.routine.exercise_pending = True  # Wait for user to say ready
            self.routine.timer_active = False  # Timer not running yet

            # Set up first section and exercise
            first_section = config.sections[0]
            first_exercise = first_section.exercises[0] if first_section.exercises else None

            self.routine.current_section = first_section.name
            if first_exercise:
                self.routine.current_exercise = {
                    "id": first_exercise.id,
                    "name": first_exercise.name,
                    "duration_seconds": first_exercise.duration_seconds,
                    "reps": first_exercise.reps,
                    "sets": first_exercise.sets,
                    "per_side": first_exercise.per_side,
                    "hold_seconds": first_exercise.hold_seconds,
                    "cues": first_exercise.cues,
                    "type": first_exercise.type,
                }
                # Calculate timer duration
                self.routine.timer_duration = first_exercise.get_total_duration()
            else:
                self.routine.current_exercise = None
                self.routine.timer_duration = 30

            # DON'T start timer yet - wait for user to say ready
            self.routine.timer_start = None

            # Build response
            total_mins = config.duration_minutes
            response = f"Starting {config.name}. {total_mins} minutes total. "
            response += f"First section: {first_section.name}. "

            if first_exercise:
                response += f"First exercise: {first_exercise.name}. "
                if first_exercise.duration_seconds:
                    dur = first_exercise.duration_seconds
                    if first_exercise.per_side:
                        total_dur = dur * 2
                        response += f"{dur} seconds each side, {total_dur} total. "
                    else:
                        response += f"{dur} seconds. "
                elif first_exercise.reps:
                    response += f"{first_exercise.reps} reps. "

                # Add first cue if available
                if first_exercise.cues:
                    response += f"{first_exercise.cues[0]} "

                response += "Say ready or go to start timer."

            return response

        except Exception as e:
            self.routine.active = False
            raise

    async def _handle_routine_ready(self) -> str:
        """User said ready - start the exercise timer."""
        if not self.routine.active:
            return "No routine in progress."

        ex = self.routine.current_exercise
        if not ex:
            return "No current exercise."

        # Clear auto-advance state if user starts manually during pending phase
        if self.routine.auto_advance_pending:
            self.routine.auto_advance_pending = False
            self.routine.auto_advance_phase = None
            self.routine.auto_advance_start = None

        # Start timer
        self.routine.timer_start = time.monotonic()
        self.routine.timer_active = True
        self.routine.exercise_pending = False
        self.routine.exercise_complete = False

        # Reset side-tracking for per_side exercises
        is_per_side = ex.get('per_side', False)
        self.routine.side_switched = False
        self.routine.current_side = 'left' if is_per_side else None

        duration = self.routine.timer_duration
        ex_name = ex['name']

        # Play start chime
        try:
            from atlas.voice.audio_utils import chime_timer_start
            chime_timer_start()
        except ImportError:
            pass

        # Build response with side indicator for per_side exercises
        if is_per_side:
            half_duration = duration // 2
            return f"Timer started. {ex_name}. Left side. {half_duration} seconds. Go."
        return f"Timer started. {ex_name}. {duration} seconds. Go."

    async def _handle_routine_pause(self) -> str:
        """Pause routine and wait for resume or form request."""
        self.routine.paused = True
        self.routine.timer_active = False
        # Store remaining time
        if self.routine.timer_start:
            elapsed = time.monotonic() - self.routine.timer_start
            self.routine.timer_remaining = max(0, self.routine.timer_duration - elapsed)
        else:
            self.routine.timer_remaining = self.routine.timer_duration

        ex = self.routine.current_exercise
        if ex:
            return f"Paused. {ex['name']}. Say resume to continue, or ask about form."
        return "Paused. Say resume to continue."

    async def _handle_routine_resume(self) -> str:
        """Resume paused routine."""
        if not self.routine.paused:
            return "Routine not paused."

        self.routine.paused = False
        self.routine.timer_active = True

        # Get remaining time and restart timer
        remaining_time = self.routine.timer_remaining

        # Set timer start so elapsed calculation gives correct remaining time
        # elapsed = current_time - timer_start
        # remaining = duration - elapsed
        # We want: remaining = remaining_time
        # So: elapsed = duration - remaining_time
        # timer_start = current_time - elapsed = current_time - (duration - remaining_time)
        elapsed_before_pause = self.routine.timer_duration - remaining_time
        self.routine.timer_start = time.monotonic() - elapsed_before_pause

        ex = self.routine.current_exercise
        if ex:
            return f"Resuming {ex['name']}. {int(remaining_time)} seconds. Timer running."
        return "Resuming."

    async def _handle_routine_skip(self) -> str:
        """Skip current exercise and advance."""
        ex_name = self.routine.current_exercise['name'] if self.routine.current_exercise else "exercise"
        response = f"Skipping {ex_name}. "

        # Advance to next exercise
        advance_result = await self._advance_routine_exercise()
        return response + advance_result

    async def _handle_routine_stop(self) -> str:
        """Stop routine early."""
        section_name = self.routine.current_section or "routine"
        ex_idx = self.routine.exercise_idx
        section_idx = self.routine.section_idx

        logger.info(f"[ROUTINE-STOP] Stopping routine in {section_name}, exercise {ex_idx + 1}")

        # Reset state
        self.routine.active = False
        self.routine.paused = False
        self.routine.timer_active = False
        self.routine.exercise_pending = False
        self.routine.exercise_complete = False
        self.routine.current_exercise = None
        self.routine.current_section = None
        self.routine.timer_start = None
        self.routine.timer_duration = 0
        self.routine.timer_remaining = 0

        # Reset auto-advance state
        self.routine.auto_advance_pending = False
        self.routine.auto_advance_start = None
        self.routine.auto_advance_phase = None
        self.routine.next_exercise_msg = None
        self.routine.next_exercise_name = None

        # Reset indices
        self.routine.section_idx = 0
        self.routine.exercise_idx = 0

        # Clear timer from session status so UI hides timer card
        self._clear_timer_from_session_status()
        logger.info("[ROUTINE-STOP] Cleared timer from session status - returning to idle")

        return f"Routine stopped in {section_name}, exercise {ex_idx + 1}. Good effort."

    def _force_reset_routine_state(self):
        """Force reset all routine state variables (sync version for error recovery)."""
        logger.debug("FORCE_RESET: Clearing all routine state")
        self.routine.reset()
        # Clear timer from session status
        self._clear_timer_from_session_status()

    async def _handle_routine_complete(self) -> str:
        """Complete routine gracefully - set finished state for UI COMPLETE button."""
        from atlas.health.morning_sync import load_cached_status
        from atlas.health.workout_lookup import get_todays_workout
        import time

        # Set routine finished state (don't reset yet - wait for user to click COMPLETE)
        self.routine.active = False  # No longer active
        self.routine.timer_active = False
        self.routine.exercise_pending = False
        self.routine.auto_advance_pending = False
        self.routine.routine_finished = True  # Show COMPLETE button in UI
        self.routine.routine_finish_time = time.monotonic()

        # Play completion chime
        try:
            from atlas.voice.audio_utils import chime_routine_complete
            chime_routine_complete()
        except ImportError:
            pass

        # Build completion message with workout preview
        response = "Morning routine complete. Well done. Press COMPLETE to log. "

        # Check traffic light status
        status = load_cached_status()
        if status:
            traffic = status.get("traffic_light", "GREEN")
            battery = status.get("body_battery")

            if traffic == "RED":
                response += f"Recovery day. Body battery at {battery}. "
                response += "Light movement only, or rest. "
            elif traffic == "YELLOW":
                response += f"Yellow day. Body battery at {battery}. Proceed with caution. "
            else:
                response += f"Green light. Body battery at {battery}. Full intensity. "

        # Check today's workout
        workout = get_todays_workout()
        if workout:
            workout_name = workout.get("name", "Workout")
            duration = workout.get("duration_minutes", 45)
            response += f"Today: {workout_name}, {duration} minutes. "

        response += "Say start workout when ready."
        return response

    def _handle_log_routine(self) -> str:
        """Log routine completion to database and reset state (called from UI COMPLETE button)."""
        import sqlite3
        from datetime import date
        from pathlib import Path

        db_path = Path.home() / ".atlas" / "atlas.db"

        try:
            conn = sqlite3.connect(db_path)
            today = date.today()

            # Log as a workout of type 'routine'
            cursor = conn.execute("""
                INSERT INTO workouts (date, type, duration_minutes, notes)
                VALUES (?, 'routine', 18, 'Morning routine completed')
            """, (today.isoformat(),))

            conn.commit()
            workout_id = cursor.lastrowid
            conn.close()

            logger.info(f"Logged morning routine for {today.strftime('%B %d, %Y')} (#{workout_id})")

            # Now fully reset routine state
            self.routine.reset()

            # Clear timer from UI
            self._clear_timer_from_session_status()

            return f"Routine logged for {today.strftime('%B %d')}. Nice work!"

        except Exception as e:
            logger.error(f"Failed to log routine: {e}")
            self.routine.reset()
            self._clear_timer_from_session_status()
            return "Routine complete but logging failed."

    def _load_routine_form_guides(self) -> dict:
        """Load routine form guides from JSON file (cached)."""
        if not hasattr(self, '_routine_form_guides_cache'):
            form_guides_path = Path(__file__).parent.parent.parent / "config" / "exercises" / "routine_form_guides.json"
            if form_guides_path.exists():
                try:
                    with open(form_guides_path) as f:
                        data = json.load(f)
                        self._routine_form_guides_cache = data.get('exercises', {})
                except Exception as e:
                    logger.warning(f"Failed to load routine form guides: {e}")
                    self._routine_form_guides_cache = {}
            else:
                self._routine_form_guides_cache = {}
        return self._routine_form_guides_cache

    async def _handle_routine_form_request(self, text: str) -> str:
        """Provide form/setup guidance for current exercise."""
        ex = self.routine.current_exercise
        if not ex:
            return "No current exercise. Say resume to continue."

        ex_id = ex.get('id', '').lower()
        ex_name = ex.get('name', '').lower()

        # First check the detailed routine form guides
        form_guides = self._load_routine_form_guides()
        if form_guides:
            # Try exact ID match first
            if ex_id in form_guides:
                guide = form_guides[ex_id]
                return self._format_form_response(ex['name'], guide)

            # Try matching by name or aliases
            for guide_id, guide in form_guides.items():
                guide_name = guide.get('name', '').lower()
                aliases = [a.lower() for a in guide.get('aliases', [])]

                if (ex_name in guide_name or guide_name in ex_name or
                    any(alias in ex_name or ex_name in alias for alias in aliases)):
                    return self._format_form_response(ex['name'], guide)

        # Fallback to general exercise library
        exercise_lib = _load_exercise_library()
        exercises = exercise_lib.get('exercises', {})
        if exercises:
            for ex_key, lib_ex in exercises.items():
                lib_name = lib_ex.get('name', '').lower()
                lib_id = ex_key.lower()
                if ex_id in lib_id or ex_name in lib_name or lib_name in ex_name:
                    cues = lib_ex.get('cues', [])
                    setup = lib_ex.get('setup', '')
                    response_parts = [f"{ex['name']}."]
                    if setup:
                        response_parts.append(setup)
                    if cues:
                        for cue in cues[:3]:
                            response_parts.append(cue)
                    response_parts.append("Say ready when set.")
                    return " ".join(response_parts)

        # Fallback to exercise's own cues
        cues = ex.get('cues', [])
        if cues:
            response = f"{ex['name']}. " + " ".join(cues[:3])
            response += " Say ready when set."
            return response

        return f"{ex['name']}. No form cues available. Say ready to continue."

    def _format_form_response(self, name: str, guide: dict) -> str:
        """Format a form guide into a voice response."""
        parts = [f"{name}."]

        # Add setup
        setup = guide.get('setup', '')
        if setup:
            parts.append(setup)

        # Add cues (up to 4 for voice)
        cues = guide.get('cues', [])
        if cues:
            for cue in cues[:4]:
                parts.append(cue)

        parts.append("Say ready when set.")
        return " ".join(parts)

    def _get_exercise_setup_tip(self, exercise_id: str, exercise_name: str) -> str | None:
        """Get brief setup tip for exercise (for auto-advance announcements)."""
        form_guides = self._load_routine_form_guides()
        if not form_guides:
            return None

        ex_id = exercise_id.lower()
        ex_name = exercise_name.lower()

        # Try exact ID match first
        if ex_id in form_guides:
            return form_guides[ex_id].get('setup', '')

        # Try matching by name or aliases
        for guide_id, guide in form_guides.items():
            guide_name = guide.get('name', '').lower()
            aliases = [a.lower() for a in guide.get('aliases', [])]

            if (ex_name in guide_name or guide_name in ex_name or
                any(alias in ex_name or ex_name in alias for alias in aliases)):
                return guide.get('setup', '')

        return None

    def _count_routine_exercises(self) -> int:
        """Count total exercises in routine, excluding reminders."""
        if not hasattr(self, '_routine_sections') or not self._routine_sections:
            return 0
        return sum(
            1 for section in self._routine_sections
            for ex in section.exercises
            if not ex.is_reminder()
        )

    def _get_routine_exercise_number(self) -> int:
        """Get current exercise number, excluding reminders from count."""
        if not hasattr(self, '_routine_sections') or not self._routine_sections:
            return 1

        count = 1  # Start at 1

        # Add all non-reminder exercises from previous sections
        for i in range(self.routine.section_idx):
            section = self._routine_sections[i]
            count += sum(1 for ex in section.exercises if not ex.is_reminder())

        # Add non-reminder exercises before current in this section
        current_section = self._routine_sections[self.routine.section_idx]
        for j in range(self.routine.exercise_idx):
            if not current_section.exercises[j].is_reminder():
                count += 1

        # Don't count current exercise if it's a reminder
        if self.routine.exercise_idx < len(current_section.exercises):
            if current_section.exercises[self.routine.exercise_idx].is_reminder():
                count -= 1  # Reminders don't get numbered

        return max(1, count)

    def _get_next_routine_exercise_info(self) -> dict | None:
        """Get info about the next exercise in the routine (for UI preview)."""
        if not hasattr(self, '_routine_sections') or not self._routine_sections:
            return None

        # Calculate what the next exercise will be
        next_section_idx = self.routine.section_idx
        next_exercise_idx = self.routine.exercise_idx + 1

        current_section = self._routine_sections[next_section_idx]

        # Check if more exercises in current section
        if next_exercise_idx < len(current_section.exercises):
            next_ex = current_section.exercises[next_exercise_idx]
            if next_ex.is_reminder():
                return {"name": "Routine Complete", "setup": None}
            setup = self._get_exercise_setup_tip(next_ex.id, next_ex.name)
            return {"name": next_ex.name, "setup": setup}

        # Check next section
        next_section_idx += 1
        if next_section_idx < len(self._routine_sections):
            next_section = self._routine_sections[next_section_idx]
            if next_section.exercises:
                next_ex = next_section.exercises[0]
                if next_ex.is_reminder():
                    return {"name": "Routine Complete", "setup": None}
                setup = self._get_exercise_setup_tip(next_ex.id, next_ex.name)
                return {"name": next_ex.name, "setup": setup, "new_section": next_section.name}

        return {"name": "Routine Complete", "setup": None}

    def _get_exercise_form_cue(self, exercise_id: str, exercise_name: str, cue_index: int = 0) -> str | None:
        """Get a specific form cue for exercise (for rotating cues during exercise)."""
        form_guides = self._load_routine_form_guides()
        if not form_guides:
            return None

        ex_id = exercise_id.lower()
        ex_name = exercise_name.lower()

        # Try exact ID match first
        if ex_id in form_guides:
            cues = form_guides[ex_id].get('cues', [])
            if cues and cue_index < len(cues):
                return cues[cue_index]
            return None

        # Try matching by name or aliases
        for guide_id, guide in form_guides.items():
            guide_name = guide.get('name', '').lower()
            aliases = [a.lower() for a in guide.get('aliases', [])]

            if (ex_name in guide_name or guide_name in ex_name or
                any(alias in ex_name or ex_name in alias for alias in aliases)):
                cues = guide.get('cues', [])
                if cues and cue_index < len(cues):
                    return cues[cue_index]
                return None

        return None

    def _get_workout_exercise_form_cue(self, exercise_id: str, exercise_name: str) -> str | None:
        """Get form cue for workout exercise. Prefers voice_cue_short if available."""
        ex_id = exercise_id.lower()
        ex_name = exercise_name.lower()

        # First try routine form guides (more detailed)
        form_guides = self._load_routine_form_guides()
        if form_guides:
            # Try exact ID match
            if ex_id in form_guides:
                guide = form_guides[ex_id]
                # Prefer voice_cue_short for UI display
                if guide.get('voice_cue_short'):
                    return guide['voice_cue_short']
                cues = guide.get('cues', [])
                return cues[0] if cues else None

            # Try matching by name or aliases
            for guide_id, guide in form_guides.items():
                guide_name = guide.get('name', '').lower()
                aliases = [a.lower() for a in guide.get('aliases', [])]

                if (ex_name in guide_name or guide_name in ex_name or
                    any(alias in ex_name or ex_name in alias for alias in aliases)):
                    # Prefer voice_cue_short for UI display
                    if guide.get('voice_cue_short'):
                        return guide['voice_cue_short']
                    cues = guide.get('cues', [])
                    return cues[0] if cues else None

        # Fallback to exercise library (for workout exercises like Goblet Squat, RDL)
        exercise_lib = _load_exercise_library()
        exercises = exercise_lib.get('exercises', {})
        if exercises:
            for ex_key, lib_ex in exercises.items():
                lib_name = lib_ex.get('name', '').lower()
                lib_id = ex_key.lower()
                if ex_id == lib_id or ex_id in lib_id or ex_name in lib_name or lib_name in ex_name:
                    # Prefer voice_cue_short for UI display
                    if lib_ex.get('voice_cue_short'):
                        return lib_ex['voice_cue_short']
                    cues = lib_ex.get('cues', [])
                    return cues[0] if cues else None

        return None

    def _get_workout_exercise_setup_tip(self, exercise_id: str, exercise_name: str) -> str | None:
        """Get setup tip for workout exercise (from form guides or exercise library)."""
        ex_id = exercise_id.lower()
        ex_name = exercise_name.lower()

        # First try routine form guides
        form_guides = self._load_routine_form_guides()
        if form_guides:
            if ex_id in form_guides:
                return form_guides[ex_id].get('setup', '')
            for guide_id, guide in form_guides.items():
                guide_name = guide.get('name', '').lower()
                aliases = [a.lower() for a in guide.get('aliases', [])]
                if (ex_name in guide_name or guide_name in ex_name or
                    any(alias in ex_name or ex_name in alias for alias in aliases)):
                    return guide.get('setup', '')

        # Fallback to exercise library for workout exercises
        exercise_lib = _load_exercise_library()
        exercises = exercise_lib.get('exercises', {})
        if exercises:
            for ex_key, lib_ex in exercises.items():
                lib_name = lib_ex.get('name', '').lower()
                lib_id = ex_key.lower()
                if ex_id == lib_id or ex_id in lib_id or ex_name in lib_name or lib_name in ex_name:
                    return lib_ex.get('setup', '')
        return None

    def _get_next_workout_exercise_info(self) -> dict | None:
        """Get info about the next exercise in the workout (for UI preview)."""
        if not self.workout.active or not self.workout.exercises:
            return None

        next_idx = self.workout.exercise_idx + 1
        if next_idx < len(self.workout.exercises):
            next_ex = self.workout.exercises[next_idx]
            # WorkoutExercise is a dataclass, use attribute access not .get()
            ex_id = getattr(next_ex, 'id', '') or next_ex.name.lower().replace(' ', '_')
            ex_name = next_ex.name
            setup = self._get_workout_exercise_setup_tip(ex_id, ex_name)
            return {"name": ex_name, "setup": setup}

        return {"name": "Workout Complete", "setup": None}

    async def _advance_routine_exercise(self) -> str:
        """Advance to next exercise or section."""
        if not hasattr(self, '_routine_sections') or not self._routine_sections:
            self.routine.active = False
            return "Routine complete."

        current_section = self._routine_sections[self.routine.section_idx]
        self.routine.exercise_idx += 1

        # Check if more exercises in section
        if self.routine.exercise_idx < len(current_section.exercises):
            next_ex = current_section.exercises[self.routine.exercise_idx]
            self.routine.current_exercise = {
                "id": next_ex.id,
                "name": next_ex.name,
                "duration_seconds": next_ex.duration_seconds,
                "reps": next_ex.reps,
                "sets": next_ex.sets,
                "per_side": next_ex.per_side,
                "hold_seconds": next_ex.hold_seconds,
                "cues": next_ex.cues,
                "type": next_ex.type,
            }
            self.routine.timer_duration = next_ex.get_total_duration()

            # Handle reminder-type exercises (no timer, just announcement)
            if next_ex.is_reminder():
                response = f"{next_ex.name}. "
                if next_ex.cues:
                    response += f"{next_ex.cues[0]} "
                response += "Routine complete. Great effort."
                # End routine on reminder (reminders are final items)
                self.routine.active = False
                self.routine.exercise_pending = False
                self.routine.timer_active = False
                try:
                    from atlas.voice.audio_utils import chime_routine_complete
                    chime_routine_complete()
                except ImportError:
                    pass
                return response

            # DON'T auto-start timer - wait for user ready
            self.routine.timer_start = None
            self.routine.timer_active = False
            self.routine.exercise_pending = True
            self.routine.exercise_complete = False

            response = f"Next: {next_ex.name}. "
            if next_ex.duration_seconds:
                dur = next_ex.duration_seconds
                if next_ex.per_side:
                    total_dur = dur * 2
                    response += f"{dur} seconds each side, {total_dur} total. "
                else:
                    response += f"{dur} seconds. "
            elif next_ex.reps:
                response += f"{next_ex.reps} reps. "

            if next_ex.cues:
                response += f"{next_ex.cues[0]} "

            response += "Say ready to start."
            return response

        # Move to next section
        self.routine.section_idx += 1
        self.routine.exercise_idx = 0

        if self.routine.section_idx < len(self._routine_sections):
            next_section = self._routine_sections[self.routine.section_idx]
            self.routine.current_section = next_section.name

            # Play section complete chime
            try:
                from atlas.voice.audio_utils import chime_section_complete
                chime_section_complete()
            except ImportError:
                pass

            if next_section.exercises:
                next_ex = next_section.exercises[0]
                self.routine.current_exercise = {
                    "id": next_ex.id,
                    "name": next_ex.name,
                    "duration_seconds": next_ex.duration_seconds,
                    "reps": next_ex.reps,
                    "sets": next_ex.sets,
                    "per_side": next_ex.per_side,
                    "hold_seconds": next_ex.hold_seconds,
                    "cues": next_ex.cues,
                    "type": next_ex.type,
                }
                self.routine.timer_duration = next_ex.get_total_duration()

                # Handle reminder-type exercises (no timer, just announcement)
                if next_ex.is_reminder():
                    response = f"Section complete. Final step: {next_ex.name}. "
                    if next_ex.cues:
                        response += f"{next_ex.cues[0]} "
                    response += "Routine complete. Great effort."
                    # End routine on reminder
                    self.routine.active = False
                    self.routine.exercise_pending = False
                    self.routine.timer_active = False
                    try:
                        from atlas.voice.audio_utils import chime_routine_complete
                        chime_routine_complete()
                    except ImportError:
                        pass
                    return response

                # DON'T auto-start timer - wait for user ready
                self.routine.timer_start = None
                self.routine.timer_active = False
                self.routine.exercise_pending = True
                self.routine.exercise_complete = False

                response = f"Section complete. Next section: {next_section.name}. "
                response += f"First exercise: {next_ex.name}. "
                if next_ex.duration_seconds:
                    dur = next_ex.duration_seconds
                    if next_ex.per_side:
                        total_dur = dur * 2
                        response += f"{dur} seconds each side, {total_dur} total. "
                    else:
                        response += f"{dur} seconds. "
                elif next_ex.reps:
                    response += f"{next_ex.reps} reps. "

                response += "Say ready to start."
                return response

        # Routine complete
        self.routine.active = False
        self.routine.timer_active = False
        self.routine.exercise_pending = False
        self.routine.current_exercise = None
        self.routine.current_section = None

        # Play completion chime
        try:
            from atlas.voice.audio_utils import chime_routine_complete
            chime_routine_complete()
        except ImportError:
            pass

        return "Routine complete. Well done."

    def _check_routine_timer(self) -> tuple[str | None, bool]:
        """
        Check routine exercise timer status.

        Returns:
            (message, exercise_complete) - message if timer ended
        """
        if not self.routine.active or self.routine.paused:
            return None, False

        if not self.routine.timer_start:
            return None, False

        elapsed = time.monotonic() - self.routine.timer_start
        remaining = self.routine.timer_duration - elapsed

        # Check if this is a per_side exercise
        ex = self.routine.current_exercise
        is_per_side = ex and ex.get('per_side', False)
        half_duration = self.routine.timer_duration / 2

        # Per-side exercises: switch sides at half duration
        if is_per_side and not self.routine.side_switched and elapsed >= half_duration:
            self.routine.side_switched = True
            self.routine.current_side = 'right'
            # Play side switch chime (double beep)
            try:
                from atlas.voice.audio_utils import chime_side_switch
                chime_side_switch()
            except Exception:
                pass
            return "Switch sides.", False  # Not complete yet

        if remaining <= 0 and not self.routine.exercise_complete:
            self.routine.exercise_complete = True
            # Play exercise complete chime
            try:
                from atlas.voice.audio_utils import chime_exercise_complete
                chime_exercise_complete()
            except ImportError:
                pass
            return "Exercise complete.", True

        return None, False

    def _get_routine_time_remaining(self) -> int:
        """Get remaining time for current exercise."""
        if not self.routine.timer_start:
            return 0
        elapsed = time.monotonic() - self.routine.timer_start
        return max(0, int(self.routine.timer_duration - elapsed))

    def _start_routine_auto_advance(self):
        """Start auto-advance to next exercise (Command Centre autonomous flow)."""
        self.routine.auto_advance_pending = True
        self.routine.auto_advance_start = time.monotonic()
        self.routine.auto_advance_phase = 'completed'
        self.routine.timer_active = False

        # Pre-build the next exercise announcement
        self.routine.next_exercise_msg = self._build_next_exercise_announcement()
        logger.debug(f"ROUTINE AUTO-ADVANCE Started. Phase: completed. Next msg: {self.routine.next_exercise_msg[:50] if self.routine.next_exercise_msg else 'None'}...")

    def _build_next_exercise_announcement(self) -> str | None:
        """Build announcement for next exercise including setup tip.

        Also stores the next exercise name in _routine_next_exercise_name for UI display.
        """
        if not hasattr(self, '_routine_sections') or not self._routine_sections:
            self.routine.next_exercise_name = None
            return None

        # Calculate what the next exercise will be
        next_section_idx = self.routine.section_idx
        next_exercise_idx = self.routine.exercise_idx + 1

        current_section = self._routine_sections[next_section_idx]

        # Check if more exercises in current section
        if next_exercise_idx < len(current_section.exercises):
            next_ex = current_section.exercises[next_exercise_idx]
            ex_name = next_ex.name

            # Store name for UI display during transition
            self.routine.next_exercise_name = ex_name

            # Get setup tip from form guides
            setup_tip = self._get_exercise_setup_tip(next_ex.id, next_ex.name)

            # Build announcement: "Get ready. Next exercise: Cat-Cow. Get on all fours."
            if setup_tip:
                return f"Get ready. Next exercise: {ex_name}. {setup_tip}"
            elif next_ex.cues:
                return f"Get ready. Next exercise: {ex_name}. {next_ex.cues[0]}"
            else:
                return f"Get ready. Next exercise: {ex_name}."

        # Check next section
        next_section_idx += 1
        if next_section_idx < len(self._routine_sections):
            next_section = self._routine_sections[next_section_idx]
            if next_section.exercises:
                next_ex = next_section.exercises[0]
                ex_name = next_ex.name

                # Store name for UI display during transition
                self.routine.next_exercise_name = ex_name

                # Get setup tip from form guides
                setup_tip = self._get_exercise_setup_tip(next_ex.id, next_ex.name)

                # Include section transition - announce clearly
                section_msg = f"Section complete. Next section: {next_section.name}. Get ready. Next exercise: {ex_name}."
                if setup_tip:
                    return f"{section_msg} {setup_tip}"
                elif next_ex.cues:
                    return f"{section_msg} {next_ex.cues[0]}"
                else:
                    return section_msg

        # Routine complete
        self.routine.next_exercise_name = None
        return None

    def _check_routine_auto_advance(self):
        """
        Check and process routine auto-advance state machine.

        Timing:
        - 'completed' phase: 2 seconds (let "Exercise complete" sink in)
        - 'pending' phase: 4 seconds (UI shows READY? screen with voice announcement)
        - Then: auto-start timer

        The voice announcement now happens when entering 'pending' phase, synchronized
        with the READY? screen appearing on the UI.
        """
        if not self.routine.auto_advance_start:
            return

        elapsed = time.monotonic() - self.routine.auto_advance_start

        if self.routine.auto_advance_phase == 'completed':
            # After 2 seconds: advance state and announce (UI shows READY? with voice)
            if elapsed >= 2.0:
                if self.routine.next_exercise_msg:
                    logger.debug("ROUTINE AUTO-ADVANCE Phase: pending (advancing state + announcing)")

                    # NOW advance to next exercise FIRST (so UI shows READY? screen)
                    try:
                        asyncio.run(self._advance_routine_exercise_silent())
                    except Exception as e:
                        logger.error(f"[ROUTINE AUTO-ADVANCE] Advance failed: {e}")
                        self.routine.auto_advance_pending = False
                        return

                    # Now announce (voice synchronized with READY? screen)
                    self._autonomous_speak(self.routine.next_exercise_msg)

                    # Enter pending phase for positioning time
                    self.routine.auto_advance_phase = 'pending'
                    # DON'T reset timer - keep original start time for continuous countdown
                else:
                    # No next exercise = routine complete
                    logger.debug("ROUTINE AUTO-ADVANCE Routine complete")
                    try:
                        msg = asyncio.run(self._handle_routine_complete())
                        self._autonomous_speak(msg)
                    except Exception as e:
                        logger.error(f"[ROUTINE AUTO-ADVANCE] Complete failed: {e}")
                    self.routine.auto_advance_pending = False

        elif self.routine.auto_advance_phase == 'pending':
            # After 6 seconds total (2s completed + 4s pending): start timer
            if elapsed >= 6.0:
                logger.debug("ROUTINE AUTO-ADVANCE Phase: starting timer")

                self.routine.auto_advance_pending = False
                self.routine.auto_advance_phase = None
                self.routine.auto_advance_start = None

                # Start the timer automatically
                ex = self.routine.current_exercise
                if ex:
                    # Check if exercise has a timer
                    has_timer = ex.get('duration_seconds') or ex.get('reps')
                    if has_timer:
                        self._auto_start_routine_timer()
                    else:
                        # No timer exercise (like Morning Sunlight) - just announce
                        self._autonomous_speak(f"{ex.get('name', 'Exercise')}. No timer needed. Say finished or skip.")

    def _auto_start_routine_timer(self):
        """Auto-start routine timer (Command Centre autonomous flow)."""
        ex = self.routine.current_exercise
        if not ex:
            return

        # Start timer
        self.routine.timer_start = time.monotonic()
        self.routine.timer_active = True
        self.routine.exercise_pending = False
        self.routine.exercise_complete = False

        # Reset side-tracking for per_side exercises
        is_per_side = ex.get('per_side', False)
        self.routine.side_switched = False
        self.routine.current_side = 'left' if is_per_side else None

        # Play start chime
        try:
            from atlas.voice.audio_utils import chime_timer_start
            chime_timer_start()
        except ImportError:
            pass

        # Build and speak the "Go" message
        duration = self.routine.timer_duration
        if is_per_side:
            half_duration = duration // 2
            msg = f"Go. Left side. {half_duration} seconds."
        else:
            msg = f"Go. {duration} seconds."

        self._autonomous_speak(msg)

    async def _advance_routine_exercise_silent(self):
        """Advance to next exercise without speaking (for auto-advance flow)."""
        if not hasattr(self, '_routine_sections') or not self._routine_sections:
            self.routine.active = False
            return

        current_section = self._routine_sections[self.routine.section_idx]
        self.routine.exercise_idx += 1

        # Check if more exercises in section
        if self.routine.exercise_idx < len(current_section.exercises):
            next_ex = current_section.exercises[self.routine.exercise_idx]
            self.routine.current_exercise = {
                "id": next_ex.id,
                "name": next_ex.name,
                "duration_seconds": next_ex.duration_seconds,
                "reps": next_ex.reps,
                "sets": next_ex.sets,
                "per_side": next_ex.per_side,
                "hold_seconds": next_ex.hold_seconds,
                "cues": next_ex.cues,
                "type": next_ex.type,
            }
            self.routine.timer_duration = next_ex.get_total_duration()

            # Reminder exercises end the routine
            if next_ex.is_reminder():
                self.routine.active = False
                self.routine.exercise_pending = False
                return

            self.routine.timer_start = None
            self.routine.timer_active = False
            self.routine.exercise_pending = True
            self.routine.exercise_complete = False
            return

        # Move to next section
        self.routine.section_idx += 1
        self.routine.exercise_idx = 0

        if self.routine.section_idx < len(self._routine_sections):
            next_section = self._routine_sections[self.routine.section_idx]
            self.routine.current_section = next_section.name

            # Play section complete chime
            try:
                from atlas.voice.audio_utils import chime_section_complete
                chime_section_complete()
            except ImportError:
                pass

            if next_section.exercises:
                next_ex = next_section.exercises[0]
                self.routine.current_exercise = {
                    "id": next_ex.id,
                    "name": next_ex.name,
                    "duration_seconds": next_ex.duration_seconds,
                    "reps": next_ex.reps,
                    "sets": next_ex.sets,
                    "per_side": next_ex.per_side,
                    "hold_seconds": next_ex.hold_seconds,
                    "cues": next_ex.cues,
                    "type": next_ex.type,
                }
                self.routine.timer_duration = next_ex.get_total_duration()

                # Reminder exercises end the routine
                if next_ex.is_reminder():
                    self.routine.active = False
                    self.routine.exercise_pending = False
                    return

                self.routine.timer_start = None
                self.routine.timer_active = False
                self.routine.exercise_pending = True
                self.routine.exercise_complete = False
                return

        # Routine complete - will be handled by caller
        self.routine.active = False

    # ========================================
    # ASSESSMENT PROTOCOL HANDLERS
    # ========================================

    def _is_assessment_start_intent(self, text: str) -> bool:
        """Check if text is starting a new assessment."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in ASSESS_START_PATTERNS)

    def _is_assessment_resume_intent(self, text: str) -> bool:
        """Check if text is resuming an assessment."""
        text_lower = text.lower().strip()
        return any(p in text_lower for p in ASSESS_RESUME_PATTERNS)

    def _is_assessment_active(self) -> bool:
        """Check if assessment session is active."""
        return self.assessment.runner is not None and self.assessment.runner.state is not None

    def _is_assessment_session_pending(self) -> bool:
        """Check if waiting for session selection."""
        return self.assessment.pending_session is not None or (
            self.assessment.runner is not None and
            self.assessment.runner.state is None
        )

    def _get_assessment_command(self, text: str) -> str | None:
        """Check if text matches an assessment command."""
        text_lower = text.lower().strip()
        for cmd, patterns in ASSESS_COMMANDS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return cmd
        return None

    def _is_timer_start(self, text: str) -> bool:
        """Check for timer start command."""
        text_lower = text.lower().strip()
        # Check for exact match first (single word commands)
        if text_lower in ["go", "start", "ready", "begin"]:
            return True
        # Check for phrase matches
        return any(phrase in text_lower for phrase in ASSESS_TIMER_START)

    def _is_timer_stop(self, text: str) -> bool:
        """Check for timer stop command."""
        text_lower = text.lower().strip()
        return any(stop_word in text_lower for stop_word in ASSESS_TIMER_STOP)

    def _is_assessment_info_intent(self, text: str) -> bool:
        """Check if querying assessment info (not starting or resuming)."""
        text_lower = text.lower().strip()
        # Exclude if text STARTS with start/resume patterns (those trigger sessions)
        # "start baseline" → action, but "how long is baseline assessment" → info
        for p in ASSESS_START_PATTERNS:
            if text_lower.startswith(p):
                return False
        for p in ASSESS_RESUME_PATTERNS:
            if text_lower.startswith(p):
                return False
        # Use pre-compiled patterns for efficiency
        return any(pattern.search(text_lower) for pattern in ASSESS_INFO_COMPILED)

    async def _handle_assessment_info(self, text: str) -> str:
        """Provide information about assessment protocol without starting it."""
        logger.info(f"Assessment info query: {text[:50]}")
        text_lower = text.lower()

        # Get actual test count from protocol config (avoid hardcoded values)
        try:
            protocol_path = Path(__file__).parent.parent.parent / "config" / "assessments" / "protocol_voice.json"
            with open(protocol_path) as f:
                protocol = json.load(f)
            total_tests = protocol.get("metadata", {}).get("total_tests", 71)
        except Exception as e:
            logger.warning(f"Could not read protocol config: {e}, using fallback count")
            total_tests = 71  # Fallback

        # Check for duration query
        if any(kw in text_lower for kw in ["how long", "duration", "time"]):
            return ("Baseline assessment has three sessions. "
                    "Session 1 is body composition, about 20 minutes. "
                    "Session 2 is strength and mobility, about 45 minutes. "
                    "Session 3 is cardio tests, about 30 minutes. "
                    "Say 'start baseline' when ready.")

        # Check for session query
        if any(kw in text_lower for kw in ["session", "which", "what are"]):
            return ("Three sessions. "
                    "Session 1 covers weight, measurements, blood pressure, resting heart rate. "
                    "Session 2 covers strength tests, mobility, balance. "
                    "Session 3 covers cardio fitness and recovery. "
                    "Say 'start baseline' to begin, or 'session 1' to jump straight in.")

        # General protocol explanation
        return (f"Baseline assessment tracks {total_tests} tests across strength, mobility, and cardio. "
                "Results establish your starting point for tracking progress. "
                "Three sessions: 1 for body composition, 2 for strength and mobility, "
                "3 for cardio. Say 'start baseline' when ready, or 'session 1' to begin.")

    async def _handle_assessment_start(self, text: str) -> str:
        """Handle starting a new assessment session."""
        from atlas.health.assessment_runner import AssessmentProtocolRunner

        # Initialize runner if needed
        if self.assessment.runner is None:
            self.assessment.runner = AssessmentProtocolRunner()

        # Check if session specified in text
        session_id = self.assessment.runner.parse_session_choice(text)

        if session_id:
            # Start specific session
            response = await self.assessment.runner.start_session(session_id)
            self.assessment.pending_session = None
            return response
        else:
            # Prompt for session selection
            self.assessment.pending_session = "pending"
            return self.assessment.runner.get_session_choices()

    async def _handle_assessment_session_choice(self, text: str) -> str:
        """Handle session selection during pending state."""
        if self.assessment.runner is None:
            from atlas.health.assessment_runner import AssessmentProtocolRunner
            self.assessment.runner = AssessmentProtocolRunner()

        session_id = self.assessment.runner.parse_session_choice(text)

        if session_id:
            self.assessment.pending_session = None
            return await self.assessment.runner.start_session(session_id)
        else:
            return "Which session? 1, 2, or 3?"

    async def _handle_assessment_resume(self) -> str:
        """Handle resuming an assessment session."""
        from atlas.health.assessment_runner import AssessmentProtocolRunner

        if self.assessment.runner is None:
            self.assessment.runner = AssessmentProtocolRunner()

        return await self.assessment.runner.resume_session()

    async def _handle_assessment_input(self, text: str) -> str:
        """Process input during active assessment."""
        if self.assessment.runner is None:
            return "No active assessment."

        text_lower = text.lower().strip()

        # Check for commands first
        cmd = self._get_assessment_command(text)

        if cmd == "setup":
            return await self.assessment.runner.get_setup()
        elif cmd == "form":
            # Get exercise form from library based on current test
            return await self._get_exercise_form_for_assessment()
        elif cmd == "skip":
            return await self.assessment.runner.skip_test()
        elif cmd == "undo":
            return await self.assessment.runner.undo_last()
        elif cmd == "repeat":
            # Re-speak current test prompt
            if self.assessment.runner._test_state:
                return self.assessment.runner._format_test_prompt(
                    self.assessment.runner._test_state.test_def
                )
            return "No current test."
        elif cmd == "status":
            return await self.assessment.runner.get_status()
        elif cmd == "equipment":
            return await self.assessment.runner.get_equipment_needed()
        elif cmd == "pause":
            response = await self.assessment.runner.pause_session()
            self.assessment.runner = None
            self.assessment.timing = False
            self.assessment.timer_start = None
            return response
        elif cmd == "reset":
            # Clear all assessment state
            session_id = self.assessment.runner._state.session_id if self.assessment.runner and self.assessment.runner._state else "unknown"
            if self.assessment.runner:
                self.assessment.runner._clear_state()
            self.assessment.runner = None
            self.assessment.timing = False
            self.assessment.timer_start = None
            self.assessment.pending_session = None
            return f"Assessment cleared. Session {session_id} cancelled. Say session 1, 2, or 3 to start fresh."

        # Handle timed test control
        if self.assessment.timing:
            elapsed = time.monotonic() - self.assessment.timer_start
            max_time = self.assessment.runner.get_max_time()

            # Auto-stop if max time reached
            if elapsed >= max_time:
                self.assessment.timing = False
                self.assessment.timer_start = None
                response = await self.assessment.runner.record_result(float(max_time))
                return f"{int(max_time)} seconds. Maximum reached. " + response.split(". ", 1)[-1] if ". " in response else response

            # Timer is running - check for stop command
            if self._is_timer_stop(text):
                self.assessment.timing = False
                self.assessment.timer_start = None
                elapsed_rounded = round(elapsed, 1)
                response = await self.assessment.runner.record_result(elapsed_rounded)
                return response
            else:
                # Still timing, ignore other input
                return f"Still timing. {int(elapsed)} seconds. Say stop when done."

        # Check for timer start (timed tests only)
        if self.assessment.runner.current_test_is_timed():
            if self._is_timer_start(text):
                self.assessment.timing = True
                self.assessment.timer_start = time.monotonic()
                return await self.assessment.runner.start_timer()

        # Check for countdown start
        if self.assessment.runner.current_test_is_countdown():
            if self._is_timer_start(text):
                # For countdown tests, start timer and wait for reps count
                self.assessment.timing = True
                self.assessment.timer_start = time.monotonic()
                countdown = self.assessment.runner.get_countdown_seconds()
                return f"Timing. {countdown} seconds. Count your reps."

        # Parse and record the input
        return await self.assessment.runner.parse_and_record(text)

    async def _check_assessment_timer_beeps(self) -> list[int]:
        """Check if any beep intervals have been passed. Returns list of passed intervals."""
        if not self.assessment.timing or not self.assessment.timer_start:
            return []

        if not self.assessment.runner:
            return []

        elapsed = time.monotonic() - self.assessment.timer_start
        beep_intervals = self.assessment.runner.get_beep_intervals()

        # Track which beeps have been played (stored on runner for simplicity)
        if not hasattr(self, "_beeps_played"):
            self._beeps_played = set()

        new_beeps = []
        for interval in beep_intervals:
            if elapsed >= interval and interval not in self._beeps_played:
                new_beeps.append(interval)
                self._beeps_played.add(interval)

        # Reset beeps when timer stops
        if not self.assessment.timing:
            self._beeps_played = set()

        return new_beeps

    async def _check_assessment_timer_max(self) -> tuple[bool, float]:
        """Check if max time reached. Returns (reached, elapsed)."""
        if not self.assessment.timing or not self.assessment.timer_start:
            return False, 0.0

        if not self.assessment.runner:
            return False, 0.0

        elapsed = time.monotonic() - self.assessment.timer_start
        max_time = self.assessment.runner.get_max_time()

        if elapsed >= max_time:
            return True, float(max_time)

        return False, elapsed

    def process_audio(self):
        """Process audio file through ATLAS pipeline."""
        from atlas.voice.intent_dispatcher import IntentDispatcher, _make_decision

        # Read audio
        audio = np.fromfile(AUDIO_IN_FILE, dtype=np.float32)
        AUDIO_IN_FILE.unlink()

        print(f"\nProcessing {len(audio) / SAMPLE_RATE_IN:.1f}s of audio...")

        # STT
        start = time.perf_counter()
        transcription = self.stt.transcribe(audio, SAMPLE_RATE_IN)
        stt_time = (time.perf_counter() - start) * 1000
        print(f"You: {transcription.text}")
        print(f"  [STT: {stt_time:.0f}ms]")

        if not transcription.text.strip():
            print("  [No speech detected]")
            self.write_status("DONE")
            return

        # Route
        decision = self.router.classify(transcription.text)
        print(f"  [Route: {decision.tier.value}, conf: {decision.confidence:.2f}]")

        # Collect all audio to send back
        all_audio = []
        tts_sample_rate = 24000  # Will be updated by actual TTS output
        tts_time = 0  # Track TTS timing for launcher

        # Check intents BEFORE LLM routing
        response_text = ""
        action_type = "query"  # Default action type
        saved_to = ""  # Where data was saved (if applicable)

        # Try intent dispatch first
        dispatcher = IntentDispatcher(self)
        intent_result = dispatcher.dispatch(transcription.text)

        if intent_result:
            # Intent was handled - extract results
            response_text = intent_result.response_text
            action_type = intent_result.action_type
            saved_to = intent_result.saved_to
            if intent_result.tier_override:
                decision = _make_decision(intent_result.tier_override)
        else:
            # No intent matched - fall through to LLM
            print("ATLAS: ", end="", flush=True)

            # Inject session context for LLM queries
            session_context = self.session_buffer.format_for_llm()
            if session_context:
                augmented_query = f"{session_context}\n\nCurrent query: {transcription.text}"
            else:
                augmented_query = transcription.text

            async def get_response():
                nonlocal response_text
                try:
                    async for token in self.router.route_and_stream(
                        augmented_query,  # Use augmented query with context
                        temperature=0.7,
                        max_tokens=100,  # Keep responses short for voice
                    ):
                        response_text += token
                        print(token, end="", flush=True)
                except Exception as api_error:
                    # API failed - try local LLM
                    logger.warning(f"API error: {api_error}, trying local LLM...")
                    print(f"\n  [API error: {type(api_error).__name__}, trying local...]", flush=True)
                    response_text = ""
                    try:
                        # OllamaClient uses generate() not chat()
                        local_response = self.llm.generate(
                            prompt=transcription.text,
                            system=SYSTEM_PROMPT,
                            temperature=0.7,
                            max_tokens=100
                        )
                        response_text = local_response.content
                        print(response_text, flush=True)
                    except Exception as local_error:
                        logger.error(f"Local LLM also failed: {local_error}")
                        response_text = f"Both cloud and local LLM failed. Cloud: {type(api_error).__name__}. Local: {type(local_error).__name__}"
                        print(response_text)

            async def get_response_with_timeout():
                try:
                    await asyncio.wait_for(get_response(), timeout=30.0)
                except asyncio.TimeoutError:
                    nonlocal response_text
                    response_text = "Sorry, I took too long. Try again."
                    print(response_text)

            asyncio.run(get_response_with_timeout())
            print()

        # TTS for response - check for voice preference change
        if response_text.strip():
            new_voice = self._read_voice_preference()
            if new_voice != self.current_voice:
                print(f"  [Voice changed: {self.current_voice} -> {new_voice}]")
                self.current_voice = new_voice
                self.tts = self._get_tts_for_voice(new_voice)
                self.tts._ensure_loaded()

            start = time.perf_counter()
            result = self.tts.synthesize(response_text)
            tts_time = (time.perf_counter() - start) * 1000
            tts_sample_rate = result.sample_rate
            print(f"  [TTS: {tts_time:.0f}ms, {tts_sample_rate}Hz]")
            all_audio.append(result.audio)

        # Add exchange to session buffer for future context
        if response_text.strip():
            self.session_buffer.add_exchange(
                user_text=transcription.text,
                atlas_response=response_text,
                intent_type=action_type,
            )

        # Write combined audio to output file with metadata
        if all_audio:
            combined = np.concatenate(all_audio)
            # Add 200ms silence tail to prevent audio cutoff during playback
            silence_tail = np.zeros(int(0.2 * tts_sample_rate), dtype=np.float32)
            combined = np.concatenate([combined, silence_tail])
            combined.astype(np.float32).tofile(AUDIO_OUT_FILE)
            self.write_metadata(tts_sample_rate)  # Tell Windows the correct sample rate
            print(f"  [Response: {len(combined) / tts_sample_rate:.1f}s audio @ {tts_sample_rate}Hz]")

        # Write session status for Windows launcher
        self._write_session_status(
            tier=decision.tier.value,
            confidence=decision.confidence,
            cost=0.0,  # LOCAL is free; HAIKU cost tracked separately by router
            user_text=transcription.text,
            atlas_response=response_text,
            stt_ms=stt_time,
            tts_ms=tts_time,
            action=action_type,
            saved_to=saved_to
        )

        self.write_status("DONE")

    async def _sync_garmin_on_startup(self):
        """Sync Garmin data on server startup (replaces cron job)."""
        try:
            from atlas.health.garmin import GarminService, is_garmin_auth_valid
            from atlas.health.morning_sync import sync_and_cache_morning_status
            from atlas.health.workout_lookup import get_current_week, is_deload_week

            if not is_garmin_auth_valid():
                print("  [Garmin auth not valid - skipping sync]")
                return

            print("  Syncing Garmin data...", flush=True)
            await sync_and_cache_morning_status()

            # Show current week info
            week = get_current_week()
            deload = is_deload_week()
            week_info = f"Week {week}" + (" (DELOAD)" if deload else "")
            print(f"  [Garmin synced. Phase 1 {week_info}]")

        except Exception as e:
            print(f"  [Garmin sync failed: {e}]")

    def run(self):
        """Main loop."""
        self.setup()

        print("\n" + "=" * 50)
        print("ATLAS Bridge Server (File-based)")
        print("=" * 50)

        # Sync Garmin data on startup (replaces 5am cron job)
        asyncio.run(self._sync_garmin_on_startup())

        print("Waiting for Windows client...")
        print("=" * 50 + "\n")

        try:
            while True:
                cmd = self.read_command()

                if cmd == "PING":
                    print("[PING received]")
                    self.write_status("PONG")

                elif cmd == "PROCESS":
                    print(f"[PROCESS received]", flush=True)

                    # Wait for audio file with retry (cross-filesystem sync delay)
                    retries = 0
                    max_retries = 30  # 3 seconds max wait
                    while not AUDIO_IN_FILE.exists() and retries < max_retries:
                        time.sleep(0.1)
                        retries += 1

                    if AUDIO_IN_FILE.exists():
                        if retries > 0:
                            print(f"  [Audio file appeared after {retries * 100}ms]", flush=True)
                        try:
                            self.process_audio()
                        except Exception as e:
                            print(f"\n*** PROCESS ERROR: {type(e).__name__}: {e} ***", flush=True)
                            import traceback
                            traceback.print_exc()
                            # Write error to session status so UI shows something
                            self._write_session_status(
                                tier="ERROR",
                                confidence=0.0,
                                user_text="[processing failed]",
                                atlas_response=f"Error: {type(e).__name__}: {str(e)[:100]}",
                                action="error"
                            )
                            self.write_status("DONE")  # Tell Windows we're done despite error
                    else:
                        print(f"[PROCESS but no audio file after {max_retries * 100}ms wait]", flush=True)
                        print(f"  [Expected at: {AUDIO_IN_FILE}]", flush=True)
                        # Show what files DO exist
                        try:
                            existing = list(BRIDGE_DIR.glob("*"))
                            print(f"  [Bridge dir contents: {[f.name for f in existing]}]", flush=True)
                        except Exception as e:
                            print(f"  [Cannot list bridge dir: {e}]", flush=True)
                        self.write_status("DONE")

                elif cmd == "QUIT":
                    print("[QUIT received]")
                    # Clear timer state before shutdown
                    self._clear_timer_from_session_status()
                    break

                # UI button commands (Command Centre)
                # NOTE: TTS spawned in background thread to avoid blocking command polling
                elif cmd == "PAUSE_ROUTINE":
                    print("[PAUSE_ROUTINE received from UI]")
                    if self.routine.active and not self.routine.paused:
                        try:
                            msg = asyncio.run(self._handle_routine_pause())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[PAUSE_ROUTINE ERROR: {e}]")
                    elif self.workout.active and not self.workout.paused and not self.routine.active:
                        # Handle workout pause when no routine is active
                        try:
                            msg = asyncio.run(self._handle_workout_pause())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[PAUSE_WORKOUT ERROR: {e}]")
                    COMMAND_FILE.unlink(missing_ok=True)

                elif cmd == "RESUME_ROUTINE":
                    print("[RESUME_ROUTINE received from UI]")
                    if self.routine.active and self.routine.paused:
                        try:
                            msg = asyncio.run(self._handle_routine_resume())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[RESUME_ROUTINE ERROR: {e}]")
                    elif self.workout.active and self.workout.paused and not self.routine.active:
                        # Handle workout resume when no routine is active
                        try:
                            msg = asyncio.run(self._handle_workout_resume())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[RESUME_WORKOUT ERROR: {e}]")
                    COMMAND_FILE.unlink(missing_ok=True)

                elif cmd == "SKIP_EXERCISE":
                    print(f"[SKIP_EXERCISE received from UI - routine_active={self.routine.active}, "
                          f"routine_pending={self.routine.exercise_pending}, "
                          f"auto_advance={self.routine.auto_advance_pending}, "
                          f"workout_active={self.workout.active}, "
                          f"workout_pending={self.workout.exercise_pending}]")

                    # Check WORKOUT first (takes priority over stale routine state)
                    if self.workout.active:
                        try:
                            msg = asyncio.run(self._handle_workout_skip())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[SKIP_EXERCISE ERROR: {e}]")
                    elif self.routine.active or self.routine.auto_advance_pending or self.routine.timer_active:
                        # Cancel auto-advance if pending
                        self.routine.auto_advance_pending = False
                        self.routine.auto_advance_start = None
                        self.routine.auto_advance_phase = None
                        self.routine.paused = False
                        self.routine.active = True
                        try:
                            msg = asyncio.run(self._handle_routine_skip())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[SKIP_EXERCISE ERROR: {e}]")
                    else:
                        print("[SKIP_EXERCISE: Nothing active to skip]")
                    COMMAND_FILE.unlink(missing_ok=True)

                elif cmd == "SET_COMPLETE":
                    print(f"[SET_COMPLETE received from UI - workout_active={self.workout.active}, "
                          f"set_active={self.workout.set_active}]")

                    if self.workout.active and self.workout.set_active:
                        try:
                            msg = asyncio.run(self._handle_workout_set_done())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[SET_COMPLETE ERROR: {e}]")
                    else:
                        print("[SET_COMPLETE: No active set to complete]")
                    COMMAND_FILE.unlink(missing_ok=True)

                elif cmd == "STOP_ROUTINE":
                    print(f"[STOP_ROUTINE received from UI - routine_active={self.routine.active}, "
                          f"workout_active={self.workout.active}, auto_advance={self.routine.auto_advance_pending}]")

                    # Check if ANY routine/workout state is active
                    routine_state_active = (
                        self.routine.active or
                        self.routine.auto_advance_pending or
                        self.routine.timer_active or
                        self.routine.exercise_pending
                    )

                    if routine_state_active:
                        print("[STOP_ROUTINE: Stopping routine...]")
                        try:
                            msg = asyncio.run(self._handle_routine_stop())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                            print("[STOP_ROUTINE: Routine stopped successfully, server continues running]")
                        except Exception as e:
                            print(f"[STOP_ROUTINE ERROR: {e}]")
                            import traceback
                            traceback.print_exc()
                            # Force reset state even on error
                            self._force_reset_routine_state()
                    elif self.workout.active:
                        print("[STOP_ROUTINE: Stopping workout...]")
                        try:
                            msg = asyncio.run(self._handle_workout_stop())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                            print("[STOP_ROUTINE: Workout stopped successfully, server continues running]")
                        except Exception as e:
                            print(f"[STOP_ROUTINE ERROR: {e}]")
                            import traceback
                            traceback.print_exc()
                            # Force reset state even on error
                            self._force_reset_workout_state()
                    else:
                        print("[STOP_ROUTINE: Nothing active to stop - forcing state reset]")
                        self._force_reset_routine_state()
                        self._force_reset_workout_state()

                    print("[STOP_ROUTINE: Command processed, continuing main loop]")
                    COMMAND_FILE.unlink(missing_ok=True)

                elif cmd == "LOG_ROUTINE":
                    print(f"[LOG_ROUTINE received from UI - routine_finished={self.routine.routine_finished}]")

                    if self.routine.routine_finished:
                        try:
                            msg = self._handle_log_routine()
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                            print("[LOG_ROUTINE: Routine logged successfully]")
                        except Exception as e:
                            print(f"[LOG_ROUTINE ERROR: {e}]")
                            import traceback
                            traceback.print_exc()
                            # Reset state anyway
                            self.routine.reset()
                            self._clear_timer_from_session_status()
                    else:
                        print("[LOG_ROUTINE: No routine awaiting logging]")

                    COMMAND_FILE.unlink(missing_ok=True)

                elif cmd == "LOG_WORKOUT":
                    print(f"[LOG_WORKOUT received from UI - workout_finished={self.workout.workout_finished}]")

                    if self.workout.workout_finished:
                        try:
                            msg = asyncio.run(self._handle_workout_completion("finished workout", has_issues=False))
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                            print("[LOG_WORKOUT: Workout logged successfully]")
                        except Exception as e:
                            print(f"[LOG_WORKOUT ERROR: {e}]")
                            import traceback
                            traceback.print_exc()
                            # Reset state anyway
                            self._force_reset_workout_state()
                    else:
                        print("[LOG_WORKOUT: No workout awaiting logging]")

                    COMMAND_FILE.unlink(missing_ok=True)

                elif cmd == "START_TIMER":
                    print(f"[START_TIMER received from UI - routine_active={self.routine.active}, "
                          f"pending={self.routine.exercise_pending}, auto_advance={self.routine.auto_advance_pending}, "
                          f"workout_active={self.workout.active}, workout_pending={self.workout.exercise_pending}]")
                    # Check WORKOUT first (takes priority over stale routine state)
                    if self.workout.active and self.workout.exercise_pending:
                        # Start workout set (equivalent to saying "ready")
                        try:
                            msg = asyncio.run(self._handle_workout_ready(""))
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[START_WORKOUT ERROR: {e}]")
                    elif self.routine.active and self.routine.exercise_pending:
                        # Start the timer for current exercise
                        try:
                            msg = asyncio.run(self._handle_routine_ready())
                            Thread(target=self._autonomous_speak, args=(msg,), daemon=True).start()
                        except Exception as e:
                            print(f"[START_TIMER ERROR: {e}]")
                    elif self.routine.auto_advance_pending:
                        # Skip auto-advance and start immediately
                        # During 'completed' phase, state isn't advanced yet
                        if self.routine.auto_advance_phase == 'completed':
                            # Advance to next exercise first
                            try:
                                asyncio.run(self._advance_routine_exercise_silent())
                            except Exception as e:
                                print(f"[START_TIMER: Advance failed: {e}]")

                        self.routine.auto_advance_pending = False
                        self.routine.auto_advance_phase = None
                        self.routine.auto_advance_start = None

                        # Start the timer (this speaks "Go. X seconds.")
                        self._auto_start_routine_timer()
                    COMMAND_FILE.unlink(missing_ok=True)

                # AUTONOMOUS TIMER CHECK - runs every 100ms regardless of user input
                try:
                    self._check_and_play_timers()
                except Exception as e:
                    logger.error(f"[TIMER-AUTO] Timer check failed: {e}")

                time.sleep(0.1)  # Poll every 100ms

        except KeyboardInterrupt:
            print("\n\nShutting down...")


def main():
    # Enable INFO logging for diagnostic output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    server = BridgeFileServer()
    server.run()


if __name__ == "__main__":
    main()
