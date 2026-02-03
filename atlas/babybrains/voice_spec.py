"""
Baby Brains Voice Spec Loader

Loads the BabyBrains-Writer voice specification and extracts
relevant sections for comment/script generation.
"""

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default voice spec location
DEFAULT_VOICE_SPEC_PATH = Path("/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md")

# Human story profile location
DEFAULT_HUMAN_STORY_PATH = Path(__file__).parent.parent.parent / "config" / "babybrains" / "human_story.json"

# Opening and closing tag patterns for non-greedy section extraction
_OPEN_TAG = re.compile(r"<([a-z_]+)>")
_CLOSE_TAG_FMT = "</{name}>"

# Key sections relevant to different generation tasks
#
# IMPORTANT: These must match actual XML tags in BabyBrains-Writer.md
# Verified tags (grep -n "^<[a-z_]*>"):
#   L16: voice_dna (contains australian_authenticity_strict as nested tag at L39)
#   L57: ai_detection_avoidance
#   L180: format_adaptations
#   L312: evidence_framework
#   L448: neuro_translation_protocols
#   L452: safety_compliance
#   L627: few_shot_examples
#   L728: content_rules
#
# NOTE: australian_authenticity_strict is NESTED inside voice_dna (L39-53).
# Requesting both would produce duplicated content (~500 chars overlap).
# We include it only in COMMENT_SECTIONS where voice_dna is also present,
# but the parser extracts nested sections independently.

COMMENT_SECTIONS = [
    "voice_dna",
    "ai_detection_avoidance",
    "australian_authenticity_strict",  # Nested in voice_dna but extracted separately
    "content_rules",
]

SCRIPT_SECTIONS = [
    "voice_dna",                       # Contains australian_authenticity_strict
    "ai_detection_avoidance",
    "format_adaptations",
    "neuro_translation_protocols",     # Fixed: was neural_science_bridge
    "evidence_framework",
    "safety_compliance",               # Added: critical for content safety
    "content_rules",
    # NOTE: few_shot_examples (~100 lines, 3-4KB) EXCLUDED to manage prompt size
    # Inject skill-specific examples directly in skill prompts instead
]

FULL_SECTIONS = [
    "voice_dna",
    "ai_detection_avoidance",
    "format_adaptations",
    "evidence_framework",
    "neuro_translation_protocols",     # Fixed: was neural_science_bridge
    "safety_compliance",
    "content_rules",
    "few_shot_examples",               # Only in FULL context (for reference docs)
]


class VoiceSpec:
    """
    Loader for the BabyBrains-Writer voice specification.

    Parses the 1712-line markdown file and extracts sections
    by XML-style tag names for targeted prompt construction.
    """

    def __init__(self, spec_path: Optional[Path] = None):
        self.spec_path = spec_path or DEFAULT_VOICE_SPEC_PATH
        self._raw: Optional[str] = None
        self._sections: dict[str, str] = {}

    def load(self) -> bool:
        """
        Load and parse the voice spec file.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.spec_path.exists():
            logger.warning(f"Voice spec not found: {self.spec_path}")
            return False

        self._raw = self.spec_path.read_text(encoding="utf-8")
        self._parse_sections()
        logger.info(f"Voice spec loaded: {len(self._sections)} sections from {self.spec_path}")
        return True

    def _parse_sections(self) -> None:
        """Parse XML-style sections from the raw spec.

        Handles nested tags by finding each opening tag and its
        corresponding closing tag, extracting the content between.
        Inner sections are stored independently from their parents.
        """
        if self._raw is None:
            return

        self._sections = {}
        for match in _OPEN_TAG.finditer(self._raw):
            name = match.group(1)
            start = match.end()
            close_tag = _CLOSE_TAG_FMT.format(name=name)
            close_idx = self._raw.find(close_tag, start)
            if close_idx == -1:
                continue
            content = self._raw[start:close_idx].strip()
            self._sections[name] = content

    @property
    def is_loaded(self) -> bool:
        return self._raw is not None

    @property
    def section_names(self) -> list[str]:
        return list(self._sections.keys())

    def get_section(self, name: str) -> Optional[str]:
        """Get a specific section by name."""
        if not self.is_loaded:
            self.load()
        return self._sections.get(name)

    def get_sections(self, names: list[str]) -> str:
        """
        Get multiple sections concatenated for prompt injection.

        Args:
            names: List of section names to extract

        Returns:
            Concatenated section text with headers
        """
        if not self.is_loaded:
            self.load()

        parts = []
        for name in names:
            content = self._sections.get(name)
            if content:
                parts.append(f"## {name.replace('_', ' ').title()}\n\n{content}")
            else:
                logger.debug(f"Section not found: {name}")

        return "\n\n---\n\n".join(parts)

    def get_comment_context(self) -> str:
        """Get voice spec context optimized for comment generation."""
        return self.get_sections(COMMENT_SECTIONS)

    def get_script_context(self) -> str:
        """Get voice spec context optimized for script generation."""
        return self.get_sections(SCRIPT_SECTIONS)

    def get_full_context(self) -> str:
        """Get the complete voice spec context."""
        return self.get_sections(FULL_SECTIONS)

    def get_raw(self) -> Optional[str]:
        """Get the raw, unparsed voice spec text."""
        if not self.is_loaded:
            self.load()
        return self._raw


def load_human_story(story_path: Optional[Path] = None) -> dict:
    """
    Load the human story profile for comment personalization.

    Args:
        story_path: Optional path to human_story.json

    Returns:
        Dictionary with human story fields, or empty dict if not found
    """
    import json

    path = story_path or DEFAULT_HUMAN_STORY_PATH
    if not path.exists():
        logger.warning(f"Human story not found: {path}")
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Check if the profile has been completed
        if data.get("status", "").startswith("INCOMPLETE"):
            logger.warning("Human story profile is INCOMPLETE -- personal-angle comments disabled")
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load human story: {e}")
        return {}


# Module-level singleton for reuse
_voice_spec: Optional[VoiceSpec] = None


def get_voice_spec() -> VoiceSpec:
    """Get or create the voice spec singleton."""
    global _voice_spec
    if _voice_spec is None:
        _voice_spec = VoiceSpec()
        _voice_spec.load()
    return _voice_spec
