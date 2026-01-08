# ATLAS Voice Bridge - Complete Handover

**Date:** January 6, 2026
**Status:** Partially Working, Performance Issues Identified
**Priority:** Complete CUDA setup, then optimize

---

## What We Built This Session

### 1. Windows-WSL2 Audio Bridge (File-Based)

Two-component system that bypasses WSL2 networking issues:

**WSL2 Server:** `atlas/voice/bridge_file_server.py`
- Receives audio via file (`~/.bridge/audio_in.raw`)
- Runs STT → Router → LLM → TTS pipeline
- Returns audio via file (`~/.bridge/audio_out.raw`)
- Writes sample rate metadata for correct playback

**Windows Client:** `scripts/audio_bridge_windows_file.py`
- Captures audio from Windows microphone
- Sends to WSL2 via `\\wsl$\Ubuntu\...` path
- Plays TTS response at correct sample rate (24kHz)

### 2. Socket-Based Bridge (Not Working)

Files exist but WSL2 networking blocks connections:
- `atlas/voice/bridge_server.py` (socket server)
- `scripts/audio_bridge_windows.py` (socket client)

**Root Cause:** Hyper-V firewall blocks inbound connections even with `networkingMode=mirrored`.

**Fix (not yet applied):**
```powershell
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
```

---

## Current Performance (Unacceptable)

| Component | Time | Expected | Issue |
|-----------|------|----------|-------|
| STT (faster-whisper) | 7.8s | ~0.5s | Model loads on first request |
| TTS (Kokoro) | 14.3s | ~1.5s | Running on CPU (no CUDA) |
| LLM Response | Too long | 1-3 sentences | System prompt not enforced |
| **Total** | ~25s | ~3s | **8x slower than target** |

---

## Root Causes Identified

### 1. TTS Running on CPU (CUDA Not Configured)

**Problem:** onnxruntime-gpu installed but CUDA Toolkit missing
```
libcublasLt.so.12: cannot open shared object file
```

**Partial Fix Started:**
```bash
# These were run:
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install cuda-toolkit-12-6  # This needs to run

# cudnn package name was wrong, try:
sudo apt-get install libcudnn9-cuda-12
```

**To enable GPU in TTS:**
```bash
export ONNX_PROVIDER=CUDAExecutionProvider
```

### 2. STT Model Loading Overhead

**Problem:** First request takes ~8s (model load + transcription)
**Solution:** Preload models at server startup

In `bridge_file_server.py`, models load lazily. Add explicit preload:
```python
def __init__(self):
    # Force model loading at startup
    self.stt._ensure_loaded()
    self.tts._ensure_loaded()
```

### 3. Transcription Cutting Off Words

**Observation:** User reported beginning of messages cut off
**Possible Causes:**
1. VAD speech_pad_ms too low (currently 100ms)
2. Recording starts late after Enter pressed
3. Audio chunk boundaries

**Do NOT switch to tiny.en yet** - it may make this worse.

### 4. LLM Responses Too Long

**Problem:** Haiku giving generic, long responses instead of ATLAS persona
**Root Cause:** System prompt not being passed correctly to API

**Fixed in:** `atlas/llm/api.py`
```python
# Now only includes system if present
if system_content:
    kwargs["system"] = system_content
```

**Still Needed:** Verify system prompt is being passed through router

---

## Files Modified This Session

| File | Change |
|------|--------|
| `atlas/voice/bridge_file_server.py` | Created - file-based WSL2 server |
| `scripts/audio_bridge_windows_file.py` | Created - Windows audio client |
| `atlas/voice/bridge_server.py` | Created - socket server (blocked by firewall) |
| `scripts/audio_bridge_windows.py` | Created - socket client |
| `atlas/llm/api.py` | Fixed system prompt handling |
| `atlas/voice/vad.py` | Fixed numpy→tensor conversion |
| `atlas/voice/pipeline.py` | Changed chunk size 30ms→64ms |

---

## To Complete CUDA Setup

```bash
# 1. Install CUDA Toolkit (if not done)
sudo apt-get install cuda-toolkit-12-6

# 2. Install cuDNN (correct package name)
sudo apt-get install libcudnn9-cuda-12

# 3. Set environment variables
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 4. Verify
nvcc --version
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
# Should show: CUDAExecutionProvider
```

---

## To Test After CUDA Setup

```bash
# WSL2 - Start server with GPU
cd /home/squiz/ATLAS && source venv/bin/activate
export ONNX_PROVIDER=CUDAExecutionProvider
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python -m atlas.voice.bridge_file_server
```

```powershell
# Windows - Run client
python \\wsl$\Ubuntu\home\squiz\ATLAS\scripts\audio_bridge_windows_file.py
```

**Expected Performance After GPU:**
- TTS: 14s → ~1.5s (10x improvement)
- Total: ~25s → ~5s

---

## Architecture Decisions Made

### Why File-Based Bridge Instead of Sockets?

WSL2 `networkingMode=mirrored` with `firewall=true` blocks inbound connections from Windows. The Hyper-V firewall needs configuration.

File-based works immediately because `\\wsl$\` path is always accessible.

### Why faster-whisper Instead of Moonshine?

Moonshine package API changed - `load_model` no longer exists. Faster-whisper is already installed and works.

### Why Not Use Native WSL2 Audio (WSLg)?

WSLg PulseAudio is unreliable for real-time recording. Timeouts and "paTimedOut" errors are common. The Windows-side capture with file transfer is more reliable.

---

## Outstanding Issues

1. **CUDA not fully configured** - TTS still on CPU
2. **First-request lag** - Models load lazily
3. **Transcription cutoff** - May need VAD tuning
4. **Socket bridge blocked** - Hyper-V firewall not configured
5. **Response length** - Need to verify system prompt flows through

---

## Quick Test Commands

```bash
# Test router classification
ANTHROPIC_API_KEY="$(cat .env | tr -d '\n')" python -c "
from atlas.llm import get_router
r = get_router()
for q in ['stop', 'what time is it', 'plan my workout']:
    d = r.classify(q)
    print(f'{d.tier.value:10} <- {q}')
"

# Test TTS speed
python -c "
import time
from atlas.voice.tts import get_tts
tts = get_tts()
start = time.perf_counter()
r = tts.synthesize('Test sentence.')
print(f'TTS: {(time.perf_counter()-start)*1000:.0f}ms for {r.audio_duration_s:.1f}s audio')
"

# Check GPU providers
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

---

## Next Steps Priority

1. **Complete CUDA installation** - Biggest performance win
2. **Add model preloading** - Eliminate first-request lag
3. **Test with GPU** - Verify 10x TTS improvement
4. **Investigate transcription cutoff** - May need to increase speech_pad_ms
5. **Configure Hyper-V firewall** - Enable socket bridge (optional, file-based works)

---

## Key Learnings

1. **WSL2 networking is fragile** - Hyper-V firewall blocks by default
2. **onnxruntime vs onnxruntime-gpu** - Must install GPU version AND CUDA Toolkit
3. **kokoro-onnx GPU detection is broken** - Use `ONNX_PROVIDER` env var
4. **16GB RAM is sufficient** - Bottleneck is GPU compute, not RAM
5. **File-based IPC works reliably** - When network fails, files don't
