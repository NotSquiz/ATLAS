from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel
import sounddevice as sd
import soundfile as sf
import time

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"

print("Loading CustomVoice model...")
model = Qwen3TTSModel.from_pretrained(MODEL_ID)

speakers = model.get_supported_speakers()
print(f"\nAvailable speakers: {speakers}")

TEST_TEXT = "Good morning sir. Your status is green. Full intensity today. The gains happen in recovery."

print("\n" + "="*50)
print("VOICE AUDITION - Listen to all speakers")
print("="*50)

for speaker in speakers:
    print(f"\n--- {speaker.upper()} ---")
    audio, sr = model.generate_custom_voice(
        text=TEST_TEXT,
        speaker=speaker,
        language="english"
    )
    sf.write(f"/tmp/voice_{speaker}.wav", audio[0], sr)
    print(f"Playing {speaker}...")
    sd.play(audio[0], sr)
    sd.wait()
    time.sleep(0.5)  # Brief pause between voices

print("\n" + "="*50)
print("All voices saved to /tmp/voice_*.wav")
print("Which voice did you prefer?")
