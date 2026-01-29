# Command Centre UX Fixes - Round 3

**Status**: Ready for implementation
**Created**: 2026-01-20

---

## Issues Identified from Testing

### 1. READY Screen - PAUSE Button Should Be START (UX)
**Current**: On "READY?" screen, PAUSE button shows normal PAUSE state
**Expected**: Button should show "▶ START" or "▶ GO" so user can click to start timer
**User request**: "I should be able to press the [PAUSE] button - it should say [READY] or something"

**Fix locations**:
- `scripts/atlas_launcher.py` - `_update_button_states()` needs to check for `pending_ready` flag
- `scripts/atlas_launcher.py` - `_on_pause_click()` needs to send START_TIMER command when pending
- `atlas/voice/bridge_file_server.py` - Add START_TIMER command handler

### 2. Button State Not Resetting After SKIP
**Current**: After pressing SKIP, button stays yellow "RESUME"
**Expected**: Button should reset to normal "PAUSE" state
**Root cause**: `is_paused` state not being properly read from timer_data, or UI not updating

**Fix locations**:
- `scripts/atlas_launcher.py` - `_update_button_states()` - ensure it reads from timer_data on every update
- Check that `routine_pending` mode returns `is_paused: False` (already does)

### 3. STOP Button Not Working
**Current**: Pressing STOP button does nothing
**Expected**: Should stop the routine completely

**Debug needed**:
- Check if STOP_ROUTINE command is being written to command.txt
- Check if server is reading the command
- Check if handler is executing

**Fix locations**:
- `atlas/voice/bridge_file_server.py` - STOP_ROUTINE handler (line ~4752)
- Check guard conditions

### 4. Voice "STOP" Command Skips Instead of Stops
**Current**: Saying "stop" skips to next exercise instead of stopping routine
**Expected**: Should stop the entire routine

**Root cause**: Likely the stop command is matching skip patterns, or wrong handler called

**Fix locations**:
- `atlas/voice/bridge_file_server.py` - Check `_is_routine_stop_command()` patterns
- Check order of pattern matching in voice intent handler
- Ensure stop has priority over skip

### 5. Timer Visual Disappears After STOP
**Current**: After stop command, timer visual disappears
**Expected**: Should show neutral state or "Routine Stopped" message

**Root cause**: `_get_timer_status()` returns None when routine is stopped

**Fix locations**:
- Could add a "routine_stopped" mode temporarily
- Or just ensure clean transition to no-timer state

---

## Implementation Order

### Phase 1: Fix STOP Issues (Critical)
1. Debug STOP button - add logging to see if command received
2. Fix voice STOP command - check pattern matching order
3. Ensure `_handle_routine_stop()` is called correctly

### Phase 2: Fix Button States
1. Reset button to PAUSE after SKIP (check `is_paused` handling)
2. Make PAUSE button show START on READY screen
3. Add START_TIMER command for clicking START on pending screen

### Phase 3: Verification
1. Test PAUSE/RESUME cycle
2. Test SKIP resets button state
3. Test STOP button works
4. Test voice STOP stops routine
5. Test START button on READY screen

---

## Key Files

| File | Changes Needed |
|------|----------------|
| `atlas/voice/bridge_file_server.py` | Fix STOP handler, add START_TIMER command |
| `scripts/atlas_launcher.py` | Fix button states, add START logic |

---

## Key Line Numbers (approximate)

| Location | Purpose |
|----------|---------|
| `bridge_file_server.py:4752` | STOP_ROUTINE command handler |
| `bridge_file_server.py:~4260` | Voice stop intent handling |
| `bridge_file_server.py:320` | ROUTINE_STOP_PATTERNS |
| `atlas_launcher.py:471` | _on_pause_click() |
| `atlas_launcher.py:490` | _update_button_states() |
