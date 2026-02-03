"""
QC Hook: Caption Safe Zone Validation

Validates that captions don't extend into platform-specific safe zones.
Supports ASS and VTT formats (not SRT - lacks position metadata).

Usage:
    python -m atlas.babybrains.content.hooks.qc_safezone --subtitle <path> --platform <platform>

Input (CLI args):
    --subtitle: Path to subtitle file (ASS or VTT)
    --platform: Platform name (tiktok, instagram_reels, youtube_shorts, facebook_reels)

Output JSON (to stdout):
{
    "pass": bool,
    "issues": [{"code": str, "msg": str}]
}
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Load safe zone thresholds from config
CONFIG_PATH = Path(__file__).parent.parent.parent.parent.parent / "config" / "babybrains" / "safezone_thresholds.json"


def load_safezone_config() -> dict:
    """Load safe zone thresholds from config."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    # Fallback minimal config
    return {
        "platforms": {
            "tiktok": {
                "safe_zones": {
                    "top": {"pixels": 150},
                    "bottom": {"pixels": 270},
                    "left": {"pixels": 40},
                    "right": {"pixels": 100},
                },
            },
        },
        "supported_formats": ["ass", "vtt"],
    }


def get_file_format(file_path: Path) -> Optional[str]:
    """Detect subtitle file format."""
    suffix = file_path.suffix.lower()
    if suffix == ".ass" or suffix == ".ssa":
        return "ass"
    elif suffix == ".vtt":
        return "vtt"
    elif suffix == ".srt":
        return "srt"
    return None


def parse_ass_positions(content: str) -> list[dict]:
    """
    Parse ASS file and extract position information.

    ASS format uses:
    - \\pos(x,y) for absolute positioning
    - Alignment codes (\\an1-9) for screen position
    - PlayResX/PlayResY for resolution reference
    """
    positions = []

    # Get resolution from header
    play_res_x = 1920  # Default
    play_res_y = 1080  # Default

    for line in content.split("\n"):
        if line.startswith("PlayResX:"):
            try:
                play_res_x = int(line.split(":")[1].strip())
            except ValueError:
                pass
        elif line.startswith("PlayResY:"):
            try:
                play_res_y = int(line.split(":")[1].strip())
            except ValueError:
                pass

    # Parse dialogue lines
    for line in content.split("\n"):
        if not line.startswith("Dialogue:"):
            continue

        # Extract position from style overrides
        pos_match = re.search(r"\\pos\((\d+),(\d+)\)", line)
        if pos_match:
            x = int(pos_match.group(1))
            y = int(pos_match.group(2))
            # Scale to 1080x1920 if different resolution
            if play_res_y != 1920:
                y = int(y * 1920 / play_res_y)
            if play_res_x != 1080:
                x = int(x * 1080 / play_res_x)
            positions.append({"x": x, "y": y, "source": "pos"})

        # Extract alignment
        an_match = re.search(r"\\an(\d)", line)
        if an_match:
            alignment = int(an_match.group(1))
            # Map alignment to approximate Y position
            # 1-3: bottom, 4-6: middle, 7-9: top
            if alignment <= 3:
                y = 1800  # Bottom area
            elif alignment <= 6:
                y = 960   # Middle
            else:
                y = 120   # Top area
            positions.append({"y": y, "alignment": alignment, "source": "an"})

    return positions


def parse_vtt_positions(content: str) -> list[dict]:
    """
    Parse VTT file and extract position information.

    VTT format uses cue settings like:
    - position:50%
    - line:80%
    - align:center
    """
    positions = []

    # Regex for VTT cue settings
    cue_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})(.*)"
    )

    for line in content.split("\n"):
        match = cue_pattern.match(line)
        if match:
            settings = match.group(3)

            # Extract line position
            line_match = re.search(r"line:(\d+)%?", settings)
            if line_match:
                line_pct = int(line_match.group(1))
                y = int(1920 * line_pct / 100)  # Convert to pixels
                positions.append({"y": y, "source": "line"})

            # Extract position
            pos_match = re.search(r"position:(\d+)%?", settings)
            if pos_match:
                pos_pct = int(pos_match.group(1))
                x = int(1080 * pos_pct / 100)
                positions.append({"x": x, "source": "position"})

    return positions


def check_positions(
    positions: list[dict], platform: str, config: dict
) -> list[dict[str, str]]:
    """Check if any positions violate safe zones."""
    issues = []

    platform_config = config.get("platforms", {}).get(platform)
    if not platform_config:
        issues.append({
            "code": "SAFEZONE_UNKNOWN_PLATFORM",
            "msg": f"Unknown platform: {platform}",
        })
        return issues

    zones = platform_config.get("safe_zones", {})
    top_zone = zones.get("top", {}).get("pixels", 0)
    bottom_zone = zones.get("bottom", {}).get("pixels", 0)
    left_zone = zones.get("left", {}).get("pixels", 0)
    right_zone = zones.get("right", {}).get("pixels", 0)

    for pos in positions:
        y = pos.get("y")
        x = pos.get("x")

        # Check top violation
        if y is not None and y < top_zone:
            issues.append({
                "code": "SAFEZONE_TOP_VIOLATION",
                "msg": f"Caption at y={y}px is in top safe zone ({top_zone}px)",
            })

        # Check bottom violation (1920 - bottom_zone)
        if y is not None and y > (1920 - bottom_zone):
            issues.append({
                "code": "SAFEZONE_BOTTOM_VIOLATION",
                "msg": f"Caption at y={y}px is in bottom safe zone ({bottom_zone}px from bottom)",
            })

        # Check left violation
        if x is not None and x < left_zone:
            issues.append({
                "code": "SAFEZONE_SIDE_VIOLATION",
                "msg": f"Caption at x={x}px is in left safe zone ({left_zone}px)",
            })

        # Check right violation (1080 - right_zone)
        if x is not None and x > (1080 - right_zone):
            issues.append({
                "code": "SAFEZONE_SIDE_VIOLATION",
                "msg": f"Caption at x={x}px is in right safe zone ({right_zone}px from right)",
            })

    return issues


def validate_safezone(
    subtitle_path: Path, platform: str
) -> tuple[bool, list[dict[str, str]]]:
    """
    Validate subtitle safe zones.

    Returns:
        (pass, issues) tuple
    """
    issues: list[dict[str, str]] = []
    config = load_safezone_config()

    # Check file exists
    if not subtitle_path.exists():
        issues.append({
            "code": "SAFEZONE_FILE_NOT_FOUND",
            "msg": f"Subtitle file not found: {subtitle_path}",
        })
        return False, issues

    # Check format
    file_format = get_file_format(subtitle_path)

    if file_format == "srt":
        issues.append({
            "code": "SAFEZONE_FORMAT_UNSUPPORTED",
            "msg": "SRT format lacks position metadata required for safe zone validation. Use ASS or VTT format.",
        })
        # Still return pass since we can't validate
        return True, issues

    if file_format not in config.get("supported_formats", ["ass", "vtt"]):
        issues.append({
            "code": "SAFEZONE_FORMAT_UNSUPPORTED",
            "msg": f"Unsupported subtitle format: {file_format}",
        })
        return True, issues

    # Read and parse file
    content = subtitle_path.read_text(encoding="utf-8", errors="replace")

    if file_format == "ass":
        positions = parse_ass_positions(content)
    elif file_format == "vtt":
        positions = parse_vtt_positions(content)
    else:
        positions = []

    if not positions:
        # No position metadata found - can't validate
        logger.debug("No position metadata found in subtitle file")
        return True, issues

    # Check positions against safe zones
    position_issues = check_positions(positions, platform, config)
    issues.extend(position_issues)

    return len(issues) == 0, issues


def run_hook_cli(subtitle_path: str, platform: str) -> dict[str, Any]:
    """Run the QC hook via CLI."""
    passed, issues = validate_safezone(Path(subtitle_path), platform)
    return {"pass": passed, "issues": issues}


def main() -> int:
    """Main entrypoint for CLI execution."""
    parser = argparse.ArgumentParser(description="Validate caption safe zones")
    parser.add_argument("--subtitle", required=True, help="Path to subtitle file (ASS or VTT)")
    parser.add_argument("--platform", required=True,
                       choices=["tiktok", "instagram_reels", "youtube_shorts", "facebook_reels"],
                       help="Target platform")

    args = parser.parse_args()

    result = run_hook_cli(args.subtitle, args.platform)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
