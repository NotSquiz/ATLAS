# ATLAS Command Centre - PWA Architecture

**Version:** 1.0
**Date:** January 2026
**Status:** Planning Complete - Ready for Implementation

---

## Executive Summary

The ATLAS Command Centre is a Progressive Web App (PWA) that gamifies health and life optimization using Old School RuneScape-inspired mechanics. It displays real-time XP gains, skill levels, quests, and achievements fed by the existing ATLAS voice pipeline.

**Key Decisions:**
- **Vite + React** over Next.js (68x faster HMR, no SSR overhead)
- **Server-Sent Events** over WebSocket (simpler, auto-reconnect for one-way events)
- **Monorepo** structure (simplified type sharing, single deploy)
- **Service worker caching** over browser SQLite (sufficient for offline read-only)

---

## Technology Stack

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| **Build** | Vite | 6.x | ~130ms dev server start, 10-30% smaller bundles |
| **Framework** | React | 18/19 | Concurrent features for smooth animations |
| **Language** | TypeScript | 5.x | Type safety, FastAPI type generation |
| **Styling** | Tailwind CSS | 3.x | Utility-first, easy OSRS theming |
| **Components** | shadcn/ui | latest | Accessible primitives, full customization |
| **PWA** | vite-plugin-pwa | 1.2.x | Zero-config Workbox, manifest generation |
| **Server State** | TanStack Query | v5 | ~13KB, automatic caching, devtools |
| **Client State** | Zustand | 5.x | ~1.2KB, persist middleware |
| **Animation** | Framer Motion | 11.x | Declarative, spring physics |
| **Particles** | tsParticles | latest | Lazy-loaded, fireworks preset |
| **API Client** | openapi-fetch | latest | Type-safe, generated from OpenAPI |
| **Backend** | FastAPI | 0.115.x | Async, automatic OpenAPI schema |
| **Database** | SQLite (existing) | 3.x | WAL mode, concurrent reads |
| **Real-time** | SSE (sse-starlette) | latest | Auto-reconnect, simpler than WS |

### Why Not Next.js?

1. `next-pwa` plugin unmaintained since July 2024
2. SSR overhead for local-only app (no SEO benefit)
3. 10-15% framework overhead for unused features
4. Static export has PWA manifest issues

### Why SSE Over WebSocket?

| Factor | SSE | WebSocket |
|--------|-----|-----------|
| Direction | One-way (server→client) | Bidirectional |
| Reconnection | Automatic with `retry` | Manual implementation |
| Complexity | Simple HTTP | Protocol upgrade |
| Our use case | XP notifications (one-way) | Overkill |

---

## Project Structure

```
atlas-command-centre/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entry + static file serving
│   │   ├── config.py               # Settings, paths
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py           # REST endpoints
│   │   │   ├── events.py           # SSE endpoint
│   │   │   └── deps.py             # Dependencies (DB session)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py          # Pydantic models → TypeScript
│   │   │   └── database.py         # SQLAlchemy models (read-only)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── skills.py           # Skill queries
│   │   │   ├── quests.py           # Quest queries
│   │   │   └── xp_watcher.py       # Poll xp_events table
│   │   └── static/                 # Built React app (production)
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── public/
│   │   ├── icons/                  # PWA icons (192, 512)
│   │   ├── fonts/                  # RuneStar/Pixelify fonts
│   │   └── sounds/                 # Level-up audio
│   ├── src/
│   │   ├── main.tsx                # Entry + QueryClient + PWA register
│   │   ├── App.tsx                 # Router, layout
│   │   ├── api/
│   │   │   ├── client.ts           # openapi-fetch setup
│   │   │   ├── hooks.ts            # TanStack Query hooks
│   │   │   └── types.ts            # Generated from OpenAPI
│   │   ├── stores/
│   │   │   ├── gameStore.ts        # Zustand: UI state, animations
│   │   │   └── settingsStore.ts    # Zustand: preferences (persisted)
│   │   ├── hooks/
│   │   │   ├── useSSE.ts           # SSE connection with reconnect
│   │   │   ├── useSkills.ts        # TanStack Query wrapper
│   │   │   ├── useLevelUp.ts       # Level-up celebration trigger
│   │   │   └── useInstallPrompt.ts # PWA install prompt
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui primitives
│   │   │   ├── osrs/               # OSRS-styled components
│   │   │   │   ├── Panel.tsx       # Beveled panel
│   │   │   │   ├── SkillCard.tsx   # Skill display
│   │   │   │   ├── XPBar.tsx       # Progress bar
│   │   │   │   ├── QuestItem.tsx   # Quest list item
│   │   │   │   └── LevelUpBanner.tsx # Celebration modal
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── OfflineBanner.tsx
│   │   │   └── ReloadPrompt.tsx    # PWA update notification
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # Main view
│   │   │   ├── Skills.tsx          # All skills detail
│   │   │   ├── Quests.tsx          # Quest management
│   │   │   ├── Achievements.tsx    # Achievement gallery
│   │   │   └── Settings.tsx        # Preferences
│   │   ├── lib/
│   │   │   ├── sounds.ts           # Audio manager
│   │   │   ├── xp.ts               # XP calculations
│   │   │   └── utils.ts            # Helpers
│   │   └── styles/
│   │       ├── globals.css         # Tailwind base + OSRS vars
│   │       └── fonts.css           # @font-face declarations
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── scripts/
│   ├── generate-types.sh           # FastAPI → TypeScript
│   ├── dev.sh                      # Start both servers
│   └── build.sh                    # Production build
│
├── tests/
│   ├── unit/                       # Vitest
│   ├── e2e/                        # Playwright
│   ├── visual/                     # Screenshot tests
│   └── fixtures/                   # Test data
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions
│
├── docker-compose.yml              # Visual regression consistency
├── playwright.config.ts
├── vitest.config.ts
├── lighthouserc.js                 # PWA audits
└── README.md
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXISTING ATLAS VOICE PIPELINE                        │
│  Voice Command → STT → Intent → XP Calculator → SQLite Write            │
│  (bridge_file_server.py, xp_service.py)                                 │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ Writes to ~/.atlas/atlas.db
                                    │ Tables: player_skills, xp_events
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (WSL2)                             │
│                                                                         │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐    │
│  │   SQLite Reader      │    │   XP Event Watcher                 │    │
│  │   (WAL mode)         │◄───│   Polls xp_events every 500ms      │    │
│  │   Read-only queries  │    │   Tracks last_processed_id         │    │
│  └──────────┬───────────┘    └────────────────┬───────────────────┘    │
│             │                                  │                         │
│             ▼                                  ▼                         │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐    │
│  │   REST API           │    │   SSE Endpoint                     │    │
│  │   GET /api/skills    │    │   GET /api/events/xp               │    │
│  │   GET /api/quests    │    │   Yields: {skill, xp, level, ...}  │    │
│  │   GET /api/achieve   │    │   Retry hint: 3000ms               │    │
│  └──────────┬───────────┘    └────────────────┬───────────────────┘    │
│             │                                  │                         │
└─────────────┼──────────────────────────────────┼─────────────────────────┘
              │ HTTP (cached)                    │ SSE (real-time)
              ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      REACT PWA (Browser)                                │
│                                                                         │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐    │
│  │   TanStack Query     │◄───│   useSSE Hook                      │    │
│  │   (Server State)     │    │   - Auto-reconnects on wake        │    │
│  │   - Skills cache     │    │   - Updates TQ cache on XP event   │    │
│  │   - Quests cache     │    │   - Triggers level-up celebration  │    │
│  │   - Achievements     │    └────────────────┬───────────────────┘    │
│  └──────────┬───────────┘                     │                         │
│             │                                  │                         │
│             ▼                                  ▼                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Zustand Store                                 │   │
│  │   - levelUpQueue: pending celebrations                          │   │
│  │   - activeAnimation: current banner                             │   │
│  │   - soundEnabled: user preference (persisted)                   │   │
│  │   - theme: 'osrs_classic' | 'osrs_dark' (persisted)            │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                  │                                       │
│                                  ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    React Components                              │   │
│  │   Dashboard → SkillsGrid → SkillCard → XPBar                    │   │
│  │            → QuestList → QuestItem                               │   │
│  │            → LevelUpBanner (AnimatePresence)                     │   │
│  │            → Particles (lazy-loaded)                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Service Worker (Workbox)                      │   │
│  │   - Precache: JS, CSS, fonts, icons                             │   │
│  │   - NetworkFirst: /api/skills, /api/quests (24h fallback)       │   │
│  │   - CacheFirst: fonts (1 year)                                  │   │
│  │   - NetworkOnly: /api/events/xp (real-time, uncacheable)        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Latency Analysis

| Stage | Time | Cumulative |
|-------|------|------------|
| Voice → SQLite write | ~100ms | 100ms |
| FastAPI poll interval | 500ms | 600ms |
| SSE push to browser | ~50ms | 650ms |
| React state update | ~50ms | **700ms** |

**Target: 1-2 seconds. Achieved: ~700ms.**

---

## Service Worker Strategy

### Caching Configuration

```typescript
// vite.config.ts - workbox configuration
workbox: {
  globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
  runtimeCaching: [
    // API data: Network first with offline fallback
    {
      urlPattern: /\/api\/(skills|quests|achievements)/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-data',
        networkTimeoutSeconds: 10,
        expiration: { maxEntries: 50, maxAgeSeconds: 86400 }
      }
    },
    // Configuration: Fast response with background update
    {
      urlPattern: /\/api\/config/,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'api-config',
        expiration: { maxAgeSeconds: 604800 }
      }
    },
    // Fonts: Long-lived cache
    {
      urlPattern: /\.woff2$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'fonts',
        expiration: { maxAgeSeconds: 31536000 }
      }
    }
  ]
}
```

### Offline Behavior

| State | Behavior |
|-------|----------|
| **Online** | Normal operation, real-time SSE updates |
| **Offline** | Shows cached data, offline banner, mutations disabled |
| **Reconnect** | SSE auto-reconnects, TanStack Query refetches stale data |
| **Update available** | Prompt user to refresh for new version |

---

## Database Integration

### Read-Only Access Pattern

FastAPI reads from the existing `~/.atlas/atlas.db` that the voice pipeline writes to. This is intentionally **read-only** from the PWA perspective:

```python
# backend/app/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

DB_PATH = Path.home() / ".atlas" / "atlas.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={
        "check_same_thread": False,  # Allow multi-thread access
        "timeout": 5,  # Wait up to 5s for locks
    },
    # Read-only by design - voice pipeline handles writes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Tables Accessed

| Table | Purpose | Access |
|-------|---------|--------|
| `player_skills` | Current skill levels/XP | Read |
| `xp_events` | XP event log (for SSE) | Read |
| `activity_streaks` | Streak tracking | Read |
| `achievements` | Achievement definitions | Read |
| `player_achievements` | Unlocked achievements | Read |

### WAL Mode Compatibility

The existing database uses WAL (Write-Ahead Logging) mode, which allows:
- Concurrent reads while voice pipeline writes
- No blocking between readers
- Short-lived connections prevent checkpoint blocking

---

## Type Generation Workflow

```bash
# scripts/generate-types.sh
#!/bin/bash

# Start FastAPI if not running
pgrep -f "uvicorn" || uvicorn backend.app.main:app &
sleep 2

# Generate TypeScript types from OpenAPI schema
cd frontend
npx openapi-typescript http://localhost:8000/openapi.json \
  --output src/api/types.ts

echo "Types generated at frontend/src/api/types.ts"
```

### Pydantic → TypeScript

```python
# backend/app/models/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Skill(BaseModel):
    name: str
    level: int
    current_xp: int
    xp_to_next: int
    progress_percent: float

class XPEvent(BaseModel):
    id: int
    skill: str
    xp_gained: int
    total_xp: int
    level: int
    level_up: bool
    source: str
    timestamp: datetime

class Quest(BaseModel):
    id: str
    name: str
    description: str
    type: str  # 'daily' | 'weekly' | 'monthly'
    progress: int
    target: int
    xp_reward: int
    completed: bool
```

Automatically generates:

```typescript
// frontend/src/api/types.ts (generated)
export interface Skill {
  name: string;
  level: number;
  current_xp: number;
  xp_to_next: number;
  progress_percent: number;
}

export interface XPEvent {
  id: number;
  skill: string;
  xp_gained: number;
  total_xp: number;
  level: number;
  level_up: boolean;
  source: string;
  timestamp: string;
}
```

---

## Development Workflow

### Starting Development

```bash
# Terminal 1: FastAPI backend
cd atlas-command-centre/backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: React frontend
cd atlas-command-centre/frontend
pnpm dev  # Vite on port 5173, proxies /api to :8000

# Or use the combined script:
./scripts/dev.sh
```

### Hot Reload

- **Frontend**: Vite HMR (~100ms for most changes)
- **Backend**: uvicorn `--reload` watches Python files
- **Types**: Run `generate-types.sh` after API changes

### Production Build

```bash
# Build React app
cd frontend && pnpm build

# Copy to FastAPI static folder
cp -r dist/* ../backend/app/static/

# Run FastAPI serving static files
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## PWA Installation

### Manifest Configuration

```json
{
  "name": "ATLAS Command Centre",
  "short_name": "ATLAS",
  "description": "Gamified health optimization dashboard",
  "theme_color": "#1a1a2e",
  "background_color": "#1a1a2e",
  "display": "standalone",
  "start_url": "/",
  "icons": [
    { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

### Installation Prompt Strategy

Show custom install button only after user engagement (e.g., first XP gain or quest completion). This respects attention and increases acceptance.

---

## Potential Pitfalls

| Issue | Mitigation |
|-------|------------|
| **WSL2 networking** | If `localhost:8000` fails, use WSL2 IP (`hostname -I`) |
| **SQLite locks** | Short-lived connections, WAL mode already enabled |
| **SSE connection limits** | Single user, single tab - not an issue |
| **Service worker stale code** | Hourly update check + "new version" prompt |
| **Vite HMR memory** | Restart dev server every few hours during heavy dev |
| **CORS preflight caching** | Clear browser cache when debugging CORS |

---

## Future Considerations

### When to Add Browser SQLite

Current architecture sufficient for most offline needs. Consider wa-sqlite if:
- Complex offline queries needed (joins, aggregations)
- API latency becomes noticeable even when online
- Want full database preload for instant offline access

### Multi-Device Sync (Future)

Current: Local-first, single device.
Future: If adding cloud sync, consider:
- Simple "download full, upload changes" for single-user
- CRDTs only if multi-device conflict resolution needed

---

## References

- [vite-plugin-pwa Documentation](https://vite-pwa-org.netlify.app/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Zustand](https://github.com/pmndrs/zustand)
- [FastAPI SSE](https://github.com/sysid/sse-starlette)
- [openapi-typescript](https://github.com/drwpow/openapi-typescript)
- [Local-First Software (Ink & Switch)](https://www.inkandswitch.com/essay/local-first/)
