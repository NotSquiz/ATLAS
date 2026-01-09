"""
Code Simplification Patterns

Defines patterns for detecting code that can be simplified, along with
explanations to help users learn best practices.

Based on:
- Python best practices
- ATLAS CLAUDE.md coding standards
- Anthropic code-simplifier pattern
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PatternCategory(Enum):
    """Categories of simplification patterns."""
    REDUNDANT = "redundant_code"
    COMPLEXITY = "complexity_reduction"
    NAMING = "naming_clarity"
    DEAD_CODE = "dead_code"
    CONSISTENCY = "consistency"
    ATLAS_SPECIFIC = "atlas_specific"


class Severity(Enum):
    """Severity of suggestions."""
    INFO = "info"           # Nice to know
    SUGGESTION = "suggestion"  # Recommended improvement
    WARNING = "warning"      # Should fix
    ERROR = "error"          # Must fix (e.g., bare except)


@dataclass
class SimplificationPattern:
    """A pattern that detects simplifiable code."""
    id: str
    category: PatternCategory
    severity: Severity
    name: str
    description: str
    pattern: re.Pattern  # Regex to detect the issue
    example_before: str
    example_after: str
    explanation: str  # Educational explanation for beginner coders
    auto_fix: Optional[str] = None  # Regex replacement if auto-fixable


# Python Best Practice Patterns
PYTHON_PATTERNS = [
    SimplificationPattern(
        id="REDUNDANT_TRUE_COMPARISON",
        category=PatternCategory.REDUNDANT,
        severity=Severity.SUGGESTION,
        name="Redundant True comparison",
        description="Comparing explicitly to True is redundant",
        pattern=re.compile(r'\bif\s+(\w+)\s*==\s*True\s*:'),
        example_before="if x == True:",
        example_after="if x:",
        explanation=(
            "In Python, 'if x:' already checks if x is truthy. "
            "Comparing to True is redundant and less Pythonic. "
            "The explicit comparison also fails for truthy values like 1 or 'yes'."
        ),
    ),
    SimplificationPattern(
        id="REDUNDANT_FALSE_COMPARISON",
        category=PatternCategory.REDUNDANT,
        severity=Severity.SUGGESTION,
        name="Redundant False comparison",
        description="Comparing explicitly to False is redundant",
        pattern=re.compile(r'\bif\s+(\w+)\s*==\s*False\s*:'),
        example_before="if x == False:",
        example_after="if not x:",
        explanation=(
            "In Python, 'if not x:' checks if x is falsy. "
            "Comparing to False is redundant. "
            "Using 'not x' is more Pythonic and handles None, 0, '', etc."
        ),
    ),
    SimplificationPattern(
        id="REDUNDANT_NONE_COMPARISON",
        category=PatternCategory.REDUNDANT,
        severity=Severity.WARNING,
        name="Use 'is None' instead of '== None'",
        description="None comparisons should use 'is' not '=='",
        pattern=re.compile(r'\b(\w+)\s*==\s*None\b'),
        example_before="if x == None:",
        example_after="if x is None:",
        explanation=(
            "None is a singleton in Python, so use 'is None' for identity comparison. "
            "Using '==' can give unexpected results if a class overrides __eq__. "
            "PEP 8 recommends: 'Comparisons to singletons like None should use is'."
        ),
    ),
    SimplificationPattern(
        id="REDUNDANT_TERNARY_BOOL",
        category=PatternCategory.REDUNDANT,
        severity=Severity.SUGGESTION,
        name="Redundant ternary for boolean",
        description="Ternary returning True/False can be simplified",
        pattern=re.compile(r'\bTrue\s+if\s+(.+?)\s+else\s+False\b'),
        example_before="return True if condition else False",
        example_after="return bool(condition)  # or just: return condition",
        explanation=(
            "If you're returning True when a condition is true and False otherwise, "
            "you can just return the condition directly. "
            "Use bool() if you need to ensure a boolean type."
        ),
    ),
    SimplificationPattern(
        id="REDUNDANT_TERNARY_BOOL_REVERSED",
        category=PatternCategory.REDUNDANT,
        severity=Severity.SUGGESTION,
        name="Redundant ternary for boolean (reversed)",
        description="Ternary returning False/True can be simplified",
        pattern=re.compile(r'\bFalse\s+if\s+(.+?)\s+else\s+True\b'),
        example_before="return False if condition else True",
        example_after="return not condition",
        explanation=(
            "Returning False when true and True when false is just 'not condition'. "
            "This is more readable and idiomatic Python."
        ),
    ),
    SimplificationPattern(
        id="REDUNDANT_LEN_CHECK",
        category=PatternCategory.REDUNDANT,
        severity=Severity.SUGGESTION,
        name="Redundant len() check",
        description="Empty sequence check can be simplified",
        pattern=re.compile(r'\bif\s+len\((\w+)\)\s*(>|!=)\s*0\s*:'),
        example_before="if len(my_list) > 0:",
        example_after="if my_list:",
        explanation=(
            "In Python, empty sequences ([], '', {}) are falsy. "
            "Instead of checking len() > 0, just use 'if my_list:'. "
            "This is more Pythonic and slightly faster."
        ),
    ),
    SimplificationPattern(
        id="REDUNDANT_LEN_ZERO_CHECK",
        category=PatternCategory.REDUNDANT,
        severity=Severity.SUGGESTION,
        name="Redundant len() == 0 check",
        description="Empty sequence check can be simplified",
        pattern=re.compile(r'\bif\s+len\((\w+)\)\s*==\s*0\s*:'),
        example_before="if len(my_list) == 0:",
        example_after="if not my_list:",
        explanation=(
            "In Python, empty sequences are falsy. "
            "Instead of checking len() == 0, use 'if not my_list:'. "
            "This is the Pythonic idiom for checking emptiness."
        ),
    ),
    SimplificationPattern(
        id="BARE_EXCEPT",
        category=PatternCategory.CONSISTENCY,
        severity=Severity.ERROR,
        name="Bare except clause",
        description="Bare except catches all exceptions including KeyboardInterrupt",
        pattern=re.compile(r'\bexcept\s*:\s*$', re.MULTILINE),
        example_before="except:",
        example_after="except Exception:",
        explanation=(
            "A bare 'except:' catches ALL exceptions, including KeyboardInterrupt "
            "and SystemExit, which you usually don't want to catch. "
            "Use 'except Exception:' to catch normal errors, or better yet, "
            "catch specific exceptions like 'except ValueError:'. "
            "ATLAS rule: 'Specific exceptions before catch-all'."
        ),
    ),
    SimplificationPattern(
        id="UNNECESSARY_PASS",
        category=PatternCategory.DEAD_CODE,
        severity=Severity.INFO,
        name="Unnecessary pass statement",
        description="Pass statement after other code in block",
        pattern=re.compile(r'(\n\s+\w[^\n]+\n\s+pass\s*$)', re.MULTILINE),
        example_before="def foo():\n    x = 1\n    pass",
        example_after="def foo():\n    x = 1",
        explanation=(
            "'pass' is only needed for empty blocks. "
            "If there's other code in the block, the pass does nothing."
        ),
    ),
    SimplificationPattern(
        id="DOUBLE_NEGATION",
        category=PatternCategory.REDUNDANT,
        severity=Severity.SUGGESTION,
        name="Double negation",
        description="Double negation can be simplified",
        pattern=re.compile(r'\bnot\s+not\s+'),
        example_before="if not not condition:",
        example_after="if bool(condition):  # or just: if condition:",
        explanation=(
            "Double negation ('not not x') cancels out. "
            "If you need to convert to bool, use bool(x) for clarity. "
            "Usually you can just use the value directly."
        ),
    ),
    SimplificationPattern(
        id="MUTABLE_DEFAULT_ARG",
        category=PatternCategory.CONSISTENCY,
        severity=Severity.WARNING,
        name="Mutable default argument",
        description="Using mutable default argument (list/dict) is dangerous",
        pattern=re.compile(r'def\s+\w+\([^)]*=\s*(\[\]|\{\})[^)]*\)'),
        example_before="def foo(items=[]):",
        example_after="def foo(items=None):\n    if items is None:\n        items = []",
        explanation=(
            "Mutable default arguments (like [] or {}) are shared between calls! "
            "This is a common Python gotcha. If you append to the default list, "
            "that change persists across calls. Use None as the default and "
            "create a new list inside the function."
        ),
    ),
]

# ATLAS-Specific Patterns (from CLAUDE.md)
ATLAS_PATTERNS = [
    SimplificationPattern(
        id="ATLAS_SYNC_IO",
        category=PatternCategory.ATLAS_SPECIFIC,
        severity=Severity.WARNING,
        name="Synchronous I/O in async context",
        description="Consider using async/await for I/O operations",
        pattern=re.compile(r'\bdef\s+\w+\([^)]*\).*?(?:open\(|requests\.|urllib)', re.DOTALL),
        example_before="def read_file(path):\n    return open(path).read()",
        example_after="async def read_file(path):\n    async with aiofiles.open(path) as f:\n        return await f.read()",
        explanation=(
            "ATLAS rule: 'Use async/await for all I/O'. "
            "Blocking I/O can cause latency issues in async code. "
            "Use aiofiles for file I/O and aiohttp/httpx for HTTP."
        ),
    ),
    SimplificationPattern(
        id="ATLAS_MISSING_LOGGING",
        category=PatternCategory.ATLAS_SPECIFIC,
        severity=Severity.INFO,
        name="Consider adding logging",
        description="Module may benefit from logging setup",
        pattern=re.compile(r'^(?!.*import\s+logging)(?!.*logger\s*=)', re.MULTILINE),
        example_before="# No logging import",
        example_after="import logging\nlogger = logging.getLogger(__name__)",
        explanation=(
            "ATLAS rule: 'Always add logging to new modules'. "
            "Logging helps debug issues in production without adding print statements. "
            "Use logger.debug() for verbose info, logger.info() for important events, "
            "logger.error() for errors."
        ),
    ),
    SimplificationPattern(
        id="ATLAS_BROAD_EXCEPTION",
        category=PatternCategory.ATLAS_SPECIFIC,
        severity=Severity.WARNING,
        name="Catching broad Exception",
        description="Consider catching specific exceptions",
        pattern=re.compile(r'\bexcept\s+Exception\s*(?:as\s+\w+)?:'),
        example_before="except Exception as e:",
        example_after="except (ValueError, KeyError) as e:",
        explanation=(
            "ATLAS rule: 'Specific exceptions before catch-all'. "
            "Catching Exception is better than bare except, but consider "
            "which specific exceptions you expect and handle those. "
            "This makes debugging easier and prevents swallowing unexpected errors."
        ),
    ),
]

# Complexity Patterns
COMPLEXITY_PATTERNS = [
    SimplificationPattern(
        id="NESTED_IF_DEPTH",
        category=PatternCategory.COMPLEXITY,
        severity=Severity.SUGGESTION,
        name="Deep nesting detected",
        description="Consider using guard clauses or early returns",
        pattern=re.compile(r'(\s{12,}if\s+)'),  # 3+ levels of 4-space indent
        example_before=(
            "def process(x):\n"
            "    if x:\n"
            "        if x.valid:\n"
            "            if x.ready:\n"
            "                return x.value"
        ),
        example_after=(
            "def process(x):\n"
            "    if not x:\n"
            "        return None\n"
            "    if not x.valid:\n"
            "        return None\n"
            "    if not x.ready:\n"
            "        return None\n"
            "    return x.value"
        ),
        explanation=(
            "Deep nesting makes code hard to read. Use 'guard clauses' - "
            "check for invalid conditions early and return/raise immediately. "
            "This 'flattens' your code and makes the main logic clearer."
        ),
    ),
    SimplificationPattern(
        id="LONG_FUNCTION",
        category=PatternCategory.COMPLEXITY,
        severity=Severity.INFO,
        name="Long function detected",
        description="Consider breaking into smaller functions",
        pattern=re.compile(r'def\s+\w+\([^)]*\):(?:[^\n]*\n){50,}', re.MULTILINE),
        example_before="# Function with 50+ lines",
        example_after="# Break into smaller, focused functions",
        explanation=(
            "Functions longer than ~30-50 lines are often doing too much. "
            "Consider extracting logical sections into helper functions. "
            "Each function should do one thing well. "
            "This improves testability and reusability."
        ),
    ),
]

# Dead Code Patterns
DEAD_CODE_PATTERNS = [
    SimplificationPattern(
        id="UNUSED_IMPORT",
        category=PatternCategory.DEAD_CODE,
        severity=Severity.INFO,
        name="Potentially unused import",
        description="Import may not be used in the file",
        pattern=re.compile(r'^import\s+(\w+)\s*$', re.MULTILINE),
        example_before="import os  # but os is never used",
        example_after="# Remove unused import",
        explanation=(
            "Unused imports clutter the file and can slow down startup. "
            "Remove imports that aren't used. Your IDE can usually detect these. "
            "Note: some imports have side effects, so verify before removing."
        ),
    ),
    SimplificationPattern(
        id="COMMENTED_CODE",
        category=PatternCategory.DEAD_CODE,
        severity=Severity.INFO,
        name="Commented-out code detected",
        description="Consider removing commented-out code",
        pattern=re.compile(r'^\s*#\s*(def |class |if |for |while |return |import )', re.MULTILINE),
        example_before="# def old_function():\n#     pass",
        example_after="# Remove - use git history if needed",
        explanation=(
            "Commented-out code clutters the file. If you need to reference old code, "
            "use git history. Keeping dead code 'just in case' makes the codebase "
            "harder to understand."
        ),
    ),
]

# Combine all patterns
SIMPLIFICATION_PATTERNS: list[SimplificationPattern] = (
    PYTHON_PATTERNS +
    ATLAS_PATTERNS +
    COMPLEXITY_PATTERNS +
    DEAD_CODE_PATTERNS
)

# Quick lookup by ID
PATTERNS_BY_ID = {p.id: p for p in SIMPLIFICATION_PATTERNS}

# ATLAS-specific rules summary (for display)
ATLAS_RULES = {
    "async_await": "Use async/await for all I/O operations",
    "specific_exceptions": "Catch specific exceptions before catch-all (except Exception)",
    "logging": "Always add logging to new modules",
    "no_over_engineering": "Keep solutions simple and focused",
}


def get_patterns_by_category(category: PatternCategory) -> list[SimplificationPattern]:
    """Get all patterns in a category."""
    return [p for p in SIMPLIFICATION_PATTERNS if p.category == category]


def get_patterns_by_severity(min_severity: Severity) -> list[SimplificationPattern]:
    """Get patterns at or above a severity level."""
    severity_order = [Severity.INFO, Severity.SUGGESTION, Severity.WARNING, Severity.ERROR]
    min_index = severity_order.index(min_severity)
    return [p for p in SIMPLIFICATION_PATTERNS if severity_order.index(p.severity) >= min_index]
