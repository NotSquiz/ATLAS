# ATLAS Verified Architecture - January 2026

**Research Complete:** 21 research topics (R1-R21), ~30 files total (Gemini + Opus)
**Constraint:** ~6GB usable RAM in WSL2 on 16GB Windows 11
**Status:** FULLY VERIFIED - Technical + Persona systems complete
**Date Verified:** January 2026

### Analysis Files
- `/home/squiz/project rebuild/ATLAS/ANALYSIS_R1-R9_FOUNDATIONAL.md`
- `/home/squiz/project rebuild/ATLAS/ANALYSIS_R10-R15_TECHNICAL.md`
- `/home/squiz/project rebuild/ATLAS/ANALYSIS_R16-R21_PERSONA.md`

---

## Verification Status (January 2026)

3 independent sub-agents analyzed all research files and confirmed:

| Aspect | Verification Result |
|--------|-------------------|
| **Conclusions match** | ✅ All 3 agents converged on same recommendations |
| **No conflicts found** | ✅ Files are complementary, not contradictory |
| **Currency check** | ⚠️ R11-R15 have "2025" in titles but content is valid |
| **R10 explicitly current** | ✅ "January 2026 Reference" in title |
| **Technical content** | ✅ References latest versions (sqlite-vec v0.1.6, MCP 2025-11-25) |

### Handover Documents Created
- **`/home/squiz/project rebuild/ATLAS/HANDOVER_FOR_FRESH_AGENT.md`** - Complete context for new agent
- **`/home/squiz/project rebuild/ATLAS/WHAT_WE_LEARNED_R10-R15.md`** - Specific findings from verification research

### What Changed from R1-R9 to R10-R15
| Topic | Original | Verified |
|-------|----------|----------|
| Embedding model | all-MiniLM-L6-v2 | **BGE-small-en-v1.5** |
| SDK name | claude-code-sdk | **claude-agent-sdk** |
| Memory reclaim | gradual | **dropcache** |
| External APIs | ref.tools | **Jina Reader** |
| AutoGen | Consider it | **AVOID (deprecated)** |
| WSL2 audio | Assumed OK | **50-300ms overhead identified** |

---

## Executive Summary

ATLAS is **feasible and well-architected**. The research converged on clear choices with high confidence. Key decisions:

| Layer | Choice | Confidence |
|-------|--------|------------|
| **Orchestration** | Claude Agent SDK + native subagents | HIGH |
| **Memory** | SQLite + sqlite-vec + FTS5 + BGE-small-en-v1.5 | HIGH |
| **STT** | Moonshine Base (speed) OR faster-whisper turbo INT8 (accuracy) | HIGH |
| **TTS** | Kokoro-82M ONNX (GPU) or Piper (CPU fallback) | HIGH |
| **VAD** | Silero VAD v6.2 | HIGH |
| **MCP** | STDIO transport, single unified server | HIGH |
| **Knowledge** | Exa.ai + Jina Reader + DevDocs (self-hosted) | HIGH |
| **WSL2** | `autoMemoryReclaim=dropcache` + zswap | HIGH |

---

## 1. Windows/WSL2 Configuration (VERIFIED)

### Critical: Fix DoSvc Memory Leak First
```powershell
Stop-Service -Force -Name "DoSvc"
Set-Service -Name "DoSvc" -StartupType Disabled
Set-ItemProperty -Path "HKLM:\SYSTEM\ControlSet001\Services\Ndu" -Name "Start" -Value 4
Set-Service -Name "SysMain" -StartupType Disabled
Set-Service -Name "WSearch" -StartupType Disabled
```

### Verified .wslconfig
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

**Conflict Resolution:** Opus said `dropcache`, Gemini said `gradual`. Research shows `gradual` conflicts with zswap and Docker. **Use `dropcache`** for stability.

### GPU/Audio Status
- **CUDA**: Works at 85-95% native performance. Install driver on Windows ONLY.
- **VRAM**: Separate from WSL2 memory limit (your 4GB VRAM is additional)
- **Audio**: WSLg PulseAudio works. Do NOT install PipeWire. 50-200ms latency overhead.
- **Hybrid audio recommended**: Windows capture → WSL2 processing → Windows playback

---

## 2. Claude Agent SDK Integration (VERIFIED)

### SDK Renamed (Breaking Change)
```bash
pip install claude-agent-sdk  # NOT claude-code-sdk
```

### Headless Execution
```bash
claude -p "Your prompt" --output-format stream-json
claude -p "Continue work" --resume <session_id>
```

### Subagent Types (Built-in)
| Type | Model | Use |
|------|-------|-----|
| **General-Purpose** | Sonnet | Complex tasks |
| **Plan** | Sonnet | Read-only research |
| **Explore** | Haiku | Fast codebase discovery |

### Hooks Configuration (`~/.claude/settings.json`)
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": ".claude/hooks/validate-bash.py"}]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{"type": "command", "command": ".claude/hooks/post-edit.sh"}]
    }]
  }
}
```

### Exit Code 2 = Block Operation
```bash
#!/bin/bash
# Hook script - exit 2 to block, stderr fed back to Claude
if echo "$input" | grep -q "rm -rf"; then
  echo "Blocked: dangerous command" >&2
  exit 2
fi
exit 0
```

### MCP Configuration (`~/.claude.json`)
```json
{
  "mcpServers": {
    "atlas-memory": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "atlas.mcp.memory_server"],
      "env": {"ATLAS_DB": "/home/user/.atlas/memory.db"}
    }
  }
}
```

### Resource Costs
- **Per Claude Code process**: 1.5-2GB RAM (can grow to 12GB over 30-60 min)
- **Recommendation**: Restart sessions periodically, use `/compact` for long sessions

---

## 3. Memory Architecture (VERIFIED)

### Stack Change: BGE-small-en-v1.5 over all-MiniLM-L6-v2
| Model | MTEB | Dims | INT8 Size | Reason |
|-------|------|------|-----------|--------|
| all-MiniLM-L6-v2 | ~56 | 384 | ~23MB | Previous recommendation |
| **BGE-small-en-v1.5** | **~62** | 384 | **~32MB** | **10% better retrieval** |

### sqlite-vec v0.1.6 (Verified)
- Filtered vector search NOW SUPPORTED
- Brute-force KNN only (no ANN) - fine for <500K vectors
- 30MB RAM overhead

### Schema
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE semantic_memory (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding BLOB
);

CREATE VIRTUAL TABLE vec_semantic USING vec0(
    memory_id INTEGER PRIMARY KEY,
    embedding float[384],
    user_id TEXT PARTITION KEY
);

CREATE VIRTUAL TABLE fts_memory USING fts5(
    content,
    tokenize = 'porter unicode61'
);
```

### Hybrid Search with RRF (60% vector, 40% FTS)
```sql
WITH vec_matches AS (...), fts_matches AS (...)
SELECT memory_id,
    (COALESCE(1.0/(60 + fts_rank), 0) * 0.4 +
     COALESCE(1.0/(60 + vec_rank), 0) * 0.6) AS score
...
```

### Performance at 100K Records
- Hybrid search: **<75ms**
- Storage: **500-700MB**
- Scale limit: **500K records** before considering LanceDB

---

## 4. Voice Pipeline (VERIFIED)

### STT Options (Choose Based on Need)
| Model | VRAM | Latency | WER | Best For |
|-------|------|---------|-----|----------|
| **Moonshine Base** | ~1.2GB | <700ms | 10.1% | Speed, edge |
| **faster-whisper turbo INT8** | ~1.5GB | ~1.5s | **1.9%** | Accuracy |

**Recommendation:** Start with Moonshine Base for responsiveness. Switch to turbo if accuracy issues.

### TTS: Kokoro-82M (Verified #1 on TTS Arena)
```bash
pip install kokoro-onnx
```
- Latency: <300ms on GPU
- RAM: ~500MB
- License: Apache 2.0
- Streaming: Yes

**Fallback:** Piper TTS for CPU-only (<256MB RAM)

### VAD: Silero v6.2 (Verified)
```python
threshold = 0.5
min_speech_duration_ms = 250
min_silence_duration_ms = 400  # Key tuning parameter
speech_pad_ms = 100
```

### Realistic Latency Budget
| Component | Optimistic | Realistic | Pessimistic |
|-----------|------------|-----------|-------------|
| VAD silence | 300ms | 400ms | 600ms |
| STT | 500ms (Moonshine) | 1.2s (turbo) | 2.0s |
| LLM (Haiku TTFT) | 300ms | 500ms | 800ms |
| TTS (first audio) | 300ms | 400ms | 700ms |
| Audio I/O | 100ms | 200ms | 500ms |
| **TOTAL** | **1.5s** | **2.7s** | **4.6s** |

**Sub-3s achievable** with Moonshine + Kokoro + hybrid audio architecture.

---

## 5. External Knowledge (VERIFIED)

### Budget Stack: $12-20/month
| Service | Cost | Use |
|---------|------|-----|
| **Exa.ai** | ~$15/month | Code search, neural search |
| **Jina Reader** | $0 (10M free tokens) | Documentation conversion |
| **DevDocs (self-hosted)** | $0 | Framework docs |
| **GitHub API** | $0 | Targeted code search |
| **Stack Overflow** | $0 | Q&A (10K req/day) |

### Caching TTLs
```python
CACHE_TTL = {
    'api_documentation': 48 * 3600,  # 48 hours
    'package_metadata': 4 * 3600,    # 4 hours
    'code_examples': 72 * 3600,      # 72 hours
    'stackoverflow': 2 * 3600,       # 2 hours
}
```

Expected cache hit rate at steady state: **75-85%**

---

## 6. Agent Architecture (VERIFIED)

### Framework Decision
| Option | Status | Recommendation |
|--------|--------|----------------|
| LangGraph | Enterprise-proven (LinkedIn, Uber) | Use for complex workflows |
| CrewAI | $18M funded, 450M agents/month | Use for rapid prototyping |
| AutoGen | **DEPRECATED** | **AVOID** |
| Claude native | Built-in | **Start here** |

**Recommendation:** Start with Claude native subagents. Add LangGraph only if complexity demands.

### MCP Security (CRITICAL)
MCP has documented vulnerabilities (prompt injection, tool poisoning). **Mandatory:**
- Run MCP servers in containers
- Treat as untrusted third-party code
- Human-in-the-loop for sensitive operations
- Monitor for tool definition changes

### Self-Correction Reality
> "No prior work demonstrates successful self-correction with feedback from prompted LLMs" - TACL 2024

**What works:**
- Self-consistency sampling (5 samples, vote)
- Tool-assisted verification (code execution, tests)
- External validation (linters, type checkers)

**Skip:** Asking LLM to "check its work" without external grounding

---

## 7. RAM Budget (VERIFIED)

### Component Breakdown
| Component | RAM | Notes |
|-----------|-----|-------|
| WSL2 kernel | ~300MB | Fixed |
| Python + libraries | ~200MB | Base |
| BGE-small-en-v1.5 (ONNX) | ~100MB | Embedding model |
| sqlite-vec + FTS5 | ~100MB | At 100K records |
| Silero VAD | ~50MB | Minimal |
| Kokoro TTS | ~500MB | On GPU = less RAM |
| faster-whisper/Moonshine | ~500MB | System RAM (model on GPU) |
| MCP Server | ~150MB | Unified |
| **TOTAL** | **~1.9GB** | Leaves 4GB+ headroom |

### VRAM Budget (4GB)
| Component | VRAM |
|-----------|------|
| Moonshine Base OR faster-whisper turbo | ~1.5GB |
| Kokoro-82M | ~300MB |
| Display | ~300MB |
| **Headroom** | **~1.9GB** |

---

## 8. Build Priority

### P0: MVP (Week 1-2)
1. Apply WSL2 optimizations (DoSvc fix, .wslconfig)
2. SQLite + sqlite-vec + FTS5 memory system
3. BGE-small-en-v1.5 embeddings (ONNX)
4. Moonshine STT + Piper TTS (simpler first)
5. Single MCP server (STDIO)
6. Basic PreToolUse safety hook

### P1: Core Experience (Week 3-4)
7. Upgrade to Kokoro TTS (GPU)
8. Claude Haiku streaming with prompt caching
9. Exa.ai + Jina Reader integration
10. Hybrid search (RRF fusion)
11. Nightly memory consolidation

### P2: Enhanced (Week 5+)
12. Hybrid audio architecture (Windows capture)
13. faster-whisper turbo for accuracy mode
14. Adaptive reflection system
15. Custom subagents

---

## 9. Files to Create

```
/home/squiz/ATLAS/
├── atlas/
│   ├── __init__.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── store.py          # SQLite + sqlite-vec
│   │   ├── embeddings.py     # BGE-small-en-v1.5 ONNX
│   │   └── search.py         # Hybrid RRF search
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt.py            # Moonshine/faster-whisper
│   │   ├── tts.py            # Kokoro/Piper
│   │   └── vad.py            # Silero
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── memory_server.py  # FastMCP memory tools
│   └── knowledge/
│       ├── __init__.py
│       ├── exa.py            # Exa.ai client
│       └── cache.py          # SQLite cache
├── .claude/
│   ├── settings.json         # Hooks configuration
│   └── hooks/
│       └── validate-bash.py  # Safety hook
├── config/
│   └── voice-persona.md      # Already exists
└── scripts/
    └── optimize_wsl.ps1      # Windows optimization
```

---

## 10. Verification Checklist

Before starting implementation:

- [ ] Apply DoSvc fix and verify RAM freed
- [ ] Create .wslconfig and restart WSL
- [ ] Verify `nvidia-smi` works in WSL2
- [ ] Test audio with `aplay /usr/share/sounds/alsa/Front_Center.wav`
- [ ] Install `claude-agent-sdk` (new package name)
- [ ] Verify sqlite-vec installs: `pip install sqlite-vec`
- [ ] Test BGE-small download: `sentence-transformers` package

---

## Summary

**We are ready to build ATLAS.** The research phase is complete with high-confidence architectural decisions validated across 24 research documents from both Gemini and Opus.

The architecture is:
- **Feasible** within 6GB RAM constraint
- **Well-validated** with specific numbers and benchmarks
- **Incrementally buildable** with clear P0→P2 priorities
- **Future-proof** with migration paths (LanceDB, more RAM)

**Next step:** Begin P0 implementation with integrated technical + persona architecture.

---

## 11. Persona System Architecture (R16-R21 COMPLETE)

### The Integrated Persona Stack

```
┌──────────────────────────────────────────────────────────────────┐
│                    ATLAS PERSONA SYSTEM                          │
├──────────────────────────────────────────────────────────────────┤
│  R17: PHILOSOPHICAL FOUNDATION                                   │
│  - Stoicism + Dokkōdō as operating system                        │
│  - Dichotomy of Control as primary algorithm                     │
│  - Five compatible traditions (Stoic, Bushido, Aristotle,        │
│    Antifragility, Sun Tzu, Zen action)                          │
├──────────────────────────────────────────────────────────────────┤
│  R21: CHARACTER SPECIFICATION                                    │
│  - Lethal Gentleman: capable, refined, restrained                │
│  - "Power held in check signals greater capability"              │
│  - Speech patterns: direct, understated, no empty phrases        │
├──────────────────────────────────────────────────────────────────┤
│  R19: THREE-LAYER PERSONA ARCHITECTURE                           │
│  - Core Identity (unchanging): values, worldview, boundaries     │
│  - Character Expression (consistent): tone, 1-3 quirks, style    │
│  - Contextual Adaptation (flexible): mood response, relationship │
├──────────────────────────────────────────────────────────────────┤
│  R18: USER STATE MODELING                                        │
│  - 6 dimensions: valence, arousal, load, clarity, engagement,    │
│    receptivity                                                   │
│  - 5 modes: minimal, structured, challenging, philosophical,     │
│    listening                                                     │
├──────────────────────────────────────────────────────────────────┤
│  R16: CONTEXTUAL APPROPRIATENESS                                 │
│  - DARN-CAT framework for permission detection                   │
│  - Venting vs advice-seeking distinction                         │
│  - Default to listening under uncertainty                        │
├──────────────────────────────────────────────────────────────────┤
│  R20: SELF-IMPROVEMENT LOOP                                      │
│  - Performance self-assessment (implicit signals)                │
│  - Research monitoring (3-layer: RSS → filter → deep analysis)   │
│  - Human-in-the-loop governance (ATLAS proposes, human disposes) │
└──────────────────────────────────────────────────────────────────┘
```

### Core Unifying Principle

> **"Restraint as the master virtue"** - Wisdom only with permission. Philosophy influences WHAT is said, not decoration on HOW. The measure of success is recognizing when to be helpful vs when to offer depth.

### The 5 Interaction Modes (R18)

| Mode | Trigger State | Behavior |
|------|---------------|----------|
| **Minimal/Efficient** | User in flow | Brief, direct, no preamble |
| **Structured/Supportive** | User overwhelmed | Break into steps, scaffolding |
| **Motivational/Challenging** | User stuck/avoiding | OARS framework, change talk |
| **Reflective/Philosophical** | Meaning-seeking | Open questions, values |
| **Listening/Validating** | Venting, processing | Reflect emotions, don't fix |

### Lethal Gentleman Decision Matrix (R21)

| Context | Response |
|---------|----------|
| Genuine effort failing | Gentle redirection |
| Excuses or avoidance | Direct confrontation |
| Fear of challenge | Challenge with support |
| Defensive posture | Create safety first |
| Self-deception | Mirror reality clearly |
| Grief/genuine pain | Presence, not correction |
| Repeated same error | Increased directness |
| Success achieved | Acknowledge, raise bar |

### Speech Pattern Guidelines

**Use:**
- Definitive verbs: "is," "will," "requires"
- Short declarative sentences for impact
- Understated intensifiers: "rather," "quite"

**Eliminate:**
- Excessive superlatives
- Empty phrases ("Hope that helps!", "Great question!")
- Apologetic excess
- Exclamation marks
- Filler words

### Anti-Patterns (All Persona Files Agree)

1. Servile agreement - validating everything
2. Empty encouragement - "You've got this!" without specificity
3. Performative toughness - "alpha" posturing
4. Unsolicited lecturing - teaching when support needed
5. The Righting Reflex - jumping to solutions
6. Toxic positivity - "Everything happens for a reason"

### The Ultimate Test (R21)

> "Would someone leave this interaction feeling respected, challenged, and better equipped - even if they heard things they didn't want to hear?"

---

## 12. Updated Build Priority (Technical + Persona)

### P0: Foundation (Start Here)
1. Apply WSL2 optimizations (DoSvc fix, .wslconfig)
2. SQLite + sqlite-vec + FTS5 memory system
3. BGE-small-en-v1.5 embeddings (ONNX)
4. **Persona prompt template** (Lethal Gentleman foundation)
5. **User state tracking placeholders** (log for later analysis)
6. Moonshine STT + Piper TTS (simpler first)
7. Single MCP server (STDIO)
8. Basic PreToolUse safety hook

### P1: Core Experience
9. Upgrade to Kokoro TTS (GPU)
10. Claude Haiku streaming with prompt caching
11. **Mode selection logic** (5 modes based on state)
12. **Permission detection** (DARN-CAT signals)
13. Exa.ai + Jina Reader integration
14. Hybrid search (RRF fusion)
15. Nightly memory consolidation

### P2: Enhanced
16. Hybrid audio architecture (Windows capture)
17. faster-whisper turbo for accuracy mode
18. **Full state modeling** (6 dimensions)
19. **Self-improvement proposals** (research monitoring)
20. Adaptive reflection system
21. Custom subagents

---

## 13. The ATLAS Formula (Complete)

```
ATLAS = Technical Foundation (R1-R15)
        ├── Memory: SQLite + sqlite-vec + FTS5 + BGE-small
        ├── Voice: Moonshine/turbo + Kokoro + Silero VAD
        ├── Orchestration: Claude Agent SDK + MCP
        └── Knowledge: Exa.ai + Jina Reader + DevDocs

      + Persona System (R16-R21)
        ├── Philosophy: Stoicism + Dokkōdō (R17)
        ├── Character: Lethal Gentleman (R21)
        ├── Architecture: 3-layer persona (R19)
        ├── Adaptation: 6 states → 5 modes (R18)
        ├── Gating: Permission-based depth (R16)
        └── Evolution: Human-governed self-improvement (R20)
```

**All research complete. Ready for implementation.**
