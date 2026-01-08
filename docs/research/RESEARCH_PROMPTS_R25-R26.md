# ATLAS Research Prompts: R25-R26

**Purpose:** Fill remaining gaps identified in R22-R24 analysis
**Date:** January 2026

---

## RESEARCH PROMPT R25: Local LLM Selection for Resource-Constrained Personal AI

```
I'm building ATLAS, an autonomous AI life assistant running on WSL2 with strict hardware constraints: 4GB VRAM (RTX 3050 Ti), 6GB RAM allocated to WSL2. The system requires sub-3-second voice interaction latency with a voice pipeline (Silero VAD → Moonshine STT → LLM → Kokoro TTS).

A conflict has emerged in my research:
- R15 (technical verification research) recommended: Qwen 2.5 7B Q4_K_M
- R24 (hybrid architecture research) recommended: Qwen3-4B Q4_K_M (~2.75GB VRAM)

I need definitive guidance on local LLM selection for ATLAS.

Research the following for me (as of January 2026):

1. MODEL COMPARISON: Qwen3-4B vs Qwen 2.5 7B
Compare these specific configurations:
- Qwen3-4B Q4_K_M (GGUF)
- Qwen 2.5 7B Q4_K_M (GGUF)
- Include: Qwen3-8B Q4_K_M as potential middle ground

For each model, evaluate:
- Actual VRAM usage (idle, under load, with KV cache)
- First token latency and tokens/second on RTX 3050 Ti
- Quality on instruction following and multi-turn conversation
- Reasoning capability for task planning
- Tool calling / function calling support
- Context window practical limits on 4GB VRAM

2. ATLAS-SPECIFIC TASK EVALUATION
How do these models perform on personal assistant tasks:

a) Intent classification accuracy:
   - "Prepare my morning workout for Monday"
   - "What supplements should I take today?"
   - "Check my TikTok analytics from last week"
   - Ambiguous: "I'm tired" (venting vs request for help)

b) Slot extraction reliability:
   - Extracting: day=monday, workout_type=[yoga, calisthenics], injury=shoulder
   - Handling implicit slots: "the usual" → reference resolution

c) Workout generation quality:
   - Safety: respecting injury constraints
   - Completeness: warm-up, main, cool-down
   - Personalization: matching user fitness level

d) Multi-turn conversation coherence:
   - Following up on previous context
   - Handling corrections ("No, I meant Tuesday")
   - Maintaining persona consistency

3. VOICE LATENCY BUDGET ANALYSIS
With the pipeline: VAD (20ms) → STT (500-700ms) → LLM (???) → TTS (200-300ms)
- What LLM latency is achievable for first token?
- What total generation time for 50-100 token responses?
- Impact of KV cache quantization (q8_0, q4_0) on quality vs speed
- Streaming output: when does first token arrive?

4. MEMORY OPTIMIZATION TECHNIQUES
Within 4GB VRAM constraint:
- Flash Attention impact on Qwen models
- KV cache quantization strategies
- Context length vs quality tradeoff
- Layer offloading to CPU (performance impact)
- Concurrent STT+LLM possibility or sequential only?

5. QUANTIZATION COMPARISON
For the recommended model, compare:
- Q4_K_M (default recommendation)
- Q5_K_M (quality improvement?)
- Q4_K_S (smaller, faster?)
- Q8_0 (fits in 4GB VRAM?)

Provide quality degradation metrics vs inference speed.

6. INTEGRATION AND DEPLOYMENT
- Ollama vs llama.cpp vs vLLM for WSL2 deployment
- Optimal Ollama configuration for 4GB VRAM
- Environment variables (OLLAMA_FLASH_ATTENTION, OLLAMA_KV_CACHE_TYPE, etc.)
- Model loading time and memory spikes during load
- Graceful handling when VRAM is exhausted

7. HYBRID LOCAL/CLOUD ARCHITECTURE
When should ATLAS fall back to cloud (Claude API)?
- Complexity threshold detection
- Context length triggers
- Quality confidence routing
- Cost implications ($20/month budget)
- Latency comparison: local fast path vs cloud slow path

8. ALTERNATIVE MODELS TO CONSIDER
If neither Qwen option is ideal, evaluate:
- Phi-3-mini-4k-instruct (Microsoft)
- Llama-3.2-3B-Instruct
- Gemma-2-2B-it
- Mistral-7B-Instruct-v0.3 (fits 4GB?)

Provide a decision matrix with VRAM, latency, and quality scores.

9. THE MORNING SCENARIO TEST
Evaluate each model on this exact interaction:

User: "ATLAS, prepare my morning workout for Monday. Check Garmin for recovery, my shoulder is sore, include yoga and calisthenics."

Expected model behavior:
1. Parse intent: morning workout preparation
2. Extract: day=Monday, constraints=[shoulder injury], types=[yoga, calisthenics]
3. Recognize need for: Garmin API call, injury profile lookup
4. Generate: appropriate workout respecting all constraints

Score each model on: accuracy, latency, coherence.

10. RECOMMENDATION FORMAT
Provide a clear recommendation in this format:

PRIMARY: [Model name + quantization]
- VRAM usage: X GB
- First token latency: X ms
- Quality score: X/10
- Why: [reasoning]

FALLBACK: [Alternative if primary unavailable]
CLOUD TRIGGER: [When to escalate to Claude API]

Include specific Ollama/llama.cpp configuration commands.

Provide benchmark data from papers, open benchmarks (MMLU, MT-Bench, etc.), and real-world testing reports from 2024-2025. Focus on personal assistant and agent use cases, not general benchmarks.
```

---

## RESEARCH PROMPT R26: Verification API Integration for Personal AI Domains

```
I'm building ATLAS, an autonomous AI life assistant that generates outputs across four domains: fitness/workout, health/supplements, nutrition/recipes, and content creation. Research R22 established that external verification (not LLM self-reflection) is essential for quality - "2-3x improvement."

I need practical integration guidance for verification APIs and databases that can ground ATLAS's outputs in external truth.

Constraints:
- Budget: <$20/month total for all APIs
- Latency: <500ms per verification call (inline verification)
- Reliability: Offline fallback required for safety-critical domains
- Privacy: User health data must not leak to third parties

Research the following for me (as of January 2026):

1. HEALTH & SUPPLEMENT VERIFICATION

a) Drug-Supplement Interaction APIs:
- Supp.AI (Allen Institute):
  - Is it still available? API access method?
  - Rate limits and pricing
  - Coverage: 2,044 supplements × 2,866 drugs claimed - verify this
  - Response format and integration pattern
  - Latency characteristics

- DrugBank:
  - API availability for non-commercial use
  - Pharmacokinetic interaction data
  - Cost for personal projects

- Drugs.com / Medscape:
  - Any API access or scraping feasibility?
  - Consumer-friendly severity ratings

- Open alternatives:
  - OpenFDA drug interactions
  - RxNorm for drug identification
  - Any open-source interaction databases?

b) Supplement Safety Databases:
- Natural Medicines Database (paid?)
- NIH Office of Dietary Supplements
- Examine.com data accessibility
- ConsumerLab (API?)

c) Implementation Pattern:
```python
async def verify_supplement_safety(supplements: List[str], medications: List[str]) -> VerificationResult:
    # What's the optimal pattern here?
    # Caching strategy for common interactions?
    # Fallback when API unavailable?
    pass
```

2. EXERCISE & WORKOUT VERIFICATION

a) Contraindication Databases:
- ACE (American Council on Exercise) - any API?
- ACSM exercise guidelines - structured data?
- ExRx.net - exercise database with contraindications?
- Are there open datasets mapping conditions → exercise restrictions?

b) Exercise Safety Rules:
- Load progression limits (10-15% weekly max)
- Muscle recovery requirements (48-72 hours)
- Form/technique safety for common exercises
- Equipment-exercise compatibility

c) Build vs Buy Analysis:
- Should I build a local SQLite database of exercise rules?
- Or is there an API worth paying for?
- What's the minimum viable verification for workout safety?

d) Implementation Pattern:
```python
def verify_workout_safety(workout: WorkoutPlan, user_profile: UserProfile) -> SafetyResult:
    # Check: contraindications, load progression, recovery time, equipment
    # What external data sources?
    # Local rules vs API calls?
    pass
```

3. NUTRITION & RECIPE VERIFICATION

a) Nutritional Data APIs:
- USDA FoodData Central:
  - API access and rate limits
  - Data freshness and coverage
  - Branded vs generic foods
  - Integration complexity

- Nutritionix:
  - Free tier limits
  - Natural language food parsing
  - Accuracy for macro calculation

- Open Food Facts:
  - Coverage for US foods
  - Data quality concerns
  - Barcode scanning integration

- Edamam:
  - Recipe analysis API
  - Nutritional calculation accuracy
  - Pricing for personal use

b) Dietary Compliance Verification:
- Ingredient classification databases (vegan, gluten-free, allergens)
- Allergen detection in recipes
- Cross-contamination warnings

c) Recipe Completeness Checks:
- NLP approach: do all ingredients appear in steps?
- Cooking time/temperature validation
- Portion/serving size reasonability

d) Implementation Pattern:
```python
async def verify_recipe(recipe: Recipe, dietary_requirements: List[str]) -> RecipeVerification:
    # Nutritional calculation
    # Dietary compliance
    # Allergen detection
    # Completeness check
    pass
```

4. CONTENT CREATION VERIFICATION

a) Plagiarism Detection:
- Copyscape API (cost?)
- Open alternatives for personal use
- Embedding-based similarity (local)

b) AI Content Detection:
- GPTZero API
- Originality.AI
- Should ATLAS verify its own content isn't "too AI"?
- What threshold is acceptable?

c) Factual Verification:
- Cross-referencing claims against sources
- RAGAS (Retrieval-Augmented Generation Assessment)
- Citation verification

d) Platform Fit Verification:
- TikTok: 15-60s duration, vertical format, hook in first 3s
- YouTube: 8-15min optimal, thumbnail requirements
- Blog/SEO: word count, keyword density, readability
- Are there APIs for platform-specific checks?

e) Readability Scoring:
- Flesch-Kincaid (local calculation)
- Hemingway-style analysis
- Audience matching

5. CACHING & RATE LIMITING STRATEGY

For each API integration:
- What should be cached and for how long?
- How to handle rate limits gracefully?
- Fallback behavior when API is unavailable
- Cost optimization through intelligent caching

```python
CACHE_CONFIG = {
    'drug_interactions': {'ttl': 7 * 24 * 3600, 'storage': 'sqlite'},  # 7 days
    'nutritional_data': {'ttl': 30 * 24 * 3600, 'storage': 'sqlite'},  # 30 days
    'exercise_contraindications': {'ttl': 90 * 24 * 3600, 'storage': 'sqlite'},  # 90 days
    # What else?
}
```

6. OFFLINE FALLBACK ARCHITECTURE

For safety-critical verifications (health, workout safety):
- What data should be stored locally?
- How to keep local data updated?
- Degraded mode behavior when offline
- User notification requirements

7. PRIVACY & COMPLIANCE

- FDA guidance on Clinical Decision Support (January 2025)
- HIPAA considerations for health data
- What disclaimers are legally required?
- Data minimization for API calls (don't send full health profile)

8. BUDGET ALLOCATION

With $20/month total budget across all ATLAS APIs:
- Exa.ai: ~$15 (from R13 analysis)
- Remaining: ~$5 for verification APIs

What's achievable within $5/month for verification?
- Which paid APIs are worth it?
- Which can be replaced with free/local alternatives?

9. LATENCY BUDGET

Within 3-second total voice response:
- Verification must complete in <500ms
- Parallel verification calls where possible
- Which verifications are blocking vs advisory?

| Domain | Blocking? | Max Latency | Fallback |
|--------|-----------|-------------|----------|
| Drug interactions | Yes | 300ms | Local cache |
| Workout safety | Yes | 200ms | Local rules |
| Nutritional calc | No | 500ms | Estimate |
| Content quality | No | 1000ms | Skip |

10. INTEGRATION ARCHITECTURE

Provide a unified verification interface:

```python
class VerificationEngine:
    async def verify(self, output: Any, domain: Domain, user_context: UserContext) -> VerificationResult:
        # Route to appropriate verifier
        # Handle timeouts and fallbacks
        # Return structured result with confidence
        pass

@dataclass
class VerificationResult:
    passed: bool
    confidence: float
    issues: List[VerificationIssue]
    suggestions: List[str]
    source: str  # Which API/database provided verification
```

Provide specific API documentation links, pricing information (as of January 2026), code examples, and recommendations for each domain. Prioritize free/open options but identify paid options worth the cost for critical safety verifications.
```

---

## RESEARCH PROMPT R27: LangGraph Integration Patterns for Voice-First Agents

```
I'm building ATLAS, an autonomous AI life assistant with voice-first interaction (sub-3-second response budget). Research R23-R24 recommended LangGraph StateGraph for complex multi-step workflows, but my current architecture uses Claude Agent SDK + MCP servers.

I need guidance on when and how to integrate LangGraph, and how it interoperates with my existing stack.

Research the following for me (as of January 2026):

1. LANGGRAPH VS CLAUDE AGENT SDK
- What does LangGraph provide that Claude Agent SDK doesn't?
- What does Claude Agent SDK provide that LangGraph doesn't?
- Are they complementary or competing?
- Integration patterns for using both

2. WHEN TO USE LANGGRAPH
For ATLAS skills, which need LangGraph vs simpler patterns?

| Skill | Complexity | LangGraph? | Rationale |
|-------|------------|------------|-----------|
| Simple Q&A | Low | No | Single LLM call |
| Workout generation | Medium | ? | Multi-tool, sequential |
| Content pipeline | High | ? | DAG, conditions, retry |

Provide decision criteria for when LangGraph overhead is justified.

3. STATEGRAPH FOR VOICE LATENCY
- StateGraph adds overhead - how much?
- Can StateGraph work within 3-second voice budget?
- Streaming patterns with StateGraph
- Early termination for quick responses

4. MCP + LANGGRAPH INTEGRATION
My tools are exposed via MCP servers (STDIO transport):
- How to wrap MCP tools for LangGraph nodes?
- Error handling at the MCP-LangGraph boundary
- State passing between MCP and LangGraph

5. CHECKPOINTING FOR PERSONAL AI
SqliteSaver for persistence:
- Schema and storage requirements
- Resume interrupted workflows
- Time-travel debugging
- Memory cleanup for long-running assistant

6. CONDITIONAL ROUTING PATTERNS
For confidence-based routing (0.9/0.7/clarify):
- LangGraph conditional edges vs Python if/else
- Dynamic routing based on LLM confidence
- Human-in-the-loop approval gates

7. PARALLEL EXECUTION IN LANGGRAPH
For DAG-based parallel execution:
- LangGraph Send API for fan-out
- Gathering results from parallel nodes
- Error handling when one branch fails
- Timeout management per branch

8. PRACTICAL IMPLEMENTATION
Provide a complete example:
- Morning workout skill as LangGraph StateGraph
- Including: Garmin API, user profile, workout generation, verification
- With checkpointing and error recovery
- Meeting 3-second latency target

9. LANGGRAPH ALTERNATIVES
For simpler cases where LangGraph is overkill:
- asyncio.gather for basic parallelism
- Simple Python state machines
- When to use what

10. PRODUCTION PATTERNS
- Logging and observability (LangSmith?)
- Testing LangGraph workflows
- Debugging failed executions
- Performance monitoring

Provide code examples using LangGraph 0.2+ (latest stable as of January 2026), Python async patterns, and integration with Claude API. Include benchmark data on LangGraph overhead for latency-sensitive applications.
```

---

## Research Execution Plan

| Prompt | Priority | Reason | Recommended Agent |
|--------|----------|--------|-------------------|
| R25 (Local LLM) | HIGH | Blocks implementation - need model decision | Gemini Deep Research |
| R26 (Verification APIs) | HIGH | Core to verification architecture | Claude Opus |
| R27 (LangGraph) | MEDIUM | Needed for complex workflows only | Either |

**Execution Order:**
1. R25 first (blocks P0 implementation)
2. R26 second (needed for P1 verification engine)
3. R27 third (can defer until complex workflows needed)

**Estimated Research Time:**
- R25: 20-30 minutes (benchmarks, comparisons)
- R26: 30-45 minutes (many APIs to investigate)
- R27: 15-20 minutes (focused scope)
