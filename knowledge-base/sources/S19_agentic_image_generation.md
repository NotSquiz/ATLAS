# S19: Agentic Image Generation — Nano Banana + Claude Code + Google Agentic Vision

## Frontmatter

| Field | Value |
|-------|-------|
| **ID** | S19 |
| **Source** | X.com post (DAIR.AI cohort practitioner), https://blog.google/innovation-and-ai/technology/developers-tools/agentic-vision-gemini-3-flash/, https://github.com/kkoppenhaver/cc-nano-banana, https://mkdev.me/posts/unlimited-image-generation-with-nano-banana-pro-and-custom-claude-code-skill |
| **Author** | Multiple: DAIR.AI cohort member (X post), Google DeepMind (Agentic Vision), Kirill Shevchenko (mkdev.me skill), Keanan Koppenhaver (GitHub skill) |
| **Date** | January 27-31, 2026 |
| **Type** | Practitioner + Product launch (composite source) |
| **Processed** | January 31, 2026 |
| **Credibility** | 7 |
| **Items Extracted** | 12 |
| **Patterns Identified** | P52 (new); P5, P6, P41 (reinforced) |
| **Intake Mode** | DEEP |

## TL;DR (3 lines max)

Agents can now generate, evaluate, and iteratively improve images via self-critiquing loops — "Agentic Image Generation." Nano Banana Pro (Gemini 3 Pro Image) provides the API, Claude Code skills provide the orchestration, and visual annotation plugins close the human feedback loop. Google's Agentic Vision (Think→Act→Observe) formalizes this as a model-native capability. **Directly applicable to Baby Brains Instagram carousel production.**

## Key Thesis

> Agentic image generation combines an AI coding agent's analytical capability with image generation APIs in a self-improving loop — the agent generates, evaluates its own output, identifies flaws, adjusts prompts, and regenerates until quality meets threshold. Human visual annotations can further guide this loop with spatial precision.

---

## Extracted Items

### Nano Banana Pro (Image Generation Model)

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S19.01 | **Nano Banana Pro = Gemini 3 Pro Image** — Google's most advanced image gen model. Text-to-image + image-to-image, 1K/2K/4K resolution. Codename that stuck from internal development | `TOOLS` | HIGH | HIGH | 7.5 | -- | The underlying model for BB content. ~$0.13/4K image via Google AI Studio, ~$0.04/image for Flash variant |
| S19.02 | **Free API access exists** — Puter.js offers Nano Banana (Gemini 3 Pro + 2.5 Flash Image) at zero cost, no API key required. Together AI also provides access | `TOOLS` `COST` | MEDIUM | MEDIUM | 5.8 | P3 | Could dramatically reduce BB content costs. Verify rate limits and quality before relying on free tier |
| S19.03 | **SynthID watermarking on all output** — All Gemini-generated images include invisible SynthID watermark denoting AI origin. Cannot be removed | `BUSINESS` `SECURITY` | HIGH | HIGH | 6.5 | -- | BB must decide: transparent about AI imagery, or use as starting point with human editing? Industry-standard practice |

### Agentic Image Generation Loop

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S19.04 | **Self-improving image generation loop** — Agent generates image, evaluates output against intent, identifies flaws ("stopwatch floating unnaturally"), adjusts prompt, regenerates. 100+ icons produced iteratively for $45 | `ARCH` `TOOLS` | HIGH | HIGH | 7.8 | P52, P5 | Core pattern: generate → evaluate → critique → retry. Same loop structure as our activity pipeline (ELEVATE→AUDIT→RETRY) |
| S19.05 | **Claude Code skill wraps Nano Banana API** — Tiny Python script as Claude Code skill enables image gen within coding workflows. Skills installed at `~/.claude/skills/nano-banana/`. Multiple implementations available (GitHub, MCP server) | `TOOLS` `ARCH` | HIGH | HIGH | 7.2 | P50, P52 | Validates S18 plugin pattern: skill = domain capability. Could build BB image gen as Claude Code skill |
| S19.06 | **Visual annotation as agent feedback** — Playground plugin enables humans to provide precise spatial annotations (draw, circle, arrow) that the agentic loop uses to make better API calls. "Visual cues are extremely powerful for agents" | `ARCH` `UX` | HIGH | MEDIUM | 7.0 | P52, P6 | Human draws "make this bigger" circle → agent interprets → regenerates. Brain (human spatial cues) + Hands (agent generation) |
| S19.07 | **Multiple visual feedback plugins emerging** — ShowMe (mockup + annotation), Plannotator (plan review + annotation), Frontend Dev (AI visual testing). Ecosystem forming around visual agent feedback | `TOOLS` `COMMUNITY` | MEDIUM | HIGH | 6.2 | P52 | Visual feedback loop is becoming a recognized pattern. Not just one practitioner's idea |

### Google Agentic Vision (Gemini 3 Flash)

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S19.08 | **Agentic Vision: Think→Act→Observe loop** — Model analyzes image, generates Python code to manipulate/annotate it, re-examines modified image. Converts image understanding from static act to agentic process | `ARCH` `TOOLS` | HIGH | HIGH | 8.1 | P52 | Google formalizing what practitioners discovered independently. Model-native agentic vision. 5-10% quality boost across vision benchmarks |
| S19.09 | **Zoom & Inspect capability** — Model detects when details too small, writes code to crop and re-examine at higher resolution. Serial numbers, gauges, small text all become readable | `ARCH` | MEDIUM | HIGH | 6.5 | P52 | Could apply to BB: agent inspects generated carousel images, zooms to verify text readability on mobile |
| S19.10 | **Image annotation for transparency** — Model draws bounding boxes, arrows, labels directly on images. Output is auditable — you can see HOW the model arrived at its conclusion | `SECURITY` `ARCH` | MEDIUM | HIGH | 6.8 | P52 | Auditability pattern: agent shows its work visually. Applicable to QC pipeline — agent annotates what it changed and why |

### Baby Brains Content Pipeline Implications

| # | Item | Tags | Rel | Conf | Signal | Patterns | Notes |
|---|------|------|-----|------|--------|----------|-------|
| S19.11 | **Instagram carousel automation pipeline** — Combine: trend research → content brief → Nano Banana image gen → agentic QC loop → carousel assembly → platform-specific export. Agent iterates on brand consistency | `BUSINESS` `ARCH` | HIGH | MEDIUM | 7.4 | P52, P5, P12 | Maps to BB content pipeline (S3 in sprint tasks). Agentic image gen fills the "visual asset" gap. Human reviews final output |
| S19.12 | **Cost-effective at scale** — 100+ icons for $45 (practitioner report). 4K images ~$0.13 each via Google AI Studio. Free tiers available. BB could produce weekly carousel visuals for under $5/week | `COST` `BUSINESS` | HIGH | MEDIUM | 6.8 | P3 | Compare to: stock photos ($10-50/image), designer ($50-200/carousel), or Canva Pro ($13/month). Agentic gen is cheapest at quality |

---

## Patterns Identified

**Pattern P52: Agentic Vision = Think→Act→Observe for Multimodal (NEW)**
Agents can now SEE their own output and iterate on it. The pattern: generate visual output → evaluate against criteria → identify specific flaws → modify prompt/parameters → regenerate. Works for image generation (Nano Banana loop), image understanding (Google Agentic Vision), and visual QC (annotation plugins). This is the visual equivalent of our text-based activity pipeline (ELEVATE→AUDIT→RETRY). ATLAS implications: BB content pipeline should include agentic image QC; visual annotation could enhance any pipeline that produces visual output.

**Existing patterns reinforced:**
- **P5** (Proactive > Reactive): Self-improving loops are inherently proactive — agent notices flaws without being told.
- **P6** (Brain + Hands): Human provides spatial annotations (brain), agent generates/regenerates (hands).
- **P41** (Developer as Engineering Manager): Practitioner directs image generation via high-level prompts; agent handles iteration.
- **P50** (Plugin Architecture): Nano Banana skill IS a Claude Code plugin following the canonical pattern from S18.

---

## Action Items

| ID | Action | Priority | Status | Depends On | Rationale |
|----|--------|----------|--------|------------|-----------|
| A57 | Evaluate Nano Banana Pro API for BB carousel image generation — test with sample carousel, measure quality and cost | P1 | TODO | -- | Cheapest high-quality option; free tier exists; directly applicable to content pipeline |
| A58 | Build BB image generation Claude Code skill — wrap Nano Banana API with BB brand guidelines as system context | P2 | TODO | A57 | Skill = reusable pipeline component. Include brand colors, fonts, style rules in skill context |
| A59 | Investigate Agentic Vision (Gemini 3 Flash) for visual QC — test carousel images through Think→Act→Observe for readability/consistency checks | P2 | TODO | A57 | 5-10% quality boost from code-driven analysis; auditability via annotations |
| A60 | Research SynthID implications for BB content — determine policy on AI-generated imagery disclosure | P2 | TODO | -- | Regulatory and brand trust consideration. All Nano Banana output has invisible watermark |

---

## Cross-References

| This Source | Connects To | Relationship |
|-------------|-------------|-------------|
| S19.04 (self-improving loop) | S14.34 (Reflexion/Wait Pattern, P34) | Same meta-pattern: generate → evaluate → reflect → retry. Text version is Reflexion; image version is agentic image gen |
| S19.05 (Claude Code skill) | S18.01 (plugin architecture, P50) | Nano Banana skill follows the canonical plugin pattern (skills + commands) |
| S19.06 (visual annotation) | S2.06 (Brain + Hands, P6) | Human spatial annotation = brain input; agent generation = hands execution |
| S19.08 (Agentic Vision) | S14.32 (hybrid planning, P32) | Think→Act→Observe is Plan-and-Execute with visual modality. Model plans analysis, executes code, observes result |
| S19.11 (carousel pipeline) | BB Sprint Task bb-3 (content production pipeline) | Agentic image gen fills the visual asset production gap in BB content pipeline |
| S19.12 (cost) | S1.03 (cost awareness, P3) | $0.04-0.13/image makes agent-generated visuals cheaper than any alternative |

---

## Credibility Assessment

| Dimension | Score (1-10) | Notes |
|-----------|-------------|-------|
| Author expertise | 7 | Practitioners (DAIR.AI cohort, mkdev.me) + Google DeepMind (Agentic Vision). Mixed practitioner + first-party |
| Evidence quality | 7 | Practitioner reports with cost data ($45/100 icons). Google benchmarks (5-10% improvement). No peer review |
| Recency | 10 | January 27-31, 2026 (this week) |
| Reproducibility | 8 | Open-source skills, public APIs, free tiers. Anyone can replicate |
| Bias risk (10=none) | 6 | Google promoting their model. Practitioners may over-hype. But open-source and verifiable |
| **Composite** | **7** | |

### Strengths
- Multiple independent practitioners converging on same pattern (agentic image loops)
- Google formalizing with Agentic Vision (first-party model capability, not just a hack)
- Cost data from real usage ($45 for 100+ icons, $0.04-0.13/image)
- Directly applicable to Baby Brains content pipeline gap
- Open-source implementations available to study

### Weaknesses
- X.com post is anecdotal (single practitioner, cohort marketing context)
- "Playground plugin" details sparse — couldn't find specific implementation
- Agentic Vision is brand new (Jan 27), no independent validation yet
- Self-improving loop quality ceiling unclear — when does iteration stop improving?
- SynthID watermark implications for brand content not well understood

---

## Noise Filter

- DAIR.AI cohort marketing ("sign up for my course") — filtered, extracted only the technical pattern
- "This is insane!" social media hype — filtered
- Nano Banana naming history — noted but not relevant to architecture
- Leonardo AI pricing details — too specific to one platform, noted API cost range instead
- Multiple GitHub forks of nano-banana skill — one reference implementation is sufficient

---

## Verification Checklist

- [x] **Fact-Check**: Nano Banana Pro = Gemini 3 Pro Image confirmed via Google DeepMind page. $45/100 icons from practitioner report (mkdev.me). Free API via Puter.js verified. Agentic Vision confirmed via Google blog (Jan 28).
- [x] **Confidence Extraction**: Each item tagged. HIGH for model capabilities and pricing (verifiable). MEDIUM for pipeline implications (projected, not tested by us).
- [x] **Wait Pattern**: "What assumptions am I making?" — Assuming BB carousel images can be adequately generated by AI. May need human graphic designer for brand-critical assets. Assuming agentic loop converges (no evidence of infinite retry). Assuming SynthID isn't a deal-breaker for BB brand.
- [ ] **Inversion Test** (for Signal >= 8 items): S19.08 Agentic Vision (8.1): "What would make this wrong?" — If code execution adds latency that makes it impractical for batch processing. If 5-10% improvement is benchmark-specific and doesn't transfer to carousel-style images. Reasonable risk — MEDIUM confidence that it transfers to our use case.

---

*S19 processed: 2026-01-31*
