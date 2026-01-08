# ATLAS Research Synthesis

**Generated:** 2026-01-04
**Sources:** 18 research files (9 topics × Gemini + Opus)
**Constraint:** ~6GB usable RAM (WSL2 on 16GB Windows 11)

---

## Executive Summary

All 9 research topics have been analyzed. **ATLAS is feasible within 6GB RAM** with the following key decisions:

| Decision | Choice | Why |
|----------|--------|-----|
| Vector DB | SQLite + sqlite-vec | 30MB overhead vs 500MB+ for ChromaDB |
| Embeddings | all-MiniLM-L6-v2 (ONNX INT8) | 50-100MB, 384 dims, local |
| Graph | SQLite CTEs (NOT NetworkX for large graphs) | Zero RAM overhead |
| STT | faster-whisper (INT8, beam=1) | 2.9GB VRAM, sub-1s latency |
| TTS | Piper (CPU) or Kokoro (if GPU) | 100-300ms latency |
| MCP Transport | STDIO only | 5-10MB vs 30-50MB for HTTP |
| Task Queue | SQLite-backed MCP server | <10MB |
| Knowledge Source | ref.tools + exa.ai with SQLite cache | 60-80% cache hit rate |

---

## Consensus Points (Both Sources Agree)

### Memory Architecture (R1)
- **sqlite-vec** over sqlite-vss (30MB RAM, successor library)
- **all-MiniLM-L6-v2** at 384 dimensions (MTEB ~56)
- **ONNX Runtime** mandatory for inference (2x speedup over PyTorch)
- **Hybrid FTS5 + Vector** search with RRF fusion (k=60)
- **<100K records** target scale for brute-force viability
- **Three-tier memory**: Core (identity), Episodic (experiences), Semantic (facts)

### Learning & Reflection (R2)
- **Multi-tier reflection**: Lightweight (~500ms) → Adaptive → Nightly → Weekly
- **Event-based triggers** more effective than time-based during active use
- **SM-2/FSRS** for memory decay scheduling
- **Importance threshold ~150** triggers reflection (from Generative Agents)
- **Sycophancy flip rate >20%** indicates problem

### Windows Optimization (R3)
- **WSL2 .wslconfig**: `memory=6GB`, `autoMemoryReclaim=gradual`
- **Disable**: DoSvc, SysMain, WSearch, DiagTrack
- **faster-whisper INT8** fits in 4GB VRAM (~2.9GB actual)
- **Edge over Chrome** for RAM efficiency (sleeping tabs = 85% reduction)

### Voice Pipeline (R4)
- **faster-whisper** with CTranslate2, beam_size=1, greedy decoding
- **Claude 3.5 Haiku** TTFT ~0.36s (streaming essential)
- **VAD silence** 300-400ms threshold
- **Sub-4s achievable**, 1.5-2.5s realistic for CPU-only

### MCP Servers (R5)
- **STDIO transport** mandatory (5-10MB vs 50-80MB for HTTP)
- **Official MCP SDK** includes FastMCP internally
- **Single consolidated server** preferred (150MB vs 250MB+ for multiple)
- **Google OAuth auto-refreshes** tokens

### Knowledge Graphs (R6)
- **NetworkX viable** for <5000 nodes (~50-200KB)
- **YAML as source of truth**, pickle for fast reload (10x faster)
- **JSONL + byte-offset index** for larger/growing data (O(1) access)

### Orchestration (R7)
- **Claude Code native subagents** sufficient (no LangChain needed)
- **PreToolUse hook** is primary safety mechanism (exit code 2 blocks)
- **SQLite task queue** for async work
- **Risk scoring** with thresholds (70 = approval, 90 = block)

### External Knowledge (R8)
- **ref.tools** delivers 60-95% fewer tokens
- **exa.ai** for code search ($5/1K queries)
- **SQLite cache** reduces API calls 60-80%
- **WAL mode** essential for concurrent access

### ATLAS Design (R9)
- **tree-sitter** for universal AST parsing
- **SQLite + FTS5** for memory (sub-millisecond search)
- **MCP as integration layer**
- **Ruff** for Python linting (10-100x faster)
- **ReAct pattern** for reasoning loop

---

## Key Conflicts & Resolutions

| Topic | Opus Says | Gemini Says | Resolution |
|-------|-----------|-------------|------------|
| ONNX INT8 RAM | ~100MB | ~50MB | **Budget 75-100MB** (conservative) |
| INT8 Latency | 10-15ms | 2-5ms | **Budget 5-15ms** (realistic) |
| Graph Solution | NetworkX | SQLite CTEs | **CTEs for traversal, NetworkX only for small in-memory analysis** |
| TTS Choice | Piper (CPU) | Kokoro (GPU) | **Piper for CPU-only, Kokoro if GPU available** |
| FTS Tokenizer | Porter stemmer | Trigram | **Trigram** for fuzzy matching |
| autoMemoryReclaim | dropcache | gradual | **gradual** (safer with Docker) |
| WSL2 swap | 8GB | 4GB | **8GB** (safer for model loading spikes) |
| Vector Store | ChromaDB/LanceDB | SQLite BLOBs | **SQLite BLOBs** (RAM constraint) |
| Orchestration | Native only | External frameworks | **Native Claude Code** (simplest, fits constraint) |

---

## Gaps Requiring Further Research

### Critical (Block Implementation)
1. **WSL2 GPU passthrough** - Can we use GPU in WSL2? Current state unclear
2. **Claude Code CLI current syntax** - Verify `-p`, `--resume` flags still work
3. **MCP config format** - Verify `.mcp.json` structure hasn't changed

### Important (Affects Design)
4. **Moonshine vs Distil-Whisper** - Need current benchmarks
5. **Concurrent subagent limits** - Memory per instance unknown
6. **Session resume reliability** - How often does it fail?

### Nice to Have (Optimization)
7. **Cold start latency** - Time from boot to ready
8. **Memory fragmentation** - Long-running process stability
9. **Docker + autoMemoryReclaim** - Known conflicts, severity unclear

---

## RAM Budget

| Component | RAM (MB) | Notes |
|-----------|----------|-------|
| **Fixed Costs** | | |
| WSL2 + Python base | 150 | Baseline |
| sqlite-vec + FTS5 | 80-100 | 100K records |
| all-MiniLM-L6-v2 | 75-100 | ONNX INT8 |
| Silero VAD | 50 | Voice detection |
| **Variable Costs** | | |
| faster-whisper | 500 | System RAM (model on GPU) |
| Piper TTS | 100-200 | CPU mode |
| OR Kokoro TTS | 300 | CPU mode |
| MCP Server | 100-200 | Unified STDIO |
| Claude Code CLI | 50-100 | Per instance |
| **Optional** | | |
| tree-sitter | 60-80 | 3-4 languages |
| LSP servers | 300-500 | pyright + tsserver |
| **TOTAL ESTIMATE** | **1,500-2,500** | Leaves 3.5-4.5GB headroom |

**VRAM Budget (4GB GPU):**
- faster-whisper INT8: ~2.9GB
- Display buffer: ~300MB
- Headroom: ~800MB (avoid Kokoro GPU unless needed)

---

## Build Priority Matrix

### P0: MVP (Must Have)
1. **SQLite + sqlite-vec + FTS5** memory system
2. **faster-whisper INT8** STT
3. **Piper** TTS (CPU)
4. **Single MCP server** (STDIO)
5. **PreToolUse safety hooks**
6. **Basic reflection** (lightweight tier only)

### P1: Core Experience
7. **Claude Haiku streaming** with prompt caching
8. **exa.ai + ref.tools** with SQLite cache
9. **Nightly consolidation** (episodic → semantic)
10. **Git checkpointing** (PostToolUse hook)
11. **Task queue MCP** for async work

### P2: Enhanced
12. **tree-sitter** code parsing
13. **LSP integration** (pyright, tsserver)
14. **Adaptive reflection** (confidence-triggered)
15. **NetworkX** for small graph analysis

### P3: Future (More RAM Needed)
16. **ChromaDB/LanceDB** vector DB
17. **Neo4j GraphRAG**
18. **Multiple concurrent subagents** (>2)
19. **Kokoro GPU** TTS

---

## Recommended .wslconfig

```ini
[wsl2]
memory=6GB
swap=8GB
processors=8

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
```

---

## Recommended Stack Summary

```yaml
memory:
  database: SQLite (WAL mode)
  vectors: sqlite-vec (30MB)
  text_search: FTS5 (trigram tokenizer)
  embeddings: all-MiniLM-L6-v2 (ONNX INT8, 384 dims)
  graph: SQLite CTEs (not NetworkX for large traversals)

voice:
  stt: faster-whisper (base.en, INT8, beam=1)
  vad: Silero (300ms silence threshold)
  llm: Claude 3.5 Haiku (streaming, prompt cache)
  tts: Piper (CPU) or Kokoro (GPU if available)

integration:
  transport: STDIO only
  framework: Official MCP Python SDK
  pattern: Single unified server

knowledge:
  docs: ref.tools (primary)
  code: exa.ai get_code_context_exa
  cache: SQLite (64MB page cache, 7-day TTL)

orchestration:
  agents: Claude Code native subagents (max 2-3 concurrent)
  safety: PreToolUse hooks (Python scripts)
  queue: SQLite-backed task MCP server
  checkpoints: Git commits (PostToolUse hook)

reflection:
  lightweight: Every turn, ~500ms, confidence check
  nightly: 3am, episodic→semantic consolidation
  decay: SM-2/FSRS retrievability
```

---

## Verification Checklist

Before building, verify these with web search:

- [ ] sqlite-vec current version and API stability
- [ ] Claude Code CLI `-p` and `--resume` current syntax
- [ ] MCP `.mcp.json` configuration format (spec version)
- [ ] exa.ai current pricing ($5/1K still valid?)
- [ ] ref.tools current pricing and credit system
- [ ] Moonshine model availability and benchmarks vs Distil-Whisper
- [ ] autoMemoryReclaim behavior with Docker Desktop
- [ ] WSL2 GPU passthrough current state (WSLg)
- [ ] garminconnect/garth library stability (unofficial Garmin API)
- [ ] DoSvc 20GB memory leak - still present in current Windows 11?
