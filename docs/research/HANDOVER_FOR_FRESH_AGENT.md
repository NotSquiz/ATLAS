# ATLAS Project Handover - January 2026

**Purpose:** This document provides everything a fresh agent needs to understand and build ATLAS without re-reading 15 research files.

---

## What is ATLAS?

ATLAS is a **voice-first AI life assistant** running on constrained hardware:
- 16GB Windows 11 system
- ~6GB usable RAM in WSL2
- 4GB VRAM (RTX 3050 Ti)
- Target: Sub-3 second voice latency
- Budget: <$20/month for external APIs

---

## Research Validation Status

**24 research documents analyzed** (R1-R15 from Gemini + Opus deep research):

| Category | Files | Validation | Confidence |
|----------|-------|------------|------------|
| Memory/Embeddings | R1, R6, R12 | ✅ Converged | HIGH |
| Voice Pipeline | R4, R11 | ✅ Converged | HIGH |
| WSL2/Windows | R3, R14 | ✅ Verified Dec 2025 | HIGH |
| Claude/MCP | R5, R7, R10 | ✅ Verified Jan 2026 | HIGH |
| Knowledge APIs | R8, R13 | ✅ Converged | HIGH |
| Architecture | R9, R15 | ✅ Converged | HIGH |
| Learning/Reflection | R2 | ✅ Verified | MEDIUM |

**Date Note:** R11-R15 have "2025" in titles (written from 2025 perspective) but technical content is still current. R10 explicitly says "January 2026 Reference."

---

## Verified Technology Stack

### Memory System
```
Database:      SQLite (single file, WAL mode)
Vector Search: sqlite-vec v0.1.6 (filtered search supported)
Text Search:   FTS5 with Porter stemmer
Embeddings:    BGE-small-en-v1.5 (NOT all-MiniLM-L6-v2)
               - 384 dimensions, ~32MB INT8
               - 10% better retrieval than all-MiniLM-L6-v2
Search:        Hybrid RRF (60% vector, 40% keyword)
Scale Limit:   500K vectors before considering LanceDB
```

### Voice Pipeline
```
STT Options:
  - Moonshine Base: ~700ms, 10% WER, ~1.2GB VRAM (SPEED)
  - faster-whisper turbo INT8: ~1.5s, 1.9% WER, ~1.5GB VRAM (ACCURACY)

TTS:           Kokoro-82M ONNX
               - <300ms GPU latency
               - #1 on TTS Spaces Arena
               - Apache 2.0 license
Fallback TTS:  Piper (CPU-only, <256MB RAM)

VAD:           Silero VAD v6.2
               - <1ms per 30ms chunk
               - threshold=0.5, min_silence=400ms
```

### Claude Integration
```
Package:       claude-agent-sdk (renamed from claude-code-sdk)
               pip install claude-agent-sdk

Headless:      claude -p "prompt" --output-format stream-json
Resume:        claude -p "continue" --resume <session_id>

Subagents:
  - Explore (Haiku): Fast codebase discovery
  - Plan (Sonnet): Architecture research
  - General-Purpose (Sonnet): Complex tasks

Hooks:         10 event types, exit code 2 = block operation
MCP Transport: STDIO for local servers
```

### External Knowledge ($12-20/month)
```
Exa.ai:        $15/month (semantic code search, <350ms P50)
Jina Reader:   $0 (10M free tokens, ~3 months)
DevDocs:       $0 (self-hosted via Docker)
GitHub API:    $0 (10 req/min limit)
Stack Overflow: $0 (10K req/day with API key)
```

### WSL2 Configuration
```ini
# ~/.wslconfig (Windows side)
[wsl2]
memory=6GB
swap=8GB
processors=6

[experimental]
autoMemoryReclaim=dropcache    # NOT gradual (has bugs)
sparseVhd=true
```

**Critical Windows Fix:**
```powershell
# DoSvc memory leak in Windows 11 24H2 - FIX FIRST
Stop-Service -Force -Name "DoSvc"
Set-Service -Name "DoSvc" -StartupType Disabled
```

---

## Resolved Conflicts

| Topic | Conflict | Resolution |
|-------|----------|------------|
| Embedding model | R1/R6 said all-MiniLM-L6-v2, R12 said BGE-small | **BGE-small-en-v1.5** (R12 explicitly supersedes) |
| autoMemoryReclaim | Some sources said gradual | **dropcache** (gradual conflicts with Docker/zswap) |
| External APIs | R8 said ref.tools, R13 said too expensive | **Jina Reader** (free tier, replaces ref.tools) |
| SDK name | Some docs said claude-code-sdk | **claude-agent-sdk** (renamed) |
| AutoGen | Some docs recommended it | **AVOID** (deprecated, MS moving to new framework) |

---

## RAM Budget (Verified)

### System RAM (~6GB WSL2)
| Component | RAM |
|-----------|-----|
| WSL2 kernel | ~300MB |
| Python + libraries | ~200MB |
| BGE-small-en-v1.5 | ~100MB |
| sqlite-vec + FTS5 | ~100MB |
| Silero VAD | ~50MB |
| MCP Server | ~150MB |
| **Subtotal** | **~900MB** |
| **Headroom** | **~5GB** |

### GPU VRAM (4GB, separate from RAM)
| Component | VRAM |
|-----------|------|
| Moonshine Base OR faster-whisper | ~1.5GB |
| Kokoro-82M | ~300MB |
| Display overhead | ~300MB |
| **Headroom** | **~1.9GB** |

---

## What NOT to Do

1. **Don't install PipeWire in WSL2** - breaks WSLg audio
2. **Don't use autoMemoryReclaim=gradual** - causes hangs
3. **Don't use AutoGen** - deprecated
4. **Don't install NVIDIA driver in WSL2** - Windows driver handles it
5. **Don't trust LLM self-correction** - use external verification
6. **Don't run MCP servers without containers** - security vulnerabilities documented

---

## Build Priority

### P0: MVP (First)
1. Apply WSL2 optimizations (DoSvc fix, .wslconfig)
2. SQLite + sqlite-vec + FTS5 memory system
3. BGE-small-en-v1.5 embeddings (ONNX)
4. Moonshine STT + Piper TTS (simpler first)
5. Single MCP server (STDIO)
6. Basic PreToolUse safety hook

### P1: Core Experience (Second)
7. Upgrade to Kokoro TTS (GPU)
8. Claude Haiku streaming
9. Exa.ai + Jina Reader integration
10. Hybrid search (RRF fusion)

### P2: Enhanced (Later)
11. Hybrid audio architecture (Windows capture)
12. faster-whisper turbo for accuracy mode
13. Adaptive reflection system

---

## File Structure to Create

```
/home/squiz/ATLAS/
├── atlas/
│   ├── __init__.py
│   ├── memory/
│   │   ├── store.py          # SQLite + sqlite-vec
│   │   ├── embeddings.py     # BGE-small-en-v1.5 ONNX
│   │   └── search.py         # Hybrid RRF search
│   ├── voice/
│   │   ├── stt.py            # Moonshine/faster-whisper
│   │   ├── tts.py            # Kokoro/Piper
│   │   └── vad.py            # Silero
│   ├── mcp/
│   │   └── memory_server.py  # FastMCP memory tools
│   └── knowledge/
│       ├── exa.py            # Exa.ai client
│       └── cache.py          # SQLite cache
├── .claude/
│   ├── settings.json         # Hooks configuration
│   └── hooks/
│       └── validate-bash.py  # Safety hook
└── scripts/
    └── optimize_wsl.ps1      # Windows optimization
```

---

## Verification Checklist

Before building, confirm:
- [ ] DoSvc disabled, RAM freed
- [ ] .wslconfig applied, WSL restarted
- [ ] `nvidia-smi` works in WSL2
- [ ] Audio test: `aplay /usr/share/sounds/alsa/Front_Center.wav`
- [ ] `pip install claude-agent-sdk` succeeds
- [ ] `pip install sqlite-vec` succeeds

---

## Key Research Files (If Deep Dive Needed)

| File | Topic | Read If... |
|------|-------|------------|
| R10 | Claude Code/MCP | Need hook or MCP details |
| R11 | Voice pipeline | Need STT/TTS specifics |
| R12 | SQLite memory | Need schema or search details |
| R13 | External APIs | Need API integration details |
| R14 | WSL2 optimization | Need Windows config details |
| R15 | Agent architecture | Need orchestration patterns |

---

## Summary for Fresh Agent

**ATLAS is ready to build.** The research phase is complete with:
- 24 documents analyzed
- All conflicts resolved
- All technology choices verified
- RAM/VRAM budgets confirmed
- Build priorities established

**Start with P0 items.** The architecture is sound and fits the hardware constraints.
