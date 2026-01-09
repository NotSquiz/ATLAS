"""
ATLAS Code Simplifier
Based on Anthropic's code-simplifier agent.

Usage:
    /simplify <file>
    python -m atlas.simplifier.code_simplifier --file path/to/file.py
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .patterns import PATTERNS, Pattern, Severity

logger = logging.getLogger(__name__)


@dataclass
class Issue:
    pattern_id: str
    line: int
    name: str
    fix: str
    severity: Severity

    def __str__(self) -> str:
        icon = {"error": "X", "warning": "!", "suggestion": "*", "info": "i"}
        return f"[{icon.get(self.severity.value, '?')}] L{self.line}: {self.name} -> {self.fix}"


@dataclass
class SimplificationResult:
    file_path: Optional[str] = None
    lines: int = 0
    issues: list[Issue] = field(default_factory=list)
    error: Optional[str] = None

    def by_severity(self, severity: Severity) -> list[Issue]:
        return [i for i in self.issues if i.severity == severity]

    def format(self) -> str:
        if self.error:
            return f"Error: {self.error}"
        if not self.issues:
            return f"Clean: {self.file_path or 'code'} ({self.lines} lines)"

        lines = [f"{self.file_path or 'code'}: {len(self.issues)} issues"]
        for sev in [Severity.ERROR, Severity.WARNING, Severity.SUGGESTION, Severity.INFO]:
            for issue in self.by_severity(sev):
                lines.append(f"  {issue}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "file": self.file_path,
            "lines": self.lines,
            "issues": [{"id": i.pattern_id, "line": i.line, "name": i.name, "fix": i.fix, "severity": i.severity.value} for i in self.issues],
            "error": self.error,
        }


class CodeSimplifier:
    def __init__(self, patterns: Optional[list[Pattern]] = None):
        self.patterns = patterns or PATTERNS

    def analyze(self, code: str, file_path: Optional[str] = None) -> SimplificationResult:
        lines = code.splitlines()
        result = SimplificationResult(file_path=file_path, lines=len(lines))

        for pattern in self.patterns:
            for i, line in enumerate(lines, 1):
                if pattern.pattern.search(line):
                    result.issues.append(Issue(
                        pattern_id=pattern.id,
                        line=i,
                        name=pattern.name,
                        fix=pattern.fix,
                        severity=pattern.severity,
                    ))

        result.issues.sort(key=lambda x: (x.line, x.severity.value))
        return result

    def analyze_file(self, path: str | Path) -> SimplificationResult:
        path = Path(path)
        if not path.exists():
            return SimplificationResult(file_path=str(path), error=f"Not found: {path}")
        if path.suffix != ".py":
            return SimplificationResult(file_path=str(path), error=f"Not a .py file: {path}")
        try:
            return self.analyze(path.read_text(), str(path))
        except Exception as e:
            return SimplificationResult(file_path=str(path), error=str(e))


def main():
    parser = argparse.ArgumentParser(description="Code simplifier")
    parser.add_argument("--file", "-f", help="File to analyze")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        sys.exit(1)

    result = CodeSimplifier().analyze_file(args.file)
    print(json.dumps(result.to_dict(), indent=2) if args.json else result.format())
    sys.exit(1 if result.by_severity(Severity.ERROR) else 0)


if __name__ == "__main__":
    main()
