"""
ATLAS Hook Framework

Wraps existing validators as Claude Agent SDK-style hooks.
Provides deterministic verification without LLM involvement.

Principle: Wrap existing validators, don't rebuild.

Hooks:
    babybrains:
        - qc_runner: Wraps qc/qc_runner.py (blocking)

    babybrains_content:
        - qc_brief: Brief structural validation (30s)
        - qc_safety: Safety gate with hazard/supervision checks (30s)
        - qc_montessori: Montessori alignment validation (30s)
        - qc_hook_token: Hook in scene 1 validation (30s)
        - qc_script: Script requirements validation (30s)
        - qc_audio: Audio levels validation via ffmpeg (180s)
        - qc_caption_wer: Caption WER via faster-whisper (180s)
        - qc_safezone: Caption safe zones validation (30s)

    knowledge:
        - tier1_validators: Wraps scripts/validate_*.py (blocking)
        - activity_qc: Activity quality/voice validation (blocking)

    web:
        - pre_pr: Wraps npm run pre-pr (blocking)

Usage:
    runner = HookRunner()

    # Run hook with stdin input
    result = await runner.run("babybrains", "qc_runner", input_data={"format": "s21", ...})

    # Run hook with CLI args (for file-based hooks)
    result = await runner.run(
        "babybrains_content", "qc_audio",
        cli_args=["path/to/audio.wav", "--master"]
    )

    if not result.passed:
        print(f"Hook blocked: {result.issues}")
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any
import asyncio
import json
import logging
import subprocess

logger = logging.getLogger(__name__)


class HookTiming(Enum):
    """When a hook runs relative to skill execution."""
    PRE_EXECUTION = "pre"    # Before skill runs (validate inputs)
    POST_EXECUTION = "post"  # After skill completes (validate outputs)


@dataclass
class HookIssue:
    """Single issue from a hook."""
    code: str
    message: str
    severity: str = "block"  # "block" or "advisory"


@dataclass
class HookResult:
    """Result of hook execution."""
    passed: bool
    blocking: bool
    issues: list[HookIssue] = field(default_factory=list)
    message: str = ""
    raw_output: str = ""
    exit_code: int = 0
    hook_name: str = ""  # Which hook produced this result

    @property
    def blocking_issues(self) -> list[HookIssue]:
        """Return only blocking issues."""
        return [i for i in self.issues if i.severity == "block"]

    @property
    def advisory_issues(self) -> list[HookIssue]:
        """Return only advisory issues."""
        return [i for i in self.issues if i.severity == "advisory"]


class HookRunner:
    """
    Executes hooks by wrapping existing validators.

    Each hook is defined as a shell command that:
    - Accepts input via stdin (JSON) or file argument
    - Returns exit code 0 for pass, non-zero for fail
    - Outputs structured result (JSON preferred)
    """

    # Hook definitions: repo -> hook_name -> config
    HOOKS = {
        "babybrains": {
            "qc_runner": {
                "cmd": ["python", "qc/qc_runner.py"],
                "cwd": "/home/squiz/code/babybrains-os",
                "blocking": True,
                "input_mode": "stdin",  # Pass input via stdin as JSON
                "output_format": "json",  # Expects JSON output
                "timing": HookTiming.POST_EXECUTION,
                # Block codes from qc_rules.yaml
                "block_codes": [
                    "HOOK_FLAG_MISSING",
                    "HOOK_TOO_LONG",
                    "FIRST_FRAME_ACTION",
                    "WORD_BUDGET_S21",
                    "WORD_BUDGET_S60",
                    "AU_CUES_EXCESS",
                    "SRT_MISSING",
                    "AGE_MATERIAL_MISMATCH",
                    "SAFETY_LINES_MISSING",
                ],
            },
        },
        "knowledge": {
            "tier1_validators": {
                "cmd": ["bash", "-c", """
                    python scripts/validate_observations_schema.py && \
                    python scripts/check_observation_dangling.py && \
                    python scripts/validate_evidence_atoms.py
                """],
                "cwd": "/home/squiz/code/knowledge",
                "blocking": True,
                "input_mode": "none",
                "output_format": "text",
                "timing": HookTiming.POST_EXECUTION,
            },
            "activity_qc": {
                "cmd": ["python3", "scripts/check_activity_quality.py"],
                "cwd": "/home/squiz/code/knowledge",
                "blocking": True,
                "input_mode": "stdin",
                "output_format": "json",
                "timeout": 120,  # D109: LLM context checks need >30s
                "timing": HookTiming.POST_EXECUTION,
                "block_codes": [
                    "VOICE_EM_DASH",
                    "VOICE_FORMAL_TRANSITION",
                    "VOICE_SUPERLATIVE",
                    "VOICE_PRESSURE_LANGUAGE",  # D35: Added to match D32 enforcement
                    "STRUCTURE_MISSING_SECTION",
                    "STRUCTURE_INVALID_YAML",
                    "CROSS_REF_INVALID_PRINCIPLE",
                ],
            },
        },
        "web": {
            "pre_pr": {
                "cmd": ["npm", "run", "pre-pr"],
                "cwd": "/home/squiz/code/web",
                "blocking": True,
                "input_mode": "none",
                "output_format": "text",
                "timing": HookTiming.POST_EXECUTION,
            },
        },
        # Baby Brains Content Production QC Hooks (Phase 1)
        # All hooks output JSON: {"pass": bool, "issues": [{"code": str, "msg": str}]}
        "babybrains_content": {
            "qc_brief": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_brief"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "stdin",
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 30,
                "block_codes": [
                    "BRIEF_MISSING_TITLE",
                    "BRIEF_MISSING_HOOK_TEXT",
                    "BRIEF_MISSING_AGE_RANGE",
                    "BRIEF_INVALID_AGE_RANGE",
                    "BRIEF_MISSING_TARGET_LENGTH",
                    "BRIEF_INVALID_TARGET_LENGTH",
                    "BRIEF_INVALID_MONTESSORI_PRINCIPLE",
                    "BRIEF_INVALID_CONTENT_PILLAR",
                    "BRIEF_INVALID_HOOK_PATTERN",
                    "BRIEF_HOOK_TOO_LONG",
                ],
            },
            "qc_safety": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_safety"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "stdin",
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 30,
                "block_codes": [
                    "SAFETY_CHOKING_HAZARD",
                    "SAFETY_UNSUPERVISED",
                    "SAFETY_MEDICAL_CLAIM",
                    "SAFETY_DANGEROUS_ITEM",
                    "SAFETY_WATER_HAZARD",
                    "SAFETY_AGE_INAPPROPRIATE",
                ],
            },
            "qc_montessori": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_montessori"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "stdin",
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 30,
                "block_codes": [
                    "MONTESSORI_PLASTIC_TOYS",
                    "MONTESSORI_BRANDED_CHARACTER",
                    "MONTESSORI_FANTASY_UNDER6",
                    "MONTESSORI_EXTRINSIC_REWARD",
                    "MONTESSORI_LANGUAGE",
                ],
            },
            "qc_hook_token": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_hook_token"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "stdin",
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 30,
                "block_codes": [
                    "HOOK_TOKEN_MISSING",
                    "HOOK_TOO_LATE",
                    "HOOK_WORD_COUNT",
                    "HOOK_PATTERN_MISMATCH",
                ],
            },
            "qc_script": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_script"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "stdin",
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 30,
                "block_codes": [
                    "SCRIPT_INVALID_FORMAT",
                    "SCRIPT_WORD_BUDGET_UNDER",
                    "SCRIPT_WORD_BUDGET_EXCEEDED",
                    "SCRIPT_SCENE_COUNT_LOW",
                    "SCRIPT_SCENE_COUNT_HIGH",
                    "SCRIPT_AU_SPELLING",
                    "SCRIPT_EM_DASH",
                    "SCRIPT_FORMAL_TRANSITION",
                    "SCRIPT_NO_CONTRACTION",
                    "SCRIPT_EMPTY_SCENE",
                    "SCRIPT_SCENE_TOO_LONG",
                    "SCRIPT_INVALID_JSON",
                ],
            },
            # CLI-based hooks (take file paths as arguments, not stdin)
            # These require special handling in the pipeline - pass file paths via cmd
            "qc_audio": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_audio"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "args",  # Takes file path as positional arg
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 180,  # Longer timeout for ffmpeg processing
                "block_codes": [
                    "AUDIO_FILE_NOT_FOUND",
                    "AUDIO_MEASUREMENT_FAILED",
                    "AUDIO_MEASUREMENT_INVALID",
                    "AUDIO_LUFS_TOO_QUIET",
                    "AUDIO_LUFS_TOO_LOUD",
                    "AUDIO_TRUE_PEAK_EXCEEDED",
                    "AUDIO_LRA_EXCEEDED",
                ],
            },
            "qc_caption_wer": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_caption_wer"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "args",  # Takes --video and --srt as args
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 180,  # Longer timeout for Whisper processing
                "block_codes": [
                    "CAPTION_VIDEO_NOT_FOUND",
                    "CAPTION_SRT_NOT_FOUND",
                    "CAPTION_SRT_EMPTY",
                    "CAPTION_TRANSCRIPTION_FAILED",
                    "CAPTION_WER_TOO_HIGH",
                ],
            },
            "qc_safezone": {
                "cmd": ["python3", "-m", "atlas.babybrains.content.hooks.qc_safezone"],
                "cwd": "/home/squiz/code/ATLAS",
                "blocking": True,
                "input_mode": "args",  # Takes --subtitle and --platform as args
                "output_format": "json",
                "timing": HookTiming.POST_EXECUTION,
                "timeout": 30,
                "block_codes": [
                    "SAFEZONE_FILE_NOT_FOUND",
                    "SAFEZONE_UNKNOWN_PLATFORM",
                    "SAFEZONE_TOP_VIOLATION",
                    "SAFEZONE_BOTTOM_VIOLATION",
                    "SAFEZONE_SIDE_VIOLATION",
                ],
            },
        },
    }

    def __init__(self):
        """Initialize the hook runner."""
        pass

    def get_available_hooks(self, repo: str) -> list[str]:
        """Get list of available hooks for a repo."""
        return list(self.HOOKS.get(repo, {}).keys())

    def _get_hook_timing(self, config: dict) -> HookTiming:
        """
        Get timing from hook config with validation and backwards compatibility.

        Handles:
            - Missing timing field -> defaults to POST_EXECUTION
            - String values ("pre", "post") -> converts to enum
            - Invalid values -> raises clear error
        """
        timing = config.get("timing", HookTiming.POST_EXECUTION)

        # Handle string values for robustness
        if isinstance(timing, str):
            try:
                return HookTiming(timing)
            except ValueError:
                valid = [t.value for t in HookTiming]
                raise ValueError(f"Invalid timing '{timing}'. Must be one of: {valid}")

        # Validate enum type
        if not isinstance(timing, HookTiming):
            raise TypeError(f"timing must be HookTiming enum, got {type(timing).__name__}")

        return timing

    def get_hooks_by_timing(self, repo: str, timing: HookTiming) -> list[str]:
        """
        Get hook names for a specific timing phase.

        Args:
            repo: Repository name (babybrains, knowledge, web)
            timing: Which phase (PRE_EXECUTION or POST_EXECUTION)

        Returns:
            List of hook names in definition order (dict order).
            Empty list if repo not found or no hooks match timing.
        """
        repo_hooks = self.HOOKS.get(repo, {})
        matching = []

        for hook_name, config in repo_hooks.items():
            hook_timing = self._get_hook_timing(config)
            if hook_timing == timing:
                matching.append(hook_name)

        return matching

    async def run_all_for_timing(
        self,
        repo: str,
        timing: HookTiming,
        input_data: Optional[dict] = None,
        stop_on_block: bool = True,
        timeout: Optional[int] = None,
    ) -> list[HookResult]:
        """
        Run all hooks for a specific timing phase.

        Args:
            repo: Repository name
            timing: Which phase (PRE_EXECUTION or POST_EXECUTION)
            input_data: Data to pass to hooks via stdin (if hook expects it)
            stop_on_block: If True, stop on first blocking failure.
                           If False, run all hooks and collect all results.
            timeout: Per-hook timeout override (uses config timeout if None)

        Returns:
            List of HookResults in execution order.
            Empty list if no hooks match the timing.

        Behavior:
            - Hooks run sequentially in definition order
            - Each result includes hook_name for identification
            - If stop_on_block=True and a blocking hook fails, remaining hooks are skipped
            - Each hook uses its configured timeout unless overridden

        Note:
            Hooks with input_mode="args" require individual run() calls with cli_args.
        """
        hook_names = self.get_hooks_by_timing(repo, timing)
        results = []

        for hook_name in hook_names:
            result = await self.run(repo, hook_name, input_data=input_data, timeout=timeout)
            result.hook_name = hook_name  # Populate hook_name
            results.append(result)

            # Stop on blocking failure if requested
            if stop_on_block and result.blocking and not result.passed:
                break

        return results

    async def run(
        self,
        repo: str,
        hook_name: str,
        input_data: Optional[dict] = None,
        input_file: Optional[Path] = None,
        timeout: Optional[int] = None,
        cli_args: Optional[list[str]] = None,
    ) -> HookResult:
        """
        Run a hook and return the result.

        Args:
            repo: Repository name (babybrains, knowledge, web, babybrains_content)
            hook_name: Hook name (qc_runner, tier1_validators, qc_brief, etc.)
            input_data: Data to pass as JSON via stdin (for input_mode="stdin")
            input_file: File path to pass as argument
            timeout: Timeout in seconds (overrides config timeout if provided)
            cli_args: Command-line arguments to append (for input_mode="args")

        Returns:
            HookResult with pass/fail status and issues
        """
        hook_config = self.HOOKS.get(repo, {}).get(hook_name)
        if not hook_config:
            return HookResult(
                passed=False,
                blocking=False,
                message=f"Unknown hook: {repo}/{hook_name}",
                issues=[HookIssue(code="UNKNOWN_HOOK", message=f"Hook not found: {repo}/{hook_name}")],
                hook_name=hook_name,
            )

        cmd = list(hook_config["cmd"])  # Copy to avoid mutating config
        cwd = hook_config["cwd"]
        blocking = hook_config["blocking"]
        input_mode = hook_config["input_mode"]
        output_format = hook_config["output_format"]

        # Use config timeout if not overridden, default to 60s
        effective_timeout = timeout if timeout is not None else hook_config.get("timeout", 60)

        logger.debug(f"Running hook {repo}/{hook_name} (timeout={effective_timeout}s, blocking={blocking})")

        # Prepare input based on mode
        stdin_data = None
        if input_mode == "stdin" and input_data:
            stdin_data = json.dumps(input_data)
        elif input_mode == "stdin" and input_file:
            stdin_data = input_file.read_text()
        elif input_mode == "args" and cli_args:
            # Append CLI arguments to command
            cmd.extend(cli_args)

        # Run the command with proper process cleanup on timeout
        # D109: Use Popen + proc.kill() instead of subprocess.run() to prevent
        # orphan processes when asyncio.wait_for cancels the thread.
        proc = None
        try:
            def _run_hook():
                nonlocal proc
                proc = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = proc.communicate(input=stdin_data, timeout=effective_timeout)
                return subprocess.CompletedProcess(
                    args=cmd, returncode=proc.returncode,
                    stdout=stdout, stderr=stderr,
                )

            result = await asyncio.wait_for(
                asyncio.to_thread(_run_hook),
                timeout=effective_timeout + 5,  # Grace margin for thread cleanup
            )
        except (asyncio.TimeoutError, subprocess.TimeoutExpired):
            # Kill the process explicitly
            if proc is not None and proc.poll() is None:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            logger.warning(f"Hook {repo}/{hook_name} timed out after {effective_timeout}s")
            return HookResult(
                passed=False,
                blocking=blocking,
                message=f"Hook timed out after {effective_timeout}s",
                issues=[HookIssue(code="TIMEOUT", message=f"Hook execution timed out")],
                hook_name=hook_name,
            )
        except (subprocess.SubprocessError, OSError, IOError) as e:
            logger.error(f"Hook {repo}/{hook_name} execution failed: {e}")
            return HookResult(
                passed=False,
                blocking=blocking,
                message=f"Hook execution failed: {e}",
                issues=[HookIssue(code="EXECUTION_ERROR", message=str(e))],
                hook_name=hook_name,
            )
        except Exception as e:
            # Catch-all for unexpected errors - log with full context
            logger.exception(f"Unexpected error in hook {repo}/{hook_name}")
            return HookResult(
                passed=False,
                blocking=blocking,
                message=f"Hook execution failed: {e}",
                issues=[HookIssue(code="EXECUTION_ERROR", message=str(e))],
                hook_name=hook_name,
            )
        finally:
            # Belt-and-suspenders process cleanup (D109)
            if proc is not None and proc.poll() is None:
                try:
                    proc.kill()
                    proc.wait(timeout=1)
                except Exception:
                    pass

        # Parse output and set hook_name
        if output_format == "json":
            hook_result = self._parse_json_result(result, hook_config)
        else:
            hook_result = self._parse_text_result(result, hook_config)
        hook_result.hook_name = hook_name  # ONE place, can't miss
        return hook_result

    def _parse_json_result(self, result: subprocess.CompletedProcess, config: dict) -> HookResult:
        """Parse JSON output from hook."""
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse hook JSON output: {e}")
            return HookResult(
                passed=False,
                blocking=config["blocking"],
                message="Failed to parse hook output as JSON",
                raw_output=result.stdout,
                exit_code=result.returncode,
                issues=[HookIssue(code="PARSE_ERROR", message="Invalid JSON output")],
            )

        # Handle qc_runner.py format: {"pass": bool, "issues": [{"code": str, "msg": str}, ...]}
        passed = output.get("pass", result.returncode == 0)
        raw_issues = output.get("issues", [])
        block_codes = set(config.get("block_codes", []))

        issues = []
        for issue in raw_issues:
            code = issue.get("code", "UNKNOWN")
            msg = issue.get("msg", "")
            severity = "block" if code in block_codes else "advisory"
            issues.append(HookIssue(code=code, message=msg, severity=severity))

        return HookResult(
            passed=passed,
            blocking=config["blocking"] and not passed,
            issues=issues,
            raw_output=result.stdout,
            exit_code=result.returncode,
            message="QC passed" if passed else f"QC failed with {len([i for i in issues if i.severity == 'block'])} blocking issues",
        )

    def _parse_text_result(self, result: subprocess.CompletedProcess, config: dict) -> HookResult:
        """Parse text output from hook (simple pass/fail based on exit code)."""
        passed = result.returncode == 0

        issues = []
        if not passed:
            issues.append(HookIssue(
                code="VALIDATION_FAILED",
                message=result.stderr or result.stdout or "Validation failed",
                severity="block",
            ))

        return HookResult(
            passed=passed,
            blocking=config["blocking"] and not passed,
            issues=issues,
            raw_output=result.stdout,
            exit_code=result.returncode,
            message="Validation passed" if passed else "Validation failed",
        )


# Convenience function
async def run_hook(repo: str, hook_name: str, **kwargs) -> HookResult:
    """Run a hook using the default runner."""
    runner = HookRunner()
    return await runner.run(repo, hook_name, **kwargs)


# CLI entry point
if __name__ == "__main__":
    import argparse
    import sys

    def print_result(result: HookResult) -> None:
        """Print a single hook result."""
        print(f"Passed: {result.passed}")
        print(f"Blocking: {result.blocking}")
        print(f"Message: {result.message}")
        if result.hook_name:
            print(f"Hook: {result.hook_name}")

        if result.issues:
            print("\nIssues:")
            for issue in result.issues:
                icon = "X" if issue.severity == "block" else "!"
                print(f"  {icon} [{issue.code}] {issue.message}")

    def list_hooks(runner: HookRunner, repo: str, timing_filter: Optional[str] = None) -> None:
        """List hooks for a repository, optionally filtered by timing."""
        repo_hooks = runner.HOOKS.get(repo, {})
        if not repo_hooks:
            print(f"Repository: {repo} (not found)", file=sys.stderr)
            sys.exit(1)

        if timing_filter:
            timing = HookTiming.PRE_EXECUTION if timing_filter == "pre" else HookTiming.POST_EXECUTION
            print(f"Repository: {repo} ({timing.name} only)\n")
            hooks = runner.get_hooks_by_timing(repo, timing)
            print(f"{timing.name}:")
            if hooks:
                for h in hooks:
                    print(f"  - {h}")
            else:
                print("  (none)")
        else:
            print(f"Repository: {repo}\n")
            for timing in HookTiming:
                hooks = runner.get_hooks_by_timing(repo, timing)
                print(f"{timing.name}:")
                if hooks:
                    for h in hooks:
                        print(f"  - {h}")
                else:
                    print("  (none)")
                print()

    async def main():
        parser = argparse.ArgumentParser(
            description="ATLAS Hook Runner",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run a specific hook
  python -m atlas.orchestrator.hooks babybrains qc_runner
  python -m atlas.orchestrator.hooks babybrains qc_runner --input tests/file.json

  # Run all hooks for a timing phase
  python -m atlas.orchestrator.hooks babybrains --timing post
  python -m atlas.orchestrator.hooks babybrains --timing pre

  # List available hooks
  python -m atlas.orchestrator.hooks babybrains --list
  python -m atlas.orchestrator.hooks babybrains --list --timing pre
"""
        )
        parser.add_argument("repo", help="Repository name (babybrains, knowledge, web)")
        parser.add_argument("hook_name", nargs="?", help="Specific hook to run")
        parser.add_argument("--timing", choices=["pre", "post"],
                            help="Run all hooks for timing phase")
        parser.add_argument("--input", dest="input_file",
                            help="Input JSON file")
        parser.add_argument("--list", action="store_true", dest="list_hooks",
                            help="List available hooks")

        args = parser.parse_args()

        # Mutual exclusion checks
        if args.hook_name and args.timing:
            print("Error: Cannot specify both hook_name and --timing", file=sys.stderr)
            sys.exit(1)
        if args.hook_name and args.list_hooks:
            print("Error: Cannot specify both hook_name and --list", file=sys.stderr)
            sys.exit(1)

        runner = HookRunner()

        # Load input data if provided
        input_data = None
        if args.input_file:
            input_path = Path(args.input_file)
            if input_path.exists():
                input_data = json.loads(input_path.read_text())
            else:
                print(f"Error: File not found: {input_path}", file=sys.stderr)
                sys.exit(1)

        # Route to appropriate action
        if args.list_hooks:
            list_hooks(runner, args.repo, args.timing)
            sys.exit(0)

        elif args.timing:
            timing = HookTiming.PRE_EXECUTION if args.timing == "pre" else HookTiming.POST_EXECUTION
            results = await runner.run_all_for_timing(args.repo, timing, input_data=input_data)

            if not results:
                print(f"No {timing.name} hooks found for {args.repo}")
                sys.exit(0)

            all_passed = True
            for result in results:
                print(f"\n--- {result.hook_name} ---")
                print_result(result)
                if not result.passed:
                    all_passed = False

            sys.exit(0 if all_passed else 1)

        elif args.hook_name:
            result = await runner.run(args.repo, args.hook_name, input_data=input_data)
            print_result(result)
            sys.exit(0 if result.passed else 1)

        else:
            parser.print_help()
            sys.exit(1)

    asyncio.run(main())
