# ATLAS V2 Orchestrator Guide

> **Purpose:** This document explains ATLAS's orchestration capabilities so that ATLAS (or any agent) can understand and use them effectively.
> **Last Updated:** January 9, 2026

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
| `docs/DECISIONS.md` | Why each decision was made (D1-D18) |
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
# Primary mode: single activity with quality audit
python -m atlas.pipelines.activity_conversion --activity tummy-time

# With explicit retry count
python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 3

# List pending activities
python -m atlas.pipelines.activity_conversion --list-pending

# Batch mode (use only after skills reliably produce Grade A)
python -m atlas.pipelines.activity_conversion --batch --limit 10
```

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
| `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md` | Grading criteria |

### External Dependencies

The quality audit requires these files to exist:
- **Voice Rubric** (required): `/home/squiz/code/knowledge/coverage/VOICE_ELEVATION_RUBRIC.md`
- **Reference A+ Activity** (optional): `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml`

If rubric is missing, audit returns Grade F with system error.

---

## 10. Code Simplifier (January 2026)

### What It Does
On-demand code analysis tool that suggests improvements while preserving functionality. Designed as a learning tool for beginner coders, with educational explanations for each suggestion.

### Key Features
- **Pattern-based analysis**: Detects 15+ common issues (redundant code, anti-patterns, complexity)
- **ATLAS-specific rules**: Enforces CLAUDE.md coding standards (async/await, specific exceptions, logging)
- **Educational explanations**: Each suggestion includes before/after examples and "why" explanation
- **Severity levels**: ERROR (must-fix), WARNING, SUGGESTION, INFO

### Usage

```bash
# Help and usage info
/simplify

# Analyze a file
/simplify atlas/orchestrator/hooks.py

# With detailed explanations (learning mode)
/simplify --verbose atlas/orchestrator/hooks.py

# CLI mode
python -m atlas.simplifier.code_simplifier --file path/to/file.py
python -m atlas.simplifier.code_simplifier --file path/to/file.py --verbose
python -m atlas.simplifier.code_simplifier --file path/to/file.py --json
```

### What It Detects

| Category | Examples |
|----------|----------|
| **Redundant Code** | `if x == True:` -> `if x:`, `len(list) == 0` -> `not list` |
| **Python Anti-patterns** | Bare `except:`, mutable default arguments (`def foo(items=[])`) |
| **ATLAS Standards** | Missing async/await for I/O, broad Exception catches, missing logging |
| **Complexity** | Deep nesting (>3 levels), long functions (>50 lines) |

### Example Output

```
Code Simplification Report
========================================
File: atlas/orchestrator/hooks.py
Lines analyzed: 538
Suggestions: 14

Summary: 1 warnings, 7 suggestions, 6 info

WARNINGS:
  [!] Line 325: Catching broad Exception

SUGGESTIONS:
  [*] Line 201: Deep nesting detected
  [*] Line 243: Deep nesting detected

INFO:
  [i] Line 70: Long function detected: advisory_issues() is 81 lines

ATLAS Coding Standards (from CLAUDE.md):
  - Use async/await for all I/O operations
  - Catch specific exceptions before catch-all (except Exception)
  - Always add logging to new modules

Tip: Use --verbose for detailed explanations
```

### Verbose Output (Learning Mode)

```
[WARNING] Catching broad Exception
  Line 325: except Exception as e:

  Before: except Exception as e:
  After:  except (ValueError, KeyError) as e:

  Why: ATLAS rule: 'Specific exceptions before catch-all'. Catching Exception
  is better than bare except, but consider which specific exceptions you expect
  and handle those. This makes debugging easier and prevents swallowing
  unexpected errors.
```

### Programmatic Usage

```python
from atlas.simplifier import CodeSimplifier
from atlas.simplifier.patterns import Severity

# Create simplifier
simplifier = CodeSimplifier()

# Analyze file
result = simplifier.analyze_file("path/to/file.py")

# Check results
if result.has_suggestions:
    print(result.format_report(verbose=True))

# Filter by severity
errors = result.suggestions_by_severity(Severity.ERROR)
warnings = result.suggestions_by_severity(Severity.WARNING)

# JSON output (for integration)
print(result.to_json())
```

### Configuration

Configuration file: `config/simplifier.json`

```json
{
  "enabled": true,
  "auto_trigger": {
    "enabled": false,
    "complexity_threshold": 10,
    "min_lines": 20,
    "exclude_paths": ["tests/", "*.test.py"]
  },
  "output": {
    "default_verbose": false,
    "show_atlas_rules": true
  },
  "blocking": false
}
```

### Key Files

| File | Purpose |
|------|---------|
| `atlas/simplifier/__init__.py` | Module exports |
| `atlas/simplifier/code_simplifier.py` | Main analysis logic |
| `atlas/simplifier/patterns.py` | Simplification patterns with explanations |
| `config/simplifier.json` | Configuration options |
| `atlas/orchestrator/command_router.py` | `/simplify` command handler |

### Future Enhancements
- **Auto Hook mode**: Enable as POST hook after code-producing skills
- **Adversarial verification**: Use SubAgentExecutor to verify suggestions
- **Wait pattern integration**: Apply reflection before major simplifications

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
