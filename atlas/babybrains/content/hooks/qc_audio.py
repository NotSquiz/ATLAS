"""
QC Hook: Audio Levels Validation

Validates audio levels using ffmpeg loudnorm filter.
Timeout: 180s (longer due to ffmpeg processing)

Usage:
    python -m atlas.babybrains.content.hooks.qc_audio <audio_file> [--master]

Input (CLI args):
    audio_file: Path to audio file (wav, mp3, m4a)
    --master: If set, validates as master (stricter true peak)

Output JSON (to stdout):
{
    "pass": bool,
    "issues": [{"code": str, "msg": str}],
    "measurements": {
        "input_i": float,    # Integrated loudness (LUFS)
        "input_tp": float,   # True peak (dBTP)
        "input_lra": float,  # Loudness range (LU)
        "input_thresh": float
    }
}
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Audio specs from export_presets.json
VOICEOVER_SPECS = {
    "target_lufs": -14,
    "true_peak_max": -1.0,
    "lufs_tolerance": 2.0,  # +/- 2 LUFS from target
}

MASTER_SPECS = {
    "target_lufs": -14,
    "true_peak_max": -1.0,
    "loudness_range_max": 8.0,  # Max LRA for consistency
    "lufs_tolerance": 1.0,  # Stricter for master
}


def run_ffmpeg_loudnorm(file_path: Path) -> Optional[dict]:
    """
    Run ffmpeg loudnorm filter to measure audio levels.

    Returns measurements dict or None on error.
    """
    cmd = [
        "ffmpeg",
        "-i", str(file_path),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json",
        "-f", "null",
        "-"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for audio processing
        )
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg loudnorm timed out")
        return None
    except FileNotFoundError:
        logger.error("ffmpeg not found - install ffmpeg")
        return None

    # Parse JSON from stderr (ffmpeg outputs to stderr)
    stderr = result.stderr

    # Find the JSON block in the output
    try:
        # Look for the JSON output block
        json_start = stderr.rfind("{")
        json_end = stderr.rfind("}") + 1

        if json_start == -1 or json_end <= json_start:
            logger.error("Could not find JSON in ffmpeg output")
            return None

        json_str = stderr[json_start:json_end]
        measurements = json.loads(json_str)
        return measurements
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ffmpeg JSON: {e}")
        return None


def validate_audio(
    file_path: Path, is_master: bool = False
) -> tuple[bool, list[dict[str, str]], Optional[dict]]:
    """
    Validate audio levels.

    Returns:
        (pass, issues, measurements) tuple
    """
    issues: list[dict[str, str]] = []

    # Check file exists
    if not file_path.exists():
        issues.append({
            "code": "AUDIO_FILE_NOT_FOUND",
            "msg": f"Audio file not found: {file_path}",
        })
        return False, issues, None

    # Get measurements
    measurements = run_ffmpeg_loudnorm(file_path)

    if measurements is None:
        issues.append({
            "code": "AUDIO_MEASUREMENT_FAILED",
            "msg": "Failed to measure audio levels with ffmpeg",
        })
        return False, issues, None

    # Parse measurements
    try:
        lufs = float(measurements.get("input_i", 0))
        true_peak = float(measurements.get("input_tp", 0))
        lra = float(measurements.get("input_lra", 0))
    except (TypeError, ValueError) as e:
        issues.append({
            "code": "AUDIO_MEASUREMENT_INVALID",
            "msg": f"Invalid measurement values: {e}",
        })
        return False, issues, measurements

    # Select specs based on master flag
    specs = MASTER_SPECS if is_master else VOICEOVER_SPECS

    # Check LUFS
    target = specs["target_lufs"]
    tolerance = specs["lufs_tolerance"]

    if lufs < target - tolerance:
        issues.append({
            "code": "AUDIO_LUFS_TOO_QUIET",
            "msg": f"Audio too quiet: {lufs:.1f} LUFS (target: {target} +/- {tolerance})",
        })
    elif lufs > target + tolerance:
        issues.append({
            "code": "AUDIO_LUFS_TOO_LOUD",
            "msg": f"Audio too loud: {lufs:.1f} LUFS (target: {target} +/- {tolerance})",
        })

    # Check true peak
    tp_max = specs["true_peak_max"]
    if true_peak > tp_max:
        issues.append({
            "code": "AUDIO_TRUE_PEAK_EXCEEDED",
            "msg": f"True peak too high: {true_peak:.1f} dBTP (max: {tp_max})",
        })

    # Check LRA for master
    if is_master:
        lra_max = specs.get("loudness_range_max", 8.0)
        if lra > lra_max:
            issues.append({
                "code": "AUDIO_LRA_EXCEEDED",
                "msg": f"Loudness range too wide: {lra:.1f} LU (max: {lra_max})",
            })

    return len(issues) == 0, issues, measurements


def run_hook_cli(file_path: str, is_master: bool = False) -> dict[str, Any]:
    """Run the QC hook via CLI."""
    path = Path(file_path)
    passed, issues, measurements = validate_audio(path, is_master)

    result = {
        "pass": passed,
        "issues": issues,
    }

    if measurements:
        result["measurements"] = {
            "input_i": measurements.get("input_i"),
            "input_tp": measurements.get("input_tp"),
            "input_lra": measurements.get("input_lra"),
            "input_thresh": measurements.get("input_thresh"),
        }

    return result


def main() -> int:
    """Main entrypoint for CLI execution."""
    parser = argparse.ArgumentParser(description="Validate audio levels")
    parser.add_argument("file", help="Path to audio file")
    parser.add_argument("--master", action="store_true", help="Validate as master audio")

    args = parser.parse_args()

    result = run_hook_cli(args.file, args.master)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
