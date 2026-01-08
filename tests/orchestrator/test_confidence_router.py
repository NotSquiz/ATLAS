"""Tests for confidence_router.py - Confidence-based response routing."""
import pytest


class TestExtractConfidence:
    """Test extract_confidence() function."""

    def test_high_confidence_detected(self):
        """Detect high confidence markers like 'I am confident'."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("I am confident this is correct")
        assert score > 0.7
        assert len(markers) > 0

    def test_high_confidence_definitely(self):
        """Detect 'definitely' as high confidence marker."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("This is definitely the answer")
        assert score > 0.7
        assert "definitely" in markers

    def test_high_confidence_certainly(self):
        """Detect 'certainly' as high confidence marker."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("This is certainly true")
        assert score > 0.7
        assert "certainly" in markers

    def test_medium_confidence_detected(self):
        """Detect medium confidence markers like 'I think'."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("I think this might be right")
        assert 0.4 < score < 0.8
        assert len(markers) > 0

    def test_medium_confidence_probably(self):
        """Detect 'probably' as medium confidence marker."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("This is probably correct")
        assert 0.4 < score < 0.8
        assert "probably" in markers

    def test_low_confidence_detected(self):
        """Detect low confidence markers like 'I'm not sure'."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("I'm not sure about this")
        assert score < 0.5
        assert len(markers) > 0

    def test_low_confidence_might_be(self):
        """Detect 'might be' as low confidence marker."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("This might be correct")
        assert score < 0.5
        assert "might be" in markers

    def test_low_confidence_uncertain(self):
        """Detect 'I'm uncertain' as low confidence marker."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("I'm uncertain about this")
        assert score < 0.5
        assert len(markers) > 0

    def test_no_markers_default_medium(self):
        """No markers should return medium confidence (0.6)."""
        from atlas.orchestrator.confidence_router import extract_confidence

        score, markers = extract_confidence("The answer is 42.")
        assert score == 0.6
        assert len(markers) == 0

    def test_mixed_markers_weighted_average(self):
        """Mixed markers produce weighted average score."""
        from atlas.orchestrator.confidence_router import extract_confidence

        # Mix of high and low markers
        score, markers = extract_confidence(
            "I am confident, but I might be wrong and could be mistaken"
        )
        # Score should be between high (0.9) and low (0.3)
        assert 0.3 < score < 0.9
        assert len(markers) >= 2


class TestRouteByConfidence:
    """Test route_by_confidence() function."""

    def test_high_confidence_returns_proceed(self):
        """High confidence should return PROCEED action."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
            ConfidenceLevel,
        )

        result = route_by_confidence("I am definitely certain this is correct")
        assert result.level == ConfidenceLevel.HIGH
        assert result.action == VerificationAction.PROCEED

    def test_medium_confidence_returns_verify_external(self):
        """Medium confidence should return VERIFY_EXTERNAL action."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
            ConfidenceLevel,
        )

        result = route_by_confidence("I think this is probably correct")
        assert result.level == ConfidenceLevel.MEDIUM
        assert result.action == VerificationAction.VERIFY_EXTERNAL

    def test_low_confidence_returns_regenerate(self):
        """Low confidence should return REGENERATE action."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
            ConfidenceLevel,
        )

        result = route_by_confidence("I'm not sure, it might be wrong, could be anything")
        assert result.level == ConfidenceLevel.LOW
        assert result.action == VerificationAction.REGENERATE

    def test_force_verification_overrides(self):
        """force_verification=True should override normal routing."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
        )

        # High confidence would normally PROCEED
        result = route_by_confidence(
            "I am definitely certain this is correct",
            force_verification=True
        )
        assert result.action == VerificationAction.VERIFY_EXTERNAL

    def test_result_contains_markers(self):
        """Result should include the markers that were found."""
        from atlas.orchestrator.confidence_router import route_by_confidence

        result = route_by_confidence("I definitely think this is probably correct")
        assert len(result.markers_found) > 0
        assert "definitely" in result.markers_found

    def test_result_contains_reasoning(self):
        """Result should include reasoning for the decision."""
        from atlas.orchestrator.confidence_router import route_by_confidence

        result = route_by_confidence("I am confident this is correct")
        assert result.reasoning is not None
        assert len(result.reasoning) > 0


class TestConfidenceInversion:
    """Test confidence inversion for safety-critical domains."""

    def test_high_confidence_safety_domain_adversarial(self):
        """High confidence + safety domain = VERIFY_ADVERSARIAL (inversion)."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
        )

        result = route_by_confidence(
            "I am definitely certain about this medical advice",
            domain="medical"
        )
        assert result.action == VerificationAction.VERIFY_ADVERSARIAL
        assert "adversarial" in result.reasoning.lower()

    def test_high_confidence_health_domain_adversarial(self):
        """High confidence + health domain = VERIFY_ADVERSARIAL."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
        )

        result = route_by_confidence(
            "I am certainly sure about this health recommendation",
            domain="health"
        )
        assert result.action == VerificationAction.VERIFY_ADVERSARIAL

    def test_high_confidence_financial_domain_adversarial(self):
        """High confidence + financial domain = VERIFY_ADVERSARIAL."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
        )

        result = route_by_confidence(
            "I definitely recommend this financial strategy",
            domain="financial"
        )
        assert result.action == VerificationAction.VERIFY_ADVERSARIAL

    def test_high_confidence_legal_domain_adversarial(self):
        """High confidence + legal domain = VERIFY_ADVERSARIAL."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
        )

        result = route_by_confidence(
            "I am certainly correct about this legal interpretation",
            domain="legal"
        )
        assert result.action == VerificationAction.VERIFY_ADVERSARIAL

    def test_medium_confidence_safety_domain_verify_external(self):
        """Medium/low confidence + safety domain = VERIFY_EXTERNAL (no inversion)."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
        )

        result = route_by_confidence(
            "I think this medical advice might be correct",
            domain="medical"
        )
        # Should be VERIFY_EXTERNAL, not adversarial (inversion only for HIGH)
        assert result.action == VerificationAction.VERIFY_EXTERNAL

    def test_high_confidence_non_safety_domain_proceeds(self):
        """High confidence + non-safety domain = PROCEED (no inversion)."""
        from atlas.orchestrator.confidence_router import (
            route_by_confidence,
            VerificationAction,
        )

        result = route_by_confidence(
            "I am definitely certain this coding solution is correct",
            domain="programming"
        )
        assert result.action == VerificationAction.PROCEED


class TestIsSafetyCritical:
    """Test is_safety_critical() helper function."""

    def test_medical_is_critical(self):
        """Medical domain should be safety critical."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical("medical") is True

    def test_health_is_critical(self):
        """Health domain should be safety critical."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical("health") is True

    def test_financial_is_critical(self):
        """Financial domain should be safety critical."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical("financial") is True

    def test_legal_is_critical(self):
        """Legal domain should be safety critical."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical("legal") is True

    def test_safety_is_critical(self):
        """Safety domain should be safety critical."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical("safety") is True

    def test_programming_not_critical(self):
        """Programming domain should not be safety critical."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical("programming") is False

    def test_none_domain_not_critical(self):
        """None domain should not be safety critical."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical(None) is False

    def test_substring_match(self):
        """Safety critical detection should work with substring match."""
        from atlas.orchestrator.confidence_router import is_safety_critical

        assert is_safety_critical("medical_advice") is True
        assert is_safety_critical("financial_planning") is True


class TestApplyWaitPattern:
    """Test apply_wait_pattern() function."""

    def test_generates_prompt(self):
        """Should generate a self-correction prompt."""
        from atlas.orchestrator.confidence_router import apply_wait_pattern

        prompt = apply_wait_pattern("The answer is 42", "What is the meaning of life?")
        assert "Wait" in prompt
        assert "42" in prompt
        assert "meaning of life" in prompt

    def test_includes_original_response(self):
        """Prompt should include the original response."""
        from atlas.orchestrator.confidence_router import apply_wait_pattern

        original = "Python is the best programming language"
        prompt = apply_wait_pattern(original, "What language should I learn?")
        assert original in prompt

    def test_includes_original_query(self):
        """Prompt should include the original query."""
        from atlas.orchestrator.confidence_router import apply_wait_pattern

        query = "How do I fix this bug?"
        prompt = apply_wait_pattern("Try restarting the server", query)
        assert query in prompt

    def test_includes_reflection_prompts(self):
        """Prompt should include self-reflection questions."""
        from atlas.orchestrator.confidence_router import apply_wait_pattern

        prompt = apply_wait_pattern("Some response", "Some query")
        assert "assumptions" in prompt.lower()
        assert "wrong" in prompt.lower()


class TestConfidenceLevelEnum:
    """Test ConfidenceLevel enum."""

    def test_levels_exist(self):
        """All three confidence levels should exist."""
        from atlas.orchestrator.confidence_router import ConfidenceLevel

        assert hasattr(ConfidenceLevel, "HIGH")
        assert hasattr(ConfidenceLevel, "MEDIUM")
        assert hasattr(ConfidenceLevel, "LOW")

    def test_level_values(self):
        """Confidence levels should have correct string values."""
        from atlas.orchestrator.confidence_router import ConfidenceLevel

        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"


class TestVerificationActionEnum:
    """Test VerificationAction enum."""

    def test_actions_exist(self):
        """All verification actions should exist."""
        from atlas.orchestrator.confidence_router import VerificationAction

        assert hasattr(VerificationAction, "PROCEED")
        assert hasattr(VerificationAction, "VERIFY_EXTERNAL")
        assert hasattr(VerificationAction, "VERIFY_ADVERSARIAL")
        assert hasattr(VerificationAction, "REGENERATE")
        assert hasattr(VerificationAction, "ESCALATE")

    def test_action_values(self):
        """Actions should have correct string values."""
        from atlas.orchestrator.confidence_router import VerificationAction

        assert VerificationAction.PROCEED.value == "proceed"
        assert VerificationAction.VERIFY_ADVERSARIAL.value == "verify_adversarial"
