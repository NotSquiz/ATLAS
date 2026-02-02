# 1B: MidJourney Video -- Extracted Data

Extraction date: 2026-02-01
Source file: `docs/research/bb-content-production/results/1B.md`
Source title: "MidJourney video generation: February 2026 evaluation for stylized educational content"

---

## PRICING & PLANS

| Plan | Monthly Price | Fast GPU Hours | Video Access (SD) | HD Video (720p) | Relax Video |
|------|--------------|----------------|-------------------|-----------------|-------------|
| Basic | $10/month | 3.3 hours | SD only, Fast Mode | No | No |
| Standard | $30/month | 15 hours | SD + HD, Fast only | Yes (Fast only) | No |
| Pro | $60/month | 30 hours | Full access | Yes (Fast only) | Yes (SD only) |
| Mega | $120/month | 60 hours | Full access | Yes (Fast only) | Yes (SD only) |

- Additional GPU hours: **$4/hour**, expire after **60 days** [VERIFIED -- official docs cited]
- "Unlimited video" marketing claim applies ONLY to Pro ($60) and Mega ($120) plans, ONLY through Relax Mode, ONLY at 480p SD, with **0-30 minute variable queue waits** [VERIFIED -- official docs cited]
- Fast Mode video consumes GPU time at **8x the rate of image generation** [VERIFIED -- official docs cited]
- Therefore Pro plan's 30 GPU hours = approximately **3.75 hours** of Fast Mode video generation [CLAIMED -- derived calculation, math checks out: 30/8 = 3.75]
- HD mode (720p) costs approximately **3.2x more** than SD mode [VERIFIED -- official docs cited]
- HD mode is available ONLY in Fast Mode -- **no unlimited HD video exists on any plan** [VERIFIED -- official docs cited]
- Pro plan ($60/month) described as "the practical minimum" for content production [CLAIMED -- author recommendation, not sourced]

Source: docs.midjourney.com/hc/en-us/articles/37460773864589-Video, updates.midjourney.com/introducing-our-v1-video-model/ (June 18, 2025)

---

## GENERATION LIMITS

- Each video job produces **4 video variations of 5 seconds each** [VERIFIED -- official docs cited]
- GPU cost per video job: approximately **8x** an image job [VERIFIED -- official docs cited]
- Batch size can be reduced: `--bs 1` (4x cost reduction) or `--bs 2` (2x cost reduction) [VERIFIED -- official docs cited]
- Relax Mode queue: **0-30 minutes** variable wait [VERIFIED -- official docs cited]
- HD video (720p) available ONLY in Fast Mode [VERIFIED -- official docs cited]
- No daily/monthly numeric caps mentioned -- limits are GPU-hour-based for Fast Mode, unlimited for Relax Mode (Pro/Mega only, SD only) [VERIFIED -- structural inference from pricing table]

---

## VIDEO CAPABILITIES

### Core Specifications
- **Workflow**: Image-to-video EXCLUSIVELY -- no text-to-video capability [VERIFIED -- official docs cited]
- **Starting length**: 5 seconds per generation [VERIFIED -- official docs cited]
- **Maximum length**: 21 seconds (initial 5 seconds + up to 4 extensions of 4 seconds each) [VERIFIED -- official docs cited]
- **Resolution**: 480p (SD) standard; 720p (HD) for Standard/Pro/Mega plans in Fast Mode only [VERIFIED -- official docs cited]
- **Frame rate**: 24fps [VERIFIED -- official docs cited]
- **Generation time**: 2-5 minutes per 4-variation batch [VERIFIED -- official docs cited]
- **Audio**: None -- all outputs are silent [VERIFIED -- multiple sources cited]

### Reference System Support
- **--cref (character reference)**: NOT supported for video [VERIFIED -- official docs explicitly state this]
- **--sref (style reference)**: NOT supported for video [VERIFIED -- official docs explicitly state this]
- **Omni Reference**: NOT compatible with video generations [VERIFIED -- official docs quote: "Other Image Reference Types (not compatible with video generations): Image Prompt, Style Reference, Omni Reference (replaces Character Reference)."]

### Supported Video Parameters
- `--motion low` [VERIFIED -- official docs cited]
- `--motion high` [VERIFIED -- official docs cited]
- `--raw` [VERIFIED -- official docs cited]
- `--loop` [VERIFIED -- official docs cited]
- `--end` (target end frame via image URL) [VERIFIED -- official docs cited]
- `--bs #` (batch size control) [VERIFIED -- official docs cited]

### Animation Modes
1. **Auto Mode**: MidJourney decides motion -- best for atmospheric content [VERIFIED -- official docs cited]
2. **Manual Mode**: User writes motion prompt describing desired movement [VERIFIED -- official docs cited]
3. **Loop Mode**: Creates seamless loops where start and end frames match [VERIFIED -- official docs cited]

### External Image Animation
- External images can be animated by entering the image URL at the start of the prompt with `--video` [VERIFIED -- official docs cited]

### Platform Access
- Video generation available on **web only** -- NOT yet available in Discord bot [CLAIMED -- stated without explicit source URL]

Source: docs.midjourney.com/hc/en-us/articles/37460773864589-Video, updates.midjourney.com/looping-and-end-frame-for-video-video-in-the-discord-bot/ (July 25, 2025)

---

## QUALITY ASSESSMENT

### Overall Ranking
- Ranked **#1 overall** in a 9-scene comparison test against Kling 2.1, Hailuo 2, and Runway Gen-4 [VERIFIED -- TitanXT, July 2025]
- Won **7 of 9 test categories** [VERIFIED -- TitanXT, July 2025]

### Stylized Content Performance
- **Claymation and stop-motion aesthetics**: Described as "Great precision by perfecting textures like felt, fabric, or plasticine" [VERIFIED -- MidLibrary quote]
- **Abstract and artistic motion**: **85.7% success rate** (6/7 tests) for geometric abstractions and fluid art [VERIFIED -- test data cited]
- **Natural ambient motion**: **88.9% success rate** (16/18 tests) for scenes with clouds, water, fog, and subtle lighting changes [VERIFIED -- test data cited]

### Effective Prompts for Clay-Style Content
Specifically cited terms: "claymation," "plasticine," "stop-motion," "handcrafted patchwork puppet," "felt texture" [VERIFIED -- MidLibrary source cited]

### Human Figure and Baby Motion Performance

| Content Type | Success Rate | Sample Size | Common Issues |
|--------------|-------------|-------------|---------------|
| Portrait animations (subtle motion) | 66.7% | 10/15 | Facial distortion in ~33% of attempts |
| Human motion (single person) | 57% | 4/7 | Motion logic errors |
| Multi-person/complex motion | 20% | 1/5 | Position changes, limb deformation |
| **Overall human motion** | **41.7%** | **5/12** | Significant generation failure rate |

[VERIFIED -- gamsgo.com/blog/midjourney-video-generator (2025)]

### Specific Failure Types (from testing)
- Facial distortion: 3/15 portraits [VERIFIED -- test data cited]
- Drifting features: 2/15 portraits [VERIFIED -- test data cited]
- Motion logic errors: 4/12 motion tests [VERIFIED -- test data cited]
- Position/count changes: 3/12 motion tests [VERIFIED -- test data cited]
- Limb deformation: 2/12 motion tests [VERIFIED -- test data cited]

### User Quotes
- Trustpilot reviewer (December 6, 2025): "Pics are nice, videos not so much, after a while you become annoyed that the most humans looks kinda the same..." [VERIFIED -- Trustpilot, date cited]
- Text rendering: "Often illegible or nonsensical" -- noted as problematic for educational captions [CLAIMED -- stated without specific source attribution]

Source: gamsgo.com/blog/midjourney-video-generator (2025), trustpilot.com/review/www.midjourney.com

---

## SUCCESS RATE

- **Overall human motion success rate**: ~50% (stated as headline figure) [VERIFIED -- derived from test data showing 41.7% for overall human motion, rounded up in summary]
- **Portrait animations**: 66.7% (10/15) [VERIFIED -- test data]
- **Single-person motion**: 57% (4/7) [VERIFIED -- test data]
- **Multi-person motion**: 20% (1/5) [VERIFIED -- test data]
- **Abstract/artistic motion**: 85.7% (6/7) [VERIFIED -- test data]
- **Natural ambient motion**: 88.9% (16/18) [VERIFIED -- test data]
- **Recommended planning assumption**: 3-5 generation attempts per required clip featuring human motion [CLAIMED -- author recommendation]

Note: The headline "50% success rate" slightly overstates the tested "overall human motion" figure of 41.7% (5/12). The 50% figure appears to be a round number used in the introduction and limitations section.

---

## COMPARISON TO COMPETITORS

### Feature-by-Feature Comparison

| Capability | MidJourney | Kling 2.1 | Runway Gen-4 | Luma Dream Machine |
|-----------|------------|-----------|--------------|-------------------|
| Stylized 3D/clay aesthetic | 5/5 (Best) | 3/5 (Good) | 3/5 (Good) | 4/5 (Very good) |
| Human motion naturalness | 3/5 (Poor) | 5/5 (Best) | 4/5 (Very good) | 3/5 (Moderate) |
| Character consistency | 4/5 (Within clips only) | 4/5 (Good) | 5/5 (Best -- tagging system) | 3/5 (Moderate) |
| Audio generation | No | No | No | Yes |
| Resolution | 720p max | 1080p | 4K | 1080p |
| Text-to-video | No | Yes | Yes | Yes |
| Entry price | $10/month | ~$10/month | $12/month | $9.99/month |

[VERIFIED -- TitanXT comparison July 28, 2025; Tom's Guide coverage]

### Key Competitive Insights
- MidJourney aesthetic quality for stylized content is "widely considered superior" [CLAIMED -- editorial assessment]
- **Kling AI**: Focuses on realistic human motion -- may achieve better motion results for baby/parent figures [VERIFIED -- TitanXT comparison]
- **Runway Gen-4**: Offers "superior character consistency tools" through its tagging system [VERIFIED -- TitanXT comparison]
- **Luma Dream Machine**: Only competitor with native audio generation [VERIFIED -- comparison table]
- **Suggested hybrid approach**: MidJourney for stylized backgrounds + object animations, Kling for clips requiring reliable human/baby motion, composite in editing software [CLAIMED -- author recommendation]

Source: titanxt.io/post/comparing-top-ai-video-generators (July 28, 2025), tomsguide.com/ai/midjourneys-video-generator-is-behind-the-competition-heres-why-i-love-it-anyway

---

## KNOWN LIMITATIONS

1. **No audio generation** -- all outputs silent. Recommended tools: MM Audio, Soundverse, Suno AI [VERIFIED -- multiple sources]
2. **Low resolution ceiling** -- 480p/720p max vs competitors at 1080p-4K. Workaround: Topaz Video AI or Aiarty for upscaling [VERIFIED -- official specs]
3. **Short duration cap** -- 21 seconds max, requires external editing for longer sequences [VERIFIED -- official specs]
4. **Human motion unreliability** -- "Physical logic of human movements remains unreliable" with ~50% failure rate [VERIFIED -- test data]
5. **No character/style reference for video** -- --cref and --sref not supported [VERIFIED -- official docs]
6. **High GPU consumption** -- 8x image cost limits volume on lower-tier plans [VERIFIED -- official docs]
7. **Web-only access** -- video generation not available in Discord bot [CLAIMED -- stated in source]
8. **Text rendering fails** -- "Often illegible or nonsensical," problematic for educational captions [CLAIMED -- stated without specific source]
9. **No text-to-video** -- image-to-video workflow exclusively [VERIFIED -- official docs]
10. **Human faces look samey** -- "the most humans looks kinda the same" (Trustpilot user) [VERIFIED -- Trustpilot quote, December 6, 2025]

### Community Frustration Quote
January 2026 Trustpilot review: "Midjourney is going downhill and it seems the devs are asleep at the wheel. Too much focus on rolling out updates and new features, instead of just making sure the features that already exist are stable..." [VERIFIED -- Trustpilot, January 2026]

Source: trustpilot.com/review/www.midjourney.com (December 2025-January 2026), venturebeat.com coverage

---

## RECENT CHANGES

### January 9, 2026: Niji V7 Release (image model -- implications for video)
- Major coherency boost for anime-style content [VERIFIED -- updates.midjourney.com]
- "Fine details like eyes, reflections, and small background elements are now much clearer" [VERIFIED -- official quote]
- Better prompt following for "specific designs or repeatable characters" [VERIFIED -- official update]
- Caveat: More literal interpretation, so broad "vibey" prompts may behave differently [VERIFIED -- official update]
- Note: This is an IMAGE model update, not a video model update [VERIFIED -- explicitly stated]

### November 19-20, 2025
- Web interface updates and new user profile features (non-video specific) [VERIFIED -- official updates]

### August 2025: HD Video Mode Launch (most recent major VIDEO update)
- Native 720p resolution (4x pixel density vs SD) [VERIFIED -- official update]
- Available to Standard/Pro/Mega plans in Fast Mode [VERIFIED -- official update]
- Professional user feedback: "no longer wanting to use post-process upscalers" for many use cases [CLAIMED -- unattributed user report]

### Announced but NOT Yet Released (from June 2025 Roadmap)
- Turbo mode for faster generation [VERIFIED -- official roadmap]
- Native video upscaling [VERIFIED -- official roadmap]
- Start/end frame control improvements [VERIFIED -- official roadmap]
- **Niji-specific video model** for stylized content [VERIFIED -- official roadmap, June 2025]

Source: updates.midjourney.com (official), docs.midjourney.com/hc/en-us/articles/32199405667853-Version

---

## KEY NUMBERS (Quick Reference)

| Metric | Value | Confidence |
|--------|-------|------------|
| Pro plan price | $60/month | VERIFIED |
| Mega plan price | $120/month | VERIFIED |
| Max video length | 21 seconds (5s + 4x4s extensions) | VERIFIED |
| Max resolution | 720p (HD, Fast Mode only) | VERIFIED |
| Frame rate | 24fps | VERIFIED |
| GPU cost multiplier (video vs image) | 8x | VERIFIED |
| HD cost multiplier (vs SD) | 3.2x | VERIFIED |
| Generation time per batch | 2-5 minutes | VERIFIED |
| Variations per job | 4 | VERIFIED |
| Overall human motion success rate | 41.7% (tested) / ~50% (stated) | VERIFIED (see note) |
| Portrait animation success | 66.7% (10/15) | VERIFIED |
| Single person motion success | 57% (4/7) | VERIFIED |
| Multi-person motion success | 20% (1/5) | VERIFIED |
| Abstract/artistic motion success | 85.7% (6/7) | VERIFIED |
| Natural ambient motion success | 88.9% (16/18) | VERIFIED |
| Recommended attempts per keeper (human motion) | 3-5 | CLAIMED |
| Additional GPU hours cost | $4/hour | VERIFIED |
| Additional GPU hours expiry | 60 days | VERIFIED |
| Relax Mode queue wait | 0-30 minutes (variable) | VERIFIED |
| --cref support for video | No | VERIFIED |
| --sref support for video | No | VERIFIED |
| Text-to-video support | No | VERIFIED |
| Audio generation | No | VERIFIED |

---

## CONTRADICTIONS & UNCERTAINTIES

### 1. Human Motion Success Rate Discrepancy
- The introduction and limitations sections both state "~50% success rate" for human motion
- The detailed test data shows **41.7% (5/12)** for overall human motion
- These are not contradictory (50% is approximate) but the tested figure is notably lower than the headline claim
- **Confidence**: The 41.7% figure is more precise; the 50% figure appears to be editorial rounding

### 2. "Unlimited Video" Marketing vs Reality
- Marketing claims "unlimited video" for Pro/Mega plans
- Reality: unlimited ONLY for SD (480p) via Relax Mode with 0-30 minute waits
- HD (720p) video ALWAYS consumes Fast Mode GPU hours -- never unlimited
- **Confidence**: VERIFIED contradiction between marketing and actual capability

### 3. Character Consistency Rating
- Competitor table rates MidJourney character consistency at 4/5 "within clips only"
- But the detailed section confirms --cref and --sref do NOT work with video
- Cross-clip consistency requires manual workarounds (pre-generating consistent character images in V7 with --oref, then animating)
- The 4/5 rating may overstate practical consistency for multi-clip pipelines
- **Confidence**: Possible overstatement -- needs cross-reference with actual production testing

### 4. Test Sample Sizes Are Small
- Multi-person motion: only 5 tests (1/5 = 20%)
- Single person motion: only 7 tests (4/7 = 57%)
- Human motion overall: only 12 tests
- These sample sizes produce high variance -- the exact percentages should be treated as indicative, not definitive
- **Confidence**: Numbers are real but sample sizes warrant caution

### 5. Source Timeliness
- The TitanXT comprehensive comparison is from July 2025 (7 months old)
- HD Video Mode launched in August 2025 (after the comparison)
- Competitor capabilities may have changed significantly since July 2025
- Kling, Runway, and Luma have all released updates since the comparison date
- **Confidence**: Comparison data is STALE -- needs cross-reference with 1C (full tool comparison)

### 6. Niji Video Model Status
- Announced in June 2025 roadmap
- Still listed as "not yet released" as of the document's February 2026 date
- This is approximately 8 months after announcement with no delivery
- **Confidence**: May be delayed or deprioritized -- uncertain timeline

### 7. "3/5 Poor" vs "3/5 Moderate" Rating Inconsistency
- MidJourney human motion naturalness rated 3/5 labeled "Poor"
- Luma Dream Machine human motion naturalness rated 3/5 labeled "Moderate"
- Same numeric rating, different qualitative labels
- **Confidence**: Minor editorial inconsistency -- may reflect genuine nuance or may be an error

---

## SOURCE URLS

| URL | Context | Date Referenced |
|-----|---------|-----------------|
| docs.midjourney.com/hc/en-us/articles/37460773864589-Video | Official video documentation -- pricing, specs, parameter support | Undated (current) |
| updates.midjourney.com/introducing-our-v1-video-model/ | V1 video model launch announcement | June 18, 2025 |
| updates.midjourney.com/looping-and-end-frame-for-video-video-in-the-discord-bot/ | Loop mode and end frame feature announcement | July 25, 2025 |
| updates.midjourney.com | Official updates page (general) | Referenced for January 2026 Niji V7 |
| docs.midjourney.com/hc/en-us/articles/32199405667853-Version | Version history documentation | Referenced for recent changes |
| gamsgo.com/blog/midjourney-video-generator | Quality assessment and success rate test data (2025) | 2025 |
| trustpilot.com/review/www.midjourney.com | User reviews and complaints | December 2025-January 2026 |
| titanxt.io/post/comparing-top-ai-video-generators | 9-scene competitor comparison test | July 28, 2025 |
| tomsguide.com/ai/midjourneys-video-generator-is-behind-the-competition-heres-why-i-love-it-anyway | Editorial competitor comparison | Undated |
| venturebeat.com | Referenced for coverage of limitations | Undated (no specific URL) |

### Source Quality Notes
- Official MidJourney docs (2 URLs): High reliability for specs and pricing
- TitanXT comparison: Detailed methodology (9 scenes) but dated July 2025 -- 7 months stale
- Trustpilot reviews: Anecdotal, individual opinions, but specific and dated
- Gamsgo blog: Test data with specific sample sizes -- methodology unclear
- Tom's Guide: Editorial outlet, generally reliable for consumer tech
- VentureBeat: Referenced but no specific URL provided -- weak citation
- MidLibrary: Quoted for prompt terms but no URL provided -- weak citation
