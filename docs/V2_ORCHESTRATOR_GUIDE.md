# ATLAS V2 Orchestrator Guide

> **Purpose:** This document explains ATLAS's orchestration capabilities so that ATLAS (or any agent) can understand and use them effectively.
> **Last Updated:** January 10, 2026

---

## Reference Documentation

**Read these for deeper understanding of WHY these capabilities exist:**

### Masterclass Source Material
The V2 architecture is based on the Claude Agent SDK Masterclass by Tariq (Anthropic). The key insights are documented in:

| Document | Content | Read When |
|----------|---------|-----------|
| `docs/research/R30.Claude Agent SDK Masterclass Analysis.md` | **10 key insights**, executive summary, timestamps | Start here for the "why" |
| `docs/research/R30_Section1_Philosophy.md` | Agent definition, loops, bash philosophy | Understanding agent patterns |
| `docs/research/R30_Section2_Implementation.md` | Skills, sub-agents, hooks, state management | Implementing new features |
| `docs/research/R30_Section3_Advanced.md` | Q&A, verification patterns, production tips | Advanced patterns |

### Key Masterclass Quotes (with timestamps)

> **[194s]** "Agents build their own context, decide their own trajectories, are working very very autonomously."

> **[2001s]** Skills = Progressive Disclosure - "Agent discovers capabilities by reading skill files on demand."

> **[4147s]** Sub-Agents - "Avoid context pollution. Start a new context session" for complex sub-tasks.

> **[4575s]** Context Management - Store state externally (git diff, files), clear context between tasks.

> **[4928s]** Verification - "Verification can happen anywhere and should happen anywhere."

> **[6596s]** Hooks - Use deterministic hooks to enforce behavior and fight hallucinations.

### Raw Transcript
The full masterclass transcript (127KB) is available for searching specific topics:
```
/home/squiz/ATLAS/masterclass_transcript.txt
```
Use `grep` to find specific discussions (e.g., `grep -i "verification" masterclass_transcript.txt`).

### Architecture & Decisions
| Document | Content |
|----------|---------|
| `docs/ATLAS_ARCHITECTURE_V2.md` | Design specs for each V2 component |
| `docs/DECISIONS.md` | Why each decision was made (D1-D35) |
| `docs/TECHNICAL_STATUS.md` | Current implementation status |

---

## Quick Reference

| Component | File | Purpose |
|-----------|------|---------|
| SubAgentExecutor | `atlas/orchestrator/subagent_executor.py` | Spawn parallel sub-agents with isolated context |
| HookRunner | `atlas/orchestrator/hooks.py` | Run validators before/after skill execution |
| SessionManager | `atlas/orchestrator/session_manager.py` | Track session state and git changes |
| SkillLoader | `atlas/orchestrator/skill_executor.py` | Load skills or specific sections on demand |
| ScratchPad | `atlas/orchestrator/scratch_pad.py` | Track intermediate results during skill chains |
| Quality Audit Pipeline | `atlas/pipelines/activity_conversion.py` | 7-stage pipeline with Grade A enforcement |
| CodeSimplifier | `atlas/simplifier/code_simplifier.py` | On-demand code quality analysis and learning |
| Voice API Pipeline | `atlas/voice/bridge_file_server.py` | Token-efficient voice-first health queries |
| InteractiveWorkoutTimer | `atlas/voice/bridge_file_server.py` | Voice-controlled user-paced workout execution |
| MorningSyncService | `atlas/health/morning_sync.py` | Cached status + voice formatting |

---

## 1. SubAgentExecutor

### What It Does
Spawns sub-agents (via `claude -p` CLI) with fresh, isolated context. Enables parallel execution and adversarial verification.

### When To Use
- Running multiple independent tasks simultaneously
- Needing a "second opinion" on generated content
- Isolating context to prevent cross-contamination

### Usage

```python
from atlas.orchestrator.subagent_executor import SubAgentExecutor

executor = SubAgentExecutor(timeout=120)  # 2 minute default

# Single task
result = await executor.spawn(
    task="Summarize this code and identify potential bugs",
    context={"file": "auth.py", "focus": "security"},  # Optional context
    timeout=60  # Override timeout
)
print(result.output)  # The sub-agent's response
print(result.success)  # True/False

# Parallel tasks (runs simultaneously)
results = await executor.spawn_parallel([
    "Review error handling in auth module",
    "Check for SQL injection vulnerabilities",
    "Verify input validation coverage"
])
for r in results:
    print(f"{r.task[:30]}... -> {r.success}")

# Adversarial verification (fresh agent double-checks work)
verification = await executor.verify_adversarially(
    output={"draft": "Your generated content here..."},
    skill_name="draft_21s",
    persona="junior analyst at McKinsey"  # Default persona
)
if not verification.passed:
    print(f"Issues found: {verification.issues}")
```

### CLI Testing
```bash
python -m atlas.orchestrator.subagent_executor --test
```

### Stdin-Based Execution (D24)
Prompts are passed via stdin to avoid Linux ARG_MAX limits (~128-256KB). This is critical when prompts include large context (voice standards, rubrics).

```python
# Implementation detail (handled automatically):
# - spawn() passes prompt via subprocess input= parameter
# - verify_adversarially() uses same pattern
# - Large system prompts (>100KB) use temp file fallback
```

### How To Extend
To add new verification personas, modify `verify_adversarially()` in `subagent_executor.py:380`.

---

## 2. HookRunner (Validators)

### What It Does
Wraps existing validation scripts as hooks that run at specific timing points (PRE or POST execution).

### When To Use
- Validating skill inputs before execution
- Running QC checks after content generation
- Enforcing quality gates automatically

### Currently Configured Hooks

| Repo | Hook | Timing | Blocking | Purpose |
|------|------|--------|----------|---------|
| babybrains | qc_runner | POST | Yes | Video script QC |
| knowledge | tier1_validators | POST | Yes | Schema validation |
| knowledge | activity_qc | POST | Yes | Activity Atom voice/structure QC |
| web | pre_pr | POST | Yes | Pre-PR checks |

### Usage

```python
from atlas.orchestrator.hooks import HookRunner, HookTiming

runner = HookRunner()

# List available hooks for a repo
hooks = runner.get_available_hooks("babybrains")  # ['qc_runner']

# Run a specific hook
result = await runner.run(
    repo="babybrains",
    hook_name="qc_runner",
    input_data={"format": "s21", "content": "..."},
    timeout=60
)

if result.passed:
    print("QC passed!")
else:
    print(f"Blocked: {result.blocking}")
    for issue in result.issues:
        print(f"  [{issue.code}] {issue.message}")

# Run all POST hooks for a repo
results = await runner.run_all_for_timing(
    repo="babybrains",
    timing=HookTiming.POST_EXECUTION,
    stop_on_block=True  # Stop at first failure
)
```

### CLI Testing
```bash
# List hooks
python -m atlas.orchestrator.hooks babybrains --list

# Run by timing
python -m atlas.orchestrator.hooks babybrains --timing post

# Run specific hook with input
python -m atlas.orchestrator.hooks babybrains qc_runner --input data.json
```

### Activity QC Hook (knowledge repo)

The `activity_qc` hook validates Activity Atoms for:
- **Voice violations:** Em-dashes, en-dashes, formal transitions, superlatives
- **Structure completeness:** 34 required YAML sections
- **Cross-references:** Valid principle slugs (18 total)

```bash
# Test activity against QC hook
cat activity.yaml | python3 /home/squiz/code/knowledge/scripts/check_activity_quality.py

# Output format (hooks.py compatible):
{
  "pass": true,
  "issues": [{"code": "VOICE_EM_DASH", "severity": "block", "msg": "...", "line": 45}],
  "warnings": [{"code": "WARN_AGE_EXTREME", "severity": "advisory", "msg": "..."}],
  "stats": {"em_dash_count": 0, "superlative_count": 0, "sections_found": 34}
}
```

**Block codes:** `VOICE_EM_DASH`, `VOICE_FORMAL_TRANSITION`, `VOICE_SUPERLATIVE`, `STRUCTURE_MISSING_SECTION`, `STRUCTURE_INVALID_YAML`, `CROSS_REF_INVALID_PRINCIPLE`

### How To Add New Hooks
Edit the `HOOKS` dict in `hooks.py:83`:

```python
HOOKS = {
    "babybrains": {
        "new_validator": {
            "cmd": ["python", "scripts/validate_something.py"],
            "cwd": "/home/squiz/code/babybrains-os",
            "blocking": True,  # True = blocks on failure
            "input_mode": "stdin",  # "stdin" or "none"
            "output_format": "json",  # "json" or "text"
            "timing": HookTiming.PRE_EXECUTION,  # or POST_EXECUTION
        },
    },
}
```

---

## 3. SessionManager

### What It Does
Tracks session state across interactions. Persists to `~/.atlas/sessions/`. Captures git context for resumption.

### When To Use
- Starting a work session on a specific repo
- Tracking which skills have been executed
- Storing scratch notes that persist
- Getting git diff context for resumption after context clearing

### Usage

```python
from atlas.orchestrator.session_manager import SessionManager, get_session_manager

mgr = SessionManager()

# Start a session
session_id = mgr.start_session(repo="babybrains")  # Returns: "babybrains_20260108_143022"

# Track skill execution
mgr.record_skill("ingest")
mgr.record_skill("plan")
mgr.record_skill("draft_21s")

# Store scratch data
mgr.add_to_scratch("current_domain", "sleep")
mgr.add_to_scratch("target_age", "12-18m")

# Retrieve scratch data
domain = mgr.get_from_scratch("current_domain")

# Get git context (what files changed)
git_ctx = mgr.get_git_context(repo_path=Path("/home/squiz/code/babybrains-os"))
print(f"Modified: {git_ctx.files_modified}")
print(f"Added: {git_ctx.files_added}")
print(f"Clean: {git_ctx.is_clean}")

# Get context for resumption after clearing
resume_data = mgr.clear_and_resume()
# Returns: {session_state, git_context, resume_prompt}

# Save state (auto-saves on changes, but can force)
mgr.save_state()

# End session
mgr.end_session()

# List past sessions
sessions = mgr.list_sessions(repo="babybrains")

# Load a previous session
mgr.load_session("babybrains_20260108_143022")
```

### CLI Testing
```bash
# Start session
python -m atlas.orchestrator.session_manager --start --repo babybrains

# Get git context
python -m atlas.orchestrator.session_manager --git-context --path /home/squiz/code/babybrains-os

# List sessions
python -m atlas.orchestrator.session_manager --list --repo babybrains

# Resume session
python -m atlas.orchestrator.session_manager --resume babybrains_20260108_143022

# Cleanup old sessions
python -m atlas.orchestrator.session_manager --cleanup --days 7
```

### Session File Location
Sessions are stored as JSON at: `~/.atlas/sessions/{session_id}.json`

---

## 4. Progressive Loading (SkillLoader)

### What It Does
Loads skill markdown files efficiently - either full content, just the header, or specific sections.

### When To Use
- Loading only the sections needed for a task (saves context tokens)
- Checking what a skill contains before loading
- Getting size estimates for context budgeting

### Skill Structure
Skills are markdown files with `## ` headers defining sections:
```markdown
# Skill: draft_21s
**Purpose:** Generate a 21-second script...

---

## I/O Schema
[content]

## 3. Voice DNA Requirements
[content]

## 10. Output Structure
[content]
```

### Usage

```python
from atlas.orchestrator.skill_executor import SkillLoader, SkillExecutor

loader = SkillLoader()

# List available skills
skills = loader.list_skills()  # ['draft_21s', 'draft_60s', 'ingest', ...]

# Load full skill (original behavior)
full_content = loader.load_skill("draft_21s")

# Load just the header (before first ## section)
header = loader.load_skill_header("draft_21s")

# List sections without loading content
sections = loader.list_skill_sections("draft_21s")
for s in sections:
    print(f"{s.name} (lines {s.line_start}-{s.line_end})")

# Load specific section (partial match works!)
section = loader.load_skill_section("draft_21s", "Voice DNA")
# Matches: "## 3. Voice DNA Requirements"
print(section.content)

# Load multiple sections
sections = loader.load_skill_sections("draft_21s", ["Voice DNA", "Output Structure"])

# Get size info
size = loader.get_skill_size("draft_21s")
# Returns: {"bytes": 8404, "lines": 349, "sections": 12, "estimated_tokens": 2101}
```

### Partial Matching
Section names match with this priority:
1. Exact match
2. Case-insensitive exact
3. Number prefix stripped (e.g., "Voice DNA" matches "3. Voice DNA Requirements")
4. Substring match

### CLI Testing
```bash
# List skills
python -m atlas.orchestrator.skill_executor --list

# List sections
python -m atlas.orchestrator.skill_executor draft_21s --list-sections

# Get header only
python -m atlas.orchestrator.skill_executor draft_21s --header-only

# Get specific sections
python -m atlas.orchestrator.skill_executor draft_21s --sections "Voice DNA,Output Structure"

# Get size info
python -m atlas.orchestrator.skill_executor draft_21s --size
```

### Skill File Locations
Skills: `/home/squiz/code/babybrains-os/skills/*.md`
Schemas: `/home/squiz/code/babybrains-os/schemas/*.json`

---

## 5. ScratchPad

### What It Does
Tracks intermediate results during multi-step skill chains. Each entry has a key, value, step number, timestamp, and optional skill name.

### When To Use
- Running skill chains (ingest → plan → draft → qc)
- Needing to recover if a step fails
- Debugging what each step produced
- Generating summaries for context reload

### Usage

```python
from atlas.orchestrator.scratch_pad import ScratchPad
from pathlib import Path

pad = ScratchPad(session_id="content_session_001")

# Add entries (step auto-increments if not provided)
pad.add("ingest_output", {"domain": "sleep", "age": "12-18m"}, step=1, skill_name="ingest")
pad.add("plan_result", {"segments": [1, 2, 3, 4]}, step=2, skill_name="plan")
pad.add("draft_output", {"text": "...", "word_count": 62}, step=3, skill_name="draft_21s")

# Retrieve values
ingest = pad.get("ingest_output")
latest = pad.get_latest(n=3)

# Query by step or skill
step2_entries = pad.get_by_step(2)
plan_entries = pad.get_by_skill("plan")

# Get human-readable summary
print(pad.get_summary())
# Output:
# ScratchPad: content_session_001 (3 entries, 3 steps)
# Step 1 (ingest):
#   - ingest_output: {"domain": "sleep", "age": "12-18m"}
# Step 2 (plan):
#   - plan_result: {"segments": [1, 2, 3, 4]}
# ...

# Get minimal context dict for LLM injection
ctx = pad.get_context_dict()

# Persist to file
pad.to_file(Path("~/.atlas/scratch/session.json"))

# Load from file
loaded = ScratchPad.from_file(Path("~/.atlas/scratch/session.json"))

# Clear entries
pad.clear()  # All entries
pad.clear_before_step(3)  # Keep step 3+, clear 1-2
```

### CLI Testing
```bash
# Add entry
python -m atlas.orchestrator.scratch_pad --session test --add key=value --step 1

# View summary
python -m atlas.orchestrator.scratch_pad --session test --summary

# View as JSON
python -m atlas.orchestrator.scratch_pad --session test --json

# Clear
python -m atlas.orchestrator.scratch_pad --session test --clear

# Load from file
python -m atlas.orchestrator.scratch_pad --load /path/to/scratch.json --summary
```

---

## Complete Workflow Example

Here's how all components work together for a content generation task:

```python
import asyncio
from pathlib import Path
from atlas.orchestrator.session_manager import SessionManager
from atlas.orchestrator.skill_executor import SkillLoader, SkillExecutor
from atlas.orchestrator.scratch_pad import ScratchPad
from atlas.orchestrator.hooks import HookRunner, HookTiming
from atlas.orchestrator.subagent_executor import SubAgentExecutor

async def generate_content(domain: str, age_band: str):
    # 1. Start session
    session = SessionManager()
    session_id = session.start_session(repo="babybrains")

    # 2. Initialize scratch pad
    pad = ScratchPad(session_id)

    # 3. Load only the sections we need
    loader = SkillLoader()
    voice_section = loader.load_skill_section("draft_21s", "Voice DNA")
    output_section = loader.load_skill_section("draft_21s", "Output Structure")

    # 4. Execute skill
    executor = SkillExecutor()
    result = await executor.execute(
        "draft_21s",
        input_data={"domain": domain, "age_band": age_band}
    )

    # 5. Track result
    pad.add("draft_output", result.output, step=1, skill_name="draft_21s")
    session.record_skill("draft_21s")

    # 6. Run QC hook
    hooks = HookRunner()
    qc_result = await hooks.run("babybrains", "qc_runner", input_data=result.output)

    if not qc_result.passed:
        pad.add("qc_failure", qc_result.issues, step=2, skill_name="qc")
        return {"success": False, "issues": qc_result.issues}

    # 7. Adversarial verification
    sub = SubAgentExecutor()
    verification = await sub.verify_adversarially(
        output=result.output,
        skill_name="draft_21s"
    )

    if not verification.passed:
        pad.add("verification_issues", verification.issues, step=3)
        # Could retry or flag for review

    # 8. Save everything
    pad.to_file(Path.home() / ".atlas" / "scratch" / f"{session_id}.json")
    session.save_state()

    return {"success": True, "output": result.output, "session_id": session_id}

# Run it
result = asyncio.run(generate_content("sleep", "12-18m"))
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `BABYBRAINS_REPO` | `~/code/babybrains-os` | Path to babybrains-os repo |
| `ANTHROPIC_API_KEY` | (none) | Optional - only for API mode. Activity Pipeline uses CLI mode (Max subscription) |

---

## File Locations

| What | Where |
|------|-------|
| Orchestrator code | `/home/squiz/ATLAS/atlas/orchestrator/` |
| Sessions | `~/.atlas/sessions/*.json` |
| Scratch pads | `~/.atlas/scratch/*.json` |
| Skills | `/home/squiz/code/babybrains-os/skills/*.md` |
| Schemas | `/home/squiz/code/babybrains-os/schemas/*.json` |

---

## Adding New Capabilities

### Adding a New Hook
1. Edit `atlas/orchestrator/hooks.py`
2. Add entry to `HOOKS` dict with cmd, cwd, blocking, input_mode, output_format, timing
3. Test with `python -m atlas.orchestrator.hooks <repo> <hook_name>`

### Adding a New Skill
1. Create `skills/<skill_name>.md` in babybrains-os
2. Follow structure: `# Skill:` header, `## ` sections
3. Optionally create `schemas/<skill_name>.out.v1.json` for validation
4. Test with `python -m atlas.orchestrator.skill_executor <skill_name> --list-sections`

### Extending SubAgentExecutor
- New verification personas: modify `verify_adversarially()` method
- New spawn options: add parameters to `spawn()` method
- Parallel execution limits: modify `spawn_parallel()` batching

---

## Troubleshooting

### SubAgent not responding
- Check `claude` CLI is installed: `which claude`
- Check timeout isn't too short (default 120s)

### Hooks failing
- Run hook directly: `python /path/to/validator.py`
- Check cwd path exists
- Check input_mode matches what script expects

### Session not persisting
- Check `~/.atlas/sessions/` directory exists
- Check file permissions
- Call `save_state()` explicitly if needed

### Skill section not found
- Use `--list-sections` to see exact names
- Partial matching is case-insensitive
- Check for typos in section name

### ARG_MAX error (D24)
**Symptom:** `[Errno 7] Argument list too long: 'claude'`

**Cause:** Prompt + system prompt exceeds Linux ARG_MAX (~128-256KB)

**Solution:** Already fixed in `skill_executor.py` and `subagent_executor.py` (Jan 10, 2026):
- Prompts pass via stdin (`input=` parameter)
- Large system prompts (>100KB) use temp file with `@` prefix

---

## 6. Confidence Router (January 2026)

### What It Does
Routes responses based on verbalized confidence levels. Implements research findings from Anthropic's introspection paper.

### Key Insight: Confidence Inversion
High confidence in safety-critical domains triggers MORE verification, not less. This catches systematic hallucinations where the model incorrectly activates "known entity" signals.

### Usage

```python
from atlas.orchestrator.confidence_router import (
    route_by_confidence,
    apply_wait_pattern,
    ConfidenceLevel,
    VerificationAction,
)

# Basic routing
result = route_by_confidence(response_text)
print(result.score)   # 0.0-1.0
print(result.level)   # HIGH, MEDIUM, LOW
print(result.action)  # PROCEED, VERIFY_EXTERNAL, VERIFY_ADVERSARIAL, REGENERATE

# With safety-critical domain (triggers confidence inversion)
result = route_by_confidence(response_text, domain="health")
# High confidence + health domain → VERIFY_ADVERSARIAL (not PROCEED)

# The "Wait" pattern for self-correction (89.3% blind spot reduction)
correction_prompt = apply_wait_pattern(original_response, query)
```

### Confidence Levels and Actions

| Level | Score | Default Action | Safety-Critical Action |
|-------|-------|----------------|------------------------|
| HIGH | > 0.8 | PROCEED | VERIFY_ADVERSARIAL |
| MEDIUM | 0.5-0.8 | VERIFY_EXTERNAL | VERIFY_EXTERNAL |
| LOW | < 0.5 | REGENERATE | REGENERATE |

### Safety-Critical Domains
These domains always require external verification:
- health, medical, supplements, exercise
- safety, financial, legal

### CLI Testing
```bash
python -m atlas.orchestrator.confidence_router "I am confident this is correct"
python -m atlas.orchestrator.confidence_router "I think this might work"
```

---

## 7. Sandboxing (January 2026)

### What It Does
OS-level security isolation for sub-agents and hooks. Prevents prompt injection attacks from accessing sensitive files or exfiltrating data.

### Why It Matters
Sub-agents spawned via `claude -p` have full system access. A prompt injection attack could:
- Read `~/.ssh/id_rsa` and exfiltrate via network
- Modify `~/.bashrc` to persist malware
- Access credentials in `.env` files

### Sandbox Configs

| Config | File | Use For |
|--------|------|---------|
| SubAgent | `config/sandbox/subagent.json` | SubAgentExecutor spawns |
| Hook | `config/sandbox/hook.json` | HookRunner validators |

### SubAgent Config (`config/sandbox/subagent.json`)
```json
{
  "network": {
    "allowedDomains": ["api.anthropic.com"]
  },
  "filesystem": {
    "denyRead": ["~/.ssh", "~/.aws", "~/.gnupg"],
    "allowWrite": ["/home/squiz/ATLAS", "/home/squiz/code"],
    "denyWrite": [".env*", "*.key", "*.pem"]
  }
}
```

### Hook Config (`config/sandbox/hook.json`)
```json
{
  "network": {
    "allowedDomains": []  // Hooks run offline
  },
  "filesystem": {
    "denyRead": ["~/.ssh", "~/.aws"],
    "allowWrite": ["/home/squiz/code"]
  }
}
```

### Usage (when integrated)
```bash
# Manual sandboxed execution
srt --settings config/sandbox/subagent.json claude -p "your prompt"

# In SubAgentExecutor (future integration)
cmd = ["srt", "--settings", sandbox_config] + base_cmd
```

### Requirements
- `npm install -g @anthropic-ai/sandbox-runtime`
- Linux (bubblewrap) or macOS (seatbelt)
- WSL2 works (uses Linux sandboxing)

---

## 8. Session Handoff (January 2026)

### What It Does
Manages context transitions between sessions via structured files.

### Files

| File | Format | Purpose |
|------|--------|---------|
| `.claude/handoff.md` | Markdown | Human-readable session notes |
| `.claude/atlas-progress.json` | JSON | Machine-readable task tracking |

### Why JSON for Progress
Research finding: Models are less likely to inappropriately modify JSON than Markdown. Use JSON for task status that needs to persist accurately.

### Handoff Protocol

**At Session Start:**
1. Read `.claude/handoff.md` for context
2. Read `.claude/atlas-progress.json` for task status
3. Update "Last Session Summary" if continuing work

**At Session End:**
1. Update `handoff.md` with completed work and pending tasks
2. Update `atlas-progress.json` task statuses
3. Note any key decisions or blockers

### Example Workflow
```python
import json
from pathlib import Path

# Read progress
progress = json.load(open('.claude/atlas-progress.json'))
pending = [t for t in progress['pending_tasks'] if t['status'] == 'pending']

# Work on first pending task
task = pending[0]
task['status'] = 'in_progress'

# Save progress
with open('.claude/atlas-progress.json', 'w') as f:
    json.dump(progress, f, indent=2)
```

---

## 9. Quality Audit Pipeline (January 2026)

### What It Does
Ensures only Grade A content reaches human review by adding a quality audit stage after QC hook. Implements intelligent retry using the "Wait" pattern when grades are below A.

### Key Features
- **CLI Mode**: Uses Max subscription (`claude` CLI), no API key needed
- **Grade A Gate**: Only A/A+/A- grades proceed to human review
- **Intelligent Retry**: "Wait" pattern reflection between attempts (89.3% blind spot reduction)
- **Voice Rubric**: Grades against BabyBrains voice standards
- **Stage Caching (D79)**: Retries skip stages 1-3, only re-run 4-7 (60-70% faster)
- **Early Truncation Detection (D79)**: Detects incomplete YAML before expensive QC/AUDIT

### Performance Optimizations (D79)

**Stage Caching**: On first attempt, full 7-stage pipeline runs and caches transform output (`canonical_yaml`, `canonical_id`, `file_path`). On retry, stages 1-3 (INGEST/RESEARCH/TRANSFORM) are skipped because feedback only affects ELEVATE. Uses `_convert_from_cached_transform()` method.

**Early Truncation Detection**: All canonical Activity Atoms end with `parent_search_terms:` list. The `_detect_truncation()` method checks for this pattern after ELEVATE but before QC_HOOK and QUALITY_AUDIT. Truncated output returns `QC_FAILED` immediately, saving 5-10 minutes of unnecessary processing.

| Metric | Before D79 | After D79 | Improvement |
|--------|------------|-----------|-------------|
| Retry time (stages 1-3) | ~3-5 min | 0 min | 100% skipped |
| Total retry time | ~15-21 min | ~5-7 min | 60-70% faster |
| Truncation detection | After AUDIT | After ELEVATE | 2-4 min earlier |

### Pipeline Flow
```
RAW ACTIVITY
     │
     ▼
┌─────────────────────┐
│ 1. INGEST           │
│ 2. RESEARCH         │
│ 3. TRANSFORM        │  7-stage pipeline
│ 4. ELEVATE          │  (with feedback on retry)
│ 5. VALIDATE         │
│ 6. QC HOOK          │
│ 7. QUALITY AUDIT    │
└─────────┬───────────┘
          │
          │ Grade A? ──NO──► Reflect → Retry
          │
          ▼ YES
┌─────────────────────┐
│ HUMAN REVIEW        │ Only sees Grade A content
└─────────────────────┘
```

### Usage

```python
from atlas.pipelines.activity_conversion import ActivityConversionPipeline

# Initialize (no API key needed - uses CLI mode)
pipeline = ActivityConversionPipeline()

# Convert single activity with intelligent retry
result = await pipeline.convert_with_retry("tummy-time", max_retries=2)

# Check result
if result.status == ActivityStatus.DONE:
    print(f"Grade A achieved: {result.canonical_id}")
else:
    print(f"Failed: {result.error}")
    for issue in result.qc_warnings:
        print(f"  - {issue}")
```

### CLI Commands

```bash
# Verify deduplication before batch processing (D37)
python -m atlas.pipelines.activity_conversion --verify

# Primary mode: single activity with quality audit
python -m atlas.pipelines.activity_conversion --activity tummy-time

# With explicit retry count
python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 3

# List pending activities
python -m atlas.pipelines.activity_conversion --list-pending

# Batch mode (use only after skills reliably produce Grade A)
python -m atlas.pipelines.activity_conversion --batch --limit 10
```

### Deduplication Verification (D37)

The `--verify` command provides visibility into activity deduplication before processing:

```
============================================================
ACTIVITY DEDUPLICATION REPORT
============================================================

Raw activities loaded:        234
Explicit duplicates (skip):   7
Grouped activities:           75 → 22 atoms
Standalone activities:        152
----------------------------------------
Expected canonical atoms:     174

Groups:
  visual-mobiles-progression: 5 sources → 1 atom
  breastfeeding-support: 6 sources → 1 atom
  ...

✓ All conversion map references validated
```

**Key features:**
- Detects duplicate IDs in raw YAML (warns, keeps first)
- Validates all conversion map references exist
- Shows group→atom consolidation math
- Exits with code 1 if validation issues found

### How Intelligent Retry Works

When quality audit returns a non-A grade:

1. **Reflect**: `reflect_on_failure()` applies the "Wait" pattern:
   ```
   Wait. Before re-elevating, pause and consider:
   - What assumptions did the previous attempt make?
   - Why did these specific issues occur?
   - What would I tell another agent who made these mistakes?
   ```

2. **Feedback**: Reflection generates specific guidance for fixes

3. **Retry**: `convert_activity()` receives feedback, passes to elevate skill

4. **Learn**: Each retry learns from what went wrong, not just hopes for different output

### Grade Scale

| Grade | Result | Meaning |
|-------|--------|---------|
| A/A+/A- | PASS | Ready for human review |
| B+ | FAIL | 1-2 fixable issues, retry triggered |
| B | FAIL | Multiple issues, retry triggered |
| C | FAIL | Significant issues, retry triggered |
| F | FAIL | Major problems or audit failure |

### Key Files

| File | Purpose |
|------|---------|
| `atlas/pipelines/activity_conversion.py` | Pipeline orchestrator |
| `audit_quality()` method | Grades against Voice Rubric |
| `reflect_on_failure()` method | Wait pattern reflection |
| `convert_with_retry()` method | Intelligent retry loop |
| `_fix_canonical_slug()` method | Deterministic slug derivation (D25) |
| `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` | Grading criteria |
| `/home/squiz/code/babybrains-os/skills/activity/elevate_voice_activity.md` | ELEVATE skill with zero-tolerance rules (D26) |

### External Dependencies

The quality audit requires these files to exist:
- **Voice Rubric** (required): `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md`
- **Reference A+ Activity** (optional): `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml`

If rubric is missing, audit returns Grade F with system error.

### Pipeline Fixes (January 10, 2026)

**D24: Stdin-Based CLI Execution**
- All CLI executions pass prompt via stdin (no size limit)
- Avoids ARG_MAX error when voice standard (~95KB) + rubric (~12KB) + YAML combined

**D25: Deterministic canonical_slug**
- Post-processes LLM output with `_fix_canonical_slug()`
- Formula: `canonical_slug = canonical_id.lower().replace('_', '-')`
- Robust to LLM format variations

**D26: Zero-Tolerance Superlatives**
- ELEVATE skill has CRITICAL section at top (lines 7-24)
- Superlatives escalated from MODERATE to SEVERE
- Validation rule 3 changed from WARN to BLOCK
- Philosophy section has counter-balance warning

**D32: Zero-Tolerance Pressure Language**
- Added pressure language to CRITICAL section (line 15)
- Psychological intervention: "If you feel the urge to write 'You need to'..."
- Permission-giving alternatives from Grade A benchmarks
- BLOCK validation rule 4 for pressure language
- Grade A criteria updated to require "zero pressure language"

**D33: Robust JSON Parsing**
- `_extract_audit_json()` method with truncation detection
- Automatic repair for unbalanced braces/brackets
- Extended timeout for final retry (10 min vs 5 min)
- Full raw response logging on failure

**D34: Sandbox Disabled**
- `sandbox=False` for audit_quality() and reflect_on_failure()
- Prevents EROFS errors with claude CLI config writes
- No security benefit for trusted local file operations

**D35: Context-Aware QC Exceptions**
- Added "focus best", developmental verb + best patterns
- Added negation patterns for "perfect" (doesn't exist, does not need)
- `_fix_principle_slugs()` for hyphen → underscore normalization
- `VOICE_PRESSURE_LANGUAGE` added to hook block_codes

**A/B Test Results (Jan 11):**
- tummy-time: **Grade A PASSED**
- caring-for-clothes-folding-hanging: Failed (raw data mismatch)
- undivided-attention-during-feeding: Failed (pressure language)

---

## 10. Code Simplifier (January 2026)

Pattern-based code analysis. Based on Anthropic's code-simplifier agent.

### Usage

```bash
/simplify atlas/orchestrator/hooks.py
python -m atlas.simplifier.code_simplifier --file path/to/file.py
python -m atlas.simplifier.code_simplifier --file path/to/file.py --json
```

### Patterns Detected

| ID | Issue | Fix |
|----|-------|-----|
| REDUNDANT_TRUE | `if x == True:` | `if x:` |
| REDUNDANT_FALSE | `if x == False:` | `if not x:` |
| REDUNDANT_NONE | `x == None` | `x is None` |
| REDUNDANT_LEN | `len(x) > 0` | `if x:` |
| BARE_EXCEPT | `except:` | `except Exception:` |
| MUTABLE_DEFAULT | `def f(x=[])` | Use None default |
| BROAD_EXCEPTION | `except Exception:` | Catch specific |
| DEEP_NESTING | 3+ indent levels | Guard clauses |
| SYNC_IO | Sync file/http | Use async |

### Example Output

```
atlas/orchestrator/hooks.py: 5 issues
  [X] L325: Bare except catches everything -> except Exception:
  [!] L201: Deep nesting - use guard clauses -> Early return pattern
  [*] L243: == None -> is None -> x is None
```

### Files

| File | Purpose |
|------|---------|
| `atlas/simplifier/code_simplifier.py` | Main logic |
| `atlas/simplifier/patterns.py` | Pattern definitions |
| `config/simplifier.json` | Config (auto_hook, blocking) |

---

## 11. 2nd Brain / Thought Classifier (January 2026)

Voice-first capture and classification system. Transforms ATLAS from reactive (queries) to proactive (capture + digest).

### Philosophy

Based on "2nd Brain" video: "AI running a loop, not just AI as search."

| Video Concept | ATLAS Implementation |
|---------------|---------------------|
| Frictionless Capture (Dropbox) | Voice pipeline with capture triggers |
| Auto-Sort (Sorter) | ThoughtClassifier with pattern matching |
| Categories (Form) | PEOPLE, PROJECTS, IDEAS, ADMIN, RECIPES |
| Storage (Filing Cabinet) | SQLite semantic_memory with hierarchical source |
| Proactive Push (Tap on Shoulder) | Daily/weekly digest generator |
| Background Loop | Scheduler with systemd/cron support |

### Capture Triggers

Say any of these to bypass LLM and save directly:

```
"Remember...", "Save...", "Note...", "Capture...", "Record...", "Store..."
"Don't forget...", "Log this...", "Write down...", "Remember this..."
```

Example:
```
You: "Remember that Sarah called about the deadline"
ATLAS: "Captured as a person note. Stored."
```

### Categories & Records

| Category | Record Type | Key Fields |
|----------|-------------|------------|
| PEOPLE | PersonRecord | name, context, follow_ups, last_touched |
| PROJECTS | ProjectRecord | name, parent_project, sub_area, next_action |
| IDEAS | IdeaRecord | name, one_liner, notes |
| ADMIN | AdminRecord | name, due_date, status |
| RECIPES | RecipeRecord | name, notes |

### Project Hierarchy (Taxonomy)

Projects are auto-classified into parent/sub-area:

| Parent | Sub-Areas | Trigger Examples |
|--------|-----------|------------------|
| **baby-brains** | website, app, knowledge, os, marketing, content | "baby brains", "bb", "landing page" |
| **health** | sauna, red-light, garmin, workouts, ice-bath, running, meals | "sauna", "cold plunge", "5k", "macros" |

Voice confirmation includes hierarchy:
```
"Captured as Baby Brains website project. Stored."
"Captured as Health ice-bath project. Stored."
```

### Storage Format

Hierarchical source field for SQL queries:
```python
source = "classifier:projects:baby-brains:website"
source = "classifier:projects:health:running"
source = "classifier:recipes"
source = "classifier:ideas"
```

Query by hierarchy:
```sql
-- All Baby Brains projects
SELECT * FROM semantic_memory WHERE source LIKE '%:baby-brains:%';

-- Just health running entries
SELECT * FROM semantic_memory WHERE source LIKE '%:health:running';
```

### Usage

#### Voice Capture
```bash
python atlas/voice/pipeline.py
# Then speak: "Remember to build the landing page for Baby Brains"
```

#### CLI Classification
```bash
echo "Build Baby Brains landing page" | python -m atlas.orchestrator.classifier --json
echo "Try cold plunge for 3 minutes" | python -m atlas.orchestrator.classifier --store
```

#### MCP Tools
```python
# In Claude conversation
capture_thought("Build the Baby Brains landing page")
classify_thought("Research DIY sauna builds")
generate_daily_digest()
generate_weekly_review()
```

#### Digest Generation
```bash
python -m atlas.digest.generator --type daily
python -m atlas.digest.generator --type weekly --format voice
```

#### Scheduler
```bash
# Run once
python -m atlas.scheduler.loop --once daily_digest

# Run daemon
python -m atlas.scheduler.loop --daemon

# Generate cron/systemd configs
python -m atlas.scheduler.loop --generate-cron
python -m atlas.scheduler.loop --generate-systemd
```

### Key Files

| File | Purpose |
|------|---------|
| `atlas/orchestrator/classifier.py` | ThoughtClassifier, categories, PROJECT_TAXONOMY |
| `atlas/voice/pipeline.py` | CAPTURE_TRIGGERS, _handle_capture() |
| `atlas/digest/generator.py` | DigestGenerator, DailyDigest, WeeklyReview |
| `atlas/scheduler/loop.py` | ATLASScheduler, cron/systemd generation |
| `atlas/mcp/server.py` | capture_thought, classify_thought, generate_*_digest |

### Adding New Project Areas

Edit `PROJECT_TAXONOMY` in `atlas/orchestrator/classifier.py`:

```python
PROJECT_TAXONOMY = {
    "baby-brains": {
        "patterns": [r"\bbaby\s*brains?\b", r"\bbb\b"],
        "areas": {
            "website": [r"\bweb(?:site)?\b", r"\blanding\s+page\b"],
            # Add new area here
            "docs": [r"\bdocumentation\b", r"\bdocs\b"],
        }
    },
    # Add new parent project here
    "atlas": {
        "patterns": [r"\batlas\b"],
        "areas": {
            "voice": [r"\bvoice\b", r"\bstt\b", r"\btts\b"],
            "memory": [r"\bmemory\b", r"\bstore\b"],
        }
    },
}
```

---

## 11. Voice API Pipeline (January 2026)

### What It Does
Token-efficient voice-first health queries via PowerShell↔WSL2 bridge. Enables frictionless morning routine where user wakes up, speaks to ATLAS, and gets health status + guided workout.

### Key Design Decisions

**D40: Direct HTTP for Garmin API**
The `garth.connectapi()` library function returned empty responses despite valid OAuth tokens. Fixed by making direct HTTP requests to `connectapi.garmin.com` with OAuth2 bearer tokens. Working endpoints:
- `/hrv-service/hrv/{date}` - HRV data
- `/wellness-service/wellness/dailyStress/{date}` - Body battery + stress

**D41: Intent Detection Before LLM Routing**
Health/fitness queries use regex pattern matching to bypass LLM entirely (0 tokens). Order:
1. Health intents → cached status (0 tokens)
2. Meal intents → Haiku parsing (~200 tokens)
3. Capture intents → direct storage (0 tokens)
4. General queries → Router (Haiku/Sonnet)

**D42: Two Response Formats**
- Quick status: "my status" → one-liner
- Detailed briefing: "morning briefing" / "how was my sleep" → full metrics

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Windows         │     │ ~/.atlas/.bridge│     │ WSL2            │
│ PowerShell      │────▶│ audio_in.raw    │────▶│ bridge_file_    │
│ (mic input)     │     │ status.txt      │     │ server.py       │
│                 │◀────│ audio_out.raw   │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                        ┌────────────────────────────────┼────────────────────────────────┐
                        │                                │                                │
                        ▼                                ▼                                ▼
               ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
               │ Health Intent   │             │ Meal Intent     │             │ General Query   │
               │ (regex match)   │             │ (prefix match)  │             │ (LLM router)    │
               │                 │             │                 │             │                 │
               │ morning_sync.py │             │ nutrition/      │             │ llm/router.py   │
               │ → 0 tokens      │             │ → ~200 tokens   │             │ → varies        │
               └─────────────────┘             └─────────────────┘             └─────────────────┘
```

### Voice Commands

#### Quick Status (0 tokens)
```
"my status"
"what's my status"
"what is my status"
→ "YELLOW. Battery 32. HRV 56. Proceed with caution. Active Mobility."
```

#### Detailed Briefing (0 tokens)
```
"morning briefing"
"how was my sleep"
"give me a rundown"
→ "Morning briefing. YELLOW status. Mixed recovery signals.
   Body battery 32. Running low. HRV 56. Watch still calibrating baseline.
   Sleep data unavailable from Garmin. Stress moderate at 41.
   Today's workout: Active Mobility."
```

### Health Intent Patterns

```python
# In bridge_file_server.py
HEALTH_PATTERNS = [
    r"(what'?s|what is|show|give me|tell me).*(status|morning status)",
    r"my (morning )?status",
    r"(how am i|how'm i) (doing|today)",
    r"traffic light",
    r"body battery",
    r"hrv",
    r"sleep (score|hours|quality)",
    r"how (was|is|did).*(sleep|i sleep)",
    r"(morning )?briefing",
    r"(daily |morning )?report",
    r"give me.*(rundown|summary|overview)",
]
```

### Morning Sync Cache

Status is cached to `~/.atlas/morning_status.json` for 0-token queries:

```python
from atlas.health.morning_sync import get_morning_status, format_status_voice, format_briefing_voice

# Returns cached if <4 hours old, syncs fresh otherwise
status = get_morning_status()

# Quick format (one-liner)
format_status_voice(status)
# → "YELLOW. Battery 32. HRV 56. Proceed with caution."

# Detailed format
format_briefing_voice(status)
# → "Morning briefing. YELLOW status. Mixed recovery signals..."
```

### Token Cost Summary

| Action | Tokens | Cost |
|--------|--------|------|
| Morning status query | 0 (cache) | $0 |
| Detailed briefing | 0 (cache) | $0 |
| Meal logging | ~200 | $0.0002 |
| Thought capture | 0 | $0 |
| General query | ~500 | $0.0005 |
| **Daily estimate** | ~550 | **~$0.0006** |

Monthly estimate: ~$0.02

### Key Files

| File | Purpose |
|------|---------|
| `atlas/voice/bridge_file_server.py` | Main voice bridge server with intent routing |
| `atlas/health/morning_sync.py` | Status caching, voice formatting, 5am cron |
| `atlas/health/garmin.py` | Direct HTTP to Garmin API |
| `atlas/health/service.py` | HealthService orchestration |
| `atlas/health/routine_runner.py` | Timer-based 18-min morning routine |
| `atlas/health/workout_runner.py` | Timer-based workout execution |
| `atlas/voice/audio_utils.py` | Chime generation (440Hz sine waves) |

### CLI Testing

```bash
# Test morning sync (shows all metrics)
python -m atlas.health.morning_sync --test

# Voice output only
python -m atlas.health.morning_sync --test --voice

# Force fresh Garmin sync
python -m atlas.health.morning_sync --force

# Test workout runner
python -m atlas.health.workout_runner --dry-run

# List available workout protocols
python -m atlas.health.workout_runner --list
```

### Qwen3-TTS Voice Cloning (January 2026)

Voice synthesis using Qwen3-TTS with Jeremy Irons voice clone ("Lethal Gentleman" persona).

**Model:** `Qwen/Qwen3-TTS-12Hz-0.6B-Base` with ICL (In-Context Learning) mode

**Key Files:**
- `atlas/voice/tts_qwen.py` - TTS wrapper with voice cloning
- `config/voice/qwen_tts_voices.json` - Voice configurations
- `config/voice/jeremy_irons.wav` - Reference audio (11 seconds)

**Usage:**
```python
from atlas.voice.tts_qwen import get_qwen_tts

tts = get_qwen_tts("jeremy_irons")
result = tts.synthesize("Good morning, sir. Your status... is green.")

# result.audio - numpy array of audio samples
# result.sample_rate - 24000 Hz
# result.duration_ms - synthesis time
```

**Voice Cloning Requirements:**
- Clean reference audio (3-15 seconds, interview/podcast quality)
- Accurate transcript of reference audio
- RP British accent works best (regional accents struggle)

**Pacing Control:**
Use punctuation to control speech rhythm:
- Commas (`,`) → short pause
- Ellipses (`...`) → longer pause
- Periods (`.`) → sentence break

**Decision D90:** Adopted Qwen3-TTS over Kokoro-82M for voice quality. Jeremy Irons clone provides authoritative British voice matching ATLAS "Lethal Gentleman" persona. Thomas Shelby (Cillian Murphy) failed due to TV audio processing and Birmingham accent complexity.

### Future Enhancements

1. **Yesterday Comparison**: "Body battery 32, down from 45 yesterday"
2. **Weekly Trends**: "HRV trending up 12% over 7 days"
3. **Predictive Insights**: "At current drain, you'll hit low reserves around 3pm"
4. **Weekly Voice Summary**: Sunday evening review
5. **Additional Voice Clones**: Find clean interview audio for more voice options

---

## 12. Interactive Workout Timer (January 2026)

### What It Does
Voice-controlled workout execution that behaves like a personal trainer. User controls the pace - sets start when ready, rest periods have countdown beeps, and exercises advance on user command.

### Key Design Decisions

**D58: User-Paced Sets vs Auto-Timer**
The original WorkoutRunner ran timers automatically. The interactive version waits for user commands:
- "ready" → start set
- "done" → complete set, start rest
- Rest countdown with beeps at 30s, 15s, 5s

**D59: Weight Tracking (In Scope)**
Simple weight prompt during workout: "What weight?" → "30 kilos" → logged with exercise.
Progressive overload system (baseline-informed, periodization) is OUT OF SCOPE for this release.

### State Machine

```
                    ┌──────────────────────────────┐
                    │     WORKOUT_INACTIVE         │
                    └──────────────┬───────────────┘
                                   │ "start workout"
                    ┌──────────────▼───────────────┐
                    │   EXERCISE_PENDING           │
                    │ (waiting for "ready")        │
                    └──────────────┬───────────────┘
                                   │ "ready"
                    ┌──────────────▼───────────────┐
                    │   SET_ACTIVE                 │
                    │ (user doing reps)            │
                    └──────────────┬───────────────┘
                                   │ "done"
                ┌──────────────────┴──────────────────┐
                │                                      │
       (not last set)                          (last set)
                │                                      │
    ┌───────────▼───────────┐            ┌────────────▼────────────┐
    │   REST_ACTIVE         │            │   Next exercise or      │
    │ (countdown timer)     │            │   WORKOUT_COMPLETE      │
    └───────────┬───────────┘            └─────────────────────────┘
                │ timer ends OR "ready"
                │
    ┌───────────▼───────────┐
    │ EXERCISE_PENDING      │
    │ (next set)            │
    └───────────────────────┘
```

### Voice Commands

| Command | State | Response |
|---------|-------|----------|
| "start workout" | Inactive | "Strength A. 45 minutes. First exercise: Goblet Squat. 3 sets of 6. Say ready when set up." |
| "30 kilos" | Pending | "Got it. 30 kilos. Say ready to begin." |
| "ready" | Pending | "Set 1 at 30 kilos. Begin." |
| "done" / "finished" | Set active | "Set 1 complete. Rest 90 seconds." |
| "how long" | Resting | "45 seconds left." |
| "skip" | Any | "Skipping Goblet Squat. Next: Floor Press..." |
| "stop workout" | Active | "Workout stopped. 3 exercises completed." |

### Countdown Beeps

Rest timer plays audio beeps:
- **30 seconds**: Low pitch (550Hz)
- **15 seconds**: Medium pitch (660Hz)
- **5 seconds**: High pitch (880Hz), louder

### Usage

```python
# Voice activation (primary method)
# Say: "start workout"
# ATLAS: "Strength A. 45 minutes. First exercise..."

# The workout state is managed in BridgeFileServer:
# - _workout_active: bool
# - _workout_exercise_pending: bool
# - _workout_set_active: bool
# - _workout_rest_active: bool
# - _workout_current_weight: float | None
# - _workout_log: list[dict]  # Completed exercises
```

### Intent Detection Priority

Interactive workout has HIGH priority (stateful):
1. Assessment active (higher)
2. **Interactive workout active** ← handles ready/done/skip
3. **Interactive workout start** ← "start workout"
4. Other intents...

### Key Files

| File | Purpose |
|------|---------|
| `atlas/voice/bridge_file_server.py` | State machine, handlers, voice patterns |
| `atlas/voice/audio_utils.py` | Countdown beep generation (440Hz-880Hz) |
| `atlas/voice/number_parser.py` | `parse_weight_value()` for weight input |
| `atlas/health/workout_runner.py` | `get_todays_protocol()`, WorkoutExercise |
| `config/workouts/phase1.json` | Workout protocols with exercises |

### Voice Patterns

```python
# In bridge_file_server.py
WORKOUT_START_PATTERNS = ["start workout", "begin workout", "let's workout", ...]
WORKOUT_READY_PATTERNS = ["ready", "start", "begin", "let's go", ...]
WORKOUT_SET_DONE_PATTERNS = ["done", "finished", "racked", "got it", ...]
WORKOUT_SKIP_PATTERNS = ["skip", "skip this", "next exercise", ...]
WORKOUT_STOP_PATTERNS = ["stop workout", "end workout", "cancel workout", ...]
```

### Testing

```bash
# Start the voice bridge server
python -m atlas.voice.bridge_file_server

# Then via voice:
# 1. "start workout"
# 2. "30 kilos"  (or just "ready" to skip weight)
# 3. "ready"
# 4. (do your set)
# 5. "done"
# 6. (wait for rest or say "ready" to skip)
# 7. Repeat until workout complete
# 8. "finished my workout" (logs to database)
```

### Future Enhancements (Out of Scope)

1. ~~**Progressive Overload System**~~: ✅ IMPLEMENTED - see ProgressionService
2. **Rep Counting**: "I got 5 reps" during set - ✅ IMPLEMENTED (AMRAP on final set)
3. **Garmin HR Integration**: Real-time HR during sets
4. **Tempo Guidance**: Audio cues for lifting cadence

---

## 13. Workout Scheduler (January 2026)

The WorkoutScheduler tracks program progress and handles missed workouts intelligently.

### The Problem

Calendar-only scheduling doesn't handle real life:
- Missed workouts compound ("you're 5 workouts behind")
- No tracking of program day/week
- User doesn't know if they're on track

### The Solution

```python
from atlas.health.scheduler import WorkoutScheduler

scheduler = WorkoutScheduler()

# Get next workout (handles catch-ups)
next_workout = scheduler.get_next_workout()
# Returns: ScheduledWorkout with protocol_id, program_day, is_catch_up, etc.

# Start program (Day 1)
scheduler.start_phase("phase_1")  # Sets today as Day 1

# Log completed workout
scheduler.log_workout(
    protocol_id="strength_a",
    duration_minutes=45,
    traffic_light="GREEN",
)

# Check status
status = scheduler.get_status()
# {'program_day': 10, 'program_week': 2, 'workouts_completed': 8, 'on_track': True}
```

### Sequential Mode (Default)

Missed workouts are caught up in order:

```
Phase starts Monday Jan 13
User misses Mon, Tue
Says "start workout" on Wednesday

Scheduler returns:
  - protocol_id: "strength_a" (Monday's workout)
  - is_catch_up: True
  - days_behind: 2
  - message: "Catching up from Monday. Strength A..."
```

### Voice Integration

```bash
# Program management
"start program"     → Starts Phase 1 from today
"schedule status"   → "Week 2, Day 10. On track. 8 workouts completed."
"what day am I on"  → Same as schedule status
"reset my program"  → Requires confirmation (shows workout count)

# Traffic light override
"green day"         → Starts workout with GREEN override
"yellow day"        → Starts workout with YELLOW override

# Rest day handling
"start workout" (on Sunday) → "Today is a recovery day. No workout scheduled."

# Catch-up announcement
"start workout" (behind) → "Week 2, Day 10. Catching up from Monday. Strength A..."
```

### Database Schema

```sql
CREATE TABLE workout_sessions (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    protocol_id TEXT NOT NULL,     -- 'strength_a', 'zone2_cardio', etc.
    protocol_name TEXT,
    program_day INTEGER,           -- Day 1, Day 2, etc.
    program_week INTEGER,          -- Week 1, Week 2, etc.
    phase TEXT DEFAULT 'phase_1',
    duration_minutes INTEGER,
    traffic_light TEXT,            -- GREEN/YELLOW/RED
    garmin_activity_id TEXT,
    notes TEXT,
    created_at TIMESTAMP,
    UNIQUE(date, protocol_id)
);
```

### Key Files

| File | Purpose |
|------|---------|
| `atlas/health/scheduler.py` | WorkoutScheduler class |
| `atlas/voice/bridge_file_server.py` | Voice intent handling |
| `config/workouts/phase1.json` | Schedule configuration |

---

## 14. Interactive Morning Routine (January 2026)

Voice-guided 18-minute morning protocol with timer control and form cues.

### Voice Commands

```bash
"start routine"       → Begins morning protocol
"ready" / "begin"     → Starts exercise timer
"pause" / "hold on"   → Pauses timer
"resume" / "continue" → Resumes timer
"form" / "setup"      → Shows form cues (auto-pauses)
"skip" / "next"       → Skips to next exercise
"finished" / "done"   → Completes routine (on last exercise)
```

### Flow

```
1. "start routine"
   → "Starting ATLAS Morning Protocol. 18 minutes. First: Plantar Fascia Ball Roll..."

2. "ready"
   → "60 seconds. Begin." (timer starts, chime at end)

3. [Timer ends]
   → Chime plays, advances to next exercise

4. "form"
   → "Plantar Fascia Ball Roll. Apply moderate pressure. Roll heel to toes..."
   → Auto-pauses, says "Say resume when ready"

5. [Last exercise]
   → "finished"
   → "Morning routine complete. Green light. Today: Strength A. Say start workout."
```

### Form Guides

Form cues are loaded from `config/exercises/routine_form_guides.json`:

```json
{
  "exercises": {
    "plantar_ball_roll": {
      "name": "Plantar Fascia Ball Roll",
      "setup": "Stand near wall for balance. Place lacrosse ball under foot.",
      "cues": [
        "Apply moderate pressure",
        "Roll heel to toes slowly",
        "Pause 5 seconds on tender spots"
      ],
      "common_mistakes": [
        {"mistake": "Too much pressure", "fix": "Start light, increase gradually"}
      ]
    }
  }
}
```

---

## Research References

These patterns are based on Anthropic's 2025-2026 research:

| Pattern | Source | Key Finding |
|---------|--------|-------------|
| Session Handoff | [Long-Running Agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents) | JSON prevents model modification; single-task-per-session |
| Sandboxing | [Claude Code Sandboxing](https://anthropic.com/engineering/claude-code-sandboxing) | OS-level isolation for sub-agents |
| Confidence Routing | [Introspection](https://anthropic.com/research/introspection) | "Wait" pattern reduces blind spots 89.3% |
| Verification | [Tracing Thoughts](https://anthropic.com/research/tracing-thoughts-language-model) | CoT is unfaithful; external verification required |

---

*This guide should be read by any agent working on ATLAS to understand available capabilities.*
