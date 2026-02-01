#!/usr/bin/env python3
"""Layer 3: Stop-Time Propagation Check (Stop hook — command).

Before the agent finishes, verify all canonical values are consistent
across files. BLOCKS if inconsistencies found.

Critical implementation details:
1. stop_hook_active guard: prevents infinite loop where agent can never stop
2. Exit 0 + JSON decision:block: gives Claude structured feedback
3. Crash protection: wrap in try/except, never exit 1
4. Scoped grep patterns: context-aware, not bare numbers
"""
import json
import re
import sys
from pathlib import Path

try:
    input_data = json.loads(sys.stdin.read())

    # CRITICAL: prevent infinite loop — if stop_hook_active, allow immediately
    if input_data.get("stop_hook_active", False):
        sys.exit(0)

    # Load canonical values registry
    repo_root = Path(__file__).parent.parent.parent
    registry_path = repo_root / "config" / "canonical_values.json"
    if not registry_path.exists():
        sys.exit(0)  # No registry = nothing to check

    registry = json.loads(registry_path.read_text())

    issues = []
    for name, entry in registry["values"].items():
        old_patterns = entry.get("old_incorrect", [])
        references = entry.get("references", [])
        canonical = entry.get("canonical", "")

        # Check source of truth file too
        all_files = references + [entry.get("source_of_truth", "")]

        for ref_file in all_files:
            if not ref_file:
                continue
            full_path = repo_root / ref_file
            if not full_path.exists():
                continue

            content = full_path.read_text()
            for old_val in old_patterns:
                try:
                    if re.search(old_val, content):
                        issues.append(
                            f"  - {ref_file}: found pattern '{old_val}' "
                            f"(should be '{canonical}')"
                        )
                except re.error:
                    # Invalid regex pattern — skip
                    continue

    if issues:
        reason = (
            "PROPAGATION CHECK FAILED. Fix these before finishing:\n"
            + "\n".join(issues)
        )
        output = {"decision": "block", "reason": reason}
        print(json.dumps(output))
        sys.exit(0)

    # All consistent — allow stop
    sys.exit(0)

except Exception as e:
    # Fail open with warning — NEVER exit 1 (silently passes in hooks)
    print(f"Propagation check error: {e}", file=sys.stderr)
    sys.exit(0)
