"""
QC Hook: Safety Gate

Validates content for safety hazards, supervision requirements, and medical claims.

Input JSON:
{
    "script_text": str,           # Full voiceover text
    "scene_descriptions": [str],  # Visual descriptions per scene
    "age_range": str              # "0-6m", "6-12m", "12-24m", "24-36m"
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

# Load safety rules from config
CONFIG_PATH = Path(__file__).parent.parent.parent.parent.parent / "config" / "babybrains" / "safety_rules.json"


def load_safety_rules() -> dict:
    """Load safety rules from config file."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    # Fallback minimal rules
    return {
        "hazard_keywords": {
            "choking_hazards": ["marble", "coin", "button", "battery", "small ball"],
            "unsupervised_activities": ["leave alone", "unsupervised", "without watching"],
            "dangerous_items": ["sharp", "knife", "scissors"],
            "water_hazards": ["bath alone", "pool unsupervised"],
        },
        "medical_claim_patterns": ["diagnose", "cure", "treat", "therapy", "symptom"],
    }


def check_choking_hazards(
    text: str, scenes: list[str], age_range: str, rules: dict
) -> list[dict[str, str]]:
    """Check for choking hazards without appropriate warnings."""
    issues = []
    combined = text.lower() + " " + " ".join(scenes).lower()

    hazards = rules.get("hazard_keywords", {}).get("choking_hazards", [])
    for hazard in hazards:
        if hazard.lower() in combined:
            # Check if there's a warning nearby
            warning_patterns = ["supervise", "age appropriate", "watch", "caution"]
            has_warning = any(p in combined for p in warning_patterns)
            if not has_warning:
                issues.append({
                    "code": "SAFETY_CHOKING_HAZARD",
                    "msg": f"Choking hazard '{hazard}' mentioned without supervision warning",
                })

    return issues


def check_supervision(
    text: str, scenes: list[str], rules: dict
) -> list[dict[str, str]]:
    """Check for unsupervised activity suggestions."""
    issues = []
    combined = text.lower() + " " + " ".join(scenes).lower()

    patterns = rules.get("hazard_keywords", {}).get("unsupervised_activities", [])
    for pattern in patterns:
        if pattern.lower() in combined:
            issues.append({
                "code": "SAFETY_UNSUPERVISED",
                "msg": f"Content suggests unsupervised activity: '{pattern}'",
            })

    return issues


def check_dangerous_items(
    text: str, scenes: list[str], rules: dict
) -> list[dict[str, str]]:
    """Check for dangerous items without safety context."""
    issues = []
    combined = text.lower() + " " + " ".join(scenes).lower()

    items = rules.get("hazard_keywords", {}).get("dangerous_items", [])
    safety_words = ["child-safe", "safety", "rounded", "plastic", "wooden"]

    for item in items:
        if item.lower() in combined:
            # Check if safety context present
            has_safety = any(s in combined for s in safety_words)
            if not has_safety:
                issues.append({
                    "code": "SAFETY_DANGEROUS_ITEM",
                    "msg": f"Dangerous item '{item}' mentioned without safety context",
                })

    return issues


def check_water_hazards(
    text: str, scenes: list[str], rules: dict
) -> list[dict[str, str]]:
    """Check for water hazards without supervision."""
    issues = []
    combined = text.lower() + " " + " ".join(scenes).lower()

    patterns = rules.get("hazard_keywords", {}).get("water_hazards", [])
    for pattern in patterns:
        if pattern.lower() in combined:
            issues.append({
                "code": "SAFETY_WATER_HAZARD",
                "msg": f"Water hazard: '{pattern}' - requires constant adult supervision",
            })

    # Check for any water activity without supervision mention
    water_activities = ["water play", "splash", "bath", "swimming", "paddling pool"]
    supervision_words = ["supervise", "watch", "adult", "never leave", "stay with"]

    for activity in water_activities:
        if activity in combined:
            has_supervision = any(s in combined for s in supervision_words)
            if not has_supervision:
                issues.append({
                    "code": "SAFETY_WATER_HAZARD",
                    "msg": f"Water activity '{activity}' requires supervision mention",
                })
                break  # Only report once

    return issues


def check_medical_claims(text: str, rules: dict) -> list[dict[str, str]]:
    """Check for medical claims that should use educational framing."""
    issues = []
    text_lower = text.lower()

    patterns = rules.get("medical_claim_patterns", [])
    alternatives = rules.get("allowed_medical_alternatives", [])

    for pattern in patterns:
        if pattern.lower() in text_lower:
            # Check if proper framing is used
            has_proper_framing = any(
                alt.lower() in text_lower for alt in alternatives
            )
            if not has_proper_framing:
                issues.append({
                    "code": "SAFETY_MEDICAL_CLAIM",
                    "msg": f"Medical term '{pattern}' used - reframe as educational content",
                })

    return issues


def check_age_appropriate(
    text: str, scenes: list[str], age_range: str, rules: dict
) -> list[dict[str, str]]:
    """Check for age-inappropriate content."""
    issues = []
    combined = text.lower() + " " + " ".join(scenes).lower()

    age_rules = rules.get("age_appropriate_rules", {}).get(age_range, {})
    prohibited = age_rules.get("prohibited_items", [])

    for item in prohibited:
        if item.lower() in combined:
            issues.append({
                "code": "SAFETY_AGE_INAPPROPRIATE",
                "msg": f"'{item}' is not appropriate for age range {age_range}",
            })

    return issues


def validate_safety(data: dict[str, Any]) -> tuple[bool, list[dict[str, str]]]:
    """
    Validate content for safety.

    Returns:
        (pass, issues) tuple
    """
    issues: list[dict[str, str]] = []
    rules = load_safety_rules()

    script_text = data.get("script_text", "")
    scenes = data.get("scene_descriptions", [])
    age_range = data.get("age_range", "12-24m")

    # Run all safety checks
    issues.extend(check_choking_hazards(script_text, scenes, age_range, rules))
    issues.extend(check_supervision(script_text, scenes, rules))
    issues.extend(check_dangerous_items(script_text, scenes, rules))
    issues.extend(check_water_hazards(script_text, scenes, rules))
    issues.extend(check_medical_claims(script_text, rules))
    issues.extend(check_age_appropriate(script_text, scenes, age_range, rules))

    return len(issues) == 0, issues


def run_hook(input_json: str) -> dict[str, Any]:
    """Run the QC hook on input JSON."""
    try:
        data = json.loads(input_json)
    except json.JSONDecodeError as e:
        return {
            "pass": False,
            "issues": [{"code": "SAFETY_INVALID_JSON", "msg": f"Invalid JSON input: {e}"}],
        }

    passed, issues = validate_safety(data)
    return {"pass": passed, "issues": issues}


def main() -> int:
    """Main entrypoint for CLI execution."""
    input_json = sys.stdin.read()
    result = run_hook(input_json)
    print(json.dumps(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
