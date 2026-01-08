# What We Learned from R10-R15 (Verification Research)

These 6 prompts (12 files - Gemini PDF + Opus MD each) were designed to verify and deepen the original R1-R9 research.

---

## R10: Claude Code CLI and MCP Protocol

**Key Learnings:**
1. **SDK renamed**: `claude-agent-sdk` not `claude-code-sdk`
2. **Headless mode exists**: `claude -p "prompt" --output-format stream-json`
3. **Sessions resume**: `--resume <session_id>` continues work
4. **Hooks system**: 10 event types, exit code 2 blocks operations
5. **MCP spec version**: 2025-11-25 is current
6. **STDIO transport**: Best for local servers (no network overhead)
7. **FastMCP**: `pip install "mcp[cli]"` for Python servers

**Changed from R1-R9:** Confirmed SDK naming, added hook details not in earlier research.

---

## R11: Voice AI Pipeline for 6GB RAM

**Key Learnings:**
1. **Moonshine is the dark horse**: 5-15x faster than Whisper at equivalent accuracy
2. **Trade-off confirmed**: Moonshine (10% WER, 500ms) vs faster-whisper turbo (1.9% WER, 1.5s)
3. **Kokoro-82M verified #1**: On TTS Spaces Arena, sub-300ms GPU latency
4. **WSL2 audio bottleneck**: 50-300ms overhead from WSLg PulseAudio
5. **Hybrid architecture solves it**: Windows audio capture → WSL2 processing
6. **DO NOT install PipeWire**: Breaks WSLg completely
7. **Sub-3s achievable**: But tight - requires all optimizations

**Changed from R1-R9:** Added Moonshine as primary option, identified WSL2 audio as hidden bottleneck.

---

## R12: SQLite for AI Agent Memory

**Key Learnings:**
1. **BGE-small-en-v1.5 > all-MiniLM-L6-v2**: 10% better retrieval, same dimensions
2. **sqlite-vec v0.1.6**: Filtered vector search NOW WORKS
3. **Hybrid search via RRF**: 60% vector + 40% FTS5 is optimal
4. **WAL mode essential**: 10-12x faster writes
5. **Three-tier memory**: Core (persona) → Semantic (facts) → Episodic (conversations)
6. **Scale limit**: 500K vectors before needing LanceDB
7. **Storage at 100K records**: ~500-700MB total

**Changed from R1-R9:** Upgraded embedding model recommendation, confirmed sqlite-vec filtered search.

---

## R13: External Knowledge APIs

**Key Learnings:**
1. **ref.tools too expensive**: $27-45/month exceeds budget
2. **Jina Reader replaces it**: 10M free tokens (~3 months)
3. **Exa.ai is cost-effective**: $5/1K searches, <350ms P50
4. **GitHub API severely limited**: Only 10 req/min
5. **Self-host DevDocs**: Eliminates documentation access headaches
6. **Cache hit rate**: 75-85% at steady state with proper TTLs
7. **Budget stack**: Exa + Jina + DevDocs = $12-20/month

**Changed from R1-R9:** Replaced ref.tools recommendation with Jina Reader for budget.

---

## R14: WSL2 Memory Optimization

**Key Learnings:**
1. **DoSvc memory leak**: Active in Windows 11 24H2, MUST FIX FIRST
2. **autoMemoryReclaim=dropcache**: NOT gradual (gradual has bugs with Docker)
3. **sparseVhd=true**: Enable for automatic VHD shrinking
4. **CUDA works perfectly**: 85-95% of native Linux performance
5. **VRAM is separate**: Doesn't count against WSL2 memory limit
6. **Podman uses 65% less memory**: Than Docker Desktop if needed
7. **Realistic budget**: 5-6GB available for AI with optimization

**Changed from R1-R9:** Confirmed dropcache over gradual, identified DoSvc leak as critical fix.

---

## R15: AI Agent Architecture

**Key Learnings:**
1. **AutoGen is DEPRECATED**: Microsoft moving to new framework (GA Q1 2026)
2. **LangGraph leads**: Verified at LinkedIn, Uber, Replit
3. **CrewAI viable**: $18M funded, 450M agents/month
4. **Self-correction is mostly myth**: External verification required
5. **Self-consistency sampling works**: 5 samples + vote = +17.9% accuracy
6. **MCP security vulnerabilities**: Prompt injection, tool poisoning documented
7. **Qwen 2.5 7B local**: Sweet spot for quality/size on 16GB

**Changed from R1-R9:** Added AutoGen deprecation warning, MCP security concerns.

---

## Summary: What Changed from Original Research

| Topic | R1-R9 Said | R10-R15 Clarified |
|-------|------------|-------------------|
| Embedding model | all-MiniLM-L6-v2 | **BGE-small-en-v1.5** (10% better) |
| SDK name | claude-code-sdk | **claude-agent-sdk** (renamed) |
| Memory reclaim | gradual | **dropcache** (gradual has bugs) |
| External APIs | ref.tools | **Jina Reader** (free tier) |
| AutoGen | Consider it | **AVOID** (deprecated) |
| STT primary | faster-whisper | **Moonshine OR faster-whisper** (trade-off) |
| WSL2 audio | Assumed fine | **Hidden bottleneck** (50-300ms) |
| MCP security | Not mentioned | **Critical concerns** (containerize) |

---

## Confidence Assessment

| Finding | Confidence | Why |
|---------|------------|-----|
| BGE-small > all-MiniLM | HIGH | R12 explicit, benchmarks cited |
| dropcache > gradual | HIGH | R14 explicit, GitHub issues cited |
| Moonshine viable | HIGH | R11 benchmarks, October 2024 release |
| Kokoro #1 TTS | HIGH | R11 cites TTS Arena ranking |
| AutoGen deprecated | HIGH | R15 explicit, Microsoft announcement |
| DoSvc leak | HIGH | R14 explicit, KB5072033 cited |
| Jina Reader free tier | MEDIUM-HIGH | R13 claims 10M tokens, verify |
| Sub-3s latency | MEDIUM | Achievable but requires all optimizations |

---

## What R10-R15 Did NOT Cover

These gaps remain from R1-R9 (not contradicted, just not re-verified):
- Specific APScheduler patterns for reflection scheduling
- NetworkX vs pure-SQLite for graph relationships
- Exact prompt templates for personas
- Long-term scaling beyond 500K vectors

These are lower priority and can be addressed during implementation.
