"""
ATLAS Code Simplifier

Analyzes Python code and suggests improvements while preserving functionality.
Designed as a learning tool for beginner coders.

Usage:
    # As a module
    from atlas.simplifier import CodeSimplifier

    simplifier = CodeSimplifier()
    result = simplifier.analyze_file("path/to/file.py")
    print(result.format_report())

    # CLI
    python -m atlas.simplifier.code_simplifier --file path/to/file.py
    python -m atlas.simplifier.code_simplifier --file path/to/file.py --verbose
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .patterns import (
    SIMPLIFICATION_PATTERNS,
    ATLAS_RULES,
    SimplificationPattern,
    PatternCategory,
    Severity,
    get_patterns_by_severity,
)

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """A single simplification suggestion."""
    pattern_id: str
    line_number: int
    line_content: str
    category: PatternCategory
    severity: Severity
    name: str
    description: str
    example_before: str
    example_after: str
    explanation: str

    def format_short(self) -> str:
        """Format as a short one-liner."""
        severity_icon = {
            Severity.INFO: "i",
            Severity.SUGGESTION: "*",
            Severity.WARNING: "!",
            Severity.ERROR: "X",
        }
        icon = severity_icon.get(self.severity, "?")
        return f"[{icon}] Line {self.line_number}: {self.name}"

    def format_verbose(self) -> str:
        """Format with full explanation."""
        lines = [
            f"[{self.severity.value.upper()}] {self.name}",
            f"  Line {self.line_number}: {self.line_content.strip()[:60]}",
            "",
            f"  Before: {self.example_before}",
            f"  After:  {self.example_after}",
            "",
            f"  Why: {self.explanation}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "pattern_id": self.pattern_id,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "category": self.category.value,
            "severity": self.severity.value,
            "name": self.name,
            "description": self.description,
            "example_before": self.example_before,
            "example_after": self.example_after,
            "explanation": self.explanation,
        }


@dataclass
class SimplificationResult:
    """Result of analyzing a file or code snippet."""
    file_path: Optional[str] = None
    total_lines: int = 0
    suggestions: list[Suggestion] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_suggestions(self) -> bool:
        return len(self.suggestions) > 0

    @property
    def suggestion_count(self) -> int:
        return len(self.suggestions)

    def suggestions_by_severity(self, severity: Severity) -> list[Suggestion]:
        """Get suggestions filtered by severity."""
        return [s for s in self.suggestions if s.severity == severity]

    def format_report(self, verbose: bool = False) -> str:
        """Format as a human-readable report."""
        if self.error:
            return f"Error: {self.error}"

        if not self.has_suggestions:
            lines = [
                "No suggestions found.",
                "",
                f"Analyzed {self.total_lines} lines.",
                "Your code looks good!",
            ]
            return "\n".join(lines)

        # Group by severity
        errors = self.suggestions_by_severity(Severity.ERROR)
        warnings = self.suggestions_by_severity(Severity.WARNING)
        suggestions = self.suggestions_by_severity(Severity.SUGGESTION)
        infos = self.suggestions_by_severity(Severity.INFO)

        lines = [
            f"Code Simplification Report",
            f"{'=' * 40}",
            f"File: {self.file_path or '(code snippet)'}",
            f"Lines analyzed: {self.total_lines}",
            f"Suggestions: {self.suggestion_count}",
            "",
        ]

        # Summary counts
        summary_parts = []
        if errors:
            summary_parts.append(f"{len(errors)} must-fix")
        if warnings:
            summary_parts.append(f"{len(warnings)} warnings")
        if suggestions:
            summary_parts.append(f"{len(suggestions)} suggestions")
        if infos:
            summary_parts.append(f"{len(infos)} info")

        if summary_parts:
            lines.append(f"Summary: {', '.join(summary_parts)}")
            lines.append("")

        # List suggestions
        if errors:
            lines.append("MUST FIX:")
            for s in errors:
                if verbose:
                    lines.append(s.format_verbose())
                    lines.append("")
                else:
                    lines.append(f"  {s.format_short()}")
            lines.append("")

        if warnings:
            lines.append("WARNINGS:")
            for s in warnings:
                if verbose:
                    lines.append(s.format_verbose())
                    lines.append("")
                else:
                    lines.append(f"  {s.format_short()}")
            lines.append("")

        if suggestions:
            lines.append("SUGGESTIONS:")
            for s in suggestions:
                if verbose:
                    lines.append(s.format_verbose())
                    lines.append("")
                else:
                    lines.append(f"  {s.format_short()}")
            lines.append("")

        if infos:
            lines.append("INFO:")
            for s in infos:
                if verbose:
                    lines.append(s.format_verbose())
                    lines.append("")
                else:
                    lines.append(f"  {s.format_short()}")
            lines.append("")

        # ATLAS rules reminder (if relevant patterns found)
        atlas_suggestions = [s for s in self.suggestions if s.category == PatternCategory.ATLAS_SPECIFIC]
        if atlas_suggestions:
            lines.extend([
                "ATLAS Coding Standards (from CLAUDE.md):",
                f"  - {ATLAS_RULES['async_await']}",
                f"  - {ATLAS_RULES['specific_exceptions']}",
                f"  - {ATLAS_RULES['logging']}",
                "",
            ])

        # Helpful tip
        if not verbose and self.has_suggestions:
            lines.append("Tip: Use --verbose for detailed explanations")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "file_path": self.file_path,
            "total_lines": self.total_lines,
            "suggestion_count": self.suggestion_count,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "error": self.error,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class CodeSimplifier:
    """
    Analyzes Python code and suggests simplifications.

    Uses pattern matching to detect common issues and provides
    educational explanations for each suggestion.
    """

    def __init__(
        self,
        min_severity: Severity = Severity.INFO,
        patterns: Optional[list[SimplificationPattern]] = None,
    ):
        """
        Initialize the code simplifier.

        Args:
            min_severity: Minimum severity level to report
            patterns: Custom patterns to use (defaults to all patterns)
        """
        self.min_severity = min_severity
        self.patterns = patterns or get_patterns_by_severity(min_severity)
        logger.debug(f"CodeSimplifier initialized with {len(self.patterns)} patterns")

    def analyze_code(self, code: str, file_path: Optional[str] = None) -> SimplificationResult:
        """
        Analyze a code string and return suggestions.

        Args:
            code: Python source code to analyze
            file_path: Optional file path for reporting

        Returns:
            SimplificationResult with all suggestions
        """
        result = SimplificationResult(
            file_path=file_path,
            total_lines=len(code.splitlines()),
        )

        lines = code.splitlines()

        for pattern in self.patterns:
            try:
                self._check_pattern(pattern, code, lines, result)
            except Exception as e:
                logger.warning(f"Error checking pattern {pattern.id}: {e}")

        # Sort suggestions by line number, then severity
        severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.SUGGESTION: 2, Severity.INFO: 3}
        result.suggestions.sort(key=lambda s: (s.line_number, severity_order.get(s.severity, 99)))

        return result

    def _check_pattern(
        self,
        pattern: SimplificationPattern,
        code: str,
        lines: list[str],
        result: SimplificationResult,
    ) -> None:
        """Check a single pattern against the code."""
        # Some patterns work on full code, others line-by-line
        if pattern.id in ("LONG_FUNCTION", "ATLAS_MISSING_LOGGING"):
            # These need full code analysis
            self._check_full_code_pattern(pattern, code, lines, result)
        else:
            # Check line by line
            self._check_line_pattern(pattern, code, lines, result)

    def _check_line_pattern(
        self,
        pattern: SimplificationPattern,
        code: str,
        lines: list[str],
        result: SimplificationResult,
    ) -> None:
        """Check a pattern that matches individual lines."""
        for i, line in enumerate(lines, start=1):
            match = pattern.pattern.search(line)
            if match:
                result.suggestions.append(Suggestion(
                    pattern_id=pattern.id,
                    line_number=i,
                    line_content=line,
                    category=pattern.category,
                    severity=pattern.severity,
                    name=pattern.name,
                    description=pattern.description,
                    example_before=pattern.example_before,
                    example_after=pattern.example_after,
                    explanation=pattern.explanation,
                ))

    def _check_full_code_pattern(
        self,
        pattern: SimplificationPattern,
        code: str,
        lines: list[str],
        result: SimplificationResult,
    ) -> None:
        """Check patterns that need full code context."""
        if pattern.id == "ATLAS_MISSING_LOGGING":
            # Check if logging is set up
            has_logging_import = "import logging" in code or "from logging" in code
            has_logger = "logger = " in code or "logger=" in code

            if not has_logging_import and not has_logger:
                result.suggestions.append(Suggestion(
                    pattern_id=pattern.id,
                    line_number=1,
                    line_content="(file-level)",
                    category=pattern.category,
                    severity=pattern.severity,
                    name=pattern.name,
                    description=pattern.description,
                    example_before=pattern.example_before,
                    example_after=pattern.example_after,
                    explanation=pattern.explanation,
                ))

        elif pattern.id == "LONG_FUNCTION":
            # Find functions longer than 50 lines
            self._check_long_functions(pattern, lines, result)

    def _check_long_functions(
        self,
        pattern: SimplificationPattern,
        lines: list[str],
        result: SimplificationResult,
        max_lines: int = 50,
    ) -> None:
        """Check for functions that are too long."""
        import re

        func_start = None
        func_name = None
        func_indent = 0

        for i, line in enumerate(lines, start=1):
            # Check for function definition
            match = re.match(r'^(\s*)(async\s+)?def\s+(\w+)\s*\(', line)
            if match:
                # Check if previous function was too long
                if func_start and (i - func_start) > max_lines:
                    result.suggestions.append(Suggestion(
                        pattern_id=pattern.id,
                        line_number=func_start,
                        line_content=f"def {func_name}(...)",
                        category=pattern.category,
                        severity=pattern.severity,
                        name=f"{pattern.name}: {func_name}() is {i - func_start} lines",
                        description=pattern.description,
                        example_before=pattern.example_before,
                        example_after=pattern.example_after,
                        explanation=pattern.explanation,
                    ))

                func_start = i
                func_name = match.group(3)
                func_indent = len(match.group(1))

    def analyze_file(self, file_path: str | Path) -> SimplificationResult:
        """
        Analyze a Python file and return suggestions.

        Args:
            file_path: Path to the Python file

        Returns:
            SimplificationResult with all suggestions
        """
        path = Path(file_path)

        if not path.exists():
            return SimplificationResult(
                file_path=str(path),
                error=f"File not found: {path}",
            )

        if not path.suffix == ".py":
            return SimplificationResult(
                file_path=str(path),
                error=f"Not a Python file: {path}",
            )

        try:
            code = path.read_text(encoding="utf-8")
        except Exception as e:
            return SimplificationResult(
                file_path=str(path),
                error=f"Error reading file: {e}",
            )

        return self.analyze_code(code, file_path=str(path))


def main():
    """CLI entry point for the code simplifier."""
    parser = argparse.ArgumentParser(
        description="Analyze Python code and suggest simplifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m atlas.simplifier.code_simplifier --file script.py
  python -m atlas.simplifier.code_simplifier --file script.py --verbose
  python -m atlas.simplifier.code_simplifier --file script.py --json
  echo "if x == True: pass" | python -m atlas.simplifier.code_simplifier --stdin
        """,
    )

    parser.add_argument(
        "--file", "-f",
        help="Python file to analyze",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read code from stdin (for hook mode)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed explanations for each suggestion",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (for hook integration)",
    )
    parser.add_argument(
        "--min-severity",
        choices=["info", "suggestion", "warning", "error"],
        default="info",
        help="Minimum severity level to report (default: info)",
    )

    args = parser.parse_args()

    # Determine severity
    severity_map = {
        "info": Severity.INFO,
        "suggestion": Severity.SUGGESTION,
        "warning": Severity.WARNING,
        "error": Severity.ERROR,
    }
    min_severity = severity_map[args.min_severity]

    # Create simplifier
    simplifier = CodeSimplifier(min_severity=min_severity)

    # Get code to analyze
    if args.stdin:
        code = sys.stdin.read()
        result = simplifier.analyze_code(code)
    elif args.file:
        result = simplifier.analyze_file(args.file)
    else:
        parser.print_help()
        sys.exit(1)

    # Output result
    if args.json:
        # JSON output for hook mode
        output = {
            "pass": not result.suggestions_by_severity(Severity.ERROR),
            "issues": [
                {"code": s.pattern_id, "msg": s.description}
                for s in result.suggestions
                if s.severity in (Severity.ERROR, Severity.WARNING)
            ],
            "warnings": [
                {"code": s.pattern_id, "msg": s.description}
                for s in result.suggestions
                if s.severity in (Severity.SUGGESTION, Severity.INFO)
            ],
            "details": result.to_dict(),
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(result.format_report(verbose=args.verbose))

    # Exit with appropriate code
    if result.error:
        sys.exit(1)
    if result.suggestions_by_severity(Severity.ERROR):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
