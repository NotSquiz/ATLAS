#!/usr/bin/env python3
"""Layer 2: Real-Time Propagation Warning (PostToolUse hook).

When a source-of-truth file is edited, immediately warn about other files
that reference the same value. Advisory only — does NOT block.

Reads stdin JSON from hook system, checks if edited file is a source of
truth in canonical_values.json, warns about references.
"""
import json
import sys
from pathlib import Path

try:
    input_data = json.loads(sys.stdin.read())

    # Extract the file path from the tool input
    tool_input = input_data.get("toolInput", {})
    edited_file = tool_input.get("file_path", "")
    if not edited_file:
        sys.exit(0)

    # Load canonical values registry
    repo_root = Path(__file__).parent.parent.parent
    registry_path = repo_root / "config" / "canonical_values.json"
    if not registry_path.exists():
        sys.exit(0)

    registry = json.loads(registry_path.read_text())

    # Normalize the edited file path to be relative to repo root
    try:
        edited_relative = str(Path(edited_file).resolve().relative_to(repo_root.resolve()))
    except ValueError:
        sys.exit(0)  # File is outside repo — not our concern

    # Check if edited file is a source of truth
    warnings = []
    for name, entry in registry["values"].items():
        source = entry.get("source_of_truth", "")
        if edited_relative == source or edited_file.endswith(source):
            refs = entry.get("references", [])
            if refs:
                ref_list = ", ".join(refs)
                warnings.append(
                    f"You modified '{source}' which is source of truth for "
                    f"'{name}' (canonical: {entry['canonical']}). "
                    f"These files also reference it: {ref_list}. Update them too."
                )

    if warnings:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "WARNING: " + " | ".join(warnings)
            }
        }
        print(json.dumps(output))

    sys.exit(0)

except Exception as e:
    # Fail open — never block edits
    print(f"Edit propagation check error: {e}", file=sys.stderr)
    sys.exit(0)
