# Complete DaVinci Resolve Studio pipeline for AI-generated short-form video

**DaVinci Resolve Studio provides a professional-grade assembly pipeline for high-volume AI-generated content production**, offering scripting automation, Power Bins for brand assets, and Fairlight audio tools that justify using it over simpler alternatives. For producing 25-35 stylized clay-aesthetic videos monthly, the optimal approach combines DaVinci's color grading and audio capabilities with selective use of tools like CapCut for trendy caption styles and Repurpose.io for cross-platform distribution. Your existing MidJourney/Kling/Pika/Hailuo workflow pairs well with DaVinci's batch processing, and notably, **rendering through DaVinci automatically strips most metadata** including AI-identifying information—though platform disclosure requirements still apply.

---

## Project setup for 9:16 vertical short-form video

The foundation for efficient batch production starts with proper project configuration. Set your timeline resolution to **1080×1920** (or 2160×3840 for 4K masters), frame rate to **30fps** for standard content (60fps for fast motion), and use the "Use vertical resolution" checkbox available since DaVinci 18.1. Access settings via File → Project Settings (Shift+9).

**Optimal timeline track structure** for AI content assembly:
- V1: Main AI video clips
- V2: B-roll/overlay footage  
- V3: Graphics/logos/watermarks
- V4: Captions (subtitle track)
- A1: Primary voiceover
- A2: Background music
- A3: Sound effects

For export, use **H.264 codec in MP4 container** at 8-10 Mbps bitrate with AAC audio at 48kHz. This universal preset works across TikTok, Instagram Reels, YouTube Shorts, and Facebook without platform-specific variations. TikTok accepts files up to 500MB-1GB, Instagram up to 650MB, and YouTube Shorts up to 256GB technically—though short-form files rarely exceed 50MB.

**Power Bins** are critical for brand consistency across 25-35 monthly videos. Enable them via Media Pool → ellipsis menu → Show Power Bins. Unlike regular bins, Power Bins persist across ALL projects in your database, making them perfect for storing animated logos, music beds, sound effects, transitions, and watermarks. Organize with subfolders: Brand Assets/Logos, Audio/Music Library, Audio/Sound Effects, Transitions, and Color/PowerGrades.

---

## Automation and scripting capabilities

DaVinci Resolve Studio unlocks Python and Lua scripting via the Resolve Script API, enabling substantial automation for batch production. The free version lost UIManager support in v19.1, making Studio essential for full automation workflows.

**What can be scripted:**
- Auto-import media from folder structures using `MediaStorage.AddItemListToMediaPool()`
- Create timelines and append clips programmatically with `MediaPool.AppendToTimeline()`
- Apply LUTs across clips with `TimelineItem.SetLUT(nodeIndex, lutPath)`
- Batch render to multiple formats using the render queue API
- Copy grades between clips with `TimelineItem.CopyGrades()`

**Key GitHub resources for existing scripts:**
- **aman7mishra/DaVinci-Resolve-Python-Automation** — Complete automation including import, timeline creation, and rendering
- **X-Raym/DaVinci-Resolve-Scripts** (63 stars) — Organized Lua scripts for markers, editing, grading, media pool operations
- **pedrolabonia/pydavinci** — Python wrapper with auto-completion and type hints
- **jkf87/davinci_resolve_autocutter** — AI transcription and auto-cutting with Whisper integration

For batch export to multiple platforms, the workflow involves adding the same timeline to the Render Queue multiple times with different presets (TikTok, Instagram, YouTube), then clicking "Render All" to process sequentially. While DaVinci can't export to multiple formats simultaneously in a single pass, the queue system handles this efficiently.

**Fusion macros** extend automation to motion graphics. Create your brand intro animation, select nodes (except MediaIn/MediaOut), right-click → Macro → Create Macro, and save to `Templates/Edit/Titles/`. The macro becomes available in Effects Library after restart.

---

## Metadata handling and C2PA considerations

**Critical finding: Most AI video tools do NOT embed C2PA metadata.** Your workflow tools—Kling, Pika, and Hailuo—primarily use visible watermarks (removable with paid plans) rather than embedded provenance data. MidJourney uses IPTC Digital Source Type but not full C2PA. OpenAI's DALL-E/Sora and Adobe Firefly DO embed C2PA, so be aware if you incorporate those tools.

**DaVinci Resolve effectively strips metadata during render.** Exported files do not contain original source metadata, and there's no option to preserve it in the Delivery page. This means rendering through DaVinci handles metadata scrubbing automatically without additional steps.

If you need explicit metadata removal from source files before import:

```bash
# FFmpeg: Strip all metadata
ffmpeg -i input.mp4 -map_metadata -1 -c:v copy -c:a copy output.mp4

# ExifTool: Remove all metadata
exiftool -all= -overwrite_original video.mp4

# Check for C2PA (if concerned about specific files)
c2patool file.jpg
```

**Platform Terms of Service require content-level disclosure** for realistic AI-generated content regardless of metadata. TikTok requires the "AI-generated" toggle for realistic content and auto-detects C2PA tags. Meta applies "AI Info" labels when detecting C2PA from tools like DALL-E. YouTube requires disclosure via upload toggle for synthetic content depicting realistic events or people. Stripping metadata isn't prohibited, but failing to disclose AI generation of realistic content violates platform policies.

**Preserve copyright metadata** for content protection. After export, add using ExifTool:
```bash
exiftool -Copyright="© 2026 Your Name. All Rights Reserved." -Creator="Your Name" video.mp4
```

---

## Caption workflow for maximum engagement

**The 85% statistic holds:** Industry research confirms 75-85% of social media videos are watched with sound off, with captions driving **12-40% increases in watch time**. For parenting/educational content, captions are non-negotiable.

**DaVinci Resolve Studio's native transcription** (since v18.5) offers one-click caption generation: Timeline → Create Subtitles from Audio. Select English (Australian isn't explicitly optimized but works), set max characters per line to **15-18 for vertical video**, and choose a caption preset. Transcription runs at approximately 9x real-time on M1 Max hardware.

For better Australian accent accuracy, use **Whisper large-v3 locally** via AutoSubs (free DaVinci plugin at github.com/tmoroney/auto-subs) or StoryToolkitAI. Research shows American English gets best Whisper accuracy, with Australian slightly lower—the large-v3 model compensates.

**Caption styling for TikTok/Reels performance:**
- **Font:** Montserrat Bold or Bebas Neue (analyzed across 2M videos, Montserrat appeared in 1.2M)
- **Size:** 60-72pt for vertical video
- **Style:** White text with 2-4px black stroke (universal contrast)
- **Position:** Upper-middle third, **300-350px minimum from bottom** to clear platform UI
- **Animation:** Word-by-word highlight is the current trend leader, with each word lighting up as spoken

**DaVinci Resolve 20's animated subtitles** offer built-in word highlighting: Effects → Titles → Animated → Word Highlight. Drag the animation onto your subtitle track header and customize in Inspector.

**Batch caption workflow for 25-35 videos monthly:**
1. Collect all voiceover files for the week
2. Batch transcribe using Whisper CLI: `for file in *.mp3; do whisper "$file" --model medium --output_format srt; done`
3. Import SRTs to pre-templated DaVinci projects with styled subtitle tracks
4. Quick sync review, fix major issues only
5. Export with burn-in captions

**Time estimate per video:** 6-11 minutes with automation vs 16-26 minutes manual.

---

## Color grading for brand consistency

For your warm clay-amber aesthetic with bioluminescent glow, the optimal approach is **hybrid: establish the look in AI prompts, then refine in post**. Prompts excel at overall mood and lighting direction; DaVinci excels at precise hue control and matching multiple AI-generated clips.

**PowerGrades** are essential for brand consistency. Create your grade in the Color page using a node structure:
- Node 1: Tonality (Lift/Gamma/Gain for exposure)
- Node 2: Balance (push offset toward gold/amber)
- Node 3: Saturation (HSV mode, boost saturation in gamma)
- Node 4: Secondary (Lum vs Sat curve for highlight control)
- Node 5: Look (split toning or LUT)
- Node 6: Post (vignette, final adjustments)

Save to PowerGrade album: Gallery → Grab Still → drag to PowerGrade folder. Export as .DRX + .DPX files for backup. Apply to any clip by middle-clicking the grade thumbnail or dragging from Gallery.

**Bioluminescent glow effect in Fusion:**
1. Open clip in Fusion page
2. Add Soft Glow + Glow nodes: MediaIn → Soft Glow → Glow → MediaOut
3. Settings: Filter = Gaussian, Glow Size = 0.1-0.15, Threshold = 0.4-0.7
4. Use Color Scale to tint glow toward cyan/amber for bioluminescent appearance

**For Edit page glow:** Effects → Resolve FX Light → Glow. Set Shine Threshold lower for more glow, use Color Filter picker for tint.

**LUT creation:** Right-click graded clip thumbnail → Generate 3D LUT → 33 Point Cube. Note that LUTs only store color transformation—not nodes, power windows, qualifiers, or effects. For complete grade transfer, use PowerGrades.

---

## Audio mixing and sync optimization

**Handling AI video lip-sync limitations:** Since AI-generated characters often have generic or no lip movement, treat the voiceover as narration over illustrative visuals rather than synced dialogue. Cut video to audio rhythm rather than matching audio to video. For cases requiring lip-sync, tools like Vozo AI, Sync.so, or Rask AI can post-process AI video with realistic lip movement.

**Recommended levels for educational content:**
| Element | Target Level |
|---------|-------------|
| Voiceover | -12 to -6 dBFS |
| Background music (under VO) | -24 to -18 dBFS |
| Music (solo sections) | -12 to -6 dBFS |
| Sound effects | -18 to -12 dBFS |

**Audio ducking in Fairlight** automates music levels:
1. Switch to Fairlight page (Shift+7)
2. Open Mixer → double-click Dynamics on voiceover track → enable Sidechain → Set to "Send"
3. On music track, double-click Dynamics → select "Music Pumper" preset → enable Sidechain compressor → set Source to voiceover track
4. Adjust: Threshold -30 to -20 dB, Ratio 3:1-6:1, Attack 10-50ms, Release 200-500ms

**LUFS targets for platforms:**
- TikTok/Instagram Reels: -10 to -12 LUFS (creators push louder)
- YouTube: -14 LUFS
- Facebook: -13 LUFS
- **Universal safe target: -14 LUFS** (platforms normalize automatically)

**Sound effects improve engagement.** Meta research shows videos with audio cues aligned to visuals have **1.5x higher engagement**. For parenting/educational content, use gentle transition sounds (soft whooshes, pops), subtle emphasis chimes for learning moments, and warm ambient textures. Limit to 2-3 SFX per 30-60 second clip. Avoid harsh or startling sounds for family content.

**Free SFX sources:** Uppbeat (creator-focused), Pixabay, Freesound, ZapSplat.

---

## Multi-platform export specifications

**Universal export preset (works for all platforms):**
- Resolution: 1080×1920
- Codec: H.264 (MP4)
- Bitrate: 8-10 Mbps VBR
- Frame rate: 30fps
- Audio: AAC-LC, 128-192 kbps, 48kHz stereo

**Platform-specific nuances:**
| Platform | Max File Size | Max Length | Notes |
|----------|---------------|------------|-------|
| TikTok | 500MB-1GB | 60 min upload | 15-34 seconds optimal engagement |
| Instagram Reels | 650MB | 90 sec standard, 15 min upload | Leave bottom 310px clear |
| YouTube Shorts | 256GB (technical) | 3 minutes | Width must be ≤1080px to qualify |
| Facebook Reels | 1GB | 90 seconds | All FB videos now treated as Reels |

**Batch export workflow:** Create render presets for each platform (Deliver page → configure settings → three-dot menu → Save As New Preset). Add the same timeline to Render Queue multiple times with different presets, then Render All.

**Smart Reframe** (Studio only) handles horizontal-to-vertical conversion with AI subject tracking: Inspector → Video → Smart Reframe → set Object of Interest to Auto → Reframe. Results require manual touch-up for complex shots but work well for talking heads.

**For 4:5 Instagram feed posts:** Duplicate timeline → right-click → Timeline Settings → uncheck "Use Project Settings" → set to 1080×1350.

---

## DaVinci Resolve versus CapCut for this workflow

**CapCut excels at:** Trendy animated captions (one-click word-by-word highlight, 100+ styled templates), viral template library updated weekly, TikTok integration (same parent company), speed for simple edits, and mobile editing. CapCut's auto-caption with stylized templates significantly beats manual DaVinci caption workflows for social-native content.

**DaVinci Resolve excels at:** Professional color grading (no comparison), complex multi-track editing with proper ripple behavior, Fairlight audio post-production, scripting automation, output quality control, and team collaboration.

**Optimal hybrid workflow for your use case:**
1. **DaVinci Resolve:** Create master edit with professional color grading, audio mixing, and brand template application
2. **DaVinci:** Export high-quality master file
3. **CapCut (optional):** Add trendy caption animations, viral effects, platform-specific elements
4. **Repurpose.io ($25/month):** Auto-distribute and resize across TikTok, Instagram, YouTube, Facebook with automatic watermark removal and scheduling integration

For 25-35 videos monthly at consistent quality, **DaVinci Resolve Studio as primary with CapCut for caption polish** provides the best balance. CapCut's free tier handles caption styling adequately; use it specifically for that step rather than as the primary editor.

**Other tools worth considering:**
- **Repurpose.io:** Auto-repurposes content to 10+ platforms with resizing
- **Creatomate:** API-based video automation for programmatic generation
- **Opus Clip:** AI extracts best clips from long-form content

---

## Template system for consistent branding at scale

**Create a master project template containing:**
- Pre-configured 1080×1920 timeline settings
- Track structure (V1-V4, A1-A3) with labeled tracks
- Brand intro (0.5-1s) saved as Fusion macro and stored in Power Bin
- Caption style preset (save via Inspector → Track tab → three-dot menu → Save Track as Preset)
- PowerGrade for brand color look
- Audio template with pre-configured ducking on music track
- Brand outro with CTA in Power Bin
- Watermark/logo overlay (create adjustment clip with logo, store in Power Bin, place on top video track)

**Template application workflow:**
1. Duplicate master project template (right-click → Save Project As)
2. Import new AI video clips and voiceover to Media Pool
3. Replace placeholder clips on timeline (drag from Media Pool)
4. Import SRT → apply saved caption style preset
5. Apply PowerGrade from Gallery (middle-click or drag)
6. Drag brand intro/outro from Power Bins to timeline
7. Adjust music ducking if needed (should auto-work from template)
8. Export using saved render preset

**Time savings:** With this system, each video should take **15-25 minutes** from raw assets to export-ready, enabling 25-35 videos monthly with approximately 8-15 hours of assembly work.

**Power Bin organization for brand assets:**
```
Power Bins/
├── Brand Assets/
│   ├── Logos (PNG with alpha)
│   ├── Animated Intros
│   └── Animated Outros (with CTA)
├── Audio/
│   ├── Music Library/
│   ├── Sound Effects/Transitions
│   └── Audio Stingers
├── Graphics/
│   ├── Lower Thirds
│   └── Watermarks
└── Color/
    └── PowerGrades/
```

**Important limitation:** Power Bins reference files—they don't copy them. Keep source files on permanently attached storage with consistent paths.

---

## Key resources and tutorials

**Official documentation:**
- Blackmagic Training: blackmagicdesign.com/products/davinciresolve/training
- Scripting API: Help → Documentation → Developer (README.txt)
- Formatted API docs: extremraym.com/cloud/resolve-scripting-doc/ (v20.3)

**YouTube educators:**
- **Casey Faris** (Ground Control) — Blackmagic Certified Trainer, Fusion specialist
- **MrAlexTech** — Comprehensive Resolve tutorials, Magic Animate plugin creator
- **JayAreTV** — PowerGrade workflows, Fusion color nodes

**Script repositories:**
- github.com/X-Raym/DaVinci-Resolve-Scripts
- github.com/aman7mishra/DaVinci-Resolve-Python-Automation
- github.com/tmoroney/auto-subs (Whisper caption plugin)

**Template marketplaces:**
- Mixkit.co (free templates)
- Motion Array (paid, extensive library)
- Envato Elements (subscription)

**Caption tools:**
- AutoSubs: github.com/tmoroney/auto-subs (free Whisper-based)
- Snap Captions 2: orsonlord.com (pay-what-you-want DaVinci plugin)

---

## Implementation checklist

**One-time setup (invest 2-4 hours):**
- [ ] Create master project template with vertical settings
- [ ] Configure Power Bin folder structure
- [ ] Import brand assets to Power Bins
- [ ] Create and save PowerGrade for clay-amber-glow aesthetic
- [ ] Build Fusion macro for brand intro animation
- [ ] Configure Fairlight audio template with ducking
- [ ] Create render presets for each platform
- [ ] Install AutoSubs or configure Whisper for caption generation

**Per-video workflow (15-25 minutes):**
- [ ] Duplicate project template
- [ ] Import AI clips + voiceover
- [ ] Generate/import SRT captions
- [ ] Assemble timeline (drag from Power Bins)
- [ ] Apply PowerGrade
- [ ] Quick audio level check
- [ ] Export via render preset
- [ ] Distribute via Metricool or Repurpose.io

This pipeline transforms DaVinci Resolve Studio into an efficient assembly line for AI-generated content while maintaining professional-grade output quality—the exact balance needed for high-volume short-form production.