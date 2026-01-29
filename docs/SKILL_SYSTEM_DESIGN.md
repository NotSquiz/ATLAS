# ATLAS Command Centre - Skill System Design

**Version:** 1.0
**Date:** January 2026
**Status:** Design Discussion - Requires User Input

---

## Design Philosophy

The skill system is the **core loop** of ATLAS gamification. It should:

1. **Reflect real value** - XP comes from activities that genuinely improve life
2. **Be personally meaningful** - Skills map to what YOU care about
3. **Create positive pressure** - The "underleveled skill" feeling drives behavior
4. **Reward consistency** - Daily small actions compound into big progress
5. **Feel achievable** - Level 99 should be aspirational but reachable in a lifetime

---

## Current Implementation (7 Skills)

The MVP backend already implements these 7 skills:

| Skill | Description | Primary XP Sources |
|-------|-------------|-------------------|
| **Strength** | Physical power, resistance training | Strength A/B/C workouts |
| **Endurance** | Cardiovascular fitness, stamina | Zone 2 cardio, rucks, activities |
| **Mobility** | Flexibility, joint health, movement | Morning routine, mobility work |
| **Nutrition** | Diet quality, macro adherence | Meal logs, supplements |
| **Recovery** | Sleep, rest, regeneration | Garmin sleep score, body battery, rest days |
| **Consistency** | Daily discipline, streak building | Any daily activity, streak bonus |
| **Work** | Professional output, projects | Baby Brains captures, focus sessions |

### Current XP Values

```python
XP_TABLE = {
    # Strength
    "workout_strength": 150,
    # Endurance
    "workout_cardio": 120,
    # Mobility
    "morning_routine": 75,
    # Nutrition
    "supplement_batch": 25,
    "meal_log": 40,
    # Recovery
    "sleep_good": 60,        # Garmin sleep score >= 80
    "body_battery_good": 30, # Body battery >= 50
    "rest_day": 50,
    # Consistency
    "daily_checkin": 30,
    "streak_bonus": 5,       # Per streak day (capped at 14)
    # Work
    "work_session": 100,
    "work_capture": 30,
    # Bonus
    "assessment_complete": 250,
    "weight_log": 20,
}
```

---

## The Question: 7 vs 9 vs 12 Skills

### Option A: Keep 7 Skills (Current)
**Pros:** Simpler, already implemented, focused
**Cons:** Missing important life domains (Family, Mind)

### Option B: Expand to 9 Skills
Add **Focus** and **Presence** to cover mental and relational domains.

| New Skill | Description | XP Sources |
|-----------|-------------|------------|
| **Focus** | Deep work, learning, mental clarity | Focus sessions, learning streaks, no-distraction blocks |
| **Presence** | Quality time with loved ones | Dad time logged, date nights, family activities |

### Option C: Expand to 12 Skills (Full Life System)
Complete coverage of all life optimization domains.

| Domain | Skills |
|--------|--------|
| **Body** | Strength, Endurance, Mobility, Nutrition, Recovery |
| **Mind** | Focus, Learning |
| **People** | Presence, Social |
| **Work** | Creation, Wealth |
| **Meta** | Consistency |

---

## Proposed: 9-Skill System

After analysis, **9 skills** strikes the right balance:
- Covers essential life domains
- Not overwhelming to display
- Each skill has clear, distinct XP sources
- Room to expand later if needed

### The 9 Skills

```
┌─────────────────────────────────────────────────────────────────┐
│                        BODY (5 skills)                          │
├─────────────┬─────────────┬─────────────┬──────────┬───────────┤
│  Strength   │  Endurance  │  Mobility   │ Nutrition│  Recovery │
│     ⚔️      │     🏃      │     🧘      │    🍎    │     🌙    │
└─────────────┴─────────────┴─────────────┴──────────┴───────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  MIND (1 skill)     │     PEOPLE (1 skill)      │
├─────────────────────────────────────┼───────────────────────────┤
│            Focus                    │        Presence           │
│              🎯                     │           👨‍👧             │
└─────────────────────────────────────┴───────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│        WORK (1 skill)               │      META (1 skill)       │
├─────────────────────────────────────┼───────────────────────────┤
│           Creation                  │       Consistency         │
│              💼                     │           🔥              │
└─────────────────────────────────────┴───────────────────────────┘
```

---

## Detailed Skill Definitions

### BODY DOMAIN

#### 1. Strength ⚔️
**What it represents:** Physical power, muscle mass, resistance training capability

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Strength A workout | 150 | Full session |
| Strength B workout | 150 | Full session |
| Strength C workout | 150 | Full session |
| PR (personal record) | 500 | Major milestone |

**Why it matters:** Foundation of physical capability. Prevents injury, builds functional strength.

---

#### 2. Endurance 🏃
**What it represents:** Cardiovascular fitness, stamina, aerobic capacity

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Zone 2 cardio (30+ min) | 120 | Ruck, walk, bike |
| Zone 2 extended (60+ min) | 200 | Saturday ruck |
| Garmin cardio activity | 80-150 | Based on duration/intensity |
| 10k+ steps day | 50 | Passive activity |

**Why it matters:** Heart health, energy levels, longevity marker.

---

#### 3. Mobility 🧘
**What it represents:** Flexibility, joint health, movement quality, injury prevention

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Morning routine (18 min) | 75 | Full protocol |
| Mobility assessment | 50 | Testing range of motion |
| Stretch session (15+ min) | 40 | Dedicated stretching |
| Doorframe ER holds | 20 | Rehab specific |

**Why it matters:** Enables other training, prevents injury, quality of movement.

---

#### 4. Nutrition 🍎
**What it represents:** Diet quality, macro adherence, fueling performance

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Meal logged | 40 | Per meal with macros |
| Supplement batch (morning) | 25 | Preworkout + breakfast |
| Supplement batch (evening) | 25 | Bedtime |
| Protein target hit (140g+) | 100 | Daily bonus |
| Breakfast eaten (before 9am) | 50 | High value - breaks bad habit |
| Clean eating day | 75 | No junk food |

**Why it matters:** Fuels everything. Nutrition is the multiplier for all other efforts.

**Personal Note:** "Breakfast eaten" is high XP because you tend to skip it. This is personalized difficulty weighting.

---

#### 5. Recovery 🌙
**What it represents:** Sleep quality, rest, regeneration, stress management

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Sleep score 80+ | 60 | Garmin metric |
| Sleep score 90+ | 100 | Excellent night |
| Body battery 50+ (morning) | 30 | Garmin metric |
| Rest day taken | 50 | Scheduled recovery |
| Sauna session | 40 | Heat exposure |
| Ice bath | 40 | Cold exposure |
| No caffeine after 2pm | 30 | Sleep hygiene |

**Why it matters:** Recovery is where adaptation happens. Training without recovery = injury.

---

### MIND DOMAIN

#### 6. Focus 🎯
**What it represents:** Deep work capability, attention span, mental clarity

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Deep focus block (2+ hours) | 100 | No interruptions |
| Focus session (1 hour) | 50 | Dedicated work |
| Learning session | 60 | Reading, courses, skills |
| No social media day | 75 | Digital discipline |
| Morning routine completed before phone | 40 | Win the morning |

**Why it matters:** Attention is the currency of the knowledge worker. Protect it.

---

### PEOPLE DOMAIN

#### 7. Presence 👨‍👧
**What it represents:** Quality time with loved ones, relational investment

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Dad time (1+ hour, no screens) | 100 | Quality time with child |
| Family activity | 75 | Outings, games, etc. |
| Date night | 100 | Partner time |
| Phone call with family | 30 | Staying connected |
| Present at dinner (no devices) | 40 | Daily ritual |

**Why it matters:** Relationships are life's true wealth. Easy to neglect when optimizing elsewhere.

**Personal Note:** This is YOUR highest-value skill. The "Dad of the Week" quest exists for a reason.

---

### WORK DOMAIN

#### 8. Creation 💼
**What it represents:** Professional output, project progress, building things

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Work session logged | 100 | Deep work on projects |
| Thought capture (Baby Brains) | 30 | Ideas captured |
| Task completed | 40 | Meaningful progress |
| Weekly review | 75 | Reflection + planning |
| Ship something | 200 | Release, publish, deploy |

**Why it matters:** Create more than you consume. Output compounds.

---

### META DOMAIN

#### 9. Consistency 🔥
**What it represents:** Daily discipline, habit maintenance, showing up

**XP Sources:**
| Activity | XP | Notes |
|----------|-----|-------|
| Any activity logged | 30 | First activity of day |
| Streak day | 5× streak_days | Capped at 70 XP (14 days) |
| All daily quests | 100 | Bonus for completion |
| Week without miss | 200 | Perfect week |
| 30-day streak | 500 | Major milestone |
| 100-day streak | 2000 | Legendary |

**Why it matters:** Consistency beats intensity. The habit of showing up is the master skill.

---

## XP Economy Balance

### Daily XP Targets

| Activity Level | Daily XP | Notes |
|----------------|----------|-------|
| **Light day** | 200-400 | Basic maintenance |
| **Normal day** | 400-800 | Good progress |
| **Power day** | 800-1200 | High performance |
| **Perfect day** | 1200-1500 | All systems firing |

### Level Progression (Compressed OSRS)

| Level | Total XP | Time to Reach |
|-------|----------|---------------|
| 10 | 1,154 | ~1-2 weeks |
| 25 | 8,740 | ~2-3 months |
| 50 | 101,333 | ~6-9 months |
| 75 | 1,210,421 | ~3-5 years |
| 99 | 13,034,431 | ~20-30 years |

**Philosophy:** Level 50 should feel like "you've made it" for a skill. Level 99 is lifetime achievement.

---

## Personal vs Universal

### Skills that are UNIVERSAL (good for anyone)

| Skill | Why Universal |
|-------|---------------|
| Strength | Everyone benefits from physical strength |
| Endurance | Heart health matters to everyone |
| Mobility | Movement quality is universal |
| Nutrition | Everyone eats |
| Recovery | Everyone needs rest |
| Focus | Attention matters in any pursuit |
| Consistency | Discipline helps everyone |

### Skills that are PERSONAL (may need customization)

| Skill | Personal Aspect | Generic Alternative |
|-------|-----------------|---------------------|
| **Presence** | "Dad time" specific | Could be "Relationships" |
| **Creation** | "Baby Brains" specific | Could be "Work" or "Projects" |

### Future: User-Defined Skills?

For public release, consider:
- Core 7 skills (universal)
- 2-3 customizable slots (user defines)
- Custom XP sources per user

---

## Quest System Integration

### Daily Quests (Reset at midnight)

| Quest | Requirements | XP | Skills |
|-------|--------------|-----|--------|
| **Morning Triple** | Routine + Weight + Supps | 300 | Mobility, Consistency, Nutrition |
| **Movement Minimum** | Any workout OR 10k steps | 100 | Strength/Endurance |
| **Deep Focus** | 2+ hour focus block | 200 | Focus, Creation |
| **Recovery Protocol** | Sleep 80+ AND no caffeine after 2pm | 150 | Recovery |
| **Present Dad** | 1+ hour quality time | 150 | Presence |

### Weekly Quests (Reset Sunday)

| Quest | Requirements | XP | Skills |
|-------|--------------|-----|--------|
| **Protein Champion** | Hit protein 5+ days | 500 | Nutrition |
| **Consistency King** | Activity logged 7/7 days | 400 | Consistency |
| **Iron Week** | Complete all scheduled workouts | 600 | Strength, Endurance |
| **Dad of the Week** | Quality time 5+ days | 500 | Presence |

### Monthly Challenges

| Quest | Requirements | XP | Skills |
|-------|--------------|-----|--------|
| **Iron Man** | Don't miss a workout all month | 2000 | Consistency |
| **Sleep Master** | Average sleep score 85+ | 1500 | Recovery |
| **Clean Machine** | No junk food all month | 1500 | Nutrition |

---

## Skill Display Priority

On dashboard, show skills in this order (highest impact first):

1. **Underleveled skills** - Skills falling behind (create urgency)
2. **Close to level-up** - Skills within 20% of next level (create momentum)
3. **Active quests** - Skills with related quest progress
4. **By total XP** - Default sort

---

## Skill Color Assignments

For visual differentiation:

| Skill | Color | Hex |
|-------|-------|-----|
| Strength | Red | `#ff6b6b` |
| Endurance | Blue | `#4ecdc4` |
| Mobility | Purple | `#a855f7` |
| Nutrition | Green | `#22c55e` |
| Recovery | Indigo | `#6366f1` |
| Focus | Orange | `#f97316` |
| Presence | Pink | `#ec4899` |
| Creation | Amber | `#f59e0b` |
| Consistency | Yellow | `#eab308` |

---

## Implementation Notes

### Database Changes Needed

If expanding from 7 to 9 skills:

```sql
-- Add new skills to player_skills
INSERT INTO player_skills (skill_name, current_xp, current_level)
VALUES
  ('focus', 0, 1),
  ('presence', 0, 1);

-- Update XP sources mapping
-- Rename 'work' to 'creation' if desired
UPDATE player_skills SET skill_name = 'creation' WHERE skill_name = 'work';
```

### Voice Intent Updates

New intents needed:
- "logged focus time" / "deep work done"
- "quality time with [child name]" / "dad time"

---

## Open Questions

1. **7 vs 9 skills?** - Stick with 7 MVP or expand to 9?
2. **Skill renaming?** - Change "Work" to "Creation"?
3. **Custom XP sources?** - Should users define their own?
4. **Social features?** - Leaderboards? (probably no, this is personal)
5. **Skill caps?** - Virtual levels past 99? Or hard cap?

---

## Recommendation

**Start with 9 skills.** The Mind (Focus) and People (Presence) domains are too important to leave out. They represent the areas that get neglected when optimizing health and work.

The current 7-skill backend can be extended:
- Add Focus and Presence to database
- Add XP hooks for new activities
- Update voice intents

The PWA should be designed for **9 skill cards** from the start, even if 2 are "coming soon" initially.

---

## Next Steps

1. **User decision:** Confirm 9-skill system
2. **Finalize XP values:** Balance the economy
3. **Design skill icons:** Midjourney prompts for 9 icons
4. **Update backend:** Add Focus + Presence skills
5. **Add voice intents:** Support new XP sources
