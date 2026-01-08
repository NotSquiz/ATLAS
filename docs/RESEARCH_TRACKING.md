# ATLAS Research Tracking

**Started:** January 4, 2026
**Status:** Research in progress

---

## Quick Search Baseline (January 2026)

These are baseline findings from web search. Deep research agents will provide more detail.

### CRITICAL NEW FINDING: Claude Code SDK Renamed

| Item | Finding | Source |
|------|---------|--------|
| **SDK Rename** | Claude Code SDK → **Claude Agent SDK** | [Agent SDK Docs](https://docs.claude.com/en/api/agent-sdk/overview) |
| **Headless Mode** | `-p` or `--print` flag confirmed | [Headless Docs](https://code.claude.com/docs/en/headless) |
| **Auth Options** | Bedrock, Vertex AI, Foundry supported | SDK docs |
| **Built-in Features** | Subagents, Skills, Hooks, Slash Commands, Plugins | SDK docs |

---

### CRITICAL NEW FINDING: WSL2 zswap Configuration

Specific `.wslconfig` for optimal memory with zswap:

```ini
[wsl2]
memory=6GB
swap=8GB
kernelCommandLine="zswap.enabled=1 zswap.shrinker_enabled=1 zswap.compressor=zstd zswap.zpool=zsmalloc vm.swappiness=133"

[experimental]
autoMemoryReclaim=dropCache
sparseVhd=true
```

| Setting | Value | Reason |
|---------|-------|--------|
| autoMemoryReclaim | `dropCache` NOT `gradual` | gradual conflicts with zswap |
| swappiness | 133 | Aggressive compression, prioritizes cache |
| compressor | zstd | Good balance speed/ratio |

Source: [Whitewater Foundry](https://www.whitewaterfoundry.com/blog/2025/3/7/get-more-from-less-how-zswap-optimizes-memory-in-wsl2)

---

### CRITICAL NEW FINDING: Moonshine ONNX Package

| Item | Finding | Source |
|------|---------|--------|
| **Recommended Package** | `moonshine-onnx` (not keras moonshine) | [GitHub](https://github.com/moonshine-ai/moonshine) |
| **Install** | `pip install useful-moonshine-onnx` | Same |
| **Tiny Size** | 27M params, ~190MB | Same |
| **Base Size** | 62M params, ~400MB | Same |
| **Speed** | 5-15x faster than Whisper | Same |
| **License** | MIT (models + code) | Same |
| **2025 Paper** | "Flavors of Moonshine" arXiv:2509.02523 | arXiv |

**Action:** Moonshine-ONNX is the clear winner for our edge constraint.

### MCP Protocol - CURRENT STATE

| Item | Finding | Source |
|------|---------|--------|
| **Latest Spec Version** | **2025-11-25** (November 25, 2025) | [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25) |
| **Governance** | Donated to Linux Foundation's Agentic AI Foundation (December 2025) | Wikipedia |
| **Co-founders** | Anthropic, Block, OpenAI | Wikipedia |
| **New Feature: Tasks** | New abstraction for tracking work performed by MCP servers | Blog |
| **Previous Version** | 2025-06-18 (OAuth auth, structured outputs, elicitation) | Spec history |

**Action:** Our research assumed older MCP - need to review 2025-11-25 spec changes.

---

### WSL2 Memory - 2026 UPDATE

| Item | Finding | Source |
|------|---------|--------|
| **autoMemoryReclaim** | `gradual` may **CONFLICT with zswap** (new finding!) | [Whitewater Foundry](https://www.whitewaterfoundry.com/blog/2025/12/2/get-more-from-less-how-zswap-optimizes-memory-in-wsl2-2026-update) |
| **Recommended Mode** | `dropcache` has shown no issues | Same source |
| **WSL2 Kernel** | Now 6.x with new module VHDX architecture | Same source |
| **zswap** | New optimization - reduces SSD wear, improves performance | Same source |
| **Memory reclaim rate** | Fixed portion calculated to zero cache after 30 minutes | Microsoft DevBlog |

**Action:** Our synthesis said `gradual` - may need to switch to `dropcache`. Need to investigate zswap configuration.

---

### STT Models - 2025/2026 Landscape

| Model | Speed | Accuracy (WER) | Best For | Source |
|-------|-------|----------------|----------|--------|
| **Moonshine Tiny** | 5x faster than Whisper | 12.81% | Edge devices, real-time | [arXiv](https://arxiv.org/html/2410.15608v1) |
| **Moonshine Base** | 5x faster | Better than Tiny | Edge with more resources | Same |
| **faster-whisper** | 4x faster than OpenAI | Same as Whisper | Server/desktop | [GitHub](https://github.com/SYSTRAN/faster-whisper) |
| **Canary Qwen 2.5B** | - | High accuracy | English, strict accuracy | [Northflank](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2025-benchmarks) |
| **IBM Granite Speech 3.3 8B** | - | High accuracy | English, strict accuracy | Same |
| **Parakeet TDT** | Low latency | - | Streaming | Same |
| **Distil-Whisper** | Low latency | - | Streaming | Same |

**Key Insight:** Moonshine 27M params vs Whisper Tiny 37M - smaller AND faster. Best for our edge use case.

**Action:** Moonshine may be better choice than faster-whisper for our constraint. Need deep research benchmarks.

---

### sqlite-vec - Current State

| Item | Finding | Source |
|------|---------|--------|
| **Latest Version** | v0.1.5+ (metadata filtering added) | [GitHub](https://github.com/asg017/sqlite-vec) |
| **Status** | Active development, Mozilla Builders sponsor | Same |
| **Community Fork** | [vlasky/sqlite-vec](https://github.com/vlasky/sqlite-vec) - merges pending PRs | GitHub |
| **New Feature** | Metadata columns in vec0 virtual tables | Release notes |

**Action:** Confirm metadata filtering syntax for filtered vector search.

---

## Deep Research Results

### Prompt 1: Claude Code & MCP

| Agent | Status | Key Findings | Conflicts |
|-------|--------|--------------|-----------|
| Gemini | [ ] Pending | | |
| Opus | [ ] Pending | | |

**Consensus:**

**Conflicts to resolve:**

**Action items:**

---

### Prompt 2: Voice Pipeline

| Agent | Status | Key Findings | Conflicts |
|-------|--------|--------------|-----------|
| Gemini | [ ] Pending | | |
| Opus | [ ] Pending | | |

**Consensus:**

**Conflicts to resolve:**

**Action items:**

---

### Prompt 3: SQLite Memory

| Agent | Status | Key Findings | Conflicts |
|-------|--------|--------------|-----------|
| Gemini | [ ] Pending | | |
| Opus | [ ] Pending | | |

**Consensus:**

**Conflicts to resolve:**

**Action items:**

---

### Prompt 4: External APIs

| Agent | Status | Key Findings | Conflicts |
|-------|--------|--------------|-----------|
| Gemini | [ ] Pending | | |
| Opus | [ ] Pending | | |

**Consensus:**

**Conflicts to resolve:**

**Action items:**

---

### Prompt 5: Windows/WSL2

| Agent | Status | Key Findings | Conflicts |
|-------|--------|--------------|-----------|
| Gemini | [ ] Pending | | |
| Opus | [ ] Pending | | |

**Consensus:**

**Conflicts to resolve:**

**Action items:**

---

### Prompt 6: Cutting Edge

| Agent | Status | Key Findings | Conflicts |
|-------|--------|--------------|-----------|
| Gemini | [ ] Pending | | |
| Opus | [ ] Pending | | |

**Consensus:**

**Conflicts to resolve:**

**Action items:**

---

## Synthesis Updates Required

Based on quick search, these items in RESEARCH_SYNTHESIS.md need updating:

| Item | Current Value | May Need Update To | Confidence |
|------|---------------|-------------------|------------|
| autoMemoryReclaim | `gradual` | `dropcache` (zswap conflict) | HIGH - verify |
| MCP spec version | Not specified | `2025-11-25` | CONFIRMED |
| STT recommendation | faster-whisper | Moonshine (for edge) | MEDIUM - need benchmarks |
| WSL2 kernel | Not specified | 6.x | CONFIRMED |
| zswap | Not mentioned | Add to config | NEW finding |

---

## Research Completion Checklist

- [ ] All 6 prompts run through Gemini
- [ ] All 6 prompts run through Opus
- [ ] Results compared for conflicts
- [ ] RESEARCH_SYNTHESIS.md updated with verified info
- [ ] NEEDS_VERIFICATION.md items resolved
- [ ] Final VERIFIED_ARCHITECTURE.md created
- [ ] Ready for implementation
