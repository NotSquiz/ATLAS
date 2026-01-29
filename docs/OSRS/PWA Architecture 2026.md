# PWA Architecture for ATLAS Command Centre: 2026 Best Practices

**Vite + React is your best choice, paired with Server-Sent Events for real-time updates and a layered caching strategy.** Your instinct toward Vite is validated by performance benchmarks showing **68x faster HMR** than alternatives and **71-83% less memory usage**—critical for your constrained hardware. For a single-user local-first app, avoid over-engineering: simple service worker caching beats browser SQLite until you genuinely need complex offline queries.

## Recommended stack with justifications

The 2026 consensus for local-first PWAs has coalesced around lightweight, composable tools rather than monolithic frameworks. Here's the optimal stack for ATLAS Command Centre:

| Layer | Choice | Reasoning |
|-------|--------|-----------|
| Build Tool | **Vite 6.x** | ~130ms dev server start, 10-30% smaller bundles than Next.js |
| Framework | **React 18/19** | Stable, massive ecosystem, concurrent features for smooth animations |
| PWA Plugin | **vite-plugin-pwa 1.2.x** | Zero-config Workbox integration, built-in manifest generation |
| State (Server) | **TanStack Query v5** | ~13KB, automatic caching, optimistic updates, devtools |
| State (Client) | **Zustand** | ~1.2KB, simple API, persist middleware for user preferences |
| Real-time | **Server-Sent Events** | Auto-reconnection, perfect for one-way XP notifications |
| API Client | **openapi-fetch** | Type-safe, generated from FastAPI's OpenAPI schema |
| Offline Storage | **Dexie.js** | Clean IndexedDB wrapper for structured data caching |

**Why not Next.js?** The `next-pwa` plugin is deprecated (unmaintained since July 2024), static export has PWA manifest issues, and you'd carry ~10-15% framework overhead for SSR features you'll never use against a local FastAPI backend.

**Why not Remix?** After merging into React Router v7 in November 2024, the framework's direction became uncertain—Remix v3 announced it's abandoning React entirely for a Preact fork, causing developer confusion and migration to TanStack Router.

## Project structure for FastAPI + React monorepo

A monorepo structure simplifies type sharing and coordinated deployment for a single-developer project:

```
atlas-command-centre/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry + SPA serving
│   │   ├── api/
│   │   │   ├── routes.py        # REST endpoints
│   │   │   └── events.py        # SSE endpoint for real-time
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models → TypeScript types
│   │   ├── db/
│   │   │   └── database.py      # SQLite connection to ~/.atlas/atlas.db
│   │   └── static/              # Built React files (production)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # Entry point + QueryClient
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── client.ts        # openapi-fetch setup
│   │   │   └── hooks.ts         # TanStack Query hooks
│   │   ├── stores/
│   │   │   └── gameStore.ts     # Zustand: UI state, animations
│   │   ├── hooks/
│   │   │   └── useSSE.ts        # SSE connection with reconnection
│   │   ├── components/
│   │   │   └── ReloadPrompt.tsx # PWA update notification
│   │   └── types/
│   │       └── api.d.ts         # Generated from OpenAPI
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── scripts/
│   └── generate-types.sh        # FastAPI → TypeScript automation
└── README.md
```

**Type generation workflow**: Run `npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.d.ts` after starting FastAPI. This extracts types from your Pydantic models automatically—no manual synchronization needed.

## Data flow from voice command to level-up animation

The architecture maintains clear separation between your existing voice pipeline and the new dashboard:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         VOICE PIPELINE (Existing)                   │
│  Voice Command → Speech Recognition → XP Calculator → SQLite Write │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │ Writes to ~/.atlas/atlas.db
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND (WSL2)                        │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐   │
│  │  SQLite Reader  │◄───│  XP Event Watcher (polling @500ms)   │   │
│  │  WAL Mode       │    │  Tracks last_event_id               │   │
│  └────────┬────────┘    └──────────────────┬───────────────────┘   │
│           │                                │                        │
│           ▼                                ▼                        │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐   │
│  │  REST API       │    │  SSE Endpoint /events/xp             │   │
│  │  /api/skills    │    │  Yields: {xp, level, skill, levelUp} │   │
│  │  /api/quests    │    └──────────────────┬───────────────────┘   │
│  └────────┬────────┘                       │                        │
└───────────┼────────────────────────────────┼────────────────────────┘
            │ HTTP                           │ SSE (auto-reconnect)
            ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       REACT PWA (Browser)                           │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐   │
│  │  TanStack Query │◄───│  useSSE Hook                         │   │
│  │  (Server State) │    │  - Reconnects on wake                │   │
│  │  Skills, Quests │    │  - Updates TQ cache on XP event      │   │
│  └────────┬────────┘    └──────────────────┬───────────────────┘   │
│           │                                │                        │
│           ▼                                ▼                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Zustand Store (Client State)                    │   │
│  │  - Selected skill, UI preferences (persisted)                │   │
│  │  - Level-up modal visibility, XP animation state             │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              React Components                                │   │
│  │  XPBar → SkillsGrid → LevelUpCelebration → QuestTracker     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Latency target achieved**: Voice command → SQLite write (existing, ~100ms) → FastAPI detects change (500ms poll) → SSE push to browser (~50ms) → React state update (~50ms) = **~700ms total**, well under your 1-2 second requirement.

## Service worker strategy with Workbox

The vite-plugin-pwa approach uses Workbox internally with sensible defaults, requiring minimal configuration while supporting advanced customization.

**Caching strategy by content type:**

| Content | Strategy | Cache Duration | Rationale |
|---------|----------|----------------|-----------|
| React bundle, CSS | Precache | Until version change | Hash-versioned, immutable |
| Fonts (woff2) | Cache-First | 1 year | Rarely change |
| Images, icons | Cache-First | 30 days | Visual assets, large files |
| /api/skills, /api/quests | NetworkFirst (10s timeout) | 24 hours | Fresh preferred, offline fallback |
| /api/config | StaleWhileRevalidate | 7 days | Rarely changes, fast response |
| SSE endpoint | NetworkOnly | — | Real-time, uncacheable |

**Offline behavior**: When FastAPI is down, the service worker serves cached API responses. The UI displays an offline banner and disables mutation actions. Cached skill levels and quest progress remain viewable. When the server returns, SSE reconnects automatically and TanStack Query refetches stale data.

## Code snippets for critical integrations

### FastAPI SSE endpoint for XP events

```python
# backend/app/api/events.py
from fastapi import APIRouter, Request, Query
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from app.db.database import get_xp_events_since

router = APIRouter()

async def xp_event_generator(request: Request, last_event_id: int = 0):
    """Generator yielding XP events as they appear in SQLite"""
    current_id = last_event_id
    
    while True:
        if await request.is_disconnected():
            break
        
        # Check SQLite for new events (WAL mode handles concurrent reads)
        events = await get_xp_events_since(current_id)
        
        for event in events:
            current_id = event.id
            yield {
                "event": "xp_update",
                "id": str(event.id),
                "retry": 3000,  # Reconnect hint for client
                "data": json.dumps({
                    "skill": event.skill,
                    "xp_gained": event.xp_gained,
                    "total_xp": event.total_xp,
                    "level": event.level,
                    "level_up": event.level_up
                })
            }
        
        # Poll every 500ms for sub-second latency
        await asyncio.sleep(0.5)

@router.get("/events/xp")
async def xp_stream(
    request: Request,
    lastEventId: int = Query(0, alias="lastEventId")
):
    """SSE endpoint - supports resuming from last event after reconnection"""
    return EventSourceResponse(xp_event_generator(request, lastEventId))
```

### React SSE hook with sleep/wake handling

```typescript
// frontend/src/hooks/useSSE.ts
import { useEffect, useState, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface XPUpdate {
  skill: string;
  xp_gained: number;
  total_xp: number;
  level: number;
  level_up: boolean;
}

export function useXPStream(onLevelUp?: (level: number) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const lastEventIdRef = useRef<string>('0');
  const eventSourceRef = useRef<EventSource | null>(null);
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    const url = `/api/events/xp?lastEventId=${lastEventIdRef.current}`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => setIsConnected(true);
    
    eventSource.addEventListener('xp_update', (event) => {
      lastEventIdRef.current = event.lastEventId;
      const data: XPUpdate = JSON.parse(event.data);
      
      // Update TanStack Query cache optimistically
      queryClient.setQueryData(['skills'], (old: any) => {
        if (!old) return old;
        return old.map((skill: any) =>
          skill.name === data.skill
            ? { ...skill, xp: data.total_xp, level: data.level }
            : skill
        );
      });
      
      if (data.level_up && onLevelUp) {
        onLevelUp(data.level);
      }
    });

    eventSource.onerror = () => {
      setIsConnected(false);
      // EventSource auto-reconnects; this just updates UI state
    };

    return eventSource;
  }, [queryClient, onLevelUp]);

  useEffect(() => {
    const eventSource = connect();
    
    // Reconnect after laptop wake
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && 
          eventSource.readyState === EventSource.CLOSED) {
        eventSource.close();
        connect();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      eventSource.close();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [connect]);

  return { isConnected };
}
```

### Vite PWA configuration with Workbox

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'prompt',  // User controls updates
      devOptions: { enabled: true },  // Debug SW in development
      
      manifest: {
        name: 'ATLAS Command Centre',
        short_name: 'ATLAS',
        description: 'Gamification dashboard with OSRS-style XP tracking',
        theme_color: '#1a1a2e',
        background_color: '#1a1a2e',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        cleanupOutdatedCaches: true,
        
        runtimeCaching: [
          // API data: Network first with offline fallback
          {
            urlPattern: /\/api\/(skills|quests|achievements)/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-data',
              networkTimeoutSeconds: 10,
              expiration: { maxEntries: 50, maxAgeSeconds: 86400 },
              cacheableResponse: { statuses: [0, 200] }
            }
          },
          // Configuration: Stale-while-revalidate for fast loads
          {
            urlPattern: /\/api\/config/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-config',
              expiration: { maxEntries: 10, maxAgeSeconds: 604800 }
            }
          },
          // Fonts: Cache first, long-lived
          {
            urlPattern: /\.woff2$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'fonts',
              expiration: { maxEntries: 20, maxAgeSeconds: 31536000 }
            }
          }
        ]
      }
    })
  ],
  
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  },
  
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: { vendor: ['react', 'react-dom'] }
      }
    }
  }
});
```

### PWA update prompt component

```tsx
// frontend/src/components/ReloadPrompt.tsx
import { useRegisterSW } from 'virtual:pwa-register/react';

export function ReloadPrompt() {
  const {
    offlineReady: [offlineReady, setOfflineReady],
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(registration) {
      // Check for updates every hour
      if (registration) {
        setInterval(() => registration.update(), 60 * 60 * 1000);
      }
    }
  });

  if (!offlineReady && !needRefresh) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-gray-900 text-white p-4 rounded-lg shadow-lg">
      {offlineReady && <span>Ready for offline use!</span>}
      {needRefresh && (
        <>
          <span className="mr-3">New version available</span>
          <button 
            onClick={() => updateServiceWorker(true)}
            className="bg-blue-600 px-3 py-1 rounded"
          >
            Update
          </button>
        </>
      )}
      <button 
        onClick={() => { setOfflineReady(false); setNeedRefresh(false); }}
        className="ml-2 text-gray-400"
      >
        ✕
      </button>
    </div>
  );
}
```

## PWA installation for desktop-like experience

The manifest configuration above already sets `display: standalone` for app-like appearance. For a non-intrusive install prompt:

```tsx
// frontend/src/hooks/useInstallPrompt.ts
import { useState, useEffect } from 'react';

export function useInstallPrompt() {
  const [installPrompt, setInstallPrompt] = useState<any>(null);
  const [isInstalled, setIsInstalled] = useState(
    window.matchMedia('(display-mode: standalone)').matches
  );

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e);
    };
    
    window.addEventListener('beforeinstallprompt', handler);
    window.addEventListener('appinstalled', () => setIsInstalled(true));
    
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const promptInstall = async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    const result = await installPrompt.userChoice;
    if (result.outcome === 'accepted') setIsInstalled(true);
    setInstallPrompt(null);
  };

  return { canInstall: !!installPrompt && !isInstalled, promptInstall, isInstalled };
}
```

**Best practice**: Show a custom install button only after the user has engaged with the app (e.g., after creating their first skill or completing a quest). This respects user attention and increases install acceptance rates.

## Potential pitfalls specific to this architecture

**WSL2 networking quirks** can cause connectivity issues between Windows browser and WSL2 FastAPI. If `localhost:8000` fails, try the WSL2 IP address directly (`hostname -I` in WSL2). Some users need to run `wsl --shutdown` and restart after Windows updates that break WSL2 networking.

**SQLite concurrent access** from voice pipeline (writes) and FastAPI (reads) requires WAL mode, which you already have. However, long-running read transactions can block checkpointing—ensure FastAPI connections are short-lived and use connection pooling with `check_same_thread=False`.

**SSE connection limits** in browsers cap at 6 connections per domain (HTTP/1.1). Since you're single-user with one dashboard tab, this isn't an issue, but close connections properly on component unmount to avoid leaks.

**Service worker update timing** can leave users on stale code if they never close the tab. The hourly `registration.update()` check mitigates this, but consider adding a "new version" indicator that persists until they refresh.

**Memory pressure from Vite HMR** during long development sessions (1000+ module reloads) can cause slowdowns. Restart the dev server every few hours during intensive development.

**CORS preflight caching** with `max_age=7200` reduces OPTIONS requests during development, but if you change CORS settings, browsers may use stale preflight responses. Clear browser cache or use incognito when debugging CORS issues.

## When to consider browser SQLite

Your current architecture (FastAPI reads SQLite, caches responses in service worker) is sufficient for most offline scenarios. Consider browser SQLite (wa-sqlite with OPFS) only if:

- You need complex offline queries (joins, aggregations, full-text search) beyond what cached JSON provides
- The app feels slow due to API latency even when online
- You want to pre-load the entire skill/quest database for instant offline access

If you upgrade later, wa-sqlite's `OPFSCoopSyncVFS` offers excellent performance without requiring COOP/COEP headers. For syncing, a simple "download full DB on app start, upload changes periodically" pattern works well for single-user scenarios—CRDTs are overkill until you add multi-device or multi-user sync.

## Resources for deeper implementation

**Official documentation:**
- vite-plugin-pwa: https://vite-pwa-org.netlify.app/
- TanStack Query: https://tanstack.com/query/latest
- Zustand: https://github.com/pmndrs/zustand
- FastAPI WebSockets/SSE: https://fastapi.tiangolo.com/advanced/websockets/

**Architecture patterns:**
- Local-first software essay (Ink & Switch): https://www.inkandswitch.com/essay/local-first/
- Linear's sync engine architecture: Demonstrates IndexedDB + LWW for production-scale offline

**Type generation:**
- openapi-typescript: https://github.com/drwpow/openapi-typescript
- openapi-fetch (type-safe client): https://github.com/drwpow/openapi-fetch

**Offline storage:**
- Dexie.js: https://dexie.org/
- wa-sqlite (if you need browser SQLite later): https://github.com/rhashimoto/wa-sqlite

This architecture gives you a lightweight, maintainable foundation that can evolve. Start simple with the service worker caching pattern, add browser SQLite only when the use case demands it, and avoid CRDTs until you genuinely need multi-device conflict resolution.