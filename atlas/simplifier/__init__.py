"""
ATLAS Code Simplifier Module

On-demand code simplification tool that analyzes code and suggests improvements
while preserving exact functionality. Helps learn Python best practices.

Usage:
    /simplify [file_path]           - Analyze file and suggest improvements
    /simplify --verbose [file_path] - Show detailed explanations

    # CLI mode
    python -m atlas.simplifier.code_simplifier --file path/to/file.py
"""

from .code_simplifier import CodeSimplifier, SimplificationResult
from .patterns import SIMPLIFICATION_PATTERNS, ATLAS_RULES

__all__ = [
    "CodeSimplifier",
    "SimplificationResult",
    "SIMPLIFICATION_PATTERNS",
    "ATLAS_RULES",
]
