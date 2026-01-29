# OSRS Interface Redesign - Complete Plan

**Date:** January 23, 2026
**Status:** Research Complete, Ready to Implement

## Reference Image
`/home/squiz/ATLAS/docs/OSRS/OSRS dash.png`

---

## Layout Overview

```
┌─────────────────────────────────────┬──────────────────┐
│                                     │   MINIMAP/HUD    │
│     MAIN ACTIVITY WINDOW            │   + Body Battery │
│     (Timer, Exercise, Status)       │   + Stat Orbs    │
│     ~65% width                      │   + Quick Nav    │
│                                     ├──────────────────┤
├─────────────────────────────────────┤   INVENTORY      │
│     CHAT/INFO BOX                   │   (4×7 = 28)     │
│     Tabs: Transcript|Quests|Status  │                  │
│                                     │   [Tab Buttons]  │
└─────────────────────────────────────┴──────────────────┘
```

---

## Zone Mappings

### Zone 1: Main Window (Top Left) - Activity Display
- **Idle:** Status dashboard (Traffic Light, Body Battery, today's schedule)
- **Workout Active:** Exercise name, set/rep, weight, form cue, timer
- **Routine Active:** Exercise name, timer, section progress
- **Assessment:** Test name, instructions, input prompts

### Zone 2: Chat Box (Below Main) - Information Panel
| Tab | Content |
|-----|---------|
| Transcript | Voice exchange history |
| Quests | Daily/Weekly quests with XP rewards |
| Status | System messages, recent actions |
| Notes | Captured thoughts |

### Zone 3: Minimap/HUD (Top Right) - Player Status
- **Main Circle:** Body Battery (0-100) with Traffic Light ring
- **HP Orb:** Sleep Score
- **Prayer Orb:** HRV Status
- **Run Orb:** Streak Days
- **Quick Nav Buttons:** Baby Brains, Tactical, Reflections, Settings, Health

### Zone 4: Inventory (Right Side) - 28 Action Slots

| Row | Slot 1 | Slot 2 | Slot 3 | Slot 4 |
|-----|--------|--------|--------|--------|
| **1 Workouts** | Strength A | Strength B | Strength C | Zone 2 |
| **2 Supps** | Morning | Breakfast | Bedtime | Ice Bath |
| **3 Nutrition** | Healthy Meal | Protein | Quick Meal | Snack |
| **4 Mind** | Deep Work | Learning | Journal | Focus Timer |
| **5 Routines** | Morning | Assessment | Sauna | Weight Log |
| **6 Soul** | Dad Time | Conversation | Service | Courage |
| **7 Meta** | Rest Day | Achievements | Stats | Streak Freeze |

### Zone 5: Bottom Tabs - Panel Switcher
- Inventory (actions) | Equipment (active states) | Skills (12 grid) | Quests | Settings

---

## Color Palette

```python
OSRS_COLORS = {
    # Backgrounds
    "panel_bg": "#3c3024",
    "skill_bg": "#252015",
    "slot_bg": "#4a5a39",
    "chat_bg": "#3a3a2a",

    # Borders
    "border_dark": "#1a1510",
    "border_light": "#c8c8b8",

    # Text
    "gold_xp": "#ffff00",
    "gold_dark": "#c8a000",
    "text_light": "#e8e0c8",
    "text_muted": "#a89878",

    # Orbs
    "hp_red": "#cc0000",
    "prayer_blue": "#0066cc",
    "run_green": "#00cc00",
    "special_gold": "#ffcc00",
}
```

---

## Asset Sources (For Private Use)

1. **Sprites:** OSRS Wiki, Spriters Resource, RuneLite cache
2. **Fonts:** RuneStar GitHub (runescape_uf.ttf)
3. **Legal:** Jagex Fan Content Policy permits personal use

---

## Implementation Phases

### Phase A: Layout Restructure
- [ ] Rewrite `_build_ui()` with OSRS zone layout
- [ ] Main window area (top left)
- [ ] Chat box area (bottom left)
- [ ] Minimap/HUD area (top right)
- [ ] Inventory area (right side)

### Phase B: HUD Components
- [ ] Body Battery orb (circular canvas)
- [ ] Stat orbs (HP/Prayer/Run style)
- [ ] Quick nav buttons (around orb)
- [ ] XP counter display

### Phase C: Inventory System
- [ ] 28-slot grid (4×7)
- [ ] Load item sprites
- [ ] Click actions → voice commands
- [ ] Hover tooltips
- [ ] State tracking (done/available)

### Phase D: Tab System
- [ ] Chat box tabs (Transcript/Quests/Status/Notes)
- [ ] Right panel tabs (Inventory/Equipment/Skills/Quests)
- [ ] Quest display with progress

### Phase E: Integration
- [ ] Wire to existing voice bridge
- [ ] XP animations on award
- [ ] Level-up celebrations
- [ ] Live data from gamification service
