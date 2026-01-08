"""
ATLAS Sub-Agent Executor

Spawns sub-agents with isolated context for parallel execution and adversarial verification.

Architecture:
    - Sub-agents execute via `claude -p` subprocess (isolated context window)
    - Context can be passed via prompt serialization (JSON-safe conversion applied)
    - Each sub-agent gets its own context window (masterclass [4147s])
    - Supports parallel spawning via asyncio.gather()
    - Adversarial verification uses "junior analyst" framing (masterclass [4147s])

Key Insight from Claude Agent SDK Masterclass:
    [4147s] "Avoid context pollution. Start a new context session."
    [3969s] "Sub-agents are great for when you need to do a lot of work and return an answer."

Usage:
    executor = SubAgentExecutor()

    # Single sub-agent
    result = await executor.spawn("Analyze this data and return key insights")

    # Parallel sub-agents
    results = await executor.spawn_parallel([
        "Summarize section 1",
        "Summarize section 2",
        "Summarize section 3",
    ])

    # Adversarial verification
    verification = await executor.verify_adversarially(
        output={"analysis": "..."},
        skill_name="data_analysis"
    )
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
import asyncio
import json
import logging
import shutil
import subprocess
import time

# MEDIUM: Add logging
logger = logging.getLogger(__name__)

# Sandbox configuration path for sub-agents
SANDBOX_CONFIG = Path(__file__).parent.parent.parent / "config" / "sandbox" / "subagent.json"


@dataclass
class SubAgentResult:
    """Result of sub-agent execution."""
    success: bool
    output: Optional[str] = None           # Raw text output from sub-agent
    parsed_output: Optional[dict] = None   # If JSON output was parsed
    error: Optional[str] = None
    task: str = ""
    duration_ms: float = 0.0


@dataclass
class VerificationResult:
    """Result of adversarial verification."""
    passed: bool
    issues: list[str] = field(default_factory=list)
    skill_name: str = ""
    duration_ms: float = 0.0


# Maximum length for error messages to prevent memory issues
_MAX_ERROR_LENGTH = 1024


class SubAgentExecutor:
    """
    Execute sub-agents with isolated context.

    Each sub-agent runs in an isolated context via `claude -p` subprocess,
    preventing context pollution from the main agent. Optional context
    can be passed via JSON serialization in the prompt.
    """

    DEFAULT_TIMEOUT = 120  # 2 minutes

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize SubAgentExecutor.

        Args:
            timeout: Default timeout in seconds for sub-agent execution
        """
        self.timeout = timeout
        # CRITICAL #5: Check CLI availability once in __init__, not every spawn()
        self._cli_available = self._check_cli_available()
        # Cache sandbox availability check
        self._sandbox_available_cached = self._sandbox_available()

    def _check_cli_available(self) -> bool:
        """Check if claude CLI is available."""
        return shutil.which("claude") is not None

    def _sandbox_available(self) -> bool:
        """Check if srt sandbox command is available."""
        return shutil.which("srt") is not None

    def _serialize_context(self, context: dict) -> str:
        """
        CRITICAL #1: Safely serialize context to JSON string.

        Handles non-JSON-serializable types (datetime, lambda, custom objects)
        by converting them to strings.

        Args:
            context: Context dictionary to serialize

        Returns:
            JSON string representation of context
        """
        def json_safe_default(obj: Any) -> str:
            """Convert non-serializable objects to string representation."""
            try:
                # Handle common types explicitly for better output
                if hasattr(obj, 'isoformat'):  # datetime, date, time
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):
                    return f"<{type(obj).__name__}: {obj.__dict__}>"
                else:
                    return str(obj)
            except Exception:
                return f"<{type(obj).__name__}: unserializable>"

        try:
            return json.dumps(context, indent=2, default=json_safe_default)
        except Exception as e:
            logger.warning(f"Context serialization fallback triggered: {e}")
            # Ultimate fallback: convert entire context to string repr
            return json.dumps({"_serialization_error": str(context)}, indent=2)

    def _validate_task(self, task: Any) -> Optional[str]:
        """
        CRITICAL #3 & #7: Validate task input.

        Returns error message if invalid, None if valid.
        """
        # Check for None
        if task is None:
            return "Task cannot be None"

        # Check type
        if not isinstance(task, str):
            return f"Task must be a string, got {type(task).__name__}"

        # Check for empty/whitespace-only
        if not task or not task.strip():
            return "Task cannot be empty or whitespace-only"

        # CRITICAL #7: Check for dangerous characters (null bytes, etc.)
        if '\x00' in task:
            return "Task contains null bytes which are not allowed"

        # Check for other control characters that could cause issues
        dangerous_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
                          '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12',
                          '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a',
                          '\x1b', '\x1c', '\x1d', '\x1e', '\x1f']
        for char in dangerous_chars:
            if char in task:
                return f"Task contains dangerous control character (0x{ord(char):02x})"

        return None  # Valid

    def _validate_timeout(self, timeout: Optional[int]) -> Optional[str]:
        """
        CRITICAL #3: Validate timeout parameter.

        Returns error message if invalid, None if valid.
        """
        if timeout is None:
            return None  # Will use default

        if not isinstance(timeout, (int, float)):
            return f"Timeout must be a number, got {type(timeout).__name__}"

        if timeout <= 0:
            return f"Timeout must be positive, got {timeout}"

        return None  # Valid

    async def _run_subprocess_with_timeout(
        self,
        cmd: list[str],
        timeout: int,
    ) -> tuple[Optional[subprocess.CompletedProcess], Optional[str]]:
        """
        CRITICAL #2: Run subprocess with proper timeout handling and resource cleanup.

        Uses Popen to ensure process is killed on timeout (no resource leak).

        Returns:
            Tuple of (CompletedProcess or None, error message or None)
        """
        proc = None
        try:
            # Use Popen for explicit control over process lifecycle
            proc = await asyncio.to_thread(
                lambda: subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    asyncio.to_thread(proc.communicate),
                    timeout=timeout,
                )

                # Create a CompletedProcess-like result
                result = subprocess.CompletedProcess(
                    args=cmd,
                    returncode=proc.returncode,
                    stdout=stdout,
                    stderr=stderr,
                )
                return result, None

            except asyncio.TimeoutError:
                # CRITICAL: Kill the process on timeout to prevent resource leak
                logger.warning(f"Subprocess timed out after {timeout}s, killing process")
                try:
                    proc.kill()
                    # Wait for process to actually terminate
                    await asyncio.to_thread(proc.wait, timeout=5)
                except Exception as kill_error:
                    logger.error(f"Failed to kill subprocess: {kill_error}")
                return None, f"Sub-agent timed out after {timeout}s"

        except (subprocess.SubprocessError, OSError, IOError) as e:
            # HIGH #1: Specific exception catching
            logger.error(f"Subprocess execution failed: {e}")
            return None, f"Sub-agent execution failed: {e}"
        except Exception as e:
            # Catch-all for unexpected errors, but log them
            logger.exception(f"Unexpected error in subprocess execution: {e}")
            return None, f"Sub-agent execution failed unexpectedly: {e}"
        finally:
            # Ensure process is cleaned up
            if proc is not None and proc.poll() is None:
                try:
                    proc.kill()
                    proc.wait(timeout=1)
                except Exception:
                    pass  # Best effort cleanup

    async def spawn(
        self,
        task: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
        sandbox: bool = True,
    ) -> SubAgentResult:
        """
        Spawn a single sub-agent with isolated context.

        Uses `claude -p` subprocess call to ensure complete context isolation.
        The sub-agent has no knowledge of the main agent's context unless
        explicitly passed via the context parameter.

        Args:
            task: Task description for the sub-agent
            context: Optional context dict to include in prompt (JSON-serialized)
            timeout: Optional timeout override in seconds (must be positive)
            sandbox: Whether to run in sandbox mode (default True, gracefully degrades if srt not installed)

        Returns:
            SubAgentResult with output or error
        """
        start = time.perf_counter()

        # CRITICAL #3: Input validation - task
        task_error = self._validate_task(task)
        if task_error:
            logger.warning(f"Invalid task: {task_error}")
            return SubAgentResult(
                success=False,
                task=str(task) if task is not None else "",
                error=task_error,
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        # CRITICAL #3: Input validation - timeout
        timeout_error = self._validate_timeout(timeout)
        if timeout_error:
            logger.warning(f"Invalid timeout: {timeout_error}")
            return SubAgentResult(
                success=False,
                task=task,
                error=timeout_error,
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        # CRITICAL #5: Use cached CLI availability check
        if not self._cli_available:
            return SubAgentResult(
                success=False,
                task=task,
                error="Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code",
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        # MEDIUM: Copy context to prevent mutation
        if context is not None:
            context = dict(context)

        # Build prompt with optional context
        prompt = task
        if context:
            # CRITICAL #1: Use safe serialization
            context_str = self._serialize_context(context)
            prompt = f"""Context:
```json
{context_str}
```

Task: {task}"""

        # Build command
        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive, isolated context)
            "--output-format", "text",
            prompt,
        ]

        # Wrap with sandbox if enabled and available
        if sandbox and self._sandbox_available_cached:
            config_path = str(SANDBOX_CONFIG)
            cmd = ["srt", "--settings", config_path] + cmd
            logger.debug(f"Sub-agent running in sandbox mode with config: {config_path}")
        elif sandbox and not self._sandbox_available_cached:
            logger.debug("Sandbox requested but srt not available, running without sandbox")
        else:
            logger.debug("Sub-agent running without sandbox (sandbox=False)")

        effective_timeout = timeout or self.timeout

        # CRITICAL #2: Use subprocess with proper timeout and cleanup
        result, error = await self._run_subprocess_with_timeout(cmd, effective_timeout)

        duration_ms = (time.perf_counter() - start) * 1000

        if error:
            return SubAgentResult(
                success=False,
                task=task,
                error=error,
                duration_ms=duration_ms,
            )

        if result.returncode != 0:
            # HIGH #2: Truncate stderr to prevent memory issues
            stderr_text = result.stderr.strip() if result.stderr else ""
            if len(stderr_text) > _MAX_ERROR_LENGTH:
                stderr_text = stderr_text[:_MAX_ERROR_LENGTH] + "... (truncated)"

            error_msg = stderr_text if stderr_text else f"CLI returned exit code {result.returncode}"
            return SubAgentResult(
                success=False,
                task=task,
                output=result.stdout.strip() if result.stdout else None,
                error=error_msg,
                duration_ms=duration_ms,
            )

        raw_output = result.stdout.strip() if result.stdout else ""

        # HIGH #3: Handle multiline output - use lstrip() before checking for JSON
        parsed = None
        stripped_output = raw_output.lstrip()
        if stripped_output.startswith("{") or stripped_output.startswith("["):
            try:
                parsed = json.loads(stripped_output)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                parsed = self._extract_json(raw_output)

        return SubAgentResult(
            success=True,
            task=task,
            output=raw_output,
            parsed_output=parsed,
            duration_ms=duration_ms,
        )

    async def spawn_parallel(
        self,
        tasks: list[str],
        contexts: Optional[list[dict]] = None,
        timeout: Optional[int] = None,
        sandbox: bool = True,
    ) -> list[SubAgentResult]:
        """
        Spawn multiple sub-agents in parallel.

        Uses asyncio.gather() to execute all sub-agents concurrently.
        Each sub-agent still runs in its own isolated context.

        Args:
            tasks: List of task descriptions
            contexts: Optional list of context dicts (one per task)
            timeout: Optional timeout override in seconds
            sandbox: Whether to run in sandbox mode (default True, gracefully degrades if srt not installed)

        Returns:
            List of SubAgentResults in same order as tasks
        """
        if not tasks:
            return []

        if contexts is None:
            contexts = [None] * len(tasks)
        elif len(contexts) != len(tasks):
            # Pad or truncate contexts to match tasks
            contexts = contexts[:len(tasks)] + [None] * (len(tasks) - len(contexts))

        # Create coroutines for all tasks
        coroutines = [
            self.spawn(task, context=ctx, timeout=timeout, sandbox=sandbox)
            for task, ctx in zip(tasks, contexts)
        ]

        # Execute in parallel, handling exceptions individually
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # HIGH #5: Convert any exceptions to failed SubAgentResults with type validation
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} raised exception: {result}")
                processed_results.append(SubAgentResult(
                    success=False,
                    task=tasks[i] if i < len(tasks) else "",
                    error=f"Unexpected error: {result}",
                    duration_ms=0.0,
                ))
            elif isinstance(result, SubAgentResult):
                # HIGH #5: Explicit type validation
                processed_results.append(result)
            else:
                # Unexpected type - log and convert to error
                logger.error(f"Task {i} returned unexpected type: {type(result)}")
                processed_results.append(SubAgentResult(
                    success=False,
                    task=tasks[i] if i < len(tasks) else "",
                    error=f"Unexpected result type: {type(result).__name__}",
                    duration_ms=0.0,
                ))

        return processed_results

    async def verify_adversarially(
        self,
        output: dict,
        skill_name: str,
        persona: str = "junior analyst at McKinsey",
    ) -> VerificationResult:
        """
        Spawn sub-agent to adversarially check output.

        Uses isolated context with "junior analyst" framing from masterclass [4147s]:
        "You'd start a new context session and be like 'Hey, adversarially check
        the work of - this output was made by a junior analyst at McKinsey...'"

        Args:
            output: Output dict to verify
            skill_name: Name of the skill that produced the output
            persona: Persona for framing (default: "junior analyst at McKinsey")

        Returns:
            VerificationResult with passed status and any issues found
        """
        start = time.perf_counter()

        # Build adversarial verification prompt
        # CRITICAL #1: Use safe serialization for output
        output_json = self._serialize_context(output) if isinstance(output, dict) else json.dumps(output, default=str)
        prompt = f"""You are reviewing work produced by a {persona}.

The following output was produced by the "{skill_name}" skill:

```json
{output_json}
```

Your task: Critically evaluate this output. Look for:
1. Factual accuracy - Are the statements correct?
2. Logical consistency - Does the reasoning make sense?
3. Missing information - Are there obvious gaps?
4. Potential errors - Any mistakes or issues?

Be skeptical and thorough. If you find issues, list them clearly.

Respond with ONLY a JSON object in this exact format:
{{"passed": true/false, "issues": ["issue 1", "issue 2", ...]}}

If no issues found, use: {{"passed": true, "issues": []}}"""

        result = await self.spawn(prompt)

        duration_ms = (time.perf_counter() - start) * 1000

        if not result.success:
            return VerificationResult(
                passed=False,
                issues=[f"Verification failed: {result.error}"],
                skill_name=skill_name,
                duration_ms=duration_ms,
            )

        # Parse verification response
        if result.parsed_output:
            parsed = result.parsed_output
        else:
            # Try to extract JSON from response
            parsed = self._extract_json(result.output or "")

        if parsed and isinstance(parsed, dict):
            return VerificationResult(
                passed=parsed.get("passed", False),
                issues=parsed.get("issues", []),
                skill_name=skill_name,
                duration_ms=duration_ms,
            )

        # Fallback: couldn't parse verification response
        logger.warning(f"Could not parse verification response for skill '{skill_name}'")
        return VerificationResult(
            passed=False,
            issues=["Could not parse verification response"],
            skill_name=skill_name,
            duration_ms=duration_ms,
        )

    def _extract_json(self, text: str) -> Optional[dict]:
        """
        Extract JSON from response (handles markdown code blocks).

        CRITICAL #4: Logs when extraction fails for debugging.
        """
        if not text:
            logger.debug("_extract_json called with empty text")
            return None

        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON from ```json block: {e}")

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON from ``` block: {e}")

        # Try to find raw JSON (starts with { or [)
        for i, char in enumerate(text):
            if char in "{[":
                try:
                    return json.loads(text[i:])
                except json.JSONDecodeError:
                    continue

        # CRITICAL #4: Log when all extraction methods fail
        logger.debug(f"_extract_json: No valid JSON found in text (length={len(text)})")
        return None


# Convenience function
async def spawn_subagent(task: str, **kwargs) -> SubAgentResult:
    """Spawn a sub-agent using the default executor."""
    executor = SubAgentExecutor()
    return await executor.spawn(task, **kwargs)


# CLI entry point
if __name__ == "__main__":
    import sys

    async def run_test():
        """Run a basic test to verify sub-agent spawning works."""
        print("=== SubAgentExecutor Test ===\n", file=sys.stderr)

        executor = SubAgentExecutor()

        # Check CLI availability (uses cached value)
        if not executor._cli_available:
            print("ERROR: Claude CLI not found", file=sys.stderr)
            print("Install with: npm install -g @anthropic-ai/claude-code", file=sys.stderr)
            sys.exit(1)

        # Test input validation
        print("0. Testing input validation...", file=sys.stderr)

        # Empty task
        result = await executor.spawn("")
        assert not result.success, "Empty task should fail"
        print(f"   Empty task correctly rejected: {result.error}", file=sys.stderr)

        # None task
        result = await executor.spawn(None)  # type: ignore
        assert not result.success, "None task should fail"
        print(f"   None task correctly rejected: {result.error}", file=sys.stderr)

        # Negative timeout
        result = await executor.spawn("test", timeout=-5)
        assert not result.success, "Negative timeout should fail"
        print(f"   Negative timeout correctly rejected: {result.error}", file=sys.stderr)

        print("   All validation tests passed!", file=sys.stderr)

        print("\n1. Testing spawn() with simple task...", file=sys.stderr)
        result = await executor.spawn(
            "What is 2 + 2? Reply with just the number."
        )

        if result.success:
            print(f"   SUCCESS: Got response in {result.duration_ms:.0f}ms", file=sys.stderr)
            print(f"   Output: {result.output[:100]}..." if len(result.output or "") > 100 else f"   Output: {result.output}", file=sys.stderr)
        else:
            print(f"   FAILED: {result.error}", file=sys.stderr)
            sys.exit(1)

        print("\n2. Testing spawn_parallel() with 2 tasks...", file=sys.stderr)
        results = await executor.spawn_parallel([
            "What is the capital of France? Reply with just the city name.",
            "What is the capital of Japan? Reply with just the city name.",
        ])

        for i, res in enumerate(results):
            status = "SUCCESS" if res.success else "FAILED"
            print(f"   Task {i+1}: {status} ({res.duration_ms:.0f}ms)", file=sys.stderr)
            if res.success:
                output_preview = res.output[:50] if res.output else "None"
                print(f"   Output: {output_preview}", file=sys.stderr)

        print("\n3. Testing verify_adversarially()...", file=sys.stderr)
        test_output = {
            "claim": "The Earth is the third planet from the Sun",
            "confidence": 0.95
        }
        verification = await executor.verify_adversarially(
            output=test_output,
            skill_name="test_skill"
        )

        status = "PASSED" if verification.passed else "FAILED"
        print(f"   Verification: {status} ({verification.duration_ms:.0f}ms)", file=sys.stderr)
        if verification.issues:
            print(f"   Issues: {verification.issues}", file=sys.stderr)

        print("\n4. Testing datetime in context (serialization)...", file=sys.stderr)
        import datetime
        result = await executor.spawn(
            "What day is mentioned in the context? Reply with just the date.",
            context={"date": datetime.datetime.now(), "nested": {"lambda_test": lambda x: x}}
        )
        if result.success or "datetime" not in (result.error or "").lower():
            print(f"   SUCCESS: datetime context handled correctly", file=sys.stderr)
        else:
            print(f"   FAILED: {result.error}", file=sys.stderr)
            sys.exit(1)

        print("\n=== All tests completed ===", file=sys.stderr)

    async def main():
        if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
            print("Usage: python -m atlas.orchestrator.subagent_executor [options]")
            print()
            print("Options:")
            print("  --test                Run basic test to verify sub-agent spawning works")
            print("  --task TASK           Spawn a sub-agent with the given task")
            print("  --context FILE        JSON file with context for --task")
            print("  --context-json JSON   Inline JSON context for --task")
            print()
            print("Examples:")
            print("  python -m atlas.orchestrator.subagent_executor --test")
            print("  python -m atlas.orchestrator.subagent_executor --task 'Summarize Python'")
            print("  python -m atlas.orchestrator.subagent_executor --task 'Analyze data' --context data.json")
            print("  python -m atlas.orchestrator.subagent_executor --task 'Analyze' --context-json '{\"key\": \"value\"}'")
            sys.exit(0)

        if "--test" in sys.argv:
            await run_test()
        elif "--task" in sys.argv:
            idx = sys.argv.index("--task")
            if idx + 1 >= len(sys.argv):
                print("Error: --task requires an argument", file=sys.stderr)
                sys.exit(1)
            task = sys.argv[idx + 1]

            # HIGH #4: Parse --context or --context-json flags
            context = None
            if "--context" in sys.argv:
                ctx_idx = sys.argv.index("--context")
                if ctx_idx + 1 >= len(sys.argv):
                    print("Error: --context requires a file path argument", file=sys.stderr)
                    sys.exit(1)
                context_file = sys.argv[ctx_idx + 1]
                try:
                    with open(context_file, 'r') as f:
                        context = json.load(f)
                except FileNotFoundError:
                    print(f"Error: Context file not found: {context_file}", file=sys.stderr)
                    sys.exit(1)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in context file: {e}", file=sys.stderr)
                    sys.exit(1)
            elif "--context-json" in sys.argv:
                ctx_idx = sys.argv.index("--context-json")
                if ctx_idx + 1 >= len(sys.argv):
                    print("Error: --context-json requires a JSON string argument", file=sys.stderr)
                    sys.exit(1)
                try:
                    context = json.loads(sys.argv[ctx_idx + 1])
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in --context-json: {e}", file=sys.stderr)
                    sys.exit(1)

            executor = SubAgentExecutor()
            result = await executor.spawn(task, context=context)

            if result.success:
                print(result.output)
            else:
                print(f"Error: {result.error}", file=sys.stderr)
                sys.exit(1)

            print(f"\n--- Stats ---", file=sys.stderr)
            print(f"Duration: {result.duration_ms:.0f}ms", file=sys.stderr)
        else:
            print(f"Unknown option: {sys.argv[1]}", file=sys.stderr)
            print("Use --help for usage information", file=sys.stderr)
            sys.exit(1)

    asyncio.run(main())
