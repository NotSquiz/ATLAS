# ATLAS Research Prompts - Ready to Copy

**DATE: January 2026** - All prompts request CURRENT information as of January 2026.

Copy each prompt directly into Gemini Deep Research or Opus Web Research.
Run each through BOTH agents, then compare results.

---

## PROMPT 1: Claude Code & MCP (CRITICAL - RUN FIRST)

```
I am building ATLAS, an AI life assistant wrapping Claude Code with orchestration, memory, and voice. I need CURRENT, VERIFIED information as of JANUARY 2026 about Claude Code CLI and the Model Context Protocol.

CLAUDE CODE CLI:
1. Exact command syntax for headless/non-interactive mode - is it `-p` or `--print`?
2. Session resumption - exact flags and how it works
3. Running Claude Code programmatically from Python/Node.js - official methods
4. Available subagent types (general-purpose, Explore, Plan, etc.) - complete list
5. Hooks configuration - PreToolUse, PostToolUse - where do configs live, exact JSON schema
6. The `--dangerously-skip-permissions` flag - when appropriate, security implications
7. Output format options (text, json, stream-json) - exact syntax

MCP (Model Context Protocol):
1. Current MCP spec version number as of January 2026
2. Correct configuration file location and format
3. STDIO vs HTTP/SSE transport - official recommendation for local servers
4. Official Python SDK - package name, current version, installation
5. FastMCP - is it merged into official SDK or separate package?
6. Registering MCP servers with Claude Code - exact configuration syntax

HOOKS SYSTEM:
1. All hook types that exist
2. Exact JSON schema for hook input/output
3. How to block a tool call (exit code 2 behavior)
4. Async/non-blocking hooks - supported?

Provide exact command examples, link to official documentation, note any changes in 2025, and flag anything experimental/beta.
```

---

## PROMPT 2: Voice Pipeline - STT/TTS/VAD (HIGH PRIORITY)

```
I need the optimal voice AI pipeline for a constrained system as of JANUARY 2026: 16GB total RAM, ~6GB usable for WSL2, NVIDIA RTX 3050 Ti (4GB VRAM). Target: sub-3 second end-to-end latency, must run locally.

SPEECH-TO-TEXT - Compare these with ACTUAL 2025/2026 BENCHMARKS:

1. faster-whisper (CTranslate2):
   - Current version January 2026
   - VRAM requirements per model size
   - INT8 quantization: latency AND accuracy benchmarks
   - Real-world latency for 3-5 second utterances

2. Moonshine (Useful Sensors):
   - Production readiness status January 2026
   - Direct benchmark comparison vs faster-whisper
   - ONNX support status and performance
   - Memory footprint

3. Distil-Whisper: Current state vs alternatives

4. Any NEW STT models from 2025 optimized for low-latency local inference?

TEXT-TO-SPEECH - Compare:

1. Piper: Current version, best voices, latency, memory, streaming
2. Kokoro: ONNX status, CPU vs GPU, memory requirements
3. Any NEW neural TTS from 2025 under 500MB RAM?

VAD: Silero VAD still best? Alternatives from 2025?

WSL2 SPECIFIC (January 2026 state):
- Audio passthrough current state
- GPU CUDA support status, required drivers
- Does faster-whisper CUDA work in WSL2?

REALISTIC LATENCY: Pessimistic/realistic/optimistic estimates for full pipeline.

Provide actual benchmark numbers, memory measurements, comparison tables.
```

---

## PROMPT 3: SQLite Memory Architecture (HIGH PRIORITY)

```
I'm building persistent memory for an AI assistant as of JANUARY 2026. 6GB RAM budget, hybrid search (keyword + vector), <100K records initially, must be embedded.

Current plan: SQLite + sqlite-vec + FTS5 + all-MiniLM-L6-v2 (384 dimensions, ONNX INT8)

SQLITE-VEC (January 2026):
1. Current version and stability status
2. RAM usage benchmarks: idle, during query, with 100K 384-dim vectors
3. Query performance at 100K vectors
4. Filtered vector search support?
5. Comparison with alternatives: sqlite-vss, chromadb-embedded, LanceDB

FTS5:
1. Best tokenizer for conversational AI memory
2. Combining FTS5 + vector search - best fusion strategy
3. Memory overhead at 100K documents

EMBEDDING MODEL:
1. Is all-MiniLM-L6-v2 still optimal in January 2026?
2. ONNX INT8 quantization accuracy
3. Alternatives: BGE-small, E5-small, GTE-small
4. Any new efficient embedding models from 2025?

SCHEMA PATTERNS:
1. Tiered memory (core/episodic/semantic) best practices
2. Storing embeddings: BLOB vs virtual table
3. Memory consolidation patterns

PERFORMANCE: Realistic hybrid search latency at 100K records, real-time embed+insert feasibility.

GRAPH: SQLite CTEs vs NetworkX - when is each needed?

Provide benchmark data, memory measurements, code examples, decision matrices.
```

---

## PROMPT 4: External Knowledge APIs - Pricing & Limits

```
ATLAS needs external knowledge APIs as of JANUARY 2026: documentation, code examples, packages, Stack Overflow. Budget: <$20/month, <500ms latency.

EXA.AI (January 2026):
1. Current pricing for all tiers
2. Rate limits
3. Code search quality vs GitHub search, Sourcegraph
4. Alternatives?

REF.TOOLS (January 2026):
1. Current pricing model
2. Actual token reduction achieved
3. Coverage and rate limits
4. Alternatives: Jina Reader, FireCrawl

GITHUB API: Code search limits, rate limits, cost

STACK OVERFLOW (January 2026): API access status after AI policy changes, restrictions

PACKAGE REGISTRIES: PyPI, npm rate limits and stability

COST MODEL: For 50-100 queries/day, realistic monthly cost

Provide CURRENT pricing verified against official pages, rate limits, API examples.
```

---

## PROMPT 5: Windows 11 WSL2 Optimization (CRITICAL - RUN FIRST)

```
Running AI workloads on Windows 11 (latest 2026 build) with 16GB RAM, WSL2 Ubuntu. Goal: ~6GB usable for WSL2. Need GPU (RTX 3050 Ti) and audio working.

WSLCONFIG (January 2026):
1. Current .wslconfig syntax - all options
2. autoMemoryReclaim - status and modes (gradual, dropcache)
3. Docker Desktop interaction
4. Recommended config for 16GB AI system

MEMORY:
1. Does WSL2 return memory to Windows properly now?
2. Known bugs January 2026
3. Monitoring actual WSL2 memory usage

WINDOWS SERVICES (2026):
1. Safe to disable for RAM?
2. New memory-heavy services?
3. Memory leak status: DoSvc, NDU, others

GPU IN WSL2 (January 2026):
1. CUDA support current state
2. Required driver versions
3. PyTorch/ONNX CUDA working?
4. Verification commands

AUDIO IN WSL2:
1. PulseAudio vs PipeWire status
2. Microphone reliability
3. Setup steps

PRACTICAL BUDGET: Windows idle, with browser, WSL2 available, total for AI

Provide current info for latest Windows 11, .wslconfig examples, PowerShell commands, verification steps.
```

---

## PROMPT 6: Cutting Edge Agent Architecture

```
Building ATLAS personal AI assistant as of JANUARY 2026: voice interface, persistent memory, MCP tools, reflection, orchestration. 6GB RAM constraint.

Ensure I'm not missing developments from 2025.

ORCHESTRATION (2026):
1. Multi-agent state of the art
2. LangGraph vs CrewAI vs AutoGen vs Claude native - which won?
3. New frameworks from 2025
4. What works on 6GB RAM?

MEMORY/RAG:
1. Latest agent memory developments 2025
2. GraphRAG maturity
3. New efficient embedding models
4. Memory-efficient RAG for constrained systems

TOOL USE:
1. MCP adoption status - is it standard now?
2. Alternatives
3. Computer use for personal assistants

REFLECTION:
1. Reflexion improvements
2. Self-improvement without fine-tuning - what works
3. Constitutional AI patterns

VOICE AGENTS:
1. Real-time voice AI advances 2025
2. Interruption handling
3. Conversational turn-taking

LOCAL AI:
1. Consumer hardware models 2025
2. Hybrid local+cloud best practices
3. Quantization advances (GGUF, AWQ, etc.)

PERSONAL ASSISTANTS:
1. What shipped in 2025? Lessons learned
2. What patterns work in practice
3. Security best practices

KEY PAPERS/PROJECTS from 2025

Focus on PRACTICAL, implementable. Distinguish proven from experimental. Prioritize constrained hardware.
```

---

## Execution Checklist

| # | Prompt | Priority | Gemini | Opus | Compared |
|---|--------|----------|--------|------|----------|
| 1 | Claude Code/MCP | CRITICAL | [ ] | [ ] | [ ] |
| 5 | Windows/WSL2 | CRITICAL | [ ] | [ ] | [ ] |
| 2 | Voice Pipeline | HIGH | [ ] | [ ] | [ ] |
| 3 | SQLite Memory | HIGH | [ ] | [ ] | [ ] |
| 4 | External APIs | MEDIUM | [ ] | [ ] | [ ] |
| 6 | Cutting Edge | MEDIUM | [ ] | [ ] | [ ] |

**NOTE:** You mentioned you've already started prompts 1-3. The research agents should find current info regardless of dates in prompts. If concerned, you can re-run with explicit "January 2026" dates.
