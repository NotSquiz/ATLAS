"""
ATLAS Orchestrator Module

Supreme orchestrator for the Baby Brains ecosystem.
Provides slash command routing, skill execution, and hook framework.

Architecture:
    atlas/llm/router.py         -> LLM tier routing (LOCAL/HAIKU/AGENT_SDK)
    atlas/orchestrator/         -> Slash command orchestration (this module)

Components:
    command_router.py   - Parse and route slash commands
    skill_loader.py     - Load skill markdown + contexts
    skill_executor.py   - Execute skills via Claude Agent SDK
    hooks.py            - Wrap existing validators as hooks

Slash Commands:
    /babybrains - Content pipeline orchestrator (9 skills)
    /knowledge  - Knowledge graph orchestrator (6 atoms, 5 validators)
    /web        - Development orchestrator (7 agents)
    /app        - Decision log orchestrator
    /workout    - Health orchestrator (FUTURE)

Usage:
    from atlas.orchestrator import CommandRouter, execute_command

    # Or run directly:
    python -m atlas.orchestrator.command_router babybrains status
"""


def __getattr__(name: str):
    """Lazy import to avoid circular import issues when running as __main__."""
    if name in ("CommandRouter", "SlashCommand", "CommandResult", "execute_command"):
        from . import command_router
        return getattr(command_router, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CommandRouter",
    "SlashCommand",
    "CommandResult",
    "execute_command",
]
