# Prompt PE: Claude Code Production Automation Pipeline

## Context

I'm building an AI-assisted content production pipeline for "Baby Brains" -- a Montessori-inspired parenting education brand producing stylized 3D / clay-aesthetic short-form social videos for adults (parents). I use Claude Code in VS Code as my primary development environment.

**The pipeline is now confirmed (from prior research PA-PD, PF):**

1. **Knowledge Base** (Montessori activities, developmental science) → script via 3-act template (Hook/Meat/CTA) with 7 hook variations per entry
2. **MidJourney V7 Standard** ($30/month) → character-consistent scene images using --oref and --sref
3. **Pika 2.5 Pro** ($28/month) → primary video clips ≤25s (motion-only prompts over MJ images, Pikaffects for clay deformation)
4. **Kling O1 Pro** ($37/month) → secondary video for 60s content (6x 10s clips stitched, Elements for character)
5. **Hailuo Max** ($199.99 one-time burst month) → library building via 01 Live model + API automation
6. **Voice**: Self-recorded Australian VO (primary), Chatterbox Turbo local TTS ($0, 8GB VRAM), ElevenLabs ($5/month fallback)
7. **QC in Claude Code**: ffmpeg keyframe extraction → Claude visual review → Video Quality MCP scoring
8. **DaVinci Resolve Studio** → assembly using Power Bins, PowerGrades, Fairlight ducking, Fusion glow, AutoSubs captions
9. **Distribution**: Metricool (50 posts/month free) or Repurpose.io ($25/month) → TikTok, Instagram, YouTube Shorts, Facebook

**My environment:**
- 8GB VRAM GPU (RTX), 32GB RAM
- MCP (Model Context Protocol) server capability in Claude Code
- Python development environment
- ffmpeg installed
- DaVinci Resolve Studio (full license)
- Running WSL2 on Windows

## Research Required

### 1. MCP Servers: Installation & Configuration for THIS Pipeline

We've identified these MCP servers as relevant. I need INSTALLATION INSTRUCTIONS and REAL-WORLD CONFIGURATION for each:

**Video Quality MCP** (hlpsxc/video-quality-assessment-mcp):
- Exact installation steps (npm/pip/docker?)
- How to configure in Claude Code's MCP settings (`.claude/mcp_servers.json` or similar)
- Input format: does it accept local file paths? URLs? What video formats?
- Output format: does it return structured JSON with PSNR/SSIM/VMAF? What are the pass/fail thresholds for social media quality?
- Can it batch-process a folder of clips?
- Does it require GPU? Will it run on my 8GB VRAM alongside other tools?

**OpenCV MCP** (GongRzhe/opencv-mcp-server):
- Exact installation steps
- Claude Code configuration
- Key functions needed: frame extraction from video, image comparison (for character consistency checking), edge detection, histogram analysis
- Can it extract keyframes at a specified interval (e.g., every 0.5s)?
- Can it compare two images and return a similarity score? (for checking generated clip vs reference image)
- Memory/GPU requirements

**Video-Audio MCP** (misbahsy/video-audio-mcp):
- Installation and configuration
- Can it: concatenate clips with crossfade transitions? Add VO track to video? Burn in SRT captions? Strip metadata?
- Does it expose ffmpeg commands that Claude can call, or does it abstract them?
- Could it handle simple assembly (clips + VO + music) without needing DaVinci for basic videos?

**Additional MCP servers** -- search for any MCP servers released up to February 2026 that handle:
- Image generation API wrappers (MidJourney third-party APIs, Kling API, Pika API)
- TTS / voice generation (Chatterbox, ElevenLabs wrappers)
- Social media scheduling (Metricool, Buffer, Later APIs)
- File organization / asset management
- Subtitle/caption generation (Whisper-based)
- SQLite database management (for asset tracking)
- Image manipulation (resize, crop, watermark for thumbnails)

For EACH server found: GitHub URL, star count, last update date, installation method, and whether it's actively maintained.

### 2. ffmpeg Scripts for THIS Specific Pipeline

I need WORKING scripts (Python-callable and/or bash) for each step of our pipeline. These should be immediately usable, not theoretical:

**Keyframe extraction for QC:**
```bash
# Extract frames at 2fps from a clip for Claude visual review
ffmpeg -i input.mp4 -vf "fps=2" output_%03d.png
```
- Wrap this in a Python function that processes all .mp4 files in a folder
- Output frames to a `_qc/` subfolder alongside the video
- Include frame numbering that maps back to timestamp

**Multi-clip concatenation with transitions:**
- Input: ordered list of clips in a folder (sorted by filename)
- Transitions: crossfade (0.5s), hard cut, or configurable
- Output: single assembled video
- Handle clips of different resolutions/framerates gracefully (normalize first)

**Voiceover overlay:**
- Input: video clip + .wav voiceover file
- Align VO to start of video
- Mix: VO at -6 dBFS, video audio ducked to -24 dBFS (or muted)
- Output: combined video

**Caption burn-in:**
- Input: video + .srt file
- Style: white Montserrat Bold, 60pt, 2px black stroke, positioned in upper-middle third
- Output: captioned video
- Research: does ffmpeg's drawtext support word-by-word highlight timing? Or is this DaVinci-only?

**Metadata stripping:**
```bash
ffmpeg -i input.mp4 -map_metadata -1 -c:v copy -c:a copy output_clean.mp4
```
- Wrap in Python batch processor for all files in a folder
- Verify C2PA removal using c2patool (if available)
- After stripping, add copyright: `exiftool -Copyright="© 2026 Baby Brains" video.mp4`

**Platform-specific export presets:**
- TikTok: 1080x1920, H.264, 2000-4000 kbps, 30fps, AAC 128kbps
- Instagram Reels: 1080x1920, H.264, 3500-4500 kbps, 30fps, AAC 128kbps
- YouTube Shorts: 1080x1920, H.264, 8000-15000 kbps, 30fps, AAC 192kbps
- Facebook: 1080x1920, H.264, 4000-8000 kbps, 30fps, AAC 128kbps
- Batch: take a master file and output all 4 platform versions

**Contact sheet / thumbnail grid:**
- Extract 6-9 frames evenly spaced from a video
- Arrange in a 3x3 grid with timestamps
- Output as single PNG for quick visual review

### 3. Content Database & Script Generation System

The content-to-script pipeline (from PF research) follows this flow:
```
Knowledge Base Entry → 7 Hook Variations → Scene Breakdown → AI Prompts → Production
```

Research the best implementation approach:

**Database structure** (SQLite preferred for local, version-controllable):
```sql
-- Core tables needed:
-- activities (name, age_range_min, age_range_max, montessori_principle, key_learning, description)
-- scripts (activity_id, hook_pattern, full_script_text, status)
-- scenes (script_id, scene_number, duration_seconds, priority [P1_CORE|P2_CONTEXT|P3_DEPTH],
--         vo_text, ai_visual_prompt, camera_movement, transition_in, transition_out)
-- clips (scene_id, take_number, tool_used, file_path, qc_status, qc_notes, qc_score)
-- videos (script_id, duration_tier [60s|30s|15s], assembled_file_path, platform,
--         publish_date, metrics_3sec_retention, metrics_views)
```

**Scene priority system (critical for multi-length derivatives):**
Each scene is tagged P1/P2/P3. From one 60s master script, three video lengths are derived:
- 60s master = P1 + P2 + P3 scenes
- 30s derivative = P1 + P2 only (drop P3, DaVinci closes gaps)
- 15s hook loop = P1 only (hook + hero moment + CTA)
All three use the SAME generated clips -- no re-generation. The DB query for building a 30s cut list: `SELECT * FROM scenes WHERE script_id=? AND priority IN ('P1_CORE','P2_CONTEXT') ORDER BY scene_number`

- Is SQLite the right choice, or should we use JSON/YAML files for easier editing?
- How to integrate this with Claude Code so I can query: "show me all unpublished scripts for 8-12 month activities"
- Can we build a Claude Code slash command or MCP tool that generates a script from a knowledge base entry?

**Template system:**
- The script template from PF research: Hook (15 words) → Problem (25 words) → Demo (50 words) → Learning (25 words) → Tip (20 words) → CTA (15 words)
- Character DNA prefix that gets prepended to every AI visual prompt:
  `"Clay-style baby, 12-month appearance, round face, curious bright eyes, soft cotton outfit in muted earth tones, Aardman-inspired aesthetic, warm clay-amber tones, bioluminescent subsurface glow"`
- The 7 hook variation matrix (Problem Statement, Result-First, Curiosity Gap, Authority, Pattern Interrupt, Relatable, Contrarian)
- How to implement this as a Python module that takes a KB entry and outputs 7 complete scripts with scene breakdowns and per-scene AI prompts?

**Prompt generation:**
- Input: scene description ("Baby character explores a wooden ring stacker, Montessori prepared environment")
- Output for MidJourney: Full prompt with --oref [URL], --sref [URL], --ow, --sw, --s, --v 7, negative prompts
- Output for Pika: Motion-only prompt + `-camera` command + `-neg` string + guidance scale
- Output for Kling: [Shot type] + [Camera] + [Subject+Style] + [Action+Endpoint] + [Environment] + [Lighting] + "claymation style, stop-motion aesthetic"
- Are there any existing tools or Python libraries that help with AI prompt templating?

### 4. QC Pipeline Implementation

Design the EXACT implementation for Claude Code-based QC:

**Trigger mechanism:**
- Option A: File watcher (watchdog Python library) monitors `04_RAW_GENERATIONS/` folder
- Option B: Manual command / Claude Code slash command: `/qc VID023_S02_T01_pika_raw.mp4`
- Option C: Batch QC command: `/qc-batch` processes all unreviewed clips
- Which is most practical for a solo creator? Are there MCP servers for file watching?

**QC workflow implementation:**
1. ffmpeg extracts keyframes at 2fps → saves to `_qc/` subfolder
2. Video Quality MCP scores the clip (PSNR, SSIM, VMAF) → structured results
3. Claude receives frames as images + VQ scores + the original MJ reference image
4. Claude evaluates against checklist:
   - Character proportions match reference (head shape, body ratio)
   - Bioluminescent glow consistent (no flicker, no color drift)
   - Hands: correct finger count, no melting/morphing
   - Face: expressions readable, no warping
   - Background: stable, no scene switching
   - Motion: natural, no stuttering or jitter
   - Start/end frames clean for stitching
5. Results logged to SQLite `clips` table with qc_status (pass/fail/review) and qc_notes
6. Summary report generated (markdown or terminal output)

**Research questions:**
- Can Claude Code's vision capability reliably detect hand artifacts in 512px frames?
- What VMAF score threshold correlates with "social media acceptable" quality?
- Has anyone built a similar AI-assisted video QC pipeline? Find examples.
- Can we compare frames from generated clip against the source MJ image using OpenCV MCP?
- What's the most efficient frame resolution for QC? Full 1080p or downscaled 512px?

### 5. Voice Pipeline Integration

**Chatterbox Turbo setup:**
- Exact installation steps for Chatterbox on WSL2 with 8GB VRAM
- Python API / CLI usage for batch TTS
- Voice cloning: how to prepare the reference audio sample (format, duration, quality requirements)
- Can it run as a local API server that Claude Code calls?
- Memory management: can it coexist with other tools on 8GB VRAM?
- Latency per generation: how long for a 30-second voiceover?

**ElevenLabs API integration:**
- Python SDK setup and API key management
- Voice cloning via API (minimum sample requirements for Australian accent)
- Cost per minute of generated audio on Starter plan ($5/month, 30 min)
- Streaming vs file-based generation
- Any MCP server wrappers for ElevenLabs?

**Caption/SRT generation:**
- Since we HAVE the script text, we don't need speech-to-text -- we need text-to-timed-SRT
- Given: script text + generated .wav audio file
- Output: .srt file with accurate word-level timestamps
- Options: forced alignment (aeneas, gentle, WhisperX alignment mode) vs simple word-count-based timing
- Which approach gives best results for Australian-accented speech?
- Can this be done locally without API calls?

### 6. DaVinci Resolve Scripting Integration

DaVinci Resolve Studio has a Python/Lua scripting API. Research:

**Can Claude Code trigger DaVinci operations via scripts?**
- Auto-import clips from our asset folder structure
- Create a new timeline from a script's scene breakdown (auto-place clips in order)
- Apply the brand PowerGrade to all clips
- Apply audio template (ducking preset)
- Import SRT and apply caption style
- Add brand intro/outro from Power Bins
- **Create derivative timelines**: Duplicate the 60s master, programmatically remove scenes tagged P3 (for 30s) or P2+P3 (for 15s), apply cross-dissolves at new cut points
- Batch render to 4 platform presets × 3 duration variants (up to 12 exports per video)

**Practical limitations:**
- Does the scripting API require DaVinci to be running in the background?
- Can scripts be triggered from command line, or only from within DaVinci's console?
- Is pedrolabonia/pydavinci actively maintained and compatible with DaVinci 20?
- Are there any MCP servers that wrap the DaVinci Resolve API?

**What's automatable vs what requires manual work:**
- Which steps genuinely save time via automation vs which are faster to do manually?
- For 25-35 videos/month, is the scripting investment worth it, or is the template approach (duplicate project, drag clips) sufficient?

### 7. Hailuo Burst Automation (API-Based)

The burst month requires maximizing throughput. Research automation:

**fal.ai + Hailuo integration:**
- How to set up fal.ai account and connect to Hailuo 01 Live model
- API call structure: submit image + prompt → receive task_id → poll status → download
- Rate limits and concurrent generation limits via API
- Cost: does fal.ai charge on top of Hailuo subscription, or is it a pass-through?

**n8n workflow for bulk production:**
- The n8n template (workflows/7335) reads from Google Sheets and auto-generates
- Can this be adapted to read from our SQLite content database instead?
- Can n8n run locally (self-hosted) or does it require cloud?
- Alternative: can we build a simpler Python script that does the same thing (read prompts from DB → submit to API → poll → download → organize)?

**Download automation:**
- Hailuo has NO bulk download
- Can we automate individual downloads via browser automation (Playwright/Selenium)?
- Or does the API return direct download URLs?
- Auto-organize downloads into our folder structure with correct naming convention

### 8. Scheduling & Distribution Automation

**Metricool API:**
- Does Metricool have a public API? (Last checked: unclear)
- If yes: can we upload video + caption + hashtags + scheduled time from Python/Claude Code?
- If no: what's the best API-accessible scheduler for our 4 platforms?

**Platform upload APIs (current state, February 2026):**
- TikTok: Content Posting API availability, reach penalty vs native upload (verified data)
- Instagram: Reels upload via Meta Graph API -- current limitations, approval requirements
- YouTube Shorts: YouTube Data API v3 upload -- any Shorts-specific restrictions?
- Facebook: Video upload via Graph API -- current state

**Repurpose.io alternative:**
- Does it have an API, or is it manual upload only?
- Can it auto-detect and remove watermarks as claimed?
- Worth $25/month vs manual cross-posting?

**For each viable option:** exact setup steps, authentication requirements, rate limits, and whether Claude Code can invoke them directly.

---

## Output Format

For each section, provide:
1. **Recommended approach** (pick ONE, not multiple options)
2. **Installation/setup commands** (copy-pasteable)
3. **Working code snippets** (Python, tested where possible)
4. **Known limitations** (what WON'T work, so we don't waste time)
5. **Build priority** (what to build first vs defer)

Focus on practical, incrementally buildable automation. Start with the highest-ROI automation (QC pipeline and prompt generation) and defer nice-to-haves (full DaVinci scripting, scheduling API).
