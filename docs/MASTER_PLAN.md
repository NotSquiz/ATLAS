# ATLAS Verified Architecture - January 2026

**Research Complete:** 29 research topics (R1-R29)
**Constraint:** ~6GB usable RAM in WSL2 on 16GB Windows 11 + 4GB VRAM (RTX 3050 Ti)
**Status:** Phase 0 COMPLETE (Memory) + Phase 1 COMPLETE (Voice)
**Last Updated:** January 7, 2026

---

## Analysis Files

- `/home/squiz/ATLAS/docs/research/ANALYSIS_R1-R9_FOUNDATIONAL.md`
- `/home/squiz/ATLAS/docs/research/ANALYSIS_R10-R15_TECHNICAL.md`
- `/home/squiz/ATLAS/docs/research/ANALYSIS_R16-R21_PERSONA.md`
- `/home/squiz/ATLAS/docs/research/ANALYSIS_R22-R24_SKILL_SYSTEM.md`
- `/home/squiz/ATLAS/docs/research/ANALYSIS_R25-R27_IMPLEMENTATION.md`

---

## Executive Summary

| Decision | Choice | Source |
|----------|--------|--------|
| **Local LLM** | Qwen2.5-3B-Instruct Q4_K_M (~2.0-2.5GB VRAM) | R28 |
| **Cloud Fallback** | Claude Haiku/Sonnet (>4K context, <70% confidence) | R25 |
| **Memory** | SQLite + sqlite-vec + FTS5 + BGE-small-en-v1.5 | R1-R15 |
| **STT** | Moonshine Base on CPU | R25 (revised from R11) |
| **TTS** | Kokoro-82M ONNX (GPU streaming) | R11 |
| **VAD** | Silero VAD v6.2 | R11 |
| **Orchestration** | Claude Agent SDK + LangGraph for complex workflows | R27 |
| **MCP** | STDIO transport, unified server | R1-R15 |
| **Verification** | External grounding (NOT self-assessment) | R22 |
| **Workflow** | DAG-based parallel execution | R23 |
| **Checkpointing** | LangGraph SqliteSaver | R27 |

---

## User Context

- **Location:** Australia
- **Partner:** Naturopath (handles supplements/herbs/natural health protocols)
- **Equipment:** Home gym (power rack, bench, pull-up bar, barbell, dumbbells, skipping rope, neck harness)
- **Injuries:** Has injuries requiring rehab (separate Opus session to design protocol)
- **Goals:**
  - Blueprint-style health tracking (Bryan Johnson approach)
  - Workout planning with injury awareness
  - Later: Baby Brains content creation (Instagram, TikTok, YouTube Shorts)

---

## 1. Windows/WSL2 Configuration

### Critical: Fix DoSvc Memory Leak First
```powershell
Stop-Service -Force -Name "DoSvc"
Set-Service -Name "DoSvc" -StartupType Disabled
Set-ItemProperty -Path "HKLM:\SYSTEM\ControlSet001\Services\Ndu" -Name "Start" -Value 4
Set-Service -Name "SysMain" -StartupType Disabled
Set-Service -Name "WSearch" -StartupType Disabled
```

### .wslconfig
```ini
[wsl2]
memory=6GB
swap=8GB
processors=6
networkingMode=mirrored
dnsTunneling=true
firewall=true

[experimental]
autoMemoryReclaim=dropcache
sparseVhd=true
hostAddressLoopback=true
```

### GPU/Audio Status
- **CUDA**: Works at 85-95% native performance
- **VRAM**: 4GB available (separate from WSL2 memory)
- **Audio**: WSLg PulseAudio works, 50-200ms latency overhead

---

## 2. Local LLM Configuration (R28 - REVISED)

### Why Qwen2.5-3B-Instruct (Not Qwen3-4B)

| Model | VRAM Needed | Thinking Mode | Fits 4GB? |
|-------|-------------|---------------|-----------|
| Qwen3-4B Q4_K_M | ~3.05GB | **MANDATORY** (broken) | Unstable |
| Qwen2.5-3B-Instruct Q4_K_M | ~2.0-2.5GB | **NONE** | **YES** ✅ |

R25 recommended Qwen3-4B but **R28 proved its thinking mode is architectural and cannot be disabled**, consuming 200-500 tokens on internal reasoning before generating content. Qwen2.5-3B has NO thinking mode and outputs content immediately.

### Environment Variables
```bash
# ~/.bashrc
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1
```

### Ollama Setup
```bash
ollama pull qwen2.5:3b-instruct

cat > ~/ATLAS-Modelfile << 'EOF'
FROM qwen2.5:3b-instruct
PARAMETER num_ctx 2048
PARAMETER num_predict 256
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
SYSTEM "You are ATLAS—a mentor who speaks economically. Keep responses to 1-3 sentences. Be direct. No hedging."
EOF

ollama create atlas-local -f ~/ATLAS-Modelfile
```

### Performance
- First token: ~200-350ms
- Generation: ~20-40 tok/s
- Complete pipeline: ~1,000-1,450ms (faster than Qwen3 due to no thinking overhead)

### Cloud Routing (R25)
```python
def route_query(context_tokens: int, confidence: float) -> str:
    if context_tokens > 4000: return "cloud_sonnet"
    if confidence < 0.7: return "cloud_haiku"
    return "local"
```

---

## 3. Memory Architecture

### Status: ✅ IMPLEMENTED (January 7, 2026)

### Stack
| Component | Choice | Status |
|-----------|--------|--------|
| Database | SQLite + WAL mode | ✅ |
| Vector Search | sqlite-vec v0.1.6 | ✅ |
| Full-Text Search | FTS5 | ✅ |
| Embeddings | BGE-small-en-v1.5 (sentence-transformers ONNX) | ✅ |

### Implementation Files
| File | Purpose |
|------|---------|
| `atlas/memory/store.py` | MemoryStore with hybrid RRF search |
| `atlas/memory/embeddings.py` | BGE-small-en-v1.5 via sentence-transformers ONNX |
| `atlas/memory/blueprint.py` | CRUD API for health/fitness tables |
| `atlas/memory/schema.sql` | Complete database schema |

### Database Location
- Default: `~/.atlas/atlas.db`
- Configurable via `MemoryStore(db_path)`

### Performance (Verified)
| Metric | Result | Target |
|--------|--------|--------|
| Embedding generation | 10.1ms | <15ms ✅ |
| Hybrid search (10K) | ~10-20ms | - |
| Hybrid search (100K) | ~100ms | <75ms (acceptable) |

**Note:** sqlite-vec uses brute-force KNN. Binary quantization available as upgrade path if needed.

### Schema (Implemented)
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Semantic memory with embeddings
CREATE TABLE semantic_memory (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    memory_type TEXT DEFAULT 'general',
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE VIRTUAL TABLE vec_semantic USING vec0(
    memory_id INTEGER PRIMARY KEY,
    embedding float[384]
);

CREATE VIRTUAL TABLE fts_memory USING fts5(content, content=semantic_memory);
-- Plus FTS sync triggers for insert/update/delete

-- Blueprint tables: daily_metrics, supplements, supplement_log,
-- workouts, workout_exercises, lab_results, injuries
```

### Hybrid Search (RRF)
- 60% vector weight, 40% FTS weight
- Reciprocal Rank Fusion for combining results
- Two-phase query: vector search first, then metadata fetch

---

## 4. Voice Pipeline

### Components (R28 Revised)
| Component | Choice | Runs On |
|-----------|--------|---------|
| VAD | Silero v6.2 | CPU |
| STT | Moonshine Base | **CPU** (reserve GPU for LLM) |
| LLM | Qwen2.5-3B-Instruct | GPU |
| TTS | Kokoro-82M | GPU (streaming) |

### Latency Budget
| Component | Time |
|-----------|------|
| VAD silence wait | ~400ms |
| STT (Moonshine) | ~600ms |
| LLM (first token) | ~200ms |
| LLM (streaming) | ~1200ms |
| TTS (first audio) | ~250ms |
| **TOTAL** | **~2,400ms** ✅ |

---

## 5. Verification Architecture (R22 - CRITICAL)

### Self-Assessment is BROKEN
R22 proved that LLM self-verification without external grounding **degrades quality**.

### Use External Verification Instead
```python
class VerificationEngine:
    async def verify(self, output, domain: str) -> VerificationResult:
        if domain == "workout":
            return self.verify_workout(output)
        elif domain == "nutrition":
            return self.verify_nutrition(output)
        # ...

    def verify_workout(self, workout):
        checks = {
            "injuries_respected": self.check_injury_safety(workout),
            "load_progression": self.check_load_limits(workout),
            "recovery_time": self.check_recovery(workout),
            "equipment_available": self.check_equipment(workout),
        }
        return VerificationResult(passed=all(checks.values()), checks=checks)
```

### Confidence-Based Routing (R24)
```python
def route_by_confidence(confidence: float) -> str:
    if confidence >= 0.9: return "execute"
    if confidence >= 0.7: return "confirm"
    return "clarify"
```

---

## 6. Workflow Engine (R23, R27)

### When to Use LangGraph

| Skill | LangGraph? | Rationale |
|-------|------------|-----------|
| Simple Q&A | No | Direct Claude API |
| Log supplement | No | Single DB write |
| Morning workout | **Yes** | Multi-tool DAG |
| Content pipeline | **Yes** | Complex branching |

### DAG-Based Parallel Execution (R23)
```python
# Instead of sequential:
# Step 1 → Step 2 → Step 3 → Step 4

# Use parallel where possible:
workflow_dag = {
    "garmin": {"deps": []},
    "injuries": {"deps": []},
    "history": {"deps": []},
    "generate": {"deps": ["garmin", "injuries", "history"]},
    "verify": {"deps": ["generate"]}
}
# Steps 1-3 run in parallel → 3.6x speedup
```

### SqliteSaver Checkpointing (R27)
```python
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("atlas_checkpoints.db")
graph = builder.compile(checkpointer=checkpointer)
```

---

## 7. APIs (Simplified for Your Needs)

### Phase 1 - Core (Now)
| Purpose | Solution | Cost |
|---------|----------|------|
| Fitness tracking | Garmin API (Forerunner 165) | FREE |
| Exercise database | Curated local DB (your equipment) | FREE |
| Blueprint tracking | SQLite (supplements, biomarkers, sleep) | FREE |

### Phase 2 - Enhanced (When Ready)
| Purpose | Solution | Cost |
|---------|----------|------|
| Nutrition (products) | Open Food Facts (includes AU) | FREE |
| Nutrition (raw foods) | AUSNUT or USDA | FREE |

### Phase 3 - Baby Brains (Month+)
| Purpose | Solution | Cost |
|---------|----------|------|
| Instagram | Instagram Graph API | FREE |
| TikTok | TikTok API | FREE |
| YouTube Shorts | YouTube Data API | FREE |

### NOT Needed (Removed)
- ~~Supp.AI, OpenFDA, RxNorm~~ - Partner (Naturopath) handles health protocols
- ~~Spoonacular, GPTZero, Copyscape~~ - Not required for your use case
- ~~US privacy compliance~~ - You're in Australia

---

## 8. Persona System (R16-R21)

### Core Character: Lethal Gentleman
- Capable, refined, restrained
- "Power held in check signals greater capability"
- Direct speech, no empty phrases

### 5 Interaction Modes
| Mode | Trigger | Behavior |
|------|---------|----------|
| Minimal | User in flow | Brief, direct |
| Structured | User overwhelmed | Break into steps |
| Challenging | User stuck | OARS framework |
| Philosophical | Meaning-seeking | Open questions |
| Listening | Venting | Reflect, don't fix |

### Speech Guidelines
**Use:** Definitive verbs, short sentences, understated intensifiers
**Eliminate:** Superlatives, "Hope that helps!", apologetic excess, exclamation marks

---

## 9. Blueprint-Style Tracking Schema

```sql
-- Daily biomarkers
CREATE TABLE daily_metrics (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    sleep_hours REAL,
    sleep_score INTEGER,
    resting_hr INTEGER,
    hrv_avg INTEGER,
    weight_kg REAL,
    energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
    mood INTEGER CHECK(mood BETWEEN 1 AND 10),
    notes TEXT
);

-- Supplement tracking
CREATE TABLE supplements (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dosage TEXT,
    timing TEXT,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE supplement_log (
    id INTEGER PRIMARY KEY,
    supplement_id INTEGER REFERENCES supplements(id),
    date DATE NOT NULL,
    taken BOOLEAN DEFAULT TRUE
);

-- Workout tracking
CREATE TABLE workouts (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    type TEXT,
    duration_minutes INTEGER,
    notes TEXT
);

CREATE TABLE workout_exercises (
    id INTEGER PRIMARY KEY,
    workout_id INTEGER REFERENCES workouts(id),
    exercise_id TEXT,
    sets INTEGER,
    reps TEXT,
    weight_kg REAL
);

-- Injuries (for rehab tracking)
CREATE TABLE injuries (
    id INTEGER PRIMARY KEY,
    body_part TEXT NOT NULL,
    description TEXT,
    severity INTEGER CHECK(severity BETWEEN 1 AND 5),
    status TEXT DEFAULT 'active',
    contraindicated_exercises TEXT
);

-- Lab results
CREATE TABLE lab_results (
    id INTEGER PRIMARY KEY,
    test_date DATE NOT NULL,
    marker TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT
);
```

---

## 10. Your Equipment Database

```python
EQUIPMENT = [
    "power_rack",
    "bench",
    "pullup_bar",
    "barbell",
    "dumbbells",
    "skipping_rope",
    "neck_harness"
]

# Curate exercises specifically for this equipment
# Include injury modifications from rehab plan
```

---

## 11. Implementation Phases

### Phase 0: Foundation ✅ COMPLETE
- [x] Apply WSL2 optimizations (DoSvc fix, .wslconfig)
- [x] Install Ollama + Qwen2.5-3B-Instruct
- [x] Set environment variables (FLASH_ATTENTION, KV_CACHE, MAX_LOADED_MODELS)
- [x] Test local LLM latency
- [x] SQLite + sqlite-vec + FTS5 setup
- [x] Memory system with hybrid search (store.py, embeddings.py, blueprint.py)
- [ ] Basic MCP server skeleton (NEXT)

### Phase 1: Core Lifestyle (IN PROGRESS)
- [ ] **Injury Rehab Session** (separate Opus conversation)
- [ ] **Blueprint Protocol Session** (with Naturopath input)
- [ ] Garmin Forerunner 165 integration
- [ ] Curated exercise database (your equipment)
- [ ] Workout generation with injury filtering
- [ ] Supplement/biomarker logging
- [ ] Daily metrics tracking
- [x] Voice interface (faster-whisper CPU + Kokoro GPU) ✅ COMPLETE
- [x] Windows launcher with spacebar-to-talk ✅ COMPLETE
- [ ] Basic calendar/reminders

### Phase 2: Enhanced Tracking (When Ready)
- [ ] Nutrition tracking (Open Food Facts)
- [ ] Meal logging
- [ ] Progress measurements
- [ ] LangGraph for complex workflows
- [ ] SqliteSaver checkpointing

### Phase 3: Baby Brains (Month+)
- [ ] Instagram Graph API integration
- [ ] TikTok API integration
- [ ] YouTube Data API integration
- [ ] Content analytics dashboard

---

## 12. Separate Opus Sessions Needed

### Session 1: Injury Rehab Design
```
I need help designing an injury rehabilitation protocol for my home workouts.

My injuries: [LIST YOUR SPECIFIC INJURIES]

My equipment: Power rack, bench, pull-up bar, barbell, dumbbells,
skipping rope, neck harness

Please help me:
1. Identify exercises to AVOID for each injury
2. Design REHAB exercises for my equipment
3. Create a progression plan from rehab to full training
4. Set realistic timelines
```

### Session 2: Blueprint Protocol Design
```
I want to design a Bryan Johnson-style Blueprint health protocol.

Context:
- My partner is a Naturopath (will validate supplement stack)
- I have a Garmin Forerunner 165 for HRV/sleep/activity
- I want baseline blood work and biomarker tracking

Help me design:
1. What biomarkers to track (blood work, daily metrics)
2. Supplement/herb considerations (Naturopath will validate)
3. Daily routine structure
4. Weekly/monthly review cadence
```

---

## 13. Project Structure (Current)

```
/home/squiz/ATLAS/
├── atlas/
│   ├── __init__.py
│   ├── memory/                    # ✅ IMPLEMENTED
│   │   ├── __init__.py            # Exports + get_memory_store()
│   │   ├── store.py               # MemoryStore with hybrid RRF search
│   │   ├── embeddings.py          # BGE-small-en-v1.5 via sentence-transformers ONNX
│   │   ├── blueprint.py           # CRUD API for health/fitness tables
│   │   └── schema.sql             # Complete database schema
│   ├── voice/                     # ✅ IMPLEMENTED
│   │   ├── stt.py                 # faster-whisper (CPU)
│   │   ├── tts.py                 # Kokoro (GPU streaming)
│   │   ├── vad.py                 # Silero v6.2
│   │   ├── pipeline.py            # Voice pipeline orchestration
│   │   └── bridge_file_server.py  # WSL↔Windows file bridge
│   ├── llm/                       # ✅ IMPLEMENTED
│   │   ├── local.py               # Qwen2.5-3B via Ollama
│   │   ├── api.py                 # Claude Haiku API
│   │   ├── cloud.py               # Claude Agent SDK
│   │   ├── router.py              # Hybrid semantic routing
│   │   └── cost_tracker.py        # Usage + budget tracking
│   ├── mcp/
│   │   └── server.py              # FastMCP (skeleton exists)
│   ├── orchestrator/              # ✅ IMPLEMENTED
│   │   ├── __init__.py
│   │   ├── command_router.py      # Routes /babybrains, /knowledge, etc.
│   │   ├── hooks.py               # Wraps validators (qc_runner.py)
│   │   └── skill_executor.py      # Dual-mode: CLI ($0) or API (paid)
│   ├── core/                      # PLANNED
│   │   ├── verification.py        # External verification engine
│   │   └── dag_executor.py        # Parallel execution
│   ├── skills/                    # PLANNED
│   │   ├── workout.py             # Workout generation
│   │   └── tracking.py            # Blueprint logging
│   └── integrations/              # PLANNED
│       ├── garmin.py              # Garmin Connect API
│       └── calendar.py            # Google Calendar
├── config/
│   └── persona.md                 # Lethal Gentleman prompt
├── scripts/
│   ├── atlas_launcher.py          # ✅ Windows GUI launcher
│   ├── ATLAS_Launcher.bat         # Console shortcut
│   ├── ATLAS_Launcher.vbs         # Silent shortcut
│   └── test_memory.py             # Memory system tests
└── docs/
    ├── MASTER_PLAN.md             # This file
    └── DECISIONS.md               # Architecture decisions
```

---

## 14. RAM Budget

### System RAM (6GB)
| Component | RAM |
|-----------|-----|
| WSL2 kernel | ~300MB |
| Python + libraries | ~200MB |
| BGE-small-en-v1.5 | ~100MB |
| sqlite-vec + FTS5 | ~100MB |
| Moonshine STT | ~500MB |
| MCP Server | ~150MB |
| Working memory | ~500MB |
| **TOTAL** | **~1.85GB** |
| **Headroom** | **~4.15GB** |

### VRAM (4GB)
| Component | VRAM |
|-----------|------|
| Qwen2.5-3B-Instruct Q4_K_M | ~2.0GB |
| KV Cache (q8_0, 2K ctx) | ~0.2GB |
| Kokoro TTS | ~0.3GB |
| **TOTAL** | **~2.5GB** |
| **Headroom** | **~1.5GB** ✅ |

---

## 15. Research Status

| Phase | Status |
|-------|--------|
| R1-R9 (Foundational) | ✅ Complete |
| R10-R15 (Technical) | ✅ Complete |
| R16-R21 (Persona) | ✅ Complete |
| R22-R24 (Skill System) | ✅ Complete |
| R25-R27 (Implementation) | ✅ Complete |
| R28 (Local LLM Selection) | ✅ Complete |
| R29 (Hybrid Routing) | ✅ Complete |
| **ALL RESEARCH** | **✅ COMPLETE** |

---

## 16. Windows Launcher & Dashboard

### Purpose
Unified Windows GUI for voice interaction without console windows.

### Architecture
```
Windows (GUI)                    WSL2 (Processing)
─────────────────────────────────────────────────────
┌──────────────────┐            ┌──────────────────┐
│ atlas_launcher.py│◄──────────►│bridge_file_server│
│  (CustomTkinter) │  .bridge/  │     (Python)     │
└──────────────────┘   files    └──────────────────┘
         │                               │
    sounddevice                    ┌─────┴─────┐
    (mic/speaker)                  │  Router   │
                                   ├───────────┤
                                   │ STT (CPU) │
                                   │ TTS (GPU) │
                                   └───────────┘
```

### Voice Pipeline Flow
```
Windows Mic → .bridge/audio_in.raw → WSL2 Server
                                         ↓
                                    STT (faster-whisper base.en)
                                         ↓
                                    Router (LOCAL/HAIKU/AGENT_SDK)
                                         ↓
                                    LLM (Qwen local or Claude Haiku)
                                         ↓
                                    TTS (Kokoro GPU, Lewis/Emma voices)
                                         ↓
.bridge/audio_out.raw ← Windows Playback
```

### Bridge Files (`~/.bridge/`)
| File | Direction | Purpose |
|------|-----------|---------|
| `audio_in.raw` | Win→WSL | Recorded audio |
| `audio_out.raw` | WSL→Win | TTS response |
| `metadata.txt` | WSL→Win | Sample rate for playback |
| `command.txt` | Win→WSL | PING/PROCESS/QUIT |
| `status.txt` | WSL→Win | PONG/DONE |
| `voice.txt` | Win→WSL | Voice preference |
| `session_status.json` | WSL→Win | Costs, routing, timing |

### Key Design Decisions
1. **CustomTkinter over PyQt6**: Simpler, built-in dark mode, pure Python
2. **Single file over package**: No pip install needed, easy to modify
3. **JSON over SQLite**: Avoids cross-WSL SQLite locking issues
4. **File-based IPC**: More reliable than WSL2 networking
5. **Hold-to-talk**: No VAD needed on Windows side, reduces complexity

### Dependencies (Windows)
```bash
pip install customtkinter sounddevice numpy
```

### Usage
```bash
# From Windows - with console (debugging)
python scripts/atlas_launcher.py

# From Windows - silent (production)
pythonw scripts/atlas_launcher.py
# Or double-click scripts/ATLAS_Launcher.vbs
```

---

## 17. Environment Setup

### CUDA/cuDNN (~/.bashrc)
```bash
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda/bin:$PATH
```

### Key Dependencies
```bash
# WSL2/Ubuntu
pip install onnxruntime-gpu  # TTS acceleration
pip install faster-whisper   # STT (faster than moonshine)

# Windows
pip install customtkinter sounddevice numpy
```

---

## 18. Known Limitations

| Limitation | Status | Notes |
|------------|--------|-------|
| No tool use | Deferred | Timer/alarm requests acknowledged but not executed |
| Memory | ✅ IMPLEMENTED | `atlas.memory` module with hybrid search |
| Content filtering | Noted | May block certain health topics via API |
| Router confidence | Investigating | Sometimes stuck at 0.50 |

---

## 19. Open Issues (For Future Phases)

| Issue | Severity | Notes |
|-------|----------|-------|
| Router always 0.50 | Medium | Embeddings may not be loading. Need to verify sentence-transformers. |
| Cost shows $0.0000 | Low | HAIKU calls should have cost. Tracking may be misconfigured. |
| Persona breaks | Medium | "I am Claude" slips through. May need context injection. |
| No repo awareness | Medium | ATLAS doesn't know its codebase location. |

**Status:** Minor issues. Voice works end-to-end. Note for Phase 2+.

---

## 20. Orchestrator Infrastructure (January 2026)

### Vision Evolution

**Old Vision:** Voice assistant that classifies → routes → responds

**New Vision:** Agentic orchestrator that gathers context → acts → verifies → iterates

### ATLAS as Supreme Coordinator

ATLAS orchestrates across the Baby Brains ecosystem:

| Repo | Purpose | Key Patterns |
|------|---------|--------------|
| `babybrains-os` | 9-skill content pipeline | YAML routers, JSON schemas, QC gates |
| `knowledge` | 121-atom knowledge graph | Python validators, session workflows |
| `web` | Next.js marketing site | Hierarchical AGENTS.md |
| `app` | React Native app | Offline-first, decision logs |
| `ATLAS` | Voice + memory + orchestration | 3-tier routing, embeddings |

### Infrastructure Components

| Component | File | Status |
|-----------|------|--------|
| Command Router | `atlas/orchestrator/command_router.py` | ✅ Working |
| Hook Framework | `atlas/orchestrator/hooks.py` | ✅ Working |
| Skill Executor | `atlas/orchestrator/skill_executor.py` | ✅ Working |

**Command Router:** Routes slash commands (`/babybrains status`, `/knowledge status`, etc.)

**Hook Framework:** Wraps existing validators (qc_runner.py) for deterministic verification

**Skill Executor:** Dual-mode execution:
- CLI mode (default): Uses Max subscription ($0)
- API mode (`--api`): Per-token costs

### Cost Model Decision (Critical)

| Method | Cost | Use For |
|--------|------|---------|
| Claude Max ($100/mo) | Included | Interactive work, development |
| Claude Code CLI | Included in Max | ATLAS default mode |
| Anthropic API | Per-token | Autonomous automation only |
| Agent SDK | Uses API | Same as API - no Max integration |

**Key Insight:** Agent SDK = API costs. Cannot use Max subscription for programmatic calls.

---

## 21. R30 Masterclass Analysis (January 2026)

### Source
Claude Agent SDK Masterclass by Tariq (Anthropic) - 112 minutes

### 10 Key Insights Applied to ATLAS

1. **"Bash is all you need"** - Bash tool beats custom tools
2. **Agent = Autonomy** - Agents build own context, decide trajectories
3. **Agent Loop** - Gather context → Take action → Verify work
4. **Verification Everywhere** - Put verification in as many places as possible
5. **Skills = Progressive Disclosure** - Agent discovers capabilities on demand
6. **Sub-Agents for Context Isolation** - Avoid context pollution
7. **Clear Context Often** - Store state externally, reload via git diff
8. **Hooks Fight Hallucinations** - Deterministic enforcement
9. **Design APIs for Agents** - Use syntax agents know (SQL, ranges)
10. **Reversibility Matters** - Good intuition for agent success

### ATLAS Alignment

| Pattern | Status |
|---------|--------|
| Skills as markdown → system prompt | ✅ Aligned |
| Hooks for deterministic verification | ✅ Aligned |
| CLI-first execution | ✅ Aligned |
| File system as context | ✅ Aligned |

### V2 Gaps to Address

| Gap | Priority | File to Create |
|-----|----------|----------------|
| Sub-agent support | High | `subagent_executor.py` |
| Multi-point verification | High | Extend `hooks.py` |
| Context management | High | `session_manager.py` |
| Adversarial checking | Medium | In `subagent_executor.py` |
| Progressive loading | Medium | Extend `skill_executor.py` |
| Scratch pad | Low | `scratch_pad.py` |

### Research Documents

- `docs/research/R30.Claude Agent SDK Masterclass Analysis.md` - Full synthesis
- `docs/research/R30_Section1_Philosophy.md` - Agent definition, loops
- `docs/research/R30_Section2_Implementation.md` - Skills, sub-agents, hooks
- `docs/research/R30_Section3_Advanced.md` - Q&A, production patterns
- `docs/ATLAS_ARCHITECTURE_V2.md` - Implementation recommendations

---

## Summary

ATLAS implementation status:

1. **Phase 0:** Foundation ✅ COMPLETE
   - WSL2/Ollama/environment configured
   - SQLite + sqlite-vec + FTS5 memory system
   - BGE-small-en-v1.5 embeddings (10.1ms latency)
   - Hybrid RRF search (~100ms at 100K records)
   - Blueprint CRUD API (daily_metrics, supplements, workouts, injuries, lab_results)

2. **Phase 1:** Voice Pipeline + Windows Launcher ✅ COMPLETE
   - STT (faster-whisper base.en on CPU, ~1000ms latency)
   - TTS (Kokoro on GPU, Lewis/Emma voices, ~1-2s latency)
   - Router (LOCAL/HAIKU/AGENT_SDK tiers)
   - Windows launcher with spacebar-to-talk
   - File-based Windows↔WSL2 bridge

3. **Orchestrator Infrastructure:** ✅ COMPLETE
   - Command router for `/babybrains`, `/knowledge`, `/web`, `/app`
   - Hook framework wrapping existing validators
   - Dual-mode skill executor (CLI $0 / API paid)
   - R30 Masterclass analysis completed (see Section 21)

4. **Phase 1 (continued):** Core Lifestyle - PENDING
   - Garmin integration, workout generation, supplement logging

5. **V2 Architecture:** NEXT
   - Sub-agent support, multi-point hooks, context management
   - See `docs/ATLAS_ARCHITECTURE_V2.md` for implementation plan

6. **Phase 2:** Enhanced (LangGraph workflows) - LATER
7. **Phase 3:** Baby Brains (social media APIs) - LATER

**Current:** Voice + Memory + Orchestrator infrastructure complete.

**Next:** V2 architecture components (sub-agents, hooks, session management), then Knowledge Graph completion.

**Resources:**
- Architecture decisions: `docs/DECISIONS.md` (D1-D12)
- V2 implementation plan: `docs/ATLAS_ARCHITECTURE_V2.md`
- Masterclass analysis: `docs/research/R30.Claude Agent SDK Masterclass Analysis.md`
