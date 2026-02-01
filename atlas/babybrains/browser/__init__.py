"""
Baby Brains Browser Automation

Stealth browser automation for YouTube warming using Patchright.
Requires optional [browser] dependencies: pip install -e ".[browser]"
"""

from atlas.babybrains.browser.warming_browser import (
    SessionConfig,
    SessionResult,
    WarmingBrowser,
    WatchResult,
)

__all__ = [
    "SessionConfig",
    "SessionResult",
    "WarmingBrowser",
    "WatchResult",
]
