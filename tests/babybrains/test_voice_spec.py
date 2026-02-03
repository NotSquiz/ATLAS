"""Tests for Baby Brains voice spec loader."""

import json
from pathlib import Path

import pytest

from atlas.babybrains.voice_spec import VoiceSpec, load_human_story


@pytest.fixture
def sample_voice_spec(tmp_path):
    """Create a minimal voice spec file for testing."""
    spec_content = """---
name: BabyBrains-Writer
---

<system_prompt>
<role>
You are the Senior Content Architect for Baby Brains.
</role>

<voice_dna>
Friendly Expert: A warm, knowledgeable Australian parent.
Australian vocabulary: mum, nappy, pram, cot, dummy.
Grade 8 reading level.
<australian_authenticity_strict>
Use aussie slang. Cost of living awareness.
</australian_authenticity_strict>
</voice_dna>

<ai_detection_avoidance>
Em-dashes FORBIDDEN (the #1 AI tell).
No formal transitions (Moreover, Furthermore).
Contractions always (you're, it's, we've).
</ai_detection_avoidance>

<content_rules>
No medical claims. Evidence-anchored. Montessori authenticity.
</content_rules>

<format_adaptations>
21s scripts: 55-65 words. 60s scripts: 160-185 words.
</format_adaptations>

<neuro_translation_protocols>
synaptic pruning = gardening the brain; myelination = insulating the wires.
</neuro_translation_protocols>

<evidence_framework>
Research strongly shows for high certainty. Early research suggests for preliminary.
</evidence_framework>

<safety_compliance>
No choking hazards. Always supervise. Redirect to healthcare provider.
</safety_compliance>

<few_shot_examples>
Example 1: A good script.
Example 2: Another good script.
Example 3: A third example.
</few_shot_examples>
</system_prompt>
"""
    spec_path = tmp_path / "BabyBrains-Writer.md"
    spec_path.write_text(spec_content)
    return spec_path


@pytest.fixture
def sample_human_story(tmp_path):
    """Create a sample human story file."""
    story = {
        "bb_human_story": {
            "who": "A dad in Australia",
            "child": "16-month-old son",
            "status": "INCOMPLETE - DO NOT USE FOR COMMENT GENERATION UNTIL CRAFTED",
        },
        "comment_rules": {
            "personal_angle_percentage": 0.35,
        },
    }
    story_path = tmp_path / "human_story.json"
    story_path.write_text(json.dumps(story))
    return story_path


class TestVoiceSpec:
    """Test voice spec loading and section extraction."""

    def test_load_spec(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        assert spec.load() is True
        assert spec.is_loaded is True

    def test_load_missing_file(self, tmp_path):
        spec = VoiceSpec(tmp_path / "nonexistent.md")
        assert spec.load() is False
        assert spec.is_loaded is False

    def test_section_names(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        names = spec.section_names
        assert "voice_dna" in names
        assert "ai_detection_avoidance" in names
        assert "australian_authenticity_strict" in names  # Updated: was australian_literary_voice
        assert "content_rules" in names

    def test_get_section(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        voice_dna = spec.get_section("voice_dna")
        assert voice_dna is not None
        assert "Australian" in voice_dna
        assert "mum" in voice_dna

    def test_get_missing_section(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        assert spec.get_section("nonexistent") is None

    def test_get_sections(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        combined = spec.get_sections(["voice_dna", "ai_detection_avoidance"])
        assert "Voice Dna" in combined
        assert "Ai Detection Avoidance" in combined
        assert "Em-dashes FORBIDDEN" in combined

    def test_get_comment_context(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        ctx = spec.get_comment_context()
        assert "mum" in ctx
        assert "Em-dashes" in ctx

    def test_get_script_context(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        ctx = spec.get_script_context()
        assert "mum" in ctx
        assert "55-65 words" in ctx

    def test_get_raw(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        raw = spec.get_raw()
        assert raw is not None
        assert "BabyBrains-Writer" in raw

    def test_auto_load_on_get_section(self, sample_voice_spec):
        spec = VoiceSpec(sample_voice_spec)
        # Don't call load() explicitly
        voice_dna = spec.get_section("voice_dna")
        assert voice_dna is not None


class TestHumanStory:
    """Test human story profile loading."""

    def test_load_human_story(self, sample_human_story):
        story = load_human_story(sample_human_story)
        assert "bb_human_story" in story
        assert story["bb_human_story"]["who"] == "A dad in Australia"

    def test_load_missing_story(self, tmp_path):
        story = load_human_story(tmp_path / "nonexistent.json")
        assert story == {}

    def test_incomplete_story_detected(self, sample_human_story):
        story = load_human_story(sample_human_story)
        assert story["bb_human_story"]["status"].startswith("INCOMPLETE")


class TestVoiceSpecSectionConstants:
    """Test that section constants match actual BabyBrains-Writer.md tags."""

    def test_script_sections_returns_expected_sections(self, sample_voice_spec):
        """get_script_context should return 7 sections (no duplication)."""
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        ctx = spec.get_script_context()
        # Should have these sections based on SCRIPT_SECTIONS constant
        assert "Voice Dna" in ctx
        assert "Ai Detection Avoidance" in ctx
        assert "Format Adaptations" in ctx
        assert "Neuro Translation Protocols" in ctx
        assert "Evidence Framework" in ctx
        assert "Safety Compliance" in ctx
        assert "Content Rules" in ctx

    def test_script_context_excludes_few_shot_examples(self, sample_voice_spec):
        """few_shot_examples should NOT be in SCRIPT_SECTIONS (too large)."""
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        ctx = spec.get_script_context()
        assert "Few Shot Examples" not in ctx

    def test_full_context_includes_few_shot_examples(self, sample_voice_spec):
        """FULL_SECTIONS should include few_shot_examples."""
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        ctx = spec.get_full_context()
        assert "Few Shot Examples" in ctx

    def test_nested_section_parsed_independently(self, sample_voice_spec):
        """australian_authenticity_strict inside voice_dna is extracted as own section."""
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        # Verify the nested section is parsed
        aus_section = spec.get_section("australian_authenticity_strict")
        assert aus_section is not None
        assert "aussie slang" in aus_section

    def test_no_duplicate_content_in_script_context(self, sample_voice_spec):
        """Script context should not have duplicated nested content."""
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        ctx = spec.get_script_context()
        # australian_authenticity_strict is inside voice_dna, so we check
        # that "aussie slang" appears only once (from voice_dna, not separately)
        # Since SCRIPT_SECTIONS doesn't include australian_authenticity_strict,
        # it should only appear once via voice_dna
        occurrences = ctx.count("aussie slang")
        assert occurrences == 1, f"Expected 1 occurrence, got {occurrences}"

    def test_comment_sections_includes_australian_authenticity(self, sample_voice_spec):
        """COMMENT_SECTIONS includes australian_authenticity_strict for comments."""
        spec = VoiceSpec(sample_voice_spec)
        spec.load()
        ctx = spec.get_comment_context()
        # Should have both voice_dna and australian_authenticity_strict
        # This means "aussie slang" appears twice (once in voice_dna, once in extracted section)
        assert "Voice Dna" in ctx
        # australian_authenticity_strict is in COMMENT_SECTIONS
        assert "Australian Authenticity Strict" in ctx
