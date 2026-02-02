# Baby Brains Content Production: Verification & Planning Handoff

> For the next Claude session. Read this FIRST, then the SYNTHESIS.md, then verify against raw research.
> Created: 2026-02-02

## Current State

19 research prompts have been run across two phases:
- **Phase 1** (13 prompts: 1A-8A): Tool economics, platform algorithms, audio, policy, competition, visual direction, MJ V7
- **Phase 2** (6 prompts: PA-PF): Hailuo burst, Pika clay workflow, Kling O1, DaVinci post-production, Claude Code automation, Content-to-script

A master synthesis exists at `SYNTHESIS.md` (~900+ lines). It was written at speed and has known gaps. The user caught at least one omission (multi-scene stitching techniques were reduced to a one-liner). There are likely others.

## What Needs to Happen

### 1. VERIFY: Re-read raw research with Junior Analyst focus

Use the verification methodology from `docs/VERIFICATION_PROMPTS.md` -- specifically the **Junior Analyst Challenge** and **Fact-Check** patterns.

**For each raw result file**, spawn an opus agent to:
1. Read the raw research file
2. Read the corresponding section in SYNTHESIS.md
3. List everything in the raw research that is NOT in the synthesis
4. Flag contradictions between raw data and synthesis
5. Flag actionable details that were summarized away

**File index:**

| File | Location | Key Topic |
|------|----------|-----------|
| 1A | `results/1A.md` | Kling pricing & real costs |
| 1B | `results/1B.md` | MidJourney video state |
| 1C | `results/1C.md` | Full tool comparison |
| 2A | `results/2A.md` | TikTok optimal length |
| 2B | `results/2B.md` | IG/YT/FB optimal length |
| 3A | `results/3A.md` | TikTok sound strategy |
| 3B | `results/3B.md` | Voice generation tools |
| 4A | `results/4A.md` | Real AI video workflows |
| 4B | `results/4B.md` | Scheduling & distribution |
| 5A | `results/5A.md` | AI content policy |
| 6A | `results/6A.md` | Competitive landscape |
| 7A | `results/7A.md` | Ethereal/bioluminescent effects |
| 8A | `results/8A.md` | MJ V7 prompting |
| PA | `results/PA.md` | Hailuo Max burst pipeline |
| PB | `results/PB.md` | Pika stylized clay pipeline |
| PC | `results/PC.md` | Kling O1 & IMAGE 3.0 |
| PD | `results/PD.md` | DaVinci post-production |
| PE | `results/PE.md` | Claude Code automation |
| PF | `results/PF.md` | Content-to-script system |

All files are in: `/home/squiz/code/ATLAS/docs/research/bb-content-production/`

Phase 1 extractions (processed summaries) are in `extracted/` subfolder.
Phase 2 raw results are in `results/` subfolder.

### 2. IDENTIFY GAPS: Known issues and open questions

**Known gaps in synthesis:**

1. **No practical daily workflow.** The synthesis describes pipeline stages but not "what does Tuesday afternoon look like." The user works a couple hours per day. Need a concrete weekly schedule.

2. **"Studio quality" is undefined.** The user's goal is A+ quality that stands above AI slop. What specifically makes the difference? Frame rates, color grading depth, sound design, pacing, caption quality? This needs a quality checklist derived from the research.

3. **PE's YouTube code sets `selfDeclaredMadeForKids: True`** -- this is WRONG. Baby Brains content is for ADULTS (parents), not children. This flag would severely limit reach and disable comments. Must be `False`.

4. **Kling IMAGE 3.0 discrepancy.** The user provided actual screenshots of early access release notes. The PC research agent said "no evidence of Kling IMAGE 3.0." The user's screenshots are primary evidence -- they should override the research agent's finding. The synthesis partially captured this but should re-examine.

5. **Priority tagging (P1/P2/P3 for derivative timelines)** was designed after PE was sent. Not researched. Need to verify: can DaVinci scripting programmatically duplicate a timeline and delete specific clips? The PE research says clips can only be appended, not deleted -- this may block automated derivative creation.

6. **Chatterbox on 8GB VRAM is unverified.** PE says 4-6GB. The user needs to actually test this. If it doesn't work, the voice strategy changes.

7. **No character has been created yet.** All prompt engineering is theoretical. The MJ character design workflow (--oref, reference sheets) hasn't been tested in practice.

8. **Burst month logistics are theoretical.** Nobody has confirmed they successfully did a one-month Hailuo Max intensive with the specific workflow we're proposing.

9. **Cross-document details may be lost.** Examples of things that might be in raw research but not in synthesis:
   - Specific creator names/channels for reference
   - Exact URLs for tools/resources
   - Edge cases and failure modes
   - Specific numbers (e.g., exact credit costs for specific operations)
   - Community workarounds and tips

### 3. BUILD: Practical workflow document

After verification, create a new document: `WORKFLOW.md` that is:
- A step-by-step daily/weekly production guide
- Written for a human who has 2 hours/day
- Organized by phase of production, not by tool
- Includes quality checkpoints at each stage
- Distinguishes what Claude Code automates vs what the human does
- Starts with "Week 1: Setup" and progresses to steady-state production

### 4. PLAN: What to build first

The PE research suggests a build priority, but it should be reality-checked:
- Phase 1 (Week 1-2): SQLite + MCP servers + ffmpeg QC scripts
- Phase 2 (Week 3-4): Hook generator + prompt templates + voice setup
- Phase 3 (Month 2): DaVinci scripts + API uploads
- Phase 4 (Month 3+): Polish

But before ANY code is written:
1. Create MJ character (test --oref workflow)
2. Generate one test video on Pika free tier
3. Generate one test video on Kling free tier
4. Test Chatterbox on 8GB VRAM
5. Assemble one complete video in DaVinci manually

This real-world testing will validate or invalidate assumptions in the research.

## Verification Methodology

For the next session, use this pattern:

```
For each research file (PA.md, PB.md, etc.):

1. READ the raw research file completely
2. READ the corresponding SYNTHESIS.md section
3. COMPARE: What's in raw but NOT in synthesis?
4. FLAG: Any contradictions, outdated info, or wrong assumptions
5. EXTRACT: Actionable details that were summarized away
6. QUALITY CHECK: Would this detail matter for A+ studio quality output?
```

Run this as parallel opus agents (one per file or group of related files) to stay within context limits.

## User Context

- Hardware: 8GB VRAM, 32GB RAM, WSL2 on Windows
- Software: DaVinci Resolve Studio (full license), VS Code with Claude Code, ffmpeg
- Budget: $50-120/month for tools
- Time: ~2 hours/day for production
- Content: Montessori parenting education for ADULTS (not children)
- Aesthetic: Stylized 3D / clay / Brancusi-inspired with bioluminescent glow
- Goal: A+ studio quality that stands above typical AI content
- Voice: Australian accent, warm, evidence-based
- Platforms: TikTok, Instagram Reels, YouTube Shorts, Facebook
- Volume target: 25-35 videos/month (5-7/week)
