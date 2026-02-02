# Baby Brains Content Production: Workflow & Implementation Plan

> Companion to [SYNTHESIS.md](SYNTHESIS.md) — operational playbook derived from 19 research prompts + 12 verification agents.
> Created: 2026-02-02
> Hardware: RTX 3050 Ti 8GB VRAM, 32GB RAM (WSL2)

---

## 1. Weekly Rhythm

| Day | Focus | Time | Output |
|-----|-------|------|--------|
| **Monday** | Script writing + scene breakdowns | 2-3 hrs | 3-5 scripts (3-act, P1/P2/P3 tagged) |
| **Tuesday** | MJ image generation (character + scenes) | 2-3 hrs | 15-25 scene images |
| **Wednesday** | Video generation (Pika/Kling) | 2-3 hrs | 8-15 raw clips |
| **Thursday** | Voice recording + Chatterbox TTS | 1-2 hrs | 3-5 voiceovers + SRT |
| **Friday** | DaVinci assembly + QC | 2-3 hrs | 3-5 finished videos (3 lengths each) |
| **Saturday** | Batch export + scheduling | 1-2 hrs | Upload queue for next week |
| **Sunday** | Rest / review analytics | 30 min | Performance check |

**Target output:** 5-7 finished videos/week across platforms.

**Posting frequency** (PF lines 287-293):

| Platform | Optimal Frequency | Notes |
|----------|-------------------|-------|
| TikTok | 1-3x daily | Consistency beats frequency; same time daily builds ritual |
| Instagram Reels | 4-7x weekly | Mix Reels, carousels, static posts |
| YouTube Shorts | 1-3x daily | Same posting time builds audience habit |
| Facebook | 3-5x weekly | Longer tolerance for content length |

**Australian posting times (AEST):** Best engagement Thursday 7-10 PM AEST (4B lines 66-78).

---

## 2. Daily Session Template

**2-hour focused production block** (adapted from PF line 609):

```
0:00-0:10  Setup: Open DaVinci, load project, review today's scripts
0:10-0:30  Generation: Queue video clips (Pika/Kling) or MJ images
0:30-0:50  Assembly: Build timeline from approved clips
0:50-1:10  Audio: Import VO, set ducking, add SFX (2-3 max)
1:10-1:30  Captions: Generate/review SRT, burn in
1:30-1:50  Derivatives: Duplicate timeline → 30s (drop P3) → 15s (P1 only)
1:50-2:00  Export: Queue 3 lengths × platform presets
```

**Parallel task while waiting for generation:** Script next video, QC previous clips, update tracking spreadsheet.

---

## 3. Batch Production Workflow

### Step 1: Character Prep (one-time, then maintain)

1. Create base character with MJ --oref:
   ```
   A stylized 3D character, [description], Pixar style, Cinema 4D render,
   clean white background, full body, front view --ar 2:3 --v 7
   ```
2. Generate reference sheet (front, side, 3/4, detail views)
3. Create color palette swatch image (600-1200px, 4-6 horizontal swatches)
4. Test --sv 1 (warmth, recommended for BB brand) and --sv 6 (default)
5. Run --sw permutation: `--sw {0, 200, 400, 600, 800, 1000}`
6. Lock Character DNA template for all future prompts

### Step 2: Script Batch

Use the **4-Phase Batch System** (PF lines 273-277) for 10 pieces in 9 focused hours:
1. **Research** (2 hrs): Select Montessori topics, pull from knowledge base
2. **Outlining** (1 hr): 3-act structure, assign P1/P2/P3 priority tiers
3. **Writing/Scripting** (4 hrs): Full scene breakdowns with AI prompts
4. **Editing/Finalizing** (2 hrs): Review, word counts, transition descriptions

Each script must specify:
```
SCENE [N]:
  PRIORITY: P1 CORE / P2 CONTEXT / P3 DEPTH
  DURATION: [seconds]
  AI PROMPT: [Character DNA] + [action] + [camera] + [lighting]
  VO TEXT: "[exact narration]" (12-16 words per line, 130 WPM)
  TEXT OVERLAY: "[on-screen text]"
  TRANSITION OUT: [end action/frame description for Screenshot Shuffle]
  TRANSITION IN: [matching start description for next scene]
```

### Step 3: Image Generation (MJ V7)

- Use --oref with ORIGINAL base image (never chain references)
- Generate ALL scene images before starting video
- Use Relax mode for cost efficiency (Standard plan sufficient)
- `--bs 1` for video to cut cost by 4x
- Expect text rendering to fail in video — add text as overlay in DaVinci

### Step 4: Video Generation

**Primary: Pika Pro ($28/month)**
- Upload MJ image, prompt motion ONLY (do NOT restate visual style)
- Guidance scale 7-10 for image inputs
- Draft at 480p 5s (12 credits) for testing → finalize at 720p-1080p
- Pikaffects "Squish It" for clay deformation (15 credits I2V)
- Budget: ~25-35 polished 720p clips from 2,300 credits
- ⚠️ "Claymation" keyword can cause distortions — use "3D clay animation" or "Pixar style"

**Secondary: Kling Pro ($37/month) for 60s content**
- Generate 6× 10s clips and stitch externally (better than 12× extensions)
- Use Standard Mode for iteration (3.5x cheaper), Professional for finals
- Pan/tilt terminology is INVERTED: "pan" = vertical, "tilt" = horizontal
- Always add endpoints: "then settles into position" to prevent 99% freezes
- ⚠️ All failed generations consume credits with no refunds

**Stitching: Screenshot Shuffle**
1. Generate first clip → capture final frame
2. Upload final frame as starting image for next clip
3. Prompt continuing action
4. Repeat for each scene
5. Shorter clips (5s) maintain better consistency

### Step 5: Voice & Audio

**Voice priority:**
1. Self-recorded Australian voiceover (gold standard, best algorithm treatment)
2. Chatterbox Turbo ($0 local) for bulk — cannot run simultaneously with video gen on 8GB VRAM
3. ElevenLabs Starter ($5/month, 30 min) as cloud fallback
4. Fish Audio API ($9.99/200 min) if ElevenLabs insufficient

**Audio assembly:**
- VO levels: -12 to -6 dBFS
- Music under VO: -24 to -18 dBFS
- SFX: -18 to -12 dBFS (limit 2-3 per clip)
- Fairlight ducking: Threshold -30 to -20 dB, Ratio 3:1-6:1, Attack 10-50ms, Release 200-500ms
- Target: -14 LUFS universal

**Forced alignment:** aeneas for text → timed SRT (accent-agnostic, better than Whisper for known script text).

### Step 6: Assembly (DaVinci Resolve Studio)

**⚠️ DaVinci Resolve Studio required** (free version lost UIManager in v19.1).
**⚠️ DaVinci scripting runs from Windows Python only** (not WSL2).

1. Auto-import clips from folder structure via pybmd
2. Create timeline scaffold from scene breakdown
3. Apply Master Template: 1080x1920, 30fps, H.264 MP4
4. Apply PowerGrade (6-node: Tonality → Balance → Saturation → Secondary → Look → Post)
5. Import VO + set Fairlight auto-ducking (MANUAL — not scriptable)
6. Add caption track (DaVinci 20 Word Highlight or AutoSubs)
7. Duplicate master → delete P3 scenes for 30s → delete P2+P3 for 15s
   - **Deletion step is MANUAL** — API can only append, cannot delete (PE line 558)
8. Batch render: 3 lengths × 4 platform presets

**Per-platform export presets:**

| Platform | Video Bitrate | Audio | Sample Rate |
|----------|--------------|-------|-------------|
| TikTok | 3,000 kbps VBR | 128k AAC | 44.1 kHz |
| Instagram Reels | 4,000 kbps VBR | 128k AAC | 44.1 kHz |
| YouTube Shorts | 12,000 kbps VBR | 192k AAC | 48 kHz |
| Facebook | 6,000 kbps VBR | 128k AAC | 44.1 kHz |

### Step 7: Distribution

- YouTube Shorts: Data API v3 (immediate, ~100 uploads/day). Set `madeForKids: false`.
- Instagram Reels: Graph API (requires app review, 4-8 hrs setup)
- Facebook Reels: Graph API (Pages only, same review)
- TikTok: **MANUAL initially** (API = private-only until audit, weeks of review)
- 5 hashtags maximum per post (TikTok Aug 2025, Instagram Dec 2025)
- Keywords matter more than hashtags for discovery

---

## 4. Quality Checkpoints

### Per-Clip QC (before assembly)

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

### Per-Video QC (after assembly)

- [ ] Audio levels hit -14 LUFS
- [ ] Captions accurate (check "Montessori" and educational terms)
- [ ] First 3 seconds hook the viewer
- [ ] CTA present in final 3-5 seconds
- [ ] No copyrighted music in videos >60s (YouTube monetization blocker)
- [ ] Platform-specific export bitrate correct
- [ ] Metadata stripped (DaVinci rendering auto-strips; verify with exiftool)

### Diagnosis by Drop-Off Pattern (PF lines 414-417)

| Pattern | Diagnosis | Fix |
|---------|-----------|-----|
| Drop-off after few seconds | Weak hook | Test different hook pattern (7 available) |
| High watch time, low engagement | Weak CTA | Strengthen call-to-action |
| Low retention throughout | Pacing issues | Tighten editing, more visual changes |

**Algorithm resilience:** 3-5 consecutive underperforming videos won't damage algorithmic standing; 8-10+ consecutive flops starts to hurt (PF line 399).

---

## 5. Tool Setup Checklist

### Accounts to Create

- [ ] MidJourney Standard ($30/month) — unlimited Relax mode for images
- [ ] Pika **Pro** ($28/month) — Standard has NO commercial license
- [ ] Kling free tier (66 credits/day) — upgrade to Pro ($37) when needed
- [ ] Envato VideoGen ($16.50/month) — promotional, grab before Feb 25, 2026
- [ ] TikTok account (Creator account recommended for trending sounds access)
- [ ] Instagram account
- [ ] YouTube channel (set `madeForKids: false` on ALL uploads)

### Software to Install

- [ ] DaVinci Resolve **Studio** (paid license required for scripting)
- [ ] Windows Python environment (DaVinci scripting is Windows-only)
- [ ] pybmd (`pip install pybmd`) — DaVinci Python automation library
- [ ] Chatterbox Turbo (`pip install chatterbox-tts`, conda env, Python 3.11, CUDA 12.4)
  - First run downloads ~5GB models
  - 4-6GB VRAM — cannot coexist with video gen on 8GB
- [ ] aeneas (forced alignment for SRT generation)
- [ ] AutoSubs plugin for DaVinci (github.com/tmoroney/auto-subs)
- [ ] ffmpeg (for metadata stripping, frame extraction, platform exports)
- [ ] exiftool (for copyright metadata: `exiftool -Copyright="© 2026 Baby Brains" video.mp4`)

### API Keys

- [ ] YouTube Data API v3 (Google Cloud Console)
- [ ] Instagram Graph API (Meta Developer)
- [ ] ElevenLabs API key ($5/month Starter as fallback)
- [ ] fal.ai account (for LoRA training and potential API generation)

### MCP Servers

| Server | Purpose | Install |
|--------|---------|---------|
| Video-Audio MCP (misbahsy) | ffmpeg wrapper | `uv sync` (git clone) |
| OpenCV MCP (GongRzhe) | Frame extraction + comparison | `pip install opencv-mcp-server` |
| SQLite MCP (Anthropic) | Database queries | `uvx mcp-server-sqlite` |
| ElevenLabs MCP (Official) | TTS cloud fallback | `uvx elevenlabs-mcp` |
| DaVinci Resolve MCP (samuelgursky) | Natural language DaVinci | `git clone + install.sh` |
| Fast-Whisper MCP | Transcription | `pip install faster-whisper-mcp` |

---

## 6. Cost Tracking Template

### Monthly Subscription Tracking

| Tool | Tier | Monthly Cost | Start Date | Notes |
|------|------|-------------|-----------|-------|
| MidJourney | Standard | $30 | | Unlimited Relax for images |
| Pika | Pro | $28 | | Min tier with commercial license |
| Kling | Free → Pro | $0-37 | | Upgrade when 60s content needed |
| Envato VideoGen | Standard (promo) | $16.50 | | Expires Feb 25 promo |
| ElevenLabs | Starter | $5 | | Cloud TTS fallback |
| DaVinci Studio | License | One-time | | Required for scripting |
| **Monthly total** | | **$79.50-116.50** | | |

### Per-Video Cost Tracking

| Video ID | Tool Used | Credits Spent | Failed Attempts | Effective Cost | Time (min) |
|----------|-----------|---------------|-----------------|----------------|------------|
| VID001 | Pika Pro | | | | |
| VID002 | Kling Pro | | | | |

**Cost risk factors:**
- Kling: All failed generations consume credits, no refunds (PC lines 62, 114)
- Pika: Credits expire monthly, no rollover
- Kling stylized content: 3-5x cost multiplier due to 30-40% first-try success
- Budget for 2-3 generations per keeper (simple) or up to 10 (complex scenes)

### Weekly Budget Review

| Week | Subscriptions | Per-Video Credits | Total | Videos Produced | Cost/Video |
|------|--------------|-------------------|-------|-----------------|------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |

---

## 7. Realistic Output Estimates

| Content Type | Time Per Video | Monthly Hours | Monthly Output |
|-------------|----------------|---------------|----------------|
| **Simple faceless** (MJ images + ken burns) | 15-25 min | 8-15 hrs | 25-35 videos |
| **Character-consistent** (full pipeline) | 45-75 min | 25-45 hrs | 20-35 videos |
| **With DaVinci template + scripts** | 20-30 min | 12-18 hrs | 25-35 videos |

Baby Brains requires character-consistent content. The 15-25 hrs/month estimate in some sources is for simple faceless only (4A lines 126-127).

**Derivative output multiplier:** Each 60s master produces 3 versions (60s/30s/15s) from the same clip pool. Producing 10 master scripts yields ~30 publishable videos.

---

## 8. Series Concepts

**Recurring format series** — same structure, different content each week (PF lines 259-267):

| Series | Format | Posting | Example Topics |
|--------|--------|---------|----------------|
| **Activity of the Week** | 30-60s demo | Monday | Object permanence, sensory bins, pouring practice, threading beads |
| **Montessori Minute** | 30s principle explanation | Wednesday | "Follow the child," prepared environment, sensitive periods, practical life |
| **Common Mistakes** | 30-60s myth-busting | Friday | Over-praising, interrupting concentration, age-inappropriate toys, over-stimulating environments |

**Progressive series** — builds over time:

| Series | Arc | Duration |
|--------|-----|----------|
| **Age & Stage** | Developmental milestones 0-36 months | 36 episodes |
| **Environment Setup** | Room-by-room Montessori home transformation | 8-10 episodes |
| **30-Day Gentle Parenting Challenge** | Daily follow-along | 30 episodes |

**Content pillar mix:**
- Educational/How-To: 40%
- Myth-Busting/Authority: 25%
- Behind-the-Scenes/Authentic: 20%
- Entertainment/Trending: 15%

---

## 9. Script Templates

### Template 1: Micro-Tutorial (15-30s)

```
HOOK (0-3s, P1 CORE): [Pattern from 7 hook types]
  VO: "[Problem or result statement, 15 words max]"
  TEXT: Bold text overlay matching VO
  VISUAL: Character in relevant setting

DEMONSTRATION (3-20s, P1 CORE): Main activity
  VO: "[Step-by-step narration, 130 WPM]"
  TEXT: Key phrase highlighted
  VISUAL: Close-up on activity, camera push-in

CTA (20-30s, P1 CORE): Payoff
  VO: "Follow for more [topic]"
  TEXT: "Follow @BabyBrains"
  VISUAL: Brand moment + warm glow
  LOOP: End frame matches opening for seamless loop
```

### Template 2: Core Educational (30-60s)

```
HOOK (0-3s, P1 CORE): [Hook pattern]
  VO + TEXT + VISUAL: WAVE delivery (Words, Audio, Visual, Emotion)
  Note: VO starts at 0.5s (visual + text first)

PROBLEM (3-10s, P2 CONTEXT): Why parents need this
  VO: "[Relatable parent scenario]"
  VISUAL: Character showing frustration/confusion

DEMO A (10-25s, P1 CORE): Key activity moment
  VO: "[Primary instruction]"
  VISUAL: Character performing activity with child character

DEMO B (25-40s, P3 DEPTH): Additional detail
  VO: "[Extended explanation]"
  VISUAL: Alternative angle or variation

PRACTICAL TIP (40-55s, P2 CONTEXT): How to do this at home
  VO: "[Actionable parent advice]"
  VISUAL: Home setting illustration

CTA (55-60s, P1 CORE): Follow + share
  VO: "Save this for later"
  VISUAL: Brand moment
```

**Derivative cuts:**
- 30s version: Hook → Problem → Demo A → Practical Tip → CTA (drop Demo B)
- 15s loop: Hook → Demo A → CTA (loop)

### Template 3: Before/After/Bridge (30-60s)

```
BEFORE (0-10s): "Most parents do [common approach]..."
PROBLEM (10-20s): "But this actually [negative outcome]..."
BRIDGE (20-40s): "Instead, try [Montessori approach]..."
AFTER (40-55s): Show positive result with child character
CTA (55-60s): "Follow for more Montessori tips"
```

### Template 4: Authority/Expert (30-60s)

```
CREDENTIAL (0-3s): "After [X] years of Montessori..."
MYTH (3-15s): "Everyone says [common belief]..."
TRUTH (15-40s): "But the research shows [evidence]..."
PROOF (40-55s): Demonstration of correct approach
CTA (55-60s): "Share with a parent who needs this"
```

### Template 5: Deep Dive Educational (60-90s)

```
HOOK (0-3s, P1): Result-first or curiosity gap
CONTEXT (3-15s, P2): Why this matters developmentally
DEMO A (15-30s, P1): Primary activity demonstration
SCIENCE (30-45s, P3): Developmental science explanation
DEMO B (45-60s, P3): Variation or age adaptation
PRACTICAL (60-75s, P2): Parent implementation guide
RECAP (75-85s, P2): 3-point summary
CTA (85-90s, P1): "Save + follow"
```

### Hook Variation Matrix

Each knowledge base entry generates **7 different videos** using the 7 hook patterns:

1. **Problem Statement**: "When your toddler won't stop biting..."
2. **Result-First** (HIGHEST PERFORMER): "This one phrase stopped tantrums"
3. **Curiosity Gap**: "The one thing I wish I knew before becoming a parent"
4. **Authority/Expert**: "After 10 years of Montessori teaching, this works"
5. **Pattern Interrupt**: Child mid-activity with visual chaos
6. **Relatable "Me Too"**: "POV: you're a mom surviving bedtime"
7. **Contrarian/Myth-Buster**: "Stop playing peekaboo wrong"

Same content body, different opening → enables A/B testing.

---

## 10. WAVE Hook Delivery

The WAVE formula for parenting content hooks (PF lines 106-114):

### Framework

| Element | What | Example | Timing |
|---------|------|---------|--------|
| **W** — Words | Text overlay on screen | "How to handle toddler biting" | Frame 1 (0.0s) |
| **A** — Audio | First voiceover sentence | "Here's what actually works..." | 0.5s (delay for AI-animated content) |
| **V** — Visual | Setting/action shown | Parent character or activity in progress | Frame 1 (0.0s) |
| **E** — Emotion | Authentic reaction/connection | Frustrated parent → resolution | Throughout first 3s |

### Key Rules

- **Visual + text appear FIRST** (frame 1), voiceover begins at 0.5 seconds
- This accommodates the 92% of U.S. mobile viewers who start with sound off
- Text overlay must be readable in 1.7 seconds (Instagram hook window)
- 15 words maximum in the hook
- Visual change within first 3 seconds locks the viewer

### Word Count Budgets by Length

| Video Length | Total Words | Pacing |
|-------------|-------------|--------|
| 15s | ~33 words | 130 WPM |
| 30s | ~65 words | 130 WPM |
| 45s | ~98 words | 130 WPM |
| 60s | ~130 words | 130 WPM |
| 90s | ~195 words | 130 WPM |

---

## A/B Testing & Analytics

### Tracking Spreadsheet Structure (PF lines 424-436)

| Column | Purpose |
|--------|---------|
| Video URL | Reference link |
| Post date/time | Timing analysis |
| Platform | Cross-platform comparison |
| Hook type used | Pattern identification (1-7) |
| Views (24h, 48h, 7d) | Performance trajectory |
| 3-sec retention | Critical metric (target: 65%+) |
| Completion rate | Content quality indicator |
| Saves, shares, comments | Engagement depth |
| Test hypothesis | What you changed |
| Result/learnings | What worked |

### Key Metrics

- **North star:** 65%+ 3-second retention → 4-7x more impressions (OpusClip Nov 2025, PF line 402)
- **TikTok boost trigger:** 75% completion rate (2A line 71)
- **Instagram hook window:** 1.7 seconds (Dataslayer.ai, 2B line 36)
- **Faces in first 3s:** +35% retention (Zebracat 2025, 2B line 36)

### Testing Protocol

1. Single variable isolation per test (change only one thing)
2. Wait 24-48 hours — TikTok needs ~20K views for significance
3. Track 3-sec retention, avg watch time, completion rate, save rate, share rate
4. 3-5 underperforming videos won't damage standing; 8-10+ consecutive will

---

## Build Priority Plan

### Prerequisites (Before Week 1)

- [ ] Confirm 8GB VRAM (CLAUDE.md says 4GB — user confirms 8GB)
- [ ] Purchase/activate DaVinci Resolve Studio license
- [ ] Set up Windows Python environment (DaVinci scripting is Windows-only)
- [ ] Create TikTok and Instagram accounts
- [ ] Budget allocation: ~$100-120/month for simultaneous tool subscriptions during testing
- [ ] Sign up for Envato VideoGen ($16.50/mo promo) **before Feb 25, 2026 deadline**

### Week 1: Foundation (Test Before Code)

- [ ] Verify Pika Pro commercial license terms FIRST (Standard has NO license)
- [ ] Create MJ character reference sheet (--oref + --sref + --sv 1 for warmth, --sv 6 as default)
- [ ] Test --sw permutation: `--sw {0, 200, 400, 600, 800, 1000}` with BB style reference
- [ ] Test clay term variants: "claymation" vs "3D clay animation" vs "Pixar style" across Kling, Pika Pro, MJ
  - Pika free tier has only 80 credits/month — budget carefully
  - Expect Claymation distortions in Pika; use "3D clay animation" instead
- [ ] Test multi-person scene success rate (parent + baby) — expect ~20% success in MJ
- [ ] Test Chatterbox Turbo on 8GB VRAM (borderline; first run downloads ~5GB; test stability)
- [ ] Generate 3 test videos end-to-end manually (no automation)
- [ ] Test burned-in caption workflow in DaVinci Studio (Effects > Titles > Animated > Word Highlight)

### Week 2: Audio + Script Pipeline

- [ ] Set up Chatterbox (if VRAM test passes) or Fish Audio API ($9.99/200 min) as primary TTS
- [ ] Test Uppbeat ($5.59/mo) vs Epidemic Sound ($9-19/mo) for background music
- [ ] Verify CML cross-platform licensing: CML tracks are TikTok-only
- [ ] Adapt 5 script templates (Micro-Tutorial, Core Educational, Before/After/Bridge, Authority, Deep Dive)
- [ ] Test WAVE hook formula on 3 videos
- [ ] Set up 130 WPM pacing target and word count budgets per template length
- [ ] Set up aeneas for forced alignment (script text → timed SRT)

### Week 3: Assembly + Distribution Setup

- [ ] DaVinci scripting spike (Windows Python, confirm append-only; test pybmd)
- [ ] Build P1 master timeline workflow (derivative deletion step is MANUAL)
- [ ] Test per-platform export: TikTok 3Mbps, Reels 4Mbps, Shorts 12Mbps, Facebook 6Mbps
- [ ] Set up cost tracking spreadsheet (include Kling failed-generation credit loss)
- [ ] Set up Fairlight ducking preset (threshold -30 to -20dB, ratio 3:1-6:1)
- [ ] Create Power Bins folder structure (files are referenced, not copied — stable paths required)
- [ ] Set up YouTube Data API v3 upload pipeline (with `madeForKids: false`)

### Week 4: First Real Batch

- [ ] Produce 3-5 complete videos using full workflow
- [ ] Measure actual time per video (target: 20-30 min with template approach)
- [ ] Implement A/B tracking spreadsheet (10 columns)
- [ ] Test 5-hashtag strategy on TikTok and Instagram
- [ ] Monitor: 3-5 underperforming videos won't damage algorithmic standing
- [ ] Diagnose by drop-off pattern if needed: weak hook / weak CTA / pacing issues

### Week 5+: Code Automation (Only If Week 4 Validates)

- [ ] Batch video generation scripts (reference PE burst generation code ~57 lines)
- [ ] DaVinci automation within API limitations (append-only, Track 1 only)
- [ ] Upload pipeline automation: YouTube + Instagram + Facebook
- [ ] Cost/quota monitoring dashboard
- [ ] Consider Creatomate ($54-99/mo) if manual workflow proves too slow
- [ ] QC pipeline: watchdog auto-queues to SQLite, `/qc` triggers Claude review
- [ ] SSIM comparison: first frame vs source MJ image (>0.7 = good preservation)
- [ ] VMAF threshold: 80-85 acceptable for social media
