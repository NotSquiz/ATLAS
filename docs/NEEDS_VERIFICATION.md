# ATLAS: Claims Needing Verification

**Purpose:** These claims from research files may be outdated or need current validation before implementation.

---

## CRITICAL (Block Implementation)

### 1. Claude Code CLI Syntax
**Claim:** Headless mode uses `-p` flag, session resume uses `--resume`
**Source:** R7 (both sources)
**Risk:** HIGH - CLI flags evolve rapidly
**Verify:** `claude --help` or official docs
**Impact:** Core orchestration depends on this

### 2. MCP Configuration Format
**Claim:** Configuration in `.mcp.json` or `~/.claude.json`
**Source:** R5, R7, R8 (all sources)
**Risk:** MEDIUM - MCP spec actively evolving
**Verify:** Current MCP specification docs
**Impact:** All MCP servers depend on correct config format

### 3. WSL2 GPU Passthrough
**Claim:** Gemini assumes RTX 3050 Ti usable in WSL2
**Source:** R4 Gemini
**Risk:** HIGH - WSLg GPU support varies by driver/Windows version
**Verify:** Test `nvidia-smi` in WSL2, check WSLg status
**Impact:** Determines TTS choice (Piper CPU vs Kokoro GPU)

---

## HIGH PRIORITY (Affects Architecture)

### 4. sqlite-vec Status
**Claim:** "sqlite-vec is successor to sqlite-vss, 30MB default RAM"
**Source:** R1 (both sources)
**Risk:** MEDIUM - Newer library, API may have changed
**Verify:** https://github.com/asg017/sqlite-vec - check latest release, API
**Impact:** Core vector search depends on this

### 5. Exa.ai Pricing
**Claim:** "$5 per 1,000 queries" for Auto/Fast search
**Source:** R8 Opus
**Risk:** HIGH - AI API pricing changes frequently
**Verify:** https://exa.ai/pricing
**Impact:** Monthly cost budgeting, caching strategy

### 6. ref.tools Credit System
**Claim:** "200 free credits (never expire), $9/month for 1,000"
**Source:** R8 Opus
**Risk:** HIGH - Pricing models change
**Verify:** https://ref.tools/pricing
**Impact:** Knowledge retrieval strategy

### 7. Claude 3.5 Haiku TTFT
**Claim:** "Time-to-first-token approximately 0.36 seconds"
**Source:** R4 (both sources)
**Risk:** MEDIUM - API performance varies
**Verify:** Current Anthropic benchmarks or live testing
**Impact:** Voice latency budget

### 8. Moonshine Model
**Claim:** "Moonshine tiny achieves 5x speedup, 0.3-0.6s for 3-5s audio"
**Source:** R4 Opus
**Risk:** HIGH - Very new model (late 2024)
**Verify:** https://github.com/usefulsensors/moonshine - benchmarks
**Impact:** Could be faster STT option than faster-whisper

---

## MEDIUM PRIORITY (Optimization)

### 9. DoSvc Memory Leak
**Claim:** "Delivery Optimization (DoSvc) causes 20GB memory leak"
**Source:** R3 Opus (cites December 2025)
**Risk:** MEDIUM - May be patched
**Verify:** Windows 11 current build release notes
**Impact:** RAM optimization script validity

### 10. autoMemoryReclaim Stability
**Claim:** "Experimental feature, gradual mode recommended"
**Source:** R3 (both sources)
**Risk:** MEDIUM - WSL2 updates frequently
**Verify:** Current WSL2 release notes
**Impact:** Memory reclamation reliability

### 11. Garmin garth Library
**Claim:** "OAuth1 tokens survive for 1 year"
**Source:** R5 Opus
**Risk:** HIGH - Unofficial API, Garmin could change anytime
**Verify:** https://github.com/matin/garth - recent issues/releases
**Impact:** Health data MCP server reliability

### 12. FastMCP Integration
**Claim:** "FastMCP 2.0 merged into official MCP SDK"
**Source:** R5 (both sources)
**Risk:** MEDIUM - SDK actively developed
**Verify:** https://github.com/modelcontextprotocol/python-sdk
**Impact:** MCP server implementation approach

### 13. Prompt Caching Benefits
**Claim:** "Reduce latency 2-10x and costs up to 90%"
**Source:** R9 Opus
**Risk:** MEDIUM - Benefits depend on use pattern
**Verify:** Anthropic prompt caching docs
**Impact:** Cost optimization strategy

---

## LOW PRIORITY (Nice to Know)

### 14. Ruff Speed Claims
**Claim:** Opus says "10-100x faster", Gemini says "30x faster"
**Source:** R9 (both sources)
**Risk:** LOW - Either way, it's faster
**Verify:** Ruff benchmarks
**Impact:** Just accuracy

### 15. ONNX INT8 Exact Memory
**Claim:** Opus says ~100MB, Gemini says ~50MB
**Source:** R1 (both sources)
**Risk:** LOW - Both within budget
**Verify:** Actual measurement
**Impact:** Fine-tuning RAM budget

### 16. FTS5 Performance at Scale
**Claim:** "Single-digit millisecond latency for <100K records"
**Source:** R1 Opus
**Risk:** LOW - Well-established SQLite feature
**Verify:** Benchmark with actual data
**Impact:** Query latency expectations

---

## Verification Commands

```bash
# WSL2 GPU check
nvidia-smi

# sqlite-vec installation test
pip install sqlite-vec
python -c "import sqlite_vec; print(sqlite_vec.__version__)"

# Claude Code version
claude --version
claude --help

# MCP SDK version
pip show mcp

# Moonshine availability
pip install moonshine-onnx
python -c "from moonshine import Moonshine; print('OK')"
```

---

## Web Searches to Run

1. "sqlite-vec 2025 API documentation"
2. "exa.ai pricing January 2025"
3. "Claude Code CLI headless mode 2025"
4. "WSL2 GPU passthrough CUDA 2025"
5. "MCP specification latest version 2025"
6. "Moonshine vs faster-whisper benchmark 2025"
7. "Windows 11 DoSvc memory leak fix"
8. "autoMemoryReclaim WSL2 Docker conflict"
