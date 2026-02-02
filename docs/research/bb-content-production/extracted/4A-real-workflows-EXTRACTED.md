# 4A: Real AI Video Production Workflows — Extracted Data

**Source file:** `docs/research/bb-content-production/results/4A.md`
**Extraction date:** 2026-02-01
**Extraction scope:** Every workflow, tool stack, time estimate, cost figure, success rate, and practitioner datapoint in the source document.

---

## CREATOR/STUDIO PROFILES

### Alex Braun
- **Platform(s):** Not specified (workflow documented on Medium)
- **Content type:** Illustrated/animated short-form content
- **Monthly output:** Not specified
- **Tool stack (exact):** MidJourney (images) + Kling AI (animation) — full five-stage pipeline (script, image gen, video animation, voiceover, assembly)
- **Monthly tool spend:** Not specified individually
- **Time per video:** Not specified individually
- **Success rate per generation:** Not specified individually
- **Workflow (step by step):**
  1. Script generation via ChatGPT or Claude (structured scripts with image prompts at ~20-second intervals)
  2. Image generation in MidJourney (keyframe illustrations with consistent character prompts, fixed aspect ratios, identical style descriptors)
  3. Video animation via Kling AI image-to-video (Elements feature for character consistency)
  4. Voiceover via ElevenLabs or Hailuo AI
  5. Assembly in DaVinci Resolve, CapCut, or Premiere Pro
- **Source URL:** Medium (late 2025) — no direct URL provided
- **Confidence:** CLAIMED — named as practitioner of the dominant pipeline, but no direct output metrics attributed

### Diana D.
- **Platform(s):** Not specified
- **Content type:** Animated commercial
- **Monthly output:** Not specified (single project referenced)
- **Tool stack (exact):** Not fully specified; Kling AI implied (re-renders, unprompted characters appearing)
- **Monthly tool spend:** Spent **$125 USD** on a single animated commercial
- **Time per video:** Not specified
- **Success rate per generation:** Very low — multiple re-renders due to unprompted characters appearing in scenes
- **Workflow:** Not detailed beyond re-render mentions
- **Source URL:** Trustpilot review, October 2025
- **Confidence:** VERIFIED — specific dollar figure from named Trustpilot reviewer with date

### Tory (DEV Community)
- **Platform(s):** DEV Community (analysis author, not necessarily a video creator)
- **Content type:** Cost analysis/benchmarking across AI video platforms
- **Monthly output:** N/A (analyst, not producer)
- **Tool stack (exact):** Tested: Pika 2.0, Kling 2.6 (with audio), and others
- **Monthly tool spend:** N/A
- **Time per video:** N/A
- **Success rate per generation:** Reports only 2-3 of 10 generations are publication-worthy for complex scenes
- **Workflow:** Systematic cost comparison across platforms
- **Source URL:** https://dev.to/toryreut/everyones-generating-videos-i-calculated-what-ai-video-actually-costs-in-2026-37ag (January 7, 2026)
- **Confidence:** VERIFIED — direct URL, dated, named author

### CrePal.ai
- **Platform(s):** Not specified (testing/review entity)
- **Content type:** Kling AI Elements feature testing
- **Monthly output:** 50+ test generations reported
- **Tool stack (exact):** Kling AI with Elements feature
- **Monthly tool spend:** Not specified
- **Time per video:** Not specified
- **Success rate per generation:** **50-70%** character consistency success rate
- **Workflow:** Not detailed beyond Elements testing
- **Source URL:** Not directly provided
- **Confidence:** CLAIMED — attributed figure but no direct URL to verify methodology

### Reddit Community (r/AIVideo, r/KlingAI)
- **Platform(s):** Reddit
- **Content type:** AI-generated video (various)
- **Monthly output:** Varies
- **Tool stack (exact):** Primarily Kling AI
- **Monthly tool spend:** Varies
- **Time per video:** Not specified
- **Success rate per generation:** Consensus: **2-3 generations per usable output**; lip sync **7/10 success rate**
- **Workflow:** Not individually detailed
- **Source URL:** r/aivideo (147 upvotes on referenced analysis post — no direct URL)
- **Confidence:** CLAIMED — aggregated community sentiment, not individually verifiable

---

## MJ + KLING PIPELINE (Image-to-Video)

### The Dominant Five-Stage Pipeline
1. **Script Generation** — ChatGPT or Claude; structured scripts with image prompts at ~20-second intervals
2. **Image Generation** — MidJourney; keyframe illustrations with:
   - "Immutable traits" defined (fur color, eye shape, signature accessories)
   - Fixed aspect ratios: 16:9 (YouTube), 9:16 (TikTok/Reels)
   - Identical style descriptors across all images ("soft pastel, watercolor, whimsical lighting")
3. **Video Animation** — Kling AI image-to-video:
   - Elements feature (Kling 1.6+): upload 1-4 reference images for character consistency
   - Kling 2.6: motion control combining reference videos with character images
4. **Voiceover** — ElevenLabs or Hailuo AI (TTS)
5. **Assembly** — DaVinci Resolve (free), CapCut (free/$10-20/mo), or Premiere Pro

### Generations Per Usable Result
- **Reddit consensus:** 2-3 generations per usable output [CLAIMED — community aggregation]
- **Trustpilot users:** "many many tries before you get something usable" for complex prompts [CLAIMED — qualitative]
- **Tory (DEV Community):** Only 2-3 of 10 generations are publication-worthy for complex scenes [CLAIMED — single analyst]
- **Hidden cost multiplier:** Failed attempts consume **3-5x nominal budget** [CLAIMED — Tory's analysis]
- **Lip sync success rate:** ~7/10 with "slight uncanny valley effect" [CLAIMED — Reddit]
- **Known bug:** Some generations fail at 99% completion — affects both free and paid users [CLAIMED — Reddit/Trustpilot]
- **Confidence:** The 2-3 attempts figure is CLAIMED but appears from multiple independent sources (Reddit, Trustpilot, DEV Community), suggesting reasonable reliability. The "2-3 of 10" figure from Tory appears to describe complex scenes specifically and CONTRADICTS the "2-3 attempts" figure for simpler content — these describe different difficulty tiers.

### Character Consistency Across Clips
- **Does it hold?** Partially. 50-70% success rate with Kling Elements (CrePal.ai, 50+ tests) [CLAIMED]
- **Reddit consensus:** "Character consistency is miles ahead of competitors" but "faces may drift in longer clips" [CLAIMED]
- **MidJourney --cref (now --oref in V7):**
  - Works best with MJ-generated images, NOT photographs [CLAIMED]
  - --cw parameter (0-100) controls fidelity: 100 = all details, 0 = face only [VERIFIED — matches MJ docs]
  - Cannot precisely replicate dimples, freckles, or specific clothing details [CLAIMED]
  - No direct video-to-video support — must generate images first, then animate externally [VERIFIED — architectural limitation]
- **Kling Elements feature:** Upload up to **7 reference images** (source says "up to 7" in consistency section but "1-4" in pipeline section) [CONTRADICTED internally — 1-4 vs 7 reference images]

### Clip Stitching Methods
- **Not explicitly detailed** in the source document
- Implied: Assembly stage in DaVinci Resolve / CapCut / Premiere Pro handles combining clips
- **Reference chaining** mentioned as a workaround: use last frame of completed segment as reference for next prompt
- **Last-frame extraction** recommended for scene continuity
- **Confidence:** INCOMPLETE — the source does not deeply cover stitching methodology

### Editing Software Used
- **DaVinci Resolve** — free; DaVinci Resolve 20 Studio $295 one-time; includes AI IntelliScript, AI Audio Assistant, Magic Mask
- **CapCut** — Free / Standard ~$10/mo / Pro ~$13-20/mo
- **Premiere Pro** — mentioned but no pricing given
- **AutoCut plugin** (for DaVinci Resolve) — $15-40/month; auto-remove silences, auto-captions, auto-podcast editing

---

## HIGH-VOLUME PRODUCTION (20-30+ videos/month)

### Batching Strategies
**Four-phase batch workflow (from n8n templates and documented practices):**

| Phase | Day(s) | Activities |
|-------|--------|------------|
| Phase 1: Preparation | Day 1 | Create character bible (appearance, poses, expressions); generate 6-10 reference images; batch write 30 scripts via ChatGPT/Claude; set up templates in assembly tool |
| Phase 2: Asset Generation | Days 2-3 | Batch generate all character images (grouped by scene type); create voice tracks with ElevenLabs batch processing; organize assets in folders by video |
| Phase 3: Video Assembly | Days 4-5 | Template-based assembly via Creatomate; batch animate images with Kling Elements; add captions/effects using templates |
| Phase 4: Export & Distribution | Day 6 | Export in platform formats (16:9, 9:16, 1:1); schedule via upload-post.com or social schedulers |

**Confidence:** CLAIMED — described as common practice across creators, sourced from n8n templates and unspecified "documented practices"

### Time Investment Per Month
| Content Type | Monthly Hours | Notes |
|--------------|---------------|-------|
| Simple faceless shorts (30/mo) | 15-20 hours | "Achievable in 1-2 days" |
| Character-consistent shorts (30/mo) | 45-75 hours | "Spread over month" |
| 25 videos/month (recommended target) | 15-25 hours | "Batchable to 4-5 concentrated days" |

- **AI workflows save 55-63%** of production time vs. traditional methods [CLAIMED — Artlist Creative Trend Report 2026]
- **Per-video time:** 30-60 minutes after workflow is established [CLAIMED — recommendation section]
- **Confidence:** The 15-25 hours for 25 videos and 30-60 min per video are CONTRADICTED internally. 25 videos x 30 min = 12.5 hours (below range); 25 videos x 60 min = 25 hours (top of range). The range is internally consistent at the boundaries but the "after workflow is established" qualifier suggests optimistic estimates.

### Automation Tools Used

| Tool | Function | Monthly Cost | Confidence |
|------|----------|--------------|------------|
| Creatomate | CSV-to-video batch generation | $54 (Essential, ~200 videos) / $99 (Growth, ~1,000 videos) | VERIFIED — pricing page cited |
| n8n + ComfyUI | Automated idea-to-video pipeline | Free-$20 | CLAIMED |
| Make.com + HeyGen | Bulk video from spreadsheets | $29+ | CLAIMED |
| Plainly | After Effects template batching | $69+ | CLAIMED |

### Per-Video Production Cost
- **$0.14/video** — Pika 2.0 Standard (cheapest, no commercial use) [VERIFIED — Tory analysis]
- **$0.60/video** — Kling AI Standard [VERIFIED — Tory analysis]
- **$0.70-1.00/video** — Runway Gen-4 Standard [VERIFIED — Tory analysis]
- **$1-2/video** — Simple character animation on Kling Standard [CLAIMED]
- **$1.80-2.70/video** — Creatomate templated production [CLAIMED — derived from plan pricing]
- **$2-5/video** — Including failed generations (recommended budget) [CLAIMED]
- **$2.30/video** — Kling AI Pro [VERIFIED — Tory analysis]
- **$3-5+/video** — Standard per-video cost with iterations [CLAIMED]
- **$13.50/video** — Kling 2.6 with audio (most expensive) [VERIFIED — Tory analysis]
- **$125 total** — Single animated commercial (extreme failure case) [VERIFIED — Trustpilot]
- **96x price spread** between cheapest and most expensive options [VERIFIED — Tory analysis: $0.14 to $13.50]

---

## ASSEMBLY TOOLS

### CapCut
- **Still best free option?** YES for manual editing. Document states: "CapCut remains the best free/low-cost option for manual editing" [CLAIMED]
- **2026 Pricing:**
  - Free: Basic editing, 1080p export, watermark on some templates, auto-adds CapCut ending clip (removable)
  - Standard: ~$10/month — watermark removal, some premium effects
  - Pro: ~$13-20/month — 4K/HDR export, full AI tools, cloud storage
- **Strengths:**
  - AI Script-to-Video (input text, AI assembles draft)
  - AI Clip Maker (auto-generates multiple shorts with captions)
  - 100+ auto-caption templates
  - Excellent social media format exports
- **Limitations:**
  - **No API access** — cannot programmatically batch generate
  - Manual workflow required despite AI assistance
  - Feature gating: AI Script Rewriter limited to 5/day even on Pro
  - No integration with Zapier, Make, or automation tools
- **ByteDance pricing changes (2024-2025)** introduced limitations [CLAIMED — no specifics given]
- **Confidence:** CLAIMED for "best free option" — comparative claim without systematic comparison

### Alternatives (2026)

#### For API-Driven Batch Production:
| Tool | Pros | Cons | Cost | Confidence |
|------|------|------|------|------------|
| **Creatomate** | Template-based REST API; CSV-to-video bulk; built-in ElevenLabs integration; best value for batch | Not mentioned | Essential $54/mo (~200 videos), Growth $99/mo (~1,000 videos) | VERIFIED (pricing page cited) |
| **Shotstack** | JSON-based API; integrates with AI tools; developer-friendly | Not mentioned | $49/mo for 200 minutes | CLAIMED |
| **Remotion** | React-based; free for individuals | Requires React knowledge | Free (individuals); Lambda ~$0.001-0.02/video | CLAIMED |

#### For Manual Editing with AI Assistance:
| Tool | Pros | Cons | Cost | Confidence |
|------|------|------|------|------------|
| **DaVinci Resolve 20** | AI IntelliScript, AI Audio Assistant, Magic Mask; powerful free tier | Steeper learning curve (implied) | Free / $295 one-time (Studio) | VERIFIED (well-known pricing) |
| **AutoCut plugin** (for DaVinci) | Auto-remove silences (1hr video -> 30s); auto-captions (1hr subtitles -> 1min); auto-podcast editing | Requires DaVinci Resolve | $15-40/month | CLAIMED |

### API-Driven Assembly (Creatomate etc.)
- **Viable for batch?** YES — explicitly recommended for 20-30 videos/month scaling
- **Creatomate specifics:**
  - Supports creating batches of 30+ videos from single spreadsheet upload
  - CSV data input documented (geography shorts example)
  - REST API for template-based generation
  - Built-in ElevenLabs integration for voiceover
  - Per-video cost: ~$1.80-2.70 (derived from $54/200 videos and $54/20 videos)
- **Confidence:** CLAIMED for workflow viability; VERIFIED for pricing

---

## CHARACTER CONSISTENCY IN PRACTICE

### --cref Reliability for Video
- **MidJourney --cref** is now **--oref (Omni-Reference) in V7** [CLAIMED — version-specific]
- Works best with MJ-generated images, not photographs
- --cw (character weight) parameter: 0-100 scale; 100 = all details, 0 = face only
- **Cannot** precisely replicate: dimples, freckles, specific clothing details
- **No direct video-to-video support** — must generate consistent images first, then animate externally
- **Confidence:** CLAIMED — consistent with known MJ documentation but V7/oref transition timing not independently verified in this document

### Workarounds Developed
1. **Seed locking** — Lock seeds across generations for style consistency
2. **Reference chaining** — Use last frame of completed segment as reference for next prompt
3. **Character bibles** — Define immutable traits in detailed prompts, use consistently
4. **Multi-step quality check** — Generate, refine in MidJourney/Flux, then feed to Kling
5. **LoRA training** — Train custom models on 15-30 reference images; ~$2 per training run on fal.ai; unlimited consistent generations afterward
6. **Post-processing face fix** — Apply faceswap after generation; use ADetailer for face fixing

**Confidence:** CLAIMED — these are described as practitioner-developed workarounds without specific attribution per technique

### Better Approaches Than MJ+Kling

| Tool | Best For | Character Consistency Rating | Confidence |
|------|----------|------------------------------|------------|
| **Higgsfield Popcorn** | Built specifically for consistency | Excellent | CLAIMED — no evidence cited |
| **Runway Gen-4 References** | Multi-perspective scene creation | Excellent | CLAIMED — no evidence cited |
| **Kling AI Elements** | Best value for animated content | Good (50-70%) | CLAIMED — CrePal.ai testing |
| **LTX Studio Elements** | Persistent character assets | Good | CLAIMED — no evidence cited |
| **ComfyUI + LoRA** | Maximum control | Excellent (with setup time) | CLAIMED — no evidence cited |

**For illustrated children's content specifically:** Create "hero character sheet" in MJ (front, side, three-quarter views), use Kling Elements with those references. Favor simple silhouettes and solid colors; avoid complex patterns that drift. [CLAIMED — recommendation, not empirically tested in document]

---

## WORKFLOW PATTERNS

Distilled common patterns across all creators mentioned:

1. **Character Bible First:** Every successful high-volume creator starts by defining immutable character traits, generating reference sheets, and maintaining consistency documents before any production begins.

2. **Script Batching:** Scripts are written in bulk (30 at a time) using LLMs (ChatGPT/Claude) with structured prompts that include image generation directives at ~20-second intervals.

3. **Asset Generation Before Assembly:** All images and voice tracks are generated in dedicated phases (Days 2-3) before any video assembly begins, enabling parallel processing and quality checks.

4. **Template-Driven Assembly:** At scale (20+ videos), creators shift from manual editing to template-based tools (Creatomate, Plainly) that accept CSV/spreadsheet input for batch generation.

5. **Reference Chaining for Continuity:** Last frame of each completed segment becomes the reference image for the next segment's generation, maintaining visual continuity across clips.

6. **Failure Budget Planning:** Successful practitioners budget 2-3x their nominal generation costs and time to account for failed/unusable outputs. Complex scenes may require up to 10 attempts for 2-3 usable results.

7. **Style Simplification for AI:** Illustrated/stylized aesthetics (watercolor, pastel, simple silhouettes) are deliberately chosen over photorealistic styles because AI handles them more consistently.

8. **Multi-Format Export:** Videos are produced once and exported in three aspect ratios (16:9, 9:16, 1:1) for cross-platform distribution (YouTube, TikTok/Reels, Facebook).

---

## KEY NUMBERS (Quick Reference)

| Metric | Value | Confidence |
|--------|-------|------------|
| **Average time per video** | 30-60 minutes (after workflow established) | CLAIMED |
| **Average cost per video** | $2-5 including failures | CLAIMED |
| **Average takes per keeper** | 2-3 generations (simple); up to 10 attempts for 2-3 keepers (complex) | CLAIMED (multiple sources) |
| **Most common tool stack** | MidJourney + Kling AI + ElevenLabs + CapCut | CLAIMED (presented as dominant) |
| **Most common tool stack cost** | $38-48/month (basic) / $55-65/month (with more headroom) | CLAIMED |
| **Character consistency rate (Kling Elements)** | 50-70% | CLAIMED (CrePal.ai) |
| **Lip sync success rate** | ~70% (7/10) | CLAIMED (Reddit) |
| **Monthly hours for 25 videos** | 15-25 hours | CLAIMED |
| **Monthly hours for 30 faceless shorts** | 15-20 hours | CLAIMED |
| **Monthly hours for 30 character-consistent shorts** | 45-75 hours | CLAIMED |
| **AI time savings vs. traditional** | 55-63% | CLAIMED (Artlist report) |
| **Cheapest per-video cost** | $0.14 (Pika 2.0, no commercial use) | VERIFIED (Tory) |
| **Most expensive per-video cost** | $13.50 (Kling 2.6 with audio) | VERIFIED (Tory) |
| **Price spread across platforms** | 96x | VERIFIED (derived) |
| **Worst-case single project cost** | $125 (Diana D., animated commercial) | VERIFIED (Trustpilot) |
| **LoRA training cost** | ~$2 per run on fal.ai | CLAIMED |
| **Creators using AI tools** | 87% of creative professionals | CLAIMED (Artlist, 6,500+ surveyed) |
| **Content production increase with AI** | 5-10x more with same resources | CLAIMED (Artlist) |

---

## CONTRADICTIONS & UNCERTAINTIES

### Internal Contradictions
1. **Kling Elements reference image limit:** The pipeline section states "1-4 reference images" but the character consistency section states "up to 7 reference images." These are in the same document and one must be incorrect. The 7-image figure appears in the more detailed consistency section and may be the correct current limit.

2. **Generation success rates — severity mismatch:** The "2-3 generations per usable output" consensus (simple content) vs. "2-3 of 10 publication-worthy" (complex scenes) represent very different failure rates (33-50% failure vs. 70-80% failure). The document does not clearly delineate when each applies, though context suggests the 2-3/10 rate is for complex scenes only.

3. **Tool stack cost totals:** The first table totals $55-65/month, but the recommendation section totals $38-48/month for an apparently similar stack. The difference: MidJourney Pro ($30) in the first vs. MidJourney Standard ($10) in the second. This is not a contradiction but could confuse readers — two different MidJourney tiers are recommended in different sections without explicit acknowledgment.

4. **Monthly time for 25 videos:** Stated as "15-25 hours" and per-video time as "30-60 minutes." At 30 min x 25 = 12.5 hours (below range); at 60 min x 25 = 25 hours (matches top). The low end of the per-video estimate is inconsistent with the low end of the monthly estimate.

### Uncertainties
1. **Artlist Creative Trend Report figures** (87% AI adoption, 5-10x productivity, 55-63% time savings): These come from a single survey by a commercial entity (Artlist) that sells creative tools. Possible sampling bias — their 6,500 respondents are likely already AI-adjacent.

2. **CrePal.ai 50-70% consistency rate:** No methodology disclosed. "50+ test generations" is a small sample. The range (50-70%) is wide enough to suggest significant variability.

3. **Tory's cost analysis:** Single analyst's calculations. Per-video costs depend heavily on plan utilization rates and generation complexity. The $0.14 Pika figure assumes full plan utilization.

4. **"No commercial use" on Pika 2.0 Standard ($0.14/video):** Flagged in the pricing table but easy to overlook. This makes the cheapest option unusable for Baby Brains.

5. **Higgsfield Popcorn and LTX Studio Elements** are rated "Excellent" and "Good" respectively for character consistency with zero supporting evidence in the document.

6. **Hailuo AI** mentioned as voiceover alternative to ElevenLabs but with no pricing, quality comparison, or further detail.

7. **n8n + ComfyUI pipeline** listed as "Free-$20" but ComfyUI setup complexity and hardware requirements are not discussed.

8. **DaVinci Resolve 20 AI features** (IntelliScript, Audio Assistant) — version 20 specific features not independently verified in this document.

---

## SOURCE URLS

All URLs explicitly referenced in the source document:

1. **DEV Community — Tory cost analysis (Jan 7, 2026):**
   https://dev.to/toryreut/everyones-generating-videos-i-calculated-what-ai-video-actually-costs-in-2026-37ag

2. **Artlist Creative Trend Report 2026 (Nov 20, 2025):**
   https://artlist.io/blog/artlist-creative-trend-report-2026/

3. **Creatomate pricing:**
   https://creatomate.com/pricing

4. **MidJourney official video documentation:**
   https://docs.midjourney.com/hc/en-us/articles/37460773864589-Video

5. **Kling AI Trustpilot reviews (189 reviews):**
   https://www.trustpilot.com/review/klingai.com

6. **n8n automation workflow:**
   https://n8n.io/workflows/3121-ai-powered-short-form-video-generator-with-openai-flux-kling-and-elevenlabs/

7. **Geeky Gadgets — Kling Elements guide:**
   https://www.geeky-gadgets.com/how-to-create-consistent-characters-with-kling-ai/

**Sources referenced but without direct URLs:**
- Alex Braun's Medium article (late 2025)
- YouTube tutorials (unspecified)
- Reddit r/AIVideo and r/KlingAI posts (specific post with 147 upvotes referenced but not linked)
- CrePal.ai testing report
- Diana D. Trustpilot review (October 2025)
- Trustpilot reviews (189 total referenced)
