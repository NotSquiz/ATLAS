"""
Baby Brains Content QC Hooks

Deterministic validators for content production pipeline.
Each hook is a standalone CLI script with __main__ entrypoint.

Input: JSON from stdin (for text-based hooks)
Output: JSON to stdout {"pass": bool, "issues": [{"code": str, "msg": str}]}
Exit code: 0=pass, 1=fail

Hooks:
- qc_brief: Brief structural validation (30s timeout)
- qc_safety: Safety gate with hazard/supervision checks (30s timeout)
- qc_montessori: Montessori alignment validation (30s timeout)
- qc_hook_token: Hook in scene 1 validation (30s timeout)
- qc_script: Script requirements validation (30s timeout)
- qc_audio: Audio levels validation via ffmpeg (180s timeout)
- qc_caption_wer: Caption WER via faster-whisper (180s timeout)
- qc_safezone: Caption safe zones validation (30s timeout)
"""

from atlas.babybrains.content.hooks import qc_brief
from atlas.babybrains.content.hooks import qc_safety
from atlas.babybrains.content.hooks import qc_montessori
from atlas.babybrains.content.hooks import qc_hook_token
from atlas.babybrains.content.hooks import qc_script
from atlas.babybrains.content.hooks import qc_audio
from atlas.babybrains.content.hooks import qc_caption_wer
from atlas.babybrains.content.hooks import qc_safezone

__all__ = [
    "qc_brief",
    "qc_safety",
    "qc_montessori",
    "qc_hook_token",
    "qc_script",
    "qc_audio",
    "qc_caption_wer",
    "qc_safezone",
]
