# Baby Brains Launch Strategy
## January 2026 - Strategic Action Plan

**Created:** January 16, 2026
**Last Updated:** January 30, 2026
**Status:** ACTIVE - Partially Executed (see status update below)
**Owner:** Alexander (Solo Founder)

---

## Executive Summary

You have **exceptional documentation** already prepared. The issue isn't lack of strategy—it's analysis paralysis and scattered priorities. This document consolidates everything into **executable daily tasks** that move the needle.

### Current Reality Check
| Asset | Status (Jan 16) | Status (Jan 30) | Quality |
|-------|-----------------|-----------------|---------|
| Knowledge Graph (125 activities) | 40-50% complete | 40-50% complete | GOLD - continue refining |
| BabyBrains-Writer Voice Spec | Complete (95KB) | Complete (95KB) | EXCELLENT |
| Platform Research | December 2025 | December 2025 | NEEDS UPDATE |
| Social Media Accounts | NOT CREATED | **CREATED** (all 4) | ✅ Done |
| Account Warming | N/A | **NOT CONSISTENT** | ⚠️ Gap — needs automation |
| Video Production Pipeline | NOT TESTED | NOT TESTED | BLOCKING |
| Website | Hero video blocking | Hero video blocking | BLOCKING |
| Agent Knowledge Base | N/A | **COMPLETE** (17 sources) | See `docs/research/AGENT_KNOWLEDGE_BASE.md` |

### January 30 Status Update
**What got done:** Social media accounts created (YouTube, Instagram, TikTok, Facebook). Agent Knowledge Base research completed (17 sources, 284 items, 49 patterns — informs agent architecture). Architecture decisions logged (D96-D99).

**What didn't get done:** Account warming not consistent. Website still not live. Content pipeline not established. No videos produced. No articles started.

**New plan:** Build automation to handle daily account warming (agent-assisted). Build content strategy engine. Build content production pipeline. Unblock website with placeholder. See `atlas-progress.json` tasks bb-1 through bb-5.

### Critical Path (Next 4 Weeks)
1. **Week 1:** Create accounts, begin YouTube incubation, test video workflow
2. **Week 2:** Website live with placeholder, content bank production begins
3. **Week 3:** Account warming (engagement, no posting), refine Knowledge Graph
4. **Week 4:** Soft launch on Instagram/TikTok (3 posts), YouTube continues incubation

---

## Part 1: Research Validation (January 2026 Updates)

### What's Changed Since Your December Research

Your research is **largely still valid** with these refinements:

#### Instagram (Confirmed/Refined)
| Metric | Your Doc | January 2026 Reality | Action |
|--------|----------|---------------------|--------|
| Hashtags | 3-5 max | **3-5 confirmed** - semantic SEO now primary | ✅ No change needed |
| Primary signal | Sends | **Sends confirmed** - 10-20x weight vs likes | ✅ No change needed |
| Morning window | 8-10 AM | **8:30-10 AM AEDT** refined | Minor tweak |
| Trial Reels | Mentioned | **Now mainstream** - use for A/B testing | Add to workflow |
| AI content detection | Not addressed | **Active scanning for AI** - use Descript voice, not synthetic faces | Add safeguard |

#### TikTok (Confirmed/Refined)
| Metric | Your Doc | January 2026 Reality | Action |
|--------|----------|---------------------|--------|
| Caption length | 4,000 chars | **Confirmed** - SEO goldmine | ✅ No change needed |
| Trust Phase | 30-90 days | **Still active** - niche discipline critical | ✅ No change needed |
| Video length | Bifurcated (11-18s + 60s+) | **30-60s now optimal** for engagement + watch time | Adjust to 30-60s primary |
| Hashtags | 3-5 | **1-5 optimal** (reach rate 1.16%) | Slight relaxation |
| File naming SEO | Mentioned | **Critical** - rename files with keywords before upload | Add to production SOP |

#### YouTube (Confirmed/Refined)
| Metric | Your Doc | January 2026 Reality | Action |
|--------|----------|---------------------|--------|
| 3-week incubation | Required | **Still critical** - create channel TODAY | ⚠️ URGENT |
| Sweet spot | 50-70s | **30-60s confirmed** for growth channels | ✅ No change needed |
| Loop mechanics | Important | **Loops count as additional views** - engineer for rewatches | Add to content design |
| Custom thumbnails | Mentioned | **90% of top performers use them** | Add to production SOP |

### Research Prompts to Re-Run

Before finalizing your platform playbooks, re-run these with Opus Research mode. I've refined the prompts:

#### Prompt 1: Instagram Algorithm Refresh (January 2026)
```
Research Task: Instagram Reels Algorithm - January 2026 Update

Context: Australian Montessori parenting brand launching social media. Need to validate December 2025 research.

SPECIFIC QUESTIONS:
1. Has the "Sends" weighting changed since December 2025?
2. What's the exact hashtag limit enforcement (3-5 still correct?)
3. Trial Reels feature status - any updates?
4. AI-generated content detection - what triggers flags?
5. "Your Algorithm" reset feature - still active for January?
6. Australian AEDT optimal posting windows - any January shifts?

Output: Table format comparing December 2025 assumptions vs January 2026 reality with sources.
```

#### Prompt 2: TikTok Trust Phase Validation
```
Research Task: TikTok New Account Strategy - January 2026

Context: Australian Montessori parenting brand launching. Need Trust Phase specifics.

SPECIFIC QUESTIONS:
1. Trust Phase duration for parenting/education niche accounts in 2026?
2. Posting frequency during Trust Phase (2-3/day still recommended?)
3. 4,000 character caption SEO - best practices for education content?
4. Visual AI recognition - how to optimize Montessori material shots?
5. Commercial Music Library status for Australian business accounts?
6. TikTok Shop Australia - current beta status?
7. Under-16 ban enforcement - observable impacts on audience composition?

Output: Actionable checklist with specific numbers.
```

#### Prompt 3: AI Video Generation Current State
```
Research Task: AI Video Generation Tools - January 2026

Context: Solo founder needs affordable, consistent video for Montessori parenting content. Faceless/POV style focusing on hands, materials, environments.

REQUIREMENTS:
- Budget: ~$30-60/month for video gen
- Style: Calm, consistent Montessori aesthetic (natural light, wooden materials)
- Format: 1080x1920 (9:16), 30-60 second clips
- Volume: 10-20 clips/month

SPECIFIC QUESTIONS:
1. Kling AI vs Luma Dream Machine vs Runway - current pricing and best for educational content?
2. Any tools specializing in "hands working" or POV content?
3. API availability for n8n integration?
4. Detection risk - which tools are least likely to trigger "AI content" flags?
5. MidJourney image-to-video vs dedicated video tools - quality comparison?

Output: Recommended tool with pricing breakdown and specific settings for Montessori content.
```

---

## Part 2: Platform Strategy Decision

### Recommendation: Platform Prioritisation

Based on your constraints (4 hours/day, solo founder, AI-generated content):

| Platform | Priority | Role | When to Launch |
|----------|----------|------|----------------|
| **Instagram Reels** | PRIMARY | Authority building, "Sends" optimization | Week 4 (soft launch) |
| **TikTok** | SECONDARY | Discovery, Trust Phase grinding | Week 4 (soft launch) |
| **YouTube Shorts** | TERTIARY | Long-term search SEO, Bridge Strategy | Week 6+ (post-incubation) |
| **Facebook Reels** | AUTOPILOT | Cross-post from Instagram | Auto-publish from Week 4 |

### Why This Order?

1. **Instagram first:** Your audience (Anxious New Parent, 25-35, university-educated) lives here. "Sends" metric aligns with your "share with partner" content strategy.

2. **TikTok parallel:** Toddler Wrangler persona primary. Trust Phase requires consistent niche posting—your Knowledge Graph enables this.

3. **YouTube delayed:** 3-week incubation means you should CREATE IT NOW but not post until February 6+ (if you create it today, January 16).

4. **Facebook auto:** Cross-post from Instagram. 5.91% engagement rate (higher than TikTok's 5.75%). Don't ignore, but don't create separately.

### Content Adaptation Strategy

Same video concept, different execution:

| Element | Instagram | TikTok | YouTube Shorts |
|---------|-----------|--------|----------------|
| **Length** | 30-45s | 30-60s | 50-70s |
| **Hook** | Pattern interrupt (first 1.5s) | Curiosity question | Problem statement |
| **Caption** | 125 chars visible + 3-5 hashtags | 4,000 chars SEO-rich + 3-5 hashtags | Keyword title + 250+ word description |
| **CTA** | "Save for later" (drives Saves) | "Share with your partner" (drives Shares) | "Watch the full guide" (Related Video link) |
| **Music** | Meta Sound Collection | Commercial Music Library | YouTube Audio Library OR ASMR textures |

---

## Part 3: Video Generation Decision

### Current Stack Assessment

| Tool | Current Use | Verdict |
|------|-------------|---------|
| MidJourney ($30/mo) | Images + basic video | **KEEP for images**, video mode insufficient |
| Claude Max ($100/mo) | Writing, strategy | **KEEP** - essential |

### Recommended Video Stack Addition

Based on January 2026 research:

#### Option A: Budget Stack (~$40/mo additional)
| Tool | Cost | Use |
|------|------|-----|
| **Kling AI Standard** | $6.99/mo | Human motion, hands, Montessori materials |
| **Luma Dream Machine Lite** | $29.99/mo | Physics-aware B-roll, keyframe control |
| **TOTAL** | ~$37/mo | |

**Why this combo:**
- Kling excels at realistic hand movements (critical for faceless Montessori content)
- Luma handles keyframes (show "before" → "after" of activity setup)
- Both have API access for future n8n automation

#### Option B: Minimal Test ($10/mo)
| Tool | Cost | Use |
|------|------|-----|
| **Kling AI Standard** | $6.99/mo | Everything |
| **Free tier testing** | $0 | Test Luma/Runway free tiers first |

**Recommendation:** Start with Option B. Test Kling Standard for 2 weeks. Add Luma if you need keyframe/physics features.

### Production Workflow (Proposed)

```
1. SCRIPT (Claude Opus via Skills)
   ↓
2. VISUAL PROMPTS (Extract from script)
   ↓
3. BASE IMAGE (MidJourney - Montessori scene)
   ↓
4. VIDEO (Kling - animate hands/materials)
   ↓
5. VOICEOVER (Descript or consistent AI voice)
   ↓
6. CAPTIONS (Descript auto-captions)
   ↓
7. FINISHING (CapCut - brand fonts, polish)
   ↓
8. EXPORT (Platform-specific versions)
```

### Test Video Task

Before committing to tools, produce ONE test video end-to-end:

**Test Video Brief:**
- Topic: "Why your toddler does the same thing 47 times"
- Length: 45 seconds
- Style: Faceless POV - hands stacking blocks repeatedly
- Voice: Warm Australian (AI or your own voice clone)
- Visual: Child's hands (AI-generated) stacking wooden blocks

**Success Criteria:**
1. Does it look "real enough"? (Show Jade, get honest feedback)
2. Can you produce it in under 2 hours?
3. Would you share it if you saw it?

---

## Part 4: BabyBrains-Writer Voice Assessment

### Verdict: EXCELLENT - Minor Refinements Only

The 95KB agent document is comprehensive and well-designed. Key strengths:
- Cosmic view integration (Maria Montessori's later philosophy)
- Australian authenticity markers
- Em-dash elimination gate
- Evidence tier framework
- 10-step validation chain

### Suggested Refinements

1. **Add "Scrunchy Mom" calibration:**
```markdown
<scrunchy_calibration>
The dominant audience is "Scrunchy" - hybrid crunchy/silky. 
- Acknowledge wooden toys AND screen time reality
- Avoid dogmatic Montessori perfection
- "Pizza night exists in Montessori homes too"
</scrunchy_calibration>
```

2. **Add cost-of-living awareness check:**
```markdown
<budget_check>
Every activity recommendation must pass:
- Can this be done with items already in the home?
- Is there a Kmart/Aldi alternative mentioned?
- Does the expensive option have a DIY version?
</budget_check>
```

3. **Add short-form video calibration:**
```markdown
<short_form_voice>
For 21-60s scripts:
- First 3 words = pattern interrupt
- Sentences max 12 words
- One idea per segment
- End with open loop OR permission statement
</short_form_voice>
```

### How to Implement

Have Opus CLI create a "Voice Spec Addendum" file that gets appended to the agent context when generating short-form content. Don't modify the 95KB master document—extend it.

---

## Part 5: Day-by-Day Action Plan

### Week 1: Foundation (January 16-22)

#### Thursday January 16 (TODAY)
| Time | Task | Tool | Done |
|------|------|------|------|
| 30m | Create YouTube channel | Browser | ☐ |
| 15m | Phone verify YouTube | Phone | ☐ |
| 30m | Create Instagram account (Creator) | Browser | ☐ |
| 30m | Create TikTok account (Business) | Browser | ☐ |
| 30m | Create Facebook Page | Browser | ☐ |
| 15m | Link Instagram to Facebook Page | Browser | ☐ |

**YouTube Incubation Starts TODAY - No posting until February 6**

#### Friday January 17
| Time | Task | Tool | Done |
|------|------|------|------|
| 30m | YouTube incubation: Watch 5 parenting videos, like 3, subscribe 2 | YouTube | ☐ |
| 30m | Sign up for Kling AI Standard ($6.99) | Browser | ☐ |
| 2h | Test video generation: "Hands stacking blocks" prompt | Kling AI | ☐ |
| 1h | Evaluate output quality | Personal judgment | ☐ |

#### Saturday January 18
| Time | Task | Tool | Done |
|------|------|------|------|
| 30m | YouTube incubation: Watch 5 more, engage | YouTube | ☐ |
| 2h | Website: Replace hero video with static image placeholder | DaVinci/Code | ☐ |
| 1h | Website: Verify all pages functional | Browser | ☐ |
| 30m | Knowledge Graph: Continue activity refinement | Claude Skills | ☐ |

#### Sunday January 19
| Time | Task | Tool | Done |
|------|------|------|------|
| 30m | YouTube incubation | YouTube | ☐ |
| 2h | Knowledge Graph: Refine 3 activities | Claude Skills | ☐ |
| 1h | Run research prompt #1 (Instagram refresh) | Opus Research | ☐ |
| 30m | Review Instagram research output | Personal | ☐ |

#### Monday January 20
| Time | Task | Tool | Done |
|------|------|------|------|
| 30m | YouTube incubation | YouTube | ☐ |
| 1h | Run research prompt #2 (TikTok Trust Phase) | Opus Research | ☐ |
| 2h | Create first FULL test video end-to-end | Full workflow | ☐ |
| 30m | Show test video to Jade, get feedback | In-person | ☐ |

#### Tuesday January 21
| Time | Task | Tool | Done |
|------|------|------|------|
| 30m | YouTube incubation | YouTube | ☐ |
| 1h | Run research prompt #3 (AI Video Tools) | Opus Research | ☐ |
| 2h | Iterate test video based on feedback | Full workflow | ☐ |
| 30m | Update PLATFORM-PLAYBOOKS.md with research findings | Claude CLI | ☐ |

#### Wednesday January 22
| Time | Task | Tool | Done |
|------|------|------|------|
| 30m | YouTube incubation | YouTube | ☐ |
| 2h | Knowledge Graph: Refine 3 more activities | Claude Skills | ☐ |
| 1h | Website: Final testing | Browser | ☐ |
| 30m | Set website LIVE (even if imperfect) | Deployment | ☐ |

**Week 1 Checkpoint:**
- ☐ All 4 social accounts created
- ☐ YouTube incubation ongoing (7 days complete)
- ☐ Video workflow tested with 1-2 test pieces
- ☐ Website LIVE with placeholder hero
- ☐ Research prompts run, docs updated

---

### Week 2: Content Bank Production (January 23-29)

**Daily recurring:**
- 30m YouTube incubation (watch, like, subscribe)
- 30m Account warming on Instagram/TikTok (follow 5-10 parenting accounts, like/comment on 10 posts)

#### Week 2 Production Target
| Content Type | Quantity | Status |
|--------------|----------|--------|
| 30-45s Reels scripts | 8 | ☐ |
| Rendered videos | 5 | ☐ |
| Knowledge Graph activities refined | 10 | ☐ |

**Focus Topics for First 5 Videos:**
1. "Why your toddler does the same thing 47 times" (Repetition/brain building)
2. "Your baby isn't broken. Here's why they..." (Normalizing behavior)
3. "The 3am panic: What's actually happening" (Sleep reassurance)
4. "Montessori on a budget: What you actually need" (Budget pillar)
5. "Why 'good job' might not be helping" (Gentle controversy)

---

### Week 3: Account Warming (January 30 - February 5)

**NO POSTING YET** - just engagement

**Daily:**
- 30m YouTube incubation (continues)
- 1h Instagram: Comment on 20 posts in #montessoriaustralia, #australianparents
- 1h TikTok: Watch parenting content, comment thoughtfully, follow creators
- 2h Knowledge Graph refinement OR content production

**Week 3 Production Target:**
| Content Type | Quantity | Status |
|--------------|----------|--------|
| Additional scripts | 10 | ☐ |
| Rendered videos in bank | 12-15 total | ☐ |
| Knowledge Graph at | 60%+ | ☐ |

---

### Week 4: Soft Launch (February 6-12)

**YouTube incubation COMPLETE on February 6** (if created January 16)

#### February 6 (Thursday) - LAUNCH DAY
| Time | Task | Platform | Done |
|------|------|----------|------|
| 8:30 AM AEDT | Post Reel #1 | Instagram | ☐ |
| 11:00 AM AEDT | Post video #1 | TikTok | ☐ |
| Auto | Cross-post to Facebook | Facebook | ☐ |
| Evening | Respond to ALL comments | Both | ☐ |

#### Week 4 Posting Schedule
| Day | Instagram | TikTok | YouTube |
|-----|-----------|--------|---------|
| Thu Feb 6 | Post #1 | Post #1 | NO (wait) |
| Fri Feb 7 | Engage only | Engage only | Post #1 (first Short) |
| Sat Feb 8 | Post #2 | Post #2 | Engage only |
| Sun Feb 9 | Engage only | Engage only | Engage only |
| Mon Feb 10 | Post #3 | Post #3 | Post #2 |
| Tue Feb 11 | Engage only | Engage only | Engage only |
| Wed Feb 12 | Post #4 | Post #4 | Post #3 |

**Week 4 Target: 4 posts per platform (except YouTube: 3)**

---

## Part 6: Metrics to Track

### Week 4+ Key Metrics

| Metric | Instagram | TikTok | YouTube | Target |
|--------|-----------|--------|---------|--------|
| Sends/Shares | PRIMARY | PRIMARY | N/A | Track per post |
| Watch Time | Track | Track | PRIMARY | >50% completion |
| Saves | Track | Track | Track | 5%+ of views |
| Followers gained | Track | Track | Track | +50/week minimum |
| Bio link clicks | Track | Track | Track | 2%+ of profile visits |

### Monthly Review Questions
1. Which hook types drove most Sends?
2. Which topics drove most Saves?
3. What time of day performed best?
4. AI video quality: Any comments/concerns?
5. Burnout check: Is cadence sustainable?

---

## Part 7: Risk Mitigation Reminders

### Top 5 Risks (from your docs)

| Risk | Mitigation | Status |
|------|------------|--------|
| Jade employment contract | Ghost support only, no public attribution | ACTIVE |
| Solo founder burnout | 1/day max sustainable cadence | PLANNED |
| AI video detection | Use voiceover, avoid synthetic faces | PLANNED |
| YouTube shadow-ban | 3-week incubation (START TODAY) | ⚠️ URGENT |
| TikTok Trust Phase confusion | Stick to Montessori/parenting only for 90 days | PLANNED |

---

## Part 8: Document Updates Needed

Have Opus CLI make these updates to your existing docs:

### PLATFORM-PLAYBOOKS.md Updates
1. Line 20: Change "5-10 hashtags" → "3-5 hashtags (platform-enforced limit)"
2. Line 17: Change TikTok "21-34s" → "30-60s optimal for engagement"
3. Line 18: Change TikTok caption "2,200 chars" → "4,000 chars"
4. Line 23: Change Instagram morning "6-9 AM" → "8:30-10 AM"
5. Add new section: "YouTube 3-Week Incubation Protocol"

### SOCIAL-MEDIA-STRATEGY.md Updates
1. Reconcile cadence_policy.md conflict (2-3/week) with aspirational (1-2/day)
   - Recommendation: "Phase 1: 4-5/week total across platforms. Phase 2 (Month 3+): Increase to 1/day if sustainable."

### New Documents Needed
1. `PRODUCTION-SOP.md` - Step-by-step video production workflow
2. `CONTENT-BANK-TRACKER.md` - Track what's produced vs. posted
3. `TOOL-STACK.md` - Current subscriptions and costs

---

## Quick Reference: Today's Actions

### Absolute Minimum (If You Only Have 2 Hours)

1. **Create YouTube channel** (15 min) - MOST URGENT, incubation starts now
2. **Create Instagram account** (10 min)
3. **Create TikTok account** (10 min)
4. **YouTube incubation** (30 min) - watch parenting videos, engage
5. **Sign up Kling AI Standard** (10 min)
6. **Test one video generation** (45 min)

### If You Have Full 4 Hours

All of the above, plus:
- Create Facebook Page and link to Instagram
- Run first research prompt (Instagram refresh)
- Begin first test video script using BabyBrains-Writer

---

## Summary: The Path Forward

**You have done the hard strategic work.** Your documentation is excellent. What you need now is:

1. **Execution over analysis** - Stop refining, start creating
2. **Imperfect action** - Ship the website with a placeholder hero
3. **Trust the systems you built** - The Knowledge Graph + BabyBrains-Writer will produce quality
4. **Sustainable pace** - 4-5 posts/week, not 1-3/day

The needle moves when content goes live. Everything else is preparation.

**Start the YouTube incubation clock TODAY.**

---

*Document created by Strategic Launch Advisor. Execute with confidence.*
