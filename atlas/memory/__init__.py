"""Memory subsystem with SQLite + sqlite-vec + FTS5."""

from .store import MemoryStore, Memory, SearchResult, get_store
from .embeddings import BGEEmbedder, EmbeddingResult, get_embedder
from .blueprint import (
    BlueprintAPI,
    DailyMetrics,
    Supplement,
    SupplementLog,
    Workout,
    WorkoutExercise,
    LabResult,
    Injury,
    get_blueprint_api,
)

# Singleton memory store
_memory_store = None


def get_memory_store() -> MemoryStore:
    """
    Get singleton memory store instance.

    Creates store at ~/.atlas/atlas.db if not exists.
    Initializes schema on first access.

    Usage:
        from atlas.memory import get_memory_store

        store = get_memory_store()
        store.add_memory("User prefers morning workouts", importance=0.8)
    """
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
        _memory_store.init_db()
    return _memory_store


__all__ = [
    # Store
    "MemoryStore",
    "Memory",
    "SearchResult",
    "get_store",
    "get_memory_store",
    # Embeddings
    "BGEEmbedder",
    "EmbeddingResult",
    "get_embedder",
    # Blueprint
    "BlueprintAPI",
    "DailyMetrics",
    "Supplement",
    "SupplementLog",
    "Workout",
    "WorkoutExercise",
    "LabResult",
    "Injury",
    "get_blueprint_api",
]
