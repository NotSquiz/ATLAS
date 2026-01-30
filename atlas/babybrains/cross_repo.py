"""
Cross-Repo Document Search

Searches across all Baby Brains repositories for relevant
strategy, research, and content documents.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Config location
CROSS_REPO_CONFIG = Path(__file__).parent.parent.parent / "config" / "babybrains" / "cross_repo_paths.json"


class CrossRepoSearch:
    """
    Search across all BB repositories using a static path map.

    The path map is defined in config/babybrains/cross_repo_paths.json
    and maps topic keywords to file paths across 5 active repos.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CROSS_REPO_CONFIG
        self._config: Optional[dict] = None

    def _load_config(self) -> dict:
        """Load the cross-repo path map config."""
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            logger.warning(f"Cross-repo config not found: {self.config_path}")
            self._config = {"repos": {}, "topic_map": {}}
            return self._config

        self._config = json.loads(self.config_path.read_text(encoding="utf-8"))
        return self._config

    @property
    def repos(self) -> dict[str, str]:
        """Get repo name -> base path mapping."""
        return self._load_config().get("repos", {})

    @property
    def topic_map(self) -> dict[str, list[dict]]:
        """Get topic -> file entries mapping."""
        return self._load_config().get("topic_map", {})

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for documents matching a query across all repos.

        Uses keyword matching against topic names and summaries.

        Args:
            query: Search query (e.g., "platform strategy", "montessori")
            limit: Maximum results to return

        Returns:
            List of dicts with: repo, path, full_path, summary, topic
        """
        config = self._load_config()
        query_lower = query.lower()
        query_words = query_lower.split()

        results = []
        seen_paths = set()

        for topic, entries in config.get("topic_map", {}).items():
            topic_lower = topic.lower()

            # Score: how many query words match the topic or its entries
            score = 0
            for word in query_words:
                if word in topic_lower:
                    score += 2  # topic match weighted higher
                for entry in entries:
                    summary_lower = (entry.get("summary") or "").lower()
                    if word in summary_lower:
                        score += 1

            if score == 0:
                continue

            for entry in entries:
                repo = entry["repo"]
                rel_path = entry["path"]
                base_path = config.get("repos", {}).get(repo, "")
                full_path = f"{base_path}/{rel_path}" if base_path else rel_path

                # Deduplicate
                if full_path in seen_paths:
                    continue
                seen_paths.add(full_path)

                # Check if file actually exists
                exists = Path(full_path).exists()

                results.append({
                    "repo": repo,
                    "path": rel_path,
                    "full_path": full_path,
                    "summary": entry.get("summary", ""),
                    "topic": topic,
                    "score": score,
                    "exists": exists,
                })

        # Sort by score descending
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def get_topic_docs(self, topic: str) -> list[dict]:
        """
        Get all documents for a specific topic.

        Args:
            topic: Exact topic name (e.g., "youtube", "montessori")

        Returns:
            List of document entries for the topic
        """
        config = self._load_config()
        entries = config.get("topic_map", {}).get(topic, [])

        results = []
        for entry in entries:
            repo = entry["repo"]
            base_path = config.get("repos", {}).get(repo, "")
            full_path = f"{base_path}/{entry['path']}" if base_path else entry["path"]

            results.append({
                "repo": repo,
                "path": entry["path"],
                "full_path": full_path,
                "summary": entry.get("summary", ""),
                "exists": Path(full_path).exists(),
            })

        return results

    def list_topics(self) -> list[str]:
        """Get all available topics."""
        return list(self._load_config().get("topic_map", {}).keys())


# Module-level singleton
_search: Optional[CrossRepoSearch] = None


def get_cross_repo_search() -> CrossRepoSearch:
    """Get or create the cross-repo search singleton."""
    global _search
    if _search is None:
        _search = CrossRepoSearch()
    return _search
