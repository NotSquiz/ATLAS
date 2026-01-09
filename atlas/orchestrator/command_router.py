"""
ATLAS Command Router

Parses and routes slash commands to appropriate skill orchestrators.
Separate from atlas/llm/router.py which handles LLM tier routing.

Usage:
    router = CommandRouter()

    # Check if input is a slash command
    if router.is_slash_command("/babybrains next21 regulation"):
        result = await router.execute("/babybrains next21 regulation")

Supported Commands:
    /babybrains status              - Check orchestrator status
    /babybrains qc <file>           - Run QC validation
    /babybrains next21 <domain>     - Full 21s pipeline
    /babybrains next60 <domain>     - Full 60s pipeline

    /knowledge search <query>       - Search knowledge atoms
    /knowledge validate             - Run Tier 1 validators

    /web pre-pr                     - Run npm run pre-pr
    /web review                     - Run all agents

    /app decision <pattern>         - Search decision log

    /simplify <file>                - Analyze code for issues
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import json
import re
import shlex
import sys

from .hooks import HookRunner, HookResult
from .skill_executor import SkillExecutor, SkillResult


class CommandType(Enum):
    """Types of slash commands."""
    BABYBRAINS = "babybrains"
    KNOWLEDGE = "knowledge"
    WEB = "web"
    APP = "app"
    SIMPLIFY = "simplify"  # Code simplification tool
    WORKOUT = "workout"  # FUTURE - Phase 5
    UNKNOWN = "unknown"


@dataclass
class SlashCommand:
    """Parsed slash command."""
    raw: str
    command_type: CommandType
    subcommand: str
    args: list[str] = field(default_factory=list)
    flags: dict[str, str] = field(default_factory=dict)

    @property
    def full_command(self) -> str:
        """Return the full command string (e.g., '/babybrains next21')."""
        return f"/{self.command_type.value} {self.subcommand}".strip()


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[dict] = None


class CommandRouter:
    """
    Routes slash commands to appropriate skill orchestrators.

    Architecture:
        /babybrains -> skills/babybrains/BABYBRAINS.md
        /knowledge  -> skills/knowledge/KNOWLEDGE.md
        /web        -> skills/web/WEB.md
        /app        -> skills/app/APP.md
    """

    # Regex to match slash commands: /command [args...]
    # ^        - start of string
    # /(\w+)   - slash + command name (capture group 1)
    # (?:\s+(.*))?  - optional: whitespace + rest of command (capture group 2)
    # $        - end of string
    SLASH_COMMAND_PATTERN = re.compile(r'^/(\w+)(?:\s+(.*))?$')

    # Repo paths for each command type
    REPO_PATHS = {
        CommandType.BABYBRAINS: Path("/home/squiz/code/babybrains-os"),
        CommandType.KNOWLEDGE: Path("/home/squiz/code/knowledge"),
        CommandType.WEB: Path("/home/squiz/code/web"),
        CommandType.APP: Path("/home/squiz/code/app"),
    }

    # Skills folder base path
    SKILLS_BASE = Path("/home/squiz/ATLAS/skills")

    def __init__(self):
        """Initialize the command router."""
        self._skill_loaders: dict[CommandType, "SkillLoader"] = {}
        self._hook_runner = HookRunner()
        self._skill_executor: Optional[SkillExecutor] = None

    def _get_skill_executor(self) -> SkillExecutor:
        """Lazy initialization of skill executor."""
        if self._skill_executor is None:
            self._skill_executor = SkillExecutor()
        return self._skill_executor

    def is_slash_command(self, text: str) -> bool:
        """Check if text is a slash command."""
        return text.strip().startswith('/') and self.SLASH_COMMAND_PATTERN.match(text.strip()) is not None

    def parse(self, text: str) -> SlashCommand:
        """
        Parse a slash command string into components.

        Examples:
            "/babybrains status" -> SlashCommand(BABYBRAINS, "status", [])
            "/babybrains next21 regulation parents" -> SlashCommand(BABYBRAINS, "next21", ["regulation", "parents"])
            "/knowledge search tantrums" -> SlashCommand(KNOWLEDGE, "search", ["tantrums"])
        """
        text = text.strip()
        match = self.SLASH_COMMAND_PATTERN.match(text)

        if not match:
            return SlashCommand(
                raw=text,
                command_type=CommandType.UNKNOWN,
                subcommand="",
                args=[],
            )

        command_name = match.group(1).lower()
        rest = match.group(2) or ""

        # Parse command type
        try:
            command_type = CommandType(command_name)
        except ValueError:
            command_type = CommandType.UNKNOWN

        # Parse subcommand and args
        parts = shlex.split(rest) if rest else []
        subcommand = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        # Extract flags (--flag value or --flag=value)
        flags = {}
        remaining_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('--'):
                if '=' in arg:
                    key, value = arg[2:].split('=', 1)
                    flags[key] = value
                elif i + 1 < len(args) and not args[i + 1].startswith('-'):
                    flags[arg[2:]] = args[i + 1]
                    i += 1
                else:
                    flags[arg[2:]] = "true"
            else:
                remaining_args.append(arg)
            i += 1

        return SlashCommand(
            raw=text,
            command_type=command_type,
            subcommand=subcommand,
            args=remaining_args,
            flags=flags,
        )

    async def execute(self, text: str) -> CommandResult:
        """
        Execute a slash command.

        This is the main entry point for command execution.
        Routes to appropriate skill loader and executor.
        """
        command = self.parse(text)

        if command.command_type == CommandType.UNKNOWN:
            return CommandResult(
                success=False,
                output="",
                error=f"Unknown command: {text}. Available: /babybrains, /knowledge, /web, /app",
            )

        # Route to appropriate handler
        handler = getattr(self, f"_handle_{command.command_type.value}", None)
        if handler:
            return await handler(command)

        return CommandResult(
            success=False,
            output="",
            error=f"No handler for command type: {command.command_type.value}",
        )

    async def _handle_babybrains(self, command: SlashCommand) -> CommandResult:
        """Handle /babybrains commands."""

        if command.subcommand == "status":
            # Simple status check - proves routing works
            repo_path = self.REPO_PATHS[CommandType.BABYBRAINS]
            skill_path = self.SKILLS_BASE / "babybrains" / "BABYBRAINS.md"

            repo_exists = repo_path.exists()
            skill_exists = skill_path.exists()

            status_lines = [
                "babybrains-os orchestrator status:",
                f"  Repo path: {repo_path} {'[OK]' if repo_exists else '[MISSING]'}",
                f"  Skill file: {skill_path} {'[OK]' if skill_exists else '[STUB]'}",
                "",
                "Available commands:",
                "  /babybrains status              - This status check",
                "  /babybrains qc <file>           - Run QC validation",
                "  /babybrains draft --skill NAME  - Execute skill via CLI (Max, $0)",
                "  /babybrains draft --skill NAME --api  - Execute via API (paid)",
                "  /babybrains next21 <domain>     - Full 21s pipeline (TODO)",
                "  /babybrains next60 <domain>     - Full 60s pipeline (TODO)",
            ]

            return CommandResult(
                success=True,
                output="\n".join(status_lines),
                data={
                    "repo_exists": repo_exists,
                    "skill_exists": skill_exists,
                    "ready": repo_exists,
                },
            )

        elif command.subcommand == "qc":
            # Run QC validation hook
            # Input can be: file path as arg, or JSON via stdin
            input_data = None
            input_source = "stdin"

            if command.args:
                # File path provided as argument
                file_path = Path(command.args[0])
                if not file_path.is_absolute():
                    file_path = self.REPO_PATHS[CommandType.BABYBRAINS] / file_path
                if not file_path.exists():
                    return CommandResult(
                        success=False,
                        output="",
                        error=f"File not found: {file_path}",
                    )
                try:
                    input_data = json.loads(file_path.read_text())
                    input_source = str(file_path)
                except json.JSONDecodeError as e:
                    return CommandResult(
                        success=False,
                        output="",
                        error=f"Invalid JSON in {file_path}: {e}",
                    )
            else:
                # Try to read from stdin if available
                if not sys.stdin.isatty():
                    try:
                        stdin_text = sys.stdin.read()
                        input_data = json.loads(stdin_text)
                    except json.JSONDecodeError as e:
                        return CommandResult(
                            success=False,
                            output="",
                            error=f"Invalid JSON from stdin: {e}",
                        )
                else:
                    return CommandResult(
                        success=False,
                        output="",
                        error="No input provided. Usage: /babybrains qc <file.json> or echo '{...}' | /babybrains qc",
                    )

            # Run the QC hook
            hook_result = await self._hook_runner.run(
                repo="babybrains",
                hook_name="qc_runner",
                input_data=input_data,
            )

            # Format output
            output_lines = [
                f"QC Validation: {'PASSED' if hook_result.passed else 'FAILED'}",
                f"Input: {input_source}",
                "",
            ]

            if hook_result.issues:
                blocking = [i for i in hook_result.issues if i.severity == "block"]
                advisory = [i for i in hook_result.issues if i.severity == "advisory"]

                if blocking:
                    output_lines.append(f"Blocking Issues ({len(blocking)}):")
                    for issue in blocking:
                        output_lines.append(f"  ❌ [{issue.code}] {issue.message}")

                if advisory:
                    output_lines.append(f"\nAdvisory Issues ({len(advisory)}):")
                    for issue in advisory:
                        output_lines.append(f"  ⚠️  [{issue.code}] {issue.message}")

            if not hook_result.passed:
                output_lines.extend([
                    "",
                    "Options:",
                    "  /babybrains qc <file> --fix    # (TODO) Auto-fix suggestions",
                    "  Fix issues manually and re-run QC",
                ])

            return CommandResult(
                success=hook_result.passed,
                output="\n".join(output_lines),
                error=None if hook_result.passed else hook_result.message,
                data={
                    "passed": hook_result.passed,
                    "blocking_count": len([i for i in hook_result.issues if i.severity == "block"]),
                    "advisory_count": len([i for i in hook_result.issues if i.severity == "advisory"]),
                },
            )

        elif command.subcommand == "draft":
            # Execute single skill
            # Usage: /babybrains draft --skill draft_21s [--api] [input.json]
            skill_name = command.flags.get("skill")
            if not skill_name:
                return CommandResult(
                    success=False,
                    output="",
                    error="Missing --skill flag. Usage: /babybrains draft --skill draft_21s [--api]",
                )

            # Check for flags
            use_api = "api" in command.flags
            validate = "no-validate" not in command.flags

            # Parse optional input
            input_data = None
            if command.args:
                # First arg is input file
                input_file = Path(command.args[0])
                if not input_file.is_absolute():
                    input_file = self.REPO_PATHS[CommandType.BABYBRAINS] / input_file
                if not input_file.exists():
                    return CommandResult(
                        success=False,
                        output="",
                        error=f"Input file not found: {input_file}",
                    )
                try:
                    input_data = json.loads(input_file.read_text())
                except json.JSONDecodeError as e:
                    return CommandResult(
                        success=False,
                        output="",
                        error=f"Invalid JSON in {input_file}: {e}",
                    )

            # Execute skill
            try:
                executor = SkillExecutor(use_api=use_api)
                result = await executor.execute(skill_name, input_data=input_data, validate=validate)
            except ValueError as e:
                return CommandResult(
                    success=False,
                    output="",
                    error=f"Skill executor error: {e}",
                )

            # Format output
            mode = "API" if use_api else "CLI (Max)"
            if result.success:
                output_lines = [
                    f"Skill '{skill_name}' executed successfully [{mode}]",
                    f"Tokens: ~{result.tokens_used} | Duration: {result.duration_ms:.0f}ms",
                    "",
                    "Output:",
                    json.dumps(result.output, indent=2),
                ]
                return CommandResult(
                    success=True,
                    output="\n".join(output_lines),
                    data=result.output,
                )
            else:
                output_lines = [
                    f"Skill '{skill_name}' failed: {result.error}",
                ]
                if result.validation_errors:
                    output_lines.append("\nValidation errors:")
                    for err in result.validation_errors:
                        output_lines.append(f"  - {err}")
                if result.raw_output:
                    output_lines.append(f"\nRaw output (truncated):\n{result.raw_output[:500]}")

                return CommandResult(
                    success=False,
                    output="\n".join(output_lines),
                    error=result.error,
                )

        elif command.subcommand in ("next21", "next60"):
            # TODO: Implement full skill chain
            return CommandResult(
                success=False,
                output="",
                error=f"{command.subcommand} skill chain not yet implemented. See Phase 2 in plan.",
            )

        else:
            return CommandResult(
                success=False,
                output="",
                error=f"Unknown babybrains subcommand: {command.subcommand}. Try: status, qc, next21, next60",
            )

    async def _handle_knowledge(self, command: SlashCommand) -> CommandResult:
        """Handle /knowledge commands."""

        if command.subcommand == "status":
            repo_path = self.REPO_PATHS[CommandType.KNOWLEDGE]
            return CommandResult(
                success=True,
                output=f"knowledge orchestrator ready\nRepo: {repo_path}",
                data={"repo_exists": repo_path.exists()},
            )

        return CommandResult(
            success=False,
            output="",
            error=f"/knowledge commands not yet implemented. See Phase 3 in plan.",
        )

    async def _handle_web(self, command: SlashCommand) -> CommandResult:
        """Handle /web commands."""

        if command.subcommand == "status":
            repo_path = self.REPO_PATHS[CommandType.WEB]
            return CommandResult(
                success=True,
                output=f"web orchestrator ready\nRepo: {repo_path}",
                data={"repo_exists": repo_path.exists()},
            )

        return CommandResult(
            success=False,
            output="",
            error=f"/web commands not yet implemented. See Phase 4 in plan.",
        )

    async def _handle_app(self, command: SlashCommand) -> CommandResult:
        """Handle /app commands."""

        if command.subcommand == "status":
            repo_path = self.REPO_PATHS[CommandType.APP]
            return CommandResult(
                success=True,
                output=f"app orchestrator ready\nRepo: {repo_path}",
                data={"repo_exists": repo_path.exists()},
            )

        return CommandResult(
            success=False,
            output="",
            error=f"/app commands not yet implemented. See Phase 4 in plan.",
        )

    async def _handle_workout(self, command: SlashCommand) -> CommandResult:
        """Handle /workout commands (FUTURE - Phase 5)."""
        return CommandResult(
            success=False,
            output="",
            error="/workout commands planned for Phase 5. Not yet implemented.",
        )

    async def _handle_simplify(self, command: SlashCommand) -> CommandResult:
        """Handle /simplify <file> - analyze code for issues."""
        from atlas.simplifier import CodeSimplifier, Severity

        # Get file path
        file_path = command.subcommand if command.subcommand else (command.args[0] if command.args else None)
        if not file_path:
            return CommandResult(success=True, output="Usage: /simplify <file>")

        # Resolve path
        path = Path(file_path)
        if not path.is_absolute() and not path.exists():
            atlas_path = Path("/home/squiz/ATLAS") / file_path
            if atlas_path.exists():
                path = atlas_path

        # Analyze
        result = CodeSimplifier().analyze_file(path)
        if result.error:
            return CommandResult(success=False, output="", error=result.error)

        return CommandResult(
            success=not result.by_severity(Severity.ERROR),
            output=result.format(),
            data=result.to_dict(),
        )


# Convenience function for quick command execution
async def execute_command(text: str) -> CommandResult:
    """Execute a slash command using the default router."""
    router = CommandRouter()
    return await router.execute(text)


# CLI entry point
if __name__ == "__main__":
    import asyncio

    def main():
        """CLI entry point for command router."""
        if len(sys.argv) < 2:
            print("Usage: python -m atlas.orchestrator.command_router <command> [args...]")
            print("Example: python -m atlas.orchestrator.command_router babybrains status")
            sys.exit(1)

        # Build command from args (add leading /)
        cmd = "/" + " ".join(sys.argv[1:])

        # Execute
        result = asyncio.run(execute_command(cmd))

        # Always print output if present
        if result.output:
            print(result.output)

        # Print error if present and no output shown
        if result.error and not result.output:
            print(f"Error: {result.error}", file=sys.stderr)

        # Exit with appropriate code
        if not result.success:
            sys.exit(1)

    main()
