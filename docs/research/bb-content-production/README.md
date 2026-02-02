# Baby Brains Content Production: Research Prompt Suite

## Location
All prompts saved in: `docs/research/bb-content-production/`

## Execution Order

### Wave 1 — Run First (gates all other decisions)
| File | Prompt | Decision it unlocks |
|------|--------|---------------------|
| `1A-kling-pricing.md` | Kling AI current pricing & real costs | Actual cost per video |
| `1B-midjourney-video.md` | MidJourney video current state | MJ viability as primary tool |
| `1C-full-tool-comparison.md` | Complete AI video tool comparison | **Which tool(s) to use + actual monthly budget** |

**Run all 3 in parallel.** Wait for results before proceeding.

### Wave 2 — Run Second (platform decisions)
| File | Prompt | Decision it unlocks |
|------|--------|---------------------|
| `2A-tiktok-video-length.md` | TikTok optimal video length | Primary platform length target |
| `2B-other-platforms-length.md` | IG Reels, YT Shorts, FB length | Cross-platform length strategy |

**Run both in parallel.**

### Wave 2.5 — Run in Parallel with Wave 2
| File | Prompt | Decision it unlocks |
|------|--------|---------------------|
| `3A-tiktok-sound-strategy.md` | TikTok sound strategy | Audio approach for primary platform |
| `5A-ai-content-policy.md` | AI content policy (all platforms) | Disclosure strategy |

**Run both in parallel, concurrent with Wave 2.**

### Wave 3 — Run Third (workflow design)
| File | Prompt | Decision it unlocks |
|------|--------|---------------------|
| `4A-real-workflows.md` | Real AI video production workflows | **Production workflow + batch schedule** |
| `9A-budget-optimization.md` | Sub-$100/month tool stacks | Final budget allocation |

**Run both in parallel.** Depends on Wave 1 results for context.

### Wave 4 — Run Fourth (refinement)
| File | Prompt | Decision it unlocks |
|------|--------|---------------------|
| `3B-voice-generation-tools.md` | Voice generation tools (Australian) | TTS tool selection |
| `4B-scheduling-distribution.md` | Batch scheduling & distribution | Publishing workflow |
| `6A-competitive-landscape.md` | Competitive landscape | Positioning & differentiation |
| `7A-ethereal-effects.md` | Bioluminescent/ethereal effects | Visual direction specifics |
| `8A-midjourney-v7-prompting.md` | MJ V7 character consistency | Prompt templates |

**Run all 5 in parallel.** These are refinement — nice to have, not blocking.

## Decision Gates

```
Wave 1 complete → DECIDE: Primary video tool + monthly budget
Wave 2 complete → DECIDE: Video length targets per platform
Wave 2.5 complete → DECIDE: Audio approach + disclosure strategy
Wave 3 complete → DECIDE: Production workflow + batch schedule
Wave 4 complete → DECIDE: Positioning, visual direction, prompt templates
```

## Saving Results

Save each research result as:
```
docs/research/bb-content-production/results/1A-kling-pricing-RESULTS.md
docs/research/bb-content-production/results/1B-midjourney-video-RESULTS.md
...etc
```

## Context for the Research Agent

These prompts assume the agent knows nothing about Baby Brains. Each prompt is self-contained. If the agent needs context, provide this brief:

> Baby Brains is an Australian Montessori-based parenting education brand producing short-form social video content. Visual style: stylized 3D / soft clay aesthetic (NOT photorealistic — AI babies that look real are prohibited by platforms). Brand aesthetic: "Bioluminescent Solarpunk" with warm clay-amber tones and subsurface glow. Target: 25-35 videos/month across TikTok, IG Reels, YT Shorts, Facebook. Budget: $50-120/month for tools. Hardware: RTX 3050 Ti 4GB VRAM for any local processing.
