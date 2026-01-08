# ATLAS Architecture V2

> Based on Claude Agent SDK Masterclass Analysis (R30)
> Updated: 2026-01-08
> **Status: ✅ COMPLETE** - All 6 gaps implemented and audited

---

## Overview

ATLAS V2 evolves the orchestrator based on masterclass insights while preserving what's already working.

**Core Principle**: ATLAS is well-aligned with Claude Agent SDK patterns. V2 adds the missing capabilities identified in the gap analysis.

### V2 Implementation Status (January 8, 2026)

| Component | Status | Confidence |
|-----------|--------|------------|
| SubAgentExecutor | ✅ Complete | 95% |
| HookTiming | ✅ Complete | 98% |
| SessionManager | ✅ Complete | 98% |
| Progressive Loading | ✅ Complete | 92% |
| ScratchPad | ✅ Complete | 98% |

---

## Current State (V1)

### What's Working

| Component | File | Status |
|-----------|------|--------|
| Command Router | `atlas/orchestrator/command_router.py` | ✅ Production |
| Skill Executor | `atlas/orchestrator/skill_executor.py` | ✅ Production |
| Hook Framework | `atlas/orchestrator/hooks.py` | ✅ Production |

### Aligned with Masterclass

1. **Skills as markdown specs** → System prompt pattern ✅
2. **Hooks wrap validators** → Deterministic verification ✅
3. **CLI-first execution** → Claude CLI integration ✅
4. **File system as context** → Skills loaded from disk ✅

---

## V2 Additions

### 1. Sub-Agent Support (Priority: High)

**Gap**: No parallel execution or context isolation.

**Solution**: Add `SubAgentExecutor` class.

```python
# atlas/orchestrator/subagent_executor.py

class SubAgentExecutor:
    """Execute sub-agents with isolated context."""

    async def spawn(
        self,
        task: str,
        context: Optional[dict] = None,
        parallel: bool = False
    ) -> SubAgentResult:
        """
        Spawn a sub-agent with fresh context.

        Args:
            task: Task description for the sub-agent
            context: Minimal context to seed (NOT full history)
            parallel: If True, returns immediately (use await_all)
        """
        # Implementation: subprocess call to claude CLI
        # with fresh context (no pollution from main agent)
        pass

    async def spawn_parallel(
        self,
        tasks: list[str],
        contexts: Optional[list[dict]] = None
    ) -> list[SubAgentResult]:
        """Spawn multiple sub-agents in parallel."""
        pass
```

**Use Cases**:
- Parallel skill execution across repos
- Adversarial verification ("junior analyst" pattern)
- Complex data analysis with context isolation

---

### 2. Multi-Point Verification (Priority: High)

**Gap**: Only post-execution hooks.

**Solution**: Extend `HookRunner` with hook timing.

```python
# atlas/orchestrator/hooks.py (extended)

class HookTiming(Enum):
    PRE_EXECUTION = "pre"    # Before skill runs
    MID_EXECUTION = "mid"    # During skill chain
    POST_EXECUTION = "post"  # After skill completes

HOOKS = {
    "babybrains": {
        "qc_runner": {
            "timing": HookTiming.POST_EXECUTION,  # existing
            ...
        },
        "prereq_check": {
            "timing": HookTiming.PRE_EXECUTION,  # NEW
            "cmd": ["python", "scripts/check_prereqs.py"],
            "blocking": True,
        },
        "intermediate_validation": {
            "timing": HookTiming.MID_EXECUTION,  # NEW
            "cmd": ["python", "qc/validate_step.py"],
            "blocking": False,  # Advisory only
        }
    }
}
```

**Hook Placement Points**:
1. **Pre-execution**: Check prerequisites (files exist, dependencies ready)
2. **Mid-execution**: Validate intermediate outputs in skill chains
3. **Post-execution**: Final QC validation (existing)

---

### 3. Context Management (Priority: High)

**Gap**: No session management or context clearing.

**Solution**: Add `SessionManager` class.

```python
# atlas/orchestrator/session_manager.py

class SessionManager:
    """Manage context across skill executions."""

    def __init__(self, session_dir: Path = Path(".claude/sessions")):
        self.session_dir = session_dir
        self.current_session_id: Optional[str] = None

    async def start_session(self) -> str:
        """Start new session, return session ID."""
        pass

    async def save_state(self, state: dict) -> None:
        """Save current state to session file."""
        pass

    async def get_git_diff_context(self) -> dict:
        """Get minimal context using git diff pattern."""
        # Run: git diff --stat
        # Return: {"changes": [...], "files_modified": [...]}
        pass

    async def clear_and_resume(self) -> dict:
        """Clear context window, reload minimal state."""
        state = await self.load_state()
        git_context = await self.get_git_diff_context()
        return {
            "previous_state": state,
            "current_changes": git_context,
            # Minimal context, not full history
        }
```

**Patterns Implemented**:
- Git diff for context reload (masterclass [4575s])
- State persistence to files (masterclass [4583s])
- Session clearing between tasks

---

### 4. Adversarial Checking (Priority: Medium)

**Gap**: No "junior analyst" verification pattern.

**Solution**: Add to `SubAgentExecutor`.

```python
# atlas/orchestrator/subagent_executor.py (extended)

class SubAgentExecutor:

    async def verify_adversarially(
        self,
        output: dict,
        skill_name: str,
        persona: str = "junior analyst at McKinsey"
    ) -> VerificationResult:
        """
        Spawn sub-agent to adversarially check output.

        Uses fresh context with "junior analyst" framing.
        """
        prompt = f"""
        You are a {persona} reviewing work.

        The following output was produced by a {skill_name} skill:

        {json.dumps(output, indent=2)}

        Check for:
        1. Factual accuracy
        2. Logical consistency
        3. Missing information
        4. Potential errors

        Return JSON: {{"passed": bool, "issues": [...]}}
        """

        return await self.spawn(
            task=prompt,
            context=None  # Fresh context - no pollution
        )
```

---

### 5. Progressive Context Loading (Priority: Medium)

**Gap**: Skills load full content at once.

**Solution**: Extend `SkillLoader` with progressive loading.

```python
# atlas/orchestrator/skill_executor.py (extended)

class SkillLoader:

    def load_skill_header(self, skill_name: str) -> str:
        """Load only skill header/summary."""
        skill_content = self.load_skill(skill_name)
        # Extract first section only
        return skill_content.split("## ")[0]

    def load_skill_section(self, skill_name: str, section: str) -> str:
        """Load specific section of skill on demand."""
        skill_content = self.load_skill(skill_name)
        # Extract specific section
        pass

    def list_skill_sections(self, skill_name: str) -> list[str]:
        """List available sections in skill."""
        skill_content = self.load_skill(skill_name)
        # Parse ## headers
        return [line[3:] for line in skill_content.split("\n")
                if line.startswith("## ")]
```

---

### 6. Scratch Pad Pattern (Priority: Low)

**Gap**: No intermediate state tracking during complex operations.

**Solution**: Add `ScratchPad` class.

```python
# atlas/orchestrator/scratch_pad.py

class ScratchPad:
    """Track intermediate state during skill chains."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries: list[ScratchEntry] = []

    def add(self, key: str, value: Any, step: int) -> None:
        """Add entry to scratch pad."""
        self.entries.append(ScratchEntry(
            key=key,
            value=value,
            step=step,
            timestamp=datetime.now()
        ))

    def get_summary(self) -> str:
        """Get summary for context reload."""
        # Format entries as minimal context string
        pass

    def to_file(self, path: Path) -> None:
        """Persist scratch pad to file."""
        pass
```

---

## V2 File Structure

```
/home/squiz/ATLAS/
├── atlas/
│   └── orchestrator/
│       ├── __init__.py
│       ├── command_router.py      # V1 (unchanged)
│       ├── skill_executor.py      # V1 + progressive loading
│       ├── hooks.py               # V1 + multi-point timing
│       ├── subagent_executor.py   # V2 NEW
│       ├── session_manager.py     # V2 NEW
│       └── scratch_pad.py         # V2 NEW
└── docs/
    ├── ATLAS_ARCHITECTURE_V2.md   # This file
    └── research/
        ├── R30.Claude Agent SDK Masterclass Analysis.md
        ├── R30_Section1_Philosophy.md
        ├── R30_Section2_Implementation.md
        └── R30_Section3_Advanced.md
```

---

## Implementation Order

### Phase 1: Verification Enhancement (Week 1)

1. Extend `HookRunner` with `HookTiming` enum
2. Add pre-execution hooks to existing `HOOKS` config
3. Test with babybrains `prereq_check` hook

### Phase 2: Sub-Agent Support (Week 2)

1. Implement `SubAgentExecutor` class
2. Add parallel execution support
3. Implement adversarial checking method

### Phase 3: Context Management (Week 3)

1. Implement `SessionManager` class
2. Add git diff pattern for context reload
3. Integrate with `CommandRouter` for session tracking

### Phase 4: Progressive Loading (Week 4)

1. Extend `SkillLoader` with header/section methods
2. Add scratch pad for complex skill chains
3. Test with multi-step babybrains pipelines

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Skill execution success rate | ~85% | 95% |
| Context window usage | Unknown | <50% per task |
| Parallel skill execution | Not supported | 3+ concurrent |
| Pre-execution validation | 0 hooks | 2+ per repo |
| Session recovery | Manual | Automatic |

---

## Compatibility Notes

### Breaking Changes: None

V2 is purely additive. All V1 components continue working.

### Deprecations: None

No V1 patterns are deprecated.

### Migration Path

1. Deploy V2 alongside V1
2. Enable new features incrementally
3. No code changes required for existing workflows

---

## References

- [R30.Claude Agent SDK Masterclass Analysis](./research/R30.Claude%20Agent%20SDK%20Masterclass%20Analysis.md)
- [R30_Section1_Philosophy](./research/R30_Section1_Philosophy.md)
- [R30_Section2_Implementation](./research/R30_Section2_Implementation.md)
- [R30_Section3_Advanced](./research/R30_Section3_Advanced.md)
- [ORCHESTRATOR_HANDOVER](./ORCHESTRATOR_HANDOVER.md)

---

*Architecture V2 defined: 2026-01-07*
*Based on: Claude Agent SDK Masterclass (Tariq, Anthropic)*
