# CRITICAL STATE (injected into every session)

## Canonical Values
- Incubation duration: **7 DAYS** (not 21). Source: warming_schedule.json
- Intelligence engine: **Grok** (not YouTube). YouTube is video discovery only.
- Grok model: **grok-3-fast**. Cost: $0.20/$0.50 per M tokens + $5/1K search calls.
- YouTube ToS: NO cross-channel aggregation, NO derived metrics from API data.

## Active Sprint: Sprint 1
- Order: S0.1 → S2.1 → S2.2 → S2.3 → S2.BF1 → V0.1 → V0.2 → M1
- Plan: /home/squiz/code/babybrains-os/docs/automation/SPRINT_PLAN_V3.md
- DO NOT modify completed files: youtube_client.py, grok_client.py (audited)
- DEFERRED: A61, S2.6-full, Quorum Voting (Month 2+, data-driven triggers)

## Rules (Always Apply)
- All I/O must be async
- Parameterized SQL queries only
- Multi-file changes: grep ALL files referencing changed values
- Self-review degrades quality (P54) — spawn independent critic for significant work
- Run tests before committing

## Anti-Patterns From Recent Sessions
- Changing a value in ONE file without checking all references
- Using "21 days" for incubation (correct: 7 days)
- Writing YouTube ToS-violating cross-source rankings

## Cross-Repo Note
- Hooks only fire for ATLAS repo work
- When editing babybrains-os files, manually check propagation
- babybrains-os docs path: /home/squiz/code/babybrains-os/docs/automation/

<!-- Last verified: 2026-01-31T23:39:44Z -->
