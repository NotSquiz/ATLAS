# 5A: AI Content Policy -- Extracted Data

**Source:** `/docs/research/bb-content-production/results/5A.md`
**Extraction Date:** 2026-02-01
**Source Title:** "AI content policies for Montessori parenting creators in 2026"
**Scope:** TikTok, Instagram, YouTube, Facebook policy analysis for stylized/illustrated AI content

---

## TIKTOK

### Synthetic Media Policy (exact text/summary)

**Exact quoted policy language (from support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content, dated 2025):**

> "We encourage creators to label content that has been either completely generated or significantly edited by AI... We also require creators to label all AI-generated content that contains realistic images, audio, and video."

**Key distinction:** Policy only mandates labeling for content that "could mislead viewers about reality." [VERIFIED -- direct quote attributed to TikTok support page]

**TikTok Creator Academy exemptions:** "Obviously cartoony AI edits" and "AI-generated art or animations" are explicitly exempt from mandatory labeling. [VERIFIED -- attributed to Creator Academy]

### Enforcement Statistics (latest numbers)

| Metric | Value | Period | Confidence |
|--------|-------|--------|------------|
| Policy-violating AIGC removals | <25,000 | H1 2025 | VERIFIED (TikTok transparency report) |
| Change from prior period | -53% decrease | H1 2025 vs prior | VERIFIED |
| Creator-labeled AI videos | 8.7 million | H1 2025 (36% growth) | VERIFIED |
| Auto-labeled AI content | ~5.5 million | H1 2025 (81% growth) | VERIFIED |
| Removals (alternate figure) | 51,618 | H2 2025 | CLAIMED (Napolify, Nov 2025; different categorization method noted) |

**Note:** The 51,618 and <25,000 figures are from different periods and different categorization methods. Source explicitly flags this discrepancy.

### Stylized/Animated AI Content Exemption

- **Explicitly exempt: YES**
- Exact policy language: Mandatory labeling applies only to "realistic images, audio, and video." Labeling is "encouraged" but not required for stylized content.
- Creator Academy explicitly exempts "obviously cartoony AI edits" and "AI-generated art or animations."
- Confidence: **VERIFIED** -- direct attribution to TikTok policy pages

### Creator Rewards Program

- **AI content eligible: NO**
- Current rules: Program "explicitly requires content 'filmed, designed, and produced entirely by yourself.'" [VERIFIED -- attributed to program terms]
- Third-party confirmation: Napolify (November 2025) confirms "TikTok explicitly prohibits monetization of AI-generated content through its Creator Rewards Program." [VERIFIED -- attributed to Napolify]
- Virtual influencers: Completely excluded. [VERIFIED]
- **Practical impact:** AI creators must rely on brand sponsorships, product sales, or external revenue streams. No platform-based monetization path.

### C2PA Metadata

- **Auto-detection behavior:** Confirmed active since May 2024. TikTok automatically detects metadata from:
  - OpenAI DALL-E 3 [VERIFIED]
  - Microsoft Bing Image Creator [VERIFIED]
  - Adobe Firefly [VERIFIED]
- **MidJourney C2PA status: NOT IMPLEMENTED.** MidJourney does NOT embed C2PA Content Credentials. MidJourney-generated content does NOT trigger TikTok's automatic labeling system. [VERIFIED -- explicitly stated]
- **Auto-labeling behavior:** Content with detected C2PA metadata gets automatic AI label. Without C2PA (e.g., MidJourney), no automatic label is applied.
- **Invisible watermarking:** As of November 24, 2025, TikTok began testing invisible watermarking for content created with C2PA credentials. [CLAIMED -- date-specific, attributed but testing status may have changed]

### 2026 Policy Changes

- January 22, 2026 Terms of Service changes related to U.S. ownership restructuring. No major AI-specific policy announcements. [VERIFIED -- specific date provided]
- November 2025 feature: Users can now see "less" or "more" AI-generated content in For You feeds. Creates potential reach implications for AI creators. [VERIFIED]
- No other 2026-specific AI policy updates documented. [NOTE: absence of evidence, not evidence of absence]

### TikTok Engagement Benchmarks

| Metric | Value | Period | Confidence |
|--------|-------|--------|------------|
| Average engagement rate | 4.90% | H1 2025 | VERIFIED |
| Small accounts (<100K followers) engagement | 7.50% | H1 2025 | VERIFIED |

---

## INSTAGRAM / META

### "AI Info" Label Policy

**Official policy source:** about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/ (updated October 23, 2025)

**Mandatory disclosure threshold:** Only for "photorealistic video or realistic-sounding audio" that was digitally created or altered. [VERIFIED -- attributed to official Meta policy page]

**Exact quoted exception:**

> "This requirement does not apply to images."

[VERIFIED -- direct quote from Meta help center at meta.com/help/artificial-intelligence/1783222608822690/]

**Stylized content exemption (from SEM Consultants UK):** "Labelling wouldn't be required if, for example, a reel of a forest was created in the style of a cartoon as this would not be a realistic depiction." [VERIFIED -- attributed to SEM Consultants UK documentation of Meta policy]

### C2PA Auto-Labeling from MidJourney

- Nick Clegg (Meta's President of Global Affairs) stated Meta built "industry-leading tools" to identify metadata from: Google, OpenAI, Microsoft, Adobe, **MidJourney**, and Shutterstock. [VERIFIED -- attributed to Nick Clegg]
- When C2PA metadata is detected, Instagram and Facebook automatically display the "AI Info" label -- **even on stylized content.** [VERIFIED]
- **Critical distinction:** Mandatory disclosure is NOT required for stylized content, but automatic labeling MAY occur anyway if C2PA metadata is present. [VERIFIED]
- **Contradiction note:** MidJourney is listed by Meta as a detected source, but the TikTok section states "MidJourney has NOT implemented C2PA Content Credentials." If MidJourney does not embed C2PA, Meta's detection of MidJourney metadata would require a different mechanism than C2PA, or MidJourney may have implemented C2PA for Meta's system specifically. **This is a potential CONTRADICTION or ambiguity in the source.**

### Algorithm Impact of AI Labels

**Suppression evidence:**
- Napolify (July 2025): Reports engagement penalties "up to 80% for purely AI-generated posts" and "60-80% reduction in visibility" for deepfake-style content. [CLAIMED -- third-party source, conflicts with official position]

**Neutral evidence:**
- Meta's official position (via Razorfish analysis): "There's no impact on organic reach from an algorithmic perspective just because of the label." [VERIFIED -- attributed to official Meta/Razorfish analysis]

**Source weighting note:** The document recommends the official position be weighted more heavily but flags the discrepancy for monitoring. The Napolify figures may conflate algorithm suppression with user behavioral response to labels.

### Stripping C2PA Metadata

- **Against ToS: NO** (not explicitly prohibited)
- Meta has acknowledged "there are ways that people can strip out invisible markers." [VERIFIED -- direct attribution to Meta]
- No documented enforcement actions exist for metadata removal alone. [VERIFIED -- stated as absence of evidence]
- The primary violation risk is failing to disclose photorealistic video or realistic audio when required -- not metadata management practices. [VERIFIED -- analytical conclusion from policy reading]
- **Practical methods cited:** "Save for Web" or utilities like ExifTool can remove C2PA data. [VERIFIED]
- **Source recommendation:** Stripping metadata "carries some policy risk and undermines the transparency strategy." [CLAIMED -- editorial assessment, not policy statement]

### Instagram Engagement Benchmarks

| Metric | Value | Period | Confidence |
|--------|-------|--------|------------|
| Median engagement rate | 0.43% | 2024 | VERIFIED |
| Reels engagement | 0.50% | 2024 | VERIFIED |
| Carousels engagement | 0.55% | 2024 | VERIFIED |
| TikTok vs Instagram ratio | ~5x higher on TikTok | 2024-2025 | VERIFIED |

---

## YOUTUBE

### Shorts AI Disclosure Requirements

**Official policy source:** support.google.com/youtube/answer/14328491

**Mandatory disclosure threshold:** Only when content is "meaningfully altered or synthetically generated when it seems realistic." [VERIFIED -- attributed to YouTube support page]

**Explicit exemptions (no disclosure required):**
1. "Clearly unrealistic content, such as animation" [VERIFIED]
2. Green screen effects depicting fantasy scenarios [VERIFIED]
3. "Production assistance, like using generative AI tools to create or improve a video outline, script, thumbnail, title, or infographic" [VERIFIED]
4. Caption creation and video upscaling [VERIFIED]

**Disclosure label placement:** Appears in the expanded description field. Sensitive topics (health, news, elections, finance) receive more prominent player-level labels. [VERIFIED]

**For illustrated Montessori content: No disclosure required under current policy.** [VERIFIED -- analytical conclusion]

### "Made for Kids" + AI Content Interaction

- Made for Kids designation operates **independently** from AI policies. [VERIFIED]
- No specific interaction rules exist between Made for Kids and AI disclosure. [VERIFIED]
- YouTube quality principles for kids' content (support.google.com/youtube/answer/10774223) warn against content that is "hard to follow... often the result of mass production or autogeneration." [VERIFIED -- direct quote]
- This warning applies to **how content is made** (quality), not whether AI was involved (tool). [VERIFIED -- analytical interpretation]
- Educational Montessori content with clear storylines, defined educational value, and quality production complies regardless of AI assistance. [CLAIMED -- editorial assessment]

### Monetization Eligibility

- **Current policy:** AI-generated content is NOT banned. YouTube bans "mass-produced or repetitive content... easily replicable at scale." [VERIFIED]
- **July 15, 2025 policy update:** Renamed "repetitious content" to "inauthentic content." [VERIFIED -- specific date]
- **CEO Neal Mohan (January 21, 2026 letter):** "AI will remain a tool for expression, not a replacement." [VERIFIED -- attributed with specific date]
- **Key monetization requirements:**
  1. Content must be original and authentic [VERIFIED]
  2. Each video must differ substantively from others [VERIFIED]
  3. Content must provide educational or entertainment value [VERIFIED]
  4. Template-based production is prohibited [VERIFIED]
- **Critical quote:** "Disclosing content as altered or synthetic won't limit a video's audience or impact its eligibility to earn money." [VERIFIED -- direct quote attributed to YouTube]
- **Over 1 million channels** used YouTube's AI creation tools daily in December 2025. [CLAIMED -- attributed but not to specific source]

### "Meaningful human creative contribution" definition

- **NOT an official YouTube phrase.** [VERIFIED -- explicitly stated in source]
- Monetization policies describe equivalent requirements: originality, variation across videos, educational/entertainment value, and authentic voice. [VERIFIED]

### Shorts-Specific Rules

- Same disclosure rules as long-form YouTube content. No Shorts-specific AI disclosure variations documented. [VERIFIED]
- Disclosure label appears in expanded description field. [VERIFIED]

### YouTube Trust Impact

- YouTube internal research indicates the "altered or synthetic" banner "modestly reduces CTR but increases trust metrics" among viewers aware of AI risks. [CLAIMED -- attributed to "YouTube's internal research" but no specific publication cited]

---

## FACEBOOK

### AI Content Policies

- Facebook AI content policies are **identical to Instagram's** -- Meta explicitly states policies apply uniformly across "Facebook, Instagram and Threads." [VERIFIED -- attributed to Meta]
- Same photorealistic video/realistic audio threshold applies. [VERIFIED]
- Stylized content: Exempt from mandatory disclosure. [VERIFIED]

### Algorithm Suppression Evidence

**Official denial:**
- Facebook VP of Product Jagjit Chawla stated: "AI-generated content will be treated the same as human-generated content, as long as its topic is considered interesting to the user." [VERIFIED -- attributed with name and title]

**What IS suppressed (regardless of AI involvement):**
- Unoriginal/copied content [VERIFIED]
- Mass-produced "AI slop" [VERIFIED]
- Content lacking originality [VERIFIED]
- Meta took action against 500,000 accounts in H1 2025 for "unoriginal content" -- targeting content farms, not legitimate AI creators with human oversight. [VERIFIED]

### Facebook Reels

- Follow the same rules as Instagram Reels. No platform-specific variations for AI content. [VERIFIED]

### Facebook Monetization

- Content Monetization Program launched August 31, 2025. [VERIFIED -- specific date]
- AI-generated videos meeting "original content" requirements are eligible. [VERIFIED]
- Educational content using AI illustrations qualifies if it provides genuine value. [CLAIMED -- editorial interpretation of policy]

---

## CROSS-PLATFORM: DISCLOSURE AS ADVANTAGE

### Evidence That Proactive Disclosure HELPS

**Case studies:**

1. **Deutsche Telekom "A Message from Ella" campaign:** Used AI to age a 9-year-old girl, warning parents about sharenting consequences. Described as "viral." [VERIFIED -- specific campaign cited]

2. **Assam Police #DontBeASharent campaign (July 2023):** Specifically used AI-generated images of children -- "deliberately practicing what they preached about not sharing real children's photos." Caption: "Children are not social media trophies." [VERIFIED -- specific campaign with date]

3. **Trusting News research (July 2025):** 94% of audiences want transparency around AI use. 87.2% said understanding WHY AI was used is important. This suggests the disclosure penalty can be mitigated by leading with purpose rather than process. [VERIFIED -- specific percentages attributed to named research]

4. **YouTube internal research:** "Altered or synthetic" banner "modestly reduces CTR but increases trust metrics" -- transparency may build long-term audience quality. [CLAIMED -- no specific publication]

### Evidence That Disclosure HURTS

**Case studies:**

1. **USC Marshall School of Business study (SSRN, May 2025), "Made with AI: Consumer Engagement with Social Media Containing AI Disclosures":** AIGC disclosures on TikTok reduce consumer engagement NOT through quality concerns, but by diminishing parasocial connection (one-sided emotional bonds). Disclosures "signal reduced effort from the creator." Key finding: "Disclosures that signal greater effort can mitigate engagement reductions." [VERIFIED -- specific institution, publication venue, date, and findings cited]

2. **13-experiment study in Organizational Behavior and Human Decision Processes (ScienceDirect, 2025), "The Transparency Dilemma":** Actors disclosing AI usage are trusted LESS than those who don't -- across different disclosure framings and whether voluntary or mandatory. Trust penalty is "attenuated but not eliminated" among evaluators with favorable technology attitudes. [VERIFIED -- specific journal, number of experiments, and title cited]

3. **Bynder 2024 study (n=2,000 UK/US):** When unaware of origin, 56% preferred AI-generated content. Once they suspected AI involvement, 52% reported becoming less engaged. 20% characterized brands using AI as "lazy." [VERIFIED -- specific sample size and percentages]

4. **Napolify (July 2025):** Up to 80% engagement penalty for purely AI-generated posts on Meta platforms, 60-80% reduction in visibility for deepfake-style content. [CLAIMED -- conflicts with Meta official position]

### Anti-Sharenting / Privacy-First Framing

- **Does it improve trust?**
  - Trusting News: 87.2% said understanding WHY AI was used matters -- privacy protection is a clear "why." [VERIFIED]
  - USC study: Disclosures signaling greater effort can mitigate engagement reductions -- privacy-first framing signals ethical intention/effort. [VERIFIED]
  - Deutsche Telekom + Assam Police campaigns provide successful precedent for AI + child privacy positioning. [VERIFIED]

- **Sharenting risk data:**
  - By 2030, nearly two-thirds of identity fraud cases affecting young people will result from sharenting (Adweek/Deutsche Telekom data). [CLAIMED -- specific prediction, sourcing chain unclear]
  - Average 5-year-old has approximately 1,500 pictures uploaded without consent. [CLAIMED -- widely cited but original source not specified]
  - Human Rights Watch research on LAION-5B: Children's personal photos are being used to train AI models and create deepfakes without consent. [VERIFIED -- attributed to Human Rights Watch]

- **First-mover opportunity:** "No case studies exist of Montessori or parenting influencers using AI-generated content specifically for child privacy protection." [VERIFIED -- stated as absence of evidence]
  - Top Montessori accounts cited: @motherhood.and.montessori (674K followers), @followyourchild (414K followers) -- both rely entirely on real-life family content. [VERIFIED -- specific accounts and follower counts]

---

## RECOMMENDED DISCLOSURE STRATEGY

(What the research suggests)

1. **Stylized/illustrated AI content does NOT require mandatory disclosure on any of the four platforms.** All platforms distinguish between photorealistic (mandatory) and stylized (exempt). [VERIFIED across all four platform analyses]

2. **Lead with privacy rationale, not AI process.** Recommended framing: "These illustrations are AI-created to protect my children's privacy and digital future while sharing our Montessori journey." [CLAIMED -- editorial recommendation based on research synthesis]

3. **Rationale for proactive disclosure despite exemption:**
   - Signals effort and ethical intention (USC study shows this mitigates engagement penalties) [VERIFIED]
   - 94% of audiences want transparency; 87.2% want to understand WHY (Trusting News) [VERIFIED]
   - Builds long-term trust even if short-term CTR dips (YouTube internal research) [CLAIMED]
   - Privacy-first positioning is a potential first-mover competitive advantage [CLAIMED -- editorial]

4. **MidJourney is the recommended tool for minimizing auto-detection:** MidJourney does not embed C2PA metadata, so content will not trigger automatic AI labels on TikTok or Meta platforms. [VERIFIED]

5. **Metadata stripping is not prohibited but not recommended:** Undermines the transparency strategy and carries some policy risk. [CLAIMED -- editorial assessment]

6. **Australian context:** No Australia-specific AI disclosure regulations beyond platform-level policies. TikTok's social media ban for under-16s (effective 2025) may affect target audience composition. [VERIFIED]

---

## KEY RULES (Quick Reference)

### TikTok
| Rule | Status |
|------|--------|
| **MUST:** Label realistic AI images/video/audio | Mandatory |
| **MUST NOT:** Claim AI content for Creator Rewards monetization | Prohibited |
| **CAN:** Post stylized/illustrated AI content without label | Permitted |
| **SHOULD:** Consider user preference filter impact on reach | Advisory |

### Instagram
| Rule | Status |
|------|--------|
| **MUST:** Disclose photorealistic AI video or realistic AI audio | Mandatory |
| **MUST NOT:** n/a for stylized content | -- |
| **CAN:** Post stylized AI images/video without mandatory disclosure | Permitted |
| **BEWARE:** C2PA metadata triggers automatic "AI Info" label even on stylized content | Auto-enforcement |

### YouTube
| Rule | Status |
|------|--------|
| **MUST:** Disclose realistic-looking AI-generated/altered content | Mandatory |
| **MUST NOT:** Mass-produce template-based repetitive content | Prohibited (demonetization risk) |
| **CAN:** Post stylized/animated AI content without disclosure | Permitted |
| **CAN:** Use AI for scripts, thumbnails, outlines, captions without disclosure | Permitted |
| **CAN:** Monetize original, varied AI-assisted content | Permitted |

### Facebook
| Rule | Status |
|------|--------|
| **MUST:** Disclose photorealistic AI video or realistic AI audio | Mandatory (same as Instagram) |
| **MUST NOT:** n/a for stylized content | -- |
| **CAN:** Post stylized AI content without mandatory disclosure | Permitted |
| **CAN:** Monetize via Content Monetization Program if original | Permitted |
| **BEWARE:** C2PA metadata triggers automatic "AI Info" label (same as Instagram) | Auto-enforcement |

---

## CONTRADICTIONS & UNCERTAINTIES

### CONTRADICTION 1: Meta C2PA Detection vs MidJourney C2PA Status
- **Claim A (TikTok section):** "MidJourney has NOT implemented C2PA Content Credentials."
- **Claim B (Instagram section):** Nick Clegg states Meta detects metadata from MidJourney (among others).
- **Analysis:** If MidJourney does not embed C2PA, Meta cannot detect MidJourney content via C2PA. Either (a) MidJourney implemented some other form of metadata, (b) Meta uses non-C2PA detection for MidJourney, (c) MidJourney implemented C2PA after the TikTok data point, or (d) Meta's claim is aspirational. **UNRESOLVED.**

### CONTRADICTION 2: Meta Algorithm Suppression
- **Official position (Meta/Razorfish):** "No impact on organic reach from an algorithmic perspective just because of the label."
- **Third-party claim (Napolify, July 2025):** "Up to 80% engagement penalty" and "60-80% reduction in visibility."
- **Analysis:** The Napolify figures may measure user behavioral response to labels (not algorithm suppression), or may measure deepfake-style content which IS suppressed by Meta's quality systems. The discrepancy could be measurement methodology, content type conflation, or genuine contradiction. **UNRESOLVED.** Source weights official position higher.

### CONTRADICTION 3: TikTok Removal Statistics
- **H1 2025 transparency report:** <25,000 removals
- **Napolify November 2025:** 51,618 removals
- **Analysis:** Source attributes discrepancy to different periods (H1 vs H2 2025) and different categorization methods. Not necessarily contradictory but not reconciled. **PARTIALLY RESOLVED.**

### UNCERTAINTY 1: "Meaningful Human Creative Contribution"
- Source explicitly states this is NOT an official YouTube phrase, yet the concept is implied by monetization requirements (originality, variation, value, authentic voice). No formal definition or test exists. **UNCERTAIN** how YouTube would evaluate edge cases.

### UNCERTAINTY 2: YouTube Internal Research on Trust
- "Modestly reduces CTR but increases trust metrics" attributed to "YouTube's internal research" but no specific publication, blog post, or date is cited. **UNVERIFIABLE** from this source alone.

### UNCERTAINTY 3: Long-Term Policy Direction
- All current exemptions for stylized content could change. No platform has committed to maintaining these exemptions permanently. The November 2025 TikTok user preference feature (see more/less AI content) suggests platforms are actively iterating. **UNCERTAIN.**

### UNCERTAINTY 4: Australian Regulatory Environment
- "No Australia-specific AI disclosure regulations currently apply beyond platform-level policies." This could change given Australia's active stance on social media regulation (under-16 ban). **UNCERTAIN** for 2026+.

---

## SOURCE URLS (with official policy page links)

### Official Platform Policy Pages (cited in source)
1. **TikTok AI Content Policy:** support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content (dated 2025)
2. **Meta AI Labeling Approach:** about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/ (updated October 23, 2025)
3. **Meta AI Help Center:** meta.com/help/artificial-intelligence/1783222608822690/
4. **YouTube AI Disclosure:** support.google.com/youtube/answer/14328491
5. **YouTube Kids Content Quality:** support.google.com/youtube/answer/10774223

### Research Papers / Studies (cited in source)
6. **USC Marshall "Made with AI" study:** SSRN, May 2025
7. **"The Transparency Dilemma":** Organizational Behavior and Human Decision Processes (ScienceDirect), 2025 -- 13 experiments
8. **Bynder 2024 study:** n=2,000 UK/US participants
9. **Trusting News research:** July 2025

### Third-Party Analysis (cited in source)
10. **Napolify:** November 2025 (TikTok enforcement); July 2025 (Meta engagement penalties)
11. **SEM Consultants UK:** Meta stylized content exemption documentation
12. **Razorfish:** Meta algorithm impact analysis
13. **Adweek / Deutsche Telekom:** Sharenting identity fraud projection (2030)
14. **Human Rights Watch:** LAION-5B children's photo research

### Campaign References (cited in source)
15. **Deutsche Telekom "A Message from Ella"** -- AI aging for anti-sharenting
16. **Assam Police #DontBeASharent** -- July 2023, AI-generated children's images

### Platform Announcements (cited in source)
17. **TikTok C2PA expansion:** May 2024
18. **TikTok invisible watermarking test:** November 24, 2025
19. **TikTok ToS U.S. restructuring:** January 22, 2026
20. **YouTube "inauthentic content" rename:** July 15, 2025
21. **Neal Mohan CEO letter:** January 21, 2026
22. **Facebook Content Monetization Program launch:** August 31, 2025

---

## SUMMARY STRATEGY TABLE (from source)

| Platform | Mandatory Disclosure | Auto-Detection Risk | Monetization Path |
|----------|---------------------|---------------------|-------------------|
| TikTok | Not required (stylized) | MidJourney: No / Adobe: Yes | Brand deals only (Creator Rewards excludes AI) |
| Instagram | Not required (stylized) | High if C2PA metadata present | Standard monetization eligible |
| YouTube Shorts | Not required (stylized) | Low for stylized content | Eligible if original and varied |
| Facebook | Not required (stylized) | High if C2PA metadata present | Content Monetization Program eligible |

**Bottom line from source:** The policy landscape is favorable for stylized/illustrated AI content depicting Montessori parenting education. Privacy-first positioning offers potential competitive differentiation while aligning AI disclosure with audience values rather than presenting it as a liability.
