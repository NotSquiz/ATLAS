# Prompt PD: Assembly & Post-Production Pipeline

## Context
I'm producing 25-35 stylized 3D / clay-aesthetic short-form videos per month for TikTok, Instagram Reels, YouTube Shorts, and Facebook. Videos range from 7-60 seconds. I have DaVinci Resolve Studio (full license, not free version). The production pipeline is:

1. Source material (Montessori activities, developmental science) -> Script
2. MidJourney / Kling IMAGE -> Character-consistent scene images
3. Pika / Kling / Hailuo -> Animated video clips (5-10s each)
4. Voice: Self-recorded Australian voiceover + Chatterbox TTS (local, 8GB VRAM)
5. **Assembly and post-production** (THIS PROMPT)
6. Scheduling and distribution via Metricool

I need the ASSEMBLY AND POST-PRODUCTION workflow optimized for speed and consistency.

## Research Required

### 1. DaVinci Resolve Studio for Short-Form AI Content
- Find REAL creators using DaVinci Resolve for AI-generated short-form content assembly
- Search YouTube ("DaVinci Resolve AI video workflow", "DaVinci Resolve short form template"), Reddit (r/davinciresolve, r/VideoEditing)
- What's the optimal project setup for short-form vertical video (9:16)?
- Timeline settings for TikTok/Reels (resolution, frame rate, codec)
- Template workflow: how to create a reusable template with placeholder tracks for video, voiceover, music, captions

### 2. DaVinci Resolve Automation & Batch Processing
- DaVinci Resolve Studio has Fusion, scripting, and macro capabilities. What can be automated?
- Can you batch-import clips, auto-arrange on timeline, and batch-export?
- Scripting: DaVinci Resolve uses Python/Lua scripting API. What operations can be scripted?
  - Auto-import media from folder structure
  - Auto-apply color grading / LUT across all clips
  - Auto-add burn-in captions from SRT
  - Auto-add intro/outro bumpers
  - Batch render to multiple formats/platforms
- Any existing scripts or templates for short-form content production?
- How does the "Power Bins" feature help with reusable assets (brand elements, music, transitions)?

### 3. Metadata Scrubbing (C2PA / EXIF Removal)
- MidJourney reportedly does NOT embed C2PA metadata (confirmed in our research)
- But other tools (Kling, Pika, Hailuo) -- do they embed C2PA or other AI-identifying metadata?
- How to verify: what tools detect C2PA metadata in images/video files?
- How to strip C2PA metadata if present:
  - ffmpeg methods
  - ExifTool methods
  - DaVinci Resolve: does rendering/exporting strip metadata automatically?
- EXIF data: what metadata do AI tools embed? (generation parameters, model name, etc.)
- Is metadata scrubbing against any platform's Terms of Service? (TikTok, Instagram, YouTube, Facebook)
- What metadata SHOULD we preserve or add? (copyright, creator attribution, etc.)

### 4. Caption / Subtitle Workflow
- TikTok and Instagram: burn-in captions are essential (85%+ watch with sound off on some platforms)
- Options for caption generation:
  - DaVinci Resolve built-in subtitle tools
  - Auto-caption tools (CapCut, Descript, Whisper-based)
  - SRT import workflow
- Style recommendations for parenting/educational content captions
- Font, size, position, animation -- what performs best on TikTok/Reels?
- Batch caption workflow: can you auto-generate captions from voiceover and batch-apply to multiple videos?

### 5. Color Grading for Consistent Brand Look
- How to create and apply a consistent color grade across all videos for brand recognition
- The Baby Brains aesthetic: warm clay-amber tones, bioluminescent glow, soft lighting
- Should color grading be done in DaVinci Resolve (post-production) or handled entirely in the AI generation prompt?
- LUT creation: can you create a custom LUT that enhances the bioluminescent glow look?
- Fusion: any node setups specifically useful for enhancing AI-generated stylized 3D content?

### 6. Audio Mixing & Sync
- Voiceover sync with AI-generated video clips: how to handle imperfect lip-sync or timing
- Background music: how to mix educational voiceover with calm background music (levels, ducking)
- Sound effects: should AI-generated content have sound effects? What improves engagement?
- DaVinci Resolve Fairlight: any automation for consistent audio levels across multiple videos?
- Audio templates: can you create a master audio template (music bed, VO track, SFX track) and batch-apply?

### 7. Multi-Platform Export
- Export settings for each platform:
  - TikTok (resolution, bitrate, codec, max file size)
  - Instagram Reels (same questions)
  - YouTube Shorts (same questions)
  - Facebook (same questions)
- Can DaVinci Resolve batch-export to multiple formats in one render pass?
- Does DaVinci Resolve support per-platform aspect ratio variations (9:16 vs 4:5 for IG feed)?
- Any tools that automatically reformat/resize for each platform?

### 8. DaVinci Resolve vs CapCut for This Workflow
- CapCut is free and popular for short-form content. But I already have DaVinci Resolve Studio.
- Is there anything CapCut does BETTER than DaVinci Resolve for AI short-form content?
- CapCut auto-captions, trending effects, TikTok integration -- are these worth using alongside DaVinci?
- Hybrid workflow: use CapCut for quick social-native features, DaVinci for premium production?
- Any other assembly tools worth considering? (Premiere, Final Cut, Creatomate for automation?)

### 9. Template System for Consistent Branding
- How to build a reusable production template that includes:
  - Brand intro (0.5-1s animated logo)
  - Caption style preset
  - Color grade / LUT
  - Audio template (music bed, VO track structure)
  - Brand outro with CTA
  - Watermark/logo overlay position
- How to apply this template to 25-35 videos per month efficiently
- Any DaVinci Resolve features specifically for template-based production?

Provide specific URLs, tutorials, scripts, and templates where available. Prioritize DaVinci Resolve Studio workflows over other tools.
