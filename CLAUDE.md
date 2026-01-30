# ATLAS Project Context

---
## ⛔ NON-NEGOTIABLE WORKFLOW RULES ⛔
**READ THIS FIRST. EVERY SESSION. NO EXCEPTIONS.**

### CHECKPOINT 1: Before Writing Any Code
```
STOP. Ask yourself:
□ Did I read the relevant existing file FIRST?
□ Did I check .claude/handoff.md for current state?
□ For multi-file changes: Did I spawn planner agent?
□ For new features: Did I use TodoWrite to plan steps?
```

### CHECKPOINT 2: Before Committing
```
STOP. Ask yourself:
□ Did I run tests? (pytest tests/)
□ Did I check for hardcoded secrets?
□ Did I update .claude/handoff.md with what changed?
□ For new components: Did I follow docs/DOCUMENTATION_UPDATE_GUIDE.md?
```

### CHECKPOINT 3: Agent Spawning Rules
| Situation | Action | Agent Prompt Location |
|-----------|--------|----------------------|
| Planning multi-file feature | Spawn planner agent | `.claude/agents/planner.md` |
| Reviewing code quality | Spawn code-reviewer | `.claude/agents/code-reviewer.md` |
| Security-sensitive changes | Spawn security-reviewer | `.claude/agents/security-reviewer.md` |
| Baby Brains activity QC | Spawn activity-auditor | `.claude/agents/activity-auditor.md` |

### CHECKPOINT 4: Mandatory File Checks
**BEFORE starting work, READ these files:**
- `.claude/handoff.md` - Current session state (ALWAYS)
- `.claude/rules/atlas-conventions.md` - Coding standards
- `.claude/rules/security.md` - Security rules

### The "Wait" Pattern (Use When Uncertain)
Before finalizing any significant decision, pause and ask:
> "Wait. What assumptions am I making? What could I be missing?"

### TodoWrite Is Mandatory For:
- Any task with 3+ steps
- Bug fixes affecting multiple files
- Feature implementations
- Mark items complete IMMEDIATELY when done

### User Operating Instructions
**To get best results from Claude:**
- Start sessions with: "Read .claude/handoff.md first"
- For planning: "Use the planner agent from .claude/agents/"
- For reviews: "Run code-reviewer agent before committing"
- After sessions: "Update handoff.md with what we did"

---

## What ATLAS Is
Voice-first AI assistant with <1.8s latency target.
Hardware: ThinkPad X1 Extreme, 16GB RAM, RTX 3050 Ti 4GB.

## V2 Orchestrator Components
| Component | File | Purpose |
|-----------|------|---------|
| SkillLoader | atlas/orchestrator/skill_executor.py | Load skills progressively |
| SubAgentExecutor | atlas/orchestrator/subagent_executor.py | Spawn isolated sub-agents |
| HookRunner | atlas/orchestrator/hooks.py | PRE/POST validation hooks |
| SessionManager | atlas/orchestrator/session_manager.py | Session state + git context |
| ScratchPad | atlas/orchestrator/scratch_pad.py | Intermediate results tracking |
| ConfidenceRouter | atlas/orchestrator/confidence_router.py | Route responses by confidence level |
| CodeSimplifier | atlas/simplifier/code_simplifier.py | On-demand code quality analysis |
| ThoughtClassifier | atlas/orchestrator/classifier.py | Classify thoughts → PEOPLE/PROJECTS/IDEAS/ADMIN/RECIPES |
| DigestGenerator | atlas/digest/ | Generate daily/weekly summaries from semantic memory |
| ATLASScheduler | atlas/scheduler/loop.py | Background scheduler for proactive tasks |
| NutritionService | atlas/nutrition/service.py | Meal logging with USDA FDC nutrition lookup |
| HealthService | atlas/health/service.py | Daily status orchestration with Traffic Light |
| TrafficLightRouter | atlas/health/router.py | GREEN/YELLOW/RED workout intensity routing |
| WorkoutService | atlas/health/workout.py | Workout protocols from phase configs |
| AssessmentService | atlas/health/assessment.py | Baseline tracking, LSI calculation, GATE evaluation |
| PhaseService | atlas/health/phase.py | Training phase management with GATE integration |
| SupplementService | atlas/health/supplement.py | Supplement checklist and compliance tracking |
| PainService | atlas/health/pain.py | Pain logging with voice formatting (0-10 scale) |
| SessionBuffer | atlas/voice/session_buffer.py | Rolling 5-exchange context buffer for LLM (10-min TTL) |
| GarminService | atlas/health/garmin.py | Garmin Connect API integration via garth library |
| MorningSyncService | atlas/health/morning_sync.py | Cached health status for voice pipeline |
| RoutineRunner | atlas/health/routine_runner.py | Timer-based 18-minute morning protocol |
| WorkoutRunner | atlas/health/workout_runner.py | Timer-based workout execution with form cues |
| InteractiveWorkoutTimer | atlas/voice/bridge_file_server.py | Voice-controlled workout with user-paced sets |
| BridgeFileServer | atlas/voice/bridge_file_server.py | WSL2↔Windows voice bridge with intent routing |
| AssessmentProtocolRunner | atlas/health/assessment_runner.py | Voice-guided 71-test baseline assessment protocol |
| NumberParser | atlas/voice/number_parser.py | Spoken number, BP, weight+reps parsing with hedging |
| AssessmentCalculator | atlas/health/assessment_calculator.py | 1RM estimation, LSI calculation |
| WorkoutScheduler | atlas/health/scheduler.py | Program day tracking, missed workout handling, phase management |
| InteractiveRoutineRunner | atlas/voice/bridge_file_server.py | Voice-guided morning routine with form cues |
| CommandCentreUI | scripts/atlas_launcher.py | OSRS-style Windows GUI with inventory, skills, quests tabs |
| QuestPanel | scripts/atlas_launcher.py | Daily todo display with XP rewards, domain color-coding |
| DynamicSquareSlots | scripts/atlas_launcher.py | Responsive inventory slots that maintain square aspect ratio |
| SkillTooltips | scripts/atlas_launcher.py | OSRS-style hover tooltips showing XP progress |
| TimerIPC | atlas/voice/bridge_file_server.py | Timer state via session_status.json (100ms polling) |
| StateModels | atlas/voice/state_models.py | WorkoutState, RoutineState, AssessmentState, TimerState dataclasses |
| TimerBuilders | atlas/voice/timer_builders.py | Timer dict building logic extracted from BridgeFileServer |
| IntentDispatcher | atlas/voice/intent_dispatcher.py | Priority-ordered intent dispatch replacing if/elif chain |
| IntentPatterns | config/voice/intent_patterns.json | Externalized intent patterns (hot-configurable) |
| Qwen3TTS | atlas/voice/tts_qwen.py | Voice cloning TTS with Jeremy Irons (Lethal Gentleman) |
| VoiceConfig | config/voice/qwen_tts_voices.json | Voice cloning configs (ref audio + transcript) |
| BBWarmingService | atlas/babybrains/warming/service.py | Orchestrate daily warming pipeline |
| BBCommentGenerator | atlas/babybrains/warming/comments.py | Sonnet API comment drafts with voice spec QC |
| BBTranscriptFetcher | atlas/babybrains/warming/transcript.py | YouTube transcript fetching via API |
| BBTargetScorer | atlas/babybrains/warming/targets.py | Niche relevance scoring + engagement levels |
| BBVoiceSpec | atlas/babybrains/voice_spec.py | Load + section-extract BabyBrains-Writer.md |
| BBCrossRepoSearch | atlas/babybrains/cross_repo.py | Search docs across 5 BB repos |
| BBDatabase | atlas/babybrains/db.py | 10-table schema + query helpers |
| BBModels | atlas/babybrains/models.py | Dataclasses for all BB entities |
| BBCLI | atlas/babybrains/cli.py | CLI: status, find-doc, warming commands |

## Infrastructure (January 2026)
Based on Anthropic research papers. See `docs/V2_ORCHESTRATOR_GUIDE.md` for full details.

| Feature | Location | Purpose |
|---------|----------|---------|
| Session Handoff | `.claude/handoff.md` | Track session state for context transitions |
| Progress Tracking | `.claude/atlas-progress.json` | JSON task tracking (prevents model modification) |
| Sandbox Configs | `config/sandbox/*.json` | Security isolation for sub-agents and hooks |
| Confidence Router | `atlas/orchestrator/confidence_router.py` | Route by verbalized confidence + "Wait" pattern |
| Activity QC Hook | `knowledge/scripts/check_activity_quality.py` | Voice/structure validation for Activity Atoms |
| Activity Pipeline | `atlas/pipelines/activity_conversion.py` | 7-stage pipeline with quality audit gate |
| Quality Audit | `atlas/pipelines/activity_conversion.py:audit_quality()` | Grade A enforcement via Voice Rubric |
| Health CLI | `atlas/health/cli.py` | 9-command CLI for fitness tracking |
| Baseline Assessments | `config/assessments/baseline.json` | 40+ tests across 9 categories + GATE criteria |
| Phase Configs | `config/workouts/phase1.json` | Workout protocols + daily routine |
| Fitness Schema | `atlas/memory/schema_fitness.sql` | Pain log, assessments, phases, exercises |
| Garmin Integration | `atlas/health/garmin.py` | Sleep, HRV, body battery sync via direct HTTP |
| Garmin Auth Setup | `scripts/garmin_auth_setup.py` | One-time authentication, tokens in ~/.garth/ |
| Voice Bridge | `atlas/voice/bridge_file_server.py` | File-based PowerShell↔WSL2 voice communication |
| Morning Status Cache | `~/.atlas/morning_status.json` | Cached Garmin + Traffic Light for 0-token queries |
| Audio Utils | `atlas/voice/audio_utils.py` | Chime + countdown beeps for timers (550Hz-880Hz) |
| Voice Assessment Protocol | `config/assessments/protocol_voice.json` | 71 tests across 3 sessions with voice prompts |
| Workout HR Data | `atlas/memory/schema_fitness.sql` | Garmin activity sync → workout_hr_data table |
| Workout Scheduler | `atlas/health/scheduler.py` | Program day calculation, sequential catch-up mode |
| Workout Sessions Table | `atlas/health/scheduler.py` | Tracks completed workouts for program tracking |
| Routine Form Guides | `config/exercises/routine_form_guides.json` | 20 exercises with setup, cues, common mistakes |
| Command Centre UI | `scripts/atlas_launcher.py` | Windows GUI with large timer, button controls |
| Timer Status IPC | `~/.atlas/.bridge/session_status.json` | Real-time timer data for UI (100ms polling) |
| Button Commands | `~/.atlas/.bridge/command.txt` | UI→Server: PAUSE/RESUME/SKIP/STOP/START_TIMER |
| BB Schema | `atlas/babybrains/schema.sql` | 10 tables for warming, trends, content pipeline |
| BB Configs | `config/babybrains/*.json` | Platform rules, warming schedule, audience personas |
| BB Cross-Repo Map | `config/babybrains/cross_repo_paths.json` | Topic→file mappings across 5 repos |
| BB Human Story | `config/babybrains/human_story.json` | Personal angle profile (PLACEHOLDER) |
| BB MCP Tools | `atlas/mcp/server.py` | bb_status, bb_find_doc, bb_warming_daily/done/status |

### Garmin Integration
```bash
# One-time setup (after adding GARMIN_USERNAME/PASSWORD to .env)
python scripts/garmin_auth_setup.py

# Check status
python -m atlas.health.cli garmin status

# Sync today's data
python -m atlas.health.cli garmin sync

# Full morning sync (Garmin + Traffic Light + workout)
python -m atlas.health.cli daily
```

```python
from atlas.health.garmin import GarminService, is_garmin_auth_valid

# Quick auth check (for 5am cron fail-fast)
if not is_garmin_auth_valid():
    logger.critical("GARMIN AUTH EXPIRED")

# Sync daily metrics
service = GarminService()
metrics = await service.sync_today()
# Returns: GarminMetrics(sleep_hours, hrv_status, resting_hr, body_battery, ...)

# Sync activity HR data (after workout completion)
hr_data = await service.sync_latest_activity()  # Within last 4 hours
# Returns: {avg_hr, max_hr, duration_min, calories, activity_type, ...}
```

### Confidence Routing
```python
from atlas.orchestrator.confidence_router import route_by_confidence

result = route_by_confidence(response_text, domain="health")
# Returns: action (PROCEED, VERIFY_EXTERNAL, VERIFY_ADVERSARIAL, REGENERATE)
# Safety-critical domains trigger confidence inversion (high confidence = more verification)
```

### The "Wait" Pattern (89.3% blind spot reduction)
```python
from atlas.orchestrator.confidence_router import apply_wait_pattern

correction_prompt = apply_wait_pattern(original_response, query)
# Adds: "Wait. Before evaluating, pause and consider: What assumptions did I make?..."
```

### Voice API Pipeline (January 2026)
Token-efficient voice-first health queries via PowerShell↔WSL2 bridge.

**Voice Commands:**
```bash
# Quick status (0 tokens - reads from cache)
"my status"           → "YELLOW. Battery 32. HRV 56. Proceed with caution."
"what's my status"    → Same as above

# Detailed briefing (0 tokens - reads from cache)
"morning briefing"    → Full metrics: body battery, HRV, sleep, stress, workout
"how was my sleep"    → Same as above

# Pain logging (0 tokens)
"shoulder is at a 4"  → "Logged shoulder right at 4. Monitor it."
"pain status"         → "Pain levels: shoulder right 4, ankle left 2."

# Supplement logging (0 tokens)
"took my vitamin d"   → "Checked off vitamin d."
"took my preworkout supps" → "Checked off 6 preworkout supplements."
"took my morning supps"    → "Checked off 6 preworkout supplements." (morning aliases to preworkout)
"took my breakfast supps"  → "Checked off 7 breakfast supplements."
"took my bedtime supps"    → "Checked off 5 before bed supplements."
"what supps are next?"     → Time-aware: shows preworkout/breakfast/bedtime based on hour
"what supps do I still need?" → Lists remaining by timing category

# Weight/body composition (0 tokens)
"83.2 kilos at 18 percent body fat" → "Logged. 83.2 kilos, 18.5% body fat. 0.3 down from last."
"log weight 83 kilos"       → "Logged. 83 kilos."
"83 kg 18% fat 42% muscle"  → "Logged. 83 kilos, 18% body fat, 42% muscle."
"weighed in at 83.2"        → "Logged. 83.2 kilos."
"what's my weight"          → "83.2 kilos, 18.5% body fat. 0.3 down from yesterday."
"body composition"          → "83.2 kilos. 18.5% body fat. 42% muscle. 55% water."
"weight trend"              → "Down 1.2 kilos this week. Body fat down 0.5%."

# Workout completion (0 tokens + optional Garmin sync)
"finished my workout" → "Strength A logged. 42 min. Avg HR 128, max 156."
"workout done but skipped squats" → "Got it. What did you skip or modify? Any notes?"

# Program/schedule management (0 tokens)
"start program"       → "Phase 1 started. Day 1, Week 1. Today: Strength A. Say start workout."
"schedule status"     → "Week 2, Day 10. On track. 8 workouts completed. Today: Strength B."
"what day am I on"    → Same as schedule status
"am I on track"       → Same as schedule status
"reset my program"    → "You're on Week 2 with 8 workouts. Reset? Say confirm or cancel." (requires confirmation)

# Interactive workout (0 tokens - stateful session, uses scheduler)
"start workout"       → "Week 1, Day 1. Strength A. 45 minutes. First: Goblet Squat. 3 sets of 6. Say ready."
"green day"           → Overrides traffic light: "Override to GREEN. Strength A. 45 minutes..."
"yellow day"          → Overrides traffic light: "Override to YELLOW. Strength A (reduced intensity)..."
"30 kilos"            → "Got it. 30 kilos. Say ready to begin."
"ready"               → "Set 1 at 30 kilos. Begin."
"done" / "finished"   → "Set 1 complete. Rest 90 seconds." (countdown beeps at 30s, 15s, 5s)
"how long"            → "45 seconds left." (during rest)
"skip"                → "Skipping Goblet Squat. Next: Floor Press..."
"stop workout"        → "Workout complete. 5 exercises done. Press COMPLETE or say finished workout to log."
# After stop: UI shows COMPLETE button, clicking logs workout
# Catch-up mode: if missed workouts, scheduler says "Catching up from Monday. Strength A..."
# Rest day: "Today is a recovery day. No workout scheduled. Rest or go for a walk."

# Interactive morning routine (0 tokens - stateful session with auto-timer)
"start routine"       → "Starting ATLAS Morning Protocol. 18 minutes total. First section: Feet & Plantar Fascia..."
"morning protocol"    → Same as above (start routine)
"start rehab"         → Same as above (start routine)
"pause" / "hold on"   → "Paused. Short Foot Exercise. Say resume to continue, or ask about form."
"how do I do this"    → "Short Foot Exercise. Lift arch without curling toes. Say resume when ready." (auto-pauses + form cues)
"show me the form"    → Same as above (form help from exercise library)
"resume" / "continue" → "Resuming Short Foot Exercise. 25 seconds remaining."
"skip" / "next"       → "Skipping Short Foot Exercise. Next: Ankle CARs. 5 reps..."
"how long" / "time"   → "35 seconds remaining."
"stop routine"        → "Routine stopped in Ankle Mobility, exercise 2. Good effort."
# Auto-advances when exercise timer completes (chime plays)
# Section complete chime plays between sections

# Command Centre button controls (alternative to voice)
# UI buttons write commands to ~/.atlas/.bridge/command.txt
[START] button        → START_TIMER (starts pending exercise timer)
[PAUSE] button        → PAUSE_ROUTINE (pauses timer, button changes to RESUME)
[RESUME] button       → RESUME_ROUTINE (resumes from pause)
[SKIP] button         → SKIP_EXERCISE (advances to next exercise)
[STOP] button         → STOP_ROUTINE (stops routine completely)
# Button states sync with server via session_status.json is_paused field
# Timer display: Large countdown (80pt), progress bar, exercise name, section, form cue

# Baseline assessments (0 tokens)
"what are baseline protocols?" → Explains 71 tests, 3 sessions, durations
"baseline protocol"      → Same as above (info query)
"start baseline"         → Prompts for session A/B/C choice
"session A"              → Starts body comp session (weight, measurements, BP, etc.)
"session B"              → Starts strength/mobility session (tests with timers)
"session C"              → Starts cardio session (HR tests, talk test)
"120 over 80"            → Natural BP input (parses systolic/diastolic)
"20 kilos for 5 reps"    → Natural weight+reps input
"go" / "stop" / "done"   → Timer control for timed tests

# Results tagged with protocol_run for quarterly comparison:
# baseline_2026_q1, baseline_2026_q2, etc. (auto-generated)

# Meal logging (uses Haiku for parsing)
"log meal: chicken and rice"  → Parses via USDA FDC, stores in semantic_memory

# Thought capture (0 tokens)
"remember to update the website"  → Classifies and stores via ThoughtClassifier
```

**Architecture:**
```
Windows (PowerShell) ←→ ~/.atlas/.bridge/ ←→ WSL2 (bridge_file_server.py)
                           │
                           ├── audio_in.raw (mic input)
                           ├── audio_out.raw (TTS response)
                           └── status.txt (ready/processing/done)
```

**Intent Detection Priority:**
1. Active assessment session (stateful) → 0 tokens
2. Assessment session pending → 0 tokens
3. Assessment resume → 0 tokens
4. Assessment info → 0 tokens ("what are baseline protocols?")
5. Assessment start → 0 tokens ("start baseline")
6. **Interactive workout active (stateful)** → 0 tokens
7. **Phase reset pending (confirmation)** → 0 tokens
8. **Schedule status** → 0 tokens ("schedule status", "what day am I on")
9. **Phase start/reset** → 0 tokens ("start program", "reset my program")
10. **Interactive workout start / traffic override** → 0 tokens ("start workout", "green day")
11. **Interactive routine active (stateful)** → 0 tokens
12. **Interactive routine start** → 0 tokens ("start routine")
13. Workout confirmation (stateful pending) → 0 tokens
14. Weight logging → 0 tokens
15. Pain logging/status → 0 tokens
16. Supplement logging/status → 0 tokens
17. Workout completion → 0 tokens + Garmin sync + scheduler log
18. Workout query → 0 tokens
19. Exercise query → 0 tokens
20. Health status → 0 tokens
21. Meal logging → Haiku API
22. Capture intents → 0 tokens
23. General queries → Haiku API (falls back to local Ollama)

**Key Files:**
| File | Purpose |
|------|---------|
| `atlas/voice/bridge_file_server.py` | Main voice bridge server with intent routing + timer state |
| `scripts/atlas_launcher.py` | Windows Command Centre UI with timer display + buttons |
| `atlas/voice/audio_utils.py` | Distinct chimes for timer events (start, complete, section) |
| `atlas/voice/session_buffer.py` | Rolling context buffer for LLM (5 exchanges, 10-min TTL) |
| `atlas/voice/number_parser.py` | Parse spoken numbers, BP, weight+reps with hedging |
| `atlas/health/pain.py` | PainService for voice-enabled pain logging |
| `atlas/health/morning_sync.py` | Status caching + voice formatting |
| `atlas/health/routine_runner.py` | Timer-based morning routine |
| `atlas/health/workout_runner.py` | Timer-based workout execution |
| `atlas/health/assessment_runner.py` | Voice-guided assessment protocol execution |
| `atlas/voice/audio_utils.py` | Chime generation |
| `config/assessments/protocol_voice.json` | 69 tests across 3 sessions (A/B/C) |
| `atlas/health/scheduler.py` | Workout scheduling, program day tracking, catch-up mode |
| `atlas/health/progression.py` | Progressive overload, weight recommendations |
| `config/exercises/routine_form_guides.json` | Form cues for 20 morning routine exercises |

**Intent Matching (Regex-Based):**
Workout and routine start intents use regex matching for flexibility:

```python
# Workout start pattern (regex):
# (start|begin|do|run|let's) + [optional fillers] + (workout|strength|cardio|training|zone|mobility)
# Excludes: stretch, routine, morning, rehab, protocol → these go to routine handler

# Examples that match workout:
"start workout"              # Direct match
"begin next strength workout" # Filler "next" allowed
"let's begin a workout"      # Filler "a" allowed
"start the cardio"           # Filler "the" allowed

# Examples that match routine (not workout):
"begin a stretch workout"    # "stretch" → routine
"start morning routine"      # "routine" → routine
"let's stretch"              # "stretch" → routine
```

**UI Button States:**
- `can_skip` flag in timer data controls SKIP button (disabled on last exercise)
- `workout_complete` / `routine_complete` modes show COMPLETE button
- COMPLETE button sends `LOG_WORKOUT` or `LOG_ROUTINE` based on mode

## Key Commands
- Tests: `pytest`
- BB tests: `pytest tests/babybrains/`
- Voice pipeline: `python atlas/voice/pipeline.py`
- BB CLI: `python -m atlas.babybrains.cli status`
- BB find doc: `python -m atlas.babybrains.cli find-doc "youtube"`
- BB warming: `python -m atlas.babybrains.cli warming daily`

## Key Documentation
- V2 Guide: docs/V2_ORCHESTRATOR_GUIDE.md
- Architecture: docs/ATLAS_ARCHITECTURE_V2.md
- Activity Pipeline: docs/HANDOVER_ACTIVITY_PIPELINE.md
- **Verification Prompts: docs/VERIFICATION_PROMPTS.md** (self-check patterns)

## Coding Standards
- Use async/await for all I/O
- Specific exceptions before catch-all
- Always add logging to new modules

## Current Focus
Phase 4 - Quality audit pipeline + intelligent retry with Wait pattern

### Activity Pipeline Commands (CLI Mode - No API Key)
```bash
# Convert single activity (primary mode)
python -m atlas.pipelines.activity_conversion --activity tummy-time

# With explicit retry count (uses Wait pattern for intelligent retry)
python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 3

# List pending activities
python -m atlas.pipelines.activity_conversion --list-pending

# Batch mode (only after skills reliably produce Grade A)
python -m atlas.pipelines.activity_conversion --batch --limit 10
```

### Quality Audit Pipeline
```python
# Quality audit grades activities A/B+/B/C/F using Voice Elevation Rubric
# Only Grade A proceeds to human review
# Non-A grades trigger intelligent retry with "Wait" pattern reflection

from atlas.pipelines.activity_conversion import ActivityConversionPipeline

pipeline = ActivityConversionPipeline()
result = await pipeline.convert_with_retry("tummy-time", max_retries=2)
# D79: Stage caching - retries skip INGEST/RESEARCH/TRANSFORM (60-70% faster)
# D79: Early truncation detection - fails fast if YAML incomplete
# Uses Wait pattern (89.3% blind spot reduction) between retries
```

### Pipeline Performance (D79)
- **Stage Caching**: First attempt runs full 7-stage pipeline, caches transform output. Retries skip stages 1-3 (INGEST/RESEARCH/TRANSFORM) and run only stages 4-7 (ELEVATE→AUDIT).
- **Early Truncation Detection**: Checks for `parent_search_terms:` terminator after ELEVATE, before expensive QC/AUDIT stages. Truncated output triggers immediate retry.
- **Result**: Retry time reduced from ~15-21 min to ~5-7 min (60-70% improvement).

### QC Superlative Exceptions (D39)
The QC hook blocks superlatives but allows these contexts:
- **"best"**: "works best", "best practices", "best interests of the child", "try your best"
- **"perfect"**: Negations ("not perfect", "doesn't need to be perfect"), verb form ("perfect the skill")
- **"extraordinary"**: Montessori contexts ("extraordinary absorptive"), relational ("extraordinary to your baby")
- **"incredible"**: Montessori phrase ("incredible focus")

See `knowledge/scripts/check_activity_quality.py` lines 121-160 for full exception patterns.

## 2nd Brain / Thought Classifier
"AI running a loop, not just AI as search" - proactive capture and organization.

### Voice → Classify → Save Flow
```python
# Speak: "Remember to update the Baby Brains landing page"
# Voice pipeline detects capture intent via CAPTURE_TRIGGERS
# ThoughtClassifier routes to: PROJECTS → baby-brains → website
# Stored with source: "classifier:projects:baby-brains:website"
```

### Categories
| Category | Sub-Projects | Patterns |
|----------|-------------|----------|
| PROJECTS | baby-brains (website/app/knowledge/os/marketing/content), health (sauna/red-light/garmin/workouts/ice-bath/running/meals) | hierarchical taxonomy |
| PEOPLE | - | names, "met with", "spoke to" |
| IDEAS | - | "what if", "idea:", "could we" |
| ADMIN | - | "pay", "bill", "deadline", "call" |
| RECIPES | - | "cooked", "made", "recipe" |

### Capture Commands
```bash
# Via voice (triggers: "remember", "note", "capture", "log", "save")
"Remember to order red light panel from China"  # → health:red-light

# Via MCP
atlas capture_thought "Build BB landing page"  # → baby-brains:website

# Via CLI
python -m atlas.orchestrator.classifier "Made carbonara tonight"  # → recipes
```

### Proactive Digests
```bash
# Generate daily digest
python -m atlas.scheduler.loop --once daily_digest

# Run scheduler daemon (7am daily, Sunday 6pm weekly)
python -m atlas.scheduler.loop --daemon
```

## Nutrition Tracking
Automatic calorie/macro calculation from natural language food descriptions.

### Meal Logging
```bash
# Via voice (triggers: "log meal", "had for breakfast/lunch/dinner", "just ate")
"Log meal: 100g chicken breast, cup of rice, broccoli"
# → "Logged meal. 450 cal, 45g protein, 35g carbs, 8g fat."

# Via MCP
atlas log_meal "5 crackers with 100g camembert, 50g salami"
```

### Components
| Component | File | Purpose |
|-----------|------|---------|
| NutritionService | atlas/nutrition/service.py | Orchestrate parse → lookup → store |
| USDAFoodData | atlas/nutrition/usda_client.py | USDA FoodData Central API client |
| FoodParser | atlas/nutrition/food_parser.py | Regex + Claude NLP for parsing |

### API Setup
```bash
# Get free USDA API key at: https://fdc.nal.usda.gov/api-key-signup.html
export USDA_API_KEY="your-key-here"
```

### Data Flow
```
"100g chicken, cup of rice"
  → FoodParser (Claude NLP) → [FoodItem, FoodItem]
  → USDA FDC lookup → NutrientInfo per item
  → Sum totals → Store in semantic_memory (source: classifier:health:meals)
```

## Health/Fitness Tracking
Comprehensive rehabilitation and fitness tracking with Traffic Light system, GATE evaluations, and phase management.

### CLI Commands
```bash
python3 -m atlas.health.cli daily --sleep 7.5 --hrv BALANCED --rhr 52  # Morning status
python3 -m atlas.health.cli workout                    # Today's workout protocol
python3 -m atlas.health.cli supplements               # Supplement checklist
python3 -m atlas.health.cli pain all                  # Log pain levels (all body parts)
python3 -m atlas.health.cli routine                   # Morning routine display
python3 -m atlas.health.cli routine start             # Interactive guided routine
python3 -m atlas.health.cli assess baseline           # Baseline testing protocol
python3 -m atlas.health.cli assess log --id ankle_dorsiflexion_left --value 9.5
python3 -m atlas.health.cli assess gate 1             # Check GATE 1 readiness
python3 -m atlas.health.cli phase                     # Current phase status
python3 -m atlas.health.cli phase check               # Check advancement readiness
python3 -m atlas.health.cli garmin status             # Check Garmin connection
python3 -m atlas.health.cli garmin sync               # Sync Garmin data manually
```

### Traffic Light System
```python
from atlas.health.router import TrafficLightRouter, TrafficLightStatus

router = TrafficLightRouter()
result = router.evaluate(sleep_hours=7.5, hrv_status="BALANCED", resting_hr=52)
# result.status = TrafficLightStatus.GREEN
# GREEN: Full intensity | YELLOW: -15% intensity | RED: Recovery only
```

### GATE System (Running Readiness)
| GATE | Timing | Key Tests |
|------|--------|-----------|
| GATE 1 | Week 12+ | Ankle LSI ≥90%, balance 60s, 25 heel raises |
| GATE 2 | Week 16+ | Hop tests LSI ≥90%, 2-mile jog |
| GATE 3 | Week 20+ | Hop tests LSI ≥95%, tempo run 20min |
| GATE 4 | Week 24+ | Sprint progression, RSA ≤10% decrement |

### Phase Management
- Phase 1 → Phase 2: Requires GATE 1 + 4 weeks minimum + pain ≤3/10
- Phase progression automatically checks GATE criteria
- Regression triggers: 3+ RED days/week, pain spike ≥6/10

### Assessment Categories
| Category | Tests |
|----------|-------|
| Strength | Trap bar deadlift, goblet squat, floor press |
| Mobility | Ankle dorsiflexion (WBLT), shoulder flexion, hip flexors |
| Stability | Single-leg balance, McGill curl-up, side planks |
| Cardio | Resting HR, HR recovery |
| Calf Strength | Single-leg heel raises |
| Hop Tests | Single/triple/crossover/timed hops (Phase 2+) |
| Agility | T-test, Illinois agility (Phase 2c/3) |

### Protocol Run Tracking (Quarterly Baselines)
Results are tagged with `protocol_run` for quarterly comparison:
```
baseline_2026_q1   # January baseline
baseline_2026_q2   # April baseline (3 months later)
gate_1_check       # GATE 1 assessment
retest_2026_q2     # Manual retest
```

Query quarterly progress:
```sql
SELECT * FROM assessments WHERE protocol_run = 'baseline_2026_q1';
```

### Key Files
| File | Purpose |
|------|---------|
| `atlas/health/cli.py` | 9-command CLI |
| `atlas/health/router.py` | Traffic Light logic |
| `atlas/health/garmin.py` | Garmin Connect sync + activity HR data |
| `atlas/health/service.py` | HealthService orchestration layer |
| `atlas/health/morning_sync.py` | 5am cron job + voice formatting (Lethal Gentleman) |
| `atlas/health/routine_runner.py` | Timer-based 18-min morning protocol |
| `atlas/health/workout_runner.py` | Timer-based workout with form cues |
| `atlas/health/assessment.py` | LSI calculation, GATE evaluation |
| `atlas/health/assessment_runner.py` | Voice-guided assessment protocol (69 tests) |
| `atlas/health/assessment_calculator.py` | 1RM estimation, LSI calculation |
| `atlas/health/phase.py` | Phase transitions with GATE integration |
| `atlas/voice/number_parser.py` | Parse spoken numbers, BP, weight+reps |
| `scripts/garmin_auth_setup.py` | One-time Garmin authentication |
| `config/assessments/baseline.json` | 40+ assessments with GATE criteria |
| `config/assessments/protocol_voice.json` | Voice protocol: 69 tests, 3 sessions |
| `config/workouts/phase1.json` | Phase 1 protocols + daily routine |
| `config/exercises/exercise_library.json` | 44 exercises with form cues |
| `docs/FITNESS/` | Research documentation |

### WorkoutExercise Extended Fields (January 2026)
Support for unilateral, isometric, and directional exercises:

```python
from atlas.health.workout_runner import WorkoutExercise

# Fields added for Phase 1 rehabilitation tracking
@dataclass
class WorkoutExercise:
    # ... existing fields ...
    per_side: bool = False          # Clamshells, side plank
    hold_seconds: Optional[int]     # McGill curl-up 8-10s
    side: Optional[str]             # 'left', 'right', 'both'
    distance_steps: Optional[int]   # Lateral band walks
    per_direction: bool = False     # Each direction tracking
```

Voice announcements adapt automatically:
- `per_side=True` → "3 sets of 15 each side"
- `per_direction=True` → "3 sets of 10 steps each direction"
- `hold_seconds=8` → "Hold 8 seconds each rep"

### Phase 1 Evidence-Based Improvements (January 2026)
Based on 2020-2026 research (Rio isometric protocol, Alfredson eccentric, McGill Big 3):

**Daily Routine:**
- Doorframe ER: 3×60s at 40-70% MVC (was 2×45s)
- Eccentric Calf Raises: 3×15 per side (was 10 reps)
- Added Clamshells for glute med activation

**Strength A (Monday):** McGill Curl-Up, Banded Ankle DF Mobilization, Single-Leg RDL
**Strength C (Friday):** Side Plank, Inverted Rows, Lateral Band Walks
**Saturday:** Zone 2 Extended (ruck/walk) replaced VO2 Max intervals (HIIT cleared after GATE 1)
