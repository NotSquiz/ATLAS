#!/usr/bin/env python3
"""
Regression audit for canonical Activity Atom YAMLs.

Runs all 13 AI detection categories from ai_detection.py against every
canonical YAML in knowledge/data/canonical/activities/. Reports which
files would now fail under current detection rules.

Usage:
    python scripts/audit_canonicals.py              # Full report
    python scripts/audit_canonicals.py --verbose    # Show each issue with location
    python scripts/audit_canonicals.py --category 5 # Test single category only
"""

import argparse
import glob
import logging
import os
import re
import sys
from pathlib import Path

# Add project root to path so we can import atlas modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from atlas.babybrains.ai_detection import (
    check_ai_cliches,
    check_conversational_ai_tells,
    check_em_dashes,
    check_enthusiasm,
    check_filler_phrases,
    check_formal_transitions,
    check_hedge_stacking,
    check_hollow_affirmations,
    check_list_intros,
    check_non_contractions,
    check_outcome_promises,
    check_pressure_language,
    check_superlatives,
    get_severity,
)

logger = logging.getLogger(__name__)

# Category number → checker function mapping
CATEGORY_CHECKERS = {
    1: ("SUPERLATIVES", check_superlatives),
    2: ("OUTCOME_PROMISES", check_outcome_promises),
    3: ("PRESSURE_LANGUAGE", check_pressure_language),
    4: ("FORMAL_TRANSITIONS", check_formal_transitions),
    5: ("NON_CONTRACTIONS", check_non_contractions),
    6: ("HOLLOW_AFFIRMATIONS", check_hollow_affirmations),
    7: ("AI_CLICHES", check_ai_cliches),
    8: ("HEDGE_STACKING", check_hedge_stacking),
    9: ("LIST_INTROS", check_list_intros),
    10: ("ENTHUSIASM_MARKERS", check_enthusiasm),
    11: ("FILLER_PHRASES", check_filler_phrases),
    12: ("EM_DASHES", check_em_dashes),
    13: ("CONVERSATIONAL_AI_TELLS", check_conversational_ai_tells),
}

# Fields that contain prose text (check these for AI patterns)
PROSE_FIELDS = {
    "title",
    "summary",
    "description",
    "rationale",
    "qc_notes",
    "why_it_works",
    "what_to_notice",
    "preparation",
    "contraindications",
    "grounded_in_principles",
    "modern_validation",
    "au_cultural_adaptation",
    "au_compliance_standards",
}

# Fields containing lists of prose strings (check each item)
PROSE_LIST_FIELDS = {
    "goals",
    "execution_steps",
    "goals_achieved",
    "tips",
    "caregiver_prompts",
    "tags",
}


def extract_text_for_checking(yaml_content: str) -> str:
    """
    Extract prose text from YAML content, stripping parent_search_terms.

    Matches pipeline behavior: parent_search_terms is SEO content that
    legitimately uses phrases like "best books for..." which would
    false-positive on superlative checks.

    Args:
        yaml_content: Raw YAML file content

    Returns:
        Text blob suitable for AI detection checking
    """
    # Strip parent_search_terms section (matches _audit_ai_patterns behavior)
    text = re.sub(
        r"^parent_search_terms:.*",
        "",
        yaml_content,
        flags=re.MULTILINE | re.DOTALL,
    )
    return text


def find_canonical_yamls(base_path: str | None = None) -> list[Path]:
    """
    Find all canonical activity YAML files.

    Args:
        base_path: Override base path (for testing). Defaults to
                   knowledge/data/canonical/activities/

    Returns:
        Sorted list of YAML file paths
    """
    if base_path is None:
        # Default: knowledge repo relative to ATLAS project root
        base_path = str(
            project_root.parent / "knowledge" / "data" / "canonical" / "activities"
        )

    pattern = os.path.join(base_path, "**", "*.yaml")
    files = [Path(f) for f in glob.glob(pattern, recursive=True)]
    return sorted(files)


def audit_file(
    filepath: Path,
    categories: list[int] | None = None,
) -> dict:
    """
    Run AI detection checks on a single YAML file.

    Args:
        filepath: Path to YAML file
        categories: List of category numbers to check (None = all 13)

    Returns:
        Dict with keys: filepath, issues, passing, issue_count
    """
    content = filepath.read_text(encoding="utf-8")
    text = extract_text_for_checking(content)

    cats_to_check = categories or list(CATEGORY_CHECKERS.keys())
    all_issues = []

    for cat_num in cats_to_check:
        if cat_num not in CATEGORY_CHECKERS:
            continue
        name, checker = CATEGORY_CHECKERS[cat_num]
        issues = checker(text)
        for issue in issues:
            issue["category_num"] = cat_num
            issue["category_name"] = name
            issue["severity"] = get_severity(issue.get("code", ""))
        all_issues.extend(issues)

    return {
        "filepath": filepath,
        "issues": all_issues,
        "passing": len(all_issues) == 0,
        "issue_count": len(all_issues),
    }


def print_summary(results: list[dict], verbose: bool = False) -> None:
    """Print audit summary report."""
    total = len(results)
    passing = sum(1 for r in results if r["passing"])
    failing = total - passing

    print("\n" + "=" * 70)
    print("CANONICAL YAML REGRESSION AUDIT")
    print("=" * 70)
    print(f"\nFiles scanned: {total}")
    print(f"Passing:       {passing}")
    print(f"Failing:       {failing}")

    if failing == 0:
        print("\nAll files pass all AI detection categories.")
        return

    # Issues by category
    category_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for result in results:
        for issue in result["issues"]:
            cat = f"Cat {issue['category_num']}: {issue['category_name']}"
            category_counts[cat] = category_counts.get(cat, 0) + 1
            sev = issue.get("severity", "UNKNOWN")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

    print("\n--- Issues by Category ---")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")

    print("\n--- Issues by Severity ---")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
        if sev in severity_counts:
            print(f"  {sev}: {severity_counts[sev]}")

    # Per-file details
    print("\n--- Failing Files ---")
    for result in results:
        if result["passing"]:
            continue
        relpath = result["filepath"].name
        print(f"\n  {relpath} ({result['issue_count']} issues)")

        if verbose:
            for issue in result["issues"]:
                sev = issue.get("severity", "?")
                code = issue.get("code", "?")
                msg = issue.get("msg", "?")
                print(f"    [{sev}] {code}: {msg}")


def main() -> int:
    """Run the regression audit. Returns 0 if all pass, 1 if any fail."""
    parser = argparse.ArgumentParser(
        description="Regression audit for canonical Activity Atom YAMLs"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show each issue with details"
    )
    parser.add_argument(
        "--category",
        "-c",
        type=int,
        help="Test single category only (1-13)",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Override base path for YAML files",
    )
    args = parser.parse_args()

    categories = [args.category] if args.category else None

    if categories and categories[0] not in CATEGORY_CHECKERS:
        print(f"Error: Category {categories[0]} not found. Valid: 1-13")
        return 2

    yamls = find_canonical_yamls(args.path)
    if not yamls:
        print("No YAML files found.")
        return 2

    print(f"Found {len(yamls)} canonical YAML files.")
    if categories:
        cat_num = categories[0]
        name = CATEGORY_CHECKERS[cat_num][0]
        print(f"Checking category {cat_num} only: {name}")

    results = []
    for filepath in yamls:
        result = audit_file(filepath, categories)
        results.append(result)

    print_summary(results, verbose=args.verbose)

    any_failing = any(not r["passing"] for r in results)
    return 1 if any_failing else 0


if __name__ == "__main__":
    sys.exit(main())
