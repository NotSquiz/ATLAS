# Baby Brains Automation System - Full Architecture Plan (v2)

**Scope:** Complete Baby Brains agent system -- warming, trends, content pipeline, cross-repo intelligence
**Status:** Week 1 COMPLETE (S1.1-S1.8, 98 tests). Week 2 ready pending stealth research + API keys.
**Key Change from v1:** Integrated findings from 6 repos, proper warming pipeline design, Claude Max ($0 LLM), cross-repo knowledge map

---

## KB Audit Findings (January 31, 2026)

Cross-referenced against 22-source Agent Knowledge Base (S1-S22). Key findings:

| Finding | KB Source | Impact on Plan | Status |
|---------|-----------|---------------|--------|
| Self-review degrades quality (same model generate + evaluate = 60% error) | P54, S20 | Comment pipeline uses regex gate (good). Add independent Haiku critic when scaling | NOTED — human review mitigates for now |
| Opposing incentives create coherence (92.1% vs 60% single-agent) | P53, S20 | Content pipeline (Week 3) should have brand-safety vs engagement agents | DEFERRED to Week 3 |
| Browser automation detected at infrastructure level | D102, P54 | Stealth patches mandatory for S2.1-S2.3. See `docs/BROWSER_STEALTH_RESEARCH.md` | ADDED to sprint tasks |
| Plugin architecture is canonical (skills+commands+connectors+sub-agents) | P50, S18 | Current BB module is monolithic package. Refactor to plugins post-Sprint 3 | DEFERRED (A53) |
| MCP Tool Search saves 85% tokens as tool count grows | P51, S18 | 14 new BB tools will push total past 20. Evaluate before Sprint 3 | DEFERRED (A54) |
| Agentic image gen for BB carousels ($0.04-0.13/image) | P52, S19 | S3.3 visual_generator should evaluate Nano Banana Pro before MidJourney | NOTED for Week 3 |
| Human story deferred | D103 | Comment generator handles gracefully (0% personal angle). Fill later | DEFERRED |
| Account warming reset | D105 | Accounts not consistently warmed. Treat pipeline start as Day 1 | ADDED S0.1 task |

---

## What Changed from v1

1. **Cross-repo intelligence** -- 5 active repos mapped (educational-research archived/ignored), orchestrator knows where everything is
2. **Fully autonomous warming** -- Playwright watches, likes, subscribes, AND comments. Zero human involvement.
3. **Dual-mode Claude** -- Max ($0) for interactive, Sonnet API (~$1-3/mo) for automated cron/daemon tasks
4. **Platform research integrated** -- YouTube 21-day incubation, Instagram Sends KPI, TikTok Trust Phase
5. **Approved cadence** -- IG 1/day (6 days), TikTok 1/day (7 days), YT 3/week (per strategic-decisions.md)
6. **AI-only content** -- All content fully AI-generated, no human filming (per strategic-decisions.md)
7. **BabyBrains-Writer comment skill** -- Transcript-aware commenting via Sonnet API, quality gated
8. **Content stack NOT proven** -- Video generation tools need proper research (realistic family/baby footage)
9. **Platform algo index needed** -- Cross-platform algorithm rules indexed for orchestrator brain

## Open Issues (Must Resolve During Build)

### Issue 1: Content Generation Stack is UNPROVEN
The Dec 2025 production-tools research recommended Luma Dream Machine + Kling AI, but this has **NOT been tested**. We need realistic-looking footage of:
- Families at home
- Babies crawling, playing, reaching
- Specific activities (pouring, stacking, tummy time)
- Prepared environments (shelves, floor beds, art areas)

**Action:** Day 5 includes a proper research + testing phase for AI video generation tools. Must evaluate: Luma, Kling, Runway, Pika, Sora (if available), HailuoAI, and any newer entrants. Criteria: realism of baby/family footage, cost, API availability, consistency across clips. This is a blocking dependency for the content pipeline.

### Issue 2: Platform Algorithm Index
Each platform has different algo requirements (posting times, hashtag limits, caption lengths, hook timing, engagement signals). This research EXISTS scattered across `babybrains-os/docs/research/*.md` and `babybrains-os/docs/PLATFORM-PLAYBOOKS.md` but needs to be indexed into a structured config that the orchestrator can query. **Action:** Day 1 includes extracting platform rules into `config/babybrains/platforms.json` from existing research docs.

### Issue 3: System Rename (ATLAS -> Astro)
User wants to rename the system. Leaning toward **Astro** as the user-facing name, with **MAGI** (Neon Genesis inspired, three-brain debate architecture) potentially as the internal architecture name. "Astro runs on MAGI." This is a significant refactoring task (code, configs, docs, file paths, module names). **NOT blocking Day 1-7 build** -- we build the BB module now under current naming, then do the rename as a separate focused task. Noted and prepped for.

---

## Architecture Decisions (D100-D106)

### D100: Primary Interface -- Claude Code MCP Tools + CLI
You already live in Claude Code. Adding BB tools to the existing ATLAS MCP server gives you natural language access with zero new tooling.

- **PRIMARY:** Claude Code / Claude Desktop via MCP tools (14 new tools)
- **SECONDARY:** CLI commands (`python -m atlas.babybrains.cli warming daily`)
- **TERTIARY:** Telegram bot for mobile push notifications (Day 7)
- **VOICE:** Add "Baby Brains status" as 0-token intent to existing voice bridge

### D101: Dual-Mode Claude (Max for interactive, API for automation)
Two modes of Claude usage, optimized for cost and capability:

- **Interactive work** (content briefs, scripts, strategy): Claude Code CLI via Max subscription ($0)
- **Automated tasks** (comment generation, transcript analysis, cron jobs): Anthropic API with Sonnet, token-optimized ($1-3/mo)

The API is needed for cron jobs and daemon processes that run without a human session. Sonnet is the right model for comments -- fast, cheap, good enough with proper guardrails. Opus reserved for strategy/planning when you're in Claude Code.

```
Claude Code CLI (Max)  = Interactive Brain  -> Scripts, briefs, strategy, quality review ($0)
Anthropic API (Sonnet) = Automation Brain   -> Comments, transcript analysis, cron tasks (~$1-3/mo)
Grok API ($0.20/M)     = X.com Eyes         -> Trending topics, competitor analysis
YouTube Data API       = Video Eyes         -> Trending parenting videos, transcript fetch
Reddit API (PRAW)      = Forum Eyes         -> Community discussions, pain points
Google Trends          = Search Eyes        -> Rising search terms
Local regex            = Router             -> Existing 0-token intent matching
```

Total monthly cost: ~$8-15 (Sonnet API + Grok + YouTube). Interactive Claude operations = $0.

### D102: Warming Pipeline (Auto-Watch + Human-Post Comments)
**AUDIT FINDING (Jan 30, 2026):** Two independent audits confirmed that automated comment posting via Playwright will result in permanent account termination on YouTube and Instagram. YouTube's AI moderation (strengthened Dec 2025) detects browser automation at the infrastructure level, not by reading comment content. Accounts are terminated without human review. This is an existential risk for a pre-launch brand.

**DECISION:** Auto-watch, auto-like, auto-subscribe via Playwright. Comments generated by Sonnet API but HUMAN-POSTED (copy-paste from terminal). ~15 min/day human effort. Accounts survive.

**LLM for Comment Drafts:** Anthropic API (Sonnet) with token-optimized prompts. Cost: ~$8-15/month total (comments + trend analysis + briefs).

**The Pipeline:**
```
1. Target Generation (6:30 AM cron, automated)
   -> YouTube Data API + Grok scan for relevant parenting content
   -> Score each target: niche fit, channel quality, engagement opportunity
   -> Generate prioritized target list (5-10 per platform per day)

2. Video Analysis + Comment Draft (automated, Sonnet API)
   -> Fetch video transcript (youtube-transcript-api / YouTube Data API captions)
   -> Sonnet analyzes: topic relevance, key claims, emotional hooks, BB angle
   -> Cross-reference with Knowledge Graph (where coverage exists, fallback to general)
   -> Generate BB-voice comment draft (transcript-aware, knowledge-backed)
   -> Quality gate: em-dash check, voice spec validation, length check

3. Browser Automation (Playwright headed Chrome via WSLg, automated)
   -> STEALTH REQUIRED: See docs/BROWSER_STEALTH_RESEARCH.md
   -> Use system Chrome (channel="chrome"), NOT bundled Chromium
   -> Persistent browser profile (cookies/history survive between sessions)
   -> Open video in real Chrome window
   -> Watch for 60-300s (longer = higher quality/relevance score)
   -> Random variance: +/- 15% of target watch time (gaussian distribution)
   -> Humanized mouse movements + random scrolling during watch
   -> Like if engagement_level >= LIKE (random 2-5s delay after watch)
   -> Subscribe if engagement_level >= SUBSCRIBE (max 2/day, after 90s+ watch)
   -> Random inter-video delay: 30-120s between targets (gaussian, not uniform)
   -> Circuit breaker: stop if 3 consecutive failures
   -> Anti-detection: navigator.webdriver masked, fingerprint validated

4. Comment Review + Post (HUMAN, ~15 min/day)
   -> "bb warming daily" shows: video title, transcript summary, drafted comment
   -> User reviews/edits comment in terminal
   -> User copy-pastes into real browser tab (already open from Playwright session)
   -> "bb warming done youtube 3 comments, 2 likes, 1 subscribe"

5. Learning Loop (Week 2+)
   -> Track which comments get engagement (manual input via bb_warming_done)
   -> Adjust comment generation prompts based on patterns
```

| Action | Method | Risk |
|--------|--------|------|
| Watch videos | Playwright headed Chrome (60-300s) | VERY LOW |
| Like after watching | Playwright (random delay) | LOW |
| Subscribe | Playwright (max 2/day, quality check) | LOW |
| Comment (YouTube) | **HUMAN** copy-paste from AI-drafted text | NONE |
| Comment (Instagram) | **HUMAN** copy-paste from AI-drafted text | NONE |
| Instagram like/follow | Playwright (rate limited) | LOW |

### D103: BabyBrains-Writer Comment Skill (Knowledge-Backed + Human Story)
Comments are NOT templated. Each comment is generated fresh from THREE layers:

**Layer 1: Knowledge Base (what we actually know)**
- The video's actual transcript (fetched via YouTube API or Whisper)
- Cross-referenced with our Knowledge Graph source material at `/home/squiz/code/knowledge/`:
  - **Original Maria Montessori texts** (`sources/raw_extractions/maria_primary/`):
    - The Absorbent Mind (content analysis + guidance extraction)
    - The Secret of Childhood (content analysis + guidance extraction)
    - The Child in the Family (content analysis)
    - Education and Peace (content analysis)
  - **Modern Montessori books** (`sources/raw_extractions/other/`):
    - The Joyful Child (5 extraction categories: guidance, environment, adult prep, interaction, troubleshooting)
    - Montessori from the Start (5 extraction categories)
    - Understanding the Human Being (5 extraction categories)
  - **53 structured source files** across philosophy, activities, guidance
  - **Activity canonicals** (`master_index/` -- 125+ activities, growing)
  - **Research findings** (`docs/research/RP01-RP18` -- 18 research results)
  - **Evidence registry** (`evidence/GUIDELINE_REGISTRY.yaml` -- AU guidelines with URLs)
- Comments cite real knowledge, not generic advice. If a video discusses tummy time, our comment references what we actually know from our Montessori source extractions.

**Layer 2: Voice Spec (how we say it)**
- BabyBrains-Writer voice spec (1712 lines, loaded from `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md`)
- AU English, anti-superlative, calm competence tone
- Platform-specific length/style rules

**Layer 3: Human Story (who we are)**
- We are a real family. Father, partner, 16-month-old son.
- No big company, limited funds and time.
- Wanting to do the best with the information scattered around the internet.
- Researching Montessori, neuroscience, and respectful parenting because we're living it.
- Comments should sometimes reflect this human element when appropriate:
  - "We found this with our little one too..." (shared experience)
  - "This is something we've been researching..." (learning journey)
  - "As a dad trying to figure this out..." (vulnerability/authenticity)
  - Not every comment needs the personal angle -- maybe 30-40% do.
  - The rest are knowledge-grounded observations or encouragements.

**The Human Story Profile:**
NOTE: The profile below is a PLACEHOLDER SKELETON. It is NOT the basis of truth. A proper human story must be crafted as a dedicated task (Sprint S1.2 will include a prompt for the user to flesh this out). The comment system must NOT use this placeholder as-is -- it needs the real, complete story before generating personal-angle comments.

```yaml
bb_human_story:
  # PLACEHOLDER - User must complete before personal-angle comments go live
  who: "TBD - needs proper crafting"
  child: "TBD"
  motivation: "TBD"
  background: "TBD"
  credibility: "TBD"
  tone: "Learning alongside other parents, not preaching from above"
  vulnerability: "TBD"
  partner: "TBD"
  status: "INCOMPLETE - DO NOT USE FOR COMMENT GENERATION UNTIL CRAFTED"
```

**Comment Generation Rules (from Voice Spec):**
- Em-dashes FORBIDDEN (the #1 AI tell)
- No formal transitions (Moreover, Furthermore, etc.)
- Contractions always (you're, it's, we've)
- Australian vocabulary (mum, nappy, pram, kindy)
- Grade 8 reading level
- Cost-of-living aware (lead with free/DIY)
- Vary length: some short (1-2 sentences), some medium (3-4 sentences)
- ~30-40% of comments include personal/human element
- ~60-70% are knowledge-grounded observations or encouragements
- Never preachy, never guru-positioning
- Never mention partner's credentials publicly (employment contract)

### D104: Cross-Repo Knowledge Map
The orchestrator brain knows where everything is across all 6 repositories:

```
/home/squiz/code/
├── ATLAS/                          # THIS REPO - Personal AI + BB Agent (rename to Astro pending)
│   ├── atlas/babybrains/           # NEW: BB automation module
│   ├── atlas/mcp/server.py         # MCP tools (existing + new BB tools)
│   ├── docs/research/              # Agent Knowledge Base (17 sources)
│   └── docs/BABY-BRAINS-LAUNCH-STRATEGY-JAN2026.md
│
├── babybrains-os/                  # Marketing agent v2.2
│   ├── docs/SOCIAL-MEDIA-STRATEGY.md
│   ├── docs/PLATFORM-PLAYBOOKS.md
│   ├── docs/AUDIENCE-SEGMENTATION.md
│   ├── docs/strategic-review/09-strategic-decisions.md  # AUTHORITATIVE
│   ├── docs/research/instagram-dec-2025.md
│   ├── docs/research/tiktok-dec-2025.md
│   ├── docs/research/youtube-dec-2025.md
│   ├── docs/research/au-parenting-landscape.md
│   ├── docs/research/production-tools-dec-2025.md
│   ├── skills/                     # 9-skill content pipeline
│   └── qc/                         # Quality control rules
│
├── knowledge/                      # Master Index / Knowledge Graph (~55-58% complete)
│   ├── docs/overview/SYNTHESIS_SUMMARY*.md
│   ├── docs/overview/WEBSITE_MARKETING*.md
│   ├── docs/research/RP01-RP18     # 18 research results
│   ├── docs/research-prompts/      # 18 research prompts
│   └── docs/planning/              # 90+ planning stories
│
├── web/                            # Next.js website
│   ├── .claude/agents/BabyBrains-Writer.md  # 1712-line voice spec
│   ├── .claude/agents/content-reviewer.md   # E-E-A-T review
│   ├── .claude/agents/editorial-qa-automator.md
│   └── docs/BABY-BRAINS-CANONICAL-SPEC.md
│
├── app/                            # Mobile app (documented, not built)
│
└── educational-research/           # ARCHIVED -- useful data migrated to /knowledge. IGNORE.
```

**New MCP tool: `bb_find_doc(topic)`** -- Searches across all 6 repos for relevant strategy/research docs. Returns file paths + summaries. This is the cross-repo brain.

### D105: Platform-Aware Strategy (Dec 2025 Research Integrated)

**YouTube (from youtube-dec-2025.md):**
- **21-day incubation**: New channels must NOT post for 21 days. Engage/consume only during this period.
- **Loop mechanics**: Each replay counts as additional view. Design for "Perfect Loop".
- **50-70s sweet spot**: Avoids 90-120s dead zone.
- **Bridge Strategy**: Use "Related Video" links to convert Shorts viewers to long-form.

**Instagram (from instagram-dec-2025.md):**
- **"Sends" are primary signal**: DM shares weighted 10-20x higher than likes.
- **3-5 hashtags max** (down from 5-10). Semantic SEO replaces hashtag stuffing.
- **Prime time: 7-9:30 PM AEDT** ("Revenge Bedtime" window).
- **Trial Reels**: A/B test with non-followers before committing to feed.
- **Bimodal length**: 15-30s for cold reach, 60-90s for community retention.

**TikTok (from tiktok-dec-2025.md):**
- **Trust Phase (30-90 days)**: Strict niche discipline, 2-3 posts/day during sandbox.
- **4,000-char captions**: TikTok is now a micro-blogging platform.
- **Three-tier length**: 11-18s (viral reach), 21-34s (storytelling), 60s+ (educational depth).
- **Visual AI recognition**: Platform AI scans video frames for categorization.
- **File naming SEO**: Rename video files with keywords before upload.

### D106: Batch Async Architecture
Every pipeline follows: scheduled generation -> human review -> manual execution. Matches Theme 1 from synthesis (async delegation = THE use case).

---

## System Diagram

```
USER INTERFACES
  Claude Code ──────┐
  Claude Desktop ───┤── ATLAS MCP Server (atlas/mcp/server.py)
  Terminal CLI ─────┤     12 EXISTING tools + 14 NEW BB tools
  Telegram (Day 7) ─┘

                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌─────────────┐ ┌──────────┐ ┌────────────┐
   │ BB Warming  │ │ BB Trend │ │ BB Content │
   │ Service     │ │ Engine   │ │ Pipeline   │
   │             │ │          │ │            │
   │ targets()   │ │ scan()   │ │ brief()    │
   │ watch()     │ │ score()  │ │ script()   │
   │ comments()  │ │ match()  │ │ visuals()  │
   │ log_done()  │ │          │ │ export()   │
   └──────┬──────┘ └────┬─────┘ └─────┬──────┘
          │              │             │
   ┌──────┴──────────────┴─────────────┴──────┐
   │              CROSS-REPO BRAIN              │
   │  bb_find_doc()  → Search 6 repos          │
   │  voice_spec.py  → Load BabyBrains-Writer  │
   │  platform_rules → Dec 2025 research       │
   └──────────────────────┬────────────────────┘
          │              │             │
   ┌──────┴──────────────┴─────────────┴──────┐
   │              API CLIENTS                   │
   │  GrokClient      (X.com search)           │
   │  YouTubeClient   (Data API v3 + captions) │
   │  RedditClient    (PRAW async)             │
   │  GoogleTrendsClient (pytrends)            │
   │  Playwright      (headed Chrome warming)  │
   │  Claude Code CLI (Max, $0 brain)          │
   └──────────────────────┬────────────────────┘
                          │
   ┌──────────────────────┴────────────────────┐
   │         ATLAS DATABASE (atlas.db)          │
   │  EXISTING: semantic_memory, daily_metrics  │
   │  NEW: bb_warming_targets                   │
   │       bb_warming_actions                   │
   │       bb_accounts                          │
   │       bb_trends                            │
   │       bb_content_briefs                    │
   │       bb_scripts                           │
   │       bb_visual_assets                     │
   │       bb_exports                           │
   │       bb_engagement_log                    │
   │       bb_cross_repo_index                  │
   └────────────────────────────────────────────┘
```

---

## Daily User Workflow (What Your Day Looks Like)

```
 6:30 AM  [AUTO] bb_morning_prep
          -> Generates warming targets from overnight trend scan
          -> Fetches video transcripts for top targets
          -> Generates BB-voice comments (transcript-aware)
          -> Determines engagement levels per target

 7:00 AM  [AUTO] daily_digest now includes BB status

 8:00 AM  [AUTO] bb_trend_scan
          -> Grok/YouTube/Reddit/Google aggregation
          -> Cross-references with Knowledge Graph topics
          -> Scores opportunities against audience segments

 9:00 AM  [AUTO] Playwright watches/likes/subscribes in background (~60-90 min)

 9:30 AM  [YOU]  "bb warming daily" (~15 min)
          -> See targets with pre-written BB-voice comments
          -> Review/edit comments, copy-paste into browser tabs
          -> "bb warming done youtube 3 comments, 1 subscribe"

 2:00 PM  [YOU]  "bb trending topics" -> see scored trends
          [YOU]  "bb content brief 'toddler repetition'" -> brief with hooks + evidence
          [YOU]  "bb generate script brief_id=42 format=60s" -> full BB-voice script
          [YOU]  "bb generate visuals script_id=87" -> MidJourney + Kling prompts
          [YOU]  Paste prompts into MidJourney/Kling, assemble in CapCut
          [YOU]  "bb export script_id=87" -> platform-specific captions + hashtags

 5:00 PM  [AUTO] Telegram: "2 items in review queue"
 8:00 PM  [YOU]  "bb status" -> warming progress, content pipeline, trends
```

---

## Module Structure (New Files)

```
atlas/babybrains/                     # NEW MODULE
├── __init__.py
├── models.py                         # Dataclasses: WarmingTarget, TrendResult, ContentBrief, etc.
├── schema.sql                        # 10 new BB tables
├── db.py                             # DB init + query helpers
├── voice_spec.py                     # Load + section-extract from BabyBrains-Writer.md
├── cross_repo.py                     # Cross-repo document search + index
├── cli.py                            # CLI: python -m atlas.babybrains.cli
├── warming/
│   ├── __init__.py
│   ├── service.py                    # WarmingService: orchestrate daily warming
│   ├── targets.py                    # Target generation from trend data
│   ├── comments.py                   # Comment generation using BB voice spec + transcript
│   ├── browser.py                    # Playwright headed Chrome: watch, like, subscribe
│   └── transcript.py                 # YouTube transcript fetching (API + Whisper fallback)
├── trends/
│   ├── __init__.py
│   ├── engine.py                     # TrendEngine: aggregate + score all sources
│   ├── aggregator.py                 # Cross-source dedup + scoring
│   └── scorer.py                     # Opportunity scoring (niche fit, gap analysis)
├── content/
│   ├── __init__.py
│   ├── brief_generator.py            # Content briefs from trends
│   ├── script_generator.py           # Video scripts (21s/60s) using BB voice spec
│   ├── visual_generator.py           # MidJourney + Kling prompt extraction
│   ├── caption_generator.py          # Platform-specific captions + hashtags
│   └── exporter.py                   # Full platform export packaging
└── clients/
    ├── __init__.py
    ├── grok_client.py                # xAI Grok API
    ├── youtube_client.py             # YouTube Data API v3 (search + captions)
    ├── reddit_client.py              # Reddit PRAW async wrapper
    └── google_trends_client.py       # pytrends async wrapper

config/babybrains/                    # NEW CONFIGS
├── platforms.json                    # Platform rules (from Dec 2025 research)
├── warming_schedule.json             # Daily targets per platform, warming phases
├── warming_engagement_rules.json     # Watch time, like/subscribe thresholds
├── trend_queries.json                # Default search queries per source
├── competitors.json                  # Competitor accounts to monitor
├── audience_segments.json            # 5 personas from AUDIENCE-SEGMENTATION.md
└── cross_repo_paths.json             # Maps topics to file paths across 6 repos

MODIFIED FILES:
├── atlas/mcp/server.py               # Add 14 BB tools
├── atlas/scheduler/loop.py           # Add 6 BB scheduled tasks
├── .env                              # Add: GROK_API_KEY, YOUTUBE_API_KEY, REDDIT_CLIENT_ID/SECRET
```

---

## 14 New MCP Tools

```python
# Warming (4)
bb_warming_daily(platform?)         -> Today's targets with transcript-aware BB-voice comments
bb_warming_watch(platform?)         -> Launch Playwright to watch/like/subscribe targets
bb_warming_done(platform, actions)  -> Log completed warming actions
bb_warming_status()                 -> Progress dashboard (days, actions, growth)

# Trends (1)
bb_trend_scan(force?)               -> Run full trend scan (cached unless force=True)

# Content (5)
bb_content_brief(topic, trend_id?)  -> Generate brief with hooks, evidence, visuals
bb_generate_script(brief_id, fmt)   -> Generate video script (21s/60s/article)
bb_generate_visuals(script_id)      -> MidJourney + Kling prompts from script
bb_export_platform(script_id, plat) -> Platform-specific captions + hashtags
bb_review_queue()                   -> Show all items pending review

# Management (3)
bb_review_item(type, id, action)    -> Approve/reject/revise content items
bb_status()                         -> Full dashboard: warming + content + trends
bb_calendar(days?)                  -> Content calendar for next N days

# Cross-Repo Intelligence (1)
bb_find_doc(topic)                  -> Search all 6 repos for relevant strategy/research docs
```

---

## Database Schema (10 New Tables)

- `bb_accounts` -- Platform accounts being warmed (platform, handle, status, followers, incubation_end_date)
- `bb_warming_targets` -- Daily targets (url, channel, transcript_summary, suggested_comment, engagement_level, watch_duration_target)
- `bb_warming_actions` -- Actions taken (target_id, action_type, content_posted, actual_watch_seconds, time_spent)
- `bb_engagement_log` -- Weekly snapshots (followers, engagement_rate, impressions, sends_count)
- `bb_trends` -- Trend scan results (topic, score, sources JSON, opportunity_level, audience_segment)
- `bb_content_briefs` -- Content briefs (hooks, core_message, evidence, visual_concepts, knowledge_graph_refs)
- `bb_scripts` -- Video scripts (script_text, voiceover, word_count, format_type, captions per platform)
- `bb_visual_assets` -- MidJourney/Kling prompts and file paths
- `bb_exports` -- Platform-specific export packages (scheduled, published, performance_data)
- `bb_cross_repo_index` -- Maps topics to file paths across 6 repos (topic, repo, file_path, summary, last_indexed)

---

## API Key Setup (Day 1)

```bash
# Add to /home/squiz/ATLAS/.env:
GROK_API_KEY=           # Sign up: console.x.ai ($5 free credit)
YOUTUBE_API_KEY=        # Google Cloud Console -> YouTube Data API v3 (free, 10K units/day)
REDDIT_CLIENT_ID=       # reddit.com/prefs/apps -> Create "script" app (free)
REDDIT_CLIENT_SECRET=   # Same as above
```

Claude operations: $0 (Max subscription via Claude Code CLI).
All clients degrade gracefully if keys missing.

---

## 3-Week Build Plan (Audit-Adjusted)

**Audit finding:** 7-day timeline was 4-6x too aggressive. Restructured into 3 focused weeks with clear gates.

### Week 1: Foundation + Warming MVP (Sprint 1)
| Task | What Gets Built | Gate |
|------|----------------|------|
| **S1.1** | Schema (10 tables), models (dataclasses), db.py | Tables created, tests pass |
| **S1.2** | voice_spec.py (load BabyBrains-Writer.md), human_story profile | Voice spec sections extractable |
| **S1.3** | cross_repo.py + cross_repo_paths.json (static path map) | `bb_find_doc` returns results |
| **S1.4** | Platform configs from Dec 2025 research (platforms.json, warming_schedule.json) | Configs loadable |
| **S1.5** | `bb_status` + `bb_find_doc` MCP tools | Tools work in Claude Code |
| **S1.6** | transcript.py (youtube-transcript-api + fallback) | Transcripts fetched for 20 test videos |
| **S1.7** | comments.py (Sonnet API + voice spec + knowledge + human story) | Comments pass voice spec quality gate |
| **S1.8** | WarmingService + `bb_warming_daily` MCP tool + CLI | **GATE: Type `bb warming daily`, see targets with comments** |

### Week 2: Browser Automation + Trend Engine (Sprint 2)
| Task | What Gets Built | Gate |
|------|----------------|------|
| **S2.1** | Validate WSLg/headed Chrome on WSL2 (spike test) | Chrome window opens or fallback plan |
| **S2.2** | browser.py (Playwright: watch, like, subscribe) | Videos watched automatically |
| **S2.3** | `bb_warming_watch` + `bb_warming_done` MCP tools | Full warming workflow operational |
| **S2.4** | YouTubeClient (Data API v3: search + captions) | YouTube search returns results |
| **S2.5** | GrokClient (xAI API: X.com trending search) | Grok returns parenting trends |
| **S2.6** | TrendEngine + scorer + `bb_trend_scan` MCP tool | **GATE: `bb trend scan` returns scored trends** |

### Week 3: Content Pipeline + Polish (Sprint 3)
| Task | What Gets Built | Gate |
|------|----------------|------|
| **S3.1** | brief_generator.py + `bb_content_brief` MCP tool | Brief generated from trend |
| **S3.2** | script_generator.py + `bb_generate_script` MCP tool | 21s/60s scripts in BB voice |
| **S3.3** | visual_generator.py + `bb_generate_visuals` MCP tool | MidJourney/Kling prompts from script |
| **S3.4** | caption_generator.py + exporter.py + `bb_export_platform` MCP tool | Platform-specific exports |
| **S3.5** | `bb_review_queue` + `bb_calendar` + `bb_review_item` MCP tools | Review workflow functional |
| **S3.6** | Scheduler integration (6 BB cron tasks in loop.py) | Cron tasks trigger correctly |
| **S3.7** | Integration testing + docs update + handoff.md | **GATE: Full E2E test passes** |

### Post-Sprint (Phase 2, separate sprints):
- Reddit client (asyncpraw)
- Google Trends alternative (pytrends is dead, need Glimpse or Google API alpha)
- Telegram notifications
- Voice bridge intent ("Baby Brains status")
- AI video generation tool research + testing
- Learning loop (comment engagement tracking)
- System rename (ATLAS -> Astro)

---

## Execution Strategy: Sprint Task System

**Problem:** Each sprint task (S1.1, S1.2, etc.) must be executable by a fresh Claude Code session.
**Solution:** A `SPRINT_TASKS.md` file that serves as the master task tracker. Each task is self-contained with:

```markdown
## S1.1: Schema + Models + DB Init
**Status:** PENDING | IN_PROGRESS | DONE
**Prerequisites:** None (first task)
**Read First:** .claude/handoff.md, docs/BB_AUTOMATION_PLAN_V2.md (Schema section)
**Build:** atlas/babybrains/schema.sql, atlas/babybrains/models.py, atlas/babybrains/db.py
**Test:** pytest tests/babybrains/test_db.py
**Acceptance:** 10 tables created in atlas.db, models importable, db.init_bb_tables() works
**Update After:** Mark DONE in SPRINT_TASKS.md, update handoff.md
```

**New session startup:** "Read .claude/handoff.md and docs/SPRINT_TASKS.md, pick up the next PENDING task."

**Git workflow (2-machine sync):**
- Build on laptop (better wifi)
- Commit + push after each task completes
- Desktop pulls before running
- All state is in git (no local-only files except .env)

### Dependency chain:
```
S1.1 (schema) <- S1.2, S1.3, S1.4 can run in parallel
S1.5 (MCP tools) <- depends on S1.1, S1.3
S1.6 (transcripts) <- independent
S1.7 (comments) <- depends on S1.2, S1.6
S1.8 (warming service) <- depends on S1.1, S1.6, S1.7
---
S2.1 (WSLg test) <- independent, DO FIRST
S2.2 (browser) <- depends on S2.1
S2.3 (MCP tools) <- depends on S2.2
S2.4, S2.5 (API clients) <- depends on S1.1
S2.6 (trend engine) <- depends on S2.4, S2.5
---
S3.1-S3.5 <- depends on S1.1, S1.2
S3.6 (scheduler) <- depends on all services
S3.7 (integration) <- depends on all
```

---

## What's Automated vs Human

| Task | Method | Human Effort |
|------|--------|-------------|
| Find trending content | **AUTO** (Grok, YouTube, Reddit, Google) | None |
| Fetch video transcripts | **AUTO** (YouTube API / Whisper) | None |
| Analyze video for BB angle | **AUTO** (Sonnet API, token-optimized) | None |
| Generate warming comments | **AUTO** (Sonnet + BB voice spec + transcript) | None |
| Watch YouTube videos | **AUTO** (Playwright, 60-300s, quality-based) | None |
| Like YouTube videos | **AUTO** (Playwright, after 60s+ watch) | None |
| Subscribe to channels | **AUTO** (Playwright, max 2/day, quality check) | None |
| Post comments (YouTube) | **HUMAN** copy-paste from AI-drafted text | ~10 min/day |
| Post comments (Instagram) | **HUMAN** copy-paste from AI-drafted text | ~5 min/day |
| Instagram like/follow | **AUTO** (Playwright, rate limited) | None |
| Generate content briefs | **AUTO** (trend + knowledge graph) | Approve |
| Write video scripts | **AUTO** (Claude + BB voice spec) | Review |
| Generate MidJourney/Kling prompts | **AUTO** (extracted from script) | Paste into tools |
| Platform-specific captions | **AUTO** (per platform rules from Dec 2025 research) | Review |
| Track engagement metrics | **AUTO** (weekly snapshots + comment scraping) | None |
| Search across 6 repos | **AUTO** (bb_find_doc) | Just ask |

**Total daily human effort for warming: ~15 min** (review + copy-paste comments)
**Daily human effort for content pipeline: ~30 min** (review scripts, paste visual prompts)
**Monthly API cost: ~$8-15** (Sonnet API + Grok + YouTube Data API)

---

## How the System Learns and Gets Smarter

The system starts with heuristic scoring and generic prompts. It gets smarter through 5 feedback loops:

**Loop 1 -- Comment Quality (Week 2+):**
Track which posted comments get replies/likes. System learns: "Personal experience anecdotes get 3x engagement." Adjusts comment generation prompts. Stored in `bb_warming_actions.engagement_result`.

**Loop 2 -- Trend Prediction (Week 3+):**
Track which trend-sourced content actually performs. System learns: "Reddit-first topics hit TikTok 3-5 days later." Adjusts opportunity scorer weights in `config/babybrains/trend_queries.json`.

**Loop 3 -- Content Performance (Month 2+):**
Track views/saves/shares per published piece. System learns: "Curiosity hooks outperform permission hooks 2:1." Adjusts brief generator to prioritize high-performing patterns. Stored in `bb_exports.performance_data`.

**Loop 4 -- Warming Strategy Optimization (Week 2+):**
Track engagement timing per platform. System learns: "Instagram at 8:30am AEDT = 2x engagement vs 2pm." Adjusts warming schedule in `config/babybrains/warming_schedule.json`.

**Loop 5 -- Voice Spec Calibration (Month 2+):**
Track audience response to different BB voice characteristics. System feeds insights back as voice spec addenda (never modifies the 95KB master spec at `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md`).

**Implementation:**
- `bb_engagement_log` stores weekly snapshots per platform
- `bb_exports.performance_data` tracks per-piece metrics
- `bb_warming_actions` tracks which comment styles get engagement
- New MCP tool `bb_insights()` (Day 6+) surfaces accumulated patterns
- By Week 4: enough data for meaningful pattern detection

---

## Verification Plan

After each day's build:
1. Run `pytest tests/babybrains/` -- unit tests for new code
2. Test MCP tools via Claude Code: type the natural language command, verify output
3. Test CLI: `python -m atlas.babybrains.cli <command>`
4. Day 3+: Verify browser automation with a real YouTube video
5. Day 4+: Verify cron tasks via `python -m atlas.scheduler.loop --once bb_morning_prep`
6. Day 7: Full end-to-end workflow test

---

## Critical Files to Modify

| File | Change |
|------|--------|
| `atlas/mcp/server.py` | Add 14 BB tools following existing `@mcp.tool()` pattern |
| `atlas/scheduler/loop.py` | Add 6 BB scheduled tasks to `_setup_default_tasks()` |
| `.env` | Add GROK_API_KEY, YOUTUBE_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET |
| `CLAUDE.md` | Add BB module documentation, CLI commands, MCP tools |
| `.claude/handoff.md` | Update with BB build progress |

## Key External Files (Read-Only Reference)

| File | Purpose |
|------|---------|
| `/home/squiz/code/web/.claude/agents/BabyBrains-Writer.md` (1712 lines) | Voice spec -- loaded by voice_spec.py |
| `/home/squiz/code/babybrains-os/docs/strategic-review/09-strategic-decisions.md` | Authoritative strategy decisions |
| `/home/squiz/code/babybrains-os/docs/SOCIAL-MEDIA-STRATEGY.md` | Social media funnel |
| `/home/squiz/code/babybrains-os/docs/PLATFORM-PLAYBOOKS.md` | Platform specs |
| `/home/squiz/code/babybrains-os/docs/AUDIENCE-SEGMENTATION.md` | 5 target personas |
| `/home/squiz/code/babybrains-os/docs/research/youtube-dec-2025.md` | YouTube incubation rule |
| `/home/squiz/code/babybrains-os/docs/research/instagram-dec-2025.md` | Instagram Sends KPI |
| `/home/squiz/code/babybrains-os/docs/research/tiktok-dec-2025.md` | TikTok Trust Phase |
| `/home/squiz/code/knowledge/docs/overview/SYNTHESIS_SUMMARY_AND_NEXT_STEPS.md` | Knowledge Graph status |
| `/home/squiz/ATLAS/atlas/nutrition/usda_client.py` | API client pattern to follow |
| `/home/squiz/ATLAS/atlas/mcp/server.py` | MCP tool pattern to follow |
| `/home/squiz/ATLAS/atlas/scheduler/loop.py` | Scheduler pattern to follow |
