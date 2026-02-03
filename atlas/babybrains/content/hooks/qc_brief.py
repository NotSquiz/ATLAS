"""
QC Hook: Brief Structural Validation

Validates that a content brief has all required fields for content production.

Input JSON:
{
    "title": str,
    "hook_text": str,
    "target_length": str,  # "21s", "60s", "90s"
    "age_range": str,      # "0-6m", "6-12m", "12-24m", "24-36m"
    "montessori_principle": str,
    "content_pillar": str,
    "hook_pattern": int    # 1-6
}

Output JSON:
{
    "pass": bool,
    "issues": [{"code": str, "msg": str}]
}
"""

import json
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)

# Valid values
VALID_TARGET_LENGTHS = {"21s", "60s", "90s"}
VALID_AGE_RANGES = {"0-6m", "6-12m", "12-24m", "24-36m"}
VALID_HOOK_PATTERNS = {1, 2, 3, 4, 5, 6}
VALID_CONTENT_PILLARS = {
    "movement",
    "language",
    "practical_life",
    "sensorial",
    "feeding",
    "sleep",
    "play",
    "environment",
}


def validate_brief(data: dict[str, Any]) -> tuple[bool, list[dict[str, str]]]:
    """
    Validate a content brief.

    Returns:
        (pass, issues) tuple
    """
    issues: list[dict[str, str]] = []

    # Required fields
    if not data.get("title"):
        issues.append({
            "code": "BRIEF_MISSING_TITLE",
            "msg": "Brief must have a title",
        })

    if not data.get("hook_text"):
        issues.append({
            "code": "BRIEF_MISSING_HOOK_TEXT",
            "msg": "Brief must have hook_text for video opening",
        })

    if not data.get("age_range"):
        issues.append({
            "code": "BRIEF_MISSING_AGE_RANGE",
            "msg": "Brief must specify target age_range (0-6m, 6-12m, 12-24m, 24-36m)",
        })
    elif data.get("age_range") not in VALID_AGE_RANGES:
        issues.append({
            "code": "BRIEF_INVALID_AGE_RANGE",
            "msg": f"age_range must be one of: {', '.join(sorted(VALID_AGE_RANGES))}",
        })

    if not data.get("target_length"):
        issues.append({
            "code": "BRIEF_MISSING_TARGET_LENGTH",
            "msg": "Brief must specify target_length (21s, 60s, 90s)",
        })
    elif data.get("target_length") not in VALID_TARGET_LENGTHS:
        issues.append({
            "code": "BRIEF_INVALID_TARGET_LENGTH",
            "msg": f"target_length must be one of: {', '.join(sorted(VALID_TARGET_LENGTHS))}",
        })

    # Optional but validated if present
    if data.get("montessori_principle"):
        principle = data["montessori_principle"]
        # Basic validation - should be a non-empty string
        if not isinstance(principle, str) or len(principle) < 3:
            issues.append({
                "code": "BRIEF_INVALID_MONTESSORI_PRINCIPLE",
                "msg": "montessori_principle must be a valid principle slug",
            })

    if data.get("content_pillar"):
        pillar = data["content_pillar"]
        if pillar not in VALID_CONTENT_PILLARS:
            issues.append({
                "code": "BRIEF_INVALID_CONTENT_PILLAR",
                "msg": f"content_pillar must be one of: {', '.join(sorted(VALID_CONTENT_PILLARS))}",
            })

    if data.get("hook_pattern") is not None:
        pattern = data["hook_pattern"]
        if pattern not in VALID_HOOK_PATTERNS:
            issues.append({
                "code": "BRIEF_INVALID_HOOK_PATTERN",
                "msg": f"hook_pattern must be 1-6, got: {pattern}",
            })

    # Hook text quality checks
    hook_text = data.get("hook_text", "")
    if hook_text:
        # Check length (should be punchy, under 100 chars)
        if len(hook_text) > 100:
            issues.append({
                "code": "BRIEF_HOOK_TOO_LONG",
                "msg": f"hook_text should be under 100 chars, got: {len(hook_text)}",
            })

        # Check for question or statement pattern
        if not hook_text.endswith(("?", ".", "!", "...")):
            issues.append({
                "code": "BRIEF_HOOK_NO_PUNCTUATION",
                "msg": "hook_text should end with punctuation (?, ., !, ...)",
            })

    return len(issues) == 0, issues


def run_hook(input_json: str) -> dict[str, Any]:
    """Run the QC hook on input JSON."""
    try:
        data = json.loads(input_json)
    except json.JSONDecodeError as e:
        return {
            "pass": False,
            "issues": [{"code": "BRIEF_INVALID_JSON", "msg": f"Invalid JSON input: {e}"}],
        }

    passed, issues = validate_brief(data)
    return {"pass": passed, "issues": issues}


def main() -> int:
    """Main entrypoint for CLI execution."""
    input_json = sys.stdin.read()
    result = run_hook(input_json)
    print(json.dumps(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
