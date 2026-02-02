# 7A: Bioluminescent/Ethereal Effects -- Extracted Data

Source file: `docs/research/bb-content-production/results/7A.md`
Extraction date: 2026-02-01

---

## MIDJOURNEY V7 TECHNIQUES

### Subsurface Scattering / Inner Glow

- **Best prompt keywords:**
  - `subsurface scattering` [VERIFIED -- appears in multiple working prompts]
  - `lit from within` [VERIFIED -- appears in example prompts]
  - `soft clay texture` [CLAIMED -- stated in summary, not in an exact example prompt]
  - `subsurface illumination` [VERIFIED -- appears in crystal goddess prompt]
  - `glowing from within` [VERIFIED -- listed in keyword reference]
  - `inner glow` [VERIFIED -- listed in keyword reference and workflow prompt]
  - `warm inner light` [VERIFIED -- listed in keyword reference]
  - `radiant core` [VERIFIED -- listed in keyword reference]
  - `backlit` [VERIFIED -- listed in keyword reference]
  - `rim light` [VERIFIED -- listed in keyword reference]
  - `volumetric lighting` [VERIFIED -- listed in keyword reference and workflow prompt]
  - `octane render` [VERIFIED -- listed in keyword reference, appears in example prompts]
  - `ray tracing` / `raytracing` [VERIFIED -- listed in keyword reference, appears in example prompts]
  - `SSS lighting` [VERIFIED -- listed in keyword reference]
  - `wax-like texture` [VERIFIED -- appears in translucent clay prompt]

- **--stylize values that work:**
  - Range: **150-400** for SSS/glow work [CLAIMED -- stated as optimal range]
  - Sweet spot: **200-300** for translucent clay lit from within [CLAIMED -- stated as optimal parameter block]
  - Specific example value: `--s 200` (translucent clay figurine prompt) [VERIFIED -- exact prompt shown]
  - Specific example value: `--s 250` (material transition prompt) [VERIFIED -- exact prompt shown]
  - Specific example value: `--s 300` (workflow pipeline prompt) [VERIFIED -- exact prompt shown]
  - Specific example value: `--s 1000` (bioluminescent character prompt, described as "insane details" style) [VERIFIED -- exact prompt shown]
  - Below 150: "too literal an interpretation" [CLAIMED]
  - Above 500: "pushes toward abstract artistic flourishes that may overwhelm the subtle glow effect" [CLAIMED]
  - V7 range is 0-1000 [CLAIMED]
  - Legacy equivalent: `--s 20000` in earlier versions equals approximately `--s 500-750` in V7 combined with `ethereal atmosphere` descriptors [CLAIMED]

- **--chaos values that work:**
  - Range: **15-20** for translucent clay lit from within [CLAIMED -- stated in parameter block]
  - Broader useful range: **10-25** provides useful variation while maintaining material consistency [CLAIMED]

- **Other parameters:**
  - `--style raw` for organic glow rather than harsh neon [CLAIMED -- stated in summary]
  - `--q 2` (quality 2) included in optimal parameter block [VERIFIED -- shown in parameter block]
  - `--exp` parameter (0-100): Keep under 25 for prompt consistency. Higher values can enhance luminosity but may push toward overexposure [CLAIMED -- V7-specific parameter]
  - `--weird` parameter: **UNAVAILABLE in V7** -- avoid including it [CLAIMED]
  - `--ar 3:4` used in translucent clay prompt [VERIFIED]
  - `--ar 2:3` used in bioluminescent mushroom prompt [VERIFIED]
  - `--ar 9:16` used in bioluminescent character portrait [VERIFIED]
  - `--ar 1:1` used in workflow pipeline prompt [VERIFIED]
  - `--vt` used in crystal goddess prompt (older version parameter) [VERIFIED]
  - `--upbeta` used in simple glowing structure prompt (older version) [VERIFIED]

### "Translucent Clay Lit From Within"

- **Achievable:** YES [VERIFIED -- multiple prompt examples provided, described as achievable through "careful prompt engineering"]
- **Best approach:**
  1. Use `subsurface scattering` + `lit from within` + `soft clay texture` as core keyword combination [CLAIMED]
  2. Set `--stylize 200-350` with `--style raw` [CLAIMED]
  3. In V7, explicitly request `wax-like texture` or `soft skinned` because V7's natural skin rendering lost V6's beneficial "waxy quality" [CLAIMED -- important V6-to-V7 migration note]
  4. Add `translucent` + `warm amber internal glow` for color specificity [VERIFIED -- from example prompt]
  5. Combine with `hyperrealistic, 8K` for detail [VERIFIED -- from example prompt]
- **Example prompts (exact):** See COMPLETE EXAMPLE PROMPTS section below

### V7 vs V6 Differences

- **What changed:**
  - V7 simulates light transport with physical accuracy; V6 only approximated subsurface scattering [CLAIMED]
  - V7 understands how light bounces through skin, refracts through glass, creates soft shadows from diffused sources [CLAIMED]
  - V7 can distinguish between material types: brushed aluminum vs polished chrome, old leather vs new leather [CLAIMED]
  - V7 can differentiate matte clay surfaces from translucent wax-like materials given the right cues [CLAIMED]
  - Same prompt in V7 produces more realistic translucency without needing as many modifier terms [CLAIMED]
  - V6 produced a "waxy quality" in skin that users described -- this actually benefited the translucent clay look [CLAIMED]
  - V7's more natural skin rendering means you lose that waxy quality and may need to explicitly add `wax-like texture` or `soft skinned` to recover it [CLAIMED -- key migration insight]
  - `--weird` parameter no longer available in V7 [CLAIMED]
  - New `--exp` parameter (0-100) introduced in V7 for advanced tone mapping [CLAIMED]

---

## ANIMATION PRESERVATION

### SSS/Glow in Kling

- **Does it survive animation:** PARTIAL [VERIFIED -- described as having "best temporal stability" but with known issues]
- **Flickering/degradation issues:**
  - Uneven color transitions in gradient-heavy visuals [CLAIMED]
  - Occasional text artifacts [CLAIMED]
  - Some face deformation in stylized content [CLAIMED]
  - Temporal flickering is the "universal challenge" across all AI video platforms [CLAIMED]
- **Mitigation features:**
  - **Motion Brush feature** allows isolating glowing elements for targeted animation, preventing whole-scene instability [CLAIMED]
  - Kling explicitly supports terms: "glowing trees, bioluminescent flowers" and "neon glow" with realistic light interaction on surfaces [CLAIMED]
- **Versions mentioned:** Kling 2.1 Pro (excellent temporal stability), Kling 2.5 Turbo (fast with good stability) [CLAIMED]

### SSS/Glow in Other Tools

- **Runway Gen-3 Alpha:**
  - Official bioluminescent support -- prompting guide explicitly includes bioluminescent ocean example [VERIFIED -- example prompt provided]
  - "Advanced temporal modeling" solves previous frame jitter issues [CLAIMED]
  - Characters, lighting, perspective remain stable throughout clips [CLAIMED]
  - For videos over 10 seconds, inconsistencies in object shape, position, or appearance can emerge [CLAIMED]
  - Runway Gen 4 ranked 4th for flicker resistance, described as "good but adds slight camera movement" [CLAIMED]

- **Luma Ray3:**
  - World's first AI video generator with **native 16-bit High Dynamic Range output** [CLAIMED]
  - Critical for preserving bright, glowing elements without clipping or degradation [CLAIMED]
  - EXR export options: 10-bit, 12-bit, 16-bit [CLAIMED]
  - Enables professional color grading workflows [CLAIMED]
  - Prompt structure: `Main subject -> Action -> Details -> Scene -> Style -> Camera -> Reinforcer` [CLAIMED]
  - Include lighting cues like "sunset glow," "soft glow reflects in her eyes," or "luminescent mushrooms" [CLAIMED]
  - Luma Ray 2 ranked 5th (less stable for static scenes); Ray3 improves this [CLAIMED]
  - Ranked best for **glow fidelity** specifically due to native HDR [CLAIMED]

- **Veo 3:**
  - Ranked #1 overall for consistency (best flicker resistance) [CLAIMED]
  - No further detail provided

- **Higgsfield Sora 2 Enhancer:**
  - Mentioned as post-processing tool to reduce flickering [CLAIMED]
  - Not a standalone generator but a remediation tool [CLAIMED]

### Comparative Flicker Resistance (Ranked Best to Worst)

1. **Veo 3** -- Best overall consistency [CLAIMED]
2. **Kling 2.1 Pro** -- Excellent temporal stability, minimizes artifacts [CLAIMED]
3. **Kling 2.5 Turbo** -- Fast with good stability [CLAIMED]
4. **Runway Gen 4** -- Good but adds slight camera movement [CLAIMED]
5. **Luma Ray 2** -- Less stable for static scenes; Ray3 improves this [CLAIMED]

Note: Ray3 is described as best for glow fidelity (HDR) but is not included in the flicker ranking -- possibly because it was too new at time of ranking, or the ranking is from a different source. [UNCERTAINTY]

### Examples of Animated Bioluminescent AI Content

- **URLs:** NONE PROVIDED -- no specific URLs to animated examples are given in the source document.

### Mitigation Strategies for Glow Flickering

1. Simplify visual complexity -- reduce the number of detailed glowing elements [CLAIMED]
2. Include explicit consistency prompts: `"consistent appearance throughout the video"` and `"distinctive features remain unchanged"` [CLAIMED]
3. Add 1-second frame padding at video edges [CLAIMED]
4. Post-process with Higgsfield Sora 2 Enhancer [CLAIMED]
5. For video generation, add: `"The bioluminescent glow maintains consistent intensity throughout"` [CLAIMED]

---

## REFERENCE ART DIRECTION

### Clay + Luminescence + Cosmic Backgrounds

- **Examples found (URLs):** NONE PROVIDED
- **Prompt keywords for this combination:**
  - `deep space nebula` + warm character [CLAIMED]
  - `cosmic energy` [CLAIMED]
  - `stardust` [CLAIMED]
  - `teal and magenta color palette` [CLAIMED]
  - `cold blue nebula + warm orange/amber subject` [CLAIMED]
  - `deep blacks contrasting with warm glow` [CLAIMED]
  - `celestial black background` [CLAIMED]

### Foxfire Aesthetic

- **Definition:** Bioluminescent fungi on decaying wood producing soft bluish-green glow, historically called "fairy fire" [VERIFIED -- real phenomenon]
- **Chemical basis:** Luciferin/luciferase reactions [VERIFIED -- real biochemistry]
- **Art reference:** Marta Djourina's 2021 "Foxfire" series -- analogue photography with cultivated bioluminescent mushrooms, creating ethereal magenta-on-paper images [CLAIMED -- no URL provided]
- **Visual characteristics to target:**
  - Blue-green to yellow-green glow range [CLAIMED]
  - Warm wood base tones contrasting with cool bioluminescent accents [CLAIMED]
  - Soft, diffuse light (no sharp edges) [CLAIMED]
  - Atmospheric, not spotlit [CLAIMED]

### AI-Generated Examples

- **Pixar's *Soul* (2020):** Gold standard for volumetric ethereal characters [CLAIMED]
  - Soul characters are "conceptual beings of light" with prism-like response to lighting [CLAIMED]
  - Appear translucent with internal luminescence rather than hard surfaces with SSS [CLAIMED]
  - Custom **"Iridescence Driver" (IDriver)** shading node feeds into Double Henyey-Greenstein volume shader [CLAIMED]
  - IDriver determines albedo color using normals to look up into a color ramp, faking diffuse and specular lobes [CLAIMED]
  - "Soft normals" filtering removes smaller details outside the face for extra-soft appearance [CLAIMED]
  - Maintains readable expressions -- critical for children's content [CLAIMED]

- **Pixar's *Elemental* (2023):** Emotion-linked luminescence [CLAIMED]
  - Ember's fire becomes "more transparent and candle-like" when vulnerable [CLAIMED]
  - Fire shifts to purple when angry [CLAIMED]
  - Fire characteristics map to emotional controls ("zero to 10 sadness control") [CLAIMED]
  - Demonstrates translucency and glow mapped to narrative/emotional beats [CLAIMED]
  - Directly informs "glowing translucent (unconscious) to structured wood (conscious)" transition concept [CLAIMED]

### Traditionally Rendered Examples

- Marta Djourina's "Foxfire" series (2021) -- analogue photography, no URL [CLAIMED]
- No other traditionally rendered examples provided.

---

## PROMPT ENGINEERING KEYWORD LIST

### Translucent Clay Materials

| Keyword/Phrase | Source Context | Confidence |
|---|---|---|
| `claymation style` | keyword reference | CLAIMED |
| `clay texture` | keyword reference | CLAIMED |
| `plasticine` | keyword reference | CLAIMED |
| `3D clay` | keyword reference | CLAIMED |
| `stop motion aesthetic` | keyword reference | CLAIMED |
| `handmade feeling` | keyword reference | CLAIMED |
| `soft matte finish` | keyword reference | CLAIMED |
| `translucent` | keyword reference + example prompts | VERIFIED |
| `semi-transparent` | keyword reference | CLAIMED |
| `wax-like translucency` | keyword reference | CLAIMED |
| `wax-like texture` | example prompt + V6/V7 migration advice | VERIFIED |
| `jellyfish texture` | keyword reference | CLAIMED |
| `soft skinned` | keyword reference + V6/V7 migration advice | VERIFIED |
| `cute 3D clay character` | workflow prompt | VERIFIED |
| `soft translucent material` | workflow prompt | VERIFIED |
| `translucent clay figurine` | example prompt | VERIFIED |

### Subsurface Scattering

| Keyword/Phrase | Source Context | Confidence |
|---|---|---|
| `subsurface scattering` | keyword reference + example prompts | VERIFIED |
| `SSS lighting` | keyword reference | CLAIMED |
| `subsurface illumination` | keyword reference + crystal goddess prompt | VERIFIED |
| `glowing from within` | keyword reference | CLAIMED |
| `lit from within` | keyword reference + example prompt | VERIFIED |
| `inner glow` | keyword reference + workflow prompt | VERIFIED |
| `warm inner light` | keyword reference | CLAIMED |
| `radiant core` | keyword reference | CLAIMED |
| `backlit` | keyword reference | CLAIMED |
| `rim light` | keyword reference | CLAIMED |
| `volumetric lighting` | keyword reference + workflow prompt | VERIFIED |
| `octane render` | keyword reference + example prompts | VERIFIED |
| `ray tracing` | keyword reference | CLAIMED |
| `raytracing` | example prompt (bioluminescent character) | VERIFIED |
| `warm amber internal glow` | example prompt (translucent clay figurine) | VERIFIED |

### Bioluminescent Glow

| Keyword/Phrase | Source Context | Confidence |
|---|---|---|
| `bioluminescent` | keyword reference + summary + Kling/Runway prompts | VERIFIED |
| `bio-luminescent effect` | keyword reference | CLAIMED |
| `living light` | keyword reference | CLAIMED |
| `organic glow` | keyword reference | CLAIMED |
| `lightpulse` | keyword reference + bioluminescent mushroom prompt | VERIFIED |
| `glowing plankton` | keyword reference | CLAIMED |
| `firefly glow` | keyword reference | CLAIMED |
| `foxfire` | keyword reference + foxfire section | VERIFIED |
| `faerie fire` | keyword reference | CLAIMED |
| `glowing fungi` | keyword reference | CLAIMED |
| `luminescent mushrooms` | keyword reference + summary | VERIFIED |
| `ghost mushrooms` | keyword reference | CLAIMED |
| `floating spores` | keyword reference + bioluminescent mushroom prompt | VERIFIED |
| `neon glowing bioluminescent` | example prompt | VERIFIED |
| `fireflies` | example prompt (mushroom prompt) | VERIFIED |
| `bioluminescent flowers` | Kling prompt example | VERIFIED |
| `bioluminescent creatures` | Runway prompt example | VERIFIED |
| `gentle luminescence` | workflow prompt | VERIFIED |
| `bioluminescent accents` | workflow prompt | VERIFIED |

### Cosmic/Nebula Backgrounds with Warm Characters

| Keyword/Phrase | Source Context | Confidence |
|---|---|---|
| `deep space nebula` + warm character | keyword reference | CLAIMED |
| `cosmic energy` | keyword reference | CLAIMED |
| `stardust` | keyword reference | CLAIMED |
| `teal and magenta color palette` | keyword reference | CLAIMED |
| `cold blue nebula + warm orange/amber subject` | keyword reference | CLAIMED |
| `deep blacks contrasting with warm glow` | keyword reference | CLAIMED |
| `celestial black background` | keyword reference | CLAIMED |

Note: No complete example prompts provided specifically for cosmic/nebula backgrounds. All keywords are from the reference list only. [UNCERTAINTY]

### Unconscious-to-Conscious Transition (Glowing Translucent -> Structured Wood)

| Keyword/Phrase | Source Context | Confidence |
|---|---|---|
| `dissolving into` | keyword reference | CLAIMED |
| `transforming into` | keyword reference | CLAIMED |
| `morphing from... to...` | keyword reference | CLAIMED |
| `material gradient` | keyword reference + transition prompt | VERIFIED |
| `organic transformation` | keyword reference | CLAIMED |
| `solidifying from translucent to opaque` | keyword reference | CLAIMED |
| `ethereal to solid` | keyword reference | CLAIMED |
| `ghostly to physical` | keyword reference | CLAIMED |
| `translucent edges, solid core` | keyword reference | CLAIMED |
| `glowing translucent body gradually transitioning to warm wooden texture` | transition prompt | VERIFIED |
| `ethereal glow fading into organic grain` | transition prompt | VERIFIED |
| `subsurface scattering to solid opacity` | transition prompt | VERIFIED |

### Atmosphere/Quality Modifiers (from example prompts)

| Keyword/Phrase | Source Context | Confidence |
|---|---|---|
| `hyperrealistic` | translucent clay prompt | VERIFIED |
| `8K` | translucent clay prompt + mushroom prompt | VERIFIED |
| `hyper realistic` | mushroom prompt | VERIFIED |
| `unreal engine` | mushroom prompt + character prompt | VERIFIED |
| `photorealism` | mushroom prompt + character prompt | VERIFIED |
| `dramatic lighting` | mushroom prompt + crystal goddess prompt | VERIFIED |
| `cinematic` | crystal goddess prompt + Kling prompt | VERIFIED |
| `cinematic realism` | character prompt | VERIFIED |
| `cinematic quality` | Kling prompt | VERIFIED |
| `incredible detail` | mushroom prompt | VERIFIED |
| `insanely detailed` | character prompt | VERIFIED |
| `insane details` | character prompt | VERIFIED |
| `high dynamic range` / `hdr` | mushroom prompt | VERIFIED |
| `soft studio lighting` | translucent clay prompt | VERIFIED |
| `soft lighting` | transition prompt + workflow prompt | VERIFIED |
| `rule of thirds` | character prompt | VERIFIED |
| `golden ratio` | character prompt | VERIFIED |
| `asymmetric composition` | character prompt | VERIFIED |
| `depth of field` | character prompt | VERIFIED |
| `dreamlike atmosphere` | Kling prompt | VERIFIED |
| `ethereal atmosphere` | mentioned as V7 equivalent modifier | CLAIMED |
| `Pixar style` | workflow prompt | VERIFIED |
| `warm color palette` | workflow prompt | VERIFIED |
| `3d render` | mushroom prompt | VERIFIED |
| `anthropomorphic` | mushroom prompt | VERIFIED |
| `clean lines` | mushroom prompt | VERIFIED |
| `full body` | mushroom prompt + character prompt | VERIFIED |
| `geometric` | mushroom prompt | VERIFIED |
| `glowing` | mushroom prompt (multiple times) | VERIFIED |
| `glitters` | mushroom prompt | VERIFIED |
| `ghostly` | mushroom prompt | VERIFIED |
| `uplight` | mushroom prompt | VERIFIED |
| `purple mist` | mushroom prompt | VERIFIED |
| `beautiful forms` | mushroom prompt | VERIFIED |
| `spectacular` | mushroom prompt | VERIFIED |
| `hypermaximalist` | character prompt | VERIFIED |

---

## NEGATIVE PROMPTS

### Exact Negative Prompt String Provided:
```
--no plastic, neon harsh, synthetic glow, artificial lighting, cheap render,
glossy plastic, rubber texture, vinyl, stark shadows, overexposed, clinical,
sterile, lifeless, photorealistic, horror, scary, text, watermark
```

### Individual Negative Terms:

| Term | Purpose | Confidence |
|---|---|---|
| `plastic` | Prevent plastic material appearance | VERIFIED |
| `neon harsh` | Prevent harsh neon glow (vs organic glow) | VERIFIED |
| `synthetic glow` | Prevent artificial-looking luminescence | VERIFIED |
| `artificial lighting` | Prevent non-organic light quality | VERIFIED |
| `cheap render` | Prevent low-quality CG look | VERIFIED |
| `glossy plastic` | Prevent shiny plastic surface | VERIFIED |
| `rubber texture` | Prevent rubbery material | VERIFIED |
| `vinyl` | Prevent vinyl material | VERIFIED |
| `stark shadows` | Prevent harsh shadow contrast | VERIFIED |
| `overexposed` | Prevent blown-out glow | VERIFIED |
| `clinical` | Prevent sterile/medical appearance | VERIFIED |
| `sterile` | Prevent lifeless atmosphere | VERIFIED |
| `lifeless` | Prevent dead/inert appearance | VERIFIED |
| `photorealistic` | Prevent hyper-real (maintain stylized look) | VERIFIED |
| `horror` | Content safety for children's content | VERIFIED |
| `scary` | Content safety for children's content | VERIFIED |
| `text` | Prevent text artifacts | VERIFIED |
| `watermark` | Prevent watermark artifacts | VERIFIED |

### Workflow Prompt Negative (Condensed):
```
--no plastic, harsh neon, synthetic
```

---

## COMPLETE EXAMPLE PROMPTS

### Prompt 1: Translucent Clay Figurine (MidJourney V7)
```
translucent clay figurine lit from within, warm amber internal glow,
subsurface scattering, soft studio lighting, wax-like texture,
hyperrealistic, 8K --v 7 --ar 3:4 --s 200
```
Source: "Proven community prompts" section. Confidence: VERIFIED (presented as working prompt).

### Prompt 2: Bioluminescent Mushroom Character (PromptHero)
```
neon glowing bioluminescent soft skinned mushroom with luminous forest
backdrop, incredible detail, fireflies, floating spores, glow, flow,
beautiful forms, purple mist, 3d render, anthropomorphic, clean lines,
full body, transluscent, geometric, glowing, glitters, lightpulse, neon,
ghostly, highly detailed, hyper realistic, unreal engine, 8k, photorealism,
dramatic lighting, spectacular, dramatic, uplight, raytracing, high dynamic
range, hdr --ar 2:3
```
Source: "PromptHero verified" label. Confidence: CLAIMED (attributed to PromptHero, no URL). Note: No `--v` parameter specified. Note: Contains typo `transluscent` (should be `translucent`).

### Prompt 3: Bioluminescent Character Portrait (Multi-Prompt Weighted)
```
long-shot, full body portrait of [character] ::10 lucid weirdcore cybercore,
looking off in distance ::6 style | bioluminescent intense glowing biomechanical
rips emerging from skin, styled in insanely detailed intricate marginalia headdress,
gorgeous, wearing mask made from fibre-optics, bright neon lights shining, very
colorful, blue, green, purple, glowing ::6 background | glowing forest, vivid neon
wonderland dream, particles, blue, green, purple ::4 parameters | rule of thirds,
golden ratio, photorealism, raytraced shadows, depth of field, asymmetric composition,
hypermaximalist, insane details, octane render, photorealism, cinematic realism, unreal
engine, 8k ::7 --ar 9:16 --s 1000
```
Source: "Proven community prompts" section. Confidence: CLAIMED (no attribution/URL). Note: Uses multi-prompt weighting syntax (::N). Note: Very high --s 1000 value. Note: Labeled as "character with glowing skin emerging from within."

### Prompt 4: Crystal Goddess with SSS
```
a crystal goddess composed of webs, translucent, subsurface illumination,
subsurface scattering, cinematic, octane render, photorealistic, detail,
character creation, dramatic lighting --vt
```
Source: "Proven community prompts" section. Confidence: CLAIMED (no attribution). Note: Uses `--vt` (older MidJourney parameter, not V7).

### Prompt 5: Simple Glowing Structure (Legacy)
```
translucent structure light weight glowing --upbeta --s 20000 --q 2
```
Source: "Proven community prompts" section. Confidence: CLAIMED. Note: `--upbeta` and `--s 20000` are legacy parameters. In V7, equivalent results from `--s 500-750` + `ethereal atmosphere` [CLAIMED].

### Prompt 6: Kling AI Glowing Forest Animation
```
A weary adventurer enters a misty enchanted forest. Wide shot of massive
glowing trees, bioluminescent flowers lighting the path. The camera lowers
to ground level, following boots as fog curls around them. Consistent ethereal
glow throughout, dreamlike atmosphere, cinematic quality.
```
Source: "Recommended Kling prompt for glowing characters." Confidence: CLAIMED (not attributed to official Kling docs).

### Prompt 7: Runway Gen-3 Bioluminescent Ocean (Official)
```
A glowing ocean at night time with bioluminescent creatures under water.
The camera starts with a macro close-up of a glowing jellyfish and then
expands to reveal the entire ocean lit up with various glowing colors
under a starry sky.
```
Source: "Runway's prompting guide explicitly includes this example." Confidence: CLAIMED (attributed to official Runway guide but no URL).

### Prompt 8: Material Transition (Translucent to Wood)
```
[character] with glowing translucent body gradually transitioning to warm
wooden texture, material gradient, ethereal glow fading into organic grain,
subsurface scattering to solid opacity, soft lighting --v 7 --s 250
```
Source: "Example transition prompt" in keyword reference section. Confidence: CLAIMED (presented as example, not tested/verified).

### Prompt 9: Workflow Pipeline Prompt (Children's Content)
```
[character description], cute 3D clay character, soft translucent material,
subsurface scattering, inner glow, bioluminescent accents, warm color palette,
soft lighting, Pixar style, volumetric lighting, gentle luminescence
--ar 1:1 --s 300 --no plastic, harsh neon, synthetic
```
Source: "Recommended workflow" section. Confidence: CLAIMED (presented as recommended approach, not verified output).

### Video Consistency Prompt Addition
```
"The bioluminescent glow maintains consistent intensity throughout"
```
Source: Workflow Step 3. Confidence: CLAIMED. Usage: Append to video generation prompts.

---

## KEY TECHNIQUES (Quick Reference)

1. **Core SSS formula (MJ V7):** `subsurface scattering` + `lit from within` + `soft clay texture` + `--s 200-350` + `--style raw`
2. **V6->V7 migration:** Add `wax-like texture` or `soft skinned` to recover V6's beneficial waxy quality
3. **Optimal V7 parameters:** `--s 200-300 --chaos 15-20 --q 2` for translucent clay
4. **--exp parameter:** Keep under 25 to avoid overexposure of glow
5. **Animation platform selection:** Luma Ray3 for glow fidelity (HDR), Kling 2.1 Pro for temporal stability, Runway Gen-3 for bioluminescent nature
6. **Flicker mitigation:** Simplify scene, add consistency language, 1-second frame padding, post-process with Higgsfield
7. **Negative prompt essentials:** `--no plastic, neon harsh, synthetic glow, artificial lighting, cheap render`
8. **Material transitions:** Generate keyframe images at start/end states, use AI video interpolation between them
9. **Emotion-linked glow:** Follow Pixar Elemental's model -- map translucency/color to emotional states
10. **Foxfire visual targets:** Blue-green to yellow-green glow, warm wood base, soft diffuse light, atmospheric not spotlit

---

## CONTRADICTIONS & UNCERTAINTIES

### Contradiction 1: --stylize Range Inconsistency
- Summary paragraph states `--stylize values between 200-350` [line 3]
- Parameter block states `--s 200-300` [line 17]
- Broader discussion states `150-400 range` for SSS/glow work [line 20]
- These overlap but are not identical. The broadest range (150-400) is probably the safe envelope, with 200-300 as the sweet spot.
- **Status: MINOR CONTRADICTION** -- likely just different levels of specificity.

### Contradiction 2: Ray3 vs Ranking Omission
- Ray3 is described as best for glow fidelity due to native 16-bit HDR [line 107-109]
- But the flicker resistance ranking lists "Luma Ray 2" at position 5 and does not include Ray3 [line 124]
- Either Ray3 was not yet benchmarked at ranking time, or glow fidelity and flicker resistance are treated as separate metrics.
- **Status: UNCERTAINTY** -- unclear if Ray3 would rank higher than Ray2 for flicker.

### Contradiction 3: "photorealistic" as Both Positive and Negative
- `photorealistic` and `photorealism` appear in multiple positive example prompts (mushroom, character, crystal goddess) [lines 43, 57, 65]
- `photorealistic` also appears in the negative prompt list [line 177]
- This is context-dependent: for the children's clay aesthetic specifically, photorealism is undesired. For general bioluminescent effects, it is desired.
- **Status: CONTEXT-DEPENDENT** -- not a true contradiction, but a trap for copy-paste usage.

### Uncertainty 1: No URLs or Visual Examples
- No URLs to any generated images, videos, or reference art are provided anywhere in the document.
- PromptHero attribution given but no link.
- Runway "official guide" referenced but no link.
- Marta Djourina's "Foxfire" series mentioned but no link.
- Pixar references are to publicly known films but no specific frame references.
- **Status: UNCERTAINTY** -- all claims about prompt results are unverifiable from this document alone.

### Uncertainty 2: V7 Parameter Specifics
- Claims about `--exp` parameter (0-100) and `--weird` being unavailable in V7 are stated without source attribution.
- V7's stylize range of 0-1000 is stated without source.
- **Status: CLAIMED** -- need to verify against official MidJourney V7 documentation.

### Uncertainty 3: Veo 3 Ranking
- Veo 3 is ranked #1 for consistency but receives zero further discussion.
- No prompts, no workflow advice, no limitations mentioned.
- **Status: CLAIMED** -- insufficient detail to act on.

### Uncertainty 4: Legacy Prompt Compatibility
- Prompts 2, 3, 4, and 5 use older MidJourney parameters (`--vt`, `--upbeta`, `--s 20000`) or lack version flags entirely.
- Only Prompts 1, 8, and 9 explicitly use `--v 7`.
- It is unclear whether the older prompts have been tested/verified on V7.
- **Status: UNCERTAINTY** -- legacy prompts may need adaptation for V7.

### Uncertainty 5: Kling Prompt Source
- The Kling prompt (Prompt 6) is presented as "recommended" but not attributed to official Kling documentation.
- **Status: CLAIMED** -- may be community-sourced or author-composed.

---

## SOURCE URLS

**No URLs are provided anywhere in the source document.**

Referenced but not linked:
- PromptHero (prompt sharing platform) -- no specific page
- Runway Gen-3 Alpha prompting guide -- no URL
- Marta Djourina's "Foxfire" series (2021) -- no URL
- Pixar's *Soul* (2020) -- film, no specific technical resource linked
- Pixar's *Elemental* (2023) -- film, no specific technical resource linked
- Higgsfield Sora 2 Enhancer -- no URL
- Luma Ray3 documentation -- no URL
- Kling AI documentation -- no URL

---

## LUMA RAY3 PROMPT STRUCTURE (Extracted)

Official structure pattern:
```
Main subject -> Action -> Details -> Scene -> Style -> Camera -> Reinforcer
```

Recommended lighting cues to include:
- `sunset glow`
- `soft glow reflects in her eyes`
- `luminescent mushrooms`

---

## PIXAR TECHNICAL DETAILS (For Reference/Inspiration Only)

### Soul (2020) Custom Shading Pipeline:
- **Iridescence Driver (IDriver):** Custom shading node
- **Double Henyey-Greenstein volume shader:** Receives IDriver output
- **Albedo method:** Normals look up into color ramp, faking diffuse + specular lobes
- **"Soft normals" filtering:** Removes smaller details outside the face
- **Result:** Extra-soft appearance while maintaining readable facial expressions

### Elemental (2023) Emotion Mapping:
- Transparency mapped to vulnerability (candle-like)
- Color shift to purple mapped to anger
- "Zero to 10 sadness control" for fire characteristics
- **Applicable insight:** Map translucency/glow intensity to narrative/emotional states in Baby Brains content

---

## WORKFLOW SUMMARY (4-Step Pipeline)

| Step | Action | Tool | Notes |
|---|---|---|---|
| 1 | Generate source images | MidJourney V7 | Use SSS + inner glow prompts, --s 300, --no negatives |
| 2 | Test animation | Luma Ray3 (glow fidelity) OR Kling 2.1 Pro (stability) OR Runway Gen-3 (bioluminescent nature) | Platform-dependent on content type |
| 3 | Add consistency prompts | All platforms | "bioluminescent glow maintains consistent intensity throughout" |
| 4 | Post-process if needed | Higgsfield Sora 2 Enhancer | For flickering remediation, frame-padding |

### Material Transition Technique (Unconscious -> Conscious):
1. Generate keyframe images showing material gradient (glowing translucent -> structured wood)
2. Use AI video interpolation for smooth morphing between states
3. Runway and Luma both handle material transitions well with clear start/end reference frames [CLAIMED]
