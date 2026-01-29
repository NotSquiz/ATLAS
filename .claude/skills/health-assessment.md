# Health Assessment Workflow

## Overview
ATLAS health and fitness tracking system with Traffic Light routing and GATE-based progression.

## Daily Health Flow

### Morning Sync (5am cron)
```bash
python -m atlas.health.cli daily
```

1. **Garmin Sync**: Sleep, HRV, body battery, resting HR
2. **Traffic Light Evaluation**: GREEN/YELLOW/RED
3. **Cache Update**: `~/.atlas/morning_status.json`
4. **Workout Selection**: Based on traffic light and schedule

### Traffic Light Rules

| Status | Criteria | Workout Modification |
|--------|----------|---------------------|
| GREEN | Sleep >7h, HRV Balanced+, Battery >50 | Full intensity |
| YELLOW | Sleep 5-7h OR HRV Low OR Battery 30-50 | -15% intensity |
| RED | Sleep <5h OR HRV Poor OR Battery <30 | Recovery only |

## Baseline Assessments

### Protocol Sessions
- **Session A**: Body composition, measurements, BP, RHR
- **Session B**: Strength, mobility, stability tests
- **Session C**: Cardio tests, HR recovery

### Running Commands
```bash
# View protocol info
python -m atlas.health.cli assess baseline

# Log single assessment
python -m atlas.health.cli assess log --id ankle_dorsiflexion_left --value 9.5

# Check GATE readiness
python -m atlas.health.cli assess gate 1
```

## GATE System (Running Readiness)

| GATE | Timing | Key Criteria |
|------|--------|--------------|
| GATE 1 | Week 12+ | Ankle LSI >=90%, balance 60s, 25 heel raises |
| GATE 2 | Week 16+ | Hop tests LSI >=90%, 2-mile jog |
| GATE 3 | Week 20+ | Hop tests LSI >=95%, tempo run 20min |
| GATE 4 | Week 24+ | Sprint progression, RSA <=10% decrement |

### LSI Calculation
```
LSI = (Affected Limb / Unaffected Limb) * 100%
```
Must reach 90-95% for running clearance.

## Phase Management

### Phase Progression
- **Phase 1 -> 2**: GATE 1 passed + 4 weeks minimum + pain <=3/10
- **Phase 2 -> 3**: GATE 2 passed + structured running

### Regression Triggers
- 3+ RED days in one week
- Pain spike >=6/10
- Injury setback

## Voice Commands

```bash
# Quick status
"my status"           # Traffic light + key metrics
"morning briefing"    # Full health briefing

# Pain tracking
"shoulder is at a 4"  # Log pain 0-10
"pain status"         # Current pain levels

# Workout flow
"start workout"       # Begin scheduled workout
"finished workout"    # Log completion + Garmin sync

# Assessment
"start baseline"      # Begin assessment protocol
"session A/B/C"       # Start specific session
```

## Key Files

| File | Purpose |
|------|---------|
| `atlas/health/cli.py` | 9-command CLI |
| `atlas/health/router.py` | Traffic Light logic |
| `atlas/health/service.py` | Health orchestration |
| `atlas/health/garmin.py` | Garmin integration |
| `atlas/health/assessment.py` | LSI, GATE evaluation |
| `config/assessments/baseline.json` | 40+ assessment definitions |
| `config/assessments/protocol_voice.json` | Voice protocol (69 tests) |
