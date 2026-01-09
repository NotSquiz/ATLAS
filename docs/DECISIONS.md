# ATLAS Architecture Decisions Log

Decisions are logged chronologically. Future agents should read this to understand why choices were made.

**Last Updated:** January 9, 2026

---

## D1: CustomTkinter for Windows Launcher
**Date:** January 2026
**Context:** Needed Windows GUI for voice bridge

**Options Considered:**
1. PyQt6 - More powerful, but complex, large dependency
2. CustomTkinter - Simple, modern look, pure Python
3. Tkinter - Native but dated appearance

**Decision:** CustomTkinter

**Rationale:**
- Built-in dark mode with `ctk.set_appearance_mode("dark")`
- Modern widget styling without CSS
- No binary dependencies (unlike PyQt)
- ~200KB vs ~40MB for PyQt6
- Sufficient for our needs (buttons, labels, text)

---

## D2: File-Based IPC Over Sockets for WSL Bridge
**Date:** January 2026
**Context:** Windows <-> WSL2 communication

**Options Considered:**
1. TCP sockets via localhost
2. Named pipes
3. File-based via `\\wsl$\Ubuntu` path

**Decision:** File-based IPC

**Rationale:**
- WSL2 networking is unreliable (mirrored mode helps but not perfect)
- `\\wsl$\` path is always accessible when WSL is running
- Simple polling model (100ms) is adequate for voice latency
- No port conflicts or firewall issues
- Easy to debug (inspect files directly)

---

## D3: JSON Status File Over SQLite for Cross-System Data
**Date:** January 2026
**Context:** Sharing session data (costs, routing) between WSL server and Windows GUI

**Options Considered:**
1. SQLite with WAL mode
2. JSON file
3. Memory-mapped file

**Decision:** JSON file (`session_status.json`)

**Rationale:**
- SQLite locking fails across WSL2/Windows boundary
- JSON is human-readable for debugging
- Small data size (< 1KB) - no performance concern
- Python's json module is built-in

---

## D4: Qwen2.5-3B Over Qwen3-4B for Local LLM
**Date:** January 2026 (R28)
**Context:** Local LLM for voice assistant on 4GB VRAM

**Options Considered:**
1. Qwen3-4B Q4_K_M (~3.05GB) - Newer, thinking mode
2. Qwen2.5-3B-Instruct Q4_K_M (~2.0GB) - Older, direct output

**Decision:** Qwen2.5-3B-Instruct

**Rationale:**
- Qwen3-4B's thinking mode is MANDATORY and cannot be disabled
- Thinking mode wastes 200-500 tokens on internal reasoning
- Qwen2.5-3B outputs immediately (critical for voice latency)
- Fits comfortably in 4GB VRAM with headroom for TTS

---

## D5: Three-Tier Routing (LOCAL/HAIKU/AGENT_SDK)
**Date:** January 2026 (R29)
**Context:** Balancing latency, cost, and capability

**Decision:**
- **LOCAL** (Qwen 3B): Commands, timers, greetings (~220ms, free)
- **HAIKU** (Direct API): Advice, explanations (~2800ms, $0.001)
- **AGENT_SDK** (Claude): Complex planning (~7400ms, free via Max Plan)

**Rationale:**
- 40-50% of voice queries are simple -> LOCAL handles fast and free
- API latency from Australia is 5.6x worse than US (~2800ms vs ~500ms)
- Filler phrases ("Let me see...") mask cloud latency
- Budget limits ($10/month) prevent runaway costs

---

## D6: Flexible Router Patterns for Timer Commands
**Date:** January 2026
**Context:** "set a 30 second timer" was routing to HAIKU instead of LOCAL

**Problem:** Original pattern `r"^set\s+(timer|alarm)"` was too strict

**Solution:** Made patterns flexible:
```python
r"(set|start|stop|pause|resume|cancel).*(timer|alarm|reminder)"
r"timer\s+for\s+\d+"
r"\d+\s*(second|minute|hour)s?\s+timer"
```

**Rationale:** Voice input varies - users say "set a 30 second timer" not "set timer 30 seconds"

---

## D7: ATLAS Identity Enforcement
**Date:** January 2026
**Context:** ATLAS was saying "I am Claude, created by Anthropic"

**Solution:** System prompt with strict rules:
```
STRICT RULES (NEVER BREAK):
1. You ARE Atlas. Never say "I am Claude" or mention Anthropic.
2. Maximum 20 words. Count them. Stop at 20.
3. One sentence preferred. Two max.
4. No lists, no markdown, no asterisks.
```

**Rationale:** Voice assistant needs consistent identity and brevity

---

## D8: faster-whisper Over Moonshine for STT
**Date:** January 2026
**Context:** Choosing STT engine for voice pipeline

**Options Considered:**
1. Moonshine - New, designed for CPU
2. faster-whisper - Optimized Whisper with CTranslate2

**Decision:** faster-whisper with base.en model

**Rationale:**
- More stable API than moonshine (which changed between versions)
- base.en provides good balance of speed and accuracy
- Runs well on CPU, leaving GPU for LLM and TTS
- Better community support and documentation

---

## D9: Hold-to-Talk Over Continuous Listening
**Date:** January 2026
**Context:** Voice interaction model for Windows launcher

**Options Considered:**
1. Wake word detection ("Hey ATLAS")
2. Continuous VAD-based listening
3. Push-to-talk (hold SPACEBAR)

**Decision:** Hold SPACEBAR to talk

**Rationale:**
- No wake word model needed (saves complexity and resources)
- No VAD needed on Windows side
- User has full control over when to speak
- Avoids accidental triggers
- Simpler to implement and debug
- Can add wake word later as enhancement

---

## D10: Claude Max vs Agent SDK Cost Model
**Date:** January 2026
**Context:** Needed to understand when API costs apply vs included in Max subscription

**Discovery:**
- Claude Max subscription ($100/mo) covers: Claude.ai, Claude Code CLI
- Agent SDK = API calls = per-token costs (NOT covered by Max)
- Subprocess calls to `claude --print` use Max subscription

**Decision:** Dual-mode architecture

**Cost Model:**
| Method | Cost | Use For |
|--------|------|---------|
| Claude Max ($100/mo) | Included | Interactive work, development |
| Claude Code CLI | Included in Max | ATLAS default mode (subprocess) |
| Anthropic API | Per-token ($$$) | Autonomous automation only |
| Agent SDK | Uses API | Same as API - no Max integration |

**Rationale:**
- Use CLI mode (Max) for development and batch sessions = $0
- Reserve API for true automation (scheduled, unattended)
- Critical discovery: Agent SDK is NOT covered by Max subscription

---

## D11: Dual-Mode Skill Executor
**Date:** January 2026
**Context:** Need both Max-subscription ($0) and API modes for skill execution

**Implementation:**
```python
# atlas/orchestrator/skill_executor.py
class SkillExecutor:
    def __init__(self, use_api: bool = False):
        self.use_api = use_api  # False = CLI mode (uses Max)

    async def execute(self, skill_name: str, input_data: dict):
        if self.use_api:
            # Per-token cost - for automation
            return await self._execute_api(skill_name, input_data)
        else:
            # Uses Max subscription - default
            return await self._execute_cli(skill_name, input_data)
```

**CLI Mode (default):**
- Subprocess call to `claude --print`
- Uses Max subscription ($0)
- Best for development, batch sessions

**API Mode (--api flag):**
- Direct `anthropic.Client()` calls
- Per-token cost
- Best for scheduled automation

**Rationale:**
- Most work should be $0 via CLI mode
- API mode available when true automation needed
- User explicitly opts in to costs with `--api` flag

---

## D12: Orchestrator as Supreme Coordinator
**Date:** January 2026
**Context:** ATLAS scope expanded beyond voice assistant

**Original Vision:** Voice assistant that classifies → routes → responds

**New Vision:** Agentic orchestrator that gathers context → acts → verifies → iterates

**Ecosystem:**
| Repo | Purpose |
|------|---------|
| `babybrains-os` | 9-skill content pipeline |
| `knowledge` | 121-atom knowledge graph |
| `web` | Next.js marketing site |
| `app` | React Native app |
| `ATLAS` | Voice + memory + orchestration |

**Implementation:**
- `command_router.py` - Routes `/babybrains`, `/knowledge`, `/web`, `/app` commands
- `hooks.py` - Wraps existing validators for deterministic verification
- `skill_executor.py` - Loads markdown skills, executes via CLI or API

**Rationale:**
- ATLAS is not just a voice assistant
- It's the coordination layer across Baby Brains ecosystem
- Enables content automation at scale

---

## D13: HookTiming PRE/POST Only (MID Deferred)
**Date:** January 2026
**Context:** Implementing multi-point hook timing for V2

**Options Considered:**
1. PRE/MID/POST timing for all hooks
2. PRE/POST only, defer MID until skill chaining exists

**Decision:** PRE/POST only

**Rationale:**
- MID_EXECUTION requires skill chaining which doesn't exist yet
- YAGNI - no current use case for mid-execution hooks
- Can add MID later without breaking changes

---

## D14: SubAgent via Subprocess (Context Isolation)
**Date:** January 2026
**Context:** How to spawn sub-agents with isolated context

**Options Considered:**
1. In-process Agent SDK calls (shared context)
2. Subprocess to `claude -p` (fresh context)
3. API calls (expensive, no Max coverage)

**Decision:** Subprocess to `claude -p`

**Rationale:**
- Complete context isolation (masterclass recommendation)
- Uses Max subscription ($0 cost)
- Each sub-agent gets fresh context window
- Parallel execution via asyncio.gather()

---

## D15: Session Management via Files
**Date:** January 2026
**Context:** How to persist session state across context clears

**Options Considered:**
1. SQLite database
2. JSON files in ~/.atlas/sessions/
3. In-memory only

**Decision:** JSON files

**Rationale:**
- Simple, human-readable, debuggable
- No database setup required
- Easy to inspect/edit session state
- Portable across systems
- Sufficient for current scale

---

## D16: hooks.py CLI Breaking Change
**Date:** January 2026
**Context:** Original CLI used positional argument for input file

**Change:** `input_file` positional → `--input` flag

**Old:** `python -m ... babybrains qc_runner myfile.json`
**New:** `python -m ... babybrains qc_runner --input myfile.json`

**Rationale:**
- Positional was ambiguous (is myfile.json a hook_name or input?)
- Flag is explicit and self-documenting
- Allows `--timing` without confusion

---

## D17: Progressive Loading via Section Parsing
**Date:** January 2026
**Context:** Skills can be 8-12KB markdown files. Loading full content wastes context tokens when only specific sections are needed.

**Options Considered:**
1. YAML front matter for section metadata
2. Parse markdown ## headers at runtime
3. Pre-compile skill indexes

**Decision:** Parse markdown ## headers at runtime

**Rationale:**
- Skills already use ## headers consistently
- No additional metadata files needed
- 4-level partial matching (exact → case-insensitive → number-stripped → substring) handles user queries flexibly
- Lazy parsing means no startup cost

---

## D18: ScratchPad as Separate Module
**Date:** January 2026
**Context:** SessionManager has basic `scratch_data` dict. Needed richer intermediate state tracking for skill chains.

**Options Considered:**
1. Extend SessionManager.scratch_data with more features
2. Create separate ScratchPad class
3. Use SQLite for scratch state

**Decision:** Separate ScratchPad class

**Rationale:**
- Single Responsibility: SessionManager handles sessions, ScratchPad handles intermediate state
- ScratchPad can be used independently of sessions
- Typed ScratchEntry dataclass provides structure (key, value, step, timestamp, skill_name)
- File persistence enables recovery without coupling to SessionManager

---

## D19: Activity QC Hook Output Format
**Date:** January 2026
**Context:** Creating QC hook for Activity Atoms that integrates with existing HookRunner

**Options Considered:**
1. Custom output format optimized for Activity validation
2. Match existing hooks.py `_parse_json_result()` expectations exactly

**Decision:** Match hooks.py format (`pass`, `msg`, `severity: "block"`)

**Rationale:**
- hooks.py expects `output.get("pass")` not `output.get("passed")`
- hooks.py expects `issue.get("msg")` not `issue.get("message")`
- hooks.py uses `severity: "block"` not `severity: "blocking"`
- Framework compatibility > custom naming
- Discovered via adversarial sub-agent verification before deployment

---

## D20: Context-Aware Superlative Detection
**Date:** January 2026
**Context:** Superlative check was producing false positives on legitimate phrases

**Problem Cases:**
- "Best practices suggest..." (legitimate technical term)
- "Children perfect their skills" ("perfect" as verb)
- "Technique is still imperfect" (negated form)
- "Doesn't need to be perfect" (negated context)

**Decision:** Multi-layer context awareness

**Implementation:**
1. **Exception phrases:** Pre-compiled patterns for "best practice", "try your best", etc.
2. **Verb detection:** Pattern for "perfect(s|ed|ing) the/their/his/her/a"
3. **Prefix negation:** `(?<!im)` to exclude "imperfect"
4. **Context negation:** Check for "not/n't/no/never" preceding the match

**Rationale:**
- Voice guidelines allow anti-perfectionist messaging ("doesn't need to be perfect")
- Technical phrases like "best practices" are not promotional
- False positives undermine trust in the QC hook
- Pre-compiled patterns avoid O(n²) regex compilation

---

## D21: Quality Audit Gate (Grade A Enforcement)
**Date:** January 2026
**Context:** Activity Conversion Pipeline needed quality control beyond deterministic QC hook

**Problem:** QC hook catches structural issues (em-dashes, missing sections) but cannot assess:
- Philosophy integration (6 Montessori principles)
- Voice authenticity (Australian, understated confidence)
- Rationale field quality (Observable → Philosophy → Psychology → Reassurance)
- Science weaving (Observable → Invisible → Meaningful)

**Options Considered:**
1. Expand QC hook to check all criteria (deterministic)
2. Add LLM-based quality audit stage (semantic evaluation)
3. Human review catches everything (manual bottleneck)

**Decision:** LLM-based Quality Audit Stage after QC Hook

**Implementation:**
- `audit_quality()` spawns sub-agent to grade against Voice Elevation Rubric
- Only Grade A/A+/A- proceeds to human review
- Non-A grades trigger intelligent retry with "Wait" pattern reflection

**Rationale:**
- Voice quality requires semantic understanding (can't be regex)
- Sub-agent has fresh context (no pollution from conversion)
- Grade A gate reduces human reviewer burden
- Retry mechanism improves output quality automatically

---

## D22: Intelligent Retry with Wait Pattern
**Date:** January 2026
**Context:** When quality audit fails, need to improve next attempt rather than blind retry

**Problem:** Simple retry loops just hope for different output. LLMs have "blind spots" where they consistently make the same mistake.

**Research Finding:** Anthropic's introspection research shows 89.3% blind spot reduction with "Wait" pattern:
```
Wait. Before continuing, pause and consider:
- What assumptions did I make?
- Why did these specific issues occur?
- What would I tell another agent who made these mistakes?
```

**Decision:** Intelligent retry with `reflect_on_failure()` + feedback injection

**Implementation:**
```python
# After failed quality audit:
feedback = await self.reflect_on_failure(failed_yaml, issues, grade)
result = await self.convert_activity(raw_id, feedback=feedback)
```

**Rationale:**
- Each retry learns from what went wrong
- Feedback is passed to elevate skill for informed re-elevation
- Reduces retry count needed to reach Grade A
- Leverages proven Anthropic research pattern

---

## D23: CLI Mode Default (No API Key Required)
**Date:** January 2026
**Context:** Activity Pipeline was requiring ANTHROPIC_API_KEY for SkillExecutor

**Problem:**
- API mode costs per-token
- User has Max subscription (CLI mode is $0)
- Pipeline should work out-of-box without environment setup

**Decision:** Switch to CLI mode by default

**Before:**
```python
if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError("ANTHROPIC_API_KEY required")
self.skill_executor = SkillExecutor(use_api=True)
```

**After:**
```python
# CLI mode for Max subscription (no API key needed)
self.skill_executor = SkillExecutor(timeout=300)
```

**Rationale:**
- Consistent with D10/D11 (CLI mode = Max = $0)
- Zero setup required for users with Max subscription
- Extended timeout (300s) for quality processing
- API mode still available if explicitly needed

---

## Template for New Decisions

```
## D[N]: [Title]
**Date:** [Month Year]
**Context:** [Why this decision was needed]

**Options Considered:**
1. [Option 1]
2. [Option 2]

**Decision:** [What was chosen]

**Rationale:** [Why]
```
