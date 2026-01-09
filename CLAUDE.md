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
| Activity QC Hook | `knowledge/scripts/check_activity_quality.py` | Voice/structure validation for Activity Atoms |
| Activity Pipeline | `atlas/pipelines/activity_conversion.py` | 7-stage pipeline with quality audit gate |
| Quality Audit | `atlas/pipelines/activity_conversion.py:audit_quality()` | Grade A enforcement via Voice Rubric |

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
- **Verification Prompts: docs/VERIFICATION_PROMPTS.md** (self-check patterns)

## Coding Standards
- Use async/await for all I/O
- Specific exceptions before catch-all
- Always add logging to new modules

## Current Focus
Phase 4 - Quality audit pipeline + intelligent retry with Wait pattern

### Activity Pipeline Commands (CLI Mode - No API Key)
```bash
# Convert single activity (primary mode)
python -m atlas.pipelines.activity_conversion --activity tummy-time

# With explicit retry count (uses Wait pattern for intelligent retry)
python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 3

# List pending activities
python -m atlas.pipelines.activity_conversion --list-pending

# Batch mode (only after skills reliably produce Grade A)
python -m atlas.pipelines.activity_conversion --batch --limit 10
```

### Quality Audit Pipeline
```python
# Quality audit grades activities A/B+/B/C/F using Voice Elevation Rubric
# Only Grade A proceeds to human review
# Non-A grades trigger intelligent retry with "Wait" pattern reflection

from atlas.pipelines.activity_conversion import ActivityConversionPipeline

pipeline = ActivityConversionPipeline()
result = await pipeline.convert_with_retry("tummy-time", max_retries=2)
# Uses Wait pattern (89.3% blind spot reduction) between retries
```
