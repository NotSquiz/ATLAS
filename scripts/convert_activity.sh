#!/bin/bash
# Activity Conversion Script
# Usage: ./convert_activity.sh [options]

set -e

ACTIVITY_ID="${1:-}"
RETRIES="${2:-2}"

cd /home/squiz/ATLAS

# Suppress duplicate warnings at Python level
export PYTHONWARNINGS="ignore"

# Default: no args = find next available
if [ -z "$ACTIVITY_ID" ]; then
    echo ""
    echo "=========================================="
    echo "  ACTIVITY CONVERSION PIPELINE"
    echo "  Finding next available activity..."
    echo "=========================================="
    echo ""
    python3 -m atlas.pipelines.activity_conversion --next --retry "$RETRIES"

elif [ "$ACTIVITY_ID" == "--list" ]; then
    python3 -m atlas.pipelines.activity_conversion --list-pending

elif [ "$ACTIVITY_ID" == "--batch" ]; then
    LIMIT="${2:-3}"
    echo ""
    echo "=========================================="
    echo "  BATCH MODE: Converting up to $LIMIT activities"
    echo "=========================================="
    echo ""
    python3 -m atlas.pipelines.activity_conversion --batch --limit "$LIMIT"

elif [ "$ACTIVITY_ID" == "--help" ]; then
    echo "Activity Conversion Script"
    echo ""
    echo "Usage:"
    echo "  ./convert_activity.sh              Auto-convert next available"
    echo "  ./convert_activity.sh --list       List pending activities"
    echo "  ./convert_activity.sh --batch 5    Batch convert 5"
    echo "  ./convert_activity.sh <id>         Convert specific activity"
    echo "  ./convert_activity.sh <id> 3       Convert with 3 retries"

else
    echo ""
    echo "=========================================="
    echo "  Converting: $ACTIVITY_ID"
    echo "=========================================="
    echo ""
    python3 -m atlas.pipelines.activity_conversion --activity "$ACTIVITY_ID" --retry "$RETRIES"
fi
