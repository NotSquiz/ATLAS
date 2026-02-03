"""
QC Hook: Montessori Alignment

Validates content for Montessori philosophy alignment.

Input JSON:
{
    "script_text": str,           # Full voiceover text
    "scene_descriptions": [str],  # Visual descriptions per scene
    "age_range": str,             # "0-6m", "6-12m", "12-24m", "24-36m"
    "materials_mentioned": [str]  # Optional list of materials
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
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Load Montessori rules from config
CONFIG_PATH = Path(__file__).parent.parent.parent.parent.parent / "config" / "babybrains" / "montessori_rules.json"


def load_montessori_rules() -> dict:
    """Load Montessori rules from config file."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    # Fallback minimal rules
    return {
        "material_blocklist": {
            "plastic_toys": ["plastic toys", "battery-powered", "electronic toys"],
            "character_merchandise": ["cartoon character", "disney", "paw patrol"],
            "reward_systems": ["sticker chart", "reward chart", "prize"],
        },
        "fantasy_rules": {
            "under_6_prohibited": ["fairy", "dragon", "monster", "unicorn", "magic"],
            "exception_contexts": ["after age 6", "older child"],
        },
        "language_requirements": {
            "avoid_extrinsic": ["good boy", "good girl", "well done", "good job"],
        },
    }


def check_plastic_toys(
    text: str, scenes: list[str], materials: list[str], rules: dict
) -> list[dict[str, str]]:
    """Check for plastic/electronic toys instead of natural materials."""
    issues = []
    combined = (text + " " + " ".join(scenes) + " " + " ".join(materials)).lower()

    blocklist = rules.get("material_blocklist", {}).get("plastic_toys", [])
    for item in blocklist:
        if item.lower() in combined:
            issues.append({
                "code": "MONTESSORI_PLASTIC_TOYS",
                "msg": f"'{item}' - prefer natural materials (wood, cotton, metal)",
            })

    return issues


def check_character_merchandise(
    text: str, scenes: list[str], rules: dict
) -> list[dict[str, str]]:
    """Check for branded character merchandise."""
    issues = []
    combined = (text + " " + " ".join(scenes)).lower()

    blocklist = rules.get("material_blocklist", {}).get("character_merchandise", [])
    for item in blocklist:
        if item.lower() in combined:
            issues.append({
                "code": "MONTESSORI_BRANDED_CHARACTER",
                "msg": f"'{item}' - avoid branded character merchandise",
            })

    return issues


def check_reward_systems(
    text: str, scenes: list[str], rules: dict
) -> list[dict[str, str]]:
    """Check for extrinsic reward systems."""
    issues = []
    combined = (text + " " + " ".join(scenes)).lower()

    blocklist = rules.get("material_blocklist", {}).get("reward_systems", [])
    for item in blocklist:
        if item.lower() in combined:
            issues.append({
                "code": "MONTESSORI_EXTRINSIC_REWARD",
                "msg": f"'{item}' - Montessori avoids extrinsic reward systems",
            })

    return issues


def check_fantasy_content(
    text: str, scenes: list[str], age_range: str, rules: dict
) -> list[dict[str, str]]:
    """Check for inappropriate fantasy content for young children."""
    issues = []

    # Only check for under-6 content
    under_6_ranges = {"0-6m", "6-12m", "12-24m", "24-36m"}
    if age_range not in under_6_ranges:
        return issues

    combined = (text + " " + " ".join(scenes)).lower()

    prohibited = rules.get("fantasy_rules", {}).get("under_6_prohibited", [])
    exceptions = rules.get("fantasy_rules", {}).get("exception_contexts", [])

    # Check if exception context is present
    has_exception = any(exc.lower() in combined for exc in exceptions)
    if has_exception:
        return issues

    for item in prohibited:
        if item.lower() in combined:
            issues.append({
                "code": "MONTESSORI_FANTASY_UNDER6",
                "msg": f"'{item}' - fantasy content not recommended for under 6 years",
            })

    return issues


def check_extrinsic_praise(
    text: str, rules: dict
) -> list[dict[str, str]]:
    """Check for extrinsic praise language."""
    issues = []
    text_lower = text.lower()

    avoid = rules.get("language_requirements", {}).get("avoid_extrinsic", [])
    preferred = rules.get("language_requirements", {}).get("preferred_acknowledgment", [])

    for phrase in avoid:
        if phrase.lower() in text_lower:
            suggestion = "Use descriptive acknowledgment instead: 'I see you...', 'You did it'"
            issues.append({
                "code": "MONTESSORI_EXTRINSIC_REWARD",
                "msg": f"'{phrase}' is extrinsic praise. {suggestion}",
            })

    return issues


def check_montessori_language(
    text: str, rules: dict
) -> list[dict[str, str]]:
    """Check for proper Montessori terminology."""
    issues = []
    text_lower = text.lower()

    # Check preferred terms
    preferred = rules.get("language_requirements", {}).get("preferred_terms", {})

    # Only flag if the wrong term is used AND the right one isn't
    for wrong, right in preferred.items():
        if wrong.lower() in text_lower and right.lower() not in text_lower:
            # Special case: "play" is ok in some contexts
            if wrong == "play":
                # Check if it's in context of "pretend play" or "dramatic play"
                if "pretend play" in text_lower or "dramatic play" in text_lower:
                    continue
            issues.append({
                "code": "MONTESSORI_LANGUAGE",
                "msg": f"Consider using '{right}' instead of '{wrong}'",
            })

    return issues


def validate_montessori(data: dict[str, Any]) -> tuple[bool, list[dict[str, str]]]:
    """
    Validate content for Montessori alignment.

    Returns:
        (pass, issues) tuple
    """
    issues: list[dict[str, str]] = []
    rules = load_montessori_rules()

    script_text = data.get("script_text", "")
    scenes = data.get("scene_descriptions", [])
    age_range = data.get("age_range", "12-24m")
    materials = data.get("materials_mentioned", [])

    # Run all Montessori checks
    issues.extend(check_plastic_toys(script_text, scenes, materials, rules))
    issues.extend(check_character_merchandise(script_text, scenes, rules))
    issues.extend(check_reward_systems(script_text, scenes, rules))
    issues.extend(check_fantasy_content(script_text, scenes, age_range, rules))
    issues.extend(check_extrinsic_praise(script_text, rules))
    issues.extend(check_montessori_language(script_text, rules))

    return len(issues) == 0, issues


def run_hook(input_json: str) -> dict[str, Any]:
    """Run the QC hook on input JSON."""
    try:
        data = json.loads(input_json)
    except json.JSONDecodeError as e:
        return {
            "pass": False,
            "issues": [{"code": "MONTESSORI_INVALID_JSON", "msg": f"Invalid JSON input: {e}"}],
        }

    passed, issues = validate_montessori(data)
    return {"pass": passed, "issues": issues}


def main() -> int:
    """Main entrypoint for CLI execution."""
    input_json = sys.stdin.read()
    result = run_hook(input_json)
    print(json.dumps(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
