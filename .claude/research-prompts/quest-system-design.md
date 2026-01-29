# Quest System Design - Research Prompt for Opus

## Context
ATLAS is a voice-first AI assistant with an OSRS (Old School RuneScape)-inspired gamification layer. We want to design a Quest system that gamifies daily tasks and long-term projects, awarding XP when completed.

## Current System
- 12 Virtues across 3 domains: BODY, MIND, SOUL
- XP system with OSRS-style leveling (1-99)
- Voice-first input ("remember to update the website tomorrow")
- Semantic memory for thought capture
- ThoughtClassifier that routes thoughts to categories

## Quest System Requirements

### 1. Quest Types
Design a taxonomy of quest types:

**Daily Quests** (reset each day)
- Morning routine, meal logging, supplements
- Auto-generated from user's schedule
- Time-sensitive (must complete by end of day)

**Long-Term Projects** (like RS Quest Tab)
- Multi-step projects with milestones
- "Finish BB Website Landing Page" → 500 XP
- Progress tracking (0%, 25%, 50%, 75%, Complete)

**Habit Quests** (streak-based)
- "Meditate for 7 consecutive days"
- Bonus XP for streak maintenance
- Forgiveness mechanics (miss 1 of 7 days OK)

**Challenge Quests** (achievement-style)
- One-time accomplishments
- "Complete first 5K run" → unlock running quests

### 2. Quest Capture Flow
Design the voice → classification → quest creation flow:

```
User: "Tomorrow I want to finish the landing page design"
→ Parse intent: project task
→ Classify domain: MIND (Creation)
→ Estimate complexity: Medium (50-100 XP)
→ Ask for confirmation: "Add 'Finish landing page' as a quest? Estimated 75 XP."
→ Store in quest database
```

### 3. XP Calculation
Design the XP assignment algorithm:

**Factors to consider:**
- Difficulty (easy/medium/hard/epic)
- Estimated time investment
- Domain alignment (which virtue does it strengthen?)
- Historical data (how long did similar tasks take?)
- User feelings ("I'm dreading this" = more XP for completion)

**Proposed XP ranges:**
| Difficulty | XP Range | Examples |
|------------|----------|----------|
| Trivial | 10-20 | Check email, quick reply |
| Easy | 20-50 | Log meals, take supplements |
| Medium | 50-100 | Workout, 1-hour deep work |
| Hard | 100-250 | Complete project milestone |
| Epic | 250-500 | Ship major feature, run first 10K |

### 4. Quest Completion Detection
How does the system know when a quest is complete?

**Voice trigger:**
- "I finished the landing page"
- "Quest complete: morning routine"

**Auto-detection:**
- Health service logs workout → mark workout quest done
- Meal logged via voice → mark nutrition quest done
- Time tracker shows 2 hours deep work → mark focus quest done

**Manual UI:**
- Click quest in Quest tab to toggle complete

### 5. Quest Prioritization
Design the daily quest display order:

**Priority factors:**
- Time sensitivity (due today > due this week)
- XP value (higher XP quests more prominent)
- Streak risk (about to break streak = urgent)
- Domain balance (spread across BODY/MIND/SOUL)

### 6. Database Schema
Design the quest storage:

```sql
CREATE TABLE quests (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    quest_type TEXT,  -- daily, project, habit, challenge
    domain TEXT,      -- body, mind, soul
    virtue TEXT,      -- strength, focus, courage, etc.
    xp_reward INTEGER,
    difficulty TEXT,
    status TEXT,      -- pending, in_progress, completed, failed
    due_date TEXT,
    parent_quest_id TEXT,  -- for multi-step quests
    step_number INTEGER,
    streak_count INTEGER,
    created_at TEXT,
    completed_at TEXT
);

CREATE TABLE quest_templates (
    id TEXT PRIMARY KEY,
    title TEXT,
    recurrence TEXT,  -- daily, weekly, monthly
    conditions TEXT,  -- JSON of trigger conditions
    xp_base INTEGER,
    domain TEXT,
    virtue TEXT
);
```

### 7. Evening Reflection Integration
Design the nightly quest planning flow:

```
User: "Plan tomorrow"
→ Review incomplete quests
→ Suggest rollover or defer
→ Capture new intentions
→ Ask about energy/mood expectations
→ Generate optimized quest list
```

### 8. Adaptability for Other Users
Design for eventual monetization/public release:

- User-defined domains (not everyone has BODY/MIND/SOUL)
- Custom virtues and skills
- Configurable XP curves
- Template marketplace (share quest templates)
- Privacy-first design (all data local or user-controlled)

### 9. Anti-Burnout Mechanisms
Design protections against gamification fatigue:

- "Rest Day" quest (get XP for NOT doing productive things)
- Diminishing returns on same quest type
- Maximum daily XP cap to prevent obsession
- Streak forgiveness (1 miss per week doesn't break streak)
- "Good Enough" completions (80% credit for partial)

### 10. Integration Points
Map to existing ATLAS systems:

| System | Quest Integration |
|--------|------------------|
| HealthService | Auto-complete workout/nutrition quests |
| ThoughtClassifier | Route captured thoughts to quest creation |
| SemanticMemory | Store quest metadata for reflection |
| VoicePipeline | "Complete quest X" voice commands |
| DigestGenerator | Include quest progress in daily/weekly summaries |
| GamificationService | Award XP, update virtue levels |

## Deliverables Requested

1. **Complete Quest Taxonomy** - All quest types with examples
2. **XP Calculation Algorithm** - Pseudocode with test cases
3. **Database Schema** - Full SQL with indexes
4. **Voice Command Grammar** - All quest-related voice triggers
5. **UI/UX Wireframes** - Quest tab layout and interactions
6. **Evening Reflection Script** - Full conversation flow
7. **Anti-Burnout Rules** - Specific mechanisms and thresholds
8. **API Design** - Quest service endpoints
9. **Migration Path** - How to extend for other users
10. **Success Metrics** - How to know the system is working

## Constraints
- Must work voice-first (minimal UI interaction)
- Must integrate with OSRS aesthetic
- Must be adaptable for potential monetization
- Must respect user autonomy (no guilt mechanics)
- Must handle edge cases gracefully

## Prior Art to Research
- Habitica
- Todoist Karma
- Streaks app
- OSRS Quest system (requirements, progression)
- Gamification research (Yu-kai Chou's Octalysis)
