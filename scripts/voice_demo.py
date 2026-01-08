#!/usr/bin/env python3
"""Demo all Kokoro voices for selection."""

import sys
import time
import numpy as np

# Add parent to path
sys.path.insert(0, "/home/squiz/ATLAS")

from atlas.voice.tts import KokoroTTS

VOICES = [
    ("af_bella", "American Female - Bella"),
    ("af_nicole", "American Female - Nicole"),
    ("af_sarah", "American Female - Sarah"),
    ("af_sky", "American Female - Sky"),
    ("am_adam", "American Male - Adam"),
    ("am_michael", "American Male - Michael"),
    ("bf_emma", "British Female - Emma"),
    ("bf_isabella", "British Female - Isabella"),
    ("bm_george", "British Male - George"),
    ("bm_lewis", "British Male - Lewis"),
]

DEMO_TEXT = "Hello, I am ATLAS, your personal assistant. How may I help you today?"

def save_wav(audio: np.ndarray, sample_rate: int, path: str):
    """Save audio to WAV file."""
    import wave
    import struct

    # Normalize and convert to 16-bit PCM
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)

    with wave.open(path, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_int16.tobytes())

def main():
    print("=" * 60)
    print("ATLAS Voice Demo - All 10 Kokoro Voices")
    print("=" * 60)
    print(f"\nDemo text: \"{DEMO_TEXT}\"\n")

    tts = KokoroTTS()

    for i, (voice_id, voice_name) in enumerate(VOICES, 1):
        print(f"\n[{i}/10] {voice_name}")
        print(f"       Voice ID: {voice_id}")
        print("       Synthesizing...", end=" ", flush=True)

        start = time.perf_counter()
        result = tts.synthesize(DEMO_TEXT, voice=voice_id)
        elapsed = (time.perf_counter() - start) * 1000

        print(f"done ({elapsed:.0f}ms)")

        # Save to file for Windows playback
        output_path = f"/home/squiz/ATLAS/.bridge/voice_{i:02d}_{voice_id}.wav"
        save_wav(result.audio, result.sample_rate, output_path)
        print(f"       Saved: {output_path}")

        # Also save metadata
        with open("/home/squiz/ATLAS/.bridge/current_voice.txt", "w") as f:
            f.write(f"{i}|{voice_id}|{voice_name}")

    print("\n" + "=" * 60)
    print("All voices saved to ~/.bridge/voice_XX_*.wav")
    print("=" * 60)
    print("\nTo play on Windows, run:")
    print('  cd \\\\wsl$\\Ubuntu\\home\\squiz\\ATLAS\\.bridge')
    print('  for %f in (voice_*.wav) do start /wait "" "%f"')
    print("\nOr play individually:")
    for i, (voice_id, voice_name) in enumerate(VOICES, 1):
        print(f'  {i:2d}. start voice_{i:02d}_{voice_id}.wav  # {voice_name}')

if __name__ == "__main__":
    main()
