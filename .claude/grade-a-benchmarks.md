# Grade A Benchmarks for A/B Comparison
## Established January 10, 2026

These benchmarks were established by 3 Opus sub-agents analyzing complete Grade A activities.

---

## Benchmark Activities

| Domain | Activity | Raw Source ID | Canonical File | Score | Method |
|--------|----------|---------------|----------------|-------|--------|
| Movement | Tummy Time (0-6m) | `tummy-time` | `ACTIVITY_MOVEMENT_TUMMY_TIME_MICRO_SESSIONS_0_6M.yaml` | 70/70 | True A/B |
| Practical Life | Clothes Folding (24-36m) | `caring-for-clothes-folding-hanging` | `ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml` | 68.5/70 | True A/B |
| Feeding | Responsive Bottle Breast (0-6m) | None (manually created) | `ACTIVITY_FEEDING_RESPONSIVE_BOTTLE_BREAST_0_6M.yaml` | 69/70 | Rubric-based |

### Raw Source Location
```
/home/squiz/code/knowledge/sources/structured/activities_v1/activities_fixed_01.yaml
```

---

## Universal Patterns (All 3 Activities)

### Anti-Pattern Compliance
- **Em-dashes**: ZERO (—, –, --)
- **Formal transitions**: ZERO (Moreover, Furthermore, Additionally, etc.)
- **Superlatives**: ZERO (amazing, incredible, perfect, etc.)
- **Outcome promises**: ZERO (will develop, guarantees, etc.)
- **Pressure language**: ZERO (must, need to, have to)

### Philosophy Integration
All 6 Montessori concepts present, naturally woven (not lectured):
1. Cosmic View - Activity framed as meaningful work
2. Spiritual Embryo - Child develops from within
3. Adult as Obstacle - Self-awareness prompts for adult
4. Freedom Within Limits - Limits as loving structure
5. Transformed Adult - Adult self-regulation
6. Conditions Not Outcomes - Trust over control

### Signature Phrases
- "Sound familiar?" / "That's normal too"
- "Your job isn't to teach... It's to [listen/watch/create conditions]"
- "Notice the urge to [help/correct]. Sometimes helping is love. Sometimes it's impatience."
- "Both are normal" / "Wide variation is normal"
- "Some babies... Others..." (never absolutes)

### Rationale Pattern
Every rationale follows: Observable → Philosophy → Psychology → Reassurance
1. What parent sees (observable behavior)
2. Why it matters for who child is becoming (philosophy)
3. How parent should feel about it (permission/psychology)
4. It's okay, you're doing enough (reassurance)

---

## Domain-Specific Emphasis

| Domain | Primary Emphasis | Less Emphasis On |
|--------|------------------|------------------|
| Movement | Physical development, "body already knows" | Complex neuroscience |
| Practical Life | Adult self-reflection, "notice the urge" | Relational framing |
| Feeding | Relational/connection, caregiver wellbeing | Brain metaphors |

---

## A/B Comparison Method

### Method 1: True A/B (for activities with raw sources)

**Step 1:** Run pipeline on raw source
```bash
python -m atlas.pipelines.activity_conversion --activity tummy-time --retry 2
python -m atlas.pipelines.activity_conversion --activity caring-for-clothes-folding-hanging --retry 2
```

**Step 2:** Compare automated output directly to manual Grade A file
- Same input → Both outputs should match in voice, structure, philosophy
- Document any divergences

### Method 2: Rubric-based (for activities without raw sources)

**Step 1:** Run pipeline on any raw activity (e.g., `undivided-attention-during-feeding`)
```bash
python -m atlas.pipelines.activity_conversion --activity undivided-attention-during-feeding --retry 2
```

**Step 2:** Score against rubric patterns
- Anti-pattern counts (should be ZERO)
- Philosophy presence (natural, not forced)
- Signature phrases (present and authentic)
- Rationale pattern (Observable→Philosophy→Psychology→Reassurance)

### Scoring Rubric (70 points)
- Anti-patterns: 20 points (deductions for violations)
- Philosophy: 15 points
- Australian Voice: 15 points
- Parent Psychology: 10 points
- Structure: 10 points

---

## Benchmark File Locations

| Benchmark | Path |
|-----------|------|
| Movement | `/home/squiz/code/knowledge/data/canonical/activities/movement/ACTIVITY_MOVEMENT_TUMMY_TIME_MICRO_SESSIONS_0_6M.yaml` |
| Practical Life | `/home/squiz/code/knowledge/data/canonical/activities/practical_life/ACTIVITY_PRACTICAL_LIFE_CARING_CLOTHES_FOLDING_HANGING_24_36M.yaml` |
| Feeding | `/home/squiz/code/knowledge/data/canonical/activities/feeding/ACTIVITY_FEEDING_RESPONSIVE_FEEDING_BASICS_0_6M.yaml` |

---

## Success Criteria

Automated output achieves Grade A when:
1. Zero blocking QC issues
2. Score ≥ 65/70 on rubric
3. All 6 philosophy concepts present (naturally woven)
4. Signature phrases feel authentic (not templated)
5. Rationale pattern consistent throughout
