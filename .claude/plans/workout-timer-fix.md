# ATLAS Workout Timer Fix - Implementation Plan

## Problem Summary

The workout timer system has two critical issues:

### Issue 1: Timer Never Starts (Bug)
When user says "Ready" for a timed exercise (Single-leg Balance), response is "Set 1. Begin." instead of "Set 1. Left side. 30 seconds. Begin."

**Root Cause:** In `_handle_workout_ready()`, the progression recommendation block (lines 1400-1410) checks `if ex.get('reps')` and returns early asking for weight. But timed exercises have `reps=None`, so this shouldn't trigger. However, there's a second path at line 1411 that runs `if self._workout_current_set == 0` which tries to get progression recommendations for ALL exercises on the first set, returning before the timed exercise check can run.

**Fix:** Reorder code to check for timed exercises FIRST, before any progression logic.

### Issue 2: No Autonomous Timer Prompts (Architecture)
Current system is event-driven - timers only checked when user speaks. If user is silent during a 30-second balance hold, no prompts fire.

**Root Cause:** Main loop waits for user input before checking timers.

**Fix:** Add background thread that checks timers every 500ms and plays audio/speech autonomously.

---

## Implementation Plan

### Phase 1: Fix Timer Start Logic (Quick Fix)

**File:** `atlas/voice/bridge_file_server.py`

**Location:** `_handle_workout_ready()` around line 1400

**Current Code Flow:**
```
1. Check if exercise has reps AND no weight set
2. If first set, get progression recommendation (RETURNS EARLY)
3. Increment set counter
4. Check if timed exercise → start timer (NEVER REACHED)
5. Return "Set X. Begin."
```

**Fixed Code Flow:**
```
1. Increment set counter
2. Check if timed exercise (has duration_seconds)
   → If yes: start timer, return "Set X. Left side. 30 seconds. Begin."
3. Check if exercise has reps AND no weight set
   → If first set and no weight, get progression recommendation
4. Return "Set X. Begin."
```

**Tasks:**
- [ ] Move `self._workout_current_set += 1` to top of function (after active checks)
- [ ] Move timed exercise check block BEFORE rep/weight checks
- [ ] Test that "Ready" now starts timer for balance exercise

### Phase 2: Add Background Timer Thread

**File:** `atlas/voice/bridge_file_server.py`

#### 2.1 Add Thread Infrastructure

**Location:** `__init__` after line 612

**Add:**
```python
import threading

# Thread synchronization for autonomous timers
self._timer_lock = threading.RLock()
self._timer_thread: threading.Thread | None = None
self._timer_thread_stop = threading.Event()
self._tts_lock = threading.Lock()  # Protect TTS calls
```

#### 2.2 Add Thread Start/Stop Methods

**Add new methods:**
```python
def _start_timer_thread(self):
    """Start background thread for autonomous timer checking."""

def _stop_timer_thread(self):
    """Stop background timer thread gracefully."""
```

#### 2.3 Add Timer Loop Method

**Add new method:**
```python
def _timer_thread_loop(self):
    """Background loop checking timers every 500ms."""
    # Check workout rest timer
    # Check workout exercise timer (timed holds)
    # Check routine timer
    # Play beeps/chimes immediately via sounddevice
    # Speak prompts via autonomous TTS
```

#### 2.4 Add Autonomous Speech Method

**Add new method:**
```python
def _speak_autonomous(self, text: str):
    """Speak text autonomously from timer thread."""
    # Synthesize with TTS (locked)
    # Play via sounddevice directly (not file bridge)
```

#### 2.5 Start Thread in run()

**Location:** `run()` method, after `self.setup()`

**Add:**
```python
self._start_timer_thread()
```

**Add to shutdown:**
```python
self._stop_timer_thread()
```

### Phase 3: Add Lock Protection

**Wrap timer state mutations with `self._timer_lock`:**

| Method | State Variables |
|--------|-----------------|
| `_handle_workout_ready()` | `_workout_exercise_timer_*`, `_workout_rest_*` |
| `_handle_workout_set_done()` | `_workout_rest_*`, `_workout_set_active` |
| `_check_workout_rest_timer()` | All rest timer vars |
| `_check_workout_exercise_timer()` | All exercise timer vars |
| `_start_interactive_workout()` | All workout state init |
| `_handle_workout_stop()` | All workout state cleanup |

### Phase 4: Testing

- [ ] Test "start workout" → "ready" starts timer with "Left side. 30 seconds."
- [ ] Test timer auto-prompts "Switch sides" after 30 seconds (no user input)
- [ ] Test timer auto-prompts "Set complete. Rest 60 seconds." after both sides
- [ ] Test rest timer countdown beeps at 30s, 15s, 5s
- [ ] Test rest timer auto-prompts "Rest done. Set 2. Say ready."
- [ ] Test "stop workout" cleanly stops all timers and thread
- [ ] Test rep-based exercises still work (Goblet Squat asks for weight)

---

## File Changes Summary

| File | Changes |
|------|---------|
| `atlas/voice/bridge_file_server.py` | Reorder `_handle_workout_ready()`, add timer thread, add locks |
| `atlas/voice/audio_utils.py` | No changes (already supports non-blocking playback) |

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Thread race conditions | Use RLock for all timer state, extensive testing |
| TTS conflicts (main vs timer thread) | Use separate lock for TTS, timer uses sounddevice directly |
| Audio playback overlap | Timer thread uses non-blocking sounddevice, brief prompts |
| Thread not stopping on shutdown | Use daemon=True, explicit stop signal, join with timeout |

---

## Estimated Tasks

1. **Phase 1 (Quick Fix):** Reorder `_handle_workout_ready()` - 15 min
2. **Phase 2.1-2.2 (Thread Infra):** Add thread setup - 10 min
3. **Phase 2.3 (Timer Loop):** Implement autonomous checks - 30 min
4. **Phase 2.4 (Auto Speech):** Add sounddevice TTS - 15 min
5. **Phase 2.5 (Integration):** Wire up thread start/stop - 5 min
6. **Phase 3 (Locks):** Add lock protection - 20 min
7. **Phase 4 (Testing):** End-to-end testing - 15 min

**Total:** ~2 hours

---

## Success Criteria

1. User says "Ready" → Timer starts with "Left side. 30 seconds. Begin."
2. After 30 seconds (no user input) → Chime + "Switch sides. Right leg. Begin."
3. After 30 more seconds → Chime + "Set 1 complete. Rest 60 seconds."
4. Countdown beeps play at 30s, 15s, 5s during rest
5. After rest → "Rest done. Set 2. Say ready."
6. Full workout completes with minimal user prompts
7. No crashes, race conditions, or audio glitches
