# ATLAS Verification Research Prompts

**Purpose:** Prompts for Gemini Deep Research and Opus Web Research to verify claims and fill gaps before ATLAS implementation.

**Instructions:** Run each prompt through a dedicated research agent. Compare results. Flag any contradictions with our current synthesis.

---

## Research Prompt 1: Claude Code CLI & MCP Current State (CRITICAL)

```
RESEARCH TASK: Claude Code CLI and MCP Protocol - Current State January 2025

CONTEXT:
I am building ATLAS, an AI life assistant that wraps Claude Code with orchestration, memory, and voice capabilities. My research from late 2024 may be outdated. I need CURRENT, VERIFIED information about Claude Code's CLI capabilities and the Model Context Protocol.

SPECIFIC QUESTIONS TO ANSWER:

1. CLAUDE CODE CLI (as of January 2025):
   - What is the exact command syntax for headless/non-interactive mode?
   - Is there a `-p` or `--prompt` flag? What does it do exactly?
   - How does session resumption work? Is there a `--resume` flag?
   - Can you run Claude Code programmatically from Python/Node.js?
   - What are the current subagent types available (general-purpose, Explore, Plan, etc.)?
   - How do you configure hooks (PreToolUse, PostToolUse)? Where do configs live?
   - What is the `--dangerously-skip-permissions` flag and when is it appropriate?

2. MCP (Model Context Protocol) SPECIFICATION:
   - What is the current MCP spec version?
   - What is the correct configuration file format? (`.mcp.json` vs `mcp.json` vs in claude config)
   - STDIO vs HTTP/SSE transport - what's recommended for local servers?
   - How do you register an MCP server with Claude Code?
   - What's the official Python SDK package name and current version?
   - Is FastMCP merged into the official SDK or separate?

3. HOOKS SYSTEM:
   - What hook types exist (PreToolUse, PostToolUse, Notification, etc.)?
   - What's the exact JSON schema for hook input/output?
   - How do you block a tool call from a hook (exit code 2)?
   - Can hooks be async/non-blocking?

4. INTEGRATION PATTERNS:
   - How do production systems orchestrate multiple Claude Code instances?
   - What are the memory/resource costs per Claude Code process?
   - Are there official examples of headless automation?

SUCCESS CRITERIA:
- Provide exact command examples that work TODAY
- Include links to official documentation
- Note any breaking changes from 2024 to 2025
- Flag anything marked "experimental" or "beta"
- If information conflicts exist between sources, note all versions

OUTPUT FORMAT:
Structured markdown with code examples, verified against official Anthropic/MCP documentation. Include dates of documentation sources.
```

---

## Research Prompt 2: Voice Pipeline Components - 2025 State of the Art

```
RESEARCH TASK: Optimal Voice AI Pipeline for 6GB RAM Constraint - January 2025

CONTEXT:
Building a voice-first AI assistant on constrained hardware:
- 16GB total RAM, ~6GB usable for WSL2
- NVIDIA RTX 3050 Ti (4GB VRAM) - uncertain if usable in WSL2
- Target: sub-3 second end-to-end latency (user speaks → assistant responds audibly)
- Must run locally, not cloud STT/TTS

SPECIFIC QUESTIONS:

1. SPEECH-TO-TEXT (STT):
   a) faster-whisper: Current version, VRAM per model size, INT8 performance (latency + accuracy), beam_size=1 accuracy impact
   b) Moonshine (Useful Sensors): Production-ready? Benchmarks vs faster-whisper? ONNX support? Memory footprint?
   c) Distil-Whisper: Current state vs faster-whisper, when to choose it?
   d) Any NEW low-latency STT models from late 2024/early 2025?

2. TEXT-TO-SPEECH (TTS):
   a) Piper: Current version, best conversational voices, latency for ~50 words, streaming support?
   b) Kokoro-82M: ONNX status, CPU vs GPU performance, memory requirements?
   c) Any NEW neural TTS under 500MB RAM?

3. VAD: Is Silero VAD still best? Optimal silence threshold? Alternatives?

4. WSL2 AUDIO: PulseAudio/PipeWire status, microphone reliability, latency overhead?

5. WSL2 GPU: CUDA support current state, required drivers, does faster-whisper CUDA work?

6. REALISTIC LATENCY: Given these components, pessimistic/realistic/optimistic end-to-end estimates?

SUCCESS CRITERIA:
- Actual benchmarks with numbers (not marketing)
- Memory usage measured
- Comparison tables
- Note "bleeding edge" vs "production stable"
```

---

## Research Prompt 3: SQLite-Based AI Memory Architecture

```
RESEARCH TASK: SQLite for AI Agent Memory - 2025 Best Practices

CONTEXT:
Building persistent memory for AI assistant:
- 6GB RAM budget
- Needs: episodic (conversations), semantic (facts), core (identity) memory
- Hybrid search: keyword (FTS) + vector similarity
- Scale: <100K records initially, years of growth
- Must be embedded (no separate server)

Plan: SQLite + sqlite-vec + FTS5 + all-MiniLM-L6-v2 (384 dims, ONNX INT8)

SPECIFIC QUESTIONS:

1. SQLITE-VEC: Correct choice in Jan 2025? Version/stability? RAM benchmarks (idle, query, 100K vectors)? Query performance? Filtered vector search support? vs sqlite-vss, chromadb-embedded?

2. FTS5: Best tokenizer (porter vs trigram)? BM25 alternatives? Fusion with vector search? Memory at 100K docs?

3. EMBEDDINGS: all-MiniLM-L6-v2 still optimal? ONNX INT8 accuracy loss? Alternatives (BGE-small, E5-small)? New efficient models late 2024?

4. SCHEMA: Tiered memory patterns? Embedding storage (BLOB vs virtual table)? Importance scoring/decay? Consolidation strategies?

5. PERFORMANCE: Realistic hybrid search latency at 100K? Real-time embed+insert possible? WAL considerations? File size growth rate?

6. ALTERNATIVES: LanceDB? DuckDB vectors? When to switch from SQLite?

7. GRAPH: SQLite CTEs for relationships - performance limits? When is NetworkX needed?

SUCCESS CRITERIA:
- Benchmark data from actual tests
- Memory measurements (RSS)
- Code examples
- Decision framework
```

---

## Research Prompt 4: External Knowledge APIs - Pricing & Capabilities

```
RESEARCH TASK: External Knowledge APIs for AI Agents - January 2025

CONTEXT:
ATLAS needs external knowledge: docs, code examples, package info, Stack Overflow.
Requirements:
- Cost: <$20/month for personal use
- Latency: <500ms typical
- Token-efficient responses
- Lightweight integration

Plan: ref.tools (docs) + exa.ai (code search) + direct PyPI/npm APIs + SQLite cache

SPECIFIC QUESTIONS:

1. EXA.AI: Current pricing (Jan 2025)? Rate limits? API stability? Code search quality? Token efficiency? Competitors?

2. REF.TOOLS: Current pricing/credits? Token reduction reality? Site coverage? Rate limits? Alternatives (Jina Reader, FireCrawl)?

3. GITHUB API: Code search limits? Rate limits? Cost? Can it replace exa.ai?

4. STACK OVERFLOW: API access in 2025 (after AI policy changes)? Rate limits? Restrictions?

5. PACKAGE REGISTRIES: PyPI, npm, crates.io - rate limits, stability?

6. DOCUMENTATION: Which sites block scrapers? DevDocs API? ReadTheDocs API?

7. CACHING: Reasonable TTLs? Cache invalidation? Expected hit rates?

8. COST MODEL: 50-100 queries/day - realistic monthly cost?

SUCCESS CRITERIA:
- CURRENT pricing (verify against official pages)
- Actual rate limits
- Working API examples
- Total cost estimate
```

---

## Research Prompt 5: Windows 11 WSL2 Optimization (CRITICAL)

```
RESEARCH TASK: Windows 11 + WSL2 Memory Optimization - January 2025

CONTEXT:
Running ATLAS on:
- Windows 11 (latest stable)
- 16GB total RAM
- WSL2 Ubuntu for AI workloads
- Goal: ~6GB usable in WSL2

SPECIFIC QUESTIONS:

1. WSLCONFIG: Current syntax/options? autoMemoryReclaim status? sparseVhd? Docker interaction?

2. MEMORY RECLAMATION: Does WSL2 return memory now? gradual vs dropcache? Known bugs? Monitoring?

3. WINDOWS SERVICES: Safe to disable for RAM? New memory-heavy services? SysMain on SSD? Search alternatives?

4. MEMORY LEAKS: DoSvc still leaking? NDU fix still needed? New leaks in 2024-2025?

5. GPU IN WSL2: CUDA support status? Required driver? VRAM vs memory limit? PyTorch/ONNX CUDA working?

6. AUDIO IN WSL2: PulseAudio vs PipeWire? Microphone reliability? Latency overhead?

7. REALISTIC BUDGET: After optimization - Windows idle, with browser, WSL2 available, total for AI?

8. DOCKER: Docker Desktop vs Podman memory? autoMemoryReclaim interaction?

SUCCESS CRITERIA:
- Current info (Win11 23H2/24H2)
- Actual memory measurements
- Working .wslconfig
- PowerShell commands
- GPU/audio verification steps
```

---

## Research Prompt 6: Cutting Edge Agent Architecture

```
RESEARCH TASK: State of the Art in AI Agent Architecture - Late 2024 / Early 2025

CONTEXT:
Building ATLAS personal AI assistant with voice, memory, tools, reflection, orchestration.
Want to ensure not missing recent developments.

SPECIFIC QUESTIONS:

1. ORCHESTRATION: State of the art multi-agent? LangGraph vs CrewAI vs AutoGen vs Claude native? New frameworks?

2. MEMORY/RAG: Latest agent memory developments? GraphRAG maturity? Cognitive architectures? New efficient embedding models?

3. TOOL USE: MCP adoption? Alternatives? Computer use for assistants? Dynamic tool creation?

4. REFLECTION: Reflexion improvements? Self-improvement without fine-tuning? DSPy practical? Constitutional AI patterns?

5. VOICE AGENTS: Real-time approaches? Interruption handling? Emotion detection? Voice cloning ethics?

6. LOCAL/EDGE AI: Consumer hardware models? Hybrid local+cloud? Privacy patterns? Quantization advances?

7. PERSONAL ASSISTANTS: What shipped late 2024? Lessons from failures? Working patterns? Security best practices?

8. PAPERS/PROJECTS: Important late 2024 papers? Best open source examples? Agent benchmarks?

SUCCESS CRITERIA:
- PRACTICAL, implementable patterns
- Distinguish proven vs experimental
- Prioritize constrained hardware
- Links to papers/repos
- Honest hype vs substance assessment
```

---

## Execution Plan

### Priority Order:
1. **Prompt 1** (Claude Code/MCP) - BLOCKS everything
2. **Prompt 5** (Windows/WSL2) - Validates hardware assumptions
3. **Prompt 2** (Voice) - Core UX
4. **Prompt 3** (Memory) - Core architecture
5. **Prompt 4** (APIs) - Cost planning
6. **Prompt 6** (Cutting Edge) - Don't miss innovations

### Process:
1. Run each through BOTH Gemini Deep Research AND Opus Web Research
2. Compare for conflicts
3. Flag contradictions with RESEARCH_SYNTHESIS.md
4. Update synthesis with verified info

### Output:
After all research → VERIFIED_ARCHITECTURE.md → Implementation tickets → Proof-of-concept
