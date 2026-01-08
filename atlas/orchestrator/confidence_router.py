"""
Confidence-based response routing for ATLAS.

Based on Anthropic's introspection research (October 2025):
- Verbalized confidence correlates better with accuracy than raw logits
- "Wait" pattern reduces blind spots by 89.3%
- High-confidence claims in novel domains need HEAVIER verification

Reference: anthropic.com/research/introspection
"""

import re
import logging
from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence classification levels."""
    HIGH = "high"        # > 0.8 - Light verification
    MEDIUM = "medium"    # 0.5-0.8 - Standard verification  
    LOW = "low"          # < 0.5 - Heavy verification or regenerate


class VerificationAction(Enum):
    """Actions based on confidence routing."""
    PROCEED = "proceed"                    # Light verification sufficient
    VERIFY_EXTERNAL = "verify_external"    # Need external API/tool check
    VERIFY_ADVERSARIAL = "verify_adversarial"  # Need multi-agent review
    REGENERATE = "regenerate"              # Confidence too low, try again
    ESCALATE = "escalate"                  # Human review needed


@dataclass
class ConfidenceResult:
    """Result of confidence extraction and routing."""
    score: float
    level: ConfidenceLevel
    action: VerificationAction
    markers_found: list[str]
    reasoning: str


# Confidence markers from language patterns
HIGH_CONFIDENCE_MARKERS = [
    r"\bi(?:'m| am) confident\b",
    r"\bdefinitely\b",
    r"\bcertainly\b",
    r"\bwithout doubt\b",
    r"\bclearly\b",
    r"\bobviously\b",
]

MEDIUM_CONFIDENCE_MARKERS = [
    r"\bi think\b",
    r"\bi believe\b",
    r"\bprobably\b",
    r"\blikely\b",
    r"\bshould be\b",
    r"\bseems like\b",
]

LOW_CONFIDENCE_MARKERS = [
    r"\bi(?:'m| am) not sure\b",
    r"\bi(?:'m| am) uncertain\b",
    r"\bpossibly\b",
    r"\bmight be\b",
    r"\bcould be\b",
    r"\bi don(?:'t| not) know\b",
    r"\bunclear\b",
    r"\bnot certain\b",
]

# Safety-critical domains that always need heavy verification
SAFETY_CRITICAL_DOMAINS = [
    "health",
    "medical",
    "supplements",
    "exercise",
    "safety",
    "financial",
    "legal",
]


def extract_confidence(response: str) -> Tuple[float, list[str]]:
    """
    Extract confidence level from response text.
    
    Returns:
        Tuple of (confidence_score 0-1, list of markers found)
    """
    response_lower = response.lower()
    markers_found = []
    
    # Count markers at each level
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for pattern in HIGH_CONFIDENCE_MARKERS:
        matches = re.findall(pattern, response_lower)
        if matches:
            high_count += len(matches)
            markers_found.extend(matches)
    
    for pattern in MEDIUM_CONFIDENCE_MARKERS:
        matches = re.findall(pattern, response_lower)
        if matches:
            medium_count += len(matches)
            markers_found.extend(matches)
    
    for pattern in LOW_CONFIDENCE_MARKERS:
        matches = re.findall(pattern, response_lower)
        if matches:
            low_count += len(matches)
            markers_found.extend(matches)
    
    # Calculate weighted score
    total_markers = high_count + medium_count + low_count
    
    if total_markers == 0:
        # No explicit markers - default to medium confidence
        return 0.6, []
    
    # Weighted average: high=0.9, medium=0.6, low=0.3
    weighted_sum = (high_count * 0.9) + (medium_count * 0.6) + (low_count * 0.3)
    score = weighted_sum / total_markers
    
    return score, markers_found


def is_safety_critical(domain: Optional[str]) -> bool:
    """Check if domain requires mandatory heavy verification."""
    if domain is None:
        return False
    return any(critical in domain.lower() for critical in SAFETY_CRITICAL_DOMAINS)


def route_by_confidence(
    response: str,
    domain: Optional[str] = None,
    force_verification: bool = False,
) -> ConfidenceResult:
    """
    Route response based on extracted confidence and domain.
    
    Args:
        response: The model's response text
        domain: Optional domain category for the query
        force_verification: If True, always require external verification
        
    Returns:
        ConfidenceResult with routing decision
    """
    score, markers = extract_confidence(response)
    
    # Determine confidence level
    if score >= 0.8:
        level = ConfidenceLevel.HIGH
    elif score >= 0.5:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW
    
    # Safety-critical domains always need heavy verification
    # Key insight from research: high confidence in novel/critical domains
    # should trigger MORE verification, not less (confidence inversion)
    if is_safety_critical(domain):
        if level == ConfidenceLevel.HIGH:
            # Confidence inversion: high confidence + safety critical = suspicious
            action = VerificationAction.VERIFY_ADVERSARIAL
            reasoning = "High confidence in safety-critical domain triggers adversarial review"
        else:
            action = VerificationAction.VERIFY_EXTERNAL
            reasoning = "Safety-critical domain requires external verification"
    elif force_verification:
        action = VerificationAction.VERIFY_EXTERNAL
        reasoning = "Forced verification requested"
    elif level == ConfidenceLevel.HIGH:
        action = VerificationAction.PROCEED
        reasoning = "High confidence allows proceeding with light verification"
    elif level == ConfidenceLevel.MEDIUM:
        action = VerificationAction.VERIFY_EXTERNAL
        reasoning = "Medium confidence requires external verification"
    else:  # LOW
        action = VerificationAction.REGENERATE
        reasoning = "Low confidence suggests regenerating response"
    
    logger.debug(
        f"Confidence routing: score={score:.2f}, level={level.value}, "
        f"action={action.value}, domain={domain}"
    )
    
    return ConfidenceResult(
        score=score,
        level=level,
        action=action,
        markers_found=markers,
        reasoning=reasoning,
    )


# The "Wait" pattern from introspection research
WAIT_PATTERN_PROMPT = """
Wait. Before evaluating, pause and consider:
- What assumptions did I make?
- Where might I be wrong?
- What would I tell someone else who gave this answer?

Now evaluate and correct if needed:
"""


def apply_wait_pattern(original_response: str, query: str) -> str:
    """
    Generate a self-correction prompt using the "Wait" pattern.
    
    Research finding: This reduces blind spots by 89.3%.
    
    Args:
        original_response: The initial model response
        query: The original user query
        
    Returns:
        Formatted prompt for self-correction
    """
    return f"""Given this question: {query}

And this initial answer: {original_response}

{WAIT_PATTERN_PROMPT}"""


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_response = " ".join(sys.argv[1:])
    else:
        test_response = "I think this is probably correct, but I'm not entirely sure."
    
    result = route_by_confidence(test_response)
    print(f"Response: {test_response}")
    print(f"Confidence Score: {result.score:.2f}")
    print(f"Level: {result.level.value}")
    print(f"Action: {result.action.value}")
    print(f"Markers: {result.markers_found}")
    print(f"Reasoning: {result.reasoning}")
