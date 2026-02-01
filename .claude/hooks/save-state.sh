#!/usr/bin/env bash
# Layer 5: PreCompact State Save
#
# Persist critical state before context compaction so it can be
# re-injected by Layer 1 (inject-context.py on SessionStart).
#
# PreCompact cannot block compaction, but can write files that
# SessionStart will re-inject.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CRITICAL_STATE="$REPO_ROOT/.claude/critical-state.md"
REGISTRY="$REPO_ROOT/config/canonical_values.json"

# Ensure critical-state.md exists and is current
if [ ! -f "$CRITICAL_STATE" ]; then
    echo "WARNING: critical-state.md not found" >&2
    exit 0
fi

# Validate canonical_values.json is valid JSON
if [ -f "$REGISTRY" ]; then
    python3 -c "import json; json.load(open('$REGISTRY'))" 2>/dev/null || {
        echo "WARNING: canonical_values.json is invalid JSON" >&2
        exit 0
    }
fi

# Add timestamp to critical-state.md if it doesn't have one from this session
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
if ! grep -q "Last verified:" "$CRITICAL_STATE" 2>/dev/null; then
    echo "" >> "$CRITICAL_STATE"
    echo "<!-- Last verified: $TIMESTAMP -->" >> "$CRITICAL_STATE"
else
    sed -i "s/<!-- Last verified: .* -->/<!-- Last verified: $TIMESTAMP -->/" "$CRITICAL_STATE"
fi

exit 0
