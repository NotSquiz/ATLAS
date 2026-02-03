# Baby Brains Content Production: Master Synthesis

> Cross-referencing 13 extraction reports (1A through 8A) + Phase 2 research (PA-PF)
> Compiled: 2026-02-02, updated 2026-02-02
> Status: ALL research complete. Phase 1 (13 prompts) + Phase 2 (6 prompts) fully synthesized.
> Next: Begin implementation. See Build Priority Roadmap in Pipeline Decision 8.

---

## EXECUTIVE SUMMARY

Thirteen research files were extracted, categorized, and confidence-tagged by independent agents. This synthesis resolves contradictions, identifies clear winners, and provides actionable decision paths across six decision gates.

**Top-line findings:**

1. **No single tool wins everything.** Kling is the only tool that generates 60s natively, but it scores poorly for stylized/clay content (2.5/5 Pixar-style success, 30-40% first-try). Pika scores highest for stylized quality (5/5, 74-89% success) but maxes out at 25s. The optimal stack is a two-tool setup.

2. **The video length debate is resolved by content type, not a single number.** Educational parenting content on TikTok gets 43.2% more reach at 60s+ (Napolify, VERIFIED). But completion rates crater at those lengths (31% for 60s-3min). The data supports a multi-length strategy: 30-60s as the primary format, with 15-25s hooks and 60-90s deep dives.

3. **Human voice is non-negotiable.** AI voiceover faces 38% lower FYP exposure on TikTok post-November 2025 (3A). Business accounts cannot access trending sounds (3A). Qwen3-TTS (already installed in ATLAS, 0.6B, voice cloning) runs locally for $0/month. Fish Audio API (~$11/mo Plus tier, #1 TTS-Arena) is the primary cloud fallback. Google Colab VS Code extension provides a free T4 GPU (15GB) for heavier models like Maya1 (3B, voice design via natural language). Self-recorded Australian voiceover remains the gold standard.

4. **Stylized AI content is exempt from mandatory disclosure on ALL four platforms** (5A). MidJourney does not embed C2PA metadata. The anti-sharenting privacy framing is the recommended positioning.

5. **The competitive white space is real.** Zero Montessori+AI accounts exist worldwide (6A). The content is for PARENTS (adults), not children -- the Montessori community's screen-time concerns for under-6s do not apply to adult-facing educational content about Montessori principles.

6. **MidJourney V7 has replaced --cref with --oref** (8A). No reference features work with MJ video generation at all. Character-consistent video requires: generate still with --oref, upscale, then use Animate button.

---

## DECISION GATE 1: Video Generation Tool(s)

### The Problem

The user's budget target is $50-120/month. The 1C-recommended dual-tool setup (Kling Premier $92 + Pika Fancy $76 = $168) exceeds this. We need to find the right compromise between quality, capability, and cost.

### Cross-Referenced Tool Assessment

#### Kling AI 2.6

| Dimension | Data | Source | Confidence |
|-----------|------|--------|------------|
| Pricing (Pro) | $25.99-37/month, 3,000 credits | 1A, 1C | CLAIMED (price ranges vary) |
| Pricing (Premier) | $64.99-92/month, 8,000 credits | 1A, 1C | CLAIMED (price ranges vary) |
| Stylized 3D quality | 4/5 (1C) but Pixar-style only 2.5/5 (1A) | 1A, 1C | **CONTRADICTION** |
| First-try success (stylized) | 30-40% (1A) | 1A | CLAIMED |
| True cost multiplier (stylized) | 3-5x listed credit cost | 1A | CLAIMED |
| Character consistency | Elements, 4 reference images, 5/5 (1C) | 1C | CLAIMED |
| Max single generation | 2 minutes, 3 minutes via extension | 1C | CLAIMED |
| Native 60s | YES -- only tool in the industry | 1C | VERIFIED (unique capability) |
| Native audio | Yes (Kling 2.6), dialogue + SFX + ambient | 1A, 1C | CLAIMED |
| Trustpilot rating | 1.3/5 from 189 reviews (1A) OR 2.3/5 from 222 reviews (1C) | 1A, 1C | **CONTRADICTION** |
| Glow/SSS preservation | Best temporal stability, Motion Brush for isolation | 7A | CLAIMED |
| Real user cost for 25 videos/month | ~5,250 credits needed (with stylized multiplier) = Premier required | 1A | CLAIMED |
| Failed generations | **All failed generations consume credits with no refunds.** 99% freezes also consume full credits. | PC lines 62, 114 | VERIFIED |

**UPDATE (Feb 2026): Two major Kling releases:**

**Kling O1 (Omni One)** -- December 1, 2025. Unified 7-in-1 VIDEO engine (text-to-video, image-to-video, keyframe interpolation, video inpainting, style transformation, shot extension, reference-based generation). Supports **7-10 reference images** with `@image1` tagging syntax. Chain-of-thought reasoning. Start & end frame control.

**Kling IMAGE 3.0** -- Early access, February 2026. IMAGE generation model (not video). Key features:
- **Image Series Mode**: Single-Image-to-Series and Multi-Image-to-Series for generating storyboard sequences with unified style. Batch optimization for multiple images.
- **Visual Chain-of-Thought (vCoT)**: "Think first, render later." Scene decomposition, common-sense reasoning, causal judgment before generation. Handles abstract conceptual metaphors and complex narratives.
- **Native 2K/4K output**: Higher resolution source images for video pipeline input.
- **Deep-Stack Visual Information Flow**: Pixel-level consistency in key elements, style tone, and atmospheric details across a series.
- **Cinematic Narrative Aesthetic Engine**: Multi-dimensional narrative expression (composition, perspective, lighting, emotions).
- **Dual Reward Model**: Reinforcement learning balancing realism and cinematic aesthetics.

**Implication:** Kling IMAGE 3.0's Image Series Mode could potentially replace MidJourney for image generation -- it's designed for exactly our use case (consistent characters across multiple storyboard scenes). Needs testing once generally available. No pricing change -- same credit-based tiers. No unlimited tier.

> **Source note:** Kling IMAGE 3.0 features confirmed via Reddit announcement screenshots (Feb 2026) showing official Kling launch. Prerelease to selected accounts — not yet publicly documented or broadly available. PC.md lines 120-128 previously stated "no evidence"; user screenshots are primary evidence overriding that assessment.

**Kling verdict:** Essential for 60s content. O1's 7-10 reference images and unified model are a significant upgrade for character consistency. Still credit-hungry and no unlimited option. Budget: minimum Pro ($37) for limited volume, Premier ($92) for full production. Not viable for burst production strategy.

#### Pika 2.5

| Dimension | Data | Source | Confidence |
|-----------|------|--------|------------|
| Pricing (Fancy) | $76/month, 6,000 credits | 1C | CLAIMED |
| Pricing (Pro) | $28/month, 2,300 credits | 1C | CLAIMED |
| Stylized 3D quality | **5/5** -- purpose-built, Pikaffects clay deformation | 1C | CLAIMED |
| First-try success | **74-89%** -- highest in industry | 1C | CLAIMED |
| Character consistency | Pikaframes keyframing, 3/5 -- no reference-image system | 1C | CLAIMED |
| Max video length | 5s per generation, 25s via Pikaframes | 1C | CLAIMED |
| Audio | None | 1C | VERIFIED |
| Credits rollover | **Yes** -- paid plans now have roll-over credits (updated 2025) | 1C, Staleness report | UPDATED |

**⚠️ Commercial license update (late 2025):** Pika Standard ($8/month) now includes commercial use rights. Pro ($28/month) recommended for higher credit allocation but is no longer required for commercial use (4A line 56, updated).

**Quality caveat:** Pika's own documentation includes a disclaimer that the tool is "not suitable for professional-grade output" (1C line 72). This likely refers to photorealistic/VFX use cases — for stylized clay animation, Pika's 74-89% success rate and 5/5 quality score suggest it performs well within its niche.

**Per-video Kling cost range (cross-source):** Per-video costs vary significantly by source and assumptions: $1.61-1.76 per 10s video (1A line 93, assuming 50% stylized failure rate) vs $0.80-1.20 Pro / $0.45-0.70 Premier (1C lines 36-40, using higher success assumptions). The difference reflects failure rate assumptions for stylized content.

**Pika verdict:** Best quality for clay aesthetic but limited to 25s max. No audio. The high success rate (74-89%) means less credit waste. Standard ($8) now includes commercial rights; Pro ($28) recommended for credit allocation and higher generation limits.

#### MidJourney Video V1

| Dimension | Data | Source | Confidence |
|-----------|------|--------|------------|
| Pricing | Pro $60/month, Mega $120/month | 1B, 1C | VERIFIED |
| Stylized quality | **5/5** -- inherits MJ's signature aesthetic | 1C | CLAIMED |
| Video mode | **Image-to-video ONLY** -- cannot text-to-video | 1B | VERIFIED |
| Max video length | 5s per generation, 21s via 4s extensions | 1B, 8A | VERIFIED |
| Reference features for video | **NONE** -- --cref, --oref, --sref all incompatible with video | 8A | VERIFIED (official docs) |
| Character consistency for video | Workaround: generate still with --oref, upscale, Animate button | 8A | CLAIMED (community workaround) |
| Human motion success | ~50-60% overall (GamsGo testing); **multi-person/complex motion only 20% (1/5)** with position changes and limb deformation (1B line 100). Parent+baby scenes have an 80% failure rate. | 1B, 8A | CLAIMED |
| Video quality degradation | Best at 0-5s, noticeable at 13-17s, lowest at 17-21s | 8A | CLAIMED |
| Relax mode (unlimited SD) | Pro and Mega only | 1B | VERIFIED |
| Video costs 8x image GPU time | Yes | 1C | CLAIMED |
| Audio | None | 1B, 1C | VERIFIED |

**Cost optimization:** MJ video `--bs 1` cuts video cost by 4x (1B line 34). Use `--bs 2` for 2x savings. Essential for iterating on video clips. Note: MJ video is 24fps (1B line 32); HD 720p mode costs 3.2x more than SD (1B line 18).

**Overall MJ human motion success:** Empirical testing shows **41.7% (5/12)** across all motion types, excluding portrait animations (1B line 76). Portrait animations have 66.7% success. Single-person motion: 57%.

**MJ verdict:** Excellent stylized quality but severely limited for video. 21s max, no audio, no reference features in video mode, quality degrades after 9s. Best used as the IMAGE generation engine (--oref character consistency, --sref style) feeding into a separate video tool.

**⚠️ Pricing clarification:** MJ **VIDEO** Relax mode requires Pro ($60/month) or Mega ($120/month) — NOT available on Standard ($30/month). MJ **IMAGE** Relax mode IS available on Standard ($30/month). The recommended Stack A/B/C all use Standard for IMAGE generation, which is correct. Video generation costs 8x image GPU time and uses Fast GPU minutes on all plans.

#### Hailuo / MiniMax 2.3

| Dimension | Data | Source | Confidence |
|-----------|------|--------|------------|
| Pricing (Master) | $94.99/month -- 10,000 credits, **NOT unlimited** | User-verified Feb 2026 | VERIFIED |
| Pricing (Ultra) | $124.99/month -- 12,000 credits + unlimited Hailuo 01 (no credit cost) | User-verified Feb 2026 | VERIFIED |
| Pricing (Max) | $199.99/month -- 20,000 credits + unlimited 01 & 02 in Relax Mode | User-verified Feb 2026 | VERIFIED |
| Stylized quality | 5/5 -- excels at anime, illustration, ink wash, game CG. Hailuo 01 "Live" variant specifically designed for animating artwork/cartoons. | 1C, new research | CLAIMED |
| Character consistency | Subject reference, 3/5 -- limited | 1C | CLAIMED |
| Max video length | 6-10s | 1C | CLAIMED |
| Audio | Yes -- voiceovers, lip-sync, smart music library, 4/5 | 1C | CLAIMED |
| Relax Mode queue | 5 sequential tasks, 2 parallel renders. ~30s wait per task. | New research | CLAIMED |

**NOTE:** The 1C research cited $94.99 as "Unlimited" -- this was a **legacy plan discontinued June 2025**. Current unlimited requires Ultra ($124.99, Hailuo 01 only) or Max ($199.99, both models). Current sale pricing available: Master $63.99, Pro $24.99.

**Hailuo verdict:** Best option for burst production (Max plan, one month, cancel). Hailuo 01 Live is strong for stylized/cartoon content. But ongoing monthly at $199.99 exceeds budget. The Master tier ($94.99, 10,000 credits) is a non-unlimited alternative for steady production.

**Market note (Jan-Feb 2026):** MiniMax (Hailuo's parent company) filed for IPO in January 2026, signaling growing resources. Hailuo is an active competitor worth re-evaluating quarterly as the product evolves.

#### Luma Ray3

| Dimension | Data | Source | Confidence |
|-----------|------|--------|------------|
| Pricing (Unlimited) | $75.99/month | 1C | CLAIMED |
| Stylized quality | 3/5 | 1C | CLAIMED |
| Glow fidelity | **Best in industry** -- native 16-bit HDR output | 7A | CLAIMED |
| Character consistency | 3/5 -- basic references | 1C | CLAIMED |
| Max video length | 10s single, ~30s via extension | 1C | CLAIMED |

**Luma verdict:** The glow/SSS specialist. Native HDR makes it best for bioluminescent effects. But 3/5 for general stylized quality and character consistency limits it to a supplementary role.

### Pricing Cross-Check: 1A vs 1C

| Tier | 1A Price | 1C Price | Match? |
|------|----------|----------|--------|
| Standard | $6.99-10 | $6.99 | Partial (1A wider range) |
| Pro | $25.99-37 | $37 | Partial (1C uses upper bound only) |
| Premier | $64.99-92 | $92 | Partial (1C uses upper bound only) |
| Trustpilot | 1.3/5 (189 reviews) | 2.3/5 (222 reviews) | **CONTRADICTION** |

The Trustpilot discrepancy (1.3 vs 2.3, 189 vs 222 reviews) suggests the data was gathered at different times or from different Kling product pages (the company has multiple products).

### Recommended Tool Stacks

#### Stack A: Minimum Viable ($58/month)
- **MidJourney Standard** ($30/month) -- Image generation engine. Unlimited Relax mode for character-consistent stills. --oref for character, --sref for brand style. 15 hrs fast GPU + unlimited relax is sufficient for image work.
- **Pika Pro** ($28/month) -- High-quality stylized clips under 25s. 74-89% success rate means ~19 usable videos from 2,300 credits.
- **Kling Free tier** (~2 videos/day, 66 credits) -- For 60s content and iteration.
- Total: **$58/month**
- Strength: Best stylized quality (MJ images + Pika animation), fits budget target.
- Limitation: No native 60s capability without Kling paid tier.

#### Stack B: Recommended Balance ($67/month)
- **MidJourney Standard** ($30/month) -- Image engine + short video (5-21s via Animate)
- **Kling Pro** ($37/month) -- Video generation for clips requiring motion. ~20 usable stylized videos/month. Only tool with native 60s.
- Total: **$67/month**
- Strength: Native 60s capability, strong character consistency (Kling Elements).
- Limitation: Kling stylized quality is weaker (2.5/5 Pixar-style) -- may need multiple takes.

#### Stack C: Full Production ($95/month)
- **MidJourney Standard** ($30/month) -- Image engine
- **Pika Pro** ($28/month) -- Primary video for stylized clips under 25s (best quality)
- **Kling Pro** ($37/month) -- For 60s content specifically
- Total: **$95/month**
- Strength: Best of both worlds -- Pika for quality, Kling for length.

#### Stack D: Burst Production (one-month intensive)
- **MidJourney Standard** ($30/month) -- Image engine
- **Hailuo Max** ($199.99/month) -- True unlimited Relax Mode for both Hailuo 01 & 02. 20,000 priority credits. Cancel after one month.
- Total: **$230 one-time** (amortized: ~$77/month over 3 months of content)
- Realistic throughput: 760-2,280 usable clips in one dedicated month.
- Strength: Produces 3 months of content library in one billing cycle. Hailuo 01 Live is strong for stylized/cartoon content.
- Limitation: Requires dedicated production time (8+ hours/day for 20 days). Weaker character consistency (3/5). Max 10s per generation = heavy stitching.
- **No contract** -- monthly billing, cancel anytime.

#### Stack E: Time-Limited Opportunity (expires Feb 25, 2026)
- **MidJourney Standard** ($30/month) -- Image engine
- **Envato VideoGen** ($16.50/month) -- Promotional unlimited AI video. Now uses multiple models (Seedance 1.0, Hailuo 02, Google Veo 3 — not just Luma Ray3). Includes commercial license. Speech videos capped at 30/month.
- Total: **$46.50/month**
- Strength: Cheapest unlimited option available. Worth grabbing immediately for testing.
- Limitation: Promotional pricing ends Feb 25. Stylized quality was rated 3/5 when using Ray3 only — may have improved with Veo 3 and other models now available. Unknown throttling behavior.
- **⚠️ TIME-SENSITIVE:** This promotional pricing expires **February 25, 2026**. Grab immediately for testing even if not primary tool.

### Tool Decision: What 9A Needs to Answer

Before finalizing, the budget optimization research (9A) should investigate:
1. Real-world Pika Pro ($28) capacity -- is 2,300 credits enough for 15-20 finished videos?
2. MidJourney Animate quality for stylized clay -- does it preserve the aesthetic?
3. Kling Free tier reliability -- can 2 videos/day consistently supplement a paid primary tool?
4. Whether any open-source video tools run on 8GB VRAM locally or 15GB via Colab (LTX-2 once available?)
5. **Hailuo actual pricing** -- is the "Unlimited" tier $94.99 or $199.99? What are the real tier names and limits?
6. MidJourney Standard ($30) vs Pro ($60) -- confirm that Standard's unlimited Relax mode is sufficient for the image volume needed (character sheets, scene generation, style testing)

---

## DECISION GATE 2: Video Length Strategy

### Data Summary

| Platform | Optimal Length | Source | Sample Size | Confidence |
|----------|---------------|--------|-------------|------------|
| **TikTok (reach)** | 60s-10min | Buffer Mar 2025 | 1.1M videos | VERIFIED |
| **TikTok (engagement)** | ~2 minutes | Socialinsider Jan24-Jun25 | 2M videos | VERIFIED |
| **TikTok (completion)** | Under 10s (81.2%) | TTS Vibes 2026 | Unknown | VERIFIED |
| **TikTok (edu content)** | 60s+ (43.2% more reach) | Napolify 2025 | Unknown | VERIFIED |
| **IG Reels** | 60-90s | Socialinsider | 31M posts | VERIFIED |
| **YouTube Shorts** | 35-60s | 2B extraction | Multiple sources | CLAIMED |
| **Facebook** | 60-90s | 2B extraction | Multiple sources | CLAIMED |

### The Reach vs Completion Paradox (Resolved)

The data shows two competing signals:
- **Reach maximization:** 60s+ content (Buffer: 432.5 median reach vs 221 for 10-30s)
- **Completion maximization:** Under 10s content (TTS Vibes: 81.2% completion vs 31% for 60s-3min)

**Resolution:** TikTok's algorithm uses BOTH absolute watch time AND completion rate. A 45-second video watched for 30 seconds accumulates more total watch time than a 15-second video fully completed. The algorithm appears to use different distribution pathways: completion-based boosting for short content, watch-time-based boosting for long content. Educational content specifically benefits from the watch-time pathway (Napolify: 43.2% more reach at 60s+).

### Recommended Length Strategy

| Content Tier | Length | Purpose | Volume |
|-------------|--------|---------|--------|
| **Hook clips** | 7-15s | Algorithm testing, loop-optimized, A/B testing hooks | 30% of output |
| **Core educational** | 30-60s | Primary parenting tips, highest production value. 30-45s for TikTok/Reels, up to 60s for YouTube (2A line 174) | 40% of output |
| **Deep dives** | 60-90s | Montessori demonstrations, monetization-eligible (TikTok 60s+, YT 60s+) | 20% of output |
| **Long-form** | 90s-3min | Series/episodic, repurpose to YouTube Shorts as 60s clips | 10% of output |

### Cross-Platform Compatibility

| Format | TikTok | IG Reels | YT Shorts | Facebook |
|--------|--------|----------|-----------|----------|
| 7-15s hooks | Good completion | Works | Works | Weak (FB prefers longer) |
| 30-45s core | Good balance | Good | Good | Good |
| 60-90s deep | Best reach (edu) | Optimal (Socialinsider) | Optimal | Optimal |
| 90s+ long | Monetizable | Works | Needs 60s+ for monetization | Works |

**Key insight from 2B:** A single 60-second video works well across ALL four platforms. This is the universal sweet spot for cross-posting. The 30-45s tier is a TikTok-specific optimization; the 7-15s tier is for testing.

**Platform maximum durations (Feb 2026):** YouTube Shorts up to 3 minutes (Oct 2024 expansion). Instagram Reels up to 20 minutes recording. TikTok up to 60 minutes (uploaded). These maximums do not change the recommended strategy — sub-90s content still receives highest algorithmic priority across all platforms.

### Platform Discovery Features (2025-2026)

Three major platform updates have elevated SEO importance for short-form content:

- **Instagram posts now indexable by Google and Bing** (July 2025): Each Reel functions as a micro-landing page for web search. Keywords in captions, alt text, and burned-in captions are crawlable.
- **YouTube Shorts appear in Google Discover** (September 2025): Shorts surface in Google Discover feeds, dramatically expanding potential reach beyond YouTube itself. YouTube SEO (titles, descriptions, tags) now drives external discovery.
- **Facebook October 2025 algorithm update**: 50% more same-day content shown in feeds. Recency advantage means posting timing matters more than ever for Facebook Reels.

These changes reinforce the SEO-first strategy: keywords in narration → captions → titles matter more than hashtags for discovery.

### Hook Window

All sources agree: **3 seconds** to hook the viewer. 33% scroll away within 3 seconds (Sotrender 2025). For parenting content, the two proven hook patterns are:
1. State the problem immediately: "When your toddler won't stop hitting..."
2. Show the end result first: "This one phrase stopped tantrums in our house"

Post-hook, a December 2024 algorithm update extended the quality evaluation window to 15-20 seconds. Content must deliver value within this window, not just hook.

**Algorithmic boost:** Videos with **75% completion rate** trigger TikTok algorithmic boost (2A line 71). For 30-60s content, this means viewers must stay for 22-45 seconds.

**Instagram-specific:** Viewers decide within **1.7 seconds** whether to continue watching (Dataslayer.ai citing Instagram research, 2B line 36). This is shorter than the general 3-second consensus across platforms. Videos featuring **faces in the first 3 seconds achieve 35% higher retention** (Zebracat 2025, 2B line 36) — relevant for the parent character in Baby Brains content.

### Retention Ladder (Beyond the Hook)

The hook gets viewers IN. The retention ladder keeps them watching (OLD-1 PSY-005, adapted for multi-length strategy):

| Timing | Element | Purpose |
|--------|---------|---------|
| 0-3s | Hook | Capture attention (see 7 hook patterns in WORKFLOW.md) |
| 3-8s | Payoff #1 | Deliver first value — reward the viewer for staying |
| 8-15s | Payoff #2 | Deepen engagement — introduce the core content |
| Midpoint | Pattern interrupt | Combat attention dip — visual change, new question, or mini-mystery |
| Final 5s | Emotional moment + CTA | Create connection and prompt action |

**Mid-point re-hook for 60s content** (OLD-4 CP-005): Insert a secondary hook or mini-mystery at the 25-30s mark. Examples: "But here's what nobody tells you...", a visual pattern interrupt, or a new question. Without mid-point re-hooks, 60s completion rates suffer (31% average for 60s-3min content).

**Pattern interrupt catalogue** (OLD-5 CP-002/004/005): Pattern interrupts boost watch time by up to 85% and conversion by 32%. Ranked techniques for Montessori content (calibrated for calm tone — avoid frantic energy):

1. **Camera angle switch** (wide → close-up → medium) — highest impact, natural in stitched content
2. **Text overlay pop-up** — keyword emphasis, data points, quotes
3. **B-roll insertion** — show the material/toy/environment detail
4. **Audio shift** — music swell, SFX emphasis, pause-then-speak
5. **On-screen question** — "But does this actually work?"

**Implementation rules:** Place first interrupt within 3-4 seconds. Create contrast with what came before. Every interrupt must serve the core message. For P2/P3 educational content, prefer subtle interrupts (camera angle, B-roll) over flashy ones (text pop-ups, effects).

### Hashtag Limits (Major 2025 Platform Shift)

| Platform | Max Hashtags | Optimal Number | Current Importance |
|----------|-------------|----------------|-------------------|
| TikTok | **5** (since Aug 2025) | 3-5 | Moderate — keywords matter more |
| Instagram | **5** (since Dec 2025) | 3-5 | Low — keywords critical |
| YouTube Shorts | 15 | 3-5 (always include #Shorts) | Moderate |
| Facebook | No strict limit | 1-3 | Low — more = spam signals |

Both TikTok and Instagram enforced 5-hashtag limits in 2025, a major shift from prior 30+ strategies (4B lines 216-222). **SEO keywords now drive discovery more than hashtags** on both platforms.

**Cross-posting penalties:**
- Instagram imposes a **duplicate content penalty** (24hrs to 30 days suppression) and penalizes **TikTok watermarks** on cross-posted content (4B lines 36-39)
- Facebook Reels are now **default for ALL videos** (June 2025, Meta announcement) — no distinction between video posts and Reels (2B line 107)

**Sound-off viewing stat correction:** The widely cited "85% watch with sound off" is from a **2016 Digiday article** — outdated. More recent estimates: 69-74% (Verizon Media 2019, St4.ca survey). Captioned videos still receive +40% watch time regardless (2B lines 110-118).

### YouTube Shorts Monetization Thresholds

YouTube Partner Program requirements for Shorts monetization (2B lines 55-58):
- **Full ad revenue access:** 1,000 subscribers + either 4,000 watch hours (12 months) OR **10 million valid public Shorts views in 90 days**
- **Early access (fan funding only):** 500 subscribers + 3,000 watch hours OR **3 million Shorts views in 90 days**

There is no minimum video length for Shorts monetization once a channel qualifies.

**⚠️ Content ID restriction:** YouTube Shorts **over 1 minute using copyrighted/Content ID claimed music are blocked globally** — not just demonetized but blocked from publication. This is separate from the existing >60s VO-only monetization rule. Use only royalty-free or original audio for all Shorts content.

---

## DECISION GATE 3: Audio & Voice Strategy

### The Business Account Problem

From 3A: TikTok Business accounts **are restricted exclusively to the Commercial Music Library (CML)** — over 1 million pre-cleared tracks, but excluding all mainstream hits, viral trending sounds, and most recognizable music (3A line 59). This is a hard platform restriction. Options:
1. Use a **Creator account** (access to trending sounds, but weaker analytics)
2. Use a **Business account** with original audio only
3. Hybrid: Creator for TikTok, Business for other platforms

**⚠️ CML Cross-Platform Licensing:** CML tracks are licensed for TikTok use ONLY. Using CML music on Instagram, YouTube, or Facebook requires separate licensing — the TikTok CML license does NOT extend to other platforms (3A line 77). This is a hard constraint for any multi-platform strategy using CML audio.

**January 2026 CML tightening:** TikTok updated CML terms of service in January 2026 with stricter no cross-platform clauses and off-platform tracking restrictions. The existing warning about CML being TikTok-only is now formally enforced.

### Burned-In Captions (Production Requirement)

An estimated 69-74% of mobile viewers watch with sound off (4B line 237 cites 92%, but this is likely from the same category of outdated marketing statistics corrected above). Captioned videos receive **+40% higher watch time** (4B). Instagram does not support SRT sidecar files. **TikTok now supports SRT upload** via Ads Manager and the Video Editor (as of 2025), though burned-in remains the safer option for consistency. Burned-in captions remain the primary recommendation for cross-platform visual consistency. YouTube Shorts uniquely benefits from a hybrid approach: burned-in for visual consistency + SRT for SEO indexing and auto-translation.

### YouTube Shorts: Copyrighted Music Blocks Monetization

YouTube Shorts **over 60 seconds using copyrighted music are blocked from monetization** (2B line 59). Only royalty-free or original audio is permitted for 1-3 minute Shorts. This reinforces the original/self-recorded audio strategy.

### Music Licensing Risk

**Sony lawsuit precedent (Aug 2025):** Up to **$150K per track for willful infringement** (3A line 68). This applies to using non-CML trending sounds on Business accounts or any copyrighted music without proper licensing. The risk is real — rights holders are actively pursuing AI content creators.

### Voice Generation Alternatives

**Fish Audio API:** ~$11/mo Plus tier ($5.50/mo annual), or $15/1M chars — **~70% cheaper than ElevenLabs** and ranked **#1 on TTS-Arena** with WER 0.008, CER 0.004 (best in class) (3B lines 144-146). API-only service; the local model requires 12GB+ VRAM (exceeds 8GB local, but could run on Colab T4 15GB). Primary cloud TTS fallback.

### Uppbeat: Music AND SFX Source

Uppbeat is misclassified as SFX-only in the existing synthesis (line ~844). It should also appear here as a music licensing option at **$5.59-13.99/month** (3A line 73). Competitive alternative to Epidemic Sound for background music.

### AI Voice Suppression

From 3A (post-November 2025 TikTok update):
- AI voiceover: **38% lower FYP exposure** [CLAIMED -- single source]
- Human narration: **+21% completion rate** [CLAIMED]
- Trending audio: **98.31% more views** (Hootsuite) [VERIFIED]
- Original audio: **3x weight** vs trending sounds (January 2025 update) [CLAIMED from 2A]

These data points conflict: original audio gets 3x weight, but trending audio gets 98% more views. The resolution is likely that "original audio" means human-created original content (voiceover, original music), not silence. The 3x boost rewards authenticity, not trending sound avoidance.

**TikTok sound behaviour:**
- **88% of TikTok users say sound is "essential"** to their experience (3A line 21) — the sound-off stat (92%, 4B) applies to all U.S. mobile video viewers, not TikTok specifically
- TikTok automatically shares all original audio as reusable sounds (3A lines 8-9)
- Low-volume trending sound layering technique: 10-20% volume under 100-200% VO (3A line 11) — lets you benefit from trending sound algorithm boost without losing voiceover clarity
- **Trending sounds boost educational engagement ~47%** (3A line 25)
- **Warm female narration** dominates successful parenting accounts (3A lines 47-52)

### Hardware: 8GB VRAM local + 15GB free via Colab

The actual hardware has 8GB VRAM and 32GB system RAM. The 3B extraction flagged a mismatch with CLAUDE.md (which listed 4GB) -- the user confirms 8GB is correct.

**Cloud GPU (free):** Google Colab VS Code extension provides a free NVIDIA T4 (15GB usable VRAM) directly in VS Code. 12hr max sessions, 90min idle timeout, 15-30 GPU hrs/week. This enables models that don't fit locally (Maya1 3B needs 16GB+) and parallel workflows (TTS on Colab while video gen runs locally). See: [KB source S23](../../knowledge-base/sources/S23_colab_vscode_free_gpu.md)

**What runs on 8GB VRAM (local):**
- **Chatterbox Turbo** (350M params): 8GB borderline but viable. MIT license. Voice cloning from 5-10s reference audio. 63.75% preferred over ElevenLabs in blind evaluations [CLAIMED]. Emotion exaggeration control. **$0/month.** TTS Arena #16. Note: embeds **PerTh neural watermark** (imperceptible, survives compression) (3B line 112).
- **F5-TTS** (335M params): 8GB "comfortable fit". Excellent clone quality. **But CC-BY-NC license (non-commercial blocker).** OpenF5-TTS-Base (Apache 2.0) is an alternative but "still alpha."
- **CosyVoice**: 8GB "at the limit" -- borderline. Apache 2.0 license. 77-78% speaker similarity. May be unstable.
- **Sesame CSM-1B**: 4.5GB VRAM on CUDA. CC license (requires Llama 3.2-1B access). Best for conversational speech with natural pauses, "umms," and turn-taking. Voice cloning via 2-3 minute reference (3B lines 71-77).
- **Qwen3-TTS** (0.6B params, already installed in ATLAS): Voice cloning via reference audio + transcript. ~4-6GB VRAM. Jeremy Irons voice already configured. Can clone any voice from short sample. **$0/month.**
- **Maya1** (3B params, Apache 2.0): Voice *design* via natural language description (not cloning). 20+ inline emotion tags. #2 on Artificial Analysis TTS ranking. **Needs 16GB+ VRAM — won't run locally on 8GB.** Potential cloud/API option. See: [huggingface.co/maya-research/maya1](https://huggingface.co/maya-research/maya1)

### Recommended Audio Stack

| Use Case | Tool | Cost | Notes |
|----------|------|------|-------|
| **Premium brand voice** | Self-recorded Australian VO | $0 | Record narration directly. Highest authenticity, best algorithm treatment. |
| **Bulk daily VO** | Qwen3-TTS (local, already installed) | $0/month | Voice cloning from reference audio. 0.6B params, ~4-6GB VRAM. Already in ATLAS with Jeremy Irons voice. Clone an Australian voice from short sample. |
| **Cloud fallback (primary)** | Fish Audio API | ~$11/mo Plus ($5.50 annual) | 70% cheaper than ElevenLabs, ranked #1 TTS-Arena (3B lines 144-146). API-based, no local VRAM needed. |
| **Cloud fallback (alt)** | ElevenLabs Starter | $5/month | 30,000 credits ≈ 30 min/month (credit-based system). Note: **Professional Voice Cloning** requires Creator plan at $22/month (3B line 44). |
| **Background music** | Royalty-free library | $0-19/month | Epidemic Sound ($9-19/month depending on tier, 3A line 72), Artlist ($10), or free options (Pixabay, Free Music Archive) |
| **Investigate** | Maya1 (via free Colab T4) | $0 | Voice design via natural language. 20+ emotions. 3B params, needs 16GB+ — test on Colab T4 (15GB usable, borderline). Apache 2.0. See A68. |

**Decision:** Primary voice is self-recorded Australian voiceover for core content. Qwen3-TTS ($0 local, already installed) for bulk production with cloned voice. Fish Audio API (~$11/mo Plus tier) as cloud fallback. This keeps voice costs at **$0-11/month**.

---

## DECISION GATE 4: AI Disclosure & Platform Policy

### Policy Summary Across All Platforms

| Platform | Stylized AI Labeling | Realistic AI Labeling | C2PA Detection | Algorithm Penalty |
|----------|---------------------|----------------------|----------------|-------------------|
| **TikTok** | Optional (exempt) | Mandatory | ~35-45% auto | Not proven for stylized |
| **Instagram** | "AI Info" auto-label if detected | "AI Info" label | Yes (from some tools) | 23-47% lower reach (single source, 2B) |
| **YouTube** | Disclosure recommended | Mandatory for realistic | Not specified | "Meaningful human contribution" required for monetization |
| **Facebook** | No specific policy | Follows Meta rules | Yes (from some tools) | Not proven |

### Key Finding: MidJourney Does NOT Embed C2PA

From 5A: MidJourney does not embed C2PA metadata in generated images. This means:
- Instagram/Meta auto-labeling will NOT trigger from MJ-generated content
- No automatic "AI Info" label applied
- This is significant because 2B reports AI-labeled content gets 23-47% lower reach on Instagram

### TikTok Creator Rewards: AI Content Excluded?

From 5A and 2A, the picture is nuanced:
- TikTok does not *explicitly* ban AI content from Creator Rewards
- But it requires "original, high-quality content" with "significant human creative input"
- Pure AI-generated content without editing/direction: "likely won't qualify"
- AI-assisted content meeting originality standards: "can be monetized" [CLAIMED]
- External sponsorships remain viable regardless

### YouTube "Template-Based Production" Prohibition

YouTube prohibits "template-based production" (renamed "inauthentic content" July 2025) (5A line 162). Each video must differ substantively from others and demonstrate educational or entertainment value. This conflicts with our pipeline approach (scripted templates, batch production) and requires mitigation:
- **Each video must have unique voiceover narration**, not just text overlay variations
- **Visual content must vary** between videos (different scenes, activities, settings) — not just hook swaps
- **The 7-hook-variation strategy** is safe as long as the underlying visual content and voiceover differ; the hook is only 3 seconds of a 30-60s video
- **Monitor YouTube's enforcement** — this policy targets mass-produced "wallpaper" channels, not educational content with genuine variety

### Recommended Disclosure Strategy

1. **Do NOT proactively label content as AI-generated** on any platform. Stylized content is exempt from mandatory disclosure on all four platforms.
2. **Include privacy-first framing in bio/about sections:** "We use AI illustration to protect children's privacy -- no real children are shown in our content."
3. **If asked directly**, be transparent about AI use. Frame it as a deliberate choice for child safety, not cost-cutting.
4. **Use MidJourney as the image engine** (no C2PA embedding) to avoid auto-labeling on Instagram.
5. **Monitor platform policy changes quarterly.** The AI content policy landscape is shifting rapidly.

### Audience Perception of AI Content

- **Parasocial connection loss:** USC Marshall study (May 2025) found AI disclosure reduces parasocial connection with creators (5A lines 70-74). The privacy-first framing mitigates this by positioning AI as an ethical choice rather than a cost-saving measure.
- **Transparency demand:** 94% of audiences want transparency about AI use; 87.2% want to understand WHY AI was used (5A line 88). The "protecting children's privacy" rationale satisfies this demand.

### Production Time Reality

Existing synthesis references 15-25 hrs/month for production. This figure is for **simple faceless content only** (4A lines 126-127). **Character-consistent content** (what Baby Brains requires) takes **45-75 hrs/month** — 3x the simple faceless estimate. Factor this into workflow planning.

### Character Consistency: LoRA Training

For stronger character consistency beyond MJ --oref, LoRA fine-tuning is available:
- **15-30 reference images** needed for training (4A line 82)
- **~$2 per training run** on fal.ai
- Creates a model checkpoint that reproduces the character more reliably than prompt-based reference
- Trade-off: additional setup time vs better consistency for high-volume production

### Batch Automation: Creatomate

**Creatomate** ($54-99/month) offers CSV-to-video batch automation with built-in ElevenLabs TTS, yielding ~$1.80-2.70 per video including voice (4A lines 134-172). Consider if manual DaVinci workflow proves too slow for production volume. Higher monthly cost but potentially faster throughput.

**CapCut limitation:** CapCut has no API — cannot batch generate or automate (4A line 159). Manual-only for assembly. DaVinci scripting is the only automation path.

### COPPA Compliance

**Disney paid a $10M COPPA settlement in 2025** for child-directed content labeling failures. Penalties up to **$50,120 per violation** under COPPA (16 CFR 312, 2024 inflation-adjusted; 2025 adjustment may be higher). Separate FTC Act Section 5 penalties reach $53,088 per violation (6A line 101). Baby Brains content is for ADULTS (parents) — set `madeForKids: false` on YouTube. However, thumbnails showing animated children could trigger COPPA auto-classification. Monitor this and appeal if misclassified.

**⚠️ TIME-SENSITIVE: COPPA Full Compliance Deadline — April 22, 2026.** The January 2025 COPPA amendments expand biometric data protections and require separate consent for data sharing with third parties. Full compliance with all amended provisions required by April 22, 2026. Three interlocking compliance checklists apply to Baby Brains content:

1. **Child Safety Checklist**: Adult supervision visible in all activity demos, avoid private spaces (bathrooms/bedrooms), age-appropriate activities only, no PII visible, privacy settings enabled on all accounts, monitor comments for child safety concerns (OLD-5 QI-002)
2. **COPPA Compliance Checklist**: Content ABOUT children (for adult parents) vs content FOR children — explicit audience designation required. Set `madeForKids: false` on YouTube. Understand that thumbnails showing animated children could trigger COPPA auto-classification (OLD-5 QI-004)
3. **FTC Disclosure Checklist**: Platform-specific labeling tools (Instagram Branded Content Tool, TikTok Content Disclosure, YouTube checkbox). $53,088 per violation for FTC non-compliance (OLD-5 QI-005)

**Sharenting context:** 2/3 of identity fraud by 2030 is projected to come from sharenting (5A line 86). Australian TikTok ban for under-16s (5A line 117). Both reinforce the privacy-first positioning.

---

## DECISION GATE 5: Competitive Positioning & Differentiation

### The White Space

From 6A:
- **ZERO** Montessori+AI accounts exist worldwide on any platform
- **ZERO** Australian AI parenting content creators identified
- BabyBus (43M YouTube subs) is the only large animated "Montessori-inspired" channel, but it's traditional 2D animation, not AI
- No animated parenting accounts use the stylized 3D/clay aesthetic

### Audience Clarification

Baby Brains content is for **PARENTS (adults)**, not for children to watch. The Montessori community's philosophical opposition to screens for under-6 does not apply here -- this is adult educational content about child development, not children's media. This distinction eliminates the perceived "positioning minefield" from the 6A research.

That said, some Montessori purists may still object to AI-generated content on principle. This is a minor concern, not a strategic blocker.

### Australian Market Data

The Australian market directly supports the multi-platform strategy (OLD-5 AS-001):
- **78% social media penetration** across the Australian population
- **1 hour 51 minutes** average daily social media use
- **6.5 platforms** per person on average
- **TikTok**: 38+ hours/month per user (highest engagement platform)
- **Facebook Reels**: 5.91% engagement rate — leads all platforms for Reels content (OLD-5 AS-009)

These statistics justify investing in all four platforms simultaneously rather than focusing on one.

### Australian Content Themes

**Seasonal AU content calendar** (OLD-5 AS-007/008):
- **January-February**: Back to school, summer outdoor activities, water play, sun safety
- **March-May**: Autumn activities, indoor play transitions, Easter
- **June-August**: Winter indoor activities, rainy day play, school holiday content
- **September-October**: Spring, gardening with toddlers, outdoor exploration
- **November-December**: Holiday season, summer prep, end-of-year activities

**Trending AU parenting themes** (OLD-5 CS-025, Q4 2025 — refresh quarterly):
- Lighthouse parenting (letting children navigate challenges)
- Gentle parenting techniques
- Budget-friendly activities (cost of living focus)
- Tech boundaries and screen-free play
- Sustainability and eco-friendly parenting

Prioritize themes that align with Montessori philosophy: budget-friendly activities, sustainability, screen-free play, following the child's lead.

### Content Gap: Ages 0-3 Montessori

Most Montessori social content skews toward **3-6 years**. The infant-toddler segment (0-3) is underserved (6A lines 199-200). Baby Brains' focus on this age range is a genuine competitive advantage — there is both audience demand and a content gap.

### Positioning Recommendation

**Target the "Montessori-curious parent."**

The audience is parents who:
- Want evidence-based, respectful parenting guidance
- Are already on TikTok/Instagram (self-selected screen users)
- Value privacy and won't show their children's faces online
- Are interested in Montessori principles but don't require AMI certification

**Differentiation pillars:**
1. **Privacy-first:** "AI illustration protects children's privacy" -- turns the AI tool into an ethical choice
2. **Visual distinctiveness:** Bioluminescent solarpunk clay aesthetic is genuinely unique; no competitor uses it
3. **Evidence-based:** Content backed by developmental science, not influencer opinions
4. **Australian voice:** Underserved market with no AI parenting creators

**Avoid:**
- Claiming "official Montessori" status
- Comparing to or criticizing existing parenting influencers

---

## DECISION GATE 6: Visual Direction & Prompt Engineering

### MidJourney V7 State (from 8A)

**Critical changes from V6:**
- **--cref is DEPRECATED.** Replaced by --oref (Omni Reference) since April 2025.
- **--oref** handles characters, objects, vehicles, creatures. Accepts external/real photos equally well.
- **--oref costs 2x GPU time** vs standard generation.
- **Only ONE reference image** allowed per --oref (V6 --cref allowed multiple).
- **--ow (Omni Weight):** Range 0-1000. Recommended 100-250 for character work. Official warning: don't exceed 400 without high --s and --exp values.
- **--exp parameter:** V7 tone mapping control (0-100). Keep under 25 for prompt consistency — higher values enhance luminosity but can cause overexposure (7A line 22). **--weird parameter is unavailable in V7** (7A line 22).
- **--sref** now has 6 versions (--sv 1-6). Default is --sv 6. Sref codes only work with --sv 4 or --sv 6.
- **Seeds have limited relevance** in V7 -- use --oref and --sref for consistency instead.
- **V7 --oref incompatibilities:** Not compatible with Fast Mode, Draft Mode, Conversational Mode, --q 4, Vary Region, Pan, Zoom Out, or inpainting/outpainting (which still uses V6.1) (8A lines 164-165).

**Video limitations:**
- **No reference features work with video** (--cref, --oref, --sref all incompatible)
- Video is image-to-video ONLY (cannot text-to-video)
- 5s per generation, 21s max via extensions
- Quality degrades after 9 seconds
- Human motion: ~50-60% success rate
- Video generation is **web-only** — not available via Discord (1B line 114)
- **Text rendering fails in video** — any text in the source image will distort (1B line 115)

**Video motion parameters** (8A lines 91-95):
- `--motion low`: Subtle/calm motion for ambient scenes
- `--motion high`: Dynamic motion with both subject and camera movement
- `--loop`: Makes end frame match start frame (useful for 7-15s hook clips)
- `--end <URL>`: Specifies ending frame image (useful for Screenshot Shuffle stitching)

### Character Consistency Workflow (from 8A)

1. **Create base character** with --oref:
   ```
   stylized infant with simplified sculptural features, smooth ovoid head,
   large expressive eyes, warm clay-amber skin tones with subtle subsurface
   scattering, [description], Brancusi-inspired organic forms, soft volumetric
   light, clean white background, full body, front view --ar 2:3 --v 7
   --no cartoon, Disney, Pixar, anime, photorealistic, harsh shadows, plastic
   ```
   See brand direction: `docs/research/Baby Brains unified visual system...md`

2. **Generate reference sheet:**
   ```
   character reference sheet, [description], multiple views, front view,
   side view, three-quarter view, various expressions, clean white background,
   professional --oref [URL] --ow 100 --v 7
   ```

3. **Apply across scenes:**
   ```
   stylized sculptural character, [ACTION/SCENE], [key traits], warm clay-amber
   tones, subsurface scattering, soft golden ambient lighting
   --oref [original_base_URL] --ow 150
   --sref [style_reference_URL] --sw 300 --seed [consistent_seed] --v 7
   --no cartoon, Disney, Pixar, anime, photorealistic, harsh shadows, plastic
   ```

**Key rule:** Always reference the ORIGINAL base image. Never chain references (A->B->C degrades consistency).

**Multi-character workaround:** Since V7 --oref only allows one reference image, create both characters in a single reference image and describe both in your prompt. Alternatively, create the first character with --oref, send to Editor, switch to V6.1, and use --cref for the second character (8A lines 167-168).

### --sv (Style Version) Behaviour Table (from 8A)

| Version | Behaviour | Best Use Case |
|---------|-----------|---------------|
| --sv 1 | Reliable enhancer, adds warmth, boosts contrast | Client work, consistent results (BB brand warmth) |
| --sv 2 | Creative wild card, unpredictable transformations | Experimentation only |
| --sv 3 | Artistic balancer, thoughtful modifications | Art theory-based enhancement |
| --sv 4 | Professional standard (pre-June 16, 2025 model) | Legacy sref codes |
| --sv 5 | Vintage specialist, warm tones, nostalgic film look | Retro branding |
| --sv 6 | **Default** — safe, balanced, contemporary | General use |

Sref codes only work with --sv 4 or --sv 6. Uploading your own images unlocks all six versions (8A lines 33-44).

### --sw (Style Weight) Permutation Testing (from 8A)

Optimal --sw values for brand aesthetics — test with permutations:
```
[prompt] --sref [URL] --sw {0, 200, 400, 600, 800, 1000} --v 7
```
- **--sw 100** (default): Balanced transfer
- **--sw 200-400**: Recommended starting range for brand consistency
- **--sw 500-700**: Very strong style influence
- **--sw 800-1000**: Closely mimics reference (differences can be subtle)

For color palette swatches as --sref, use **--sw 180** and add "flat color, minimal gradients" to avoid swatch geometry influencing architectural elements (8A lines 46-57).

### Bioluminescent/Ethereal Effects (from 7A)

**Core SSS formula for MJ V7:**
```
subsurface scattering, lit from within, soft clay texture,
wax-like texture --s 200-300 --chaos 15-20 --q 2 --style raw
```

**V6 to V7 migration note:** V7 lost V6's beneficial "waxy quality" in skin rendering. Explicitly add `wax-like texture` or `soft skinned` to recover it.

**Negative prompts (essential):**
```
--no plastic, neon harsh, synthetic glow, artificial lighting, cheap render,
glossy plastic, rubber texture, vinyl, stark shadows, overexposed, clinical,
sterile, lifeless, photorealistic, horror, scary, text, watermark,
fast pan, shaky cam, hyperlapse, strobe, bokeh balls, lens flare
```

**Animation platform selection for glow:**
| Priority | Tool | Reason |
|----------|------|--------|
| Glow fidelity | Luma Ray3 | Native 16-bit HDR output |
| Flicker resistance (#1) | **Veo 3** | Best overall consistency (7A line 120) |
| Temporal stability (#2) | Kling 2.1 Pro | Best flicker resistance for glow among non-Google tools |
| Bioluminescent nature | Runway Gen-3 | Official bioluminescent prompt support |

**Full flicker resistance ranking** (7A lines 118-124): Veo 3 > Kling 2.1 Pro > Kling 2.5 Turbo > Runway Gen 4 > Luma Ray 2 (Ray3 improves).

**Material transition (unconscious -> conscious):**
```
[character] with glowing translucent body gradually transitioning to warm
wooden texture, material gradient, ethereal glow fading into organic grain,
subsurface scattering to solid opacity, soft lighting --v 7 --s 250
```

Generate keyframe images at start/end states, then use AI video interpolation between them.

### Style Reference Code

Community-recommended sref for ethereal glow: `--sref 1007775450` with `--sw 300+` [CLAIMED -- community recommendation, needs testing]

### Color Palette as --sref

Create a 600-1200px wide image with 4-6 horizontal solid-color swatches of the Baby Brains palette (warm clay-amber, bioluminescent blue-green, cosmic darks). Use `--sw 180` and add "flat color, minimal gradients" to the prompt. Rectilinear swatch designs may influence architectural elements -- be aware.

### Clay/Claymation Keyword Behaviour Across Tools

| Tool | "Claymation" Keyword | Recommended Alternative |
|------|---------------------|------------------------|
| **Pika** | Can cause distortions — expect iteration (PB line 60) | "3D clay animation", "soft matte clay surface", "soft stop-motion feel" |
| **Kling** | Works adequately | Standard prompting |
| **MidJourney** | Works well with V7 | "Claymation/stop-motion aesthetic" in Character DNA |

**Pikaframes temporal stability caveat:** Curious Refuge Labs scored Pika 2.2's temporal stability at **1.4/10** in benchmark testing (PB lines 52-54). This is a separate issue from character consistency (3/5) — it refers to surreal morphing tendencies in longer sequences. Mitigation: use two images with similar composition, keep backgrounds simple, and prompt camera motion + subject motion clearly.

### Environment Setting Variants

Beyond the standard Montessori playroom, include these settings for variety (OLD-2 SET-001/002/003):

- **Compact apartment**: Montessori-in-small-spaces messaging. Open-plan living, clever storage, wall-mounted shelves, modest floor space with carefully curated activity area. Accessibility message: you don't need a dedicated playroom.
- **Coastal bright room**: Large windows, natural light flooding in, light timber floors, linen curtains, hints of ocean colour palette. Australian coastal feel without being overtly "beach themed."
- **Outdoor verandah/deck**: Covered outdoor area, timber decking, native plants visible, natural shade. Australian entertaining-area feel for outdoor activity videos.

### Additional Stylized Video Tools

| Tool | Aesthetic | Pricing | Key Capability |
|------|-----------|---------|----------------|
| **Mootion** | Claymation | Varies | 3-minute videos in under 2 minutes (6A line 92) |
| **Higgsfield Popcorn** | Character consistency | TBD | Built specifically for character consistency (4A line 89) |
| **InVideo V3** | "Text-to-Cocomelon" | $28/month | One-prompt animated educational videos (6A line 91) |

---

## CROSS-FILE CONTRADICTIONS

### Resolved

| # | Contradiction | Files | Resolution |
|---|--------------|-------|------------|
| 1 | Kling Trustpilot rating: 1.3/5 (1A) vs 2.3/5 (1C) | 1A, 1C | Different scrape dates and/or different product pages. Treat as 1.3-2.3 range. Either way, customer satisfaction is poor. |
| 2 | Kling stylized quality: 4/5 (1C general) vs 2.5/5 Pixar-style (1A specific) | 1A, 1C | 1A provides style-specific breakdown. For clay/Pixar content specifically, use 1A's 2.5/5 (30-40% success). The 1C 4/5 likely reflects a broader category including anime. |
| 3 | Short videos (7-15s) vs long videos (60s+) for TikTok | 2A | Not a true contradiction. Different metrics: short wins completion rate, long wins reach. Educational content specifically favors long. Use multi-length strategy. |
| 4 | Original audio 3x weight (2A) vs trending audio 98% more views (3A) | 2A, 3A | Different comparison baselines. "Original audio" = human-created voiceover (vs silence or AI voice). "Trending audio" = viral sounds (vs non-trending sounds). Both can coexist: original voiceover + trending sound overlay. |
| 5 | MidJourney C2PA: "does not embed" (5A) vs "auto-labeling on Meta" (2B) | 5A, 2B | Meta auto-labels content it detects as AI-generated, but without C2PA metadata from MJ, detection relies on other signals. MJ content is less likely to be auto-labeled than content from tools that do embed C2PA. |
| 6 | MJ human motion success: 41.7% overall (1B line 76) vs 50-60% (7A line 100) | 1B, 7A | Use 41.7% (empirical 12-test breakdown, excludes portrait animations); 50-60% may include portrait animations in count. |
| 7 | Per-video Kling cost: $1.61-1.76 (1A line 93) vs $0.45-1.20 across tiers (1C lines 36-40) | 1A, 1C | Range depends on tier AND assumed success rate. 1A factors 50% stylized failure rate; 1C uses higher success assumption. Premier $0.45-0.70, Pro $0.80-1.20, base ~$1.61-1.76. |
| 8 | Core content length: 30-60s (2A line 174) vs 30-45s (original synthesis table line 223) | 2A, synthesis | Allow 60s for YouTube, 30-45s for TikTok/Reels. Fixed in DG2 strategy table. |
| 9 | MJ tier pricing: $10 Standard (4A line 197) vs $30 Standard elsewhere | 4A, official | $10 is old "Basic" tier; $30 is current "Standard"; $60 is "Pro" — 4A uses outdated naming. |
| 10 | Per-video time with templates: 15-25 min (PD line 229) vs 20-30 min (PE line 611) | PD, PE | Ranges overlap; PD is DaVinci-only assembly, PE is full pipeline including generation. |
| 11 | Kling IMAGE 3.0: described as product (see Kling IMAGE 3.0 section in DG1) vs "no evidence" (PC lines 120-128) | Synthesis, PC | RESOLVED: User has Reddit screenshots (Feb 2026) confirming prerelease to selected accounts. Footnote added to DG1. |
| 12 | Video Quality MCP: "skip initially" (PE line 11, see DaVinci export section) vs "recommended" (see MJ V7 State section) | PE, synthesis | Internal synthesis contradiction — reconciled to "Phase 2+ addition." Video Quality MCP duplicates ffmpeg + Claude vision. |
| 13 | Sound-off viewing: 85% (PD line 79) vs 69-74% (2B lines 110-118) | PD, 2B | 85% is from a 2016 Digiday article; use 69-74% from 2019+ data. Both agree captioned content performs better. |

**Single-source data points** (no contradicting data available):
- Multi-person motion success rate: 20% (1B line 100) — based on 1/5 test sample; no contradicting data
- Pikaframes temporal stability: 1.4/10 (PB line 52, Curious Refuge Labs benchmark) — note this measures temporal stability, NOT character consistency (3/5, line 79). Different metrics, not contradictory.

### Unresolved

| # | Contradiction | Files | Impact |
|---|--------------|-------|--------|
| 1 | Kling pricing: ranges vary across sources ($25.99-37 for Pro) | 1A, 1C | Medium -- affects budget calculations. Assume upper bound ($37 Pro, $92 Premier) for planning. |
| 2 | AI voiceover 38% lower FYP (3A) -- single source, no verification | 3A | High -- this drives the "human voice required" decision. If wrong, could use cheaper AI voice. |
| 3 | AI-labeled content 23-47% lower reach on Instagram (2B) -- single source | 2B | Medium -- drives the "avoid C2PA/auto-labeling" strategy. |
| 4 | TikTok Creator Rewards: "excludes AI" (5A summary) vs "AI-assisted can be monetized" (2A detail) | 5A, 2A | Low -- monetization is a future concern. Focus on audience building first. |
| 5 | --ow optimal range: 100-250 (MidJourneyV6.org) vs 400-500 (TitanXT) | 8A | Low -- context-dependent. Start at 100-250, test higher for specific needs. |
| ~~6~~ | ~~Hailuo pricing~~ | ~~1C~~ | **RESOLVED:** $94.99 was a legacy "Unlimited" plan discontinued June 2025. Current Max Plan is $199.99/month for true unlimited. Master at $94.99 has 10,000 credits (NOT unlimited). Verified Feb 2026. |

---

## DATA QUALITY ASSESSMENT

### Source URL Problem

**Very few verifiable URLs were provided across the 13 research files.** Most data points are attributed by source name and date only. 4A provides 7 real URLs (DEV Community cost analysis, Artlist Creative Trend Report 2026, Creatomate pricing, MidJourney video docs, Kling Trustpilot, n8n workflow, Geeky Gadgets Kling guide). The remaining 12 files lack direct URLs. The highest-priority verifications needed:

1. **Buffer March 2025 study** (1.1M TikTok videos, reach by length) -- cornerstone of length strategy
2. **Socialinsider study** (31M Instagram posts, 2M TikTok videos) -- cornerstone of cross-platform strategy
3. **TTS Vibes 2026** (completion rate data) -- cornerstone of the completion vs reach analysis
4. **Kling pricing pages** -- confirm current tier pricing ($37 or $25.99 for Pro?)
5. **Pika pricing pages** -- confirm $28/Pro, $76/Fancy
6. **TikTok AI policy** (September 13, 2025) -- confirm stylized content exemption language

### Confidence Distribution

Across all 13 extractions:
- **VERIFIED** (source named + specific data): ~35% of data points
- **CLAIMED** (stated without primary source): ~55% of data points
- **CONTRADICTED** (conflicts with other data): ~10% of data points

The CLAIMED proportion is high. Most "verified" data points are verified by source name only (e.g., "Buffer March 2025") not by URL. True verification requires finding the original source.

### Research Gaps

1. **No data on how NEW accounts perform** at different video lengths (all studies measure existing accounts with followers)
2. **No data on stylized AI content algorithmic performance** (only policy data, not performance data)
3. ~~No Australian-specific audience data~~ **Partially filled**: AU social media stats (78% penetration, 1h51m/day, 6.5 platforms — OLD-5 AS-001), AU posting times by platform/day (OLD-5), AU seasonal content themes (OLD-5 AS-007/008) now integrated. Remaining gap: no AU-specific algorithm performance data (what content types perform best with AU audiences specifically).
4. **Voice tool benchmarks** — Qwen3-TTS is installed and working locally (4-6GB). Remaining: test Maya1 on Colab T4 (A68), compare Qwen3-TTS cloned Australian voice vs Fish Audio API vs self-recorded VO quality.
5. **No real user data for Pika + MJ combined workflow** (the recommended stack)

---

## DECISION GATE 7: Video QC Pipeline (Claude-Assisted)

### Available MCP Tools

| MCP Server | Purpose | Key Capability |
|------------|---------|----------------|
| **Video Quality MCP** (hlpsxc) | Artifact detection + quality metrics | PSNR, SSIM, VMAF scores. Detects blur, blocking, ringing, banding, dark detail loss. |
| **OpenCV MCP** (GongRzhe) | Frame extraction + analysis | Motion detection between frames, edge detection, histogram analysis, feature detection. |
| **AI Vision MCP** (tan-yong-sheng) | Semantic content analysis | Video analysis via local files. Image comparison (2-4 images). Uses Gemini/Vertex. |
| **Video-Audio MCP** (misbahsy) | Assembly + editing | 30+ ffmpeg tools: trimming, concatenation, overlays, subtitles, transitions. |

### Recommended QC Workflow

1. **Generate video** (Kling/Pika/Hailuo)
2. **Extract keyframes:** `ffmpeg -i clip.mp4 -vf "fps=2" frame_%03d.png` (2 frames/sec)
3. **Claude reviews frames** for: character consistency, glow preservation, hand/face artifacts, color drift, composition
4. **Video Quality MCP** runs artifact detection: blur, blocking, banding scores
5. **Compare takes** side-by-side using OpenCV MCP frame comparison
6. **Assembly** via Video-Audio MCP or CapCut for final edit

### QC Checklist (per clip)

- [ ] Character proportions match reference sheet
- [ ] Ovoid/egg head shape maintained (not distorted)
- [ ] Bioluminescent glow consistent throughout (no flicker)
- [ ] Warm clay-amber skin tone preserved (no color shift)
- [ ] Hands: correct finger count, no melting
- [ ] Face: expressions readable, no morphing
- [ ] Background: no scene switching mid-clip
- [ ] Motion: natural movement, no stuttering
- [ ] Transitions: clean start/end frames for stitching
- [ ] No text artifacts or watermarks

### Setup (Immediate)

Install Video Quality MCP and OpenCV MCP into Claude Code's MCP config. This gives us frame-by-frame QC capability without leaving the development environment.

---

## BURST PRODUCTION STRATEGY

### Concept

Subscribe to an unlimited-tier tool for ONE month. Batch-produce 60-90 videos (3 months of content at 5-7/week). Cancel subscription. Amortize cost over 3 months.

### Platform Comparison for Burst

| Platform | Plan | Monthly Cost | Amortized (3 months) | Unlimited? | Ban Risk | Stylized Quality |
|----------|------|-------------|----------------------|------------|----------|-----------------|
| **Hailuo Max** | Max | $199.99 | ~$67/month | Yes (Relax Mode, 01 & 02) | Low | Good (01 Live for cartoons) |
| **Runway** | Unlimited | $95 | ~$32/month | Yes (Explore Mode) | **HIGH** -- bans reported | Good |
| **Luma Pro** | Pro | $99.99 | ~$33/month | Yes (Relaxed Mode) | Unknown | 3/5 stylized |
| **Envato** | Standard (promo) | $16.50 | ~$5.50/month | Yes (until Feb 25) | Unknown | 3/5 (Ray3) |
| **Kling** | Premier | $92 | N/A | **NO** -- credit-based only | N/A | 4/5 |

### Recommended Burst Approach

**Phase 1 (Now -- Feb 25):** Sign up for Envato VideoGen ($16.50) while promotional unlimited is active. Test quality for stylized clay content (now uses multiple models including Veo 3, Seedance 1.0, Hailuo 02 — not just Ray3). Generate as many test clips as possible. Low risk, low cost.

**Phase 2 (After character + style finalized):** Subscribe to Hailuo Max ($199.99) for one intensive production month. Use Hailuo 01 Live for stylized/cartoon animations. Target 60-90 finished videos. Cancel after month.

**Avoid:** Runway Unlimited for burst -- aggressive throttling and account ban reports make it unreliable.

**Kling's role in burst:** Since Kling has no unlimited tier, use it for specific needs only (native 60s clips, precise character control via O1's 7-10 references). Buy Premier ($92) for the burst month if 60s content is needed, but don't rely on it for volume.

### Throughput Estimates (Hailuo Max, one month)

| Scenario | Hours/Day | Days | Total Generations | Usable (30% rate) | Sufficient? |
|----------|-----------|------|-------------------|--------------------|-------------|
| Light | 4 hrs | 15 | ~1,800 | ~540 clips | Yes (3+ months) |
| Medium | 6 hrs | 20 | ~3,600 | ~1,080 clips | Yes (6+ months) |
| Intensive | 8 hrs | 25 | ~6,000 | ~1,800 clips | Yes (12+ months) |

At 2 parallel renders, ~2-5 min per Relax Mode generation, with continuous queuing.

---

## OUTSTANDING QUESTIONS FOR 9A (Budget Optimization)

The 9A prompt should be **reframed** given what we now know. The original 9A prompt focused on sub-$100/month stacks. The real question is now about **production efficiency and workflow**, not just tool selection. 9A should address:

1. **Real production workflows** from creators using MJ (images) + Kling/Pika (video) pipelines. Exact step-by-step. Time per video. Batch techniques. Asset management systems.
2. **MidJourney Standard ($30) capacity** -- confirm unlimited Relax handles 25-35 videos/month of character sheets, scene generation, and style reference testing. Any real-world reports of Standard being insufficient?
3. **MidJourney Animate button quality** for stylized clay -- is it good enough for short clips (5-21s) or does a dedicated video tool always win?
4. **Kling O1 workflow specifics** -- how do creators use the 7-10 reference image tagging (@image1 syntax)? What's the real-world experience with the unified model for character-consistent animation?
5. **Hailuo 01 Live for stylized content** -- real user quality assessments. How does it compare to Pika for clay/3D animation?
6. **Burst production logistics** -- has anyone done a one-month Hailuo Max intensive? What was their daily output? What broke? What tools did they use for asset management?
7. **CapCut batch workflows** -- can you template the assembly process (add VO, captions, background music, transitions) to reduce per-video assembly time?
8. **Open-source video tools on 8GB local / 15GB Colab** -- LTX-2, any others approaching production quality?
9. **Hybrid workflows** -- what % of content can use MJ stills with ken burns/parallax (in CapCut) instead of full AI video?

---

## RECOMMENDED NEXT STEPS

> **Detailed implementation plan in WORKFLOW.md** — see Build Priority section for week-by-week breakdown.

### Critical Constraints (from verification rounds)

Before starting implementation, note these constraints that affect the entire workflow:
- **CML music is TikTok-only** — separate licensing needed for cross-platform use (3A line 77)
- **5-hashtag limit** on both TikTok (Aug 2025) and Instagram (Dec 2025)
- **Burned-in captions recommended** — Instagram does not support SRT sidecar. TikTok now supports SRT via Ads Manager (as of 2025) but burned-in remains the safer cross-platform option.
- **Pika Standard now includes commercial license** ($8/month) — Pro ($28) recommended for credit allocation
- **DaVinci Studio required** for scripting automation (free version lost UIManager in v19.1)
- **DaVinci scripting is Windows Python only** — WSL2 not supported
- **Character-consistent content takes 45-75 hrs/month** (not 15-25, which is simple faceless only)
- **Multi-person motion (parent+baby) has 80% failure rate** in MJ video
- **YouTube Shorts copyrighted music blocks monetization** for videos >60s

### Immediate (This Week)

1. **Sign up for Envato VideoGen** ($16.50/month) -- promotional unlimited AI video (multiple models incl. Veo 3, Seedance 1.0) expires Feb 25, 2026. Low-cost unlimited testing opportunity. Grab it now.
2. **Verify Pika Standard/Pro license terms** -- Standard now includes commercial use; confirm current terms before production use.
3. **Sign up for MidJourney Standard** ($30/month). Unlimited Relax mode for images is sufficient.
4. **Create Baby Brains base character** using the --oref workflow from 8A. Test --sv 1 (warmth) and --sv 6 (default).
5. **Test --sw permutation**: `--sw {0, 200, 400, 600, 800, 1000}` with BB style reference.
6. **Sign up for Pika free tier** (80 credits/month — budget carefully, test only) and **Kling free tier** (66 credits/day).
7. **Record 30 seconds of Australian voiceover** for voice cloning testing.
8. **Test Qwen3-TTS** (already installed) with Australian voice reference sample. Also install VS Code Colab extension and test Maya1 on free T4 (A68).
9. **Purchase/activate DaVinci Resolve Studio** license.
10. **Set up Windows Python environment** for DaVinci scripting (ATLAS runs on WSL2, not supported).
11. **Create TikTok and Instagram accounts** if not already done.

### After Testing (Week 2-3)

12. **Compare results** from MJ Animate vs Pika vs Kling vs Envato/Ray3. Identify the quality winner for stylized clay.
13. **Refine character design** based on what actually renders well across tools.
14. **Establish the production pipeline:** MJ (images) -> [winner tool] (video) -> DaVinci Studio (assembly) -> Qwen3-TTS/self-recorded (voice) -> scheduling.
15. **Test burned-in caption workflow** in DaVinci Studio (Effects → Titles → Animated → Word Highlight).
16. **Test per-platform export presets**: TikTok 3Mbps, Reels 4Mbps, Shorts 12Mbps, Facebook 6Mbps.

### Burst Production Month (When Ready)

17. Character, style, and pipeline all proven with test content.
18. Subscribe to **Hailuo Max** ($199.99) for one month. Use prepaid/virtual card.
19. Batch-produce 60-90 videos across all content tiers (hooks, core, deep dives).
20. Use Kling Pro/Premier ($37-92) alongside for clips requiring native 60s.
21. Cancel Hailuo after the month. Download ALL videos immediately (no bulk download available).

### Launch & Iterate

22. Set up Metricool (free tier, 50 posts/month) for cross-platform scheduling.
23. Decide on Creator vs Business account for TikTok (CML trade-off).
24. Release content from library at 5-7 videos/week, 5 hashtags max per post.
25. Monitor 3-second retention (target 65%+ per OpusClip study). Diagnose by drop-off pattern.
26. **Track with A/B spreadsheet** (12-column structure — see WORKFLOW.md Tracking Spreadsheet).

---

## PHASE 2: PRODUCTION PIPELINE SYNTHESIS

> Cross-referencing PA (Hailuo burst), PB (Pika clay), PC (Kling O1), PD (DaVinci post-production), PF (content-to-script)
> Extracted: 2026-02-02

---

### PIPELINE DECISION 1: Hailuo Burst Viability (PA)

**Verdict: Viable but high-risk. Proceed with prepaid/virtual card.**

| Factor | Finding | Risk |
|--------|---------|------|
| Trustpilot rating | **1.6/5** (79% one-star) | HIGH |
| Wait times on Max | **18+ hours** during peak (user reports) | HIGH |
| Optimal model for clay | **Hailuo 01 Live** (5/5 for artistic style preservation) | Low |
| Hailuo 02 vs 2.3 for stylized | **02 outperforms 2.3** in stylized tests (contradicts marketing) | Medium |
| 20,000 credits = | ~333 standard 768p OR ~83 Pro 1080p videos | - |
| Relax Mode throttling | Unlimited but 5 sequential tasks, 2 parallel renders | Medium |
| Cancellation | NO bulk download. Users report **months of unauthorized charges** | HIGH |
| Runway comparison | @VividFeverDreams generated **13,185 videos on Runway** vs **1,086 on Hailuo** — roughly 12x throughput difference (PA line 15) | Context |
| API automation | MiniMax API (official), fal.ai, Kie.ai (third-party) | Low |

**Critical workflow details:**
- **Prompts under 15 words** to avoid token weight dilution
- Formula: `[Camera Movement] + Subject Action + Environment/Atmosphere`
- Camera in square brackets: `[Push in]`, `[Zoom out]`, `[Pan left]`
- **Subject Reference (S2V-01)** for character consistency across clips
- **Screenshot Shuffle** for multi-scene stitching: capture final frame → use as next clip's start image
- Shorter clips (5s) maintain consistency better than longer ones
- **Expect slight color shifts** requiring post-production matching
- **n8n workflow templates** exist for bulk production (reads prompts from Google Sheets)

**Mitigation strategy:** Use prepaid/virtual credit card. Download every video immediately. Cancel 7 days before renewal. Screenshot all confirmation.

---

### PIPELINE DECISION 2: Pika Clay Workflow (PB)

**Verdict: Primary tool for stylized clips under 25s. Draft at 480p, finalize at 720p-1080p.**

**Image-to-Video handoff (critical insight):**
- Upload MJ image and **prompt motion ONLY** -- do NOT restate visual style
- Guidance scale 7-10 for image inputs
- Image specs: 16:9 or 9:16, min 1024px short side, PNG preferred

**Pikaffects for clay deformation:**
- **Squish It**: Best for clay -- physically compresses subject, reads as soft malleable material
- Inflate It, Deflate It: Natural material expansion/collapse
- Melt It, Poke It: Organic interaction effects
- Cost: 15 credits (I2V) or 18 credits (V2V)
- Can be stacked and combined with standard prompts

**Pikaframes (multi-keyframe, up to 25s):**

| Duration | 480p | 720p | 1080p |
|----------|------|------|-------|
| 5s | 12 | 20 | 40 |
| 10s | 24 | 40 | 80 |
| 15s | 36 | 60 | 120 |
| 25s | 60 | 100 | 200 |

Budget ~150-300 credits per finished 20s 720p sequence including re-rolls.

**Character consistency strategy:**
- No dedicated reference system (3/5), BUT:
- Generate ALL clips from the **same MJ source image** with different action prompts
- Build 12-image reference pack (same outfit, multiple angles, clean backgrounds)
- **Pikascenes**: Upload characters, objects, wardrobe as separate "ingredients"
- Seed control (`-seed ###`) only works when both prompt AND negative prompt unchanged

**Prompt engineering:**
- Style: "Claymation style, soft stop-motion feel, warm cinematic lighting" or "3D clay animation, sculptural organic forms"
- Bioluminescent: "subsurface scattering on gel", "inner glow", "warm translucent amber"
- Camera: `-camera zoom in|out|pan left|right|up|down|rotate cw|ccw` (one at a time only)
- **Essential negative prompts**: `-neg morphing, noisy, bad quality, distorted, blurry, deformed hands, extra fingers, warped face, jitter, flicker`

**Realistic monthly output (2,300 credits Pro):**
- 720p 10s clips: **25-35 polished clips/month**
- 1080p 10s clips: **12-18 polished clips/month**
- Cost-saving: draft at 480p 5s (12 credits) = ~190 quick tests

---

### PIPELINE DECISION 3: Kling O1 Precision Use (PC)

**Verdict: Use for 60s content and precise character control only. Not primary tool for clay.**

**The 60-second reality:**
- True native generation maxes at **10 seconds per clip**
- 60s = 12 sequential 5s extensions, each requiring a new prompt
- ~420 credits for 60s Professional Mode
- **Quality degrades after 30 seconds** of extensions
- Community consensus: **generate 6x 10s clips and stitch externally** for better results

**O1 reference system:**
- `@Image1`/`@Image2` syntax for references (1-indexed), `@Element1`/`@Element2` for saved bundles
- Up to 7 references (no video input) or 4 references (with video editing)
- **Assign roles explicitly**: "Reference @image1 for lighting. Reference @image2 for environment. Ignore subjects."
- Elements require minimum 2 images (front + additional angle)

**Critical prompt engineering:**
- **Pan/tilt inverted**: "pan" = vertical in Kling. Use "tilt left" for horizontal camera movement.
- **Always add endpoints** to prevent 99% freezes: "then settles into position"
- Keep to 3-5 elements per prompt max
- Formula: `[Shot type] + [Camera movement] + [Subject with style] + [Action with endpoint] + [Environment] + [Lighting] + [Style]`

**Credit economics:**
- Standard Mode: 10 credits/5s. Professional: 35 credits/5s (**3.5x savings** using Standard for iteration)
- Free tier: 66 credits/day = ~6 Standard tests daily (useful for prompt refinement)
- Pro ($37): 28-42 final Professional videos/month after iterations
- Premier ($92): 76-114 final Professional videos/month

**API access (for automation):**
- Third-party preferred: PiAPI ($0.195-0.66/5s), fal.ai (~$0.90/10s), Kie.ai ($0.28-0.55/5s)
- **Kling official API:** Available at klingai.com/global/dev but enterprise-focused — minimum ~$4,200 prepayment for 30,000 units (90-day validity) (PC line 151). Third-party APIs are more practical for our scale.
- Python SDK: `kling-ai-sdk` (TechWithTy/kling on GitHub)
- Documented automation chain: GPT/Claude (script) → MJ (images) → Kling API (video) → ffmpeg (stitch)
- **Chain-of-Thought reliability caveat:** O1's CoT improvements are mostly from Kling marketing; independent verification remains limited (PC line 92)

---

### PIPELINE DECISION 4: DaVinci Resolve Assembly (PD)

**Verdict: Primary assembly tool. Hybrid with CapCut for trendy captions. Rendering auto-strips metadata.**

**⚠️ DaVinci Resolve Studio REQUIRED:** The free version lost UIManager support in v19.1, making Studio essential for full scripting/automation workflows (PD line 28). Budget for Studio license before attempting any DaVinci automation.

**Project setup:**
- 1080x1920, 30fps, H.264 MP4, AAC 48kHz
- Track structure: V1 main video, V2 b-roll, V3 graphics/logos, V4 captions, A1 VO, A2 music, A3 SFX
- **Power Bins** persist across ALL projects: brand logos, intros, outros, music, SFX, transitions. **Important:** Power Bins reference files — they don't copy them. Keep source files on permanently attached storage with consistent paths (PD line 249).

**Per-platform export bitrates** (PE lines 189-194, PB line 190):

| Platform | Video Bitrate | Audio | Sample Rate |
|----------|--------------|-------|-------------|
| TikTok | 3,000 kbps VBR (max 4,000) | 128k AAC | 44.1 kHz |
| Instagram Reels | 4,000 kbps VBR (max 4,500) | 128k AAC | 44.1 kHz |
| YouTube Shorts | **12,000 kbps** VBR (max 15,000) | 192k AAC | 48 kHz |
| Facebook | 6,000 kbps VBR (max 8,000) | 128k AAC | 44.1 kHz |

Note: The existing "8-10 Mbps universal" (from PD) is YouTube-appropriate but overkill for TikTok (wastes upload time) and underkill for YouTube Shorts (quality loss).

**Automation via scripting API (Python/Lua):**
- `MediaStorage.AddItemListToMediaPool()` -- auto-import from folders
- `MediaPool.AppendToTimeline()` -- programmatic timeline creation
- `TimelineItem.SetLUT(nodeIndex, lutPath)` -- apply LUT across clips
- `TimelineItem.CopyGrades()` -- copy grades between clips
- Batch render via render queue API
- Key repos: aman7mishra/DaVinci-Resolve-Python-Automation, X-Raym/DaVinci-Resolve-Scripts, pedrolabonia/pydavinci

**Metadata handling (CRITICAL FINDING):**
- **DaVinci rendering automatically strips most metadata** including AI-identifying information
- Kling, Pika, Hailuo do NOT embed C2PA (use visible watermarks, removable with paid plans)
- Additional stripping if needed: `ffmpeg -i input.mp4 -map_metadata -1 -c:v copy -c:a copy output.mp4`
- After export, add copyright: `exiftool -Copyright="© 2026 Baby Brains" -Creator="Baby Brains" video.mp4`

**Caption workflow:**
- DaVinci v18.5+ native transcription: Timeline → Create Subtitles from Audio
- **AutoSubs plugin** (github.com/tmoroney/auto-subs): Free Whisper-based, better for Australian accent
- DaVinci 20: built-in word-by-word highlight animation (Effects → Titles → Animated → Word Highlight, PD line 92)
- Batch: `for file in *.mp3; do whisper "$file" --model medium --output_format srt; done`
- Styling: Montserrat Bold, 60-72pt, white + 2-4px black stroke, upper-middle third, 300-350px from bottom. **TODO**: Brand text watermark design for all videos needs separate creative decision (C7 — open item).
- Per video with automation: **6-11 minutes** vs 16-26 manual

**Color grading for brand consistency:**
- **PowerGrades**: 6-node structure (Tonality → Balance → Saturation → Secondary → Look → Post)
- Push offset toward gold/amber in Balance node
- **Bioluminescent glow in Fusion**: Soft Glow + Glow nodes, Size 0.1-0.15, Threshold 0.4-0.7, Color Scale for tint
- Save as PowerGrade → apply to any clip via middle-click
- LUT export: right-click thumbnail → Generate 3D LUT → 33 Point Cube
- **Color matching tools:** CapCut AI Color Matcher (auto style transfer), DaVinci Shot Match (per-clip), Colourlab AI OFX plugin (auto-balance across timelines) (PB lines 172-176)

**Audio template:**
- VO: -12 to -6 dBFS | Music under VO: -24 to -18 | Music solo: -12 to -6 | SFX: -18 to -12
- **Fairlight auto-ducking**: Sidechain compressor on music track, source = VO track. Parameters: Threshold -30 to -20 dB, Ratio 3:1-6:1, Attack 10-50ms, Release 200-500ms. Use "Music Pumper" preset as starting point (PD lines 144-147).
- Universal LUFS target: **-14 LUFS** (platforms normalize automatically)
- Sound effects: **1.5x higher engagement** (Meta research). Limit 2-3 per clip. Gentle transitions, emphasis chimes.
- Free SFX: Uppbeat, Pixabay, Freesound, ZapSplat

**Per-video workflow: 15-25 minutes** from raw assets to export. 25-35 videos/month = **8-15 hours assembly**.

---

### PIPELINE DECISION 5: Content-to-Script System (PF)

**Verdict: 3-act structure with 7 hook variations per knowledge base entry. Audio-first editing.**

**WAVE Hook Delivery Formula** (PF lines 106-114): For AI-animated content, start with **visual action + text overlay** in the first frame, with voiceover beginning at 0.5 seconds (PF line 115). The hybrid WAVE approach:
- **W — Words on screen** (text overlay): "How to handle toddler biting"
- **A — Audio** (first sentence): "Here's what actually works..."
- **V — Visual** (setting/action): Show parent character or activity in progress
- **E — Emotion** (reaction): Create connection through authenticity

**Pacing target:** 130 WPM for voiceover (PF line 478). This is slower than conversational speech (~150-160 WPM) to accommodate sound-off viewers reading captions.

**5 Script Templates** available (PF lines 447-591): Type.ai TikTok Format (15-60s), Two-Column AV (30-60s), Micro-Tutorial (15-30s), Before/After/Bridge (30-60s), Deep Dive Educational (60-90s). Full templates to be adapted in WORKFLOW.md.

**Script framework:**
- **3-Act**: Hook (0-3s, 15 words) → Meat (3-50s, structured segments) → Payoff/CTA (3-5s, 15 words)
- 12-16 words per line maximum
- Visual change cadence: **3-5 seconds** for P1 content (hooks, snackable clips — viral energy), **6-8 seconds** for P2/P3 content (educational, deep dives — calm Montessori tone)
- Scene counts: 15s = 5-8 scenes, 30s = 8-15, 60s = 15-30

**7 proven hook patterns for parenting content:**
1. **Problem Statement**: "When your toddler won't stop biting..."
2. **Result-First** (HIGHEST PERFORMER): "This one phrase stopped tantrums in our house"
3. **Curiosity Gap**: "The one thing I wish I knew before becoming a parent"
4. **Authority/Expert**: "After 10 years of Montessori teaching, this is what works"
5. **Pattern Interrupt**: Child mid-activity with visual chaos
6. **Relatable "Me Too"**: "POV: you're a mom just trying to survive bedtime"
7. **Contrarian/Myth-Buster**: "Stop playing peekaboo wrong"

**Hook timing by video length:**
- 7-15s loops: 0-1s hook, immediate payoff
- 15-30s: 0-2s hook, 3-7s payoff
- 30-60s: 0-3s hook, 10s payoff
- 60-90s: 0-3s hook, 15-20s delayed payoff

**Knowledge-to-script template (60s master → 30s / 15s derivatives):**

Every scene gets a **priority tier** so shorter versions can be cut deterministically:

| Priority | Meaning | Included in |
|----------|---------|-------------|
| **P1 CORE** | Hook, hero demo moment, CTA | 15s + 30s + 60s |
| **P2 CONTEXT** | Problem illustration, key learning, practical tip | 30s + 60s |
| **P3 DEPTH** | Extra demo steps, detailed explanation, secondary examples | 60s only |

**Cut logic:**
- **60s master**: All scenes (P1 + P2 + P3)
- **30s derivative**: P1 + P2 scenes only (drop P3, re-join transitions)
- **15s hook clip**: P1 scenes only (hook + hero moment + CTA, loop-optimized)

This means you generate video clips for ALL scenes once (during the 60s master production), then **DaVinci assembly creates 3 timelines from the same clip pool** -- no re-generation needed for shorter versions.

```
INPUT: Activity entry (name, age range, principle, key learning)

HOOK (3s, 15 words): [P1 CORE] [Pattern from variation matrix]
  AI PROMPT: [Character DNA] + hook visual + text overlay
  TRANSITION OUT: [end frame description for Screenshot Shuffle]

PROBLEM/CONTEXT (7s, 25 words): [P2 CONTEXT] Why parents need this
  AI PROMPT: [Character DNA] + problem illustration
  TRANSITION IN: [matching start from previous scene]
  TRANSITION OUT: [end frame for next scene]

DEMONSTRATION A - Setup (8s): [P1 CORE] The key moment of the activity
  AI PROMPT: [Character DNA] + primary action + camera push-in
  OVERLAP: end-action matches start of Demo B

DEMONSTRATION B - Detail (8s): [P3 DEPTH] Additional steps/angles
  AI PROMPT: [Character DNA] + secondary action
  OVERLAP: end-action matches start of Demo C

DEMONSTRATION C - Result (9s): [P2 CONTEXT] Child's reaction/achievement
  AI PROMPT: [Character DNA] + payoff moment

KEY LEARNING (10s, 25 words): [P3 DEPTH] What the child develops
  AI PROMPT: [Character DNA] + learning visual
  TRANSITION IN/OUT: [matching descriptions]

PRACTICAL TIP (10s, 20 words): [P2 CONTEXT] How to do this at home
  AI PROMPT: [Character DNA] + tip illustration

CTA (5s, 15 words): [P1 CORE] Follow + share prompt
  AI PROMPT: Brand moment + logo + warm glow
```

**Resulting timelines from one script:**
- **60s master** (all scenes): Hook → Problem → Demo A → Demo B → Demo C → Learning → Tip → CTA
- **30s version** (P1+P2): Hook → Problem → Demo A → Demo C → Tip → CTA
- **15s loop** (P1 only): Hook → Demo A → CTA (loop back to hook)

**DaVinci workflow:** Create the 60s master timeline first. Duplicate it twice. **Delete P3 scenes manually for 30s. Delete P2+P3 manually for 15s.** The DaVinci scripting API can only append to timelines — it cannot delete or trim clips (PE line 558). The deletion step in derivative creation MUST be done manually in the timeline editor. Transitions auto-close gaps (or add cross-dissolves at cut points). Three exports from the same clip library.

**Hook variation matrix**: Each KB entry generates **7 different videos** using the 7 hook patterns above. Same content, different opening -- enables A/B testing.

**Content tree**: Each entry also branches into: quick tip (30s), deep dive (90s), story version, myth-buster, user question response, seasonal/trending adaptation.

**4-pillar content mix:**
- Educational/How-To: 40%
- Myth-Busting/Authority: 25%
- Behind-the-Scenes/Authentic: 20%
- Entertainment/Trending: 15%

**A/B testing protocol:**
- **North star metric: 65%+ 3-second retention** → 4-7x more impressions (OpusClip Nov 2025 study of general short-form content; parenting/educational niche benchmarks may differ — establish own baseline in weeks 1-4)
- Single variable isolation per test
- Wait 24-48 hours, TikTok needs ~20K views for significance
- Track: 3-sec retention, avg watch time, completion rate, save rate, share rate

**AI prompt specification (8-part framework):**
```
Shot Type + Subject → Action → Setting/Context → Visual Style → Camera Movement → Lighting/Composition → Audio Cues → Technical Controls
```

**Character DNA template (include in every prompt):**
```
NAME: Baby Brain
PHYSICAL: 18-month appearance, curly light brown hair, bright curious eyes, round face
CLOTHING: Soft cotton onesie in muted earth tones
DISTINCTIVE: Slightly oversized head, gentle expression
STYLE ANCHOR: Claymation/stop-motion aesthetic, warm clay-amber tones, bioluminescent subsurface glow
```

---

### PIPELINE DECISION 6: Multi-Scene Stitching & Continuity (PA + PC)

**All video tools max out at 5-10s per generation.** Any video longer than 10s requires stitching multiple clips. This is the core production challenge and must be designed into the script/scene breakdown from the start.

**Three stitching strategies (use together):**

**1. Screenshot Shuffle (PA -- Hailuo primary technique):**
1. Generate first 5-10s clip
2. Capture the **final frame** as a screenshot
3. Upload that screenshot as the **starting image** for the next generation
4. Write prompt continuing the action logically
5. Repeat for each subsequent scene

This creates natural visual flow between segments. Shorter clips (5s) maintain better consistency than longer ones.

**2. Overlap Technique (PA -- for action continuity):**
- Design Clip 1 to **end** with: "character reaches for door handle"
- Design Clip 2 to **start** with: "character's hand on door handle, pushing open"
- The overlapping action description bridges the cut point
- This MUST be scripted into the scene breakdown at writing time

**3. Kling Extension Chain (PC -- for 60s content):**
- Generate 10s base clip
- Use "Extend Video" to add 5s at a time
- Each extension needs a new prompt describing what happens next
- Quality degrades after ~30s of extensions
- **Better alternative:** Generate 6x 10s standalone clips and stitch in DaVinci

**Character Bible for cross-clip consistency (PA):**
- Create master document with **exact phrasing** for physical traits, wardrobe, distinctive features
- Use "brown trench coat" consistently -- **never** switch to "coat" or "jacket"
- Include technical specs: "35mm lens, low-angle shot" for framing consistency
- Prepend Character DNA prefix to EVERY prompt

**Transition handling in DaVinci (PA + PD):**
- **Hard cuts**: Work when action flows naturally between clips
- **Cross-dissolves** (0.5-1s): Hide minor inconsistencies in character/lighting
- **J-cuts / L-cuts**: Audio leads/follows visual by 5-15 frames (smoother perceived transition)
- **DaVinci Smooth Cut**: Specifically masks discontinuities in AI-generated clips
- Keep transitions **under 1 second** -- longer dissolves expose AI facial inconsistencies

**Implication for scene breakdowns:**
Every scene in the script must specify:
```
SCENE [N]:
  ...
  TRANSITION OUT: [end action/frame description for Screenshot Shuffle]
  TRANSITION IN: [matching start description for next scene]
```
This makes stitching pre-scripted and deterministic rather than ad-hoc in post.

---

### PIPELINE DECISION 7: Asset Management (PA + PD)

**Folder structure:**
```
/BB_PRODUCTION/
├── /01_CHARACTER_REFERENCES/    # MJ hero images, reference sheets
├── /02_SCRIPTS/                 # Script files with scene breakdowns
├── /03_SCENE_IMAGES/            # MJ-generated scene stills
├── /04_RAW_GENERATIONS/         # All video tool output
│   ├── /VID_001_ObjectPermanence/
│   │   ├── VID001_S01_T01_pika_raw.mp4
│   │   └── VID001_S01_T02_pika_raw.mp4
├── /05_SELECTS/                 # QC-approved clips
├── /06_WORKING_EDITS/           # DaVinci project files
├── /07_FINAL_EXPORTS/           # Platform-ready videos
│   ├── /tiktok/
│   ├── /instagram/
│   ├── /youtube/
│   └── /facebook/
├── /08_VOICEOVER/               # VO files (self-recorded + Qwen3-TTS)
├── /09_CAPTIONS/                # SRT files
└── /10_AUDIO/                   # Music beds, SFX
```

**Naming convention:** `[VideoID]_[Scene]_[Take]_[Tool]_[Status].mp4`
Example: `VID023_S02_T01_pika_approved.mp4`

**Tracking:** Airtable (free tier, 1,000 records) with 4 linked tables: Videos, Clips, Prompts, Characters. Alternative: SQLite database for full local control.

**DaVinci integration:** Standard Bins per video, Smart Bins for auto-filtering (by resolution, duration), Power Bins for brand assets.

---

### PIPELINE DECISION 8: Automation & Tooling (PE)

**Verdict: MCP servers cover 70% of the pipeline. QC pipeline and prompt generation are highest-ROI. DaVinci scripting has diminishing returns at our volume -- template approach is optimal.**

#### MCP Server Stack (Confirmed Available)

| Server | Purpose | Stars | Install |
|--------|---------|-------|---------|
| **Video-Audio MCP** (misbahsy) | ffmpeg wrapper: concat, VO overlay, captions, metadata strip | 42 | `uv sync` (git clone) |
| **OpenCV MCP** (GongRzhe) | Frame extraction, image comparison, feature detection | 84 | `pip install opencv-mcp-server` |
| **SQLite MCP** (Anthropic official) | Database queries from Claude Code | N/A | `uvx mcp-server-sqlite` |
| **ElevenLabs MCP** (Official) | TTS cloud fallback | N/A | `uvx elevenlabs-mcp` |
| **DaVinci Resolve MCP** (samuelgursky) | Natural language DaVinci control | **426** | `git clone + install.sh` |
| **Fast-Whisper MCP** | Transcription/alignment | 50+ | `pip install faster-whisper-mcp` |
| **image-process-mcp-server** | Resize, crop, watermark for thumbnails | 30+ | `npx -y image-process-mcp-server` |
| **Metricool MCP** (Official) | Scheduling (requires Advanced plan ~$20/mo) | N/A | `uvx mcp-metricool` |

**NOT available as MCP**: MidJourney, Pika, Kling -- use direct Python API calls.

**Skip initially**: Video Quality MCP -- its VMAF calculation duplicates what ffmpeg + Claude vision can do.

#### Critical Constraint: 8GB Local VRAM Sharing

Qwen3-TTS uses **4-6GB VRAM**. It **cannot run simultaneously** with video generation or other GPU-heavy tasks on the local 8GB GPU. Two approaches:

**Option A — Sequential (local only):**
1. Generate all video clips (local GPU)
2. Then run Qwen3-TTS for all voiceovers (local GPU)
3. Then QC and assembly (CPU-bound)

**Option B — Parallel (local + Colab):**
1. Generate video clips on local GPU (8GB)
2. Simultaneously run TTS on Colab T4 (15GB free) — eliminates VRAM contention
3. QC and assembly (CPU-bound)

Cloud fallback: Fish Audio API (~$11/mo Plus tier) during GPU-heavy periods.

#### CRITICAL FINDING: fal.ai Charges Separately from Hailuo

**fal.ai is pay-per-use, NOT a pass-through to your Hailuo subscription.** The $199.99 Hailuo Max subscription is for the **web interface only**. API usage via fal.ai is billed separately:
- Hailuo 01 Live (768p, 6s): ~$0.27/video via fal.ai
- Hailuo 02 Pro (1080p, 6s): ~$0.48/video via fal.ai

**Implication for burst month:** You cannot automate via API AND use your subscription. Two options:
1. **Web interface** ($199.99 subscription): Manual/semi-manual with Chrome autopilot extension. Unlimited Relax Mode.
2. **API** (fal.ai): Fully automated. But 500 videos × $0.27 = **$135 on top of** any subscription.

**Revised burst strategy:** Use web interface with Hailuo Max subscription for maximum throughput. The Chrome "Hailuo & Runway AutoPilot" extension provides semi-automation. Reserve API (fal.ai) for specific re-generations or smaller batches where automation justifies the per-video cost.

#### DaVinci Resolve: WSL2 Not Supported

**DaVinci scripting must run from Windows-native Python**, not WSL2. The scripting API requires DaVinci to be running with Studio license.

**What IS scriptable:**
- Auto-import from folders
- Create timeline from clips
- Apply LUT
- Import SRT subtitles
- Batch render to presets

**What is NOT scriptable:**
- Audio ducking (manual only)
- Trim/split clips (append only)
- Fine timeline editing
- PowerGrade application (workaround via `ApplyGradeFromDRX()`)

**Recommended library:** pybmd (`pip install pybmd`) -- actively maintained, auto-launches Resolve.

**ROI for 25-35 videos/month:**

| Approach | Setup | Per-video | Monthly total |
|----------|-------|-----------|---------------|
| Manual | 0 hrs | 45-60 min | 25-35 hrs |
| Template + 3 scripts | 15-20 hrs | 20-30 min | 12-18 hrs |
| Full automation | 50+ hrs | 10-15 min | 6-9 hrs |

**Verdict:** Template + 3 scripts. Breaks even in month 2. Full automation doesn't justify 50+ hours of dev work.

#### TikTok API: Private-Only Until Audit

**Unaudited TikTok apps** (initial state):
- Limited to 5 users per 24 hours
- **ALL posts forced to SELF_ONLY (private)** -- must manually change after upload
- Audit requires: demo videos, compliance documentation, privacy policy, weeks of review

**Strategy:** Manual TikTok posting initially. Automate YouTube + Instagram + Facebook first (all API-ready).

**⚠️ PE BUG: YouTube upload code sets `selfDeclaredMadeForKids: True`** -- this is WRONG. Baby Brains content is for ADULTS (parents), NOT children. This flag disables comments, notifications, and severely limits reach. Must be `False`.

#### Voice Pipeline: Qwen3-TTS + aeneas

**Qwen3-TTS** ($0 local, already installed in ATLAS):
- Location: `atlas/voice/tts_qwen.py`
- Voice cloning via reference audio + transcript (ICL mode)
- ~4-6GB VRAM. Jeremy Irons voice already configured; clone an Australian voice from short sample
- Config: `config/voice/qwen_tts_voices.json`

**Maya1** ($0 via Colab T4, investigate):
- 3B params, Apache 2.0, voice *design* via natural language description
- 20+ inline emotion tags (`<laugh>`, `<whisper>`, `<sigh>`, etc.)
- Needs 16GB+ VRAM — test on free Colab T4 (15GB usable, borderline). See A68

**aeneas** for forced alignment (text → timed SRT):
- Accent-agnostic (better than Whisper for known script text)
- `python -m aeneas.tools.execute_task voiceover.wav script.txt "task_language=eng|..." output.srt`
- Works well with Australian accent
- Sentence-level by default; word-level needs `--presets-word` or WhisperX post-processing

**Caption burn-in**: ffmpeg's drawtext does NOT support word-by-word karaoke highlighting. Requires ASS subtitle format with `\kf` tags generated from forced alignment. DaVinci 20's built-in animated subtitles are easier for this.

#### QC Pipeline Implementation

**Trigger:** Hybrid -- watchdog auto-queues new clips to SQLite as "pending", manual `/qc` command triggers Claude review.

**WSL2 constraint:** inotify does NOT work for files on `/mnt/c/`. Store raw generations in WSL2 Linux filesystem or use `PollingObserver`.

**Optimal frame resolution:** 1024px on long edge (Claude vision auto-resizes >1568px; <512px loses artifact detail).

**VMAF thresholds:** 80-85 acceptable for social media. Premium streaming targets 93+, but platform compression makes higher scores unnecessary.

**SSIM for character consistency:** Compare first frame of generated clip against source MJ image using scikit-image `structural_similarity`. Score >0.7 indicates good preservation.

#### Build Priority Roadmap

> **Detailed week-by-week implementation plan in [WORKFLOW.md](WORKFLOW.md)** — see Build Priority section.

**Phase 1 (Week 1-2): Foundation + Testing**
- Verify Pika Standard/Pro license terms, DaVinci Studio purchase, Windows Python setup
- MJ character reference sheet with --oref + --sref + --sv testing
- Test clay keyword variants and multi-person success rate
- Qwen3-TTS Australian voice test (already installed); Maya1 test on Colab T4 (A68)
- SQLite database with schema + Anthropic SQLite MCP
- ffmpeg scripts: keyframe extraction, per-platform exports, metadata stripping
- Basic QC workflow (manual trigger)

**Phase 2 (Week 3-4): Audio + Assembly**
- Qwen3-TTS vs Fish Audio API vs Maya1 (Colab) comparison for primary TTS
- Music licensing setup (Uppbeat/Epidemic Sound), verify CML cross-platform limitations
- 5 script templates adapted from PF
- DaVinci scripting spike (Windows Python, confirm append-only constraint)
- Per-platform export presets, Fairlight ducking, Power Bins setup
- First real batch: 3-5 complete videos

**Phase 3 (Month 2): Automation**
- Hailuo burst generation (web interface + Chrome extension, NOT fal.ai API)
- DaVinci import + timeline scaffold + batch render scripts (Windows Python)
- P1/P2/P3 derivative workflow (deletion step is MANUAL)
- YouTube + Instagram API uploads (with `madeForKids: false`)

**Phase 4 (Month 3+): Polish**
- DaVinci MCP integration
- Metricool scheduling (if Advanced plan justified)
- Analytics feedback loop to content database
- TikTok API audit (if volume justifies)
- Consider Creatomate ($54-99/mo) if manual workflow too slow

---

### COMPLETE END-TO-END PIPELINE

```
PHASE 1: CONTENT PLANNING
  Knowledge Base entry
  → Script template (3-act, 7 hook variations)
  → Scene breakdown (6-8 sec per scene, detailed AI prompts)
  → Character DNA prefix for all prompts

PHASE 2: IMAGE GENERATION
  Scene descriptions + Character DNA
  → MidJourney V7 ($30 Standard, --oref for character, --sref for style)
  → Hero images at max resolution
  → Reference sheet (front, side, 3/4, detail views)

PHASE 3: VIDEO GENERATION
  MJ images + motion-only prompts
  → PRIMARY: Pika 2.5 ($28 Pro) for clips ≤25s
     - Draft at 480p (12 credits), finalize at 720p-1080p
     - Pikaffects (Squish It) for clay deformation
     - Same MJ source image across all clips
  → SECONDARY: Kling O1 ($37 Pro) for 60s content
     - 6x 10s clips, stitch externally
     - Elements for character bundles
     - Standard Mode for iteration, Professional for finals
  → BURST: Hailuo Max ($199.99 one month) for library building
     - 01 Live model for stylized content
     - Web interface batch submission (fal.ai charges separately — see Pipeline Decision 8)
     - Virtual credit card, download immediately

PHASE 4: VOICE & AUDIO
  Script text
  → Self-recorded Australian VO (primary, gold standard)
  → Qwen3-TTS ($0 local, already installed) for bulk/backup
  → OR run TTS on Colab T4 ($0, 15GB) in parallel with local video gen
  → Fish Audio API (~$11/mo Plus tier; $5.50/mo annual) cloud fallback
  → Whisper → SRT for captions

PHASE 5: QC (in Claude Code via MCP)
  Raw clips (stored in WSL2 Linux filesystem, NOT /mnt/c/)
  → OpenCV MCP extracts keyframes at 2fps, 1024px
  → SSIM comparison: first frame vs source MJ image (>0.7 = good)
  → Claude vision reviews frames (hands, face, glow, background, motion)
  → Results logged to SQLite via SQLite MCP
  → Pass/fail with notes, VMAF 80-85 threshold for social media

PHASE 6: ASSEMBLY (DaVinci Resolve Studio -- Windows Python, NOT WSL2)
  Approved clips + VO + SRT + brand assets (Power Bins)
  → pybmd script: auto-import clips from folder structure
  → pybmd script: create timeline scaffold from scene breakdown
  → Master template (1080x1920, 30fps, track structure, PowerGrade)
  → Fairlight auto-ducking (MANUAL -- not scriptable)
  → Fusion glow enhancement if needed
  → AutoSubs/Whisper for caption generation (or DaVinci 20 word highlight)
  → Duplicate master timeline → delete P3 scenes (30s) → delete P2+P3 (15s)
  → pybmd script: batch render 3 lengths × 4 platforms = up to 12 exports
  → 20-30 minutes per video (template + 3 scripts approach)

PHASE 7: CAPTION ALIGNMENT & BURN-IN (uses voice files from Phase 4)
  Voice audio (.wav) from Phase 4 + script text
  → aeneas forced alignment: script text + .wav → word-timed .srt
  → ASS format with \kf tags for karaoke highlighting (ffmpeg drawtext can't do this)
  → Caption QC: WER ≤10%, sync tolerance ≤0.2s

PHASE 8: DISTRIBUTION
  Final exports
  → YouTube Shorts: Data API v3 (immediate, ~100 uploads/day)
  → Instagram Reels: Graph API (requires app review, 4-8 hrs setup)
  → Facebook Reels: Graph API (Pages only, same review)
  → TikTok: MANUAL initially (API = private-only until audit, weeks)
  → Metricool MCP for scheduling (requires Advanced plan ~$20/month)
  → 5-7 videos/week, stagger posting times
  → A/B test hooks, track 3-second retention in content database
```

---

## APPENDIX: Key Numbers at a Glance

| Category | Metric | Value | Source Confidence |
|----------|--------|-------|-------------------|
| **Budget** | Target range | $50-120/month | User specified |
| **Budget** | Recommended Stack A | $58/month (MJ Standard + Pika Pro) | Derived |
| **Tools** | Best stylized quality | Pika 2.5 (5/5, 74-89% success) | CLAIMED |
| **Tools** | Only native 60s | Kling AI | VERIFIED (unique) |
| **Tools** | Best character consistency | Vidu Q2 (7 refs) or Kling (4 refs, production-proven) | CLAIMED |
| **Length** | TikTok edu reach boost at 60s+ | +43.2% | VERIFIED (Napolify) |
| **Length** | Cross-platform sweet spot | 60 seconds | Derived from 2A+2B |
| **Length** | Hook window | 3 seconds | VERIFIED (multi-source) |
| **Audio** | AI voiceover FYP penalty | -38% | CLAIMED (single source) |
| **Audio** | Qwen3-TTS (local, installed) | $0/month, voice cloning, 0.6B params | VERIFIED (installed) |
| **Audio** | Fish Audio API (cloud primary) | ~$11/mo Plus tier, #1 TTS-Arena | CLAIMED (3B) |
| **Audio** | Colab T4 for parallel TTS | Free 15GB GPU, 12hr sessions | VERIFIED (S23) |
| **Policy** | Stylized AI content labeling | Optional/exempt (all platforms) | VERIFIED |
| **Policy** | MidJourney C2PA embedding | Does NOT embed | VERIFIED |
| **Competition** | Montessori+AI accounts worldwide | ZERO | CLAIMED (6A search) |
| **Competition** | Australian AI parenting creators | ZERO | CLAIMED (6A search) |
| **MJ V7** | --cref status | DEPRECATED, use --oref | VERIFIED (official) |
| **MJ V7** | Video reference features | NONE work with video | VERIFIED (official) |
| **MJ V7** | Video max length | 21s (quality degrades after 9s) | VERIFIED |
| **MJ V7** | Video costs | 8x image GPU time | CLAIMED |
| **Glow** | Best SSS formula | `subsurface scattering, lit from within, soft clay texture, wax-like texture --s 200-300` | CLAIMED (community) |
| **Glow** | Best animation tool for glow | Luma Ray3 (HDR) or Kling 2.1 Pro (stability) | CLAIMED |
| **Schedule** | Best posting time (AEDT Oct-Apr; AEST May-Sep) | Thursday 7-10 PM | CLAIMED (4B) |
| **Schedule** | Optimal frequency | 5-7 videos/week | CLAIMED (4B) |
| **Schedule** | Cross-post penalty (TikTok) | Up to 40% | CLAIMED (4B) |
| **Schedule** | Best free scheduler | Metricool (50 posts/month free) | CLAIMED (4B) |
| **Production** | Real-world time for 25 videos | 15-25 hrs/mo (simple faceless); 45-75 hrs/mo (character-consistent) | CLAIMED (4A) |
| **Production** | Generations per keeper (simple) | 2-3 | CLAIMED (4A) |
| **Production** | Generations per keeper (complex) | Up to 10 | CLAIMED (4A) |
| **Production** | Real-world cost per video | $2-5 including failures | CLAIMED (4A) |
| **Hailuo** | Trustpilot rating | 1.6/5 (79% one-star) | VERIFIED (PA) |
| **Hailuo** | Best model for clay | 01 Live (5/5 artistic style preservation) | CLAIMED (PA) |
| **Hailuo** | Max plan throughput | 333 standard 768p or 83 Pro 1080p from 20K credits | CLAIMED (PA) |
| **Pika** | Motion-only prompting | Do NOT restate visual style for image-to-video | CLAIMED (PB) |
| **Pika** | Squish It Pikaffect | Best clay deformation effect (15 credits I2V) | CLAIMED (PB) |
| **Pika** | Realistic monthly output (Pro) | 25-35 polished 720p clips OR 12-18 at 1080p | CLAIMED (PB) |
| **Pika** | Quick draft cost | 480p 5s = 12 credits (~190 tests from 2,300) | VERIFIED (PB) |
| **Kling** | True native max | 10s per clip (60s = 12x extensions) | VERIFIED (PC) |
| **Kling** | Standard vs Professional | 3.5x credit savings using Standard for iteration | VERIFIED (PC) |
| **Kling** | Pan/tilt terminology | INVERTED: "pan" = vertical, "tilt" = horizontal | CLAIMED (PC) |
| **DaVinci** | Metadata stripping | Rendering auto-strips most metadata including AI info | VERIFIED (PD) |
| **DaVinci** | Per-video assembly time | 15-25 min (with template) | CLAIMED (PD) |
| **DaVinci** | Caption automation saving | 6-11 min (automated) vs 16-26 min (manual) | CLAIMED (PD) |
| **DaVinci** | LUFS target | -14 LUFS universal safe target | VERIFIED (PD) |
| **Script** | Critical metric | 65%+ 3-second retention → 4-7x impressions | CLAIMED (PF) |
| **Benchmarks** | Engagement rate (likes) | >50 likes per 1K views = very good | CLAIMED (OLD-1 ANL-005) |
| **Benchmarks** | Engagement rate (comments) | >5 comments per 1K views = good | CLAIMED (OLD-1 ANL-006) |
| **Benchmarks** | Hook rate benchmark | 30.7% average, 40-45% top quartile | CLAIMED (OLD-5 AK-001) |
| **Benchmarks** | Completion rate (20s) | >80% = achievable for hits | CLAIMED (OLD-1 ANL-003) |
| **Benchmarks** | Completion rate (60s) | >60% = very solid, 50%+ = successful | CLAIMED (OLD-1 ANL-003) |
| **Benchmarks** | 3-second retention target | 65% = good (algorithmic boost), 80% = excellent (stretch goal) | CLAIMED (PF + OLD-1) |
| **Script** | Words per line | 12-16 max | CLAIMED (PF) |
| **Script** | Scene change frequency | 3-5s (P1 hooks/snackable), 6-8s (P2/P3 educational) | CLAIMED (PF + OLD-4) |
| **Script** | Hook variations per entry | 7 (one per hook pattern) | Derived (PF) |
| **Automation** | MCP servers available | 8 confirmed (see PE section) | VERIFIED (PE) |
| **Automation** | MCP for MJ/Pika/Kling | NONE exist -- use direct API | VERIFIED (PE) |
| **Automation** | DaVinci MCP | samuelgursky/davinci-resolve-mcp (426 stars) | VERIFIED (PE) |
| **Automation** | DaVinci + WSL2 | NOT supported -- Windows Python only | VERIFIED (PE) |
| **Automation** | TTS VRAM (Qwen3-TTS) | 4-6GB, cannot coexist with video gen on local 8GB. Colab T4 (15GB free) enables parallel. | VERIFIED (PE) + S23 |
| **Automation** | fal.ai + Hailuo | SEPARATE billing (~$0.27/video, NOT pass-through) | VERIFIED (PE) |
| **Automation** | TikTok API posting | Private-only until audit approved (weeks) | VERIFIED (PE) |
| **Automation** | VMAF social media threshold | 80-85 acceptable | CLAIMED (PE) |
| **Automation** | Claude vision optimal frame size | 1024px on long edge | CLAIMED (PE) |
| **Automation** | Per-video time (template+scripts) | 20-30 min | CLAIMED (PE) |
| **Automation** | Setup time (Phases 1-3) | 40-60 hours total | CLAIMED (PE) |
| **Automation** | Template approach break-even | Month 2 | CLAIMED (PE) |

---

## APPENDIX: Australian Localisation Guide

> Cross-reference: BB-Writer agent at `/web/.claude/agents/BabyBrains-Writer.md` handles AU English in text generation. This guide covers visual and production localisation.

### Indoor Visual Cues (1-2 per AI prompt)

| Cue | Prompt Description (NO brand names) | Source |
|-----|--------------------------------------|--------|
| Power outlets | Three-pin Australian power outlets on wall | OLD-1 SET-001 |
| Skirting boards | Timber skirting boards, painted or stained | OLD-1 SET-002 |
| Rugs | Jute, sisal, or natural fibre rugs | OLD-1 SET-003 |
| Textiles | Linen textures on curtains, cushions, throws | OLD-1 SET-004 |
| Ceiling fans | White ceiling fans | OLD-1 SET-005 |
| Doors | Sliding glass doors leading to outdoor area | OLD-1 SET-006 |
| Flooring | Polished concrete, light timber, or tiles | OLD-1 SET-007 |
| Plants (indoor) | Fiddle-leaf fig, monstera, devil's ivy | OLD-1 SET-008 |
| Light switches | Australian rocker-style light switches (not toggle) | OLD-3 AU pack |
| Furniture | Mid-century modern mixed with natural timber | OLD-3 AU pack |

### Outdoor Visual Cues (1-2 per AI prompt)

| Cue | Prompt Description (NO brand names) | Source |
|-----|--------------------------------------|--------|
| Fences | Timber or Colorbond-style fencing | OLD-1 SET-012 |
| Plants (outdoor) | Bottlebrush, grevillea, kangaroo paw, native grasses | OLD-1 SET-013 |
| Lighting | North-facing windows for natural light | OLD-1 VIS-001 |
| Architecture | Weatherboard, brick, or rendered exterior | OLD-1 SET-014 |
| Entertaining | Covered outdoor area, pergola or verandah, timber decking | OLD-3 AU pack |

### Language and Spelling Reference

Cross-reference: BB-Writer agent handles this in text generation. This table is for manual QC and review.

| AU English | NOT | Notes |
|-----------|-----|-------|
| Mum | Mom | Always |
| Nappies | Diapers | Always |
| Kindy / Kinder | Kindergarten / Pre-K | Regional variation OK |
| Bub | Baby (informal) | Use sparingly for warmth |
| Organise | Organize | -ise endings throughout |
| Colour | Color | -our endings throughout |
| Behaviour | Behavior | -our endings throughout |
| Centre | Center | -re endings throughout |
| Practise (verb) | Practice (verb) | Noun = practice |
| Favourite | Favorite | -our endings throughout |

### Localisation Dosage Rules

- **1-2 AU localisers per MJ/AI prompt** (OLD-3 AUD-002): Avoids overt clichés, keeps prompts focused
- **2-3 AU cues per finished video** (OLD-1 SET-016): Enough for subconscious recognition without making it "about" Australia
- **Subtlety principle**: AU details should be noticed subconsciously, never foregrounded (OLD-3 PSY-005, OLD-1 AUD-003). The goal is "I have that same rug!" recognition, not "this is an Australian video"

### Avoid List

| Do NOT Include | Why | Source |
|---------------|-----|--------|
| American power outlets | Instantly breaks AU immersion | OLD-1 SET-001 |
| Snow/winter imagery | AU content = southern hemisphere seasons | OLD-5 AS-007 |
| Brand names in prompts | Hallucination risk, trademark risk, AI generation artifacts | OLD-3 AUD-004 |
| "Mom" / American spelling | Primary audience is Australian | OLD-1 BRV-003 |
| Loud kookaburra audio | Startling for infants. Magpie ambient OK. | OLD-1 PRD-007 |
| Toggle light switches | American style, not AU | OLD-3 AU pack |

**Note**: "Carpet (wall-to-wall)" and "Front-loading dryers" removed from avoid list per user decision — both are common enough in Australian homes.

### Products and Brands (Describe, Never Name)

When depicting Australian baby/toddler products, describe the product TYPE and material, never the brand name. This avoids hallucination risk and trademark issues.

| Category | Describe as... |
|----------|---------------|
| Sleep bags | Organic cotton zip-front sleep bags |
| Wooden toys | Natural timber stacking toys, wooden blocks |
| Safety gates | Pressure-mounted safety gate, white metal frame |
| Textiles | Natural linen, organic cotton throws |
