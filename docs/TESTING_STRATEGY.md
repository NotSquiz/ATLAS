# ATLAS Command Centre - Testing Strategy

**Version:** 1.0
**Date:** January 2026
**Status:** Planning Complete - Ready for Implementation

---

## Executive Summary

Testing strategy optimized for **AI-assisted development** (Claude Code iterating autonomously). The key innovation is **state file dumps** - structured JSON exports that enable sub-5-second feedback loops without relying solely on screenshots.

**Stack:**
- **E2E**: Playwright (25.9M weekly downloads, native PWA/WebSocket support)
- **Unit**: Vitest (10-20x faster than Jest for Vite projects)
- **Components**: Storybook 10 (Vite-native, interactive controls)
- **Visual**: Playwright screenshots + Docker (free, consistent rendering)
- **PWA Audits**: Lighthouse CI

---

## Testing Stack Justification

| Layer | Tool | Why |
|-------|------|-----|
| **E2E** | Playwright | Native `routeWebSocket()`, `context.setOffline()`, free parallelization |
| **Unit** | Vitest | Shares Vite config, HMR watch mode, 10-20x faster than Jest |
| **Components** | Storybook 10 | Interactive XP/level controls, visual documentation |
| **Visual Regression** | Playwright + Docker | Free, local-first, consistent fonts via container |
| **PWA Audits** | Lighthouse CI | Automated scores, budget enforcement |
| **AI Feedback** | Custom state dumper | JSON for Claude to parse, not screenshots |

### Why Not Cypress?

- Playwright has 4x downloads (25.9M vs ~5M)
- Native WebSocket routing (added v1.48)
- Better PWA/service worker support
- Free parallelization (Cypress requires paid dashboard)

### Why Not Jest?

- Vitest shares Vite configuration (no duplicate setup)
- HMR-powered watch mode (only re-runs affected tests)
- Native ESM support
- 10-20x faster execution

---

## Project Structure

```
tests/
├── unit/                           # Vitest - co-located or here
│   ├── hooks/
│   │   ├── useXPSync.test.ts
│   │   ├── useSkills.test.ts
│   │   └── useLevelUp.test.ts
│   ├── utils/
│   │   ├── xp.test.ts
│   │   └── formatting.test.ts
│   └── components/                 # Or co-located in src/
│       └── SkillCard.test.tsx
│
├── e2e/                            # Playwright
│   ├── level-up-flow.spec.ts
│   ├── sse-updates.spec.ts
│   ├── offline-behavior.spec.ts
│   ├── pwa-install.spec.ts
│   └── quest-tracking.spec.ts
│
├── visual/                         # Playwright screenshots
│   ├── skill-card.visual.spec.ts
│   ├── dashboard.visual.spec.ts
│   └── level-up-banner.visual.spec.ts
│
├── fixtures/
│   ├── skills.json                 # Mock skill data
│   ├── quests.json                 # Mock quest data
│   ├── db-states.ts                # SQLite fixture loader
│   └── state-dump.ts               # AI feedback export
│
└── baselines/                      # Visual regression baselines
    └── *.png

test-results/                       # Generated (gitignored)
├── state-dump.json                 # For Claude to read
├── ai-feedback.jsonl               # Structured test failures
└── screenshots/
```

### File Naming Convention

| Pattern | Type |
|---------|------|
| `*.test.ts` | Unit tests (Vitest) |
| `*.spec.ts` | E2E tests (Playwright) |
| `*.visual.spec.ts` | Visual regression (Playwright) |

---

## Configuration Files

### Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    include: ['src/**/*.test.{ts,tsx}', 'tests/unit/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules', 'tests', '**/*.d.ts']
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
```

### Playwright Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: ['**/*.spec.ts'],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['blob']  // For CI merge
  ],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'visual-regression',
      testMatch: '**/*.visual.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        // Docker container for consistent fonts
        launchOptions: {
          args: ['--font-render-hinting=none']
        }
      },
    },
    {
      name: 'mobile',
      testMatch: ['**/mobile-*.spec.ts'],
      use: { ...devices['iPhone 13'] },
    },
  ],

  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
```

### Test Setup

```typescript
// src/test-setup.ts
import '@testing-library/jest-dom';
import { MotionGlobalConfig } from 'framer-motion';

// Disable Framer Motion animations in tests
MotionGlobalConfig.skipAnimations = true;

// Mock Audio API
Object.defineProperty(window.HTMLMediaElement.prototype, 'play', {
  configurable: true,
  writable: true,
  value: vi.fn().mockImplementation(() => Promise.resolve())
});

// Track audio calls for verification
window.__audioPlayCalls = [];
const originalPlay = HTMLAudioElement.prototype.play;
HTMLAudioElement.prototype.play = function() {
  window.__audioPlayCalls.push({
    src: this.src,
    timestamp: Date.now()
  });
  return originalPlay.call(this);
};
```

---

## Example Tests

### Unit Test: Skill Card Component

```typescript
// src/components/osrs/SkillCard.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MotionConfig } from 'framer-motion';
import { describe, test, expect, vi } from 'vitest';
import { SkillCard } from './SkillCard';

const renderWithMotion = (ui: React.ReactElement) => {
  return render(
    <MotionConfig transition={{ duration: 0 }}>
      {ui}
    </MotionConfig>
  );
};

describe('SkillCard', () => {
  const defaultProps = {
    name: 'Strength',
    level: 23,
    currentXP: 1240,
    xpToNext: 2500,
    iconSrc: '/icons/strength.png'
  };

  test('displays skill name and level', () => {
    renderWithMotion(<SkillCard {...defaultProps} />);

    expect(screen.getByText('Strength')).toBeInTheDocument();
    expect(screen.getByText('23')).toBeInTheDocument();
  });

  test('XP bar shows correct progress percentage', () => {
    renderWithMotion(<SkillCard {...defaultProps} />);

    const progressBar = screen.getByTestId('xp-bar-fill');
    // 1240 / 2500 = 49.6%
    expect(progressBar).toHaveStyle({ width: '49.6%' });
  });

  test('displays XP values', () => {
    renderWithMotion(<SkillCard {...defaultProps} />);

    expect(screen.getByText(/1,240/)).toBeInTheDocument();
    expect(screen.getByText(/2,500/)).toBeInTheDocument();
  });

  test('applies hover effect', async () => {
    const user = userEvent.setup();
    renderWithMotion(<SkillCard {...defaultProps} />);

    const card = screen.getByTestId('skill-card');
    await user.hover(card);

    expect(card).toHaveAttribute('data-hovered', 'true');
  });
});
```

### E2E Test: Level-Up Flow with SSE

```typescript
// tests/e2e/level-up-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Level-up celebration', () => {
  test('shows banner when SSE sends level-up event', async ({ page }) => {
    // Mock SSE endpoint
    await page.route('**/api/events/xp', async route => {
      const body = `event: xp_update
data: {"skill":"strength","xp_gained":500,"total_xp":2600,"level":24,"level_up":true}
id: 1

`;
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body
      });
    });

    await page.goto('/dashboard');

    // Wait for level-up banner
    const banner = page.locator('[data-testid="level-up-banner"]');
    await expect(banner).toBeVisible({ timeout: 2000 });
    await expect(banner).toContainText('Level 24');
    await expect(banner).toContainText('Strength');

    // Banner should auto-hide
    await expect(banner).not.toBeVisible({ timeout: 5000 });
  });

  test('plays sound on level-up', async ({ page }) => {
    // Inject audio spy
    await page.addInitScript(() => {
      window.__audioPlayCalls = [];
      const originalPlay = HTMLAudioElement.prototype.play;
      HTMLAudioElement.prototype.play = function() {
        window.__audioPlayCalls.push({ src: this.src, time: Date.now() });
        return Promise.resolve();
      };
    });

    await page.route('**/api/events/xp', async route => {
      const body = `event: xp_update
data: {"skill":"strength","xp_gained":500,"total_xp":2600,"level":24,"level_up":true}
id: 1

`;
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body
      });
    });

    await page.goto('/dashboard');
    await page.waitForTimeout(1000);

    const audioCalls = await page.evaluate(() => window.__audioPlayCalls);
    expect(audioCalls.some(c => c.src.includes('level-up'))).toBe(true);
  });

  test('updates within latency target (<2s)', async ({ page }) => {
    const startTime = Date.now();

    await page.route('**/api/events/xp', async route => {
      await new Promise(r => setTimeout(r, 100)); // Simulate network
      const body = `event: xp_update
data: {"skill":"strength","xp_gained":50,"total_xp":1290,"level":23,"level_up":false}
id: 1

`;
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body
      });
    });

    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="strength-xp"]')).toContainText('1,290');

    const elapsed = Date.now() - startTime;
    expect(elapsed).toBeLessThan(2000);
  });
});
```

### E2E Test: Offline Behavior

```typescript
// tests/e2e/offline-behavior.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Offline functionality', () => {
  test('shows cached data when offline', async ({ page, context }) => {
    // First visit to cache data
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="skills-grid"]')).toBeVisible();

    // Wait for service worker
    await page.waitForFunction(() => navigator.serviceWorker.controller);

    // Go offline
    await context.setOffline(true);

    // Reload should work from cache
    await page.reload();
    await expect(page.locator('[data-testid="skills-grid"]')).toBeVisible();

    // Offline indicator shown
    await expect(page.locator('[data-testid="offline-banner"]')).toBeVisible();
  });

  test('reconnects SSE after coming back online', async ({ page, context }) => {
    await page.goto('/dashboard');

    // Go offline then online
    await context.setOffline(true);
    await page.waitForTimeout(1000);
    await context.setOffline(false);

    // SSE should reconnect (check connection indicator)
    await expect(page.locator('[data-testid="connection-status"]'))
      .toHaveAttribute('data-connected', 'true', { timeout: 5000 });
  });
});
```

### Visual Regression Test

```typescript
// tests/visual/skill-card.visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Skill Card Visual', () => {
  test.beforeEach(async ({ page }) => {
    // Disable animations for deterministic screenshots
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          transition-duration: 0s !important;
        }
        .particle-container { display: none !important; }
      `
    });
  });

  test('skill card at various XP levels', async ({ page }) => {
    // Test via Storybook for isolated components
    await page.goto('/storybook-iframe?id=osrs-skillcard--default');
    await page.waitForSelector('[data-testid="skill-card"]');

    await expect(page.locator('[data-testid="skill-card"]'))
      .toHaveScreenshot('skill-card-default.png', {
        maxDiffPixels: 50,
        threshold: 0.2
      });
  });

  test('level-up banner appearance', async ({ page }) => {
    await page.goto('/storybook-iframe?id=osrs-levelupbanner--visible');
    await page.waitForSelector('[data-testid="level-up-banner"]');

    await expect(page.locator('[data-testid="level-up-banner"]'))
      .toHaveScreenshot('level-up-banner.png');
  });

  test('full dashboard layout', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      mask: [
        page.locator('[data-testid="timestamp"]'),
        page.locator('[data-testid="connection-indicator"]')
      ]
    });
  });
});
```

---

## AI Feedback Pattern (State Dumps)

### Why State Dumps Over Screenshots

| Aspect | Screenshots | State Dumps |
|--------|-------------|-------------|
| Speed | 500ms+ per capture | <10ms JSON write |
| Parseability | Requires vision | Structured JSON |
| Assertions | Visual diff (imprecise) | Exact value checks |
| CI cost | Storage, comparison | Minimal |

### State Dump Implementation

```typescript
// tests/fixtures/state-dump.ts
import { Page } from '@playwright/test';

export interface UIStateDump {
  route: string;
  timestamp: string;
  gamification: {
    totalXP: number;
    totalLevel: number;
    skills: Array<{
      name: string;
      level: number;
      xp: number;
      progress: number;
    }>;
    activeQuests: Array<{
      id: string;
      name: string;
      progress: number;
      target: number;
    }>;
  };
  ui: {
    visibleComponents: string[];
    activeAnimations: string[];
    levelUpQueue: Array<{ skill: string; level: number }>;
    errors: string[];
  };
  network: {
    sseConnected: boolean;
    pendingRequests: number;
    lastEventId: string;
  };
}

export async function dumpUIState(page: Page): Promise<UIStateDump> {
  return await page.evaluate(() => {
    // Assumes app exposes state for testing
    const gameState = (window as any).__ATLAS_STATE__;

    return {
      route: window.location.pathname,
      timestamp: new Date().toISOString(),
      gamification: gameState?.gamification || {},
      ui: {
        visibleComponents: Array.from(
          document.querySelectorAll('[data-testid]:not([hidden])')
        ).map(el => el.getAttribute('data-testid')),
        activeAnimations: Array.from(
          document.querySelectorAll('[data-animation-state="animating"]')
        ).map(el => el.getAttribute('data-testid')),
        levelUpQueue: gameState?.levelUpQueue || [],
        errors: (window as any).__TEST_ERRORS__ || []
      },
      network: {
        sseConnected: gameState?.sseConnected || false,
        pendingRequests: (window as any).__PENDING_REQUESTS__ || 0,
        lastEventId: gameState?.lastEventId || '0'
      }
    };
  });
}
```

### Test Writing State for Claude

```typescript
// tests/e2e/ai-feedback.spec.ts
import { test, expect } from '@playwright/test';
import { dumpUIState } from '../fixtures/state-dump';
import * as fs from 'fs';

test('dashboard state after XP award', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Trigger XP gain
  await page.evaluate(() => {
    // Simulate SSE event
    window.dispatchEvent(new CustomEvent('xp-update', {
      detail: { skill: 'strength', xp_gained: 100 }
    }));
  });

  await page.waitForTimeout(500);

  // Dump state for AI
  const state = await dumpUIState(page);
  fs.writeFileSync(
    'test-results/state-dump.json',
    JSON.stringify(state, null, 2)
  );

  // Structured assertions Claude can parse
  expect(state.gamification.skills.find(s => s.name === 'strength')?.xp)
    .toBeGreaterThan(0);
  expect(state.ui.errors).toHaveLength(0);
  expect(state.network.sseConnected).toBe(true);
});
```

### CLAUDE.md Testing Instructions

```markdown
## Development Loop (Ralph Wiggum Pattern)

1. Read `test-results/state-dump.json` for current UI state
2. Read `test-results/ai-feedback.jsonl` for test failures
3. Implement fix based on structured error data
4. Run: `pnpm test && pnpm e2e`
5. On pass: commit and move to next task
6. On fail: parse error JSON, iterate

### State File Schema
- `gamification.skills[].level`: Current skill levels
- `gamification.totalXP`: Total XP across all skills
- `ui.visibleComponents`: Array of visible data-testid values
- `ui.activeAnimations`: Currently animating elements
- `ui.errors`: Runtime errors captured
- `network.sseConnected`: SSE connection status

### Quick Commands
```bash
pnpm test              # Unit tests (Vitest)
pnpm e2e               # E2E tests (Playwright)
pnpm e2e:visual        # Visual regression
pnpm test:coverage     # With coverage report
```
```

---

## Animation Testing

### Disabling Animations for Unit Tests

```typescript
// Framer Motion global disable
import { MotionGlobalConfig } from 'framer-motion';
MotionGlobalConfig.skipAnimations = true;

// Or per-test with wrapper
import { MotionConfig } from 'framer-motion';

const renderWithMotion = (ui: React.ReactElement) => {
  return render(
    <MotionConfig transition={{ duration: 0 }}>
      {ui}
    </MotionConfig>
  );
};
```

### Verifying Animation State in E2E

```tsx
// Component with animation state attribute
<motion.div
  data-testid="level-up-banner"
  data-animation-state={isAnimating ? "animating" : "complete"}
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  onAnimationComplete={() => setIsAnimating(false)}
>
```

```typescript
// E2E test
test('animation completes', async ({ page }) => {
  await page.click('[data-testid="trigger-level-up"]');

  // Wait for animation to start
  await expect(page.locator('[data-animation-state="animating"]'))
    .toBeVisible();

  // Wait for completion
  await expect(page.locator('[data-animation-state="complete"]'))
    .toBeVisible({ timeout: 4000 });
});
```

---

## Audio Testing

### Intercepting Audio in E2E

```typescript
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.__audioPlayCalls = [];
    const originalPlay = HTMLAudioElement.prototype.play;
    HTMLAudioElement.prototype.play = function() {
      window.__audioPlayCalls.push({
        src: this.src,
        timestamp: Date.now()
      });
      return Promise.resolve();
    };
  });
});

test('plays level-up sound', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="trigger-level-up"]');
  await page.waitForTimeout(500);

  const audioCalls = await page.evaluate(() => window.__audioPlayCalls);
  expect(audioCalls.some(c => c.src.includes('level-up'))).toBe(true);
});
```

---

## PWA Testing

### Service Worker Registration

```typescript
test('registers service worker', async ({ page, context }) => {
  const swPromise = context.waitForEvent('serviceworker');
  await page.goto('/');

  const sw = await swPromise;
  expect(sw.url()).toContain('sw.js');
});
```

### Manifest Validation

```typescript
test('valid PWA manifest', async ({ request }) => {
  const response = await request.get('/manifest.json');
  const manifest = await response.json();

  expect(manifest.name).toBeTruthy();
  expect(manifest.short_name).toBeTruthy();
  expect(manifest.display).toMatch(/standalone|fullscreen/);

  const sizes = manifest.icons.map(i => i.sizes);
  expect(sizes).toContain('192x192');
  expect(sizes).toContain('512x512');
});
```

### Lighthouse CI Configuration

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      startServerCommand: 'pnpm preview',
      startServerReadyPattern: 'Local:',
      url: ['http://localhost:4173/', 'http://localhost:4173/dashboard'],
      numberOfRuns: 3
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:pwa': ['error', { minScore: 0.9 }],
        'installable-manifest': 'error',
        'service-worker': 'error',
        'works-offline': 'warn'
      }
    },
    upload: { target: 'temporary-public-storage' }
  }
};
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with: { version: 10 }
      - uses: actions/setup-node@v5
        with: { node-version: 20, cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - run: pnpm test --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  e2e-tests:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.57.0-noble
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with: { version: 10 }
      - uses: actions/setup-node@v5
        with: { node-version: 20, cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/

  visual-regression:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.57.0-noble
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with: { version: 10 }
      - uses: actions/setup-node@v5
        with: { node-version: 20, cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - run: npx playwright test --project=visual-regression
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: visual-diff
          path: test-results/

  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with: { version: 10 }
      - uses: actions/setup-node@v5
        with: { node-version: 20, cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - uses: treosh/lighthouse-ci-action@v12
        with:
          uploadArtifacts: true
          configPath: ./lighthouserc.js
```

---

## Performance Testing

### Memory Leak Detection

```typescript
test('no memory leaks during animations', async ({ page }) => {
  const client = await page.context().newCDPSession(page);
  await page.goto('/dashboard');

  await client.send('HeapProfiler.collectGarbage');
  let metrics = await client.send('Performance.getMetrics');
  const initialHeap = metrics.metrics.find(m => m.name === 'JSHeapUsedSize')?.value;

  // Trigger 50 level-up animations
  for (let i = 0; i < 50; i++) {
    await page.click('[data-testid="trigger-level-up"]');
    await page.waitForTimeout(100);
  }

  await client.send('HeapProfiler.collectGarbage');
  metrics = await client.send('Performance.getMetrics');
  const finalHeap = metrics.metrics.find(m => m.name === 'JSHeapUsedSize')?.value;

  // Allow 20% growth max
  expect(finalHeap).toBeLessThan(initialHeap * 1.2);
});
```

### Animation FPS Verification

```typescript
async function measureFPS(page: Page, durationMs = 2000) {
  return await page.evaluate((duration) => {
    return new Promise((resolve) => {
      const timestamps: number[] = [];
      let rafId: number;

      const record = (t: number) => {
        timestamps.push(t);
        rafId = requestAnimationFrame(record);
      };

      rafId = requestAnimationFrame(record);

      setTimeout(() => {
        cancelAnimationFrame(rafId);
        const deltas = timestamps.slice(1).map((t, i) => t - timestamps[i]);
        const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
        resolve({
          fps: Math.round(1000 / avgDelta),
          jankFrames: deltas.filter(d => d > 33).length
        });
      }, duration);
    });
  }, durationMs);
}

test('maintains 60fps during animations', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="trigger-level-up"]');

  const { fps, jankFrames } = await measureFPS(page);

  expect(fps).toBeGreaterThanOrEqual(55);
  expect(jankFrames).toBeLessThan(5);
});
```

---

## NPM Scripts

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "e2e": "playwright test",
    "e2e:ui": "playwright test --ui",
    "e2e:visual": "playwright test --project=visual-regression",
    "e2e:update-snapshots": "playwright test --update-snapshots",
    "lighthouse": "lhci autorun"
  }
}
```

---

## References

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Vitest Documentation](https://vitest.dev/guide/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Service Workers](https://playwright.dev/docs/service-workers)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [Framer Motion Testing](https://github.com/motiondivision/motion/issues/1690)
