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
</voice_dna>

<ai_detection_avoidance>
Em-dashes FORBIDDEN (the #1 AI tell).
No formal transitions (Moreover, Furthermore).
Contractions always (you're, it's, we've).
</ai_detection_avoidance>

<australian_literary_voice>
Understated confidence. Tall poppy awareness.
Cost of living awareness. Calibrated reassurance.
</australian_literary_voice>

<content_rules>
No medical claims. Evidence-anchored. Montessori authenticity.
</content_rules>

<format_adaptations>
21s scripts: 55-65 words. 60s scripts: 160-185 words.
</format_adaptations>
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
        assert "australian_literary_voice" in names
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
