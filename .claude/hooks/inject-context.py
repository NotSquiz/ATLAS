#!/usr/bin/env python3
"""Layer 1: Passive Context Injection (SessionStart hook).

Injects critical-state.md into every session so agents can't skip it.
Fires on session begin, resume, AND after compaction — critical state
survives context loss.

Outputs structured JSON with additionalContext (plain stdout is ignored
in normal mode).
"""
import json
import sys
from pathlib import Path

try:
    critical_state_path = Path(__file__).parent.parent / "critical-state.md"
    if not critical_state_path.exists():
        sys.exit(0)  # No critical state file = nothing to inject

    content = critical_state_path.read_text()
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": content
        }
    }
    print(json.dumps(output))
    sys.exit(0)
except Exception as e:
    # Fail open — never block session start
    print(f"Context injection error: {e}", file=sys.stderr)
    sys.exit(0)
