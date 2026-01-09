"""
ATLAS Skill Executor

Executes babybrains-os markdown skills via Claude.

Architecture:
    - Skills are markdown prompt specifications, NOT code
    - Skill markdown becomes the system prompt
    - User prompt specifies what to generate
    - Output validates against JSON schema

Two execution modes:
    1. CLI mode (default): Uses `claude --print` via Max subscription ($0)
    2. API mode (--api): Uses Anthropic API directly (for automation)

Usage:
    # CLI mode (default - uses Max subscription)
    executor = SkillExecutor()
    result = await executor.execute("draft_21s", input_data={"domain": "sleep", ...})

    # API mode (for automation)
    executor = SkillExecutor(use_api=True)
    result = await executor.execute("draft_21s", input_data={"domain": "sleep", ...})
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import time

import jsonschema

logger = logging.getLogger(__name__)


# Repo paths - use environment variable with fallback to user's home directory
BABYBRAINS_REPO = Path(
    os.environ.get("BABYBRAINS_REPO", str(Path.home() / "code" / "babybrains-os"))
)
SKILLS_PATH = BABYBRAINS_REPO / "skills"
SCHEMAS_PATH = BABYBRAINS_REPO / "schemas"


@dataclass
class SkillResult:
    """Result of skill execution."""
    success: bool
    output: Optional[dict] = None
    raw_output: str = ""
    error: Optional[str] = None
    skill_name: str = ""
    validation_errors: list[str] = field(default_factory=list)
    tokens_used: int = 0
    duration_ms: float = 0.0


@dataclass
class SkillSection:
    """
    A parsed section from a skill markdown file.

    Attributes:
        name: Section name without ## prefix (e.g., "I/O Schema")
        content: Full content including header line
        line_start: 1-indexed line number where section starts
        line_end: 1-indexed line number where section ends
        level: Heading level (2 for ##, 3 for ###)
    """
    name: str
    content: str
    line_start: int
    line_end: int
    level: int = 2


class SkillLoader:
    """
    Loads skill specifications and schemas from babybrains-os.

    Skills are markdown files in the skills/ directory.
    Schemas are JSON files in the schemas/ directory.

    Supports progressive loading:
        - load_skill(): Full content
        - load_skill_header(): Just header (# Skill + Purpose)
        - list_skill_sections(): Section names and line ranges
        - load_skill_section(): Single section by name
        - load_skill_sections(): Multiple sections by name
        - get_skill_size(): File statistics
    """

    def __init__(self, skills_path: Path = SKILLS_PATH, schemas_path: Path = SCHEMAS_PATH):
        self.skills_path = skills_path
        self.schemas_path = schemas_path

    def _get_skill_path(self, skill_name: str) -> Path:
        """
        Get path to skill file, raising FileNotFoundError if missing.

        Args:
            skill_name: Name of skill (without .md extension)

        Returns:
            Path to skill file

        Raises:
            FileNotFoundError: If skill file doesn't exist
        """
        skill_file = self.skills_path / f"{skill_name}.md"
        if not skill_file.exists():
            logger.warning(f"Skill file not found: {skill_file}")
            raise FileNotFoundError(f"Skill not found: {skill_file}")
        return skill_file

    def load_skill(self, skill_name: str) -> str:
        """Load skill markdown content."""
        skill_file = self._get_skill_path(skill_name)
        logger.debug(f"Loading full skill: {skill_name}")
        content = skill_file.read_text()
        logger.debug(f"Loaded skill '{skill_name}' ({len(content)} chars)")
        return content

    def load_schema(self, skill_name: str) -> Optional[dict]:
        """Load output schema for skill (if exists)."""
        # Try common schema naming patterns
        patterns = [
            f"{skill_name}.out.v1.json",
            f"{skill_name}.out.json",
            f"{skill_name}.schema.json",
        ]

        for pattern in patterns:
            schema_file = self.schemas_path / pattern
            if schema_file.exists():
                logger.debug(f"Loading schema: {schema_file}")
                return json.loads(schema_file.read_text())

        logger.debug(f"No schema found for skill: {skill_name}")
        return None

    def list_skills(self) -> list[str]:
        """List available skills."""
        if not self.skills_path.exists():
            logger.warning(f"Skills path does not exist: {self.skills_path}")
            return []
        skills = [f.stem for f in self.skills_path.glob("*.md")]
        logger.debug(f"Found {len(skills)} skills")
        return skills

    def load_skill_header(self, skill_name: str) -> str:
        """
        Load only the header portion of a skill (# Skill + **Purpose:** lines).

        Header ends at the first ## section or --- separator.

        Args:
            skill_name: Name of skill (without .md extension)

        Returns:
            Header content string

        Raises:
            FileNotFoundError: If skill file doesn't exist
        """
        skill_file = self._get_skill_path(skill_name)
        logger.debug(f"Loading header for skill: {skill_name}")

        content = skill_file.read_text()
        lines = content.split('\n')
        header_lines = []

        for line in lines:
            # Header ends at first section or separator
            if line.startswith('## ') or line.strip() == '---':
                break
            header_lines.append(line)

        header = '\n'.join(header_lines).strip()
        logger.debug(f"Loaded header ({len(header)} chars) for skill: {skill_name}")
        return header

    def _parse_sections(self, content: str) -> list[SkillSection]:
        """
        Parse skill markdown content into sections.

        Section boundaries are determined by ## headers.
        Content between ## markers (including ###) belongs to the preceding ##.

        Args:
            content: Full skill markdown content

        Returns:
            List of SkillSection objects in document order
        """
        lines = content.split('\n')
        sections: list[SkillSection] = []

        current_name: Optional[str] = None
        current_start: Optional[int] = None

        for line_num, line in enumerate(lines, start=1):
            # Only ## (not ###) marks a new section
            if line.startswith('## ') and not line.startswith('### '):
                # Close previous section
                if current_name is not None and current_start is not None:
                    sections.append(SkillSection(
                        name=current_name,
                        content='\n'.join(lines[current_start - 1:line_num - 1]),
                        line_start=current_start,
                        line_end=line_num - 1,
                        level=2,
                    ))

                # Start new section
                current_name = line[3:].strip()
                current_start = line_num

        # Close final section
        if current_name is not None and current_start is not None:
            sections.append(SkillSection(
                name=current_name,
                content='\n'.join(lines[current_start - 1:]),
                line_start=current_start,
                line_end=len(lines),
                level=2,
            ))

        return sections

    def list_skill_sections(self, skill_name: str) -> list[SkillSection]:
        """
        List all sections in a skill with their line ranges.

        Args:
            skill_name: Name of skill (without .md extension)

        Returns:
            List of SkillSection objects (with content populated)

        Raises:
            FileNotFoundError: If skill file doesn't exist
        """
        skill_file = self._get_skill_path(skill_name)
        logger.debug(f"Listing sections for skill: {skill_name}")

        content = skill_file.read_text()
        sections = self._parse_sections(content)

        logger.debug(f"Found {len(sections)} sections in skill: {skill_name}")
        return sections

    def _find_section_by_name(
        self,
        sections: list[SkillSection],
        section_name: str
    ) -> Optional[SkillSection]:
        """
        Find a section by name with partial matching support.

        Matching priority:
        1. Exact match (case-sensitive)
        2. Case-insensitive exact match
        3. Case-insensitive after stripping number prefix (e.g., "3. Voice DNA")
        4. Case-insensitive substring match

        Args:
            sections: List of parsed sections
            section_name: Name to search for

        Returns:
            SkillSection if found, None otherwise
        """
        name_lower = section_name.lower()

        # Priority 1: Exact match
        for section in sections:
            if section.name == section_name:
                return section

        # Priority 2: Case-insensitive exact match
        for section in sections:
            if section.name.lower() == name_lower:
                return section

        # Priority 3: Match after stripping number prefix
        for section in sections:
            section_lower = section.name.lower()
            # Strip number prefix like "3. " from section name
            stripped = re.sub(r'^\d+\.\s*', '', section_lower)
            if stripped == name_lower or stripped.startswith(name_lower):
                return section

        # Priority 4: Substring match
        for section in sections:
            if name_lower in section.name.lower():
                return section

        return None

    def load_skill_section(
        self,
        skill_name: str,
        section_name: str
    ) -> Optional[SkillSection]:
        """
        Load a single section by name.

        Uses fuzzy matching (see _find_section_by_name for priority).

        Args:
            skill_name: Name of skill (without .md extension)
            section_name: Section name to find (partial match supported)

        Returns:
            SkillSection if found, None if not found

        Raises:
            FileNotFoundError: If skill file doesn't exist
        """
        sections = self.list_skill_sections(skill_name)
        section = self._find_section_by_name(sections, section_name)

        if section:
            logger.debug(f"Found section '{section.name}' in skill '{skill_name}'")
        else:
            logger.debug(f"Section '{section_name}' not found in skill '{skill_name}'")

        return section

    def load_skill_sections(
        self,
        skill_name: str,
        section_names: list[str]
    ) -> list[SkillSection]:
        """
        Load multiple sections by name.

        Args:
            skill_name: Name of skill (without .md extension)
            section_names: List of section names to find

        Returns:
            List of found SkillSection objects (in order requested).
            Missing sections are silently skipped (check return length).

        Raises:
            FileNotFoundError: If skill file doesn't exist
        """
        all_sections = self.list_skill_sections(skill_name)
        found: list[SkillSection] = []

        for name in section_names:
            section = self._find_section_by_name(all_sections, name)
            if section:
                found.append(section)
                logger.debug(f"Found section '{section.name}' for query '{name}'")
            else:
                logger.debug(f"Section '{name}' not found in skill '{skill_name}'")

        return found

    def get_skill_size(self, skill_name: str) -> dict:
        """
        Get size statistics for a skill file.

        Args:
            skill_name: Name of skill (without .md extension)

        Returns:
            Dict with keys:
                - bytes: File size in bytes
                - lines: Line count
                - sections: Number of ## sections
                - estimated_tokens: Rough token estimate (chars/4)

        Raises:
            FileNotFoundError: If skill file doesn't exist
        """
        skill_file = self._get_skill_path(skill_name)
        content = skill_file.read_text()

        sections = self._parse_sections(content)
        file_bytes = skill_file.stat().st_size
        line_count = content.count('\n') + 1

        size_info = {
            "bytes": file_bytes,
            "lines": line_count,
            "sections": len(sections),
            "estimated_tokens": len(content) // 4,
        }

        logger.debug(f"Skill '{skill_name}' size: {size_info}")
        return size_info


class SkillExecutor:
    """
    Execute skills via Claude.

    Two modes:
        1. CLI mode (default): Uses `claude --print` via Max subscription ($0)
        2. API mode: Uses Anthropic API directly (for automation)

    Takes skill markdown as system prompt, generates JSON output,
    and validates against schema.
    """

    # Use Haiku for API mode (fast, cheap)
    MODEL = "claude-3-5-haiku-20241022"

    def __init__(
        self,
        loader: Optional[SkillLoader] = None,
        use_api: bool = False,
        model: Optional[str] = None,
    ):
        self.loader = loader or SkillLoader()
        self.use_api = use_api
        self.model = model or self.MODEL
        self._client = None

        # Only initialize API client if using API mode
        if self.use_api:
            self._init_api_client()

    def _init_api_client(self):
        """Initialize Anthropic API client (lazy, only for API mode)."""
        from atlas.llm.api import AnthropicClient

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required for --api mode")

        self._client = AnthropicClient(api_key=api_key, timeout=60.0)

    def _check_cli_available(self) -> bool:
        """Check if claude CLI is available."""
        return shutil.which("claude") is not None

    async def execute(
        self,
        skill_name: str,
        input_data: Optional[dict] = None,
        user_prompt: Optional[str] = None,
        validate: bool = True,
        max_tokens: int = 4096,
        temperature: float = 0.3,  # Lower temp for structured output
    ) -> SkillResult:
        """
        Execute a skill and return structured output.

        Args:
            skill_name: Name of skill (e.g., "draft_21s")
            input_data: Input data to pass to skill (becomes part of user prompt)
            user_prompt: Custom user prompt (overrides default)
            validate: Whether to validate output against schema
            max_tokens: Maximum tokens for output
            temperature: Temperature for generation

        Returns:
            SkillResult with output data or error
        """
        # Load skill markdown
        try:
            skill_markdown = self.loader.load_skill(skill_name)
        except FileNotFoundError as e:
            return SkillResult(
                success=False,
                skill_name=skill_name,
                error=str(e),
            )

        # Load schema for validation
        schema = None
        if validate:
            schema = self.loader.load_schema(skill_name)

        # Build user prompt
        if user_prompt:
            prompt = user_prompt
        elif input_data:
            prompt = self._build_prompt(skill_name, input_data)
        else:
            prompt = self._build_default_prompt(skill_name)

        # Execute via CLI or API
        if self.use_api:
            raw_output, tokens_used, duration_ms, exec_error = await self._execute_api(
                prompt, skill_markdown, max_tokens, temperature
            )
        else:
            raw_output, tokens_used, duration_ms, exec_error = await self._execute_cli(
                prompt, skill_markdown
            )

        if exec_error:
            return SkillResult(
                success=False,
                skill_name=skill_name,
                error=exec_error,
                raw_output=raw_output,
            )

        # Parse JSON from response
        output_data = None
        parse_error = None

        try:
            # Handle markdown code blocks
            json_str = self._extract_json(raw_output)
            output_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            parse_error = f"Invalid JSON: {e}"

        # Validate against schema if available
        validation_errors = []
        if output_data and schema and validate:
            validation_errors = self._validate_schema(output_data, schema)

        # Determine success
        success = output_data is not None and not validation_errors and not parse_error

        return SkillResult(
            success=success,
            output=output_data,
            raw_output=raw_output,
            error=parse_error or (validation_errors[0] if validation_errors else None),
            skill_name=skill_name,
            validation_errors=validation_errors,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )

    async def _execute_cli(
        self,
        prompt: str,
        system_prompt: str,
    ) -> tuple[str, int, float, Optional[str]]:
        """
        Execute via Claude CLI (uses Max subscription - $0).

        Returns: (raw_output, tokens_used, duration_ms, error)
        """
        if not self._check_cli_available():
            return "", 0, 0.0, "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"

        start = time.perf_counter()

        # Build command
        # Use --print for non-interactive, --output-format json for structured output
        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive)
            "--output-format", "text",  # Get raw text output
            "--system-prompt", system_prompt,
            prompt,
        ]

        try:
            # Run CLI command (5 minute timeout for complex skills like transform)
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for complex skills
                ),
                timeout=310,  # Slightly longer async timeout
            )
        except asyncio.TimeoutError:
            return "", 0, 0.0, "CLI execution timed out after 5 minutes"
        except Exception as e:
            return "", 0, 0.0, f"CLI execution failed: {e}"

        duration_ms = (time.perf_counter() - start) * 1000

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"CLI returned exit code {result.returncode}"
            return result.stdout, 0, duration_ms, error_msg

        # CLI doesn't report token counts, estimate from output length
        raw_output = result.stdout.strip()
        tokens_estimate = len(raw_output) // 4  # Rough estimate

        return raw_output, tokens_estimate, duration_ms, None

    async def _execute_api(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int, float, Optional[str]]:
        """
        Execute via Anthropic API directly.

        Returns: (raw_output, tokens_used, duration_ms, error)
        """
        if self._client is None:
            self._init_api_client()

        try:
            response = await self._client.agenerate(
                prompt=prompt,
                system=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except (ConnectionError, TimeoutError, OSError) as e:
            logger.error(f"API connection error: {e}")
            return "", 0, 0.0, f"API connection error: {e}"
        except ValueError as e:
            logger.error(f"API value error: {e}")
            return "", 0, 0.0, f"API value error: {e}"
        except Exception as e:
            # Catch-all for unexpected errors (anthropic SDK errors, etc.)
            logger.exception(f"Unexpected API error")
            return "", 0, 0.0, f"API error: {e}"

        return (
            response.content.strip(),
            response.input_tokens + response.output_tokens,
            response.total_duration_ms,
            None,
        )

    def _build_prompt(self, skill_name: str, input_data: dict) -> str:
        """Build user prompt from input data."""
        # Extract key fields for prompt
        domain = input_data.get("domain", "general")
        age_band = input_data.get("age_band", "12-18m")
        audience = input_data.get("audience", "parents")

        # Format input data as context
        input_json = json.dumps(input_data, indent=2)

        return f"""Execute the {skill_name} skill.

Input:
- Domain: {domain}
- Age band: {age_band}
- Target audience: {audience}

```json
{input_json}
```

IMPORTANT: Respond with ONLY the JSON output. No explanation, no markdown, no commentary. Start your response with {{ and end with }}."""

    def _build_default_prompt(self, skill_name: str) -> str:
        """Build default prompt when no input data provided."""
        return f"""Execute the {skill_name} skill with a demonstration example.

IMPORTANT: Respond with ONLY the JSON output matching the skill's output schema. No explanation, no markdown, no commentary. Start your response with {{ and end with }}."""

    def _extract_json(self, text: str) -> str:
        """Extract JSON from response (handles markdown code blocks)."""
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Try to find raw JSON (starts with { or [)
        for i, char in enumerate(text):
            if char in "{[":
                # Find matching closing bracket
                try:
                    json.loads(text[i:])
                    # If this parses, return the string
                    return text[i:]
                except json.JSONDecodeError:
                    continue

        # Return as-is if no extraction worked
        return text

    def _validate_schema(self, data: dict, schema: dict) -> list[str]:
        """Validate data against JSON schema."""
        errors = []
        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Invalid schema: {e.message}")
        return errors


# Convenience function
async def execute_skill(skill_name: str, **kwargs) -> SkillResult:
    """Execute a skill using the default executor."""
    executor = SkillExecutor()
    return await executor.execute(skill_name, **kwargs)


# CLI entry point
if __name__ == "__main__":
    import argparse
    import sys

    async def main():
        parser = argparse.ArgumentParser(
            description="ATLAS Skill Executor - Execute and inspect babybrains-os skills",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # List all available skills
  python -m atlas.orchestrator.skill_executor --list

  # Execute a skill (CLI mode - default)
  python -m atlas.orchestrator.skill_executor draft_21s

  # Execute with API mode
  python -m atlas.orchestrator.skill_executor draft_21s --api

  # Show skill header only
  python -m atlas.orchestrator.skill_executor draft_21s --header-only

  # List sections in a skill
  python -m atlas.orchestrator.skill_executor draft_21s --list-sections

  # Load specific sections
  python -m atlas.orchestrator.skill_executor draft_21s --sections "Voice DNA,Output"

  # Show skill size statistics
  python -m atlas.orchestrator.skill_executor draft_21s --size
"""
        )

        parser.add_argument("skill_name", nargs="?", help="Name of skill to execute/inspect")

        # Execution options
        parser.add_argument("--input", dest="input_file", help="Input data JSON file")
        parser.add_argument("--api", action="store_true", help="Use Anthropic API instead of CLI")
        parser.add_argument("--no-validate", action="store_true", help="Skip schema validation")

        # Progressive loading options (mutually exclusive with each other)
        inspect_group = parser.add_mutually_exclusive_group()
        inspect_group.add_argument("--list", action="store_true", dest="list_skills",
                                   help="List available skills")
        inspect_group.add_argument("--header-only", action="store_true",
                                   help="Show only skill header")
        inspect_group.add_argument("--list-sections", action="store_true",
                                   help="List sections in skill")
        inspect_group.add_argument("--sections", type=str,
                                   help="Load specific sections (comma-separated)")
        inspect_group.add_argument("--size", action="store_true",
                                   help="Show skill size statistics")

        args = parser.parse_args()

        loader = SkillLoader()

        # Handle --list (no skill_name required)
        if args.list_skills:
            print("Available skills:")
            for skill in loader.list_skills():
                print(f"  - {skill}")
            sys.exit(0)

        # All other options require skill_name
        if not args.skill_name:
            parser.print_help()
            sys.exit(1)

        skill_name = args.skill_name

        try:
            # Progressive loading options
            if args.header_only:
                header = loader.load_skill_header(skill_name)
                print(header)
                sys.exit(0)

            elif args.list_sections:
                sections = loader.list_skill_sections(skill_name)
                print(f"Sections in '{skill_name}' ({len(sections)} total):\n")
                for section in sections:
                    print(f"  {section.line_start:3d}-{section.line_end:3d}  ## {section.name}")
                sys.exit(0)

            elif args.sections:
                section_names = [s.strip() for s in args.sections.split(",")]
                sections = loader.load_skill_sections(skill_name, section_names)

                if not sections:
                    print(f"No sections found matching: {section_names}", file=sys.stderr)
                    all_sections = loader.list_skill_sections(skill_name)
                    print(f"Available sections: {[s.name for s in all_sections]}", file=sys.stderr)
                    sys.exit(1)

                for section in sections:
                    print(f"\n{'='*60}")
                    print(f"## {section.name} (lines {section.line_start}-{section.line_end})")
                    print(f"{'='*60}\n")
                    print(section.content)
                sys.exit(0)

            elif args.size:
                size_info = loader.get_skill_size(skill_name)
                print(f"Skill: {skill_name}")
                print(f"  Bytes: {size_info['bytes']:,}")
                print(f"  Lines: {size_info['lines']:,}")
                print(f"  Sections: {size_info['sections']}")
                print(f"  Est. Tokens: ~{size_info['estimated_tokens']:,}")
                sys.exit(0)

        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("\nAvailable skills:", file=sys.stderr)
            for skill in loader.list_skills():
                print(f"  - {skill}", file=sys.stderr)
            sys.exit(1)

        # Default: Execute skill
        # Parse optional input file
        input_data = None
        if args.input_file:
            input_file = Path(args.input_file)
            if input_file.exists():
                try:
                    input_data = json.loads(input_file.read_text())
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Error: Input file not found: {input_file}", file=sys.stderr)
                sys.exit(1)

        # Show mode
        mode = "API" if args.api else "CLI (Max subscription)"
        print(f"Mode: {mode}", file=sys.stderr)

        # Execute skill
        try:
            executor = SkillExecutor(use_api=args.api)
            result = await executor.execute(
                skill_name,
                input_data=input_data,
                validate=not args.no_validate
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Output result
        if result.success:
            print(json.dumps(result.output, indent=2))
        else:
            print(f"Skill execution failed: {result.error}", file=sys.stderr)
            if result.validation_errors:
                print("\nValidation errors:", file=sys.stderr)
                for err in result.validation_errors:
                    print(f"  - {err}", file=sys.stderr)
            if result.raw_output:
                print(f"\nRaw output (truncated):\n{result.raw_output[:500]}...", file=sys.stderr)
            sys.exit(1)

        # Show stats
        print(f"\n--- Stats ---", file=sys.stderr)
        print(f"Tokens: ~{result.tokens_used}", file=sys.stderr)
        print(f"Duration: {result.duration_ms:.0f}ms", file=sys.stderr)
        if not args.api:
            print(f"Cost: $0 (Max subscription)", file=sys.stderr)

    asyncio.run(main())
