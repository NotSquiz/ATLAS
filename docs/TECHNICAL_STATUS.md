# ATLAS Technical Status

**Last Updated:** January 23, 2026
**Status:** Phase 0-3 COMPLETE + Phase 4 IN PROGRESS (Quality Audit Pipeline) + Health/Fitness Module COMPLETE + Garmin Integration COMPLETE + Voice API Pipeline COMPLETE + Voice Intents COMPLETE + Interactive Workout Timer COMPLETE + Workout Scheduler COMPLETE + Interactive Morning Routine COMPLETE + Voice Announcements COMPLETE + STOP Button Fix COMPLETE + BridgeFileServer Refactoring COMPLETE + Pipeline Audit D82-D88 COMPLETE

---

## Quick Reference

### Core Architecture
```
User Voice → STT (Moonshine) → Router → LLM → TTS (Kokoro) → Speaker
                                  ↓
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
                 LOCAL         HAIKU       AGENT_SDK
              (Qwen 3B)    (Direct API)   (Claude Code)
               ~220ms        ~2800ms        ~7400ms
                FREE        ~$0.001/q        FREE
```

### Key Files

| File | Purpose | Status |
|------|---------|--------|
| `atlas/llm/local.py` | OllamaClient for Qwen 3B | ✅ Working |
| `atlas/llm/api.py` | Direct Anthropic API (Haiku) | ✅ Working |
| `atlas/llm/cloud.py` | Claude Agent SDK wrapper | ✅ Working |
| `atlas/llm/router.py` | Three-tier semantic router | ✅ Working |
| `atlas/llm/cost_tracker.py` | SQLite budget tracking | ✅ Working |
| `atlas/voice/pipeline.py` | Full voice pipeline | ✅ Working |
| `atlas/voice/stt.py` | Moonshine/Whisper STT | ✅ Working |
| `atlas/voice/tts.py` | Kokoro TTS | ✅ Working |
| `atlas/voice/vad.py` | Silero VAD | ✅ Working |
| `atlas/memory/store.py` | MemoryStore with hybrid RRF search | ✅ Working |
| `atlas/memory/embeddings.py` | BGE-small-en-v1.5 ONNX embeddings | ✅ Working |
| `atlas/memory/blueprint.py` | CRUD API for health/fitness tables | ✅ Working |
| `atlas/memory/schema.sql` | Complete database schema | ✅ Working |
| `config/routing.yaml` | Router configuration | ✅ Created |

---

## R29 Hybrid Routing System

### Three Tiers

| Tier | Model | Use Case | Latency | Cost |
|------|-------|----------|---------|------|
| **LOCAL** | Qwen2.5-3B (Ollama) | Commands, timers, simple queries | ~220ms | Free |
| **HAIKU** | Claude 3.5 Haiku (Direct API) | Advice, explanations, drafting | ~2800ms | ~$0.001/query |
| **AGENT_SDK** | Claude via Agent SDK | Complex planning, multi-step tasks | ~7400ms | Free (Max Plan) |

### Router Classification

The router uses three-stage classification:

1. **Regex patterns** (<1ms): Safety keywords, commands, complex task indicators
2. **Embedding similarity** (~20ms): MiniLM-L6-v2 against tier prototypes
3. **Default fallback**: HAIKU when uncertain

```python
from atlas.llm import get_router, Tier

router = get_router()
decision = router.classify("what time is it")
# decision.tier = Tier.LOCAL, confidence=0.95, category="command"

decision = router.classify("plan my workout for the week")
# decision.tier = Tier.AGENT_SDK, confidence=0.85, category="complex"
```

### Cost Tracking

SQLite database at `~/.atlas/cost_tracker.db`:
- Logs all API usage (tier, tokens, cost, latency)
- Budget limits: $10/month, $0.33/day
- Soft limit (80%): Enables "thrifty mode" - prefers LOCAL
- Hard limit (100%): API blocked, LOCAL only

```python
from atlas.llm import get_cost_tracker

tracker = get_cost_tracker()
status = tracker.get_budget_status()
# status.monthly_spend, status.can_use_api, status.thrifty_mode
```

---

## Memory System (Phase 0)

### Status: ✅ IMPLEMENTED (January 7, 2026)

**Database:** `~/.atlas/atlas.db` (SQLite + WAL mode)

### Components

| Component | Purpose | Performance |
|-----------|---------|-------------|
| `embeddings.py` | BGE-small-en-v1.5 via sentence-transformers ONNX | 10.1ms/embedding |
| `store.py` | Hybrid RRF search (60% vector, 40% FTS) | ~100ms at 100K |
| `blueprint.py` | CRUD for health/fitness tables | <1ms |
| `schema.sql` | All tables + FTS5 triggers | - |

### Usage

```python
from atlas.memory import get_memory_store, get_embedder, get_blueprint_api

# Memory operations
store = get_memory_store()
store.add_memory("User prefers morning workouts", importance=0.8)
results = store.search_hybrid("workout", embedding, limit=5)

# Blueprint operations
api = get_blueprint_api()
api.log_daily_metrics(DailyMetrics(date=date.today(), sleep_hours=7.5, mood=7))
```

### Tables

| Table | Purpose |
|-------|---------|
| `semantic_memory` | Core memory with embeddings |
| `vec_semantic` | Vector index (sqlite-vec) |
| `fts_memory` | Full-text search index (FTS5) |
| `daily_metrics` | Sleep, HRV, weight, mood |
| `supplements` | Supplement catalog |
| `supplement_log` | Dosing log |
| `workouts` | Workout sessions |
| `workout_exercises` | Exercise details |
| `lab_results` | Blood work |
| `injuries` | Injury tracking + contraindications |

### Test

```bash
python scripts/test_memory.py          # Basic tests
python scripts/test_memory.py --scale  # 100K scale test
```

---

## Voice Pipeline Features

### Current Implementation (`atlas/voice/pipeline.py`)

1. **Router Integration**
   - Uses `ATLASRouter` instead of direct OllamaClient
   - Config: `use_router=True` (default)

2. **Filler Phrases**
   - When routing to cloud, speaks: "Let me see.", "One moment.", etc.
   - Masks ~2800ms API latency
   - Config: `enable_filler_phrases=True` (default)

3. **Streaming-First TTS**
   - Speaks complete sentences as they arrive
   - Doesn't wait for full LLM response

4. **Command Interrupts**
   - Monitors for: "stop", "wait", "quiet", "shush", "enough", "okay"
   - Fuzzy matching for typos
   - Stops TTS immediately when detected

5. **Hot Window Mode**
   - After ATLAS speaks, stays listening for 6 seconds
   - No need to press Enter for follow-up questions
   - Config: `hot_window_duration_s=6.0` (default)

### Running the Voice Pipeline

```bash
cd /home/squiz/ATLAS
source venv/bin/activate

# With router (requires ANTHROPIC_API_KEY for cloud tiers)
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python -m atlas.voice.pipeline

# Local-only mode
python -c "
from atlas.voice.pipeline import VoicePipeline, VoicePipelineConfig
config = VoicePipelineConfig(use_router=False)
import asyncio
asyncio.run(VoicePipeline(config).start())
"

# Text mode (no audio)
python -m atlas.voice.pipeline --text-mode
```

---

## Windows Command Centre

### File: `scripts/atlas_launcher.py`

CustomTkinter GUI with large timer display and button controls for voice + visual interaction.

**Layout:**
```
┌─────────────────────────────────────┐
│  ATLAS Command Centre    [START][STOP]
├─────────────────────────────────────┤
│              ┌─────┐                │
│              │  37 │  ← Large timer │
│              │ sec │    (80pt font) │
│              └─────┘                │
│     ●●●●●●●○○○○○○○○○  38%          │
├─────────────────────────────────────┤
│  Hip Flexor Stretch          8/20  │
│  Lower Back & Hips          [LEFT] │
│  💡 Squeeze glute of back leg.      │
├─────────────────────────────────────┤
│  [⏸ PAUSE]  [⏭ SKIP]  [⏹ STOP]     │
├─────────────────────────────────────┤
│  Voice: Lewis │ GPU: CUDA │ 1260ms │
├─────────────────────────────────────┤
│  ▾ Transcript (collapsible)        │
└─────────────────────────────────────┘
```

**Features:**
- **Timer Display**: Large 80pt countdown, progress bar, color-coded urgency
- **Exercise Info**: Name, section, counter (8/20), side indicator, form cue
- **Button Controls**: PAUSE/RESUME, SKIP, STOP (alternative to voice)
- **Transition Screen**: "GET READY" with setup tip during auto-advance
- Hold SPACEBAR to record, release to send (voice still works)
- Voice toggle (Lewis/Emma)
- Session cost and routing display
- STT/TTS latency display
- GPU status indicator (CUDA/CPU)
- Transcript history with timestamps

**Button Commands (via command.txt):**
| Button | Command | Action |
|--------|---------|--------|
| START | `START_TIMER` | Start timer on pending/ready screen |
| PAUSE | `PAUSE_ROUTINE` | Pause active timer (button changes to RESUME) |
| RESUME | `RESUME_ROUTINE` | Resume from pause |
| SKIP | `SKIP_EXERCISE` | Advance to next exercise |
| STOP | `STOP_ROUTINE` | Stop routine completely |

**Timer IPC (session_status.json):**
```json
{
  "timer": {
    "active": true,
    "mode": "routine",
    "exercise_name": "Hip Flexor Stretch",
    "remaining_seconds": 37,
    "is_paused": false,
    "form_cue": "Squeeze glute of back leg."
  }
}
```

**Running:**
```bash
# Windows PowerShell - with console (debugging)
python scripts/atlas_launcher.py

# Windows - silent (no console)
pythonw scripts/atlas_launcher.py
```

**Desktop Shortcuts:**
- `ATLAS_Launcher.bat` - Console mode
- `ATLAS_Launcher.vbs` - Silent mode

---

## Key Files Modified

| File | Changes |
|------|---------|
| `atlas/voice/stt.py` | Removed initial_prompt bias, disabled vad_filter, added 100ms silence head |
| `atlas/voice/tts.py` | GPU provider selection with CPU fallback |
| `atlas/voice/bridge_file_server.py` | Timer state machine, auto-advance logic, button command handlers, timer IPC |
| `atlas/voice/audio_utils.py` | Distinct chimes: timer start (660Hz), exercise complete (440→550→660Hz) |
| `atlas/llm/router.py` | Flexible timer patterns for LOCAL routing |
| `scripts/atlas_launcher.py` | Command Centre UI with timer display, button controls, state-driven rendering |

---

## Measured Latency (from Australia)

| Component | Latency |
|-----------|---------|
| STT (Moonshine) | ~600ms |
| Router classification | ~50ms |
| Qwen 3B local | ~220ms TTFT |
| Haiku Direct API | ~2800ms TTFT |
| Agent SDK | ~7400ms TTFT |
| TTS (Kokoro) | ~250ms |

**End-to-end with LOCAL:** ~1100ms
**End-to-end with HAIKU:** ~3700ms (filler phrase masks wait)

---

## Dependencies

### Installed
```
anthropic==0.75.0      # Direct API client
tenacity==9.1.2        # Retry logic
pybreaker==1.4.1       # Circuit breaker
httpx==0.28.1          # HTTP client
sentence-transformers  # Embedding router
torch, numpy, scipy    # ML dependencies
```

### Voice Components
```
kokoro-onnx            # TTS
moonshine / faster-whisper  # STT
silero-vad             # Voice activity detection
sounddevice            # Audio I/O
```

---

## Configuration Files

### `config/routing.yaml`
- Router thresholds (local: 0.65, haiku: 0.82, agent: 0.88)
- Budget limits ($10/month)
- Latency targets
- Persona failure messages
- Filler phrases

### `config/Modelfile.atlas`
- Ollama model config for Qwen 3B
- System prompt (Lethal Gentleman persona)

### `.env`
- ANTHROPIC_API_KEY (required for cloud tiers)

---

## Persona: The Lethal Gentleman

System prompt in `atlas/voice/pipeline.py`:
- Speaks economically, leads with shorter sentences
- No hedging qualifiers ("just", "maybe", "perhaps")
- Understated confidence, practical concern
- Brief responses: 1-3 sentences for simple queries

Failure messages:
- API error: "I cannot access that resource at the moment."
- Budget exceeded: "The external archives are temporarily unavailable."
- Uncertainty: Ask clarifying question, then escalate silently

---

## Orchestrator Infrastructure (January 2026)

### Status: ✅ IMPLEMENTED

ATLAS evolved from voice assistant to **agentic orchestrator** across Baby Brains ecosystem.

### Components

| File | Purpose | Status |
|------|---------|--------|
| `atlas/orchestrator/command_router.py` | Routes `/babybrains`, `/knowledge`, `/web`, `/app` | ✅ Working |
| `atlas/orchestrator/hooks.py` | Wraps validators for deterministic verification | ✅ Working |
| `atlas/orchestrator/skill_executor.py` | Dual-mode skill execution | ✅ Working |

### Cost Model (Critical Decision)

| Mode | Cost | Command |
|------|------|---------|
| CLI (default) | $0 (Max subscription) | `python -m atlas.orchestrator.skill_executor --skill draft_21s` |
| API | Per-token | `python -m atlas.orchestrator.skill_executor --skill draft_21s --api` |

**Key Insight:** Agent SDK = API costs. CLI mode uses Max subscription ($0).

### Testing

```bash
# Test command router
python -m atlas.orchestrator.command_router babybrains status
python -m atlas.orchestrator.command_router knowledge status

# Test skill executor (CLI mode - uses Max)
python -m atlas.orchestrator.skill_executor --skill draft_21s --repo babybrains-os
```

### V2 Components Status

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| SubAgentExecutor | `subagent_executor.py` | ✅ Complete | Fixed 7 CRITICAL + 6 HIGH issues (Jan 8, 2026) |
| HookTiming | `hooks.py` | ✅ Complete | PRE/POST enum, hook_name field, get_hooks_by_timing(), run_all_for_timing(timeout), CLI --timing/--list/--input, logging + specific exceptions (Jan 8) |
| SessionManager | `session_manager.py` | ✅ Complete | Git diff pattern, state persistence |
| Progressive Loading | `skill_executor.py` | ✅ Complete | SkillSection dataclass, 8 new methods, 5 CLI flags, partial matching (Jan 8) |
| ScratchPad | `scratch_pad.py` | ✅ Complete | ScratchEntry dataclass, file persistence, step tracking, CLI (Jan 8) |
| Activity QC Hook | `knowledge/scripts/check_activity_quality.py` | ✅ Complete | Voice/structure/cross-ref validation for Activity Atoms (Jan 9) |
| Pipelines Directory | `atlas/pipelines/__init__.py` | ✅ Complete | Pipeline orchestrator package directory (Jan 9) |
| Activity Conversion Pipeline | `atlas/pipelines/activity_conversion.py` | ✅ Complete | 7-stage pipeline with quality audit gate (Jan 9) |
| Quality Audit Stage | `audit_quality()` method | ✅ Complete | Grade A enforcement via Voice Rubric (Jan 9) |
| Intelligent Retry | `convert_with_retry()` + `reflect_on_failure()` | ✅ Complete | Wait pattern for 89.3% blind spot reduction (Jan 9) |
| LLM Context Checking (D77) | `check_activity_quality.py` | ✅ Complete | Pressure/outcome/transition false positive fixes (Jan 21) |
| Stage Caching + Truncation (D79) | `activity_conversion.py` | ✅ Complete | 60-70% faster retries, early truncation detection (Jan 21) |
| CLI Error Display Fix (D80) | `activity_conversion.py` | ✅ Complete | Print result.error for FAILED status, fix misleading retry count (Jan 22) |
| --auto-approve Fix (D81) | `activity_conversion.py` | ✅ Complete | Fix --auto-approve not working with --next flag (Jan 22) |
| Status Handlers (D82) | `activity_conversion.py` | ✅ Complete | Add REVISION_NEEDED/QC_FAILED handlers to --next path (Jan 23) |
| Summary Counts Fix (D83) | `activity_conversion.py` | ✅ Complete | Fix stale cache bug - update cache before calculating counts (Jan 23) |
| Exit Codes (D84) | `activity_conversion.py` | ✅ Complete | Add sys.exit(1) for --next path failures (Jan 23) |
| Batch Retry (D85) | `activity_conversion.py` | ✅ Complete | Batch mode now uses convert_with_retry() (Jan 23) |
| SKIPPED Handler (D86) | `activity_conversion.py` | ✅ Complete | Handle SKIPPED status in CLI paths (Jan 23) |
| Adversarial Coverage (D87) | `activity_conversion.py` | ✅ Complete | Increase from 5000 to 15000 chars (~75% coverage) (Jan 23) |
| File Lock on Parse (D88) | `activity_conversion.py` | ✅ Complete | Add LOCK_SH when reading progress file (Jan 23) |
| CLI Mode | `SkillExecutor(timeout=300)` | ✅ Complete | Max subscription - no API key needed (Jan 9) |
| Stdin-Based CLI (D24) | `skill_executor.py`, `subagent_executor.py` | ✅ Complete | Pass prompts via stdin to avoid ARG_MAX (Jan 10) |
| Deterministic Slug (D25) | `activity_conversion.py:_fix_canonical_slug()` | ✅ Complete | Post-process canonical_slug derivation (Jan 10) |
| Zero-Tolerance Superlatives (D26) | `elevate_voice_activity.md` | ✅ Complete | CRITICAL section + BLOCK rule (Jan 10) |
| Zero-Tolerance Pressure (D32) | `elevate_voice_activity.md` | ✅ Complete | CRITICAL section + BLOCK rule + permission-giving alternatives (Jan 10) |
| Robust JSON Parsing (D33) | `activity_conversion.py:_extract_audit_json()` | ✅ Complete | Truncation detection + auto-repair + extended final timeout (Jan 10) |
| Sandbox Disabled (D34) | `activity_conversion.py` | ✅ Complete | Prevents EROFS errors with claude CLI (Jan 11) |
| Context-Aware QC (D35) | `check_activity_quality.py`, `hooks.py` | ✅ Complete | False positive fixes + principle slug normalization (Jan 11) |
| Age Range Normalization (D36) | `activity_conversion.py` | ✅ Complete | Trust label over raw min_months + specific retry feedback (Jan 11) |
| Deduplication Verification (D37) | `activity_conversion.py` | ✅ Complete | --verify command, duplicate detection, group context (Jan 11) |
| Empty Response Detection (D38) | `skill_executor.py`, `subagent_executor.py` | ✅ Complete | Detect CLI exit 0 with empty stdout (Jan 11) |
| QC False Positive Fix (D39) | `check_activity_quality.py` | ✅ Complete | Relational superlative exceptions (Jan 11) |
| ELEVATE Context Optimization (D40) | Multiple files | ✅ Complete | 47% context reduction + verification protocol + LLM context check (Jan 11) |
| Adversarial Audit Prompt (D41) | `activity_conversion.py` | ✅ Complete | Skeptical auditor + BLOCKING vs ADVISORY distinction (Jan 11) |
| Interactive Workout Timer (D58) | `bridge_file_server.py` | ✅ Complete | Voice-controlled user-paced workout with countdown beeps (Jan 17) |
| Weight Tracking (D59) | `bridge_file_server.py`, `number_parser.py` | ✅ Complete | Simple weight prompt during workout, `parse_weight_value()` (Jan 17) |

### V2 Gaps (From Masterclass Analysis)

| Gap | Priority | Status |
|-----|----------|--------|
| Sub-agent support | High | ✅ DONE |
| Multi-point hooks | High | ✅ DONE (PRE/POST, MID deferred) |
| Context management | High | ✅ DONE |
| Adversarial checking | Medium | ✅ DONE (in SubAgentExecutor) |
| Progressive loading | Medium | ✅ DONE (Jan 8, 2026) |
| Scratch pad | Low | ✅ DONE (Jan 8, 2026) |

See `docs/ATLAS_ARCHITECTURE_V2.md` for full implementation plan.

---

## Health/Fitness Module (January 2026)

### Status: ✅ IMPLEMENTED

Comprehensive fitness tracking system for injury rehabilitation with Traffic Light system, GATE evaluations, and phase management.

### Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Health CLI | `atlas/health/cli.py` | ✅ Complete | 9 commands: daily, workout, supplements, pain, routine, assess, phase, stats, garmin |
| TrafficLightRouter | `atlas/health/router.py` | ✅ Complete | GREEN/YELLOW/RED based on sleep, HRV, RHR |
| WorkoutService | `atlas/health/workout.py` | ✅ Complete | Loads phase configs, injury-aware filtering |
| SupplementService | `atlas/health/supplement.py` | ✅ Complete | Checklist, compliance tracking |
| AssessmentService | `atlas/health/assessment.py` | ✅ Complete | 40+ tests, LSI calculation, GATE evaluation |
| PhaseService | `atlas/health/phase.py` | ✅ Complete | Phase transitions with GATE integration |
| GarminService | `atlas/health/garmin.py` | ✅ Complete | Sleep, HRV, body battery + activity HR sync (Jan 17) |
| AssessmentProtocolRunner | `atlas/health/assessment_runner.py` | ✅ Complete | Voice-guided 69-test baseline protocol (Jan 17) |
| NumberParser | `atlas/voice/number_parser.py` | ✅ Complete | Spoken numbers, BP, weight+reps parsing (Jan 17) |
| AssessmentCalculator | `atlas/health/assessment_calculator.py` | ✅ Complete | 1RM estimation, LSI calculation (Jan 17) |
| MorningSyncService | `atlas/health/morning_sync.py` | ✅ Complete | Cached status, voice formatting (Jan 15) |
| RoutineRunner | `atlas/health/routine_runner.py` | ✅ Complete | Timer-based 18-min morning protocol (Jan 15) |
| WorkoutRunner | `atlas/health/workout_runner.py` | ✅ Complete | Timer-based workout with form cues (Jan 15) |
| Garmin Auth | `scripts/garmin_auth_setup.py` | ✅ Complete | One-time auth, tokens in ~/.garth/ |
| Garmin Tests | `tests/health/test_garmin.py` | ✅ Complete | 31 tests passing |
| Baseline Config | `config/assessments/baseline.json` | ✅ Complete | 9 categories, GATE 1-4 criteria |
| Phase 1 Config | `config/workouts/phase1.json` | ✅ Complete | Protocols + daily routine |
| Fitness Schema | `atlas/memory/schema_fitness.sql` | ✅ Complete | pain_log, assessments, phases, exercises, workout_hr_data |
| Voice Protocol Config | `config/assessments/protocol_voice.json` | ✅ Complete | 69 tests across 3 sessions (A/B/C) with voice prompts |

### Features

| Feature | Status | Notes |
|---------|--------|-------|
| Traffic Light System | ✅ Working | GREEN (full), YELLOW (-15%), RED (recovery) |
| Daily Morning Routine | ✅ Working | 5 sections, 18 min, interactive guided mode |
| Pain Tracking | ✅ Working | 5 body parts, 0-10 scale, validation |
| Assessment System | ✅ Working | Baseline, progress, LSI calculation |
| GATE Evaluation | ✅ Working | GATE 1-4 with specific test criteria |
| Phase Management | ✅ Working | Advancement with GATE checks, regression triggers |
| Input Validation | ✅ Working | Sleep hours (0-24), HRV choices, pain levels |
| Error Handling | ✅ Working | JSON parse, date parse, None access, division by zero |
| Garmin Integration | ✅ Working | Sleep, HRV, body battery, RHR + activity HR sync |
| Voice Assessment Protocol | ✅ Working | 69 tests, 3 sessions, natural BP/weight input |
| Garmin Auth | ✅ Working | One-time setup, tokens auto-refresh |
| Fail-Fast Health Check | ✅ Working | `is_garmin_auth_valid()` for cron jobs |

### CLI Commands

```bash
# Garmin integration
python3 -m atlas.health.cli garmin status        # Check connection
python3 -m atlas.health.cli garmin sync          # Sync today's data

# Daily workflow
python3 -m atlas.health.cli routine              # Morning routine
python3 -m atlas.health.cli pain all             # Log pain levels
python3 -m atlas.health.cli daily                # Morning sync (auto-pulls Garmin)
python3 -m atlas.health.cli workout              # Today's workout
python3 -m atlas.health.cli supplements          # Supplement checklist

# Assessment workflow
python3 -m atlas.health.cli assess baseline      # View protocols
python3 -m atlas.health.cli assess log --id ankle_dorsiflexion_left --value 9.5
python3 -m atlas.health.cli assess progress      # View progress
python3 -m atlas.health.cli assess gate 1        # Check GATE readiness

# Phase management
python3 -m atlas.health.cli phase                # Current status
python3 -m atlas.health.cli phase check          # Advancement check
python3 -m atlas.health.cli phase advance        # Advance (if ready)
```

### Verification Status

| Check | Result |
|-------|--------|
| Code Review | ✅ Completed - 4 sub-agents |
| Critical Bugs Fixed | ✅ 8 issues resolved |
| Input Validation | ✅ Added for pain, sleep, HRV |
| Error Handling | ✅ JSON, dates, None access, division by zero |
| End-to-End Test | ✅ All commands verified |

### Known Limitations

| Limitation | Priority | Notes |
|------------|----------|-------|
| ~~Garmin integration stub~~ | ~~P2~~ | ✅ COMPLETE (Jan 14, 2026) |
| ~~5am Automation~~ | ~~P2~~ | ✅ COMPLETE - morning_sync.py can be cron'd (Jan 15) |
| Phase 2/3 configs | P3 | Not needed until Week 13+ |
| No pain history view | P3 | Enhancement for later |
| No supplement deactivation | P3 | Enhancement |

---

## Voice API Pipeline (January 2026)

### Status: ✅ IMPLEMENTED

Token-efficient voice-first health queries via PowerShell↔WSL2 bridge. Enables frictionless morning routine.

### Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| BridgeFileServer | `atlas/voice/bridge_file_server.py` | ✅ Complete | Health intent routing added (Jan 15) |
| MorningSyncService | `atlas/health/morning_sync.py` | ✅ Complete | Cache + voice formatting |
| RoutineRunner | `atlas/health/routine_runner.py` | ✅ Complete | Timer-based 18-min protocol |
| WorkoutRunner | `atlas/health/workout_runner.py` | ✅ Complete | Timer-based workout execution |
| AudioUtils | `atlas/voice/audio_utils.py` | ✅ Complete | Chime generation (440Hz) |

### Key Design Decisions

| Decision | Description |
|----------|-------------|
| D48: Direct HTTP for Garmin | `garth.connectapi()` returned empty; fixed with direct HTTP to connectapi.garmin.com |
| D49: Intent Before LLM | Health queries use regex to bypass LLM (0 tokens) |
| D50: Two Response Formats | Quick status vs detailed briefing |
| D56: Sleep API Endpoint Fix | Changed from `/sleep-service/sleep/` to `/wellness-service/wellness/dailySleepData/` (Jan 17) |

### Voice Commands

| Command | Response Type | Tokens |
|---------|--------------|--------|
| "my status" | Quick one-liner | 0 |
| "morning briefing" | Detailed metrics | 0 |
| "how was my sleep" | Detailed metrics | 0 |
| "log meal: chicken rice" | Nutrition lookup | ~200 |

### Token Cost

| Action | Tokens | Monthly Cost |
|--------|--------|--------------|
| Status queries | 0 | $0 |
| Meal logging | ~200 | ~$0.006 |
| Thought capture | 0 | $0 |
| **Total estimate** | ~550/day | **~$0.02/month** |

### Known Limitations

| Limitation | Priority | Notes |
|------------|----------|-------|
| ~~Sleep API empty~~ | ~~P3~~ | ✅ FIXED (D56) - Changed to `/wellness-service/wellness/dailySleepData/` endpoint |
| HRV onboarding | P3 | Watch needs 7+ days for BALANCED/UNBALANCED status |
| No trend analysis | P2 | Future: yesterday comparison, weekly trends |
| No predictive insights | P3 | Future: "low reserves by 3pm" |

---

## Voice Intent Implementation (January 2026)

### Status: ✅ IMPLEMENTED

Comprehensive voice intent routing for health tracking, supplements, pain logging, and workout completion.

### Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| PainService | `atlas/health/pain.py` | ✅ Complete | Voice formatting, 0-10 scale, body part aliases |
| SessionBuffer | `atlas/voice/session_buffer.py` | ✅ Complete | 5 exchanges, 10-min TTL, uses atlas.db |
| Pain Intents | `bridge_file_server.py` | ✅ Complete | Negation checking, status query support |
| Supplement Intents | `bridge_file_server.py` | ✅ Complete | Individual before batch detection |
| Workout Completion | `bridge_file_server.py` | ✅ Complete | Smart confirmation flow, uses get_todays_workout() |

### Bug Fixes (Phase 0)

| Fix | File | Notes |
|-----|------|-------|
| HRV status not passed | `service.py:206` | Now passes hrv_status from metrics |
| Body battery not stored | `blueprint.py`, `schema.sql` | Added hrv_status + body_battery fields |
| Insufficient data → YELLOW | `router.py` | Changed to RED (conservative default) |
| Body battery YELLOW threshold | `router.py` | Added explicit 25-49 → YELLOW check |
| Garmin token permissions | `~/.garth/*.json` | Fixed to chmod 600 |

### Bug Fixes (Phase 4 - Workout Completion)

| Fix | File | Notes |
|-----|------|-------|
| Silent data loss | `bridge_file_server.py:835-837,876-878` | Error handlers now return honest "Couldn't log workout" instead of lying |
| Class variable state bug | `bridge_file_server.py:302` | `_pending_workout` moved from class to instance variable |
| No state timeout | `bridge_file_server.py:762-766` | Added 5-minute TTL for pending workout (prevents stale confirmations) |
| Positive notes not captured | `bridge_file_server.py:184-188` | Expanded WORKOUT_ISSUE_PATTERNS with positive feedback patterns |

### Bug Fixes (Phase 5 - Voice Bridge LLM + Assessment Info)

| Fix | File | Notes |
|-----|------|-------|
| Local LLM fallback broken | `bridge_file_server.py:1640-1647` | Changed `self.llm.chat()` to `self.llm.generate().content` (OllamaClient has no .chat()) |
| .env not loaded | `bridge_file_server.py:21-22` | Added `from dotenv import load_dotenv; load_dotenv()` |
| .env format wrong | `.env` | Fixed raw keys to `ANTHROPIC_API_KEY=...` format |
| Assessment info queries miss | `bridge_file_server.py:223-232` | Added `ASSESS_INFO_PATTERNS` with regex for "what are baseline protocols?" |
| False negatives for info | `bridge_file_server.py:1264-1273` | Changed exclusion to check `startswith()` not `in` (so "how long is baseline assessment" works) |

### Voice Commands Added

| Command | Intent | Response |
|---------|--------|----------|
| "shoulder is at a 4" | Pain logging | "Logged shoulder right at 4. Monitor it." |
| "no pain in my shoulder" | Pain (rejected) | Falls through to LLM (negation detected) |
| "pain status" | Pain status | "Pain levels: shoulder right 4, ankle left 2." |
| "took my vitamin d" | Supplement individual | "Checked off vitamin d." |
| "took my preworkout supps" | Supplement batch | "Checked off 6 preworkout supplements." |
| "took my morning supps" | Supplement batch (alias) | "Checked off 6 preworkout supplements." |
| "took my breakfast supps" | Supplement batch | "Checked off 7 breakfast supplements." |
| "took my bedtime supps" | Supplement batch | "Checked off 5 before bed supplements." |
| "what supps are next?" | Supplement status | Time-aware response by hour |
| "what supps do I still need?" | Supplement remaining | Lists by timing category |
| "finished my workout" | Workout completion | "Strength A logged. 45 minutes. Well executed." |
| "workout done but skipped squats" | Workout with issues | "Got it. What did you skip or modify?" |
| "yes log it" | Workout confirmation | "Strength A logged with notes. 45 minutes." |
| "session A" | Start assessment session | "Session A. Body composition. Step on scale." |
| "120 over 80" | Blood pressure (natural) | "One twenty over eighty. Recorded." |
| "20 kilos for 5 reps" | Weight+reps (natural) | "Twenty kilos for five. Recorded." |
| "go" / "stop" / "done" | Timer control | Starts/stops timed tests |
| "undo" / "go back" | Correction | Returns to previous test |
| "what are baseline protocols?" | Assessment info | "Baseline assessment has 69 tests across 3 sessions..." |
| "baseline protocol" | Assessment info | Same as above |
| "how long is baseline assessment?" | Assessment info | Duration breakdown by session |
| "start workout" | Interactive workout start | "Strength A. 45 minutes. First: Goblet Squat. 3x6. Say ready." |
| "30 kilos" | Weight input | "Got it. 30 kilos. Say ready to begin." |
| "ready" | Start set | "Set 1 at 30 kilos. Begin." |
| "done" / "finished" | Complete set | "Set 1 complete. Rest 90 seconds." |
| "how long" | Rest remaining | "45 seconds left." |
| "skip" | Skip exercise | "Skipping Goblet Squat. Next: Floor Press..." |
| "stop workout" | End early | "Workout stopped. 3 exercises completed." |

### Intent Detection Priority

```
1. WORKOUT_CONFIRM (stateful pending)
2. ASSESSMENT_ACTIVE (stateful - during test)
3. ASSESSMENT_SESSION_PENDING (waiting for A/B/C)
4. ASSESSMENT_RESUME ("resume baseline")
5. ASSESSMENT_INFO ("what are baseline protocols?")
6. ASSESSMENT_START ("start baseline")
7. INTERACTIVE_WORKOUT_ACTIVE (stateful - handles ready/done/skip)
8. INTERACTIVE_WORKOUT_START ("start workout")
9. WEIGHT
10. PAIN (log or status)
11. SUPPLEMENT (individual, batch, or status)
12. WORKOUT_COMPLETE
13. WORKOUT (query)
14. EXERCISE (query)
15. HEALTH (status or briefing)
16. MEAL
17. CAPTURE
18. LLM fallback
```

### Architecture Decisions

| Decision | Summary |
|----------|---------|
| D51 | Session buffer uses main atlas.db (not separate file) |
| D52 | Supplement: check individual names BEFORE batch keywords |
| D53 | Insufficient recovery data defaults to RED (conservative) |
| D54 | Pain intent negation checking (20-char window) |
| D55 | Supplement timing: 3 categories (preworkout, with_meal, before_bed) |

### Verification

| Test | Result |
|------|--------|
| PainService log/format | ✅ Passed |
| SessionBuffer add/get/format | ✅ Passed |
| TrafficLightRouter insufficient → RED | ✅ Passed |
| TrafficLightRouter body battery 30 → YELLOW | ✅ Passed |
| Negation check "no pain" | ✅ Not triggered |

---

## Voice-Guided Assessment Protocol (January 2026)

### Status: ✅ IMPLEMENTED

69-test baseline assessment protocol with voice-first interface, natural language input parsing, and Garmin integration.

### Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| AssessmentProtocolRunner | `atlas/health/assessment_runner.py` | ✅ Complete | State machine for 69 tests across 3 sessions |
| NumberParser | `atlas/voice/number_parser.py` | ✅ Complete | Parse spoken numbers with hedging, units, BP, weight+reps |
| AssessmentCalculator | `atlas/health/assessment_calculator.py` | ✅ Complete | 1RM estimation (Epley formula), LSI calculation |
| Voice Protocol Config | `config/assessments/protocol_voice.json` | ✅ Complete | 69 tests with prompts, validation, input types |
| Workout HR Data Schema | `atlas/memory/schema_fitness.sql` | ✅ Complete | workout_hr_data table for Garmin activity sync |

### Sessions

| Session | Tests | Focus |
|---------|-------|-------|
| A | 15 tests | Body composition (weight, measurements, BP, resting HR) |
| B | 38 tests | Strength/mobility (1RM, ROM, FMS, balance) |
| C | 16 tests | Cardio (zone tests, recovery, talk test) |

### Input Types Supported

| Type | Examples | Parser |
|------|----------|--------|
| Numeric | "82", "eighty two", "about 82 kilos" | `parse_spoken_number()` |
| Timed | "go"→start, "stop"→end with elapsed time | Timer with 100ms beeps |
| Boolean | "yes", "pain-free", "nope" | `parse_boolean()` |
| Categorical | "balanced", "low" | `parse_categorical()` |
| FMS | "three", "compensation", "pain" | `parse_fms_score()` |
| Compound | "120 over 80", "20 kilos for 5 reps" | `parse_blood_pressure()`, `parse_weight_reps()` |

### Garmin Activity Sync

After workout completion, automatically syncs Garmin activity HR data:

```python
# User: "finished my workout"
# → Logs workout to DB
# → Syncs Garmin activity (within 4 hours)
# → Stores HR data in workout_hr_data table
# ATLAS: "Strength A logged. 42 min. Avg HR 128, max 156."
```

| Data Captured | Source |
|---------------|--------|
| Resting HR, HRV, Body Battery | Daily Garmin sync |
| Workout Avg/Max HR, Calories | Activity sync after "finished workout" |
| Duration, Activity Type | Activity sync |

### Voice Commands

| Command | Action |
|---------|--------|
| "session A/B/C" | Start specific session |
| "skip" | Skip current test |
| "undo" / "go back" | Return to previous test |
| "pause" / "resume" | Pause/resume session |
| "what test is this" | Repeat current test prompt |
| "progress" | Show completion status |

### Verification Fixes Applied

| Issue | Fix |
|-------|-----|
| "ninety" parsed as "n ety" | Changed unit patterns to use word boundaries |
| "one twenty" = 21 for BP | Added explicit BP "one X" patterns (one twenty = 120) |
| Timezone bug in activity age | Changed to `datetime.now(AEST)` with timezone-aware parsing |
| Activity-workout mismatch | Added `expected_type` validation |
| Silent parse errors | Added explicit `return None` after exceptions |

---

## Phase 1 Workout Program Improvements (January 18, 2026)

### Status: ✅ IMPLEMENTED

Evidence-based Phase 1 workout program improvements with full system integration.

### Components Updated

| Component | File | Changes |
|-----------|------|---------|
| WorkoutExercise (runner) | `atlas/health/workout_runner.py` | Added per_side, hold_seconds, side, distance_steps, per_direction fields |
| WorkoutExercise (blueprint) | `atlas/memory/blueprint.py` | Same fields for database persistence |
| Exercise Library | `config/exercises/exercise_library.json` | Added 8 new exercises with form cues |
| Phase 1 Config | `config/workouts/phase1.json` | Updated daily routine, strength protocols, Zone 2 Extended |
| Voice Pipeline | `atlas/voice/bridge_file_server.py` | Updated announcements for per_side, per_direction, hold_seconds |

### New WorkoutExercise Fields

| Field | Type | Purpose |
|-------|------|---------|
| `per_side` | bool | Exercise performed per side (clamshells, side plank) |
| `hold_seconds` | Optional[int] | Isometric holds (McGill curl-up 8-10s) |
| `side` | Optional[str] | 'left', 'right', 'both' for unilateral tracking |
| `distance_steps` | Optional[int] | Step-based exercises (lateral walks) |
| `per_direction` | bool | Exercise performed each direction |

### New Exercises Added (8 total)

| Exercise | Category | Purpose |
|----------|----------|---------|
| mcgill_curl_up | core | McGill Big 3 component |
| clamshells | hip | Glute med activation, knee valgus fix |
| side_plank | core | McGill Big 3 component |
| inverted_row | upper_body_pull | Horizontal pulling volume |
| lateral_band_walks | hip | Knee valgus correction |
| single_leg_rdl | lower_body | Ankle compensation fix |
| suitcase_carry | functional | Anti-lateral flexion |
| neck_harness | neck | Blueprint standard |

### Daily Routine Changes

| Change | Before | After |
|--------|--------|-------|
| Doorframe ER | 2×45s | 3×60s (Rio protocol) |
| Eccentric Calf Raises | 10 reps | 3×15 (Alfredson protocol) |
| Clamshells | Not present | 2×15 per side |

### Strength Protocol Changes

**Strength A (Monday):**
- Added McGill Curl-Up (3×10, 8s holds)
- Added Banded Ankle DF Mobilization (3×10, RIGHT only)
- Added Single-Leg RDL (3×8, right priority)
- Added Goblet Squat (4×10)
- Added KB Swings (4×15)

**Strength C (Friday):**
- Added Side Plank (3×30s/side)
- Added Inverted Rows (3×12)
- Added Lateral Band Walks (3×10 steps/direction)
- Added Trap Bar Deadlift (4×6)
- Added Turkish Get-Up (2×3/side)
- Added KB Clean & Press (3×6/side)

**Saturday:**
- Replaced VO2 Max 4×4 intervals with Zone 2 Extended
- Added ruck walk as preferred modality
- HIIT clearance requirements documented for Phase 2

### Voice Pipeline Updates

| Feature | Implementation |
|---------|----------------|
| per_side exercises | Voice says "each side" (e.g., "3 sets of 10 each side") |
| per_direction exercises | Voice says "each direction" |
| hold_seconds | Voice says "Hold X seconds each rep" |
| Notes truncation | Long notes truncated to 50 chars for voice |

### Verification Status

| Check | Result |
|-------|--------|
| All JSON files valid | ✅ Passed |
| WorkoutExercise dataclass complete | ✅ Passed |
| Voice announcements correct | ✅ Passed |
| 11 new exercises present | ✅ Passed |
| Config files synchronized | ✅ Passed |

---

## Workout Scheduler (January 2026)

### Status: ✅ IMPLEMENTED

Intelligent workout scheduling with program day tracking, missed workout handling, and phase management confirmation flow.

### Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| WorkoutScheduler | `atlas/health/scheduler.py` | ✅ Complete | Sequential catch-up mode, program day tracking |
| workout_sessions table | `atlas/health/scheduler.py` | ✅ Complete | Tracks completed workouts with duration, HR, notes |
| Schedule Status Handler | `atlas/voice/bridge_file_server.py` | ✅ Complete | Voice-first schedule queries |
| Phase Start/Reset Handler | `atlas/voice/bridge_file_server.py` | ✅ Complete | Confirmation flow for destructive operations |

### Features

| Feature | Status | Notes |
|---------|--------|-------|
| Sequential Catch-Up Mode | ✅ Working | Missed workouts done in order (Monday missed = do Monday on Tuesday) |
| Program Day/Week Tracking | ✅ Working | Tracks days since phase start |
| Confirmation Flow for Reset | ✅ Working | "reset my program" requires confirmation with 30s timeout |
| Rest Day Handling | ✅ Working | Sunday returns friendly message, doesn't start interactive workout |
| No-Phase Handling | ✅ Working | Prompts user to "start program" instead of silent auto-start |
| Already-Done Detection | ✅ Working | Prevents duplicate workouts on same day |
| Traffic Light Override | ✅ Working | "green day" / "yellow day" bypasses Garmin-derived intensity |

### Voice Commands

| Command | Intent | Response |
|---------|--------|----------|
| "start program" | Phase start (first time) | "Phase 1 started. Day 1, Week 1. Today: Strength A. Say start workout." |
| "schedule status" | Schedule query | "Week 2, Day 10. On track. 8 workouts completed." |
| "what day am I on" | Schedule query | Same as above |
| "am I on track" | Schedule query | Same as above |
| "reset my program" | Phase reset (confirm) | "You're on Week 2 with 8 workouts. Reset? Say confirm or cancel." |
| "confirm" | Reset confirmation | "Phase 1 started fresh. Day 1, Week 1. Today: Strength A." |
| "cancel" | Reset cancellation | "Reset cancelled. Still on Week 2, Day 10." |
| "start workout" (rest day) | Rest day message | "Today is a recovery day. No workout scheduled. Rest or go for a walk." |
| "start workout" (no phase) | No-phase prompt | "No program started yet. Today would be Strength A. Say 'start program' to begin." |

### Architecture Decisions

| Decision | Summary |
|----------|---------|
| D60 | Sequential mode for catch-up (not calendar-based) |
| D61 | Confirmation required for reset operations (30s timeout) |
| D62 | "start program" vs "reset my program" distinction |
| D63 | Rest days return message instead of starting workout |
| D64 | No-phase returns special status requiring explicit start |

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS workout_sessions (
    id INTEGER PRIMARY KEY,
    phase_name TEXT NOT NULL,
    protocol_id TEXT NOT NULL,
    program_day INTEGER NOT NULL,
    completed_at TEXT NOT NULL,
    duration_minutes INTEGER,
    avg_hr INTEGER,
    max_hr INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL
);
```

### Verification Status

| Check | Result |
|-------|--------|
| Code Review Self-Check | ✅ Passed |
| Junior Analyst Review | ✅ Passed - 3 issues fixed |
| Inversion Test | ✅ Passed - edge cases validated |
| Rest day handling | ✅ Returns friendly message |
| Reset confirmation flow | ✅ 30s timeout with state tracking |
| No-phase handling | ✅ Prompts for explicit start |

---

## Interactive Morning Routine (January 2026)

### Status: ✅ IMPLEMENTED

Voice-guided 18-minute morning protocol with auto-advancing timers, form cues, and section-based navigation.

### Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| InteractiveRoutineRunner | `atlas/voice/bridge_file_server.py` | ✅ Complete | State machine for routine execution |
| RoutineRunner | `atlas/health/routine_runner.py` | ✅ Complete | Timer-based 18-min protocol (CLI mode) |
| Routine Form Guides | `config/exercises/routine_form_guides.json` | ✅ Complete | 20 exercises with setup, cues, common mistakes |

### Features

| Feature | Status | Notes |
|---------|--------|-------|
| Auto-advancing timers | ✅ Working | Exercises auto-advance when timer completes |
| Form help on demand | ✅ Working | "how do I do this" provides form cues |
| Pause/resume | ✅ Working | User controls timing |
| Skip exercises | ✅ Working | Move to next exercise in sequence |
| Section complete chimes | ✅ Working | Audio feedback between sections |
| Time remaining queries | ✅ Working | "how long" returns remaining seconds |

### Voice Commands

| Command | Intent | Response |
|---------|--------|----------|
| "start routine" | Start morning protocol | "Starting ATLAS Morning Protocol. 18 minutes total. First section: Feet & Plantar Fascia..." |
| "morning protocol" | Start morning protocol | Same as above |
| "start rehab" | Start morning protocol | Same as above |
| "pause" / "hold on" | Pause current exercise | "Paused. Short Foot Exercise. Say resume to continue." |
| "how do I do this" | Form help | "Short Foot Exercise. Lift arch without curling toes..." |
| "show me the form" | Form help | Same as above |
| "resume" / "continue" | Resume exercise | "Resuming Short Foot Exercise. 25 seconds remaining." |
| "skip" / "next" | Skip exercise | "Skipping Short Foot Exercise. Next: Ankle CARs. 5 reps..." |
| "how long" / "time" | Time remaining | "35 seconds remaining." |
| "stop routine" | End early | "Routine stopped in Ankle Mobility, exercise 2. Good effort." |

### Daily Routine Sections (18 min total)

| Section | Duration | Exercises |
|---------|----------|-----------|
| Feet & Plantar Fascia | ~2 min | Short Foot, Toe Yoga, Ball Roll |
| Ankle Mobility | ~3 min | Ankle CARs, WBLT Stretch, Calf Raises |
| Hip Stability | ~4 min | Clamshells, Glute Bridges, Hip CARs |
| Shoulder Rehab | ~5 min | Doorframe ER, Towel Crush, Side-Lying Wiper |
| Core Activation | ~4 min | Bird-Dog, Dead Bug, Breathing |

### Form Guide Structure

```json
{
  "short_foot_exercise": {
    "name": "Short Foot Exercise",
    "setup": "Stand barefoot, weight evenly distributed.",
    "cues": [
      "Lift your arch by pulling toes toward heel",
      "Don't curl your toes",
      "Hold 5 seconds"
    ],
    "common_mistakes": [
      "Curling toes instead of lifting arch",
      "Holding breath"
    ]
  }
}
```

---

## Voice Announcement & STOP Button Fixes (January 21, 2026)

### Status: ✅ IMPLEMENTED

Two UX improvements for the interactive morning routine in Command Centre.

### Voice Announcement on READY? Screen

**Problem:** When transitioning between exercises, the READY? screen appeared but there was silence - users on the mat or away from screen couldn't hear what's next.

**Solution:** Modified auto-advance flow in `bridge_file_server.py`:

| Phase | UI State | Voice | Duration |
|-------|----------|-------|----------|
| 'completed' | "COMPLETE" | Chime only | 2 seconds |
| 'pending' | "READY?" | **"Next: {exercise}. {setup tip}."** | 4 seconds |
| timer | Exercise name | "Go. {duration} seconds." | Exercise duration |

**Key Change:** State advances FIRST via `_advance_routine_exercise_silent()`, THEN voice announces - ensuring UI and voice are synchronized.

### STOP Button Behavior Fix

**Problem:** Pressing STOP killed the entire server instead of returning to idle/main menu state.

**Root Cause:** `_handle_routine_stop()` wasn't calling `_clear_timer_from_session_status()`, so timer data persisted in `session_status.json` and UI continued showing timer.

**Solution:** Updated `_handle_routine_stop()` to:
1. Reset all state variables (`_routine_exercise_complete`, `_routine_timer_duration`, etc.)
2. Reset indices (`_routine_section_idx`, `_routine_exercise_idx`)
3. Call `_clear_timer_from_session_status()` to clear timer from UI
4. Confirm via TTS "Routine stopped..."

**Result:** STOP now exits current routine, UI shows idle state, server continues running for new commands.

### Files Modified

| File | Changes |
|------|---------|
| `atlas/voice/bridge_file_server.py` | Voice announcement in auto-advance, STOP handler fix, timer status clearing |
| `scripts/atlas_launcher.py` | UI countdown display during 'pending' phase |

### Verification

| Check | Result |
|-------|--------|
| Voice announces on READY? screen | ✅ Synchronized with UI |
| STOP exits routine | ✅ State fully reset |
| Server continues after STOP | ✅ Accepts new commands |
| UI shows idle after STOP | ✅ Timer card hidden |
| Can start new routine after STOP | ✅ All state reset |

---

## BridgeFileServer Modular Refactoring (January 21, 2026)

### Status: ✅ IMPLEMENTED

Major refactoring of `bridge_file_server.py` to improve maintainability, testability, and code organization.

### Problem

The voice bridge had grown to 5820 lines with:
- 52 scattered instance variables
- 936-line `process_audio()` method with 30+ if/elif branches
- 325-line `_get_timer_status()` method
- 400+ lines of hardcoded pattern constants

### Solution: Modular Extraction

| New Module | Lines | Purpose |
|------------|-------|---------|
| `atlas/voice/state_models.py` | 173 | WorkoutState, RoutineState, AssessmentState, TimerState dataclasses |
| `atlas/voice/timer_builders.py` | 547 | Timer dict building with TimerContext |
| `atlas/voice/intent_dispatcher.py` | 1123 | IntentDispatcher with priority-ordered handlers |
| `config/voice/intent_patterns.json` | ~500 | Externalized patterns (hot-configurable) |

### Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| bridge_file_server.py | 5820 lines | 4767 lines | -18% |
| process_audio() | 936 lines | 148 lines | -84% |
| _get_timer_status() | 325 lines | 66 lines | -80% |
| Instance variables | 52 scattered | 4 dataclasses | Organized |

### Key Changes

1. **State Classes**: Variables like `self._workout_active` → `self.workout.active`
2. **Timer Builders**: `get_timer_status(ctx)` with 8 focused builder functions
3. **Intent Dispatcher**: `IntentDispatcher(self).dispatch(text)` replaces if/elif chain
4. **Pattern Config**: `get_patterns("general", "meal_triggers")` for hot-reloadable patterns

### Files Modified

| File | Changes |
|------|---------|
| `atlas/voice/bridge_file_server.py` | State class usage, timer builder integration, dispatcher wiring |
| `atlas/voice/state_models.py` | NEW - 4 dataclasses with reset() methods |
| `atlas/voice/timer_builders.py` | NEW - TimerContext + 8 builder functions |
| `atlas/voice/intent_dispatcher.py` | NEW - IntentDispatcher class |
| `config/voice/intent_patterns.json` | NEW - All patterns externalized |

### Verification

| Check | Result |
|-------|--------|
| All modules compile | ✅ Passed |
| State class reset() | ✅ Works |
| Timer builders | ✅ Return correct dicts |
| Intent dispatcher | ✅ Routes correctly |
| Full import test | ✅ BridgeFileServer imports |

---

## What's NOT Implemented Yet

| Feature | Priority | Notes |
|---------|----------|-------|
| Tool use (timers, etc.) | P2 | Commands acknowledged but not executed |
| MCP server | P2 | Expose memory/Blueprint tools to Claude Desktop |
| Voice ↔ Memory integration | P2 | Inject memories into voice pipeline context |
| Wake word ("Hey ATLAS") | P3 | Currently push-to-talk |

---

## Known Limitations

| Limitation | Notes |
|------------|-------|
| No tool use | Timer/alarm requests acknowledged but not executed |
| Memory ✅ | IMPLEMENTED - `atlas.memory` module with hybrid search |
| Content filtering | May block certain health topics via API |
| Router confidence | Sometimes stuck at 0.50 - embeddings may not be loading |

---

## Open Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Router always 0.50 | Medium | Embeddings may not be loading. Verify sentence-transformers. |
| Cost shows $0.0000 | Low | HAIKU calls should have cost. Tracking may be misconfigured. |
| Persona breaks | Medium | "I am Claude" slips through. May need context injection. |
| No repo awareness | Medium | ATLAS doesn't know its codebase location. |

**Status:** Minor issues. Voice works end-to-end. Note for Phase 2+.

---

## Testing Commands

```bash
# Test router classification
python -c "
from atlas.llm import get_router
router = get_router()
for q in ['what time is it', 'plan my workout', 'medical advice']:
    r = router.classify(q)
    print(f'{q} -> {r.tier.value} ({r.confidence:.2f})')
"

# Test cost tracker
python -c "
from atlas.llm import get_cost_tracker
t = get_cost_tracker()
s = t.get_budget_status()
print(f'Monthly: \${s.monthly_spend:.4f} / \${s.monthly_limit}')
"

# Test memory system
python scripts/test_memory.py

# Test memory at scale (100K records)
python scripts/test_memory.py --scale

# Test embeddings
python -c "
from atlas.memory import get_embedder
embedder = get_embedder()
result = embedder.embed('morning workout')
print(f'Latency: {result.duration_ms:.1f}ms, Dims: {len(result.embedding)}')
"

# Run latency benchmark
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python scripts/voice_latency_benchmark.py
```

---

## Research Documents

| Document | Content |
|----------|---------|
| `docs/research/R29.*` | LLM routing strategies |
| `docs/research/R21.*` | Lethal Gentleman persona |
| `docs/research/R11.*` | Voice latency optimization |
| `docs/TASK_JARVIS_FEATURE_ADOPTION.md` | Feature comparison with JARVIS |

---

## Quick Start for New Agent

1. **Understand architecture decisions:** Read `docs/DECISIONS.md`
2. **Understand the routing:** Read `atlas/llm/router.py`
3. **Understand the voice pipeline:** Read `atlas/voice/pipeline.py`
4. **Run tests:** Use commands in "Testing Commands" section
5. **Check budget:** `get_cost_tracker().get_budget_status()`
6. **Config options:** See `VoicePipelineConfig` in pipeline.py
7. **Windows launcher:** Run from Windows with `python scripts/atlas_launcher.py`
