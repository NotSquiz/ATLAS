# ATLAS Research Analysis: R10-R15 Technical Verification

## Key Agreements

| Topic | Agreement | Files |
|-------|-----------|-------|
| **WSL2 Audio** | Do NOT install PipeWire - use PulseAudio | R11, R14 |
| **Audio Latency** | 50-200ms+ overhead from WSLg | R11, R14 |
| **Hybrid Audio** | Windows capture + WSL2 ML inference optimal | R11, R14 |
| **CUDA in WSL2** | 85-95% native performance, mature | R11, R14 |
| **SQLite** | Recommended for memory and caching | R12, R13 |
| **Memory Budget** | 4-6GB for AI workloads | R11, R12, R14 |
| **Silero VAD** | Production standard | R11, R15 |
| **MCP** | Universal standard, requires sandboxing | R10, R15 |
| **BGE-small-en-v1.5** | Recommended over all-MiniLM | R12, R15 |
| **autoMemoryReclaim** | Use dropcache, NOT gradual | R14 |

## Unified Stack Recommendation

| Component | Choice | Source |
|-----------|--------|--------|
| Orchestration | Claude Agent SDK + MCP | R10, R15 |
| Local LLM | Qwen 2.5 7B Q4_K_M | R15 |
| Cloud Fallback | Claude API | R10, R15 |
| Embedding | BGE-small-en-v1.5 (INT8) | R12 |
| Vector DB | sqlite-vec + FTS5 | R12 |
| Hybrid Search | RRF (60% vector, 40% FTS) | R12 |
| VAD | Silero VAD v6.2 | R11, R15 |
| STT (Local) | Moonshine Base or faster-whisper turbo | R11 |
| TTS (Local) | Kokoro-82M ONNX | R11 |
| Voice Framework | Pipecat | R15 |
| External APIs | Exa.ai + Jina Reader + DevDocs | R13 |
| WSL2 Config | 6GB memory, dropcache, sparseVhd | R14 |
| Critical Fix | Disable DoSvc service | R14 |

## Key Numbers

| Metric | Value | Source |
|--------|-------|--------|
| Hybrid search latency (100K) | <75ms | R12 |
| FTS5 query | <10ms | R12 |
| BGE-small MTEB | ~62 | R12 |
| Jina Reader free tier | 10M tokens | R13 |
| Cache hit rate (steady) | 75-85% | R13 |
| Budget-optimized APIs | $12-20/month | R13 |
| WSL2 GPU performance | 85-95% native | R14 |
| DoSvc leak range | 200MB to 20GB | R14 |
| Claude Code process RAM | 1.5-2GB base | R10 |
| Realistic voice E2E | ~3.0s | R11 |

## Configuration Snippets

### .wslconfig
```ini
[wsl2]
memory=6GB
processors=6
swap=4GB
pageReporting=true

[experimental]
autoMemoryReclaim=dropcache
sparseVhd=true
```

### Silero VAD
```python
threshold = 0.5
min_speech_duration_ms = 250
min_silence_duration_ms = 400
speech_pad_ms = 100
```

### Cache TTLs
```python
CACHE_TTL = {
    'api_documentation': 48 * 3600,
    'package_metadata': 4 * 3600,
    'code_examples': 72 * 3600,
    'stackoverflow': 2 * 3600,
}
```
