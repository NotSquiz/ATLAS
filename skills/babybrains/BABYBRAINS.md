# babybrains-os Orchestrator Skill

## Overview

Orchestrates the 9-skill content pipeline for Baby Brains marketing materials.
This skill file is loaded as the system prompt when executing `/babybrains` commands.

**Repo**: `/home/squiz/code/babybrains-os`

## Skill Chain

The content pipeline follows this chain:

```
Intent → play_select → angle_synth → brief_skeleton → draft_21s/60s → cite_safety → qc
```

### Skills

| # | Skill | Purpose | Input | Output |
|---|-------|---------|-------|--------|
| 1 | play_select | Rank 5 whitelisted plays by relevance | topic, persona, format | Ranked plays |
| 2 | angle_synth | Generate 3 distinct content angles | play, knowledge | 3 hooks with evidence |
| 3 | brief_skeleton | Create segment structure | angle, format, play | Beat assignments |
| 4 | draft_21s | Generate 55-65 word script | plan, ingest | Full script + SRT |
| 5 | draft_60s | Generate 160-185 word script | plan, ingest | Full script + SRT |
| 6 | cite_safety | Validate citations, generate safety | draft, knowledge | Validated claims |
| 7 | qc | Quality control validation | all outputs | Pass/Fail + issues |

## Commands

```bash
/babybrains status                     # Check orchestrator status
/babybrains qc < script.json           # Run QC validation only
/babybrains next21 <domain> [audience] # Full 21s script pipeline
/babybrains next60 <domain> [audience] # Full 60s script pipeline
```

## Context Files

The following context files are loaded when executing skills:

- `contexts/intents.md` - Intent to skill chain mapping
- `contexts/plays.md` - Whitelisted plays for content
- `contexts/qc_rules.md` - QC blocking and advisory rules

## Hooks

- `hooks/qc_runner.md` - Wraps `/home/squiz/code/babybrains-os/qc/qc_runner.py`

## Execution Pattern

When ATLAS receives `/babybrains next21 regulation`:

1. CommandRouter parses command → `SlashCommand(BABYBRAINS, "next21", ["regulation"])`
2. SkillLoader loads this file + contexts
3. SkillExecutor builds Claude Agent SDK prompt:
   - System: This file + contexts
   - User: "Execute skill chain for domain=regulation, format=21s"
4. Claude generates JSON matching each skill's output schema
5. Outputs chain: skill_1.json → skill_2 input → skill_2.json → ...
6. QC hook runs on final output
7. Result returned to user

## Status

- [x] Skill file created (stub)
- [ ] Contexts loaded from babybrains-os
- [ ] Hook wrapper for qc_runner.py
- [ ] Full skill chain execution
- [ ] Schema validation

---

*Last updated: 2026-01-07*
*Phase: 2 (babybrains-os integration)*
