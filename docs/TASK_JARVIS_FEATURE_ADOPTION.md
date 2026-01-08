# Task: Assess and Adopt Features from isair/jarvis into ATLAS

**Date:** January 6, 2026
**Type:** Architectural Integration Analysis
**Priority:** High - Informs next development phase

---

## 1. Context for the Agent

You are being asked to carefully evaluate which features from the [isair/jarvis](https://github.com/isair/jarvis) open-source project should be adopted into ATLAS, and HOW they should be integrated without compromising ATLAS's core architectural advantages.

### What is ATLAS?
ATLAS is a voice-first AI life assistant with a sophisticated three-tier LLM routing architecture (R29). It's designed for:
- Cost-aware hybrid routing (Local/API/Agent SDK)
- Voice-optimized latency (<3s E2E target)
- The "Lethal Gentleman" persona (refined, direct, no hedging)
- Hardware-constrained environments scaling to powerful hardware
- Research-backed decisions (29 research topics completed)

### What is isair/jarvis?
jarvis is a functional, privacy-first local AI assistant with:
- Single local model (gpt-oss:20b via Ollama)
- Extensive MCP integrations (500+ services)
- Voice with wake word, interrupt, voice cloning
- Multiple personality profiles (Developer/Business/Coach)
- Persistent memory with keyword extraction
- Production-ready today

### The Goal
Identify features from jarvis that would enhance ATLAS WITHOUT:
- Compromising the three-tier routing intelligence
- Losing cost tracking and budget management
- Breaking the Lethal Gentleman persona coherence
- Adding complexity that doesn't serve the user's goals

---

## 2. Files to Read

### ATLAS Architecture
```
/home/squiz/ATLAS/docs/MASTER_PLAN.md                    # Core architecture
/home/squiz/ATLAS/docs/R29_IMPLEMENTATION_STATUS.md      # Current routing status
/home/squiz/ATLAS/docs/ARCHITECTURE_COMPARISON_R29.md    # R29 vs original
/home/squiz/ATLAS/docs/COMPARISON_ATLAS_VS_JARVIS.md     # Initial comparison
/home/squiz/ATLAS/docs/FUTURE_VISION_LOCAL_AI_2026.md    # Hardware roadmap
```

### ATLAS Implementation
```
/home/squiz/ATLAS/atlas/llm/router.py       # Semantic router
/home/squiz/ATLAS/atlas/llm/api.py          # Direct Anthropic client
/home/squiz/ATLAS/atlas/llm/local.py        # Ollama client
/home/squiz/ATLAS/atlas/llm/cost_tracker.py # Cost tracking
/home/squiz/ATLAS/atlas/voice/pipeline.py   # Voice pipeline (if exists)
/home/squiz/ATLAS/config/routing.yaml       # Router configuration
```

### ATLAS Persona Research
```
/home/squiz/ATLAS/docs/research/R21.The Lethal Gentleman - A complete AI persona specification.md
```

### jarvis (External)
```
https://github.com/isair/jarvis              # Main repo
https://github.com/isair/jarvis/blob/main/README.md  # Documentation
```

---

## 3. Features to Evaluate

### Category A: Voice System Enhancements

| Feature | jarvis Implementation | Assessment Questions |
|---------|----------------------|---------------------|
| **Interrupt commands** | "stop", "shush" mid-response | How does this interact with streaming TTS? What's the implementation pattern? |
| **Hot window mode** | Stays listening after response for follow-ups | Duration? How to detect follow-up vs new query? |
| **Voice cloning** | Chatterbox TTS with 3-10s sample | Compatible with Kokoro? Resource requirements? |
| **Emotion control** | Exaggeration parameter 0.0-1.0+ | Does this fit Lethal Gentleman persona (restrained)? |

**Key question:** Which voice features improve UX without adding latency?

### Category B: Memory System Enhancements

| Feature | jarvis Implementation | Assessment Questions |
|---------|----------------------|---------------------|
| **Keyword extraction** | Automatic from conversations | Algorithm? Integration with existing FTS5? |
| **Time-range filtering** | Native in memory queries | Schema changes needed? |
| **Memory enrichment** | Context injection at query time | How does this affect prompt size/cost? |
| **Unlimited context** | No token resets | Already planned via RAG - any differences? |

**Key question:** What memory patterns improve retrieval without bloating context?

### Category C: Personality/Profile System

| Feature | jarvis Implementation | Assessment Questions |
|---------|----------------------|---------------------|
| **Multiple profiles** | Developer/Business/Coach auto-switching | How to integrate with Lethal Gentleman? |
| **Context-aware switching** | Based on query content | Conflict with existing interaction modes? |
| **Profile-specific tools** | Different tools per profile | Router already does tier selection - overlap? |

**Key question:** Can profiles ENHANCE Lethal Gentleman rather than replace it?

### Category D: MCP Integrations

| Feature | jarvis Implementation | Assessment Questions |
|---------|----------------------|---------------------|
| **Home Assistant** | Native MCP server | Priority for ATLAS? Configuration complexity? |
| **Google Workspace** | Gmail, Drive, Calendar, Docs | User need? Privacy implications? |
| **GitHub** | Repos, issues, PRs | User need? |
| **Database connectors** | MySQL, PostgreSQL, SQLite, MongoDB | Already using SQLite - extend? |
| **Composio (500+)** | Meta-integration layer | Worth the dependency? |

**Key question:** Which integrations serve THIS user's actual workflow?

### Category E: Privacy & Security

| Feature | jarvis Implementation | Assessment Questions |
|---------|----------------------|---------------------|
| **Hardened mode** | Config to disable all network | Already local-first - add explicit mode? |
| **Sensitive redaction** | Auto-redact emails, tokens, passwords | Patterns to adopt? |
| **Network verification** | Scripts to audit connections | Easy to add - priority? |
| **Data export/delete** | User-controlled | GDPR-style compliance? |

**Key question:** What privacy features build user trust?

### Category F: Developer Experience

| Feature | jarvis Implementation | Assessment Questions |
|---------|----------------------|---------------------|
| **Cross-platform scripts** | macOS/Windows/Linux installers | ATLAS currently WSL2-only - expand? |
| **Screenshot OCR** | Visual context for debugging | Useful for voice-first? |
| **Multi-step planning** | Task decomposition before execution | Overlap with DAG executor (R23)? |

**Key question:** What DX improvements matter for a personal (not distributed) project?

---

## 4. Assessment Criteria

For each feature, evaluate:

### 4.1 User Value
- Does this serve the user's actual goals (fitness, health tracking, productivity)?
- How often would this feature be used?
- What's the UX improvement magnitude?

### 4.2 Architectural Fit
- Does it conflict with three-tier routing?
- Does it add latency to the voice path?
- Does it complicate the cost model?

### 4.3 Implementation Effort
- Lines of code estimate
- New dependencies required
- Testing complexity
- Maintenance burden

### 4.4 Persona Coherence
- Does it fit the Lethal Gentleman character?
- Does it require persona modifications?
- Could it break immersion?

### 4.5 Priority Classification
```
P0 - Critical: Adopt immediately, blocks other work
P1 - High: Adopt in next phase, significant value
P2 - Medium: Adopt when convenient, nice to have
P3 - Low: Consider later, minimal value
P4 - Skip: Doesn't fit ATLAS, or jarvis does it wrong
```

---

## 5. What ATLAS Must NOT Change

These are core differentiators - do NOT recommend changes that compromise:

### 5.1 Three-Tier Routing Intelligence
```
LOCAL (40-50%) → HAIKU (35-40%) → AGENT_SDK (10-15%)
```
jarvis uses single local model. ATLAS's routing is superior. Preserve it.

### 5.2 Cost Tracking and Budget Management
```
SQLite tracking → Daily/Monthly limits → Thrifty mode → Graceful degradation
```
jarvis has no cost awareness. ATLAS's budget system is essential. Preserve it.

### 5.3 Latency Engineering
```
<3s E2E target → Filler phrases → Streaming TTS
```
Real-world latency from Australia is ~2800ms for API. Filler strategy is critical. Preserve it.

### 5.4 Lethal Gentleman Core Character
```
- Capable, refined, restrained
- Direct speech, no hedging
- "Power held in check"
```
Any personality additions must ENHANCE this, not replace it.

### 5.5 Research-Backed Decisions
```
29 research topics (R1-R29) inform architecture
```
Don't adopt jarvis patterns that contradict validated research.

---

## 6. Suggested Analysis Structure

### Phase 1: Deep Dive on jarvis
1. Clone and explore the jarvis repository
2. Read all source files, not just README
3. Understand their memory implementation
4. Understand their voice pipeline
5. Understand their MCP integration pattern

### Phase 2: Feature-by-Feature Assessment
For each feature in Section 3:
1. Document exactly how jarvis implements it
2. Evaluate against criteria in Section 4
3. Propose how it would integrate with ATLAS (if adopted)
4. Assign priority classification
5. Estimate implementation effort

### Phase 3: Synthesis
1. Create prioritized adoption list
2. Identify any architectural changes needed
3. Flag any conflicts or concerns
4. Propose implementation order

### Phase 4: Implementation Specifications
For P0 and P1 features:
1. Write detailed implementation specs
2. Identify files to modify
3. Propose code patterns
4. Define test criteria

---

## 7. Output Expected

Produce a document with:

```markdown
# ATLAS Feature Adoption from jarvis - Assessment Report

## Executive Summary
[2-3 paragraphs on overall findings]

## Adoption Recommendations

### P0 - Adopt Immediately
| Feature | Why | Implementation Approach | Effort |
|---------|-----|------------------------|--------|
| ... | ... | ... | ... |

### P1 - Adopt Next Phase
| Feature | Why | Implementation Approach | Effort |
|---------|-----|------------------------|--------|
| ... | ... | ... | ... |

### P2 - Adopt When Convenient
[Same format]

### P3 - Consider Later
[Same format]

### P4 - Do Not Adopt
| Feature | Why Not |
|---------|---------|
| ... | ... |

## Architectural Impact
[Any changes to existing architecture]

## Persona Integration
[How adopted features fit Lethal Gentleman]

## Implementation Roadmap
[Suggested order and dependencies]

## Open Questions
[Anything needing user input]
```

---

## 8. User Context (Important)

The user building ATLAS:
- **Location:** Australia (affects API latency)
- **Hardware now:** 16GB RAM, 4GB VRAM (WSL2)
- **Hardware planned:** Mac Mini M5 Pro 64GB (Q2 2026)
- **Partner:** Naturopath (handles health protocols)
- **Equipment:** Home gym (power rack, bench, etc.)
- **Goals:** Blueprint-style health tracking, workout planning, later content creation
- **Persona preference:** Refined, direct, no hedging - the "Lethal Gentleman"

Features should be evaluated against THIS user's actual needs, not general-purpose assistant needs.

---

## 9. Key Questions to Answer

1. **Voice:** Should ATLAS adopt Chatterbox voice cloning, or stick with Kokoro?

2. **Profiles:** Should Lethal Gentleman have sub-profiles (Developer/Coach/etc.), or stay unified?

3. **MCP:** Which integrations matter? (Home Assistant? Garmin? Google? GitHub?)

4. **Memory:** Is jarvis's keyword extraction better than planned FTS5 approach?

5. **Privacy:** Should ATLAS have explicit "hardened mode" like jarvis?

6. **Interrupt:** How to implement mid-response interrupt with streaming TTS?

7. **Hot window:** What duration for follow-up listening? How to detect intent?

---

## 10. Don't Forget

- jarvis works TODAY. ATLAS is still being built. Some jarvis patterns may be "good enough for now" vs "optimal for long-term."

- The user is planning hardware upgrade to Mac Mini M5 64GB. Some jarvis patterns that don't fit current constraints may fit future hardware.

- jarvis uses single 20B model. ATLAS has frontier reasoning via Claude API. Don't downgrade capabilities just to match jarvis patterns.

- The goal is SYNTHESIS - best of both - not wholesale adoption of either approach.

---

**This task requires careful, thorough analysis. Take time to understand both systems deeply before making recommendations.**
