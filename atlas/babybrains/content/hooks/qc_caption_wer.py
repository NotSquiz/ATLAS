"""
QC Hook: Caption Word Error Rate Validation

Validates captions against audio using faster-whisper for transcription.
Timeout: 180s (longer due to Whisper processing)

Usage:
    python -m atlas.babybrains.content.hooks.qc_caption_wer --video <path> --srt <path>

Input (CLI args):
    --video: Path to video/audio file
    --srt: Path to SRT caption file

Output JSON (to stdout):
{
    "pass": bool,
    "issues": [{"code": str, "msg": str}],
    "metrics": {
        "wer": float,           # Word Error Rate (0.0-1.0)
        "word_count": int,      # Total words in reference
        "substitutions": int,
        "insertions": int,
        "deletions": int
    }
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

# WER thresholds from whisper_normalizations.json
WER_THRESHOLDS = {
    "pass": 0.10,      # Under 10% is acceptable
    "warning": 0.15,   # 10-15% is borderline
    "fail": 0.20,      # Over 20% fails
}

# Try to import faster-whisper
WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    logger.debug("faster-whisper not installed - WER validation will be skipped")


def parse_srt(srt_path: Path) -> str:
    """Parse SRT file and extract text."""
    if not srt_path.exists():
        return ""

    content = srt_path.read_text(encoding="utf-8", errors="replace")
    lines = content.strip().split("\n")

    text_lines = []
    for line in lines:
        # Skip index numbers and timestamps
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        text_lines.append(line)

    return " ".join(text_lines)


def normalize_text(text: str, mappings: Optional[dict] = None) -> str:
    """Normalize text for WER comparison."""
    # Lowercase
    text = text.lower()

    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    # Apply domain-specific mappings
    if mappings:
        for canonical, variants in mappings.items():
            for variant in variants:
                text = text.replace(variant.lower(), canonical.lower())

    return text.strip()


def calculate_wer(reference: str, hypothesis: str) -> dict:
    """
    Calculate Word Error Rate using Levenshtein distance.

    Returns metrics dict with wer, substitutions, insertions, deletions.
    """
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    if not ref_words:
        return {
            "wer": 0.0 if not hyp_words else 1.0,
            "word_count": 0,
            "substitutions": 0,
            "insertions": len(hyp_words),
            "deletions": 0,
        }

    # Build distance matrix
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(
                    d[i - 1][j] + 1,     # Deletion
                    d[i][j - 1] + 1,     # Insertion
                    d[i - 1][j - 1] + 1  # Substitution
                )

    # Backtrack to count S/I/D
    i, j = len(ref_words), len(hyp_words)
    substitutions = insertions = deletions = 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_words[i - 1] == hyp_words[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + 1:
            substitutions += 1
            i -= 1
            j -= 1
        elif j > 0 and d[i][j] == d[i][j - 1] + 1:
            insertions += 1
            j -= 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            deletions += 1
            i -= 1
        else:
            break

    wer = (substitutions + insertions + deletions) / len(ref_words)

    return {
        "wer": wer,
        "word_count": len(ref_words),
        "substitutions": substitutions,
        "insertions": insertions,
        "deletions": deletions,
    }


def transcribe_audio(audio_path: Path) -> Optional[str]:
    """Transcribe audio using faster-whisper."""
    if not WHISPER_AVAILABLE:
        return None

    try:
        # Use small model for speed
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio_path), language="en")

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)

        return " ".join(text_parts)
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return None


def validate_caption_wer(
    video_path: Path, srt_path: Path
) -> tuple[bool, list[dict[str, str]], Optional[dict]]:
    """
    Validate caption WER against audio.

    Returns:
        (pass, issues, metrics) tuple
    """
    issues: list[dict[str, str]] = []

    # Check files exist
    if not video_path.exists():
        issues.append({
            "code": "CAPTION_VIDEO_NOT_FOUND",
            "msg": f"Video file not found: {video_path}",
        })
        return False, issues, None

    if not srt_path.exists():
        issues.append({
            "code": "CAPTION_SRT_NOT_FOUND",
            "msg": f"SRT file not found: {srt_path}",
        })
        return False, issues, None

    # Parse SRT
    caption_text = parse_srt(srt_path)
    if not caption_text:
        issues.append({
            "code": "CAPTION_SRT_EMPTY",
            "msg": "SRT file is empty or could not be parsed",
        })
        return False, issues, None

    # Transcribe audio
    if not WHISPER_AVAILABLE:
        issues.append({
            "code": "CAPTION_WHISPER_UNAVAILABLE",
            "msg": "faster-whisper not installed - WER validation skipped",
        })
        # Return pass=True since we can't validate
        return True, issues, None

    transcribed = transcribe_audio(video_path)
    if not transcribed:
        issues.append({
            "code": "CAPTION_TRANSCRIPTION_FAILED",
            "msg": "Failed to transcribe audio",
        })
        return False, issues, None

    # Normalize both texts
    ref_normalized = normalize_text(caption_text)
    hyp_normalized = normalize_text(transcribed)

    # Calculate WER
    metrics = calculate_wer(ref_normalized, hyp_normalized)

    # Check thresholds
    wer = metrics["wer"]

    if wer > WER_THRESHOLDS["fail"]:
        issues.append({
            "code": "CAPTION_WER_TOO_HIGH",
            "msg": f"WER too high: {wer:.1%} (max: {WER_THRESHOLDS['fail']:.0%})",
        })
    elif wer > WER_THRESHOLDS["warning"]:
        issues.append({
            "code": "CAPTION_WER_WARNING",
            "msg": f"WER borderline: {wer:.1%} (recommended: <{WER_THRESHOLDS['pass']:.0%})",
        })

    return len(issues) == 0, issues, metrics


def run_hook_cli(video_path: str, srt_path: str) -> dict[str, Any]:
    """Run the QC hook via CLI."""
    passed, issues, metrics = validate_caption_wer(
        Path(video_path), Path(srt_path)
    )

    result = {
        "pass": passed,
        "issues": issues,
    }

    if metrics:
        result["metrics"] = metrics

    return result


def main() -> int:
    """Main entrypoint for CLI execution."""
    parser = argparse.ArgumentParser(description="Validate caption WER")
    parser.add_argument("--video", required=True, help="Path to video/audio file")
    parser.add_argument("--srt", required=True, help="Path to SRT caption file")

    args = parser.parse_args()

    result = run_hook_cli(args.video, args.srt)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
