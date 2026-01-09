"""
ATLAS Code Simplifier - Pattern-based code quality checks.
Based on Anthropic's code-simplifier agent.
"""

from .code_simplifier import CodeSimplifier, SimplificationResult
from .patterns import PATTERNS, Severity

__all__ = ["CodeSimplifier", "SimplificationResult", "PATTERNS", "Severity"]
