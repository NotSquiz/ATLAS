# ATLAS Phase 0 Handover - Fresh Agent Prompt

Copy everything below the line to start a new Opus conversation.

---

## HANDOVER PROMPT

I'm building ATLAS, an autonomous AI life assistant. All research is complete (27 topics). I need help implementing **Phase 0: Foundation**.

### Project Location
```
/home/squiz/ATLAS/
```

### Key Documents (Read These First)
```
/home/squiz/ATLAS/docs/MASTER_PLAN.md           ← Architecture & decisions
/home/squiz/ATLAS/docs/research/ANALYSIS_R25-R27_IMPLEMENTATION.md  ← Code patterns
```

### Hardware Constraints
- **RAM:** 6GB allocated to WSL2 (on 16GB Windows 11)
- **VRAM:** 4GB (RTX 3050 Ti)
- **Platform:** WSL2 Ubuntu

### Phase 0 Tasks (In Order)

**1. WSL2 Optimizations**
- Fix DoSvc memory leak (PowerShell script on Windows side)
- Create/update `.wslconfig` with verified settings
- Verify `autoMemoryReclaim=dropcache`

**2. Ollama + Qwen2.5-3B-Instruct Setup**
```bash
# Environment variables (~/.bashrc)
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_PARALLEL=1

# Install and configure
ollama pull qwen2.5:3b-instruct
# Create ATLAS Modelfile (see MASTER_PLAN.md Section 2)
```

**3. Test Local LLM**
- Verify first token latency (~200-350ms target)
- Verify generation speed (~20-40 tok/s target)
- Verify VRAM usage (~2.0-2.5GB with KV cache)

**4. SQLite + sqlite-vec + FTS5**
- Create database schema (see MASTER_PLAN.md Section 3 & 9)
- Install sqlite-vec v0.1.6
- Test vector search works
- Create Blueprint tracking tables

**5. Basic MCP Server Skeleton**
- FastMCP-based unified server
- STDIO transport
- Placeholder tools for memory operations

### Critical Decisions Already Made
| Decision | Choice | Why |
|----------|--------|-----|
| Local LLM | Qwen2.5-3B-Instruct Q4_K_M | No thinking mode, ~2.0-2.5GB VRAM, stable |
| NOT Qwen3-4B | Mandatory thinking mode | R28 proved thinking mode cannot be disabled |
| STT | Moonshine on CPU | Reserve GPU for LLM |
| Memory reclaim | `dropcache` | `gradual` conflicts with Docker |

### File Structure to Create
```
/home/squiz/ATLAS/
├── atlas/
│   ├── __init__.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── store.py          # SQLite + sqlite-vec
│   │   └── schema.sql        # All tables
│   ├── llm/
│   │   ├── __init__.py
│   │   └── local.py          # Qwen2.5-3B via Ollama
│   └── mcp/
│       ├── __init__.py
│       └── server.py         # FastMCP skeleton
├── config/
│   └── .env.example
├── scripts/
│   └── optimize_wsl.ps1      # Windows optimization
├── pyproject.toml
└── README.md
```

### Success Criteria for Phase 0
- [ ] WSL2 using ~1.5-2GB idle (not 4GB+)
- [ ] `ollama run atlas-local` responds in <2 seconds
- [ ] `nvidia-smi` shows ~2.5GB VRAM during inference
- [ ] SQLite database created with all tables
- [ ] `python -c "import sqlite_vec"` works
- [ ] Basic MCP server starts without errors

### What NOT to Do in Phase 0
- Don't implement voice (STT/TTS) yet - that's Phase 1
- Don't integrate Garmin yet - that's Phase 1
- Don't add LangGraph yet - that's Phase 2
- Don't worry about the persona system yet - that's Phase 1

### Questions to Ask Me
- Do you have Ollama installed already?
- What's your current WSL2 memory usage? (`free -h`)
- Have you applied the DoSvc fix before?

Begin by reading the MASTER_PLAN.md, then let's start with WSL2 optimizations.
