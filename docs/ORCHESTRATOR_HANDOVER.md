# ATLAS Orchestrator Implementation Handover

**Created**: 2026-01-07
**Status**: Steps 1-2 Complete, Step 3 Ready

---

## 1. Completed Work

### Step 1: Infrastructure (Routing Works)
**Status**: ✅ VERIFIED

Created slash command routing infrastructure:

| File | Purpose |
|------|---------|
| `atlas/orchestrator/__init__.py` | Module init with lazy imports |
| `atlas/orchestrator/command_router.py` | Slash command parsing and routing |
| `skills/babybrains/BABYBRAINS.md` | Skill specification stub |

**Test Results**:
```bash
$ python -m atlas.orchestrator.command_router babybrains status
babybrains-os orchestrator status:
  Repo path: /home/squiz/code/babybrains-os [OK]
  Skill file: /home/squiz/ATLAS/skills/babybrains/BABYBRAINS.md [OK]
```

### Step 2: Single Hook (QC Validation Works)
**Status**: ✅ VERIFIED

Created hook framework that wraps existing validators:

| File | Purpose |
|------|---------|
| `atlas/orchestrator/hooks.py` | Hook runner wrapping qc_runner.py |

**Test Results**:
```bash
# Pass case
$ python -m atlas.orchestrator.command_router babybrains qc tests/scripts/draft_21s.pass.json
QC Validation: PASSED
Advisory Issues (1):
  ⚠️  [EVIDENCE_MISSING] ...

# Fail case
$ python -m atlas.orchestrator.command_router babybrains qc tests/scripts/draft_21s.fail.json
QC Validation: FAILED
Blocking Issues (5):
  ❌ [HOOK_FLAG_MISSING] ...
  ❌ [HOOK_TOO_LONG] ...
  ❌ [FIRST_FRAME_ACTION] ...
  ❌ [SRT_MISSING] ...
  ❌ [SAFETY_LINES_MISSING] ...
```

---

## 2. Step 3 Requirements: skill_executor.py

### What It Needs To Do

Execute a single babybrains-os skill by:
1. Loading the skill spec markdown (e.g., `skills/draft_21s.md`)
2. Using the markdown as Claude Agent SDK system prompt
3. Passing input data as user prompt
4. Validating output against JSON schema
5. Returning structured result

### Skill Invocation Mechanism (Key Decision)

Skills are **NOT code** - they're **prompt specifications**. The execution flow:

```
User: /babybrains draft --skill draft_21s
              ↓
CommandRouter parses command
              ↓
SkillExecutor loads /home/squiz/code/babybrains-os/skills/draft_21s.md
              ↓
SkillExecutor builds Claude Agent SDK query:
  - System prompt = skill markdown content
  - User prompt = "Generate output for domain=X, format=21s"
              ↓
Claude Agent SDK generates JSON output
              ↓
Output validates against schemas/draft_21s.out.v1.json
              ↓
Return structured result
```

### Required Implementation

Create `atlas/orchestrator/skill_executor.py`:

```python
class SkillExecutor:
    """Execute skills via Claude Agent SDK."""

    async def execute(
        self,
        skill_name: str,
        input_data: dict,
        validate: bool = True,
    ) -> SkillResult:
        # 1. Load skill markdown from babybrains-os/skills/{skill_name}.md
        # 2. Load schema from babybrains-os/schemas/{skill_name}.out.v1.json
        # 3. Build Claude Agent SDK prompt
        # 4. Call claude_agent_sdk.query() or similar
        # 5. Validate output against schema
        # 6. Return result
```

### Claude Agent SDK Usage

From R30 research, the SDK pattern is:
```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Execute draft_21s skill for domain=regulation",
    options=ClaudeAgentOptions(
        system_prompt=skill_markdown_content,
        model="haiku",  # Use haiku for speed
        max_turns=1,    # Single turn for skill execution
    )
):
    # Handle streaming response
```

**Note**: Verify actual SDK API - method names may differ from masterclass.

---

## 3. Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Router separation | Separate `command_router.py` from `llm/router.py` | Keep LLM tier routing separate from slash command orchestration |
| Skill invocation | Markdown → system prompt | Skills are prompts, not code (masterclass pattern) |
| Hook wrapping | Subprocess wrapper | Use existing validators, don't rebuild |
| CLI-first | CLI before voice | Prove orchestration before adding NLU complexity |
| First repo | babybrains-os | Most sophisticated skill chain, proves full pattern |

---

## 4. Files to Reference

### Architecture Documentation
- `/home/squiz/ATLAS/docs/research/R30.Claude Agent SDK Masterclass Analysis.md` - Core concepts with timestamps
- `/home/squiz/.claude/plans/majestic-seeking-lagoon.md` - Full implementation plan

### Working Code
- `/home/squiz/ATLAS/atlas/orchestrator/command_router.py` - Slash command routing
- `/home/squiz/ATLAS/atlas/orchestrator/hooks.py` - Hook framework

### Skill Specifications
- `/home/squiz/ATLAS/skills/babybrains/BABYBRAINS.md` - Orchestrator entry point
- `/home/squiz/code/babybrains-os/skills/draft_21s.md` - Example skill to execute
- `/home/squiz/code/babybrains-os/schemas/draft_21s.out.v1.json` - Output schema

### Test Files
- `/home/squiz/code/babybrains-os/tests/scripts/draft_21s.pass.json` - Valid input
- `/home/squiz/code/babybrains-os/tests/scripts/draft_21s.fail.json` - Invalid input

---

## 5. Next Steps (Step 3)

### Implementation Tasks

1. **Create `atlas/orchestrator/skill_executor.py`**
   - SkillLoader class to load markdown + schema
   - SkillExecutor class to run via Claude Agent SDK
   - Schema validation using jsonschema

2. **Update `command_router.py`**
   - Add handler for `/babybrains draft --skill <name>`
   - Wire up SkillExecutor

3. **Test with single skill**
   - Execute draft_21s skill
   - Validate output against schema

### Suggested Command Interface

```bash
# Execute single skill with input from file
/babybrains draft --skill draft_21s --input plan_output.json

# Or pipe input
cat plan_output.json | /babybrains draft --skill draft_21s
```

---

## 6. Test Commands

### Verify Steps 1-2 Still Work
```bash
cd /home/squiz/ATLAS
source venv/bin/activate

# Step 1: Status check
python -m atlas.orchestrator.command_router babybrains status

# Step 2: QC validation
python -m atlas.orchestrator.command_router babybrains qc tests/scripts/draft_21s.pass.json
python -m atlas.orchestrator.command_router babybrains qc tests/scripts/draft_21s.fail.json
```

### Step 3 Success Criteria
```bash
# Execute single skill (when implemented)
python -m atlas.orchestrator.command_router babybrains draft --skill draft_21s

# Should:
# 1. Load skills/draft_21s.md as system prompt
# 2. Execute via Claude Agent SDK
# 3. Return JSON matching draft_21s.out.v1.json schema
```

---

## 7. Open Questions for Step 3

1. **Claude Agent SDK API**: Need to verify actual method names (`query()` vs `Agent.run()` vs other)
2. **Input format**: Should draft_21s receive full plan output or extracted fields?
3. **Streaming**: Should we stream the response or wait for complete output?
4. **Error handling**: What happens if Claude returns invalid JSON?

---

## 8. Session Start Prompt for New Agent

```
Continue ATLAS orchestrator implementation.

Context:
- Read /home/squiz/ATLAS/docs/ORCHESTRATOR_HANDOVER.md (this file)
- Read /home/squiz/ATLAS/docs/research/R30.Claude Agent SDK Masterclass Analysis.md
- Steps 1-2 complete: command_router.py and hooks.py working

Task: Implement Step 3 - skill_executor.py
- Create atlas/orchestrator/skill_executor.py
- /babybrains draft --skill draft_21s should execute single skill via Claude Agent SDK
- Skill spec (markdown) becomes system prompt
- Output validates against JSON schema from babybrains-os/schemas/

Test files available:
- /home/squiz/code/babybrains-os/skills/draft_21s.md (skill spec)
- /home/squiz/code/babybrains-os/schemas/draft_21s.out.v1.json (output schema)
```

---

*Handover created: 2026-01-07*
*Next step: Implement skill_executor.py for Step 3*
