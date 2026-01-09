"""
Code Simplification Patterns
Based on Anthropic's code-simplifier agent.
"""

import re
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    INFO = "info"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Pattern:
    id: str
    severity: Severity
    name: str
    pattern: re.Pattern
    fix: str  # What to do instead


PATTERNS = [
    # Redundant code
    Pattern("REDUNDANT_TRUE", Severity.SUGGESTION, "if x == True -> if x",
            re.compile(r'\bif\s+\w+\s*==\s*True\s*:'), "if x:"),
    Pattern("REDUNDANT_FALSE", Severity.SUGGESTION, "if x == False -> if not x",
            re.compile(r'\bif\s+\w+\s*==\s*False\s*:'), "if not x:"),
    Pattern("REDUNDANT_NONE", Severity.WARNING, "== None -> is None",
            re.compile(r'\b\w+\s*==\s*None\b'), "x is None"),
    Pattern("REDUNDANT_TERNARY", Severity.SUGGESTION, "True if x else False -> bool(x)",
            re.compile(r'\bTrue\s+if\s+.+?\s+else\s+False\b'), "bool(x)"),
    Pattern("REDUNDANT_LEN", Severity.SUGGESTION, "len(x) > 0 -> if x",
            re.compile(r'\bif\s+len\(\w+\)\s*(?:>|!=)\s*0\s*:'), "if x:"),
    Pattern("REDUNDANT_LEN_ZERO", Severity.SUGGESTION, "len(x) == 0 -> if not x",
            re.compile(r'\bif\s+len\(\w+\)\s*==\s*0\s*:'), "if not x:"),

    # Python anti-patterns
    Pattern("BARE_EXCEPT", Severity.ERROR, "Bare except catches everything",
            re.compile(r'\bexcept\s*:\s*$', re.MULTILINE), "except Exception:"),
    Pattern("MUTABLE_DEFAULT", Severity.WARNING, "Mutable default argument",
            re.compile(r'def\s+\w+\([^)]*=\s*(\[\]|\{\})[^)]*\)'), "Use None, create inside"),
    Pattern("BROAD_EXCEPTION", Severity.WARNING, "Catching broad Exception",
            re.compile(r'\bexcept\s+Exception\s*(?:as\s+\w+)?:'), "Catch specific exceptions"),

    # Complexity
    Pattern("DEEP_NESTING", Severity.SUGGESTION, "Deep nesting - use guard clauses",
            re.compile(r'(\s{12,}if\s+)'), "Early return pattern"),

    # ATLAS standards (from CLAUDE.md)
    Pattern("SYNC_IO", Severity.WARNING, "Sync I/O - use async",
            re.compile(r'\bdef\s+\w+\([^)]*\).*?(?:open\(|requests\.|urllib)', re.DOTALL),
            "async def with aiofiles/httpx"),
]

PATTERNS_BY_ID = {p.id: p for p in PATTERNS}
