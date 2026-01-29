# ATLAS Supplement Migration
## For Opus CLI Implementation

**Date:** January 2026  
**Final Timing Categories:** `preworkout`, `with_meal`, `before_bed`

---

## Final Supplement Stack

| Supplement | Timing | Dose | Notes |
|------------|--------|------|-------|
| **PREWORKOUT (fasted, ~5am)** ||||
| Electrolytes | preworkout | 1 scoop | Upon waking |
| Creatine | preworkout | 5g | Daily |
| NR (Nicotinamide Riboside) | preworkout | 1 cap | Daily |
| Tongkat Ali | preworkout | 5g | 3 weeks on / 1 off |
| NAC | preworkout | 1 scoop | Split dose - morning |
| Collagen | preworkout | 15g + Vit C | Strength days only |
| **WITH MEAL (breakfast, ~7am)** ||||
| L-Theanine | with_meal | 1/4 tsp | With coffee |
| Allimax (Garlic) | with_meal | 1 cap | |
| Preconception Multi | with_meal | 2 caps | |
| Nicotinamide (B3) | with_meal | 500mg | Skin protection |
| Bio Active Lipids | with_meal | 2 caps | NEW |
| Methyl Fortified | with_meal | 1 pill | NEW |
| Liquid Herbs | with_meal | 15ml | NEW |
| **BEFORE BED (~9pm)** ||||
| Magnesium Glycinate | before_bed | 300-400mg | |
| NAC | before_bed | 1 scoop | Split dose - evening |
| Inositol | before_bed | 1 tsp | |
| L-Theanine | before_bed | 1/4 tsp | |
| Collagen | before_bed | 15g | Cardio + rest days |

---

## Migration SQL

Run this in order:

```sql
-- ============================================
-- STEP 1: Update existing supplement timings
-- ============================================

-- Preworkout supplements (was "morning")
UPDATE supplements SET timing = 'preworkout' WHERE name = 'Creatine';
UPDATE supplements SET timing = 'preworkout' WHERE name = 'NR' OR name = 'Nicotinamide Riboside';
UPDATE supplements SET timing = 'preworkout' WHERE name = 'Tongkat Ali';
UPDATE supplements SET timing = 'preworkout' WHERE name = 'Collagen';

-- NAC: Update existing to preworkout, we'll add a second entry for before_bed
UPDATE supplements SET timing = 'preworkout', dose = '1 scoop' WHERE name = 'NAC';

-- With meal supplements (keep or update)
UPDATE supplements SET timing = 'with_meal' WHERE name = 'L-Theanine' AND timing = 'morning';
UPDATE supplements SET timing = 'with_meal' WHERE name = 'Allimax' OR name = 'Allimax (Garlic)';
UPDATE supplements SET timing = 'with_meal' WHERE name = 'Preconception Multi';
UPDATE supplements SET timing = 'with_meal' WHERE name LIKE '%Nicotinamide%' AND name NOT LIKE '%Riboside%';

-- Before bed supplements
UPDATE supplements SET timing = 'before_bed' WHERE name = 'Magnesium Glycinate';
UPDATE supplements SET timing = 'before_bed' WHERE name = 'Inositol';
UPDATE supplements SET timing = 'before_bed' WHERE name LIKE '%L-Theanine%' AND timing = 'before_bed';

-- ============================================
-- STEP 2: Remove deprecated timing values
-- ============================================

-- Remove old "morning" timing (should all be preworkout or with_meal now)
-- Verify first: SELECT * FROM supplements WHERE timing = 'morning';

-- Remove TMG (no longer in stack)
UPDATE supplements SET active = 0 WHERE name = 'TMG' OR name = 'Trimethylglycine';

-- ============================================
-- STEP 3: Add new supplements
-- ============================================

-- Electrolytes (preworkout - upon waking)
INSERT INTO supplements (name, dose, timing, active, notes)
SELECT 'Electrolytes', '1 scoop', 'preworkout', 1, 'Upon waking'
WHERE NOT EXISTS (SELECT 1 FROM supplements WHERE name = 'Electrolytes');

-- NAC evening dose (split dosing)
INSERT INTO supplements (name, dose, timing, active, notes)
SELECT 'NAC (PM)', '1 scoop', 'before_bed', 1, 'Split dose - evening'
WHERE NOT EXISTS (SELECT 1 FROM supplements WHERE name = 'NAC (PM)');

-- Bio Active Lipids
INSERT INTO supplements (name, dose, timing, active, notes)
SELECT 'Bio Active Lipids', '2 caps', 'with_meal', 1, 'With breakfast'
WHERE NOT EXISTS (SELECT 1 FROM supplements WHERE name = 'Bio Active Lipids');

-- Methyl Fortified
INSERT INTO supplements (name, dose, timing, active, notes)
SELECT 'Methyl Fortified', '1 pill', 'with_meal', 1, 'With breakfast'
WHERE NOT EXISTS (SELECT 1 FROM supplements WHERE name = 'Methyl Fortified');

-- Liquid Herbs
INSERT INTO supplements (name, dose, timing, active, notes)
SELECT 'Liquid Herbs', '15ml', 'with_meal', 1, 'With food'
WHERE NOT EXISTS (SELECT 1 FROM supplements WHERE name = 'Liquid Herbs');

-- Collagen evening entry (for cardio/rest days)
INSERT INTO supplements (name, dose, timing, active, notes)
SELECT 'Collagen (PM)', '15g', 'before_bed', 1, 'Cardio + rest days only'
WHERE NOT EXISTS (SELECT 1 FROM supplements WHERE name = 'Collagen (PM)');

-- L-Theanine PM entry (separate from morning dose)
INSERT INTO supplements (name, dose, timing, active, notes)
SELECT 'L-Theanine (PM)', '1/4 tsp', 'before_bed', 1, 'Before bed'
WHERE NOT EXISTS (SELECT 1 FROM supplements WHERE name = 'L-Theanine (PM)');

-- ============================================
-- STEP 4: Update notes for conditional supps
-- ============================================

UPDATE supplements SET notes = 'Strength days only' WHERE name = 'Collagen' AND timing = 'preworkout';
UPDATE supplements SET notes = '3 weeks on / 1 off cycle' WHERE name = 'Tongkat Ali';
UPDATE supplements SET notes = 'Split dose - morning' WHERE name = 'NAC' AND timing = 'preworkout';

-- ============================================
-- STEP 5: Verify migration
-- ============================================

-- Run this to check the final state:
-- SELECT name, dose, timing, active, notes FROM supplements WHERE active = 1 ORDER BY 
--   CASE timing 
--     WHEN 'preworkout' THEN 1 
--     WHEN 'with_meal' THEN 2 
--     WHEN 'before_bed' THEN 3 
--   END, name;
```

---

## Post-Migration Verification

After running migration, verify with:

```sql
SELECT timing, COUNT(*) as count FROM supplements WHERE active = 1 GROUP BY timing;
```

**Expected result:**
| timing | count |
|--------|-------|
| preworkout | 6 |
| with_meal | 7 |
| before_bed | 5 |

**Total: 18 supplement entries** (some are AM/PM splits of same supplement)

---

## Voice Command Updates

After migration, these commands should work:

| Voice Command | Action |
|---------------|--------|
| "took my preworkout supps" | Marks 6 preworkout supplements |
| "took my morning supps" | Alias → preworkout |
| "took breakfast supps" | Marks 7 with_meal supplements |
| "took my bedtime supps" | Marks 5 before_bed supplements |
| "supplement status" | Shows completion by timing window |
| "what supps are next?" | Time-aware response |

---

## Timing Aliases for Voice Bridge

```python
SUPPLEMENT_TIMING_ALIASES = {
    # Preworkout
    "preworkout": "preworkout",
    "pre workout": "preworkout",
    "pre-workout": "preworkout",
    "morning": "preworkout",  # Alias morning to preworkout
    "fasted": "preworkout",
    "waking": "preworkout",
    
    # With meal
    "with_meal": "with_meal",
    "with meal": "with_meal",
    "breakfast": "with_meal",
    "with breakfast": "with_meal",
    "with food": "with_meal",
    
    # Before bed
    "before_bed": "before_bed",
    "before bed": "before_bed",
    "bedtime": "before_bed",
    "evening": "before_bed",
    "night": "before_bed",
    "pm": "before_bed",
}
```

---

## Conditional Logic: Collagen by Day Type

The Collagen supplement appears twice:
- `Collagen` (preworkout) - Strength days
- `Collagen (PM)` (before_bed) - Cardio/rest days

**Option A: Manual tracking**  
User says "took my collagen" and it marks whichever timing is appropriate.

**Option B: Smart tracking (recommended)**  
Check `phase_config.json` for today's workout type:
- If strength day → show Collagen in preworkout list, hide Collagen (PM)
- If cardio/rest day → show Collagen (PM) in before_bed list, hide Collagen

```python
def get_collagen_timing_for_today() -> str:
    """Returns which collagen entry to show based on today's workout."""
    from atlas.health.workout_lookup import get_todays_workout
    
    workout = get_todays_workout()
    if workout and workout.get("type", "").upper().startswith("STRENGTH"):
        return "preworkout"
    else:
        return "before_bed"
```

---

## Notes for Opus CLI

1. **Run migration first** before updating voice patterns
2. **Verify counts** match expected (6 preworkout, 7 with_meal, 5 before_bed)
3. **TMG is deactivated**, not deleted (preserves history)
4. **NAC and Collagen have AM/PM entries** - both should be marked when user takes them
5. **L-Theanine has AM/PM entries** - morning with coffee, evening before bed

---

*Migration Version: 1.0*
*Stack Version: January 2026*
