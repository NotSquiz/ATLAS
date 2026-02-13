#!/usr/bin/env python3
"""
Strip production_notes and content_production fields from canonical YAML files.

D115: Activity Atoms are pure knowledge artifacts. All video/content production
decisions belong to a downstream Director Agent.

Handles three file patterns:
  1. Files with BOTH production_notes + content_production
  2. Files with only production_notes
  3. Files with only content_production

Uses # TAGS or tags: as the safe boundary — this field consistently follows
production blocks in all files.

Safety: NEVER strips au_safety_overlays or any content outside the production
block boundaries.

Usage:
    python scripts/strip_production_fields.py              # Execute strip
    python scripts/strip_production_fields.py --dry-run    # Report only
"""

import argparse
import glob
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Directories to process
KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent.parent / "knowledge"
TARGET_DIRS = [
    KNOWLEDGE_ROOT / "data" / "canonical" / "activities",
    KNOWLEDGE_ROOT / "data" / "canonical" / "guidance",
    KNOWLEDGE_ROOT / "data" / "staging" / "needs_voice_elevation",
]

# Regex patterns for production blocks and their comment headers.
# Strategy: match from the comment header (or field start) through to the
# line BEFORE the tags section.
#
# Pattern matches:
#   - Optional blank line before the comment header
#   - Comment header line (various formats)
#   - All content until (but not including) a line starting with "# TAGS" or "tags:"
#
# The regex is applied to the entire file text.

PRODUCTION_BLOCK_RE = re.compile(
    r"""
    # Match the production block(s) between au_compliance/au_safety and tags
    # Capture from production comment header through to tags boundary
    (?:^[ \t]*\n)?                      # Optional blank line before header
    (?:
        ^[ \t]*\#[ \t]*(?:PRODUCTION[ \t]+METADATA|PRODUCTION[ \t]+NOTES|
        CONTENT[ \t]+PRODUCTION(?:[ \t]+NOTES)?|SECTION[ \t]+31[^\n]*)[ \t]*\n
    )                                   # Comment header line
    (?:(?!^[ \t]*\#[ \t]*TAGS|^tags:)   # Negative lookahead: stop before tags
        .+\n                            # Consume lines
    )*
    """,
    re.MULTILINE | re.VERBOSE,
)

# Fallback: catch production_notes: or content_production: that appear
# WITHOUT a comment header (shouldn't happen, but safety net)
BARE_FIELD_RE = re.compile(
    r"""
    (?:^[ \t]*\n)?                      # Optional blank line
    ^(?:production_notes|content_production):[ \t]*[^\n]*\n   # Field start
    (?:(?!^[ \t]*\#[ \t]*TAGS|^tags:|^[a-z_]+:[ \t])  # Stop at tags or next top-level field
        .+\n
    )*
    """,
    re.MULTILINE | re.VERBOSE,
)


def find_yaml_files() -> list[Path]:
    """Find all YAML files across target directories."""
    files = []
    for d in TARGET_DIRS:
        if d.exists():
            pattern = str(d / "**" / "*.yaml")
            files.extend(Path(f) for f in glob.glob(pattern, recursive=True))
    return sorted(files)


def has_production_fields(text: str) -> bool:
    """Check if text contains production_notes or content_production."""
    return bool(
        re.search(r"^production_notes:", text, re.MULTILINE)
        or re.search(r"^content_production:", text, re.MULTILINE)
    )


def strip_production(text: str) -> str:
    """
    Strip all production blocks from YAML text.

    Returns cleaned text with production blocks removed.
    """
    original = text

    # Phase 1: Strip blocks that have comment headers
    text = PRODUCTION_BLOCK_RE.sub("", text)

    # Phase 2: Strip any remaining bare production_notes/content_production fields
    # (fields without a preceding comment header)
    if has_production_fields(text):
        text = BARE_FIELD_RE.sub("", text)

    # Phase 3: Clean up multiple consecutive blank lines (max 1)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Safety check: ensure we didn't accidentally strip au_safety_overlays
    if "au_safety_overlays" in original and "au_safety_overlays" not in text:
        logger.error("SAFETY CHECK FAILED: au_safety_overlays was stripped!")
        return original  # Return original to prevent data loss

    return text


def validate_result(filepath: Path, original: str, cleaned: str) -> list[str]:
    """Validate the cleaned file hasn't lost important content."""
    issues = []

    # Check tags section still exists
    if re.search(r"^tags:", original, re.MULTILINE):
        if not re.search(r"^tags:", cleaned, re.MULTILINE):
            issues.append(f"{filepath.name}: tags: section was accidentally stripped")

    # Check parent_search_terms still exists (activity files)
    if re.search(r"^parent_search_terms:", original, re.MULTILINE):
        if not re.search(r"^parent_search_terms:", cleaned, re.MULTILINE):
            issues.append(
                f"{filepath.name}: parent_search_terms was accidentally stripped"
            )

    # Check no production fields remain
    if re.search(r"^production_notes:", cleaned, re.MULTILINE):
        issues.append(f"{filepath.name}: production_notes still present after strip")
    if re.search(r"^content_production:", cleaned, re.MULTILINE):
        issues.append(f"{filepath.name}: content_production still present after strip")

    # Check au_safety_overlays preserved
    if "au_safety_overlays" in original and "au_safety_overlays" not in cleaned:
        issues.append(f"{filepath.name}: au_safety_overlays was stripped (CRITICAL)")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Strip production fields from canonical YAML files (D115)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be stripped without writing",
    )
    args = parser.parse_args()

    files = find_yaml_files()
    if not files:
        logger.error("No YAML files found in target directories.")
        return 2

    logger.info(f"Found {len(files)} YAML files across {len(TARGET_DIRS)} directories.")

    modified = 0
    skipped = 0
    total_lines_removed = 0
    all_issues: list[str] = []

    for filepath in files:
        original = filepath.read_text(encoding="utf-8")

        if not has_production_fields(original):
            skipped += 1
            continue

        cleaned = strip_production(original)
        issues = validate_result(filepath, original, cleaned)
        all_issues.extend(issues)

        if issues:
            for issue in issues:
                logger.error(f"  ISSUE: {issue}")
            continue

        orig_lines = original.count("\n")
        clean_lines = cleaned.count("\n")
        lines_removed = orig_lines - clean_lines

        rel_path = filepath.relative_to(KNOWLEDGE_ROOT)
        logger.info(
            f"  {'[DRY RUN] ' if args.dry_run else ''}"
            f"{rel_path}: {orig_lines} → {clean_lines} lines "
            f"(-{lines_removed})"
        )

        if not args.dry_run:
            filepath.write_text(cleaned, encoding="utf-8")

        modified += 1
        total_lines_removed += lines_removed

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"{'DRY RUN ' if args.dry_run else ''}SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Files scanned:   {len(files)}")
    logger.info(f"Files modified:  {modified}")
    logger.info(f"Files skipped:   {skipped} (no production fields)")
    logger.info(f"Lines removed:   {total_lines_removed}")

    if all_issues:
        logger.info("")
        logger.error(f"ISSUES FOUND: {len(all_issues)}")
        for issue in all_issues:
            logger.error(f"  - {issue}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
