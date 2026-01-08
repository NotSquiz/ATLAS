"""LLM subsystem with local, cloud API, and Agent SDK backends."""

from .local import OllamaClient
from .cloud import ClaudeAgentClient, get_claude_client
from .api import AnthropicClient, get_haiku_client
from .router import ATLASRouter, get_router, Tier, RoutingDecision, RouterConfig
from .cost_tracker import CostTracker, get_cost_tracker, BudgetStatus

__all__ = [
    # Clients
    "OllamaClient",
    "ClaudeAgentClient",
    "get_claude_client",
    "AnthropicClient",
    "get_haiku_client",
    # Router
    "ATLASRouter",
    "get_router",
    "Tier",
    "RoutingDecision",
    "RouterConfig",
    # Cost tracking
    "CostTracker",
    "get_cost_tracker",
    "BudgetStatus",
]
