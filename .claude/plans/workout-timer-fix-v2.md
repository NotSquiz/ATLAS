# ATLAS Workout Timer Fix - REVISED Plan v2

## Verification Results

Four Opus subagents reviewed v1 and found critical issues. This revised plan addresses them.

### Key Finding: Root Cause Was Wrong

The original diagnosis was incorrect. The code at lines 1418-1435 DOES check for `duration_seconds` and SHOULD start the timer. The `ex.get('reps')` check is falsy for timed exercises, so it's skipped.

**Actual root cause hypothesis:**
1. `_workout_current_exercise` may not have `duration_seconds` populated at runtime
2. OR there's a code path that returns early before reaching the timed check
3. OR an exception is being silently caught

**Action:** Add debug logging FIRST before any code changes.

---

## Revised Implementation Plan

### Phase 0: DIAGNOSTIC (Must Complete First)

**Goal:** Identify the ACTUAL root cause before changing code.

**Add debug logging to `_handle_workout_ready()`:**

```python
async def _handle_workout_ready(self, text: str) -> str:
    """User said ready - check for weight or start the set."""
    logger.info(f"[READY] _handle_workout_ready called with text='{text}'")

    if not self._workout_active:
        logger.warning("[READY] No workout active")
        return "No workout in progress."

    ex = self._workout_current_exercise
    logger.info(f"[READY] Current exercise: {ex}")

    if not ex:
        logger.warning("[READY] No current exercise")
        return "No current exercise."

    # Log all exercise fields
    logger.info(f"[READY] Exercise fields: reps={ex.get('reps')}, duration={ex.get('duration_seconds')}, per_side={ex.get('per_side')}")
    logger.info(f"[READY] Current set={self._workout_current_set}, weight={self._workout_current_weight}")

    # ... rest of function with more logging at each decision point
```

**Test and capture logs:**
1. Start workout
2. Say "Ready"
3. Check logs to see exactly which code path executed

---

### Phase 1: Fix Based on Diagnostic

**Only after Phase 0 confirms the bug location.**

If diagnostic shows `duration_seconds` is missing → fix `_setup_next_exercise()`
If diagnostic shows early return → fix code ordering
If diagnostic shows exception → fix error handling

---

### Phase 2: Single-Threaded Timer Polling (REVISED APPROACH)

**Original plan used background thread. This caused:**
- Race conditions
- Deadlock risk
- Two audio paths
- asyncio incompatibility

**Revised approach:** Check timers on every main loop iteration (100ms), no threading required.

#### 2.1 Modify Main Loop Structure

**Current (blocks until user speaks):**
```python
while True:
    self._wait_for_command()  # Blocks until PROCESS
    self._process()
```

**Revised (non-blocking poll + timer check):**
```python
while True:
    # Non-blocking check for command (100ms timeout)
    has_command = self._poll_for_command(timeout=0.1)

    # ALWAYS check timers, even without user input
    self._check_and_play_timers()

    # Process user input if available
    if has_command:
        self._process()
```

#### 2.2 Implement `_poll_for_command()`

```python
def _poll_for_command(self, timeout: float = 0.1) -> bool:
    """Non-blocking check for command file. Returns True if command ready."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if COMMAND_FILE.exists():
            cmd = COMMAND_FILE.read_text().strip()
            if cmd == "PROCESS":
                COMMAND_FILE.unlink()
                return True
        time.sleep(0.01)  # 10ms granularity
    return False
```

#### 2.3 Implement `_check_and_play_timers()`

```python
def _check_and_play_timers(self):
    """Check all active timers and play audio if needed. Single-threaded."""
    # Check workout exercise timer (timed holds)
    if self._workout_exercise_timer_active:
        msg, beeps = self._check_workout_exercise_timer()
        for bp in beeps:
            play_countdown_beep(bp)
        if msg:
            self._autonomous_speak(msg)

    # Check workout rest timer
    if self._workout_rest_active:
        msg, beeps = self._check_workout_rest_timer()
        for bp in beeps:
            play_countdown_beep(bp)
        if msg:
            self._autonomous_speak(msg)

    # Check routine timer
    if self._routine_active and self._routine_timer_active:
        msg, done = self._check_routine_timer()
        if msg:
            self._autonomous_speak(msg)
```

#### 2.4 Implement `_autonomous_speak()`

```python
def _autonomous_speak(self, text: str):
    """Speak text autonomously via file bridge (same as normal responses)."""
    logger.info(f"[TIMER] Autonomous speech: {text}")
    print(f"[TIMER SPEAK: {text}]", flush=True)

    # Use same TTS as normal responses
    result = self.tts.synthesize(text)

    # Write to same output file (Windows client plays it)
    result.audio.astype(np.float32).tofile(AUDIO_OUT_FILE)

    # Signal Windows to play
    STATUS_FILE.write_text("speaking")
```

**Benefits of single-threaded approach:**
- No race conditions
- No deadlock risk
- Uses same audio path as normal speech
- No asyncio conflicts
- Simpler debugging

---

### Phase 3: Update Timer Check Methods

The existing `_check_workout_exercise_timer()` and `_check_workout_rest_timer()` need updates:

#### 3.1 Exercise Timer - Handle Side Switches

Already implemented in v1, just ensure it works with single-threaded model.

#### 3.2 Rest Timer - Update State on Completion

```python
def _check_workout_rest_timer(self) -> tuple[str | None, list[int]]:
    """Check workout rest timer. Returns (message, beeps_to_play)."""
    if not self._workout_rest_active or not self._workout_rest_start:
        return None, []

    elapsed = time.monotonic() - self._workout_rest_start  # Use monotonic!
    remaining = self._workout_rest_duration - elapsed

    # Countdown beeps
    beep_points = [30, 15, 5]
    new_beeps = []
    for bp in beep_points:
        if remaining <= bp and bp not in self._workout_beeps_played:
            self._workout_beeps_played.add(bp)
            new_beeps.append(bp)

    # Rest complete
    if elapsed >= self._workout_rest_duration:
        self._workout_rest_active = False
        self._workout_exercise_pending = True
        next_set = self._workout_current_set + 1
        return f"Rest done. Set {next_set}. Say ready.", new_beeps

    return None, new_beeps
```

---

### Phase 4: Use `time.monotonic()` Instead of `time.time()`

**Problem identified:** `time.time()` can jump due to NTP corrections.

**Fix:** Replace all timer calculations:
```python
# Before
self._workout_rest_start = time.time()
elapsed = time.time() - self._workout_rest_start

# After
self._workout_rest_start = time.monotonic()
elapsed = time.monotonic() - self._workout_rest_start
```

---

### Phase 5: Testing

1. **Phase 0 diagnostic test:** Verify logs show correct code path
2. **Timer start test:** "Ready" returns "Set 1. Left side. 30 seconds. Begin."
3. **Auto-prompt test:** Wait 30 seconds, hear "Switch sides. Right leg. Begin."
4. **Rest timer test:** Countdown beeps at 30/15/5, then "Rest done. Set 2."
5. **Full workout test:** Complete all sets of balance exercise
6. **Mixed exercise test:** Balance exercise followed by rep-based exercise

---

## File Changes Summary

| File | Changes |
|------|---------|
| `atlas/voice/bridge_file_server.py` | Add logging, modify main loop, add `_poll_for_command()`, add `_autonomous_speak()` |

---

## Risk Mitigation

| Original Risk | Mitigation |
|---------------|------------|
| Race conditions | Single-threaded - eliminated |
| Deadlock | No locks needed - eliminated |
| Two audio paths | Same file bridge for all audio |
| Thread crashes | No threads - eliminated |
| asyncio conflicts | No threading - eliminated |

---

## Estimated Tasks (Revised)

1. **Phase 0 (Diagnostic):** Add logging, test, identify root cause - 20 min
2. **Phase 1 (Fix bug):** Based on diagnostic findings - 15 min
3. **Phase 2 (Single-threaded polling):** Modify main loop - 30 min
4. **Phase 3 (Timer methods):** Update state handling - 20 min
5. **Phase 4 (Monotonic clock):** Replace time.time() - 10 min
6. **Phase 5 (Testing):** End-to-end tests - 20 min

**Total:** ~2 hours (more realistic than v1)

---

## Success Criteria

1. Debug logs show exact code path on "Ready"
2. Timed exercises announce duration and side
3. Timer auto-prompts every 30 seconds without user input
4. Rest timer beeps and announces completion
5. Full workout completes smoothly
6. No audio glitches or overlap
