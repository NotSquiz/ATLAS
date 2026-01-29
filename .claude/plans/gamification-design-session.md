# ATLAS Gamification Design Session

**Date:** January 22, 2026
**Status:** Planning Phase Complete - Awaiting Deep Research Results
**Next Step:** Review "Lethal Gentleman" research, finalize skill system, begin Phase 1 implementation

---

## Session Summary (Updated)

### What We Built (MVP Backend) - COMPLETE
- ✅ OSRS level calculator (`atlas/gamification/level_calculator.py`)
- ✅ XP service with async/fail-safe pattern (`atlas/gamification/xp_service.py`)
- ✅ Database schema (`atlas/memory/schema_gamification.sql`)
- ✅ XP hooks in 6 health services
- ✅ Voice intent: "what's my XP" / "skill status"
- ✅ 57 unit tests passing

### Planning Documentation Created - COMPLETE
| Document | Location | Purpose |
|----------|----------|---------|
| PWA Architecture | `docs/PWA_ARCHITECTURE.md` | Stack, structure, data flow (~480 lines) |
| OSRS Design System | `docs/OSRS_DESIGN_SYSTEM.md` | Colors, fonts, components (~450 lines) |
| Testing Strategy | `docs/TESTING_STRATEGY.md` | Vitest, Playwright, AI feedback (~600 lines) |
| API Specification | `docs/API_SPECIFICATION.md` | FastAPI endpoints, SSE events (~450 lines) |
| Skill System Design | `docs/SKILL_SYSTEM_DESIGN.md` | Skills, virtues, XP sources (~400 lines) |
| Implementation Plan | `.claude/plans/pwa-implementation.md` | 6-phase build plan (~350 lines) |

### Research Completed
Three Opus research agents returned results (saved to `docs/OSRS/`):
1. **PWA Architecture 2026.md** - Stack confirmed: Vite + React + SSE (not WebSocket)
2. **OSRS Visual Design System.md** - Font correction: NOT Press Start 2P, use RuneStar/Pixelify Sans
3. **React PWA Testing 2026.md** - Playwright + Vitest + state dumps for AI feedback

### Verification Completed
Three Opus verification agents reviewed the 9-skill system:

| Agent | Key Finding |
|-------|-------------|
| **Inversion Test** | Risk of system becoming master; missing domains (Learning, Play); 9 skills at upper limit |
| **Philosophy Expert** | REFLECTION IS MISSING - critical for Stoicism/Musashi; Courage under-captured |
| **Behavioral Psychology** | Fix streak mechanics (rolling windows); need rest day design; overjustification risk |

**Consensus across all three:**
- Add Reflection/Wisdom skill (self-examination)
- Use rolling windows not consecutive streaks
- Design rest days as strategic, not failure
- Expand Presence → broader Contribution?

---

## Awaiting: "The Lethal Gentleman" Research

Sent comprehensive research prompt to Opus Research Agent exploring:
- Historical archetypes of admirable men (Alexander, Caesar, Musashi, Marcus Aurelius)
- Stoic virtues and Bushido principles
- The "lethal gentleman" concept - dangerous but controlled
- Fatherhood as the ultimate test
- Gamification without dark patterns
- Daily practices of history's greatest

**Prompt saved at:** `docs/OSRS/research-prompt-lethal-gentleman.md`
**Expected deliverables:**
1. The Timeless Virtues (8-12 cross-cultural essentials)
2. The Lethal Gentleman Skill Tree
3. Daily Practice Protocol mapped to XP
4. The Failure Codex (handling bad days)
5. Red Lines (what NOT to gamify)
6. The Ultimate Question (who you become after 10 years)

---

## Architecture Decision: PWA - CONFIRMED

### Stack Finalized
```
Frontend: Vite 6.x + React 18/19 + Tailwind + shadcn/ui + Framer Motion
State:    TanStack Query (server) + Zustand (client)
Real-time: Server-Sent Events (NOT WebSocket - simpler, auto-reconnect)
Backend:  FastAPI (Python) reading existing SQLite
PWA:      vite-plugin-pwa with Workbox
Testing:  Playwright (E2E) + Vitest (unit) + state dumps (AI feedback)
```

### Key Architecture Insights from Research
- **SSE over WebSocket:** Better for one-way XP notifications, handles laptop sleep/wake
- **Latency:** ~700ms voice→UI (well under 1-2s target)
- **State dumps:** JSON exports for Claude to verify, not screenshots
- **Font correction:** RuneStar or Pixelify Sans, NOT Press Start 2P

---

## Skill System: Current Proposal (9 Skills)

| Skill | Domain | Virtue | XP Sources |
|-------|--------|--------|------------|
| Strength | Body | Power | Weight training |
| Endurance | Body | Grit | Cardio, long efforts |
| Mobility | Body | Readiness | Morning routine |
| Nutrition | Body | Temperance | Clean eating, protein |
| Recovery | Body | Wisdom (rest) | Sleep, rest days, cold/heat |
| Focus | Mind | Clarity | Deep work, no distractions |
| Presence | People | Justice | Dad time, family |
| Creation | Work | Courage | Building, shipping |
| Consistency | Meta | Discipline | Daily streaks |

### Decisions Pending (Post-Research)

| Question | Options | Leaning |
|----------|---------|---------|
| **10th skill: Reflection?** | Yes (Seneca/Musashi) or fold into Focus | Yes - add it |
| **Presence scope?** | Family only OR broader "Contribution" | Undecided |
| **Streak mechanics?** | Consecutive days OR rolling windows (5/7) | Rolling windows |
| **Rest day XP?** | Penalty OR strategic (earn XP for resting well) | Strategic |
| **Courage tracking?** | Own skill OR fold into Creation/others | Fold into others |

---

## Key Corrections from Research

### Font (CRITICAL)
- ❌ ~~Press Start 2P~~ - 1980s Namco arcade font, NOT OSRS
- ✅ RuneStar Fonts (CC0) - exact OSRS recreation
- ✅ Pixelify Sans (Google Fonts) - best alternative

### Real-time Updates
- ❌ ~~WebSocket~~ - overkill for one-way notifications
- ✅ SSE (Server-Sent Events) - simpler, auto-reconnect

### Testing Strategy
- ❌ ~~Screenshots for AI~~ - slow, imprecise
- ✅ State file dumps (JSON) - instant, structured, parseable

---

## Assets Needed (Midjourney)

User has Midjourney subscription. Prompts included in `docs/OSRS_DESIGN_SYSTEM.md`:
- 9 skill icons (32x32 pixel art)
- PWA app icons (192x192, 512x512)

---

## Philosophy Grounding

### The Core Question
"Gamify the man I want to become" - not productivity theater, but character development.

### The Archetype: Lethal Gentleman
- Dangerous but controlled
- Strong but gentle
- Driven but present
- Disciplined but alive
- Sharp fangs and claws, sheathed by choice

### Philosophical Foundations
- **Stoicism:** Four virtues (Wisdom, Courage, Justice, Temperance)
- **Musashi:** Constant practice, accept death, no wasted movement
- **Crossover:** Practice > theory, focus on what you control, memento mori

---

## Implementation Phases (Summary)

| Phase | Focus | Key Deliverable |
|-------|-------|-----------------|
| 1 | FastAPI Backend | API serving skill data from existing SQLite |
| 2 | React PWA Foundation | Vite + React + PWA config connected to API |
| 3 | Core UI Components | OSRS-styled skill cards, XP bars, panels |
| 4 | Real-Time Updates | SSE connection, live XP updates |
| 5 | Level-Up Celebration | Banner, particles, sound |
| 6 | Quest System + Polish | Quests, offline, settings |

Full details in `.claude/plans/pwa-implementation.md`

---

## Files Created This Session

| File | Purpose |
|------|---------|
| `docs/PWA_ARCHITECTURE.md` | Complete architecture specification |
| `docs/OSRS_DESIGN_SYSTEM.md` | Visual design system with corrections |
| `docs/TESTING_STRATEGY.md` | Testing approach for AI-assisted development |
| `docs/API_SPECIFICATION.md` | FastAPI endpoints and SSE events |
| `docs/SKILL_SYSTEM_DESIGN.md` | Skill definitions, virtues, XP sources |
| `.claude/plans/pwa-implementation.md` | 6-phase implementation plan |
| `docs/OSRS/research-prompt-lethal-gentleman.md` | Deep research prompt |

---

## Research Documents (from Opus)

| File | Key Insights |
|------|--------------|
| `docs/OSRS/PWA Architecture 2026.md` | Vite confirmed, SSE over WS, ~700ms latency |
| `docs/OSRS/OSRS Visual Design System.md` | Font correction, beveled borders, zero radius |
| `docs/OSRS/React PWA Testing 2026.md` | State dumps, Playwright, Ralph Wiggum loop |
| `docs/OSRS/Visual Feedback and Testing.md` | Original (for CustomTkinter - superseded) |
| `docs/OSRS/research-prompts.md` | The 3 research prompts sent |

---

## To Resume After Compact

1. **Check for Lethal Gentleman research** in `docs/OSRS/`
2. **Read skill system verification results** (summarized above)
3. **Finalize skill decisions:**
   - 9 or 10 skills?
   - Reflection as separate skill?
   - Presence scope?
4. **Begin Phase 1:** Scaffold FastAPI backend
5. **Create Midjourney assets:** Skill icons

---

## Key Decisions Made

1. ✅ PWA architecture (vs CustomTkinter)
2. ✅ Vite + React + FastAPI stack
3. ✅ SSE for real-time (not WebSocket)
4. ✅ Font: RuneStar/Pixelify Sans (NOT Press Start 2P)
5. ✅ Testing: Playwright + Vitest + state dumps
6. ✅ Skills mapped to virtues (Stoicism/Musashi)
7. ✅ "Lethal Gentleman" as guiding archetype
8. 🔄 Skill count: 9 or 10 (pending research)
9. 🔄 Streak mechanics: rolling windows vs consecutive
10. 🔄 Rest day design: strategic vs penalty

---

## Verification Agent Quotes (Key Insights)

**Inversion Test:**
> "You might build an extremely effective system for becoming someone you don't actually want to be."

**Philosophy Expert:**
> "The system should be understood as scaffolding, not structure. The moment you confuse the XP with the life, burn the system down."

**Behavioral Psychology:**
> "On my worst day, does this mechanic help me or judge me? If the answer is ever 'judge,' redesign that component."
