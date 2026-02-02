# Phase 2 Research Prompts: Production Pipeline

## Purpose
These prompts focus on HOW to produce content efficiently, not which tools to use (Phase 1 answered that). Each prompt targets a specific stage of the production pipeline with emphasis on real-world workflows from experienced creators.

## New Information Since Phase 1
- **Kling IMAGE 3.0** (early access Feb 2026): Image Series Mode for storyboard generation, Visual Chain-of-Thought, 2K/4K output, batch optimization. Could potentially replace MidJourney for image generation.
- **Kling O1 (Omni One)** (Dec 2025): Unified 7-in-1 video model, 7-10 reference images with @image tagging.
- **Hailuo pricing corrected**: $94.99 is Master (10K credits, NOT unlimited). True unlimited is Max at $199.99/month.
- **Hardware confirmed**: 8GB VRAM, 32GB RAM (not 4GB as previously documented).
- **DaVinci Resolve Studio** available (full license).
- **Envato VideoGen**: Promotional unlimited via Luma Ray3 at $16.50/month until Feb 25, 2026.

## Prompts

| ID | Title | Focus | Priority |
|----|-------|-------|----------|
| **PA** | Hailuo Max Burst Pipeline | Maximizing one $200 month of unlimited generation | HIGH |
| **PB** | Pika Stylized Clay Pipeline | End-to-end MJ->Pika workflow for best clay quality | HIGH |
| **PC** | Kling O1 & IMAGE 3.0 Pipeline | Precision generation with O1/3.0 features, 60s native | HIGH |
| **PD** | Post-Production Pipeline | DaVinci Resolve assembly, metadata, captions, export | HIGH |
| **PE** | Claude Code Automation | MCP tools, ffmpeg scripts, QC pipeline, asset management | MEDIUM |
| **PF** | Content-to-Script System | Knowledge base -> script -> scene breakdown -> prompts | HIGH |

## Execution Order

### Run First (in parallel -- all are independent)
- **PA** (Hailuo burst) -- answers "how to maximize the $200 month"
- **PB** (Pika pipeline) -- answers "best quality workflow for stylized clay"
- **PC** (Kling pipeline) -- answers "precision control and 60s generation"

### Run Second (in parallel -- depends on PA/PB/PC for tool context)
- **PD** (Post-production) -- answers "how to assemble and export efficiently"
- **PF** (Content-to-script) -- answers "how to go from idea to production-ready script"

### Run Third (after PD/PF provide pipeline context)
- **PE** (Claude Code automation) -- answers "what can we automate in VS Code"

## Decision Gates

After PA + PB + PC: **Which tool wins for each content tier?**
- Hook clips (7-15s): Pika or Hailuo?
- Core educational (30-45s): Pika Pikaframes or Kling?
- Deep dives (60-90s): Kling 60s native or Hailuo stitched?
- Burst month: Hailuo Max confirmed or alternative?

After PD: **Post-production workflow finalized**
- DaVinci Resolve template established
- Metadata scrubbing verified
- Export presets for all 4 platforms

After PF: **Content system established**
- Script template(s) selected
- Scene breakdown format standardized
- Prompt generation from scene descriptions templated

After PE: **Automation scope defined**
- Which MCP tools to install
- What ffmpeg scripts to build
- QC pipeline design
- Asset management database schema
