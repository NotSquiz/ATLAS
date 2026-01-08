# ATLAS Master Implementation Guide
## Synthesized from R1-R6 Research (Opus + Gemini)

> **Generated:** January 2026
> **Hardware:** ThinkPad X1 Extreme Gen 4i, 16GB RAM, RTX 3050 Ti 4GB VRAM

---

## Quick Reference: Critical Numbers

| Parameter | Value | Source |
|-----------|-------|--------|
| Windows optimized baseline | ~6-7GB | R3 |
| WSL2 memory limit | 6GB | R3 |
| ATLAS total RAM budget | ~1GB | R1 |
| all-MiniLM-L6-v2 INT8 | 22MB model, 50MB RAM | R1 |
| Whisper base.en INT8 | 0.5-1.0s latency | R4 |
| Voice pipeline target | <1.8s end-to-end | R4 |
| MCP per-server overhead | 35-45MB (STDIO) | R5 |
| sqlite-vec query latency | <1ms for 100K records | R1 |
| Confidence threshold (adaptive) | 0.5-0.7 | R2 |

---

## Part 1: Windows Optimization (R3)

### 1.1 Services to Disable (Admin PowerShell)

```powershell
#Requires -RunAsAdministrator

# Create restore point first
Checkpoint-Computer -Description "Before ATLAS Optimization" -RestorePointType MODIFY_SETTINGS

# Critical: NDU memory leak fix
Set-ItemProperty -Path "HKLM:\SYSTEM\ControlSet001\Services\Ndu" -Name "Start" -Value 4

# Disable memory-heavy services
$services = @("DoSvc","SysMain","WSearch","DiagTrack","dmwappushservice","WerSvc","diagsvc","MapsBroker","PcaSvc")
foreach ($svc in $services) {
    Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
    Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
    Write-Host "[OK] Disabled: $svc" -ForegroundColor Green
}
```

**Expected savings:** 400MB-1.5GB

### 1.2 WSL2 Configuration

Create `C:\Users\[Username]\.wslconfig`:

```ini
[wsl2]
memory=6GB
swap=4GB
swapFile=C:\\Temp\\wsl-swap.vhdx
processors=8
gpuSupport=true
pageReporting=true

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
networkingMode=mirrored
```

Run `wsl --shutdown` and wait 8 seconds before restart.

### 1.3 Registry Tweaks

```powershell
# Processor scheduling for IDE responsiveness
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl" -Name "Win32PrioritySeparation" -Value 38

# Reduce background reservation from 20% to 10%
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" -Name "SystemResponsiveness" -Value 10
```

### 1.4 DO NOT DISABLE

- **TabletInputService** - Breaks Windows Terminal
- **NlaSvc** - Breaks network status
- **Lenovo Vantage** - Set to Manual (needed for BIOS updates)

---

## Part 2: SQLite Memory Schema (R1)

### 2.1 Core Tables

```sql
-- ~/ATLAS/data/memory.db

-- Episodic memory (all interactions)
CREATE TABLE episodic_memory (
    id INTEGER PRIMARY KEY,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    token_count INTEGER,
    importance REAL DEFAULT 5.0,
    analysis TEXT  -- JSON: {confidence, domain, lesson}
);

-- Semantic memory (consolidated facts)
CREATE TABLE semantic_memory (
    id INTEGER PRIMARY KEY,
    concept TEXT NOT NULL,
    description TEXT NOT NULL,
    domain TEXT,
    source_episode_ids TEXT,  -- JSON array
    recall_count INTEGER DEFAULT 0,
    stability REAL DEFAULT 2.5,  -- SM-2 EF factor
    last_recalled DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(concept, domain)
);

-- Semantic edges (relationships)
CREATE TABLE semantic_edges (
    source_id INTEGER REFERENCES semantic_memory(id),
    target_id INTEGER REFERENCES semantic_memory(id),
    relationship TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    PRIMARY KEY (source_id, target_id, relationship)
);

-- Lessons learned (RLAIF)
CREATE TABLE lessons (
    id INTEGER PRIMARY KEY,
    trigger_embedding BLOB,  -- 384-dim float32
    original_query TEXT,
    bad_response TEXT,
    good_response TEXT,
    critique_summary TEXT,
    application_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Reflection logs
CREATE TABLE reflections (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    reflection_type TEXT,  -- lightweight, adaptive, nightly, weekly
    trigger TEXT,
    insights TEXT,
    memory_updates TEXT,  -- JSON
    constitution_check BOOLEAN DEFAULT 1
);

-- FTS5 index (external content for 40-50% size reduction)
CREATE VIRTUAL TABLE episodic_fts USING fts5(
    content,
    content='episodic_memory',
    content_rowid='id',
    tokenize='trigram'
);

-- Vector tables (sqlite-vec)
CREATE VIRTUAL TABLE vec_episodic USING vec0(
    embedding float[384]
);

CREATE VIRTUAL TABLE vec_semantic USING vec0(
    embedding float[384]
);

-- Triggers for FTS sync
CREATE TRIGGER episodic_ai AFTER INSERT ON episodic_memory BEGIN
    INSERT INTO episodic_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER episodic_ad AFTER DELETE ON episodic_memory BEGIN
    INSERT INTO episodic_fts(episodic_fts, rowid, content) VALUES('delete', old.id, old.content);
END;

-- Indexes
CREATE INDEX idx_episodic_timestamp ON episodic_memory(timestamp);
CREATE INDEX idx_episodic_session ON episodic_memory(session_id);
CREATE INDEX idx_semantic_domain ON semantic_memory(domain);
CREATE INDEX idx_semantic_recall ON semantic_memory(recall_count);
```

### 2.2 Embedding Model Setup

```python
# ~/ATLAS/bin/embedder.py
import onnxruntime as ort
from tokenizers import Tokenizer
import numpy as np

class LightweightEmbedder:
    """22MB model, 50MB RAM, 2-5ms latency"""

    def __init__(self, model_path="models/all-MiniLM-L6-v2-int8.onnx",
                 tokenizer_path="models/tokenizer.json"):
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.session = ort.InferenceSession(
            model_path,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )

    def embed(self, text: str) -> np.ndarray:
        encoded = self.tokenizer.encode(text)
        inputs = {
            'input_ids': np.array([encoded.ids], dtype=np.int64),
            'attention_mask': np.array([encoded.attention_mask], dtype=np.int64),
            'token_type_ids': np.array([encoded.type_ids], dtype=np.int64)
        }

        outputs = self.session.run(None, inputs)

        # Mean pooling
        last_hidden = outputs[0]
        mask = np.expand_dims(inputs['attention_mask'], axis=-1)
        masked = last_hidden * mask
        summed = masked.sum(axis=1)
        counted = np.clip(mask.sum(axis=1), 1e-9, None)
        embedding = summed / counted

        # L2 normalize
        norm = np.linalg.norm(embedding)
        return (embedding / norm).flatten()
```

### 2.3 Hybrid Search (FTS5 + Vector)

```python
def hybrid_search(query: str, query_embedding: np.ndarray, conn, k: int = 10):
    """Reciprocal Rank Fusion of keyword + semantic search"""

    # FTS5 keyword search
    fts_results = conn.execute("""
        SELECT rowid, bm25(episodic_fts) as score
        FROM episodic_fts WHERE episodic_fts MATCH ?
        LIMIT ?
    """, (query, k * 3)).fetchall()

    # Vector similarity search
    vec_results = conn.execute("""
        SELECT rowid, distance FROM vec_episodic
        WHERE embedding MATCH ? AND k = ?
    """, (query_embedding.tobytes(), k * 3)).fetchall()

    # RRF fusion (k=60)
    rrf_scores = {}
    for rank, (idx, _) in enumerate(fts_results, 1):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (60 + rank)
    for rank, (idx, _) in enumerate(vec_results, 1):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (60 + rank)

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:k]
```

---

## Part 3: Reflection & Learning Schedule (R2)

### 3.1 Four-Tier Reflection System

| Tier | Trigger | Budget | Model |
|------|---------|--------|-------|
| Lightweight | Every interaction | 300 tokens, <500ms | Haiku |
| Adaptive | Confidence < 0.5, failure | 500 tokens, 2-3 turns | Sonnet |
| Nightly | 10pm cron | 4000 tokens | Sonnet |
| Weekly | Sunday 8pm | 8000 tokens | Sonnet |

### 3.2 Confidence Scoring

```python
def compute_confidence(response, history, embedder) -> float:
    """Composite confidence score"""

    weights = {
        'verbalized': 0.2,      # Did model express uncertainty?
        'consistency': 0.3,     # Self-consistency across samples
        'ood': 0.2,             # Out-of-distribution detection
        'user_signal': 0.3      # User corrections/undos
    }

    scores = {}

    # Verbalized confidence (regex for hedge words)
    hedge_words = ['perhaps', 'maybe', 'might', 'not sure', 'uncertain']
    scores['verbalized'] = 1.0 - (sum(w in response.lower() for w in hedge_words) * 0.15)

    # Self-consistency (3 samples at temp=0.7)
    # scores['consistency'] = average_pairwise_similarity(samples)

    # OOD detection (Mahalanobis distance from historical embeddings)
    # scores['ood'] = 1.0 if distance < 3.0 else 0.5

    # User signal (track corrections, undos)
    # scores['user_signal'] = 1.0 - (corrections / total_responses)

    return sum(weights[k] * scores.get(k, 0.5) for k in weights)
```

### 3.3 Memory Consolidation (Episodic → Semantic)

Promote when 3+ of 5 criteria met:
1. Access frequency >= 3 in different contexts
2. Cross-referenced to >= 2 semantic memories
3. Same insight from multiple episodes
4. Age > 7 days
5. Successfully applied >= 2 times

### 3.4 Spaced Repetition (SM-2)

```python
def update_stability(memory, recall_quality: int):
    """recall_quality: 0-5 (0=complete failure, 5=perfect)"""
    if recall_quality >= 3:
        memory.stability = memory.stability * (1.3 - 0.1 * (5 - recall_quality))
        memory.recall_count += 1
    else:
        memory.stability = 2.5  # Reset
    memory.last_recalled = datetime.now()
```

---

## Part 4: Voice Pipeline Optimization (R4)

### 4.1 Whisper Settings

```python
from faster_whisper import WhisperModel

model = WhisperModel(
    "base.en",                      # Or "tiny.en" for speed
    device="cuda",                  # GPU essential
    compute_type="int8"             # 2x throughput
)

segments, _ = model.transcribe(
    audio,
    beam_size=1,                    # Greedy: 2-3x speedup
    language="en",
    vad_filter=True,
    vad_parameters={
        "min_silence_duration_ms": 300,
        "speech_pad_ms": 100,
        "threshold": 0.5
    },
    condition_on_previous_text=False,
    word_timestamps=False
)
```

### 4.2 Kokoro TTS Optimization

```python
import onnxruntime as ort

sess_options = ort.SessionOptions()
sess_options.intra_op_num_threads = 4
sess_options.inter_op_num_threads = 1
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
sess_options.enable_mem_pattern = True

session = ort.InferenceSession(
    "kokoro-v1.0.onnx",
    sess_options,
    providers=['CUDAExecutionProvider']  # 25-50x real-time
)
```

### 4.3 Streaming Pipeline

```python
async def process_llm(query):
    """Stream LLM → dispatch sentences to TTS immediately"""
    async with claude.messages.stream(
        max_tokens=150,
        model="claude-3-5-haiku-20241022"
    ) as stream:
        sentence_buffer = ""
        async for token in stream.text_stream:
            sentence_buffer += token
            if token in ".!?;":
                await tts_queue.put(sentence_buffer)
                sentence_buffer = ""
```

### 4.4 Pre-Warming

```python
# At startup - eliminates 2-3s cold start
await asyncio.to_thread(stt.transcribe, np.zeros(16000), beam_size=1)
await asyncio.to_thread(tts.create, "Ready", voice="bm_lewis")
```

### 4.5 Target Latencies

| Component | Current | Optimized |
|-----------|---------|-----------|
| STT | 2-4s | 0.4-0.5s |
| LLM TTFT | 3-8s | 0.36-0.5s |
| TTS | 1-3s | 0.2-0.4s |
| **Total** | **6-15s** | **~1.45s** |

---

## Part 5: MCP Integration (R5)

### 5.1 Claude CLI MCP Commands

```bash
# Add servers
claude mcp add --transport stdio calendar -- python ~/ATLAS/mcp/calendar_server.py
claude mcp add --transport stdio garmin -- python ~/ATLAS/mcp/garmin_server.py

# Check status
/mcp

# Test individual tools
claude mcp call garmin get_health_metrics --arg target_date=2025-01-04
```

### 5.2 Minimal MCP Server Template

```python
# ~/ATLAS/mcp/template_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MyTools")

@mcp.tool()
def my_tool(arg: str) -> str:
    """Tool description for LLM routing."""
    return f"Result: {arg}"

if __name__ == "__main__":
    mcp.run()  # STDIO transport, 35-45MB RAM
```

### 5.3 OAuth Patterns

**Google Calendar:**
1. Run `setup_auth.py` once (browser required)
2. Saves `token.json` with refresh token
3. Runtime: auto-refreshes silently

**Garmin:**
1. Run `garth.login(email, password)` once
2. Saves session to `~/.garminconnect`
3. Runtime: `garth.resume()` (tokens last 1 year)

### 5.4 Memory Footprint

| Server | Docker | STDIO Native |
|--------|--------|--------------|
| Calendar | 80MB | 35MB |
| Garmin | 90MB | 45MB |
| Knowledge Graph | 70MB | 30MB |
| **Total** | **240MB** | **110MB** |

---

## Part 6: Knowledge Graph (R6)

### 6.1 File Structure

```
knowledge_graph/
├── montessori_graph.jsonl       # Compiled YAML → JSONL
├── montessori_graph.idx         # Byte-offset index
├── health_data.jsonl
└── embeddings/
    ├── vectors.npy
    └── node_ids.json
```

### 6.2 LazyNode Pattern

```python
class LazyNode:
    """Memory-efficient: only loads data when accessed"""

    def __init__(self, node_id, loader):
        self.id = node_id
        self._loader = loader
        self._cache = None

    @property
    def data(self):
        if self._cache is None:
            self._cache = self._loader.fetch(self.id)
        return self._cache

    @property
    def neighbors(self):
        for nid in self.data.get('edges', []):
            yield LazyNode(nid, self._loader)
```

### 6.3 Hybrid Search (Vector + Graph)

1. **Stage 1:** LanceDB semantic search → top-K candidates
2. **Stage 2:** Graph filter (prerequisites, relationships)
3. **Stage 3:** Rank survivors by vector similarity

### 6.4 Performance

| Operation | 150 nodes | 500 nodes | 1000 nodes |
|-----------|-----------|-----------|------------|
| JSONL load | 50-100ms | 100-200ms | 200-500ms |
| BFS (3 hops) | <1ms | 1-2ms | 2-5ms |
| Semantic search | 1-5ms | 1-5ms | 1-5ms |

---

## Part 7: Constitution & Principles

### 7.1 Core Principles

```json
{
  "principles": [
    "Prioritize long-term user utility over short-term agreement",
    "Admit uncertainty rather than guess",
    "Challenge self-destructive patterns respectfully",
    "Never optimize for praise at expense of accuracy",
    "Maintain honesty even when unwelcome",
    "Respect user autonomy in all decisions",
    "Verify outcomes via observable data"
  ],
  "forbidden_patterns": [
    "Excessive enthusiasm or flattery",
    "Pretending capabilities don't exist",
    "Gaming metrics by avoiding difficult tasks",
    "Confirming beliefs without evidence"
  ]
}
```

### 7.2 Sycophancy Detection

```python
def detect_sycophancy(responses, challenges):
    """Track flip rate when user pushes back"""
    flip_rate = sum(
        1 for r in responses
        if r.changed_after_challenge
    ) / len(challenges)

    if flip_rate > 0.2:  # Alert threshold
        log_warning("Sycophancy detected", flip_rate)
```

---

## Implementation Checklist

### Phase 0: Windows Optimization (Day 1-2)
- [ ] Run PowerShell service optimization script
- [ ] Create .wslconfig
- [ ] Apply registry tweaks
- [ ] Install Process Explorer, RAMMap
- [ ] Verify 5-6GB available

### Phase 1: Memory Foundation (Week 1-2)
- [ ] Create memory.db with schema
- [ ] Download all-MiniLM-L6-v2 INT8 ONNX
- [ ] Implement LightweightEmbedder
- [ ] Create core_memory.json
- [ ] Create constitution.json
- [ ] Implement hybrid_search()

### Phase 2: Voice Optimization (Week 3-4)
- [ ] Switch to Whisper base.en with beam_size=1
- [ ] Add CUDA provider to Kokoro
- [ ] Implement streaming LLM → TTS
- [ ] Add pre-warming at startup
- [ ] Measure latency improvements

### Phase 3: Reflection System (Week 5-6)
- [ ] Implement confidence scoring
- [ ] Add per-interaction lightweight reflection
- [ ] Create nightly consolidation job
- [ ] Implement lesson extraction

### Phase 4: MCP Integration (Week 7-8)
- [ ] Create calendar_server.py
- [ ] Create garmin_server.py
- [ ] Register with Claude CLI
- [ ] Test tool routing

### Phase 5: Knowledge Graph (Week 9-10)
- [ ] Build YAML → JSONL compiler
- [ ] Create byte-offset index
- [ ] Implement LazyNode traversal
- [ ] Add LanceDB vector search

---

## Quick Command Reference

```bash
# Windows (Admin PowerShell)
wsl --shutdown                    # Restart WSL2 after config changes

# WSL2 (ATLAS)
source ~/ATLAS/venv/bin/activate
export PULSE_SERVER=unix:/mnt/wslg/PulseServer
python ~/ATLAS/bin/atlas_voice.py

# MCP
claude mcp add --transport stdio garmin -- python ~/ATLAS/mcp/garmin_server.py
/mcp                              # Check server status

# Memory monitoring
free -h                           # Linux
Get-Process vmmem | Select WorkingSet64  # PowerShell
```
