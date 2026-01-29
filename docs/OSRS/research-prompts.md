# Opus Research Prompts for ATLAS Gamification PWA

Save each research result to `docs/OSRS/` with the suggested filename.

---

## Research Prompt 1: PWA Architecture 2026

**Save result as:** `docs/OSRS/PWA Architecture 2026.md`

```
# Research Request: PWA Architecture for Local-First Gamification Dashboard (2026)

## Context

I'm building a gamification dashboard PWA called "ATLAS Command Centre" with the following characteristics:

- **Primary use:** Personal health/fitness tracking with Old School RuneScape-inspired XP and leveling
- **Data source:** Existing SQLite database on local machine (~/.atlas/atlas.db)
- **Backend:** FastAPI (Python) running locally on WSL2
- **Frontend:** React-based PWA running in browser, installable as desktop app
- **Voice integration:** Existing voice pipeline writes XP events to SQLite; dashboard reads and displays
- **Target platform:** Windows 11 desktop (primary), with future mobile potential
- **Offline requirement:** Must work when FastAPI server is down (read-only mode acceptable)
- **Real-time need:** Level-up events should appear within 1-2 seconds of voice command

## Technical Constraints

- Hardware: ThinkPad X1 Extreme, 16GB RAM, RTX 3050 Ti 4GB (avoid memory-heavy solutions)
- Existing stack: Python 3.11, SQLite with WAL mode, WSL2 Ubuntu
- No cloud backend initially (local-first architecture)
- Single user (no auth needed initially)

## Research Questions

### 1. React Framework Selection (2026 Best Practices)

Compare for this specific use case:
- **Vite + React** vs **Next.js** vs **Remix**
- Which is best for:
  - Offline-first PWA with service worker
  - Local FastAPI backend (not serverless)
  - Desktop-app-like experience when installed
  - Bundle size (memory constrained)
  - Hot reload development experience

I'm leaning toward Vite. Validate or challenge this.

### 2. FastAPI + React Integration Patterns

- Recommended project structure (monorepo vs separate repos?)
- How should FastAPI serve the React build in production?
- CORS configuration for local development
- API client patterns: fetch vs axios vs TanStack Query
- Type sharing between Python (Pydantic) and TypeScript

### 3. Real-Time Updates Architecture

For showing level-ups and XP gains in real-time:
- **WebSocket** (FastAPI websockets) vs **Server-Sent Events** vs **Polling**
- Pros/cons for local-only app
- How to handle reconnection when laptop sleeps/wakes
- Battery/resource impact of each approach

### 4. PWA Service Worker Strategy

- **Workbox** vs custom service worker for 2026
- Caching strategy for:
  - Static assets (React bundle, fonts, icons)
  - API responses (skill levels, quest data)
  - SQLite data (can service workers access SQLite?)
- Offline fallback UI patterns
- Background sync for when server comes back online

### 5. State Management

For gamification data (skills, XP, quests, achievements):
- **Zustand** vs **Jotai** vs **TanStack Query** vs **Redux Toolkit**
- What's the 2026 consensus for this scale of app?
- How to sync server state with local optimistic updates

### 6. Local-First / Offline-First Patterns

- Is there a better pattern than "FastAPI + SQLite on server, cache in browser"?
- SQLite in browser via sql.js or wa-sqlite? (Would this help offline?)
- CRDTs or other sync patterns for local-first?
- How do apps like Obsidian or Notion handle this?

### 7. PWA Installation Experience

- manifest.json best practices for desktop-like experience
- How to prompt installation without being annoying
- Custom install button patterns
- Handling updates (when to prompt user to refresh)

## Deliverables Requested

1. **Recommended stack** with justification
2. **Project structure** (folder layout)
3. **Data flow diagram** (voice command → SQLite → FastAPI → WebSocket → React)
4. **Service worker strategy** summary
5. **Code snippets** for:
   - FastAPI WebSocket endpoint for real-time events
   - React hook for consuming WebSocket
   - Service worker registration with Workbox
6. **Potential pitfalls** specific to this architecture
7. **Resources/documentation** links for further reading
```

---

## Research Prompt 2: OSRS Visual Design System

**Save result as:** `docs/OSRS/OSRS Visual Design System.md`

```
# Research Request: Old School RuneScape Visual Design System for Web App

## Context

I'm building a gamification dashboard that uses Old School RuneScape (OSRS) as its visual inspiration. The app tracks real-life health/fitness activities and rewards them with XP, levels (1-99), skills, quests, and achievements - exactly like OSRS but for real life.

The goal is to capture the nostalgic, satisfying feel of OSRS progression without directly copying copyrighted assets.

## What I'm Building

- **Skill cards** showing 7 skills (Strength, Endurance, Mobility, Nutrition, Recovery, Consistency, Work)
- **XP progress bars** with the iconic yellow/gold fill
- **Level-up banner/modal** that appears on level-up with celebratory animation
- **Quest list** showing daily/weekly objectives
- **Achievement banners** for milestones
- **Navigation sidebar** (OSRS-style tabs)
- **Overall dark medieval aesthetic**

## Research Questions

### 1. OSRS Color Palette (Exact Values)

I need the exact hex codes used in OSRS interfaces:
- Background colors (dark browns, blacks)
- Gold/yellow for XP bars and highlights
- Text colors (white, yellow, green, red for stats)
- Border colors for panels
- Hover/active states

Provide a complete color palette I can use in Tailwind CSS config.

### 2. Typography

OSRS uses pixel fonts. For web recreation:
- **Press Start 2P** - is this the right choice for headers?
- **VT323** - is this appropriate for body text?
- Are there better alternatives that more closely match OSRS?
- What sizes work best (OSRS interface is small, but web needs larger)?
- Font loading strategy for web (FOUT, FOIT, font-display)
- Fallback stack for pixel fonts

### 3. Level-Up Animation Breakdown

The OSRS level-up is iconic. I need:
- **Timing:** How long does the animation last?
- **Sequence:** What elements appear and when?
  - Fireworks/sparkles
  - Text appearance
  - Icon/skill symbol
  - Sound timing
- **Easing curves:** What makes it feel "right"?
- **How to recreate in Framer Motion or CSS**

Provide a detailed animation specification I could implement.

### 4. UI Component Specifications

For each component, I need:
- Dimensions (or aspect ratios)
- Border styles (OSRS has distinctive beveled borders)
- Shadow/depth effects
- Spacing/padding patterns
- How corners are handled (rounded? square? beveled?)

Components:
- Skill card (showing icon, name, level, XP bar)
- XP progress bar
- Quest list item
- Achievement badge
- Tab/button
- Modal/dialog
- Tooltip

### 5. Iconography

For skill icons and UI elements:
- Where can I find OSRS-style pixel art icons (free/CC0)?
- Recommended icon packs that match the aesthetic
- Should I commission custom pixel art? (Budget-friendly options?)
- Icon sizes that work for web (16x16? 32x32? SVG?)
- Tools for creating simple pixel art icons myself

### 6. Sound Design

The OSRS level-up jingle is iconic but copyrighted. I need:
- **Legal considerations:** Can I use OSRS sounds? (Likely no)
- **Alternatives:** Where to find similar retro/8-bit sounds?
  - Free sound effect libraries
  - AI sound generation tools (2026 options)
  - Commissioning chiptune sounds
- **Sound specifications:** What makes the level-up sound satisfying?
  - Frequency range
  - Duration
  - Musical qualities (triumphant fanfare)

### 7. Animation Library Recommendation

For the game-like feel:
- **Framer Motion** vs **GSAP** vs **Lottie** vs **CSS animations**
- Which is best for:
  - Level-up fireworks/particles
  - XP bar filling
  - Number counting up (XP gained)
  - Banner slide-in/fade
- Performance considerations
- Code examples for each animation type

### 8. Responsive Design for OSRS Aesthetic

OSRS is designed for fixed-size interface. How to adapt:
- Should I keep fixed pixel sizes or scale?
- Mobile considerations (larger touch targets)
- How to maintain pixel-perfect feel at different resolutions
- CSS techniques for crisp pixel art scaling (image-rendering: pixelated)

### 9. Legal/Copyright Considerations

- Can I say "OSRS-inspired" or "RuneScape-style" in marketing?
- What elements are copyrighted vs general game design patterns?
- How do other OSRS-inspired projects (Melvor Idle, etc.) handle this?
- Safe approach for a potentially commercial product

## Deliverables Requested

1. **Complete color palette** as Tailwind config
2. **Typography specification** with font sizes, weights, line heights
3. **Level-up animation storyboard** with timing (can be text-based)
4. **Component dimension guide** (can be rough measurements)
5. **Icon resource list** with links
6. **Sound resource list** with links
7. **Animation library recommendation** with justification
8. **Code snippets** for:
   - Tailwind theme extension for OSRS colors
   - CSS for pixel-perfect scaling
   - Framer Motion level-up animation skeleton
9. **Reference images** (links to OSRS interface screenshots for reference)
10. **Legal summary** for OSRS-inspired projects
```

---

## Research Prompt 3: React PWA Testing Strategy 2026

**Save result as:** `docs/OSRS/React PWA Testing 2026.md`

```
# Research Request: Testing Strategy for React PWA with Voice Integration (2026)

## Context

I'm building a React PWA (gamification dashboard) with these characteristics:

- **Frontend:** React 18+ with Vite, TypeScript, Tailwind CSS
- **Backend:** FastAPI (Python) serving REST API + WebSocket
- **Database:** SQLite on server (WSL2)
- **Voice integration:** Separate voice pipeline triggers XP events; dashboard displays them
- **Animations:** Level-up banners, XP bar fills, particle effects (Framer Motion)
- **PWA features:** Offline support, installable, service worker caching
- **Development environment:** WSL2 Ubuntu, testing browser-based app

The key challenge: Claude Code (AI assistant) will be iterating on this UI autonomously. It needs fast feedback loops to verify changes work correctly without human visual inspection for every change.

## Testing Requirements

### Must Test:
1. **Component rendering:** Skill cards, XP bars, quest lists display correct data
2. **Real-time updates:** WebSocket events trigger UI updates within 1-2s
3. **Animations:** Level-up banner appears on level-up event
4. **State management:** XP values, skill levels stay in sync with server
5. **Offline behavior:** App shows cached data when server unavailable
6. **PWA installation:** manifest.json correct, service worker registers

### Nice to Test:
7. **Visual regression:** UI looks the same after refactoring
8. **Audio events:** Sound effects trigger at right moments (can't hear, but can verify calls)
9. **Performance:** No memory leaks, animations smooth at 60fps
10. **Accessibility:** Keyboard navigation, screen reader support

## Research Questions

### 1. E2E Testing Framework (2026)

Compare for this use case:
- **Playwright** vs **Cypress** vs **WebdriverIO**
- Which is best for:
  - PWA testing (service worker, offline)
  - WebSocket testing
  - Animation verification (did animation play?)
  - Running in WSL2 (headless Chrome)
  - Integration with Vite
  - Speed (fast feedback loops)

I've heard Playwright is the 2026 standard. Validate or challenge.

### 2. Visual Regression Testing

For catching unintended UI changes:
- **Chromatic** vs **Percy** vs **Playwright screenshots** vs **Loki**
- Cost considerations (free tier limits?)
- Local-only option? (no cloud dependency)
- How to handle intentional changes (updating baselines)
- Animation frames: how to snapshot mid-animation?
- Pixel font rendering: any gotchas across environments?

### 3. Component Testing

For testing React components in isolation:
- **Vitest** vs **Jest** for 2026
- **React Testing Library** best practices
- Testing Framer Motion animations in unit tests
- Mocking WebSocket connections
- Testing custom hooks (useXPSync, useSkillData)

### 4. API/Integration Testing

For testing FastAPI + React together:
- Testing WebSocket connections end-to-end
- Database fixtures (loading test data into SQLite)
- Testing offline fallback behavior
- Mocking vs real backend in tests

### 5. Storybook for Component Development

- Is Storybook still recommended in 2026?
- Alternatives (Ladle, Histoire)?
- Benefits for AI-assisted development (Claude can see component states)
- Integration with visual regression testing
- Storybook for animation components

### 6. Testing Animations

This is tricky - how to verify animations programmatically:
- Playwright's animation handling
- Checking CSS animation state
- Verifying Framer Motion variants applied
- Testing animation timing without watching
- Snapshot testing animated components (which frame?)

### 7. Testing Audio/Sound Effects

Claude can't hear, but needs to verify sounds trigger correctly:
- Mocking Web Audio API
- Logging sound events for verification
- Testing that level-up sound plays on level-up event
- Pattern for audio testing in E2E

### 8. PWA-Specific Testing

- Testing service worker registration
- Testing offline mode (simulating network failure)
- Testing cache behavior
- Testing manifest.json (installability)
- Testing push notifications (if added later)
- Lighthouse CI integration

### 9. CI/CD Pipeline

- GitHub Actions workflow for:
  - Unit tests (Vitest)
  - E2E tests (Playwright)
  - Visual regression (Chromatic/Percy or local)
  - Lighthouse performance audit
- Running tests in WSL2 vs native Linux CI
- Caching strategies for faster CI

### 10. AI-Assisted Development Testing Pattern

Specific to Claude Code iterating autonomously:
- Fast feedback loop (< 5 seconds from change to result)
- State file dumps (JSON) vs screenshots
- When to use screenshots vs structured assertions
- Ralph Wiggum Loop pattern for UI development
- How to write tests that give Claude actionable feedback

## Deliverables Requested

1. **Recommended testing stack** with justification:
   - Unit testing framework
   - E2E testing framework
   - Visual regression solution
   - Component development tool

2. **Project structure** for tests:
   ```
   tests/
   ├── unit/
   ├── e2e/
   ├── visual/
   └── fixtures/
   ```

3. **Example test files** for:
   - Unit test: Skill card component
   - E2E test: Level-up flow (award XP → verify banner appears)
   - Visual regression: Skill card baseline
   - WebSocket test: Real-time XP update

4. **CI/CD workflow** (GitHub Actions YAML)

5. **Testing patterns for animations** with code examples

6. **Audio testing pattern** with code examples

7. **PWA testing checklist** with Playwright examples

8. **State file pattern** for AI feedback:
   - What to export to JSON for Claude to read
   - How to structure for easy assertions
   - Example test that reads state file

9. **Performance testing approach**:
   - Memory leak detection
   - Animation frame rate verification
   - Bundle size monitoring

10. **Resources/documentation** links for further reading
```

---

## How to Use These Prompts

1. Open 3 tabs of Claude.ai (web interface)
2. Enable "Extended Thinking" if available
3. Enable "Research Mode" (the web search capability)
4. Paste one prompt per tab
5. Let them run (may take a few minutes each)
6. Save results to `docs/OSRS/` with the suggested filenames
7. Come back and say "research is ready" - I'll read and synthesize

The prompts are long but specific - this gives Opus research mode clear targets rather than vague exploration.
