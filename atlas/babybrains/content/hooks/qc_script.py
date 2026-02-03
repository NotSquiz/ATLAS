"""
QC Hook: Script Requirements

Validates script structure, word count, AU spelling, and formatting.

Input JSON:
{
    "scenes": [
        {
            "number": int,
            "vo_text": str,
            "duration_seconds": float,
            ...
        },
        ...
    ],
    "format_type": str,       # "21s", "60s", "90s"
    "total_word_count": int
}

Output JSON:
{
    "pass": bool,
    "issues": [{"code": str, "msg": str}]
}
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Word budgets at 130 WPM
WORD_BUDGETS = {
    "21s": {"min": 40, "max": 55},
    "60s": {"min": 110, "max": 140},
    "90s": {"min": 170, "max": 200},
}

# Scene count ranges
SCENE_RANGES = {
    "21s": {"min": 4, "max": 6},
    "60s": {"min": 8, "max": 12},
    "90s": {"min": 12, "max": 16},
}

# Load AU localisation rules
CONFIG_PATH = Path(__file__).parent.parent.parent.parent.parent / "config" / "babybrains" / "au_localisation.json"


def load_au_rules() -> dict:
    """Load AU localisation rules from config."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    # Fallback minimal rules
    return {
        "spelling_pairs": {
            "mom": "mum",
            "diaper": "nappy",
            "color": "colour",
            "organize": "organise",
        },
    }


def check_word_budget(
    word_count: int, format_type: str
) -> list[dict[str, str]]:
    """Check if word count is within budget for format."""
    issues = []

    budget = WORD_BUDGETS.get(format_type)
    if not budget:
        issues.append({
            "code": "SCRIPT_INVALID_FORMAT",
            "msg": f"Unknown format_type: {format_type}. Use 21s, 60s, or 90s.",
        })
        return issues

    if word_count < budget["min"]:
        issues.append({
            "code": "SCRIPT_WORD_BUDGET_UNDER",
            "msg": f"Script too short: {word_count} words (min: {budget['min']} for {format_type})",
        })
    elif word_count > budget["max"]:
        issues.append({
            "code": "SCRIPT_WORD_BUDGET_EXCEEDED",
            "msg": f"Script too long: {word_count} words (max: {budget['max']} for {format_type})",
        })

    return issues


def check_scene_count(
    scenes: list[dict], format_type: str
) -> list[dict[str, str]]:
    """Check if scene count is appropriate for format."""
    issues = []

    range_ = SCENE_RANGES.get(format_type)
    if not range_:
        return issues  # Already flagged in word budget check

    scene_count = len(scenes)

    if scene_count < range_["min"]:
        issues.append({
            "code": "SCRIPT_SCENE_COUNT_LOW",
            "msg": f"Too few scenes: {scene_count} (min: {range_['min']} for {format_type})",
        })
    elif scene_count > range_["max"]:
        issues.append({
            "code": "SCRIPT_SCENE_COUNT_HIGH",
            "msg": f"Too many scenes: {scene_count} (max: {range_['max']} for {format_type})",
        })

    return issues


def check_au_spelling(text: str) -> list[dict[str, str]]:
    """Check for US spellings that should be Australian."""
    issues = []
    rules = load_au_rules()

    spelling_pairs = rules.get("spelling_pairs", {})
    text_lower = text.lower()

    for us_spelling, au_spelling in spelling_pairs.items():
        # Use word boundary matching
        pattern = r"\b" + re.escape(us_spelling.lower()) + r"\b"
        if re.search(pattern, text_lower):
            issues.append({
                "code": "SCRIPT_AU_SPELLING",
                "msg": f"Use '{au_spelling}' instead of '{us_spelling}' (AU English)",
            })

    return issues


def check_ai_tells(text: str) -> list[dict[str, str]]:
    """Check for AI writing patterns to avoid."""
    issues = []

    # Em-dash detection (the #1 AI tell)
    # Include: em-dash (—), en-dash (–), double hyphen (--)
    if "—" in text or "–" in text or "--" in text:
        issues.append({
            "code": "SCRIPT_EM_DASH",
            "msg": "Em-dashes (—) are FORBIDDEN. Use commas, periods, or line breaks.",
        })

    # Formal transitions
    formal_transitions = [
        "moreover",
        "furthermore",
        "consequently",
        "nevertheless",
        "additionally",
        "subsequently",
    ]
    text_lower = text.lower()
    for transition in formal_transitions:
        if transition in text_lower:
            issues.append({
                "code": "SCRIPT_FORMAL_TRANSITION",
                "msg": f"Avoid formal transition '{transition}'. Use natural conversational flow.",
            })

    # Check for contractions (should use them)
    non_contractions = [
        (r"\bit is\b", "it's"),
        (r"\byou are\b", "you're"),
        (r"\bthey are\b", "they're"),
        (r"\bwe are\b", "we're"),
        (r"\bdoes not\b", "doesn't"),
        (r"\bdo not\b", "don't"),
        (r"\bcannot\b", "can't"),
        (r"\bwill not\b", "won't"),
    ]
    for pattern, contraction in non_contractions:
        if re.search(pattern, text_lower):
            issues.append({
                "code": "SCRIPT_NO_CONTRACTION",
                "msg": f"Use contraction '{contraction}' for natural voice",
            })
            break  # Only report once

    return issues


def check_scene_structure(scenes: list[dict]) -> list[dict[str, str]]:
    """Check individual scene structure."""
    issues = []

    for i, scene in enumerate(scenes, 1):
        vo_text = scene.get("vo_text", "")

        # Empty scene
        if not vo_text or not vo_text.strip():
            issues.append({
                "code": "SCRIPT_EMPTY_SCENE",
                "msg": f"Scene {i} has no voiceover text",
            })
            continue

        # Very long scene
        scene_words = len(vo_text.split())
        if scene_words > 40:
            issues.append({
                "code": "SCRIPT_SCENE_TOO_LONG",
                "msg": f"Scene {i} is too long ({scene_words} words). Max ~40 per scene.",
            })

    return issues


def validate_script(data: dict[str, Any]) -> tuple[bool, list[dict[str, str]]]:
    """
    Validate script requirements.

    Returns:
        (pass, issues) tuple
    """
    issues: list[dict[str, str]] = []

    scenes = data.get("scenes", [])
    format_type = data.get("format_type", "60s")
    total_word_count = data.get("total_word_count")

    # Calculate word count if not provided
    if total_word_count is None:
        total_word_count = sum(
            len(s.get("vo_text", "").split()) for s in scenes
        )

    # Build full script text for text-based checks
    full_text = " ".join(s.get("vo_text", "") for s in scenes)

    # Run all checks
    issues.extend(check_word_budget(total_word_count, format_type))
    issues.extend(check_scene_count(scenes, format_type))
    issues.extend(check_au_spelling(full_text))
    issues.extend(check_ai_tells(full_text))
    issues.extend(check_scene_structure(scenes))

    return len(issues) == 0, issues


def run_hook(input_json: str) -> dict[str, Any]:
    """Run the QC hook on input JSON."""
    try:
        data = json.loads(input_json)
    except json.JSONDecodeError as e:
        return {
            "pass": False,
            "issues": [{"code": "SCRIPT_INVALID_JSON", "msg": f"Invalid JSON input: {e}"}],
        }

    passed, issues = validate_script(data)
    return {"pass": passed, "issues": issues}


def main() -> int:
    """Main entrypoint for CLI execution."""
    input_json = sys.stdin.read()
    result = run_hook(input_json)
    print(json.dumps(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
