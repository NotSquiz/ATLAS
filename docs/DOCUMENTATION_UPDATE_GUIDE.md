# ATLAS Documentation Update Guide

**When making changes to ATLAS, update these documents:**

## Always Update

| Change Type | Update These |
|-------------|--------------|
| New orchestrator component | `CLAUDE.md`, `V2_ORCHESTRATOR_GUIDE.md` |
| New infrastructure | `CLAUDE.md`, `V2_ORCHESTRATOR_GUIDE.md` |
| Architecture decision | `DECISIONS.md` |
| Completion of planned work | `TECHNICAL_STATUS.md`, `.claude/atlas-progress.json` |
| Session end | `.claude/handoff.md` |
| New workflow/skill | `.claude/skills/<name>.md` |
| New agent prompt | `.claude/agents/<name>.md` |
| New coding standard | `.claude/rules/<name>.md` |

## Document Locations

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| `CLAUDE.md` | Agent context (auto-loaded) | Every new component |
| `docs/V2_ORCHESTRATOR_GUIDE.md` | How to use V2 components | Every new feature |
| `docs/TECHNICAL_STATUS.md` | Implementation status | Phase completions |
| `docs/DECISIONS.md` | Architecture decisions | New decisions |
| `docs/ATLAS_ARCHITECTURE_V2.md` | Design specs | Major changes |
| `.claude/handoff.md` | Session transitions | Every session end |
| `.claude/atlas-progress.json` | Task tracking | Task status changes |

## Claude Code Infrastructure (.claude/)

| Path | Purpose | When to Update |
|------|---------|----------------|
| `.claude/agents/planner.md` | Feature planning prompts | New planning patterns |
| `.claude/agents/code-reviewer.md` | Code review prompts | New review criteria |
| `.claude/agents/security-reviewer.md` | Security audit prompts | New security rules |
| `.claude/agents/activity-auditor.md` | Baby Brains QC prompts | QC criteria changes |
| `.claude/agents/test-writer.md` | TDD assistance prompts | Testing patterns |
| `.claude/skills/tdd-workflow.md` | TDD workflow guide | Process changes |
| `.claude/skills/activity-pipeline.md` | Activity conversion flow | Pipeline changes |
| `.claude/skills/health-assessment.md` | Health tracking flow | Health feature changes |
| `.claude/skills/pr-review.md` | PR review checklist | Review process changes |
| `.claude/rules/atlas-conventions.md` | Project coding standards | Convention changes |
| `.claude/rules/security.md` | Security requirements | New security rules |
| `.claude/rules/coding-style.md` | Python style guide | Style changes |
| `.claude/rules/testing.md` | Test requirements | Testing standards |

## Checklist for New Components

- [ ] Add to `CLAUDE.md` component table
- [ ] Add section to `V2_ORCHESTRATOR_GUIDE.md` with usage examples
- [ ] Update `TECHNICAL_STATUS.md` if completing planned work
- [ ] Add to `DECISIONS.md` if architectural choice was made
- [ ] Commit with descriptive message

## Current Components (January 2026)

| Component | Documented In |
|-----------|---------------|
| SkillLoader | V2 Guide Section 4 |
| SubAgentExecutor | V2 Guide Section 1 |
| HookRunner | V2 Guide Section 2 |
| SessionManager | V2 Guide Section 3 |
| ScratchPad | V2 Guide Section 5 |
| ConfidenceRouter | V2 Guide Section 6 |
| Sandboxing | V2 Guide Section 7 |
| Session Handoff | V2 Guide Section 8 |
| Quality Audit Pipeline | V2 Guide Section 9 |
| CodeSimplifier | V2 Guide Section 10 |
| 2nd Brain / ThoughtClassifier | V2 Guide Section 11 |
| Voice API Pipeline | V2 Guide Section 11 |
| InteractiveWorkoutTimer | V2 Guide Section 12 |
| AssessmentProtocolRunner | CLAUDE.md Voice API |
| NumberParser | CLAUDE.md Voice API |
| Garmin Activity Sync | CLAUDE.md Garmin Integration |
| StateModels | CLAUDE.md V2 Components |
| TimerBuilders | CLAUDE.md V2 Components |
| IntentDispatcher | CLAUDE.md V2 Components |
| IntentPatterns | CLAUDE.md V2 Components |
| Qwen3TTS | V2 Guide Section 11 (Voice API) |
| XPService (Octalysis) | `atlas/gamification/xp_service.py` |
| OSRS Command Centre | `.claude/plans/osrs-command-centre.md` |

## OSRS Command Centre UI (In Progress)

| Path | Purpose | When to Update |
|------|---------|----------------|
| `.claude/plans/osrs-command-centre.md` | 5-phase implementation plan | Phase completions |
| `docs/OSRS/UI_DEVELOPMENT_SETUP.md` | Dev tools and testing setup | Tool changes |
| `docs/OSRS/Visual Feedback and Testing.md` | Autonomous iteration workflow | Workflow changes |
| `docs/OSRS/OSRS Visual Design System.md` | Colors, fonts, styling | Design decisions |
| `docs/OSRS/Octalysis - Research Synthesis.md` | Gamification framework | XP economy changes |

## Development Tools

| Path | Purpose | When to Update |
|------|---------|----------------|
| `dev_tools/hot_reload.py` | Auto-restart on file changes | Tool improvements |
| `dev_tools/state_exporter.py` | Export UI state to JSON | State schema changes |
| `dev_tools/capture_screen.ps1` | Windows screenshot capture | Screenshot workflow |
| `tests/fixtures/db_states.py` | Database test fixtures | New test scenarios |
| `tests/ui/test_state_export.py` | UI state verification tests | New UI components |

## Gamification System

| Path | Purpose | When to Update |
|------|---------|----------------|
| `atlas/gamification/xp_service.py` | XP awards, skills, Octalysis titles | XP economy changes |
| `atlas/gamification/level_calculator.py` | OSRS XP curve formulas | Level calculations |
| `atlas/memory/schema_gamification.sql` | Database schema | New tables/columns |
| `tests/gamification/test_xp_service.py` | 80 gamification tests | New features |

## Research Prompts

| Path | Purpose | When to Update |
|------|---------|----------------|
| `.claude/research-prompts/quest-system-design.md` | Quest/todo gamification design | Quest feature changes |

## Strategic Research

| Path | Purpose | When to Update |
|------|---------|----------------|
| `docs/research/R31.Personal AI Assistant Landscape January 2026 - Clawdbot Era.md` | Comprehensive analysis of Clawdbot, personal AI trends, Love Equation, ATLAS 3.0 strategy | New landscape discoveries |
| `.claude/plans/transient-rolling-hamming.md` | Active strategic plan for ATLAS 3.0 evolution | Implementation progress |

### R31 Contents (January 2026)
- Clawdbot phenomenon analysis (9.7k GitHub stars, viral use cases)
- Competitive landscape (Clawdbot, Lindy, Dume.ai, Claude Code)
- Useful skills (/last30days, WooYun Legacy security)
- Levangie Labs cognitive architecture (CAF, episodic memory)
- Brian Roemmele's Love Equation (dE/dt = β(C-D)E)
- Security architecture for MCP/Skills
- ATLAS 3.0 strategic plan (5 phases)
- 90-day implementation roadmap

## Checklist for OSRS UI Changes

- [ ] Update `.claude/plans/osrs-command-centre.md` with phase progress
- [ ] Run `pytest tests/ui/` to verify state export
- [ ] Run `pytest tests/gamification/` for XP integration
- [ ] Update `docs/OSRS/UI_DEVELOPMENT_SETUP.md` if dev workflow changes
- [ ] Screenshot before/after for visual changes
- [ ] Update sprite mappings in plan if changed
