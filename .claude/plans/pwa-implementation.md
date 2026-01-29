# ATLAS Command Centre PWA - Implementation Plan

**Version:** 1.0
**Date:** January 2026
**Status:** Ready to Execute

---

## Overview

Phased implementation of the OSRS-inspired gamification PWA. Building on the existing MVP backend (gamification tables + XP service already implemented).

**Total Estimated Phases:** 6
**Approach:** Incremental, testable milestones

---

## Pre-Implementation Checklist

### Assets to Prepare (Before Phase 1)

- [ ] **Fonts:** Download RuneStar fonts OR configure Pixelify Sans
- [ ] **Skill Icons:** Generate 9 icons via Midjourney (32x32 pixel art)
- [ ] **Sounds:** Source/create level-up jingle + XP chime (JSFXR or Kenney)
- [ ] **PWA Icons:** Create 192x192 and 512x512 app icons
- [ ] **Color palette:** Validate OSRS hex values in Tailwind config

### Development Environment

- [ ] Node 20+ installed
- [ ] pnpm installed (`npm install -g pnpm`)
- [ ] Vite project scaffolded
- [ ] FastAPI backend running (reads existing SQLite)

---

## Phase 1: Project Scaffold + FastAPI Backend

**Goal:** Working API serving skill data from existing SQLite

### Tasks

1. **Create project structure**
   ```bash
   mkdir atlas-command-centre
   cd atlas-command-centre
   mkdir backend frontend scripts tests
   ```

2. **FastAPI backend setup**
   - [ ] `backend/app/main.py` - FastAPI app with CORS
   - [ ] `backend/app/api/routes.py` - REST endpoints
   - [ ] `backend/app/models/database.py` - SQLite connection
   - [ ] `backend/app/models/schemas.py` - Pydantic models
   - [ ] `backend/requirements.txt` - Dependencies

3. **Implement core endpoints**
   - [ ] `GET /api/skills` - All skills with levels
   - [ ] `GET /api/skills/{name}` - Single skill detail
   - [ ] `GET /api/stats/today` - Today's XP summary
   - [ ] `GET /api/config` - App configuration

4. **Verify against existing data**
   ```bash
   # Start FastAPI
   uvicorn backend.app.main:app --reload

   # Test endpoints
   curl http://localhost:8000/api/skills
   ```

### Deliverables
- FastAPI serving skill data from `~/.atlas/atlas.db`
- Pydantic models matching API specification
- Basic test coverage for endpoints

### Verification
```bash
# API returns skill data
curl http://localhost:8000/api/skills | jq '.skills | length'
# Should return: 7 (or 9 if expanded)
```

---

## Phase 2: React PWA Foundation

**Goal:** Vite + React app with PWA config, connecting to FastAPI

### Tasks

1. **Scaffold Vite project**
   ```bash
   cd frontend
   pnpm create vite . --template react-ts
   pnpm install
   ```

2. **Install dependencies**
   ```bash
   pnpm add @tanstack/react-query zustand framer-motion
   pnpm add -D tailwindcss postcss autoprefixer vite-plugin-pwa
   ```

3. **Configure Tailwind with OSRS colors**
   - [ ] `tailwind.config.ts` - OSRS color palette
   - [ ] `src/styles/globals.css` - Base styles + font imports

4. **Configure PWA plugin**
   - [ ] `vite.config.ts` - PWA manifest + Workbox config
   - [ ] PWA icons in `public/icons/`

5. **Setup state management**
   - [ ] `src/api/client.ts` - API client setup
   - [ ] `src/api/hooks.ts` - TanStack Query hooks
   - [ ] `src/stores/gameStore.ts` - Zustand store

6. **Create basic layout**
   - [ ] `src/App.tsx` - Router + providers
   - [ ] `src/components/layout/Header.tsx`
   - [ ] `src/components/layout/Sidebar.tsx`
   - [ ] `src/pages/Dashboard.tsx` - Placeholder

### Deliverables
- Working Vite dev server
- TanStack Query fetching from FastAPI
- PWA installable (manifest valid)
- Basic layout structure

### Verification
```bash
# Dev server starts
pnpm dev

# PWA manifest valid
curl http://localhost:5173/manifest.json | jq '.name'

# API connection works (check browser devtools)
```

---

## Phase 3: Core UI Components

**Goal:** OSRS-styled skill cards, XP bars, panels

### Tasks

1. **OSRS Panel component**
   - [ ] `src/components/osrs/Panel.tsx` - Beveled border effect
   - [ ] Light and dark variants

2. **Skill Card component**
   - [ ] `src/components/osrs/SkillCard.tsx`
   - [ ] Icon + name + level + XP bar
   - [ ] Hover effects

3. **XP Progress Bar component**
   - [ ] `src/components/osrs/XPBar.tsx`
   - [ ] Green fill, dark background
   - [ ] XP text overlay

4. **Skills Grid**
   - [ ] `src/components/osrs/SkillsGrid.tsx`
   - [ ] 3-column layout (or responsive)

5. **Dashboard page**
   - [ ] `src/pages/Dashboard.tsx`
   - [ ] Header with total level + today's XP
   - [ ] Skills grid

6. **Storybook setup**
   ```bash
   pnpm add -D @storybook/react-vite
   npx storybook init
   ```
   - [ ] Stories for Panel, SkillCard, XPBar

### Deliverables
- All OSRS components working
- Storybook with component documentation
- Dashboard displaying real skill data

### Verification
- Visual inspection in browser
- Storybook running: `pnpm storybook`
- Components match design system spec

---

## Phase 4: Real-Time Updates (SSE)

**Goal:** Live XP updates from voice pipeline

### Tasks

1. **FastAPI SSE endpoint**
   - [ ] `backend/app/api/events.py` - SSE endpoint
   - [ ] `backend/app/services/xp_watcher.py` - Poll xp_events table

2. **React SSE hook**
   - [ ] `src/hooks/useSSE.ts` - EventSource with reconnection
   - [ ] Handle visibility change (laptop wake)

3. **TanStack Query integration**
   - [ ] Update cache on SSE events
   - [ ] Optimistic updates

4. **Connection status indicator**
   - [ ] `src/components/layout/ConnectionStatus.tsx`
   - [ ] Show connected/disconnected state

5. **XP toast notifications**
   - [ ] `src/components/osrs/XPToast.tsx`
   - [ ] "+150 Strength XP" style notification

### Deliverables
- SSE connection working
- XP updates appear within 1-2 seconds
- Connection status visible

### Verification
```bash
# Award XP via CLI
python -m atlas.gamification.xp_service --award strength 100 manual_test

# Watch PWA update in real-time
```

---

## Phase 5: Level-Up Celebration

**Goal:** The iconic OSRS level-up banner with sound and particles

### Tasks

1. **Level-up banner component**
   - [ ] `src/components/osrs/LevelUpBanner.tsx`
   - [ ] Framer Motion animations
   - [ ] Skill icon + level number

2. **Particle effects**
   - [ ] Install tsParticles: `pnpm add tsparticles react-particles`
   - [ ] Lazy-load fireworks preset
   - [ ] Trigger on level-up

3. **Sound system**
   - [ ] `src/lib/sounds.ts` - Audio manager
   - [ ] Level-up sound file
   - [ ] Respect mute setting

4. **Level-up queue**
   - [ ] Zustand: `levelUpQueue` array
   - [ ] Process one at a time
   - [ ] Auto-dismiss after animation

5. **SSE integration**
   - [ ] Detect `level_up: true` in events
   - [ ] Trigger celebration

### Deliverables
- Level-up banner appears on level-up
- Particles + sound play
- Multiple level-ups queue correctly

### Verification
```bash
# Trigger level-up via CLI (award enough XP)
python -m atlas.gamification.xp_service --award strength 5000 test

# Watch celebration in PWA
```

---

## Phase 6: Quest System + Polish

**Goal:** Quest tracking, achievements, offline support, final polish

### Tasks

1. **Quest endpoints**
   - [ ] `GET /api/quests` - All quests with progress
   - [ ] Quest progress SSE events

2. **Quest list component**
   - [ ] `src/components/osrs/QuestList.tsx`
   - [ ] `src/components/osrs/QuestItem.tsx`
   - [ ] Daily/weekly tabs

3. **Quest completion celebration**
   - [ ] Similar to level-up but smaller
   - [ ] "+300 XP" notification

4. **Achievements page**
   - [ ] `src/pages/Achievements.tsx`
   - [ ] Achievement grid with unlock status

5. **Offline support**
   - [ ] `src/components/layout/OfflineBanner.tsx`
   - [ ] Service worker caching verified
   - [ ] Graceful degradation

6. **Settings page**
   - [ ] `src/pages/Settings.tsx`
   - [ ] Sound toggle
   - [ ] Theme toggle (light/dark OSRS)

7. **PWA install prompt**
   - [ ] `src/hooks/useInstallPrompt.ts`
   - [ ] Custom install button

8. **Performance audit**
   - [ ] Lighthouse CI passing
   - [ ] Bundle size check
   - [ ] Memory leak test

### Deliverables
- Complete quest system
- Offline mode working
- PWA installable with custom prompt
- Lighthouse score 90+

### Verification
```bash
# Lighthouse audit
pnpm build
pnpm preview
npx lighthouse http://localhost:4173 --view

# Offline test
# 1. Install PWA
# 2. Stop FastAPI
# 3. Verify cached data displays
```

---

## Post-MVP: Future Enhancements

### Phase 7+: Advanced Features (Not in MVP)

- [ ] Skill detail pages with history
- [ ] XP rate graphs (daily/weekly/monthly)
- [ ] Achievement notifications
- [ ] Multiple themes
- [ ] Export/backup data
- [ ] Custom skill configuration (for other users)

---

## Testing Milestones

### After Phase 2
```bash
pnpm test        # Unit tests pass
pnpm e2e         # Basic E2E passes
```

### After Phase 4
```bash
pnpm e2e         # SSE tests pass
# Manual: Voice command → PWA updates
```

### After Phase 6
```bash
pnpm test        # All unit tests
pnpm e2e         # All E2E tests
pnpm lighthouse  # PWA score 90+
```

---

## Definition of Done (MVP)

- [ ] Dashboard shows all skills with real data
- [ ] XP updates appear within 1-2 seconds of voice command
- [ ] Level-up celebration plays with sound + particles
- [ ] Quest list shows daily/weekly quests
- [ ] Works offline (cached data)
- [ ] Installable as desktop app
- [ ] Lighthouse PWA score 90+
- [ ] All tests passing

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| WSL2 networking issues | Test early, document fallbacks |
| SQLite locking | WAL mode already enabled, short connections |
| Font rendering differences | Docker for visual regression |
| Memory pressure (animations) | Lazy-load particles, limit count |
| SSE disconnection | Auto-reconnect with lastEventId |

---

## Session Workflow

When starting a session:

1. **Read handoff:** `.claude/handoff.md`
2. **Check progress:** `.claude/atlas-progress.json`
3. **Read relevant docs:**
   - `docs/PWA_ARCHITECTURE.md`
   - `docs/OSRS_DESIGN_SYSTEM.md`
   - `docs/API_SPECIFICATION.md`
4. **Pick up where left off**
5. **Update handoff when done**

---

## Quick Reference

### Start Development
```bash
# Terminal 1: FastAPI
cd atlas-command-centre/backend
uvicorn app.main:app --reload

# Terminal 2: Vite
cd atlas-command-centre/frontend
pnpm dev
```

### Run Tests
```bash
pnpm test          # Unit tests
pnpm e2e           # E2E tests
pnpm storybook     # Component dev
```

### Build Production
```bash
cd frontend && pnpm build
cp -r dist/* ../backend/app/static/
cd ../backend && uvicorn app.main:app
```

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `docs/PWA_ARCHITECTURE.md` | Stack, structure, data flow |
| `docs/OSRS_DESIGN_SYSTEM.md` | Colors, fonts, components |
| `docs/TESTING_STRATEGY.md` | Vitest, Playwright, AI patterns |
| `docs/API_SPECIFICATION.md` | FastAPI endpoints, SSE events |
| `docs/SKILL_SYSTEM_DESIGN.md` | Skill definitions, XP values |
| `.claude/plans/pwa-implementation.md` | This file |
| `docs/OSRS/` | Opus research documents |
