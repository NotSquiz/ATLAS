# Command Centre UX Fixes - Implementation Plan

**Status**: Ready for implementation
**Created**: 2026-01-20
**Files to modify**:
- `atlas/voice/audio_utils.py` - New exercise complete chime
- `atlas/voice/bridge_file_server.py` - Timer data, transition logic
- `scripts/atlas_launcher.py` - UI polling, button states

---

## Quick Reference - Key Line Numbers

| File | Function | Line | Issue |
|------|----------|------|-------|
| `bridge_file_server.py` | `_check_routine_auto_advance()` | ~3290 | Race condition - calls advance during TTS |
| `bridge_file_server.py` | `_get_timer_status()` | ~830 | Missing `is_paused` field |
| `bridge_file_server.py` | `_get_timer_status()` transition | ~870 | Uses wrong exercise name during transition |
| `atlas_launcher.py` | `_poll_status()` | ~636 | 500ms polling (too slow) |
| `atlas_launcher.py` | `_on_pause_click()` | ~467 | No visual feedback |
| `audio_utils.py` | `chime_exercise_complete()` | ~164 | Uses single 440Hz (same as timer start pattern) |

---

## Issues Identified

### 1. UI Text Lagging Behind (CRITICAL)
**Root Cause**: Race condition in auto-advance state machine
- `_advance_routine_exercise_silent()` updates `_routine_current_exercise` IMMEDIATELY after TTS starts
- UI reads new state while old announcement is still playing
- Exercise index and name don't match during transition

**Location**: `bridge_file_server.py:3292-3296`

**Fix**: Delay state update until AFTER the positioning phase (4 seconds)
- Keep next exercise info in `_routine_next_exercise_msg` during transition
- Only update `_routine_current_exercise` when timer actually starts
- Add explicit "next_exercise_name" field to timer_data during transition

### 2. Pause Button No Visual Feedback (CRITICAL)
**Root Cause**:
- `timer_data` doesn't include `is_paused` field
- UI has no state tracking for paused
- Button color doesn't change when clicked

**Locations**:
- `bridge_file_server.py:804-845` (_get_timer_status)
- `atlas_launcher.py:239-274` (button definitions)
- `atlas_launcher.py:467-477` (click handlers)

**Fix**:
1. Add `is_paused` to timer_data from server
2. Track pause state in UI
3. Change PAUSE button to green + "RESUME" text when paused
4. Add click feedback (brief highlight)

### 3. Exercise Complete / Timer Start Sound Same (MEDIUM)
**Root Cause**: Both use single sine waves with exponential decay
- Exercise complete: 440Hz, 0.2s
- Timer start: 660Hz, 0.15s
- Too similar in pattern

**Location**: `audio_utils.py:164-226`

**Fix**:
- Exercise complete: Ascending 3-note (440-550-660Hz), warm and satisfying
- Timer start: Keep brief but make more distinct (staccato double beep)

### 4. UI Polling Too Slow (MEDIUM)
**Root Cause**: 500ms polling interval vs 100ms server updates
- Creates 4-5x lag between state change and UI update
- Timer appears "jumpy"

**Location**: `atlas_launcher.py:636`

**Fix**: Reduce to 100ms polling to match server cadence

### 5. Button Interactions Need Verification (LOW)
- SKIP should work during auto-advance
- STOP should cancel everything immediately
- Need click feedback on all buttons

---

## Implementation Order

### Phase A: Fix Audio Chimes (Quick Win - 15 min)
1. Create new `generate_exercise_complete_chime()` - ascending 3-note
2. Keep timer start as brief staccato
3. Test distinctiveness

### Phase B: Fix Timer Status Data (20 min)
1. Add `is_paused` to `_get_timer_status()`
2. Add `next_exercise_name` for transition phase
3. Fix countdown calculation during phase change

### Phase C: Fix UI State Management (30 min)
1. Reduce polling to 100ms
2. Add pause state tracking
3. PAUSE button visual state (green + "RESUME" when paused)
4. Add click feedback animation

### Phase D: Fix Transition Logic (30 min)
1. Delay state update until timer actually starts
2. Keep current exercise info during transition
3. Only increment indices when timer starts
4. Update UI to use `next_exercise_name` during transition mode

### Phase E: Verification (15 min)
1. Test full routine flow
2. Verify PAUSE/RESUME cycle
3. Verify SKIP works at all states
4. Verify STOP cancels everything
5. Verify audio distinctiveness

---

## Detailed Changes

### audio_utils.py Changes
```python
def generate_exercise_complete_chime(sample_rate=24000):
    """Ascending 3-note warm chime for exercise completion."""
    # 440-550-660 Hz ascending (minor pentatonic feel)
    note1 = generate_chime(440, 0.12, sample_rate, 0.5)
    silence = np.zeros(int(sample_rate * 0.05), dtype=np.float32)
    note2 = generate_chime(550, 0.12, sample_rate, 0.5)
    note3 = generate_chime(660, 0.18, sample_rate, 0.5)  # Extend final note
    return np.concatenate([note1, silence, note2, silence, note3])

def chime_exercise_complete():
    """Play warm ascending chime for exercise completion."""
    chime = generate_exercise_complete_chime()
    play_audio(chime, blocking=False)
```

### bridge_file_server.py Changes

1. **_get_timer_status()** - Add is_paused and fix transition:
```python
return {
    "active": True,
    "mode": "routine",
    "is_paused": self._routine_paused,  # ADD THIS
    "exercise_name": ex.get('name', 'Exercise'),
    ...
}
```

2. **Transition mode** - Use stored next exercise name:
```python
if self._routine_auto_advance_pending:
    return {
        "mode": "routine_transition",
        "exercise_name": self._routine_next_exercise_name or 'Next Exercise',  # From stored state
        "next_exercise_setup": self._routine_next_exercise_msg,  # Full setup tip
        ...
    }
```

3. **_check_routine_auto_advance()** - Delay state update:
```python
elif self._routine_auto_advance_phase == 'announcing':
    if elapsed >= 4.0:
        # NOW update state (not during announcement)
        asyncio.run(self._advance_routine_exercise_silent())
        self._auto_start_routine_timer()
```

### atlas_launcher.py Changes

1. **Polling frequency**:
```python
self.after(100, self._poll_status)  # Was 500
```

2. **Button state management**:
```python
def _update_button_states(self, timer_data):
    is_paused = timer_data.get("is_paused", False)
    if is_paused:
        self.pause_btn.configure(
            fg_color=COLORS["success"],
            text="▶ RESUME"
        )
    else:
        self.pause_btn.configure(
            fg_color=COLORS["card"],
            text="⏸ PAUSE"
        )
```

3. **Click feedback**:
```python
def _on_pause_click(self):
    self.pause_btn.configure(fg_color=COLORS["warning"])
    self.after(150, lambda: self.pause_btn.configure(fg_color=COLORS["card"]))
    self._send_command("PAUSE_ROUTINE")
```

---

## Verification Checklist
- [ ] Exercise complete chime is distinct from timer start
- [ ] PAUSE button turns green and shows "RESUME" when paused
- [ ] Timer display updates smoothly (no 2-3 second jumps)
- [ ] Exercise name matches what's being announced
- [ ] SKIP works during transition
- [ ] STOP cancels everything immediately
- [ ] Countdown doesn't jump from 2s back to 4s
