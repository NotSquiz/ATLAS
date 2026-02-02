# Prompt PA: Hailuo Max Burst Production Pipeline

## Context
I'm producing stylized 3D / clay-aesthetic short-form social content for a parenting education brand. I plan to subscribe to Hailuo Max ($199.99/month, true unlimited Relax Mode for Hailuo 01 & 02 + 20,000 priority credits) for ONE intensive month to batch-produce 60-90 videos (3 months of content). Then cancel.

My image generation will come from MidJourney Standard ($30/month) and possibly Kling IMAGE 3.0 (which has a new Image Series Mode for storyboard generation with unified style). Videos are 7-60 seconds across multiple content tiers.

## Research Required

### 1. Hailuo Max Plan Real-World Experience
- Find REAL users who have used Hailuo Max ($199.99) or the previous Unlimited plan for high-volume production
- Search Reddit (r/AIVideo, r/aivideo), YouTube, production blogs, X/Twitter
- What was their actual daily throughput? How many generations per day in Relax Mode?
- Did they hit any throttling, rate limits, or quality degradation during sustained heavy use?
- Were there any account issues, unexpected charges, or feature limitations not advertised?
- What's the actual Relax Mode wait time under sustained load? (reports suggest ~30 seconds per task, but is this consistent?)

### 2. Hailuo 01 vs 02 for Stylized/Clay Content
- Hailuo 01 has a "Live" variant specifically designed for animating artwork (drawings, sketches, cartoons, comics). How good is it for clay-style 3D characters?
- Hailuo 02 focuses on cinematic realism at 1080p. Does it handle stylized content well or does it push toward photorealism?
- Hailuo 2.3 reportedly adds anime/illustration/game-CG support but some testing found it regressed vs 02 for stylized content. What's the current consensus?
- For each model variant: find example outputs of stylized 3D / clay / Pixar-style content. How do they compare?
- Which model (01 Live, 02, or 2.3) should I use for clay-aesthetic baby characters?

### 3. Batch Queuing Strategy for Burst Month
- Queue limits: 5 sequential tasks, 2 parallel renders. How do experienced users work within these limits?
- Is there an API or automation option to queue generations without manual clicking? (n8n, Make.com, API access?)
- What's the optimal daily schedule for maximum throughput? (e.g., queue before sleep, work in batches of X)
- How do users organize and track hundreds of generations? File naming conventions, folder structures, spreadsheets?
- Do priority credits (20,000) generate faster than Relax Mode? What's the actual speed difference?
- Strategy: Use priority credits for the most important/complex scenes, Relax Mode for variations and re-rolls?

### 4. Image-to-Video Pipeline with Hailuo
- Exact step-by-step: How do you take a MidJourney/Kling IMAGE output and feed it to Hailuo for animation?
- Does Hailuo accept reference images? How does its "Subject Reference" system work in practice?
- What image resolution/format works best as input?
- What prompt structure produces the best results for animating a still image?
- How much does the animated output deviate from the input image? (character consistency, color shift, detail loss)
- Can you specify camera movement, character action, and scene progression in the prompt?

### 5. Multi-Scene Stitching for Longer Videos
- Hailuo generates 6-10 second clips. To make a 30-60 second video, you need 3-10 clips stitched together.
- How do experienced creators ensure visual continuity between clips?
- What's the best approach to transitions between clips? (cut, dissolve, narrative continuity)
- Does Hailuo have any built-in features for scene continuation or clip extension?
- How do people handle the "seam" where one clip ends and another begins? (frame matching, overlap technique)

### 6. Asset Management During Burst Production
- When producing 60-90 videos in one month, each requiring 3-10 clips + re-rolls, you could have 500-2000+ raw files
- What file organization systems do high-volume creators use?
- Any tools for batch renaming, tagging, or cataloguing AI-generated video clips?
- How do people track which clips go with which final video?
- DaVinci Resolve bins and smart bins -- any AI-video-specific workflows?

### 7. Cancellation & Data Retention
- After cancelling Hailuo Max, do you retain access to previously generated content?
- Is there a download-all-before-cancelling requirement?
- Any reports of issues accessing or downloading content after subscription ends?
- Do credits expire immediately on cancellation or at end of billing period?

Provide specific URLs, usernames, and dates for all sources. Include screenshots or examples where available.
