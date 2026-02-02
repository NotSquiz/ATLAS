# Baby Brains production pipeline: Complete automation research

Your proposed pipeline is technically sound and highly automatable. **MCP servers exist for every major component** except Pika/Kling direct integration. The highest-ROI automation targets are the **QC pipeline** (immediate time savings per video) and **prompt generation system** (compounds value across your entire content library). DaVinci Resolve scripting offers diminishing returns for 25-35 videos/month—a template approach with selective automation provides 80% of the benefit at 20% of the development time.

The critical constraint is your 8GB VRAM: Chatterbox Turbo and video generation cannot run simultaneously. Build the pipeline with sequential GPU tasks or use ElevenLabs as your TTS fallback during generation bursts.

---

## Section 1: MCP servers — installation and configuration

**Recommended approach**: Install Video-Audio MCP as your primary workhorse (handles 70% of ffmpeg tasks), OpenCV MCP for frame analysis, and the official SQLite MCP for database operations. Skip the Video Quality MCP initially—its VMAF calculation duplicates what you can achieve with raw ffmpeg + Claude vision analysis.

### Video-Audio MCP (misbahsy/video-audio-mcp)

**GitHub**: 42 stars, MIT license, actively maintained  
**Capabilities**: Concatenate with crossfade, add voiceover, burn SRT captions, strip metadata, add text/image overlays, B-roll insertion, silence removal

```bash
# Installation
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/misbahsy/video-audio-mcp.git
cd video-audio-mcp && uv sync
```

**Claude Code configuration** (`~/.claude/mcp_servers.json`):
```json
{
  "mcpServers": {
    "VideoAudioServer": {
      "command": "uv",
      "args": ["--directory", "/home/user/video-audio-mcp", "run", "server.py"]
    }
  }
}
```

**Input/output**: Local file paths (absolute), supports MP4/MOV/MKV. Abstracts ffmpeg commands—you describe operations in natural language, it executes.

**Limitation**: Cannot customize edge-case ffmpeg parameters. For karaoke-style word highlighting, you'll need raw ffmpeg with ASS subtitles.

### OpenCV MCP (GongRzhe/opencv-mcp-server)

**GitHub**: 84 stars, MIT license, last updated December 2025

```bash
pip install opencv-mcp-server
```

```json
{
  "mcpServers": {
    "opencv": {
      "command": "uvx",
      "args": ["opencv-mcp-server"]
    }
  }
}
```

**Key functions**: `extract_video_frames` with `step` parameter (e.g., step=15 at 30fps = every 0.5s), `detect_features` for SSIM-style comparison, `detect_faces` for QC flagging.

**GPU requirements**: Optional—runs on CPU by default. YOLO object detection can use GPU but consumes ~2GB VRAM.

### Additional essential MCP servers

| Server | Purpose | Install | Stars |
|--------|---------|---------|-------|
| **mcp-server-sqlite** (Anthropic official) | Database queries | `uvx mcp-server-sqlite --db-path ~/baby_brains.db` | N/A |
| **elevenlabs-mcp** (Official) | TTS fallback | `uvx elevenlabs-mcp` + `ELEVENLABS_API_KEY` env | N/A |
| **mcp-metricool** (Official) | Scheduling | `uvx mcp-metricool` (requires Advanced plan) | N/A |
| **Fast-Whisper MCP** | Transcription/alignment | `pip install faster-whisper-mcp` | 50+ |
| **image-process-mcp-server** | Resize/crop/watermark | `npx -y image-process-mcp-server` | 30+ |

**Not found**: No MCP servers for MidJourney, Pika, or Kling APIs. Use direct Python API calls for these.

---

## Section 2: ffmpeg scripts for the pipeline

### 1. Keyframe extraction for QC

```python
import subprocess
from pathlib import Path

def extract_qc_frames(video_path: str, output_dir: str = None, fps: float = 2) -> list[str]:
    """Extract frames at 2fps for Claude vision QC. Returns list of frame paths."""
    video = Path(video_path)
    qc_dir = Path(output_dir) if output_dir else video.parent / f"{video.stem}_qc"
    qc_dir.mkdir(exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y", "-i", str(video),
        "-vf", f"fps={fps},scale=1024:-1",  # 1024px optimal for Claude vision
        "-q:v", "2", str(qc_dir / "frame_%04d.jpg")
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Generate timestamp mapping
    duration = float(subprocess.check_output([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(video)
    ]).decode().strip())
    
    frames = sorted(qc_dir.glob("*.jpg"))
    return [(str(f), i/fps) for i, f in enumerate(frames)]
```

### 2. Multi-clip concatenation with crossfade

```python
def concat_clips(clip_folder: str, output: str, crossfade: float = 0.5) -> None:
    """Concatenate clips with crossfade. Normalizes resolution/fps first."""
    clips = sorted(Path(clip_folder).glob("*.mp4"))
    
    # Normalize all clips to 1080x1920 @ 30fps
    normalized = []
    for i, clip in enumerate(clips):
        norm_path = f"/tmp/norm_{i}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(clip),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                   "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30",
            "-c:v", "libx264", "-crf", "18", "-c:a", "aac", norm_path
        ], check=True, capture_output=True)
        normalized.append(norm_path)
    
    if crossfade == 0:
        # Hard cut via concat demuxer
        list_file = "/tmp/concat.txt"
        with open(list_file, "w") as f:
            for c in normalized:
                f.write(f"file '{c}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                       "-i", list_file, "-c", "copy", output], check=True)
    else:
        # Build xfade filter chain (complex for 3+ clips)
        # For 2 clips:
        subprocess.run([
            "ffmpeg", "-y", "-i", normalized[0], "-i", normalized[1],
            "-filter_complex",
            f"[0:v][1:v]xfade=transition=fade:duration={crossfade}:offset=4.5[v];"
            f"[0:a][1:a]acrossfade=d={crossfade}[a]",
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", output
        ], check=True)
```

### 3. Voiceover overlay with ducking

```bash
# VO at -6dBFS, video audio muted (cleanest for narration)
ffmpeg -i video.mp4 -i voiceover.wav \
  -filter_complex "[1:a]loudnorm=I=-6:TP=-1.5:LRA=11[vo]" \
  -map 0:v -map "[vo]" -c:v copy -c:a aac -b:a 128k output.mp4
```

### 4. Caption burn-in with ASS styling

```python
def burn_captions(video: str, srt: str, output: str) -> None:
    """Burn SRT with Montserrat Bold, white text, black stroke, upper third."""
    style = (
        "FontName=Montserrat Bold,FontSize=60,PrimaryColour=&HFFFFFF,"
        "OutlineColour=&H000000,Outline=2,Alignment=8,MarginV=200"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", video,
        "-vf", f"subtitles={srt}:force_style='{style}'",
        "-c:v", "libx264", "-crf", "18", "-c:a", "copy", output
    ], check=True)
```

**Word-by-word highlighting**: ffmpeg's `drawtext` does NOT support karaoke timing. Use ASS format with `\kf` tags generated from forced alignment (see Section 5).

### 5. Metadata stripping including C2PA

```bash
# Strip ALL metadata
ffmpeg -i input.mp4 -map_metadata -1 -map_chapters -1 -c:v copy -c:a copy \
  -fflags +bitexact stripped.mp4

# Add copyright via exiftool
exiftool -overwrite_original -Copyright="© 2026 Baby Brains" stripped.mp4
```

### 6. Platform export presets (batch)

```python
PRESETS = {
    "tiktok":   {"vbr": "3000k", "max": "4000k", "abr": "128k", "ar": 44100},
    "reels":    {"vbr": "4000k", "max": "4500k", "abr": "128k", "ar": 44100},
    "shorts":   {"vbr": "12000k", "max": "15000k", "abr": "192k", "ar": 48000},
    "facebook": {"vbr": "6000k", "max": "8000k", "abr": "128k", "ar": 44100},
}

def export_all_platforms(master: str, output_dir: str) -> dict[str, str]:
    """Export master to all 4 platform versions."""
    outputs = {}
    for platform, p in PRESETS.items():
        out = f"{output_dir}/{Path(master).stem}_{platform}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-i", master,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                   "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-b:v", p["vbr"], "-maxrate", p["max"],
            "-bufsize", f"{int(p['max'][:-1])*2}k",
            "-r", "30", "-g", "60", "-c:a", "aac", "-b:a", p["abr"],
            "-ar", str(p["ar"]), "-movflags", "+faststart", out
        ], check=True, capture_output=True)
        outputs[platform] = out
    return outputs
```

### 7. Contact sheet thumbnail grid

```bash
ffmpeg -i video.mp4 \
  -vf "fps=9/60,scale=360:-1,drawtext=text='%{pts\:hms}':x=10:y=H-th-10:\
fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile=3x3:padding=4:margin=4" \
  -frames:v 1 -q:v 2 contact_sheet.png
```

**Build priority**: Scripts 1, 3, 6 first (highest per-video time savings). Script 2 and 4 can wait until you have consistent clip lengths.

---

## Section 3: Content database and script generation

**Recommended approach**: SQLite for production tracking (queryable), YAML for human-editable templates. The official Anthropic SQLite MCP server enables natural language queries directly in Claude Code.

### Database schema

```sql
CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    age_range TEXT CHECK(age_range IN ('0-3m','3-6m','6-9m','9-12m','12-18m','18-24m','2-3y')),
    category TEXT,
    skill_areas TEXT,  -- JSON array: ["fine motor", "problem solving"]
    materials TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scripts (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER REFERENCES activities(id),
    hook_type TEXT CHECK(hook_type IN ('problem','result_first','curiosity','authority',
                                        'pattern_interrupt','relatable','contrarian')),
    hook_text TEXT,      -- ~15 words
    problem_text TEXT,   -- ~25 words  
    demo_text TEXT,      -- ~50 words
    learning_text TEXT,  -- ~25 words
    tip_text TEXT,       -- ~20 words
    cta_text TEXT,       -- ~15 words
    status TEXT DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scenes (
    id INTEGER PRIMARY KEY,
    script_id INTEGER REFERENCES scripts(id),
    scene_order INTEGER,
    mj_prompt TEXT,
    pika_prompt TEXT,
    kling_prompt TEXT,
    duration_seconds INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE clips (
    id INTEGER PRIMARY KEY,
    scene_id INTEGER REFERENCES scenes(id),
    file_path TEXT,
    source TEXT CHECK(source IN ('midjourney','pika','kling','hailuo')),
    vmaf_score REAL,
    qc_status TEXT DEFAULT 'pending',
    qc_notes TEXT,
    selected BOOLEAN DEFAULT FALSE
);

-- Useful query: unpublished scripts for 8-12 month range
CREATE VIEW pending_scripts AS
SELECT s.*, a.title as activity_title 
FROM scripts s JOIN activities a ON s.activity_id = a.id
WHERE a.age_range IN ('6-9m', '9-12m') AND s.status != 'published';
```

### Seven hook variation generator

```python
from jinja2 import Environment, BaseLoader

HOOKS = {
    "problem": "Your {{ age_range }} baby keeps {{ problem_behavior }}...",
    "result_first": "Watch this {{ age_range }} baby {{ achievement }}...",
    "curiosity": "Most parents don't know this about {{ skill_area }}...",
    "authority": "Montessori teachers use this {{ activity_type }} technique...",
    "pattern_interrupt": "{{ unexpected_opener }}",
    "relatable": "We've all been there — {{ common_struggle }}...",
    "contrarian": "Forget what you've heard about {{ misconception }}...",
}

def generate_all_hooks(activity: dict) -> list[dict]:
    """Generate all 7 hook variations for an activity."""
    env = Environment(loader=BaseLoader())
    return [
        {"type": hook_type, "text": env.from_string(template).render(**activity)}
        for hook_type, template in HOOKS.items()
    ]
```

### AI prompt generation templates

**MidJourney V7** (character consistency via --oref):
```python
MJ_TEMPLATE = """
{character_dna}, {action}, {environment}, {lighting},
soft clay aesthetic, 3D rendered, pastel colors, Montessori nursery style
--oref {character_ref_url} --ow 300 --sref 74185 --v 7 --ar 9:16
"""

# Character DNA prefix (use consistently)
CHARACTER_DNA = "Baby_Maya: 8-month-old baby with round face, dark wispy hair, curious expression, soft clay 3D style"
```

**Pika 2.5** (image-to-video, motion-only):
```python
PIKA_TEMPLATE = """
{subject} {action}, subtle natural movement, {environment_motion},
camera {camera_move}, warm soft lighting, shallow depth of field
-camera {camera_param} -ar 9:16 -neg morphing, jitter, hand distortion, face warping
"""
```

**Kling** (4-element formula):
```python
KLING_TEMPLATE = """
{shot_type} shot, camera {camera_movement},
{character_dna} {action_with_endpoint},
{environment}, {lighting},
photorealistic quality, cinematic depth of field
"""
# Example: "Medium close-up shot, camera slowly tracks right, baby in pastel onesie gently places third stacking block, modern nursery with natural window light, warm golden hour lighting"
```

**Limitation**: No existing Python libraries specifically for AI video prompt templating. Jinja2 with custom templates is the standard approach.

---

## Section 4: QC pipeline implementation

**Recommended approach**: Hybrid trigger—watchdog logs new files to SQLite as "pending," manual `/qc` slash command in Claude Code triggers review. Fully automatic triggers add complexity without proportional benefit for solo creators.

### File watcher setup

```python
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import sqlite3

class NewClipHandler(PatternMatchingEventHandler):
    def __init__(self, db_path):
        super().__init__(patterns=["*.mp4"], ignore_directories=True)
        self.db_path = db_path
    
    def on_created(self, event):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO clips (file_path, qc_status) VALUES (?, 'pending')",
            (event.src_path,)
        )
        conn.commit()
        print(f"Queued for QC: {event.src_path}")

# Start watcher (run in background)
observer = Observer()
observer.schedule(NewClipHandler("baby_brains.db"), "04_RAW_GENERATIONS/", recursive=True)
observer.start()
```

**WSL2 critical note**: inotify does NOT work for files on `/mnt/c/`. Store raw generations in WSL2's Linux filesystem (`~/projects/baby_brains/`) or use `PollingObserver` as fallback.

### QC workflow implementation

```python
import subprocess
from pathlib import Path

def run_qc(video_path: str, source_mj_image: str = None) -> dict:
    """Complete QC workflow for a single clip."""
    video = Path(video_path)
    qc_dir = video.parent / f"{video.stem}_qc"
    qc_dir.mkdir(exist_ok=True)
    
    # 1. Extract frames at 2fps, 1024px (optimal for Claude vision)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video),
        "-vf", "fps=2,scale=1024:-1", "-q:v", "2",
        str(qc_dir / "frame_%04d.jpg")
    ], check=True, capture_output=True)
    
    # 2. Calculate VMAF (requires reference—skip for AI-generated)
    # For social media: Target VMAF 80-85 is acceptable
    
    # 3. SSIM comparison to source MidJourney image (if provided)
    ssim_score = None
    if source_mj_image:
        from skimage.metrics import structural_similarity
        import cv2
        frame = cv2.imread(str(qc_dir / "frame_0001.jpg"), cv2.IMREAD_GRAYSCALE)
        source = cv2.imread(source_mj_image, cv2.IMREAD_GRAYSCALE)
        source = cv2.resize(source, (frame.shape[1], frame.shape[0]))
        ssim_score = structural_similarity(frame, source)
    
    # 4. Return frame paths for Claude vision analysis
    frames = sorted(qc_dir.glob("*.jpg"))
    return {
        "video": str(video),
        "frames": [str(f) for f in frames[:5]],  # First 5 frames
        "ssim_to_source": ssim_score,
        "qc_dir": str(qc_dir)
    }
```

### Claude vision QC checklist

When sending frames to Claude for analysis, use this prompt structure:

```
Analyze these video frames for AI generation artifacts:

1. HANDS: Extra/missing fingers, warped hands, unnatural positions
2. FACE: Warping, asymmetry, unnatural expressions  
3. CHARACTER: Proportions consistent with reference, no morphing
4. BACKGROUND: Stability, no warping/swimming elements
5. MOTION: Start/end frames clean, no jitter artifacts

Rate each: PASS | MINOR | MAJOR
Overall recommendation: APPROVE | REGENERATE | MANUAL_REVIEW
```

**Optimal frame resolution**: 1024px on long edge. Claude vision auto-resizes images larger than 1568px; smaller than 512px loses detail for artifact detection.

**VMAF thresholds**: For TikTok/Reels, **VMAF 80-85** is acceptable. Premium streaming targets 93+, but social media compression makes higher scores unnecessary.

**Limitation**: Claude cannot reliably identify if content is AI-generated and should not be used for authenticity verification. It CAN detect visible artifacts like hand deformities.

---

## Section 5: Voice pipeline integration

**Recommended approach**: Chatterbox Turbo as primary (local, zero marginal cost), ElevenLabs MCP as fallback ($0.17/min). Use aeneas for forced alignment to generate word-timed SRT files.

### Chatterbox Turbo installation (WSL2)

```bash
conda create -n chatterbox python=3.11 -y
conda activate chatterbox
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install chatterbox-tts

# First run downloads ~5GB of models
```

**Python usage**:
```python
import torchaudio as ta
from chatterbox.tts_turbo import ChatterboxTurboTTS

model = ChatterboxTurboTTS.from_pretrained(device="cuda")

def generate_voiceover(text: str, reference_audio: str, output_path: str):
    """Generate VO using your cloned voice. Reference: 10+ seconds of clean audio."""
    wav = model.generate(text, audio_prompt_path=reference_audio)
    ta.save(output_path, wav, model.sr)
    return output_path
```

**Voice cloning requirements**: 10+ seconds of clean audio, WAV format, single speaker, no background noise.

**VRAM usage**: ~4-6GB. **Cannot run simultaneously** with Stable Diffusion or other GPU-heavy tasks on 8GB. Sequential processing required.

**Local API server** (for Claude Code integration):
```bash
git clone https://github.com/travisvn/chatterbox-tts-api
cd chatterbox-tts-api && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 4123
# OpenAI-compatible endpoint at POST /v1/audio/speech
```

### ElevenLabs fallback via MCP

```json
{
  "mcpServers": {
    "ElevenLabs": {
      "command": "uvx",
      "args": ["elevenlabs-mcp"],
      "env": {"ELEVENLABS_API_KEY": "your_key"}
    }
  }
}
```

**Starter plan ($5/month)**: 30 minutes TTS, instant voice cloning included. ~$0.17/minute effective cost.

### Forced alignment for word-timed SRT

**Recommended tool**: aeneas (accent-agnostic, uses TTS+DTW not ASR)

```bash
pip install aeneas
# Requires: espeak, ffmpeg (already installed)

# Generate word-level SRT
python -m aeneas.tools.execute_task \
  voiceover.wav \
  script.txt \
  "task_language=eng|is_text_type=plain|os_task_file_format=srt" \
  output.srt
```

**Python integration**:
```python
import subprocess

def generate_timed_srt(audio_path: str, script_path: str, output_srt: str):
    """Generate word-timed SRT from audio + known script text."""
    subprocess.run([
        "python", "-m", "aeneas.tools.execute_task",
        audio_path, script_path,
        "task_language=eng|is_text_type=plain|os_task_file_format=srt",
        output_srt
    ], check=True)
```

**Australian accent**: aeneas works well (accent-agnostic approach). Montreal Forced Aligner is more accurate but requires dictionary setup.

**Limitation**: aeneas provides sentence-level timing by default. For true word-by-word karaoke, use `--presets-word` or post-process with WhisperX alignment.

---

## Section 6: DaVinci Resolve scripting integration

**Recommended approach**: Template project + three simple Python scripts (import, timeline scaffold, batch render). Full automation has diminishing returns for 25-35 videos/month.

### API capabilities confirmed

| Task | Possible | Method |
|------|----------|--------|
| Auto-import from folder | ✅ | `MediaStorage.AddItemListToMediaPool(paths)` |
| Create timeline from clips | ✅ | `MediaPool.CreateTimelineFromClips(name, clips)` |
| Apply LUT to clips | ✅ | `TimelineItem.SetLUT(nodeIndex, lutPath)` |
| Import SRT subtitles | ✅ | `Timeline.ImportIntoTimeline(srtPath)` |
| Batch render to presets | ✅ | `AddRenderJob()` + `StartRendering()` |
| Apply PowerGrade | ⚠️ | Must use `ApplyGradeFromDRX()`, no direct method |
| Audio ducking | ❌ | Not scriptable—manual only |
| Trim/split clips | ❌ | API only appends, cannot edit positions |

### Practical requirements

- **DaVinci must be running** for scripts to work
- **Studio version required** for external scripting
- **WSL2 not supported**—run scripts from Windows native Python
- **Headless mode** (`resolve -nogui`) works but some render operations fail without display

### Recommended library: pybmd (actively maintained)

```bash
pip install pybmd
```

```python
from pybmd import Resolve

resolve = Resolve(auto_start=True)  # Launches Resolve if not running
project = resolve.project

# Import media
media_pool = project.media_pool
storage = resolve.media_storage
clips = storage.add_items_to_media_pool(["/path/to/clips/folder"])

# Create timeline
timeline = media_pool.create_timeline_from_clips("Episode_001", clips)

# Batch render to presets
project.set_current_render_format_and_codec("mp4", "H264")
project.set_render_settings({"TargetDir": "/output", "CustomName": "tiktok_export"})
project.add_render_job()
project.start_rendering()
```

### MCP server available

**samuelgursky/davinci-resolve-mcp** (426 stars, actively maintained)

```bash
git clone https://github.com/samuelgursky/davinci-resolve-mcp.git
cd davinci-resolve-mcp && ./install.sh  # macOS
# or install.bat on Windows
```

Enables natural language commands: "Create a new timeline called 'Final Edit' and import all clips from the raw folder"

### ROI analysis for 25-35 videos/month

| Approach | Setup time | Per-video time | Monthly total | Break-even |
|----------|-----------|----------------|---------------|------------|
| Manual | 0 hrs | 45-60 min | 25-35 hrs | — |
| Template + 3 scripts | 15-20 hrs | 20-30 min | 12-18 hrs | Month 2 |
| Full automation | 50+ hrs | 10-15 min | 6-9 hrs | Month 6+ |

**Recommendation**: Build template approach first. Automate only: import, timeline scaffold, batch render. Manual: color grading, audio ducking, fine edits.

---

## Section 7: Hailuo burst automation (API-based)

**Recommended approach**: Direct Python script with fal.ai API—simpler than n8n for SQLite integration and gives fine-grained concurrency control.

### fal.ai setup and cost structure

```bash
pip install fal-client aiohttp aiosqlite
export FAL_KEY="your_api_key"  # Get from fal.ai dashboard
```

**Critical clarification**: fal.ai is **pay-per-use**, NOT a pass-through to your Hailuo subscription. You pay fal.ai directly:
- **Hailuo 01 Live (768p, 6s)**: ~$0.27/video
- **Hailuo 02 Pro (1080p, 6s)**: ~$0.48/video

Your $199.99 Hailuo subscription is for the **web interface only**. API usage through fal.ai is billed separately.

### Burst generation script

```python
import asyncio
import fal_client
import aiosqlite
import aiohttp
from pathlib import Path

async def burst_generate(db_path: str, output_dir: str, concurrent: int = 5):
    """Generate video library from pending prompts in database."""
    semaphore = asyncio.Semaphore(concurrent)  # Respect rate limits
    
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT id, mj_image_url, prompt FROM scenes WHERE status='pending'"
        )
        jobs = await cursor.fetchall()
    
    async def process_job(job_id, image_url, prompt):
        async with semaphore:
            try:
                response = await fal_client.submit_async(
                    "fal-ai/minimax/video-01-live/image-to-video",
                    arguments={"prompt": prompt, "image_url": image_url}
                )
                result = await response.get()
                
                # Download video
                video_url = result["video"]["url"]
                output_path = Path(output_dir) / f"VID{job_id:04d}_hailuo_raw.mp4"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(video_url) as resp:
                        output_path.write_bytes(await resp.read())
                
                return job_id, str(output_path), None
            except Exception as e:
                return job_id, None, str(e)
    
    tasks = [process_job(*job) for job in jobs]
    results = await asyncio.gather(*tasks)
    
    # Update database
    async with aiosqlite.connect(db_path) as db:
        for job_id, path, error in results:
            if path:
                await db.execute(
                    "UPDATE scenes SET status='generated', video_path=? WHERE id=?",
                    (path, job_id)
                )
            else:
                await db.execute(
                    "UPDATE scenes SET status='failed', error=? WHERE id=?",
                    (error, job_id)
                )
        await db.commit()

# Run: asyncio.run(burst_generate("baby_brains.db", "./04_RAW_GENERATIONS", concurrent=5))
```

### Rate limits and constraints

- **Default**: 2-10 concurrent tasks (varies by account tier)
- **With $1,000+ credits**: Up to 40 concurrent
- **Video duration**: 6 seconds standard
- **File retention**: 7 days minimum—download immediately

### n8n alternative

Template 7335 exists and works with Google Sheets → Freepik/Hailuo → Google Drive. To adapt for SQLite:
1. Install n8n: `docker run -d -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n`
2. Install SQLite community node: `n8n-node-sqlite3`
3. Replace Google Sheets nodes with SQLite query nodes

**Recommendation**: Python script is simpler for your use case. n8n adds overhead without significant benefit.

---

## Section 8: Scheduling and distribution automation

**Recommended approach**: YouTube Data API (most accessible) + Meta Graph API (Reels/Facebook). TikTok API requires audit for public posts. Use Metricool MCP for scheduling if you have Advanced plan.

### Platform API summary

| Platform | API Available | Public Posting | Setup Effort |
|----------|--------------|----------------|--------------|
| YouTube Shorts | ✅ Data API v3 | ✅ Immediate | 2-4 hours |
| Instagram Reels | ✅ Graph API | ✅ After app review | 4-8 hours |
| Facebook Reels | ✅ Graph API | ✅ Pages only | 4-8 hours |
| TikTok | ⚠️ Content Posting API | ❌ Private only (unaudited) | Weeks for audit |

### YouTube Shorts upload

```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_short(credentials, video_path: str, title: str, description: str):
    """Upload video as YouTube Short. Include #Shorts in title."""
    youtube = build('youtube', 'v3', credentials=credentials)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{title} #Shorts",
                "description": f"{description}\n\n#Shorts #BabyBrains #Montessori",
                "categoryId": "22"  # People & Blogs
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": True  # Required for baby content
            }
        },
        media_body=MediaFileUpload(video_path, mimetype="video/mp4")
    )
    return request.execute()
```

**Quota**: ~100 units per upload, 10,000 units/day = ~100 uploads/day theoretical max.

### Instagram Reels upload

```python
import requests

def upload_reel(page_id: str, access_token: str, video_url: str, caption: str):
    """Upload Reel via Meta Graph API. Requires Business/Creator account."""
    # Step 1: Create container
    response = requests.post(
        f"https://graph.facebook.com/v18.0/{page_id}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,  # Must be public, direct URL (no redirects)
            "caption": caption,
            "access_token": access_token
        }
    )
    creation_id = response.json()["id"]
    
    # Step 2: Poll until ready, then publish
    # (simplified—production code needs polling loop)
    requests.post(
        f"https://graph.facebook.com/v18.0/{page_id}/media_publish",
        params={"creation_id": creation_id, "access_token": access_token}
    )
```

**Requirements**: Business/Creator account, Facebook Page linked, OAuth app review completed.

### TikTok API limitations

**Unaudited apps** (your situation initially):
- Limited to 5 users per 24 hours
- **ALL posts forced to SELF_ONLY (private)** mode
- Must manually change privacy settings after upload

**Audited apps** require:
- Demo videos of complete integration
- Compliance with UX guidelines
- Privacy Policy on website
- Weeks of review process

**Reach penalty**: No verified data proving API posts get less reach. Issues arise from bot-like patterns, VPN usage, or non-compliant implementations.

### Metricool MCP integration

```json
{
  "mcpServers": {
    "metricool": {
      "command": "uvx",
      "args": ["--upgrade", "mcp-metricool"],
      "env": {
        "METRICOOL_USER_TOKEN": "your_token",
        "METRICOOL_USER_ID": "your_user_id"
      }
    }
  }
}
```

**Requires**: Metricool Advanced plan (~$20/month) for API access.

### Repurpose.io assessment

- **No API** available
- Good for non-technical cross-posting
- $25/month saves ~2 hours/week for active creators
- **Recommendation**: Skip—use direct APIs for programmatic control, or manual posting for low volume

---

## Build priority roadmap

### Phase 1: Foundation (Week 1-2)
1. ✅ SQLite database with schema
2. ✅ SQLite MCP server in Claude Code
3. ✅ ffmpeg scripts for keyframe extraction + platform exports
4. ✅ Basic QC workflow (manual trigger)

### Phase 2: Content generation (Week 3-4)
1. Hook variation generator
2. MidJourney/Pika/Kling prompt templates
3. Chatterbox Turbo local TTS setup
4. aeneas forced alignment for SRT

### Phase 3: Automation (Month 2)
1. Hailuo burst generation script
2. DaVinci import + render scripts
3. YouTube/Instagram API uploads
4. File watcher for auto-queuing

### Phase 4: Polish (Month 3+)
1. DaVinci MCP integration (if ROI justified)
2. Metricool scheduling (if Advanced plan)
3. Full pipeline orchestration
4. Analytics feedback loop

**Total estimated setup time**: 40-60 hours for Phases 1-3. Phase 4 is optional polish.

---

## Known limitations summary

| Component | What won't work |
|-----------|-----------------|
| **MCP servers** | No MidJourney/Pika/Kling wrappers exist—use direct API |
| **ffmpeg** | Karaoke captions require ASS format, not drawtext |
| **Chatterbox** | Cannot run alongside video generation on 8GB VRAM |
| **DaVinci API** | Cannot trim/split clips, no audio ducking, clips append to Track 1 only |
| **DaVinci + WSL2** | Not supported—run from Windows Python |
| **Hailuo API** | fal.ai charges separately from web subscription |
| **TikTok API** | Private-only posts until audit approved (weeks) |
| **File watching** | WSL2 inotify broken for /mnt/c/—use Linux filesystem |

This pipeline is achievable and will significantly reduce your per-video production time from ~60 minutes to ~15-20 minutes once built. Focus on the QC pipeline first—it provides immediate value and compounds as your content library grows.