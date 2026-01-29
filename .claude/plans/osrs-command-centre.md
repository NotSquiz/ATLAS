# OSRS Command Centre - Implementation Plan

**Status:** Phase 2+ Complete - Protocol System Added
**Date:** January 24, 2026
**Last Updated:** January 24, 2026

---

## Executive Summary

Transform ATLAS Command Centre into an OSRS-style gamification dashboard with:
- 12-skill panel (4x3 grid) with tooltips
- HP orb showing Body Battery/Total Level
- 28-slot inventory for life activities (TRUE SQUARE slots)
- Protocol launchers for interactive sessions (workout, routine, etc.)
- Settings panel with toggles
- Tab bar with real OSRS icons

---

## Implementation Progress

### Phase 1: Core Layout Shell - COMPLETE
- [x] Two-panel layout (left game area, right OSRS panel)
- [x] HUD with orbs (Sleep, HRV, Battery, Streak, XP)
- [x] 12 skill cards in 4x3 grid with domain headers
- [x] 28-slot inventory grid
- [x] Tab bar for switching panels

### Phase 2: UI Polish - COMPLETE (January 24, 2026)
- [x] Fixed square inventory slots (dynamic resize)
- [x] Real OSRS tab icons (combat, stats, quest_point, wrench)
- [x] Red border highlight on active tab
- [x] Skill hover tooltips with XP display
- [x] Domain color coding (BODY=red, MIND=blue, SOUL=gold)
- [x] Sprite swaps per user feedback (weapons, potions)

### Phase 2+: Architecture Update - COMPLETE (January 24, 2026)
- [x] HUD expansion (fills space when inventory capped)
- [x] Inventory fixed max height (7 rows × 74px)
- [x] Tab bar evenly spaced (grid layout)
- [x] Total Level display in HUD
- [x] Bigger orbs (44px mini, 70px central)
- [x] Protocol tab (replaces Quests) with 6 launchers
- [x] Settings tab with toggle switches

### Phase 3: Protocol System - IN PROGRESS
- [x] Protocol launcher UI (6 buttons)
- [x] Protocol commands sent to bridge
- [ ] Main window transformation when protocol active
- [ ] Timer display in main window
- [ ] Form cues and progress display
- [ ] Quest capture via voice

### Phase 4: HUD Data - TODO
- [x] Total Level display (UI ready)
- [ ] Connect to real Garmin data
- [ ] Real XP values from database
- [ ] Streak from database

### Phase 5: Integration - TODO
- [ ] Connect XP awards to gamification service
- [ ] Real skill levels from database
- [ ] Voice commands for all actions
- [ ] Settings toggle persistence

---

## Design Decisions (From Research)

### Hybrid Metaphor System
| Life Activity | RS Metaphor | Why |
|--------------|-------------|-----|
| Supplements, Meals | Inventory items | Consumable, one-time use |
| Current workout, Project | Equipment slots | Active, ongoing state |
| Deep work, Device-free | Prayers/Toggles | Mode switches |
| Daily goals, BB work | Quest log | Multi-step, progress tracking |

### Key Specifications
- **Inventory**: 28 slots (4x7), TRUE SQUARE with dynamic resize
- **Skills**: 4x3 grid (BODY row, MIND row, SOUL row)
- **HP Orb**: Body Battery (0-100) displayed as fill level
- **Quest Log**: Color-coded by domain (body/mind/soul)
- **Tabs**: Real OSRS icons with red border on active

### What NOT to Do
- Don't gamify relationships (family time is Achievement Diary, not item)
- Don't punish missed days (no "death" mechanics)
- Don't force XP grinding (batch XP for sessions)
- Don't copy OSRS pixel-for-pixel (capture the *feeling*)

---

## Current Sprite Mappings

### Tab Icons (Downloaded from OSRS Wiki)
| Tab | Sprite | Purpose |
|-----|--------|---------|
| Inventory | combat_icon.png | 28 quick-action slots |
| Skills | stats_icon.png | 12 virtues (BODY/MIND/SOUL) |
| Protocols | quest_point_icon.png | Launch interactive sessions |
| Settings | wrench.png | Preferences & integrations |

### Protocol Tab Launchers
| Protocol | Icon | Command | Description |
|----------|------|---------|-------------|
| Start Workout | ⚔ | start workout | Strength A/B/C or Zone 2 |
| Morning Routine | sunrise | start routine | 18-min ATLAS Protocol |
| Seneca Reflection | book | start reflection | Stoic evening review |
| Baseline Test | flask | start baseline | Assessment protocol |
| Deep Focus | target | start focus | Pomodoro + device-free |
| Daily Quests | scroll | show quests | View today's tasks |

### Settings Tab Sections
| Section | Settings |
|---------|----------|
| Integrations | Garmin Sync, Voice Enabled |
| Notifications | Workout Reminders, Supplement Alerts |
| Display | Dark Mode, XP Popups |

### Workout Weapons (User Requested)
| Slot | Sprite | Rationale |
|------|--------|-----------|
| Str A | abyssal_whip.png | Upper body |
| Str B | dragon_scimitar.png | Chest/arms |
| Str C | dharoks_greataxe.png | Full body compound |
| Zone2 | boots_of_lightness.png | Cardio/running |

### Supplements (Color = Timing)
| Slot | Sprite | Meaning |
|------|--------|---------|
| AM | strength_potion.png | Red = pre-workout |
| Bfast | saradomin_brew.png | Restore = post-workout |
| Bed | prayer_potion.png | Blue = sleep |
| Ice | icefiend.png | Cold = ice bath |

### 12 Virtues (Skills Panel)
| Domain | Virtue | Sprite | Notes |
|--------|--------|--------|-------|
| BODY | Strength | strength.png | OSRS icon |
| BODY | Endurance | defence.png | OSRS icon - shield = resilience |
| BODY | Mobility | agility.png | OSRS icon |
| BODY | Nutrition | hitpoints.png | OSRS icon - heart = life force |
| MIND | Focus | focus_skill.png | Custom - eye in diamond |
| MIND | Learning | learn_skill.png | Custom - open book with glow |
| MIND | Reflection | reflect_skill.png | Custom - Saiyan meditation, blue aura |
| MIND | Creation | create_skill.png | Custom - workbench with laptop + tools |
| SOUL | Presence | presence_skill.png | Custom - enso circle with lotus |
| SOUL | Service | service_skill.png | Custom - Creation of Adam hands |
| SOUL | Courage | courage_skill.png | Custom - lion head (Leo connection) |
| SOUL | Consistency | consistency_skill.png | Custom - Sisyphus sunset scene |

---

## Technical Implementation

### Dynamic Square Slots
```python
# Key mechanism: bind to <Configure> event
self.inv_frame.bind("<Configure>", self._resize_inventory)

def _resize_inventory(self, event=None):
    # Calculate slot size from available width/height
    slot_from_width = available_width // 4
    slot_from_height = available_height // 7
    slot_size = min(slot_from_width, slot_from_height, 70)
    # Rebuild grid at new size
    self._build_inventory_slots(slot_size)
```

### OSRS Tab Styling
```python
# Active tab: red border like OSRS
btn.configure(
    fg_color=OSRS["slot_bg"],
    border_color=OSRS["orb_red"]  # Red highlight
)
```

### Skill Tooltips
- Recursive binding to entire card and children
- OSRS XP formula for level calculations
- Shows: Name, Level, XP, Next Level, Remaining

---

## Files Modified (Phase 2)

| File | Changes |
|------|---------|
| `scripts/atlas_launcher.py` | Dynamic squares, OSRS tabs, tooltips, quests |
| `assets/sprites/*.png` | Added combat_icon, stats_icon, quest_point_icon, wrench |
| `docs/OSRS/MIDJOURNEY_PROMPTS.md` | Custom sprite prompts |
| `.claude/research-prompts/quest-system-design.md` | Quest system research prompt |

---

## Next Steps

1. **Quest System Deep Design**
   - Run Opus research agent on `.claude/research-prompts/quest-system-design.md`
   - Design XP calculation algorithm
   - Design voice capture flow

2. **HUD Visual Polish**
   - Download/create orb textures
   - Add Total Level display
   - Connect to real Garmin data

3. **Integration**
   - Connect UI to gamification service
   - Real skill levels from database
   - Voice command integration

---

## Verification Commands

```powershell
# Test launcher
python \\wsl$\Ubuntu\home\squiz\ATLAS\scripts\atlas_launcher.py
```

**Expected:**
- Square inventory slots that resize with window
- OSRS tab icons with red border on active
- Skill tooltips on hover
- Quests tab with clickable todos
