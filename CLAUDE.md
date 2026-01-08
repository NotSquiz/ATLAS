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
| ConfidenceRouter | atlas/orchestrator/confidence_router.py | Route responses by confidence level |

## Infrastructure (January 2026)
Based on Anthropic research papers. See `docs/V2_ORCHESTRATOR_GUIDE.md` for full details.

| Feature | Location | Purpose |
|---------|----------|---------|
| Session Handoff | `.claude/handoff.md` | Track session state for context transitions |
| Progress Tracking | `.claude/atlas-progress.json` | JSON task tracking (prevents model modification) |
| Sandbox Configs | `config/sandbox/*.json` | Security isolation for sub-agents and hooks |
| Confidence Router | `atlas/orchestrator/confidence_router.py` | Route by verbalized confidence + "Wait" pattern |

### Confidence Routing
```python
from atlas.orchestrator.confidence_router import route_by_confidence

result = route_by_confidence(response_text, domain="health")
# Returns: action (PROCEED, VERIFY_EXTERNAL, VERIFY_ADVERSARIAL, REGENERATE)
# Safety-critical domains trigger confidence inversion (high confidence = more verification)
```

### The "Wait" Pattern (89.3% blind spot reduction)
```python
from atlas.orchestrator.confidence_router import apply_wait_pattern

correction_prompt = apply_wait_pattern(original_response, query)
# Adds: "Wait. Before evaluating, pause and consider: What assumptions did I make?..."
```

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
