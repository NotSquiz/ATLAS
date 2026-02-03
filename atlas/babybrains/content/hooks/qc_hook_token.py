"""
QC Hook: Hook in Scene 1 Validation

Validates that the hook text appears in scene 1 of the script.

Input JSON:
{
    "scenes": [
        {
            "number": 1,
            "vo_text": str,
            ...
        },
        ...
    ],
    "hook_text": str
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

# Word limits per format
HOOK_WORD_LIMITS = {
    "21s": 15,  # Hook should be ~15 words for 21s video
    "60s": 25,  # Hook should be ~25 words for 60s video
    "90s": 30,  # Hook should be ~30 words for 90s video
}


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    import re
    # Lowercase, remove extra spaces, basic punctuation
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def text_similarity(hook: str, scene_text: str) -> float:
    """Calculate similarity between hook and scene text."""
    hook_norm = normalize_text(hook)
    scene_norm = normalize_text(scene_text)

    # Check for exact match
    if hook_norm in scene_norm:
        return 1.0

    # Check word overlap
    hook_words = set(hook_norm.split())
    scene_words = set(scene_norm.split())

    if not hook_words:
        return 0.0

    overlap = len(hook_words & scene_words)
    return overlap / len(hook_words)


def validate_hook_token(data: dict[str, Any]) -> tuple[bool, list[dict[str, str]]]:
    """
    Validate that hook text appears in scene 1.

    Returns:
        (pass, issues) tuple
    """
    issues: list[dict[str, str]] = []

    scenes = data.get("scenes", [])
    hook_text = data.get("hook_text", "")

    # Basic validation
    if not hook_text:
        issues.append({
            "code": "HOOK_TOKEN_MISSING",
            "msg": "No hook_text provided for validation",
        })
        return False, issues

    if not scenes:
        issues.append({
            "code": "HOOK_TOKEN_NO_SCENES",
            "msg": "No scenes provided for validation",
        })
        return False, issues

    # Get scene 1
    scene_1 = None
    for scene in scenes:
        if scene.get("number") == 1:
            scene_1 = scene
            break

    if scene_1 is None:
        # Try first scene if no number
        scene_1 = scenes[0] if scenes else None

    if scene_1 is None:
        issues.append({
            "code": "HOOK_TOKEN_NO_SCENE_1",
            "msg": "Could not find scene 1 in script",
        })
        return False, issues

    # Get scene 1 voiceover text
    scene_1_vo = scene_1.get("vo_text", "")
    if not scene_1_vo:
        issues.append({
            "code": "HOOK_TOKEN_EMPTY_SCENE",
            "msg": "Scene 1 has no voiceover text",
        })
        return False, issues

    # Check if hook appears in scene 1
    similarity = text_similarity(hook_text, scene_1_vo)

    if similarity < 0.5:  # Less than 50% word overlap
        issues.append({
            "code": "HOOK_TOKEN_MISSING",
            "msg": f"Hook text not found in scene 1 (similarity: {similarity:.0%})",
        })

    # Check hook word count
    hook_words = len(hook_text.split())
    if hook_words > 30:
        issues.append({
            "code": "HOOK_WORD_COUNT",
            "msg": f"Hook is too long ({hook_words} words). Keep under 30 words for impact.",
        })

    # Check hook timing (should be in first 5 seconds = first ~12 words at 130 WPM)
    scene_1_words = scene_1_vo.split()
    first_12_words = " ".join(scene_1_words[:12])

    hook_similarity_early = text_similarity(hook_text, first_12_words)
    if hook_similarity_early < 0.3 and similarity >= 0.5:
        issues.append({
            "code": "HOOK_TOO_LATE",
            "msg": "Hook should appear in first 5 seconds (first ~12 words)",
        })

    return len(issues) == 0, issues


def run_hook(input_json: str) -> dict[str, Any]:
    """Run the QC hook on input JSON."""
    try:
        data = json.loads(input_json)
    except json.JSONDecodeError as e:
        return {
            "pass": False,
            "issues": [{"code": "HOOK_INVALID_JSON", "msg": f"Invalid JSON input: {e}"}],
        }

    passed, issues = validate_hook_token(data)
    return {"pass": passed, "issues": issues}


def main() -> int:
    """Main entrypoint for CLI execution."""
    input_json = sys.stdin.read()
    result = run_hook(input_json)
    print(json.dumps(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
