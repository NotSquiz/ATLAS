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
| **Thursday** | Voice recording + Qwen3-TTS | 1-2 hrs | 3-5 voiceovers + SRT |
| **Friday** | DaVinci assembly + QC | 2-3 hrs | 3-5 finished videos (3 lengths each) |
| **Saturday** | Batch export + scheduling | 1-2 hrs | Upload queue for next week |
| **Sunday** | Rest / review analytics | 30 min | Performance check |

**Target output:** 5-7 finished videos/week across platforms.

**Posting frequency — ramp-up approach:**

Consistency beats frequency. Start slow while learning the pipeline, then scale up once the workflow is reliable.

| Phase | Per Platform | Total Posts/Week | Duration |
|-------|-------------|------------------|----------|
| **Learning** (Weeks 1-4) | ~1 every 2 days | 8-12 across all platforms | Until workflow is comfortable |
| **Building** (Weeks 5-8) | 3-4x per week | 12-16 across all platforms | Until quality is consistent |
| **Optimal** (Week 9+) | See targets below | 25-40+ across all platforms | Steady state |

**Optimal frequency targets** (PF lines 287-293) — aspirational, not starting point:

| Platform | Optimal Frequency | Notes |
|----------|-------------------|-------|
| TikTok | 1-3x daily | Same time daily builds ritual |
| Instagram Reels | 4-7x weekly | Mix Reels, carousels, static posts |
| YouTube Shorts | 1-3x daily | Same posting time builds audience habit |
| Facebook | 3-5x weekly | Longer tolerance for content length |

**Australian posting times (AEDT Oct-Apr; subtract 1hr for AEST May-Sep) — full schedule** (OLD-5, Sprout Social analysis of 50M engagements from 17K AU profiles):

| Day | Instagram | TikTok | YouTube Shorts | Facebook |
|-----|-----------|--------|----------------|----------|
| Mon | 6-9 PM (peak) | 10 AM-12 PM, 7-9 PM | 8 AM, 1 PM, 6-8 PM | 11 AM-1 PM, 6-8 PM |
| Tue | 6-8 PM | 9-11 AM, 5-7 PM | 7-8 AM | 11 AM-1 PM, 6-8 PM |
| Wed | 6-8 PM | 6-8 AM, 7-9 PM | 7-8 AM | 11 AM-1 PM, 6-8 PM (best) |
| Thu | 6-8 PM | 9 AM-12 PM, 7-9 PM (best) | 9 AM, 3-4 PM | 11 AM-1 PM, 6-8 PM |
| Fri | 8-10 AM, 6-8 PM | 7-9 AM, 11 PM | 7 AM, 9 AM, 3 PM, 6 PM (best) | 11 AM-1 PM, 6-8 PM |
| Sat | 4-9 PM (worst day) | 8-10 AM, 7-9 PM | 1-2 PM | 9-11 AM, 3-5 PM |
| Sun | 7-8 PM | 10 AM-12 PM, 9 PM (worst) | 10 AM-12 PM | 9-11 AM, 3-5 PM (best w Wed) |

**Key patterns:** Before-work scrolls (6-9 AM), lunch breaks (11 AM-1 PM), post-dinner downtime (7-9 PM). Instagram worst = Saturday. TikTok worst = Sunday. Facebook best = Wednesday + Sunday.

**Algorithm safety:** 3-5 underperforming videos won't damage algorithmic standing. 8-10+ consecutive flops starts to hurt (PF line 399). During the Learning phase, focus on learning the tools and producing quality content — not hitting frequency targets.

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

> **Brand direction:** Warm 3D-rendered environments with claymation-influenced sculptural characters.
> Brancusi/Hepworth-inspired simplified organic forms, bioluminescent glow, warm clay-amber tones.
> See: `docs/research/Unifying Baby Brains - From premium identity to platform-native social.md`
> and `docs/research/Baby Brains unified visual system bridges premium identity with platform-safe social content.md`

**1. Create "Baby Brains Baby" hero character:**

Start with a detailed base prompt (clean background for maximum reference quality):
```
stylized infant with simplified sculptural features, smooth ovoid head,
large expressive eyes, warm clay-amber skin tones with subtle subsurface
scattering, sitting on natural maple wood floor, Montessori playroom with
cream walls and warm golden hour lighting streaming through windows,
Brancusi-inspired organic forms, soft volumetric light, limited palette of
warm cream maple amber and muted teal accents
--ar 2:3 --v 7 --stylize 100
--no cartoon, Disney, Pixar, anime, photorealistic, harsh shadows, plastic
```

Key character traits:
- **Form:** Ovoid/egg-shaped head (Brancusi's "Beginning of the World"), rounded forms, no sharp edges
- **Material:** Warm clay-amber tones with subtle gradients suggesting subsurface scattering — not literal wood grain but warm, alive surfaces
- **Features:** Large expressive eyes (primary emotional communication), simple curved eyebrows, minimal mouth (simple curve)
- **Style:** Single primary character, adjustable proportions for 0-36 months developmental stages

**2. Generate reference sheet** (front, side, 3/4, detail views) from best hero image

**3. Create Social Content Palette swatch image** (600-1200px, 4-6 horizontal swatches):
- Primary (60%): Warm White #F7F5F0, Maple Cream #E6DECD, Warm Maple #CCBFA3, Soft Cream #FFFAF5
- Secondary (30%): Soft Amber #D9A856, Muted Amber #C4A870, Warm Kelp #3D4F45, Warm Olive #8B9A7E
- Accent (10%): Muted Teal #5BA8A8, Soft Aqua #7ABAB4, Dusty Violet #8D6AA8
- MJ does NOT reliably recognize hex codes — use the swatch image with `--sref` instead

**4. Lock style + character references:**
- Use hero image as BOTH `--oref` (omni reference) and `--sref` (style) for double-locking
- `--oref [hero_URL] --ow 80` — maintains face strongly, allows pose flexibility
- `--sref [hero_URL] --sw 300-400` — strong style adherence
- Test `--sv 1` (warmth, recommended for BB) and `--sv 6` (default)

**5. Run --sw permutation:** `--sw {0, 200, 400, 600, 800, 1000}` with BB style reference

**6. Test scene variations:**
```
# Educational activity scene
stylized toddler with simplified Brancusi-inspired features playing with
pink tower Montessori blocks, smooth rounded forms, warm maple wood table
surface, cream background, warm subsurface scattering lighting, soft
ambient glow, natural linen textures, sculptural minimalist aesthetic,
muted teal accent on one block
--oref [hero_URL] --ow 80 --sref [hero_URL] --sw 300
--ar 1:1 --stylize 100
--no text, harsh lighting, cartoon style, photorealistic

# Claymation-influenced variant (test)
claymation style infant character with smooth organic sculptural features,
soft matte clay surface, warm amber tones, gentle fingerprint textures,
Montessori wooden toys on natural maple shelf, warm cinematic lighting
with soft shadows, stop-motion aesthetic, tactile handmade quality,
cream and maple color palette
--oref [hero_URL] --ow 80 --sref [hero_URL] --sw 300
--ar 9:16 --stylize 80
--no shiny, plastic, harsh, photorealistic, neon

# Premium hero moment (parent + baby)
sculptural mother and infant, simplified organic Brancusi Hepworth forms,
smooth polished surfaces suggesting warm maple wood and amber resin,
intimate embrace, dramatic volumetric lighting with warm subsurface
scattering, deep midnight blue-black background with subtle bioluminescent
cyan accents, electric cyan highlights at edges, modernist aesthetic
--ar 4:5 --stylize 150
--no cartoon, detailed faces, busy background
```

**7. Lock Character DNA template for all future prompts**

**MJ prompt suffix (append to ALL generation prompts):**
`warm subsurface scattering, soft golden ambient lighting, gentle inner glow, volumetric light rays`

**Keywords to AVOID** (cause style drift): "cute," "adorable," "fun," "colorful," "playful," "children's book illustration," "3D render" without style qualifier, "realistic"

**Safer alternatives:** Instead of "cute baby" → "stylized infant with simplified organic features." Instead of "colorful" → specific color names + "limited palette." Instead of "children's educational" → "Montessori learning" + "minimalist aesthetic."

### Pre-Production: YAML Clip Brief

Before writing scripts, create a clip brief for each planned video (OLD-3 SCR-001):

```yaml
title: "Object Permanence Game"
hook_text: "Your baby thinks things disappear forever"
target_length: 60s
priority_tier: P1  # P1 CORE / P2 CONTEXT / P3 DEPTH
age_range: "6-12 months"
montessori_principle: "Object permanence"
setting: "Montessori playroom, timber floor, natural light"
au_localisers: ["jute rug", "sliding glass door"]
safety_lines: ["Stop if baby becomes distressed"]
camera_notes: "Wide establishing → close-up on hands → medium result"
character_refs: ["hero_image_URL"]
tags: ["object-permanence", "sensory", "6-months"]
```

This brief feeds into the scene breakdown and ensures all production requirements are captured before scripting begins.

### Step 2: Script Batch

Use the **4-Phase Batch System** (PF lines 273-277) for 10 pieces in 9 focused hours:
1. **Research** (2 hrs): Select Montessori topics, pull from knowledge base
2. **Outlining** (1 hr): 3-act structure, assign P1/P2/P3 priority tiers
3. **Writing/Scripting** (4 hrs): Full scene breakdowns with AI prompts
4. **Editing/Finalizing** (2 hrs): Review, word counts, transition descriptions

**Anti-template variation checklist** (mandatory for YouTube compliance — OLD-1 CST-009):
- [ ] Synonym rotation: varied word choices across scripts (not the same phrasing every time)
- [ ] Beat ordering shuffle: vary the sequence of content beats between videos
- [ ] Sentence length mixing: alternate short punchy sentences with longer explanatory ones
- [ ] Narration perspective alternation: rotate first person / third person / direct address
- [ ] Does this script sound different from the last 3 scripts? If not, revise.

**{HOOK} token convention**: Place a `{HOOK}` marker in the first VO line of every script. Automated QC validates hook keyword presence in line 1 via regex (OLD-4 ST-008).

Each script must specify:
```
SCENE [N]:
  PRIORITY: P1 CORE / P2 CONTEXT / P3 DEPTH
  DURATION: [seconds]
  AI PROMPT: [Character DNA] + [action] + [camera] + [lighting]
  VO TEXT: "[exact narration]" (12-16 words per VO line, 130 WPM speaking pace)
  CAPTION DISPLAY: "[on-screen caption]" (max 2 lines, 6-8 words each, ~32 chars/line — separate from VO line count)
  TEXT OVERLAY: "[on-screen text]"
  SEO KEYWORDS: Naturally embed search terms in VO so they appear in captions (OLD-1 PRD-005)
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
- ⚠️ "Claymation" keyword can cause distortions in Pika — use "3D clay animation" or "soft matte clay surface" instead

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

**A/B/C Shot Archetype Structure** (OLD-3 CST-001/002):
For each stitched scene sequence, follow this pattern:
- **Shot A (Wide)**: Establish the scene — full room/environment visible, character in context
- **Shot B (Close-up)**: Demonstrate the activity — hands, face, or material interaction detail
- **Shot C (Medium)**: Show the result/CTA — character reaction, learning moment, or brand closure

This wide→close→medium progression creates natural visual flow and matches viewer attention patterns.

### Step 5: Voice & Audio

**Voice priority:**
1. Self-recorded Australian voiceover (gold standard, best algorithm treatment)
2. Qwen3-TTS ($0 local, already installed in ATLAS) — voice cloning from reference audio, 0.6B params, ~4-6GB VRAM. Clone an Australian voice from a short sample.
3. Fish Audio API (~$11/mo Plus tier; $5.50/mo annual) — 70% cheaper than ElevenLabs, #1 TTS-Arena. Primary cloud fallback.
4. ElevenLabs Starter ($5/month, 30,000 credits ≈ 30 min) — secondary cloud fallback
5. **Investigate:** Maya1 (3B, Apache 2.0, voice design via natural language, 20+ emotions) — needs 16GB+ VRAM locally, cloud/API deployment possible. See: huggingface.co/maya-research/maya1

**Audio assembly:**
- VO levels: -12 to -6 dBFS
- Music under VO: -24 to -18 dBFS
- SFX: -18 to -12 dBFS (limit 2-3 per clip)
- Fairlight ducking: Threshold -30 to -20 dB, Ratio 3:1-6:1, Attack 10-50ms, Release 200-500ms
- Target: -14 LUFS integrated (platforms normalize automatically)
- True-peak limit: **TP = -1.5 dB** (prevents digital clipping on lossy codecs — OLD-2 PLT-003)
- Loudness Range: **LRA = 11** (prevents jarring volume shifts within a video — OLD-2 PLT-003)

**Forced alignment:** aeneas for text → timed SRT (accent-agnostic, better than Whisper for known script text).

### Step 6: Assembly (DaVinci Resolve Studio)

**⚠️ DaVinci Resolve Studio required** (free version lost UIManager in v19.1).
**⚠️ DaVinci scripting runs from Windows Python only** (not WSL2).

1. Auto-import clips from folder structure via pybmd
2. Create timeline scaffold from scene breakdown
3. Apply Master Template: 1080x1920, 30fps, H.264 High Profile Level 4.2 MP4 (OLD-2 PLT-002 — maximum compatibility across all platforms)
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

> **Note:** Master project should use 48 kHz audio. DaVinci will downsample to 44.1 kHz on TikTok/Instagram/Facebook exports automatically.

### Step 7: Distribution

**Core principle:** All derivative lengths (60s/30s/15s) go to ALL four platforms in platform-appropriate exports. A single 60-second video works well across all platforms (see SYNTHESIS.md "Cross-platform compatibility" section). The 30s and 15s derivatives serve as additional content pieces, not platform-specific cuts.

**Platform-specific safe zones** (OLD-3 PLT-001/002/003 — re-verify on current platform UIs before hardcoding into templates):

| Platform | Top margin | Bottom margin | Left | Right | Notes |
|----------|-----------|---------------|------|-------|-------|
| Instagram Reels | ≥220px | ≥420px | — | — | Username + like/share buttons |
| TikTok | ≥108px | ≥320px | 60px | 120px | Description text + interaction buttons |
| YouTube Shorts | ≥140px | ≥270px | — | — | Title + subscribe button |
| Facebook Reels | ≥200px | ≥350px | — | — | Similar to Instagram (Meta shared UI) |

**All captions and text overlays must fall within these safe zones.** Test on actual phone screens before publishing (see Review Gate in QC section). Safe zone values may shift with UI updates — re-verify quarterly.

**Per master script → 12 export files:**
```
1 master × 3 lengths (60s/30s/15s) × 4 platforms (TikTok/IG/YT/FB) = 12 files
```

Each export uses the platform-specific bitrate preset from Step 6. The platforms do not penalize based on video length — all lengths are valid on all platforms.

**Staggering strategy (critical for Instagram):**
- Instagram imposes a **duplicate content penalty** (24hrs-30 days suppression) and penalizes TikTok watermarks
- Upload natively to each platform (never use TikTok/Instagram share buttons to cross-post)
- Stagger same-length uploads across platforms by 6-12 hours minimum
- Vary captions slightly per platform (different hashtags, tone adjustments)
- Post different lengths to the same platform on different days (don't flood all 3 lengths in one day)

**Example weekly distribution for a single master video:**
| Day | TikTok | Instagram | YouTube | Facebook |
|-----|--------|-----------|---------|----------|
| Mon | 60s | — | — | — |
| Tue | — | 60s | 60s | 60s |
| Wed | 30s | — | — | — |
| Thu | 15s | 30s | 30s | 30s |
| Fri | — | 15s | — | 15s |

### SEO Keyword Placement Guide

Keywords now drive discovery more than hashtags on both TikTok and Instagram. Place keywords strategically across these surfaces, ordered by impact (OLD-5 CS-008/017/018):

**Universal keyword hierarchy** (highest impact first):
1. **Filename** — include primary keyword in the video filename before upload
2. **Title/Caption first line** — front-load the primary keyword in first 80-125 characters
3. **Description body** — natural keyword inclusion throughout
4. **Hashtags** — 5 max (see hashtag strategy below)
5. **On-screen text** — burned-in captions are indexed by platforms
6. **Spoken audio** — platforms transcribe and index voiceover content

**Platform-specific priorities:**
- **Instagram**: Profile name/bio > captions > alt text (under 100 chars, keyword-rich — OLD-5 PG-007) > hashtags > subtitles. Instagram posts now indexable by Google/Bing (July 2025).
- **TikTok**: Captions > on-screen text > voiceover > descriptions > hashtags
- **YouTube**: Title (under 60 chars for full visibility) > description (250+ words recommended) > tags (~5, main keyword first) > spoken audio. YouTube Shorts appear in Google Discover (Sep 2025).
- **Facebook**: Caption > description > conversational tone keywords

**Keyword-in-narration technique** (OLD-1 PRD-005): Naturally embed search terms in voiceover so they appear in auto-generated captions. Examples: "baby independent play", "Montessori home setup", "toddler activities for 6 month old". This makes spoken words searchable across all platforms.

### Platform Caption Character Limits

| Platform | Max chars | Visible before "more" | Title field | Notes |
|----------|----------|----------------------|-------------|-------|
| Instagram | 2,200 | First 125 (80-100 in main feed) | N/A | Front-load hook + keyword |
| TikTok | 2,200-4,000 | First 1-2 lines | N/A | Keyword-first |
| YouTube Shorts | 5,000 (description) | First 100-150 | 100 chars (under 60 for full visibility) | Description is SEO-critical |
| Facebook | 2,200 | First 125 | N/A | Conversational tone |

Source: OLD-5 PS-006/007/008. File size limits: Instagram/Facebook 4GB, TikTok 500MB (under 3 min) / 2GB (3-10 min).

### Platform Tone Differentiation

Adapt the same video's caption and presentation per platform while maintaining BB brand voice (OLD-5 BV-001, CS-011-014):

| Platform | Tone | Caption Style | Example Opener |
|----------|------|--------------|----------------|
| **TikTok** | Authentic, conversational, raw | Short, punchy, keyword-front | "ok but why does no one talk about this" |
| **Instagram** | Polished, visually premium | Clean, aspirational, emoji-light | "The Montessori approach to independent play" |
| **YouTube** | Educational, keyword-rich | Descriptive title + detailed description | "Montessori Activities for 6 Month Old Baby" |
| **Facebook** | Conversational, community-focused | Longer, question-based, shareable | "Tried this with our bub yesterday and..." |

**All platforms maintain BB core voice:** calm, evidence-based, encouraging, Australian English. The differentiation is in framing and energy, not substance.

### Hashtag Strategy: 3-Bucket Formula

**5 hashtags maximum per post** (TikTok Aug 2025, Instagram Dec 2025). Select using the 3-bucket formula (OLD-5 CS-019):

| Bucket | Purpose | Count | AU Examples |
|--------|---------|-------|-------------|
| **Niche** (audience identifier) | Reach your specific audience | 1-2 | #melbourneparents, #sydneymums, #perthmum, #brisbanekids |
| **Medium** (topic) | Reach topic-interested users | 2 | #australianparents, #aussieparenting, #montessoriathome |
| **Broad** (discovery) | Reach general audience | 1 | #montessori, #toddleractivities, #babyplay |

**Rules:**
- Never use #fyp — it's noise, not signal
- Rotate combinations weekly to prevent hashtag fatigue
- Track which combinations drive saves (highest-signal engagement metric)
- AU-specific hashtags perform better for local audience building

### YouTube Shorts Thumbnails

Custom thumbnails increase CTR by up to **154%** (OLD-5 PS-014). YouTube Shorts now support custom thumbnail upload:

- **Size:** 1280×720 (16:9) or 1080×1920 (9:16)
- **Max file size:** 2MB
- **Design:** Use a single still from the video with bold text overlay. Maintain BB clay aesthetic. Face/character in frame increases clicks.
- **Add to Saturday batch export workflow** — generate thumbnail alongside video exports.

**Upload methods:**
- YouTube Shorts: Data API v3 (immediate, ~100 uploads/day). Set `madeForKids: false`.
- Instagram Reels: Graph API (requires app review, 4-8 hrs setup)
- Facebook Reels: Graph API (Pages only, same review)
- TikTok: **MANUAL initially** (API = private-only until audit, weeks of review)
- 5 hashtags maximum per post (TikTok Aug 2025, Instagram Dec 2025)
- Keywords now drive discovery more than hashtags on both TikTok and Instagram

### Platform-Specific Upload Checklist

**Facebook Reels:**
- SRT naming convention: `videoname.en_US.srt` (must match video filename) (OLD-4 PG-008)
- October 2025 algorithm favours same-day content (50% more shown) — post same day as creation when possible

**YouTube Shorts:**
- Tags: ~5 tags, main keyword first, include competitor/related tags (OLD-5 CS-009)
- Title: Under 60 characters for full visibility. Include primary keyword.
- Description: 250+ words. Include secondary keywords naturally.
- Always include `#Shorts` tag

**Instagram Reels:**
- Alt text: Under 100 characters, keyword-rich (OLD-5 PG-007). Instagram posts now indexable by Google/Bing.
- No TikTok watermarks (24hr-30 day suppression penalty)

**TikTok:**
- API posts are private-only until audit approved. Manual posting initially.
- SRT upload now available via Ads Manager and Video Editor (as of 2025)

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
- [ ] No readable AI-generated text artifacts (signs, books, labels — blur if present) (OLD-3 PRD-015)
- [ ] Prop continuity: objects present in earlier shots persist through later shots (OLD-3 VIS-011)
- [ ] Lighting consistency maintained across stitched clips (OLD-3 VIS-012)
- [ ] Camera framing progression: wide establishing → close-up detail → medium result (OLD-3 VIS-013)

### Per-Video QC (after assembly)

- [ ] Audio levels hit -14 LUFS
- [ ] Captions accurate (check "Montessori" and educational terms)
- [ ] First 3 seconds hook the viewer
- [ ] CTA present in final 3-5 seconds
- [ ] No copyrighted music in videos >60s (YouTube monetization blocker)
- [ ] Platform-specific export bitrate correct
- [ ] Metadata stripped (DaVinci rendering auto-strips; verify with exiftool)

### Safety Gate (before publish) — ALL must pass

- [ ] **"Stop if..." disclaimers**: Safety disclaimers starting with "Stop if..." included in both VO and burned-in captions, displayed 2-3 seconds (OLD-3 CST-005)
- [ ] **Content safety verification**: No small choking hazards, no unsupervised climbing, no age-inappropriate activities, no dangerous stunts, no medical advice (OLD-1 QCI-003)
- [ ] **Montessori alignment**: Authentic Montessori materials (not plastic/electronic), age-appropriate activities, no fantasy elements (under 6), no branded products, known Montessori allowances (OLD-1 QCI-005)
- [ ] **Child safety compliance**: Adult supervision visible, avoid private spaces (bathrooms/bedrooms), age-appropriate only, no PII, privacy settings enabled, monitor comments (OLD-5 QI-002)

### Caption & Audio QC Gate

- [ ] **WER ≤10%**: Word Error Rate must be ≤10% (≥90% accuracy) for published captions. Run Whisper WER harness against reference SRT (OLD-2 ANL-001)
- [ ] **Caption sync tolerance**: ≤0.2 seconds between VO audio and burned-in caption display (OLD-3 QCI-003)
- [ ] **Caption display spec**: Maximum 2 lines visible at a time, 6-8 words per displayed line (~32 characters). This is SEPARATE from the VO script line count of 12-16 words (OLD-3 PRD-010)

### Review Gate (before upload)

- [ ] **Human review required** (100% pass — no "good enough" exceptions): Human reviewer signs off on visual quality, safety, brand compliance with initials and date (OLD-3 PRD-012). **AI review recommended when available** — Claude/Opus with MCP video tools can augment human review for visual QC and safety checks. AI video review tooling is in development; use human-only review until available.
- [ ] **Phone screen test**: Watch on actual mobile phone with sound off. Check: captions readable, safe zones clear, audio levels appropriate, no visual artifacts at mobile resolution (OLD-3 PRD-013, OLD-4 PG-009)
- [ ] **Platform metadata verified**: AI labels set correctly, `madeForKids: false` on YouTube, correct category, correct audience designation (OLD-3 QCI-007)
- [ ] **AU English verified**: All captions, titles, and descriptions use Australian English spelling (see SYNTHESIS.md Appendix: Australian Localisation Guide). Cross-ref BB-Writer agent for automated checks.

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

- [ ] MidJourney Standard ($30/month) — unlimited Relax mode for **images only**. VIDEO Relax requires Pro ($60) or Mega ($120). Standard is sufficient for image generation pipeline.
- [ ] Pika **Pro** ($28/month) recommended — Standard ($8/mo) now includes commercial use; Pro for higher credits
- [ ] Kling free tier (66 credits/day) — upgrade to Pro ($37) when needed
- [ ] Envato VideoGen ($16.50/month) — promotional, grab before Feb 25, 2026
- [ ] TikTok account (Creator account recommended for trending sounds access)
- [ ] Instagram account
- [ ] YouTube channel (set `madeForKids: false` on ALL uploads)

### Cloud GPU (Free)

- [ ] **Google Colab VS Code extension** — free T4 GPU (15GB usable VRAM) in your IDE
  - Install "Google Colab" extension in VS Code, open .ipynb, select "Colab" kernel, authenticate
  - 12hr max sessions, 90min idle timeout, 15-30 GPU hrs/week free
  - Use for: Maya1 TTS testing (needs 16GB+), LoRA training ($0 vs $2/run on fal.ai), batch TTS while video gen runs locally
  - Eliminates VRAM contention — run TTS on Colab while Pika/Kling use local 8GB
  - Source: https://developers.googleblog.com/google-colab-is-coming-to-vs-code/

### Software to Install

- [ ] DaVinci Resolve **Studio 20** (paid license required for scripting. v20 adds 100+ new features including AI tools. Free version lost UIManager in v19.1.)
- [ ] Windows Python environment (DaVinci scripting is Windows-only)
- [ ] pybmd (`pip install pybmd`) — DaVinci Python automation library
- [ ] Qwen3-TTS (already installed in ATLAS — `atlas/voice/tts_qwen.py`)
  - Clone an Australian voice from short reference audio sample
  - ~4-6GB VRAM — cannot coexist with video gen on local 8GB (use Colab T4 for parallel TTS)
- [ ] aeneas (forced alignment for SRT generation)
- [ ] AutoSubs plugin for DaVinci (github.com/tmoroney/auto-subs)
- [ ] ffmpeg (for metadata stripping, frame extraction, platform exports)
- [ ] exiftool (for copyright metadata: `exiftool -Copyright="© 2026 Baby Brains" video.mp4`)

### API Keys

- [ ] YouTube Data API v3 (Google Cloud Console)
- [ ] Instagram Graph API (Meta Developer)
- [ ] Fish Audio API key (~$11/month or $5.50/month promo — restructured to tiered plans, primary cloud TTS fallback)
- [ ] ElevenLabs API key ($5/month Starter, 30,000 credits — uses credit system, not minutes)
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
| Pika | Pro | $28 | | Recommended tier (higher credits; Standard now includes commercial use) |
| Kling | Free → Pro | $0-37 | | Upgrade when 60s content needed |
| Envato VideoGen | Standard (promo) | $16.50 | | Expires Feb 25 promo |
| Fish Audio | API | ~$11/mo | | Primary cloud TTS (#1 TTS-Arena) |
| ElevenLabs | Starter | $5 | | Secondary cloud TTS fallback |
| DaVinci Studio | License | One-time | | Required for scripting |
| **Monthly total** | | **$89.50-131.50** | | |

### Per-Video Cost Tracking

| Video ID | Tool Used | Credits Spent | Failed Attempts | Effective Cost | Time (min) |
|----------|-----------|---------------|-----------------|----------------|------------|
| VID001 | Pika Pro | | | | |
| VID002 | Kling Pro | | | | |

**Cost risk factors:**
- Kling: All failed generations consume credits, no refunds (PC lines 62, 114)
- Pika: Credits now roll over on paid plans (updated 2025). Standard ($8/mo) now includes commercial use.
- Kling stylized content: 3-5x cost multiplier due to 30-40% first-try success
- Budget for 2-3 generations per keeper (simple) or up to 10 (complex scenes)

### Weekly Budget Review

| Week | Subscriptions | Per-Video Credits | Total | Videos Produced | Cost/Video |
|------|--------------|-------------------|-------|-----------------|------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |

### Production Throughput Tracker

Daily production log for identifying bottlenecks (OLD-2 AUT-009):

```csv
date,slugs_done,mj_images,pika_clips,kling_clips,qc_passed,qc_failed,assembly_done,avg_minutes_per_video,failures,notes
2026-02-01,3,12,8,2,7,3,2,28,"1 Kling freeze","First batch"
```

Track daily to identify which pipeline stage is the bottleneck. Review weekly in WBR (see Analytics section).

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

### Developmental Stage Content Mapping (0-36 months)

Content categories mapped by developmental stage for search discoverability (OLD-1 CST-010):

| Age Range | Primary Content Focus | Example Activities |
|-----------|----------------------|-------------------|
| 0-3 months | Sensory stimulation, tummy time, tracking | High-contrast cards, gentle mobiles, face-to-face play |
| 3-6 months | Reaching, grasping, rolling | Grasping rattles, texture exploration, supported sitting |
| 6-9 months | Sitting, crawling prep, object permanence | Peek-a-boo, treasure baskets, container play |
| 9-12 months | Cruising, pincer grasp, cause-and-effect | Ball drop, stacking, shape sorting, first steps prep |
| 12-18 months | Walking, practical life intro, language explosion | Pouring, spooning, simple puzzles, naming objects |
| 18-24 months | Running, pretend play, autonomy | Dressing frames, food prep, matching, water transfer |
| 24-36 months | Complex practical life, social skills, concentration | Polishing, sweeping, cutting, threading, art activities |

Parents search by age ("activities for 6 month old", "toddler Montessori"), not by abstract category. Tag every video with its target age range.

### AU Seasonal Content Calendar

Plan content around Australian seasons, NOT northern hemisphere (OLD-5 AS-007/008):

| Period | AU Season | Content Themes |
|--------|-----------|---------------|
| Jan-Feb | Summer / Back to school | Outdoor water play, sun safety activities, school readiness |
| Mar-May | Autumn | Indoor sensory play, leaf collection, rainy day activities |
| Jun-Aug | Winter | Cosy indoor activities, cooking with toddlers, indoor gross motor |
| Sep-Oct | Spring | Gardening with toddlers, outdoor exploration, nature walks |
| Nov-Dec | Late spring / Summer | Holiday-themed activities, outdoor play, end-of-year content |

Cross-reference with SYNTHESIS.md "Australian Content Themes" section for trending topic integration.

---

## 9. Script Templates

### Production Techniques for Scripts

**Reverse-structure editing** (OLD-1 PSY-004): For "Result-First" hooks (highest performer), show the end result in the first second, then "rewind" to show the process. Edit the 60s master video to place the final scene first as a brief flash (1-2s), then cut to the standard sequence.

**Seamless loop technique** (OLD-1 PSY-007): For 7-15s hook clips, design the final frame to match the opening frame exactly. Viewers may not notice the restart, inflating completion rates and triggering algorithmic boost. Use MJ `--loop` parameter for video generation.

**Cliffhanger loop** (OLD-1 PSY-007): For 60s videos, end mid-action to trigger rewatching. Example: "And the one thing that changed everything was—" [cut to start]. Use sparingly — this can frustrate viewers if overused.

**Mid-point re-hook for 60s content** (OLD-4 CP-005): Insert a secondary hook or mini-mystery at the 25-30s mark to combat the natural attention dip. Examples: "But here's what nobody tells you...", a visual pattern interrupt, or a new question. Critical for maintaining completion rates on longer content.

**60s timecoded script template** (OLD-4 ST-001):
```
0:00-0:03  HOOK {HOOK}: Result-first or curiosity gap [P1 CORE]
0:03-0:08  PROBLEM: Why this matters to parents [P2 CONTEXT]
0:08-0:18  DEMONSTRATION A: Primary activity [P1 CORE]
0:18-0:25  LEARNING: What child develops [P3 DEPTH]
0:25-0:30  RE-HOOK: "But here's the thing..." [P2 CONTEXT]
0:30-0:45  DEMONSTRATION B: Variation or progression [P3 DEPTH]
0:45-0:55  PRACTICAL TIP: How to do this at home [P2 CONTEXT]
0:55-1:00  CTA: Follow/save/comment [P1 CORE]
```

Variable beat cadence: **3-5 seconds** for P1 content (hooks, snackable clips) for viral energy. **6-8 seconds** for P2/P3 content (educational, deep dives) for calm Montessori tone.

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

**CTA variations** — rotate across videos:
- "Follow for more [topic]" (standard)
- "Save this for later" (bookmark trigger)
- "Would you let your baby try this? Comment below" (question-based, highest engagement — OLD-1 PSY-009)
- "Share with a parent who needs this" (share trigger)
- "Tag a mum who needs to see this" (AU-specific share trigger)

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
- This accommodates the estimated 69-74% of mobile viewers who may start with sound off (earlier figures of 85-92% are from outdated 2016-era studies — see SYNTHESIS.md sound-off data correction)
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
| Negative FB % | Swipe-away rate, "Not Interested" (OLD-4 AK-003) |
| Per-1K metrics | Saves/1K, shares/1K, comments/1K for cross-video comparison (OLD-4 AK-002) |

### Key Metrics

- **North star:** 65%+ 3-second retention → 4-7x more impressions (OpusClip Nov 2025 — general short-form benchmark; establish own parenting-niche baseline in weeks 1-4)
- **TikTok boost trigger:** 75% completion rate (2A line 71)
- **Instagram hook window:** 1.7 seconds (Dataslayer.ai, 2B line 36)
- **Faces in first 3s:** +35% retention (Zebracat 2025, 2B line 36)

### Testing Protocol

1. Single variable isolation per test (change only one thing)
2. Wait 24-48 hours — TikTok needs ~20K views for significance
3. Track 3-sec retention, avg watch time, completion rate, save rate, share rate
4. 3-5 underperforming videos won't damage standing; 8-10+ consecutive will

### Weekly Business Review (WBR) Dashboard

One-page weekly review template — forces data-driven decisions (OLD-1 ANL-011):

| Section | Metrics | Action |
|---------|---------|--------|
| **Performance Summary** | Total views (7d), weighted avg retention, avg completion rate | Track trend (up/down/flat) |
| **Top 3 Videos** | Highest performing by 3-sec retention | Identify what worked — replicate |
| **Bottom 3 Videos** | Lowest performing by 3-sec retention | Diagnose by drop-off pattern (hook/CTA/pacing) |
| **Engagement Totals** | Saves, shares, comments, follows gained | Track per-1K normalised metrics |
| **Experiment Results** | Current A/B test hypothesis + result | Single variable isolation |
| **Negative Feedback** | Swipe-away rate, "Not Interested" presses (Instagram: "Viewed vs Swiped Away" in Insights) | Negative signals weigh MORE in algorithms (OLD-4 AK-003) |
| **Next Week Plan** | Content to produce, tests to run, issues to fix | Actionable items only |

Review every Sunday during the 30-minute analytics check (Section 1 weekly rhythm).

### A/B Test Decision Rubric

Four-outcome framework for interpreting test results (OLD-4 CS-004, generalised from format testing to any variable):

| Outcome | Criteria | Action |
|---------|----------|--------|
| **A wins clearly** | >5 percentage point difference, n≥10 per variant, 500+ views each (OLD-3 ANL-008) | Scale variant A. Document why it worked. |
| **B wins clearly** | Same thresholds, B outperforms | Scale variant B. Update templates. |
| **Inconclusive** | <5 percentage point difference OR insufficient sample | Extend test (more videos) or try a hybrid approach |
| **Both fail** | Neither variant meets 65% 3-sec retention target | Diagnose CONTENT, not format. The problem is the topic or execution, not the variable being tested. |

**Key rule:** Test ONE variable at a time. Wait 24-48 hours minimum (TikTok needs ~20K views for significance).

---

## Build Priority Plan

### Prerequisites (Before Week 1)

- [ ] Confirm 8GB VRAM (CLAUDE.md says 4GB — user confirms 8GB)
- [ ] Purchase/activate DaVinci Resolve Studio license
- [ ] Set up Windows Python environment (DaVinci scripting is Windows-only)
- [ ] Create TikTok and Instagram accounts
- [ ] Budget allocation: ~$100-120/month for simultaneous tool subscriptions during testing
- [ ] **⚠️ TIME-SENSITIVE:** Sign up for Envato VideoGen ($16.50/mo promo) **before Feb 25, 2026 deadline**. Grab immediately even if not primary tool.

### Week 1: Foundation (Test Before Code)

- [ ] Verify Pika Standard/Pro license terms (Standard now includes commercial use)
- [ ] Create BB Baby hero character (Brancusi-inspired sculptural, warm clay-amber, subsurface glow)
  - Use Step 1 prompts from Section 3 — NOT Pixar style (Pixar is in the negative prompt list)
  - Lock `--oref` + `--sref` with hero image for double consistency
- [ ] Test --sv 1 (warmth) vs --sv 6 (default) with hero reference
- [ ] Test --sw permutation: `--sw {0, 200, 400, 600, 800, 1000}` with BB style reference
- [ ] Test clay term variants: "claymation" vs "3D clay animation" vs "soft matte clay surface" across Kling, Pika Pro, MJ
  - Pika free tier has only 80 credits/month — budget carefully
  - Expect Claymation distortions in Pika; use "3D clay animation" or "soft matte clay surface" instead
- [ ] Test multi-person scene success rate (parent + baby) — expect ~20% success in MJ
- [ ] Test Qwen3-TTS with Australian voice reference (already installed, clone from short sample)
- [ ] Cross-reference BB-Writer agent (`/web/.claude/agents/BabyBrains-Writer.md`) for AU English in all text generation — do NOT duplicate localisation rules in multiple places
- [ ] Generate 3 test videos end-to-end manually (no automation)
- [ ] Test burned-in caption workflow in DaVinci Studio (Effects > Titles > Animated > Word Highlight)

### Week 2: Audio + Script Pipeline

- [ ] Test Qwen3-TTS cloned Australian voice quality (already installed) vs Fish Audio API (~$11/mo Plus tier)
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
- [ ] Implement A/B tracking spreadsheet (12 columns — see Tracking Spreadsheet Structure above)
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

---

## Automation Roadmap

Automation items ordered by ROI. Implement A-1 through A-4 first (high priority, low complexity). Items A-5 through A-12 are future additions once the manual pipeline is reliable.

### High Priority (Implement First)

**A-1: Whisper WER QC Harness** (OLD-2 QCI-001)
- Extract audio from finished video → transcribe with faster-whisper → compare against reference SRT → compute WER
- Fail if WER >10%. Log to tracking spreadsheet.
- Implementation: Adapt OLD-2's wer_harness.py for current pipeline. Add as post-assembly QC step.

**A-2: Caption Safe-Zone Validator** (OLD-3 PLT-001/002/003)
- Parse .ASS subtitle MarginV value → check against per-platform thresholds → generate pass/fail report
- Run before batch export step. Re-verify pixel values quarterly (platform UIs change).

**A-3: Audio Level Checker** (OLD-2 PLT-003)
- FFmpeg loudnorm filter: `ffmpeg -i input.mp4 -filter:a loudnorm=print_format=json -f null /dev/null`
- Pre-export check flags deviations from -14 LUFS, TP > -1.5dB, or VO outside -12 to -6 dBFS.

**A-4: {HOOK} Token Validation** (OLD-4 ST-008)
- Regex check that first VO line of every script contains a hook marker. Catches scripts starting with preamble instead of hook.
- Run during Monday script-writing session before production begins.

### Medium Priority (After Manual Pipeline Works)

**A-5: Cross-Posting Stagger Scheduler** — Takes 12 exported files, assigns to optimal AU posting times (AEDT/AEST seasonal) per platform/day, queues uploads. n8n or Python cron.

**A-6: n8n Watch-Folder Pipeline** — Monitors inbox for MJ clips, checks for matching VO/subtitle files, routes through processing pipeline. Complete 10-node design exists in OLD-2.

**A-7: Platform-Specific Caption Generator** — From single script/brief, auto-generate platform-specific captions (TikTok raw/conversational, Instagram polished, YouTube keyword-rich, Facebook community).

**A-8: Hashtag Rotation System** — JSON pool of AU hashtags categorised by bucket (niche/medium/broad), random selection per post. Prevents same-hashtag fatigue.

**A-9: MJ Prompt Generation from YAML Brief** — Auto-generate MJ prompts from YAML clip brief by filling template with setting, camera, AU localiser, and character reference parameters.

### Lower Priority (Scale Phase)

**A-10: Shot Cadence Analyser** — FFmpeg scene detection validates no static shot exceeds threshold (3-5s for P1, 6-8s for P2/P3).

**A-11: Watermark Detection Pre-Cross-Post** — Detect platform watermarks before cross-posting (Instagram suppresses TikTok-watermarked content).

**A-12: Upscaler A/B Test Framework** — 12-clip comparison with MOS, Sobel edge, CER. For evaluating Real-ESRGAN vs Topaz vs DaVinci Super Scale.

### n8n Context

n8n is a watch-folder automation orchestrator. A complete 10-node workflow design exists in OLD-2 (inbox monitoring → slug extraction → file validation → conditional routing → FFmpeg finishing → Whisper WER QC → JSON sidecar → webhook notification). **Priority: MEDIUM.** Get the core manual pipeline working first (Steps 1-7), then add n8n as an automation layer. n8n 2.0 released December 2025.

### Upscaling Strategy

| Tier | Source | Upscaler | Cost | Use Case |
|------|--------|----------|------|----------|
| **Bulk** (90%+) | 480p (MJ Relax) | Real-ESRGAN 2x → 1080p | $0 | Most clips |
| **Hero** (2-3/week) | 480p or 720p | Topaz Proteus → 1080p | License fee | Flagship content |
| **Skip** | 720p+ (already HD) | None or Lanczos | $0 | Already meets 1080p |

**TODO:** Test DaVinci Resolve 20 Super Scale (Studio only, AI upscaling) on sample clips before committing to external tools.

SD (480p) + upscale is definitively cheaper than HD generation. MJ Relax mode gives unlimited 480p generations (Standard $30/month). MJ Fast at 720p costs 3.2x more GPU minutes. Quality difference after upscaling is marginal for stylised clay content.
