"""Tests for Baby Brains comment generator."""

import pytest

from atlas.babybrains.warming.comments import (
    CommentDraft,
    CommentGenerator,
    FORBIDDEN_PATTERNS,
    AU_VOCABULARY_CHECKS,
)


class TestCommentDraft:
    """Test CommentDraft dataclass."""

    def test_passes_quality_gate_good(self):
        draft = CommentDraft(
            video_id="test",
            comment_text="This is a great insight about toddler development.",
            quality_issues=[],
        )
        assert draft.passes_quality_gate is True

    def test_fails_quality_gate_with_issues(self):
        draft = CommentDraft(
            video_id="test",
            comment_text="test",
            quality_issues=["Contains em-dash"],
        )
        assert draft.passes_quality_gate is False

    def test_fails_quality_gate_empty_text(self):
        draft = CommentDraft(video_id="test", comment_text="")
        assert draft.passes_quality_gate is False


class TestQualityGate:
    """Test comment quality gate checks."""

    @pytest.fixture
    def generator(self):
        return CommentGenerator(
            voice_spec_context="Test voice spec",
            human_story={"bb_human_story": {"status": "INCOMPLETE"}},
        )

    def test_good_comment_passes(self, generator):
        text = "We've been doing something similar with our little one. The way you explained the concept of prepared environments really clicked for us."
        issues = generator.quality_check(text)
        assert issues == []

    def test_em_dash_caught(self, generator):
        text = "This is great \u2014 really enjoyed it."
        issues = generator.quality_check(text)
        assert any("forbidden" in i.lower() for i in issues)

    def test_en_dash_caught(self, generator):
        text = "Ages 0\u20133 are important."
        issues = generator.quality_check(text)
        assert any("forbidden" in i.lower() for i in issues)

    def test_moreover_caught(self, generator):
        text = "Moreover, this is an important topic."
        issues = generator.quality_check(text)
        assert any("Moreover" in i for i in issues)

    def test_furthermore_caught(self, generator):
        text = "Furthermore, the research shows this."
        issues = generator.quality_check(text)
        assert any("Furthermore" in i for i in issues)

    def test_us_english_mom_caught(self, generator):
        text = "As a mom I really appreciate this."
        issues = generator.quality_check(text)
        assert any("mom" in i for i in issues)

    def test_us_english_diaper_caught(self, generator):
        text = "Great tips for diaper changing."
        issues = generator.quality_check(text)
        assert any("diaper" in i for i in issues)

    def test_us_english_stroller_caught(self, generator):
        text = "Love the stroller hack."
        issues = generator.quality_check(text)
        assert any("stroller" in i for i in issues)

    def test_au_english_mum_passes(self, generator):
        text = "As a mum this resonates with me."
        issues = generator.quality_check(text)
        assert not any("mum" in i for i in issues)

    def test_too_long_caught(self, generator):
        text = "x" * 501
        issues = generator.quality_check(text)
        assert any("Too long" in i for i in issues)

    def test_too_short_caught(self, generator):
        text = "Hi"
        issues = generator.quality_check(text)
        assert any("Too short" in i for i in issues)

    def test_excessive_emojis_caught(self, generator):
        text = "Love this! \U0001F60D\U0001F44F\U0001F525\U0001F389"
        issues = generator.quality_check(text)
        assert any("emoji" in i.lower() for i in issues)

    def test_one_emoji_passes(self, generator):
        text = "We've found the same thing with our toddler. Such a helpful video \U0001F44F"
        issues = generator.quality_check(text)
        assert not any("emoji" in i.lower() for i in issues)

    def test_contractions_not_flagged(self, generator):
        """Contractions like it's, you're, we've should pass."""
        text = "It's exactly what we've been looking for. You're spot on about the sensitive periods."
        issues = generator.quality_check(text)
        assert issues == []


class TestCommentGeneratorInit:
    """Test CommentGenerator initialization."""

    def test_init_with_context(self):
        gen = CommentGenerator(
            voice_spec_context="test spec",
            human_story={"bb_human_story": {"status": "COMPLETE"}},
        )
        assert gen._voice_spec_context == "test spec"

    def test_init_without_context(self):
        gen = CommentGenerator()
        assert gen._voice_spec_context is None
        assert gen._client is None
