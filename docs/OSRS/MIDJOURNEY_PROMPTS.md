# OSRS-Style Custom Sprite Reference

**Last Updated:** January 26, 2026

Reference for custom sprites created for the ATLAS virtue system.

## Tab Icons (DOWNLOADED - January 24, 2026)

Downloaded from OSRS Wiki - no custom sprites needed:
| Tab | File | Size | Source |
|-----|------|------|--------|
| Inventory | combat_icon.png | 19x19 | OSRS Wiki |
| Stats | stats_icon.png | 25x23 | OSRS Wiki |
| Quests | quest_point_icon.png | 21x21 | OSRS Wiki |
| Settings | wrench.png | 27x27 | OSRS Wiki |

---

## Final Virtue Sprite Mappings (January 26, 2026)

### BODY Domain (OSRS Icons)
| Virtue | Sprite | Rationale |
|--------|--------|-----------|
| Strength | strength.png | OSRS fist = raw power |
| Endurance | defence.png | Shield = resilience, staying power |
| Mobility | agility.png | Running figure = movement |
| Nutrition | hitpoints.png | Heart = life force, sustenance |

### MIND Domain (Custom Icons)
| Virtue | Sprite | Concept | Personal Meaning |
|--------|--------|---------|------------------|
| Focus | focus_skill.png | Eye in diamond, concentrated gaze | Locked-in attention |
| Learning | learn_skill.png | Open book with golden glow | Knowledge acquisition |
| Reflection | reflect_skill.png | Saiyan meditation with blue aura | DBZ nostalgia + zen practice |
| Creation | create_skill.png | Workbench with laptop + tools | Hybrid digital/physical making |

### SOUL Domain (Custom Icons)
| Virtue | Sprite | Concept | Personal Meaning |
|--------|--------|---------|------------------|
| Presence | presence_skill.png | Enso circle with lotus flower | Zen mindfulness, being here now |
| Service | service_skill.png | Creation of Adam hands touching | Divine connection, reaching out to help |
| Courage | courage_skill.png | Noble lion head | Son is Leo, lions = bravery |
| Consistency | consistency_skill.png | Sisyphus pushing boulder at sunset | "One must imagine Sisyphus happy" - Camus |

---

## Successful Prompt Patterns

### Key Learnings for Midjourney Pixel Art

**Essential modifiers:**
- `no anti-aliasing` - prevents soft edges
- `hard pixel edges` - enforces stepped pixels
- `no gradients` - keeps colors flat
- `--style raw` - reduces Midjourney's "beautification"
- `transparent background` - for skill icons
- `limited color palette` - OSRS-authentic

**Base template (transparent skill icon):**
```
32x32 pixel art icon, [subject],
transparent background, OSRS aesthetic,
hard pixel edges, no anti-aliasing, no gradients,
limited color palette, --ar 1:1 --v 6 --style raw
```

**Base template (framed mode button):**
```
32x32 pixel art icon, [subject],
dark stone background, golden border highlight,
OSRS aesthetic, hard pixel edges, no anti-aliasing,
--ar 1:1 --v 6 --style raw
```

---

## Prompts That Worked

### Focus (Eye in Diamond)
```
32x32 pixel art icon, focused eye inside diamond shape,
concentrated gaze, target pupil, transparent background,
OSRS aesthetic, hard pixel edges, no anti-aliasing,
--ar 1:1 --v 6 --style raw
```

### Learning (Open Book)
```
32x32 pixel art icon, open ancient book with golden glow,
knowledge light emanating from pages, transparent background,
OSRS aesthetic, hard pixel edges, no anti-aliasing,
--ar 1:1 --v 6 --style raw
```

### Reflection (Saiyan Meditation)
```
32x32 pixel art icon, super saiyan meditation pose,
calm blue energy aura, serene warrior, transparent background,
pixel art, hard edges, no anti-aliasing,
--ar 1:1 --v 6 --style raw
```

### Creation (Workbench)
```
32x32 pixel art icon, wooden craftsman workbench,
laptop and tools, carpenter workspace, transparent background,
OSRS aesthetic, hard pixel edges, no anti-aliasing,
--ar 1:1 --v 6 --style raw
```

### Presence (Enso + Lotus)
```
32x32 pixel art icon, zen enso brush circle containing lotus flower,
golden enso ring, white lotus with golden center, green lily pad,
mindfulness symbol, transparent background,
OSRS aesthetic, hard pixel edges, no anti-aliasing,
--ar 1:1 --v 6 --style raw
```

### Service (Creation of Adam Hands)
```
32x32 pixel art, Sistine Chapel Creation of Adam hands,
two hands reaching toward each other, golden divine spark between fingertips,
transparent background, pixel art, hard edges, no anti-aliasing,
--ar 1:1 --v 6 --style raw
```

### Courage (Lion)
```
32x32 pixel art icon, noble lion head facing forward,
golden mane, fierce determined eyes, courage symbol,
transparent background, OSRS aesthetic, hard pixel edges,
no anti-aliasing, --ar 1:1 --v 6 --style raw
```

### Consistency (Sisyphus)
```
32x32 pixel art icon, Sisyphus pushing boulder up hill,
sunset behind, man rolling stone up slope, eternal struggle,
beautiful sky, circular frame, transparent background,
pixel art, hard edges, --ar 1:1 --v 6 --style raw
```

---

## Inventory Item Sprites

### Meals
| Meal | Sprite | Status |
|------|--------|--------|
| Breakfast | brekky Inventory.png | Ready - eggs, bacon, coffee |
| Lunch | Lunch Inventory.png | Ready - sandwich |
| Dinner | shark.png | OSRS default |
| Snack | banana.png | OSRS default |

---

## Sprite Specifications

| Property | Value |
|----------|-------|
| Size | 32x32 pixels (source), scales to 24-48px in UI |
| Format | PNG with transparency |
| Background | Transparent for skill icons |
| Style | Hard pixel edges, no anti-aliasing |
| Palette | Limited colors, OSRS-authentic |

---

## Files Location

- Custom sprites: `assets/sprites/*_skill.png`
- Source files: `docs/OSRS/sprites/*.png`
- OSRS downloads: `assets/sprites/*.png`
