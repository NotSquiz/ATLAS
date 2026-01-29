# Comprehensive testing strategy for React PWA with AI-assisted development

**Playwright dominates 2026 E2E testing with 25.9M+ weekly npm downloads, while Vitest has become the standard for unit testing Vite projects with 10-20x faster execution than Jest.** For your gamification dashboard, this combination provides sub-5-second feedback loops essential for Claude Code's autonomous iteration. The key innovation enabling AI-assisted development is the "state file dump" pattern—exporting structured JSON rather than relying solely on screenshots allows Claude to programmatically verify UI state without visual inspection.

This strategy covers all 10 research areas: E2E frameworks, visual regression, component testing, API/integration testing, Storybook alternatives, animation testing, audio verification, PWA-specific testing, CI/CD pipelines, and AI feedback patterns optimized for autonomous development.

## Recommended testing stack and justification

The 2026 testing landscape has consolidated around a clear set of winners. **Playwright** leads E2E testing with native PWA support, WebSocket routing (added in v1.48), and WSL2 compatibility in headless mode. **Vitest** dominates unit testing for Vite projects, sharing configuration and delivering HMR-powered watch mode that re-runs only affected tests. For visual regression, **Playwright's built-in screenshot comparison** with Docker provides free, local-first testing with consistent font rendering.

| Layer | Tool | Justification |
|-------|------|---------------|
| **E2E Testing** | Playwright | 4x Cypress downloads, native `routeWebSocket()`, `context.setOffline()`, free parallelization |
| **Unit Testing** | Vitest | Native Vite integration, 10-20x faster than Jest, HMR watch mode |
| **Component Dev** | Storybook 10 | Rich ecosystem, Vite-native since v7, interactive controls for XP/level testing |
| **Visual Regression** | Playwright + Docker | Free, local-first, consistent rendering via container |
| **PWA Audits** | Lighthouse CI | Automated scores in CI, budget enforcement |
| **State Extraction** | Custom state dumper | JSON exports for AI consumption |

For component isolation during development, **Storybook 10** remains the standard despite alternatives like Ladle (faster startup but minimal ecosystem). Storybook's controls system enables testing edge cases—sliding XP values to test overflow, triggering level-up animations, and verifying particle effects at various densities.

## Project structure for tests

```
project-root/
├── src/
│   └── components/
│       └── SkillCard/
│           ├── SkillCard.tsx
│           └── SkillCard.test.tsx      # Co-located unit tests
├── tests/
│   ├── unit/
│   │   ├── hooks/
│   │   │   ├── useXPSync.test.ts
│   │   │   └── useSkillData.test.ts
│   │   └── utils/
│   │       └── gamification.test.ts
│   ├── e2e/
│   │   ├── level-up-flow.spec.ts
│   │   ├── websocket-updates.spec.ts
│   │   └── offline-behavior.spec.ts
│   ├── visual/
│   │   ├── skill-card.visual.spec.ts
│   │   └── dashboard.visual.spec.ts
│   └── fixtures/
│       ├── users.json
│       ├── skills.json
│       ├── state-dump.ts               # AI state extraction
│       └── screenshot.css              # Animation disabling
├── test-results/                       # Generated, gitignored
│   ├── ai-feedback.jsonl
│   ├── state-dump.json
│   └── screenshots/
├── .storybook/
│   └── main.ts
├── playwright.config.ts
├── vitest.config.ts
├── lighthouserc.js
├── docker-compose.yml                  # Consistent visual testing
└── CLAUDE.md                           # AI agent instructions
```

File naming follows consistent conventions: `*.test.ts` for unit tests (co-located or in `tests/unit/`), `*.spec.ts` for E2E tests, and `*.visual.spec.ts` for visual regression tests.

## Example test files

### Unit test: Skill card component

```typescript
// src/components/SkillCard/SkillCard.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MotionConfig } from 'framer-motion';
import { describe, test, expect, vi } from 'vitest';
import { SkillCard } from './SkillCard';

// Wrap with MotionConfig to disable animations in tests
const renderWithMotion = (ui: React.ReactElement) => {
  return render(
    <MotionConfig transition={{ duration: 0 }}>
      {ui}
    </MotionConfig>
  );
};

describe('SkillCard', () => {
  test('displays skill name and current level', () => {
    renderWithMotion(
      <SkillCard 
        name="TypeScript" 
        level={5} 
        xp={2500} 
        maxXP={3000} 
      />
    );
    
    expect(screen.getByRole('heading', { name: /typescript/i })).toBeInTheDocument();
    expect(screen.getByText('Level 5')).toBeInTheDocument();
  });

  test('XP bar width matches percentage', () => {
    renderWithMotion(
      <SkillCard name="React" level={3} xp={750} maxXP={1000} />
    );
    
    const progressBar = screen.getByTestId('xp-bar-fill');
    expect(progressBar).toHaveStyle({ width: '75%' });
  });

  test('calls onLevelUp callback when level threshold reached', async () => {
    const onLevelUp = vi.fn();
    const user = userEvent.setup();
    
    renderWithMotion(
      <SkillCard 
        name="React" 
        level={3} 
        xp={990} 
        maxXP={1000} 
        onLevelUp={onLevelUp}
      />
    );
    
    await user.click(screen.getByRole('button', { name: /gain xp/i }));
    
    expect(onLevelUp).toHaveBeenCalledWith({ skill: 'React', newLevel: 4 });
  });

  test('applies hover animation variant on interaction', async () => {
    const user = userEvent.setup();
    renderWithMotion(<SkillCard name="CSS" level={2} xp={500} maxXP={1000} />);
    
    const card = screen.getByTestId('skill-card');
    await user.hover(card);
    
    // With duration: 0, transform applies immediately
    expect(card).toHaveAttribute('data-hovered', 'true');
  });
});
```

### E2E test: Level-up flow with WebSocket

```typescript
// tests/e2e/level-up-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Level-up flow', () => {
  test('awards XP via WebSocket and displays level-up banner', async ({ page }) => {
    // Mock WebSocket to control XP events
    await page.routeWebSocket('wss://*/ws/xp', ws => {
      ws.onMessage(message => {
        const data = JSON.parse(message as string);
        if (data.type === 'subscribe') {
          ws.send(JSON.stringify({ type: 'subscribed', channel: 'xp' }));
        }
      });
      
      // Simulate XP award after 500ms
      setTimeout(() => {
        ws.send(JSON.stringify({
          type: 'xp_awarded',
          amount: 500,
          totalXP: 1000,
          triggeredLevelUp: true,
          newLevel: 5
        }));
      }, 500);
    });

    await page.goto('/dashboard');
    
    // Verify initial state
    await expect(page.locator('[data-testid="current-level"]')).toHaveText('Level 4');
    await expect(page.locator('[data-testid="level-up-banner"]')).not.toBeVisible();
    
    // Wait for WebSocket event (within 2s constraint)
    const startTime = Date.now();
    await expect(page.locator('[data-testid="level-up-banner"]')).toBeVisible({ 
      timeout: 2000 
    });
    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(2000);
    
    // Verify banner content
    await expect(page.locator('[data-testid="level-up-banner"]')).toContainText('Level 5');
    
    // Verify level updated
    await expect(page.locator('[data-testid="current-level"]')).toHaveText('Level 5');
    
    // Banner should auto-hide after animation
    await expect(page.locator('[data-testid="level-up-banner"]')).not.toBeVisible({ 
      timeout: 5000 
    });
  });

  test('updates XP bar in real-time within 1-2 seconds', async ({ page }) => {
    const receivedTimestamps: number[] = [];
    
    await page.routeWebSocket('wss://*/ws/xp', ws => {
      ws.onMessage(message => {
        if (JSON.parse(message as string).type === 'subscribe') {
          // Send XP update immediately
          ws.send(JSON.stringify({
            type: 'xp_update',
            currentXP: 750,
            maxXP: 1000,
            timestamp: Date.now()
          }));
        }
      });
    });

    await page.goto('/dashboard');
    
    // Measure time to UI update
    const beforeUpdate = Date.now();
    await expect(page.locator('[data-testid="xp-bar-fill"]')).toHaveCSS('width', /75%/);
    const updateTime = Date.now() - beforeUpdate;
    
    expect(updateTime).toBeLessThan(2000);
    console.log(`XP bar updated in ${updateTime}ms`);
  });
});
```

### Visual regression test: Skill card baseline

```typescript
// tests/visual/skill-card.visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Skill Card Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    // Disable all animations for deterministic screenshots
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
        .particle-container { display: none !important; }
      `
    });
  });

  test('skill card at 0% XP', async ({ page }) => {
    await page.goto('/storybook-iframe?id=components-skillcard--empty');
    await page.waitForSelector('[data-testid="skill-card"]');
    
    await expect(page.locator('[data-testid="skill-card"]'))
      .toHaveScreenshot('skill-card-0-percent.png', {
        maxDiffPixels: 50,
        threshold: 0.2
      });
  });

  test('skill card at 75% XP', async ({ page }) => {
    await page.goto('/storybook-iframe?id=components-skillcard--three-quarters');
    await page.waitForSelector('[data-testid="skill-card"]');
    
    await expect(page.locator('[data-testid="skill-card"]'))
      .toHaveScreenshot('skill-card-75-percent.png');
  });

  test('skill card at max level', async ({ page }) => {
    await page.goto('/storybook-iframe?id=components-skillcard--max-level');
    await page.waitForSelector('[data-testid="skill-card"]');
    
    await expect(page.locator('[data-testid="skill-card"]'))
      .toHaveScreenshot('skill-card-max-level.png');
  });

  test('dashboard full view', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Mask dynamic content
    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      mask: [
        page.locator('[data-testid="timestamp"]'),
        page.locator('[data-testid="loading-spinner"]')
      ]
    });
  });
});
```

### WebSocket test: Real-time XP synchronization

```typescript
// tests/unit/hooks/useXPSync.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import WS from 'vitest-websocket-mock';
import { describe, test, expect, beforeEach, afterEach } from 'vitest';
import { useXPSync } from '@/hooks/useXPSync';

describe('useXPSync', () => {
  let server: WS;

  beforeEach(() => {
    server = new WS('ws://localhost:8080/ws/xp');
  });

  afterEach(() => {
    WS.clean();
  });

  test('connects and receives initial XP state', async () => {
    const { result } = renderHook(() => useXPSync('user-123'));
    
    await server.connected;
    expect(result.current.isConnected).toBe(true);
    
    // Server sends initial state
    server.send(JSON.stringify({ 
      type: 'init', 
      xp: 1500, 
      level: 3 
    }));
    
    await waitFor(() => {
      expect(result.current.xp).toBe(1500);
      expect(result.current.level).toBe(3);
    });
  });

  test('handles real-time XP updates', async () => {
    const { result } = renderHook(() => useXPSync('user-123'));
    await server.connected;
    
    server.send(JSON.stringify({ type: 'init', xp: 1000, level: 2 }));
    
    await waitFor(() => expect(result.current.xp).toBe(1000));
    
    // Simulate voice pipeline XP event
    act(() => {
      server.send(JSON.stringify({ 
        type: 'xp_awarded', 
        amount: 250,
        totalXP: 1250,
        source: 'voice_interaction'
      }));
    });
    
    await waitFor(() => {
      expect(result.current.xp).toBe(1250);
    });
  });

  test('queues updates during disconnection', async () => {
    const { result } = renderHook(() => useXPSync('user-123'));
    await server.connected;
    
    // Disconnect
    server.close();
    await waitFor(() => expect(result.current.isConnected).toBe(false));
    
    // Local XP gain while offline
    act(() => {
      result.current.addLocalXP(100);
    });
    
    expect(result.current.pendingSync).toBe(true);
    expect(result.current.localXP).toBe(100);
    
    // Reconnect
    server = new WS('ws://localhost:8080/ws/xp');
    await server.connected;
    
    // Verify sync message sent
    await expect(server).toReceiveMessage(
      expect.stringContaining('"type":"sync_request"')
    );
  });

  test('triggers level-up callback when threshold reached', async () => {
    const onLevelUp = vi.fn();
    const { result } = renderHook(() => useXPSync('user-123', { onLevelUp }));
    
    await server.connected;
    server.send(JSON.stringify({ type: 'init', xp: 950, level: 2, maxXP: 1000 }));
    
    act(() => {
      server.send(JSON.stringify({
        type: 'xp_awarded',
        amount: 100,
        totalXP: 50,
        triggeredLevelUp: true,
        newLevel: 3
      }));
    });
    
    await waitFor(() => {
      expect(onLevelUp).toHaveBeenCalledWith({ oldLevel: 2, newLevel: 3 });
    });
  });
});
```

## CI/CD workflow (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI - React PWA Dashboard

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  PNPM_VERSION: '10'

jobs:
  # Unit tests with sharding for speed
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}
      - uses: actions/setup-node@v5
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - name: Run Vitest (shard ${{ matrix.shard }}/4)
        run: pnpm vitest run --reporter=blob --shard=${{ matrix.shard }}/4
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: vitest-blob-${{ matrix.shard }}
          path: .vitest-reports/
          retention-days: 1

  # E2E tests with Playwright container
  e2e-tests:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.57.0-noble
      options: --user 1001
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}
      - uses: actions/setup-node@v5
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - name: Run Playwright (shard ${{ matrix.shard }}/4)
        run: npx playwright test --shard=${{ matrix.shard }}/4 --reporter=blob
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-blob-${{ matrix.shard }}
          path: blob-report/
          retention-days: 1

  # Visual regression (separate for baseline management)
  visual-regression:
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.57.0-noble
      options: --user 1001
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}
      - uses: actions/setup-node@v5
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: npx playwright test --project=visual-regression
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: visual-diff-results
          path: test-results/
          retention-days: 7

  # Lighthouse CI for PWA audits
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}
      - uses: actions/setup-node@v5
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v12
        with:
          uploadArtifacts: true
          temporaryPublicStorage: true
          configPath: ./lighthouserc.js

  # Merge test reports
  merge-reports:
    needs: [unit-tests, e2e-tests]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}
      - uses: actions/setup-node@v5
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - uses: actions/download-artifact@v4
        with:
          path: all-reports
          pattern: playwright-blob-*
          merge-multiple: true
      - run: npx playwright merge-reports --reporter=html ./all-reports
      - uses: actions/upload-artifact@v4
        with:
          name: html-report
          path: playwright-report/
          retention-days: 30
```

## Testing animations with Framer Motion

Testing animations requires a dual approach: **disable animations for deterministic unit tests**, but **verify animation behavior in E2E tests** via data attributes and computed styles.

### Framer Motion mock for unit tests

```typescript
// src/test-setup.ts
import '@testing-library/jest-dom';
import { MotionGlobalConfig } from 'framer-motion';

// Globally disable animations in test environment
MotionGlobalConfig.skipAnimations = true;
```

For more control, wrap components in `MotionConfig`:

```typescript
// Custom render helper
import { MotionConfig } from 'framer-motion';

export const renderWithMotion = (ui: React.ReactElement) => {
  return render(
    <MotionConfig transition={{ duration: 0 }}>
      {ui}
    </MotionConfig>
  );
};
```

### E2E animation verification via data attributes

```typescript
// In your animated component
<motion.div
  data-testid="level-up-banner"
  data-animation-state={isAnimating ? "animating" : "complete"}
  initial={{ opacity: 0, y: -50 }}
  animate={{ opacity: 1, y: 0 }}
  onAnimationComplete={() => setIsAnimating(false)}
>
  Level Up!
</motion.div>
```

```typescript
// E2E test
test('level-up banner animation completes', async ({ page }) => {
  await page.goto('/dashboard?trigger=levelup');
  
  // Wait for animation to start
  await expect(page.locator('[data-animation-state="animating"]')).toBeVisible();
  
  // Wait for completion
  await expect(page.locator('[data-animation-state="complete"]')).toBeVisible({ 
    timeout: 3000 
  });
  
  // Verify final CSS state
  const banner = page.locator('[data-testid="level-up-banner"]');
  await expect(banner).toHaveCSS('opacity', '1');
  await expect(banner).toHaveCSS('transform', 'matrix(1, 0, 0, 1, 0, 0)');
});
```

### XP bar animation testing

```typescript
test('XP bar animates smoothly to new value', async ({ page }) => {
  await page.goto('/dashboard');
  
  const getBarWidth = () => page.locator('.xp-bar-fill').evaluate(
    el => parseFloat(getComputedStyle(el).width)
  );
  
  const initialWidth = await getBarWidth();
  
  // Trigger XP gain
  await page.click('[data-testid="gain-xp"]');
  
  // Wait for animation to start (width changes)
  await page.waitForFunction(
    (initial) => {
      const el = document.querySelector('.xp-bar-fill');
      return parseFloat(getComputedStyle(el!).width) !== initial;
    },
    initialWidth
  );
  
  // Verify final state
  await page.waitForTimeout(500); // Animation duration
  const finalWidth = await getBarWidth();
  expect(finalWidth).toBeGreaterThan(initialWidth);
});
```

## Audio testing pattern

**Playwright cannot detect audio playback directly.** The solution is to intercept `HTMLAudioElement.play()` calls and expose them for verification.

### Intercepting audio calls in E2E

```typescript
// tests/e2e/audio.spec.ts
test.describe('Sound effects', () => {
  test.beforeEach(async ({ page }) => {
    // Inject audio spy before page loads
    await page.addInitScript(() => {
      window.__audioPlayCalls = [];
      const originalPlay = HTMLAudioElement.prototype.play;
      HTMLAudioElement.prototype.play = function() {
        window.__audioPlayCalls.push({
          src: this.src,
          timestamp: Date.now()
        });
        return originalPlay.call(this);
      };
    });
  });

  test('plays level-up sound on level-up event', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Trigger level up
    await page.click('[data-testid="debug-level-up"]');
    
    // Verify audio played
    const audioCalls = await page.evaluate(() => window.__audioPlayCalls);
    expect(audioCalls.some(call => call.src.includes('level-up.mp3'))).toBe(true);
  });

  test('respects mute setting', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Mute audio
    await page.click('[data-testid="mute-toggle"]');
    
    // Clear previous calls
    await page.evaluate(() => { window.__audioPlayCalls = []; });
    
    // Trigger sound event
    await page.click('[data-testid="earn-achievement"]');
    
    // Verify no audio played
    const audioCalls = await page.evaluate(() => window.__audioPlayCalls);
    expect(audioCalls).toHaveLength(0);
  });
});
```

### Unit test mock for audio

```typescript
// src/test-setup.ts
Object.defineProperty(window.HTMLMediaElement.prototype, 'play', {
  configurable: true,
  writable: true,
  value: vi.fn().mockImplementation(() => Promise.resolve())
});

// In test file
test('SoundManager plays correct sound', () => {
  const playSpy = vi.spyOn(HTMLAudioElement.prototype, 'play');
  const soundManager = new SoundManager();
  
  soundManager.play('level-up');
  
  expect(playSpy).toHaveBeenCalled();
  expect(soundManager.getEventLog()).toContainEqual(
    expect.objectContaining({ sound: 'level-up', action: 'play' })
  );
});
```

## PWA testing checklist with Playwright

### Service worker registration

```typescript
test('registers service worker on load', async ({ page, context }) => {
  const swPromise = context.waitForEvent('serviceworker');
  await page.goto('/');
  
  const sw = await swPromise;
  expect(sw.url()).toContain('sw.js');
  
  // Verify SW controls the page
  const isControlling = await page.evaluate(
    () => navigator.serviceWorker.controller !== null
  );
  expect(isControlling).toBe(true);
});
```

### Offline behavior testing

```typescript
test('works offline after caching', async ({ page, context }) => {
  // First visit to populate cache
  await page.goto('/dashboard');
  await page.waitForFunction(() => navigator.serviceWorker.controller);
  
  // Go offline
  await context.setOffline(true);
  
  // Reload should work from cache
  await page.reload();
  await expect(page.locator('h1')).toContainText('Dashboard');
  
  // Verify offline indicator
  await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
  
  // Restore connection
  await context.setOffline(false);
});
```

### Manifest validation

```typescript
test('has valid PWA manifest', async ({ request }) => {
  const response = await request.get('/manifest.json');
  expect(response.ok()).toBe(true);
  
  const manifest = await response.json();
  
  // Required fields for installability
  expect(manifest.name).toBeTruthy();
  expect(manifest.short_name).toBeTruthy();
  expect(manifest.start_url).toBeTruthy();
  expect(manifest.display).toMatch(/standalone|fullscreen|minimal-ui/);
  
  // Required icon sizes
  const sizes = manifest.icons.map((i: any) => i.sizes);
  expect(sizes).toContain('192x192');
  expect(sizes).toContain('512x512');
});
```

### Lighthouse CI configuration

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

## State file pattern for AI feedback

The state file pattern enables Claude Code to verify UI state through structured JSON rather than visual inspection. This provides **sub-second feedback** on whether changes achieved the desired effect.

### State dump utility

```typescript
// tests/fixtures/state-dump.ts
import { Page } from '@playwright/test';

export interface UIStateDump {
  route: string;
  timestamp: string;
  gamification: {
    xp: number;
    level: number;
    skills: { name: string; level: number; xp: number }[];
    achievements: string[];
  };
  ui: {
    visibleBanners: string[];
    activeAnimations: string[];
    errors: string[];
  };
  network: {
    pendingRequests: number;
    wsConnected: boolean;
  };
}

export async function dumpUIState(page: Page): Promise<UIStateDump> {
  return await page.evaluate(() => ({
    route: window.location.pathname,
    timestamp: new Date().toISOString(),
    gamification: window.__GAMIFICATION_STATE__ || {},
    ui: {
      visibleBanners: Array.from(document.querySelectorAll('[data-testid*="banner"]:not([hidden])'))
        .map(el => el.getAttribute('data-testid')),
      activeAnimations: Array.from(document.querySelectorAll('[data-animation-state="animating"]'))
        .map(el => el.getAttribute('data-testid')),
      errors: window.__TEST_ERRORS__ || []
    },
    network: {
      pendingRequests: window.__PENDING_REQUESTS__ || 0,
      wsConnected: window.__WS_CONNECTED__ || false
    }
  }));
}
```

### Test that writes state for Claude

```typescript
// tests/e2e/ai-feedback.spec.ts
import { test, expect } from '@playwright/test';
import { dumpUIState } from '../fixtures/state-dump';
import * as fs from 'fs';

test('dashboard state after XP award', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');
  
  // Trigger action
  await page.click('[data-testid="earn-xp"]');
  await page.waitForTimeout(500);
  
  // Dump state for AI analysis
  const state = await dumpUIState(page);
  fs.writeFileSync(
    'test-results/state-dump.json',
    JSON.stringify(state, null, 2)
  );
  
  // Structured assertions Claude can parse
  expect(state.gamification.xp).toBeGreaterThan(0);
  expect(state.ui.errors).toHaveLength(0);
  expect(state.network.wsConnected).toBe(true);
});
```

### CLAUDE.md instructions for the loop

```markdown
## Development Loop (Ralph Wiggum Pattern)

1. Read `test-results/state-dump.json` for current UI state
2. Read `test-results/ai-feedback.jsonl` for test failures
3. Implement fix based on structured error data
4. Run: `pnpm test && pnpm e2e`
5. On pass: commit and move to next task
6. On fail: parse error JSON, iterate

### State File Schema
- `gamification.xp`: Current XP value (number)
- `gamification.level`: Current level (number)
- `ui.visibleBanners`: Array of visible banner test IDs
- `ui.errors`: Runtime errors captured
- `network.wsConnected`: WebSocket connection status
```

## Performance testing approach

### Memory leak detection during animations

```typescript
test('no memory leaks during repeated animations', async ({ page }) => {
  const client = await page.context().newCDPSession(page);
  await page.goto('/dashboard');
  
  // Initial heap measurement
  await client.send('HeapProfiler.collectGarbage');
  let metrics = await client.send('Performance.getMetrics');
  const initialHeap = metrics.metrics.find(m => m.name === 'JSHeapUsedSize')?.value || 0;
  
  // Trigger particle effect 50 times
  for (let i = 0; i < 50; i++) {
    await page.click('[data-testid="trigger-particles"]');
    await page.waitForTimeout(100);
  }
  
  // Final measurement
  await client.send('HeapProfiler.collectGarbage');
  metrics = await client.send('Performance.getMetrics');
  const finalHeap = metrics.metrics.find(m => m.name === 'JSHeapUsedSize')?.value || 0;
  
  // Allow 20% variance
  expect(finalHeap).toBeLessThan(initialHeap * 1.2);
});
```

### Animation FPS verification

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
        resolve({ fps: Math.round(1000 / avgDelta), jankFrames: deltas.filter(d => d > 33).length });
      }, duration);
    });
  }, durationMs);
}

test('animations maintain 60fps', async ({ page }) => {
  await page.goto('/dashboard');
  await page.click('[data-testid="start-animation"]');
  
  const { fps, jankFrames } = await measureFPS(page);
  
  expect(fps).toBeGreaterThanOrEqual(55);
  expect(jankFrames).toBeLessThan(5);
});
```

### Bundle size monitoring

```javascript
// vite.config.ts
import bundlesize from 'vite-plugin-bundlesize';

export default defineConfig({
  plugins: [
    bundlesize({
      limits: [
        { name: 'assets/index-*.js', limit: '150 kB', mode: 'gzip' },
        { name: '**/*.css', limit: '30 kB', mode: 'gzip' }
      ]
    })
  ]
});
```

## Key resources and documentation

### Core Testing Tools
- **Playwright**: https://playwright.dev/docs/intro
- **Vitest**: https://vitest.dev/guide/
- **React Testing Library**: https://testing-library.com/docs/react-testing-library/intro/

### PWA & Service Workers
- **Playwright Service Workers**: https://playwright.dev/docs/service-workers
- **Lighthouse CI**: https://github.com/GoogleChrome/lighthouse-ci
- **Vite PWA Plugin**: https://vite-pwa-org.netlify.app/

### Animation & Audio
- **Playwright WebSocket Routing**: https://playwright.dev/docs/api/class-websocketroute
- **Framer Motion Testing**: https://github.com/motiondivision/motion/issues/1690
- **Chromatic Animation Handling**: https://www.chromatic.com/docs/animations/

### AI-Assisted Development
- **Ralph Wiggum Pattern**: https://github.com/snwfdhmp/awesome-ralph
- **Claude Code Best Practices**: https://www.anthropic.com/engineering/claude-code-best-practices
- **Smart Ralph Plugin**: https://github.com/tzachbon/smart-ralph

### Visual Testing
- **Playwright Screenshots**: https://playwright.dev/docs/test-snapshots
- **Docker Images**: https://playwright.dev/docs/docker

## Conclusion

The 2026 testing landscape has consolidated around **Playwright for E2E** (including PWA and WebSocket testing) and **Vitest for unit tests** in Vite projects. For AI-assisted development, the critical innovation is shifting from screenshot-based verification to **structured state dumps**—JSON files that Claude Code can parse, compare, and act upon in sub-second feedback loops.

Three patterns define effective AI-assisted testing: First, expose animation state via `data-animation-state` attributes rather than relying on timing. Second, intercept audio API calls to log sound events for verification. Third, implement the **Ralph Wiggum loop**—a verification-driven development cycle where tests serve as hard rails and state persists in files rather than conversation context.

For your gamification dashboard specifically: use Docker containers to ensure font rendering consistency between WSL2 and CI, implement `dumpUIState()` to export XP/level/skill data for Claude to verify, and configure Lighthouse CI with PWA assertions to catch service worker regressions automatically. The total cost for this setup is effectively **$0**—Playwright, Vitest, and Lighthouse CI are all open source with free CI integration.