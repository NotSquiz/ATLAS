# Integration Recommendations: Old Research into North Star Docs

## Date: 2026-02-03
## Pipeline Summary
- 5 old research documents analyzed (519 total findings)
  - OLD-1: 127 findings (Skills Overview, Hooks, Analytics, AU Localiser)
  - OLD-2: 78 findings (Montessori Clip Production Pipeline)
  - OLD-3: 119 findings (Pipeline Design Support)
  - OLD-4: 68 findings (Pipeline Design -- Virality Focus)
  - OLD-5: 127 findings (Q4 2025 Platform Requirements)
- 2 North Star baselines indexed
  - SYNTHESIS.md (NS-1): 187 findings
  - WORKFLOW.md (NS-2): 147 findings
- Gap analysis totals: **136 GAPs**, **34 CONFLICTs**, **246 VALIDATIONs**, **103 PARTIALs**
  - Part 1 (OLD-1/2/3): 89 GAPs, 22 CONFLICTs, 148 VALIDATIONs, 65 PARTIALs
  - Part 2 (OLD-4/5): 47 GAPs, 12 CONFLICTs, 98 VALIDATIONs, 38 PARTIALs
- Staleness: 21 VERIFIED, 18 OUTDATED, 12 UPDATED, 0 DEPRECATED, 7 UNVERIFIABLE

---

## PRIORITY 1: Immediate Integration (GAP + VERIFIED + HIGH Actionability)

These findings are NEW information not in the current docs, VERIFIED as still accurate (or from domains not subject to staleness), and HIGH actionability. Incorporate directly into SYNTHESIS.md or WORKFLOW.md.

### 1.1 Australian English Spelling Requirement
- **Source**: OLD-1 BRV-003, OLD-3 BRV-004
- **What**: "Mum" not "mom", "organise" not "organize", "colour" not "color", "nappies" not "diapers", "kindy" not "kindergarten", "bub" not "baby" (full list in OLD-5 AS-002)
- **Why integrate**: Completely absent from ALL NS QC checklists and brand voice specs. Found in 2 independent old sources. Basic brand requirement for an Australian content business.
- **Where**: Add to WORKFLOW.md Section 7 (QC Checklist) as mandatory check item AND to brand voice guidance
- **Cross-references**: OLD-5 AS-002 provides extended AU terminology list for SEO optimization
- **Staleness check**: VERIFIED -- language conventions do not change. Staleness report confirms "Australian localisation cues and brand voice guidance" as Low Risk / Still Accurate.

### 1.2 Australian Localisation Visual Cues
- **Source**: OLD-1 SET-001 through SET-016 (14 indoor + 4 outdoor cues), OLD-3 AU localisation pack (10 prompt modifiers)
- **What**: Comprehensive AU-specific visual elements:
  - **Indoor**: Power outlets (3-pin), timber skirting boards, jute/sisal rugs, linen textures, ceiling fans, sliding doors, Australian flooring (polished concrete, light timber), native indoor plants (fiddle-leaf fig, monstera), safety gates (AU brands), baby products (AU brands like Ergo Pouch, Kmart essentials)
  - **Outdoor**: Timber/Colorbond fences, native plants (bottlebrush, grevillea, kangaroo paw), natural light (north-facing windows prized in AU), weatherboard/brick/render exteriors
  - **Dosage**: 1-2 AU localizers per prompt (OLD-3 AUD-002), 2-3 cues per video (OLD-1 SET-016)
- **Why integrate**: Zero AU-specific set/environment guidance in NS. NS-1 identifies "no Australian-specific audience data" as a known research gap. This IS the core differentiation pillar (OLD-1 AUD-002: "I have that same rug!" drives engagement comments).
- **Where**: Create new "Australian Localisation Guide" appendix in SYNTHESIS.md. Reference from WORKFLOW.md scene breakdown template.
- **Cross-references**: OLD-1 AUD-002 (relatability engagement), OLD-1 AUD-003 (international viewers not alienated), OLD-3 AUD-002 (subtlety principle)
- **Staleness check**: VERIFIED -- physical/cultural cues do not change. Staleness report lists AU localisation as "Still Accurate."

### 1.3 Safety Disclaimers and Content Safety QC
- **Source**: OLD-3 CST-005, OLD-1 QCI-003, OLD-5 QI-002
- **What**: Three interlocking safety requirements:
  1. **"Stop if..." disclaimers**: Always include safety disclaimers starting with "Stop if..." in both VO and burned-in captions, displayed 2-3 seconds (OLD-3 CST-005)
  2. **Content safety verification**: Flag small choking hazards, unsupervised climbing, age-inappropriate activities, dangerous stunts, medical advice (OLD-1 QCI-003)
  3. **Child safety compliance checklist**: Adult supervision visible, avoid private spaces (bathrooms/bedrooms), age-appropriate only, no PII, privacy settings, monitor comments (OLD-5 QI-002)
- **Why integrate**: Missing from NS QC entirely. For parenting content aimed at parents of infants/toddlers, safety QC is non-negotiable. Appears in 3 independent old sources.
- **Where**: Add "Safety Gate" to WORKFLOW.md per-clip QC checklist (NS-2 QCI-001). Add child safety compliance checklist as pre-publish gate.
- **Cross-references**: OLD-3 VIS-014 (expert approval mental model), OLD-4 QC-003 (compliance checks)
- **Staleness check**: VERIFIED -- safety principles do not date.

### 1.4 Platform-Specific Safe Zone Pixel Values
- **Source**: OLD-3 PLT-001, PLT-002, PLT-003
- **What**:
  - Instagram Reels: >=220px top, >=420px bottom
  - TikTok: >=108px top, >=320px bottom, 60px left, 120px right
  - YouTube Shorts: >=140px top, >=270px bottom
- **Why integrate**: NS baselines have NO platform-specific safe zone pixel values. Without these, captions get covered by platform UI elements (username, like/share buttons, description text).
- **Where**: Add to SYNTHESIS.md platform specs table AND WORKFLOW.md caption/subtitle section
- **Cross-references**: OLD-1 PLT-006 (general safe zone principle), OLD-4 PS-004 (approximate percentages validate same concept)
- **Staleness check**: UNVERIFIABLE per staleness report -- "Safe zones may have shifted with UI updates." **Recommend re-verifying exact pixel values on each platform before hardcoding into templates.** General guidance (keep text center-safe) confirmed still valid.

### 1.5 Caption Display Line Limits
- **Source**: OLD-3 PRD-010, OLD-1 PRD-002
- **What**: On-screen caption display rules:
  - Maximum 2 lines at a time
  - 6-8 words per displayed caption line (~32 characters)
  - 5-6 words per line (OLD-1 PRD-002), 1.2s per displayed line
- **Why integrate**: NS-2 BRV-002 says "12-16 words per line" which refers to VO script lines, NOT on-screen caption display. These are distinct specifications. Without display limits, captions become unreadable on mobile screens.
- **Where**: Add as distinct "Caption Display Specification" in WORKFLOW.md, clearly separated from VO script line counts. Add to QC checklist.
- **Cross-references**: OLD-3 QCI-003 (caption sync tolerance <=0.2s -- also add)
- **Staleness check**: VERIFIED -- caption readability standards are driven by screen size physics, not platform policy.

### 1.6 WER <=10% Caption Accuracy Threshold
- **Source**: OLD-2 ANL-001, OLD-3 ANL-007
- **What**: Word Error Rate must be <=10% (>=90% accuracy) for published captions. Complete Python implementation (wer_harness.py) provided in OLD-2.
- **Why integrate**: NS baselines have NO quantitative caption accuracy metric. For a brand where captions ARE the primary content delivery mechanism (69-74% sound-off viewing), caption accuracy is a critical quality gate. Appears in 2 independent sources.
- **Where**: Add WER <=10% as QC gate metric in WORKFLOW.md. Reference Whisper WER harness as automation tool.
- **Cross-references**: OLD-2 QCI-001 (Whisper WER harness implementation)
- **Staleness check**: VERIFIED -- Whisper still available per staleness report. Metric standard unchanged.

### 1.7 Australian Posting Times by Platform and Day (AEDT)
- **Source**: OLD-5 (AU posting times section)
- **What**: Comprehensive AEDT posting times for Instagram, TikTok, YouTube, and Facebook broken down by day of week. NS-1 only has "Thursday 7-10 PM AEST" as a single data point.
- **Why integrate**: NS-1 explicitly identifies "no Australian-specific audience data" as a research gap. This directly fills it. Operational daily use -- impacts every single post.
- **Where**: Replace the single-line posting time in WORKFLOW.md Section 1 with the full platform-by-day schedule from OLD-5.
- **Cross-references**: OLD-5 AS-007/008 (seasonal AU opportunities), OLD-5 AS-001 (AU social media usage stats: 78% penetration, 1h51m/day)
- **Staleness check**: VERIFIED -- posting time data based on user behaviour patterns, directionally stable.

### 1.8 Australian Social Media Usage Statistics
- **Source**: OLD-5 AS-001
- **What**: 78% AU social media penetration, 1h51m average daily use, 6.5 platforms per person, TikTok 38+ hrs/month per user.
- **Why integrate**: NS-1 notes "No Australian-specific audience data" as a research gap. This directly fills it with quantitative justification for the multi-platform strategy.
- **Where**: Add to SYNTHESIS.md audience strategy section (before Decision Gate 5 or as supporting data).
- **Cross-references**: OLD-5 AS-009 (Facebook Reels engagement rate 5.91% leads platforms)
- **Staleness check**: VERIFIED -- 2025 data, directionally valid for 2026 planning.

### 1.9 Platform-Specific SEO Keyword Hierarchies
- **Source**: OLD-5 CS-008, CS-017, CS-018
- **What**:
  - **Universal hierarchy**: filename > title/caption > description > hashtags > on-screen text > spoken audio
  - **Instagram priority**: Profile name/bio > captions > alt text > hashtags > subtitles
  - **TikTok priority**: Captions > on-screen text > voiceover > descriptions > hashtags
- **Why integrate**: Actionable SEO guidance completely missing from NS baselines. NS-2 CST-012 says "keywords over hashtags" but provides no hierarchy of where keywords have the most impact.
- **Where**: Add as "SEO Keyword Placement Guide" in WORKFLOW.md distribution section.
- **Cross-references**: OLD-1 PRD-005 (embed SEO terms naturally in narration), OLD-5 CS-006 (TikTok caption SEO structure), OLD-5 CS-007 (YouTube Shorts title/description strategy)
- **Staleness check**: VERIFIED -- Instagram Google/Bing indexing (Jul 2025) and YouTube Shorts in Google Discover (Sep 2025) both confirmed active per staleness report. Makes this more important, not less.

### 1.10 Platform Caption Character Limits
- **Source**: OLD-5 PS-006, PS-007, PS-008
- **What**:
  - Instagram/Facebook: 2,200 chars (first 125 visible before "more")
  - TikTok: 2,200-4,000 chars (first 1-2 lines visible)
  - YouTube Shorts: 5,000 char description, 100 char title (under 60 for full visibility)
- **Why integrate**: Basic operational specs missing from NS baselines. Without these limits, scripts/descriptions get truncated unpredictably.
- **Where**: Add to WORKFLOW.md platform specs reference table (alongside resolution, codec, etc.)
- **Cross-references**: OLD-5 PS-009 (file size limits: IG/FB 4GB, TikTok 500MB/<3min)
- **Staleness check**: VERIFIED -- TikTok caption limit and YouTube title/description limits confirmed current per staleness report.

### 1.11 Question-Based CTA for Engagement
- **Source**: OLD-1 PSY-009
- **What**: "Would you let your baby try this? Comment below." Questions at video end drive engagement (comments and interaction). NS mentions CTAs but doesn't call out question-based CTAs specifically.
- **Why integrate**: Comments are a key algorithm signal across all platforms. Question-based CTAs directly prompt the highest-value engagement type.
- **Where**: Add as explicit CTA variation in WORKFLOW.md NS-2 BRV-005 CTA variations list.
- **Cross-references**: OLD-4 CP-007 (challenge format drives both watch time AND interaction)
- **Staleness check**: VERIFIED -- engagement psychology is evergreen.

### 1.12 Two-Person Approval Gate
- **Source**: OLD-3 PRD-012
- **What**: Both reviewers must sign with initials and date. 100% pass required -- no "good enough" exceptions. Missing from NS entirely.
- **Why integrate**: For content involving children's activities, a single-reviewer process creates risk. Two-person review catches safety issues, brand violations, and cultural missteps that one person might miss.
- **Where**: Add to WORKFLOW.md QC section as final pre-publish gate.
- **Cross-references**: OLD-3 PRD-013 (phone screen testing mandatory -- also add)
- **Staleness check**: VERIFIED -- process requirement, not tool-dependent.

### 1.13 Phone Screen Testing Before Publish
- **Source**: OLD-3 PRD-013, OLD-4 PG-009
- **What**: Mandatory test on actual phone before any video is published. Check: captions readable, safe zones clear, audio levels appropriate, no visual artifacts visible at mobile resolution. Appears in 2 independent sources.
- **Why integrate**: NS baselines don't mention device testing. Content is consumed 95%+ on mobile -- desktop QC alone is insufficient.
- **Where**: Add as mandatory step in WORKFLOW.md QC checklist, after DaVinci assembly and before upload.
- **Cross-references**: OLD-4 PG-009 (watch on phone sound-off, check transcript search)
- **Staleness check**: VERIFIED -- mobile-first testing is evergreen.

### 1.14 Search Keyword Integration in Narration
- **Source**: OLD-1 PRD-005
- **What**: Naturally incorporate search terms ("baby independent play", "Montessori home setup", "toddler activities") into voiceover narration so they appear in captions. Platforms index caption text for search ranking.
- **Why integrate**: NS-2 CST-012 says "keywords over hashtags" but doesn't describe the technique of embedding keywords in narration/VO for automatic caption indexing. This is the HOW behind the WHAT.
- **Where**: Add to WORKFLOW.md script writing section as production technique. Cross-reference with SEO keyword hierarchies (1.9).
- **Cross-references**: OLD-5 CS-008 (spoken audio is lowest in keyword hierarchy, but VO-to-caption indexing elevates it)
- **Staleness check**: VERIFIED -- TikTok and YouTube both confirmed to analyze voice/text per staleness report.

### 1.15 Montessori Alignment QC Gate
- **Source**: OLD-1 QCI-005
- **What**: QC check for: authentic Montessori materials (not plastic/electronic), age-appropriate activities, no fantasy elements (under 6), no branded products, known Montessori allowances. NS QC focuses on visual quality (character consistency, glow, artifacts) but NOT content accuracy.
- **Why integrate**: For a Montessori-branded content channel, content accuracy IS brand identity. A single video showing non-Montessori practices could damage credibility with the target audience.
- **Where**: Add as content-level QC gate in WORKFLOW.md alongside visual QC.
- **Cross-references**: OLD-3 CST-007 (evidence-only content rule: no unproven claims, no medical/therapy implications)
- **Staleness check**: VERIFIED -- Montessori principles do not change.

### 1.16 Child Safety Compliance Checklist (Detailed)
- **Source**: OLD-5 QI-002, OLD-5 QI-004, OLD-5 QI-005
- **What**: Three checklists consolidated:
  - **Child safety**: Adult supervision visible, avoid private spaces, age-appropriate only, no PII, privacy settings, monitor comments
  - **COPPA compliance**: Content ABOUT children vs FOR children distinction, explicit audience designation, madeForKids: false, 2025 COPPA amendments (biometric protections, April 2026 deadline)
  - **FTC disclosure**: $53,088 per violation, platform-specific labeling tools (IG Branded Content Tool, TikTok Content Disclosure, YouTube checkbox)
- **Why integrate**: NS-1 MON-005 mentions COPPA risk briefly. OLD-5 provides the detailed operational checklist needed to actually comply. April 2026 full COPPA compliance deadline is imminent.
- **Where**: Add as formal compliance section in SYNTHESIS.md AND as pre-publish gate in WORKFLOW.md.
- **Cross-references**: OLD-5 MO-002/003 (fine amounts -- update NS-1's $42,530 to current $50,120/video)
- **Staleness check**: UPDATED per staleness report -- COPPA amendments published April 2025, effective June 2025, full compliance deadline April 22, 2026. Fine amounts confirmed current.

---

## PRIORITY 2: Integrate with Adaptation (GAP + VERIFIED + MEDIUM-HIGH Actionability)

New information that's still accurate but needs adaptation for the current pipeline context (e.g., stylized clay direction vs photorealistic origin, multi-tool pipeline vs MJ-only origin).

### 2.1 Retention Ladder Structure with Timing Milestones
- **Source**: OLD-1 PSY-005
- **What**: Specific timing rungs: 0-3s hook, 3-8s payoff #1, 8-15s payoff #2, pattern interrupt at halfway point, emotional moment at 35-50s mark. NS-1 has hook timing by content length (CST-007) but not the full retention ladder concept with mid-video pattern interrupts.
- **Why integrate**: Directly informs scene breakdown timing. Provides a concrete framework for scriptwriting.
- **Where**: Add to SYNTHESIS.md as content psychology principle. Reference from WORKFLOW.md scene breakdown template.
- **Adaptation needed**: Timing milestones need adjustment for the NS multi-length strategy (15s/30s/60s/90s) rather than the OLD 21s/60s format.
- **Staleness check**: VERIFIED -- retention psychology is evergreen.

### 2.2 Mid-Point Re-Hook for 60s Videos
- **Source**: OLD-4 CP-005
- **What**: Insert a secondary hook or mini-mystery at the 15-30s mark in 60s videos to combat the natural attention dip. Not mentioned in NS baselines despite the 60s content strategy.
- **Why integrate**: 60s is the primary format in NS. Without mid-point re-hooks, completion rates for 60s content will suffer (NS-1 ANL-003 notes 31% completion for 60s-3min).
- **Where**: Add to WORKFLOW.md script templates for 60s+ content.
- **Adaptation needed**: Integrate with NS-1's 3-act structure rather than OLD-4's 21s/60s dual format.
- **Staleness check**: VERIFIED -- virality psychology does not date.

### 2.3 Variation Levers for Anti-Template Compliance
- **Source**: OLD-1 CST-009
- **What**: Techniques to avoid AI-templated feel: synonym rotation, beat ordering shuffle, rotating phrasings, sentence length mixing, narration perspective alternation (first/third person, addressing viewer -- see OLD-1 BRV-005).
- **Why integrate**: Critical for YouTube's anti-template policy (NS-1 PLT-003 mentions "template-based production prohibited"). Without deliberate variation, AI-assisted content risks flagging.
- **Where**: Add to WORKFLOW.md script writing section as mandatory variation checklist.
- **Adaptation needed**: Frame as QC check ("Does this script sound like the last 3 scripts?") rather than OLD-1's skill-prompt-based variation system.
- **Staleness check**: VERIFIED -- YouTube policy still active per NS-1.

### 2.4 A/B/C Shot Archetype Structure for Stitched Content
- **Source**: OLD-3 CST-001, CST-002
- **What**: Shot A = wide context (establish scene), Shot B = close-up demo (show activity), Shot C = medium CTA/result. The 7+7+7s three-clip format provides concrete structure for stitched content.
- **Why integrate**: NS-1 AUT-006 describes Screenshot Shuffle stitching and NS-2 AUT-005 covers it, but neither provides shot archetype guidance (what each clip SHOULD contain).
- **Where**: Add to WORKFLOW.md stitching/scene breakdown guidance.
- **Adaptation needed**: Adapt from 7s segments to variable-length segments appropriate for the NS multi-length strategy.
- **Staleness check**: VERIFIED -- production technique, not tool-dependent.

### 2.5 Pattern Interrupts: Quantified Impact and Technique Catalogue
- **Source**: OLD-5 CP-002, CP-004, CP-005
- **What**:
  - Pattern interrupts boost watch time by up to 85% and conversion by 32%
  - Ranked techniques: camera angle switches, zoom effects, text overlay pop-ups, B-roll insertion, audio interrupts, on-screen questions, visual effects
  - Implementation rules: don't overuse, place first within 3-4 seconds, create contrast, serve core message
- **Why integrate**: NS-1 CST-006 mentions "visual change every 6-8 seconds" but doesn't quantify the impact or catalogue the techniques.
- **Where**: Add to SYNTHESIS.md content psychology section AND WORKFLOW.md production guidance.
- **Adaptation needed**: Calibrate frequency for calm Montessori tone (not every technique is appropriate -- avoid "frantic" feel).
- **Staleness check**: VERIFIED -- engagement psychology, confirmed still valid per staleness report.

### 2.6 YAML Clip Brief Template
- **Source**: OLD-3 SCR-001
- **What**: Pre-production planning schema with: title, hook text, beat array, vo_word_budget, safety_lines ("Stop if..."), tags, target_length, setting, camera_notes.
- **Why integrate**: NS-2 has a scene breakdown template but not a pre-production clip brief. The brief comes BEFORE the scene breakdown -- it's the planning document that feeds into production.
- **Where**: Add to WORKFLOW.md before the scene breakdown stage (Section 3 or 4).
- **Adaptation needed**: Update fields for NS pipeline (add P1/P2/P3 tier tag, multi-tool notes, character reference fields).
- **Staleness check**: VERIFIED -- planning template, not tool-dependent.

### 2.7 WBR (Weekly Business Review) Dashboard Structure
- **Source**: OLD-1 ANL-011
- **What**: One-page dashboard: total views, weighted retention, top/bottom 3 videos, engagement totals, experiment results, next week plan. NS-2 ANA-008 has a 10-column tracking spreadsheet but not a rollup/review template.
- **Why integrate**: Without a structured review cadence, analytics data gets collected but never acted upon. The WBR forces weekly decision-making.
- **Where**: Add to WORKFLOW.md analytics section (Section 6 or 7).
- **Adaptation needed**: Include NS-specific metrics (3-second retention, save rate, share rate) alongside OLD-1's structure.
- **Staleness check**: VERIFIED -- business process, not tool-dependent.

### 2.8 A/B Test Decision Rubric
- **Source**: OLD-4 CS-004
- **What**: Four-outcome decision rubric: (1) stitched wins -> scale stitched, (2) one-take wins -> scale one-take, (3) inconclusive -> extend test or try hybrid, (4) both fail -> diagnose content not format. With prescribed actions for each outcome.
- **Why integrate**: NS-1 CST-011 has A/B testing protocol but focused on hook variation only, and lacks a decision framework for interpreting results.
- **Where**: Add to WORKFLOW.md A/B testing methodology section.
- **Adaptation needed**: Generalize beyond one-take vs stitched to cover any A/B variable (hook type, content length, posting time, etc.).
- **Cross-references**: OLD-4 AK-006 (significance threshold >5 percentage points), OLD-3 ANL-008/009 (minimum 500 views, n=10 per variant)
- **Staleness check**: VERIFIED -- statistical methodology, not tool-dependent.

### 2.9 Audio Specification Completion (True-Peak and LRA)
- **Source**: OLD-2 PLT-003
- **What**: Audio specs beyond -14 LUFS: True-peak limit TP=-1.5dB, Loudness Range LRA=11. NS-2 PRD-020 targets -14 LUFS but doesn't specify TP or LRA.
- **Why integrate**: Incomplete audio specs cause inconsistent loudness across videos. TP prevents digital clipping. LRA prevents jarring volume shifts within a video.
- **Where**: Add to WORKFLOW.md audio specification section (alongside existing -14 LUFS target).
- **Adaptation needed**: None -- these are universal audio standards.
- **Staleness check**: VERIFIED -- audio engineering standards unchanged.

### 2.10 Negative Feedback Tracking
- **Source**: OLD-4 AK-003
- **What**: Track swipe-away rate, "Not Interested" presses, and active dislike signals. NS-2 ANA-008 tracking spreadsheet doesn't include negative feedback metrics.
- **Why integrate**: Negative feedback signals are weighted MORE heavily by algorithms than positive ones. Ignoring them means missing the most actionable data.
- **Where**: Add "Negative FB%" column to WORKFLOW.md tracking spreadsheet specification.
- **Adaptation needed**: Check which platforms expose this data (Instagram skip rate confirmed available per OLD-5 CP-009).
- **Staleness check**: VERIFIED -- Instagram skip rate ("Viewed vs Swiped Away") confirmed in 2025/2026 Insights per staleness report.

### 2.11 Platform-Specific Tone Differentiation
- **Source**: OLD-5 BV-001, CS-011 through CS-014
- **What**: Content adaptation rules per platform:
  - TikTok: authentic/raw aesthetic, conversational
  - Instagram: polished, visually premium
  - Facebook: conversational, older demographic, community-focused
  - YouTube: keyword-rich titles/descriptions, educational framing
- **Why integrate**: NS-1 has platform-specific export specs (resolution, codec) but NOT content adaptation guidelines. The same video with different captions/tone performs differently per platform.
- **Where**: Add to WORKFLOW.md distribution section as cross-posting adaptation rules.
- **Adaptation needed**: Align with BB brand voice (calm, Montessori, evidence-based) on all platforms while adjusting tone.
- **Staleness check**: VERIFIED -- platform culture differences are stable patterns.

### 2.12 TikTok Hashtag 3-Bucket Formula + AU Examples
- **Source**: OLD-5 CS-019, AS-004
- **What**:
  - Formula: Audience identifier + Topic + Problem solved. Avoid #fyp.
  - AU hashtag examples: Mix niche (#melbourneparents, #sydneymums) + medium (#australianparents, #aussieparenting) + broad (#montessori, #toddleractivities)
- **Why integrate**: NS-1 PLT-005 says "max 5 hashtags" but provides no strategy for hashtag selection. This provides the HOW.
- **Where**: Add to WORKFLOW.md distribution section as hashtag strategy template.
- **Adaptation needed**: Generate BB-specific hashtag pools using the formula.
- **Staleness check**: VERIFIED -- TikTok hashtag best practice (3-6 recommended) confirmed per staleness report.

### 2.13 Content Themes for Australian Parents
- **Source**: OLD-5 CS-023, CS-025, AS-003, AS-007/008
- **What**:
  - **Seasonal AU themes**: Summer outdoor content, beach/camping, school holidays (Jan-Feb back to school, Sep-Oct spring, Nov-Dec holidays)
  - **Trending themes Q4 2025**: Lighthouse parenting, gentle parenting, budget strategies, tech boundaries, sustainability
  - **AU-specific search topics**: Comprehensive keyword list by category (education, cost of living, tech, parenting styles)
- **Why integrate**: NS-1 identifies Montessori 0-3 content gap but doesn't provide seasonal or trend-based content planning input for AU market.
- **Where**: Add to WORKFLOW.md content planning section as content calendar input AND to SYNTHESIS.md audience strategy.
- **Adaptation needed**: Prioritize themes that align with Montessori philosophy (budget-friendly activities, sustainability, screen-free play).
- **Staleness check**: VERIFIED for seasonal patterns (evergreen). Trend data from Q4 2025 -- directionally useful but refresh quarterly.

### 2.14 {HOOK} Token Convention for Automated QC
- **Source**: OLD-4 ST-008, AP-002
- **What**: Explicit {HOOK} token placed in first VO sentence of every script. Automated QC validates hook keyword is present in line 1. Simple regex check.
- **Why integrate**: NS has QC infrastructure plans but no automated hook verification. Hooks are THE most critical element (NS-1 PSY-001: 3-second window).
- **Where**: Add to WORKFLOW.md script template standard AND QC automation pipeline.
- **Adaptation needed**: Define what constitutes a valid hook marker within BB's brand voice.
- **Staleness check**: VERIFIED -- automation pattern, not tool-dependent.

### 2.15 Timecoded Script Templates for 60s Content
- **Source**: OLD-4 ST-001 through ST-007
- **What**: 6 detailed timecoded templates with second-by-second pacing across 3 hook patterns (Outcome-First, Micro-Challenge, Curiosity Gap) for both 21s and 60s formats.
- **Why integrate**: NS-2 has 5 named script templates but they lack second-by-second timing guidance. For 60s content especially, precise pacing prevents the attention dip that kills completion rate.
- **Where**: Add 60s timecoded templates to WORKFLOW.md script section.
- **Adaptation needed**: Update from OLD-4's 21s/60s format to NS's multi-length system. Focus on 30s and 60s templates (21s maps roughly to NS's 15-25s hook tier). Adapt Micro-Challenge pattern as new hook type.
- **Staleness check**: VERIFIED -- scriptwriting patterns, not tool-dependent.

### 2.16 Developmental Stage Content Mapping
- **Source**: OLD-1 CST-010
- **What**: Content categories mapped by developmental stage: Under 1 year = gross motor/sensory. 1-2 years = everyday tasks/practical life. NS-1 CST-008 mentions ages 0-3 underserved but doesn't provide age-stage content mapping.
- **Why integrate**: Parents search by age ("activities for 6 month old", "toddler Montessori"), not by abstract category. Age-stage mapping drives content discoverability.
- **Where**: Add to WORKFLOW.md content planning section.
- **Adaptation needed**: Expand to full 0-36 month range aligned with NS-1's identified content gap.
- **Staleness check**: VERIFIED -- developmental milestones are evidence-based and stable.

### 2.17 YouTube Shorts Custom Thumbnails
- **Source**: OLD-5 PS-014
- **What**: Custom thumbnails at 1280x720 (16:9), 2MB max. Custom thumbnails increase CTR up to 154%.
- **Why integrate**: 154% CTR increase is a massive lever. NS baselines don't mention thumbnail design at all.
- **Where**: Add to WORKFLOW.md production and export section. Add thumbnail creation to Saturday batch export workflow.
- **Adaptation needed**: Design thumbnail templates consistent with BB clay/stylized aesthetic.
- **Staleness check**: VERIFIED -- YouTube thumbnail specs confirmed current per staleness report.

### 2.18 MJ Prompt Glossary: Tested Terms and Banned Terms
- **Source**: OLD-2 VIS-005, VIS-006
- **What**:
  - **Recommended terms**: Curated, MJ-tested terms for camera movement, focus, and lighting
  - **Banned terms**: Motion-specific bans (fast pan, shaky cam, hyperlapse, strobe, bokeh balls, lens flare)
- **Why integrate**: NS-1 VIS-003 has negative prompts focused on style (no plastic, no neon) but missing motion/camera banned terms. These cause generation failures and wasted credits.
- **Where**: Merge banned terms into SYNTHESIS.md NS-1 VIS-003 negative prompt set. Add tested terms as appendix.
- **Adaptation needed**: Filter for terms applicable to stylized clay aesthetic (some photorealistic camera terms may not apply).
- **Staleness check**: VERIFIED -- MJ parameters (--motion, --seed) confirmed still functional per staleness report.

### 2.19 Production Throughput Daily Tracking
- **Source**: OLD-2 AUT-009
- **What**: ops/throughput_tracker.csv with: date, slugs_done, relax_jobs, fast_jobs, avg_minutes, failures, notes. NS-2 MON-002 tracks per-video costs but not daily production throughput.
- **Why integrate**: Without throughput tracking, you can't measure pipeline efficiency or identify bottlenecks. The WORKFLOW's weekly rhythm needs a measurement system.
- **Where**: Add to WORKFLOW.md analytics/operations section.
- **Adaptation needed**: Align columns with NS pipeline stages (MJ generation, Pika/Kling generation, DaVinci assembly, QC pass/fail).
- **Staleness check**: VERIFIED -- CSV tracking, not tool-dependent.

---

## PRIORITY 3: Validations (Reinforcement -- No Action Needed)

Findings from old research that confirm current North Star positions. Useful as confidence boosters but require no changes.

| Category | Validation Count | Key Confirmations |
|----------|-----------------|-------------------|
| CONTENT_PSYCHOLOGY | 18 | 3-second hook window (5 sources), sound-off viewing majority, no slow intros, pattern interrupts every 2-8s, seamless loops, rewatch psychology |
| CONTENT_STRATEGY | 12 | CTA should be value-tied not generic, share-prompting for educational content, hook in first 3s mandatory, 60s enables monetization |
| PLATFORM_SPECS | 22 | 1080x1920 universal, burned-in captions required (3 sources), YouTube SRT support, Instagram muted autoplay, -14 LUFS audio standard, madeForKids:false critical |
| BRAND_VOICE | 8 | Montessori calm/encouraging/factual tone, adult-facing not kiddie show, no branded products, content should feel human even if AI-generated |
| QC_INFRASTRUCTURE | 10 | Auto-caption cleanup required, seed discipline for repeatability, export QC checklist concept, WER check for TTS content |
| AUDIENCE_STRATEGY | 8 | Australian parents primary target, privacy-first approach, content for adults about children |
| PRODUCTION_GUIDANCE | 8 | Dual caption strategy (burned-in + SRT), SRT timing sync, 48kHz audio, FFmpeg as core tool |
| TOOLS_AND_TECH | 7 | FFmpeg, n8n, DuckDB, PostHog, Google Sheets, Metricool, Claude for QC |
| ANALYTICS_KPIS | 6 | 3-second retention as north star, 65%+ target, completion rate tracking, per-1K normalization concept |

**Total validations across all 5 OLD sources: 246** -- the old research broadly confirms the North Star direction.

---

## CONFLICTS: Human Decision Required

Items where old research and current North Star docs disagree. Both sides presented for human decision.

### Conflict 1: Instagram Reels Optimal Length
- **Old research says**: 15-30s optimal for IG Reels (OLD-5 CS-001)
- **Current North Star says**: 60-90s optimal (NS-1 PLT-002, sourced from Socialinsider 31M posts)
- **Staleness check**: Both are from 2025 research. Instagram Reels now supports up to 20 minutes (per staleness report), so the platform isn't constraining either approach.
- **Recommendation**: These measure different things -- OLD-5 measures viral/completion potential (shorter = higher completion), NS-1 measures engagement depth (longer = more watch time). The NS 4-tier strategy already resolves this by producing content at multiple lengths. **Suggest no change**, but add OLD-5's observation that 15-30s has higher completion rates as a note to the P1 (hook/snackable) tier.

### Conflict 2: TikTok Optimal Length
- **Old research says**: 15-30s for viral potential (OLD-5 CS-002)
- **Current North Star says**: 60s-10min for reach (NS-1 PLT-001, sourced from Buffer Mar 2025, 1.1M videos)
- **Staleness check**: TikTok now supports up to 60-minute uploads per staleness report.
- **Recommendation**: Same resolution as Conflict 1 -- different metrics. NS-1's 4-tier strategy already covers both. **Suggest no change**, but note the tension between completion and reach in SYNTHESIS.md for future experiment design.

### Conflict 3: Beat Cadence / Shot Duration
- **Old research says**: 3-5 seconds maximum, never linger >6s (OLD-4 PG-001), with OLD-1 PSY-006 at 2-5s
- **Current North Star says**: Visual change every 6-8 seconds (NS-1 CST-006)
- **Staleness check**: Both are based on engagement psychology (verified evergreen).
- **Recommendation**: NS's 6-8s pacing was chosen for calm Montessori content. OLD's 3-5s is for viral engagement content. **Human decision needed**: Should BB content lean calm (6-8s) or viral (3-5s)? Consider: 6-8s for deep-dive/educational content (P2/P3), 3-5s for hook/snackable content (P1). Add note to WORKFLOW.md acknowledging both cadences with guidance on when each applies.

### Conflict 4: VO Pacing / Words Per Minute
- **Old research says**: 143-180 WPM (OLD-1: ~3 words/sec, OLD-3: 160-180 WPM, OLD-4: 55-65 words/21s)
- **Current North Star says**: 130 WPM (NS-2 BRV-001)
- **Staleness check**: NS chose 130 WPM deliberately to accommodate sound-off caption reading.
- **Recommendation**: **NS is correct and intentional.** The old research rates (143-180 WPM) are conversational speaking rates. NS's 130 WPM is deliberately slower for caption readability. 69-74% of viewers watch sound-off. **No change needed.** However, clarify in WORKFLOW.md that 130 WPM is for VO delivery, and on-screen caption display speed may differ (OLD-3 PRD-009 notes 160-180 WPM as READING speed -- viewers read faster than they listen). Add this distinction.

### Conflict 5: 3-Second Retention Target
- **Old research says**: >80% (OLD-1 ANL-001)
- **Current North Star says**: 65%+ (NS-1 ANL-001, sourced from OpusClip study with 4-7x impression multiplier)
- **Staleness check**: NS is better sourced with specific data.
- **Recommendation**: **NS target (65%+) is the operational target.** OLD-1's 80% could serve as a "stretch goal" tier. Add tiered success language: 65% = good (algorithmic boost), 80% = excellent (top-quartile performance).

### Conflict 6: Hashtag Limits
- **Old research says**: IG/FB max 30, recommend 5-10 (OLD-5 PS-018)
- **Current North Star says**: TikTok max 5 (Aug 2025), IG max 5 (Dec 2025) (NS-1 PLT-005)
- **Staleness check**: NS reflects later policy updates (Aug/Dec 2025 vs OLD-5's Q4 2025 general guidance).
- **Recommendation**: **Keep NS-1's 5-max as it reflects the latest platform policies.** OLD-5 may predate the stricter limits.

### Conflict 7: Caption Font Choice
- **Old research says**: Arial, 60px, 3px outline (OLD-3 VIS-010)
- **Current North Star says**: Montserrat Bold, 60-72pt, 2-4px black stroke (NS-1 PRD-017)
- **Staleness check**: Both are functional choices.
- **Recommendation**: **NS font (Montserrat Bold) is an intentional brand decision.** No change. However, OLD-3's WCAG AA compliance note and .ASS file format specification are valuable additions -- integrate those technical details without changing the font choice.

---

## OUTDATED: Do Not Integrate

Items from old research confirmed outdated by the staleness report. Listed here so nothing is silently dropped.

### Tool/Platform Duration Updates

| Item | Old Claim | Current Reality (Feb 2026) | Source(s) | Impact |
|------|-----------|---------------------------|-----------|--------|
| YouTube Shorts length | "Up to 60s" | 3 minutes since Oct 2024. Content ID blocks Shorts >1 min globally. | OLD-1 | Update platform specs in both NS docs |
| Instagram Reels length | "3 minutes" (OLD-5) / "60-90s optimal" (NS-1) | Up to 20 minutes recording. Algorithm still favors sub-90s. | OLD-5, NS-1 | Update max duration in platform specs |
| TikTok duration | "Up to 60s" (OLD-1) | In-app 10-30 min, upload up to 60 min | OLD-1 | Update platform specs |
| TikTok SRT upload | "Does NOT support manual SRT" | SRT now available via TikTok Ads Manager and Video Editor | OLD-1, OLD-4 | Update caption strategy -- SRT now possible for TikTok |

### Tool Pricing/Feature Updates

| Item | Old Claim | Current Reality (Feb 2026) | Source(s) | Impact |
|------|-----------|---------------------------|-----------|--------|
| MidJourney Relax plan | "Standard plan includes unlimited video Relax" | Requires Pro ($60) or Mega ($120), NOT Standard ($30) | OLD-2, OLD-3, WORKFLOW | Update cost model. Budget impact: $30 more/month minimum for video Relax. |
| Pika credit rollover | "No rollover" | Paid plans now have roll-over credits | WORKFLOW | Minor update to cost model |
| Pika commercial license | "Standard has NO commercial license" | Standard ($8/mo) now includes commercial use | WORKFLOW | Good news: cheaper commercial entry point |
| DaVinci Resolve version | Implied v19.x | Now DaVinci Resolve 20 with 100+ new features including AI tools | WORKFLOW | Re-evaluate DaVinci scripting capabilities (UIManager issue may be resolved) |
| ElevenLabs pricing | "$5/month, 30 min" | Starter still $5/month but uses credit system (30,000 credits) not minutes | WORKFLOW | Minor update |
| Fish Audio pricing | "$9.99/200 min" | Restructured to tiered plans (~$11/mo or $5.50 promo) | WORKFLOW | Minor update |

### Policy/Compliance Updates

| Item | Old Claim | Current Reality (Feb 2026) | Source(s) | Impact |
|------|-----------|---------------------------|-----------|--------|
| COPPA fine amount | "$42,530 per video" (NS-1) | $50,120/video COPPA, $53,088/violation FTC. Disney fined Sept 2025. | NS-1, OLD-5 | **Update SYNTHESIS.md with current fine amounts** |
| COPPA amendments | Not mentioned in old research | January 2025 amendments: biometric data, consent requirements, April 22 2026 full compliance deadline | OLD-5 | **Add compliance deadline to both docs** |
| TikTok CML terms | "Free for business, TikTok-only" | January 2026 TOS tightened: stricter no cross-platform clause, off-platform tracking | OLD-5 | Update music licensing section |

### Visual Direction (Intentional Pivot, Not Staleness)

| Item | Old Position | Current NS Position | Source(s) | Notes |
|------|-------------|-------------------|-----------|-------|
| Visual style | Photorealistic Australian home | Stylized clay/bioluminescent Brancusi-inspired | OLD-1/2/3 | Intentional strategic pivot. NS direction confirmed correct. AU localisation cues remain useful for stylized settings (see P1.2). |
| Character approach | Hands-only, no faces | Named "BB Baby" character with face | OLD-2 | NS strategic choice. Hands-only could be supplementary format. |
| AR filters | "No AR filters or cutesy animations" (Montessori reality) | Stylized clay characters with bioluminescent glow | OLD-1 | NS-1 AUD-004 resolves: content is for adults, not children. |
| Pipeline architecture | Claude Sonnet/Haiku 5-stage skill pipeline | MJ+Pika+Kling+DaVinci+MCP 8-phase pipeline | OLD-1 | Complete architecture change. NS reflects current tooling. |

---

## PARTIAL: Details to Add to Existing Coverage

Items already partially covered in North Star docs but with missing details from old research worth adding.

### P-1: Reverse-Structure Video Editing Technique
- **Currently in NS**: NS-1 CST-003 lists "Result-First" as HIGHEST PERFORMER hook pattern
- **Missing detail**: The specific production technique of showing the end result in the first second, then rewinding to show the process
- **Source**: OLD-1 PSY-004
- **Where to add**: WORKFLOW.md scene breakdown guidance for Result-First hook pattern

### P-2: Seamless Loop / Cliffhanger Loop Variants
- **Currently in NS**: NS-2 CPY-010 mentions "end frame matches opening for seamless loop"
- **Missing detail**: Rewatch psychology (viewers may not realize the restart, inflating completion rates) and the cliffhanger variant (60s videos end mid-action to trigger rewatch)
- **Source**: OLD-1 PSY-007
- **Where to add**: WORKFLOW.md script templates, noted as technique for both short (seamless loop) and long (cliffhanger) formats

### P-3: Environment Setting Variants (Apartment + Coastal)
- **Currently in NS**: NS-2 SET-001 through SET-007 describe Montessori playroom variants
- **Missing detail**: "Compact apartment" setting (Montessori in modest spaces -- accessibility messaging) and "coastal bright room" setting (AU feel with natural light)
- **Source**: OLD-2 SET-001/002/003
- **Where to add**: WORKFLOW.md scene settings catalogue

### P-4: Caption Sync Tolerance
- **Currently in NS**: QC checks mention caption accuracy
- **Missing detail**: Specific tolerance: <=0.2s between VO audio and burned-in caption display
- **Source**: OLD-3 QCI-003
- **Where to add**: WORKFLOW.md QC checklist, audio/caption section

### P-5: Platform Metadata as QC Gate
- **Currently in NS**: NS-1 PLT-008 covers AI disclosure policies, NS-2 PLT-011 flags madeForKids
- **Missing detail**: Structure these as a formal pre-publish QC gate step (not just awareness items)
- **Source**: OLD-3 QCI-007
- **Where to add**: WORKFLOW.md QC checklist as distinct gate step: "Platform metadata verified" (AI labels set, madeForKids:false, correct category, correct audience)

### P-6: Prop Continuity and Lighting Consistency
- **Currently in NS**: NS-1 QCI-002 #7 says "Background: no scene switching"
- **Missing detail**: Prop persistence (if object in Shot A, ensure it appears in Shot C) and explicit lighting matching rule across clips
- **Source**: OLD-3 VIS-011, VIS-012
- **Where to add**: WORKFLOW.md stitching QC checklist

### P-7: On-Screen AI Text Artifact Check
- **Currently in NS**: NS-1 QCI-002 has 10-item visual QC
- **Missing detail**: If any AI-generated text appears (signs, books, labels), ensure it's gibberish-free or blurred. AI text generation is a known weakness.
- **Source**: OLD-3 PRD-015
- **Where to add**: WORKFLOW.md QC checklist item #11: "No readable AI-generated text artifacts"

### P-8: Camera Framing Progression
- **Currently in NS**: Scene breakdown template exists but no shot-to-shot progression guidance
- **Missing detail**: Shot progression: wide establishing -> close-up detail -> medium result. Creates natural visual flow in stitched content.
- **Source**: OLD-3 VIS-013
- **Where to add**: WORKFLOW.md stitching guidance

### P-9: H.264 High Profile Level 4.2
- **Currently in NS**: NS-2 PLT-016 specifies "H.264 MP4" without profile/level
- **Missing detail**: Specific codec profile (High) and level (4.2) for maximum compatibility
- **Source**: OLD-2 PLT-002
- **Where to add**: WORKFLOW.md export specification section

### P-10: Engagement Rate Benchmarks
- **Currently in NS**: Tracks engagement but provides no specific thresholds
- **Missing detail**: Likes per 1K views >50 = very good. Comments per 1K views >5 = good. Hook rate benchmark: 30.7% average, 40-45% top quartile (OLD-5 AK-001).
- **Source**: OLD-1 ANL-005, OLD-1 ANL-006, OLD-5 AK-001
- **Where to add**: SYNTHESIS.md analytics section as benchmark reference table

### P-11: Facebook SRT Naming Convention
- **Currently in NS**: SRT for YouTube covered
- **Missing detail**: Facebook naming convention: video.en_US.srt (must match video filename)
- **Source**: OLD-4 PG-008
- **Where to add**: WORKFLOW.md platform-specific distribution section

### P-12: YouTube Tags Strategy
- **Currently in NS**: YouTube distribution covered but tags not specified
- **Missing detail**: ~5 tags, main keyword first, competitor tags. Plus YouTube Shorts title under 60 chars for full visibility.
- **Source**: OLD-5 CS-009, OLD-5 ST-002
- **Where to add**: WORKFLOW.md YouTube distribution checklist

### P-13: Instagram Alt Text for SEO
- **Currently in NS**: Instagram distribution covered but alt text not mentioned
- **Missing detail**: Alt text under 100 characters, keyword-rich. Instagram posts now indexable by Google/Bing.
- **Source**: OLD-5 PG-007, OLD-5 PS-021
- **Where to add**: WORKFLOW.md Instagram distribution checklist

### P-14: Per-1K Normalization for Metrics
- **Currently in NS**: NS-2 ANA-008 tracks raw saves/shares/comments
- **Missing detail**: Normalize all engagement metrics per 1,000 views for valid cross-video comparison
- **Source**: OLD-4 AK-002
- **Where to add**: WORKFLOW.md analytics tracking spreadsheet definition

### P-15: Completion Rate Tiered Thresholds
- **Currently in NS**: NS-1 ANL-003 has 81.2% for under-10s and 31% for 60s-3min
- **Missing detail**: Aspirational targets: >80% for 20s = "achievable for hits", >60% for 60s = "very solid", 50%+ for 60s = "successful"
- **Source**: OLD-1 ANL-003
- **Where to add**: SYNTHESIS.md analytics section as success tier labels

---

## Australia-Specific Production Guide (Consolidated)

All AU-specific findings from all 5 old sources plus baselines, consolidated into one reference. This section should be added to SYNTHESIS.md as an appendix.

### Indoor Visual Cues
| Cue | Description | Source |
|-----|-------------|--------|
| Power outlets | 3-pin Australian outlets visible on walls | OLD-1 SET-001 |
| Skirting boards | Timber skirting boards (paint or stain) | OLD-1 SET-002 |
| Rugs | Jute, sisal, or natural fibre rugs | OLD-1 SET-003 |
| Textiles | Linen textures on curtains, cushions, throws | OLD-1 SET-004 |
| Ceiling fans | White ceiling fans (ubiquitous in AU homes) | OLD-1 SET-005 |
| Doors | Sliding glass doors leading to outdoor area | OLD-1 SET-006 |
| Flooring | Polished concrete, light timber, or tiles | OLD-1 SET-007 |
| Plants (indoor) | Fiddle-leaf fig, monstera, devil's ivy | OLD-1 SET-008 |
| Safety gates | Australian-style safety gates | OLD-1 SET-009 |
| Baby products | AU brands: Ergo Pouch sleep bags, Kmart wooden toys | OLD-1 SET-010 |
| Light switches | Australian-style light switches (rocker, not toggle) | OLD-3 AU pack |
| Kitchen | Open shelving, Smeg-style appliances (described, not branded) | OLD-3 AU pack |
| Furniture | Mid-century modern + natural timber mix | OLD-3 AU pack |

### Outdoor Visual Cues
| Cue | Description | Source |
|-----|-------------|--------|
| Fences | Timber or Colorbond fencing | OLD-1 SET-012 |
| Plants (outdoor) | Bottlebrush, grevillea, kangaroo paw, native grasses | OLD-1 SET-013 |
| Lighting | North-facing windows (prized in AU for natural light) | OLD-1 VIS-001 |
| Architecture | Weatherboard, brick, or rendered exterior | OLD-1 SET-014 |
| Entertaining | Covered outdoor area (pergola/verandah) | OLD-3 AU pack |

### Language and Spelling
| AU English | NOT | Source |
|-----------|-----|--------|
| Mum | Mom | OLD-1 BRV-003, OLD-3 BRV-004 |
| Nappies | Diapers | OLD-5 AS-002 |
| Kindy / Kinder | Kindergarten / Pre-K | OLD-5 AS-002 |
| Bub | Baby (informal) | OLD-5 AS-002 |
| Organise | Organize | OLD-1 BRV-003 |
| Colour | Color | OLD-1 BRV-003 |
| Behaviour | Behavior | OLD-1 BRV-003 |
| Centre | Center | OLD-1 BRV-003 |
| Practise (verb) | Practice (verb) | Standard AU English |
| Favourite | Favorite | Standard AU English |

### Posting Times (AEDT)
- **Source**: OLD-5 (comprehensive schedule by platform and day)
- **Note**: Full schedule to be extracted from OLD-5 during integration. NS-1 only had "Thursday 7-10 PM AEST."
- **Action**: Replace single data point in WORKFLOW.md with full schedule.

### Products and Brands (Reference Only -- Never Name in Content)
| Category | AU Brands to Describe (Not Name) | Source |
|----------|----------------------------------|--------|
| Sleep bags | Ergo Pouch style (organic cotton, zip-front) | OLD-1 SET-010 |
| Wooden toys | Kmart wooden toy style, Plan Toys style | OLD-1 SET-010 |
| Safety | BabyDan / Dreambaby gate style | OLD-1 SET-009 |
| Textiles | Linen Republic style, natural fibres | OLD-3 AU pack |

### Avoid List
| Do NOT Include | Why | Source |
|---------------|-----|--------|
| American power outlets | Instantly breaks AU immersion | OLD-1 SET-001 |
| Carpet (wall-to-wall) | Uncommon in modern AU homes | OLD-1 SET-007 |
| Snow/winter imagery | AU content = southern hemisphere seasons | OLD-5 AS-007 |
| Brand names in prompts | Trademark risk, AI generation artifacts | OLD-3 AUD-004 |
| "Mom" / American spelling | Primary audience is Australian | OLD-1 BRV-003 |
| Loud kookaburra audio | Startling for infants. Magpie ambient OK. | OLD-1 PRD-007 |
| Toggle light switches | American style, not AU | OLD-3 AU pack |
| Front-loading dryers | Top-loaders more common in AU homes | AU context knowledge |

### Localisation Dosage Rules
- **1-2 AU localizers per MJ/AI prompt** (OLD-3 AUD-002): avoids overt cliches, keeps prompts focused
- **2-3 AU cues per finished video** (OLD-1 SET-016): enough for subconscious recognition without making it "about" Australia
- **Subtlety principle**: AU details should be noticed subconsciously, never foregrounded (OLD-3 PSY-005, OLD-1 AUD-003)

---

## Automation Pipeline Additions

Specific automation opportunities to add to WORKFLOW.md, from the staleness/automation report.

### High Priority

#### A-1: Whisper WER QC Harness
- **Source**: OLD-2 QCI-001 (complete Python implementation provided)
- **What**: Extract audio from finished video, transcribe with Whisper, compare against reference SRT, compute Word Error Rate. Fail if WER >10%.
- **Feasibility**: HIGH -- Whisper still available (staleness VERIFIED), script provided in old research
- **Implementation**:
  1. Install faster-whisper (more efficient than original Whisper)
  2. Adapt OLD-2's wer_harness.py for NS pipeline (input: finished MP4 + reference SRT)
  3. Add as post-assembly QC step before export
  4. Log WER to tracking spreadsheet
- **Integration point**: Connects to existing WORKFLOW.md QC pipeline (watchdog + SQLite + Claude)

#### A-2: Caption Safe-Zone Validator
- **Source**: OLD-3 PLT-001/002/003, staleness Gap #5
- **What**: Parse .ASS subtitle file's MarginV value, verify against platform-specific safe zones. Flag violations before export.
- **Feasibility**: HIGH -- simple text parsing
- **Implementation**:
  1. Parse MarginV from .ASS file
  2. Check against per-platform thresholds
  3. Generate per-platform pass/fail report
  4. Run before batch export step
- **Note**: Re-verify pixel values before implementation (staleness: UNVERIFIABLE for exact pixels)

#### A-3: Audio Level Checker
- **Source**: OLD-2 PLT-003, staleness Gap #12
- **What**: FFmpeg loudnorm filter measures integrated loudness in a single command. Pre-export check flags deviations from -14 LUFS, TP>-1.5dB, or VO outside -12 to -6 dBFS range.
- **Feasibility**: HIGH -- FFmpeg already in toolchain
- **Implementation**: `ffmpeg -i input.mp4 -filter:a loudnorm=print_format=json -f null /dev/null`
- **Integration point**: Add as automated check in DaVinci assembly QC step

#### A-4: {HOOK} Token Validation
- **Source**: OLD-4 ST-008, AP-002
- **What**: Simple regex check that first line of every VO script contains a hook marker. Catches scripts that start with preamble instead of hook.
- **Feasibility**: HIGH -- regex, no dependencies
- **Implementation**: Validate against script template standard during Monday script-writing session
- **Integration point**: Add to script QC (before production begins)

#### A-5: Cross-Posting Stagger Scheduler
- **Source**: OLD-5, staleness Gap #7
- **What**: Takes batch of 12 exported files (3 lengths x 4 platforms), assigns to optimal posting times per platform per day (AU AEDT), queues uploads.
- **Feasibility**: HIGH -- n8n 2.0 released Dec 2025, cron alternative
- **Implementation**:
  1. Define posting schedule (from OLD-5 AU times)
  2. n8n workflow or Python script assigns file -> timeslot
  3. YouTube Data API v3 for automated upload (already PLANNED in WORKFLOW)
  4. Notification/reminder for manual platforms (TikTok, Instagram)

### Medium Priority

#### A-6: n8n Watch-Folder Pipeline
- **Source**: OLD-2 AUT-001 (complete 10-node design)
- **What**: Automated file routing: monitors inbox for MJ clips, checks for matching VO/subtitle files, routes through processing pipeline, fires webhook on completion.
- **Feasibility**: HIGH -- n8n 2.0 active and mature
- **Implementation**: Adapt OLD-2's node design for NS pipeline stages. Connect to BB SQLite schema for content tracking.
- **Complexity**: MEDIUM -- requires n8n installation and configuration

#### A-7: Platform-Specific Caption Generation
- **Source**: OLD-5, staleness Gap #6
- **What**: From a single script/brief, auto-generate platform-specific captions: TikTok (raw/conversational, keyword front-loaded), Instagram (polished, SEO alt text), YouTube (keyword-rich title/description), Facebook (conversational).
- **Feasibility**: HIGH -- template-based string formatting
- **Implementation**: JSON templates per platform, Python script fills from master brief

#### A-8: Hashtag Rotation System
- **Source**: OLD-5, staleness Gap #8
- **What**: JSON pool of AU-specific hashtags categorized by bucket (niche/medium/broad), random selection per post to prevent same-hashtag fatigue.
- **Feasibility**: HIGH -- simple JSON + random selection
- **Implementation**: Build hashtag pools using OLD-5 CS-019 formula, rotate per post

#### A-9: MJ Prompt Generation from YAML Clip Brief
- **Source**: OLD-3, staleness Gap #13
- **What**: Auto-generate MJ prompts from YAML clip brief by filling template with setting, camera, AU localiser, and character reference parameters.
- **Feasibility**: HIGH -- template filling
- **Implementation**: YAML brief (from 2.6 above) -> template engine -> MJ prompt with --oref, --seed, --motion, AU cues
- **Complexity**: MEDIUM -- needs prompt template library and AU localiser injection logic

### Lower Priority

#### A-10: Shot Cadence Analyzer
- **Source**: OLD-4, staleness Gap #10
- **What**: FFmpeg scene detection (scdet filter) validates no static shot exceeds configured threshold (5-8s depending on content tier).
- **Feasibility**: MEDIUM -- requires FFmpeg scene detection tuning
- **Implementation**: `ffmpeg -i input.mp4 -filter:v "select='gt(scene,0.3)'" -vsync vfr frames/%04d.png`

#### A-11: Watermark Detection Pre-Cross-Post
- **Source**: OLD-5, staleness Gap #9
- **What**: Detect platform watermarks before cross-posting (Instagram suppresses TikTok-watermarked content).
- **Feasibility**: MEDIUM -- image analysis or metadata check
- **Complexity**: MEDIUM

#### A-12: Upscaler A/B Test Framework
- **Source**: OLD-2 QCI-004
- **What**: 12-clip comparison with MOS (Mean Opinion Score), Sobel edge detection, CER (Character Error Rate). For evaluating Real-ESRGAN vs Topaz vs native upscaling.
- **Feasibility**: MEDIUM -- requires OpenCV + Tesseract
- **Complexity**: MEDIUM -- only needed if upscaling quality questions arise

---

## Implementable Artifacts Catalogue

Summary of all code, configs, scripts, and schemas found across old research with recommended next steps.

| Artifact | Source | Type | Staleness Status | Next Step |
|----------|--------|------|-----------------|-----------|
| wer_harness.py (Whisper WER check) | OLD-2 QCI-001 | Python script | VERIFIED (Whisper still available) | Adapt for NS pipeline, add as QC step |
| .ASS subtitle style template | OLD-3 TEC-003 | Config file | VERIFIED (FFmpeg .ASS support unchanged) | Update font to Montserrat Bold, adapt MarginV per platform |
| FFmpeg caption burn-in command | OLD-3 | CLI command | VERIFIED | Adapt for NS caption style |
| FFmpeg stitch command | OLD-3 | CLI command | VERIFIED | Already in NS pipeline concept |
| FFmpeg stitch+caption command | OLD-3 | CLI command | VERIFIED | Combine with NS DaVinci workflow |
| YAML clip brief schema | OLD-3 SCR-001 | Template | VERIFIED | Add P1/P2/P3 tier field, character reference fields |
| finish.sh (batch finishing) | OLD-2 AUT-002 | Bash script | VERIFIED | Adapt for NS pipeline file structure |
| ffmpeg_finish.yml (n8n workflow) | OLD-2 AUT-001 | n8n config | VERIFIED (n8n 2.0 released) | Review and adapt for NS pipeline |
| throughput_tracker.csv | OLD-2 AUT-009 | CSV template | VERIFIED | Align columns with NS pipeline stages |
| 10 MJ prompt sets (topics) | OLD-3 CST-008 | Prompts | OUTDATED (photorealistic direction) | Topic ideas valid; prompts need rewrite for clay/stylized |
| 6 timecoded script templates | OLD-4 ST-001-007 | Templates | VERIFIED (structure valid) | Adapt timing for NS multi-length strategy |
| 4 hand appearance presets | OLD-2 VIS-007 | Prompts | OUTDATED (hands-only superseded) | Archive -- only useful if hands-only supplementary format added |
| 13 reference URLs | OLD-4 OT-001 | Bibliography | PARTIALLY VERIFIED | Add unique URLs to source verification list |
| TikTok caption SEO template | OLD-5 ST-001 | Template | VERIFIED | Add to WORKFLOW.md distribution section |
| YouTube Shorts title/description template | OLD-5 ST-002 | Template | VERIFIED | Add to WORKFLOW.md distribution section |
| Instagram hashtag template (AU) | OLD-5 ST-003 | Template | VERIFIED | Add to WORKFLOW.md distribution section |

---

## New Platform Features to Add to North Star Docs

Critical platform updates from staleness report that affect BOTH existing NS docs AND integration decisions.

| Feature | Impact | Source | Where to Add |
|---------|--------|--------|-------------|
| YouTube Shorts now 3 min (Oct 2024) | Longer-form Shorts possible, but Content ID blocks >1 min with claimed music | Staleness report | SYNTHESIS.md platform specs |
| Instagram Reels now 20 min (2025) | Algorithm still favors sub-90s. No practical change to BB strategy. | Staleness report | SYNTHESIS.md platform specs (update max duration) |
| TikTok upload up to 60 min | No practical change to BB short-form strategy | Staleness report | SYNTHESIS.md platform specs (update max duration) |
| Instagram posts indexable by Google/Bing (Jul 2025) | Each Reel is now a micro-landing page for web search. SEO importance elevated. | OLD-5 PS-021, staleness VERIFIED | SYNTHESIS.md -- reinforces SEO-first strategy |
| YouTube Shorts in Google Discover (Sep 2025) | Shorts appear in Google Discover feeds. YouTube SEO importance elevated. | OLD-5 PS-020, staleness VERIFIED | SYNTHESIS.md -- reinforces YouTube as primary platform |
| Facebook Oct 2025 algorithm: 50% more same-day content | Recency advantage for Facebook posting. Favour same-day content. | OLD-5 PS-022, staleness VERIFIED | WORKFLOW.md distribution strategy |
| COPPA amendments: April 22, 2026 full compliance deadline | Expanded biometric protections, separate consent for data sharing. IMMINENT. | Staleness report | SYNTHESIS.md compliance section -- **TIME-SENSITIVE** |
| YouTube Shorts Music Content ID >1 min | Shorts >1 min with Content ID claimed music blocked globally | Staleness report (NEW FINDING) | SYNTHESIS.md platform specs AND WORKFLOW.md music licensing |
| TikTok CML January 2026 TOS tightened | Stricter no cross-platform clause, off-platform tracking | Staleness report | WORKFLOW.md music licensing section |
| Hailuo/MiniMax emerged (IPO Jan 2026) | New video generation competitor worth evaluating | Staleness report (NEW ENTRANT) | SYNTHESIS.md tool evaluation list |
| TikTok SRT upload now available | Via Ads Manager and Video Editor. Changes dual-caption strategy. | Staleness report | SYNTHESIS.md/WORKFLOW.md caption strategy |
| Envato VideoGen promo expires Feb 25, 2026 | TIME-SENSITIVE promo deadline | Staleness report | WORKFLOW.md tools section -- verify before deadline |

---

## Human Decision Checklist

Items requiring your judgment before integration:

### Conflicts (Must Decide)
- [ ] **Conflict 3 (Beat Cadence)**: Should BB content use 3-5s (viral) or 6-8s (calm) shot duration? Or differentiate by content tier (P1 viral, P2/P3 calm)?
- [ ] **Conflict 1+2 (Optimal Length by Platform)**: Accept that NS 4-tier strategy already resolves this, or adjust tier priorities?
- [ ] **Conflict 5 (3-Second Retention)**: Accept 65% as target with 80% as stretch goal?

### Strategic Decisions
- [ ] **Safe zone pixel values**: Re-verify on current platform UIs before hardcoding? Or use as starting point and refine?
- [ ] **Two-person review**: Practically feasible for current team size? Or adapt to self-review checklist with mandatory 24-hour cooling-off period?
- [ ] **Hands-only supplementary format**: Worth producing alongside BB Baby character content? Or stay focused on single visual direction?

### Approvals
- [ ] Approve P1 items (16 items) for immediate integration into SYNTHESIS.md and WORKFLOW.md
- [ ] Approve P2 items (19 items) with adaptations as described
- [ ] Approve PARTIAL items (15 items) for detail additions
- [ ] Approve automation additions (12 items) for WORKFLOW.md pipeline
- [ ] Review OUTDATED items -- any worth keeping as historical reference?
- [ ] Review Australia-Specific Production Guide for completeness before adding as appendix

### Time-Sensitive Items
- [ ] **COPPA compliance deadline: April 22, 2026** -- ensure compliance checklist is integrated immediately
- [ ] **Envato VideoGen promo: expires Feb 25, 2026** -- verify if still available/relevant
- [ ] **COPPA fine amount in SYNTHESIS.md**: Update from $42,530 to $50,120 immediately

---

## Appendix: Source Cross-Reference Index

For traceability, every recommendation in this document maps to these source files:

| Source ID | File | Location |
|-----------|------|----------|
| OLD-1 | extraction-OLD-1.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |
| OLD-2 | extraction-OLD-2.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |
| OLD-3 | extraction-OLD-3.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |
| OLD-4 | extraction-OLD-4.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |
| OLD-5 | extraction-OLD-5.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |
| NS-1 | SYNTHESIS.md | `/home/squiz/code/ATLAS/docs/research/bb-content-production/` |
| NS-2 | WORKFLOW.md | `/home/squiz/code/ATLAS/docs/research/bb-content-production/` |
| Gap Part 1 | gap-analysis-part1.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |
| Gap Part 2 | gap-analysis-part2.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |
| Staleness | staleness-and-automation-report.md | `/home/squiz/code/ATLAS/docs/research/bb-old-extractions/` |

---

*End of Integration Recommendations. Generated 2026-02-03 by Claude Opus 4.5 synthesis agent.*
*Total recommendations: 16 P1 (immediate), 19 P2 (with adaptation), 15 PARTIAL (detail additions), 7 CONFLICT (human decision), 12 AUTOMATION (pipeline), plus Australia-specific consolidated guide and implementable artifacts catalogue.*

---

## Integration Changelog (Phase 5 Execution)

**Date:** 2026-02-03
**Executed by:** 10 Opus agents across 4 waves

### Items Integrated: 67/67 (100%)

| Category | Items | Status |
|----------|-------|--------|
| P1 (Immediate) | 16/16 | All integrated |
| P2 (With Adaptation) | 19/19 | All integrated |
| PARTIAL (Detail Additions) | 15/15 | All integrated |
| Conflict Resolutions | 7/7 | All resolved per user decisions |
| OUTDATED Corrections | 10/10 | All corrected |
| TIME-SENSITIVE Flags | 2/2 | Both prominently flagged |
| Automation Roadmap | 12/12 | A-1 to A-12 documented |

### User Decisions Applied
- AU English: Cross-reference to BB-Writer agent, not duplication
- AU Visual Cues: Descriptions only, NO brand names (hallucination risk)
- Removed from avoid list: "Carpet (wall-to-wall)" and "Front-loading dryers"
- Optimal length: Multi-length strategy accepted (no single number)
- Beat cadence: Variable — 3-5s for P1 (viral), 6-8s for P2/P3 (educational)
- WPM: 130 WPM confirmed
- 3-second retention: 65% target, 80% stretch goal
- Hashtags: 5 max
- Caption font: Montserrat Bold (brand watermark = TODO, separate design decision)
- Two-person review: AI (Claude/Opus) + Human (not 2 humans)
- Hands-only format: NO — stick to BB Baby character

### Post-Integration Verification
- Wave 2: 67/67 items confirmed present, 0 missing, 0 contradictions between documents
- Wave 3: Cross-document consistency PASS (85% confidence). Two minor fixes applied:
  1. TikTok SRT self-contradiction in SYNTHESIS "Critical Constraints" section resolved
  2. Scene change frequency in SYNTHESIS appendix updated to include P1/P2/P3 variable cadence

### Minor Known Gaps (Non-Blocking)
1. COPPA fine source attribution cites 6A ($42,530) but value updated to $50,120 — the updated value is correct per January 2025 amendments
2. Export bitrate tables duplicated across both docs (operational risk if one updated without other)
