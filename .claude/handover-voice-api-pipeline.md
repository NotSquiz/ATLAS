# Handover: Voice API Pipeline for ATLAS Morning Routine

**Date:** January 14, 2026
**For:** Fresh agent to build Claude API integration for Voice Bridge
**Priority:** Token-efficient voice assistant for health/fitness tracking

---

## Mission

Build a frictionless morning routine system where the user wakes up, speaks to ATLAS, and gets guided through their day - minimal computer interaction, maximum efficiency.

**User context:** 38-year-old male, 16-month-old baby waking at 4-5am, rehabilitation + fitness focus, Australian timezone.

---

## Priority Order (User-Specified)

1. **Morning status + guided routine** (most important)
2. **Workout logging** (after workout ends, one interaction)
3. **Memory capture** (nice to have)
4. **Meal logging** (last)

**Critical constraint:** Token efficiency. Minimize API costs.

---

## Persona: The Lethal Gentleman

ATLAS speaks with:
- **Lethal Gentleman** stereotype - understated confidence, practical concern
- **Stoicism** - no complaints, focus on what's controllable
- **Musashi** - warrior philosophy, discipline, mastery through practice

**Existing voice documentation in codebase** - search for agentic voice doc or Lethal Gentleman references.

**Example tone:**
> "GREEN. 7.2 hours. Your body is ready. Strength B - shoulder focus. The work is the reward."

NOT:
> "Great job on your sleep! You're doing amazing! Let's crush this workout!"

---

## What Already Exists (DO NOT REBUILD)

### 1. Garmin Integration (Complete - Jan 14)
```bash
python -m atlas.health.cli garmin status  # → Configured: Yes, Session valid: Yes
python -m atlas.health.cli garmin sync    # → Pulls sleep, HRV, body battery, RHR
```
**File:** `atlas/health/garmin.py`
- User authenticated with Forerunner 165
- First real sleep data: January 15, 2026

### 2. Health CLI (9 commands working)
```bash
python -m atlas.health.cli daily          # Morning sync with Traffic Light
python -m atlas.health.cli routine start  # Interactive 18-min guided routine
python -m atlas.health.cli workout        # Today's workout protocol
python -m atlas.health.cli supplements    # Checklist
```

### 3. Traffic Light System
**File:** `atlas/health/router.py`
- GREEN: Full intensity
- YELLOW: -15% intensity
- RED: Recovery only

### 4. Morning Routine (18 min, 5 sections)
**File:** `config/workouts/phase1.json`
- Feet & plantar fascia (4 min)
- Ankle mobility (4 min)
- Lower back & hips (4 min)
- Shoulder rehab (4 min)
- Posture reset (2 min)

### 5. Voice Bridge (Exists - needs connection)
**Architecture:** PowerShell → microphone → WSL2 → Claude Code → response back
**Files:** Check `atlas/voice/` directory, existing agent records in `.claude/`

---

## What Needs to Be Built

### Phase 1: Morning Status + Guided Routine

#### 1A. 5am Cron Job
**New file:** `atlas/health/morning_sync.py`

```python
async def run_morning_sync():
    """Runs at 5am automatically."""
    if not is_garmin_auth_valid():
        logger.critical("GARMIN AUTH EXPIRED")
        return

    service = HealthService()
    result = await service.morning_sync()
    save_to_json("~/.atlas/morning_status.json", result)
```

Cron: `0 5 * * * /home/squiz/ATLAS/.venv/bin/python -m atlas.health.morning_sync`

#### 1B. Voice → Status Query
When user says "What's my status?":
1. Read cached `morning_status.json` (0 tokens)
2. Format response with Lethal Gentleman tone
3. Speak via TTS

**Token cost: 0** (read from cache)

#### 1C. Guided Routine with Timers
When user says "Start my routine":
1. Load steps from `phase1.json`
2. For each step:
   - Speak instruction (TTS, local)
   - Run timer (`asyncio.sleep`, local)
   - Play chime (local audio)
3. Speak "Complete."

**Token cost: ~50** (initial intent only)

Timers are local Python - accurate, no tokens per step.

---

### Phase 2: Workout Logging (Post-Workout)

#### Design: Log AFTER Workout Ends

User does the workout with timer guidance, then logs everything in ONE interaction at the end.

**Voice interaction:**
```
User: "Log workout. Goblet squat 3 sets of 12 at 20 kilos.
       Floor press 3 sets of 10 at 15 kilos. Felt strong."

ATLAS: "Logged Strength B. Goblet squat 3x12 at 20kg. Floor press 3x10 at 15kg.
        RPE 6. Solid work."
```

**Token cost: ~200** (one Haiku call to parse and confirm)

#### Workout Execution with Timers

The workout itself should be timer-based like the morning routine:
- Exercise name + form cues
- Lifting cadence (e.g., "3 seconds down, 1 second pause, 2 seconds up")
- Rest timers between sets
- Equipment change pauses

**New file:** `atlas/health/workout_runner.py`
```python
async def run_workout(workout_plan):
    """Guided workout with timers, form cues, cadence."""
    for exercise in workout_plan.exercises:
        speak(f"{exercise.name}. {exercise.form_cue}")
        speak(f"Tempo: {exercise.tempo}. {exercise.sets} sets of {exercise.reps}.")

        for set_num in range(exercise.sets):
            speak(f"Set {set_num + 1}. Begin.")
            await asyncio.sleep(exercise.set_duration)
            play_chime()

            if set_num < exercise.sets - 1:
                speak(f"Rest. {exercise.rest_seconds} seconds.")
                await asyncio.sleep(exercise.rest_seconds)
                play_chime()

        # Equipment change pause if needed
        if exercise.equipment_change:
            speak("Change equipment. 30 seconds.")
            await asyncio.sleep(30)
```

---

### Phase 3: Memory Capture (Nice to Have)

When user says "Remember to order red light panel":
1. Classify thought (Haiku, ~50 tokens)
2. Store in semantic memory with source tag
3. Confirm: "Noted. Red light panel, health project."

**File exists:** `atlas/orchestrator/classifier.py` (ThoughtClassifier)

---

### Phase 4: Meal Logging

When user says "Log meal: 3 eggs, toast with butter":
1. Parse food items (Haiku, ~100 tokens)
2. Lookup nutrition (USDA API - may need debugging)
3. Store and confirm

**Files exist:** `atlas/nutrition/service.py`, `atlas/nutrition/usda_client.py`
**Known issue:** USDA API had connection problems previously.

---

## Token Efficiency Strategy

### 1. Cache Everything Possible
- Morning status at 5am → JSON file
- Workout plan for today → JSON file
- Supplement list → JSON file

### 2. Local Pattern Matching First
Before calling Haiku, check for simple patterns:
```python
SIMPLE_PATTERNS = {
    r"(what'?s|show|my) status": "get_status",
    r"start (my |the )?routine": "start_routine",
    r"(what'?s|show|today'?s) workout": "get_workout",
    r"(\d+) seconds?": "timer",
    r"(stop|pause|skip|next)": "control",
}
```
These cost 0 tokens.

### 3. Haiku for Understanding, Tools for Doing
- Haiku parses intent (~50-100 tokens)
- Python executes (0 tokens)
- Response from template or cache (0 tokens)

### 4. Batch Logging
- Workout: Log everything at END (1 call, not per-exercise)
- Meals: Log full meal (not per-item)

### Estimated Daily Costs
| Action | Tokens | Cost |
|--------|--------|------|
| Morning status | 0 (cache) | $0 |
| Start routine | 50 | $0.00005 |
| 18-min routine | 0 (timers) | $0 |
| Get workout | 0 (cache) | $0 |
| 45-min workout | 0 (timers) | $0 |
| Log workout | 200 | $0.0002 |
| 1 memory capture | 100 | $0.0001 |
| 1 meal log | 200 | $0.0002 |
| **Daily total** | ~550 | **~$0.0006** |

**Monthly estimate: ~$0.02** (if using caching properly)

---

## Voice Bridge Architecture

**Current flow:**
```
Windows PowerShell
    ↓ (microphone capture)
Audio file
    ↓ (passed to WSL2)
STT (Moonshine/Whisper)
    ↓ (transcribed text)
Claude Code CLI (current)  →  Should become: Haiku API
    ↓ (response text)
TTS (Kokoro)
    ↓ (audio)
Windows audio output
```

**Files to investigate:**
- `atlas/voice/bridge_file_server.py`
- `atlas/voice/pipeline.py`
- `scripts/atlas_launcher.py`
- Any `.claude/` agent records about Voice Bridge

**Task:** Connect Voice Bridge to lightweight Haiku API instead of Claude Code CLI.

---

## Key Files Reference

| Purpose | File |
|---------|------|
| Garmin sync | `atlas/health/garmin.py` |
| Health orchestrator | `atlas/health/service.py` |
| Traffic Light | `atlas/health/router.py` |
| Workout service | `atlas/health/workout.py` |
| Morning routine config | `config/workouts/phase1.json` |
| CLI entry point | `atlas/health/cli.py` |
| Thought classifier | `atlas/orchestrator/classifier.py` |
| Nutrition service | `atlas/nutrition/service.py` |
| Voice pipeline | `atlas/voice/pipeline.py` |
| Voice bridge | `atlas/voice/bridge_file_server.py` |
| Persona/voice docs | Search for "Lethal Gentleman" |

---

## Prerequisites Before Starting

1. **Fund Anthropic API:** https://console.anthropic.com/settings/billing

2. **Verify Garmin working:**
   ```bash
   source /home/squiz/ATLAS/.venv/bin/activate
   python -m atlas.health.cli garmin status
   ```

3. **First real sleep data:** January 15, 2026 (tomorrow morning)

4. **Find Voice Bridge docs:**
   ```bash
   grep -r "voice bridge" /home/squiz/ATLAS/.claude/
   grep -r "Lethal Gentleman" /home/squiz/ATLAS/
   ```

---

## Success Criteria

1. ✅ Morning status query < 1 second (cached)
2. ✅ Guided routine runs with accurate timers
3. ✅ Workout runs with form cues, cadence, rest timers
4. ✅ Post-workout logging in one voice interaction
5. ✅ Daily token cost < $0.01
6. ✅ Lethal Gentleman persona maintained

---

## Questions Resolved

| Question | Answer |
|----------|--------|
| Voice Bridge architecture | PowerShell → mic → WSL2 → Claude Code → back |
| API Key | User will fund at console.anthropic.com |
| Workout logging | Timer-based during, log AFTER (one call) |
| Persona | Lethal Gentleman + Stoicism + Musashi |
| Priority | Status → Workout → Memory → Meals |
| Token efficiency | Critical - use caching extensively |
