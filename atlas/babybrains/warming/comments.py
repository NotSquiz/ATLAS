"""
Baby Brains Comment Generator

Generates transcript-aware, BB-voice comments using Anthropic Sonnet API.
Comments are drafted for HUMAN posting (not automated).

Three layers:
1. Knowledge Base: video transcript + cross-referenced knowledge
2. Voice Spec: BabyBrains-Writer voice specification
3. Human Story: personal element when appropriate
"""

import json
import logging
import os
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Sonnet model for automated comment generation
SONNET_MODEL = "claude-sonnet-4-20250514"

# Comment quality gate checks
FORBIDDEN_PATTERNS = [
    r"\u2014",          # em-dash
    r"\u2013",          # en-dash (also avoid)
    r"Moreover,",
    r"Furthermore,",
    r"Additionally,",
    r"In conclusion,",
    r"It's worth noting",
    r"Interestingly,",
    r"Importantly,",
]

AU_VOCABULARY_CHECKS = {
    "mom": "mum",
    "diaper": "nappy",
    "stroller": "pram",
    "crib": "cot",
    "pacifier": "dummy",
    "preschool": "kindy",
    "pediatrician": "paediatrician",
}


@dataclass
class CommentDraft:
    """A generated comment draft ready for human review."""

    video_id: str
    video_title: Optional[str] = None
    transcript_summary: Optional[str] = None
    comment_text: str = ""
    has_personal_angle: bool = False
    quality_score: float = 0.0
    quality_issues: list[str] = field(default_factory=list)
    model_used: str = ""
    tokens_used: int = 0

    @property
    def passes_quality_gate(self) -> bool:
        return len(self.quality_issues) == 0 and len(self.comment_text) > 0


class CommentGenerator:
    """
    Generates BB-voice comments using Sonnet API.

    Uses three layers:
    - Voice spec (from BabyBrains-Writer.md)
    - Video transcript (from youtube-transcript-api)
    - Human story (from human_story.json)
    """

    def __init__(
        self,
        voice_spec_context: Optional[str] = None,
        human_story: Optional[dict] = None,
    ):
        self._voice_spec_context = voice_spec_context
        self._human_story = human_story
        self._client = None

    def _get_client(self):
        """Lazy-init Anthropic client."""
        if self._client is not None:
            return self._client

        try:
            import anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY required for comment generation")

            self._client = anthropic.Anthropic(api_key=api_key)
            return self._client
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

    def _load_voice_spec(self) -> str:
        """Load voice spec context if not already provided."""
        if self._voice_spec_context:
            return self._voice_spec_context

        from atlas.babybrains.voice_spec import get_voice_spec

        spec = get_voice_spec()
        self._voice_spec_context = spec.get_comment_context()
        return self._voice_spec_context

    def _load_human_story(self) -> dict:
        """Load human story if not already provided."""
        if self._human_story:
            return self._human_story

        from atlas.babybrains.voice_spec import load_human_story

        self._human_story = load_human_story()
        return self._human_story

    def _build_system_prompt(self) -> str:
        """Build the system prompt with voice spec context."""
        voice_spec = self._load_voice_spec()

        return f"""You are the BabyBrains comment writer. You write YouTube and Instagram comments
that sound like a real Australian parent who knows their stuff about child development and Montessori.

VOICE SPECIFICATION:
{voice_spec}

COMMENT RULES:
- Em-dashes (--) are FORBIDDEN. Use commas, full stops, or restructure.
- No formal transitions (Moreover, Furthermore, Additionally)
- Always use contractions (you're, it's, we've, that's)
- Australian vocabulary: mum (not mom), nappy (not diaper), pram (not stroller), cot (not crib)
- Australian spelling: colour, organise, behaviour, realise
- Grade 8 reading level. Keep it simple.
- Vary length: some short (1-2 sentences), some medium (3-4 sentences)
- Never preachy, never guru-positioning
- Cost-of-living aware (lead with free/DIY when relevant)
- Reference the actual video content (you'll be given the transcript)
- No hashtags in comments
- No links in comments
- No emojis overload (0-1 emoji max)
"""

    def _build_comment_prompt(
        self,
        transcript: str,
        video_title: str,
        include_personal: bool = False,
        platform: str = "youtube",
        max_length: int = 500,
    ) -> str:
        """Build the user prompt for comment generation."""
        human_story = self._load_human_story()
        story_status = human_story.get("bb_human_story", {}).get("status", "")

        personal_instruction = ""
        if include_personal and not story_status.startswith("INCOMPLETE"):
            story = human_story.get("bb_human_story", {})
            personal_instruction = f"""
Include a personal element in this comment. You are:
- {story.get('who', 'A dad in Australia')}
- With a {story.get('child', 'young child')}
- Tone: {story.get('tone', 'Learning alongside other parents')}

Use phrases like "We found this with our little one too..." or "As a dad trying to figure this out..."
"""
        elif include_personal:
            # Story not complete yet, skip personal angle
            personal_instruction = ""
            include_personal = False

        return f"""Write a single YouTube comment for this video.

VIDEO TITLE: {video_title}

VIDEO TRANSCRIPT (key excerpt):
{transcript[:3000]}

{personal_instruction}

REQUIREMENTS:
- Maximum {max_length} characters
- Reference something specific from the video (show you actually watched it)
- Sound like a real person, not a brand
- Add genuine value (insight, question, or shared experience)
- No em-dashes
- Australian English
- Platform: {platform}

Write ONLY the comment text. No preamble, no quotes, no explanation.
"""

    async def generate_comment(
        self,
        transcript: str,
        video_title: str,
        video_id: str = "",
        platform: str = "youtube",
        max_length: int = 500,
    ) -> CommentDraft:
        """
        Generate a BB-voice comment for a video.

        Args:
            transcript: Video transcript text
            video_title: Title of the video
            video_id: YouTube video ID
            platform: Target platform
            max_length: Maximum comment length in characters

        Returns:
            CommentDraft with generated comment and quality assessment
        """
        # Decide whether to include personal angle (~35% of the time)
        include_personal = random.random() < 0.35

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_comment_prompt(
            transcript=transcript,
            video_title=video_title,
            include_personal=include_personal,
            platform=platform,
            max_length=max_length,
        )

        try:
            client = self._get_client()
            response = client.messages.create(
                model=SONNET_MODEL,
                max_tokens=300,
                temperature=0.8,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            comment_text = response.content[0].text.strip()
            tokens = response.usage.input_tokens + response.usage.output_tokens

            # Run quality gate
            issues = self._quality_check(comment_text)

            return CommentDraft(
                video_id=video_id,
                video_title=video_title,
                transcript_summary=transcript[:200] if transcript else None,
                comment_text=comment_text,
                has_personal_angle=include_personal,
                quality_score=1.0 if not issues else max(0.0, 1.0 - len(issues) * 0.2),
                quality_issues=issues,
                model_used=SONNET_MODEL,
                tokens_used=tokens,
            )

        except Exception as e:
            logger.error(f"Comment generation failed: {e}")
            return CommentDraft(
                video_id=video_id,
                video_title=video_title,
                quality_issues=[f"Generation failed: {e}"],
            )

    def _quality_check(self, text: str) -> list[str]:
        """
        Run quality gate checks on a generated comment.

        Returns list of issues found (empty = passes).
        """
        issues = []

        # Check forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text):
                issues.append(f"Contains forbidden pattern: {pattern}")

        # Check for US English vocabulary
        text_lower = text.lower()
        for us_word, au_word in AU_VOCABULARY_CHECKS.items():
            # Check for standalone word (not as substring)
            if re.search(rf"\b{us_word}\b", text_lower):
                issues.append(f"US English: '{us_word}' should be '{au_word}'")

        # Check length
        if len(text) > 500:
            issues.append(f"Too long: {len(text)} chars (max 500)")

        if len(text) < 10:
            issues.append(f"Too short: {len(text)} chars")

        # Check for excessive emojis
        emoji_count = len(re.findall(r"[\U0001F300-\U0001F9FF]", text))
        if emoji_count > 2:
            issues.append(f"Too many emojis: {emoji_count} (max 2)")

        return issues

    def quality_check(self, text: str) -> list[str]:
        """Public quality check method for external use."""
        return self._quality_check(text)
