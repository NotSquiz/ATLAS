# ATLAS Gamification System Design

**Date:** January 22, 2026
**Status:** MVP Backend Implemented - UI/UX Design Needed
**Plan Source:** User-provided plan in conversation

---

## Current Implementation Status

### Completed (MVP Backend)
- [x] OSRS level calculator (`atlas/gamification/level_calculator.py`)
- [x] XP service with async/fail-safe pattern (`atlas/gamification/xp_service.py`)
- [x] Database schema (`atlas/memory/schema_gamification.sql`)
- [x] XP hooks in 6 health services (non-blocking)
- [x] Voice intent: "what's my XP" / "skill status"
- [x] 57 unit tests passing

### Needs Design Work
- [ ] XP economy balancing (values are placeholder)
- [ ] UI/UX for Command Centre integration
- [ ] Level-up announcement strategy
- [ ] Achievement system design
- [ ] Streak mechanics refinement
- [ ] OSRS visual theme (fonts, colors, icons)

---

## Verification Feedback Summary

Three Opus sub-agents reviewed the original plan and identified critical issues:

### Critical Issues Addressed
1. **Latency risk** → Used `award_xp_safe_async()` (non-blocking)
2. **Transaction safety** → Added `BEGIN IMMEDIATE` / `COMMIT` / `ROLLBACK`
3. **Import failures** → XP failures never break health tracking
4. **Cold start** → Skills seeded on table creation
5. **Announcement fatigue** → Only announce via explicit "skill status" query

### Design Issues Still Open

#### 1. XP Economy Not Balanced
Current values are placeholders:
```python
XP_TABLE = {
    "workout_strength": 150,    # How does this compare to OSRS rates?
    "morning_routine": 75,      # Too high? Too low?
    "meal_log": 40,             # 3 meals = 120 XP/day from food alone
}
```

**Questions to answer:**
- Target time to Level 50? (Current estimate: 8-12 months)
- Should recovery activities (sleep, rest) give as much XP as active work?
- Is 200-400 XP/day typical the right target?

#### 2. OSRS Curve May Not Fit Health
- OSRS: 71 years to max at current XP rates
- Health activities are time-bounded (1 workout/day max)
- Need to decide: authentic OSRS curve OR health-appropriate curve?

**Options:**
A. Keep OSRS curve, inflate XP values (current approach)
B. Custom curve optimized for health (faster early levels)
C. Hybrid: OSRS formula but with "virtual levels" past 99

#### 3. Level-Up Announcements
Currently: No automatic announcements (only "skill status" query)

**Options:**
A. Announce at end of response that triggered level-up
B. Queue level-ups, announce as daily summary
C. Never announce (user discovers via query)
D. Only announce milestone levels (10, 25, 50, 75, 99)

#### 4. Streak Mechanics
Current: Simple consecutive day counter, caps at 14 days (+70 XP max)

**Issues:**
- No forgiveness for missed days (1 miss = reset 100-day streak)
- No timezone handling
- No "streak freeze" feature

**Questions:**
- Allow 1 "grace day" per week?
- Store longest_streak separately from current_streak?
- Timezone: user local or UTC?

#### 5. Missing XP Sources
Not currently awarding XP for:
- Sleep quality (only sleep_score >= 80)
- Pain logging (should low pain = XP?)
- Assessment completion (only GATE milestones)
- Exercise form queries (engagement reward?)

#### 6. Gaming Prevention
No safeguards against:
- Logging fake supplements ("took my morning supps" x10)
- Multiple meal logs for same meal
- Inflating workout counts

---

## 7 Skills (Implemented)

| Skill | XP Sources | Current Rate |
|-------|-----------|--------------|
| **Strength** | Strength A/B/C workouts | 150 XP/workout |
| **Endurance** | Zone 2 cardio, activities | 120 XP/workout |
| **Mobility** | Morning routine | 75 XP/routine |
| **Nutrition** | Meals (40), supplements (25) | ~150 XP/day |
| **Recovery** | Sleep >= 80 (60), body battery >= 50 (30) | 0-90 XP/day |
| **Consistency** | Daily activity + streak bonus | 30 + (5 × streak days) |
| **Work** | Baby Brains captures | 30 XP/capture |

---

## UI/UX Design Needed

### Command Centre Integration
Current UI (`scripts/atlas_launcher.py`) has no XP display.

**Questions:**
- Where does XP card fit? (Before timer? After transcript?)
- What to show? (Total level? Top 3 skills? Progress bars?)
- Full OSRS theme or minimal gold accent?

### OSRS Visual Theme (Future)
From original plan:
```python
OSRS_COLORS = {
    "bg_dark": "#1a1a1a",
    "bg_card": "#2d2d2d",
    "gold": "#FFD700",
    "gold_dark": "#B8860B",
    "text_primary": "#FFFFFF",
    "green": "#00FF00",
    "yellow": "#FFFF00",
    "red": "#FF0000",
}
```

Fonts (need to download):
- **Press Start 2P** - headers
- **VT323** - body text

---

## Database Schema (Implemented)

```sql
-- Player skills (seeded with 7 skills at Level 1)
CREATE TABLE player_skills (
    skill_name TEXT PRIMARY KEY,
    current_xp INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    updated_at TIMESTAMP
);

-- XP events (audit trail)
CREATE TABLE xp_events (
    id INTEGER PRIMARY KEY,
    skill_name TEXT,
    xp_gained INTEGER,
    source_type TEXT,
    streak_bonus INTEGER,
    created_at TIMESTAMP
);

-- Streaks
CREATE TABLE activity_streaks (
    date DATE PRIMARY KEY,
    streak_day INTEGER,
    activities_logged INTEGER
);

-- Achievements (schema exists, not implemented)
CREATE TABLE achievements (...);
CREATE TABLE player_achievements (...);
```

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `atlas/gamification/__init__.py` | 63 | Module init, lazy loading |
| `atlas/gamification/level_calculator.py` | 120 | OSRS XP formula |
| `atlas/gamification/xp_service.py` | 430 | XP award/query service |
| `atlas/memory/schema_gamification.sql` | 100 | Database schema |
| `tests/gamification/test_level_calculator.py` | 150 | 25 level calc tests |
| `tests/gamification/test_xp_service.py` | 280 | 32 XP service tests |

---

## Files Modified (XP Hooks)

| File | Method | XP Award |
|------|--------|----------|
| `atlas/health/scheduler.py` | `log_workout()` | Strength/Endurance |
| `atlas/health/routine_runner.py` | `run()` | Mobility |
| `atlas/health/supplement.py` | `mark_all_taken()` | Nutrition |
| `atlas/nutrition/service.py` | `_store_meal()` | Nutrition |
| `atlas/health/morning_sync.py` | `save_morning_status()` | Recovery |
| `atlas/orchestrator/classifier.py` | `classify_and_store()` | Work |
| `atlas/voice/bridge_file_server.py` | (new methods) | Skill status intent |
| `atlas/voice/intent_dispatcher.py` | `_try_query_handlers()` | Skill status handler |

---

## Next Steps (Recommended Priority)

1. **Balance XP economy** - Define target progression curve
2. **Design UI mockup** - Where XP fits in Command Centre
3. **Decide announcement strategy** - When/how to notify level-ups
4. **Implement streak forgiveness** - Grace days, timezone handling
5. **Add gaming prevention** - Rate limits, anomaly detection
6. **Full OSRS theme** - Fonts, colors, sidebar navigation

---

## How to Test

```bash
# Run unit tests
pytest tests/gamification/ -v

# Test XP service CLI
python -m atlas.gamification.xp_service --status
python -m atlas.gamification.xp_service --test
python -m atlas.gamification.xp_service --award strength 100 manual_test
python -m atlas.gamification.xp_service --reconcile

# Voice test (when bridge running)
"what's my XP"
"skill status"
"check my levels"
```

---

## Original Plan Location

The full original plan was provided in conversation. Key points preserved above.
Verification feedback from 3 Opus sub-agents also in conversation history.
