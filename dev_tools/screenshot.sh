#!/bin/bash
# screenshot.sh - Capture Windows screenshot from WSL2 and return WSL path
#
# Usage (from WSL2):
#   ./dev_tools/screenshot.sh
#
# Returns:
#   WSL path to captured screenshot (e.g., /mnt/c/Users/.../atlas_20260123_...png)

set -e

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PowerShell script should be alongside this script
PS_SCRIPT="$SCRIPT_DIR/capture_screen.ps1"

# Check if PowerShell script exists (in WSL path)
if [[ ! -f "$PS_SCRIPT" ]]; then
    echo "ERROR: capture_screen.ps1 not found at $PS_SCRIPT" >&2
    exit 1
fi

# Convert WSL path to Windows path for PowerShell
WIN_SCRIPT_PATH=$(wslpath -w "$PS_SCRIPT")

# Capture screenshot via PowerShell
screenshot_path=$(powershell.exe -ExecutionPolicy Bypass -File "$WIN_SCRIPT_PATH" 2>/dev/null | tr -d '\r\n')

if [[ -z "$screenshot_path" ]]; then
    echo "ERROR: Screenshot capture failed - no output from PowerShell" >&2
    exit 1
fi

# Convert Windows path to WSL path
# C:\Users\foo\bar -> /mnt/c/Users/foo/bar
wsl_path=$(echo "$screenshot_path" | sed 's/\\/\//g' | sed 's/^\([A-Za-z]\):/\/mnt\/\L\1/')

# Verify file exists
if [[ ! -f "$wsl_path" ]]; then
    echo "ERROR: Screenshot file not found at $wsl_path" >&2
    echo "       Windows path was: $screenshot_path" >&2
    exit 1
fi

echo "$wsl_path"
