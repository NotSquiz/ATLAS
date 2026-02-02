# 8A: MidJourney V7 Character Consistency & Video Prompting -- Extracted Data

---

## --cref (Character Reference)

### Current V7 Behavior

- **--cref NO LONGER WORKS in V7.** [VERIFIED -- official docs cited]
- MidJourney V7 replaced --cref with Omni Reference (--oref) when V7 launched April 3, 2025 and became default June 17, 2025. [VERIFIED -- dates from official updates]
- Official documentation states: "Character Reference is not compatible with version 7, please use Omni Reference instead." [VERIFIED -- direct quote from official docs]
- --cref still works in V6.1 for multi-character workarounds (see Failure Modes). [VERIFIED -- described in workaround section]

### Works for Video: NO

- --cref does NOT work with video generation. [VERIFIED -- official docs]
- Neither --cref, --oref, nor --sref work with video generation. [VERIFIED -- official docs explicitly state "not compatible with video generations"]

### Recommended --cw Values

- N/A for V7. The --cw parameter belonged to the V6 --cref system.
- V6 --cref had --cw range 0-100, default 100. [VERIFIED -- comparison table in source]

### Failure Modes & Workarounds

- V6 --cref sometimes placed heads backward when camera POV was behind a character. [VERIFIED -- described as a known V6 issue]
- V6 --cref worked best with MJ-generated content; external/real photos were less reliable. [VERIFIED -- stated as V6 limitation]

### Consistency Across 20+ Generations

- Not applicable -- --cref is deprecated in V7. Use --oref instead (see Omni-Reference section).

---

## --sref (Style Reference)

### Current Behavior & Best Practices

- V7 introduced a **six-version style reference system (--sv)**. [VERIFIED -- detailed table from source]
- Sref codes only work with --sv 4 or --sv 6. Uploading your own images unlocks all six versions. [VERIFIED -- stated as critical note]

#### --sv Version Table

| Version | Behavior | Best Use Case |
|---------|----------|---------------|
| --sv 1 | Reliable enhancer, adds warmth, boosts contrast | Client work, consistent results |
| --sv 2 | Creative wild card, unpredictable transformations | Experimentation |
| --sv 3 | Artistic balancer, thoughtful modifications | Art theory-based enhancement |
| --sv 4 | Professional standard (pre-June 16, 2025 model) | Legacy sref codes |
| --sv 5 | Vintage specialist, warm tones, nostalgic film look | Retro branding |
| --sv 6 | **Default** -- Safe, balanced, contemporary | General use |

### Optimal --sw Values

- **--sw 100** (default): Balanced transfer. [VERIFIED]
- **--sw 200-400**: Recommended starting range for brand aesthetics. [CLAIMED -- attributed to "experienced users"]
- **--sw 500-700**: Very strong style influence. [CLAIMED]
- **--sw 800-1000**: Closely mimics the reference but differences can be subtle. Always test first. [CLAIMED]
- **--sw 180**: Recommended starting point specifically for color palette swatches. [CLAIMED -- community recommendation]

#### Permutation Testing Template (verbatim prompt):

```
[prompt] --sref [URL] --sw {0, 200, 400, 600, 800, 1000} --v 7
```

### Color Palette Swatch as --sref

- **Works, but with limitations.** [VERIFIED]
- Create a 600-1200px wide image with 4-6 horizontal, solid-color swatches. [CLAIMED -- community technique]
- MidJourney interprets colors contextually based on scene lighting and surface materials rather than hard-locking exact HEX values. [VERIFIED -- behavioral observation]
- Rectilinear swatch designs may unintentionally influence architectural elements in generated images. [CLAIMED -- community observation]
- Mitigation: use "flat color, minimal gradients" in your prompt. [CLAIMED]
- Start with **--sw 180** for palettes. [CLAIMED]

### Maintaining Lighting/Glow Effects

- Lighting and glow effects transfer "moderately well" through --sref. [CLAIMED -- subjective assessment]
- Community-recommended sref code for ethereal glow: **--sref 1007775450** -- creates minimalist style with glowing edges and dreamy atmosphere. [CLAIMED -- community recommendation]
- Higher --sw values (300+) strengthen lighting effect preservation. [CLAIMED]

---

## Omni-Reference (--oref)

### What It Is

- Replacement for --cref in V7. [VERIFIED -- official]
- Launched: May 1, 2025 (from updates.midjourney.com). Became available when V7 launched April 3, 2025. [VERIFIED -- official update dates]
- Handles characters, objects, vehicles, creatures -- broader scope than --cref which was characters only. [VERIFIED -- official docs]
- External images (including real photographs) now work equally well as MidJourney-generated images. [VERIFIED -- stated as improvement over V6]
- Costs **2x more GPU time** than standard generation. [VERIFIED -- from comparison table]

### How It Differs from --cref/--sref

| Parameter | V6 --cref | V7 --oref |
|-----------|-----------|-----------|
| Weight control | --cw 0-100 | --ow 0-1000 |
| Multiple images | Yes | **Only ONE image allowed** |
| Default weight | 100 | 100 |
| GPU cost | Standard | **2x more GPU time** |
| Scope | Characters only | Characters, objects, vehicles, creatures |

- Camera angle handling is much better -- V7 understands spatial relationships, no more backward-head issue. [VERIFIED]

### Recommended --ow (Omni Weight) Values

- **--ow 25-50**: Style transfers like photo-to-anime; preserves core features while allowing significant stylistic change. [CLAIMED -- from experienced users]
- **--ow 100** (default): Balanced starting point for most use cases. [VERIFIED]
- **--ow 100-250**: Optimal range according to testing by MidJourneyV6.org. [CLAIMED -- attributed to MidJourneyV6.org]
- **--ow 300-400**: Strong fidelity for preserving facial features and clothing details. [CLAIMED]
- **--ow 400-500**: TitanXT testing found this range often produced better similarity results. [CLAIMED -- attributed to TitanXT]

### Official Warning on --ow

"If you aren't using extremely high --s and --exp values, you probably should not go over values like --ow 400 or things may actually be worse." [VERIFIED -- direct quote from MidJourney official guidance]

### Better for Style + Character Simultaneously?

- --oref handles character/object reference. --sref handles style reference. They are separate systems and can be combined. [VERIFIED]
- For 20+ generation consistency: combine --oref (100-250 weight) with --sref for style, always referencing original base image. [CLAIMED -- community best practice]

### --oref Incompatibilities

NOT compatible with: [VERIFIED -- official docs]
- Fast Mode
- Draft Mode
- Conversational Mode
- --q 4
- Vary Region
- Pan
- Zoom Out
- Inpainting/outpainting (which still uses V6.1)

### Multiple Characters Workaround

Since V7 --oref only allows ONE reference image: [VERIFIED -- official limitation]
1. Create both characters in a single reference image and describe both in your prompt. [CLAIMED -- community workaround]
2. Alternative: Create first character with --oref, send to Editor, switch to V6.1, and use --cref for the second character. [CLAIMED -- community workaround]

---

## VIDEO GENERATION

### Best Prompt Structure for Video

**Structure:** Subject + Active Action Verb + Camera Movement + Environmental Details [CLAIMED -- from source guidance]

**Two-part structure (verbatim prompt example):**

```
Camera: slow push-in, steady. Subject: hair and fabric move gently in the wind; subtle eye movement; natural --motion high --raw --video 1
```

**Key rules:**
- Remove image-focused keywords like "8K," "HDR," or "f/1.8" -- these are ineffective for video. [CLAIMED]
- Use natural descriptions. [CLAIMED]

### Maximum Useful Length

- Not explicitly stated. Source recommends concise prompts focused on Subject + Action + Camera + Environment. [NO DATA -- not directly addressed]

### Motion/Camera Movement Specification

**Parameters:**
- `--motion low`: Subtle/calm motion for ambient scenes. [VERIFIED -- from parameter list]
- `--motion high`: Dynamic motion with both subject and camera movement. [VERIFIED]
- `--raw`: Stricter prompt adherence. [VERIFIED]
- `--loop`: Makes end frame match start frame. [VERIFIED]
- `--end <URL>`: Specifies ending frame image. [VERIFIED]
- `--video 1`: Enables video generation (used in example prompt). [VERIFIED -- from example]

### Video Specifications

- V1 Video Model launched June 19, 2025. [VERIFIED -- from official updates]
- Creates 5-second clips at 24fps. [VERIFIED]
- Extendable to **21 seconds maximum** via 4-second extensions. [VERIFIED]

### Quality Degradation by Segment

| Segment | Quality |
|---------|---------|
| 0-5 seconds | Best quality |
| 5-9 seconds | Good quality |
| 13-17 seconds | Noticeable degradation |
| 17-21 seconds | Lowest quality |

**Recommendation:** Plan critical content for the first 5 seconds and limit extensions to two for quality consistency. [CLAIMED -- source recommendation]

**Note:** Gap between 9-13 seconds is not described in source. This may be an omission or it may fall between "Good" and "Noticeable degradation." [UNCERTAINTY]

### Success Rate (video vs image)

**From GamsGo testing:** [CLAIMED -- attributed to GamsGo]

| Content Type | Success Rate |
|-------------|-------------|
| Landscapes & still life | ~80-90% |
| Portraits | ~66.7% (failures from facial distortion, drifting features) |
| Human motion | ~50-60% |
| Abstract/artistic | ~70-80% |

### Known Limitations & Bugs

- Motion stutters. [CLAIMED -- community reports]
- Subject warping with dramatic movements. [CLAIMED]
- Camera drift on "static camera" requests. [CLAIMED]
- Text rendering often illegible. [CLAIMED]
- **No reference features work with video** (--cref, --oref, --sref all incompatible). [VERIFIED -- official]

### Character-Consistent Video Workaround

1. Generate your still image with --oref first. [CLAIMED -- community workflow]
2. Upscale (U1-U4). [CLAIMED]
3. Use "Animate (High motion)" or "Animate (Low motion)" buttons. [CLAIMED]
4. This animates that specific consistent character image. [CLAIMED]

---

## SEED DISCIPLINE

### Same --seed for Consistency

- Seeds remain useful for: [VERIFIED -- official docs]
  - A/B testing prompt phrasing while keeping starting noise constant
  - Creating thematically cohesive image sets
  - Controlled experimentation with parameter differences

### Still Relevant in V7?

- **Limited relevance.** [VERIFIED -- official]
- Official MidJourney documentation states: "shouldn't be relied on for the same results over different prompting sessions" and "can't capture or bookmark a specific style, character, or appearance across different prompts." [VERIFIED -- direct quotes from official docs]
- Seeds are NOT recommended for: [VERIFIED -- official guidance]
  - True character consistency (use --oref instead)
  - Style preservation (use --sref instead)
  - Multi-session projects
- Official guidance: "For consistency in your images, we recommend style references, omni references, and personalization." [VERIFIED -- direct quote]

---

## COMMUNITY BEST PRACTICES

### Power User Workflows for Consistent Characters (20+ Generations)

**Core principle:** Always reference your original base image rather than chaining references (Image A -> Image B -> Image C degrades consistency). [CLAIMED -- community best practice, but strongly supported by multiple sources]

**Step 1 -- Create excellent base character (verbatim prompt):**

```
A stylized 3D character, [detailed description], Pixar style, Cinema 4D render, clean white background, full body, front view --ar 2:3 --v 7
```

**Tips for base character:**
- Use simple/solid colored clothing (patterns are hard to replicate). [CLAIMED]
- Clean backgrounds. [CLAIMED]
- Portrait orientation (2:3 or 4:5). [CLAIMED]

**Step 2 -- Generate character reference sheet (verbatim prompt):**

```
character reference sheet, [character description], multiple views, front view, side view, three-quarter view, various expressions, clean white background, professional --oref [URL] --ow 100 --v 7
```

**Step 3 -- Apply across generations (verbatim prompt):**

```
3D stylized character, [ACTION/SCENE], [key character traits: hair color, eye color, outfit colors], Pixar render style, soft lighting --oref [original_base_URL] --ow 150 --sref [3D_style_reference_URL] --sw 100 --seed [consistent_seed] --v 7 --ar 16:9
```

**Parameters used in Step 3:**
- --oref with original base URL (not chained)
- --ow 150
- --sref with 3D style reference URL
- --sw 100
- --seed with consistent value
- --v 7
- --ar 16:9

### Stylized 3D / Clay Aesthetic Techniques

**Prompt terms and their effects:**
- "Claymation" -- whimsical, surreal with vivid colors. [CLAIMED]
- "3D clay animation" -- stop-motion look with tactile textures. [CLAIMED]
- "Clay render" -- clean 3D with clay-like materials. [CLAIMED]

**Clay world example (verbatim prompt):**

```
miniature, Super cute clay world, isometric view of garden, flowers, cute clay freeze frame animation, tilt shift, excellent lighting, volume, 3D, super detail --chaos 0 --style raw
```

**Parameters in clay example:**
- --chaos 0
- --style raw

### Specific MJ Techniques

**For character consistency failures:**
- Use higher quality reference images with clear, unobstructed faces. [CLAIMED]
- Always reference the original base image rather than chaining. [CLAIMED]
- Try rerolling and use the same seed for related generations. [CLAIMED]

**When character ignores text prompt (too similar to reference):**
- Lower --ow to 50-100. This gives the text prompt more influence. [CLAIMED]

**Fine detail preservation:**
- Intricate details like specific freckles, logos, and tattoos won't reproduce accurately. [VERIFIED -- known limitation]
- Reinforce key details in the text prompt rather than relying solely on the reference. [CLAIMED]

---

## COMPLETE PROMPT EXAMPLES

### Example 1: Base Character Creation

```
A stylized 3D character, [detailed description], Pixar style, Cinema 4D render, clean white background, full body, front view --ar 2:3 --v 7
```

### Example 2: Character Reference Sheet

```
character reference sheet, [character description], multiple views, front view, side view, three-quarter view, various expressions, clean white background, professional --oref [URL] --ow 100 --v 7
```

### Example 3: Scene Generation with Character Consistency

```
3D stylized character, [ACTION/SCENE], [key character traits: hair color, eye color, outfit colors], Pixar render style, soft lighting --oref [original_base_URL] --ow 150 --sref [3D_style_reference_URL] --sw 100 --seed [consistent_seed] --v 7 --ar 16:9
```

### Example 4: Style Reference Permutation Testing

```
[prompt] --sref [URL] --sw {0, 200, 400, 600, 800, 1000} --v 7
```

### Example 5: Clay World Scene

```
miniature, Super cute clay world, isometric view of garden, flowers, cute clay freeze frame animation, tilt shift, excellent lighting, volume, 3D, super detail --chaos 0 --style raw
```

### Example 6: Video Prompt Structure

```
Camera: slow push-in, steady. Subject: hair and fabric move gently in the wind; subtle eye movement; natural --motion high --raw --video 1
```

---

## KEY TECHNIQUES (Quick Reference)

| Technique | Implementation | Confidence |
|-----------|---------------|------------|
| Character consistency (V7) | --oref with original base image, --ow 100-250 | VERIFIED (official + community) |
| Style consistency | --sref with --sw 200-400 for brand work | CLAIMED (community) |
| Combined character + style | --oref [char_URL] --ow 150 + --sref [style_URL] --sw 100 | CLAIMED (community) |
| Avoid reference chaining | Always use original base image, never chain A->B->C | CLAIMED (strongly supported) |
| Character-consistent video | Generate still with --oref, upscale, then Animate button | CLAIMED (workaround) |
| Clay/3D aesthetic | "Claymation" / "3D clay animation" / "Clay render" + --style raw | CLAIMED |
| Color palette as sref | 600-1200px swatch image, --sw 180, add "flat color, minimal gradients" | CLAIMED |
| Ethereal glow sref code | --sref 1007775450 with --sw 300+ | CLAIMED (community) |
| Seed for A/B testing | Same --seed across prompt variants | VERIFIED (official) |
| Video quality planning | Critical content in first 5 seconds, max 2 extensions | CLAIMED |
| Multiple characters | Both in one ref image, OR use Editor + V6.1 --cref for second | CLAIMED |
| Lower ref influence | Reduce --ow to 50-100 for more text prompt influence | CLAIMED |

---

## CONTRADICTIONS & UNCERTAINTIES

### 1. --oref Launch Date Discrepancy
- Source states V7 "launched April 3, 2025" with --oref replacing --cref.
- Separate entry states Omni Reference was announced at updates.midjourney.com on "May 1, 2025."
- **Possible explanation:** V7 launched in April but --oref may have been added/announced separately in May. Or V7 alpha vs default dates differ. [UNCERTAINTY]

### 2. Video Quality Gap (9-13 seconds)
- The quality degradation table jumps from "5-9 seconds: Good quality" to "13-17 seconds: Noticeable degradation."
- The 9-13 second range is not characterized. [UNCERTAINTY -- likely an oversight in source or original research]

### 3. --ow Optimal Range Disagreement
- MidJourneyV6.org recommends --ow 100-250.
- TitanXT testing found --ow 400-500 often produced better similarity.
- Official MJ warns against going over --ow 400 without high --s and --exp values.
- **These are not strictly contradictory** (different use cases, different quality criteria) but could confuse users. [NOTED -- context-dependent]

### 4. --video 1 Parameter
- The video prompt example includes `--video 1` as a parameter, but the official parameters section only lists `--motion`, `--raw`, `--loop`, and `--end`.
- It is unclear whether `--video 1` is an actual parameter or shorthand. [UNCERTAINTY]

### 5. "Animate" Buttons vs Text-to-Video
- The workaround for character-consistent video uses "Animate (High motion)" / "Animate (Low motion)" buttons on an upscaled image.
- It is not explicitly stated whether this produces the same quality as text-to-video or is a different pipeline. [UNCERTAINTY]

### 6. --style raw vs --raw
- The clay example uses `--style raw` while the video example uses `--raw`. These may or may not be equivalent in V7. [UNCERTAINTY -- not clarified in source]

### 7. Sref Code Compatibility
- Source states sref codes only work with --sv 4 or --sv 6. But the ethereal glow code (--sref 1007775450) is recommended without specifying which --sv to use. [UNCERTAINTY -- assumed --sv 4 or 6 but not stated]

---

## ALL PARAMETER VALUES MENTIONED

| Parameter | Values Mentioned | Context |
|-----------|-----------------|---------|
| --oref | [URL] | Single image URL for omni reference |
| --ow | 25-50, 100 (default), 100-250, 300-400, 400-500 | Omni weight |
| --sref | [URL] or code (e.g., 1007775450) | Style reference |
| --sw | 100 (default), 180, 200-400, 500-700, 800-1000 | Style weight |
| --sv | 1, 2, 3, 4, 5, 6 (default) | Style version |
| --cw | 0-100, default 100 | Character weight (V6 only) |
| --cref | [URL] | Character reference (V6 only, deprecated in V7) |
| --v | 7 | Model version |
| --ar | 2:3, 4:5, 16:9 | Aspect ratio |
| --seed | [number] | Seed for reproducibility |
| --motion | low, high | Video motion level |
| --raw | (no value) | Stricter prompt adherence |
| --loop | (no value) | Video loop (end matches start) |
| --end | [URL] | Video ending frame |
| --chaos | 0 | Variation amount |
| --style | raw | Style mode |
| --s | (high values mentioned but no specific number) | Stylize |
| --exp | (mentioned but no specific value) | Experimental |
| --q | 4 (mentioned as incompatible with --oref) | Quality |
| --video | 1 (from example, unconfirmed parameter) | Video enable |

---

## SOURCE URLS

| Source | URL | Date |
|--------|-----|------|
| MidJourney Official - Omni Reference | docs.midjourney.com/hc/en-us/articles/36285124473997-Omni-Reference | Current |
| MidJourney Official - Character Reference | docs.midjourney.com/hc/en-us/articles/32162917505293-Character-Reference | Current |
| MidJourney Official - Style Reference | docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference | Current |
| MidJourney Official - Video | docs.midjourney.com/hc/en-us/articles/37460773864589-Video | Current |
| MidJourney Official - Seeds | docs.midjourney.com/hc/en-us/articles/32604356340877-Seeds | Current |
| MidJourney Updates - Omni Reference Launch | updates.midjourney.com/omni-reference-oref/ | May 1, 2025 |
| MidJourney Updates - V1 Video Model | updates.midjourney.com/introducing-our-v1-video-model/ | June 19, 2025 |
| Geeky Curiosity - Style Reference Testing | geekycuriosity.substack.com | August 8, 2025 |
| TitanXT - Omni Reference Testing | titanxt.io/post/testing-midjourney-v7s-new-omni-reference-feature | May 2025 |
| PromptsRef - Camera Prompts Guide | promptsref.com | November 27, 2025 |
| Tom's Guide - Character Consistency | tomsguide.com | 2025 |
| GamsGo - Video Success Rate Testing | (attributed in text, no URL provided) | Not dated |
| MidJourneyV6.org - --ow Testing | (attributed in text, no URL provided) | Not dated |
