# Handover: Fix CLI Timeouts for Full Pipeline

## Context
Activity conversion via CLI mode (Max subscription) takes 20+ minutes total. Current timeouts are too short.

## Problem
| Stage | Current Timeout | Needed |
|-------|-----------------|--------|
| SkillExecutor CLI | 300s (5 min) | 600s (10 min) per skill |
| SubAgentExecutor | 120s | 300s for quality audit |

## Files to Modify

### 1. `/home/squiz/ATLAS/atlas/orchestrator/skill_executor.py`
Line ~575: Change timeout from 300 to 600
```python
# BEFORE
timeout=300,  # 5 minute timeout
# AFTER
timeout=600,  # 10 minute timeout for complex skills
```

Line ~577: Change async timeout
```python
# BEFORE
timeout=310,
# AFTER
timeout=610,
```

Line ~580: Update error message
```python
# BEFORE
"CLI execution timed out after 5 minutes"
# AFTER
"CLI execution timed out after 10 minutes"
```

### 2. `/home/squiz/ATLAS/atlas/pipelines/activity_conversion.py`
Line ~149: SubAgentExecutor timeout (for quality audit)
```python
# BEFORE
self.sub_executor = SubAgentExecutor(timeout=120)
# AFTER
self.sub_executor = SubAgentExecutor(timeout=300)
```

Also update `audit_quality()` spawn timeout (~line 751):
```python
# BEFORE
timeout=120,
# AFTER
timeout=300,
```

And `reflect_on_failure()` spawn timeout (~line 1143):
```python
# BEFORE
timeout=60,
# AFTER
timeout=120,
```

## Test Command
```bash
python -m atlas.pipelines.activity_conversion --activity tummy-time
```

Expected: Full pipeline runs 15-25 minutes, reaches Quality Audit stage.

## Commits Already Made
```
a3f1c68 Fix SkillExecutor init and increase CLI timeout to 5 minutes
38d4ab9 Add Quality Audit Pipeline with intelligent retry (Phase 4)
```

## After Timeout Fix
Commit with message:
```
Increase CLI timeouts for full pipeline execution

Skills take 5-10 minutes each via CLI mode.
Full pipeline expected: 15-25 minutes total.
```
