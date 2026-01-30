"""Tests for Baby Brains cross-repo search."""

import json
from pathlib import Path

import pytest

from atlas.babybrains.cross_repo import CrossRepoSearch


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample cross-repo config."""
    config = {
        "repos": {
            "ATLAS": str(tmp_path / "ATLAS"),
            "babybrains-os": str(tmp_path / "babybrains-os"),
            "web": str(tmp_path / "web"),
        },
        "topic_map": {
            "platform strategy": [
                {
                    "repo": "babybrains-os",
                    "path": "docs/PLATFORM-PLAYBOOKS.md",
                    "summary": "Platform-specific posting strategies",
                },
                {
                    "repo": "babybrains-os",
                    "path": "docs/SOCIAL-MEDIA-STRATEGY.md",
                    "summary": "Overall social media funnel strategy",
                },
            ],
            "youtube": [
                {
                    "repo": "babybrains-os",
                    "path": "docs/research/youtube-dec-2025.md",
                    "summary": "YouTube algorithm research Dec 2025",
                },
            ],
            "voice spec": [
                {
                    "repo": "web",
                    "path": ".claude/agents/BabyBrains-Writer.md",
                    "summary": "1712-line voice specification",
                },
            ],
            "montessori": [
                {
                    "repo": "ATLAS",
                    "path": "docs/montessori.md",
                    "summary": "Montessori philosophy notes",
                },
            ],
        },
    }

    # Create some test files so exists check works
    (tmp_path / "babybrains-os" / "docs" / "research").mkdir(parents=True)
    (tmp_path / "babybrains-os" / "docs" / "PLATFORM-PLAYBOOKS.md").write_text("test")
    (tmp_path / "babybrains-os" / "docs" / "research" / "youtube-dec-2025.md").write_text("test")

    config_path = tmp_path / "cross_repo_paths.json"
    config_path.write_text(json.dumps(config))
    return config_path


class TestCrossRepoSearch:
    """Test cross-repo document search."""

    def test_search_platform(self, sample_config):
        search = CrossRepoSearch(sample_config)
        results = search.search("platform strategy")
        assert len(results) >= 1
        assert any(r["repo"] == "babybrains-os" for r in results)

    def test_search_youtube(self, sample_config):
        search = CrossRepoSearch(sample_config)
        results = search.search("youtube")
        assert len(results) >= 1
        assert any("youtube" in r["path"] for r in results)

    def test_search_no_results(self, sample_config):
        search = CrossRepoSearch(sample_config)
        results = search.search("zzz_nonexistent_topic")
        assert len(results) == 0

    def test_search_partial_match(self, sample_config):
        search = CrossRepoSearch(sample_config)
        results = search.search("strategy")
        assert len(results) >= 1

    def test_search_sorted_by_score(self, sample_config):
        search = CrossRepoSearch(sample_config)
        results = search.search("platform strategy")
        if len(results) > 1:
            assert results[0]["score"] >= results[1]["score"]

    def test_search_deduplicates(self, sample_config):
        search = CrossRepoSearch(sample_config)
        results = search.search("platform")
        paths = [r["full_path"] for r in results]
        assert len(paths) == len(set(paths))

    def test_exists_check(self, sample_config):
        search = CrossRepoSearch(sample_config)
        results = search.search("youtube")
        youtube_result = [r for r in results if "youtube" in r["path"]]
        assert len(youtube_result) >= 1
        assert youtube_result[0]["exists"] is True

    def test_get_topic_docs(self, sample_config):
        search = CrossRepoSearch(sample_config)
        docs = search.get_topic_docs("youtube")
        assert len(docs) == 1
        assert docs[0]["repo"] == "babybrains-os"

    def test_get_topic_docs_empty(self, sample_config):
        search = CrossRepoSearch(sample_config)
        docs = search.get_topic_docs("nonexistent")
        assert len(docs) == 0

    def test_list_topics(self, sample_config):
        search = CrossRepoSearch(sample_config)
        topics = search.list_topics()
        assert "youtube" in topics
        assert "platform strategy" in topics
        assert "voice spec" in topics

    def test_missing_config(self, tmp_path):
        search = CrossRepoSearch(tmp_path / "nonexistent.json")
        results = search.search("anything")
        assert results == []
