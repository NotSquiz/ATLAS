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
| BBWarmingService | V2 Guide Section 13 (Baby Brains) |
| BBCommentGenerator | V2 Guide Section 13 (Baby Brains) |
| BBTranscriptFetcher | V2 Guide Section 13 (Baby Brains) |
| BBTargetScorer | V2 Guide Section 13 (Baby Brains) |
| BBVoiceSpec | V2 Guide Section 13 (Baby Brains) |
| BBCrossRepoSearch | V2 Guide Section 13 (Baby Brains) |
| BBDatabase | V2 Guide Section 13 (Baby Brains) |
| BBCLI | V2 Guide Section 13 (Baby Brains) |
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

## Agent Knowledge Base (January 30, 2026)

| Path | Purpose | When to Update |
|------|---------|----------------|
| `docs/research/AGENT_KNOWLEDGE_BASE.md` | Structured intake of 17 sources: 284 items, 49 patterns, cross-references | New sources (S18+), Phase 2 synthesis, Phase 3 architecture |

### Knowledge Base Contents
- **17 sources (S1-S17):** Practitioner articles, academic survey, GitHub projects, Reddit posts
- **284 extracted items** with category tags (ARCH, SECURITY, MEMORY, etc.) and relevance ratings
- **49 patterns** cross-referenced across sources
- **Per-source:** Items table, key patterns, cross-references, action items, credibility assessment
- **Architecture decisions logged:** D96-D99

### Key Findings for Architecture
| Finding | Source | Decision |
|---------|--------|----------|
| Dual-agent architecture (Personal + Baby Brains) | S14, S16 | D97 |
| FSRS-6 memory decay over flat storage | S17 (Vestige) | D98 |
| Hybrid planning validated (ReWOO + ReAct + Plan-and-Execute) | S14 | D99 |
| Circuit breaker + fallback chains for resilience | S16 (BrainPro) | Pending implementation |
| Privacy tiers for model routing | S16 (BrainPro) | Pending implementation |

## Baby Brains Agent Documentation

| Path | Purpose | When to Update |
|------|---------|----------------|
| `docs/BABY-BRAINS-LAUNCH-STRATEGY-JAN2026.md` | 4-week launch plan with day-by-day tasks | Strategy changes, milestone completions |
| `skills/babybrains/BABYBRAINS.md` | 9-skill content pipeline orchestrator | Pipeline changes |

### Baby Brains Build Status (January 30, 2026)
| Task | Status | Tracker ID |
|------|--------|------------|
| Account warming automation (foundation) | ✅ WEEK 1 DONE (S1.1-S1.8, 98 tests) | bb-1 |
| Account warming automation (browser) | PENDING (S2.1-S2.3) | bb-1b |
| Trend engine (YouTube + Grok) | PENDING (S2.4-S2.6) | bb-2 |
| Content production pipeline | PENDING (S3.1-S3.4) | bb-3 |
| Website relaunch | PENDING | bb-4 |
| Article/SEO/GEO pipeline | PENDING | bb-5 |

## Checklist for OSRS UI Changes

- [ ] Update `.claude/plans/osrs-command-centre.md` with phase progress
- [ ] Run `pytest tests/ui/` to verify state export
- [ ] Run `pytest tests/gamification/` for XP integration
- [ ] Update `docs/OSRS/UI_DEVELOPMENT_SETUP.md` if dev workflow changes
- [ ] Screenshot before/after for visual changes
- [ ] Update sprite mappings in plan if changed
