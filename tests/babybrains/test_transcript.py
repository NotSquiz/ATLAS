"""Tests for YouTube transcript fetcher."""

import asyncio

import pytest

from atlas.babybrains.warming.transcript import (
    extract_video_id,
    fetch_transcript,
    TranscriptResult,
)


class TestExtractVideoId:
    """Test video ID extraction from various URL formats."""

    def test_standard_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_plain_id(self):
        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_params(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30") == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        assert extract_video_id("https://example.com/notavideo") is None

    def test_empty_string(self):
        assert extract_video_id("") is None


class TestTranscriptResult:
    """Test TranscriptResult dataclass."""

    def test_available_with_text(self):
        result = TranscriptResult(video_id="test", text="Hello world")
        assert result.available is True

    def test_not_available_without_text(self):
        result = TranscriptResult(video_id="test", text=None)
        assert result.available is False

    def test_not_available_with_empty_text(self):
        result = TranscriptResult(video_id="test", text="")
        assert result.available is False


class TestFetchTranscript:
    """Test transcript fetching."""

    def test_invalid_video_id(self):
        result = asyncio.run(fetch_transcript("not_a_valid_url_at_all!!!"))
        assert result.source == "failed"
        assert result.error is not None

    def test_fetch_returns_result(self):
        """Test that fetch_transcript returns a TranscriptResult regardless of success."""
        result = asyncio.run(fetch_transcript("dQw4w9WgXcQ"))
        assert isinstance(result, TranscriptResult)
        assert result.video_id == "dQw4w9WgXcQ"
