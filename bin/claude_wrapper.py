#!/usr/bin/env python3
"""
Claude CLI Wrapper for ATLAS

Uses Claude Code CLI with Max subscription authentication.
DO NOT set ANTHROPIC_API_KEY env variable - this bypasses subscription billing.

Authentication: Run `claude login` once to authenticate with Max subscription.

Usage:
    from claude_wrapper import ClaudeWrapper

    claude = ClaudeWrapper()
    response = claude.query("What is 2+2?")
    print(response)
"""

import subprocess
import json
import shutil
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class Model(Enum):
    """Available Claude models."""
    SONNET = "sonnet"
    OPUS = "opus"
    HAIKU = "haiku"


@dataclass
class ClaudeResponse:
    """Structured response from Claude CLI."""
    result: str
    session_id: Optional[str] = None
    cost_usd: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None

    @property
    def text(self) -> str:
        """Alias for result."""
        return self.result


class ClaudeError(Exception):
    """Error from Claude CLI."""
    pass


class ClaudeWrapper:
    """
    Wraps Claude Code CLI for programmatic access via Max subscription.

    Uses -p (print mode) and --output-format json for machine-readable output.
    """

    def __init__(
        self,
        model: Model = Model.SONNET,
        max_budget_usd: Optional[float] = None,
        system_prompt: Optional[str] = None,
        mcp_config: Optional[str] = None,
    ):
        """
        Initialize Claude wrapper.

        Args:
            model: Default model to use (sonnet, opus, haiku)
            max_budget_usd: Maximum cost per request (optional)
            system_prompt: Default system prompt (optional)
            mcp_config: Path to MCP config JSON file (optional)
        """
        self.model = model
        self.max_budget_usd = max_budget_usd
        self.system_prompt = system_prompt
        self.mcp_config = mcp_config

        # Verify CLI is available
        self._verify_cli()

    def _verify_cli(self) -> None:
        """Verify claude CLI is installed and accessible."""
        if not shutil.which("claude"):
            raise ClaudeError(
                "claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code\n"
                "Then authenticate with: claude login"
            )

    def _build_command(
        self,
        prompt: str,
        model: Optional[Model] = None,
        system_prompt: Optional[str] = None,
        json_schema: Optional[str] = None,
        allowed_tools: Optional[list[str]] = None,
        max_budget_usd: Optional[float] = None,
        session_id: Optional[str] = None,
        continue_session: bool = False,
    ) -> list[str]:
        """Build the CLI command with all flags."""
        cmd = ["claude", "-p", prompt, "--output-format", "json"]

        # Model selection
        model = model or self.model
        cmd.extend(["--model", model.value])

        # System prompt
        sys_prompt = system_prompt or self.system_prompt
        if sys_prompt:
            cmd.extend(["--system-prompt", sys_prompt])

        # JSON schema for structured output
        if json_schema:
            cmd.extend(["--json-schema", json_schema])

        # Allowed tools
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        # Budget cap
        budget = max_budget_usd or self.max_budget_usd
        if budget:
            cmd.extend(["--max-budget-usd", str(budget)])

        # Session management
        if continue_session:
            cmd.append("--continue")
        elif session_id:
            cmd.extend(["--resume", session_id])

        # MCP config
        if self.mcp_config:
            cmd.extend(["--mcp-config", self.mcp_config])

        return cmd

    def query(
        self,
        prompt: str,
        model: Optional[Model] = None,
        system_prompt: Optional[str] = None,
        json_schema: Optional[str] = None,
        allowed_tools: Optional[list[str]] = None,
        max_budget_usd: Optional[float] = None,
        timeout: int = 120,
        session_id: Optional[str] = None,
        continue_session: bool = False,
    ) -> ClaudeResponse:
        """
        Send a query to Claude via CLI.

        Args:
            prompt: The prompt to send
            model: Override default model
            system_prompt: Override default system prompt
            json_schema: JSON schema for structured output validation
            allowed_tools: List of tools to allow (e.g., ["Read", "Edit", "Bash"])
            max_budget_usd: Override default budget cap
            timeout: Timeout in seconds (default 120)
            session_id: Resume a specific session by ID
            continue_session: Continue the most recent conversation

        Returns:
            ClaudeResponse with result text and metadata

        Raises:
            ClaudeError: If CLI returns an error
        """
        cmd = self._build_command(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            json_schema=json_schema,
            allowed_tools=allowed_tools,
            max_budget_usd=max_budget_usd,
            session_id=session_id,
            continue_session=continue_session,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise ClaudeError(f"Request timed out after {timeout} seconds")

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            raise ClaudeError(f"Claude CLI error (code {result.returncode}): {error_msg}")

        # Parse JSON response
        try:
            data = json.loads(result.stdout)
            return ClaudeResponse(
                result=data.get("result", ""),
                session_id=data.get("session_id"),
                cost_usd=data.get("cost_usd"),
                raw=data,
            )
        except json.JSONDecodeError:
            # Fallback: return raw output as result
            return ClaudeResponse(
                result=result.stdout.strip(),
                raw={"raw_output": result.stdout},
            )

    def query_with_tools(
        self,
        prompt: str,
        tools: list[str],
        **kwargs,
    ) -> ClaudeResponse:
        """
        Query with specific tools enabled.

        Common tools: Read, Edit, Bash, Write, Glob, Grep

        Example:
            response = claude.query_with_tools(
                "Find all Python files and count lines",
                tools=["Bash", "Glob", "Read"]
            )
        """
        return self.query(prompt, allowed_tools=tools, **kwargs)

    def query_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs,
    ) -> ClaudeResponse:
        """
        Query with JSON schema validation for structured output.

        Example:
            schema = {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "score": {"type": "integer", "minimum": 1, "maximum": 10}
                },
                "required": ["summary", "score"]
            }
            response = claude.query_structured("Rate this code", schema)
        """
        return self.query(prompt, json_schema=json.dumps(schema), **kwargs)


# Convenience function for simple queries
def ask_claude(prompt: str, model: Model = Model.SONNET) -> str:
    """
    Simple one-liner for quick queries.

    Usage:
        from claude_wrapper import ask_claude
        answer = ask_claude("What is the capital of France?")
    """
    wrapper = ClaudeWrapper(model=model)
    return wrapper.query(prompt).result


if __name__ == "__main__":
    # Quick test
    print("Testing Claude CLI wrapper...")

    try:
        claude = ClaudeWrapper()
        response = claude.query("What is 2+2? Reply with just the number.")
        print(f"Response: {response.result}")
        print(f"Session ID: {response.session_id}")
        print("Test passed!")
    except ClaudeError as e:
        print(f"Test failed: {e}")
