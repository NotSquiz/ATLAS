# 1A: Kling AI Pricing -- Extracted Data

## PRICING TIERS

### Subscription Tiers (as of January 2026)

Source notes: "appears in two versions across sources, likely reflecting regional differences or recent updates." The table below is described as "the most commonly cited structure."

| Tier | Monthly Price | Annual Price (per month) | Credits Included | Estimated 5s Pro Videos |
|------|--------------|--------------------------|------------------|-------------------------|
| Free | $0 | N/A | 66/day (expire daily, no rollover) | ~2/day |
| Standard | $6.99-10 | ~$6.60 | 660 | 9-19 videos |
| Pro | $25.99-37 | ~$24.42 | 3,000 | 42-85 videos |
| Premier | $64.99-92 | ~$60.72 | 8,000 | 114-228 videos |
| Ultra | ~$180 (approximate) | ~$119 (approximate) | 26,000 | 742+ videos |

**Confidence notes:**
- CLAIMED: Price ranges (e.g., $6.99-10) suggest regional or version variation. The document does not pin down a single canonical price per tier.
- CLAIMED: Annual prices given with "~" prefix indicating approximation.
- CLAIMED: Ultra tier prices both use "~" prefix -- least precise of all tiers.

### Features by Tier

**All paid plans include:**
- 1080p HD resolution [CLAIMED]
- Watermark removal [CLAIMED]
- Priority processing [CLAIMED]
- Full commercial rights [CLAIMED]
- Credit rollover: up to 20% unused credits, valid 2 years [CLAIMED]

**Free tier limitations:**
- 720p resolution cap [CLAIMED]
- Watermarks present [CLAIMED]
- Queue delays reaching 3+ hours during peak times [CLAIMED]

---

## CREDITS SYSTEM

### Credit Consumption by Mode and Duration

| Video Duration | Standard Mode (720p) | Professional Mode (1080p) | With Native Audio (Kling 2.6) |
|---------------|---------------------|--------------------------|-------------------------------|
| 5 seconds | 10-20 credits | 35 credits | 50 credits |
| 10 seconds | 20-40 credits | 70 credits | 100 credits |
| 21 seconds | ~80 credits | ~150 credits | ~210 credits |
| 60 seconds | ~240 credits | ~420+ credits | ~600+ credits |

**Confidence notes:**
- CLAIMED: 5s and 10s values appear precise (no "~"). 21s and 60s values are all prefixed with "~" indicating estimates/extrapolations.
- CLAIMED: The "+" suffix on 420+ and 600+ indicates floor estimates only.
- CLAIMED: Native audio described as "nearly triple standard video-only costs."
- CLAIMED: Standard Mode range (10-20 for 5s) is notably wide -- reason for variance not explained.

### Video Extension Costs
- Extensions add 5 seconds at a time [CLAIMED]
- Extension cost equals generating a new clip of equal length [CLAIMED]
- Maximum extended video length: 3 minutes (through chained extensions) [CLAIMED]
- 60-second professional video: 400-600 credits [CLAIMED -- note this differs from the table's ~420+ figure, suggesting the 400-600 range accounts for extension chaining overhead]

### Lip Sync Feature
- Standalone lip sync: approximately 10 credits per 10 seconds of processed video [CLAIMED]

### Credit Rollover Rules
- Paid plans: up to 20% unused credits roll over [CLAIMED]
- Rollover credits valid for 2 years [CLAIMED]
- Free tier: credits expire daily, zero rollover [CLAIMED]

---

## COST-PER-VIDEO CALCULATIONS

### Raw Credit Cost (no failure adjustment)

Derived from credits table, using Pro plan ($37/month, 3,000 credits) as reference:

**5-second clips:**
- Standard Mode: 10-20 credits = $0.12-0.25/video (at $37/3000cr)
- Professional Mode: 35 credits = $0.43/video
- With Audio: 50 credits = $0.62/video

**10-second clips:**
- Standard Mode: 20-40 credits = $0.25-0.49/video
- Professional Mode: 70 credits = $0.86/video
- With Audio: 100 credits = $1.23/video

**21-second clips:**
- Professional Mode: ~150 credits = ~$1.85/video
- With Audio: ~210 credits = ~$2.59/video

**60-second clips:**
- Professional Mode: ~420+ credits = ~$5.18+/video
- With Audio: ~600+ credits = ~$7.40+/video

*Note: These per-video costs are my calculations from the source data. The source itself provides the following explicit per-video costs only after failure-rate adjustment (see below).*

### Failure-Adjusted Cost Per Video (from source)

At 50% success rate assumption:
- Pro plan ($37/month, 3,000 credits, ~21 usable 10s videos): **$1.76/video** [CLAIMED]
- Premier plan ($92/month, 8,000 credits, ~57 usable 10s videos): **$1.61/video** [CLAIMED]
- Worse styles (unspecified): **$2.50-4.00/video** [CLAIMED]

---

## MONTHLY PRODUCTION CAPACITY

### Theoretical Capacity (ignoring failures)

*Calculated from 5s Professional Mode at 35 credits each:*

| Tier | Credits | 5s Pro Videos (theoretical) | 10s Pro Videos (theoretical) |
|------|---------|----------------------------|------------------------------|
| Free | 66/day (~2,000/mo) | ~57/month | ~28/month |
| Standard | 660 | ~19 | ~9 |
| Pro | 3,000 | ~85 | ~42 |
| Premier | 8,000 | ~228 | ~114 |
| Ultra | 26,000 | ~742 | ~371 |

**Confidence:** These match the source's stated ranges (e.g., Pro: 42-85 videos for 5s). The range in the source table (42-85) appears to span Standard-to-Professional mode costs.

### Realistic Capacity (50% success rate)

Explicitly stated in source for 10-second Professional Mode:
- Pro (3,000 credits): 3,000 / 70 = ~42 theoretical, ~21 usable [CLAIMED]
- Premier (8,000 credits): 8,000 / 70 = ~114 theoretical, ~57 usable [CLAIMED]

### Worked Example from Source (25 videos/month, 10s Professional)

| Factor | Calculation |
|--------|-------------|
| Base credits needed | 25 videos x 70 credits = 1,750 credits |
| Success rate adjustment (50%) | 1,750 x 2 = 3,500 credits |
| Stylized content adjustment | Add 1.5x = 5,250 credits |
| Recommended plan | Premier ($65-92/mo) or Pro with credit packs |

[CLAIMED -- the "1.5x" stylized adjustment stacks multiplicatively on top of the 2x success rate adjustment, giving an effective 3x multiplier for stylized content.]

---

## REAL USER COST REPORTS

### Diana D (Trustpilot)
- Spent: **$125 USD** attempting to create a single short commercial [CLAIMED -- Trustpilot review]
- Issue: "The system kept adding extra, unprompted characters... Every time it happened, I had to re-render the scene -- and each retry cost more credits."
- Source: Trustpilot (no direct URL provided in document)

### DecencyOma Okafor (Trustpilot)
- Paid: **$6** for monthly Standard plan [CLAIMED -- Trustpilot review]
- Advertised: 660 credits, "about 33 videos" [CLAIMED -- their understanding of marketing]
- Actual: Each video cost **50 credits**, yielding only **~12 videos, not 33** [CLAIMED]
- Source: Trustpilot (no direct URL provided)

### DrBentman (AI filmmaking forum, unspecified)
- Plan: Premier [CLAIMED]
- Quote: "A 10-second video can cost about 70 credits. So you get a little over 100 generations with the [Premier] plan."
- Note: "When I'm working on a real project and not messing around, I eat up credits like candy." [CLAIMED]
- Source: AI filmmaking forum (no direct URL provided)

### InCauda Venenum (Trustpilot)
- Lost: **7,000 credits** when switching between tiers [CLAIMED -- Trustpilot review]
- Quote: "My remaining credits were reset to zero with no on-screen warning."
- Source: Trustpilot (no direct URL provided)

### Reddit Consensus (cited "across multiple analysis sites")
- Quote: "Kling is the best value for low-to-medium volume creators. If you make 5-20 videos per month... it's your top pick. For everything else, Runway."
- Recommended plan: Pro at **$37/month** for 5-20 videos/month [CLAIMED]
- Source: Reddit (no specific subreddit or URL provided)

### Max-Productive.ai
- Report: "User reports consistently describe scenarios where thousands of credits are consumed without producing a single usable video." [CLAIMED]
- Source: Max-Productive.ai (no direct URL provided)

---

## HIDDEN COSTS & GOTCHAS

### 1. Credit Expiration Traps
- Free tier: credits expire daily, zero rollover [CLAIMED]
- Paid tiers: "supposedly roll over" but users report credits vanishing unexpectedly [CLAIMED]
- InCauda Venenum case: 7,000 credits lost on tier switch with no on-screen warning [CLAIMED -- Trustpilot]

### 2. Failed Generations Consume Full Credits
- No refunds for failed generations [CLAIMED]
- "99% freeze bug": videos halt at 99% completion, consuming credits without producing output [CLAIMED]
- Max-Productive.ai reports thousands of credits consumed without single usable video [CLAIMED]

### 3. Time Costs
- Free tier: 8-12 minutes average generation time, up to 3+ hours during peak [CLAIMED]
- Paid tiers: 2-4 minutes per attempt average [CLAIMED]
- With 3-5 attempts per usable video: single short clip can consume 15-30 minutes of waiting [CLAIMED]

### 4. Customer Support
- Trustpilot rating for support: **1.0/10** [CLAIMED]
- Reported issues: inability to cancel subscriptions, double billing, no response to credit loss complaints [CLAIMED]
- Overall Trustpilot rating: **1.3/5** from **189 reviews** [CLAIMED -- stated in opening paragraph]

### 5. Model Complexity Limits
- Kling 1.6 and 2.5 Turbo models have "tighter complexity limits" [CLAIMED]
- Fail more often on prompts with 4+ distinct elements [CLAIMED]

---

## SUCCESS RATE / TAKES PER USABLE VIDEO

### Overall Success Rate
- **33-50% usable output** on first attempts [CLAIMED]
- Budget recommendation: **2-3x listed credit costs** for realistic planning [CLAIMED]

### Style-Specific Performance

| Content Style | Performance Score | Expected Success Rate | True Cost Multiplier |
|--------------|-------------------|----------------------|---------------------|
| Vintage/Film Noir | 4.9/5 | ~90% first-try usable | 1.1x |
| 3D Game Cinematics | 4.9/5 | ~90% first-try usable | 1.1x |
| Cinematic Photorealistic | 4.8/5 | ~85-90% first-try | 1.2x |
| Sci-fi | 3.8/5 | ~60-70% first-try | 1.5-1.7x |
| Vector Animations | 3.5/5 | ~50-60% first-try | 1.7-2x |
| Retro Anime | 3.2/5 | ~40-50% first-try | 2-2.5x |
| **Pixar-Style Animation** | **2.5/5** | **~30-40% first-try** | **2.5-3.3x** |

**Confidence:** All values are CLAIMED. The source does not cite where the performance scores (x/5) originate. No methodology described for the success rate percentages or the cost multipliers.

### Stylized Content Warning
- For stylized 3D, claymation-style content: budget **3-5x listed credit costs** [CLAIMED]
- Known issues with anime, Pixar-style, and claymation: flickering, color oversaturation, consistency issues [CLAIMED]

### Common Failure Modes
- Random mid-video scene switching: ~10% of attempts [CLAIMED]
- Character morphing during animation [CLAIMED -- no percentage given]
- Physics failures in complex movements [CLAIMED -- no percentage given]
- Hand/eye artifacts in close-ups [CLAIMED -- no percentage given]

---

## CHARACTER CONSISTENCY (Elements)

### Feature Details
- **Elements feature** included in all plans [CLAIMED]
- Allows up to **4 reference images** for maintaining character appearance across generations [CLAIMED]
- **No additional credit charge** for using Elements -- consumes standard video generation credits [CLAIMED]

### Reliability
- Complex multi-character scenes with Elements enabled have **higher failure rates** [CLAIMED]
- This effectively increases costs through wasted attempts [CLAIMED]
- No specific percentage given for the increased failure rate [UNCERTAINTY]

### User Assessment
- Source's conclusion section calls Elements "superior" compared to alternatives [CLAIMED]
- No specific user testimonials about Elements success/failure rates included

---

## AUDIO GENERATION

### Kling 2.6 Native Audio
- Audio generation is **bundled** via Kling 2.6 model, not a separate feature fee [CLAIMED]
- Included capabilities: dialogue, sound effects, ambient audio [CLAIMED]
- Credit cost premium:
  - 10-second video WITH audio: **100 credits** [CLAIMED]
  - 10-second video WITHOUT audio: **30-70 credits** [CLAIMED -- note this range is wider than the table's "70 credits" for Professional Mode, suggesting it includes Standard Mode]

### Lip Sync (Standalone Feature)
- Cost: approximately **10 credits per 10 seconds** of processed video [CLAIMED]

### Quality Assessment
- No quality assessment of audio output is provided in the document [UNCERTAINTY]

---

## KEY NUMBERS (Quick Reference)

- Trustpilot rating: **1.3/5** from **189 reviews** [CLAIMED]
- Trustpilot support rating: **1.0/10** [CLAIMED]
- Overall success rate: **33-50%** first-try usable [CLAIMED]
- True cost multiplier (standard content): **2x** listed price [CLAIMED]
- True cost multiplier (stylized content): **3-5x** listed price [CLAIMED]
- Pro plan: **$25.99-37/month**, **3,000 credits** [CLAIMED]
- Premier plan: **$64.99-92/month**, **8,000 credits** [CLAIMED]
- 10s Professional Mode video: **70 credits** [CLAIMED]
- 10s video with audio (Kling 2.6): **100 credits** [CLAIMED]
- Effective cost per usable 10s video (Pro, 50% success): **$1.76** [CLAIMED]
- Effective cost per usable 10s video (Premier, 50% success): **$1.61** [CLAIMED]
- Free tier queue wait: up to **3+ hours** peak [CLAIMED]
- Paid tier generation time: **2-4 minutes** per attempt [CLAIMED]
- Real user single-project spend: **$125** for one short commercial (Diana D) [CLAIMED -- Trustpilot]
- Runway alternative: **$95/month unlimited** [CLAIMED]
- Luma AI alternative: **$29.99 for 10,000 credits** [CLAIMED]
- Credit rollover limit: **20%** of unused, valid **2 years** [CLAIMED]
- Elements: up to **4 reference images**, no extra credit cost [CLAIMED]
- Max video length via extensions: **3 minutes** [CLAIMED]
- Prompt recommendation: under **40-50 words**, **4 or fewer** distinct elements [CLAIMED]
- True cost formula: Listed credit cost x 2 (standard) or x 3-5 (stylized) [CLAIMED]
- "A creator budgeting $50/month should plan for $25 worth of usable output." [CLAIMED]

---

## CONTRADICTIONS & UNCERTAINTIES

### 1. Price Range Ambiguity
The source gives price ranges for every tier (e.g., Standard: $6.99-10, Pro: $25.99-37, Premier: $64.99-92) without explaining whether the variation is regional, historical, or represents different billing cycles. The annual prices are single-point estimates (~$6.60, ~$24.42, ~$60.72) which should mathematically derive from the monthly price, but the ranges make verification impossible.

### 2. Standard Mode Credit Range
Standard Mode for 5 seconds is listed as "10-20 credits" -- a 2x range for the same operation. No explanation for when it would be 10 vs 20. This propagates uncertainty through all capacity calculations.

### 3. 5-Second Video Capacity vs Credit Math
The source's tier table says Pro yields "42-85" estimated 5s Pro videos. At 35 credits per 5s Professional Mode video: 3,000 / 35 = 85.7 (matches upper bound). But the lower bound of 42 implies 3,000 / 42 = ~71 credits per video, which doesn't match any listed credit cost. The range likely spans Standard (10-20 credits) to Professional (35 credits), but this is not stated.

### 4. Audio Credit Cost Inconsistency
The credits table says 10s Professional Mode = 70 credits. The audio section says "10-second video-only costs 30-70 credits." The low end (30 credits) doesn't match any entry in the table -- it's below even the Standard Mode 10s cost of 20-40 credits. Possible that the "30-70" range spans Standard through Professional mode, but this creates confusion.

### 5. 60-Second Video Credit Range
Table says 60s Professional Mode costs "~420+ credits" but the text says "400-600 credits." These ranges overlap but are not identical. The text figure may include extension overhead while the table is theoretical.

### 6. Success Rate Source Unattributed
The 33-50% overall success rate is stated as fact ("Research indicates") but no specific source is cited. The style-specific performance scores (e.g., 4.9/5 for Film Noir, 2.5/5 for Pixar) have no attribution -- unclear if these are from a review site, user survey, or author's assessment.

### 7. DecencyOma's Math
User claims 50 credits per video on Standard plan. The credits table shows 5s Standard Mode at 10-20 credits and 5s Professional Mode at 35 credits. 50 credits corresponds to 5s With Native Audio. Either the user was generating audio-enabled videos (more expensive than expected) or the pricing has changed since the table was compiled.

### 8. Trustpilot Data Currency
189 reviews and 1.3/5 rating are stated but not dated. Trustpilot ratings can change rapidly with new reviews. Individual testimonials (Diana D, DecencyOma, InCauda Venenum) are undated within the document.

### 9. Competitor Pricing Lacks Depth
Runway at $95/month "unlimited" and Luma AI at $29.99 for 10,000 credits are mentioned once each in the conclusion without detailed comparison. The "unlimited" claim for Runway is qualified only with "per-generation throttling" -- no details on what throttling means in practice.

### 10. Ultra Tier Thinly Sourced
Ultra tier (~$180/month, ~$119 annual, 26,000 credits) uses approximate markers on every data point, suggesting this tier may be newer or less commonly discussed in user reports.

---

## SOURCE URLS

The document references the following sources by name but provides **zero direct URLs**:

| Source | Context | Type |
|--------|---------|------|
| Trustpilot | Overall rating 1.3/5, 189 reviews; individual reviews from Diana D, DecencyOma Okafor, InCauda Venenum | Review platform |
| Reddit | Community consensus on value positioning, cited "across multiple analysis sites" | Forum |
| Max-Productive.ai | Report on credit consumption without usable output | Analysis site |
| AI filmmaking forum (unspecified) | DrBentman user testimonial about Premier plan usage | Forum |
| "Creator reviews from late 2025 through early 2026" | General timeframe for data gathering | Multiple sources |

**No direct URLs are provided anywhere in the source document.** All source attribution is by platform name or username only. This significantly limits verifiability of all CLAIMED data points.
