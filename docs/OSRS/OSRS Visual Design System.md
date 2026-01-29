# OSRS-Inspired Web App Design System Guide

Creating an authentic nostalgic experience without legal risk requires understanding exactly what makes OSRS visually distinctive while using entirely original assets. This guide provides **production-ready specifications** for a health/fitness gamification dashboard that captures that early-2000s MMO magic. Melvor Idle proved this approach works—Jagex even partnered with them after seeing their independent, original take on the concept.

## Complete color palette with Tailwind configuration

The OSRS interface uses warm earth tones dominated by **tan stone backgrounds**, **dark brown borders**, and **high-contrast text colors**. The palette below is extracted from OSRS Wiki CSS variables and RuneLite theming systems:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        osrs: {
          // Panel backgrounds (tan/stone textures)
          'body-main': '#e2dbc8',
          'body-light': '#d8ccb4',
          'body-mid': '#d0bd97',
          'body-dark': '#b8a282',
          'body-border': '#94866d',
          'body-bg': '#c0a886',
          'sidebar': '#cfc08d',
          
          // Dark backgrounds
          'dark-bg': '#28221d',
          'dark-panel': '#18140c',
          
          // Button system
          'button-bg': '#605443',
          'button-border': '#3c352a',
          'button-dark': '#18140c',
          'button-light': '#3a301d',
          
          // Accent colors
          'gold': '#ff9900',
          'gold-rich': '#f7c600',
          'amber': '#fda63a',
          
          // Text hierarchy
          'text-yellow': '#ffff00',
          'text-green': '#00ff00',
          'text-red': '#ff0000',
          'text-orange': '#ff7f00',
          'text-cyan': '#00ffff',
          'text-grey': '#808080',
          
          // Links
          'link': '#936039',
          'link-hover': '#ba0000',
          
          // Scrollbar gradient
          'scroll-outer': '#746241',
          'scroll-inner': '#b09060',
          'scroll-shadow': '#7c6945',
        }
      },
      borderRadius: {
        'osrs': '0px', // Squared corners for authenticity
      }
    }
  }
}
```

**Key design principle**: OSRS uses **zero border-radius**—sharp, squared corners create the authentic retro interface feel. The beveled 3D effect on panels uses lighter shades (`#cfc08d`) on top/left edges and darker shades (`#3c352a`) on bottom/right.

---

## Typography specification abandoning Press Start 2P

Press Start 2P is **not appropriate** for OSRS—it's an 1980s Namco arcade font with a distinctly Nintendo aesthetic. OSRS uses custom bitmap fonts originally converted from Verdana and system fonts.

### Recommended font stack

**Best option**: [RuneStar Fonts](https://github.com/RuneStar/fonts/releases/latest) (CC0 license)—exact pixel-by-pixel recreations of actual OSRS fonts, available in TTF/OTF for web embedding.

**Google Fonts alternatives**:
- **Headers**: [Silkscreen](https://fonts.google.com/specimen/Silkscreen)—clean pixel aesthetic
- **Body text**: [Pixelify Sans](https://fonts.google.com/specimen/Pixelify+Sans)—multiple weights (400-700), best readability
- **Data/stats**: [VT323](https://fonts.google.com/specimen/VT323)—terminal-style, good for numbers

### Font sizes for web readability

| Element | OSRS Native | Web Recommended | CSS |
|---------|-------------|-----------------|-----|
| XP/stats numbers | 11px | 12-14px | `0.75rem` |
| Body text | 12px | 14-16px | `0.875rem–1rem` |
| Interface labels | 12px | 14-16px | `0.875rem` |
| h3 headings | — | 20-24px | `1.25rem–1.5rem` |
| h1 headings | — | 32-48px | `2rem–3rem` |

### CSS implementation for crisp pixel fonts

```css
@font-face {
  font-family: 'RuneScape Plain';
  src: url('/fonts/RuneScape-Plain-12.woff2') format('woff2'),
       url('/fonts/RuneScape-Plain-12.ttf') format('truetype');
  font-weight: 400;
  font-display: swap;
}

:root {
  --font-osrs: 'RuneScape Plain', 'Pixelify Sans', 'VT323', monospace;
  --leading-tight: 1.1;
  --leading-normal: 1.3;
}

.pixel-font {
  font-family: var(--font-osrs);
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: grayscale;
  font-smooth: never;
  text-rendering: optimizeSpeed;
}
```

Use `font-display: swap` with preloading for best performance. Fallback stack should progress from pixel fonts to monospace to prevent jarring FOUT.

---

## Level-up animation storyboard with precise timing

OSRS operates on a **600ms server tick** (30 client ticks at 20ms each). All animations snap to this timing, creating the distinctive "chunky" retro feel.

### Animation sequence breakdown

| Time | Event | Details |
|------|-------|---------|
| 0ms | Fireworks trigger | Multi-colored particles burst outward from center |
| 0ms | Sound #1 plays | Primary fanfare (Sound ID 2396) |
| 200ms | Text appears | "Congratulations" message in chatbox |
| 400ms | Icon displays | Skill icon with golden glow effect |
| 500ms | Sound #2 plays | Secondary flourish (Sound ID 2384) |
| 800ms | Level number | New level appears with scale animation |
| 2000ms | Particles fade | Particles begin opacity fade-out |
| 3000ms | Animation ends | Regular level-up complete |

**Level 99 variations**: Larger particle radius, more spectacular colors (red/gold), extended duration to ~3500ms, different secondary sound at 700ms.

### Particle characteristics

The fireworks use **radial burst patterns** with gravity-affected fall. Colors are predominantly **yellow, white, and orange**. Particles explode outward, then drift downward while fading. For web recreation, keep particle counts at **50-100 on mobile**, **150-200 on desktop** for performance.

### Easing recommendations

OSRS animations feel "snappy" rather than smooth—use **ease-out** for initial bursts, **linear** for particle fall, and consider CSS `steps()` for authentic frame-by-frame feel. Avoid bounce effects—OSRS keeps things immediate.

---

## UI component dimension guide

### Skill card specification

```
┌─────────────────────────────────┐
│  ┌──────┐                       │  Border: 2px solid #94866d
│  │ ICON │  Skill Name      99   │  Bevel: top/left #cfc08d, bottom/right #3c352a
│  │32x32 │  ████████░░░░  XP     │  Background: #d0bd97
│  └──────┘                       │  Padding: 8px
└─────────────────────────────────┘
  Width: 200-260px | Height: 60-80px
```

### XP progress bar

- **Height**: 12-16px
- **Border**: 2px solid `#3c352a`
- **Background**: `#18140c` (dark)
- **Fill**: `#00ff00` (green)
- **Text overlay**: Yellow (`#ffff00`) centered XP values
- **Corner radius**: 0px (squared)

### Modal/dialog specifications

- **Width**: 300-400px (fixed, don't scale with viewport)
- **Border**: 4px beveled effect
- **Background**: `#d0bd97` with subtle gradient
- **Close button**: 24x24px top-right
- **Padding**: 12-16px internal

### Tooltip styling

- **Background**: `#d0bd97` solid (or configurable transparency)
- **Border**: 1px `#18140c`
- **Text**: Yellow (`#ffff00`) for titles, white for content
- **Max-width**: 200px
- **Padding**: 4-8px

---

## Icon resources with direct links

### Free/CC0 pixel art icon libraries

| Resource | Icons | License | Best For |
|----------|-------|---------|----------|
| [Game-icons.net](https://game-icons.net/) | 4,170+ | CC BY 3.0 | Versatile RPG icons |
| [7Soul RPG Icons (OpenGameArt)](https://opengameart.org/content/496-pixel-art-icons-for-medievalfantasy-rpg) | 496 | CC0 | Medieval/fantasy, perfect for skills |
| [Kenney Pixel UI Pack](https://kenney.nl/assets/pixel-ui-pack) | 750 | CC0 | Interface elements |
| [Kenney Game Icons](https://kenney.nl/assets/game-icons) | 105+ | CC0 | General game UI |
| [itch.io CC0 Assets](https://itch.io/game-assets/assets-cc0) | 2,400+ packs | CC0 | Varied collections |

### Recommended icon sizes for web

- **16x16**: Inline text, small indicators
- **32x32**: Standard skill icons, inventory items (scale 2x to 64x64 for display)
- **48x48/64x64**: Featured skills, large displays

### Pixel art creation tools

- **[Piskel](https://www.piskelapp.com/)** (Free, browser)—quick prototypes
- **[Aseprite](https://www.aseprite.org/)** ($20)—professional standard, great for animations
- **[LibreSprite](https://libresprite.github.io/)** (Free)—Aseprite fork

**Fiverr commissions**: Simple 32x32 icons run $5-15 each; sets of 10-20 icons cost $30-100.

---

## Sound resources with direct links

### Jagex explicitly prohibits using OSRS sounds (Section 6.1.3 of Fan Content Policy). Here are legal alternatives:

| Resource | License | Description |
|----------|---------|-------------|
| [Kenney Audio](https://kenney.nl/assets) | CC0 | UI sounds, RPG effects—excellent quality |
| [OpenGameArt 512 8-bit SFX](https://opengameart.org/content/512-sound-effects-8-bit-style) | CC0 | Comprehensive retro pack |
| [Freesound.org](https://freesound.org/) | Various | Search "level up 8-bit", "achievement chime" |
| [Pixabay Sound Effects](https://pixabay.com/sound-effects/search/8%20bit%20video%20game/) | Royalty-free | 8-bit category |
| [JSFXR](https://sfxr.me/) | Generate your own | Browser-based 8-bit sound generator |

### AI sound generation (2026 options)

- **[ElevenLabs Sound Effects](https://elevenlabs.io/sound-effects)**—text-to-sound, prompt: "retro 8-bit level up fanfare chime"
- **[SFX Engine](https://sfxengine.com/)**—free AI sound generator
- **[Suno](https://suno.com/)**—full music/jingles from prompts

### What makes level-up sounds satisfying

Effective level-up audio uses **ascending arpeggios** (rising notes = success), **major key tonality** (universally positive), **clear resolution** on the final note, and **short duration** (2-4 seconds) for quick gratification without interrupting gameplay.

---

## Animation library recommendation: Framer Motion + tsParticles + CSS

After comparing Framer Motion, GSAP, Lottie, and CSS animations, the optimal stack for this project is:

| Use Case | Library | Reason |
|----------|---------|--------|
| UI transitions | Framer Motion (~32KB gzipped) | Declarative API, spring physics, AnimatePresence |
| Progress bars | Framer Motion | useSpring, color interpolation |
| Number counting | Framer Motion or react-countup | Built-in or lightweight dedicated lib |
| Particle fireworks | tsParticles (lazy-loaded) | Purpose-built presets, excellent performance |
| Sprite animations | CSS | Zero bundle impact, `steps()` timing |
| Pixel scaling | CSS | `image-rendering: pixelated` native support |

**Avoid Lottie**—its 60-80KB bundle plus JSON animation files (often 100KB-1.3MB each) is overkill for pixel-style animations.

### Framer Motion level-up animation skeleton

```tsx
import { motion, AnimatePresence } from "framer-motion";
import Particles from "react-particles";
import { loadFireworksPreset } from "tsparticles-preset-fireworks";

interface LevelUpProps {
  skill: string;
  newLevel: number;
  iconSrc: string;
  onComplete?: () => void;
}

export function LevelUpCelebration({ skill, newLevel, iconSrc, onComplete }: LevelUpProps) {
  const [isVisible, setIsVisible] = useState(true);

  const particlesInit = useCallback(async (engine) => {
    await loadFireworksPreset(engine);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      onComplete?.();
    }, 4000);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <AnimatePresence>
      {isVisible && (
        <>
          <Particles
            id="fireworks"
            init={particlesInit}
            options={{ preset: "fireworks" }}
            className="absolute inset-0 pointer-events-none"
          />
          
          <motion.div
            className="level-up-modal"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
          >
            <motion.img
              src={iconSrc}
              alt={skill}
              className="skill-icon pixel-art"
              initial={{ y: -50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
            />
            
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              Level Up!
            </motion.h1>
            
            <motion.p transition={{ delay: 0.6 }}>
              Your <strong>{skill}</strong> is now level{" "}
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: [0, 1.3, 1] }}
                transition={{ delay: 0.8, duration: 0.5 }}
              >
                {newLevel}
              </motion.span>
            </motion.p>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

---

## CSS pixel-perfect scaling techniques

```css
/* Universal pixel art rendering */
.pixel-art,
.pixel-art img {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  image-rendering: -moz-crisp-edges;
  -ms-interpolation-mode: nearest-neighbor;
}

/* Scalable pixel container */
.osrs-icon {
  --base-size: 32px;
  --scale-factor: 2;
  
  width: calc(var(--base-size) * var(--scale-factor));
  height: calc(var(--base-size) * var(--scale-factor));
  image-rendering: pixelated;
}

/* Responsive scaling */
@media (min-width: 768px) { .osrs-icon { --scale-factor: 3; } }
@media (min-width: 1024px) { .osrs-icon { --scale-factor: 4; } }

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

/* Beveled panel effect */
.osrs-panel {
  background: #d0bd97;
  border: 2px solid #94866d;
  border-top-color: #cfc08d;
  border-left-color: #cfc08d;
  border-bottom-color: #3c352a;
  border-right-color: #3c352a;
  border-radius: 0;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .level-up-animation { animation: simple-fade 0.3s ease-out; }
  .sprite-sheet { animation: none; }
}
```

---

## Responsive design for OSRS aesthetic

**Fixed pixel sizes are recommended** for authenticity—OSRS interfaces don't scale smoothly. Use CSS custom properties to step between discrete sizes rather than fluid scaling:

```css
:root {
  --pixel-unit: 1px;
}

@media (min-width: 768px) {
  :root { --pixel-unit: 1.5px; }
}

@media (min-width: 1024px) {
  :root { --pixel-unit: 2px; }
}
```

**Mobile considerations**: Touch targets need minimum 44x44px. Scale icons to **64x64** minimum on mobile while maintaining pixel-crisp rendering. Keep particle counts lower (50-100) for performance.

---

## Legal summary for commercial products

### Protected elements (DO NOT use)
- "RuneScape®", "OSRS®", "Jagex®" trademarks
- Any actual game assets, sounds, music, UI screenshots
- Specific character names, locations, lore

### Unprotected elements (SAFE to use)
- **Game mechanics**: XP systems, levels 1-99, skill progression (confirmed by U.S. Copyright Office—rules aren't copyrightable)
- **Color palettes**: Cannot be copyrighted
- **General aesthetics**: Medieval fantasy, pixel art, retro RPG themes
- **Generic skill names**: "Woodcutting", "Mining", "Fishing" are common words

### Safe marketing language
✅ "Inspired by classic 2000s MMORPGs"
✅ "Nostalgic RPG skill training"
✅ "Old-school fantasy progression"
❌ "OSRS-inspired" (mentions trademark)
❌ "RuneScape-style" (mentions trademark)

### Required disclaimer
> "This application is an independent project and is not affiliated with, endorsed by, or connected to Jagex Limited or any of its games."

**Precedent**: Melvor Idle successfully operated for years describing itself as "inspired by RuneScape" using **entirely original assets**. Jagex later approached them to publish the game—proving the model works when you create original art and avoid trademark use.

---

## Conclusion

Building an OSRS-inspired fitness gamification app is legally viable and technically straightforward with the right approach. The key principles: use **squared corners and beveled borders** for authentic panel styling, implement **RuneStar fonts or Pixelify Sans** for typography, keep animations **snappy with ease-out curves** rather than bouncy, and source all assets from **CC0 libraries like Kenney.nl and OpenGameArt**. The Framer Motion + tsParticles + CSS stack provides the best balance of developer experience, performance, and visual fidelity for level-up celebrations. Most importantly, create entirely original assets while freely using the unprotectable game mechanics—this is exactly how Melvor Idle built a successful business that eventually attracted Jagex's partnership rather than their lawyers.