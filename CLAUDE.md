# ATLAS Project Context

## What ATLAS Is
Voice-first AI assistant with <1.8s latency target.
Hardware: ThinkPad X1 Extreme, 16GB RAM, RTX 3050 Ti 4GB.

## V2 Orchestrator Components
| Component | File | Purpose |
|-----------|------|---------|
| SkillLoader | atlas/orchestrator/skill_executor.py | Load skills progressively |
| SubAgentExecutor | atlas/orchestrator/subagent_executor.py | Spawn isolated sub-agents |
| HookRunner | atlas/orchestrator/hooks.py | PRE/POST validation hooks |
| SessionManager | atlas/orchestrator/session_manager.py | Session state + git context |
| ScratchPad | atlas/orchestrator/scratch_pad.py | Intermediate results tracking |

## Key Commands
- Tests: `pytest`
- Voice pipeline: `python atlas/voice/pipeline.py`

## Key Documentation
- V2 Guide: docs/V2_ORCHESTRATOR_GUIDE.md
- Architecture: docs/ATLAS_ARCHITECTURE_V2.md
- Activity Pipeline: docs/HANDOVER_ACTIVITY_PIPELINE.md

## Coding Standards
- Use async/await for all I/O
- Specific exceptions before catch-all
- Always add logging to new modules

## Current Focus
Full setup implementation - Phase 1-3 infrastructure
