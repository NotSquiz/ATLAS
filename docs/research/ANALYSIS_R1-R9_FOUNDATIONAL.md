# ATLAS Research Analysis: R1-R9 Foundational Documents

## Key Agreements Across Files

| Topic | Consensus | Files |
|-------|-----------|-------|
| **Embedding model** | all-MiniLM-L6-v2 (384 dims, ONNX int8) | R1, R6, R9 |
| **Vector DB** | SQLite (sqlite-vec) for constrained RAM | R1, R5, R6, R9 |
| **LLM for speed** | Claude 3.5 Haiku for latency-critical | R4, R7 |
| **Memory schema** | SQLite + FTS5 for hybrid search | R1, R2, R9 |
| **MCP transport** | STDIO only (no HTTP overhead) | R5, R7 |
| **WSL2 memory** | 6GB limit with autoMemoryReclaim=dropcache | R3, R5 |
| **Knowledge graph** | NetworkX for <5K nodes, pickle caching | R1, R6 |
| **Target latency** | Sub-3 second voice, 800-1500ms TTFA | R4 |

## Critical Numbers

| Constraint | Value | Source |
|------------|-------|--------|
| Usable RAM (after optimization) | 4-6GB | R3 |
| VRAM limit | 4GB | User |
| Voice latency target | <3s total, <1.8s TTFA | R4 |
| API budget | <$20/month | R8 |
| MCP server total memory | <600-700MB | R5 |
| Embedding latency | 10-15ms | R1 |
| Vector search (100K) | <5ms | R1 |

## Technology Stack (R1-R9)

| Component | Recommendation | Memory |
|-----------|----------------|--------|
| Embedding | all-MiniLM-L6-v2 ONNX int8 | 63MB |
| Vector DB | sqlite-vec | 30MB base |
| Text Search | FTS5 Porter stemmer | Minimal |
| Knowledge Graph | NetworkX (<5K nodes) | ~150KB |
| LLM (speed) | Claude 3.5 Haiku | API |
| STT | Moonshine tiny or faster-whisper base.en | ~1GB VRAM |
| TTS | Piper (CPU) or Kokoro (GPU) | 60MB-500MB |
| MCP Servers | Unified single-process | ~150MB |

## Gaps Identified

1. Local LLM integration details (Qwen, Llama)
2. Wake word detection implementation
3. Error recovery / graceful degradation
4. Testing strategy for ATLAS system
5. Startup time benchmarks
6. Backup/recovery procedures
7. Version upgrade strategy
