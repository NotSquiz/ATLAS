# Research Prompt: Octalysis Gamification Framework

**For: Opus Research Agent (Web)**
**Purpose: Deep dive into Octalysis for ATLAS "Lethal Gentleman" skill system**
**Output Location: `docs/OSRS/Octalysis - Research Synthesis.md`**

---

## Context: What We're Building

We're building a gamification system called "The Lethal Gentleman" - a life orchestration system with 12 skills across 3 domains:

**BODY (The Vessel):** Strength, Endurance, Mobility, Nutrition
**MIND (The Citadel):** Focus, Learning, Reflection, Creation
**SOUL (The Character):** Presence, Service, Courage, Consistency

Each skill has:
- A virtue it represents (e.g., Strength = Power)
- XP sources (activities that award XP)
- A shadow warning (the dark side if taken too far)

The system uses OSRS-style exponential leveling (Level 99 max, ~13M XP).

**Critical Constraints:**
1. Must NOT create addictive dark patterns
2. Must gamify the USER's inputs, not their child's outputs
3. Must design for eventual graduation (user no longer needs the system)
4. Shadow warnings exist for each skill to prevent obsession

---

## Research Questions

### Part 1: Octalysis Framework Fundamentals

1. **What are the 8 Core Drives of Octalysis?**
   - Explain each drive with examples
   - Which drives are "White Hat" (positive) vs "Black Hat" (negative)?
   - What is the Octalysis score and how is it calculated?

2. **How does the Octalysis Spectrum work?**
   - Extrinsic vs Intrinsic motivation spectrum
   - Left Brain (logic) vs Right Brain (creativity) drives
   - How do these interact?

3. **What is Level 2 and Level 3 Octalysis?**
   - How does the framework account for different user phases?
   - Discovery → Onboarding → Scaffolding → Endgame
   - What drives are most important at each phase?

### Part 2: Applying to Lethal Gentleman

4. **Map each of our 12 skills to Octalysis drives:**
   - Which Core Drive does each skill primarily activate?
   - Are there any drives we're not engaging?
   - Are we over-relying on any single drive?

5. **Analyze our current XP sources through Octalysis lens:**
   - "workout_strength": 150 XP - What drive?
   - "evening_audit": 60 XP (Seneca's Trial) - What drive?
   - "fear_faced": 100 XP - What drive?
   - "project_shipped": 200 XP - What drive?

6. **How should we handle the "Endgame" phase?**
   - OSRS Level 99 takes years - what keeps people engaged?
   - How do we avoid "level grinding" becoming meaningless?
   - What's the Octalysis approach to long-term retention?

### Part 3: Anti-Dark Pattern Design

7. **Which Octalysis drives can become toxic?**
   - Loss Aversion (Core Drive 8) risks
   - Scarcity (Core Drive 6) risks
   - Social Pressure (Core Drive 5) risks
   - How do we use them ethically or avoid them?

8. **How do we design for "graduation"?**
   - The system should make itself less necessary over time
   - How does Octalysis approach intrinsic motivation development?
   - What game mechanics help users internalize the behaviors?

9. **Streak mechanics - good or toxic?**
   - Our current streak system: consecutive days, caps at 14
   - Octalysis perspective on streaks
   - Better alternatives (rolling windows, forgiveness mechanics)?

### Part 4: XP Economy Design

10. **What does Octalysis say about reward calibration?**
    - Variable vs fixed rewards
    - Optimal reward frequency
    - Diminishing returns handling
    - "Reward inflation" prevention

11. **Achievement design through Octalysis:**
    - What makes achievements meaningful?
    - Rarity tiers and their psychological impact
    - "Epic Meaning" (Core Drive 1) in achievement naming

12. **Leaderboards and social comparison:**
    - We have NO leaderboards (solo system)
    - Is this a mistake or correct for our use case?
    - Self-competition alternatives

### Part 5: Practical Recommendations

13. **Provide specific recommendations for our system:**
    - Which 2-3 Core Drives should we emphasize?
    - Which drives should we explicitly avoid/limit?
    - Specific mechanics to add or remove

14. **Propose an Octalysis-informed XP table:**
    - Which activities should give more/less XP?
    - Are there activity types we're missing?
    - How should we handle "failure XP" (our Failure Codex)?

15. **Level milestone design:**
    - What should happen at Level 10, 25, 50, 75, 99?
    - Special titles/names for achievements
    - Ceremonies/rituals for major milestones

---

## Output Format

Please structure your research synthesis as:

```markdown
# Octalysis Framework - Research Synthesis for ATLAS

## Executive Summary
[2-3 paragraphs: Key findings and top recommendations]

## Part 1: Framework Fundamentals
[Detailed explanation of Octalysis]

## Part 2: Skill-to-Drive Mapping
[Table mapping our 12 skills to Core Drives]

## Part 3: Anti-Dark Pattern Analysis
[Our risks and mitigations]

## Part 4: XP Economy Recommendations
[Specific XP values and rationale]

## Part 5: Implementation Roadmap
[Prioritized list of changes to make]

## Appendix: Sources
[URLs and citations]
```

---

## Background Reading (If Helpful)

- Yu-kai Chou's Octalysis website: yukaichou.com/gamification-examples/octalysis-complete-gamification-framework/
- Yu-kai Chou's book: "Actionable Gamification: Beyond Points, Badges, and Leaderboards"
- Our research: `docs/OSRS/The Lethal Gentleman - Research Synthesis.md`
- Our current XP table: `atlas/gamification/xp_service.py`

---

## Success Criteria

The research is successful if it:
1. Maps all 12 skills to Octalysis Core Drives
2. Identifies which drives we're over/under-using
3. Provides specific XP calibration recommendations
4. Addresses dark pattern risks explicitly
5. Gives actionable implementation priorities
