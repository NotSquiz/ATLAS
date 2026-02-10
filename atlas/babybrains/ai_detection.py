"""
AI Detection Module for Baby Brains Content

Shared module implementing comprehensive AI writing pattern detection.
Used by both the content production pipeline (qc_script.py) and activity
pipeline (check_activity_quality.py).

Based on BabyBrains-Writer.md voice specification and 3-agent audit findings.

Pattern Categories (12 total):
1. SUPERLATIVES - 9 words with context-aware exceptions
2. OUTCOME_PROMISES - Claims of guaranteed child outcomes
3. PRESSURE_LANGUAGE - "You must", "You need to", etc.
4. FORMAL_TRANSITIONS - "Moreover", "Furthermore", etc.
5. NON_CONTRACTIONS - "It is" instead of "It's"
6. HOLLOW_AFFIRMATIONS - "It's important to note"
7. AI_CLICHES - "In today's fast-paced world"
8. HEDGE_STACKING - "Could potentially", "Perhaps might"
9. LIST_INTROS - "Let's dive in", "Here are 5 ways"
10. ENTHUSIASM_MARKERS - Multiple exclamation marks
11. FILLER_PHRASES - "In order to", "Due to the fact"
12. EM_DASHES - Em-dash, en-dash, double-hyphen
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================
# 1. SUPERLATIVES (9 words with exceptions)
# ============================================

SUPERLATIVES = [
    "amazing",
    "incredible",
    "wonderful",
    "perfect",
    "optimal",
    "best",
    "fantastic",
    "extraordinary",
    "ideal",
]

# Exception patterns per word - must check BEFORE flagging
# Patterns use raw strings for regex safety
SUPERLATIVE_EXCEPTIONS: dict[str, list[re.Pattern]] = {
    "best": [
        re.compile(r"\bbest\s+practice[s]?\b", re.IGNORECASE),
        re.compile(r"\b(?:do|try)\s+(?:your|their)\s+best\b", re.IGNORECASE),
        re.compile(r"\bworks?\s+best\b", re.IGNORECASE),
        re.compile(r"\bbest\s+(?:for|time|way|interests)\b", re.IGNORECASE),
        re.compile(r"\b(?:learn|sleep|eat|grow|develop)s?\s+best\b", re.IGNORECASE),
        re.compile(r"\bat\s+best\b", re.IGNORECASE),  # "at best" (qualifier)
    ],
    "perfect": [
        # Verb form: "perfects", "perfected", "perfecting"
        re.compile(r"\bperfect(?:s|ed|ing)\s+(?:the|their|a)\b", re.IGNORECASE),
        # Negations
        re.compile(r"\bdoesn't\s+(?:need|have)\s+to\s+be\s+perfect\b", re.IGNORECASE),
        re.compile(r"\bnot\s+(?:about\s+)?perfect(?:ion)?\b", re.IGNORECASE),
        re.compile(r"\bimperfect\b", re.IGNORECASE),  # prefix negation
    ],
    "extraordinary": [
        # Montessori term: "extraordinary absorptive mind"
        re.compile(r"\bextraordinary\s+absorptive\b", re.IGNORECASE),
        # Relational: "extraordinary to your baby"
        re.compile(r"\bextraordinary\s+to\s+your\b", re.IGNORECASE),
    ],
    "incredible": [
        # Montessori phrase: "incredible focus"
        re.compile(r"\bincredible\s+focus\b", re.IGNORECASE),
    ],
    # amazing, wonderful, fantastic have NO exceptions
    "amazing": [],
    "wonderful": [],
    "fantastic": [],
    # optimal: only "suboptimal" is allowed
    "optimal": [
        re.compile(r"\bsub-?optimal\b", re.IGNORECASE),  # "suboptimal" (negation)
    ],
    # ideal: Montessori "ideal period" is a technical term
    "ideal": [
        re.compile(r"\bideal\s+period\b", re.IGNORECASE),  # Montessori sensitive period
    ],
}


def _is_superlative_exception(text: str, word: str, match: re.Match) -> bool:
    """Check if a superlative match is an allowed exception.

    Bug fix (2026-02-04): Now verifies the exception pattern contains the
    actual match position, not just that the exception exists somewhere in text.
    This prevents false negatives where "best practices" at one position
    would incorrectly exempt "the best" elsewhere in the same text.
    """
    exceptions = SUPERLATIVE_EXCEPTIONS.get(word, [])
    match_start = match.start()
    match_end = match.end()

    for pattern in exceptions:
        for exc_match in pattern.finditer(text):
            # Verify the exception contains our superlative position
            if exc_match.start() <= match_start and match_end <= exc_match.end():
                return True
    return False


def check_superlatives(text: str) -> list[dict[str, str]]:
    """
    Check for superlative words that indicate AI writing.

    Context-aware: Allows exceptions like "best practices", "try your best",
    "doesn't need to be perfect", "extraordinary absorptive mind" (Montessori).

    Returns list of issues with code SCRIPT_SUPERLATIVE.
    """
    issues = []
    text_lower = text.lower()

    for word in SUPERLATIVES:
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            # Check if this is an allowed exception
            if not _is_superlative_exception(text, word, match):
                issues.append({
                    "code": "SCRIPT_SUPERLATIVE",
                    "msg": f"Avoid superlative '{word}'. Use specific, grounded language.",
                })
                break  # Only report each word once

    return issues


# ============================================
# 2. OUTCOME PROMISES
# ============================================

OUTCOME_PROMISE_PATTERNS = [
    re.compile(r"\bwill\s+develop\b", re.IGNORECASE),
    re.compile(r"\bwill\s+become\b", re.IGNORECASE),
    re.compile(r"\bwill\s+make\s+your\s+child\b", re.IGNORECASE),
    re.compile(r"\bguarantees?\b", re.IGNORECASE),
    re.compile(r"\bensures?\s+your\s+child\s+will\b", re.IGNORECASE),
]


def check_outcome_promises(text: str) -> list[dict[str, str]]:
    """
    Check for outcome promises that claim guaranteed child development.

    Returns list of issues with code SCRIPT_OUTCOME_PROMISE.
    """
    issues = []

    for pattern in OUTCOME_PROMISE_PATTERNS:
        if pattern.search(text):
            match_text = pattern.pattern.replace(r"\b", "").replace(r"\s+", " ")
            issues.append({
                "code": "SCRIPT_OUTCOME_PROMISE",
                "msg": f"Avoid outcome promises like '{match_text}'. Use 'may help support' instead.",
            })
            break  # Only report once

    return issues


# ============================================
# 3. PRESSURE LANGUAGE
# ============================================

PRESSURE_PATTERNS = [
    re.compile(r"\byou\s+must\b", re.IGNORECASE),
    re.compile(r"\byou\s+need\s+to\b", re.IGNORECASE),
    re.compile(r"\byou\s+have\s+to\b", re.IGNORECASE),
    re.compile(r"\byou\s+should\s+always\b", re.IGNORECASE),
    re.compile(r"\bnever\s+(?:do|let|allow)\b", re.IGNORECASE),
]


def check_pressure_language(text: str) -> list[dict[str, str]]:
    """
    Check for pressure language that creates parental guilt.

    Returns list of issues with code SCRIPT_PRESSURE_LANGUAGE.
    """
    issues = []

    for pattern in PRESSURE_PATTERNS:
        if pattern.search(text):
            match_text = pattern.pattern.replace(r"\b", "").replace(r"\s+", " ")
            issues.append({
                "code": "SCRIPT_PRESSURE_LANGUAGE",
                "msg": f"Avoid pressure language like '{match_text}'. Be supportive, not prescriptive.",
            })
            break  # Only report once

    return issues


# ============================================
# 4. FORMAL TRANSITIONS (11 words)
# ============================================

FORMAL_TRANSITIONS = [
    "moreover",
    "furthermore",
    "consequently",
    "nevertheless",
    "additionally",
    "subsequently",
    "nonetheless",
    "hence",
    "thus",
    "therefore",
    "in conclusion",
]


def check_formal_transitions(text: str) -> list[dict[str, str]]:
    """
    Check for formal academic transitions that sound AI-generated.

    Special case: "however" is only flagged at sentence start.

    Returns list of issues with code SCRIPT_FORMAL_TRANSITION.
    """
    issues = []
    text_lower = text.lower()

    for transition in FORMAL_TRANSITIONS:
        if transition in text_lower:
            issues.append({
                "code": "SCRIPT_FORMAL_TRANSITION",
                "msg": f"Avoid formal transition '{transition}'. Use natural conversational flow.",
            })
            break  # Only report once

    # Special check: "however" at sentence start only
    if re.search(r"(?:^|[.!?]\s+)however\b", text_lower):
        issues.append({
            "code": "SCRIPT_FORMAL_TRANSITION",
            "msg": "Avoid starting sentences with 'However'. Rewrite for natural flow.",
        })

    return issues


# ============================================
# 5. NON-CONTRACTIONS (25+ patterns)
# ============================================

# (pattern, suggested contraction)
NON_CONTRACTION_PAIRS = [
    (r"\bit is\b", "it's"),
    (r"\byou are\b", "you're"),
    (r"\bthey are\b", "they're"),
    (r"\bwe are\b", "we're"),
    (r"\bdoes not\b", "doesn't"),
    (r"\bdo not\b", "don't"),
    (r"\bcannot\b", "can't"),
    (r"\bwill not\b", "won't"),
    (r"\bthat is\b", "that's"),
    (r"\bwhat is\b", "what's"),
    (r"\bwho is\b", "who's"),
    (r"\bthere is\b", "there's"),
    (r"\bwe have\b", "we've"),
    (r"\bthey have\b", "they've"),
    (r"\bwould not\b", "wouldn't"),
    (r"\bcould not\b", "couldn't"),
    (r"\bshould not\b", "shouldn't"),
    (r"\bhas not\b", "hasn't"),
    (r"\bhave not\b", "haven't"),
    (r"\bhad not\b", "hadn't"),
    (r"\bis not\b", "isn't"),
    (r"\bare not\b", "aren't"),
    (r"\bwas not\b", "wasn't"),
    (r"\bwere not\b", "weren't"),
    (r"\blet us\b", "let's"),
]


def check_non_contractions(text: str) -> list[dict[str, str]]:
    """
    Check for non-contracted forms that should use contractions.

    Returns list of issues with code SCRIPT_NO_CONTRACTION.
    """
    issues = []
    text_lower = text.lower()

    for pattern, contraction in NON_CONTRACTION_PAIRS:
        if re.search(pattern, text_lower):
            original = pattern.replace(r"\b", "")
            issues.append({
                "code": "SCRIPT_NO_CONTRACTION",
                "msg": f"Use contraction '{contraction}' instead of '{original}' for natural voice.",
            })
            break  # Only report once

    return issues


# ============================================
# 6. HOLLOW AFFIRMATIONS
# ============================================

HOLLOW_AFFIRMATION_PATTERNS = [
    re.compile(r"\bit'?s\s+important\s+to\s+note\b", re.IGNORECASE),
    re.compile(r"\bit'?s\s+worth\s+mentioning\b", re.IGNORECASE),
    re.compile(r"\binterestingly\b", re.IGNORECASE),
    re.compile(r"\bit\s+should\s+be\s+(?:noted|pointed\s+out)\b", re.IGNORECASE),
    re.compile(r"\bimportantly\b", re.IGNORECASE),
    re.compile(r"\bnotably\b", re.IGNORECASE),
]


def check_hollow_affirmations(text: str) -> list[dict[str, str]]:
    """
    Check for hollow affirmations that add no value.

    Returns list of issues with code SCRIPT_HOLLOW_AFFIRMATION.
    """
    issues = []

    for pattern in HOLLOW_AFFIRMATION_PATTERNS:
        if pattern.search(text):
            issues.append({
                "code": "SCRIPT_HOLLOW_AFFIRMATION",
                "msg": "Remove hollow affirmation. State the point directly.",
            })
            break  # Only report once

    return issues


# ============================================
# 7. AI CLICHES
# ============================================

AI_CLICHE_PATTERNS = [
    re.compile(r"\bin\s+today'?s\s+(?:fast-paced|modern|digital)\s+world\b", re.IGNORECASE),
    re.compile(r"\bat\s+the\s+end\s+of\s+the\s+day\b", re.IGNORECASE),
    re.compile(r"\bgame[- ]?changer\b", re.IGNORECASE),
    re.compile(r"\bto\s+the\s+next\s+level\b", re.IGNORECASE),  # "take X to the next level"
    re.compile(r"\bjourney\b", re.IGNORECASE),  # "parenting journey"
    re.compile(r"\bunlock\s+(?:your|their)\b", re.IGNORECASE),  # "unlock their potential"
    re.compile(r"\bdelve\s+into\b", re.IGNORECASE),
    re.compile(r"\bembark\s+on\b", re.IGNORECASE),
]


def check_ai_cliches(text: str) -> list[dict[str, str]]:
    """
    Check for AI-typical cliches and buzzwords.

    Returns list of issues with code SCRIPT_AI_CLICHE.
    """
    issues = []

    for pattern in AI_CLICHE_PATTERNS:
        if pattern.search(text):
            issues.append({
                "code": "SCRIPT_AI_CLICHE",
                "msg": "Remove AI cliche. Use specific, authentic language.",
            })
            break  # Only report once

    return issues


# ============================================
# 8. HEDGE STACKING
# ============================================

HEDGE_STACKING_PATTERNS = [
    re.compile(r"\bcould\s+potentially\b", re.IGNORECASE),
    re.compile(r"\bperhaps\s+might\b", re.IGNORECASE),
    re.compile(r"\bmight\s+possibly\b", re.IGNORECASE),
    re.compile(r"\bpossibly\s+could\b", re.IGNORECASE),
    re.compile(r"\bmay\s+potentially\b", re.IGNORECASE),
    re.compile(r"\bperhaps\s+could\b", re.IGNORECASE),
]


def check_hedge_stacking(text: str) -> list[dict[str, str]]:
    """
    Check for stacked hedging words that indicate uncertainty.

    Returns list of issues with code SCRIPT_HEDGE_STACKING.
    """
    issues = []

    for pattern in HEDGE_STACKING_PATTERNS:
        if pattern.search(text):
            issues.append({
                "code": "SCRIPT_HEDGE_STACKING",
                "msg": "Remove stacked hedges. Use one qualifier or none.",
            })
            break  # Only report once

    return issues


# ============================================
# 9. ROBOTIC LIST INTROS
# ============================================

LIST_INTRO_PATTERNS = [
    re.compile(r"\blet'?s\s+dive\s+(?:in|into)\b", re.IGNORECASE),
    re.compile(r"\bhere\s+are\s+\d+\s+(?:ways?|tips?|reasons?|things?)\b", re.IGNORECASE),
    re.compile(r"\bwithout\s+further\s+ado\b", re.IGNORECASE),
    re.compile(r"\bthe\s+following\s+(?:benefits?|points?|tips?)\s+include\b", re.IGNORECASE),
    re.compile(r"\bfirst\s+and\s+foremost\b", re.IGNORECASE),
    re.compile(r"\blast\s+but\s+not\s+least\b", re.IGNORECASE),
]


def check_list_intros(text: str) -> list[dict[str, str]]:
    """
    Check for robotic list introduction phrases.

    Returns list of issues with code SCRIPT_LIST_INTRO.
    """
    issues = []

    for pattern in LIST_INTRO_PATTERNS:
        if pattern.search(text):
            issues.append({
                "code": "SCRIPT_LIST_INTRO",
                "msg": "Avoid robotic list intros. Start with the content directly.",
            })
            break  # Only report once

    return issues


# ============================================
# 10. EXCESSIVE ENTHUSIASM
# ============================================

ENTHUSIASM_PATTERNS = [
    re.compile(r"!{2,}"),  # Multiple exclamation marks
    re.compile(r"\b(?:Amazing|Incredible|Wonderful|Fantastic)!", re.IGNORECASE),  # Superlative + exclamation
    re.compile(r"\bso\s+excited\b", re.IGNORECASE),
    re.compile(r"\babsolutely\s+love\b", re.IGNORECASE),
]


def check_enthusiasm(text: str) -> list[dict[str, str]]:
    """
    Check for excessive enthusiasm markers.

    Returns list of issues with code SCRIPT_ENTHUSIASM.
    """
    issues = []

    for pattern in ENTHUSIASM_PATTERNS:
        if pattern.search(text):
            issues.append({
                "code": "SCRIPT_ENTHUSIASM",
                "msg": "Reduce enthusiasm. Use calm, confident tone.",
            })
            break  # Only report once

    return issues


# ============================================
# 11. FILLER PHRASES
# ============================================

FILLER_PATTERNS = [
    re.compile(r"\bin\s+order\s+to\b", re.IGNORECASE),  # just use "to"
    re.compile(r"\bdue\s+to\s+the\s+fact\s+that\b", re.IGNORECASE),  # use "because"
    re.compile(r"\bin\s+terms\s+of\b", re.IGNORECASE),
    re.compile(r"\bwith\s+regard(?:s)?\s+to\b", re.IGNORECASE),
    re.compile(r"\bat\s+this\s+point\s+in\s+time\b", re.IGNORECASE),  # use "now"
    re.compile(r"\bfor\s+the\s+purpose\s+of\b", re.IGNORECASE),  # use "to"
    re.compile(r"\bthe\s+fact\s+that\b", re.IGNORECASE),
]


def check_filler_phrases(text: str) -> list[dict[str, str]]:
    """
    Check for filler phrases that can be simplified.

    Returns list of issues with code SCRIPT_FILLER_PHRASE.
    """
    issues = []

    for pattern in FILLER_PATTERNS:
        if pattern.search(text):
            issues.append({
                "code": "SCRIPT_FILLER_PHRASE",
                "msg": "Remove filler phrase. Use simpler wording.",
            })
            break  # Only report once

    return issues


# ============================================
# 12. EM-DASHES (Already implemented)
# ============================================


def check_em_dashes(text: str) -> list[dict[str, str]]:
    """
    Check for em-dashes, en-dashes, and double-hyphens.

    Em-dashes are the #1 AI writing tell.

    Returns list of issues with code SCRIPT_EM_DASH.
    """
    issues = []

    # Em-dash (—), en-dash (–), double hyphen (--)
    if "—" in text or "–" in text or "--" in text:
        issues.append({
            "code": "SCRIPT_EM_DASH",
            "msg": "Em-dashes (—) are FORBIDDEN. Use commas, periods, or line breaks.",
        })

    return issues


# ============================================
# MAIN API
# ============================================


def check_ai_tells(text: str) -> list[dict[str, str]]:
    """
    Check text for all AI writing patterns.

    Runs all 12 pattern checkers and aggregates results.

    Args:
        text: The text to check

    Returns:
        List of issues: [{"code": str, "msg": str}]
    """
    issues: list[dict[str, str]] = []

    # Run all checkers
    issues.extend(check_em_dashes(text))
    issues.extend(check_formal_transitions(text))
    issues.extend(check_superlatives(text))
    issues.extend(check_outcome_promises(text))
    issues.extend(check_pressure_language(text))
    issues.extend(check_non_contractions(text))
    issues.extend(check_hollow_affirmations(text))
    issues.extend(check_ai_cliches(text))
    issues.extend(check_hedge_stacking(text))
    issues.extend(check_list_intros(text))
    issues.extend(check_enthusiasm(text))
    issues.extend(check_filler_phrases(text))

    return issues


# ============================================
# SEVERITY LEVELS (for pipeline prioritization)
# ============================================

# Block codes by severity
CRITICAL_CODES = {"SCRIPT_EM_DASH"}
HIGH_CODES = {
    "SCRIPT_FORMAL_TRANSITION",
    "SCRIPT_SUPERLATIVE",
    "SCRIPT_OUTCOME_PROMISE",
    "SCRIPT_PRESSURE_LANGUAGE",
}
MEDIUM_CODES = {
    "SCRIPT_NO_CONTRACTION",
    "SCRIPT_HOLLOW_AFFIRMATION",
    "SCRIPT_AI_CLICHE",
    "SCRIPT_HEDGE_STACKING",
    "SCRIPT_LIST_INTRO",
    "SCRIPT_ENTHUSIASM",
}
LOW_CODES = {"SCRIPT_FILLER_PHRASE"}


def get_severity(code: str) -> str:
    """Get severity level for a block code."""
    if code in CRITICAL_CODES:
        return "CRITICAL"
    if code in HIGH_CODES:
        return "HIGH"
    if code in MEDIUM_CODES:
        return "MEDIUM"
    if code in LOW_CODES:
        return "LOW"
    return "UNKNOWN"


def has_critical_issues(issues: list[dict[str, str]]) -> bool:
    """Check if any issues are CRITICAL severity."""
    return any(issue.get("code") in CRITICAL_CODES for issue in issues)


def has_high_or_critical_issues(issues: list[dict[str, str]]) -> bool:
    """Check if any issues are HIGH or CRITICAL severity."""
    return any(
        issue.get("code") in CRITICAL_CODES or issue.get("code") in HIGH_CODES
        for issue in issues
    )
