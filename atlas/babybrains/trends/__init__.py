"""
Baby Brains Trend Detection Module

Thin wrapper around GrokClient with budget gates and brand safety.
"""

from atlas.babybrains.trends.engine import TrendService, TrendServiceResult

__all__ = ["TrendService", "TrendServiceResult"]
