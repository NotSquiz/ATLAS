# Knowledge Base Changelog

## 2026-01-31 — v1.3 (S18-S20 Added)

### Added
- S18: Claude Cowork Plugins (Anthropic product launch, 14 items, P50-P51)
- S19: Agentic Image Generation (Nano Banana + Agentic Vision, 12 items, P52)
- S20: Team of Rivals + Swarm Intelligence (16 items, P53-P55)
- 7 new patterns: P50-P55 + P52
- 12 new action items: A53-A64
- A61 elevated to P0 (independent critic agent — self-review degrades quality)

### Updated
- P6 promoted to Tier 1 (4 sources, was 3) — S20 remote code execution validates
- P14 promoted to Tier 1 (4 sources, was 3) — S18 skills = passive context
- P38 promoted to Tier 2 (3 sources, was 2) — S20 Swiss Cheese Model
- P19, P40 promoted to Tier 2 (3 sources each)
- P8, P17, P44, P45 convergence increased
- ACTIONS.md: 52→64 actions, 12→13 P0 critical

---

## 2026-01-31 — v1.2 (S18 Added)

### Added
- S18: Claude Cowork Plugins (Anthropic product launch + open-source repo, Jan 30 2026)
- P50: Plugin Architecture = Canonical Agent Customization (NEW)
- P51: Dynamic Tool Loading / MCP Tool Search (NEW)
- A53-A56: Four new action items (plugin architecture, MCP Tool Search, plugin study, BB plugin)

### Updated
- P14 promoted to Tier 1 (4 sources, was 3) — S18 validates skills = passive context
- P19 promoted to Tier 2 (3 sources, was 2) — sub-agent scoped permissions
- P40 promoted to Tier 2 (3 sources, was 2) — slash commands as single triggers
- P8, P17, P44, P45 convergence updated (+S18)
- ACTIONS.md summary and domain dashboard updated (52→56 actions)

---

## 2026-01-31 — v1.1 (Index Overhaul)

### Structural
- Split monolithic file (2,546 lines) into hub-and-spoke architecture
- 17 individual source files in `sources/`
- Consolidated PATTERNS.md (49 patterns), ACTIONS.md (52 actions), SYNTHESIS.md (8 themes)
- Signal Heatmap with composite scoring (38 items scored)
- Source intake template with verification checklist
- Generated README dashboard

### Added
- Signal scoring formula: `(R×0.30) + (C×0.25) + (Q×0.25) + (V×0.20)`
- Security override floor (Signal >= 7.0 for credible SECURITY items)
- Action item IDs (A01-A52) with dependencies and status tracking
- Credibility scoring rubric (5 dimensions, 1-10 each)
- Verification gate for HIGH-relevance items

---

## 2026-01-30 — v1.0 (Initial Build)

### Added
- S1-S17: 17 sources processed (284 items extracted)
- P1-P49: 49 patterns identified
- Phase 2 Synthesis: 8 themes, convergence map, 4 contradictions resolved
- Build order mapped to Baby Brains execution priorities

### Status
- Phase 1 (Intake): COMPLETE for S1-S17
- Phase 2 (Synthesis): COMPLETE
- Phase 3 (Architecture Decisions): Ready when needed
