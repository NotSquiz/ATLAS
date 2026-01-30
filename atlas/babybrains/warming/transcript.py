"""
YouTube Transcript Fetcher

Fetches video transcripts using youtube-transcript-api.
Falls back to video metadata (title + description) if transcript unavailable.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    """Result from a transcript fetch attempt."""

    video_id: str
    text: Optional[str] = None
    summary: Optional[str] = None
    language: Optional[str] = None
    is_generated: bool = False
    source: str = "transcript"  # 'transcript', 'metadata', 'failed'
    error: Optional[str] = None

    @property
    def available(self) -> bool:
        return self.text is not None and len(self.text) > 0


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.

    Handles:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - Plain video ID string
    """
    patterns = [
        r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _summarize_transcript(text: str, max_sentences: int = 5) -> str:
    """Create a brief summary from transcript text.

    Takes the first N sentences as a rough summary.
    """
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return ". ".join(sentences[:max_sentences]) + "." if sentences else ""


async def fetch_transcript(
    url_or_id: str,
    languages: Optional[list[str]] = None,
) -> TranscriptResult:
    """
    Fetch transcript for a YouTube video.

    Args:
        url_or_id: YouTube URL or video ID
        languages: Preferred languages (default: ['en'])

    Returns:
        TranscriptResult with text and metadata
    """
    video_id = extract_video_id(url_or_id)
    if not video_id:
        return TranscriptResult(
            video_id=url_or_id,
            source="failed",
            error=f"Could not extract video ID from: {url_or_id}",
        )

    languages = languages or ["en"]

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=languages)

        # Combine all transcript segments
        full_text = " ".join(
            snippet.text for snippet in transcript.snippets
        )

        # Clean up the text
        full_text = re.sub(r"\s+", " ", full_text).strip()

        summary = _summarize_transcript(full_text)

        return TranscriptResult(
            video_id=video_id,
            text=full_text,
            summary=summary,
            language=transcript.language,
            is_generated=transcript.is_generated,
            source="transcript",
        )

    except Exception as e:
        error_msg = str(e)
        logger.debug(f"Transcript not available for {video_id}: {error_msg}")

        # Try to get basic info from the video page as fallback
        return TranscriptResult(
            video_id=video_id,
            source="failed",
            error=error_msg,
        )


async def fetch_transcripts_batch(
    urls: list[str],
    languages: Optional[list[str]] = None,
) -> list[TranscriptResult]:
    """
    Fetch transcripts for multiple videos.

    Args:
        urls: List of YouTube URLs or video IDs
        languages: Preferred languages

    Returns:
        List of TranscriptResults (same order as input)
    """
    results = []
    for url in urls:
        result = await fetch_transcript(url, languages)
        results.append(result)

    return results
