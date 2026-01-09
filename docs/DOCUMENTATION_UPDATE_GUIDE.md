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
