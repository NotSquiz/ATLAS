"""
Audio Utilities for Voice Pipeline

Provides chime generation and audio playback for timers.

Usage:
    from atlas.voice.audio_utils import generate_chime, play_audio

    # Generate a completion chime
    chime = generate_chime()
    play_audio(chime)

    # Custom chime (higher pitch, longer)
    high_chime = generate_chime(freq_hz=880, duration_s=0.3)
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Default audio settings (match Kokoro TTS output)
DEFAULT_SAMPLE_RATE = 24000


def generate_chime(
    freq_hz: int = 440,
    duration_s: float = 0.2,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    volume: float = 0.5,
) -> np.ndarray:
    """
    Generate a simple sine wave chime with exponential decay.

    Args:
        freq_hz: Frequency in Hz (440 = A4, 880 = A5)
        duration_s: Duration in seconds
        sample_rate: Sample rate (should match TTS output)
        volume: Volume multiplier (0.0 to 1.0)

    Returns:
        Audio data as float32 numpy array
    """
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), dtype=np.float32)

    # Sine wave with exponential decay envelope for pleasant fade-out
    envelope = np.exp(-t * 8, dtype=np.float32)
    wave = np.sin(2 * np.pi * freq_hz * t, dtype=np.float32)

    return (wave * envelope * volume).astype(np.float32)


def generate_double_chime(
    freq_hz: int = 440,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    volume: float = 0.4,
) -> np.ndarray:
    """
    Generate a double chime (two notes) for section completion.

    Returns:
        Audio data as float32 numpy array
    """
    # First note
    note1 = generate_chime(freq_hz, 0.15, sample_rate, volume)

    # Short silence
    silence = np.zeros(int(sample_rate * 0.05), dtype=np.float32)

    # Second note (fifth above)
    note2 = generate_chime(int(freq_hz * 1.5), 0.2, sample_rate, volume)

    return np.concatenate([note1, silence, note2])


def generate_completion_chime(sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Generate a pleasant three-note completion chime (major chord arpeggio).

    Returns:
        Audio data as float32 numpy array
    """
    # C-E-G arpeggio (major chord)
    c = generate_chime(523, 0.15, sample_rate, 0.4)  # C5
    silence = np.zeros(int(sample_rate * 0.05), dtype=np.float32)
    e = generate_chime(659, 0.15, sample_rate, 0.4)  # E5
    g = generate_chime(784, 0.25, sample_rate, 0.4)  # G5

    return np.concatenate([c, silence, e, silence, g])


# Pre-generated chimes for quick access
_CHIMES = {}


def get_chime(chime_type: str = "single", sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Get a pre-generated chime by type.

    Args:
        chime_type: "single", "double", or "completion"
        sample_rate: Sample rate

    Returns:
        Audio data as float32 numpy array
    """
    key = (chime_type, sample_rate)
    if key not in _CHIMES:
        if chime_type == "single":
            _CHIMES[key] = generate_chime(sample_rate=sample_rate)
        elif chime_type == "double":
            _CHIMES[key] = generate_double_chime(sample_rate=sample_rate)
        elif chime_type == "completion":
            _CHIMES[key] = generate_completion_chime(sample_rate=sample_rate)
        else:
            _CHIMES[key] = generate_chime(sample_rate=sample_rate)

    return _CHIMES[key]


def play_audio(
    audio: np.ndarray,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    blocking: bool = True,
) -> bool:
    """
    Play audio through the default output device.

    Args:
        audio: Audio data as numpy array
        sample_rate: Sample rate
        blocking: Wait for playback to complete

    Returns:
        True if playback started successfully
    """
    try:
        import sounddevice as sd
        sd.play(audio, sample_rate, blocking=blocking)
        return True
    except Exception as e:
        logger.warning(f"Audio playback failed: {e}")
        return False


def play_chime(chime_type: str = "single", blocking: bool = True) -> bool:
    """
    Play a chime sound.

    Args:
        chime_type: "single", "double", or "completion"
        blocking: Wait for playback to complete

    Returns:
        True if playback started successfully
    """
    chime = get_chime(chime_type)
    return play_audio(chime, blocking=blocking)


# Convenience functions
def generate_exercise_complete_chime(sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Generate ascending 3-note chime for exercise completion.

    Distinct warm sound: 440-550-660 Hz (minor pentatonic feel).
    Clearly different from timer_start (single 660Hz beep).
    """
    note1 = generate_chime(freq_hz=440, duration_s=0.12, sample_rate=sample_rate, volume=0.5)
    silence = np.zeros(int(sample_rate * 0.05), dtype=np.float32)
    note2 = generate_chime(freq_hz=550, duration_s=0.12, sample_rate=sample_rate, volume=0.5)
    note3 = generate_chime(freq_hz=660, duration_s=0.18, sample_rate=sample_rate, volume=0.5)
    return np.concatenate([note1, silence, note2, silence, note3])


def chime_exercise_complete():
    """Play warm ascending chime for exercise completion."""
    chime = generate_exercise_complete_chime()
    play_audio(chime, blocking=False)


def chime_section_complete():
    """Play chime for section completion."""
    play_chime("double")


def chime_routine_complete():
    """Play chime for full routine completion."""
    play_chime("completion")


def generate_side_switch_beep(sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Generate double beep for side switch (same frequency, quick succession).
    Distinct from section complete (which uses ascending notes).
    """
    beep1 = generate_chime(freq_hz=660, duration_s=0.1, sample_rate=sample_rate, volume=0.5)
    silence = np.zeros(int(sample_rate * 0.08), dtype=np.float32)
    beep2 = generate_chime(freq_hz=660, duration_s=0.1, sample_rate=sample_rate, volume=0.5)
    return np.concatenate([beep1, silence, beep2])


def generate_rest_done_beep(sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Generate triple ascending beep for rest done / ready for next set.
    """
    beep1 = generate_chime(freq_hz=440, duration_s=0.1, sample_rate=sample_rate, volume=0.5)
    silence = np.zeros(int(sample_rate * 0.06), dtype=np.float32)
    beep2 = generate_chime(freq_hz=550, duration_s=0.1, sample_rate=sample_rate, volume=0.5)
    beep3 = generate_chime(freq_hz=660, duration_s=0.15, sample_rate=sample_rate, volume=0.5)
    return np.concatenate([beep1, silence, beep2, silence, beep3])


def generate_workout_complete_fanfare(sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Generate triumphant fanfare for workout completion.
    Rising major chord with sustained final note.
    """
    # C-E-G-C (octave) arpeggio
    c4 = generate_chime(freq_hz=523, duration_s=0.12, sample_rate=sample_rate, volume=0.5)
    silence = np.zeros(int(sample_rate * 0.04), dtype=np.float32)
    e4 = generate_chime(freq_hz=659, duration_s=0.12, sample_rate=sample_rate, volume=0.5)
    g4 = generate_chime(freq_hz=784, duration_s=0.12, sample_rate=sample_rate, volume=0.5)
    c5 = generate_chime(freq_hz=1046, duration_s=0.4, sample_rate=sample_rate, volume=0.6)
    return np.concatenate([c4, silence, e4, silence, g4, silence, c5])


def generate_timer_start_beep(sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Generate single beep for timer start (go signal).
    """
    return generate_chime(freq_hz=660, duration_s=0.15, sample_rate=sample_rate, volume=0.5)


def chime_timer_start():
    """Play single beep to signal timer has started (go)."""
    beep = generate_timer_start_beep()
    play_audio(beep, blocking=False)


def chime_side_switch():
    """Play double beep for side switch during timed exercises."""
    beep = generate_side_switch_beep()
    play_audio(beep, blocking=False)


def chime_rest_done():
    """Play triple ascending beep when rest period ends."""
    beep = generate_rest_done_beep()
    play_audio(beep, blocking=False)


def chime_workout_complete():
    """Play fanfare when entire workout is completed."""
    fanfare = generate_workout_complete_fanfare()
    play_audio(fanfare, blocking=True)


# ============================================
# COUNTDOWN BEEPS FOR REST TIMERS
# ============================================

def generate_countdown_beep(
    seconds_remaining: int,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> np.ndarray:
    """
    Generate appropriate beep for countdown based on time remaining.

    Args:
        seconds_remaining: Seconds left in countdown (30, 15, 5 typical)
        sample_rate: Sample rate

    Returns:
        Audio data as float32 numpy array
    """
    if seconds_remaining <= 5:
        # Urgent - higher pitch, louder
        return generate_chime(freq_hz=880, duration_s=0.15, sample_rate=sample_rate, volume=0.6)
    elif seconds_remaining <= 15:
        # Warning - medium pitch
        return generate_chime(freq_hz=660, duration_s=0.12, sample_rate=sample_rate, volume=0.5)
    elif seconds_remaining <= 30:
        # Alert - lower pitch
        return generate_chime(freq_hz=550, duration_s=0.1, sample_rate=sample_rate, volume=0.4)
    else:
        # Default single beep
        return generate_chime(sample_rate=sample_rate)


def play_countdown_beep(seconds_remaining: int, blocking: bool = False) -> bool:
    """
    Play countdown beep for given time remaining.

    Args:
        seconds_remaining: Seconds left (determines tone)
        blocking: Wait for playback to complete

    Returns:
        True if playback started successfully
    """
    beep = generate_countdown_beep(seconds_remaining)
    return play_audio(beep, blocking=blocking)


def get_countdown_beep(seconds_remaining: int, sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """
    Get countdown beep audio data (for concatenating with TTS).

    Args:
        seconds_remaining: Seconds left (determines tone)
        sample_rate: Sample rate (should match TTS)

    Returns:
        Audio data as float32 numpy array
    """
    return generate_countdown_beep(seconds_remaining, sample_rate)


if __name__ == "__main__":
    # Test chimes
    print("Testing single chime...")
    play_chime("single")

    import time
    time.sleep(0.5)

    print("Testing double chime...")
    play_chime("double")

    time.sleep(0.5)

    print("Testing completion chime...")
    play_chime("completion")

    print("Done!")
