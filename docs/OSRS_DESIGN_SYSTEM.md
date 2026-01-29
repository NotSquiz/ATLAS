# ATLAS Command Centre - OSRS Design System

**Version:** 1.0
**Date:** January 2026
**Status:** Planning Complete - Ready for Implementation

---

## Design Philosophy

The ATLAS Command Centre captures the nostalgic, satisfying feel of Old School RuneScape progression while using **entirely original assets**. The goal is authentic retro MMO aesthetic, not a copy.

**Core Principles:**
1. **Zero border-radius** - Squared corners everywhere
2. **Beveled 3D borders** - Light top/left, dark bottom/right
3. **Snappy animations** - Ease-out, no bounce, 600ms tick feel
4. **High contrast text** - Yellow/green/white on dark backgrounds
5. **Pixel-perfect rendering** - Crisp edges, no anti-aliasing blur

---

## Color Palette

### Tailwind Configuration

```javascript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        osrs: {
          // Panel backgrounds (tan/stone - OSRS authentic)
          'body-main': '#e2dbc8',
          'body-light': '#d8ccb4',
          'body-mid': '#d0bd97',
          'body-dark': '#b8a282',
          'body-border': '#94866d',
          'body-bg': '#c0a886',
          'sidebar': '#cfc08d',

          // Dark backgrounds (for dark theme variant)
          'dark-bg': '#28221d',
          'dark-panel': '#18140c',
          'dark-mid': '#1a1a2e',

          // Button system
          'button-bg': '#605443',
          'button-border': '#3c352a',
          'button-dark': '#18140c',
          'button-light': '#3a301d',

          // Accent colors
          'gold': '#ff9900',
          'gold-rich': '#f7c600',
          'amber': '#fda63a',

          // XP bar colors
          'xp-fill': '#00ff00',
          'xp-bg': '#18140c',
          'xp-border': '#3c352a',

          // Text hierarchy
          'text-yellow': '#ffff00',
          'text-green': '#00ff00',
          'text-red': '#ff0000',
          'text-orange': '#ff7f00',
          'text-cyan': '#00ffff',
          'text-white': '#ffffff',
          'text-grey': '#808080',

          // Links
          'link': '#936039',
          'link-hover': '#ba0000',

          // Bevel colors (for 3D effect)
          'bevel-light': '#cfc08d',
          'bevel-dark': '#3c352a',

          // Scrollbar
          'scroll-outer': '#746241',
          'scroll-inner': '#b09060',
        }
      },
      borderRadius: {
        'osrs': '0px',
      },
      fontFamily: {
        'osrs': ['RuneScape Plain', 'Pixelify Sans', 'VT323', 'monospace'],
        'osrs-header': ['Silkscreen', 'RuneScape Plain', 'monospace'],
      }
    }
  }
}
```

### Color Usage Guidelines

| Element | Color | Hex |
|---------|-------|-----|
| Panel background | body-mid | `#d0bd97` |
| Dark panel background | dark-panel | `#18140c` |
| XP bar fill | text-green | `#00ff00` |
| XP bar background | dark-panel | `#18140c` |
| Level numbers | text-yellow | `#ffff00` |
| Skill names | text-white | `#ffffff` |
| Quest complete | text-green | `#00ff00` |
| Quest incomplete | text-grey | `#808080` |
| Level up text | gold-rich | `#f7c600` |
| Error/warning | text-red | `#ff0000` |
| Bevel top/left | bevel-light | `#cfc08d` |
| Bevel bottom/right | bevel-dark | `#3c352a` |

---

## Typography

### Font Stack (CORRECTED)

> **Important:** Press Start 2P is NOT appropriate for OSRS. It's a 1980s Namco arcade font with Nintendo aesthetics.

**Primary fonts:**
- **RuneStar Fonts** (CC0) - Exact pixel-by-pixel OSRS recreation
  - Download: https://github.com/RuneStar/fonts/releases/latest
- **Pixelify Sans** (Google Fonts) - Best alternative with multiple weights
- **Silkscreen** (Google Fonts) - Clean pixel aesthetic for headers
- **VT323** (Google Fonts) - Terminal style for numbers/stats

### Font Loading

```css
/* frontend/src/styles/fonts.css */

/* Primary: RuneStar (download TTF/WOFF2 to public/fonts/) */
@font-face {
  font-family: 'RuneScape Plain';
  src: url('/fonts/runescape-plain-12.woff2') format('woff2'),
       url('/fonts/runescape-plain-12.ttf') format('truetype');
  font-weight: 400;
  font-display: swap;
}

/* Fallback: Pixelify Sans from Google */
@import url('https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;500;600;700&family=Silkscreen:wght@400;700&family=VT323&display=swap');

/* Pixel rendering (disable anti-aliasing) */
.pixel-font {
  font-family: 'RuneScape Plain', 'Pixelify Sans', 'VT323', monospace;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: grayscale;
  font-smooth: never;
  text-rendering: optimizeSpeed;
}
```

### Font Size Scale

| Element | OSRS Native | Web Size | CSS |
|---------|-------------|----------|-----|
| XP/stats numbers | 11px | 14px | `text-sm` |
| Body text | 12px | 16px | `text-base` |
| Interface labels | 12px | 14px | `text-sm` |
| Skill names | 12px | 18px | `text-lg` |
| Section headers | - | 24px | `text-2xl` |
| Page titles | - | 32px | `text-3xl` |
| Level-up number | - | 48-64px | `text-5xl` / `text-6xl` |

---

## Component Specifications

### Beveled Panel

The signature OSRS 3D panel effect:

```tsx
// components/osrs/Panel.tsx
interface PanelProps {
  children: React.ReactNode;
  variant?: 'light' | 'dark';
  className?: string;
}

export function Panel({ children, variant = 'light', className }: PanelProps) {
  const bg = variant === 'light' ? 'bg-osrs-body-mid' : 'bg-osrs-dark-panel';

  return (
    <div className={cn(
      bg,
      'border-2 border-osrs-body-border',
      'border-t-osrs-bevel-light border-l-osrs-bevel-light',
      'border-b-osrs-bevel-dark border-r-osrs-bevel-dark',
      'rounded-osrs p-3',
      className
    )}>
      {children}
    </div>
  );
}
```

### Skill Card

```
┌─────────────────────────────────────┐
│  ┌──────┐                           │
│  │ ICON │  STRENGTH           23    │  ← Yellow level number
│  │32x32 │  ████████████░░░░        │  ← Green XP bar
│  └──────┘  1,240 / 2,500 XP        │  ← Grey XP text
└─────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Width | 200-280px |
| Height | 70-90px |
| Padding | 12px |
| Icon size | 32x32 (scaled 2x to 64x64 for display) |
| Border | 2px beveled |
| Background | `#d0bd97` (light) or `#18140c` (dark) |
| Corner radius | 0px |

### XP Progress Bar

```
┌────────────────────────────────────────┐
│████████████████████░░░░░░░░░░░░░░░░░░░│  ← Green fill on dark bg
└────────────────────────────────────────┘
         1,240 / 2,500 XP                   ← Centered text overlay
```

| Property | Value |
|----------|-------|
| Height | 14-18px |
| Border | 2px solid `#3c352a` |
| Background | `#18140c` |
| Fill | `#00ff00` |
| Text | Yellow `#ffff00`, centered |
| Corner radius | 0px |

### Quest Item

```
┌─────────────────────────────────────────────────┐
│  ○  Morning Triple                    +300 XP   │  ← Incomplete
│  ✓  Movement Minimum                  +100 XP   │  ← Complete (green)
└─────────────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Height | 36-44px |
| Checkbox | 16x16, custom pixel style |
| Text complete | `#00ff00` |
| Text incomplete | `#ffffff` |
| XP reward | `#ffff00` right-aligned |

### Level-Up Banner Modal

```
╔═══════════════════════════════════════════════╗
║                                               ║
║              ⚔️  STRENGTH  ⚔️                 ║
║                                               ║
║                 Level 25                      ║  ← Large gold text
║                                               ║
║           "Journeyman Strength"               ║  ← Milestone name
║                                               ║
╚═══════════════════════════════════════════════╝
```

| Property | Value |
|----------|-------|
| Width | 320-400px (fixed) |
| Border | 4px beveled gold |
| Background | `#d0bd97` with subtle gradient |
| Level text | 48-64px, gold `#f7c600` |
| Duration | 3-4 seconds |

---

## Animation Specifications

### Timing Principles

OSRS operates on **600ms server ticks**. Animations should feel "snappy" and immediate, not smooth and bouncy.

| Timing | Use Case |
|--------|----------|
| **0ms** | Instant state changes |
| **150-200ms** | Micro-interactions (hover, press) |
| **300-400ms** | UI transitions (panels, modals) |
| **600ms** | Game-feel transitions (XP bar fill) |
| **2000-4000ms** | Celebration sequences (level-up) |

### Easing Curves

| Effect | Easing | Notes |
|--------|--------|-------|
| Appear/Enter | `ease-out` | Fast start, gentle stop |
| Disappear/Exit | `ease-in` | Gentle start, fast end |
| Particle burst | `linear` | Consistent fall |
| Number counting | `ease-out` | Satisfying deceleration |
| **Avoid** | `bounce`, `elastic` | Too playful for OSRS feel |

### Level-Up Animation Sequence

| Time | Event | Implementation |
|------|-------|----------------|
| 0ms | Particles trigger | tsParticles fireworks preset |
| 0ms | Sound plays | level-up.mp3 |
| 200ms | Banner appears | Framer Motion scale spring |
| 400ms | Icon displays | Fade + slight y translation |
| 600ms | Level number | Scale [0 → 1.3 → 1] |
| 800ms | Milestone text | Fade in |
| 2000ms | Particles fade | Opacity transition |
| 3500ms | Banner exits | Scale down + fade |

### Framer Motion Configuration

```tsx
// Level-up banner animation
const bannerVariants = {
  hidden: { scale: 0, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: { type: 'spring', stiffness: 200, damping: 20 }
  },
  exit: {
    scale: 0,
    opacity: 0,
    transition: { duration: 0.3 }
  }
};

// Level number pop effect
const levelNumberVariants = {
  hidden: { scale: 0 },
  visible: {
    scale: [0, 1.3, 1],
    transition: { delay: 0.6, duration: 0.5, ease: 'easeOut' }
  }
};

// XP bar fill
const xpBarVariants = {
  initial: { width: '0%' },
  animate: (progress: number) => ({
    width: `${progress}%`,
    transition: { duration: 0.6, ease: 'easeOut' }
  })
};
```

---

## Particle System (tsParticles)

### Fireworks Configuration

```tsx
// Lazy-load particles only when level-up triggers
const Particles = lazy(() => import('react-particles'));

const fireworksOptions = {
  preset: 'fireworks',
  background: { color: 'transparent' },
  particles: {
    number: { value: 150 },  // 50-100 on mobile
    color: { value: ['#ffff00', '#ffffff', '#ff9900', '#00ff00'] },
    life: { duration: { value: 2 } },
  },
  emitters: {
    position: { x: 50, y: 50 },
    rate: { quantity: 5, delay: 0.1 },
  }
};
```

### Performance Guidelines

| Device | Particle Count |
|--------|---------------|
| Mobile | 50-100 |
| Tablet | 100-150 |
| Desktop | 150-200 |

---

## Icon System

### Skill Icons (Midjourney Generation)

You have Midjourney - use these prompts for consistent 32x32 pixel art icons:

```
Base prompt template:
"32x32 pixel art icon, [SUBJECT], medieval fantasy RPG style,
limited color palette, dark background, crisp edges,
no anti-aliasing, retro video game aesthetic --ar 1:1 --v 6"

Skill-specific prompts:

STRENGTH:
"32x32 pixel art icon, crossed swords, medieval fantasy RPG style,
golden blades, dark background, crisp edges --ar 1:1 --v 6"

ENDURANCE:
"32x32 pixel art icon, running boots with wings, medieval fantasy,
leather brown, motion lines, dark background --ar 1:1 --v 6"

MOBILITY:
"32x32 pixel art icon, flexible figure stretching, yoga pose,
zen energy glow, dark background, retro RPG style --ar 1:1 --v 6"

NUTRITION:
"32x32 pixel art icon, golden apple with sparkle, medieval fantasy,
health potion style, dark background --ar 1:1 --v 6"

RECOVERY:
"32x32 pixel art icon, crescent moon with stars, night sky,
sleep and rest theme, dark background, retro RPG --ar 1:1 --v 6"

CONSISTENCY:
"32x32 pixel art icon, eternal flame torch, streak fire,
burning consistently, dark background, RPG style --ar 1:1 --v 6"

WORK:
"32x32 pixel art icon, quill and scroll, productivity theme,
medieval scribe, dark background, retro game style --ar 1:1 --v 6"
```

**Post-processing:**
1. Export at 32x32 from Midjourney
2. Clean up in Aseprite/Piskel if needed
3. Ensure crisp pixel edges (no blur)
4. Save as PNG with transparency

### Free Icon Resources (Backup)

| Resource | Count | License | Link |
|----------|-------|---------|------|
| 7Soul RPG Icons | 496 | CC0 | [OpenGameArt](https://opengameart.org/content/496-pixel-art-icons-for-medievalfantasy-rpg) |
| Game-icons.net | 4,170+ | CC BY 3.0 | [game-icons.net](https://game-icons.net/) |
| Kenney Game Icons | 105+ | CC0 | [kenney.nl](https://kenney.nl/assets/game-icons) |

### Icon Display

```css
/* Pixel-perfect scaling */
.skill-icon {
  width: 64px;  /* 32px scaled 2x */
  height: 64px;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

@media (min-width: 1024px) {
  .skill-icon {
    width: 96px;  /* 32px scaled 3x */
    height: 96px;
  }
}
```

---

## Sound Design

### Legal Note

Jagex explicitly prohibits using OSRS sounds (Section 6.1.3 of Fan Content Policy). We must create or source original sounds.

### Sound Resources

| Resource | License | Best For |
|----------|---------|----------|
| [Kenney Audio](https://kenney.nl/assets) | CC0 | UI sounds, RPG effects |
| [JSFXR](https://sfxr.me/) | Generate | Custom 8-bit sounds |
| [OpenGameArt 512 SFX](https://opengameart.org/content/512-sound-effects-8-bit-style) | CC0 | Retro sound pack |
| [ElevenLabs Sound Effects](https://elevenlabs.io/sound-effects) | AI | Text-to-sound generation |

### Required Sounds

| Event | Sound Character | Duration |
|-------|-----------------|----------|
| **Level up** | Ascending arpeggio, triumphant fanfare | 2-3 seconds |
| **XP gain** | Quick positive chime | 0.3-0.5 seconds |
| **Quest complete** | Achievement flourish | 1-1.5 seconds |
| **Button click** | Subtle click/tap | 0.1 seconds |
| **Error** | Low negative tone | 0.3 seconds |

### What Makes Level-Up Sound Satisfying

- **Ascending notes** - Rising = success
- **Major key** - Universally positive
- **Clear resolution** - Ends on root note
- **Short duration** - 2-4 seconds max
- **Distinct attack** - Immediate, not faded in

### JSFXR Settings for Level-Up

```
Preset: Powerup
Wave type: Square
Attack: 0.05
Sustain: 0.3
Decay: 0.2
Frequency: 0.5 (start low)
Frequency slide: 0.3 (ascending)
```

---

## CSS Utilities

### Global Styles

```css
/* frontend/src/styles/globals.css */

/* OSRS gold text with pixel outline */
.osrs-text-gold {
  font-family: var(--font-osrs);
  color: #ffff00;
  text-shadow:
    1px 1px 0 #000,
    -1px -1px 0 #000,
    1px -1px 0 #000,
    -1px 1px 0 #000;
}

/* Beveled panel base */
.osrs-panel {
  background: #d0bd97;
  border: 2px solid #94866d;
  border-top-color: #cfc08d;
  border-left-color: #cfc08d;
  border-bottom-color: #3c352a;
  border-right-color: #3c352a;
  border-radius: 0;
}

/* Dark variant */
.osrs-panel-dark {
  background: #18140c;
  border-color: #3c352a;
  border-top-color: #4a4035;
  border-left-color: #4a4035;
  border-bottom-color: #0a0a0a;
  border-right-color: #0a0a0a;
}

/* Pixel art images */
.pixel-art {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  -ms-interpolation-mode: nearest-neighbor;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .level-up-animation {
    animation: none;
    transition: opacity 0.3s ease-out;
  }

  .particle-container {
    display: none;
  }
}
```

### Tailwind Utilities

```javascript
// tailwind.config.ts plugins
plugins: [
  function({ addUtilities }) {
    addUtilities({
      '.text-osrs-shadow': {
        'text-shadow': '1px 1px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000'
      },
      '.pixel-render': {
        'image-rendering': 'pixelated',
        '-ms-interpolation-mode': 'nearest-neighbor'
      },
      '.no-font-smooth': {
        '-webkit-font-smoothing': 'none',
        '-moz-osx-font-smoothing': 'grayscale',
        'font-smooth': 'never'
      }
    })
  }
]
```

---

## Responsive Design

### Breakpoints

OSRS interfaces don't scale smoothly - use discrete size steps:

```css
:root {
  --pixel-unit: 1px;
  --icon-scale: 2;
}

@media (min-width: 768px) {
  :root {
    --pixel-unit: 1.5px;
    --icon-scale: 2.5;
  }
}

@media (min-width: 1024px) {
  :root {
    --pixel-unit: 2px;
    --icon-scale: 3;
  }
}
```

### Mobile Considerations

| Element | Desktop | Mobile |
|---------|---------|--------|
| Skill card width | 260px | 100% |
| Icon size | 64-96px | 48-64px |
| Touch targets | N/A | min 44x44px |
| Particle count | 150-200 | 50-100 |
| Font size min | 14px | 16px |

---

## Dark vs Light Theme

### Theme Variables

```css
:root {
  /* Light theme (OSRS classic) */
  --panel-bg: #d0bd97;
  --panel-border: #94866d;
  --text-primary: #000000;
  --bevel-light: #cfc08d;
  --bevel-dark: #3c352a;
}

[data-theme="dark"] {
  /* Dark theme variant */
  --panel-bg: #18140c;
  --panel-border: #3c352a;
  --text-primary: #ffffff;
  --bevel-light: #4a4035;
  --bevel-dark: #0a0a0a;
}
```

Default to dark theme for modern aesthetic; offer classic light as option.

---

## Legal Compliance

### Protected (DO NOT USE)

- "RuneScape", "OSRS", "Jagex" trademarks
- Actual game assets, sounds, music
- Specific character names, locations, lore
- Direct UI screenshots

### Safe to Use

- Game mechanics (XP systems, levels 1-99)
- Color palettes (cannot be copyrighted)
- Medieval fantasy aesthetics
- Generic skill names ("Woodcutting", "Mining", etc.)
- OSRS-style design patterns (beveled borders, pixel fonts)

### Required Disclaimer

Include in app footer/about page:

> "This application is an independent project and is not affiliated with, endorsed by, or connected to Jagex Limited or any of its games."

### Safe Marketing Language

| Safe | Avoid |
|------|-------|
| "Inspired by classic 2000s MMORPGs" | "OSRS-inspired" |
| "Nostalgic RPG progression" | "RuneScape-style" |
| "Old-school fantasy gamification" | Any Jagex trademark |

### Precedent

Melvor Idle operated successfully using original assets with OSRS-inspired mechanics. Jagex later approached them for a publishing partnership - proving the model works when assets are original.

---

## Asset Checklist

### Fonts (Download/Configure)
- [ ] RuneStar fonts TTF/WOFF2
- [ ] Pixelify Sans (Google Fonts)
- [ ] Silkscreen (Google Fonts)
- [ ] VT323 (Google Fonts)

### Icons (Create with Midjourney)
- [ ] Strength icon (32x32)
- [ ] Endurance icon (32x32)
- [ ] Mobility icon (32x32)
- [ ] Nutrition icon (32x32)
- [ ] Recovery icon (32x32)
- [ ] Consistency icon (32x32)
- [ ] Work icon (32x32)

### Sounds (Source/Create)
- [ ] Level-up fanfare (2-3s)
- [ ] XP gain chime (0.3s)
- [ ] Quest complete (1s)
- [ ] Button click (0.1s)
- [ ] Error tone (0.3s)

### PWA Assets
- [ ] App icon 192x192
- [ ] App icon 512x512
- [ ] Maskable icon variant
- [ ] Favicon

---

## References

- [RuneStar Fonts](https://github.com/RuneStar/fonts/releases)
- [OSRS Wiki CSS](https://oldschool.runescape.wiki/)
- [Pixelify Sans](https://fonts.google.com/specimen/Pixelify+Sans)
- [Kenney Assets](https://kenney.nl/assets)
- [tsParticles](https://particles.js.org/)
- [Framer Motion](https://www.framer.com/motion/)
